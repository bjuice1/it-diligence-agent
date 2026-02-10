# Spec 05: Wire CostBuildUp into Tool Schema, Execution & Calculator

**Status:** Implemented
**Depends on:** Spec 03 (linked stores for accurate counts), Spec 04 (entity-scoped findings, `cost_buildup_json` DB column)
**Enables:** Spec 06 (prompt guidance referencing anchor keys)

---

## Problem Statement

A sophisticated cost infrastructure exists but is completely disconnected from the reasoning workflow:

| Component | Location | Status |
|-----------|----------|--------|
| `CostBuildUp` dataclass | reasoning_tools.py:372-456 | Built, never populated by tools |
| `WorkItem.cost_buildup` field | reasoning_tools.py:477 | Exists, always None |
| `cost_estimator.estimate_cost()` | cost_estimator.py:165-296 | Production-ready, never called from reasoning |
| `COST_ANCHORS` (31 anchors) | cost_model.py:26-213 | Comprehensive, never referenced by LLM |
| `cost_database.py` (97 activities) | cost_database.py | Research-backed, disconnected |
| `cost_calculator.calculate_costs_from_work_items()` | cost_calculator.py:78-166 | Uses only `cost_estimate` STRING, ignores `cost_buildup` |
| `create_work_item` tool schema | reasoning_tools.py:2217-2328 | No `cost_buildup` property |
| `_execute_create_work_item()` | reasoning_tools.py:2973-3068 | Only validates `cost_estimate` string |

**Result:** The LLM produces vague cost ranges like `"100k_to_250k"` with no transparency about how the estimate was derived. The precise anchor-based estimation system goes unused.

---

## Changes Required

### Change 1: Add `cost_buildup` to `create_work_item` Tool Schema

**File:** `tools_v2/reasoning_tools.py` lines 2217-2328

**Current schema `properties` dict** ends with `buyer_facts_cited`, `overlap_id`, `dependencies`. `cost_estimate` is a required enum field.

**Add `cost_buildup` as an optional object property (after `cost_estimate`):**

```python
"cost_buildup": {
    "type": "object",
    "description": (
        "Optional structured cost breakdown using benchmark anchors. "
        "When provided, this gives transparent, auditable cost estimates "
        "instead of vague ranges. Use anchor_key from the COST ANCHORS reference table."
    ),
    "properties": {
        "anchor_key": {
            "type": "string",
            "description": "Key from COST_ANCHORS (e.g., 'app_migration_simple', 'identity_separation', 'cloud_migration')",
            "enum": [
                # Application anchors
                "app_migration_simple", "app_migration_moderate", "app_migration_complex",
                "license_microsoft", "license_erp",
                # Infrastructure anchors
                "dc_migration", "cloud_migration", "storage_migration",
                # Identity anchors
                "identity_separation",
                # Network anchors
                "network_separation", "wan_setup",
                # Security anchors
                "security_remediation", "security_tool_deployment",
                # Data anchors
                "data_segregation",
                # Vendor anchors
                "vendor_contract_transition",
                # PMO & Change anchors
                "pmo_overhead", "change_management",
                # TSA Exit anchors
                "tsa_exit_identity", "tsa_exit_email", "tsa_exit_service_desk",
                "tsa_exit_infrastructure", "tsa_exit_network", "tsa_exit_security",
                "tsa_exit_erp_support",
            ],
        },
        "quantity": {
            "type": "integer",
            "description": "Number of units (users, apps, sites, etc.) — use 1 for fixed costs. MUST come from cited facts.",
            "minimum": 1,
        },
        "unit_label": {
            "type": "string",
            "description": "What the quantity represents",
            "enum": ["users", "applications", "sites", "servers", "vendors",
                     "data_centers", "terabytes", "organization", "endpoints"],
        },
        "size_tier": {
            "type": "string",
            "description": "For fixed_by_size anchors: which tier applies based on quantity",
            "enum": ["small", "medium", "large"],
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of assumptions underlying this estimate (e.g., 'Standard complexity migration', '500 users from F-TGT-APP-001')",
        },
        "source_facts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Fact IDs that provide the quantities used (e.g., 'F-TGT-APP-001' for user count)",
        },
        "notes": {
            "type": "string",
            "description": "Additional context about the estimate",
        },
    },
    "required": ["anchor_key", "quantity", "unit_label", "source_facts"],
},
```

**`cost_buildup` is NOT in the `required` array** — it's an optional enhancement. The `cost_estimate` string remains required for backwards compatibility.

