"""
Reasoning Tools for V2 Architecture

Tools used by Reasoning agents to analyze facts and produce findings.
All findings MUST cite fact IDs from the FactStore (evidence chain).

Tool Functions:
- identify_risk: Create a risk with fact citations
- create_strategic_consideration: Strategic observation with citations
- create_work_item: Integration work item with citations
- create_recommendation: Deal recommendation with citations
- complete_reasoning: Signal reasoning phase complete
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging
import re
import threading
import hashlib


def _generate_timestamp() -> str:
    """
    Generate ISO format timestamp and validate it.

    Returns:
        ISO format timestamp string (YYYY-MM-DDTHH:MM:SS.ffffff)

    Raises:
        ValueError: If timestamp format is invalid
    """
    timestamp = datetime.now().isoformat()
    # Validate ISO format: YYYY-MM-DDTHH:MM:SS[.ffffff][+HH:MM]
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?([+-]\d{2}:\d{2})?$'
    if not re.match(iso_pattern, timestamp):
        raise ValueError(f"Generated timestamp has invalid format: {timestamp}")
    return timestamp


def _normalize_string(s: str) -> str:
    """
    Normalize a string for stable ID generation.

    - Lowercase
    - Remove extra whitespace
    - Strip punctuation (except underscores)
    """
    if not s:
        return ""
    # Lowercase and strip
    s = s.lower().strip()
    # Replace multiple spaces with single space
    s = re.sub(r'\s+', ' ', s)
    # Remove punctuation except underscores
    s = re.sub(r'[^\w\s]', '', s)
    return s


def _generate_stable_id(prefix: str, domain: str, title: str, owner: Optional[str] = None) -> str:
    """
    Generate a stable, deterministic ID based on content hash.

    This ensures the same item always gets the same ID, preventing duplicates
    when parallel agents create the same finding independently.

    Args:
        prefix: ID prefix (WI, R, SC, REC)
        domain: The domain name
        title: The finding title
        owner: Optional owner type (for work items)

    Returns:
        Stable ID in format PREFIX-XXXX (e.g., WI-a3f2)
    """
    # Build content string for hashing
    parts = [
        _normalize_string(domain),
        _normalize_string(title),
    ]
    if owner:
        parts.append(_normalize_string(owner))

    content = "|".join(parts)

    # Generate short hash (4 hex chars = 65536 possibilities)
    # For a typical DD run with <100 items per type, collision risk is negligible
    full_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    short_hash = full_hash[:4]

    return f"{prefix}-{short_hash}"

if TYPE_CHECKING:
    from tools_v2.fact_store import FactStore

logger = logging.getLogger(__name__)

# =============================================================================
# STANDARDIZED ENUMS
# =============================================================================

ALL_DOMAINS = [
    "infrastructure",
    "network",
    "cybersecurity",
    "applications",
    "organization",
    "identity_access",
    "cross-domain"
]

SEVERITY_LEVELS = ["critical", "high", "medium", "low"]
CONFIDENCE_LEVELS = ["high", "medium", "low"]
WORK_PHASES = ["Day_1", "Day_100", "Post_100"]
PRIORITY_LEVELS = ["critical", "high", "medium", "low"]

# M&A Lenses - every finding must connect to at least one
MNA_LENSES = ["day_1_continuity", "tsa_exposure", "separation_complexity", "synergy_opportunity", "cost_driver"]

# Cost estimate ranges for work items
COST_RANGES = [
    "under_25k",      # < $25,000
    "25k_to_100k",    # $25,000 - $100,000
    "100k_to_500k",   # $100,000 - $500,000
    "500k_to_1m",     # $500,000 - $1,000,000
    "over_1m"         # > $1,000,000
]

# Mapping cost ranges to numeric values for aggregation
COST_RANGE_VALUES = {
    "under_25k": {"low": 0, "high": 25000},
    "25k_to_100k": {"low": 25000, "high": 100000},
    "100k_to_500k": {"low": 100000, "high": 500000},
    "500k_to_1m": {"low": 500000, "high": 1000000},
    "over_1m": {"low": 1000000, "high": 2500000},  # Cap at 2.5M for estimation
}

# Cost calibration guidance - typical items at each range
# Use this to calibrate estimates and ensure consistency
COST_CALIBRATION = {
    "under_25k": [
        "Simple tool deployment (single product, existing infrastructure)",
        "Basic configuration/policy changes",
        "Small network changes (1-2 devices)",
        "Simple automation/script development",
        "Basic documentation creation",
        "Single-user application migration",
    ],
    "25k_to_100k": [
        "MFA rollout (using existing identity platform)",
        "Site-to-site VPN setup",
        "Single site network connectivity",
        "Small application migration (1-5 simple apps)",
        "Active Directory trust relationship",
        "Basic DR capability for critical apps",
        "Small server migration (5-15 servers)",
        "EDR deployment (50-100 endpoints)",
    ],
    "100k_to_500k": [
        "VMware upgrade (small environment <100 VMs)",
        "EDR deployment (200-500 endpoints)",
        "SIEM implementation",
        "Identity platform migration (small org <500 users)",
        "Network architecture refresh (single site)",
        "Cloud landing zone / foundation setup",
        "Medium application migration (5-15 apps)",
        "Storage system migration or refresh",
        "Security program foundation buildout",
    ],
    "500k_to_1m": [
        "VMware upgrade (100-500 VMs)",
        "Identity platform migration (500-2000 users)",
        "Data center consolidation (single site exit)",
        "Large application migration program (15-30 apps)",
        "Network architecture redesign (multi-site)",
        "Security transformation initiative",
        "ERP customization or minor upgrade",
        "Cloud migration program (lift-and-shift)",
    ],
    "over_1m": [
        "ERP migration (SAP S/4HANA, Oracle Cloud)",
        "Data center exit/full migration",
        "Enterprise cloud transformation",
        "Major M&A IT integration program",
        "Enterprise security transformation",
        "Custom application rewrite/modernization",
        "Full infrastructure modernization",
    ]
}


# =============================================================================
# REASONING OUTPUT CLASSES
# =============================================================================

@dataclass
class Risk:
    """A risk identified through reasoning about facts."""
    finding_id: str
    domain: str
    title: str
    description: str
    category: str
    severity: str
    integration_dependent: bool  # True if only relevant if deal proceeds
    mitigation: str
    based_on_facts: List[str]  # Fact IDs that support this finding
    confidence: str
    reasoning: str  # Explain HOW facts led to this conclusion
    mna_lens: str = ""  # Primary M&A lens (day_1_continuity, tsa_exposure, etc.)
    mna_implication: str = ""  # Specific deal implication (1-2 sentences)
    timeline: Optional[str] = None  # When this becomes critical
    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Risk":
        return cls(**data)


@dataclass
class StrategicConsideration:
    """A strategic observation about the deal."""
    finding_id: str
    domain: str
    title: str
    description: str
    lens: str  # buyer_alignment, tsa, synergy, value_creation, etc.
    implication: str  # What this means for the deal
    based_on_facts: List[str]  # Fact IDs that support this finding
    confidence: str
    reasoning: str  # Explain HOW facts led to this conclusion
    mna_lens: str = ""  # Primary M&A lens (day_1_continuity, tsa_exposure, etc.)
    mna_implication: str = ""  # Specific deal implication (1-2 sentences)
    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "StrategicConsideration":
        return cls(**data)


@dataclass
class WorkItem:
    """An integration work item triggered by findings."""
    finding_id: str
    domain: str
    title: str
    description: str
    phase: str  # Day_1, Day_100, Post_100
    priority: str
    owner_type: str  # buyer, target, shared, vendor
    triggered_by: List[str]  # Fact IDs that necessitate this work
    based_on_facts: List[str]  # Additional supporting fact IDs
    confidence: str
    reasoning: str  # Explain WHY this work is needed

    # NEW: Cost estimation
    cost_estimate: str  # One of COST_RANGES: under_25k, 25k_to_100k, etc.

    # NEW: Link to risks that this work item addresses
    triggered_by_risks: List[str] = field(default_factory=list)  # Risk IDs (R-001, R-002)

    # M&A Framing
    mna_lens: str = ""  # Primary M&A lens (day_1_continuity, tsa_exposure, etc.)
    mna_implication: str = ""  # Specific deal implication (1-2 sentences)

    dependencies: List[str] = field(default_factory=list)  # Other work items
    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkItem":
        return cls(**data)

    def get_cost_range_values(self) -> Dict[str, int]:
        """Get the numeric low/high values for this work item's cost estimate."""
        return COST_RANGE_VALUES.get(self.cost_estimate, {"low": 0, "high": 0})


