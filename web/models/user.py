"""
User Model for Authentication

File-based user storage for Phase 2. Will migrate to PostgreSQL in Phase 3.
"""

import json
import uuid
import bcrypt
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from flask_login import UserMixin
import threading


class Role:
    """User role constants."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

    @classmethod
    def all_roles(cls) -> List[str]:
        return [cls.ADMIN, cls.ANALYST, cls.VIEWER]

    @classmethod
    def can_edit(cls, role: str) -> bool:
        """Check if role can edit data."""
        return role in [cls.ADMIN, cls.ANALYST]

    @classmethod
    def can_admin(cls, role: str) -> bool:
        """Check if role has admin privileges."""
        return role == cls.ADMIN


@dataclass
class User(UserMixin):
    """User model for authentication."""

    id: str
    email: str
    password_hash: str
    name: str = ""
    roles: List[str] = field(default_factory=lambda: [Role.ANALYST])
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_login: Optional[str] = None
    tenant_id: Optional[str] = None  # For multi-tenancy support

    def get_id(self) -> str:
        """Flask-Login requires this method."""
        return self.id

    @property
    def is_active(self) -> bool:
        """Flask-Login requires this property."""
        return self.active

    @property
    def is_authenticated(self) -> bool:
        """Flask-Login requires this property."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Flask-Login requires this property."""
        return False

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def can_edit(self) -> bool:
        """Check if user can edit data."""
        return any(Role.can_edit(r) for r in self.roles)

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return any(Role.can_admin(r) for r in self.roles)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary."""
        return cls(**data)

    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storage."""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')


class UserStore:
    """
    File-based user storage.

    Thread-safe singleton for managing users.
    Will be replaced with database in Phase 3.
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, storage_path: Optional[Path] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage_path: Optional[Path] = None):
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            from config_v2 import DATA_DIR
            self._storage_path = storage_path or DATA_DIR / "users.json"
            self._users: Dict[str, User] = {}
            self._email_index: Dict[str, str] = {}  # email -> user_id
            self._load()
            self._initialized = True

    def _load(self):
        """Load users from file."""
        if self._storage_path.exists():
            try:
                with open(self._storage_path, 'r') as f:
                    data = json.load(f)
                    for user_data in data.get('users', []):
                        user = User.from_dict(user_data)
                        self._users[user.id] = user
                        self._email_index[user.email.lower()] = user.id
            except Exception as e:
                print(f"Error loading users: {e}")
                self._users = {}
                self._email_index = {}

    def _save(self):
        """Save users to file."""
        with self._lock:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'users': [user.to_dict() for user in self._users.values()],
                'updated_at': datetime.utcnow().isoformat()
            }
            # Write atomically
            temp_path = self._storage_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            temp_path.replace(self._storage_path)

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        user_id = self._email_index.get(email.lower())
        if user_id:
            return self._users.get(user_id)
        return None

    def create_user(
        self,
        email: str,
        password: str,
        name: str = "",
        roles: Optional[List[str]] = None
    ) -> Optional[User]:
        """Create a new user."""
        with self._lock:
            # Check if email already exists
            if self.get_by_email(email):
                return None

            user = User(
                id=str(uuid.uuid4()),
                email=email.lower(),
                password_hash=User.hash_password(password),
                name=name or email.split('@')[0],
                roles=roles or [Role.ANALYST],
                active=True,
                created_at=datetime.utcnow().isoformat()
            )

            self._users[user.id] = user
            self._email_index[user.email] = user.id
            self._save()

            return user

    def update_user(self, user: User) -> bool:
        """Update an existing user."""
        with self._lock:
            if user.id not in self._users:
                return False

            # Update email index if email changed
            old_user = self._users[user.id]
            if old_user.email != user.email:
                del self._email_index[old_user.email]
                self._email_index[user.email.lower()] = user.id

            self._users[user.id] = user
            self._save()
            return True

    def update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        with self._lock:
            user = self._users.get(user_id)
            if user:
                user.last_login = datetime.utcnow().isoformat()
                self._save()

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return False

            del self._email_index[user.email]
            del self._users[user_id]
            self._save()
            return True

    def list_users(self) -> List[User]:
        """List all users."""
        return list(self._users.values())

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        user = self.get_by_email(email)
        if user and user.active and user.check_password(password):
            self.update_last_login(user.id)
            return user
        return None

    def user_count(self) -> int:
        """Get total number of users."""
        return len(self._users)

    def ensure_admin_exists(self, default_email: str = "admin@example.com", default_password: str = "changeme"):
        """Ensure at least one admin user exists."""
        with self._lock:
            # Check if any admin exists
            admins = [u for u in self._users.values() if u.is_admin()]
            if not admins:
                # Create default admin
                self.create_user(
                    email=default_email,
                    password=default_password,
                    name="Admin",
                    roles=[Role.ADMIN]
                )
                print(f"Created default admin user: {default_email}")


# Singleton instance
_user_store: Optional[UserStore] = None


def get_user_store() -> UserStore:
    """Get the singleton UserStore instance."""
    global _user_store
    if _user_store is None:
        _user_store = UserStore()
    return _user_store
