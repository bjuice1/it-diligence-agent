# IT Due Diligence System: Implementation Plan

**Version:** 1.0
**Date:** 2026-01-26
**Reference:** ARCHITECTURE_APPROACH.md

---

## Overview

This plan implements the architecture defined in ARCHITECTURE_APPROACH.md across 10 development phases. Each phase is designed to be completed in one focused session and builds on previous phases.

**Total Phases:** 10
**Steps per Phase:** 10-15
**Estimated Total Steps:** ~120

---

## Phase Dependencies

```
Phase 1 (Document Layer) ──────┐
                               │
Phase 2 (Entity Separation) ───┼──► Phase 5 (Citation Validation)
                               │           │
Phase 3 (Fact Store) ──────────┘           │
                                           ▼
Phase 4 (Extraction Rules) ──────► Phase 6 (Discovery Logging)
                                           │
                                           ▼
                               Phase 7 (Confirmation Backend)
                                           │
                                           ▼
                               Phase 8 (Confirmation UI)
                                           │
                                           ▼
                               Phase 9 (Evidence Chain)
                                           │
                                           ▼
                               Phase 10 (Analysis Layer)
```

---

## Phase 1: Document Layer Foundation

**Status: COMPLETE** (2026-01-26)

**Goal:** Create the document registry and storage infrastructure that serves as the audit anchor.

**Files Created/Modified:**
- `tools_v2/document_store.py` (NEW) - 450+ lines
- `config_v2.py` - Added document paths
- `utils/file_hasher.py` (NEW) - SHA-256 hashing
- `utils/__init__.py` (NEW) - Package init
- `tests/test_document_store.py` (NEW) - 26 tests

### Steps (All Complete)

| # | Task | Status |
|---|------|--------|
| 1.1 | Create file hasher utility | DONE |
| 1.2 | Define Document dataclass | DONE |
| 1.3 | Create DocumentStore class | DONE |
| 1.4 | Implement hash-based duplicate detection | DONE |
| 1.5 | Define storage directory structure | DONE |
| 1.6 | Implement raw file storage | DONE |
| 1.7 | Implement text extraction hook | DONE |
| 1.8 | Add page number preservation | DONE |
| 1.9 | Create document manifest | DONE |
| 1.10 | Add document status tracking | DONE |
| 1.11 | Implement `get_documents_for_entity()` | DONE |
| 1.12 | Add authority level helpers | DONE |
| 1.13 | Write document store tests | DONE (26 tests, all passing) |
| 1.14 | Integrate with config | DONE |

### Deliverables (Complete)
- [x] `utils/file_hasher.py` with SHA-256 computation
- [x] `tools_v2/document_store.py` with DocumentStore class
- [x] Updated `config_v2.py` with document paths
- [x] `tests/test_document_store.py`
- [x] Document storage directory structure

---

## Phase 2: Entity Separation

**Status: COMPLETE** (2026-01-26)

**Goal:** Implement separate upload paths for target and buyer documents, eliminating entity inference.

**Files Modified:**
- `web/app.py` - Updated process_upload, added entity_summary endpoint, dashboard entity display
- `web/templates/upload.html` - Dual upload zones with authority selection
- `web/templates/dashboard.html` - Entity summary display
- `tools_v2/discovery_tools.py` - Entity validation (no silent defaults)

### Steps (All Complete)

| # | Task | Status |
|---|------|--------|
| 2.1 | Create dual upload UI | DONE |
| 2.2 | Add entity parameter to upload endpoint | DONE |
| 2.3 | Validate entity on upload | DONE |
| 2.4 | Route files to entity directories | DONE |
| 2.5 | Add authority level selection | DONE |
| 2.6 | Store authority level with document | DONE |
| 2.7 | Update document manifest with entity | DONE |
| 2.8 | Modify discovery agent to receive entity | DONE (via DocumentStore) |
| 2.9 | Remove entity inference from discovery | DONE (returns error now) |
| 2.10 | Update fact creation to require entity | DONE |
| 2.11 | Add entity display in dashboard | DONE |
| 2.12 | Create entity summary endpoint | DONE |
| 2.13 | Add entity filter to fact views | PARTIAL (API ready, UI filter pending) |
| 2.14 | Test mixed upload scenario | Ready for testing |

