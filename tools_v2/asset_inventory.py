"""
Asset Inventory Module (Enhancement Plan Points 1-11)

Structured asset tracking for infrastructure due diligence.
Includes EOL tracking, categorization, and refresh flagging.

This module complements the FactStore by providing a more structured
view of infrastructure assets beyond free-form facts.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, date
from enum import Enum
import logging
import threading
import json

logger = logging.getLogger(__name__)


# =============================================================================
# ASSET TYPES AND CATEGORIES (Point 3)
# =============================================================================

class AssetType(Enum):
    """Primary asset type classification."""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    SECURITY = "security"
    ENDPOINT = "endpoint"
    CLOUD = "cloud"
    SOFTWARE = "software"
    OTHER = "other"


class AssetCategory(Enum):
    """Detailed asset categories within each type."""
    # Compute
    PHYSICAL_SERVER = "physical_server"
    VIRTUAL_SERVER = "virtual_server"
    MAINFRAME = "mainframe"
    CONTAINER_HOST = "container_host"
    HPC_CLUSTER = "hpc_cluster"

    # Storage
    SAN = "san"
    NAS = "nas"
    OBJECT_STORAGE = "object_storage"
    BACKUP_APPLIANCE = "backup_appliance"
    TAPE_LIBRARY = "tape_library"

    # Network
    ROUTER = "router"
    SWITCH = "switch"
    LOAD_BALANCER = "load_balancer"
    WAN_OPTIMIZER = "wan_optimizer"
    WIRELESS_CONTROLLER = "wireless_controller"
    WIRELESS_AP = "wireless_ap"

    # Security
    FIREWALL = "firewall"
    IDS_IPS = "ids_ips"
    WAF = "waf"
    VPN_CONCENTRATOR = "vpn_concentrator"
    PROXY = "proxy"
    HSM = "hsm"

    # Endpoint
    DESKTOP = "desktop"
    LAPTOP = "laptop"
    THIN_CLIENT = "thin_client"
    MOBILE_DEVICE = "mobile_device"
    PRINTER = "printer"

    # Cloud
    IAAS_INSTANCE = "iaas_instance"
    PAAS_SERVICE = "paas_service"
    SAAS_SUBSCRIPTION = "saas_subscription"
    CLOUD_STORAGE = "cloud_storage"

    # Software
    OPERATING_SYSTEM = "operating_system"
    DATABASE = "database"
    MIDDLEWARE = "middleware"
    HYPERVISOR = "hypervisor"

    OTHER = "other"


class OwnershipType(Enum):
    """Asset ownership classification."""
    TARGET = "target"           # Owned by target company
    BUYER = "buyer"             # Owned by buyer
    SHARED = "shared"           # Shared between target and parent
    THIRD_PARTY = "third_party" # Managed by third party/MSP
    LEASED = "leased"           # Leased equipment
    UNKNOWN = "unknown"


class EOLStatus(Enum):
    """End-of-Life status classification."""
    CURRENT = "current"           # Fully supported
    APPROACHING = "approaching"   # EOL within 12 months
    EXTENDED = "extended"         # Past EOL but on extended support
    PAST_EOL = "past_eol"        # Past EOL, no support
    UNKNOWN = "unknown"           # EOL status not determined


class RefreshReason(Enum):
    """Reasons for flagging an asset for refresh consideration."""
    EOL = "eol"                       # End of life
    PERFORMANCE = "performance"        # Performance limitations
    SECURITY = "security"              # Security vulnerabilities
    CAPACITY = "capacity"              # Capacity constraints
    COMPATIBILITY = "compatibility"    # Compatibility issues
    COST = "cost"                      # High maintenance costs
    STANDARDIZATION = "standardization" # Non-standard platform
    NONE = "none"                      # No refresh needed


# =============================================================================
# EOL DATABASE (Point 7)
# =============================================================================

# Common vendor EOL dates - this should be expanded/externalized
# Format: (vendor, product_family, version) -> (eol_date, eos_date)
EOL_DATABASE = {
    # VMware
    ("vmware", "vsphere", "6.5"): {"eol": "2022-10-15", "eos": "2023-11-15"},
    ("vmware", "vsphere", "6.7"): {"eol": "2022-10-15", "eos": "2023-11-15"},
    ("vmware", "vsphere", "7.0"): {"eol": "2025-04-02", "eos": "2027-04-02"},
    ("vmware", "vsphere", "8.0"): {"eol": "2027-10-01", "eos": "2029-10-01"},

    # Windows Server
    ("microsoft", "windows_server", "2012"): {"eol": "2018-10-09", "eos": "2023-10-10"},
    ("microsoft", "windows_server", "2012_r2"): {"eol": "2018-10-09", "eos": "2023-10-10"},
    ("microsoft", "windows_server", "2016"): {"eol": "2022-01-11", "eos": "2027-01-12"},
    ("microsoft", "windows_server", "2019"): {"eol": "2024-01-09", "eos": "2029-01-09"},
    ("microsoft", "windows_server", "2022"): {"eol": "2026-10-13", "eos": "2031-10-14"},

    # SQL Server
    ("microsoft", "sql_server", "2012"): {"eol": "2017-07-11", "eos": "2022-07-12"},
    ("microsoft", "sql_server", "2014"): {"eol": "2019-07-09", "eos": "2024-07-09"},
    ("microsoft", "sql_server", "2016"): {"eol": "2021-07-13", "eos": "2026-07-14"},
    ("microsoft", "sql_server", "2017"): {"eol": "2022-10-11", "eos": "2027-10-12"},
    ("microsoft", "sql_server", "2019"): {"eol": "2025-01-07", "eos": "2030-01-08"},

    # Cisco Switches (examples)
    ("cisco", "catalyst", "3750"): {"eol": "2016-07-31", "eos": "2021-07-31"},
    ("cisco", "catalyst", "3850"): {"eol": "2022-04-30", "eos": "2027-04-30"},
    ("cisco", "catalyst", "9300"): {"eol": "2028-01-01", "eos": "2033-01-01"},

    # Cisco Firewalls
    ("cisco", "asa", "5505"): {"eol": "2017-09-02", "eos": "2022-09-02"},
    ("cisco", "asa", "5515"): {"eol": "2019-09-02", "eos": "2024-09-02"},
    ("cisco", "asa", "5525"): {"eol": "2020-09-02", "eos": "2025-09-02"},

    # Palo Alto
    ("paloalto", "pa", "3000"): {"eol": "2022-03-01", "eos": "2025-03-01"},
    ("paloalto", "pa", "5000"): {"eol": "2023-07-01", "eos": "2026-07-01"},

    # Fortinet
    ("fortinet", "fortigate", "60e"): {"eol": "2024-01-01", "eos": "2029-01-01"},
    ("fortinet", "fortigate", "100e"): {"eol": "2024-06-01", "eos": "2029-06-01"},

    # Red Hat
    ("redhat", "rhel", "7"): {"eol": "2024-06-30", "eos": "2026-06-30"},
    ("redhat", "rhel", "8"): {"eol": "2029-05-31", "eos": "2031-05-31"},
    ("redhat", "rhel", "9"): {"eol": "2032-05-31", "eos": "2034-05-31"},

    # Oracle Database
    ("oracle", "database", "12c"): {"eol": "2022-03-01", "eos": "2025-03-01"},
    ("oracle", "database", "19c"): {"eol": "2027-04-01", "eos": "2030-04-01"},
}


def _generate_timestamp() -> str:
    """Generate ISO format timestamp."""
    return datetime.now().isoformat()


# =============================================================================
# ASSET DATA MODEL (Point 1)
# =============================================================================

@dataclass
class Asset:
    """
    A single infrastructure asset with structured tracking.

    Provides more structured data than a generic Fact for
    infrastructure inventory purposes.
    """
    asset_id: str                                 # A-INFRA-001
    asset_type: str                               # compute, storage, network, etc.
    category: str                                 # physical_server, firewall, etc.
    name: str                                     # Asset name/identifier
    vendor: str = ""                              # Dell, Cisco, VMware, etc.
    model: str = ""                               # Specific model
    version: str = ""                             # Version/firmware
    quantity: int = 1                             # Count of this asset
    location: str = ""                            # Data center, site, cloud region
    owner: str = "target"                         # target, buyer, shared, third_party

    # EOL Tracking (Points 7-10)
    eol_date: str = ""                            # End of Life date (YYYY-MM-DD)
    eos_date: str = ""                            # End of Support date
    eol_status: str = "unknown"                   # current, approaching, past_eol

    # Refresh Considerations (Point 11)
    refresh_flag: bool = False                    # Needs refresh consideration
    refresh_reason: str = "none"                  # EOL, performance, security, etc.
    refresh_notes: str = ""                       # Additional context

    # Source tracking
    source_fact_ids: List[str] = field(default_factory=list)  # Related fact IDs
    source_document: str = ""                     # Source document
    evidence_quote: str = ""                      # Supporting quote

    # Metadata
    created_at: str = field(default_factory=_generate_timestamp)
    updated_at: str = ""
    confidence: float = 0.0                       # 0.0-1.0 confidence in data
    notes: str = ""                               # Additional notes

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Asset":
        return cls(**data)

    def check_eol_status(self) -> str:
        """
        Check and update EOL status based on current date (Point 8).
        """
        if not self.eol_date:
            return EOLStatus.UNKNOWN.value

        try:
            eol = datetime.strptime(self.eol_date, "%Y-%m-%d").date()
            today = date.today()
            months_until_eol = (eol.year - today.year) * 12 + (eol.month - today.month)

            if today > eol:
                # Check if on extended support
                if self.eos_date:
                    eos = datetime.strptime(self.eos_date, "%Y-%m-%d").date()
                    if today <= eos:
                        self.eol_status = EOLStatus.EXTENDED.value
                    else:
                        self.eol_status = EOLStatus.PAST_EOL.value
                else:
                    self.eol_status = EOLStatus.PAST_EOL.value
            elif months_until_eol <= 12:
                self.eol_status = EOLStatus.APPROACHING.value
            else:
                self.eol_status = EOLStatus.CURRENT.value

            return self.eol_status

        except ValueError:
            return EOLStatus.UNKNOWN.value

    def flag_for_refresh(self, reason: str, notes: str = "") -> None:
        """Flag this asset for refresh consideration (Point 11)."""
        self.refresh_flag = True
        self.refresh_reason = reason
        self.refresh_notes = notes
        self.updated_at = _generate_timestamp()


# =============================================================================
# ASSET INVENTORY STORE (Points 1-6)
# =============================================================================

class AssetInventory:
    """
    Central store for structured infrastructure assets.

    Complements FactStore with structured asset tracking:
    - Asset categorization (Point 3)
    - EOL tracking (Points 7-10)
    - Refresh flagging (Point 11)
    - Location and ownership mapping (Points 5-6)
    """

    def __init__(self):
        self.assets: List[Asset] = []
        self._counters: Dict[str, int] = {}
        self._index: Dict[str, Asset] = {}
        self._lock = threading.RLock()
        self.metadata: Dict[str, Any] = {
            "created_at": _generate_timestamp(),
            "version": "1.0"
        }

    def _generate_asset_id(self, asset_type: str) -> str:
        """Generate unique asset ID."""
        prefix_map = {
            "compute": "COMP",
            "storage": "STOR",
            "network": "NET",
            "security": "SEC",
            "endpoint": "END",
            "cloud": "CLD",
            "software": "SW",
            "other": "OTH"
        }
        prefix = prefix_map.get(asset_type, "OTH")

        with self._lock:
            if prefix not in self._counters:
                self._counters[prefix] = 0
            self._counters[prefix] += 1
            return f"A-{prefix}-{self._counters[prefix]:03d}"

    def add_asset(
        self,
        asset_type: str,
        category: str,
        name: str,
        vendor: str = "",
        model: str = "",
        version: str = "",
        quantity: int = 1,
        location: str = "",
        owner: str = "target",
        source_fact_ids: List[str] = None,
        source_document: str = "",
        evidence_quote: str = "",
        notes: str = ""
    ) -> str:
        """
        Add an asset to the inventory (Point 2).

        Returns the generated asset ID.
        """
        with self._lock:
            asset_id = self._generate_asset_id(asset_type)

            asset = Asset(
                asset_id=asset_id,
                asset_type=asset_type,
                category=category,
                name=name,
                vendor=vendor,
                model=model,
                version=version,
                quantity=quantity,
                location=location,
                owner=owner,
                source_fact_ids=source_fact_ids or [],
                source_document=source_document,
                evidence_quote=evidence_quote,
                notes=notes
            )

            # Look up EOL information
            self._populate_eol_data(asset)

            # Check EOL status
            asset.check_eol_status()

            # Auto-flag for refresh if past EOL
            if asset.eol_status in (EOLStatus.PAST_EOL.value, EOLStatus.EXTENDED.value):
                asset.flag_for_refresh(RefreshReason.EOL.value, f"EOL: {asset.eol_date}")

            self.assets.append(asset)
            self._index[asset_id] = asset

            logger.debug(f"Added asset {asset_id}: {name}")
            return asset_id

    def _populate_eol_data(self, asset: Asset) -> None:
        """Look up and populate EOL data from database (Point 7)."""
        if not asset.vendor or not asset.model:
            return

        # Normalize for lookup
        vendor_key = asset.vendor.lower().replace(" ", "_")
        # Try to extract product family from model
        model_parts = asset.model.lower().replace("-", " ").split()

        # Try various combinations
        for product_family in model_parts:
            for version in [asset.version, model_parts[-1] if model_parts else ""]:
                key = (vendor_key, product_family, version)
                if key in EOL_DATABASE:
                    eol_data = EOL_DATABASE[key]
                    asset.eol_date = eol_data.get("eol", "")
                    asset.eos_date = eol_data.get("eos", "")
                    logger.debug(f"Found EOL data for {asset.name}: EOL={asset.eol_date}")
                    return

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Get asset by ID."""
        with self._lock:
            return self._index.get(asset_id)

    def get_assets_by_type(self, asset_type: str) -> List[Asset]:
        """Get all assets of a specific type (Point 3)."""
        with self._lock:
            return [a for a in self.assets if a.asset_type == asset_type]

    def get_assets_by_category(self, category: str) -> List[Asset]:
        """Get all assets of a specific category."""
        with self._lock:
            return [a for a in self.assets if a.category == category]

    def get_assets_by_location(self, location: str) -> List[Asset]:
        """Get all assets at a specific location (Point 5)."""
        with self._lock:
            return [a for a in self.assets if a.location == location]

    def get_assets_by_owner(self, owner: str) -> List[Asset]:
        """Get all assets with specific ownership (Point 6)."""
        with self._lock:
            return [a for a in self.assets if a.owner == owner]

    def get_assets_by_vendor(self, vendor: str) -> List[Asset]:
        """Get all assets from a specific vendor."""
        with self._lock:
            vendor_lower = vendor.lower()
            return [a for a in self.assets if a.vendor.lower() == vendor_lower]

    # =========================================================================
    # EOL TRACKING (Points 7-10)
    # =========================================================================

    def get_eol_assets(self, status: str = None) -> List[Asset]:
        """
        Get assets by EOL status (Point 8).

        Args:
            status: Filter by status (current, approaching, extended, past_eol)
                   If None, returns all non-current assets.
        """
        with self._lock:
            if status:
                return [a for a in self.assets if a.eol_status == status]
            else:
                return [a for a in self.assets if a.eol_status != EOLStatus.CURRENT.value]

    def get_eol_timeline(self) -> Dict[str, List[Dict]]:
        """
        Generate EOL timeline visualization data (Point 10).

        Returns assets grouped by EOL timeframe.
        """
        with self._lock:
            today = date.today()
            timeline = {
                "past_eol": [],
                "0_to_6_months": [],
                "6_to_12_months": [],
                "12_to_18_months": [],
                "18_to_24_months": [],
                "beyond_24_months": [],
                "unknown": []
            }

            for asset in self.assets:
                if not asset.eol_date:
                    timeline["unknown"].append(asset.to_dict())
                    continue

                try:
                    eol = datetime.strptime(asset.eol_date, "%Y-%m-%d").date()
                    months_until = (eol.year - today.year) * 12 + (eol.month - today.month)

                    if months_until < 0:
                        timeline["past_eol"].append(asset.to_dict())
                    elif months_until <= 6:
                        timeline["0_to_6_months"].append(asset.to_dict())
                    elif months_until <= 12:
                        timeline["6_to_12_months"].append(asset.to_dict())
                    elif months_until <= 18:
                        timeline["12_to_18_months"].append(asset.to_dict())
                    elif months_until <= 24:
                        timeline["18_to_24_months"].append(asset.to_dict())
                    else:
                        timeline["beyond_24_months"].append(asset.to_dict())

                except ValueError:
                    timeline["unknown"].append(asset.to_dict())

            return timeline

    def get_eol_summary(self) -> Dict[str, Any]:
        """Get summary of EOL status across all assets (Point 9)."""
        with self._lock:
            summary = {
                "total_assets": len(self.assets),
                "by_status": {},
                "past_eol_count": 0,
                "approaching_eol_count": 0,
                "critical_refresh_needed": 0
            }

            for status in EOLStatus:
                count = sum(1 for a in self.assets if a.eol_status == status.value)
                summary["by_status"][status.value] = count

            summary["past_eol_count"] = summary["by_status"].get(EOLStatus.PAST_EOL.value, 0)
            summary["approaching_eol_count"] = summary["by_status"].get(EOLStatus.APPROACHING.value, 0)
            summary["critical_refresh_needed"] = (
                summary["past_eol_count"] + summary["approaching_eol_count"]
            )

            return summary

    # =========================================================================
    # REFRESH TRACKING (Point 11)
    # =========================================================================

    def get_refresh_candidates(self) -> List[Asset]:
        """Get all assets flagged for refresh consideration (Point 11)."""
        with self._lock:
            return [a for a in self.assets if a.refresh_flag]

    def get_refresh_by_reason(self) -> Dict[str, List[Dict]]:
        """Get refresh candidates grouped by reason."""
        with self._lock:
            by_reason = {}
            for asset in self.assets:
                if asset.refresh_flag:
                    reason = asset.refresh_reason
                    if reason not in by_reason:
                        by_reason[reason] = []
                    by_reason[reason].append(asset.to_dict())
            return by_reason

    def flag_assets_for_refresh(
        self,
        asset_ids: List[str],
        reason: str,
        notes: str = ""
    ) -> int:
        """Bulk flag assets for refresh consideration."""
        count = 0
        with self._lock:
            for asset_id in asset_ids:
                asset = self._index.get(asset_id)
                if asset:
                    asset.flag_for_refresh(reason, notes)
                    count += 1
        return count

    # =========================================================================
    # RECONCILIATION (Point 4)
    # =========================================================================

    def reconcile_counts(self) -> Dict[str, Any]:
        """
        Reconcile asset counts and identify discrepancies (Point 4).

        Returns summary of potential inconsistencies.
        """
        with self._lock:
            # Group by vendor + model to find potential duplicates
            vendor_model_groups = {}
            for asset in self.assets:
                key = (asset.vendor.lower(), asset.model.lower())
                if key not in vendor_model_groups:
                    vendor_model_groups[key] = []
                vendor_model_groups[key].append(asset)

            discrepancies = []
            for (vendor, model), assets in vendor_model_groups.items():
                if len(assets) > 1:
                    # Check for conflicting quantities or details
                    locations = set(a.location for a in assets)
                    total_qty = sum(a.quantity for a in assets)

                    discrepancies.append({
                        "vendor": vendor,
                        "model": model,
                        "asset_count": len(assets),
                        "total_quantity": total_qty,
                        "locations": list(locations),
                        "asset_ids": [a.asset_id for a in assets],
                        "note": "Multiple entries for same vendor/model - verify if duplicates or distinct assets"
                    })

            return {
                "total_assets": len(self.assets),
                "unique_vendor_models": len(vendor_model_groups),
                "potential_discrepancies": len(discrepancies),
                "discrepancies": discrepancies
            }

    # =========================================================================
    # VENDOR ANALYSIS (Point 20)
    # =========================================================================

    def get_vendor_concentration(self) -> Dict[str, Any]:
        """
        Analyze vendor concentration (Point 20).

        Identifies over-reliance on single vendors.
        """
        with self._lock:
            vendor_counts = {}
            vendor_by_type = {}

            for asset in self.assets:
                vendor = asset.vendor.lower() or "(unknown)"

                if vendor not in vendor_counts:
                    vendor_counts[vendor] = 0
                vendor_counts[vendor] += asset.quantity

                # Track by asset type
                if vendor not in vendor_by_type:
                    vendor_by_type[vendor] = {}
                if asset.asset_type not in vendor_by_type[vendor]:
                    vendor_by_type[vendor][asset.asset_type] = 0
                vendor_by_type[vendor][asset.asset_type] += asset.quantity

            total = sum(vendor_counts.values())

            # Calculate concentration percentages
            concentration = {
                v: {"count": c, "percentage": (c / total * 100) if total > 0 else 0}
                for v, c in vendor_counts.items()
            }

            # Flag high concentration (>50% in any type)
            high_concentration = []
            for vendor, types in vendor_by_type.items():
                for asset_type, count in types.items():
                    type_total = sum(
                        a.quantity for a in self.assets if a.asset_type == asset_type
                    )
                    if type_total > 0 and (count / type_total) > 0.5:
                        high_concentration.append({
                            "vendor": vendor,
                            "asset_type": asset_type,
                            "count": count,
                            "percentage": count / type_total * 100
                        })

            return {
                "total_assets": total,
                "vendor_count": len(vendor_counts),
                "vendor_concentration": concentration,
                "high_concentration_warnings": high_concentration
            }

    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Export inventory to dictionary."""
        with self._lock:
            return {
                "metadata": self.metadata,
                "summary": {
                    "total_assets": len(self.assets),
                    "by_type": {
                        t.value: sum(1 for a in self.assets if a.asset_type == t.value)
                        for t in AssetType
                    },
                    "by_owner": {
                        o.value: sum(1 for a in self.assets if a.owner == o.value)
                        for o in OwnershipType
                    }
                },
                "assets": [a.to_dict() for a in self.assets],
                "eol_summary": self.get_eol_summary(),
                "refresh_summary": {
                    "flagged_count": len(self.get_refresh_candidates()),
                    "by_reason": {k: len(v) for k, v in self.get_refresh_by_reason().items()}
                }
            }

    def save(self, path: str) -> None:
        """Save inventory to JSON file."""
        data = self.to_dict()
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self.assets)} assets to {path}")

    @classmethod
    def load(cls, path: str) -> "AssetInventory":
        """Load inventory from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)

        inventory = cls()
        inventory.metadata = data.get("metadata", {})

        for asset_dict in data.get("assets", []):
            asset = Asset.from_dict(asset_dict)
            inventory.assets.append(asset)
            inventory._index[asset.asset_id] = asset

            # Update counters
            try:
                parts = asset.asset_id.split("-")
                if len(parts) >= 3:
                    prefix = parts[1]
                    seq = int(parts[2])
                    inventory._counters[prefix] = max(
                        inventory._counters.get(prefix, 0), seq
                    )
            except (ValueError, IndexError):
                pass

        logger.info(f"Loaded {len(inventory.assets)} assets from {path}")
        return inventory

    def __repr__(self) -> str:
        return f"AssetInventory(assets={len(self.assets)})"


