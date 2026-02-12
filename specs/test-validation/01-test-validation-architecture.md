# Test Validation Framework - Architecture

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document defines the architecture for automated validation of IT due diligence pipeline outputs against expected ground truth. The framework ensures that source documents (e.g., CloudServe application inventory) are correctly extracted, analyzed, and reflected in generated dossiers with measurable accuracy.

**Problem Statement:** Currently, there is no systematic way to verify that the discovery and reasoning pipeline correctly processes input documents. This leads to:
- Manual verification bottlenecks
- Regression risks when modifying discovery agents
- Inability to detect data loss or extraction errors
- Confusion about which dossier validates against which source documents

**Solution:** Build a pytest-based validation framework that compares pipeline outputs against golden fixture files containing expected results.

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      TEST VALIDATION FRAMEWORK                  │
└─────────────────────────────────────────────────────────────────┘

  Input Documents                 Golden Fixtures
  ┌──────────────┐               ┌──────────────┐
  │ CloudServe   │               │ Expected     │
  │ Doc 1-6.md   │               │ Output       │
  └──────┬───────┘               │ (JSON)       │
         │                        └──────┬───────┘
         │                               │
         ▼                               ▼
  ┌─────────────────┐           ┌──────────────────┐
  │   Discovery     │           │  Fixture Loader  │
  │   Pipeline      │           │  (validates      │
  │   (existing)    │           │   schema)        │
  └────────┬────────┘           └────────┬─────────┘
           │                              │
           ▼                              │
  ┌─────────────────────────────────┐    │
  │  Actual Output                  │    │
  │  - inventory_store.json         │    │
  │  - facts_{timestamp}.json       │    │
  │  - findings_{timestamp}.json    │    │
  │  - it_dd_report_{ts}.html       │    │
  └───────────────┬─────────────────┘    │
                  │                      │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Assertion Engine    │
                  │  - CountAssertion    │
                  │  - CostAssertion     │
                  │  - RiskAssertion     │
                  │  - CompletenessCheck │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Test Runner         │
                  │  (pytest)            │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Report Generator    │
                  │  - Pass/Fail summary │
                  │  - Diff visualization│
                  │  - Regression alerts │
                  └──────────────────────┘
```

### Data Flow

1. **Test Setup Phase:**
   - Pytest discovers test files in `tests/validation/`
   - Each test file corresponds to one deal (e.g., `test_cloudserve_accuracy.py`)
   - Test loads golden fixture from `tests/golden/{deal_name}_expected.json`
   - Fixture loader validates schema against `02-golden-fixture-schema.md`

2. **Execution Phase:**
   - Test runs discovery pipeline on input documents (or loads existing outputs)
   - Pipeline generates actual outputs in `output/deals/{deal_id}/`
   - Test loads actual outputs: `inventory_store.json`, `facts.json`, etc.

3. **Assertion Phase:**
   - Assertion engine compares actual vs expected using domain-specific assertions
   - Each assertion type (Count, Cost, Risk, etc.) has tolerance/matching logic
   - Assertions fail if actual deviates beyond acceptable threshold

4. **Reporting Phase:**
   - Pytest collects all assertion results
   - Report generator creates human-readable diff (expected vs actual)
   - CI/CD receives pass/fail signal with detailed failure logs

---

## Specification

### Core Components

#### 1. Fixture Loader (`tests/validation/fixture_loader.py`)

**Purpose:** Load and validate golden fixture files.

**Interface:**
```python
from typing import Dict, Any
from pathlib import Path

