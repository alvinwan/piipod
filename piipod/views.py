from functools import wraps
from flask import url_for as flask_url_for, redirect, render_template, request, g, abort
from flask_login import login_required
from piipod import config
import flask_login


def current_user():
    """Returns currently-logged-in user"""
    return flask_login.current_user


def render(f, *args, **kwargs):
    """Render templates with defaults"""
    for k, v in config.items():
        kwargs.setdefault('cfg_%s' % k, v)
    return render_template(f, *args,
        domain=config['domain'],
        request=request,
        g=g,
        logout=request.args.get('logout', False),
        the_url=url_for,
        current_url=current_url,
        **kwargs)


def anonymous_required(f):
    """Decorator for views that require anonymous users (e.g., sign in)"""
    @wraps(f)
    def decorator(*args, **kwargs):
        if flask_login.current_user.is_authenticated:
            return redirect(url_for('dashboard.home'))
        return f(*args, **kwargs)
    return decorator


def requires(*permissions):
    """Decorator for views, restricting access to the roles listed"""
    def wrap(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            if not all(flask_login.current_user.can(p) for p in permissions):
                if getattr(g, 'group', None):
                    return redirect(url_for('group.home'))
                return redirect(url_for('dashboard.home'))
            return f(*args, **kwargs)
        return decorator
    return wrap


def strip_subdomain(string):
    """Strip subdomain prefix if applicable"""
    if '/subdomain' not in request.path or not getattr(g, 'group', None):
        return string
    string = string.replace('/subdomain', '')
    if '/%s' % g.group.url in string:
        string = string.replace('/%s' % g.group.url, '', 1)
    return string


def current_url():
    """Return current URL"""
    return strip_subdomain(request.path)


def url_for(*args, **kwargs):
    """Special url function for subdomain websites"""
    return strip_subdomain(flask_url_for(*args, **kwargs))
