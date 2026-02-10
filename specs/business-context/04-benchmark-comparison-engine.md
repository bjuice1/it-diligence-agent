# Spec 04: Benchmark Comparison Engine

**Feature Area:** Business Context
**Spec ID:** BC-04
**Status:** Draft
**Dependencies:** Spec 01 (Company Profile), Spec 02 (Industry Classification), Spec 03 (Industry Template)
**Consumed By:** Spec 05 (UI Rendering / Report Dashboard)
**Last Updated:** 2026-02-09

---

## Overview

The Benchmark Comparison Engine computes Expected vs Observed vs Variance for every available metric in an IT due diligence engagement. The engine is **fully deterministic** -- it makes zero LLM calls, produces identical output on repeated runs, and completes in under two seconds as pure in-memory computation.

The core innovation is **eligibility rules**: a set of pre-checks that prevent the engine from producing misleading metrics when upstream data is insufficient. A metric is only computed and displayed if every required input passes its eligibility gate. When a metric fails eligibility, the engine emits a structured explanation of exactly which data is missing and what documents would need to be in the data room to enable the comparison.

Every comparison row includes:
- **Expected range** (low / typical / high) sourced from the `BenchmarkLibrary` with full citation
- **Observed value** extracted or computed from `FactStore`, `InventoryStore`, and `OrganizationDataStore`
- **Variance classification** with deterministic implication text
- **Confidence level** reflecting the quality of both the benchmark and the observed data
- **Provenance chain** linking back to source documents and fact IDs

The engine covers three comparison dimensions:
1. **Metric comparisons** -- quantitative ratios and absolute values (IT spend % revenue, headcount ratios, cost per employee, etc.)
2. **Technology stack comparisons** -- expected systems from the industry template matched against the application inventory
3. **Staffing comparisons** -- expected role categories and counts matched against the organization data store

---

## Architecture

### New Files

| File | Purpose |
|------|---------|
| `services/benchmark_engine.py` | Comparison computation engine. Stateless functions that accept upstream data and return a `BenchmarkReport`. |
| `models/benchmark_comparison.py` | Dataclass models for `MetricComparison`, `SystemComparison`, `StaffingComparison`, `BenchmarkReport`, and supporting types. |

### Data Flow

```
CompanyProfile (Spec 01)
IndustryClassification (Spec 02)     services/benchmark_engine.py
IndustryTemplate (Spec 03)        -->  generate_benchmark_report()  -->  BenchmarkReport
FactStore (stores/fact_store.py)                                           |
InventoryStore (stores/inventory_store.py)                                 v
OrganizationDataStore (models/organization_stores.py)              Consumed by Spec 05
BenchmarkLibrary (tools_v2/benchmark_library.py)                   (UI / Report Dashboard)
```

### Read Dependencies

| Source | What is Read | How |
|--------|-------------|-----|
| `CompanyProfile` (Spec 01) | `revenue`, `employee_count`, `it_headcount`, `it_budget`, `size_tier`, `operating_model` -- each as `ProfileField(value, confidence, provenance, source_fact_ids)` | Passed as argument to `generate_benchmark_report()` |
| `IndustryClassification` (Spec 02) | `primary_industry`, `sub_industry`, `confidence` | Passed as argument; used to select benchmark rows from `BenchmarkLibrary` |
| `IndustryTemplate` (Spec 03) | `expected_systems` (critical/common/general lists), `expected_metrics` (it_pct_revenue, it_staff_per_100, app_count_per_100, it_cost_per_employee), `expected_organization`, `typical_risks`, `core_workflows`, `deal_lens_considerations` | Passed as argument; provides the "expected" side of each comparison |
| `FactStore` | Facts by domain/category; `fact_id`, `details`, `evidence`, `source_document`, `confidence_score` | Queried for supplementary observed values not available from CompanyProfile (e.g., security spend, cloud adoption %) |
| `InventoryStore` | `count("application", entity)`, `get_items(inventory_type="application", entity=entity)` | Application counts and vendor/category matching for technology stack comparison |
| `OrganizationDataStore` | `staff_members` list (each `StaffMember` with `role_category`, `employment_type`, `name`), `msp_relationships` list, `total_internal_fte`, `total_msp_fte_equivalent`, `authoritative_headcount` | Staffing comparison observed counts; MSP FTE equivalents for adjusted headcount |
| `BenchmarkLibrary` | `get_benchmark(metric, industry, company_size)` returning `BenchmarkData(low, typical, high, source, year, unit)` | Expected ranges for each metric; falls back to `"general"` industry if industry-specific data unavailable |

### Write / Output

| Output | Consumer |
|--------|----------|
| `BenchmarkReport` dataclass | Spec 05 (UI rendering), serialized to JSON for persistence, embedded in final report artifacts |

### Principles

- **No LLM calls.** Every computation is arithmetic or string formatting.
- **No side effects.** The engine reads from stores but writes nothing. It returns a `BenchmarkReport` value.
- **No network calls.** All benchmark data is embedded in `tools_v2/benchmark_library.py`.
- **Idempotent.** Given identical inputs, `generate_benchmark_report()` always returns an identical `BenchmarkReport`.

---

## Specification

### 1. Data Models

All models live in `models/benchmark_comparison.py`.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

@dataclass
class MetricProvenance:
    """
    Full traceability chain for how an observed metric was derived.

    Links back to source documents, fact IDs, and the computation steps
    so a reviewer can verify or challenge any number in the report.
    """
    expected_source: str
    # Human-readable citation for the benchmark.
    # Example: "Gartner IT Key Metrics 2024 -- Insurance, 50-100M"
    # Example: "Internal rule of thumb (cross-industry average)"

    observed_source: str
    # One of:
    #   "document_sourced"  -- value came directly from a single document/fact
    #   "computed"          -- value was calculated from multiple facts
    #   "inferred"          -- value was estimated from indirect evidence
    #   "inventory_count"   -- value came from counting inventory items

    observed_fact_ids: List[str] = field(default_factory=list)
    # Fact IDs from FactStore that contributed to the observed value.
    # Example: ["F-ORG-003", "F-ORG-007"]

    observed_documents: List[str] = field(default_factory=list)
    # Source document filenames.
    # Example: ["IT_Budget_FY2025.xlsx", "Org_Chart.pdf"]

    computation_notes: str = ""
    # Free-text explanation of how observed was calculated.
    # Example: "CompanyProfile.it_budget ($4.2M) / CompanyProfile.revenue ($82M) * 100 = 5.12%"


# ---------------------------------------------------------------------------
# Metric Comparison
# ---------------------------------------------------------------------------

@dataclass
class MetricComparison:
    """
    A single Expected vs Observed comparison row for a quantitative metric.

    This is the core unit of the benchmark report. Each row answers:
    "For metric X, what does the industry say is normal, what did we observe,
    and what does the gap (if any) imply?"
    """
    metric_id: str
    # Machine-readable identifier.
    # One of: "it_pct_revenue", "it_staff_per_100_employees",
    #         "app_count_per_100_employees", "it_cost_per_employee",
    #         "total_it_spend", "total_it_headcount",
    #         "outsourcing_pct", "cloud_adoption_pct",
    #         "security_pct_it", "tech_refresh_cycle"

    metric_label: str
    # Human-readable label for display.
    # Example: "IT Spend as % of Revenue"

    expected_low: Optional[float]
    expected_typical: Optional[float]
    expected_high: Optional[float]
    # From BenchmarkLibrary. None if no benchmark available for this
    # industry/size combination.

    observed: Optional[float]
    # Computed observed value. None if metric is ineligible.

    observed_formatted: str
    # Human-readable formatted value for display.
    # Examples: "$4.2M", "5.1%", "12 FTE", "18 apps/100 employees"
    # Empty string if observed is None.

    variance_category: str
    # Deterministic classification of observed vs expected.
    # One of: "well_below_range", "below_range",
    #         "within_range_low", "within_range_high",
    #         "above_range", "well_above_range",
    #         "insufficient_data", "no_benchmark"

    implication: str
    # Deterministic text explaining what the variance means.
    # Generated by classify_variance(). Never empty.

    confidence: str
    # One of: "high", "medium", "low"
    # Minimum of observed confidence and expected confidence.

    eligible: bool
    # True if this metric passed all eligibility checks.
    # False metrics are included in the report with ineligibility_reason.

    ineligibility_reason: str
    # If not eligible, a specific explanation of what is missing.
    # Empty string if eligible.

    provenance: MetricProvenance
    # Full traceability chain.

    unit: str
    # Display unit. One of: "%", "ratio", "count", "USD", "years"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "metric_label": self.metric_label,
            "expected_low": self.expected_low,
            "expected_typical": self.expected_typical,
            "expected_high": self.expected_high,
            "observed": self.observed,
            "observed_formatted": self.observed_formatted,
            "variance_category": self.variance_category,
            "implication": self.implication,
            "confidence": self.confidence,
            "eligible": self.eligible,
            "ineligibility_reason": self.ineligibility_reason,
            "provenance": {
                "expected_source": self.provenance.expected_source,
                "observed_source": self.provenance.observed_source,
                "observed_fact_ids": self.provenance.observed_fact_ids,
                "observed_documents": self.provenance.observed_documents,
                "computation_notes": self.provenance.computation_notes,
            },
            "unit": self.unit,
        }


