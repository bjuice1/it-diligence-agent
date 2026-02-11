# Spec 11: Organization Bridge Integration

**Status:** Draft
**Created:** 2026-02-11
**Complexity:** Medium
**Estimated Implementation:** 3-4 hours

---

## Overview

This specification defines the integration of hierarchy detection (spec 08) and assumption generation (spec 09) into the organization bridge service (`services/organization_bridge.py`). The bridge service orchestrates the adaptive extraction flow: detect hierarchy presence → extract observed data → generate assumptions if needed → merge all data into inventory.

**Why this exists:** The bridge service is the central integration point between fact extraction (discovery phase) and inventory population (analysis phase). This is where the conditional logic "extract vs assume" must live to ensure seamless operation without changing upstream (discovery agents) or downstream (UI, cost engine) components.

**Key principle:** Feature-flagged, backward-compatible integration. Existing behavior unchanged when flag disabled; new adaptive behavior enabled by default.

---

## Architecture

### Component Positioning

```
Discovery Phase (completed)
    ↓
FactStore (org facts populated)
    ↓
[THIS COMPONENT] → organization_bridge.py
    ├─→ Step 1: Detect hierarchy (spec 08)
    ├─→ Step 2: Extract observed data (existing logic)
    ├─→ Step 3: Generate assumptions if needed (spec 09)
    ├─→ Step 4: Merge assumptions into FactStore
    └─→ Step 5: Create inventory from all facts (spec 10)
    ↓
OrganizationDataStore (populated inventory)
    ↓
Downstream consumers (UI, cost engine, reports)
```

### Dependencies

**Input:**
- FactStore with organization facts (from discovery)
- Target/buyer entity designation
- Deal ID for data isolation
- Optional company profile (for assumption engine)

**Output:**
- OrganizationDataStore with inventory items (observed + assumed)
- Status indicator (success/no_org_facts/no_facts)
- Logging of detection results and assumptions generated

**Consumes:**
- Spec 08: `detect_hierarchy_presence()`, `HierarchyPresence`
- Spec 09: `generate_org_assumptions()`, `OrganizationAssumption`
- Spec 10: Enhanced inventory schema with data_source fields

**External Dependencies:**
- `stores.fact_store.FactStore`
- `models.organization_stores.OrganizationDataStore`
- `config_v2.ENABLE_ORG_ASSUMPTIONS` (feature flag)

---

## Specification

### 1. Feature Flag Configuration

**File:** `config_v2.py`

```python
# Organization Assumption Feature Flags (spec 11)
ENABLE_ORG_ASSUMPTIONS = True          # Master switch for adaptive extraction
ENABLE_BUYER_ORG_ASSUMPTIONS = False   # Generate assumptions for buyer entity too?

# Logging verbosity for assumption generation
LOG_ASSUMPTION_GENERATION = True       # Log assumptions at INFO level
LOG_HIERARCHY_DETECTION = True         # Log detection results at INFO level
```

**Environment Variable Override:**

```bash
# .env file
ENABLE_ORG_ASSUMPTIONS=true
ENABLE_BUYER_ORG_ASSUMPTIONS=false
```

### 2. Updated Bridge Function Signature

**File:** `services/organization_bridge.py`

**Current Signature:**

```python
def build_organization_from_facts(
    fact_store: FactStore,
    target_name: str = "Target",
    deal_id: str = ""
) -> Tuple[OrganizationDataStore, str]:
    """Build OrganizationDataStore from facts."""
    pass
```

**Enhanced Signature:**

```python
def build_organization_from_facts(
    fact_store: FactStore,
    target_name: str = "Target",
    deal_id: str = "",
    entity: str = "target",                          # NEW: explicit entity parameter
    company_profile: Optional[Dict[str, Any]] = None,  # NEW: for assumption engine
    enable_assumptions: Optional[bool] = None         # NEW: override feature flag
) -> Tuple[OrganizationDataStore, str]:
    """
    Build OrganizationDataStore from facts with adaptive extraction.

    Args:
        fact_store: FactStore containing organization facts
        target_name: Name of target company (for display)
        deal_id: Deal ID for data isolation
        entity: "target" or "buyer" (which entity to analyze)
        company_profile: Optional company context (industry, size) for assumptions
        enable_assumptions: Override ENABLE_ORG_ASSUMPTIONS flag

    Returns:
        Tuple of (OrganizationDataStore, status) where status is:
        - "success": Org data was found and built
        - "success_with_assumptions": Data built using assumptions
        - "no_org_facts": Analysis ran but no org facts found
        - "no_facts": No facts at all in the store

    Flow (spec 11):
        1. Detect hierarchy presence (spec 08)
        2. Extract observed data (existing logic)
        3. If hierarchy PARTIAL/MISSING and assumptions enabled:
            a. Generate assumptions (spec 09)
            b. Merge into FactStore
            c. Extract again (now includes assumptions)
        4. Return populated OrganizationDataStore
    """
    pass  # Implementation below
```

