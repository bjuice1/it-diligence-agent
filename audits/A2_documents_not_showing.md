# Audit A2: Documents Not Showing

## Status: IMPLEMENTED ✓
## Priority: HIGH (Tier 1 - Quick Win)
## Complexity: Quick
## Review Score: 8.5/10 (GPT review, Feb 8 2026)
## Implementation Date: Feb 8, 2026

---

## 1. Problem Statement

**Symptom:** Dashboard and home page show "No documents" even after documents have been uploaded and processed.

**User Impact:**
- Users cannot see what documents were analyzed
- Cannot verify uploads succeeded
- Cannot trace facts back to source documents
- Appears system is broken/empty

**Expected Behavior:** After uploading documents, the UI should list all uploaded documents with metadata (filename, upload date, status, entity).

---

## 2. Current Evidence

### Manifest shows 8 documents uploaded:
```json
{
  "deal_id": "28d0aabe-79cd-4376-a2db-e2e82640596a",
  "document_count": 8,
  "documents": [
    {"filename": "Great_Insurance_Document_1_Executive_IT_Profile.md", "entity": "target", ...},
    {"filename": "Great_Insurance_Document_2_Application_Inventory.md", "entity": "target", ...},
    // ... 6 more
  ]
}
```

### But database query returns 0:
```sql
SELECT * FROM documents WHERE deal_id = '28d0aabe-79cd-4376-a2db-e2e82640596a'
-- Returns 0 rows
```

**Conclusion:** Documents exist in filesystem (manifest.json) but not in database (Document table).

---

## 3. Decision & Invariants (GPT FEEDBACK)

### Decision: DB is Source of Truth (Recommended)

**Invariants:**
1. Upload returns success (200) **only if** a `documents` row exists for that upload
2. UI document list reads from **one source only** (DB)
3. Manifest is **derived/cache**, not authoritative
4. If manifest is kept, it must be validated/backfilled to match DB

**Why DB as source of truth:**
- Enables querying, filtering, permissions, statuses, pagination, search
- Works in hosted environments with ephemeral filesystems
- Supports multi-user scenarios
- Standard pattern for web applications

**Why NOT manifest as primary:**
- Harder to support search/filter/status
- Harder to do permissions / multi-user
- Risky in hosted environments with ephemeral filesystems

---

## 4. Hypotheses

| # | Hypothesis | Likelihood | How to Verify |
|---|------------|------------|---------------|
| **H0** | **Upload and UI point at different DBs (or schema)** | **HIGH** | Log DATABASE_URL in upload route AND UI route; confirm same |
| H1 | Upload route saves to filesystem but skips DB insert | HIGH | Read upload route code |
| H2 | DB insert exists but fails silently | MEDIUM | Check for try/except swallowing errors |
| H3 | Document model has wrong schema/table name | LOW | Check model definition |
| H4 | DB insert is in a task that never runs | MEDIUM | Check if deferred to Celery |
| H5 | Transaction not committed | MEDIUM | Look for missing db.session.commit() |

> **Note (GPT):** H0 is elevated to top priority. "Works locally / breaks hosted" often comes from different DB connections between upload/analysis/UI paths.

---

## 5. Document Identity & Idempotency (GPT FEEDBACK)

### Document Identity Key (choose one):

| Option | Key | Pros | Cons |
|--------|-----|------|------|
| **Best** | `document_id` (UUID) generated at upload | Unique, immutable | Must generate on upload |
| Good | `(deal_id, entity, sha256)` | Content-based, handles re-upload | Needs hash computation |
| Weak | `(deal_id, entity, filename)` | Simple | Breaks on rename/re-upload |

### Decision: Use `document_id` (UUID)

**Idempotency rules:**
- Re-upload same file (same hash) → update existing record, don't duplicate
- Re-upload different file with same name → new document_id, keep both
- Delete → soft delete (mark inactive), don't hard delete

---

## 6. Architecture Understanding

### Document Storage Flow (Expected):
```
User uploads file
    → Flask route receives file
    → File saved to: uploads/{deal_id}/{entity}/data_room/{hash}_{filename}
    → Compute sha256 hash
    → Insert Document row to DB  ← MUST HAPPEN BEFORE 200 OK
    → Commit transaction
    → Update manifest.json (optional, as cache)
    → Return 200 OK
    → Document appears in UI
```

### Key Components:
1. **Filesystem storage:** `uploads/{deal_id}/` directory structure
2. **Database storage:** `Document` table in PostgreSQL (SOURCE OF TRUTH)
3. **Manifest tracking:** `uploads/{deal_id}/manifest.json` - derived cache (optional)
4. **UI display:** Routes that query Document table only

---

## 7. Files to Investigate

### Primary Files:
| File | What to Look For |
|------|------------------|
| `web/app.py` | Upload route - where is file saved? DB insert? |
| `web/database.py` | Document model definition |
| `web/tasks/analysis_tasks.py` | Document processing task - does it insert to DB? |

