"""
Deal Routes - API and page routes for deal management

Provides:
- Deal CRUD API endpoints
- Deal list and detail pages
- Session/context management
"""

import os
import logging
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, session
from flask_login import current_user, login_required
from functools import wraps

from web.database import db
from web.services.deal_service import get_deal_service, DealStatus

# Auth configuration
AUTH_REQUIRED = os.environ.get('AUTH_REQUIRED', 'true').lower() != 'false'


def auth_optional(f):
    """Decorator that makes auth optional based on AUTH_REQUIRED setting."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if AUTH_REQUIRED and not current_user.is_authenticated:
            from flask_login import login_manager
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get the current authenticated user or None."""
    if current_user.is_authenticated:
        return current_user
    return None


def get_validated_user_id():
    """
    Get a validated user ID that exists in the database.

    Returns:
        tuple: (user_id, tenant_id) - both may be None if no valid user

    This handles the case where:
    - AUTH_REQUIRED=false: Returns (None, None) - anonymous access
    - User is authenticated but not in DB: Syncs user to DB, returns their ID
    - User is authenticated and in DB: Returns their ID
    """
    user = get_current_user()
    if not user:
        return None, None

    user_id = user.id
    tenant_id = getattr(user, 'tenant_id', None)

    # Verify user exists in database
    from web.database import db, User as DBUser
    try:
        db_user = DBUser.query.get(user_id)
        if db_user:
            # User exists in DB, use their tenant_id from DB if available
            return user_id, db_user.tenant_id or tenant_id

        # User authenticated but not in DB - sync them
        logger.info(f"Syncing authenticated user {user_id} to database")
        new_db_user = DBUser(
            id=user_id,
            email=getattr(user, 'email', f'user_{user_id[:8]}@synced.local'),
            password_hash=getattr(user, 'password_hash', 'synced_user_no_password'),
            name=getattr(user, 'name', 'Synced User'),
            tenant_id=tenant_id,
            active=True
        )
        db.session.add(new_db_user)
        db.session.commit()
        logger.info(f"User {user_id} synced to database")
        return user_id, tenant_id

    except Exception as e:
        logger.warning(f"Could not validate/sync user {user_id}: {e}")
        # Fall back to no owner - deal will be anonymous
        db.session.rollback()
        return None, None

logger = logging.getLogger(__name__)

deals_bp = Blueprint('deals', __name__)


def require_deal_access(f):
    """Decorator to check deal access permissions."""
    @wraps(f)
    def decorated(*args, **kwargs):
        deal_id = kwargs.get('deal_id')
        if not deal_id:
            return jsonify({'error': 'Deal ID required'}), 400

        service = get_deal_service()
        deal = service.get_deal(deal_id, include_stats=False)

        if not deal:
            return jsonify({'error': 'Deal not found'}), 404

        # Check ownership (if auth is enabled)
        user = get_current_user()
        if user and deal.owner_id and str(deal.owner_id) != str(user.id):
            return jsonify({'error': 'Access denied'}), 403

        return f(*args, **kwargs)
    return decorated


# =============================================================================
# API Endpoints
# =============================================================================

@deals_bp.route('/api/deals', methods=['GET'])
@auth_optional
def list_deals():
    """
    List all deals for the current user.

    Query params:
        include_archived: bool (default: false)
        sort: string (name, created, accessed, status)
        order: asc/desc
        search: string (search in name/target)
    """
    service = get_deal_service()
    user = get_current_user()
    user_id = user.id if user else None

    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    sort_by = request.args.get('sort', 'accessed')
    order = request.args.get('order', 'desc')
    search = request.args.get('search', '').strip()

    deals = service.get_deals_for_user(
        user_id=user_id,
        include_archived=include_archived,
        include_stats=True
    )

    # Apply search filter
    if search:
        search_lower = search.lower()
        deals = [d for d in deals if
                 search_lower in (d.name or '').lower() or
                 search_lower in (d.target_name or '').lower() or
                 search_lower in (d.buyer_name or '').lower()]

    # Apply sorting
    sort_key = {
        'name': lambda d: (d.name or '').lower(),
        'created': lambda d: d.created_at or '',
        'accessed': lambda d: d.last_accessed_at or d.created_at or '',
        'status': lambda d: d.status or '',
    }.get(sort_by, lambda d: d.last_accessed_at or '')

    deals = sorted(deals, key=sort_key, reverse=(order == 'desc'))

    return jsonify({
        'deals': [_deal_to_dict(d) for d in deals],
        'total': len(deals)
    })


