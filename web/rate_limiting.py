"""
Rate Limiting Configuration for IT Due Diligence Agent (Phase 7)

Provides rate limiting for:
- API endpoint protection
- Abuse prevention
- Resource management
- Per-tenant limits
"""

import os
import logging
from typing import Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Rate limit storage backend
RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
RATELIMIT_STRATEGY = os.environ.get('RATELIMIT_STRATEGY', 'fixed-window')

# Default limits
RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day, 50 per hour')
RATELIMIT_API_DEFAULT = os.environ.get('RATELIMIT_API_DEFAULT', '100 per minute')

# Enable/disable rate limiting
RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'true').lower() == 'true'

# Check if flask-limiter is available
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    Limiter = None


# =============================================================================
# KEY FUNCTIONS
# =============================================================================

def get_rate_limit_key():
    """
    Get the key for rate limiting.

    Priority:
    1. Authenticated user ID
    2. Tenant ID
    3. API key (from header)
    4. IP address
    """
    from flask import request, g
    from flask_login import current_user

    # Authenticated user
    if current_user and current_user.is_authenticated:
        return f"user:{current_user.id}"

    # Tenant from context
    tenant_id = getattr(g, 'tenant_id', None)
    if tenant_id:
        return f"tenant:{tenant_id}"

    # API key from header
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return f"apikey:{api_key[:16]}"  # Only use prefix for privacy

    # Fall back to IP
    return f"ip:{get_remote_address()}"


def get_tenant_key():
    """Get key based on tenant for tenant-wide limits."""
    from flask import g

    tenant_id = getattr(g, 'tenant_id', None)
    if tenant_id:
        return f"tenant:{tenant_id}"

    return get_rate_limit_key()


def get_ip_key():
    """Get key based on IP address only."""
    return f"ip:{get_remote_address()}"


# =============================================================================
# LIMITER SETUP
# =============================================================================

# Global limiter instance
limiter = None


def init_rate_limiter(app):
    """
    Initialize rate limiter for Flask app.

    Args:
        app: Flask application instance

    Returns:
        Limiter instance or None if not available
    """
    global limiter

    if not LIMITER_AVAILABLE:
        logger.warning("flask-limiter not installed. Rate limiting disabled.")
        return None

    if not RATELIMIT_ENABLED:
        logger.info("Rate limiting disabled via configuration.")
        return None

    try:
        limiter = Limiter(
            app=app,
            key_func=get_rate_limit_key,
            default_limits=[RATELIMIT_DEFAULT],
            storage_uri=RATELIMIT_STORAGE_URL,
            strategy=RATELIMIT_STRATEGY,
            headers_enabled=True,  # Add X-RateLimit headers to responses
            header_name_mapping={
                'X-RateLimit-Limit': 'limit',
                'X-RateLimit-Remaining': 'remaining',
                'X-RateLimit-Reset': 'reset',
            },
            swallow_errors=True,  # Don't crash on storage errors
        )

        # Register error handler
        @app.errorhandler(429)
        def ratelimit_handler(e):
            from flask import jsonify
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': str(e.description),
                'retry_after': e.get_response().headers.get('Retry-After', 60)
            }), 429

        logger.info(
            f"Rate limiter initialized: storage={RATELIMIT_STORAGE_URL}, "
            f"strategy={RATELIMIT_STRATEGY}"
        )
        return limiter

    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {e}")
        return None


# =============================================================================
# RATE LIMIT DECORATORS
# =============================================================================

def rate_limit(limit_string: str, key_func: Callable = None):
    """
    Decorator to apply rate limiting to a route.

    Args:
        limit_string: Rate limit string (e.g., "10 per minute")
        key_func: Optional custom key function

    Usage:
        @app.route('/api/expensive')
        @rate_limit("5 per minute")
        def expensive_operation():
            ...
    """
    def decorator(f):
        if limiter and RATELIMIT_ENABLED:
            # Apply the flask-limiter decorator
            if key_func:
                return limiter.limit(limit_string, key_func=key_func)(f)
            else:
                return limiter.limit(limit_string)(f)
        return f
    return decorator


