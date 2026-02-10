# Spec 01: Company Profile Extraction

**Feature Area:** Business Context
**Status:** Draft
**Dependencies:** Existing FactStore, OrganizationBridge, session DealContext
**Consumed by:** Spec 02 (Industry Classification), Spec 04 (Benchmark Engine), Spec 05 (UI)

---

## Overview

The IT Due Diligence Agent currently scatters company profile data across four separate, incompatible dataclasses:

1. **`tools_v2/consistency_engine.py` `CompanyProfile`** -- fields: `employee_count`, `industry`, `geography`, `it_maturity`, `annual_revenue`. Hard-coded mid-market defaults. Used for cost multiplier calculations.
2. **`tools_v2/pe_report_schemas.py` `DealContext`** -- fields: `target_name`, `deal_type`, `target_revenue`, `target_employees`, `target_industry`, `target_it_budget`, `target_it_headcount`, `buyer_name`, `buyer_revenue`, `buyer_employees`, `buyer_industry`, `buyer_it_budget`, `deal_value`, `expected_close_date`. Used for PE report generation.
3. **`tools_v2/session.py` `DealContext`** -- fields: `target_name`, `buyer_name`, `deal_type`, `industry`, `sub_industry`, `secondary_industries`, `industry_confirmed`, `deal_size`, `integration_approach`, `timeline_pressure`, `custom_focus_areas`, `notes`. Used during interactive CLI sessions.
4. **`prompts/shared/strategic_cost_assessment.py` `CompanyProfile`** -- fields: `revenue`, `employees`, `it_headcount`, `app_count`, `dc_count`, `cloud_percentage`, `outsourcing_percentage`, `erp_count`. Used for strategic cost estimation.

None of these carry provenance. None explain where their values came from. When an analyst sees "450 employees" in the final report, there is no way to trace that number back to the specific document and paragraph it was extracted from.

This spec introduces a **canonical `CompanyProfile`** that:

- Auto-extracts every field from facts already collected during the discovery phase
- Wraps every field in a `ProfileField` that records confidence, provenance, source fact IDs, and source documents
- Makes zero LLM calls -- pure deterministic data assembly from `FactStore` contents
- Replaces all four scattered dataclasses as the single source of truth
- Degrades gracefully when data is missing, always labeling gaps explicitly rather than silently defaulting

---

## Architecture

### New Files

| File | Purpose |
|------|---------|
| `stores/company_profile.py` | Canonical `ProfileField` and `CompanyProfile` dataclasses |
| `services/profile_extractor.py` | `ProfileExtractor` service that reads `FactStore` and produces `CompanyProfile` |

### Data Flow

```
                    +------------------+
                    |  Discovery Phase |
                    |  (LLM agents)    |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    FactStore     |  <- facts with domain, category, details, evidence
                    |  (fact_store.py) |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
    +-------------------+         +---------------------+
    | OrganizationBridge|         | ProfileExtractor    |  <- NEW (this spec)
    | (org_bridge.py)   |         | (profile_extractor) |
    +--------+----------+         +----------+----------+
             |                               |
             |  staff_members, MSPs          |  CompanyProfile with ProfileFields
             +---------------+---------------+
                             |
                             v
                    +------------------+
                    |  CompanyProfile   |  <- NEW canonical model (this spec)
                    | (company_profile) |
                    +--------+---------+
                             |
              +--------------+--------------+--------------+
              |              |              |              |
              v              v              v              v
        Spec 02:       Spec 04:       Spec 05:    consistency_engine
        Industry       Benchmark      UI Views    (updated to accept
        Classifier     Engine                      new profile)
```

### Integration Boundaries

- **Input:** `FactStore` instance (populated by discovery agents), `DealContext` from `tools_v2/session.py` (for user-specified fields like `target_name`, `buyer_name`, `deal_type`)
- **Output:** `CompanyProfile` instance with all fields wrapped in `ProfileField`
- **No LLM calls.** The `ProfileExtractor` is a pure function: `(FactStore, DealContext) -> CompanyProfile`
- **Timing:** Profile extraction runs AFTER discovery completes, BEFORE the reasoning phase begins. It is invoked once per deal run. If facts change (e.g., incremental document upload), it can be re-invoked to produce an updated profile.

---

## Specification

### 1. ProfileField Wrapper

Every extracted value on the `CompanyProfile` is wrapped in a `ProfileField` to carry provenance metadata. Defined in `stores/company_profile.py`:

```python
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from datetime import datetime


@dataclass
class ProfileField:
    """
    Wrapper for a single company profile value with full provenance.

    Every field on CompanyProfile is a ProfileField so that consumers
    can inspect not just the value but how it was determined.
    """
    value: Any                              # The extracted/computed value
    confidence: str                         # "high", "medium", "low"
    provenance: str                         # "document_sourced", "inferred", "user_specified", "default"
    source_fact_ids: List[str] = field(     # Fact IDs (e.g., F-TGT-ORG-003) that contributed
        default_factory=list
    )
    source_documents: List[str] = field(    # Document filenames (e.g., "IT Budget 2024.xlsx")
        default_factory=list
    )
    inference_rationale: str = ""           # If provenance is "inferred", explains the logic
                                            # If provenance is "default", states "No data found; using default"
    conflicts: List[Dict[str, Any]] = field(  # If multiple contradictory values were found
        default_factory=list                   # Each entry: {"value": X, "fact_id": "F-...", "source": "doc.pdf"}
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON export."""
        return {
            "value": self.value,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "source_fact_ids": self.source_fact_ids,
            "source_documents": self.source_documents,
            "inference_rationale": self.inference_rationale,
            "conflicts": self.conflicts,
        }

    @classmethod
    def not_found(cls, field_label: str) -> "ProfileField":
        """Factory for a field where no data was found in the data room."""
        return cls(
            value=None,
            confidence="low",
            provenance="default",
            inference_rationale=f"{field_label} not found in data room documents",
        )

    @classmethod
    def user_specified(cls, value: Any) -> "ProfileField":
        """Factory for a field provided directly by the user via DealContext."""
        return cls(
            value=value,
            confidence="high",
            provenance="user_specified",
        )

    @classmethod
    def insufficient_data(cls, field_label: str) -> "ProfileField":
        """Factory for when no organization facts exist at all."""
        return cls(
            value=None,
            confidence="low",
            provenance="default",
            inference_rationale=f"Insufficient data - no organization facts available to determine {field_label}",
        )
```

#### Confidence Levels

| Level | Meaning | When Used |
|-------|---------|-----------|
| `"high"` | Value found explicitly in a document or provided by user | Document states "450 employees"; user entered company name in CLI |
| `"medium"` | Value derived from structured data but required interpretation | Headcount counted from org chart nodes; geography inferred from 2 data center locations |
| `"low"` | Value is a best guess, or data was not found | Revenue estimated from employee count; field not present in any document |

