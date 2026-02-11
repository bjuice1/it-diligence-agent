# Spec 12: Organization Testing Strategy

**Status:** Draft
**Created:** 2026-02-11
**Complexity:** Medium
**Estimated Implementation:** 4-5 hours

---

## Overview

This specification defines the comprehensive testing strategy for the adaptive organization extraction feature (specs 08-11). Testing covers four layers: unit tests for individual components, integration tests for cross-component flows, golden fixture tests for regression, and end-to-end tests for the full pipeline.

**Why this exists:** The adaptive org feature touches 4 major components (detector, assumption engine, schema, bridge) and introduces conditional logic. Without rigorous testing, edge cases (borderline thresholds, mixed data sources, error conditions) could cause production failures. This strategy ensures high confidence in correctness and reliability.

**Key principle:** Test both paths (extract-only AND extract+assume) with equal rigor. Existing behavior must remain unchanged (regression protection).

---

## Architecture

### Testing Pyramid

```
           End-to-End (2-3 tests)
          /                      \
    Integration (10-15 tests)
   /                                \
Unit Tests (30-40 tests)
```

**Layer Breakdown:**

1. **Unit Tests (30-40 tests):** Individual functions in isolation
   - Detector logic (7+ tests)
   - Assumption generation (9+ tests)
   - Schema validation (6+ tests)
   - Bridge helpers (8+ tests)

2. **Integration Tests (10-15 tests):** Cross-component flows
   - Detector → Assumption engine (3 tests)
   - Assumption engine → FactStore → Bridge (3 tests)
   - Bridge → Inventory → UI (3 tests)
   - Error paths and fallback (2 tests)

3. **Golden Fixture Tests (3-5 tests):** Regression protection
   - Existing docs with FULL hierarchy (no change)
   - New docs with MISSING hierarchy (new path)
   - Mixed entity docs (target + buyer isolation)

4. **End-to-End Tests (2-3 tests):** Full pipeline validation
   - Document ingestion → Discovery → Bridge → UI rendering
   - Cost estimation with assumed data
   - VDR gap generation from detection

---

## Specification

### 1. Unit Tests by Component

#### 1.1 Hierarchy Detector (Spec 08)

**File:** `tests/test_org_hierarchy_detector.py`

**Test Matrix:**

| Test Name | Input | Expected Output |
|-----------|-------|-----------------|
| `test_detect_full_hierarchy` | 10 roles, 90% reports_to, layers mentioned | status=FULL, confidence≥0.8 |
| `test_detect_partial_hierarchy_mid_range` | 8 roles, 50% reports_to, no layers | status=PARTIAL, confidence 0.5-0.7 |
| `test_detect_missing_hierarchy` | 5 roles, 0% reports_to, no layers/chart | status=MISSING, confidence≥0.6, gaps populated |
| `test_detect_borderline_80_percent` | 10 roles, 79% reports_to (just below threshold) | status=PARTIAL, confidence penalty |
| `test_detect_borderline_30_percent` | 10 roles, 31% reports_to (just above threshold) | status=PARTIAL |
| `test_detect_conflicting_signals` | org_chart=True, 0% reports_to | confidence penalty applied |
| `test_detect_empty_facts` | Empty FactStore | status=UNKNOWN, confidence=0.0 |
| `test_detect_entity_filtering` | Target + buyer facts | Only target analyzed when entity="target" |
| `test_detect_high_confidence_full` | 95% reports_to, layers + chart | confidence≥0.9 |
| `test_detect_gaps_identification` | MISSING status | gaps list includes all 4 categories |

**Example Test:**

```python
def test_detect_full_hierarchy():
    """Test detection of complete hierarchy (FULL status)."""
    # Arrange
    fact_store = FactStore()
    for i in range(10):
        fact_store.add_fact(Fact(
            item=f"Role {i}",
            category="roles",
            domain="organization",
            entity="target",
            details={'reports_to': f'Manager {i // 2}'},
            evidence={'exact_quote': 'Org chart shows 3 management layers'},
            confidence=0.95
        ))

    # Act
    result = detect_hierarchy_presence(fact_store, entity="target")

    # Assert
    assert result.status == HierarchyPresenceStatus.FULL
    assert result.confidence >= 0.8
    assert result.has_reports_to is True
    assert result.roles_with_reports_to == 10
    assert result.has_explicit_layers is True
    assert len(result.gaps) == 0
```

