# Test Plan Template

Use this template for each phase of the 115-Point Enhancement Plan.

---

## Test Plan: Phase [N] - [Phase Name]

**Date:** [YYYY-MM-DD]
**Author:** [Name]
**Baseline Tests:** [Number] tests passing

---

## Scope

**What functionality is being added/modified:**
- [ ] New enum(s): [List enums]
- [ ] New tool(s): [List tools]
- [ ] New storage: [List AnalysisStore additions]
- [ ] New methods: [List methods]
- [ ] Modified existing: [List modifications]

---

## Pre-requisites

- [ ] All existing tests pass (baseline)
- [ ] Dependencies installed (if any)
- [ ] Previous phases complete (if dependent)

---

## Test Categories

### A. Unit Tests

Create tests in `tests/test_phase_[N]_[name].py`

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| N.1 | test_[name]_enum_values | Verify enum contains expected values including Unknown | All values present |
| N.2 | test_[name]_required_fields | Verify required fields enforced | Error on missing required |
| N.3 | test_[name]_optional_fields | Verify optional fields work | No error when omitted |
| N.4 | test_[name]_storage | Verify data stored correctly | Data in correct list |
| N.5 | test_[name]_id_generation | Verify unique IDs generated | Sequential IDs |
| N.6 | test_[name]_duplicate_detection | Verify duplicates caught | Returns existing ID |
| N.7 | test_[name]_defaults_applied | Verify defaults are set | Missing fields have defaults |

### B. Integration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| N.10 | test_tool_to_store_flow | End-to-end tool execution | Data retrievable from store |
| N.11 | test_retrieval_filtering | Test getter with filters | Correct subset returned |
| N.12 | test_export_includes_data | Export contains new data | New data in output |

### C. Edge Cases

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| N.20 | test_unknown_values | Unknown enum values accepted | Stored correctly |
| N.21 | test_empty_arrays | Empty array fields work | No errors |
| N.22 | test_special_characters | Text with special chars | Handled correctly |
| N.23 | test_very_long_text | Very long field values | Stored or truncated appropriately |

### D. Regression Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| N.30 | test_existing_tools_unaffected | Existing tools still work | No change in behavior |
| N.31 | test_existing_getters_work | Existing getters work | Same output |

---

## Test Implementation Example

```python
"""
Tests for Phase [N]: [Phase Name]

Run with: pytest tests/test_phase_N_[name].py -v
"""
import pytest
from tools.analysis_tools import (
    AnalysisStore,
    NEW_ENUM,
    ANALYSIS_TOOLS
)

class TestPhaseNEnums:
    """Test new enum definitions."""

    def test_enum_contains_unknown(self):
        """Verify enum includes Unknown value."""
        assert "Unknown" in NEW_ENUM

    def test_enum_values_valid(self):
        """Verify all enum values follow naming convention."""
        for value in NEW_ENUM:
            # Title_Case_With_Underscores
            assert "_" in value or value[0].isupper()


class TestPhaseNTool:
    """Test new tool functionality."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_record_new_type_basic(self, store):
        """Test basic recording."""
        result = store.execute_tool("record_new_type", {
            "field_one": "Test Value",
            "field_two": "Enum_Value",
            "source_evidence": {
                "exact_quote": "This is the exact quote from document",
                "evidence_type": "direct_statement",
                "confidence_level": "high"
            }
        })

        assert result["status"] == "recorded"
        assert result["id"].startswith("NT-")

    def test_record_new_type_duplicate(self, store):
        """Test duplicate detection."""
        # First record
        store.execute_tool("record_new_type", {
            "field_one": "Same Value",
            "source_evidence": {
                "exact_quote": "Quote one",
                "evidence_type": "direct_statement",
                "confidence_level": "high"
            }
        })

        # Duplicate
        result = store.execute_tool("record_new_type", {
            "field_one": "Same Value",
            "source_evidence": {
                "exact_quote": "Quote two",
                "evidence_type": "direct_statement",
                "confidence_level": "high"
            }
        })

        assert result["status"] == "duplicate"

    def test_getter_with_filter(self, store):
        """Test filtered retrieval."""
        # Add test data
        store.execute_tool("record_new_type", {...})
        store.execute_tool("record_new_type", {...})

        # Filter
        results = store.get_new_types(filter_field="specific_value")

        assert len(results) > 0
        for r in results:
            assert r.get("filter_field") == "specific_value"
```

---

## Validation Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific phase tests
pytest tests/test_phase_N_[name].py -v

# Run with coverage
pytest tests/ --cov=tools --cov-report=term-missing

# Run only new tests
pytest tests/test_phase_N_[name].py -v --tb=short

# Check for regressions (run full suite)
pytest tests/ -v --tb=line
```

---

## Success Criteria

- [ ] All existing tests pass (no regressions)
- [ ] All new tests pass
- [ ] Test coverage for new code ≥ 80%
- [ ] No warnings or deprecations introduced
- [ ] Edge cases handled gracefully

---

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | | | [ ] Pass |
| Reviewer | | | [ ] Approved |
