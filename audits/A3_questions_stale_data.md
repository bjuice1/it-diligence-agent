# Audit A3: Questions Using Stale Data

## Status: IMPLEMENTED ✓
## Priority: HIGH (Tier 1 - Quick Win)
## Complexity: Quick
## Implementation Date: Feb 8, 2026

---

## 1. Problem Statement

**Symptom:** Questions feature displays data from previous deals/sessions instead of current analysis.

**User Impact:**
- Users see irrelevant questions not related to their current deal
- Confusing UX - appears system is showing wrong analysis
- Cannot trust question recommendations

**Expected Behavior:** Questions should only show items generated from the current deal's analysis.

---

## 2. Current Evidence

- User reported questions appearing that relate to old/different deals
- Exact query and data source not yet traced
- Need to verify: is this a query scope issue or caching issue?

---

## 3. Hypotheses

| # | Hypothesis | Likelihood | How to Verify |
|---|------------|------------|---------------|
| H1 | Query missing `deal_id` filter | HIGH | Read query in route |
| H2 | Questions cached in Flask session | MEDIUM | Check for session usage |
| H3 | Questions stored globally, not per-deal | MEDIUM | Check model/table schema |
| H4 | Wrong table being queried | LOW | Verify table name |
| H5 | deal_id passed but wrong value | MEDIUM | Trace deal_id source |

---

## 4. Architecture Understanding

### Question Flow (Expected):
```
Analysis runs for deal X
    → Discovery agents identify gaps
    → Questions generated from gaps
    → Questions stored with deal_id = X
    → UI queries questions WHERE deal_id = X
    → User sees questions for deal X only
```

### Key Components:
1. **Question generation:** Likely in reasoning agents or separate step
2. **Question storage:** `OpenQuestion` model in database
3. **Question display:** Route in `web/app.py`

---

## 5. Files to Investigate

### Primary Files:
| File | What to Look For |
|------|------------------|
| `web/app.py` | Questions route - find the query |
| `web/database.py` | `OpenQuestion` model - has deal_id field? |

### Secondary Files:
| File | What to Look For |
|------|------------------|
| `agents_v2/*_reasoning_agent.py` | Where questions are generated |
| `stores/fact_store.py` | Gap → Question relationship |
| `web/tasks/analysis_tasks.py` | Question generation in pipeline |

---

## 6. Audit Steps

### Phase 1: Trace the Query
- [ ] 1.1 Find questions route in `web/app.py` (search for "question" in routes)
- [ ] 1.2 Read the database query - is deal_id filtered?
- [ ] 1.3 Check `OpenQuestion` model schema

### Phase 2: Trace Question Generation
- [ ] 2.1 Find where questions are created
- [ ] 2.2 Verify deal_id is set on creation
- [ ] 2.3 Check for any global/shared question storage

### Phase 3: Check for Caching
- [ ] 3.1 Search for Flask session usage with questions
- [ ] 3.2 Check for Redis caching of questions
- [ ] 3.3 Look for in-memory caching

### Phase 4: Fix & Verify
- [ ] 4.1 Add deal_id filter if missing
- [ ] 4.2 Clear any stale caches
- [ ] 4.3 Test with multiple deals - verify isolation

---

## 7. Potential Solutions

### Solution A: Add deal_id Filter to Query
```python
# Before (broken):
questions = OpenQuestion.query.all()

# After (fixed):
questions = OpenQuestion.query.filter_by(deal_id=deal_id).all()
```

### Solution B: Fix deal_id on Question Creation
```python
# Ensure deal_id is set when creating questions
question = OpenQuestion(
    deal_id=deal_id,  # Must be passed through
    question_text=text,
    domain=domain,
    # ...
)
```

### Solution C: Clear Session/Cache
```python
# If questions cached in session
session.pop('questions', None)

# If using Redis
cache.delete(f'questions:{deal_id}')
```

---

## 8. Database Schema Check

Expected `OpenQuestion` model:
```python
class OpenQuestion(db.Model):
    id = db.Column(db.String, primary_key=True)
    deal_id = db.Column(db.String, nullable=False)  # MUST EXIST
    domain = db.Column(db.String)
    question_text = db.Column(db.Text)
    priority = db.Column(db.String)
    status = db.Column(db.String)
    created_at = db.Column(db.DateTime)
```

If `deal_id` column doesn't exist, need migration.

---

## 9. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing questions | Add filter, don't delete data |
| Missing deal_id on old questions | Backfill or filter out null deal_ids |
| Performance with many deals | Ensure deal_id is indexed |

---

## 10. Success Criteria

- [ ] Questions route includes `deal_id` filter
- [ ] Switching deals shows different questions
- [ ] New deal shows no questions until analysis runs
- [ ] Questions persist correctly per deal

---

## 11. Questions for Review

1. Where are questions generated - discovery or reasoning phase?
2. Is there a separate "Questions Agent" or embedded in other agents?
3. Should questions be deletable/editable by users?
4. Are questions derived from Gaps or generated independently?

---

## 12. Dependencies

- None

## 13. Blocks

- Question-driven workflow features

---

## 14. Implementation Notes (Feb 8, 2026)

### Root Cause Confirmed
**H1 was correct**: Questions were saved to global files (`open_questions_{timestamp}.json`) without deal_id, and the UI route loaded the most recent file regardless of which deal created it.

### Changes Made

**File: `web/analysis_runner.py` (line ~972)**
- Questions now saved with deal_id in filename: `open_questions_{deal_id}_{timestamp}.json`
- Falls back to timestamp-only for legacy compatibility when no deal_id

**File: `web/app.py` (route `/open-questions`)**
- Now filters questions files by current deal_id from session
- Searches for `open_questions_{current_deal_id}_*.json` pattern
- Falls back to legacy files only when no deal selected

### Testing Instructions
1. Create/select Deal A, run analysis → questions saved as `open_questions_{deal_a_id}_*.json`
2. Create/select Deal B, run analysis → questions saved as `open_questions_{deal_b_id}_*.json`
3. Visit `/open-questions` with Deal A selected → see only Deal A questions
4. Switch to Deal B → see only Deal B questions

### Backwards Compatibility
- Existing question files without deal_id are still loadable (legacy fallback)
- New files always include deal_id for proper isolation
