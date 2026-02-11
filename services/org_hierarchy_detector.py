"""
Organization Hierarchy Detector

Analyzes organization facts to determine hierarchy presence and quality.
Part of adaptive organization extraction feature (spec 08).

This module implements the detection logic that decides whether:
- FULL: Complete hierarchy exists → extract as normal
- PARTIAL: Some hierarchy data → extract + supplement with assumptions
- MISSING: Little to no hierarchy → generate assumptions

Detection happens after discovery completes but before inventory population.
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

    Algorithm:
        1. Validate entity parameter
        2. Extract all org facts and validate entity fields (P0 fix #4)
        3. Filter facts by specified entity
        4. Check for explicit hierarchy indicators
        5. Calculate quantitative metrics
        6. Apply decision rules to determine status
        7. Calculate confidence score
        8. Identify gaps for VDR requests
    """
    # Validate entity parameter
    if entity not in ("target", "buyer"):
        raise ValueError(f"Invalid entity '{entity}'. Must be 'target' or 'buyer'")

    # Extract ALL org facts first (before filtering by entity)
    all_org_facts = [f for f in fact_store.facts if f.domain == "organization"]

    # CRITICAL (P0 FIX #4): Validate entity field on facts
    # This prevents silent failures where entity=None causes empty result lists
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

    # Check for explicit hierarchy indicators
    indicators = _check_explicit_hierarchy_indicators(org_facts)

    # Count roles and leadership
    leadership_facts = [f for f in org_facts if f.category == "leadership"]
    role_facts = [f for f in org_facts if f.category in ("leadership", "central_it", "roles", "app_teams")]

    leadership_count = len(leadership_facts)
    total_role_count = len(role_facts)

    # Count roles with reports_to populated
    roles_with_reports_to = sum(
        1 for f in role_facts
        if 'reports_to' in (f.details or {}) and (f.details or {}).get('reports_to')
    )

    # Calculate reports_to percentage
    reports_to_percentage = (
        roles_with_reports_to / total_role_count
        if total_role_count > 0
        else 0.0
    )

    # Classify status based on detection rules
    status = _classify_status(
        has_reports_to=indicators['has_reports_to'],
        has_explicit_layers=indicators['has_explicit_layers'],
        has_span_data=indicators['has_span_data'],
        has_org_chart=indicators['has_org_chart'],
        reports_to_percentage=reports_to_percentage,
        leadership_count=leadership_count,
        total_role_count=total_role_count
    )

    # Calculate confidence score
    confidence = _calculate_confidence(
        status=status,
        reports_to_percentage=reports_to_percentage,
        has_explicit_layers=indicators['has_explicit_layers'],
        has_org_chart=indicators['has_org_chart'],
        total_role_count=total_role_count
    )

    # Identify gaps for VDR requests
    gaps = _identify_gaps(
        status=status,
        has_reports_to=indicators['has_reports_to'],
        has_explicit_layers=indicators['has_explicit_layers'],
        has_span_data=indicators['has_span_data'],
        has_org_chart=indicators['has_org_chart']
    )

    return HierarchyPresence(
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
        # Early exit optimization (P1 fix suggestion)
        if has_reports_to and has_explicit_layers and has_span_data and has_org_chart:
            break

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

    # Edge case: insufficient data to classify
    if total_role_count < 3:
        return HierarchyPresenceStatus.MISSING

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

    # Default to PARTIAL if unclear
    return HierarchyPresenceStatus.PARTIAL


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

    # Penalty for borderline cases (near 30% or 80% thresholds)
    if 0.28 <= reports_to_percentage <= 0.32:  # near 30% threshold
        base_confidence -= 0.1
    if 0.78 <= reports_to_percentage <= 0.82:  # near 80% threshold
        base_confidence -= 0.1

    # Penalty for conflicting signals
    if has_org_chart and reports_to_percentage < 0.30:
        base_confidence -= 0.15  # org chart exists but no data extracted

    return max(0.0, min(1.0, base_confidence))  # clamp to [0, 1]


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
