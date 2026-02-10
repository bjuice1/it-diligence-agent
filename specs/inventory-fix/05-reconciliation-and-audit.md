# 05 — Reconciliation & Audit: Post-Discovery Integrity Gate

## Status: NOT STARTED
## Priority: MEDIUM (Ensures data quality and provides operational visibility)
## Depends On: 01-pipeline-wiring, 02-llm-fact-promotion, 03-entity-enforcement
## Enables: Confidence in inventory counts, debugging of missing items

---

## Overview

After Specs 01-04, the pipeline creates InventoryItems (deterministic + LLM-promoted), enforces entity scoping, and displays deduplicated counts in the UI. But there is no **post-discovery integrity check** — no way to know if items were lost, duplicated across stores, or if LLM promotion missed candidates.

**The fix:** Wire `reconcile_facts_and_inventory()` (already exists in `inventory_integration.py:319`) into the post-discovery flow, add a per-run inventory audit report, and surface discrepancies to operators.

The good news: `reconcile_facts_and_inventory()` already implements name+vendor similarity matching with configurable threshold (0.8 default). `sync_inventory_to_facts()` (line 225) already handles bidirectional linking. `get_inventory_summary()` (line 485) already produces summary stats. We just need to orchestrate them and persist the results.

---

## Architecture

```
BEFORE (current):
  Discovery completes
    → Facts saved to DB
    → InventoryStore saved to JSON (after Spec 01)
    → No reconciliation, no audit
    → Operator has no visibility into data quality

AFTER (fixed):
  Discovery completes
    → Facts saved to DB
    → InventoryStore saved to JSON
    → reconcile_facts_and_inventory() runs  ← LINKS UNMATCHED ITEMS
    → generate_inventory_audit() runs       ← PRODUCES AUDIT REPORT
    → Audit report saved to JSON            ← OPERATOR VISIBILITY
    → Discrepancies logged with details     ← DEBUGGING SUPPORT
```

---

## Specification

### Change 1: Post-discovery reconciliation hook in `main_v2.py`

**Add after InventoryStore save (after the save added by Spec 01):**

```python
from tools_v2.inventory_integration import reconcile_facts_and_inventory

# Reconcile unlinked facts and inventory items
reconcile_stats = reconcile_facts_and_inventory(
    fact_store=fact_store,
    inventory_store=inventory_store,
    entity="target",
    similarity_threshold=0.8,
)
logger.info(
    f"Reconciliation: {reconcile_stats['matched']} matched, "
    f"{reconcile_stats['unmatched_facts']} unmatched facts, "
    f"{reconcile_stats['unmatched_items']} unmatched items"
)

# Repeat for buyer entity if present
buyer_items = inventory_store.get_items(entity="buyer")
if buyer_items:
    buyer_stats = reconcile_facts_and_inventory(
        fact_store=fact_store,
        inventory_store=inventory_store,
        entity="buyer",
        similarity_threshold=0.8,
    )
    logger.info(f"Buyer reconciliation: {buyer_stats['matched']} matched")

# Re-save after reconciliation (links were updated)
inventory_store.save()
```

**Same hook in `web/tasks/analysis_tasks.py:_analyze_domain()`:**

```python
# After inventory_store.save() (added by Spec 01)
from tools_v2.inventory_integration import reconcile_facts_and_inventory

reconcile_stats = reconcile_facts_and_inventory(
    fact_store=fact_store,
    inventory_store=inventory_store,
    entity="target",
    similarity_threshold=0.8,
)
logger.info(f"Reconciliation for {domain}: {reconcile_stats}")
inventory_store.save()  # Re-save with updated links
```

---

### Change 2: New function `generate_inventory_audit()` in `tools_v2/inventory_integration.py`

**Add after `get_inventory_summary()` (after line 539):**

