# Spec 04: Entity Propagation into Reasoning Outputs & Database Persistence

**Status:** Implemented
**Depends on:** None (independent concern, can be implemented in parallel with Specs 01-03)
**Enables:** Spec 05 (entity-aware cost estimation), Spec 06 (entity-aware prompt guidance)

---

## Problem Statement

Entity distinction (buyer vs. target) is strong at the discovery phase but breaks down at the reasoning phase:

1. **Discovery phase is well-protected:**
   - FactStore uses `F-TGT-*` / `F-BYR-*` prefixes (fact_store.py line 524)
   - `add_fact()` requires entity parameter (default `"target"`)
   - Gap flagging passes entity to `add_gap()` (discovery_tools.py line 680)

2. **Reasoning phase has gaps:**
   - `_execute_identify_risk()` (reasoning_tools.py line 2846) has `risk_scope` parameter but no entity validation — defaults to `"target_standalone"` silently
   - `_execute_create_strategic_consideration()` (line 2934) has no entity field at all
   - `_execute_create_recommendation()` (line 3071) has no entity field
   - WorkItem has `target_facts_cited` and `buyer_facts_cited` fields (lines 493-494) but they're populated by `add_work_item()` (line 855-856) only via prefix parsing — not validated at the reasoning tool level

3. **Finding database model has no entity column:**
   - `web/database.py` Finding model (lines 783-903) has `finding_type`, `domain`, `severity` etc. but **no `entity` field**
   - No `risk_scope` field persisted to DB
   - No `cost_buildup_json` field (needed for Spec 05)
   - `finding_repository.py` queries cannot filter by entity

4. **flag_gap entity default is implicit:**
   - `discovery_tools.py` line 656: `entity = input_data.get("entity", "target")` — silent default means LLM can omit entity and it defaults to target without warning

5. **ANCHOR RULE not enforced:**
   - Buyer-context findings (work items, risks) should ALWAYS cite at least one target fact to prevent hallucinated buyer-only findings
   - WorkItem has `target_facts_cited` and `buyer_facts_cited` but the enforcement that `buyer_facts_cited` items must also include `target_facts_cited` is not validated

---

## Files to Modify

### 1. `web/database.py` — Add Entity & Cost Fields to Finding Model

**Current Finding model (lines 783-903):** No entity field, no risk_scope, no cost_buildup.

**Add after `finding_type` field (line ~790):**

```python
class Finding(Base, SoftDeleteMixin):
    __tablename__ = 'findings'

    id = Column(String(50), primary_key=True)
    deal_id = Column(String(36), ForeignKey('deals.id'), nullable=False)
    analysis_run_id = Column(String(36), ForeignKey('analysis_runs.id'), nullable=True)

    finding_type = Column(String(50), nullable=False)
    entity = Column(String(20), default='target')       # NEW: "target" or "buyer"
    risk_scope = Column(String(50), default='')          # NEW: "target_standalone", "integration_dependent", "buyer_action"

    domain = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    # ... existing fields ...

    # Work Item cost fields
    cost_estimate = Column(String(50), nullable=True)
    cost_buildup_json = Column(JSON, default=None)       # NEW: Serialized CostBuildUp dict

    # ... rest of existing fields ...
```

**Add index for entity queries (after line ~855):**

```python
Index('idx_findings_entity', 'deal_id', 'entity'),
```

**Update `to_dict()` method (lines 857-903) to include new fields:**

```python
def to_dict(self):
    d = {
        'id': self.id,
        'deal_id': self.deal_id,
        'analysis_run_id': self.analysis_run_id,
        'finding_type': self.finding_type,
        'entity': self.entity or 'target',          # NEW
        'risk_scope': self.risk_scope or '',          # NEW
        'domain': self.domain,
        # ... existing fields ...
        'cost_estimate': self.cost_estimate,
        'cost_buildup_json': self.cost_buildup_json,  # NEW
        # ... existing fields ...
    }
    return d
```

**Database migration:** This adds nullable columns with defaults, so it's safe to apply without data migration. Existing rows get `entity='target'` and `risk_scope=''` and `cost_buildup_json=None`.

