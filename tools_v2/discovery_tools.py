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
import json

if TYPE_CHECKING:
    from stores.fact_store import FactStore

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

# Import shared cost status utility
from utils.cost_status_inference import infer_cost_status, normalize_numeric

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
        "leadership", "central_it", "roles", "app_teams", "outsourcing",
        "embedded_it", "shadow_it", "key_individuals", "skills", "budget"
    ]
}

# Status values
STATUS_VALUES = ["documented", "partial", "gap"]

# Gap importance levels
GAP_IMPORTANCE = ["critical", "high", "medium", "low"]


# =============================================================================
# APPLICATION NAME VALIDATION
# =============================================================================

# Field label patterns that indicate parsing errors (item contains a label, not a name)
FIELD_LABEL_PATTERNS = [
    r'^\*{0,2}name\*{0,2}\s*:',        # **Name**: or Name:
    r'^\*{0,2}vendor\*{0,2}\s*:',      # **Vendor**: or Vendor:
    r'^\*{0,2}version\*{0,2}\s*:',     # **Version**: or Version:
    r'^\*{0,2}users?\*{0,2}\s*:',      # **Users**: or User:
    r'^\*{0,2}criticality\*{0,2}\s*:', # **Criticality**:
    r'^\*{0,2}deployment\*{0,2}\s*:',  # **Deployment**:
    r'^\*{0,2}license\*{0,2}\s*:',     # **License**:
    r'^\*{0,2}contract\*{0,2}\s*:',    # **Contract**:
    r'^\*{0,2}status\*{0,2}\s*:',      # **Status**:
    r'^\*{0,2}type\*{0,2}\s*:',        # **Type**:
    r'^\*{0,2}category\*{0,2}\s*:',    # **Category**:
    r'^\*{0,2}description\*{0,2}\s*:', # **Description**:
    r'^\*{0,2}technology\*{0,2}\s*:',  # **Technology**:
    r'^\*{0,2}deployed\*{0,2}\s*:',    # **Deployed**:
    r'^\*{0,2}modules?\*{0,2}\s*:',    # **Modules**:
    r'^\*{0,2}integrations?\*{0,2}\s*:', # **Integrations**:
]

# Minimum required details for applications domain
# Must have item (name) + at least one of these detail fields
APPLICATION_MINIMUM_DETAIL_FIELDS = [
    'vendor', 'version', 'deployment', 'user_count', 'users',
    'criticality', 'license_type', 'modules', 'technology_stack'
]


def validate_application_name(item: str) -> tuple[bool, str]:
    """
    Validate that an application name is actually an application name,
    not a field label that was incorrectly parsed.

    Args:
        item: The item/name field from the inventory entry

    Returns:
        Tuple of (is_valid, rejection_reason)
        - (True, "") if valid
        - (False, "reason") if invalid
    """
    import re

    if not item:
        return False, "Item name is empty"

    item_lower = item.lower().strip()

    # Check against field label patterns
    for pattern in FIELD_LABEL_PATTERNS:
        if re.match(pattern, item_lower, re.IGNORECASE):
            return False, f"Item appears to be a field label, not an application name: '{item}'"

    # Check for common field label keywords at the start
    label_keywords = ['name', 'vendor', 'version', 'users', 'user', 'criticality',
                      'deployment', 'license', 'contract', 'status', 'type',
                      'category', 'description', 'technology', 'deployed', 'modules']

    # If item starts with a label keyword followed by : or -, it's likely a field label
    for keyword in label_keywords:
        if item_lower.startswith(keyword) and len(item_lower) > len(keyword):
            next_char = item_lower[len(keyword)]
            if next_char in [':', '-', ' ']:
                # Check if there's actual content after
                rest = item_lower[len(keyword):].lstrip(':- ')
                if rest:
                    return False, f"Item appears to be a field label with value: '{item}'. Use the value '{rest}' as the item name instead."

    # Check minimum length (after stripping markdown)
    clean_name = re.sub(r'[\*\#\-\_]', '', item).strip()
    if len(clean_name) < 2:
        return False, f"Item name too short after cleanup: '{clean_name}'"

    return True, ""


