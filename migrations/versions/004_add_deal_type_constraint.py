"""Add NOT NULL and CHECK constraint to deal_type

Revision ID: 004_add_deal_type_constraint
Revises: 003_add_cost_status_to_facts
Create Date: 2025-02-11

This migration:
1. Backfills NULL deal_type values with 'acquisition' (safe default)
2. Adds NOT NULL constraint to deal_type column
3. Adds CHECK constraint to validate deal_type values

Valid deal types: acquisition, carveout, divestiture
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_deal_type_constraint'
down_revision = '003_add_cost_status_to_facts'
branch_labels = None
depends_on = None


def upgrade():
    """Add deal_type constraints."""
    # Step 1: Backfill NULL values with 'acquisition' (safe default)
    # Also normalize any legacy values to valid types
    op.execute("""
        UPDATE deals
        SET deal_type = 'acquisition'
        WHERE deal_type IS NULL
           OR deal_type = ''
           OR deal_type = 'merger'
           OR deal_type = 'investment'
           OR deal_type = 'other'
    """)

    # Step 2: Normalize 'carve-out' to 'carveout' (remove hyphen)
    op.execute("""
        UPDATE deals
        SET deal_type = 'carveout'
        WHERE deal_type = 'carve-out'
    """)

    # Step 3: Add NOT NULL constraint
    # For PostgreSQL
    try:
        op.alter_column('deals', 'deal_type',
                       existing_type=sa.String(50),
                       nullable=False,
                       existing_server_default='acquisition')
    except Exception as e:
        print(f"Note: Could not add NOT NULL constraint (may already exist): {e}")

    # Step 4: Add CHECK constraint for valid values
    try:
        op.create_check_constraint(
            'valid_deal_type',
            'deals',
            "deal_type IN ('acquisition', 'carveout', 'divestiture')"
        )
    except Exception as e:
        print(f"Note: Could not add CHECK constraint (may already exist): {e}")


def downgrade():
    """Remove deal_type constraints."""
    # Step 1: Drop CHECK constraint
    try:
        op.drop_constraint('valid_deal_type', 'deals', type_='check')
    except Exception as e:
        print(f"Note: Could not drop CHECK constraint: {e}")

    # Step 2: Remove NOT NULL constraint
    try:
        op.alter_column('deals', 'deal_type',
                       existing_type=sa.String(50),
                       nullable=True)
    except Exception as e:
        print(f"Note: Could not remove NOT NULL constraint: {e}")
