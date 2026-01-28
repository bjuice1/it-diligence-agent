"""
Authentication Routes

Login, logout, registration, and password management endpoints.
"""

import os
import logging
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from web.auth import auth_bp
from web.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm
from web.models.user import get_user_store, Role

logger = logging.getLogger(__name__)

# Phase 7: Rate limiting for auth routes
USE_RATE_LIMITING = os.environ.get('USE_RATE_LIMITING', 'false').lower() == 'true'
USE_AUDIT_LOGGING = os.environ.get('USE_AUDIT_LOGGING', 'true').lower() == 'true'


def audit_auth_event(action, user_id=None, email=None, success=True, details=None):
    """Log authentication events."""
    if not USE_AUDIT_LOGGING:
        return
    try:
        from web.audit_service import audit_log, AuditAction, AuditSeverity
        audit_log(
            action=action,
            resource_type='user',
            resource_id=user_id,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            details={
                'email': email,
                'success': success,
                **(details or {})
            }
        )
    except Exception as e:
        logger.debug(f"Audit logging failed: {e}")


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user_store = get_user_store()
        user = user_store.authenticate(form.email.data, form.password.data)

        if user:
            login_user(user, remember=form.remember_me.data)
            flash('Welcome back!', 'success')

            # Audit successful login
            audit_auth_event('auth.login', user_id=user.id, email=form.email.data, success=True)

            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            # Audit failed login
            audit_auth_event('auth.login_failed', email=form.email.data, success=False)
            flash('Invalid email or password.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    user_id = current_user.id if current_user else None
    email = current_user.email if current_user else None

    logout_user()

    # Audit logout
    audit_auth_event('auth.logout', user_id=user_id, email=email, success=True)

    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    # Check if registration is enabled
    if os.environ.get('DISABLE_REGISTRATION', '').lower() == 'true':
        flash('Registration is currently disabled. Please contact an administrator.', 'warning')
        return redirect(url_for('auth.login'))

    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user_store = get_user_store()

        # Create user
        user = user_store.create_user(
            email=form.email.data,
            password=form.password.data,
            name=form.name.data,
            roles=[Role.ANALYST]  # Default role
        )

        if user:
            # Audit user creation
            audit_auth_event('user.create', user_id=user.id, email=form.email.data, success=True,
                           details={'name': form.name.data, 'roles': ['analyst']})
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred. Please try again.', 'error')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page."""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
        else:
            user_store = get_user_store()

            # Update password
            from web.models.user import User
            current_user.password_hash = User.hash_password(form.new_password.data)
            user_store.update_user(current_user)

            flash('Password updated successfully.', 'success')
            return redirect(url_for('dashboard'))

    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('auth/profile.html', user=current_user)
