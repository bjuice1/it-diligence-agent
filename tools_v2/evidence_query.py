"""
Evidence Query Layer

Provides queryable access to facts, findings, and evidence to support
narrative generation and enable drill-down from summaries to details.

This layer enables:
1. Querying facts by domain, function, or tag
2. Tracing narrative statements back to evidence
3. Finding gaps in coverage
4. Supporting interactive exploration
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re


class EvidenceType(Enum):
    """Types of evidence."""
    FACT = "fact"           # Documented inventory item
    INFERENCE = "inference"  # Labeled inference from facts
    PATTERN = "pattern"      # Pattern-based observation
    GAP = "gap"             # Missing information
    RISK = "risk"           # Identified risk
    SYNERGY = "synergy"     # Identified opportunity


@dataclass
class Evidence:
    """A piece of evidence that supports findings."""
    evidence_id: str
    evidence_type: EvidenceType
    domain: str
    function: Optional[str]
    content: str
    details: Dict[str, Any] = field(default_factory=dict)
    source_facts: List[str] = field(default_factory=list)  # Fact IDs this is based on
    tags: List[str] = field(default_factory=list)
    mna_lens: Optional[str] = None
    confidence: str = "medium"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.value,
            "domain": self.domain,
            "function": self.function,
            "content": self.content,
            "details": self.details,
            "source_facts": self.source_facts,
            "tags": self.tags,
            "mna_lens": self.mna_lens,
            "confidence": self.confidence,
        }


@dataclass
class EvidenceIndex:
    """Index for fast evidence lookup."""
    by_id: Dict[str, Evidence] = field(default_factory=dict)
    by_domain: Dict[str, List[str]] = field(default_factory=dict)
    by_function: Dict[str, List[str]] = field(default_factory=dict)
    by_type: Dict[str, List[str]] = field(default_factory=dict)
    by_tag: Dict[str, List[str]] = field(default_factory=dict)
    by_mna_lens: Dict[str, List[str]] = field(default_factory=dict)
    by_source_fact: Dict[str, List[str]] = field(default_factory=dict)


class EvidenceStore:
    """
    Central store for all evidence supporting the narrative.
    Provides query capabilities for navigation and traceability.
    """

    def __init__(self):
        self.evidence: Dict[str, Evidence] = {}
        self.index = EvidenceIndex()
        self._id_counter = 0

    def add_evidence(self, evidence: Evidence) -> str:
        """Add evidence to the store and index it."""
        if not evidence.evidence_id:
            evidence.evidence_id = self._generate_id(evidence.evidence_type, evidence.domain)

        self.evidence[evidence.evidence_id] = evidence

        # Index by ID
        self.index.by_id[evidence.evidence_id] = evidence

        # Index by domain
        if evidence.domain not in self.index.by_domain:
            self.index.by_domain[evidence.domain] = []
        self.index.by_domain[evidence.domain].append(evidence.evidence_id)

        # Index by function
        if evidence.function:
            if evidence.function not in self.index.by_function:
                self.index.by_function[evidence.function] = []
            self.index.by_function[evidence.function].append(evidence.evidence_id)

        # Index by type
        type_key = evidence.evidence_type.value
        if type_key not in self.index.by_type:
            self.index.by_type[type_key] = []
        self.index.by_type[type_key].append(evidence.evidence_id)

        # Index by tags
        for tag in evidence.tags:
            if tag not in self.index.by_tag:
                self.index.by_tag[tag] = []
            self.index.by_tag[tag].append(evidence.evidence_id)

        # Index by M&A lens
        if evidence.mna_lens:
            if evidence.mna_lens not in self.index.by_mna_lens:
                self.index.by_mna_lens[evidence.mna_lens] = []
            self.index.by_mna_lens[evidence.mna_lens].append(evidence.evidence_id)

        # Index by source facts
        for fact_id in evidence.source_facts:
            if fact_id not in self.index.by_source_fact:
                self.index.by_source_fact[fact_id] = []
            self.index.by_source_fact[fact_id].append(evidence.evidence_id)

        return evidence.evidence_id

    def _generate_id(self, etype: EvidenceType, domain: str) -> str:
        """Generate a unique evidence ID."""
        self._id_counter += 1
        prefix_map = {
            EvidenceType.FACT: "F",
            EvidenceType.INFERENCE: "I",
            EvidenceType.PATTERN: "P",
            EvidenceType.GAP: "G",
            EvidenceType.RISK: "R",
            EvidenceType.SYNERGY: "S",
        }
        prefix = prefix_map.get(etype, "E")
        domain_abbr = domain[:4].upper()
        return f"{prefix}-{domain_abbr}-{self._id_counter:03d}"

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def get(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID."""
        return self.evidence.get(evidence_id)

    def query_by_domain(self, domain: str) -> List[Evidence]:
        """Get all evidence for a domain."""
        ids = self.index.by_domain.get(domain, [])
        return [self.evidence[eid] for eid in ids if eid in self.evidence]

    def query_by_function(self, function: str) -> List[Evidence]:
        """Get all evidence for a function."""
        ids = self.index.by_function.get(function, [])
        return [self.evidence[eid] for eid in ids if eid in self.evidence]

    def query_by_type(self, evidence_type: EvidenceType) -> List[Evidence]:
        """Get all evidence of a specific type."""
        ids = self.index.by_type.get(evidence_type.value, [])
        return [self.evidence[eid] for eid in ids if eid in self.evidence]

    def query_by_tag(self, tag: str) -> List[Evidence]:
        """Get all evidence with a specific tag."""
        ids = self.index.by_tag.get(tag, [])
        return [self.evidence[eid] for eid in ids if eid in self.evidence]

    def query_by_mna_lens(self, lens: str) -> List[Evidence]:
        """Get all evidence for an M&A lens."""
        ids = self.index.by_mna_lens.get(lens, [])
        return [self.evidence[eid] for eid in ids if eid in self.evidence]

    def query_by_source_fact(self, fact_id: str) -> List[Evidence]:
        """Get all evidence derived from a source fact."""
        ids = self.index.by_source_fact.get(fact_id, [])
        return [self.evidence[eid] for eid in ids if eid in self.evidence]

    def query(
        self,
        domain: Optional[str] = None,
        function: Optional[str] = None,
        evidence_type: Optional[EvidenceType] = None,
        mna_lens: Optional[str] = None,
        tags: Optional[List[str]] = None,
        text_search: Optional[str] = None,
    ) -> List[Evidence]:
        """
        Query evidence with multiple filters.
        All filters are ANDed together.
        """
        # Start with all evidence
        result_ids: Set[str] = set(self.evidence.keys())

        # Filter by domain
        if domain:
            domain_ids = set(self.index.by_domain.get(domain, []))
            result_ids &= domain_ids

        # Filter by function
        if function:
            func_ids = set(self.index.by_function.get(function, []))
            result_ids &= func_ids

        # Filter by type
        if evidence_type:
            type_ids = set(self.index.by_type.get(evidence_type.value, []))
            result_ids &= type_ids

        # Filter by M&A lens
        if mna_lens:
            lens_ids = set(self.index.by_mna_lens.get(mna_lens, []))
            result_ids &= lens_ids

        # Filter by tags (any tag matches)
        if tags:
            tag_ids: Set[str] = set()
            for tag in tags:
                tag_ids |= set(self.index.by_tag.get(tag, []))
            result_ids &= tag_ids

        # Text search in content
        if text_search:
            search_lower = text_search.lower()
            text_match_ids = {
                eid for eid in result_ids
                if search_lower in self.evidence[eid].content.lower()
            }
            result_ids &= text_match_ids

        return [self.evidence[eid] for eid in result_ids]

    # =========================================================================
    # TRACEABILITY METHODS
    # =========================================================================

    def trace_citation(self, citation: str) -> Optional[Evidence]:
        """
        Trace a citation (e.g., F-CYBER-001) back to evidence.
        """
        return self.get(citation)

    def extract_citations(self, text: str) -> List[str]:
        """
        Extract all citation IDs from text.
        Pattern: (F-DOMAIN-###) or F-DOMAIN-###
        """
        pattern = r'\(?([FIPGRS]-[A-Z]{3,4}-\d{3})\)?'
        matches = re.findall(pattern, text)
        return list(set(matches))

    def resolve_citations(self, text: str) -> Dict[str, Evidence]:
        """
        Extract and resolve all citations in text to their evidence.
        """
        citations = self.extract_citations(text)
        resolved = {}
        for cid in citations:
            evidence = self.get(cid)
            if evidence:
                resolved[cid] = evidence
        return resolved

    def get_evidence_chain(self, evidence_id: str) -> Dict[str, Any]:
        """
        Get the full evidence chain for a piece of evidence.
        Includes source facts and any derived evidence.
        """
        evidence = self.get(evidence_id)
        if not evidence:
            return {"error": f"Evidence {evidence_id} not found"}

        chain = {
            "evidence": evidence.to_dict(),
            "source_facts": [],
            "derived_from": [],
        }

        # Get source facts
        for fact_id in evidence.source_facts:
            fact = self.get(fact_id)
            if fact:
                chain["source_facts"].append(fact.to_dict())

        # Get anything derived from this evidence's source facts
        for fact_id in evidence.source_facts:
            derived = self.query_by_source_fact(fact_id)
            for d in derived:
                if d.evidence_id != evidence_id:
                    chain["derived_from"].append(d.to_dict())

        return chain

    # =========================================================================
    # COVERAGE ANALYSIS
    # =========================================================================

    def get_coverage_by_domain(self) -> Dict[str, Dict[str, int]]:
        """
        Get evidence coverage statistics by domain.
        """
        coverage = {}
        for domain in self.index.by_domain:
            domain_evidence = self.query_by_domain(domain)
            coverage[domain] = {
                "total": len(domain_evidence),
                "facts": len([e for e in domain_evidence if e.evidence_type == EvidenceType.FACT]),
                "inferences": len([e for e in domain_evidence if e.evidence_type == EvidenceType.INFERENCE]),
                "gaps": len([e for e in domain_evidence if e.evidence_type == EvidenceType.GAP]),
                "risks": len([e for e in domain_evidence if e.evidence_type == EvidenceType.RISK]),
            }
        return coverage

    def get_coverage_by_function(self) -> Dict[str, Dict[str, int]]:
        """
        Get evidence coverage statistics by function.
        """
        coverage = {}
        for function in self.index.by_function:
            func_evidence = self.query_by_function(function)
            coverage[function] = {
                "total": len(func_evidence),
                "facts": len([e for e in func_evidence if e.evidence_type == EvidenceType.FACT]),
                "gaps": len([e for e in func_evidence if e.evidence_type == EvidenceType.GAP]),
            }
        return coverage

    def get_gaps(self) -> List[Evidence]:
        """Get all documented gaps."""
        return self.query_by_type(EvidenceType.GAP)

    def get_gaps_by_domain(self) -> Dict[str, List[Evidence]]:
        """Get gaps organized by domain."""
        gaps = self.get_gaps()
        by_domain = {}
        for gap in gaps:
            if gap.domain not in by_domain:
                by_domain[gap.domain] = []
            by_domain[gap.domain].append(gap)
        return by_domain

    # =========================================================================
    # M&A LENS VIEWS
    # =========================================================================

    def get_day1_evidence(self) -> List[Evidence]:
        """Get all evidence related to Day-1 continuity."""
        return self.query_by_mna_lens("day_1_continuity")

    def get_tsa_evidence(self) -> List[Evidence]:
        """Get all evidence related to TSA exposure."""
        return self.query_by_mna_lens("tsa_exposure")

    def get_separation_evidence(self) -> List[Evidence]:
        """Get all evidence related to separation complexity."""
        return self.query_by_mna_lens("separation_complexity")

    def get_synergy_evidence(self) -> List[Evidence]:
        """Get all evidence related to synergy opportunities."""
        return self.query_by_mna_lens("synergy_opportunity")

    def get_mna_summary(self) -> Dict[str, int]:
        """Get summary counts by M&A lens."""
        return {
            lens: len(ids)
            for lens, ids in self.index.by_mna_lens.items()
        }

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Export entire store as dict."""
        return {
            "evidence": {eid: e.to_dict() for eid, e in self.evidence.items()},
            "summary": {
                "total": len(self.evidence),
                "by_type": {t: len(ids) for t, ids in self.index.by_type.items()},
                "by_domain": {d: len(ids) for d, ids in self.index.by_domain.items()},
                "by_mna_lens": self.get_mna_summary(),
            }
        }

    def to_markdown_index(self) -> str:
        """Generate a markdown index of all evidence."""
        lines = ["# Evidence Index\n"]

        # By domain
        lines.append("## By Domain\n")
        for domain in sorted(self.index.by_domain.keys()):
            evidence_list = self.query_by_domain(domain)
            lines.append(f"### {domain.title()} ({len(evidence_list)} items)\n")
            for e in evidence_list:
                lines.append(f"- **{e.evidence_id}** [{e.evidence_type.value}]: {e.content[:80]}...")
            lines.append("")

        # Gaps summary
        gaps = self.get_gaps()
        if gaps:
            lines.append("## Gaps Requiring Follow-up\n")
            for gap in gaps:
                lines.append(f"- **{gap.evidence_id}** ({gap.domain}): {gap.content}")
            lines.append("")

        # M&A lens summary
        lines.append("## By M&A Lens\n")
        for lens, count in self.get_mna_summary().items():
            lines.append(f"- **{lens}**: {count} items")

        return "\n".join(lines)


# =============================================================================
# FACT STORE INTEGRATION
# =============================================================================

def import_from_fact_store(fact_store: Any, evidence_store: EvidenceStore) -> int:
    """
    Import facts from the existing FactStore into the EvidenceStore.

    Args:
        fact_store: The existing FactStore instance
        evidence_store: The EvidenceStore to populate

    Returns:
        Number of facts imported
    """
    imported = 0

    for fact in fact_store.facts:
        evidence = Evidence(
            evidence_id=fact.fact_id,
            evidence_type=EvidenceType.FACT,
            domain=fact.domain if hasattr(fact, 'domain') else _infer_domain(fact.fact_id),
            function=fact.function if hasattr(fact, 'function') else None,
            content=fact.item if hasattr(fact, 'item') else str(fact),
            details=fact.details if hasattr(fact, 'details') else {},
            tags=fact.tags if hasattr(fact, 'tags') else [],
            confidence="high",  # Facts are high confidence
        )
        evidence_store.add_evidence(evidence)
        imported += 1

    return imported


def _infer_domain(fact_id: str) -> str:
    """Infer domain from fact ID pattern."""
    if not fact_id:
        return "unknown"

    # Pattern: F-DOMAIN-###
    parts = fact_id.split("-")
    if len(parts) >= 2:
        domain_map = {
            "INFRA": "infrastructure",
            "APP": "applications",
            "APPS": "applications",
            "ORG": "organization",
            "CYBER": "cybersecurity",
            "SEC": "cybersecurity",
            "IAM": "identity_access",
            "ID": "identity_access",
            "NET": "network",
        }
        return domain_map.get(parts[1].upper(), "unknown")

    return "unknown"


# =============================================================================
# QUERY BUILDER FOR UI
# =============================================================================

class QueryBuilder:
    """
    Builder pattern for constructing evidence queries.
    Useful for UI filters.
    """

    def __init__(self, store: EvidenceStore):
        self.store = store
        self._domain: Optional[str] = None
        self._function: Optional[str] = None
        self._type: Optional[EvidenceType] = None
        self._lens: Optional[str] = None
        self._tags: List[str] = []
        self._text: Optional[str] = None

    def domain(self, domain: str) -> 'QueryBuilder':
        self._domain = domain
        return self

    def function(self, function: str) -> 'QueryBuilder':
        self._function = function
        return self

    def type(self, evidence_type: EvidenceType) -> 'QueryBuilder':
        self._type = evidence_type
        return self

    def mna_lens(self, lens: str) -> 'QueryBuilder':
        self._lens = lens
        return self

    def tag(self, tag: str) -> 'QueryBuilder':
        self._tags.append(tag)
        return self

    def text(self, search: str) -> 'QueryBuilder':
        self._text = search
        return self

    def execute(self) -> List[Evidence]:
        return self.store.query(
            domain=self._domain,
            function=self._function,
            evidence_type=self._type,
            mna_lens=self._lens,
            tags=self._tags if self._tags else None,
            text_search=self._text,
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'EvidenceType',
    'Evidence',
    'EvidenceStore',
    'EvidenceIndex',
    'QueryBuilder',
    'import_from_fact_store',
]