#### Provenance Types

| Provenance | Meaning |
|------------|---------|
| `"document_sourced"` | Value was extracted directly from a data room document, with evidence quote |
| `"inferred"` | Value was computed from other facts (e.g., operating_model from MSP count) |
| `"user_specified"` | Value was entered by the user in the CLI session (DealContext) |
| `"default"` | No data was found; field carries a default or None |

### 2. Canonical CompanyProfile Model

Defined in `stores/company_profile.py`:

```python
@dataclass
class CompanyProfile:
    """
    Canonical company profile extracted from FactStore.

    Single source of truth for all company-level attributes.
    Every field is a ProfileField with confidence + provenance.

    Replaces:
    - tools_v2/consistency_engine.py CompanyProfile
    - tools_v2/pe_report_schemas.py DealContext (target fields)
    - tools_v2/session.py DealContext (company-level fields)
    - prompts/shared/strategic_cost_assessment.py CompanyProfile
    """

    # --- Identity ---
    company_name: ProfileField           # str value - target company name
    deal_type: ProfileField              # str value - "acquisition", "carveout", "bolt_on"

    # --- Financial ---
    revenue: ProfileField                # Optional[float] value - annual revenue in USD
    revenue_range: ProfileField          # str value - "small", "midmarket", "large"

    # --- Headcount ---
    employee_count: ProfileField         # Optional[int] value - total company employees
    it_headcount: ProfileField           # Optional[int] value - IT staff (FTE)
    it_headcount_with_contractors: ProfileField  # Optional[int] value - IT FTE + contractor/MSP equivalents

    # --- Budget ---
    it_budget: ProfileField              # Optional[float] value - annual IT spend in USD

    # --- Industry (placeholder -- Spec 02 fills this in) ---
    industry: ProfileField               # str value - industry key (e.g., "healthcare")

    # --- Geography ---
    geography: ProfileField              # str value - "single_office", "multi_office_domestic", "international"

    # --- Operating Model ---
    operating_model: ProfileField        # str value - "in_house", "hybrid", "heavily_outsourced"

    # --- Computed ---
    size_tier: str                       # "small", "midmarket", "large", "unknown" (not a ProfileField -- deterministic)

    # --- Metadata ---
    extracted_at: str = ""               # ISO timestamp of extraction
    fact_store_version: str = ""         # FactStore metadata version used
    total_facts_analyzed: int = 0        # How many facts were scanned
    extraction_warnings: List[str] = field(default_factory=list)  # Any issues during extraction

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire profile for JSON export or API response."""
        return {
            "company_name": self.company_name.to_dict(),
            "deal_type": self.deal_type.to_dict(),
            "revenue": self.revenue.to_dict(),
            "revenue_range": self.revenue_range.to_dict(),
            "employee_count": self.employee_count.to_dict(),
            "it_headcount": self.it_headcount.to_dict(),
            "it_headcount_with_contractors": self.it_headcount_with_contractors.to_dict(),
            "it_budget": self.it_budget.to_dict(),
            "industry": self.industry.to_dict(),
            "geography": self.geography.to_dict(),
            "operating_model": self.operating_model.to_dict(),
            "size_tier": self.size_tier,
            "extracted_at": self.extracted_at,
            "fact_store_version": self.fact_store_version,
            "total_facts_analyzed": self.total_facts_analyzed,
            "extraction_warnings": self.extraction_warnings,
        }

    # ---- Backwards-compatible properties for existing consumers ----

    @property
    def employee_count_value(self) -> int:
        """Backwards-compatible: returns employee count or 300 (mid-market default)."""
        return self.employee_count.value if self.employee_count.value is not None else 300

    @property
    def industry_value(self) -> str:
        """Backwards-compatible: returns industry or 'technology' default."""
        return self.industry.value if self.industry.value else "technology"

    @property
    def geography_value(self) -> str:
        """Backwards-compatible: returns geography or 'single_country' default."""
        return self.geography.value if self.geography.value else "single_country"

    @property
    def annual_revenue_value(self) -> float:
        """Backwards-compatible: returns revenue or $50M default."""
        return self.revenue.value if self.revenue.value is not None else 50_000_000

    @property
    def it_budget_value(self) -> float:
        """Backwards-compatible: returns IT budget or 0."""
        return self.it_budget.value if self.it_budget.value is not None else 0

    @property
    def it_headcount_value(self) -> int:
        """Backwards-compatible: returns IT headcount or 0."""
        return self.it_headcount.value if self.it_headcount.value is not None else 0
```

### 3. ProfileExtractor Service

Defined in `services/profile_extractor.py`. This is the core extraction logic.

```python
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from stores.fact_store import FactStore, Fact
from stores.company_profile import CompanyProfile, ProfileField

logger = logging.getLogger(__name__)


class ProfileExtractor:
    """
    Extracts a canonical CompanyProfile from FactStore contents.

    Pure deterministic function: same FactStore -> same CompanyProfile.
    Makes zero LLM calls. Runs in <1 second.
    """

    def __init__(self, fact_store: FactStore, deal_context: Any = None):
        """
        Args:
            fact_store: Populated FactStore from discovery phase.
            deal_context: Optional DealContext from tools_v2/session.py
                          for user-specified fields (target_name, industry, etc.)
        """
        self.fact_store = fact_store
        self.deal_context = deal_context
        self._warnings: List[str] = []

    def extract(self) -> CompanyProfile:
        """
        Run extraction and return a CompanyProfile.

        Returns:
            CompanyProfile with all fields populated (or marked as not found).
        """
        ...  # Full implementation specified in extraction rules below
```

### 4. Extraction Rules

Each field has a specific extraction procedure. The `ProfileExtractor.extract()` method calls one private method per field, then assembles the `CompanyProfile`.

#### 4.1 company_name

**Source:** `DealContext.target_name` (user-provided during session setup)

**Procedure:**
1. If `deal_context` is not None and `deal_context.target_name` is a non-empty string, use it.
2. Confidence: `"high"`. Provenance: `"user_specified"`.
3. If `deal_context` is None or `target_name` is empty, search all facts for the most common `entity == "target"` value in fact details with keys `"company_name"`, `"target_name"`, `"organization_name"`. Take the most frequent non-empty value. Confidence: `"medium"`, provenance: `"inferred"`, rationale: "Extracted from most frequent company name mention across facts".
4. If still not found, return `ProfileField.not_found("Company name")`.