# ---------------------------------------------------------------------------
# System (Technology Stack) Comparison
# ---------------------------------------------------------------------------

@dataclass
class SystemComparison:
    """
    Comparison of a single expected system from the industry template
    against what was found in the application inventory.

    Never asserts that a system does not exist -- only that it was or
    was not found in the provided data room documents.
    """
    category: str
    # Functional category from IndustryTemplate.expected_systems.
    # Example: "policy_administration", "claims_management", "erp"

    description: str
    # Human-readable description from the template.
    # Example: "Core policy lifecycle management system"

    expected_criticality: str
    # From template: "critical", "high", "medium"

    common_vendors: List[str]
    # Typical vendor names from template.
    # Example: ["Duck Creek", "Guidewire", "Majesco"]

    status: str
    # Match result. One of:
    #   "found"      -- a matching system exists in InventoryStore
    #   "not_found"  -- no matching system in InventoryStore or FactStore
    #   "partial"    -- mentioned in facts but not in structured inventory

    observed_system: Optional[str]
    # Name of the matched system if found.
    # Example: "Duck Creek Policy v4.2"

    observed_vendor: Optional[str]
    # Vendor of the matched system if found.
    # Example: "Duck Creek Technologies"

    inventory_item_id: Optional[str]
    # Cross-reference to InventoryStore item ID.
    # Example: "I-APP-a3f291"

    notes: str
    # Contextual notes. For "not_found" items, always includes the
    # standard disclaimer (see Technology Stack Comparison section).

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "expected_criticality": self.expected_criticality,
            "common_vendors": self.common_vendors,
            "status": self.status,
            "observed_system": self.observed_system,
            "observed_vendor": self.observed_vendor,
            "inventory_item_id": self.inventory_item_id,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Staffing Comparison
# ---------------------------------------------------------------------------

@dataclass
class StaffingComparison:
    """
    Comparison of observed staffing in a role category against what
    the industry template expects.

    Includes actual staff names for reviewer reference and MSP coverage
    notes where applicable.
    """
    category: str
    # RoleCategory value string.
    # Example: "infrastructure", "applications", "security"

    expected_label: str
    # Human-readable label from the template.
    # Example: "Infrastructure / Network Administration"

    expected_count: str
    # Range string from template.
    # Example: "2-3", "1-2", "3-5"

    expected_min: int
    # Parsed minimum from expected_count.

    expected_max: int
    # Parsed maximum from expected_count.

    observed_count: int
    # Actual count from OrganizationDataStore (FTE + contractors in this category).

    observed_names: List[str]
    # Names of staff members in this category (for reviewer reference).
    # Example: ["John Smith", "Jane Doe"]

    variance: str
    # One of: "within_range", "understaffed", "overstaffed"

    msp_coverage_note: str
    # If MSPs cover functions in this category, a note is included.
    # Example: "MSP 'Acme IT Services' provides 2.0 FTE equivalent for infrastructure."
    # Empty string if no MSP coverage.

    notes: str
    # Additional context.
    # Example: "Includes 1 contractor (1099) in addition to 2 FTEs."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "expected_label": self.expected_label,
            "expected_count": self.expected_count,
            "expected_min": self.expected_min,
            "expected_max": self.expected_max,
            "observed_count": self.observed_count,
            "observed_names": self.observed_names,
            "variance": self.variance,
            "msp_coverage_note": self.msp_coverage_note,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Benchmark Report (top-level container)
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkReport:
    """
    Complete benchmark comparison report.

    This is the single output artifact of the Benchmark Comparison Engine.
    It is consumed by Spec 05 (UI rendering) and persisted as JSON for
    downstream reporting.
    """

    # --- Context -----------------------------------------------------------

    company_name: str
    # Target company name from CompanyProfile.

    company_profile_summary: Dict[str, Any]
    # Serialized snapshot of key CompanyProfile fields used in this report:
    #   revenue, employee_count, it_headcount, it_budget, size_tier, operating_model
    # Each value is a dict with keys: value, confidence, provenance.

    industry_classification: Dict[str, Any]
    # Serialized snapshot: primary_industry, sub_industry, confidence.

    template_used: str
    # Template ID from IndustryTemplate (Spec 03).
    # Example: "insurance_mid_market"

    # --- Comparisons -------------------------------------------------------

    metric_comparisons: List[MetricComparison] = field(default_factory=list)
    # All metric comparison rows, both eligible and ineligible.

    system_comparisons: List[SystemComparison] = field(default_factory=list)
    # All expected systems from the template with match status.

    staffing_comparisons: List[StaffingComparison] = field(default_factory=list)
    # All role category comparisons from the template.

    # --- Summary Statistics ------------------------------------------------

    eligible_metric_count: int = 0
    # Number of metric comparisons where eligible == True.

    total_metric_count: int = 0
    # Total number of metric comparisons attempted.

    overall_confidence: str = "low"
    # Weighted summary of confidence across eligible metrics.
    # Computed as the mode (most common) confidence level among eligible metrics.
    # Falls back to "low" if no eligible metrics.

    # --- Deal Context ------------------------------------------------------

    deal_lens: Optional[str] = None
    # If CompanyProfile.operating_model or other signals indicate a deal type.
    # One of: "growth", "carve_out", "platform_add_on", "turnaround", None.

    deal_lens_considerations: List[str] = field(default_factory=list)
    # From IndustryTemplate.deal_lens_considerations, filtered to the
    # applicable deal_lens. Empty list if deal_lens is None.

    # --- Metadata ----------------------------------------------------------

    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    # ISO 8601 timestamp of report generation.

    is_deterministic: bool = True
    # Always True. Marker for downstream consumers to know this report
    # contains no LLM-generated content.

    engine_version: str = "1.0.0"
    # Semantic version of the benchmark engine for compatibility tracking.

    def get_eligible_metrics(self) -> List[MetricComparison]:
        """Return only metrics that passed eligibility checks."""
        return [m for m in self.metric_comparisons if m.eligible]

    def get_ineligible_metrics(self) -> List[MetricComparison]:
        """Return metrics that failed eligibility checks."""
        return [m for m in self.metric_comparisons if not m.eligible]

    def get_critical_system_gaps(self) -> List[SystemComparison]:
        """Return critical expected systems that were not found."""
        return [
            s for s in self.system_comparisons
            if s.expected_criticality == "critical" and s.status == "not_found"
        ]

    def get_understaffed_categories(self) -> List[StaffingComparison]:
        """Return role categories flagged as understaffed."""
        return [s for s in self.staffing_comparisons if s.variance == "understaffed"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_name": self.company_name,
            "company_profile_summary": self.company_profile_summary,
            "industry_classification": self.industry_classification,
            "template_used": self.template_used,
            "metric_comparisons": [m.to_dict() for m in self.metric_comparisons],
            "system_comparisons": [s.to_dict() for s in self.system_comparisons],
            "staffing_comparisons": [s.to_dict() for s in self.staffing_comparisons],
            "eligible_metric_count": self.eligible_metric_count,
            "total_metric_count": self.total_metric_count,
            "overall_confidence": self.overall_confidence,
            "deal_lens": self.deal_lens,
            "deal_lens_considerations": self.deal_lens_considerations,
            "generated_at": self.generated_at,
            "is_deterministic": self.is_deterministic,
            "engine_version": self.engine_version,
        }
