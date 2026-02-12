# Domain-First Architecture Redesign Plan
## Strategic Refactor - Option C (4-6 Weeks)

**Status:** PROPOSED
**Priority:** P0 - CRITICAL (Architecture bankruptcy)
**Estimated Duration:** 4-6 weeks
**Author:** Claude Sonnet 4.5 (Architectural Analysis)
**Date:** 2026-02-12

---

## Executive Summary

The current system has **4 parallel truth systems** fighting for authority (FactStore, InventoryStore, Database, JSON files), causing cascading failures where each fix creates new issues. This plan redesigns the architecture using **Domain-Driven Design** principles to establish a **single source of truth**.

**Current State:** Storage-first design (code organized around FactStore/InventoryStore)
**Target State:** Domain-first design (code organized around Application/Infrastructure entities)
**Benefits:** Single source of truth, reliable deduplication, testable, maintainable

---

## Problem Statement

### Current Architecture Issues

1. **Identity Without Authority**
   - 3 ID systems: `F-APP-001` (FactStore), `I-APP-a3f291` (InventoryStore), UUIDs (Database)
   - No canonical ID for cross-run deduplication
   - Re-importing same document creates duplicates

2. **Deduplication Without Reconciliation**
   - Deterministic parser → InventoryStore (exact content hashing)
   - LLM discovery → FactStore (no deduplication)
   - Promotion → InventoryStore (fuzzy matching 0.8 threshold)
   - **Result:** Same app counted 2-3 times with different IDs

3. **Entity Scoping Without Enforcement**
   - Entity validation at 5 different layers (parsing, FactStore, InventoryStore, Database, UI)
   - Silent failures when entity is None or wrong
   - Same app appears in both Target and Buyer (documented in audit B1)

4. **Storage Without Persistence Strategy**
   - FactStore → Database (incremental, durable) ✅
   - InventoryStore → JSON file (at end, volatile) ❌
   - If `inventory_store.save()` fails, all inventory lost
   - UI fallback: "Legacy Facts" banner

### Symptom Timeline (Last 8 Hours)

| Fix Attempted | Outcome | Why It Failed |
|---------------|---------|---------------|
| Disable org assumptions | 791→61 facts | Treated symptom, not disease |
| Lower max iterations | Stopped infinite loop | Correct, but revealed deeper issue |
| Add promotion step | **143 apps (double count!)** | Added 2nd pipeline without removing 1st |
| Rollback promotion | Back to ~60 apps | Bandaid - root cause still exists |

**Pattern:** Additive fixes to broken foundation. Need redesign, not more patches.

---

## Target Architecture: Domain-First Design

### Conceptual Model

