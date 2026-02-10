# Spec 03: FactStore↔InventoryStore Bidirectional Linking

**Status:** Implemented
**Depends on:** Spec 01 (clean data), Spec 02 (correct categories)
**Enables:** Spec 05 (accurate app/user counts for cost estimation)

---

## Problem Statement

Application data flows through two disconnected paths:

1. **LLM extraction → FactStore** — Discovery agents extract facts like `F-TGT-APP-001: "SAP ECC 6.0, 500 users"` into the FactStore. These facts have evidence, entity scope, and domain classification.

2. **Table parsing → FactStore only** — `deterministic_parser.py:_app_table_to_facts()` (lines 292-397) creates facts in the FactStore but **never creates InventoryStore items**. The InventoryStore (`I-APP-xxx`) is only populated via manual import or the `inventory_integration.py:sync_inventory_to_facts()` one-way sync.

**Consequences:**
- The FactStore may have `F-TGT-APP-001` for SAP but no corresponding `I-APP-xxx` InventoryItem
- The InventoryStore may have `I-APP-abc123` from an import but no linked fact
- UI components querying different stores show different application counts
- Cost estimation using InventoryStore app counts gets different numbers than FactStore-based analysis
- No way to trace from a fact back to its inventory item or vice versa

---

## Architecture: Current Two-Path Problem

```
PDF Document
    │
    ├── LLM Agent ──────── fact_store.add_fact() ──→ F-TGT-APP-001
    │                                                  (no inventory item)
    │
    └── deterministic_parser
        └── _app_table_to_facts() ──→ fact_store.add_fact() ──→ F-TGT-APP-002
                                                                  (no inventory item)

Excel Import ──→ inventory_store.add_item() ──→ I-APP-abc123
                                                  (no fact)

sync_inventory_to_facts() ──→ I-APP-abc123 → F-TGT-APP-003
                              (one-way only, no back-link)
```

**Target architecture:**

```
PDF Document
    │
    ├── LLM Agent ──→ fact_store.add_fact() ──→ F-TGT-APP-001
    │                                              ↕ (bidirectional link)
    │                                          I-APP-abc123
    │
    └── deterministic_parser
        └── _app_table_to_facts()
            ├── fact_store.add_fact() ──→ F-TGT-APP-002
            │                               ↕ (bidirectional link)
            └── inventory_store.add_item() → I-APP-def456
```

---

## Files to Modify

### 1. `stores/fact_store.py` — Add `inventory_item_id` Field to Fact

**Current Fact dataclass (lines 93-135):** No reference to InventoryStore items.

**Add field after `deal_id` (line 105):**

```python
@dataclass
class Fact:
    fact_id: str
    domain: str
    category: str
    item: str
    details: Dict[str, Any]
    status: str
    evidence: Dict[str, str]
    entity: str = "target"
    analysis_phase: str = "target_extraction"
    is_integration_insight: bool = False
    source_document: str = ""
    deal_id: str = ""
    inventory_item_id: str = ""  # NEW: Cross-reference to I-APP-xxx, I-INFRA-xxx
    # ... rest of fields
```

**Update `to_dict()` (line ~136)** to include `inventory_item_id`.

**Update `from_dict()` (line ~230)** to deserialize `inventory_item_id` with default `""` for backwards compatibility.

### 2. `stores/inventory_store.py` (or `inventory_item.py`) — Add `source_fact_ids` Field

**Current InventoryItem dataclass (lines 26-145 in inventory_item.py):** Has `deal_id` but no reference to FactStore facts.

**Add field after `deal_id` (line ~68):**

```python
@dataclass
class InventoryItem:
    item_id: str
    inventory_type: str
    entity: str
    data: Dict[str, Any]
    source_file: str = ""
    source_type: str = "import"
    deal_id: str = ""
    source_fact_ids: List[str] = field(default_factory=list)  # NEW: F-TGT-APP-xxx IDs that reference this item
    enrichment: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    # ... rest of fields
```

**Update serialization methods** (`to_dict()`, `from_dict()`) to include `source_fact_ids`.

### 3. `tools_v2/deterministic_parser.py` — Route to Both Stores

**Current `_app_table_to_facts()` (lines 292-397):** Only calls `fact_store.add_fact()`.