```

---

### 2. Metric Definitions and Extraction Logic

Each metric has a unique ID, a human-readable label, a formula for computing the observed value, and an eligibility rule. The engine iterates over all defined metrics, checks eligibility, computes the observed value if eligible, fetches the expected range from `BenchmarkLibrary`, and classifies the variance.

#### 2.1 Metric Registry

The engine maintains an ordered list of metric definitions. Each entry specifies:

| Field | Type | Purpose |
|-------|------|---------|
| `metric_id` | `str` | Unique key matching `BenchmarkLibrary` metric names |
| `metric_label` | `str` | Human-readable display name |
| `unit` | `str` | Display unit (`%`, `ratio`, `count`, `USD`, `years`) |
| `benchmark_library_key` | `str` | Key in `BENCHMARK_LIBRARY` dict for expected range lookup |
| `requires` | `List[str]` | CompanyProfile fields or store queries that must be non-None |
| `min_confidence` | `str` | Minimum acceptable confidence for required ProfileFields (`"high"`, `"medium"`, `"low"`) |
| `additional_check` | `Optional[str]` | Name of an additional validation function |
| `failure_message` | `str` | User-facing explanation when ineligible |
| `compute` | `Callable` | Function that takes resolved inputs and returns `(observed_value, provenance)` |
| `format` | `Callable` | Function that takes `observed_value` and returns `observed_formatted` string |

```python
METRIC_REGISTRY = [
    {
        "metric_id": "it_pct_revenue",
        "metric_label": "IT Spend as % of Revenue",
        "unit": "%",
        "benchmark_library_key": "it_pct_revenue",
        "requires": ["revenue", "it_budget"],
        "min_confidence": "medium",
        "additional_check": "same_fiscal_period",
        "failure_message": (
            "Revenue or IT budget not found in data room. "
            "Cannot compute IT spend as percentage of revenue."
        ),
    },
    {
        "metric_id": "it_staff_per_100_employees",
        "metric_label": "IT Staff per 100 Employees",
        "unit": "ratio",
        "benchmark_library_key": "it_staff_ratio",
        "requires": ["it_headcount", "employee_count"],
        "min_confidence": "low",
        "additional_check": "it_headcount_distinguishable",
        "failure_message": (
            "IT headcount or total employee count not available."
        ),
    },
    {
        "metric_id": "app_count_per_100_employees",
        "metric_label": "Applications per 100 Employees",
        "unit": "count",
        "benchmark_library_key": "app_count_ratio",
        "requires": ["employee_count"],
        "min_confidence": "low",
        "additional_check": "app_inventory_populated",
        "failure_message": (
            "Employee count not available or no applications found in inventory."
        ),
    },
    {
        "metric_id": "it_cost_per_employee",
        "metric_label": "IT Cost per Employee",
        "unit": "USD",
        "benchmark_library_key": "cost_per_employee",
        "requires": ["it_budget", "employee_count"],
        "min_confidence": "medium",
        "additional_check": None,
        "failure_message": (
            "IT budget or total employee count not available."
        ),
    },
    {
        "metric_id": "total_it_spend",
        "metric_label": "Total IT Spend",
        "unit": "USD",
        "benchmark_library_key": "it_pct_revenue",
        # Special: expected is computed, not direct lookup.
        "requires": ["it_budget"],
        "min_confidence": "medium",
        "additional_check": None,
        "failure_message": (
            "IT budget not found in data room documents."
        ),
    },
    {
        "metric_id": "total_it_headcount",
        "metric_label": "Total IT Headcount",
        "unit": "count",
        "benchmark_library_key": None,
        # Expected comes from IndustryTemplate.expected_organization, not BenchmarkLibrary.
        "requires": ["it_headcount"],
        "min_confidence": "low",
        "additional_check": None,
        "failure_message": (
            "IT headcount not available from data room documents."
        ),
    },
    {
        "metric_id": "outsourcing_pct",
        "metric_label": "IT Outsourcing %",
        "unit": "%",
        "benchmark_library_key": "outsourcing_pct",
        "requires": ["it_budget"],
        "min_confidence": "low",
        "additional_check": "msp_costs_available",
        "failure_message": (
            "IT budget or MSP cost data not available to compute outsourcing percentage."
        ),
    },
    {
        "metric_id": "security_pct_it",
        "metric_label": "Cybersecurity Spend as % of IT Budget",
        "unit": "%",
        "benchmark_library_key": "security_pct_it",
        "requires": ["it_budget"],
        "min_confidence": "medium",
        "additional_check": "security_spend_available",
        "failure_message": (
            "IT budget or cybersecurity spend not available."
        ),
    },
]
```

#### 2.2 Per-Metric Extraction Rules

##### 2.2.1 `it_pct_revenue` -- IT Spend as % of Revenue

**Formula:**
```
observed = (CompanyProfile.it_budget.value / CompanyProfile.revenue.value) * 100
```

**Eligibility:**
- `CompanyProfile.it_budget.value` must be non-None
- `CompanyProfile.revenue.value` must be non-None
- Both must have `confidence >= "medium"` (confidence ordering: `"high"` > `"medium"` > `"low"`)
- **Additional check (`same_fiscal_period`):** If both `it_budget.provenance` and `revenue.provenance` contain a year, they must match. If years cannot be determined, the check passes with a provenance note.

**Expected Range:**
```python
benchmark = get_benchmark("it_pct_revenue", industry, size_tier, fallback_to_general=True)
# expected_low = benchmark.low
# expected_typical = benchmark.typical
# expected_high = benchmark.high
```

**Provenance:**
- `expected_source`: `benchmark.source` + ` ({benchmark.year})` + ` -- {industry}, {size_tier}`
- `observed_source`: `"computed"`
- `observed_fact_ids`: union of `CompanyProfile.it_budget.source_fact_ids` and `CompanyProfile.revenue.source_fact_ids`
- `computation_notes`: `"CompanyProfile.it_budget (${it_budget:,.0f}) / CompanyProfile.revenue (${revenue:,.0f}) * 100 = {result:.2f}%"`

**Formatting:**
- `observed_formatted`: `"{observed:.1f}%"` (e.g., `"5.1%"`)

**Ineligibility Message:**
`"Revenue or IT budget not found in data room. Cannot compute IT spend as percentage of revenue."`

---

##### 2.2.2 `it_staff_per_100_employees` -- IT Staff per 100 Employees

**Formula:**
```
observed = (CompanyProfile.it_headcount.value / CompanyProfile.employee_count.value) * 100
```

**Eligibility:**
- `CompanyProfile.it_headcount.value` must be non-None
- `CompanyProfile.employee_count.value` must be non-None
- Both must have `confidence >= "low"`
- **Additional check (`it_headcount_distinguishable`):** The `it_headcount` value must represent a clearly identified IT-specific count. If `it_headcount.provenance` indicates the value was derived from total headcount without clear IT/non-IT separation, the check fails.

**Special Handling -- MSP FTE Equivalents:**
If the `OrganizationDataStore` contains MSP relationships, the engine computes two variants:
- `observed_internal_only`: uses `CompanyProfile.it_headcount.value` as-is
- `observed_including_msp`: adds `OrganizationDataStore.total_msp_fte_equivalent` to the headcount

The primary `observed` value uses `observed_internal_only`. The provenance `computation_notes` includes both variants if MSP data exists:
```
"Internal IT headcount: 15 FTE. MSP FTE equivalent: 4.0. Ratio computed using internal only (15/350 * 100 = 4.29). Including MSP: (19/350 * 100 = 5.43)."
```

**Expected Range:**
```python
benchmark = get_benchmark("it_staff_ratio", industry, size_tier, fallback_to_general=True)
```

**Formatting:**
- `observed_formatted`: `"{observed:.1f} per 100"` (e.g., `"4.3 per 100"`)

---

##### 2.2.3 `app_count_per_100_employees` -- Applications per 100 Employees

**Formula:**
```
app_count = InventoryStore.count("application", entity)
observed = (app_count / CompanyProfile.employee_count.value) * 100
```

**Eligibility:**
- `CompanyProfile.employee_count.value` must be non-None
- `CompanyProfile.employee_count.confidence >= "low"`
- **Additional check (`app_inventory_populated`):** `InventoryStore.count("application", entity)` must be `> 0`

**Application Count Filtering:**
The engine counts business applications only. It excludes items from `InventoryStore` where the application `data` dict contains `category` matching any of:
- `"infrastructure_utility"`
- `"monitoring"`
- `"backup"`
- `"antivirus"`
- `"agent"`

If the `data` dict has no `category` field, the application is included in the count (conservative -- assumes it is a business application).

**Expected Range:**
```python
benchmark = get_benchmark("app_count_ratio", industry, size_tier, fallback_to_general=True)
```

**Formatting:**
- `observed_formatted`: `"{app_count} apps ({observed:.1f} per 100 employees)"` (e.g., `"42 apps (12.0 per 100 employees)"`)

---

##### 2.2.4 `it_cost_per_employee` -- IT Cost per Employee

**Formula:**
```
observed = CompanyProfile.it_budget.value / CompanyProfile.employee_count.value
```

**Eligibility:**
- `CompanyProfile.it_budget.value` must be non-None with `confidence >= "medium"`
- `CompanyProfile.employee_count.value` must be non-None with `confidence >= "medium"`

**Expected Range:**
```python
benchmark = get_benchmark("cost_per_employee", industry, size_tier, fallback_to_general=True)
```

**Formatting:**
- `observed_formatted`: `"${observed:,.0f}"` (e.g., `"$12,857"`)

---

##### 2.2.5 `total_it_spend` -- Total IT Spend (Absolute)

**Formula:**
```
observed = CompanyProfile.it_budget.value
```

**Expected Computation (special -- not a direct lookup):**
If `CompanyProfile.revenue.value` is non-None:
```python
pct_benchmark = get_benchmark("it_pct_revenue", industry, size_tier, fallback_to_general=True)
if pct_benchmark:
    expected_low = pct_benchmark.low * revenue / 100
    expected_typical = pct_benchmark.typical * revenue / 100
    expected_high = pct_benchmark.high * revenue / 100