@dataclass
class Recommendation:
    """A recommendation for the deal team."""
    finding_id: str
    domain: str
    title: str
    description: str
    action_type: str  # negotiate, budget, investigate, accept, mitigate
    urgency: str  # immediate, pre-close, post-close
    rationale: str
    based_on_facts: List[str]  # Fact IDs that support this recommendation
    confidence: str
    reasoning: str  # Explain the reasoning chain
    mna_lens: str = ""  # Primary M&A lens (day_1_continuity, tsa_exposure, etc.)
    mna_implication: str = ""  # Specific deal implication (1-2 sentences)
    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Recommendation":
        return cls(**data)


# =============================================================================
# FUNCTION STORY (imported from template)
# =============================================================================

# Import FunctionStory from the template module
try:
    from prompts.shared.function_story_template import FunctionStory
except ImportError:
    # Fallback if import fails - define minimal version
    @dataclass
    class FunctionStory:
        """A structured narrative story for an IT function/team."""
        function_name: str
        domain: str
        day_to_day: str
        strengths: List[str]
        constraints: List[str]
        upstream_dependencies: List[str]
        downstream_dependents: List[str]
        mna_implication: str
        mna_lens: str
        based_on_facts: List[str]
        inferences: List[str]
        confidence: str = "medium"
        created_at: str = field(default_factory=lambda: _generate_timestamp())

        def to_dict(self) -> Dict:
            return asdict(self)

        def to_markdown(self) -> str:
            return f"### {self.function_name}\n{self.day_to_day}"


# =============================================================================
# REASONING STORE
# =============================================================================

