from flask import Blueprint, render_template, request, redirect, url_for
from queue import app
from .models import User
from .controllers import *
import flask_login


admin = Blueprint('admin', __name__, url_prefix='/admin')

#########
# ADMIN #
#########

@admin.route('/')
@flask_login.login_required
def home():
    """staff homepage"""
    # option to see analytics or to start helping
    return render_template('admin.html')


#############
# ANALYTICS #
#############


@admin.route('/analytics')
def analytics():
    """analytics for requests"""
    return render_template('analytics.html')
