# Deal ID Propagation Audit & Fix

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document specifies how to audit the inventory item creation pipeline to identify where `deal_id` is not being propagated, and how to fix it to ensure multi-tenant data isolation.

**Purpose:** Eliminate "InventoryItem created without deal_id" warnings by ensuring deal_id propagates through the entire discovery → inventory creation pipeline.

**Scope:** Audit deterministic parser, bridge services, discovery agents; fix deal_id propagation gaps; add validation to prevent future regressions.

**Problem Solved:** Currently, 35+ inventory items are being created without `deal_id`, breaking multi-tenant isolation. Cost queries may return items from wrong deals, contaminating totals.

---

## Architecture

### Current State (Broken deal_id Propagation)

```
Discovery Pipeline:
    Document Upload
        ↓
    PDF/DOCX Parsing
        ↓
    Deterministic Parser (table extraction)
        ↓ (deal_id LOST HERE?)
    Discovery Agents (LLM extraction)
        ↓ (deal_id LOST HERE?)
    Bridge Services (applications_bridge.py, organization_bridge.py)
        ↓ (deal_id LOST HERE?)
    InventoryStore.add_item()
        ↓
    InventoryItem created WITHOUT deal_id ❌
```

**Evidence from Flask logs:**
```
InventoryItem I-APP-b79922 created without deal_id - data isolation may be compromised
InventoryItem I-APP-d918ca created without deal_id - data isolation may be compromised
... (35 total warnings)
```

---

### Target State (deal_id Propagated)

```
Discovery Pipeline:
    Document Upload (deal_id assigned)
        ↓ [deal_id]
    PDF/DOCX Parsing
        ↓ [deal_id]
    Deterministic Parser (table extraction, deal_id preserved)
        ↓ [deal_id]
    Discovery Agents (facts have deal_id)
        ↓ [deal_id]
    Bridge Services (read deal_id from facts, pass to inventory)
        ↓ [deal_id]
    InventoryStore.add_item(deal_id=...)
        ↓
    InventoryItem created WITH deal_id ✅
```

**Benefit:** Multi-tenant isolation enforced. Cost queries filter by deal_id, preventing cross-deal contamination.

---

## Specification

### Phase 1: Audit - Identify Breakage Points

**Objective:** Trace inventory item creation to find where deal_id is dropped.

#### 1.1 Check Deterministic Parser

**File:** `tools_v2/deterministic_parser.py`

**Questions:**
- Does `parse_application_tables()` accept deal_id parameter?
- Does `parse_organization_tables()` accept deal_id parameter?
- Do parsed results include deal_id field?

**Expected Findings:**
- Parser likely creates dicts without deal_id field
- Parser doesn't know about deal_id (operates on raw text)

