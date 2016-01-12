from flask import Blueprint, render_template, request
from .forms import *
from .controllers import *
from piap import app, login_manager
from piap.admin.models import User
from piap.views import anonymous_required
import flask_login

public = Blueprint('public', __name__)

##########
# PUBLIC #
##########

@public.route('/')
def home():
    """"""
    pass


###################
# SIGN IN/SIGN UP #
###################

@public.route('/signin', methods=['POST', 'GET'])
@anonymous_required
def signin():
    """Sign in"""
    form, message = SigninForm(request.form), ''
    if request.method == 'POST' and form.validate():
        user = get_user(username=request.form['username'])
        if user and user.password == request.form['password']:
            flask_login.login_user(user)
            print(' * %s (%s) logged in.' % (user.name, user.email))
            return get_user_home(user)
        message = 'Login failed.'
    return render_template('signin.html', message=message, form=form)

@public.route('/signup', methods=['GET', 'POST'])
@anonymous_required
def signup():
    """Sign up"""
    form = UserForm(request.form)
    if request.method == 'POST' and form.validate():
        return render_template('confirm.html', **add_user(request.form))
    return render_template('signup.html', form=form)

######################
# SESSION UTILIITIES #
######################

@login_manager.user_loader
def user_loader(id):
    """Load user by id"""
    print(' * Reloading user with id "%s", from user_loader' % id)
    return get_user(id=id)

@login_manager.request_loader
def request_loader(request):
    """Loads user by Flask Request object"""
    id = request.form.get('id')
    user = get_user(id=id)
    if not user:
        print(' * Anonymous user found.')
        return
    # encryption handled by SQLAlchemy PasswordType field
    user.is_authenticated = user.password == request.form['password']
    if user.is_authenticated:
        print(' * Reloaded user with id "%s", from request_loader' % id)
    return user

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('public.queue'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return get_user_home(flask_login.current_user)
