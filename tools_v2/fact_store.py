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
import json
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


@dataclass
class Fact:
    """
    A single extracted fact with unique ID for citation.

    Facts are observations from the document - NOT conclusions.
    The Reasoning phase will analyze facts and draw conclusions.
    """
    fact_id: str              # F-INFRA-001
    domain: str               # infrastructure, network, etc.
    category: str             # hosting, compute, storage, etc.
    item: str                 # What this fact is about
    details: Dict[str, Any]   # Flexible key-value pairs
    status: str               # documented, partial, gap
    evidence: Dict[str, str]  # exact_quote, source_section
    entity: str = "target"    # "target" (being acquired) or "buyer" - CRITICAL for avoiding confusion
    source_document: str = "" # Filename of source document (for incremental updates)
    created_at: str = field(default_factory=lambda: _generate_timestamp())
    updated_at: str = ""      # Set when fact is modified

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Fact":
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
    created_at: str = field(default_factory=lambda: _generate_timestamp())

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Gap":
        return cls(**data)


class FactStore:
    """
    Central store for facts extracted during Discovery phase.

    Features:
    - Unique fact IDs for citation (F-{DOMAIN}-{SEQ})
    - Domain and category organization
    - Merge capability for parallel discovery agents
    - Export to JSON for reasoning phase handoff
    - Load from JSON to resume or reason from existing facts

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
    """

    def __init__(self):
        self.facts: List[Fact] = []
        self.gaps: List[Gap] = []
        self._fact_counters: Dict[str, int] = {}
        self._gap_counters: Dict[str, int] = {}
        self.discovery_complete: Dict[str, bool] = {}
        self.metadata: Dict[str, Any] = {
            "created_at": _generate_timestamp(),
            "version": "2.0"
        }
        # Thread safety: Lock for all mutating operations
        self._lock = threading.RLock()
        # Performance: Index for O(1) fact/gap lookups
        self._fact_index: Dict[str, Fact] = {}
        self._gap_index: Dict[str, Gap] = {}

    def add_fact(self, domain: str, category: str, item: str,
                 details: Dict[str, Any], status: str,
                 evidence: Dict[str, str], entity: str = "target",
                 source_document: str = "") -> str:
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

        Returns:
            Unique fact ID (e.g., F-INFRA-001)
        """
        # Validate entity - fail fast instead of silently defaulting
        if entity not in ("target", "buyer"):
            raise ValueError(f"Invalid entity '{entity}'. Must be 'target' or 'buyer'")
        
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
            fact_id = self._generate_fact_id(domain)

            fact = Fact(
                fact_id=fact_id,
                domain=domain,
                category=category,
                item=item,
                details=details or {},
                status=status,
                evidence=evidence or {},
                entity=entity,
                source_document=source_document
            )

            self.facts.append(fact)
            self._fact_index[fact_id] = fact  # Update index
            logger.debug(f"Added fact {fact_id}: {item}")

        return fact_id

    def add_gap(self, domain: str, category: str,
                description: str, importance: str) -> str:
        """
        Add a gap (missing information) and return its ID.

        Args:
            domain: infrastructure, network, etc.
            category: Category within domain
            description: What information is missing
            importance: critical, high, medium, low

        Returns:
            Unique gap ID (e.g., G-INFRA-001)
        """
        with self._lock:
            gap_id = self._generate_gap_id(domain)
            gap = Gap(
                gap_id=gap_id,
                domain=domain,
                category=category,
                description=description,
                importance=importance
            )

            self.gaps.append(gap)
            self._gap_index[gap_id] = gap  # Update index
            logger.debug(f"Added gap {gap_id}: {description[:50]}...")

        return gap_id

    def _generate_fact_id(self, domain: str) -> str:
        """
        Generate unique fact ID: F-{DOMAIN_PREFIX}-{SEQ}
        
        NOTE: Must be called within self._lock context.
        This method modifies self._fact_counters and is not thread-safe on its own.
        """
        prefix = DOMAIN_PREFIXES.get(domain, "GEN")

        if prefix not in self._fact_counters:
            self._fact_counters[prefix] = 0

        self._fact_counters[prefix] += 1
        return f"F-{prefix}-{self._fact_counters[prefix]:03d}"

    def _generate_gap_id(self, domain: str) -> str:
        """
        Generate unique gap ID: G-{DOMAIN_PREFIX}-{SEQ}
        
        NOTE: Must be called within self._lock context.
        This method modifies self._gap_counters and is not thread-safe on its own.
        """
        prefix = DOMAIN_PREFIXES.get(domain, "GEN")

        if prefix not in self._gap_counters:
            self._gap_counters[prefix] = 0

        self._gap_counters[prefix] += 1
        return f"G-{prefix}-{self._gap_counters[prefix]:03d}"

    def get_fact(self, fact_id: str) -> Optional[Fact]:
        """Get a specific fact by ID (O(1) lookup using index)."""
        with self._lock:
            return self._fact_index.get(fact_id)

    def get_gap(self, gap_id: str) -> Optional[Gap]:
        """Get a specific gap by ID (O(1) lookup using index)."""
        with self._lock:
            return self._gap_index.get(gap_id)

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
            Dict with all facts, gaps, and metadata
        """
        with self._lock:
            all_domains = set(f.domain for f in self.facts) | set(g.domain for g in self.gaps)

            return {
                "metadata": self.metadata,
                "summary": {
                    "total_facts": len(self.facts),
                    "total_gaps": len(self.gaps),
                    "domains": list(all_domains)
                },
                "facts": [f.to_dict() for f in self.facts],
                "gaps": [g.to_dict() for g in self.gaps],
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
    def load(cls, path: str) -> "FactStore":
        """Load fact store from JSON file with retry logic."""
        from tools_v2.io_utils import safe_file_read
        
        data = safe_file_read(path, mode='r', encoding='utf-8', max_retries=3)

        store = cls()
        store.metadata = data.get("metadata", {})

        # Load facts with robust ID parsing and index building
        for fact_dict in data.get("facts", []):
            fact = Fact.from_dict(fact_dict)
            store.facts.append(fact)
            store._fact_index[fact.fact_id] = fact  # Build index

            # Update counters to continue from loaded IDs (robust parsing)
            try:
                parts = fact.fact_id.split("-")
                if len(parts) >= 3:
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
                if len(parts) >= 3:
                    prefix = parts[1]
                    seq = int(parts[2])
                    store._gap_counters[prefix] = max(
                        store._gap_counters.get(prefix, 0), seq
                    )
                else:
                    logger.warning(f"Unexpected gap ID format: {gap.gap_id}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse gap ID {gap.gap_id}: {e}")

        store.discovery_complete = data.get("discovery_complete", {})

        logger.info(f"Loaded {len(store.facts)} facts from {path}")
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

    def __repr__(self) -> str:
        return f"FactStore(facts={len(self.facts)}, gaps={len(self.gaps)})"
