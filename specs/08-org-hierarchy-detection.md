# Spec 08: Organization Hierarchy Detection Logic

**Status:** Draft
**Created:** 2026-02-11
**Complexity:** Medium
**Estimated Implementation:** 3-4 hours

---

## Overview

This specification defines the detection logic to determine whether an organization census contains sufficient management structure data (reporting lines, organizational layers, span of control) to build a complete organizational hierarchy, or whether assumption-building logic should be triggered.

**Why this exists:** The IT due diligence pipeline needs to adapt to varying levels of organizational documentation. Some VDR packages include complete org charts with reporting lines and management layers; others provide only headcount summaries. This detection logic determines which extraction path to follow.

**Key Decision:** Detection happens in the bridge service (not discovery agent) because it requires analyzing the COMPLETE set of extracted facts, which only exists after discovery completes.

---

## Architecture

### Component Positioning

```
Discovery Phase
    ↓
FactStore (org facts extracted)
    ↓
[THIS COMPONENT] → HierarchyDetector
    ↓
    ├─→ HierarchyPresence (FULL) → Extract as normal
    ├─→ HierarchyPresence (PARTIAL) → Extract + Assumption supplement
    └─→ HierarchyPresence (MISSING) → Assumption generation
    ↓
Bridge Service continues...
```

### Dependencies

**Input:**
- FactStore containing organization domain facts (from discovery phase)
- Domain: `"organization"`
- Categories: `leadership`, `central_it`, `roles`, `app_teams`, `outsourcing`, `embedded_it`, `key_individuals`, `skills`, `budget`

**Output:**
- `HierarchyPresence` dataclass with detection results
- Used by: Assumption engine (spec 09), Bridge service (spec 11)

**External Dependencies:**
- `stores.fact_store.FactStore`
- `models.organization_models` (for enums)

---

## Specification

### 1. Data Contract: HierarchyPresence

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any

class HierarchyPresenceStatus(Enum):
    """Status of organizational hierarchy in source documents."""
    FULL = "full"           # Complete hierarchy with reports_to, layers, span
    PARTIAL = "partial"     # Some hierarchy data but gaps exist
    MISSING = "missing"     # Little to no hierarchy data
    UNKNOWN = "unknown"     # Unable to determine (error state)

