# Audit B1: Buyer/Target Entity Separation

## Status: PARTIALLY IMPLEMENTED ✓
## Priority: HIGH (Tier 2 - Data Integrity)
## Complexity: Medium
## Review Score: 8.0/10 (GPT review, Feb 8 2026)
## Implementation Date: Feb 8, 2026

---

## 1. Problem Statement

**Symptom:** Some views mix buyer and target data instead of showing only target company information.

**User Impact:**
- Buyer apps appearing in target analysis
- Confusing reports mixing two companies
- Incorrect risk assessments
- Misleading application counts

**Expected Behavior:** Target views show only target entity data. Buyer views show only buyer entity data. Clear separation throughout.

---

## 2. Product Decision & Invariants (GPT FEEDBACK)

### Decision: Default View is Target-Only

**Rationale:** Due diligence is about what you're buying (the target). Buyer data is context, not the focus.

**Invariants:**
1. All diligence views default to `entity='target'`
2. Buyer data is accessible ONLY via explicit toggle or separate "Buyer" section
3. Entity field is **NOT NULL** in database
4. Entity values are constrained to: `target`, `buyer` (add `synergy` later if needed)
5. Facts without entity are invalid and should not exist

**UI Behavior:**
- `/applications` → shows target apps only (no toggle needed for v1)
- `/applications?entity=buyer` → shows buyer apps (optional, future)
- Buyer section is separate tab/route, not mixed

---

## 3. Entity Contract (GPT FEEDBACK)

### Database Constraints (REQUIRED):

```sql
-- Add check constraint to facts table
ALTER TABLE facts
ADD CONSTRAINT entity_valid CHECK (entity IN ('target', 'buyer'));

-- Ensure NOT NULL
ALTER TABLE facts
ALTER COLUMN entity SET NOT NULL;

-- Same for other tables with entity
ALTER TABLE documents
ADD CONSTRAINT doc_entity_valid CHECK (entity IN ('target', 'buyer'));
```

### Model-Level Enforcement:

```python
# In web/database.py
class Fact(db.Model):
    entity = db.Column(
        db.String(20),
        nullable=False,  # NOT NULL
        default='target'
    )

    @validates('entity')
    def validate_entity(self, key, value):
        allowed = ['target', 'buyer']
        if value not in allowed:
            raise ValueError(f"entity must be one of {allowed}")
        return value
```

---

## 4. Current Evidence

From manifest.json:
- 7 documents marked as `entity: "target"`
- 1 document marked as `entity: "buyer"` (Buyer Company Profile - Atlantic International.pdf)

Need to verify:
- Are facts being stored with correct entity?
- Are UI queries filtering by entity?

---

## 5. Hypotheses

| # | Hypothesis | Likelihood | How to Verify |
|---|------------|------------|---------------|
| H1 | UI queries not filtering by `entity='target'` | HIGH | Read route queries |
| H2 | Facts stored with wrong entity value | MEDIUM | Query DB, check entity distribution |
| H3 | Entity not passed through analysis pipeline | MEDIUM | Trace entity param through code |
| H4 | Buyer docs processed as target | LOW | Check document → entity mapping |
| H5 | Entity column missing from some tables | LOW | Check all relevant models |
| **H6** | **Old facts have NULL entity, queries include them** | **HIGH** | Query for NULL/empty entity |

> **Note (GPT):** H6 elevated - if you've iterated a lot, old facts with missing entity will silently mix in.

---

## 6. Entity Inference & Backfill Policy (GPT FEEDBACK)

### Backfill Rule:
```
fact.entity = document.entity (via fact.source_document_id → documents.entity)
```

### Required for backfill to work:
- Every fact must have `source_document_id`
- Every document must have `entity`
- If `source_document_id` missing, cannot backfill (must delete or manually tag)

### Backfill Script:

```python
def backfill_fact_entities(deal_id: str):
    """Backfill entity on facts from their source documents."""

    # Get all facts without entity
    facts_to_fix = Fact.query.filter(
        Fact.deal_id == deal_id,
        (Fact.entity.is_(None)) | (Fact.entity == '')
    ).all()

    fixed = 0
    for fact in facts_to_fix:
        if fact.source_document_id:
            doc = Document.query.get(fact.source_document_id)
            if doc and doc.entity:
                fact.entity = doc.entity
                fixed += 1
        else:
            # No source doc - default to target with warning
            logger.warning(f"Fact {fact.id} has no source_document_id, defaulting to target")
            fact.entity = 'target'
            fixed += 1

    db.session.commit()
    logger.info(f"Backfilled {fixed} facts for deal {deal_id}")
    return fixed
```

---

## 7. Architecture Understanding

### Entity Flow (Expected):
```
Document uploaded with entity = "target" or "buyer"
    → Manifest records entity per document
    → Document table stores entity
    → Analysis task receives entity parameter
    → Discovery agent uses entity for fact creation
    → Facts stored with entity field (NOT NULL)
    → UI queries filter by entity='target'
    → User sees only target data
```

### Key Touch Points:
1. **Document level:** `manifest.json` + `documents` table → entity per doc
2. **Analysis level:** `run_domain_discovery()` → entity param
3. **Storage level:** `FactStore.add_fact()` → entity field (required)
4. **Query level:** UI routes → `filter_by(entity='target')` (always)

---

## 8. Files to Investigate

### Primary Files:
| File | What to Look For |
|------|------------------|
| `web/app.py` | UI routes - entity filtering in queries |
| `web/tasks/analysis_tasks.py` | Entity handling per document |
| `tools_v2/deterministic_parser.py` | Entity param in `add_fact()` calls |

### Secondary Files:
| File | What to Look For |
|------|------------------|
| `agents_v2/base_discovery_agent.py` | Entity passed to discovery |
| `stores/fact_store.py` | Entity field on Fact dataclass |
| `web/database.py` | Entity column on Fact model (NOT NULL?) |

### Key Routes to Check:
| Route | Expected Behavior |
|-------|-------------------|
| `/applications` | Show only target apps |
| `/infrastructure` | Show only target infra |
| `/organization` | Show only target org |
| `/risks` | Show only target risks |

---

## 9. Audit Steps

### Phase 1: Verify Data Storage
- [ ] 1.1 Query DB: `SELECT entity, COUNT(*) FROM facts GROUP BY entity`
- [ ] 1.2 Query for NULL/empty entity: `SELECT COUNT(*) FROM facts WHERE entity IS NULL OR entity = ''`
- [ ] 1.3 Check if buyer facts exist separately from target
- [ ] 1.4 Sample some facts - verify entity matches source doc

### Phase 2: Trace Entity Through Pipeline
- [ ] 2.1 Check manifest.json - all docs have entity?
- [ ] 2.2 Check `analysis_tasks.py` - entity passed per document?
- [ ] 2.3 Check `deterministic_parser.py` - entity used in add_fact?
- [ ] 2.4 Check discovery agents - entity propagated?

### Phase 3: Audit UI Queries
- [ ] 3.1 Find `applications_overview()` route
- [ ] 3.2 Check query - filtered by entity?
- [ ] 3.3 Repeat for all domain routes
- [ ] 3.4 Check report generation - entity filtered?

### Phase 4: Add Constraints
- [ ] 4.1 Add NOT NULL constraint to entity column
- [ ] 4.2 Add CHECK constraint for valid values
- [ ] 4.3 Add model-level validation
- [ ] 4.4 Run backfill for existing NULL entities

### Phase 5: Fix & Verify
- [ ] 5.1 Add missing entity filters to all queries
- [ ] 5.2 Verify entity passed correctly through pipeline
- [ ] 5.3 Test with deal that has both buyer and target docs
- [ ] 5.4 Run cross-contamination test

