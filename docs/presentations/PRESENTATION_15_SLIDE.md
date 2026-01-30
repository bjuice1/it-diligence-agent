# IT Due Diligence Agent
## Deal Team Guide

---

# Slide 1: The IT DD Challenge

## Current State Is Unsustainable

| Pain Point | Reality |
|------------|---------|
| **Time** | 80+ hours reading documents per deal |
| **Cost** | $150-300K external consultant fees |
| **Quality** | Varies by who does the work |
| **Speed** | 3-4 weeks delays deal velocity |
| **Output** | Data dumps, not insights |

### The Real Problem
Traditional IT DD tells you **what exists**. It doesn't tell you **what it means for the deal**.

---

# Slide 2: Our Philosophy

## The Brain on Top

We are not a data extraction tool. We are the **analysis layer** that makes data meaningful.

```
┌────────────────────────────────────────────────────────────┐
│                    THE VALUE CHAIN                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   ToltIQ / Manual     ──►    AI BRAIN    ──►    INSIGHTS   │
│   (Data Extraction)          (Analysis)         (So What)  │
│                                                            │
│   "SAP exists"               "SAP is 80%        "Migration │
│   "500 users"                 of transactions"   risk $2-4M│
│   "$1.2M license"            "Heavy custom"     18-24 mo"  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Core Principles
1. **Lead with insights**, not data
2. **Every finding cites evidence**
3. **Designed for M&A context**, not generic IT assessment

---

# Slide 3: The 30-Second Version

## How It Works

```
┌─────────────┐          ┌─────────────┐          ┌─────────────┐
│             │          │             │          │             │
│  DOCUMENTS  │  ─────►  │  AI BRAIN   │  ─────►  │   REPORT    │
│             │          │             │          │             │
└─────────────┘          └─────────────┘          └─────────────┘
     INPUT                  PROCESS                  OUTPUT