```python
def _extract_company_name(self) -> ProfileField:
    if self.deal_context and getattr(self.deal_context, 'target_name', None):
        return ProfileField.user_specified(self.deal_context.target_name)

    # Fallback: scan facts for company name mentions
    name_keys = {"company_name", "target_name", "organization_name"}
    name_counts: Dict[str, List[str]] = {}  # name -> [fact_ids]
    for fact in self.fact_store.facts:
        if fact.entity != "target":
            continue
        for key in name_keys:
            val = (fact.details or {}).get(key, "")
            if val and isinstance(val, str) and len(val.strip()) > 1:
                name = val.strip()
                name_counts.setdefault(name, []).append(fact.fact_id)

    if name_counts:
        best_name = max(name_counts, key=lambda n: len(name_counts[n]))
        return ProfileField(
            value=best_name,
            confidence="medium",
            provenance="inferred",
            source_fact_ids=name_counts[best_name][:5],
            source_documents=list({
                f.source_document for f in self.fact_store.facts
                if f.fact_id in name_counts[best_name] and f.source_document
            }),
            inference_rationale="Extracted from most frequent company name mention across target facts",
        )

    return ProfileField.not_found("Company name")
```

#### 4.2 revenue

**Source:** Organization-domain facts with category `"budget"`. Also scan all facts for details keys related to revenue.

**Procedure:**
1. Get all facts where `domain == "organization"` and `category == "budget"`.
2. Search each fact's `details` dict for keys: `"annual_revenue"`, `"revenue"`, `"total_revenue"`, `"company_revenue"`.
3. Parse the value as a float (handling string formats like `"$50M"`, `"50,000,000"`, `"50 million"`). Use a helper `_parse_dollar_amount(value) -> Optional[float]`.
4. If multiple facts provide revenue values:
   - If values agree (within 10% tolerance), take the value from the most recent fact (`created_at`). Confidence: `"high"`.
   - If values conflict (>10% difference), take the most recent, record all alternatives in `conflicts`. Confidence: `"medium"`. Rationale: "Multiple revenue figures found; using most recent. Conflict noted."
5. If found in a document, provenance: `"document_sourced"`. Populate `source_fact_ids` and `source_documents`.
6. If not found in any fact, return `ProfileField.not_found("Revenue")`.

**Dollar amount parser** (private helper on `ProfileExtractor`):

```python
def _parse_dollar_amount(self, value: Any) -> Optional[float]:
    """
    Parse dollar amounts from various formats.

    Handles:
    - 50000000, 50_000_000 (numeric)
    - "$50M", "$50 million", "$50,000,000" (string)
    - "50M", "50 million", "50mm" (no dollar sign)
    - "50B", "50 billion" (billions)
    - "50K", "50 thousand" (thousands)
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    text = value.strip().replace("$", "").replace(",", "").replace("_", "").lower()
    if not text:
        return None

    multipliers = {
        "k": 1_000, "thousand": 1_000,
        "m": 1_000_000, "mm": 1_000_000, "million": 1_000_000, "mil": 1_000_000,
        "b": 1_000_000_000, "bn": 1_000_000_000, "billion": 1_000_000_000,
    }

    for suffix, mult in multipliers.items():
        if text.endswith(suffix):
            num_part = text[: -len(suffix)].strip()
            try:
                return float(num_part) * mult
            except ValueError:
                continue

    try:
        return float(text)
    except ValueError:
        return None
```

#### 4.3 revenue_range

**Source:** Computed from `revenue` field.

**Procedure:**
1. If `revenue.value` is not None:
   - `< 50_000_000` -> `"small"`
   - `>= 50_000_000` and `< 500_000_000` -> `"midmarket"`
   - `>= 500_000_000` -> `"large"`
   - Confidence and provenance inherit from `revenue`.
2. If `revenue.value` is None but `employee_count.value` is known:
   - `< 100` -> `"small"`
   - `>= 100` and `< 1000` -> `"midmarket"`
   - `>= 1000` -> `"large"`
   - Confidence: one level below employee_count confidence (high->medium, medium->low, low->low). Provenance: `"inferred"`. Rationale: "Revenue not available; range estimated from employee count."
3. If neither is known, value is `"unknown"`, confidence `"low"`, provenance `"default"`.

```python
def _compute_revenue_range(self, revenue: ProfileField, employee_count: ProfileField) -> ProfileField:
    if revenue.value is not None:
        amount = revenue.value
        if amount < 50_000_000:
            tier = "small"
        elif amount < 500_000_000:
            tier = "midmarket"
        else:
            tier = "large"
        return ProfileField(
            value=tier,
            confidence=revenue.confidence,
            provenance=revenue.provenance,
            source_fact_ids=list(revenue.source_fact_ids),
            source_documents=list(revenue.source_documents),
            inference_rationale=f"Derived from revenue ${amount:,.0f}",
        )

    if employee_count.value is not None:
        count = employee_count.value
        if count < 100:
            tier = "small"
        elif count < 1000:
            tier = "midmarket"
        else:
            tier = "large"
        downgraded = {"high": "medium", "medium": "low", "low": "low"}
        return ProfileField(
            value=tier,
            confidence=downgraded[employee_count.confidence],
            provenance="inferred",
            source_fact_ids=list(employee_count.source_fact_ids),
            source_documents=list(employee_count.source_documents),
            inference_rationale=f"Revenue not available; range estimated from {count} employees",
        )

    return ProfileField(
        value="unknown",
        confidence="low",
        provenance="default",
        inference_rationale="Neither revenue nor employee count available to determine revenue range",
    )
```

#### 4.4 employee_count

**Source:** Organization-domain facts. Search broadly across categories.

**Procedure:**
1. Get all facts where `domain == "organization"` and `entity == "target"`.
2. Search each fact's `details` dict for keys: `"total_employees"`, `"headcount"`, `"employee_count"`, `"fte_count"`, `"total_headcount"`, `"company_size"`, `"number_of_employees"`.
3. Parse values as integers (handling strings like `"~450"`, `"450 employees"`, `"approximately 500"`). Use helper `_parse_integer(value) -> Optional[int]`.
4. Also check `category == "budget"` facts for `"total_employees"` or `"total_headcount"` in details (these are often authoritative).
5. **Conflict resolution:** If multiple values found:
   - If all values within 15% of each other, take value from the most recent fact. Confidence: `"high"`.
   - If values conflict (>15% difference), take the value from the fact with the highest `confidence_score` (the existing 0.0-1.0 score on the `Fact` dataclass). If scores are equal, take the most recent. Record all alternatives in `conflicts`. Confidence: `"medium"`. Rationale: "Multiple headcount figures found; using value from highest-confidence fact. See conflicts."