#### 1.2 Assumption Engine (Spec 09)

**File:** `tests/test_org_assumption_engine.py`

**Test Matrix:**

| Test Name | Input | Expected Output |
|-----------|-------|-----------------|
| `test_generate_full_structure_tech_small` | MISSING, tech, 20 headcount | 3 layers, 5-10 assumptions, flat structure |
| `test_generate_full_structure_manufacturing_large` | MISSING, mfg, 400 headcount | 5 layers, 10-15 assumptions, deep structure |
| `test_generate_gap_filling_partial` | PARTIAL, leadership exists, no reports_to | reports_to assumptions only |
| `test_no_assumptions_for_full` | FULL hierarchy | Empty list returned |
| `test_industry_mapping_default` | Unknown industry | Uses 'default' benchmarks |
| `test_company_size_very_small` | 15 headcount | 2 layers, wide span |
| `test_company_size_very_large` | 600 headcount | 6 layers, narrow span |
| `test_role_title_inference_vp` | "VP of Infrastructure" | Layer 2 |
| `test_role_title_inference_ambiguous` | "Principal Engineer" | Layer 4 (IC-equivalent) |
| `test_assumption_to_fact_conversion` | OrganizationAssumption | Valid fact dict with data_source="assumed" |
| `test_confidence_scores_range` | Various assumptions | All in 0.6-0.8 range |
| `test_assumption_basis_populated` | Generated assumption | assumption_basis not empty |

**Example Test:**

```python
def test_generate_full_structure_tech_small():
    """Test full structure generation for small tech company."""
    # Arrange
    fact_store = FactStore()
    fact_store.add_fact(Fact(
        item="IT Budget",
        category="budget",
        domain="organization",
        entity="target",
        details={'total_it_headcount': 20},
        evidence={'exact_quote': 'Total IT staff: 20'}
    ))

    hierarchy_presence = HierarchyPresence(
        status=HierarchyPresenceStatus.MISSING,
        confidence=0.7,
        has_reports_to=False,
        has_explicit_layers=False,
        has_span_data=False,
        has_org_chart=False,
        leadership_count=0,
        total_role_count=0,
        roles_with_reports_to=0,
        gaps=["All hierarchy data"],
        detection_timestamp="2026-02-11T00:00:00Z",
        fact_count=1
    )

    company_profile = {'industry': 'technology'}

    # Act
    assumptions = generate_org_assumptions(
        fact_store=fact_store,
        hierarchy_presence=hierarchy_presence,
        entity="target",
        company_profile=company_profile
    )

    # Assert
    assert len(assumptions) >= 5  # CIO + VPs + structure notes
    assert len(assumptions) <= 10  # Not excessive
    assert all(a.confidence >= 0.6 and a.confidence <= 0.8 for a in assumptions)
    assert all(a.data_source == "assumed" for a in assumptions)
    assert any("CIO" in a.item or "Chief Information Officer" in a.item for a in assumptions)

    # Check layer count is appropriate for small tech (2-3 layers)
    layer_assumption = next((a for a in assumptions if "layers" in str(a.details).lower()), None)
    if layer_assumption:
        expected_layers = layer_assumption.details.get('expected_layers')
        assert expected_layers in [2, 3], "Small tech should have 2-3 layers"
```

#### 1.3 Schema Enhancements (Spec 10)

**File:** `tests/test_inventory_schema_enhancements.py`

**Test Matrix:**