class ReasoningStore:
    """
    Stores reasoning outputs (findings) with fact citations.

    Similar pattern to FactStore but for analysis outputs.
    Validates fact citations against the source FactStore.
    """

    def __init__(self, fact_store: "FactStore" = None):
        self.fact_store = fact_store
        self.risks: List[Risk] = []
        self.strategic_considerations: List[StrategicConsideration] = []
        self.work_items: List[WorkItem] = []
        self.recommendations: List[Recommendation] = []
        self.function_stories: List[FunctionStory] = []  # Phase 3: Function narratives
        self._counters: Dict[str, int] = {}  # Kept for backwards compatibility
        self._used_ids: Set[str] = set()  # Track all used IDs to prevent duplicates
        self.metadata: Dict[str, Any] = {
            "created_at": _generate_timestamp(),
            "version": "2.2"  # Version bump for function stories
        }
        # Thread safety: Lock for all mutating operations
        self._lock = threading.RLock()

    def _generate_id(self, prefix: str) -> str:
        """
        Generate unique finding ID using counter (legacy method).

        NOTE: Must be called within self._lock context.
        This method modifies self._counters and is not thread-safe on its own.

        Prefer _generate_stable_id_safe() for new code.
        """
        if prefix not in self._counters:
            self._counters[prefix] = 0
        self._counters[prefix] += 1
        new_id = f"{prefix}-{self._counters[prefix]:03d}"
        self._used_ids.add(new_id)
        return new_id

    def _generate_stable_id_safe(
        self,
        prefix: str,
        domain: str,
        title: str,
        owner: Optional[str] = None
    ) -> str:
        """
        Generate a stable, deterministic ID with collision handling.

        This creates IDs based on content hash, ensuring the same finding
        always gets the same ID. If a collision occurs (same hash but
        different content already exists), adds a numeric suffix.

        NOTE: Must be called within self._lock context.

        Args:
            prefix: ID prefix (WI, R, SC, REC)
            domain: The domain name
            title: The finding title
            owner: Optional owner type

        Returns:
            Stable unique ID
        """
        base_id = _generate_stable_id(prefix, domain, title, owner)

        # Check for collision
        if base_id not in self._used_ids:
            self._used_ids.add(base_id)
            return base_id

        # Handle collision by adding numeric suffix
        suffix = 2
        while f"{base_id}-{suffix}" in self._used_ids:
            suffix += 1
        final_id = f"{base_id}-{suffix}"
        self._used_ids.add(final_id)
        logger.debug(f"ID collision detected for {base_id}, using {final_id}")
        return final_id

    def validate_fact_citations(self, fact_ids: List[str], fail_fast: bool = False) -> Dict[str, Any]:
        """
        Validate that cited fact IDs exist in FactStore.
        
        Args:
            fact_ids: List of fact/gap IDs to validate
            fail_fast: If True, raise ValueError on invalid citations (default: False, just warn)
        
        Returns:
            Dict with valid, invalid, and validation_rate
        
        Raises:
            ValueError: If fail_fast=True and invalid citations found
        """
        if not self.fact_store:
            if fail_fast and fact_ids:
                raise ValueError("Cannot validate citations: FactStore not available")
            return {"valid": fact_ids, "invalid": [], "validation_rate": 1.0}
        
        result = self.fact_store.validate_fact_citations(fact_ids)
        
        if fail_fast and result.get("invalid"):
            invalid = result["invalid"]
            raise ValueError(
                f"Invalid fact/gap citations found: {invalid}. "
                f"Validation rate: {result['validation_rate']:.1%}"
            )
        
        return result

    def add_risk(self, **kwargs) -> str:
        """Add a risk and return its ID (uses stable hashing)."""
        with self._lock:
            # Generate stable ID based on domain + title
            domain = kwargs.get("domain", "unknown")
            title = kwargs.get("title", "")
            risk_id = self._generate_stable_id_safe("R", domain, title)
            kwargs["finding_id"] = risk_id

            # Validate fact/gap citations (fail fast if configured)
            based_on = kwargs.get("based_on_facts", [])
            try:
                # Check if fail_fast is enabled via config
                from config_v2 import ENABLE_CITATION_VALIDATION
                fail_fast = ENABLE_CITATION_VALIDATION
            except ImportError:
                fail_fast = False

            validation = self.validate_fact_citations(based_on, fail_fast=fail_fast)
            if validation.get("invalid") and not fail_fast:
                logger.warning(f"Risk {risk_id} cites unknown IDs: {validation['invalid']}")

            risk = Risk(**kwargs)
            self.risks.append(risk)
            logger.debug(f"Added risk {risk_id}: {risk.title}")
            return risk_id

    def add_strategic_consideration(self, **kwargs) -> str:
        """Add a strategic consideration and return its ID (uses stable hashing)."""
        with self._lock:
            # Generate stable ID based on domain + title
            domain = kwargs.get("domain", "unknown")
            title = kwargs.get("title", "")
            sc_id = self._generate_stable_id_safe("SC", domain, title)
            kwargs["finding_id"] = sc_id

            # Validate fact/gap citations
            based_on = kwargs.get("based_on_facts", [])
            validation = self.validate_fact_citations(based_on)
            if validation.get("invalid"):
                logger.warning(f"Strategic consideration {sc_id} cites unknown IDs: {validation['invalid']}")

            sc = StrategicConsideration(**kwargs)
            self.strategic_considerations.append(sc)
            logger.debug(f"Added strategic consideration {sc_id}: {sc.title}")
            return sc_id

    def add_work_item(self, **kwargs) -> str:
        """Add a work item and return its ID (uses stable hashing with domain+title+owner)."""
        with self._lock:
            # Generate stable ID based on domain + title + owner_type
            domain = kwargs.get("domain", "unknown")
            title = kwargs.get("title", "")
            owner_type = kwargs.get("owner_type", "")
            wi_id = self._generate_stable_id_safe("WI", domain, title, owner_type)
            kwargs["finding_id"] = wi_id

            # Validate fact/gap citations
            triggered_by = kwargs.get("triggered_by", [])
            based_on = kwargs.get("based_on_facts", [])
            all_ids = list(set(triggered_by + based_on))
            validation = self.validate_fact_citations(all_ids)
            if validation.get("invalid"):
                logger.warning(f"Work item {wi_id} cites unknown IDs: {validation['invalid']}")

            # Validate cost estimate - fail fast instead of silent default
            cost_estimate = kwargs.get("cost_estimate")
            if not cost_estimate:
                raise ValueError(f"Work item {wi_id} missing required cost_estimate")
            if cost_estimate not in COST_RANGES:
                raise ValueError(
                    f"Work item {wi_id} has invalid cost_estimate: {cost_estimate}. "
                    f"Must be one of: {', '.join(COST_RANGES)}"
                )

            # Ensure triggered_by_risks is a list
            if "triggered_by_risks" not in kwargs:
                kwargs["triggered_by_risks"] = []

            wi = WorkItem(**kwargs)
            self.work_items.append(wi)
            logger.debug(f"Added work item {wi_id}: {wi.title} (cost: {wi.cost_estimate})")
            return wi_id

    def add_recommendation(self, **kwargs) -> str:
        """Add a recommendation and return its ID (uses stable hashing)."""
        with self._lock:
            # Generate stable ID based on domain + title
            domain = kwargs.get("domain", "unknown")
            title = kwargs.get("title", "")
            rec_id = self._generate_stable_id_safe("REC", domain, title)
            kwargs["finding_id"] = rec_id

            # Validate fact/gap citations
            based_on = kwargs.get("based_on_facts", [])
            validation = self.validate_fact_citations(based_on)
            if validation.get("invalid"):
                logger.warning(f"Recommendation {rec_id} cites unknown IDs: {validation['invalid']}")

            rec = Recommendation(**kwargs)
            self.recommendations.append(rec)
            logger.debug(f"Added recommendation {rec_id}: {rec.title}")
            return rec_id

    def add_function_story(self, **kwargs) -> str:
        """Add a function story and return the function name as ID."""
        with self._lock:
            function_name = kwargs.get("function_name", "unknown")
            domain = kwargs.get("domain", "unknown")

            # Validate fact/gap citations
            based_on = kwargs.get("based_on_facts", [])
            validation = self.validate_fact_citations(based_on)
            if validation.get("invalid"):
                logger.warning(f"Function story {function_name} cites unknown IDs: {validation['invalid']}")

            story = FunctionStory(**kwargs)
            self.function_stories.append(story)
            logger.debug(f"Added function story: {function_name} ({domain})")
            return f"FS-{domain}-{function_name}"

    def get_function_stories(self) -> List[Dict]:
        """Get all function stories as dicts (thread-safe)."""
        with self._lock:
            return [s.to_dict() for s in self.function_stories]

    def get_function_stories_markdown(self) -> str:
        """Get all function stories as markdown narrative (thread-safe)."""
        with self._lock:
            if not self.function_stories:
                return ""
            return "\n\n".join([s.to_markdown() for s in self.function_stories])

    def get_all_findings(self) -> Dict[str, Any]:
        """Get all reasoning outputs (thread-safe)."""
        with self._lock:
            return {
                "metadata": self.metadata,
                "summary": {
                    "risks": len(self.risks),
                    "strategic_considerations": len(self.strategic_considerations),
                    "work_items": len(self.work_items),
                    "recommendations": len(self.recommendations),
                    "function_stories": len(self.function_stories)
                },
                "risks": [r.to_dict() for r in self.risks],
                "strategic_considerations": [sc.to_dict() for sc in self.strategic_considerations],
                "work_items": [wi.to_dict() for wi in self.work_items],
                "recommendations": [rec.to_dict() for rec in self.recommendations],
                "function_stories": [fs.to_dict() for fs in self.function_stories]
            }

    def get_evidence_chain(self, finding_id: str) -> Dict[str, Any]:
        """
        Get the full evidence chain for a finding (thread-safe).

        Returns the finding plus all facts it cites.
        """
        with self._lock:
            # Find the finding
            finding = None
            finding_type = None

            for r in self.risks:
                if r.finding_id == finding_id:
                    finding = r
                    finding_type = "risk"
                    break

            if not finding:
                for sc in self.strategic_considerations:
                    if sc.finding_id == finding_id:
                        finding = sc
                        finding_type = "strategic_consideration"
                        break

            if not finding:
                for wi in self.work_items:
                    if wi.finding_id == finding_id:
                        finding = wi
                        finding_type = "work_item"
                        break

            if not finding:
                for rec in self.recommendations:
                    if rec.finding_id == finding_id:
                        finding = rec
                        finding_type = "recommendation"
                        break

            if not finding:
                return {"error": f"Finding not found: {finding_id}"}

            # Get cited facts (fact_store.get_fact/get_gap are already thread-safe)
            fact_ids = finding.based_on_facts
            if hasattr(finding, "triggered_by"):
                fact_ids = list(set(fact_ids + finding.triggered_by))

            cited_facts = []
            if self.fact_store:
                for fid in fact_ids:
                    # Try fact first, then gap (both are citable)
                    fact = self.fact_store.get_fact(fid)
                    if fact:
                        cited_facts.append(fact.to_dict())
                    else:
                        # Check if it's a gap ID
                        gap = self.fact_store.get_gap(fid)
                        if gap:
                            cited_facts.append(gap.to_dict())

            return {
                "finding": finding.to_dict(),
                "finding_type": finding_type,
                "cited_facts": cited_facts,
                "evidence_chain_complete": len(cited_facts) == len(fact_ids)
            }

    def get_total_cost_estimate(self) -> Dict[str, Any]:
        """
        Get aggregated cost estimates across all work items (thread-safe).

        Returns:
            Dict with low/high totals and breakdown by phase
        """
        with self._lock:
            total_low = 0
            total_high = 0
            by_phase = {}
            by_domain = {}

            for wi in self.work_items:
                cost_values = wi.get_cost_range_values()
                total_low += cost_values["low"]
                total_high += cost_values["high"]

                # Aggregate by phase
                if wi.phase not in by_phase:
                    by_phase[wi.phase] = {"low": 0, "high": 0, "count": 0}
                by_phase[wi.phase]["low"] += cost_values["low"]
                by_phase[wi.phase]["high"] += cost_values["high"]
                by_phase[wi.phase]["count"] += 1

                # Aggregate by domain
                if wi.domain not in by_domain:
                    by_domain[wi.domain] = {"low": 0, "high": 0, "count": 0}
                by_domain[wi.domain]["low"] += cost_values["low"]
                by_domain[wi.domain]["high"] += cost_values["high"]
                by_domain[wi.domain]["count"] += 1

            return {
                "total": {"low": total_low, "high": total_high},
                "by_phase": by_phase,
                "by_domain": by_domain,
                "work_item_count": len(self.work_items)
            }

    def get_risk_cost_mapping(self) -> Dict[str, Dict[str, Any]]:
        """
        Get cost mapping from risks to their associated work items (thread-safe).

        Returns:
            Dict mapping risk_id to cost info and work items
        """
        with self._lock:
            risk_costs = {}

            for risk in self.risks:
                risk_id = risk.finding_id
                risk_costs[risk_id] = {
                    "risk_title": risk.title,
                    "risk_severity": risk.severity,
                    "work_items": [],
                    "total_cost": {"low": 0, "high": 0}
                }

            # Map work items to risks via triggered_by_risks
            for wi in self.work_items:
                cost_values = wi.get_cost_range_values()

                for risk_id in wi.triggered_by_risks:
                    if risk_id in risk_costs:
                        risk_costs[risk_id]["work_items"].append({
                            "work_item_id": wi.finding_id,
                            "title": wi.title,
                            "phase": wi.phase,
                            "cost_estimate": wi.cost_estimate,
                            "cost_values": cost_values
                        })
                        risk_costs[risk_id]["total_cost"]["low"] += cost_values["low"]
                        risk_costs[risk_id]["total_cost"]["high"] += cost_values["high"]

            return risk_costs

    def get_risks_with_costs(self) -> List[Dict[str, Any]]:
        """
        Get all risks with their associated remediation costs (thread-safe).

        Returns:
            List of risks with cost information attached
        """
        with self._lock:
            # Build risk_cost_mapping inline to avoid nested lock (RLock allows re-entry but cleaner this way)
            risk_costs = {}
            for risk in self.risks:
                risk_id = risk.finding_id
                risk_costs[risk_id] = {
                    "risk_title": risk.title,
                    "risk_severity": risk.severity,
                    "work_items": [],
                    "total_cost": {"low": 0, "high": 0}
                }

            # Map work items to risks via triggered_by_risks
            for wi in self.work_items:
                cost_values = wi.get_cost_range_values()
                for risk_id in wi.triggered_by_risks:
                    if risk_id in risk_costs:
                        risk_costs[risk_id]["work_items"].append({
                            "work_item_id": wi.finding_id,
                            "title": wi.title,
                            "phase": wi.phase,
                            "cost_estimate": wi.cost_estimate,
                            "cost_values": cost_values
                        })
                        risk_costs[risk_id]["total_cost"]["low"] += cost_values["low"]
                        risk_costs[risk_id]["total_cost"]["high"] += cost_values["high"]

            results = []
            for risk in self.risks:
                risk_dict = risk.to_dict()
                cost_info = risk_costs.get(risk.finding_id, {
                    "work_items": [],
                    "total_cost": {"low": 0, "high": 0}
                })

                risk_dict["remediation_cost"] = cost_info["total_cost"]
                risk_dict["remediation_work_items"] = cost_info["work_items"]
                risk_dict["has_remediation_plan"] = len(cost_info["work_items"]) > 0

                results.append(risk_dict)

            # Sort by severity then by cost (high to low)
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            results.sort(key=lambda x: (
                severity_order.get(x.get("severity", "low"), 4),
                -x["remediation_cost"]["high"]
            ))

            return results

    def merge_from(self, other: "ReasoningStore") -> Dict[str, int]:
        """
        Merge findings from another store.

        PRESERVES original finding IDs to maintain triggered_by_risks links.
        Updates internal counters to prevent future ID conflicts.
        THREAD-SAFE: All operations are protected by internal lock.

        Args:
            other: Another ReasoningStore to merge from

        Returns:
            Dict with counts of merged items
        """
        with self._lock:
            counts = {"risks": 0, "strategic": 0, "work_items": 0, "recommendations": 0, "duplicates": 0}

            # Get existing IDs to check for duplicates
            existing_risk_ids = {r.finding_id for r in self.risks}
            existing_sc_ids = {sc.finding_id for sc in self.strategic_considerations}
            existing_wi_ids = {wi.finding_id for wi in self.work_items}
            existing_rec_ids = {rec.finding_id for rec in self.recommendations}

            def update_counter(finding_id: str, prefix: str):
                """Update counter to avoid future ID conflicts."""
                try:
                    parts = finding_id.split("-")
                    if len(parts) >= 2:
                        seq = int(parts[-1])  # Use last part as sequence number
                        current_max = self._counters.get(prefix, 0)
                        if seq > current_max:
                            self._counters[prefix] = seq
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse finding ID for counter update: {finding_id}")

            # Merge risks
            for risk in other.risks:
                if risk.finding_id in existing_risk_ids:
                    counts["duplicates"] += 1
                    continue
                self.risks.append(risk)
                existing_risk_ids.add(risk.finding_id)
                self._used_ids.add(risk.finding_id)  # Track stable ID
                counts["risks"] += 1
                update_counter(risk.finding_id, "R")

            # Merge strategic considerations
            for sc in other.strategic_considerations:
                if sc.finding_id in existing_sc_ids:
                    counts["duplicates"] += 1
                    continue
                self.strategic_considerations.append(sc)
                existing_sc_ids.add(sc.finding_id)
                self._used_ids.add(sc.finding_id)  # Track stable ID
                counts["strategic"] += 1
                update_counter(sc.finding_id, "SC")

            # Merge work items
            for wi in other.work_items:
                if wi.finding_id in existing_wi_ids:
                    counts["duplicates"] += 1
                    continue
                self.work_items.append(wi)
                existing_wi_ids.add(wi.finding_id)
                self._used_ids.add(wi.finding_id)  # Track stable ID
                counts["work_items"] += 1
                update_counter(wi.finding_id, "WI")

            # Merge recommendations
            for rec in other.recommendations:
                if rec.finding_id in existing_rec_ids:
                    counts["duplicates"] += 1
                    continue
                self.recommendations.append(rec)
                existing_rec_ids.add(rec.finding_id)
                self._used_ids.add(rec.finding_id)  # Track stable ID
                counts["recommendations"] += 1
                update_counter(rec.finding_id, "REC")

            # Also merge _used_ids from other store
            self._used_ids.update(other._used_ids)

        logger.info(f"Merged {counts['risks']} risks, {counts['work_items']} work items (skipped {counts['duplicates']} duplicates)")
        return counts

    def import_from_dict(self, findings_dict: Dict[str, Any]) -> Dict[str, int]:
        """
        Import findings from a dictionary, preserving original IDs.

        Used when merging reasoning results from parallel agents.
        THREAD-SAFE: All operations are protected by internal lock.

        Args:
            findings_dict: Dict with risks, strategic_considerations, work_items, recommendations

        Returns:
            Dict with counts of imported items
        """
        with self._lock:
            counts = {"risks": 0, "strategic": 0, "work_items": 0, "recommendations": 0}

            def update_counter(finding_id: str, prefix: str):
                """Update counter to avoid future ID conflicts."""
                try:
                    parts = finding_id.split("-")
                    if len(parts) >= 2:
                        seq = int(parts[-1])
                        current_max = self._counters.get(prefix, 0)
                        if seq > current_max:
                            self._counters[prefix] = seq
                except (ValueError, IndexError):
                    pass

            # Import risks
            for risk_dict in findings_dict.get("risks", []):
                risk = Risk.from_dict(risk_dict)
                self.risks.append(risk)
                self._used_ids.add(risk.finding_id)  # Track stable ID
                counts["risks"] += 1
                update_counter(risk.finding_id, "R")

            # Import strategic considerations
            for sc_dict in findings_dict.get("strategic_considerations", []):
                sc = StrategicConsideration.from_dict(sc_dict)
                self.strategic_considerations.append(sc)
                self._used_ids.add(sc.finding_id)  # Track stable ID
                counts["strategic"] += 1
                update_counter(sc.finding_id, "SC")

            # Import work items
            for wi_dict in findings_dict.get("work_items", []):
                wi = WorkItem.from_dict(wi_dict)
                self.work_items.append(wi)
                self._used_ids.add(wi.finding_id)  # Track stable ID
                counts["work_items"] += 1
                update_counter(wi.finding_id, "WI")

            # Import recommendations
            for rec_dict in findings_dict.get("recommendations", []):
                rec = Recommendation.from_dict(rec_dict)
                self.recommendations.append(rec)
                self._used_ids.add(rec.finding_id)  # Track stable ID
                counts["recommendations"] += 1
                update_counter(rec.finding_id, "REC")

            return counts

    def save(self, path: str):
        """Save reasoning store to JSON file with retry logic."""
        from tools_v2.io_utils import safe_file_write

        data = self.get_all_findings()
        data["_counters"] = self._counters  # Preserve counters for backward compat
        data["_used_ids"] = list(self._used_ids)  # Preserve used IDs for stable hashing

        safe_file_write(path, data, mode='w', encoding='utf-8', max_retries=3)

        logger.info(f"Saved {len(self.risks)} risks, {len(self.work_items)} work items to {path}")

    @classmethod
    def load(cls, path: str, fact_store: "FactStore" = None) -> "ReasoningStore":
        """
        Load reasoning store from JSON file.

        Args:
            path: Path to JSON file
            fact_store: Optional FactStore for citation validation

        Returns:
            Loaded ReasoningStore
        """
        from tools_v2.io_utils import safe_file_read
        
        data = safe_file_read(path, mode='r', encoding='utf-8', max_retries=3)

        store = cls(fact_store=fact_store)
        store.metadata = data.get("metadata", {})

        # Load risks
        for risk_dict in data.get("risks", []):
            risk = Risk.from_dict(risk_dict)
            store.risks.append(risk)

        # Load strategic considerations
        for sc_dict in data.get("strategic_considerations", []):
            sc = StrategicConsideration.from_dict(sc_dict)
            store.strategic_considerations.append(sc)

        # Load work items
        for wi_dict in data.get("work_items", []):
            wi = WorkItem.from_dict(wi_dict)
            store.work_items.append(wi)

        # Load recommendations
        for rec_dict in data.get("recommendations", []):
            rec = Recommendation.from_dict(rec_dict)
            store.recommendations.append(rec)

        # Restore counters for backward compat
        store._counters = data.get("_counters", {})

        # Restore used IDs set (for stable ID collision detection)
        saved_used_ids = data.get("_used_ids", [])
        if saved_used_ids:
            store._used_ids = set(saved_used_ids)
        else:
            # Rebuild _used_ids from loaded findings
            store._used_ids = set()
            for r in store.risks:
                store._used_ids.add(r.finding_id)
            for sc in store.strategic_considerations:
                store._used_ids.add(sc.finding_id)
            for wi in store.work_items:
                store._used_ids.add(wi.finding_id)
            for rec in store.recommendations:
                store._used_ids.add(rec.finding_id)

        # If no counters saved, calculate from loaded IDs (backward compat)
        if not store._counters:
            def safe_parse_seq(finding_id: str, prefix: str) -> int:
                """Safely parse sequence number from finding ID."""
                try:
                    parts = finding_id.split("-")
                    if len(parts) >= 2:
                        return int(parts[-1])  # Use last part as sequence
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse finding ID: {finding_id}")
                return 0

            for r in store.risks:
                seq = safe_parse_seq(r.finding_id, "R")
                store._counters["R"] = max(store._counters.get("R", 0), seq)
            for sc in store.strategic_considerations:
                seq = safe_parse_seq(sc.finding_id, "SC")
                store._counters["SC"] = max(store._counters.get("SC", 0), seq)
            for wi in store.work_items:
                seq = safe_parse_seq(wi.finding_id, "WI")
                store._counters["WI"] = max(store._counters.get("WI", 0), seq)
            for rec in store.recommendations:
                seq = safe_parse_seq(rec.finding_id, "REC")
                store._counters["REC"] = max(store._counters.get("REC", 0), seq)

        logger.info(f"Loaded {len(store.risks)} risks, {len(store.work_items)} work items from {path}")
        return store