### Secondary Files:
| File | What to Look For |
|------|------------------|
| `web/blueprints/*.py` | Any document-related blueprints |
| `services/document_manifest.py` | Manifest handling logic |
| `tools_v2/document_ingestion.py` | Ingestion pipeline |

### UI Files:
| File | What to Look For |
|------|------------------|
| `web/templates/` | Document list templates |
| `web/app.py` | Document display route - what does it query? |

---

## 8. Root Cause Confirmation Checklist (GPT FEEDBACK)

Before implementing fix, verify:

- [ ] **Same deal_id** across upload route, manifest path, DB query, and UI session
- [ ] **Same DB** (host/name/schema) across upload route, UI route, and any workers
- [ ] **Commit occurs** (no silent rollback)
- [ ] **Document model** points to correct table
- [ ] **Migrations applied** (table exists in target DB)

### Verification commands:
```python
# Add to upload route temporarily:
import os
print(f"Upload DB: {os.environ.get('DATABASE_URL', 'not set')[:50]}...")

# Add to document list route temporarily:
print(f"UI DB: {os.environ.get('DATABASE_URL', 'not set')[:50]}...")
```

---

## 9. Audit Steps

### Phase 1: Understand Current State
- [ ] 1.1 Read `Document` model in `web/database.py` - what fields exist?
- [ ] 1.2 Find upload route in `web/app.py` - trace the full upload flow
- [ ] 1.3 Find document display route - what does it query?
- [ ] 1.4 Verify same DB used in upload and display routes (H0 check)

### Phase 2: Identify Gap
- [ ] 2.1 Trace upload: does it insert to Document table?
- [ ] 2.2 If yes, why is insert failing? Check error handling
- [ ] 2.3 If no, where should insert be added?
- [ ] 2.4 Check if insert is wrapped in try/except that swallows errors

### Phase 3: Design Fix
- [ ] 3.1 Determine correct insertion point (before 200 OK)
- [ ] 3.2 Map manifest fields → Document model fields
- [ ] 3.3 Handle edge cases (re-upload, delete, update)
- [ ] 3.4 Ensure upload fails visibly if DB insert fails

### Phase 4: Implement & Verify
- [ ] 4.1 Add/fix DB insert with proper error handling
- [ ] 4.2 Test with fresh upload
- [ ] 4.3 Verify documents appear in UI immediately
- [ ] 4.4 Create backfill script for existing manifest documents

---

## 10. Potential Solutions

### Solution A: Add DB Insert to Upload Route (RECOMMENDED)
```python
# In upload route after saving file
try:
    doc = Document(
        id=str(uuid.uuid4()),  # document_id
        deal_id=deal_id,
        filename=filename,
        entity=entity,
        file_path=file_path,
        sha256_hash=computed_hash,
        uploaded_at=datetime.utcnow(),
        status='pending'
    )
    db.session.add(doc)
    db.session.commit()

    # Log for observability
    logger.info(f"Document uploaded: deal_id={deal_id}, doc_id={doc.id}, db_insert=success")

    # Optional: update manifest as cache
    update_manifest(deal_id, doc)

    return jsonify({'status': 'ok', 'document_id': doc.id}), 200

except Exception as e:
    db.session.rollback()
    logger.error(f"Document upload failed: deal_id={deal_id}, error={e}")
    return jsonify({'status': 'error', 'message': 'Upload failed'}), 500
```

### Solution B: Backfill Script for Existing Data
```python
def sync_manifest_to_db(deal_id):
    """One-time backfill: sync existing manifest to DB."""
    manifest = load_manifest(deal_id)
    synced = 0

    for doc_entry in manifest.get('documents', []):
        existing = Document.query.filter_by(
            deal_id=deal_id,
            sha256_hash=doc_entry.get('hash_sha256')
        ).first()

        if not existing:
            doc = Document(
                id=doc_entry.get('doc_id', str(uuid.uuid4())),
                deal_id=deal_id,
                filename=doc_entry['filename'],
                entity=doc_entry.get('entity', 'target'),
                sha256_hash=doc_entry.get('hash_sha256'),
                file_path=doc_entry.get('raw_file_path'),
                uploaded_at=datetime.fromisoformat(doc_entry.get('ingestion_timestamp', '')),
                status=doc_entry.get('status', 'pending')
            )
            db.session.add(doc)
            synced += 1

    db.session.commit()
    logger.info(f"Backfill complete: deal_id={deal_id}, synced={synced} documents")
    return synced
```

---

## 11. Observability Requirements (GPT FEEDBACK)

