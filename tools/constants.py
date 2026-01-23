"""
Shared Constants for IT Due Diligence Agent

Cross-cutting values used across multiple modules.
Centralizes "Unknown", "N/A", and other standard values.

Version: 1.0
Phase: 1 (Foundation & Architecture)
"""

# =============================================================================
# UNKNOWN/N/A STANDARDS
# =============================================================================

# Standard "Unknown" value for enum fields
# Use when information is not available in documentation
UNKNOWN = "Unknown"

# Standard "Not Applicable" value
# Use when a field/capability doesn't apply to this business
NOT_APPLICABLE = "Not_Applicable"

# Standard "None" representation for optional strings
# Use when a field is intentionally empty (not missing, just none)
NONE_PROVIDED = "None_Provided"


# =============================================================================
# FIELD NOT DOCUMENTED MARKERS
# =============================================================================

# Use when a field couldn't be populated from available docs
FIELD_NOT_DOCUMENTED = "[Not documented]"

# Use when explicitly stated as not available
EXPLICITLY_UNAVAILABLE = "[Explicitly stated as unavailable]"

# Use when information needs to be requested
NEEDS_FOLLOW_UP = "[Requires follow-up]"


# =============================================================================
# ID PREFIXES
# =============================================================================

# Existing prefixes
ID_PREFIXES = {
    # Application inventory
    "application": "APP",
    "capability": "CAP",
    "buyer_application": "BAPP",
    "overlap": "OVL",

    # Four-lens framework
    "current_state": "CS",
    "risk": "R",
    "strategic_consideration": "SC",
    "work_item": "WI",
    "recommendation": "REC",

    # Supporting
    "assumption": "A",
    "gap": "G",
    "question": "Q",

    # Planned additions (Phases 7-12)
    "business_context": "BC",
    "eol_assessment": "EOL",
    "technical_debt": "TD",
    "contract": "CON"
}


# =============================================================================
# PROMPT VERSIONING
# =============================================================================

PROMPT_VERSIONS = {
    "applications_prompt": "1.1",
    "identity_access_prompt": "1.0",
    "infrastructure_prompt": "1.0",
    "network_prompt": "1.0",
    "cybersecurity_prompt": "1.0",
    "organization_prompt": "1.0",
    "dd_reasoning_framework": "2.0"
}

def get_prompt_version(prompt_name: str) -> str:
    """Get the version of a specific prompt."""
    return PROMPT_VERSIONS.get(prompt_name, "Unknown")

def get_all_prompt_versions() -> dict:
    """Get all prompt versions."""
    return PROMPT_VERSIONS.copy()


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

# Excel column widths by content type
EXCEL_COLUMN_WIDTHS = {
    "id": 10,
    "name": 30,
    "short_text": 20,
    "description": 50,
    "evidence": 60,
    "long_text": 80,
    "status": 15,
    "enum": 20,
    "date": 12,
    "boolean": 8,
    "number": 10,
    "list": 40
}

# Severity/Priority color coding (hex without #)
SEVERITY_COLORS = {
    "critical": "FF6B6B",   # Red
    "high": "FFA94D",       # Orange
    "medium": "FFE066",     # Yellow
    "low": "69DB7C",        # Light green
    "unknown": "CED4DA"     # Gray
}

# Status color coding
STATUS_COLORS = {
    "complete": "69DB7C",      # Green
    "in_progress": "FFE066",   # Yellow
    "pending": "CED4DA",       # Gray
    "blocked": "FF6B6B",       # Red
    "duplicate": "74C0FC"      # Blue
}

# Business criticality colors
CRITICALITY_COLORS = {
    "Critical": "FF6B6B",   # Red
    "High": "FFA94D",       # Orange
    "Medium": "FFE066",     # Yellow
    "Low": "69DB7C",        # Green
    "Unknown": "CED4DA"     # Gray
}


# =============================================================================
# VALIDATION THRESHOLDS
# =============================================================================

# Minimum quote length for evidence validation (characters)
MIN_QUOTE_LENGTH = 10

# Maximum quote length (to prevent overly long quotes)
MAX_QUOTE_LENGTH = 500

# Fuzzy match threshold for duplicate detection (0.0-1.0)
DUPLICATE_THRESHOLD = 0.85

# Evidence density warning threshold (findings per 1000 chars)
# Below 0.5 = under-analyzed, above 2.0 = may be over-inferring
EVIDENCE_DENSITY_MIN = 0.5
EVIDENCE_DENSITY_MAX = 2.0

# Confidence distribution warnings
CONFIDENCE_HIGH_MAX_PCT = 80  # Warn if >80% high confidence
CONFIDENCE_LOW_MAX_PCT = 30   # Warn if >30% low confidence


# =============================================================================
# CAPABILITY AREA DEFAULTS
# =============================================================================

# Number of capability areas (for completeness checks)
TOTAL_CAPABILITY_AREAS = 13

# Critical capabilities that must always be assessed
CRITICAL_CAPABILITY_AREAS = [
    "finance_accounting",
    "human_resources",
    "identity_security"
]


# =============================================================================
# EXPORT SETTINGS
# =============================================================================

# Default Excel tab order for full export
EXCEL_TAB_ORDER = [
    "Summary",
    "Applications",
    "Capability_Coverage",
    "Buyer_Overlaps",
    "Risks",
    "Work_Items",
    "Gaps_Questions",
    "Contracts",  # Future
    "EOL_Assessment"  # Future
]

# Tab names that require the enhancement plan to be complete
FUTURE_TABS = ["Contracts", "EOL_Assessment"]


# =============================================================================
# DATA CLASSIFICATION DEFAULTS
# =============================================================================

# Default data classification when not specified
DEFAULT_DATA_CLASSIFICATION = {
    "contains_pii": None,
    "pii_types": [],
    "contains_phi": None,
    "phi_types": [],
    "contains_pci": None,
    "pci_types": [],
    "contains_financial": None,
    "data_residency": ["Unknown"]
}


# =============================================================================
# FILE PATHS
# =============================================================================

# Relative paths from project root
OUTPUT_DIR = "output"
DOCS_DIR = "docs"
METHODOLOGY_DIR = "docs/methodology"
ARCHITECTURE_DIR = "docs/architecture"


# =============================================================================
# VERSION INFO
# =============================================================================

CONSTANTS_VERSION = "1.0"
ENHANCEMENT_PLAN_VERSION = "115-Point Plan v1.0"
