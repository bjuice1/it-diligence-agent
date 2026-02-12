"""
Database Configuration and Models for IT Due Diligence Agent

Phase 1: PostgreSQL database with SQLAlchemy ORM.
Supports both PostgreSQL (production) and SQLite (development/testing).

Enhancements (v2):
- Soft delete pattern (deleted_at column)
- Audit columns (created_by, updated_by)
- Full-text search index on facts
- Junction table for fact→finding links
- Analysis runs tracking
- Pending changes for incremental updates
- Deal snapshots for rollback
- Notifications system
- Transaction decorator for atomicity
- Circuit breaker for database failures
"""

import os
import uuid
import time
import threading
import logging
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Callable, TypeVar

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Text, ForeignKey, JSON, Index, event, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TSVECTOR
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from flask_login import UserMixin

logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

# Type variable for generic functions
T = TypeVar('T')


# =============================================================================
# CIRCUIT BREAKER FOR DATABASE FAILURES
# =============================================================================

class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class DatabaseCircuitBreaker:
    """
    Circuit breaker pattern for database operations.

    Prevents cascading failures by failing fast when database is unavailable.
    After threshold failures, circuit opens and returns fallback for timeout period.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = 'closed'  # closed, open, half-open
        self._half_open_calls = 0
        self._lock = threading.RLock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == 'open':
                # Check if we should transition to half-open
                if self._last_failure_time and \
                   time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = 'half-open'
                    self._half_open_calls = 0
            return self._state

    def record_success(self):
        """Record a successful operation."""
        with self._lock:
            if self._state == 'half-open':
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    # Enough successes, close the circuit
                    self._state = 'closed'
                    self._failure_count = 0
                    logger.info("Circuit breaker closed - database recovered")
            elif self._state == 'closed':
                self._failure_count = 0

    def record_failure(self):
        """Record a failed operation."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == 'half-open':
                # Failed during recovery, open again
                self._state = 'open'
                logger.warning("Circuit breaker reopened - database still failing")
            elif self._failure_count >= self.failure_threshold:
                self._state = 'open'
                logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    def can_execute(self) -> bool:
        """Check if an operation can be executed."""
        state = self.state  # This may transition to half-open
        return state in ('closed', 'half-open')

    def __call__(self, fallback: Callable[[], T] = None):
        """
        Decorator to wrap database operations with circuit breaker.

        Args:
            fallback: Optional function to call when circuit is open
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                if not self.can_execute():
                    if fallback:
                        logger.info(f"Circuit open, using fallback for {func.__name__}")
                        return fallback()
                    raise CircuitBreakerOpen(
                        f"Database circuit breaker is open. "
                        f"Will retry after {self.recovery_timeout}s"
                    )

                try:
                    result = func(*args, **kwargs)
                    self.record_success()
                    return result
                except (OperationalError, SQLAlchemyError) as e:
                    self.record_failure()
                    if fallback and not self.can_execute():
                        logger.warning(f"Database error, using fallback: {e}")
                        return fallback()
                    raise

            return wrapper
        return decorator


# Global circuit breaker instance
db_circuit_breaker = DatabaseCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30.0,
    half_open_max_calls=3
)


# =============================================================================
# TRANSACTION DECORATOR
# =============================================================================

def transactional(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for transactional database operations.

    Ensures all operations within the decorated function are atomic.
    Commits on success, rolls back on any exception.

    Usage:
        @transactional
        def create_deal_with_documents(deal_data, documents):
            deal = Deal(**deal_data)
            db.session.add(deal)
            for doc in documents:
                doc.deal_id = deal.id
                db.session.add(doc)
            return deal
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            logger.error(f"Transaction rolled back in {func.__name__}: {e}")
            raise

    return wrapper


@contextmanager
def transaction_scope():
    """
    Context manager for transactional operations.

    Usage:
        with transaction_scope():
            deal = Deal(name='Test')
            db.session.add(deal)
            fact = Fact(deal_id=deal.id, ...)
            db.session.add(fact)
        # Auto-commits on exit, rolls back on exception
    """
    try:
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Transaction rolled back: {e}")
        raise


# =============================================================================
# DATABASE SESSION HELPERS
# =============================================================================

@contextmanager
def get_db_session():
    """
    Context manager for database sessions with auto-commit/rollback.

    Usage:
        with get_db_session() as session:
            user = session.query(User).first()
            user.name = 'Updated'
        # Auto-commits on exit
    """
    try:
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise
    finally:
        db.session.remove()


# =============================================================================
# MIXINS FOR COMMON PATTERNS
# =============================================================================

class SoftDeleteMixin:
    """Mixin for soft delete pattern - records are marked deleted, not removed."""
    deleted_at = Column(DateTime, nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self):
        """Mark record as deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None