# =============================================================================
# TOOL DEFINITIONS (for Anthropic API)
# =============================================================================

REASONING_TOOLS = [
    {
        "name": "identify_risk",
        "description": """Identify a risk based on facts from discovery.

        Every risk MUST cite the fact IDs that support it (based_on_facts).
        Distinguish standalone risks from integration-dependent risks.

        Be specific - reference actual facts, not generic concerns.

        Returns a unique risk ID (e.g., R-001).""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Domain this risk relates to"
                },
                "title": {
                    "type": "string",
                    "description": "Concise risk title (e.g., 'EOL VMware Version', 'Single Data Center Exposure')"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the risk and its exposure"
                },
                "category": {
                    "type": "string",
                    "description": "Risk category (e.g., 'technical_debt', 'security', 'compliance', 'operational', 'financial')"
                },
                "severity": {
                    "type": "string",
                    "enum": SEVERITY_LEVELS,
                    "description": "critical=deal-impacting, high=significant, medium=notable, low=minor"
                },
                "integration_dependent": {
                    "type": "boolean",
                    "description": "True if this risk only matters if deal proceeds, False if standalone concern"
                },
                "mitigation": {
                    "type": "string",
                    "description": "How this risk can be mitigated or managed"
                },
                "timeline": {
                    "type": "string",
                    "description": "When this risk becomes critical (e.g., 'Q4 2024', 'At integration', 'Ongoing')"
                },
                "based_on_facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "REQUIRED: Fact IDs that support this risk (e.g., ['F-INFRA-003', 'F-INFRA-007'])"
                },
                "confidence": {
                    "type": "string",
                    "enum": CONFIDENCE_LEVELS,
                    "description": "How confident in this assessment based on evidence quality"
                },
                "reasoning": {
                    "type": "string",
                    "description": "REQUIRED: Provide explicit analytical reasoning (50-150 words). Structure: 'I observed [specific fact] → This indicates [interpretation] → Combined with [other fact], this means [conclusion] → For this deal, this matters because [deal impact].' Must connect evidence to conclusion with clear logic chain."
                },
                "mna_lens": {
                    "type": "string",
                    "enum": ["day_1_continuity", "tsa_exposure", "separation_complexity", "synergy_opportunity", "cost_driver"],
                    "description": "REQUIRED: Primary M&A lens this finding connects to. day_1_continuity=affects Day 1 ops, tsa_exposure=requires transition services, separation_complexity=entanglement with parent, synergy_opportunity=value creation potential, cost_driver=affects IT costs"
                },
                "mna_implication": {
                    "type": "string",
                    "description": "REQUIRED: Specific implication for THIS deal (1-2 sentences). Example: 'For this carveout, the single AD forest shared with parent means identity services will require 12-18 month TSA and $400-600K standalone build.'"
                }
            },
            "required": ["domain", "title", "description", "category", "severity",
                        "integration_dependent", "mitigation", "based_on_facts",
                        "confidence", "reasoning", "mna_lens", "mna_implication"]
        }
    },
    {
        "name": "create_strategic_consideration",
        "description": """Create a strategic observation about the deal.

        Used for buyer alignment observations, TSA implications,
        synergy analysis, and deal thesis impacts.

        Must cite supporting facts from discovery.

        Returns a unique consideration ID (e.g., SC-001).""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Domain this consideration relates to"
                },
                "title": {
                    "type": "string",
                    "description": "Concise title (e.g., 'Cloud Platform Misalignment', 'TSA Required for AD Services')"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed observation"
                },
                "lens": {
                    "type": "string",
                    "enum": ["buyer_alignment", "tsa", "synergy", "value_creation", "risk_transfer", "governance"],
                    "description": "Strategic lens this relates to"
                },
                "implication": {
                    "type": "string",
                    "description": "What this means for the deal (cost, timeline, risk, opportunity)"
                },
                "based_on_facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "REQUIRED: Fact IDs that support this consideration"
                },
                "confidence": {
                    "type": "string",
                    "enum": CONFIDENCE_LEVELS,
                    "description": "Confidence in this assessment"
                },
                "reasoning": {
                    "type": "string",
                    "description": "REQUIRED: Provide explicit analytical reasoning (50-150 words). Structure: 'Based on [facts], I conclude [observation] because [logic]. This affects deal value/integration/timeline because [specific impact]. The buyer should consider [implication].' Must show clear cause-and-effect thinking."
                },
                "mna_lens": {
                    "type": "string",
                    "enum": ["day_1_continuity", "tsa_exposure", "separation_complexity", "synergy_opportunity", "cost_driver"],
                    "description": "REQUIRED: Primary M&A lens this consideration connects to"
                },
                "mna_implication": {
                    "type": "string",
                    "description": "REQUIRED: Specific implication for THIS deal (1-2 sentences). Quantify where possible (timeline, cost, risk level)."
                }
            },
            "required": ["domain", "title", "description", "lens", "implication",
                        "based_on_facts", "confidence", "reasoning", "mna_lens", "mna_implication"]
        }
    },
    {
        "name": "create_work_item",
        "description": """Create an integration work item triggered by findings.

        Work items are phased: Day_1 (business continuity), Day_100 (stabilization), Post_100 (optimization).

        Must cite the facts that necessitate this work AND provide a cost estimate.

        If this work item addresses a specific risk, include the risk ID in triggered_by_risks.

        Returns a unique work item ID (e.g., WI-001).""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Domain this work item relates to"
                },
                "title": {
                    "type": "string",
                    "description": "Work item title (e.g., 'Upgrade VMware to 8.0', 'Establish TSA for AD Services')"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of what needs to be done"
                },
                "phase": {
                    "type": "string",
                    "enum": WORK_PHASES,
                    "description": "Day_1=business continuity, Day_100=stabilization, Post_100=optimization"
                },
                "priority": {
                    "type": "string",
                    "enum": PRIORITY_LEVELS,
                    "description": "Priority within the phase"
                },
                "owner_type": {
                    "type": "string",
                    "enum": ["buyer", "target", "shared", "vendor"],
                    "description": "Who owns this work item"
                },
                "cost_estimate": {
                    "type": "string",
                    "enum": COST_RANGES,
                    "description": "Estimated cost range: under_25k (<$25K), 25k_to_100k ($25K-$100K), 100k_to_500k ($100K-$500K), 500k_to_1m ($500K-$1M), over_1m (>$1M)"
                },
                "triggered_by_risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Risk IDs (R-001, R-002) that this work item addresses/remediates"
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Other work items this depends on (can be titles or IDs)"
                },
                "triggered_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "REQUIRED: Fact IDs that necessitate this work"
                },
                "based_on_facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional fact IDs that inform this work item"
                },
                "confidence": {
                    "type": "string",
                    "enum": CONFIDENCE_LEVELS,
                    "description": "Confidence this work is needed"
                },
                "reasoning": {
                    "type": "string",
                    "description": "REQUIRED: Explain the business logic (50-150 words). Structure: 'This work is needed because [specific gap/risk from facts]. If not done by [phase], [consequence]. This must happen [before/after] [other work] because [dependency logic]. The [owner] is responsible because [rationale].' Show sequencing logic."
                },
                "mna_lens": {
                    "type": "string",
                    "enum": ["day_1_continuity", "tsa_exposure", "separation_complexity", "synergy_opportunity", "cost_driver"],
                    "description": "REQUIRED: Primary M&A lens this work item addresses"
                },
                "mna_implication": {
                    "type": "string",
                    "description": "REQUIRED: Why this work matters for the deal (1-2 sentences). Connect to Day-1 readiness, TSA exit, separation, synergy capture, or cost."
                }
            },
            "required": ["domain", "title", "description", "phase", "priority",
                        "owner_type", "cost_estimate", "triggered_by", "confidence", "reasoning", "mna_lens", "mna_implication"]
        }
    },
    {
        "name": "create_recommendation",
        "description": """Create a recommendation for the deal team.

        Recommendations guide negotiation, budgeting, and investigation priorities.

        Must cite supporting facts.

        Returns a unique recommendation ID (e.g., REC-001).""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Domain this recommendation relates to"
                },
                "title": {
                    "type": "string",
                    "description": "Recommendation title"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed recommendation"
                },
                "action_type": {
                    "type": "string",
                    "enum": ["negotiate", "budget", "investigate", "accept", "mitigate"],
                    "description": "Type of action recommended"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["immediate", "pre-close", "post-close"],
                    "description": "When this should be addressed"
                },
                "rationale": {
                    "type": "string",
                    "description": "Why this recommendation is being made"
                },
                "based_on_facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "REQUIRED: Fact IDs that support this recommendation"
                },
                "confidence": {
                    "type": "string",
                    "enum": CONFIDENCE_LEVELS,
                    "description": "Confidence in this recommendation"
                },
                "reasoning": {
                    "type": "string",
                    "description": "REQUIRED: Full reasoning chain (50-150 words). Structure: 'The evidence shows [facts] → This creates [situation] → The deal team should [action] because [logic] → If they don't, [risk/missed opportunity] → Timing is [urgency] because [driver].' Connect dots from evidence to action."
                },
                "mna_lens": {
                    "type": "string",
                    "enum": ["day_1_continuity", "tsa_exposure", "separation_complexity", "synergy_opportunity", "cost_driver"],
                    "description": "REQUIRED: Primary M&A lens this recommendation addresses"
                },
                "mna_implication": {
                    "type": "string",
                    "description": "REQUIRED: Deal impact if recommendation is followed vs ignored (1-2 sentences). Be specific about timeline, cost, or risk."
                }
            },
            "required": ["domain", "title", "description", "action_type", "urgency",
                        "rationale", "based_on_facts", "confidence", "reasoning", "mna_lens", "mna_implication"]
        }
    },
    {
        "name": "create_function_story",
        "description": """Create a narrative story for an IT function/team.

        Function stories provide the contextual depth for executive narratives.
        Each story describes: what the function does, strengths, constraints,
        dependencies, and M&A implications.

        Use this to build rich narratives for IT teams and functional areas.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string",
                    "description": "Name of the function (e.g., 'ERP', 'Service Desk', 'Security Operations')"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Domain this function belongs to"
                },
                "day_to_day": {
                    "type": "string",
                    "description": "2-3 sentences describing what this function primarily does day-to-day"
                },
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "1-3 strengths based on evidence. Format: '[Strength]. Evidence: [fact ref]'"
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "1-3 constraints/bottlenecks. Format: '[Constraint]. Evidence: [fact ref]. Inference: [implication]'"
                },
                "upstream_dependencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What this function depends on (2-4 items)"
                },
                "downstream_dependents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What depends on this function (2-4 items)"
                },
                "mna_implication": {
                    "type": "string",
                    "description": "1-2 sentences on Day-1/TSA/Separation/Synergy relevance"
                },
                "mna_lens": {
                    "type": "string",
                    "enum": ["day_1_continuity", "tsa_exposure", "separation_complexity", "synergy_opportunity", "cost_driver"],
                    "description": "Primary M&A lens for this function"
                },
                "based_on_facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fact IDs supporting this story"
                },
                "inferences": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Labeled inferences made (e.g., 'Inference: Lean staffing suggests capacity risk')"
                },
                "confidence": {
                    "type": "string",
                    "enum": CONFIDENCE_LEVELS,
                    "description": "Confidence in this story based on evidence quality"
                }
            },
            "required": ["function_name", "domain", "day_to_day", "strengths", "constraints",
                        "upstream_dependencies", "downstream_dependents", "mna_implication",
                        "mna_lens", "based_on_facts", "confidence"]
        }
    },
    {
        "name": "complete_reasoning",
        "description": """Signal that reasoning is complete for a domain.

        Call this after producing all risks, strategic considerations,
        work items, and recommendations based on the facts.

        Allows the orchestrator to proceed to review/coordinator phase.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Domain that has been fully analyzed"
                },
                "facts_analyzed": {
                    "type": "integer",
                    "description": "Number of facts from discovery that were analyzed"
                },
                "facts_cited": {
                    "type": "integer",
                    "description": "Number of facts actually cited in findings"
                },
                "summary": {
                    "type": "string",
                    "description": "Brief summary of key findings (2-3 sentences)"
                }
            },
            "required": ["domain", "facts_analyzed", "summary"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION
# =============================================================================

def execute_reasoning_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    reasoning_store: ReasoningStore
) -> Dict[str, Any]:
    """
    Execute a reasoning tool and store results in ReasoningStore.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Tool input parameters
        reasoning_store: ReasoningStore instance to record findings

    Returns:
        Dict with result status and any generated IDs
    """
    if tool_name == "identify_risk":
        return _execute_identify_risk(tool_input, reasoning_store)
    elif tool_name == "create_strategic_consideration":
        return _execute_create_strategic_consideration(tool_input, reasoning_store)
    elif tool_name == "create_work_item":
        return _execute_create_work_item(tool_input, reasoning_store)
    elif tool_name == "create_recommendation":
        return _execute_create_recommendation(tool_input, reasoning_store)
    elif tool_name == "create_function_story":
        return _execute_create_function_story(tool_input, reasoning_store)
    elif tool_name == "complete_reasoning":
        return _execute_complete_reasoning(tool_input, reasoning_store)
    else:
        return {
            "status": "error",
            "message": f"Unknown reasoning tool: {tool_name}"
        }