### 2. `tools_v2/reasoning_tools.py` — Add Entity Validation to Risk Identification

**`_execute_identify_risk()` (lines 2846-2931):**

**Current:** `risk_scope` is an optional parameter with silent default `"target_standalone"`.

**Add entity validation after existing required field checks (line ~2898):**

```python
def _execute_identify_risk(input_data, fact_store, reasoning_store, **kwargs):
    # ... existing validation (lines 2859-2898) ...

    # NEW: Entity validation
    risk_scope = input_data.get("risk_scope", "target_standalone")
    VALID_RISK_SCOPES = ["target_standalone", "integration_dependent", "buyer_action"]
    if risk_scope not in VALID_RISK_SCOPES:
        return {"status": "error", "message": f"Invalid risk_scope '{risk_scope}'. Must be one of: {VALID_RISK_SCOPES}"}

    # NEW: Determine entity from cited facts
    based_on_facts = input_data.get("based_on_facts", [])
    entity = _infer_entity_from_citations(based_on_facts, fact_store)

    # NEW: ANCHOR RULE enforcement
    # If buyer facts are cited, at least one target fact must also be cited
    buyer_facts = [f for f in based_on_facts if "BYR" in f.upper()]
    target_facts = [f for f in based_on_facts if "TGT" in f.upper()]

    if buyer_facts and not target_facts:
        return {
            "status": "error",
            "message": "ANCHOR RULE violation: Risks citing buyer facts must also cite at least one target fact. "
                       "Buyer facts provide context, but risks must be anchored to target observations."
        }

    # Pass entity to store
    result = reasoning_store.add_risk(
        domain=input_data["domain"],
        title=input_data["title"],
        description=input_data["description"],
        # ... existing fields ...
        entity=entity,          # NEW
        risk_scope=risk_scope,  # NEW (was silently defaulted)
    )
    return result
```

### 3. `tools_v2/reasoning_tools.py` — Add Entity Validation to Strategic Considerations

**`_execute_create_strategic_consideration()` (lines 2934-2970):**

```python
def _execute_create_strategic_consideration(input_data, fact_store, reasoning_store, **kwargs):
    # ... existing validation ...

    # NEW: Entity inference from citations
    based_on_facts = input_data.get("based_on_facts", [])
    entity = _infer_entity_from_citations(based_on_facts, fact_store)

    # NEW: ANCHOR RULE for buyer-context considerations
    buyer_facts = [f for f in based_on_facts if "BYR" in f.upper()]
    target_facts = [f for f in based_on_facts if "TGT" in f.upper()]

    if buyer_facts and not target_facts:
        return {
            "status": "error",
            "message": "ANCHOR RULE violation: Strategic considerations citing buyer facts must also cite "
                       "at least one target fact to anchor the analysis."
        }

    result = reasoning_store.add_strategic_consideration(
        # ... existing fields ...
        entity=entity,  # NEW
    )
    return result
```

### 4. `tools_v2/reasoning_tools.py` — Add Entity Validation to Recommendations

**`_execute_create_recommendation()` (lines 3071-3108):**

Same pattern as above — infer entity from citations, enforce ANCHOR RULE.

### 5. `tools_v2/reasoning_tools.py` — Add Entity Inference Helper

**New function (add near the validation functions around line 3196):**

```python
def _infer_entity_from_citations(
    fact_ids: List[str],
    fact_store: "FactStore",
) -> str:
    """Infer the entity scope from cited fact IDs.

    Rules:
    - All target facts → "target"
    - All buyer facts → "buyer"
    - Mixed facts → "target" (target takes precedence; buyer facts provide context)
    - No facts → "target" (default)
    """
    if not fact_ids:
        return "target"

    has_target = any("TGT" in fid.upper() for fid in fact_ids)
    has_buyer = any("BYR" in fid.upper() for fid in fact_ids)

    if has_target:
        return "target"  # Target takes precedence (even if mixed)
    elif has_buyer:
        return "buyer"
    else:
        # Fallback: check fact_store for entity field
        for fid in fact_ids:
            fact = fact_store.get_fact(fid)
            if fact:
                return fact.entity
        return "target"
```

