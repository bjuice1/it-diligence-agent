# Audit Plans Index

## Overview

This directory contains detailed audit plans for each known issue in the IT Diligence Agent system. Each audit has been reviewed with GPT for architectural correctness and operational realism.

---

## Review Scores (GPT, Feb 8 2026)

| Audit | Issue | Score | Status | Tier |
|-------|-------|-------|--------|------|
| A1 | Target apps incomplete | N/A | **FIXED** | - |
| A2 | Documents not showing | 8.5/10 | **IMPLEMENTED** | Tier 1 |
| A3 | Questions stale data | 8.5/10 | **IMPLEMENTED** | Tier 1 |
| B1 | Buyer/Target separation | 8.0/10 | **PARTIAL** | Tier 2 |
| B2 | Field normalization | 8.2/10 | **ENHANCED** | Tier 2 |
| B3 | Risks vs Gaps | 8.7/10 | **PARTIAL** | Tier 2 |
| C1 | Risk consolidation | 8.4/10 | **PARTIAL** | Tier 3* |
| C2 | Inline report editing | 8.5/10 | **IMPLEMENTED** | Tier 3 |
| C3 | Org chart CSS tree | 8.6/10 | **PARTIAL** | Tier 2* |

*C1 and C3 become Tier 1/2 if client-facing

---

## Recommended Build Order

### Phase 1: Unblock Testing (Quick Wins)
1. **A2** - Documents not showing (8.5/10)
   - Decision: DB is source of truth
   - Key: Add DB insert to upload, backfill existing
2. **A3** - Questions stale data (pending review)
   - Likely: Add deal_id filter to query

### Phase 2: Data Integrity
3. **B1** - Buyer/Target separation (8.0/10)
   - Decision: Default target-only, entity NOT NULL
   - Key: Add filters to all queries, backfill entities
4. **B2** - Field normalization (8.2/10)
   - Decision: Normalize at ingestion, merge stores
   - Key: Create normalizer, define canonical schema
5. **B3** - Risks vs Gaps (8.7/10)
   - Decision: Three categories (Gap/Observation/Risk)
   - Key: Require evidence for risks

### Phase 3: Polish (Partner-Facing)
6. **C3** - Org chart (8.6/10)
   - Decision: CSS tree, single renderer
   - Key: Multi-root handling, cycle detection
7. **C1** - Risk consolidation (8.4/10)
   - Decision: Graph clustering, evidence provenance
   - Key: Post-classification only, domain-first
8. **C2** - Report editing (pending review)
   - Key: ReportOverride model, persist edits

---

## Key Decisions Made

### Data Architecture
| Topic | Decision |
|-------|----------|
| Document source of truth | Database (not manifest) |
| Entity default | `target` (buyer via toggle) |
| Field normalization timing | At ingestion (not display) |
| Risk evidence | Required (non-empty evidence_facts) |
| Consolidation timing | Storage-time (with display toggle) |

### Classification Model
| Category | Definition | Action |
|----------|------------|--------|
| Gap | Missing data | Ask seller |
| Observation | Uncertain concern | Investigate |
| Risk | Confirmed issue | Mitigate |

### Org Chart
| Topic | Decision |
|-------|----------|
| Renderer | Single shared module (all codepaths) |
| Multi-root | Synthetic parent |
| Cycles | Cut edge, mark, continue |
| Large trees | Depth-limit to 3 |

---

## Files by Audit

### Tier 1 (Quick Wins)
- `A2_documents_not_showing.md` - 6.6KB, updated with GPT feedback
- `A3_questions_stale_data.md` - 4.9KB, pending GPT review

### Tier 2 (Data Integrity)
- `B1_buyer_target_separation.md` - 9KB, updated with GPT feedback
- `B2_field_normalization.md` - 14KB, updated with GPT feedback
- `B3_risks_vs_gaps.md` - 12KB, updated with GPT feedback

### Tier 3 (Features)
- `C1_risk_consolidation.md` - 13KB, updated with GPT feedback
- `C2_inline_report_editing.md` - 12KB, pending GPT review
- `C3_org_chart_css_tree.md` - 14KB, updated with GPT feedback

---

## Workflow

For each audit:

1. **Review Plan** - Read the .md file thoroughly
2. **External Input** - Get GPT/expert review on considerations ✓
3. **Refine Plan** - Update based on feedback ✓
4. **Execute** - Follow the step-by-step audit process
5. **Verify** - Check all success criteria
6. **Document** - Update status and notes

---

## Already Fixed

| Issue | Fixed Date | Notes |
|-------|------------|-------|
| A1: Target apps incomplete | Feb 7, 2026 | Removed invalid `extraction_method` param |
| A2: Documents not showing | Feb 8, 2026 | Added DB insert to upload route, updated /documents to query DB, added backfill endpoint |
| A3: Questions stale data | Feb 8, 2026 | Added deal_id to question filenames, filtered loading by current deal |
| B1: Buyer/Target separation | Feb 8, 2026 | Fixed /facts route to default to entity='target' (partial - domain routes already correct) |
| B2: Field normalization | Feb 8, 2026 | Enhanced field_normalizer.py with type coercion (int, float, date), logging unrecognized categories |
| B3: Risks vs Gaps | Feb 8, 2026 | Created classification_validator.py with gap/observation indicators, evidence checking |
| C1: Risk consolidation | Feb 8, 2026 | Created risk_consolidation.py with graph clustering, ConsolidatedRisk model (partial - UI/pipeline integration remaining) |
| C2: Inline report editing | Feb 8, 2026 | Full implementation in pe_reports.py - save endpoints, override helpers, JS/CSS injection for editing UI |
| C3: Org chart CSS tree | Feb 8, 2026 | Created tools_v2/org_chart.py with tree builder + renderer (partial - web view integration remaining) |