**Modify to also create InventoryStore items (after line 390, where fact is added):**

```python
def _app_table_to_facts(
    table: "ParsedTable",
    fact_store: "FactStore",
    source_file: str,
    entity: str = "target",
    inventory_store: Optional["InventoryStore"] = None,  # NEW parameter
) -> int:
    """Convert application table to facts AND inventory items."""
    facts_created = 0

    for row_data in table.rows:
        # ... existing extraction logic (lines 302-376) ...

        # Create fact (existing logic)
        fact_id = fact_store.add_fact(
            domain="applications",
            category=category,
            item=app_name,
            details=details,
            status=status,
            evidence=evidence,
            entity=entity,
            source_document=source_file,
        )
        facts_created += 1

        # NEW: Also create inventory item if store available
        if inventory_store is not None:
            inv_data = {
                "name": app_name,
                "vendor": details.get("vendor", ""),
                "version": details.get("version", ""),
                "hosting": details.get("hosting", ""),
                "users": details.get("users", ""),
                "cost": details.get("cost", ""),
                "criticality": details.get("criticality", ""),
                "category": category,
                "source_category": details.get("source_category", ""),
                "category_confidence": details.get("category_confidence", ""),
                "category_inferred_from": details.get("category_inferred_from", ""),
            }
            # Remove empty values
            inv_data = {k: v for k, v in inv_data.items() if v}

            inv_item_id = inventory_store.add_item(
                inventory_type="application",
                entity=entity,
                data=inv_data,
                source_file=source_file,
                source_type="import",
                deal_id=fact_store.deal_id,
            )

            # Bidirectional linking
            if inv_item_id and fact_id:
                # Link fact → inventory
                fact = fact_store.get_fact(fact_id)
                if fact:
                    fact.inventory_item_id = inv_item_id

                # Link inventory → fact
                inv_item = inventory_store.get_item(inv_item_id)
                if inv_item:
                    if fact_id not in inv_item.source_fact_ids:
                        inv_item.source_fact_ids.append(fact_id)

    return facts_created
```

**Similarly update `_infra_table_to_facts()` (lines 400-481) and `_contract_table_to_facts()` (lines 484-527)** to accept optional `inventory_store` parameter and create linked items.

**Update `table_to_facts()` (lines 261-289)** to pass `inventory_store` through:

```python
def table_to_facts(
    table: "ParsedTable",
    table_type: str,
    fact_store: "FactStore",
    source_file: str,
    entity: str = "target",
    inventory_store: Optional["InventoryStore"] = None,  # NEW
) -> int:
    if table_type == "application_inventory":
        return _app_table_to_facts(table, fact_store, source_file, entity, inventory_store)
    elif table_type == "infrastructure_inventory":
        return _infra_table_to_facts(table, fact_store, source_file, entity, inventory_store)
    elif table_type == "contract_inventory":
        return _contract_table_to_facts(table, fact_store, source_file, entity, inventory_store)
    else:
        return 0
```

### 4. `tools_v2/inventory_integration.py` — Make `sync_inventory_to_facts()` Bidirectional

**Current (lines 225-301):** One-way sync: Inventory → Facts. Creates facts from inventory items but doesn't link back.

**Enhance to set cross-references:**

```python
def sync_inventory_to_facts(
    inventory_store: "InventoryStore",
    fact_store: "FactStore",
    entity: str = "target",
    source_file: str = "inventory_import",
) -> Dict[str, int]:
    """Bidirectional sync: create facts from inventory items AND link them."""
    stats = {"synced": 0, "skipped": 0, "linked": 0, "by_type": {}}

    for item in inventory_store.get_items(entity=entity):
        # ... existing fact creation logic (lines 245-290) ...

        fact_id = fact_store.add_fact(
            domain=domain,
            category=category,
            item=item.name,
            details=details,
            status="documented",
            evidence=evidence,
            entity=entity,
            source_document=source_file,
        )

        if fact_id:
            # NEW: Bidirectional linking
            # Link fact → inventory item
            fact = fact_store.get_fact(fact_id)
            if fact:
                fact.inventory_item_id = item.item_id

            # Link inventory item → fact
            if fact_id not in item.source_fact_ids:
                item.source_fact_ids.append(fact_id)

            stats["linked"] += 1
            stats["synced"] += 1

    return stats
```