@deals_bp.route('/api/deals', methods=['POST'])
@auth_optional
def create_deal():
    """
    Create a new deal.

    Body:
        name: string (required)
        target_name: string (required)
        buyer_name: string (optional)
        deal_type: string (REQUIRED - acquisition, carveout, divestiture)
        industry: string (optional)
        sub_industry: string (optional)
    """
    service = get_deal_service()
    data = request.get_json() or {}

    # Get validated user ID (handles sync if needed)
    user_id, tenant_id = get_validated_user_id()

    # VALIDATION: Deal type is REQUIRED
    deal_type = data.get('deal_type', '').strip()
    if not deal_type:
        return jsonify({
            'error': 'Deal type is required. Please select Acquisition, Carve-Out, or Divestiture.'
        }), 400

    # VALIDATION: Deal type must be valid enum value
    VALID_DEAL_TYPES = ['acquisition', 'carveout', 'divestiture']
    if deal_type not in VALID_DEAL_TYPES:
        return jsonify({
            'error': f'Invalid deal type: {deal_type}. Must be one of: {", ".join(VALID_DEAL_TYPES)}.'
        }), 400

    deal, error = service.create_deal(
        user_id=user_id,
        name=data.get('name'),
        target_name=data.get('target_name'),
        buyer_name=data.get('buyer_name'),
        deal_type=deal_type,
        industry=data.get('industry'),
        sub_industry=data.get('sub_industry'),
        tenant_id=tenant_id,
        context=data.get('context')
    )

    if error:
        return jsonify({'error': error}), 400

    # Set as active deal
    service.set_active_deal_for_session(str(deal.id))

    return jsonify({
        'deal': _deal_to_dict(deal),
        'message': f'Deal created successfully as {deal_type.upper()}.'
    }), 201


@deals_bp.route('/api/deals/<deal_id>', methods=['GET'])
@auth_optional
@require_deal_access
def get_deal(deal_id):
    """Get deal details."""
    service = get_deal_service()
    deal = service.get_deal(deal_id, include_stats=True)

    if not deal:
        return jsonify({'error': 'Deal not found'}), 404

    return jsonify({
        'deal': _deal_to_dict(deal),
        'summary': service.get_deal_summary(deal_id),
        'progress': service.get_deal_progress(deal_id)
    })


@deals_bp.route('/api/deals/<deal_id>', methods=['PATCH'])
@auth_optional
@require_deal_access
def update_deal(deal_id):
    """
    Update a deal.

    Body can include: name, target_name, buyer_name, deal_type, industry, status
    """
    service = get_deal_service()
    user = get_current_user()
    data = request.get_json() or {}

    # Filter allowed fields
    allowed = ['name', 'target_name', 'buyer_name', 'deal_type', 'industry',
               'sub_industry', 'status', 'context', 'settings']
    updates = {k: v for k, v in data.items() if k in allowed}

    # Validate deal_type if it's being updated
    if 'deal_type' in updates:
        deal_type = updates['deal_type']
        VALID_DEAL_TYPES = ['acquisition', 'carveout', 'divestiture']
        if deal_type and deal_type not in VALID_DEAL_TYPES:
            return jsonify({
                'error': f'Invalid deal type: {deal_type}. Must be one of: {", ".join(VALID_DEAL_TYPES)}.'
            }), 400

    deal, error = service.update_deal(
        deal_id=deal_id,
        user_id=user.id if user else None,
        **updates
    )

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'deal': _deal_to_dict(deal),
        'message': 'Deal updated successfully'
    })