### Change 2: Process `cost_buildup` in `_execute_create_work_item()`

**File:** `tools_v2/reasoning_tools.py` lines 2973-3068

**After the existing `cost_estimate` validation (line ~3026) and before calling `reasoning_store.add_work_item()` (line ~3035):**

```python
    # Existing: Validate cost_estimate (line 3020-3026)
    cost_estimate = input_data.get("cost_estimate")
    if cost_estimate not in COST_RANGES:
        return {"status": "error", "message": f"Invalid cost_estimate. Must be one of: {COST_RANGES}"}

    # NEW: Process cost_buildup if provided
    cost_buildup_obj = None
    cost_buildup_input = input_data.get("cost_buildup")

    if cost_buildup_input:
        try:
            from tools_v2.cost_estimator import estimate_cost

            anchor_key = cost_buildup_input.get("anchor_key")
            quantity = cost_buildup_input.get("quantity", 1)
            unit_label = cost_buildup_input.get("unit_label", "organization")
            size_tier = cost_buildup_input.get("size_tier")
            assumptions = cost_buildup_input.get("assumptions", [])
            source_facts = cost_buildup_input.get("source_facts", [])
            notes = cost_buildup_input.get("notes", "")

            # Call the cost estimator to create a CostBuildUp object
            cost_buildup_obj = estimate_cost(
                anchor_key=anchor_key,
                quantity=quantity,
                size_tier=size_tier,
                source_facts=source_facts,
                assumptions=assumptions,
                notes=notes,
                estimation_source="benchmark",
                confidence="medium",
            )

            if cost_buildup_obj is None:
                # Invalid anchor_key or estimation failure — log warning but don't block
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"cost_buildup estimation failed for anchor_key='{anchor_key}'. "
                    f"Falling back to cost_estimate='{cost_estimate}'."
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"cost_buildup processing error: {e}. Using cost_estimate fallback.")

    # Existing: Call reasoning_store.add_work_item() (line ~3035)
    result = reasoning_store.add_work_item(
        domain=input_data["domain"],
        title=input_data["title"],
        description=input_data["description"],
        phase=input_data["phase"],
        priority=input_data["priority"],
        owner_type=input_data["owner_type"],
        cost_estimate=cost_estimate,
        cost_buildup=cost_buildup_obj,  # NEW: Pass CostBuildUp object
        triggered_by=input_data.get("triggered_by", []),
        based_on_facts=input_data.get("based_on_facts", []),
        confidence=input_data.get("confidence", "medium"),
        reasoning=input_data.get("reasoning", ""),
        # ... other existing fields ...
    )

    # NEW: Include cost transparency in response
    if cost_buildup_obj:
        result["cost_buildup_summary"] = cost_buildup_obj.format_summary()
        result["cost_buildup_range"] = f"${cost_buildup_obj.total_low:,.0f} - ${cost_buildup_obj.total_high:,.0f}"

    return result
```

### Change 3: Update `cost_calculator.py` to Prefer CostBuildUp

**File:** `tools_v2/cost_calculator.py` lines 78-166

**Current `calculate_costs_from_work_items()` (line ~100):**
```python
# Currently only reads cost_estimate string:
cost_range = COST_RANGE_VALUES.get(work_item.cost_estimate, {"low": 0, "high": 0})
low = cost_range["low"]
high = cost_range["high"]
```

**Replace with CostBuildUp-preferring logic:**

