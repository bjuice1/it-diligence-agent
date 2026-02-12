# Deal Type Awareness Test Suite

Comprehensive test suite for deal type awareness feature covering all 3 deal types (acquisition, carveout, divestiture) across 6 domains.

**Spec Reference**: `specs/deal-type-awareness/06-testing-validation.md`

---

## Test Coverage Overview

| Test Level | File Count | Test Count | Coverage |
|------------|------------|------------|----------|
| Unit Tests | 4 | ~50 | All core functions |
| Integration Tests | 2 | ~15 | Cross-subsystem flows |
| E2E Tests | 1 | ~5 | Full pipeline |
| Regression Tests | 1 | ~10 | Golden fixtures |
| **TOTAL** | **8** | **~80** | **85%** |

---

## Test Files

### Unit Tests (`tests/unit/`)

1. **`test_deal_type_validation.py`**
   - Database NOT NULL constraint validation
   - CHECK constraint for valid values
   - Deal model defaults and edge cases
   - ~15 tests

2. **`test_synergy_engine_branching.py`**
   - Acquisition → consolidation synergies
   - Carveout → separation costs
   - Divestiture → higher separation costs
   - No consolidation for carveout/divestiture
   - ~12 tests

3. **`test_cost_multipliers.py`**
   - Acquisition baseline (1.0x)
   - Carveout higher multipliers (1.5-3.0x)
   - Divestiture highest multipliers (2.0-3.5x)
   - Cost calculation integration
   - Backward compatibility
   - ~18 tests

4. **`test_prompt_conditioning.py`**
   - Acquisition → consolidation focus
   - Carveout → separation focus + TSA
   - Divestiture → extraction focus
   - Deal type appears at top of prompts
   - ~10 tests

### Integration Tests (`tests/integration/`)

5. **`test_deal_type_cost_flow.py`**
   - Deal model → cost engine flow
   - Acquisition cost flow (no TSA)
   - Carveout cost flow (with TSA)
   - Divestiture cost flow (highest costs)
   - Cost multiplier propagation
   - ~10 tests

6. **`test_deal_type_reasoning_flow.py`**
   - Facts → reasoning → findings
   - Acquisition generates consolidation findings
   - Carveout focuses on separation
   - Inventory-based reasoning
   - Cross-domain reasoning
   - ~8 tests

### E2E Tests (`tests/e2e/`)

7. **`test_full_pipeline_by_deal_type.py`**
   - Full pipeline: Discovery → Reasoning → Cost → Narrative
   - Test all 3 deal types end-to-end
   - Pipeline comparison across types
   - Error handling
   - ~8 tests (marked as `@pytest.mark.slow`)

### Regression Tests (`tests/regression/`)

8. **`test_deal_type_regression.py`**
   - Golden fixture validation
   - Cross-fixture comparison
   - Backward compatibility
   - ~10 tests

---

## Golden Fixtures (`tests/fixtures/`)

Test fixtures for regression prevention:

- **`golden_acquisition.json`**: Expected outputs for acquisition deals
- **`golden_carveout.json`**: Expected outputs for carveout deals
- **`golden_divestiture.json`**: Expected outputs for divestiture deals

Each fixture defines:
- Test scenario (inputs)
- Expected outputs (costs, multipliers, findings)
- Validation rules
- Cost ratios vs baseline

---

## Running Tests

### Run All Deal Type Tests

```bash
cd "9.5/it-diligence-agent 2"

# All deal type awareness tests
pytest tests/unit/test_deal_type*.py tests/unit/test_synergy*.py tests/unit/test_cost_multipliers.py tests/unit/test_prompt*.py tests/integration/test_deal_type*.py tests/e2e/test_full_pipeline*.py tests/regression/test_deal_type*.py -v
```

### Run by Test Level

```bash
# Unit tests only (fast)
pytest tests/unit/test_deal_type_validation.py tests/unit/test_synergy_engine_branching.py tests/unit/test_cost_multipliers.py tests/unit/test_prompt_conditioning.py -v

# Integration tests only
pytest tests/integration/test_deal_type_cost_flow.py tests/integration/test_deal_type_reasoning_flow.py -v

# E2E tests only (slow)
pytest tests/e2e/test_full_pipeline_by_deal_type.py -v --slow

# Regression tests only
pytest tests/regression/test_deal_type_regression.py -v
```

### Run by Marker

```bash
# All integration tests
pytest -m integration -v

# All E2E tests
pytest -m e2e -v

# All regression tests
pytest -m regression -v

# Skip slow tests
pytest -m "not slow" -v
```

### Run Specific Test

```bash
# Single test file
pytest tests/unit/test_cost_multipliers.py -v

# Single test class
pytest tests/unit/test_cost_multipliers.py::TestDealTypeMultipliers -v

# Single test function
pytest tests/unit/test_cost_multipliers.py::TestDealTypeMultipliers::test_acquisition_baseline_multipliers -v
```

