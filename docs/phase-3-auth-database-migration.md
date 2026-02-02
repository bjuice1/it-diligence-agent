# Phase 3: Authentication Database Migration

**Status:** NOT IMPLEMENTED

## Problem Statement

The current authentication system uses a **file-based UserStore** (`users.json`) while the rest of the application uses a **PostgreSQL/SQLite database**. This creates critical issues:

1. **Broken Foreign Keys**: `Deal.owner_id` references `users.id` in the database, but users exist only in a JSON file
2. **No Data Integrity**: User IDs in deals may not correspond to real database records
3. **Multi-tenancy Disabled**: The `Tenant` model exists but isn't connected to auth
4. **Audit Trail Broken**: `AuditLog.user_id` can't link to actual users
5. **Scalability Issues**: File-based auth doesn't scale, isn't transactional, and has race condition risks

---

## Current State

### File-Based Auth (Active)

```
Location: web/models/user.py + data/users.json

UserStore class:
- Reads/writes users.json
- Singleton pattern with thread locking
- Password hashing with bcrypt
- Role-based access (admin, analyst, viewer)
```

**Current users.json:**
```json
{
  "users": [
    {"id": "a474d9e2-...", "email": "admin@example.com", "roles": ["admin"]},
    {"id": "632ea2a4-...", "email": "test@example.com", "roles": ["analyst"]}
  ]
}
```

### Database User Model (Inactive)

```
Location: web/database.py

SQLAlchemy User model:
- Table: users (currently empty)
- Fields: id, tenant_id, email, password_hash, name, roles, active, created_at, last_login
- Relationships: tenant, deals, notifications
- Indexes: email (unique), tenant_id
```

### The Gap

| System | Users Stored | Used By |
|--------|--------------|---------|
| `users.json` | 2 users | Login, logout, registration |
| `users` table | 0 users | Deal ownership, audit logs, notifications |

---

## Goal

Migrate authentication to use the database as the single source of truth for user data. This enables:

- Proper foreign key relationships (Deal → User)
- Multi-tenancy support (User → Tenant)
- Transactional user operations
- Audit trail integrity
- Future features (team sharing, permissions, SSO)

---

## Implementation Plan

### Step 1: Create UserRepository

**File:** `web/repositories/user_repository.py`

```python
"""
User Repository - Database operations for User model.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import or_

from web.database import db, User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User CRUD and queries."""

    model = User

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        return self.query().filter(
            User.email.ilike(email)
        ).first()

    def get_by_tenant(self, tenant_id: str, include_inactive: bool = False) -> List[User]:
        """Get all users for a tenant."""
        query = self.query().filter(User.tenant_id == tenant_id)
        if not include_inactive:
            query = query.filter(User.active == True)
        return query.all()

    def email_exists(self, email: str, exclude_user_id: str = None) -> bool:
        """Check if email is already registered."""
        query = User.query.filter(User.email.ilike(email))
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None

    def create_user(
        self,
        email: str,
        password_hash: str,
        name: str = "",
        roles: List[str] = None,
        tenant_id: str = None
    ) -> User:
        """Create a new user."""
        return self.create(
            email=email.lower(),
            password_hash=password_hash,
            name=name or email.split('@')[0],
            roles=roles or ['analyst'],
            tenant_id=tenant_id,
            active=True
        )

    def update_last_login(self, user: User) -> User:
        """Update user's last login timestamp."""
        return self.update(user, last_login=datetime.utcnow())

    def deactivate_user(self, user: User) -> User:
        """Deactivate a user (soft disable, not delete)."""
        return self.update(user, active=False)

    def activate_user(self, user: User) -> User:
        """Reactivate a user."""
        return self.update(user, active=True)

    def search(
        self,
        search_term: str = None,
        tenant_id: str = None,
        role: str = None,
        active_only: bool = True,
        page: int = 1,
        per_page: int = 50
    ) -> tuple:
        """Search users with pagination."""
        query = self.query()

        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)

        if active_only:
            query = query.filter(User.active == True)

        if role:
            # JSON array contains - works for both PostgreSQL and SQLite
            query = query.filter(User.roles.contains([role]))

        if search_term:
            search_filter = or_(
                User.email.ilike(f'%{search_term}%'),
                User.name.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)

        total = query.count()
        items = query.order_by(User.created_at.desc()) \
                     .offset((page - 1) * per_page) \
                     .limit(per_page) \
                     .all()

        return items, total

    def count_by_tenant(self, tenant_id: str) -> int:
        """Count users in a tenant."""
        return self.query().filter(
            User.tenant_id == tenant_id,
            User.active == True
        ).count()

    def get_admins(self, tenant_id: str = None) -> List[User]:
        """Get all admin users."""
        query = self.query().filter(
            User.roles.contains(['admin']),
            User.active == True
        )
        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)
        return query.all()
```