```python
def generate_inventory_audit(
    inventory_store: InventoryStore,
    fact_store: FactStore,
    deal_id: str = "",
) -> Dict[str, Any]:
    """Generate a comprehensive inventory audit report for a discovery run.

    Checks:
    1. Item counts by type and entity
    2. Linking coverage (facts with inventory links, items with fact links)
    3. Orphaned facts (no inventory item match)
    4. Orphaned items (no fact links)
    5. Duplicate detection (same name+entity, different IDs)
    6. Entity distribution (target vs buyer)
    7. Data completeness (missing required fields)

    Args:
        inventory_store: The InventoryStore to audit
        fact_store: The FactStore to cross-reference
        deal_id: Deal identifier for the report

    Returns:
        Dict containing the full audit report
    """
    report = {
        "deal_id": deal_id,
        "generated_at": _now_iso(),
        "inventory_counts": {},
        "fact_counts": {},
        "linking": {},
        "orphans": {},
        "duplicates": [],
        "data_quality": {},
        "overall_health": "unknown",
        "issues": [],
    }

    # 1. Inventory counts by type and entity
    for entity in ["target", "buyer"]:
        entity_counts = {}
        for inv_type in ["application", "infrastructure", "organization", "vendor"]:
            items = inventory_store.get_items(
                inventory_type=inv_type, entity=entity, status="active"
            )
            entity_counts[inv_type] = len(items)
        report["inventory_counts"][entity] = entity_counts

    # 2. Fact counts by domain and entity
    for entity in ["target", "buyer"]:
        entity_facts = {}
        for domain in ["applications", "infrastructure", "organization"]:
            facts = fact_store.get_entity_facts(entity, domain=domain)
            entity_facts[domain] = len(facts)
        report["fact_counts"][entity] = entity_facts

    # 3. Linking coverage
    all_items = inventory_store.get_items(status="active")
    linked_items = [i for i in all_items if i.source_fact_ids]
    unlinked_items = [i for i in all_items if not i.source_fact_ids]

    all_facts = fact_store.get_entity_facts("target")
    linked_facts = [f for f in all_facts if hasattr(f, 'inventory_item_id') and f.inventory_item_id]
    unlinked_facts = [f for f in all_facts if not (hasattr(f, 'inventory_item_id') and f.inventory_item_id)]

    report["linking"] = {
        "total_items": len(all_items),
        "linked_items": len(linked_items),
        "unlinked_items": len(unlinked_items),
        "item_link_rate": _safe_pct(len(linked_items), len(all_items)),
        "total_facts": len(all_facts),
        "linked_facts": len(linked_facts),
        "unlinked_facts": len(unlinked_facts),
        "fact_link_rate": _safe_pct(len(linked_facts), len(all_facts)),
    }

    # 4. Orphaned items (no fact links and no enrichment — possibly stale)
    orphan_items = [
        {"item_id": i.item_id, "name": i.name, "type": i.inventory_type, "entity": i.entity}
        for i in unlinked_items
        if not i.is_enriched
    ]
    report["orphans"] = {
        "items": orphan_items[:20],  # Cap at 20 for readability
        "item_count": len(orphan_items),
        "fact_count": len(unlinked_facts),
    }

    # 5. Duplicate detection (same name+entity, different IDs)
    seen = {}
    for item in all_items:
        key = (item.name.lower().strip(), item.entity, item.inventory_type)
        if key in seen:
            report["duplicates"].append({
                "name": item.name,
                "entity": item.entity,
                "type": item.inventory_type,
                "id_a": seen[key],
                "id_b": item.item_id,
            })
        else:
            seen[key] = item.item_id

    # 6. Data quality — check for missing required fields
    quality_issues = []
    for item in all_items:
        missing = []
        if not item.name or item.name == "Unknown":
            missing.append("name")
        if item.inventory_type == "application":
            if not item.data.get("vendor"):
                missing.append("vendor")
        elif item.inventory_type == "infrastructure":
            if not item.data.get("environment"):
                missing.append("environment")
        elif item.inventory_type == "organization":
            if not item.data.get("role"):
                missing.append("role")

        if missing:
            quality_issues.append({
                "item_id": item.item_id,
                "name": item.name,
                "missing_fields": missing,
            })

    report["data_quality"] = {
        "items_with_missing_fields": len(quality_issues),
        "details": quality_issues[:20],  # Cap for readability
    }

    # 7. Overall health assessment
    issues = []
    if report["linking"]["item_link_rate"] < 50:
        issues.append(f"Low item link rate: {report['linking']['item_link_rate']}%")
    if len(report["duplicates"]) > 0:
        issues.append(f"{len(report['duplicates'])} duplicate items detected")
    if report["orphans"]["item_count"] > 10:
        issues.append(f"{report['orphans']['item_count']} orphaned items (no fact links)")
    if report["data_quality"]["items_with_missing_fields"] > 5:
        issues.append(f"{report['data_quality']['items_with_missing_fields']} items missing required fields")

    report["issues"] = issues
    if not issues:
        report["overall_health"] = "healthy"
    elif len(issues) <= 2:
        report["overall_health"] = "fair"
    else:
        report["overall_health"] = "needs_attention"

    return report


def save_inventory_audit(
    report: Dict[str, Any],
    deal_id: str = "",
    output_dir: str = "",
) -> str:
    """Save inventory audit report to JSON file.

    Args:
        report: Audit report dict from generate_inventory_audit()
        deal_id: Deal ID for path construction
        output_dir: Override output directory (default: output/deals/{deal_id}/)

    Returns:
        Path to the saved report file
    """
    import json
    from pathlib import Path

    if not output_dir:
        output_dir = f"output/deals/{deal_id}" if deal_id else "output"

    path = Path(output_dir) / "inventory_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Saved inventory audit to {path}")
    return str(path)


def _safe_pct(numerator: int, denominator: int) -> float:
    """Calculate percentage safely."""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _now_iso() -> str:
    """Current datetime as ISO string."""
    from datetime import datetime
    return datetime.now().isoformat()
```