### 3. Integration Algorithm

**Main Flow:**

```python
def build_organization_from_facts(
    fact_store: FactStore,
    target_name: str = "Target",
    deal_id: str = "",
    entity: str = "target",
    company_profile: Optional[Dict[str, Any]] = None,
    enable_assumptions: Optional[bool] = None
) -> Tuple[OrganizationDataStore, str]:
    """Build OrganizationDataStore with adaptive extraction."""

    # Determine if assumptions are enabled
    assumptions_enabled = (
        enable_assumptions if enable_assumptions is not None
        else ENABLE_ORG_ASSUMPTIONS
    )

    # Check entity-specific flag for buyer assumptions
    if entity == "buyer" and not ENABLE_BUYER_ORG_ASSUMPTIONS:
        assumptions_enabled = False

    # Get deal_id from fact_store if not provided
    if not deal_id and hasattr(fact_store, 'deal_id') and fact_store.deal_id:
        deal_id = fact_store.deal_id

    # Initialize empty store
    store = OrganizationDataStore()

    # Check if fact store has any facts at all
    total_facts = len(fact_store.facts) if fact_store.facts else 0
    if total_facts == 0:
        logger.warning("No facts at all in fact store")
        return store, "no_facts"

    # CRITICAL (P0 FIX): Validate entity field on facts before filtering
    all_org_facts = [f for f in fact_store.facts if f.domain == "organization"]

    facts_missing_entity = [
        f.item for f in all_org_facts
        if not hasattr(f, 'entity') or f.entity is None or f.entity == ""
    ]

    if facts_missing_entity:
        logger.error(
            f"Found {len(facts_missing_entity)} org facts with missing entity field. "
            f"This indicates an upstream bug. Facts: {facts_missing_entity[:5]}"
        )
        # Option 1: Fail fast (recommended for data integrity)
        raise ValueError(
            f"Entity validation failed: {len(facts_missing_entity)} org facts "
            f"have missing entity field. Cannot proceed with adaptive extraction."
        )
        # Option 2: Filter out and continue (permissive, risks hiding bugs)
        # all_org_facts = [f for f in all_org_facts if hasattr(f, 'entity') and f.entity]
        # logger.warning(f"Filtered out {len(facts_missing_entity)} facts with missing entity")

    # Get organization domain facts for entity (now safe)
    org_facts = [f for f in all_org_facts if f.entity == entity]

    if not org_facts:
        logger.warning(f"No organization facts found for entity: {entity}")
        return store, "no_org_facts"

    # STEP 1: Detect hierarchy presence (spec 08)
    from services.org_hierarchy_detector import detect_hierarchy_presence

    hierarchy_presence = detect_hierarchy_presence(fact_store, entity=entity)

    if LOG_HIERARCHY_DETECTION:
        logger.info(f"Hierarchy detection for {entity}: {hierarchy_presence.status.value} "
                    f"(confidence: {hierarchy_presence.confidence:.2f})")

    # STEP 2: Extract observed data (existing logic)
    # [Existing extraction code here - unchanged]
    # This populates `store` with observed data from org_facts
    _extract_observed_org_data(fact_store, store, entity, deal_id)

    # STEP 3: Generate and merge assumptions if needed
    status = "success"
    if assumptions_enabled:
        from services.org_assumption_engine import generate_org_assumptions
        from services.org_hierarchy_detector import HierarchyPresenceStatus

        # Generate assumptions for PARTIAL or MISSING hierarchy
        if hierarchy_presence.status in [
            HierarchyPresenceStatus.PARTIAL,
            HierarchyPresenceStatus.MISSING
        ]:
            assumptions = generate_org_assumptions(
                fact_store=fact_store,
                hierarchy_presence=hierarchy_presence,
                entity=entity,
                company_profile=company_profile
            )

            if assumptions:
                # STEP 3a: Remove old assumptions (P0 fix - prevent pollution)
                _remove_old_assumptions_from_fact_store(
                    fact_store=fact_store,
                    entity=entity
                )

                # STEP 3b: Merge new assumptions into FactStore
                # (includes idempotency check - P0 fix)
                _merge_assumptions_into_fact_store(
                    fact_store=fact_store,
                    assumptions=assumptions,
                    deal_id=deal_id,
                    entity=entity  # For idempotency check
                )

                # Re-extract with assumptions now included
                _extract_assumed_org_data(fact_store, store, entity, deal_id, assumptions)

                status = "success_with_assumptions"

                if LOG_ASSUMPTION_GENERATION:
                    logger.info(f"Generated and merged {len(assumptions)} assumptions for {entity}")

    return store, status
```

