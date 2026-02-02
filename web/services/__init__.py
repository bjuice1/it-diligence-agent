"""
Service Layer for Business Logic

Services coordinate between repositories and provide
business logic, transaction management, and validation.
"""

from .auth_service import AuthService, get_auth_service

__all__ = [
    'AuthService',
    'get_auth_service',
]
