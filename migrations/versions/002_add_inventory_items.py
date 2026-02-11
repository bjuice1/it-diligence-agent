"""Add inventory_items table for deduplicated inventory storage

Revision ID: 002
Revises: 001
Create Date: 2026-02-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Create inventory_items table with content-hashed IDs."""

    op.create_table(
        'inventory_items',
        sa.Column('item_id', sa.String(length=50), nullable=False),
        sa.Column('deal_id', sa.String(length=36), nullable=False),
        sa.Column('inventory_type', sa.String(length=50), nullable=False),
        sa.Column('entity', sa.String(length=20), nullable=False, server_default='target'),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='active'),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('source_fact_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('source_files', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('source_type', sa.String(length=50), nullable=True, server_default='discovery'),
        sa.Column('is_enriched', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('enrichment_date', sa.DateTime(), nullable=True),
        sa.Column('needs_investigation', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('investigation_reason', sa.Text(), nullable=True, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('item_id'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
    )

    # Create indexes for fast queries
    op.create_index('idx_inventory_deal_type', 'inventory_items', ['deal_id', 'inventory_type'])
    op.create_index('idx_inventory_deal_entity', 'inventory_items', ['deal_id', 'entity'])
    op.create_index('idx_inventory_deal_status', 'inventory_items', ['deal_id', 'status'])
    op.create_index('idx_inventory_type_entity', 'inventory_items', ['inventory_type', 'entity'])
    op.create_index('idx_inventory_deleted', 'inventory_items', ['deleted_at'])


def downgrade():
    """Drop inventory_items table."""

    op.drop_index('idx_inventory_deleted', table_name='inventory_items')
    op.drop_index('idx_inventory_type_entity', table_name='inventory_items')
    op.drop_index('idx_inventory_deal_status', table_name='inventory_items')
    op.drop_index('idx_inventory_deal_entity', table_name='inventory_items')
    op.drop_index('idx_inventory_deal_type', table_name='inventory_items')
    op.drop_table('inventory_items')
