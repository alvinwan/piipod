from queue import db
from flask import redirect, url_for
from piap.staff.models import User, add_obj

#############
# UTILITIES #
#############

def multi2dict(multi):
    return dict(multi.items())

###############
# CONTROLLERS #
###############

def add_user(data):
    """
    Save user

    :param Request request: Flask request object
    :return: information for confirmation page
    """
    add_obj(User(**multi2dict(data)))
    return {
        'message': 'Signed up! <code>%s</code>' % str({
            'username': data['username'],
            'email': data['email'],
            'name': data['name']
        }),
        'action': 'Sign in',
        'url': url_for('public.signin')
    }

def get_user(**kwargs):
    """
    Get user by kwargs.

    :param kwargs: key arguments containing user details
    :return: User object or None
    """
    return User.query.filter_by(**kwargs).first()

def get_user_home(user):
    """
    Get home page for user

    :param User user: user object
    :return: User object or None
    """
    if user and getattr(user, 'role', None) == 'staff':
        return redirect(url_for('staff.home'))
    return redirect(url_for('public.queue'))
