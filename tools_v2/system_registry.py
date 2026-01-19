"""
System Registry - Pass 1 System Catalog

This module provides storage and management for systems discovered
during Pass 1 of the multi-pass extraction process.

A "system" is any platform, technology, or major component:
- AWS Cloud Platform
- NetSuite ERP
- Salesforce CRM
- Dallas Data Center
- Cisco Network Infrastructure

Systems serve as parent entities for granular facts extracted in Pass 2.
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM CATEGORIES
# =============================================================================

SYSTEM_CATEGORIES = {
    "cloud_platform": "Cloud infrastructure providers (AWS, Azure, GCP)",
    "erp": "Enterprise Resource Planning systems",
    "crm": "Customer Relationship Management systems",
    "hris": "Human Resources Information Systems",
    "data_center": "Physical data center facilities",
    "network_infrastructure": "Core network equipment and services",
    "security_platform": "Security tools and platforms",
    "database_platform": "Database management systems",
    "application_platform": "Application servers and platforms",
    "collaboration": "Email, messaging, productivity tools",
    "dev_platform": "Development and CI/CD platforms",
    "analytics": "BI and analytics platforms",
    "storage": "Storage systems and platforms",
    "backup_dr": "Backup and disaster recovery systems",
    "identity": "Identity and access management",
    "monitoring": "Monitoring and observability",
    "vendor_service": "Third-party managed services",
    "legacy": "Legacy or mainframe systems",
    "other": "Uncategorized systems"
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class System:
    """
    A system, platform, or major technology component.

    Example:
        System(
            system_id="SYS-a3f2",
            name="AWS Cloud Platform",
            vendor="Amazon Web Services",
            category="cloud_platform",
            domain="infrastructure",
            description="Primary cloud infrastructure provider",
            status="active",
            criticality="high",
            evidence_quotes=["The company operates primarily on AWS..."],
            source_documents=["IT Overview.pdf"],
            first_mentioned_page=3
        )
    """
    system_id: str
    name: str
    vendor: Optional[str] = None
    category: str = "other"
    domain: str = "infrastructure"
    description: str = ""
    status: str = "active"  # active, deprecated, planned, unknown
    criticality: str = "medium"  # low, medium, high, critical
    entity: str = "target"  # target or buyer

    # Evidence tracking
    evidence_quotes: List[str] = field(default_factory=list)
    source_documents: List[str] = field(default_factory=list)
    first_mentioned_page: Optional[int] = None

    # Relationships
    parent_system_id: Optional[str] = None  # For subsystems
    related_systems: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Pass 2 tracking
    detail_extraction_complete: bool = False
    granular_fact_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'System':
        """Create from dictionary."""
        # Handle missing fields gracefully
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def to_row(self) -> Dict[str, Any]:
        """Convert to flat row for Excel/CSV export."""
        return {
            "ID": self.system_id,
            "Name": self.name,
            "Vendor": self.vendor or "",
            "Category": self.category,
            "Domain": self.domain,
            "Description": self.description,
            "Status": self.status,
            "Criticality": self.criticality,
            "Entity": self.entity,
            "Source Documents": ", ".join(self.source_documents),
            "First Page": self.first_mentioned_page or "",
            "Integrations": ", ".join(self.integrations),
            "Tags": ", ".join(self.tags),
            "Granular Facts": self.granular_fact_count,
            "Detail Complete": "Yes" if self.detail_extraction_complete else "No"
        }

    def add_evidence(self, quote: str, source_doc: str, page: Optional[int] = None):
        """Add evidence quote and source."""
        if quote and quote not in self.evidence_quotes:
            self.evidence_quotes.append(quote)
        if source_doc and source_doc not in self.source_documents:
            self.source_documents.append(source_doc)
        if page and not self.first_mentioned_page:
            self.first_mentioned_page = page
        self.updated_at = datetime.utcnow().isoformat()


# =============================================================================
# SYSTEM REGISTRY
# =============================================================================

class SystemRegistry:
    """
    Registry of all systems discovered in Pass 1.

    Features:
    - Hash-based IDs for deduplication
    - Category and domain organization
    - Relationship tracking
    - Integration with granular facts store
    """

    def __init__(self):
        self._systems: Dict[str, System] = {}
        self._by_category: Dict[str, List[str]] = {}
        self._by_domain: Dict[str, List[str]] = {}
        self._by_vendor: Dict[str, List[str]] = {}
        self._name_to_id: Dict[str, str] = {}  # For quick lookup by name
        self.created_at: str = datetime.utcnow().isoformat()
        self.last_updated: str = self.created_at

    def _generate_system_id(self, name: str, vendor: Optional[str] = None) -> str:
        """Generate stable, deterministic system ID from content."""
        content = f"{name}|{vendor or ''}".lower().strip()
        hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()[:6]
        return f"SYS-{hash_value}"

    def _normalize_name(self, name: str) -> str:
        """Normalize system name for matching."""
        return name.lower().strip()

    def add_system(
        self,
        name: str,
        vendor: Optional[str] = None,
        category: str = "other",
        domain: str = "infrastructure",
        description: str = "",
        status: str = "active",
        criticality: str = "medium",
        evidence_quote: str = "",
        source_document: str = "",
        source_page: Optional[int] = None,
        entity: str = "target",
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Add or update a system in the registry.

        Returns:
            The system ID (existing if duplicate, new if unique)
        """
        # Generate stable ID
        system_id = self._generate_system_id(name, vendor)
        normalized_name = self._normalize_name(name)

        # Check for existing system
        if system_id in self._systems:
            # Update existing system with new evidence
            existing = self._systems[system_id]
            if evidence_quote:
                existing.add_evidence(evidence_quote, source_document, source_page)
            if description and not existing.description:
                existing.description = description
            if tags:
                existing.tags = list(set(existing.tags + tags))
            logger.debug(f"Updated existing system: {system_id} - {name}")
            return system_id

        # Create new system
        system = System(
            system_id=system_id,
            name=name,
            vendor=vendor,
            category=category,
            domain=domain,
            description=description,
            status=status,
            criticality=criticality,
            entity=entity,
            evidence_quotes=[evidence_quote] if evidence_quote else [],
            source_documents=[source_document] if source_document else [],
            first_mentioned_page=source_page,
            tags=tags or []
        )

        # Store and index
        self._systems[system_id] = system
        self._name_to_id[normalized_name] = system_id
        self._index_system(system)
        self.last_updated = datetime.utcnow().isoformat()

        logger.info(f"Added system: {system_id} - {name}")
        return system_id

    def _index_system(self, system: System):
        """Add system to indices for fast lookup."""
        # Index by category
        if system.category not in self._by_category:
            self._by_category[system.category] = []
        self._by_category[system.category].append(system.system_id)

        # Index by domain
        if system.domain not in self._by_domain:
            self._by_domain[system.domain] = []
        self._by_domain[system.domain].append(system.system_id)

        # Index by vendor
        if system.vendor:
            vendor_key = system.vendor.lower()
            if vendor_key not in self._by_vendor:
                self._by_vendor[vendor_key] = []
            self._by_vendor[vendor_key].append(system.system_id)

    def get_system(self, system_id: str) -> Optional[System]:
        """Get a system by ID."""
        return self._systems.get(system_id)

    def get_system_by_name(self, name: str) -> Optional[System]:
        """Get a system by name (fuzzy match)."""
        normalized = self._normalize_name(name)

        # Exact match
        if normalized in self._name_to_id:
            return self._systems.get(self._name_to_id[normalized])

        # Partial match
        for sys_name, sys_id in self._name_to_id.items():
            if normalized in sys_name or sys_name in normalized:
                return self._systems.get(sys_id)

        return None

    def find_system_id(self, name: str) -> Optional[str]:
        """Find system ID by name."""
        system = self.get_system_by_name(name)
        return system.system_id if system else None

    def get_all_systems(self) -> List[System]:
        """Get all systems."""
        return list(self._systems.values())

    def get_systems_by_category(self, category: str) -> List[System]:
        """Get all systems in a category."""
        system_ids = self._by_category.get(category, [])
        return [self._systems[sid] for sid in system_ids if sid in self._systems]

    def get_systems_by_domain(self, domain: str) -> List[System]:
        """Get all systems in a domain."""
        system_ids = self._by_domain.get(domain, [])
        return [self._systems[sid] for sid in system_ids if sid in self._systems]

    def get_systems_by_vendor(self, vendor: str) -> List[System]:
        """Get all systems from a vendor."""
        vendor_key = vendor.lower()
        system_ids = self._by_vendor.get(vendor_key, [])
        return [self._systems[sid] for sid in system_ids if sid in self._systems]

    def get_systems_needing_details(self) -> List[System]:
        """Get systems that haven't completed Pass 2 detail extraction."""
        return [s for s in self._systems.values()
                if not s.detail_extraction_complete]

    def mark_detail_complete(self, system_id: str, fact_count: int):
        """Mark a system as having completed detail extraction."""
        if system_id in self._systems:
            self._systems[system_id].detail_extraction_complete = True
            self._systems[system_id].granular_fact_count = fact_count
            self._systems[system_id].updated_at = datetime.utcnow().isoformat()

    def add_integration(self, system_id: str, target_system_id: str):
        """Record an integration between two systems."""
        if system_id in self._systems and target_system_id in self._systems:
            source = self._systems[system_id]
            target = self._systems[target_system_id]

            if target_system_id not in source.integrations:
                source.integrations.append(target_system_id)
            if system_id not in target.integrations:
                target.integrations.append(system_id)

    @property
    def total_systems(self) -> int:
        """Total number of systems."""
        return len(self._systems)

    @property
    def categories(self) -> List[str]:
        """List of categories with systems."""
        return list(self._by_category.keys())

    @property
    def domains(self) -> List[str]:
        """List of domains with systems."""
        return list(self._by_domain.keys())

    @property
    def vendors(self) -> List[str]:
        """List of vendors."""
        return list(self._by_vendor.keys())

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def to_rows(self) -> List[Dict[str, Any]]:
        """Convert systems to flat rows for Excel/CSV export."""
        return [s.to_row() for s in self._systems.values()]

    def to_json(self) -> str:
        """Export all systems as JSON string."""
        data = {
            "metadata": {
                "total_systems": self.total_systems,
                "categories": self.categories,
                "domains": self.domains,
                "created_at": self.created_at,
                "last_updated": self.last_updated
            },
            "systems": [s.to_dict() for s in self._systems.values()]
        }
        return json.dumps(data, indent=2, default=str)

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def save(self, filepath: Path):
        """Save registry to JSON file."""
        data = {
            "metadata": {
                "total_systems": self.total_systems,
                "created_at": self.created_at,
                "last_updated": self.last_updated
            },
            "systems": [s.to_dict() for s in self._systems.values()]
        }

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved {self.total_systems} systems to {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> 'SystemRegistry':
        """Load registry from JSON file."""
        registry = cls()

        filepath = Path(filepath)
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return registry

        with open(filepath, 'r') as f:
            data = json.load(f)

        registry.created_at = data.get("metadata", {}).get("created_at", registry.created_at)
        registry.last_updated = data.get("metadata", {}).get("last_updated", registry.last_updated)

        for system_data in data.get("systems", []):
            system = System.from_dict(system_data)
            registry._systems[system.system_id] = system
            registry._name_to_id[registry._normalize_name(system.name)] = system.system_id
            registry._index_system(system)

        logger.info(f"Loaded {registry.total_systems} systems from {filepath}")
        return registry

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the registry."""
        systems = self.get_all_systems()

        return {
            "total_systems": self.total_systems,
            "systems_by_category": {cat: len(ids) for cat, ids in self._by_category.items()},
            "systems_by_domain": {dom: len(ids) for dom, ids in self._by_domain.items()},
            "systems_by_status": self._count_by_field("status"),
            "systems_by_criticality": self._count_by_field("criticality"),
            "unique_vendors": len(self._by_vendor),
            "systems_with_integrations": sum(1 for s in systems if s.integrations),
            "total_integrations": sum(len(s.integrations) for s in systems) // 2,
            "detail_complete": sum(1 for s in systems if s.detail_extraction_complete),
            "detail_pending": sum(1 for s in systems if not s.detail_extraction_complete),
            "total_granular_facts": sum(s.granular_fact_count for s in systems)
        }

    def _count_by_field(self, field: str) -> Dict[str, int]:
        """Count systems by a specific field value."""
        counts = {}
        for system in self._systems.values():
            value = getattr(system, field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts


# =============================================================================
# TOOL FUNCTIONS (for LLM agent use)
# =============================================================================

def create_register_system_tool(registry: SystemRegistry):
    """
    Create a tool function for LLM agents to register systems.

    Returns a function that can be called with system parameters.
    """
    def register_system(
        name: str,
        vendor: str = None,
        category: str = "other",
        domain: str = "infrastructure",
        description: str = "",
        status: str = "active",
        criticality: str = "medium",
        evidence_quote: str = "",
        source_document: str = "",
        source_page: int = None,
        entity: str = "target",
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Register a system in the System Registry.

        Args:
            name: System name (e.g., "AWS Cloud Platform", "NetSuite ERP")
            vendor: Vendor name (e.g., "Amazon Web Services", "Oracle")
            category: One of: cloud_platform, erp, crm, hris, data_center,
                      network_infrastructure, security_platform, database_platform,
                      application_platform, collaboration, dev_platform, analytics,
                      storage, backup_dr, identity, monitoring, vendor_service,
                      legacy, other
            domain: One of: infrastructure, applications, cybersecurity,
                    network, identity_access, organization
            description: Brief description of the system
            status: One of: active, deprecated, planned, unknown
            criticality: One of: low, medium, high, critical
            evidence_quote: Exact quote from source document
            source_document: Filename of source
            source_page: Page number if available
            entity: "target" or "buyer"
            tags: Optional list of tags

        Returns:
            Dictionary with system_id and status
        """
        try:
            system_id = registry.add_system(
                name=name,
                vendor=vendor,
                category=category,
                domain=domain,
                description=description,
                status=status,
                criticality=criticality,
                evidence_quote=evidence_quote,
                source_document=source_document,
                source_page=source_page,
                entity=entity,
                tags=tags
            )

            return {
                "status": "success",
                "system_id": system_id,
                "message": f"Registered system: {name}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    return register_system
