from flask import Blueprint, request, redirect, session
from .forms import *
from piipod import app, login_manager, logger, googleclientID
from piipod.models import User
from piipod.views import anonymous_required, render, url_for, current_url
from urllib.parse import urlparse
import flask_login
from oauth2client import client, crypt
from apiclient import discovery
import httplib2

public = Blueprint('public', __name__)

##########
# PUBLIC #
##########

@public.route('/')
def home():
    """Home page"""
    return render('index.html')


##################
# LOGIN/REGISTER #
##################

@public.route('/login', methods=['POST', 'GET'])
def login():
    """login to the web application"""
    flow = client.flow_from_clientsecrets(
        'client_secrets.json',
        scope='https://www.googleapis.com/auth/calendar.readonly',
        redirect_uri=url_for('public.login', _external=True))
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)
    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        session['credentials'] = credentials.to_json()
        return redirect(session['redirect'])

@public.route('/tokenlogin', methods=['POST'])
def token_login():
    """Login via Google token"""
    redirect = request.form.get('return', None)
    google_info = verify_google_token(request.form['token'])
    if google_info:
        print(' * Google Token verified!')
        google_id = google_info['sub']
        user = User.query.filter_by(email=google_info['email']).first()
        if not user:
            print(' * Registering user using Google token...')
            user = User(
                name=google_info['name'],
                email=google_info['email'],
                google_id=google_id
            ).save()
        else:
            user.update(name=google_info['name'], google_id=google_id).save()
        flask_login.login_user(user)
        print(' * %s (%s) logged in.' % (user.name, user.email))
        if redirect:
            return redirect
        return url_for('dashboard.home')
    return 'Google token verification failed.'

######################
# SESSION UTILIITIES #
######################

@login_manager.user_loader
def user_loader(id):
    """Load user by id"""
    print(' * Reloading user with id "%s", from user_loader' % id)
    return User.query.get(id)

@login_manager.request_loader
def request_loader(request):
    """Loads user by Flask Request object"""
    id = int(request.form.get('id') or 0)
    user = User.query.get(id) if id else None
    if not user:
        logger.debug('Anonymous user found.')
        return
    # encryption handled by SQLAlchemy PasswordType field
    user.is_authenticated = user.password == request.form['password']
    if user.is_authenticated:
        logger.debug('Reloaded user with id "%s", from request_loader' % id)
    return user

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(request.args.get('redirect',
        url_for('public.home')) + '?logout=true')

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('public.login'))

##################
# ERROR HANDLERS #
##################

@app.errorhandler(404)
def not_found(error):
    return render('error.html',
        title='404. Oops.',
        code=404,
        message='Oops. This page doesn\'t exist!',
        url='/',
        action='Return to homepage?'), 404


@app.errorhandler(500)
def not_found(error):
    return render('error.html',
        title='500. Hurr.',
        code=500,
        message='Sorry. Here is the error: <br><code>%s</code><br> Please file an issue on the <a href="https://github.com/CS70/ohquu/issues">Github issues page</a>, with the above code if it has not already been submitted.' % str(error)), 500


#########################
# GOOGLE AUTHENTIACTION #
#########################

def verify_google_token(auth_code):
    """
    Verify a google token

    :param token str: token
    :return: token information if valid or None
    """
    try:
        # flow = client.credentials_from_clientsecrets_and_code(
        #     'client_secrets.json',
        #     ['https://www.googleapis.com/auth/calendar.readonly'],
        #     auth_code)
        # credentials = flow.step2_exchange(auth_code)
        # session['credentials'] = credentials.to_json()
        idinfo = client.verify_id_token(auth_code, googleclientID)
        #If multiple clients access the backend server:
        if idinfo['aud'] not in [googleclientID]:
            raise crypt.AppIdentityError("Unrecognized client.")
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise crypt.AppIdentityError("Wrong issuer.")
        # Is this needed?
        # if idinfo['hd'] != url_for('public.home'):
        #     raise crypt.AppIdentityError("Wrong hosted domain.")
    except crypt.AppIdentityError:
        return
    return idinfo
