from functools import wraps
from flask import url_for, redirect, render_template, g
from flask_login import login_required
import flask_login


def current_user():
    """Returns currently-logged-in user"""
    return flask_login.current_user


def render(f, *args, **kwargs):
    """Render templates with defaults"""
    return render_template(f, *args, **kwargs)


def anonymous_required(f):
    """Decorator for views that require anonymous users (e.g., sign in)"""
    @wraps(f)
    def decorator(*args, **kwargs):
        if flask_login.current_user.is_authenticated:
            return url_for('dashboard.home')
        return f(*args, **kwargs)
    return decorator

# TODO: convert to event-specific requirement?
def requires(*roles):
    """Decorator for views, restricting access to the roles listed"""
    def wrap(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            if getattr(g.user, 'role', None) not in roles:
                return 'Permission denied.'
            return f(*args, **kwargs)
        return decorator
    return wrap