```python
def calculate_costs_from_work_items(work_items: List) -> "CostBreakdown":
    """Calculate costs from work items, preferring CostBuildUp when available.

    Priority:
    1. CostBuildUp (precise, anchor-based) — if work_item.cost_buildup exists
    2. cost_estimate string (vague range) — fallback
    """
    breakdown = CostBreakdown()

    for work_item in work_items:
        # Prefer CostBuildUp for precise estimates
        if hasattr(work_item, 'cost_buildup') and work_item.cost_buildup is not None:
            low = work_item.cost_buildup.total_low
            high = work_item.cost_buildup.total_high
            estimation_source = "cost_buildup"
        else:
            # Fallback to vague range
            cost_range = COST_RANGE_VALUES.get(
                getattr(work_item, 'cost_estimate', 'under_25k'),
                {"low": 0, "high": 0}
            )
            low = cost_range["low"]
            high = cost_range["high"]
            estimation_source = "cost_range"

        # Accumulate totals
        breakdown.total_low += low
        breakdown.total_high += high

        # Track per-item details
        phase = getattr(work_item, 'phase', 'Unknown')
        domain = getattr(work_item, 'domain', 'Unknown')
        owner = getattr(work_item, 'owner_type', 'Unknown')

        # Aggregate by phase
        if phase not in breakdown.by_phase:
            breakdown.by_phase[phase] = {"low": 0, "high": 0, "count": 0}
        breakdown.by_phase[phase]["low"] += low
        breakdown.by_phase[phase]["high"] += high
        breakdown.by_phase[phase]["count"] += 1

        # Aggregate by domain
        if domain not in breakdown.by_domain:
            breakdown.by_domain[domain] = {"low": 0, "high": 0, "count": 0}
        breakdown.by_domain[domain]["low"] += low
        breakdown.by_domain[domain]["high"] += high
        breakdown.by_domain[domain]["count"] += 1

        # Aggregate by owner
        if owner not in breakdown.by_owner:
            breakdown.by_owner[owner] = {"low": 0, "high": 0, "count": 0}
        breakdown.by_owner[owner]["low"] += low
        breakdown.by_owner[owner]["high"] += high
        breakdown.by_owner[owner]["count"] += 1

        # Track individual work item costs with source info
        breakdown.work_item_costs.append({
            "id": getattr(work_item, 'finding_id', ''),
            "title": getattr(work_item, 'title', ''),
            "low": low,
            "high": high,
            "estimation_source": estimation_source,
            "anchor_key": work_item.cost_buildup.anchor_key if work_item.cost_buildup else None,
        })

    return breakdown
```

### Change 4: Update `add_work_item()` to Accept `cost_buildup`

**File:** `tools_v2/reasoning_tools.py` — `ReasoningStore.add_work_item()` (lines 836-877)

**Current signature** does not include `cost_buildup` parameter.

**Add parameter:**

```python
def add_work_item(
    self,
    domain: str,
    title: str,
    description: str,
    phase: str,
    priority: str,
    owner_type: str,
    cost_estimate: str,
    cost_buildup: Optional["CostBuildUp"] = None,  # NEW
    triggered_by: List[str] = None,
    based_on_facts: List[str] = None,
    confidence: str = "medium",
    reasoning: str = "",
    # ... other existing params ...
) -> Dict[str, Any]:
```

**Pass to WorkItem constructor (line ~870):**

```python
work_item = WorkItem(
    finding_id=work_item_id,
    domain=domain,
    title=title,
    # ... existing fields ...
    cost_estimate=cost_estimate,
    cost_buildup=cost_buildup,  # NEW
    # ... rest of fields ...
)
```

### Change 5: Persist CostBuildUp to Database

**When saving findings to DB** (wherever WorkItems are serialized to Finding model), serialize the CostBuildUp:

```python
# In the persistence layer (e.g., where WorkItem → Finding):
finding.cost_buildup_json = work_item.cost_buildup.to_dict() if work_item.cost_buildup else None
```

This uses the `cost_buildup_json` column added in Spec 04.

### Change 6: Update Excel Export (Cost Transparency Sheet)

**File:** `tools_v2/excel_exporter.py`

**Add a "Cost Buildup" sheet to the Excel export:**

```python
def _write_cost_buildup_sheet(self, workbook, work_items):
    """Write cost buildup transparency sheet."""
    sheet = workbook.add_worksheet("Cost Buildup")

    headers = [
        "Work Item ID", "Title", "Domain", "Phase",
        "Cost Estimate (Range)", "Anchor Key", "Anchor Name",
        "Method", "Quantity", "Unit", "Unit Cost Low", "Unit Cost High",
        "Total Low", "Total High", "Confidence", "Source",
        "Assumptions", "Source Facts",
    ]

    for col, header in enumerate(headers):
        sheet.write(0, col, header)

    row = 1
    for wi in work_items:
        sheet.write(row, 0, wi.finding_id)
        sheet.write(row, 1, wi.title)
        sheet.write(row, 2, wi.domain)
        sheet.write(row, 3, wi.phase)
        sheet.write(row, 4, wi.cost_estimate)

        if wi.cost_buildup:
            cb = wi.cost_buildup
            sheet.write(row, 5, cb.anchor_key)
            sheet.write(row, 6, cb.anchor_name)
            sheet.write(row, 7, cb.estimation_method)
            sheet.write(row, 8, cb.quantity)
            sheet.write(row, 9, cb.unit_label)
            sheet.write(row, 10, cb.unit_cost_low)
            sheet.write(row, 11, cb.unit_cost_high)
            sheet.write(row, 12, cb.total_low)
            sheet.write(row, 13, cb.total_high)
            sheet.write(row, 14, cb.confidence)
            sheet.write(row, 15, cb.estimation_source)
            sheet.write(row, 16, "; ".join(cb.assumptions))
            sheet.write(row, 17, ", ".join(cb.source_facts))
        else:
            sheet.write(row, 5, "N/A (range only)")

        row += 1
```

