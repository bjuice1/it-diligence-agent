"""
Experimental domain model configuration.

CRITICAL: Uses SEPARATE database from production to prevent data corruption.

Production DB: Uses DATABASE_URL from .env (PostgreSQL on Railway)
Experimental DB: Uses domain_experimental.db (SQLite, local only)

Created: 2026-02-12 (Worker 0 - Isolation Setup)
"""

import os
from domain.guards import ExperimentalGuard


class DomainConfig:
    """Configuration for experimental domain model."""

    def __init__(self):
        # Enforce experimental mode
        ExperimentalGuard.require_experimental_mode()

        # Use SEPARATE database (NEVER production DB)
        self.database_url = os.getenv(
            'DOMAIN_DATABASE_URL',
            'sqlite:///domain_experimental.db'  # Default: local SQLite
        )

        # PostgreSQL schema isolation (if using shared DB for testing)
        self.database_schema = os.getenv(
            'DOMAIN_DATABASE_SCHEMA',
            'domain_model_experimental'  # NOT public schema
        )

        # Verify we're NOT using production database
        production_db = os.getenv('DATABASE_URL')
        if production_db and self.database_url == production_db:
            raise RuntimeError(
                "🚨 EXPERIMENTAL CODE ATTEMPTING TO USE PRODUCTION DATABASE!\n\n"
                "domain_experimental.db != production DB\n"
                "Set DOMAIN_DATABASE_URL to a SEPARATE database.\n\n"
                "See ISOLATION_STRATEGY.md Layer 3."
            )

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite (vs PostgreSQL)."""
        return self.database_url.startswith('sqlite:///')

    @property
    def connection_args(self) -> dict:
        """SQLAlchemy connection arguments."""
        if self.is_sqlite:
            return {
                'check_same_thread': False,  # Allow multi-threaded access
                'timeout': 30  # 30 second lock timeout
            }
        else:
            return {
                'options': f'-c search_path={self.database_schema},public'
            }


# Singleton instance
# Note: This will raise if ENABLE_DOMAIN_MODEL != 'true'
# This is intentional - config should only be imported in experimental code
try:
    config = DomainConfig()
except RuntimeError as e:
    # If guards prevent initialization, that's expected
    # Don't fail module import, just don't create config
    config = None
