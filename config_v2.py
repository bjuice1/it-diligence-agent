"""
Configuration for V2 Architecture

V2 uses a Discovery-Reasoning split with model tiering:
- Discovery: Haiku (cheaper, faster) for fact extraction
- Reasoning: Sonnet (capable) for analysis and synthesis
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Try multiple sources for API key (env var, .env file, Streamlit secrets)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Fallback to Streamlit secrets if available (for Streamlit Cloud deployment)
if not ANTHROPIC_API_KEY:
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
            ANTHROPIC_API_KEY = st.secrets['ANTHROPIC_API_KEY']
    except Exception:
        pass

# Model tiering - key benefit of v2 architecture
DISCOVERY_MODEL = "claude-3-5-haiku-20241022"  # Fast, cheap for extraction
REASONING_MODEL = "claude-sonnet-4-20250514"   # Capable for analysis

# Token limits
# CRITICAL: Discovery needs MORE tokens when extracting large inventories (30+ apps)
# Each create_inventory_entry tool call uses ~100-200 tokens in the response
DISCOVERY_MAX_TOKENS = 8192   # Increased from 4096 - needed for 30+ item inventories
REASONING_MAX_TOKENS = 8192   # Analysis needs more space

# Iteration limits
# CRITICAL: Large inventories (30+ items) need more iterations
# Each iteration typically extracts 3-5 items, so 50+ needed for completeness
DISCOVERY_MAX_ITERATIONS = 60  # Increased from 50 for better coverage of large inventories
REASONING_MAX_ITERATIONS = 40

# Temperature - SET TO 0 FOR DETERMINISTIC OUTPUT
# This is critical for consistency between runs
DISCOVERY_TEMPERATURE = 0.0  # Zero for fully deterministic extraction
REASONING_TEMPERATURE = 0.0  # Zero for deterministic scoring and analysis
NARRATIVE_TEMPERATURE = 0.1  # Slight variation allowed for prose (non-critical)


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"  # Note: different from v1's data/output

# V2-specific output directories
FACTS_DIR = OUTPUT_DIR / "facts"
FINDINGS_DIR = OUTPUT_DIR / "findings"
LOGS_DIR = OUTPUT_DIR / "logs"

# =============================================================================
# DOCUMENT STORAGE (Phase 1: Document Layer)
# =============================================================================

# Document storage root - Uploads directory for user-provided documents
# Phase D: Renamed from output/documents to uploads/ for clarity
UPLOADS_DIR = BASE_DIR / "uploads"
DOCUMENTS_DIR = UPLOADS_DIR  # Alias for backward compatibility

# Entity-specific document directories
TARGET_DOCS_DIR = UPLOADS_DIR / "target"
BUYER_DOCS_DIR = UPLOADS_DIR / "buyer"

# Authority level subdirectories (created within entity dirs)
AUTHORITY_FOLDERS = {
    1: "data_room",        # Highest authority - official data room documents
    2: "correspondence",   # Medium authority - formal correspondence
    3: "notes"             # Lowest authority - discussion notes
}


def ensure_directories():
    """Create required directories (called lazily when needed)."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FACTS_DIR.mkdir(parents=True, exist_ok=True)
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Document storage directories (Phase D: uploads/ directory)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Entity directories with authority subfolders
    for entity_dir in [TARGET_DOCS_DIR, BUYER_DOCS_DIR]:
        entity_dir.mkdir(parents=True, exist_ok=True)
        for folder in AUTHORITY_FOLDERS.values():
            (entity_dir / folder).mkdir(exist_ok=True)
        (entity_dir / "extracted").mkdir(exist_ok=True)

    # Validation system directories
    VALIDATION_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# DOMAIN CONFIGURATION
# =============================================================================

# V2 domains (same as v1)
DOMAINS = [
    "infrastructure",
    "network",
    "cybersecurity",
    "applications",
    "identity_access",
    "organization"
]

# Categories per domain (for discovery validation)
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


# =============================================================================
# COST TRACKING (estimated)
# =============================================================================

