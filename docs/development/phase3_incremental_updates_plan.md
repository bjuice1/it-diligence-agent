# Phase 3: Incremental Updates - 115-Point Plan

*Created: 2026-01-28*
*Updated: 2026-01-28 (v2 - Added improvements)*
*Status: Planning*
*Depends On: Phase 1 (Database), Phase 2 (Deal Management)*

## Overview

Enable adding documents to existing deals and intelligently updating the analysis without losing previous work. Includes document inventory management, smart merge logic, version tracking, "what changed" visibility, and async processing via Celery.

---

## Phase A: Document Inventory & Versioning (Points 1-30)
**Status: Not Started**

### Document Model Enhancements (1-12)
- [ ] 1. Add `content_checksum` calculation on upload (SHA-256 of content)
- [ ] 2. Add `analysis_status` enum: not_analyzed, queued, analyzing, analyzed, stale, error
- [ ] 3. Add `facts_extracted_count` denormalized field
- [ ] 4. Add `last_analyzed_at` timestamp
- [ ] 5. Add `last_analyzed_run_id` FK to analysis_runs
- [ ] 6. Add `error_message` field for failed processing
- [ ] 7. Implement `mark_document_stale(doc_id)` when superseded
- [ ] 8. Implement `get_documents_needing_analysis(deal_id)` query
- [ ] 9. Add document metadata extraction (author, created_date, title from PDF)
- [ ] 10. Track processing time per document for estimates
- [ ] 11. Add `priority` field for processing queue ordering
- [ ] 12. Implement `get_document_version_history(original_doc_id)`

