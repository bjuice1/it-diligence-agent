"""Add cost_status column to facts table for efficient cost quality queries

Revision ID: 003
Revises: 002
Create Date: 2026-02-11

Background:
Previously, cost_status was stored only in the JSON details column, making it
impossible to query efficiently. This migration adds a dedicated cost_status
column with CHECK constraint and partial index for performance.

Addresses: P0 Finding #2 from adversarial analysis
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Add cost_status column to facts table."""
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    dialect = bind.dialect.name

    # Check if column already exists (idempotency)
    columns = [c['name'] for c in inspector.get_columns('facts')]
    if 'cost_status' in columns:
        print("cost_status column already exists, skipping creation")
        return

    # Add cost_status column with CHECK constraint
    op.add_column(
        'facts',
        sa.Column(
            'cost_status',
            sa.String(length=20),
            nullable=True,  # Nullable to support existing records
        )
    )

    # Add CHECK constraint for allowed values
    # SQLite enforces CHECK constraints as of version 3.3.0 (2006)
    op.create_check_constraint(
        'check_cost_status_values',
        'facts',
        "cost_status IS NULL OR cost_status IN ('known', 'unknown', 'internal_no_cost', 'estimated')"
    )

    # Create indexes - syntax differs by database
    if dialect == 'postgresql':
        # PostgreSQL supports partial indexes with WHERE clause
        op.execute("""
            CREATE INDEX idx_facts_cost_status_unknown
            ON facts (deal_id, domain, entity)
            WHERE cost_status = 'unknown' AND deleted_at IS NULL
        """)

        # General index with partial WHERE clause
        op.create_index(
            'idx_facts_cost_status',
            'facts',
            ['deal_id', 'cost_status'],
            postgresql_where=sa.text('deleted_at IS NULL')
        )
    else:
        # SQLite doesn't support partial indexes with WHERE clause
        # Create full indexes instead (less efficient but functional)
        op.create_index(
            'idx_facts_cost_status_unknown',
            'facts',
            ['deal_id', 'domain', 'entity', 'cost_status']
        )

        op.create_index(
            'idx_facts_cost_status',
            'facts',
            ['deal_id', 'cost_status']
        )

    # Migrate existing data: Extract cost_status from JSON details column
    # Syntax differs between PostgreSQL and SQLite
    if dialect == 'postgresql':
        # PostgreSQL JSON operators: ->> for text extraction, ? for key existence
        op.execute("""
            UPDATE facts
            SET cost_status = details->>'cost_status'
            WHERE details ? 'cost_status'
              AND details->>'cost_status' IN ('known', 'unknown', 'internal_no_cost', 'estimated')
        """)

        # For facts that have cost in details but no cost_status, infer it
        op.execute("""
            UPDATE facts
            SET cost_status = CASE
                WHEN details ? 'cost' OR details ? 'annual_cost' THEN 'known'
                ELSE NULL
            END
            WHERE cost_status IS NULL
              AND domain = 'applications'
              AND deleted_at IS NULL
        """)
    else:
        # SQLite JSON functions: json_extract with path
        op.execute("""
            UPDATE facts
            SET cost_status = json_extract(details, '$.cost_status')
            WHERE json_extract(details, '$.cost_status') IS NOT NULL
              AND json_extract(details, '$.cost_status') IN ('known', 'unknown', 'internal_no_cost', 'estimated')
        """)

        # For facts that have cost in details but no cost_status, infer it
        op.execute("""
            UPDATE facts
            SET cost_status = CASE
                WHEN json_extract(details, '$.cost') IS NOT NULL
                  OR json_extract(details, '$.annual_cost') IS NOT NULL THEN 'known'
                ELSE NULL
            END
            WHERE cost_status IS NULL
              AND domain = 'applications'
              AND deleted_at IS NULL
        """)


def downgrade():
    """Remove cost_status column from facts table."""
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    dialect = bind.dialect.name

    # Check if column exists before trying to drop it
    columns = [c['name'] for c in inspector.get_columns('facts')]
    if 'cost_status' not in columns:
        print("cost_status column doesn't exist, skipping removal")
        return

    # Before dropping, migrate data back to JSON details (for safety)
    # Syntax differs between PostgreSQL and SQLite
    if dialect == 'postgresql':
        # PostgreSQL jsonb_set function
        op.execute("""
            UPDATE facts
            SET details = jsonb_set(
                COALESCE(details, '{}'::jsonb),
                '{cost_status}',
                to_jsonb(cost_status)
            )
            WHERE cost_status IS NOT NULL
        """)
    else:
        # SQLite json_set function
        op.execute("""
            UPDATE facts
            SET details = json_set(
                COALESCE(details, '{}'),
                '$.cost_status',
                cost_status
            )
            WHERE cost_status IS NOT NULL
        """)

    # Drop indexes (check existence first for idempotency)
    try:
        op.drop_index('idx_facts_cost_status', table_name='facts')
    except Exception:
        pass  # Index might not exist

    try:
        if dialect == 'postgresql':
            op.execute("DROP INDEX IF EXISTS idx_facts_cost_status_unknown")
        else:
            op.drop_index('idx_facts_cost_status_unknown', table_name='facts')
    except Exception:
        pass  # Index might not exist

    # Drop CHECK constraint
    try:
        op.drop_constraint('check_cost_status_values', 'facts', type_='check')
    except Exception:
        pass  # Constraint might not exist or not enforced on SQLite

    # Drop column
    op.drop_column('facts', 'cost_status')