```
┌─────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                         │
│  (Business Logic - Single Source of Truth)              │
│                                                          │
│  Application (Aggregate Root)                           │
│    ├── id: ApplicationId (stable, deterministic)        │
│    ├── name: str (canonical, normalized)                │
│    ├── vendor: str                                      │
│    ├── entity: Entity (value object, validated)         │
│    ├── observations: List[Observation] (from facts)     │
│    ├── cost: Money (value object)                       │
│    └── merge(other) / is_duplicate_of(other)            │
│                                                          │
│  ApplicationRepository (Interface)                      │
│    ├── save(app)                                        │
│    ├── find_or_create(name, entity) → Application       │
│    ├── find_by_entity(entity) → List[Application]       │
│    └── find_similar(name, threshold) → List[App]        │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────┴───────────────────────────────┐
│              INFRASTRUCTURE LAYER                        │
│  (Implementation Details - Hidden from Domain)           │
│                                                          │
│  PostgreSQLApplicationRepository                         │
│    ├── Uses SQLAlchemy ORM                              │
│    ├── UNIQUE constraint on (name_normalized, entity)   │
│    ├── Automatic deduplication via database             │
│    └── Transactional save (ACID guarantees)             │
│                                                          │
│  InventoryFileStore (Optional - Export Only)            │
│    └── Materialized view for JSON export                │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────┴───────────────────────────────┐
│               APPLICATION LAYER                          │
│  (Use Cases - Orchestrates Domain Logic)                │
│                                                          │
│  AnalysisPipeline                                       │
│    1. Extract observations (deterministic + LLM)        │
│    2. Convert to Application domain objects             │
│    3. Deduplicate via ApplicationRepository             │
│    4. Save (single atomic transaction)                  │
│                                                          │
│  InventoryQueryService                                  │
│    └── Read-only queries for UI                         │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────┴───────────────────────────────┐
│                  UI LAYER                                │
│  (Presentation - Thin, Stateless)                        │
│                                                          │
│  /applications route                                    │
│    └── calls InventoryQueryService.get_applications()   │
│    └── Renders template (no business logic)             │
└─────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Single Source of Truth:** ApplicationRepository is the ONLY authority for application data
2. **Domain-First:** Business logic in domain layer, storage is implementation detail
3. **Stable Identity:** ApplicationId generated deterministically from (name_normalized, entity)
4. **Deduplication Once:** In repository layer, enforced by database UNIQUE constraint
5. **No Fallback Logic:** UI always reads from repository, never multiple sources

---

## Implementation Phases (6 Weeks)

### Week 1: Domain Model & Value Objects

**Goal:** Define domain entities and value objects

#### Deliverables

**1. Core Domain Entities** (`domain/entities/application.py`)

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import hashlib

class Entity(Enum):
    """Value object for entity (target vs buyer)."""
    TARGET = "target"
    BUYER = "buyer"

    @classmethod
    def from_string(cls, value: str) -> "Entity":
        """Parse from string with validation."""
        normalized = value.lower().strip()
        if normalized in ["target", "seller", "divestiture"]:
            return cls.TARGET
        elif normalized in ["buyer", "acquirer", "parent"]:
            return cls.BUYER
        else:
            raise ValueError(f"Invalid entity: {value}")

@dataclass(frozen=True)
class ApplicationId:
    """Stable, deterministic ID for applications."""
    value: str

    @staticmethod
    def generate(name: str, entity: Entity) -> "ApplicationId":
        """Generate stable ID from normalized name + entity.

        Examples:
            "Salesforce" + TARGET → app_a3f291cd_target
            "salesforce crm" + TARGET → app_a3f291cd_target (same!)
            "Salesforce" + BUYER → app_a3f291cd_buyer (different entity)
        """
        normalized = normalize_application_name(name)
        fingerprint = hashlib.md5(normalized.encode()).hexdigest()[:8]
        return ApplicationId(f"app_{fingerprint}_{entity.value}")

@dataclass
class Observation:
    """Single observation about an application from a document.

    Replaces the current Fact concept - but stored as part of Application,
    not as a separate store.
    """
    source_document: str
    source_type: str  # "table", "prose", "manual"
    extracted_data: dict
    confidence: float
    timestamp: str

@dataclass
class Money:
    """Value object for monetary amounts."""
    amount: float
    currency: str = "USD"
    status: str = "unknown"  # "known", "estimated", "internal_no_cost", "unknown"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

@dataclass
class Application:
    """Aggregate root for application inventory.

    This is the SINGLE SOURCE OF TRUTH for application data.
    All other representations (FactStore, InventoryStore, JSON files)
    are derived from this.
    """
    # Identity (immutable)
    id: ApplicationId
    entity: Entity

    # Core data (mutable)
    name: str  # Canonical name (may differ from observations)
    vendor: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None

    # Observations (evidence)
    observations: List[Observation] = field(default_factory=list)

    # Derived/computed fields
    cost: Optional[Money] = None
    criticality: Optional[str] = None

    # Metadata
    created_at: str = ""
    updated_at: str = ""

    def add_observation(self, obs: Observation) -> None:
        """Add new observation and update derived fields."""
        self.observations.append(obs)
        self._update_derived_fields()

    def merge(self, other: "Application") -> None:
        """Merge another application into this one (deduplication)."""
        if self.id != other.id:
            raise ValueError("Cannot merge apps with different IDs")

        # Merge observations
        self.observations.extend(other.observations)

        # Update derived fields (choose best quality data)
        self._update_derived_fields()

    def is_duplicate_of(self, other: "Application", threshold: float = 0.65) -> bool:
        """Check if this app is a duplicate of another using fuzzy matching."""
        from difflib import SequenceMatcher

        # Same ID = definitely duplicate
        if self.id == other.id:
            return True

        # Different entity = definitely NOT duplicate
        if self.entity != other.entity:
            return False

        # Fuzzy name match
        name_similarity = SequenceMatcher(
            None,
            normalize_application_name(self.name),
            normalize_application_name(other.name)
        ).ratio()

        if name_similarity >= threshold:
            # Boost confidence if vendor also matches
            if self.vendor and other.vendor:
                vendor_similarity = SequenceMatcher(
                    None,
                    self.vendor.lower(),
                    other.vendor.lower()
                ).ratio()

                # Weighted average
                similarity = (name_similarity * 0.7) + (vendor_similarity * 0.3)
                return similarity >= threshold

            return True

        return False

    def _update_derived_fields(self) -> None:
        """Update cost, category, etc. from observations."""
        # Choose best quality observation for each field
        for obs in sorted(self.observations, key=lambda o: o.confidence, reverse=True):
            if not self.vendor and obs.extracted_data.get("vendor"):
                self.vendor = obs.extracted_data["vendor"]

            if not self.cost and obs.extracted_data.get("cost"):
                self.cost = Money(
                    amount=float(obs.extracted_data["cost"]),
                    status=obs.extracted_data.get("cost_status", "unknown")
                )

            # ... other fields


def normalize_application_name(name: str) -> str:
    """Normalize application name for stable ID generation.

    Examples:
        "Salesforce CRM" → "salesforce"
        "Microsoft Office 365" → "microsoft office"
        "SAP ERP (R/3)" → "sap erp"
    """
    import re

    # Lowercase
    normalized = name.lower().strip()

    # Remove common suffixes
    for suffix in ["crm", "erp", "365", "online", "cloud", "suite", "platform"]:
        normalized = re.sub(rf'\b{suffix}\b', '', normalized)

    # Remove special chars
    normalized = re.sub(r'[^\w\s]', '', normalized)

    # Remove extra whitespace
    normalized = ' '.join(normalized.split())

    return normalized
```

**2. Repository Interface** (`domain/repositories/application_repository.py`)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.application import Application, ApplicationId, Entity