6. If found directly in a document's details with an evidence quote, provenance: `"document_sourced"`.
7. If only an org chart-based count is available (i.e., no explicit headcount number, but organization bridge produced staff_members), use `len(staff_members)` from `organization_bridge.build_organization_from_facts()`. Confidence: `"medium"`, provenance: `"inferred"`, rationale: "Total headcount counted from org chart / census data extracted during discovery."
8. If not found, return `ProfileField.not_found("Total headcount")`.

**Integer parser** (private helper):

```python
def _parse_integer(self, value: Any) -> Optional[int]:
    """
    Parse integer from various formats.

    Handles:
    - 450 (numeric)
    - "450", "~450", "approximately 500", "450 employees"
    - "four hundred fifty" is NOT handled (too ambiguous)
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if not isinstance(value, str):
        return None

    import re
    text = value.strip().lower()
    text = text.replace(",", "").replace("~", "").replace("approximately", "").replace("about", "")
    text = text.replace("employees", "").replace("people", "").replace("staff", "").replace("fte", "")
    text = text.replace("headcount", "").strip()

    match = re.search(r'(\d+)', text)
    if match:
        return int(match.group(1))
    return None
```

#### 4.5 it_headcount

**Source:** Organization bridge output (`staff_members`) and organization budget facts.

**Procedure:**
1. **Primary: authoritative headcount from budget facts.**
   Get all facts where `domain == "organization"` and `category == "budget"`. Search for `details["total_it_headcount"]` or `details["it_headcount"]` or `details["it_staff_count"]`. If found, use it. Confidence: `"high"`, provenance: `"document_sourced"`.

2. **Secondary: count from organization bridge.**
   Call `build_organization_from_facts(fact_store, target_name, deal_id)` (imported from `services/organization_bridge.py`). From the returned `OrganizationDataStore`:
   - Count FTE staff: `sum(1 for s in store.staff_members if s.employment_type == EmploymentType.FTE)`
   - Confidence: `"high"` if the source facts included census/HR data (check if any source fact has category `"roles"` or `"central_it"`). Otherwise `"medium"`.
   - Provenance: `"inferred"`. Rationale: "IT headcount counted from {N} staff members extracted from org chart / census data."
   - `source_fact_ids`: collect fact_ids from all organization-domain facts that contributed to staff members (leadership, central_it, app_teams, roles, key_individuals categories).

3. **Tertiary: count from individual role facts.**
   If organization bridge returns no staff members, search all facts with `domain == "organization"` and `category in ("roles", "leadership", "central_it", "app_teams")`. Sum up details values for keys `"count"`, `"team_size"`, `"headcount"`. Confidence: `"low"`, provenance: `"inferred"`, rationale: "IT headcount summed from team size mentions in individual role facts."

4. If none of the above produces a value, return `ProfileField.not_found("IT headcount")`.

**Note:** The `it_headcount_with_contractors` field is computed separately:
- Take FTE headcount from above.
- Add contractor and MSP equivalent headcount from organization bridge: `sum(1 for s in store.staff_members if s.employment_type in (EmploymentType.CONTRACTOR, EmploymentType.MSP, EmploymentType.TEMP))`.
- Add MSP FTE equivalents from `MSPRelationship` objects if available.
- Provenance: `"inferred"`. Rationale: "IT headcount including {N} FTEs + {M} contractors/MSP equivalents."

#### 4.6 it_budget

**Source:** Organization budget facts, vendor cost facts.

**Procedure:**
1. Get all facts where `domain == "organization"` and `category == "budget"`.
2. Search details for keys: `"it_budget"`, `"technology_budget"`, `"total_it_spend"`, `"annual_it_spend"`, `"it_operating_budget"`.
3. Parse as dollar amount using `_parse_dollar_amount()`.
4. If found explicitly in a document:
   - Confidence: `"high"`. Provenance: `"document_sourced"`.
5. If not found but can be **inferred** from components:
   - Compute: `(it_headcount * avg_salary_by_category) + sum(known_vendor_costs)`
   - Average salary by category comes from `DEFAULT_SALARIES` in `services/organization_bridge.py` (already defined: Leadership $180K, Security $140K, Applications $120K, etc.)
   - Known vendor costs come from facts with `domain == "applications"` or `domain == "infrastructure"` where `details` contains `"annual_cost"`, `"license_cost"`, `"subscription_cost"`.
   - Confidence: `"low"`. Provenance: `"inferred"`. Rationale: "IT budget estimated from {N} staff at avg ${X}/year + ${Y} in identified vendor/license costs. Actual budget may differ significantly."
   - Add warning to `extraction_warnings`: "IT budget was estimated, not found in documents. Treat as directional only."
6. If neither direct nor inferred is possible, return `ProfileField.not_found("IT budget")`.

#### 4.7 industry

**Source:** User-specified in DealContext, or placeholder for Spec 02.

**Procedure:**
1. If `deal_context` is not None and `deal_context.industry` is a non-empty string:
   - If `deal_context.industry_confirmed == True`, confidence: `"high"`, provenance: `"user_specified"`.
   - If `deal_context.industry_confirmed == False`, confidence: `"medium"`, provenance: `"inferred"`, rationale: "Auto-detected industry, not yet confirmed by user."
2. If no deal_context industry, set value to `"unknown"`, confidence: `"low"`, provenance: `"default"`, rationale: "Industry not specified. Will be classified by Spec 02 Industry Classifier."
3. **This field is intentionally minimal.** Spec 02 (Industry Classification) will enhance it with sub-industry, secondary industries, and regulatory context. This spec only provides the placeholder so the field exists on CompanyProfile.

#### 4.8 geography

**Source:** Infrastructure location facts, organization facts with office/location mentions.

**Procedure:**
1. Collect location signals from multiple fact domains:

   a. **Infrastructure facts** (`domain == "infrastructure"`): search `details` for keys `"region"`, `"location"`, `"data_center_location"`, `"cloud_region"`, `"deployment_region"`. Extract location strings.

   b. **Organization facts** (`domain == "organization"`): search `details` for keys `"location"`, `"office_location"`, `"headquarters"`, `"hq_location"`. Also check `StaffMember.location` values from organization bridge output.

   c. **Network facts** (`domain == "network"`): search `details` for keys `"office_locations"`, `"site_locations"`, `"wan_sites"`.

2. Normalize collected locations to countries (use simple heuristic: if location contains a US state abbreviation or US city name, mark as "US"; if it contains a non-US country name, mark as that country; if it contains a cloud region like `"us-east-1"`, `"eu-west-1"`, mark accordingly).

3. Classification:
   - 0 or 1 distinct locations found, all in same country -> `"single_office"`
   - 2+ locations, all in same country -> `"multi_office_domestic"`
   - Locations in 2+ countries -> `"international"`

