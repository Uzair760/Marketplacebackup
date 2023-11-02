from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask1.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
        Length(max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired(),
        Length(min=8, max=30)])
    confirm_password = StringField('Confirm Password',
        validators=[DataRequired(), Length(min=8, max=30), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username already exists.')

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('This email already exists.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
        Length(max=20)])
    password = StringField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateProfileDetails(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
        Length(max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Change Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('This username already exists.')

    def validate_email(self, email):
        if email.data != current_user.email:
            email = User.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError('This email already exists.')

class PostListing(FlaskForm):
    item = StringField('Item', validators=[DataRequired()])
    desc = TextAreaField('Description')
    price = StringField('Price', validators=[DataRequired()])
    item_picture = FileField('Add an Image', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Post Listing')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email is None:
            raise ValidationError('There is no account registered to this email.')

class ResetPasswordForm(FlaskForm):
    password = StringField('Password', validators=[DataRequired(),
        Length(min=8, max=30)])
    confirm_password = StringField('Confirm Password',
        validators=[DataRequired(), Length(min=8, max=30), EqualTo('password')])
    submit = SubmitField('Reset Password')
