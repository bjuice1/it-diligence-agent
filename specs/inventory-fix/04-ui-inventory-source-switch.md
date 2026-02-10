# 04 — UI Inventory Source Switch: InventoryStore as Primary Count Source

## Status: NOT STARTED
## Priority: HIGH (Makes correct counts visible to users)
## Depends On: 01-pipeline-wiring, 02-llm-fact-promotion, 03-entity-enforcement
## Enables: 05-reconciliation-and-audit

---

## Overview

After Specs 01-03, the InventoryStore is populated with deduplicated, entity-scoped, content-hashed inventory items from both deterministic tables and LLM extraction. But the web UI still reads counts from **FactStore** (database Fact table) via bridge functions, which produces inflated numbers (same app in 3 docs = 3 counts).

**The fix:** Invert the route priority. Make InventoryStore the primary source, with FactStore as the fallback for legacy runs that don't have an InventoryStore.

The good news: `build_applications_from_inventory_store()` (line 353 of `applications_bridge.py`) and `build_infrastructure_from_inventory_store()` (line 401 of `infrastructure_bridge.py`) **already exist and work**. The routes in `web/app.py` already fall back to them. We just need to flip the priority order and add a `build_organization_from_inventory_store()` (which doesn't exist yet).

---

## Architecture

```
BEFORE (current):
  /applications route:
    1. TRY: Database facts → build_applications_inventory()       ← INFLATED COUNTS
    2. FALLBACK: InventoryStore → build_applications_from_inventory_store()  ← ALWAYS EMPTY
    3. FALLBACK: Empty inventory

AFTER (fixed):
  /applications route:
    1. TRY: InventoryStore → build_applications_from_inventory_store()  ← DEDUPLICATED COUNTS
    2. FALLBACK: Database facts → build_applications_inventory()        ← LEGACY SUPPORT
    3. FALLBACK: Empty inventory
```

Same pattern for `/infrastructure` and `/organization`.

---

## Specification

### Change 1: `/applications` route in `web/app.py` (line ~3300)

**Current priority order (lines 3324-3390):**
```python
# PRIMARY: Database facts
if current_deal_id:
    data = DealData()
    all_facts = data.get_all_facts(entity='target')
    app_facts = [f for f in all_facts if f.domain == "applications"]
    if app_facts:
        fact_adapter = wrap_db_facts(all_facts)
        inventory, status = build_applications_inventory(fact_adapter)
        return render_template(..., data_source="database")

# FALLBACK: InventoryStore
inv_store = get_inventory_store()
if len(inv_store) > 0:
    target_apps = inv_store.get_items(inventory_type="application", entity="target")
    if target_apps:
        inventory, status = build_applications_from_inventory_store(inv_store)
        return render_template(..., data_source="inventory")

# EMPTY
return render_template(..., data_source="none")
```

**New priority order:**
```python
# PRIMARY: InventoryStore (deduplicated, entity-scoped)
from web.blueprints.inventory import get_inventory_store
inv_store = get_inventory_store()
target_apps = inv_store.get_items(inventory_type="application", entity="target")
if target_apps:
    inventory, status = build_applications_from_inventory_store(inv_store)
    return render_template(
        'applications/overview.html',
        inventory=inventory,
        data_source="inventory",
        item_count=len(target_apps),
    )

# FALLBACK: Database facts (legacy runs without InventoryStore)
if current_deal_id:
    data = DealData()
    all_facts = data.get_all_facts(entity='target')
    app_facts = [f for f in all_facts if f.domain == "applications"]
    if app_facts:
        fact_adapter = wrap_db_facts(all_facts)
        inventory, status = build_applications_inventory(fact_adapter)
        return render_template(
            'applications/overview.html',
            inventory=inventory,
            data_source="database_legacy",
        )

# EMPTY
return render_template(
    'applications/overview.html',
    inventory=ApplicationsInventory(),
    data_source="none",
)
```

---

### Change 2: `/infrastructure` route in `web/app.py` (line ~3441)

**Same inversion as Change 1:**

```python
# PRIMARY: InventoryStore
inv_store = get_inventory_store()
infra_items = inv_store.get_items(inventory_type="infrastructure", entity="target")
if infra_items:
    inventory, status = build_infrastructure_from_inventory_store(inv_store)
    return render_template(
        'infrastructure/overview.html',
        inventory=inventory,
        data_source="inventory",
    )

# FALLBACK: Database facts
if current_deal_id:
    data = DealData()
    all_facts = data.get_all_facts(entity='target')
    infra_facts = [f for f in all_facts if f.domain == "infrastructure"]
    if infra_facts:
        fact_adapter = wrap_db_facts(all_facts)
        inventory, status = build_infrastructure_inventory(fact_adapter)
        return render_template(
            'infrastructure/overview.html',
            inventory=inventory,
            data_source="database_legacy",
        )

# EMPTY
return render_template(
    'infrastructure/overview.html',
    inventory=InfrastructureInventory(),
    data_source="none",
)
```

---

### Change 3: New function `build_organization_from_inventory_store()`

**File:** `services/organization_bridge.py`

**This function does not exist yet.** `build_applications_from_inventory_store()` and `build_infrastructure_from_inventory_store()` exist in their respective bridge files, but there is no equivalent for organization.

**Add after `build_organization_from_facts()` (after line ~187):**

```python
def build_organization_from_inventory_store(
    inventory_store: InventoryStore,
    target_name: str = "Target",
    deal_id: str = "",
) -> Tuple[OrganizationDataStore, str]:
    """Build OrganizationDataStore from InventoryStore organization items.

    This is the InventoryStore-based equivalent of build_organization_from_facts().
    Used when InventoryStore is populated (post Spec 01+02+03).

    Args:
        inventory_store: InventoryStore with organization items
        target_name: Company name for display
        deal_id: Deal ID for filtering

    Returns:
        Tuple of (OrganizationDataStore, status_message)
    """
    from stores.inventory_store import InventoryStore

    store = OrganizationDataStore()
    store.target_name = target_name

    # Get org items scoped to target entity
    org_items = inventory_store.get_items(
        inventory_type="organization", entity="target", status="active"
    )

    if not org_items:
        return store, "no_org_items"

    staff_members = []

    for item in org_items:
        data = item.data
        role = data.get("role", "Unknown Role")
        team = data.get("team", "")
        headcount = _safe_int(data.get("headcount", ""))
        fte = _safe_float(data.get("fte", ""))
        location = data.get("location", "")
        reports_to = data.get("reports_to", "")
        name = data.get("name", "")

        member = StaffMember(
            role=role,
            name=name,
            team=team,
            department=data.get("department", "IT"),
            headcount=headcount if headcount else 1,
            fte=fte if fte else (float(headcount) if headcount else 1.0),
            location=location,
            reports_to=reports_to,
            deal_id=deal_id,
            source="inventory",
            inventory_item_id=item.item_id,
        )
        staff_members.append(member)

    store.staff_members = staff_members
    store._update_counts()

    status = f"Built org from {len(org_items)} inventory items"
    logger.info(status)

    return store, "success"


def _safe_int(value) -> int:
    """Safely convert to int, returning 0 on failure."""
    if not value:
        return 0
    try:
        return int(float(str(value).replace(",", "")))
    except (ValueError, TypeError):
        return 0


def _safe_float(value) -> float:
    """Safely convert to float, returning 0.0 on failure."""
    if not value:
        return 0.0
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0
```

**Note:** The `StaffMember` dataclass may need an `inventory_item_id` field added if it doesn't have one. Check `models/organization_models.py` or `services/organization_bridge.py` for the definition. If StaffMember doesn't accept `inventory_item_id`, remove that kwarg and store the link separately.

---

### Change 4: `/organization` route in `web/app.py` (line ~3153)

**Current code calls `get_organization_analysis()` which always uses facts.**

**New priority order in `get_organization_analysis()` (line ~2546):**

```python
def get_organization_analysis():
    """Get or run the organization analysis — InventoryStore first, then DB facts."""
    current_deal_id = flask_session.get('current_deal_id')

    # PRIMARY: InventoryStore
    from web.blueprints.inventory import get_inventory_store
    inv_store = get_inventory_store()
    org_items = inv_store.get_items(inventory_type="organization", entity="target")
    if org_items:
        from services.organization_bridge import build_organization_from_inventory_store
        store, status = build_organization_from_inventory_store(
            inv_store,
            target_name=target_name,
            deal_id=current_deal_id or "",
        )
        if status == "success":
            # Build full result with benchmarks, MSP, etc.
            result = _build_org_result_from_store(store, current_deal_id)
            return result

    # FALLBACK: Database facts (existing logic)
    if current_deal_id:
        load_deal_context(current_deal_id)
        data = DealData()
        all_facts = data.get_all_facts(entity='target')
        org_facts = [f for f in all_facts if f.domain == "organization"]
        if all_facts and org_facts:
            # ... existing fact-based logic ...
```

---

### Change 5: Buyer view support

**Current state:** All routes hardcode `entity='target'`. Buyer views are either missing or return empty.

**For this spec:** Add buyer entity support to InventoryStore queries. When a route receives `?entity=buyer` query param:

```python
# In /applications route
requested_entity = request.args.get('entity', 'target')
if requested_entity not in ('target', 'buyer'):
    requested_entity = 'target'

inv_store = get_inventory_store()
entity_apps = inv_store.get_items(
    inventory_type="application",
    entity=requested_entity,
    status="active"
)
```

This naturally returns buyer items when they exist, and empty when they don't — which is correct if the deal has no buyer documents.

---

### Change 6: Data source indicator in templates

**Add to all inventory overview templates** (applications/overview.html, infrastructure/overview.html, organization/overview.html):

```html
{% if data_source == "inventory" %}
<span class="data-source-badge inventory">Inventory Store (Deduplicated)</span>
{% elif data_source == "database_legacy" %}
<span class="data-source-badge legacy">Legacy Facts (May contain duplicates)</span>
{% elif data_source == "none" %}
<span class="data-source-badge empty">No data — run analysis first</span>
{% endif %}
```

This gives operators immediate visibility into where counts are coming from.

---

## Benefits

1. **Correct counts immediately** — same app in 3 docs = 1 count (not 3)
2. **Buyer view works** — buyer items exist in InventoryStore with `entity="buyer"`, queryable via `?entity=buyer`
3. **Zero bridge function rewrites** — `build_*_from_inventory_store()` functions already exist and are tested
4. **Graceful degradation** — legacy runs without InventoryStore fall back to fact-based counting (current behavior)
5. **Visible data source** — operators can see whether counts come from deduplicated inventory or legacy facts

---

## Expectations

After this spec is implemented:

1. `/applications` displays `inventory.total_count` matching `inventory_store.count(inventory_type="application", entity="target")`
2. If a document mentions "Salesforce" in 3 different sections, the UI shows 1 application (not 3)
3. `/applications?entity=buyer` shows only buyer apps (or empty if no buyer docs were analyzed)
4. `/organization` shows team/headcount data from InventoryStore org items
5. A `data_source` badge is visible on each overview page
6. Legacy deals (analyzed before this fix) still show their fact-based counts as fallback

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| InventoryStore has fewer items than expected (users see "missing" apps) | Medium | Medium | This is actually correct — previous counts were inflated. Add a comparison note: "Previously showed N facts, now showing M unique items." Log the difference. |
| Organization bridge function missing StaffMember fields | Low | Medium | Check StaffMember dataclass before implementation. Remove unsupported kwargs. |
| `get_inventory_store()` loads empty store for current deal | Low | Medium | After Spec 01, discovery saves `inventory_store.json`. If file missing, fallback to facts. |
| Route changes break existing tests | Medium | Low | Existing tests likely test the fact-based path. Add parallel tests for inventory path. Keep both paths working. |

---

## Results Criteria

### Automated Tests

```python
def test_applications_route_uses_inventory_store(client):
    """Applications route should prefer InventoryStore when populated."""
    # Setup: create a deal with InventoryStore data
    inv_store = InventoryStore(deal_id="test-deal")
    inv_store.add_item(
        inventory_type="application", entity="target",
        data={"name": "Salesforce", "vendor": "Salesforce"},
        deal_id="test-deal",
    )
    inv_store.add_item(
        inventory_type="application", entity="target",
        data={"name": "SAP ECC", "vendor": "SAP"},
        deal_id="test-deal",
    )
    inv_store.save()

    # Request
    with client.session_transaction() as sess:
        sess['current_deal_id'] = 'test-deal'

    response = client.get('/applications')
    assert response.status_code == 200
    assert b'2 applications' in response.data  # Exact count
    assert b'inventory' in response.data.lower()  # Data source indicator

def test_applications_route_falls_back_to_facts(client):
    """Applications route should fall back to facts when InventoryStore is empty."""
    # No InventoryStore data, but facts exist in DB
    # ... setup DB facts ...
    response = client.get('/applications')
    assert response.status_code == 200
    assert b'database_legacy' in response.data.lower() or b'legacy' in response.data.lower()

def test_buyer_entity_filter(client):
    """Requesting entity=buyer should show only buyer items."""
    inv_store = InventoryStore(deal_id="test-deal")
    inv_store.add_item(
        inventory_type="application", entity="target",
        data={"name": "Target App"}, deal_id="test-deal",
    )
    inv_store.add_item(
        inventory_type="application", entity="buyer",
        data={"name": "Buyer App"}, deal_id="test-deal",
    )
    inv_store.save()

    with client.session_transaction() as sess:
        sess['current_deal_id'] = 'test-deal'

    response = client.get('/applications?entity=buyer')
    assert b'Buyer App' in response.data
    assert b'Target App' not in response.data
```

### Manual Verification

1. Run analysis on a test document
2. Navigate to `/applications` — verify count matches unique apps
3. Navigate to `/applications?entity=buyer` — verify buyer-only view
4. Check the data source badge shows "Inventory Store (Deduplicated)"
5. Delete `inventory_store.json` and refresh — verify fallback to fact-based counts with "Legacy" badge

---

## Files Modified

| File | Change |
|------|--------|
| `web/app.py` | Invert priority in `/applications` route (~line 3300), `/infrastructure` route (~line 3441), `get_organization_analysis()` (~line 2546) |
| `services/organization_bridge.py` | Add `build_organization_from_inventory_store()`, `_safe_int()`, `_safe_float()` |
| `web/templates/applications/overview.html` | Add data source badge |
| `web/templates/infrastructure/overview.html` | Add data source badge |
| `web/templates/organization/overview.html` | Add data source badge |

**Lines of code:** ~80 lines added (org bridge function), ~60 lines modified (route inversions), ~10 lines per template.
