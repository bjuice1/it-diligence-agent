"""
Discovery Tools for V2 Architecture

Tools used by Discovery agents to extract facts from documents.
All facts go into the FactStore with unique IDs for later citation.

Tool Functions:
- create_inventory_entry: Extract a fact with evidence
- flag_gap: Identify missing information
- complete_discovery: Signal discovery phase complete
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from difflib import SequenceMatcher
import logging

if TYPE_CHECKING:
    from tools_v2.fact_store import FactStore

# Import config values
try:
    from config_v2 import (
        DUPLICATE_SIMILARITY_THRESHOLD,
        MIN_EVIDENCE_QUOTE_LENGTH,
        ENABLE_DUPLICATE_DETECTION,
        ENABLE_FACT_VALIDATION
    )
except ImportError:
    # Fallback defaults if config not available
    DUPLICATE_SIMILARITY_THRESHOLD = 0.85
    MIN_EVIDENCE_QUOTE_LENGTH = 10
    ENABLE_DUPLICATE_DETECTION = True
    ENABLE_FACT_VALIDATION = False

logger = logging.getLogger(__name__)

# =============================================================================
# DOMAIN CONFIGURATION
# =============================================================================

ALL_DOMAINS = [
    "infrastructure",
    "network",
    "cybersecurity",
    "applications",
    "organization",
    "identity_access"
]

# Domain-specific categories (used for validation)
DOMAIN_CATEGORIES = {
    "infrastructure": [
        "hosting", "compute", "storage", "backup_dr", "cloud", "legacy", "tooling"
    ],
    "network": [
        "wan", "lan", "remote_access", "dns_dhcp", "load_balancing", "network_security", "monitoring"
    ],
    "cybersecurity": [
        "endpoint", "perimeter", "detection", "vulnerability", "compliance", "incident_response", "governance"
    ],
    "applications": [
        "erp", "crm", "custom", "saas", "integration", "development", "database"
    ],
    "identity_access": [
        "directory", "authentication", "privileged_access", "provisioning", "sso", "mfa", "governance"
    ],
    "organization": [
        "structure", "staffing", "vendors", "skills", "processes", "budget", "roadmap"
    ]
}

# Status values
STATUS_VALUES = ["documented", "partial", "gap"]

# Gap importance levels
GAP_IMPORTANCE = ["critical", "high", "medium", "low"]


# =============================================================================
# TOOL DEFINITIONS (for Anthropic API)
# =============================================================================

DISCOVERY_TOOLS = [
    {
        "name": "create_inventory_entry",
        "description": """Record a fact discovered in the documentation.

        Use this to document what EXISTS in the IT environment.
        Every entry MUST include evidence (exact quote from the document).

        CRITICAL: You MUST specify the entity field to indicate whether this fact
        is about the TARGET company (being acquired) or the BUYER.
        - Check document headers/filenames for "target_profile" vs "buyer_profile"
        - Default to "target" if the document is about the company being acquired
        - Use "buyer" only when explicitly from buyer documentation

        This is EXTRACTION only - do not analyze or draw conclusions.
        The Reasoning phase will analyze these facts later.

        Returns a unique fact ID (e.g., F-INFRA-001) that can be cited in reasoning.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this fact relates to"
                },
                "category": {
                    "type": "string",
                    "description": "Category within domain (e.g., 'hosting', 'compute', 'wan', 'endpoint')"
                },
                "item": {
                    "type": "string",
                    "description": "What this fact is about (e.g., 'VMware Environment', 'Firewall Cluster', 'ERP System')"
                },
                "entity": {
                    "type": "string",
                    "enum": ["target", "buyer"],
                    "description": "CRITICAL: 'target' for acquisition target company, 'buyer' for acquiring company. Check document source carefully."
                },
                "details": {
                    "type": "object",
                    "description": "Key-value pairs of extracted information (vendor, version, count, capacity, etc.)",
                    "additionalProperties": True
                },
                "status": {
                    "type": "string",
                    "enum": STATUS_VALUES,
                    "description": "documented=complete info, partial=some info missing, gap=flagged as missing"
                },
                "evidence": {
                    "type": "object",
                    "description": "Source evidence for this fact",
                    "properties": {
                        "exact_quote": {
                            "type": "string",
                            "description": "Verbatim text from the document (REQUIRED, 10-500 chars)"
                        },
                        "source_section": {
                            "type": "string",
                            "description": "Section where this was found (e.g., 'Infrastructure Overview')"
                        }
                    },
                    "required": ["exact_quote"]
                }
            },
            "required": ["domain", "category", "item", "entity", "status", "evidence"]
        }
    },
    {
        "name": "flag_gap",
        "description": """Flag missing or incomplete information in the documentation.

        Use this when expected information is NOT present in the document.
        Gaps are important signals for the Reasoning phase about where uncertainty exists.

        Good gaps are specific: "No DR RTO/RPO defined" not "DR info incomplete".

        Returns a unique gap ID (e.g., G-INFRA-001).""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this gap relates to"
                },
                "category": {
                    "type": "string",
                    "description": "Category within domain where information is missing"
                },
                "description": {
                    "type": "string",
                    "description": "Specific description of what information is missing and why it matters"
                },
                "importance": {
                    "type": "string",
                    "enum": GAP_IMPORTANCE,
                    "description": "critical=deal-breaking, high=significant risk, medium=notable gap, low=nice to have"
                }
            },
            "required": ["domain", "category", "description", "importance"]
        }
    },
    {
        "name": "complete_discovery",
        "description": """Signal that discovery is complete for a domain.

        Call this after you have:
        1. Processed all relevant sections of the document
        2. Created inventory entries for all discovered facts
        3. Flagged gaps for all expected-but-missing information

        This allows the orchestrator to proceed to the Reasoning phase.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Domain that has been fully processed"
                },
                "categories_covered": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of categories that were found in the document"
                },
                "categories_missing": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of categories with no information (flagged as gaps)"
                },
                "summary": {
                    "type": "string",
                    "description": "Brief summary of what was discovered (1-2 sentences)"
                }
            },
            "required": ["domain", "categories_covered", "summary"]
        }
    }
]


