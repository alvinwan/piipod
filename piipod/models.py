"""
Important: Changes here need to be followed by `make refresh`.
"""
from piipod import db, tz
from flask import request, g
from sqlalchemy import types, desc, asc
from sqlalchemy.orm import relationship
from sqlalchemy_utils import PasswordType, ArrowType
from passlib.context import CryptContext
from piipod.defaults import default_event_settings, default_group_settings, \
    default_user_settings
import sqlalchemy
import arrow
import csv
import flask_login
import pymysql


class Base(db.Model):
    """Base Model for all other models"""

    __abstract__ = True

    __access_token = None
    __context = CryptContext(schemes=['pbkdf2_sha512'])

    id = db.Column(db.Integer, primary_key=True)
    updated_at = db.Column(ArrowType)
    updated_by = db.Column(db.Integer)
    created_at = db.Column(ArrowType, default=arrow.now('US/Pacific'))
    created_by = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)

    @property
    def entity(self):
        """Returns entity name"""
        return self.__class__.__name__.lower()

    @property
    def access_token(self):
        """Generate token"""
        if not self.__access_token:
            self.__access_token = self.generate_access_token()
        return self.__access_token

    @staticmethod
    def random_hash():
        """Generates random hash"""
        return Base.hash(str(arrow.now()))

    @staticmethod
    def hash(value):
        """Hashes value"""
        return Base.__context.encrypt(value)

    @classmethod
    def from_request(cls):
        """Create object from request"""
        return cls(**dict(request.form.items()))

    def update(self, **kwargs):
        """Update object with kwargs"""
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def modify_time(self, *fields, act=lambda t: t):
        """Modify times"""
        for field in fields:
            setattr(self, field, act(getattr(self, field)))
        return self

    def to_local(self, *fields):
        """Convert all to local times"""
        return self.modify_time(*fields, act=lambda t: t.to(tz or 'local'))

    def to_utc(self, *fields):
        """Convert all to UTC times"""
        return self.modify_time(*fields, act=lambda t: t.to('utc'))

    def set_tz(self, *fields, tz):
        """Set timezones of current times to be a specific tz"""
        return self.modify_time(*fields,
            act=lambda t: t.replace(tzinfo=tz))

    def set_local(self, *fields):
        """Set timezones of current times to be local time"""
        from dateutil import tz as t
        return self.set_tz(*fields, tz=t.gettz(tz) if tz else t.tzlocal())

    def save(self):
        """Save object"""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self):
        """
        Delete object
        Use deactivate where possible.
        """
        try:
            db.session.delete(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise UserWarning(str(e))

    def setting(self, name):
        """Get Setting by name"""
        assert name in self.__defaultsettings__, 'Not a valid setting'
        key = {'%s_id' % self.entity: self.id}
        setting = self.__settingclass__.query.filter_by(
            name=name,
            **key).one_or_none()
        if not setting:
            setting = self.load_setting(name)
        default_description = self.__defaultsettings__[name].get('description', None)
        # Note: This doesn't actually take effect on the settings page - only when the setting is loaded.
        if setting.description != default_description:
            setting.update(description=default_description).save()
        return setting

    def load_setting(self, name):
        """load a setting"""
        key = {'%s_id' % self.entity: self.id}
        key.update(self.__defaultsettings__[name])
        key.setdefault('name', name)
        key.setdefault('type', str)
        key['type'] = str(key['type'])
        return self.__settingclass__(
            **key).save()

    def load_settings(self, *names):
        """load a series of settings"""
        if not names:
            return [self.setting(k) for k in self.__defaultsettings__]
        return [self.setting(n) for n in names]

    def deactivate(self):
        """deactivate"""
        return self.update(is_active=False).save()

    def activate(self):
        """activate"""
        return self.update(is_active=True).save()

    def load_roles(self, roles):
        """load role settings"""
        RoleClass = {
            'event': EventRole,
            'group': GroupRole
        }[self.entity]
        for role in roles:
            filt = {
                'name': role['name'],
                '%s_id' % self.entity: self.id
            }
            if not RoleClass.query.filter_by(**filt).one_or_none():
                role = role.copy()
                role.setdefault('%s_id' % self.entity, self.id)
                RoleClass(**role).save()
        return self

    def generate_access_token(self):
        """Generates access token"""
        key = {'%s_id' % self.entity: self.id}
        return (self.__settingclass__.query.filter_by(
            name='access_token',
            **key
        ).order_by(desc(self.__settingclass__.id)).first() or self.__settingclass__(
            name='access_token',
            value=self.random_hash(),
            label='Access Token',
            description='for integrating with other services',
            **key
        ).save()).value

    @classmethod
    def get_or_create(cls, data={}, override=False, **filter_by):
        """Get or create user by email"""
        obj = cls.query.filter_by(**filter_by).one_or_none()
        if override and obj:
            data = {k: v for k,v in data.items() if not k.endswith('_id')}
            return obj.update(**data).save()
        filter_by.update(data)
        return obj or cls(**filter_by).save()


class Setting(Base):
    """base setting model"""

    __abstract__ = True

    name = db.Column(db.String(100))
    label = db.Column(db.String(100))
    description = db.Column(db.Text)
    value = db.Column(db.Text)
    type = db.Column(db.String(50))
    toggable = db.Column(db.Boolean, default=True)


class Role(Base):
    """base role model (<- hahaha. punny)"""

    __abstract__ = True

    name = db.Column(db.String(100))
    permissions = db.Column(db.Text)

    def all_permissions(self):
        return [s.strip() for s in self.permissions.split(',')]


############
# ENTITIES #
############


class UserSetting(Setting):
    """settings for a PIAP user"""

    __tablename__ = 'user_setting'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(Base, flask_login.UserMixin):
    """PIAP system user"""

    __tablename__ = 'user'
    __settingclass__ = UserSetting
    __defaultsettings__ = default_user_settings

    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']))
    settings = relationship("UserSetting", backref="user")
    image_url = db.Column(db.Text)
    google_id = db.Column(db.String(30), unique=True)
    signups = db.relationship('Signup', backref="user")

    def groups(self):
        """All groups for this user"""
        return Group.query.join(Membership).filter_by(user_id=self.id).all()

    def join(self, group, role=None, role_id=None):
        """Join a group"""
        assert group.id, 'Save group object first'
        assert isinstance(group, Group), 'Can only join group.'
        try:
            role_id = role_id or GroupRole.query.filter_by(
                name=role,
                group_id=group.id
            ).one().id
            return Membership(
                user_id=self.id,
                group_id=group.id,
                role_id=role_id).save()
        except sqlalchemy.orm.exc.NoResultFound:
            raise UserWarning('No such group role "%s" found!' % role)

    def signup(self, event, role=None, role_id=None, **kwargs):
        """Signup for an event"""
        assert event.id, 'Save event object first'
        assert isinstance(event, Event), 'Can only signup for events.'
        signup = Signup.query.filter_by(
            user_id=self.id,
            event_id=event.id
        ).one_or_none()
        role = EventRole.query.filter_by(
            name=role,
            event_id=event.id
        ).one_or_none()
        if not role_id:
            if role:
                role_id = role.id
            else:
                role_id = EventRole(name=role, event_id=event.id).save().id
        if signup:
            return signup.update(
                role_id=role_id, is_active=True, **kwargs).save()
        return Signup(
            user_id=self.id,
            event_id=event.id,
            role_id=role_id,
            **kwargs).save()

    def leave(self, event):
        """Leave an event"""
        signup = Signup.query.filter_by(
            user_id=self.id,
            event_id=event.id,
            is_active=True
        ).one_or_none()
        if signup:
            return signup.deactivate()

    def checkin(self, event, authorizer):
        """Checkin for an event"""
        return Checkin(
            authorizer_id=authorizer.id,
            user_id=self.id,
            event_id=event.id).save()

    def get_permission(self, category):
        """Returns permission for object"""
        try:
            if category == 'event':
                return EventRole.query.join(Signup).filter_by(
                    event_id=g.event.id,
                    user_id=self.id
                ).one_or_none().all_permissions()
            if category == 'group':
                return GroupRole.query.join(Membership).filter_by(
                    user_id=self.id,
                    group_id=g.group.id
                ).one_or_none().all_permissions()
            return []
        except AttributeError:
            return []

    def permissions(self, include=('event', 'group')):
        """get all permissions"""
        return sum([self.get_permission(r) for r in include], [])

    def can(self, permission, include=('event', 'group')):
        """Check if user has the given permission"""
        permissions = self.permissions(include)
        if '*' in permissions or permission in permissions:
            return True
        return False

    @property
    def num_active_signups(self):
        """Number of active signups"""
        return Signup.query.join(Event).filter(
            Signup.user_id == self.id,
            Event.start >= arrow.now()
        ).count()

    @property
    def num_waitlisted_signups(self):
        """Number of active signups"""
        return Signup.query.join(Event).filter(
            Signup.user_id == self.id,
            Event.start >= arrow.now(),
            Signup.category == 'Waitlisted'
        ).count()

    @property
    def num_non_waitlisted_signups(self):
        """Number of active signups"""
        return Signup.query.join(Event).filter(
            Signup.user_id == self.id,
            Event.start >= arrow.now(),
            Signup.category != 'Waitlisted'
        ).count()


class GroupSetting(Setting):
    """settings for a PIAP group"""

    __tablename__ = 'group_setting'

    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))


