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
    from stores.fact_store import FactStore

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

# Overlap types for buyer-aware reasoning
# Used to classify how target and buyer systems relate
OVERLAP_TYPES = [
    "platform_mismatch",        # Different vendors/platforms (SAP vs Oracle)
    "platform_alignment",       # Same platforms (AWS + AWS) - synergy opportunity
    "version_gap",              # Same platform, different versions
    "capability_gap",           # Target lacks something buyer has
    "capability_overlap",       # Both have same capability (consolidation opportunity)
    "integration_complexity",   # Different integration patterns/middleware
    "data_model_mismatch",      # Incompatible data structures
    "licensing_conflict",       # License terms that conflict or require renegotiation
    "security_posture_gap",     # Security maturity differences
    "process_divergence",       # Business process differences affecting integration
]

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
class OverlapCandidate:
    """
    Structured comparison between TARGET and BUYER systems.

    Generated BEFORE findings - forces the model to "show its work" by
    explicitly comparing what target has vs what buyer has before
    making any integration-related conclusions.

    This is the foundation for PE-grade outputs: every overlap finding
    must trace back to an explicit OverlapCandidate.
    """
    overlap_id: str                      # OC-001, OC-002, etc.
    domain: str                          # Which domain this overlap is in
    overlap_type: str                    # One of OVERLAP_TYPES

    # Entity fact references (MUST have both for valid overlap)
    target_fact_ids: List[str]           # F-TGT-xxx IDs
    buyer_fact_ids: List[str]            # F-BYR-xxx IDs

    # What we're comparing
    target_summary: str                  # e.g., "SAP ECC 6.0 with 247 custom objects"
    buyer_summary: str                   # e.g., "Oracle Cloud ERP, enterprise license"

    # Analysis
    why_it_matters: str                  # Integration implication explanation
    confidence: float                    # 0.0-1.0

    # Gaps that need filling
    missing_info_questions: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "OverlapCandidate":
        return cls(**data)

    def validate(self) -> List[str]:
        """Validate that this overlap candidate follows entity rules."""
        errors = []

        # Must have target facts
        if not self.target_fact_ids:
            errors.append(f"OverlapCandidate {self.overlap_id} has no target facts - overlaps must anchor in target")

        # Must have buyer facts (otherwise it's not an overlap)
        if not self.buyer_fact_ids:
            errors.append(f"OverlapCandidate {self.overlap_id} has no buyer facts - this is a standalone target observation, not an overlap")

        # Validate fact ID prefixes
        for fid in self.target_fact_ids:
            if "BYR" in fid:
                errors.append(f"OverlapCandidate {self.overlap_id}: target_fact_ids contains buyer fact {fid}")

        for fid in self.buyer_fact_ids:
            if "TGT" in fid:
                errors.append(f"OverlapCandidate {self.overlap_id}: buyer_fact_ids contains target fact {fid}")

        # Validate overlap_type
        if self.overlap_type not in OVERLAP_TYPES:
            errors.append(f"OverlapCandidate {self.overlap_id}: invalid overlap_type '{self.overlap_type}'")

        return errors


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
    based_on_facts: List[str]  # Fact IDs that support this finding (legacy, combined list)
    confidence: str
    reasoning: str  # Explain HOW facts led to this conclusion
    mna_lens: str = ""  # Primary M&A lens (day_1_continuity, tsa_exposure, etc.)
    mna_implication: str = ""  # Specific deal implication (1-2 sentences)
    timeline: Optional[str] = None  # When this becomes critical

    # === Entity Tracking (PE-Grade) ===
    # Separates target vs buyer fact citations for clarity
    entity: str = "target"  # "target" or "buyer" - inferred from cited facts
    risk_scope: str = "target_standalone"  # "target_standalone", "integration_dependent", "buyer_action"
    target_facts_cited: List[str] = field(default_factory=list)  # F-TGT-xxx IDs
    buyer_facts_cited: List[str] = field(default_factory=list)   # F-BYR-xxx IDs (empty if standalone)
    overlap_id: Optional[str] = None  # Link to OverlapCandidate (OC-xxx) if integration-related
    integration_related: bool = False  # Auto-set by validation if buyer facts cited

    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Risk":
        # Handle missing new fields for backwards compatibility
        data.setdefault("entity", "target")
        data.setdefault("risk_scope", "target_standalone")
        data.setdefault("target_facts_cited", [])
        data.setdefault("buyer_facts_cited", [])
        data.setdefault("overlap_id", None)
        data.setdefault("integration_related", data.get("integration_dependent", False))
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
    based_on_facts: List[str]  # Fact IDs that support this finding (legacy, combined list)
    confidence: str
    reasoning: str  # Explain HOW facts led to this conclusion
    mna_lens: str = ""  # Primary M&A lens (day_1_continuity, tsa_exposure, etc.)
    mna_implication: str = ""  # Specific deal implication (1-2 sentences)

    # === Entity Tracking (PE-Grade) ===
    entity: str = "target"  # "target" or "buyer" - inferred from cited facts
    integration_related: bool = False  # True if this consideration involves buyer comparison
    target_facts_cited: List[str] = field(default_factory=list)  # F-TGT-xxx IDs
    buyer_facts_cited: List[str] = field(default_factory=list)   # F-BYR-xxx IDs
    overlap_id: Optional[str] = None  # Link to OverlapCandidate (OC-xxx) if applicable

    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "StrategicConsideration":
        # Handle missing new fields for backwards compatibility
        data.setdefault("entity", "target")
        data.setdefault("integration_related", False)
        data.setdefault("target_facts_cited", [])
        data.setdefault("buyer_facts_cited", [])
        data.setdefault("overlap_id", None)
        return cls(**data)


# Estimation source types - tracks WHERE the cost estimate came from
ESTIMATION_SOURCES = [
    "benchmark",       # Industry benchmark/anchor from cost model
    "inventory",       # Derived from actual inventory data (apps, users, etc.)
    "vendor_quote",    # Actual vendor quote or proposal
    "historical",      # Historical project costs from similar work
    "ai_research",     # AI-driven research estimate (web search, market data)
    "hybrid",          # Combination of multiple sources
    "manual",          # Manual override/adjustment
]


