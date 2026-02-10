# 02 — LLM Fact Promotion: Convert Unstructured Facts to Inventory Items

## Status: NOT STARTED
## Priority: HIGH (Closes the gap between structured and unstructured extraction)
## Depends On: 01-pipeline-wiring, 03-entity-enforcement
## Enables: 04-ui-inventory-source-switch, 05-reconciliation-and-audit

---

## Overview

After Spec 01, the deterministic parser creates InventoryItems for every table row. But LLM discovery agents extract facts from **unstructured prose** (paragraphs, bullet lists, narratives) — and these facts go only to FactStore, never to InventoryStore.

Example: A document says "The company uses Workday for HR management across 2,000 employees." The LLM extracts this as a Fact (`F-TGT-APP-xxx`) but no InventoryItem is created. If Workday also appears in a table, the deterministic parser creates both. But if it only appears in prose, it's invisible to InventoryStore counts.

**The fix:** After all discovery agents complete, run a promotion step that:
1. Finds LLM-extracted facts that have no `inventory_item_id` (not already linked)
2. Checks InventoryStore for matching items (by fingerprint/name similarity)
3. If match: links fact to existing item (bidirectional)
4. If no match: creates a new InventoryItem from the fact's data

This uses the existing `reconcile_facts_and_inventory()` function in `tools_v2/inventory_integration.py` for matching, extended to also create new items for unmatched facts.

---

## Architecture

```
DISCOVERY PHASE (Spec 01):
  Deterministic Parser → Facts + InventoryItems (linked)
  LLM Agents → Facts only (no inventory_item_id)

PROMOTION PHASE (this spec):
  For each LLM fact without inventory_item_id:
    ├─ Match against InventoryStore by name+vendor similarity
    │   ├─ MATCH FOUND → Link fact ↔ existing item
    │   └─ NO MATCH → Create new InventoryItem from fact data
    └─ Quarantine if fact has insufficient data (no name)

RESULT:
  InventoryStore contains ALL known items:
    - From tables (deterministic parser)
    - From prose (LLM extraction → promotion)
  Every item has source_fact_ids linking back to evidence
  Every fact has inventory_item_id linking to its canonical item
```

---

## Specification

### New Function: `promote_facts_to_inventory()`

**File:** `tools_v2/inventory_integration.py`

**Add after `reconcile_facts_and_inventory()` (after line 394):**

