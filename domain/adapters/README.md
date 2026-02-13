# Domain Adapters - Integration Layer

**Status:** ✅ Complete
**Tests:** 13/13 PASSING (100%)
**Created:** 2026-02-12

---

## Overview

This package bridges the **new domain model** (Workers 1-3: kernel, applications, infrastructure) with the **existing production systems** (FactStore, InventoryStore).

Without these adapters, the domain model would be completely isolated and unusable in production.

---

## Architecture

```
Production Pipeline (OLD):
  Document → FactStore → InventoryStore → Web UI

Integration Pipeline (NEW):
  Document → FactStore → [ADAPTERS] → Domain Model → [ADAPTERS] → InventoryStore → Web UI
                           ↑                                        ↑
                    FactStoreAdapter                      InventoryAdapter
```

---

## Components

### 1. FactStoreAdapter (`fact_store_adapter.py`)

**Purpose:** Reads production FactStore → Converts to Domain Model

**Responsibilities:**
- Reads Facts from production FactStore
- Converts Facts to domain Observations
- Groups observations by entity (app/infrastructure)
- Uses domain repositories for deduplication
- Returns domain aggregates (Application, Infrastructure)

**Example:**
```python
from domain.adapters import FactStoreAdapter
from stores.fact_store import FactStore
from domain.applications.repository import ApplicationRepository

fact_store = FactStore(deal_id="deal-123")
adapter = FactStoreAdapter()
repo = ApplicationRepository()

# Load applications from facts
applications = adapter.load_applications(fact_store, repo)
# Result: List[Application] with deduplication applied
```

**Key Methods:**
- `load_applications(fact_store, repository, entity_filter=None)` → List[Application]
- `load_infrastructure(fact_store, repository, entity_filter=None)` → List[Infrastructure]

---

### 2. InventoryAdapter (`inventory_adapter.py`)

**Purpose:** Writes Domain Model → Production InventoryStore (for UI)

**Responsibilities:**
- Converts domain aggregates to InventoryItems
- Writes to production InventoryStore
- Handles entity conversion (Entity enum → string)
- Preserves observation priorities (manual > table > LLM)
- Tracks source_fact_ids for bidirectional linking

**Example:**
```python
from domain.adapters import InventoryAdapter
from stores.inventory_store import InventoryStore

adapter = InventoryAdapter()
inventory = InventoryStore(deal_id="deal-123")

# Sync applications to inventory (makes them visible in UI)
adapter.sync_applications(applications, inventory)

# Now web UI can display these applications
```

**Key Methods:**
- `sync_applications(applications, inventory_store, source_fact_ids=None)` → List[str]
- `sync_infrastructure(infrastructures, inventory_store, source_fact_ids=None)` → List[str]

---

### 3. ComparisonTool (`comparison.py`)

**Purpose:** Validates old system vs new system outputs match

**Responsibilities:**
- Runs both old and new systems side-by-side
- Compares counts (application, infrastructure, by entity)
- Validates no data loss
- Validates entity separation maintained
- Generates comparison report

**Example:**
```python
from domain.adapters import ComparisonTool

tool = ComparisonTool()
result = tool.compare(
    fact_store=fact_store,
    old_inventory=old_inventory_store,
    deal_id="deal-123"
)

result.print_summary()

if not result.passed:
    print("Differences found! Review before cutover.")
```

**Key Methods:**
- `compare(fact_store, old_inventory, deal_id, tolerance=0.05)` → ComparisonResult
- `quick_check(fact_store, deal_id)` → Dict[str, int]

---

## Integration Tests

**Location:** `domain/adapters/tests/test_adapters.py`

**Coverage:** 13 comprehensive tests

### Test Categories

#### 1. FactStoreAdapter Tests (5 tests)
- ✅ `test_load_applications_basic` - Basic fact → application conversion
- ✅ `test_load_applications_deduplication` - Deduplication working
- ✅ `test_load_applications_entity_separation` - Target vs buyer isolation
- ✅ `test_load_infrastructure_vendor_none` - vendor=None support
- ✅ `test_adapter_stats` - Statistics tracking

#### 2. InventoryAdapter Tests (3 tests)
- ✅ `test_sync_applications_basic` - Basic domain → inventory sync
- ✅ `test_sync_preserves_observations` - Observation priority preserved
- ✅ `test_adapter_stats` - Statistics tracking

#### 3. Round-Trip Tests (2 tests)
- ✅ `test_application_round_trip` - Full pipeline: Fact → Domain → Inventory
- ✅ `test_infrastructure_round_trip` - Full infrastructure pipeline

#### 4. ComparisonTool Tests (2 tests)
- ✅ `test_comparison_same_counts` - Validates count matching
- ✅ `test_quick_check` - Quick validation

