"""
Important: Changes here need to be followed by `make refresh`.
"""
from piipod import db
from flask import request, g
from sqlalchemy import types, desc
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base, AbstractConcreteBase
from sqlalchemy_utils import PasswordType, ArrowType
from passlib.context import CryptContext
import arrow
import flask_login


class Base(db.Model):
    """Base Model for all other models"""

    __abstract__ = True

    __access_token = None
    __context = CryptContext(schemes=['pbkdf2_sha512'])

    id = db.Column(db.Integer, primary_key=True)
    updated_at = db.Column(ArrowType)
    updated_by = db.Column(db.Integer)
    created_at = db.Column(ArrowType, default=arrow.utcnow())
    created_by = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)
        self.entity = self.__class__.__name__.lower()

    @property
    def access_token(self):
        """Generate token"""
        if not self.__access_token:
            self.__access_token = self.generate_access_token()
        return self.__access_token

    def random_hash(self):
        """Generates random hash"""
        return self.__context.encrypt(str(arrow.utcnow()))

    @classmethod
    def from_request(cls):
        """Create object from request"""
        return cls(**dict(request.form.items())).save()

    def update(self, **kwargs):
        """Update object with kwargs"""
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def save(self):
        """Save object"""
        db.session.add(self)
        db.session.commit()
        return self

    def setting(self, shortname):
        """Get setting by shortname"""
        return self.__settingclass__.query.filter_by(shortname=shortname).one()

    def deactivate(self):
        """deactivate"""
        self.is_active = False
        return self.save()

    def activate(self):
        """activate"""
        self.is_active = True
        return self.save()

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

    @property
    def permissions(self):
        """get all permissions"""
        ps = sum([role.permissions.split(',') for role in (g.group_role, g.event_role) if role], [])
        return [s.strip() for s in ps]

    def can(self, permission):
        """Check if user has the given permission"""
        if permission in self.permissions:
            return True
        return False

class Setting(Base):
    """base setting model"""

    __abstract__ = True

    shortname = db.Column(db.String(50))
    name = db.Column(db.String(100))
    value = db.Column(db.Text)


class Role(Base):
    """base role model (<- hahaha. punny)"""

    __abstract__ = True

    name = db.Column(db.String(100))
    permissions = db.Column(db.Text)


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

    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']))
    settings = relationship("UserSetting", backref="user")

    def groups(self):
        """All groups for this user"""
        return Group.query.join(Membership).filter_by(user_id=self.id).all()

    def join(self, group, role):
        """Join a group"""
        assert group.id, 'Save group object first'
        assert isinstance(group, Group), 'Can only join group.'
        role = GroupRole.query.filter_by(
            name=role,
            group_id=self.id
        ).one()
        return Membership(
            user_id=self.id,
            group_id=group.id,
            role_id=role.id).save()

    def signup(self, event, role):
        """Signup for an event"""
        assert event.id, 'Save event object first'
        assert isinstance(event, Event), 'Can only signup for events.'
        signup = Signup.query.filter_by(
            user_id=self.id,
            event_id=event.id
        ).one_or_none()
        if signup:
            signup.role = role
            signup.is_active = True
            return signup.save()
        role = EventRole.query.filter_by(
            name=role,
            event_id=self.id
        ).one()
        return Signup(
            user_id=self.id,
            event_id=event.id,
            role_id=role.id).save()

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
            participant_id=self.id,
            event_id=event.id).save()

    def generate_access_token(self):
        """Generates access token"""
        return (UserSetting.query.filter_by(
            user_id=self.id,
            shortname='access_token'
        ).order_by(desc(UserSetting.id)).first() or UserSetting(
            user_id=self.id,
            shortname='access_token',
            name='Access Token',
            value=self.random_hash()
        ).save()).value


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

    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    events = db.relationship('Event', backref='group', lazy='dynamic')
    settings = relationship("GroupSetting", backref="group")

    @property
    def events(self):
        """List of all events"""
        return Event.query.filter_by(group_id=self.id).all()

    @property
    def members(self):
        """List of all members"""
        return User.query.join(Membership).filter_by(group_id=self.id).all()

    def link(self, user, role):
        """links group to a user"""
        assert self.id, 'Save the object first.'
        return user.join(self, role)

    def setting_query(self):
        return GroupSetting.query.filter_by(group_id=self.id)

    def generate_access_token(self):
        """Generates access token"""
        return (GroupSetting.query.filter_by(
            group_id=self.id,
            shortname='access_token'
        ).order_by(desc(GroupSetting.id)).first() or GroupSetting(
            group_id=self.id,
            shortname='access_token',
            name='Access Token',
            value=self.random_hash()
        ).save()).value

    def __contains__(self, user):
        """Tests if user is in group"""
        return Membership.query.filter_by(
            user_id=user.id, group_id=self.id
        ).one_or_none() is not None


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

    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    start = db.Column(ArrowType, nullable=True)
    end = db.Column(ArrowType, nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    settings = relationship("EventSetting", backref="event")
    checkins = relationship("Checkin", backref="event")

    @property
    def group(self):
        return Group.query.get(self.group_id)

    @property
    def participants(self):
        """Returns all participants"""
        return User.query.join(Signup).filter_by(
            event_id=self.id,
            is_active=True).all()

    def __contains__(self, user):
        """Check if user is in signups"""
        return Signup.query.filter_by(
            user_id=user.id,
            event_id=self.id,
            is_active=True
        ).one_or_none() is not None

    def generate_access_token(self):
        """Generates access token"""
        return (EventSetting.query.filter_by(
            event_id=self.id,
            shortname='access_token'
        ).order_by(desc(EventSetting.id)).first() or EventSetting(
            event_id=self.id,
            shortname='access_token',
            name='Access Token',
            value=self.random_hash()
        ).save()).value


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

    @property
    def event(self):
        return Event.query.get(self.event_id)

    @property
    def user(self):
        return User.query.get(self.user_id)

    @property
    def is_checked_in(self):
        return Checkin.query.filter_by(
            user_id=self.user_id,
            event_id=self.event_id).one_or_none() is not None


class Membership(Base):
    """user membership in group"""

    __tablename__ = 'membership'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('group_role.id'))

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