```python
def promote_facts_to_inventory(
    fact_store: FactStore,
    inventory_store: InventoryStore,
    entity: str = "target",
    similarity_threshold: float = 0.8,
) -> Dict[str, Any]:
    """Promote unlinked LLM-extracted facts to InventoryItems.

    After discovery, some facts exist only in FactStore (extracted from
    unstructured prose by LLM agents). This function:
    1. Finds facts without inventory_item_id
    2. Attempts to match against existing InventoryItems
    3. Creates new InventoryItems for unmatched facts
    4. Establishes bidirectional links in all cases

    Args:
        fact_store: FactStore with all discovery facts
        inventory_store: InventoryStore (partially populated by deterministic parser)
        entity: Entity filter ("target" or "buyer")
        similarity_threshold: Minimum similarity for matching (0.0-1.0)

    Returns:
        Dict with promotion statistics:
        - matched: Facts linked to existing InventoryItems
        - promoted: New InventoryItems created from facts
        - quarantined: Facts with insufficient data for promotion
        - skipped: Facts already linked (had inventory_item_id)
        - by_domain: Breakdown by domain
    """
    from difflib import SequenceMatcher
    from stores.id_generator import generate_inventory_id

    stats = {
        "matched": 0,
        "promoted": 0,
        "quarantined": 0,
        "skipped": 0,
        "by_domain": {},
    }

    # Domain → inventory_type mapping
    domain_to_type = {
        "applications": "application",
        "infrastructure": "infrastructure",
        "organization": "organization",
    }

    # Get all entity-scoped facts
    entity_facts = fact_store.get_entity_facts(entity)

    for fact in entity_facts:
        domain = fact.domain

        # Skip domains that don't map to inventory types
        inv_type = domain_to_type.get(domain)
        if not inv_type:
            continue

        # Skip facts that already have an inventory link
        if fact.inventory_item_id:
            stats["skipped"] += 1
            continue

        # Track by domain
        if domain not in stats["by_domain"]:
            stats["by_domain"][domain] = {"matched": 0, "promoted": 0, "quarantined": 0}

        # Extract item name from fact
        item_name = fact.item
        if not item_name or len(item_name.strip()) < 2:
            stats["quarantined"] += 1
            stats["by_domain"][domain]["quarantined"] += 1
            logger.debug(f"Quarantined fact {fact.fact_id}: no usable item name")
            continue

        # Try to match against existing inventory items
        existing_items = inventory_store.get_items(
            inventory_type=inv_type, entity=entity, status="active"
        )

        best_match = None
        best_score = 0.0
        fact_name = item_name.lower().strip()

        for item in existing_items:
            item_name_lower = item.name.lower().strip()
            score = SequenceMatcher(None, fact_name, item_name_lower).ratio()

            # Boost score if vendor also matches (applications only)
            if inv_type == "application":
                fact_vendor = (fact.details or {}).get("vendor", "").lower()
                item_vendor = item.data.get("vendor", "").lower()
                if fact_vendor and item_vendor:
                    vendor_score = SequenceMatcher(None, fact_vendor, item_vendor).ratio()
                    score = (score * 0.7) + (vendor_score * 0.3)

            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score >= similarity_threshold:
            # MATCH FOUND: Link fact to existing item
            fact.inventory_item_id = best_match.item_id
            if fact.fact_id not in best_match.source_fact_ids:
                best_match.source_fact_ids.append(fact.fact_id)

            stats["matched"] += 1
            stats["by_domain"][domain]["matched"] += 1
            logger.debug(
                f"Matched fact {fact.fact_id} -> item {best_match.item_id} "
                f"({best_score:.2f} similarity)"
            )

        else:
            # NO MATCH: Create new InventoryItem from fact
            inv_data = _build_inventory_data_from_fact(fact, inv_type)

            try:
                inv_item_id = inventory_store.add_item(
                    inventory_type=inv_type,
                    entity=entity,
                    data=inv_data,
                    source_file=fact.source_document or "",
                    source_type="discovery",
                    deal_id=fact_store.deal_id,
                )

                # Bidirectional linking
                fact.inventory_item_id = inv_item_id
                inv_item = inventory_store.get_item(inv_item_id)
                if inv_item and fact.fact_id not in inv_item.source_fact_ids:
                    inv_item.source_fact_ids.append(fact.fact_id)

                stats["promoted"] += 1
                stats["by_domain"][domain]["promoted"] += 1
                logger.debug(f"Promoted fact {fact.fact_id} -> new item {inv_item_id}")

            except Exception as e:
                stats["quarantined"] += 1
                stats["by_domain"][domain]["quarantined"] += 1
                logger.warning(f"Failed to promote fact {fact.fact_id}: {e}")

    logger.info(
        f"Fact promotion complete [{entity}]: "
        f"{stats['matched']} matched, {stats['promoted']} promoted, "
        f"{stats['quarantined']} quarantined, {stats['skipped']} skipped"
    )

    return stats


def _build_inventory_data_from_fact(fact, inv_type: str) -> Dict[str, Any]:
    """Build InventoryItem data dict from a Fact's fields.

    Maps fact.item and fact.details to the appropriate schema
    fields for the inventory type.
    """
    details = fact.details or {}

    if inv_type == "application":
        data = {
            "name": fact.item,
            "vendor": details.get("vendor", ""),
            "version": details.get("version", ""),
            "hosting": details.get("deployment", "") or details.get("hosting", ""),
            "users": details.get("user_count", "") or details.get("users", ""),
            "cost": details.get("annual_cost", "") or details.get("cost", ""),
            "criticality": details.get("criticality", ""),
            "category": fact.category or "",
            "source_category": details.get("source_category", ""),
            "category_confidence": details.get("category_confidence", ""),
            "category_inferred_from": details.get("category_inferred_from", ""),
        }
    elif inv_type == "infrastructure":
        data = {
            "name": fact.item,
            "type": details.get("server_type", "") or details.get("type", ""),
            "os": details.get("operating_system", "") or details.get("os", ""),
            "environment": details.get("environment", ""),
            "ip": details.get("ip_address", "") or details.get("ip", ""),
            "location": details.get("location", "") or details.get("datacenter", ""),
            "cpu": details.get("cpu", "") or details.get("cpu_cores", ""),
            "memory": details.get("memory", ""),
            "storage": details.get("storage", ""),
            "role": details.get("role", "") or details.get("function", ""),
        }
    elif inv_type == "organization":
        data = {
            "role": details.get("role", fact.item),
            "name": details.get("person_name", "") or details.get("name", ""),
            "team": details.get("team", ""),
            "department": details.get("department", "IT"),
            "headcount": details.get("headcount", "") or details.get("total_headcount", ""),
            "fte": details.get("fte", ""),
            "location": details.get("location", ""),
            "reports_to": details.get("reports_to", ""),
            "responsibilities": details.get("responsibilities", ""),
        }
    else:
        data = {"name": fact.item}

    # Remove empty values
    return {k: v for k, v in data.items() if v}
```