@deals_bp.route('/api/deals/<deal_id>/update_type', methods=['POST'])
@auth_optional
@require_deal_access
def update_deal_type(deal_id):
    """
    Update deal type and provide warning about re-analysis.

    Body:
        deal_type: string (required - acquisition, carveout, divestiture)
    """
    service = get_deal_service()
    user = get_current_user()
    data = request.get_json() or {}

    new_deal_type = data.get('deal_type', '').strip()

    # Validate
    VALID_DEAL_TYPES = ['acquisition', 'carveout', 'divestiture']
    if not new_deal_type or new_deal_type not in VALID_DEAL_TYPES:
        return jsonify({
            'error': f'Invalid deal type. Must be one of: {", ".join(VALID_DEAL_TYPES)}.'
        }), 400

    # Get current deal to log the change
    deal = service.get_deal(deal_id)
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404

    old_type = deal.deal_type

    # Update deal type
    deal, error = service.update_deal(
        deal_id=deal_id,
        user_id=user.id if user else None,
        deal_type=new_deal_type
    )

    if error:
        return jsonify({'error': error}), 400

    logger.info(f"Deal {deal_id} type changed from {old_type} to {new_deal_type}")

    return jsonify({
        'deal': _deal_to_dict(deal),
        'message': f'Deal type changed from {old_type} to {new_deal_type}. Please re-run analysis to update recommendations.'
    })


@deals_bp.route('/api/deals/<deal_id>', methods=['DELETE'])
@auth_optional
@require_deal_access
def delete_deal(deal_id):
    """
    Delete a deal.

    Query params:
        hard: bool (default: false) - permanent deletion
    """
    service = get_deal_service()
    hard_delete = request.args.get('hard', 'false').lower() == 'true'

    success, error = service.delete_deal(deal_id, hard_delete=hard_delete)

    if not success:
        return jsonify({'error': error}), 400

    # Clear active deal if it was this one
    if session.get('current_deal_id') == deal_id:
        service.clear_active_deal()

    return jsonify({'message': 'Deal deleted successfully'})


@deals_bp.route('/api/deals/<deal_id>/archive', methods=['POST'])
@auth_optional
@require_deal_access
def archive_deal(deal_id):
    """Archive a deal."""
    service = get_deal_service()
    success, error = service.archive_deal(deal_id)

    if not success:
        return jsonify({'error': error}), 400

    return jsonify({'message': 'Deal archived successfully'})


@deals_bp.route('/api/deals/<deal_id>/restore', methods=['POST'])
@auth_optional
@require_deal_access
def restore_deal(deal_id):
    """Restore an archived deal."""
    service = get_deal_service()
    success, error = service.restore_deal(deal_id)

    if not success:
        return jsonify({'error': error}), 400

    return jsonify({'message': 'Deal restored successfully'})


@deals_bp.route('/api/deals/<deal_id>/duplicate', methods=['POST'])
@auth_optional
@require_deal_access
def duplicate_deal(deal_id):
    """
    Duplicate a deal as a template.

    Body:
        new_name: string (required)
    """
    service = get_deal_service()
    user = get_current_user()
    data = request.get_json() or {}

    new_name = data.get('new_name')
    if not new_name:
        return jsonify({'error': 'New name is required'}), 400

    deal, error = service.duplicate_deal(
        deal_id=deal_id,
        new_name=new_name,
        user_id=user.id if user else None
    )

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'deal': _deal_to_dict(deal),
        'message': 'Deal duplicated successfully'
    }), 201


@deals_bp.route('/api/deals/<deal_id>/export', methods=['GET'])
@auth_optional
@require_deal_access
def export_deal(deal_id):
    """Export deal data as JSON."""
    service = get_deal_service()
    data = service.export_deal(deal_id)

    if not data:
        return jsonify({'error': 'Deal not found'}), 404

    return jsonify(data)


@deals_bp.route('/api/deals/import', methods=['POST'])
@auth_optional
def import_deal():
    """
    Import a deal from JSON.

    Body:
        data: object (exported deal data)
        new_name: string (optional)
    """
    service = get_deal_service()
    user = get_current_user()
    body = request.get_json() or {}

    import_data = body.get('data')
    if not import_data:
        return jsonify({'error': 'Import data is required'}), 400

    deal, error = service.import_deal(
        data=import_data,
        user_id=user.id if user else None,
        new_name=body.get('new_name')
    )

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'deal': _deal_to_dict(deal),
        'message': 'Deal imported successfully'
    }), 201