| Test Name | Expected Validation |
|-----------|---------------------|
| `test_schema_includes_new_fields` | data_source, confidence_score, etc. in optional fields |
| `test_fingerprint_includes_data_source` | Same role, different data_source → different fingerprints |
| `test_fingerprint_includes_entity` | Same role, different entity → different fingerprints |
| `test_data_source_enum_values` | OBSERVED, ASSUMED, HYBRID all valid |
| `test_data_source_display_labels` | display_label returns human-readable strings |
| `test_data_source_badge_colors` | badge_color returns correct CSS classes |
| `test_confidence_validation_ranges` | Observed 0.8-1.0, assumed 0.6-0.8, hybrid 0.7-0.9 |
| `test_backward_compatibility` | Old inventory item without new fields gets defaults |

**Example Test:**

```python
def test_fingerprint_includes_data_source():
    """Test that data_source is part of fingerprint calculation."""
    # Arrange
    store = InventoryStore()

    item_observed = {
        'role': 'VP of Infrastructure',
        'team': 'Infrastructure',
        'entity': 'target',
        'data_source': 'observed',
    }

    item_assumed = {
        'role': 'VP of Infrastructure',
        'team': 'Infrastructure',
        'entity': 'target',
        'data_source': 'assumed',
    }

    # Act
    fp_observed = store._generate_fingerprint('organization', item_observed)
    fp_assumed = store._generate_fingerprint('organization', item_assumed)

    # Assert
    assert fp_observed != fp_assumed, "Fingerprints must differ by data_source"
    assert fp_observed.startswith('I-ORG-')
    assert fp_assumed.startswith('I-ORG-')
```

#### 1.4 Bridge Integration (Spec 11)

**File:** `tests/test_org_bridge_integration.py`

**Test Matrix:**

| Test Name | Input | Expected Behavior |
|-----------|-------|-------------------|
| `test_bridge_full_hierarchy_no_assumptions` | FULL hierarchy, enabled | No assumptions, observed only |
| `test_bridge_missing_hierarchy_with_assumptions` | MISSING, enabled | Assumptions generated and merged |
| `test_bridge_partial_hierarchy_gap_filling` | PARTIAL, enabled | Gap-filling assumptions only |
| `test_bridge_assumptions_disabled_flag` | MISSING, disabled flag | No assumptions despite MISSING |
| `test_bridge_buyer_assumptions_disabled` | Buyer entity, MISSING | No buyer assumptions (per flag) |
| `test_bridge_error_graceful_fallback` | Mock exception | Falls back to observed-only, logs error |
| `test_bridge_entity_filtering` | Target + buyer facts | Only target processed |
| `test_bridge_preserve_observed_on_merge` | Observed + assumptions | Both coexist, no overwriting |

**Example Test:**

```python
def test_bridge_missing_hierarchy_with_assumptions():
    """Test bridge generates assumptions for MISSING hierarchy."""
    # Arrange
    fact_store = FactStore()
    fact_store.add_fact(Fact(
        item="Infrastructure Team",
        category="central_it",
        domain="organization",
        entity="target",
        details={'headcount': 10},
        evidence={'exact_quote': 'Infrastructure team: 10 people'}
    ))

    # Act
    store, status = build_organization_from_facts(
        fact_store=fact_store,
        target_name="Test Co",
        deal_id="deal123",
        entity="target",
        company_profile={'industry': 'technology'},
        enable_assumptions=True
    )

    # Assert
    assert status == "success_with_assumptions"
    assert len(store.staff_members) > 1  # Observed + assumed

    # Check for assumed items
    assumed_items = [s for s in store.staff_members if s.data_source == 'assumed']
    assert len(assumed_items) >= 1, "Should have at least one assumed item"

    # Check for observed items still present
    observed_items = [s for s in store.staff_members if s.data_source == 'observed']
    assert len(observed_items) >= 1, "Should preserve observed items"
```

---

### 2. Integration Tests

**File:** `tests/integration/test_adaptive_org_extraction.py`

#### 2.1 Cross-Component Flow Tests

**Test 1: Detector → Assumption Engine**

