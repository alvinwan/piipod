from flask import Blueprint, render_template, request, url_for, redirect
from .forms import *
from piipod import app, login_manager, logger
from piipod.models import User
from piipod.views import anonymous_required
from urllib.parse import urlparse
import flask_login

public = Blueprint('public', __name__)

##########
# PUBLIC #
##########

@public.route('/')
def home():
    """Home page"""
    return render_template('index.html')


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
            redirect_url = urlparse(form.pop('redirect', None))
            if redirect_url.scheme and redirect_url.netloc in ALLOWED_NETLOCS:
                return redirect(redirect_url + '?access-token=%s' %
                    user.generate_access_token())
            return redirect(url_for('dashboard.home'))
        message = 'Login failed.'
    return render_template('form.html',
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
        user = User.from_request().save()
        redirect_url = urlparse(form.pop('redirect', None))
        if redirect_url.scheme and redirect_url.netloc in ALLOWED_NETLOCS:
            return redirect(redirect_url + '?access-token=%s' %
                user.generate_access_token())
        return redirect(url_for('public.login'))
    return render_template('form.html',
        title='Register',
        submit='register',
        form=form,
        back=url_for('public.home'))

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
    return redirect(url_for('public.home'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('public.login'))
