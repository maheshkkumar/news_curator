from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, SelectField
from wtforms.fields import SelectMultipleField
from wtforms.validators import DataRequired
from config import CATEGORIES


class LoginForm(Form):
    """Login form to access writing and settings pages"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    
class UploadForm(Form):
	"""Upload form to submit a new link"""
	description = StringField('Name', validators=[DataRequired()])
	link = StringField('Link', validators=[DataRequired()])
	category = SelectField(label='Category', choices=CATEGORIES)

class UserProfileForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])

class UserChangePassword(Form):	
	current_password = PasswordField('Current Password', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])