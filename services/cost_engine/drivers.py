"""
Driver Extraction Module

Extracts quantitative drivers from facts for cost calculations.
Drivers are the inputs to deterministic cost models (user counts, sites, apps, etc.)

Key concepts:
- Drivers are extracted from fact details fields
- Each driver tracks its source (fact ID) and confidence
- Overrides allow analysts to correct extracted values
- Effective drivers = extracted + overrides merged
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class DriverConfidence(Enum):
    """Confidence level in an extracted driver value."""
    HIGH = "high"          # Explicit value in document
    MEDIUM = "medium"      # Inferred from context
    LOW = "low"            # Assumed default
    OVERRIDE = "override"  # Human-provided override


class OwnershipType(Enum):
    """Who owns a system/service."""
    TARGET = "target"
    PARENT = "parent"
    BUYER = "buyer"
    SHARED = "shared"
    UNKNOWN = "unknown"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DriverSource:
    """Tracks where a driver value came from."""
    fact_id: Optional[str] = None       # F-ORG-012, etc.
    fact_item: Optional[str] = None     # Human-readable item name
    field_path: Optional[str] = None    # details.user_count
    confidence: DriverConfidence = DriverConfidence.LOW
    extraction_method: str = "default"  # "direct", "inferred", "counted", "default"
    notes: str = ""

    def to_dict(self) -> Dict:
        result = asdict(self)
        result['confidence'] = self.confidence.value
        return result


@dataclass
class DealDrivers:
    """
    Quantitative drivers extracted from facts.

    These are the inputs to cost calculations. Each driver can be:
    - Extracted directly from a fact (high confidence)
    - Inferred from related facts (medium confidence)
    - Assumed as default (low confidence)
    - Overridden by analyst (override confidence)

    Entity dimension enables separate calculations for buyer vs target.
    """

    # ==========================================================================
    # ENTITY DIMENSION
    # ==========================================================================
    entity: str = "target"  # "target", "buyer", or "all"

    # ==========================================================================
    # SCALE DRIVERS
    # ==========================================================================
    total_users: Optional[int] = None
    it_headcount: Optional[int] = None
    sites: Optional[int] = None
    countries: Optional[int] = None

    # ==========================================================================
    # APPLICATION DRIVERS
    # ==========================================================================
    total_apps: Optional[int] = None
    erp_system: Optional[str] = None        # "SAP", "Oracle", "NetSuite", "None"
    erp_users: Optional[int] = None
    crm_system: Optional[str] = None
    crm_users: Optional[int] = None
    custom_apps: Optional[int] = None
    saas_apps: Optional[int] = None

    # ==========================================================================
    # INFRASTRUCTURE DRIVERS
    # ==========================================================================
    data_centers: Optional[int] = None
    servers: Optional[int] = None
    vms: Optional[int] = None
    cloud_provider: Optional[str] = None    # "AWS", "Azure", "GCP", "Multi", "None"
    cloud_spend_annual: Optional[float] = None
    storage_tb: Optional[float] = None
    endpoints: Optional[int] = None

    # ==========================================================================
    # IDENTITY DRIVERS
    # ==========================================================================
    identity_provider: Optional[str] = None  # "Azure AD", "Okta", "On-prem AD"
    identity_users: Optional[int] = None
    mfa_deployed: Optional[bool] = None
    pam_solution: Optional[str] = None

    # ==========================================================================
    # NETWORK DRIVERS
    # ==========================================================================
    wan_type: Optional[str] = None           # "MPLS", "SD-WAN", "Internet"
    wan_sites: Optional[int] = None
    vpn_users: Optional[int] = None

    # ==========================================================================
    # SECURITY DRIVERS
    # ==========================================================================
    edr_solution: Optional[str] = None
    siem_solution: Optional[str] = None
    soc_model: Optional[str] = None          # "in-house", "mssp", "parent", "none"

    # ==========================================================================
    # OWNERSHIP DRIVERS (GPT's suggestion)
    # ==========================================================================
    identity_owned_by: OwnershipType = OwnershipType.UNKNOWN
    dc_owned_by: OwnershipType = OwnershipType.UNKNOWN
    wan_owned_by: OwnershipType = OwnershipType.UNKNOWN
    erp_owned_by: OwnershipType = OwnershipType.UNKNOWN
    email_owned_by: OwnershipType = OwnershipType.UNKNOWN
    soc_owned_by: OwnershipType = OwnershipType.UNKNOWN

    shared_with_parent: List[str] = field(default_factory=list)  # ["identity", "dc", "wan"]

    # ==========================================================================
    # TIMELINE DRIVERS
    # ==========================================================================
    tsa_months_assumed: int = 12             # Default assumption

    # ==========================================================================
    # SOURCE TRACKING
    # ==========================================================================
    sources: Dict[str, DriverSource] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = {}
        for key, value in asdict(self).items():
            if key == 'sources':
                result['sources'] = {k: v.to_dict() if hasattr(v, 'to_dict') else v
                                     for k, v in self.sources.items()}
            elif isinstance(value, OwnershipType):
                result[key] = value.value
            elif isinstance(value, list) and key == 'shared_with_parent':
                result[key] = value
            else:
                result[key] = value
        return result

    def get_missing_drivers(self, required: List[str]) -> List[str]:
        """Return list of required drivers that are None."""
        missing = []
        for driver_name in required:
            if getattr(self, driver_name, None) is None:
                missing.append(driver_name)
        return missing

    def get_assumed_drivers(self) -> List[str]:
        """Return list of drivers using default/low confidence values."""
        assumed = []
        for driver_name, source in self.sources.items():
            if source.confidence == DriverConfidence.LOW:
                assumed.append(driver_name)
        return assumed

    def __post_init__(self):
        """Validate entity field."""
        allowed_entities = ["target", "buyer", "all"]
        if self.entity not in allowed_entities:
            raise ValueError(f"entity must be one of {allowed_entities}, got: {self.entity}")


@dataclass
class DriverExtractionResult:
    """Result of extracting drivers from a deal's facts."""
    drivers: DealDrivers
    facts_scanned: int
    drivers_extracted: int
    drivers_assumed: int
    conflicts: List[Dict]  # Multiple facts claimed different values
    warnings: List[str]

    def to_dict(self) -> Dict:
        return {
            'drivers': self.drivers.to_dict(),
            'facts_scanned': self.facts_scanned,
            'drivers_extracted': self.drivers_extracted,
            'drivers_assumed': self.drivers_assumed,
            'conflicts': self.conflicts,
            'warnings': self.warnings,
        }


