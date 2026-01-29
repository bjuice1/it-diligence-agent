"""Initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2026-01-28

Creates all tables for Phase 1 Database Foundation:
- tenants (multi-tenancy support)
- users (authentication)
- deals (central organizing entity)
- documents (with versioning)
- facts (with soft delete, provenance)
- findings (risks, work items, recommendations)
- fact_finding_links (normalized junction table)
- analysis_runs (run tracking)
- pending_changes (incremental update queue)
- deal_snapshots (rollback support)
- notifications (user alerts)
- audit_log (activity tracking)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('plan', sa.String(50), default='free'),
        sa.Column('plan_expires_at', sa.DateTime, nullable=True),
        sa.Column('settings', sa.JSON, default=dict),
        sa.Column('max_users', sa.Integer, default=5),
        sa.Column('max_deals', sa.Integer, default=10),
        sa.Column('max_storage_mb', sa.Integer, default=500),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('suspended_at', sa.DateTime, nullable=True),
        sa.Column('suspended_reason', sa.String(255), default=''),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_tenants_slug', 'tenants', ['slug'])

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), default=''),
        sa.Column('roles', sa.JSON, default=['analyst']),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('last_login', sa.DateTime, nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])

    # Deals table
    op.create_table(
        'deals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False, default=''),
        sa.Column('target_name', sa.String(255), nullable=False),
        sa.Column('buyer_name', sa.String(255), default=''),
        sa.Column('deal_type', sa.String(50), default='acquisition'),
        sa.Column('industry', sa.String(100), default=''),
        sa.Column('sub_industry', sa.String(100), default=''),
        sa.Column('deal_value', sa.String(50), default=''),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('target_locked', sa.Boolean, default=False),
        sa.Column('buyer_locked', sa.Boolean, default=False),
        sa.Column('locked_at', sa.DateTime, nullable=True),
        sa.Column('locked_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('documents_uploaded', sa.Integer, default=0),
        sa.Column('facts_extracted', sa.Integer, default=0),
        sa.Column('findings_count', sa.Integer, default=0),
        sa.Column('analysis_runs_count', sa.Integer, default=0),
        sa.Column('review_percent', sa.Float, default=0.0),
        sa.Column('context', sa.JSON, default=dict),
        sa.Column('settings', sa.JSON, default=dict),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_accessed_at', sa.DateTime, default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('idx_deals_tenant_status', 'deals', ['tenant_id', 'status'])
    op.create_index('idx_deals_owner', 'deals', ['owner_id'])
    op.create_index('idx_deals_deleted', 'deals', ['deleted_at'])

    # Deal snapshots table (created before analysis_runs due to FK)
    op.create_table(
        'deal_snapshots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('deal_id', sa.String(36), sa.ForeignKey('deals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_number', sa.Integer, nullable=False),
        sa.Column('snapshot_type', sa.String(50), default='pre_analysis'),
        sa.Column('description', sa.String(255), default=''),
        sa.Column('facts_data', sa.JSON, default=list),
        sa.Column('findings_data', sa.JSON, default=list),
        sa.Column('documents_data', sa.JSON, default=list),
        sa.Column('deal_context', sa.JSON, default=dict),
        sa.Column('facts_count', sa.Integer, default=0),
        sa.Column('findings_count', sa.Integer, default=0),
        sa.Column('documents_count', sa.Integer, default=0),
        sa.Column('data_size_bytes', sa.Integer, default=0),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_snapshots_deal', 'deal_snapshots', ['deal_id'])
    op.create_index('idx_snapshots_created', 'deal_snapshots', ['created_at'])
    op.create_unique_constraint('uq_deal_snapshot_number', 'deal_snapshots', ['deal_id', 'snapshot_number'])

    # Analysis runs table
    op.create_table(
        'analysis_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('deal_id', sa.String(36), sa.ForeignKey('deals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_number', sa.Integer, nullable=False),
        sa.Column('run_type', sa.String(50), default='full'),
        sa.Column('domains', sa.JSON, default=list),
        sa.Column('entity', sa.String(20), default='target'),
        sa.Column('documents_analyzed', sa.JSON, default=list),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('progress', sa.Float, default=0.0),
        sa.Column('current_step', sa.String(100), default=''),
        sa.Column('facts_created', sa.Integer, default=0),
        sa.Column('facts_updated', sa.Integer, default=0),
        sa.Column('facts_unchanged', sa.Integer, default=0),
        sa.Column('findings_created', sa.Integer, default=0),
        sa.Column('findings_updated', sa.Integer, default=0),
        sa.Column('errors_count', sa.Integer, default=0),
        sa.Column('error_message', sa.Text, default=''),
        sa.Column('error_details', sa.JSON, default=dict),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=True),
        sa.Column('initiated_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('pre_run_snapshot_id', sa.String(36), sa.ForeignKey('deal_snapshots.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('idx_analysis_runs_deal', 'analysis_runs', ['deal_id'])
    op.create_index('idx_analysis_runs_status', 'analysis_runs', ['status'])
    op.create_unique_constraint('uq_deal_run_number', 'analysis_runs', ['deal_id', 'run_number'])

    # Documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('deal_id', sa.String(36), sa.ForeignKey('deals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False, default=''),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('file_size', sa.Integer, default=0),
        sa.Column('mime_type', sa.String(100), default=''),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('previous_version_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_current', sa.Boolean, default=True),
        sa.Column('entity', sa.String(20), nullable=False, default='target'),
        sa.Column('authority_level', sa.Integer, default=1),
        sa.Column('document_type', sa.String(50), default=''),
        sa.Column('document_category', sa.String(100), default=''),
        sa.Column('storage_path', sa.Text, nullable=False),
        sa.Column('storage_type', sa.String(20), default='local'),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('extracted_text', sa.Text, default=''),
        sa.Column('page_count', sa.Integer, default=0),
        sa.Column('word_count', sa.Integer, default=0),
        sa.Column('processing_error', sa.Text, default=''),
        sa.Column('content_checksum', sa.String(64), nullable=True),
        sa.Column('extra_metadata', sa.JSON, default=dict),
        sa.Column('uploaded_at', sa.DateTime, default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime, nullable=True),
        sa.Column('uploaded_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_documents_deal_entity', 'documents', ['deal_id', 'entity'])
    op.create_index('idx_documents_hash', 'documents', ['file_hash'])
    op.create_index('idx_documents_deleted', 'documents', ['deleted_at'])
    op.create_index('idx_documents_current', 'documents', ['deal_id', 'is_current'])

    # Facts table
    op.create_table(
        'facts',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('deal_id', sa.String(36), sa.ForeignKey('deals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('analysis_run_id', sa.String(36), sa.ForeignKey('analysis_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('domain', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100), default=''),
        sa.Column('entity', sa.String(20), nullable=False, default='target'),
        sa.Column('item', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), default='documented'),
        sa.Column('details', sa.JSON, default=dict),
        sa.Column('evidence', sa.JSON, default=dict),
        sa.Column('source_document', sa.String(255), default=''),
        sa.Column('source_page_numbers', sa.JSON, default=list),
        sa.Column('source_quote', sa.Text, default=''),
        sa.Column('confidence_score', sa.Float, default=0.5),
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('verified_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('verification_status', sa.String(50), default='pending'),
        sa.Column('verification_note', sa.Text, default=''),
        sa.Column('needs_review', sa.Boolean, default=False),
        sa.Column('needs_review_reason', sa.Text, default=''),
        sa.Column('analysis_phase', sa.String(50), default='target_extraction'),
        sa.Column('is_integration_insight', sa.Boolean, default=False),
        sa.Column('related_domains', sa.JSON, default=list),
        sa.Column('change_type', sa.String(20), default='new'),
        sa.Column('previous_version_id', sa.String(50), nullable=True),
        sa.Column('content_checksum', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_facts_deal_domain', 'facts', ['deal_id', 'domain'])
    op.create_index('idx_facts_deal_entity', 'facts', ['deal_id', 'entity'])
    op.create_index('idx_facts_verification', 'facts', ['deal_id', 'verification_status'])
    op.create_index('idx_facts_deleted', 'facts', ['deleted_at'])
    op.create_index('idx_facts_change_type', 'facts', ['deal_id', 'change_type'])

    # Findings table
    op.create_table(
        'findings',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('deal_id', sa.String(36), sa.ForeignKey('deals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_run_id', sa.String(36), sa.ForeignKey('analysis_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('finding_type', sa.String(50), nullable=False),
        sa.Column('domain', sa.String(50), nullable=False),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('description', sa.Text, default=''),
        sa.Column('reasoning', sa.Text, default=''),
        sa.Column('confidence', sa.String(20), default='medium'),
        sa.Column('mna_lens', sa.String(50), default=''),
        sa.Column('mna_implication', sa.Text, default=''),
        sa.Column('based_on_facts', sa.JSON, default=list),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('category', sa.String(100), default=''),
        sa.Column('mitigation', sa.Text, default=''),
        sa.Column('integration_dependent', sa.Boolean, default=False),
        sa.Column('timeline', sa.String(100), nullable=True),
        sa.Column('phase', sa.String(50), nullable=True),
        sa.Column('priority', sa.String(20), nullable=True),
        sa.Column('owner_type', sa.String(50), nullable=True),
        sa.Column('cost_estimate', sa.String(50), nullable=True),
        sa.Column('triggered_by_risks', sa.JSON, default=list),
        sa.Column('dependencies', sa.JSON, default=list),
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('urgency', sa.String(50), nullable=True),
        sa.Column('rationale', sa.Text, default=''),
        sa.Column('lens', sa.String(50), nullable=True),
        sa.Column('implication', sa.Text, default=''),
        sa.Column('extra_data', sa.JSON, default=dict),
        sa.Column('change_type', sa.String(20), default='new'),
        sa.Column('previous_version_id', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_findings_deal_type', 'findings', ['deal_id', 'finding_type'])
    op.create_index('idx_findings_deal_domain', 'findings', ['deal_id', 'domain'])
    op.create_index('idx_findings_severity', 'findings', ['deal_id', 'finding_type', 'severity'])
    op.create_index('idx_findings_deleted', 'findings', ['deleted_at'])
    op.create_index('idx_findings_change_type', 'findings', ['deal_id', 'change_type'])

    # Fact-Finding links junction table
    op.create_table(
        'fact_finding_links',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('fact_id', sa.String(50), sa.ForeignKey('facts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('finding_id', sa.String(50), sa.ForeignKey('findings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(50), default='supports'),
        sa.Column('relevance_score', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('idx_fact_finding_fact', 'fact_finding_links', ['fact_id'])
    op.create_index('idx_fact_finding_finding', 'fact_finding_links', ['finding_id'])
    op.create_unique_constraint('uq_fact_finding', 'fact_finding_links', ['fact_id', 'finding_id'])

    # Pending changes table
    op.create_table(
        'pending_changes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('deal_id', sa.String(36), sa.ForeignKey('deals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_run_id', sa.String(36), sa.ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=True),
        sa.Column('change_type', sa.String(20), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('tier', sa.Integer, default=1),
        sa.Column('new_data', sa.JSON, nullable=True),
        sa.Column('old_data', sa.JSON, nullable=True),
        sa.Column('diff_summary', sa.Text, default=''),
        sa.Column('fields_changed', sa.JSON, default=list),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('reviewed_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('review_note', sa.Text, default=''),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('applied_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_pending_changes_deal', 'pending_changes', ['deal_id'])
    op.create_index('idx_pending_changes_status', 'pending_changes', ['status'])
    op.create_index('idx_pending_changes_tier', 'pending_changes', ['deal_id', 'tier'])

    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('deal_id', sa.String(36), sa.ForeignKey('deals.id', ondelete='CASCADE'), nullable=True),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, default=''),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('priority', sa.String(20), default='normal'),
        sa.Column('read', sa.Boolean, default=False),
        sa.Column('read_at', sa.DateTime, nullable=True),
        sa.Column('dismissed', sa.Boolean, default=False),
        sa.Column('extra_data', sa.JSON, default=dict),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_notifications_user', 'notifications', ['user_id'])
    op.create_index('idx_notifications_unread', 'notifications', ['user_id', 'read'])
    op.create_index('idx_notifications_created', 'notifications', ['created_at'])

    # Audit log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deal_id', sa.String(36), sa.ForeignKey('deals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('details', sa.JSON, default=dict),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('idx_audit_tenant', 'audit_log', ['tenant_id'])
    op.create_index('idx_audit_deal', 'audit_log', ['deal_id'])
    op.create_index('idx_audit_user', 'audit_log', ['user_id'])
    op.create_index('idx_audit_created', 'audit_log', ['created_at'])


def downgrade():
    op.drop_table('audit_log')
    op.drop_table('notifications')
    op.drop_table('pending_changes')
    op.drop_table('fact_finding_links')
    op.drop_table('findings')
    op.drop_table('facts')
    op.drop_table('documents')
    op.drop_table('analysis_runs')
    op.drop_table('deal_snapshots')
    op.drop_table('deals')
    op.drop_table('users')
    op.drop_table('tenants')