```python
def test_detection_drives_assumption_generation():
    """Test that MISSING detection triggers assumption generation."""
    # Arrange: Create minimal org facts (MISSING hierarchy)
    fact_store = FactStore()
    fact_store.add_fact(Fact(
        item="IT Team",
        category="central_it",
        domain="organization",
        entity="target",
        details={'headcount': 30}
    ))

    # Act: Run detection
    hierarchy_presence = detect_hierarchy_presence(fact_store, entity="target")

    # Assert detection is MISSING
    assert hierarchy_presence.status == HierarchyPresenceStatus.MISSING

    # Act: Generate assumptions based on detection
    assumptions = generate_org_assumptions(
        fact_store=fact_store,
        hierarchy_presence=hierarchy_presence,
        entity="target",
        company_profile={'industry': 'technology'}
    )

    # Assert assumptions generated
    assert len(assumptions) > 0
    assert all(a.entity == "target" for a in assumptions)
```

**Test 2: Assumption Engine → FactStore → Bridge**

```python
def test_assumptions_merge_and_extract():
    """Test assumptions merge into FactStore and extract to inventory."""
    # Arrange
    fact_store = FactStore()
    fact_store.add_fact(Fact(
        item="Applications Team",
        category="central_it",
        domain="organization",
        entity="target",
        details={'headcount': 20}
    ))

    # Generate assumptions
    hierarchy_presence = HierarchyPresence(
        status=HierarchyPresenceStatus.MISSING,
        confidence=0.7,
        has_reports_to=False,
        has_explicit_layers=False,
        has_span_data=False,
        has_org_chart=False,
        leadership_count=0,
        total_role_count=0,
        roles_with_reports_to=0,
        gaps=[],
        detection_timestamp="2026-02-11",
        fact_count=1
    )

    assumptions = generate_org_assumptions(
        fact_store=fact_store,
        hierarchy_presence=hierarchy_presence,
        entity="target"
    )

    # Merge assumptions
    _merge_assumptions_into_fact_store(fact_store, assumptions, deal_id="deal123")

    # Assert assumptions in FactStore
    assumed_facts = [f for f in fact_store.facts if f.details.get('data_source') == 'assumed']
    assert len(assumed_facts) == len(assumptions)

    # Act: Extract to inventory
    store, status = build_organization_from_facts(
        fact_store=fact_store,
        entity="target",
        deal_id="deal123",
        enable_assumptions=False  # Already merged manually
    )

    # Assert inventory includes assumed items
    assumed_staff = [s for s in store.staff_members if s.data_source == 'assumed']
    assert len(assumed_staff) > 0
```

**Test 3: Bridge → Inventory → UI**

```python
def test_inventory_to_ui_rendering():
    """Test inventory with mixed data sources renders correctly in UI."""
    # Arrange: Build inventory with mixed sources
    fact_store = FactStore()
    # [Add facts...]

    store, status = build_organization_from_facts(
        fact_store=fact_store,
        entity="target",
        enable_assumptions=True
    )

    # Act: Render UI template (mock template context)
    context = {
        'staff_members': store.staff_members
    }

    # Assert: Check staff members have display properties
    for staff in context['staff_members']:
        assert hasattr(staff, 'data_source')
        assert hasattr(staff, 'confidence_score')

        if staff.data_source == 'assumed':
            assert staff.assumption_basis is not None
            assert 0.6 <= staff.confidence_score <= 0.8
```

#### 2.2 Error Path Tests

**Test 1: Graceful Fallback on Assumption Engine Error**

```python
def test_assumption_engine_error_fallback():
    """Test bridge falls back to observed-only if assumption engine fails."""
    # Arrange
    fact_store = FactStore()
    fact_store.add_fact(Fact(
        item="Security Team",
        category="central_it",
        domain="organization",
        entity="target",
        details={'headcount': 5}
    ))

    # Mock assumption engine to raise exception
    with patch('services.org_assumption_engine.generate_org_assumptions',
               side_effect=Exception("Assumption engine error")):

        # Act
        store, status = build_organization_from_facts(
            fact_store=fact_store,
            entity="target",
            enable_assumptions=True
        )

        # Assert: Fallback succeeded
        assert status == "success_fallback"
        assert len(store.staff_members) >= 1  # Observed data still extracted
```

