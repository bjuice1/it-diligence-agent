"""
Authentication Service - Database-backed user authentication.

IMPORTANT: This service owns transaction boundaries.
All commits and rollbacks happen here, not in repositories.
"""

import os
import bcrypt
import logging
import secrets
from typing import Optional, Tuple, List

from web.database import db, User
from web.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """
    Database-backed authentication service.

    Transaction boundaries:
    - All public methods that modify data will commit or rollback
    - Read-only methods do not affect transactions
    """

    def __init__(self):
        self.repo = UserRepository()

    # =========================================================================
    # PASSWORD UTILITIES
    # =========================================================================

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storage using bcrypt."""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        if not password or not password_hash:
            return False
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False

    @staticmethod
    def is_valid_bcrypt_hash(hash_str: str) -> bool:
        """Check if string looks like a valid bcrypt hash."""
        if not hash_str:
            return False
        return hash_str.startswith('$2') and len(hash_str) >= 59

    # =========================================================================
    # AUTHENTICATION
    # =========================================================================

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.

        Returns User if successful, None otherwise.
        Updates last_login on success (commits).
        """
        if not email or not password:
            return None

        user = self.repo.get_by_email(email)

        if not user:
            logger.debug(f"Auth failed: user not found for {email}")
            return None

        if not user.active:
            logger.debug(f"Auth failed: user {email} is inactive")
            return None

        if not self.verify_password(password, user.password_hash):
            logger.debug(f"Auth failed: invalid password for {email}")
            return None

        # Update last login (COMMIT)
        try:
            self.repo.set_last_login(user)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to update last_login: {e}")
            db.session.rollback()
            # Don't fail auth just because last_login update failed

        logger.info(f"User {email} authenticated successfully")
        return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID (for Flask-Login user_loader). Read-only."""
        return self.repo.get_by_id(user_id, include_inactive=True)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive). Read-only."""
        return self.repo.get_by_email(email)

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    def create_user(
        self,
        email: str,
        password: str,
        name: str = "",
        roles: List[str] = None,
        tenant_id: str = None
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Create a new user.

        Returns (User, None) on success.
        Returns (None, error_message) on failure.
        """
        # Validate email
        if not email or '@' not in email:
            return None, "Invalid email address"

        email = email.strip().lower()

        # Check for duplicate
        if self.repo.email_exists(email):
            return None, "Email already registered"

        # Validate password
        if not password or len(password) < 8:
            return None, "Password must be at least 8 characters"

        try:
            user = User(
                email=email,
                password_hash=self.hash_password(password),
                name=name or email.split('@')[0],
                roles=roles or ['analyst'],
                tenant_id=tenant_id,
                active=True
            )
            self.repo.add_user(user)
            db.session.commit()  # COMMIT
            logger.info(f"User {email} registered successfully")
            return user, None

        except Exception as e:
            db.session.rollback()  # ROLLBACK
            logger.error(f"Registration failed for {email}: {e}")
            return None, "Registration failed"

    # =========================================================================
    # PASSWORD MANAGEMENT
    # =========================================================================

    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user's password.

        Returns (True, None) on success.
        Returns (False, error_message) on failure.
        """
        if not self.verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"

        if len(new_password) < 8:
            return False, "New password must be at least 8 characters"

        try:
            self.repo.set_password_hash(user, self.hash_password(new_password))
            db.session.commit()  # COMMIT
            logger.info(f"Password changed for user {user.email}")
            return True, None
        except Exception as e:
            db.session.rollback()  # ROLLBACK
            logger.error(f"Password change failed: {e}")
            return False, "Password change failed"

    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================

    def deactivate_user(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """Deactivate a user (soft delete)."""
        user = self.repo.get_by_id(user_id, include_inactive=True)
        if not user:
            return False, "User not found"

        try:
            self.repo.set_inactive(user)
            db.session.commit()  # COMMIT
            return True, None
        except Exception as e:
            db.session.rollback()  # ROLLBACK
            return False, str(e)

    def activate_user(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """Reactivate a user."""
        user = self.repo.get_by_id(user_id, include_inactive=True)
        if not user:
            return False, "User not found"

        try:
            self.repo.set_active(user)
            db.session.commit()  # COMMIT
            return True, None
        except Exception as e:
            db.session.rollback()  # ROLLBACK
            return False, str(e)

    def list_users(self) -> List[User]:
        """List all active users. Read-only."""
        return self.repo.list_all()

    def user_count(self) -> int:
        """Get total active user count. Read-only."""
        return self.repo.count_active()

    def admin_exists(self) -> bool:
        """Check if any admin user exists. Read-only."""
        return self.repo.admin_exists()

    # =========================================================================
    # ADMIN BOOTSTRAP (CLI only, not auto-startup)
    # =========================================================================

    def create_admin(
        self,
        email: str,
        password: str = None,
        name: str = "Admin"
    ) -> Tuple[Optional[User], str]:
        """
        Create an admin user. Called from CLI command only.

        If password is None, generates a random one and returns it.

        Returns (User, password) on success.
        Returns (None, error_message) on failure.
        """
        # Generate random password if not provided
        generated_password = None
        if not password:
            generated_password = secrets.token_urlsafe(16)
            password = generated_password

        user, error = self.create_user(
            email=email,
            password=password,
            name=name,
            roles=['admin']
        )

        if error:
            return None, error

        # Return the generated password if we made one
        return user, generated_password or password


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the singleton AuthService instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
