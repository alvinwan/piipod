from wtforms_alchemy import ModelForm, ModelFieldList
from wtforms.fields import FormField
import wtforms as wtf
from piap.admin.models import User


class LoginForm(wtf.Form):
    username = wtf.StringField()
    password = wtf.PasswordField()


class RegisterForm(ModelForm):
    """form for user signup and signin"""
    class Meta:
        model = User
        only = ('name', 'email', 'username', 'password')