class GroupRole(Role):
    """roles for group membership"""

    __tablename__ = 'group_role'

    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))


class Group(Base):
    """A PIAP group can be any form or sort of organization."""

    __tablename__ = 'group'
    __settingclass__ = GroupSetting
    __defaultsettings__ = default_group_settings

    name = db.Column(db.String(50))
    url = db.Column(db.String(30), unique=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    events = db.relationship('Event', backref='group', lazy='dynamic')
    settings = relationship("GroupSetting", backref="group")

    @property
    def num_events(self):
        """Number of events"""
        return Event.query.filter_by(group_id=self.id, is_active=True).count()

    def events(self, start, end):
        """Returns events between start and end"""
        return Event.query.filter(
            Event.group_id==self.id,
            Event.is_active==True,
            Event.start > start,
            Event.start < end).order_by(asc(Event.start)).all()

    def members(self, page=1, per_page=10, paginated=True):
        """List of all members"""
        pagination = Membership.query.filter_by(group_id=self.id).paginate(page, per_page)
        return pagination if paginated else pagination.items

    def setting_query(self):
        return GroupSetting.query.filter_by(group_id=self.id)

    def __contains__(self, user):
        """Tests if user is in group"""
        return Membership.query.filter_by(
            user_id=user.id,
            group_id=self.id,
            is_active=True
        ).one_or_none() is not None

    def current_events(self):
        """Fetch all events happening right now."""
        return Event.query.filter(
            Event.start <= arrow.now(tz or 'local').replace(hours=2),
            Event.end >= arrow.now(tz or 'local').replace(hours=-2),
            Event.group_id==self.id,
            Event.is_active==True
        ).all()

    def roles(self):
        """Returns all GroupRoles"""
        return GroupRole.query.filter_by(group_id=self.id, is_active=True).all()


class EventSetting(Setting):
    """settings for a PIAP event"""

    __tablename__ = 'event_setting'

    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))


