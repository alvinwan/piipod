from flask import Blueprint, render_template, request, redirect, url_for, g
from piipod.views import current_user, login_required
from .forms import EventForm
from piipod.models import Group, Event


event = Blueprint('event', __name__,
    url_prefix='/g/<int:group_id>/e/<int:event_id>')


@event.url_defaults
def add_ids(endpoint, values):
    values.setdefault('group_id', getattr(g, 'group_id', None))
    values.setdefault('event_id', getattr(g, 'event_id', None))


@event.url_value_preprocessor
def pull_ids(endpoint, values):
    g.group_id = values.pop('group_id')
    g.group = Group.query.get(g.group_id)
    g.event_id = values.pop('event_id')
    g.event = Event.query.get(g.event_id)
    g.user = current_user()


def render_event(f, *args, **kwargs):
    """custom render for events"""
    from piipod.views import render
    kwargs.setdefault('group', g.group)
    kwargs.setdefault('event', g.event)
    return render(f, *args, **kwargs)


#########
# EVENT #
#########


@event.route('/')
@login_required
def home():
    """event homepage"""
    return render_event('event/index.html')


@event.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """event edit"""
    form = EventForm(request.form, obj=g.event)
    if request.method == 'POST' and form.validate():
        g.event.update(**request.form).save()
        return redirect(url_for('event.home'))
    return render_event('form.html',
        title='Edit Event',
        submit='save',
        form=form)
