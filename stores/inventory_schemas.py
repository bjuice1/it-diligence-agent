"""
Inventory Schema Definitions

Defines the structure for different inventory types:
- Applications
- Infrastructure
- Organization
- Vendors

Each schema specifies required/optional fields and which fields
are used for content-based ID generation.
"""

from typing import Dict, List, Any

# ID prefixes for different inventory types
INVENTORY_PREFIXES = {
    "application": "APP",
    "infrastructure": "INFRA",
    "organization": "ORG",
    "vendor": "VENDOR",
}

# Schema definitions for each inventory type
INVENTORY_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "application": {
        "required": ["name"],
        "optional": [
            "vendor",
            "version",
            "hosting",          # on-prem, cloud, hybrid, saas
            "users",            # user count or description
            "cost",             # annual cost
            "cost_status",      # known | unknown | internal_no_cost | estimated
            "cost_quality_note", # free-form note explaining cost status
            "criticality",      # critical, high, medium, low
            "category",         # erp, crm, custom, etc.
            "contract_end",     # contract end date
            "owner",            # business owner
            "support_model",    # vendor, internal, hybrid
            "notes",
            "source_category",        # raw category string from source document
            "category_confidence",    # high, medium, low, none
            "category_inferred_from", # mapping_exact, mapping_alias, mapping_partial, keyword_inference, default
        ],
        "id_fields": ["name", "vendor"],  # Used for content-hashing
    },
    "infrastructure": {
        "required": ["name"],  # hostname, server name, etc.
        "optional": [
            "type",             # server, vm, container, network_device, storage
            "os",               # operating system
            "ip",               # IP address
            "location",         # data center, cloud region
            "environment",      # production, staging, dev, dr
            "cpu",              # CPU cores/specs
            "memory",           # RAM
            "storage",          # Storage capacity
            "role",             # database, web, app, etc.
            "notes",
        ],
        "id_fields": ["name", "environment"],
    },
    "organization": {
        "required": ["role"],  # job title or role name
        "optional": [
            "name",             # person's name (if known)
            "team",             # team name
            "department",       # IT, Security, Infrastructure, etc.
            "headcount",        # number of people in role
            "fte",              # FTE count
            "location",         # office location
            "reports_to",       # reporting line
            "responsibilities", # key responsibilities
            "notes",
        ],
        "id_fields": ["role", "team"],
    },
    "vendor": {
        "required": ["vendor_name"],
        "optional": [
            "contract_type",    # MSA, SOW, subscription, license
            "services",         # services provided
            "start_date",       # contract start
            "end_date",         # contract end
            "renewal_date",     # next renewal
            "acv",              # annual contract value
            "tcv",              # total contract value
            "owner",            # internal owner
            "auto_renew",       # auto-renewal terms
            "termination",      # termination notice period
            "notes",
        ],
        "id_fields": ["vendor_name", "contract_type"],
    },
}

# Enrichment categories for Application Intelligence
ENRICHMENT_CATEGORIES = [
    "industry_standard",    # Ubiquitous (Salesforce, Office 365, SAP)
    "vertical_specific",    # Common in industry (Duck Creek for insurance)
    "niche",                # Uncommon, specialized
    "unknown",              # Can't identify, needs research
    "custom",               # Built in-house
]

# Enrichment confidence levels
ENRICHMENT_CONFIDENCE = [
    "high",     # Confident in categorization
    "medium",   # Reasonably confident
    "low",      # Uncertain, needs verification
]

# Enrichment flags
ENRICHMENT_FLAGS = [
    None,           # No flag
    "investigate",  # Needs investigation
    "confirm",      # Needs confirmation from target
    "critical",     # Critical system, verify details
]

# Valid status values for inventory items
ITEM_STATUSES = [
    "active",       # Current, in use
    "removed",      # Marked as removed
    "deprecated",   # Being phased out
    "planned",      # Future addition
]

# Source types
SOURCE_TYPES = [
    "import",       # Imported from file
    "manual",       # Manually added by user
    "discovery",    # Extracted via LLM discovery
]


def get_schema(inventory_type: str) -> Dict[str, Any]:
    """
    Get schema for an inventory type.

    Args:
        inventory_type: One of: application, infrastructure, organization, vendor

    Returns:
        Schema dict with required, optional, and id_fields

    Raises:
        ValueError: If inventory_type is not recognized
    """
    if inventory_type not in INVENTORY_SCHEMAS:
        valid_types = list(INVENTORY_SCHEMAS.keys())
        raise ValueError(
            f"Unknown inventory type: {inventory_type}. "
            f"Valid types: {valid_types}"
        )
    return INVENTORY_SCHEMAS[inventory_type]


def get_id_fields(inventory_type: str) -> List[str]:
    """Get fields used for ID generation."""
    return get_schema(inventory_type)["id_fields"]


def get_required_fields(inventory_type: str) -> List[str]:
    """Get required fields for an inventory type."""
    return get_schema(inventory_type)["required"]


def get_optional_fields(inventory_type: str) -> List[str]:
    """Get optional fields for an inventory type."""
    return get_schema(inventory_type)["optional"]


def get_all_fields(inventory_type: str) -> List[str]:
    """Get all fields (required + optional) for an inventory type."""
    schema = get_schema(inventory_type)
    return schema["required"] + schema["optional"]


def validate_inventory_type(inventory_type: str) -> bool:
    """Check if inventory type is valid."""
    return inventory_type in INVENTORY_SCHEMAS


def get_prefix(inventory_type: str) -> str:
    """Get ID prefix for an inventory type."""
    if inventory_type not in INVENTORY_PREFIXES:
        raise ValueError(f"Unknown inventory type: {inventory_type}")
    return INVENTORY_PREFIXES[inventory_type]
