"""
Important: Changes here need to be followed by `make refresh`.
"""

from piap import db
from sqlalchemy import types
from sqlalchemy_utils import PasswordType
from sqlalchemy_utils.types.choice import ChoiceType
import flask_login

#############
# UTILITIES #
#############

def add_obj(obj):
    """
    Add object to database

    :param obj: any instance of a Model
    :return: information regarding database add
    """
    db.session.add(obj)
    db.session.commit()

##########
# MODELS #
##########


class User(db.Model, flask_login.UserMixin):
    """PIAP system user"""

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    updated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)

    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']))


class Organization(db.Model):
    """PIAP organization"""

    __tablename__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    updated_at = db.Column(db.DateTime)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    events = db.relationship('Event', backref='organization', lazy='dynamic')
    shifts = db.relationship('Shift', backref='organization', lazy='dynamic')


class Event(db.Model):
    """PIAP event, with registered shifts"""

    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    updated_at = db.Column(db.DateTime)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    shifts = db.relationship('Shift', backref='event', lazy='dynamic')


class Shift(db.Model):
    """PIAP shift, associated with both events and organizations"""

    __tablename__ = 'shift'
    id = db.Column(db.Integer, primary_key=True)
    updated_at = db.Column(db.DateTime)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    name = db.Column(db.String(50))
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))


########################
# RELATIONSHIP TABLES #
#######################

signups = db.Table('signups',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('shift_id', db.Integer, db.ForeignKey('shift.id')),
    db.Column('role', db.String(50))
)

duties = db.Table('duties',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('role', db.String(50))
)

employment = db.Table('employment',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('organization_id', db.Integer, db.ForeignKey('organization.id')),
    db.Column('role', db.String(50))
)
