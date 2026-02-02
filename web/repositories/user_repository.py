"""
User Repository - Database operations for User model.

IMPORTANT: This repository does NOT commit transactions.
The calling service (AuthService) owns commit/rollback.
This differs from other repositories to support the auth transaction pattern.
"""

from typing import Optional, List
from datetime import datetime

from web.database import db, User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User CRUD and queries.

    Note: User model uses `active=False` for soft-disable,
    not `deleted_at` like other models.
    """

    model = User

    # =========================================================================
    # QUERIES (read-only, no commits)
    # =========================================================================

    def get_by_id(self, id: str, include_inactive: bool = False) -> Optional[User]:
        """Get user by ID. Excludes inactive users by default."""
        query = User.query.filter_by(id=id)
        if not include_inactive:
            query = query.filter(User.active == True)
        return query.first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        if not email:
            return None
        return User.query.filter(
            User.email.ilike(email.strip().lower())
        ).first()

    def email_exists(self, email: str, exclude_user_id: str = None) -> bool:
        """Check if email is already registered."""
        if not email:
            return False
        query = User.query.filter(User.email.ilike(email.strip().lower()))
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None

    def get_admins(self) -> List[User]:
        """
        Get all active admin users.
        Uses proper DB query for Postgres, fallback for SQLite.
        """
        dialect = db.session.bind.dialect.name if db.session.bind else 'sqlite'

        if dialect == 'postgresql':
            # Proper jsonb query for Postgres
            return User.query.filter(
                User.active == True,
                User.roles.op('@>')('["admin"]')
            ).all()
        else:
            # SQLite fallback - filter in Python (acceptable for small user counts)
            users = User.query.filter(User.active == True).all()
            return [u for u in users if u.is_admin()]

    def list_all(self, include_inactive: bool = False) -> List[User]:
        """List all users."""
        query = User.query
        if not include_inactive:
            query = query.filter(User.active == True)
        return query.order_by(User.created_at.desc()).all()

    def count_active(self) -> int:
        """Get total active user count."""
        return User.query.filter(User.active == True).count()

    def admin_exists(self) -> bool:
        """Check if any admin user exists."""
        return len(self.get_admins()) > 0

    # =========================================================================
    # MUTATIONS (prepare changes, DO NOT COMMIT)
    # AuthService owns transaction boundaries
    # =========================================================================

    def add_user(self, user: User) -> User:
        """Add user to session (does not commit)."""
        db.session.add(user)
        return user

    def set_last_login(self, user: User) -> User:
        """Update last login timestamp (does not commit)."""
        user.last_login = datetime.utcnow()
        return user

    def set_inactive(self, user: User) -> User:
        """Mark user as inactive (does not commit)."""
        user.active = False
        return user

    def set_active(self, user: User) -> User:
        """Mark user as active (does not commit)."""
        user.active = True
        return user

    def set_password_hash(self, user: User, password_hash: str) -> User:
        """Update password hash (does not commit)."""
        user.password_hash = password_hash
        return user
