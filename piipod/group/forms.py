from wtforms_alchemy import ModelForm, ModelFieldList
import wtforms as wtf
from piipod.models import Group
from piipod.defaults import default_group_roles
from piipod.forms import choicify
import arrow


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

    user_id = wtf.HiddenField()
    group_id = wtf.HiddenField()
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

class SyncForm(wtf.Form):
    """sync with service"""

    pattern = wtf.StringField('Filter Synced Events', description='Only sync events that match the given regex string. Use <code>*</code> to match all events.', default='*')
    calendar = wtf.SelectField(coerce=str)
    recurrence_start = wtf.DateTimeField('Recurrence Start', description='Using all recurring events, create recurrences starting from this datetime. (Default: Today)', default=arrow.now().to('local'))
    recurrence_end = wtf.DateTimeField('Recurrence End', description='Using all recurring events, create recurrences ending at this datetime. (Default: One week from today)',
    default=arrow.now().to('local').replace(weeks=1))
    shift_duration = wtf.IntegerField('Shift Duration', description='Specify <b>in minutes</b> the length of each shift. Each event will be split into shifts of this duration. Use <code>0</code> to <i>not</i> split events into shifts.', default=0)
    shift_alignment = wtf.SelectField('Shift Alignment', description='Specify where to start splitting shifts. If <code>shift_duration</code> is <code>0</code>, this field will be ignored.', choices=(
        ('HOUR', 'Align with the hour'),
        ('START', 'Align with the start')
    ))


class ConfirmSyncForm(wtf.Form):
    """confirm sync"""

    confirm = wtf.HiddenField(default='y')
    pattern = wtf.HiddenField()
    calendar = wtf.HiddenField()
    recurrence_start = wtf.HiddenField()
    recurrence_end = wtf.HiddenField()
    shift_duration = wtf.HiddenField()
    shift_alignment = wtf.HiddenField()


class DeleteEventsEnMasse(wtf.Form):
    """delete events within a range"""

    start_id = wtf.IntegerField()
    end_id = wtf.IntegerField()