---

### Step 2: Create Database-Backed AuthService

**File:** `web/services/auth_service.py`

```python
"""
Authentication Service - Database-backed user authentication.

Replaces the file-based UserStore with database operations.
"""

import bcrypt
import logging
from typing import Optional, Tuple
from datetime import datetime

from flask_login import UserMixin
from web.database import db, User
from web.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """
    Database-backed authentication service.

    Handles user authentication, registration, and password management.
    """

    def __init__(self):
        self.repo = UserRepository()

    # =========================================================================
    # PASSWORD UTILITIES
    # =========================================================================

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storage."""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False

    # =========================================================================
    # AUTHENTICATION
    # =========================================================================

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.

        Returns User if successful, None otherwise.
        """
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

        # Update last login
        self.repo.update_last_login(user)
        logger.info(f"User {email} authenticated successfully")

        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID (for Flask-Login user_loader)."""
        return self.repo.get_by_id(user_id)

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    def register(
        self,
        email: str,
        password: str,
        name: str = "",
        roles: list = None,
        tenant_id: str = None
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Register a new user.

        Returns:
            Tuple of (User, None) on success
            Tuple of (None, error_message) on failure
        """
        # Validate email
        if not email or '@' not in email:
            return None, "Invalid email address"

        # Check if email exists
        if self.repo.email_exists(email):
            return None, "Email already registered"

        # Validate password
        if len(password) < 8:
            return None, "Password must be at least 8 characters"

        try:
            user = self.repo.create_user(
                email=email,
                password_hash=self.hash_password(password),
                name=name,
                roles=roles or ['analyst'],
                tenant_id=tenant_id
            )
            logger.info(f"User {email} registered successfully")
            return user, None

        except Exception as e:
            logger.error(f"Registration failed for {email}: {e}")
            return None, "Registration failed. Please try again."

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

        Returns:
            Tuple of (True, None) on success
            Tuple of (False, error_message) on failure
        """
        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"

        # Validate new password
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters"

        if current_password == new_password:
            return False, "New password must be different from current password"

        try:
            self.repo.update(user, password_hash=self.hash_password(new_password))
            logger.info(f"Password changed for user {user.email}")
            return True, None

        except Exception as e:
            logger.error(f"Password change failed for {user.email}: {e}")
            return False, "Password change failed. Please try again."

    def reset_password(self, user: User, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Reset user's password (admin function).

        Returns:
            Tuple of (True, None) on success
            Tuple of (False, error_message) on failure
        """
        if len(new_password) < 8:
            return False, "Password must be at least 8 characters"

        try:
            self.repo.update(user, password_hash=self.hash_password(new_password))
            logger.info(f"Password reset for user {user.email}")
            return True, None

        except Exception as e:
            logger.error(f"Password reset failed for {user.email}: {e}")
            return False, "Password reset failed."

    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================

    def update_profile(
        self,
        user: User,
        name: str = None,
        email: str = None
    ) -> Tuple[Optional[User], Optional[str]]:
        """Update user profile."""
        updates = {}

        if name is not None:
            updates['name'] = name

        if email is not None and email != user.email:
            if self.repo.email_exists(email, exclude_user_id=user.id):
                return None, "Email already in use"
            updates['email'] = email.lower()

        if not updates:
            return user, None

        try:
            user = self.repo.update(user, **updates)
            return user, None
        except Exception as e:
            logger.error(f"Profile update failed: {e}")
            return None, "Update failed. Please try again."

    # =========================================================================
    # ADMIN BOOTSTRAP
    # =========================================================================

    def ensure_admin_exists(
        self,
        email: str = "admin@example.com",
        password: str = "changeme",
        name: str = "Admin"
    ) -> Optional[User]:
        """
        Ensure at least one admin user exists.

        Called on app startup to guarantee admin access.
        """
        # Check if any admin exists
        admins = self.repo.get_admins()
        if admins:
            return admins[0]

        # Create default admin
        user, error = self.register(
            email=email,
            password=password,
            name=name,
            roles=['admin']
        )

        if user:
            logger.info(f"Created default admin user: {email}")
        else:
            logger.error(f"Failed to create admin: {error}")

        return user


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the singleton AuthService instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
```

