"""
Network Inventory Module (Enhancement Plan Points 21-40)

Structured tracking for WAN, LAN, and network security infrastructure.
Includes circuit inventory, firewall tracking, and architecture assessment.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import logging
import threading
import json

logger = logging.getLogger(__name__)


def _generate_timestamp() -> str:
    """Generate ISO format timestamp."""
    return datetime.now().isoformat()


# =============================================================================
# NETWORK ENUMS AND TYPES (Points 21-22, 28, 33)
# =============================================================================

class CircuitType(Enum):
    """WAN circuit types."""
    MPLS = "mpls"
    SD_WAN = "sd_wan"
    DIA = "dia"  # Direct Internet Access
    P2P = "p2p"  # Point to Point
    BROADBAND = "broadband"
    LTE_5G = "lte_5g"
    METRO_ETHERNET = "metro_ethernet"
    DARK_FIBER = "dark_fiber"
    SATELLITE = "satellite"
    OTHER = "other"


class NetworkDeviceType(Enum):
    """LAN device types."""
    CORE_SWITCH = "core_switch"
    DISTRIBUTION_SWITCH = "distribution_switch"
    ACCESS_SWITCH = "access_switch"
    ROUTER = "router"
    WIRELESS_CONTROLLER = "wireless_controller"
    WIRELESS_AP = "wireless_ap"
    LOAD_BALANCER = "load_balancer"
    WAN_OPTIMIZER = "wan_optimizer"
    OTHER = "other"


class FirewallType(Enum):
    """Firewall/security appliance types."""
    PERIMETER_FIREWALL = "perimeter_firewall"
    INTERNAL_FIREWALL = "internal_firewall"
    DATACENTER_FIREWALL = "datacenter_firewall"
    CLOUD_FIREWALL = "cloud_firewall"
    NGFW = "ngfw"  # Next-Gen Firewall
    UTM = "utm"  # Unified Threat Management
    WAF = "waf"  # Web Application Firewall
    VPN_CONCENTRATOR = "vpn_concentrator"
    IDS_IPS = "ids_ips"
    OTHER = "other"


class NetworkArchitectureType(Enum):
    """Network architecture patterns."""
    HUB_SPOKE = "hub_spoke"
    FULL_MESH = "full_mesh"
    PARTIAL_MESH = "partial_mesh"
    HYBRID = "hybrid"
    CLOUD_FIRST = "cloud_first"
    UNKNOWN = "unknown"


class SegmentationMaturity(Enum):
    """Network segmentation maturity levels."""
    NONE = "none"  # Flat network
    BASIC = "basic"  # VLANs only
    MODERATE = "moderate"  # VLANs + ACLs
    ADVANCED = "advanced"  # Micro-segmentation
    ZERO_TRUST = "zero_trust"  # Full zero-trust


# =============================================================================
# WAN CIRCUIT DATA MODEL (Points 21-27)
# =============================================================================

@dataclass
class WANCircuit:
    """
    A WAN circuit with tracking for type, bandwidth, carrier, and contracts.
    """
    circuit_id: str                               # C-WAN-001
    circuit_type: str                             # mpls, sd_wan, dia, etc.
    carrier: str                                  # Carrier/ISP name
    bandwidth_mbps: int = 0                       # Bandwidth in Mbps
    site_a: str = ""                              # Site A endpoint
    site_b: str = ""                              # Site B endpoint (or "Internet")

    # Contract details (Point 23, 27)
    contract_end_date: str = ""                   # YYYY-MM-DD
    contract_term_months: int = 0                 # Contract length
    notice_period_days: int = 0                   # Early termination notice
    monthly_cost: float = 0.0                     # Monthly recurring cost
    has_termination_clause: bool = False          # ETF applies?

    # Utilization (Point 24)
    avg_utilization_percent: float = 0.0          # Average utilization
    peak_utilization_percent: float = 0.0         # Peak utilization

    # Redundancy (Point 26)
    is_primary: bool = True                       # Primary or backup circuit
    backup_circuit_id: str = ""                   # ID of backup circuit if exists
    has_redundancy: bool = False                  # Is this circuit redundant?

    # Metadata
    owner: str = "target"                         # target, buyer, shared
    source_fact_ids: List[str] = field(default_factory=list)
    source_document: str = ""
    notes: str = ""
    created_at: str = field(default_factory=_generate_timestamp)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "WANCircuit":
        return cls(**data)

    def is_contract_expiring_soon(self, months: int = 12) -> bool:
        """Check if contract expires within specified months."""
        if not self.contract_end_date:
            return False
        try:
            from datetime import date
            end = datetime.strptime(self.contract_end_date, "%Y-%m-%d").date()
            today = date.today()
            months_until = (end.year - today.year) * 12 + (end.month - today.month)
            return 0 < months_until <= months
        except ValueError:
            return False


# =============================================================================
# LAN DEVICE DATA MODEL (Points 28-32)
# =============================================================================

@dataclass
class LANDevice:
    """
    A LAN device (switch, router, wireless AP, etc.) with location tracking.
    """
    device_id: str                                # D-LAN-001
    device_type: str                              # core_switch, access_switch, etc.
    vendor: str = ""                              # Cisco, Aruba, Juniper, etc.
    model: str = ""                               # Specific model
    location: str = ""                            # Site/building/floor
    quantity: int = 1                             # Count of this device type at location

    # For switches
    port_count: int = 0                           # Total ports
    poe_capable: bool = False                     # Power over Ethernet

    # For wireless
    wifi_standard: str = ""                       # WiFi 5, WiFi 6, WiFi 6E
    managed_ap_count: int = 0                     # APs managed (for controllers)

    # EOL tracking
    eol_date: str = ""                            # End of Life date
    eos_date: str = ""                            # End of Support date
    eol_status: str = "unknown"                   # current, approaching, past_eol

    # Metadata
    owner: str = "target"
    source_fact_ids: List[str] = field(default_factory=list)
    source_document: str = ""
    notes: str = ""
    created_at: str = field(default_factory=_generate_timestamp)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "LANDevice":
        return cls(**data)


# =============================================================================
# FIREWALL DATA MODEL (Points 33-37)
# =============================================================================

@dataclass
class Firewall:
    """
    A firewall or security appliance with rule count and EOL tracking.
    """
    firewall_id: str                              # FW-001
    firewall_type: str                            # perimeter, internal, ngfw, etc.
    vendor: str = ""                              # Palo Alto, Fortinet, Cisco, etc.
    model: str = ""                               # Specific model
    location: str = ""                            # Site/DC location

    # Configuration complexity
    rule_count: int = 0                           # Number of rules
    nat_rules: int = 0                            # NAT rules
    vpn_tunnels: int = 0                          # Site-to-site VPN tunnels

    # Capacity
    throughput_gbps: float = 0.0                  # Rated throughput
    concurrent_sessions: int = 0                  # Max concurrent sessions
    current_utilization_percent: float = 0.0     # Current utilization

    # High Availability
    is_ha_pair: bool = False                      # Part of HA pair?
    ha_mode: str = ""                             # active-active, active-passive

    # EOL tracking (Point 34)
    eol_date: str = ""
    eos_date: str = ""
    eol_status: str = "unknown"

    # VPN details (Point 36)
    remote_access_vpn: bool = False               # Supports remote access VPN?
    vpn_client_count: int = 0                     # Number of VPN clients
    split_tunnel: bool = False                    # Split tunnel enabled?

    # Metadata
    owner: str = "target"
    source_fact_ids: List[str] = field(default_factory=list)
    source_document: str = ""
    notes: str = ""
    created_at: str = field(default_factory=_generate_timestamp)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Firewall":
        return cls(**data)


# =============================================================================
# SITE CONNECTIVITY (Point 25)
# =============================================================================

@dataclass
class Site:
    """
    A network site with connectivity information.
    """
    site_id: str                                  # SITE-001
    site_name: str                                # Site name
    site_type: str = ""                           # hq, branch, dc, remote
    address: str = ""                             # Physical address

    # Connectivity
    circuit_ids: List[str] = field(default_factory=list)  # Connected circuits
    is_hub: bool = False                          # Hub site in hub-spoke?
    connected_sites: List[str] = field(default_factory=list)  # Direct connections

    # Infrastructure at site
    lan_device_ids: List[str] = field(default_factory=list)
    firewall_ids: List[str] = field(default_factory=list)

    # Criticality
    user_count: int = 0                           # Users at site
    is_production_dc: bool = False                # Hosts production systems?

    # Metadata
    owner: str = "target"
    source_fact_ids: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=_generate_timestamp)

    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# NETWORK INVENTORY STORE (Points 21-40)
# =============================================================================

class NetworkInventory:
    """
    Central store for network infrastructure tracking.

    Tracks:
    - WAN circuits (MPLS, SD-WAN, DIA, etc.)
    - LAN devices (switches, routers, wireless)
    - Firewalls and security appliances
    - Sites and connectivity
    """

    def __init__(self):
        self.circuits: List[WANCircuit] = []
        self.lan_devices: List[LANDevice] = []
        self.firewalls: List[Firewall] = []
        self.sites: List[Site] = []

        self._counters: Dict[str, int] = {}
        self._circuit_index: Dict[str, WANCircuit] = {}
        self._device_index: Dict[str, LANDevice] = {}
        self._firewall_index: Dict[str, Firewall] = {}
        self._site_index: Dict[str, Site] = {}

        self._lock = threading.RLock()
        self.metadata: Dict[str, Any] = {
            "created_at": _generate_timestamp(),
            "version": "1.0"
        }

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID with prefix."""
        with self._lock:
            if prefix not in self._counters:
                self._counters[prefix] = 0
            self._counters[prefix] += 1
            return f"{prefix}-{self._counters[prefix]:03d}"

    # =========================================================================
    # WAN CIRCUIT METHODS (Points 21-27)
    # =========================================================================

    def add_circuit(
        self,
        circuit_type: str,
        carrier: str,
        bandwidth_mbps: int = 0,
        site_a: str = "",
        site_b: str = "",
        contract_end_date: str = "",
        monthly_cost: float = 0.0,
        **kwargs
    ) -> str:
        """Add a WAN circuit to the inventory."""
        with self._lock:
            circuit_id = self._generate_id("C-WAN")

            circuit = WANCircuit(
                circuit_id=circuit_id,
                circuit_type=circuit_type,
                carrier=carrier,
                bandwidth_mbps=bandwidth_mbps,
                site_a=site_a,
                site_b=site_b,
                contract_end_date=contract_end_date,
                monthly_cost=monthly_cost,
                **kwargs
            )

            self.circuits.append(circuit)
            self._circuit_index[circuit_id] = circuit

            logger.debug(f"Added circuit {circuit_id}: {carrier} {circuit_type}")
            return circuit_id

    def get_circuit(self, circuit_id: str) -> Optional[WANCircuit]:
        """Get circuit by ID."""
        with self._lock:
            return self._circuit_index.get(circuit_id)

    def get_circuits_by_type(self, circuit_type: str) -> List[WANCircuit]:
        """Get all circuits of a specific type."""
        with self._lock:
            return [c for c in self.circuits if c.circuit_type == circuit_type]

    def get_circuits_by_carrier(self, carrier: str) -> List[WANCircuit]:
        """Get all circuits from a carrier."""
        with self._lock:
            carrier_lower = carrier.lower()
            return [c for c in self.circuits if c.carrier.lower() == carrier_lower]

    def get_expiring_circuits(self, months: int = 12) -> List[WANCircuit]:
        """Get circuits with contracts expiring within specified months."""
        with self._lock:
            return [c for c in self.circuits if c.is_contract_expiring_soon(months)]

    def get_wan_topology(self) -> Dict[str, Any]:
        """
        Analyze WAN topology and identify architecture pattern (Point 21, 25).
        """
        with self._lock:
            if not self.circuits:
                return {"architecture": NetworkArchitectureType.UNKNOWN.value, "sites": []}

            # Build site connectivity graph
            site_connections: Dict[str, Set[str]] = {}
            for circuit in self.circuits:
                if circuit.site_a and circuit.site_b:
                    if circuit.site_a not in site_connections:
                        site_connections[circuit.site_a] = set()
                    if circuit.site_b not in site_connections:
                        site_connections[circuit.site_b] = set()

                    if circuit.site_b != "Internet":
                        site_connections[circuit.site_a].add(circuit.site_b)
                        site_connections[circuit.site_b].add(circuit.site_a)

            # Determine architecture pattern
            sites = list(site_connections.keys())
            if not sites:
                architecture = NetworkArchitectureType.UNKNOWN.value
            else:
                # Check for hub-spoke (one site connected to most others)
                max_connections = max(len(conns) for conns in site_connections.values())
                avg_connections = sum(len(conns) for conns in site_connections.values()) / len(sites)

                if max_connections > len(sites) * 0.7:
                    architecture = NetworkArchitectureType.HUB_SPOKE.value
                elif avg_connections > len(sites) * 0.5:
                    architecture = NetworkArchitectureType.FULL_MESH.value
                elif avg_connections > 2:
                    architecture = NetworkArchitectureType.PARTIAL_MESH.value
                else:
                    architecture = NetworkArchitectureType.HYBRID.value

            return {
                "architecture": architecture,
                "site_count": len(sites),
                "circuit_count": len(self.circuits),
                "sites": sites,
                "connectivity": {site: list(conns) for site, conns in site_connections.items()}
            }

    def get_wan_redundancy_analysis(self) -> Dict[str, Any]:
        """
        Analyze WAN redundancy and identify single points of failure (Point 26).
        """
        with self._lock:
            # Group circuits by site pair
            site_pairs: Dict[tuple, List[WANCircuit]] = {}
            for circuit in self.circuits:
                if circuit.site_a and circuit.site_b:
                    key = tuple(sorted([circuit.site_a, circuit.site_b]))
                    if key not in site_pairs:
                        site_pairs[key] = []
                    site_pairs[key].append(circuit)

            # Identify single points of failure
            spof_connections = []
            redundant_connections = []

            for (site_a, site_b), circuits in site_pairs.items():
                if len(circuits) == 1:
                    spof_connections.append({
                        "site_a": site_a,
                        "site_b": site_b,
                        "circuit_id": circuits[0].circuit_id,
                        "circuit_type": circuits[0].circuit_type,
                        "carrier": circuits[0].carrier
                    })
                else:
                    # Check carrier diversity
                    carriers = set(c.carrier for c in circuits)
                    circuit_types = set(c.circuit_type for c in circuits)
                    redundant_connections.append({
                        "site_a": site_a,
                        "site_b": site_b,
                        "circuit_count": len(circuits),
                        "carrier_diverse": len(carriers) > 1,
                        "type_diverse": len(circuit_types) > 1
                    })

            return {
                "total_connections": len(site_pairs),
                "single_point_of_failure_count": len(spof_connections),
                "redundant_connection_count": len(redundant_connections),
                "spof_connections": spof_connections,
                "redundant_connections": redundant_connections,
                "redundancy_score": len(redundant_connections) / len(site_pairs) if site_pairs else 0
            }

    def get_carrier_concentration(self) -> Dict[str, Any]:
        """Analyze carrier concentration across WAN circuits."""
        with self._lock:
            carrier_counts: Dict[str, int] = {}
            total_bandwidth = 0
            carrier_bandwidth: Dict[str, int] = {}

            for circuit in self.circuits:
                carrier = circuit.carrier or "(unknown)"
                carrier_counts[carrier] = carrier_counts.get(carrier, 0) + 1
                carrier_bandwidth[carrier] = carrier_bandwidth.get(carrier, 0) + circuit.bandwidth_mbps
                total_bandwidth += circuit.bandwidth_mbps

            return {
                "carrier_count": len(carrier_counts),
                "circuit_count": len(self.circuits),
                "total_bandwidth_mbps": total_bandwidth,
                "by_carrier": {
                    carrier: {
                        "circuit_count": count,
                        "bandwidth_mbps": carrier_bandwidth.get(carrier, 0),
                        "circuit_percent": count / len(self.circuits) * 100 if self.circuits else 0
                    }
                    for carrier, count in carrier_counts.items()
                }
            }

    # =========================================================================
    # LAN DEVICE METHODS (Points 28-32)
    # =========================================================================

    def add_lan_device(
        self,
        device_type: str,
        vendor: str = "",
        model: str = "",
        location: str = "",
        quantity: int = 1,
        **kwargs
    ) -> str:
        """Add a LAN device to the inventory."""
        with self._lock:
            device_id = self._generate_id("D-LAN")

            device = LANDevice(
                device_id=device_id,
                device_type=device_type,
                vendor=vendor,
                model=model,
                location=location,
                quantity=quantity,
                **kwargs
            )

            self.lan_devices.append(device)
            self._device_index[device_id] = device

            logger.debug(f"Added LAN device {device_id}: {vendor} {model}")
            return device_id

    def get_lan_device(self, device_id: str) -> Optional[LANDevice]:
        """Get LAN device by ID."""
        with self._lock:
            return self._device_index.get(device_id)

    def get_devices_by_location(self, location: str) -> List[LANDevice]:
        """Get all devices at a location."""
        with self._lock:
            location_lower = location.lower()
            return [d for d in self.lan_devices if d.location.lower() == location_lower]

    def get_devices_by_type(self, device_type: str) -> List[LANDevice]:
        """Get all devices of a type."""
        with self._lock:
            return [d for d in self.lan_devices if d.device_type == device_type]

    def get_wireless_summary(self) -> Dict[str, Any]:
        """Get wireless infrastructure summary (Point 30)."""
        with self._lock:
            controllers = [d for d in self.lan_devices if d.device_type == "wireless_controller"]
            aps = [d for d in self.lan_devices if d.device_type == "wireless_ap"]

            wifi_standards = set()
            total_aps = 0

            for ap in aps:
                total_aps += ap.quantity
                if ap.wifi_standard:
                    wifi_standards.add(ap.wifi_standard)

            for ctrl in controllers:
                if ctrl.managed_ap_count:
                    total_aps = max(total_aps, ctrl.managed_ap_count)

            return {
                "controller_count": len(controllers),
                "ap_count": total_aps,
                "wifi_standards": list(wifi_standards),
                "vendors": list(set(d.vendor for d in controllers + aps if d.vendor))
            }

    # =========================================================================
    # FIREWALL METHODS (Points 33-37)
    # =========================================================================

    def add_firewall(
        self,
        firewall_type: str,
        vendor: str = "",
        model: str = "",
        location: str = "",
        **kwargs
    ) -> str:
        """Add a firewall to the inventory."""
        with self._lock:
            firewall_id = self._generate_id("FW")

            firewall = Firewall(
                firewall_id=firewall_id,
                firewall_type=firewall_type,
                vendor=vendor,
                model=model,
                location=location,
                **kwargs
            )

            self.firewalls.append(firewall)
            self._firewall_index[firewall_id] = firewall

            logger.debug(f"Added firewall {firewall_id}: {vendor} {model}")
            return firewall_id

    def get_firewall(self, firewall_id: str) -> Optional[Firewall]:
        """Get firewall by ID."""
        with self._lock:
            return self._firewall_index.get(firewall_id)

    def get_eol_firewalls(self) -> List[Firewall]:
        """Get firewalls that are past or approaching EOL (Point 34)."""
        with self._lock:
            return [f for f in self.firewalls
                    if f.eol_status in ("past_eol", "approaching")]

    def get_firewall_summary(self) -> Dict[str, Any]:
        """Get firewall infrastructure summary."""
        with self._lock:
            total_rules = sum(f.rule_count for f in self.firewalls)
            total_vpn_tunnels = sum(f.vpn_tunnels for f in self.firewalls)
            ha_pairs = sum(1 for f in self.firewalls if f.is_ha_pair)

            return {
                "firewall_count": len(self.firewalls),
                "total_rule_count": total_rules,
                "total_vpn_tunnels": total_vpn_tunnels,
                "ha_pair_count": ha_pairs,
                "by_type": {
                    ft.value: sum(1 for f in self.firewalls if f.firewall_type == ft.value)
                    for ft in FirewallType
                },
                "by_vendor": {
                    vendor: sum(1 for f in self.firewalls if f.vendor == vendor)
                    for vendor in set(f.vendor for f in self.firewalls if f.vendor)
                },
                "eol_count": len(self.get_eol_firewalls()),
                "remote_access_capable": sum(1 for f in self.firewalls if f.remote_access_vpn),
                "total_vpn_clients": sum(f.vpn_client_count for f in self.firewalls)
            }

    def get_segmentation_assessment(self) -> Dict[str, Any]:
        """
        Assess network segmentation maturity (Point 29, 35).
        """
        with self._lock:
            # Count internal firewalls as indicator of segmentation
            internal_fws = sum(1 for f in self.firewalls
                             if f.firewall_type in ("internal_firewall", "datacenter_firewall"))

            # Assess maturity based on infrastructure
            total_fws = len(self.firewalls)

            if total_fws == 0:
                maturity = SegmentationMaturity.UNKNOWN
                score = 0
            elif internal_fws == 0:
                maturity = SegmentationMaturity.BASIC
                score = 25
            elif internal_fws < total_fws * 0.3:
                maturity = SegmentationMaturity.MODERATE
                score = 50
            elif internal_fws < total_fws * 0.5:
                maturity = SegmentationMaturity.ADVANCED
                score = 75
            else:
                maturity = SegmentationMaturity.ZERO_TRUST
                score = 90

            return {
                "maturity_level": maturity.value,
                "maturity_score": score,
                "total_firewalls": total_fws,
                "internal_firewalls": internal_fws,
                "perimeter_only": internal_fws == 0 and total_fws > 0,
                "assessment": self._get_segmentation_assessment_text(maturity)
            }

    def _get_segmentation_assessment_text(self, maturity: SegmentationMaturity) -> str:
        """Get human-readable assessment text."""
        texts = {
            SegmentationMaturity.NONE: "No network segmentation detected. Flat network architecture.",
            SegmentationMaturity.BASIC: "Basic segmentation with VLANs. Perimeter-only firewalls.",
            SegmentationMaturity.MODERATE: "Moderate segmentation with some internal firewalls and ACLs.",
            SegmentationMaturity.ADVANCED: "Advanced segmentation with significant internal firewalling.",
            SegmentationMaturity.ZERO_TRUST: "Zero-trust architecture with comprehensive micro-segmentation.",
        }
        return texts.get(maturity, "Unable to assess segmentation maturity.")

    # =========================================================================
    # SITE METHODS (Point 25)
    # =========================================================================

    def add_site(
        self,
        site_name: str,
        site_type: str = "",
        address: str = "",
        **kwargs
    ) -> str:
        """Add a site to the inventory."""
        with self._lock:
            site_id = self._generate_id("SITE")

            site = Site(
                site_id=site_id,
                site_name=site_name,
                site_type=site_type,
                address=address,
                **kwargs
            )

            self.sites.append(site)
            self._site_index[site_id] = site

            logger.debug(f"Added site {site_id}: {site_name}")
            return site_id

    def get_site_connectivity_map(self) -> Dict[str, Any]:
        """Generate site connectivity map (Point 25)."""
        with self._lock:
            site_map = {}

            for site in self.sites:
                # Get circuits for this site
                site_circuits = [
                    c for c in self.circuits
                    if c.site_a == site.site_name or c.site_b == site.site_name
                ]

                # Get connected sites
                connected = set()
                for c in site_circuits:
                    if c.site_a == site.site_name and c.site_b != "Internet":
                        connected.add(c.site_b)
                    elif c.site_b == site.site_name:
                        connected.add(c.site_a)

                site_map[site.site_name] = {
                    "site_id": site.site_id,
                    "site_type": site.site_type,
                    "is_hub": site.is_hub,
                    "user_count": site.user_count,
                    "circuit_count": len(site_circuits),
                    "connected_sites": list(connected),
                    "has_internet": any(c.site_b == "Internet" or c.circuit_type == "dia"
                                       for c in site_circuits)
                }

            return {
                "site_count": len(self.sites),
                "sites": site_map
            }

    # =========================================================================
    # ARCHITECTURE ASSESSMENT (Points 38-40)
    # =========================================================================

    def get_architecture_assessment(self) -> Dict[str, Any]:
        """
        Comprehensive network architecture assessment (Point 38).
        """
        with self._lock:
            # Determine technology mix
            has_sdwan = any(c.circuit_type == "sd_wan" for c in self.circuits)
            has_mpls = any(c.circuit_type == "mpls" for c in self.circuits)
            mpls_count = sum(1 for c in self.circuits if c.circuit_type == "mpls")
            sdwan_count = sum(1 for c in self.circuits if c.circuit_type == "sd_wan")

            # Assess maturity
            if sdwan_count > mpls_count:
                maturity = "modern"
                description = "SD-WAN first architecture with modern connectivity approach"
            elif has_sdwan and has_mpls:
                maturity = "transitional"
                description = "Hybrid architecture with both MPLS and SD-WAN"
            elif has_mpls and not has_sdwan:
                maturity = "traditional"
                description = "Traditional MPLS-based architecture"
            else:
                maturity = "basic"
                description = "Basic connectivity without enterprise WAN services"

            return {
                "maturity": maturity,
                "description": description,
                "has_sdwan": has_sdwan,
                "has_mpls": has_mpls,
                "sdwan_circuit_count": sdwan_count,
                "mpls_circuit_count": mpls_count,
                "total_circuits": len(self.circuits),
                "topology": self.get_wan_topology(),
                "redundancy": self.get_wan_redundancy_analysis(),
                "segmentation": self.get_segmentation_assessment()
            }

    def get_shared_dependencies(self) -> Dict[str, Any]:
        """
        Identify shared network dependencies (Point 39).
        """
        with self._lock:
            shared_circuits = [c for c in self.circuits if c.owner == "shared"]
            shared_firewalls = [f for f in self.firewalls if f.owner == "shared"]
            shared_devices = [d for d in self.lan_devices if d.owner == "shared"]

            return {
                "has_shared_dependencies": bool(shared_circuits or shared_firewalls or shared_devices),
                "shared_circuit_count": len(shared_circuits),
                "shared_firewall_count": len(shared_firewalls),
                "shared_device_count": len(shared_devices),
                "shared_circuits": [c.to_dict() for c in shared_circuits],
                "shared_firewalls": [f.to_dict() for f in shared_firewalls],
                "separation_complexity": self._assess_separation_complexity(
                    shared_circuits, shared_firewalls, shared_devices
                )
            }

    def _assess_separation_complexity(
        self,
        circuits: List[WANCircuit],
        firewalls: List[Firewall],
        devices: List[LANDevice]
    ) -> str:
        """Assess complexity of separating shared network resources."""
        total_shared = len(circuits) + len(firewalls) + len(devices)

        if total_shared == 0:
            return "low"
        elif total_shared < 5:
            return "moderate"
        elif total_shared < 10:
            return "high"
        else:
            return "very_high"

    def get_documentation_gaps(self) -> Dict[str, Any]:
        """
        Identify network documentation gaps (Point 40).
        """
        with self._lock:
            gaps = []

            # Check for missing circuit details
            circuits_missing_bandwidth = [c for c in self.circuits if c.bandwidth_mbps == 0]
            if circuits_missing_bandwidth:
                gaps.append({
                    "area": "wan_circuits",
                    "gap": "bandwidth_not_documented",
                    "count": len(circuits_missing_bandwidth),
                    "severity": "medium"
                })

            circuits_missing_contract = [c for c in self.circuits if not c.contract_end_date]
            if circuits_missing_contract:
                gaps.append({
                    "area": "wan_circuits",
                    "gap": "contract_dates_not_documented",
                    "count": len(circuits_missing_contract),
                    "severity": "high"
                })

            # Check for missing firewall details
            firewalls_missing_rules = [f for f in self.firewalls if f.rule_count == 0]
            if firewalls_missing_rules:
                gaps.append({
                    "area": "firewalls",
                    "gap": "rule_count_not_documented",
                    "count": len(firewalls_missing_rules),
                    "severity": "medium"
                })

            # Check for missing device EOL
            devices_missing_eol = [d for d in self.lan_devices if d.eol_status == "unknown"]
            if devices_missing_eol:
                gaps.append({
                    "area": "lan_devices",
                    "gap": "eol_status_not_documented",
                    "count": len(devices_missing_eol),
                    "severity": "medium"
                })

            return {
                "gap_count": len(gaps),
                "gaps": gaps,
                "documentation_score": max(0, 100 - len(gaps) * 15)
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
                    "circuit_count": len(self.circuits),
                    "lan_device_count": len(self.lan_devices),
                    "firewall_count": len(self.firewalls),
                    "site_count": len(self.sites)
                },
                "circuits": [c.to_dict() for c in self.circuits],
                "lan_devices": [d.to_dict() for d in self.lan_devices],
                "firewalls": [f.to_dict() for f in self.firewalls],
                "sites": [s.to_dict() for s in self.sites],
                "assessments": {
                    "architecture": self.get_architecture_assessment(),
                    "wan_topology": self.get_wan_topology(),
                    "redundancy": self.get_wan_redundancy_analysis(),
                    "segmentation": self.get_segmentation_assessment(),
                    "documentation_gaps": self.get_documentation_gaps()
                }
            }

    def save(self, path: str) -> None:
        """Save inventory to JSON file."""
        data = self.to_dict()
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved network inventory to {path}")

    @classmethod
    def load(cls, path: str) -> "NetworkInventory":
        """Load inventory from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)

        inventory = cls()
        inventory.metadata = data.get("metadata", {})

        for c_dict in data.get("circuits", []):
            circuit = WANCircuit.from_dict(c_dict)
            inventory.circuits.append(circuit)
            inventory._circuit_index[circuit.circuit_id] = circuit

        for d_dict in data.get("lan_devices", []):
            device = LANDevice.from_dict(d_dict)
            inventory.lan_devices.append(device)
            inventory._device_index[device.device_id] = device

        for f_dict in data.get("firewalls", []):
            firewall = Firewall.from_dict(f_dict)
            inventory.firewalls.append(firewall)
            inventory._firewall_index[firewall.firewall_id] = firewall

        for s_dict in data.get("sites", []):
            site = Site(**s_dict)
            inventory.sites.append(site)
            inventory._site_index[site.site_id] = site

        logger.info(f"Loaded network inventory from {path}")
        return inventory

    def __repr__(self) -> str:
        return f"NetworkInventory(circuits={len(self.circuits)}, devices={len(self.lan_devices)}, firewalls={len(self.firewalls)})"


# =============================================================================
# NETWORK EXTRACTION FROM FACTS
# =============================================================================

def extract_network_from_facts(fact_store, network_inventory: NetworkInventory = None) -> NetworkInventory:
    """
    Extract structured network data from FactStore facts.

    Parses network domain facts and creates structured entries.
    """
    if network_inventory is None:
        network_inventory = NetworkInventory()

    # Get network facts
    network_facts = [f for f in fact_store.facts if f.domain == "network"]

    for fact in network_facts:
        details = fact.details or {}
        category = fact.category.lower()
        item_lower = fact.item.lower()

        # Detect WAN circuits
        if any(kw in category for kw in ["wan", "circuit", "mpls", "sdwan", "sd-wan"]):
            circuit_type = _detect_circuit_type(fact.item, details)
            network_inventory.add_circuit(
                circuit_type=circuit_type,
                carrier=details.get("carrier", details.get("provider", "")),
                bandwidth_mbps=int(details.get("bandwidth", details.get("bandwidth_mbps", 0)) or 0),
                site_a=details.get("site_a", details.get("location", "")),
                site_b=details.get("site_b", ""),
                source_fact_ids=[fact.fact_id],
                source_document=fact.source_document,
                owner=fact.entity
            )

        # Detect firewalls
        elif any(kw in item_lower for kw in ["firewall", "asa", "fortigate", "palo alto", "checkpoint"]):
            fw_type = _detect_firewall_type(fact.item, details)
            network_inventory.add_firewall(
                firewall_type=fw_type,
                vendor=details.get("vendor", ""),
                model=details.get("model", ""),
                location=details.get("location", ""),
                rule_count=int(details.get("rule_count", details.get("rules", 0)) or 0),
                source_fact_ids=[fact.fact_id],
                source_document=fact.source_document,
                owner=fact.entity
            )

        # Detect LAN devices
        elif any(kw in item_lower for kw in ["switch", "router", "wireless", "wifi", "access point"]):
            device_type = _detect_device_type(fact.item, details)
            network_inventory.add_lan_device(
                device_type=device_type,
                vendor=details.get("vendor", ""),
                model=details.get("model", ""),
                location=details.get("location", ""),
                quantity=int(details.get("count", details.get("quantity", 1)) or 1),
                source_fact_ids=[fact.fact_id],
                source_document=fact.source_document,
                owner=fact.entity
            )

    logger.info(f"Extracted {len(network_inventory.circuits)} circuits, "
                f"{len(network_inventory.firewalls)} firewalls, "
                f"{len(network_inventory.lan_devices)} LAN devices from {len(network_facts)} network facts")

    return network_inventory


def _detect_circuit_type(item: str, details: Dict) -> str:
    """Detect circuit type from fact data."""
    item_lower = item.lower()

    if "sd-wan" in item_lower or "sdwan" in item_lower:
        return CircuitType.SD_WAN.value
    if "mpls" in item_lower:
        return CircuitType.MPLS.value
    if "dia" in item_lower or "direct internet" in item_lower:
        return CircuitType.DIA.value
    if "point to point" in item_lower or "p2p" in item_lower:
        return CircuitType.P2P.value
    if "broadband" in item_lower:
        return CircuitType.BROADBAND.value
    if "lte" in item_lower or "5g" in item_lower:
        return CircuitType.LTE_5G.value

    return CircuitType.OTHER.value


def _detect_firewall_type(item: str, details: Dict) -> str:
    """Detect firewall type from fact data."""
    item_lower = item.lower()

    if "perimeter" in item_lower or "edge" in item_lower:
        return FirewallType.PERIMETER_FIREWALL.value
    if "internal" in item_lower:
        return FirewallType.INTERNAL_FIREWALL.value
    if "datacenter" in item_lower or "dc" in item_lower:
        return FirewallType.DATACENTER_FIREWALL.value
    if "waf" in item_lower or "web application" in item_lower:
        return FirewallType.WAF.value
    if "vpn" in item_lower:
        return FirewallType.VPN_CONCENTRATOR.value
    if "ids" in item_lower or "ips" in item_lower:
        return FirewallType.IDS_IPS.value

    return FirewallType.NGFW.value


def _detect_device_type(item: str, details: Dict) -> str:
    """Detect LAN device type from fact data."""
    item_lower = item.lower()

    if "core" in item_lower and "switch" in item_lower:
        return NetworkDeviceType.CORE_SWITCH.value
    if "distribution" in item_lower:
        return NetworkDeviceType.DISTRIBUTION_SWITCH.value
    if "access" in item_lower and "switch" in item_lower:
        return NetworkDeviceType.ACCESS_SWITCH.value
    if "router" in item_lower:
        return NetworkDeviceType.ROUTER.value
    if "controller" in item_lower and "wireless" in item_lower:
        return NetworkDeviceType.WIRELESS_CONTROLLER.value
    if "access point" in item_lower or " ap" in item_lower or "wifi" in item_lower:
        return NetworkDeviceType.WIRELESS_AP.value
    if "load balancer" in item_lower or "f5" in item_lower:
        return NetworkDeviceType.LOAD_BALANCER.value

    return NetworkDeviceType.ACCESS_SWITCH.value
