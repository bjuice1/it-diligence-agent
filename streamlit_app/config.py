"""
Configuration Module - Unified Configuration for Streamlit App

Handles environment variables, Streamlit secrets, and defaults
with proper fallback chains and validation.

Steps 19-25 of the alignment plan.
"""

import os
import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum


# =============================================================================
# ENVIRONMENT
# =============================================================================

class Environment(Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

@dataclass
class APIConfig:
    """API-related configuration."""
    anthropic_api_key: str = ""
    discovery_model: str = "claude-3-5-haiku-20241022"
    reasoning_model: str = "claude-sonnet-4-20250514"
    narrative_model: str = "claude-sonnet-4-20250514"
    discovery_temperature: float = 0.0
    reasoning_temperature: float = 0.0
    narrative_temperature: float = 0.1
    max_retries: int = 3
    timeout_seconds: int = 300

    def is_configured(self) -> bool:
        """Check if API is properly configured."""
        return bool(self.anthropic_api_key)

    def validate(self) -> List[str]:
        """Validate API configuration. Returns list of errors."""
        errors = []
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY not set")
        return errors


@dataclass
class PathConfig:
    """File path configuration."""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    input_dir: Path = field(default_factory=lambda: Path("data/input"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    facts_dir: Path = field(default_factory=lambda: Path("output/facts"))
    findings_dir: Path = field(default_factory=lambda: Path("output/findings"))
    uploads_dir: Path = field(default_factory=lambda: Path("data/uploads"))
    sessions_dir: Path = field(default_factory=lambda: Path("sessions"))

    def __post_init__(self):
        """Make paths absolute based on project root."""
        if not self.input_dir.is_absolute():
            self.input_dir = self.project_root / self.input_dir
        if not self.output_dir.is_absolute():
            self.output_dir = self.project_root / self.output_dir
        if not self.facts_dir.is_absolute():
            self.facts_dir = self.project_root / self.facts_dir
        if not self.findings_dir.is_absolute():
            self.findings_dir = self.project_root / self.findings_dir
        if not self.uploads_dir.is_absolute():
            self.uploads_dir = self.project_root / self.uploads_dir
        if not self.sessions_dir.is_absolute():
            self.sessions_dir = self.project_root / self.sessions_dir

    def ensure_directories(self):
        """Create all required directories."""
        for path in [
            self.input_dir,
            self.output_dir,
            self.facts_dir,
            self.findings_dir,
            self.uploads_dir,
            self.sessions_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


@dataclass
class FeatureFlags:
    """Feature toggles for gradual rollout."""
    # Core features
    background_processing: bool = False  # Not yet fully implemented
    organization_module: bool = True
    open_questions: bool = True
    cost_analysis: bool = True
    narrative_view: bool = True

    # Advanced features
    granular_facts: bool = True
    verification_ui: bool = True
    org_chart: bool = True
    deal_readout: bool = True
    inventory_panel: bool = True

    # Experimental
    incremental_processing: bool = False
    multi_user_sessions: bool = False

    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return getattr(self, feature, False)


@dataclass
class UIConfig:
    """UI-related configuration."""
    page_title: str = "IT Due Diligence Agent"
    page_icon: str = "🔍"
    layout: str = "wide"
    sidebar_state: str = "expanded"
    theme_primary_color: str = "#f97316"
    theme_background: str = "#fafaf9"
    items_per_page: int = 20
    max_upload_size_mb: int = 50
    max_total_upload_mb: int = 200


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    password_protected: bool = False
    app_password: str = ""
    require_api_key: bool = True
    allowed_domains: List[str] = field(default_factory=list)


@dataclass
class AppConfig:
    """Complete application configuration."""
    environment: Environment = Environment.DEVELOPMENT
    api: APIConfig = field(default_factory=APIConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    ui: UIConfig = field(default_factory=UIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    debug: bool = False

    def validate(self) -> List[str]:
        """Validate all configuration. Returns list of errors."""
        errors = []
        errors.extend(self.api.validate())

        if self.security.password_protected and not self.security.app_password:
            errors.append("Password protection enabled but APP_PASSWORD not set")

        return errors


# =============================================================================
# CONFIGURATION LOADER
# =============================================================================

class ConfigLoader:
    """
    Loads configuration from multiple sources with fallback chain:
    1. Environment variables
    2. Streamlit secrets
    3. Default values
    """

    _config: Optional[AppConfig] = None

    @classmethod
    def load(cls, force_reload: bool = False) -> AppConfig:
        """
        Load configuration from all sources.

        Args:
            force_reload: If True, reload even if already loaded

        Returns:
            Loaded AppConfig
        """
        if cls._config is not None and not force_reload:
            return cls._config

        config = AppConfig()

        # Determine environment
        env_str = cls._get_value("ENVIRONMENT", "development")
        try:
            config.environment = Environment(env_str.lower())
        except ValueError:
            config.environment = Environment.DEVELOPMENT

        # API Configuration
        config.api.anthropic_api_key = cls._get_value("ANTHROPIC_API_KEY", "")
        config.api.discovery_model = cls._get_value(
            "DISCOVERY_MODEL",
            "claude-3-5-haiku-20241022"
        )
        config.api.reasoning_model = cls._get_value(
            "REASONING_MODEL",
            "claude-sonnet-4-20250514"
        )

        # Security Configuration
        config.security.app_password = cls._get_value("APP_PASSWORD", "")
        config.security.password_protected = bool(config.security.app_password)

        # Debug mode
        config.debug = cls._get_value("DEBUG", "false").lower() in ("true", "1", "yes")

        # Feature flags from environment
        for flag in [
            "background_processing",
            "organization_module",
            "open_questions",
            "cost_analysis",
            "narrative_view",
            "granular_facts",
            "verification_ui",
            "incremental_processing",
        ]:
            env_key = f"FEATURE_{flag.upper()}"
            env_val = cls._get_value(env_key, None)
            if env_val is not None:
                setattr(config.features, flag, env_val.lower() in ("true", "1", "yes"))

        # Ensure directories exist
        config.paths.ensure_directories()

        cls._config = config
        return config

    @classmethod
    def _get_value(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get value from environment or secrets.

        Priority:
        1. Environment variable
        2. Streamlit secrets
        3. Default value
        """
        # Check environment first
        value = os.getenv(key)
        if value is not None:
            return value

        # Check Streamlit secrets
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass

        return default

    @classmethod
    def get(cls) -> AppConfig:
        """Get current configuration (loads if needed)."""
        if cls._config is None:
            return cls.load()
        return cls._config

    @classmethod
    def reload(cls) -> AppConfig:
        """Force reload configuration."""
        return cls.load(force_reload=True)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_config() -> AppConfig:
    """Get application configuration."""
    return ConfigLoader.get()


def get_api_key() -> str:
    """Get Anthropic API key."""
    return ConfigLoader.get().api.anthropic_api_key


def is_api_configured() -> bool:
    """Check if API is properly configured."""
    return ConfigLoader.get().api.is_configured()


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature flag is enabled."""
    return ConfigLoader.get().features.is_enabled(feature)


def get_environment() -> Environment:
    """Get current environment."""
    return ConfigLoader.get().environment


def is_production() -> bool:
    """Check if running in production."""
    return get_environment() == Environment.PRODUCTION


def is_development() -> bool:
    """Check if running in development."""
    return get_environment() == Environment.DEVELOPMENT


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return ConfigLoader.get().debug


# =============================================================================
# API KEY VALIDATION
# =============================================================================

def validate_api_key() -> tuple[bool, str]:
    """
    Validate that API key works by making a test call.

    Returns:
        Tuple of (success, message)
    """
    api_key = get_api_key()
    if not api_key:
        return False, "No API key configured"

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Quick test call
        client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}]
        )
        return True, "API connection successful"

    except Exception as e:
        error_type = type(e).__name__
        if "AuthenticationError" in error_type:
            return False, "Invalid API key"
        elif "RateLimitError" in error_type:
            return False, "Rate limited - try again later"
        else:
            return False, f"API error: {error_type}: {str(e)[:100]}"


# =============================================================================
# SYNC WITH PROJECT CONFIG
# =============================================================================

def sync_with_project_config():
    """
    Sync configuration with the main project config_v2.py.

    This ensures the Streamlit app uses the same settings
    as the CLI and Flask app.
    """
    try:
        from config_v2 import (
            ANTHROPIC_API_KEY,
            OUTPUT_DIR,
            FACTS_DIR,
            FINDINGS_DIR,
            ensure_directories,
        )

        config = ConfigLoader.get()

        # Sync API key if not already set
        if not config.api.anthropic_api_key and ANTHROPIC_API_KEY:
            config.api.anthropic_api_key = ANTHROPIC_API_KEY

        # Sync paths
        config.paths.output_dir = OUTPUT_DIR
        config.paths.facts_dir = FACTS_DIR
        config.paths.findings_dir = FINDINGS_DIR

        # Ensure directories
        ensure_directories()

        return True

    except ImportError as e:
        print(f"Could not sync with project config: {e}")
        return False