class EventRole(Role):
    """roles for event membership"""

    __tablename__ = 'event_role'

    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))


class Event(Base):
    """PIAP event"""

    __tablename__ = 'event'
    __settingclass__ = EventSetting
    __defaultsettings__ = default_event_settings

    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    start = db.Column(ArrowType)
    end = db.Column(ArrowType)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    google_id = db.Column(db.String(50), unique=True)
    settings = relationship("EventSetting", backref="event")
    checkins = relationship("Checkin", backref="event")
    frequency = db.Column(db.String(20))
    byday = db.Column(db.String(10))
    until = db.Column(ArrowType)

    @property
    def group(self):
        return Group.query.get(self.group_id)

    @property
    def signups(self):
        """Returns all participants"""
        return Signup.query.filter_by(
            event_id=self.id,
            is_active=True).all()

    def signups_by_category(self, **kwargs):
        """Returns all accepted participants"""
        if kwargs['category'] == '*':
            kwargs.pop('category')
        return Signup.query.filter_by(
            event_id=self.id,
            is_active=True,
            **kwargs).all()

    @property
    def num_signups(self):
        """number of signups"""
        return int(Signup.query.filter_by(
            event_id=self.id,
            is_active=True).count())

    @property
    def categories(self):
        """all event categories"""
        return [s.strip().split('(')[0] for s in g.event.setting('categories').value.split(',')] + ['Accepted', 'Waitlisted']

    @property
    def category_defaults(self):
        """all event categories"""
        counts = [('Accepted', 0), ('Waitlisted', 0)]
        for s in g.event.setting('categories').value.split(','):
            data = s.strip().split('(')
            if len(data) > 1:
                counts.append((data[0], int(data[1][:-1])))
            else:
                counts.append((data[0], 0))
        return counts

    @property
    def category_counts(self):
        """all event categories"""
        counts = []
        for s in g.event.setting('categories').value.split(',') + ('Accepted', 'Waitlisted'):
            category = s.strip().split('(')[0]
            counts.append((category, Signup.query.filter_by(
                category=category,
                is_active=True,
                event_id=self.id
            )))
        return counts

    def __contains__(self, user):
        """Check if user is in signups"""
        if not user.is_authenticated:
            return False
        return Signup.query.filter_by(
            user_id=user.id,
            event_id=self.id,
            is_active=True
        ).one_or_none() is not None

    @property
    def num_non_waitlisted_signups(self):
        """Number of active signups"""
        return Event.query.join(Signup).filter(
            Event.id == self.id,
            Event.start >= arrow.now(),
            Signup.category != 'Waitlisted',
            Signup.is_active == True
        ).count()

    @classmethod
    def range(cls, event_start, event_end, shift_duration, shift_alignment):
        """Returns an iterable of time spans"""
        def start(i=None):
            """generates iterable of time spans in shift_duration from start"""
            i = i or event_start
            j = i.replace(minutes=shift_duration)
            while i < event_end:
                if i >= event_end:
                    raise StopIteration
                if j > event_end:
                    j = event_end
                yield i, j
                i = j
                j = j.replace(minutes=shift_duration)

        def hour():
            """generates iterable of time spans per hour from start"""
            i, j = event_start, event_start.replace(minutes=shift_duration)
            if i.floor('hour') != i:
                j = event_start.replace(hours=1).floor('hour')
            yield i, j
            for i, j in start(j):
                yield i, j

        return locals()[shift_alignment.lower()]()

    @classmethod
    def split(cls, event_data, shift_duration, shift_alignment):
        """
        Splits and saves event as a series of shifts
        :param event_data: dictionary of event attributes
        :param shift_duration: time in minutes
        :param shift_alignment: HOUR, START, END
        """
        if shift_duration == 0:
            return Event(**event_data).save()
        return [Event(**event_data).update(start=i, end=j).save()
            for i, j in Event.range(
                event_data['start'], event_data['end'],
                shift_duration, shift_alignment)]


    def split_existing(self, event_data, shift_duration, shift_alignment):
        """
        Splits and saves existing event
        :param event_data: dictionary of event attributes
        :param shift_duration: time in minutes
        :param shift_alignment: HOUR, START, END
        """
        if shift_duration == 0:
            return Event(**event_data).save()

        span_range = Event.range(
            event_data['start'], event_data['end'],
            shift_duration, shift_alignment)

        # modify existing event to match shift
        i, j = next(span_range)
        self.update(start=i, end=j).save()

        # create all other events
        event_data['parent_id'] = self.id
        event_data.pop('google_id', '')
        return [self] + [Event(**event_data).update(start=i, end=j).save()
            for i, j in span_range]

