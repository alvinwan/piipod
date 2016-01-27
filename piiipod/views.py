from functools import wraps
from flask import url_for as flask_url_for, redirect, render_template, request, g
from flask_login import login_required
from piiipod import config
import flask_login


def current_user():
    """Returns currently-logged-in user"""
    return flask_login.current_user


def render(f, *args, **kwargs):
    """Render templates with defaults"""
    for k, v in config.items():
        kwargs.setdefault('cfg_%s' % k, v)
    if not debug: # if on production
        kwargs.setdefault('domain', domain)
    return render_template(f, *args,
        googleclientID=googleclientID,
        banner_message=notifications.get(
            int(request.args.get('notification', None) or -1), None),
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
            if not all(u.can(p) for p in permissions):
                return 'Permissions Error'
            return f(*args, **kwargs)
        return decorator
    return wrap


def strip_subdomain(string, n=1):
    """Strip subdomain prefix if applicable"""
    if '/subdomain/' not in request.path:
        return string
    url = '/' + '/'.join([s for s in string.split('/') if s][n:])
    # hack fix TODO: more legit fix
    if url.endswith('admin'):
        return url + '/'
    return url


def current_url():
    """Return current URL"""
    return strip_subdomain(request.path, n=2)


def url_for(*args, **kwargs):
    """Special url function for subdomain websites"""
    return strip_subdomain(flask_url_for(*args, **kwargs))