### Document Storage Versioning (13-18)
- [ ] 13. Create versioned storage path pattern: `uploads/{deal_id}/{doc_id}/v{version}/`
- [ ] 14. Keep previous document versions in storage (don't delete)
- [ ] 15. Implement `get_document_file(doc_id, version=None)` - latest by default
- [ ] 16. Add storage cleanup policy (keep last N versions, configurable)
- [ ] 17. Implement `compare_document_versions(doc_id, v1, v2)` text diff
- [ ] 18. Add total storage size tracking per deal

### Document Inventory Page (19-30)
- [ ] 19. Redesign `/documents` page as full document inventory
- [ ] 20. Table columns: filename, entity, status, facts count, version, uploaded, analyzed
- [ ] 21. Status badges with colors (green=analyzed, yellow=stale, red=error, gray=pending)
- [ ] 22. "Upload New Documents" button with drag-drop zone
- [ ] 23. "Replace Document" action per row (uploads new version)
- [ ] 24. "Re-analyze" action to queue single document
- [ ] 25. "View History" action showing all versions
- [ ] 26. Bulk select for batch operations (analyze, delete)
- [ ] 27. Document preview modal (first page thumbnail for PDFs)
- [ ] 28. Filter by: entity, status, domain relevance, date range
- [ ] 29. Sort by: date, name, status, facts count, size
- [ ] 30. Storage usage summary with visual bar

---

## Phase B: Update Analysis Workflow (Points 31-55)
**Status: Not Started**

### Analysis Queue Management (31-40)
- [ ] 31. Create `tasks/document_analysis_task.py` Celery task
- [ ] 32. Implement priority queue for document processing
- [ ] 33. Add `analysis_queue` table (doc_id, priority, queued_at, started_at, status)
- [ ] 34. Implement `queue_document_for_analysis(doc_id, priority=5)`
- [ ] 35. Implement `queue_documents_batch(doc_ids, priority=5)`
- [ ] 36. Add queue position tracking ("3rd in queue, ~5 min wait")
- [ ] 37. Implement queue pause/resume for deal (during conflict resolution)
- [ ] 38. Add retry logic with exponential backoff for failures
- [ ] 39. Set max concurrent analyses per deal (default 2)
- [ ] 40. Add queue monitoring endpoint `/api/queue/status`

### Update Analysis UI (41-50)
- [ ] 41. Create "Update Analysis" modal/page
- [ ] 42. Show documents pending analysis with reasons (new, stale, error retry)
- [ ] 43. Analysis mode selector: "New only", "Include stale", "Full re-analysis"
- [ ] 44. Domain selector for partial domain updates
- [ ] 45. Estimated time display based on queue and history
- [ ] 46. "Preview Changes" dry-run option (analyze but don't apply)
- [ ] 47. Start/Cancel analysis buttons with confirmation
- [ ] 48. Real-time progress display via WebSocket/polling
- [ ] 49. Analysis log stream showing current activity
- [ ] 50. Notification when analysis completes (browser + optional email)

### Incremental Analysis Engine (51-55)
- [ ] 51. Create `services/incremental_analyzer.py`
- [ ] 52. Implement `analyze_documents_incremental(deal_id, doc_ids, domains)`
- [ ] 53. Pass existing facts context to LLM for consistency
- [ ] 54. Generate structured change output (new, updated, removed facts)
- [ ] 55. Create analysis run record with `is_incremental=True`

---

## Phase C: Fact Provenance & History (Points 56-75)
**Status: Not Started**

### Fact Provenance Tracking (56-65)
- [ ] 56. Add `source_document_section` field (section title/header)
- [ ] 57. Add `source_page_numbers` array field
- [ ] 58. Add `source_quote` field (exact text excerpt)
- [ ] 59. Add `extraction_method` enum (llm_extract, manual, import)
- [ ] 60. Add `extraction_confidence` field (0.0-1.0 from LLM)
- [ ] 61. Link facts to specific document version (not just document)
- [ ] 62. Implement `get_fact_source_context(fact_id)` - returns doc excerpt
- [ ] 63. Add "View Source" button on fact detail page
- [ ] 64. Highlight source quote in document preview
- [ ] 65. Track which LLM model extracted each fact

### Fact Version History (66-75)
- [ ] 66. Implement fact versioning via `previous_version_id` chain
- [ ] 67. Create new fact version on update (don't modify in place)
- [ ] 68. Implement `get_fact_history(fact_id)` returning version chain
- [ ] 69. Show fact history timeline on detail page
- [ ] 70. Diff view between fact versions (side-by-side)
- [ ] 71. "Revert to Version" action
- [ ] 72. Track who/what made each change (user, analysis run, import)
- [ ] 73. Add `change_reason` field (analysis update, manual edit, correction)
- [ ] 74. Implement `get_facts_changed_since(deal_id, timestamp)`
- [ ] 75. Add fact change notifications to activity feed

---

## Phase D: Smart Merge Logic (Points 76-95)
**Status: Not Started**

### Change Detection & Classification (76-85)
- [ ] 76. Create `services/fact_merger.py`
- [ ] 77. Implement fact similarity scoring using checksums and fuzzy matching
- [ ] 78. Classify changes: new, update_minor, update_major, conflict, remove
- [ ] 79. Define Tier 1 (auto-apply): New facts, high confidence (>0.9)
- [ ] 80. Define Tier 2 (batch review): Updates, medium confidence (0.7-0.9)
- [ ] 81. Define Tier 3 (manual review): Conflicts, low confidence (<0.7), authority conflicts
- [ ] 82. Detect contradictions between sources (same item, different values)
- [ ] 83. Flag authority level conflicts (interview says X, org chart says Y)
- [ ] 84. Calculate confidence delta (did update improve or reduce confidence?)
- [ ] 85. Generate merge recommendation per change

### Pending Changes Queue (86-92)
- [ ] 86. Implement `create_pending_change(deal_id, change_type, entity, old, new, tier)`
- [ ] 87. Implement `get_pending_changes(deal_id, tier=None, status='pending')`
- [ ] 88. Implement `accept_change(change_id, reviewer_id, note=None)`
- [ ] 89. Implement `reject_change(change_id, reviewer_id, reason)`
- [ ] 90. Implement `defer_change(change_id, defer_until=None)`
- [ ] 91. Implement `bulk_accept_changes(change_ids, reviewer_id)`
- [ ] 92. Auto-expire old pending changes after N days (configurable, default 30)

### Conflict Resolution UI (93-95)
- [ ] 93. Create `/review/conflicts` page for Tier 3 review
- [ ] 94. Side-by-side comparison: current value vs proposed value
- [ ] 95. Show source documents for both sides with highlights

---

## Phase E: What Changed View (Points 96-110)
**Status: Not Started**

### Change Summary Dashboard (96-103)
- [ ] 96. Create "What's New" dashboard widget/page
- [ ] 97. Summary cards: new facts, updated facts, new risks, resolved gaps
- [ ] 98. Filter by: time range, domain, change type, source document
- [ ] 99. Highlight high-impact changes (critical risks, major updates)
- [ ] 100. "Changes since last review" quick filter
- [ ] 101. Compare between any two analysis runs
- [ ] 102. Export change summary as PDF/Markdown report
- [ ] 103. Email digest option for changes (daily/weekly)

### Inline Change Indicators (104-110)
- [ ] 104. Add `[NEW]` badge to new items in all list views
- [ ] 105. Add `[UPDATED]` badge to changed items
- [ ] 106. Add `[STALE]` badge to facts from superseded documents
- [ ] 107. Inline diff highlighting (additions green, removals red)
- [ ] 108. "Show only changes" toggle on list pages
- [ ] 109. "Mark all as reviewed" bulk action
- [ ] 110. Clear badges after explicit review acknowledgment

---

## Phase F: Rollback & Recovery (Points 111-115)
**Status: Not Started**

### Analysis Run Snapshots (111-113)
- [ ] 111. Store full state snapshot with each analysis run (facts, findings as JSON)
- [ ] 112. Implement `get_snapshot(run_id)` to retrieve historical state
- [ ] 113. "View as of Run #N" mode showing historical data

### Rollback Capability (114-115)
- [ ] 114. Implement `rollback_to_run(deal_id, run_id)` creating new run from snapshot
- [ ] 115. Add rollback confirmation with impact preview (what will change)

---

## File Changes Summary

### New Files
| File | Purpose |
|------|---------|
| `services/incremental_analyzer.py` | Incremental analysis logic |
| `services/fact_merger.py` | Smart merge logic |
| `tasks/document_analysis_task.py` | Celery task for doc analysis |
| `database/models/analysis_queue.py` | Queue model |
| `web/templates/documents/inventory.html` | Document inventory page |
| `web/templates/analysis/update.html` | Update analysis page |
| `web/templates/analysis/whats_new.html` | What changed view |
| `web/templates/review/conflicts.html` | Conflict resolution |
| `web/templates/components/diff_view.html` | Diff component |
| `web/templates/components/change_badge.html` | NEW/UPDATED badges |

### Modified Files
| File | Changes |
|------|---------|
| `database/models/document.py` | Add versioning, status fields |
| `database/models/fact.py` | Add provenance, history fields |
| `database/models/analysis_run.py` | Add snapshot storage |
| `web/app.py` | New routes, queue endpoints |
| `web/templates/base.html` | Add change notification indicator |
| `agents/` | Update for incremental mode |

---

## UI Mockups

### Document Inventory
```
┌─────────────────────────────────────────────────────────────────┐
│  Document Inventory            [Upload New ▼] [Update Analysis] │
│  12 documents │ 2 pending │ 1 stale │ 234 facts │ 45 MB used   │
├─────────────────────────────────────────────────────────────────┤
│  Filter: [All Entities ▼] [All Status ▼]    Search: [________] │
├─────────────────────────────────────────────────────────────────┤
│  □ │ Document               │ Entity │ Status     │Facts│ Ver │
│  ──┼────────────────────────┼────────┼────────────┼─────┼─────│
│  □ │ IT_Org_Chart.pdf       │ Target │ ✓ Analyzed │  45 │ v2  │
│  □ │ App_Inventory.xlsx     │ Target │ ✓ Analyzed │  78 │ v1  │
│  □ │ Network_Diagram.pdf    │ Target │ ⚠ Stale    │  23 │ v1  │
│  □ │ Security_Policy.docx   │ Target │ ○ Queued   │   - │ v1  │
│  □ │ Interview_CIO.pdf      │ Target │ ○ Pending  │   - │ v1  │
│  □ │ Budget_2025.xlsx       │ Target │ ✗ Error    │   - │ v1  │
├─────────────────────────────────────────────────────────────────┤
│  Selected: 0   [Analyze Selected] [Delete Selected]             │
└─────────────────────────────────────────────────────────────────┘
```

### Update Analysis Modal
```
┌─────────────────────────────────────────────────────────────────┐
│  Update Analysis                                           [X]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Documents to process:                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ☑ Security_Policy.docx (new)                            │   │
│  │ ☑ Interview_CIO.pdf (new)                               │   │
│  │ ☐ Network_Diagram.pdf (stale - v1 superseded)           │   │
│  │ ☐ Budget_2025.xlsx (error - retry)                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Analysis Mode:                                                 │
│  ◉ Analyze selected documents only (2 docs)                    │
│  ○ Include stale documents (3 docs)                            │
│  ○ Full re-analysis - all documents (6 docs)                   │
│                                                                 │
│  Domains:                                                       │
│  [✓] All  [✓] Apps  [✓] Infra  [✓] Cyber  [✓] Org  [ ] Network │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ℹ Estimated: ~4 minutes based on 2 documents            │   │
│  │   Queue position: Next (no wait)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ☐ Preview changes only (don't apply)                          │
│                                                                 │
│                         [Cancel]  [Start Analysis]              │
└─────────────────────────────────────────────────────────────────┘
```

### What's New Summary
```
┌─────────────────────────────────────────────────────────────────┐
│  What's New                    Since: [Last Review ▼] [Export]  │
│  Analysis Run #5 completed Jan 28, 2026 at 2:34 PM              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │ 📊 FACTS                 │  │ ⚠️ RISKS                  │    │
│  │ ─────────────────────    │  │ ─────────────────────    │    │
│  │ +12 new facts            │  │ +2 new risks             │    │
│  │   • 5 cybersecurity      │  │   • R-CYBER-004 (High)   │    │
│  │   • 4 organization       │  │   • R-ORG-007 (Medium)   │    │
│  │   • 3 applications       │  │                          │    │
│  │                          │  │ ~1 severity changed      │    │
│  │ ~3 facts updated         │  │   • R-INFRA-002 Med→Low  │    │
│  │ -1 fact removed (stale)  │  │                          │    │
│  │                          │  │ ✓1 risk resolved         │    │
│  │ [View All Facts →]       │  │ [View All Risks →]       │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 🔍 PENDING REVIEW (3 items)                              │  │
│  │ ──────────────────────────────────────────────────────── │  │
│  │ • 2 Tier 2 changes need batch review                     │  │
│  │ • 1 Tier 3 conflict needs individual review              │  │
│  │                                                          │  │
│  │ [Review Tier 2 Batch →]  [Review Conflicts →]            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [Mark All as Reviewed]                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Conflict Resolution
```
┌─────────────────────────────────────────────────────────────────┐
│  Resolve Conflict: F-ORG-023                              [X]  │
│  Domain: Organization │ Category: Staffing                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │ CURRENT VALUE           │  │ PROPOSED UPDATE             │  │
│  │ ─────────────────────── │  │ ─────────────────────────── │  │
│  │ IT Department has       │  │ IT Department has           │  │
│  │ [15 FTE employees]      │  │ [18 FTE employees]          │  │
│  │                         │  │                             │  │
│  │ Source: IT_Org_Chart.pdf│  │ Source: Interview_CIO.pdf   │  │
│  │ Page: 3                 │  │ Page: 7                     │  │
│  │ Confidence: 0.85        │  │ Confidence: 0.92            │  │
│  │ Authority: Level 2      │  │ Authority: Level 3          │  │
│  │ [View Source]           │  │ [View Source]               │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
│                                                                 │
│  Resolution:                                                    │
│  ◉ Accept proposed (higher authority source)                   │
│  ○ Keep current                                                │
│  ○ Merge: Use proposed value, keep current as note             │
│  ○ Flag for VDR request (need clarification)                   │
│                                                                 │
│  Note: [CIO interview is more recent, updating headcount____]  │
│                                                                 │
│                           [Skip]  [Resolve & Next]              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Merge Tier Definitions

| Tier | Criteria | Action | Examples |
|------|----------|--------|----------|
| **Tier 1** | Confidence >0.9, no conflicts, new fact | Auto-apply | New app from inventory doc |
| **Tier 2** | Confidence 0.7-0.9, minor update, same source | Batch review | Updated version number |
| **Tier 3** | Confidence <0.7, conflict, authority mismatch | Manual review | Contradicting headcounts |

---

## Progress Summary

| Phase | Points | Complete | Status |
|-------|--------|----------|--------|
| A: Document Inventory & Versioning | 1-30 | 0/30 | Not Started |
| B: Update Analysis Workflow | 31-55 | 0/25 | Not Started |
| C: Fact Provenance & History | 56-75 | 0/20 | Not Started |
| D: Smart Merge Logic | 76-95 | 0/20 | Not Started |
| E: What Changed View | 96-110 | 0/15 | Not Started |
| F: Rollback & Recovery | 111-115 | 0/5 | Not Started |

**Overall: 0/115 points complete (0%)**

---

## Success Criteria

Phase 3 is complete when:
1. Document inventory shows all documents with version history
2. Users can upload new documents and replace existing ones
3. Incremental analysis processes only new/changed documents
4. Facts track their source document, page, and quote
5. Smart merge categorizes changes into tiers
6. Tier 1 changes auto-apply, Tier 2/3 queue for review
7. "What's New" clearly shows all changes since last review
8. Can rollback to any previous analysis run
9. Full audit trail of all changes

---

## Notes

- Document versioning keeps all versions in storage (configurable retention)
- Fact checksums enable fast diff without full text comparison
- Analysis queue uses Celery (from Phase 2) for background processing
- Provenance tracking enables "View Source" from any fact
- Snapshot storage allows point-in-time recovery
- Change badges persist until explicitly marked as reviewed
