# Phase 3: Auth Database Migration - Implementation Plan

**Version 2.0** - Updated based on GPT review feedback

## Executive Summary

**Goal:** Migrate authentication from file-based storage (`data/users.json`) to PostgreSQL/SQLite database, completing the database-first architecture established in Phases 1 & 2.

**Why:** The current file-based auth is inconsistent with the database-first architecture. All other app data (deals, facts, findings, gaps) is in the database. Users should be too.

**Risk Level:** Medium - Auth is critical path, but migration preserves existing password hashes and provides rollback via feature flag.

---

## Key Design Decisions (Updated from Review)

| Decision | Approach | Rationale |
|----------|----------|-----------|
| **Admin bootstrap** | CLI command, not auto-startup | No hardcoded credentials; explicit action required |
| **Transaction ownership** | AuthService commits, repos don't | Single place owns transactions; clear rollback behavior |
| **Multi-tenant** | Global for now | tenant_id exists but not enforced; future phase |
| **Rollout strategy** | Feature flag `AUTH_BACKEND=db\|json` | Gradual migration with instant rollback |
| **JSON roles query** | Postgres jsonb with SQLite fallback | Proper DB query, not Python filtering |

---

## Current Architecture (What We're Replacing)

### File-Based UserStore (`web/models/user.py`)

```
User Request → Flask-Login → UserStore.get_by_id() → users.json file
                                    ↓
Login Form → UserStore.authenticate() → bcrypt verify → users.json
```

**Problems with current system:**
- Hardcoded admin credentials in source code
- File I/O on every auth operation
- No transaction support
- Inconsistent with DB-first architecture

---

## Target Architecture

```
User Request → Flask-Login → AuthService.get_by_id() → PostgreSQL users table
                                    ↓
Login Form → AuthService.authenticate() → bcrypt verify → PostgreSQL
```

**Components:**
1. **UserRepository** - Database queries only (NO commits)
2. **AuthService** - Business logic + transaction ownership (commits here)
3. **Migration Script** - Full implementation with validation
4. **CLI Command** - `flask create-admin` for admin bootstrap

---

## Implementation Details

### File 1: `web/repositories/user_repository.py` (NEW)

**Key principle: Repositories do NOT commit. They prepare queries/changes.**

```python
"""
User Repository - Database operations for User model.

IMPORTANT: This repository does NOT commit transactions.
The calling service (AuthService) owns commit/rollback.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import or_, text

from web.database import db, User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User CRUD and queries."""

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
        dialect = db.session.bind.dialect.name

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
```

---

### File 2: `web/services/auth_service.py` (NEW)

**Key principle: AuthService owns ALL transaction commits/rollbacks.**

```python
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
from datetime import datetime

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
            user.password_hash = self.hash_password(new_password)
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
        if not password:
            password = secrets.token_urlsafe(16)

        user, error = self.create_user(
            email=email,
            password=password,
            name=name,
            roles=['admin']
        )

        if error:
            return None, error

        return user, password


# Singleton accessor
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the singleton AuthService instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
```

---

### File 3: `web/cli.py` (NEW or ADD to existing)

**Admin bootstrap via CLI command, not auto-startup.**

```python
"""
Flask CLI commands for auth management.
"""

import click
from flask.cli import with_appcontext


@click.command('create-admin')
@click.option('--email', prompt=True, help='Admin email address')
@click.option('--password', default=None, help='Password (generated if not provided)')
@click.option('--name', default='Admin', help='Display name')
@with_appcontext
def create_admin_command(email, password, name):
    """Create an admin user."""
    from web.services.auth_service import get_auth_service

    auth = get_auth_service()

    # Check if admin already exists
    if auth.get_by_email(email):
        click.echo(f"Error: User {email} already exists")
        return

    user, result = auth.create_admin(email, password, name)

    if not user:
        click.echo(f"Error: {result}")
        return

    click.echo(f"Admin user created: {email}")
    if not password:
        click.echo(f"Generated password: {result}")
        click.echo("Please change this password after first login.")


@click.command('list-users')
@with_appcontext
def list_users_command():
    """List all users."""
    from web.services.auth_service import get_auth_service

    auth = get_auth_service()
    users = auth.list_users()

    if not users:
        click.echo("No users found.")
        return

    click.echo(f"{'Email':<40} {'Name':<20} {'Roles':<20} {'Active'}")
    click.echo("-" * 90)
    for user in users:
        roles = ', '.join(user.roles) if user.roles else '-'
        click.echo(f"{user.email:<40} {user.name:<20} {roles:<20} {user.active}")


def register_cli(app):
    """Register CLI commands with Flask app."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(list_users_command)
```