########################
# RELATIONSHIP TABLES #
#######################


class Checkin(Base):
    """checkin for event"""

    __tablename__ = 'checkin'

    authorizer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))

    @property
    def authorizer(self):
        """authorizing user"""
        return User.query.get(self.authorizer_id)


class Signup(Base):
    """user signup for event"""

    __tablename__ = 'signup'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('event_role.id'))
    category = db.Column(db.String(50))
    status = db.Column(db.String(50))
    preference = db.Column(db.Integer)
    comment = db.Column(db.Text)

    @property
    def event(self):
        return Event.query.get(self.event_id)

    @property
    def user(self):
        return User.query.get(self.user_id)

    @property
    def role(self):
        return EventRole.query.get(self.role_id)

    @property
    def is_checked_in(self):
        return Checkin.query.filter_by(
            user_id=self.user_id,
            event_id=self.event_id).count() > 0

    @property
    def num_check_ins(self):
        return Checkin.query.filter_by(
            user_id=self.user_id,
            event_id=self.event_id).count()

    @classmethod
    def from_csv_string(cls, string, override=False):
        """Import signups from csv"""
        try:
            reader = csv.reader(string.splitlines(), delimiter=',')
            headers = [s.strip() for s in next(reader)]
            for row in reader:
                if ''.join(row).strip() == '':
                    continue
                data = dict(zip(headers, [s.strip() for s in row]))
                user_data = {}
                for k in list(data.keys()):
                    if k.startswith('user_'):
                        user_data[k[5:]] = data.pop(k)
                user = User.get_or_create(email=user_data['email'], data=user_data)
                event_id = data.pop('event_id', None)
                event_ids = data.pop('event_ids', None)
                if event_ids:
                    event_ids = [int(s.strip()) for s in event_ids[1:-1].split('|') if s]
                elif event_id:
                    event_ids = [event_id]
                else:
                    raise UserWarning('Must specify an event_id or event_ids col.')
                for event_id in event_ids:
                    event = Event.query.get(event_id)
                    role = EventRole.query.filter_by(name=event.setting('role').value, event_id=event_id).one()
                    data['is_active'] = True
                    yield Signup.get_or_create(user_id=user.id, event_id=event_id, override=override, role_id=role.id, data=data)
        except sqlalchemy.exc.IntegrityError:
            raise UserWarning('Invalid event_id found. Check that all event_ids are associated with valid events.')


class Membership(Base):
    """user membership in group"""

    __tablename__ = 'membership'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('group_role.id'))

    # TODO: restrict to signups that belong to a specific group
    def signups(self):
        """Returns signups for this membership"""
        return Signup.query.filter_by(
            user_id=self.user_id,
            is_active=True).all()

    def save(self):
        """save membership"""
        if not Membership.query.filter(
            Membership.user_id == self.user_id,
            Membership.group_id == self.group_id
        ).one_or_none():
            return super(Membership, self).save()
        return self

    @property
    def group(self):
        return Group.query.get(self.group_id)

    @property
    def user(self):
        return User.query.get(self.user_id)

    @property
    def role(self):
        return GroupRole.query.get(self.role_id)
