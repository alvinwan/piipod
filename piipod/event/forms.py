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

    def __iter__(self):
        self.group_id.default = g.group_id
        self.process()
        return super(ModelForm, self).__iter__()
