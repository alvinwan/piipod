from flask import Blueprint, render_template, request, redirect, url_for, g
from piipod.views import current_user, login_required


event = Blueprint('event', __name__,
    url_prefix='/g/<string:group_name>/e/<int:event_id>')


@event.url_defaults
def add_ids(endpoint, values):
    values.setdefault('group_id', g.group_id)
    values.setdefault('event_id', g.event_id)


@event.url_value_preprocessor
def pull_ids(endpoint, values):
    g.group_id = values.pop('group_id')
    g.event_id = values.pop('event_id')
    g.user = current_user()


def render_event(f, *args, **kwargs):
    """custom render for events"""
    from piipod.views import render
    return render(f, *args, **kwargs)


#########
# EVENT #
#########


@event.route('/')
@login_required
def home():
    """event homepage"""
    return render_event('event/index.html')


@event.route('/events')
@login_required
def events():
    """group events"""
    return 'events'
