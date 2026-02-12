# Testing & Validation

**Status:** Specification
**Created:** 2026-02-11
**Depends On:** All previous documents (01-05)
**Enables:** 07-rollout-migration.md
**Estimated Scope:** 4-5 hours

---

## Overview

**Purpose:** Define comprehensive testing strategy across all application enhancement components to ensure 95%+ test coverage and validation against real-world documents.

**Scope:**
- Unit tests for all new functions
- Integration tests for end-to-end flows
- Golden fixtures for regression prevention
- Performance testing for large portfolios
- UI testing for enrichment status features

---

## Test Architecture

### Test Layers

```
┌────────────────────────────────────────────────────────┐
│  Layer 5: Manual/UAT Testing                           │
│  - Real document uploads                               │
│  - UI interaction testing                              │
│  - Stakeholder validation                              │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│  Layer 4: End-to-End Integration Tests                │
│  - Document → Inventory → Cost → UI                   │
│  - Golden fixtures (known-good outputs)                │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│  Layer 3: Cross-Component Integration Tests            │
│  - Parser → Bridge → Inventory                         │
│  - Inventory → Cost Engine                             │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│  Layer 2: Component Unit Tests                         │
│  - Entity extraction heuristics                        │
│  - Table parser robustness                             │
│  - Cost model calculations                             │
│  - Quality score calculations                          │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│  Layer 1: Function-Level Unit Tests                    │
│  - normalize_unicode()                                 │
│  - match_header()                                      │
│  - classify_complexity()                               │
└────────────────────────────────────────────────────────┘
```

---

## Specification

### 1. Unit Tests by Component

#### 1.1 Entity Propagation (Doc 01)

**Test file:** `tests/unit/test_entity_extraction.py`

```python
# Minimum 15 tests covering:

def test_extract_from_section_header_target():
    """'Target Company' in header → entity='target'"""

def test_extract_from_section_header_buyer():
    """'Acquirer' in header → entity='buyer'"""

def test_extract_from_filename():
    """'buyer_apps.pdf' → entity='buyer' (low confidence)"""

def test_ambiguous_returns_none():
    """No clear signals → None (requires user input)"""

def test_conflicting_signals_raises_error():
    """'Target' in header + 'buyer' in filename → EntityAmbiguityError"""

def test_per_row_entity_column():
    """Entity column in table → 'per_row' mode"""

def test_mixed_table_split():
    """Table with Entity column splits into target + buyer tables"""

def test_bridge_raises_on_missing_entity():
    """Bridge enforces entity presence (no silent defaults)"""

def test_bridge_raises_on_invalid_entity():
    """Invalid entity value → EntityValidationError"""

def test_entity_normalization():
    """'Seller' → 'target', 'Parent' → 'buyer'"""

# ... 5 more edge case tests
```

#### 1.2 Table Parser Robustness (Doc 02)

**Test file:** `tests/unit/test_table_parser_robustness.py`

```python
# Minimum 20 tests covering:

def test_unicode_normalization_em_dash():
    """Em-dash (U+2014) → hyphen (U+002D)"""

def test_unicode_normalization_smart_quotes():
    """Smart quotes → straight quotes"""

def test_unicode_normalization_nbsp():
    """Non-breaking space → regular space"""

def test_merged_cell_expansion():
    """['App', '', 'Vendor'] → ['App', 'App', 'Vendor']"""

def test_multirow_header_detection():
    """Detect 2-3 row headers and combine"""

def test_flexible_header_matching_exact():
    """'Application' → 'application' (1.0 confidence)"""

def test_flexible_header_matching_synonym():
    """'App' → 'application' (0.95 confidence)"""

def test_flexible_header_matching_partial():
    """'Application Name' → 'application' (0.7 confidence)"""

def test_multiline_cell_joining():
    """Empty first column → append to previous row"""

def test_extraction_quality_high():
    """Good headers + complete rows → quality >0.8"""

def test_extraction_quality_low():
    """Poor headers + sparse rows → quality <0.5"""

# ... 9 more tests for edge cases
```

#### 1.3 Application Cost Model (Doc 03)

**Test file:** `tests/unit/test_application_cost_model.py`

