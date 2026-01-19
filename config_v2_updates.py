# =============================================================================
# CONFIG V2 UPDATES - Multi-Pass Extraction & Higher Limits
# =============================================================================
# Add these settings to config_v2.py

# -----------------------------------------------------------------------------
# INCREASED ITERATION LIMITS
# -----------------------------------------------------------------------------

# Discovery Phase - Increased from 30 to 100 for exhaustive extraction
MAX_DISCOVERY_ITERATIONS = 100

# Reasoning Phase - Increased from 40 to 80
MAX_REASONING_ITERATIONS = 80

# Multi-Pass specific limits
PASS_1_MAX_ITERATIONS = 50   # Major systems discovery
PASS_2_MAX_ITERATIONS = 100  # Detail extraction per system
PASS_3_MAX_ITERATIONS = 50   # Relationships and validation

# -----------------------------------------------------------------------------
# MULTI-PASS EXTRACTION CONFIGURATION
# -----------------------------------------------------------------------------

MULTI_PASS_ENABLED = True

EXTRACTION_PASSES = {
    "pass_1_systems": {
        "name": "System Discovery",
        "description": "Identify all major systems, platforms, and technologies",
        "focus": ["platforms", "vendors", "major_systems"],
        "granularity": "high_level",
        "max_iterations": 50
    },
    "pass_2_details": {
        "name": "Detail Extraction",
        "description": "Extract counts, versions, configurations for each system",
        "focus": ["counts", "versions", "configurations", "capacities", "costs"],
        "granularity": "line_item",
        "max_iterations": 100
    },
    "pass_3_validation": {
        "name": "Validation & Reconciliation",
        "description": "Cross-check details against summaries, flag inconsistencies",
        "focus": ["reconciliation", "gap_detection", "consistency"],
        "granularity": "verification",
        "max_iterations": 50
    }
}

# -----------------------------------------------------------------------------
# GRANULAR FACTS CONFIGURATION
# -----------------------------------------------------------------------------

# Enable separate storage for raw line-item facts
GRANULAR_FACTS_ENABLED = True

# Export formats
EXPORT_FORMATS = ["csv", "xlsx", "json"]

# Granular fact categories (for Excel sheet organization)
GRANULAR_CATEGORIES = {
    "infrastructure": [
        "servers", "vms", "storage_volumes", "backup_jobs",
        "cloud_resources", "network_devices", "licenses"
    ],
    "applications": [
        "application_inventory", "integrations", "databases",
        "api_endpoints", "scheduled_jobs", "user_counts"
    ],
    "security": [
        "security_tools", "certificates", "firewall_rules",
        "user_accounts", "service_accounts", "mfa_status"
    ],
    "organization": [
        "headcount", "roles", "vendors", "contracts",
        "sla_terms", "support_agreements"
    ]
}

# -----------------------------------------------------------------------------
# VALIDATION THRESHOLDS
# -----------------------------------------------------------------------------

# Reconciliation tolerance (e.g., if summary says "~50 servers" and detail count is 47)
RECONCILIATION_TOLERANCE = 0.15  # 15% variance allowed

# Minimum detail coverage (what % of summary items need detail backup)
MIN_DETAIL_COVERAGE = 0.80  # 80% of summary items should have granular details

# Flag items where summary vs detail variance exceeds this
VARIANCE_ALERT_THRESHOLD = 0.25  # 25% triggers warning
