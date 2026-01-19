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
DISCOVERY_MAX_TOKENS = 4096   # Extraction needs less
REASONING_MAX_TOKENS = 8192   # Analysis needs more space

# Iteration limits
DISCOVERY_MAX_ITERATIONS = 30
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

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FACTS_DIR.mkdir(parents=True, exist_ok=True)
FINDINGS_DIR.mkdir(parents=True, exist_ok=True)


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

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5  # Open circuit after N failures
CIRCUIT_BREAKER_SUCCESS_THRESHOLD = 2  # Close circuit after N successes (half-open)
CIRCUIT_BREAKER_TIMEOUT = 60.0  # Seconds before trying half-open


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
# OUTPUT CONFIGURATION
# =============================================================================

# Evidence chain format
EVIDENCE_FORMAT = "markdown"  # or "json"

# Export options
EXPORT_FACTS_JSON = True
EXPORT_FINDINGS_JSON = True
EXPORT_EXCEL = True
EXPORT_HTML = True