### Deliverables (Complete)
- [x] Dual upload interface in web UI
- [x] Entity validation (no defaults, errors on missing)
- [x] Entity summary in dashboard
- [x] Entity correctly flows from upload → document → fact

---

## Phase 3: Fact Store Enhancements

**Goal:** Add confirmation tracking, correction history, and proper timestamps to the fact store.

**Files to Create/Modify:**
- `tools_v2/fact_store.py`
- `tools_v2/discovery_tools.py`

### Steps

| # | Task | Details | Validation |
|---|------|---------|------------|
| 3.1 | Add confirmation status enum | `ConfirmationStatus`: `provisional`, `confirmed`, `corrected`, `rejected` | Enum defined and usable |
| 3.2 | Add confirmation fields to Fact | `confirmation_status`, `confirmed_by`, `confirmed_at`, `correction_notes` | Fields on Fact dataclass |
| 3.3 | Add doc_id field to Fact | Link fact to source document by doc_id (not just filename) | Field added, populated |
| 3.4 | Add quote_location field | Store page number / section reference for quote | Field stores location |
| 3.5 | Add extraction metadata | `extraction_model`, `extraction_run_id`, `extraction_timestamp` | Metadata captured |
| 3.6 | Implement `updated_at` timestamp | Auto-update on any fact modification | Timestamp changes on edit |
| 3.7 | Create correction history | When fact corrected, store `{original_value, new_value, changed_by, changed_at, field_name}` | History preserved |
| 3.8 | Add `confirm_fact()` method | Sets status to confirmed, records confirmer and timestamp | Method works correctly |
| 3.9 | Add `correct_fact()` method | Updates values, sets status to corrected, preserves original, records change | Correction tracked |
| 3.10 | Add `reject_fact()` method | Sets status to rejected with reason, excludes from active queries | Rejected facts excluded |
| 3.11 | Add review priority field | `review_priority`: `high`, `medium`, `low` based on confidence and category | Priority calculated |
| 3.12 | Implement priority calculation | Low confidence → high priority. Security/compliance → high priority. | Priority logic correct |
| 3.13 | Add `get_facts_for_review()` | Returns facts filtered by status=provisional, sorted by priority | Returns correct order |
| 3.14 | Update serialization | JSON save/load includes all new fields | Persistence works |
| 3.15 | Migrate existing facts | Script to add default values to existing facts (status=provisional, etc.) | Old data compatible |

### Deliverables
- [ ] Confirmation status tracking on facts
- [ ] Correction history preservation
- [ ] Review priority calculation
- [ ] `confirm_fact()`, `correct_fact()`, `reject_fact()` methods
- [ ] Migration script for existing data

---

## Phase 4: Extraction Rules Enforcement

**Goal:** Enforce "no inference" rule and improve extraction completeness validation.

**Files to Create/Modify:**
- `prompts/v2_*_discovery_prompt.py` (all domain prompts)
- `tools_v2/discovery_tools.py`
- `tools_v2/extraction_validator.py` (NEW)

### Steps

