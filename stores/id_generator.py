"""
Content-Based ID Generation

Generates stable IDs from content hash to ensure consistency across:
- Re-imports of the same data
- Multiple sessions
- Save/load cycles

IDs are deterministic: same content always produces same ID.
"""

import hashlib
from typing import Dict, Any, List

from stores.inventory_schemas import (
    INVENTORY_PREFIXES,
    get_id_fields,
    validate_inventory_type,
)

# Domain prefixes for facts (matching existing fact_store.py)
FACT_DOMAIN_PREFIXES = {
    "infrastructure": "INFRA",
    "network": "NET",
    "cybersecurity": "CYBER",
    "applications": "APP",
    "identity_access": "IAM",
    "organization": "ORG",
    "general": "GEN",
}


def generate_inventory_id(
    inventory_type: str,
    data: Dict[str, Any],
    entity: str = "target",
    deal_id: str = ""
) -> str:
    """
    Generate stable inventory item ID from content hash.

    Same item always gets same ID, regardless of import order or session.
    Including deal_id ensures items with same content in different deals
    get different IDs (proper isolation).

    NOTE: Empty/null optional fields are normalized to "unspecified" to
    ensure deterministic hashing. This prevents fingerprint collisions
    when optional fields (vendor, environment, team, contract_type) are
    missing or inconsistent across source documents.

    Args:
        inventory_type: One of: application, infrastructure, organization, vendor
        data: Item data dict containing at least the id_fields for the type
        entity: "target" or "buyer"
        deal_id: Deal ID for scoping (ensures cross-deal uniqueness)

    Returns:
        ID like "I-APP-a3f291" (prefix + 6-char hash)

    Raises:
        ValueError: If inventory_type is invalid

    Example:
        >>> generate_inventory_id("application", {"name": "Salesforce", "vendor": "Salesforce"}, "target", "deal-123")
        'I-APP-7b3c91'
    """
    if not validate_inventory_type(inventory_type):
        raise ValueError(f"Invalid inventory type: {inventory_type}")

    # Get fields used for ID generation
    id_fields = get_id_fields(inventory_type)

    # Build content string from key fields
    # Include deal_id FIRST to ensure different deals get different IDs
    parts = [deal_id, inventory_type, entity]
    for field in id_fields:
        value = data.get(field, "")
        # Normalize: lowercase, strip whitespace
        # Use sentinel value for empty optional fields to ensure stable hashing
        normalized = str(value).lower().strip() if value else "unspecified"
        parts.append(normalized)

    # Create hash
    content = "|".join(parts)
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:6]

    # Get prefix
    prefix = INVENTORY_PREFIXES[inventory_type]

    return f"I-{prefix}-{hash_val}"


def generate_fact_id(
    domain: str,
    observation: str,
    entity: str = "target",
    source_document: str = ""
) -> str:
    """
    Generate stable fact ID from content hash.

    Facts are observations from unstructured content. The ID is based on
    the domain, observation text, entity, and optionally the source document.

    Args:
        domain: One of: infrastructure, network, cybersecurity, applications,
                identity_access, organization, general
        observation: The observation text (what was observed)
        entity: "target" or "buyer"
        source_document: Optional source filename for disambiguation

    Returns:
        ID like "F-CYBER-a3f291" (prefix + 6-char hash)

    Raises:
        ValueError: If domain is not recognized

    Example:
        >>> generate_fact_id("cybersecurity", "MFA not enabled for admin accounts", "target")
        'F-CYBER-8d2a91'
    """
    if domain not in FACT_DOMAIN_PREFIXES:
        raise ValueError(
            f"Invalid domain: {domain}. "
            f"Valid domains: {list(FACT_DOMAIN_PREFIXES.keys())}"
        )

    # Build content string
    # Normalize observation: lowercase, strip, collapse whitespace
    normalized_obs = " ".join(observation.lower().strip().split())

    parts = [domain, entity, normalized_obs]
    if source_document:
        parts.append(source_document.lower().strip())

    # Create hash
    content = "|".join(parts)
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:6]

    # Get prefix
    prefix = FACT_DOMAIN_PREFIXES[domain]

    return f"F-{prefix}-{hash_val}"


def generate_gap_id(
    domain: str,
    description: str,
    entity: str = "target"
) -> str:
    """
    Generate stable gap ID from content hash.

    Args:
        domain: The domain this gap belongs to
        description: Description of the gap
        entity: "target" or "buyer"

    Returns:
        ID like "G-CYBER-a3f291"
    """
    if domain not in FACT_DOMAIN_PREFIXES:
        raise ValueError(f"Invalid domain: {domain}")

    # Normalize description
    normalized_desc = " ".join(description.lower().strip().split())

    parts = [domain, entity, normalized_desc]
    content = "|".join(parts)
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:6]

    prefix = FACT_DOMAIN_PREFIXES[domain]
    return f"G-{prefix}-{hash_val}"


def is_inventory_id(item_id: str) -> bool:
    """Check if an ID is an inventory item ID (starts with I-)."""
    return item_id.startswith("I-")


def is_fact_id(item_id: str) -> bool:
    """Check if an ID is a fact ID (starts with F-)."""
    return item_id.startswith("F-")


def is_gap_id(item_id: str) -> bool:
    """Check if an ID is a gap ID (starts with G-)."""
    return item_id.startswith("G-")


def parse_id(item_id: str) -> Dict[str, str]:
    """
    Parse an ID into its components.

    Args:
        item_id: An ID like "I-APP-a3f291" or "F-CYBER-8d2a91"

    Returns:
        Dict with:
        - type: "inventory", "fact", or "gap"
        - prefix: The domain/type prefix (APP, CYBER, etc.)
        - hash: The hash portion

    Raises:
        ValueError: If ID format is invalid
    """
    parts = item_id.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid ID format: {item_id}")

    type_char, prefix, hash_val = parts

    if type_char == "I":
        id_type = "inventory"
    elif type_char == "F":
        id_type = "fact"
    elif type_char == "G":
        id_type = "gap"
    else:
        raise ValueError(f"Unknown ID type: {type_char}")

    return {
        "type": id_type,
        "prefix": prefix,
        "hash": hash_val,
    }


def ids_match(id1: str, id2: str) -> bool:
    """
    Check if two IDs refer to the same item.

    This is a simple equality check, but exists for clarity and
    potential future fuzzy matching.
    """
    return id1 == id2
