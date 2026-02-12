#!/bin/bash
#
# Validation script for deal type awareness test suite
# Checks that all tests can be collected without errors
#
# Usage: ./tests/validate_deal_type_tests.sh
#

set -e  # Exit on error

cd "$(dirname "$0")/.."

echo "============================================"
echo "Deal Type Awareness Test Suite Validation"
echo "============================================"
echo ""

echo "Validating test collection (dry run)..."
echo ""

# Unit tests
echo "1. Unit Tests"
echo "   - test_deal_type_validation.py"
pytest tests/unit/test_deal_type_validation.py --collect-only -q
echo "   - test_synergy_engine_branching.py"
pytest tests/unit/test_synergy_engine_branching.py --collect-only -q
echo "   - test_cost_multipliers.py"
pytest tests/unit/test_cost_multipliers.py --collect-only -q
echo "   - test_prompt_conditioning.py"
pytest tests/unit/test_prompt_conditioning.py --collect-only -q
echo ""

# Integration tests
echo "2. Integration Tests"
echo "   - test_deal_type_cost_flow.py"
pytest tests/integration/test_deal_type_cost_flow.py --collect-only -q
echo "   - test_deal_type_reasoning_flow.py"
pytest tests/integration/test_deal_type_reasoning_flow.py --collect-only -q
echo ""

# E2E tests
echo "3. E2E Tests"
echo "   - test_full_pipeline_by_deal_type.py"
pytest tests/e2e/test_full_pipeline_by_deal_type.py --collect-only -q
echo ""

# Regression tests
echo "4. Regression Tests"
echo "   - test_deal_type_regression.py"
pytest tests/regression/test_deal_type_regression.py --collect-only -q
echo ""

echo "============================================"
echo "✅ All tests collected successfully!"
echo "============================================"
echo ""
echo "Summary:"
pytest tests/unit/test_deal_type_validation.py \
      tests/unit/test_synergy_engine_branching.py \
      tests/unit/test_cost_multipliers.py \
      tests/unit/test_prompt_conditioning.py \
      tests/integration/test_deal_type_cost_flow.py \
      tests/integration/test_deal_type_reasoning_flow.py \
      tests/e2e/test_full_pipeline_by_deal_type.py \
      tests/regression/test_deal_type_regression.py \
      --collect-only -q | tail -1
echo ""
echo "Next steps:"
echo "1. Run unit tests: pytest tests/unit/test_deal_type*.py tests/unit/test_synergy*.py tests/unit/test_cost_multipliers.py -v"
echo "2. Run integration tests: pytest tests/integration/test_deal_type*.py -v"
echo "3. Run E2E tests: pytest tests/e2e/test_full_pipeline*.py -v --slow"
echo "4. Run regression tests: pytest tests/regression/test_deal_type*.py -v"
echo ""
