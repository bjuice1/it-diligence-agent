# 03 — Entity Enforcement & Organization Table Parser

## Status: NOT STARTED
## Priority: HIGH (Data quality + Org inventory gap)
## Depends On: Nothing (parallel with 01)
## Enables: 02-llm-fact-promotion, 04-ui-inventory-source-switch

---

## Overview

Two independent data quality issues addressed in one spec because they share the same files:

**Issue A — Silent entity default (Audit Finding 3):** The `create_inventory_entry` tool in `discovery_tools.py` defaults entity to `"target"` when the LLM omits it (line 516). This contradicts the `flag_gap` tool which correctly rejects missing entity (lines 667-672). A buyer fact can silently become a target fact.

**Issue B — No organization table parser (Audit Finding 4):** The deterministic parser handles application tables (`_app_table_to_facts`), infrastructure tables (`_infra_table_to_facts`), and contract tables (`_contract_table_to_facts`). There is no `_org_table_to_facts()`. Organization data only enters as LLM-extracted Facts, never as InventoryItems — even when source documents contain structured org tables (Team Summary, Role Breakdown, etc.).

---

## Architecture

### Issue A: Entity Flow

```
BEFORE:
  LLM calls create_inventory_entry(domain="applications", item="Salesforce")
  → entity not in tool_input
  → entity = input_data.get("entity", "target")  ← SILENT DEFAULT
  → fact created with entity="target" even if from buyer doc

AFTER:
  LLM calls create_inventory_entry(domain="applications", item="Salesforce")
  → entity not in tool_input
  → REJECTED with error message requiring explicit entity
  → LLM retries with entity="buyer"
```

### Issue B: Org Table Detection

```
BEFORE:
  | Team | Headcount | FTE | Location | Reports To |
  |------|-----------|-----|----------|------------|
  | Applications | 12 | 10.5 | NYC | VP IT |

  → detect_table_type() returns "unknown"
  → table skipped
  → LLM extracts these as unstructured Facts (if it notices them)

AFTER:
  → detect_table_type() returns "organization_inventory"
  → _org_table_to_facts() processes each row
  → Creates Fact + InventoryItem (inventory_type="organization")
  → Row above becomes: I-ORG-{hash} with role="Applications Team", headcount=12
```

---

## Specification

### Change 1: Fix entity default in `create_inventory_entry`

**File:** `tools_v2/discovery_tools.py`

**Current code (line 516):**
```python
entity = input_data.get("entity", "target")  # Default to target if not specified
```

**New code:**
```python
entity = input_data.get("entity")
if entity is None:
    logger.warning(f"REJECTED create_inventory_entry: entity not specified for '{input_data.get('item', 'unknown')}'")
    return {
        "status": "error",
        "reason": "missing_entity",
        "message": "Entity is REQUIRED for create_inventory_entry. Must be 'target' or 'buyer'. "
                   "Check the document source — target_profile docs → entity='target', "
                   "buyer_profile docs → entity='buyer'. Do not omit this field."
    }
```

**Validation block (lines 543-551) is already correct** — it rejects invalid entity values. This change ensures missing entity is also rejected, not silently defaulted.

**Impact analysis:** The tool schema at line 266 already lists `"entity"` in the `"required"` array:
```python
"required": ["domain", "category", "item", "entity", "status", "evidence"]
```
The Anthropic API enforces required fields in tool calls, so the LLM should always include entity. This change is a defense-in-depth guard for edge cases where the LLM malforms the tool call or the field is stripped.

---

### Change 2: Add organization table headers to deterministic parser

**File:** `tools_v2/deterministic_parser.py`

**Add after line 65 (after CONTRACT_HEADERS):**
```python
# Column headers that indicate organization/staffing table
ORG_INVENTORY_HEADERS = {
    "team", "team name", "department", "group", "function",
    "role", "title", "job title", "position",
    "headcount", "hc", "head count", "fte", "ftes",
    "reports to", "reporting to", "manager", "reports",
    "location", "office", "site",
    "responsibilities", "scope", "focus area",
    "name", "lead", "leader", "director", "vp",
}
```

