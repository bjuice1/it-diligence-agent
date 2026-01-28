"""
Authentication Blueprint

Handles user login, logout, registration, and password management.
"""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from web.auth import routes  # noqa: E402, F401
