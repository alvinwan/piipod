from wtforms_alchemy import ModelForm, ModelFieldList
import wtforms as wtf
from piipod.models import Group
from piipod.defaults import default_group_roles
from piipod.forms import choicify


class GroupForm(ModelForm):
    """form for groups"""

    class Meta:
        model = Group
        only = ('name', 'description')

    category = wtf.SelectField(
        'Category',
        choices=choicify(default_group_roles.keys()),
        coerce=str)


class GroupSignupForm(wtf.Form):
    """signup form for groups"""

    user_id = wtf.HiddenField('user')
    group_id = wtf.HiddenField('group')