---

### Change 3: Update `detect_table_type()` to recognize org tables

**File:** `tools_v2/deterministic_parser.py`

**Current code (line 271-294):**
```python
def detect_table_type(table: ParsedTable) -> str:
    headers_lower = {h.lower() for h in table.headers if h}

    app_score = len(headers_lower & APP_INVENTORY_HEADERS)
    infra_score = len(headers_lower & INFRA_INVENTORY_HEADERS)
    contract_score = len(headers_lower & CONTRACT_HEADERS)

    if app_score >= 3 and app_score > infra_score and app_score > contract_score:
        return "application_inventory"
    elif infra_score >= 3 and infra_score > app_score:
        return "infrastructure_inventory"
    elif contract_score >= 3:
        return "contract_inventory"

    return "unknown"
```

**New code:**
```python
def detect_table_type(table: ParsedTable) -> str:
    headers_lower = {h.lower() for h in table.headers if h}

    app_score = len(headers_lower & APP_INVENTORY_HEADERS)
    infra_score = len(headers_lower & INFRA_INVENTORY_HEADERS)
    contract_score = len(headers_lower & CONTRACT_HEADERS)
    org_score = len(headers_lower & ORG_INVENTORY_HEADERS)

    # Score-based classification with priority ordering
    scores = {
        "application_inventory": app_score,
        "infrastructure_inventory": infra_score,
        "contract_inventory": contract_score,
        "organization_inventory": org_score,
    }

    # Find highest scoring type with minimum threshold of 3
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score >= 3:
        return best_type

    return "unknown"
```

---

### Change 4: Add `_org_table_to_facts()` function

**File:** `tools_v2/deterministic_parser.py`

**Add after `_contract_table_to_facts()` (after line 727):**

