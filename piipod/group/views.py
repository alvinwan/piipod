from flask import Blueprint, render_template, request, redirect, url_for, g
from piipod.views import me, login_required


group = Blueprint('group', __name__, url_prefix='/g/<group_name>')


@group.url_defaults
def add_group_name(endpoint, values):
    values.setdefault('group_name', g.group_name)


@group.url_value_preprocessor
def pull_group_name(endpoint, values):
    g.group_name = values.pop('group_name')


#########
# GROUP #
#########

@group.route('/')
@login_required
def home():
    """group homepage"""
    return render_template('group/index.html')

@group.route('/events')
@login_required
def events():
    """group events"""
    return 'events'