# =============================================================================
# ASSET EXTRACTION FROM FACTS (Point 2)
# =============================================================================

def extract_assets_from_facts(fact_store, asset_inventory: AssetInventory = None) -> AssetInventory:
    """
    Extract structured assets from FactStore facts (Point 2).

    Parses infrastructure facts and creates structured Asset entries.

    Args:
        fact_store: FactStore with infrastructure facts
        asset_inventory: Existing inventory to add to (or creates new)

    Returns:
        AssetInventory with extracted assets
    """
    if asset_inventory is None:
        asset_inventory = AssetInventory()

    # Category to asset type mapping
    category_type_map = {
        "hosting": AssetType.COMPUTE.value,
        "compute": AssetType.COMPUTE.value,
        "servers": AssetType.COMPUTE.value,
        "virtualization": AssetType.COMPUTE.value,
        "storage": AssetType.STORAGE.value,
        "backup_dr": AssetType.STORAGE.value,
        "backup": AssetType.STORAGE.value,
        "network": AssetType.NETWORK.value,
        "wan": AssetType.NETWORK.value,
        "lan": AssetType.NETWORK.value,
        "firewall": AssetType.SECURITY.value,
        "security": AssetType.SECURITY.value,
        "cloud": AssetType.CLOUD.value,
        "endpoint": AssetType.ENDPOINT.value,
        "tooling": AssetType.SOFTWARE.value
    }

    # Get infrastructure facts
    infra_facts = [f for f in fact_store.facts if f.domain == "infrastructure"]

    for fact in infra_facts:
        # Determine asset type from category
        asset_type = category_type_map.get(fact.category.lower(), AssetType.OTHER.value)

        # Extract details
        details = fact.details or {}
        vendor = details.get("vendor", details.get("provider", ""))
        model = details.get("model", details.get("product", ""))
        version = details.get("version", "")
        quantity = details.get("count", details.get("quantity", 1))
        location = details.get("location", details.get("datacenter", ""))

        # Determine more specific category
        category = _determine_asset_category(fact.category, fact.item, details)

        # Extract evidence
        evidence = fact.evidence.get("exact_quote", "") if fact.evidence else ""

        # Add to inventory
        asset_inventory.add_asset(
            asset_type=asset_type,
            category=category,
            name=fact.item,
            vendor=vendor,
            model=model,
            version=version,
            quantity=int(quantity) if isinstance(quantity, (int, str)) and str(quantity).isdigit() else 1,
            location=location,
            owner=fact.entity,
            source_fact_ids=[fact.fact_id],
            source_document=fact.source_document,
            evidence_quote=evidence[:500] if evidence else ""
        )

    logger.info(f"Extracted {len(asset_inventory.assets)} assets from {len(infra_facts)} infrastructure facts")
    return asset_inventory


