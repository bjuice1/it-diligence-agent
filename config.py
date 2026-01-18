"""
Configuration for IT Diligence Analysis Agent
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"  # Using Sonnet for speed + quality balance
MAX_TOKENS = 8192

# Agent Configuration
MAX_TOOL_ITERATIONS = 50  # Max tool calls per agent (increased to 50 for complete analysis)
TEMPERATURE = 0.3  # Lower for more consistent analysis

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Domain Configuration
DOMAINS = [
    "infrastructure",
    "network",
    "cybersecurity",
    "applications",
    "identity_access",
    "organization"
]

# Analysis Output Categories
OUTPUT_CATEGORIES = [
    "assumptions",
    "gaps",
    "risks",
    "work_items",
    "recommendations"
]

# Severity/Impact Levels
SEVERITY_LEVELS = ["critical", "high", "medium", "low"]
CONFIDENCE_LEVELS = ["high", "medium", "low"]

# Cost Estimation Defaults
DEFAULT_LABOR_RATES = {
    "project_manager": 175,
    "solution_architect": 225,
    "infrastructure_engineer": 150,
    "cloud_engineer": 175,
    "security_engineer": 185,
    "network_engineer": 160,
    "dba": 165,
    "systems_admin": 125
}

DEFAULT_CONTINGENCY = 0.20  # 20%
DEFAULT_COMPLEXITY_FACTOR = 1.25  # Medium complexity