```

| Stage | What Happens |
|-------|--------------|
| **Input** | Upload VDR docs (Excel, Word, PDF) |
| **Process** | AI extracts facts, identifies patterns, flags risks |
| **Output** | Deal-ready report with costs, risks, work items |

**Time:** Hours, not weeks

---

# Slide 4: What Goes In

## Supported Document Types

| Type | Examples | What We Extract |
|------|----------|-----------------|
| **Excel** | Application inventory, Org charts | Structured data, item lists |
| **Word** | IT assessments, Security reviews | Narrative facts, quotes |
| **PDF** | Vendor contracts, Architecture docs | Text content, tables |
| **Markdown** | Meeting notes, Data room indexes | Unstructured insights |

### Typical VDR Content
- Application inventory spreadsheet
- Infrastructure summary
- Organization chart
- Security assessment
- Vendor/contract list
- IT budget documentation

---

# Slide 5: What Comes Out

## Four Key Deliverables

### 1. Cost Center
All IT costs in one view for deal modeling
- Run-rate (annual recurring)
- One-time (integration costs)
- Synergy opportunities

### 2. Risk Register
Evidence-backed risks with mitigation
- Severity ratings
- M&A implications
- Supporting facts

### 3. Work Items
Phased integration roadmap
- Day 1 / Day 100 / Post-100
- Cost estimates per item
- Dependencies mapped

### 4. Data Flow Diagrams
Visual system connectivity
- Application relationships
- Integration points
- Criticality indicators

---

# Slide 6: The Evidence Chain

## Every Conclusion Traces to Source

```
┌─────────────────────────────────────────────────────────────┐
│                     RISK                                     │
│   "High ERP concentration with dual-platform costs"         │
│   Risk ID: R-APP-01                                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│    FACT     │ │    FACT     │ │    FACT     │
│  F-APP-001  │ │  F-APP-003  │ │  F-APP-007  │
│ "SAP S/4..."│ │"NetSuite..."│ │ "$586K..."  │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  SOURCE DOCUMENT                             │
│                                                             │
│  "Application_Inventory.xlsx"                               │
│                                                             │
│  Exact quote: "SAP S/4HANA serves as our core ERP          │
│  platform with approximately 500 active users and           │
│  handles 80% of financial transactions..."                  │
└─────────────────────────────────────────────────────────────┘
```

### Why This Matters
- **Auditable** - Investment committee can trace any finding
- **Validatable** - Confirm in management calls
- **Transparent** - No "black box" AI

---

# Slide 7: Cost Center Overview

## All Costs in One Place

```
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTIVE SUMMARY                         │
│                                                             │
│   Total Run-Rate: $36.1M/yr                                 │
│   One-Time Range: $2.2M - $8.4M                             │
│   Synergy Potential: $1.2M/yr                               │
└─────────────────────────────────────────────────────────────┘
```

| Run-Rate Costs | Amount | % |
|----------------|--------|---|
| Headcount | $28.9M | 80% |
| Applications | $7.2M | 20% |
| Infrastructure | TBD | - |
| **Total** | **$36.1M** | 100% |

| One-Time Costs | Low | Mid | High |
|----------------|-----|-----|------|
| Day 1 | $275K | $650K | $1.0M |
| Day 100 | $1.2M | $2.9M | $4.5M |
| Post-100 | $750K | $1.8M | $2.9M |
| **Total** | **$2.2M** | **$5.3M** | **$8.4M** |

### Data Quality Indicators
We show confidence levels so you know what to verify:
- **High**: From structured inventory data
- **Medium**: From document extraction
- **Low**: Inferred or incomplete

---

# Slide 8: Risk Analysis

## How Risks Are Identified

### Risk Structure

| Field | Description |
|-------|-------------|
| **ID** | R-APP-001, R-INFRA-002, etc. |
| **Title** | Clear statement of the risk |
| **Severity** | Critical / High / Medium / Low |
| **Description** | What the risk is |
| **So What** | M&A implication |
| **Mitigation** | Recommended approach |
| **Citing Facts** | Evidence trail |

### Example Risk

> **R-APP-001: High ERP Concentration Risk**
>
> SAP S/4HANA handles 80% of business transactions with heavy customization.
>
> **So What:** Migration or replacement would cost $2-4M and take 18-24 months. TSA exposure is significant.
>
> **Mitigation:** Negotiate extended TSA, begin assessment immediately.
>
> **Evidence:** F-APP-001, F-APP-003, F-APP-007

---

# Slide 9: Work Items & Phases

## Integration Roadmap

### Phase Framework

| Phase | Timeline | Focus |
|-------|----------|-------|
| **Day 1** | Close date | Business continuity |
| **Day 100** | First 100 days | Initial integration |
| **Post-100** | After 100 days | Optimization |

### Work Item Structure

| Field | Description |
|-------|-------------|
| **ID** | W-APP-001, W-INFRA-002 |
| **Title** | What needs to be done |
| **Phase** | When it needs to happen |
| **Cost Estimate** | Range (low/mid/high) |
| **Owner** | Buyer / Target / Shared |
| **Dependencies** | What must happen first |
| **Triggered By** | Which risks/gaps drive this |

### Sample by Phase

| Phase | Items | Cost Range |
|-------|-------|------------|
| Day 1 | 5 | $275K - $1.0M |
| Day 100 | 10 | $1.2M - $4.5M |
| Post-100 | 6 | $750K - $2.9M |

---

# Slide 10: Data Quality & Confidence

## Transparency About Uncertainty

### Confidence Levels

| Level | Meaning | Source |
|-------|---------|--------|
| **High** | Explicitly stated in documents | Direct quotes |
| **Medium** | Reasonably inferred | Context + patterns |
| **Low** | Possible but uncertain | Limited data |

### What We Flag

- **Gaps**: Information that should exist but doesn't
- **Unknowns**: Items we couldn't identify/classify
- **Assumptions**: Where we made judgment calls

### Data Quality Bar (in UI)

```
┌─────────────────────────────────────────────────────────────┐
│ Data Quality:                                               │
│ [Headcount: Medium] [Apps: High] [Infra: Low] [Costs: Med] │
└─────────────────────────────────────────────────────────────┘
```

**Philosophy:** Better to be honest about uncertainty than falsely confident.

---

# Slide 11: Human Review Workflow

## AI + Human = Best Results

### Review Process

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  AI EXTRACT  │ ──► │  SME REVIEW  │ ──► │  CONFIRMED   │
│  (Draft)     │     │  (Validate)  │     │  (Final)     │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Review Queue Features

| Feature | Purpose |
|---------|---------|
| **Priority sorting** | High-impact items first |
| **Bulk actions** | Approve multiple similar items |
| **Correction workflow** | Fix and learn from errors |
| **Audit trail** | Who reviewed what, when |

### SME Verification

For high-value findings, flag for expert review:
- ERP cost estimates
- Security assessment gaps
- Key person dependencies

---

# Slide 12: Demo - Upload Flow

## Live Walkthrough

### Step 1: Document Upload

```
┌─────────────────────────────────────────────────────────────┐
│  UPLOAD DOCUMENTS                                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │     Drag and drop files here                        │   │
│  │     or click to browse                              │   │
│  │                                                      │   │
│  │     Supported: Excel, Word, PDF, Markdown           │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Recent uploads:                                            │
│  ✓ Application_Inventory.xlsx (33 apps detected)           │
│  ✓ IT_Assessment_2025.docx (processing...)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Step 2: Type Detection