#### 5. Entity Separation Tests (1 test)
- ✅ `test_entity_not_contaminated` - Target/buyer isolation maintained

**Run tests:**
```bash
pytest domain/adapters/tests/test_adapters.py -v
```

---

## Usage Example: Full Pipeline

```python
from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from domain.applications.repository import ApplicationRepository
from domain.infrastructure.repository import InfrastructureRepository
from domain.adapters import FactStoreAdapter, InventoryAdapter, ComparisonTool

# Step 1: Load facts from production
fact_store = FactStore(deal_id="deal-123")
# (facts populated by document parsing pipeline)

# Step 2: Convert to domain model
fact_adapter = FactStoreAdapter()

app_repo = ApplicationRepository()
infra_repo = InfrastructureRepository()

applications = fact_adapter.load_applications(fact_store, app_repo)
infrastructures = fact_adapter.load_infrastructure(fact_store, infra_repo)

print(f"Loaded {len(applications)} applications, {len(infrastructures)} infrastructure")

# Step 3: Sync to inventory for UI
inv_adapter = InventoryAdapter()
inventory = InventoryStore(deal_id="deal-123")

inv_adapter.sync_applications(applications, inventory)
inv_adapter.sync_infrastructure(infrastructures, inventory)

print(f"Synced to inventory - now visible in web UI")

# Step 4: Validate against old system
comparison = ComparisonTool()
result = comparison.compare(fact_store, old_inventory, "deal-123")

result.print_summary()

if result.passed:
    print("✅ New system matches old system - safe to proceed!")
else:
    print("❌ Differences found - review before cutover")
```

---

## Data Flow Details

### Fact → Observation Conversion

**FactStore Fact:**
```python
Fact(
    fact_id="F-APP-001",
    domain="applications",
    category="saas",
    item="Salesforce",
    details={"vendor": "Salesforce", "cost": 50000},
    entity="target",
    deal_id="deal-123",
    evidence={"exact_quote": "Page 5: Salesforce CRM"}
)
```

**Converts to Domain Observation:**
```python
Observation(
    source_type="table",  # Mapped from category
    confidence=0.9,
    evidence="Page 5: Salesforce CRM",
    extracted_at=datetime.now(),
    deal_id="deal-123",
    entity=Entity.TARGET,
    data={"vendor": "Salesforce", "cost": 50000}
)
```

### Application → InventoryItem Conversion

**Domain Application:**
```python
Application(
    id="APP-TARGET-a3f291c2",
    name="Salesforce",
    vendor="Salesforce",
    entity=Entity.TARGET,
    deal_id="deal-123",
    observations=[obs1, obs2, obs3]
)
```

**Converts to InventoryItem:**
```python
InventoryItem(
    item_id="I-APP-xyz123",  # Generated by InventoryStore
    inventory_type="application",
    entity="target",
    deal_id="deal-123",
    data={
        "name": "Salesforce",
        "vendor": "Salesforce",
        "domain_id": "APP-TARGET-a3f291c2",  # Reverse lookup
        "cost": 50000,  # From highest priority observation
        "observation_count": 3,
        "confidence": 0.95
    }
)
```

---

## Statistics Tracking

Both adapters track statistics for monitoring:

**FactStoreAdapter stats:**
```python
{
    "facts_processed": 150,
    "applications_created": 45,
    "infrastructure_created": 32,
    "observations_converted": 150,
    "duplicates_merged": 8
}
```

**InventoryAdapter stats:**
```python
{
    "applications_synced": 45,
    "infrastructure_synced": 32,
    "items_added": 77,
    "items_updated": 0
}
```

---

## Production Readiness

| Criterion | Status |
|-----------|--------|
| Tests passing | ✅ 13/13 (100%) |
| Code quality | ✅ Production-ready |
| Documentation | ✅ Complete |
| Data integrity | ✅ Validated (round-trip tests) |
| Entity separation | ✅ Maintained |
| Deduplication | ✅ Working |
| Performance | ✅ In-memory (fast) |

**Ready for:**
- ✅ Integration into main_v2.py pipeline
- ✅ Production deployment (after Worker 4)
- ✅ Dual-write strategy (old + new systems)

---

## Next Steps

1. **Wire into Pipeline** - Integrate adapters into `main_v2.py`
2. **Build Worker 4** - Organization domain (complete the domain model)
3. **End-to-End Testing** - Test full pipeline with real data
4. **Production Cutover** - Dual-write → Validate → Switch reads → Remove old

---

**Created:** 2026-02-12
**Integration Layer Complete:** 3 adapters, 13 tests, 100% passing
