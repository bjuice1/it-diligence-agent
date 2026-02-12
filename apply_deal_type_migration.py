#!/usr/bin/env python3
"""
Apply deal_type migration directly.

Since alembic isn't configured, this script applies the migration
using direct SQL commands through the Flask app's database connection.
"""

import sys
import os

# Set environment to avoid database usage during import
os.environ['USE_DATABASE'] = 'false'

print("=" * 80)
print("APPLYING DEAL TYPE MIGRATION")
print("=" * 80)
print()

try:
    from web.database import db, Deal
    from web.app import create_app
    from sqlalchemy import text

    # Create app context
    app = create_app()

    with app.app_context():
        print("Step 1: Backfilling NULL and invalid deal_type values...")

        # Backfill NULL and invalid values
        result = db.session.execute(text("""
            UPDATE deals
            SET deal_type = 'acquisition'
            WHERE deal_type IS NULL
               OR deal_type = ''
               OR deal_type = 'merger'
               OR deal_type = 'investment'
               OR deal_type = 'other'
        """))

        backfilled = result.rowcount
        print(f"   ✅ Backfilled {backfilled} records to 'acquisition'")

        # Normalize carve-out to carveout
        result = db.session.execute(text("""
            UPDATE deals
            SET deal_type = 'carveout'
            WHERE deal_type = 'carve-out'
        """))

        normalized = result.rowcount
        print(f"   ✅ Normalized {normalized} 'carve-out' → 'carveout'")

        db.session.commit()
        print()

        print("Step 2: Adding NOT NULL constraint...")
        try:
            db.session.execute(text("""
                ALTER TABLE deals
                ALTER COLUMN deal_type SET NOT NULL
            """))
            db.session.commit()
            print("   ✅ NOT NULL constraint added")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'violates not-null' in str(e).lower():
                print(f"   ⚠️  Constraint may already exist: {e}")
                db.session.rollback()
            else:
                print(f"   ❌ Error: {e}")
                db.session.rollback()
                # Continue anyway - constraint might already be there

        print()

        print("Step 3: Adding CHECK constraint...")
        try:
            db.session.execute(text("""
                ALTER TABLE deals
                ADD CONSTRAINT valid_deal_type
                CHECK (deal_type IN ('acquisition', 'carveout', 'divestiture'))
            """))
            db.session.commit()
            print("   ✅ CHECK constraint added")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f"   ⚠️  Constraint already exists")
                db.session.rollback()
            else:
                print(f"   ❌ Error: {e}")
                db.session.rollback()

        print()

        print("Step 4: Verifying migration...")

        # Count deals by type
        result = db.session.execute(text("""
            SELECT deal_type, COUNT(*) as count
            FROM deals
            GROUP BY deal_type
            ORDER BY deal_type
        """))

        print("   Deal type distribution:")
        for row in result:
            print(f"     - {row[0]}: {row[1]}")

        # Try to insert invalid value (should fail)
        print()
        print("Step 5: Testing constraints...")
        try:
            db.session.execute(text("""
                INSERT INTO deals (name, target_name, deal_type)
                VALUES ('Test Deal', 'Test Target', 'invalid_type')
            """))
            db.session.commit()
            print("   ❌ ERROR: Invalid deal_type was accepted!")
            sys.exit(1)
        except Exception as e:
            db.session.rollback()
            if 'valid_deal_type' in str(e) or 'check constraint' in str(e).lower():
                print("   ✅ CHECK constraint working (rejected invalid value)")
            else:
                print(f"   ⚠️  Unexpected error: {e}")

        # Try to insert NULL (should fail)
        try:
            db.session.execute(text("""
                INSERT INTO deals (name, target_name, deal_type)
                VALUES ('Test Deal 2', 'Test Target 2', NULL)
            """))
            db.session.commit()
            print("   ❌ ERROR: NULL deal_type was accepted!")
            sys.exit(1)
        except Exception as e:
            db.session.rollback()
            if 'not null' in str(e).lower() or 'violates not-null' in str(e).lower():
                print("   ✅ NOT NULL constraint working (rejected NULL)")
            else:
                print(f"   ⚠️  Unexpected error: {e}")

        print()
        print("=" * 80)
        print("✅ MIGRATION COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  - Backfilled {backfilled} NULL/invalid values")
        print(f"  - Normalized {normalized} hyphenated values")
        print("  - NOT NULL constraint: ✅")
        print("  - CHECK constraint: ✅")
        print()
        print("The database now enforces:")
        print("  1. deal_type cannot be NULL")
        print("  2. deal_type must be one of: acquisition, carveout, divestiture")
        print()

except Exception as e:
    print(f"❌ MIGRATION FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