| # | Task | Details | Validation |
|---|------|---------|------------|
| 4.1 | Create extraction validator module | `extraction_validator.py` with validation functions | Module created |
| 4.2 | Define inference detection patterns | Patterns indicating inference: "likely", "probably", "appears to", "suggests", "implies" | Patterns defined |
| 4.3 | Implement `detect_inference()` | Check fact details and quote for inference language | Detects inference words |
| 4.4 | Add inference flag to fact | `is_inferred: bool` field, auto-set if inference detected | Flag set correctly |
| 4.5 | Route inferred items to gaps | If inference detected, create gap instead of fact, or flag for review | Inferred → gap/flag |
| 4.6 | Update prompts: no inference rule | Add explicit instruction to all prompts: "Do NOT infer. Only extract explicit statements." | Prompts updated |
| 4.7 | Update prompts: quote requirement | Strengthen: "Every fact MUST have an exact quote. If you cannot quote it, do not extract it." | Prompts updated |
| 4.8 | Add minimum quote length check | Quotes < 10 characters flagged as potentially insufficient | Short quotes flagged |
| 4.9 | Implement completeness scoring | Score based on: has quote, has details, has source location | Score calculated |
| 4.10 | Add extraction quality metrics | Track per-run: facts extracted, facts flagged, inference detected count | Metrics captured |
| 4.11 | Create gap from weak evidence | If evidence too weak for fact, auto-create gap: "Need confirmation: [item]" | Gaps created |
| 4.12 | Update validation in tool execution | In `execute_discovery_tool()`: run validation, flag/reject as needed | Validation runs |
| 4.13 | Add validation summary to logs | Audit log includes validation results: accepted, flagged, rejected counts | Summary in logs |
| 4.14 | Test with known inference examples | Create test cases with inference language, verify detection | Tests pass |

### Deliverables
- [ ] `extraction_validator.py` with inference detection
- [ ] Updated prompts with no-inference rule
- [ ] Automatic gap creation for weak evidence
- [ ] Validation summary in audit logs

---

## Phase 5: Citation Validation

**Goal:** Make citation validation strict and fail-fast. Findings must cite real facts.

**Files to Create/Modify:**
- `tools_v2/reasoning_tools.py`
- `config_v2.py`
- `agents_v2/reasoning_agent.py`

### Steps

| # | Task | Details | Validation |
|---|------|---------|------------|
| 5.1 | Set citation validation ON by default | In `config_v2.py`: `ENABLE_CITATION_VALIDATION = True` | Default is True |
| 5.2 | Make FactStore required for reasoning | If FactStore is None, raise error immediately, don't proceed | Error on missing store |
| 5.3 | Implement strict citation check | `validate_citations()`: all cited fact IDs must exist in FactStore | Invalid IDs detected |
| 5.4 | Add citation validation to finding creation | Before creating finding, validate all `based_on_facts` | Validation runs |
| 5.5 | Fail on invalid citations | If any cited fact doesn't exist, reject the finding with clear error | Finding rejected |
| 5.6 | Add warning for rejected fact citations | If finding cites a rejected fact, warn but allow (flag for review) | Warning logged |
| 5.7 | Track citation validation results | Per-finding: `citation_validation: {valid: [], invalid: [], rejected: []}` | Results tracked |
| 5.8 | Add validation rate metric | Percentage of findings with 100% valid citations | Metric calculated |
| 5.9 | Create citation report | Summary: findings by citation validity, invalid citations list | Report generated |
| 5.10 | Update reasoning prompts | Instruct LLM: "Only cite fact IDs that exist. Invalid citations will be rejected." | Prompts updated |
| 5.11 | Add fact existence check tool | Give reasoning agent tool to verify fact exists before citing | Tool available |
| 5.12 | Test invalid citation handling | Create finding with fake fact ID, verify rejection | Rejection works |
| 5.13 | Test rejected fact citation | Cite rejected fact, verify warning and flag | Warning generated |

### Deliverables
- [ ] Citation validation ON by default
- [ ] Strict validation (invalid = rejection)
- [ ] Citation validation results tracked
- [ ] Reasoning prompts updated

---

## Phase 6: Discovery Logging Enhancement

**Goal:** Complete audit trail for discovery including LLM call context and validation results.

**Files to Create/Modify:**
- `tools_v2/discovery_logger.py`
- `agents_v2/base_discovery_agent.py`
- `tools_v2/llm_call_logger.py` (NEW)

### Steps

