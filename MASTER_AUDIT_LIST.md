# Master Audit List (Feb 7, 2026)

## Overview

Comprehensive list of all known issues, bugs, and improvements needed. Each audit includes:
- **Problem Statement**: What's broken or missing
- **Impact**: How it affects users
- **Complexity**: Estimated effort (Quick/Medium/Deep)
- **Dependencies**: What must be done first
- **Status**: OPEN / IN PROGRESS / FIXED

---

## Priority Tiers

### Tier 1: Critical Bugs (Blocking Testing)
| ID | Issue | Status | Complexity |
|----|-------|--------|------------|
| A1 | Target apps incomplete (19 vs 33) | **FIXED** | Quick |
| A2 | Documents not showing | OPEN | Quick |
| A3 | Questions using old data | OPEN | Quick |

### Tier 2: Data Integrity Issues
| ID | Issue | Status | Complexity |
|----|-------|--------|------------|
| B1 | Buyer/Target entity separation | OPEN | Medium |
| B2 | App inventory field normalization | OPEN | Medium |
| B3 | Risks vs Gaps classification | OPEN | Medium |

### Tier 3: Feature Improvements
| ID | Issue | Status | Complexity |
|----|-------|--------|------------|
| C1 | Risk consolidation/deduplication | OPEN | Deep |
| C2 | Inline report editing with persistence | OPEN | Deep |
| C3 | Org chart (replace broken mermaid) | OPEN | Medium |

### Tier 4: Future Enhancements
| ID | Issue | Status | Complexity |
|----|-------|--------|------------|
| D1 | Document inventory (facts per doc) | BACKLOG | Medium |
| D2 | Diagram generation | BACKLOG | Deep |
| D3 | IT org L1-L5 layering | BACKLOG | Deep |

---

## Tier 1: Critical Bugs

### A1: Target Apps Incomplete ✅ FIXED
**Problem:** Only 19 of 33 target apps were extracting from documents.

**Root Cause:** `deterministic_parser.py` passed `extraction_method="deterministic_parser"` to `FactStore.add_fact()`, but that parameter doesn't exist.

**Fix Applied:** Removed invalid parameter from 3 locations in `tools_v2/deterministic_parser.py`.

**Verified:** All 33 apps now extract correctly.

---

### A2: Documents Not Showing
**Problem:** Dashboard and UI show "No documents" even after upload.

**Impact:** Users can't see what documents were analyzed.

**Complexity:** Quick

**Hypotheses:**
1. Documents not being saved to `Document` table in DB
2. Query not filtering by correct `deal_id`
3. Documents stored in filesystem but not tracked in DB
4. Upload route not creating DB records

**Audit Steps:**
1. [ ] Query `Document` table for test deal: `SELECT * FROM documents WHERE deal_id = ?`
2. [ ] Trace upload route in `web/app.py` - does it insert to DB?
3. [ ] Check `manifest.json` vs DB records - are they in sync?
4. [ ] Find document display route and verify query

**Files to Investigate:**
- `web/app.py` - document upload routes, display routes
- `web/database.py` - Document model
- `web/tasks/analysis_tasks.py` - document processing
- `uploads/{deal_id}/manifest.json` - file manifest

**Current Evidence:**
```sql
SELECT * FROM documents WHERE deal_id = '28d0aabe-79cd-4376-a2db-e2e82640596a'
-- Returns 0 rows
```
But `manifest.json` shows 8 documents uploaded.

---

### A3: Questions Using Old Data
**Problem:** Questions feature displays stale data from previous deals/sessions.

**Impact:** Users see irrelevant questions not related to current analysis.

**Complexity:** Quick

**Hypotheses:**
1. Query not scoped to current `deal_id`
2. Questions cached in session/memory
3. Query hitting wrong table

**Audit Steps:**
1. [ ] Find questions route in `web/app.py`
2. [ ] Check SQL query for `deal_id` filter
3. [ ] Check `OpenQuestion` model in `web/database.py`
4. [ ] Trace where questions are generated/stored
5. [ ] Check for caching in Flask session

**Files to Investigate:**
- `web/app.py` - questions routes
- `web/database.py` - OpenQuestion model
- Question generation in agents

---

## Tier 2: Data Integrity Issues

