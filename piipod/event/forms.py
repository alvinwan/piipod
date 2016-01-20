from flask import g
from wtforms_alchemy import ModelForm, ModelFieldList
import wtforms as wtf
from piipod.models import Event


class EventForm(ModelForm):
    """form for user events"""

    class Meta:
        model = Event
        only = ('name', 'description', 'start', 'end')

    group_id = wtf.HiddenField('group_id')


class EventSignupForm(wtf.Form):
    """signup form for events"""

    user_id = wtf.HiddenField('user')
    event_id = wtf.HiddenField('event')