### 5. `tools_v2/inventory_integration.py` — Add Reconciliation Function

**New function for matching existing unlinked facts to inventory items:**

```python
def reconcile_facts_and_inventory(
    fact_store: "FactStore",
    inventory_store: "InventoryStore",
    entity: str = "target",
    similarity_threshold: float = 0.8,
) -> Dict[str, int]:
    """Match unlinked facts to inventory items by name+vendor similarity.

    For facts that were created by LLM extraction (no inventory_item_id)
    and inventory items that were created by import (no source_fact_ids),
    attempt to match them and create bidirectional links.

    Returns: {"matched": int, "unmatched_facts": int, "unmatched_items": int}
    """
    from difflib import SequenceMatcher

    stats = {"matched": 0, "unmatched_facts": 0, "unmatched_items": 0}

    # Get unlinked facts (applications domain, no inventory_item_id)
    app_facts = [
        f for f in fact_store.get_facts(domain="applications", entity=entity)
        if not f.inventory_item_id
    ]

    # Get unlinked inventory items (no source_fact_ids)
    app_items = [
        item for item in inventory_store.get_items(
            inventory_type="application", entity=entity
        )
        if not item.source_fact_ids
    ]

    # Match by name similarity
    matched_item_ids = set()
    for fact in app_facts:
        fact_name = fact.item.lower().strip()
        best_match = None
        best_score = 0.0

        for item in app_items:
            if item.item_id in matched_item_ids:
                continue

            item_name = item.name.lower().strip()
            score = SequenceMatcher(None, fact_name, item_name).ratio()

            # Boost score if vendor also matches
            fact_vendor = fact.details.get("vendor", "").lower()
            item_vendor = item.data.get("vendor", "").lower()
            if fact_vendor and item_vendor:
                vendor_score = SequenceMatcher(None, fact_vendor, item_vendor).ratio()
                score = (score * 0.7) + (vendor_score * 0.3)

            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score >= similarity_threshold:
            # Create bidirectional link
            fact.inventory_item_id = best_match.item_id
            if fact.fact_id not in best_match.source_fact_ids:
                best_match.source_fact_ids.append(fact.fact_id)
            matched_item_ids.add(best_match.item_id)
            stats["matched"] += 1
        else:
            stats["unmatched_facts"] += 1

    stats["unmatched_items"] = len(app_items) - len(matched_item_ids)
    return stats
```

### 6. Upstream Callers — Pass `inventory_store` to Parser

**Find all callers of `table_to_facts()` and `preprocess_document()`** and update them to pass `inventory_store`:

The main caller is likely in the discovery agent pipeline. Search for:
```
grep -r "table_to_facts\|preprocess_document" --include="*.py"
```

Update each caller to pass the inventory store if available. If the caller doesn't have access to the inventory store, the parameter is optional (defaults to `None`) so no breaking change.

---

## Deal-Scoping Verification

**Critical:** Both FactStore and InventoryStore items must be scoped to the same `deal_id`. The linking logic must verify:

```python
# In all linking functions:
assert fact.deal_id == inventory_item.deal_id, \
    f"Cross-deal linking prohibited: fact {fact.fact_id} (deal {fact.deal_id}) " \
    f"cannot link to item {inventory_item.item_id} (deal {inventory_item.deal_id})"
```

This prevents facts from Deal A accidentally linking to inventory items from Deal B.

---

## Test Cases

### Test 1: Dual Store Creation from Table
```python
def test_app_table_creates_both_stores():
    """Parsing a table should create both F-* and I-* entries."""
    fact_store = FactStore(deal_id="test-deal")
    inv_store = InventoryStore(deal_id="test-deal")

    table = create_test_table([
        {"name": "SAP ECC", "vendor": "SAP", "users": "500"},
        {"name": "Salesforce", "vendor": "Salesforce", "users": "200"},
    ])

    count = _app_table_to_facts(table, fact_store, "test.pdf", "target", inv_store)

    # Facts created
    assert count == 2
    app_facts = fact_store.get_facts(domain="applications")
    assert len(app_facts) == 2

    # Inventory items also created
    app_items = inv_store.get_items(inventory_type="application")
    assert len(app_items) == 2

    # Bidirectional links exist
    sap_fact = [f for f in app_facts if "SAP" in f.item][0]
    assert sap_fact.inventory_item_id != ""
    sap_item = inv_store.get_item(sap_fact.inventory_item_id)
    assert sap_fact.fact_id in sap_item.source_fact_ids
```