class AuditMixin:
    """Mixin for audit columns - who created/updated records."""

    @declared_attr
    def created_by(cls):
        return Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    @declared_attr
    def updated_by(cls):
        return Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)


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

    # Last accessed deal (for session restoration - Spec 01)
    last_deal_id = Column(String(36), ForeignKey('deals.id', ondelete='SET NULL'), nullable=True, index=True)
    last_deal_accessed_at = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship('Tenant', back_populates='users')
    deals = relationship('Deal', back_populates='owner', lazy='dynamic', foreign_keys='Deal.owner_id')
    last_deal = relationship('Deal', foreign_keys=[last_deal_id], lazy='select')
    notifications = relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

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
            'last_deal_id': self.last_deal_id,
            'last_deal_accessed_at': self.last_deal_accessed_at.isoformat() if self.last_deal_accessed_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create a User instance from a dictionary."""
        # Handle datetime fields
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_login' in data and isinstance(data['last_login'], str):
            data['last_login'] = datetime.fromisoformat(data['last_login'])
        return cls(**data)

    def get_unread_notification_count(self) -> int:
        """Get count of unread notifications."""
        return self.notifications.filter_by(read=False).count()

    # Session persistence methods (Spec 01)
    def update_last_deal(self, deal_id: str) -> None:
        """
        Update the user's last accessed deal.

        This is called when a user explicitly selects a deal or navigates to a deal page.
        Used for session restoration when flask_session is lost.

        Args:
            deal_id: The deal ID to set as last accessed

        Note:
            Does NOT commit the transaction. Caller must handle db.session.commit().
        """
        self.last_deal_id = deal_id
        self.last_deal_accessed_at = datetime.utcnow()

    def get_last_deal(self) -> Optional['Deal']:
        """
        Get the user's last accessed deal, if it exists and is not deleted.

        Returns:
            Deal object if found and not soft-deleted, None otherwise

        Usage:
            last_deal = current_user.get_last_deal()
            if last_deal:
                flask_session['current_deal_id'] = last_deal.id
        """
        if not self.last_deal_id:
            return None

        # The relationship loads the deal, but we need to check if it's deleted
        deal = self.last_deal
        if deal and not deal.is_deleted:
            return deal

        return None

    def clear_last_deal(self) -> None:
        """
        Clear the user's last accessed deal.

        Called when:
        - User explicitly logs out
        - User's access to a deal is revoked
        - Deal is deleted

        Note:
            Does NOT commit the transaction. Caller must handle db.session.commit().
        """
        self.last_deal_id = None
        self.last_deal_accessed_at = None


# =============================================================================
# DEAL MODEL
# =============================================================================

class Deal(SoftDeleteMixin, AuditMixin, db.Model):
    """A due diligence deal/project."""
    __tablename__ = 'deals'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    owner_id = Column(String(36), ForeignKey('users.id'), nullable=True)

    # Deal information
    name = Column(String(255), nullable=False, default='')  # User-friendly deal name
    target_name = Column(String(255), nullable=False)
    buyer_name = Column(String(255), default='')
    deal_type = Column(
        String(50),
        nullable=False,  # NOT NULL constraint
        default='acquisition',  # Keep default for backward compatibility
        # NOTE: After migration period, consider removing default to force explicit selection
    )
    industry = Column(String(100), default='')
    sub_industry = Column(String(100), default='')  # More specific industry
    deal_value = Column(String(50), default='')  # Range like "$50M-100M"

    # Status tracking with state machine
    status = Column(String(50), default='draft')  # draft, active, analyzing, complete, archived
    target_locked = Column(Boolean, default=False)  # Entity locking for two-phase analysis
    buyer_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime, nullable=True)
    locked_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Progress tracking
    documents_uploaded = Column(Integer, default=0)
    facts_extracted = Column(Integer, default=0)
    findings_count = Column(Integer, default=0)
    analysis_runs_count = Column(Integer, default=0)
    review_percent = Column(Float, default=0.0)  # 0-100

    # Context and settings
    context = Column(JSON, default=dict)  # Deal context (thesis, scope, etc.)
    settings = Column(JSON, default=dict)  # Analysis settings

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship('Tenant', back_populates='deals')
    owner = relationship('User', back_populates='deals', foreign_keys=[owner_id])
    locker = relationship('User', foreign_keys=[locked_by])
    documents = relationship('Document', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')
    facts = relationship('Fact', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')
    findings = relationship('Finding', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')
    analysis_runs = relationship('AnalysisRun', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')
    snapshots = relationship('DealSnapshot', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')
    pending_changes = relationship('PendingChange', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')
    report_overrides = relationship('ReportOverride', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')
    inventory_items = relationship('InventoryItem', back_populates='deal', lazy='dynamic', cascade='all, delete-orphan')

    # Indexes and constraints
    __table_args__ = (
        Index('idx_deals_tenant_status', 'tenant_id', 'status'),
        Index('idx_deals_owner', 'owner_id'),
        Index('idx_deals_deleted', 'deleted_at'),
        # CHECK constraint for valid deal types
        db.CheckConstraint(
            "deal_type IN ('acquisition', 'carveout', 'divestiture')",
            name='valid_deal_type'
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name or self.target_name,
            'target_name': self.target_name,
            'buyer_name': self.buyer_name,
            'deal_type': self.deal_type,
            'industry': self.industry,
            'sub_industry': self.sub_industry,
            'deal_value': self.deal_value,
            'status': self.status,
            'target_locked': self.target_locked,
            'buyer_locked': self.buyer_locked,
            'documents_uploaded': self.documents_uploaded,
            'facts_extracted': self.facts_extracted,
            'findings_count': self.findings_count,
            'review_percent': self.review_percent,
            'context': self.context,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'is_deleted': self.is_deleted,
        }

    def update_access_time(self):
        """Update last accessed timestamp."""
        self.last_accessed_at = datetime.utcnow()


# =============================================================================
# DOCUMENT MODEL
# =============================================================================

class Document(SoftDeleteMixin, db.Model):
    """An uploaded document for analysis."""
    __tablename__ = 'documents'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)

    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False, default='')  # User's original name
    file_hash = Column(String(64), nullable=False)  # SHA-256 hash
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), default='')

    # Version tracking for incremental updates
    version = Column(Integer, default=1)
    previous_version_id = Column(String(36), ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)
    is_current = Column(Boolean, default=True)  # Latest version

    # Classification
    entity = Column(String(20), nullable=False, default='target')  # 'target' or 'buyer'
    authority_level = Column(Integer, default=1)  # 1-5, higher = more authoritative
    document_type = Column(String(50), default='')  # contract, presentation, spreadsheet, etc.
    document_category = Column(String(100), default='')  # More specific category

    # Storage
    storage_path = Column(Text, nullable=False)  # Path or S3 key
    storage_type = Column(String(20), default='local')  # 'local' or 's3'

    # Processing status
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    extracted_text = Column(Text, default='')
    page_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    processing_error = Column(Text, default='')

    # Content checksum for fast diff detection
    content_checksum = Column(String(64), nullable=True)  # Hash of extracted text

    # Extra metadata
    extra_metadata = Column(JSON, default=dict)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Audit - who uploaded
    uploaded_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    deal = relationship('Deal', back_populates='documents')
    previous_version = relationship('Document', remote_side=[id], foreign_keys=[previous_version_id])
    uploader = relationship('User', foreign_keys=[uploaded_by])

    # Indexes
    __table_args__ = (
        Index('idx_documents_deal_entity', 'deal_id', 'entity'),
        Index('idx_documents_hash', 'file_hash'),
        Index('idx_documents_deleted', 'deleted_at'),
        Index('idx_documents_current', 'deal_id', 'is_current'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'filename': self.filename,
            'original_filename': self.original_filename or self.filename,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'version': self.version,
            'is_current': self.is_current,
            'entity': self.entity,
            'authority_level': self.authority_level,
            'document_type': self.document_type,
            'document_category': self.document_category,
            'status': self.status,
            'page_count': self.page_count,
            'word_count': self.word_count,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'is_deleted': self.is_deleted,
        }


# =============================================================================
# FACT MODEL
# =============================================================================

class Fact(SoftDeleteMixin, db.Model):
    """An extracted fact from document analysis."""
    __tablename__ = 'facts'

    id = Column(String(50), primary_key=True)  # F-INFRA-001 format
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)
    document_id = Column(String(36), ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)
    analysis_run_id = Column(String(36), ForeignKey('analysis_runs.id', ondelete='SET NULL'), nullable=True)

    # Classification
    domain = Column(String(50), nullable=False)  # infrastructure, network, cybersecurity, etc.
    category = Column(String(100), default='')
    entity = Column(String(20), nullable=False, default='target')  # 'target' or 'buyer'

    # Content
    item = Column(Text, nullable=False)  # What this fact is about
    status = Column(String(50), default='documented')  # documented, partial, gap
    details = Column(JSON, default=dict)  # Flexible key-value pairs

    # Cost Quality Tracking (for applications domain)
    cost_status = Column(String(20), nullable=True)  # known, unknown, internal_no_cost, estimated

    # Evidence / Provenance
    evidence = Column(JSON, default=dict)  # exact_quote, source_section
    source_document = Column(Text, default='')  # Filename(s) - can be long for multi-doc facts
    source_page_numbers = Column(JSON, default=list)  # [1, 2, 5] - pages where found
    source_quote = Column(Text, default='')  # Exact quote from document

    # Confidence and verification
    confidence_score = Column(Float, default=0.5)
    verified = Column(Boolean, default=False)
    verified_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
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

    # Change tracking for incremental updates
    change_type = Column(String(20), default='new')  # new, updated, unchanged
    previous_version_id = Column(String(50), nullable=True)  # Previous fact ID if updated
    content_checksum = Column(String(64), nullable=True)  # For fast diff detection

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    deal = relationship('Deal', back_populates='facts')
    document = relationship('Document')
    analysis_run = relationship('AnalysisRun', back_populates='facts')
    verifier = relationship('User', foreign_keys=[verified_by])
    finding_links = relationship('FactFindingLink', back_populates='fact', cascade='all, delete-orphan')

    # Indexes - including full-text search
    __table_args__ = (
        Index('idx_facts_deal_domain', 'deal_id', 'domain'),
        Index('idx_facts_deal_entity', 'deal_id', 'entity'),
        Index('idx_facts_verification', 'deal_id', 'verification_status'),
        Index('idx_facts_deleted', 'deleted_at'),
        Index('idx_facts_change_type', 'deal_id', 'change_type'),
        # Note: Full-text search index created in migration for PostgreSQL
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fact_id': self.id,
            'deal_id': self.deal_id,
            'document_id': self.document_id,
            'domain': self.domain,
            'category': self.category,
            'entity': self.entity,
            'item': self.item,
            'status': self.status,
            'details': self.details,
            'cost_status': self.cost_status,  # Cost quality tracking
            'evidence': self.evidence,
            'source_document': self.source_document,
            'source_page_numbers': self.source_page_numbers,
            'source_quote': self.source_quote,
            'confidence_score': self.confidence_score,
            'verified': self.verified,
            'verification_status': self.verification_status,
            'needs_review': self.needs_review,
            'change_type': self.change_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
        }


# =============================================================================
# GAP MODEL (Information gaps requiring VDR requests)
# =============================================================================

class Gap(SoftDeleteMixin, db.Model):
    """An information gap identified during analysis."""
    __tablename__ = 'gaps'

    id = Column(String(50), primary_key=True)  # GAP-xxxx format
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)
    analysis_run_id = Column(String(36), ForeignKey('analysis_runs.id', ondelete='SET NULL'), nullable=True)

    # Gap identification
    domain = Column(String(50), nullable=False)
    category = Column(String(100), default='')
    entity = Column(String(50), default='target')

    # Content
    description = Column(Text, nullable=False)
    importance = Column(String(20), default='medium')  # critical, high, medium, low
    requested_item = Column(Text, default='')  # What to request from VDR

    # Source tracking
    source_document = Column(String(500), default='')
    related_facts = Column(JSON, default=list)  # Fact IDs that led to this gap

    # Status
    status = Column(String(50), default='open')  # open, resolved, pending_response
    resolution_note = Column(Text, default='')
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), default='')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to deal
    deal = db.relationship('Deal', backref=db.backref('gaps', lazy='dynamic'))

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            'gap_id': self.id,
            'id': self.id,
            'deal_id': self.deal_id,
            'domain': self.domain,
            'category': self.category,
            'entity': self.entity,
            'description': self.description,
            'importance': self.importance,
            'requested_item': self.requested_item,
            'source_document': self.source_document,
            'related_facts': self.related_facts,
            'status': self.status,
            'resolution_note': self.resolution_note,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# FINDING MODEL (Risks, Work Items, Recommendations, etc.)
# =============================================================================

class Finding(SoftDeleteMixin, db.Model):
    """A finding from reasoning analysis (risk, work item, recommendation, etc.)."""
    __tablename__ = 'findings'

    id = Column(String(50), primary_key=True)  # R-xxxx, WI-xxxx, REC-xxxx format
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)
    analysis_run_id = Column(String(36), ForeignKey('analysis_runs.id', ondelete='SET NULL'), nullable=True)

    # Type classification
    finding_type = Column(String(50), nullable=False)  # risk, work_item, recommendation, strategic_consideration
    entity = Column(String(20), default='target')       # "target" or "buyer"
    risk_scope = Column(String(50), default='')          # "target_standalone", "integration_dependent", "buyer_action"

    # Common fields
    domain = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, default='')
    reasoning = Column(Text, default='')
    confidence = Column(String(20), default='medium')

    # M&A framing
    mna_lens = Column(String(50), default='')  # day_1_continuity, tsa_exposure, etc.
    mna_implication = Column(Text, default='')

    # Evidence chain - array of fact IDs (kept for backward compat, use junction table for new code)
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
    cost_buildup_json = Column(JSON, default=None)       # Serialized CostBuildUp dict
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

    # Change tracking
    change_type = Column(String(20), default='new')  # new, updated, unchanged
    previous_version_id = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    deal = relationship('Deal', back_populates='findings')
    analysis_run = relationship('AnalysisRun', back_populates='findings')
    fact_links = relationship('FactFindingLink', back_populates='finding', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        Index('idx_findings_deal_type', 'deal_id', 'finding_type'),
        Index('idx_findings_deal_domain', 'deal_id', 'domain'),
        Index('idx_findings_severity', 'deal_id', 'finding_type', 'severity'),
        Index('idx_findings_deleted', 'deleted_at'),
        Index('idx_findings_change_type', 'deal_id', 'change_type'),
        Index('idx_findings_entity', 'deal_id', 'entity'),
    )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'finding_id': self.id,
            'deal_id': self.deal_id,
            'finding_type': self.finding_type,
            'entity': self.entity or 'target',
            'risk_scope': self.risk_scope or '',
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
                'cost_buildup_json': self.cost_buildup_json,
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
# FACT-FINDING JUNCTION TABLE (Normalized Relationship)
# =============================================================================

class FactFindingLink(db.Model):
    """
    Junction table for many-to-many relationship between facts and findings.
    Replaces the denormalized based_on_facts JSON array.
    """
    __tablename__ = 'fact_finding_links'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fact_id = Column(String(50), ForeignKey('facts.id', ondelete='CASCADE'), nullable=False)
    finding_id = Column(String(50), ForeignKey('findings.id', ondelete='CASCADE'), nullable=False)

    # Context about the relationship
    relationship_type = Column(String(50), default='supports')  # supports, contradicts, context
    relevance_score = Column(Float, default=1.0)  # 0.0-1.0

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    fact = relationship('Fact', back_populates='finding_links')
    finding = relationship('Finding', back_populates='fact_links')

    # Indexes and constraints
    __table_args__ = (
        Index('idx_fact_finding_fact', 'fact_id'),
        Index('idx_fact_finding_finding', 'finding_id'),
        db.UniqueConstraint('fact_id', 'finding_id', name='uq_fact_finding'),
    )


# =============================================================================
# INVENTORY ITEM MODEL (Deduplicated structured inventory)
# =============================================================================

class InventoryItem(SoftDeleteMixin, db.Model):
    """Deduplicated inventory items from discovery analysis.

    Uses content-hashed IDs for stable deduplication across re-imports.
    Replaces JSON file-based InventoryStore with database persistence.
    """
    __tablename__ = 'inventory_items'

    # Primary key - content-hashed ID (e.g., I-APP-a3f291)
    item_id = Column(String(50), primary_key=True)

    # Scoping
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)
    inventory_type = Column(String(50), nullable=False)  # application, infrastructure, organization, vendor
    entity = Column(String(20), nullable=False, default='target')  # target or buyer

    # Core fields
    name = Column(Text, nullable=False)  # Item name (app name, server name, etc.)
    status = Column(String(20), default='active')  # active, removed, merged

    # All other attributes stored as JSONB (vendor, version, category, etc.)
    data = Column(JSON, default=dict, nullable=False)

    # Provenance - links back to Facts that created this inventory item
    source_fact_ids = Column(JSON, default=list)  # Array of fact IDs
    source_files = Column(JSON, default=list)  # Source document filenames
    source_type = Column(String(50), default='discovery')  # discovery, import, manual

    # Enrichment tracking
    is_enriched = Column(Boolean, default=False)
    enrichment_date = Column(DateTime, nullable=True)
    needs_investigation = Column(Boolean, default=False)
    investigation_reason = Column(Text, default='')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deal = relationship('Deal', back_populates='inventory_items')

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_inventory_deal_type', 'deal_id', 'inventory_type'),
        Index('idx_inventory_deal_entity', 'deal_id', 'entity'),
        Index('idx_inventory_deal_status', 'deal_id', 'status'),
        Index('idx_inventory_type_entity', 'inventory_type', 'entity'),
        Index('idx_inventory_deleted', 'deleted_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary matching InventoryItem dataclass format."""
        return {
            'item_id': self.item_id,
            'deal_id': self.deal_id,
            'inventory_type': self.inventory_type,
            'entity': self.entity,
            'name': self.name,
            'status': self.status,
            'data': self.data or {},
            'source_fact_ids': self.source_fact_ids or [],
            'source_files': self.source_files or [],
            'source_type': self.source_type,
            'is_enriched': self.is_enriched,
            'enrichment_date': self.enrichment_date.isoformat() if self.enrichment_date else None,
            'needs_investigation': self.needs_investigation,
            'investigation_reason': self.investigation_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
        }


