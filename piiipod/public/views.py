from flask import Blueprint, request, url_for, redirect
from .forms import *
from piiipod import app, login_manager, logger, googleclientID
from piiipod.models import User
from piiipod.views import anonymous_required, render
from urllib.parse import urlparse
import flask_login
from oauth2client import client, crypt

public = Blueprint('public', __name__)

##########
# PUBLIC #
##########

@public.route('/')
def home():
    """Home page"""
    return render('index.html',
        logout=request.args.get('logout', False),
        redirect=request.args.get('redirect', None))


##################
# LOGIN/REGISTER #
##################

@public.route('/login', methods=['POST', 'GET'])
@anonymous_required
def login():
    """login to the web application"""
    form, message = LoginForm(request.form), ''
    form.redirect.default = request.args.get('redirect', None)
    form.process()
    if request.method == 'POST' and form.validate():
        user = User.query.filter(
            User.username == request.form['username']).one_or_none()
        if user and user.password == request.form['password']:
            flask_login.login_user(user)
            print(' * %s (%s) logged in.' % (user.name, user.email))
            # redirect_url = urlparse(form.pop('redirect', None))
            # if redirect_url.scheme and redirect_url.netloc in ALLOWED_NETLOCS:
            #     return redirect(redirect_url + '?access-token=%s' % user.access_token)
            return redirect(url_for('dashboard.home'))
        message = 'Login failed.'
    return render('form.html',
        title='Login',
        submit='login',
        message=message,
        form=form,
        back=url_for('public.home'))

@public.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    """register for the piap network"""
    form = RegisterForm(request.form)
    form.redirect.default = request.args.get('redirect', None)
    form.process()
    if request.method == 'POST' and form.validate():
        request_data = dict(request.form.items())
        redirect_url = urlparse(request_data.pop('redirect', None))
        user = User(**request_data).save()
        if redirect_url.scheme and redirect_url.netloc in ALLOWED_NETLOCS:
            return redirect(redirect_url + '?access-token=%s' %
                user.generate_access_token())
        return redirect(url_for('public.login'))
    return render('form.html',
        title='Register',
        submit='register',
        form=form,
        back=url_for('public.home'))

@public.route('/tokenlogin', methods=['POST'])
@anonymous_required
def token_login():
    """Login via Google token"""
    google_info = verify_google_token(request.form['token'])
    if google_info:
        print(' * Google Token verified!')
        google_id = google_info['sub']
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            print(' * Registering user using Google token...')
            user = User(
                name=google_info['name'],
                email=google_info['email'],
                google_id=google_id
            ).save()
        flask_login.login_user(user)
        print(' * %s (%s) logged in.' % (user.name, user.email))
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
    return redirect(url_for('public.home', logout='true'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('public.login'))

##################
# ERROR HANDLERS #
##################

@app.errorhandler(404)
def not_found(error):
    return redirect(url_for('dashboard.home'))

@app.errorhandler(500)
def server_error(error):
    from queue import db
    db.session.rollback()
    return 'Sorry, try again! Sometimes, our server goes to sleep, which causes our application to crash. If this problem persists, file an issue on the <a href="https://github.com/alvinwan/piiipod/issues">Github issues page</a>.'


#########################
# GOOGLE AUTHENTIACTION #
#########################

def verify_google_token(token):
    """
    Verify a google token

    :param token str: token
    :return: token information if valid or None
    """
    try:
        idinfo = client.verify_id_token(token, googleclientID)
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