| # | Task | Details | Validation |
|---|------|---------|------------|
| 6.1 | Create LLM call logger | `llm_call_logger.py`: captures model, temperature, tokens, prompt hash, response summary | Module created |
| 6.2 | Add call context to log entry | For each API call: model, temperature, input tokens, output tokens, call duration | Context captured |
| 6.3 | Log prompt version/hash | Hash the system prompt, store for reproducibility tracking | Prompt hash stored |
| 6.4 | Add iteration context | Each tool call knows which iteration and which API call it came from | Context linked |
| 6.5 | Log full facts text shown to LLM | When reasoning uses facts, log which facts were in context | Facts in context logged |
| 6.6 | Add validation results to log | For each fact: validation status (accepted/flagged/rejected) and reason | Validation in log |
| 6.7 | Create structured JSON log | In addition to .md, create .json with machine-readable log | JSON log created |
| 6.8 | Add session ID to logs | Unique session ID links all logs from one analysis run | Session ID present |
| 6.9 | Implement log aggregation | Combine all domain logs into single session log | Aggregation works |
| 6.10 | Add timing breakdown | Per-iteration: API call time, tool execution time, total time | Timing in logs |
| 6.11 | Create log viewer endpoint | `/api/logs/{session_id}` returns log data | Endpoint works |
| 6.12 | Add log summary to dashboard | Show recent runs with key metrics: facts, gaps, cost, duration | Summary visible |
| 6.13 | Implement log retention policy | Config: keep logs for N days, auto-cleanup older | Cleanup works |
| 6.14 | Test log completeness | Run discovery, verify all expected data in log | Log complete |

### Deliverables
- [ ] LLM call context in logs
- [ ] Structured JSON logs
- [ ] Session-level log aggregation
- [ ] Log viewer in dashboard

---

## Phase 7: Confirmation Workflow Backend

**Goal:** Implement backend APIs and logic for fact confirmation workflow.

**Files to Create/Modify:**
- `web/app.py`
- `tools_v2/fact_store.py`
- `tools_v2/confirmation_workflow.py` (NEW)

### Steps

| # | Task | Details | Validation |
|---|------|---------|------------|
| 7.1 | Create confirmation workflow module | `confirmation_workflow.py` with workflow logic | Module created |
| 7.2 | Implement review queue | `get_review_queue(priority, entity, domain)` returns ordered facts for review | Queue returns facts |
| 7.3 | Add queue statistics | Count by: priority, entity, domain, status | Stats calculated |
| 7.4 | Create `/api/review-queue` endpoint | Returns paginated review queue with filters | Endpoint works |
| 7.5 | Create `/api/fact/{id}/confirm` endpoint | POST: marks fact as confirmed | Endpoint works |
| 7.6 | Create `/api/fact/{id}/correct` endpoint | POST: applies correction, preserves history | Endpoint works |
| 7.7 | Create `/api/fact/{id}/reject` endpoint | POST: marks as rejected with reason | Endpoint works |
| 7.8 | Add bulk confirmation | `/api/facts/bulk-confirm` for multiple facts | Bulk works |
| 7.9 | Add confirmation statistics | `/api/confirmation-stats`: confirmed, pending, rejected counts | Stats correct |
| 7.10 | Implement reviewer assignment | Optional: assign facts to specific reviewers | Assignment works |
| 7.11 | Add confirmation deadline tracking | Optional: flag facts pending > N days | Deadline flagging |
| 7.12 | Create confirmation audit log | Log all confirmation actions: who, when, what | Audit log created |
| 7.13 | Add undo capability | Allow reverting confirmation within time window | Undo works |
| 7.14 | Test workflow end-to-end | Fact → review → confirm/correct/reject → verify state | Workflow complete |

### Deliverables
- [ ] Review queue API
- [ ] Confirm/correct/reject endpoints
- [ ] Bulk confirmation
- [ ] Confirmation audit log

---

## Phase 8: Confirmation UI

**Goal:** Build user interface for fact review and confirmation.

**Files to Create/Modify:**
- `web/templates/review.html` (NEW)
- `web/templates/fact_detail.html` (NEW)
- `web/static/js/review.js` (NEW)
- `web/app.py`

### Steps