### 4. Helper Functions

**Extract Observed Data (Existing Logic, Refactored):**

```python
def _extract_observed_org_data(
    fact_store: FactStore,
    store: OrganizationDataStore,
    entity: str,
    deal_id: str
) -> None:
    """
    Extract observed organization data from facts.

    This is the existing extraction logic, unchanged except:
    - Filters facts by entity
    - Only processes facts with data_source != "assumed" (or missing data_source)
    """
    org_facts = [
        f for f in fact_store.facts
        if f.domain == "organization"
        and f.entity == entity
        and f.details.get('data_source', 'observed') == 'observed'
    ]

    # [Existing extraction code from current organization_bridge.py]
    # Process leadership_facts, central_it_facts, roles_facts, etc.
    # Create StaffMember objects, populate store.staff_members, etc.
    # (No changes needed to existing logic beyond filtering)
```

**Remove Old Assumptions (P0 Fix):**

```python
def _remove_old_assumptions_from_fact_store(
    fact_store: FactStore,
    entity: str
) -> int:
    """
    Remove old assumptions for an entity from FactStore.

    CRITICAL (P0 FIX): Prevents stale assumptions from polluting
    inventory when source data is updated or assumptions re-generated.

    Args:
        fact_store: FactStore to clean
        entity: "target" or "buyer"

    Returns:
        Number of assumptions removed
    """
    original_count = len(fact_store.facts)

    # Filter out assumed facts for this entity
    fact_store.facts = [
        f for f in fact_store.facts
        if not (f.domain == "organization" and
                f.entity == entity and
                f.details.get('data_source') == 'assumed')
    ]

    removed_count = original_count - len(fact_store.facts)

    if removed_count > 0:
        logger.info(f"Removed {removed_count} old assumptions for {entity} (cleanup)")

    return removed_count
```

**Merge Assumptions into FactStore:**

```python
def _merge_assumptions_into_fact_store(
    fact_store: FactStore,
    assumptions: List[OrganizationAssumption],
    deal_id: str,
    entity: str
) -> None:
    """
    Merge synthetic assumptions into FactStore as Fact objects.

    CRITICAL (P0 FIX): Includes idempotency protection to prevent
    duplicate assumptions if bridge is called multiple times.

    This allows downstream extraction logic to treat assumptions
    the same as observed facts (unified processing).
    """
    from stores.fact_store import Fact

    # IDEMPOTENCY CHECK: Find existing assumptions for this entity
    existing_assumption_keys = set()
    for fact in fact_store.facts:
        if (fact.domain == "organization" and
            fact.entity == entity and
            fact.details.get('data_source') == 'assumed'):
            # Create unique key from item + category
            key = f"{fact.category}:{fact.item}"
            existing_assumption_keys.add(key)

    logger.debug(f"Found {len(existing_assumption_keys)} existing assumptions for {entity}")

    # Filter out assumptions that already exist
    new_assumptions = []
    duplicate_count = 0

    for assumption in assumptions:
        key = f"{assumption.category}:{assumption.item}"
        if key in existing_assumption_keys:
            duplicate_count += 1
            logger.debug(f"Skipping duplicate assumption: {assumption.item}")
        else:
            new_assumptions.append(assumption)

    if duplicate_count > 0:
        logger.info(f"Skipped {duplicate_count} duplicate assumptions (idempotency protection)")

    # Merge only new assumptions
    for assumption in new_assumptions:
        # Convert assumption to Fact
        fact_dict = assumption.to_fact()

        # Create Fact object
        synthetic_fact = Fact(
            item=fact_dict['item'],
            category=fact_dict['category'],
            domain=fact_dict['domain'],
            entity=fact_dict['entity'],
            details=fact_dict['details'],
            evidence=fact_dict['evidence'],
            confidence=fact_dict.get('confidence', 0.7),
            deal_id=deal_id
        )

        # Add to fact store
        fact_store.add_fact(synthetic_fact)

    logger.info(f"Merged {len(new_assumptions)} new assumptions into FactStore "
                f"(skipped {duplicate_count} duplicates)")
```

