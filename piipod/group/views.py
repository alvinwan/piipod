from flask import Blueprint, request, redirect, url_for, g
from piipod.views import current_user, login_required
from .forms import *
from piipod.event.forms import EventForm


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
    kwargs.setdefault('group', g.group)
    return render(f, *args, **kwargs)


#########
# GROUP #
#########


@group.route('/')
@login_required
def home():
    """group homepage"""
    return render_group('group/index.html')


@group.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """group edit"""
    if request.form == 'POST':
        return redirect(url_for('group.home'))
    return render_group('form.html', form=GroupForm(request.form, obj=g.group))


@group.route('/e/', methods=['GET', 'POST'])
@login_required
def create_event():
    """create event"""
    if request.form == 'POST':
        return redirect(url_for('event.home',
            event_id=Event.from_request().save().id))
    return render_group('form.html', form=EventForm())


@group.route('/events')
@login_required
def events():
    """group events"""
    return 'events'