---

## 10. Potential Solutions

### Solution A: Add Entity Filter to UI Queries (SHIP FIRST)
```python
# Before (broken):
apps = Fact.query.filter_by(deal_id=deal_id, domain='applications').all()

# After (fixed):
apps = Fact.query.filter_by(
    deal_id=deal_id,
    domain='applications',
    entity='target'  # Add this filter
).all()
```

### Solution B: Fix Entity in Analysis Pipeline (IF AUDIT SHOWS WRONG STORAGE)
```python
# In analysis_tasks.py
for doc in manifest['documents']:
    entity = doc.get('entity', 'target')  # Get from manifest
    run_domain_discovery(
        document_text=text,
        entity=entity,  # Pass through
        ...
    )
```

### Solution C: Toggle (OPTIONAL, PRODUCT DECISION)
```python
# Only if you want buyer visible in UI
@app.route('/applications')
def applications_overview():
    entity = request.args.get('entity', 'target')  # Default target
    apps = Fact.query.filter_by(
        deal_id=deal_id,
        domain='applications',
        entity=entity
    ).all()
```

---

## 11. Cross-Contamination Test (GPT FEEDBACK)

### Automated Integration Test:

```python
def test_entity_separation():
    """Verify no cross-contamination between buyer and target."""

    # Setup: Upload one buyer doc + one target doc
    deal_id = create_test_deal()
    upload_document(deal_id, 'target_app_inventory.md', entity='target')
    upload_document(deal_id, 'buyer_profile.pdf', entity='buyer')

    # Run analysis
    run_analysis(deal_id)

    # Query target apps
    target_apps = Fact.query.filter_by(
        deal_id=deal_id,
        domain='applications',
        entity='target'
    ).all()

    # Query buyer apps
    buyer_apps = Fact.query.filter_by(
        deal_id=deal_id,
        domain='applications',
        entity='buyer'
    ).all()

    # Assert no buyer facts in target query
    for app in target_apps:
        assert app.entity == 'target', f"Buyer app in target: {app.item}"

    # Assert no target facts in buyer query
    for app in buyer_apps:
        assert app.entity == 'buyer', f"Target app in buyer: {app.item}"

    # Assert counts match expectations
    assert len(target_apps) > 0, "Should have target apps"
    # buyer_apps may be 0 if buyer doc has no apps
```

---

## 12. Synergy Fact Type (GPT FEEDBACK - Future)

For buyer/target comparisons, DON'T hack it with mixed entities. Create a dedicated type:

```python
# Future: For integration analysis
class SynergyFact(db.Model):
    id = db.Column(db.String, primary_key=True)
    deal_id = db.Column(db.String, nullable=False)
    domain = db.Column(db.String)  # 'integration', 'synergy'

    # Comparison fields
    target_fact_id = db.Column(db.String, db.ForeignKey('facts.id'))
    buyer_fact_id = db.Column(db.String, db.ForeignKey('facts.id'))

    comparison_type = db.Column(db.String)  # 'overlap', 'gap', 'opportunity'
    description = db.Column(db.Text)
```

This keeps diligence views clean while enabling future value.

---

## 13. Database Verification Queries

```sql
-- Check entity distribution
SELECT entity, domain, COUNT(*)
FROM facts
WHERE deal_id = '28d0aabe-...'
GROUP BY entity, domain
ORDER BY entity, domain;

-- Find any facts without entity (CRITICAL)
SELECT COUNT(*) as null_entity_count
FROM facts
WHERE entity IS NULL OR entity = '';

-- Compare target vs buyer app counts
SELECT entity, COUNT(*)
FROM facts
WHERE domain = 'applications' AND deal_id = '...'
GROUP BY entity;

-- Verify source document has entity
SELECT f.id, f.item, f.entity as fact_entity, d.entity as doc_entity
FROM facts f
LEFT JOIN documents d ON f.source_document_id = d.id
WHERE f.deal_id = '...'
AND f.entity != d.entity;  -- Mismatches
```

