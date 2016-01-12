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
    """queue system user"""

    __tablename__ = 'user'

    ROLES = (
        ('student', 'student'),
        ('staff', 'reader, tutor, GSI, or professor')
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']))
    created_at = db.Column(db.DateTime)