---

### Change 3: Wire audit into post-discovery flow in `main_v2.py`

**Add after reconciliation (Change 1), before function return:**

```python
from tools_v2.inventory_integration import generate_inventory_audit, save_inventory_audit

# Generate and save audit report
audit_report = generate_inventory_audit(
    inventory_store=inventory_store,
    fact_store=fact_store,
    deal_id=effective_deal_id,
)
audit_path = save_inventory_audit(
    audit_report,
    deal_id=effective_deal_id,
)
logger.info(
    f"Inventory audit: {audit_report['overall_health']} — "
    f"{audit_report['linking']['total_items']} items, "
    f"{audit_report['linking']['item_link_rate']}% linked"
)
if audit_report["issues"]:
    for issue in audit_report["issues"]:
        logger.warning(f"Audit issue: {issue}")
```

**Same in `web/tasks/analysis_tasks.py:_analyze_domain()`:**

```python
from tools_v2.inventory_integration import generate_inventory_audit, save_inventory_audit

audit_report = generate_inventory_audit(
    inventory_store=inventory_store,
    fact_store=fact_store,
    deal_id=deal_id,
)
save_inventory_audit(audit_report, deal_id=deal_id)
logger.info(f"Domain {domain} audit: {audit_report['overall_health']}")
```

---

### Change 4: Extend `reconcile_facts_and_inventory()` to all domains

**Current limitation:** `reconcile_facts_and_inventory()` (line 319) only matches `applications` domain facts to `application` inventory items.

**Extend to infrastructure and organization:**

```python
def reconcile_facts_and_inventory(
    fact_store: FactStore,
    inventory_store: InventoryStore,
    entity: str = "target",
    similarity_threshold: float = 0.8,
) -> Dict[str, int]:
    """Match unlinked facts to inventory items by name similarity.

    Extended to cover all domains — not just applications.
    """
    from difflib import SequenceMatcher

    stats = {"matched": 0, "unmatched_facts": 0, "unmatched_items": 0}

    # Domain → inventory type mapping
    domain_type_pairs = [
        ("applications", "application"),
        ("infrastructure", "infrastructure"),
        ("organization", "organization"),
    ]

    for domain, inv_type in domain_type_pairs:
        domain_facts = [
            f for f in fact_store.get_entity_facts(entity, domain=domain)
            if not getattr(f, 'inventory_item_id', None)
        ]

        domain_items = [
            item for item in inventory_store.get_items(
                inventory_type=inv_type, entity=entity
            )
            if not item.source_fact_ids
        ]

        matched_item_ids = set()
        for fact in domain_facts:
            fact_name = fact.item.lower().strip()
            best_match = None
            best_score = 0.0

            for item in domain_items:
                if item.item_id in matched_item_ids:
                    continue

                item_name = item.name.lower().strip()
                score = SequenceMatcher(None, fact_name, item_name).ratio()

                # Boost score if secondary field also matches
                if inv_type == "application":
                    fact_vendor = fact.details.get("vendor", "").lower()
                    item_vendor = item.data.get("vendor", "").lower()
                    if fact_vendor and item_vendor:
                        vendor_score = SequenceMatcher(None, fact_vendor, item_vendor).ratio()
                        score = (score * 0.7) + (vendor_score * 0.3)
                elif inv_type == "infrastructure":
                    fact_env = fact.details.get("environment", "").lower()
                    item_env = item.data.get("environment", "").lower()
                    if fact_env and item_env:
                        env_score = SequenceMatcher(None, fact_env, item_env).ratio()
                        score = (score * 0.7) + (env_score * 0.3)

                if score > best_score:
                    best_score = score
                    best_match = item

            if best_match and best_score >= similarity_threshold:
                fact.inventory_item_id = best_match.item_id
                if fact.fact_id not in best_match.source_fact_ids:
                    best_match.source_fact_ids.append(fact.fact_id)
                matched_item_ids.add(best_match.item_id)
                stats["matched"] += 1
            else:
                stats["unmatched_facts"] += 1

        stats["unmatched_items"] += len(domain_items) - len(matched_item_ids)

    return stats
```