**Usage:**
```bash
# Create admin with generated password
flask create-admin --email admin@example.com

# Create admin with specific password
flask create-admin --email admin@example.com --password MySecurePass123

# List all users
flask list-users
```

---

### File 4: `scripts/migrate_users_to_db.py` (NEW - Full Implementation)

```python
#!/usr/bin/env python3
"""
Migrate users from users.json to database.

Features:
- --dry-run flag for preview
- Timestamped backups
- Email normalization
- Duplicate detection
- Hash validation
- Single transaction commit

Usage:
    python scripts/migrate_users_to_db.py --dry-run  # Preview only
    python scripts/migrate_users_to_db.py            # Execute migration
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def is_valid_bcrypt_hash(hash_str: str) -> bool:
    """Check if string looks like a valid bcrypt hash."""
    if not hash_str:
        return False
    return hash_str.startswith('$2') and len(hash_str) >= 59


def migrate_users(dry_run: bool = False):
    """Migrate users from JSON file to database."""
    from flask import Flask
    from web.database import db, init_db, User
    from config_v2 import DATA_DIR

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'migration-key'
    init_db(app)

    json_path = DATA_DIR / 'users.json'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = DATA_DIR / f'users.json.backup_{timestamp}'

    with app.app_context():
        # Create tables if needed
        db.create_all()

        # Check for users.json
        if not json_path.exists():
            print(f"No users.json found at {json_path}")
            print("Nothing to migrate.")
            return

        # Load users from JSON
        with open(json_path, 'r') as f:
            data = json.load(f)

        json_users = data.get('users', [])
        print(f"\nFound {len(json_users)} users in users.json")

        # Check existing database users
        db_users = User.query.all()
        db_emails = {u.email.lower() for u in db_users}
        db_ids = {u.id for u in db_users}
        print(f"Found {len(db_users)} users already in database\n")

        # Track for duplicate detection
        seen_emails = {}
        users_to_add = []
        issues = []

        for user_data in json_users:
            user_id = user_data.get('id')
            email = user_data.get('email', '').strip().lower()
            password_hash = user_data.get('password_hash', '')

            # Validate email
            if not email or '@' not in email:
                issues.append(f"  SKIP: Invalid email: {email or '(empty)'}")
                continue

            # Check for duplicate email in JSON file
            if email in seen_emails:
                issues.append(f"  SKIP: Duplicate email in JSON: {email} (IDs: {seen_emails[email]}, {user_id})")
                continue
            seen_emails[email] = user_id

            # Check if already in database
            if email in db_emails:
                print(f"  SKIP: {email} (already in database)")
                continue

            if user_id in db_ids:
                issues.append(f"  SKIP: User ID {user_id} already in database with different email")
                continue

            # Validate password hash
            if not is_valid_bcrypt_hash(password_hash):
                issues.append(f"  WARN: {email} has invalid/empty password hash - will need password reset")
                # Still migrate, but flag it

            # Prepare user for migration
            user = User(
                id=user_id,
                email=email,
                password_hash=password_hash,
                name=user_data.get('name', ''),
                roles=user_data.get('roles', ['analyst']),
                active=user_data.get('active', True),
                tenant_id=user_data.get('tenant_id'),
            )

            # Parse timestamps
            if user_data.get('created_at'):
                try:
                    user.created_at = datetime.fromisoformat(
                        user_data['created_at'].replace('Z', '+00:00')
                    )
                except Exception:
                    pass

            if user_data.get('last_login'):
                try:
                    user.last_login = datetime.fromisoformat(
                        user_data['last_login'].replace('Z', '+00:00')
                    )
                except Exception:
                    pass

            users_to_add.append(user)
            action = "WOULD MIGRATE" if dry_run else "MIGRATE"
            roles = ', '.join(user.roles) if user.roles else 'analyst'
            print(f"  {action}: {email} (roles: {roles})")

        # Print issues
        if issues:
            print("\nIssues found:")
            for issue in issues:
                print(issue)

        # Summary
        print(f"\n{'=' * 50}")
        print(f"Migration {'preview' if dry_run else 'summary'}:")
        print(f"  To migrate: {len(users_to_add)}")
        print(f"  Skipped:    {len(json_users) - len(users_to_add)}")
        print(f"  Issues:     {len(issues)}")

        if dry_run:
            print("\nThis was a dry run. No changes were made.")
            print("Run without --dry-run to perform actual migration.")
            return

        if not users_to_add:
            print("\nNo users to migrate.")
            return

        # Create backup with timestamp
        shutil.copy2(json_path, backup_path)
        print(f"\nBacked up users.json to {backup_path}")

        # Migrate in single transaction
        try:
            for user in users_to_add:
                db.session.add(user)

            db.session.commit()
            print(f"\nSuccessfully migrated {len(users_to_add)} users!")

        except Exception as e:
            db.session.rollback()
            print(f"\nMigration failed: {e}")
            print("No changes were made to the database.")
            return

        print("\nNext steps:")
        print("1. Verify: SELECT COUNT(*) FROM users;")
        print("2. Test login with migrated users")
        print("3. Set AUTH_BACKEND=db in environment")
        print(f"4. Keep backup at {backup_path} for rollback")


def main():
    parser = argparse.ArgumentParser(
        description='Migrate users from JSON to database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview only, no changes'
    )
    args = parser.parse_args()

    migrate_users(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
```

