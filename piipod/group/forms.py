from wtforms_alchemy import ModelForm, ModelFieldList
import wtforms as wtf
from piipod.models import Group


class GroupForm(ModelForm):
    """form for groups"""
    
    class Meta:
        model = Group
        only = ('name', 'description')
