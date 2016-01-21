from flask import Blueprint, request, redirect, url_for, g
from piipod.views import current_user, login_required
from .forms import GroupForm, GroupSignupForm
from piipod.event.forms import EventForm
from piipod.models import Event, Group, Membership, GroupRole


group = Blueprint('group', __name__, url_prefix='/g/<int:group_id>')


@group.url_defaults
def add_group_id(endpoint, values):
    values.setdefault('group_id', getattr(g, 'group_id', None))


@group.url_value_preprocessor
def pull_group_id(endpoint, values):
    g.group_id = values.pop('group_id')
    g.group = Group.query.get(g.group_id)
    g.user = current_user()
    if g.user.is_authenticated:
        g.membership = Membership.query.filter_by(
            group_id=g.group_id,
            user_id=g.user.id,
            is_active=True).one_or_none()
        if g.membership:
            g.group_role = GroupRole.query.get(g.membership.role_id)
        else:
            g.group_role = None
    else:
        g.membership = g.group_role = None


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
        event = Event.from_request().save()
        return redirect(url_for('event.home',
            event_id=g.user.signup(event, 'owner')))
    return render_group('form.html',
        title='Create Event',
        submit='Create',
        form=form)


@group.route('/events')
@login_required
def events():
    """group events"""
    return 'events'


@group.route('/signup', methods=['GET', 'POST'])
@login_required
def signup():
    """group signup"""
    form = GroupSignupForm()
    if g.user in g.group:
        return redirect(url_for('group.home', notif=5))
    form.group_id.default = g.group.id
    form.user_id.default = g.user.id
    form.process()
    if request.method == 'POST' and form.validate():
        membership = g.user.join(g.group, 'member')
        return redirect(url_for('group.home'))
    return render_group('form.html',
        title='Signup %s' % group.name,
        submit='Join',
        form=form)