```python
def _org_table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str,
    source_document: str,
    inventory_store: Optional["InventoryStore"] = None,
) -> int:
    """Convert organization/staffing table to facts (and optionally inventory items).

    Handles tables with team/role data: Team Summary, Role Breakdown,
    IT Org Structure, Staffing tables.
    """
    facts_created = 0

    header_mapping = {
        # Team/group identifiers
        "team": "item",
        "team name": "item",
        "department": "item",
        "group": "item",
        "function": "item",
        # Role identifiers (if team not present)
        "role": "role",
        "title": "role",
        "job title": "role",
        "position": "role",
        # Person name
        "name": "person_name",
        "lead": "person_name",
        "leader": "person_name",
        "director": "person_name",
        "vp": "person_name",
        # Staffing numbers
        "headcount": "headcount",
        "hc": "headcount",
        "head count": "headcount",
        "fte": "fte",
        "ftes": "fte",
        # Reporting
        "reports to": "reports_to",
        "reporting to": "reports_to",
        "manager": "reports_to",
        "reports": "reports_to",
        # Other
        "location": "location",
        "office": "location",
        "site": "location",
        "responsibilities": "responsibilities",
        "scope": "responsibilities",
        "focus area": "responsibilities",
    }

    for row in table.rows:
        # Find the team/role name (primary identifier)
        item_name = None

        # Priority: team name > role > person name
        for header in ["team", "team name", "department", "group", "function"]:
            if header in row and row[header]:
                item_name = row[header]
                break

        if not item_name:
            for header in ["role", "title", "job title", "position"]:
                if header in row and row[header]:
                    item_name = row[header]
                    break

        if not item_name:
            for header in ["name", "lead", "leader"]:
                if header in row and row[header]:
                    item_name = row[header]
                    break

        if not item_name:
            logger.warning(f"Skipping org row without identifiable name: {row}")
            continue

        # Build details
        details = {}
        for header, value in row.items():
            if not value:
                continue
            std_field = header_mapping.get(header.lower(), header.lower().replace(" ", "_"))
            if std_field == "item":
                continue  # Skip the name field itself
            # Normalize numeric fields
            if std_field in ("headcount", "fte"):
                normalized = _normalize_numeric(value)
                if normalized is not None:
                    details[std_field] = normalized
            else:
                details[std_field] = value

        # Determine category based on content
        category = "central_it"  # Default
        item_lower = item_name.lower()
        if any(kw in item_lower for kw in ["leader", "cio", "cto", "vp", "director", "head of"]):
            category = "leadership"
        elif any(kw in item_lower for kw in ["outsourc", "msp", "managed service", "contractor"]):
            category = "outsourcing"
        elif any(kw in item_lower for kw in ["embed", "shadow", "business"]):
            category = "embedded_it"

        evidence = {
            "exact_quote": f"{item_name} | HC: {details.get('headcount', 'N/A')} | FTE: {details.get('fte', 'N/A')}",
            "source_section": "Organization/Staffing Table"
        }

        try:
            fact_id = fact_store.add_fact(
                domain="organization",
                category=category,
                item=item_name,
                details=details,
                status="documented",
                evidence=evidence,
                entity=entity,
                source_document=source_document,
                needs_review=False,
            )
            facts_created += 1
            logger.debug(f"Created org fact {fact_id}: {item_name}")

            # Create inventory item if store available (Spec 03 linking)
            if inventory_store is not None and fact_id:
                try:
                    inv_data = {
                        "role": details.get("role", item_name),
                        "name": details.get("person_name", ""),
                        "team": item_name if category == "central_it" else "",
                        "department": "IT",
                        "headcount": details.get("headcount", ""),
                        "fte": details.get("fte", ""),
                        "location": details.get("location", ""),
                        "reports_to": details.get("reports_to", ""),
                        "responsibilities": details.get("responsibilities", ""),
                    }
                    # Remove empty values
                    inv_data = {k: v for k, v in inv_data.items() if v}

                    # Ensure required 'role' field is present
                    if "role" not in inv_data:
                        inv_data["role"] = item_name

                    inv_item_id = inventory_store.add_item(
                        inventory_type="organization",
                        entity=entity,
                        data=inv_data,
                        source_file=source_document,
                        source_type="discovery",
                        deal_id=fact_store.deal_id,
                    )

                    # Bidirectional linking
                    if inv_item_id:
                        fact = fact_store.get_fact(fact_id)
                        if fact:
                            fact.inventory_item_id = inv_item_id
                        inv_item = inventory_store.get_item(inv_item_id)
                        if inv_item:
                            if fact_id not in inv_item.source_fact_ids:
                                inv_item.source_fact_ids.append(fact_id)
                        logger.debug(f"Linked org fact {fact_id} <-> inventory {inv_item_id}")

                except Exception as inv_e:
                    logger.warning(f"Failed to create org inventory item for {item_name}: {inv_e}")

        except Exception as e:
            logger.error(f"Failed to create org fact for {item_name}: {e}")

    return facts_created
```

---

### Change 5: Wire org parser into `table_to_facts()` dispatch

**File:** `tools_v2/deterministic_parser.py`

**Current code (line 301-331):**
```python
def table_to_facts(table, fact_store, entity, source_document, inventory_store):
    table_type = detect_table_type(table)

    if table_type == "application_inventory":
        return _app_table_to_facts(...)
    elif table_type == "infrastructure_inventory":
        return _infra_table_to_facts(...)
    elif table_type == "contract_inventory":
        return _contract_table_to_facts(...)
    else:
        logger.warning(f"Unknown table type...")
        return 0
```

**New code — add org dispatch:**
```python
    elif table_type == "organization_inventory":
        return _org_table_to_facts(table, fact_store, entity, source_document, inventory_store)
```

---

## Benefits

1. **Entity enforcement closes a data corruption vector** — buyer data can never silently become target data
2. **Org table parser captures structured org data deterministically** — no LLM hallucination risk for team names, headcounts, FTEs
3. **Consistent with existing patterns** — the org parser follows the exact same structure as app/infra/contract parsers
4. **Backward compatible** — entity rejection only fires when LLM omits a required field, which the API schema already enforces

---

## Expectations

After this spec is implemented:

1. A document containing a Team Summary table with 7 teams produces 7 org Facts AND 7 org InventoryItems
2. Each InventoryItem has `inventory_type="organization"`, `entity` matching the document, and role/headcount/fte fields populated
3. An LLM agent that omits the `entity` field in `create_inventory_entry` receives an error response and must retry with explicit entity
4. The `flag_gap` and `create_inventory_entry` tools now have identical entity enforcement behavior

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Entity rejection causes LLM retry loop | Very Low | Medium | Anthropic API enforces `required` fields in tool schema. The LLM should always include entity. This is defense-in-depth only. |
| Org table misclassified as another type | Low | Low | Score-based classification with >= 3 header match threshold. Org headers are distinct from app/infra headers. |
| Org table with unusual headers not detected | Medium | Low | Start with comprehensive header set. Log unrecognized tables as "unknown" for review. Can expand headers iteratively. |
| Headcount/FTE parsing errors from non-numeric values | Low | Low | `_normalize_numeric()` already handles N/A, TBD, dashes, currency symbols. Returns None for unparseable values. |

---

## Results Criteria

### Automated Tests

```python
def test_entity_rejection_when_missing():
    """create_inventory_entry without entity should be rejected."""
    from tools_v2.discovery_tools import execute_discovery_tool
    from stores.fact_store import FactStore

    fact_store = FactStore(deal_id="test-deal")
    result = execute_discovery_tool(
        "create_inventory_entry",
        {
            "domain": "applications",
            "category": "erp",
            "item": "SAP",
            "status": "documented",
            "evidence": {"exact_quote": "SAP ECC 6.0 is the primary ERP system"}
            # NOTE: entity intentionally omitted
        },
        fact_store
    )
    assert result["status"] == "error"
    assert "entity" in result["message"].lower()

def test_org_table_detection():
    """Organization table should be correctly detected."""
    from tools_v2.deterministic_parser import parse_markdown_table, detect_table_type

    table_text = """| Team | Headcount | FTE | Location | Reports To |
|---|---|---|---|---|
| Applications | 12 | 10.5 | NYC | VP IT |
| Infrastructure | 8 | 8.0 | NYC | VP IT |
| Security | 5 | 4.0 | Remote | CISO |"""

    parsed = parse_markdown_table(table_text)
    assert parsed is not None
    assert detect_table_type(parsed) == "organization_inventory"

def test_org_table_to_facts():
    """Organization table should produce facts and inventory items."""
    from tools_v2.deterministic_parser import parse_markdown_table, _org_table_to_facts
    from stores.fact_store import FactStore
    from stores.inventory_store import InventoryStore

    table_text = """| Team | Headcount | FTE | Location | Reports To |
|---|---|---|---|---|
| Applications | 12 | 10.5 | NYC | VP IT |
| Infrastructure | 8 | 8.0 | NYC | VP IT |
| Security | 5 | 4.0 | Remote | CISO |"""

    parsed = parse_markdown_table(table_text)
    fact_store = FactStore(deal_id="test-deal")
    inv_store = InventoryStore(deal_id="test-deal")

    facts_created = _org_table_to_facts(parsed, fact_store, "target", "org_doc.pdf", inv_store)

    assert facts_created == 3
    org_items = inv_store.get_items(inventory_type="organization", entity="target")
    assert len(org_items) == 3

    # Verify headcount parsed
    for item in org_items:
        assert item.data.get("headcount") or item.data.get("role")
```

### Manual Verification

1. Find a test document with an org/team table
2. Run discovery: `python main_v2.py data/input/org_doc.pdf --domain organization`
3. Check facts output for `category: "central_it"` facts with team details
4. Check `inventory_store.json` for `inventory_type: "organization"` items

---

## Files Modified

| File | Change |
|------|--------|
| `tools_v2/discovery_tools.py` | Change entity default from `"target"` to `None` with rejection (line 516) |
| `tools_v2/deterministic_parser.py` | Add `ORG_INVENTORY_HEADERS`, update `detect_table_type()`, add `_org_table_to_facts()`, update `table_to_facts()` dispatch |

**Lines of code:** ~150 lines added (mostly the `_org_table_to_facts` function), ~5 lines modified.
