"""
Granular Facts Store - Line-Item Level Fact Storage

This module provides storage and management for granular (line-item) facts
extracted during Pass 2 of the multi-pass extraction process.

Each granular fact represents a single data point:
- 47 EC2 instances
- NetSuite version 2024.1
- 4.2 TB storage capacity
- $45,000/month cloud spend

These facts link back to parent systems and forward to source evidence.
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# FACT TYPE DEFINITIONS
# =============================================================================

FACT_TYPES = {
    "count": "Numeric quantity (instances, users, licenses)",
    "version": "Software/hardware version",
    "capacity": "Size, throughput, or limit",
    "cost": "Dollar amount (one-time or recurring)",
    "date": "Temporal reference (implementation, renewal, EOL)",
    "config": "Configuration setting or option",
    "status": "State indicator (active, deprecated, planned)",
    "integration": "System-to-system connection",
    "location": "Geographic or logical location",
    "contact": "Person or team reference",
    "sla": "Service level agreement term",
    "license": "Licensing information",
    "vendor": "Vendor/supplier detail",
    "other": "Uncategorized fact"
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GranularFact:
    """
    A single line-item fact with full traceability.

    Example:
        GranularFact(
            granular_fact_id="GF-a3f2",
            parent_system_id="SYS-b7c1",
            domain="infrastructure",
            category="cloud_compute",
            fact_type="count",
            item="EC2 Instances",
            value=47,
            unit="instances",
            context={"regions": ["us-east-1", "us-west-2"], "types": "mixed"},
            evidence_quote="...running 47 EC2 instances across 3 AWS regions...",
            source_document="IT Overview.pdf",
            source_page=12,
            confidence=0.95
        )
    """
    granular_fact_id: str
    parent_system_id: Optional[str]  # Links to System Registry
    domain: str
    category: str
    fact_type: str
    item: str
    value: Any  # Can be int, float, str, bool, list
    unit: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    evidence_quote: str = ""
    source_document: str = ""
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    confidence: float = 1.0
    entity: str = "target"  # target or buyer
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    validated: bool = False
    validation_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GranularFact':
        """Create from dictionary."""
        return cls(**data)

    def to_row(self) -> Dict[str, Any]:
        """Convert to flat row for Excel/CSV export."""
        return {
            "ID": self.granular_fact_id,
            "Parent System": self.parent_system_id or "",
            "Domain": self.domain,
            "Category": self.category,
            "Type": self.fact_type,
            "Item": self.item,
            "Value": self.value,
            "Unit": self.unit or "",
            "Context": json.dumps(self.context) if self.context else "",
            "Evidence": self.evidence_quote[:200] if self.evidence_quote else "",
            "Source": self.source_document,
            "Page": self.source_page or "",
            "Section": self.source_section or "",
            "Confidence": f"{self.confidence:.0%}",
            "Entity": self.entity,
            "Validated": "Yes" if self.validated else "No"
        }


# =============================================================================
# GRANULAR FACTS STORE
# =============================================================================

class GranularFactsStore:
    """
    Storage and management for granular (line-item) facts.

    Features:
    - Hash-based IDs for deduplication
    - Parent system linking
    - Multi-format export (JSON, CSV, Excel-ready)
    - Filtering and aggregation
    - Validation status tracking
    """

    def __init__(self):
        self._facts: Dict[str, GranularFact] = {}
        self._by_system: Dict[str, List[str]] = {}  # system_id -> [fact_ids]
        self._by_domain: Dict[str, List[str]] = {}  # domain -> [fact_ids]
        self._by_type: Dict[str, List[str]] = {}    # fact_type -> [fact_ids]
        self.created_at: str = datetime.utcnow().isoformat()
        self.last_updated: str = self.created_at

    def _generate_fact_id(self, domain: str, item: str, value: Any,
                          parent_system_id: Optional[str] = None) -> str:
        """Generate stable, deterministic fact ID from content."""
        content = f"{domain}|{item}|{value}|{parent_system_id or ''}"
        content = content.lower().strip()
        hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()[:6]
        return f"GF-{hash_value}"

    def add_fact(
        self,
        domain: str,
        category: str,
        fact_type: str,
        item: str,
        value: Any,
        unit: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        evidence_quote: str = "",
        source_document: str = "",
        source_page: Optional[int] = None,
        source_section: Optional[str] = None,
        parent_system_id: Optional[str] = None,
        confidence: float = 1.0,
        entity: str = "target"
    ) -> str:
        """
        Add a granular fact to the store.

        Returns:
            The fact ID (existing if duplicate, new if unique)
        """
        # Generate stable ID
        fact_id = self._generate_fact_id(domain, item, value, parent_system_id)

        # Check for duplicate
        if fact_id in self._facts:
            logger.debug(f"Duplicate fact detected: {fact_id}")
            # Update if new evidence is better
            existing = self._facts[fact_id]
            if len(evidence_quote) > len(existing.evidence_quote):
                existing.evidence_quote = evidence_quote
                existing.source_document = source_document
                existing.source_page = source_page
            return fact_id

        # Create new fact
        fact = GranularFact(
            granular_fact_id=fact_id,
            parent_system_id=parent_system_id,
            domain=domain,
            category=category,
            fact_type=fact_type,
            item=item,
            value=value,
            unit=unit,
            context=context or {},
            evidence_quote=evidence_quote,
            source_document=source_document,
            source_page=source_page,
            source_section=source_section,
            confidence=confidence,
            entity=entity
        )

        # Store and index
        self._facts[fact_id] = fact
        self._index_fact(fact)
        self.last_updated = datetime.utcnow().isoformat()

        logger.info(f"Added granular fact: {fact_id} - {item}: {value}")
        return fact_id

    def _index_fact(self, fact: GranularFact):
        """Add fact to indices for fast lookup."""
        # Index by system
        if fact.parent_system_id:
            if fact.parent_system_id not in self._by_system:
                self._by_system[fact.parent_system_id] = []
            self._by_system[fact.parent_system_id].append(fact.granular_fact_id)

        # Index by domain
        if fact.domain not in self._by_domain:
            self._by_domain[fact.domain] = []
        self._by_domain[fact.domain].append(fact.granular_fact_id)

        # Index by type
        if fact.fact_type not in self._by_type:
            self._by_type[fact.fact_type] = []
        self._by_type[fact.fact_type].append(fact.granular_fact_id)

    def get_fact(self, fact_id: str) -> Optional[GranularFact]:
        """Get a fact by ID."""
        return self._facts.get(fact_id)

    def get_all_facts(self) -> List[GranularFact]:
        """Get all facts."""
        return list(self._facts.values())

    def get_facts_by_system(self, system_id: str) -> List[GranularFact]:
        """Get all facts for a specific system."""
        fact_ids = self._by_system.get(system_id, [])
        return [self._facts[fid] for fid in fact_ids if fid in self._facts]

    def get_facts_by_domain(self, domain: str) -> List[GranularFact]:
        """Get all facts for a specific domain."""
        fact_ids = self._by_domain.get(domain, [])
        return [self._facts[fid] for fid in fact_ids if fid in self._facts]

    def get_facts_by_type(self, fact_type: str) -> List[GranularFact]:
        """Get all facts of a specific type."""
        fact_ids = self._by_type.get(fact_type, [])
        return [self._facts[fid] for fid in fact_ids if fid in self._facts]

    def get_numeric_facts(self) -> List[GranularFact]:
        """Get all facts with numeric values (for aggregation)."""
        return [f for f in self._facts.values()
                if isinstance(f.value, (int, float))]

    def sum_by_item(self, item_pattern: str) -> float:
        """Sum all numeric values for facts matching an item pattern."""
        total = 0.0
        pattern = item_pattern.lower()
        for fact in self._facts.values():
            if pattern in fact.item.lower() and isinstance(fact.value, (int, float)):
                total += fact.value
        return total

    def count_by_domain(self) -> Dict[str, int]:
        """Count facts per domain."""
        return {domain: len(facts) for domain, facts in self._by_domain.items()}

    def count_by_type(self) -> Dict[str, int]:
        """Count facts per type."""
        return {ftype: len(facts) for ftype, facts in self._by_type.items()}

    def count_by_system(self) -> Dict[str, int]:
        """Count facts per system."""
        return {sys: len(facts) for sys, facts in self._by_system.items()}

    @property
    def total_facts(self) -> int:
        """Total number of facts."""
        return len(self._facts)

    @property
    def domains(self) -> List[str]:
        """List of domains with facts."""
        return list(self._by_domain.keys())

    @property
    def systems(self) -> List[str]:
        """List of systems with facts."""
        return list(self._by_system.keys())

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def to_rows(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Convert facts to flat rows for Excel/CSV export.

        Args:
            domain: Optional domain filter

        Returns:
            List of row dictionaries
        """
        if domain:
            facts = self.get_facts_by_domain(domain)
        else:
            facts = self.get_all_facts()

        return [f.to_row() for f in facts]

    def to_json(self) -> str:
        """Export all facts as JSON string."""
        data = {
            "metadata": {
                "total_facts": self.total_facts,
                "domains": self.domains,
                "created_at": self.created_at,
                "last_updated": self.last_updated
            },
            "facts": [f.to_dict() for f in self._facts.values()]
        }
        return json.dumps(data, indent=2, default=str)

    def to_csv_rows(self) -> List[List[str]]:
        """Export as CSV-ready rows (header + data)."""
        if not self._facts:
            return []

        # Header
        rows = [list(self.to_rows()[0].keys())] if self._facts else []

        # Data rows
        for fact in self._facts.values():
            row_dict = fact.to_row()
            rows.append([str(v) for v in row_dict.values()])

        return rows

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def save(self, filepath: Path):
        """Save store to JSON file."""
        data = {
            "metadata": {
                "total_facts": self.total_facts,
                "created_at": self.created_at,
                "last_updated": self.last_updated
            },
            "facts": [f.to_dict() for f in self._facts.values()]
        }

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved {self.total_facts} granular facts to {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> 'GranularFactsStore':
        """Load store from JSON file."""
        store = cls()

        filepath = Path(filepath)
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return store

        with open(filepath, 'r') as f:
            data = json.load(f)

        store.created_at = data.get("metadata", {}).get("created_at", store.created_at)
        store.last_updated = data.get("metadata", {}).get("last_updated", store.last_updated)

        for fact_data in data.get("facts", []):
            fact = GranularFact.from_dict(fact_data)
            store._facts[fact.granular_fact_id] = fact
            store._index_fact(fact)

        logger.info(f"Loaded {store.total_facts} granular facts from {filepath}")
        return store

    def merge_from(self, other: 'GranularFactsStore'):
        """Merge facts from another store (deduplicates by ID)."""
        for fact in other.get_all_facts():
            if fact.granular_fact_id not in self._facts:
                self._facts[fact.granular_fact_id] = fact
                self._index_fact(fact)

        self.last_updated = datetime.utcnow().isoformat()
        logger.info(f"Merged {other.total_facts} facts, now have {self.total_facts}")

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the store."""
        numeric_facts = self.get_numeric_facts()

        return {
            "total_facts": self.total_facts,
            "facts_by_domain": self.count_by_domain(),
            "facts_by_type": self.count_by_type(),
            "facts_by_system": self.count_by_system(),
            "unique_systems": len(self._by_system),
            "unique_domains": len(self._by_domain),
            "numeric_facts": len(numeric_facts),
            "validated_facts": sum(1 for f in self._facts.values() if f.validated),
            "unvalidated_facts": sum(1 for f in self._facts.values() if not f.validated),
            "facts_with_evidence": sum(1 for f in self._facts.values() if f.evidence_quote),
            "avg_confidence": sum(f.confidence for f in self._facts.values()) / max(1, self.total_facts)
        }


# =============================================================================
# TOOL FUNCTIONS (for LLM agent use)
# =============================================================================

def create_granular_fact_tool(store: GranularFactsStore):
    """
    Create a tool function for LLM agents to add granular facts.

    Returns a function that can be called with fact parameters.
    """
    def add_granular_fact(
        domain: str,
        category: str,
        fact_type: str,
        item: str,
        value: Any,
        unit: str = None,
        context: Dict = None,
        evidence_quote: str = "",
        source_document: str = "",
        source_page: int = None,
        parent_system_id: str = None,
        entity: str = "target"
    ) -> Dict[str, Any]:
        """
        Add a granular (line-item) fact to the store.

        Args:
            domain: One of infrastructure, applications, cybersecurity,
                    network, identity_access, organization
            category: Subcategory within domain
            fact_type: One of count, version, capacity, cost, date, config,
                       status, integration, location, contact, sla, license, vendor
            item: What this fact describes (e.g., "EC2 Instances")
            value: The actual value (number, string, etc.)
            unit: Optional unit (instances, users, TB, USD/month)
            context: Additional context as key-value pairs
            evidence_quote: Exact quote from source document
            source_document: Filename of source
            source_page: Page number if available
            parent_system_id: ID of parent system from System Registry
            entity: "target" or "buyer"

        Returns:
            Dictionary with fact_id and status
        """
        try:
            fact_id = store.add_fact(
                domain=domain,
                category=category,
                fact_type=fact_type,
                item=item,
                value=value,
                unit=unit,
                context=context,
                evidence_quote=evidence_quote,
                source_document=source_document,
                source_page=source_page,
                parent_system_id=parent_system_id,
                entity=entity
            )

            return {
                "status": "success",
                "fact_id": fact_id,
                "message": f"Added granular fact: {item} = {value}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    return add_granular_fact