@dataclass
class HierarchyPresence:
    """Result of hierarchy detection analysis.

    This object describes what organizational structure data was found
    in the source documents and determines whether assumption-building
    logic should be triggered.
    """
    # Primary status
    status: HierarchyPresenceStatus
    confidence: float  # 0.0-1.0, how confident we are in this assessment

    # Detailed findings
    has_reports_to: bool        # reports_to field populated in facts?
    has_explicit_layers: bool   # explicit mention of org layers/levels?
    has_span_data: bool         # span of control mentioned?
    has_org_chart: bool         # org chart diagram in source docs?

    # Quantitative metrics
    leadership_count: int       # number of leadership roles found
    total_role_count: int       # total distinct roles found
    roles_with_reports_to: int  # how many roles have reports_to populated

    # Gap identification
    gaps: List[str]             # what's missing (for VDR requests)

    # Metadata
    detection_timestamp: str    # ISO 8601 timestamp
    fact_count: int             # total org facts analyzed

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for logging/storage."""
        return {
            'status': self.status.value,
            'confidence': self.confidence,
            'has_reports_to': self.has_reports_to,
            'has_explicit_layers': self.has_explicit_layers,
            'has_span_data': self.has_span_data,
            'has_org_chart': self.has_org_chart,
            'leadership_count': self.leadership_count,
            'total_role_count': self.total_role_count,
            'roles_with_reports_to': self.roles_with_reports_to,
            'gaps': self.gaps,
            'detection_timestamp': self.detection_timestamp,
            'fact_count': self.fact_count,
        }
```

### 2. Detection Algorithm

**Location:** `services/org_hierarchy_detector.py` (new file)

**Main Function:**

```python
def detect_hierarchy_presence(fact_store: FactStore, entity: str = "target") -> HierarchyPresence:
    """
    Analyze organization facts to determine hierarchy presence.

    Args:
        fact_store: FactStore containing organization facts
        entity: "target" or "buyer" (default: "target")

    Returns:
        HierarchyPresence object with detection results

    Algorithm:
        1. Extract all org facts for the specified entity
        2. Check for explicit hierarchy indicators
        3. Calculate quantitative metrics
        4. Apply decision rules to determine status
        5. Identify gaps for VDR requests
    """
    pass  # Implementation below
```

### 3. Detection Rules (Decision Logic)

**Rule Set for Status Classification:**

```python
def _classify_status(
    has_reports_to: bool,
    has_explicit_layers: bool,
    has_span_data: bool,
    has_org_chart: bool,
    reports_to_percentage: float,  # 0.0-1.0
    leadership_count: int,
    total_role_count: int
) -> HierarchyPresenceStatus:
    """
    Apply decision rules to classify hierarchy presence.

    FULL Status (all must be true):
        - reports_to_percentage >= 0.80 (80%+ roles have reporting lines)
        - has_explicit_layers OR has_org_chart (structural documentation exists)
        - leadership_count >= 2 (at least CIO + 1 direct report level)

    PARTIAL Status (any must be true):
        - 0.30 <= reports_to_percentage < 0.80 (30-79% roles have reporting lines)
        - has_reports_to AND (leadership_count >= 2)
        - has_explicit_layers OR has_org_chart (but missing reports_to data)

    MISSING Status:
        - reports_to_percentage < 0.30 (less than 30% roles have reporting lines)
        - AND no explicit layers, no org chart
        - OR total_role_count < 3 (insufficient data to assess)
    """

    # FULL: Complete hierarchy
    if (reports_to_percentage >= 0.80 and
        (has_explicit_layers or has_org_chart) and
        leadership_count >= 2):
        return HierarchyPresenceStatus.FULL

    # PARTIAL: Some hierarchy data
    if ((0.30 <= reports_to_percentage < 0.80) or
        (has_reports_to and leadership_count >= 2) or
        (has_explicit_layers or has_org_chart)):
        return HierarchyPresenceStatus.PARTIAL

    # MISSING: Little to no hierarchy
    if (reports_to_percentage < 0.30 and
        not has_explicit_layers and
        not has_org_chart):
        return HierarchyPresenceStatus.MISSING

    # Edge case: insufficient data to classify
    if total_role_count < 3:
        return HierarchyPresenceStatus.MISSING

    # Default to PARTIAL if unclear
    return HierarchyPresenceStatus.PARTIAL
```

### 4. Confidence Scoring

**Confidence Formula:**

```python
def _calculate_confidence(
    status: HierarchyPresenceStatus,
    reports_to_percentage: float,
    has_explicit_layers: bool,
    has_org_chart: bool,
    total_role_count: int
) -> float:
    """
    Calculate confidence score (0.0-1.0) for the detection.

    Higher confidence when:
    - More roles documented (higher total_role_count)
    - Clear signals (explicit layers, org chart)
    - Unambiguous percentages (very high or very low)

    Lower confidence when:
    - Borderline percentages (near thresholds)
    - Conflicting signals (org chart exists but no reports_to)
    - Few roles documented (small sample size)
    """
    base_confidence = 0.5

    # Boost for sample size
    if total_role_count >= 10:
        base_confidence += 0.2
    elif total_role_count >= 5:
        base_confidence += 0.1

    # Boost for explicit documentation
    if has_explicit_layers:
        base_confidence += 0.15
    if has_org_chart:
        base_confidence += 0.15

    # Boost for clear percentages (far from thresholds)
    if status == HierarchyPresenceStatus.FULL:
        if reports_to_percentage >= 0.90:
            base_confidence += 0.1
    elif status == HierarchyPresenceStatus.MISSING:
        if reports_to_percentage <= 0.20:
            base_confidence += 0.1

    # Penalty for borderline cases
    if 0.28 <= reports_to_percentage <= 0.32:  # near 30% threshold
        base_confidence -= 0.1
    if 0.78 <= reports_to_percentage <= 0.82:  # near 80% threshold
        base_confidence -= 0.1

    # Penalty for conflicting signals
    if has_org_chart and reports_to_percentage < 0.30:
        base_confidence -= 0.15  # org chart exists but no data extracted

    return max(0.0, min(1.0, base_confidence))  # clamp to [0, 1]
```

### 5. Hierarchy Indicators (What to Look For)

**Explicit Indicators in Facts:**

```python
def _check_explicit_hierarchy_indicators(org_facts: List[Fact]) -> Dict[str, bool]:
    """
    Check for explicit hierarchy indicators in fact details.

    Returns dict with:
        - has_reports_to: Any fact has 'reports_to' field populated
        - has_explicit_layers: Mention of "layers", "levels", "tiers"
        - has_span_data: Mention of "span of control", "direct reports"
        - has_org_chart: Evidence includes "org chart", "organization chart"
    """
    has_reports_to = False
    has_explicit_layers = False
    has_span_data = False
    has_org_chart = False

    # Keywords for detection
    layer_keywords = ['layer', 'level', 'tier', 'depth', 'hierarchy']
    span_keywords = ['span of control', 'direct report', 'reports to', 'manages']
    chart_keywords = ['org chart', 'organization chart', 'organizational structure']

    for fact in org_facts:
        details = fact.details or {}
        evidence_text = str(fact.evidence).lower() if fact.evidence else ""

        # Check reports_to field
        if 'reports_to' in details and details['reports_to']:
            has_reports_to = True

        # Check for layer mentions
        if any(kw in evidence_text for kw in layer_keywords):
            has_explicit_layers = True

        # Check for span mentions
        if any(kw in evidence_text for kw in span_keywords):
            has_span_data = True

        # Check for org chart mentions
        if any(kw in evidence_text for kw in chart_keywords):
            has_org_chart = True

    return {
        'has_reports_to': has_reports_to,
        'has_explicit_layers': has_explicit_layers,
        'has_span_data': has_span_data,
        'has_org_chart': has_org_chart,
    }
```

### 6. Gap Identification

**Generate VDR Gaps Based on Detection:**

```python
def _identify_gaps(
    status: HierarchyPresenceStatus,
    has_reports_to: bool,
    has_explicit_layers: bool,
    has_span_data: bool,
    has_org_chart: bool
) -> List[str]:
    """
    Identify what organizational data is missing.

    Gaps are used for VDR follow-up requests.
    """
    gaps = []

    if status in [HierarchyPresenceStatus.PARTIAL, HierarchyPresenceStatus.MISSING]:
        if not has_reports_to:
            gaps.append("Reporting lines (who reports to whom)")

        if not has_explicit_layers:
            gaps.append("Management layers/levels (CXO, VP, Director, Manager, IC)")

        if not has_span_data:
            gaps.append("Span of control (number of direct reports per manager)")

        if not has_org_chart:
            gaps.append("Organization chart or hierarchy diagram")

    if status == HierarchyPresenceStatus.MISSING:
        gaps.append("Complete IT organization structure documentation")

    return gaps
```

### 7. Complete Implementation

**File:** `services/org_hierarchy_detector.py`

```python
"""
Organization Hierarchy Detector

