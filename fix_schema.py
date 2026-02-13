#!/usr/bin/env python3
"""
Quick fix: Add missing investigation_reason column to inventory_items table
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from web.app import app
from web.database import db

def add_missing_column():
    """Add investigation_reason column if missing"""
    print("=" * 70)
    print("FIXING DATABASE SCHEMA - Adding investigation_reason column")
    print("=" * 70)

    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(db.text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='inventory_items'
                AND column_name='investigation_reason'
            """))

            if result.fetchone():
                print("✓ investigation_reason column already exists")
                return

            print("Adding investigation_reason column...")

            # Add the column
            db.session.execute(db.text("""
                ALTER TABLE inventory_items
                ADD COLUMN investigation_reason TEXT DEFAULT ''
            """))

            db.session.commit()
            print("✓ Column added successfully")

            # Verify
            result = db.session.execute(db.text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='inventory_items'
                AND column_name='investigation_reason'
            """))

            if result.fetchone():
                print("✓ Verified: investigation_reason column exists")
            else:
                print("❌ Verification failed!")
                sys.exit(1)

            print("\n" + "=" * 70)
            print("SCHEMA FIX COMPLETE ✓")
            print("=" * 70)

        except Exception as e:
            print(f"❌ Fix failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    add_missing_column()