# =============================================================================
# FIELD MAPPINGS
# =============================================================================

# Maps fact detail fields to driver names
# Format: (fact_field_path, driver_name, transform_fn)
FIELD_MAPPINGS = [
    # User counts
    ('user_count', 'total_users', int),
    ('users', 'total_users', int),
    ('total_users', 'total_users', int),
    ('headcount', 'total_users', int),
    ('employee_count', 'total_users', int),
    ('num_users', 'total_users', int),
    ('active_users', 'total_users', int),

    # IT headcount
    ('it_headcount', 'it_headcount', int),
    ('it_staff', 'it_headcount', int),
    ('it_team_size', 'it_headcount', int),

    # Sites
    ('sites', 'sites', int),
    ('locations', 'sites', int),
    ('offices', 'sites', int),
    ('site_count', 'sites', int),
    ('num_sites', 'sites', int),

    # Countries
    ('countries', 'countries', int),
    ('country_count', 'countries', int),
    ('regions', 'countries', int),

    # Data centers
    ('data_centers', 'data_centers', int),
    ('datacenters', 'data_centers', int),
    ('dc_count', 'data_centers', int),

    # Servers/VMs
    ('servers', 'servers', int),
    ('server_count', 'servers', int),
    ('vms', 'vms', int),
    ('vm_count', 'vms', int),
    ('virtual_machines', 'vms', int),

    # Endpoints
    ('endpoints', 'endpoints', int),
    ('endpoint_count', 'endpoints', int),
    ('devices', 'endpoints', int),
    ('workstations', 'endpoints', int),

    # Storage
    ('storage_tb', 'storage_tb', float),
    ('storage', 'storage_tb', float),

    # Cloud spend
    ('cloud_spend', 'cloud_spend_annual', float),
    ('annual_cloud_spend', 'cloud_spend_annual', float),
    ('cloud_cost', 'cloud_spend_annual', float),

    # ERP users
    ('erp_users', 'erp_users', int),
    ('sap_users', 'erp_users', int),
    ('oracle_users', 'erp_users', int),

    # CRM users
    ('crm_users', 'crm_users', int),
    ('salesforce_users', 'crm_users', int),

    # VPN users
    ('vpn_users', 'vpn_users', int),
    ('remote_users', 'vpn_users', int),

    # Identity users (usually same as total_users)
    ('identity_users', 'identity_users', int),
    ('ad_users', 'identity_users', int),
    ('directory_users', 'identity_users', int),
]