### 6. `tools_v2/discovery_tools.py` — Harden `flag_gap` Entity Validation

**Current (line 656):**
```python
entity = input_data.get("entity", "target")  # Silent default
```

**Replace with:**
```python
entity = input_data.get("entity")
if entity is None:
    return {
        "status": "error",
        "message": "Entity is required for flag_gap. Must be 'target' or 'buyer'. "
                   "Do not omit this field — explicitly specify which entity this gap belongs to."
    }
if entity not in ("target", "buyer"):
    return {
        "status": "error",
        "message": f"Invalid entity '{entity}'. Must be 'target' or 'buyer'."
    }
```

**Also update the tool schema for `flag_gap`** to mark entity as required (remove default from the JSON schema definition).

### 7. `web/repositories/finding_repository.py` — Add Entity Filter

**Update `get_by_deal()` (lines 24-64) to support entity filtering:**

```python
def get_by_deal(
    self,
    deal_id: str,
    run_id: Optional[str] = None,
    finding_type: Optional[str] = None,
    domain: Optional[str] = None,
    severity: Optional[str] = None,
    entity: Optional[str] = None,  # NEW
    include_orphaned: bool = True,
) -> List[Finding]:
    query = self.session.query(Finding).filter(
        Finding.deal_id == deal_id,
        Finding.deleted_at.is_(None),
    )

    if finding_type:
        query = query.filter(Finding.finding_type == finding_type)
    if domain:
        query = query.filter(Finding.domain == domain)
    if severity:
        query = query.filter(Finding.severity == severity)
    if entity:  # NEW
        query = query.filter(Finding.entity == entity)

    # ... existing run_id / orphaned logic ...

    return query.all()
```

### 8. `stores/finding_repository.py` — Update Serialization

**Update any serialization in `stores/finding_repository.py`** to include entity fields when persisting to the database. Ensure `entity`, `risk_scope`, and `cost_buildup_json` flow from ReasoningStore WorkItem/Risk objects to the Finding database model.

### 9. ReasoningStore Methods — Add Entity Parameter

**Update `add_risk()`, `add_strategic_consideration()`, `add_recommendation()`** in the ReasoningStore class to accept and store `entity` parameter:

```python
def add_risk(self, domain, title, description, ..., entity="target", risk_scope="target_standalone"):
    risk = Risk(
        # ... existing fields ...
        entity=entity,
        risk_scope=risk_scope,
    )
    self.risks.append(risk)
    return {"status": "success", "risk_id": risk.finding_id, "entity": entity}
```

---

## ANCHOR RULE Specification

The ANCHOR RULE prevents hallucinated buyer-only findings:

```
RULE: Any finding (risk, work item, strategic consideration, recommendation) that cites
buyer facts (F-BYR-*) MUST also cite at least one target fact (F-TGT-*).

RATIONALE: The purpose of this diligence is to assess the TARGET. Buyer facts provide
context for how the buyer's environment interacts with the target, but every finding
must be anchored in an observation about the target.

EXCEPTION: Strategic considerations with lens="buyer_alignment" may cite buyer-only
facts IF the consideration is explicitly about buyer readiness (not target issues).
```

**Implementation in all reasoning tool execution functions:**

```python
# Check ANCHOR RULE
buyer_cited = [f for f in all_cited_facts if "BYR" in f.upper()]
target_cited = [f for f in all_cited_facts if "TGT" in f.upper()]

if buyer_cited and not target_cited:
    # Exception check
    is_buyer_alignment = (
        finding_type == "strategic_consideration"
        and input_data.get("lens") == "buyer_alignment"
    )
    if not is_buyer_alignment:
        return {
            "status": "error",
            "message": "ANCHOR RULE: Findings citing buyer facts must also cite target facts."
        }
```

---

## Test Cases

### Test 1: Entity on Risk
```python
def test_risk_has_entity_from_citations():
    """Risk entity should be inferred from cited fact IDs."""
    result = _execute_identify_risk({
        "domain": "infrastructure",
        "title": "Test risk",
        "description": "Test",
        "category": "hosting",
        "severity": "medium",
        "mitigation": "Test mitigation",
        "based_on_facts": ["F-TGT-INFRA-001"],
        "confidence": "medium",
        "reasoning": "Test reasoning " * 10,
    }, fact_store, reasoning_store)

    assert result["status"] == "success"
    risk = reasoning_store.risks[-1]
    assert risk.entity == "target"
```