---

### File 5: `web/auth/routes.py` (MODIFY)

**Add feature flag for gradual rollout:**

```python
import os

# Feature flag for auth backend
AUTH_BACKEND = os.environ.get('AUTH_BACKEND', 'json').lower()

def get_auth_backend():
    """Get the appropriate auth backend based on feature flag."""
    if AUTH_BACKEND == 'db':
        from web.services.auth_service import get_auth_service
        return get_auth_service()
    else:
        from web.models.user import get_user_store
        return get_user_store()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # ... existing GET handling ...

    if form.validate_on_submit():
        auth = get_auth_backend()
        user = auth.authenticate(form.email.data, form.password.data)
        # ... rest of login logic ...
```

---

### File 6: `web/app.py` (MODIFY)

**Update user_loader with feature flag:**

```python
import os

AUTH_BACKEND = os.environ.get('AUTH_BACKEND', 'json').lower()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    if AUTH_BACKEND == 'db':
        from web.services.auth_service import get_auth_service
        return get_auth_service().get_by_id(user_id)
    else:
        from web.models.user import get_user_store
        return get_user_store().get_by_id(user_id)


def init_auth():
    """Initialize authentication system."""
    if AUTH_BACKEND == 'db':
        from web.services.auth_service import get_auth_service
        auth = get_auth_service()
        # NO auto-bootstrap - use CLI command instead
        if not auth.admin_exists():
            logger.warning(
                "No admin user exists. Run 'flask create-admin' to create one."
            )
    else:
        # Legacy file-based auth
        from web.models.user import get_user_store
        user_store = get_user_store()
        user_store.ensure_admin_exists()
```

**Register CLI commands:**

```python
from web.cli import register_cli

def create_app():
    app = Flask(__name__)
    # ... existing setup ...
    register_cli(app)
    return app
```

---

## Migration Execution Steps

### Phase A: Prepare (No Impact to Production)

1. **Create new files:**
   - [ ] `web/repositories/user_repository.py`
   - [ ] `web/services/auth_service.py`
   - [ ] `web/cli.py`
   - [ ] `scripts/migrate_users_to_db.py`

2. **Update exports:**
   - [ ] `web/repositories/__init__.py`
   - [ ] `web/services/__init__.py`

3. **Test in isolation:**
   ```bash
   # Verify imports work
   python -c "from web.services.auth_service import get_auth_service"
   ```

### Phase B: Migrate Data

4. **Run migration dry-run:**
   ```bash
   python scripts/migrate_users_to_db.py --dry-run
   ```

5. **Review output for issues**

6. **Execute migration:**
   ```bash
   python scripts/migrate_users_to_db.py
   ```

