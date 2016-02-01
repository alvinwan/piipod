from wtforms_alchemy import ModelForm, ModelFieldList
import wtforms as wtf
from piipod.models import Group
from piipod.defaults import default_group_roles
from piipod.forms import choicify


class GroupForm(ModelForm):
    """form for groups"""

    class Meta:
        model = Group
        only = ('name', 'description', 'url')

    category = wtf.SelectField(
        'Category',
        choices=choicify(default_group_roles.keys()),
        coerce=str)


class GroupSignupForm(wtf.Form):
    """signup form for groups"""

    user_id = wtf.HiddenField('user')
    group_id = wtf.HiddenField('group')
    role_id = wtf.SelectField(coerce=int)


class ProcessWaitlistsForm(wtf.Form):
    """process form"""

    identifiers = wtf.StringField('Identifiers', description='comma-separated list of tags or event IDs to include in the resolver')
    algorithms = wtf.SelectField('Resolver Algorithm',
        description='Algorithm to apply, to process waitlists for the specified events',
        choices=(
            ('SMA', 'Stable Marriage Algorithm'),
            ('CSP', 'Constraint Satisfaction Problem')),
        coerce=str)


class ImportSignupsForm(wtf.Form):
    """import signups"""

    csv = wtf.TextAreaField('csv', description='Comma-separated text with <i>at least</i> the headers <code>user_email, category, event_id</code>. You may additionally specify <code>status, preference, comment, user_name, event_ids</code>, where <code>event_ids</code> is a tuple of bar-delimited event IDs. i.e., <code>(25|234|3)</code>')
    override = wtf.BooleanField(description='Check to override signup details if a corresponding signup with the same user and event id is found.')