```python
# Minimum 25 tests covering:

def test_simple_saas_low_cost():
    """Simple SaaS collaboration → <$10K"""

def test_critical_erp_high_cost():
    """Critical on-prem ERP → >$300K"""

def test_complexity_multiplier_variance():
    """Critical (3.0x) vs simple (0.5x) = 6x difference"""

def test_category_multiplier_variance():
    """ERP (2.5x) vs collaboration (0.8x) = 3.125x difference"""

def test_deployment_multiplier_variance():
    """On-prem (1.5x) vs SaaS (0.3x) = 5x difference"""

def test_integration_costs_api():
    """5 APIs × $2K = $10K"""

def test_integration_costs_sso():
    """SSO required = $5K"""

def test_integration_costs_data_migration():
    """500GB → $50K (500/100 × $10K)"""

def test_tsa_cost_for_carveout_parent_hosted():
    """Carveout + hosted_by_parent → TSA cost >0"""

def test_tsa_cost_zero_for_acquisition():
    """Acquisition → TSA cost = 0 (even if hosted_by_parent)"""

def test_cost_breakdown_transparency():
    """All multipliers present in cost_breakdown dict"""

def test_classify_complexity_from_category():
    """ERP category → 'critical' complexity"""

def test_classify_complexity_from_users():
    """>1000 users → 'complex' or 'critical'"""

def test_detect_deployment_saas_vendor():
    """Vendor='Salesforce' → 'saas'"""

def test_detect_deployment_custom_category():
    """Category='custom' → 'custom' deployment"""

# ... 10 more tests
```

#### 1.4 Cost Engine Integration (Doc 04)

**Test file:** `tests/unit/test_cost_engine_inventory_integration.py`

```python
# Minimum 15 tests covering:

def test_calculate_app_costs_from_inventory():
    """InventoryStore with 5 apps → ApplicationCostSummary"""

def test_aggregate_totals():
    """total_one_time = sum of all app one_time_total"""

def test_get_top_cost_apps():
    """get_top_cost_apps(3) returns 3 most expensive"""

def test_get_apps_by_complexity():
    """Groups apps by simple/medium/complex/critical"""

def test_dual_mode_with_inventory():
    """calculate_deal_costs with inventory_store uses inventory path"""

def test_dual_mode_without_inventory():
    """calculate_deal_costs without inventory_store uses DealDrivers path"""

def test_feature_flag_disabled():
    """Feature flag off → uses legacy count-based costing"""

def test_backward_compatibility():
    """Existing callers without inventory_store still work"""

# ... 7 more tests
```

#### 1.5 UI Enrichment Status (Doc 05)

**Test file:** `tests/unit/test_ui_enrichment_status.py`

```python
# Minimum 10 tests covering:

def test_calculate_quality_score_high():
    """High extraction + enriched + complete → >0.8"""

def test_calculate_quality_score_low():
    """Low extraction + not enriched + sparse → <0.5"""

def test_enrichment_metadata_deterministic():
    """Deterministic enrichment → high confidence"""

def test_enrichment_metadata_llm_confident():
    """LLM confident → high confidence, no investigation"""

def test_enrichment_metadata_llm_probable():
    """LLM probable → medium confidence, needs investigation"""

def test_enrichment_metadata_failed():
    """Enrichment failed → needs investigation"""

# ... 4 more tests
```

### 2. Integration Tests

#### 2.1 Entity Propagation End-to-End

**Test file:** `tests/integration/test_entity_end_to_end.py`

```python
def test_target_document_full_pipeline():
    """Document with 'Target Company' → all inventory items entity='target'"""
    doc_path = "fixtures/entity_extraction/target_header.pdf"

    # Parse
    parsed = parse_document(doc_path)
    assert parsed.entity == 'target'

    # Process
    inv_store = InventoryStore(deal_id="test")
    process_applications(parsed, drivers, inv_store)

    # Verify all items have entity='target'
    items = inv_store.get_items(inventory_type='application')
    assert all(item.entity == 'target' for item in items)
    assert len(inv_store.get_items(entity='buyer')) == 0

def test_buyer_document_full_pipeline():
    """Document with 'Acquirer' → all inventory items entity='buyer'"""
    # Similar to above

def test_mixed_table_full_pipeline():
    """Document with Entity column → split into target + buyer inventories"""
    # Similar to above
```

#### 2.2 Parser Robustness with Real PDFs

**Test file:** `tests/integration/test_parser_real_documents.py`

```python
def test_parse_merged_header_pdf():
    """Real PDF with merged headers extracts correctly"""
    doc_path = "fixtures/parser_robustness/merged_headers.pdf"
    parsed = parse_document(doc_path)

    assert parsed.extraction_quality > 0.7
    assert 'application' in [h.lower() for h in parsed.headers]
    assert len(parsed.rows) > 0

def test_parse_multiline_cells_pdf():
    """PDF with multi-line cells joins correctly"""
    # Similar pattern

def test_parse_unicode_heavy_pdf():
    """PDF with em-dashes, smart quotes parses correctly"""
    # Similar pattern
```

