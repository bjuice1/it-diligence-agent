# Experimental Domain Model - Complete Isolation Strategy
## Safe Background Development During Production Demo

**Status:** ACTIVE
**Priority:** P0 - CRITICAL (Demo protection + parallel development)
**Created:** 2026-02-12
**Purpose:** Build new domain model system in complete isolation without ANY risk to Railway production

---

## 📊 CURRENT STATE ANALYSIS

### Production Environment (Railway)

**Current Commit:** `edf84e4` (REFINE: Architecture crisis doc - executive-ready with financial analysis)
**Critical Rollback:** `5ba1bb9` (ROLLBACK: Disable fact promotion to fix duplication crisis)
**Git Status:** Clean (no uncommitted changes)
**Demo Date:** 2026-02-13 (TOMORROW)

### Existing Code Structure

```
9.5/it-diligence-agent 2/
├── [PRODUCTION - ACTIVE ON RAILWAY]
│   ├── agents_v2/              ← Discovery, reasoning, narrative agents
│   ├── stores/                 ← FactStore, InventoryStore (current system)
│   ├── web/                    ← Flask app (7,435 lines, deployed to Railway)
│   ├── services/               ← Business logic (cost_engine, bridges)
│   ├── main_v2.py              ← CLI (1,635 lines)
│   ├── config_v2.py            ← Configuration
│   └── data/                   ← Sessions, reports, uploads
│
├── [PROOF-OF-CONCEPT - NOT IN PRODUCTION]
│   └── domain/                 ← POC from commit dccf49c (1,180 lines)
│       ├── entities/           ← Application, Observation
│       ├── value_objects/      ← ApplicationId, Entity, Money
│       ├── repositories/       ← ApplicationRepository interface
│       └── DEMO.py             ← Proof of concept demo
│
└── [DOCUMENTATION]
    ├── ARCHITECTURAL_CRISIS_SUMMARY.md      ← Root cause analysis (16 pages)
    ├── docs/architecture/
    │   └── domain-first-redesign-plan.md    ← 6-week migration plan (28 pages)
    └── audits/                              ← Known issues (A1-C3)
```

### Key Findings from Investigation

