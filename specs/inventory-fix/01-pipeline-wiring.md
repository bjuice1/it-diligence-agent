# 01 — Pipeline Wiring: Connect InventoryStore to Discovery Pipeline

## Status: NOT STARTED
## Priority: CRITICAL (Unblocks all other specs)
## Depends On: Nothing
## Enables: 02-llm-fact-promotion, 04-ui-inventory-source-switch, 05-reconciliation-and-audit

---

## Overview

The `InventoryStore` is fully implemented with content-hashed IDs, entity-aware fingerprints, deal isolation, merge/dedupe logic, and schema validation. The `BaseDiscoveryAgent` accepts an `inventory_store` parameter and passes it to the deterministic parser. The deterministic parser creates InventoryItems when `inventory_store is not None`.

**The problem:** Neither `main_v2.py:run_discovery()` nor `web/tasks/analysis_tasks.py:_analyze_domain()` ever instantiate or pass an `InventoryStore`. The parameter defaults to `None`, so the deterministic parser's `if inventory_store is not None` guard always fails. Every table row creates a Fact but never an InventoryItem. The entire Spec 03 (bidirectional linking) is dead code in production.

**The fix:** Create an InventoryStore at pipeline entry, pass it through to the discovery agent, and persist it after discovery completes.

---

## Architecture

```
BEFORE (broken):
  main_v2.py:run_discovery()
    → agent_class(fact_store=..., inventory_store=NOT PASSED)
      → BaseDiscoveryAgent.__init__(inventory_store=None)
        → deterministic_preprocess(inventory_store=None)
          → if inventory_store is not None: ← ALWAYS FALSE
              create inventory items  ← NEVER RUNS

AFTER (fixed):
  main_v2.py:run_discovery()
    → InventoryStore(deal_id=deal_id) created
    → agent_class(fact_store=..., inventory_store=inv_store)
      → BaseDiscoveryAgent.__init__(inventory_store=inv_store)
        → deterministic_preprocess(inventory_store=inv_store)
          → if inventory_store is not None: ← TRUE
              create inventory items + bidirectional links ← RUNS
    → inv_store.save()
```

---

## Specification

### Change 1: `main_v2.py:run_discovery()` (line 139)

**Current signature (line 139-147):**
```python
def run_discovery(
    document_text: str,
    domain: str = "infrastructure",
    fact_store: Optional[FactStore] = None,
    target_name: Optional[str] = None,
    industry: Optional[str] = None,
    document_name: str = "",
    deal_id: Optional[str] = None
) -> FactStore:
```

**New signature:**
```python
def run_discovery(
    document_text: str,
    domain: str = "infrastructure",
    fact_store: Optional[FactStore] = None,
    target_name: Optional[str] = None,
    industry: Optional[str] = None,
    document_name: str = "",
    deal_id: Optional[str] = None,
    inventory_store: Optional[InventoryStore] = None,
) -> FactStore:
```

**New logic (after line 171, before agent creation at line 185):**
```python
# Import at top of file
from stores.inventory_store import InventoryStore

# Create InventoryStore if not provided (line ~172)
if inventory_store is None:
    inventory_store = InventoryStore(deal_id=effective_deal_id)
```

**Update agent_kwargs (line 188-195):**
```python
agent_kwargs = {
    "fact_store": fact_store,
    "api_key": ANTHROPIC_API_KEY,
    "model": DISCOVERY_MODEL,
    "max_tokens": DISCOVERY_MAX_TOKENS,
    "max_iterations": DISCOVERY_MAX_ITERATIONS,
    "target_name": target_name,
    "inventory_store": inventory_store,  # NEW
}
```

**Return change:** The function currently returns only `fact_store`. Change to return both:
```python
# Return type changes to Tuple[FactStore, InventoryStore]
return fact_store, inventory_store
```

**Alternatively**, to minimize blast radius on callers, store the inventory_store as an attribute on the returned fact_store:
```python
fact_store._inventory_store = inventory_store
return fact_store
```

**Recommended approach:** Change return type. There are only 4 call sites, all in this same file.

---

### Change 2: `main_v2.py:run_discovery_for_domain()` (line 545)

**Current code (line 545-580):**
```python
def run_discovery_for_domain(
    document_text: str,
    domain: str,
    shared_fact_store: FactStore,
    target_name: Optional[str] = None,
    deal_id: Optional[str] = None
) -> Dict:
```