### Change 7: Update HTML Report (Cost Transparency Section)

**File:** `tools_v2/html_report.py`

**In the work item display section (lines 925-936), add CostBuildUp detail:**

```python
# After showing AI cost range, add buildup transparency:
if hasattr(wi, 'cost_buildup') and wi.cost_buildup:
    cb = wi.cost_buildup
    cost_html += f'''
    <div class="cost-buildup-detail">
        <strong>Cost Basis:</strong> {cb.anchor_name} ({cb.anchor_key})<br>
        <strong>Method:</strong> {cb.estimation_method} &times; {cb.quantity} {cb.unit_label}<br>
        <strong>Unit Range:</strong> ${cb.unit_cost_low:,.0f} - ${cb.unit_cost_high:,.0f} per {cb.unit_label}<br>
        <strong>Total:</strong> ${cb.total_low:,.0f} - ${cb.total_high:,.0f}<br>
        <strong>Confidence:</strong> {cb.confidence} ({cb.estimation_source})<br>
        <strong>Assumptions:</strong> {"; ".join(cb.assumptions) if cb.assumptions else "None stated"}<br>
    </div>
    '''
```

---

## Anchor Key Reference Table

For use in Spec 06 prompts. All keys from `COST_ANCHORS` (cost_model.py lines 26-213):

| Anchor Key | Name | Unit Type | Typical Range |
|------------|------|-----------|---------------|
| `app_migration_simple` | Simple App Migration | per_app | $5K-$25K/app |
| `app_migration_moderate` | Moderate App Migration | per_app | $25K-$100K/app |
| `app_migration_complex` | Complex App Migration | per_app | $100K-$500K/app |
| `license_microsoft` | Microsoft License Transition | per_user | $150-$400/user |
| `license_erp` | ERP License Transition | per_user | $500-$2,000/user |
| `dc_migration` | Data Center Migration | per_dc | $500K-$2M/DC |
| `cloud_migration` | Cloud Migration | per_app | $10K-$100K/app |
| `storage_migration` | Storage Migration | per_tb | $5K-$20K/TB |
| `identity_separation` | Identity Separation | fixed_by_size | $100K-$2M |
| `network_separation` | Network Separation | fixed_by_complexity | $50K-$500K |
| `wan_setup` | WAN Setup | per_site | $10K-$50K/site |
| `security_remediation` | Security Remediation | fixed_by_gaps | $50K-$500K |
| `security_tool_deployment` | Security Tool Deployment | per_endpoint | $30-$80/endpoint |
| `data_segregation` | Data Segregation | fixed_by_size | $100K-$1M |
| `vendor_contract_transition` | Vendor Contract Transition | per_vendor | $5K-$50K/vendor |
| `pmo_overhead` | PMO Overhead | percentage | 10-15% of total |
| `change_management` | Change Management | per_user | $50-$200/user |
| `tsa_exit_identity` | TSA Exit: Identity | fixed_plus_per_user | $100K-$500K |
| `tsa_exit_email` | TSA Exit: Email | per_user | $20-$50/user |
| `tsa_exit_service_desk` | TSA Exit: Service Desk | fixed_plus_per_user | $200K-$800K |
| `tsa_exit_infrastructure` | TSA Exit: Infrastructure | fixed_by_size | $300K-$2M |
| `tsa_exit_network` | TSA Exit: Network | per_site | $20K-$80K/site |
| `tsa_exit_security` | TSA Exit: Security | fixed_by_size | $150K-$600K |
| `tsa_exit_erp_support` | TSA Exit: ERP Support | fixed_by_size | $200K-$1M |

---

## Backwards Compatibility

**Critical requirement:** Work items with only `cost_estimate` (no `cost_buildup`) must continue to work exactly as before.

**Guarantees:**
1. `cost_buildup` is optional in the tool schema — LLM can omit it
2. `_execute_create_work_item()` processes `cost_buildup` only if present, falls back gracefully
3. `cost_calculator.py` checks `work_item.cost_buildup is not None` before using it
4. `cost_buildup_json` DB column is nullable (None for old findings)
5. Excel/HTML export handle `wi.cost_buildup is None` gracefully

