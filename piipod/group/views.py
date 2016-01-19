from flask import Blueprint, request, redirect, url_for, g
from piipod.views import current_user, login_required


group = Blueprint('group', __name__, url_prefix='/g/<string:group_id>')


@group.url_defaults
def add_group_id(endpoint, values):
    values.setdefault('group_id', g.group_id)


@group.url_value_preprocessor
def pull_group_id(endpoint, values):
    g.group_id = values.pop('group_id')
    g.group = Group.get(g.group_id)
    g.user = current_user()


def render_group(f, *args, **kwargs):
    """custom render for groups"""
    from piipod.views import render
    return render(f, *args, **kwargs)


#########
# GROUP #
#########


@group.route('/')
@login_required
def home():
    """group homepage"""
    return render_group('group/index.html')


@group.route('/events')
@login_required
def events():
    """group events"""
    return 'events'
