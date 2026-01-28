"""
Tenant Isolation Middleware for Multi-Tenancy (Phase 6)

Handles tenant resolution and ensures data isolation between organizations.
"""

import os
from functools import wraps
from typing import Optional, Callable

from flask import g, request, abort, current_app
from flask_login import current_user


def resolve_tenant_id() -> Optional[str]:
    """
    Resolve the tenant ID from the current request context.

    Resolution order:
    1. X-Tenant-ID header (for API clients)
    2. Subdomain (e.g., acme.diligence.app)
    3. Current user's tenant (for authenticated requests)
    4. Default tenant from environment (for development)

    Returns:
        Tenant ID string or None if not resolved
    """
    # 1. Check X-Tenant-ID header (useful for API integrations)
    header_tenant = request.headers.get('X-Tenant-ID')
    if header_tenant:
        return header_tenant

    # 2. Check subdomain
    host = request.host.lower()
    # Skip subdomain extraction for localhost/IP addresses
    if not host.startswith('localhost') and not host[0].isdigit():
        parts = host.split('.')
        if len(parts) >= 3:  # subdomain.domain.tld
            subdomain = parts[0]
            if subdomain not in ('www', 'api', 'app'):
                # Need to look up tenant by slug
                from web.database import Tenant
                tenant = Tenant.query.filter_by(slug=subdomain, active=True).first()
                if tenant:
                    return tenant.id

    # 3. Check current user's tenant
    if current_user and current_user.is_authenticated:
        if hasattr(current_user, 'tenant_id') and current_user.tenant_id:
            return current_user.tenant_id

    # 4. Fall back to default tenant (for development/testing)
    default_tenant = os.environ.get('DEFAULT_TENANT_ID')
    if default_tenant:
        return default_tenant

    return None


def set_tenant():
    """
    Before-request hook to set the current tenant in Flask's g object.

    This should be registered with the Flask app:
        app.before_request(set_tenant)
    """
    # Skip tenant resolution for public routes
    public_endpoints = {
        'static', 'health_check', 'login', 'register', 'forgot_password',
        'reset_password', 'index', None
    }

    if request.endpoint in public_endpoints:
        g.tenant_id = None
        return

    g.tenant_id = resolve_tenant_id()


def require_tenant(f: Callable) -> Callable:
    """
    Decorator to require a valid tenant for a route.

    Usage:
        @app.route('/api/deals')
        @require_tenant
        def list_deals():
            # g.tenant_id is guaranteed to be set
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(g, 'tenant_id', None):
            abort(403, description="No tenant context. Please authenticate or provide X-Tenant-ID header.")
        return f(*args, **kwargs)
    return decorated_function


def tenant_scoped_query(model_class, **extra_filters):
    """
    Create a query that's automatically scoped to the current tenant.

    Usage:
        deals = tenant_scoped_query(Deal).all()
        active_deals = tenant_scoped_query(Deal, status='active').all()

    Args:
        model_class: SQLAlchemy model class with tenant_id column
        **extra_filters: Additional filter conditions

    Returns:
        Scoped query object
    """
    from web.database import db

    query = model_class.query

    # Apply tenant filter if tenant context exists
    tenant_id = getattr(g, 'tenant_id', None)
    if tenant_id and hasattr(model_class, 'tenant_id'):
        query = query.filter(model_class.tenant_id == tenant_id)

    # Apply additional filters
    if extra_filters:
        query = query.filter_by(**extra_filters)

    return query


class TenantMixin:
    """
    Mixin for services that need tenant-aware operations.

    Usage:
        class DealService(TenantMixin):
            def list_deals(self):
                return self.scoped_query(Deal).all()
    """

    def get_tenant_id(self) -> Optional[str]:
        """Get current tenant ID from Flask g object."""
        return getattr(g, 'tenant_id', None)

    def scoped_query(self, model_class, **filters):
        """Create a tenant-scoped query."""
        return tenant_scoped_query(model_class, **filters)

    def ensure_tenant(self, obj):
        """
        Ensure an object has the current tenant_id set.

        Call this before saving new objects to automatically set tenant.
        """
        tenant_id = self.get_tenant_id()
        if tenant_id and hasattr(obj, 'tenant_id'):
            if not obj.tenant_id:
                obj.tenant_id = tenant_id
        return obj


def validate_tenant_access(resource_tenant_id: Optional[str]) -> bool:
    """
    Validate that the current tenant can access a resource.

    Args:
        resource_tenant_id: The tenant_id of the resource being accessed

    Returns:
        True if access is allowed, False otherwise
    """
    current_tenant = getattr(g, 'tenant_id', None)

    # No tenant context = no access to tenant-specific resources
    if not current_tenant:
        return resource_tenant_id is None

    # Tenant must match
    return resource_tenant_id == current_tenant


def require_same_tenant(resource_tenant_id: Optional[str]):
    """
    Abort with 403 if the resource doesn't belong to the current tenant.

    Usage:
        deal = Deal.query.get(deal_id)
        require_same_tenant(deal.tenant_id)
    """
    if not validate_tenant_access(resource_tenant_id):
        abort(403, description="Access denied: resource belongs to a different organization.")


# =============================================================================
# ADMIN/SUPER-TENANT SUPPORT
# =============================================================================

def is_super_admin() -> bool:
    """
    Check if the current user is a super admin who can access all tenants.

    Super admins are identified by:
    - Having 'super_admin' role
    - Having no tenant_id (platform-level user)
    """
    if not current_user or not current_user.is_authenticated:
        return False

    # Check for super_admin role
    if hasattr(current_user, 'roles') and 'super_admin' in (current_user.roles or []):
        return True

    return False


def get_accessible_tenant_ids() -> Optional[list]:
    """
    Get list of tenant IDs the current user can access.

    Returns:
        List of tenant IDs, or None if user can access all (super admin)
    """
    if is_super_admin():
        return None  # Can access all

    tenant_id = getattr(g, 'tenant_id', None)
    if tenant_id:
        return [tenant_id]

    return []


# =============================================================================
# TENANT INITIALIZATION
# =============================================================================

def create_default_tenant(app):
    """
    Create a default tenant for development/testing if none exists.

    This should be called during app initialization.
    """
    with app.app_context():
        from web.database import db, Tenant

        # Check if any tenant exists
        if Tenant.query.first() is None:
            default_tenant = Tenant(
                name='Default Organization',
                slug='default',
                plan='free',
                max_users=100,
                max_deals=1000,
                max_storage_mb=10000,
            )
            db.session.add(default_tenant)
            db.session.commit()

            # Set as default tenant in environment
            os.environ.setdefault('DEFAULT_TENANT_ID', default_tenant.id)

            current_app.logger.info(f"Created default tenant: {default_tenant.id}")
            return default_tenant

    return None


def assign_user_to_tenant(user, tenant_id: str):
    """
    Assign a user to a tenant.

    Args:
        user: User model instance
        tenant_id: ID of the tenant to assign
    """
    from web.database import db, Tenant

    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")

    if not tenant.is_within_user_limit():
        raise ValueError(f"Tenant {tenant.name} has reached its user limit")

    user.tenant_id = tenant_id
    db.session.commit()
