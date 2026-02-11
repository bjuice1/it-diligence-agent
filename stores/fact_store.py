"""
Fact Store for V2 Architecture

Central storage for facts extracted during Discovery phase.
Each fact gets a unique ID that Reasoning agents can cite.

Key Features:
- Unique fact IDs (F-INFRA-001, F-NET-002, etc.)
- Domain and category organization
- Merge capability for parallel discovery
- Export/import for reasoning phase handoff
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


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
import logging
import threading

logger = logging.getLogger(__name__)

# Domain prefixes for fact IDs
DOMAIN_PREFIXES = {
    "infrastructure": "INFRA",
    "network": "NET",
    "cybersecurity": "CYBER",
    "applications": "APP",
    "identity_access": "IAM",
    "organization": "ORG",
    "general": "GEN"
}

# Similarity threshold for duplicate detection (Point 72)
DUPLICATE_SIMILARITY_THRESHOLD = 0.85

# Confidence scoring factors (Point 73)
CONFIDENCE_FACTORS = {
    "has_evidence": 0.30,        # Has evidence quote
    "evidence_length": 0.15,    # Evidence quote length
    "has_details": 0.20,        # Has detailed attributes
    "has_source": 0.15,         # Has source document
    "is_verified": 0.20         # Human verified
}

# Verification status options (Phase 1 - Validation Workflow)
class VerificationStatus:
    """Verification status values for facts."""
    PENDING = "pending"          # Not yet reviewed
    CONFIRMED = "confirmed"      # Human confirmed as accurate
    INCORRECT = "incorrect"      # Human marked as incorrect
    NEEDS_INFO = "needs_info"    # Needs more information to verify
    SKIPPED = "skipped"          # Reviewer skipped (will revisit)

VERIFICATION_STATUSES = [
    VerificationStatus.PENDING,
    VerificationStatus.CONFIRMED,
    VerificationStatus.INCORRECT,
    VerificationStatus.NEEDS_INFO,
    VerificationStatus.SKIPPED
]

# Domain priority weights for review queue
DOMAIN_PRIORITY_WEIGHTS = {
    "cybersecurity": 1.0,      # Highest priority - security critical
    "infrastructure": 0.9,
    "applications": 0.8,
    "network": 0.8,
    "identity_access": 0.85,
    "organization": 0.6,
    "general": 0.5
}


@dataclass
class Fact:
    """
    A single extracted fact with unique ID for citation.

    Facts are observations from the document - NOT conclusions.
    The Reasoning phase will analyze facts and draw conclusions.

    Verification Status:
    - verified: Has a human reviewed and confirmed this fact?
    - verified_by: Who verified it (username/email)
    - verified_at: When it was verified (ISO timestamp)
    """
    fact_id: str              # F-INFRA-001
    domain: str               # infrastructure, network, etc.
    category: str             # hosting, compute, storage, etc.
    item: str                 # What this fact is about
    details: Dict[str, Any]   # Flexible key-value pairs
    status: str               # documented, partial, gap
    evidence: Dict[str, str]  # exact_quote, source_section
    entity: str = "target"    # "target" (being acquired) or "buyer" - CRITICAL for avoiding confusion
    analysis_phase: str = "target_extraction"  # "target_extraction" or "buyer_extraction" - which phase created this fact
    is_integration_insight: bool = False       # True if this fact describes cross-entity integration considerations
    source_document: str = "" # Filename of source document (for incremental updates)
    deal_id: str = ""         # Deal this fact belongs to - REQUIRED for proper isolation
    inventory_item_id: str = ""  # Cross-reference to I-APP-xxx, I-INFRA-xxx in InventoryStore
    created_at: str = field(default_factory=lambda: _generate_timestamp())
    updated_at: str = ""      # Set when fact is modified
    # Verification fields - for human-in-the-loop validation
    verified: bool = False              # Has human verified this fact?
    verified_by: Optional[str] = None   # Who verified (username/email)
    verified_at: Optional[str] = None   # When verified (ISO timestamp)
    # Extended verification workflow (Phase 1)
    verification_status: str = "pending"  # pending, confirmed, incorrect, needs_info, skipped
    verification_note: str = ""           # Reviewer's note about verification
    reviewer_id: Optional[str] = None     # Who is assigned to review this fact
    # Confidence scoring (Point 73)
    confidence_score: float = 0.0       # 0.0-1.0 confidence rating
    # Domain overlap detection (Point 75)
    related_domains: List[str] = field(default_factory=list)
    # Needs review flag - for entries that require human validation
    needs_review: bool = False          # Flagged for human review (sparse details, low confidence)
    needs_review_reason: str = ""       # Why it needs review

    def to_dict(self) -> Dict:
        result = asdict(self)
        # Include calculated review priority
        result['review_priority'] = self.review_priority
        return result

    @property
    def review_priority(self) -> float:
        """
        Calculate review priority score (higher = more urgent to review).

        Factors:
        - Domain weight (security > infrastructure > apps > org)
        - Inverse confidence (low confidence = high priority)
        - Evidence quality (no evidence = high priority)
        - Source document (no source = higher priority)

        Returns:
            Float 0.0-1.0 where 1.0 is highest priority
        """
        # Already verified facts have zero priority
        if self.verification_status == VerificationStatus.CONFIRMED:
            return 0.0
        if self.verification_status == VerificationStatus.INCORRECT:
            return 0.0

        # Start with domain weight
        domain_weight = DOMAIN_PRIORITY_WEIGHTS.get(self.domain, 0.5)

        # Inverse confidence (low confidence = high priority)
        confidence_factor = 1.0 - self.confidence_score

        # Evidence quality factor
        evidence_factor = 0.0
        if not self.evidence or not self.evidence.get("exact_quote"):
            evidence_factor = 0.3  # No evidence = boost priority
        elif len(self.evidence.get("exact_quote", "")) < 20:
            evidence_factor = 0.15  # Short evidence = small boost

        # Source document factor
        source_factor = 0.2 if not self.source_document else 0.0

        # Combine factors (weighted average)
        priority = (
            domain_weight * 0.3 +
            confidence_factor * 0.4 +
            evidence_factor +
            source_factor
        )

        return min(1.0, priority)

    def calculate_confidence(self) -> float:
        """Calculate confidence score based on evidence quality (Point 73)."""
        score = 0.0

        # Has evidence quote
        if self.evidence and self.evidence.get("exact_quote"):
            score += CONFIDENCE_FACTORS["has_evidence"]
            # Evidence length bonus
            quote_len = len(self.evidence.get("exact_quote", ""))
            if quote_len >= 50:
                score += CONFIDENCE_FACTORS["evidence_length"]
            elif quote_len >= 20:
                score += CONFIDENCE_FACTORS["evidence_length"] * 0.5

        # Has meaningful details - with domain-specific logic
        if self.details:
            if self.domain == "applications":
                # Applications domain: boost for key fields
                app_key_fields = ['vendor', 'version', 'deployment', 'user_count', 'users', 'criticality']
                key_field_count = sum(1 for f in app_key_fields if f in self.details and self.details[f])
                if key_field_count >= 3:
                    score += CONFIDENCE_FACTORS["has_details"]
                elif key_field_count >= 2:
                    score += CONFIDENCE_FACTORS["has_details"] * 0.75
                elif key_field_count >= 1:
                    score += CONFIDENCE_FACTORS["has_details"] * 0.5
                # Small penalty for apps with no key fields
            elif len(self.details) >= 2:
                score += CONFIDENCE_FACTORS["has_details"]
            else:
                score += CONFIDENCE_FACTORS["has_details"] * 0.5

        # Has source document
        if self.source_document:
            score += CONFIDENCE_FACTORS["has_source"]

        # Is verified
        if self.verified:
            score += CONFIDENCE_FACTORS["is_verified"]

        return min(1.0, score)

    @classmethod
    def from_dict(cls, data: Dict) -> "Fact":
        # Handle backwards compatibility - remove calculated field if present
        data = dict(data)  # Make a copy
        data.pop('review_priority', None)  # Remove calculated field if present

        # Set defaults for new fields if not present (backwards compatibility)
        if 'verification_status' not in data:
            # Migrate from old verified boolean to new status
            if data.get('verified', False):
                data['verification_status'] = VerificationStatus.CONFIRMED
            else:
                data['verification_status'] = VerificationStatus.PENDING
        if 'verification_note' not in data:
            data['verification_note'] = ""
        if 'reviewer_id' not in data:
            data['reviewer_id'] = None
        # New needs_review fields (backwards compatibility)
        if 'needs_review' not in data:
            data['needs_review'] = False
        if 'needs_review_reason' not in data:
            data['needs_review_reason'] = ""
        # Deal isolation (backwards compatibility)
        if 'deal_id' not in data:
            data['deal_id'] = ""  # Legacy facts without deal_id
        # Inventory linking (backwards compatibility - Spec 03)
        if 'inventory_item_id' not in data:
            data['inventory_item_id'] = ""  # Legacy facts without inventory link

        return cls(**data)


@dataclass
class Gap:
    """
    A gap identified during discovery - missing information.

    Gaps are important signals for the Reasoning phase about
    where uncertainty exists.
    """
    gap_id: str               # G-INFRA-001
    domain: str
    category: str
    description: str
    importance: str           # critical, high, medium, low
    entity: str = "target"    # "target" or "buyer" - which entity this gap is for
    deal_id: str = ""         # Deal this gap belongs to - REQUIRED for proper isolation
    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Gap":
        # Handle legacy gaps without entity field
        if 'entity' not in data:
            data['entity'] = 'target'
        # Deal isolation (backwards compatibility)
        if 'deal_id' not in data:
            data['deal_id'] = ""  # Legacy gaps without deal_id
        return cls(**data)


@dataclass
class FactStoreSnapshot:
    """
    Read-only snapshot of facts for context injection.

    Used to provide TARGET facts as immutable context during Phase 2
    (buyer analysis) without risk of modification.

    This is passed to the discovery agents during buyer extraction
    so they can reference what was found about the target company.
    """
    entity: str                    # Which entity this snapshot is for
    facts: List[Dict[str, Any]]    # List of fact dicts (read-only)
    gaps: List[Dict[str, Any]]     # List of gap dicts (read-only)
    created_at: str                # When snapshot was created

    def get_facts_by_domain(self, domain: str) -> List[Dict]:
        """Get facts for a specific domain."""
        return [f for f in self.facts if f.get('domain') == domain]

    def get_facts_by_category(self, domain: str, category: str) -> List[Dict]:
        """Get facts for a specific domain and category."""
        return [f for f in self.facts
                if f.get('domain') == domain and f.get('category') == category]

    def to_context_string(self, include_evidence: bool = False) -> str:
        """
        Format snapshot as context string for LLM prompt injection.

        This produces a structured summary that can be included in
        the buyer analysis prompt as read-only reference.

        Args:
            include_evidence: Whether to include evidence quotes

        Returns:
            Formatted string for prompt injection
        """
        lines = [
            f"=== {self.entity.upper()} COMPANY FACTS (READ-ONLY REFERENCE) ===",
            f"Snapshot created: {self.created_at}",
            f"Total facts: {len(self.facts)}",
            "",
            "IMPORTANT: These facts are about the TARGET company.",
            "Do NOT extract new facts from this section.",
            "Use this as context when analyzing BUYER documents.",
            "",
        ]

        # Group by domain
        by_domain: Dict[str, List[Dict]] = {}
        for fact in self.facts:
            domain = fact.get('domain', 'unknown')
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(fact)

        for domain, domain_facts in sorted(by_domain.items()):
            lines.append(f"## {domain.upper()}")
            for fact in domain_facts:
                item = fact.get('item', 'Unknown')
                category = fact.get('category', 'unknown')
                fact_id = fact.get('fact_id', '')
                lines.append(f"- [{fact_id}] {category}: {item}")

                # Add key details
                details = fact.get('details', {})
                for key in ['vendor', 'version', 'deployment', 'cost', 'user_count']:
                    if key in details and details[key]:
                        lines.append(f"    {key}: {details[key]}")

                if include_evidence:
                    evidence = fact.get('evidence', {})
                    if evidence.get('exact_quote'):
                        quote = evidence['exact_quote'][:200]
                        lines.append(f"    evidence: \"{quote}...\"")

            lines.append("")

        lines.append("=== END TARGET COMPANY FACTS ===")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dict for serialization."""
        return {
            "entity": self.entity,
            "facts": self.facts,
            "gaps": self.gaps,
            "created_at": self.created_at,
            "fact_count": len(self.facts),
            "gap_count": len(self.gaps)
        }


