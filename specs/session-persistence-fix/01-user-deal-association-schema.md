# 01 — User-Deal Association Schema

## Status: NOT STARTED
## Priority: CRITICAL (Foundation for all session persistence)
## Depends On: Nothing
## Enables: 02-deal-selection-api, 03-automatic-context-restoration

---

## Overview

The User model currently has no database-backed relationship to track which deal a user is currently working on. Deal selection is stored ONLY in `flask_session['current_deal_id']`, which is ephemeral (lost on session expiry, browser restart, server restart in some configurations).

**The fix:** Add `last_deal_id` and `last_deal_accessed_at` fields to the `User` model, allowing the application to remember and restore a user's deal context even after session loss.

This is the foundation for Specs 02 (explicit selection API) and 03 (automatic restoration). Without this schema, there's no durable source of truth.

---

## Architecture

```
BEFORE (current):
  User selects deal → flask_session['current_deal_id'] = deal_id
  Session expires → deal_id lost forever
  User must manually re-select deal

AFTER (with this schema):
  User selects deal → flask_session['current_deal_id'] = deal_id
                    → User.last_deal_id = deal_id (database)
                    → User.last_deal_accessed_at = now()
  Session expires → load from User.last_deal_id (Spec 03)
  User context restored automatically
```

**Data Flow:**
1. User action triggers deal selection (upload, analysis, manual select)
2. API endpoint (Spec 02) updates BOTH session and database
3. On subsequent requests, if session is empty:
   - Before-request hook (Spec 03) reads `User.last_deal_id`
   - Verifies deal exists and user has access
   - Restores `flask_session['current_deal_id']`

---

## Specification

### Change 1: Add columns to `users` table

**Migration SQL (PostgreSQL):**
```sql
-- Add last_deal_id column (nullable FK to deals)
ALTER TABLE users
ADD COLUMN last_deal_id VARCHAR(36);

-- Add last_deal_accessed_at timestamp
ALTER TABLE users
ADD COLUMN last_deal_accessed_at TIMESTAMP;

-- Add foreign key constraint
ALTER TABLE users
ADD CONSTRAINT fk_users_last_deal
FOREIGN KEY (last_deal_id)
REFERENCES deals(id)
ON DELETE SET NULL;

-- Add index for faster queries
CREATE INDEX idx_users_last_deal ON users(last_deal_id);
```

**Migration SQL (SQLite):**
```sql
-- SQLite doesn't support ADD CONSTRAINT in ALTER TABLE
-- Must handle FK in application code or recreate table

-- Add columns (SQLite allows this)
ALTER TABLE users ADD COLUMN last_deal_id VARCHAR(36);
ALTER TABLE users ADD COLUMN last_deal_accessed_at TIMESTAMP;

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_users_last_deal ON users(last_deal_id);
```

**Rollback SQL (both databases):**
```sql
DROP INDEX IF EXISTS idx_users_last_deal;
ALTER TABLE users DROP COLUMN last_deal_accessed_at;
ALTER TABLE users DROP COLUMN last_deal_id;
```

---

### Change 2: Update `User` model in `web/database.py`

**Location:** After line 390 in `web/database.py` (in the `User` class)

**Add these columns:**
```python
# Last accessed deal (for session restoration)
last_deal_id = Column(String(36), ForeignKey('deals.id', ondelete='SET NULL'), nullable=True, index=True)
last_deal_accessed_at = Column(DateTime, nullable=True)

# Relationship
last_deal = relationship('Deal', foreign_keys=[last_deal_id], lazy='select')
```

**Add these helper methods (after the `to_dict()` method, around line 420):**
```python
def update_last_deal(self, deal_id: str) -> None:
    """
    Update the user's last accessed deal.

    This is called when a user explicitly selects a deal or navigates to a deal page.
    Used for session restoration when flask_session is lost.

    Args:
        deal_id: The deal ID to set as last accessed

    Note:
        Does NOT commit the transaction. Caller must handle db.session.commit().
    """
    self.last_deal_id = deal_id
    self.last_deal_accessed_at = datetime.utcnow()

def get_last_deal(self) -> Optional['Deal']:
    """
    Get the user's last accessed deal, if it exists and is not deleted.

    Returns:
        Deal object if found and not soft-deleted, None otherwise

    Usage:
        last_deal = current_user.get_last_deal()
        if last_deal:
            flask_session['current_deal_id'] = last_deal.id
    """
    if not self.last_deal_id:
        return None

    # The relationship loads the deal, but we need to check if it's deleted
    deal = self.last_deal
    if deal and not deal.is_deleted:
        return deal

    return None

def clear_last_deal(self) -> None:
    """
    Clear the user's last accessed deal.

    Called when:
    - User explicitly logs out
    - User's access to a deal is revoked
    - Deal is deleted

    Note:
        Does NOT commit the transaction. Caller must handle db.session.commit().
    """
    self.last_deal_id = None
    self.last_deal_accessed_at = None
```