def _determine_asset_category(fact_category: str, item: str, details: Dict) -> str:
    """Determine specific asset category from fact data."""
    item_lower = item.lower()
    category_lower = fact_category.lower()

    # Server detection
    if any(kw in item_lower for kw in ["server", "vm", "virtual machine", "instance"]):
        if "virtual" in item_lower or "vm" in item_lower:
            return AssetCategory.VIRTUAL_SERVER.value
        return AssetCategory.PHYSICAL_SERVER.value

    # Storage detection
    if any(kw in item_lower for kw in ["san", "storage area network"]):
        return AssetCategory.SAN.value
    if any(kw in item_lower for kw in ["nas", "network attached"]):
        return AssetCategory.NAS.value
    if any(kw in item_lower for kw in ["backup", "veeam", "commvault"]):
        return AssetCategory.BACKUP_APPLIANCE.value

    # Network detection
    if any(kw in item_lower for kw in ["switch", "catalyst", "nexus"]):
        return AssetCategory.SWITCH.value
    if any(kw in item_lower for kw in ["router", "routing"]):
        return AssetCategory.ROUTER.value
    if any(kw in item_lower for kw in ["load balancer", "f5", "netscaler"]):
        return AssetCategory.LOAD_BALANCER.value
    if any(kw in item_lower for kw in ["wireless", "wifi", "access point", "ap"]):
        return AssetCategory.WIRELESS_AP.value

    # Security detection
    if any(kw in item_lower for kw in ["firewall", "asa", "fortigate", "palo alto"]):
        return AssetCategory.FIREWALL.value
    if any(kw in item_lower for kw in ["vpn", "remote access"]):
        return AssetCategory.VPN_CONCENTRATOR.value
    if any(kw in item_lower for kw in ["ids", "ips", "intrusion"]):
        return AssetCategory.IDS_IPS.value

    # Cloud detection
    if any(kw in item_lower for kw in ["aws", "azure", "gcp", "ec2", "cloud"]):
        return AssetCategory.IAAS_INSTANCE.value

    # Software detection
    if any(kw in item_lower for kw in ["vmware", "hypervisor", "hyper-v", "esxi"]):
        return AssetCategory.HYPERVISOR.value
    if any(kw in item_lower for kw in ["windows server", "linux", "rhel", "ubuntu"]):
        return AssetCategory.OPERATING_SYSTEM.value
    if any(kw in item_lower for kw in ["sql", "oracle", "database", "postgres", "mysql"]):
        return AssetCategory.DATABASE.value

    return AssetCategory.OTHER.value