### Test 2: Cross-Reference Integrity
```python
def test_bidirectional_link_integrity():
    """Every fact→inventory link must have a matching inventory→fact link."""
    # ... create facts and items via table parsing ...

    for fact in fact_store.get_facts(domain="applications"):
        if fact.inventory_item_id:
            item = inv_store.get_item(fact.inventory_item_id)
            assert item is not None, f"Fact {fact.fact_id} references missing item {fact.inventory_item_id}"
            assert fact.fact_id in item.source_fact_ids, \
                f"Item {item.item_id} missing back-link to fact {fact.fact_id}"
```

### Test 3: Reconciliation by Similarity
```python
def test_reconcile_unlinked_facts_and_items():
    """Reconciliation should match similar names across stores."""
    fact_store = FactStore(deal_id="test-deal")
    inv_store = InventoryStore(deal_id="test-deal")

    # Create a fact from LLM (no inventory link)
    fact_store.add_fact(
        domain="applications", category="erp", item="SAP ECC 6.0",
        details={"vendor": "SAP SE"}, status="documented",
        evidence={"exact_quote": "SAP ECC 6.0"}, entity="target",
    )

    # Create an inventory item from import (no fact link)
    inv_store.add_item(
        inventory_type="application", entity="target",
        data={"name": "SAP ECC", "vendor": "SAP"},
        source_file="import.xlsx", source_type="import",
        deal_id="test-deal",
    )

    stats = reconcile_facts_and_inventory(fact_store, inv_store, "target")
    assert stats["matched"] == 1
    assert stats["unmatched_facts"] == 0
    assert stats["unmatched_items"] == 0
```

### Test 4: Deal Scoping
```python
def test_cross_deal_linking_blocked():
    """Facts from one deal must not link to inventory items from another."""
    # Create fact with deal_id="deal-1"
    # Create inventory item with deal_id="deal-2"
    # Attempt link → should raise AssertionError or be skipped
```

### Test 5: Backwards Compatibility
```python
def test_old_facts_without_inventory_id():
    """Facts created before this change should still work."""
    old_fact_dict = {"fact_id": "F-TGT-APP-001", "domain": "applications", ...}
    # No "inventory_item_id" key
    fact = Fact.from_dict(old_fact_dict)
    assert fact.inventory_item_id == ""  # Default empty string
```

---

## Acceptance Criteria

1. Parse a table document → verify both `F-APP-xxx` fact AND `I-APP-xxx` inventory item exist
2. Cross-references verified: `fact.inventory_item_id == item.item_id` AND `fact.fact_id in item.source_fact_ids`
3. UI shows consistent application counts regardless of whether it queries FactStore or InventoryStore
4. `sync_inventory_to_facts()` now creates bidirectional links (not just one-way)
5. `reconcile_facts_and_inventory()` matches >80% of similar-named apps across stores
6. No cross-deal linking occurs (deal_id isolation maintained)
7. Backwards compatible: old facts/items without new fields load with empty defaults

---

## Performance Considerations

**Reconciliation with large inventories:**
- `reconcile_facts_and_inventory()` is O(F × I) where F = unlinked facts, I = unlinked items
- For typical M&A (50-500 applications), this is fast (<100ms)
- For very large inventories (>1000 apps), consider indexing by normalized first word
- **Gate 1 check:** If reconciliation takes >1s for test data, add indexing before proceeding to Spec 05

---

## Rollback Plan

- New fields (`inventory_item_id`, `source_fact_ids`) default to empty — removing them doesn't break existing data
- `inventory_store` parameter is optional (`None`) — removing it from callers restores old behavior
- Reconciliation is a standalone function — not calling it has no side effects
- All changes are additive to the data model; no existing fields are modified or removed

---

## Implementation Notes

*Documented 2026-02-09 from actual implementation.*

### 1. Files Modified