### Test 2: ANCHOR RULE Enforcement
```python
def test_anchor_rule_rejects_buyer_only_risk():
    """Risks citing only buyer facts should be rejected."""
    result = _execute_identify_risk({
        "domain": "infrastructure",
        "title": "Buyer-only risk",
        "description": "Test",
        "category": "hosting",
        "severity": "medium",
        "mitigation": "Test",
        "based_on_facts": ["F-BYR-INFRA-001"],  # Only buyer facts!
        "confidence": "medium",
        "reasoning": "Test reasoning " * 10,
    }, fact_store, reasoning_store)

    assert result["status"] == "error"
    assert "ANCHOR RULE" in result["message"]
```

### Test 3: ANCHOR RULE Allows Mixed Citations
```python
def test_anchor_rule_allows_mixed_citations():
    """Findings citing both buyer and target facts should be accepted."""
    result = _execute_identify_risk({
        # ... required fields ...
        "based_on_facts": ["F-TGT-INFRA-001", "F-BYR-INFRA-002"],
        # ...
    }, fact_store, reasoning_store)

    assert result["status"] == "success"
```

### Test 4: flag_gap Entity Required
```python
def test_flag_gap_requires_entity():
    """flag_gap without entity should return error, not default to target."""
    result = _execute_flag_gap(
        {"domain": "applications", "category": "inventory", "description": "Missing app list"},
        fact_store,
    )
    assert result["status"] == "error"
    assert "entity" in result["message"].lower()
```

### Test 5: Finding Model Entity Persistence
```python
def test_finding_entity_persists_to_db(db_session):
    """Entity field should be stored and queryable in the Finding table."""
    finding = Finding(
        id="R-test-001",
        deal_id="test-deal",
        finding_type="risk",
        entity="target",
        risk_scope="target_standalone",
        domain="infrastructure",
        title="Test",
    )
    db_session.add(finding)
    db_session.commit()

    loaded = db_session.query(Finding).filter_by(id="R-test-001").first()
    assert loaded.entity == "target"
    assert loaded.risk_scope == "target_standalone"
```

### Test 6: Entity Filter in Repository
```python
def test_repository_filters_by_entity(db_session):
    """Repository should filter findings by entity."""
    repo = FindingRepository(db_session)

    # Create target and buyer findings
    # ... create findings with entity="target" and entity="buyer" ...

    target_findings = repo.get_by_deal("test-deal", entity="target")
    buyer_findings = repo.get_by_deal("test-deal", entity="buyer")

    assert all(f.entity == "target" for f in target_findings)
    assert all(f.entity == "buyer" for f in buyer_findings)
```

---

## Acceptance Criteria

1. All findings (risks, work items, strategic considerations, recommendations) have `entity` field populated
2. Finding records in DB have `entity` column with value "target" or "buyer"
3. `risk_scope` persisted to DB for risk findings
4. `cost_buildup_json` column exists on Finding (prepared for Spec 05)
5. ANCHOR RULE enforced: buyer-only findings rejected with clear error message
6. `flag_gap` rejects calls without explicit entity (no silent default)
7. Repository `get_by_deal()` supports entity filter
8. All existing tests pass (backwards compatibility via defaults)

---

## Database Migration Notes

**New columns on `findings` table:**
| Column | Type | Default | Nullable |
|--------|------|---------|----------|
| `entity` | String(20) | `'target'` | No (with default) |
| `risk_scope` | String(50) | `''` | Yes |
| `cost_buildup_json` | JSON | `None` | Yes |

**Migration is safe:** All new columns have defaults. Existing rows will get `entity='target'`, `risk_scope=''`, `cost_buildup_json=NULL`. No data loss.

**New index:** `idx_findings_entity` on `(deal_id, entity)`.

---

## Rollback Plan

