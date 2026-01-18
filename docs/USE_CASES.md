# Use Cases
## IT Due Diligence Agent in Practice

---

## Overview

This document shows how the IT Due Diligence Agent fits into real deal workflows. These scenarios illustrate when and how to use the tool at different stages.

---

## Scenario 1: Early-Stage Screening

### The Situation

You're staffed on a new deal. The target just uploaded initial IT documentation to the VDR - about 40 pages covering infrastructure, security, and applications. The deal team needs a quick read on IT posture to inform the LOI.

### Without the Tool

- Associate spends 4-6 hours reading documents
- Manually extracts key facts into a spreadsheet
- Drafts initial observations for the team
- Senior reviews, asks clarifying questions
- **Total time: 1-2 days**

### With the Tool

**Morning:**
```bash
# Download docs from VDR, drop into input folder
python main_v2.py input/
```

**15 minutes later:**
- Review executive summary
- Check coverage grade (tells you how complete the picture is)
- Scan high-severity risks
- Review generated VDR requests

**Within 2 hours:**
- Validated findings against source documents
- Added deal-specific context
- Shared initial observations with deal team
- Sent first round of follow-up questions to target

### What the Team Gets

```
┌─────────────────────────────────────────────────────────────────┐
│ EARLY SCREENING OUTPUT                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Coverage Grade: C (47% of critical items documented)            │
│                                                                 │
│ Key Observations:                                               │
│ • VMware 6.7 (EOL) - upgrade likely needed                     │
│ • No DR documentation provided                                  │
│ • Cloud footprint unclear - AWS mentioned but no details        │
│                                                                 │
│ Immediate Follow-ups Needed:                                    │
│ • DR plan and RTO/RPO targets                                   │
│ • Cloud infrastructure details                                  │
│ • Security compliance certifications                            │
│                                                                 │
│ Initial Risk Flag: Medium-High IT complexity                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Scenario 2: Deep Dive Analysis

### The Situation

Deal is progressing. Target has uploaded comprehensive IT documentation - 150+ pages including network diagrams, security assessments, vendor contracts, and org charts. The team needs a thorough IT DD analysis for the IC memo.

### Without the Tool

- Associate spends 2-3 days reading all documents
- Creates detailed inventory across all domains
- Identifies risks and drafts findings
- Estimates integration costs
- Senior spends half a day reviewing and refining
- **Total time: 3-4 days**

### With the Tool

**Day 1 Morning:**
```bash
python main_v2.py input/
```

**Day 1 Afternoon:**
- Review all outputs systematically
- Validate evidence citations
- Adjust severity ratings based on deal context
- Refine cost estimates based on integration approach
- Add industry-specific considerations

**Day 2:**
- Senior review of refined analysis
- Finalize findings for IC memo
- **Total time: 1.5 days**

### What the Team Gets

```
┌─────────────────────────────────────────────────────────────────┐
│ DEEP DIVE OUTPUT                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Coverage Grade: B+ (78% of critical items documented)           │
│                                                                 │
│ INFRASTRUCTURE                                                  │
│ • 340 VMs on VMware 6.7 (EOL Oct 2022)                         │
│ • Primary DC: Equinix Chicago, DR: Equinix Dallas              │
│ • Backup: Veeam, daily, 30-day retention                       │
│ • Gap: RTO/RPO not documented                                   │
│                                                                 │
│ CYBERSECURITY                                                   │
│ • EDR: CrowdStrike Falcon (good)                               │
│ • No SIEM identified                                           │
│ • SOC2 Type II certified (last audit: 6 months ago)            │
│ • Gap: Penetration test results not provided                    │
│                                                                 │
│ APPLICATIONS                                                    │
│ • ERP: SAP S/4HANA (cloud)                                     │
│ • CRM: Salesforce                                              │
│ • 12 custom applications identified                            │
│ • Technical debt: Legacy .NET apps flagged                     │
│                                                                 │
│ ESTIMATED INTEGRATION COSTS                                     │
│ ├── Day 1: $50K - $150K (connectivity, access)                 │
│ ├── Day 100: $400K - $900K (VMware upgrade, migrations)        │
│ └── Post-100: $200K - $500K (app rationalization)              │
│                                                                 │
│ TOP RISKS FOR IC                                                │
│ 1. VMware EOL - security/support risk (HIGH)                   │
│ 2. No SIEM - detection gap (MEDIUM)                            │
│ 3. Legacy .NET apps - integration complexity (MEDIUM)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Scenario 3: VDR Request Generation

### The Situation

Initial documents received, but there are significant gaps. Need to send a comprehensive follow-up request to the target before the management presentation.

### Without the Tool

