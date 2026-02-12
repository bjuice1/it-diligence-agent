# Quick Test Execution Guide

## TL;DR - Run All Deal Type Tests

```bash
cd "9.5/it-diligence-agent 2"

pytest tests/unit/test_deal_type_validation.py \
       tests/unit/test_synergy_engine_branching.py \
       tests/unit/test_cost_multipliers.py \
       tests/unit/test_prompt_conditioning.py \
       tests/integration/test_deal_type_cost_flow.py \
       tests/integration/test_deal_type_reasoning_flow.py \
       tests/e2e/test_full_pipeline_by_deal_type.py \
       tests/regression/test_deal_type_regression.py \
       -v
```

**Expected**: 89 tests

---

## By Test Level

### Unit Tests (Fast - ~10 seconds)

```bash
pytest tests/unit/test_deal_type_validation.py \
       tests/unit/test_synergy_engine_branching.py \
       tests/unit/test_cost_multipliers.py \
       tests/unit/test_prompt_conditioning.py \
       -v
```

**Expected**: 54 tests

### Integration Tests (Medium - ~30 seconds)

```bash
pytest tests/integration/test_deal_type_cost_flow.py \
       tests/integration/test_deal_type_reasoning_flow.py \
       -v
```

**Expected**: 22 tests

### E2E Tests (Slow - ~2 minutes)

```bash
pytest tests/e2e/test_full_pipeline_by_deal_type.py -v --slow
```

**Expected**: 8 tests

### Regression Tests (Fast - ~5 seconds)

```bash
pytest tests/regression/test_deal_type_regression.py -v
```

**Expected**: 5 tests

---

## With Coverage

```bash
pytest tests/unit/test_deal_type_validation.py \
       tests/unit/test_synergy_engine_branching.py \
       tests/unit/test_cost_multipliers.py \
       tests/unit/test_prompt_conditioning.py \
       tests/integration/test_deal_type_cost_flow.py \
       tests/integration/test_deal_type_reasoning_flow.py \
       --cov=services.cost_engine \
       --cov=web.blueprints.costs \
       --cov=prompts \
       --cov=web.database \
       --cov-report=html \
       --cov-report=term-missing
```

View coverage: `open htmlcov/index.html`

---

## Full Test Suite (All 572+ tests)

```bash
pytest tests/ -v
```

**Expected**: 661+ tests (572 existing + 89 new)

---

## Troubleshooting

### If tests fail due to database

```bash
# Check database migration status
alembic current

# Run migrations
alembic upgrade head
```

### If tests fail due to imports

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### If E2E tests timeout

```bash
# Skip slow tests
pytest -m "not slow" -v
```

---

## Validation

Check that all tests can be collected:

```bash
./tests/validate_deal_type_tests.sh
```

Or manually:

```bash
pytest tests/unit/test_deal_type*.py \
       tests/unit/test_synergy*.py \
       tests/unit/test_cost_multipliers.py \
       tests/unit/test_prompt*.py \
       tests/integration/test_deal_type*.py \
       tests/e2e/test_full_pipeline*.py \
       tests/regression/test_deal_type*.py \
       --collect-only -q
```

Should show: **89 tests collected**

---

## More Info

- Full documentation: `tests/README_DEAL_TYPE_TESTS.md`
- Implementation details: `tests/IMPLEMENTATION_SUMMARY.md`
- Completion status: `DEAL_TYPE_TESTS_COMPLETE.md`