# =============================================================================
# ANALYSIS RUN MODEL
# =============================================================================

class AnalysisRun(db.Model):
    """
    Tracks each analysis run for a deal.
    Supports incremental updates and rollback.
    Also stores task state for UI resilience (survives server restarts).
    """
    __tablename__ = 'analysis_runs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)

    # Task identification (for UI tracking - survives server restarts)
    task_id = Column(String(50), unique=True, nullable=True, index=True)  # e.g., "analysis_abc123"

    # Run identification
    run_number = Column(Integer, nullable=False)  # Sequential per deal
    run_type = Column(String(50), default='full')  # full, incremental, targeted

    # Configuration
    domains = Column(JSON, default=list)  # Domains analyzed
    entity = Column(String(20), default='target')  # target, buyer, both
    documents_analyzed = Column(JSON, default=list)  # Document IDs included

    # Status
    status = Column(String(50), default='pending')  # pending, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)  # 0-100
    current_step = Column(String(100), default='')

    # Results summary
    facts_created = Column(Integer, default=0)
    facts_updated = Column(Integer, default=0)
    facts_unchanged = Column(Integer, default=0)
    findings_created = Column(Integer, default=0)
    findings_updated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, default='')
    error_details = Column(JSON, default=dict)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Who initiated
    initiated_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Snapshot reference (for rollback)
    pre_run_snapshot_id = Column(String(36), ForeignKey('deal_snapshots.id', ondelete='SET NULL'), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    deal = relationship('Deal', back_populates='analysis_runs')
    initiator = relationship('User', foreign_keys=[initiated_by])
    facts = relationship('Fact', back_populates='analysis_run', lazy='dynamic')
    findings = relationship('Finding', back_populates='analysis_run', lazy='dynamic')
    pre_run_snapshot = relationship('DealSnapshot', foreign_keys=[pre_run_snapshot_id])

    # Indexes
    __table_args__ = (
        Index('idx_analysis_runs_deal', 'deal_id'),
        Index('idx_analysis_runs_status', 'status'),
        db.UniqueConstraint('deal_id', 'run_number', name='uq_deal_run_number'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'run_number': self.run_number,
            'run_type': self.run_type,
            'domains': self.domains,
            'entity': self.entity,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'facts_created': self.facts_created,
            'facts_updated': self.facts_updated,
            'findings_created': self.findings_created,
            'errors_count': self.errors_count,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# PENDING CHANGE MODEL (For Review Before Apply)
# =============================================================================

class PendingChange(db.Model):
    """
    Tracks pending changes from incremental analysis.
    Allows review before applying to main data.
    """
    __tablename__ = 'pending_changes'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)
    analysis_run_id = Column(String(36), ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=True)

    # What changed
    change_type = Column(String(20), nullable=False)  # create, update, delete
    resource_type = Column(String(50), nullable=False)  # fact, finding, document
    resource_id = Column(String(100), nullable=True)  # ID of existing resource (for update/delete)

    # Change tier (from plan)
    tier = Column(Integer, default=1)  # 1=auto-apply, 2=quick-review, 3=full-review

    # The new/updated data
    new_data = Column(JSON, nullable=True)
    old_data = Column(JSON, nullable=True)  # For updates/deletes

    # Diff summary
    diff_summary = Column(Text, default='')
    fields_changed = Column(JSON, default=list)

    # Status
    status = Column(String(50), default='pending')  # pending, approved, rejected, applied, skipped

    # Review
    reviewed_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(Text, default='')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)

    # Relationships
    deal = relationship('Deal', back_populates='pending_changes')
    reviewer = relationship('User', foreign_keys=[reviewed_by])

    # Indexes
    __table_args__ = (
        Index('idx_pending_changes_deal', 'deal_id'),
        Index('idx_pending_changes_status', 'status'),
        Index('idx_pending_changes_tier', 'deal_id', 'tier'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'change_type': self.change_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'tier': self.tier,
            'new_data': self.new_data,
            'old_data': self.old_data,
            'diff_summary': self.diff_summary,
            'fields_changed': self.fields_changed,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# REPORT OVERRIDE MODEL (Human Edits to AI Reports)
# =============================================================================

class ReportOverride(db.Model):
    """
    Stores human edits to AI-generated report text.
    When a user edits a section in the web UI, the override is saved here
    and applied when rendering or exporting reports.
    """
    __tablename__ = 'report_overrides'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)

    # Which report section
    domain = Column(String(100), nullable=False)       # e.g. 'applications', 'infrastructure'
    section = Column(String(100), nullable=False)       # 'assessment', 'implications', 'actions'
    field_name = Column(String(200), nullable=False)    # specific field within section

    # Values
    original_value = Column(Text, default='')
    override_value = Column(Text, nullable=False)

    # Audit
    created_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)

    # Relationships
    deal = relationship('Deal', back_populates='report_overrides')
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_report_overrides_deal_domain', 'deal_id', 'domain', 'section', 'field_name'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'domain': self.domain,
            'section': self.section,
            'field_name': self.field_name,
            'original_value': self.original_value,
            'override_value': self.override_value,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active,
        }