**Update the `to_dict()` method (line ~410) to include new fields:**
```python
def to_dict(self) -> Dict[str, Any]:
    return {
        'id': self.id,
        'tenant_id': self.tenant_id,
        'email': self.email,
        'name': self.name,
        'roles': self.roles,
        'active': self.active,
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'last_login': self.last_login.isoformat() if self.last_login else None,
        'last_deal_id': self.last_deal_id,  # NEW
        'last_deal_accessed_at': self.last_deal_accessed_at.isoformat() if self.last_deal_accessed_at else None,  # NEW
    }
```

---

### Change 3: Add migration helper to `web/database.py`

**Location:** In the `_run_migrations()` function (after line 1468 in `web/database.py`), add:

```python
# Migration 4: Add last_deal_id and last_deal_accessed_at to users (Session Persistence Fix - Spec 01)
_add_column_if_missing('users', 'last_deal_id', "VARCHAR(36)", logger)
_add_column_if_missing('users', 'last_deal_accessed_at', "TIMESTAMP", logger)

# Add index for last_deal_id lookups
try:
    dialect = db.engine.dialect.name
    if dialect == 'postgresql':
        db.session.execute(db.text(
            "CREATE INDEX IF NOT EXISTS idx_users_last_deal ON users(last_deal_id)"
        ))
        db.session.commit()
        logger.info("Index idx_users_last_deal ensured")
    elif dialect == 'sqlite':
        # SQLite CREATE INDEX IF NOT EXISTS is already supported
        db.session.execute(db.text(
            "CREATE INDEX IF NOT EXISTS idx_users_last_deal ON users(last_deal_id)"
        ))
        db.session.commit()
        logger.info("Index idx_users_last_deal ensured (SQLite)")
except Exception as e:
    logger.warning(f"idx_users_last_deal index creation failed (non-fatal): {e}")
    db.session.rollback()
```

---

### Change 4: Permissions & Access Control

**When setting `last_deal_id`, verify user has permission to access the deal.**

The `update_last_deal()` method does NOT enforce permissions — it's a low-level setter. **Permission checks belong in the API layer (Spec 02).**

**Permission logic (to be used in Spec 02):**

```python
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
    """
    # Rule 1: Owner
    if deal.owner_id == user.id:
        return True

    # Rule 2: Same tenant (if multi-tenancy enabled)
    USE_MULTI_TENANCY = os.environ.get('USE_MULTI_TENANCY', 'false').lower() == 'true'
    if USE_MULTI_TENANCY and user.tenant_id and user.tenant_id == deal.tenant_id:
        return True

    # Rule 3: Explicit share (future enhancement)
    # if DealShare.query.filter_by(deal_id=deal.id, user_id=user.id).first():
    #     return True

    # Default: no access
    return False
```