**New signature:**
```python
def run_discovery_for_domain(
    document_text: str,
    domain: str,
    shared_fact_store: FactStore,
    shared_inventory_store: InventoryStore,
    target_name: Optional[str] = None,
    deal_id: Optional[str] = None
) -> Dict:
```

**New logic (line ~561-570):**
```python
# Local FactStore for this domain (existing)
local_store = FactStore(deal_id=effective_deal_id)

# Shared InventoryStore — thread-safe (already has _lock in add_item)
# No need for local copy; InventoryStore.add_item() uses threading.Lock
result = run_discovery(
    document_text=document_text,
    domain=domain,
    fact_store=local_store,
    target_name=target_name,
    deal_id=effective_deal_id,
    inventory_store=shared_inventory_store,  # NEW: pass shared store
)
```

**Thread safety note:** `InventoryStore.add_item()` (line 130) already uses `with self._lock:` for thread-safe writes. No additional synchronization needed.

---

### Change 3: `main_v2.py:run_parallel_discovery()` (line ~640)

**Current code creates shared_fact_store, passes to futures.**

**Add shared InventoryStore (after line 655):**
```python
shared_fact_store = FactStore(deal_id=deal_id)
shared_inventory_store = InventoryStore(deal_id=deal_id)  # NEW
```

**Update executor.submit call (line 661-668):**
```python
futures = {
    executor.submit(
        run_discovery_for_domain,
        document_text,
        domain,
        shared_fact_store,
        shared_inventory_store,  # NEW
        target_name,
        deal_id
    ): domain
    for domain in domains
}
```

**After parallel completion, save InventoryStore:**
```python
# Save inventory store (after all futures complete)
shared_inventory_store.save()
logger.info(f"Saved {len(shared_inventory_store)} inventory items to {shared_inventory_store.storage_path}")
```

---

### Change 4: Sequential discovery path in `main_v2.py` (line ~1150)

**Current code (lines 1150-1160):**
```python
# Sequential discovery
fact_store = FactStore(deal_id=deal_id)
for domain in domains_to_analyze:
    run_discovery(
        document_text=document_text,
        domain=domain,
        fact_store=fact_store,
        target_name=args.target_name,
        deal_id=deal_id
    )
```

**New code:**
```python
# Sequential discovery
fact_store = FactStore(deal_id=deal_id)
inventory_store = InventoryStore(deal_id=deal_id)  # NEW
for domain in domains_to_analyze:
    run_discovery(
        document_text=document_text,
        domain=domain,
        fact_store=fact_store,
        target_name=args.target_name,
        deal_id=deal_id,
        inventory_store=inventory_store,  # NEW
    )

# Save inventory store after all discovery completes
inventory_store.save()
```

---

### Change 5: `web/tasks/analysis_tasks.py:_analyze_domain()` (line ~208)

**Current code (lines 208-220):**
```python
fact_store = FactStore(deal_id=deal_id)

# Get deal info for context
deal = Deal.query.get(deal_id)

agent_class = DISCOVERY_AGENTS[domain]
agent = agent_class(
    api_key=ANTHROPIC_API_KEY,
    fact_store=fact_store
)
```

**New code:**
```python
from stores.inventory_store import InventoryStore

fact_store = FactStore(deal_id=deal_id)
inventory_store = InventoryStore(deal_id=deal_id)  # NEW

# Get deal info for context
deal = Deal.query.get(deal_id)

agent_class = DISCOVERY_AGENTS[domain]
agent = agent_class(
    api_key=ANTHROPIC_API_KEY,
    fact_store=fact_store,
    inventory_store=inventory_store,  # NEW
)
```

**After facts are saved to DB (after line 256), save InventoryStore:**
```python
# Save inventory items to deal-specific path
inventory_store.save()
logger.info(f"Saved {len(inventory_store)} inventory items for deal {deal_id}")
```

**Optional DB persistence (future):** Also write InventoryItems to a PostgreSQL table, mirroring how facts are persisted at lines 231-256. This is deferred — JSON persistence is sufficient for the initial fix. The web's `get_inventory_store()` already loads from the JSON path.

---

### Change 6: Session-based discovery in `main_v2.py` (line ~1100)

**Current code (lines 1104-1117) — parallel path within session:**
```python
run_parallel_discovery(
    document_text=document_text,
    domains=domains_to_analyze,
    max_workers=MAX_PARALLEL_AGENTS,
    target_name=args.target_name
)
```

**New code:**
```python
run_parallel_discovery(
    document_text=document_text,
    domains=domains_to_analyze,
    max_workers=MAX_PARALLEL_AGENTS,
    target_name=args.target_name,
    deal_id=deal_id  # Already present, verify
)
# InventoryStore is saved inside run_parallel_discovery
```