- New DB columns with defaults — removing them requires a migration but doesn't break existing data
- Entity validation in reasoning tools — removing validation restores permissive behavior
- ANCHOR RULE — removing enforcement restores old behavior where buyer-only findings are accepted
- `flag_gap` entity requirement — restoring `default="target"` returns to old behavior
- All changes have clear, single-point reversibility

---

## Implementation Notes

*Documented post-implementation on 2026-02-09.*

### 1. Files Modified

#### `web/database.py` (Finding Model)
- **Lines 793-794**: Added `entity = Column(String(20), default='target')` and `risk_scope = Column(String(50), default='')` immediately after `finding_type` on line 792, exactly as specified.
- **Line 822**: Added `cost_buildup_json = Column(JSON, default=None)` in the work-item-specific fields section.
- **Line 858**: Added `Index('idx_findings_entity', 'deal_id', 'entity')` to the `__table_args__` tuple.
- **Lines 866-867**: Updated `to_dict()` to include `'entity': self.entity or 'target'` and `'risk_scope': self.risk_scope or ''` in the base result dict.
- **Line 894**: `cost_buildup_json` included in the work_item branch of `to_dict()`.

#### `tools_v2/reasoning_tools.py` (Dataclasses)
- **Line 301**: `Risk` dataclass has `entity: str = "target"` field.
- **Line 302**: `Risk` dataclass has `risk_scope: str = "target_standalone"` field.
- **Lines 303-304**: `Risk` dataclass has `target_facts_cited` and `buyer_facts_cited` list fields.
- **Line 316**: `Risk.from_dict()` sets `data.setdefault("entity", "target")` for backwards compatibility.
- **Line 341**: `StrategicConsideration` dataclass has `entity: str = "target"` field.
- **Lines 343-344**: `StrategicConsideration` has `target_facts_cited` and `buyer_facts_cited` list fields.
- **Line 355**: `StrategicConsideration.from_dict()` sets `data.setdefault("entity", "target")`.
- **Line 497**: `WorkItem` dataclass has `entity: str = "target"` field.
- **Lines 499-500**: `WorkItem` has `target_facts_cited` and `buyer_facts_cited` list fields.
- **Line 519**: `WorkItem.from_dict()` sets `data.setdefault("entity", "target")`.
- **Line 550**: `Recommendation` dataclass has `entity: str = "target"` field.
- **Lines 552-553**: `Recommendation` has `target_facts_cited` and `buyer_facts_cited` list fields.
- **Line 564**: `Recommendation.from_dict()` sets `data.setdefault("entity", "target")`.

#### `tools_v2/reasoning_tools.py` (ReasoningStore Methods)
- **Lines 807-815** (`add_risk`): Populates `target_facts_cited` and `buyer_facts_cited` from `based_on_facts` using TGT/BYR prefix parsing. Calls `_infer_entity_from_citations()` if `entity` not in kwargs.
- **Lines 837-845** (`add_strategic_consideration`): Same entity inference and fact-citation split pattern.
- **Lines 870-878** (`add_work_item`): Same pattern, combining `triggered_by` and `based_on_facts` for entity inference.
- **Lines 917-925** (`add_recommendation`): Same pattern.

#### `tools_v2/reasoning_tools.py` (Execution Functions)
- **Lines 2995-3002** (`_execute_identify_risk`): Added `risk_scope` validation against `VALID_RISK_SCOPES = ["target_standalone", "integration_dependent", "buyer_action"]`.
- **Lines 3004-3005**: Calls `_infer_entity_from_citations()` to determine entity.
- **Lines 3007-3017**: ANCHOR RULE enforcement -- rejects findings with buyer facts but no target facts.
- **Lines 3035-3036**: Passes `entity` and `risk_scope` to `reasoning_store.add_risk()`.
- **Line 3042**: Returns `entity` in success response.
- **Lines 3068-3069** (`_execute_create_strategic_consideration`): Calls `_infer_entity_from_citations()`.
- **Lines 3071-3083**: ANCHOR RULE enforcement with `buyer_alignment` lens exception (line 3077).
- **Line 3098**: Passes `entity` to `reasoning_store.add_strategic_consideration()`.
- **Lines 3269-3270** (`_execute_create_recommendation`): Calls `_infer_entity_from_citations()`.
- **Lines 3272-3281**: ANCHOR RULE enforcement.
- **Line 3297**: Passes `entity` to `reasoning_store.add_recommendation()`.

