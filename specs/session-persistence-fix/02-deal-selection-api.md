# 02 — Deal Selection API Endpoint

## Status: NOT STARTED
## Priority: HIGH (Enables explicit deal selection with dual persistence)
## Depends On: 01-user-deal-association-schema
## Enables: 03-automatic-context-restoration, improved UX

---

## Overview

Currently, there is no centralized "select deal" endpoint. Deal selection happens implicitly during document upload or analysis initiation, and the selection is stored ONLY in `flask_session['current_deal_id']`. There's no explicit user action to "switch to Deal X."

**The problem:**
- No way for users to explicitly switch between deals
- Deal selection not persisted to database (Audit Finding 5)
- No audit trail of deal switches
- Frontend has no clear API to call

**The fix:** Create `POST /api/deals/<deal_id>/select` endpoint that:
1. Validates user has permission to access the deal
2. Updates `flask_session['current_deal_id']` (session persistence)
3. Updates `User.last_deal_id` in database (Spec 01 schema)
4. Updates `Deal.last_accessed_at` timestamp
5. Creates audit log entry
6. Returns confirmation with deal details

---

## Architecture

```
CURRENT (implicit selection):
  User uploads document → deal_id passed in form
  → flask_session['current_deal_id'] = deal_id
  → No database update, no audit log

AFTER (explicit selection):
  User clicks deal in selector OR API called programmatically
  → POST /api/deals/<deal_id>/select
  → Permission check (user_can_access_deal)
  → flask_session['current_deal_id'] = deal_id
  → User.last_deal_id = deal_id (database)
  → Deal.last_accessed_at = now()
  → AuditLog entry created
  → Response: {success: true, deal: {...}}
```

**Integration Points:**
- **Spec 01 schema:** Uses `user.update_last_deal()` method
- **Spec 03 restoration:** This endpoint ensures DB is always up-to-date, so restoration has fresh data
- **Frontend:** Deal selector dropdown (to be discovered/built) calls this endpoint

---

## Specification

### API Endpoint Specification

**Route:** `POST /api/deals/<deal_id>/select`

**Authentication:** Required (`@login_required` decorator)