#### `stores/fact_store.py`
- **Line 118:** Added `inventory_item_id: str = ""` field to the `Fact` dataclass, with comment `# Cross-reference to I-APP-xxx, I-INFRA-xxx in InventoryStore`. Placed after `deal_id` (line 117), exactly as specified.
- **Lines 137-141 (`to_dict`):** No explicit change needed; `to_dict()` uses `asdict(self)` which automatically includes all dataclass fields, so `inventory_item_id` is serialized by default.
- **Lines 256-258 (`from_dict`):** Added backwards-compatibility handling:
  ```python
  if 'inventory_item_id' not in data:
      data['inventory_item_id'] = ""  # Legacy facts without inventory link
  ```

#### `stores/inventory_item.py`
- **Line 60:** Added `source_fact_ids: List[str] = field(default_factory=list)` field to the `InventoryItem` dataclass, with comment `# F-TGT-APP-xxx IDs that reference this item`. Placed after `deal_id` (line 57), as specified.
- **Line 59:** Added inline comment `# FactStore cross-references (Spec 03: bidirectional linking)`.
- **Lines 233-235 (`to_dict`):** No explicit change needed; `to_dict()` uses `asdict(self)` which automatically includes `source_fact_ids`.
- **Lines 250-252 (`from_dict`):** Added backwards-compatibility handling:
  ```python
  if "source_fact_ids" not in data:
      data["source_fact_ids"] = []  # Legacy items without fact links
  ```

#### `tools_v2/deterministic_parser.py`
- **Lines 301-331 (`table_to_facts`):** Added `inventory_store: Optional["InventoryStore"] = None` parameter (line 306). Updated all three dispatch calls to pass `inventory_store` through (lines 324, 326, 328).
- **Lines 334-522 (`_app_table_to_facts`):** Added `inventory_store` parameter (line 339). After fact creation (line 470), added inventory item creation and bidirectional linking logic (lines 474-517). Creates inventory item with `inventory_type="application"`, builds `inv_data` dict from parsed details, removes empty values, calls `inventory_store.add_item()`, then sets `fact.inventory_item_id` and appends to `inv_item.source_fact_ids`.
- **Lines 525-645 (`_infra_table_to_facts`):** Added `inventory_store` parameter (line 530). After fact creation (line 603), added inventory item creation block (lines 605-640) for `inventory_type="infrastructure"`. Maps fields like `server_type`, `operating_system`, `environment`, `ip_address`, `location`, `cpu`, `memory`, `storage`.
- **Lines 648-727 (`_contract_table_to_facts`):** Added `inventory_store` parameter (line 653). After fact creation (line 688), added inventory item creation block (lines 690-722) for `inventory_type="vendor"`. Maps fields like `contract_type`, `start_date`, `end_date`, `acv`, `tcv`.
- **Lines 734-788 (`preprocess_document`):** Added `inventory_store` parameter (line 739). Passes it through to `table_to_facts()` call at line 787.

#### `tools_v2/inventory_integration.py`
- **Lines 225-316 (`sync_inventory_to_facts`):** Made bidirectional. Docstring updated (line 232) to say "Bidirectional sync". Added `"linked": 0` to stats dict (line 250). After fact creation (line 291), added bidirectional linking block (lines 294-305): sets `fact.inventory_item_id = item.item_id` and appends `fact_id` to `item.source_fact_ids`. Increments `stats["linked"]`.
- **Lines 319-394 (`reconcile_facts_and_inventory`):** New function added, exactly as specified. Uses `difflib.SequenceMatcher` with a configurable `similarity_threshold` (default 0.8). Gets unlinked facts via `fact_store.get_entity_facts(entity, domain="applications")` and unlinked items via `inventory_store.get_items(inventory_type="application", entity=entity)`. Matches by name similarity with 70/30 name/vendor weighting when vendor is available. Returns `{"matched", "unmatched_facts", "unmatched_items"}`.

#### `agents_v2/base_discovery_agent.py`
- **Line 90 (`__init__` signature):** Added `inventory_store: Optional[Any] = None` parameter.
- **Line 118:** Stores it as `self.inventory_store` with comment `# Optional InventoryStore for bidirectional linking (Spec 03)`.
- **Line 234:** Passes `inventory_store=self.inventory_store` to the `deterministic_preprocess()` call during document preprocessing (line 229).