def validate_application_completeness(item: str, details: dict) -> tuple[bool, str, bool]:
    """
    Check if an application entry has sufficient details to be useful.

    Args:
        item: The application name
        details: The details dictionary

    Returns:
        Tuple of (is_valid, message, needs_review)
        - is_valid: Whether to accept the entry
        - message: Validation message
        - needs_review: Whether to flag for human review
    """
    if not details:
        # No details at all - flag for review but accept
        return True, "No details provided - flagged for review", True

    # Check if at least one meaningful detail field is present
    has_meaningful_detail = False
    for field in APPLICATION_MINIMUM_DETAIL_FIELDS:
        if field in details and details[field]:
            has_meaningful_detail = True
            break

    if not has_meaningful_detail:
        # Accept but flag for review
        return True, f"Application '{item}' has no vendor, version, or deployment info - flagged for review", True

    return True, "", False


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
                },
                "source_document": {
                    "type": "string",
                    "description": "Filename of the source document this fact was extracted from (e.g., 'IT_Asset_Inventory.xlsx'). IMPORTANT for traceability."
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

        CRITICAL: You MUST specify the entity field to indicate whether this gap
        is about the TARGET company (being acquired) or the BUYER.

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
                },
                "entity": {
                    "type": "string",
                    "enum": ["target", "buyer"],
                    "description": "REQUIRED: 'target' for acquisition target company, 'buyer' for acquiring company. Must be explicitly specified."
                }
            },
            "required": ["domain", "category", "description", "importance", "entity"]
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
    # Handle case where tool_input is a string (sometimes happens with LLM responses)
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            logger.error(f"Tool input is a string and not valid JSON: {tool_input[:100]}")
            return {
                "status": "error",
                "message": "Tool input must be a dictionary, not a string. Please provide structured parameters."
            }

    if not isinstance(tool_input, dict):
        logger.error(f"Tool input is not a dictionary: {type(tool_input)}")
        return {
            "status": "error",
            "message": f"Tool input must be a dictionary, got {type(tool_input).__name__}"
        }

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
        entity = input_data.get("entity")
        if entity is None:
            logger.warning(f"REJECTED create_inventory_entry: entity not specified for '{input_data.get('item', 'unknown')}'")
            return {
                "status": "error",
                "reason": "missing_entity",
                "message": "Entity is REQUIRED for create_inventory_entry. Must be 'target' or 'buyer'. "
                           "Check the document source — target_profile docs → entity='target', "
                           "buyer_profile docs → entity='buyer'. Do not omit this field."
            }
        status = input_data.get("status", "documented")
        evidence = input_data.get("evidence", {})
        details = input_data.get("details", {})
        source_document = input_data.get("source_document", "")  # Track source document for traceability

        # Handle case where evidence/details are strings instead of dicts
        if isinstance(evidence, str):
            try:
                evidence = json.loads(evidence)
            except json.JSONDecodeError:
                # If it's a plain string, treat it as the exact_quote
                evidence = {"exact_quote": evidence}

        if isinstance(details, str):
            try:
                details = json.loads(details)
            except json.JSONDecodeError:
                details = {"raw": details}

        if not all([domain, category, item]):
            return {
                "status": "error",
                "message": "Missing required fields: domain, category, item"
            }

        # Validate entity - CRITICAL: No silent defaults
        # Entity confusion corrupts the entire analysis
        if entity not in ("target", "buyer"):
            logger.error(f"REJECTED: Invalid entity '{entity}'. Must be 'target' or 'buyer'.")
            return {
                "status": "error",
                "reason": "invalid_entity",
                "message": f"Invalid entity '{entity}'. Must be exactly 'target' or 'buyer'. "
                           f"Entity is determined by document upload location, not inference. "
                           f"Check the source document's entity designation."
            }

        # =================================================================
        # APPLICATION NAME VALIDATION (for applications domain)
        # =================================================================
        needs_review = False

        if domain == "applications":
            # Check if item looks like a field label instead of an app name
            is_valid_name, rejection_reason = validate_application_name(item)
            if not is_valid_name:
                logger.warning(f"REJECTED application entry: {rejection_reason}")
                return {
                    "status": "rejected",
                    "reason": "invalid_name",
                    "message": f"REJECTED: {rejection_reason}. Please extract the actual application name, not the field label."
                }

            # Check if entry has sufficient details
            is_complete, completeness_msg, flag_for_review = validate_application_completeness(item, details)
            if flag_for_review:
                needs_review = True
                logger.info(f"Application flagged for review: {completeness_msg}")

        # =================================================================
        # END APPLICATION VALIDATION
        # =================================================================

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

        # =================================================================
        # COST STATUS INFERENCE (for applications domain)
        # =================================================================
        if domain == "applications" and isinstance(details, dict):
            # Check for cost-related fields in details
            cost_fields = ['cost', 'annual_cost', 'license_cost', 'annual_license_cost']
            cost_value = None
            original_cost_value = None

            for field in cost_fields:
                if field in details:
                    original_cost_value = details[field]
                    # Normalize the cost value
                    cost_value = normalize_numeric(str(original_cost_value)) if original_cost_value else None
                    break

            # If cost information exists, infer status
            if original_cost_value is not None:
                vendor_name = details.get('vendor') or details.get('provider') or details.get('supplier')
                cost_status, cost_note = infer_cost_status(
                    cost_value=cost_value,
                    vendor_name=vendor_name,
                    original_value=str(original_cost_value)
                )
                details['cost_status'] = cost_status
                if cost_note:
                    details['cost_quality_note'] = cost_note

                # Store normalized cost if available
                if cost_value is not None:
                    details['cost'] = cost_value

                logger.debug(f"Application '{item}': cost_status='{cost_status}' (cost={original_cost_value})")
        # =================================================================
        # END COST STATUS INFERENCE
        # =================================================================

        # Add fact to store (with needs_review flag if applicable)
        fact_id = fact_store.add_fact(
            domain=domain,
            category=category,
            item=item,
            details=details,
            status=status,
            evidence=evidence,
            entity=entity,
            source_document=source_document,
            needs_review=needs_review
        )

        entity_label = "TARGET" if entity == "target" else "BUYER"
        logger.debug(f"Created inventory entry: {fact_id} - {item} [{entity_label}]" + (" [NEEDS REVIEW]" if needs_review else ""))

        result = {
            "status": "success",
            "fact_id": fact_id,
            "entity": entity,
            "message": f"Recorded [{entity_label}]: {item} ({category})"
        }

        if needs_review:
            result["needs_review"] = True
            result["message"] += " [FLAGGED FOR REVIEW - sparse details]"

        return result

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

        # Entity is REQUIRED - no silent default to "target"
        entity = input_data.get("entity")
        if entity is None:
            return {
                "status": "error",
                "message": "Entity is required for flag_gap. Must be 'target' or 'buyer'. "
                           "Do not omit this field — explicitly specify which entity this gap belongs to."
            }
        if entity not in ("target", "buyer"):
            return {
                "status": "error",
                "message": f"Invalid entity '{entity}'. Must be 'target' or 'buyer'."
            }

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

        # Add gap to store with entity (critical for two-phase separation)
        gap_id = fact_store.add_gap(
            domain=domain,
            category=category,
            description=description,
            importance=importance,
            entity=entity  # Pass entity to maintain target/buyer separation
        )

        logger.debug(f"Flagged gap: {gap_id} [{entity}] - {description[:50]}...")

        return {
            "status": "success",
            "gap_id": gap_id,
            "entity": entity,
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

        # Get stats for this domain BEFORE marking complete
        domain_data = fact_store.get_domain_facts(domain)

        # =================================================================
        # COMPLETENESS VALIDATION
        # =================================================================
        warnings = []

        # =================================================================
        # APPLICATIONS DOMAIN VALIDATION
        # =================================================================
        if domain == "applications":
            app_facts = [f for f in domain_data.get("facts", [])
                        if f.get("domain") == "applications"]
            app_count = len(app_facts)

            # Add verification reminder - the key is extracting EVERYTHING in the document
            # not hitting an arbitrary number
            warnings.append(
                f"✓ Extracted {app_count} applications. "
                f"VERIFY: Did you extract EVERY application from the document? "
                f"Check 'Complete Application List' tables and ensure ALL rows were captured. "
                f"If the document states 'Total Applications: XX', your count should match."
            )

            # Check category coverage to identify potential gaps
            categories_found = set(f.get("category") for f in app_facts if f.get("category"))

            # Common application categories that should typically be present
            common_categories = {
                "erp": "ERP (Oracle, SAP, NetSuite)",
                "crm": "CRM (Salesforce, Dynamics)",
                "hcm": "HR/HCM (Workday, ADP)",
                "vertical": "Industry/Vertical apps",
                "collaboration": "Collaboration (M365, Slack)",
                "finance": "Finance (BlackLine, Coupa)"
            }

            missing_categories = []
            for cat, desc in common_categories.items():
                if cat not in categories_found:
                    missing_categories.append(desc)

            if missing_categories:
                warnings.append(
                    f"Categories not found: {', '.join(missing_categories)}. "
                    f"If the document mentions applications in these categories, go back and extract them."
                )

        # =================================================================
        # ORGANIZATION DOMAIN VALIDATION
        # =================================================================
        elif domain == "organization":
            # Count central_it (team) entries
            central_it_facts = [f for f in domain_data.get("facts", [])
                               if f.get("category") == "central_it"]
            team_count = len(central_it_facts)

            # Typical Team Summary tables have 5-7 teams
            # Warn if fewer than 5 teams extracted
            if team_count < 5:
                warnings.append(
                    f"WARNING: Only {team_count} central_it teams extracted. "
                    f"Most Team Summary tables have 5-7 teams (Applications, Infrastructure, "
                    f"Security & Compliance, Service Desk, Data & Analytics, PMO, IT Leadership). "
                    f"Did you extract ALL teams?"
                )
                logger.warning(f"Organization completeness check: only {team_count} teams")

            # Check if common teams are present
            extracted_team_names = {f.get("item", "").lower() for f in central_it_facts}
            expected_teams = ["applications", "infrastructure", "security", "service desk",
                            "data", "pmo", "it leadership"]
            missing_common_teams = [t for t in expected_teams
                                   if not any(t in name for name in extracted_team_names)]
            if missing_common_teams:
                warnings.append(
                    f"NOTE: Common teams that may be missing: {', '.join(missing_common_teams)}. "
                    f"Check if these exist in the Team Summary table."
                )

            # Count roles entries
            roles_facts = [f for f in domain_data.get("facts", [])
                          if f.get("category") == "roles"]
            if len(roles_facts) == 0:
                warnings.append(
                    "NOTE: No 'roles' category facts extracted. "
                    "If there's a Role & Compensation Breakdown table, extract those rows."
                )

        # Mark discovery complete for this domain
        fact_store.mark_discovery_complete(
            domain=domain,
            categories_covered=categories_covered,
            categories_missing=categories_missing
        )

        logger.info(f"Discovery complete for {domain}: {domain_data['fact_count']} facts, {domain_data['gap_count']} gaps")

        result = {
            "status": "success",
            "domain": domain,
            "fact_count": domain_data["fact_count"],
            "gap_count": domain_data["gap_count"],
            "categories_covered": categories_covered,
            "message": f"Discovery complete: {domain_data['fact_count']} facts, {domain_data['gap_count']} gaps"
        }

        # Add warnings if any
        if warnings:
            result["warnings"] = warnings
            result["message"] += "\n\n" + "\n".join(warnings)

        return result

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


def get_application_validation_summary(fact_store: "FactStore") -> Dict[str, Any]:
    """
    Get a summary of application validation results.

    Args:
        fact_store: FactStore containing application facts

    Returns:
        Dictionary with validation statistics:
        - total: Total application entries
        - high_confidence: Entries with confidence >= 0.6
        - needs_review: Entries flagged for review
        - low_confidence: Entries with low confidence
        - by_category: Breakdown by application category
    """
    summary = {
        "total": 0,
        "high_confidence": 0,
        "needs_review": 0,
        "low_confidence": 0,
        "by_category": {},
        "review_reasons": [],
    }

    if not fact_store or not fact_store.facts:
        return summary

    # Filter to applications domain
    app_facts = [f for f in fact_store.facts if f.domain == "applications"]

    for fact in app_facts:
        summary["total"] += 1
        category = fact.category or "other"

        # Initialize category if needed
        if category not in summary["by_category"]:
            summary["by_category"][category] = {
                "total": 0,
                "high_confidence": 0,
                "needs_review": 0,
            }

        summary["by_category"][category]["total"] += 1

        # Check confidence and review status
        needs_review = getattr(fact, 'needs_review', False)
        confidence = getattr(fact, 'confidence_score', 0.0)

        if needs_review:
            summary["needs_review"] += 1
            summary["by_category"][category]["needs_review"] += 1
            reason = getattr(fact, 'needs_review_reason', '')
            if reason:
                summary["review_reasons"].append({
                    "item": fact.item,
                    "fact_id": fact.fact_id,
                    "reason": reason,
                })
        elif confidence >= 0.6:
            summary["high_confidence"] += 1
            summary["by_category"][category]["high_confidence"] += 1
        else:
            summary["low_confidence"] += 1

    return summary


def format_validation_summary(summary: Dict[str, Any]) -> str:
    """
    Format validation summary as a readable string.

    Args:
        summary: Validation summary from get_application_validation_summary

    Returns:
        Formatted string for display
    """
    lines = [
        "=" * 50,
        "APPLICATION INVENTORY VALIDATION SUMMARY",
        "=" * 50,
        "",
        f"Total Applications: {summary['total']}",
        f"  ✅ High Confidence: {summary['high_confidence']}",
        f"  ⚠️  Needs Review:   {summary['needs_review']}",
        f"  ❓ Low Confidence:  {summary['low_confidence']}",
        "",
    ]

    if summary['by_category']:
        lines.append("By Category:")
        for cat, stats in sorted(summary['by_category'].items()):
            review_flag = f" (⚠️{stats['needs_review']})" if stats['needs_review'] > 0 else ""
            lines.append(f"  - {cat}: {stats['total']}{review_flag}")
        lines.append("")

    if summary['review_reasons']:
        lines.append("Items Needing Review:")
        for item in summary['review_reasons'][:10]:  # Show first 10
            lines.append(f"  - {item['item']} ({item['fact_id']}): {item['reason']}")
        if len(summary['review_reasons']) > 10:
            lines.append(f"  ... and {len(summary['review_reasons']) - 10} more")
        lines.append("")

    lines.append("=" * 50)

    return "\n".join(lines)