# =============================================================================
# OPEN QUESTION ENTITY (Point 82 - Enhancement Plan)
# =============================================================================

# Suggested recipients for open questions
QUESTION_RECIPIENTS = [
    "Target CIO",
    "Target IT Director",
    "Target Security Lead",
    "Target Infrastructure Lead",
    "Target Applications Lead",
    "Target Network Lead",
    "IT Operations",
    "Integration Team",
    "Management"
]

@dataclass
class OpenQuestion:
    """
    An open question for follow-up with management or target company.

    Open Questions are distinct from Gaps and Risks:
    - Gap: Missing information identified during discovery
    - Risk: A concern based on evidence (facts)
    - OpenQuestion: A specific question to ask stakeholders

    The triage flow is:
    - Gaps → OpenQuestions (transform missing info into actionable questions)
    - Facts → Risks (where evidence supports concern)
    - Risks → WorkItems (remediation actions)
    """
    question_id: str                              # Q-INFRA-001
    question_text: str                            # The actual question to ask
    domain: str                                   # infrastructure, network, etc.
    category: str                                 # Category within domain
    priority: str                                 # critical, high, medium, low
    source_gap_ids: List[str] = field(default_factory=list)  # Gap IDs that led to this question
    suggested_recipient: str = "Management"       # Who should answer this
    context: str = ""                             # Background context for the question
    impact_if_unanswered: str = ""               # Why this question matters
    status: str = "open"                          # open, answered, not_applicable, deferred
    answer: str = ""                              # The answer when provided
    answered_by: str = ""                         # Who provided the answer
    answered_at: str = ""                         # When answered
    deal_id: str = ""                             # Deal this question belongs to
    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "OpenQuestion":
        # Backwards compatibility for deal_id
        if 'deal_id' not in data:
            data = dict(data)
            data['deal_id'] = ""
        return cls(**data)

    def mark_answered(self, answer: str, answered_by: str) -> None:
        """Mark the question as answered."""
        self.status = "answered"
        self.answer = answer
        self.answered_by = answered_by
        self.answered_at = _generate_timestamp()

    def mark_not_applicable(self, reason: str = "") -> None:
        """Mark the question as not applicable."""
        self.status = "not_applicable"
        self.answer = reason or "Not applicable to this assessment"

    def mark_deferred(self, reason: str = "") -> None:
        """Mark the question as deferred for later."""
        self.status = "deferred"
        self.answer = reason or "Deferred for future follow-up"


