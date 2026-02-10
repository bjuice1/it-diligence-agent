"""
Inventory Dossier Builder

Creates comprehensive "dossiers" for each inventory item that combine:
- Facts (what we know)
- Evidence (source quotes)
- Risks (what's concerning)
- Work Items (what needs to happen)
- Narratives (what we wrote)
- AI Assessment (synthesized view)

This gives practitioners a single pane of glass for each item,
allowing them to "dig as deep as they want."
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


# =============================================================================
# DOSSIER DATA MODEL
# =============================================================================

@dataclass
class SourceEvidence:
    """Evidence from source documents (Phase 3 - Enhanced Traceability)."""
    quote: str
    source_document: str
    source_section: str = ""
    source_page: str = ""           # Page number if available
    source_line: str = ""           # Line number if available
    source_anchor: str = ""         # heading_path, table_name, or chunk_id for non-page docs
    fact_id: str = ""
    is_exact_quote: bool = True     # vs paraphrase

    def format_citation(self) -> str:
        """Format as auditable citation."""
        parts = [self.source_document] if self.source_document else ["Unknown source"]
        if self.source_section:
            parts.append(f"§{self.source_section}")
        if self.source_page:
            parts.append(f"p.{self.source_page}")
        if self.source_anchor and not self.source_page:
            # Use anchor when page not available
            parts.append(f"@{self.source_anchor}")
        if self.source_line:
            parts.append(f"L{self.source_line}")
        return " | ".join(parts)

    def quality_score(self) -> int:
        """
        Evidence quality score for status calculation (0-3).

        Scoring:
        - +1: Has citation metadata (section, page, or anchor)
        - +1: Is exact quote (not paraphrase)
        - +1: Quote contains a number (backs a key field like cost, count)
        """
        score = 0
        # Has citation metadata
        if self.source_section or self.source_page or self.source_anchor:
            score += 1
        # Is exact quote (not paraphrase)
        if self.is_exact_quote:
            score += 1
        # Quote contains a number (backs a key field)
        if self.quote and any(c.isdigit() for c in self.quote):
            score += 1
        return score


@dataclass
class RelatedRisk:
    """A risk related to this inventory item."""
    risk_id: str
    title: str
    description: str
    severity: str
    category: str = ""
    cost_estimate_low: Optional[int] = None
    cost_estimate_high: Optional[int] = None
    mitigation: str = ""
    based_on_facts: List[str] = field(default_factory=list)


@dataclass
class RelatedWorkItem:
    """A work item related to this inventory item."""
    work_item_id: str
    title: str
    description: str
    phase: str  # "day_1", "day_100", etc.
    effort: str = ""
    owner: str = ""
    based_on_facts: List[str] = field(default_factory=list)


@dataclass
class ItemDossier:
    """
    Comprehensive dossier for a single inventory item.

    Contains everything we know about one app, server, control, etc.
    """
    # Identity
    name: str
    domain: str
    category: str = ""
    entity: str = "target"
    entity_was_inferred: bool = False  # True if entity was defaulted (not from source data)
    item_type: str = ""  # "application", "server", "control", etc.

    # Core attributes (domain-specific)
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Facts - what we extracted
    fact_ids: List[str] = field(default_factory=list)
    fact_count: int = 0

    # Evidence - source quotes
    evidence: List[SourceEvidence] = field(default_factory=list)
    source_documents: List[str] = field(default_factory=list)

    # Risks - what's concerning
    risks: List[RelatedRisk] = field(default_factory=list)
    risk_count: int = 0
    highest_risk_severity: str = "none"

    # Work Items - what needs to happen
    work_items: List[RelatedWorkItem] = field(default_factory=list)
    work_item_count: int = 0
    day_1_items: int = 0
    day_100_items: int = 0

    # Narrative - what we wrote in reports
    narrative_excerpts: List[str] = field(default_factory=list)

    # AI Assessment - synthesized view
    summary: str = ""
    key_considerations: List[str] = field(default_factory=list)
    overall_status: str = "green"  # green, yellow, red
    recommendation: str = ""

    # Data completeness tracking (Phase 1 - Entity Separation)
    data_gaps: List[str] = field(default_factory=list)  # Missing critical fields
    data_completeness: float = 1.0  # 0.0 to 1.0
    canonical_key: str = ""  # For delta matching (entity:domain:item:vendor:instance)

    # Conflict tracking (Phase 6)
    attribute_conflicts: Dict[str, List[Any]] = field(default_factory=dict)
    has_conflicts: bool = False
    conflict_count: int = 0

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert nested dataclasses
        result['evidence'] = [asdict(e) if hasattr(e, '__dataclass_fields__') else e for e in self.evidence]
        result['risks'] = [asdict(r) if hasattr(r, '__dataclass_fields__') else r for r in self.risks]
        result['work_items'] = [asdict(w) if hasattr(w, '__dataclass_fields__') else w for w in self.work_items]
        return result


# =============================================================================
# DOSSIER BUILDER
# =============================================================================

class DossierBuilder:
    """
    Builds comprehensive dossiers by linking facts, findings, and narratives.

    The key insight: Findings cite fact_ids. Items come from facts.
    We can trace the citation chain to connect everything.
    """

    def __init__(
        self,
        facts: List[Dict],
        findings: Dict[str, Any],
        narratives: Dict[str, str] = None
    ):
        """
        Initialize with analysis data.

        Args:
            facts: List of fact dictionaries
            findings: Findings dict with risks, work_items, recommendations
            narratives: Optional dict of domain -> narrative text
        """
        self.facts = facts
        self.findings = findings
        self.narratives = narratives or {}

        # Data quality tracking (Phase 1 - Entity Separation)
        self.unknown_entity_count = 0  # Facts missing entity field

        # Build indexes for efficient lookup
        self._index_facts()
        self._index_findings()

        # Log data quality warning if needed
        if self.unknown_entity_count > 0:
            logger.warning(f"{self.unknown_entity_count} facts missing entity field - data quality defect")

    def _index_facts(self):
        """Index facts by ID and by item name (entity-aware)."""
        self.facts_by_id: Dict[str, Dict] = {}
        self.facts_by_domain: Dict[str, List[Dict]] = {}
        self.facts_by_item: Dict[str, List[Dict]] = {}  # entity:domain:item -> facts
        self.facts_by_canonical_key: Dict[str, List[Dict]] = {}  # canonical_key -> facts
        self.items_with_inferred_entity: Set[str] = set()  # Track which items had entity inferred

        for fact in self.facts:
            fact_id = fact.get('fact_id', '')
            domain = self._normalize_domain(fact.get('domain', 'general'))
            item = fact.get('item', '').strip()

            # Track entity - flag when we have to infer it
            entity = fact.get('entity')
            entity_was_inferred = False
            if entity is None:
                entity = 'target'
                entity_was_inferred = True
                self.unknown_entity_count += 1  # Track the defect

            if fact_id:
                self.facts_by_id[fact_id] = fact

            if domain not in self.facts_by_domain:
                self.facts_by_domain[domain] = []
            self.facts_by_domain[domain].append(fact)

            if item:
                # FIXED: Include entity in key to prevent Target/Buyer mixing
                item_key = f"{entity}:{domain}:{item.lower()}"
                if item_key not in self.facts_by_item:
                    self.facts_by_item[item_key] = []
                self.facts_by_item[item_key].append(fact)

                # Track items that had entity inferred (Phase 9 fix)
                if entity_was_inferred:
                    self.items_with_inferred_entity.add(item_key)

                # Also index by canonical key for robust matching
                canonical_key = self._generate_canonical_key(fact)
                if canonical_key not in self.facts_by_canonical_key:
                    self.facts_by_canonical_key[canonical_key] = []
                self.facts_by_canonical_key[canonical_key].append(fact)

    def _index_findings(self):
        """Index findings and build fact_id -> finding mappings."""
        self.risks: List[Dict] = []
        self.work_items: List[Dict] = []
        self.recommendations: List[Dict] = []

        # Mapping: fact_id -> list of findings that cite it
        self.findings_by_fact_id: Dict[str, List[Dict]] = {}

        # Extract findings from various structures
        if isinstance(self.findings, dict):
            self.risks = self.findings.get('risks', [])
            self.work_items = self.findings.get('work_items', [])
            self.recommendations = self.findings.get('recommendations', [])

        # Build fact_id -> findings index
        all_findings = self.risks + self.work_items + self.recommendations
        for finding in all_findings:
            # Findings may have based_on_facts or based_on field
            fact_refs = finding.get('based_on_facts', []) or finding.get('based_on', [])
            if isinstance(fact_refs, str):
                fact_refs = [fact_refs]

            for fact_id in fact_refs:
                if fact_id not in self.findings_by_fact_id:
                    self.findings_by_fact_id[fact_id] = []
                self.findings_by_fact_id[fact_id].append(finding)

    # =========================================================================
    # ENTITY & DOMAIN NORMALIZATION (Phase 1 - Entity Separation)
    # =========================================================================

    # Domain name normalization mapping
    DOMAIN_ALIASES = {
        'identity & access': 'identity_access',
        'identity and access': 'identity_access',
        'iam': 'identity_access',
        'security': 'cybersecurity',
        'cyber': 'cybersecurity',
        'infra': 'infrastructure',
        'apps': 'applications',
        'network & connectivity': 'network',
        'org': 'organization',
        'people': 'organization',
    }

    # Critical fields by domain - missing these should be flagged as data gaps (Phase 4)
    CRITICAL_FIELDS = {
        'applications': ['user_count', 'vendor', 'version', 'criticality', 'annual_cost'],
        'infrastructure': ['location', 'capacity', 'age', 'annual_cost', 'vendor'],
        'cybersecurity': ['coverage', 'deployment_scope', 'last_assessment', 'vendor'],
        'identity_access': ['user_count', 'mfa_coverage', 'sso_enabled', 'vendor'],
        'network': ['bandwidth', 'redundancy', 'vendor', 'annual_cost'],
        'organization': ['headcount', 'reporting_to', 'tenure', 'location'],
    }

    # Values that indicate "not stated" - should be treated as gaps
    NOT_STATED_VALUES = {'not_stated', 'not_specified', 'unknown', 'n/a', 'none', '', 'tbd', 'to be determined'}

    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain name to canonical form."""
        if not domain:
            return 'general'
        normalized = domain.lower().strip()
        return self.DOMAIN_ALIASES.get(normalized, normalized)

    def _calculate_data_gaps(self, dossier: ItemDossier) -> None:
        """
        Calculate data gaps based on missing critical fields (Phase 4).

        Modifies dossier in place to set:
        - data_gaps: List of missing critical field names
        - data_completeness: Float 0.0 to 1.0
        """
        normalized_domain = self._normalize_domain(dossier.domain)
        domain_critical = self.CRITICAL_FIELDS.get(normalized_domain, [])

        if not domain_critical:
            dossier.data_completeness = 1.0
            return

        missing_critical = []
        for field in domain_critical:
            value = dossier.attributes.get(field)
            # Check if value is missing or is a "not stated" value
            if not value or str(value).lower().strip() in self.NOT_STATED_VALUES:
                missing_critical.append(field)

        dossier.data_gaps = missing_critical
        dossier.data_completeness = 1.0 - (len(missing_critical) / len(domain_critical))

    def _generate_canonical_key(self, fact: Dict) -> str:
        """
        Generate stable item identity beyond just name.

        Handles: "ADP Workforce Now" vs "ADP" vs "ADP (Payroll Instance)"
        Key format: entity:domain:item[:vendor][:instance]
        """
        entity = fact.get('entity', 'target')
        domain = self._normalize_domain(fact.get('domain', 'general'))
        item = fact.get('item', '').strip().lower()

        # Extract vendor if available
        details = fact.get('details', {})
        vendor = details.get('vendor', '').strip().lower() if details else ''

        # Extract instance/environment if available
        instance = ''
        if details:
            instance = details.get('instance', details.get('environment', '')).strip().lower()

        # Build canonical key
        parts = [entity, domain, item]
        if vendor and vendor not in item:
            parts.append(vendor)
        if instance:
            parts.append(instance)

        return ":".join(parts)

    # =========================================================================
    # FINDING LOOKUP METHODS
    # =========================================================================

    def _find_related_findings(self, fact_ids: List[str], item_name: str) -> tuple:
        """
        Find all findings related to a set of fact_ids or item name.

        Returns (risks, work_items) tuples.
        """
        related_risks = []
        related_work_items = []
        seen_ids = set()

        # Method 1: Direct fact_id citation
        for fact_id in fact_ids:
            for finding in self.findings_by_fact_id.get(fact_id, []):
                finding_id = finding.get('finding_id', finding.get('id', ''))
                if finding_id and finding_id not in seen_ids:
                    seen_ids.add(finding_id)
                    if finding in self.risks:
                        related_risks.append(finding)
                    elif finding in self.work_items:
                        related_work_items.append(finding)

        # Method 2: Name matching in title/description (fallback)
        item_lower = item_name.lower()
        for risk in self.risks:
            finding_id = risk.get('finding_id', risk.get('id', ''))
            if finding_id in seen_ids:
                continue
            title = risk.get('title', '').lower()
            desc = risk.get('description', '').lower()
            if item_lower in title or item_lower in desc:
                seen_ids.add(finding_id)
                related_risks.append(risk)

        for wi in self.work_items:
            finding_id = wi.get('finding_id', wi.get('id', ''))
            if finding_id in seen_ids:
                continue
            title = wi.get('title', '').lower()
            desc = wi.get('description', '').lower()
            if item_lower in title or item_lower in desc:
                seen_ids.add(finding_id)
                related_work_items.append(wi)

        return related_risks, related_work_items

    def _extract_narrative_mentions(self, item_name: str, domain: str) -> List[str]:
        """Extract narrative excerpts that mention this item."""
        excerpts = []
        narrative = self.narratives.get(domain, '')

        if not narrative or not item_name:
            return excerpts

        # Split into sentences and find mentions
        item_lower = item_name.lower()
        sentences = narrative.replace('\n', ' ').split('.')

        for sentence in sentences:
            if item_lower in sentence.lower() and len(sentence.strip()) > 20:
                excerpts.append(sentence.strip() + '.')

        return excerpts[:3]  # Limit to 3 excerpts

    def _calculate_status(self, risks: List[Dict], dossier: ItemDossier = None) -> str:
        """
        Calculate status based on risks AND evidence quality (Phase 5).

        Status criteria:
        - RED: Critical/high risks OR <25% data completeness OR unknown entity
        - YELLOW: Medium risks OR <50% data completeness OR evidence quality < 3
        - GREEN: No significant risks AND >75% completeness AND evidence quality >= 3

        Args:
            risks: List of risk dictionaries
            dossier: Optional ItemDossier for quality-based assessment
        """
        # Check risk severity
        severities = [r.get('severity', 'medium').lower() for r in risks]
        has_critical = 'critical' in severities
        has_high = 'high' in severities
        has_medium = 'medium' in severities

        if dossier:
            completeness = getattr(dossier, 'data_completeness', 1.0)

            # Calculate total evidence quality score
            evidence_quality = sum(
                ev.quality_score() if hasattr(ev, 'quality_score') else 1
                for ev in dossier.evidence
            )

            # Unknown entity is a RED flag
            if dossier.entity not in ['target', 'buyer']:
                return "red"

            # RED conditions
            if has_critical or has_high:
                return "red"
            if completeness < 0.25:
                return "red"

            # YELLOW conditions
            if has_medium:
                return "yellow"
            if completeness < 0.50:
                return "yellow"
            if evidence_quality < 3:  # Quality threshold, not just count
                return "yellow"
            if getattr(dossier, 'has_conflicts', False):  # Conflicts require review
                return "yellow"

            # GREEN requires actual quality evidence
            if completeness >= 0.75 and evidence_quality >= 3:
                return "green"

            return "yellow"  # Default to yellow if uncertain

        # Fallback: risk-only logic (no dossier provided)
        if has_critical or has_high:
            return "red"
        elif has_medium:
            return "yellow"
        return "yellow"  # Default to yellow, not green

    def _get_highest_severity(self, risks: List[Dict]) -> str:
        """Get highest severity from risks."""
        severity_order = ['critical', 'high', 'medium', 'low', 'info']

        for severity in severity_order:
            for risk in risks:
                if risk.get('severity', '').lower() == severity:
                    return severity

        return "none"

    def _generate_summary(self, dossier: ItemDossier) -> str:
        """Generate a summary for the dossier based on available data."""
        parts = []

        # Base description from attributes
        if dossier.attributes.get('description'):
            parts.append(dossier.attributes['description'])

        # Risk summary
        if dossier.risk_count > 0:
            severity = dossier.highest_risk_severity
            parts.append(f"{dossier.risk_count} risk(s) identified ({severity} severity).")

        # Work item summary
        if dossier.work_item_count > 0:
            if dossier.day_1_items > 0:
                parts.append(f"{dossier.day_1_items} Day 1 action(s) required.")
            if dossier.day_100_items > 0:
                parts.append(f"{dossier.day_100_items} Day 100 item(s).")

        # No issues
        if dossier.risk_count == 0 and dossier.work_item_count == 0:
            parts.append("No significant concerns identified.")

        return " ".join(parts)

    def _generate_considerations(self, dossier: ItemDossier) -> List[str]:
        """Generate key considerations from the dossier data."""
        considerations = []

        # From risks
        for risk in dossier.risks[:3]:
            title = risk.title if hasattr(risk, 'title') else risk.get('title', '')
            if title:
                considerations.append(f"Risk: {title}")

        # From work items
        for wi in dossier.work_items[:2]:
            title = wi.title if hasattr(wi, 'title') else wi.get('title', '')
            phase = wi.phase if hasattr(wi, 'phase') else wi.get('phase', '')
            if title:
                considerations.append(f"Action ({phase}): {title}")

        # From attributes
        attrs = dossier.attributes
        if attrs.get('criticality') and 'critical' in str(attrs.get('criticality', '')).lower():
            considerations.append("Business critical system")
        if attrs.get('age_assessment') and 'legacy' in str(attrs.get('age_assessment', '')).lower():
            considerations.append("Legacy system - modernization consideration")

        return considerations[:5]  # Limit to 5

    def _generate_recommendation(self, dossier: ItemDossier) -> str:
        """Generate recommendation based on status and findings."""
        if dossier.overall_status == "red":
            if dossier.highest_risk_severity == "critical":
                return "Immediate attention required - critical issues identified"
            return "High priority - address identified risks before or during integration"
        elif dossier.overall_status == "yellow":
            return "Monitor and plan - moderate concerns to address in first 100 days"
        else:
            return "No immediate action required - continue standard operations"

    def build_dossier(self, item_name: str, domain: str, entity: str = "target") -> Optional[ItemDossier]:
        """
        Build a complete dossier for a single item.

        Args:
            item_name: Name of the item (app name, server name, etc.)
            domain: Domain (applications, infrastructure, etc.)
            entity: Entity to filter by ("target" or "buyer")

        Returns:
            ItemDossier or None if no data found
        """
        # Normalize domain name
        normalized_domain = self._normalize_domain(domain)

        # FIXED: Use entity-aware key (Phase 1)
        item_key = f"{entity}:{normalized_domain}:{item_name.lower()}"
        item_facts = self.facts_by_item.get(item_key, [])

        if not item_facts:
            # Try fuzzy match within same entity
            for key, facts in self.facts_by_item.items():
                if key.startswith(f"{entity}:{normalized_domain}:") and item_name.lower() in key:
                    item_facts = facts
                    break

        if not item_facts:
            return None

        # Generate canonical key for this dossier
        canonical_key = self._generate_canonical_key(item_facts[0]) if item_facts else ""

        # Check if this item had entity inferred during indexing (Phase 9 fix)
        entity_was_inferred = item_key in self.items_with_inferred_entity

        # Initialize dossier
        dossier = ItemDossier(
            name=item_name,
            domain=normalized_domain,
            entity=entity,
            item_type=self._get_item_type(normalized_domain),
            canonical_key=canonical_key,
            entity_was_inferred=entity_was_inferred
        )

        # Collect fact IDs and evidence
        for fact in item_facts:
            fact_id = fact.get('fact_id', '')
            if fact_id:
                dossier.fact_ids.append(fact_id)

            # Extract evidence with enhanced traceability (Phase 3)
            evidence = fact.get('evidence', {})
            if isinstance(evidence, dict) and evidence.get('exact_quote'):
                # Try multiple fields for anchor (heading_path, table_name, chunk_id)
                source_anchor = evidence.get('heading_path',
                                evidence.get('table_name',
                                evidence.get('chunk_id', '')))
                dossier.evidence.append(SourceEvidence(
                    quote=evidence['exact_quote'],
                    source_document=fact.get('source_document', ''),
                    source_section=evidence.get('source_section', ''),
                    source_page=str(evidence.get('page_number', evidence.get('page', ''))) if evidence.get('page_number') or evidence.get('page') else '',
                    source_line=str(evidence.get('line_number', '')) if evidence.get('line_number') else '',
                    source_anchor=source_anchor,
                    fact_id=fact_id,
                    is_exact_quote=True  # Our extraction always uses exact quotes
                ))

            # Track source documents
            source_doc = fact.get('source_document', '')
            if source_doc and source_doc not in dossier.source_documents:
                dossier.source_documents.append(source_doc)

            # Extract category
            if fact.get('category') and not dossier.category:
                dossier.category = fact['category']

            # Extract attributes from details WITH conflict detection (Phase 6)
            details = fact.get('details', {})
            for key, value in details.items():
                # Skip empty/not_stated values
                if not value or str(value).lower().strip() in self.NOT_STATED_VALUES:
                    continue

                if key in dossier.attributes:
                    existing = dossier.attributes[key]
                    # Normalize for comparison
                    existing_norm = str(existing).lower().strip()
                    value_norm = str(value).lower().strip()

                    if existing_norm != value_norm:
                        # Conflict detected!
                        if key not in dossier.attribute_conflicts:
                            dossier.attribute_conflicts[key] = [existing]
                        if value not in dossier.attribute_conflicts[key]:
                            dossier.attribute_conflicts[key].append(value)
                        dossier.has_conflicts = True
                        dossier.conflict_count += 1
                else:
                    dossier.attributes[key] = value

        dossier.fact_count = len(dossier.fact_ids)

        # Find related findings
        related_risks, related_work_items = self._find_related_findings(
            dossier.fact_ids, item_name
        )

        # Convert to RelatedRisk objects
        for risk in related_risks:
            dossier.risks.append(RelatedRisk(
                risk_id=risk.get('finding_id', risk.get('id', '')),
                title=risk.get('title', ''),
                description=risk.get('description', ''),
                severity=risk.get('severity', 'medium'),
                category=risk.get('category', ''),
                cost_estimate_low=risk.get('cost_estimate_low'),
                cost_estimate_high=risk.get('cost_estimate_high'),
                mitigation=risk.get('mitigation', ''),
                based_on_facts=risk.get('based_on_facts', [])
            ))

        # Convert to RelatedWorkItem objects
        for wi in related_work_items:
            phase = wi.get('phase', wi.get('timing', 'day_100'))
            dossier.work_items.append(RelatedWorkItem(
                work_item_id=wi.get('finding_id', wi.get('id', '')),
                title=wi.get('title', ''),
                description=wi.get('description', ''),
                phase=phase,
                effort=wi.get('effort', ''),
                owner=wi.get('owner', ''),
                based_on_facts=wi.get('based_on_facts', [])
            ))

            # Count by phase
            if 'day_1' in str(phase).lower() or 'day 1' in str(phase).lower():
                dossier.day_1_items += 1
            else:
                dossier.day_100_items += 1

        dossier.risk_count = len(dossier.risks)
        dossier.work_item_count = len(dossier.work_items)
        dossier.highest_risk_severity = self._get_highest_severity(related_risks)

        # Extract narrative mentions
        dossier.narrative_excerpts = self._extract_narrative_mentions(item_name, domain)

        # Calculate data gaps (Phase 4)
        self._calculate_data_gaps(dossier)

        # Calculate overall status (now uses data_completeness)
        dossier.overall_status = self._calculate_status(related_risks, dossier)

        # Generate AI assessment fields
        dossier.summary = self._generate_summary(dossier)
        dossier.key_considerations = self._generate_considerations(dossier)
        dossier.recommendation = self._generate_recommendation(dossier)

        return dossier

    def _get_item_type(self, domain: str) -> str:
        """Get item type label for domain."""
        type_map = {
            'applications': 'Application',
            'infrastructure': 'Infrastructure Asset',
            'network': 'Network Component',
            'cybersecurity': 'Security Control',
            'identity_access': 'Identity Control',
            'organization': 'Staff/Role',
        }
        return type_map.get(domain, 'Item')

    def build_domain_dossiers(self, domain: str, entity: str = None) -> List[ItemDossier]:
        """
        Build dossiers for all items in a domain.

        Args:
            domain: Domain to process
            entity: If specified, filter to that entity only.
                    If None, build for ALL entities separately (no mixing).

        Returns:
            List of ItemDossier objects (never mixed across entities)
        """
        dossiers = []

        # Normalize domain name
        normalized_domain = self._normalize_domain(domain)
        domain_facts = self.facts_by_domain.get(normalized_domain, [])

        # If no domain_facts found with normalized name, try original
        if not domain_facts:
            domain_facts = self.facts_by_domain.get(domain, [])

        # Filter by entity if specified
        if entity:
            domain_facts = [f for f in domain_facts if f.get('entity', 'target') == entity]

        # Get unique items by entity + item name (Phase 1 fix)
        # This ensures same-name items from different entities stay separate
        # Key format: entity:item_name (simple grouping key)
        items_by_entity_name: Dict[str, str] = {}  # "entity:item_lower" -> item_name (original case)
        for fact in domain_facts:
            fact_entity = fact.get('entity', 'target')
            item_name = fact.get('item', '').strip()
            if item_name:
                grouping_key = f"{fact_entity}:{item_name.lower()}"
                # Keep first occurrence's item name (preserve case)
                if grouping_key not in items_by_entity_name:
                    items_by_entity_name[grouping_key] = item_name

        # Build dossier for each unique entity:item
        for grouping_key, item_name in sorted(items_by_entity_name.items()):
            item_entity = grouping_key.split(':')[0]
            dossier = self.build_dossier(item_name, normalized_domain, entity=item_entity)
            if dossier:
                dossiers.append(dossier)

        # Sort by entity first, then status (red first), then name
        status_order = {'red': 0, 'yellow': 1, 'green': 2}
        entity_order = {'target': 0, 'buyer': 1}
        dossiers.sort(key=lambda d: (
            entity_order.get(d.entity, 2),
            status_order.get(d.overall_status, 3),
            d.name
        ))

        return dossiers

    def build_all_dossiers(self, entity: str = None) -> Dict[str, List[ItemDossier]]:
        """
        Build dossiers for all domains.

        Args:
            entity: If specified, filter to that entity only.
                    If None, build for ALL entities separately.

        Returns:
            Dict mapping domain -> list of dossiers
        """
        all_dossiers = {}

        # Normalize domain names and deduplicate
        seen_domains = set()
        for domain in self.facts_by_domain.keys():
            normalized = self._normalize_domain(domain)
            if normalized in seen_domains:
                continue
            seen_domains.add(normalized)

            dossiers = self.build_domain_dossiers(normalized, entity=entity)
            if dossiers:
                all_dossiers[normalized] = dossiers
                target_count = len([d for d in dossiers if d.entity == 'target'])
                buyer_count = len([d for d in dossiers if d.entity == 'buyer'])
                logger.info(f"Built {len(dossiers)} dossiers for {normalized} "
                           f"(target: {target_count}, buyer: {buyer_count})")

        return all_dossiers

    def get_data_quality_summary(self) -> Dict[str, Any]:
        """
        Get summary of data quality issues found during indexing.

        Returns:
            Dict with quality metrics
        """
        return {
            'unknown_entity_count': self.unknown_entity_count,
            'total_facts': len(self.facts),
            'has_quality_issues': self.unknown_entity_count > 0,
            'quality_score': 1.0 - (self.unknown_entity_count / max(len(self.facts), 1))
        }


