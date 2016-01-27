from flask import Blueprint, request, redirect, g
from piiipod.views import current_user, login_required, url_for
from .forms import GroupForm, GroupSignupForm
from piiipod.event.forms import EventForm
from piiipod.models import Event, Group, Membership, GroupRole, GroupSetting
from piiipod.defaults import default_event_roles
from sqlalchemy.orm.exc import NoResultFound


group = Blueprint('group', __name__, url_prefix='/<string:group_url>')


@group.url_defaults
def add_group_id(endpoint, values):
    values.setdefault('group_url', getattr(g, 'group_url', None))


@group.url_value_preprocessor
def pull_group_id(endpoint, values):
    try:
        g.group_url = values.pop('group_url')
        g.group = Group.query.filter_by(url=g.group_url).one()
        g.user = current_user()
        g.event_role = g.signup = None
        if g.user.is_authenticated:
            g.membership = Membership.query.filter_by(
                group_id=g.group.id,
                user_id=g.user.id,
                is_active=True).one_or_none()
            if g.membership:
                g.group_role = GroupRole.query.get(g.membership.role_id)
            else:
                g.group_role = None
        else:
            g.membership = g.group_role = None
    except NoResultFound:
        return 'No such group.'


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
            event_id=g.user.signup(event, 'Owner').event_id,
            event_url=event.url))
    form.group_id.default = g.group.id
    form.process()
    return render_group('form.html',
        title='Create Event',
        submit='Create',
        form=form)


@group.route('/events')
def events():
    """group events"""
    return render_group('group/events.html')


@group.route('/members')
def members():
    """group members"""
    return render_group('group/members.html')


@group.route('/signup', methods=['GET', 'POST'])
@login_required
def signup():
    """group signup"""
    message = ''
    form = GroupSignupForm(request.form)
    choose_role = g.group.setting('choose_role').is_active
    message = 'Thank you for your interest in %s! Just click "Join" to join.' % g.group.name
    whitelisted = []
    for block in g.group.setting('whitelist').value.split(','):
        data = block.split('(')
        if len(data) == 2:
            whitelisted.append((data[0].strip(), data[1].strip()[:-1]))
        else:
            whitelisted.append((data[0].strip(), ''))
    emails = [s.strip() for s, _ in whitelisted]
    if g.user.email in emails:
        title = [title for email, title in whitelisted if email == g.user.email][0]
        message = 'You\'ve been identified as "%s". Hello! Click "Confirm" below, to get started.' % title
    if choose_role:
        form.role_id.choices = [(r.id, r.name) for r in GroupRole.query.filter_by(
            group_id=g.group.id,
            is_active=True).all()]
    else:
        del form.role_id
    if g.user in g.group:
        return redirect(url_for('group.home', notif=5))
    if request.method == 'POST' and form.validate():
        if g.user.email in emails:
            role = {'role': title or 'Authorizer'}
        elif choose_role:
            role = {'role_id': request.form['role_id']}
        else:
            role = {'role': g.group.setting('role').value}
        membership = g.user.join(g.group, **role)
        return redirect(url_for('group.home'))
    form.group_id.default = g.group.id
    form.user_id.default = g.user.id
    form.process()
    return render_group('form.html',
        title='Signup for %s' % g.group.name,
        submit='Join',
        form=form,
        message=message,
        back=url_for('group.home'))

@group.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """edit settings"""
    g.group.setting('whitelist')
    if request.method == 'POST':
        id, value = request.form['id'], request.form['value']
        setting = GroupSetting.query.get(id)
        setting.value = value
        setting.save()
    settings = GroupSetting.query.filter_by(group_id=g.group.id).all()
    return render_group('group/settings.html', settings=settings, back=url_for('group.home'))

################
# LOGIN/LOGOUT #
################

@queue.route('/logout')
def logout():
    from piipod.public.views import logout
    return logout()


@queue.route('/tokenlogin', methods=['POST'])
def token_login():
    from piipod.public.views import token_login
    return token_login()