---

### 3. Golden Fixture Tests

**File:** `tests/golden/test_org_golden_fixtures.py`

**Purpose:** Regression protection using known-good documents.

#### 3.1 Existing Document (FULL Hierarchy)

**Test:** Existing VDR doc with complete org chart must produce unchanged output.

```python
def test_golden_fixture_great_insurance_org():
    """Regression test: Great Insurance org extraction unchanged."""
    # Arrange
    doc_path = "data/input/Target Company Profile - Great Insurance.pdf"
    fact_store = run_discovery_on_document(doc_path)

    # Act
    store, status = build_organization_from_facts(
        fact_store=fact_store,
        entity="target",
        enable_assumptions=True  # Feature enabled, but shouldn't trigger
    )

    # Assert: No assumptions generated (FULL hierarchy)
    assumed_items = [s for s in store.staff_members if s.data_source == 'assumed']
    assert len(assumed_items) == 0, "FULL hierarchy should not generate assumptions"

    # Assert: Observed count matches baseline
    observed_items = [s for s in store.staff_members if s.data_source == 'observed']
    assert len(observed_items) >= 100, "Should extract expected baseline count"
```

#### 3.2 New Document (MISSING Hierarchy)

**Test:** New minimal VDR doc triggers assumptions correctly.

```python
def test_golden_fixture_minimal_org():
    """Test: Minimal org doc generates assumptions."""
    # Arrange: Create minimal fixture
    minimal_doc_content = """
    IT Department Summary

    Total IT Staff: 45
    Teams:
    - Applications: 15 people
    - Infrastructure: 20 people
    - Security: 10 people
    """
    # [Save to fixture file, parse]

    fact_store = run_discovery_on_document(minimal_fixture_path)

    # Act
    store, status = build_organization_from_facts(
        fact_store=fact_store,
        entity="target",
        company_profile={'industry': 'technology'},
        enable_assumptions=True
    )

    # Assert: Assumptions generated
    assert status == "success_with_assumptions"
    assumed_items = [s for s in store.staff_members if s.data_source == 'assumed']
    assert len(assumed_items) >= 5, "Should generate CIO + VPs + structure"
```

#### 3.3 Mixed Entity Document

**Test:** Doc with both target and buyer org data maintains entity isolation.

```python
def test_golden_fixture_mixed_entity():
    """Test: Mixed target/buyer doc maintains entity isolation."""
    # Arrange: Use fixture with both entities
    mixed_doc_path = "data/input/test_fixtures/mixed_entity_org.pdf"
    fact_store = run_discovery_on_document(mixed_doc_path)

    # Act: Extract target only
    target_store, target_status = build_organization_from_facts(
        fact_store=fact_store,
        entity="target",
        enable_assumptions=True
    )

    # Act: Extract buyer only
    buyer_store, buyer_status = build_organization_from_facts(
        fact_store=fact_store,
        entity="buyer",
        enable_assumptions=False  # Buyer assumptions disabled
    )

    # Assert: No cross-contamination
    target_items = target_store.staff_members
    buyer_items = buyer_store.staff_members

    assert all(s.entity == "target" for s in target_items if hasattr(s, 'entity'))
    assert all(s.entity == "buyer" for s in buyer_items if hasattr(s, 'entity'))

    # Assert: No buyer assumptions generated
    buyer_assumed = [s for s in buyer_items if s.data_source == 'assumed']
    assert len(buyer_assumed) == 0, "Buyer assumptions should be disabled"
```

---

### 4. End-to-End Tests

**File:** `tests/e2e/test_adaptive_org_e2e.py`

#### 4.1 Full Pipeline Test

