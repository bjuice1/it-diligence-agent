"""
Runtime guards prevent experimental code from executing in production.

Usage in all experimental entry points:
    from domain.guards import ExperimentalGuard

    def main():
        ExperimentalGuard.require_experimental_mode()  # Raises if production
        # ... rest of experimental code

Created: 2026-02-12 (Worker 0 - Isolation Setup)
"""

import os
import sys


class ExperimentalGuard:
    """Prevents experimental code from running in production."""

    @staticmethod
    def require_experimental_mode():
        """
        Raises RuntimeError if:
        1. ENVIRONMENT=production (Railway sets this)
        2. ENABLE_DOMAIN_MODEL != 'true' (explicit opt-in required)

        Call this at the start of EVERY experimental entry point:
        - domain/cli.py::main()
        - domain/services/*.py constructors
        - Any code that writes to database
        """
        # Check 1: Prevent execution in production environment
        if os.getenv('ENVIRONMENT') == 'production':
            raise RuntimeError(
                "🚨 EXPERIMENTAL DOMAIN MODEL CANNOT RUN IN PRODUCTION!\n\n"
                "This code is under active development and will cause data corruption.\n"
                "Environment: ENVIRONMENT=production detected.\n\n"
                "If you're seeing this on Railway, check your imports:\n"
                "  - web/app.py should NOT import domain.*\n"
                "  - agents_v2/ should NOT import domain.*\n\n"
                "See ISOLATION_STRATEGY.md for details."
            )

        # Check 2: Require explicit opt-in
        if os.getenv('ENABLE_DOMAIN_MODEL') != 'true':
            print(
                "ℹ️  Experimental domain model is disabled.\n"
                "To enable for local testing:\n"
                "  export ENABLE_DOMAIN_MODEL=true\n"
                "  python -m domain.cli analyze data/input/\n",
                file=sys.stderr
            )
            raise RuntimeError(
                "Experimental features disabled. "
                "Set ENABLE_DOMAIN_MODEL=true to use."
            )

    @staticmethod
    def is_experimental_enabled() -> bool:
        """Check if experimental mode is enabled (non-throwing)."""
        return (
            os.getenv('ENABLE_DOMAIN_MODEL') == 'true' and
            os.getenv('ENVIRONMENT') != 'production'
        )

    @staticmethod
    def warn_if_production():
        """Emit warning if imported in production (for __init__.py)."""
        if os.getenv('ENVIRONMENT') == 'production':
            import warnings
            warnings.warn(
                "⚠️  EXPERIMENTAL DOMAIN MODEL IMPORTED IN PRODUCTION!\n"
                "This code is NOT ready for production use. "
                "Check your imports in web/, agents_v2/, or services/.\n"
                "See ISOLATION_STRATEGY.md for details.",
                RuntimeWarning,
                stacklevel=3
            )