# =============================================================================
# Session/Context API
# =============================================================================

@deals_bp.route('/api/session/deal', methods=['GET'])
@auth_optional
def get_current_deal():
    """Get the currently active deal for this session."""
    service = get_deal_service()
    deal = service.get_active_deal_for_session()

    if not deal:
        return jsonify({'deal': None})

    return jsonify({
        'deal': _deal_to_dict(deal),
        'summary': service.get_deal_summary(str(deal.id))
    })


@deals_bp.route('/api/session/deal', methods=['POST'])
@auth_optional
def set_current_deal():
    """
    Set the active deal for this session.

    Body:
        deal_id: string (required)
    """
    service = get_deal_service()
    data = request.get_json() or {}

    deal_id = data.get('deal_id')
    if not deal_id:
        return jsonify({'error': 'Deal ID is required'}), 400

    success = service.set_active_deal_for_session(deal_id)
    if not success:
        return jsonify({'error': 'Deal not found'}), 404

    deal = service.get_deal(deal_id)
    return jsonify({
        'deal': _deal_to_dict(deal),
        'message': 'Active deal updated'
    })


@deals_bp.route('/api/session/deal/clear', methods=['POST'])
@auth_optional
def clear_current_deal():
    """Clear the active deal selection."""
    service = get_deal_service()
    service.clear_active_deal()
    return jsonify({'message': 'Active deal cleared'})


# =============================================================================
# Page Routes
# =============================================================================

@deals_bp.route('/deals')
@auth_optional
def deals_list_page():
    """Deals list page."""
    return render_template('deals/list.html')


@deals_bp.route('/deals/new')
@auth_optional
def new_deal_page():
    """New deal page/modal."""
    return render_template('deals/new.html')


@deals_bp.route('/deals/<deal_id>')
@auth_optional
@require_deal_access
def deal_detail_page(deal_id):
    """Deal detail page."""
    service = get_deal_service()
    deal = service.get_deal(deal_id)

    if not deal:
        return redirect(url_for('deals.deals_list_page'))

    # IMPORTANT: Set this as the active deal to ensure proper data isolation
    # This ensures get_session() loads the correct deal's data
    service.set_active_deal_for_session(deal_id)

    summary = service.get_deal_summary(deal_id)
    progress = service.get_deal_progress(deal_id)

    return render_template(
        'deals/detail.html',
        deal=deal,
        summary=summary,
        progress=progress
    )


@deals_bp.route('/deals/<deal_id>/settings')
@auth_optional
@require_deal_access
def deal_settings_page(deal_id):
    """Deal settings page."""
    service = get_deal_service()
    deal = service.get_deal(deal_id)

    if not deal:
        return redirect(url_for('deals.deals_list_page'))

    # Ensure deal context is set
    service.set_active_deal_for_session(deal_id)

    return render_template('deals/settings.html', deal=deal)


# =============================================================================
# Helper Functions
# =============================================================================

def _deal_to_dict(deal) -> dict:
    """Convert Deal model to API response dict."""
    if not deal:
        return {}

    return {
        'id': str(deal.id),
        'name': deal.name,
        'target_name': deal.target_name,
        'buyer_name': deal.buyer_name,
        'deal_type': deal.deal_type,
        'industry': deal.industry,
        'sub_industry': deal.sub_industry,
        'status': deal.status,
        'target_locked': deal.target_locked,
        'buyer_locked': deal.buyer_locked,
        'documents_uploaded': getattr(deal, 'documents_uploaded', 0),
        'facts_extracted': getattr(deal, 'facts_extracted', 0),
        'findings_count': getattr(deal, 'findings_count', 0),
        'review_percent': deal.review_percent,
        'created_at': deal.created_at.isoformat() if deal.created_at else None,
        'updated_at': deal.updated_at.isoformat() if deal.updated_at else None,
        'last_accessed_at': deal.last_accessed_at.isoformat() if deal.last_accessed_at else None,
    }