### B1: Buyer/Target Entity Separation
**Problem:** Some views mix buyer and target data instead of showing only target.

**Impact:** Confusing UX; buyer apps appearing in target analysis.

**Complexity:** Medium

**Hypotheses:**
1. Facts stored with wrong `entity` value
2. UI queries not filtering by `entity='target'`
3. Entity parameter not passed correctly through pipeline

**Audit Steps:**
1. [ ] Query DB: `SELECT entity, COUNT(*) FROM facts GROUP BY entity`
2. [ ] Check `deterministic_parser.py` - is entity passed correctly?
3. [ ] Check `analysis_tasks.py` - entity handling per document
4. [ ] Check UI routes - are they filtering by entity?
5. [ ] Review `manifest.json` - documents have correct entity?

**Files to Investigate:**
- `web/app.py` - `applications_overview()` route (~line 3072)
- `tools_v2/deterministic_parser.py` - entity parameter in `add_fact()`
- `web/tasks/analysis_tasks.py` - entity per document
- `uploads/{deal_id}/manifest.json` - entity per document

---

### B2: App Inventory Field Normalization
**Problem:** Missing attributes (vendor, version, user_count) due to field name inconsistencies.

**Impact:** Incomplete app data in reports; empty columns.

**Complexity:** Medium

**Root Causes:**
1. **Field name inconsistency**: `criticality` vs `business_criticality`, `deployment` vs `hosting`
2. **Category fragmentation**: Only 9 categories recognized; insurance-specific ones fall through
3. **Two data sources compete**: FactStore and InventoryStore never merged
4. **No enrichment**: Missing fields stay blank

**Solution Plan:**
1. Create `services/field_normalizer.py` with:
   - `FIELD_ALIASES` mapping (criticality → [criticality, business_criticality, app_criticality])
   - `CATEGORY_NORMALIZATION` mapping (policy_administration → vertical)
   - `normalize_detail(details, canonical_name)` function
   - `normalize_category(raw_category)` function

2. Refactor `services/applications_bridge.py`:
   - Use normalizer for all field lookups
   - Add `merge_inventories()` to combine FactStore + InventoryStore

3. Update `tools_v2/presentation.py`:
   - Add `vertical`, `other` to category order
   - Use normalizer in `_build_app_landscape_html()`

**Files to Modify:**
- `services/field_normalizer.py` (NEW)
- `services/applications_bridge.py`
- `tools_v2/presentation.py`
- `web/app.py` - `applications_overview()` route

---

### B3: Risks vs Gaps Classification
**Problem:** Many items classified as "risks" should be "gaps" (missing information).

**Impact:** Inflated risk count; confuses what needs investigation vs what's a known problem.

**Complexity:** Medium

**Definitions:**
- **Gap**: Information we don't have yet → request from seller
- **Risk**: Confirmed problem we found → needs mitigation

**Hypotheses:**
1. Discovery prompts don't distinguish gap vs risk
2. Reasoning agent treats all issues as risks
3. No semantic criteria in prompts

**Audit Steps:**
1. [ ] Review discovery prompts in `prompts/v2_*_discovery_prompt.py`
2. [ ] Review reasoning prompts in `prompts/v2_*_reasoning_prompt.py`
3. [ ] Check `Gap` dataclass in `stores/fact_store.py`
4. [ ] Sample current gaps - are they actually gaps or misclassified risks?
5. [ ] Define clear criteria and update prompts

**Files to Investigate:**
- `prompts/v2_applications_discovery_prompt.py`
- `prompts/v2_infrastructure_discovery_prompt.py`
- `prompts/v2_*_reasoning_prompt.py`
- `stores/fact_store.py` - Gap dataclass

---

## Tier 3: Feature Improvements

### C1: Risk Consolidation/Deduplication
**Problem:** Multiple related/duplicate risks appear separately instead of grouped.

**Impact:** Redundant content; harder to prioritize; looks unprofessional.

**Complexity:** Deep

**Example:** Two separate risks about "multiple ERP environments" should be one consolidated risk.

**Solution Design:**
1. Add post-reasoning consolidation step
2. Group risks by: same system, same theme, overlapping supporting facts
3. Use LLM to merge related risks into single comprehensive risk
4. Consider "Risk PE Agent" as dedicated review pass