#### 2.3 Cost Calculation End-to-End

**Test file:** `tests/integration/test_application_cost_end_to_end.py`

```python
def test_full_pipeline_inventory_to_costs():
    """Document → Inventory → Cost calculation with variance"""
    # Parse document with mix of simple and complex apps
    doc_path = "fixtures/cost_model/mixed_portfolio.pdf"
    parsed = parse_document(doc_path)

    # Process into inventory
    inv_store = InventoryStore(deal_id="test")
    process_applications(parsed, drivers, inv_store)

    # Enrich
    enrich_inventory(inv_store)

    # Calculate costs
    cost_summary = calculate_application_costs_from_inventory(
        inv_store, deal_type='carveout'
    )

    # Verify variance
    top_apps = cost_summary.get_top_cost_apps(3)
    bottom_apps = sorted(cost_summary.app_costs, key=lambda a: a.grand_total)[:3]

    # Top apps should cost >10x bottom apps
    assert top_apps[0].grand_total > bottom_apps[0].grand_total * 10
```

### 3. Golden Fixtures

**Purpose:** Regression prevention — known-good inputs/outputs for validation.

**Fixture structure:**

```
tests/fixtures/golden/
├── applications_enhancement/
│   ├── target_10_apps.json           # Input: inventory with 10 apps
│   ├── target_10_apps_costs.json     # Expected: cost summary
│   ├── carveout_mixed.json           # Input: carveout with TSA apps
│   ├── carveout_mixed_costs.json     # Expected: costs with TSA
│   └── acquisition_simple.json       # Input: simple acquisition
│       └── acquisition_simple_costs.json  # Expected: costs
```

**Golden test:**

```python
# tests/integration/test_golden_fixtures.py

def test_golden_target_10_apps_acquisition():
    """Validate cost calculation against golden fixture."""
    # Load input
    with open('fixtures/golden/applications_enhancement/target_10_apps.json') as f:
        inventory_data = json.load(f)

    # Reconstruct inventory
    inv_store = InventoryStore(deal_id="golden-test")
    for item_data in inventory_data['items']:
        inv_store.add_item(**item_data)

    # Calculate costs
    cost_summary = calculate_application_costs_from_inventory(
        inv_store, deal_type='acquisition'
    )

    # Load expected
    with open('fixtures/golden/applications_enhancement/target_10_apps_costs.json') as f:
        expected = json.load(f)

    # Validate (allow 5% variance for floating point)
    assert cost_summary.total_one_time == pytest.approx(expected['total_one_time'], rel=0.05)
    assert cost_summary.app_count == expected['app_count']
    assert cost_summary.total_tsa == expected['total_tsa']
```

### 4. Performance Testing

**Test large portfolios:**

```python
# tests/performance/test_application_cost_performance.py

def test_100_app_portfolio_performance():
    """100 apps should calculate costs in <5 seconds."""
    import time

    inv_store = InventoryStore(deal_id="perf-test")

    # Add 100 synthetic apps
    for i in range(100):
        inv_store.add_item(
            inventory_type='application',
            entity='target',
            data={
                'name': f'App-{i:03d}',
                'category': random.choice(['erp', 'crm', 'collaboration', 'custom']),
                'complexity': random.choice(['simple', 'medium', 'complex', 'critical']),
                'users': random.randint(10, 5000)
            }
        )

    # Time cost calculation
    start = time.time()
    cost_summary = calculate_application_costs_from_inventory(inv_store, 'acquisition')
    duration = time.time() - start

    assert duration < 5.0, f"Cost calculation took {duration:.2f}s (>5s threshold)"
    assert cost_summary.app_count == 100
```

### 5. UI Testing (Manual + Automated)

**Automated UI tests (Selenium/Playwright):**

```python
# tests/ui/test_enrichment_status_ui.py

def test_quality_badges_displayed(browser):
    """Quality scores and enrichment badges visible in UI."""
    browser.visit('/deals/test-deal/inventory?type=application')

    # Find quality indicators
    quality_elements = browser.find_all('.quality-indicator')
    assert len(quality_elements) > 0

    # Check badges
    badges = browser.find_all('.badge')
    assert any('Enriched' in badge.text for badge in badges)

def test_needs_review_highlighting(browser):
    """Low-quality apps highlighted in yellow."""
    browser.visit('/deals/test-deal/inventory?type=application')

    # Find rows with needs_investigation
    warning_rows = browser.find_all('tr.table-warning')
    assert len(warning_rows) > 0

    # Check for warning badge
    for row in warning_rows:
        assert '⚠' in row.text or 'Needs Review' in row.text

def test_manual_enrichment_modal(browser):
    """Manual enrichment modal opens and saves."""
    browser.visit('/deals/test-deal/inventory?type=application')

    # Click "Review" button
    review_btn = browser.find('.btn-warning')
    review_btn.click()

    # Wait for modal
    modal = browser.find('#enrichmentModal', wait=2)
    assert modal.visible

    # Fill form
    browser.select('#enrichment-category', 'erp')
    browser.fill('#enrichment-vendor', 'SAP AG')

    # Save
    browser.find('.btn-primary').click()

    # Verify success
    assert browser.is_text_present('Enrichment saved')
```