**Extract Assumed Data (New Logic):**

```python
def _extract_assumed_org_data(
    fact_store: FactStore,
    store: OrganizationDataStore,
    entity: str,
    deal_id: str,
    assumptions: List[OrganizationAssumption]
) -> None:
    """
    Extract assumed organization data from synthetic facts.

    This processes facts with data_source="assumed" and adds them
    to the OrganizationDataStore alongside observed data.

    Uses same extraction logic as observed data, but:
    - Marks inventory items with data_source="assumed"
    - Includes confidence scores and assumption_basis
    """
    assumed_facts = [
        f for f in fact_store.facts
        if f.domain == "organization"
        and f.entity == entity
        and f.details.get('data_source') == 'assumed'
    ]

    # Process assumed facts (same categories as observed)
    for fact in assumed_facts:
        # Create StaffMember with data_source metadata
        staff_member = _create_staff_from_fact(
            fact=fact,
            deal_id=deal_id
        )

        # Add to store
        store.staff_members.append(staff_member)

    logger.debug(f"Extracted {len(assumed_facts)} assumed org facts")
```

**Updated Staff Creation (Enhanced for Spec 10):**

```python
def _create_staff_from_fact(fact: Fact, deal_id: str = "") -> StaffMember:
    """
    Create StaffMember from fact with data source metadata (spec 10).

    Enhanced to extract and preserve:
    - data_source ("observed" | "assumed" | "hybrid")
    - confidence_score
    - assumption_basis
    """
    details = fact.details or {}

    # Extract data source metadata (spec 10)
    data_source = details.get('data_source', 'observed')
    confidence = fact.confidence if hasattr(fact, 'confidence') else 1.0
    assumption_basis = details.get('assumption_basis', '')

    # Extract org fields
    role = fact.item
    team = details.get('team', '')
    department = details.get('department', '')
    reports_to = details.get('reports_to', '')
    headcount = details.get('count', details.get('headcount', 1))
    annual_cost = details.get('annual_cost', 0)

    # Determine role category
    role_category = _determine_category_from_name(role, default=RoleCategory.OTHER)

    # Create StaffMember
    return StaffMember(
        staff_id=gen_id("staff"),
        name=details.get('name', ''),
        role=role,
        team=team,
        department=department,
        reports_to=reports_to,
        role_category=role_category,
        employment_type=EmploymentType.FTE,
        annual_cost=annual_cost,
        tenure_years=0,
        headcount=headcount,
        deal_id=deal_id,

        # NEW: Data source metadata (spec 10)
        data_source=data_source,
        confidence_score=confidence,
        assumption_basis=assumption_basis if data_source in ['assumed', 'hybrid'] else None,
    )
```

### 5. Error Handling

**Graceful Degradation:**

```python
def build_organization_from_facts(
    fact_store: FactStore,
    target_name: str = "Target",
    deal_id: str = "",
    entity: str = "target",
    company_profile: Optional[Dict[str, Any]] = None,
    enable_assumptions: Optional[bool] = None
) -> Tuple[OrganizationDataStore, str]:
    """Build OrganizationDataStore with error handling."""

    try:
        # [Main integration logic from section 3]
        pass

    except Exception as e:
        # Catch any errors in detection/assumption generation
        logger.error(f"Error in adaptive org extraction for {entity}: {e}", exc_info=True)

        # Fallback: try to extract observed data only
        try:
            store = OrganizationDataStore()
            _extract_observed_org_data(fact_store, store, entity, deal_id)
            logger.warning(f"Fell back to observed-only extraction for {entity}")
            return store, "success_fallback"

        except Exception as fallback_error:
            logger.error(f"Fallback extraction also failed: {fallback_error}", exc_info=True)
            return OrganizationDataStore(), "error"
```

**Error States:**

| Status | Meaning | User Impact |
|--------|---------|-------------|
| `success` | All data extracted (observed only or FULL hierarchy) | Normal operation |
| `success_with_assumptions` | Observed + assumed data merged | UI shows badges for assumed items |
| `success_fallback` | Error in assumptions, fell back to observed only | Partial data, logged warning |
| `no_org_facts` | No org facts found for entity | Empty org section, VDR gap |
| `no_facts` | No facts at all in FactStore | Analysis failed, UI shows error |
| `error` | Unrecoverable error | UI shows error message, contact support |