---

### Change 5: Audit report accessible in web UI

**Add route in `web/app.py` (near existing `/inventory` route):**

```python
@app.route('/inventory/audit')
def inventory_audit():
    """Display the inventory audit report for the current deal."""
    current_deal_id = flask_session.get('current_deal_id')
    if not current_deal_id:
        return render_template('inventory/audit.html', report=None)

    audit_path = Path(f"output/deals/{current_deal_id}/inventory_audit.json")
    if audit_path.exists():
        with open(audit_path) as f:
            report = json.load(f)
    else:
        report = None

    return render_template('inventory/audit.html', report=report)
```

**Template `web/templates/inventory/audit.html`:**

```html
{% extends "base.html" %}
{% block content %}
<h2>Inventory Audit Report</h2>

{% if not report %}
<div class="alert alert-info">No audit report available. Run analysis first.</div>
{% else %}

<div class="audit-health {{ report.overall_health }}">
    <strong>Overall Health:</strong> {{ report.overall_health | upper }}
    <span class="timestamp">Generated: {{ report.generated_at }}</span>
</div>

{% if report.issues %}
<div class="audit-issues">
    <h4>Issues</h4>
    <ul>
    {% for issue in report.issues %}
        <li class="issue-item">{{ issue }}</li>
    {% endfor %}
    </ul>
</div>
{% endif %}

<div class="audit-section">
    <h4>Inventory Counts</h4>
    <table class="table">
        <thead>
            <tr><th>Type</th><th>Target</th><th>Buyer</th></tr>
        </thead>
        <tbody>
        {% for inv_type in ['application', 'infrastructure', 'organization', 'vendor'] %}
            <tr>
                <td>{{ inv_type | capitalize }}</td>
                <td>{{ report.inventory_counts.target[inv_type] | default(0) }}</td>
                <td>{{ report.inventory_counts.buyer[inv_type] | default(0) }}</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
</div>

<div class="audit-section">
    <h4>Linking Coverage</h4>
    <table class="table">
        <tr><td>Total Items</td><td>{{ report.linking.total_items }}</td></tr>
        <tr><td>Linked Items</td><td>{{ report.linking.linked_items }} ({{ report.linking.item_link_rate }}%)</td></tr>
        <tr><td>Total Facts</td><td>{{ report.linking.total_facts }}</td></tr>
        <tr><td>Linked Facts</td><td>{{ report.linking.linked_facts }} ({{ report.linking.fact_link_rate }}%)</td></tr>
    </table>
</div>

{% if report.duplicates %}
<div class="audit-section">
    <h4>Duplicates Detected ({{ report.duplicates | length }})</h4>
    <table class="table">
        <thead><tr><th>Name</th><th>Entity</th><th>Type</th><th>ID A</th><th>ID B</th></tr></thead>
        <tbody>
        {% for dup in report.duplicates %}
            <tr>
                <td>{{ dup.name }}</td>
                <td>{{ dup.entity }}</td>
                <td>{{ dup.type }}</td>
                <td><code>{{ dup.id_a }}</code></td>
                <td><code>{{ dup.id_b }}</code></td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% endif %}
{% endblock %}
```

---

## Benefits

1. **Catches missing links** — unlinked facts and items are identified and matched post-discovery
2. **Operator visibility** — audit report shows exact counts, link rates, duplicates, and data quality
3. **Per-run persistence** — `inventory_audit.json` is saved alongside `inventory_store.json` for each deal
4. **Multi-domain reconciliation** — extends beyond applications to infrastructure and organization
5. **Zero manual effort** — runs automatically after discovery, results accessible via `/inventory/audit`

---

## Expectations

After this spec is implemented:

1. After discovery, `output/deals/{deal_id}/inventory_audit.json` is created automatically
2. The audit report shows linking coverage (% of items with fact links, % of facts with item links)
3. `reconcile_facts_and_inventory()` matches across all three domains (apps, infra, org), not just applications
4. Duplicate items (same name+entity+type with different IDs) are detected and reported
5. Items with missing required fields are flagged
6. `/inventory/audit` route displays the report in the web UI
7. Logger warnings fire for any audit issues (low link rate, duplicates, orphans)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Reconciliation creates false matches (low similarity threshold) | Low | Medium | Default threshold is 0.8 (strict). Vendor/environment boost only applies when both fields exist. Log all matches for review. |
| Audit report adds latency to discovery | Low | Low | `generate_inventory_audit()` is O(n) over items and facts. Typical deal has <500 total. Sub-second. |
| Per-domain Celery tasks produce multiple audit files | Medium | Low | Each `_analyze_domain()` writes to same `inventory_audit.json`. Last domain to finish overwrites. Acceptable — final audit is most complete. |
| Template doesn't exist yet | Low | Low | Create minimal template. Can be enhanced later. |

---

## Results Criteria

### Automated Tests

```python
def test_reconciliation_links_unmatched():
    """Reconciliation should link unmatched facts to matching inventory items."""
    fact_store = FactStore(deal_id="test")
    inv_store = InventoryStore(deal_id="test")

    # Add unlinked fact
    fact_store.add_fact(
        domain="applications", category="saas",
        item="Salesforce CRM", details={"vendor": "Salesforce"},
        entity="target",
    )

    # Add unlinked inventory item
    inv_store.add_item(
        inventory_type="application", entity="target",
        data={"name": "Salesforce CRM", "vendor": "Salesforce"},
        deal_id="test",
    )

    stats = reconcile_facts_and_inventory(fact_store, inv_store, entity="target")
    assert stats["matched"] == 1
    assert stats["unmatched_facts"] == 0

def test_audit_report_generated():
    """Audit report should contain all required sections."""
    fact_store = FactStore(deal_id="test")
    inv_store = InventoryStore(deal_id="test")
    inv_store.add_item(
        inventory_type="application", entity="target",
        data={"name": "TestApp", "vendor": "TestCo"},
        deal_id="test",
    )

    report = generate_inventory_audit(inv_store, fact_store, deal_id="test")
    assert report["deal_id"] == "test"
    assert "inventory_counts" in report
    assert "linking" in report
    assert "overall_health" in report
    assert report["inventory_counts"]["target"]["application"] == 1

def test_duplicate_detection():
    """Audit should detect duplicate items with same name+entity."""
    inv_store = InventoryStore(deal_id="test")
    # Manually add two items with same name (bypassing dedup for test)
    from stores.inventory_item import InventoryItem
    item1 = InventoryItem(
        item_id="I-APP-aaaaaa", inventory_type="application",
        entity="target", data={"name": "Salesforce", "vendor": "SFDC"},
        deal_id="test",
    )
    item2 = InventoryItem(
        item_id="I-APP-bbbbbb", inventory_type="application",
        entity="target", data={"name": "Salesforce", "vendor": "Salesforce Inc"},
        deal_id="test",
    )
    inv_store._items[item1.item_id] = item1
    inv_store._items[item2.item_id] = item2

    report = generate_inventory_audit(inv_store, FactStore(deal_id="test"), deal_id="test")
    assert len(report["duplicates"]) == 1
```

### Manual Verification

1. Run analysis on a test document
2. Check `output/deals/{deal_id}/inventory_audit.json` exists
3. Verify linking coverage percentages are reasonable (>50% for linked items)
4. Navigate to `/inventory/audit` in web UI — verify report displays
5. Check logs for reconciliation stats and any audit warnings

---

## Files Modified

| File | Change |
|------|--------|
| `tools_v2/inventory_integration.py` | Add `generate_inventory_audit()`, `save_inventory_audit()`, `_safe_pct()`, `_now_iso()`. Extend `reconcile_facts_and_inventory()` to all domains. |
| `main_v2.py` | Wire reconciliation + audit after InventoryStore save (all entry points) |
| `web/tasks/analysis_tasks.py` | Wire reconciliation + audit after `_analyze_domain()` save |
| `web/app.py` | Add `/inventory/audit` route |
| `web/templates/inventory/audit.html` | New template for audit report display |

**Lines of code:** ~180 lines added (audit functions), ~30 lines modified (reconciliation extension), ~50 lines template.
