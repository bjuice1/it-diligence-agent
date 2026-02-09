"""
Permission helpers for deal access control.

This module provides functions to check if users have permission to access deals.
Used by API endpoints and UI components to enforce access control.
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from web.database import User, Deal


def user_can_access_deal(user: 'User', deal: 'Deal') -> bool:
    """
    Check if a user has permission to access a deal.

    Permission rules:
    1. User owns the deal (deal.owner_id == user.id)
    2. User is in the same tenant as the deal (multi-tenancy enabled)
    3. Deal is shared with user (future: explicit share table)

    Args:
        user: The User object
        deal: The Deal object

    Returns:
        True if user can access, False otherwise

    Example:
        >>> if user_can_access_deal(current_user, deal):
        >>>     # User has access
        >>>     pass
    """
    if not user or not deal:
        return False

    # Check if deal is deleted
    if deal.is_deleted:
        return False

    # Rule 1: Owner has full access
    if deal.owner_id == user.id:
        return True

    # Rule 2: Same tenant (if multi-tenancy enabled)
    USE_MULTI_TENANCY = os.environ.get('USE_MULTI_TENANCY', 'false').lower() == 'true'
    if USE_MULTI_TENANCY and user.tenant_id and user.tenant_id == deal.tenant_id:
        return True

    # Rule 3: Explicit share (future enhancement)
    # Check if deal is shared with user via DealShare table
    # if DealShare.query.filter_by(deal_id=deal.id, user_id=user.id).first():
    #     return True

    # Default: no access
    return False


def user_can_modify_deal(user: 'User', deal: 'Deal') -> bool:
    """
    Check if a user has permission to modify a deal.

    Modification permission is more restrictive than read access:
    - User must be the owner (not just same tenant)
    - Or user must have admin role

    Args:
        user: The User object
        deal: The Deal object

    Returns:
        True if user can modify, False otherwise

    Example:
        >>> if user_can_modify_deal(current_user, deal):
        >>>     deal.target_name = "New Name"
        >>>     db.session.commit()
    """
    if not user or not deal:
        return False

    # Cannot modify deleted deals
    if deal.is_deleted:
        return False

    # Owner can always modify
    if deal.owner_id == user.id:
        return True

    # Admin can modify any deal in their tenant
    if user.is_admin():
        USE_MULTI_TENANCY = os.environ.get('USE_MULTI_TENANCY', 'false').lower() == 'true'
        if USE_MULTI_TENANCY and user.tenant_id == deal.tenant_id:
            return True
        elif not USE_MULTI_TENANCY:
            return True

    return False


def get_user_deals(user: 'User', include_tenant_deals: bool = True):
    """
    Get all deals accessible by a user.

    Args:
        user: The User object
        include_tenant_deals: If True, include deals from same tenant (when multi-tenancy enabled)

    Returns:
        Query object for deals the user can access

    Example:
        >>> deals = get_user_deals(current_user).all()
        >>> for deal in deals:
        >>>     print(deal.target_name)
    """
    from web.database import Deal

    # Start with deals owned by user
    query = Deal.query.filter_by(owner_id=user.id, deleted_at=None)

    # Add tenant deals if multi-tenancy enabled
    if include_tenant_deals:
        USE_MULTI_TENANCY = os.environ.get('USE_MULTI_TENANCY', 'false').lower() == 'true'
        if USE_MULTI_TENANCY and user.tenant_id:
            # Get deals in same tenant (not owned by user)
            from sqlalchemy import and_, or_
            query = Deal.query.filter(
                and_(
                    Deal.deleted_at.is_(None),
                    or_(
                        Deal.owner_id == user.id,
                        Deal.tenant_id == user.tenant_id
                    )
                )
            )

    return query