@dataclass
class CostBuildUp:
    """
    Detailed breakdown showing how a cost was estimated.

    Provides full transparency for leadership by showing:
    - Which cost anchor/benchmark was used
    - The estimation method (per-user, per-app, fixed, etc.)
    - Quantity and unit costs
    - The SOURCE of the estimate (benchmark, inventory, vendor, AI research, etc.)
    - Confidence level based on data quality
    - Assumptions made
    - Source facts that informed the estimate
    """
    anchor_key: str           # Key from COST_ANCHORS (e.g., "identity_separation")
    anchor_name: str          # Human name (e.g., "Identity Separation")
    estimation_method: str    # per_user, per_app, per_site, fixed, fixed_by_size, percentage
    quantity: int             # Number of units (users, apps, sites) - 1 for fixed
    unit_label: str           # "users", "applications", "sites", "organization"
    unit_cost_low: float      # Low end per unit
    unit_cost_high: float     # High end per unit
    total_low: float          # quantity × unit_cost_low
    total_high: float         # quantity × unit_cost_high
    assumptions: List[str] = field(default_factory=list)    # List of assumptions made
    source_facts: List[str] = field(default_factory=list)   # Fact IDs that informed the estimate
    notes: str = ""           # Additional context
    size_tier: str = ""       # For fixed_by_size: small, medium, large

    # NEW: Estimation source tracking for transparency
    estimation_source: str = "benchmark"  # One of ESTIMATION_SOURCES
    source_details: str = ""              # Details about the source (vendor name, research URL, etc.)
    confidence: str = "medium"            # high, medium, low - based on source quality
    scale_factor: float = 1.0             # Adjustment for scale (e.g., 0.8 for volume discount)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "CostBuildUp":
        return cls(**data)

    def get_cost_range_key(self) -> str:
        """Map total to standard cost range key for backwards compatibility."""
        mid = (self.total_low + self.total_high) / 2
        if mid < 25000:
            return "under_25k"
        elif mid < 100000:
            return "25k_to_100k"
        elif mid < 500000:
            return "100k_to_500k"
        elif mid < 1000000:
            return "500k_to_1m"
        else:
            return "over_1m"

    def format_summary(self) -> str:
        """Format a human-readable summary of the cost build-up."""
        if self.estimation_method in ("fixed", "fixed_by_size"):
            base = f"{self.anchor_name}: ${self.total_low:,.0f} - ${self.total_high:,.0f}"
        else:
            base = (f"{self.anchor_name}: {self.quantity:,} {self.unit_label} × "
                    f"${self.unit_cost_low:,.0f}-${self.unit_cost_high:,.0f} = "
                    f"${self.total_low:,.0f} - ${self.total_high:,.0f}")

        # Add source info
        source_labels = {
            "benchmark": "[Benchmark]",
            "inventory": "[From Inventory]",
            "vendor_quote": "[Vendor Quote]",
            "historical": "[Historical]",
            "ai_research": "[AI Research]",
            "hybrid": "[Hybrid]",
            "manual": "[Manual]",
        }
        source_label = source_labels.get(self.estimation_source, "")
        return f"{base} {source_label}" if source_label else base

    def get_confidence_color(self) -> str:
        """Get color code for confidence level (for UI display)."""
        colors = {
            "high": "#28a745",    # Green
            "medium": "#ffc107",  # Yellow
            "low": "#dc3545",     # Red
        }
        return colors.get(self.confidence, "#6c757d")


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
    based_on_facts: List[str]  # Additional supporting fact IDs (legacy, combined list)
    confidence: str
    reasoning: str  # Explain WHY this work is needed

    # Cost estimation
    cost_estimate: str  # One of COST_RANGES: under_25k, 25k_to_100k, etc.

    # Detailed cost build-up (shows HOW the estimate was derived)
    cost_buildup: Optional[CostBuildUp] = None  # Detailed breakdown for transparency

    # Link to risks that this work item addresses
    triggered_by_risks: List[str] = field(default_factory=list)  # Risk IDs (R-001, R-002)

    # M&A Framing
    mna_lens: str = ""  # Primary M&A lens (day_1_continuity, tsa_exposure, etc.)
    mna_implication: str = ""  # Specific deal implication (1-2 sentences)

    # === PE-Grade: Separated Actions ===
    # target_action: What TARGET must do (always present, target-scoped)
    # integration_option: Optional path depending on buyer strategy
    target_action: str = ""  # e.g., "Inventory SAP objects; engage licensing"
    integration_option: Optional[str] = None  # e.g., "If Oracle harmonization, add ETL + 6 months"

    # === Entity Tracking ===
    entity: str = "target"  # "target" or "buyer" - inferred from cited facts
    integration_related: bool = False  # True if depends on buyer context
    target_facts_cited: List[str] = field(default_factory=list)  # F-TGT-xxx IDs
    buyer_facts_cited: List[str] = field(default_factory=list)   # F-BYR-xxx IDs
    overlap_id: Optional[str] = None  # Link to OverlapCandidate (OC-xxx)

    dependencies: List[str] = field(default_factory=list)  # Other work items
    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        result = asdict(self)
        # Handle CostBuildUp serialization
        if self.cost_buildup:
            result['cost_buildup'] = self.cost_buildup.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkItem":
        # Handle CostBuildUp deserialization
        if data.get('cost_buildup') and isinstance(data['cost_buildup'], dict):
            data['cost_buildup'] = CostBuildUp.from_dict(data['cost_buildup'])
        # Handle missing new fields for backwards compatibility
        data.setdefault("entity", "target")
        data.setdefault("target_action", "")
        data.setdefault("integration_option", None)
        data.setdefault("integration_related", False)
        data.setdefault("target_facts_cited", [])
        data.setdefault("buyer_facts_cited", [])
        data.setdefault("overlap_id", None)
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
    based_on_facts: List[str]  # Fact IDs that support this recommendation (legacy, combined)
    confidence: str
    reasoning: str  # Explain the reasoning chain
    mna_lens: str = ""  # Primary M&A lens (day_1_continuity, tsa_exposure, etc.)
    mna_implication: str = ""  # Specific deal implication (1-2 sentences)

    # === Entity Tracking (PE-Grade) ===
    entity: str = "target"  # "target" or "buyer" - inferred from cited facts
    integration_related: bool = False  # True if recommendation involves buyer context
    target_facts_cited: List[str] = field(default_factory=list)  # F-TGT-xxx IDs
    buyer_facts_cited: List[str] = field(default_factory=list)   # F-BYR-xxx IDs
    overlap_id: Optional[str] = None  # Link to OverlapCandidate (OC-xxx)

    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Recommendation":
        # Handle missing new fields for backwards compatibility
        data.setdefault("entity", "target")
        data.setdefault("integration_related", False)
        data.setdefault("target_facts_cited", [])
        data.setdefault("buyer_facts_cited", [])
        data.setdefault("overlap_id", None)
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

        # Overlap candidates - generated FIRST, before findings
        # Forces "show your work" comparison of target vs buyer
        self.overlap_candidates: List[OverlapCandidate] = []

        # Standard findings
        self.risks: List[Risk] = []
        self.strategic_considerations: List[StrategicConsideration] = []
        self.work_items: List[WorkItem] = []
        self.recommendations: List[Recommendation] = []
        self.function_stories: List[FunctionStory] = []  # Phase 3: Function narratives

        self._counters: Dict[str, int] = {}  # Kept for backwards compatibility
        self._used_ids: Set[str] = set()  # Track all used IDs to prevent duplicates
        self.metadata: Dict[str, Any] = {
            "created_at": _generate_timestamp(),
            "version": "2.3"  # Version bump for overlap candidates
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

    def add_overlap_candidate(self, **kwargs) -> str:
        """
        Add an overlap candidate and return its ID.

        Overlap candidates MUST be generated before findings.
        They force explicit comparison of target vs buyer systems.

        Returns:
            Overlap ID (e.g., OC-001)

        Raises:
            ValueError: If validation fails (missing target/buyer facts)
        """
        with self._lock:
            # Generate sequential ID for overlap candidates
            oc_id = self._generate_id("OC")
            kwargs["overlap_id"] = oc_id

            # Set domain if not provided
            if "domain" not in kwargs:
                kwargs["domain"] = "cross-domain"

            # Ensure list fields have defaults
            if "target_fact_ids" not in kwargs:
                kwargs["target_fact_ids"] = []
            if "buyer_fact_ids" not in kwargs:
                kwargs["buyer_fact_ids"] = []
            if "missing_info_questions" not in kwargs:
                kwargs["missing_info_questions"] = []

            overlap = OverlapCandidate(**kwargs)

            # Validate the overlap candidate
            validation_errors = overlap.validate()
            if validation_errors:
                for error in validation_errors:
                    logger.warning(error)
                # Don't block, but log warnings - model may be learning

            self.overlap_candidates.append(overlap)
            logger.debug(
                f"Added overlap candidate {oc_id}: {overlap.overlap_type} - "
                f"target={overlap.target_fact_ids}, buyer={overlap.buyer_fact_ids}"
            )
            return oc_id

    def get_overlap_candidates(self, domain: str = None) -> List[OverlapCandidate]:
        """Get overlap candidates, optionally filtered by domain."""
        with self._lock:
            if domain:
                return [oc for oc in self.overlap_candidates if oc.domain == domain]
            return list(self.overlap_candidates)

    def has_overlap_map(self) -> bool:
        """Check if overlap map has been generated (required before findings)."""
        with self._lock:
            return len(self.overlap_candidates) > 0

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

            # Populate entity-specific fact citation fields from based_on_facts
            target_facts = [f for f in based_on if "TGT" in f.upper()]
            buyer_facts = [f for f in based_on if "BYR" in f.upper()]
            kwargs["target_facts_cited"] = target_facts
            kwargs["buyer_facts_cited"] = buyer_facts

            # Ensure entity is set (infer from citations if not explicitly provided)
            if "entity" not in kwargs:
                kwargs["entity"] = _infer_entity_from_citations(based_on, self.fact_store)

            risk = Risk(**kwargs)
            self.risks.append(risk)
            logger.debug(f"Added risk {risk_id}: {risk.title} [entity={risk.entity}]")
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

            # Populate entity-specific fact citation fields from based_on_facts
            target_facts = [f for f in based_on if "TGT" in f.upper()]
            buyer_facts = [f for f in based_on if "BYR" in f.upper()]
            kwargs["target_facts_cited"] = target_facts
            kwargs["buyer_facts_cited"] = buyer_facts

            # Ensure entity is set (infer from citations if not explicitly provided)
            if "entity" not in kwargs:
                kwargs["entity"] = _infer_entity_from_citations(based_on, self.fact_store)

            sc = StrategicConsideration(**kwargs)
            self.strategic_considerations.append(sc)
            logger.debug(f"Added strategic consideration {sc_id}: {sc.title} [entity={sc.entity}]")
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

            # Populate entity-specific fact citation fields from triggered_by and based_on_facts
            target_facts = [f for f in all_ids if "TGT" in f.upper()]
            buyer_facts = [f for f in all_ids if "BYR" in f.upper()]
            kwargs["target_facts_cited"] = target_facts
            kwargs["buyer_facts_cited"] = buyer_facts

            # Ensure entity is set (infer from citations if not explicitly provided)
            if "entity" not in kwargs:
                kwargs["entity"] = _infer_entity_from_citations(all_ids, self.fact_store)

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
            buildup_info = ""
            if wi.cost_buildup is not None:
                buildup_info = f" [buildup: {wi.cost_buildup.anchor_key} ${wi.cost_buildup.total_low:,.0f}-${wi.cost_buildup.total_high:,.0f}]"
            logger.debug(f"Added work item {wi_id}: {wi.title} (cost: {wi.cost_estimate}){buildup_info} [entity={wi.entity}]")
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

            # Populate entity-specific fact citation fields from based_on_facts
            target_facts = [f for f in based_on if "TGT" in f.upper()]
            buyer_facts = [f for f in based_on if "BYR" in f.upper()]
            kwargs["target_facts_cited"] = target_facts
            kwargs["buyer_facts_cited"] = buyer_facts

            # Ensure entity is set (infer from citations if not explicitly provided)
            if "entity" not in kwargs:
                kwargs["entity"] = _infer_entity_from_citations(based_on, self.fact_store)

            rec = Recommendation(**kwargs)
            self.recommendations.append(rec)
            logger.debug(f"Added recommendation {rec_id}: {rec.title} [entity={rec.entity}]")
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
                    "overlap_candidates": len(self.overlap_candidates),
                    "risks": len(self.risks),
                    "strategic_considerations": len(self.strategic_considerations),
                    "work_items": len(self.work_items),
                    "recommendations": len(self.recommendations),
                    "function_stories": len(self.function_stories)
                },
                "overlap_candidates": [oc.to_dict() for oc in self.overlap_candidates],
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

    # =========================================================================
    # PHASE 5 IMPROVEMENTS (Points 76-80)
    # =========================================================================

    def prioritize_risks(self, weights: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        Point 76: Sophisticated risk prioritization algorithm.

        Calculates a composite priority score based on:
        - Severity (40% default weight)
        - Business impact / remediation cost (25% default weight)
        - Confidence level (15% default weight)
        - Has remediation plan (10% default weight)
        - Integration dependency (10% default weight)

        Args:
            weights: Optional custom weights for scoring factors

        Returns:
            List of risks with priority_score and ranking
        """
        default_weights = {
            "severity": 0.40,
            "business_impact": 0.25,
            "confidence": 0.15,
            "has_remediation": 0.10,
            "integration_dependency": 0.10
        }
        w = weights or default_weights

        severity_scores = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
        confidence_scores = {"high": 1.0, "medium": 0.6, "low": 0.3}

        with self._lock:
            # Get risks with costs first
            risks_with_costs = self.get_risks_with_costs()

            # Find max cost for normalization
            max_cost = max(
                (r["remediation_cost"]["high"] for r in risks_with_costs),
                default=1
            ) or 1

            prioritized = []
            for risk in risks_with_costs:
                # Calculate component scores
                severity_score = severity_scores.get(risk.get("severity", "low"), 0.25)
                confidence_score = confidence_scores.get(risk.get("confidence", "low"), 0.3)

                # Normalize cost to 0-1 scale (higher cost = higher priority)
                cost_score = risk["remediation_cost"]["high"] / max_cost if max_cost > 0 else 0

                # Remediation plan factor (risks without plans need attention)
                remediation_score = 0.0 if risk["has_remediation_plan"] else 1.0

                # Integration dependency (standalone risks may need attention regardless)
                integration_score = 0.5 if risk.get("integration_dependent", False) else 1.0

                # Calculate composite score
                priority_score = (
                    w["severity"] * severity_score +
                    w["business_impact"] * cost_score +
                    w["confidence"] * confidence_score +
                    w["has_remediation"] * remediation_score +
                    w["integration_dependency"] * integration_score
                )

                risk["priority_score"] = round(priority_score, 3)
                risk["score_breakdown"] = {
                    "severity": round(severity_score, 2),
                    "business_impact": round(cost_score, 2),
                    "confidence": round(confidence_score, 2),
                    "remediation_gap": round(remediation_score, 2),
                    "integration_factor": round(integration_score, 2)
                }
                prioritized.append(risk)

            # Sort by priority score descending
            prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

            # Add ranking
            for i, risk in enumerate(prioritized, 1):
                risk["priority_rank"] = i

            return prioritized

    def get_work_item_dependency_graph(self) -> Dict[str, Any]:
        """
        Point 77: Build work item dependency mapping.

        Returns a graph structure showing:
        - Which work items block others
        - Which work items are blocked by others
        - Critical path items (most blocking dependencies)
        - Orphan items (no dependencies either way)

        Returns:
            Dict with dependency graph and analysis
        """
        with self._lock:
            # Build dependency maps
            blocks = {}  # item_id -> list of items it blocks
            blocked_by = {}  # item_id -> list of items blocking it
            all_ids = set()

            for wi in self.work_items:
                wi_id = wi.finding_id
                all_ids.add(wi_id)
                blocks[wi_id] = []
                blocked_by[wi_id] = list(wi.dependencies) if wi.dependencies else []

            # Build reverse mapping (blocks)
            for wi_id, deps in blocked_by.items():
                for dep_id in deps:
                    if dep_id in blocks:
                        blocks[dep_id].append(wi_id)

            # Identify critical path items (most outgoing blocks)
            critical_path = sorted(
                [(wi_id, len(blocks[wi_id])) for wi_id in all_ids],
                key=lambda x: x[1],
                reverse=True
            )[:10]  # Top 10 most blocking items

            # Identify orphans (no dependencies in or out)
            orphans = [
                wi_id for wi_id in all_ids
                if not blocks[wi_id] and not blocked_by[wi_id]
            ]

            # Identify root items (nothing blocks them, but they block others)
            roots = [
                wi_id for wi_id in all_ids
                if not blocked_by[wi_id] and blocks[wi_id]
            ]

            # Identify leaf items (blocked by others, but don't block anything)
            leaves = [
                wi_id for wi_id in all_ids
                if blocked_by[wi_id] and not blocks[wi_id]
            ]

            # Build item details
            item_details = {}
            for wi in self.work_items:
                item_details[wi.finding_id] = {
                    "title": wi.title,
                    "phase": wi.phase,
                    "priority": wi.priority,
                    "domain": wi.domain,
                    "blocks": blocks.get(wi.finding_id, []),
                    "blocked_by": blocked_by.get(wi.finding_id, []),
                    "is_critical_path": wi.finding_id in [x[0] for x in critical_path[:5]],
                    "is_orphan": wi.finding_id in orphans,
                    "is_root": wi.finding_id in roots,
                    "is_leaf": wi.finding_id in leaves
                }

            return {
                "items": item_details,
                "critical_path": [{"id": x[0], "blocks_count": x[1]} for x in critical_path],
                "roots": roots,
                "leaves": leaves,
                "orphans": orphans,
                "total_items": len(all_ids),
                "total_dependencies": sum(len(v) for v in blocked_by.values())
            }

    def consolidate_findings(self, similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Point 78: Merge similar findings across domains.

        Identifies potentially duplicate or overlapping findings based on:
        - Title similarity
        - Shared fact citations
        - Same category/lens

        Args:
            similarity_threshold: Minimum similarity score to flag (0.0-1.0)

        Returns:
            Dict with consolidation recommendations
        """
        from difflib import SequenceMatcher

        def title_similarity(a: str, b: str) -> float:
            """Calculate title similarity using SequenceMatcher."""
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        def fact_overlap(facts_a: List[str], facts_b: List[str]) -> float:
            """Calculate overlap in cited facts."""
            if not facts_a or not facts_b:
                return 0.0
            set_a, set_b = set(facts_a), set(facts_b)
            intersection = len(set_a & set_b)
            union = len(set_a | set_b)
            return intersection / union if union > 0 else 0.0

        with self._lock:
            consolidation_groups = {
                "risks": [],
                "work_items": [],
                "strategic_considerations": []
            }

            # Check risks for similarity
            for i, risk_a in enumerate(self.risks):
                for risk_b in self.risks[i+1:]:
                    title_sim = title_similarity(risk_a.title, risk_b.title)
                    fact_sim = fact_overlap(risk_a.based_on_facts, risk_b.based_on_facts)
                    same_category = risk_a.category == risk_b.category
                    same_lens = risk_a.mna_lens == risk_b.mna_lens

                    # Weighted similarity score
                    similarity = (
                        0.4 * title_sim +
                        0.3 * fact_sim +
                        0.15 * (1.0 if same_category else 0.0) +
                        0.15 * (1.0 if same_lens else 0.0)
                    )

                    if similarity >= similarity_threshold:
                        consolidation_groups["risks"].append({
                            "item_a": {"id": risk_a.finding_id, "title": risk_a.title, "domain": risk_a.domain},
                            "item_b": {"id": risk_b.finding_id, "title": risk_b.title, "domain": risk_b.domain},
                            "similarity_score": round(similarity, 3),
                            "breakdown": {
                                "title_similarity": round(title_sim, 2),
                                "fact_overlap": round(fact_sim, 2),
                                "same_category": same_category,
                                "same_lens": same_lens
                            },
                            "recommendation": "Consider merging" if similarity > 0.85 else "Review for overlap"
                        })

            # Check work items for similarity
            for i, wi_a in enumerate(self.work_items):
                for wi_b in self.work_items[i+1:]:
                    title_sim = title_similarity(wi_a.title, wi_b.title)
                    fact_sim = fact_overlap(wi_a.triggered_by, wi_b.triggered_by)
                    same_phase = wi_a.phase == wi_b.phase
                    same_owner = wi_a.owner_type == wi_b.owner_type

                    similarity = (
                        0.4 * title_sim +
                        0.3 * fact_sim +
                        0.15 * (1.0 if same_phase else 0.0) +
                        0.15 * (1.0 if same_owner else 0.0)
                    )

                    if similarity >= similarity_threshold:
                        consolidation_groups["work_items"].append({
                            "item_a": {"id": wi_a.finding_id, "title": wi_a.title, "domain": wi_a.domain},
                            "item_b": {"id": wi_b.finding_id, "title": wi_b.title, "domain": wi_b.domain},
                            "similarity_score": round(similarity, 3),
                            "breakdown": {
                                "title_similarity": round(title_sim, 2),
                                "fact_overlap": round(fact_sim, 2),
                                "same_phase": same_phase,
                                "same_owner": same_owner
                            },
                            "recommendation": "Consider merging" if similarity > 0.85 else "Review for overlap"
                        })

            return {
                "consolidation_candidates": consolidation_groups,
                "summary": {
                    "potential_risk_duplicates": len(consolidation_groups["risks"]),
                    "potential_work_item_duplicates": len(consolidation_groups["work_items"]),
                    "potential_sc_duplicates": len(consolidation_groups["strategic_considerations"]),
                    "threshold_used": similarity_threshold
                }
            }

    def quantify_business_impact(self) -> Dict[str, Any]:
        """
        Point 79: Estimate dollar impact of risks.

        Calculates business impact based on:
        - Direct remediation costs (from work items)
        - Indirect costs (delay, productivity loss estimates)
        - Risk-weighted exposure

        Returns:
            Dict with impact quantification by risk, domain, and phase
        """
        # Impact multipliers for indirect costs
        INDIRECT_COST_MULTIPLIERS = {
            "critical": 2.5,  # Critical risks have significant indirect costs
            "high": 1.8,
            "medium": 1.3,
            "low": 1.1
        }

        # Delay cost per day by severity (business disruption)
        DELAY_COST_PER_DAY = {
            "critical": 50000,
            "high": 20000,
            "medium": 5000,
            "low": 1000
        }

        with self._lock:
            risks_with_costs = self.get_risks_with_costs()

            impact_by_risk = []
            total_direct = 0
            total_indirect = 0
            total_risk_weighted = 0

            for risk in risks_with_costs:
                severity = risk.get("severity", "low")
                direct_low = risk["remediation_cost"]["low"]
                direct_high = risk["remediation_cost"]["high"]

                # Calculate indirect costs
                multiplier = INDIRECT_COST_MULTIPLIERS.get(severity, 1.1)
                indirect_low = int(direct_low * (multiplier - 1))
                indirect_high = int(direct_high * (multiplier - 1))

                # Risk-weighted exposure (probability-adjusted)
                confidence = risk.get("confidence", "low")
                probability_factor = {"high": 0.8, "medium": 0.5, "low": 0.3}.get(confidence, 0.3)
                risk_weighted_low = int((direct_low + indirect_low) * probability_factor)
                risk_weighted_high = int((direct_high + indirect_high) * probability_factor)

                # Potential delay impact (assuming 30-day delay for unaddressed risks)
                delay_days = 30 if not risk["has_remediation_plan"] else 10
                delay_cost = DELAY_COST_PER_DAY.get(severity, 1000) * delay_days

                impact = {
                    "risk_id": risk["finding_id"],
                    "title": risk["title"],
                    "severity": severity,
                    "direct_cost": {"low": direct_low, "high": direct_high},
                    "indirect_cost": {"low": indirect_low, "high": indirect_high},
                    "total_cost": {
                        "low": direct_low + indirect_low,
                        "high": direct_high + indirect_high
                    },
                    "risk_weighted_exposure": {
                        "low": risk_weighted_low,
                        "high": risk_weighted_high
                    },
                    "potential_delay_cost": delay_cost,
                    "has_remediation_plan": risk["has_remediation_plan"]
                }
                impact_by_risk.append(impact)

                total_direct += direct_high
                total_indirect += indirect_high
                total_risk_weighted += risk_weighted_high

            # Aggregate by domain
            by_domain = {}
            for risk in risks_with_costs:
                domain = risk.get("domain", "unknown")
                if domain not in by_domain:
                    by_domain[domain] = {"low": 0, "high": 0, "count": 0}
                by_domain[domain]["low"] += risk["remediation_cost"]["low"]
                by_domain[domain]["high"] += risk["remediation_cost"]["high"]
                by_domain[domain]["count"] += 1

            # Aggregate by severity
            by_severity = {}
            for risk in risks_with_costs:
                severity = risk.get("severity", "low")
                if severity not in by_severity:
                    by_severity[severity] = {"low": 0, "high": 0, "count": 0}
                by_severity[severity]["low"] += risk["remediation_cost"]["low"]
                by_severity[severity]["high"] += risk["remediation_cost"]["high"]
                by_severity[severity]["count"] += 1

            return {
                "impact_by_risk": impact_by_risk,
                "totals": {
                    "direct_cost": {"low": int(total_direct * 0.6), "high": total_direct},
                    "indirect_cost": {"low": int(total_indirect * 0.6), "high": total_indirect},
                    "combined": {
                        "low": int((total_direct + total_indirect) * 0.6),
                        "high": total_direct + total_indirect
                    },
                    "risk_weighted_exposure": {
                        "low": int(total_risk_weighted * 0.6),
                        "high": total_risk_weighted
                    }
                },
                "by_domain": by_domain,
                "by_severity": by_severity,
                "risk_count": len(risks_with_costs)
            }

    def classify_timeline(self, work_item_id: str) -> Dict[str, Any]:
        """
        Point 80: Improved Day 1/100/Post-100 classification.

        Analyzes a work item and returns classification recommendation with rationale.

        Classification criteria:
        - Day_1: Business continuity critical, no workarounds, immediate impact
        - Day_100: Stabilization required, workarounds exist but unsustainable
        - Post_100: Optimization, nice-to-have improvements

        Args:
            work_item_id: ID of work item to classify

        Returns:
            Dict with recommended phase and confidence
        """
        with self._lock:
            # Find the work item
            work_item = None
            for wi in self.work_items:
                if wi.finding_id == work_item_id:
                    work_item = wi
                    break

            if not work_item:
                return {"error": f"Work item not found: {work_item_id}"}

            # Classification factors
            factors = {
                "is_business_critical": False,
                "has_workaround": True,  # Assume workaround exists unless proven otherwise
                "blocks_other_items": False,
                "addresses_critical_risk": False,
                "affects_day1_continuity": False,
                "is_tsa_dependent": False,
                "is_optimization": False
            }

            # Check if addresses critical/high risk
            for risk_id in work_item.triggered_by_risks:
                for risk in self.risks:
                    if risk.finding_id == risk_id:
                        if risk.severity in ["critical", "high"]:
                            factors["addresses_critical_risk"] = True
                        if risk.mna_lens == "day_1_continuity":
                            factors["affects_day1_continuity"] = True
                        break

            # Check M&A lens
            if work_item.mna_lens == "day_1_continuity":
                factors["is_business_critical"] = True
                factors["affects_day1_continuity"] = True
            elif work_item.mna_lens == "tsa_exposure":
                factors["is_tsa_dependent"] = True
            elif work_item.mna_lens == "synergy_opportunity":
                factors["is_optimization"] = True

            # Check if this blocks other items
            for other_wi in self.work_items:
                if work_item_id in other_wi.dependencies:
                    factors["blocks_other_items"] = True
                    break

            # Priority factor
            if work_item.priority == "critical":
                factors["is_business_critical"] = True

            # Determine recommended phase
            score_day1 = 0
            score_day100 = 0
            score_post100 = 0

            if factors["is_business_critical"]:
                score_day1 += 3
            if factors["affects_day1_continuity"]:
                score_day1 += 3
            if factors["addresses_critical_risk"]:
                score_day1 += 2
            if factors["blocks_other_items"]:
                score_day1 += 1
                score_day100 += 1

            if factors["is_tsa_dependent"]:
                score_day100 += 2
            if not factors["is_business_critical"] and factors["addresses_critical_risk"]:
                score_day100 += 1

            if factors["is_optimization"]:
                score_post100 += 3
            if not factors["addresses_critical_risk"] and not factors["is_business_critical"]:
                score_post100 += 2

            # Determine recommendation
            scores = {
                "Day_1": score_day1,
                "Day_100": score_day100,
                "Post_100": score_post100
            }
            recommended_phase = max(scores, key=scores.get)

            # Calculate confidence
            max_score = max(scores.values())
            total_score = sum(scores.values()) or 1
            confidence = "high" if max_score / total_score > 0.6 else "medium" if max_score / total_score > 0.4 else "low"

            # Check if current phase matches recommendation
            phase_matches = work_item.phase == recommended_phase

            return {
                "work_item_id": work_item_id,
                "title": work_item.title,
                "current_phase": work_item.phase,
                "recommended_phase": recommended_phase,
                "phase_matches": phase_matches,
                "confidence": confidence,
                "scores": scores,
                "factors": factors,
                "rationale": self._generate_timeline_rationale(recommended_phase, factors)
            }

    def _generate_timeline_rationale(self, phase: str, factors: Dict[str, bool]) -> str:
        """Generate human-readable rationale for timeline classification."""
        rationale_parts = []

        if phase == "Day_1":
            if factors["is_business_critical"]:
                rationale_parts.append("Business-critical item requiring immediate attention")
            if factors["affects_day1_continuity"]:
                rationale_parts.append("Directly affects Day 1 operational continuity")
            if factors["addresses_critical_risk"]:
                rationale_parts.append("Addresses critical/high severity risk")
            if factors["blocks_other_items"]:
                rationale_parts.append("Blocks other integration work items")
        elif phase == "Day_100":
            if factors["is_tsa_dependent"]:
                rationale_parts.append("Requires TSA negotiation/transition period")
            rationale_parts.append("Stabilization priority - workarounds may exist but need resolution")
        else:  # Post_100
            if factors["is_optimization"]:
                rationale_parts.append("Optimization/synergy opportunity")
            rationale_parts.append("Lower urgency - can be addressed after initial stabilization")

        return "; ".join(rationale_parts) if rationale_parts else "Standard classification based on priority and impact"

    def reclassify_all_timelines(self) -> Dict[str, Any]:
        """
        Run timeline classification on all work items and return recommendations.

        Returns:
            Dict with classification results and summary of changes
        """
        with self._lock:
            results = []
            phase_changes = {"Day_1": 0, "Day_100": 0, "Post_100": 0}
            mismatches = []

            for wi in self.work_items:
                classification = self.classify_timeline(wi.finding_id)
                results.append(classification)

                if not classification.get("phase_matches", True):
                    mismatches.append({
                        "work_item_id": wi.finding_id,
                        "title": wi.title,
                        "current": wi.phase,
                        "recommended": classification["recommended_phase"],
                        "confidence": classification["confidence"]
                    })
                    phase_changes[classification["recommended_phase"]] += 1

            return {
                "classifications": results,
                "mismatches": mismatches,
                "mismatch_count": len(mismatches),
                "total_items": len(self.work_items),
                "recommended_changes": phase_changes
            }

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
        "name": "generate_overlap_map",
        "description": """Generate the overlap map comparing TARGET and BUYER systems.

        ⚠️ MUST be called FIRST, before creating any findings.

        This tool structures your analysis by explicitly comparing what the target
        has vs what the buyer has. Every integration-related finding should trace
        back to an overlap candidate generated here.

        For each category where BOTH entities have relevant facts, create an
        overlap candidate that documents:
        - What the target has (with fact IDs)
        - What the buyer has (with fact IDs)
        - Why this comparison matters for integration
        - What questions would improve confidence

        This forces "show your work" reasoning and prevents drift into
        generic observations without evidence.

        Returns a list of overlap candidate IDs (OC-001, OC-002, etc.).""",
        "input_schema": {
            "type": "object",
            "properties": {
                "overlap_candidates": {
                    "type": "array",
                    "description": "List of overlap comparisons between target and buyer",
                    "items": {
                        "type": "object",
                        "properties": {
                            "domain": {
                                "type": "string",
                                "enum": ALL_DOMAINS,
                                "description": "Domain this overlap relates to"
                            },
                            "overlap_type": {
                                "type": "string",
                                "enum": OVERLAP_TYPES,
                                "description": "Type of overlap/mismatch between target and buyer"
                            },
                            "target_fact_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "REQUIRED: Target fact IDs (F-TGT-xxx) being compared"
                            },
                            "buyer_fact_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "REQUIRED: Buyer fact IDs (F-BYR-xxx) being compared"
                            },
                            "target_summary": {
                                "type": "string",
                                "description": "Brief summary of target's position (e.g., 'SAP ECC 6.0 with 247 custom ABAP programs')"
                            },
                            "buyer_summary": {
                                "type": "string",
                                "description": "Brief summary of buyer's position (e.g., 'Oracle Cloud ERP, enterprise license')"
                            },
                            "why_it_matters": {
                                "type": "string",
                                "description": "REQUIRED: Why this overlap matters for integration (2-3 sentences)"
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Confidence in this assessment (0.0-1.0)"
                            },
                            "missing_info_questions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Questions that would improve confidence or clarify integration approach"
                            }
                        },
                        "required": ["domain", "overlap_type", "target_fact_ids", "buyer_fact_ids",
                                    "target_summary", "buyer_summary", "why_it_matters", "confidence"]
                    }
                }
            },
            "required": ["overlap_candidates"]
        }
    },
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
                },
                "risk_scope": {
                    "type": "string",
                    "enum": ["target_standalone", "integration_dependent"],
                    "description": "target_standalone=risk exists regardless of buyer, integration_dependent=risk only matters in context of this integration"
                },
                "overlap_id": {
                    "type": "string",
                    "description": "Link to OverlapCandidate (OC-xxx) if this risk stems from a target-buyer comparison"
                },
                "target_facts_cited": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Target fact IDs (F-TGT-xxx) that support this risk"
                },
                "buyer_facts_cited": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Buyer fact IDs (F-BYR-xxx) if this is an integration-dependent risk"
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
                "cost_buildup": {
                    "type": "object",
                    "description": (
                        "Optional structured cost breakdown using benchmark anchors. "
                        "When provided, this gives transparent, auditable cost estimates "
                        "instead of vague ranges. Use anchor_key from the COST ANCHORS reference table."
                    ),
                    "properties": {
                        "anchor_key": {
                            "type": "string",
                            "description": "Key from COST_ANCHORS (e.g., 'app_migration_simple', 'identity_separation', 'cloud_migration')",
                            "enum": [
                                # Application anchors
                                "app_migration_simple", "app_migration_moderate", "app_migration_complex",
                                "license_microsoft", "license_erp",
                                # Infrastructure anchors
                                "dc_migration", "cloud_migration", "storage_migration",
                                # Identity anchors
                                "identity_separation",
                                # Network anchors
                                "network_separation", "wan_setup",
                                # Security anchors
                                "security_remediation", "security_tool_deployment",
                                # Data anchors
                                "data_segregation",
                                # Vendor anchors
                                "vendor_contract_transition",
                                # PMO & Change anchors
                                "pmo_overhead", "change_management",
                                # TSA Exit anchors
                                "tsa_exit_identity", "tsa_exit_email", "tsa_exit_service_desk",
                                "tsa_exit_infrastructure", "tsa_exit_network", "tsa_exit_security",
                                "tsa_exit_erp_support",
                            ],
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Number of units (users, apps, sites, etc.) — use 1 for fixed costs. MUST come from cited facts.",
                            "minimum": 1,
                        },
                        "unit_label": {
                            "type": "string",
                            "description": "What the quantity represents",
                            "enum": ["users", "applications", "sites", "servers", "vendors",
                                     "data_centers", "terabytes", "organization", "endpoints"],
                        },
                        "size_tier": {
                            "type": "string",
                            "description": "For fixed_by_size anchors: which tier applies based on quantity",
                            "enum": ["small", "medium", "large"],
                        },
                        "assumptions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of assumptions underlying this estimate (e.g., 'Standard complexity migration', '500 users from F-TGT-APP-001')",
                        },
                        "source_facts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Fact IDs that provide the quantities used (e.g., 'F-TGT-APP-001' for user count)",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Additional context about the estimate",
                        },
                    },
                    "required": ["anchor_key", "quantity", "unit_label", "source_facts"],
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
                },
                "target_action": {
                    "type": "string",
                    "description": "REQUIRED: What the TARGET must do (target-scoped action). Example: 'Inventory SAP custom objects; engage licensing for migration terms'. Do NOT use 'Buyer should...' language here."
                },
                "integration_option": {
                    "type": "string",
                    "description": "OPTIONAL: Alternative/additional path depending on buyer integration strategy. Example: 'If buyer confirms Oracle harmonization, add ETL buildout (+6 months)'. Buyer-dependent language is allowed here."
                },
                "overlap_id": {
                    "type": "string",
                    "description": "Link to OverlapCandidate (OC-xxx) if this work item stems from a target-buyer comparison"
                },
                "target_facts_cited": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Target fact IDs (F-TGT-xxx) that drive this work item"
                },
                "buyer_facts_cited": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Buyer fact IDs (F-BYR-xxx) if this is integration-related work"
                }
            },
            "required": ["domain", "title", "description", "phase", "priority",
                        "owner_type", "cost_estimate", "triggered_by", "confidence", "reasoning",
                        "mna_lens", "mna_implication", "target_action"]
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
# ENTITY VALIDATION (Runtime Enforcement)
# =============================================================================

