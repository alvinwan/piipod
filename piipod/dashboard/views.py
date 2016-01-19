from flask import Blueprint, render_template, request, redirect, url_for
from piipod.views import me, login_required


dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

#############
# DASHBOARD #
#############

@dashboard.route('/')
@login_required
def home():
    """user dashboard"""
    return render_template('dashboard/index.html', groups=me().groups())