### 2. Deviations from Spec

| Area | Spec Proposed | Implementation | Impact |
|---|---|---|---|
| **`table_to_facts` parameter name** | `source_file` | `source_document` | Cosmetic; matches existing codebase convention. No functional difference. |
| **`table_to_facts` parameter `table_type`** | Separate `table_type` parameter | Type detected internally via `detect_table_type(table)` | Cleaner API; type is auto-detected from table headers rather than passed explicitly. |
| **Inventory `source_type`** | `"import"` for parser-created items | `"discovery"` for parser-created items | More accurate: items created by the deterministic parser during document discovery are tagged `"discovery"`, distinguishing them from Excel/ToltIQ imports. |
| **Deal-scoping assertion** | Explicit `assert fact.deal_id == inventory_item.deal_id` guard | Not implemented as an assertion | Deal isolation is maintained implicitly: `deal_id=fact_store.deal_id` is passed when creating inventory items, so they inherit the same deal. No explicit cross-deal blocking assertion exists. |
| **`reconcile_facts_and_inventory` fact lookup** | Uses `fact_store.get_facts(domain="applications", entity=entity)` | Uses `fact_store.get_entity_facts(entity, domain="applications")` | Adapts to actual FactStore API which uses `get_entity_facts()` rather than `get_facts()` with keyword arguments. |
| **`inventory_store` type hint in `base_discovery_agent.py`** | Not specified (expected `Optional["InventoryStore"]`) | `Optional[Any]` | Avoids import dependency; the agent module does not import `InventoryStore` directly. |
| **Error handling** | Not specified in detail | All inventory creation wrapped in `try/except` with `logger.warning` | Defensive: inventory creation failures do not prevent fact creation from succeeding. |

### 3. Test Coverage

**Test file:** `tests/test_inventory_linking.py` (11 tests across 3 classes)

#### `TestBidirectionalLinking` (6 tests)
| Test | Verifies |
|---|---|
| `test_fact_has_inventory_item_id_field` | `Fact` dataclass has `inventory_item_id` field, defaults to `""` |
| `test_inventory_item_has_source_fact_ids_field` | `InventoryItem` dataclass has `source_fact_ids` field, defaults to `[]` |
| `test_fact_to_dict_includes_inventory_item_id` | `Fact.to_dict()` serializes `inventory_item_id` correctly |
| `test_inventory_item_to_dict_includes_source_fact_ids` | `InventoryItem.to_dict()` serializes `source_fact_ids` correctly |
| `test_fact_from_dict_backwards_compat_missing_inventory_item_id` | `Fact.from_dict()` handles old data without `inventory_item_id`, defaults to `""` |
| `test_inventory_item_from_dict_backwards_compat_missing_source_fact_ids` | `InventoryItem.from_dict()` handles old data without `source_fact_ids`, defaults to `[]` |

#### `TestReconciliation` (2 tests)
| Test | Verifies |
|---|---|
| `test_reconcile_function_exists` | `reconcile_facts_and_inventory` is importable and callable |
| `test_reconcile_signature` | Function signature includes `fact_store`, `inventory_store`, and `similarity_threshold` parameters |

#### `TestDealIsolation` (3 tests)
| Test | Verifies |
|---|---|
| `test_fact_has_deal_id` | `Fact` dataclass has `deal_id` field that stores a deal identifier |
| `test_inventory_item_has_deal_id` | `InventoryItem` dataclass has `deal_id` field that stores a deal identifier |
| `test_inventory_item_validates_entity` | `InventoryItem` rejects invalid `entity` values (not "target" or "buyer") with `ValueError` |

**Coverage gaps vs. spec test cases:**
- Spec Test 1 (dual store creation from table parsing) is not tested end-to-end (would require a running `FactStore` + `InventoryStore` + `_app_table_to_facts` integration test)
- Spec Test 2 (bidirectional link integrity check across all facts) is not tested end-to-end
- Spec Test 3 (reconciliation with actual stores and similarity matching) is a signature-only test, not a functional test with data
- Spec Test 4 (cross-deal linking blocked) is partially covered by deal_id field existence tests, but no test verifies that cross-deal linking is actually prevented