def _execute_identify_risk(
    input_data: Dict[str, Any],
    reasoning_store: ReasoningStore
) -> Dict[str, Any]:
    """Execute identify_risk tool with comprehensive validation."""
    try:
        # Sanitize inputs before processing
        try:
            from tools_v2.input_sanitizer import sanitize_input
            input_data = sanitize_input(input_data)
        except ImportError:
            pass  # Sanitizer not available
        
        # Validate required fields
        required_fields = ["domain", "title", "description", "category", "severity", 
                          "mitigation", "based_on_facts", "confidence", "reasoning"]
        missing = [f for f in required_fields if not input_data.get(f)]
        if missing:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}"
            }

        # Validate domain
        from config_v2 import DOMAINS
        domain = input_data.get("domain")
        if domain not in DOMAINS:
            return {
                "status": "error",
                "message": f"Invalid domain '{domain}'. Must be one of: {', '.join(DOMAINS)}"
            }

        # Validate severity
        if input_data.get("severity") not in SEVERITY_LEVELS:
            return {
                "status": "error",
                "message": f"Invalid severity. Must be one of: {', '.join(SEVERITY_LEVELS)}"
            }

        # Validate confidence
        if input_data.get("confidence") not in CONFIDENCE_LEVELS:
            return {
                "status": "error",
                "message": f"Invalid confidence. Must be one of: {', '.join(CONFIDENCE_LEVELS)}"
            }

        # Validate required fact citations
        based_on = input_data.get("based_on_facts", [])
        if not based_on:
            return {
                "status": "error",
                "message": "Risk must cite at least one fact (based_on_facts required)"
            }

        risk_id = reasoning_store.add_risk(
            domain=domain,
            title=input_data.get("title"),
            description=input_data.get("description"),
            category=input_data.get("category"),
            severity=input_data.get("severity"),
            integration_dependent=input_data.get("integration_dependent", False),
            mitigation=input_data.get("mitigation"),
            timeline=input_data.get("timeline"),
            based_on_facts=based_on,
            confidence=input_data.get("confidence"),
            reasoning=input_data.get("reasoning"),
            mna_lens=input_data.get("mna_lens", ""),
            mna_implication=input_data.get("mna_implication", "")
        )

        return {
            "status": "success",
            "risk_id": risk_id,
            "message": f"Risk recorded: {input_data.get('title')}"
        }

    except ValueError as e:
        # Citation validation failed
        logger.error(f"Citation validation failed in identify_risk: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"Error in identify_risk: {e}")
        return {"status": "error", "message": str(e)}


def _execute_create_strategic_consideration(
    input_data: Dict[str, Any],
    reasoning_store: ReasoningStore
) -> Dict[str, Any]:
    """Execute create_strategic_consideration tool."""
    try:
        based_on = input_data.get("based_on_facts", [])
        if not based_on:
            return {
                "status": "error",
                "message": "Strategic consideration must cite facts (based_on_facts required)"
            }

        sc_id = reasoning_store.add_strategic_consideration(
            domain=input_data.get("domain"),
            title=input_data.get("title"),
            description=input_data.get("description"),
            lens=input_data.get("lens"),
            implication=input_data.get("implication"),
            based_on_facts=based_on,
            confidence=input_data.get("confidence"),
            reasoning=input_data.get("reasoning"),
            mna_lens=input_data.get("mna_lens", ""),
            mna_implication=input_data.get("mna_implication", "")
        )

        return {
            "status": "success",
            "consideration_id": sc_id,
            "message": f"Strategic consideration recorded: {input_data.get('title')}"
        }

    except Exception as e:
        logger.error(f"Error in create_strategic_consideration: {e}")
        return {"status": "error", "message": str(e)}


def _execute_create_work_item(
    input_data: Dict[str, Any],
    reasoning_store: ReasoningStore
) -> Dict[str, Any]:
    """Execute create_work_item tool with comprehensive validation."""
    try:
        # Validate required fields
        required_fields = ["domain", "title", "description", "phase", "priority",
                          "owner_type", "cost_estimate", "triggered_by", "confidence", "reasoning"]
        missing = [f for f in required_fields if not input_data.get(f)]
        if missing:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}"
            }

        # Validate domain
        from config_v2 import DOMAINS
        domain = input_data.get("domain")
        if domain not in DOMAINS:
            return {
                "status": "error",
                "message": f"Invalid domain '{domain}'. Must be one of: {', '.join(DOMAINS)}"
            }

        # Validate phase
        if input_data.get("phase") not in WORK_PHASES:
            return {
                "status": "error",
                "message": f"Invalid phase. Must be one of: {', '.join(WORK_PHASES)}"
            }

        # Validate priority
        if input_data.get("priority") not in PRIORITY_LEVELS:
            return {
                "status": "error",
                "message": f"Invalid priority. Must be one of: {', '.join(PRIORITY_LEVELS)}"
            }

        # Validate owner_type
        valid_owners = ["buyer", "target", "shared", "vendor"]
        if input_data.get("owner_type") not in valid_owners:
            return {
                "status": "error",
                "message": f"Invalid owner_type. Must be one of: {', '.join(valid_owners)}"
            }

        # Validate cost_estimate
        cost_estimate = input_data.get("cost_estimate")
        if cost_estimate not in COST_RANGES:
            return {
                "status": "error",
                "message": f"Invalid cost_estimate. Must be one of: {', '.join(COST_RANGES)}"
            }

        triggered_by = input_data.get("triggered_by", [])
        if not triggered_by:
            return {
                "status": "error",
                "message": "Work item must cite triggering facts (triggered_by required)"
            }

        wi_id = reasoning_store.add_work_item(
            domain=domain,
            title=input_data.get("title"),
            description=input_data.get("description"),
            phase=input_data.get("phase"),
            priority=input_data.get("priority"),
            owner_type=input_data.get("owner_type"),
            dependencies=input_data.get("dependencies", []),
            triggered_by=triggered_by,
            based_on_facts=input_data.get("based_on_facts", []),
            confidence=input_data.get("confidence"),
            reasoning=input_data.get("reasoning"),
            cost_estimate=cost_estimate,
            triggered_by_risks=input_data.get("triggered_by_risks", []),
            mna_lens=input_data.get("mna_lens", ""),
            mna_implication=input_data.get("mna_implication", "")
        )

        return {
            "status": "success",
            "work_item_id": wi_id,
            "message": f"Work item recorded: {input_data.get('title')}"
        }

    except ValueError as e:
        logger.error(f"Validation error in create_work_item: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"Error in create_work_item: {e}")
        return {"status": "error", "message": str(e)}


def _execute_create_recommendation(
    input_data: Dict[str, Any],
    reasoning_store: ReasoningStore
) -> Dict[str, Any]:
    """Execute create_recommendation tool."""
    try:
        based_on = input_data.get("based_on_facts", [])
        if not based_on:
            return {
                "status": "error",
                "message": "Recommendation must cite facts (based_on_facts required)"
            }

        rec_id = reasoning_store.add_recommendation(
            domain=input_data.get("domain"),
            title=input_data.get("title"),
            description=input_data.get("description"),
            action_type=input_data.get("action_type"),
            urgency=input_data.get("urgency"),
            rationale=input_data.get("rationale"),
            based_on_facts=based_on,
            confidence=input_data.get("confidence"),
            reasoning=input_data.get("reasoning"),
            mna_lens=input_data.get("mna_lens", ""),
            mna_implication=input_data.get("mna_implication", "")
        )

        return {
            "status": "success",
            "recommendation_id": rec_id,
            "message": f"Recommendation recorded: {input_data.get('title')}"
        }

    except Exception as e:
        logger.error(f"Error in create_recommendation: {e}")
        return {"status": "error", "message": str(e)}


def _execute_create_function_story(
    input_data: Dict[str, Any],
    reasoning_store: ReasoningStore
) -> Dict[str, Any]:
    """Execute create_function_story tool."""
    try:
        # Validate required fields
        required_fields = ["function_name", "domain", "day_to_day", "strengths",
                          "constraints", "upstream_dependencies", "downstream_dependents",
                          "mna_implication", "mna_lens", "based_on_facts", "confidence"]
        missing = [f for f in required_fields if not input_data.get(f)]
        if missing:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}"
            }

        story_id = reasoning_store.add_function_story(
            function_name=input_data.get("function_name"),
            domain=input_data.get("domain"),
            day_to_day=input_data.get("day_to_day"),
            strengths=input_data.get("strengths", []),
            constraints=input_data.get("constraints", []),
            upstream_dependencies=input_data.get("upstream_dependencies", []),
            downstream_dependents=input_data.get("downstream_dependents", []),
            mna_implication=input_data.get("mna_implication"),
            mna_lens=input_data.get("mna_lens"),
            based_on_facts=input_data.get("based_on_facts", []),
            inferences=input_data.get("inferences", []),
            confidence=input_data.get("confidence")
        )

        return {
            "status": "success",
            "story_id": story_id,
            "message": f"Function story recorded: {input_data.get('function_name')}"
        }

    except Exception as e:
        logger.error(f"Error in create_function_story: {e}")
        return {"status": "error", "message": str(e)}


