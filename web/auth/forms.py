"""
Authentication Forms

WTForms for login, registration, and password management.
"""

import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

# Phase 3: Feature flag for auth backend
AUTH_BACKEND = os.environ.get('AUTH_BACKEND', 'json').lower()


def get_auth_backend():
    """Get the appropriate auth backend for validation."""
    if AUTH_BACKEND == 'db':
        from web.services.auth_service import get_auth_service
        return get_auth_service()
    else:
        from web.models.user import get_user_store
        return get_user_store()


class LoginForm(FlaskForm):
    """User login form."""

    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """User registration form."""

    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address")
    ])
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters")
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Create Account')

    def validate_email(self, field):
        """Check if email is already registered."""
        auth = get_auth_backend()
        if auth.get_by_email(field.data):
            raise ValidationError('This email is already registered.')


class ChangePasswordForm(FlaskForm):
    """Change password form."""

    current_password = PasswordField('Current Password', validators=[
        DataRequired(message="Current password is required")
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required"),
        Length(min=8, message="Password must be at least 8 characters")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password"),
        EqualTo('new_password', message="Passwords must match")
    ])
    submit = SubmitField('Change Password')


class ForgotPasswordForm(FlaskForm):
    """Forgot password form (request reset)."""

    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address")
    ])
    submit = SubmitField('Request Password Reset')
