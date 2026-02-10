"""
Triage Flow - Enhanced Evidence and Work Item Management

Implements Points 87-95 of the Enhancement Plan:
- Fact → Risk flow with confidence scoring and validation
- Risk → Work Item flow with dependency detection and effort estimation
- Counter-evidence tracking for balanced risk assessment

This module provides validation and enrichment for the triage pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS FOR TRIAGE FLOW
# =============================================================================

class EvidenceStrength(Enum):
    """Strength of evidence supporting a finding."""
    STRONG = "strong"        # Multiple corroborating facts, explicit statements
    MODERATE = "moderate"    # 2-3 supporting facts, some inference
    WEAK = "weak"           # Single fact or high inference
    SPECULATIVE = "speculative"  # No direct evidence, purely inferred


class WorkItemPhase(Enum):
    """Enhanced work item phases for integration planning."""
    PRE_CLOSE = "Pre_Close"        # Before deal closes (due diligence actions)
    DAY_1 = "Day_1"                # Day 1 critical (business continuity)
    DAY_30 = "Day_30"              # First month (stabilization)
    DAY_100 = "Day_100"            # First 100 days (initial integration)
    POST_100 = "Post_100"          # After 100 days (optimization)
    ONGOING = "Ongoing"            # Continuous/recurring activities


class EffortSize(Enum):
    """T-shirt sizing for effort estimation."""
    XS = "XS"    # < 1 week, 1-2 people
    S = "S"      # 1-2 weeks, 2-3 people
    M = "M"      # 2-4 weeks, 3-5 people
    L = "L"      # 1-2 months, 5-10 people
    XL = "XL"    # 2-4 months, 10+ people
    XXL = "XXL"  # 4+ months, large team


class OwnerType(Enum):
    """Suggested owner types for work items."""
    TARGET_IT = "Target IT"
    BUYER_IT = "Buyer IT"
    INTEGRATION_TEAM = "Integration Team"
    SHARED = "Shared (Target + Buyer)"
    VENDOR = "Vendor/Third Party"
    TSA_PROVIDER = "TSA Provider"
    BUSINESS = "Business Stakeholder"


# =============================================================================
# EFFORT ESTIMATION INDICATORS
# =============================================================================

# Indicators that suggest larger effort
EFFORT_INDICATORS = {
    "xxl": [
        "erp migration", "sap migration", "oracle migration",
        "data center exit", "data center consolidation",
        "enterprise transformation", "full modernization",
        "complete platform replacement"
    ],
    "xl": [
        "platform migration", "cloud migration program",
        "identity transformation", "security transformation",
        "multi-site network redesign", "large application portfolio"
    ],
    "l": [
        "migration program", "upgrade program", "consolidation",
        "architecture redesign", "refresh program", "replatform"
    ],
    "m": [
        "deployment", "implementation", "integration",
        "upgrade", "migration", "assessment", "remediation"
    ],
    "s": [
        "configuration", "setup", "enablement",
        "policy change", "process update", "documentation"
    ],
    "xs": [
        "simple change", "minor update", "quick fix",
        "single configuration", "basic script"
    ]
}

# Count-based effort adjustment
COUNT_THRESHOLDS = {
    "users": [(5000, "XXL"), (2000, "XL"), (500, "L"), (100, "M"), (0, "S")],
    "applications": [(50, "XXL"), (25, "XL"), (10, "L"), (5, "M"), (0, "S")],
    "servers": [(200, "XXL"), (100, "XL"), (50, "L"), (20, "M"), (0, "S")],
    "sites": [(50, "XXL"), (20, "XL"), (10, "L"), (5, "M"), (0, "S")],
}


# =============================================================================
# OWNER SUGGESTION RULES
# =============================================================================

OWNER_RULES = {
    # Domain-based defaults
    "domain_defaults": {
        "infrastructure": OwnerType.TARGET_IT,
        "network": OwnerType.TARGET_IT,
        "cybersecurity": OwnerType.SHARED,
        "applications": OwnerType.TARGET_IT,
        "identity_access": OwnerType.SHARED,
        "organization": OwnerType.INTEGRATION_TEAM,
    },
    # Keyword overrides
    "keyword_overrides": {
        OwnerType.BUYER_IT: [
            "buyer infrastructure", "buyer network", "connect to buyer",
            "integrate with buyer", "buyer's", "acquirer"
        ],
        OwnerType.INTEGRATION_TEAM: [
            "integration planning", "synergy", "consolidation plan",
            "transition", "carveout", "separation"
        ],
        OwnerType.TSA_PROVIDER: [
            "tsa", "transition services", "temporary support",
            "interim services"
        ],
        OwnerType.VENDOR: [
            "vendor support", "third party", "managed service",
            "outsourced", "contractor"
        ],
        OwnerType.BUSINESS: [
            "business decision", "stakeholder alignment",
            "executive approval", "budget approval"
        ]
    },
    # Phase-based adjustments
    "phase_adjustments": {
        WorkItemPhase.PRE_CLOSE: OwnerType.INTEGRATION_TEAM,
        WorkItemPhase.DAY_1: OwnerType.SHARED,
    }
}


# =============================================================================
# RISK VALIDATION RULES
# =============================================================================

@dataclass
class ValidationResult:
    """Result of validating a risk or work item."""
    is_valid: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence_adjustment: float = 0.0  # Multiplier for confidence


class RiskValidator:
    """
    Validates risks have sufficient factual basis.

    Implements Point 89: Add risk validation rules.
    """

    MIN_FACTS_FOR_HIGH_SEVERITY = 2
    MIN_FACTS_FOR_CRITICAL = 3
    MIN_EVIDENCE_FOR_STRONG = 3
    MIN_REASONING_LENGTH = 50  # Characters

    def __init__(self, fact_store=None):
        self.fact_store = fact_store

    def validate_risk(self, risk_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a risk has sufficient factual basis.

        Args:
            risk_data: Dict with risk fields (based_on_facts, severity, reasoning, etc.)

        Returns:
            ValidationResult with validity status and feedback
        """
        result = ValidationResult(is_valid=True)

        based_on_facts = risk_data.get("based_on_facts", [])
        severity = risk_data.get("severity", "medium")
        reasoning = risk_data.get("reasoning", "")
        mitigating_facts = risk_data.get("mitigating_facts", [])

        # Rule 1: Must have at least one supporting fact
        if not based_on_facts:
            result.errors.append("Risk must cite at least one supporting fact")
            result.is_valid = False
            result.confidence_adjustment = 0.5

        # Rule 2: High severity risks need more evidence
        if severity == "high" and len(based_on_facts) < self.MIN_FACTS_FOR_HIGH_SEVERITY:
            result.warnings.append(
                f"High severity risk has only {len(based_on_facts)} fact(s); "
                f"recommend at least {self.MIN_FACTS_FOR_HIGH_SEVERITY}"
            )
            result.confidence_adjustment = 0.8

        # Rule 3: Critical risks need strong evidence
        if severity == "critical" and len(based_on_facts) < self.MIN_FACTS_FOR_CRITICAL:
            result.warnings.append(
                f"Critical risk has only {len(based_on_facts)} fact(s); "
                f"recommend at least {self.MIN_FACTS_FOR_CRITICAL} for critical severity"
            )
            result.confidence_adjustment = 0.7

        # Rule 4: Reasoning should explain the connection
        if len(reasoning) < self.MIN_REASONING_LENGTH:
            result.warnings.append(
                "Reasoning is too brief; explain how the facts support this risk"
            )
            result.suggestions.append("Expand reasoning to show the logical chain from facts to risk")

        # Rule 5: Validate cited facts exist (if fact_store available)
        if self.fact_store and based_on_facts:
            invalid_facts = self._validate_fact_ids(based_on_facts)
            if invalid_facts:
                result.warnings.append(f"Unknown fact IDs cited: {invalid_facts}")
                result.confidence_adjustment *= 0.9

        # Rule 6: Check for mitigating evidence balance
        if mitigating_facts and len(mitigating_facts) >= len(based_on_facts):
            result.suggestions.append(
                "Consider lowering severity: mitigating evidence equals or exceeds supporting evidence"
            )

        return result

    def _validate_fact_ids(self, fact_ids: List[str]) -> List[str]:
        """Check which fact IDs don't exist in the fact store."""
        invalid = []
        for fid in fact_ids:
            fact = self.fact_store.get_fact(fid)
            if not fact:
                gap = self.fact_store.get_gap(fid)
                if not gap:
                    invalid.append(fid)
        return invalid