# =============================================================================
# EXPORT GATE (Phase 9 - Team-Ready Check)
# =============================================================================

@dataclass
class ExportReadiness:
    """Result of team-ready gate check."""
    is_ready: bool
    blocking_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    unknown_entity_count: int = 0
    unresolved_conflicts: int = 0
    low_completeness_domains: List[str] = field(default_factory=list)
    average_completeness: float = 1.0


class ExportGate:
    """
    Team-ready export gate (Phase 9).

    Blocks exports that have critical data quality issues:
    - Unknown entity facts
    - High number of unresolved conflicts
    - Very low data completeness

    Warns on issues that should be reviewed but don't block:
    - Some conflicts
    - Low completeness in specific domains
    """

    # Thresholds for blocking
    UNKNOWN_ENTITY_BLOCK_THRESHOLD = 0  # Any unknown entities block
    CONFLICT_BLOCK_THRESHOLD = 10        # More than 10 conflicts block
    COMPLETENESS_BLOCK_THRESHOLD = 0.25  # Less than 25% avg completeness blocks

    # Thresholds for warnings
    CONFLICT_WARN_THRESHOLD = 1
    COMPLETENESS_WARN_THRESHOLD = 0.50

    def check_readiness(self, dossiers: Dict[str, List[ItemDossier]]) -> ExportReadiness:
        """
        Check if dossiers are ready for team distribution.

        Args:
            dossiers: Dict mapping domain -> list of ItemDossier

        Returns:
            ExportReadiness with blocking issues and warnings
        """
        blocking = []
        warnings = []
        unknown_count = 0
        conflict_count = 0
        low_completeness = []
        all_completeness = []

        for domain, domain_dossiers in dossiers.items():
            domain_completeness = []

            for d in domain_dossiers:
                # Check for inferred entities (Phase 9 fix)
                # These are items where source data didn't specify target/buyer
                if d.entity_was_inferred:
                    unknown_count += 1

                # Check for unresolved conflicts
                if d.has_conflicts:
                    conflict_count += d.conflict_count

                # Track completeness
                domain_completeness.append(d.data_completeness)
                all_completeness.append(d.data_completeness)

            # Check domain-level completeness
            if domain_completeness:
                avg_completeness = sum(domain_completeness) / len(domain_completeness)
                if avg_completeness < self.COMPLETENESS_WARN_THRESHOLD:
                    low_completeness.append(f"{domain}: {avg_completeness:.0%}")

        # Calculate overall average
        overall_avg = sum(all_completeness) / len(all_completeness) if all_completeness else 1.0

        # Determine blocking issues
        if unknown_count > self.UNKNOWN_ENTITY_BLOCK_THRESHOLD:
            blocking.append(f"{unknown_count} facts with unknown entity - CANNOT EXPORT (fix entity assignment)")

        if conflict_count > self.CONFLICT_BLOCK_THRESHOLD:
            blocking.append(f"{conflict_count} unresolved attribute conflicts - REVIEW REQUIRED before distribution")

        if overall_avg < self.COMPLETENESS_BLOCK_THRESHOLD:
            blocking.append(f"Average data completeness is {overall_avg:.0%} - TOO LOW for distribution")

        # Determine warnings (non-blocking)
        if conflict_count > self.CONFLICT_WARN_THRESHOLD and conflict_count <= self.CONFLICT_BLOCK_THRESHOLD:
            warnings.append(f"{conflict_count} attribute conflicts should be reviewed")

        if low_completeness:
            warnings.append(f"Low completeness domains: {', '.join(low_completeness)}")

        return ExportReadiness(
            is_ready=len(blocking) == 0,
            blocking_issues=blocking,
            warnings=warnings,
            unknown_entity_count=unknown_count,
            unresolved_conflicts=conflict_count,
            low_completeness_domains=low_completeness,
            average_completeness=overall_avg
        )

    def render_readiness_banner(self, readiness: ExportReadiness) -> str:
        """
        Render HTML banner showing export readiness status.

        Args:
            readiness: ExportReadiness result

        Returns:
            HTML string for banner
        """
        if readiness.blocking_issues:
            issues_html = ''.join(f'<li>{issue}</li>' for issue in readiness.blocking_issues)
            return f'''
            <div style="background: #f8d7da; color: #721c24; padding: 15px 20px; border-radius: 8px;
                        border-left: 5px solid #dc3545; margin-bottom: 20px;">
                <h3 style="margin: 0 0 10px 0;">🚫 NOT READY FOR TEAM DISTRIBUTION</h3>
                <ul style="margin: 0; padding-left: 20px;">{issues_html}</ul>
            </div>'''

        elif readiness.warnings:
            warnings_html = ''.join(f'<li>{w}</li>' for w in readiness.warnings)
            return f'''
            <div style="background: #fff3cd; color: #856404; padding: 15px 20px; border-radius: 8px;
                        border-left: 5px solid #ffc107; margin-bottom: 20px;">
                <h3 style="margin: 0 0 10px 0;">⚠️ REVIEW RECOMMENDED</h3>
                <ul style="margin: 0; padding-left: 20px;">{warnings_html}</ul>
                <p style="margin: 10px 0 0 0; font-size: 0.9em;">Export is allowed but review these items before sharing.</p>
            </div>'''

        else:
            return f'''
            <div style="background: #d4edda; color: #155724; padding: 15px 20px; border-radius: 8px;
                        border-left: 5px solid #28a745; margin-bottom: 20px;">
                <h3 style="margin: 0;">✅ TEAM READY</h3>
                <p style="margin: 5px 0 0 0;">Data completeness: {readiness.average_completeness:.0%} | No blocking issues found.</p>
            </div>'''