| # | Task | Details | Validation |
|---|------|---------|------------|
| 8.1 | Create review queue page | `/review` route showing facts pending review | Page loads |
| 8.2 | Add priority tabs | Tabs: "High Priority", "Medium", "Low" filtering queue | Tabs filter correctly |
| 8.3 | Add entity filter | Filter by Target/Buyer in review queue | Filter works |
| 8.4 | Add domain filter | Filter by domain (applications, infrastructure, etc.) | Filter works |
| 8.5 | Create fact detail view | Click fact → see full details, quote, source document link | Detail view works |
| 8.6 | Add document viewer | Embedded viewer or link to open source document | Document accessible |
| 8.7 | Create confirmation buttons | "Confirm", "Correct", "Reject" buttons with appropriate forms | Buttons work |
| 8.8 | Build correction form | Form to edit fact values with diff preview | Form shows changes |
| 8.9 | Add rejection reason input | Required text field when rejecting | Reason captured |
| 8.10 | Show confirmation history | Display who confirmed/corrected and when | History visible |
| 8.11 | Add keyboard shortcuts | Enter=confirm, E=edit, R=reject for power users | Shortcuts work |
| 8.12 | Create progress indicator | "Reviewed X of Y facts (Z%)" | Progress shown |
| 8.13 | Add bulk selection | Checkbox to select multiple, bulk confirm | Bulk works in UI |
| 8.14 | Mobile-friendly layout | Responsive design for tablet use | Works on tablet |
| 8.15 | Test with offshore workflow | Simulate offshore team reviewing low-priority facts | Workflow smooth |

### Deliverables
- [ ] Review queue page
- [ ] Fact detail view with document link
- [ ] Confirmation/correction/rejection UI
- [ ] Progress tracking
- [ ] Keyboard shortcuts

---

## Phase 9: Evidence Chain & Queries

**Goal:** Implement bidirectional traceability and quote verification.

**Files to Create/Modify:**
- `tools_v2/evidence_chain.py` (NEW)
- `tools_v2/quote_verifier.py` (NEW)
- `tools_v2/fact_store.py`
- `web/app.py`

### Steps

| # | Task | Details | Validation |
|---|------|---------|------------|
| 9.1 | Create evidence chain module | `evidence_chain.py` for traceability queries | Module created |
| 9.2 | Implement forward trace | `trace_finding_to_sources(finding_id)` → facts → documents → quotes | Trace works |
| 9.3 | Implement backward trace | `find_dependent_findings(fact_id)` → all findings citing this fact | Trace works |
| 9.4 | Add document-to-facts query | `get_facts_from_document(doc_id)` → all facts from document | Query works |
| 9.5 | Create quote verifier module | `quote_verifier.py` for matching quotes to documents | Module created |
| 9.6 | Implement fuzzy quote matching | Use similarity threshold (0.8+) to handle OCR errors, minor variations | Fuzzy match works |
| 9.7 | Add quote verification status | `quote_verified`: `exact_match`, `fuzzy_match`, `not_found`, `not_applicable` | Status tracked |
| 9.8 | Run verification on fact creation | After extraction, verify quote exists in source document | Verification runs |
| 9.9 | Flag unverified quotes | Quotes not found → fact flagged for review | Flagging works |
| 9.10 | Create evidence chain API | `/api/evidence-chain/{finding_id}` returns full trace | API works |
| 9.11 | Create impact analysis API | `/api/fact/{id}/impact` returns what breaks if fact rejected | API works |
| 9.12 | Add evidence chain visualization | UI showing finding → facts → documents tree | Visual works |
| 9.13 | Implement quote highlight | When viewing document, highlight the quoted section | Highlight works |
| 9.14 | Test chain integrity | Create finding, trace to document, verify complete chain | Chain complete |

### Deliverables
- [ ] Forward and backward traceability
- [ ] Quote verification with fuzzy matching
- [ ] Evidence chain API
- [ ] Impact analysis for fact changes
- [ ] Evidence chain visualization

---

## Phase 10: Analysis Layer Updates

**Goal:** Implement draft status, dependency propagation, and analysis re-runs.

