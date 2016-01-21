from flask import g
from wtforms_alchemy import ModelForm, ModelFieldList
import wtforms as wtf
from piiipod.models import Event


class EventForm(ModelForm):
    """form for user events"""

    class Meta:
        model = Event
        only = ('name', 'description', 'start', 'end')

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
