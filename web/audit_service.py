"""
Audit Trail Service for IT Due Diligence Agent (Phase 7)

Provides comprehensive audit logging for:
- User actions
- Data changes
- System events
- Compliance tracking
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# AUDIT CONFIGURATION
# =============================================================================

AUDIT_ENABLED = os.environ.get('AUDIT_ENABLED', 'true').lower() == 'true'
AUDIT_RETENTION_DAYS = int(os.environ.get('AUDIT_RETENTION_DAYS', '365'))
AUDIT_SENSITIVE_FIELDS = {'password', 'token', 'secret', 'api_key', 'credit_card'}


# =============================================================================
# AUDIT EVENT TYPES
# =============================================================================

class AuditAction(str, Enum):
    """Standard audit action types."""

    # Authentication
    LOGIN = "auth.login"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGE = "auth.password_change"
    PASSWORD_RESET = "auth.password_reset"

    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role_change"

    # Tenant Management
    TENANT_CREATE = "tenant.create"
    TENANT_UPDATE = "tenant.update"
    TENANT_SUSPEND = "tenant.suspend"

    # Deal Management
    DEAL_CREATE = "deal.create"
    DEAL_UPDATE = "deal.update"
    DEAL_DELETE = "deal.delete"
    DEAL_ARCHIVE = "deal.archive"

    # Document Operations
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_DELETE = "document.delete"
    DOCUMENT_DOWNLOAD = "document.download"
    DOCUMENT_PROCESS = "document.process"

    # Analysis
    ANALYSIS_START = "analysis.start"
    ANALYSIS_COMPLETE = "analysis.complete"
    ANALYSIS_CANCEL = "analysis.cancel"
    ANALYSIS_FAIL = "analysis.fail"

    # Fact Operations
    FACT_CREATE = "fact.create"
    FACT_UPDATE = "fact.update"
    FACT_DELETE = "fact.delete"
    FACT_VERIFY = "fact.verify"

    # Finding Operations
    FINDING_CREATE = "finding.create"
    FINDING_UPDATE = "finding.update"
    FINDING_DELETE = "finding.delete"

    # Export Operations
    EXPORT_CREATE = "export.create"
    EXPORT_DOWNLOAD = "export.download"

    # System Events
    SYSTEM_ERROR = "system.error"
    SYSTEM_CONFIG_CHANGE = "system.config_change"

    # Data Access
    DATA_VIEW = "data.view"
    DATA_EXPORT = "data.export"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# AUDIT SERVICE
# =============================================================================

class AuditService:
    """
    Service for recording and querying audit events.

    Supports both database and file-based storage.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._use_database = False
        self._file_path = None
        self._initialized = True

    def configure(self, use_database: bool = False, file_path: str = None):
        """Configure the audit service."""
        self._use_database = use_database

        if file_path:
            self._file_path = file_path
        else:
            from config_v2 import OUTPUT_DIR
            self._file_path = OUTPUT_DIR / 'audit' / 'audit_log.jsonl'
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        severity: str = AuditSeverity.INFO,
        user_id: str = None,
        tenant_id: str = None,
        deal_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        old_value: Any = None,
        new_value: Any = None,
    ):
        """
        Log an audit event.

        Args:
            action: Action type (use AuditAction enum)
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional event details
            severity: Event severity level
            user_id: User who performed the action
            tenant_id: Tenant context
            deal_id: Deal context if applicable
            ip_address: Request IP address
            user_agent: Request user agent
            old_value: Previous value (for updates)
            new_value: New value (for updates)
        """
        if not AUDIT_ENABLED:
            return

        # Get context from Flask if not provided
        if not user_id or not ip_address:
            try:
                from flask import request, g
                from flask_login import current_user

                if not user_id and current_user and current_user.is_authenticated:
                    user_id = current_user.id
                if not tenant_id:
                    tenant_id = getattr(g, 'tenant_id', None)
                if not ip_address:
                    ip_address = request.remote_addr
                if not user_agent:
                    user_agent = str(request.user_agent)[:255] if request.user_agent else None
            except Exception:
                pass

        # Sanitize sensitive data
        if details:
            details = self._sanitize_data(details)
        if old_value:
            old_value = self._sanitize_data(old_value)
        if new_value:
            new_value = self._sanitize_data(new_value)

        event = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action': action,
            'severity': severity,
            'user_id': user_id,
            'tenant_id': tenant_id,
            'deal_id': deal_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details or {},
            'ip_address': ip_address,
            'user_agent': user_agent,
        }

        # Add change tracking if values provided
        if old_value is not None or new_value is not None:
            event['changes'] = {
                'old': old_value,
                'new': new_value,
            }

        # Store the event
        if self._use_database:
            self._log_to_database(event)
        else:
            self._log_to_file(event)

        # Also log to standard logger for immediate visibility
        log_message = f"AUDIT: {action} - resource={resource_type}:{resource_id} user={user_id}"
        if severity == AuditSeverity.ERROR:
            logger.error(log_message)
        elif severity == AuditSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def _sanitize_data(self, data: Any) -> Any:
        """Remove sensitive fields from data."""
        if isinstance(data, dict):
            return {
                k: '[REDACTED]' if k.lower() in AUDIT_SENSITIVE_FIELDS else self._sanitize_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        return data

    def _log_to_database(self, event: dict):
        """Log event to database."""
        try:
            from web.database import db, AuditLog

            audit_entry = AuditLog(
                tenant_id=event.get('tenant_id'),
                deal_id=event.get('deal_id'),
                user_id=event.get('user_id'),
                action=event['action'],
                resource_type=event.get('resource_type'),
                resource_id=event.get('resource_id'),
                details=event.get('details'),
                ip_address=event.get('ip_address'),
                user_agent=event.get('user_agent'),
            )
            db.session.add(audit_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to write audit to database: {e}")
            # Fall back to file
            self._log_to_file(event)

    def _log_to_file(self, event: dict):
        """Log event to JSONL file."""
        try:
            with open(self._file_path, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit to file: {e}")

    def query(
        self,
        action: str = None,
        user_id: str = None,
        tenant_id: str = None,
        deal_id: str = None,
        resource_type: str = None,
        resource_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        severity: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        """
        Query audit events.

        Returns:
            List of matching audit events
        """
        kwargs = {
            'action': action,
            'user_id': user_id,
            'tenant_id': tenant_id,
            'deal_id': deal_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'start_date': start_date,
            'end_date': end_date,
            'severity': severity,
            'limit': limit,
            'offset': offset,
        }

        if self._use_database:
            return self._query_database(**kwargs)
        else:
            return self._query_file(**kwargs)

    def _query_database(self, **kwargs) -> List[dict]:
        """Query audit events from database."""
        try:
            from web.database import AuditLog

            query = AuditLog.query

            if kwargs.get('action'):
                query = query.filter(AuditLog.action == kwargs['action'])
            if kwargs.get('user_id'):
                query = query.filter(AuditLog.user_id == kwargs['user_id'])
            if kwargs.get('tenant_id'):
                query = query.filter(AuditLog.tenant_id == kwargs['tenant_id'])
            if kwargs.get('deal_id'):
                query = query.filter(AuditLog.deal_id == kwargs['deal_id'])
            if kwargs.get('resource_type'):
                query = query.filter(AuditLog.resource_type == kwargs['resource_type'])
            if kwargs.get('start_date'):
                query = query.filter(AuditLog.created_at >= kwargs['start_date'])
            if kwargs.get('end_date'):
                query = query.filter(AuditLog.created_at <= kwargs['end_date'])

            query = query.order_by(AuditLog.created_at.desc())
            query = query.offset(kwargs.get('offset', 0))
            query = query.limit(kwargs.get('limit', 100))

            return [e.to_dict() for e in query.all()]
        except Exception as e:
            logger.error(f"Failed to query audit database: {e}")
            return []

    def _query_file(self, **kwargs) -> List[dict]:
        """Query audit events from file."""
        try:
            if not self._file_path.exists():
                return []

            results = []
            with open(self._file_path, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())

                        # Apply filters
                        if kwargs.get('action') and event.get('action') != kwargs['action']:
                            continue
                        if kwargs.get('user_id') and event.get('user_id') != kwargs['user_id']:
                            continue
                        if kwargs.get('tenant_id') and event.get('tenant_id') != kwargs['tenant_id']:
                            continue
                        if kwargs.get('deal_id') and event.get('deal_id') != kwargs['deal_id']:
                            continue
                        if kwargs.get('resource_type') and event.get('resource_type') != kwargs['resource_type']:
                            continue

                        results.append(event)
                    except json.JSONDecodeError:
                        continue

            # Sort by timestamp descending
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            # Apply pagination
            offset = kwargs.get('offset', 0)
            limit = kwargs.get('limit', 100)
            return results[offset:offset + limit]

        except Exception as e:
            logger.error(f"Failed to query audit file: {e}")
            return []

    def cleanup_old_events(self, days: int = None):
        """Remove audit events older than retention period."""
        days = days or AUDIT_RETENTION_DAYS
        cutoff = datetime.utcnow() - timedelta(days=days)

        if self._use_database:
            try:
                from web.database import db, AuditLog
                deleted = AuditLog.query.filter(
                    AuditLog.created_at < cutoff
                ).delete()
                db.session.commit()
                logger.info(f"Cleaned up {deleted} old audit entries")
            except Exception as e:
                logger.error(f"Failed to cleanup audit database: {e}")
        else:
            # For file-based, we'd need to rewrite the file
            # This is a simplified implementation
            logger.info("File-based audit cleanup not implemented")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global audit service instance
audit_service = AuditService()


def audit_log(
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    **kwargs
):
    """Convenience function to log an audit event."""
    audit_service.log(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        **kwargs
    )


def audit_action(action: str, resource_type: str = None):
    """
    Decorator to automatically audit a function call.

    Args:
        action: Audit action type
        resource_type: Resource type being acted on
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Execute the function
            result = f(*args, **kwargs)

            # Log the audit event
            audit_log(
                action=action,
                resource_type=resource_type,
                details={'function': f.__name__}
            )

            return result
        return wrapper
    return decorator


def audit_data_change(action: str, resource_type: str):
    """
    Decorator to audit data changes with before/after values.

    Expects the decorated function to return a tuple of (result, old_value, new_value).
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)

            # Check if function returns change tracking info
            if isinstance(result, tuple) and len(result) == 3:
                actual_result, old_value, new_value = result
                audit_log(
                    action=action,
                    resource_type=resource_type,
                    old_value=old_value,
                    new_value=new_value,
                    details={'function': f.__name__}
                )
                return actual_result
            else:
                audit_log(
                    action=action,
                    resource_type=resource_type,
                    details={'function': f.__name__}
                )
                return result

        return wrapper
    return decorator


# =============================================================================
# FLASK INTEGRATION
# =============================================================================

def setup_audit_logging(app):
    """Setup audit logging for Flask app."""

    # Configure audit service
    use_db = os.environ.get('USE_DATABASE', 'false').lower() == 'true'
    audit_service.configure(use_database=use_db)

    @app.after_request
    def audit_request(response):
        """Audit sensitive requests automatically."""
        from flask import request

        # Only audit non-GET requests and certain paths
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            # Skip health checks and static files
            if not any(p in request.path for p in ['/health', '/static/', '/api/status']):
                audit_log(
                    action=f"http.{request.method.lower()}",
                    resource_type='endpoint',
                    resource_id=request.endpoint,
                    details={
                        'path': request.path,
                        'status_code': response.status_code,
                    }
                )

        return response


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'AuditService',
    'AuditAction',
    'AuditSeverity',
    'audit_service',
    'audit_log',
    'audit_action',
    'audit_data_change',
    'setup_audit_logging',
    'AUDIT_ENABLED',
]