**URL Parameters:**
- `deal_id` (string, required): UUID of the deal to select

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "success": true,
  "deal": {
    "id": "abc-123",
    "name": "Acme Corp Acquisition",
    "target_name": "Acme Corp",
    "status": "active",
    "documents_uploaded": 12,
    "facts_extracted": 156,
    "last_accessed_at": "2026-02-09T15:30:00Z"
  },
  "message": "Switched to deal: Acme Corp Acquisition"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "success": false,
  "error": "deal_not_found",
  "message": "Deal not found or has been deleted"
}
```

**403 Forbidden:**
```json
{
  "success": false,
  "error": "access_denied",
  "message": "You do not have permission to access this deal"
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "error": "authentication_required",
  "message": "Please log in to select a deal"
}
```

---

### Implementation: Route Handler

**Location:** `web/app.py` after existing `/api/deal/<deal_id>/...` routes (around line 3900)

**Code:**

```python
@app.route('/api/deals/<deal_id>/select', methods=['POST'])
@login_required
def select_deal(deal_id):
    """
    Select a deal as the active deal for the current user.

    Sets both flask_session['current_deal_id'] and User.last_deal_id in database.
    This ensures the deal selection persists across session loss.

    Args:
        deal_id: UUID of the deal to select

    Returns:
        JSON response with deal details or error message

    Status Codes:
        200: Deal selected successfully
        403: User does not have access to this deal
        404: Deal not found or deleted
    """
    from web.database import Deal, db
    from web.permissions import user_can_access_deal
    from flask_login import current_user
    from flask import session as flask_session

    # Fetch deal
    deal = Deal.query.get(deal_id)

    # Check existence (including soft-deleted deals)
    if not deal:
        return jsonify({
            'success': False,
            'error': 'deal_not_found',
            'message': 'Deal not found'
        }), 404

    # Check if deal is deleted
    if deal.is_deleted:
        return jsonify({
            'success': False,
            'error': 'deal_not_found',
            'message': 'Deal not found or has been deleted'
        }), 404

    # Check permissions
    if not user_can_access_deal(current_user, deal):
        logger.warning(
            f"User {current_user.id} ({current_user.email}) attempted to access "
            f"deal {deal_id} ({deal.name}) without permission"
        )
        return jsonify({
            'success': False,
            'error': 'access_denied',
            'message': 'You do not have permission to access this deal'
        }), 403

    # Update session
    flask_session['current_deal_id'] = deal_id
    flask_session.modified = True  # Force session save

    # Update user's last accessed deal (Spec 01 schema)
    current_user.update_last_deal(deal_id)

    # Update deal's last accessed timestamp
    deal.update_access_time()

    # Commit database changes
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update last_deal for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': 'database_error',
            'message': 'Failed to save deal selection'
        }), 500

    # Create audit log entry
    from web.database import log_audit
    log_audit(
        action='select_deal',
        resource_type='deal',
        resource_id=deal_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        deal_id=deal_id,
        details={'deal_name': deal.name, 'target_name': deal.target_name},
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )

    logger.info(
        f"User {current_user.id} ({current_user.email}) selected deal {deal_id} ({deal.name})"
    )

    # Return success response with deal details
    return jsonify({
        'success': True,
        'deal': {
            'id': deal.id,
            'name': deal.name or deal.target_name,
            'target_name': deal.target_name,
            'buyer_name': deal.buyer_name,
            'status': deal.status,
            'documents_uploaded': deal.documents_uploaded,
            'facts_extracted': deal.facts_extracted,
            'findings_count': deal.findings_count,
            'last_accessed_at': deal.last_accessed_at.isoformat() if deal.last_accessed_at else None,
        },
        'message': f"Switched to deal: {deal.name or deal.target_name}"
    }), 200
```

---

### Implementation: Permission Helper

**Location:** New file `web/permissions.py` (create if doesn't exist)

**Code:**

```python
"""
Permission Helpers for Access Control

Centralized permission checking logic for deals, documents, and other resources.
"""

import os
from typing import Optional
from web.database import User, Deal


