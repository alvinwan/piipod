from flask import Blueprint, request, redirect, g, abort, jsonify, session
from piipod.views import current_user, login_required, url_for, requires, current_user, current_url
from .forms import GroupForm, GroupSignupForm, ProcessWaitlistsForm, \
    ImportSignupsForm, SyncForm, ConfirmSyncForm
from piipod.event.forms import EventForm
from piipod.forms import choicify
from piipod.models import Event, Group, Membership, GroupRole, GroupSetting,\
    Signup, Membership
from piipod.defaults import default_event_roles, default_group_roles
from sqlalchemy.orm.exc import NoResultFound
import csv
import googleapiclient
from apiclient import discovery
import httplib2
from oauth2client import client
import arrow
import re


group = Blueprint('group', __name__, url_prefix='/<string:group_url>')


@group.url_defaults
def add_group_id(endpoint, values):
    values.setdefault('group_url', getattr(g, 'group_url', None))


@group.url_value_preprocessor
def pull_group_id(endpoint, values):
    try:
        g.group_url = values.pop('group_url')
        g.group = Group.query.filter_by(url=g.group_url).one_or_none()
        if not g.group:
            abort(404)
        g.event_role = g.signup = None
        if current_user().is_authenticated:
            g.membership = Membership.query.filter_by(
                group_id=g.group.id,
                user_id=current_user().id,
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
    from piipod.views import render
    data = vars(g)
    data.update(kwargs)
    return render(f, *args, **data)

################
# PUBLIC PAGES #
################

@group.route('/')
def home():
    """group homepage"""
    return render_group('group/index.html')


@group.route('/events')
def events():
    """group events"""
    return render_group('group/events.html',
        page=int(request.args.get('page', 1)))


@group.route('/members')
def members():
    """group members"""
    return render_group('group/members.html')

##############
# MANAGEMENT #
##############

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

@group.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """edit settings"""
    g.group.load_settings()
    g.group.access_token
    if request.method == 'POST':
        id, value = request.form['id'], request.form['value']
        setting = GroupSetting.query.get(id)
        setting.value = value
        setting.save()
    settings = GroupSetting.query.filter_by(group_id=g.group.id).all()
    return render_group('group/settings.html', settings=settings, back=url_for('group.home'))

##########
# EVENTS #
##########

@group.route('/e/', methods=['GET', 'POST'])
@requires('create_event')
@login_required
def create_event():
    """create event"""
    form = EventForm(request.form)
    if request.method == 'POST' and form.validate():
        event = Event.from_request().save().load_roles(
            default_event_roles[g.group.category]
        ).set_local('start', 'end').save()
        return redirect(url_for('event.home',
            event_id=current_user().signup(event, 'Owner',
                category='Accepted').event_id))
    form.group_id.default = g.group.id
    form.process()
    return render_group('form.html',
        title='Create Event',
        submit='Create',
        form=form,
        back=url_for('group.events'))

@group.route('/process', methods=['GET', 'POST'])
@requires('create_event')
@login_required
def process():
    """process whitelists"""
    form = ProcessWaitlistsForm(request.form)
    if request.method == 'POST' and form.validate():
        pass
    return render_group('form.html',
        title='Process Waitlists',
        submit='Process',
        form=form,
        back=url_for('group.events'))

@group.route('/import/signups', methods=['GET', 'POST'])
@requires('create_event')
@login_required
def import_signups():
    """import signups"""
    form = ImportSignupsForm(request.form)
    if request.method == 'POST' and form.validate():
        signups = list(Signup.from_csv_string(
            request.form['csv'], request.form['override'] == 'y'))
        for signup in signups:
            Membership(group_id=g.group.id, user_id=signup.user_id,
                role_id=GroupRole.query.filter_by(
                    name='Member',
                    group_id=g.group.id).one().id
                ).save()
        return render_group('group/import_signups.html',
            message='All %d signups created.' % len(signups),
            url=url_for('group.events'),
            action='Back',
            signups=signups)
    return render_group('form.html',
        title='Import Signups',
        submit='Import',
        form=form,
        back=url_for('group.events'))

@group.route('/sync/<string:service>', methods=['GET', 'POST'])
@requires('create_event')
@login_required
def sync(service):
    """sync events with service"""
    try:
        form, message = SyncForm(request.form), ''
        setting = g.group.setting(service)
        calendars = setting.value.split(',') if setting.value else []
        form.calendar.choices = choicify(calendars)
        if not calendars:
            message = 'You have no %s to select from! Access the <a href="%s">settings</a> window to add %s IDs.' % (setting.label, url_for('group.settings'), setting.label)
            form = None
        if (request.method == 'POST' and form.validate() and calendars) or 'confirm' in request.form:

            calendarId = request.form['calendar']

            pattern = request.form.get('pattern', '*')
            if pattern != '*':
                pattern = re.compile(request.form['pattern'])

            # TODO: combine with regular login
            if 'credentials' not in session:
                session['redirect'] = current_url()
                return redirect(url_for('public.login'))
            credentials = client.OAuth2Credentials.from_json(session['credentials'])
            if credentials.access_token_expired:
                session['redirect'] = current_url()
                return redirect(url_for('public.login'))
            http_auth = credentials.authorize(httplib2.Http())
            service = discovery.build('calendar', 'v3', http=http_auth)

            all_events = []
            page_token = None
            while True:
              events = service.events().list(calendarId=calendarId.strip(), pageToken=page_token).execute()
              for event in events['items']:
                all_events.append(event)
              page_token = events.get('nextPageToken')
              if not page_token:
                break

            all_events = [e for e in all_events if (pattern == '*' or pattern.match(e.get('summary', 'None'))) and 'start' in e]

            events = [dict(
                name=e.get('summary', '')[:50],
                description=e.get('summary', ''),
                start=arrow.get(
                    e['start'].get('dateTime', e['start'].get('date', None)
                    )).to('local'),
                end=arrow.get(
                    e['end'].get('dateTime', e['start'].get('date', None)
                    )).to('local'),
                google_id=e['id'],
                group_id=g.group.id,
                recurrence=e.get('recurrence', [])
            ) for e in all_events]

            if 'confirm' not in request.form:
                form = ConfirmSyncForm(request.form)
                message = 'Are you sure? %d events will be synced:<br><br> %s' % (len(all_events), '<br>'.join('{name} <span class="subtext">({start} to {end})</span>'.format(
                    name=e['name'],
                    start=e['start'].format('MMM D h:mm a'),
                    end=e['end'].format('MMM D h:mm a')) for e in events))
                return render_group('form.html',
                    title='Confirm Sync',
                    message=message,
                    submit='Sync',
                    form=form,
                    back=url_for('group.events'))

            for event_data in events:
                query = Event.query.filter_by(google_id=event_data['google_id'])
                raw_recurrence = event_data.pop('recurrence')
                if raw_recurrence:
                    recurrence = dict(
                        item.split('=') for item in
                        raw_recurrence[0].split(':')[1].split(';'))
                    event_data.update({
                        'frequency': recurrence.get('FREQ', ''),
                        'until': arrow.get(recurrence.get('UNTIL', ''), 'YYYYMMDD'),
                        'byday': recurrence.get('BYDAY', '')
                    })

                # ['RRULE:FREQ=WEEKLY;UNTIL=20160426T160000Z;BYDAY=TU']
                recurrence_start = arrow.get(request.form['recurrence_start'], 'YYYY-MM-DD HH:mm:ss')
                recurrence_end = arrow.get(request.form['recurrence_end'], 'YYYY-MM-DD HH:mm:ss')

                if not query.count():
                    event = Event(**event_data).save()
                else:
                    event = query.first().update(**event_data).save()

                event_data.pop('google_id')
                event_data['parent_id'] = event.id

                if event.until and recurrence_start < event.until:
                    # TODO: spans are a little dumb
                    span = recurrence_start-event.start
                    start, end = event.start, event.end
                    while start < recurrence_end:
                        if event.frequency == 'DAILY':
                            diff = span.days
                            start = start.replace(days=diff)
                            end = end.replace(days=diff)
                            span = (start.replace(days=1)-start)
                        if event.frequency == 'WEEKLY':
                            diff = span.days // 7
                            start = start.replace(weeks=diff)
                            end = end.replace(weeks=diff)
                            span = start.replace(weeks=1)-start
                        # does not support MONTHLY yet
                        event_data.update({'start': start, 'end': end})
                        if recurrence_start < start < recurrence_end:
                            Event(**event_data).save()

            return redirect(url_for('group.events'))

        return render_group('form.html',
            title='Sync with %s' % setting.label,
            message=message,
            submit='Sync',
            form=form,
            back=url_for('group.events'))
    except AssertionError:
        abort(404)
    except googleapiclient.errors.HttpError:
        form.errors.setdefault('calendar', []).append('Google Calendar failed to load. Wrong link perhaps?')
        return render_group('form.html',
            title='Sync with %s' % setting.label,
            message=message,
            submit='Sync',
            form=form,
            back=url_for('group.events'))

##############
# MEMBERSHIP #
##############

@group.route('/signup', methods=['GET', 'POST'])
@login_required
def signup():
    """group signup"""
    message = ''
    form = GroupSignupForm(request.form)
    choose_role = g.group.setting('choose_role').is_active
    message = 'Thank you for your interest in %s! Just click "Join" to join.' % g.group.name
    whitelisted, submit = [], 'Join'
    for block in g.group.setting('whitelist').value.split(','):
        data = block.split('(')
        if len(data) == 2:
            whitelisted.append((data[0].strip(), data[1].strip()[:-1]))
        else:
            whitelisted.append((data[0].strip(), ''))
    emails = [s.strip() for s, _ in whitelisted]
    if current_user().email in emails:
        title = [title for email, title in whitelisted if email == current_user().email][0]
        message = 'You\'ve been identified as <code>%s</code>. Hello! Click "Confirm" below, to get started.' % title
        if not GroupRole.query.filter_by(group_id=g.group.id, name=title).one_or_none():
            submit = None
            message = 'You\'ve been identified as <code>%s</code>. Hello! However, there is no such role <code>%s</code> in this group - only <code>%s</code>. Please contact your group manager.' % (title, title, str([r.name for r in g.group.roles()]))
    if choose_role:
        form.role_id.choices = [(r.id, r.name) for r in GroupRole.query.filter_by(
            group_id=g.group.id,
            is_active=True).all()]
    else:
        del form.role_id
    if current_user() in g.group:
        return redirect(url_for('group.home', notif=5))
    if request.method == 'POST' and form.validate():
        if current_user().email in emails:
            role = {'role': title or 'Authorizer'}
        elif choose_role:
            role = {'role_id': request.form['role_id']}
        else:
            role = {'role': g.group.setting('role').value}
        membership = current_user().join(g.group, **role)
        return redirect(url_for('group.home'))
    form.group_id.default = g.group.id
    form.user_id.default = current_user().id
    form.process()
    return render_group('form.html',
        title='Signup for %s' % g.group.name,
        submit=submit,
        form=form,
        message=message,
        back=url_for('group.home'))

@group.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    """group leave"""
    Membership.query.filter_by(
        group_id=g.group.id,
        user_id=current_user().id,
        is_active=True
    ).one().deactivate()
    # raise UserWarning(Membership.query.filter_by(
    #     group_id=g.group.id,
    #     user_id=current_user().id).one().is_active)
    return redirect(url_for('group.home'))

@group.route('/u/<int:user_id>')
def member(user_id):
    """Displays information about member"""
    g.membership = Membership.query.filter_by(group_id=g.group.id, user_id=user_id).one_or_none()
    if not g.membership:
        abort(404)
    return render_group('group/member.html',
        membership=g.membership)

################
# LOGIN/LOGOUT #
################

@group.route('/logout')
def logout():
    from piipod.public.views import logout
    return logout()


@group.route('/login', methods=['POST', 'GET'])
def login():
    from piipod.public.views import login
    return login()


@group.route('/tokenlogin', methods=['POST'])
def token_login():
    from piipod.public.views import token_login
    return token_login()

@group.route('/whitelist/<string:access_token>')
@group.route('/whitelist/<string:group>/<string:access_token>')
def whitelist(access_token, group=None):
    """Endpoint for group whitelist of emails"""
    if access_token == g.group.access_token:
        terms = []
        for term in g.group.setting('whitelist').value.split(','):
            pieces = term.split('(')
            if len(pieces) == 2:
                terms.append({'email': pieces[0], 'position': pieces[1][:-1]})
            elif len(pieces) == 1 and pieces[0]:
                default_role = default_group_roles[g.group.category][-1]['name']
                terms.append({'email': pieces[0], 'position': default_role})
            else:
                continue
        return jsonify({'data': terms})
    abort(404)