---

## Test Cases

### Test 1: CostBuildUp Created via Tool
```python
def test_work_item_with_cost_buildup():
    """Creating a work item with cost_buildup should produce a CostBuildUp object."""
    result = _execute_create_work_item({
        "domain": "applications",
        "title": "Migrate SAP ECC to S/4HANA",
        "description": "Full ERP migration",
        "phase": "Post_100",
        "priority": "high",
        "owner_type": "buyer",
        "cost_estimate": "over_1m",
        "triggered_by": ["F-TGT-APP-001"],
        "confidence": "high",
        "reasoning": "SAP ECC 6.0 is end-of-life..." * 5,
        "mna_lens": "cost_driver",
        "mna_implication": "Major capital expenditure",
        "target_action": "Inventory SAP objects",
        "cost_buildup": {
            "anchor_key": "app_migration_complex",
            "quantity": 1,
            "unit_label": "applications",
            "source_facts": ["F-TGT-APP-001"],
            "assumptions": ["Complex migration due to 200+ Z-programs"],
        },
    }, fact_store, reasoning_store)

    assert result["status"] == "success"
    work_item = reasoning_store.work_items[-1]
    assert work_item.cost_buildup is not None
    assert work_item.cost_buildup.anchor_key == "app_migration_complex"
    assert work_item.cost_buildup.total_low > 0
    assert work_item.cost_buildup.total_high > work_item.cost_buildup.total_low
```

### Test 2: Backwards Compatibility (No CostBuildUp)
```python
def test_work_item_without_cost_buildup():
    """Work items without cost_buildup should work exactly as before."""
    result = _execute_create_work_item({
        "domain": "infrastructure",
        "title": "Replace EOL servers",
        "description": "Refresh 5 servers",
        "phase": "Day_100",
        "priority": "medium",
        "owner_type": "target",
        "cost_estimate": "25k_to_100k",
        "triggered_by": ["F-TGT-INFRA-001"],
        "confidence": "medium",
        "reasoning": "Five servers running Windows 2012..." * 5,
        "mna_lens": "day_1_continuity",
        "mna_implication": "Must replace before support ends",
        "target_action": "Replace servers",
    }, fact_store, reasoning_store)

    assert result["status"] == "success"
    work_item = reasoning_store.work_items[-1]
    assert work_item.cost_buildup is None  # Not provided
    assert work_item.cost_estimate == "25k_to_100k"  # Still works
```

### Test 3: Calculator Prefers CostBuildUp
```python
def test_calculator_prefers_cost_buildup():
    """cost_calculator should use CostBuildUp totals when available."""
    from tools_v2.cost_estimator import estimate_cost

    # Work item WITH cost_buildup
    cb = estimate_cost("app_migration_complex", quantity=1)
    wi_with_buildup = WorkItem(
        finding_id="WI-test-001",
        domain="applications",
        title="SAP Migration",
        cost_estimate="over_1m",
        cost_buildup=cb,
        # ... other required fields ...
    )

    # Work item WITHOUT cost_buildup
    wi_without_buildup = WorkItem(
        finding_id="WI-test-002",
        domain="infrastructure",
        title="Server Refresh",
        cost_estimate="25k_to_100k",
        cost_buildup=None,
        # ... other required fields ...
    )

    breakdown = calculate_costs_from_work_items([wi_with_buildup, wi_without_buildup])

    # First item should use CostBuildUp totals (precise)
    assert breakdown.work_item_costs[0]["estimation_source"] == "cost_buildup"
    assert breakdown.work_item_costs[0]["low"] == cb.total_low

    # Second item should use cost_estimate range (fallback)
    assert breakdown.work_item_costs[1]["estimation_source"] == "cost_range"
    assert breakdown.work_item_costs[1]["low"] == 25_000
```

### Test 4: Invalid Anchor Key Graceful Fallback
```python
def test_invalid_anchor_key_falls_back():
    """Invalid anchor_key should warn but not block work item creation."""
    result = _execute_create_work_item({
        # ... required fields ...
        "cost_estimate": "100k_to_250k",
        "cost_buildup": {
            "anchor_key": "nonexistent_anchor",
            "quantity": 1,
            "unit_label": "organization",
            "source_facts": ["F-TGT-APP-001"],
        },
    }, fact_store, reasoning_store)

    assert result["status"] == "success"  # Not blocked
    work_item = reasoning_store.work_items[-1]
    assert work_item.cost_buildup is None  # Failed gracefully
    assert work_item.cost_estimate == "100k_to_250k"  # Fallback used
```