def user_can_access_deal(user: User, deal: Deal) -> bool:
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

    Usage:
        if user_can_access_deal(current_user, deal):
            # Allow access
        else:
            abort(403)
    """
    if not user or not deal:
        return False

    # Rule 1: Owner can always access
    if deal.owner_id == user.id:
        return True

    # Rule 2: Same tenant (if multi-tenancy enabled)
    USE_MULTI_TENANCY = os.environ.get('USE_MULTI_TENANCY', 'false').lower() == 'true'
    if USE_MULTI_TENANCY:
        if user.tenant_id and user.tenant_id == deal.tenant_id:
            return True

    # Rule 3: Explicit share (future enhancement)
    # TODO: When DealShare table is added, check:
    # if DealShare.query.filter_by(deal_id=deal.id, user_id=user.id).first():
    #     return True

    # Default: no access
    return False


def user_can_edit_deal(user: User, deal: Deal) -> bool:
    """
    Check if a user has permission to edit a deal (stricter than view).

    Edit permission rules:
    1. User owns the deal
    2. User is admin in the same tenant (multi-tenancy + admin role)

    Args:
        user: The User object
        deal: The Deal object

    Returns:
        True if user can edit, False otherwise
    """
    if not user or not deal:
        return False

    # Rule 1: Owner can edit
    if deal.owner_id == user.id:
        return True

    # Rule 2: Admin in same tenant
    USE_MULTI_TENANCY = os.environ.get('USE_MULTI_TENANCY', 'false').lower() == 'true'
    if USE_MULTI_TENANCY:
        if user.tenant_id == deal.tenant_id and user.is_admin():
            return True

    return False
```

---

### Frontend Discovery & Integration

**UNKNOWN:** The audit couldn't locate the actual deal selector UI component. The base template has CSS for `.deal-selector` (lines 61-150 in `web/templates/base.html`) but no corresponding JavaScript or HTML structure was found.

**Discovery Task:** Search for existing deal selector implementation:

1. **Check base template** (`web/templates/base.html`) lines 800-1200 for HTML structure
2. **Check static JS files** for deal selection logic: `web/static/js/` (if exists)
3. **Check if deal selector is rendered server-side** via Jinja in base template

**If deal selector DOES NOT exist:**

**Add minimal deal selector to `web/templates/base.html`:**

**Location:** In the header navigation, after user menu (around line 250)

```html
<!-- Deal Selector -->
{% if current_user.is_authenticated %}
<div class="deal-selector" id="dealSelector">
    <button class="deal-selector-trigger" id="dealSelectorTrigger" aria-expanded="false">
        <div class="deal-selector-icon">📁</div>
        <div class="deal-selector-content">
            <div class="deal-selector-label">Current Deal</div>
            <div class="deal-selector-name" id="currentDealName">
                {% if session.get('current_deal_id') %}
                    {{ current_deal_name|default('Deal', true) }}
                {% else %}
                    No deal selected
                {% endif %}
            </div>
        </div>
        <svg class="deal-selector-chevron" width="16" height="16" fill="currentColor">
            <path d="M4 6l4 4 4-4"/>
        </svg>
    </button>

    <div class="deal-selector-dropdown" id="dealSelectorDropdown">
        <div class="deal-selector-search">
            <input type="text" placeholder="Search deals..." id="dealSearchInput">
        </div>
        <div class="deal-selector-list" id="dealList">
            <!-- Populated via JavaScript -->
            <div class="deal-selector-loading">Loading deals...</div>
        </div>
        <div class="deal-selector-footer">
            <a href="/deals/new" class="deal-selector-new-deal">+ New Deal</a>
        </div>
    </div>
</div>
{% endif %}
```

**Add JavaScript handler:**

**Location:** Inline `<script>` block at bottom of `base.html` OR new file `web/static/js/deal-selector.js`

```javascript
(function() {
    const selector = document.getElementById('dealSelector');
    const trigger = document.getElementById('dealSelectorTrigger');
    const dropdown = document.getElementById('dealSelectorDropdown');
    const dealList = document.getElementById('dealList');
    const currentDealName = document.getElementById('currentDealName');

    if (!selector || !trigger || !dropdown) return;

    // Toggle dropdown
    trigger.addEventListener('click', function() {
        const isOpen = selector.classList.toggle('open');
        trigger.setAttribute('aria-expanded', isOpen);

        if (isOpen) {
            loadDeals();
        }
    });

    // Close on outside click
    document.addEventListener('click', function(e) {
        if (!selector.contains(e.target)) {
            selector.classList.remove('open');
            trigger.setAttribute('aria-expanded', 'false');
        }
    });

    // Load deals list
    function loadDeals() {
        fetch('/api/deals/list')
            .then(res => res.json())
            .then(data => {
                if (data.deals && data.deals.length > 0) {
                    renderDeals(data.deals);
                } else {
                    dealList.innerHTML = '<div class="deal-selector-empty">No deals found</div>';
                }
            })
            .catch(err => {
                console.error('Failed to load deals:', err);
                dealList.innerHTML = '<div class="deal-selector-error">Failed to load deals</div>';
            });
    }

    // Render deals list
    function renderDeals(deals) {
        const currentDealId = document.body.dataset.currentDealId; // Set via server

        dealList.innerHTML = deals.map(deal => {
            const isActive = deal.id === currentDealId;
            return `
                <button class="deal-selector-item ${isActive ? 'active' : ''}"
                        data-deal-id="${deal.id}"
                        onclick="selectDeal('${deal.id}')">
                    <div class="deal-item-name">${deal.name}</div>
                    <div class="deal-item-target">${deal.target_name}</div>
                    ${isActive ? '<span class="deal-item-badge">Active</span>' : ''}
                </button>
            `;
        }).join('');
    }

    // Select deal (global function for onclick)
    window.selectDeal = function(dealId) {
        fetch(`/api/deals/${dealId}/select`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Update UI
                currentDealName.textContent = data.deal.name;
                document.body.dataset.currentDealId = data.deal.id;

                // Close dropdown
                selector.classList.remove('open');
                trigger.setAttribute('aria-expanded', 'false');

                // Reload page to reflect new deal context
                window.location.reload();
            } else {
                alert(data.message || 'Failed to select deal');
            }
        })
        .catch(err => {
            console.error('Failed to select deal:', err);
            alert('Failed to select deal. Please try again.');
        });
    };
})();
```

**Note:** This assumes a `/api/deals/list` endpoint exists to fetch user's deals. If it doesn't exist, add it:

```python
@app.route('/api/deals/list')
@login_required
def list_user_deals():
    """Get list of deals the current user can access."""
    from web.database import Deal
    from web.permissions import user_can_access_deal
    from flask_login import current_user

    # Query deals (apply tenant filter if multi-tenancy enabled)
    USE_MULTI_TENANCY = os.environ.get('USE_MULTI_TENANCY', 'false').lower() == 'true'

    if USE_MULTI_TENANCY and current_user.tenant_id:
        deals = Deal.query.filter_by(
            tenant_id=current_user.tenant_id,
            deleted_at=None
        ).order_by(Deal.last_accessed_at.desc()).limit(50).all()
    else:
        # No multi-tenancy: show user's own deals
        deals = Deal.query.filter_by(
            owner_id=current_user.id,
            deleted_at=None
        ).order_by(Deal.last_accessed_at.desc()).limit(50).all()

    # Filter by permissions (double-check)
    accessible_deals = [
        deal for deal in deals
        if user_can_access_deal(current_user, deal)
    ]

    return jsonify({
        'success': True,
        'deals': [
            {
                'id': deal.id,
                'name': deal.name or deal.target_name,
                'target_name': deal.target_name,
                'status': deal.status,
                'last_accessed_at': deal.last_accessed_at.isoformat() if deal.last_accessed_at else None
            }
            for deal in accessible_deals
        ]
    })
```

---

## Benefits

1. **Centralized deal selection logic** — All deal switches go through one endpoint
2. **Dual persistence** — Both session and database updated atomically
3. **Audit trail** — Every deal switch is logged via `AuditLog`
4. **Permission-enforced** — Can't select deals you don't have access to
5. **Frontend integration point** — Clear API for deal selector UI
6. **Enables automatic restoration** — Database always has latest selection (Spec 03 depends on this)

---

## Expectations

After this spec is implemented:

1. `POST /api/deals/<deal_id>/select` endpoint exists and is accessible
2. Selecting a deal updates BOTH `flask_session['current_deal_id']` and `User.last_deal_id`
3. Permission checks prevent unauthorized deal access
4. Audit log contains `select_deal` entries
5. Frontend deal selector (if exists) calls this endpoint
6. If deal selector doesn't exist, minimal implementation is added to base template

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Deal selector UI doesn't exist in codebase | High | Medium | Spec includes minimal implementation. Can enhance later. |
| Permissions.py file conflicts with existing auth | Low | Low | Check if `web/permissions.py` exists before creating. If exists, append functions. |
| Session not saving after update | Low | High | Explicitly set `flask_session.modified = True` after updating session dict. |
| Database commit fails silently | Low | High | Wrap commit in try/except, rollback on error, return 500 status code. |
| User rapidly switches deals causing race condition | Low | Low | Last write wins. Both session and DB updated in same request. Acceptable UX. |
| `/api/deals/list` endpoint missing | Medium | Medium | Spec includes implementation. Reuses existing permission logic. |

---

## Results Criteria

### Automated Tests

**Test 1: Successful deal selection**
```python
def test_select_deal_success(client, auth_user, test_deal):
    """Verify successful deal selection updates session and database."""
    login_as(client, auth_user)

    response = client.post(f'/api/deals/{test_deal.id}/select')
    assert response.status_code == 200

    data = response.get_json()
    assert data['success'] is True
    assert data['deal']['id'] == test_deal.id

    # Verify session updated
    with client.session_transaction() as sess:
        assert sess['current_deal_id'] == test_deal.id

    # Verify database updated
    db.session.refresh(auth_user)
    assert auth_user.last_deal_id == test_deal.id
    assert auth_user.last_deal_accessed_at is not None
```

**Test 2: Reject deal selection without permission**
```python
def test_select_deal_forbidden(client, auth_user, other_user_deal):
    """Verify users cannot select deals they don't own."""
    login_as(client, auth_user)

    response = client.post(f'/api/deals/{other_user_deal.id}/select')
    assert response.status_code == 403

    data = response.get_json()
    assert data['success'] is False
    assert data['error'] == 'access_denied'