4. Confidence:
   - 3+ location facts from documents -> `"high"`, provenance: `"document_sourced"`
   - 1-2 location facts -> `"medium"`, provenance: `"document_sourced"`
   - 0 location facts but cloud regions suggest geography -> `"low"`, provenance: `"inferred"`, rationale: "Geography inferred from cloud deployment regions only."
   - No data at all -> `ProfileField.not_found("Geography")`

#### 4.9 operating_model

**Source:** MSP relationships from organization bridge, outsourcing facts.

**Procedure:**
1. Get MSP data from organization bridge output:
   - Call `build_organization_from_facts(fact_store)` (or reuse cached result from it_headcount extraction).
   - Count MSP relationships from the `OrganizationDataStore.msp_relationships` list.
   - Check dependency levels on each MSP (from `MSPRelationship.dependency_level`: `FULL`, `PARTIAL`, `SUPPLEMENTAL`).

2. Also search facts with `domain == "organization"` and `category == "outsourcing"` for additional signals. Check `details` for keys: `"dependency_level"`, `"outsourcing_scope"`, `"managed_by"`.

3. Classification:
   - **0 MSP relationships** and no outsourcing facts -> `"in_house"`
   - **1-2 MSP relationships**, all with `SUPPLEMENTAL` or `PARTIAL` dependency -> `"hybrid"`
   - **3+ MSP relationships** OR **any MSP with `FULL` dependency** -> `"heavily_outsourced"`

4. Confidence:
   - If based on explicit outsourcing/MSP facts with evidence -> `"high"`, provenance: `"document_sourced"`
   - If inferred from absence of MSP mentions (i.e., "in_house" because no outsourcing was found) -> `"medium"`, provenance: `"inferred"`, rationale: "No MSP or outsourcing relationships found in documents; assumed in-house."
   - If only partial data -> `"low"`, provenance: `"inferred"`, rationale: "Limited outsourcing data; operating model classification may be incomplete."

#### 4.10 size_tier

**Source:** Computed deterministically from `revenue` and `employee_count`. Not a `ProfileField` -- just a plain string, because it carries no independent provenance (it is a pure function of other fields).

**Procedure:**
```python
def _compute_size_tier(self, revenue: ProfileField, employee_count: ProfileField) -> str:
    # Revenue takes priority
    if revenue.value is not None:
        if revenue.value < 50_000_000:
            return "small"
        elif revenue.value < 500_000_000:
            return "midmarket"
        else:
            return "large"

    # Fall back to employee count
    if employee_count.value is not None:
        if employee_count.value < 100:
            return "small"
        elif employee_count.value < 1000:
            return "midmarket"
        else:
            return "large"

    return "unknown"
```

### 5. ProfileExtractor.extract() Assembly

The top-level `extract()` method calls each extraction method and assembles the result:

```python
def extract(self) -> CompanyProfile:
    self._warnings = []
    org_facts = [f for f in self.fact_store.facts if f.domain == "organization" and f.entity == "target"]

    # If no facts at all, return minimal profile
    if not self.fact_store.facts:
        self._warnings.append("FactStore is empty - no facts available for extraction")
        return self._build_empty_profile()

    # If no organization facts, extract what we can from other domains
    if not org_facts:
        self._warnings.append("No organization-domain facts found - profile will be limited")

    # Extract each field
    company_name = self._extract_company_name()
    deal_type = self._extract_deal_type()
    revenue = self._extract_revenue()
    employee_count = self._extract_employee_count()
    it_headcount = self._extract_it_headcount()
    it_headcount_with_contractors = self._extract_it_headcount_with_contractors()
    it_budget = self._extract_it_budget(it_headcount)
    industry = self._extract_industry()
    geography = self._extract_geography()
    operating_model = self._extract_operating_model()

    # Computed fields
    revenue_range = self._compute_revenue_range(revenue, employee_count)
    size_tier = self._compute_size_tier(revenue, employee_count)

    return CompanyProfile(
        company_name=company_name,
        deal_type=deal_type,
        revenue=revenue,
        revenue_range=revenue_range,
        employee_count=employee_count,
        it_headcount=it_headcount,
        it_headcount_with_contractors=it_headcount_with_contractors,
        it_budget=it_budget,
        industry=industry,
        geography=geography,
        operating_model=operating_model,
        size_tier=size_tier,
        extracted_at=datetime.now().isoformat(),
        fact_store_version=self.fact_store.metadata.get("version", "unknown"),
        total_facts_analyzed=len(self.fact_store.facts),
        extraction_warnings=list(self._warnings),
    )


def _build_empty_profile(self) -> CompanyProfile:
    """Build a profile when the FactStore is completely empty."""
    company_name = (
        ProfileField.user_specified(self.deal_context.target_name)
        if self.deal_context and getattr(self.deal_context, 'target_name', None)
        else ProfileField.insufficient_data("Company name")
    )
    deal_type = (
        ProfileField.user_specified(self.deal_context.deal_type)
        if self.deal_context and getattr(self.deal_context, 'deal_type', None)
        else ProfileField.insufficient_data("Deal type")
    )
    industry = (
        ProfileField.user_specified(self.deal_context.industry)
        if self.deal_context and getattr(self.deal_context, 'industry', None)
        else ProfileField.insufficient_data("Industry")
    )

    return CompanyProfile(
        company_name=company_name,
        deal_type=deal_type,
        revenue=ProfileField.insufficient_data("Revenue"),
        revenue_range=ProfileField.insufficient_data("Revenue range"),
        employee_count=ProfileField.insufficient_data("Employee count"),
        it_headcount=ProfileField.insufficient_data("IT headcount"),
        it_headcount_with_contractors=ProfileField.insufficient_data("IT headcount with contractors"),
        it_budget=ProfileField.insufficient_data("IT budget"),
        industry=industry,
        geography=ProfileField.insufficient_data("Geography"),
        operating_model=ProfileField.insufficient_data("Operating model"),
        size_tier="unknown",
        extracted_at=datetime.now().isoformat(),
        fact_store_version="N/A",
        total_facts_analyzed=0,
        extraction_warnings=list(self._warnings),
    )
```

### 6. Graceful Degradation

The extractor is designed to work with any amount of data, from zero to comprehensive.

| Scenario | Behavior |
|----------|----------|
| **Empty FactStore** (0 facts) | Returns profile with only user-specified fields from DealContext. All other fields have `provenance="default"`, `confidence="low"`, value `None`, rationale "Insufficient data - no organization facts available to determine {field}". |
| **No organization facts** (facts exist in other domains) | Extracts geography from infrastructure/network facts. All org-dependent fields (headcount, budget, operating_model) return `ProfileField.not_found(...)`. Revenue is attempted from all domains. |
| **Partial data** (some org facts but missing budget) | Fills in what it can. Missing fields are explicitly marked not-found. Never invents numbers. |
| **Full data room** (comprehensive documents) | All fields populated with high confidence and document_sourced provenance. |
| **Conflicting data** (two documents give different headcounts) | Takes value from highest-confidence fact (then most recent as tiebreaker). Records all alternatives in `ProfileField.conflicts` list. Adds warning to `extraction_warnings`. |