### Test 5: DB Persistence
```python
def test_cost_buildup_persists_to_db(db_session):
    """CostBuildUp should be serialized to cost_buildup_json column."""
    finding = Finding(
        id="WI-test-db",
        deal_id="test-deal",
        finding_type="work_item",
        domain="applications",
        title="SAP Migration",
        cost_estimate="over_1m",
        cost_buildup_json={
            "anchor_key": "app_migration_complex",
            "total_low": 100000,
            "total_high": 500000,
            "estimation_method": "per_app",
        },
    )
    db_session.add(finding)
    db_session.commit()

    loaded = db_session.query(Finding).filter_by(id="WI-test-db").first()
    assert loaded.cost_buildup_json is not None
    assert loaded.cost_buildup_json["anchor_key"] == "app_migration_complex"
```

---

## Acceptance Criteria

1. `create_work_item` tool schema includes `cost_buildup` object with documented properties
2. LLM can pass `cost_buildup` with `anchor_key`, `quantity`, `unit_label`, `source_facts`
3. `_execute_create_work_item()` calls `cost_estimator.estimate_cost()` to create CostBuildUp
4. WorkItem has populated `cost_buildup` field (not None) when LLM provides the input
5. `cost_calculator` uses `cost_buildup.total_low/high` when available, falls back to `cost_estimate` ranges
6. Excel export shows cost buildup transparency sheet
7. HTML report shows cost buildup details per work item
8. Backwards compatible: work items without `cost_buildup` work exactly as before
9. Invalid `anchor_key` fails gracefully (warning, not error)
10. `cost_buildup_json` persisted to Finding DB model (from Spec 04)

---

## Rollback Plan

- Remove `cost_buildup` from tool schema → LLM stops providing it, all work items use ranges
- Remove `cost_buildup` processing in `_execute_create_work_item()` → WorkItem.cost_buildup stays None
- Revert `cost_calculator` → Uses only COST_RANGE_VALUES as before
- All rollbacks are independent; each can be reverted separately

---

## Implementation Notes

*Documented 2026-02-09 from implemented source files.*

### 1. Files Modified

#### `tools_v2/reasoning_tools.py`

**WorkItem dataclass (line 481):** Added `cost_buildup: Optional[CostBuildUp] = None` field with comment "Detailed breakdown for transparency".

**WorkItem.to_dict() (lines 509-510):** Custom serialization — if `self.cost_buildup` is not None, calls `self.cost_buildup.to_dict()` to serialize the CostBuildUp into the dict output.

**WorkItem.from_dict() (lines 516-517):** Custom deserialization — if `data['cost_buildup']` is a dict, reconstructs it via `CostBuildUp.from_dict(data['cost_buildup'])`.

**create_work_item tool schema (lines 2290-2357):** Added `cost_buildup` as an optional object property with 7 sub-properties: `anchor_key` (enum of 23 anchor keys), `quantity` (integer, minimum 1), `unit_label` (enum of 9 unit types), `size_tier` (enum: small/medium/large), `assumptions` (array of strings), `source_facts` (array of strings), and `notes` (string). Required sub-properties: `["anchor_key", "quantity", "unit_label", "source_facts"]`. The `cost_buildup` object is NOT in the top-level `required` array.

**_execute_create_work_item() (lines 3168-3244):** After `cost_estimate` validation (line 3160), processes `cost_buildup` input when present (lines 3168-3203). Calls `estimate_cost()` from `tools_v2.cost_estimator` with `anchor_key`, `quantity`, `size_tier`, `source_facts`, `assumptions`, `notes`, `estimation_source="benchmark"`, and `confidence="medium"`. On failure (None return or exception), logs a warning and falls back to `cost_estimate` string only. Passes `cost_buildup_obj` to `reasoning_store.add_work_item()` at line 3225. Appends `cost_buildup_summary` and `cost_buildup_range` to the response dict when a CostBuildUp was successfully created (lines 3242-3244).

**ReasoningStore.add_work_item() (lines 852-900):** Uses `**kwargs` pattern rather than an explicit `cost_buildup` parameter. The `cost_buildup` keyword is passed through kwargs into `WorkItem(**kwargs)` at line 894. After construction, logs buildup info (anchor_key plus total range) if `wi.cost_buildup is not None` (lines 897-898).