```
If revenue is not available, `expected_low/typical/high` are all `None`, and `variance_category` is set to `"no_benchmark"` with implication `"Revenue not available; cannot compute expected IT spend range for comparison."`.

**Eligibility:**
- `CompanyProfile.it_budget.value` must be non-None with `confidence >= "medium"`

**Formatting:**
- For values >= 1,000,000: `"${observed/1e6:.1f}M"` (e.g., `"$4.2M"`)
- For values >= 1,000: `"${observed/1e3:.0f}K"` (e.g., `"$850K"`)
- Otherwise: `"${observed:,.0f}"` (e.g., `"$750"`)

---

##### 2.2.6 `total_it_headcount` -- Total IT Headcount (Absolute)

**Formula:**
```
observed = CompanyProfile.it_headcount.value
```

If `OrganizationDataStore.total_msp_fte_equivalent > 0`, the provenance notes include:
```
"Internal IT headcount: {it_headcount} FTE. MSP FTE equivalent: {msp_fte}. Total effective IT capacity: {it_headcount + msp_fte}."
```

**Expected Range:**
From `IndustryTemplate.expected_organization.typical_it_headcount_range` (parsed as `min-max` string into `expected_low` and `expected_high` with midpoint as `expected_typical`). If the template does not provide this field, expected values are `None`.

**Eligibility:**
- `CompanyProfile.it_headcount.value` must be non-None

**Formatting:**
- `observed_formatted`: `"{observed} FTE"` (e.g., `"15 FTE"`)
- If MSP FTEs exist, append: `" (+{msp_fte:.1f} MSP FTE)"` (e.g., `"15 FTE (+4.0 MSP FTE)"`)

---

##### 2.2.7 `outsourcing_pct` -- IT Outsourcing Percentage

**Formula:**
```
msp_total_cost = sum(msp.contract_value_annual for msp in OrganizationDataStore.msp_relationships where msp.entity == "target")
observed = (msp_total_cost / CompanyProfile.it_budget.value) * 100
```

**Eligibility:**
- `CompanyProfile.it_budget.value` must be non-None
- **Additional check (`msp_costs_available`):** At least one MSP relationship with `contract_value_annual > 0` must exist in `OrganizationDataStore`

**Expected Range:**
```python
benchmark = get_benchmark("outsourcing_pct", industry, size_tier, fallback_to_general=True)
```

**Formatting:**
- `observed_formatted`: `"{observed:.0f}%"` (e.g., `"35%"`)

---

##### 2.2.8 `security_pct_it` -- Cybersecurity Spend as % of IT Budget

**Formula:**
```
security_spend = extract_security_spend_from_facts(fact_store)
observed = (security_spend / CompanyProfile.it_budget.value) * 100
```

**`extract_security_spend_from_facts` Logic:**
1. Query `FactStore` for facts where `domain == "cybersecurity"` and `category == "budget"` or where `details` contains keys `"annual_cost"`, `"security_budget"`, or `"cybersecurity_spend"`.
2. Sum the numeric values found. If multiple facts provide overlapping costs, take the single highest-confidence fact's value to avoid double-counting.
3. Return `(security_spend, fact_ids, documents)` or `(None, [], [])` if no data found.

**Eligibility:**
- `CompanyProfile.it_budget.value` must be non-None with `confidence >= "medium"`
- **Additional check (`security_spend_available`):** `extract_security_spend_from_facts` must return a non-None value

**Expected Range:**
```python
benchmark = get_benchmark("security_pct_it", industry, size_tier, fallback_to_general=True)
```

**Formatting:**
- `observed_formatted`: `"{observed:.1f}%"` (e.g., `"8.5%"`)

---

### 3. Eligibility Rules

Eligibility rules are the core safety mechanism. They prevent the engine from computing and displaying metrics that would be misleading due to incomplete data.

#### 3.1 Eligibility Check Algorithm

```python
CONFIDENCE_ORDERING = {"high": 3, "medium": 2, "low": 1}


def check_metric_eligibility(
    metric_def: dict,
    company_profile,       # CompanyProfile from Spec 01
    inventory_store,       # InventoryStore
    org_data_store,        # OrganizationDataStore
    fact_store,            # FactStore
) -> tuple[bool, str]:
    """
    Check whether a metric passes all eligibility requirements.

    Returns:
        (is_eligible, reason)
        If is_eligible is True, reason is "".
        If is_eligible is False, reason explains what is missing.
    """

    # Step 1: Check required CompanyProfile fields
    min_conf_level = CONFIDENCE_ORDERING.get(metric_def.get("min_confidence", "low"), 1)

    for field_name in metric_def["requires"]:
        profile_field = getattr(company_profile, field_name, None)
        if profile_field is None or profile_field.value is None:
            return (False, metric_def["failure_message"])

        field_conf_level = CONFIDENCE_ORDERING.get(profile_field.confidence, 0)
        if field_conf_level < min_conf_level:
            return (
                False,
                f"{field_name} confidence is '{profile_field.confidence}', "
                f"but metric requires at least '{metric_def['min_confidence']}'. "
                f"{metric_def['failure_message']}"
            )

    # Step 2: Run additional check if specified
    additional_check = metric_def.get("additional_check")
    if additional_check:
        check_fn = ADDITIONAL_CHECKS.get(additional_check)
        if check_fn:
            passed, reason = check_fn(company_profile, inventory_store, org_data_store, fact_store)
            if not passed:
                return (False, reason)

    return (True, "")
```

#### 3.2 Additional Check Functions

```python
ADDITIONAL_CHECKS = {
    "same_fiscal_period": _check_same_fiscal_period,
    "it_headcount_distinguishable": _check_it_headcount_distinguishable,
    "app_inventory_populated": _check_app_inventory_populated,
    "msp_costs_available": _check_msp_costs_available,
    "security_spend_available": _check_security_spend_available,
}


def _check_same_fiscal_period(profile, inventory, org_store, fact_store) -> tuple[bool, str]:
    """
    Verify that IT budget and revenue values come from the same fiscal period.
    If provenance does not include year information, the check passes with a note.
    """
    budget_year = _extract_year_from_provenance(profile.it_budget.provenance)
    revenue_year = _extract_year_from_provenance(profile.revenue.provenance)

    if budget_year is not None and revenue_year is not None:
        if budget_year != revenue_year:
            return (
                False,
                f"IT budget is from fiscal year {budget_year} but revenue is from "
                f"fiscal year {revenue_year}. Cannot reliably compute ratio across "
                f"different fiscal periods."
            )
    # If either year is unknown, pass the check (but note it in provenance)
    return (True, "")


def _check_it_headcount_distinguishable(profile, inventory, org_store, fact_store) -> tuple[bool, str]:
    """
    Verify that IT headcount represents a clearly identified IT-specific count,
    not an undifferentiated total headcount.
    """
    if profile.it_headcount is None or profile.it_headcount.value is None:
        return (False, "IT headcount not available.")

    # If it_headcount equals employee_count, it is likely undifferentiated
    if (
        profile.employee_count is not None
        and profile.employee_count.value is not None
        and profile.it_headcount.value == profile.employee_count.value
    ):
        return (
            False,
            "IT headcount appears to equal total employee count, suggesting "
            "IT staff have not been separately identified."
        )

    return (True, "")


def _check_app_inventory_populated(profile, inventory, org_store, fact_store) -> tuple[bool, str]:
    """
    Verify that the application inventory has at least one entry.
    """
    app_count = inventory.count("application") if inventory else 0
    if app_count == 0:
        return (
            False,
            "No applications found in inventory. Application inventory must be "
            "populated before computing application density metrics."
        )
    return (True, "")


def _check_msp_costs_available(profile, inventory, org_store, fact_store) -> tuple[bool, str]:
    """
    Verify that at least one MSP relationship has cost data.
    """
    if org_store is None or not org_store.msp_relationships:
        return (
            False,
            "No MSP/outsourcing relationships found in organization data."
        )

    has_costs = any(
        msp.contract_value_annual > 0
        for msp in org_store.msp_relationships
        if msp.entity == "target"
    )
    if not has_costs:
        return (
            False,
            "MSP relationships exist but no annual cost data is available."
        )

    return (True, "")


def _check_security_spend_available(profile, inventory, org_store, fact_store) -> tuple[bool, str]:
    """
    Verify that cybersecurity spend data exists in the fact store.
    """
    if fact_store is None:
        return (False, "Fact store not available.")

    security_facts = [
        f for f in fact_store.facts
        if f.domain == "cybersecurity"
        and f.details
        and any(
            k in f.details
            for k in ["annual_cost", "security_budget", "cybersecurity_spend", "total_cost"]
        )
    ]

    if not security_facts:
        return (
            False,
            "No cybersecurity spend data found in extracted facts."
        )

    return (True, "")