# =============================================================================
# DUPLICATE DETECTION
# =============================================================================

def _check_fact_duplicate(
    fact_store: "FactStore",
    domain: str,
    category: str,
    item: str,
    threshold: float = DUPLICATE_SIMILARITY_THRESHOLD,
    entity: str = "target"
) -> Optional[Dict[str, Any]]:
    """
    Check if a similar fact already exists in the store.

    Args:
        fact_store: FactStore to check against
        domain: Domain of the new fact
        category: Category of the new fact
        item: Item description of the new fact
        threshold: Similarity threshold (0.0-1.0)
        entity: Entity of the new fact ("target" or "buyer")

    Returns:
        Existing fact dict if duplicate found, None otherwise

    Note:
        Duplicates are only checked within the same entity.
        The same item can exist for both target and buyer.
    """
    # Get facts from same domain, category, AND entity
    for fact in fact_store.facts:
        if fact.domain != domain:
            continue

        # Check category match (exact or same category)
        if fact.category != category:
            continue

        # Check entity match - allow same item for different entities
        if fact.entity != entity:
            continue

        # Compare item names using fuzzy matching
        existing_item = fact.item.lower().strip()
        new_item = item.lower().strip()

        # Exact match
        if existing_item == new_item:
            return fact.to_dict()

        # Fuzzy match
        similarity = SequenceMatcher(None, existing_item, new_item).ratio()
        if similarity >= threshold:
            logger.info(f"Duplicate detected: '{item}' similar to '{fact.item}' ({similarity:.2f}) [entity={entity}]")
            return fact.to_dict()

    return None


