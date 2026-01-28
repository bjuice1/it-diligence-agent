"""
Structured Logging Configuration for IT Due Diligence Agent (Phase 7)

Provides structured JSON logging with context propagation for:
- Request tracing
- User/tenant context
- Performance metrics
- Error tracking
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Try to import structlog, fall back to standard logging if not available
try:
    import structlog
    from structlog.stdlib import BoundLogger
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog = None


# =============================================================================
# CONFIGURATION
# =============================================================================

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json')  # 'json' or 'console'
LOG_OUTPUT = os.environ.get('LOG_OUTPUT', 'stdout')  # 'stdout', 'file', or path


def get_log_level():
    """Convert string log level to logging constant."""
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    return levels.get(LOG_LEVEL, logging.INFO)


# =============================================================================
# STRUCTLOG PROCESSORS
# =============================================================================

def add_app_context(logger, method_name, event_dict):
    """Add application context to all log events."""
    event_dict['app'] = 'it-diligence-agent'
    event_dict['version'] = '1.0.0'
    return event_dict


def add_timestamp(logger, method_name, event_dict):
    """Add ISO timestamp to log events."""
    event_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    return event_dict


def add_request_context(logger, method_name, event_dict):
    """Add Flask request context if available."""
    try:
        from flask import request, g, has_request_context
        if has_request_context():
            event_dict['request_id'] = getattr(g, 'request_id', None)
            event_dict['tenant_id'] = getattr(g, 'tenant_id', None)
            event_dict['user_id'] = getattr(g, 'user_id', None)
            event_dict['path'] = request.path
            event_dict['method'] = request.method
            event_dict['ip'] = request.remote_addr
    except Exception:
        pass
    return event_dict


def censor_sensitive_data(logger, method_name, event_dict):
    """Censor sensitive data in logs."""
    sensitive_keys = {'password', 'api_key', 'secret', 'token', 'authorization'}

    def censor_dict(d):
        if isinstance(d, dict):
            return {
                k: '***REDACTED***' if any(s in k.lower() for s in sensitive_keys) else censor_dict(v)
                for k, v in d.items()
            }
        elif isinstance(d, list):
            return [censor_dict(i) for i in d]
        return d

    return censor_dict(event_dict)


# =============================================================================
# LOGGING SETUP
# =============================================================================

def configure_structlog():
    """Configure structlog for structured JSON logging."""
    if not STRUCTLOG_AVAILABLE:
        return configure_stdlib_logging()

    # Shared processors for both structlog and stdlib
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_timestamp,
        add_app_context,
        add_request_context,
        censor_sensitive_data,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if LOG_FORMAT == 'json':
        # JSON format for production
        renderer = structlog.processors.JSONRenderer()
    else:
        # Console format for development
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(get_log_level())

    # Reduce noise from third-party libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)

    return structlog.get_logger()


def configure_stdlib_logging():
    """Fallback to standard library logging if structlog not available."""

    class JsonFormatter(logging.Formatter):
        """Simple JSON formatter for stdlib logging."""

        def format(self, record):
            import json
            log_dict = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'app': 'it-diligence-agent',
            }
            if record.exc_info:
                log_dict['exception'] = self.formatException(record.exc_info)
            return json.dumps(log_dict)

    handler = logging.StreamHandler(sys.stdout)

    if LOG_FORMAT == 'json':
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(get_log_level())

    return logging.getLogger('it-diligence-agent')


def get_logger(name: Optional[str] = None):
    """Get a logger instance."""
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name) if name else structlog.get_logger()
    else:
        return logging.getLogger(name or 'it-diligence-agent')


# =============================================================================
# CONTEXT MANAGEMENT
# =============================================================================

class LogContext:
    """Context manager for adding structured context to logs."""

    def __init__(self, **context):
        self.context = context
        self._token = None

    def __enter__(self):
        if STRUCTLOG_AVAILABLE:
            self._token = structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if STRUCTLOG_AVAILABLE and self._token:
            structlog.contextvars.unbind_contextvars(*self.context.keys())
        return False


def bind_context(**context):
    """Bind context variables for structured logging."""
    if STRUCTLOG_AVAILABLE:
        structlog.contextvars.bind_contextvars(**context)


def clear_context():
    """Clear all context variables."""
    if STRUCTLOG_AVAILABLE:
        structlog.contextvars.clear_contextvars()


# =============================================================================
# PERFORMANCE LOGGING
# =============================================================================

import time
from functools import wraps


def log_performance(operation_name: str = None):
    """Decorator to log function execution time."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            logger = get_logger()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    "operation_completed",
                    operation=name,
                    duration_ms=round(duration_ms, 2),
                    status="success"
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "operation_failed",
                    operation=name,
                    duration_ms=round(duration_ms, 2),
                    status="error",
                    error=str(e),
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


# =============================================================================
# REQUEST LOGGING MIDDLEWARE
# =============================================================================

import uuid


def setup_request_logging(app):
    """Setup request logging middleware for Flask app."""
    logger = get_logger()

    @app.before_request
    def before_request():
        from flask import g, request

        # Generate request ID
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        g.request_start_time = time.time()

        # Bind context for structured logging
        bind_context(
            request_id=g.request_id,
            path=request.path,
            method=request.method
        )

        logger.info(
            "request_started",
            path=request.path,
            method=request.method,
            user_agent=request.user_agent.string[:100] if request.user_agent else None
        )

    @app.after_request
    def after_request(response):
        from flask import g, request

        duration_ms = (time.time() - getattr(g, 'request_start_time', time.time())) * 1000

        logger.info(
            "request_completed",
            path=request.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )

        # Add request ID to response headers
        response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')

        # Clear context
        clear_context()

        return response

    @app.teardown_request
    def teardown_request(exception):
        if exception:
            logger.error(
                "request_error",
                error=str(exception),
                exc_info=True
            )


# =============================================================================
# INITIALIZATION
# =============================================================================

# Auto-configure on import
_logger = None


def init_logging():
    """Initialize logging system."""
    global _logger
    if _logger is None:
        _logger = configure_structlog()
    return _logger


# Export
__all__ = [
    'get_logger',
    'configure_structlog',
    'configure_stdlib_logging',
    'LogContext',
    'bind_context',
    'clear_context',
    'log_performance',
    'setup_request_logging',
    'init_logging',
    'STRUCTLOG_AVAILABLE',
]
