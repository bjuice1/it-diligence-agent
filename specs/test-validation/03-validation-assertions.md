# Validation Assertions - Complete Catalog

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document catalogs all assertion types used to validate IT due diligence pipeline outputs against golden fixtures. Each assertion type defines comparison logic, tolerance thresholds, and failure messaging for a specific kind of validation check.

**Purpose:** Provide systematic coverage of all validation scenarios across 6 IT DD domains (applications, infrastructure, network, cybersecurity, identity, organization).

**Scope:** Defines 12 assertion types covering counts, costs, risks, completeness, specific item presence, and cross-domain consistency.

---

## Architecture

### Assertion Type Hierarchy

```
Assertion (abstract base class)
├── CountAssertion (exact or tolerance-based count matching)
├── CostAssertion (percentage-based cost matching)
├── RiskAssertion (ensures specific risks are detected)
├── CompletenessAssertion (validates data quality scores)
├── ItemPresenceAssertion (checks if specific items exist)
├── CategoryBreakdownAssertion (validates distribution across categories)
├── CriticalityDistributionAssertion (validates criticality levels)
├── StringMatchAssertion (exact or fuzzy string matching)
├── BooleanAssertion (true/false field checks)
├── ListContainsAssertion (checks list membership)
├── RangeAssertion (numeric value within range)
└── CrossDomainAssertion (consistency across domains)
```

---

## Specification

### 1. CountAssertion

**Purpose:** Validate that item counts match expected values.

**Use Cases:**
- Total application count (38 apps)
- Infrastructure items by type (85 containers, 12 serverless)
- Headcount by function (2 Apps team, 1 Infra)

**Implementation:**

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class CountAssertion(Assertion):
    """Assert that counts match (with optional tolerance)."""

    tolerance: int = 0  # Allow actual to differ by this amount

    def assert_match(self, expected: int, actual: int) -> AssertionResult:
        """
        Check if actual count is within tolerance of expected.

        Args:
            expected: Expected count from fixture
            actual: Actual count from pipeline output

        Returns:
            AssertionResult with pass/fail status
        """
        diff = abs(actual - expected)
        passed = diff <= self.tolerance

        return AssertionResult(
            passed=passed,
            expected=expected,
            actual=actual,
            diff=diff,
            message=self._generate_message(expected, actual, diff, passed)
        )

    def _generate_message(self, expected: int, actual: int, diff: int, passed: bool) -> str:
        if passed:
            return f"✓ Count matches: {actual} (expected {expected}, tolerance ±{self.tolerance})"
        else:
            return f"✗ Count mismatch: expected {expected}, got {actual} (diff: {diff}, tolerance: ±{self.tolerance})"
```

**Example Usage:**

```python
# Exact match required
assertion = CountAssertion(tolerance=0)
result = assertion.assert_match(expected=38, actual=38)
assert result.passed  # True

# Tolerance allowed
assertion = CountAssertion(tolerance=2)
result = assertion.assert_match(expected=38, actual=36)
assert result.passed  # True (within tolerance)

result = assertion.assert_match(expected=38, actual=33)
assert not result.passed  # False (outside tolerance)
```

---

### 2. CostAssertion

**Purpose:** Validate that costs match with percentage-based tolerance.

**Use Cases:**
- Total application cost ($2,331,500)
- Category-level costs (CRM: $428,000)
- Infrastructure hosting costs

**Implementation:**

```python
@dataclass
class CostAssertion(Assertion):
    """Assert that costs match (with percentage tolerance)."""

    tolerance_pct: float = 1.0  # Allow 1% deviation by default

    def assert_match(self, expected: float, actual: float) -> AssertionResult:
        """
        Check if actual cost is within tolerance % of expected.

        Handles edge cases:
        - expected=0: requires actual=0 (no tolerance)
        - Rounding differences in LLM extraction
        """
        if expected == 0:
            passed = actual == 0
            diff_pct = 0
        else:
            diff = abs(actual - expected)
            diff_pct = (diff / expected) * 100
            passed = diff_pct <= self.tolerance_pct

        return AssertionResult(
            passed=passed,
            expected=expected,
            actual=actual,
            diff=diff_pct,
            message=self._generate_message(expected, actual, diff_pct, passed)
        )

    def _generate_message(self, expected: float, actual: float, diff_pct: float, passed: bool) -> str:
        if passed:
            return f"✓ Cost matches: ${actual:,.0f} (expected ${expected:,.0f}, within {self.tolerance_pct}%)"
        else:
            return f"✗ Cost mismatch: expected ${expected:,.0f}, got ${actual:,.0f} ({diff_pct:.1f}% diff, tolerance {self.tolerance_pct}%)"
