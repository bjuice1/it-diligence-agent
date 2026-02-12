"""
InventoryItem Dataclass

Represents a single inventory record (application, infrastructure, organization, vendor).

Key differences from Fact:
- Inventory items ARE the data (structured records from ToltIQ)
- Facts are OBSERVATIONS about unstructured content
- Inventory items are editable; facts are immutable
- Inventory items have enrichment; facts have evidence
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


def _generate_timestamp() -> str:
    """Generate ISO format timestamp."""
    return datetime.now().isoformat()


@dataclass
class InventoryItem:
    """
    A structured inventory record.

    Inventory items represent real entities from the target company:
    - Applications (software systems)
    - Infrastructure (servers, VMs, network devices)
    - Organization (teams, roles, headcount)
    - Vendors (contracts, MSAs)

    Unlike Facts (which are observations with evidence), inventory items
    ARE the canonical data - they come from structured imports like
    ToltIQ exports, Excel spreadsheets, or direct entry.
    """

    # Identity
    item_id: str                    # I-APP-a3f291 (content-hashed, stable)
    inventory_type: str             # application, infrastructure, organization, vendor
    entity: str                     # target, buyer

    # Core Data (flexible schema per type)
    # Contains: name, vendor, version, cost, etc. depending on inventory_type
    # Missing fields are None (not empty string)
    data: Dict[str, Any] = field(default_factory=dict)

    # Source Tracking
    source_file: str = ""           # Original file this came from
    source_type: str = "import"     # "import", "manual", or "discovery"

    # Deal isolation - REQUIRED for proper data separation
    deal_id: str = ""               # Deal this item belongs to - REQUIRED for new items

    # FactStore cross-references (Spec 03: bidirectional linking)
    source_fact_ids: List[str] = field(default_factory=list)  # F-TGT-APP-xxx IDs that reference this item

    # Enrichment (from Application Intelligence - Phase 3)
    # category: industry_standard, vertical_specific, niche, unknown, custom
    # note: Description of what this is
    # confidence: high, medium, low
    # flag: None, investigate, confirm, critical
    enrichment: Dict[str, Any] = field(default_factory=dict)

    # Enrichment Status (Doc 05: UI Enrichment Status)
    is_enriched: bool = False                   # Has enrichment been applied
    enrichment_confidence: str = 'none'         # none | low | medium | high
    enrichment_method: str = 'none'             # none | deterministic | llm | manual
    extraction_quality: float = 0.0             # 0.0-1.0 from parser (Doc 02)
    needs_investigation: bool = False           # Flagged for manual review
    entity_validated: bool = False              # Entity explicitly validated vs inferred

    # Status
    status: str = "active"          # active, removed, deprecated, planned
    removal_reason: str = ""        # If removed, why

    # Timestamps
    created_at: str = field(default_factory=_generate_timestamp)
    modified_at: str = ""
    modified_by: str = ""

    def __post_init__(self):
        """Validate and normalize after initialization."""
        # Ensure data is a dict
        if self.data is None:
            self.data = {}

        # Ensure enrichment is a dict
        if self.enrichment is None:
            self.enrichment = {}

        # Validate inventory_type
        valid_types = ["application", "infrastructure", "organization", "vendor"]
        if self.inventory_type not in valid_types:
            raise ValueError(
                f"Invalid inventory_type: {self.inventory_type}. "
                f"Must be one of: {valid_types}"
            )

        # Validate entity
        if self.entity not in ["target", "buyer"]:
            raise ValueError(f"Invalid entity: {self.entity}. Must be 'target' or 'buyer'")

        # Validate status
        valid_statuses = ["active", "removed", "deprecated", "planned"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of: {valid_statuses}")

        # Warn if deal_id is missing (required for proper isolation)
        if not self.deal_id:
            logger.warning(f"InventoryItem {self.item_id} created without deal_id - data isolation may be compromised")

    # ----- Convenience Properties -----

    @property
    def name(self) -> str:
        """Get the item's name (from data)."""
        # Try common name fields
        for field_name in ["name", "vendor_name", "role", "hostname"]:
            if field_name in self.data and self.data[field_name]:
                return str(self.data[field_name])
        return "Unknown"

    @property
    def display_name(self) -> str:
        """Get a display-friendly name."""
        name = self.name
        vendor = self.data.get("vendor", "")
        if vendor and vendor.lower() != name.lower():
            return f"{name} ({vendor})"
        return name

    @property
    def cost(self) -> Optional[float]:
        """Get cost if available, as float."""
        raw_cost = self.data.get("cost")
        if raw_cost is None:
            return None
        if isinstance(raw_cost, (int, float)):
            return float(raw_cost)
        # Try to parse string cost
        try:
            # Remove currency symbols and commas
            cleaned = str(raw_cost).replace("$", "").replace(",", "").strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @property
    def criticality(self) -> Optional[str]:
        """Get criticality if available."""
        return self.data.get("criticality")

    @property
    def is_enriched(self) -> bool:
        """Check if item has been enriched."""
        return bool(self.enrichment and self.enrichment.get("category"))

    @property
    def enrichment_category(self) -> Optional[str]:
        """Get enrichment category if available."""
        return self.enrichment.get("category")

    @property
    def needs_investigation(self) -> bool:
        """Check if item is flagged for investigation."""
        return self.enrichment.get("flag") == "investigate"

    @property
    def is_active(self) -> bool:
        """Check if item is active (not removed)."""
        return self.status == "active"

    # ----- Methods -----

    def update(self, updates: Dict[str, Any], modified_by: str = "") -> None:
        """
        Update item data.

        Args:
            updates: Dict of field updates to apply to data
            modified_by: Who made this modification
        """
        self.data.update(updates)
        self.modified_at = _generate_timestamp()
        self.modified_by = modified_by

    def set_enrichment(
        self,
        category: str,
        note: str = "",
        confidence: str = "medium",
        flag: Optional[str] = None
    ) -> None:
        """
        Set enrichment data (from Application Intelligence).

        Args:
            category: industry_standard, vertical_specific, niche, unknown, custom
            note: Description/explanation
            confidence: high, medium, low
            flag: None, investigate, confirm, critical
        """
        valid_categories = [
            "industry_standard", "vertical_specific", "niche", "unknown", "custom"
        ]
        if category not in valid_categories:
            raise ValueError(f"Invalid category: {category}")

        self.enrichment = {
            "category": category,
            "note": note,
            "confidence": confidence,
            "flag": flag,
        }
        self.modified_at = _generate_timestamp()

    def remove(self, reason: str, removed_by: str = "") -> None:
        """
        Mark item as removed.

        Args:
            reason: Why the item was removed
            removed_by: Who removed it
        """
        self.status = "removed"
        self.removal_reason = reason
        self.modified_at = _generate_timestamp()
        self.modified_by = removed_by

    def restore(self) -> None:
        """Restore a removed item to active status."""
        self.status = "active"
        self.removal_reason = ""
        self.modified_at = _generate_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InventoryItem":
        """
        Create InventoryItem from dictionary.

        Handles backwards compatibility for missing fields.
        """
        # Make a copy to avoid modifying input
        data = dict(data)

        # Set defaults for optional fields
        if "deal_id" not in data:
            data["deal_id"] = ""  # Legacy items without deal_id
        # Spec 03: bidirectional linking (backwards compatibility)
        if "source_fact_ids" not in data:
            data["source_fact_ids"] = []  # Legacy items without fact links
        if "enrichment" not in data:
            data["enrichment"] = {}
        if "status" not in data:
            data["status"] = "active"
        if "removal_reason" not in data:
            data["removal_reason"] = ""
        if "source_type" not in data:
            data["source_type"] = "import"
        if "modified_at" not in data:
            data["modified_at"] = ""
        if "modified_by" not in data:
            data["modified_by"] = ""

        return cls(**data)

    def __str__(self) -> str:
        """String representation."""
        return f"InventoryItem({self.item_id}: {self.display_name})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"InventoryItem(item_id={self.item_id!r}, "
            f"type={self.inventory_type!r}, "
            f"name={self.name!r}, "
            f"status={self.status!r})"
        )