**Manual UI testing checklist:**

```markdown
# UI Testing Checklist

## Inventory Display
- [ ] Quality scores displayed (0-100%)
- [ ] Quality indicators color-coded (green/yellow/red)
- [ ] Enrichment badges show method (deterministic/llm/manual)
- [ ] Needs review rows highlighted in yellow
- [ ] All columns render correctly

## Source Tracing
- [ ] "View Source" link opens fact detail
- [ ] Fact detail shows source document link
- [ ] Document link opens PDF at correct page

## Manual Enrichment
- [ ] "Review" button opens modal
- [ ] Form pre-fills existing values
- [ ] Category dropdown has all categories
- [ ] Save updates inventory
- [ ] Badge updates to "✓ manual" after save

## Cost Breakdown
- [ ] "Costs" button opens modal
- [ ] All multipliers displayed
- [ ] Integration costs itemized
- [ ] TSA costs shown for carveouts
- [ ] Grand total matches summary
```

---

## Test Coverage Goals

### Minimum Coverage by Component

| Component | Unit Test Coverage | Integration Test Coverage |
|-----------|-------------------|--------------------------|
| Entity extraction | 95%+ | 90%+ (3+ real docs) |
| Table parser | 90%+ | 85%+ (5+ real PDFs) |
| Cost model | 95%+ | 90%+ (golden fixtures) |
| Cost engine integration | 90%+ | 85%+ (end-to-end) |
| UI enrichment | 85%+ | Manual testing |

### Overall Coverage Target

- **Unit tests:** 95%+ line coverage on new code
- **Integration tests:** All major flows covered
- **Golden fixtures:** 3+ known-good scenarios
- **Performance tests:** Large portfolio validated
- **UI tests:** Manual checklist completed by 2+ testers

---

## Verification Strategy

### Pre-Merge Checklist

Before merging to main branch:

- [ ] All 89+ unit tests passing
- [ ] All 10+ integration tests passing
- [ ] All 3+ golden fixtures passing
- [ ] Performance test <5s for 100 apps
- [ ] UI manual checklist 100% complete
- [ ] Code coverage >95% on new files
- [ ] No regressions in existing 572 tests

### Continuous Integration

```yaml
# .github/workflows/applications-enhancement-tests.yml

name: Applications Enhancement Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run unit tests
        run: pytest tests/unit/test_entity_extraction.py -v --cov

      - name: Run integration tests
        run: pytest tests/integration/test_*_end_to_end.py -v

      - name: Run golden fixtures
        run: pytest tests/integration/test_golden_fixtures.py -v

      - name: Check coverage
        run: pytest --cov=services --cov=tools_v2 --cov-report=html --cov-fail-under=95
```

---

## Results Criteria

### Acceptance Criteria

1. **Unit tests:**
   - [ ] 89+ tests written and passing
   - [ ] 95%+ line coverage on new code

2. **Integration tests:**
   - [ ] 10+ end-to-end tests passing
   - [ ] Real PDF fixtures validate parser robustness

3. **Golden fixtures:**
   - [ ] 3+ scenarios with known-good outputs
   - [ ] Fixtures validate cost calculations

4. **Performance:**
   - [ ] 100-app portfolio completes in <5s
   - [ ] No memory leaks or resource exhaustion

5. **UI testing:**
   - [ ] Manual checklist 100% complete
   - [ ] Tested by 2+ independent users
   - [ ] All enrichment features functional

---

## Related Documents

- **01-entity-propagation-hardening.md** - Entity extraction (tested)
- **02-table-parser-robustness.md** - Parser robustness (tested)
- **03-application-cost-model.md** - Cost model (tested)
- **04-cost-engine-inventory-integration.md** - Integration (tested)
- **05-ui-enrichment-status.md** - UI features (tested)
- **07-rollout-migration.md** - Rollout depends on tests passing

---

**Document Status:** ✅ Complete
**Last Updated:** 2026-02-11
**Next Document:** 07-rollout-migration.md (final)