**This helper should go in a new file:** `web/permissions.py` (create if doesn't exist) or inline in the API route (Spec 02).

---

### Change 5: Handle Deleted Deals

**Scenario:** User's `last_deal_id` points to a soft-deleted deal.

**Solution:** The `get_last_deal()` method (above) already checks `deal.is_deleted` and returns `None` if the deal is deleted.

**Additional cleanup:** Optionally, add a database cleanup job to set `last_deal_id = NULL` for all users whose `last_deal_id` points to deleted deals:

```python
def cleanup_deleted_deal_references():
    """
    Database maintenance: Clear last_deal_id for users whose deal is deleted.

    Run this periodically (e.g., nightly cron) or after deal deletion.
    """
    from sqlalchemy import and_

    # Find users with last_deal_id pointing to deleted deals
    users_to_update = db.session.query(User).join(
        Deal, User.last_deal_id == Deal.id
    ).filter(
        and_(
            User.last_deal_id.isnot(None),
            Deal.deleted_at.isnot(None)
        )
    ).all()

    for user in users_to_update:
        user.clear_last_deal()

    db.session.commit()
    logger.info(f"Cleared last_deal_id for {len(users_to_update)} users with deleted deals")
```

This is **optional** and not required for Spec 01. Can be deferred to operations/maintenance.

---

## Benefits

1. **Session-independent persistence** — Deal selection survives browser restarts, session expiry, server restarts
2. **User-centric UX** — Users return to their last-used deal automatically (Spec 03)
3. **Minimal schema impact** — Only 2 columns added to existing `users` table
4. **Backward compatible** — Nullable columns; existing users have `last_deal_id = NULL` until they select a deal
5. **Multi-server safe** — Database is the source of truth, not in-memory session state

---

## Expectations

After this spec is implemented:

1. The `users` table has `last_deal_id` and `last_deal_accessed_at` columns
2. The `User` model has `update_last_deal()`, `get_last_deal()`, and `clear_last_deal()` methods
3. The migration runs successfully on both PostgreSQL and SQLite
4. Existing users have `last_deal_id = NULL` (no migration data needed)
5. The schema is ready to be used by Spec 02 (API) and Spec 03 (restoration hook)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Migration fails on PostgreSQL in production | Low | High | Test migration on staging first. Include rollback SQL. Wrap in transaction. |
| SQLite FK constraint not enforced | Medium | Low | SQLite doesn't enforce FK by default unless `PRAGMA foreign_keys = ON`. Application code handles deletion via `get_last_deal()` checking `is_deleted`. |
| User's last_deal_id points to deal they no longer have access to | Medium | Medium | `get_last_deal()` doesn't check permissions — that's intentional. Spec 03's restoration hook MUST verify access before restoring session. |
| Index adds overhead to user table operations | Low | Low | `idx_users_last_deal` is on a nullable column with low write frequency (only on deal selection, not every request). Query benefit outweighs insert cost. |
| Existing tests break due to new User fields | Low | Low | New fields are nullable. Existing User factories/fixtures continue to work. Tests that serialize User to dict will see new fields but should not break. |

---

## Results Criteria

### Automated Tests

**Test 1: Migration runs successfully**
```python
def test_migration_adds_last_deal_columns():
    """Verify migration adds last_deal_id and last_deal_accessed_at to users table."""
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('users')]

    assert 'last_deal_id' in columns
    assert 'last_deal_accessed_at' in columns
```

**Test 2: User.update_last_deal() sets fields**
```python
def test_user_update_last_deal():
    """Verify update_last_deal() sets both fields."""
    user = User(email='test@example.com', password_hash='...')
    deal = Deal(id='deal-123', target_name='Test Corp')
    db.session.add_all([user, deal])
    db.session.commit()

    user.update_last_deal('deal-123')
    db.session.commit()

    assert user.last_deal_id == 'deal-123'
    assert user.last_deal_accessed_at is not None
    assert (datetime.utcnow() - user.last_deal_accessed_at).seconds < 5
```

**Test 3: User.get_last_deal() returns deal if not deleted**
```python
def test_get_last_deal_returns_deal():
    """Verify get_last_deal() returns deal if it exists and is not deleted."""
    user = User(email='test@example.com', password_hash='...')
    deal = Deal(id='deal-123', target_name='Test Corp')
    db.session.add_all([user, deal])
    db.session.commit()

    user.update_last_deal('deal-123')
    db.session.commit()

    retrieved_deal = user.get_last_deal()
    assert retrieved_deal is not None
    assert retrieved_deal.id == 'deal-123'
```

**Test 4: User.get_last_deal() returns None for deleted deal**
```python
def test_get_last_deal_returns_none_for_deleted():
    """Verify get_last_deal() returns None if deal is soft-deleted."""
    user = User(email='test@example.com', password_hash='...')
    deal = Deal(id='deal-123', target_name='Test Corp')
    db.session.add_all([user, deal])
    db.session.commit()

    user.update_last_deal('deal-123')
    deal.soft_delete()
    db.session.commit()

    retrieved_deal = user.get_last_deal()
    assert retrieved_deal is None
```

**Test 5: User.clear_last_deal() clears fields**
```python
def test_user_clear_last_deal():
    """Verify clear_last_deal() sets fields to None."""
    user = User(email='test@example.com', password_hash='...')
    user.update_last_deal('deal-123')
    db.session.commit()

    user.clear_last_deal()
    db.session.commit()

    assert user.last_deal_id is None
    assert user.last_deal_accessed_at is None
```

### Manual Verification

1. Run migration on local SQLite database: `flask db upgrade`
2. Inspect `users` table: `sqlite3 data/diligence.db` → `.schema users` → verify columns exist
3. Test on Railway staging with PostgreSQL: Deploy, verify no migration errors in logs
4. Check index exists: `SELECT * FROM pg_indexes WHERE tablename = 'users' AND indexname = 'idx_users_last_deal';` (PostgreSQL)
5. Create a user, set last_deal_id via `user.update_last_deal('some-deal-id')`, verify it persists across server restart

---

## Files Modified

| File | Change |
|------|--------|
| `web/database.py` | Add `last_deal_id`, `last_deal_accessed_at` columns to User model (lines ~390). Add `update_last_deal()`, `get_last_deal()`, `clear_last_deal()` methods (lines ~420). Add migration logic to `_run_migrations()` (lines ~1468). Update `to_dict()` (line ~410). |

**Lines of code:** ~60 lines added (model changes + migration + helpers)

---

## Dependencies

**External:**
- Requires SQLAlchemy (already present)
- Requires database with either PostgreSQL or SQLite (already configured)

**Internal:**
- Depends on existing `User` and `Deal` models (lines 378-435, 441-528 in `web/database.py`)
- Depends on existing migration system (`_run_migrations()` at line 1417 in `web/database.py`)

**Enables:**
- Spec 02 (API endpoint can call `user.update_last_deal()`)
- Spec 03 (Before-request hook can call `user.get_last_deal()`)