class ApplicationRepository(ABC):
    """Repository interface for Application aggregate.

    This defines the contract for persistence - implementations can use
    PostgreSQL, MongoDB, in-memory, etc.
    """

    @abstractmethod
    def save(self, app: Application) -> None:
        """Save or update application (upsert).

        If app.id already exists, update it.
        If app.id is new, insert it.
        """
        pass

    @abstractmethod
    def find_by_id(self, app_id: ApplicationId) -> Optional[Application]:
        """Find application by ID."""
        pass

    @abstractmethod
    def find_or_create(
        self,
        name: str,
        entity: Entity,
        initial_data: dict = None
    ) -> Application:
        """Find existing app or create new one.

        This is the PRIMARY method for deduplication:
        1. Generate stable ID from (name, entity)
        2. Try to find existing app with that ID
        3. If found, return it
        4. If not found, create new and save

        Result: GUARANTEED single app per (normalized_name, entity)
        """
        pass

    @abstractmethod
    def find_by_entity(self, entity: Entity, status: str = "active") -> List[Application]:
        """Find all applications for an entity."""
        pass

    @abstractmethod
    def find_similar(
        self,
        name: str,
        entity: Entity,
        threshold: float = 0.65
    ) -> List[Application]:
        """Find applications with similar names (fuzzy search).

        Used for detecting potential duplicates that slipped through
        due to name variations.
        """
        pass

    @abstractmethod
    def count_by_entity(self, entity: Entity) -> int:
        """Count applications for an entity."""
        pass
```

**Testing:** Unit tests for domain logic (no I/O, pure logic)

```python
# tests/domain/test_application.py
def test_application_id_is_deterministic():
    """Same name + entity always generates same ID."""
    id1 = ApplicationId.generate("Salesforce", Entity.TARGET)
    id2 = ApplicationId.generate("Salesforce", Entity.TARGET)
    assert id1 == id2

def test_application_id_differs_by_entity():
    """Same name, different entity = different ID."""
    id_target = ApplicationId.generate("Salesforce", Entity.TARGET)
    id_buyer = ApplicationId.generate("Salesforce", Entity.BUYER)
    assert id_target != id_buyer

def test_normalize_removes_crm_suffix():
    """Normalization removes common suffixes."""
    assert normalize_application_name("Salesforce CRM") == "salesforce"
    assert normalize_application_name("Microsoft 365") == "microsoft"

def test_duplicate_detection_fuzzy_match():
    """is_duplicate_of uses fuzzy matching."""
    app1 = Application(
        id=ApplicationId.generate("Salesforce", Entity.TARGET),
        entity=Entity.TARGET,
        name="Salesforce"
    )
    app2 = Application(
        id=ApplicationId.generate("Salesforce CRM", Entity.TARGET),
        entity=Entity.TARGET,
        name="Salesforce CRM"
    )
    # Normalized names match, should be duplicate
    assert app1.is_duplicate_of(app2)
```

---

### Week 2: Repository Implementation

**Goal:** Implement PostgreSQL repository with database-enforced deduplication

#### Deliverables

**1. Database Schema Migration** (`alembic/versions/004_domain_model.py`)

```sql
-- New applications table (replaces inventory items for apps)
CREATE TABLE applications (
    -- Identity (PRIMARY KEY)
    id VARCHAR(50) PRIMARY KEY,  -- "app_a3f291cd_target"

    -- Entity scoping (NOT NULL + CHECK constraint)
    entity VARCHAR(10) NOT NULL CHECK (entity IN ('target', 'buyer')),

    -- Core data
    name VARCHAR(255) NOT NULL,
    name_normalized VARCHAR(255) NOT NULL,  -- For fuzzy search
    vendor VARCHAR(255),
    version VARCHAR(100),
    category VARCHAR(100),

    -- Cost
    cost_amount DECIMAL(12,2),
    cost_currency VARCHAR(3) DEFAULT 'USD',
    cost_status VARCHAR(50) CHECK (cost_status IN ('known', 'estimated', 'internal_no_cost', 'unknown')),

    -- Metadata
    criticality VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'removed', 'deprecated')),

    -- Observations (JSONB for flexibility)
    observations JSONB DEFAULT '[]'::jsonb,

    -- Audit fields
    deal_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Deduplication enforcement
    UNIQUE (name_normalized, entity, deal_id)
);

-- Indexes for performance
CREATE INDEX idx_applications_entity ON applications(entity);
CREATE INDEX idx_applications_deal ON applications(deal_id);
CREATE INDEX idx_applications_name_trgm ON applications USING gin(name_normalized gin_trgm_ops);  -- For fuzzy search

-- Full-text search
CREATE INDEX idx_applications_search ON applications USING gin(
    to_tsvector('english', name || ' ' || COALESCE(vendor, ''))
);
```

**2. ORM Models** (`infrastructure/persistence/models.py`)

```python
from sqlalchemy import Column, String, Numeric, DateTime, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from web.database import db