```

#### 3.3 Confidence Minimum Rationale

| Confidence Minimum | Rationale |
|-------------------|-----------|
| `"medium"` for financial metrics (`it_pct_revenue`, `it_cost_per_employee`, `total_it_spend`, `security_pct_it`) | Financial ratios with low-confidence inputs produce unreliable numbers that could mislead deal teams. A "medium" threshold ensures at least partial corroboration. |
| `"low"` for count-based metrics (`it_staff_per_100`, `app_count_per_100`, `total_it_headcount`, `outsourcing_pct`) | Headcount and application counts are more forgiving of estimation because the magnitude is still informative even with uncertainty. |

---

### 4. Variance Classification

Variance classification is fully deterministic. The function takes the observed value and the expected range, and returns a category string and an implication string. No randomness, no LLM.

```python
def classify_variance(
    observed: Optional[float],
    expected_low: Optional[float],
    expected_typical: Optional[float],
    expected_high: Optional[float],
    metric_label: str = "",
) -> tuple[str, str]:
    """
    Classify observed vs expected and produce a deterministic implication.

    Args:
        observed: The computed observed value. None if metric is ineligible.
        expected_low: Low end of benchmark range. None if no benchmark.
        expected_typical: Typical benchmark value. None if no benchmark.
        expected_high: High end of benchmark range. None if no benchmark.
        metric_label: Human-readable metric name for inclusion in text.

    Returns:
        (variance_category, implication) -- both deterministic strings.
    """
    if observed is None:
        return (
            "insufficient_data",
            "Observed value not available for this metric."
        )

    if expected_low is None or expected_typical is None or expected_high is None:
        return (
            "no_benchmark",
            "No industry benchmark available for comparison. "
            "Observed value is reported without a reference range."
        )

    # --- Below Range ---
    if observed < expected_low:
        if expected_low > 0:
            pct_below = ((expected_low - observed) / expected_low) * 100
        else:
            pct_below = 0

        if pct_below > 30:
            return (
                "well_below_range",
                f"Significantly below industry norm ({pct_below:.0f}% below low end). "
                f"May indicate underinvestment, heavy outsourcing not captured in "
                f"the metric, or incomplete data in the data room."
            )
        return (
            "below_range",
            f"Below industry range ({pct_below:.0f}% below low end). "
            f"May indicate lean operations, outsourcing, or data room gaps."
        )

    # --- Above Range ---
    if observed > expected_high:
        if expected_high > 0:
            pct_above = ((observed - expected_high) / expected_high) * 100
        else:
            pct_above = 0

        if pct_above > 30:
            return (
                "well_above_range",
                f"Significantly above industry norm ({pct_above:.0f}% above high end). "
                f"May indicate higher environmental complexity, over-investment, "
                f"inclusion of non-IT costs, or an unusually broad IT scope."
            )
        return (
            "above_range",
            f"Above industry range ({pct_above:.0f}% above high end). "
            f"May indicate higher complexity or broader IT scope definition."
        )

    # --- Within Range ---
    if observed <= expected_typical:
        return (
            "within_range_low",
            f"Within expected range, toward the lower end. "
            f"Consistent with industry norms for this profile."
        )
    else:
        return (
            "within_range_high",
            f"Within expected range, toward the upper end. "
            f"Consistent with industry norms for this profile."
        )
```

#### 4.1 Variance Category Summary

| Category | Condition | Color Hint (for Spec 05) |
|----------|-----------|--------------------------|
| `well_below_range` | observed < expected_low and gap > 30% | Red |
| `below_range` | observed < expected_low and gap <= 30% | Amber |
| `within_range_low` | expected_low <= observed <= expected_typical | Green |
| `within_range_high` | expected_typical < observed <= expected_high | Green |
| `above_range` | observed > expected_high and gap <= 30% | Amber |
| `well_above_range` | observed > expected_high and gap > 30% | Red |
| `insufficient_data` | observed is None | Grey |
| `no_benchmark` | expected range is None | Grey |

---

### 5. Technology Stack Comparison

For each expected system in the `IndustryTemplate.expected_systems` list, the engine searches the `InventoryStore` and `FactStore` for evidence of a matching system.

#### 5.1 Match Algorithm

```python
def match_expected_system(
    expected_system: dict,
    inventory_store: InventoryStore,
    fact_store: FactStore,
    entity: str = "target",
) -> SystemComparison:
    """
    Match a single expected system from the industry template against
    inventory and facts.

    Args:
        expected_system: Dict with keys: category, description, criticality,
                        common_vendors, aliases (optional list of alternative names)
        inventory_store: Application inventory
        fact_store: Extracted facts
        entity: "target" or "buyer"

    Returns:
        SystemComparison with match status.
    """
    category = expected_system["category"]
    common_vendors = expected_system.get("common_vendors", [])
    aliases = expected_system.get("aliases", [])

    # Build search terms: category name + aliases + vendor names
    search_terms = [category.lower().replace("_", " ")] + [a.lower() for a in aliases]
    vendor_terms = [v.lower() for v in common_vendors]

    # --- Phase 1: Search InventoryStore ---
    apps = inventory_store.get_items(inventory_type="application", entity=entity)

    for app in apps:
        app_data = app.data or {}
        app_name = (app_data.get("name", "") or "").lower()
        app_vendor = (app_data.get("vendor", "") or "").lower()
        app_category = (app_data.get("category", "") or "").lower()
        app_description = (app_data.get("description", "") or "").lower()

        # Match by vendor name
        vendor_match = any(v in app_vendor or v in app_name for v in vendor_terms)

        # Match by category or alias
        category_match = any(
            term in app_category or term in app_name or term in app_description
            for term in search_terms
        )

        if vendor_match or category_match:
            return SystemComparison(
                category=category,
                description=expected_system.get("description", ""),
                expected_criticality=expected_system.get("criticality", "medium"),
                common_vendors=common_vendors,
                status="found",
                observed_system=app_data.get("name"),
                observed_vendor=app_data.get("vendor"),
                inventory_item_id=app.item_id,
                notes=_build_found_note(app_data, expected_system),
            )

    # --- Phase 2: Search FactStore for partial evidence ---
    all_search_terms = search_terms + vendor_terms
    matching_facts = []

    for fact in fact_store.facts:
        if fact.domain not in ("applications", "infrastructure", "general"):
            continue
        fact_text = (
            (fact.item or "").lower()
            + " "
            + str(fact.details or "").lower()
            + " "
            + str(fact.evidence or "").lower()
        )
        if any(term in fact_text for term in all_search_terms):
            matching_facts.append(fact)

    if matching_facts:
        best_fact = max(matching_facts, key=lambda f: f.confidence_score)
        return SystemComparison(
            category=category,
            description=expected_system.get("description", ""),
            expected_criticality=expected_system.get("criticality", "medium"),
            common_vendors=common_vendors,
            status="partial",
            observed_system=best_fact.item,
            observed_vendor=None,
            inventory_item_id=None,
            notes=(
                f"Mentioned in extracted facts (source: {best_fact.source_document or 'unknown'}) "
                f"but not present as a structured inventory item. "
                f"May require confirmation during management interviews."
            ),
        )

    # --- Phase 3: Not found ---
    return SystemComparison(
        category=category,
        description=expected_system.get("description", ""),
        expected_criticality=expected_system.get("criticality", "medium"),
        common_vendors=common_vendors,
        status="not_found",
        observed_system=None,
        observed_vendor=None,
        inventory_item_id=None,
        notes=(
            "Not found in data room documents. This may indicate: "
            "(a) the function is outsourced to a third party, "
            "(b) it is handled by a different system under another name, or "
            "(c) it was not included in the provided documentation. "
            "Recommend clarifying during management interviews."
        ),
    )


def _build_found_note(app_data: dict, expected_system: dict) -> str:
    """Build contextual note for a found system."""
    parts = []

    version = app_data.get("version")
    if version:
        parts.append(f"Version: {version}")

    vendor = app_data.get("vendor")
    expected_vendors = expected_system.get("common_vendors", [])
    if vendor and expected_vendors:
        if vendor.lower() not in [v.lower() for v in expected_vendors]:
            parts.append(
                f"Vendor '{vendor}' is not among common vendors "
                f"({', '.join(expected_vendors)}) but serves the same function."
            )

    if not parts:
        parts.append("Matched in application inventory.")

    return " ".join(parts)
```

#### 5.2 Important Principle: Never Assert Absence

The engine **never** states that a system does not exist at the target company. It only reports whether the system was found in the provided data room documents. The `not_found` status always includes the three-part disclaimer:
1. The function may be outsourced
2. It may be handled by a different system
3. It may not have been included in documentation

This prevents the report from making false negative assertions that could mislead the deal team.

---

### 6. Staffing Comparison

For each expected role category in the `IndustryTemplate.expected_organization`, the engine counts matching staff from `OrganizationDataStore` and classifies the variance.

#### 6.1 Staffing Match Algorithm

```python
from models.organization_models import RoleCategory, EmploymentType


def compute_staffing_comparisons(
    expected_organization: list,
    org_data_store,
    entity: str = "target",
) -> List[StaffingComparison]:
    """
    Compare observed staffing against template expectations.

    Args:
        expected_organization: List of dicts from IndustryTemplate, each with:
            category, label, expected_count (string like "2-3"), description
        org_data_store: OrganizationDataStore with staff_members and msp_relationships
        entity: "target" or "buyer"

    Returns:
        List of StaffingComparison objects.
    """
    comparisons = []

    if org_data_store is None:
        return comparisons

    target_staff = [
        s for s in org_data_store.staff_members
        if s.entity == entity
    ]
    target_msps = [
        m for m in org_data_store.msp_relationships
        if m.entity == entity
    ]

    for expected in expected_organization:
        category_str = expected["category"]
        expected_label = expected.get("label", category_str.replace("_", " ").title())
        expected_count_str = expected.get("expected_count", "0-0")

        # Parse range
        expected_min, expected_max = _parse_count_range(expected_count_str)

        # Map category string to RoleCategory enum
        role_category = RoleCategory.from_string(category_str)

        # Count matching staff
        matching_staff = [
            s for s in target_staff
            if s.role_category == role_category
        ]
        observed_count = len(matching_staff)
        observed_names = [s.name for s in matching_staff]

        # Classify variance
        if observed_count < expected_min:
            variance = "understaffed"
        elif observed_count > expected_max:
            variance = "overstaffed"
        else:
            variance = "within_range"

        # Build MSP coverage note
        msp_coverage_note = _build_msp_coverage_note(
            category_str, role_category, target_msps
        )

        # Build additional notes
        notes_parts = []
        fte_count = sum(1 for s in matching_staff if s.employment_type == EmploymentType.FTE)
        contractor_count = sum(1 for s in matching_staff if s.employment_type == EmploymentType.CONTRACTOR)
        if contractor_count > 0:
            notes_parts.append(
                f"Includes {contractor_count} contractor(s) in addition to {fte_count} FTE(s)."
            )
        if observed_count == 0 and msp_coverage_note:
            notes_parts.append(
                "No internal staff identified, but MSP coverage exists for this function."
            )
        elif observed_count == 0 and not msp_coverage_note:
            notes_parts.append(
                "No staff identified for this category in the data room documents. "
                "Function may be covered by staff categorized under a different role, "
                "or may represent a gap."
            )

        comparisons.append(StaffingComparison(
            category=category_str,
            expected_label=expected_label,
            expected_count=expected_count_str,
            expected_min=expected_min,
            expected_max=expected_max,
            observed_count=observed_count,
            observed_names=observed_names,
            variance=variance,
            msp_coverage_note=msp_coverage_note,
            notes=" ".join(notes_parts),
        ))

    return comparisons