# =============================================================================
# DRIVER OVERRIDE MODEL (User Corrections to Extracted Drivers)
# =============================================================================

class DriverOverride(db.Model):
    """
    Stores user corrections to extracted driver values.
    When a user overrides an extracted driver (e.g., user_count was 850 but should be 1200),
    the override is saved here and applied when calculating costs.
    """
    __tablename__ = 'driver_overrides'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)

    # Which driver
    driver_name = Column(String(100), nullable=False)  # e.g., 'total_users', 'sites', 'erp_system'

    # Values - stored as JSON to handle different types (int, str, bool, list)
    extracted_value = Column(JSON, nullable=True)      # What extraction found
    override_value = Column(JSON, nullable=False)      # User's correction

    # Source tracking
    source_fact_id = Column(String(50), ForeignKey('facts.id', ondelete='SET NULL'), nullable=True)
    extraction_confidence = Column(String(20), default='')  # high, medium, low

    # Reason for override
    reason = Column(Text, default='')

    # Audit
    created_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)

    # Relationships
    deal = relationship('Deal', backref=db.backref('driver_overrides', lazy='dynamic', cascade='all, delete-orphan'))
    source_fact = relationship('Fact', foreign_keys=[source_fact_id])
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_driver_overrides_deal', 'deal_id'),
        Index('idx_driver_overrides_deal_driver', 'deal_id', 'driver_name'),
        db.UniqueConstraint('deal_id', 'driver_name', name='uq_deal_driver_override'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'driver_name': self.driver_name,
            'extracted_value': self.extracted_value,
            'override_value': self.override_value,
            'source_fact_id': self.source_fact_id,
            'extraction_confidence': self.extraction_confidence,
            'reason': self.reason,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active,
        }