```

**Test 3: Reject deleted deal**
```python
def test_select_deleted_deal(client, auth_user, deleted_deal):
    """Verify deleted deals cannot be selected."""
    login_as(client, auth_user)

    response = client.post(f'/api/deals/{deleted_deal.id}/select')
    assert response.status_code == 404

    data = response.get_json()
    assert data['success'] is False
    assert data['error'] == 'deal_not_found'
```

**Test 4: Audit log entry created**
```python
def test_select_deal_creates_audit_log(client, auth_user, test_deal):
    """Verify audit log entry is created on deal selection."""
    login_as(client, auth_user)

    before_count = AuditLog.query.count()

    client.post(f'/api/deals/{test_deal.id}/select')

    after_count = AuditLog.query.count()
    assert after_count == before_count + 1

    audit_entry = AuditLog.query.order_by(AuditLog.created_at.desc()).first()
    assert audit_entry.action == 'select_deal'
    assert audit_entry.resource_id == test_deal.id
    assert audit_entry.user_id == auth_user.id
```

### Manual Verification

1. Log in to web UI
2. Navigate to base page (dashboard or upload)
3. Verify deal selector appears in header (if implemented)
4. Click deal selector, verify list of deals loads
5. Click a deal, verify:
   - Current deal name updates
   - Page reloads or data refreshes
   - `flask_session['current_deal_id']` is set (check via browser dev tools → Application → Cookies/Session)
6. Log out and log back in
7. Verify last-selected deal is automatically restored (Spec 03 enables this)

---

## Files Modified

| File | Change |
|------|--------|
| `web/app.py` | Add route `POST /api/deals/<deal_id>/select` (lines ~3900). Add route `GET /api/deals/list` (if doesn't exist). |
| `web/permissions.py` | NEW FILE. Add `user_can_access_deal()` and `user_can_edit_deal()` functions. |
| `web/templates/base.html` | Add deal selector HTML structure (lines ~250). Add JavaScript handler (inline or external). |
| `web/static/js/deal-selector.js` | NEW FILE (optional). Extract JavaScript to separate file. |

**Lines of code:** ~150 lines added (route handler + permissions + frontend)

---

## Dependencies

**Depends on:**
- Spec 01 (User.update_last_deal() method, User.last_deal_id column)
- Existing `User`, `Deal`, `AuditLog` models
- Existing authentication system (`@login_required`, `current_user`)

**Enables:**
- Spec 03 (automatic restoration depends on this endpoint keeping DB up-to-date)
- Improved UX (users can explicitly switch deals)