**Implementation Options:**
- Option A: Embedding-based similarity (group risks with cosine similarity > 0.8)
- Option B: LLM consolidation pass (ask model to group and merge)
- Option C: Rule-based grouping (same app name, same domain, same keywords)

**Files to Create/Modify:**
- `agents_v2/risk_consolidation_agent.py` (NEW)
- `web/tasks/analysis_tasks.py` - add consolidation step
- `stores/fact_store.py` - risk grouping methods

---

### C2: Inline Report Editing with Persistence
**Problem:** Report edit buttons exist but don't save; edits lost on reload.

**Impact:** Users can't customize reports; have to manually edit exports.

**Complexity:** Deep

**Current State:**
- `domain_template.html` has `.editable` elements, `toggleEdit()`, `saveEdits()` JS
- Three POST endpoints in `pe_reports.py` are stubs (log and return OK, don't persist)
- Template with editing UI not wired to web routes

**Solution Plan:**
1. Add `ReportOverride` model to `web/database.py`
2. Implement three save endpoints in `pe_reports.py`
3. Switch web view to Jinja template (not standalone HTML)
4. Add override loading/applying helpers
5. Add visual indicators for edited content
6. Apply overrides in ZIP export

**Files to Create/Modify:**
- `web/database.py` - add ReportOverride model
- `web/blueprints/pe_reports.py` - implement endpoints
- `web/templates/reports/domain_template.html` - visual indicators

---

### C3: Org Chart (Replace Broken Mermaid)
**Problem:** Mermaid org chart crashes on special characters, doesn't scale, hardcoded root.

**Impact:** Org chart unusable for most real data; crashes on O'Brien, R&D, etc.

**Complexity:** Medium

**Current Problems:**
- Parent matching uses text substring comparison
- Hardcoded "CIO / IT Leader" as root
- Crashes on apostrophes, ampersands, parentheses
- Doesn't scale past 20-30 nodes
- Three incompatible implementations

**Solution Plan:**
1. Create CSS-based tree layout (`web/static/css/org_tree.css`)
2. Build tree data from facts with proper hierarchy detection
3. Render with HTML escaping (no special char issues)
4. Fall back to flat list when hierarchy unavailable
5. Replace mermaid in `staffing_tree.html`

**Files to Create/Modify:**
- `web/static/css/org_tree.css` (NEW)
- `web/templates/organization/_org_tree.html` (NEW)
- `web/templates/organization/staffing_tree.html` - remove mermaid
- `tools_v2/presentation.py` - add `_build_org_tree_html()`
- `web/app.py` - pass tree data to template

---

## Tier 4: Future Enhancements (Backlog)

### D1: Document Inventory (Facts per Doc)
- Show which facts were extracted from each document
- Track document sections → facts mapping
- Multi-contract handling improvements

### D2: Diagram Generation
- Generate Mermaid diagrams from system data
- Parse Visio files for architecture
- Interactive system connection diagrams
- Application data flow visualization

### D3: IT Org L1-L5 Layering
- Infer management layers from census data
- Org design assumptions for validation
- Interactive org chart manipulation

---

## Execution Order

### Phase 1: Quick Wins (Unblock Testing)
1. **A2** - Documents not showing (likely missing DB insert)
2. **A3** - Questions using old data (likely missing deal_id filter)

### Phase 2: Data Integrity
3. **B1** - Buyer/Target separation (ensure entity filtering works)
4. **B2** - App inventory field normalization (create normalizer)
5. **B3** - Risks vs Gaps classification (update prompts)

### Phase 3: Feature Improvements
6. **C3** - Org chart (CSS tree replacement)
7. **C2** - Inline report editing
8. **C1** - Risk consolidation

---

## Progress Tracking

| ID | Issue | Started | Completed | Notes |
|----|-------|---------|-----------|-------|
| A1 | Apps incomplete | Feb 7 | Feb 7 | Removed invalid param |
| A2 | Documents not showing | | | |
| A3 | Questions old data | | | |
| B1 | Buyer/Target separation | | | |
| B2 | Field normalization | | | |
| B3 | Risks vs Gaps | | | |
| C1 | Risk consolidation | | | |
| C2 | Report editing | | | |
| C3 | Org chart | | | |
