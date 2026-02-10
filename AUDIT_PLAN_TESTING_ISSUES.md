# Audit Plan: Testing Issues (Feb 7, 2026)

## Issue Summary

| # | Issue | Expected | Actual | Priority | Status |
|---|-------|----------|--------|----------|--------|
| 1 | Target apps incomplete | 33 apps | 19 apps | **CRITICAL** | **FIXED** |
| 2 | Buyer/Target separation | Separate views | Mixed in some views | HIGH | OPEN |
| 3 | Documents not showing | Documents visible | "No documents" | HIGH | OPEN |
| 4 | Risks vs Gaps classification | Gaps = missing info | Many gaps as risks | MEDIUM | OPEN |
| 5 | Risk consolidation | Related risks grouped | Duplicates/fragments | MEDIUM | OPEN |
| 6 | Questions using old data | Current deal data | Stale data | MEDIUM | OPEN |

---

## Audit 1: Target Apps Incomplete (19 vs 33) ✅ FIXED

### Root Cause Found
**Bug:** `deterministic_parser.py` was passing `extraction_method="deterministic_parser"` to `FactStore.add_fact()`, but that parameter doesn't exist in the method signature.

All 33 apps were being found and parsed correctly, but every single `add_fact()` call was failing silently with:
```
FactStore.add_fact() got an unexpected keyword argument 'extraction_method'
```

### Fix Applied
Removed `extraction_method` parameter from three locations in `tools_v2/deterministic_parser.py`:
- Line 390 (app table to facts)
- Line 477 (infra table to facts)
- Line 522 (contract table to facts)

### Verification
```
$ python3 -c "..." (test script with deterministic parser)
Facts created: 33
Application facts: 33
All apps extracted:
  1. Duck Creek Policy
  2. Majesco Policy for L&A
  ... (all 33 apps)
```

### Files Modified
- `tools_v2/deterministic_parser.py` - removed invalid parameter

---

## Audit 2: Buyer/Target Separation

### Hypothesis
- Facts stored with wrong entity
- Views not filtering by entity correctly
- Entity assignment logic broken

### Audit Steps
1. [ ] Query DB: Count facts by entity per domain
2. [ ] Check entity assignment in deterministic parser
3. [ ] Check entity assignment in LLM discovery
4. [ ] Verify UI routes filter by entity='target' correctly
5. [ ] Check if buyer docs being processed as target

### Files to Check
- `web/app.py` - applications_overview route (line 3072)
- `tools_v2/deterministic_parser.py` - entity parameter
- `web/tasks/analysis_tasks.py` - entity handling

---

## Audit 3: Documents Not Showing

### Hypothesis
- Documents not being saved to Document table
- Document upload path broken
- Query not finding documents for deal

### Audit Steps
1. [ ] Query Document table for recent deal
2. [ ] Check document upload route
3. [ ] Check document processing task
4. [ ] Trace document storage path
5. [ ] Check if documents stored in filesystem but not DB

### Files to Check
- `web/app.py` - document upload routes
- `web/tasks/analysis_tasks.py` - process_document_task
- `web/database.py` - Document model

### Current Finding
```sql
SELECT * FROM documents WHERE deal_id = '28d0aabe-...'
-- Returns 0 rows (documents not being stored)
```

---

## Audit 4: Risks vs Gaps Classification

### Hypothesis
- Discovery agents flagging gaps as risks
- No distinction in prompt between "missing info" and "confirmed problem"
- Reasoning agent treating all issues as risks

### Audit Steps
1. [ ] Review discovery agent prompts for gap definition
2. [ ] Review reasoning agent prompts for risk definition
3. [ ] Check Gap model vs Risk model usage
4. [ ] Sample current gaps - are they actually gaps or risks?
5. [ ] Define clear criteria: Gap = need info, Risk = confirmed issue

### Files to Check
- `prompts/v2_*_discovery_prompt.py` - gap flagging logic
- `prompts/v2_*_reasoning_prompt.py` - risk identification
- `stores/fact_store.py` - Gap dataclass

---

## Audit 5: Risk Consolidation

### Hypothesis
- No deduplication of related risks
- LLM generating similar risks from different facts
- Need post-processing to consolidate

### Audit Steps
1. [ ] Query current risks for deal
2. [ ] Identify duplicate/related risks manually
3. [ ] Design consolidation logic (similarity matching)
4. [ ] Consider "Risk PE Agent" for review pass
5. [ ] Define risk grouping criteria

### Potential Solution
- Add risk consolidation step after reasoning
- Group by: same system, same theme, overlapping facts
- Use LLM to merge related risks into single comprehensive risk

---

## Audit 6: Questions Using Old Data

### Hypothesis
- Questions query not scoped to current deal
- Questions cached from previous session
- Database query hitting wrong table

### Audit Steps
1. [ ] Find questions route in app
2. [ ] Check query for deal_id filter
3. [ ] Trace data source for questions
4. [ ] Check for caching issues
5. [ ] Verify questions table schema

### Files to Check
- `web/app.py` - questions routes
- `web/database.py` - OpenQuestion model
- Question generation logic

---

## Execution Order

1. **Audit 1** (Apps incomplete) - CRITICAL, blocks testing
2. **Audit 3** (Documents) - Need to understand data flow
3. **Audit 2** (Buyer/Target) - Affects all views
4. **Audit 6** (Questions) - Quick check
5. **Audit 4** (Risks/Gaps) - Prompt changes
6. **Audit 5** (Risk consolidation) - New feature

---

## Quick Wins vs Deep Fixes

### Quick Wins (can fix now)
- Check deterministic parser table detection
- Add deal_id filter to questions query
- Fix document storage in analysis task

### Deep Fixes (need design)
- Risk consolidation agent
- Gap vs Risk semantic separation
- Interactive diagram generation