class FactStore:
    """
    Central store for facts extracted during Discovery phase.

    Features:
    - Unique fact IDs for citation (F-{DOMAIN}-{SEQ})
    - Domain and category organization
    - Merge capability for parallel discovery agents
    - Export to JSON for reasoning phase handoff
    - Load from JSON to resume or reason from existing facts
    - Open Questions for follow-up (Point 82-86)

    Usage:
        # In Discovery agent
        store = FactStore()
        fact_id = store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware Environment",
            details={"platform": "VMware", "version": "6.7"},
            status="documented",
            evidence={"exact_quote": "VMware vSphere 6.7"}
        )

        # Pass to Reasoning agent
        facts = store.get_domain_facts("infrastructure")

        # Transform gaps to open questions
        questions = store.transform_gaps_to_questions()
    """

    def __init__(self, deal_id: str = None):
        """
        Initialize FactStore.

        Args:
            deal_id: Deal ID for scoping all facts/gaps. Required for new stores,
                     can be None when loading legacy data.
        """
        self.deal_id = deal_id
        self.facts: List[Fact] = []
        self.gaps: List[Gap] = []
        self.open_questions: List[OpenQuestion] = []  # Point 82
        self._fact_counters: Dict[str, int] = {}
        self._gap_counters: Dict[str, int] = {}
        self._question_counters: Dict[str, int] = {}  # Point 82
        self.discovery_complete: Dict[str, bool] = {}
        self.metadata: Dict[str, Any] = {
            "created_at": _generate_timestamp(),
            "version": "2.2",  # Version bump for deal isolation
            "deal_id": deal_id or ""
        }
        # Thread safety: Lock for all mutating operations
        self._lock = threading.RLock()
        # Performance: Index for O(1) fact/gap/question lookups
        self._fact_index: Dict[str, Fact] = {}
        self._gap_index: Dict[str, Gap] = {}
        self._question_index: Dict[str, OpenQuestion] = {}  # Point 82

        # Performance: Index for assumed facts (P1 FIX #5: O(N) → O(1) idempotency check)
        # Maps entity → set of category:item keys for assumed facts
        # Example: {"target": {"leadership:CIO", "leadership:VP"}, "buyer": {...}}
        self._assumed_fact_keys_by_entity: Dict[str, set] = {}

        # Warn if no deal_id provided
        if not deal_id:
            logger.warning("FactStore created without deal_id - data isolation may be compromised")

    def add_fact(self, domain: str, category: str, item: str,
                 details: Dict[str, Any], status: str,
                 evidence: Dict[str, str], entity: str = "target",
                 source_document: str = "", needs_review: bool = False,
                 needs_review_reason: str = "",
                 analysis_phase: str = None,
                 is_integration_insight: bool = False,
                 deal_id: str = None) -> str:
        """
        Add a fact and return its unique ID.

        Args:
            domain: infrastructure, network, cybersecurity, etc.
            category: Category within domain (hosting, compute, etc.)
            item: What this fact is about
            details: Flexible key-value pairs (vendor, version, count, etc.)
            status: documented, partial, gap
            evidence: Must include 'exact_quote' from document
            entity: "target" (being acquired) or "buyer" - defaults to target
            source_document: Filename of source document (for incremental updates)
            needs_review: Flag for entries requiring human validation
            needs_review_reason: Why the entry needs review
            analysis_phase: "target_extraction" or "buyer_extraction" (auto-set if None)
            is_integration_insight: True if this is a cross-entity integration observation
            deal_id: Deal ID for scoping (uses store's deal_id if not provided)

        Returns:
            Unique fact ID with entity prefix (e.g., F-TGT-INFRA-001, F-BYR-APP-002)

        Raises:
            ValueError: If entity is invalid, locked, or deal_id missing
        """
        # Resolve deal_id - use provided value or fall back to store's deal_id
        effective_deal_id = deal_id or self.deal_id
        if not effective_deal_id:
            raise ValueError("deal_id is required - provide in add_fact() or store constructor")

        # Validate entity - fail fast instead of silently defaulting
        if entity not in ("target", "buyer"):
            raise ValueError(f"Invalid entity '{entity}'. Must be 'target' or 'buyer'")

        # Check if entity is locked (Two-Phase Analysis protection)
        if self.is_entity_locked(entity):
            raise ValueError(
                f"Cannot add facts for '{entity}' - entity is locked. "
                f"TARGET facts are locked after Phase 1 to prevent contamination. "
                f"Use unlock_entity_facts() only if re-running analysis."
            )

        # Auto-set analysis_phase based on entity if not provided
        if analysis_phase is None:
            analysis_phase = "target_extraction" if entity == "target" else "buyer_extraction"

        # Validate analysis_phase
        if analysis_phase not in ("target_extraction", "buyer_extraction"):
            raise ValueError(f"Invalid analysis_phase '{analysis_phase}'. Must be 'target_extraction' or 'buyer_extraction'")

        # Validate domain against allowed list
        try:
            from config_v2 import DOMAINS
            if domain not in DOMAINS:
                raise ValueError(
                    f"Invalid domain '{domain}'. Must be one of: {', '.join(DOMAINS)}"
                )
        except ImportError:
            # Config not available, skip validation
            pass

        with self._lock:
            fact_id = self._generate_fact_id(domain, entity)

            fact = Fact(
                fact_id=fact_id,
                domain=domain,
                category=category,
                item=item,
                details=details or {},
                status=status,
                evidence=evidence or {},
                entity=entity,
                analysis_phase=analysis_phase,
                is_integration_insight=is_integration_insight,
                source_document=source_document,
                deal_id=effective_deal_id,
                needs_review=needs_review,
                needs_review_reason=needs_review_reason
            )

            # Calculate initial confidence score
            fact.confidence_score = fact.calculate_confidence()

            # Auto-flag for review if confidence is low
            if fact.confidence_score < 0.4 and not fact.needs_review:
                fact.needs_review = True
                fact.needs_review_reason = "Low confidence score"

            self.facts.append(fact)
            self._fact_index[fact_id] = fact  # Update index

            # P1 FIX #5: Update assumed facts index for O(1) idempotency checks
            if fact.domain == "organization" and (fact.details or {}).get('data_source') == 'assumed':
                if entity not in self._assumed_fact_keys_by_entity:
                    self._assumed_fact_keys_by_entity[entity] = set()
                key = f"{fact.category}:{fact.item}"
                self._assumed_fact_keys_by_entity[entity].add(key)
                logger.debug(f"Indexed assumed fact key: {entity}/{key}")

            review_flag = " [NEEDS REVIEW]" if fact.needs_review else ""
            logger.debug(f"Added fact {fact_id}: {item} (confidence: {fact.confidence_score:.2f}){review_flag}")

        return fact_id

    def add_fact_from_dict(self, fact_data: Dict[str, Any], deal_id: str = None) -> Optional['Fact']:
        """
        Add a fact from a dictionary (for incremental updates).

        Args:
            fact_data: Dictionary containing fact fields
            deal_id: Deal ID for scoping (uses store's deal_id if not provided)

        Returns:
            The created Fact object, or None if creation failed
        """
        try:
            domain = fact_data.get("domain", "unknown")
            category = fact_data.get("category", "general")
            item = fact_data.get("item", "")
            details = fact_data.get("details", {})
            status = fact_data.get("status", "documented")
            evidence = fact_data.get("evidence", {})
            entity = fact_data.get("entity", "target")
            source_document = fact_data.get("source_document", "")
            # Use deal_id from fact_data, or provided deal_id, or fall back to store's deal_id
            effective_deal_id = fact_data.get("deal_id") or deal_id or self.deal_id

            if not item:
                return None

            fact_id = self.add_fact(
                domain=domain,
                category=category,
                item=item,
                details=details,
                status=status,
                evidence=evidence,
                entity=entity,
                source_document=source_document,
                deal_id=effective_deal_id
            )

            return self.get_fact(fact_id)

        except Exception as e:
            logger.error(f"Failed to add fact from dict: {e}")
            return None

    def add_gap(self, domain: str, category: str,
                description: str, importance: str,
                entity: str = "target", deal_id: str = None) -> str:
        """
        Add a gap (missing information) and return its ID.

        Args:
            domain: infrastructure, network, etc.
            category: Category within domain
            description: What information is missing
            importance: critical, high, medium, low
            entity: "target" or "buyer" - which entity this gap is for
            deal_id: Deal ID for scoping (uses store's deal_id if not provided)

        Returns:
            Unique gap ID with entity prefix (e.g., G-TGT-INFRA-001, G-BYR-APP-002)

        Raises:
            ValueError: If deal_id is missing
        """
        # Resolve deal_id - use provided value or fall back to store's deal_id
        effective_deal_id = deal_id or self.deal_id
        if not effective_deal_id:
            raise ValueError("deal_id is required - provide in add_gap() or store constructor")

        with self._lock:
            gap_id = self._generate_gap_id(domain, entity)
            gap = Gap(
                gap_id=gap_id,
                domain=domain,
                category=category,
                description=description,
                importance=importance,
                entity=entity,
                deal_id=effective_deal_id
            )

            self.gaps.append(gap)
            self._gap_index[gap_id] = gap  # Update index
            logger.debug(f"Added gap {gap_id}: {description[:50]}...")

        return gap_id

    def _generate_fact_id(self, domain: str, entity: str = "target") -> str:
        """
        Generate unique fact ID with entity prefix: F-{ENTITY}-{DOMAIN}-{SEQ}

        Format:
        - Target facts: F-TGT-APP-001, F-TGT-INFRA-002
        - Buyer facts: F-BYR-APP-001, F-BYR-NET-003

        This makes entity immediately visible in fact IDs, preventing
        accidental mixing of target and buyer facts in reasoning.

        NOTE: Must be called within self._lock context.
        This method modifies self._fact_counters and is not thread-safe on its own.
        """
        entity_prefix = "TGT" if entity == "target" else "BYR"
        domain_prefix = DOMAIN_PREFIXES.get(domain, "GEN")

        # Key counters by entity+domain to keep sequences separate
        counter_key = f"{entity_prefix}_{domain_prefix}"

        if counter_key not in self._fact_counters:
            self._fact_counters[counter_key] = 0

        self._fact_counters[counter_key] += 1
        return f"F-{entity_prefix}-{domain_prefix}-{self._fact_counters[counter_key]:03d}"

    def _generate_gap_id(self, domain: str, entity: str = "target") -> str:
        """
        Generate unique gap ID with entity prefix: G-{ENTITY}-{DOMAIN}-{SEQ}

        Format:
        - Target gaps: G-TGT-APP-001, G-TGT-INFRA-002
        - Buyer gaps: G-BYR-APP-001, G-BYR-NET-003

        This makes entity immediately visible in gap IDs, preventing
        accidental mixing of target and buyer gaps in reasoning.

        NOTE: Must be called within self._lock context.
        This method modifies self._gap_counters and is not thread-safe on its own.
        """
        entity_prefix = "TGT" if entity == "target" else "BYR"
        domain_prefix = DOMAIN_PREFIXES.get(domain, "GEN")

        # Key counters by entity+domain to keep sequences separate
        counter_key = f"{entity_prefix}_{domain_prefix}"

        if counter_key not in self._gap_counters:
            self._gap_counters[counter_key] = 0

        self._gap_counters[counter_key] += 1
        return f"G-{entity_prefix}-{domain_prefix}-{self._gap_counters[counter_key]:03d}"

    def get_fact(self, fact_id: str) -> Optional[Fact]:
        """Get a specific fact by ID (O(1) lookup using index)."""
        with self._lock:
            return self._fact_index.get(fact_id)

    def get_gap(self, gap_id: str) -> Optional[Gap]:
        """Get a specific gap by ID (O(1) lookup using index)."""
        with self._lock:
            return self._gap_index.get(gap_id)

    def get_assumed_fact_keys(self, entity: str) -> set:
        """
        Get set of category:item keys for assumed facts for an entity (O(1) lookup).

        P1 FIX #5: Enables O(1) idempotency check in assumption merge instead of
        O(N) scan through all facts.

        Args:
            entity: "target" or "buyer"

        Returns:
            Set of "category:item" keys for assumed facts, e.g. {"leadership:CIO", "leadership:VP"}
            Empty set if no assumed facts exist for this entity.
        """
        with self._lock:
            return self._assumed_fact_keys_by_entity.get(entity, set()).copy()

    def get_domain_facts(self, domain: str) -> Dict[str, Any]:
        """
        Get all facts for a domain, organized for reasoning.

        Returns:
            Dict with:
            - domain: str
            - facts: List of fact dicts
            - gaps: List of gap dicts
            - fact_count: int
            - gap_count: int
            - categories: Dict of category -> facts
        """
        with self._lock:
            domain_facts = [f for f in self.facts if f.domain == domain]
            domain_gaps = [g for g in self.gaps if g.domain == domain]

            # Organize by category
            by_category: Dict[str, List[Dict]] = {}
            for fact in domain_facts:
                cat = fact.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(fact.to_dict())

            return {
                "domain": domain,
                "facts": [f.to_dict() for f in domain_facts],
                "gaps": [g.to_dict() for g in domain_gaps],
                "fact_count": len(domain_facts),
                "gap_count": len(domain_gaps),
                "categories": by_category
            }

    def get_all_facts(self) -> Dict[str, Any]:
        """
        Get complete fact inventory across all domains.

        Returns:
            Dict with all facts, gaps, open questions, and metadata
        """
        with self._lock:
            all_domains = set(f.domain for f in self.facts) | set(g.domain for g in self.gaps)

            return {
                "metadata": self.metadata,
                "summary": {
                    "total_facts": len(self.facts),
                    "total_gaps": len(self.gaps),
                    "total_open_questions": len(self.open_questions),
                    "domains": list(all_domains)
                },
                "facts": [f.to_dict() for f in self.facts],
                "gaps": [g.to_dict() for g in self.gaps],
                "open_questions": [q.to_dict() for q in self.open_questions],
                "by_domain": {d: self.get_domain_facts(d) for d in all_domains},
                "discovery_complete": self.discovery_complete
            }

    def get_all_fact_ids(self) -> List[str]:
        """Get list of all fact IDs (for validation)."""
        with self._lock:
            return [f.fact_id for f in self.facts]

    def get_all_gap_ids(self) -> List[str]:
        """Get list of all gap IDs (for validation)."""
        with self._lock:
            return [g.gap_id for g in self.gaps]

    def get_all_citable_ids(self) -> List[str]:
        """Get list of all citable IDs (facts and gaps) for validation."""
        with self._lock:
            return [f.fact_id for f in self.facts] + [g.gap_id for g in self.gaps]

    def get_entity_facts(self, entity: str, domain: str = None) -> List[Fact]:
        """
        Get facts for a specific entity (target or buyer).

        Args:
            entity: "target" or "buyer"
            domain: Optional domain filter

        Returns:
            List of facts for that entity
        """
        with self._lock:
            facts = [f for f in self.facts if f.entity == entity]
            if domain:
                facts = [f for f in facts if f.domain == domain]
            return facts

    def get_entity_inventory(self, entity: str) -> Dict[str, Any]:
        """
        Get complete inventory for a specific entity.

        Returns dict organized by domain and category.
        """
        with self._lock:
            entity_facts = [f for f in self.facts if f.entity == entity]

            by_domain: Dict[str, Dict[str, List[Dict]]] = {}
            for fact in entity_facts:
                if fact.domain not in by_domain:
                    by_domain[fact.domain] = {}
                if fact.category not in by_domain[fact.domain]:
                    by_domain[fact.domain][fact.category] = []
                by_domain[fact.domain][fact.category].append(fact.to_dict())

            return {
                "entity": entity,
                "fact_count": len(entity_facts),
                "domains": list(by_domain.keys()),
                "by_domain": by_domain
            }

    def compare_entities(self, domain: str = None, category: str = None) -> Dict[str, Any]:
        """
        Compare target vs buyer facts to identify overlaps and conflicts.

        Useful for integration planning and preventing confusion.

        Args:
            domain: Optional domain to filter comparison
            category: Optional category to filter comparison

        Returns:
            Dict with target-only, buyer-only, shared, and conflicts
        """
        with self._lock:
            # Get facts directly from lists (already inside lock)
            target_facts = [f for f in self.facts if f.entity == "target"]
            buyer_facts = [f for f in self.facts if f.entity == "buyer"]

            if domain:
                target_facts = [f for f in target_facts if f.domain == domain]
                buyer_facts = [f for f in buyer_facts if f.domain == domain]

            if category:
                target_facts = [f for f in target_facts if f.category == category]
                buyer_facts = [f for f in buyer_facts if f.category == category]

            # Build lookup by item/category for comparison (case-insensitive)
            target_items = {(f.category.lower(), f.item.lower()): f for f in target_facts}
            buyer_items = {(f.category.lower(), f.item.lower()): f for f in buyer_facts}

            target_only = []
            buyer_only = []
            shared = []
            conflicts = []

            # Find target-only and shared/conflicts
            for key, fact in target_items.items():
                if key in buyer_items:
                    buyer_fact = buyer_items[key]
                    # Check if details differ (potential conflict)
                    target_vendor = fact.details.get("vendor", "").lower()
                    buyer_vendor = buyer_fact.details.get("vendor", "").lower()
                    if target_vendor and buyer_vendor and target_vendor != buyer_vendor:
                        conflicts.append({
                            "category": key[0],
                            "item": fact.item,
                            "target": fact.to_dict(),
                            "buyer": buyer_fact.to_dict(),
                            "conflict_type": "vendor_mismatch"
                        })
                    else:
                        shared.append({
                            "category": key[0],
                            "item": fact.item,
                            "target_fact_id": fact.fact_id,
                            "buyer_fact_id": buyer_fact.fact_id
                        })
                else:
                    target_only.append(fact.to_dict())

            # Find buyer-only
            for key, fact in buyer_items.items():
                if key not in target_items:
                    buyer_only.append(fact.to_dict())

            return {
                "filter": {"domain": domain, "category": category},
                "target_only_count": len(target_only),
                "buyer_only_count": len(buyer_only),
                "shared_count": len(shared),
                "conflict_count": len(conflicts),
                "target_only": target_only,
                "buyer_only": buyer_only,
                "shared": shared,
                "conflicts": conflicts
            }

    # =========================================================================
    # TWO-PHASE ANALYSIS: ENTITY LOCKING & INTEGRATION INSIGHTS
    # =========================================================================

    def lock_entity_facts(self, entity: str) -> int:
        """
        Lock all facts for an entity, preventing modification.

        Used after Phase 1 (target extraction) to ensure TARGET facts
        are immutable before Phase 2 (buyer extraction) begins.

        Args:
            entity: "target" or "buyer"

        Returns:
            Number of facts locked
        """
        with self._lock:
            if f"_locked_{entity}" not in self.metadata:
                self.metadata[f"_locked_{entity}"] = False

            if self.metadata[f"_locked_{entity}"]:
                logger.warning(f"Entity '{entity}' facts are already locked")
                return 0

            entity_facts = [f for f in self.facts if f.entity == entity]
            self.metadata[f"_locked_{entity}"] = True
            self.metadata[f"_locked_{entity}_at"] = _generate_timestamp()
            self.metadata[f"_locked_{entity}_count"] = len(entity_facts)

            logger.info(f"Locked {len(entity_facts)} {entity} facts")
            return len(entity_facts)

    def is_entity_locked(self, entity: str) -> bool:
        """Check if facts for an entity are locked."""
        return self.metadata.get(f"_locked_{entity}", False)

    def unlock_entity_facts(self, entity: str) -> bool:
        """
        Unlock facts for an entity (use with caution).

        This should only be used when re-running analysis.
        """
        with self._lock:
            if not self.metadata.get(f"_locked_{entity}", False):
                return False

            self.metadata[f"_locked_{entity}"] = False
            self.metadata.pop(f"_locked_{entity}_at", None)
            logger.warning(f"Unlocked {entity} facts - they can now be modified")
            return True

    def get_integration_insights(self) -> List[Fact]:
        """
        Get all facts marked as integration insights.

        Integration insights are observations about how TARGET and BUYER
        systems will need to interact post-acquisition.
        """
        with self._lock:
            return [f for f in self.facts if f.is_integration_insight]

    def add_integration_insight(
        self,
        domain: str,
        category: str,
        item: str,
        details: Dict[str, Any],
        evidence: Dict[str, str],
        target_fact_ids: List[str] = None,
        buyer_fact_ids: List[str] = None,
        source_document: str = ""
    ) -> str:
        """
        Add an integration insight that references both TARGET and BUYER facts.

        Integration insights are special facts created during Phase 2 that
        describe how systems from both entities will need to integrate.

        Args:
            domain: Domain of the insight
            category: Category within domain
            item: Brief description of the integration point
            details: Integration details (should include target_system, buyer_system, etc.)
            evidence: Evidence supporting the insight
            target_fact_ids: List of TARGET fact IDs this insight references
            buyer_fact_ids: List of BUYER fact IDs this insight references
            source_document: Source document for the insight

        Returns:
            Fact ID of the new integration insight
        """
        # Enrich details with cross-references
        enriched_details = {
            **details,
            "target_fact_references": target_fact_ids or [],
            "buyer_fact_references": buyer_fact_ids or [],
            "insight_type": "integration"
        }

        # Add as a buyer-phase fact with integration flag
        return self.add_fact(
            domain=domain,
            category=category,
            item=item,
            details=enriched_details,
            status="documented",
            evidence=evidence,
            entity="buyer",  # Integration insights come from buyer analysis phase
            source_document=source_document,
            analysis_phase="buyer_extraction",
            is_integration_insight=True
        )

    def create_snapshot(self, entity: str = "target") -> 'FactStoreSnapshot':
        """
        Create a read-only snapshot of facts for context injection.

        Used to provide TARGET facts as context during Phase 2 (buyer analysis)
        without risk of modification.

        Args:
            entity: Which entity's facts to snapshot (default: "target")

        Returns:
            FactStoreSnapshot with read-only view of facts
        """
        with self._lock:
            facts = [f for f in self.facts if f.entity == entity]
            gaps = [g for g in self.gaps if g.entity == entity]
            return FactStoreSnapshot(
                entity=entity,
                facts=[f.to_dict() for f in facts],
                gaps=[g.to_dict() for g in gaps],
                created_at=_generate_timestamp()
            )

    def get_phase_summary(self) -> Dict[str, Any]:
        """
        Get summary of analysis phases and entity breakdown.

        Returns:
            Dict with phase status, fact counts by entity, and lock status
        """
        with self._lock:
            target_facts = [f for f in self.facts if f.entity == "target"]
            buyer_facts = [f for f in self.facts if f.entity == "buyer"]
            integration_insights = [f for f in self.facts if f.is_integration_insight]

            return {
                "target": {
                    "fact_count": len(target_facts),
                    "locked": self.is_entity_locked("target"),
                    "locked_at": self.metadata.get("_locked_target_at"),
                    "domains": list(set(f.domain for f in target_facts))
                },
                "buyer": {
                    "fact_count": len(buyer_facts),
                    "locked": self.is_entity_locked("buyer"),
                    "locked_at": self.metadata.get("_locked_buyer_at"),
                    "domains": list(set(f.domain for f in buyer_facts))
                },
                "integration_insights": {
                    "count": len(integration_insights),
                    "domains": list(set(f.domain for f in integration_insights))
                },
                "total_facts": len(self.facts),
                "total_gaps": len(self.gaps)
            }

    # =========================================================================
    # SOURCE DOCUMENT TRACKING (for incremental updates)
    # =========================================================================

    def get_facts_by_source(self, source_document: str) -> List[Fact]:
        """
        Get all facts from a specific source document.

        Args:
            source_document: Filename of the source document

        Returns:
            List of facts from that document
        """
        with self._lock:
            return [f for f in self.facts if f.source_document == source_document]

    def get_source_documents(self) -> List[str]:
        """Get list of all source documents that contributed facts."""
        with self._lock:
            return list(set(f.source_document for f in self.facts if f.source_document))

    def get_facts_by_sources(self, source_documents: List[str]) -> List[Fact]:
        """Get facts from multiple source documents."""
        with self._lock:
            source_set = set(source_documents)
            return [f for f in self.facts if f.source_document in source_set]

    def remove_facts_from_source(self, source_document: str) -> int:
        """
        Remove all facts from a specific source document.

        Used when a document is re-processed (changed since last run).

        Args:
            source_document: Filename of the source document

        Returns:
            Number of facts removed
        """
        with self._lock:
            original_count = len(self.facts)
            # Remove from list and index
            facts_to_remove = [f for f in self.facts if f.source_document == source_document]
            for fact in facts_to_remove:
                self.facts.remove(fact)
                self._fact_index.pop(fact.fact_id, None)  # Remove from index
            
            removed = original_count - len(self.facts)
            if removed > 0:
                logger.info(f"Removed {removed} facts from source: {source_document}")
            return removed

    def get_source_summary(self) -> Dict[str, Any]:
        """
        Get summary of facts by source document.

        Returns:
            Dict mapping source document to fact count and domains covered
        """
        with self._lock:
            summary = {}
            for fact in self.facts:
                src = fact.source_document or "(unknown)"
                if src not in summary:
                    summary[src] = {"fact_count": 0, "domains": set()}
                summary[src]["fact_count"] += 1
                summary[src]["domains"].add(fact.domain)

            # Convert sets to lists for JSON serialization
            for src in summary:
                summary[src]["domains"] = list(summary[src]["domains"])

            return summary

    def validate_fact_citations(self, cited_ids: List[str]) -> Dict[str, Any]:
        """
        Validate that cited fact or gap IDs exist.

        Both facts (F-*) and gaps (G-*) are valid citation targets.
        A risk can be based on documented facts or on identified gaps
        (e.g., "risk due to missing DR documentation" cites the gap).

        Args:
            cited_ids: List of fact or gap IDs to validate

        Returns:
            Dict with valid, invalid, and validation_rate
        """
        valid_ids = set(self.get_all_citable_ids())

        valid = [fid for fid in cited_ids if fid in valid_ids]
        invalid = [fid for fid in cited_ids if fid not in valid_ids]

        return {
            "valid": valid,
            "invalid": invalid,
            "total_cited": len(cited_ids),
            "validation_rate": len(valid) / len(cited_ids) if cited_ids else 1.0
        }

    # =========================================================================
    # HUMAN VERIFICATION (anti-hallucination anchor)
    # =========================================================================

    def verify_fact(self, fact_id: str, verified_by: str) -> bool:
        """
        Mark a fact as human-verified.

        Args:
            fact_id: The fact ID to verify
            verified_by: Username/email of person verifying

        Returns:
            True if fact was found and verified, False otherwise
        """
        with self._lock:
            fact = self._fact_index.get(fact_id)
            if not fact:
                logger.warning(f"Cannot verify - fact not found: {fact_id}")
                return False

            fact.verified = True
            fact.verified_by = verified_by
            fact.verified_at = _generate_timestamp()
            fact.updated_at = _generate_timestamp()
            logger.info(f"Fact {fact_id} verified by {verified_by}")
            return True

    def unverify_fact(self, fact_id: str) -> bool:
        """
        Remove verification status from a fact.

        Args:
            fact_id: The fact ID to unverify

        Returns:
            True if fact was found and unverified, False otherwise
        """
        with self._lock:
            fact = self._fact_index.get(fact_id)
            if not fact:
                return False

            fact.verified = False
            fact.verified_by = None
            fact.verified_at = None
            fact.updated_at = _generate_timestamp()
            logger.info(f"Fact {fact_id} verification removed")
            return True

    def get_verified_facts(self, domain: str = None) -> List[Fact]:
        """
        Get all verified facts, optionally filtered by domain.

        Args:
            domain: Optional domain filter

        Returns:
            List of verified facts
        """
        with self._lock:
            facts = [f for f in self.facts if f.verified]
            if domain:
                facts = [f for f in facts if f.domain == domain]
            return facts

    def get_unverified_facts(self, domain: str = None) -> List[Fact]:
        """
        Get all unverified facts, optionally filtered by domain.

        Args:
            domain: Optional domain filter

        Returns:
            List of unverified facts
        """
        with self._lock:
            facts = [f for f in self.facts if not f.verified]
            if domain:
                facts = [f for f in facts if f.domain == domain]
            return facts

    def get_verification_stats(self) -> Dict[str, Any]:
        """
        Get verification statistics across all facts.

        Returns:
            Dict with counts, rates, and breakdown by domain
        """
        with self._lock:
            total = len(self.facts)
            verified = sum(1 for f in self.facts if f.verified)
            unverified = total - verified

            # Breakdown by domain
            by_domain = {}
            for fact in self.facts:
                if fact.domain not in by_domain:
                    by_domain[fact.domain] = {"total": 0, "verified": 0}
                by_domain[fact.domain]["total"] += 1
                if fact.verified:
                    by_domain[fact.domain]["verified"] += 1

            # Calculate rates
            for domain in by_domain:
                domain_total = by_domain[domain]["total"]
                domain_verified = by_domain[domain]["verified"]
                by_domain[domain]["rate"] = (
                    domain_verified / domain_total if domain_total > 0 else 0.0
                )

            return {
                "total_facts": total,
                "verified_count": verified,
                "unverified_count": unverified,
                "verification_rate": verified / total if total > 0 else 0.0,
                "by_domain": by_domain
            }

    def get_review_queue(
        self,
        domain: str = None,
        limit: int = 50,
        include_skipped: bool = False
    ) -> List[Fact]:
        """
        Get facts needing review, sorted by priority.

        Priority is calculated based on:
        - Domain weight (security > infrastructure > apps)
        - Inverse confidence (low confidence = high priority)
        - Evidence quality (no evidence = high priority)

        Args:
            domain: Optional domain filter
            limit: Max facts to return (default 50)
            include_skipped: Include previously skipped facts

        Returns:
            List of facts sorted by review priority (highest first)
        """
        with self._lock:
            # Filter to reviewable facts
            reviewable_statuses = [VerificationStatus.PENDING]
            if include_skipped:
                reviewable_statuses.append(VerificationStatus.SKIPPED)

            facts = [
                f for f in self.facts
                if f.verification_status in reviewable_statuses
            ]

            # Apply domain filter
            if domain:
                facts = [f for f in facts if f.domain == domain]

            # Sort by review priority (highest first)
            facts.sort(key=lambda f: f.review_priority, reverse=True)

            # Apply limit
            return facts[:limit]

    def get_review_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive review queue statistics.

        Returns:
            Dict with queue stats, progress by domain, priority breakdown
        """
        with self._lock:
            total = len(self.facts)

            # Count by verification status
            by_status = {
                VerificationStatus.PENDING: 0,
                VerificationStatus.CONFIRMED: 0,
                VerificationStatus.INCORRECT: 0,
                VerificationStatus.NEEDS_INFO: 0,
                VerificationStatus.SKIPPED: 0
            }
            for fact in self.facts:
                status = fact.verification_status
                if status in by_status:
                    by_status[status] += 1

            # Priority breakdown
            high_priority = sum(1 for f in self.facts if f.review_priority >= 0.7)
            medium_priority = sum(1 for f in self.facts if 0.4 <= f.review_priority < 0.7)
            low_priority = sum(1 for f in self.facts if 0.0 < f.review_priority < 0.4)

            # By domain progress
            by_domain = {}
            for fact in self.facts:
                if fact.domain not in by_domain:
                    by_domain[fact.domain] = {
                        "total": 0,
                        "pending": 0,
                        "confirmed": 0,
                        "incorrect": 0,
                        "needs_info": 0
                    }
                by_domain[fact.domain]["total"] += 1
                if fact.verification_status == VerificationStatus.PENDING:
                    by_domain[fact.domain]["pending"] += 1
                elif fact.verification_status == VerificationStatus.CONFIRMED:
                    by_domain[fact.domain]["confirmed"] += 1
                elif fact.verification_status == VerificationStatus.INCORRECT:
                    by_domain[fact.domain]["incorrect"] += 1
                elif fact.verification_status == VerificationStatus.NEEDS_INFO:
                    by_domain[fact.domain]["needs_info"] += 1

            # Calculate completion rates
            for domain in by_domain:
                d = by_domain[domain]
                d["completion_rate"] = d["confirmed"] / d["total"] if d["total"] > 0 else 0.0

            pending_count = by_status[VerificationStatus.PENDING]
            confirmed_count = by_status[VerificationStatus.CONFIRMED]

            return {
                "total_facts": total,
                "queue_size": pending_count + by_status[VerificationStatus.SKIPPED],
                "pending": pending_count,
                "confirmed": confirmed_count,
                "incorrect": by_status[VerificationStatus.INCORRECT],
                "needs_info": by_status[VerificationStatus.NEEDS_INFO],
                "skipped": by_status[VerificationStatus.SKIPPED],
                "completion_rate": confirmed_count / total if total > 0 else 0.0,
                "priority_breakdown": {
                    "high": high_priority,
                    "medium": medium_priority,
                    "low": low_priority
                },
                "by_domain": by_domain,
                # Phase 5: Enhanced stats
                "confidence_breakdown": self._get_confidence_breakdown(),
                "verified_today": self._get_verified_today_count(),
                "remaining_critical": self._get_remaining_critical_count(),
                "reviewer_stats": self._get_reviewer_stats(),
                "average_confidence": self._get_average_confidence()
            }

    def _get_confidence_breakdown(self) -> Dict[str, int]:
        """Get count of facts by confidence tier."""
        high = sum(1 for f in self.facts if f.confidence_score >= 0.8)
        medium = sum(1 for f in self.facts if 0.5 <= f.confidence_score < 0.8)
        low = sum(1 for f in self.facts if f.confidence_score < 0.5)
        return {"high": high, "medium": medium, "low": low}

    def _get_verified_today_count(self) -> int:
        """Count facts verified in the last 24 hours."""
        from datetime import datetime, timedelta
        today = datetime.now().date()
        count = 0
        for fact in self.facts:
            if fact.verification_status == VerificationStatus.CONFIRMED and fact.updated_at:
                try:
                    verified_date = datetime.fromisoformat(fact.updated_at.replace('Z', '+00:00')).date()
                    if verified_date == today:
                        count += 1
                except (ValueError, AttributeError):
                    pass
        return count

    def _get_remaining_critical_count(self) -> int:
        """Count pending facts with high priority (security + low confidence)."""
        return sum(1 for f in self.facts
                   if f.verification_status == VerificationStatus.PENDING
                   and f.review_priority >= 0.7)

    def _get_reviewer_stats(self) -> List[Dict[str, Any]]:
        """Get verification stats per reviewer."""
        reviewer_counts = {}
        for fact in self.facts:
            if fact.verification_status in [VerificationStatus.CONFIRMED, VerificationStatus.INCORRECT]:
                reviewer = fact.reviewer_id or "unknown"
                if reviewer not in reviewer_counts:
                    reviewer_counts[reviewer] = {"confirmed": 0, "incorrect": 0}
                if fact.verification_status == VerificationStatus.CONFIRMED:
                    reviewer_counts[reviewer]["confirmed"] += 1
                else:
                    reviewer_counts[reviewer]["incorrect"] += 1

        # Sort by total reviews
        result = []
        for reviewer, counts in reviewer_counts.items():
            total = counts["confirmed"] + counts["incorrect"]
            result.append({
                "reviewer_id": reviewer,
                "confirmed": counts["confirmed"],
                "incorrect": counts["incorrect"],
                "total": total
            })
        return sorted(result, key=lambda x: x["total"], reverse=True)

    def _get_average_confidence(self) -> float:
        """Get average confidence score across all facts."""
        if not self.facts:
            return 0.0
        return sum(f.confidence_score for f in self.facts) / len(self.facts)

    def update_verification_status(
        self,
        fact_id: str,
        status: str,
        reviewer_id: str,
        note: str = ""
    ) -> bool:
        """
        Update verification status for a fact.

        Args:
            fact_id: The fact ID to update
            status: New verification status (pending, confirmed, incorrect, needs_info, skipped)
            reviewer_id: Who is making this update
            note: Optional verification note

        Returns:
            True if fact was found and updated, False otherwise
        """
        if status not in VERIFICATION_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {VERIFICATION_STATUSES}")

        with self._lock:
            fact = self._fact_index.get(fact_id)
            if not fact:
                logger.warning(f"Cannot update verification - fact not found: {fact_id}")
                return False

            # Update verification fields
            fact.verification_status = status
            fact.reviewer_id = reviewer_id
            fact.updated_at = _generate_timestamp()

            if note:
                fact.verification_note = note

            # Also update legacy verified boolean for backwards compatibility
            if status == VerificationStatus.CONFIRMED:
                fact.verified = True
                fact.verified_by = reviewer_id
                fact.verified_at = _generate_timestamp()
            elif status in [VerificationStatus.INCORRECT, VerificationStatus.PENDING]:
                fact.verified = False
                fact.verified_by = None
                fact.verified_at = None

            # Recalculate confidence (verified status affects it)
            fact.confidence_score = fact.calculate_confidence()

            logger.info(f"Fact {fact_id} status updated to {status} by {reviewer_id}")
            return True

    def bulk_verify(self, fact_ids: List[str], verified_by: str) -> Dict[str, int]:
        """
        Verify multiple facts at once.

        Args:
            fact_ids: List of fact IDs to verify
            verified_by: Username/email of person verifying

        Returns:
            Dict with success and failure counts
        """
        results = {"verified": 0, "not_found": 0}
        for fact_id in fact_ids:
            if self.verify_fact(fact_id, verified_by):
                results["verified"] += 1
            else:
                results["not_found"] += 1
        return results

    def mark_discovery_complete(self, domain: str,
                                 categories_covered: List[str],
                                 categories_missing: List[str] = None):
        """Mark discovery as complete for a domain."""
        self.discovery_complete[domain] = {
            "complete": True,
            "completed_at": _generate_timestamp(),
            "categories_covered": categories_covered,
            "categories_missing": categories_missing or []
        }

    def merge_from(self, other: "FactStore") -> Dict[str, int]:
        """
        Merge facts from another store (for parallel discovery).

        PRESERVES original IDs to maintain citation integrity.
        Updates internal counters to prevent future ID conflicts.
        THREAD-SAFE: All operations are protected by internal lock.

        Args:
            other: Another FactStore to merge from

        Returns:
            Dict with counts of merged items
        """
        with self._lock:
            counts = {"facts": 0, "gaps": 0, "duplicates": 0}

            # Get existing IDs to check for duplicates (use index for O(1) lookup)
            existing_fact_ids = set(self._fact_index.keys())
            existing_gap_ids = set(self._gap_index.keys())

            for fact in other.facts:
                if fact.fact_id in existing_fact_ids:
                    counts["duplicates"] += 1
                    logger.warning(f"Duplicate fact ID during merge: {fact.fact_id}")
                    continue

                # Add fact directly with original ID preserved
                self.facts.append(fact)
                self._fact_index[fact.fact_id] = fact  # Update index
                existing_fact_ids.add(fact.fact_id)
                counts["facts"] += 1

                # Update counter to avoid future conflicts (atomic within lock)
                # Parse ID like "F-INFRA-001" -> prefix="INFRA", seq=1
                try:
                    parts = fact.fact_id.split("-")
                    if len(parts) >= 3:
                        prefix = parts[1]
                        seq = int(parts[2])
                        current_max = self._fact_counters.get(prefix, 0)
                        if seq > current_max:
                            self._fact_counters[prefix] = seq
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse fact ID for counter update: {fact.fact_id}")

            for gap in other.gaps:
                if gap.gap_id in existing_gap_ids:
                    counts["duplicates"] += 1
                    logger.warning(f"Duplicate gap ID during merge: {gap.gap_id}")
                    continue

                # Add gap directly with original ID preserved
                self.gaps.append(gap)
                self._gap_index[gap.gap_id] = gap  # Update index
                existing_gap_ids.add(gap.gap_id)
                counts["gaps"] += 1

                # Update counter to avoid future conflicts (atomic within lock)
                try:
                    parts = gap.gap_id.split("-")
                    if len(parts) >= 3:
                        prefix = parts[1]
                        seq = int(parts[2])
                        current_max = self._gap_counters.get(prefix, 0)
                        if seq > current_max:
                            self._gap_counters[prefix] = seq
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse gap ID for counter update: {gap.gap_id}")

            # Merge discovery_complete status
            for domain, status in other.discovery_complete.items():
                if domain not in self.discovery_complete:
                    self.discovery_complete[domain] = status

            logger.info(f"Merged {counts['facts']} facts and {counts['gaps']} gaps (skipped {counts['duplicates']} duplicates)")
            return counts

    def save(self, path: str):
        """Save fact store to JSON file with retry logic."""
        from tools_v2.io_utils import safe_file_write
        
        data = self.get_all_facts()
        safe_file_write(path, data, mode='w', encoding='utf-8', max_retries=3)
        
        logger.info(f"Saved {len(self.facts)} facts to {path}")

    @classmethod
    def load(cls, path: str, deal_id: str = None) -> "FactStore":
        """
        Load fact store from JSON file with retry logic.

        Args:
            path: Path to JSON file
            deal_id: Optional deal_id to use (overrides metadata deal_id)

        Returns:
            Loaded FactStore instance
        """
        from tools_v2.io_utils import safe_file_read

        data = safe_file_read(path, mode='r', encoding='utf-8', max_retries=3)

        # Get deal_id from argument, or from metadata, or None
        metadata = data.get("metadata", {})
        effective_deal_id = deal_id or metadata.get("deal_id")

        store = cls(deal_id=effective_deal_id)
        store.metadata = metadata

        # Load facts with robust ID parsing and index building
        for fact_dict in data.get("facts", []):
            fact = Fact.from_dict(fact_dict)
            store.facts.append(fact)
            store._fact_index[fact.fact_id] = fact  # Build index

            # Update counters to continue from loaded IDs (robust parsing)
            # Supports both legacy F-DOMAIN-SEQ and new F-ENTITY-DOMAIN-SEQ formats
            try:
                parts = fact.fact_id.split("-")
                if len(parts) == 4:
                    # New format: F-TGT-INFRA-001 -> counter_key="TGT_INFRA", seq=1
                    counter_key = f"{parts[1]}_{parts[2]}"
                    seq = int(parts[3])
                    store._fact_counters[counter_key] = max(
                        store._fact_counters.get(counter_key, 0), seq
                    )
                elif len(parts) == 3:
                    # Legacy format: F-INFRA-001 -> counter_key="INFRA", seq=1
                    prefix = parts[1]
                    seq = int(parts[2])
                    store._fact_counters[prefix] = max(
                        store._fact_counters.get(prefix, 0), seq
                    )
                else:
                    logger.warning(f"Unexpected fact ID format: {fact.fact_id}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse fact ID {fact.fact_id}: {e}")

        # Load gaps with robust ID parsing and index building
        for gap_dict in data.get("gaps", []):
            gap = Gap.from_dict(gap_dict)
            store.gaps.append(gap)
            store._gap_index[gap.gap_id] = gap  # Build index

            try:
                parts = gap.gap_id.split("-")
                if len(parts) == 4:
                    # New format: G-TGT-INFRA-001 -> counter_key="TGT_INFRA", seq=1
                    counter_key = f"{parts[1]}_{parts[2]}"
                    seq = int(parts[3])
                    store._gap_counters[counter_key] = max(
                        store._gap_counters.get(counter_key, 0), seq
                    )
                elif len(parts) == 3:
                    # Legacy format: G-INFRA-001
                    prefix = parts[1]
                    seq = int(parts[2])
                    store._gap_counters[prefix] = max(
                        store._gap_counters.get(prefix, 0), seq
                    )
                else:
                    logger.warning(f"Unexpected gap ID format: {gap.gap_id}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse gap ID {gap.gap_id}: {e}")

        # Load open questions (Point 82)
        for question_dict in data.get("open_questions", []):
            question = OpenQuestion.from_dict(question_dict)
            store.open_questions.append(question)
            store._question_index[question.question_id] = question

            try:
                parts = question.question_id.split("-")
                if len(parts) == 4:
                    counter_key = f"{parts[1]}_{parts[2]}"
                    seq = int(parts[3])
                    store._question_counters[counter_key] = max(
                        store._question_counters.get(counter_key, 0), seq
                    )
                elif len(parts) == 3:
                    prefix = parts[1]
                    seq = int(parts[2])
                    store._question_counters[prefix] = max(
                        store._question_counters.get(prefix, 0), seq
                    )
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse question ID {question.question_id}: {e}")

        store.discovery_complete = data.get("discovery_complete", {})

        logger.info(f"Loaded {len(store.facts)} facts, {len(store.gaps)} gaps, {len(store.open_questions)} questions from {path}")
        return store

    def format_for_reasoning(self, domain: str, entity: str = "target") -> str:
        """
        Format facts for injection into reasoning prompt.

        Creates a readable format with fact IDs that the
        reasoning agent can cite.

        Args:
            domain: Domain to format
            entity: "target" or "buyer" - which entity's facts to include

        Returns:
            Formatted string for {inventory} placeholder
        """
        with self._lock:
            # Filter by entity
            entity_facts = [f for f in self.facts if f.domain == domain and f.entity == entity]
            domain_gaps = [g for g in self.gaps if g.domain == domain]

            entity_label = "TARGET" if entity == "target" else "BUYER"
            lines = [f"## {domain.upper()} INVENTORY ({entity_label})\n"]
            lines.append(f"Total Facts: {len(entity_facts)}")
            lines.append(f"Gaps Identified: {len(domain_gaps)}\n")

            # Group by category
            by_category: Dict[str, List[Dict]] = {}
            for fact in entity_facts:
                if fact.category not in by_category:
                    by_category[fact.category] = []
                by_category[fact.category].append(fact.to_dict())

            for category, facts in by_category.items():
                lines.append(f"### {category.upper()}")

                for fact in facts:
                    lines.append(f"\n**{fact['fact_id']}**: {fact['item']}")

                    # Format details
                    if fact['details']:
                        details_str = ", ".join(
                            f"{k}={v}" for k, v in fact['details'].items()
                        )
                        lines.append(f"- Details: {details_str}")

                    lines.append(f"- Status: {fact['status']}")
                    lines.append(f"- Entity: {fact.get('entity', 'target')}")

                    # Include evidence quote (truncated)
                    quote = fact['evidence'].get('exact_quote', '')
                    if quote:
                        truncated = quote[:150] + "..." if len(quote) > 150 else quote
                        lines.append(f"- Evidence: \"{truncated}\"")

                lines.append("")  # Blank line between categories

            # Add gaps section
            if domain_gaps:
                lines.append("\n### IDENTIFIED GAPS")
                for gap in domain_gaps:
                    lines.append(f"\n**{gap.gap_id}**: [{gap.importance.upper()}] {gap.description}")

            # Add comparison note if buyer facts exist for same domain
            buyer_facts = [f for f in self.facts if f.domain == domain and f.entity == "buyer"]
            if buyer_facts and entity == "target":
                lines.append("\n### BUYER CONTEXT (for integration planning)")
                lines.append(f"Note: {len(buyer_facts)} buyer facts exist in this domain for comparison")

            return "\n".join(lines)

    def format_for_reasoning_with_buyer_context(
        self,
        domain: str,
        overlaps: List = None
    ) -> str:
        """
        Format facts with BOTH target and buyer context for buyer-aware reasoning.

        This is the CRITICAL FIX for buyer-aware reasoning. Unlike format_for_reasoning()
        which only returns one entity, this combines TARGET + BUYER facts in a single
        inventory with clear separation and guardrails.

        Args:
            domain: Domain to format (applications, infrastructure, etc.)
            overlaps: Optional list of OverlapCandidate objects for this domain

        Returns:
            Formatted string with:
            - Section 1: TARGET COMPANY INVENTORY
            - Section 2: BUYER COMPANY REFERENCE (if buyer facts exist)
            - Section 3: OVERLAP MAP (if overlaps provided)
            - Section 4: ANALYSIS GUARDRAILS

        BUYER-AWARE REASONING FIX (2026-02-04):
        This function solves the root cause of buyer-aware features not working.
        Before this fix, reasoning agents only received target facts because
        format_for_reasoning() had entity="target" default and no way to combine both.
        """
        from config.buyer_context_config import should_include_buyer_facts, get_buyer_fact_limit

        with self._lock:
            # Get target facts (always include)
            target_facts = [f for f in self.facts if f.domain == domain and f.entity == "target"]
            domain_gaps = [g for g in self.gaps if g.domain == domain]

            # Get buyer facts (if configured for this domain)
            buyer_facts = []
            if should_include_buyer_facts(domain):
                all_buyer_facts = [f for f in self.facts if f.domain == domain and f.entity == "buyer"]
                buyer_fact_limit = get_buyer_fact_limit(domain)

                # Apply limit if configured
                if buyer_fact_limit > 0 and len(all_buyer_facts) > buyer_fact_limit:
                    buyer_facts = all_buyer_facts[:buyer_fact_limit]
                else:
                    buyer_facts = all_buyer_facts

            lines = []

            # ======================================================================
            # SECTION 1: TARGET COMPANY INVENTORY
            # ======================================================================
            lines.append("## TARGET COMPANY INVENTORY\n")
            lines.append(f"Entity: TARGET")
            lines.append(f"Total Facts: {len(target_facts)}")
            lines.append(f"Gaps Identified: {len(domain_gaps)}\n")

            # Group target facts by category
            target_by_category: Dict[str, List[Dict]] = {}
            for fact in target_facts:
                if fact.category not in target_by_category:
                    target_by_category[fact.category] = []
                target_by_category[fact.category].append(fact.to_dict())

            for category, facts in target_by_category.items():
                lines.append(f"### {category.upper()}")

                for fact in facts:
                    lines.append(f"\n**{fact['fact_id']}**: {fact['item']}")

                    # Format details
                    if fact['details']:
                        details_str = ", ".join(
                            f"{k}={v}" for k, v in fact['details'].items()
                        )
                        lines.append(f"- Details: {details_str}")

                    lines.append(f"- Status: {fact['status']}")
                    lines.append(f"- Entity: {fact.get('entity', 'target')}")

                    # Include evidence quote (truncated)
                    quote = fact['evidence'].get('exact_quote', '')
                    if quote:
                        truncated = quote[:150] + "..." if len(quote) > 150 else quote
                        lines.append(f"- Evidence: \"{truncated}\"")

                lines.append("")  # Blank line between categories

            # Add gaps section
            if domain_gaps:
                lines.append("\n### IDENTIFIED GAPS")
                for gap in domain_gaps:
                    lines.append(f"\n**{gap.gap_id}**: [{gap.importance.upper()}] {gap.description}")

            # ======================================================================
            # SECTION 2: BUYER COMPANY REFERENCE (Conditional)
            # ======================================================================
            if buyer_facts:
                lines.append("\n" + "="*70)
                lines.append("\n## BUYER COMPANY REFERENCE (Read-Only Context)\n")
                lines.append("⚠️ **PURPOSE**: Understand integration implications and overlaps ONLY.")
                lines.append("⚠️ **DO NOT**: Create risks, work items, or recommendations FOR the buyer.")
                lines.append("⚠️ **DO**: Use buyer facts to inform target-focused integration analysis.\n")

                lines.append(f"Entity: BUYER")
                lines.append(f"Total Facts Available: {len(buyer_facts)}")
                lines.append("")

                # Group buyer facts by category
                buyer_by_category: Dict[str, List[Dict]] = {}
                for fact in buyer_facts:
                    if fact.category not in buyer_by_category:
                        buyer_by_category[fact.category] = []
                    buyer_by_category[fact.category].append(fact.to_dict())

                for category, facts in buyer_by_category.items():
                    lines.append(f"### {category.upper()}")

                    for fact in facts:
                        lines.append(f"\n**{fact['fact_id']}**: {fact['item']}")

                        # Format details
                        if fact['details']:
                            details_str = ", ".join(
                                f"{k}={v}" for k, v in fact['details'].items()
                            )
                            lines.append(f"- Details: {details_str}")

                        lines.append(f"- Status: {fact['status']}")
                        lines.append(f"- Entity: {fact.get('entity', 'buyer')}")

                    lines.append("")  # Blank line between categories

            # ======================================================================
            # SECTION 3: OVERLAP MAP (If provided)
            # ======================================================================
            if overlaps and buyer_facts:
                lines.append("\n" + "="*70)
                lines.append("\n## PRE-COMPUTED OVERLAP MAP\n")
                lines.append(f"The following {len(overlaps)} overlaps were detected between target and buyer:\n")

                for overlap in overlaps:
                    # Handle both dict and object formats
                    overlap_id = overlap.get('overlap_id') if isinstance(overlap, dict) else overlap.overlap_id
                    overlap_type = overlap.get('overlap_type') if isinstance(overlap, dict) else overlap.overlap_type
                    target_summary = overlap.get('target_summary') if isinstance(overlap, dict) else overlap.target_summary
                    buyer_summary = overlap.get('buyer_summary') if isinstance(overlap, dict) else overlap.buyer_summary
                    why_it_matters = overlap.get('why_it_matters') if isinstance(overlap, dict) else overlap.why_it_matters
                    confidence = overlap.get('confidence') if isinstance(overlap, dict) else overlap.confidence
                    target_fact_ids = overlap.get('target_fact_ids') if isinstance(overlap, dict) else overlap.target_fact_ids
                    buyer_fact_ids = overlap.get('buyer_fact_ids') if isinstance(overlap, dict) else overlap.buyer_fact_ids

                    lines.append(f"### {overlap_id}: {overlap_type.replace('_', ' ').title()}")
                    lines.append(f"**Target**: {target_summary}")
                    lines.append(f"**Buyer**: {buyer_summary}")
                    lines.append(f"**Why It Matters**: {why_it_matters}")
                    lines.append(f"**Confidence**: {confidence}")
                    lines.append(f"**Cites**: Target {target_fact_ids}, Buyer {buyer_fact_ids}")
                    lines.append("")

            # ======================================================================
            # SECTION 4: ANALYSIS GUARDRAILS
            # ======================================================================
            if buyer_facts:
                lines.append("\n" + "="*70)
                lines.append("\n## ANALYSIS GUARDRAILS\n")
                lines.append("When using buyer facts in your analysis:")
                lines.append("")
                lines.append("1. **TARGET FOCUS**: All findings (risks, work items, considerations) must be about the TARGET company")
                lines.append("   - ✅ Good: \"Target's SAP requires migration to buyer's Oracle\"")
                lines.append("   - ❌ Bad: \"Buyer should upgrade their Oracle to match target\"")
                lines.append("")
                lines.append("2. **ANCHOR RULE**: If citing buyer facts (F-BYR-xxx), you MUST also cite target facts (F-TGT-xxx)")
                lines.append("   - Buyer facts provide CONTEXT for target-focused findings")
                lines.append("   - No findings should be based solely on buyer facts")
                lines.append("")
                lines.append("3. **INTEGRATION CONTEXT**: Use buyer data to inform:")
                lines.append("   - Integration complexity (platform mismatches)")
                lines.append("   - Migration decisions (standardization targets)")
                lines.append("   - Consolidation opportunities (capability overlaps)")
                lines.append("   - Day-1 continuity (dependencies on buyer systems)")
                lines.append("")
                lines.append("4. **WORK ITEM STRUCTURE**: For integration-related work items:")
                lines.append("   - `target_action`: What TARGET must do (always required)")
                lines.append("   - `integration_option`: Buyer-dependent paths (optional)")
                lines.append("   - `overlap_id`: Reference to overlap from map above")
                lines.append("   - `integration_related`: Auto-set to true if buyer facts cited")
                lines.append("")
                lines.append("5. **VALIDATION**: Your findings will be validated against these rules")
                lines.append("   - Violations will be flagged or rejected")
                lines.append("   - See runtime validation in reasoning_tools.py")

            return "\n".join(lines)

    def __repr__(self) -> str:
        return f"FactStore(facts={len(self.facts)}, gaps={len(self.gaps)})"

    # =========================================================================
    # DOCUMENT COVERAGE TRACKING (Point 71)
    # =========================================================================

    def get_document_coverage(self) -> Dict[str, Any]:
        """
        Track which documents were analyzed by which agents (Point 71).

        Returns detailed breakdown of document -> domain -> facts.
        """
        with self._lock:
            coverage = {}

            for fact in self.facts:
                doc = fact.source_document or "(unknown)"
                domain = fact.domain

                if doc not in coverage:
                    coverage[doc] = {
                        "domains_covered": set(),
                        "fact_count": 0,
                        "categories": set(),
                        "agents": set()
                    }

                coverage[doc]["domains_covered"].add(domain)
                coverage[doc]["fact_count"] += 1
                coverage[doc]["categories"].add(fact.category)

            # Convert sets to lists for JSON serialization
            for doc in coverage:
                coverage[doc]["domains_covered"] = list(coverage[doc]["domains_covered"])
                coverage[doc]["categories"] = list(coverage[doc]["categories"])
                coverage[doc]["agents"] = list(coverage[doc]["agents"])

            # Generate summary
            total_docs = len(coverage)
            docs_with_multi_domain = sum(
                1 for d in coverage.values()
                if len(d["domains_covered"]) > 1
            )

            return {
                "total_documents": total_docs,
                "documents_with_multi_domain_coverage": docs_with_multi_domain,
                "documents": coverage,
                "coverage_summary": self._calculate_coverage_summary(coverage)
            }

    def _calculate_coverage_summary(self, coverage: Dict) -> Dict[str, Any]:
        """Generate coverage summary statistics."""
        domains_seen = set()
        categories_seen = set()

        for doc_data in coverage.values():
            domains_seen.update(doc_data["domains_covered"])
            categories_seen.update(doc_data["categories"])

        return {
            "domains_covered": list(domains_seen),
            "categories_covered": list(categories_seen),
            "total_domain_count": len(domains_seen),
            "total_category_count": len(categories_seen)
        }

    def get_uncovered_documents(self, all_documents: List[str]) -> List[str]:
        """Return documents that haven't produced any facts."""
        covered = set(self.get_source_documents())
        return [d for d in all_documents if d not in covered]

    # =========================================================================
    # FACT DEDUPLICATION (Point 72)
    # =========================================================================

    def find_duplicates(self, threshold: float = DUPLICATE_SIMILARITY_THRESHOLD) -> List[Dict]:
        """
        Find potential duplicate facts (Point 72).

        Uses item + category similarity to detect duplicates.
        Returns list of duplicate pairs with similarity scores.
        """
        with self._lock:
            duplicates = []

            for i, fact1 in enumerate(self.facts):
                for fact2 in self.facts[i + 1:]:
                    # Same domain and category are more likely duplicates
                    if fact1.domain != fact2.domain:
                        continue

                    similarity = self._calculate_fact_similarity(fact1, fact2)

                    if similarity >= threshold:
                        duplicates.append({
                            "fact1_id": fact1.fact_id,
                            "fact2_id": fact2.fact_id,
                            "item1": fact1.item,
                            "item2": fact2.item,
                            "domain": fact1.domain,
                            "similarity": similarity,
                            "recommendation": self._get_duplicate_recommendation(fact1, fact2)
                        })

            return duplicates

    def _calculate_fact_similarity(self, fact1: Fact, fact2: Fact) -> float:
        """Calculate similarity between two facts."""
        # Item text similarity
        item1_words = set(fact1.item.lower().split())
        item2_words = set(fact2.item.lower().split())

        if not item1_words or not item2_words:
            return 0.0

        intersection = item1_words & item2_words
        union = item1_words | item2_words
        jaccard = len(intersection) / len(union) if union else 0

        # Category match bonus
        category_match = 1.0 if fact1.category == fact2.category else 0.0

        # Details similarity
        details_sim = 0.0
        if fact1.details and fact2.details:
            common_keys = set(fact1.details.keys()) & set(fact2.details.keys())
            if common_keys:
                matching_values = sum(
                    1 for k in common_keys
                    if str(fact1.details[k]).lower() == str(fact2.details[k]).lower()
                )
                details_sim = matching_values / len(common_keys)

        # Weighted average
        return 0.5 * jaccard + 0.3 * category_match + 0.2 * details_sim

    def _get_duplicate_recommendation(self, fact1: Fact, fact2: Fact) -> str:
        """Generate recommendation for handling duplicate."""
        # Prefer verified facts
        if fact1.verified and not fact2.verified:
            return f"Keep {fact1.fact_id} (verified)"
        if fact2.verified and not fact1.verified:
            return f"Keep {fact2.fact_id} (verified)"

        # Prefer facts with more evidence
        ev1_len = len(fact1.evidence.get("exact_quote", "")) if fact1.evidence else 0
        ev2_len = len(fact2.evidence.get("exact_quote", "")) if fact2.evidence else 0
        if ev1_len > ev2_len:
            return f"Keep {fact1.fact_id} (better evidence)"
        if ev2_len > ev1_len:
            return f"Keep {fact2.fact_id} (better evidence)"

        # Prefer facts with more details
        d1_len = len(fact1.details) if fact1.details else 0
        d2_len = len(fact2.details) if fact2.details else 0
        if d1_len > d2_len:
            return f"Keep {fact1.fact_id} (more details)"
        if d2_len > d1_len:
            return f"Keep {fact2.fact_id} (more details)"

        return "Manual review recommended"

    def deduplicate(self, threshold: float = DUPLICATE_SIMILARITY_THRESHOLD) -> Dict[str, Any]:
        """
        Remove duplicate facts automatically.

        Returns summary of removed duplicates.
        """
        duplicates = self.find_duplicates(threshold)
        removed = []

        with self._lock:
            for dup in duplicates:
                # Determine which to remove based on recommendation
                rec = dup["recommendation"]
                if "Keep " + dup["fact1_id"] in rec:
                    to_remove = dup["fact2_id"]
                elif "Keep " + dup["fact2_id"] in rec:
                    to_remove = dup["fact1_id"]
                else:
                    continue  # Manual review needed, skip

                # Remove the duplicate
                fact = self._fact_index.get(to_remove)
                if fact:
                    self.facts.remove(fact)
                    del self._fact_index[to_remove]
                    removed.append(to_remove)

        return {
            "duplicates_found": len(duplicates),
            "automatically_removed": len(removed),
            "removed_fact_ids": removed,
            "manual_review_needed": len(duplicates) - len(removed)
        }

    # =========================================================================
    # CONFIDENCE SCORING (Point 73)
    # =========================================================================

    def calculate_all_confidence_scores(self) -> Dict[str, float]:
        """Calculate and update confidence scores for all facts."""
        scores = {}
        with self._lock:
            for fact in self.facts:
                score = fact.calculate_confidence()
                fact.confidence_score = score
                scores[fact.fact_id] = score
        return scores

    def get_low_confidence_facts(self, threshold: float = 0.5) -> List[Fact]:
        """Get facts with confidence below threshold."""
        with self._lock:
            return [f for f in self.facts if f.confidence_score < threshold]

    def get_high_confidence_facts(self, threshold: float = 0.8) -> List[Fact]:
        """Get facts with confidence above threshold."""
        with self._lock:
            return [f for f in self.facts if f.confidence_score >= threshold]

    def get_confidence_summary(self) -> Dict[str, Any]:
        """Get summary of confidence scores across all facts."""
        self.calculate_all_confidence_scores()

        with self._lock:
            if not self.facts:
                return {"total": 0, "average": 0, "distribution": {}}

            scores = [f.confidence_score for f in self.facts]
            return {
                "total_facts": len(scores),
                "average_confidence": sum(scores) / len(scores),
                "min_confidence": min(scores),
                "max_confidence": max(scores),
                "distribution": {
                    "high_confidence_90+": sum(1 for s in scores if s >= 0.9),
                    "good_confidence_70-89": sum(1 for s in scores if 0.7 <= s < 0.9),
                    "medium_confidence_50-69": sum(1 for s in scores if 0.5 <= s < 0.7),
                    "low_confidence_under_50": sum(1 for s in scores if s < 0.5)
                }
            }

    # =========================================================================
    # GAP DETECTION IMPROVEMENTS (Point 74)
    # =========================================================================

    def analyze_gaps(self) -> Dict[str, Any]:
        """
        Analyze gaps and identify missing information patterns (Point 74).
        """
        with self._lock:
            if not self.gaps:
                return {"total_gaps": 0, "by_importance": {}, "by_domain": {}}

            by_importance = {}
            by_domain = {}
            by_category = {}

            for gap in self.gaps:
                # Group by importance
                imp = gap.importance
                if imp not in by_importance:
                    by_importance[imp] = []
                by_importance[imp].append(gap.to_dict())

                # Group by domain
                dom = gap.domain
                if dom not in by_domain:
                    by_domain[dom] = []
                by_domain[dom].append(gap.to_dict())

                # Group by category
                cat = gap.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(gap.to_dict())

            return {
                "total_gaps": len(self.gaps),
                "critical_gaps": len(by_importance.get("critical", [])),
                "high_gaps": len(by_importance.get("high", [])),
                "by_importance": {k: len(v) for k, v in by_importance.items()},
                "by_domain": {k: len(v) for k, v in by_domain.items()},
                "by_category": {k: len(v) for k, v in by_category.items()},
                "gaps_by_importance": by_importance
            }

    def suggest_followup_questions(self) -> List[Dict[str, str]]:
        """Generate follow-up questions based on identified gaps."""
        questions = []

        with self._lock:
            for gap in self.gaps:
                if gap.importance in ("critical", "high"):
                    questions.append({
                        "gap_id": gap.gap_id,
                        "domain": gap.domain,
                        "question": f"What is the current status of {gap.description}?",
                        "importance": gap.importance
                    })

        return questions

    # =========================================================================
    # DOMAIN OVERLAP DETECTION (Point 75)
    # =========================================================================

    def detect_domain_overlaps(self) -> List[Dict[str, Any]]:
        """
        Identify facts that span multiple domains (Point 75).

        Some facts (e.g., "Azure AD integration") may be relevant to
        both identity_access and infrastructure domains.
        """
        overlaps = []
        domain_keywords = {
            "infrastructure": ["server", "vm", "cloud", "azure", "aws", "storage"],
            "network": ["network", "firewall", "vpn", "lan", "wan", "routing"],
            "cybersecurity": ["security", "encryption", "vulnerability", "threat", "siem"],
            "applications": ["application", "erp", "crm", "saas", "software"],
            "identity_access": ["identity", "active directory", "sso", "mfa", "authentication"],
            "organization": ["staff", "team", "vendor", "contract", "budget"]
        }

        with self._lock:
            for fact in self.facts:
                # Check which domains the fact content matches
                fact_text = f"{fact.item} {fact.category}".lower()
                if fact.evidence:
                    fact_text += f" {fact.evidence.get('exact_quote', '')}".lower()

                matched_domains = []
                for domain, keywords in domain_keywords.items():
                    if any(kw in fact_text for kw in keywords):
                        matched_domains.append(domain)

                # If matches multiple domains (beyond its own)
                if len(matched_domains) > 1 and fact.domain in matched_domains:
                    other_domains = [d for d in matched_domains if d != fact.domain]
                    if other_domains:
                        # Update the fact's related_domains
                        fact.related_domains = other_domains

                        overlaps.append({
                            "fact_id": fact.fact_id,
                            "primary_domain": fact.domain,
                            "related_domains": other_domains,
                            "item": fact.item,
                            "recommendation": f"Consider cross-referencing with {', '.join(other_domains)}"
                        })

        return overlaps

    def get_cross_domain_summary(self) -> Dict[str, Any]:
        """Get summary of cross-domain fact relationships."""
        overlaps = self.detect_domain_overlaps()

        domain_connections = {}
        for overlap in overlaps:
            primary = overlap["primary_domain"]
            for related in overlap["related_domains"]:
                key = tuple(sorted([primary, related]))
                if key not in domain_connections:
                    domain_connections[key] = 0
                domain_connections[key] += 1

        return {
            "total_overlapping_facts": len(overlaps),
            "domain_connections": {
                f"{k[0]} <-> {k[1]}": v
                for k, v in domain_connections.items()
            },
            "overlapping_facts": overlaps
        }

    # =========================================================================
    # OPEN QUESTIONS (Points 82-86 - Enhancement Plan)
    # =========================================================================

    def _generate_question_id(self, domain: str) -> str:
        """
        Generate unique question ID: Q-{DOMAIN_PREFIX}-{SEQ}

        NOTE: Must be called within self._lock context.
        """
        prefix = DOMAIN_PREFIXES.get(domain, "GEN")

        if prefix not in self._question_counters:
            self._question_counters[prefix] = 0

        self._question_counters[prefix] += 1
        return f"Q-{prefix}-{self._question_counters[prefix]:03d}"

    def add_open_question(
        self,
        domain: str,
        category: str,
        question_text: str,
        priority: str,
        source_gap_ids: List[str] = None,
        suggested_recipient: str = "Management",
        context: str = "",
        impact_if_unanswered: str = "",
        deal_id: str = None
    ) -> str:
        """
        Add an open question and return its unique ID.

        Args:
            domain: infrastructure, network, etc.
            category: Category within domain
            question_text: The actual question to ask
            priority: critical, high, medium, low
            source_gap_ids: Gap IDs that led to this question
            suggested_recipient: Who should answer this
            context: Background context
            impact_if_unanswered: Why this matters
            deal_id: Deal ID for scoping (uses store's deal_id if not provided)

        Returns:
            Unique question ID (e.g., Q-INFRA-001)

        Raises:
            ValueError: If deal_id is missing
        """
        # Resolve deal_id
        effective_deal_id = deal_id or self.deal_id
        if not effective_deal_id:
            raise ValueError("deal_id is required - provide in add_open_question() or store constructor")

        with self._lock:
            question_id = self._generate_question_id(domain)

            question = OpenQuestion(
                question_id=question_id,
                question_text=question_text,
                domain=domain,
                category=category,
                priority=priority,
                source_gap_ids=source_gap_ids or [],
                suggested_recipient=suggested_recipient,
                context=context,
                impact_if_unanswered=impact_if_unanswered,
                deal_id=effective_deal_id
            )

            self.open_questions.append(question)
            self._question_index[question_id] = question
            logger.debug(f"Added question {question_id}: {question_text[:50]}...")

        return question_id

    def get_question(self, question_id: str) -> Optional[OpenQuestion]:
        """Get a specific question by ID (O(1) lookup using index)."""
        with self._lock:
            return self._question_index.get(question_id)

    def transform_gaps_to_questions(self, include_low_priority: bool = False) -> List[str]:
        """
        Transform gaps into actionable open questions (Point 83).

        Converts identified information gaps into specific questions
        that can be asked to stakeholders.

        Args:
            include_low_priority: Whether to include low importance gaps

        Returns:
            List of created question IDs
        """
        created_question_ids = []

        with self._lock:
            for gap in self.gaps:
                # Skip low importance gaps unless requested
                if gap.importance == "low" and not include_low_priority:
                    continue

                # Generate question text from gap description
                question_text = self._gap_to_question_text(gap)

                # Determine suggested recipient based on domain
                recipient = self._suggest_recipient_for_domain(gap.domain, gap.category)

                # Determine impact based on importance
                impact = self._determine_gap_impact(gap)

                # Create the question (inherit deal_id from gap or store)
                question_id = self.add_open_question(
                    domain=gap.domain,
                    category=gap.category,
                    question_text=question_text,
                    priority=gap.importance,
                    source_gap_ids=[gap.gap_id],
                    suggested_recipient=recipient,
                    context=f"Gap identified during {gap.domain} discovery",
                    impact_if_unanswered=impact,
                    deal_id=gap.deal_id or self.deal_id
                )

                created_question_ids.append(question_id)

        logger.info(f"Transformed {len(created_question_ids)} gaps into open questions")
        return created_question_ids

    def _gap_to_question_text(self, gap: Gap) -> str:
        """Convert a gap description into a question."""
        description = gap.description.strip()

        # If already ends with question mark, use as-is
        if description.endswith("?"):
            return description

        # Common patterns to convert
        lower_desc = description.lower()

        if lower_desc.startswith("no ") or lower_desc.startswith("missing "):
            # "No information about X" -> "What is the current status of X?"
            subject = description.split(" ", 2)[-1] if len(description.split()) > 2 else description
            return f"Can you provide details about {subject}?"

        if lower_desc.startswith("unclear ") or lower_desc.startswith("unknown "):
            subject = description.split(" ", 1)[-1] if len(description.split()) > 1 else description
            return f"What is the status of {subject}?"

        if "not specified" in lower_desc or "not provided" in lower_desc:
            return f"Can you clarify: {description}?"

        if "lack of" in lower_desc:
            subject = description.replace("lack of", "").strip()
            return f"What is available regarding {subject}?"

        # Default: wrap in a question format
        return f"Can you provide information about: {description}?"

    def _suggest_recipient_for_domain(self, domain: str, category: str) -> str:
        """Suggest appropriate recipient for a question based on domain."""
        recipient_map = {
            "infrastructure": "Target Infrastructure Lead",
            "network": "Target Network Lead",
            "cybersecurity": "Target Security Lead",
            "applications": "Target Applications Lead",
            "identity_access": "Target Security Lead",
            "organization": "Target IT Director"
        }

        # Some categories have specific recipients
        category_overrides = {
            "budget": "Target IT Director",
            "staffing": "Target IT Director",
            "contracts": "Target IT Director",
            "security": "Target Security Lead",
            "compliance": "Target Security Lead"
        }

        # Check category override first
        for key, recipient in category_overrides.items():
            if key in category.lower():
                return recipient

        return recipient_map.get(domain, "Target CIO")

    def _determine_gap_impact(self, gap: Gap) -> str:
        """Determine the impact if a gap remains unanswered."""
        impact_templates = {
            "critical": "Unable to complete critical assessment of {domain} {category}. May affect deal viability assessment.",
            "high": "Assessment of {domain} {category} will be incomplete. Risk analysis may miss significant concerns.",
            "medium": "Partial understanding of {domain} {category}. Some risks may not be fully characterized.",
            "low": "Minor gap in {domain} {category} documentation. Limited impact on overall assessment."
        }

        template = impact_templates.get(gap.importance, impact_templates["medium"])
        return template.format(domain=gap.domain, category=gap.category)

    def prioritize_questions(self) -> List[OpenQuestion]:
        """
        Return questions sorted by priority (Point 84).

        Priority order: critical > high > medium > low
        Within same priority, older questions first.
        """
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        with self._lock:
            sorted_questions = sorted(
                self.open_questions,
                key=lambda q: (priority_order.get(q.priority, 4), q.created_at)
            )
            return sorted_questions

    def categorize_questions(self) -> Dict[str, Any]:
        """
        Categorize questions by domain, recipient, and status (Point 85).

        Returns organized view of all questions.
        """
        with self._lock:
            by_domain: Dict[str, List[Dict]] = {}
            by_recipient: Dict[str, List[Dict]] = {}
            by_status: Dict[str, List[Dict]] = {}
            by_priority: Dict[str, List[Dict]] = {}

            for q in self.open_questions:
                q_dict = q.to_dict()

                # By domain
                if q.domain not in by_domain:
                    by_domain[q.domain] = []
                by_domain[q.domain].append(q_dict)

                # By recipient
                if q.suggested_recipient not in by_recipient:
                    by_recipient[q.suggested_recipient] = []
                by_recipient[q.suggested_recipient].append(q_dict)

                # By status
                if q.status not in by_status:
                    by_status[q.status] = []
                by_status[q.status].append(q_dict)

                # By priority
                if q.priority not in by_priority:
                    by_priority[q.priority] = []
                by_priority[q.priority].append(q_dict)

            return {
                "total_questions": len(self.open_questions),
                "by_domain": {k: len(v) for k, v in by_domain.items()},
                "by_recipient": {k: len(v) for k, v in by_recipient.items()},
                "by_status": {k: len(v) for k, v in by_status.items()},
                "by_priority": {k: len(v) for k, v in by_priority.items()},
                "questions_by_domain": by_domain,
                "questions_by_recipient": by_recipient
            }

    def deduplicate_questions(self, similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Merge similar questions across domains (Point 86).

        Returns summary of merged questions.
        """
        merged_count = 0
        merged_pairs = []

        with self._lock:
            questions_to_remove = set()

            for i, q1 in enumerate(self.open_questions):
                if q1.question_id in questions_to_remove:
                    continue

                for q2 in self.open_questions[i + 1:]:
                    if q2.question_id in questions_to_remove:
                        continue

                    similarity = self._calculate_question_similarity(q1, q2)

                    if similarity >= similarity_threshold:
                        # Merge: keep the higher priority question
                        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                        if priority_order.get(q2.priority, 4) < priority_order.get(q1.priority, 4):
                            keep, remove = q2, q1
                        else:
                            keep, remove = q1, q2

                        # Add source gaps from removed to kept
                        keep.source_gap_ids.extend(remove.source_gap_ids)
                        keep.source_gap_ids = list(set(keep.source_gap_ids))

                        questions_to_remove.add(remove.question_id)
                        merged_pairs.append({
                            "kept": keep.question_id,
                            "removed": remove.question_id,
                            "similarity": similarity
                        })
                        merged_count += 1

            # Remove duplicates
            for qid in questions_to_remove:
                q = self._question_index.get(qid)
                if q:
                    self.open_questions.remove(q)
                    del self._question_index[qid]

        return {
            "questions_merged": merged_count,
            "questions_remaining": len(self.open_questions),
            "merge_details": merged_pairs
        }

    def _calculate_question_similarity(self, q1: OpenQuestion, q2: OpenQuestion) -> float:
        """Calculate similarity between two questions."""
        # Jaccard similarity on words
        words1 = set(q1.question_text.lower().split())
        words2 = set(q2.question_text.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2
        jaccard = len(intersection) / len(union) if union else 0

        # Boost if same domain
        domain_match = 0.2 if q1.domain == q2.domain else 0.0

        # Boost if same category
        category_match = 0.1 if q1.category == q2.category else 0.0

        return min(1.0, jaccard * 0.7 + domain_match + category_match)

    def get_unanswered_questions(self, domain: str = None) -> List[OpenQuestion]:
        """Get all unanswered questions, optionally filtered by domain."""
        with self._lock:
            questions = [q for q in self.open_questions if q.status == "open"]
            if domain:
                questions = [q for q in questions if q.domain == domain]
            return questions

    def get_question_summary(self) -> Dict[str, Any]:
        """Get summary of open questions status."""
        with self._lock:
            total = len(self.open_questions)
            open_count = sum(1 for q in self.open_questions if q.status == "open")
            answered = sum(1 for q in self.open_questions if q.status == "answered")
            deferred = sum(1 for q in self.open_questions if q.status == "deferred")
            na = sum(1 for q in self.open_questions if q.status == "not_applicable")

            # Critical questions still open
            critical_open = sum(
                1 for q in self.open_questions
                if q.status == "open" and q.priority == "critical"
            )

            return {
                "total_questions": total,
                "open": open_count,
                "answered": answered,
                "deferred": deferred,
                "not_applicable": na,
                "completion_rate": (answered + na) / total if total > 0 else 0.0,
                "critical_open": critical_open
            }

    def answer_question(self, question_id: str, answer: str, answered_by: str) -> bool:
        """Mark a question as answered."""
        with self._lock:
            question = self._question_index.get(question_id)
            if not question:
                return False

            question.mark_answered(answer, answered_by)
            logger.info(f"Question {question_id} answered by {answered_by}")
            return True

    def export_questions_for_followup(self, format: str = "list") -> Any:
        """
        Export questions in a format suitable for sending to stakeholders.

        Args:
            format: "list" for simple list, "by_recipient" for grouped by recipient

        Returns:
            Formatted questions for export
        """
        with self._lock:
            if format == "by_recipient":
                result = {}
                for q in self.open_questions:
                    if q.status != "open":
                        continue
                    recipient = q.suggested_recipient
                    if recipient not in result:
                        result[recipient] = []
                    result[recipient].append({
                        "id": q.question_id,
                        "question": q.question_text,
                        "priority": q.priority,
                        "domain": q.domain,
                        "context": q.context,
                        "impact": q.impact_if_unanswered
                    })
                return result
            else:
                return [
                    {
                        "id": q.question_id,
                        "question": q.question_text,
                        "priority": q.priority,
                        "domain": q.domain,
                        "recipient": q.suggested_recipient,
                        "context": q.context
                    }
                    for q in self.open_questions if q.status == "open"
                ]
