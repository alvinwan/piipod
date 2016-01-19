from piipod import db
from flask import redirect, url_for
from piipod.models import User

###############
# CONTROLLERS #
###############

def get_user(**kwargs):
    """
    Get user by kwargs.

    :param kwargs: key arguments containing user details
    :return: User object or None
    """
    return User.query.filter_by(**kwargs).first()

def get_user_home(user):
    """
    Get home page for user

    :param User user: user object
    :return: User object or None
    """
    # TODO: update to become event-specific
    # if user and getattr(user, 'role', None) == 'staff':
    #     return redirect(url_for('admin.home'))
    return redirect(url_for('dashbaord.home'))