Analyzes organization facts to determine hierarchy presence and quality.
Part of adaptive organization extraction feature (spec 08).
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from stores.fact_store import FactStore, Fact

logger = logging.getLogger(__name__)


class HierarchyPresenceStatus(Enum):
    """Status of organizational hierarchy in source documents."""
    FULL = "full"
    PARTIAL = "partial"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass
class HierarchyPresence:
    """Result of hierarchy detection analysis."""
    status: HierarchyPresenceStatus
    confidence: float
    has_reports_to: bool
    has_explicit_layers: bool
    has_span_data: bool
    has_org_chart: bool
    leadership_count: int
    total_role_count: int
    roles_with_reports_to: int
    gaps: List[str]
    detection_timestamp: str
    fact_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for logging/storage."""
        return {
            'status': self.status.value,
            'confidence': self.confidence,
            'has_reports_to': self.has_reports_to,
            'has_explicit_layers': self.has_explicit_layers,
            'has_span_data': self.has_span_data,
            'has_org_chart': self.has_org_chart,
            'leadership_count': self.leadership_count,
            'total_role_count': self.total_role_count,
            'roles_with_reports_to': self.roles_with_reports_to,
            'gaps': self.gaps,
            'detection_timestamp': self.detection_timestamp,
            'fact_count': self.fact_count,
        }


def detect_hierarchy_presence(fact_store: FactStore, entity: str = "target") -> HierarchyPresence:
    """
    Analyze organization facts to determine hierarchy presence.

    Args:
        fact_store: FactStore containing organization facts
        entity: "target" or "buyer" (default: "target")

    Returns:
        HierarchyPresence object with detection results

    Raises:
        ValueError: If entity is invalid or facts have missing entity fields
    """
    # Validate entity parameter
    if entity not in ("target", "buyer"):
        raise ValueError(f"Invalid entity '{entity}'. Must be 'target' or 'buyer'")

    # Extract ALL org facts first (before filtering by entity)
    all_org_facts = [f for f in fact_store.facts if f.domain == "organization"]

    # CRITICAL (P0 FIX): Validate entity field on facts
    facts_missing_entity = []
    facts_invalid_entity = []

    for fact in all_org_facts:
        if not hasattr(fact, 'entity') or fact.entity is None or fact.entity == "":
            facts_missing_entity.append(fact.item)
        elif fact.entity not in ("target", "buyer"):
            facts_invalid_entity.append((fact.item, fact.entity))

    # Log and handle invalid facts
    if facts_missing_entity:
        logger.error(
            f"Found {len(facts_missing_entity)} org facts with missing entity field. "
            f"This indicates an upstream bug in discovery agent. "
            f"Facts: {facts_missing_entity[:5]}"
        )
        raise ValueError(
            f"Entity field validation failed: {len(facts_missing_entity)} facts "
            f"have missing entity. Discovery agent must set entity on all facts."
        )

    if facts_invalid_entity:
        logger.error(
            f"Found {len(facts_invalid_entity)} org facts with invalid entity values. "
            f"Facts: {facts_invalid_entity[:5]}"
        )
        raise ValueError(
            f"Entity field validation failed: {len(facts_invalid_entity)} facts "
            f"have invalid entity values (not 'target' or 'buyer')"
        )

    # Now filter by entity (safe because we validated above)
    org_facts = [f for f in all_org_facts if f.entity == entity]

    if not org_facts:
        logger.warning(f"No organization facts found for entity: {entity}")
        return HierarchyPresence(
            status=HierarchyPresenceStatus.UNKNOWN,
            confidence=0.0,
            has_reports_to=False,
            has_explicit_layers=False,
            has_span_data=False,
            has_org_chart=False,
            leadership_count=0,
            total_role_count=0,
            roles_with_reports_to=0,
            gaps=["No organization data found"],
            detection_timestamp=datetime.utcnow().isoformat(),
            fact_count=0
        )

    # Check for hierarchy indicators
    indicators = _check_explicit_hierarchy_indicators(org_facts)

    # Count roles and leadership
    leadership_facts = [f for f in org_facts if f.category == "leadership"]
    role_facts = [f for f in org_facts if f.category in ["leadership", "roles", "central_it"]]

    leadership_count = len(leadership_facts)
    total_role_count = len(role_facts)

    # Count roles with reports_to
    roles_with_reports_to = sum(
        1 for f in role_facts
        if f.details and f.details.get('reports_to')
    )

    reports_to_percentage = (
        roles_with_reports_to / total_role_count
        if total_role_count > 0
        else 0.0
    )

    # Classify status
    status = _classify_status(
        has_reports_to=indicators['has_reports_to'],
        has_explicit_layers=indicators['has_explicit_layers'],
        has_span_data=indicators['has_span_data'],
        has_org_chart=indicators['has_org_chart'],
        reports_to_percentage=reports_to_percentage,
        leadership_count=leadership_count,
        total_role_count=total_role_count
    )

    # Calculate confidence
    confidence = _calculate_confidence(
        status=status,
        reports_to_percentage=reports_to_percentage,
        has_explicit_layers=indicators['has_explicit_layers'],
        has_org_chart=indicators['has_org_chart'],
        total_role_count=total_role_count
    )

    # Identify gaps
    gaps = _identify_gaps(
        status=status,
        has_reports_to=indicators['has_reports_to'],
        has_explicit_layers=indicators['has_explicit_layers'],
        has_span_data=indicators['has_span_data'],
        has_org_chart=indicators['has_org_chart']
    )

    result = HierarchyPresence(
        status=status,
        confidence=confidence,
        has_reports_to=indicators['has_reports_to'],
        has_explicit_layers=indicators['has_explicit_layers'],
        has_span_data=indicators['has_span_data'],
        has_org_chart=indicators['has_org_chart'],
        leadership_count=leadership_count,
        total_role_count=total_role_count,
        roles_with_reports_to=roles_with_reports_to,
        gaps=gaps,
        detection_timestamp=datetime.utcnow().isoformat(),
        fact_count=len(org_facts)
    )

    logger.info(f"Hierarchy detection for {entity}: {status.value} "
                f"(confidence: {confidence:.2f}, roles: {total_role_count}, "
                f"reports_to: {reports_to_percentage:.0%})")

    return result


def _check_explicit_hierarchy_indicators(org_facts: List[Fact]) -> Dict[str, bool]:
    """Check for explicit hierarchy indicators in facts."""
    has_reports_to = False
    has_explicit_layers = False
    has_span_data = False
    has_org_chart = False

    layer_keywords = ['layer', 'level', 'tier', 'depth', 'hierarchy']
    span_keywords = ['span of control', 'direct report', 'reports to', 'manages']
    chart_keywords = ['org chart', 'organization chart', 'organizational structure']

    for fact in org_facts:
        details = fact.details or {}
        evidence_text = str(fact.evidence).lower() if fact.evidence else ""

        if 'reports_to' in details and details['reports_to']:
            has_reports_to = True

        if any(kw in evidence_text for kw in layer_keywords):
            has_explicit_layers = True

        if any(kw in evidence_text for kw in span_keywords):
            has_span_data = True

        if any(kw in evidence_text for kw in chart_keywords):
            has_org_chart = True

    return {
        'has_reports_to': has_reports_to,
        'has_explicit_layers': has_explicit_layers,
        'has_span_data': has_span_data,
        'has_org_chart': has_org_chart,
    }


def _classify_status(
    has_reports_to: bool,
    has_explicit_layers: bool,
    has_span_data: bool,
    has_org_chart: bool,
    reports_to_percentage: float,
    leadership_count: int,
    total_role_count: int
) -> HierarchyPresenceStatus:
    """Apply decision rules to classify hierarchy presence."""

    if (reports_to_percentage >= 0.80 and
        (has_explicit_layers or has_org_chart) and
        leadership_count >= 2):
        return HierarchyPresenceStatus.FULL

    if ((0.30 <= reports_to_percentage < 0.80) or
        (has_reports_to and leadership_count >= 2) or
        (has_explicit_layers or has_org_chart)):
        return HierarchyPresenceStatus.PARTIAL

    if (reports_to_percentage < 0.30 and
        not has_explicit_layers and
        not has_org_chart):
        return HierarchyPresenceStatus.MISSING

    if total_role_count < 3:
        return HierarchyPresenceStatus.MISSING

    return HierarchyPresenceStatus.PARTIAL


def _calculate_confidence(
    status: HierarchyPresenceStatus,
    reports_to_percentage: float,
    has_explicit_layers: bool,
    has_org_chart: bool,
    total_role_count: int
) -> float:
    """Calculate confidence score for the detection."""
    base_confidence = 0.5

    if total_role_count >= 10:
        base_confidence += 0.2
    elif total_role_count >= 5:
        base_confidence += 0.1

    if has_explicit_layers:
        base_confidence += 0.15
    if has_org_chart:
        base_confidence += 0.15

    if status == HierarchyPresenceStatus.FULL:
        if reports_to_percentage >= 0.90:
            base_confidence += 0.1
    elif status == HierarchyPresenceStatus.MISSING:
        if reports_to_percentage <= 0.20:
            base_confidence += 0.1

    if 0.28 <= reports_to_percentage <= 0.32:
        base_confidence -= 0.1
    if 0.78 <= reports_to_percentage <= 0.82:
        base_confidence -= 0.1

    if has_org_chart and reports_to_percentage < 0.30:
        base_confidence -= 0.15

    return max(0.0, min(1.0, base_confidence))


def _identify_gaps(
    status: HierarchyPresenceStatus,
    has_reports_to: bool,
    has_explicit_layers: bool,
    has_span_data: bool,
    has_org_chart: bool
) -> List[str]:
    """Identify what organizational data is missing."""
    gaps = []

    if status in [HierarchyPresenceStatus.PARTIAL, HierarchyPresenceStatus.MISSING]:
        if not has_reports_to:
            gaps.append("Reporting lines (who reports to whom)")

        if not has_explicit_layers:
            gaps.append("Management layers/levels (CXO, VP, Director, Manager, IC)")

        if not has_span_data:
            gaps.append("Span of control (number of direct reports per manager)")

        if not has_org_chart:
            gaps.append("Organization chart or hierarchy diagram")

    if status == HierarchyPresenceStatus.MISSING:
        gaps.append("Complete IT organization structure documentation")

    return gaps
```

---

## Verification Strategy

### Unit Tests

**File:** `tests/test_org_hierarchy_detector.py`

**Test Cases:**

1. **test_detect_full_hierarchy**
   - Input: FactStore with 10 roles, 90% have reports_to, explicit layers mentioned
   - Expected: status=FULL, confidence >= 0.8

2. **test_detect_partial_hierarchy**
   - Input: FactStore with 8 roles, 50% have reports_to, no layers mentioned
   - Expected: status=PARTIAL, confidence 0.5-0.7

3. **test_detect_missing_hierarchy**
   - Input: FactStore with 5 roles, 0% have reports_to, no layers/chart
   - Expected: status=MISSING, confidence >= 0.6, gaps list populated

4. **test_detect_borderline_threshold**
   - Input: FactStore with 79% reports_to (near 80% threshold)
   - Expected: status=PARTIAL, confidence reduced by penalty

5. **test_detect_conflicting_signals**
   - Input: FactStore with org_chart=True but 0% reports_to
   - Expected: confidence penalty applied

6. **test_detect_empty_facts**
   - Input: Empty FactStore
   - Expected: status=UNKNOWN, confidence=0.0

7. **test_detect_entity_filtering**
   - Input: FactStore with target and buyer facts
   - Expected: Only target facts analyzed when entity="target"

### Integration Tests

**File:** `tests/integration/test_hierarchy_detection_integration.py`

**Test Cases:**

1. **test_detection_with_golden_fixture**
   - Use existing golden fixture (full org structure)
   - Expected: FULL status detected

2. **test_detection_with_sparse_fixture**
   - Create fixture with minimal org data
   - Expected: MISSING status, gaps match expected

3. **test_detection_drives_assumption_engine**
   - Mock assumption engine
   - Verify MISSING status triggers assumption generation

### Manual Verification

**Steps:**

1. Run detector on 3 real VDR docs with varying hierarchy completeness
2. Manually verify status classification matches human judgment
3. Check confidence scores are reasonable (not all 0.5 or all 1.0)
4. Verify gaps list is actionable for VDR follow-up

**Success Criteria:**
- 90%+ agreement between detector and human classification
- Confidence scores correlate with human certainty
- Gaps list contains concrete requests (not vague)

---

## Benefits

### Why This Approach

**Quantitative decision rules** (80%/30% thresholds) provide:
- Deterministic behavior (same inputs → same outputs)
- Easy to test (no LLM calls needed)
- Fast execution (<100ms)
- Explainable results (can show why status was chosen)

**Multi-signal detection** (reports_to % + explicit layers + org chart) provides:
- Robustness to varied documentation styles
- Graceful handling of partial data
- Clear gap identification for VDR requests

**Confidence scoring** provides:
- Transparent uncertainty quantification
- Ability to flag borderline cases for manual review
- Input for downstream assumption confidence

### Alternatives Considered

**Alternative 1: LLM-based detection**
- Pros: More flexible, handles nuanced cases
- Cons: Slower, costly, non-deterministic, hard to test
- Decision: Use rule-based for speed/cost/determinism

**Alternative 2: Binary detection (has/doesn't have)**
- Pros: Simpler logic
- Cons: Loses valuable PARTIAL signal, can't express uncertainty
- Decision: Three-way classification better matches reality

---

## Expectations

### Success Metrics

**Accuracy:**
- Detector agrees with human classification 90%+ of time
- Confidence scores correlate with human certainty (r > 0.7)

**Performance:**
- Detection completes in <100ms for typical fact sets (10-50 facts)
- Memory usage <50MB for detection logic

**Usability:**
- Gaps list used in 80%+ of PARTIAL/MISSING cases for VDR follow-up
- No manual overrides needed (detector works autonomously)

### What Success Looks Like

**Scenario 1: Full Hierarchy Document**
- Input: VDR doc with complete org chart, all reports_to populated
- Detection: status=FULL, confidence=0.9
- Outcome: System extracts normally, no assumptions triggered

**Scenario 2: Headcount Summary Only**
- Input: VDR doc with team headcounts, no reporting lines
- Detection: status=MISSING, confidence=0.7, gaps=["Reporting lines", "Management layers", ...]
- Outcome: Assumption engine triggered, gaps added to VDR request pack

**Scenario 3: Partial Data**
- Input: Leadership roles with reports_to, but team-level staff missing reporting lines
- Detection: status=PARTIAL, confidence=0.6, gaps=["Reporting lines for team-level staff"]
- Outcome: Extract leadership hierarchy, supplement with assumptions for teams

---

## Risks & Mitigations

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Thresholds (80%/30%) don't match real-world docs** | Mis-classification, wrong path triggered | Medium | Run on 20+ real VDR docs, calibrate thresholds if needed |
| **Conflicting signals (org chart exists but no data extracted)** | Low confidence, unclear status | Low | Explicit confidence penalty for conflicts, logged for review |
| **Entity filtering fails (buyer/target facts mixed)** | Wrong entity analyzed | Low | Entity field validated in fact creation (spec 04), tested in entity_propagation tests |
| **Performance degradation on large fact sets (1000+ facts)** | Slow detection (>1 sec) | Very Low | Detection is O(n), benchmarked at <100ms for 50 facts, should scale to 1000 |

### Implementation Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Keywords for layer/span detection too narrow** | False negatives (miss existing data) | Medium | Expand keyword lists based on real doc analysis, add tests |
| **Confidence formula produces all 0.5 scores** | Meaningless confidence | Low | Test on diverse fixtures, verify variance in outputs |
| **Gap identification too generic** | Unusable VDR requests | Medium | Validate gaps with M&A team, ensure specificity |

---

## Results Criteria

### Acceptance Criteria (Must-Have)

- [ ] `HierarchyPresence` dataclass implemented with all fields
- [ ] `detect_hierarchy_presence()` function returns correct status for:
  - [ ] FULL case (>80% reports_to + layers/chart)
  - [ ] PARTIAL case (30-79% reports_to OR leadership with reports_to)
  - [ ] MISSING case (<30% reports_to, no layers/chart)
- [ ] Confidence scores vary (not all 0.5 or all 1.0) across test cases
- [ ] Gaps list populated for PARTIAL/MISSING cases
- [ ] Entity filtering works (target vs buyer facts separated)
- [ ] Detection completes in <100ms for typical fact sets
- [ ] All unit tests pass (7 tests minimum)
- [ ] Integration tests pass with golden fixtures

### Success Metrics

**Code Quality:**
- Type hints on all functions
- Docstrings on all public functions
- Logging at INFO level for detection results
- No hard-coded magic numbers (thresholds in constants)

**Documentation:**
- README entry explaining detection logic
- Example usage in docstring
- Decision rules documented in comments

**Testability:**
- Fixtures for FULL, PARTIAL, MISSING cases
- Edge case tests (empty facts, borderline thresholds, conflicts)
- Integration test with real doc parsing

---

## Dependencies

**Depends On:**
- None (first spec in the adaptive org feature)

**Enables:**
- Spec 09: Assumption engine (consumes HierarchyPresence)
- Spec 11: Bridge integration (uses detection to route logic)

**Files Created:**
- `services/org_hierarchy_detector.py` (new, ~300 lines)

**Files Modified:**
- None (net new functionality)

---

## Open Questions

**Q1: Should detection run for buyer entity?**
- Decision: YES, but configurable via feature flag `ENABLE_BUYER_ORG_ASSUMPTIONS` (default: False per audit2)

**Q2: Should confidence threshold gate assumption generation?**
- Decision: NO threshold gating. All MISSING/PARTIAL statuses trigger assumptions, but low confidence is logged for review.

**Q3: How to handle org facts with no entity field?**
- Decision: Default to "target" (per CLAUDE.md guidance), log warning for missing entity.

---

## Implementation Checklist

- [ ] Create `services/org_hierarchy_detector.py`
- [ ] Define `HierarchyPresenceStatus` enum
- [ ] Define `HierarchyPresence` dataclass with `to_dict()`
- [ ] Implement `detect_hierarchy_presence()` main function
- [ ] Implement `_check_explicit_hierarchy_indicators()`
- [ ] Implement `_classify_status()` with decision rules
- [ ] Implement `_calculate_confidence()` with formula
- [ ] Implement `_identify_gaps()` with gap mapping
- [ ] Add logging at INFO level for detection results
- [ ] Create unit tests in `tests/test_org_hierarchy_detector.py` (7+ tests)
- [ ] Create integration tests in `tests/integration/test_hierarchy_detection_integration.py`
- [ ] Test on real VDR documents (3+ docs with varying completeness)
- [ ] Calibrate thresholds if needed based on real doc testing
- [ ] Update README with detection logic explanation

---

**Estimated Implementation Time:** 3-4 hours
**Confidence:** High (straightforward rule-based logic, no LLM calls)
