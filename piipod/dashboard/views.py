from flask import Blueprint, request, redirect, url_for, g
from piipod.views import current_user, login_required
from piipod.group.forms import GroupForm
from piipod.models import Group
from piipod.defaults import default_group_roles


dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard.url_value_preprocessor
def load_current_user(_, __):
    g.user = current_user()


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
    return render_dashboard('dashboard/index.html', groups=g.user.groups())


@dashboard.route('/g/', methods=['GET', 'POST'])
@login_required
def create_group():
    """create group form"""
    form = GroupForm(request.form)
    if request.method == 'POST' and form.validate():
        data = dict(request.form.items())
        category = data.pop('category', 'class')
        group = Group(**data).save().load_roles(
            default_group_roles[category]).save()
        return redirect(url_for('group.home',
            group_id=group.link(g.user, role='owner').group_id))
    return render_dashboard('form.html',
        title='Create Group',
        submit='create',
        form=form)