```python
def test_e2e_document_to_ui_with_assumptions():
    """End-to-end: Document ingestion → UI rendering with assumptions."""
    # Arrange
    doc_path = "data/input/test_fixtures/minimal_org.pdf"

    # Act 1: Ingest document
    doc_store = DocumentStore()
    doc = doc_store.ingest_document(doc_path, entity="target", deal_id="deal_e2e")

    # Act 2: Run discovery
    from agents_v2.discovery.organization_discovery import OrganizationDiscoveryAgent
    agent = OrganizationDiscoveryAgent()
    fact_store = FactStore()
    agent.run(documents=[doc], fact_store=fact_store)

    # Act 3: Run bridge
    org_store, status = build_organization_from_facts(
        fact_store=fact_store,
        entity="target",
        company_profile={'industry': 'financial_services'},
        enable_assumptions=True
    )

    # Act 4: Render UI (mock Flask context)
    from web.blueprints.organization import render_staffing_tree
    html = render_staffing_tree(org_store)

    # Assert: UI contains badges for assumed data
    assert 'badge-warning' in html, "UI should show assumption badges"
    assert 'Assumed' in html or 'assumed' in html.lower()
    assert status == "success_with_assumptions"
```

#### 4.2 Cost Estimation with Assumed Data

```python
def test_e2e_cost_estimation_uses_assumptions():
    """End-to-end: Cost estimates include assumed roles."""
    # Arrange: Minimal org data
    fact_store = FactStore()
    fact_store.add_fact(Fact(
        item="IT Teams",
        category="central_it",
        domain="organization",
        entity="target",
        details={'total_headcount': 30}
    ))

    # Act: Build org with assumptions
    org_store, status = build_organization_from_facts(
        fact_store=fact_store,
        entity="target",
        enable_assumptions=True
    )

    # Act: Run cost estimation
    from services.cost_engine import calculate_org_costs
    cost_summary = calculate_org_costs(org_store)

    # Assert: Costs calculated from both observed + assumed
    assert cost_summary.total_personnel_cost > 0
    assert cost_summary.assumed_cost_portion > 0  # Some cost from assumptions
    assert cost_summary.observed_cost_portion > 0  # Some cost from observed
```

---

### 5. Test Data Fixtures

**Directory:** `tests/fixtures/org_adaptive/`

**Fixture Files:**

1. **`full_hierarchy.json`**: FactStore with complete org chart (FULL status)
2. **`partial_hierarchy.json`**: FactStore with leadership but no reports_to (PARTIAL status)
3. **`missing_hierarchy.json`**: FactStore with team headcounts only (MISSING status)
4. **`mixed_entity.json`**: FactStore with target + buyer facts
5. **`tech_small.json`**: 20 headcount, tech industry
6. **`manufacturing_large.json`**: 500 headcount, manufacturing industry
7. **`borderline_80_percent.json`**: 79% reports_to (threshold edge case)

**Example Fixture:**

```json
{
  "facts": [
    {
      "item": "Chief Information Officer",
      "category": "leadership",
      "domain": "organization",
      "entity": "target",
      "details": {
        "role": "CIO",
        "reports_to": "CEO",
        "team": "IT Leadership"
      },
      "evidence": {
        "exact_quote": "John Smith, CIO, reports to CEO"
      },
      "confidence": 0.95
    },
    {
      "item": "VP of Infrastructure",
      "category": "leadership",
      "domain": "organization",
      "entity": "target",
      "details": {
        "role": "VP",
        "reports_to": "Chief Information Officer",
        "team": "Infrastructure"
      },
      "evidence": {
        "exact_quote": "Jane Doe, VP of Infrastructure, reports to CIO"
      },
      "confidence": 0.95
    }
  ]
}
```

---

### 6. Test Execution Plan

#### Phase 1: Unit Tests (Priority 1)

**Order:**
1. Schema tests (fastest, no dependencies)
2. Detector tests (independent)
3. Assumption engine tests (independent)
4. Bridge tests (depends on 2-3)

**Command:**
```bash
pytest tests/test_inventory_schema_enhancements.py -v
pytest tests/test_org_hierarchy_detector.py -v
pytest tests/test_org_assumption_engine.py -v
pytest tests/test_org_bridge_integration.py -v
```

**Success Criteria:** All 30-40 unit tests pass

#### Phase 2: Integration Tests (Priority 2)

**Order:**
1. Cross-component flow tests
2. Error path tests

