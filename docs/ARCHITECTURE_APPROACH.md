# IT Due Diligence System: Architectural Approach

**Version:** 1.0
**Date:** 2026-01-26
**Status:** Design Specification - Pre-Implementation

---

## Purpose of This Document

This document defines how the IT Due Diligence system will handle data from ingestion through analysis. It is intended for:
- Development team implementing features
- Partners reviewing system methodology
- Offshore teams performing fact verification
- Anyone needing to understand "how this works"

All implementation efforts should align with the principles and flows defined here.

---

## Table of Contents

1. [Core Philosophy](#core-philosophy)
2. [Three-Funnel Framework](#three-funnel-framework)
3. [Document Layer](#document-layer)
4. [Fact Extraction Rules](#fact-extraction-rules)
5. [Fact Lifecycle & Confirmation](#fact-lifecycle--confirmation)
6. [Analysis Layer](#analysis-layer)
7. [Human Review Workflow](#human-review-workflow)
8. [Entity Handling](#entity-handling)
9. [Evidence Chain](#evidence-chain)
10. [System Limitations](#system-limitations)
11. [Operational Considerations](#operational-considerations)
12. [Implementation Priority](#implementation-priority)

---

## Core Philosophy

### Documents Are the Source of Truth

Facts are **interpretations** of documents. The document itself—the actual file with its hash—is the immutable anchor. Facts can be:
- Confirmed (human verified against document)
- Corrected (human found error in extraction)
- Rejected (extraction was wrong)

The document never changes. Facts change as understanding improves.

### Extract Everything, Filter Nothing

The system extracts **all identifiable facts**, regardless of confidence level. High noise does not reduce value—it ensures nothing is missed. The filtering happens during human review, not during extraction.

### Inferred Information Is Not a Fact

If the LLM must infer or deduce something not explicitly stated in the document, it is **not a fact**. It belongs in:
- **Gaps**: Information that should exist but doesn't
- **Confirmation Items**: Questions for management/target to clarify

Facts require explicit documentary evidence. Conclusions require facts.

### Draft Until Confirmed

All analysis output is labeled "DRAFT - Based on Unconfirmed Facts" until the underlying facts have been reviewed. The system provides value immediately while maintaining intellectual honesty about confidence levels.

---

## Three-Funnel Framework

The system operates as three sequential processing stages:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FUNNEL 1: LOGGING                                 │
│                         (Data Collection Layer)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUTS:                           OUTPUTS:                                │
│   ─────────                         ────────                                │
│   • Raw documents (PDF, DOCX, etc.) • Document registry (with hashes)       │
│   • Extracted text                  • Extracted facts (provisional)         │
│   • Document metadata               • Identified gaps                       │
│                                     • LLM call logs (.md audit trail)       │
│                                                                             │
│   RULES:                                                                    │
│   ──────                                                                    │
│   • Extract ALL facts, even low confidence                                  │
│   • NO inference - only explicit statements                                 │
│   • Every fact links to document + exact quote                              │
│   • Every LLM call is logged                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FUNNEL 2: ANALYSIS                                │
│                        (Understanding Layer)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUTS:                           OUTPUTS:                                │
│   ─────────                         ────────                                │
│   • Confirmed + provisional facts   • Environment description               │
│   • Gaps list                       • Risk analysis                         │
│   • Entity-separated data           • Deal considerations                   │
│                                     • Integration complexity assessment     │
│                                                                             │
│   RULES:                                                                    │
│   ──────                                                                    │
│   • Output marked "DRAFT" if based on unconfirmed facts                     │
│   • Every finding cites specific fact IDs                                   │
│   • Findings track which facts they depend on                               │
│   • When facts change, dependent findings are flagged                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FUNNEL 3: FINANCE                                 │
│                         (Cost Impact Layer)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUTS:                           OUTPUTS:                                │
│   ─────────                         ────────                                │
│   • Confirmed findings              • Run rate estimates                    │
│   • Risk assessments                • One-time integration costs            │
│   • Integration complexity          • Cost synergies                        │
│                                     • Investment requirements               │
│                                                                             │
│   RULES:                                                                    │
│   ──────                                                                    │
│   • Only built on confirmed fact foundation                                 │
│   • Every cost estimate traces to findings + facts                          │
│   • Ranges provided, not false precision                                    │
│                                                                             │
│   STATUS: Not yet implemented - requires Funnel 1 & 2 stability first       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Layer

### Document Ingestion Flow

```
User uploads document
        │
        ▼
┌───────────────────┐
│ Compute SHA-256   │  ◄── Hash of raw file bytes (not extracted text)
│ hash of file      │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Check: Hash       │──── Yes ──► Document already exists
│ exists?           │             (skip or flag as duplicate)
└───────────────────┘
        │ No
        ▼
┌───────────────────┐
│ Create document   │
│ record            │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Extract text      │  ◄── PDF parsing, OCR if needed
│ (preserve pages)  │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Store in          │  ◄── Separate locations for TARGET vs BUYER
│ entity folder     │
└───────────────────┘
        │
        ▼
Ready for discovery
```

### Document Registry Schema

```
Document Record
───────────────
doc_id:              UUID (system-generated, immutable)
filename:            Original filename as uploaded
hash_sha256:         Cryptographic hash of raw file bytes
entity:              "target" | "buyer" (determined by upload location)
authority_level:     1 (data room) | 2 (formal correspondence) | 3 (discussion notes)
ingestion_timestamp: When document was added to system
uploaded_by:         User who uploaded (for audit)
raw_file_path:       Path to original unchanged file
extracted_text_path: Path to extracted text version
page_count:          Number of pages (if applicable)
status:              "pending" | "processed" | "error"
```

### Document Storage Structure

```
/documents
├── /target                        # TARGET company documents
│   ├── /data_room                 # Authority level 1
│   │   ├── {hash}_{filename}      # Original files
│   │   └── /extracted
│   │       └── {doc_id}.txt       # Extracted text
│   ├── /correspondence            # Authority level 2
│   └── /notes                     # Authority level 3
│
├── /buyer                         # BUYER company documents
│   ├── /data_room
│   ├── /correspondence
│   └── /notes
│
└── /manifest.json                 # Document registry
```

### Entity Determination

**Critical Design Decision:** Entity (target vs buyer) is determined by **upload location**, not LLM inference.

| Upload Location | Entity | Rationale |
|-----------------|--------|-----------|
| `/target/*` | target | User explicitly placed document in target folder |
| `/buyer/*` | buyer | User explicitly placed document in buyer folder |

This eliminates entity confusion at the source. The LLM does not guess which company a document describes—the user tells us by where they upload it.

**If a document contains information about both entities:**
- Upload to the primary entity's folder
- Flag during review that document contains mixed content
- Consider splitting into separate extractions if needed

---

## Fact Extraction Rules

### What Constitutes a Fact

A **fact** is an explicit statement from a document that can be:
1. Quoted directly from the source text
2. Attributed to a specific document
3. Verified by a human reviewer

### What Is NOT a Fact

| Type | Example | Where It Goes |
|------|---------|---------------|
| Inference | "Since they use AWS, they likely have cloud expertise" | Gap or finding, not fact |
| Assumption | "Assuming standard licensing terms..." | Gap (needs confirmation) |
| Opinion | "The system appears outdated" | Finding (cite facts that support) |
| Calculation | "Total users = 500 + 300 = 800" | Finding (cite source facts) |

### Extraction Completeness

**Rule: Extract everything, filter nothing.**

- If a table has 50 rows, extract 50 facts
- If confidence is low, still extract (flag for review)
- If evidence is weak, still extract (flag for review)
- Do NOT skip items because they seem unimportant

The human review process determines what matters. The extraction process captures what exists.

### Fact Schema

```
Fact Record
───────────
fact_id:              F-{DOMAIN}-{SEQ} (e.g., F-APPS-0042)
doc_id:               UUID reference to source document
entity:               "target" | "buyer" (inherited from document)
domain:               "applications" | "infrastructure" | "security" | etc.
category:             Domain-specific category
item:                 Primary identifier (e.g., application name)
details:              Structured attributes (vendor, version, users, etc.)
exact_quote:          Verbatim text from document supporting this fact
quote_location:       Page number, section, or table reference
confidence_score:     0.0 - 1.0 (calculated based on evidence quality)
extraction_timestamp: When fact was extracted
extraction_model:     LLM model used (e.g., "claude-3-5-haiku-20241022")
extraction_run_id:    Links to audit log for this extraction

# Confirmation fields
confirmation_status:  "provisional" | "confirmed" | "corrected" | "rejected"
confirmed_by:         User who reviewed
confirmed_at:         Timestamp of confirmation
correction_notes:     If corrected, what was changed and why

# Review prioritization
needs_review:         Boolean flag
needs_review_reason:  Why flagged (low confidence, missing fields, etc.)
review_priority:      "high" | "medium" | "low" (for workflow routing)
```

### Confidence Scoring

Confidence is calculated based on evidence quality:

| Factor | Impact |
|--------|--------|
| Has exact quote | +0.3 |
| Quote is substantial (>20 chars) | +0.1 |
| Has complete details (vendor, version, etc.) | +0.2 |
| From high-authority document | +0.2 |
| Multiple corroborating sources | +0.2 |

**Score interpretation:**
- 0.7 - 1.0: High confidence, standard review
- 0.4 - 0.7: Medium confidence, prioritized review
- 0.0 - 0.4: Low confidence, requires verification (route to dedicated reviewer)

**Low confidence does NOT mean rejection.** It means the fact needs more careful human review.

---

## Fact Lifecycle & Confirmation

### Status Flow

```
                    ┌─────────────┐
                    │ PROVISIONAL │  ◄── Initial state after extraction
                    └──────┬──────┘
                           │
              Human review │
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   CONFIRMED   │  │   CORRECTED   │  │   REJECTED    │
│               │  │               │  │               │
│ Fact accurate │  │ Fact updated  │  │ Fact invalid  │
│ as extracted  │  │ with correct  │  │ should not    │
│               │  │ information   │  │ be used       │
└───────────────┘  └───────────────┘  └───────────────┘
```

### Confirmation Actions

| Action | When Used | System Behavior |
|--------|-----------|-----------------|
| **Confirm** | Fact matches document exactly | Status → "confirmed", no data change |
| **Correct** | Fact has errors but is valid | Status → "corrected", original preserved, correction applied |
| **Reject** | Fact is fabricated or wrong | Status → "rejected", excluded from analysis |
| **Flag for Clarification** | Need more info from target | Creates "confirmation item" for management Q&A |

### Correction Tracking

When a fact is corrected, the system preserves:
- Original extracted values
- Corrected values
- Who made the correction
- Why (notes field)
- Timestamp

This maintains audit trail while allowing data quality improvement.

---

## Analysis Layer

### Draft Status

All analysis output carries status based on underlying facts:

| Underlying Facts | Analysis Status | Display |
|------------------|-----------------|---------|
| All confirmed | FINAL | "Analysis based on confirmed facts" |
| Mix of confirmed and provisional | DRAFT | "DRAFT - Based on unconfirmed facts" |
| Any rejected facts in citations | NEEDS REVIEW | "Contains findings based on rejected facts" |

### Finding-to-Fact Dependencies

Every finding must declare which facts it depends on:

```
Finding Record
──────────────
finding_id:      R-{TYPE}-{SEQ}
finding_type:    "risk" | "opportunity" | "work_item" | "observation"
title:           Summary of finding
description:     Detailed explanation
based_on_facts:  [F-APPS-0012, F-INFRA-0034, ...]  ◄── REQUIRED
confidence:      Derived from cited facts' confidence
draft_status:    Computed from cited facts' confirmation status
```

### Dependency Propagation

When a fact status changes:

```
Fact F-APPS-0012 changes from "provisional" to "rejected"
        │
        ▼
System queries: "Which findings cite F-APPS-0012?"
        │
        ▼
Finding R-RISK-0005 cites F-APPS-0012
        │
        ▼
Finding R-RISK-0005 flagged: "Depends on rejected fact - needs review"
```

This ensures that fact corrections flow through to analysis automatically.

---

## Human Review Workflow

### Review Routing

Facts are routed to reviewers based on priority and complexity:

```
┌─────────────────────────────────────────────────────────────────┐
│                     FACT REVIEW QUEUE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HIGH PRIORITY (Senior Team)                                    │
│  ────────────────────────                                       │
│  • Confidence < 0.4                                             │
│  • High-impact categories (security, compliance)                │
│  • Findings already built on these facts                        │
│                                                                 │
│  MEDIUM PRIORITY (Standard Review)                              │
│  ─────────────────────────────                                  │
│  • Confidence 0.4 - 0.7                                         │
│  • Standard categories                                          │
│                                                                 │
│  LOW PRIORITY (Offshore/Bulk Review)                            │
│  ───────────────────────────────────                            │
│  • Confidence > 0.7                                             │
│  • Routine categories (inventory items)                         │
│  • Simple verification: "Does document say X? Yes/No"           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Offshore Team Workflow

For low-priority facts routed to offshore teams:

1. **Fact presented with:**
   - Fact ID and extracted values
   - Source document (linked, downloadable)
   - Exact quote (if available)
   - Page/section reference

2. **Reviewer task:**
   - Open source document
   - Navigate to cited location
   - Verify: Does document contain this information?
   - Action: Confirm / Correct / Reject

3. **Escalation path:**
   - If document doesn't support fact → Reject + note
   - If fact needs interpretation → Escalate to senior team
   - If document is unclear → Flag for target clarification

### Review Metrics

Track review progress:
- Facts pending review (by priority)
- Facts reviewed per day
- Rejection rate (high rate may indicate extraction issues)
- Correction rate (indicates extraction quality)
- Average time to review

---

## Entity Handling

### The Problem We're Solving

In M&A due diligence, confusing target and buyer information is catastrophic:
- Buyer's legacy system attributed to target → wrong integration estimate
- Target's headcount attributed to buyer → wrong cost model
- Mixed data → meaningless analysis

### The Solution: Physical Separation

```
UPLOAD INTERFACE
────────────────

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Upload Documents                                              │
│                                                                 │
│   ┌─────────────────────┐    ┌─────────────────────┐           │
│   │                     │    │                     │           │
│   │   TARGET COMPANY    │    │   BUYER COMPANY     │           │
│   │   ───────────────   │    │   ──────────────    │           │
│   │                     │    │                     │           │
│   │   [Drop files here] │    │   [Drop files here] │           │
│   │                     │    │                     │           │
│   │   For: Acme Corp    │    │   For: BigCo Inc    │           │
│   │   (being acquired)  │    │   (acquirer)        │           │
│   │                     │    │                     │           │
│   └─────────────────────┘    └─────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Entity is determined by upload location.** The LLM does not infer entity.

### Entity in the Data Model

Every fact inherits entity from its source document:

```
Document (entity: "target")
    │
    └──► Fact (entity: "target")  ◄── Inherited, not inferred
            │
            └──► Finding (about: "target")  ◄── Derived from facts
```

### Mixed-Entity Documents

Some documents (e.g., comparison tables) contain both target and buyer information.

**Handling approach:**
1. Upload to primary entity folder (usually target)
2. During extraction, LLM can flag rows/sections as "buyer_mentioned"
3. Reviewer splits if needed, or notes the mixed content
4. System logs that document contains mixed content for audit

This is a known complexity, not a system failure.

---

## Evidence Chain

### The Complete Chain

For any conclusion in a report, we must be able to trace:

```
REPORT CONCLUSION
"Target's ERP system requires $500K upgrade"
        │
        │ Based on finding:
        ▼
FINDING (R-RISK-0023)
"SAP S/4HANA is end-of-life, requires migration"
        │
        │ Cites facts:
        ▼
FACT (F-APPS-0012)                    FACT (F-APPS-0013)
"SAP S/4HANA version 1909"            "Current SAP support ends Dec 2025"
        │                                     │
        │ From document:                      │ From document:
        ▼                                     ▼
DOCUMENT (doc-a1b2c3)                 DOCUMENT (doc-d4e5f6)
"IT_Systems_Inventory.xlsx"           "Vendor_Contracts.pdf"
Hash: 7f83b1657...                    Hash: 2c26b46b...
        │                                     │
        │ Exact quote:                        │ Exact quote:
        ▼                                     ▼
"SAP S/4HANA 1909, Production,        "Support agreement expires
500 users, Finance module"            December 31, 2025"
Page 1, Row 5                         Page 3, Section 2.1
```

### Bidirectional Queries

The system must support queries in both directions:

**Forward (conclusion → evidence):**
- "What facts support this finding?" → List fact IDs
- "What document is this fact from?" → Document record
- "What is the exact quote?" → Quote text and location

**Backward (evidence → conclusions):**
- "What findings cite this fact?" → List finding IDs
- "What facts came from this document?" → List fact IDs
- "If this fact is rejected, what breaks?" → Dependent findings

---

## System Limitations

### Known Limitations (By Design)

| Limitation | Explanation | Mitigation |
|------------|-------------|------------|
| LLM extraction is non-deterministic | Same document may extract slightly differently on re-run | Document hash is anchor; accept variation in interpretation |
| Quote verification is fuzzy | OCR errors, paraphrasing prevent exact match | Use fuzzy matching; flag non-matches for review |
| Some facts will be wrong | LLM can misread, misinterpret, or hallucinate | Human review catches errors; rejection workflow exists |
| Analysis is always provisional | Based on point-in-time facts that may change | Track dependencies; propagate fact changes to findings |

### Known Limitations (Technical)

| Limitation | Explanation | Future Improvement |
|------------|-------------|-------------------|
| No cross-document deduplication | "SAP S/4HANA" in doc A and "S/4 HANA" in doc B not linked | Implement entity resolution layer |
| No semantic search | Cannot ask "find all security-related facts" | Add embedding layer when needed |
| Large documents may truncate | Context window limits | Implement chunking strategy |
| Scanned PDFs depend on OCR quality | Poor scans = poor extraction | Recommend high-quality source documents |

### What This System Cannot Do

1. **Replace human judgment** - It accelerates discovery, doesn't replace analysis
2. **Guarantee accuracy** - It surfaces information with confidence levels
3. **Handle ambiguity automatically** - Ambiguous items flagged for human resolution
4. **Make investment decisions** - It provides input to decision-makers

---

## Operational Considerations

### When to Re-Run Discovery

| Scenario | Action |
|----------|--------|
| New document added | Run discovery on new document only |
| Document updated (new version) | New hash detected; run discovery; compare to previous |
| Extraction rules changed | Consider re-run on critical documents |
| Many facts rejected | Investigate extraction quality; may need prompt tuning |

### Data Freshness

- Facts have extraction timestamp
- Analysis has generation timestamp
- Dashboard shows when data was last updated
- Stale data (>24 hours since document upload) flagged

### Audit Requirements

For partner review and defensibility:

1. **Document manifest** - List of all documents with hashes and ingestion dates
2. **Extraction logs** - .md files for each discovery run showing all LLM calls
3. **Fact confirmation log** - Who confirmed/rejected each fact and when
4. **Finding-to-fact mapping** - Complete citation chain
5. **Analysis generation log** - Which model, which facts, which prompts

---

## Implementation Priority

Based on critical analysis and design decisions:

### Phase 1: Foundation (Current Sprint)

| Priority | Item | Rationale |
|----------|------|-----------|
| 1.1 | Separate upload locations for target/buyer | Eliminates entity confusion at source |
| 1.2 | Document hash + registry | Audit anchor; enables traceability |
| 1.3 | Citation validation ON by default | Findings must cite real facts |
| 1.4 | Entity validation (no silent default) | Error, not silent corruption |

### Phase 2: Confirmation Workflow

| Priority | Item | Rationale |
|----------|------|-----------|
| 2.1 | Fact confirmation UI | Enable human review |
| 2.2 | Review priority queue | Route facts to right reviewers |
| 2.3 | Correction tracking | Preserve audit trail on changes |
| 2.4 | "Draft" labeling in analysis | Honest about confidence level |

### Phase 3: Evidence Chain

| Priority | Item | Rationale |
|----------|------|-----------|
| 3.1 | Quote verification (fuzzy) | Catch hallucinated quotes |
| 3.2 | Bidirectional queries | Enable audit queries |
| 3.3 | Dependency propagation | Fact changes flow to findings |

### Phase 4: Finance Layer

| Priority | Item | Rationale |
|----------|------|-----------|
| 4.1 | Only after Phase 1-3 stable | Finance depends on accurate facts |
| 4.2 | Cost estimation framework | Run rate, one-time costs |
| 4.3 | Synergy identification | Integration opportunities |

---

## Glossary

| Term | Definition |
|------|------------|
| **Document** | Original source file (PDF, DOCX, etc.) - immutable |
| **Fact** | Explicit statement extracted from document with evidence |
| **Gap** | Expected information that is missing from documents |
| **Finding** | Analysis conclusion based on one or more facts |
| **Confirmation Item** | Question for target/management to clarify |
| **Entity** | Target (company being acquired) or Buyer (acquirer) |
| **Provisional** | Fact extracted but not yet human-reviewed |
| **Confirmed** | Fact verified by human reviewer |
| **Authority Level** | Document reliability: 1=data room, 2=correspondence, 3=notes |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-26 | System | Initial architecture specification |

---

*This document defines the architectural approach for the IT Due Diligence system. All implementation should align with these principles. Questions or proposed changes should be discussed before deviating from this specification.*