7. **Verify migration:**
   ```sql
   -- Check user count
   SELECT COUNT(*) FROM users;

   -- List all users
   SELECT email, roles, active FROM users;

   -- Check for duplicates
   SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;
   ```

### Phase C: Switch Backend

8. **Update routes with feature flag:**
   - [ ] Modify `web/auth/routes.py`
   - [ ] Modify `web/app.py`

9. **Test with file backend (default):**
   ```bash
   # AUTH_BACKEND defaults to 'json'
   flask run
   # Test login/register
   ```

10. **Switch to database backend:**
    ```bash
    export AUTH_BACKEND=db
    flask run
    ```

11. **Create admin user (if needed):**
    ```bash
    flask create-admin --email admin@example.com
    ```

### Phase D: Verify

12. **Run verification checklist** (see below)

13. **Monitor for 24-48 hours**

### Phase E: Cleanup (After Verification)

14. **Remove feature flag** - hardcode to `db`
15. **Archive `users.json`**
16. **Deprecate `web/models/user.py` UserStore**

---

## Verification Checklist

### Auth Functionality Tests

| Test | Expected Result | Pass? |
|------|-----------------|-------|
| Login with migrated user | Success, redirect to dashboard | [ ] |
| Login with wrong password | Failure, error message | [ ] |
| Login with inactive user | Failure, error message | [ ] |
| Login with non-existent email | Failure, error message | [ ] |
| Register new user | Success, can login | [ ] |
| Register duplicate email | Failure, error message | [ ] |
| Change password | Success, old password fails | [ ] |
| Logout | Session cleared | [ ] |
| Flask-Login across requests | User persists in session | [ ] |
| Server restart | Sessions persist (if using DB sessions) | [ ] |

### Admin Bootstrap Tests

| Test | Expected Result | Pass? |
|------|-----------------|-------|
| `flask create-admin --email x` | Creates admin, shows generated password | [ ] |
| `flask create-admin --email x --password y` | Creates admin with given password | [ ] |
| `flask create-admin` (existing email) | Error: already exists | [ ] |
| `flask list-users` | Shows all users with roles | [ ] |
| App startup without admin | Warning in logs, no auto-create | [ ] |

### Data Integrity Tests

| Test | Expected Result | Pass? |
|------|-----------------|-------|
| Migrated user can login with old password | Success | [ ] |
| User IDs match (for FK integrity) | `deals.owner_id` still valid | [ ] |
| Roles preserved | Admin users still admin | [ ] |
| Timestamps preserved | `created_at` matches original | [ ] |

---

## Rollback Procedure

### Instant Rollback (Feature Flag)

```bash
# Switch back to file-based auth
export AUTH_BACKEND=json
# Restart app
```

No data loss - `users.json` is still there.

### Full Rollback (If Feature Flag Removed)

1. Restore `users.json` from timestamped backup
2. Revert code changes
3. Deploy

---

## Risks and Mitigations (Updated)

| Risk | Mitigation |
|------|------------|
| Hardcoded credentials | **Eliminated** - CLI command required |
| Transaction confusion | **Fixed** - AuthService owns commits, repos don't |
| JSON role query inefficient | **Fixed** - Postgres jsonb query with SQLite fallback |
| Migration failures | Single transaction, timestamped backup |
| Breaking prod during rollout | Feature flag enables instant rollback |

---

## Multi-Tenant Decision

**Current approach: Global (not tenant-scoped)**

- Email uniqueness is global
- `authenticate()` does not require tenant context
- `tenant_id` column exists but is optional

**Future phase (when needed):**
- Add `(tenant_id, email)` unique constraint
- Require tenant context in auth
- Scope all queries to tenant

---

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `web/repositories/user_repository.py` | CREATE | DB queries (no commits) |
| `web/services/auth_service.py` | CREATE | Auth logic (owns transactions) |
| `web/cli.py` | CREATE | Flask CLI commands |
| `scripts/migrate_users_to_db.py` | CREATE | Data migration script |
| `web/repositories/__init__.py` | MODIFY | Export UserRepository |
| `web/services/__init__.py` | MODIFY | Export AuthService |
| `web/auth/routes.py` | MODIFY | Add feature flag |
| `web/app.py` | MODIFY | Add feature flag, register CLI |
| `web/models/user.py` | DEPRECATE | Remove after verification |