#### `tools_v2/cost_calculator.py`

**calculate_costs_from_work_items() (lines 78-182):** Updated to prefer CostBuildUp totals over COST_RANGE_VALUES. At lines 111-117, checks `getattr(wi, 'cost_buildup', None)` and if not None, uses `cost_buildup.total_low`, `cost_buildup.total_high`, sets `estimation_source = "cost_buildup"`, and captures `anchor_key`. Falls back to `COST_RANGE_VALUES` lookup from `cost_estimate` string at lines 118-132. Each `work_item_costs` entry (lines 135-147) includes `estimation_source` and `anchor_key` fields for traceability. Aggregation by phase, domain, and owner at lines 154-175 includes an `items` list in each bucket (not in original spec).

#### `tools_v2/excel_exporter.py`

**Export entry point (lines 225-227):** Conditionally calls `self._write_cost_buildup_sheet(wb, work_items)` when `work_items` is truthy.

**_write_cost_buildup_sheet() (lines 506-557):** Creates a "Cost Buildup" sheet with 18 columns: Work Item ID, Title, Domain, Phase, Cost Estimate (Range), Anchor Key, Anchor Name, Method, Quantity, Unit, Unit Cost Low, Unit Cost High, Total Low, Total High, Confidence, Source, Assumptions, Source Facts. Uses openpyxl (cell-based API with `ws.cell(row, column, value)`) rather than xlsxwriter (as shown in the spec pseudocode). Applies `HEADER_FILL`, `HEADER_FONT`, and centered `Alignment` to header row. For work items without a CostBuildUp, writes "N/A (range only)" in the Anchor Key column. Freezes row 1 (`ws.freeze_panes = 'A2'`) and auto-fits column widths via `_autofit_columns()`.

#### `tools_v2/html_report.py`

**Work item display (lines 965-1001):** Builds `cost_buildup_html` when `wi.cost_buildup` is not None (lines 966-981). Renders a green-bordered detail box (`background: #f0fdf4; border: 1px solid #86efac`) inside a `<dt>/<dd>` pair with heading "Cost Buildup (Anchor-Based)". Displays: Basis (anchor_name + anchor_key as code), Method (estimation_method x quantity unit_label), Unit Range (unit_cost_low - unit_cost_high per unit_label), Total (bold green, total_low - total_high), Confidence (confidence + estimation_source), and Assumptions. The buildup HTML is inserted at line 1001 between the "AI Initial Estimate" row and the "Reasoning" row.

#### `tests/test_cost_buildup.py`

New test file with 20 tests across 4 test classes (see Test Coverage below).

### 2. Deviations from Spec

| # | Area | Spec Said | Implementation Did | Impact |
|---|------|-----------|--------------------|--------|
| 1 | `add_work_item()` signature | Explicit `cost_buildup: Optional[CostBuildUp] = None` parameter (Change 4) | Uses `**kwargs` pattern; `cost_buildup` passed as a keyword arg through to `WorkItem(**kwargs)` | Functionally equivalent; no typed signature enforcement but simpler given the many optional fields already using kwargs |
| 2 | `work_item_costs` dict | Spec showed keys: `id`, `title`, `low`, `high`, `estimation_source`, `anchor_key` | Implementation adds `phase`, `domain`, `owner`, `cost_estimate` keys as well | Strictly a superset; extra fields improve traceability |
| 3 | Aggregation buckets | Spec showed `{"low": 0, "high": 0, "count": 0}` for by_phase/by_domain/by_owner | Implementation adds `"items": []` list to each bucket, tracking work item IDs | Enhancement; no backwards incompatibility |
| 4 | Phase bucket init | Spec showed on-demand creation (`if phase not in breakdown.by_phase`) | Implementation pre-initializes all phase buckets from `PHASE_LABELS` (lines 97-99) | Ensures all phases appear in output even if empty |
| 5 | Excel library | Spec pseudocode used xlsxwriter API (`workbook.add_worksheet`, `sheet.write`) | Implementation uses openpyxl API (`wb.create_sheet`, `ws.cell`) | Different library but identical 18-column output structure |
| 6 | Excel styling | Spec had no styling directives | Implementation applies `HEADER_FILL`, `HEADER_FONT`, centered alignment, freeze panes, auto-fit columns | Polish enhancement |
| 7 | HTML structure | Spec showed a `<div class="cost-buildup-detail">` block | Implementation uses `<dt>/<dd>` pairs inside existing `<dl>` with inline-styled green box | Better integration with existing item detail layout |
| 8 | DB persistence (Change 5) | Spec called for explicit serialization in persistence layer (`finding.cost_buildup_json = work_item.cost_buildup.to_dict()`) | Handled implicitly via `WorkItem.to_dict()` serialization (lines 509-510) which is called during persistence | Same outcome; serialization occurs through the dataclass method |
| 9 | Test coverage | Spec outlined 5 test cases (tool creation, backwards compat, calculator preference, invalid anchor, DB persistence) | Implementation has 20 tests in 4 classes; does not include a DB session-based persistence test (Test 5 from spec) | Broader unit coverage but DB persistence test deferred |
| 10 | `cost_estimate` range values | Spec showed `"100k_to_500k"` as a single range | Implementation splits into `"100k_to_250k"` and `"250k_to_500k"` (6 ranges total) | More granular; test assertions use the finer-grained ranges |