def rate_limit_by_ip(limit_string: str):
    """Rate limit by IP address."""
    return rate_limit(limit_string, key_func=get_ip_key)


def rate_limit_by_tenant(limit_string: str):
    """Rate limit by tenant."""
    return rate_limit(limit_string, key_func=get_tenant_key)


def exempt_from_rate_limit(f):
    """Exempt a route from rate limiting."""
    if limiter and RATELIMIT_ENABLED:
        return limiter.exempt(f)
    return f


# =============================================================================
# PREDEFINED LIMITS
# =============================================================================

class RateLimits:
    """Predefined rate limit configurations."""

    # Authentication endpoints (stricter to prevent brute force)
    AUTH_LOGIN = "5 per minute, 20 per hour"
    AUTH_REGISTER = "3 per minute, 10 per hour"
    AUTH_RESET_PASSWORD = "3 per minute, 10 per hour"

    # Analysis endpoints (resource-intensive)
    ANALYSIS_START = "5 per hour"
    ANALYSIS_STATUS = "60 per minute"

    # Document upload
    DOCUMENT_UPLOAD = "20 per hour"
    DOCUMENT_PROCESS = "10 per hour"

    # API endpoints
    API_READ = "100 per minute"
    API_WRITE = "30 per minute"
    API_DELETE = "20 per minute"

    # Export operations
    EXPORT = "10 per hour"

    # Health check (high limit)
    HEALTH_CHECK = "1000 per minute"


# =============================================================================
# DYNAMIC RATE LIMITS
# =============================================================================

def get_plan_rate_limit(operation: str) -> str:
    """
    Get rate limit based on tenant plan.

    Args:
        operation: Operation type

    Returns:
        Rate limit string
    """
    from flask import g

    # Default limits
    default_limits = {
        'analysis': "5 per hour",
        'upload': "20 per hour",
        'api': "100 per minute",
        'export': "10 per hour",
    }

    # Plan-based multipliers
    plan_multipliers = {
        'free': 1,
        'starter': 2,
        'professional': 5,
        'enterprise': 20,
    }

    # Get tenant plan
    try:
        tenant_id = getattr(g, 'tenant_id', None)
        if tenant_id:
            from web.database import Tenant
            tenant = Tenant.query.get(tenant_id)
            if tenant:
                plan = tenant.plan or 'free'
                multiplier = plan_multipliers.get(plan, 1)

                # Parse and multiply the default limit
                base_limit = default_limits.get(operation, "100 per hour")
                parts = base_limit.split()
                if len(parts) >= 3:
                    count = int(parts[0]) * multiplier
                    return f"{count} {parts[1]} {parts[2]}"
    except Exception as e:
        logger.debug(f"Error getting plan rate limit: {e}")

    return default_limits.get(operation, "100 per hour")


def dynamic_rate_limit(operation: str):
    """
    Decorator for dynamic rate limiting based on tenant plan.

    Args:
        operation: Operation type for limit lookup
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if limiter and RATELIMIT_ENABLED:
                limit = get_plan_rate_limit(operation)
                # Apply limit dynamically
                with limiter.limit(limit):
                    return f(*args, **kwargs)
            return f(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# RATE LIMIT MONITORING
# =============================================================================

def get_rate_limit_status(key: str = None) -> dict:
    """
    Get current rate limit status for a key.

    Args:
        key: Rate limit key (uses current request key if None)

    Returns:
        Dict with limit, remaining, reset info
    """
    if not limiter or not RATELIMIT_ENABLED:
        return {'enabled': False}

    try:
        key = key or get_rate_limit_key()
        # This is a simplified status - actual implementation
        # would need to query the storage backend
        return {
            'enabled': True,
            'key': key,
            'storage': RATELIMIT_STORAGE_URL,
        }
    except Exception as e:
        return {'enabled': True, 'error': str(e)}


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'init_rate_limiter',
    'limiter',
    'rate_limit',
    'rate_limit_by_ip',
    'rate_limit_by_tenant',
    'exempt_from_rate_limit',
    'RateLimits',
    'get_plan_rate_limit',
    'dynamic_rate_limit',
    'get_rate_limit_status',
    'LIMITER_AVAILABLE',
    'RATELIMIT_ENABLED',
]
