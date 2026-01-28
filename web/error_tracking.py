"""
Error Tracking Configuration for IT Due Diligence Agent (Phase 7)

Integrates Sentry for:
- Error capture and alerting
- Performance monitoring (APM)
- Release tracking
- User context
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
SENTRY_ENVIRONMENT = os.environ.get('SENTRY_ENVIRONMENT', 'development')
SENTRY_RELEASE = os.environ.get('SENTRY_RELEASE', 'it-diligence-agent@1.0.0')
SENTRY_TRACES_SAMPLE_RATE = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
SENTRY_PROFILES_SAMPLE_RATE = float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.1'))

# Check if Sentry is available
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None


# =============================================================================
# SENTRY INITIALIZATION
# =============================================================================

def init_sentry(app=None):
    """
    Initialize Sentry error tracking.

    Args:
        app: Flask application instance (optional)

    Returns:
        bool: True if Sentry was initialized successfully
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry SDK not installed. Error tracking disabled.")
        return False

    if not SENTRY_DSN:
        logger.info("SENTRY_DSN not configured. Error tracking disabled.")
        return False

    try:
        integrations = [
            FlaskIntegration(transaction_style="url"),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ]

        # Add optional integrations
        try:
            integrations.append(CeleryIntegration())
        except Exception:
            pass

        try:
            integrations.append(RedisIntegration())
        except Exception:
            pass

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENVIRONMENT,
            release=SENTRY_RELEASE,
            integrations=integrations,

            # Performance monitoring
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,

            # Data scrubbing
            send_default_pii=False,
            before_send=before_send_filter,
            before_send_transaction=before_send_transaction_filter,

            # Additional options
            attach_stacktrace=True,
            include_local_variables=True,
            max_breadcrumbs=50,
        )

        logger.info(
            f"Sentry initialized: environment={SENTRY_ENVIRONMENT}, "
            f"release={SENTRY_RELEASE}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def before_send_filter(event, hint):
    """
    Filter and modify events before sending to Sentry.

    - Remove sensitive data
    - Filter out noisy errors
    - Add custom context
    """
    # Don't send certain types of errors
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        # Filter out common non-critical errors
        ignored_exceptions = (
            ConnectionResetError,
            BrokenPipeError,
        )
        if isinstance(exc_value, ignored_exceptions):
            return None

        # Filter 404 errors
        if hasattr(exc_value, 'code') and exc_value.code == 404:
            return None

    # Scrub sensitive data from request
    if 'request' in event:
        request_data = event['request']

        # Remove sensitive headers
        if 'headers' in request_data:
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                if header in request_data['headers']:
                    request_data['headers'][header] = '[REDACTED]'

        # Remove sensitive POST data
        if 'data' in request_data and isinstance(request_data['data'], dict):
            sensitive_fields = ['password', 'token', 'secret', 'api_key']
            for field in sensitive_fields:
                if field in request_data['data']:
                    request_data['data'][field] = '[REDACTED]'

    return event


def before_send_transaction_filter(event, hint):
    """
    Filter transactions before sending to Sentry.

    - Filter out health checks
    - Filter static file requests
    """
    transaction_name = event.get('transaction', '')

    # Don't track health checks or static files
    if any(path in transaction_name for path in ['/health', '/static/', '/favicon']):
        return None

    return event


# =============================================================================
# USER CONTEXT
# =============================================================================

def set_user_context(user_id: str = None, email: str = None, tenant_id: str = None):
    """Set user context for Sentry events."""
    if not SENTRY_AVAILABLE or not sentry_sdk.Hub.current.client:
        return

    user_data = {}
    if user_id:
        user_data['id'] = user_id
    if email:
        user_data['email'] = email

    if user_data:
        sentry_sdk.set_user(user_data)

    if tenant_id:
        sentry_sdk.set_tag('tenant_id', tenant_id)


def clear_user_context():
    """Clear user context."""
    if SENTRY_AVAILABLE and sentry_sdk.Hub.current.client:
        sentry_sdk.set_user(None)


# =============================================================================
# CUSTOM CONTEXT & TAGS
# =============================================================================

def set_context(name: str, data: Dict[str, Any]):
    """Set custom context for Sentry events."""
    if SENTRY_AVAILABLE and sentry_sdk.Hub.current.client:
        sentry_sdk.set_context(name, data)


def set_tag(key: str, value: str):
    """Set a tag for Sentry events."""
    if SENTRY_AVAILABLE and sentry_sdk.Hub.current.client:
        sentry_sdk.set_tag(key, value)


def add_breadcrumb(
    message: str,
    category: str = 'default',
    level: str = 'info',
    data: Dict[str, Any] = None
):
    """Add a breadcrumb for debugging."""
    if SENTRY_AVAILABLE and sentry_sdk.Hub.current.client:
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )


# =============================================================================
# ERROR CAPTURE
# =============================================================================

def capture_exception(error: Exception = None, **extra):
    """
    Capture an exception and send to Sentry.

    Args:
        error: Exception to capture (uses current exception if None)
        **extra: Additional context to attach
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.Hub.current.client:
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)

        if error:
            return sentry_sdk.capture_exception(error)
        else:
            return sentry_sdk.capture_exception()


def capture_message(message: str, level: str = 'info', **extra):
    """
    Capture a message and send to Sentry.

    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **extra: Additional context to attach
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.Hub.current.client:
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)

        return sentry_sdk.capture_message(message, level=level)


# =============================================================================
# PERFORMANCE MONITORING
# =============================================================================

def start_transaction(name: str, op: str = 'task'):
    """
    Start a performance transaction.

    Args:
        name: Transaction name
        op: Operation type (e.g., 'task', 'celery.task', 'analysis')

    Returns:
        Transaction object or None
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.Hub.current.client:
        return None

    return sentry_sdk.start_transaction(name=name, op=op)


def trace_function(op: str = 'function'):
    """
    Decorator to trace function execution.

    Args:
        op: Operation type
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not SENTRY_AVAILABLE or not sentry_sdk.Hub.current.client:
                return func(*args, **kwargs)

            with sentry_sdk.start_span(op=op, description=func.__name__):
                return func(*args, **kwargs)

        return wrapper
    return decorator


# =============================================================================
# FLASK INTEGRATION
# =============================================================================

def setup_flask_error_handlers(app):
    """Setup Flask error handlers with Sentry integration."""

    @app.before_request
    def sentry_before_request():
        """Set Sentry context from Flask request."""
        from flask import g, request
        from flask_login import current_user

        # Set user context
        if current_user and current_user.is_authenticated:
            set_user_context(
                user_id=current_user.id,
                email=getattr(current_user, 'email', None),
                tenant_id=getattr(current_user, 'tenant_id', None)
            )

        # Set tenant context
        tenant_id = getattr(g, 'tenant_id', None)
        if tenant_id:
            set_tag('tenant_id', tenant_id)

        # Add request breadcrumb
        add_breadcrumb(
            message=f"{request.method} {request.path}",
            category='http',
            level='info',
            data={'url': request.url}
        )

    @app.teardown_request
    def sentry_teardown_request(exception):
        """Clear Sentry context after request."""
        clear_user_context()


# =============================================================================
# ANALYSIS TRACKING
# =============================================================================

def track_analysis_start(deal_id: str, domains: list, document_count: int):
    """Track analysis start for monitoring."""
    set_context('analysis', {
        'deal_id': deal_id,
        'domains': domains,
        'document_count': document_count,
    })
    add_breadcrumb(
        message=f"Analysis started for deal {deal_id}",
        category='analysis',
        level='info',
        data={'domains': domains, 'documents': document_count}
    )


def track_analysis_complete(deal_id: str, facts_count: int, findings_count: int, duration_seconds: float):
    """Track analysis completion for monitoring."""
    add_breadcrumb(
        message=f"Analysis completed for deal {deal_id}",
        category='analysis',
        level='info',
        data={
            'facts': facts_count,
            'findings': findings_count,
            'duration_seconds': duration_seconds
        }
    )


def track_analysis_error(deal_id: str, error: str, phase: str = None):
    """Track analysis error for monitoring."""
    capture_message(
        f"Analysis failed for deal {deal_id}: {error}",
        level='error',
        deal_id=deal_id,
        phase=phase
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'init_sentry',
    'SENTRY_AVAILABLE',
    'set_user_context',
    'clear_user_context',
    'set_context',
    'set_tag',
    'add_breadcrumb',
    'capture_exception',
    'capture_message',
    'start_transaction',
    'trace_function',
    'setup_flask_error_handlers',
    'track_analysis_start',
    'track_analysis_complete',
    'track_analysis_error',
]