---

### Integration Point 1: `main_v2.py` — after discovery, before save

**After all discovery domains complete (parallel path — after futures join in `run_parallel_discovery`):**

```python
from tools_v2.inventory_integration import promote_facts_to_inventory

# After parallel discovery completes and facts are merged...

# Promote LLM-extracted facts to inventory items
for entity_val in ["target", "buyer"]:
    promotion_stats = promote_facts_to_inventory(
        fact_store=shared_fact_store,
        inventory_store=shared_inventory_store,
        entity=entity_val,
    )
    if promotion_stats["promoted"] > 0 or promotion_stats["matched"] > 0:
        print(f"[PROMOTION] {entity_val}: {promotion_stats['promoted']} new items, "
              f"{promotion_stats['matched']} matched to existing")

# Save inventory store (now includes both deterministic + promoted items)
shared_inventory_store.save()
```

**Sequential path — after all domains loop:**
Same pattern. Call `promote_facts_to_inventory()` after all `run_discovery()` calls complete, before `inventory_store.save()`.

---

### Integration Point 2: `web/tasks/analysis_tasks.py` — after discovery

**In `run_analysis_task()`, after all domain results are collected (line ~130):**

```python
from tools_v2.inventory_integration import promote_facts_to_inventory
from stores.inventory_store import InventoryStore

# After all domains complete, promote LLM facts to inventory
# Load the deal's inventory store (populated by deterministic parser during discovery)
inv_store = InventoryStore(deal_id=deal_id)

# Rebuild a FactStore from DB facts for promotion
# (since individual domain stores were transient)
combined_fact_store = FactStore(deal_id=deal_id)
all_db_facts = Fact.query.filter_by(deal_id=deal_id, analysis_run_id=run.id).all()
for db_fact in all_db_facts:
    # Reconstruct minimal fact objects for promotion matching
    combined_fact_store.add_fact(
        domain=db_fact.domain,
        category=db_fact.category or "",
        item=db_fact.item or "",
        details=db_fact.details or {},
        status="documented",
        evidence={"exact_quote": db_fact.evidence or ""},
        entity=db_fact.entity or "target",
        source_document=db_fact.source_document or "",
        deal_id=deal_id,
    )

# Run promotion
for entity_val in ["target", "buyer"]:
    promote_facts_to_inventory(
        fact_store=combined_fact_store,
        inventory_store=inv_store,
        entity=entity_val,
    )

inv_store.save()
```

**Note:** This Celery integration is more complex because facts are persisted to DB during discovery, and the FactStore objects are transient per-domain. The promotion step needs a combined view. An alternative simpler approach: make `_analyze_domain()` return the InventoryStore alongside facts, and accumulate across domains. This mirrors the CLI approach more closely.

**Simpler alternative for Celery (recommended):**
In `run_analysis_task()`, create a shared InventoryStore at the top level (like the CLI does), pass it to each `_analyze_domain()` call, and run promotion at the end. This requires `_analyze_domain()` to accept and pass through `inventory_store`, matching the Change 5 in Spec 01.

---

## Benefits

1. **Closes the structured/unstructured gap** — apps mentioned in prose get the same InventoryStore treatment as apps in tables
2. **Deduplicates across extraction methods** — LLM mentions "SAP ECC" in prose, deterministic parser finds it in a table → one InventoryItem with two source_fact_ids
3. **Uses existing reconciliation logic** — SequenceMatcher similarity + vendor boost, same pattern as `reconcile_facts_and_inventory()`
4. **No new data models** — uses existing InventoryItem, existing linking fields, existing InventoryStore methods
5. **Idempotent** — running promotion twice on the same data produces the same result (content-hashed IDs prevent duplicates)

---

## Expectations

After this spec is implemented:

1. An app mentioned only in prose (not in any table) appears in InventoryStore after promotion
2. An app mentioned in both prose and a table results in ONE InventoryItem with TWO source_fact_ids
3. Promotion stats show: `promoted: N` for new items, `matched: M` for deduped items
4. `inventory_store.count(inventory_type="application", entity="target")` returns the true unique count of apps (not inflated by duplicate facts)
5. The buyer entity is promoted separately — buyer apps are not merged with target apps

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Similarity matching creates false positives (merges distinct apps) | Low | Medium | Threshold at 0.8 (80% similarity). Vendor-boosted scoring further reduces false positives. Start conservative; lower threshold only if recall is insufficient. |
| Similarity matching creates false negatives (creates duplicate items) | Medium | Low | Duplicate items are better than merged-wrong items. Content-hashed IDs mean re-running produces the same items. Can reconcile later. |
| Performance on large fact sets (500+ facts) | Low | Low | SequenceMatcher is O(n*m) per comparison, but n (unlinked facts) * m (inventory items) is typically < 10,000 comparisons. Sub-second. |
| Celery integration complexity (reconstructing FactStore from DB) | Medium | Medium | Use the simpler approach: pass shared InventoryStore through `_analyze_domain()`. Matches CLI pattern. |
| LLM facts with vague names ("the ERP system") promoted as items | Medium | Low | These create items with generic names. The quarantine check (name length < 2) catches the worst cases. Future: add a confidence threshold. |

