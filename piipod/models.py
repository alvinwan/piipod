"""
Important: Changes here need to be followed by `make refresh`.
"""
from piipod import db
from flask import request, g
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy_utils import PasswordType, ArrowType
import arrow
import flask_login


class Base(db.Model):
    """Base Model for all other models"""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    updated_at = db.Column(ArrowType)
    updated_by = db.Column(db.Integer)
    created_at = db.Column(ArrowType, default=arrow.utcnow())
    created_by = db.Column(db.Integer)

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

############
# ENTITIES #
############


class User(Base, flask_login.UserMixin):
    """PIAP system user"""

    __tablename__ = 'user'

    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']))

    def groups(self):
        """All groups for this user"""
        return [m.group for m in
            Membership.query.filter_by(user_id=self.id).all()]


class Group(Base):
    """A PIAP group can be any form or sort of organization."""

    __tablename__ = 'group'

    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    events = db.relationship('Event', backref='group', lazy='dynamic')

    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)
        Membership(user_id=g.user.id, group_id=self.id, role='owner').save()


class Event(Base):
    """PIAP event"""

    __tablename__ = 'event'

    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    start = db.Column(ArrowType)
    end = db.Column(ArrowType)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))

    @property
    def group(self):
        return Group.get(self.group_id)


########################
# RELATIONSHIP TABLES #
#######################


class Signup(Base):

    __tablename__ = 'signup'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    role = db.Column(db.String(50))

    @property
    def event(self):
        return Event.get(self.event_id)

    @property
    def user(self):
        return User.get(self.user_id)


class Membership(Base):

    __tablename__ = 'membership'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    role = db.Column(db.String(50))

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
        return Group.get(self.group_id)

    @property
    def user(self):
        return User.get(self.user_id)