# =============================================================================
# DEAL SNAPSHOT MODEL (For Rollback)
# =============================================================================

class DealSnapshot(db.Model):
    """
    Point-in-time snapshot of deal data for rollback capability.
    Created before each analysis run.
    """
    __tablename__ = 'deal_snapshots'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)

    # Snapshot metadata
    snapshot_number = Column(Integer, nullable=False)  # Sequential per deal
    snapshot_type = Column(String(50), default='pre_analysis')  # pre_analysis, manual, scheduled
    description = Column(String(255), default='')

    # Snapshot data (stored as compressed JSON)
    facts_data = Column(JSON, default=list)  # All facts at snapshot time
    findings_data = Column(JSON, default=list)  # All findings at snapshot time
    documents_data = Column(JSON, default=list)  # Document metadata (not content)
    deal_context = Column(JSON, default=dict)  # Deal settings and context

    # Counts at snapshot time
    facts_count = Column(Integer, default=0)
    findings_count = Column(Integer, default=0)
    documents_count = Column(Integer, default=0)

    # Size tracking
    data_size_bytes = Column(Integer, default=0)

    # Who created
    created_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For cleanup

    # Relationships
    deal = relationship('Deal', back_populates='snapshots')
    creator = relationship('User', foreign_keys=[created_by])

    # Indexes
    __table_args__ = (
        Index('idx_snapshots_deal', 'deal_id'),
        Index('idx_snapshots_created', 'created_at'),
        db.UniqueConstraint('deal_id', 'snapshot_number', name='uq_deal_snapshot_number'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'snapshot_number': self.snapshot_number,
            'snapshot_type': self.snapshot_type,
            'description': self.description,
            'facts_count': self.facts_count,
            'findings_count': self.findings_count,
            'documents_count': self.documents_count,
            'data_size_bytes': self.data_size_bytes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }


# =============================================================================
# NOTIFICATION MODEL
# =============================================================================

class Notification(db.Model):
    """User notifications for deal events."""
    __tablename__ = 'notifications'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=True)

    # Notification content
    notification_type = Column(String(50), nullable=False)  # analysis_complete, review_needed, error, etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, default='')
    action_url = Column(String(500), nullable=True)  # Link to relevant page

    # Priority
    priority = Column(String(20), default='normal')  # low, normal, high, urgent

    # Status
    read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    dismissed = Column(Boolean, default=False)

    # Extra data
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship('User', back_populates='notifications')
    deal = relationship('Deal')

    # Indexes
    __table_args__ = (
        Index('idx_notifications_user', 'user_id'),
        Index('idx_notifications_unread', 'user_id', 'read'),
        Index('idx_notifications_created', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'deal_id': self.deal_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'action_url': self.action_url,
            'priority': self.priority,
            'read': self.read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def mark_read(self):
        """Mark notification as read."""
        self.read = True
        self.read_at = datetime.utcnow()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _run_migrations():
    """Run lightweight schema migrations.

    These are idempotent migrations that can safely run multiple times.
    For more complex migrations, use Alembic.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Migration 1: Change facts.source_document from VARCHAR(255) to TEXT
        # This allows storing multiple document names without truncation
        result = db.session.execute(db.text("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'facts' AND column_name = 'source_document'
        """))
        row = result.fetchone()
        if row and row[0] == 'character varying':
            logger.info("Migrating facts.source_document to TEXT...")
            db.session.execute(db.text("""
                ALTER TABLE facts ALTER COLUMN source_document TYPE TEXT
            """))
            db.session.commit()
            logger.info("Migration complete: facts.source_document is now TEXT")
        else:
            logger.debug("facts.source_document already TEXT or table doesn't exist")
    except Exception as e:
        logger.warning(f"Migration check failed (non-fatal): {e}")
        db.session.rollback()

    # Migration 2: Add task_id column to analysis_runs for UI resilience
    try:
        result = db.session.execute(db.text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'analysis_runs' AND column_name = 'task_id'
        """))
        row = result.fetchone()
        if not row:
            logger.info("Adding task_id column to analysis_runs...")
            db.session.execute(db.text("""
                ALTER TABLE analysis_runs ADD COLUMN task_id VARCHAR(50) UNIQUE
            """))
            db.session.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_analysis_runs_task_id ON analysis_runs(task_id)
            """))
            db.session.commit()
            logger.info("Migration complete: analysis_runs.task_id added")
        else:
            logger.debug("analysis_runs.task_id already exists")
    except Exception as e:
        logger.warning(f"task_id migration failed (non-fatal): {e}")
        db.session.rollback()

    # Migration 3: Add entity, risk_scope, cost_buildup_json to findings (Spec 04/05)
    _add_column_if_missing('findings', 'entity', "VARCHAR(20) DEFAULT 'target'", logger)
    _add_column_if_missing('findings', 'risk_scope', "VARCHAR(50) DEFAULT ''", logger)
    _add_column_if_missing('findings', 'cost_buildup_json', "JSON DEFAULT NULL", logger)

    # Migration 4: Add last_deal_id and last_deal_accessed_at to users (Session Persistence Fix - Spec 01)
    _add_column_if_missing('users', 'last_deal_id', "VARCHAR(36)", logger)
    _add_column_if_missing('users', 'last_deal_accessed_at', "TIMESTAMP", logger)

    # Add index for last_deal_id lookups
    try:
        dialect = db.engine.dialect.name
        if dialect == 'postgresql':
            db.session.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_users_last_deal ON users(last_deal_id)"
            ))
            db.session.commit()
            logger.info("Index idx_users_last_deal ensured")
        elif dialect == 'sqlite':
            # SQLite CREATE INDEX IF NOT EXISTS is already supported
            db.session.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_users_last_deal ON users(last_deal_id)"
            ))
            db.session.commit()
            logger.info("Index idx_users_last_deal ensured (SQLite)")
    except Exception as e:
        logger.warning(f"idx_users_last_deal index creation failed (non-fatal): {e}")
        db.session.rollback()

    # Migration 5: Create flask_sessions table for SQLAlchemy session backend (Spec 04)
    _create_session_table(logger)