# Anthropic pricing per million tokens (approximate, check actual rates)
MODEL_COSTS = {
    "claude-3-5-haiku-20241022": {
        "input": 0.25,    # $0.25 per 1M input tokens
        "output": 1.25    # $1.25 per 1M output tokens
    },
    "claude-sonnet-4-20250514": {
        "input": 3.00,    # $3.00 per 1M input tokens
        "output": 15.00   # $15.00 per 1M output tokens
    }
}

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate API cost for a given model and token counts."""
    if model not in MODEL_COSTS:
        return 0.0

    costs = MODEL_COSTS[model]
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost


# =============================================================================
# DATABASE CONFIGURATION (Phase 1)
# =============================================================================

# Database URL - PostgreSQL for production, SQLite for local dev
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Feature flag - Use PostgreSQL (set to True when ready)
USE_DATABASE = os.getenv('USE_DATABASE', 'false').lower() == 'true'

# Connection pool settings
DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '5'))
DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '10'))
DATABASE_POOL_TIMEOUT = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))

# Query timeout (seconds)
DATABASE_QUERY_TIMEOUT = int(os.getenv('DATABASE_QUERY_TIMEOUT', '30'))


# =============================================================================
# REDIS CONFIGURATION (Phase 2)
# =============================================================================

# Redis URL for sessions and task queue
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Feature flags
USE_REDIS_SESSIONS = os.getenv('USE_REDIS_SESSIONS', 'false').lower() == 'true'
USE_CELERY = os.getenv('USE_CELERY', 'false').lower() == 'true'

# Session configuration
SESSION_LIFETIME_DAYS = int(os.getenv('SESSION_LIFETIME_DAYS', '7'))


# =============================================================================
# V2 FEATURE FLAGS
# =============================================================================

# Enable/disable features
ENABLE_FACT_VALIDATION = True      # Validate evidence quotes exist in document
ENABLE_CITATION_VALIDATION = False # Validate fact IDs in findings exist (False = warn only, True = fail fast)
ENABLE_DUPLICATE_DETECTION = True  # Check for duplicate facts/gaps
PARALLEL_DISCOVERY = True          # Run discovery agents in parallel
PARALLEL_REASONING = True          # Run reasoning agents in parallel

# Parallelization limits (for rate limiting)
MAX_PARALLEL_AGENTS = 3  # Max agents to run simultaneously

# API Rate Limiting
# Anthropic rate limits: ~50 requests/minute for most tiers
# Using semaphore to limit concurrent API calls across all agents
API_RATE_LIMIT_PER_MINUTE = 40  # Conservative limit (leave buffer)
API_RATE_LIMIT_SEMAPHORE_SIZE = 3  # Max concurrent API calls (matches MAX_PARALLEL_AGENTS)

# API Retry Configuration
API_MAX_RETRIES = 3  # Maximum retry attempts for API calls
API_TIMEOUT_SECONDS = 300  # 5 minute timeout per API call
API_RETRY_BACKOFF_BASE = 2  # Exponential backoff base (2^attempt seconds)
API_RATE_LIMITER_TIMEOUT = 60  # Max wait time for rate limiter slot (seconds)

# Circuit Breaker Configuration - made more resilient to prevent blocking analysis
CIRCUIT_BREAKER_ENABLED = True          # Set to False to disable circuit breaker entirely
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 15  # Open circuit after N consecutive failures (was 5)
CIRCUIT_BREAKER_SUCCESS_THRESHOLD = 1   # Close circuit after N successes in half-open (was 2)
CIRCUIT_BREAKER_TIMEOUT = 10.0          # Seconds before retrying (was 60 - too long)


# =============================================================================
# VALIDATION THRESHOLDS
# =============================================================================

# Evidence validation
MIN_EVIDENCE_QUOTE_LENGTH = 10     # Minimum characters for exact_quote
MAX_EVIDENCE_QUOTE_LENGTH = 500    # Maximum characters (truncate if longer)

# Duplicate detection
DUPLICATE_SIMILARITY_THRESHOLD = 0.85  # 0.0-1.0, higher = stricter matching

# Quote validation (fuzzy match against source document)
QUOTE_VALIDATION_THRESHOLD = 0.85  # Minimum similarity to consider quote valid


# =============================================================================
# WEB UPLOAD CONFIGURATION (Point 112: Extract magic numbers)
# =============================================================================

# File upload limits
MAX_FILE_SIZE_MB = 50           # Maximum single file size in MB
MAX_TOTAL_UPLOAD_MB = 200       # Maximum total upload size in MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_TOTAL_UPLOAD_BYTES = MAX_TOTAL_UPLOAD_MB * 1024 * 1024

# Supported file types
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'docx', 'xlsx', 'csv'}

# Session configuration
SESSION_MAX_AGE_HOURS = 24      # Session expiration time
SESSION_CLEANUP_INTERVAL = 3600 # Cleanup interval in seconds

# Pagination
DEFAULT_PAGE_SIZE = 50          # Default items per page
MAX_PAGE_SIZE = 200             # Maximum items per page

# Analysis timeouts
ANALYSIS_TIMEOUT_SECONDS = 1800 # 30 minutes max for analysis


# =============================================================================
# VALIDATION SYSTEM CONFIGURATION (Phase 14)
# =============================================================================

# Master switch for validation system
VALIDATION_ENABLED = True

# Model selection for validation
VALIDATION_MODEL = "claude-sonnet-4-20250514"  # Sonnet for thorough validation
CATEGORY_VALIDATION_MODEL = "claude-3-5-haiku-20241022"  # Haiku for category checkpoints

# Evidence verification thresholds
EVIDENCE_MATCH_THRESHOLD = 0.85  # Minimum fuzzy match score for "verified"
EVIDENCE_PARTIAL_THRESHOLD = 0.50  # Minimum for "partial_match"

# Confidence thresholds for review
CONFIDENCE_THRESHOLD_FOR_REVIEW = 0.70  # Below this triggers human review
CONFIDENCE_HIGH = 0.80  # Above this is "high confidence"
CONFIDENCE_CRITICAL = 0.40  # Below this is "critical" - likely wrong

# Re-extraction loop settings
MAX_REEXTRACTION_ATTEMPTS = 3  # Max automatic retries before escalation
REEXTRACTION_IMPROVEMENT_THRESHOLD = 0.10  # Min improvement required to continue

# Adversarial review settings
ADVERSARIAL_REVIEW_ENABLED = True
ADVERSARIAL_WEIGHT = 0.5  # Weight for adversarial findings (vs. direct validation)

# Category-specific expected ranges
MIN_EXPECTED_TEAMS = 5  # Minimum IT teams expected in organization
MAX_EXPECTED_TEAMS = 15  # Maximum reasonable teams

# Expected salary ranges per category (USD annual)
EXPECTED_SALARY_RANGES = {
    "leadership": (150000, 300000),
    "applications": (90000, 160000),
    "infrastructure": (80000, 140000),
    "security": (100000, 180000),
    "cybersecurity": (100000, 180000),
    "service_desk": (50000, 90000),
    "pmo": (90000, 150000),
    "data_analytics": (95000, 170000),
    "network": (85000, 150000),
    "default": (70000, 150000),
}

# Cross-domain consistency check thresholds
CONSISTENCY_CHECK_THRESHOLDS = {
    "headcount_vs_endpoints": (20, 200),  # Endpoints per IT person
    "headcount_vs_apps": (0.5, 30),  # Applications per IT person
    "cost_per_head": (50000, 300000),  # Total IT cost per IT headcount
    "apps_per_integration": (2, 20),  # Applications per integration point
}

# Validation flag severity mappings
FLAG_SEVERITY_WEIGHTS = {
    "critical": 1.0,  # Full impact on confidence
    "error": 0.7,     # High impact
    "warning": 0.3,   # Moderate impact
    "info": 0.0,      # No impact on confidence
}

# Validation storage settings
VALIDATION_STORAGE_DIR = OUTPUT_DIR / "validation"
AUDIT_LOG_DIR = OUTPUT_DIR / "audit"
VALIDATION_CACHE_TTL = 3600  # Cache validation results for 1 hour

# Human review queue settings
REVIEW_QUEUE_PAGE_SIZE = 20
REVIEW_QUEUE_SORT_ORDER = ["critical", "error", "warning", "info"]
AUTO_ESCALATE_AFTER_DAYS = 3  # Auto-escalate if not reviewed in N days


# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

# Evidence chain format
EVIDENCE_FORMAT = "markdown"  # or "json"

# Export options
EXPORT_FACTS_JSON = True
EXPORT_FINDINGS_JSON = True
EXPORT_EXCEL = True
EXPORT_HTML = True


# =============================================================================
# ENVIRONMENT VALIDATION
# =============================================================================

def validate_environment() -> dict:
    """
    Validate the environment configuration.

    Returns dict with:
    - valid: bool - whether environment is properly configured
    - api_key_configured: bool - whether API key is set
    - directories_exist: bool - whether required directories exist
    - warnings: list - non-fatal issues
    - errors: list - fatal issues
    """
    result = {
        'valid': True,
        'api_key_configured': bool(ANTHROPIC_API_KEY),
        'directories_exist': True,
        'warnings': [],
        'errors': []
    }

    # Check API key
    if not ANTHROPIC_API_KEY:
        result['errors'].append('ANTHROPIC_API_KEY not configured. Set it in .env file or environment.')
        result['valid'] = False
    elif len(ANTHROPIC_API_KEY) < 20:
        result['warnings'].append('ANTHROPIC_API_KEY appears to be invalid (too short)')

    # Check directories
    try:
        ensure_directories()
    except Exception as e:
        result['errors'].append(f'Could not create directories: {e}')
        result['directories_exist'] = False
        result['valid'] = False

    # Check if output directory is writable
    try:
        test_file = OUTPUT_DIR / '.write_test'
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        result['warnings'].append(f'Output directory may not be writable: {e}')

    return result


def get_config_summary() -> dict:
    """Get a summary of current configuration for debugging."""
    return {
        'base_dir': str(BASE_DIR),
        'data_dir': str(DATA_DIR),
        'output_dir': str(OUTPUT_DIR),
        'discovery_model': DISCOVERY_MODEL,
        'reasoning_model': REASONING_MODEL,
        'domains': DOMAINS,
        'api_key_set': bool(ANTHROPIC_API_KEY),
        'parallel_enabled': PARALLEL_DISCOVERY and PARALLEL_REASONING,
        'max_parallel_agents': MAX_PARALLEL_AGENTS,
        # Validation settings
        'validation_enabled': VALIDATION_ENABLED,
        'validation_model': VALIDATION_MODEL,
        'evidence_threshold': EVIDENCE_MATCH_THRESHOLD,
        'confidence_review_threshold': CONFIDENCE_THRESHOLD_FOR_REVIEW,
        'max_reextraction_attempts': MAX_REEXTRACTION_ATTEMPTS,
        'adversarial_review_enabled': ADVERSARIAL_REVIEW_ENABLED,
    }


def get_validation_config() -> dict:
    """Get validation-specific configuration."""
    return {
        'enabled': VALIDATION_ENABLED,
        'model': VALIDATION_MODEL,
        'category_model': CATEGORY_VALIDATION_MODEL,
        'thresholds': {
            'evidence_match': EVIDENCE_MATCH_THRESHOLD,
            'evidence_partial': EVIDENCE_PARTIAL_THRESHOLD,
            'confidence_review': CONFIDENCE_THRESHOLD_FOR_REVIEW,
            'confidence_high': CONFIDENCE_HIGH,
            'confidence_critical': CONFIDENCE_CRITICAL,
        },
        'reextraction': {
            'max_attempts': MAX_REEXTRACTION_ATTEMPTS,
            'improvement_threshold': REEXTRACTION_IMPROVEMENT_THRESHOLD,
        },
        'adversarial': {
            'enabled': ADVERSARIAL_REVIEW_ENABLED,
            'weight': ADVERSARIAL_WEIGHT,
        },
        'consistency_thresholds': CONSISTENCY_CHECK_THRESHOLDS,
        'salary_ranges': EXPECTED_SALARY_RANGES,
        'flag_weights': FLAG_SEVERITY_WEIGHTS,
        'storage': {
            'validation_dir': str(VALIDATION_STORAGE_DIR),
            'audit_dir': str(AUDIT_LOG_DIR),
            'cache_ttl': VALIDATION_CACHE_TTL,
        },
        'review_queue': {
            'page_size': REVIEW_QUEUE_PAGE_SIZE,
            'sort_order': REVIEW_QUEUE_SORT_ORDER,
            'auto_escalate_days': AUTO_ESCALATE_AFTER_DAYS,
        },
    }