**Critical rule:** The extractor NEVER silently assigns a default value. If a value is defaulted, the `ProfileField` carries `provenance="default"` and `confidence="low"` with a rationale explaining the gap. This is in contrast to the current `consistency_engine.py` `CompanyProfile` which defaults `employee_count=300` with no indication it is a guess.

### 7. Organization Bridge Caching

The `ProfileExtractor` may need organization bridge output for multiple fields (it_headcount, it_headcount_with_contractors, operating_model, geography via staff locations). To avoid redundant processing:

```python
class ProfileExtractor:
    def __init__(self, fact_store: FactStore, deal_context: Any = None):
        self.fact_store = fact_store
        self.deal_context = deal_context
        self._warnings: List[str] = []
        self._org_bridge_result = None  # Cached on first access
        self._org_bridge_status = None

    def _get_org_bridge_result(self):
        """Lazy-load and cache organization bridge result."""
        if self._org_bridge_result is None:
            from services.organization_bridge import build_organization_from_facts
            target_name = ""
            deal_id = ""
            if self.deal_context:
                target_name = getattr(self.deal_context, 'target_name', '') or ''
                # deal_id may be on deal_context or fact_store
            deal_id = getattr(self.fact_store, 'deal_id', '') or deal_id
            self._org_bridge_result, self._org_bridge_status = build_organization_from_facts(
                self.fact_store, target_name=target_name, deal_id=deal_id
            )
        return self._org_bridge_result, self._org_bridge_status
```

---

## Integration Points

### Update 1: `tools_v2/consistency_engine.py`

The existing `CompanyProfile` in `consistency_engine.py` is used by `calculate_work_item_cost()`, `calculate_total_costs()`, and `generate_consistency_report()`. These functions accept a `CompanyProfile` parameter and call `profile.get_total_multiplier()`.

**Migration approach:** Keep the old `CompanyProfile` class temporarily renamed to `_LegacyCompanyProfile` and add an adapter:

```python
# In tools_v2/consistency_engine.py

# Rename existing class
@dataclass
class _LegacyCompanyProfile:
    employee_count: int = 300
    industry: str = "technology"
    geography: str = "single_country"
    it_maturity: str = "standard"
    annual_revenue: float = 50_000_000

    def get_total_multiplier(self) -> Tuple[float, Dict[str, Any]]:
        ...  # existing implementation unchanged


def adapt_profile(profile) -> _LegacyCompanyProfile:
    """
    Convert new canonical CompanyProfile to legacy format for cost calculations.

    Accepts either the new CompanyProfile (from stores/company_profile.py)
    or the old CompanyProfile for backwards compatibility.
    """
    if isinstance(profile, _LegacyCompanyProfile):
        return profile

    # New canonical profile -- extract values with backwards-compatible defaults
    return _LegacyCompanyProfile(
        employee_count=profile.employee_count_value,  # uses @property, defaults to 300
        industry=profile.industry_value,              # defaults to "technology"
        geography=profile.geography_value,            # defaults to "single_country"
        it_maturity="standard",                       # new profile doesn't track maturity yet
        annual_revenue=profile.annual_revenue_value,  # defaults to $50M
    )


# Keep CompanyProfile as an alias for backwards compatibility
CompanyProfile = _LegacyCompanyProfile
```

All existing callers (`calculate_work_item_cost`, `calculate_total_costs`, `generate_consistency_report`) continue to work unchanged. New code should import from `stores/company_profile.py` and pass to these functions, which will use `adapt_profile()` internally.

### Update 2: `tools_v2/html_report.py`

Currently imports `CompanyProfile` from `consistency_engine.py` and accepts it as a parameter. No change needed in the short term -- the adapter handles conversion. In a future spec, the HTML report will render `ProfileField` provenance badges (e.g., showing a small "document-sourced" tag next to revenue).

### Update 3: `tools_v2/pe_report_schemas.py`

The `DealContext` in `pe_report_schemas.py` carries target company fields (`target_revenue`, `target_employees`, etc.) that overlap with `CompanyProfile`. Add a factory method:

```python
# In tools_v2/pe_report_schemas.py

@classmethod
def from_company_profile(cls, profile, buyer_name: str = None) -> "DealContext":
    """
    Build a DealContext from the canonical CompanyProfile.

    Args:
        profile: CompanyProfile from stores/company_profile.py
        buyer_name: Optional buyer name (not part of CompanyProfile)
    """
    return cls(
        target_name=profile.company_name.value or "Unknown",
        deal_type=profile.deal_type.value or "acquisition",
        target_revenue=profile.revenue.value,
        target_employees=profile.employee_count.value,
        target_industry=profile.industry.value,
        target_it_budget=profile.it_budget.value,
        target_it_headcount=profile.it_headcount.value,
        buyer_name=buyer_name,
    )
```

### Update 4: `tools_v2/session.py`

The session `DealContext` is the **input** to `ProfileExtractor` (it provides user-specified fields). No structural changes needed. The `ProfileExtractor` reads from it; it does not modify it.

### Update 5: `ui/deal_readout_view.py`

Currently calls `get_default_company_profile()` which returns `CompanyProfile(employee_count=300, ...)`. Replace with:

```python
def get_company_profile(fact_store: FactStore, deal_context=None) -> CompanyProfile:
    """Extract company profile from facts instead of using hardcoded defaults."""
    from services.profile_extractor import ProfileExtractor
    extractor = ProfileExtractor(fact_store, deal_context)
    return extractor.extract()
```

### Update 6: Pipeline Integration

In the main analysis pipeline (in `services/run_manager.py` or equivalent orchestrator), add profile extraction as a step:

```
1. Document ingestion
2. Discovery phase (all domain agents)
3. >>> Profile extraction (NEW -- this spec) <<<
4. Industry classification (Spec 02, reads CompanyProfile.industry)
5. Reasoning phase
6. Report generation
```

The profile is extracted once after discovery and stored on the deal's session or passed through the pipeline. If documents are added incrementally, the profile is re-extracted.

---

## Benefits

1. **Single source of truth.** One `CompanyProfile` replaces four scattered, inconsistent dataclasses. All consumers read the same data.

2. **Provenance on every number.** When the final report says "450 employees," the analyst can trace it to Fact `F-TGT-ORG-012` from document `HR Census Q3 2024.xlsx`, paragraph "Total IT headcount: 450." This builds trust in the tool's output and satisfies PE firm diligence standards.