def _create_session_table(logger):
    """Create flask_sessions table if it doesn't exist (Spec 04 - Session Architecture Hardening)."""
    try:
        # Check if table exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'flask_sessions' in inspector.get_table_names():
            logger.debug("flask_sessions table already exists")
            return

        dialect = db.engine.dialect.name
        logger.info("Creating flask_sessions table for SQLAlchemy session backend...")

        # Create table based on Flask-Session schema
        if dialect == 'postgresql':
            db.session.execute(db.text("""
                CREATE TABLE flask_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    data BYTEA,
                    expiry TIMESTAMP
                )
            """))
            db.session.execute(db.text(
                "CREATE INDEX idx_flask_sessions_expiry ON flask_sessions(expiry)"
            ))
            db.session.commit()
            logger.info("✅ Created flask_sessions table (PostgreSQL)")
        elif dialect == 'sqlite':
            db.session.execute(db.text("""
                CREATE TABLE flask_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    data BLOB,
                    expiry TIMESTAMP
                )
            """))
            db.session.execute(db.text(
                "CREATE INDEX idx_flask_sessions_expiry ON flask_sessions(expiry)"
            ))
            db.session.commit()
            logger.info("✅ Created flask_sessions table (SQLite)")

    except Exception as e:
        logger.warning(f"flask_sessions table creation failed (non-fatal): {e}")
        db.session.rollback()