def _check_gap_duplicate(
    fact_store: "FactStore",
    domain: str,
    category: str,
    description: str,
    threshold: float = DUPLICATE_SIMILARITY_THRESHOLD
) -> Optional[Dict[str, Any]]:
    """
    Check if a similar gap already exists in the store.

    Args:
        fact_store: FactStore to check against
        domain: Domain of the new gap
        category: Category of the new gap
        description: Description of the new gap
        threshold: Similarity threshold (0.0-1.0)

    Returns:
        Existing gap dict if duplicate found, None otherwise
    """
    for gap in fact_store.gaps:
        if gap.domain != domain:
            continue

        if gap.category != category:
            continue

        # Compare descriptions
        existing_desc = gap.description.lower().strip()
        new_desc = description.lower().strip()

        # Exact match
        if existing_desc == new_desc:
            return gap.to_dict()

        # Fuzzy match
        similarity = SequenceMatcher(None, existing_desc, new_desc).ratio()
        if similarity >= threshold:
            logger.info(f"Duplicate gap detected: similarity {similarity:.2f}")
            return gap.to_dict()

    return None


# =============================================================================
# TOOL EXECUTION
# =============================================================================

def execute_discovery_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    fact_store: "FactStore"
) -> Dict[str, Any]:
    """
    Execute a discovery tool and store results in FactStore.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Tool input parameters
        fact_store: FactStore instance to record facts

    Returns:
        Dict with result status and any generated IDs
    """
    if tool_name == "create_inventory_entry":
        return _execute_create_inventory_entry(tool_input, fact_store)
    elif tool_name == "flag_gap":
        return _execute_flag_gap(tool_input, fact_store)
    elif tool_name == "complete_discovery":
        return _execute_complete_discovery(tool_input, fact_store)
    else:
        return {
            "status": "error",
            "message": f"Unknown discovery tool: {tool_name}"
        }