# =============================================================================
# CONFIDENCE SCORING
# =============================================================================

class ConfidenceScorer:
    """
    Calculates risk confidence based on evidence strength.

    Implements Point 88: Risk confidence scoring based on evidence strength.
    """

    # Base scores for different confidence levels
    BASE_SCORES = {
        "high": 0.9,
        "medium": 0.7,
        "low": 0.5
    }

    # Evidence quality multipliers
    EVIDENCE_MULTIPLIERS = {
        "explicit_statement": 1.2,    # Fact explicitly states the issue
        "quantified_data": 1.15,      # Has specific numbers/metrics
        "corroborated": 1.1,          # Multiple facts support same point
        "inferred": 0.85,             # Derived through reasoning
        "speculative": 0.7,           # No direct evidence
    }

    def __init__(self, fact_store=None):
        self.fact_store = fact_store

    def calculate_confidence(
        self,
        stated_confidence: str,
        based_on_facts: List[str],
        reasoning: str,
        mitigating_facts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate an adjusted confidence score based on evidence strength.

        Args:
            stated_confidence: The confidence level stated by the agent
            based_on_facts: List of fact IDs supporting the finding
            reasoning: The reasoning text explaining the connection
            mitigating_facts: Optional list of fact IDs that counter the finding

        Returns:
            Dict with adjusted_confidence, evidence_strength, and explanation
        """
        base_score = self.BASE_SCORES.get(stated_confidence, 0.5)
        multiplier = 1.0
        explanations = []

        # Factor 1: Number of supporting facts
        fact_count = len(based_on_facts)
        if fact_count >= 3:
            multiplier *= 1.15
            explanations.append(f"Strong evidence ({fact_count} facts)")
        elif fact_count == 2:
            multiplier *= 1.05
            explanations.append(f"Moderate evidence ({fact_count} facts)")
        elif fact_count == 1:
            multiplier *= 0.95
            explanations.append("Single fact support")
        else:
            multiplier *= 0.6
            explanations.append("No factual citations")

        # Factor 2: Evidence quality (if fact store available)
        if self.fact_store and based_on_facts:
            quality_score = self._assess_evidence_quality(based_on_facts)
            multiplier *= quality_score["multiplier"]
            if quality_score["notes"]:
                explanations.append(quality_score["notes"])

        # Factor 3: Reasoning quality
        reasoning_score = self._assess_reasoning_quality(reasoning)
        multiplier *= reasoning_score["multiplier"]
        if reasoning_score["notes"]:
            explanations.append(reasoning_score["notes"])

        # Factor 4: Counter-evidence impact
        if mitigating_facts:
            mitigation_ratio = len(mitigating_facts) / max(1, fact_count)
            if mitigation_ratio > 0.5:
                multiplier *= 0.85
                explanations.append(f"Significant mitigating evidence ({len(mitigating_facts)} facts)")

        # Calculate final score (capped at 0.95)
        final_score = min(0.95, base_score * multiplier)

        # Map back to confidence level
        if final_score >= 0.8:
            adjusted_level = "high"
        elif final_score >= 0.6:
            adjusted_level = "medium"
        else:
            adjusted_level = "low"

        # Determine evidence strength
        evidence_strength = self._determine_evidence_strength(fact_count, multiplier)

        return {
            "stated_confidence": stated_confidence,
            "adjusted_confidence": adjusted_level,
            "confidence_score": round(final_score, 2),
            "evidence_strength": evidence_strength.value,
            "explanation": "; ".join(explanations),
            "fact_count": fact_count,
            "mitigating_count": len(mitigating_facts) if mitigating_facts else 0
        }

    def _assess_evidence_quality(self, fact_ids: List[str]) -> Dict[str, Any]:
        """Assess the quality of cited evidence."""
        has_quantified = False
        has_explicit = False

        for fid in fact_ids:
            fact = self.fact_store.get_fact(fid)
            if fact:
                content = fact.fact.lower() if hasattr(fact, 'fact') else str(fact).lower()
                # Check for quantified data
                if any(c.isdigit() for c in content) or any(kw in content for kw in ['%', 'percent', 'count', 'number']):
                    has_quantified = True
                # Check for explicit statements
                if any(kw in content for kw in ['confirmed', 'documented', 'stated', 'reported', 'verified']):
                    has_explicit = True

        multiplier = 1.0
        notes = []

        if has_quantified:
            multiplier *= self.EVIDENCE_MULTIPLIERS["quantified_data"]
            notes.append("quantified data")
        if has_explicit:
            multiplier *= self.EVIDENCE_MULTIPLIERS["explicit_statement"]
            notes.append("explicit statements")

        return {
            "multiplier": multiplier,
            "notes": "Includes " + ", ".join(notes) if notes else ""
        }

    def _assess_reasoning_quality(self, reasoning: str) -> Dict[str, Any]:
        """Assess the quality of the reasoning chain."""
        if not reasoning:
            return {"multiplier": 0.8, "notes": "No reasoning provided"}

        word_count = len(reasoning.split())

        # Check for logical connectors
        has_logic = any(kw in reasoning.lower() for kw in [
            "therefore", "because", "thus", "indicates", "suggests",
            "demonstrates", "implies", "consequently", "as a result"
        ])

        multiplier = 1.0
        notes = []

        if word_count < 20:
            multiplier *= 0.9
            notes.append("brief reasoning")
        elif word_count > 50:
            multiplier *= 1.05
            notes.append("detailed reasoning")

        if has_logic:
            multiplier *= 1.05
            notes.append("clear logic chain")

        return {
            "multiplier": multiplier,
            "notes": ", ".join(notes) if notes else ""
        }

    def _determine_evidence_strength(self, fact_count: int, multiplier: float) -> EvidenceStrength:
        """Determine overall evidence strength category."""
        if fact_count >= 3 and multiplier >= 1.1:
            return EvidenceStrength.STRONG
        elif fact_count >= 2 and multiplier >= 0.9:
            return EvidenceStrength.MODERATE
        elif fact_count >= 1:
            return EvidenceStrength.WEAK
        else:
            return EvidenceStrength.SPECULATIVE


# =============================================================================
# COUNTER-EVIDENCE TRACKING
# =============================================================================

@dataclass
class MitigatingEvidence:
    """
    Tracks facts that mitigate or counter a potential risk.

    Implements Point 90: Build counter-evidence tracking.
    """
    risk_id: str
    mitigating_fact_ids: List[str]
    mitigation_type: str  # "controls_in_place", "planned_remediation", "low_impact", "other"
    explanation: str
    impact_on_severity: str  # "none", "reduces_one_level", "reduces_to_low", "negates_risk"

    def to_dict(self) -> Dict:
        return {
            "risk_id": self.risk_id,
            "mitigating_fact_ids": self.mitigating_fact_ids,
            "mitigation_type": self.mitigation_type,
            "explanation": self.explanation,
            "impact_on_severity": self.impact_on_severity
        }


class CounterEvidenceTracker:
    """
    Tracks and manages counter-evidence for risks.

    Helps ensure balanced risk assessment by tracking facts
    that mitigate potential risks.
    """

    MITIGATION_TYPES = [
        "controls_in_place",      # Existing controls address the risk
        "planned_remediation",    # Remediation already planned
        "low_impact",             # Impact is contained/limited
        "low_likelihood",         # Likelihood is reduced by other factors
        "accepted_risk",          # Risk is known and accepted
        "compensating_control",   # Alternative controls in place
        "other"
    ]

    def __init__(self):
        self.mitigations: Dict[str, List[MitigatingEvidence]] = {}

    def add_mitigation(
        self,
        risk_id: str,
        mitigating_fact_ids: List[str],
        mitigation_type: str,
        explanation: str,
        impact: str = "none"
    ) -> MitigatingEvidence:
        """Add mitigating evidence for a risk."""
        mitigation = MitigatingEvidence(
            risk_id=risk_id,
            mitigating_fact_ids=mitigating_fact_ids,
            mitigation_type=mitigation_type,
            explanation=explanation,
            impact_on_severity=impact
        )

        if risk_id not in self.mitigations:
            self.mitigations[risk_id] = []
        self.mitigations[risk_id].append(mitigation)

        return mitigation

    def get_mitigations(self, risk_id: str) -> List[MitigatingEvidence]:
        """Get all mitigating evidence for a risk."""
        return self.mitigations.get(risk_id, [])

    def get_adjusted_severity(self, risk_id: str, original_severity: str) -> str:
        """
        Get adjusted severity based on mitigating evidence.

        Returns the original severity adjusted for mitigations.
        """
        mitigations = self.get_mitigations(risk_id)
        if not mitigations:
            return original_severity

        severity_order = ["low", "medium", "high", "critical"]
        current_idx = severity_order.index(original_severity) if original_severity in severity_order else 1

        for mitigation in mitigations:
            if mitigation.impact_on_severity == "negates_risk":
                return "low"  # Risk is effectively negated
            elif mitigation.impact_on_severity == "reduces_to_low":
                current_idx = 0
            elif mitigation.impact_on_severity == "reduces_one_level":
                current_idx = max(0, current_idx - 1)

        return severity_order[current_idx]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked mitigations."""
        total = sum(len(m) for m in self.mitigations.values())
        by_type = {}
        by_impact = {}

        for risk_id, mitigation_list in self.mitigations.items():
            for m in mitigation_list:
                by_type[m.mitigation_type] = by_type.get(m.mitigation_type, 0) + 1
                by_impact[m.impact_on_severity] = by_impact.get(m.impact_on_severity, 0) + 1

        return {
            "total_mitigations": total,
            "risks_with_mitigations": len(self.mitigations),
            "by_type": by_type,
            "by_impact": by_impact
        }


# =============================================================================
# WORK ITEM DEPENDENCY DETECTION
# =============================================================================

class DependencyDetector:
    """
    Detects dependencies between work items.

    Implements Point 93: Add work item dependency detection.
    """

    # Keywords that indicate dependencies
    DEPENDENCY_PATTERNS = {
        "requires_infrastructure": [
            "after network", "once connectivity", "requires vpn",
            "after firewall", "pending infrastructure"
        ],
        "requires_identity": [
            "after ad", "once sso", "requires identity",
            "after directory", "pending authentication"
        ],
        "requires_security": [
            "after security review", "once compliance",
            "requires security", "pending audit"
        ],
        "requires_data": [
            "after data migration", "once data", "requires database",
            "pending data transfer"
        ],
        "requires_application": [
            "after application", "once system", "requires app",
            "pending deployment"
        ],
        "requires_business": [
            "after business approval", "pending stakeholder",
            "requires sign-off", "once decision"
        ]
    }

    # Phase-based implicit dependencies
    PHASE_ORDER = [
        WorkItemPhase.PRE_CLOSE,
        WorkItemPhase.DAY_1,
        WorkItemPhase.DAY_30,
        WorkItemPhase.DAY_100,
        WorkItemPhase.POST_100,
        WorkItemPhase.ONGOING
    ]

    def detect_dependencies(
        self,
        work_item: Dict[str, Any],
        all_work_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect dependencies for a work item.

        Args:
            work_item: The work item to analyze
            all_work_items: All work items in the session

        Returns:
            Dict with detected dependencies and blocking items
        """
        title = work_item.get("title", "").lower()
        description = work_item.get("description", "").lower()
        domain = work_item.get("domain", "")
        phase = work_item.get("phase", "Day_100")

        full_text = f"{title} {description}"

        dependencies = {
            "explicit": work_item.get("dependencies", []),
            "inferred": [],
            "blocking": [],
            "blocked_by": [],
            "dependency_types": []
        }

        # Check for keyword-based dependencies
        for dep_type, patterns in self.DEPENDENCY_PATTERNS.items():
            if any(p in full_text for p in patterns):
                dependencies["dependency_types"].append(dep_type)

        # Find work items that might block this one
        for other_wi in all_work_items:
            if other_wi.get("finding_id") == work_item.get("finding_id"):
                continue

            # Check if other item is in an earlier phase
            other_phase = other_wi.get("phase", "Day_100")
            if self._phase_before(other_phase, phase):
                # Check domain relevance
                if self._is_dependency_candidate(work_item, other_wi):
                    dependencies["inferred"].append({
                        "work_item_id": other_wi.get("finding_id"),
                        "title": other_wi.get("title"),
                        "reason": f"Earlier phase ({other_phase}) in related domain"
                    })

        # Check triggered_by_risks overlap
        this_risks = set(work_item.get("triggered_by_risks", []))
        for other_wi in all_work_items:
            if other_wi.get("finding_id") == work_item.get("finding_id"):
                continue

            other_risks = set(other_wi.get("triggered_by_risks", []))
            shared_risks = this_risks & other_risks
            if shared_risks:
                # Items addressing same risks may be related
                other_phase = other_wi.get("phase", "Day_100")
                if self._phase_before(other_phase, phase):
                    dependencies["blocked_by"].append({
                        "work_item_id": other_wi.get("finding_id"),
                        "title": other_wi.get("title"),
                        "shared_risks": list(shared_risks)
                    })

        return dependencies

    def _phase_before(self, phase1: str, phase2: str) -> bool:
        """Check if phase1 comes before phase2."""
        try:
            p1_enum = WorkItemPhase(phase1) if isinstance(phase1, str) else phase1
            p2_enum = WorkItemPhase(phase2) if isinstance(phase2, str) else phase2
            return self.PHASE_ORDER.index(p1_enum) < self.PHASE_ORDER.index(p2_enum)
        except (ValueError, KeyError):
            return False

    def _is_dependency_candidate(
        self,
        work_item: Dict[str, Any],
        other_wi: Dict[str, Any]
    ) -> bool:
        """Check if other_wi could be a dependency for work_item."""
        domain = work_item.get("domain", "")
        other_domain = other_wi.get("domain", "")

        # Infrastructure dependencies are common
        if other_domain == "infrastructure":
            return True

        # Network is often a prerequisite
        if other_domain == "network" and domain in ["applications", "cybersecurity"]:
            return True

        # Identity is needed for many things
        if other_domain == "identity_access" and domain in ["applications", "cybersecurity"]:
            return True

        # Same domain items in earlier phases
        if domain == other_domain:
            return True

        return False

    def build_dependency_graph(
        self,
        work_items: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Build a full dependency graph for all work items.

        Returns:
            Dict mapping work_item_id to list of IDs it depends on
        """
        graph = {}

        for wi in work_items:
            wi_id = wi.get("finding_id")
            deps = self.detect_dependencies(wi, work_items)

            # Combine explicit and inferred dependencies
            all_deps = set(deps.get("explicit", []))
            for inferred in deps.get("inferred", []):
                all_deps.add(inferred.get("work_item_id"))
            for blocked in deps.get("blocked_by", []):
                all_deps.add(blocked.get("work_item_id"))

            graph[wi_id] = list(all_deps)

        return graph


# =============================================================================
# EFFORT ESTIMATION
# =============================================================================

class EffortEstimator:
    """
    Estimates effort for work items using T-shirt sizing.

    Implements Point 94: Build effort estimation logic.
    """

    def estimate_effort(
        self,
        work_item: Dict[str, Any],
        facts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Estimate effort size for a work item.

        Args:
            work_item: The work item to estimate
            facts: Optional list of related facts for context

        Returns:
            Dict with size, confidence, and rationale
        """
        title = work_item.get("title", "").lower()
        description = work_item.get("description", "").lower()
        cost_estimate = work_item.get("cost_estimate", "25k_to_100k")

        full_text = f"{title} {description}"

        # Start with cost-based estimate
        size = self._size_from_cost(cost_estimate)
        rationale = [f"Based on cost estimate: {cost_estimate}"]

        # Check for size indicators in text
        text_size = self._size_from_text(full_text)
        if text_size:
            size = self._combine_sizes(size, text_size)
            rationale.append(f"Adjusted based on scope keywords")

        # Check for count indicators
        count_size = self._size_from_counts(full_text, facts)
        if count_size:
            size = self._combine_sizes(size, count_size)
            rationale.append(f"Adjusted based on quantity indicators")

        # Get effort details
        effort_details = self._get_effort_details(size)

        return {
            "size": size.value,
            "duration_estimate": effort_details["duration"],
            "team_size_estimate": effort_details["team_size"],
            "rationale": "; ".join(rationale),
            "confidence": "medium"  # Can be improved with more data
        }

    def _size_from_cost(self, cost_estimate: str) -> EffortSize:
        """Map cost estimate to effort size."""
        mapping = {
            "under_25k": EffortSize.S,
            "25k_to_100k": EffortSize.M,
            "100k_to_500k": EffortSize.L,
            "500k_to_1m": EffortSize.XL,
            "over_1m": EffortSize.XXL
        }
        return mapping.get(cost_estimate, EffortSize.M)

    def _size_from_text(self, text: str) -> Optional[EffortSize]:
        """Extract effort size from text indicators."""
        for size, keywords in EFFORT_INDICATORS.items():
            if any(kw in text for kw in keywords):
                return EffortSize[size.upper()]
        return None

    def _size_from_counts(
        self,
        text: str,
        facts: Optional[List[Dict[str, Any]]]
    ) -> Optional[EffortSize]:
        """Estimate size based on quantity mentions."""
        # Look for numbers in text
        numbers = re.findall(r'\d+', text)
        if not numbers:
            return None

        # Try to match with thresholds
        for count_type, thresholds in COUNT_THRESHOLDS.items():
            if count_type in text:
                for num_str in numbers:
                    try:
                        num = int(num_str)
                        for threshold, size in thresholds:
                            if num >= threshold:
                                return EffortSize[size]
                    except ValueError:
                        continue
        return None

    def _combine_sizes(self, size1: EffortSize, size2: EffortSize) -> EffortSize:
        """Combine two size estimates (take the larger)."""
        sizes = [EffortSize.XS, EffortSize.S, EffortSize.M, EffortSize.L, EffortSize.XL, EffortSize.XXL]
        idx1 = sizes.index(size1)
        idx2 = sizes.index(size2)
        return sizes[max(idx1, idx2)]

    def _get_effort_details(self, size: EffortSize) -> Dict[str, str]:
        """Get duration and team size for an effort size."""
        details = {
            EffortSize.XS: {"duration": "< 1 week", "team_size": "1-2 people"},
            EffortSize.S: {"duration": "1-2 weeks", "team_size": "2-3 people"},
            EffortSize.M: {"duration": "2-4 weeks", "team_size": "3-5 people"},
            EffortSize.L: {"duration": "1-2 months", "team_size": "5-10 people"},
            EffortSize.XL: {"duration": "2-4 months", "team_size": "10+ people"},
            EffortSize.XXL: {"duration": "4+ months", "team_size": "Large program team"},
        }
        return details.get(size, details[EffortSize.M])


# =============================================================================
# OWNER SUGGESTION
# =============================================================================

class OwnerSuggester:
    """
    Suggests appropriate owner for work items.

    Implements Point 95: Implement owner suggestion.
    """

    def suggest_owner(
        self,
        work_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Suggest an owner for a work item.

        Args:
            work_item: The work item to suggest owner for

        Returns:
            Dict with suggested_owner, confidence, and rationale
        """
        domain = work_item.get("domain", "")
        phase = work_item.get("phase", "Day_100")
        title = work_item.get("title", "").lower()
        description = work_item.get("description", "").lower()
        current_owner = work_item.get("owner_type", "")

        full_text = f"{title} {description}"

        # Start with domain default
        suggested = OWNER_RULES["domain_defaults"].get(domain, OwnerType.TARGET_IT)
        rationale = [f"Default for {domain} domain"]
        confidence = "medium"

        # Check keyword overrides
        for owner_type, keywords in OWNER_RULES["keyword_overrides"].items():
            if any(kw in full_text for kw in keywords):
                suggested = owner_type
                rationale = [f"Keyword match for {owner_type.value}"]
                confidence = "high"
                break

        # Check phase adjustments
        try:
            phase_enum = WorkItemPhase(phase)
            if phase_enum in OWNER_RULES["phase_adjustments"]:
                # Phase override for early phases
                phase_owner = OWNER_RULES["phase_adjustments"][phase_enum]
                if suggested != phase_owner:
                    suggested = phase_owner
                    rationale.append(f"Adjusted for {phase} phase")
        except ValueError:
            pass

        return {
            "suggested_owner": suggested.value,
            "current_owner": current_owner,
            "confidence": confidence,
            "rationale": "; ".join(rationale),
            "alternatives": self._get_alternatives(suggested, domain)
        }

    def _get_alternatives(
        self,
        primary: OwnerType,
        domain: str
    ) -> List[str]:
        """Get alternative owner suggestions."""
        all_owners = list(OwnerType)
        alternatives = []

        # Add domain default if different
        domain_default = OWNER_RULES["domain_defaults"].get(domain)
        if domain_default and domain_default != primary:
            alternatives.append(domain_default.value)

        # Always include Shared as an option
        if primary != OwnerType.SHARED:
            alternatives.append(OwnerType.SHARED.value)

        # Add Integration Team for complex items
        if primary not in [OwnerType.INTEGRATION_TEAM, OwnerType.SHARED]:
            alternatives.append(OwnerType.INTEGRATION_TEAM.value)

        return alternatives[:3]  # Return top 3 alternatives


# =============================================================================
# RISK TO WORK ITEM MAPPER
# =============================================================================

class RiskWorkItemMapper:
    """
    Maps risks to work items and validates the relationship.

    Implements Point 91: Create clear risk-to-work-item mapping.
    """

    def validate_mapping(
        self,
        risks: List[Dict[str, Any]],
        work_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate that all risks have associated work items and vice versa.

        Returns:
            Dict with validation results and orphan items
        """
        results = {
            "is_valid": True,
            "risks_without_work_items": [],
            "work_items_without_risks": [],
            "risk_to_work_item_map": {},
            "coverage_rate": 0.0
        }

        # Build risk → work_items map
        risk_ids = {r.get("finding_id"): r for r in risks}
        wi_to_risks = {}

        for wi in work_items:
            wi_id = wi.get("finding_id")
            triggered_by = wi.get("triggered_by_risks", [])

            if not triggered_by:
                results["work_items_without_risks"].append({
                    "work_item_id": wi_id,
                    "title": wi.get("title")
                })
                results["is_valid"] = False

            for risk_id in triggered_by:
                if risk_id not in results["risk_to_work_item_map"]:
                    results["risk_to_work_item_map"][risk_id] = []
                results["risk_to_work_item_map"][risk_id].append(wi_id)

        # Check for risks without work items
        for risk_id, risk in risk_ids.items():
            if risk_id not in results["risk_to_work_item_map"]:
                severity = risk.get("severity", "medium")
                # High and critical risks should have remediation work items
                if severity in ["high", "critical"]:
                    results["risks_without_work_items"].append({
                        "risk_id": risk_id,
                        "title": risk.get("title"),
                        "severity": severity
                    })
                    results["is_valid"] = False

        # Calculate coverage
        risks_with_wi = len(results["risk_to_work_item_map"])
        total_risks = len(risks)
        results["coverage_rate"] = risks_with_wi / total_risks if total_risks > 0 else 1.0

        return results

    def suggest_work_items_for_risk(
        self,
        risk: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Suggest work items that should be created for a risk.

        Returns:
            List of suggested work item templates
        """
        suggestions = []
        severity = risk.get("severity", "medium")
        domain = risk.get("domain", "")
        title = risk.get("title", "")

        # High/critical risks need remediation
        if severity in ["high", "critical"]:
            suggestions.append({
                "title": f"Remediate: {title}",
                "phase": "Day_100" if severity == "high" else "Day_1",
                "type": "remediation"
            })

        # All risks should have assessment/monitoring
        suggestions.append({
            "title": f"Assess and monitor: {title}",
            "phase": "Day_100",
            "type": "assessment"
        })

        return suggestions


# =============================================================================
# TRIAGE MANAGER - COMBINES ALL COMPONENTS
# =============================================================================

class TriageManager:
    """
    Central manager for triage flow operations.

    Combines all triage components for easy use.
    """

    def __init__(self, fact_store=None):
        self.fact_store = fact_store
        self.risk_validator = RiskValidator(fact_store)
        self.confidence_scorer = ConfidenceScorer(fact_store)
        self.counter_evidence = CounterEvidenceTracker()
        self.dependency_detector = DependencyDetector()
        self.effort_estimator = EffortEstimator()
        self.owner_suggester = OwnerSuggester()
        self.risk_wi_mapper = RiskWorkItemMapper()

    def process_risk(
        self,
        risk_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a risk through the full triage pipeline.

        Returns enriched risk data with validation, confidence, etc.
        """
        result = dict(risk_data)

        # Validate
        validation = self.risk_validator.validate_risk(risk_data)
        result["_validation"] = {
            "is_valid": validation.is_valid,
            "warnings": validation.warnings,
            "errors": validation.errors,
            "suggestions": validation.suggestions
        }

        # Calculate confidence
        confidence = self.confidence_scorer.calculate_confidence(
            stated_confidence=risk_data.get("confidence", "medium"),
            based_on_facts=risk_data.get("based_on_facts", []),
            reasoning=risk_data.get("reasoning", ""),
            mitigating_facts=risk_data.get("mitigating_facts", [])
        )
        result["_confidence"] = confidence

        # Adjust confidence if validation found issues
        if validation.confidence_adjustment > 0:
            result["_confidence"]["adjusted_for_validation"] = True
            result["_confidence"]["confidence_score"] *= validation.confidence_adjustment

        return result

    def process_work_item(
        self,
        work_item: Dict[str, Any],
        all_work_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a work item through the full triage pipeline.

        Returns enriched work item data with dependencies, effort, owner suggestion.
        """
        result = dict(work_item)

        # Detect dependencies
        dependencies = self.dependency_detector.detect_dependencies(
            work_item, all_work_items
        )
        result["_dependencies"] = dependencies

        # Estimate effort
        effort = self.effort_estimator.estimate_effort(work_item)
        result["_effort"] = effort

        # Suggest owner
        owner = self.owner_suggester.suggest_owner(work_item)
        result["_owner_suggestion"] = owner

        return result

    def validate_triage_flow(
        self,
        risks: List[Dict[str, Any]],
        work_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate the entire triage flow (risks → work items).

        Returns validation summary with issues and suggestions.
        """
        # Validate risk-to-work-item mapping
        mapping_validation = self.risk_wi_mapper.validate_mapping(risks, work_items)

        # Validate each risk
        risk_validations = []
        for risk in risks:
            v = self.risk_validator.validate_risk(risk)
            if not v.is_valid or v.warnings:
                risk_validations.append({
                    "risk_id": risk.get("finding_id"),
                    "is_valid": v.is_valid,
                    "issues": v.errors + v.warnings
                })

        # Build dependency graph
        dependency_graph = self.dependency_detector.build_dependency_graph(work_items)

        return {
            "mapping_validation": mapping_validation,
            "risk_validations": risk_validations,
            "dependency_graph": dependency_graph,
            "summary": {
                "total_risks": len(risks),
                "total_work_items": len(work_items),
                "risks_with_issues": len(risk_validations),
                "orphan_risks": len(mapping_validation.get("risks_without_work_items", [])),
                "orphan_work_items": len(mapping_validation.get("work_items_without_risks", []))
            }
        }


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    # Test the triage flow components
    print("=== Triage Flow Module Test ===\n")

    # Test RiskValidator
    print("1. Risk Validator Test")
    validator = RiskValidator()

    weak_risk = {
        "based_on_facts": [],
        "severity": "high",
        "reasoning": "This is bad."
    }
    result = validator.validate_risk(weak_risk)
    print(f"   Weak risk valid: {result.is_valid}")
    print(f"   Errors: {result.errors}")
    print(f"   Warnings: {result.warnings}")

    strong_risk = {
        "based_on_facts": ["F-INFRA-001", "F-INFRA-002", "F-NET-001"],
        "severity": "high",
        "reasoning": "Based on the infrastructure facts showing aging systems and network analysis indicating vulnerabilities, this represents a significant risk because..."
    }
    result = validator.validate_risk(strong_risk)
    print(f"   Strong risk valid: {result.is_valid}")
    print()

    # Test ConfidenceScorer
    print("2. Confidence Scorer Test")
    scorer = ConfidenceScorer()

    conf = scorer.calculate_confidence(
        stated_confidence="high",
        based_on_facts=["F-1", "F-2", "F-3"],
        reasoning="The evidence clearly shows that these three independent facts all point to the same conclusion, therefore..."
    )
    print(f"   Stated: high, Adjusted: {conf['adjusted_confidence']}")
    print(f"   Score: {conf['confidence_score']}")
    print(f"   Evidence strength: {conf['evidence_strength']}")
    print()

    # Test EffortEstimator
    print("3. Effort Estimator Test")
    estimator = EffortEstimator()

    work_item = {
        "title": "Migrate ERP system to new platform",
        "description": "Full SAP S/4HANA migration program",
        "cost_estimate": "over_1m"
    }
    effort = estimator.estimate_effort(work_item)
    print(f"   Size: {effort['size']}")
    print(f"   Duration: {effort['duration_estimate']}")
    print(f"   Team: {effort['team_size_estimate']}")
    print()

    # Test OwnerSuggester
    print("4. Owner Suggester Test")
    suggester = OwnerSuggester()

    wi = {
        "domain": "infrastructure",
        "phase": "Day_1",
        "title": "Establish network connectivity to buyer infrastructure",
        "description": "Connect target network to buyer's VPN"
    }
    owner = suggester.suggest_owner(wi)
    print(f"   Suggested: {owner['suggested_owner']}")
    print(f"   Confidence: {owner['confidence']}")
    print(f"   Rationale: {owner['rationale']}")
    print()

    # Test TriageManager
    print("5. Full Triage Manager Test")
    manager = TriageManager()

    test_risks = [
        {"finding_id": "R-001", "title": "EOL Infrastructure", "severity": "high", "based_on_facts": ["F-1", "F-2"]},
        {"finding_id": "R-002", "title": "Weak Security", "severity": "critical", "based_on_facts": ["F-3"]}
    ]
    test_wis = [
        {"finding_id": "WI-001", "title": "Replace servers", "triggered_by_risks": ["R-001"], "phase": "Day_100"},
        {"finding_id": "WI-002", "title": "Security remediation", "triggered_by_risks": ["R-002"], "phase": "Day_1"}
    ]

    validation = manager.validate_triage_flow(test_risks, test_wis)
    print(f"   Total risks: {validation['summary']['total_risks']}")
    print(f"   Total work items: {validation['summary']['total_work_items']}")
    print(f"   Coverage rate: {validation['mapping_validation']['coverage_rate']:.0%}")
    print()

    print("=== Triage Flow Module Tests Complete ===")