class ApplicationModel(db.Model):
    """SQLAlchemy ORM model for applications table."""
    __tablename__ = 'applications'

    # Identity
    id = Column(String(50), primary_key=True)
    entity = Column(String(10), nullable=False)

    # Core data
    name = Column(String(255), nullable=False)
    name_normalized = Column(String(255), nullable=False)
    vendor = Column(String(255))
    version = Column(String(100))
    category = Column(String(100))

    # Cost
    cost_amount = Column(Numeric(12, 2))
    cost_currency = Column(String(3), default='USD')
    cost_status = Column(String(50))

    # Metadata
    criticality = Column(String(50))
    status = Column(String(50), default='active')

    # Observations (JSONB)
    observations = Column(JSONB, default=[])

    # Audit
    deal_id = Column(String(50), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # Constraints
    __table_args__ = (
        CheckConstraint("entity IN ('target', 'buyer')", name='check_entity'),
        CheckConstraint("status IN ('active', 'removed', 'deprecated')", name='check_status'),
        UniqueConstraint('name_normalized', 'entity', 'deal_id', name='unique_app_per_entity_deal'),
    )
```

**3. Repository Implementation** (`infrastructure/repositories/postgresql_application_repository.py`)

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from difflib import SequenceMatcher

from domain.entities.application import Application, ApplicationId, Entity, normalize_application_name, Money, Observation
from domain.repositories.application_repository import ApplicationRepository
from infrastructure.persistence.models import ApplicationModel

class PostgreSQLApplicationRepository(ApplicationRepository):
    """PostgreSQL implementation of ApplicationRepository."""

    def __init__(self, db_session: Session, deal_id: str):
        self.session = db_session
        self.deal_id = deal_id

    def save(self, app: Application) -> None:
        """Save or update application."""
        # Check if exists
        existing = self.session.query(ApplicationModel).get(app.id.value)

        if existing:
            # Update existing
            self._update_model_from_domain(existing, app)
        else:
            # Create new
            model = self._domain_to_model(app)
            self.session.add(model)

        self.session.commit()

    def find_by_id(self, app_id: ApplicationId) -> Optional[Application]:
        """Find by ID."""
        model = self.session.query(ApplicationModel).get(app_id.value)
        return self._model_to_domain(model) if model else None

    def find_or_create(
        self,
        name: str,
        entity: Entity,
        initial_data: dict = None
    ) -> Application:
        """Find existing app or create new.

        DEDUPLICATION HAPPENS HERE:
        - Generate stable ID from (name, entity)
        - Check if app with that ID exists
        - If yes, return existing (prevents duplicate)
        - If no, create new
        """
        # Generate stable ID
        app_id = ApplicationId.generate(name, entity)

        # Try to find existing
        existing = self.find_by_id(app_id)
        if existing:
            return existing

        # Create new
        app = Application(
            id=app_id,
            entity=entity,
            name=name,
            **(initial_data or {})
        )
        self.save(app)
        return app

    def find_by_entity(self, entity: Entity, status: str = "active") -> List[Application]:
        """Find all apps for entity."""
        models = self.session.query(ApplicationModel).filter_by(
            entity=entity.value,
            deal_id=self.deal_id,
            status=status
        ).all()

        return [self._model_to_domain(m) for m in models]

    def find_similar(
        self,
        name: str,
        entity: Entity,
        threshold: float = 0.65
    ) -> List[Application]:
        """Fuzzy search for similar names."""
        normalized_search = normalize_application_name(name)

        # Get all apps for entity
        candidates = self.find_by_entity(entity)

        # Filter by similarity
        similar = []
        for app in candidates:
            normalized_candidate = normalize_application_name(app.name)
            similarity = SequenceMatcher(
                None,
                normalized_search,
                normalized_candidate
            ).ratio()

            if similarity >= threshold:
                similar.append(app)

        return similar

    def count_by_entity(self, entity: Entity) -> int:
        """Count apps."""
        return self.session.query(ApplicationModel).filter_by(
            entity=entity.value,
            deal_id=self.deal_id,
            status='active'
        ).count()

    def _domain_to_model(self, app: Application) -> ApplicationModel:
        """Convert domain object to ORM model."""
        return ApplicationModel(
            id=app.id.value,
            entity=app.entity.value,
            name=app.name,
            name_normalized=normalize_application_name(app.name),
            vendor=app.vendor,
            version=app.version,
            category=app.category,
            cost_amount=app.cost.amount if app.cost else None,
            cost_currency=app.cost.currency if app.cost else 'USD',
            cost_status=app.cost.status if app.cost else 'unknown',
            criticality=app.criticality,
            status='active',
            observations=[obs.__dict__ for obs in app.observations],
            deal_id=self.deal_id,
            created_at=app.created_at,
            updated_at=app.updated_at,
        )

    def _model_to_domain(self, model: ApplicationModel) -> Application:
        """Convert ORM model to domain object."""
        return Application(
            id=ApplicationId(model.id),
            entity=Entity(model.entity),
            name=model.name,
            vendor=model.vendor,
            version=model.version,
            category=model.category,
            cost=Money(
                amount=float(model.cost_amount) if model.cost_amount else 0.0,
                currency=model.cost_currency or 'USD',
                status=model.cost_status or 'unknown'
            ) if model.cost_amount else None,
            criticality=model.criticality,
            observations=[Observation(**obs) for obs in (model.observations or [])],
            created_at=str(model.created_at),
            updated_at=str(model.updated_at),
        )

    def _update_model_from_domain(self, model: ApplicationModel, app: Application) -> None:
        """Update existing model from domain object."""
        model.name = app.name
        model.name_normalized = normalize_application_name(app.name)
        model.vendor = app.vendor
        model.version = app.version
        model.category = app.category
        model.cost_amount = app.cost.amount if app.cost else None
        model.cost_currency = app.cost.currency if app.cost else 'USD'
        model.cost_status = app.cost.status if app.cost else 'unknown'
        model.criticality = app.criticality
        model.observations = [obs.__dict__ for obs in app.observations]
        model.updated_at = app.updated_at
```

**Testing:** Integration tests with test database

```python
# tests/integration/test_postgresql_application_repository.py
def test_find_or_create_returns_existing(test_db_session):
    """find_or_create returns existing app, doesn't create duplicate."""
    repo = PostgreSQLApplicationRepository(test_db_session, deal_id="test-deal")

    # Create first time
    app1 = repo.find_or_create("Salesforce", Entity.TARGET)
    count1 = repo.count_by_entity(Entity.TARGET)

    # "Create" again with same name
    app2 = repo.find_or_create("Salesforce", Entity.TARGET)
    count2 = repo.count_by_entity(Entity.TARGET)

    # Should return same app, not create duplicate
    assert app1.id == app2.id
    assert count1 == 1
    assert count2 == 1  # Count didn't increase

def test_find_or_create_normalizes_names(test_db_session):
    """find_or_create treats name variants as same app."""
    repo = PostgreSQLApplicationRepository(test_db_session, deal_id="test-deal")

    app1 = repo.find_or_create("Salesforce", Entity.TARGET)
    app2 = repo.find_or_create("Salesforce CRM", Entity.TARGET)  # Variant name

    # Should return same app (normalization removes "CRM")
    assert app1.id == app2.id
    assert repo.count_by_entity(Entity.TARGET) == 1

def test_unique_constraint_prevents_duplicates(test_db_session):
    """Database UNIQUE constraint prevents duplicate apps."""
    from sqlalchemy.exc import IntegrityError

    repo = PostgreSQLApplicationRepository(test_db_session, deal_id="test-deal")

    # Create app
    app = Application(
        id=ApplicationId.generate("Salesforce", Entity.TARGET),
        entity=Entity.TARGET,
        name="Salesforce"
    )
    repo.save(app)

    # Try to create duplicate directly (bypassing find_or_create)
    duplicate = Application(
        id=ApplicationId.generate("Salesforce", Entity.TARGET),  # Same ID
        entity=Entity.TARGET,
        name="Salesforce"
    )

    # Should fail with IntegrityError
    with pytest.raises(IntegrityError):
        repo.save(duplicate)
```

---

### Week 3: Pipeline Refactor

**Goal:** Refactor analysis pipeline to use domain model

#### Deliverables

**1. Unified Ingestion Service** (`services/inventory_ingestion_service.py`)

```python
from typing import List, Tuple
from domain.entities.application import Application, Entity, Observation
from domain.repositories.application_repository import ApplicationRepository
import logging

logger = logging.getLogger(__name__)

class InventoryIngestionService:
    """Orchestrates extraction from multiple sources into unified Application domain objects.

    This is the RECONCILIATION LAYER that was missing before.
    Both deterministic parser and LLM facts flow through here.
    """

    def __init__(self, app_repo: ApplicationRepository):
        self.app_repo = app_repo

    def ingest_from_table(
        self,
        table_data: dict,
        entity: Entity,
        source_document: str
    ) -> Application:
        """Ingest application from deterministic table parser.

        Example table_data:
        {
            "name": "Salesforce",
            "vendor": "Salesforce.com",
            "cost": 50000,
            "users": 100
        }
        """
        name = table_data.get("name")
        if not name:
            raise ValueError("Table data missing 'name' field")

        # Find or create app (deduplication happens here)
        app = self.app_repo.find_or_create(name, entity)

        # Add observation
        obs = Observation(
            source_document=source_document,
            source_type="table",
            extracted_data=table_data,
            confidence=1.0,  # Deterministic = 100% confidence
            timestamp=_now_iso()
        )
        app.add_observation(obs)

        # Save
        self.app_repo.save(app)

        logger.info(f"[INGESTION] Table → {app.id.value} ({app.name})")
        return app

    def ingest_from_fact(
        self,
        fact: "Fact",  # From FactStore
        entity: Entity
    ) -> Application:
        """Ingest application from LLM-extracted fact.

        Example fact:
        Fact(
            item="Salesforce CRM",
            details={"vendor": "Salesforce", "users": "~100"},
            source_document="diligence.pdf"
        )
        """
        name = fact.item
        if not name:
            raise ValueError("Fact missing 'item' field")

        # Find or create app (deduplication happens here)
        app = self.app_repo.find_or_create(name, entity)

        # Add observation
        obs = Observation(
            source_document=fact.source_document,
            source_type="llm_prose",
            extracted_data=fact.details or {},
            confidence=fact.confidence_score if hasattr(fact, 'confidence_score') else 0.7,
            timestamp=_now_iso()
        )
        app.add_observation(obs)

        # Save
        self.app_repo.save(app)

        logger.info(f"[INGESTION] LLM → {app.id.value} ({app.name})")
        return app

    def reconcile_duplicates(self, entity: Entity, threshold: float = 0.65) -> int:
        """Find and merge potential duplicates that slipped through normalization.

        This is a SAFETY NET for edge cases where normalization didn't catch duplicates.
        """
        apps = self.app_repo.find_by_entity(entity)
        merged_count = 0

        # O(n^2) comparison - acceptable for <1000 apps
        for i, app1 in enumerate(apps):
            for app2 in apps[i+1:]:
                if app1.is_duplicate_of(app2, threshold):
                    logger.warning(
                        f"[RECONCILIATION] Found duplicate: {app1.id.value} ≈ {app2.id.value}"
                    )
                    # Merge app2 into app1
                    app1.merge(app2)
                    self.app_repo.save(app1)

                    # Mark app2 as removed
                    app2.status = "removed"
                    self.app_repo.save(app2)

                    merged_count += 1

        logger.info(f"[RECONCILIATION] Merged {merged_count} duplicates for {entity.value}")
        return merged_count


def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat()
```

**2. Refactored Analysis Pipeline** (`web/analysis_runner.py` changes)

```python
# NEW: Replace lines 764-1024 with this unified approach

def run_analysis(task: AnalysisTask, progress_callback: Callable, app=None) -> Dict[str, Any]:
    """Run analysis with domain-first architecture."""

    # ... (document parsing unchanged)

    # Create domain repository
    from infrastructure.repositories.postgresql_application_repository import PostgreSQLApplicationRepository
    from services.inventory_ingestion_service import InventoryIngestionService

    with db.session_scope() as db_session:
        app_repo = PostgreSQLApplicationRepository(db_session, deal_id=deal_id)
        ingestion_service = InventoryIngestionService(app_repo)

        # ===================================================================
        # PHASE 1: EXTRACTION (Parallel, No Side Effects)
        # ===================================================================

        # 1a. Deterministic table extraction
        table_apps = []
        for doc in target_docs:
            tables = deterministic_parser.extract_tables(doc)
            table_apps.extend(tables)

        logger.info(f"[EXTRACTION] Tables: {len(table_apps)} apps found")

        # 1b. LLM prose extraction
        llm_facts = []
        for domain in domains_to_analyze:
            facts, gaps = run_discovery_for_domain(domain, content, session, ...)
            llm_facts.extend(facts)

        logger.info(f"[EXTRACTION] LLM: {len(llm_facts)} facts found")

        # ===================================================================
        # PHASE 2: INGESTION (Single Pass, Deduplicates)
        # ===================================================================

        # Ingest table data
        for table_data in table_apps:
            try:
                ingestion_service.ingest_from_table(
                    table_data=table_data,
                    entity=Entity.TARGET,
                    source_document=table_data.get("_source_file", "")
                )
            except Exception as e:
                logger.error(f"Failed to ingest table app: {e}")

        # Ingest LLM facts
        for fact in llm_facts:
            try:
                ingestion_service.ingest_from_fact(
                    fact=fact,
                    entity=Entity(fact.entity)
                )
            except Exception as e:
                logger.error(f"Failed to ingest fact: {e}")

        # Reconcile any duplicates that slipped through
        duplicates_merged = ingestion_service.reconcile_duplicates(Entity.TARGET)

        # ===================================================================
        # RESULT: Single Source of Truth
        # ===================================================================

        final_count = app_repo.count_by_entity(Entity.TARGET)
        logger.info(f"[INGESTION] Final count: {final_count} applications (TARGET)")

        # No more InventoryStore.save() - data is already in database!
        # No more "Legacy Facts" fallback - ApplicationRepository is the truth
```

**Testing:** End-to-end pipeline tests

```python
# tests/integration/test_analysis_pipeline.py
def test_pipeline_deduplicates_table_and_llm(test_documents):
    """Full pipeline with table + LLM should deduplicate properly."""
    # GIVEN: Document with "Salesforce" in table and "Salesforce CRM" in prose
    doc = test_documents["salesforce_duplicate.pdf"]

    # WHEN: Run analysis
    result = run_analysis(task=AnalysisTask(file_paths=[doc]), ...)

    # THEN: Exactly 1 Salesforce app should exist
    app_repo = get_application_repository()
    apps = app_repo.find_by_entity(Entity.TARGET)
    salesforce_apps = [a for a in apps if "salesforce" in a.name.lower()]

    assert len(salesforce_apps) == 1

    # AND: Should have 2 observations (1 from table, 1 from LLM)
    assert len(salesforce_apps[0].observations) == 2
    assert salesforce_apps[0].observations[0].source_type == "table"
    assert salesforce_apps[0].observations[1].source_type == "llm_prose"
```

---

### Week 4: UI Migration

**Goal:** Update UI to read from ApplicationRepository

#### Deliverables

**1. Application Query Service** (`services/application_query_service.py`)

```python
from typing import List, Dict, Any
from domain.entities.application import Entity
from domain.repositories.application_repository import ApplicationRepository

class ApplicationQueryService:
    """Read-only query service for UI.

    Thin layer over ApplicationRepository that formats data for UI consumption.
    """

    def __init__(self, app_repo: ApplicationRepository):
        self.app_repo = app_repo

    def get_applications_for_ui(
        self,
        entity: str,
        category: str = None,
        search_query: str = None
    ) -> List[Dict[str, Any]]:
        """Get applications formatted for UI display."""
        entity_enum = Entity.from_string(entity)
        apps = self.app_repo.find_by_entity(entity_enum)

        # Filter by category if provided
        if category:
            apps = [a for a in apps if a.category == category]

        # Filter by search query if provided
        if search_query:
            query_lower = search_query.lower()
            apps = [a for a in apps if query_lower in a.name.lower() or
                    (a.vendor and query_lower in a.vendor.lower())]

        # Format for UI
        return [self._format_app_for_ui(a) for a in apps]

    def get_application_summary(self, entity: str) -> Dict[str, Any]:
        """Get summary statistics for entity."""
        entity_enum = Entity.from_string(entity)
        apps = self.app_repo.find_by_entity(entity_enum)

        return {
            "total_count": len(apps),
            "by_category": self._count_by_category(apps),
            "total_cost": sum(a.cost.amount for a in apps if a.cost),
            "critical_count": sum(1 for a in apps if a.criticality == "critical"),
        }

    def _format_app_for_ui(self, app: Application) -> Dict[str, Any]:
        """Format single app for UI template."""
        return {
            "id": app.id.value,
            "name": app.name,
            "vendor": app.vendor or "—",
            "category": app.category or "—",
            "cost": app.cost.amount if app.cost else None,
            "cost_status": app.cost.status if app.cost else "unknown",
            "criticality": app.criticality or "—",
            "observation_count": len(app.observations),
            "entity": app.entity.value,
        }
```

**2. Updated UI Routes** (`web/blueprints/applications.py`)

```python
# BEFORE (OLD CODE - DELETE THIS):
@bp.route('/applications')
def applications_page():
    inventory_store, entity = get_inventory_store(entity_filter)
    apps = inventory_store.get_items(inventory_type="application", entity=entity)

    if len(apps) == 0:  # FALLBACK LOGIC (BAD!)
        apps = build_apps_from_facts(fact_store, entity)
        show_legacy_banner = True

    return render_template('applications.html', apps=apps, show_legacy_banner=show_legacy_banner)


# AFTER (NEW CODE):
@bp.route('/applications')
def applications_page():
    """Applications inventory page - domain-first architecture."""
    entity = request.args.get('entity', 'target')
    category = request.args.get('category')
    search_query = request.args.get('q')

    # Get current deal
    deal_id = session.get('active_deal_id')
    if not deal_id:
        flash("No active deal selected", "warning")
        return redirect(url_for('deals.list_deals'))

    # Create repository and query service
    from infrastructure.repositories.postgresql_application_repository import PostgreSQLApplicationRepository
    from services.application_query_service import ApplicationQueryService

    with db.session_scope() as db_session:
        app_repo = PostgreSQLApplicationRepository(db_session, deal_id=deal_id)
        query_service = ApplicationQueryService(app_repo)

        # Get data (SINGLE SOURCE OF TRUTH)
        apps = query_service.get_applications_for_ui(entity, category, search_query)
        summary = query_service.get_application_summary(entity)

    # Render (NO FALLBACK LOGIC)
    return render_template(
        'applications.html',
        apps=apps,
        summary=summary,
        current_entity=entity,
        show_legacy_banner=False  # NEVER show legacy banner - always use repository
    )
```

**3. Template Updates** (`web/templates/applications.html`)

```html
<!-- REMOVE THIS BANNER (DELETE): -->
{% if show_legacy_banner %}
<div class="alert alert-warning">
    <strong>Legacy Facts (May contain duplicates)</strong>
    Analysis Data - Showing applications from legacy fact store.
</div>
{% endif %}

<!-- KEEP THIS (Apps display logic unchanged): -->
{% for app in apps %}
<tr>
    <td>{{ app.name }}</td>
    <td>{{ app.vendor }}</td>
    <td>{{ app.category }}</td>
    <td>${{ "{:,.0f}".format(app.cost) if app.cost else "—" }}</td>
    <td>
        {% if app.cost_status == 'known' %}
            <span class="badge badge-success">✓</span>
        {% elif app.cost_status == 'estimated' %}
            <span class="badge badge-warning">~</span>
        {% endif %}
    </td>
</tr>
{% endfor %}
```

---

### Week 5-6: Testing, Migration, Cutover

**Goal:** Validate, migrate data, and deploy

#### Deliverables

**1. Comprehensive Test Suite**

```python
# tests/integration/test_complete_pipeline.py
class TestCompletePipeline:
    """End-to-end tests for entire data flow."""

    def test_no_duplicates_across_runs(self):
        """Re-importing same document doesn't create duplicates."""
        # Run 1: Import document
        result1 = run_analysis(doc="salesforce.pdf")
        count1 = get_application_count()

        # Run 2: Import SAME document again
        result2 = run_analysis(doc="salesforce.pdf")
        count2 = get_application_count()

        # Should have same count (deduplication worked)
        assert count1 == count2

    def test_target_buyer_isolation(self):
        """Target and buyer data remains separate."""
        # Import target docs
        run_analysis(docs=["target_salesforce.pdf"], entity="target")

        # Import buyer docs with SAME app names
        run_analysis(docs=["buyer_salesforce.pdf"], entity="buyer")

        # Should have 2 Salesforce apps (different entities)
        target_apps = query_service.get_applications_for_ui("target")
        buyer_apps = query_service.get_applications_for_ui("buyer")

        assert len(target_apps) == 1
        assert len(buyer_apps) == 1
        assert target_apps[0]['id'] != buyer_apps[0]['id']  # Different IDs

    def test_ui_never_shows_legacy_banner(self):
        """UI always uses repository, never falls back to facts."""
        # Import data
        run_analysis(docs=["apps.pdf"])

        # Load UI page
        response = client.get('/applications?entity=target')

        # Should NOT contain legacy banner
        assert "Legacy Facts" not in response.text
        assert "May contain duplicates" not in response.text
```

**2. Data Migration Script** (`scripts/migrate_to_domain_model.py`)

```python
"""Migrate existing InventoryStore data to new ApplicationRepository.

This script:
1. Reads existing inventory JSON files
2. Converts to Application domain objects
3. Saves to new applications table
4. Validates counts match
"""

def migrate_deal(deal_id: str):
    """Migrate single deal's inventory data."""
    # Load old inventory
    old_inv_path = f"data/deals/{deal_id}/inventory.json"
    with open(old_inv_path) as f:
        old_items = json.load(f)

    # Create repository
    app_repo = PostgreSQLApplicationRepository(db.session, deal_id)

    # Migrate each item
    migrated = 0
    for item in old_items:
        if item['inventory_type'] != 'application':
            continue  # Skip infra/org for now

        # Convert to Application
        app = Application(
            id=ApplicationId.generate(item['data']['name'], Entity(item['entity'])),
            entity=Entity(item['entity']),
            name=item['data']['name'],
            vendor=item['data'].get('vendor'),
            cost=Money(item['data']['cost']) if item['data'].get('cost') else None,
            # ... other fields
        )

        app_repo.save(app)
        migrated += 1

    print(f"Migrated {migrated} applications for deal {deal_id}")

    # Validate
    new_count = app_repo.count_by_entity(Entity.TARGET)
    old_count = len([i for i in old_items if i['entity'] == 'target'])
    assert new_count == old_count, f"Count mismatch: {new_count} != {old_count}"
```

**3. Rollout Plan**

**Phase 5.1: Parallel Run (Week 5)**
- Deploy new code WITH feature flag: `USE_DOMAIN_MODEL = False`
- Run both old and new pipelines in parallel
- Compare outputs: counts should match within 5%
- Log any discrepancies

**Phase 5.2: Gradual Cutover (Week 6)**
- Monday: Enable for internal test deals (10% traffic)
- Wednesday: Enable for all new deals (50% traffic)
- Friday: Enable for all deals (100% traffic)
- Monitor:
  - Application counts (should stabilize)
  - "Legacy Facts" banner appearances (should drop to 0)
  - Database query performance

**Phase 5.3: Legacy Cleanup (Week 7)**
- Remove old InventoryStore code
- Remove FactStore→Inventory promotion code
- Remove UI fallback logic
- Archive old JSON files

---

## Success Criteria

### Quantitative Metrics

| Metric | Current State | Target State | Measurement |
|--------|---------------|--------------|-------------|
| Application count accuracy | 143 apps (should be ~60) | ±3 apps from manual count | Compare to manual inventory spreadsheet |
| Duplication rate | ~40% duplicates | <2% duplicates | Run same doc 2x, count increase |
| "Legacy Facts" banner | 100% of page loads | 0% of page loads | Log banner display events |
| Entity isolation | 15% cross-contamination | 0% cross-contamination | Check target apps don't appear in buyer |
| InventoryStore save failures | ~30% of runs | 0% (no longer used) | Remove file I/O dependency |

### Qualitative Goals

✅ **Single Source of Truth:** ApplicationRepository is authoritative, no fallback logic
✅ **Stable Identity:** Same app gets same ID across multiple analysis runs
✅ **Domain-Driven:** Business logic in domain layer, storage is implementation detail
✅ **Testable:** Can test deduplication without database (mock repository)
✅ **Maintainable:** New feature = add to Application entity, not scattered across stores

---

## Risks & Mitigation

### Risk 1: Data Migration Failures

**Probability:** Medium
**Impact:** High (existing deals show no data)
**Mitigation:**
- Validate migration script on copy of production data
- Keep old JSON files as backup for 30 days
- Implement rollback: `REVERT_TO_OLD_INVENTORY = True` flag

### Risk 2: Performance Degradation

**Probability:** Low
**Impact:** Medium (slower page loads)
**Mitigation:**
- Add database indexes (done in schema)
- Implement query result caching (Redis)
- Load test with 10,000 applications before cutover

### Risk 3: Unforeseen Edge Cases

**Probability:** High
**Impact:** Low (individual bugs, not systemic)
**Mitigation:**
- Parallel run (week 5) will expose edge cases
- Gradual rollout (10% → 50% → 100%)
- Keep old code path for emergency fallback

---

## Dependencies

- **Database:** PostgreSQL 12+ (for JSONB and trigram indexes)
- **ORM:** SQLAlchemy 2.0+ (already in use)
- **Migration Tool:** Alembic (already in use)
- **Testing:** pytest, factory_boy (for test data)

---

## Open Questions

1. **How to handle Infrastructure and Organization domains?**
   - Same pattern (InfrastructureRepository, OrganizationRepository)
   - Or generic `InventoryItemRepository<T>` with type parameter?

2. **Should we keep FactStore for non-inventory observations?**
   - Yes - facts about "document quality", "coverage gaps" don't fit Application model
   - No - everything becomes an Observation on some entity

3. **How to handle historical data from before migration?**
   - Keep old JSON files indefinitely?
   - Migrate on-the-fly when deal is accessed?

---

## Next Steps After Planning

**Week 0 (This Week):**
1. ✅ Review this plan with stakeholders
2. ✅ Get buy-in on 6-week timeline
3. ✅ Set up feature flag system (`USE_DOMAIN_MODEL = False`)
4. ✅ Create `architecture/` branch for implementation

**Week 1 Kickoff:**
1. Implement domain entities (Application, ApplicationId, Entity)
2. Write unit tests for domain logic
3. Daily sync: show working domain model by Friday

**Want me to start Week 1 implementation now? I can build the domain model POC.**