```

**Example Usage:**

```python
# Application cost with 1% tolerance
assertion = CostAssertion(tolerance_pct=1.0)
result = assertion.assert_match(expected=2331500, actual=2354000)
assert result.passed  # True (0.96% diff)

# Strict tolerance for critical costs
assertion = CostAssertion(tolerance_pct=0.1)
result = assertion.assert_match(expected=1000000, actual=1002000)
assert not result.passed  # False (0.2% diff > 0.1% tolerance)
```

---

### 3. RiskAssertion

**Purpose:** Ensure specific critical risks are detected by the reasoning pipeline.

**Use Cases:**
- Contract expiring soon (Wiz, Datadog)
- High cost applications (Salesforce, Snowflake)
- Security gaps (no SIEM, missing MFA)

**Implementation:**

```python
from typing import List, Set

@dataclass
class RiskAssertion(Assertion):
    """Assert that expected risks are detected."""

    allow_extra: bool = True  # Allow actual to have MORE risks than expected

    def assert_match(self, expected_risks: List[str], actual_risks: List[str]) -> AssertionResult:
        """
        Check if all expected risks appear in actual risks.

        Args:
            expected_risks: Risk IDs that MUST be present (e.g., ["R-WIZ-CONTRACT-EXPIRING"])
            actual_risks: Risk IDs actually detected

        Returns:
            AssertionResult showing missing risks (if any)
        """
        expected_set = set(expected_risks)
        actual_set = set(actual_risks)

        missing = expected_set - actual_set
        extra = actual_set - expected_set if not self.allow_extra else set()

        passed = len(missing) == 0 and (self.allow_extra or len(extra) == 0)

        return AssertionResult(
            passed=passed,
            expected=expected_risks,
            actual=actual_risks,
            diff={"missing": list(missing), "extra": list(extra)},
            message=self._generate_message(missing, extra, passed)
        )

    def _generate_message(self, missing: Set[str], extra: Set[str], passed: bool) -> str:
        if passed:
            return f"✓ All expected risks detected ({len(self.expected_risks)} risks)"
        else:
            msg = "✗ Risk detection failures:"
            if missing:
                msg += f" Missing: {missing}."
            if extra and not self.allow_extra:
                msg += f" Unexpected: {extra}."
            return msg
```

**Example Usage:**

```python
assertion = RiskAssertion(allow_extra=True)
result = assertion.assert_match(
    expected_risks=["R-WIZ-CONTRACT-EXPIRING", "R-DATADOG-HIGH-COST"],
    actual_risks=["R-WIZ-CONTRACT-EXPIRING", "R-DATADOG-HIGH-COST", "R-SALESFORCE-OVERLAP"]
)
assert result.passed  # True (extra risks OK)

assertion = RiskAssertion(allow_extra=False)
result = assertion.assert_match(
    expected_risks=["R-WIZ-CONTRACT-EXPIRING"],
    actual_risks=[]
)
assert not result.passed  # False (missing expected risk)
```

---

### 4. CompletenessAssertion

**Purpose:** Validate data quality and completeness scores.

**Use Cases:**
- Overall completeness score (87%)
- Domain-specific completeness (Applications: 95%, Organization: 78%)

**Implementation:**

```python
@dataclass
class CompletenessAssertion(Assertion):
    """Assert that completeness scores are within range."""

    tolerance: float = 5.0  # Allow 5 percentage points deviation

    def assert_match(self, expected_score: float, actual_score: float) -> AssertionResult:
        """
        Check if actual completeness is within tolerance of expected.

        Args:
            expected_score: Expected completeness % (0-100)
            actual_score: Actual completeness % (0-100)
        """
        diff = abs(actual_score - expected_score)
        passed = diff <= self.tolerance

        return AssertionResult(
            passed=passed,
            expected=expected_score,
            actual=actual_score,
            diff=diff,
            message=self._generate_message(expected_score, actual_score, diff, passed)
        )

    def _generate_message(self, expected: float, actual: float, diff: float, passed: bool) -> str:
        if passed:
            return f"✓ Completeness OK: {actual:.1f}% (expected {expected:.1f}%, ±{self.tolerance}%)"
        else:
            return f"✗ Completeness mismatch: expected {expected:.1f}%, got {actual:.1f}% ({diff:.1f}% diff)"