# Maps fact items/categories to string drivers
SYSTEM_MAPPINGS = {
    # ERP systems
    'erp_system': [
        ('sap', 'SAP'),
        ('s/4hana', 'SAP'),
        ('s4hana', 'SAP'),
        ('oracle', 'Oracle'),
        ('oracle ebs', 'Oracle'),
        ('netsuite', 'NetSuite'),
        ('dynamics', 'Microsoft Dynamics'),
        ('dynamics 365', 'Microsoft Dynamics'),
        ('workday', 'Workday'),
    ],
    # CRM systems
    'crm_system': [
        ('salesforce', 'Salesforce'),
        ('hubspot', 'HubSpot'),
        ('dynamics crm', 'Microsoft Dynamics'),
        ('zoho', 'Zoho'),
    ],
    # Cloud providers
    'cloud_provider': [
        ('aws', 'AWS'),
        ('amazon web services', 'AWS'),
        ('azure', 'Azure'),
        ('microsoft azure', 'Azure'),
        ('gcp', 'GCP'),
        ('google cloud', 'GCP'),
    ],
    # Identity providers
    'identity_provider': [
        ('azure ad', 'Azure AD'),
        ('entra', 'Azure AD'),
        ('okta', 'Okta'),
        ('active directory', 'On-prem AD'),
        ('on-prem ad', 'On-prem AD'),
        ('ping', 'Ping Identity'),
    ],
    # WAN types
    'wan_type': [
        ('mpls', 'MPLS'),
        ('sd-wan', 'SD-WAN'),
        ('sdwan', 'SD-WAN'),
        ('internet', 'Internet'),
    ],
    # EDR solutions
    'edr_solution': [
        ('crowdstrike', 'CrowdStrike'),
        ('falcon', 'CrowdStrike'),
        ('sentinel one', 'SentinelOne'),
        ('sentinelone', 'SentinelOne'),
        ('defender', 'Microsoft Defender'),
        ('carbon black', 'Carbon Black'),
    ],
    # SIEM solutions
    'siem_solution': [
        ('splunk', 'Splunk'),
        ('sentinel', 'Microsoft Sentinel'),
        ('qradar', 'IBM QRadar'),
        ('elastic', 'Elastic'),
    ],
    # SOC model
    'soc_model': [
        ('in-house', 'in-house'),
        ('internal', 'in-house'),
        ('mssp', 'mssp'),
        ('managed', 'mssp'),
        ('outsourced', 'mssp'),
        ('parent', 'parent'),
    ],
}