**Command:**
```bash
pytest tests/integration/test_adaptive_org_extraction.py -v
```

**Success Criteria:** All 10-15 integration tests pass

#### Phase 3: Golden Fixtures (Priority 3)

**Order:**
1. Existing docs (regression first)
2. New minimal docs
3. Mixed entity docs

**Command:**
```bash
pytest tests/golden/test_org_golden_fixtures.py -v
```

**Success Criteria:** No regression on existing docs, new docs trigger assumptions correctly

#### Phase 4: End-to-End (Priority 4)

**Order:**
1. Full pipeline test
2. Cost estimation test

**Command:**
```bash
pytest tests/e2e/test_adaptive_org_e2e.py -v --slow
```

**Success Criteria:** End-to-end flow completes, UI renders correctly

---

### 7. Coverage Targets

**Coverage Tool:** `pytest-cov`

**Command:**
```bash
pytest tests/ --cov=services.org_hierarchy_detector \
               --cov=services.org_assumption_engine \
               --cov=services.organization_bridge \
               --cov=stores.inventory_schemas \
               --cov-report=html
```

**Targets:**

| Component | Target Coverage | Critical Paths |
|-----------|-----------------|----------------|
| Detector | 90%+ | Decision rules, confidence calculation |
| Assumption Engine | 85%+ | Industry benchmarks, size adjustments |
| Bridge Integration | 90%+ | Conditional logic, error handling |
| Schema | 95%+ | Fingerprinting, validation |

**Critical Paths (Must be 100% covered):**

- Entity filtering logic (no cross-contamination)
- Feature flag checks (behavior controlled correctly)
- Error fallback paths (no unhandled exceptions)
- Fingerprint calculation (no collisions)

---

## Verification Strategy

### Manual Testing Checklist

- [ ] Run on 5 real VDR docs (varying hierarchy completeness)
- [ ] Verify detection classifications match human judgment
- [ ] Check UI badges render correctly for assumed data
- [ ] Verify cost estimates include assumed roles
- [ ] Test feature flag on/off behavior
- [ ] Check logs for detection + assumption messages
- [ ] Verify VDR gaps populated from detection results
- [ ] Test buyer entity with assumptions disabled

---

## Benefits

### Why This Approach

**Four-layer pyramid** provides:
- Fast feedback (unit tests run in seconds)
- Comprehensive coverage (40+ unit, 15+ integration, 5+ golden, 3+ e2e)
- Regression protection (golden fixtures prevent breakage)

**Fixture-based testing** provides:
- Reproducible test cases
- No dependency on live API calls (fast, deterministic)
- Easy to add edge cases

**Coverage targets** provide:
- Confidence in correctness
- Identify untested code paths
- Ensure critical paths are tested

---

## Expectations

### Success Metrics

**Test Reliability:**
- Zero flaky tests (deterministic, reproducible)
- All tests pass on CI/CD pipeline
- Tests run in <2 minutes (unit + integration)

**Coverage:**
- Overall coverage ≥85%
- Critical path coverage 100%
- No untested conditional branches

**Regression Protection:**
- Existing golden fixtures pass unchanged
- No breaking changes to existing behavior

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Tests too slow** | Mock LLM calls, use fixtures, parallelize execution |
| **Fixtures become stale** | Update quarterly, version with code |
| **Coverage gaps** | Review untested paths, add targeted tests |
| **Flaky tests** | Use deterministic fixtures, avoid time-dependent logic |

---

## Results Criteria

### Acceptance Criteria

- [ ] 30-40 unit tests covering all components
- [ ] 10-15 integration tests for cross-component flows
- [ ] 3-5 golden fixture tests (regression + new paths)
- [ ] 2-3 end-to-end tests (full pipeline)
- [ ] Coverage ≥85% overall, 100% critical paths
- [ ] All tests pass on CI/CD
- [ ] Test execution time <2 minutes (unit + integration)
- [ ] Zero flaky tests
- [ ] Fixtures documented and versioned

---

**Estimated Implementation Time:** 4-5 hours
**Confidence:** High (standard testing patterns)
