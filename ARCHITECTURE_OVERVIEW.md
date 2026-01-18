# IT Due Diligence Agent - Architecture Overview

## What This Document Covers

This document explains how the IT Due Diligence Agent works, how it fits into our diligence workflow, and where we're headed with its development.

> **Technical Note:** This is a custom Python application calling the Claude API directly.
> **Not LangChain. Not LangGraph. Not LangFlow.** No frameworks.
> See [System Architecture](docs/SYSTEM_ARCHITECTURE.md) for technical details.

---

## The Problem We're Solving

IT due diligence today involves:
- Reviewing hundreds of pages from the VDR
- Building inventories in Excel
- Tracking what we know vs. what's missing
- Generating questions for the seller
- Refining our understanding through management calls
- Producing analysis, observations, and recommendations

This is manual, time-intensive, and the knowledge lives in scattered documents and team members' heads.

**This tool aims to:**
- Accelerate initial analysis
- Maintain a structured inventory of what we learn
- Track document sources and attribution
- Support iterative refinement as new information arrives
- Produce outputs our team can validate and build upon

---

## How It Fits Into Our Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           VDR DOCUMENTS ARRIVE                          │
│                                                                         │
│   IT Overview • App Inventories • Org Charts • Security Docs • etc.    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     EXISTING TOOLS PROCESS VDR                          │
│                                                                         │
│   • Map against our standard question sets                              │
│   • Flag what's answered (green), partial (yellow), missing (red)       │
│   • Extract key information into structured outputs                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    IT DUE DILIGENCE AGENT                               │
│                                                                         │
│   PHASE 1: DISCOVERY                                                    │
│   • Ingests processed outputs + raw documents                           │
│   • Builds standardized inventory across 6 domains                      │
│   • Flags gaps where information is missing                             │
│   • Tracks source document for every fact                               │
│                                                                         │
│   PHASE 2: REASONING                                                    │
│   • Analyzes inventory to identify risks                                │
│   • Surfaces strategic considerations for the deal                      │
│   • Generates work items (Day 1, Day 100, Post-100)                     │
│   • Produces recommendations                                            │
│                                                                         │
│   OUTPUT: Structured findings + Excel inventory + HTML viewer           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      TEAM REVIEW & VALIDATION                           │
│                                                                         │
│   • Associate reviews findings in Excel                                 │
│   • Validates against source documents                                  │
│   • Identifies follow-up questions                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      QUESTIONS TO SELLER                                │
│                                                                         │
│   • Questions sent to prove/disprove assumptions                        │
│   • Questions to fill identified gaps                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      MANAGEMENT CALL                                    │
│                                                                         │
│   • Discussion with target IT leadership                                │
│   • Transcript captured with attribution                                │
│   • "John Smith (IT Director) said X on 1/10/26"                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ITERATIVE REFINEMENT                               │
│                                                                         │
│   • New information fed back into system                                │
│   • Assumptions confirmed or updated                                    │
│   • Gaps closed                                                         │
│   • Analysis refined                                                    │
│                                                                         │
│   This loop continues throughout the 2-4 week diligence                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FINAL DELIVERABLES                                 │
│                                                                         │
│   • Analysis findings                                                   │
│   • Observations                                                        │
│   • Recommendations                                                     │
│   • Excel workbook (team working document)                              │
│   • HTML report (visualization)                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The Six Domains

The agent analyzes IT through six specialized lenses:

| Domain | What It Covers |
|--------|----------------|
| **Infrastructure** | Data centers, servers, storage, cloud platforms, hosting models |
| **Network** | WAN, LAN, firewalls, DNS, remote access, connectivity |
| **Cybersecurity** | Security tools, compliance, vulnerability management, incident response |
| **Applications** | ERP, CRM, HCM, custom apps, technical debt, licensing |
| **Identity & Access** | IAM, SSO, MFA, PAM, JML processes, access governance |
| **Organization** | IT org structure, key person risk, outsourcing, skill gaps |

Each domain has:
- **Inventory categories** - standardized structure for capturing facts
- **Consideration library** - specialist thinking patterns for analysis
- **Gap tracking** - what information we don't have

---

## Two-Phase Analysis Model

### Phase 1: Discovery
**Mission:** "What exists? What's documented? What's missing?"

- Extracts facts from documents into standardized inventory
- Same structure every time, regardless of document quality
- Every fact linked to source document
- Gaps explicitly flagged (not just omitted)
- No interpretation yet - just structured extraction

**Output:** Standardized inventory tables (Excel-ready)

