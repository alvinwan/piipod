from functools import wraps
from flask import url_for, redirect, render_template
from flask_login import login_required
from piipod.public.controllers import get_user_home

import flask_login

def me():
    """Returns currently-logged-in user"""
    return flask_login.current_user


def render(f, *args, **kwargs):
    """Render templates with defaults"""
    return render_template(*args, **kwargs)


def anonymous_required(f):
    """Decorator for views that require anonymous users (e.g., sign in)"""
    @wraps(f)
    def decorator(*args, **kwargs):
        user = flask_login.current_user
        if user.is_authenticated:
            return get_user_home(user)
        return f(*args, **kwargs)
    return decorator

# TODO: convert to event-specific requirement?
def requires(*roles):
    """Decorator for views, restricting access to the roles listed"""
    def wrap(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            if getattr(flask_login.current_user, 'role', None) not in roles:
                return 'Permission denied.'
            return f(*args, **kwargs)
        return decorator
    return wrap