# =============================================================================
# DOSSIER EXPORTERS
# =============================================================================

class DossierMarkdownExporter:
    """Export dossiers to comprehensive Markdown format."""

    @staticmethod
    def export_domain(dossiers: List[ItemDossier], domain: str, output_path: Path) -> Path:
        """Export domain dossiers to Markdown."""
        lines = [
            f"# {domain.replace('_', ' ').title()} Inventory - Full Dossiers",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "",
            f"**Total Items: {len(dossiers)}**",
            "",
        ]

        # Summary counts
        red_count = len([d for d in dossiers if d.overall_status == 'red'])
        yellow_count = len([d for d in dossiers if d.overall_status == 'yellow'])
        green_count = len([d for d in dossiers if d.overall_status == 'green'])

        lines.extend([
            "## Summary",
            "",
            f"| Status | Count |",
            f"|--------|-------|",
            f"| 🔴 Critical/High Risk | {red_count} |",
            f"| 🟡 Moderate Concerns | {yellow_count} |",
            f"| 🟢 No Issues | {green_count} |",
            "",
            "---",
            "",
        ])

        # Quick reference table
        lines.extend([
            "## Quick Reference",
            "",
            "| Item | Status | Risks | Work Items | Recommendation |",
            "|------|--------|-------|------------|----------------|",
        ])

        status_emoji = {'red': '🔴', 'yellow': '🟡', 'green': '🟢'}
        for dossier in dossiers:
            emoji = status_emoji.get(dossier.overall_status, '⚪')
            rec_short = dossier.recommendation[:50] + "..." if len(dossier.recommendation) > 50 else dossier.recommendation
            lines.append(
                f"| [{dossier.name}](#{dossier.name.lower().replace(' ', '-')}) | {emoji} | {dossier.risk_count} | {dossier.work_item_count} | {rec_short} |"
            )

        lines.extend(["", "---", "", "## Detailed Dossiers", ""])

        # Full dossiers
        for dossier in dossiers:
            emoji = status_emoji.get(dossier.overall_status, '⚪')

            lines.extend([
                f"### {dossier.name}",
                "",
                f"**Status:** {emoji} {dossier.overall_status.upper()} | **Entity:** {dossier.entity} | **Category:** {dossier.category}",
                "",
            ])

            # Summary
            lines.extend([
                "#### Summary",
                "",
                f"> {dossier.summary}",
                "",
            ])

            # Key considerations
            if dossier.key_considerations:
                lines.extend([
                    "#### Key Considerations",
                    "",
                ])
                for consideration in dossier.key_considerations:
                    lines.append(f"- {consideration}")
                lines.append("")

            # Core attributes
            if dossier.attributes:
                lines.extend([
                    "#### Attributes",
                    "",
                    "| Field | Value |",
                    "|-------|-------|",
                ])
                for key, value in list(dossier.attributes.items())[:10]:
                    lines.append(f"| {key.replace('_', ' ').title()} | {value} |")
                lines.append("")

            # Evidence
            if dossier.evidence:
                lines.extend([
                    "#### Source Evidence",
                    "",
                ])
                for ev in dossier.evidence[:3]:
                    source = ev.source_document if hasattr(ev, 'source_document') else ev.get('source_document', 'Unknown')
                    quote = ev.quote if hasattr(ev, 'quote') else ev.get('quote', '')
                    lines.append(f"> \"{quote[:200]}{'...' if len(quote) > 200 else ''}\"")
                    lines.append(f"> — *{source}*")
                    lines.append("")

            # Risks
            if dossier.risks:
                lines.extend([
                    "#### Related Risks",
                    "",
                ])
                for risk in dossier.risks:
                    risk_id = risk.risk_id if hasattr(risk, 'risk_id') else risk.get('risk_id', '')
                    title = risk.title if hasattr(risk, 'title') else risk.get('title', '')
                    severity = risk.severity if hasattr(risk, 'severity') else risk.get('severity', '')
                    desc = risk.description if hasattr(risk, 'description') else risk.get('description', '')
                    mitigation = risk.mitigation if hasattr(risk, 'mitigation') else risk.get('mitigation', '')

                    lines.extend([
                        f"**{risk_id}: {title}** (Severity: {severity.upper()})",
                        "",
                        f"{desc[:300]}{'...' if len(desc) > 300 else ''}",
                        "",
                    ])
                    if mitigation:
                        lines.append(f"*Mitigation:* {mitigation[:200]}")
                        lines.append("")

            # Work Items
            if dossier.work_items:
                lines.extend([
                    "#### Work Items",
                    "",
                ])
                for wi in dossier.work_items:
                    wi_id = wi.work_item_id if hasattr(wi, 'work_item_id') else wi.get('work_item_id', '')
                    title = wi.title if hasattr(wi, 'title') else wi.get('title', '')
                    phase = wi.phase if hasattr(wi, 'phase') else wi.get('phase', '')
                    desc = wi.description if hasattr(wi, 'description') else wi.get('description', '')

                    lines.append(f"- **{wi_id}**: {title} ({phase})")
                    if desc:
                        lines.append(f"  - {desc[:150]}{'...' if len(desc) > 150 else ''}")
                lines.append("")

            # Narrative excerpts
            if dossier.narrative_excerpts:
                lines.extend([
                    "#### From Report Narrative",
                    "",
                ])
                for excerpt in dossier.narrative_excerpts:
                    lines.append(f"> {excerpt}")
                    lines.append("")

            # Recommendation
            lines.extend([
                "#### Recommendation",
                "",
                f"**{dossier.recommendation}**",
                "",
                "---",
                "",
            ])

        output_path.write_text('\n'.join(lines))
        return output_path

    @staticmethod
    def export_to_string(dossiers: List[ItemDossier], domain: str) -> str:
        """Export domain dossiers to Markdown string (no file)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "temp.md"
            DossierMarkdownExporter.export_domain(dossiers, domain, output_path)
            return output_path.read_text()


class DossierJSONExporter:
    """Export dossiers to JSON format for programmatic access."""

    @staticmethod
    def export_domain(dossiers: List[ItemDossier], domain: str, output_path: Path) -> Path:
        """Export domain dossiers to JSON."""
        data = {
            "domain": domain,
            "generated_at": datetime.now().isoformat(),
            "total_items": len(dossiers),
            "summary": {
                "red": len([d for d in dossiers if d.overall_status == 'red']),
                "yellow": len([d for d in dossiers if d.overall_status == 'yellow']),
                "green": len([d for d in dossiers if d.overall_status == 'green']),
            },
            "dossiers": [d.to_dict() for d in dossiers]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return output_path

    @staticmethod
    def export_to_string(dossiers: List[ItemDossier], domain: str) -> str:
        """Export domain dossiers to JSON string (no file)."""
        data = {
            "domain": domain,
            "generated_at": datetime.now().isoformat(),
            "total_items": len(dossiers),
            "summary": {
                "red": len([d for d in dossiers if d.overall_status == 'red']),
                "yellow": len([d for d in dossiers if d.overall_status == 'yellow']),
                "green": len([d for d in dossiers if d.overall_status == 'green']),
            },
            "dossiers": [d.to_dict() for d in dossiers]
        }
        return json.dumps(data, indent=2, default=str)


class DossierHTMLExporter:
    """Export dossiers to interactive HTML format."""

    @staticmethod
    def export_domain(dossiers: List[ItemDossier], domain: str, output_path: Path) -> Path:
        """Export domain dossiers to HTML with collapsible sections."""

        status_colors = {
            'red': '#dc3545',
            'yellow': '#ffc107',
            'green': '#28a745'
        }

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{domain.replace('_', ' ').title()} Inventory Dossiers</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .summary {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            flex: 1;
        }}
        .stat-card .count {{ font-size: 2em; font-weight: bold; }}
        .stat-card.red .count {{ color: #dc3545; }}
        .stat-card.yellow .count {{ color: #ffc107; }}
        .stat-card.green .count {{ color: #28a745; }}

        .dossier {{
            background: white;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .dossier-header {{
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 5px solid;
        }}
        .dossier-header.red {{ border-color: #dc3545; background: #fff5f5; }}
        .dossier-header.yellow {{ border-color: #ffc107; background: #fffdf5; }}
        .dossier-header.green {{ border-color: #28a745; background: #f5fff5; }}
        .dossier-header h3 {{ margin: 0; }}
        .dossier-header .badges {{ display: flex; gap: 10px; }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
        }}
        .badge.risk {{ background: #dc354520; color: #dc3545; }}
        .badge.work {{ background: #007bff20; color: #007bff; }}

        /* Entity badges (Phase 2 - Entity Separation) */
        .entity-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
            margin-right: 10px;
            letter-spacing: 0.5px;
        }}
        .entity-badge.target {{ background: #007bff; color: white; }}
        .entity-badge.buyer {{ background: #6f42c1; color: white; }}
        .entity-badge.unknown {{ background: #dc3545; color: white; }}

        /* Entity stat cards */
        .stat-card.target {{ border-top: 3px solid #007bff; }}
        .stat-card.buyer {{ border-top: 3px solid #6f42c1; }}

        .dossier-content {{
            display: none;
            padding: 20px;
            border-top: 1px solid #eee;
        }}
        .dossier.open .dossier-content {{ display: block; }}

        .section {{ margin-bottom: 20px; }}
        .section h4 {{
            color: #555;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }}
        .evidence {{
            background: #f8f9fa;
            padding: 15px;
            border-left: 3px solid #007bff;
            margin: 10px 0;
            font-style: italic;
        }}
        .evidence .source {{ font-size: 0.85em; color: #666; margin-top: 5px; font-style: normal; }}

        .risk-item, .work-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .risk-item {{ border-left: 3px solid #dc3545; }}
        .work-item {{ border-left: 3px solid #007bff; }}
        .risk-item .severity {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            text-transform: uppercase;
        }}
        .severity.critical {{ background: #dc3545; color: white; }}
        .severity.high {{ background: #fd7e14; color: white; }}
        .severity.medium {{ background: #ffc107; color: black; }}
        .severity.low {{ background: #28a745; color: white; }}

        .recommendation {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 4px;
            border-left: 3px solid #007bff;
        }}

        .attributes-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .attributes-table td {{
            padding: 8px;
            border-bottom: 1px solid #eee;
        }}
        .attributes-table td:first-child {{
            font-weight: 500;
            width: 30%;
            color: #555;
        }}

        .toggle {{ font-size: 1.2em; color: #666; }}
        .dossier.open .toggle {{ transform: rotate(90deg); }}

        .filter-bar {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }}
        .filter-btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background: #e9ecef;
        }}
        .filter-btn.active {{ background: #007bff; color: white; }}
    </style>
</head>
<body>
    <h1>{domain.replace('_', ' ').title()} Inventory</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

    <div class="summary">
        <div class="stat-card red">
            <div class="count">{len([d for d in dossiers if d.overall_status == 'red'])}</div>
            <div>Critical/High Risk</div>
        </div>
        <div class="stat-card yellow">
            <div class="count">{len([d for d in dossiers if d.overall_status == 'yellow'])}</div>
            <div>Moderate Concerns</div>
        </div>
        <div class="stat-card green">
            <div class="count">{len([d for d in dossiers if d.overall_status == 'green'])}</div>
            <div>No Issues</div>
        </div>
        <div class="stat-card target">
            <div class="count">{len([d for d in dossiers if d.entity == 'target'])}</div>
            <div>🎯 Target</div>
        </div>
        <div class="stat-card buyer">
            <div class="count">{len([d for d in dossiers if d.entity == 'buyer'])}</div>
            <div>🏢 Buyer</div>
        </div>
    </div>

    <div class="filter-bar">
        <button class="filter-btn active" onclick="filterDossiers('all')">All ({len(dossiers)})</button>
        <button class="filter-btn" onclick="filterDossiers('red')">🔴 Critical ({len([d for d in dossiers if d.overall_status == 'red'])})</button>
        <button class="filter-btn" onclick="filterDossiers('yellow')">🟡 Moderate ({len([d for d in dossiers if d.overall_status == 'yellow'])})</button>
        <button class="filter-btn" onclick="filterDossiers('green')">🟢 OK ({len([d for d in dossiers if d.overall_status == 'green'])})</button>
        <span style="border-left: 1px solid #ccc; margin: 0 10px;"></span>
        <button class="filter-btn" onclick="filterByEntity('target')">🎯 Target Only ({len([d for d in dossiers if d.entity == 'target'])})</button>
        <button class="filter-btn" onclick="filterByEntity('buyer')">🏢 Buyer Only ({len([d for d in dossiers if d.entity == 'buyer'])})</button>
    </div>
"""

        for dossier in dossiers:
            # Build evidence HTML with quality indicators (Phase 3)
            evidence_html = ""
            for ev in dossier.evidence[:3]:  # Show up to 3 evidence items
                quote = ev.quote if hasattr(ev, 'quote') else ev.get('quote', '')

                # Get formatted citation if available
                if hasattr(ev, 'format_citation'):
                    citation = ev.format_citation()
                else:
                    citation = ev.source_document if hasattr(ev, 'source_document') else ev.get('source_document', '')

                # Get quality score for indicator
                if hasattr(ev, 'quality_score'):
                    quality = ev.quality_score()
                    quality_indicator = "⭐" * quality if quality > 0 else "⚠️"
                else:
                    quality_indicator = ""

                # Get fact ID for traceability
                fact_id = ev.fact_id if hasattr(ev, 'fact_id') else ev.get('fact_id', '')
                fact_id_html = f'<span style="color:#007bff;font-weight:500">[{fact_id}]</span> ' if fact_id else ''

                evidence_html += f'''<div class="evidence">
                    "{quote[:250]}{"..." if len(quote) > 250 else ""}"
                    <div class="source">{fact_id_html}{quality_indicator} — {citation}</div>
                </div>'''

            # Build risks HTML
            risks_html = ""
            for risk in dossier.risks:
                risk_id = risk.risk_id if hasattr(risk, 'risk_id') else risk.get('risk_id', '')
                title = risk.title if hasattr(risk, 'title') else risk.get('title', '')
                severity = risk.severity if hasattr(risk, 'severity') else risk.get('severity', '')
                desc = risk.description if hasattr(risk, 'description') else risk.get('description', '')
                risks_html += f'''
                <div class="risk-item">
                    <strong>{risk_id}: {title}</strong>
                    <span class="severity {severity.lower()}">{severity}</span>
                    <p>{desc[:300]}{"..." if len(desc) > 300 else ""}</p>
                </div>'''

            # Build work items HTML
            work_html = ""
            for wi in dossier.work_items:
                wi_id = wi.work_item_id if hasattr(wi, 'work_item_id') else wi.get('work_item_id', '')
                title = wi.title if hasattr(wi, 'title') else wi.get('title', '')
                phase = wi.phase if hasattr(wi, 'phase') else wi.get('phase', '')
                work_html += f'<div class="work-item"><strong>{wi_id}: {title}</strong> <span style="color:#666">({phase})</span></div>'

            # Build attributes HTML
            attrs_html = ""
            for key, value in list(dossier.attributes.items())[:8]:
                attrs_html += f'<tr><td>{key.replace("_", " ").title()}</td><td>{value}</td></tr>'

            # Build data gaps HTML (Phase 4)
            gaps_html = ""
            if dossier.data_gaps:
                completeness_pct = int(dossier.data_completeness * 100)
                completeness_class = "red" if completeness_pct < 50 else "yellow"
                gaps_list = ''.join(f'<li>{g.replace("_", " ").title()}</li>' for g in dossier.data_gaps)
                gaps_html = f'''
                <div class="section" style="background: #fff3cd; padding: 15px; border-radius: 4px; border-left: 3px solid #ffc107;">
                    <h4 style="color: #856404; margin-top: 0;">⚠️ Data Gaps ({len(dossier.data_gaps)} critical fields missing)</h4>
                    <ul style="margin: 10px 0;">{gaps_list}</ul>
                    <p style="margin: 0; color: #856404;">
                        <strong>Data completeness:</strong> {completeness_pct}%
                        <span style="margin-left: 15px;">📋 These fields should be added to VDR request list.</span>
                    </p>
                </div>'''

            # Build conflicts HTML (Phase 6)
            conflicts_html = ""
            if dossier.has_conflicts and dossier.attribute_conflicts:
                conflicts_rows = ''.join(
                    f'<tr><td><strong>{k.replace("_", " ").title()}</strong></td><td>{" vs ".join(str(v) for v in vals)}</td></tr>'
                    for k, vals in dossier.attribute_conflicts.items()
                )
                conflicts_html = f'''
                <div class="section" style="background: #f8d7da; padding: 15px; border-radius: 4px; border-left: 3px solid #dc3545;">
                    <h4 style="color: #721c24; margin-top: 0;">⚠️ Data Conflicts Detected ({dossier.conflict_count})</h4>
                    <p style="color: #721c24;">Multiple values found for the same attribute. Review source documents:</p>
                    <table style="width: 100%;"><tbody>{conflicts_rows}</tbody></table>
                </div>'''

            # Determine entity class for badge styling
            entity_class = dossier.entity if dossier.entity in ['target', 'buyer'] else 'unknown'
            entity_label = dossier.entity.upper() if dossier.entity else 'UNKNOWN'

            html += f"""
    <div class="dossier" data-status="{dossier.overall_status}" data-entity="{dossier.entity}">
        <div class="dossier-header {dossier.overall_status}" onclick="toggleDossier(this.parentElement)">
            <h3>
                <span class="entity-badge {entity_class}">{entity_label}</span>
                {dossier.name}
            </h3>
            <div class="badges">
                {f'<span class="badge risk">{dossier.risk_count} Risks</span>' if dossier.risk_count else ''}
                {f'<span class="badge work">{dossier.work_item_count} Work Items</span>' if dossier.work_item_count else ''}
                <span class="toggle">▶</span>
            </div>
        </div>
        <div class="dossier-content">
            <div class="section">
                <h4>Summary</h4>
                <p>{dossier.summary}</p>
            </div>

            {'<div class="section"><h4>Key Considerations</h4><ul>' + ''.join(f'<li>{c}</li>' for c in dossier.key_considerations) + '</ul></div>' if dossier.key_considerations else ''}

            {'<div class="section"><h4>Attributes</h4><table class="attributes-table">' + attrs_html + '</table></div>' if attrs_html else ''}

            {gaps_html}

            {conflicts_html}

            {'<div class="section"><h4>Source Evidence</h4>' + evidence_html + '</div>' if evidence_html else ''}

            {'<div class="section"><h4>Related Risks</h4>' + risks_html + '</div>' if risks_html else ''}

            {'<div class="section"><h4>Work Items</h4>' + work_html + '</div>' if work_html else ''}

            <div class="section">
                <h4>Recommendation</h4>
                <div class="recommendation">{dossier.recommendation}</div>
            </div>
        </div>
    </div>
"""

        html += """
    <script>
        // Track current filters
        let currentStatusFilter = 'all';
        let currentEntityFilter = 'all';

        function toggleDossier(el) {
            el.classList.toggle('open');
        }

        function applyFilters() {
            document.querySelectorAll('.dossier').forEach(d => {
                const matchesStatus = currentStatusFilter === 'all' || d.dataset.status === currentStatusFilter;
                const matchesEntity = currentEntityFilter === 'all' || d.dataset.entity === currentEntityFilter;
                d.style.display = (matchesStatus && matchesEntity) ? 'block' : 'none';
            });
        }

        function filterDossiers(status) {
            // Update status filter buttons
            document.querySelectorAll('.filter-btn').forEach(btn => {
                if (btn.onclick && btn.onclick.toString().includes('filterDossiers')) {
                    btn.classList.remove('active');
                }
            });
            event.target.classList.add('active');

            currentStatusFilter = status;
            applyFilters();
        }

        function filterByEntity(entity) {
            // Update entity filter buttons
            document.querySelectorAll('.filter-btn').forEach(btn => {
                if (btn.onclick && btn.onclick.toString().includes('filterByEntity')) {
                    btn.classList.remove('active');
                }
            });
            if (currentEntityFilter !== entity) {
                event.target.classList.add('active');
                currentEntityFilter = entity;
            } else {
                // Toggle off - show all entities
                currentEntityFilter = 'all';
            }
            applyFilters();
        }

        // Expand first red item by default
        const firstRed = document.querySelector('.dossier[data-status="red"]');
        if (firstRed) firstRed.classList.add('open');
    </script>
</body>
</html>"""

        output_path.write_text(html)
        return output_path

    @staticmethod
    def export_to_string(dossiers: List[ItemDossier], domain: str) -> str:
        """Export domain dossiers to HTML string (no file)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "temp.html"
            DossierHTMLExporter.export_domain(dossiers, domain, output_path)
            return output_path.read_text()


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def build_and_export_dossiers(
    facts_path: Path,
    findings_path: Path,
    output_dir: Path,
    narratives: Dict[str, str] = None
) -> Dict[str, List[Path]]:
    """
    Build and export dossiers for all domains.

    Args:
        facts_path: Path to facts JSON
        findings_path: Path to findings JSON
        output_dir: Directory for exports
        narratives: Optional domain -> narrative text mapping

    Returns:
        Dict mapping domain -> list of exported file paths
    """
    # Load data
    with open(facts_path) as f:
        facts_data = json.load(f)

    if isinstance(facts_data, dict) and 'facts' in facts_data:
        facts = facts_data['facts']
    elif isinstance(facts_data, list):
        facts = facts_data
    else:
        facts = []

    with open(findings_path) as f:
        findings = json.load(f)

    # Build dossiers
    builder = DossierBuilder(facts, findings, narratives)
    all_dossiers = builder.build_all_dossiers()

    # Export
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for domain, dossiers in all_dossiers.items():
        results[domain] = [
            DossierMarkdownExporter.export_domain(dossiers, domain, output_dir / f"{domain}_dossiers.md"),
            DossierJSONExporter.export_domain(dossiers, domain, output_dir / f"{domain}_dossiers.json"),
            DossierHTMLExporter.export_domain(dossiers, domain, output_dir / f"{domain}_dossiers.html"),
        ]
        logger.info(f"Exported {len(dossiers)} {domain} dossiers")

    return results