### Phase 2: Reasoning
**Mission:** "Given what we learned, what does it mean?"

- Receives Phase 1 inventory as input
- Reasons like a specialist about implications
- Identifies risks (standalone vs. integration-dependent)
- Surfaces strategic considerations
- Generates phased work items
- Produces recommendations

**Key Principle:** The agent has a "consideration library" of things a specialist might think about, but it's **reference material, not a checklist**. The analysis is emergent based on what's actually in THIS environment.

**Output:** Risks, strategic considerations, work items, recommendations

---

## Why Two Phases?

| Single-Pass (Old) | Two-Phase (New) |
|-------------------|-----------------|
| One massive prompt with all questions | Focused prompts per phase |
| Same checklist regardless of environment | Adaptive analysis based on discoveries |
| Extraction and analysis mixed together | Clean separation of concerns |
| Hard to track where facts came from | Document source linked to every fact |

---

## Document Tracking & Attribution

Every fact in the system links back to its source:

**From Documents:**
```
Fact: "VMware 7.0 deployed across 200+ VMs"
Source: VDR/IT_Overview.pdf, Page 12
Ingested: 2026-01-10
Status: Documented
```

**From Meetings:**
```
Fact: "Planning SAP S/4HANA migration in 2027"
Source: Management Call - 2026-01-12
Speaker: John Smith (IT Director)
Status: Confirmed (verbal)
```

This enables:
- Traceability for every finding
- Validation against original sources
- Understanding what changed when

---

## Assumption Management

Diligence is about building and validating assumptions:

```
ASSUMPTION: "Target has adequate DR capability"

EVIDENCE FOR:
- Veeam backup solution documented (VDR/IT_Overview.pdf)
- "Daily backups with 30-day retention" mentioned

EVIDENCE AGAINST:
- DR site not documented (GAP)
- DR testing frequency not stated (GAP)

CONFIDENCE: Medium
STATUS: Needs validation

QUESTIONS TO PROVE/DISPROVE:
- Q1: Where is the DR site located?
- Q2: When was DR last tested?
- Q3: What is the RTO/RPO?
```

As answers come in, assumptions are refined, not replaced.

---

## The Iterative Nature

**This is NOT a one-shot tool.**

```
Week 1: Initial VDR analysis
        → Inventory built
        → Assumptions formed
        → Questions generated

Week 2: Responses received + Management call
        → New information ingested
        → Assumptions validated/updated
        → Gaps closed
        → Follow-up questions generated

Week 3: Additional info + Follow-up call
        → Further refinement
        → Analysis solidified

Week 4: Final analysis
        → Deliverables produced
```

The system maintains state throughout, building a complete picture over time.

---

## Excel as the Working Document

Excel is central to how we work:

- **Team Collaboration** - Multiple people reviewing and validating
- **Leadership Visibility** - Status tracking and progress
- **Source for Final Report** - Copy from working doc to deliverable
- **Familiar Interface** - Team can update and modify as they do today

The agent produces Excel as a **byproduct of doing the work well**, not as a separate export step.

The Excel workbook includes:
- Inventory sheets per domain
- Risk register with source tracking
- Gap tracker with question status
- Work items by phase
- Assumption tracker with evidence

---

## HTML Viewer

For visualization and presentation:

- Interactive view of all findings
- Filter by domain, severity, phase
- Drill into supporting evidence
- Shareable with stakeholders
- Can inform PowerPoint development

---

## Storage Architecture

All findings persist in a structured database:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                                   │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │   DOCUMENTS     │  │  ANALYSIS_RUNS  │  │   INVENTORY     │        │
│   │                 │  │                 │  │                 │        │
│   │ • document_id   │  │ • run_id        │  │ • item_id       │        │
│   │ • name, path    │  │ • timestamp     │  │ • domain        │        │
│   │ • type          │  │ • mode (fresh/  │  │ • category      │        │
│   │ • ingested_date │  │   incremental)  │  │ • source_doc    │        │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │     RISKS       │  │      GAPS       │  │   ASSUMPTIONS   │        │
│   │                 │  │                 │  │                 │        │
│   │ • risk_id       │  │ • gap_id        │  │ • assumption_id │        │
│   │ • description   │  │ • description   │  │ • statement     │        │
│   │ • severity      │  │ • domain        │  │ • evidence_for  │        │
│   │ • source_doc    │  │ • source_doc    │  │ • evidence_against│      │
│   │ • integration_  │  │ • question_     │  │ • confidence    │        │
│   │   dependent     │  │   status        │  │ • status        │        │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │   WORK_ITEMS    │  │ RECOMMENDATIONS │  │   QUESTIONS     │        │
│   │                 │  │                 │  │                 │        │
│   │ • item_id       │  │ • rec_id        │  │ • question_id   │        │
│   │ • title         │  │ • description   │  │ • text          │        │
│   │ • phase         │  │ • priority      │  │ • linked_gap    │        │
│   │ • domain        │  │ • source_doc    │  │ • status        │        │
│   │ • source_doc    │  │                 │  │ • answer        │        │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