- Associate reviews what's been provided
- Compares against mental checklist of what's needed
- Drafts follow-up questions
- Senior adds items from experience
- Risk of forgetting to ask for something
- **Total time: 2-3 hours**

### With the Tool

```bash
python main_v2.py input/
```

**VDR Request Pack generated automatically:**

```markdown
## CRITICAL Priority (12 requests)

### VDR-001: RTO/RPO Documentation
**Domain:** infrastructure | **Category:** backup_dr
Please provide disaster recovery objectives including RTO and RPO targets.
**Suggested Documents:** DR plan, BCP, backup policies

### VDR-002: SOC2 Type II Report
**Domain:** cybersecurity | **Category:** compliance
Please provide most recent SOC2 Type II audit report.
**Suggested Documents:** SOC2 report, bridge letter if applicable

### VDR-003: Network Architecture Diagram
**Domain:** network | **Category:** lan
Please provide current network architecture documentation.
**Suggested Documents:** Network diagrams, VLAN documentation

... (9 more critical requests)

## HIGH Priority (8 requests)
...
```

**What the associate does:**
- Reviews generated requests (10 minutes)
- Removes any already answered
- Adds deal-specific questions
- Sends to target

**Total time: 30 minutes** (vs. 2-3 hours)

---

## Scenario 4: Incremental Update

### The Situation

Target uploaded additional documents responding to the VDR request. Need to update the analysis with new information.

### With the Tool

```bash
# Add new docs to input folder alongside originals
python main_v2.py input/
```

The system re-analyzes everything:
- New facts extracted from additional documents
- Coverage grade updates (hopefully improves)
- Risks may be resolved or new ones identified
- VDR requests update (answered items no longer appear)

**Compare outputs:**
- Previous: Coverage Grade C (47%)
- Updated: Coverage Grade B (71%)
- 8 gaps now filled, 4 remain

---

## Scenario 5: Cross-Deal Consistency

### The Situation

Managing partner wants to compare IT posture across three targets being evaluated. Need consistent assessment framework.

### With the Tool

Run analysis on each target separately:

```bash
python main_v2.py target_a/
python main_v2.py target_b/
python main_v2.py target_c/
```

**Comparison possible because outputs are structured:**

```
                    │ Target A │ Target B │ Target C │
────────────────────┼──────────┼──────────┼──────────┤
Coverage Grade      │    B     │    C     │    A-    │
Critical Risks      │    3     │    7     │    1     │
Est. Integration    │  $500K   │  $1.2M   │  $300K   │
EOL Systems         │   Yes    │   Yes    │    No    │
SOC2 Certified      │   Yes    │    No    │   Yes    │
```

Same checklist, same framework, comparable results.

---

## Scenario 6: Post-Close Integration Planning

### The Situation

Deal closed. Integration team needs structured IT inventory and work item list to plan Day 1 and Day 100 activities.

### What the Tool Provides

**From the analysis run during DD:**

```
WORK ITEMS BY PHASE

DAY 1 (Immediate)
├── WI-001: Establish network connectivity ($25K-$50K)
├── WI-002: Set up shared authentication ($10K-$25K)
└── WI-003: Implement security monitoring ($25K-$50K)

DAY 100 (First 100 Days)
├── WI-004: VMware upgrade project ($150K-$300K)
├── WI-005: SIEM implementation ($100K-$200K)
└── WI-006: DR testing and validation ($50K-$100K)

POST-100 (Longer Term)
├── WI-007: Application rationalization ($200K-$400K)
└── WI-008: Cloud migration assessment ($50K-$100K)

COST SUMMARY
├── Day 1 Total: $60K - $125K
├── Day 100 Total: $300K - $600K
└── Post-100 Total: $250K - $500K
```

**Integration team gets:**
- Prioritized work items
- Phase assignments
- Cost ranges for budgeting
- Evidence/rationale for each item

---

## Summary: When to Use the Tool

| Situation | Use Case | Primary Output |
|-----------|----------|----------------|
| New deal, initial docs | Early screening | Coverage grade, key risks |
| Comprehensive docs received | Deep dive analysis | Full findings, cost estimates |
| Need follow-up questions | VDR generation | Prioritized request list |
| New docs uploaded | Incremental update | Updated analysis |
| Comparing targets | Cross-deal consistency | Structured comparison |
| Post-close planning | Integration support | Phased work items |

---

## Key Takeaway

The tool handles the **extraction and structuring** so the team can focus on **judgment and strategy**.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Tool does:              Team does:                           │
│   • Read documents        • Validate findings                  │
│   • Extract facts         • Add deal context                   │
│   • Identify gaps         • Calibrate severity                 │
│   • Generate questions    • Make recommendations               │
│   • Estimate costs        • Apply judgment                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*See GETTING_STARTED.md for step-by-step instructions.*