def _parse_count_range(range_str: str) -> tuple[int, int]:
    """
    Parse a count range string into (min, max).

    Handles formats:
        "2-3"   -> (2, 3)
        "2"     -> (2, 2)
        "2+"    -> (2, 999)
        "1-2"   -> (1, 2)
    """
    range_str = str(range_str).strip()

    if "-" in range_str and not range_str.startswith("-"):
        parts = range_str.split("-")
        try:
            return (int(parts[0].strip()), int(parts[1].strip()))
        except (ValueError, IndexError):
            return (0, 0)

    if range_str.endswith("+"):
        try:
            return (int(range_str[:-1].strip()), 999)
        except ValueError:
            return (0, 0)

    try:
        val = int(range_str)
        return (val, val)
    except ValueError:
        return (0, 0)


def _build_msp_coverage_note(
    category_str: str,
    role_category: RoleCategory,
    msps: list,
) -> str:
    """
    Check if any MSP provides services relevant to this role category
    and build a coverage note.
    """
    # Map role categories to service name keywords
    CATEGORY_SERVICE_KEYWORDS = {
        RoleCategory.INFRASTRUCTURE: ["infrastructure", "network", "server", "hosting", "cloud"],
        RoleCategory.APPLICATIONS: ["application", "development", "software", "saas"],
        RoleCategory.SECURITY: ["security", "cybersecurity", "soc", "siem", "compliance"],
        RoleCategory.SERVICE_DESK: ["help desk", "service desk", "support", "end user"],
        RoleCategory.DATA: ["data", "analytics", "database", "bi", "reporting"],
    }

    keywords = CATEGORY_SERVICE_KEYWORDS.get(role_category, [])
    if not keywords:
        return ""

    coverage_notes = []
    for msp in msps:
        for service in msp.services:
            service_name_lower = service.service_name.lower()
            if any(kw in service_name_lower for kw in keywords):
                coverage_notes.append(
                    f"MSP '{msp.vendor_name}' provides {service.fte_equivalent:.1f} FTE "
                    f"equivalent for {service.service_name}."
                )

    return " ".join(coverage_notes)
```

---

### 7. Confidence Scoring

#### 7.1 Per-Metric Confidence

Each metric's confidence is the **minimum** of the observed data confidence and the expected data confidence.

```python
def compute_metric_confidence(
    observed_confidence: str,
    expected_confidence: str,
) -> str:
    """
    Compute per-metric confidence as the minimum of observed and expected.

    Args:
        observed_confidence: "high", "medium", or "low"
        expected_confidence: "high", "medium", or "low"

    Returns:
        The lower of the two confidence levels.
    """
    ordering = {"high": 3, "medium": 2, "low": 1}
    obs_level = ordering.get(observed_confidence, 1)
    exp_level = ordering.get(expected_confidence, 1)
    min_level = min(obs_level, exp_level)

    reverse = {3: "high", 2: "medium", 1: "low"}
    return reverse[min_level]
```

#### 7.2 Observed Confidence Rules

| Condition | Confidence |
|-----------|------------|
| Value sourced from a single document with exact quote in evidence | `"high"` |
| Value computed from multiple corroborating facts | `"medium"` |
| Value estimated, inferred, or from a single low-confidence fact | `"low"` |

Implementation: the engine reads `CompanyProfile.{field}.confidence` for profile-based metrics. For fact-based metrics (security spend, outsourcing), the engine uses the maximum `confidence_score` among contributing facts, mapped to the string scale:
- `confidence_score >= 0.7` -> `"high"`
- `confidence_score >= 0.4` -> `"medium"`
- `confidence_score < 0.4` -> `"low"`

#### 7.3 Expected Confidence Rules

| Condition | Confidence |
|-----------|------------|
| Benchmark from named source (Gartner, HIMSS, Deloitte, etc.) with exact industry match | `"high"` |
| Benchmark from named source but using general/cross-industry fallback | `"medium"` |
| Benchmark from "Internal rule of thumb" | `"medium"` |
| No benchmark available (expected is None) | N/A (metric gets `"no_benchmark"` variance) |

Implementation: the engine checks `BenchmarkData.source`. If it contains `"Internal rule of thumb"`, confidence is `"medium"`. If `BenchmarkData.industry == "general"` and the company's actual industry is different, confidence is `"medium"`. Otherwise confidence is `"high"`.

#### 7.4 Overall Report Confidence

The report's `overall_confidence` is the **mode** (most frequent value) across all eligible metrics' confidence levels. Ties are broken toward lower confidence. If no metrics are eligible, overall confidence is `"low"`.

```python
def compute_overall_confidence(metrics: List[MetricComparison]) -> str:
    """Compute overall confidence as mode of eligible metric confidences."""
    eligible = [m for m in metrics if m.eligible]
    if not eligible:
        return "low"

    counts = {"high": 0, "medium": 0, "low": 0}
    for m in eligible:
        counts[m.confidence] = counts.get(m.confidence, 0) + 1

    # Return mode, breaking ties toward lower confidence
    max_count = max(counts.values())
    for level in ["low", "medium", "high"]:  # Check from low to high
        if counts[level] == max_count:
            return level

    return "low"
```

---

### 8. Engine Entry Point

```python
def generate_benchmark_report(
    company_profile,         # CompanyProfile (Spec 01)
    industry_classification, # IndustryClassification (Spec 02)
    industry_template,       # IndustryTemplate (Spec 03)
    fact_store,              # FactStore
    inventory_store,         # InventoryStore
    org_data_store,          # OrganizationDataStore
    deal_lens: Optional[str] = None,
    entity: str = "target",
) -> BenchmarkReport:
    """
    Generate a complete benchmark comparison report.

    This is the single entry point for the Benchmark Comparison Engine.
    It is stateless, deterministic, and makes no LLM or network calls.

    Args:
        company_profile: CompanyProfile with ProfileFields for revenue,
                        employee_count, it_headcount, it_budget, size_tier
        industry_classification: IndustryClassification with primary_industry,
                                sub_industry, confidence
        industry_template: IndustryTemplate with expected_systems,
                          expected_metrics, expected_organization,
                          deal_lens_considerations
        fact_store: FactStore with extracted facts
        inventory_store: InventoryStore with application/infrastructure items
        org_data_store: OrganizationDataStore with staff_members and
                       msp_relationships
        deal_lens: Optional deal type override
        entity: "target" or "buyer"

    Returns:
        BenchmarkReport with all comparisons computed.
    """

    # 1. Resolve industry and size for benchmark lookups
    industry = _resolve_industry(industry_classification)
    size_tier = _resolve_size_tier(company_profile)

    # 2. Compute metric comparisons
    metric_comparisons = []
    for metric_def in METRIC_REGISTRY:
        comparison = _compute_single_metric(
            metric_def=metric_def,
            company_profile=company_profile,
            industry=industry,
            size_tier=size_tier,
            industry_template=industry_template,
            fact_store=fact_store,
            inventory_store=inventory_store,
            org_data_store=org_data_store,
            entity=entity,
        )
        metric_comparisons.append(comparison)

    # 3. Compute technology stack comparisons
    system_comparisons = []
    if industry_template and hasattr(industry_template, "expected_systems"):
        for criticality_level in ["critical", "common", "general"]:
            systems = getattr(industry_template.expected_systems, criticality_level, [])
            if not systems:
                continue
            for expected_system in systems:
                comparison = match_expected_system(
                    expected_system=expected_system,
                    inventory_store=inventory_store,
                    fact_store=fact_store,
                    entity=entity,
                )
                system_comparisons.append(comparison)

    # 4. Compute staffing comparisons
    staffing_comparisons = []
    if industry_template and hasattr(industry_template, "expected_organization"):
        staffing_comparisons = compute_staffing_comparisons(
            expected_organization=industry_template.expected_organization,
            org_data_store=org_data_store,
            entity=entity,
        )

    # 5. Compute summary statistics
    eligible_count = sum(1 for m in metric_comparisons if m.eligible)
    total_count = len(metric_comparisons)
    overall_confidence = compute_overall_confidence(metric_comparisons)

    # 6. Resolve deal lens considerations
    effective_deal_lens = deal_lens or _infer_deal_lens(company_profile)
    deal_lens_considerations = []
    if effective_deal_lens and industry_template:
        all_considerations = getattr(industry_template, "deal_lens_considerations", {})
        if isinstance(all_considerations, dict):
            deal_lens_considerations = all_considerations.get(effective_deal_lens, [])
        elif isinstance(all_considerations, list):
            deal_lens_considerations = all_considerations

    # 7. Build report
    return BenchmarkReport(
        company_name=_get_company_name(company_profile),
        company_profile_summary=_serialize_profile_summary(company_profile),
        industry_classification={
            "primary_industry": getattr(industry_classification, "primary_industry", "unknown"),
            "sub_industry": getattr(industry_classification, "sub_industry", None),
            "confidence": getattr(industry_classification, "confidence", "low"),
        },
        template_used=getattr(industry_template, "template_id", "unknown"),
        metric_comparisons=metric_comparisons,
        system_comparisons=system_comparisons,
        staffing_comparisons=staffing_comparisons,
        eligible_metric_count=eligible_count,
        total_metric_count=total_count,
        overall_confidence=overall_confidence,
        deal_lens=effective_deal_lens,
        deal_lens_considerations=deal_lens_considerations,
    )
