"""
Database Configuration and Models for IT Due Diligence Agent

Phase 3: PostgreSQL database with SQLAlchemy ORM.
Supports both PostgreSQL (production) and SQLite (development/testing).
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from flask_login import UserMixin

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """Initialize database with Flask app."""
    # Configure database URL from environment
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Handle Heroku-style postgres:// URLs
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Default to SQLite for local development
        from config_v2 import DATA_DIR
        sqlite_path = DATA_DIR / 'diligence.db'
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # Handle stale connections
    }

    db.init_app(app)
    migrate.init_app(app, db)

    return db


def generate_uuid():
    """Generate a new UUID string."""
    return str(uuid.uuid4())


# =============================================================================
# TENANT MODEL (Phase 6: Multi-Tenancy)
# =============================================================================

class Tenant(db.Model):
    """Organization/tenant for multi-tenancy support."""
    __tablename__ = 'tenants'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-friendly identifier

    # Subscription/plan info
    plan = Column(String(50), default='free')  # free, starter, professional, enterprise
    plan_expires_at = Column(DateTime, nullable=True)

    # Tenant settings
    settings = Column(JSON, default=dict)  # Custom settings per tenant

    # Limits based on plan
    max_users = Column(Integer, default=5)
    max_deals = Column(Integer, default=10)
    max_storage_mb = Column(Integer, default=500)

    # Status
    active = Column(Boolean, default=True)
    suspended_at = Column(DateTime, nullable=True)
    suspended_reason = Column(String(255), default='')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship('User', back_populates='tenant', lazy='dynamic')
    deals = relationship('Deal', back_populates='tenant', lazy='dynamic')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'plan': self.plan,
            'plan_expires_at': self.plan_expires_at.isoformat() if self.plan_expires_at else None,
            'settings': self.settings,
            'max_users': self.max_users,
            'max_deals': self.max_deals,
            'max_storage_mb': self.max_storage_mb,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def is_within_user_limit(self) -> bool:
        """Check if tenant can add more users."""
        return self.users.count() < self.max_users

    def is_within_deal_limit(self) -> bool:
        """Check if tenant can create more deals."""
        return self.deals.count() < self.max_deals


# =============================================================================
# USER MODEL
# =============================================================================

class User(db.Model, UserMixin):
    """User model for authentication."""
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), default='')
    roles = Column(JSON, default=lambda: ['analyst'])  # JSON array of roles
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship('Tenant', back_populates='users')
    deals = relationship('Deal', back_populates='owner', lazy='dynamic')

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return self.active

    def has_role(self, role: str) -> bool:
        return role in (self.roles or [])

    def is_admin(self) -> bool:
        return 'admin' in (self.roles or [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'email': self.email,
            'name': self.name,
            'roles': self.roles,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


# =============================================================================
# DEAL MODEL
# =============================================================================

class Deal(db.Model):
    """A due diligence deal/project."""
    __tablename__ = 'deals'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    owner_id = Column(String(36), ForeignKey('users.id'), nullable=True)

    # Deal information
    target_name = Column(String(255), nullable=False)
    buyer_name = Column(String(255), default='')
    deal_type = Column(String(50), default='acquisition')  # acquisition, carveout, merger
    industry = Column(String(100), default='')
    deal_value = Column(String(50), default='')  # Range like "$50M-100M"

    # Status tracking
    status = Column(String(50), default='active')  # active, completed, archived
    target_locked = Column(Boolean, default=False)  # Entity locking for two-phase analysis
    buyer_locked = Column(Boolean, default=False)

    # Context and settings
    context = Column(JSON, default=dict)  # Deal context (thesis, scope, etc.)
    settings = Column(JSON, default=dict)  # Analysis settings

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship('Tenant', back_populates='deals')
    owner = relationship('User', back_populates='deals')
    documents = relationship('Document', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')
    facts = relationship('Fact', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')
    findings = relationship('Finding', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'target_name': self.target_name,
            'buyer_name': self.buyer_name,
            'deal_type': self.deal_type,
            'industry': self.industry,
            'deal_value': self.deal_value,
            'status': self.status,
            'target_locked': self.target_locked,
            'buyer_locked': self.buyer_locked,
            'context': self.context,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# DOCUMENT MODEL
# =============================================================================

class Document(db.Model):
    """An uploaded document for analysis."""
    __tablename__ = 'documents'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)

    # File information
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256 hash
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), default='')

    # Classification
    entity = Column(String(20), nullable=False, default='target')  # 'target' or 'buyer'
    authority_level = Column(Integer, default=1)  # 1-5, higher = more authoritative
    document_type = Column(String(50), default='')  # contract, presentation, spreadsheet, etc.

    # Storage
    storage_path = Column(Text, nullable=False)  # Path or S3 key
    storage_type = Column(String(20), default='local')  # 'local' or 's3'

    # Processing status
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    extracted_text = Column(Text, default='')
    page_count = Column(Integer, default=0)
    processing_error = Column(Text, default='')

    # Extra metadata
    extra_metadata = Column(JSON, default=dict)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    deal = relationship('Deal', back_populates='documents')

    # Indexes
    __table_args__ = (
        Index('idx_documents_deal_entity', 'deal_id', 'entity'),
        Index('idx_documents_hash', 'file_hash'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'filename': self.filename,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'entity': self.entity,
            'authority_level': self.authority_level,
            'document_type': self.document_type,
            'status': self.status,
            'page_count': self.page_count,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
        }


# =============================================================================
# FACT MODEL
# =============================================================================

class Fact(db.Model):
    """An extracted fact from document analysis."""
    __tablename__ = 'facts'

    id = Column(String(50), primary_key=True)  # F-INFRA-001 format
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)
    document_id = Column(String(36), ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)

    # Classification
    domain = Column(String(50), nullable=False)  # infrastructure, network, cybersecurity, etc.
    category = Column(String(100), default='')
    entity = Column(String(20), nullable=False, default='target')  # 'target' or 'buyer'

    # Content
    item = Column(Text, nullable=False)  # What this fact is about
    status = Column(String(50), default='documented')  # documented, partial, gap
    details = Column(JSON, default=dict)  # Flexible key-value pairs

    # Evidence
    evidence = Column(JSON, default=dict)  # exact_quote, source_section
    source_document = Column(String(255), default='')  # Filename

    # Confidence and verification
    confidence_score = Column(Float, default=0.5)
    verified = Column(Boolean, default=False)
    verified_by = Column(String(255), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_status = Column(String(50), default='pending')
    verification_note = Column(Text, default='')

    # Review flags
    needs_review = Column(Boolean, default=False)
    needs_review_reason = Column(Text, default='')

    # Analysis metadata
    analysis_phase = Column(String(50), default='target_extraction')
    is_integration_insight = Column(Boolean, default=False)
    related_domains = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    deal = relationship('Deal', back_populates='facts')

    # Indexes
    __table_args__ = (
        Index('idx_facts_deal_domain', 'deal_id', 'domain'),
        Index('idx_facts_deal_entity', 'deal_id', 'entity'),
        Index('idx_facts_verification', 'deal_id', 'verification_status'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fact_id': self.id,
            'deal_id': self.deal_id,
            'domain': self.domain,
            'category': self.category,
            'entity': self.entity,
            'item': self.item,
            'status': self.status,
            'details': self.details,
            'evidence': self.evidence,
            'source_document': self.source_document,
            'confidence_score': self.confidence_score,
            'verified': self.verified,
            'verification_status': self.verification_status,
            'needs_review': self.needs_review,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# FINDING MODEL (Risks, Work Items, Recommendations, etc.)
# =============================================================================

class Finding(db.Model):
    """A finding from reasoning analysis (risk, work item, recommendation, etc.)."""
    __tablename__ = 'findings'

    id = Column(String(50), primary_key=True)  # R-xxxx, WI-xxxx, REC-xxxx format
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)

    # Type classification
    finding_type = Column(String(50), nullable=False)  # risk, work_item, recommendation, strategic_consideration

    # Common fields
    domain = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, default='')
    reasoning = Column(Text, default='')
    confidence = Column(String(20), default='medium')

    # M&A framing
    mna_lens = Column(String(50), default='')  # day_1_continuity, tsa_exposure, etc.
    mna_implication = Column(Text, default='')

    # Evidence chain - array of fact IDs
    based_on_facts = Column(JSON, default=list)

    # Risk-specific fields
    severity = Column(String(20), nullable=True)  # critical, high, medium, low
    category = Column(String(100), default='')
    mitigation = Column(Text, default='')
    integration_dependent = Column(Boolean, default=False)
    timeline = Column(String(100), nullable=True)

    # Work item-specific fields
    phase = Column(String(50), nullable=True)  # Day_1, Day_100, Post_100
    priority = Column(String(20), nullable=True)
    owner_type = Column(String(50), nullable=True)  # buyer, target, shared, vendor
    cost_estimate = Column(String(50), nullable=True)  # under_25k, 25k_to_100k, etc.
    triggered_by_risks = Column(JSON, default=list)  # Risk IDs
    dependencies = Column(JSON, default=list)  # Other work item IDs

    # Recommendation-specific fields
    action_type = Column(String(50), nullable=True)  # negotiate, budget, investigate, etc.
    urgency = Column(String(50), nullable=True)  # immediate, pre-close, post-close
    rationale = Column(Text, default='')

    # Strategic consideration-specific fields
    lens = Column(String(50), nullable=True)  # buyer_alignment, tsa, synergy, etc.
    implication = Column(Text, default='')

    # Extra data (for flexibility)
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    deal = relationship('Deal', back_populates='findings')

    # Indexes
    __table_args__ = (
        Index('idx_findings_deal_type', 'deal_id', 'finding_type'),
        Index('idx_findings_deal_domain', 'deal_id', 'domain'),
        Index('idx_findings_severity', 'deal_id', 'finding_type', 'severity'),
    )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'finding_id': self.id,
            'deal_id': self.deal_id,
            'finding_type': self.finding_type,
            'domain': self.domain,
            'title': self.title,
            'description': self.description,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'mna_lens': self.mna_lens,
            'mna_implication': self.mna_implication,
            'based_on_facts': self.based_on_facts,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        # Add type-specific fields
        if self.finding_type == 'risk':
            result.update({
                'severity': self.severity,
                'category': self.category,
                'mitigation': self.mitigation,
                'integration_dependent': self.integration_dependent,
                'timeline': self.timeline,
            })
        elif self.finding_type == 'work_item':
            result.update({
                'phase': self.phase,
                'priority': self.priority,
                'owner_type': self.owner_type,
                'cost_estimate': self.cost_estimate,
                'triggered_by_risks': self.triggered_by_risks,
                'dependencies': self.dependencies,
            })
        elif self.finding_type == 'recommendation':
            result.update({
                'action_type': self.action_type,
                'urgency': self.urgency,
                'rationale': self.rationale,
            })
        elif self.finding_type == 'strategic_consideration':
            result.update({
                'lens': self.lens,
                'implication': self.implication,
            })

        return result


# =============================================================================
# AUDIT LOG MODEL
# =============================================================================

class AuditLog(db.Model):
    """Audit trail for tracking changes."""
    __tablename__ = 'audit_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True, index=True)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='SET NULL'), nullable=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Action details
    action = Column(String(100), nullable=False)  # create, update, delete, login, etc.
    resource_type = Column(String(50), nullable=True)  # fact, finding, document, etc.
    resource_id = Column(String(100), nullable=True)

    # Change details
    details = Column(JSON, default=dict)  # old_value, new_value, etc.

    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_audit_tenant', 'tenant_id'),
        Index('idx_audit_deal', 'deal_id'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_created', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'deal_id': self.deal_id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_all_tables(app):
    """Create all database tables."""
    with app.app_context():
        db.create_all()


def log_audit(action: str, resource_type: str = None, resource_id: str = None,
              tenant_id: str = None, deal_id: str = None, user_id: str = None,
              details: dict = None, ip_address: str = None, user_agent: str = None):
    """Create an audit log entry."""
    log_entry = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_id=tenant_id,
        deal_id=deal_id,
        user_id=user_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(log_entry)
    db.session.commit()
    return log_entry
