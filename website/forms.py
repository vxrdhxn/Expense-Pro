from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class SignUpForm(FlaskForm):
    email = EmailField('Email', validators=[
        DataRequired(message="Email is required"), 
        Email(message="Please enter a valid email address")
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(message="First name is required")
    ])
    password1 = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=6, message="Password must be at least 6 characters long")
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password1', message="Passwords must match")
    ])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"), 
        Email(message="Please enter a valid email")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ])
    remember = BooleanField('Remember me')