System automatically detects:
- Is this an application inventory?
- Is this infrastructure data?
- Is this organization/headcount?
- Is this a narrative assessment?

### Step 3: Processing

- Structured data → Inventory Store
- Narrative content → Discovery Agents → Fact Store
- All data → Reasoning Agents → Insights

---

# Slide 13: Demo - Analysis Flow

## Viewing Results

### Dashboard View

```
┌─────────────────────────────────────────────────────────────┐
│  IT DUE DILIGENCE DASHBOARD                                 │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  RISKS  │  │  FACTS  │  │  WORK   │  │  COSTS  │       │
│  │   12    │  │   38    │  │  ITEMS  │  │ CENTER  │       │
│  │  High   │  │ Extract │  │   21    │  │ $36.1M  │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                             │
│  Recent Findings:                                           │
│  ⚠️ R-APP-001: High ERP concentration risk                 │
│  ⚠️ R-SEC-003: MFA not enforced for admin accounts        │
│  ℹ️ F-ORG-012: 3 key persons identified with unique...     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Drill-Down Flow

1. **Dashboard** → See summary metrics
2. **Risk List** → See all risks by severity
3. **Risk Detail** → See evidence chain
4. **Source Document** → See exact quote

---

# Slide 14: Integration Points

## How This Fits Your Workflow

### With ToltIQ

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   TOLTIQ    │     │  THIS TOOL  │     │   OUTPUT    │
│   Extract   │ ──► │   Analyze   │ ──► │   Report    │
│   Data      │     │   Insight   │     │   Ready     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Standalone Mode

Can also work directly with VDR documents:
- Upload Excel inventories directly
- Process Word/PDF assessments
- No dependency on external tools

### Export Options

| Format | Use Case |
|--------|----------|
| **Excel** | Deal model integration |
| **PDF** | IC presentations |
| **JSON** | System integration |
| **Markdown** | Documentation |

---

# Slide 15: Getting Started

## How to Begin on a Live Deal

### Pre-Requisites

| Item | Status |
|------|--------|
| Docker installed | Required |
| Anthropic API key | Required |
| VDR access | Required |

### Quick Start

```bash
# 1. Navigate to docker directory
cd docker/

# 2. Start the application
docker-compose up

# 3. Open browser
# http://localhost:5001
```

### First Deal Checklist

1. [ ] Upload application inventory (Excel)
2. [ ] Upload IT assessment (Word/PDF)
3. [ ] Review auto-detected facts
4. [ ] Check generated risks
5. [ ] Review Cost Center
6. [ ] Export for deal model

### Support

- Documentation: `/docs` folder
- Issues: Ask your implementation contact

---

## Summary

| What | How | Result |
|------|-----|--------|
| Upload docs | Drag & drop | Minutes |
| Get insights | AI analysis | Automatic |
| Review findings | Evidence chain | Validated |
| Export costs | Cost Center | Deal-ready |

**We are the brain on top.**

---

*Deal Team Training Materials*
*January 2026*