```

#### 8.1 Helper Functions

```python
def _resolve_industry(industry_classification) -> str:
    """
    Map IndustryClassification.primary_industry to a BenchmarkLibrary
    industry key.
    """
    INDUSTRY_MAP = {
        "insurance": "financial_services",
        "banking": "financial_services",
        "financial_services": "financial_services",
        "fintech": "financial_services",
        "healthcare": "healthcare",
        "health_tech": "healthcare",
        "pharma": "healthcare",
        "software": "software",
        "saas": "software",
        "technology": "software",
        "manufacturing": "manufacturing",
        "industrial": "manufacturing",
        "retail": "retail",
        "ecommerce": "retail",
        "consumer": "retail",
    }
    primary = getattr(industry_classification, "primary_industry", "general")
    return INDUSTRY_MAP.get(primary.lower(), "general")


def _resolve_size_tier(company_profile) -> str:
    """
    Map CompanyProfile.size_tier or revenue to a BenchmarkLibrary size key.
    """
    # Prefer explicit size_tier from profile
    if hasattr(company_profile, "size_tier") and company_profile.size_tier:
        tier = company_profile.size_tier
        if hasattr(tier, "value") and tier.value:
            return tier.value

    # Fall back to revenue-based derivation
    if hasattr(company_profile, "revenue") and company_profile.revenue:
        revenue = company_profile.revenue.value
        if revenue is not None:
            if revenue < 50_000_000:
                return "0-50M"
            elif revenue < 100_000_000:
                return "50-100M"
            elif revenue < 500_000_000:
                return "100-500M"
            else:
                return "500M+"

    return "50-100M"  # Default fallback for PE mid-market


def _infer_deal_lens(company_profile) -> Optional[str]:
    """
    Infer deal type from CompanyProfile.operating_model if available.
    """
    if not hasattr(company_profile, "operating_model") or not company_profile.operating_model:
        return None

    om = company_profile.operating_model
    value = om.value if hasattr(om, "value") else om
    if not value:
        return None

    value_lower = str(value).lower()
    if "carve" in value_lower or "divestiture" in value_lower:
        return "carve_out"
    if "platform" in value_lower or "add-on" in value_lower or "bolt-on" in value_lower:
        return "platform_add_on"
    if "turnaround" in value_lower or "distressed" in value_lower:
        return "turnaround"

    return "growth"  # Default for PE acquisitions


def _get_company_name(company_profile) -> str:
    """Extract company name from profile."""
    if hasattr(company_profile, "company_name"):
        name_field = company_profile.company_name
        if hasattr(name_field, "value"):
            return name_field.value or "Target Company"
        return str(name_field) if name_field else "Target Company"
    return "Target Company"


def _serialize_profile_summary(company_profile) -> Dict[str, Any]:
    """Serialize key profile fields for inclusion in the report."""
    summary = {}
    for field_name in ["revenue", "employee_count", "it_headcount", "it_budget", "size_tier", "operating_model"]:
        field = getattr(company_profile, field_name, None)
        if field is not None and hasattr(field, "value"):
            summary[field_name] = {
                "value": field.value,
                "confidence": getattr(field, "confidence", "low"),
                "provenance": getattr(field, "provenance", ""),
            }
        elif field is not None:
            summary[field_name] = {"value": field, "confidence": "low", "provenance": ""}
    return summary
```

---

### 9. Formatting Utilities

```python
def format_currency(value: float) -> str:
    """Format a dollar value for display."""
    if value is None:
        return "N/A"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def format_percentage(value: float) -> str:
    """Format a percentage value for display."""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def format_count(value: float, unit_label: str = "") -> str:
    """Format a count value for display."""
    if value is None:
        return "N/A"
    int_val = int(round(value))
    if unit_label:
        return f"{int_val} {unit_label}"
    return str(int_val)


def format_ratio(value: float, suffix: str = "per 100") -> str:
    """Format a ratio value for display."""
    if value is None:
        return "N/A"
    return f"{value:.1f} {suffix}"