def _add_column_if_missing(table: str, column: str, col_def: str, logger):
    """Add a column to a table if it doesn't already exist (SQLite + PostgreSQL safe)."""
    try:
        # Use PRAGMA for SQLite, information_schema for PostgreSQL
        dialect = db.engine.dialect.name
        if dialect == 'sqlite':
            result = db.session.execute(db.text(f"PRAGMA table_info({table})"))
            cols = [row[1] for row in result.fetchall()]
            exists = column in cols
        else:
            result = db.session.execute(db.text(
                f"SELECT column_name FROM information_schema.columns "
                f"WHERE table_name = '{table}' AND column_name = '{column}'"
            ))
            exists = result.fetchone() is not None

        if not exists:
            logger.info(f"Adding {table}.{column}...")
            db.session.execute(db.text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
            db.session.commit()
            logger.info(f"Migration complete: {table}.{column} added")
        else:
            logger.debug(f"{table}.{column} already exists")
    except Exception as e:
        logger.warning(f"{table}.{column} migration failed (non-fatal): {e}")
        db.session.rollback()


def create_all_tables(app):
    """Create all database tables and run migrations."""
    with app.app_context():
        db.create_all()
        # Run lightweight migrations for schema changes
        _run_migrations()


# =============================================================================
# CONSOLIDATED RISK MODEL (C1: Risk Consolidation)
# =============================================================================

class ConsolidatedRisk(SoftDeleteMixin, db.Model):
    """
    Consolidated risk grouping related findings.

    Related risks are grouped using graph-based clustering and summarized
    into a single consolidated finding. This reduces duplication and
    makes risk prioritization clearer.

    C1 FIX: Implements graph clustering, evidence provenance, domain-first consolidation.
    """
    __tablename__ = 'consolidated_risks'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)

    # Classification
    domain = Column(String(50), nullable=False)  # applications, infrastructure, security, etc.
    entity = Column(String(20), default='target')

    # Content
    title = Column(String(200), nullable=False)  # Short title (under 50 chars ideal)
    description = Column(Text, nullable=False)  # Consolidated summary

    # Severity = max of all children
    severity = Column(String(20), nullable=False)  # critical, high, medium, low

    # Evidence & provenance (GPT FEEDBACK - critical for trust)
    child_risk_ids = Column(JSON, nullable=False)  # [finding_id, ...] original risk IDs
    supporting_facts = Column(JSON, default=list)  # Union of all child facts
    key_systems = Column(JSON, default=list)  # Systems mentioned across children
    field_provenance = Column(JSON, default=dict)  # Which child contributed what claims

    # Consolidation metadata
    consolidation_method = Column(String(50), default='rule_based')  # rule_based, llm, manual
    grouping_confidence = Column(Float, default=1.0)  # 0.0 - 1.0
    grouping_reason = Column(Text, default='')  # Why these were grouped

    # Version tracking - increment when children change
    version = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deal = relationship('Deal', backref=db.backref('consolidated_risks', lazy='dynamic', cascade='all, delete-orphan'))

    # Indexes
    __table_args__ = (
        Index('idx_consolidated_risks_deal', 'deal_id'),
        Index('idx_consolidated_risks_deal_domain', 'deal_id', 'domain'),
        Index('idx_consolidated_risks_severity', 'deal_id', 'severity'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'domain': self.domain,
            'entity': self.entity,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'child_risk_ids': self.child_risk_ids or [],
            'child_count': len(self.child_risk_ids or []),
            'supporting_facts': self.supporting_facts or [],
            'key_systems': self.key_systems or [],
            'field_provenance': self.field_provenance or {},
            'consolidation_method': self.consolidation_method,
            'grouping_confidence': self.grouping_confidence,
            'grouping_reason': self.grouping_reason,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_child_risks(self) -> List['Finding']:
        """Load the child Finding objects for this consolidated risk."""
        if not self.child_risk_ids:
            return []
        return Finding.query.filter(Finding.id.in_(self.child_risk_ids)).all()


# =============================================================================
# RUN DIFF MODEL (Phase 1a: What Changed Between Runs)
# =============================================================================

class RunDiff(db.Model):
    """
    Metric-driven diff between analysis runs.

    Tracks what changed between runs: documents, facts, risks.
    This is debugging/audit data, not narrative - just metrics.

    Phase 1a: Analysis Reasoning Layer
    """
    __tablename__ = 'run_diffs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deal_id = Column(String(36), ForeignKey('deals.id', ondelete='CASCADE'), nullable=False)

    # Run references
    previous_run_id = Column(String(36), ForeignKey('analysis_runs.id', ondelete='SET NULL'), nullable=True)
    current_run_id = Column(String(36), ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False)
    previous_run_number = Column(Integer, nullable=True)
    current_run_number = Column(Integer, nullable=False)

    # Document changes
    docs_added = Column(JSON, default=list)       # [{id, filename}]
    docs_removed = Column(JSON, default=list)     # [{id, filename}]
    docs_updated = Column(JSON, default=list)     # [{id, filename, reason}] (re-processed, new version)
    docs_total_before = Column(Integer, default=0)
    docs_total_after = Column(Integer, default=0)

    # Chunk/processing metrics
    chunks_before = Column(Integer, default=0)
    chunks_after = Column(Integer, default=0)

    # Fact changes
    facts_created = Column(Integer, default=0)
    facts_updated = Column(Integer, default=0)    # Same stable_id, different content
    facts_deleted = Column(Integer, default=0)    # Soft-deleted or removed
    facts_unchanged = Column(Integer, default=0)
    facts_total_before = Column(Integer, default=0)
    facts_total_after = Column(Integer, default=0)

    # Detailed fact changes (IDs for drill-down)
    facts_created_ids = Column(JSON, default=list)   # [fact_id, ...]
    facts_updated_ids = Column(JSON, default=list)
    facts_deleted_ids = Column(JSON, default=list)

    # Risk/finding changes
    risks_created = Column(Integer, default=0)
    risks_updated = Column(Integer, default=0)
    risks_deleted = Column(Integer, default=0)
    risks_total_before = Column(Integer, default=0)
    risks_total_after = Column(Integer, default=0)

    # Severity changes (important for risk management)
    severity_changes = Column(JSON, default=list)  # [{risk_id, old_severity, new_severity}]

    # Scope changes
    entity_scope_before = Column(String(50), default='')   # 'target', 'buyer', 'both'
    entity_scope_after = Column(String(50), default='')
    domains_before = Column(JSON, default=list)
    domains_after = Column(JSON, default=list)

    # Summary metrics
    net_facts_change = Column(Integer, default=0)    # facts_after - facts_before
    net_risks_change = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    deal = relationship('Deal', backref=db.backref('run_diffs', lazy='dynamic', cascade='all, delete-orphan'))
    previous_run = relationship('AnalysisRun', foreign_keys=[previous_run_id])
    current_run = relationship('AnalysisRun', foreign_keys=[current_run_id])

    # Indexes
    __table_args__ = (
        Index('idx_run_diffs_deal', 'deal_id'),
        Index('idx_run_diffs_current_run', 'current_run_id'),
        Index('idx_run_diffs_created', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'previous_run_id': self.previous_run_id,
            'current_run_id': self.current_run_id,
            'previous_run_number': self.previous_run_number,
            'current_run_number': self.current_run_number,
            # Documents
            'docs_added': self.docs_added or [],
            'docs_removed': self.docs_removed or [],
            'docs_updated': self.docs_updated or [],
            'docs_total_before': self.docs_total_before,
            'docs_total_after': self.docs_total_after,
            # Chunks
            'chunks_before': self.chunks_before,
            'chunks_after': self.chunks_after,
            # Facts
            'facts_created': self.facts_created,
            'facts_updated': self.facts_updated,
            'facts_deleted': self.facts_deleted,
            'facts_unchanged': self.facts_unchanged,
            'facts_total_before': self.facts_total_before,
            'facts_total_after': self.facts_total_after,
            'net_facts_change': self.net_facts_change,
            # Risks
            'risks_created': self.risks_created,
            'risks_updated': self.risks_updated,
            'risks_deleted': self.risks_deleted,
            'risks_total_before': self.risks_total_before,
            'risks_total_after': self.risks_total_after,
            'net_risks_change': self.net_risks_change,
            'severity_changes': self.severity_changes or [],
            # Scope
            'entity_scope_before': self.entity_scope_before,
            'entity_scope_after': self.entity_scope_after,
            'domains_before': self.domains_before or [],
            'domains_after': self.domains_after or [],
            # Meta
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def summary_text(self) -> str:
        """Generate a human-readable summary of changes."""
        lines = []

        # Documents
        if self.docs_added:
            lines.append(f"Documents added: {len(self.docs_added)}")
        if self.docs_removed:
            lines.append(f"Documents removed: {len(self.docs_removed)}")

        # Facts
        if self.facts_created:
            lines.append(f"Facts created: +{self.facts_created}")
        if self.facts_updated:
            lines.append(f"Facts updated: {self.facts_updated}")
        if self.facts_deleted:
            lines.append(f"Facts removed: -{self.facts_deleted}")
        lines.append(f"Facts total: {self.facts_total_before} → {self.facts_total_after}")

        # Risks
        if self.risks_created:
            lines.append(f"Risks created: +{self.risks_created}")
        if self.severity_changes:
            lines.append(f"Severity changes: {len(self.severity_changes)}")
        lines.append(f"Risks total: {self.risks_total_before} → {self.risks_total_after}")

        # Scope
        if self.entity_scope_before != self.entity_scope_after:
            lines.append(f"Scope: {self.entity_scope_before or 'none'} → {self.entity_scope_after}")

        return "\n".join(lines)


# =============================================================================
# FACT REASONING MODEL (Phase 1b: Why This Matters)
# =============================================================================

class FactReasoning(db.Model):
    """
    Why this fact matters - attached to high-signal facts only.

    Phase 1b: Analysis Reasoning Layer

    Stores brief reasoning (1-2 sentences) explaining the significance
    of a fact for IT due diligence. Only generated for high-signal facts
    (core apps, security controls, financial metrics, etc.) to control costs.

    GUARDRAILS:
    - Must cite evidence (source_refs required)
    - 40-60 tokens max
    - No claims beyond source document
    """
    __tablename__ = 'fact_reasoning'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fact_id = Column(String(50), ForeignKey('facts.id', ondelete='CASCADE'), nullable=False)
    run_id = Column(String(36), ForeignKey('analysis_runs.id', ondelete='SET NULL'), nullable=True)

    # The reasoning itself (40-60 tokens max, ~200-300 chars)
    reasoning_text = Column(String(500), nullable=False)

    # Evidence citations (REQUIRED - no orphan claims)
    source_refs = Column(JSON, nullable=False)  # [{doc_id, doc_name, page, chunk_id}]
    related_fact_ids = Column(JSON, default=list)  # Cross-references to other facts

    # Why this fact qualified for reasoning
    signal_type = Column(String(50), nullable=False)  # core_application, security_control, etc.
    signal_score = Column(Float, default=1.0)  # 0.0-1.0, higher = more significant

    # Visibility control
    visibility = Column(String(20), default='client_safe')  # client_safe, internal_only

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    fact = relationship('Fact', backref=db.backref('reasoning', uselist=False, cascade='all, delete-orphan'))
    analysis_run = relationship('AnalysisRun')

    # Indexes
    __table_args__ = (
        Index('idx_fact_reasoning_fact', 'fact_id'),
        Index('idx_fact_reasoning_run', 'run_id'),
        Index('idx_fact_reasoning_signal', 'signal_type'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'fact_id': self.fact_id,
            'run_id': self.run_id,
            'reasoning_text': self.reasoning_text,
            'source_refs': self.source_refs or [],
            'related_fact_ids': self.related_fact_ids or [],
            'signal_type': self.signal_type,
            'signal_score': self.signal_score,
            'visibility': self.visibility,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

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