**Sequential path within session (lines 1112-1117):**
Same pattern as Change 4 — create InventoryStore, pass to each `run_discovery()` call, save after loop.

---

## Benefits

1. **Zero new abstractions** — uses existing InventoryStore, BaseDiscoveryAgent parameter, deterministic_parser integration
2. **Thread-safe by design** — InventoryStore.add_item() already uses threading.Lock
3. **Immediate effect** — tables that were being parsed into Facts will now also produce InventoryItems with content-hashed IDs and bidirectional links
4. **Backward compatible** — InventoryStore parameter defaults to None; existing tests that don't pass it continue to work
5. **Persistence via existing mechanism** — `inventory_store.save()` writes to `output/deals/{deal_id}/inventory_store.json`, which `get_inventory_store()` already knows how to load

---

## Expectations

After this spec is implemented:

1. Running `python main_v2.py data/input/ --all --target-name "Acme"` produces an `inventory_store.json` file in the output directory
2. The JSON file contains InventoryItems for every row parsed from application, infrastructure, and contract tables
3. Each InventoryItem has:
   - `item_id` in `I-TYPE-HASH` format
   - `entity` set to "target" or "buyer" (matching the document)
   - `deal_id` set to the current deal
   - `source_fact_ids` containing the linked fact ID(s)
4. Each corresponding Fact has `inventory_item_id` set to the InventoryItem ID
5. `get_inventory_store()` in the web app loads these items and returns a non-empty store

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Return type change breaks callers | Medium | Medium | Only 4 call sites in main_v2.py; all in same file. Update all simultaneously. |
| Thread contention on shared InventoryStore in parallel mode | Low | Low | InventoryStore already uses threading.Lock. Lock scope is narrow (dict insert). |
| InventoryStore JSON grows large for deals with many items | Low | Low | Typical deal has 50-200 items. JSON is <100KB. Not a concern. |
| Celery task failures leave partial InventoryStore | Medium | Low | InventoryStore.save() is atomic (write-and-replace). Partial items are valid — next domain adds more. |

---

## Results Criteria

### Automated Tests

```python
def test_run_discovery_populates_inventory_store():
    """After run_discovery(), InventoryStore should contain items from tables."""
    fact_store = FactStore(deal_id="test-deal")
    inv_store = InventoryStore(deal_id="test-deal")

    # Document with a known application table
    doc_text = """
    | Application | Vendor | Version | Criticality |
    |---|---|---|---|
    | Salesforce | Salesforce | Enterprise | Critical |
    | SAP ECC | SAP | 6.0 | Critical |
    | Slack | Slack Technologies | N/A | Medium |
    """

    run_discovery(
        document_text=doc_text,
        domain="applications",
        fact_store=fact_store,
        inventory_store=inv_store,
        deal_id="test-deal"
    )

    # InventoryStore should have items from deterministic parsing
    apps = inv_store.get_items(inventory_type="application", entity="target")
    assert len(apps) >= 3, f"Expected >=3 app items, got {len(apps)}"

    # Verify bidirectional links
    for item in apps:
        assert item.source_fact_ids, f"Item {item.item_id} has no fact links"
        assert item.deal_id == "test-deal"
        assert item.entity == "target"

def test_parallel_discovery_shared_inventory_store():
    """Parallel discovery should write to a shared InventoryStore."""
    # Requires API key — integration test
    pass

def test_inventory_store_persisted_after_discovery():
    """InventoryStore JSON should exist after discovery completes."""
    # After run, check output/deals/{deal_id}/inventory_store.json exists
    pass
```

### Manual Verification

1. Run `python main_v2.py data/input/Tests/ --all --target-name "TestCo"`
2. Check `output/deals/*/inventory_store.json` exists
3. Verify it contains items: `python -c "import json; d=json.load(open('output/deals/.../inventory_store.json')); print(d['item_count'])"`
4. Verify items have `source_fact_ids` populated
5. In web UI, navigate to `/inventory` — should show non-empty data

---

## Files Modified

| File | Change |
|------|--------|
| `main_v2.py` | Add `inventory_store` param to `run_discovery()`, `run_discovery_for_domain()`, `run_parallel_discovery()`. Create and persist InventoryStore at all 4 entry points. |
| `web/tasks/analysis_tasks.py` | Create InventoryStore in `_analyze_domain()`, pass to agent, save after discovery. |

**Lines of code:** ~40 lines added, ~10 lines modified. Zero deletions.