# Ownership detection patterns
PARENT_OWNERSHIP_PATTERNS = [
    'parent',
    'corporate',
    'shared with parent',
    'enterprise agreement',
    'parent company',
    'centralized',
    'parent-managed',
    'parent-hosted',
    'parent-owned',
]


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def _parse_numeric(value: Any, transform: type = int) -> Optional[int]:
    """Parse a numeric value from various formats."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return transform(value)
    if isinstance(value, str):
        # Remove common formatting
        cleaned = value.replace(',', '').replace('$', '').replace('+', '').strip()
        # Handle ranges like "100-200" by taking first value
        if '-' in cleaned and not cleaned.startswith('-'):
            cleaned = cleaned.split('-')[0].strip()
        # Handle "~100" or "approximately 100"
        cleaned = cleaned.replace('~', '').replace('approximately', '').strip()
        try:
            if transform == int:
                return int(float(cleaned))
            return transform(cleaned)
        except (ValueError, TypeError):
            return None
    return None


def _detect_system(text: str, system_type: str) -> Optional[str]:
    """Detect a system name from text using mappings."""
    if not text:
        return None
    text_lower = text.lower()
    mappings = SYSTEM_MAPPINGS.get(system_type, [])
    for pattern, value in mappings:
        if pattern in text_lower:
            return value
    return None


def _detect_parent_ownership(fact) -> bool:
    """Check if a fact indicates parent ownership."""
    # Check details
    details = fact.details or {}
    details_str = str(details).lower()

    # Check item name
    item_str = (fact.item or '').lower()

    # Check category
    category_str = (fact.category or '').lower()

    combined = f"{details_str} {item_str} {category_str}"

    for pattern in PARENT_OWNERSHIP_PATTERNS:
        if pattern in combined:
            return True

    # Check explicit ownership field
    if details.get('owned_by', '').lower() == 'parent':
        return True
    if details.get('provider', '').lower() in ['parent', 'parent company', 'corporate']:
        return True

    return False


def extract_drivers_from_facts(facts: List[Any], deal_id: str = None, entity: str = "target") -> DriverExtractionResult:
    """
    Extract quantitative drivers from a list of facts.

    Args:
        facts: List of Fact objects (from FactStore or database)
        deal_id: Optional deal ID for logging
        entity: Entity filter ("target", "buyer", or "all")

    Returns:
        DriverExtractionResult with entity-filtered drivers
    """
    # Validate entity
    if entity not in ["target", "buyer", "all"]:
        raise ValueError(f"Invalid entity: {entity}")

    # Filter facts by entity
    if entity == "all":
        filtered_facts = facts
    else:
        # Get facts matching this entity only
        filtered_facts = [
            f for f in facts
            if getattr(f, 'entity', None) == entity
        ]

    logger.info(f"Extracting drivers for entity={entity}: {len(filtered_facts)} facts (from {len(facts)} total)")

    drivers = DealDrivers(entity=entity)
    conflicts = []
    warnings = []

    # Track candidates for each driver (may have multiple sources)
    candidates: Dict[str, List[Tuple[Any, DriverSource]]] = {}

    # Track app counts by domain
    app_count = 0
    custom_app_count = 0
    saas_app_count = 0

    # Track parent-owned services
    parent_owned_services = []

    for fact in filtered_facts:
        fact_id = getattr(fact, 'fact_id', None) or getattr(fact, 'id', 'unknown')
        details = fact.details or {}
        item = fact.item or ''
        domain = fact.domain or ''
        category = fact.category or ''

        # Check for parent ownership
        is_parent_owned = _detect_parent_ownership(fact)

        # =================================================================
        # NUMERIC DRIVER EXTRACTION
        # =================================================================
        for field_path, driver_name, transform in FIELD_MAPPINGS:
            value = details.get(field_path)
            if value is not None:
                parsed = _parse_numeric(value, transform)
                if parsed is not None and parsed > 0:
                    source = DriverSource(
                        fact_id=fact_id,
                        fact_item=item,
                        field_path=f"details.{field_path}",
                        confidence=DriverConfidence.HIGH,
                        extraction_method="direct",
                    )
                    if driver_name not in candidates:
                        candidates[driver_name] = []
                    candidates[driver_name].append((parsed, source))

        # =================================================================
        # SYSTEM DETECTION
        # =================================================================
        combined_text = f"{item} {category} {str(details)}"

        for system_type in SYSTEM_MAPPINGS.keys():
            detected = _detect_system(combined_text, system_type)
            if detected:
                source = DriverSource(
                    fact_id=fact_id,
                    fact_item=item,
                    field_path="inferred",
                    confidence=DriverConfidence.MEDIUM,
                    extraction_method="inferred",
                )
                if system_type not in candidates:
                    candidates[system_type] = []
                candidates[system_type].append((detected, source))

                # Track parent ownership for specific systems
                if is_parent_owned:
                    if system_type == 'identity_provider':
                        parent_owned_services.append('identity')
                    elif system_type == 'erp_system':
                        parent_owned_services.append('erp')
                    elif system_type == 'soc_model':
                        parent_owned_services.append('soc')

        # =================================================================
        # APPLICATION COUNTING
        # =================================================================
        if domain == 'applications':
            app_count += 1
            cat_lower = category.lower() if category else ''
            if 'custom' in cat_lower or 'proprietary' in cat_lower:
                custom_app_count += 1
            elif 'saas' in cat_lower or 'cloud' in cat_lower:
                saas_app_count += 1

        # =================================================================
        # INFRASTRUCTURE OWNERSHIP
        # =================================================================
        if domain == 'infrastructure':
            if is_parent_owned:
                if 'data center' in item.lower() or 'dc' in category.lower():
                    parent_owned_services.append('dc')

        if domain == 'network':
            if is_parent_owned:
                if 'wan' in item.lower() or 'mpls' in item.lower():
                    parent_owned_services.append('wan')

    # =================================================================
    # RESOLVE CANDIDATES (pick best or flag conflict)
    # =================================================================
    drivers_extracted = 0

    for driver_name, candidate_list in candidates.items():
        if not candidate_list:
            continue

        # For numeric drivers, check for conflicts
        if driver_name in ['total_users', 'sites', 'it_headcount', 'servers', 'vms',
                           'endpoints', 'data_centers', 'erp_users', 'crm_users', 'vpn_users']:
            values = [c[0] for c in candidate_list]
            unique_values = set(values)

            if len(unique_values) > 1:
                # Conflict - multiple different values
                conflicts.append({
                    'driver': driver_name,
                    'values': list(unique_values),
                    'sources': [c[1].fact_id for c in candidate_list],
                })
                # Use highest confidence, then largest value
                candidate_list.sort(key=lambda x: (-['low', 'medium', 'high'].index(x[1].confidence.value.lower()), -x[0]))

            best_value, best_source = candidate_list[0]
            setattr(drivers, driver_name, best_value)
            drivers.sources[driver_name] = best_source
            drivers_extracted += 1

        else:
            # For string drivers, use first high-confidence match
            candidate_list.sort(key=lambda x: -['low', 'medium', 'high'].index(x[1].confidence.value.lower()))
            best_value, best_source = candidate_list[0]
            setattr(drivers, driver_name, best_value)
            drivers.sources[driver_name] = best_source
            drivers_extracted += 1

    # =================================================================
    # SET COUNTED VALUES
    # =================================================================
    if app_count > 0:
        drivers.total_apps = app_count
        drivers.sources['total_apps'] = DriverSource(
            confidence=DriverConfidence.HIGH,
            extraction_method="counted",
            notes=f"Counted {app_count} application facts",
        )
        drivers_extracted += 1

    if custom_app_count > 0:
        drivers.custom_apps = custom_app_count
        drivers.sources['custom_apps'] = DriverSource(
            confidence=DriverConfidence.MEDIUM,
            extraction_method="counted",
            notes=f"Counted {custom_app_count} custom/proprietary apps",
        )
        drivers_extracted += 1

    if saas_app_count > 0:
        drivers.saas_apps = saas_app_count
        drivers.sources['saas_apps'] = DriverSource(
            confidence=DriverConfidence.MEDIUM,
            extraction_method="counted",
            notes=f"Counted {saas_app_count} SaaS apps",
        )
        drivers_extracted += 1

    # =================================================================
    # SET OWNERSHIP DRIVERS
    # =================================================================
    parent_owned_services = list(set(parent_owned_services))
    drivers.shared_with_parent = parent_owned_services

    if 'identity' in parent_owned_services:
        drivers.identity_owned_by = OwnershipType.PARENT
    if 'dc' in parent_owned_services:
        drivers.dc_owned_by = OwnershipType.PARENT
    if 'wan' in parent_owned_services:
        drivers.wan_owned_by = OwnershipType.PARENT
    if 'erp' in parent_owned_services:
        drivers.erp_owned_by = OwnershipType.PARENT
    if 'soc' in parent_owned_services:
        drivers.soc_owned_by = OwnershipType.PARENT

    # =================================================================
    # APPLY DEFAULTS FOR MISSING CRITICAL DRIVERS
    # =================================================================
    drivers_assumed = 0

    # If we have endpoints but not users, estimate users
    if drivers.total_users is None and drivers.endpoints is not None:
        drivers.total_users = drivers.endpoints  # Rough 1:1
        drivers.sources['total_users'] = DriverSource(
            confidence=DriverConfidence.LOW,
            extraction_method="default",
            notes="Estimated from endpoint count (1:1 ratio)",
        )
        drivers_assumed += 1
        warnings.append("User count estimated from endpoints - verify with HR data")

    # If we have users but not identity_users, assume same
    if drivers.identity_users is None and drivers.total_users is not None:
        drivers.identity_users = drivers.total_users
        drivers.sources['identity_users'] = DriverSource(
            confidence=DriverConfidence.MEDIUM,
            extraction_method="inferred",
            notes="Set equal to total_users",
        )

    # If we have users but not endpoints, estimate endpoints
    if drivers.endpoints is None and drivers.total_users is not None:
        drivers.endpoints = int(drivers.total_users * 1.2)  # Some users have multiple devices
        drivers.sources['endpoints'] = DriverSource(
            confidence=DriverConfidence.LOW,
            extraction_method="default",
            notes="Estimated from user count (1.2 devices per user)",
        )
        drivers_assumed += 1

    # Default sites if not found
    if drivers.sites is None:
        drivers.sites = 1
        drivers.sources['sites'] = DriverSource(
            confidence=DriverConfidence.LOW,
            extraction_method="default",
            notes="Assumed single site - verify site count",
        )
        drivers_assumed += 1
        warnings.append("Site count defaulted to 1 - verify actual site count")

    # WAN sites defaults to sites
    if drivers.wan_sites is None and drivers.sites is not None:
        drivers.wan_sites = drivers.sites
        drivers.sources['wan_sites'] = DriverSource(
            confidence=DriverConfidence.MEDIUM,
            extraction_method="inferred",
            notes="Set equal to sites",
        )

    logger.info(
        f"Driver extraction complete: {drivers_extracted} extracted, "
        f"{drivers_assumed} assumed, {len(conflicts)} conflicts, "
        f"{len(parent_owned_services)} parent-owned services"
    )

    return DriverExtractionResult(
        drivers=drivers,
        facts_scanned=len(filtered_facts),
        drivers_extracted=drivers_extracted,
        drivers_assumed=drivers_assumed,
        conflicts=conflicts,
        warnings=warnings,
    )


def get_effective_drivers(deal_id: str, fact_store=None, db_session=None, entity: str = "target") -> DriverExtractionResult:
    """
    Get effective drivers for a deal: extracted values merged with any overrides.

    Args:
        deal_id: The deal ID
        fact_store: Optional FactStore (if not provided, loads from DB)
        db_session: Optional database session
        entity: Entity filter ("target", "buyer", or "all")

    Returns:
        DriverExtractionResult with entity-filtered drivers (overrides applied)
    """
    # Extract from facts
    if fact_store is not None:
        facts = getattr(fact_store, 'facts', [])
        if not facts:
            # Try alternative attribute names
            facts = getattr(fact_store, 'get_all_facts', lambda: [])()
    else:
        # Load from database
        try:
            from web.database import Fact
            facts = Fact.query.filter_by(deal_id=deal_id).all()
        except Exception as e:
            logger.warning(f"Could not load facts from DB: {e}")
            facts = []

    result = extract_drivers_from_facts(facts, deal_id, entity=entity)
    drivers = result.drivers
    overrides_applied = 0

    # Apply overrides from database
    try:
        from web.database import DriverOverride
        overrides = DriverOverride.query.filter_by(deal_id=deal_id, active=True).all()

        for override in overrides:
            driver_name = override.driver_name
            if hasattr(drivers, driver_name):
                # Get override value from JSON field
                override_val = override.override_value

                # Parse the override value appropriately based on current type
                current_value = getattr(drivers, driver_name)

                if isinstance(current_value, (int, type(None))) and not isinstance(current_value, bool):
                    new_value = _parse_numeric(override_val, int)
                elif isinstance(current_value, float):
                    new_value = _parse_numeric(override_val, float)
                elif isinstance(current_value, bool):
                    if isinstance(override_val, bool):
                        new_value = override_val
                    else:
                        new_value = str(override_val).lower() in ('true', '1', 'yes')
                else:
                    new_value = override_val

                setattr(drivers, driver_name, new_value)
                drivers.sources[driver_name] = DriverSource(
                    confidence=DriverConfidence.OVERRIDE,
                    extraction_method="override",
                    notes=f"Override: {override.reason or 'user correction'}",
                )
                overrides_applied += 1

        logger.info(f"Applied {overrides_applied} driver overrides for deal {deal_id}")

    except Exception as e:
        logger.warning(f"Could not load driver overrides: {e}")

    # Update result with override info
    return DriverExtractionResult(
        drivers=drivers,
        facts_scanned=result.facts_scanned,
        drivers_extracted=result.drivers_extracted,
        drivers_assumed=result.drivers_assumed,
        conflicts=result.conflicts,
        warnings=result.warnings,
    )


@property
def extracted_count(self) -> int:
    """Alias for drivers_extracted."""
    return self.drivers_extracted


@property
def assumed_count(self) -> int:
    """Alias for drivers_assumed."""
    return self.drivers_assumed


# Add these properties to DriverExtractionResult
DriverExtractionResult.extracted_count = property(lambda self: self.drivers_extracted)
DriverExtractionResult.assumed_count = property(lambda self: self.drivers_assumed)


# =============================================================================
# TSA COST DRIVER (CARVEOUT-SPECIFIC)
# =============================================================================

class TSACostDriver:
    """
    Calculate TSA costs for carve-out deals.

    TSAs are interim service agreements where parent provides services
    to carved-out entity during separation (6-24 months typical).
    """

    def estimate_monthly_tsa_cost(
        self,
        inventory_store,
        tsa_duration_months: int = 12
    ) -> float:
        """
        Estimate monthly TSA fees based on inventory complexity.

        Typical TSA services:
        - Datacenter hosting
        - Network connectivity
        - Shared application licenses
        - IT support services

        Industry benchmark: $50K-500K/month depending on scale

        Args:
            inventory_store: InventoryStore to check for shared services
            tsa_duration_months: Duration of TSA (default 12 months)

        Returns:
            Total TSA cost over the duration
        """
        # Count critical shared services
        shared_apps = 0
        shared_infra = 0

        try:
            # Check for applications hosted on parent infrastructure
            apps = inventory_store.get_items(inventory_type='application', entity='target')
            for app in apps:
                details = getattr(app, 'details', {}) or {}
                hosting = details.get('hosting', '').lower()
                if 'parent' in hosting or 'shared' in hosting or 'corporate' in hosting:
                    shared_apps += 1

            # Check for shared infrastructure
            infra = inventory_store.get_items(inventory_type='infrastructure', entity='target')
            for item in infra:
                details = getattr(item, 'details', {}) or {}
                ownership = details.get('ownership', '').lower()
                if 'parent' in ownership or 'shared' in ownership:
                    shared_infra += 1
        except Exception as e:
            logger.warning(f"Error counting shared services for TSA: {e}")
            # Use conservative defaults if inventory unavailable
            shared_apps = 5
            shared_infra = 3

        # Base cost per shared service
        cost_per_app = 5000    # $5K/month per application
        cost_per_infra = 10000 # $10K/month per infrastructure component

        monthly_cost = (shared_apps * cost_per_app) + (shared_infra * cost_per_infra)

        # Floor and ceiling
        monthly_cost = max(50000, min(monthly_cost, 500000))

        total_tsa_cost = monthly_cost * tsa_duration_months

        logger.info(
            f"TSA cost estimate: {shared_apps} shared apps, {shared_infra} shared infra, "
            f"${monthly_cost:,.0f}/month × {tsa_duration_months} months = ${total_tsa_cost:,.0f}"
        )

        return total_tsa_cost