### 6. Logging and Observability

**Log Messages:**

```python
# Detection results
logger.info(f"Hierarchy detection for {entity}: {status.value} "
            f"(confidence: {confidence:.2f}, "
            f"roles: {total_role_count}, "
            f"reports_to: {reports_to_percentage:.0%})")

# Assumption generation
logger.info(f"Generating assumptions for {entity}: "
            f"industry={industry}, headcount={headcount}, "
            f"expected_layers={layers}")

logger.info(f"Generated {len(assumptions)} assumptions for {entity}")

# Merge and extraction
logger.debug(f"Merged {len(assumptions)} assumptions into FactStore")
logger.debug(f"Extracted {len(assumed_facts)} assumed org facts")

# Final results
logger.info(f"Organization bridge completed for {entity}: "
            f"status={status}, "
            f"observed_items={observed_count}, "
            f"assumed_items={assumed_count}")
```

**Metrics (if metrics system exists):**

```python
# Record metrics for monitoring
metrics.counter('org_extraction.detection.full', 1 if status == FULL else 0)
metrics.counter('org_extraction.detection.partial', 1 if status == PARTIAL else 0)
metrics.counter('org_extraction.detection.missing', 1 if status == MISSING else 0)

metrics.counter('org_extraction.assumptions_generated', len(assumptions))
metrics.gauge('org_extraction.assumed_items_ratio',
              assumed_count / (observed_count + assumed_count))
```

---

## Verification Strategy

### Unit Tests

**File:** `tests/test_org_bridge_integration.py`

**Test Cases:**

1. **test_bridge_full_hierarchy_no_assumptions**
   - Input: Facts with FULL hierarchy
   - Expected: Observed data only, status="success", no assumptions generated

2. **test_bridge_missing_hierarchy_with_assumptions**
   - Input: Facts with MISSING hierarchy, assumptions enabled
   - Expected: Observed + assumed data, status="success_with_assumptions"

3. **test_bridge_partial_hierarchy_gap_filling**
   - Input: Facts with PARTIAL hierarchy, assumptions enabled
   - Expected: Observed + gap-filling assumptions merged

4. **test_bridge_assumptions_disabled**
   - Input: MISSING hierarchy, assumptions disabled via flag
   - Expected: Observed data only, no assumptions, status="success"

5. **test_bridge_buyer_entity_assumptions_disabled**
   - Input: Buyer entity, MISSING hierarchy, ENABLE_BUYER_ORG_ASSUMPTIONS=False
   - Expected: No assumptions for buyer

6. **test_bridge_error_graceful_fallback**
   - Input: Mock exception in assumption generation
   - Expected: Falls back to observed-only, status="success_fallback", logged error

7. **test_bridge_entity_filtering**
   - Input: Facts for both target and buyer
   - Expected: Only target facts processed when entity="target"

8. **test_bridge_assumption_merge_preserves_observed**
   - Input: Observed facts + assumptions
   - Expected: Both present in final store, no overwriting

### Integration Tests

**File:** `tests/integration/test_adaptive_org_extraction.py`

**Test Cases:**

1. **test_full_pipeline_with_assumptions**
   - Run discovery → bridge with assumptions → UI rendering
   - Verify end-to-end flow works

2. **test_cost_engine_uses_assumed_data**
   - Generate assumptions, run cost estimation
   - Verify assumed roles contribute to cost calculations

3. **test_vdr_gaps_populated_from_detection**
   - MISSING hierarchy generates VDR gap entries
   - Verify gaps list matches detection gaps

### Manual Verification

**Steps:**

1. Run on real VDR doc with minimal org data
2. Check logs for detection + assumption messages
3. Verify UI shows mixed observed/assumed inventory
4. Check cost estimates include assumed roles

**Success Criteria:**
- Pipeline completes without errors
- Mixed data sources visible in UI
- Logs show clear detection → assumption → merge flow

---

## Benefits

### Why This Approach

**Bridge service as integration point** provides:
- Single place to add conditional logic (not scattered)
- No changes to discovery agents (upstream isolation)
- No changes to UI/cost engine (downstream isolation)
- Easy to test (mock detection/assumption components)