---

### Step 3: Migration Script

**File:** `scripts/migrate_users_to_db.py`

```python
#!/usr/bin/env python3
"""
Migrate users from users.json to database.

Run once to transfer existing file-based users to the database.

Usage:
    python scripts/migrate_users_to_db.py
    python scripts/migrate_users_to_db.py --dry-run  # Preview only
"""

import json
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def migrate_users(dry_run: bool = False):
    """Migrate users from JSON file to database."""
    from flask import Flask
    from web.database import db, init_db, User
    from config_v2 import DATA_DIR

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'migration'
    init_db(app)

    json_path = DATA_DIR / 'users.json'

    with app.app_context():
        # Load users from JSON
        if not json_path.exists():
            print(f"No users.json found at {json_path}")
            return

        with open(json_path, 'r') as f:
            data = json.load(f)

        json_users = data.get('users', [])
        print(f"Found {len(json_users)} users in users.json")

        # Check existing database users
        db_users = User.query.all()
        db_emails = {u.email.lower() for u in db_users}
        print(f"Found {len(db_users)} users already in database")

        migrated = 0
        skipped = 0

        for user_data in json_users:
            email = user_data['email'].lower()

            if email in db_emails:
                print(f"  SKIP: {email} (already in database)")
                skipped += 1
                continue

            if dry_run:
                print(f"  WOULD MIGRATE: {email}")
                migrated += 1
                continue

            # Create user in database
            user = User(
                id=user_data['id'],
                email=email,
                password_hash=user_data['password_hash'],
                name=user_data.get('name', ''),
                roles=user_data.get('roles', ['analyst']),
                active=user_data.get('active', True),
                tenant_id=user_data.get('tenant_id'),
            )

            # Parse timestamps
            if user_data.get('created_at'):
                from datetime import datetime
                try:
                    user.created_at = datetime.fromisoformat(user_data['created_at'])
                except:
                    pass

            if user_data.get('last_login'):
                try:
                    user.last_login = datetime.fromisoformat(user_data['last_login'])
                except:
                    pass

            db.session.add(user)
            print(f"  MIGRATED: {email}")
            migrated += 1

        if not dry_run:
            db.session.commit()

        print()
        print(f"Migration complete:")
        print(f"  Migrated: {migrated}")
        print(f"  Skipped: {skipped}")

        if dry_run:
            print()
            print("This was a dry run. No changes were made.")
            print("Run without --dry-run to perform actual migration.")


def main():
    parser = argparse.ArgumentParser(description='Migrate users from JSON to database')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, no changes')
    args = parser.parse_args()

    migrate_users(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
```

---

### Step 4: Update Auth Routes

**File:** `web/auth/routes.py` (modifications)

