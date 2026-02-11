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
    # Note: PostgreSQL syntax - for SQLite this would be different
    op.create_check_constraint(
        'check_cost_status_values',
        'facts',
        "cost_status IS NULL OR cost_status IN ('known', 'unknown', 'internal_no_cost', 'estimated')"
    )

    # Create partial index for efficient querying of unknown costs
    # This index only includes rows where cost_status = 'unknown', making
    # "find apps needing cost discovery" queries very fast
    op.execute("""
        CREATE INDEX idx_facts_cost_status_unknown
        ON facts (deal_id, domain, entity)
        WHERE cost_status = 'unknown' AND deleted_at IS NULL
    """)

    # Create general index for cost_status queries
    op.create_index(
        'idx_facts_cost_status',
        'facts',
        ['deal_id', 'cost_status'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )

    # Migrate existing data: Extract cost_status from JSON details column
    # This uses PostgreSQL's JSON operators (->> for text extraction)
    op.execute("""
        UPDATE facts
        SET cost_status = details->>'cost_status'
        WHERE details ? 'cost_status'
          AND details->>'cost_status' IN ('known', 'unknown', 'internal_no_cost', 'estimated')
    """)

    # For facts that have cost in details but no cost_status, infer it
    # (This handles facts created before cost_status tracking was added)
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


def downgrade():
    """Remove cost_status column from facts table."""

    # Before dropping, migrate data back to JSON details (for safety)
    op.execute("""
        UPDATE facts
        SET details = jsonb_set(
            COALESCE(details, '{}'::jsonb),
            '{cost_status}',
            to_jsonb(cost_status)
        )
        WHERE cost_status IS NOT NULL
    """)

    # Drop indexes
    op.drop_index('idx_facts_cost_status', table_name='facts')
    op.execute("DROP INDEX IF EXISTS idx_facts_cost_status_unknown")

    # Drop CHECK constraint
    op.drop_constraint('check_cost_status_values', 'facts', type_='check')

    # Drop column
    op.drop_column('facts', 'cost_status')
