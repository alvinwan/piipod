from flask import Blueprint, request, redirect, url_for, g
from piipod.views import current_user, login_required
from .forms import GroupForm
from piipod.event.forms import EventForm
from piipod.models import Event, Group


group = Blueprint('group', __name__, url_prefix='/g/<int:group_id>')


@group.url_defaults
def add_group_id(endpoint, values):
    values.setdefault('group_id', getattr(g, 'group_id', None))


@group.url_value_preprocessor
def pull_group_id(endpoint, values):
    g.group_id = values.pop('group_id')
    g.group = Group.query.get(g.group_id)
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
    form = GroupForm(request.form, obj=g.group)
    if request.method == 'POST' and form.validate():
        g.group.update(**request.form).save()
        return redirect(url_for('group.home'))
    return render_group('form.html',
        title='Edit Group',
        submit='Save',
        form=form)


@group.route('/e/', methods=['GET', 'POST'])
@login_required
def create_event():
    """create event"""
    form = EventForm()
    form.group_id.default = g.group_id
    form.process()
    if request.method == 'POST' and form.validate():
        return redirect(url_for('event.home',
            event_id=Event.from_request().save().id))
    return render_group('form.html',
        title='Create Event',
        submit='Create',
        form=form)


@group.route('/events')
@login_required
def events():
    """group events"""
    return 'events'
