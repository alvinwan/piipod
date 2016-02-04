from flask import Blueprint, render_template, request, redirect, g
from piipod.views import current_user, login_required, url_for, requires, current_user
from .forms import EventForm, EventSignupForm, EventCheckinForm, \
    EventGenerateCodeForm, ProcessWaitlistForm, RecategorizeForm
from piipod.models import Group, Event, User, UserSetting, Membership, Signup,\
    GroupRole, EventRole, Base, EventSetting
from piipod.forms import choicify
from sqlalchemy.orm.exc import NoResultFound
from piipod.defaults import default_user_settings, default_event_settings
import arrow


event = Blueprint('event', __name__,
    url_prefix='/<string:group_url>/e/<int:event_id>')


@event.url_defaults
def add_ids(endpoint, values):
    values.setdefault('group_url', getattr(g, 'group_url', None))
    values.setdefault('event_id', getattr(g, 'event_id', None))


@event.url_value_preprocessor
def pull_ids(endpoint, values):
    try:
        g.group_url = values.pop('group_url')
        g.group = Group.query.filter_by(url=g.group_url).one_or_none()
        g.event_id = values.pop('event_id')
        g.event = Event.query.get(g.event_id)
        if not g.group or not g.event:
            abort(404)
        g.event.to_local('start', 'end')
        if current_user().is_authenticated:
            g.membership = Membership.query.filter_by(
                group_id=g.group.id,
                user_id=current_user().id,
                is_active=True).one_or_none()
            if g.membership:
                g.group_role = GroupRole.query.get(g.membership.role_id)
            else:
                g.group_role = None
            g.signup = Signup.query.filter_by(
                event_id=g.event.id,
                user_id=current_user().id,
                is_active=True).one_or_none()
            if g.signup:
                if g.signup.role_id:
                    g.event_role = EventRole.query.get(g.signup.role_id)
                else:
                    role = EventRole.query.filter_by(event_id=g.event.id, name=g.event.setting('role').value).one()
                    g.signup.update(role_id=role.id).save()
                    g.event_role = role
            else:
                g.event_role = None
        else:
            g.membership = g.signup = g.group_role = g.event_role = None
    except NoResultFound:
        abort(404)


def render_event(f, *args, **kwargs):
    """custom render for events"""
    from piipod.views import render
    data = vars(g)
    data.update(kwargs)
    return render(f, *args, **data)


################
# PUBLIC PAGES #
################


@event.route('/')
def home():
    """event homepage"""
    signups = g.event.signups
    categories = {}
    for signup in signups:
        categories.setdefault(signup.category, []).append(signup)
    return render_event('event/index.html', categories=categories)


@event.route('/signup', methods=['GET', 'POST'])
@login_required
def signup():
    """event signup"""
    form = EventSignupForm(request.form)
    message = ''
    choose_role = g.event.setting('choose_role').is_active
    whitelisted = []
    for block in g.group.setting('whitelist').value.split(','):
        data = block.split('(')
        if len(data) == 2:
            whitelisted.append((data[0].strip(), data[1].strip()[:-1]))
        else:
            whitelisted.append((data[0].strip(), ''))
    emails = [s.strip() for s, _ in whitelisted]
    if current_user().email in emails:
        title = [title for email, title in whitelisted if email == current_user().email][0]
        message = 'You\'ve been identified as "%s". Hello! Click "Confirm" below, to get started.' % title
    roles = EventRole.query.filter_by(
        event_id=g.event.id,
        is_active=True).all()
    if choose_role:
        form.role_id.choices = [(r.id, r.name) for r in roles]
    else:
        del form.role_id
    if current_user() in g.event:
        return redirect(url_for('event.home', notif=7))
    if request.method == 'POST' and form.validate():
        data = {'category': g.event.setting('default_category').value }
        if current_user().email in emails:
            if title not in [r.name for r in roles]:
                title = 'Authorizer'
            data['role'] = title or 'Authorizer'
        elif choose_role:
            data['role_id'] = request.form['role_id']
        else:
            data['role'] = g.event.setting('role').value
        signup = current_user().signup(g.event, **data)
        return redirect(url_for('event.home'))
    form.event_id.default = g.event.id
    form.user_id.default = current_user().id
    form.process()
    return render_event('form.html',
        title='Signup for %s' % event.name,
        submit='Confirm',
        form=form,
        message=message,
        back=url_for('event.home'))


@event.route('/signup/<int:signup_id>/accept')
@requires('authorize')
@login_required
def accept_signup(signup_id):
    """Accept signup (pull off of waitlist)"""
    try:
        Signup.query.get(signup_id).update(category='Accepted').save()
        return redirect(url_for('event.home'))
    except NoResultFound:
        abort(404)

