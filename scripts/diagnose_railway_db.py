#!/usr/bin/env python3
"""
Railway Database Diagnostic Script

Tests PostgreSQL connection and database state on Railway.
Run this on Railway to diagnose database initialization issues.

Usage:
    python scripts/diagnose_railway_db.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def diagnose():
    """Run comprehensive database diagnostics."""
    print("=" * 70)
    print("RAILWAY DATABASE DIAGNOSTICS")
    print("=" * 70)

    # Check 1: Environment Variables
    print("\n[1] ENVIRONMENT VARIABLES")
    print("-" * 70)

    database_url = os.environ.get('DATABASE_URL', '')
    if database_url:
        # Mask password for security
        if '@' in database_url:
            parts = database_url.split('@')
            if ':' in parts[0]:
                cred_parts = parts[0].split(':')
                masked = cred_parts[0] + ':****@' + '@'.join(parts[1:])
                print(f"✓ DATABASE_URL set: {masked[:60]}...")
            else:
                print(f"✓ DATABASE_URL set: {database_url[:60]}...")
        else:
            print(f"✓ DATABASE_URL set: {database_url[:60]}...")
    else:
        print("✗ DATABASE_URL not set!")
        print("  This is the problem - Flask app cannot connect to database.")
        print("\nSOLUTION:")
        print("  1. Go to Railway project")
        print("  2. Click on PostgreSQL service")
        print("  3. Go to 'Variables' tab")
        print("  4. Copy DATABASE_URL")
        print("  5. Go to your app service")
        print("  6. Add DATABASE_URL variable with the copied value")
        return False

    use_database = os.environ.get('USE_DATABASE', 'true').lower()
    print(f"  USE_DATABASE: {use_database}")

    # Check 2: Database Connection
    print("\n[2] DATABASE CONNECTION")
    print("-" * 70)

    try:
        from flask import Flask
        from web.database import db, init_db

        app = Flask(__name__)
        init_db(app)

        with app.app_context():
            # Test connection
            db.session.execute(db.text('SELECT 1'))
            print("✓ Database connection successful")

            # Check database info
            result = db.session.execute(db.text('SELECT version()')).fetchone()
            print(f"  PostgreSQL version: {result[0].split(',')[0]}")

    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nPOSSIBLE CAUSES:")
        print("  - DATABASE_URL format incorrect")
        print("  - PostgreSQL service not running")
        print("  - Network connectivity issues")
        print("  - Insufficient permissions")
        return False

    # Check 3: Tables
    print("\n[3] DATABASE TABLES")
    print("-" * 70)

    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if tables:
            print(f"✓ Found {len(tables)} tables:")
            for table in sorted(tables):
                # Get row count
                try:
                    result = db.session.execute(
                        db.text(f'SELECT COUNT(*) FROM "{table}"')
                    ).fetchone()
                    count = result[0]
                    print(f"  - {table}: {count} rows")
                except Exception as e:
                    print(f"  - {table}: (query failed)")
        else:
            print("✗ No tables found!")
            print("\nSOLUTION:")
            print("  Run database initialization:")
            print("  python scripts/init_db.py")
            return False

    except Exception as e:
        print(f"✗ Could not inspect tables: {e}")
        return False

    # Check 4: Required Tables
    print("\n[4] REQUIRED TABLES CHECK")
    print("-" * 70)

    required_tables = [
        'tenants', 'users', 'deals', 'documents',
        'facts', 'findings', 'analysis_runs',
        'pending_changes', 'deal_snapshots',
        'notifications', 'fact_finding_links', 'audit_log'
    ]

    missing = []
    for table in required_tables:
        if table in tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} (missing)")
            missing.append(table)

    if missing:
        print(f"\n✗ Missing {len(missing)} required tables")
        print("\nSOLUTION:")
        print("  python scripts/init_db.py")
        return False

    # Check 5: Test Data Insertion
    print("\n[5] TEST WRITE")
    print("-" * 70)

    try:
        from web.database import Tenant

        # Try to query tenants
        tenant_count = Tenant.query.count()
        print(f"✓ Can read from database: {tenant_count} tenants")

    except Exception as e:
        print(f"✗ Cannot read from database: {e}")
        return False

    # Summary
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE - ALL CHECKS PASSED ✓")
    print("=" * 70)
    print("\nDatabase is properly configured and operational.")
    return True


if __name__ == '__main__':
    try:
        success = diagnose()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDiagnostics interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
