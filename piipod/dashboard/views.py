from flask import Blueprint, request, redirect, g
from piipod.views import current_user, login_required, url_for, current_user
from piipod.group.forms import GroupForm
from piipod.models import Group
from piipod.defaults import default_group_roles


dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard.url_value_preprocessor
def load_current_user(_, __):
    pass


def render_dashboard(f, *args, **kwargs):
    """custom render for dashboard"""
    from piipod.views import render
    return render(f, *args, **kwargs)


#############
# DASHBOARD #
#############


@dashboard.route('/')
@login_required
def home():
    """user dashboard"""
    return render_dashboard('dashboard/index.html', groups=current_user().groups())


@dashboard.route('/g/', methods=['GET', 'POST'])
@login_required
def create_group():
    """create group form"""
    form = GroupForm(request.form)
    if request.method == 'POST' and form.validate():
        group = Group.from_request().save().load_roles(
            default_group_roles[request.form['category']]).save()
        current_user().join(group, role='Owner')
        group.load_settings('whitelist')
        return redirect(url_for('group.home', group_url=group.url))
    return render_dashboard('public/form.html',
        title='Create Group',
        submit='create',
        form=form)