# Tools that create findings and should be validated
FINDING_TOOLS = ["identify_risk", "create_strategic_consideration", "create_work_item", "create_recommendation"]

# Patterns that indicate buyer-action language (should be rejected or reframed)
BUYER_ACTION_PATTERNS = [
    (r"\bbuyer\s+should\b", "Buyer should"),
    (r"\bbuyer\s+must\b", "Buyer must"),
    (r"\bbuyer\s+needs?\s+to\b", "Buyer needs to"),
    (r"\brecommend.*\bbuyer\b", "recommend...buyer"),
    (r"\bbuyer\s+will\s+need\b", "Buyer will need"),
]


def validate_finding_entity_rules(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that a finding follows entity separation rules.

    Rules enforced:
    1. ANCHOR RULE: Findings citing buyer facts MUST also cite target facts
    2. SCOPE RULE: "Buyer should..." language is rejected (except in integration_option)
    3. TARGET ACTION RULE: Work items should describe target-side actions

    Args:
        tool_name: Name of the tool being called
        tool_input: Input parameters for the tool

    Returns:
        Dict with:
        - valid: bool - whether the finding passes validation
        - errors: List[str] - blocking errors (finding should be rejected)
        - warnings: List[str] - non-blocking issues (finding accepted with warning)
        - auto_tags: Dict - fields to auto-set (e.g., integration_related)
    """
    errors = []
    warnings = []
    auto_tags = {}

    # Extract fact citations
    based_on = tool_input.get("based_on_facts", [])

    # For work items, also check triggered_by field
    if tool_name == "create_work_item":
        triggered_by = tool_input.get("triggered_by", [])
        # Combine both sources for entity detection
        all_citations = based_on + triggered_by
    else:
        all_citations = based_on

    # Separate by entity based on ID patterns
    target_facts = [f for f in all_citations if "TGT" in f.upper()]
    buyer_facts = [f for f in all_citations if "BYR" in f.upper()]

    # Also check legacy format (F-APP-xxx without entity prefix)
    legacy_facts = [f for f in all_citations if "TGT" not in f.upper() and "BYR" not in f.upper()]

    # =========================================================================
    # RULE 1: ANCHOR RULE - Buyer facts require target facts
    # =========================================================================
    if buyer_facts and not target_facts:
        errors.append(
            f"ENTITY_ANCHOR_VIOLATION: Finding cites buyer facts {buyer_facts} "
            f"but no target facts. All findings must anchor in target data. "
            f"Either add target fact citations or remove buyer references."
        )

    # =========================================================================
    # RULE 2: AUTO-TAG integration_related based on citations
    # =========================================================================
    if buyer_facts:
        auto_tags["integration_related"] = True
        # Also track which buyer facts were cited (for traceability)
        auto_tags["_buyer_facts_cited"] = buyer_facts
        auto_tags["_target_facts_cited"] = target_facts
    else:
        auto_tags["integration_related"] = False

    # =========================================================================
    # RULE 3: SCOPE RULE - Check for "Buyer should..." language
    # =========================================================================
    # Fields to check for buyer-action language
    fields_to_check = {
        "description": tool_input.get("description", ""),
        "title": tool_input.get("title", ""),
        "mitigation": tool_input.get("mitigation", ""),
        "reasoning": tool_input.get("reasoning", ""),
        "rationale": tool_input.get("rationale", ""),
        "target_action": tool_input.get("target_action", ""),  # Definitely shouldn't have buyer language
    }

    # integration_option is ALLOWED to have buyer references
    # (that's the whole point of that field)

    for field_name, field_value in fields_to_check.items():
        if not field_value:
            continue

        for pattern, friendly_name in BUYER_ACTION_PATTERNS:
            if re.search(pattern, field_value, re.IGNORECASE):
                if field_name == "target_action":
                    # Hard error - target_action must be target-scoped
                    errors.append(
                        f"SCOPE_VIOLATION in {field_name}: Contains '{friendly_name}' language. "
                        f"target_action must describe what the TARGET does, not the buyer. "
                        f"Move buyer-related actions to integration_option field."
                    )
                else:
                    # Warning for other fields - reframe as target action
                    warnings.append(
                        f"SCOPE_WARNING in {field_name}: Contains '{friendly_name}' language. "
                        f"Consider reframing as target-side action (e.g., 'Target must migrate to...' "
                        f"instead of 'Buyer should accept...'). "
                        f"If describing optional integration path, use integration_option field."
                    )

    # =========================================================================
    # RULE 4: WORK ITEM RULE - Should have target action focus
    # =========================================================================
    if tool_name == "create_work_item":
        description = tool_input.get("description", "")
        target_action = tool_input.get("target_action", "")

        # If there's no target_action and description mentions buyer heavily
        if not target_action:
            buyer_mentions = len(re.findall(r'\bbuyer\b', description, re.IGNORECASE))
            target_mentions = len(re.findall(r'\btarget\b', description, re.IGNORECASE))

            if buyer_mentions > target_mentions and buyer_mentions > 2:
                warnings.append(
                    f"FOCUS_WARNING: Work item description mentions 'buyer' {buyer_mentions} times "
                    f"vs 'target' {target_mentions} times. Work items should focus on target-side actions. "
                    f"Consider using target_action field to clarify the target's responsibility."
                )

    # =========================================================================
    # RULE 5: LEGACY FACT ID WARNING
    # =========================================================================
    if legacy_facts:
        warnings.append(
            f"LEGACY_FACT_IDS: Found fact IDs without entity prefix: {legacy_facts}. "
            f"New fact IDs should use F-TGT-xxx or F-BYR-xxx format for clarity."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "auto_tags": auto_tags
    }


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

    Includes runtime validation for entity separation rules:
    - Buyer facts must be accompanied by target facts
    - "Buyer should..." language is flagged/rejected
    - Auto-tags integration_related based on citations

    Args:
        tool_name: Name of the tool to execute
        tool_input: Tool input parameters
        reasoning_store: ReasoningStore instance to record findings

    Returns:
        Dict with result status and any generated IDs
    """
    # =========================================================================
    # PRE-EXECUTION VALIDATION (for finding-creating tools)
    # =========================================================================
    validation_result = None
    if tool_name in FINDING_TOOLS:
        validation_result = validate_finding_entity_rules(tool_name, tool_input)

        # Log validation results
        if validation_result["errors"]:
            for error in validation_result["errors"]:
                logger.warning(f"[VALIDATION ERROR] {tool_name}: {error}")

        if validation_result["warnings"]:
            for warning in validation_result["warnings"]:
                logger.info(f"[VALIDATION WARNING] {tool_name}: {warning}")

        # If validation fails (has errors), return error response
        # This enforces the rules - model must fix and retry
        if not validation_result["valid"]:
            return {
                "status": "validation_error",
                "message": "Finding rejected due to entity rule violations. Please fix and retry.",
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"],
                "guidance": (
                    "Entity rules: (1) Buyer facts (F-BYR-xxx) require target facts (F-TGT-xxx) - "
                    "all findings must anchor in target. (2) Avoid 'Buyer should...' language - "
                    "reframe as target-side actions. (3) Use integration_option field for "
                    "buyer-dependent paths."
                )
            }

        # Apply auto-tags to input (e.g., integration_related)
        if validation_result["auto_tags"]:
            for key, value in validation_result["auto_tags"].items():
                if not key.startswith("_"):  # Skip internal tracking fields
                    tool_input[key] = value

    # =========================================================================
    # TOOL EXECUTION
    # =========================================================================
    # Overlap map should be generated first
    if tool_name == "generate_overlap_map":
        result = _execute_generate_overlap_map(tool_input, reasoning_store)
    elif tool_name == "identify_risk":
        result = _execute_identify_risk(tool_input, reasoning_store)
    elif tool_name == "create_strategic_consideration":
        result = _execute_create_strategic_consideration(tool_input, reasoning_store)
    elif tool_name == "create_work_item":
        result = _execute_create_work_item(tool_input, reasoning_store)
    elif tool_name == "create_recommendation":
        result = _execute_create_recommendation(tool_input, reasoning_store)
    elif tool_name == "create_function_story":
        result = _execute_create_function_story(tool_input, reasoning_store)
    elif tool_name == "complete_reasoning":
        result = _execute_complete_reasoning(tool_input, reasoning_store)
    else:
        return {
            "status": "error",
            "message": f"Unknown reasoning tool: {tool_name}"
        }

    # =========================================================================
    # POST-EXECUTION: Attach validation warnings to successful results
    # =========================================================================
    if validation_result and validation_result["warnings"] and result.get("status") == "success":
        result["validation_warnings"] = validation_result["warnings"]
        result["message"] = result.get("message", "") + " (with warnings - see validation_warnings)"

    return result


def _execute_generate_overlap_map(
    input_data: Dict[str, Any],
    reasoning_store: ReasoningStore
) -> Dict[str, Any]:
    """
    Execute generate_overlap_map tool.

    This should be called FIRST before any findings are generated.
    It creates structured comparisons between target and buyer systems.
    """
    try:
        overlap_candidates = input_data.get("overlap_candidates", [])

        if not overlap_candidates:
            return {
                "status": "warning",
                "message": "No overlap candidates provided. If buyer facts exist, you should compare them to target facts.",
                "overlap_ids": []
            }

        created_ids = []
        warnings = []

        for candidate in overlap_candidates:
            # Validate required fields
            required = ["domain", "overlap_type", "target_fact_ids", "buyer_fact_ids",
                       "target_summary", "buyer_summary", "why_it_matters", "confidence"]
            missing = [f for f in required if f not in candidate or not candidate.get(f)]

            if missing:
                warnings.append(f"Overlap candidate missing fields: {missing}")
                continue

            # Validate overlap_type
            overlap_type = candidate.get("overlap_type")
            if overlap_type not in OVERLAP_TYPES:
                warnings.append(f"Invalid overlap_type '{overlap_type}'. Valid types: {OVERLAP_TYPES}")
                continue

            # Validate fact ID prefixes
            target_facts = candidate.get("target_fact_ids", [])
            buyer_facts = candidate.get("buyer_fact_ids", [])

            # Check for entity mixing in fact IDs
            target_has_buyer = any("BYR" in fid for fid in target_facts)
            buyer_has_target = any("TGT" in fid for fid in buyer_facts)

            if target_has_buyer:
                warnings.append(f"target_fact_ids contains buyer fact IDs - check your citations")
            if buyer_has_target:
                warnings.append(f"buyer_fact_ids contains target fact IDs - check your citations")

            # Add the overlap candidate
            try:
                oc_id = reasoning_store.add_overlap_candidate(
                    domain=candidate.get("domain"),
                    overlap_type=overlap_type,
                    target_fact_ids=target_facts,
                    buyer_fact_ids=buyer_facts,
                    target_summary=candidate.get("target_summary", ""),
                    buyer_summary=candidate.get("buyer_summary", ""),
                    why_it_matters=candidate.get("why_it_matters", ""),
                    confidence=candidate.get("confidence", 0.5),
                    missing_info_questions=candidate.get("missing_info_questions", [])
                )
                created_ids.append(oc_id)
            except Exception as e:
                warnings.append(f"Failed to create overlap candidate: {str(e)}")

        result = {
            "status": "success",
            "message": f"Created {len(created_ids)} overlap candidates",
            "overlap_ids": created_ids,
            "count": len(created_ids)
        }

        if warnings:
            result["warnings"] = warnings

        return result

    except Exception as e:
        logger.error(f"Error in generate_overlap_map: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to generate overlap map: {str(e)}"
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

        # Entity validation: validate risk_scope
        risk_scope = input_data.get("risk_scope", "target_standalone")
        VALID_RISK_SCOPES = ["target_standalone", "integration_dependent", "buyer_action"]
        if risk_scope not in VALID_RISK_SCOPES:
            return {
                "status": "error",
                "message": f"Invalid risk_scope '{risk_scope}'. Must be one of: {VALID_RISK_SCOPES}"
            }

        # Determine entity from cited facts
        entity = _infer_entity_from_citations(based_on, reasoning_store.fact_store)

        # ANCHOR RULE enforcement:
        # If buyer facts are cited, at least one target fact must also be cited
        buyer_facts = [f for f in based_on if "BYR" in f.upper()]
        target_facts = [f for f in based_on if "TGT" in f.upper()]

        if buyer_facts and not target_facts:
            return {
                "status": "error",
                "message": "ANCHOR RULE violation: Risks citing buyer facts must also cite at least one target fact. "
                           "Buyer facts provide context, but risks must be anchored to target observations."
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
            mna_implication=input_data.get("mna_implication", ""),
            integration_related=input_data.get("integration_related", False),
            overlap_id=input_data.get("overlap_id"),
            entity=entity,
            risk_scope=risk_scope,
        )

        return {
            "status": "success",
            "risk_id": risk_id,
            "entity": entity,
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

        # Entity inference from citations
        entity = _infer_entity_from_citations(based_on, reasoning_store.fact_store)

        # ANCHOR RULE for buyer-context considerations
        buyer_facts = [f for f in based_on if "BYR" in f.upper()]
        target_facts = [f for f in based_on if "TGT" in f.upper()]

        if buyer_facts and not target_facts:
            # Exception: buyer_alignment lens may cite buyer-only facts
            is_buyer_alignment = input_data.get("lens") == "buyer_alignment"
            if not is_buyer_alignment:
                return {
                    "status": "error",
                    "message": "ANCHOR RULE violation: Strategic considerations citing buyer facts must also cite "
                               "at least one target fact to anchor the analysis."
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
            mna_implication=input_data.get("mna_implication", ""),
            integration_related=input_data.get("integration_related", False),
            overlap_id=input_data.get("overlap_id"),
            entity=entity,
        )

        return {
            "status": "success",
            "consideration_id": sc_id,
            "entity": entity,
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

        # Process cost_buildup if provided
        cost_buildup_obj = None
        cost_buildup_input = input_data.get("cost_buildup")

        if cost_buildup_input:
            try:
                from tools_v2.cost_estimator import estimate_cost

                anchor_key = cost_buildup_input.get("anchor_key")
                quantity = cost_buildup_input.get("quantity", 1)
                unit_label = cost_buildup_input.get("unit_label", "organization")
                size_tier = cost_buildup_input.get("size_tier")
                assumptions = cost_buildup_input.get("assumptions", [])
                source_facts = cost_buildup_input.get("source_facts", [])
                notes = cost_buildup_input.get("notes", "")

                # Call the cost estimator to create a CostBuildUp object
                cost_buildup_obj = estimate_cost(
                    anchor_key=anchor_key,
                    quantity=quantity,
                    size_tier=size_tier,
                    source_facts=source_facts,
                    assumptions=assumptions,
                    notes=notes,
                    estimation_source="benchmark",
                    confidence="medium",
                )

                if cost_buildup_obj is None:
                    # Invalid anchor_key or estimation failure - log warning but don't block
                    logger.warning(
                        f"cost_buildup estimation failed for anchor_key='{anchor_key}'. "
                        f"Falling back to cost_estimate='{cost_estimate}'."
                    )
            except Exception as e:
                logger.warning(f"cost_buildup processing error: {e}. Using cost_estimate fallback.")

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
            cost_buildup=cost_buildup_obj,
            triggered_by_risks=input_data.get("triggered_by_risks", []),
            mna_lens=input_data.get("mna_lens", ""),
            mna_implication=input_data.get("mna_implication", ""),
            integration_related=input_data.get("integration_related", False),
            overlap_id=input_data.get("overlap_id"),
            integration_option=input_data.get("integration_option"),
            target_action=input_data.get("target_action", "")
        )

        result = {
            "status": "success",
            "work_item_id": wi_id,
            "message": f"Work item recorded: {input_data.get('title')}"
        }

        # Include cost transparency in response
        if cost_buildup_obj:
            result["cost_buildup_summary"] = cost_buildup_obj.format_summary()
            result["cost_buildup_range"] = f"${cost_buildup_obj.total_low:,.0f} - ${cost_buildup_obj.total_high:,.0f}"

        return result

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

        # Entity inference from citations
        entity = _infer_entity_from_citations(based_on, reasoning_store.fact_store)

        # ANCHOR RULE enforcement
        buyer_facts = [f for f in based_on if "BYR" in f.upper()]
        target_facts = [f for f in based_on if "TGT" in f.upper()]

        if buyer_facts and not target_facts:
            return {
                "status": "error",
                "message": "ANCHOR RULE violation: Recommendations citing buyer facts must also cite "
                           "at least one target fact to anchor the analysis."
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
            mna_implication=input_data.get("mna_implication", ""),
            integration_related=input_data.get("integration_related", False),
            overlap_id=input_data.get("overlap_id"),
            entity=entity,
        )

        return {
            "status": "success",
            "recommendation_id": rec_id,
            "entity": entity,
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


def _infer_entity_from_citations(
    fact_ids: List[str],
    fact_store: "FactStore" = None,
) -> str:
    """Infer the entity scope from cited fact IDs.

    Rules:
    - All target facts -> "target"
    - All buyer facts -> "buyer"
    - Mixed facts -> "target" (target takes precedence; buyer facts provide context)
    - No facts -> "target" (default)
    """
    if not fact_ids:
        return "target"

    has_target = any("TGT" in fid.upper() for fid in fact_ids)
    has_buyer = any("BYR" in fid.upper() for fid in fact_ids)

    if has_target:
        return "target"  # Target takes precedence (even if mixed)
    elif has_buyer:
        return "buyer"
    else:
        # Fallback: check fact_store for entity field
        if fact_store:
            for fid in fact_ids:
                fact = fact_store.get_fact(fid)
                if fact:
                    entity = getattr(fact, 'entity', None)
                    if entity:
                        return entity
        return "target"


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