```python
# Change imports
from web.services.auth_service import get_auth_service

# Update login handler
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        auth_service = get_auth_service()  # NEW
        user = auth_service.authenticate(form.email.data, form.password.data)  # NEW

        if user:
            login_user(user, remember=form.remember_me.data)
            # ... rest unchanged

# Update registration handler
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # ... validation code ...

    if form.validate_on_submit():
        auth_service = get_auth_service()  # NEW

        user, error = auth_service.register(  # NEW
            email=form.email.data,
            password=form.password.data,
            name=form.name.data,
            roles=['analyst']
        )

        if user:
            # ... success handling
        else:
            flash(error, 'error')  # Show actual error

# Update Flask-Login user_loader
@login_manager.user_loader
def load_user(user_id):
    auth_service = get_auth_service()  # NEW
    return auth_service.get_user_by_id(user_id)  # NEW
```

---

### Step 5: Update App Initialization

**File:** `web/app.py` (modifications)

```python
# In create_app() or app initialization:

def ensure_admin_on_startup():
    """Ensure admin user exists when app starts."""
    from web.services.auth_service import get_auth_service
    import os

    auth_service = get_auth_service()

    # Get admin credentials from environment or use defaults
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'changeme')

    auth_service.ensure_admin_exists(
        email=admin_email,
        password=admin_password,
        name='Admin'
    )

# Call on startup
with app.app_context():
    ensure_admin_on_startup()
```

---

### Step 6: Remove File-Based UserStore

Once migration is verified:

1. **Delete or deprecate** `web/models/user.py` (the old UserStore)
2. **Delete** `data/users.json` (after backing up)
3. **Update imports** throughout codebase to use `AuthService`
4. **Remove** `get_user_store()` calls

---

## Files to Create

| File | Purpose |
|------|---------|
| `web/repositories/user_repository.py` | Database operations for User model |
| `web/services/auth_service.py` | Authentication business logic |
| `scripts/migrate_users_to_db.py` | One-time migration script |

## Files to Modify

| File | Change |
|------|--------|
| `web/auth/routes.py` | Use AuthService instead of UserStore |
| `web/auth/__init__.py` | Update Flask-Login user_loader |
| `web/app.py` | Admin bootstrap on startup |
| `web/repositories/__init__.py` | Export UserRepository |

## Files to Delete (After Migration)

| File | Reason |
|------|--------|
| `web/models/user.py` | Replaced by database + AuthService |
| `data/users.json` | Data migrated to database |

---

## Migration Steps

### Pre-Migration

1. **Backup** `data/users.json`
2. **Backup** database
3. Run `python scripts/migrate_users_to_db.py --dry-run` to preview

### Migration

1. Run `python scripts/migrate_users_to_db.py` to migrate users
2. Update auth routes to use `AuthService`
3. Update Flask-Login user_loader
4. Test login/logout/register
5. Verify Deal.owner_id now has valid FK

### Post-Migration

1. Remove old `UserStore` code
2. Delete `users.json`
3. Update documentation

---

## Verification Checklist

- [ ] Users migrated to database (`SELECT COUNT(*) FROM users`)
- [ ] Login works with migrated users
- [ ] Registration creates users in database
- [ ] Password change works
- [ ] Flask-Login session persists across requests
- [ ] Deal.owner_id references valid user
- [ ] Audit logs have valid user_id
- [ ] Admin user exists on fresh database

---

## Future Considerations (Phase 4+)

### Multi-Tenancy

```python
# Tenant isolation for all queries
def get_users_for_tenant(tenant_id):
    return User.query.filter_by(tenant_id=tenant_id, active=True).all()
```

### Team/Organization Features

- Invite users to tenant
- Role management per tenant
- Deal sharing within tenant

### SSO Integration

- OAuth2 / OIDC support
- SAML for enterprise
- Link external identity to User record

### Password Policies

- Minimum complexity requirements
- Password expiration
- Password history (prevent reuse)

---

## Dependencies

- Phase 1 & 2 complete (database architecture in place)
- Flask-Login configured
- bcrypt installed for password hashing

---

## Related Documents

- `docs/database-architecture-audit.md` - Overall DB architecture
- `docs/phase-2-consistent-reads.md` - Repository pattern reference