This enables:
- Query findings by document, domain, or analysis run
- Track changes over time
- Support incremental analysis
- Generate reports from accumulated knowledge

---

## Future: Costing Agents

Cost analysis is intentionally separated from fact-finding:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ANALYSIS AGENTS                                      │
│                    (Focus on FACTS)                                     │
│                                                                         │
│   Discovery → Reasoning → Coordinator                                   │
│                                                                         │
│   Output: What exists, what's risky, what needs to happen               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│      ONE-TIME COST AGENT      │   │      RUN-RATE SPEND AGENT     │
│                               │   │                               │
│   • Integration costs         │   │   • IT operating budget       │
│   • Migration costs           │   │   • Annual spend analysis     │
│   • Work item estimation      │   │   • Cost optimization         │
│                               │   │                               │
│   Works from validated facts  │   │   Works from validated facts  │
└───────────────────────────────┘   └───────────────────────────────┘
```

**Rationale:** Get the facts right first, then cost them. Mixing fact-finding with costing creates confusion.

---

## Implementation Phases

### Phase 1: Verify Legacy System
Confirm the existing analysis engine runs end-to-end.

### Phase 2: Build Storage Layer
Create database structure for persisting all findings with document tracking.

### Phase 3: Integrate Storage
Wire the storage layer into the analysis flow so findings persist.

### Phase 4: Enable Iteration
Add capability to build on previous analysis, not just start fresh.

### Phase 5: Test & Validate
Run on synthetic documents, validate output quality.

---

## What This Means for the Team

### For Associates
- **Faster initial analysis** - Agent does first pass, you validate
- **Structured output** - Findings in consistent format, not scattered notes
- **Source tracking** - Every fact links to where it came from
- **Excel-native** - Work in familiar environment

### For Managers
- **Visibility** - Track what's known, what's missing, what's assumed
- **Quality control** - Review agent findings, correct as needed
- **Consistency** - Same structure across all deals

### For Leadership
- **Accelerated timeline** - Initial analysis in hours, not days
- **Audit trail** - Document sources for every finding
- **Scalability** - Handle more deals with same team

---

## Current Status (January 2026)

| Component | Status |
|-----------|--------|
| Six domain agents | **Working** - parallel execution with batching |
| Coordinator synthesis | **Working** - cross-domain dependencies |
| Storage layer (SQLite) | **Working** - full persistence |
| HTML viewer | **Working** - interactive filtering |
| Unit tests | **35 passing** |
| v2 Discovery/Reasoning split | Designed, not yet built |
| Cost estimation module | Designed, not yet built |

### V1 MVP: Complete
- 6 domain agents running in parallel (batched for rate limits)
- Four-lens analysis framework
- Coordinator synthesis
- JSON + HTML + SQLite output
- Quality score validation

### V2: Next Phase
- Discovery agents (extract facts into standardized inventory)
- Reasoning agents (analyze inventory, produce findings)
- Separation of extraction vs. interpretation

### V3: Future
- Multi-stage cost refinement pipeline
- Bottoms-up resource planning with rate library
- See [Cost Estimation Module](docs/COST_ESTIMATION_MODULE.md)

---

## Summary

This tool is designed to:

1. **Accelerate** initial IT due diligence analysis
2. **Structure** findings into consistent inventory format
3. **Track** document sources and attribution for every fact
4. **Support** iterative refinement as new information arrives
5. **Produce** Excel workbooks and HTML reports the team can use
6. **Enable** fact-based analysis separate from costing

It fits into our existing workflow, not replaces it. The team validates and refines what the agent produces. The agent handles the initial heavy lifting and maintains the knowledge base as the diligence progresses.

---

## Related Documentation

- [README](README.md) - Quick start and overview
- [System Architecture](docs/SYSTEM_ARCHITECTURE.md) - Technical deep dive (how the agents work)
- [Cost Estimation Module](docs/COST_ESTIMATION_MODULE.md) - Future bottoms-up costing design

---

*Version: 1.1*
*Last Updated: January 14, 2026*