**Feature flag control** provides:
- Safe rollout (disable if issues arise)
- A/B testing capability (compare with/without assumptions)
- Entity-specific control (target vs buyer)

**Graceful degradation** provides:
- Robustness (errors don't crash pipeline)
- Fallback to observed-only mode (partial success better than failure)
- Clear error states for debugging

---

## Expectations

### Success Metrics

**Correctness:**
- 100% of FULL hierarchy cases skip assumption generation
- 100% of MISSING cases generate assumptions (when enabled)
- Zero cross-entity contamination (target/buyer isolation)

**Performance:**
- Bridge integration adds <200ms to org extraction time
- Assumption generation <50ms (from spec 09)
- Detection <100ms (from spec 08)
- Total overhead: ~250-350ms (acceptable for M&A timescales)

**Reliability:**
- Zero crashes (errors caught and logged)
- Fallback succeeds in 95%+ of error cases
- All errors logged with context for debugging

---

## Risks & Mitigations

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Assumption generation throws exception** | Bridge fails, no org data | Low | Try-catch with fallback to observed-only |
| **FactStore merge corrupts existing facts** | Data integrity issues | Very Low | Merge adds new facts only, doesn't modify existing |
| **Detection false positive (FULL when actually PARTIAL)** | Assumptions not triggered, gaps remain | Low | Conservative thresholds (80% for FULL), log detection results |
| **Infinite loop if assumptions trigger re-detection** | Hang | Very Low | Detection runs once only (before assumptions), not re-triggered |

### Implementation Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Feature flag not respected** | Assumptions run when disabled | Low | Test flag behavior explicitly, check at function entry |
| **Entity filtering fails** | Buyer assumptions for target | Low | Entity parameter required, tested in entity_propagation tests |
| **Status strings inconsistent** | Downstream parsing breaks | Low | Use constants, document status values |

---

## Results Criteria

### Acceptance Criteria

- [ ] Feature flags in config_v2.py (ENABLE_ORG_ASSUMPTIONS, ENABLE_BUYER_ORG_ASSUMPTIONS)
- [ ] build_organization_from_facts() updated with new parameters
- [ ] Integration algorithm implemented (detect → extract → assume → merge)
- [ ] Helper functions: _extract_observed_org_data, _merge_assumptions_into_fact_store, _extract_assumed_org_data
- [ ] Error handling with graceful fallback
- [ ] Logging at INFO level for detection and assumptions
- [ ] Status strings documented and tested
- [ ] All unit tests pass (8+ tests)
- [ ] Integration tests pass (3+ tests)
- [ ] Performance overhead <350ms

---

## Dependencies

**Depends On:**
- Spec 08: Hierarchy detection (detect_hierarchy_presence)
- Spec 09: Assumption generation (generate_org_assumptions)
- Spec 10: Inventory schema (data_source fields)

**Enables:**
- Spec 12: Testing strategy (validates integration)
- Full adaptive org feature (end-to-end)

**Files Modified:**
- `services/organization_bridge.py` (~150 lines added, ~50 lines modified)
- `config_v2.py` (+5 lines for feature flags)

**Files Created:**
- None (all logic in existing bridge service)

---

## Open Questions

**Q1: Should assumptions be persisted in database or generated on-the-fly?**
- Decision: Persist in FactStore (database-backed if fact persistence enabled). Rationale: consistency, auditability, no re-generation on UI refresh.

**Q2: Should re-extraction be incremental or full?**
- Decision: Full re-extraction (simpler). Assumption facts are few (<20), negligible performance impact.

---

## Implementation Checklist

- [ ] Add feature flags to config_v2.py
- [ ] Update build_organization_from_facts() signature
- [ ] Implement main integration algorithm (detect → extract → assume → merge)
- [ ] Refactor existing extraction into _extract_observed_org_data()
- [ ] Implement _merge_assumptions_into_fact_store()
- [ ] Implement _extract_assumed_org_data()
- [ ] Update _create_staff_from_fact() with data_source metadata (spec 10)
- [ ] Add error handling with graceful fallback
- [ ] Add logging for detection, assumptions, merge
- [ ] Create unit tests (8+ tests)
- [ ] Create integration tests (3+ tests)
- [ ] Test feature flag behavior (on/off/buyer-specific)
- [ ] Verify performance overhead <350ms
- [ ] Update documentation (README, docstrings)

---

**Estimated Implementation Time:** 3-4 hours
**Confidence:** High (plumbing logic, well-defined interfaces)