---

## 14. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Missing entity on old facts | Backfill script with source doc lookup |
| Breaking buyer-side features | Ensure buyer routes also filter correctly |
| Mixed entity in single doc | Validate: shouldn't happen |
| NULL entity slipping through | DB constraint prevents this |

---

## 15. Definition of Done

### Must have:
- [ ] All UI queries include `entity='target'` filter
- [ ] Entity column is NOT NULL with valid values constraint
- [ ] Backfill completes for existing NULL entities
- [ ] Cross-contamination test passes
- [ ] No buyer data appears in any target view

### Tests:
- [ ] Unit test: fact creation requires valid entity
- [ ] Unit test: NULL entity rejected
- [ ] Integration test: upload buyer + target → no mixing
- [ ] Query test: target route returns 0 buyer facts

---

## 16. Success Criteria

- [ ] DB query shows correct entity counts per domain
- [ ] Target views show only target apps/infra/etc
- [ ] Buyer views (if exist) show only buyer data
- [ ] Entity flows correctly from doc → manifest → analysis → storage → display
- [ ] No cross-contamination between entities
- [ ] NULL/empty entity count is 0

---

## 17. Questions Resolved

| Question | Decision |
|----------|----------|
| Combined buyer+target view? | No - separate or no buyer view in v1 |
| Entity selectable in UI? | Default target; optional param for future |
| Integration/synergy facts? | Separate `SynergyFact` type (future) |
| Validation on buyer docs? | Yes - constrain at DB and model level |

---

## 18. Dependencies

- A2 (Documents not showing) - helps verify doc→entity mapping

## 19. Blocks

- Accurate reporting per entity
- Integration analysis features (future)

---

## 20. GPT Review Notes (Feb 8, 2026)

**Score: 8.0/10**

**Strengths:**
- Crisp problem framing
- Evidence anchored in manifest
- End-to-end entity flow is the right mental model
- Audit phases ordered correctly

**Improvements made based on feedback:**
1. Added explicit "Product Decision" - default view is target-only
2. Added "Entity Contract" - DB constraints + model validation
3. Added "Entity Inference & Backfill Policy" with script
4. Added H6 hypothesis (NULL entity mixing)
5. Added "Cross-Contamination Test" (automated)
6. Added "Synergy Fact Type" design for future comparisons
7. Added "Definition of Done" with specific tests

---

## 21. Implementation Notes (Feb 8, 2026)

### Findings

**Good news:** Most domain routes already filter by entity='target':
- `/applications` - correctly uses `data.get_all_facts(entity='target')` (line 3133)
- `/applications/<category>` - correctly uses `entity='target'` (line 3218)
- `/infrastructure` - correctly uses `entity='target'` (line 3263)
- `/organization` - uses bridge function with `entity='target'` (line 2411)

**Issue found:** The `/facts` route did NOT default to target:
- Line 1853: `entity_filter = request.args.get('entity', '')` → allowed showing ALL entities

### Fix Applied

**File: `web/app.py` (line ~1853)**
```python
# Before:
entity_filter = request.args.get('entity', '')

# After (B1 FIX):
entity_filter = request.args.get('entity', 'target')  # Default target, not empty
```

### Remaining Work

1. **Finding model lacks entity field** - Risks/work items don't have entity column
   - Low priority: findings are deal-scoped, and deals are typically target-focused
   - Future: Add `entity` column to Finding model if buyer-specific findings needed

2. **Database constraints not yet added** - NOT NULL + CHECK constraints
   - Should add migration to enforce entity constraints at DB level

3. **Cross-contamination test not implemented** - automated test pending

### Status: PARTIALLY COMPLETE
The main UI routes now default to target entity. Full implementation would add DB constraints and entity to findings.