@event.route('/signup/<int:signup_id>/deactivate')
@login_required
def deactivate_signup(signup_id):
    """Deactivate signup"""
    try:
        signup = Signup.query.get(signup_id)
        if not signup.user.id == current_user().id and not current_user().can('authorize'):
            raise UserWarning('Not allowed to delete other signups.')
        signup.update(is_active=False).save()
        return redirect(url_for('event.home'))
    except NoResultFound:
        abort(404)

@event.route('/signup/<int:signup_id>/checkin')
@login_required
@requires('authorize')
def checkin_signup(signup_id):
    """checkin signup"""
    try:
        signup = Signup.query.get(signup_id)
        checkin = signup.user.checkin(g.event, current_user())
        return redirect(url_for('event.home'))
    except NoResultFound:
        abort(404)

@event.route('/signup/<int:signup_id>/recategorize', methods=['POST', 'GET'])
@requires('authorize')
@login_required
def recategorize_signup(signup_id):
    """Deactivate signup"""
    try:
        signup = Signup.query.get(signup_id)
        form = RecategorizeForm(request.form)
        form.category.choices = choicify(g.event.categories)
        if request.method == 'POST' and form.validate():
            signup.update(category=request.form['category']).save()
            return redirect(url_for('event.home'))
        return render_event('form.html',
            title='Recategorize Signup',
            form=form,
            message='Assign the signup to a new category',
            submit='Recategorize')
    except NoResultFound:
        abort(404)

@event.route('/leave')
@login_required
def leave():
    """leave event"""
    current_user().leave(g.event)
    return redirect(url_for('group.events'))


@event.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    """event checkin"""
    message = ''
    form = EventCheckinForm(request.form)
    if request.method == 'POST' and form.validate():
        setting = UserSetting.query.filter_by(
            name='authorize_code',
            value=request.form['code'].strip(),
            is_active=True).one_or_none()
        if setting:
            checkin = current_user().checkin(g.event, setting.user)
            return redirect(url_for('event.home', notif=8))
        message = 'Authorization failed.'
    form.event_id.default = g.event.id
    form.user_id.default = current_user().id
    form.process()
    return render_event('form.html',
        title='Checkin for %s' % event.name,
        message=message,
        submit='Checkin',
        form=form)

#########
# STAFF #
#########

@event.route('/authorize', methods=['GET', 'POST'])
@login_required
def authorize():
    """event authorization (for checkin)"""
    form = EventGenerateCodeForm(request.form)
    setting = current_user().setting('authorize_code')
    n = 25
    if (request.method == 'POST' and form.validate()) or setting.value == default_user_settings['authorize_code']['value'] or UserSetting.query.filter_by(value=setting.value).count() > 1:
        setting.value = Base.hash(request.form.get('value', str(arrow.now()))
            )[n:n+int(request.form.get('length', 5))]
        setting.save()
    message = 'Current code: %s' % setting.value
    return render_event('form.html',
        title='Authorization Code for %s' % event.name,
        message=message,
        submit='Regenerate',
        form=form,
        back=url_for('event.home'))

##############
# MANAGEMENT #
##############

@event.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """event edit"""
    form = EventForm(request.form, obj=g.event)
    if request.method == 'POST' and form.validate():
        g.event.update(**request.form).save().set_local('start', 'end').save()
        return redirect(url_for('event.home'))
    return render_event('form.html',
        title='Edit Event',
        submit='save',
        form=form)

@event.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """edit settings"""
    g.event.load_settings()
    settings = EventSetting.query.filter_by(event_id=g.event.id).all()
    if request.method == 'POST':
        _id = request.form['id']
        value = request.form.get('value', None)
        is_active = request.form.get('is_active', None)
        setting = EventSetting.query.get(int(_id))
        if value is not None:
            setting.update(value=value).save()
        if is_active is not None:
            setting.update(is_active=is_active == 'y').save()
    return render_event('event/settings.html', settings=settings)

@event.route('/process', methods=['GET', 'POST'])
@requires('create_event')
@login_required
def process():
    """process whitelist"""
    form = ProcessWaitlistForm(request.form)
    if request.method == 'POST' and form.validate():
        pass
    return render_event('form.html',
        title='Process Waitlist',
        submit='Process',
        form=form)

@event.route('/delete')
@requires('create_event')
@login_required
def delete():
    """delete event"""
    g.event.deactivate()
    return redirect(url_for('group.events'))


@event.route('/restore')
@requires('create_event')
@login_required
def restore():
    """restore deleted event"""
    g.event.activate()
    return redirect(url_for('group.events'))