```

---

## Benefits

1. **Eligibility rules prevent misleading metrics.** This is the number one risk in automated benchmarking -- producing a ratio from incomplete data that a deal team takes at face value. Every metric must pass explicit gates before it is computed.

2. **Expected / Observed / Variance structure is clear and auditable.** Each row in the report shows exactly what the industry says, what the data room says, and what the gap implies. Reviewers can challenge any number by following the provenance chain.

3. **Technology stack comparison auto-identifies VDR gaps.** By comparing expected systems from the industry template against the application inventory, the engine surfaces both confirmed coverage and documentation gaps without requiring manual checklist work.

4. **Staffing comparison quantifies organizational risk.** By matching role categories against expected headcounts, the engine flags understaffing and overstaffing patterns that have direct cost and operational implications for the deal.

5. **Fully deterministic -- no LLM calls.** The engine produces identical output on repeated runs. There is no variance between runs, no temperature setting, no prompt sensitivity. This makes the output trustworthy for inclusion in formal deliverables.

6. **Sub-second execution.** Pure computation with no API calls means the benchmark report can be regenerated instantly as new data is loaded or profiles are updated.

7. **Provenance chain enables accountability.** Every number links back to specific source documents and fact IDs. A reviewer can trace any metric from the report summary back to the exact page of the exact document in the data room.

---

## Expectations

### Performance

- Engine runs in **< 2 seconds** on any standard hardware. This is pure in-memory computation with no API calls, no database queries, and no file I/O during execution.
- The engine should handle up to 50 metric definitions, 100 expected systems, and 30 staffing categories without degradation.

### Data Coverage

- A typical deal with **5+ documents** in the data room should yield at least **2 eligible metrics** (usually `total_it_spend` and `total_it_headcount` at minimum, since IT budgets and org charts are commonly provided).
- A well-documented deal with budget, revenue, org chart, and application list should yield **5-6 eligible metrics**.

### Ineligibility Messaging

- Every ineligible metric must include a **specific** explanation of what is missing. Generic messages like "insufficient data" are not acceptable.
- The `failure_message` should name the specific missing data element (e.g., "Revenue" or "IT budget") and ideally suggest what type of document would contain it.

### Technology Stack Comparison

- All `"critical"` expected systems from the industry template must be included in the comparison.
- The `not_found` status must always include the three-part disclaimer (outsourced / different name / not in documentation).

### Staffing Comparison

- All role categories present in `IndustryTemplate.expected_organization` must be compared.
- MSP coverage must be noted for categories where MSPs provide relevant services.

### Determinism

- Three sequential runs of `generate_benchmark_report()` with identical inputs must produce identical `BenchmarkReport` outputs (byte-for-byte identical when serialized, excluding `generated_at` timestamp).

---

## Risks & Mitigations

### Risk 1: All Metrics Ineligible (Very Sparse Data Room)

**Likelihood:** Medium (common in early-stage diligence or small deals with minimal VDR)

**Impact:** The benchmark report appears empty or unhelpful, reducing user trust.

**Mitigation:**
- Technology stack and staffing comparisons still run against inventory and org data even when all quantitative metrics are ineligible.
- The report includes a **"Metrics Awaiting Data"** section that lists ineligible metrics with their specific data requirements. This transforms the gap from a blank page into a structured data request.
- The UI (Spec 05) renders ineligible metrics in a greyed-out state with actionable text, not hidden entirely.

### Risk 2: Observed Values Are Wrong Due to Extraction Errors

**Likelihood:** Medium (extraction from PDFs and unstructured documents is inherently noisy)

**Impact:** Misleading variance classifications that could drive incorrect deal conclusions.

**Mitigation:**
- Every observation links to source facts with `fact_id` references. A reviewer can click through to the exact evidence quote.
- The confidence field reflects extraction quality. Low-confidence observations produce low-confidence metrics, signaling that the number should be verified.
- The `computation_notes` field in provenance shows the exact formula used, making it easy to spot errors (e.g., wrong order of magnitude).

### Risk 3: Industry Template Metrics Don't Apply (Unusual Company)

**Likelihood:** Low (templates are selected based on industry classification, but edge cases exist -- e.g., a tech-enabled insurance company that looks more like software)

**Impact:** Expected ranges are wrong, producing misleading variance categories.

**Mitigation:**
- The report includes the template ID and industry classification, so reviewers know which benchmarks were applied.
- When the industry classification confidence is below `"high"`, all expected ranges receive `"medium"` confidence at most, and the implication text includes "based on {industry} industry benchmarks; actual expectations may differ for this company's specific profile."
- The engine falls back to `"general"` industry benchmarks when industry-specific data is unavailable, and notes this in the expected source provenance.

### Risk 4: MSP FTE Equivalents Inflate Headcount Metrics

**Likelihood:** Medium (companies with heavy outsourcing may have significant MSP FTE equivalents that distort ratios)

**Impact:** IT staff ratio and headcount metrics appear higher than the internal team actually is.

**Mitigation:**
- The primary headcount metric uses **internal FTE only** (not including MSP equivalents).
- MSP FTE equivalents are shown separately in provenance `computation_notes`.
- The `total_it_headcount` metric format explicitly separates: `"15 FTE (+4.0 MSP FTE)"`.
- Staffing comparisons include `msp_coverage_note` so reviewers can see where outsourcing covers expected roles.

### Risk 5: Benchmark Data Becomes Stale

**Likelihood:** Low in the short term (benchmarks are sourced from 2024 reports), high over 2+ years.

**Impact:** Expected ranges drift from current reality, especially in fast-moving sectors.

**Mitigation:**
- Every benchmark includes a `year` field and the `expected_source` provenance always includes the publication year.
- The engine can be configured to flag benchmarks older than N years (default: 3) with a provenance warning.
- Benchmark data is centralized in `tools_v2/benchmark_library.py`, making annual updates a single-file change.

### Risk 6: Division by Zero or Invalid Arithmetic

**Likelihood:** Low (eligibility checks prevent most cases)

**Impact:** Runtime error or infinite/NaN values in the report.

**Mitigation:**
- All division operations check for zero denominators before computing.
- Eligibility checks ensure required values are non-None before computation.
- The engine wraps each metric computation in a try/except that catches `ZeroDivisionError`, `TypeError`, and `ValueError`, marking the metric as ineligible with reason `"Computation error: {error_message}"`.

---

## Results Criteria

### Test 1: Full-Data Insurance Company

**Setup:** CompanyProfile with `revenue=82M`, `employee_count=350`, `it_headcount=15`, `it_budget=4.2M`, `size_tier="50-100M"`. IndustryClassification `primary_industry="insurance"`. InventoryStore with 42 applications. OrganizationDataStore with 15 staff members and 2 MSP relationships.

**Expected Result:**
- All 6 core metrics (`it_pct_revenue`, `it_staff_per_100`, `app_count_per_100`, `it_cost_per_employee`, `total_it_spend`, `total_it_headcount`) are eligible.
- `it_pct_revenue` observed = 5.12%, compared against financial_services 50-100M benchmark (5.0%-10.0%).
- `it_cost_per_employee` observed = $12,000, compared against financial_services 50-100M benchmark ($15K-$30K).
- Variance classifications are correct for each metric.
- Technology stack comparison runs against all critical insurance systems.
- Staffing comparison shows role-by-role counts.

### Test 2: Partial Data (No Revenue)

**Setup:** CompanyProfile with `employee_count=200`, `it_headcount=8`, `it_budget=1.5M`, `revenue=None`.

**Expected Result:**
- `it_pct_revenue` is **ineligible** with reason mentioning missing revenue.
- `total_it_spend` is eligible (observed = $1.5M) but expected range is `None` (no revenue to compute expected), so `variance_category = "no_benchmark"`.
- `it_staff_per_100`, `it_cost_per_employee`, `app_count_per_100` computed where inputs exist.
- At least 3 metrics are eligible.

### Test 3: Empty Data (No Organization Data)

**Setup:** CompanyProfile with all fields None. Empty FactStore. Empty InventoryStore. None OrganizationDataStore.

**Expected Result:**
- All metrics are **ineligible** with clear messages for each.
- `eligible_metric_count = 0`.
- Technology stack comparison runs against inventory (produces all `not_found` with disclaimers).
- Staffing comparison produces empty list (no org data store).
- Report still generates without error.
- `overall_confidence = "low"`.

### Test 4: Technology Stack Match (Insurance Template)

**Setup:** Insurance industry template with critical system `policy_administration` (common vendors: Duck Creek, Guidewire). InventoryStore with application named "Duck Creek Policy v4.2" from vendor "Duck Creek Technologies".

**Expected Result:**
- `SystemComparison` for `policy_administration` has `status = "found"`, `observed_system = "Duck Creek Policy v4.2"`, `observed_vendor = "Duck Creek Technologies"`.

### Test 5: Technology Stack Missing System

**Setup:** Insurance template with critical system `actuarial` (common vendors: Willis Towers Watson, Milliman). InventoryStore with no actuarial tools.

**Expected Result:**
- `SystemComparison` for `actuarial` has `status = "not_found"`.
- `notes` contains the three-part disclaimer about outsourcing, different name, or missing documentation.

### Test 6: Staffing Within Range

**Setup:** Industry template expects infrastructure staff "2-3". OrganizationDataStore has 2 staff with `role_category = RoleCategory.INFRASTRUCTURE`.

**Expected Result:**
- `StaffingComparison` for `infrastructure` has `observed_count = 2`, `variance = "within_range"`.

### Test 7: Staffing Understaffed

**Setup:** Template expects security staff "1-2". OrganizationDataStore has 0 security staff.

**Expected Result:**
- `StaffingComparison` for `security` has `observed_count = 0`, `variance = "understaffed"`.
- Notes include: "No staff identified for this category."

### Test 8: Determinism

**Setup:** Any valid inputs.

**Expected Result:**
- Three sequential calls to `generate_benchmark_report()` with identical arguments produce `BenchmarkReport` objects that are identical when serialized to JSON (after stripping `generated_at` timestamps).

### Test 9: MSP Coverage in Staffing

**Setup:** Template expects infrastructure "2-3". OrganizationDataStore has 1 internal infra staff plus MSP "Acme IT" with service "Infrastructure Management" at 2.0 FTE equivalent.

**Expected Result:**
- `StaffingComparison` for `infrastructure` has `observed_count = 1`, `variance = "understaffed"`.
- `msp_coverage_note` contains: "MSP 'Acme IT' provides 2.0 FTE equivalent for Infrastructure Management."

### Test 10: Confidence Propagation

**Setup:** CompanyProfile with `it_budget.confidence = "high"`, `revenue.confidence = "low"`. Benchmark from Gartner (industry-specific).

**Expected Result:**
- `it_pct_revenue` metric is **ineligible** because `revenue.confidence = "low"` and the metric requires `min_confidence = "medium"`.
- Ineligibility reason mentions the confidence gap.

---

## Appendix A: Metric ID to BenchmarkLibrary Key Mapping

| Metric ID | BenchmarkLibrary Key | Unit |
|-----------|---------------------|------|
| `it_pct_revenue` | `it_pct_revenue` | % |
| `it_staff_per_100_employees` | `it_staff_ratio` | ratio |
| `app_count_per_100_employees` | `app_count_ratio` | count |
| `it_cost_per_employee` | `cost_per_employee` | USD |
| `total_it_spend` | `it_pct_revenue` (computed) | USD |
| `total_it_headcount` | N/A (from template) | count |
| `outsourcing_pct` | `outsourcing_pct` | % |
| `security_pct_it` | `security_pct_it` | % |

## Appendix B: Industry Code Mapping

| IndustryClassification Value | BenchmarkLibrary Industry |
|------------------------------|--------------------------|
| `insurance`, `banking`, `financial_services`, `fintech` | `financial_services` |
| `healthcare`, `health_tech`, `pharma` | `healthcare` |
| `software`, `saas`, `technology` | `software` |
| `manufacturing`, `industrial` | `manufacturing` |
| `retail`, `ecommerce`, `consumer` | `retail` |
| Any other value | `general` |

## Appendix C: File Inventory

| File | Status | Purpose |
|------|--------|---------|
| `models/benchmark_comparison.py` | **New** | Data models: MetricComparison, SystemComparison, StaffingComparison, BenchmarkReport, MetricProvenance |
| `services/benchmark_engine.py` | **New** | Engine: generate_benchmark_report(), eligibility checks, variance classification, matching algorithms |
| `tools_v2/benchmark_library.py` | Existing (read-only) | BenchmarkData entries and get_benchmark() lookup |
| `stores/fact_store.py` | Existing (read-only) | Fact extraction source for observed values |
| `stores/inventory_store.py` | Existing (read-only) | Application counts and system matching |
| `models/organization_stores.py` | Existing (read-only) | OrganizationDataStore for staffing data |
| `services/organization_bridge.py` | Existing (read-only) | Builds OrganizationDataStore from facts |