### 3. Test Coverage

**File:** `tests/test_cost_buildup.py` -- 20 tests across 4 classes.

#### `TestCostBuildUpCreation` (6 tests)
| Test | Verifies |
|------|----------|
| `test_estimate_cost_returns_cost_buildup` | `estimate_cost()` returns a `CostBuildUp` instance for valid anchor key (`identity_separation`) |
| `test_estimate_cost_has_valid_fields` | All required fields populated: `anchor_key`, `quantity`, `total_low`, `total_high`, `unit_label`, `anchor_name` |
| `test_estimate_cost_invalid_anchor_returns_none` | Unknown anchor key returns `None` (graceful failure) |
| `test_estimate_cost_per_app` | Per-app quantities scale correctly (5 apps >= 1 app in cost) |
| `test_estimate_cost_fixed_by_size` | Size tier differentiation works (large >= small for `identity_separation`) |
| `test_estimate_cost_preserves_source_facts` | `source_facts`, `assumptions`, and `notes` round-trip correctly |

#### `TestCostCalculatorPreference` (4 tests)
| Test | Verifies |
|------|----------|
| `test_prefers_buildup_totals` | Calculator uses CostBuildUp totals (estimation_source="cost_buildup") when present; falls back to cost_range when absent |
| `test_all_range_only_works` | All work items with only `cost_estimate` strings produce correct totals (backwards compat) |
| `test_all_buildup_works` | All work items with CostBuildUp produce precise aggregate totals |
| `test_empty_work_items` | Empty list yields zero totals and zero count |

#### `TestCostBuildUpSerialization` (5 tests)
| Test | Verifies |
|------|----------|
| `test_cost_buildup_to_dict` | `CostBuildUp.to_dict()` includes all key fields (`anchor_key`, `quantity`, `total_low`, `total_high`, `unit_cost_low`, `unit_cost_high`, `estimation_method`) |
| `test_cost_buildup_from_dict` | `CostBuildUp.from_dict()` restores `anchor_key`, `total_low`, `total_high`, `quantity` |
| `test_cost_buildup_round_trip` | Full `CostBuildUp -> dict -> CostBuildUp -> dict` produces identical output |
| `test_work_item_to_dict_includes_buildup` | `WorkItem.to_dict()` includes non-None `cost_buildup` with correct anchor_key |
| `test_work_item_to_dict_none_buildup` | `WorkItem.to_dict()` includes `cost_buildup: None` when not set |

#### `TestToolSchema` (5 tests)
| Test | Verifies |
|------|----------|
| `test_work_item_dataclass_has_cost_buildup_field` | `cost_buildup` exists as a field on the `WorkItem` dataclass |
| `test_cost_buildup_is_optional` | Creating a `WorkItem` without `cost_buildup` defaults to `None` |
| `test_get_cost_range_key` | `CostBuildUp.get_cost_range_key()` returns a valid cost range string |
| `test_format_summary` | `CostBuildUp.format_summary()` returns a readable string containing "$" |
| (implicit) | Helper `_make_work_item()` exercises WorkItem construction with and without CostBuildUp |

**Not covered by tests (noted deviations):**
- DB session-based persistence test (Spec Test 5) is not implemented; serialization is tested via `to_dict`/`from_dict` round-trips instead.
- End-to-end `_execute_create_work_item()` integration test with full reasoning store is not present in this file (may exist elsewhere).
- Excel and HTML rendering of CostBuildUp are not unit tested in this file.
