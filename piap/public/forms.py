from wtforms_alchemy import ModelForm, ModelFieldList
from wtforms.fields import FormField
import wtforms as wtf
from piap.staff.models import User


class SigninForm(wtf.Form):
    username = wtf.StringField()
    password = wtf.PasswordField()


class UserForm(ModelForm):
    """form for user signup and signin"""
    class Meta:
        model = User
        only = ('name', 'email', 'username', 'password')