3. **Deterministic.** Same FactStore input always produces the same CompanyProfile output. No LLM randomness. No temperature-dependent variation. This is critical for reproducibility -- if a deal team re-runs the analysis, they get identical company profile numbers.

4. **Graceful degradation.** A sparse data room (2 documents) still produces a useful profile with clear "not found" labels. A comprehensive data room (20+ documents) produces a fully populated profile with high confidence. The tool never panics on missing data.

5. **Conflict visibility.** When two documents disagree on headcount, both values are recorded in `ProfileField.conflicts`. The analyst sees the discrepancy instead of wondering which number to trust.

6. **Performance.** Sub-second extraction. No LLM calls, no API latency. Pure in-memory data traversal across the FactStore.

---

## Expectations

| Metric | Target |
|--------|--------|
| Extraction time | < 1 second (no LLM calls, pure data assembly from in-memory FactStore) |
| Field coverage (typical deal with 5+ documents) | At least 3 fields populated with `confidence="high"` |
| Field coverage (comprehensive deal with 15+ documents) | At least 6 fields populated with `confidence="high"` |
| Missing data labeling | 100% of missing fields carry explicit `not_found` or `insufficient_data` provenance. Zero silent defaults. |
| Determinism | `extract()` called N times on same FactStore produces byte-identical `to_dict()` output (excluding `extracted_at` timestamp) |

---

## Risks & Mitigations

### Risk 1: Revenue or headcount buried in unstructured text

**Scenario:** A document mentions "the company employs approximately 1,200 people" in a narrative paragraph, but the discovery agent did not extract this as a structured fact with a `details["total_employees"]` key.

**Impact:** `employee_count` field shows "Not found in data room documents" even though the information exists in the corpus.

**Mitigation:**
- Flag "Employee count not found" as a VDR (Virtual Data Room) gap item in the report. This prompts the deal team to check documents manually.
- In future iterations, add a targeted re-scan: when a field is not found, the profile extractor could invoke a lightweight regex search across raw document text for patterns like `\d{3,5}\s*(employees|people|headcount)`. This is out of scope for Spec 01 but noted as a follow-up.

### Risk 2: Conflicting values across documents

**Scenario:** The IT budget document says "450 IT staff" but the org chart shows 380 names. Which is correct?

**Impact:** Profile shows a single number that may be wrong.

**Mitigation:**
- The `ProfileField.conflicts` list records all candidate values with their source fact IDs and documents.
- The primary value is selected by: (1) highest `Fact.confidence_score`, then (2) most recent `Fact.created_at`.
- The `inference_rationale` explains the selection: "Selected 450 from F-TGT-ORG-015 (IT Budget 2024.xlsx, confidence 0.85) over 380 from F-TGT-ORG-042 (Org Chart.pdf, confidence 0.72). See conflicts for all values."
- The UI (Spec 05) will display a warning icon next to conflicted fields.

### Risk 3: Existing code depends on old CompanyProfile fields

**Scenario:** Code like `profile.employee_count` (returning an `int`) breaks because the new CompanyProfile returns a `ProfileField` object.

**Impact:** Runtime errors in `consistency_engine.py`, `html_report.py`, and `strategic_cost_assessment.py`.

**Mitigation:**
- The old `CompanyProfile` classes are NOT removed in Spec 01. They remain in place.
- An `adapt_profile()` function in `consistency_engine.py` converts the new canonical CompanyProfile to the legacy format on demand.
- Backwards-compatible `@property` methods on the new CompanyProfile (`employee_count_value`, `industry_value`, etc.) provide direct scalar access for callers that need it.
- Migration of old consumers is a separate, follow-up task. Each consumer is updated one at a time with its own test coverage.

### Risk 4: Organization bridge is expensive to run

**Scenario:** `build_organization_from_facts()` is called multiple times during profile extraction (once for it_headcount, once for operating_model, etc.).

**Impact:** Slower-than-expected extraction time if org bridge does heavy processing.

**Mitigation:**
- The `ProfileExtractor` caches the org bridge result on first call via `_get_org_bridge_result()`. Subsequent accesses return the cached result. Only one org bridge invocation per extraction.

### Risk 5: Dollar amount parsing fails on edge cases

**Scenario:** Revenue is recorded as "EUR 50M" or "50 crore" or "GBP 12.5 million" and the parser assumes USD.

**Impact:** Revenue is parsed but represents the wrong currency, silently producing an incorrect dollar figure.

**Mitigation:**
- The `_parse_dollar_amount()` parser only handles USD formats. If a currency prefix other than `$` or no prefix is detected, log a warning and add to `extraction_warnings`: "Revenue value may be in non-USD currency: '{original_value}'. Treating as USD."
- Future enhancement: detect and convert currencies. Out of scope for Spec 01.

---

## Results Criteria

### Test 1: Basic extraction from populated FactStore

**Setup:** Create a `FactStore` with 10+ organization facts including:
- A budget fact with `details={"annual_revenue": 75000000, "total_it_headcount": 45, "it_budget": 3500000}`
- Leadership facts with 3 named leaders
- Central IT facts with team sizes
- 2 MSP outsourcing facts (one SUPPLEMENTAL, one PARTIAL)
- Infrastructure facts with 2 US locations

**Assertion:**
- `profile.revenue.value == 75_000_000`
- `profile.revenue.confidence == "high"`
- `profile.revenue.provenance == "document_sourced"`
- `profile.it_headcount.value == 45`
- `profile.employee_count` is populated (from census or headcount key)
- `profile.operating_model.value == "hybrid"` (2 MSPs, neither FULL)
- `profile.geography.value == "multi_office_domestic"` (2 US locations)
- `profile.size_tier == "midmarket"` ($75M revenue)
- `profile.revenue_range.value == "midmarket"`

### Test 2: Empty FactStore produces "Insufficient data" profile

**Setup:** `FactStore(deal_id="test")` with zero facts. `DealContext(target_name="Acme Corp", deal_type="bolt_on")`.

**Assertion:**
- `profile.company_name.value == "Acme Corp"`
- `profile.company_name.provenance == "user_specified"`
- `profile.revenue.value is None`
- `profile.revenue.provenance == "default"`
- `profile.revenue.inference_rationale` contains "Insufficient data"
- `profile.employee_count.value is None`
- `profile.it_headcount.value is None`
- `profile.geography.value is None`
- `profile.operating_model.value is None`
- `profile.size_tier == "unknown"`
- All `ProfileField` instances with None values have `confidence == "low"`

### Test 3: Conflict resolution (contradictory headcount)

**Setup:** FactStore with two organization facts:
- Fact A (`created_at` = "2024-06-01T10:00:00", `confidence_score` = 0.72): `details={"total_employees": 380}`
- Fact B (`created_at` = "2024-09-15T14:00:00", `confidence_score` = 0.85): `details={"total_employees": 450}`