class FixtureLoader:
    """Load and validate golden fixture files."""

    def __init__(self, schema_path: Path):
        """Initialize with path to JSON schema file."""
        self.schema = self._load_schema(schema_path)

    def load_fixture(self, deal_name: str) -> Dict[str, Any]:
        """
        Load golden fixture for a deal.

        Args:
            deal_name: Deal identifier (e.g., "cloudserve")

        Returns:
            Validated fixture dictionary

        Raises:
            FileNotFoundError: If fixture doesn't exist
            ValidationError: If fixture doesn't match schema
        """
        fixture_path = Path(f"tests/golden/{deal_name}_expected.json")
        fixture_data = json.loads(fixture_path.read_text())
        self._validate(fixture_data)
        return fixture_data

    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate fixture against schema (raises on failure)."""
        jsonschema.validate(instance=data, schema=self.schema)
```

**Dependencies:**
- `jsonschema` library for validation
- Golden fixture schema from `02-golden-fixture-schema.md`

---

#### 2. Assertion Engine (`tests/validation/assertions.py`)

**Purpose:** Define assertion types for different validation checks.

**Interface:**
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class Assertion(ABC):
    """Base class for all assertion types."""

    @abstractmethod
    def assert_match(self, expected: Any, actual: Any) -> AssertionResult:
        """Compare expected vs actual, return result."""
        pass

class CountAssertion(Assertion):
    """Assert that counts match (with optional tolerance)."""

    def __init__(self, tolerance: int = 0):
        """
        Args:
            tolerance: Allow actual count to differ by this amount
                       (e.g., tolerance=2 means 38±2 apps is acceptable)
        """
        self.tolerance = tolerance

    def assert_match(self, expected: int, actual: int) -> AssertionResult:
        """Check if actual count is within tolerance of expected."""
        diff = abs(actual - expected)
        passed = diff <= self.tolerance
        return AssertionResult(
            passed=passed,
            expected=expected,
            actual=actual,
            message=f"Count mismatch: expected {expected}, got {actual} (tolerance={self.tolerance})"
        )

class CostAssertion(Assertion):
    """Assert that costs match (with percentage tolerance)."""

    def __init__(self, tolerance_pct: float = 1.0):
        """
        Args:
            tolerance_pct: Allow actual to differ by this % (e.g., 1.0 = 1%)
        """
        self.tolerance_pct = tolerance_pct

    def assert_match(self, expected: float, actual: float) -> AssertionResult:
        """Check if actual cost is within tolerance % of expected."""
        if expected == 0:
            passed = actual == 0
        else:
            diff_pct = abs((actual - expected) / expected * 100)
            passed = diff_pct <= self.tolerance_pct

        return AssertionResult(
            passed=passed,
            expected=expected,
            actual=actual,
            message=f"Cost mismatch: expected ${expected:,.0f}, got ${actual:,.0f}"
        )

class RiskAssertion(Assertion):
    """Assert that specific risks are detected."""

    def assert_match(self, expected_risks: List[str], actual_risks: List[str]) -> AssertionResult:
        """
        Check if expected risks appear in actual risks.

        Args:
            expected_risks: List of risk IDs that MUST be present (e.g., ["R-WIZ-CONTRACT-EXPIRING"])
            actual_risks: List of risk IDs actually found
        """
        missing = set(expected_risks) - set(actual_risks)
        passed = len(missing) == 0
        return AssertionResult(
            passed=passed,
            expected=expected_risks,
            actual=actual_risks,
            message=f"Missing risks: {missing}" if not passed else "All expected risks found"
        )

@dataclass
class AssertionResult:
    """Result of an assertion check."""
    passed: bool
    expected: Any
    actual: Any
    message: str
```

**Design Rationale:**
- **Tolerance-based matching:** Exact matching is brittle (LLM non-determinism, rounding differences)
- **Type-specific assertions:** Different data types need different comparison logic
- **Detailed failure messages:** Make debugging failures fast

---

#### 3. Test Runner (`tests/validation/test_*.py`)

**Purpose:** Pytest test files that orchestrate validation for each deal.

**Example:** `tests/validation/test_cloudserve_accuracy.py`

```python
import pytest
from pathlib import Path
from .fixture_loader import FixtureLoader
from .assertions import CountAssertion, CostAssertion, RiskAssertion

# Load fixtures once for all tests
fixture_loader = FixtureLoader(schema_path=Path("specs/test-validation/fixture_schema.json"))
CLOUDSERVE_EXPECTED = fixture_loader.load_fixture("cloudserve")

class TestCloudServeApplications:
    """Validate CloudServe application inventory extraction."""

    @pytest.fixture
    def actual_inventory(self):
        """Load actual pipeline output for CloudServe."""
        deal_path = Path("output/deals/2026-02-11_110325_cloudserve")
        inventory_file = deal_path / "inventory_store.json"
        return json.loads(inventory_file.read_text())

    def test_application_count(self, actual_inventory):
        """Verify 38 applications were extracted from CloudServe docs."""
        expected = CLOUDSERVE_EXPECTED["applications"]["count"]
        actual_apps = [item for item in actual_inventory["items"].values()
                       if item["inventory_type"] == "application"
                       and item["entity"] == "target"]

        assertion = CountAssertion(tolerance=0)  # Exact match required
        result = assertion.assert_match(expected=expected, actual=len(actual_apps))

        assert result.passed, result.message

    def test_total_application_cost(self, actual_inventory):
        """Verify total application cost matches expected $2,331,500."""
        expected = CLOUDSERVE_EXPECTED["applications"]["total_cost"]
        actual_apps = [item for item in actual_inventory["items"].values()
                       if item["inventory_type"] == "application"
                       and item["entity"] == "target"]
        actual_cost = sum(float(app["data"].get("cost", 0)) for app in actual_apps)

        assertion = CostAssertion(tolerance_pct=1.0)  # 1% tolerance
        result = assertion.assert_match(expected=expected, actual=actual_cost)

        assert result.passed, result.message

    def test_critical_risks_detected(self):
        """Verify critical risks are flagged (Wiz expiring, Datadog cost)."""
        expected_risks = CLOUDSERVE_EXPECTED["risks"]["critical"]
        # Load actual risks from findings or facts
        actual_risks = ["R-WIZ-CONTRACT-EXPIRING", "R-DATADOG-HIGH-COST"]  # Placeholder

        assertion = RiskAssertion()
        result = assertion.assert_match(expected=expected_risks, actual=actual_risks)

        assert result.passed, result.message
```

**Test Discovery:**
- Pytest finds all `test_*.py` files in `tests/validation/`
- Each file represents one deal scenario
- Tests within file cover different domains (apps, infra, org, etc.)

---

#### 4. Report Generator (`tests/validation/report.py`)

**Purpose:** Generate human-readable validation reports.

**Interface:**
```python
class ValidationReport:
    """Generate validation report from pytest results."""

    def __init__(self, results: List[AssertionResult]):
        self.results = results

    def to_markdown(self) -> str:
        """
        Generate markdown report.

        Returns:
            Markdown string with pass/fail summary and diffs
        """
        passed = [r for r in self.results if r.passed]
        failed = [r for r in self.results if not r.passed]

        report = f"# Validation Report\n\n"
        report += f"**Total Checks:** {len(self.results)}\n"
        report += f"**Passed:** {len(passed)} ✅\n"
        report += f"**Failed:** {len(failed)} ❌\n\n"

        if failed:
            report += "## Failures\n\n"
            for result in failed:
                report += f"- {result.message}\n"
                report += f"  - Expected: `{result.expected}`\n"
                report += f"  - Actual: `{result.actual}`\n\n"

        return report

    def to_json(self) -> Dict[str, Any]:
        """Generate machine-readable JSON report for CI/CD."""
        return {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "failures": [
                {
                    "message": r.message,
                    "expected": r.expected,
                    "actual": r.actual
                }
                for r in self.results if not r.passed
            ]
        }
```

---

## Verification Strategy

### Unit Tests

**What to test:**
1. **FixtureLoader:**
   - Loads valid fixture correctly
   - Rejects fixture with invalid schema
   - Raises FileNotFoundError for missing fixture

2. **Assertion classes:**
   - CountAssertion passes when within tolerance
   - CountAssertion fails when outside tolerance
   - CostAssertion handles percentage tolerance correctly
   - RiskAssertion detects missing expected risks

3. **Report generation:**
   - Markdown report formats correctly
   - JSON report is valid and machine-parseable

**Test file:** `tests/unit/test_validation_framework.py`

---

### Integration Tests

**What to test:**
1. **End-to-end validation run:**
   - Run discovery pipeline on CloudServe docs
   - Load golden fixture
   - Run all assertions
   - Verify report generation

2. **CI/CD integration:**
   - Pytest runs in GitHub Actions
   - Failure blocks PR merge
   - Report uploaded as artifact

**Test file:** `tests/integration/test_validation_e2e.py`

---

### Manual Verification

**Steps:**
1. Run `pytest tests/validation/test_cloudserve_accuracy.py -v`
2. Verify output shows all checks passing
3. Intentionally corrupt `inventory_store.json` (delete 5 apps)
4. Re-run pytest, confirm it detects the corruption and fails
5. Check that failure message shows expected=38, actual=33

---

## Benefits

### Why This Approach

1. **Pytest integration:** Familiar tool, rich ecosystem, CI/CD support
2. **Golden fixtures:** Single source of truth for expected outputs
3. **Type-specific assertions:** Match validation logic to data type (counts, costs, risks)
4. **Tolerance-based:** Accounts for LLM non-determinism without being overly permissive
5. **Incremental rollout:** Start with CloudServe, expand to all deals gradually

### Alternatives Considered

**Alternative 1:** Manual spreadsheet validation
- **Rejected:** Not automated, slow, error-prone

**Alternative 2:** Hardcoded assertions in discovery agents
- **Rejected:** Mixes validation with production code, hard to maintain

**Alternative 3:** Custom test runner (not pytest)
- **Rejected:** Reinventing wheel, less CI/CD integration

---

## Expectations

### Success Metrics

1. **Coverage:** All 6 domains (apps, infra, network, cybersecurity, identity, org) have validation tests
2. **Accuracy:** <5% false positive rate (tests failing when output is actually correct)
3. **Detection:** 100% detection rate for regressions (if extraction breaks, tests fail)
4. **Speed:** Full validation suite runs in <2 minutes
5. **Adoption:** All new test data sets include golden fixtures

### Acceptance Criteria

- [x] FixtureLoader loads and validates CloudServe fixture
- [x] CountAssertion, CostAssertion, RiskAssertion classes implemented
- [x] `test_cloudserve_accuracy.py` has 10+ assertions covering all domains
- [x] Pytest runs successfully with all checks passing on current CloudServe output
- [x] Report generator creates markdown + JSON outputs
- [x] CI/CD integration (see `05-ci-integration.md`)

---

## Risks & Mitigations

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **LLM non-determinism breaks exact matching** | High (false failures) | Medium | Use tolerance-based assertions, not exact matching |
| **Golden fixtures drift from actual valid outputs** | High (tests always fail) | Medium | Add fixture update script, review process |
| **Pytest runs too slow (<2min target)** | Medium (CI/CD bottleneck) | Low | Parallelize tests, cache fixtures, optimize file I/O |
| **Schema validation overhead** | Low | Low | Cache schema, validate once per test session |

### Implementation Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Incomplete assertion coverage** | Medium (bugs slip through) | Medium | Systematically test all domains from audit1 findings |
| **Fixture maintenance burden** | Medium (stale fixtures) | High | Document update process in `04-test-data-documentation.md` |
| **Team adoption resistance** | Low | Medium | Make it easy: auto-generate fixtures, simple pytest commands |

---

## Results Criteria

### How to Verify This Component Works

1. **Run CloudServe validation:**
   ```bash
   pytest tests/validation/test_cloudserve_accuracy.py -v
   ```
   - All checks pass ✅
   - Report shows 38 apps, $2.3M cost, critical risks flagged

2. **Introduce regression:**
   - Modify discovery agent to skip first 5 apps
   - Re-run pytest
   - Verify test fails with message: "Count mismatch: expected 38, got 33"

3. **Check CI/CD integration:**
   - Open PR with broken discovery code
   - GitHub Actions runs validation
   - PR blocked from merging due to test failure

4. **Generate reports:**
   - Run `pytest --html=report.html`
   - Open `report.html`, verify failures are readable
   - Check JSON report is parseable

### Definition of Done

- FixtureLoader, Assertion classes, ReportGenerator all unit tested
- CloudServe validation test file has 15+ assertions across all domains
- Tests pass on current CloudServe pipeline output
- Documentation exists for adding new fixtures (see Doc 04)
- CI/CD pipeline configured (see Doc 05)

---

## Cross-References

- **02-golden-fixture-schema.md:** Defines structure of fixture files loaded by FixtureLoader
- **03-validation-assertions.md:** Catalogs all assertion types beyond the examples here
- **04-test-data-documentation.md:** Explains how to create fixtures for new deals
- **05-ci-integration.md:** GitHub Actions configuration for running these tests
- **06-migration-rollout.md:** Incremental plan to add validation to existing deals