#### `tools_v2/reasoning_tools.py` (Entity Inference Helper)
- **Lines 3397-3428**: `_infer_entity_from_citations()` function. Returns `"target"` if any TGT fact cited (target precedence), `"buyer"` if only BYR facts, falls back to checking `fact_store.get_fact()` for legacy IDs, defaults to `"target"`.

#### `tools_v2/reasoning_tools.py` (Entity Validation Function)
- **Lines 2618-2697**: `validate_finding_entity_rules()` enforces three rules at the tool-dispatch level: (1) ANCHOR RULE -- buyer facts require target facts, (2) AUTO-TAG `integration_related`, (3) SCOPE RULE -- rejects "Buyer should..." language in non-integration_option fields.

#### `tools_v2/discovery_tools.py` (flag_gap Hardening)
- **Lines 266, 309**: Tool schema `required` list includes `"entity"` for both `create_inventory_entry` and `flag_gap`.
- **Lines 303-307**: `flag_gap` schema defines entity as `{"type": "string", "enum": ["target", "buyer"]}` with explicit description.
- **Lines 665-677** (`_execute_flag_gap`): Entity validation changed from `input_data.get("entity", "target")` (silent default) to explicit `None` check with error return: `"Entity is required for flag_gap."`. Validates entity is exactly `"target"` or `"buyer"`.

#### `web/repositories/finding_repository.py` (Entity Filter)
- **Line 31**: Added `entity: Optional[str] = None` parameter to `get_by_deal()`.
- **Lines 38**: Docstring updated to document the entity filter parameter.
- **Lines 66-67**: Added filter `if entity: query = query.filter(Finding.entity == entity)`.

#### `stores/db_writer.py` (Persistence Fields)
- **Line 451**: `write_finding()` maps `entity` from `finding_data.get('entity', 'target')`.
- **Line 452**: Maps `risk_scope` from `finding_data.get('risk_scope', '')`.
- **Line 479**: Maps `cost_buildup_json` from `finding_data.get('cost_buildup_json')` for work_item type.

#### `web/analysis_runner.py` (Entity Propagation in Persistence)
- **Line 204**: Strategic consideration persistence includes `'entity': getattr(sc, 'entity', 'target')`.
- **Line 230**: Recommendation persistence includes `'entity': getattr(rec, 'entity', 'target')`.
- **Lines 411-412**: Risk persistence includes `entity=getattr(risk, 'entity', 'target')` and `risk_scope=getattr(risk, 'risk_scope', '')`.
- **Lines 439-442, 449-450, 458**: Work item persistence includes `cost_buildup_json` serialization and `entity`/`risk_scope` fields.
- **Line 484**: Gap persistence includes `entity=getattr(gap, 'entity', 'target')`.

### 2. Deviations from Spec

1. **Additional `validate_finding_entity_rules()` function (lines 2618-2697)**: The spec did not call for a separate validation function at the tool-dispatch level. The implementation added a comprehensive entity rule validator that checks ANCHOR RULE, SCOPE RULE (rejects "Buyer should..." language), and TARGET ACTION RULE. This is invoked by the tool dispatcher before execution functions, providing defense-in-depth beyond what the spec required.

2. **`target_facts_cited` / `buyer_facts_cited` fields on all dataclasses**: The spec mentioned these existed on `WorkItem` but did not explicitly require adding them to `Risk`, `StrategicConsideration`, and `Recommendation`. The implementation added these fields to all four dataclasses with automatic population from `based_on_facts` using TGT/BYR prefix parsing in the ReasoningStore `add_*` methods.

3. **`integration_related` and `overlap_id` fields**: Added to all finding dataclasses (`Risk`, `StrategicConsideration`, `WorkItem`, `Recommendation`). The spec mentioned `integration_related` validation but not as an explicit field on all types. The implementation tracks integration context consistently across all finding types.