```

---

### 5. ItemPresenceAssertion

**Purpose:** Verify that specific named items exist in inventory.

**Use Cases:**
- Critical applications must be extracted (Salesforce, NetSuite, Okta)
- Key infrastructure components present
- Specific vendors listed

**Implementation:**

```python
from typing import List, Dict, Any

@dataclass
class ItemPresenceAssertion(Assertion):
    """Assert that specific items are present in inventory."""

    match_fields: List[str] = field(default_factory=lambda: ["name", "vendor"])

    def assert_match(self, expected_items: List[Dict], actual_inventory: List[Dict]) -> AssertionResult:
        """
        Check if all expected items appear in actual inventory.

        Args:
            expected_items: List of dicts with {name, vendor, ...}
            actual_inventory: Full inventory item list

        Returns:
            AssertionResult showing which items are missing
        """
        missing_items = []

        for expected_item in expected_items:
            found = False
            for actual_item in actual_inventory:
                if self._items_match(expected_item, actual_item):
                    found = True
                    break
            if not found:
                missing_items.append(expected_item)

        passed = len(missing_items) == 0

        return AssertionResult(
            passed=passed,
            expected=expected_items,
            actual=actual_inventory,
            diff={"missing": missing_items},
            message=self._generate_message(missing_items, passed)
        )

    def _items_match(self, expected: Dict, actual: Dict) -> bool:
        """Check if items match on specified fields."""
        for field in self.match_fields:
            if expected.get(field, "").lower() != actual.get(field, "").lower():
                return False
        return True
```

---

### 6. CategoryBreakdownAssertion

**Purpose:** Validate distribution of items across categories.

**Use Cases:**
- App count by category (CRM: 3, ERP: 1, etc.)
- Infrastructure by type (container: 85, serverless: 12)
- Headcount by function

**Implementation:**

```python
@dataclass
class CategoryBreakdownAssertion(Assertion):
    """Assert that category distributions match."""

    tolerance_per_category: int = 1  # Allow ±1 item per category

    def assert_match(self, expected_breakdown: Dict[str, int], actual_breakdown: Dict[str, int]) -> AssertionResult:
        """
        Check if actual distribution matches expected per category.

        Args:
            expected_breakdown: {category: count} from fixture
            actual_breakdown: {category: count} from pipeline output
        """
        mismatches = {}

        # Check all expected categories
        for category, expected_count in expected_breakdown.items():
            actual_count = actual_breakdown.get(category, 0)
            diff = abs(actual_count - expected_count)

            if diff > self.tolerance_per_category:
                mismatches[category] = {
                    "expected": expected_count,
                    "actual": actual_count,
                    "diff": diff
                }

        # Check for unexpected categories
        unexpected = set(actual_breakdown.keys()) - set(expected_breakdown.keys())
        if unexpected:
            mismatches["_unexpected_categories"] = list(unexpected)

        passed = len(mismatches) == 0

        return AssertionResult(
            passed=passed,
            expected=expected_breakdown,
            actual=actual_breakdown,
            diff=mismatches,
            message=self._generate_message(mismatches, passed)
        )
