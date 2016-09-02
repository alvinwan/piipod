from flask import g
from wtforms import widgets
from wtforms import SelectMultipleField
from wtforms_alchemy import ModelForm
import wtforms as wtf
from piipod.forms import choicify


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class EventForm(ModelForm):
    """form for user events"""

    name = wtf.StringField('Name')
    description = wtf.StringField('Description', description='(optional)')
    start = wtf.DateTimeField(description='2016-01-13 12:00:00')
    end = wtf.DateTimeField(description='2016-01-13 12:00:00')
    group_id = wtf.HiddenField('group_id')
    days_of_the_week = MultiCheckboxField(
        'Days of the Week',
        choices=choicify(('Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun')),
        description='Days of the week that this event repeats on')
    frequency = wtf.IntegerField(
        'Frequency',
        description='Happens every _ weeks')
    until = wtf.DateTimeField(description='2016-01-13 12:00:00')


class EventSignupForm(wtf.Form):
    """signup form for events"""

    user_id = wtf.HiddenField()
    event_id = wtf.HiddenField()
    role_id = wtf.SelectField(coerce=int)


class EventCheckinForm(wtf.Form):
    """checkin form for events"""

    event_id = wtf.HiddenField()
    user_id = wtf.HiddenField()
    code = wtf.StringField()


class EventGenerateCodeForm(wtf.Form):
    """form to generate codes"""

    length = wtf.IntegerField(default=5)
    value = wtf.StringField()


class ProcessWaitlistForm(wtf.Form):
    """form for processing waitlist"""


class CategorizeForm(wtf.Form):
    """categorize signup"""

    category = wtf.SelectField('Category', description='new category for the signup',coerce=str)


class CategorizeBatchForm(wtf.Form):
    """categorize by batch"""

    category = wtf.SelectField('Category', description='new category for the signup',coerce=str)


class FilterSignupForm(wtf.Form):
    """filter out signups"""

    value = wtf.SelectField(choices=[
        ('num_active_signups', 'User\'s Number of Active Signups'),
        ('num_waitlisted_signups', 'User\'s Number of Waitlisted Signups'),
        ('num_non_waitlisted_signups', 'User\'s Number of Non-Waitlisted Signups')
    ])
    operator = wtf.SelectField(choices=choicify(['<', '<=', '=', '>=', '>']))
    n = wtf.IntegerField('n', description='number')
    category = wtf.SelectField('Category', description='Select a category of signups to apply this filter to.')