**Action:** Deterministic parser should NOT be modified (it's text → structured data, no deal context). deal_id must be added downstream by bridge services.

---

#### 1.2 Check Discovery Agents

**Files:** `agents_v2/discovery/*.py`

**Questions:**
- Do discovery agents create facts with deal_id?
- Does FactStore.add_fact() require deal_id?

**Expected Findings:**
- Facts HAVE deal_id (from audit B1, entity separation work)
- Facts are properly scoped by deal

**Action:** Discovery agents are likely OK. Focus on bridge services.

---

#### 1.3 Check Bridge Services (PRIMARY SUSPECTS)

**Files:**
- `services/applications_bridge.py`
- `services/organization_bridge.py`
- `services/infrastructure_bridge.py` (if exists)

**Questions:**
- Do bridges read deal_id from facts?
- Do bridges pass deal_id when calling `InventoryStore.add_item()`?

**Audit Method:**

```python
# Search for add_item calls
grep -n "add_item" services/*_bridge.py

# Check if deal_id is in the call
grep -A5 "add_item" services/applications_bridge.py | grep "deal_id"
```

**Expected Findings:**
- Bridges call `inv_store.add_item()` WITHOUT deal_id parameter
- Bridges have access to deal_id (from fact.deal_id) but don't use it

**Root Cause Hypothesis:** Bridges were written before multi-tenant support. deal_id parameter not added to add_item() calls.

---

#### 1.4 Check InventoryStore.add_item() Signature

**File:** `stores/inventory_store.py`

**Questions:**
- Does `add_item()` accept deal_id parameter?
- Is deal_id required or optional?
- What happens if deal_id is None?

**Audit Method:**

```python
def add_item(
    self,
    inventory_type: str,
    name: str,
    data: Dict[str, Any],
    deal_id: Optional[str] = None,  # ← Check if this exists
    entity: Optional[str] = None,
    source_fact_ids: Optional[List[str]] = None,
    # ...
) -> InventoryItem:
```

**Expected Findings:**
- add_item() accepts deal_id but it's optional
- If deal_id is None, warning is logged (the warnings we're seeing)
- InventoryItem is created anyway (with deal_id=None)

**Action:** Enforce deal_id as required (or at minimum, make bridges pass it).

---

### Phase 2: Fix - Propagate deal_id Through Bridges

**Objective:** Ensure all bridge services pass deal_id when creating inventory items.

#### 2.1 Fix applications_bridge.py

**File:** `services/applications_bridge.py`

**Current (Suspected):**
```python
def create_inventory_from_facts(fact_store: FactStore, inv_store: InventoryStore):
    """Create inventory items from application facts."""

    app_facts = fact_store.get_facts_by_domain("applications")

    for fact in app_facts:
        # Extract application data
        app_data = {
            "name": fact.item,
            "category": fact.category,
            "cost": fact.details.get("annual_cost", 0),
            # ...
        }

        # Add to inventory WITHOUT deal_id
        inv_store.add_item(
            inventory_type="application",
            name=fact.item,
            data=app_data,
            entity=fact.entity,
            source_fact_ids=[fact.id],
            # deal_id=??? MISSING!
        )
```

**Target (Fixed):**
```python
def create_inventory_from_facts(fact_store: FactStore, inv_store: InventoryStore):
    """Create inventory items from application facts."""

    app_facts = fact_store.get_facts_by_domain("applications")

    for fact in app_facts:
        # Extract deal_id from fact
        deal_id = getattr(fact, 'deal_id', None)

        if not deal_id:
            logger.warning(f"Fact {fact.id} has no deal_id, skipping inventory creation")
            continue

        # Extract application data
        app_data = {
            "name": fact.item,
            "category": fact.category,
            "cost": fact.details.get("annual_cost", 0),
            # ...
        }

        # Add to inventory WITH deal_id
        inv_store.add_item(
            inventory_type="application",
            name=fact.item,
            data=app_data,
            deal_id=deal_id,  # ← FIX: Pass deal_id from fact
            entity=fact.entity,
            source_fact_ids=[fact.id],
        )
```

**Key Changes:**
1. Extract `deal_id` from fact before creating inventory item
2. Skip fact if deal_id is missing (with warning)
3. Pass `deal_id=deal_id` to add_item() call

---

#### 2.2 Fix organization_bridge.py

**File:** `services/organization_bridge.py`

**Same pattern as applications_bridge:**

```python
def create_organization_inventory(fact_store: FactStore, inv_store: InventoryStore):
    """Create organization inventory from facts."""

    org_facts = fact_store.get_facts_by_domain("organization")

    for fact in org_facts:
        deal_id = getattr(fact, 'deal_id', None)

        if not deal_id:
            logger.warning(f"Org fact {fact.id} has no deal_id, skipping")
            continue

        # Create inventory item
        inv_store.add_item(
            inventory_type="organization",
            name=fact.item,
            data={...},
            deal_id=deal_id,  # ← FIX
            entity=fact.entity,
            source_fact_ids=[fact.id],
        )
```

---

#### 2.3 Fix infrastructure_bridge.py (if exists)

**Check if file exists:**
```bash
ls -la services/infrastructure_bridge.py
```

If exists, apply same fix pattern.

---

#### 2.4 Check Other Bridge Services

**Audit all bridge files:**
```bash
find services/ -name "*_bridge.py" -type f
```

For each bridge:
1. Search for `add_item()` calls
2. Verify deal_id is passed
3. Add if missing

---

### Phase 3: Validation - Enforce deal_id Requirement

**Objective:** Make it impossible to create inventory items without deal_id.

#### 3.1 Add InventoryStore Validation

**File:** `stores/inventory_store.py`

**Current add_item() (suspected):**
```python
def add_item(
    self,
    inventory_type: str,
    name: str,
    data: Dict[str, Any],
    deal_id: Optional[str] = None,
    entity: Optional[str] = None,
    source_fact_ids: Optional[List[str]] = None,
) -> InventoryItem:
    """Add an item to inventory."""

    if not deal_id:
        logger.warning(f"InventoryItem {name} created without deal_id - data isolation may be compromised")
        # But still creates item! ❌
```

**Target (Strict Validation):**
```python
def add_item(
    self,
    inventory_type: str,
    name: str,
    data: Dict[str, Any],
    deal_id: str,  # ← Make required (remove Optional)
    entity: Optional[str] = None,
    source_fact_ids: Optional[List[str]] = None,
) -> InventoryItem:
    """Add an item to inventory.

    Args:
        deal_id: Required. Deal ID for multi-tenant isolation.

    Raises:
        ValueError: If deal_id is None or empty string
    """

    # Strict validation
    if not deal_id:
        raise ValueError(
            f"deal_id is required for inventory item creation. "
            f"Cannot create {inventory_type} '{name}' without deal_id. "
            f"This violates multi-tenant data isolation."
        )

    # [Rest of method unchanged]
```

**Key Changes:**
1. Remove `Optional` from deal_id type hint (make required)
2. Raise ValueError if deal_id is missing (not just warning)
3. Update docstring to indicate deal_id is required

**Breaking Change:** Yes — any code calling add_item() without deal_id will now error (which is good — forces fix).

---

#### 3.2 Add Database Constraint

**File:** `web/database.py` (InventoryItem model)

**Check current schema:**
```python
class InventoryItem(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    deal_id = db.Column(db.String(50), nullable=True)  # ← Check if True
    # ...
```

**Target (Enforce NOT NULL):**
```python
class InventoryItem(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    deal_id = db.Column(db.String(50), nullable=False)  # ← Change to False
    # ...
```

**Migration Required:**
```python
# alembic migration
def upgrade():
    # Backfill any existing items without deal_id
    op.execute("UPDATE inventory_items SET deal_id = 'unknown' WHERE deal_id IS NULL")

    # Add NOT NULL constraint
    op.alter_column('inventory_items', 'deal_id', nullable=False)

def downgrade():
    op.alter_column('inventory_items', 'deal_id', nullable=True)
```

**Note:** Only apply this if InventoryItem is persisted to database (check if web/database.py has InventoryItem model).

---

### Phase 4: Testing - Verify Zero Warnings

**Objective:** Confirm no more "created without deal_id" warnings.

#### 4.1 Integration Test

**File:** `tests/integration/test_deal_id_propagation.py` (NEW)

```python
import pytest
from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from services.applications_bridge import create_inventory_from_facts

def test_inventory_items_have_deal_id():
    """Inventory items created from facts have deal_id."""

    # Create fact store with deal_id
    fact_store = FactStore(deal_id="test-deal-123")

    # Add application fact
    fact_store.add_fact(
        domain="applications",
        category="crm",
        item="Salesforce",
        details={"annual_cost": 500000},
        entity="target",
        source_document="doc1.pdf",
    )

    # Create inventory
    inv_store = InventoryStore()
    create_inventory_from_facts(fact_store, inv_store)

    # Verify inventory item has deal_id
    apps = inv_store.get_items(inventory_type="application")
    assert len(apps) == 1
    assert apps[0].deal_id == "test-deal-123"  # Must have deal_id
```

**Expected:** Test passes, inventory item has deal_id.

---

#### 4.2 Manual Verification

**Scenario 1: Run Full Discovery Pipeline**

1. Upload documents to test deal
2. Run discovery: `python main_v2.py data/input/ --all --target-name "TestDeal"`
3. Monitor Flask logs for warnings
4. **Expected:** ZERO "created without deal_id" warnings

**Scenario 2: Check Inventory Store**

```python
# In Flask shell
from web.blueprints.inventory import get_inventory_store

inv_store = get_inventory_store()
items = inv_store.get_all_items()

# Check all items have deal_id
missing_deal_id = [item for item in items if not item.deal_id]
print(f"Items without deal_id: {len(missing_deal_id)}")
# Expected: 0
```

---

#### 4.3 Error Case Test

**Verify strict validation works:**

```python
def test_add_item_without_deal_id_raises_error():
    """Adding item without deal_id raises ValueError."""
    inv_store = InventoryStore()

    with pytest.raises(ValueError, match="deal_id is required"):
        inv_store.add_item(
            inventory_type="application",
            name="TestApp",
            data={},
            deal_id=None,  # Missing deal_id
            entity="target",
        )
```

**Expected:** Test passes, ValueError raised.

---

## Verification Strategy

### Audit Checklist

**Before fixes:**
- [ ] Identify all bridge services that create inventory items
- [ ] Check each bridge for deal_id propagation
- [ ] Confirm InventoryStore.add_item() signature
- [ ] Count current "created without deal_id" warnings (baseline)

**After fixes:**
- [ ] All bridge services pass deal_id to add_item()
- [ ] InventoryStore.add_item() enforces deal_id requirement
- [ ] Integration tests pass
- [ ] Manual verification shows zero warnings
- [ ] Database constraint added (if applicable)

---

### Root Cause Confirmation

**Expected root causes (verify during audit):**

1. **Bridge services don't pass deal_id**
   - Location: `services/applications_bridge.py`, `services/organization_bridge.py`
   - Evidence: `add_item()` calls missing `deal_id=...` parameter
   - Fix: Add `deal_id=fact.deal_id` to all add_item() calls

2. **InventoryStore doesn't enforce deal_id**
   - Location: `stores/inventory_store.py` add_item() method
   - Evidence: deal_id parameter is Optional, warns but allows None
   - Fix: Make deal_id required, raise ValueError if missing

3. **Database schema allows NULL**
   - Location: `web/database.py` InventoryItem model (if persisted)
   - Evidence: `nullable=True` on deal_id column
   - Fix: Migration to set `nullable=False`

---

## Benefits

### Why Strict deal_id Enforcement

**Alternative:** Keep warnings, allow None values.

**Rejected Because:**
- Silent data corruption (queries return wrong items)
- Hard to debug (no error, just wrong totals)
- Violates multi-tenant isolation

**Chosen Approach:** Make deal_id required, fail fast if missing.

**Benefit:** Impossible to create inventory items without proper isolation. Bugs caught immediately, not in production.

---

### Why Fix at Bridge Layer

**Alternative:** Fix at InventoryStore by inferring deal_id from context.

**Rejected Because:**
- InventoryStore doesn't have context (just data)
- Inference is fragile (what if multiple deals in session?)
- Violates single responsibility

**Chosen Approach:** Bridges read deal_id from facts, pass explicitly.

**Benefit:** Clear data flow, explicit deal_id propagation, easy to audit.

---

## Expectations

### Success Criteria

1. **Zero "created without deal_id" warnings** after fixes
2. **All bridge services pass deal_id** to add_item()
3. **InventoryStore enforces deal_id** (raises error if missing)
4. **Integration tests validate** deal_id propagation
5. **Database constraint enforces** NOT NULL (if applicable)

### Measurable Outcomes

- **Baseline:** 35 warnings per discovery run (current)
- **Target:** 0 warnings per discovery run (after fix)
- **Validation:** Run discovery 3 times, zero warnings each time

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Breaking existing code that calls add_item()** | Medium | High | Search codebase for all add_item() calls, fix before deploying strict validation |
| **Facts missing deal_id** | Low | High | Facts already have deal_id (from B1 entity work). Add test to verify. |
| **Unknown inventory creation paths** | Medium | Medium | Comprehensive grep for add_item() calls, audit each one |
| **Database migration fails** | Low | Medium | Test migration on copy of production DB first, have rollback ready |

---

## Results Criteria

### Files to Audit/Modify

**Bridge Services (3-5 files):**
- `services/applications_bridge.py` — Add deal_id to add_item() calls
- `services/organization_bridge.py` — Add deal_id to add_item() calls
- `services/infrastructure_bridge.py` — Add deal_id (if file exists)
- Any other `*_bridge.py` files found

**Core Store:**
- `stores/inventory_store.py` — Make deal_id required in add_item()

**Database (if applicable):**
- `web/database.py` — Set deal_id nullable=False
- `alembic/versions/XXX_enforce_deal_id.py` — Migration script

**Tests:**
- `tests/integration/test_deal_id_propagation.py` — Integration test (NEW)
- `tests/unit/test_inventory_store.py` — Add test for deal_id requirement

**Estimated Lines Changed:** ~80 lines (20 new, 60 modified across 5-8 files)

---

### Acceptance Checklist

- [ ] Audit completed, all bridge services identified
- [ ] All bridge services modified to pass deal_id
- [ ] InventoryStore.add_item() enforces deal_id (raises ValueError if None)
- [ ] Integration test created and passing
- [ ] Manual verification performed (zero warnings)
- [ ] Database constraint added (if applicable)
- [ ] Migration tested and deployed
- [ ] Documentation updated (CLAUDE.md note about deal_id requirement)

---

## Cross-References

- **Depends On:** None (independent audit)
- **Relates To:**
  - audit1 Finding #5 (Missing deal_id in inventory items)
  - audits/B1_buyer_target_separation.md (entity separation work that added deal_id to facts)
  - CLAUDE.md ("`deal_id` is REQUIRED on all inventory items for multi-tenant data isolation")
- **Enables:**
  - 07-integration-testing-strategy.md (validates multi-tenant isolation)

---

**IMPLEMENTATION NOTE:** This fix is independent of other cost model specs and can be implemented in parallel. Priority: HIGH — data integrity issue affecting all deals.
