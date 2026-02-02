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
    # Import Flask app components
    from flask import Flask
    from web.database import db, init_db, User

    # Try to import config
    try:
        from config_v2 import DATA_DIR
    except ImportError:
        DATA_DIR = Path(__file__).parent.parent / 'data'

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'migration-key'

    # Initialize database
    init_db(app)

    json_path = DATA_DIR / 'users.json' if isinstance(DATA_DIR, Path) else Path(DATA_DIR) / 'users.json'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = json_path.parent / f'users.json.backup_{timestamp}'

    with app.app_context():
        # Create tables if needed
        db.create_all()

        # Check for users.json
        if not json_path.exists():
            print(f"No users.json found at {json_path}")
            print("Nothing to migrate.")
            return

        # Load users from JSON
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error reading users.json: {e}")
            return

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
        skipped = 0

        for user_data in json_users:
            user_id = user_data.get('id')
            email = user_data.get('email', '').strip().lower()
            password_hash = user_data.get('password_hash', '')

            # Validate email
            if not email or '@' not in email:
                issues.append(f"  SKIP: Invalid email: {email or '(empty)'}")
                skipped += 1
                continue

            # Check for duplicate email in JSON file
            if email in seen_emails:
                issues.append(f"  SKIP: Duplicate email in JSON: {email} (IDs: {seen_emails[email]}, {user_id})")
                skipped += 1
                continue
            seen_emails[email] = user_id

            # Check if already in database by email
            if email in db_emails:
                print(f"  SKIP: {email} (already in database)")
                skipped += 1
                continue

            # Check if already in database by ID
            if user_id in db_ids:
                issues.append(f"  SKIP: User ID {user_id} already in database with different email")
                skipped += 1
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
                    created_str = user_data['created_at']
                    if created_str.endswith('Z'):
                        created_str = created_str[:-1] + '+00:00'
                    user.created_at = datetime.fromisoformat(created_str)
                except Exception:
                    pass  # Use default

            if user_data.get('last_login'):
                try:
                    login_str = user_data['last_login']
                    if login_str.endswith('Z'):
                        login_str = login_str[:-1] + '+00:00'
                    user.last_login = datetime.fromisoformat(login_str)
                except Exception:
                    pass  # Leave as None

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
        print(f"  Skipped:    {skipped}")
        print(f"  Issues:     {len([i for i in issues if 'WARN' in i])}")

        if dry_run:
            print("\nThis was a dry run. No changes were made.")
            print("Run without --dry-run to perform actual migration.")
            return

        if not users_to_add:
            print("\nNo users to migrate.")
            return

        # Create backup with timestamp
        try:
            shutil.copy2(json_path, backup_path)
            print(f"\nBacked up users.json to {backup_path}")
        except Exception as e:
            print(f"\nWarning: Could not create backup: {e}")
            response = input("Continue without backup? (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                return

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