def _execute_create_inventory_entry(
    input_data: Dict[str, Any],
    fact_store: "FactStore"
) -> Dict[str, Any]:
    """Execute create_inventory_entry tool."""
    try:
        # Validate required fields
        domain = input_data.get("domain")
        category = input_data.get("category")
        item = input_data.get("item")
        entity = input_data.get("entity", "target")  # Default to target if not specified
        status = input_data.get("status", "documented")
        evidence = input_data.get("evidence", {})
        details = input_data.get("details", {})

        if not all([domain, category, item]):
            return {
                "status": "error",
                "message": "Missing required fields: domain, category, item"
            }

        # Validate entity
        if entity not in ("target", "buyer"):
            logger.warning(f"Invalid entity '{entity}', defaulting to 'target'")
            entity = "target"

        # Validate evidence
        exact_quote = evidence.get("exact_quote", "")
        if len(exact_quote) < MIN_EVIDENCE_QUOTE_LENGTH and status == "documented":
            return {
                "status": "error",
                "message": f"Evidence exact_quote must be at least {MIN_EVIDENCE_QUOTE_LENGTH} characters for documented facts"
            }
        
        # Optional: Validate quote exists in source document (if source available)
        # Note: This requires source document text, which may not always be available
        # during discovery. Validation can be done later during review phase.
        if ENABLE_FACT_VALIDATION and exact_quote:
            # For now, we don't have source document text in discovery phase
            # This validation would need to be done post-discovery with document text
            # Just log that validation would be beneficial
            logger.debug(f"Evidence quote provided: {exact_quote[:50]}... (validation deferred)")

        # Sanitize inputs before storing
        try:
            from tools_v2.input_sanitizer import sanitize_input
            item = sanitize_input(item)
            details = sanitize_input(details)
            evidence = sanitize_input(evidence)
        except ImportError:
            # Sanitizer not available, continue without sanitization
            pass

        # Check for duplicates (if enabled) - also check entity to allow same item for both
        if ENABLE_DUPLICATE_DETECTION:
            duplicate = _check_fact_duplicate(fact_store, domain, category, item, entity=entity)
            if duplicate:
                return {
                    "status": "duplicate",
                    "fact_id": duplicate["fact_id"],
                    "message": f"Similar fact already exists: {duplicate['fact_id']} - {duplicate['item']}"
                }

        # Add fact to store
        fact_id = fact_store.add_fact(
            domain=domain,
            category=category,
            item=item,
            details=details,
            status=status,
            evidence=evidence,
            entity=entity
        )

        entity_label = "TARGET" if entity == "target" else "BUYER"
        logger.debug(f"Created inventory entry: {fact_id} - {item} [{entity_label}]")

        return {
            "status": "success",
            "fact_id": fact_id,
            "entity": entity,
            "message": f"Recorded [{entity_label}]: {item} ({category})"
        }

    except Exception as e:
        logger.error(f"Error in create_inventory_entry: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def _execute_flag_gap(
    input_data: Dict[str, Any],
    fact_store: "FactStore"
) -> Dict[str, Any]:
    """Execute flag_gap tool."""
    try:
        domain = input_data.get("domain")
        category = input_data.get("category")
        description = input_data.get("description")
        importance = input_data.get("importance", "medium")

        if not all([domain, category, description]):
            return {
                "status": "error",
                "message": "Missing required fields: domain, category, description"
            }

        # Check for duplicates (if enabled)
        if ENABLE_DUPLICATE_DETECTION:
            duplicate = _check_gap_duplicate(fact_store, domain, category, description)
            if duplicate:
                return {
                    "status": "duplicate",
                    "gap_id": duplicate["gap_id"],
                    "message": f"Similar gap already exists: {duplicate['gap_id']}"
                }

        # Add gap to store
        gap_id = fact_store.add_gap(
            domain=domain,
            category=category,
            description=description,
            importance=importance
        )

        logger.debug(f"Flagged gap: {gap_id} - {description[:50]}...")

        return {
            "status": "success",
            "gap_id": gap_id,
            "message": f"Gap flagged: {description[:50]}..."
        }

    except Exception as e:
        logger.error(f"Error in flag_gap: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def _execute_complete_discovery(
    input_data: Dict[str, Any],
    fact_store: "FactStore"
) -> Dict[str, Any]:
    """Execute complete_discovery tool."""
    try:
        domain = input_data.get("domain")
        categories_covered = input_data.get("categories_covered", [])
        categories_missing = input_data.get("categories_missing", [])
        _ = input_data.get("summary", "")

        if not domain:
            return {
                "status": "error",
                "message": "Missing required field: domain"
            }

        # Mark discovery complete for this domain
        fact_store.mark_discovery_complete(
            domain=domain,
            categories_covered=categories_covered,
            categories_missing=categories_missing
        )

        # Get stats for this domain
        domain_data = fact_store.get_domain_facts(domain)

        logger.info(f"Discovery complete for {domain}: {domain_data['fact_count']} facts, {domain_data['gap_count']} gaps")

        return {
            "status": "success",
            "domain": domain,
            "fact_count": domain_data["fact_count"],
            "gap_count": domain_data["gap_count"],
            "categories_covered": categories_covered,
            "message": f"Discovery complete: {domain_data['fact_count']} facts, {domain_data['gap_count']} gaps"
        }

    except Exception as e:
        logger.error(f"Error in complete_discovery: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_discovery_tools_for_domain(domain: str) -> List[Dict]:
    """
    Get discovery tools filtered/configured for a specific domain.

    Currently returns all tools - could be extended to customize
    descriptions or add domain-specific validation.
    """
    return DISCOVERY_TOOLS


def validate_discovery_input(tool_name: str, tool_input: Dict) -> Optional[str]:
    """
    Validate tool input before execution.

    Returns error message if invalid, None if valid.
    """
    if tool_name == "create_inventory_entry":
        required = ["domain", "category", "item", "entity", "status", "evidence"]
        for field in required:
            if field not in tool_input:
                return f"Missing required field: {field}"

        # Validate entity value
        entity = tool_input.get("entity")
        if entity not in ("target", "buyer"):
            return f"Invalid entity value: {entity}. Must be 'target' or 'buyer'"

        evidence = tool_input.get("evidence", {})
        if "exact_quote" not in evidence:
            return "Evidence must include exact_quote"

    elif tool_name == "flag_gap":
        required = ["domain", "category", "description", "importance"]
        for field in required:
            if field not in tool_input:
                return f"Missing required field: {field}"

    elif tool_name == "complete_discovery":
        if "domain" not in tool_input:
            return "Missing required field: domain"

    return None