**Files to Create/Modify:**
- `tools_v2/reasoning_tools.py`
- `agents_v2/reasoning_agent.py`
- `tools_v2/analysis_status.py` (NEW)
- `web/templates/findings.html`

### Steps

| # | Task | Details | Validation |
|---|------|---------|------------|
| 10.1 | Create analysis status module | `analysis_status.py` for status calculation and propagation | Module created |
| 10.2 | Define analysis status enum | `AnalysisStatus`: `draft`, `partially_confirmed`, `confirmed`, `needs_review` | Enum defined |
| 10.3 | Calculate finding status | Based on cited facts: all confirmed → confirmed, any provisional → draft | Calculation correct |
| 10.4 | Add status to Finding | `analysis_status` field, auto-calculated | Field populated |
| 10.5 | Implement status propagation | When fact status changes, recalculate dependent findings | Propagation works |
| 10.6 | Create dependency graph | Track fact → finding dependencies for propagation | Graph maintained |
| 10.7 | Add "DRAFT" watermark | UI shows "DRAFT - Based on Unconfirmed Facts" prominently | Watermark visible |
| 10.8 | Add confirmation progress | "Based on X confirmed, Y provisional facts" per finding | Progress shown |
| 10.9 | Flag findings with rejected facts | If finding cites rejected fact → status = needs_review | Flagging works |
| 10.10 | Implement partial re-analysis | Re-run reasoning only for findings affected by fact changes | Re-run scoped |
| 10.11 | Add analysis version tracking | Track analysis run ID, allow comparison between versions | Versioning works |
| 10.12 | Create confirmation summary report | Export: all findings with confirmation status, citation details | Report generated |
| 10.13 | Add status filter to findings view | Filter by: Draft, Confirmed, Needs Review | Filter works |
| 10.14 | Test propagation end-to-end | Confirm fact → finding status updates, reject fact → finding flagged | Propagation works |
| 10.15 | Final integration test | Full workflow: upload → extract → review → confirm → analyze → report | All works together |

### Deliverables
- [ ] Analysis status calculation
- [ ] Dependency propagation
- [ ] Draft watermark in UI
- [ ] Findings with rejected facts flagged
- [ ] Full integration working

---

## Testing Strategy

### Per-Phase Testing

Each phase includes:
1. **Unit tests** for new functions/methods
2. **Integration test** verifying phase deliverables
3. **Manual QA** of any UI changes

### End-to-End Test Scenarios

After all phases:

| Scenario | Description |
|----------|-------------|
| Happy path | Upload → Extract → Review → Confirm all → Generate report |
| Correction flow | Extract fact with error → Correct → Verify history preserved |
| Rejection flow | Extract bad fact → Reject → Verify excluded from analysis |
| Mixed entity | Upload target and buyer docs → Verify correct attribution |
| Evidence trace | Pick any finding → Trace to source document and quote |
| Status propagation | Reject fact → Verify dependent findings flagged |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing functionality | Run existing tests after each phase |
| Data migration issues | Create backup before migration, test with copy |
| Performance degradation | Profile after phases 3, 7, 9 (heavy changes) |
| UI/UX confusion | Get user feedback after phases 2, 8 |

---

## Phase Checklist

Use this to track progress:

- [x] **Phase 1:** Document Layer Foundation (COMPLETE - 2026-01-26)
- [x] **Phase 2:** Entity Separation (COMPLETE - 2026-01-26)
- [ ] **Phase 3:** Fact Store Enhancements
- [ ] **Phase 4:** Extraction Rules Enforcement
- [ ] **Phase 5:** Citation Validation
- [ ] **Phase 6:** Discovery Logging Enhancement
- [ ] **Phase 7:** Confirmation Workflow Backend
- [ ] **Phase 8:** Confirmation UI
- [ ] **Phase 9:** Evidence Chain & Queries
- [ ] **Phase 10:** Analysis Layer Updates

---

## Next Steps

1. Review this plan
2. Confirm phase order and scope
3. Begin Phase 1: Document Layer Foundation

---

*Plan created 2026-01-26. Reference ARCHITECTURE_APPROACH.md for design rationale.*