def _execute_complete_reasoning(
    input_data: Dict[str, Any],
    reasoning_store: ReasoningStore
) -> Dict[str, Any]:
    """Execute complete_reasoning tool."""
    try:
        domain = input_data.get("domain")
        summary = input_data.get("summary", "")

        # Get stats
        findings = reasoning_store.get_all_findings()

        logger.info(
            f"Reasoning complete for {domain}: "
            f"{findings['summary']['risks']} risks, "
            f"{findings['summary']['work_items']} work items"
        )

        return {
            "status": "success",
            "domain": domain,
            "risks": findings["summary"]["risks"],
            "strategic_considerations": findings["summary"]["strategic_considerations"],
            "work_items": findings["summary"]["work_items"],
            "recommendations": findings["summary"]["recommendations"],
            "message": f"Reasoning complete: {summary}"
        }

    except Exception as e:
        logger.error(f"Error in complete_reasoning: {e}")
        return {"status": "error", "message": str(e)}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_reasoning_tools() -> List[Dict]:
    """Get all reasoning tool definitions."""
    return REASONING_TOOLS


def validate_reasoning_input(tool_name: str, tool_input: Dict) -> Optional[str]:
    """
    Validate tool input before execution.

    Returns error message if invalid, None if valid.
    """
    # Check for required fact citations
    citation_fields = {
        "identify_risk": "based_on_facts",
        "create_strategic_consideration": "based_on_facts",
        "create_work_item": "triggered_by",
        "create_recommendation": "based_on_facts"
    }

    if tool_name in citation_fields:
        field = citation_fields[tool_name]
        citations = tool_input.get(field, [])
        if not citations:
            return f"Missing required fact citations: {field}"

    return None