```

---

### 7-12. Additional Assertions (Brief Specs)

**7. CriticalityDistributionAssertion**
- Validates count of items per criticality level (CRITICAL, HIGH, MEDIUM, LOW)
- Use case: Ensure 11 CRITICAL apps detected
- Tolerance: ±2 items per level

**8. StringMatchAssertion**
- Exact or fuzzy string matching
- Use case: SSO provider is "Okta"
- Supports case-insensitive, strip whitespace

**9. BooleanAssertion**
- True/false field checks
- Use case: MFA enabled = true
- No tolerance (strict match)

**10. ListContainsAssertion**
- Checks if expected items are in a list
- Use case: Compliance frameworks contain "SOC 2 Type II"
- Allows extra items

**11. RangeAssertion**
- Numeric value within min/max range
- Use case: Headcount between 40-50
- Flexible bounds

**12. CrossDomainAssertion**
- Consistency across domains
- Use case: User count in Identity domain matches employee count in Org domain
- Tolerance-based

---

## Verification Strategy

### Unit Tests

**File:** `tests/unit/test_assertions.py`

```python
class TestCountAssertion:
    def test_exact_match_passes(self):
        assertion = CountAssertion(tolerance=0)
        result = assertion.assert_match(expected=38, actual=38)
        assert result.passed

    def test_within_tolerance_passes(self):
        assertion = CountAssertion(tolerance=2)
        result = assertion.assert_match(expected=38, actual=36)
        assert result.passed

    def test_outside_tolerance_fails(self):
        assertion = CountAssertion(tolerance=2)
        result = assertion.assert_match(expected=38, actual=33)
        assert not result.passed
        assert "expected 38, got 33" in result.message

class TestCostAssertion:
    def test_percentage_tolerance_passes(self):
        assertion = CostAssertion(tolerance_pct=1.0)
        result = assertion.assert_match(expected=1000000, actual=1005000)
        assert result.passed  # 0.5% diff

    def test_zero_cost_requires_exact_match(self):
        assertion = CostAssertion(tolerance_pct=10.0)
        result = assertion.assert_match(expected=0, actual=100)
        assert not result.passed
```

---

### Integration Tests

**File:** `tests/integration/test_assertion_coverage.py`

**Purpose:** Verify that assertion suite covers all fixture fields.

```python
def test_all_fixture_fields_have_assertions():
    """Every field in golden fixture has a corresponding assertion."""
    fixture = load_fixture("cloudserve")
    assertions_used = get_all_assertions_from_tests()

    # Check applications domain
    assert "applications.count" in assertions_used
    assert "applications.total_cost" in assertions_used
    assert "applications.by_category" in assertions_used
    # ... etc for all domains
```

---

## Benefits

### Why Type-Specific Assertions

1. **Appropriate tolerance:** Costs use %, counts use absolute
2. **Clear semantics:** RiskAssertion vs CountAssertion makes intent obvious
3. **Better error messages:** Type-aware formatting ($X,XXX vs "X items")

### Why Tolerance-Based

1. **LLM non-determinism:** Exact matching is too brittle
2. **Rounding differences:** Cost extraction may round differently
3. **Minor variations OK:** 37 vs 38 apps likely not a real bug

---

## Expectations

### Coverage Target

**Minimum assertions per domain:**
- Applications: 8 assertions (count, cost, specific apps, categories, criticality, risks)
- Infrastructure: 5 assertions
- Network: 3 assertions
- Cybersecurity: 3 assertions
- Identity: 3 assertions
- Organization: 6 assertions

**Total: 30+ assertions per deal fixture**

### Success Criteria

- All 12 assertion types implemented with unit tests
- CloudServe test file uses 8+ assertion types
- 100% coverage of fixture fields (every field has an assertion)
- <5% false positive rate (tests fail incorrectly)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Too strict tolerances → brittle tests** | Start with loose tolerances (1-2%), tighten based on stability |
| **Too loose tolerances → bugs slip through** | Review failure rates, adjust if no failures ever occur |
| **Missing assertion types → gaps in coverage** | Systematically audit fixture schema for uncovered fields |
| **Assertion complexity → maintenance burden** | Keep assertions simple, avoid complex logic |

---

## Results Criteria

- All 12 assertion types have implementations
- Unit test coverage >90% for assertion classes
- CloudServe validation test uses all applicable assertion types
- Assertion failure messages are actionable (show expected vs actual clearly)

---

## Cross-References

- **01-test-validation-architecture.md:** Assertion engine component
- **02-golden-fixture-schema.md:** Fixture fields that assertions validate
- **04-test-data-documentation.md:** Guidance on which assertions to use for each domain