@dataclass
class MergeResult:
    """
    Result of merging inventory data.

    Tracks what happened during a merge/re-import operation.
    """
    added: int = 0                  # New items added
    updated: int = 0                # Existing items updated
    unchanged: int = 0              # Items with no changes
    flagged_removed: int = 0        # Items flagged as removed from source
    skipped: int = 0                # Items skipped (already removed, etc.)
    errors: List[str] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        """Total items processed."""
        return self.added + self.updated + self.unchanged + self.flagged_removed + self.skipped

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def __str__(self) -> str:
        """Summary string."""
        return (
            f"MergeResult: {self.added} added, {self.updated} updated, "
            f"{self.unchanged} unchanged, {self.flagged_removed} removed, "
            f"{self.skipped} skipped, {len(self.errors)} errors"
        )


# =============================================================================
# DATA QUALITY HELPERS (Doc 05: UI Enrichment Status)
# =============================================================================

def calculate_data_quality_score(item: InventoryItem) -> float:
    """
    Calculate overall data quality score (0.0-1.0).

    Factors:
    - Extraction quality (from parser)
    - Enrichment confidence
    - Field completeness
    - Entity validation

    Args:
        item: InventoryItem to evaluate

    Returns:
        Quality score 0.0-1.0 (higher is better)
    """
    # Extraction quality (0.0-1.0) from parser
    extraction_score = item.extraction_quality

    # Enrichment confidence
    enrichment_scores = {
        'none': 0.0,
        'low': 0.5,
        'medium': 0.75,
        'high': 1.0
    }
    enrichment_score = enrichment_scores.get(item.enrichment_confidence, 0.0)

    # Field completeness (% of expected fields filled)
    # For applications: name, category, vendor, users
    if item.inventory_type == 'application':
        expected_fields = ['name', 'category', 'vendor', 'users']
    elif item.inventory_type == 'infrastructure':
        expected_fields = ['name', 'type', 'os', 'environment']
    elif item.inventory_type == 'organization':
        expected_fields = ['role', 'department', 'headcount']
    else:  # vendor
        expected_fields = ['vendor_name', 'contract_type']

    filled = sum(1 for f in expected_fields if item.data.get(f))
    completeness_score = filled / len(expected_fields) if expected_fields else 0.0

    # Entity validation (explicit vs inferred)
    entity_score = 1.0 if item.entity_validated else 0.7

    # Weighted average
    quality = (
        extraction_score * 0.3 +
        enrichment_score * 0.4 +
        completeness_score * 0.2 +
        entity_score * 0.1
    )

    return quality


def quality_class(quality_score: float) -> str:
    """
    Get CSS class name for quality score.

    Args:
        quality_score: Quality score 0.0-1.0

    Returns:
        'high' | 'medium' | 'low'
    """
    if quality_score >= 0.8:
        return 'high'
    elif quality_score >= 0.5:
        return 'medium'
    else:
        return 'low'