### With Coverage

```bash
# Coverage for deal type awareness subsystems
pytest tests/unit/test_deal_type*.py tests/unit/test_synergy*.py tests/unit/test_cost_multipliers.py tests/integration/test_deal_type*.py \
  --cov=services.cost_engine \
  --cov=web.blueprints.costs \
  --cov=prompts \
  --cov-report=html \
  --cov-report=term-missing
```

---

## Test Dependencies

### Required Implementations

All tests assume the following specs are implemented:

- ✅ **Spec 01**: Deal Type Architecture (taxonomy)
- ✅ **Spec 02**: Synergy Engine Conditional Logic
- ✅ **Spec 03**: Reasoning Prompt Conditioning
- ✅ **Spec 04**: Cost Engine Deal Awareness
- ✅ **Spec 05**: UI Validation & Enforcement

### Test Fixtures

Tests use the following fixtures (defined in `tests/conftest.py`):

- `app`: Flask application
- `db_session`: Database session with automatic rollback
- `sample_acquisition_deal`: Pre-created acquisition deal
- `sample_carveout_deal`: Pre-created carveout deal
- `sample_divestiture_deal`: Pre-created divestiture deal
- `all_deal_types`: All three deal types at once
- `temp_output_dir`: Temporary directory for outputs

---

## Test Markers

Tests are automatically marked based on location:

| Marker | Description | Usage |
|--------|-------------|-------|
| `@pytest.mark.slow` | Slow tests (E2E) | `-m "not slow"` to skip |
| `@pytest.mark.integration` | Integration tests | `-m integration` |
| `@pytest.mark.e2e` | End-to-end tests | `-m e2e` |
| `@pytest.mark.regression` | Regression tests | `-m regression` |

---

## Success Criteria

- [x] 70+ new tests created
- [x] All 3 deal types covered (acquisition, carveout, divestiture)
- [x] All 6 domains covered (via prompt conditioning tests)
- [x] Golden fixtures created for regression prevention
- [x] Tests validate correct outputs (positive cases)
- [x] Tests prevent wrong recommendations (negative cases)
- [ ] All tests pass
- [ ] 85%+ coverage for affected subsystems
- [ ] No regressions in existing tests

---

## Key Test Scenarios

### Acquisition Tests
- ✅ Consolidation synergies identified
- ✅ No TSA costs
- ✅ 1.0x cost multipliers (baseline)
- ✅ Findings mention "consolidate", "migrate", "decommission"
- ✅ Findings do NOT mention "separate", "standalone"

### Carveout Tests
- ✅ Separation costs identified
- ✅ TSA costs present (min $600K for 12 months)
- ✅ 1.5-3.0x cost multipliers
- ✅ Findings mention "separate", "standalone", "TSA"
- ✅ Findings do NOT mention "consolidate"
- ✅ No consolidation synergies

### Divestiture Tests
- ✅ Highest separation costs
- ✅ 2.0-3.5x cost multipliers (highest)
- ✅ Deep integration detected
- ✅ Findings mention "untangle", "extraction"
- ✅ Findings do NOT mention "consolidate"
- ✅ No consolidation synergies

---

## Troubleshooting

### Tests Fail with Database Errors

Ensure database constraints are implemented:

```bash
# Check migration
alembic current

# Run migration if needed
alembic upgrade head
```

### Tests Fail with Import Errors

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Slow Tests Timeout

Increase timeout or skip slow tests:

```bash
# Skip slow tests
pytest -m "not slow" -v

# Or increase timeout in pytest.ini
```

### Golden Fixture Mismatches

Regenerate golden fixtures after intentional changes:

```bash
# Run E2E tests to generate new outputs
pytest tests/e2e/test_full_pipeline_by_deal_type.py -v --slow

# Update fixtures based on validated outputs
```

---

## Next Steps

After all tests pass:

1. **Run full test suite**: Ensure no regressions in existing 572 tests
2. **Coverage analysis**: Verify 85%+ coverage for deal type subsystems
3. **CI/CD integration**: Add test markers to CI pipeline
4. **Migration prep**: Proceed to Spec 07 (Migration & Rollout)

---

## Related Documentation

- **Spec**: `specs/deal-type-awareness/06-testing-validation.md`
- **Architecture**: `specs/deal-type-awareness/01-architecture-taxonomy.md`
- **Cost Engine**: `specs/deal-type-awareness/04-cost-engine-deal-awareness.md`
- **Synergy Engine**: `specs/deal-type-awareness/02-synergy-engine-conditional-logic.md`
- **Prompts**: `specs/deal-type-awareness/03-reasoning-prompt-conditioning.md`

---

**Last Updated**: 2026-02-11
**Test Count**: 80+ tests
**Status**: ✅ Implemented, ⏳ Awaiting execution
