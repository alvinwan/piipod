from flask import Blueprint, request, redirect, url_for, g
from piiipod.views import current_user, login_required
from .forms import GroupForm, GroupSignupForm
from piiipod.event.forms import EventForm
from piiipod.models import Event, Group, Membership, GroupRole
from piiipod.defaults import default_event_roles


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
    from piiipod.views import render
    data = vars(g)
    data.update(kwargs)
    return render(f, *args, **data)


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
    form = EventForm(request.form)
    if request.method == 'POST' and form.validate():
        event = Event.from_request().save().load_roles(
            default_event_roles[g.group.category]).save()
        return redirect(url_for('event.home',
            event_id=g.user.signup(event, 'Owner').event_id))
    form.group_id.default = g.group_id
    form.process()
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
    form = GroupSignupForm(request.form)
    form.role_id.choices = [(r.id, r.name) for r in GroupRole.query.filter_by(
        group_id=g.group.id,
        is_active=True).all()]
    if g.user in g.group:
        return redirect(url_for('group.home', notif=5))
    if request.method == 'POST' and form.validate():
        membership = g.user.join(g.group, role_id=request.form['role_id'])
        return redirect(url_for('group.home'))
    form.group_id.default = g.group.id
    form.user_id.default = g.user.id
    form.process()
    return render_group('form.html',
        title='Signup %s' % group.name,
        submit='Join',
        form=form,
        back=url_for('group.home'))