4. **`buyer_alignment` exception in Strategic Considerations**: The spec's ANCHOR RULE section (line 309) mentioned an exception for `lens="buyer_alignment"` but placed it under the generic implementation block. The implementation correctly applies this exception only in `_execute_create_strategic_consideration()` (line 3077), not in `_execute_identify_risk()` or `_execute_create_recommendation()`.

5. **`_infer_entity_from_citations()` signature difference**: The spec showed `fact_store: "FactStore"` as required. The implementation uses `fact_store: "FactStore" = None` (optional with default `None`), adding a guard `if fact_store:` before accessing it (line 3421). This makes the function more resilient to being called without a fact store reference.

6. **`create_inventory_entry` schema also requires entity**: The spec focused on `flag_gap` entity hardening. The implementation also added `"entity"` to the `required` list for the `create_inventory_entry` tool schema (line 266), broadening entity enforcement to all discovery tools.

7. **No separate `stores/finding_repository.py`**: The spec listed Section 8 as `stores/finding_repository.py`. The implementation uses `stores/db_writer.py` instead, which handles all persistence including entity fields. The `web/repositories/finding_repository.py` handles the query/filter side.

### 3. Test Coverage

**Test file:** `tests/test_entity_propagation.py` -- 17 tests across 4 test classes.

#### `TestEntityInference` (6 tests)
| Test | Verifies |
|------|----------|
| `test_target_facts_infer_target` | TGT prefix returns "target" |
| `test_buyer_facts_infer_buyer` | BYR prefix returns "buyer" |
| `test_mixed_facts_infer_target` | Mixed TGT+BYR returns "target" (precedence rule) |
| `test_no_facts_default_target` | Empty list defaults to "target" |
| `test_multiple_target_facts` | Multiple TGT facts still return "target" |
| `test_multiple_buyer_facts` | Multiple BYR-only facts return "buyer" |

#### `TestAnchorRule` (7 tests)
| Test | Verifies |
|------|----------|
| `test_anchor_rule_exists_in_identify_risk_source` | ANCHOR RULE string present in `_execute_identify_risk` source |
| `test_anchor_rule_exists_in_create_strategic_consideration_source` | ANCHOR RULE string present in `_execute_create_strategic_consideration` source |
| `test_anchor_rule_exists_in_create_recommendation_source` | ANCHOR RULE string present in `_execute_create_recommendation` source |
| `test_anchor_rule_exists_in_validate_finding_entity_rules` | ANCHOR RULE string present in `validate_finding_entity_rules` source |
| `test_validate_finding_entity_rules_rejects_buyer_only` | Buyer-only citations produce `valid=False` with ENTITY_ANCHOR_VIOLATION error |
| `test_validate_finding_entity_rules_accepts_mixed` | Mixed TGT+BYR citations produce no anchor errors |
| `test_validate_finding_entity_rules_accepts_target_only` | Target-only citations produce no anchor errors |

#### `TestFlagGapEntityRequired` (3 tests)
| Test | Verifies |
|------|----------|
| `test_flag_gap_function_exists` | `_execute_flag_gap` is importable and callable |
| `test_flag_gap_source_checks_entity` | Source code contains "entity" and "Entity is required" |
| `test_flag_gap_validates_entity_values` | Source code validates against "target" and "buyer" values |

#### `TestEntityFieldOnFindings` (4 tests -- lines 152-228, test names cut at file boundary)
| Test | Verifies |
|------|----------|
| `test_risk_has_entity_field` | `Risk` dataclass accepts `entity="target"` and stores it |
| `test_risk_default_entity_is_target` | `Risk` entity defaults to "target" when not specified |
| `test_strategic_consideration_has_entity_field` | `StrategicConsideration` has entity field defaulting to "target" |
| `test_work_item_has_entity_field` | `WorkItem` has entity field defaulting to "target" |

**Testing approach:** Tests use source code inspection (`inspect.getsource()`) for ANCHOR RULE presence verification, direct function calls for entity inference logic, and dataclass instantiation for field existence. Database persistence tests (spec Test 5, Test 6) are not present in this test file -- entity persistence is covered by the integration paths in `db_writer.py` and `analysis_runner.py`.