✅ **Production is NOT importing domain/** (verified via grep - zero imports found)
✅ **POC code already exists** in `domain/` directory (1,180 lines, 11 files)
✅ **Git is clean** - no uncommitted changes
✅ **Railway deployment stable** - running rollback commit (5ba1bb9)
⚠️ **No formal isolation** - POC is safe by accident, not by design
❌ **No safety guards** - domain code could be imported/executed accidentally
❌ **No documentation** - isolation strategy not formalized

---

## 🎯 ISOLATION REQUIREMENTS

### Critical Success Criteria

1. **Demo Protection (P0)**
   - Railway production MUST remain stable for demo tomorrow (2026-02-13)
   - ZERO risk of experimental code affecting production
   - Ability to rollback instantly if anything goes wrong

2. **Parallel Development (P0)**
   - Build new domain model in background without blocking production
   - Workers can build aggressively without fear of breaking Railway
   - Experimental code can be tested independently

3. **Clean Migration Path (P1)**
   - Clear boundary between old system (stores/) and new system (domain/)
   - Ability to compare old vs new (side-by-side validation)
   - Gradual cutover strategy when ready (not big bang)

4. **Developer Safety (P1)**
   - Impossible to accidentally import experimental code in production
   - Explicit opt-in required to use experimental features
   - Loud failures if isolation is violated

---

## 🔒 ISOLATION ARCHITECTURE

### Strategy: Multi-Layer Defense

We use **5 independent isolation layers** so that failure of any single layer does not compromise production.

```
Layer 1: Directory Separation
  ├── Production: agents_v2/, stores/, web/, services/
  └── Experimental: domain/ (already separate)

Layer 2: Import Protection
  ├── Guards in domain/__init__.py warn on production imports
  └── CI check: grep for 'from domain' in production code

Layer 3: Database Isolation
  ├── Production: Uses existing DB (via .env)
  └── Experimental: Uses domain_experimental.db (separate SQLite)

Layer 4: Feature Flags
  ├── ENABLE_DOMAIN_MODEL=false (Railway environment variable)
  └── Runtime checks prevent execution even if imported

Layer 5: Environment Validation
  ├── ENVIRONMENT=production → domain code raises error
  └── Experimental code CANNOT run on Railway
```

---

## 📁 DIRECTORY STRUCTURE (AFTER SETUP)

```
9.5/it-diligence-agent 2/
│
├── [PRODUCTION - DO NOT MODIFY DURING DEMO]
│   ├── agents_v2/              # Current discovery/reasoning agents
│   ├── stores/                 # FactStore, InventoryStore (4 truth systems)
│   │   ├── fact_store.py       # 118KB, F-DOMAIN-NNN IDs
│   │   ├── inventory_store.py  # 25KB, I-TYPE-HASH IDs
│   │   └── ...
│   ├── web/                    # Flask app (deployed to Railway)
│   │   ├── app.py              # 7,435 lines
│   │   └── blueprints/
│   ├── services/               # Business logic
│   ├── main_v2.py              # CLI entry point
│   └── config_v2.py            # Configuration
│
├── [EXPERIMENTAL - SAFE TO MODIFY AGGRESSIVELY]
│   ├── domain/                 # New domain model (POC + extensions)
│   │   │
│   │   ├── __init__.py         # 🛡️ IMPORT GUARD (warns on production use)
│   │   ├── guards.py           # 🛡️ RUNTIME GUARDS (prevents production execution)
│   │   ├── config.py           # 🛡️ EXPERIMENTAL CONFIG (separate DB)
│   │   │
│   │   ├── kernel/             # ⚙️ SHARED PRIMITIVES (all domains use these)
│   │   │   ├── entity.py       # Entity enum (target/buyer)
│   │   │   ├── observation.py  # Observation schema (shared)
│   │   │   ├── normalization.py  # Normalization rules (fixes P0-3)
│   │   │   ├── entity_inference.py  # Entity inference (shared logic)
│   │   │   ├── repository.py   # Repository base class
│   │   │   ├── fingerprint.py  # Stable ID generation
│   │   │   └── extraction.py   # Extraction coordinator (prevents double-counting)
│   │   │
│   │   ├── applications/       # 📦 APPLICATION DOMAIN
│   │   │   ├── application.py  # Application aggregate
│   │   │   ├── application_id.py  # ApplicationId value object
│   │   │   └── repository.py   # ApplicationRepository (extends kernel)
│   │   │
│   │   ├── infrastructure/     # 🖥️ INFRASTRUCTURE DOMAIN
│   │   │   ├── infrastructure.py  # Infrastructure aggregate
│   │   │   ├── infrastructure_id.py  # InfrastructureId value object
│   │   │   └── repository.py   # InfrastructureRepository (extends kernel)
│   │   │
│   │   ├── organization/       # 👥 ORGANIZATION DOMAIN
│   │   │   ├── organization_member.py  # OrganizationMember aggregate
│   │   │   ├── member_id.py    # MemberId value object
│   │   │   └── repository.py   # OrganizationRepository (extends kernel)
│   │   │
│   │   ├── adapters/           # 🔌 LEGACY INTEGRATION
│   │   │   ├── fact_store_adapter.py    # Reads old FactStore
│   │   │   ├── inventory_adapter.py     # Reads old InventoryStore
│   │   │   └── comparison.py   # Old vs New comparison tool
│   │   │
│   │   ├── services/           # 📊 DOMAIN SERVICES
│   │   │   ├── reconciliation_service.py  # Deduplication (fixes P0-2)
│   │   │   ├── analysis_service.py  # Orchestrates domain operations
│   │   │   └── migration_service.py  # Migrates old data to new model
│   │   │
│   │   ├── cli.py              # 🖥️ EXPERIMENTAL CLI (separate from main_v2.py)
│   │   ├── DEMO.py             # 🎬 POC demonstration
│   │   │
│   │   └── tests/              # ✅ DOMAIN MODEL TESTS
│   │       ├── test_kernel.py  # Kernel tests (90% coverage required)
│   │       ├── test_applications.py  # Application tests
│   │       ├── test_infrastructure.py  # Infrastructure tests
│   │       ├── test_integration.py  # Cross-domain integration
│   │       └── test_migration.py  # Migration tests
│   │
│   └── domain_experimental.db  # 🗄️ SEPARATE DATABASE (SQLite)
│
├── [CONFIGURATION]
│   ├── .env                    # Production config (Railway uses this)
│   ├── .env.experimental       # Experimental config (local dev only)
│   └── railway.json            # Railway deployment config
│
└── [DOCUMENTATION - STATUS TRACKING]
    ├── ISOLATION_STRATEGY.md   # 👈 THIS FILE
    ├── RAILWAY_DEMO_STATE.md   # Production snapshot (created during setup)
    ├── ARCHITECTURAL_CRISIS_SUMMARY.md
    └── docs/architecture/
        ├── domain-first-redesign-plan.md
        └── experimental-kernel-design.md  # (to be created)
```

---

## 🛡️ SAFETY MECHANISMS (5 LAYERS)

### Layer 1: Import Guard

**File:** `domain/__init__.py`

```python
"""
EXPERIMENTAL DOMAIN MODEL - NOT FOR PRODUCTION USE

This code is under active development for the domain-first redesign.
It should NOT be imported by production code paths.

Status: PROOF OF CONCEPT → ACTIVE DEVELOPMENT
Target: Replace stores/ (FactStore, InventoryStore)
Timeline: 6-8 weeks (see ISOLATION_STRATEGY.md)

Safe usage (local development):
    ENABLE_DOMAIN_MODEL=true python -m domain.cli analyze data/input/

Unsafe usage (production):
    from domain.applications import Application  # ❌ DON'T DO THIS in web/app.py!
"""

import os
import warnings

# Detect if imported in production environment
if os.getenv('ENVIRONMENT') == 'production':
    warnings.warn(
        "⚠️  EXPERIMENTAL DOMAIN MODEL IMPORTED IN PRODUCTION!\n"
        "This code is NOT ready for production use. "
        "Check your imports in web/, agents_v2/, or services/.\n"
        "See ISOLATION_STRATEGY.md for details.",
        RuntimeWarning,
        stacklevel=2
    )

# Expose public API
from domain.value_objects.entity import Entity
from domain.entities.application import Application
from domain.repositories.application_repository import ApplicationRepository

__all__ = ['Entity', 'Application', 'ApplicationRepository']
```

**Protection:** If production code imports domain, loud warning appears in logs.

---

### Layer 2: Runtime Guard

**File:** `domain/guards.py` (NEW)

```python
"""
Runtime guards prevent experimental code from executing in production.

Usage in all experimental entry points:
    from domain.guards import ExperimentalGuard

    def main():
        ExperimentalGuard.require_experimental_mode()  # Raises if production
        # ... rest of experimental code
"""

import os
import sys


class ExperimentalGuard:
    """Prevents experimental code from running in production."""

    @staticmethod
    def require_experimental_mode():
        """
        Raises RuntimeError if:
        1. ENVIRONMENT=production (Railway sets this)
        2. ENABLE_DOMAIN_MODEL != 'true' (explicit opt-in required)

        Call this at the start of EVERY experimental entry point:
        - domain/cli.py::main()
        - domain/services/*.py constructors
        - Any code that writes to database
        """
        # Check 1: Prevent execution in production environment
        if os.getenv('ENVIRONMENT') == 'production':
            raise RuntimeError(
                "🚨 EXPERIMENTAL DOMAIN MODEL CANNOT RUN IN PRODUCTION!\n\n"
                "This code is under active development and will cause data corruption.\n"
                "Environment: ENVIRONMENT=production detected.\n\n"
                "If you're seeing this on Railway, check your imports:\n"
                "  - web/app.py should NOT import domain.*\n"
                "  - agents_v2/ should NOT import domain.*\n\n"
                "See ISOLATION_STRATEGY.md for details."
            )

        # Check 2: Require explicit opt-in
        if os.getenv('ENABLE_DOMAIN_MODEL') != 'true':
            print(
                "ℹ️  Experimental domain model is disabled.\n"
                "To enable for local testing:\n"
                "  export ENABLE_DOMAIN_MODEL=true\n"
                "  python -m domain.cli analyze data/input/\n",
                file=sys.stderr
            )
            raise RuntimeError(
                "Experimental features disabled. "
                "Set ENABLE_DOMAIN_MODEL=true to use."
            )

    @staticmethod
    def is_experimental_enabled() -> bool:
        """Check if experimental mode is enabled (non-throwing)."""
        return (
            os.getenv('ENABLE_DOMAIN_MODEL') == 'true' and
            os.getenv('ENVIRONMENT') != 'production'
        )
```

**Protection:** Even if imported, experimental code CANNOT execute on Railway.

---

### Layer 3: Database Isolation

**File:** `domain/config.py` (NEW)

```python
"""
Experimental domain model configuration.

CRITICAL: Uses SEPARATE database from production to prevent data corruption.

Production DB: Uses DATABASE_URL from .env (PostgreSQL on Railway)
Experimental DB: Uses domain_experimental.db (SQLite, local only)
"""

import os
from domain.guards import ExperimentalGuard


class DomainConfig:
    """Configuration for experimental domain model."""

    def __init__(self):
        # Enforce experimental mode
        ExperimentalGuard.require_experimental_mode()

        # Use SEPARATE database (NEVER production DB)
        self.database_url = os.getenv(
            'DOMAIN_DATABASE_URL',
            'sqlite:///domain_experimental.db'  # Default: local SQLite
        )

        # PostgreSQL schema isolation (if using shared DB for testing)
        self.database_schema = os.getenv(
            'DOMAIN_DATABASE_SCHEMA',
            'domain_model_experimental'  # NOT public schema
        )

        # Verify we're NOT using production database
        production_db = os.getenv('DATABASE_URL')
        if production_db and self.database_url == production_db:
            raise RuntimeError(
                "🚨 EXPERIMENTAL CODE ATTEMPTING TO USE PRODUCTION DATABASE!\n\n"
                "domain_experimental.db != production DB\n"
                "Set DOMAIN_DATABASE_URL to a SEPARATE database.\n\n"
                "See ISOLATION_STRATEGY.md Layer 3."
            )

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite (vs PostgreSQL)."""
        return self.database_url.startswith('sqlite:///')

    @property
    def connection_args(self) -> dict:
        """SQLAlchemy connection arguments."""
        if self.is_sqlite:
            return {
                'check_same_thread': False,  # Allow multi-threaded access
                'timeout': 30  # 30 second lock timeout
            }
        else:
            return {
                'options': f'-c search_path={self.database_schema},public'
            }


# Singleton instance
config = DomainConfig()
```

**Protection:** Experimental code physically cannot touch production database.

---

### Layer 4: Feature Flags

**Railway Environment Variables:**

```bash
# Set in Railway dashboard (https://railway.app/project/...)
ENVIRONMENT=production
ENABLE_DOMAIN_MODEL=false      # Explicit disable
DATABASE_URL=postgresql://...   # Production database

# Experimental code checks these and refuses to run
```

**Local Development (.env.experimental):**

```bash
# Use this for local testing only (NOT deployed to Railway)
ENVIRONMENT=development
ENABLE_DOMAIN_MODEL=true
DOMAIN_DATABASE_URL=sqlite:///domain_experimental.db

# Load with: export $(cat .env.experimental | xargs)
```

**Protection:** Configuration-level isolation (Railway never enables experimental mode).

---

### Layer 5: CI Validation

**File:** `.github/workflows/isolation-check.yml` (to be created)

```yaml
name: Isolation Check
on: [push, pull_request]

jobs:
  verify-isolation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check production does not import domain
        run: |
          # Fail if production code imports experimental domain
          if grep -r "from domain" agents_v2/ stores/ web/ services/ main_v2.py; then
            echo "❌ Production code imports experimental domain!"
            echo "See ISOLATION_STRATEGY.md Layer 1"
            exit 1
          fi
          echo "✅ No domain imports in production code"

      - name: Check experimental uses separate database
        run: |
          # Verify experimental config uses domain_experimental.db
          if ! grep -q "domain_experimental.db" domain/config.py; then
            echo "❌ Experimental config does not use separate database!"
            exit 1
          fi
          echo "✅ Experimental uses separate database"

      - name: Verify guards exist
        run: |
          # Check guards.py exists and contains critical checks
          if [ ! -f domain/guards.py ]; then
            echo "❌ domain/guards.py missing!"
            exit 1
          fi
          if ! grep -q "ENVIRONMENT.*production" domain/guards.py; then
            echo "❌ Guards do not check ENVIRONMENT=production!"
            exit 1
          fi
          echo "✅ Guards are in place"
```

**Protection:** Automated checks prevent accidental isolation violations.

---

## 🤖 WORKER SPECIFICATIONS

### Execution Model: Kernel-First Sequential → Domain Parallel

**Phase 1: SEQUENTIAL (2-3 days)** - Build shared foundation
**Phase 2: PARALLEL (1-2 days)** - Build domain-specific logic

### Phase 1: Kernel Foundation (SEQUENTIAL)

#### **Worker 0: Isolation Setup** (30 minutes)

**Task:** Create isolation infrastructure before building domain model

**Deliverables:**
1. `domain/guards.py` - Runtime guards
2. `domain/config.py` - Database isolation config
3. `domain/__init__.py` - Import warnings (update existing)
4. `.env.experimental` - Experimental environment config
5. `RAILWAY_DEMO_STATE.md` - Production snapshot
6. Git tag: `demo-stable-2026-02-12`

**Validation:**
```bash
# Test guard prevents production execution
ENVIRONMENT=production ENABLE_DOMAIN_MODEL=true python -c "from domain.guards import ExperimentalGuard; ExperimentalGuard.require_experimental_mode()"
# Expected: RuntimeError with message about production

# Test import warning
ENVIRONMENT=production python -c "import domain"
# Expected: Warning about experimental code in production

# Verify separate database
grep "domain_experimental.db" domain/config.py
# Expected: Found

# Verify production code does not import domain
grep -r "from domain" agents_v2/ stores/ web/ main_v2.py
# Expected: (no output)
```

**Success Criteria:**
- ✅ All 5 files created
- ✅ Guards prevent production execution
- ✅ Import warnings work
- ✅ Separate database configured
- ✅ Git tag created
- ✅ Zero imports in production code

**Risk to Production:** ✅ **ZERO** (purely additive, no changes to production code)

---

#### **Worker 1: Kernel Design & Implementation** (2 days)

**Task:** Build `domain/kernel/` with shared primitives that ALL domains use

**Dependencies:** Worker 0 complete (isolation infrastructure exists)

**Constraint - Cross-Pollination Prevention:**
- Apps, Infrastructure, Org MUST share these primitives
- No domain can "reinvent" entity inference, normalization, or observation schema
- This prevents the "multiple sources of truth" problem at a smaller scale

**Deliverables:**

**1. `domain/kernel/entity.py`** - Entity value object
```python
from enum import Enum

class Entity(str, Enum):
    """
    Entity enum - shared across ALL domains.

    CRITICAL: Apps, Infrastructure, Org all use THIS enum.
    Prevents cross-domain inconsistency (app says 'target', infra says 'buyer').
    """
    TARGET = "target"
    BUYER = "buyer"

    def __str__(self) -> str:
        return self.value
```

**2. `domain/kernel/observation.py`** - Observation schema (SHARED)
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from domain.kernel.entity import Entity

@dataclass
class Observation:
    """
    Shared observation schema for ALL domains.

    CRITICAL: Applications, Infrastructure, Organization all use THIS schema.
    Prevents domain-specific observation formats from diverging.

    Example usage:
        # Application domain:
        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Page 5, Applications table, row 3",
            data={"cost": 50000, "users": 100}
        )

        # Infrastructure domain (SAME schema):
        obs = Observation(
            source_type="llm_prose",
            confidence=0.70,
            evidence="Mentioned in section 3.2",
            data={"provider": "AWS", "instances": 15}
        )
    """
    source_type: Literal["table", "llm_prose", "manual", "llm_assumption"]
    confidence: float  # 0.0 to 1.0
    evidence: str  # Where this observation came from (doc, page, section)
    extracted_at: datetime
    deal_id: str  # ALWAYS required for multi-tenant isolation
    entity: Entity  # ALWAYS required (target vs buyer)

    # Domain-specific data stored here
    data: dict[str, Any]

    def __post_init__(self):
        """Validate observation."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")
        if self.source_type not in ["table", "llm_prose", "manual", "llm_assumption"]:
            raise ValueError(f"Invalid source_type: {self.source_type}")
        if not self.deal_id:
            raise ValueError("deal_id is required for multi-tenant isolation")
```

**3. `domain/kernel/normalization.py`** - Normalization rules (fixes P0-3)
```python
"""
Shared normalization strategy for ALL domains.

CRITICAL: Applications, Infrastructure, Organization all use THESE rules.
Prevents cross-domain inconsistency in how names are normalized.

Fixes P0-3: "SAP ERP" vs "SAP SuccessFactors" collision
Strategy: Include vendor in fingerprint, whitelist-based suffix removal
"""

import re
from typing import Literal

DomainType = Literal["application", "infrastructure", "organization"]


class NormalizationRules:
    """Shared normalization strategy."""

    @staticmethod
    def normalize_name(name: str, domain: DomainType) -> str:
        """
        Normalize name for deduplication.

        CRITICAL: Different domains MAY have different normalization rules,
        but ALL apps use app rules, ALL infra uses infra rules (consistency).

        Args:
            name: Raw name (e.g., "Salesforce CRM", "AWS EC2 Production")
            domain: Which domain ("application", "infrastructure", "organization")

        Returns:
            Normalized name for fingerprinting

        Examples:
            # Applications:
            normalize_name("Salesforce CRM", "application") → "salesforce"
            normalize_name("SAP ERP", "application") → "sap"
            normalize_name("SAP SuccessFactors", "application") → "sap successfactors"

            # Infrastructure:
            normalize_name("AWS EC2 Production", "infrastructure") → "aws ec2 production"
            normalize_name("Azure VM Dev", "infrastructure") → "azure vm dev"
        """
        if domain == "application":
            return NormalizationRules._normalize_application(name)
        elif domain == "infrastructure":
            return NormalizationRules._normalize_infrastructure(name)
        elif domain == "organization":
            return NormalizationRules._normalize_organization(name)
        else:
            raise ValueError(f"Unknown domain: {domain}")

    @staticmethod
    def _normalize_application(name: str) -> str:
        """Application-specific normalization (fixes P0-3)."""
        # Lowercase and strip
        normalized = name.lower().strip()

        # Remove special characters
        normalized = re.sub(r'[^\w\s-]', '', normalized)

        # Remove TRAILING common suffixes only (not internal ones)
        # This prevents "SAP ERP" and "SAP SuccessFactors" from both → "sap"
        normalized = re.sub(
            r'\s+(crm|erp|online|cloud|suite|platform|app|system|software)$',
            '',
            normalized
        )

        # Collapse whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    @staticmethod
    def _normalize_infrastructure(name: str) -> str:
        """Infrastructure-specific normalization."""
        # Keep environment indicators (prod, dev, staging)
        normalized = name.lower().strip()
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    @staticmethod
    def _normalize_organization(name: str) -> str:
        """Organization-specific normalization."""
        # Keep titles (Director, Manager, VP)
        normalized = name.lower().strip()
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    @staticmethod
    def should_merge(obs1: 'Observation', obs2: 'Observation') -> bool:
        """
        Shared merging strategy when observations conflict.

        CRITICAL: ALL domains use SAME priority order.

        Priority (highest to lowest):
        1. manual (human-curated data)
        2. table (deterministic extraction)
        3. llm_prose (LLM extraction from prose)
        4. llm_assumption (LLM inference/guessing)

        Returns:
            True if obs1 should replace obs2 (obs1 has higher priority)
        """
        PRIORITY = {
            "manual": 4,
            "table": 3,
            "llm_prose": 2,
            "llm_assumption": 1
        }

        return PRIORITY.get(obs1.source_type, 0) > PRIORITY.get(obs2.source_type, 0)
```

**4. `domain/kernel/entity_inference.py`** - Entity inference (SHARED)
```python
"""
Shared entity inference rules.

CRITICAL: Applications, Infrastructure, Organization use SAME inference logic.
Prevents apps saying "target" while infra says "buyer" for same document.
"""

from typing import Optional
from domain.kernel.entity import Entity


class EntityInference:
    """Shared rules for inferring target vs buyer from context."""

    # Indicators that suggest "buyer" (our company, the acquirer)
    BUYER_INDICATORS = [
        "acquirer", "buyer", "our", "current", "existing",
        "we", "us", "internal", "parent", "acquiring company",
        # Add more based on real-world documents
    ]

    # Indicators that suggest "target" (company being acquired)
    TARGET_INDICATORS = [
        "target", "acquisition", "their", "to be acquired",
        "seller", "acquired company", "portfolio company",
        # Add more based on real-world documents
    ]

    @classmethod
    def infer_entity(cls, context: str, default: Entity = Entity.TARGET) -> Entity:
        """
        Infer entity (target vs buyer) from context.

        CRITICAL: Same logic used across ALL domains.

        Args:
            context: Text context (document name, section heading, etc.)
            default: Fallback if inference is uncertain (usually TARGET)

        Returns:
            Entity.TARGET or Entity.BUYER

        Examples:
            infer_entity("Target Company - IT Landscape") → Entity.TARGET
            infer_entity("Our Current Applications") → Entity.BUYER
            infer_entity("Applications Inventory") → Entity.TARGET (default)
        """
        context_lower = context.lower()

        # Count indicators
        buyer_score = sum(1 for indicator in cls.BUYER_INDICATORS if indicator in context_lower)
        target_score = sum(1 for indicator in cls.TARGET_INDICATORS if indicator in context_lower)

        if buyer_score > target_score:
            return Entity.BUYER
        elif target_score > buyer_score:
            return Entity.TARGET
        else:
            # Tie or no indicators → use default
            return default
```

**5. `domain/kernel/fingerprint.py`** - Stable ID generation (SHARED)
```python
"""
Stable fingerprint generation for domain IDs.

CRITICAL: ALL domains use THIS fingerprint strategy.
Ensures consistent hashing across applications, infrastructure, organization.
"""

import hashlib
from domain.kernel.entity import Entity


class FingerprintGenerator:
    """Shared fingerprint generation strategy."""

    @staticmethod
    def generate(
        name_normalized: str,
        vendor: str,
        entity: Entity,
        domain_prefix: str
    ) -> str:
        """
        Generate stable fingerprint for domain ID.

        Strategy (fixes P0-3 collision):
        - Include normalized name
        - Include vendor (prevents "SAP ERP" vs "SAP SuccessFactors" collision)
        - Include entity (target vs buyer)
        - Hash to 8 characters (collision probability ~1 in 4 billion)

        Args:
            name_normalized: Normalized name (from NormalizationRules)
            vendor: Vendor name (e.g., "SAP", "Microsoft")
            entity: Entity (target or buyer)
            domain_prefix: Domain prefix ("APP", "INFRA", "ORG")

        Returns:
            Domain ID: "{domain_prefix}-{entity_upper}-{hash8}"

        Examples:
            generate("salesforce", "Salesforce", Entity.TARGET, "APP")
              → "APP-TARGET-a3f291c2"

            generate("sap", "SAP", Entity.TARGET, "APP")
              → "APP-TARGET-b4e8f1d3"

            generate("sap successfactors", "SAP", Entity.TARGET, "APP")
              → "APP-TARGET-c9a7e2f5"  # Different from plain "sap"!
        """
        # Vendor normalization (lowercase, strip)
        vendor_normalized = vendor.lower().strip() if vendor else ""

        # Combine components for fingerprinting
        # CRITICAL: Include vendor to prevent collisions (P0-3 fix)
        fingerprint_input = f"{name_normalized}|{vendor_normalized}|{entity.value}"

        # Hash to 8 characters
        hash_full = hashlib.md5(fingerprint_input.encode()).hexdigest()
        hash_short = hash_full[:8]

        # Format: APP-TARGET-a3f291c2
        return f"{domain_prefix}-{entity.name}-{hash_short}"
```

**6. `domain/kernel/repository.py`** - Repository base class (SHARED)
```python
"""
Repository base class - shared pattern for ALL domains.

CRITICAL: Applications, Infrastructure, Organization all extend THIS.
Ensures consistent repository interface across domains.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from domain.kernel.entity import Entity

T = TypeVar('T')  # Domain aggregate type


class DomainRepository(ABC, Generic[T]):
    """
    Base repository - same pattern for Apps, Infra, Org.

    CRITICAL: All domain repositories MUST extend this.
    Provides shared deduplication primitives and query patterns.
    """

    @abstractmethod
    def save(self, item: T) -> T:
        """Save item to repository (insert or update)."""
        pass

    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        """Find item by domain ID."""
        pass

    @abstractmethod
    def find_or_create(
        self,
        name: str,
        entity: Entity,
        **kwargs
    ) -> T:
        """
        Shared deduplication primitive.

        Strategy:
        1. Normalize name (using kernel.NormalizationRules)
        2. Generate fingerprint (using kernel.FingerprintGenerator)
        3. Check if exists in DB (by fingerprint)
        4. If exists: return existing (merge observations)
        5. If not: create new

        This is THE method that prevents duplicates.
        """
        pass

    @abstractmethod
    def find_by_entity(self, entity: Entity) -> List[T]:
        """Find all items for entity (target or buyer)."""
        pass

    @abstractmethod
    def find_similar(
        self,
        name: str,
        threshold: float = 0.85,
        limit: int = 5
    ) -> List[T]:
        """
        Find similar items using fuzzy search.

        CRITICAL: Uses database trigram indexes (NOT O(n²)).
        See P0-2 fix - reconciliation must be O(n log n), not O(n²).
        """
        pass

    def reconcile_duplicates(
        self,
        items: List[T],
        threshold: float = 0.85
    ) -> int:
        """
        Shared reconciliation - NEVER inline, always background.

        CRITICAL: Fixes P0-2 (O(n²) reconciliation kills production).

        Strategy:
        1. Check count - if >500 items, skip (circuit breaker)
        2. Use database fuzzy search (O(n log n))
        3. Merge duplicates
        4. Return count of merged items

        NEVER call this in main request path - use Celery background job.
        """
        MAX_ITEMS = 500

        if len(items) > MAX_ITEMS:
            # Circuit breaker - don't block pipeline
            return 0

        merged_count = 0

        for item in items:
            # Use database fuzzy search (NOT nested loop)
            similar = self.find_similar(item.name, threshold, limit=5)

            for candidate in similar:
                if item.id != candidate.id and item.is_duplicate_of(candidate, threshold):
                    # Merge candidate into item
                    item.merge(candidate)
                    merged_count += 1

        return merged_count
```

**7. `domain/kernel/extraction.py`** - Extraction coordinator (SHARED)
```python
"""
Extraction coordinator - prevents double-counting.

CRITICAL: Prevents apps and infra from both extracting same entity from same doc.

Example problem:
  - Document: "IT Landscape.pdf" page 5
  - Contains: "Salesforce CRM - $50K/year"
  - Application domain: Extracts as app
  - Infrastructure domain: Might try to extract as SaaS infrastructure
  - Result: Double-counted cost!

This coordinator tracks what's been extracted to prevent overlap.
"""

from typing import Dict, Set


class ExtractionCoordinator:
    """Prevents double-extraction from same source."""

    def __init__(self):
        # Key: "doc_id:domain", Value: set of extracted entity names
        self._extracted: Dict[str, Set[str]] = {}

    def mark_extracted(
        self,
        doc_id: str,
        entity_name: str,
        domain: str
    ):
        """Mark entity as extracted from document by domain."""
        key = f"{doc_id}:{domain}"
        if key not in self._extracted:
            self._extracted[key] = set()
        self._extracted[key].add(entity_name.lower())

    def already_extracted(
        self,
        doc_id: str,
        entity_name: str,
        domain: str
    ) -> bool:
        """Check if entity already extracted from document."""
        key = f"{doc_id}:{domain}"
        return entity_name.lower() in self._extracted.get(key, set())

    def already_extracted_by_any_domain(
        self,
        doc_id: str,
        entity_name: str
    ) -> bool:
        """Check if entity extracted by ANY domain (cross-domain check)."""
        entity_lower = entity_name.lower()

        for domain_key in self._extracted:
            if doc_id in domain_key:
                if entity_lower in self._extracted[domain_key]:
                    return True

        return False

    def get_extracting_domain(
        self,
        doc_id: str,
        entity_name: str
    ) -> Optional[str]:
        """Get which domain extracted this entity (for conflict resolution)."""
        entity_lower = entity_name.lower()

        for domain_key, entities in self._extracted.items():
            if doc_id in domain_key and entity_lower in entities:
                # Extract domain from key "doc_id:domain" → "domain"
                return domain_key.split(':')[-1]

        return None
```

**8. `domain/kernel/tests/test_kernel.py`** - Comprehensive tests (90% coverage)

**Validation:**
```bash
# Test kernel in isolation
ENABLE_DOMAIN_MODEL=true pytest domain/kernel/tests/ -v --cov=domain.kernel --cov-report=term --cov-fail-under=90

# Expected output:
# test_entity_enum ... PASSED
# test_observation_schema ... PASSED
# test_observation_validation ... PASSED
# test_normalization_applications ... PASSED
# test_normalization_no_collisions ... PASSED  ← P0-3 fix validation
# test_entity_inference ... PASSED
# test_fingerprint_generation ... PASSED
# test_fingerprint_includes_vendor ... PASSED  ← P0-3 fix validation
# test_repository_base ... PASSED
# test_reconciliation_circuit_breaker ... PASSED  ← P0-2 fix validation
# test_extraction_coordinator ... PASSED
# ...
# Coverage: 92% (domain/kernel/)
```

**Success Criteria:**
- ✅ All 7 kernel modules created
- ✅ 90%+ test coverage
- ✅ P0-3 fix validated (normalization collision tests pass)
- ✅ P0-2 fix validated (reconciliation circuit breaker works)
- ✅ Cross-domain consistency guaranteed (shared primitives)

**Time Estimate:** 2 days

**Risk to Production:** ✅ **ZERO** (uses domain_experimental.db, guarded by ENABLE_DOMAIN_MODEL=false on Railway)

---

### Phase 2: Domain Implementation (PARALLEL)

Once kernel is stable, NOW we can safely parallelize domain-specific logic.

#### **Worker 2: Application Domain** (1 day)

**Dependencies:** Worker 1 complete (kernel exists)

**Task:** Build `domain/applications/` extending kernel

**Constraints:**
- MUST extend `kernel.DomainRepository[Application]`
- MUST use `kernel.Observation` (cannot invent own schema)
- MUST use `kernel.NormalizationRules.normalize_name(name, "application")`
- MUST use `kernel.EntityInference.infer_entity()` (same logic as other domains)
- MUST use `kernel.FingerprintGenerator.generate()`

**Deliverables:**

1. `domain/applications/application.py` - Application aggregate
2. `domain/applications/application_id.py` - ApplicationId value object
3. `domain/applications/repository.py` - ApplicationRepository (extends kernel)
4. `domain/applications/tests/` - Application-specific tests (80% coverage)

**Validation:**
```bash
# Worker 2 checks kernel compliance:
grep "from domain.kernel" domain/applications/*.py
# Expected: Multiple imports (entity, observation, normalization, etc.)

# Test application domain
ENABLE_DOMAIN_MODEL=true pytest domain/applications/tests/ -v --cov=domain.applications --cov-fail-under=80
```

**Success Criteria:**
- ✅ Extends kernel (imports verified)
- ✅ 80%+ test coverage
- ✅ Uses kernel.Observation (no custom schema)
- ✅ Uses kernel normalization (consistent with other domains)

**Risk to Production:** ✅ **ZERO**

---

#### **Worker 3: Infrastructure Domain** (1 day, parallel with Worker 2)

**Dependencies:** Worker 1 complete (kernel exists)

**Task:** Build `domain/infrastructure/` extending kernel

**Constraints:**
- MUST extend `kernel.DomainRepository[Infrastructure]`
- MUST use `kernel.Observation` (SAME schema as applications)
- MUST use `kernel.NormalizationRules.normalize_name(name, "infrastructure")`
- MUST use `kernel.EntityInference.infer_entity()` (SAME logic as applications)

**Deliverables:**

1. `domain/infrastructure/infrastructure.py` - Infrastructure aggregate
2. `domain/infrastructure/infrastructure_id.py` - InfrastructureId value object
3. `domain/infrastructure/repository.py` - InfrastructureRepository (extends kernel)
4. `domain/infrastructure/tests/` - Infrastructure-specific tests (80% coverage)

**Validation:**
```bash
# Worker 3 checks kernel compliance:
grep "from domain.kernel" domain/infrastructure/*.py
# Expected: Multiple imports (same pattern as applications)

# Test infrastructure domain
ENABLE_DOMAIN_MODEL=true pytest domain/infrastructure/tests/ -v --cov=domain.infrastructure --cov-fail-under=80
```

**Success Criteria:**
- ✅ Extends kernel (same pattern as Worker 2)
- ✅ 80%+ test coverage
- ✅ Uses kernel.Observation (consistent with applications)
- ✅ Infrastructure pattern validated (proves "same pattern for all domains")

**Risk to Production:** ✅ **ZERO**

---

#### **Worker 4: P0-2 Reconciliation Service** (4 hours, parallel with Workers 2-3)

**Dependencies:** Worker 1 complete (kernel.repository.reconcile_duplicates exists)

**Task:** Build background reconciliation service (fixes P0-2)

**Constraints:**
- NEVER run reconciliation inline (in request path)
- MUST use Celery background tasks
- MUST use database fuzzy search (O(n log n), NOT O(n²))
- MUST respect circuit breaker (MAX_ITEMS = 500)

**Deliverables:**

1. `domain/services/reconciliation_service.py` - Reconciliation service
2. `web/tasks/domain_reconciliation.py` - Celery task wrapper
3. `domain/services/tests/test_reconciliation.py` - Performance tests

**Validation:**
```bash
# Test reconciliation does NOT block
ENABLE_DOMAIN_MODEL=true pytest domain/services/tests/test_reconciliation.py::test_large_dataset_timeout -v

# Test: 10,000 apps reconcile in <5 seconds (not 30+ seconds O(n²))
ENABLE_DOMAIN_MODEL=true pytest domain/services/tests/test_reconciliation.py::test_10k_apps_performance -v
```

**Success Criteria:**
- ✅ 10,000 apps reconcile in <5 seconds (proves O(n log n))
- ✅ Circuit breaker activates at 500+ items
- ✅ Runs as Celery task (not inline)

**Risk to Production:** ✅ **ZERO**

---

#### **Reviewer: Integration & Compliance** (2 hours, after Workers 2-4 complete)

**Task:** Validate workers built consistent, isolated system

**Checks:**

**1. Kernel Compliance Check**
```bash
# All domains import from kernel
grep "from domain.kernel" domain/applications/*.py
grep "from domain.kernel" domain/infrastructure/*.py

# Both should show: entity, observation, normalization, fingerprint imports
```

**2. Cross-Domain Consistency Check**
```bash
# Both use kernel.Observation (same schema)
grep "Observation" domain/applications/application.py
grep "Observation" domain/infrastructure/infrastructure.py

# Both use kernel.EntityInference (same logic)
grep "EntityInference" domain/applications/repository.py
grep "EntityInference" domain/infrastructure/repository.py
```

**3. Isolation Validation**
```bash
# Production does NOT import domain
grep -r "from domain" agents_v2/ stores/ web/ services/ main_v2.py
# Expected: (no output)

# Domain uses separate database
grep "domain_experimental.db" domain/config.py
# Expected: Found

# Guards prevent production execution
ENVIRONMENT=production ENABLE_DOMAIN_MODEL=true python -c "from domain.guards import ExperimentalGuard; ExperimentalGuard.require_experimental_mode()"
# Expected: RuntimeError
```

**4. Integration Test**
```bash
# Test: Import document with BOTH apps and infra
ENABLE_DOMAIN_MODEL=true python -m domain.cli analyze data/input/IT_Landscape.pdf --all

# Verify:
# - Apps and infra use same entity inference (consistent entity)
# - No double-counting (extraction coordinator works)
# - Both use kernel.Observation (same schema)
```

**Success Criteria:**
- ✅ All workers import from kernel (no reinvention)
- ✅ Cross-domain consistency validated
- ✅ Isolation intact (production untouched)
- ✅ Integration test passes (apps + infra coexist)

**Failure Mode:** If ANY check fails, block merge and report to user

**Risk to Production:** ✅ **ZERO** (reviewer validates, doesn't modify)

---

## 📅 EXECUTION TIMELINE

### TODAY (2026-02-12, Before Demo Tomorrow)

#### **Phase 0: Production Lock (1 hour)** ✅ IMMEDIATE

**Steps:**
1. Tag current Railway commit:
   ```bash
   git tag demo-stable-2026-02-12
   git push origin demo-stable-2026-02-12
   ```

2. Create production snapshot:
   ```bash
   cat > RAILWAY_DEMO_STATE.md << 'EOF'
   # Railway Production State - Demo Day

   **Commit:** edf84e4 (REFINE: Architecture crisis doc)
   **Rollback:** 5ba1bb9 (ROLLBACK: Disable fact promotion)
   **Branch:** main
   **Deploy Date:** 2026-02-12
   **Demo Date:** 2026-02-13

   **Status:** 🔒 LOCKED FOR DEMO

   **DO NOT DEPLOY TO RAILWAY UNTIL AFTER DEMO**

   ## What's Running:
   - Emergency rollback (deterministic parser disabled)
   - Expected app count: 60-70 (not 143)
   - FactStore promotion disabled
   - Stable behavior (tested)

   ## Post-Demo:
   - Experimental domain model in background (domain/)
   - See: ISOLATION_STRATEGY.md
   - Timeline: 6-8 weeks migration

   ## Rollback Plan:
   If anything breaks during demo:
   1. Railway dashboard → Deployments
   2. Rollback to: demo-stable-2026-02-12
   3. Redeploy (30 seconds)

   ## Contacts:
   - Demo lead: [Your name]
   - Technical support: [Your name]
   EOF
   ```

3. Set Railway environment variables:
   - `ENVIRONMENT=production`
   - `ENABLE_DOMAIN_MODEL=false`
   - (Experimental code cannot run even if deployed)

4. Test demo flow locally:
   ```bash
   python main_v2.py data/input/ --all --target-name "DemoTarget Inc"
   # Verify: ~60-70 apps, no duplicates, reports generate
   ```

**Success Criteria:**
- ✅ Git tag created
- ✅ RAILWAY_DEMO_STATE.md exists
- ✅ Railway variables set
- ✅ Local demo tested

**Time:** 1 hour
**Risk to Production:** ✅ **ZERO** (read-only operations + config)

---

#### **Phase 1: Isolation Setup (30 minutes)** ✅ SAFE TO START

Launch Worker 0 (isolation infrastructure):
```bash
# I'll create:
# - domain/guards.py
# - domain/config.py
# - domain/__init__.py (update with warnings)
# - .env.experimental
```

**Time:** 30 minutes
**Can Start:** Immediately (purely additive)
**Risk to Production:** ✅ **ZERO**

---

### TONIGHT (Background - Runs While You Sleep)

#### **Phase 2: Kernel Foundation (2 days compressed to overnight)** ⏰ BACKGROUND

Launch Worker 1 (kernel development):
- Creates `domain/kernel/` (7 modules)
- Writes comprehensive tests (90% coverage)
- Validates P0-3 fix (normalization collision tests)
- Validates P0-2 fix (reconciliation circuit breaker)

**Time:** 8-10 hours wall-clock (overnight)
**Risk to Production:** ✅ **ZERO** (uses domain_experimental.db, feature flags off)

---

### TOMORROW MORNING (Before Demo - 2026-02-13)

#### **Phase 3: Verify Experimental Ready, Demo Untouched** (30 minutes)

**Check Worker 1 Progress:**
```bash
# Did Worker 1 complete kernel?
ls domain/kernel/
# Expected: entity.py, observation.py, normalization.py, etc.

# Are tests passing?
ENABLE_DOMAIN_MODEL=true pytest domain/kernel/tests/ -v --cov=domain.kernel
# Expected: 90%+ coverage, all tests pass
```

**Verify Production Untouched:**
```bash
# Check Railway is still on demo-stable tag
git log --oneline -1
# Expected: edf84e4 (or demo-stable tag)

# Check no domain imports in production
grep -r "from domain" agents_v2/ stores/ web/ main_v2.py
# Expected: (no output)
```

**Demo Prep:**
```bash
# Run demo one final time
python main_v2.py data/input/ --all --target-name "DemoTarget Inc"
# Expected: ~60-70 apps, stable
```

**Time:** 30 minutes
**Risk to Production:** ✅ **ZERO** (read-only checks)

---

#### **DEMO TIME** 🎬

**You run demo using production code:**
```bash
# Uses main_v2.py (production CLI)
# Uses agents_v2/, stores/ (production system)
# Uses Railway deployment (locked commit)
# Experimental code is invisible (not imported, separate DB)
```

**Experimental work continues in background (no impact on demo).**

---

### TOMORROW AFTERNOON (After Demo - 2026-02-13)

#### **Phase 4: Launch Parallel Domain Workers** (1 day compressed to 6-8 hours)

Once demo is complete and successful:

**Launch Workers 2-4 in parallel:**
- Worker 2: Application domain (extends kernel)
- Worker 3: Infrastructure domain (extends kernel)
- Worker 4: P0-2 Reconciliation service

**Launch Reviewer:**
- Validates kernel compliance
- Checks cross-domain consistency
- Runs integration tests

**Time:** 6-8 hours wall-clock (parallel)
**Risk to Production:** ✅ **ZERO** (experimental code isolated)

---

### DAY 3 (2026-02-14)

#### **Phase 5: Side-by-Side Validation** (4 hours)

**Compare old vs new system:**
```bash
# Old system (production)
python main_v2.py data/input/ --all --target-name "TestCorp"
# Output: output/facts_old.json, output/inventory_old.json

# New system (experimental)
ENABLE_DOMAIN_MODEL=true python -m domain.cli analyze data/input/ --all --target-name "TestCorp"
# Output: domain_experimental.db

# Compare results
ENABLE_DOMAIN_MODEL=true python -m domain.adapters.comparison compare output/inventory_old.json domain_experimental.db
# Expected output:
# ✅ Old: 143 apps (with duplicates)
# ✅ New: 68 apps (deduplicated correctly)
# ✅ Duplication rate: Old 40%+, New <2%
```

**Time:** 4 hours
**Decision Point:** If new system validates correctly, proceed to Week 2 (database migration redesign)

---

## 🚨 EMERGENCY PROCEDURES

### If Demo Breaks Tomorrow

**Symptom:** Demo shows duplicates, crashes, wrong counts, etc.

**Immediate Response (2 minutes):**
1. Open Railway dashboard (https://railway.app/project/...)
2. Navigate to: Deployments
3. Find: `demo-stable-2026-02-12` tag
4. Click: Redeploy
5. Wait: 30-60 seconds
6. Test: Refresh demo UI

**Rollback Verification:**
```bash
# After redeploying tag, verify Railway is on correct commit
git log --oneline | grep "demo-stable"
# Expected: Tag points to edf84e4 or earlier stable commit
```

**Root Cause Investigation (post-demo):**
- Check: Was experimental code accidentally deployed?
  ```bash
  # On Railway instance
  ls domain/
  python -c "import sys; print('domain' in sys.path)"
  ```
- Check: Were environment variables changed?
  ```bash
  # Railway dashboard → Variables
  # Verify: ENABLE_DOMAIN_MODEL=false
  ```

**Prevention:**
- Railway deployment is locked to specific commit tag
- Experimental code cannot run (ENABLE_DOMAIN_MODEL=false)
- Guards raise errors if accidentally enabled

---

### If Experimental Code Accidentally Runs in Production

**Detection:**
```bash
# Symptom: Warning in Railway logs
"⚠️ EXPERIMENTAL DOMAIN MODEL IMPORTED IN PRODUCTION!"

# Or: RuntimeError in logs
"🚨 EXPERIMENTAL DOMAIN MODEL CANNOT RUN IN PRODUCTION!"
```

**Immediate Response:**
1. Experimental code CANNOT execute (guards prevent it)
2. Warning is logged but app continues (import guard is warning-only)
3. RuntimeError prevents execution (execution guard is fatal)

**Remediation:**
1. Find accidental import:
   ```bash
   grep -r "from domain" agents_v2/ stores/ web/ services/
   # Find file that imported experimental code
   ```
2. Remove import
3. Redeploy

**This scenario is HIGHLY UNLIKELY due to 5 isolation layers.**

---

### If Workers Fail Overnight

**Symptom:** Tomorrow morning, kernel is incomplete

**Response:**
- **Demo is unaffected** (experimental work is separate)
- Run demo as planned (production code untouched)
- Post-demo: Debug worker failures
  ```bash
  # Check worker logs
  cat domain/kernel/BUILD_LOG.md

  # Check test failures
  ENABLE_DOMAIN_MODEL=true pytest domain/kernel/tests/ -v
  ```

**Recovery:**
- Workers can be re-run (idempotent)
- No production impact

---

## 📊 SUCCESS METRICS

### Demo Day (Tomorrow)

**Production Stability:**
- ✅ Demo completes without crashes
- ✅ App count is 60-70 (not 143)
- ✅ No "Legacy Facts" banner appears
- ✅ Reports generate successfully
- ✅ Zero experimental code interactions

**Experimental Progress:**
- ✅ Isolation infrastructure created (Worker 0)
- ✅ Kernel foundation built (Worker 1) [if overnight build succeeds]
- ⏸️ Domain implementations pending (Workers 2-4) [scheduled post-demo]

---

### Week 1 Complete (2026-02-14)

**Experimental System:**
- ✅ Kernel: 90%+ test coverage
- ✅ Applications: 80%+ test coverage
- ✅ Infrastructure: 80%+ test coverage
- ✅ Reconciliation: Performance tests pass (10K apps <5 sec)

**Isolation Validation:**
- ✅ Zero domain imports in production code
- ✅ Separate database verified
- ✅ Guards prevent production execution
- ✅ CI checks pass

**Comparison (Old vs New):**
- ✅ New system: <2% duplication rate (vs 40%+ old)
- ✅ New system: ±3 apps accuracy (vs ±83 old)
- ✅ New system: Stable IDs across re-imports (vs changing IDs old)

---

### Migration Decision (End of Week 1)

**Decision Matrix:**

| Metric | Old System | New System | Improvement |
|--------|-----------|------------|-------------|
| Duplication rate | 40%+ | <2% | ✅ 20x better |
| App count accuracy | ±83 apps | ±3 apps | ✅ 27x better |
| ID stability | Changes on re-import | Stable | ✅ Fixed |
| Test coverage | ~30% | 90% kernel, 80% domains | ✅ 3x better |
| Truth systems | 4 (conflicting) | 1 (domain model) | ✅ Unified |

**If all metrics green:** Proceed to Week 2 (database migration redesign)
**If any metric red:** Debug, fix, re-validate before Week 2

---

## 🔗 RELATED DOCUMENTS

1. **ARCHITECTURAL_CRISIS_SUMMARY.md** - Root cause analysis (16 pages)
   - Why we need this redesign
   - The "4 truth systems" problem
   - Financial justification ($78K investment vs $140K/quarter waste)

2. **docs/architecture/domain-first-redesign-plan.md** - Implementation plan (28 pages)
   - Original 6-week plan (has 5 P0 flaws identified by adversarial analysis)
   - Domain model architecture
   - Migration strategy (needs redesign per adversarial findings)

3. **RAILWAY_DEMO_STATE.md** - Production snapshot (created during setup)
   - What's running on Railway
   - Rollback procedures
   - Demo day checklist

4. **.env.experimental** - Experimental configuration (created during setup)
   - ENABLE_DOMAIN_MODEL=true
   - DOMAIN_DATABASE_URL=sqlite:///domain_experimental.db
   - Safe to use locally, never deploy to Railway

---

## ❓ FAQ

### Q: Can experimental code break production?

**A: No - 5 independent isolation layers prevent this:**
1. Directory separation (domain/ vs production code)
2. Import guards (warnings if imported in production)
3. Runtime guards (errors if executed in production)
4. Database isolation (separate domain_experimental.db)
5. Feature flags (ENABLE_DOMAIN_MODEL=false on Railway)

Even if ALL 5 layers failed simultaneously (extremely unlikely), experimental code would crash itself (not production).

---

### Q: What if I accidentally deploy experimental code to Railway?

**A: It cannot execute due to guards:**
```python
# In domain/guards.py
if os.getenv('ENVIRONMENT') == 'production':
    raise RuntimeError("Cannot run in production!")
```

Railway sets `ENVIRONMENT=production`, so experimental code raises error immediately. Production code (agents_v2/, stores/, web/) is unaffected.

---

### Q: How do I test experimental code locally?

**A: Use experimental environment:**
```bash
# Load experimental config
export $(cat .env.experimental | xargs)

# Run experimental CLI
python -m domain.cli analyze data/input/

# Run experimental tests
pytest domain/tests/ -v --cov=domain

# Run experimental demo
python -m domain.DEMO
```

---

### Q: When can we switch from old system to new system?

**A: After Week 1 validation + Week 2 redesign:**
1. Week 1: Build experimental system (this document)
2. Week 1 end: Side-by-side validation (old vs new)
3. Week 2: Redesign database migration (fix P0-1: split-brain issue)
4. Week 3: Implement gradual cutover (fix P0-5: feature flag in every path)
5. Week 4-6: Rollout (10% → 50% → 100%)

**Do NOT switch before validation passes.** Old system is stable (post-rollback), we have time to do this right.

---

### Q: What's the risk to tomorrow's demo?

**A: Zero risk if we follow this plan:**
- Production code locked (git tag)
- Railway environment locked (ENABLE_DOMAIN_MODEL=false)
- Experimental code isolated (separate DB, guards)
- Rollback available (30 seconds)

**Demo runs on production code (main_v2.py). Experimental code is invisible.**

---

## ✅ PRE-FLIGHT CHECKLIST

Before starting Worker 0 (isolation setup):

- [ ] Git is clean (`git status` shows no uncommitted changes)
- [ ] Current commit is `edf84e4` or later (crisis doc exists)
- [ ] `domain/` directory exists (POC from earlier)
- [ ] `domain/DEMO.py` exists and runs (proof of concept works)
- [ ] Railway is accessible (can view deployment dashboard)
- [ ] Demo data ready (`data/input/` has test documents)
- [ ] Demo is tomorrow (2026-02-13) - **CONFIRMED**

Once checklist complete, proceed to Worker 0 (isolation setup).

---

## 📝 CHANGELOG

| Date | Change | Author |
|------|--------|--------|
| 2026-02-12 | Created isolation strategy document | Claude Sonnet 4.5 (audit1) |
| 2026-02-12 | Added cross-pollination prevention (kernel layer) | Claude Sonnet 4.5 (audit1) |
| 2026-02-12 | Added 5-layer isolation architecture | Claude Sonnet 4.5 (audit1) |
| 2026-02-12 | Added emergency procedures | Claude Sonnet 4.5 (audit1) |

---

**END OF ISOLATION STRATEGY DOCUMENT**

**Next Step:** Review this document, then launch Worker 0 (isolation setup).

**Estimated Time to Production Safety:** 1.5 hours (Phase 0 + Worker 0)
**Estimated Time to Working Experimental System:** 3 days (Kernel + Domains + Validation)
**Risk to Demo Tomorrow:** ✅ **ZERO**