---

## Results Criteria

### Automated Tests

```python
def test_promotion_creates_items_from_unlinked_facts():
    """Facts without inventory_item_id should be promoted to InventoryItems."""
    from tools_v2.inventory_integration import promote_facts_to_inventory

    fact_store = FactStore(deal_id="test-deal")
    inv_store = InventoryStore(deal_id="test-deal")

    # Add a fact with no inventory link (simulating LLM extraction)
    fact_store.add_fact(
        domain="applications", category="erp", item="Workday",
        details={"vendor": "Workday Inc", "deployment": "SaaS"},
        status="documented",
        evidence={"exact_quote": "The company uses Workday for HR"},
        entity="target", deal_id="test-deal",
    )

    stats = promote_facts_to_inventory(fact_store, inv_store, entity="target")

    assert stats["promoted"] == 1
    apps = inv_store.get_items(inventory_type="application", entity="target")
    assert len(apps) == 1
    assert apps[0].name == "Workday"
    assert len(apps[0].source_fact_ids) == 1

def test_promotion_matches_existing_items():
    """Facts should match existing InventoryItems by name similarity."""
    from tools_v2.inventory_integration import promote_facts_to_inventory

    fact_store = FactStore(deal_id="test-deal")
    inv_store = InventoryStore(deal_id="test-deal")

    # Pre-existing inventory item (from deterministic parser)
    inv_store.add_item(
        inventory_type="application", entity="target",
        data={"name": "Salesforce CRM", "vendor": "Salesforce"},
        deal_id="test-deal",
    )

    # LLM fact mentioning same app with slightly different name
    fact_store.add_fact(
        domain="applications", category="crm", item="Salesforce",
        details={"vendor": "Salesforce"},
        status="documented",
        evidence={"exact_quote": "Salesforce is used for sales tracking"},
        entity="target", deal_id="test-deal",
    )

    stats = promote_facts_to_inventory(fact_store, inv_store, entity="target")

    assert stats["matched"] == 1
    assert stats["promoted"] == 0
    # Still only 1 item (not duplicated)
    apps = inv_store.get_items(inventory_type="application", entity="target")
    assert len(apps) == 1
    # But now has a fact link
    assert len(apps[0].source_fact_ids) == 1

def test_promotion_does_not_merge_across_entities():
    """Target and buyer items must remain separate."""
    from tools_v2.inventory_integration import promote_facts_to_inventory

    fact_store = FactStore(deal_id="test-deal")
    inv_store = InventoryStore(deal_id="test-deal")

    # Target item
    inv_store.add_item(
        inventory_type="application", entity="target",
        data={"name": "SAP ECC", "vendor": "SAP"},
        deal_id="test-deal",
    )

    # Buyer fact mentioning same app
    fact_store.add_fact(
        domain="applications", category="erp", item="SAP S/4HANA",
        details={"vendor": "SAP"},
        status="documented",
        evidence={"exact_quote": "Buyer runs SAP S/4HANA"},
        entity="buyer", deal_id="test-deal",
    )

    stats = promote_facts_to_inventory(fact_store, inv_store, entity="buyer")

    # Should create new item (not match target's SAP)
    assert stats["promoted"] == 1
    buyer_apps = inv_store.get_items(inventory_type="application", entity="buyer")
    assert len(buyer_apps) == 1
    target_apps = inv_store.get_items(inventory_type="application", entity="target")
    assert len(target_apps) == 1  # Unchanged
```

### Manual Verification

1. Run full discovery on a test document
2. Check `inventory_store.json` — count items
3. Compare with fact count: `inventory items <= facts` (deduplication working)
4. Verify items from prose (non-table mentions) appear in inventory
5. Check `source_fact_ids` — items from tables have 1+ facts, items from prose have 1 fact

---

## Files Modified

| File | Change |
|------|--------|
| `tools_v2/inventory_integration.py` | Add `promote_facts_to_inventory()` and `_build_inventory_data_from_fact()` functions |
| `main_v2.py` | Call promotion after discovery completes (both parallel and sequential paths) |
| `web/tasks/analysis_tasks.py` | Call promotion after all domain analyses complete |

**Lines of code:** ~180 lines added (promotion function + integration points). Zero deletions.
