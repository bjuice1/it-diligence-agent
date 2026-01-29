#!/usr/bin/env python3
"""
Database Initialization Script

Sets up the PostgreSQL database with all tables and initial data.
Run this after starting the Docker containers.

Usage:
    python scripts/init_db.py [--force]

Options:
    --force     Drop and recreate all tables (WARNING: destroys data)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / 'docker' / '.env')
load_dotenv(project_root / '.env')


def create_app():
    """Create Flask app for database initialization."""
    from flask import Flask
    from web.database import db, migrate, init_db

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key')

    init_db(app)

    return app


def init_database(force: bool = False):
    """Initialize the database."""
    print("=" * 60)
    print("IT Diligence Agent - Database Initialization")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        from web.database import db, User, Tenant, Deal

        database_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        print(f"\nDatabase: {database_url[:50]}...")

        if force:
            print("\n⚠️  Force mode: Dropping all tables...")
            db.drop_all()
            print("   Tables dropped.")

        print("\nCreating tables...")
        db.create_all()
        print("   Tables created.")

        # Check if we need to create default data
        user_count = User.query.count()

        if user_count == 0:
            print("\nCreating default admin user...")

            # Create default tenant
            tenant = Tenant(
                name='Default Organization',
                slug='default',
                plan='professional',
                max_users=100,
                max_deals=1000
            )
            db.session.add(tenant)
            db.session.flush()

            # Create admin user
            import bcrypt
            password_hash = bcrypt.hashpw(
                'changeme123'.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            admin = User(
                email='admin@example.com',
                password_hash=password_hash,
                name='Admin',
                roles=['admin', 'analyst'],
                tenant_id=tenant.id,
                active=True
            )
            db.session.add(admin)
            db.session.commit()

            print("   Created: admin@example.com / changeme123")
            print("   ⚠️  Change this password immediately!")

        else:
            print(f"\n   Found {user_count} existing user(s). Skipping default user creation.")

        # Verify tables
        print("\nVerifying tables...")
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        expected_tables = [
            'tenants', 'users', 'deals', 'documents',
            'facts', 'findings', 'analysis_runs',
            'pending_changes', 'deal_snapshots',
            'notifications', 'fact_finding_links', 'audit_log'
        ]

        for table in expected_tables:
            if table in tables:
                print(f"   ✓ {table}")
            else:
                print(f"   ✗ {table} (missing!)")

        print("\n" + "=" * 60)
        print("Database initialization complete!")
        print("=" * 60)


def run_migrations():
    """Run any pending Alembic migrations."""
    print("\nRunning migrations...")

    app = create_app()

    with app.app_context():
        from flask_migrate import upgrade
        upgrade()

    print("   Migrations complete.")


def create_fulltext_index():
    """
    Create PostgreSQL full-text search index.

    This index enables fast text search across facts.
    Only works with PostgreSQL, skipped for SQLite.
    """
    app = create_app()

    with app.app_context():
        from web.database import db
        from sqlalchemy import text

        # Check if PostgreSQL
        bind = db.session.get_bind()
        if 'postgresql' not in str(bind.dialect.name):
            print("\n   Skipping full-text index (SQLite detected)")
            return

        print("\nCreating full-text search index...")

        try:
            # Create GIN index for full-text search on facts
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_facts_fulltext
                ON facts
                USING GIN (to_tsvector('english', item || ' ' || COALESCE(source_quote, '')))
            """))
            db.session.commit()
            print("   ✓ idx_facts_fulltext created")

        except Exception as e:
            print(f"   ✗ Error creating index: {e}")
            db.session.rollback()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Initialize the database')
    parser.add_argument('--force', action='store_true',
                        help='Drop and recreate all tables')
    parser.add_argument('--migrate', action='store_true',
                        help='Run Alembic migrations')

    args = parser.parse_args()

    if args.migrate:
        run_migrations()
    else:
        init_database(force=args.force)
        create_fulltext_index()