**Assertion:**
- `profile.employee_count.value == 450` (Fact B wins: higher confidence)
- `profile.employee_count.confidence == "medium"` (conflict exists)
- `len(profile.employee_count.conflicts) == 1` (records the losing value)
- `profile.employee_count.conflicts[0]["value"] == 380`
- `profile.employee_count.conflicts[0]["fact_id"]` matches Fact A's ID
- `profile.employee_count.inference_rationale` mentions "Multiple headcount figures found"

### Test 4: Determinism (same FactStore produces identical profile)

**Setup:** FactStore with 8 facts covering revenue, headcount, geography, MSPs.

**Assertion:**
```python
extractor = ProfileExtractor(fact_store, deal_context)
profile_1 = extractor.extract()
profile_2 = extractor.extract()
profile_3 = extractor.extract()

dict_1 = profile_1.to_dict()
dict_2 = profile_2.to_dict()
dict_3 = profile_3.to_dict()

# Remove extracted_at (timestamp will differ)
for d in [dict_1, dict_2, dict_3]:
    del d["extracted_at"]

assert dict_1 == dict_2 == dict_3
```

### Test 5: Integration with consistency_engine

**Setup:** Extract a `CompanyProfile` from a test FactStore. Pass it to `generate_consistency_report()`.

**Assertion:**
- `generate_consistency_report()` completes without error.
- The returned report dict contains `company_profile` section with correct employee count and industry values.
- Cost multipliers are calculated correctly based on the extracted profile values.

### Test 6: Revenue range fallback to employee count

**Setup:** FactStore with no revenue facts but an organization fact with `details={"total_employees": 250}`.

**Assertion:**
- `profile.revenue.value is None`
- `profile.revenue_range.value == "midmarket"` (250 employees: 100-1000 range)
- `profile.revenue_range.provenance == "inferred"`
- `profile.revenue_range.inference_rationale` contains "employee"

### Test 7: Operating model classification

**Setup A (in-house):** FactStore with organization facts but zero outsourcing/MSP facts.
**Setup B (hybrid):** FactStore with 1 MSP fact, dependency_level = "supplemental".
**Setup C (heavily outsourced):** FactStore with 3 MSP facts, one with dependency_level = "full".

**Assertion:**
- Setup A: `profile.operating_model.value == "in_house"`
- Setup B: `profile.operating_model.value == "hybrid"`
- Setup C: `profile.operating_model.value == "heavily_outsourced"`

### Test 8: Dollar amount parsing

**Assertion** (unit tests on `_parse_dollar_amount`):
- `_parse_dollar_amount(50000000)` == `50_000_000`
- `_parse_dollar_amount("$50M")` == `50_000_000`
- `_parse_dollar_amount("$50 million")` == `50_000_000`
- `_parse_dollar_amount("50,000,000")` == `50_000_000`
- `_parse_dollar_amount("$2.5B")` == `2_500_000_000`
- `_parse_dollar_amount("$500K")` == `500_000`
- `_parse_dollar_amount("50mm")` == `50_000_000`
- `_parse_dollar_amount(None)` == `None`
- `_parse_dollar_amount("")` == `None`
- `_parse_dollar_amount("not a number")` == `None`

### Test 9: Integer parsing

**Assertion** (unit tests on `_parse_integer`):
- `_parse_integer(450)` == `450`
- `_parse_integer("450")` == `450`
- `_parse_integer("~450")` == `450`
- `_parse_integer("approximately 500")` == `500`
- `_parse_integer("450 employees")` == `450`
- `_parse_integer("1,200")` == `1200`
- `_parse_integer(None)` == `None`
- `_parse_integer("")` == `None`

---

## File Summary

| File | Action | Description |
|------|--------|-------------|
| `stores/company_profile.py` | **CREATE** | `ProfileField` and `CompanyProfile` dataclasses |
| `services/profile_extractor.py` | **CREATE** | `ProfileExtractor` service with all extraction logic |
| `tools_v2/consistency_engine.py` | **MODIFY** | Rename old `CompanyProfile` to `_LegacyCompanyProfile`, add `adapt_profile()`, keep `CompanyProfile` alias |
| `tools_v2/pe_report_schemas.py` | **MODIFY** | Add `DealContext.from_company_profile()` class method |
| `ui/deal_readout_view.py` | **MODIFY** | Replace `get_default_company_profile()` with `get_company_profile(fact_store, deal_context)` |
| `tests/test_profile_extractor.py` | **CREATE** | Unit and integration tests per Results Criteria above |

---

## Appendix A: Fact Domain/Category Reference

This table maps which FactStore domains and categories the ProfileExtractor searches for each field. These correspond to the domains defined in `stores/fact_store.py` `DOMAIN_PREFIXES` and the categories used by the discovery agents.

| Profile Field | Fact Domains Searched | Fact Categories Searched | Details Keys Checked |
|---------------|----------------------|-------------------------|---------------------|
| company_name | all (entity=target) | all | `company_name`, `target_name`, `organization_name` |
| revenue | organization | budget | `annual_revenue`, `revenue`, `total_revenue`, `company_revenue` |
| employee_count | organization | budget, roles, leadership, central_it | `total_employees`, `headcount`, `employee_count`, `fte_count`, `total_headcount`, `company_size`, `number_of_employees` |
| it_headcount | organization | budget, roles, leadership, central_it, app_teams, key_individuals | `total_it_headcount`, `it_headcount`, `it_staff_count` (plus org bridge census count) |
| it_budget | organization | budget | `it_budget`, `technology_budget`, `total_it_spend`, `annual_it_spend`, `it_operating_budget` |
| geography | infrastructure, organization, network | all | `region`, `location`, `data_center_location`, `cloud_region`, `deployment_region`, `office_location`, `headquarters`, `hq_location`, `office_locations`, `site_locations`, `wan_sites` |
| operating_model | organization | outsourcing | `dependency_level`, `outsourcing_scope`, `managed_by` (plus org bridge MSP relationships) |

## Appendix B: Relationship to Other Business Context Specs

| Spec | Relationship to Spec 01 |
|------|------------------------|
| **Spec 02: Industry Classification** | Consumes `CompanyProfile.industry` as seed. Enhances it with sub-industry, secondary industries, regulatory context. Writes back to `CompanyProfile.industry` field. |
| **Spec 03: (Reserved)** | -- |
| **Spec 04: Benchmark Engine** | Consumes `CompanyProfile.size_tier`, `revenue_range`, `it_headcount`, `it_budget`, `operating_model` to select appropriate benchmark cohort. |
| **Spec 05: UI Views** | Displays `CompanyProfile` fields with provenance badges. Shows conflicts and missing data warnings. |
