from flask import Blueprint, request, redirect, g, abort, jsonify, session
from piipod.views import current_user, login_required, url_for, requires, current_user, current_url
from .forms import GroupForm, GroupSignupForm, ProcessWaitlistsForm, \
    ImportSignupsForm, SyncForm, ConfirmSyncForm, DeleteEventsEnMasse
from piipod.event.forms import EventForm
from piipod.forms import choicify
from piipod.models import Event, Group, Membership, GroupRole, GroupSetting,\
    Signup, Membership, Checkin, User
from piipod.defaults import default_event_roles, default_group_roles
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import update, and_
from piipod import db
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

@group.route('/events/<string:start>')
@group.route('/events')
def events(start=None):
    """group events"""
    if not start:
        now = arrow.now()
    else:
        now = arrow.get(start, 'YYYYMMDD')
    begin, end = now.floor('week'), now.ceil('week')
    dows = [begin.replace(days=i) for i in range(7)]
    events, events_by_dow = g.group.events(begin, end), {}
    for event in events:
        events_by_dow.setdefault(event.to_local('start','end').start.format('d'), []).append(event)
    return render_group('group/events.html', dows=dows, events=events_by_dow,
        now=now)


@group.route('/members')
def members():
    """group members"""
    return render_group('group/members.html',
        page=int(request.args.get('page', 1)))

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
    return render_group('group/form.html',
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
        id = request.form['id']
        value = request.form.get('value', None)
        is_active = request.form.get('is_active', None)
        setting = GroupSetting.query.get(id)
        if value:
            setting.value = value
        if is_active is not None:
            setting.is_active = is_active
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
    form.start.default = arrow.now().floor('hour').to('local')
    form.end.default = form.start.default.replace(hours=1)
    form.process()
    return render_group('group/form.html',
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
    return render_group('group/form.html',
        title='Process Waitlists',
        submit='Process',
        form=form,
        back=url_for('group.events'))

##########
# EVENTS #
##########

@group.route('/import/signups', methods=['GET', 'POST'])
@requires('create_event')
@login_required
def import_signups():
    """import signups"""
    form = ImportSignupsForm(request.form)
    if request.method == 'POST' and form.validate():
        signups = list(Signup.from_csv_string(
            request.form['csv'], request.form.get('override', 'n') == 'y'))
        for signup in signups:
            if not Membership.query.filter_by(group_id=g.group.id, user_id=signup.user_id).count():
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
    return render_group('group/form.html',
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
        form, message = SyncForm(request.form), 'See fields below for instructions.'
        setting = g.group.setting(service)
        calendars = setting.value.split(',') if setting.value else []
        form.calendar.choices = choicify(calendars)
        form.recurrence_start.default = arrow.now().to('local')
        form.recurrence_end.default = arrow.now().to('local').replace(weeks=1)
        if not calendars:
            message = 'You have no %s to select from! Access the <a href="%s#%s">settings</a> window to add %s IDs.' % (setting.label, url_for('group.settings'), setting.name, setting.label)
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
                return render_group('group/form.html',
                    wide_title=True,
                    form_title='Confirm Sync',
                    form_message=message,
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
                shift_duration = int(request.form['shift_duration'])
                shift_alignment = request.form['shift_alignment']

                if not query.count():
                    event = Event(**event_data).save()
                else:
                    event = query.first().update(**event_data).save()
                if shift_duration:
                    event.deactivate()

                event_data.pop('google_id', '')
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
                        if recurrence_start < start < recurrence_end:
                            event_data.update({'start': start, 'end': end})
                            Event.split(
                                event_data, shift_duration, shift_alignment)

            return redirect(url_for('group.events'))
        if form:
            form.process()
        return render_group('group/form.html',
            wide_title=True,
            form_title='Sync with %s' % setting.label,
            form_description=message,
            submit='Sync',
            form=form,
            back=url_for('group.events'))
    except AssertionError:
        abort(404)
    except googleapiclient.errors.HttpError:
        form.errors.setdefault('calendar', []).append('Google Calendar failed to load. Wrong link perhaps?')
        return render_group('group/form.html',
            title='Sync with %s' % setting.label,
            message=message,
            submit='Sync',
            form=form,
            back=url_for('group.events'))

@group.route('/events/delete', methods=['POST', 'GET'])
@requires('create_event')
@login_required
def delete_events():
    """delete events en masse"""
    form = DeleteEventsEnMasse(request.form)
    if request.method == 'POST' and form.validate():
        start_id = request.form['start_id']
        end_id = request.form['end_id']
        events = Event.__table__
        db.session.execute(update(events).where(and_(events.c.id <= end_id,
            events.c.id >= start_id,
            events.c.group_id == g.group.id)).values(is_active=False))
        db.session.commit()
        return redirect(url_for('group.events'))
    return render_group('group/form.html',
        title='Delete Events En Masse',
        message='Be careful! This en masse is not undo-able.',
        submit='Delete',
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
    whitelisted, submit = [], 'Confirm'
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
    return render_group('group/form.html',
        form_title='Signup for %s' % g.group.name,
        form_description='Ready to join? Click confirm below.',
        wide_title=True,
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

    user = User.query.get(user_id)
    g.membership = Membership.query.filter_by(group_id=g.group.id, user_id=user_id).one_or_none()

    if not g.membership and user_id == current_user():
        return render_group('confirm.html',
            back=url_for('group.home'),
            title='Create Profile?',
            message='You have not yet joined this group. Click below to join now!',
            action='Join',
            url=url_for('group.signup'))

    checkins = Event.query.join(Checkin).filter(
        Checkin.user_id==user_id,
        Event.group_id==g.group.id)

    # naiive way of counting hours - need a query to do this!
    hours = 0.0
    for event in checkins:
        hours += (event.end - event.start).seconds / 3600.0

    return render_group('group/member.html',
        membership=g.membership, user=user, total_checkins=checkins.count(), total_hours=hours)

################
# LOGIN/LOGOUT #
################

@group.route('/login', methods=['POST', 'GET'])
def login():
    """Login using globally defined login procedure"""
    from piipod.public.views import login
    return login(
        home=url_for('group.home', _external=True),
        login=url_for('group.login', _external=True))

@group.route('/logout')
def logout():
    """Logout using globally defined logout procedure"""
    from piipod.public.views import logout
    return logout(home=url_for('group.home', _external=True))

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
