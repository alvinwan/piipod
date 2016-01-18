"""
Important: Changes here need to be followed by `make refresh`.
"""

from piipod import db
from piipod.models import Base
from sqlalchemy import types
from sqlalchemy_utils import PasswordType, ArrowType
import arrow
import flask_login

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


class Group(Base):
    """A PIAP group can be any form or sort of organization."""

    __tablename__ = 'group'

    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    events = db.relationship('Event', backref='group', lazy='dynamic')


class Event(Base):
    """PIAP event"""

    __tablename__ = 'event'

    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    start = db.Column(ArrowType)
    end = db.Column(ArrowType)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))


########################
# RELATIONSHIP TABLES #
#######################


class Signup(Base):

    __tablename__ = 'signup'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    role = db.Column(db.String(50))


class Membership(Base):

    __tablename__ = 'membership'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    role = db.Column(db.String(50))
