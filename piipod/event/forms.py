from flask import g
from wtforms_alchemy import ModelForm, ModelFieldList
import wtforms as wtf
from piipod.models import Event


class EventForm(ModelForm):
    """form for user events"""

    class Meta:
        model = Event
        only = ('name', 'description')

    url = wtf.StringField('slug', description='slug for your event <code>/e/[event_id]/[slug]</code>')
    start = wtf.DateTimeField(description='2016-01-13 12:00:00')
    end = wtf.DateTimeField(description='2016-01-13 12:00:00')
    group_id = wtf.HiddenField('group_id')


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