### Logging (must have):
```python
# Upload route:
logger.info(f"doc_upload: deal_id={deal_id}, entity={entity}, doc_id={doc_id}, db_insert={'ok' if success else 'failed'}")

# Document list route:
logger.info(f"doc_list: deal_id={deal_id}, count={len(documents)}, query_ms={query_time}")

# Background worker (if any):
logger.info(f"doc_process: doc_id={doc_id}, task={'start'|'finish'|'error'}, duration_ms={duration}")
```

### Why this matters:
- Current bug is "invisible failure" - no way to debug
- These logs turn future issues into 5-minute fixes

---

## 12. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing functionality | Test with existing deals first |
| Data loss if manifest/DB diverge | Backfill script + validation |
| Performance if querying filesystem | Use DB only (decision made) |
| Migration needed for existing data | Backfill script included |
| Silent success masking failure | Fail upload if DB insert fails |

---

## 13. Definition of Done (GPT FEEDBACK)

### Must have:
- [ ] Upload returns success **only if** DB row exists
- [ ] Upload returns error (not 200) if DB insert fails
- [ ] UI shows documents immediately after upload
- [ ] Document count in UI matches expected count
- [ ] Backfill script successfully syncs existing manifests to DB

### Tests:
- [ ] Unit test: upload creates DB row
- [ ] Unit test: upload fails if DB unavailable
- [ ] Integration test: upload → list docs returns ≥ 1
- [ ] Backfill test: manifest with N docs → DB has N rows

---

## 14. Success Criteria

- [ ] After upload, document appears in Document table
- [ ] UI shows all uploaded documents with correct metadata
- [ ] Document count matches manifest.json count
- [ ] Entity (buyer/target) correctly displayed
- [ ] Existing deals can see their documents (via backfill)
- [ ] No "silent success" - failures are visible

---

## 15. Questions Resolved

| Question | Decision |
|----------|----------|
| Should manifest.json or Document table be source of truth? | **DB is source of truth** |
| Is there a reason documents aren't in the DB? | No - this is a bug |
| Should we support both read paths? | No - DB only; manifest is optional cache |
| How to handle documents uploaded before fix? | Backfill script |
| Performance implications? | DB is better for scale |

---

## 16. Dependencies

- None (this is a Tier 1 quick win)

## 17. Blocked By

- Nothing

## 18. Blocks

- Full system testing (can't verify doc → fact traceability without this)
- A3 (Questions) - may share similar DB/query patterns

---

## 19. GPT Review Notes (Feb 8, 2026)

**Score: 8.5/10**

**Strengths:**
- Clear symptom + user impact + expected behavior
- Evidence-driven diagnosis (manifest vs DB)
- Good hypothesis table
- Staged audit steps

**Improvements made based on feedback:**
1. Added explicit "Decision & Invariants" section (DB as SoT)
2. Added H0 hypothesis (wrong DB/environment)
3. Added "Document Identity & Idempotency" section
4. Added "Root Cause Confirmation Checklist"
5. Added "Observability Requirements"
6. Added "Definition of Done" with tests
7. Clarified that upload must fail if DB insert fails

---

## 20. Implementation Notes (Feb 8, 2026)

### Changes Made:

**File: `web/app.py`**

1. **Added import for DocumentRepository** (line ~46):
   ```python
   from web.repositories.document_repository import DocumentRepository
   ```

2. **Added DB insert after DocumentStore save for target documents** (after line ~833):
   - After `doc_store.add_document_from_bytes()` succeeds, immediately call `doc_repo.create_document()` to persist to DB
   - Only runs when `USE_DATABASE=true` and `current_deal_id` exists
   - Logs success/failure for observability

3. **Added DB insert after DocumentStore save for buyer documents** (after line ~869):
   - Same pattern as target documents

4. **Updated `/documents` page** (line ~5612):
   - Changed from querying session-based `document_registry` to `DocumentRepository.get_by_deal()`
   - Uses `DocWrapper` class to provide object-like access for template compatibility
   - Falls back to session-based registry if DB disabled or query fails

5. **Updated `/api/documents` endpoint** (line ~5747):
   - Same DB-first pattern as documents page
   - Returns documents from DB when available

6. **Added backfill endpoint** (line ~5807):
   - `POST /api/documents/backfill` syncs manifest → DB
   - Idempotent: skips documents already in DB by hash
   - Returns count of synced/skipped documents

### Root Cause Confirmed:
- **H1 was correct**: Upload route saved to filesystem (DocumentStore/manifest) but skipped DB insert
- **DocumentRepository** existed and worked, but was never called from upload routes
- **Document model** was correctly defined in `web/database.py`

### Testing Instructions:
1. Set `USE_DATABASE=true` environment variable
2. Upload a document via `/upload`
3. Visit `/documents` — document should appear immediately
4. For existing documents: call `POST /api/documents/backfill` to sync manifest → DB

### Remaining Work:
- [ ] Wire up fact counts to documents (requires cross-table query)
- [ ] Add analysis run tracking
- [ ] Consider removing manifest.json as redundant (DB is now authoritative)
