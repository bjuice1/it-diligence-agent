# Application Review Process - Complete Walkthrough

**Document Purpose:** Comprehensive walkthrough of the Applications domain analysis process for leadership review
**Audience:** Leadership, Technical Reviewers, Process Improvement Teams
**Version:** 1.0
**Date:** January 2026

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Process Flow Diagram](#2-process-flow-diagram)
3. [Inputs - What Feeds the Process](#3-inputs---what-feeds-the-process)
4. [Phase 1: Application Enumeration](#4-phase-1-application-enumeration)
5. [Phase 2: Capability Coverage Analysis](#5-phase-2-capability-coverage-analysis)
6. [Phase 3: Four-Lens Analysis](#6-phase-3-four-lens-analysis)
7. [Phase 4: Buyer Comparison (When Applicable)](#7-phase-4-buyer-comparison-when-applicable)
8. [Outputs - What the Process Produces](#8-outputs---what-the-process-produces)
9. [Data Flow & Storage](#9-data-flow--storage)
10. [Quality Controls & Anti-Hallucination](#10-quality-controls--anti-hallucination)
11. [Integration with Other Domains](#11-integration-with-other-domains)
12. [Downstream Consumers](#12-downstream-consumers)
13. [Key Decision Points](#13-key-decision-points)
14. [Areas for Leadership Attention](#14-areas-for-leadership-attention)

---

## 1. Executive Overview

### What This Process Does

The Application Review process analyzes a target company's application portfolio to answer:

1. **What applications exist?** (Complete enumeration, not summarization)
2. **What business capabilities do they support?** (Checklist-driven coverage)
3. **What are the standalone risks?** (Independent of integration)
4. **What are the integration considerations?** (Overlap with buyer, questions to answer)
5. **What follow-up questions need answers?** (Actionable next steps)

### Key Design Principles

| Principle | Why It Matters |
|-----------|----------------|
| **Enumerate, Don't Summarize** | "47 applications" → 47 individual records, not a summary |
| **Checklist-Driven** | Compare against 13 business capabilities to find gaps |
| **Evidence-Based** | Every finding must cite source with exact quote |
| **Questions, Not Decisions** | Surface considerations; don't prescribe integration decisions |
| **Cost-Separated** | Domain agent finds facts/risks; Costing Agent handles costs |

### Process Trigger

The Applications agent is invoked by the Coordinator when:
- User requests application portfolio analysis
- DD engagement includes application domain in scope
- Cross-domain analysis requires application context

---

## 2. Process Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INPUTS                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Application  │  │ Architecture │  │  Contract/   │  │   Other DD   │    │
│  │  Inventory   │  │   Diagrams   │  │   Vendor     │  │  Documents   │    │
│  │  Documents   │  │              │  │    Lists     │  │              │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         └─────────────────┴─────────────────┴─────────────────┘             │
│                                    │                                         │
│                                    ▼                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: APPLICATION ENUMERATION                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PASS 1a: Primary Enumeration                                        │   │
│  │  • Scan app inventory documents                                      │   │
│  │  • Call record_application() for EACH app (one call per app)        │   │
│  │  • Capture: name, vendor, version, hosting, criticality, etc.       │   │
│  │  • Required: source_evidence with exact_quote                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PASS 1b: Incidental Discovery                                       │   │
│  │  • Scan OTHER documents for app mentions                             │   │
│  │  • "data from Workday" → record Workday                             │   │
│  │  • "integrates with Salesforce" → record Salesforce                 │   │
│  │  • Flag discovery_source = "Mentioned_In_Passing"                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PASS 1c: Enumeration Verification                                   │   │
│  │  • Compare: apps recorded vs counts mentioned in docs               │   │
│  │  • "47 applications" but only 23 recorded → flag_gap()              │   │
│  │  • Generate questions for missing apps                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  OUTPUT: applications[] list with APP-001, APP-002, ... IDs                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   PHASE 2: CAPABILITY COVERAGE ANALYSIS                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  BUSINESS CAPABILITY CHECKLIST (13 Areas)                            │   │
│  │                                                                       │   │
│  │  □ finance_accounting    □ human_resources      □ sales_crm         │   │
│  │  □ marketing             □ operations_supply_chain                   │   │
│  │  □ it_infrastructure     □ identity_security    □ collaboration     │   │
│  │  □ data_analytics        □ legal_compliance     □ customer_service  │   │
│  │  □ ecommerce_digital     □ industry_specific                        │   │
│  │                                                                       │   │
│  │  For EACH capability area, call record_capability_coverage()         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Coverage Assessment                                                 │   │
│  │                                                                       │   │
│  │  For each capability:                                                │   │
│  │  1. Which apps from Phase 1 cover this capability?                  │   │
│  │  2. Coverage status: Fully_Documented / Partially / Not_Found / N/A │   │
│  │  3. Business relevance for THIS company                             │   │
│  │  4. Expected apps that are MISSING                                  │   │
│  │  5. Follow-up questions for gaps                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  OUTPUT: capability_coverage[] list with CAP-001, CAP-002, ... IDs          │
│                                                                              │
│  EXAMPLE:                                                                    │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ capability_area: "identity_security"                                │    │
│  │ coverage_status: "Partially_Documented"                             │    │
│  │ business_relevance: "Critical"                                      │    │
│  │ applications_found: ["Okta", "CyberArk"]                           │    │
│  │ expected_but_missing: ["SIEM", "EDR"]                              │    │
│  │ follow_up_questions: [                                              │    │
│  │   {question: "What SIEM solution is in use?",                      │    │
│  │    target: "Target_IT_Leadership", priority: "high"}               │    │
│  │ ]                                                                   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 3: FOUR-LENS ANALYSIS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LENS 1: CURRENT STATE (create_current_state_entry)                  │   │
│  │                                                                       │   │
│  │  • Portfolio-level observations                                      │   │
│  │  • Hosting model distribution (SaaS %, on-prem %, hybrid %)         │   │
│  │  • Vendor concentration patterns                                     │   │
│  │  • Technical debt overview                                           │   │
│  │  • Maturity assessment                                               │   │
│  │                                                                       │   │
│  │  OUTPUT: current_state[] entries with CS-001, CS-002, ... IDs       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LENS 2: RISKS (identify_risk)                                       │   │
│  │                                                                       │   │
│  │  Key distinction: integration_dependent flag                         │   │
│  │                                                                       │   │
│  │  STANDALONE RISKS (integration_dependent: false):                   │   │
│  │  • EOL/EOS applications with security exposure                      │   │
│  │  • License non-compliance                                            │   │
│  │  • Unsupported versions                                              │   │
│  │  • Key person dependencies                                           │   │
│  │  • Technical debt accumulation                                       │   │
│  │                                                                       │   │
│  │  INTEGRATION RISKS (integration_dependent: true):                   │   │
│  │  • Migration complexity                                              │   │
│  │  • Data conversion challenges                                        │   │
│  │  • Integration breakage                                              │   │
│  │                                                                       │   │
│  │  OUTPUT: risks[] entries with R-001, R-002, ... IDs                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LENS 3: STRATEGIC CONSIDERATIONS (create_strategic_consideration)   │   │
│  │                                                                       │   │
│  │  • Deal-relevant insights                                            │   │
│  │  • Rationalization opportunities                                     │   │
│  │  • TSA considerations                                                │   │
│  │  • Synergy potential (qualitative)                                  │   │
│  │                                                                       │   │
│  │  REQUIRED: follow_up_question + question_target                     │   │
│  │  Every strategic consideration must generate an actionable question │   │
│  │                                                                       │   │
│  │  OUTPUT: strategic_considerations[] with SC-001, SC-002, ... IDs    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LENS 4: INTEGRATION WORK ITEMS (create_work_item)                   │   │
│  │                                                                       │   │
│  │  Phased work items:                                                  │   │
│  │  • Day_1: Critical continuity items only                            │   │
│  │  • Day_100: Stabilization and quick wins                            │   │
│  │  • Post_100: Full integration and rationalization                   │   │
│  │  • Optional: Nice-to-have improvements                              │   │
│  │                                                                       │   │
│  │  Note: Application work is typically Day_100 or Post_100            │   │
│  │  (not Day 1 critical - people need to log in first)                 │   │
│  │                                                                       │   │
│  │  OUTPUT: work_items[] with WI-001, WI-002, ... IDs                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              PHASE 4: BUYER COMPARISON (When Buyer Info Available)           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STEP 1: Record Buyer Applications (record_buyer_application)        │   │
│  │                                                                       │   │
│  │  Source: Buyer questionnaire, prior DD, known environment           │   │
│  │  Capture: app_name, vendor, category, capability_areas, source      │   │
│  │                                                                       │   │
│  │  OUTPUT: buyer_applications[] with BAPP-001, BAPP-002, ... IDs      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STEP 2: Identify Overlaps (record_application_overlap)              │   │
│  │                                                                       │   │
│  │  Overlap Types:                                                      │   │
│  │  • Same_Product: Both have Salesforce                               │   │
│  │  • Same_Category_Different_Vendor: Target Salesforce, Buyer Dynamics│   │
│  │  • Target_Only: Target has app, buyer doesn't                       │   │
│  │  • Complementary: Different apps serving different needs            │   │
│  │                                                                       │   │
│  │  For each overlap, capture:                                          │   │
│  │  • What the overlap means (considerations)                          │   │
│  │  • Questions that need answering (follow_up_questions)              │   │
│  │                                                                       │   │
│  │  NOTE: We do NOT prescribe integration decisions, timelines, or     │   │
│  │  synergies. Each deal is unique - we surface questions.             │   │
│  │                                                                       │   │
│  │  OUTPUT: application_overlaps[] with OVL-001, OVL-002, ... IDs      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  EXAMPLE:                                                                    │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ target_app_name: "Salesforce Sales Cloud"                           │    │
│  │ buyer_app_name: "Salesforce Sales Cloud"                            │    │
│  │ overlap_type: "Same_Product"                                        │    │
│  │ considerations: "Both companies use Salesforce. Consolidation       │    │
│  │   opportunity exists but customization levels will drive complexity.│    │
│  │   Data migration and user training will be key workstreams."        │    │
│  │ follow_up_questions: [                                              │    │
│  │   {question: "How customized is buyer's Salesforce instance?",     │    │
│  │    target: "Buyer_IT", why_it_matters: "Determines migration        │    │
│  │    complexity and whether consolidation is feasible"}               │    │
│  │ ]                                                                   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FINAL VERIFICATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Completeness Checklist (validate_application_completeness)          │   │
│  │                                                                       │   │
│  │  □ All applications mentioned in documents recorded?                 │   │
│  │  □ All 13 capability areas assessed?                                │   │
│  │  □ Critical capabilities (finance, HR, identity) have coverage?     │   │
│  │  □ Follow-up questions generated for all gaps?                      │   │
│  │  □ Risks have mitigations and evidence?                             │   │
│  │  □ Strategic considerations have follow-up questions?               │   │
│  │  □ Work items assigned to phases?                                   │   │
│  │  □ Buyer overlaps analyzed (if buyer info available)?               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  complete_analysis() - Summary Generation                            │   │
│  │                                                                       │   │
│  │  • Total applications recorded                                       │   │
│  │  • Capability coverage completeness                                  │   │
│  │  • Critical gaps requiring seller follow-up                         │   │
│  │  • Key risks and strategic considerations                           │   │
│  │  • Overlap summary (if buyer comparison done)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Inputs - What Feeds the Process

### Primary Document Sources

| Source Type | What We Extract | Typical Location |
|-------------|-----------------|------------------|
| **Application Inventory** | App names, vendors, versions, user counts | Dedicated inventory spreadsheet or doc |
| **Architecture Diagrams** | Integration points, data flows | Technical architecture docs |
| **Contract/Vendor Lists** | License types, expiry dates, costs (noted, not analyzed) | Procurement/legal docs |
| **IT Strategy Documents** | Modernization plans, technical debt backlog | IT roadmap docs |
| **Interview Notes** | Tribal knowledge, undocumented systems | Management presentations |
| **Infrastructure Docs** | Apps hosted on infrastructure | Server inventories |
| **Security Docs** | Security tools, identity systems | Security assessments |

### Incidental Sources (Apps Mentioned in Passing)

The agent also scans non-application documents for app mentions:
- "Data flows from **Workday** to payroll" → record Workday
- "Users authenticate via **Okta**" → record Okta
- "Reports generated in **Tableau**" → record Tableau

These are flagged with `discovery_source: "Mentioned_In_Passing"` to indicate lower confidence.

### Buyer Environment Information (When Available)

| Source | Reliability | What It Provides |
|--------|-------------|------------------|
| Buyer Questionnaire | High | Direct list of buyer's apps |
| Prior DD on Buyer | High | Detailed buyer app portfolio |
| Known Environment | Medium | Common knowledge about buyer's stack |
| Public Information | Low | Press releases, job postings, etc. |
| Assumptions | Low | Based on buyer's industry/size |

---

## 4. Phase 1: Application Enumeration

### Purpose
Create a **complete inventory** of every application mentioned in the documents. The key rule: **enumerate, don't summarize**.

### Tool Used: `record_application`

Called **once per application**. If documents mention "47 applications", there should be ~47 `record_application` calls.

### Fields Captured (26 total)

#### Required Fields (7)
| Field | Purpose |
|-------|---------|
| `application_name` | Official app name |
| `application_category` | ERP, CRM, HCM, Security, etc. |
| `vendor` | Vendor/publisher |
| `hosting_model` | SaaS, On_Premise, IaaS_Cloud, Hybrid, etc. |
| `business_criticality` | Critical, High, Medium, Low |
| `discovery_source` | How was this app found in docs? |
| `source_evidence` | Exact quote from document proving existence |

#### Optional Fields (19)
- Version, deployment_date, technology_stack
- User_count, business_owner, business_processes_supported
- License_type, contract_expiry, license_count
- Integration_count, key_integrations, customization_level
- Support_status, api_availability
- Known_issues, notes
- **Data classification** (contains_pii, contains_phi, contains_pci, data_residency)

### Pass Structure

```
PASS 1a: Primary Enumeration
├── Scan app inventory documents
├── Record each app with full detail
└── Progress tracking: "Recorded 15/47 applications..."

PASS 1b: Incidental Discovery
├── Scan architecture diagrams
├── Scan process documentation
├── Scan infrastructure docs
└── Flag as "Mentioned_In_Passing"

PASS 1c: Verification
├── Compare recorded count vs mentioned count
├── If gap exists → flag_gap()
└── Generate questions for missing apps
```

### Output
- `applications[]` list in AnalysisStore
- Each app gets unique ID: APP-001, APP-002, etc.

---

## 5. Phase 2: Capability Coverage Analysis

### Purpose
Answer: "What business capabilities are covered, and what's missing?"

This is **checklist-driven** - we don't just report what we found, we check against what a business SHOULD have.

### The 13 Business Capability Areas

| Capability | Typical Apps | Criticality |
|------------|--------------|-------------|
| `finance_accounting` | ERP, GL, AP, AR, Treasury | Critical |
| `human_resources` | HRIS, Payroll, Benefits, Recruiting | Critical |
| `sales_crm` | CRM, CPQ, Sales Enablement | High |
| `marketing` | Marketing Automation, CMS, Email | Medium |
| `operations_supply_chain` | SCM, Inventory, WMS, MES | High* |
| `it_infrastructure` | ITSM, Monitoring, CMDB | High |
| `identity_security` | IdP/SSO, PAM, SIEM, EDR | Critical |
| `collaboration` | Email, Chat, Video, Docs | High |
| `data_analytics` | BI, Data Warehouse, ETL | Medium |
| `legal_compliance` | CLM, GRC, Policy Mgmt | Medium |
| `customer_service` | Help Desk, Knowledge Base | Medium |
| `ecommerce_digital` | E-commerce Platform | Medium* |
| `industry_specific` | Vertical-specific apps | Varies |

*Varies by industry

### Tool Used: `record_capability_coverage`

Called **once per capability area** (13 calls minimum).

### Fields Captured

| Field | Purpose |
|-------|---------|
| `capability_area` | Which of the 13 areas |
| `coverage_status` | Fully_Documented, Partially_Documented, Not_Found, Not_Applicable |
| `business_relevance` | How important for THIS company |
| `applications_found[]` | Which apps cover this (linked to APP-xxx IDs) |
| `expected_but_missing[]` | Apps we'd expect but didn't find |
| `follow_up_questions[]` | Questions for seller about gaps |
| `capability_maturity` | Nascent, Developing, Established, Optimized |

### Gap Detection Logic

```
IF coverage_status = "Not_Found"
   AND business_relevance IN ("Critical", "High")
THEN
   MUST generate follow_up_questions
   System auto-generates default question if none provided
```

### Output
- `capability_coverage[]` list in AnalysisStore
- Each gets unique ID: CAP-001, CAP-002, etc.
- Aggregated follow-up questions for gaps

---

## 6. Phase 3: Four-Lens Analysis

### The Four Lenses

```
┌────────────────────────────────────────────────────────────────┐
│  LENS 1           LENS 2          LENS 3          LENS 4       │
│  Current State    Risks           Strategic       Work Items   │
│                                   Considerations               │
├────────────────────────────────────────────────────────────────┤
│  What exists      What could      What it means   What to do   │
│  today?           go wrong?       for the deal?   about it?    │
└────────────────────────────────────────────────────────────────┘
```

### Lens 1: Current State

**Tool:** `create_current_state_entry`

Portfolio-level observations:
- Overall portfolio health and maturity
- Hosting model distribution (60% SaaS, 30% on-prem, 10% hybrid)
- Vendor concentration (40% Microsoft, 25% Salesforce, etc.)
- Technical debt overview

### Lens 2: Risks

**Tool:** `identify_risk`

**Critical distinction:** `integration_dependent` flag

| integration_dependent | Meaning | Example |
|----------------------|---------|---------|
| `false` | Risk exists TODAY, no integration needed | SAP ECC on unsupported version |
| `true` | Risk only materializes during integration | Data migration complexity |

This ensures we highlight risks that exist even if the deal doesn't close.

### Lens 3: Strategic Considerations

**Tool:** `create_strategic_consideration`

**Required fields:**
- `follow_up_question` - What question does this raise?
- `question_target` - Who should answer? (Target_Management, Buyer_IT, etc.)

Every strategic consideration MUST generate an actionable question.

### Lens 4: Work Items

**Tool:** `create_work_item`

Phased approach:

| Phase | Timing | Application Examples |
|-------|--------|---------------------|
| Day_1 | Close | Ensure critical apps accessible |
| Day_100 | First 100 days | Quick wins, stabilization |
| Post_100 | Beyond 100 days | Full rationalization |
| Optional | If time/budget | Nice-to-haves |

Note: Most application work is Day_100 or Post_100. Day_1 is typically identity/access focused.

---

## 7. Phase 4: Buyer Comparison (When Applicable)

### Purpose
When buyer environment information is available, identify overlaps and surface questions - NOT prescribe decisions.

### Design Philosophy
> "Each deal is unique. The tool surfaces WHAT overlaps exist and generates QUESTIONS/CONSIDERATIONS for the deal team. It doesn't prescribe decisions, timelines, or synergies - those are judgment calls."

### Step 1: Record Buyer Applications

**Tool:** `record_buyer_application`

Minimal fields - just enough for overlap detection:
- `application_name`, `vendor`, `application_category`
- `capability_areas_covered`
- `information_source` (how we know about it)

### Step 2: Identify Overlaps

**Tool:** `record_application_overlap`

**Overlap Types:**

| Type | Meaning | Typical Question |
|------|---------|------------------|
| `Same_Product` | Both have Salesforce | How customized are each? |
| `Same_Category_Different_Vendor` | Target: SAP, Buyer: Oracle | Which is strategic platform? |
| `Target_Only` | Target has app buyer lacks | Keep, replace, or retire? |
| `Complementary` | Different apps, both needed | Integration requirements? |

**Required Outputs:**
- `considerations` - What does this overlap mean for the deal?
- `follow_up_questions[]` - What needs to be answered?

**What We Don't Do:**
- ❌ Prescribe "Consolidate_To_Buyer" decisions
- ❌ Estimate timelines like "Day_100"
- ❌ Quantify synergies
- ❌ Assign complexity scores

---

## 8. Outputs - What the Process Produces

### Primary Data Structures

| Structure | Purpose | ID Format |
|-----------|---------|-----------|
| `applications[]` | Individual app records | APP-001 |
| `capability_coverage[]` | Capability assessments | CAP-001 |
| `buyer_applications[]` | Buyer's apps (when available) | BAPP-001 |
| `application_overlaps[]` | Overlap analyses | OVL-001 |
| `current_state[]` | Portfolio observations | CS-001 |
| `risks[]` | Identified risks | R-001 |
| `strategic_considerations[]` | Deal implications | SC-001 |
| `work_items[]` | Phased actions | WI-001 |
| `gaps[]` | Documentation gaps | G-001 |
| `questions[]` | Follow-up questions | Q-001 |

### Aggregated Outputs

**Completeness Report** (`get_completeness_report()`):
```
=====================================================
APPLICATION ANALYSIS COMPLETENESS REPORT
=====================================================

Overall Status: COMPLETE_WITH_WARNINGS

APPLICATION INVENTORY:
  Applications Recorded: 47
  Applications Without Evidence: 3

CAPABILITY COVERAGE:
  Total Capability Areas: 13
  Areas Assessed: 13
  Completeness: 100%

MISSING CAPABILITY ASSESSMENTS:
  (none)

WARNINGS:
  [?] Applications without evidence: CustomApp1, CustomApp2, LegacyTool

FOLLOW-UP QUESTIONS GENERATED: 23
CRITICAL GAPS: identity_security (no SIEM found)
```

**Integration Report** (`get_integration_report()`):
```
=====================================================
TARGET vs BUYER APPLICATION OVERLAP REPORT
=====================================================

Total Overlaps Analyzed: 15

OVERLAP BY TYPE:
  Same_Product: 5
  Same_Category_Different_Vendor: 4
  Target_Only: 6

KEY CONSIDERATIONS:
  [Same_Product] Salesforce vs Salesforce
      Both companies use Salesforce - consolidation opportunity...

FOLLOW-UP QUESTIONS (23):
  - [Buyer_IT] How customized is buyer's Salesforce instance?
  - [Target_Management] What is the Salesforce contract expiry date?
```

### Follow-Up Questions (Aggregated)

Questions are collected from multiple sources:
1. `capability_coverage[].follow_up_questions` - Gaps in capability coverage
2. `strategic_considerations[].follow_up_question` - Strategic implications
3. `application_overlaps[].follow_up_questions` - Buyer comparison questions
4. `questions[]` - Direct questions flagged during analysis

All are aggregated via `get_all_follow_up_questions()` and prioritized.

---

## 9. Data Flow & Storage

### AnalysisStore Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AnalysisStore                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  APPLICATION INVENTORY                                       │
│  ├── applications: List[Dict]           # APP-001, etc.     │
│  ├── capability_coverage: List[Dict]    # CAP-001, etc.     │
│  └── (data classification embedded in each app)             │
│                                                              │
│  BUYER COMPARISON                                            │
│  ├── buyer_applications: List[Dict]     # BAPP-001, etc.    │
│  └── application_overlaps: List[Dict]   # OVL-001, etc.     │
│                                                              │
│  FOUR-LENS FRAMEWORK                                         │
│  ├── current_state: List[Dict]          # CS-001, etc.      │
│  ├── risks: List[Dict]                  # R-001, etc.       │
│  ├── strategic_considerations: List[Dict] # SC-001, etc.    │
│  └── work_items: List[Dict]             # WI-001, etc.      │
│                                                              │
│  SUPPORTING                                                  │
│  ├── gaps: List[Dict]                   # G-001, etc.       │
│  ├── questions: List[Dict]              # Q-001, etc.       │
│  ├── assumptions: List[Dict]            # A-001, etc.       │
│  └── recommendations: List[Dict]        # REC-001, etc.     │
│                                                              │
│  ID COUNTERS                                                 │
│  └── _id_counters: Dict[str, int]       # Sequential IDs    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Tool Execution Flow

```
Agent calls tool
       │
       ▼
┌──────────────────┐
│  execute_tool()  │
├──────────────────┤
│ 1. Validate input│
│ 2. Check for     │
│    duplicates    │
│ 3. Generate ID   │
│ 4. Add defaults  │
│ 5. Store finding │
│ 6. Return status │
└──────────────────┘
       │
       ▼
   Store result
       │
       ▼
 Return to agent
```

### Duplicate Detection

The system prevents duplicate entries:
- Applications: Same name + vendor = duplicate
- Capability Coverage: One record per capability area
- Overlaps: Same target_app + buyer_app = duplicate

---

## 10. Quality Controls & Anti-Hallucination

### Evidence Requirements

Every finding must cite source evidence:

```python
"source_evidence": {
    "document_reference": "Application Inventory v2.xlsx",
    "page_or_section": "Sheet: Core Applications, Row 15",
    "exact_quote": "SAP ECC 6.0, EHP 8, deployed 2015, 450 users",
    "evidence_type": "direct_statement",  # or "logical_inference"
    "confidence_level": "high"  # high, medium, low
}
```

### Confidence Levels

| Level | Meaning | When to Use |
|-------|---------|-------------|
| `high` | Direct statement in document | Explicit mention with details |
| `medium` | Reasonable inference | Implied by context |
| `low` | Assumption or sparse info | Mentioned in passing, no details |

### Discovery Source Tracking

| Source | Reliability | Treatment |
|--------|-------------|-----------|
| `App_Inventory_Document` | High | Primary source of truth |
| `Architecture_Diagram` | High | Integration context |
| `Vendor_Contract` | High | Licensing details |
| `Mentioned_In_Passing` | Medium | Flag for follow-up |
| `Inferred_From_Context` | Low | Requires validation |
| `Assumption` | Low | Must be verified |

### Validation Checks

`validate_application_completeness()` checks:
1. ✓ Applications recorded vs. counts mentioned
2. ✓ All 13 capability areas assessed
3. ✓ Critical capabilities have coverage
4. ✓ Gaps have follow-up questions
5. ✓ Evidence provided for findings

---

## 11. Integration with Other Domains

### Cross-Domain Data Flows

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ APPLICATIONS│────▶│INFRASTRUCTURE│────▶│   NETWORK   │
│             │     │             │     │             │
│ "App X runs │     │ "Server Y   │     │ "Requires   │
│  on Server Y"│     │  hosts App X"│     │  port 443"  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  IDENTITY   │     │CYBERSECURITY│     │ORGANIZATION │
│             │     │             │     │             │
│ "App X uses │     │ "App X is   │     │ "IT team    │
│  Okta SSO"  │     │  PCI scope" │     │  supports X"│
└─────────────┘     └─────────────┘     └─────────────┘
```

### How Applications Feeds Other Domains

| To Domain | What We Provide | How It's Used |
|-----------|-----------------|---------------|
| **Infrastructure** | App hosting requirements | Server/cloud capacity planning |
| **Network** | Integration endpoints | Network path analysis |
| **Identity** | SSO/MFA requirements | Access management scope |
| **Cybersecurity** | Data classification (PII/PHI/PCI) | Compliance scope |
| **Organization** | App ownership, user counts | Staffing analysis |

### How Other Domains Feed Applications

| From Domain | What They Provide | How We Use It |
|-------------|-------------------|---------------|
| **Infrastructure** | Server inventory | Where apps are hosted |
| **Identity** | IdP/directory info | Authentication architecture |
| **Cybersecurity** | Security tool inventory | Security app coverage |
| **Organization** | IT structure | App ownership mapping |

---

## 12. Downstream Consumers

### Who Uses Application Analysis Output

```
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION ANALYSIS                        │
│                       OUTPUT                                 │
└─────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  COSTING    │ │ COORDINATOR │ │   REPORT    │
    │   AGENT     │ │             │ │  GENERATOR  │
    ├─────────────┤ ├─────────────┤ ├─────────────┤
    │ Uses app    │ │ Aggregates  │ │ Produces    │
    │ inventory   │ │ cross-domain│ │ final DD    │
    │ for cost    │ │ findings    │ │ report      │
    │ estimates   │ │             │ │             │
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ License     │ │ Executive   │ │ Investment  │
    │ true-up     │ │ Summary     │ │ Committee   │
    │ estimates   │ │             │ │ Deck        │
    └─────────────┘ └─────────────┘ └─────────────┘
```

### Costing Agent Handoff

The Applications agent does NOT estimate costs. It provides:
- App counts by category, hosting model, criticality
- License types and contract information (if available)
- Integration complexity indicators
- Customization levels

The Costing Agent uses this to estimate:
- License consolidation savings
- Migration costs
- Integration development costs
- Support cost changes

### Report Generator Inputs

The report generator pulls:
- Application inventory summary
- Capability coverage matrix
- Critical gaps and questions
- Overlap analysis (if available)
- Risk summary

---

## 13. Key Decision Points

### Agent Decision Points

| Decision Point | Options | Guidance |
|----------------|---------|----------|
| **App mentioned but sparse info** | Record with low confidence OR flag as gap | Record it, flag discovery_source, generate follow-up question |
| **Capability not applicable** | Mark "Not_Applicable" OR skip | Always record with "Not_Applicable" - explicit is better than implicit |
| **Buyer info source reliability** | Trust OR flag for validation | Include `information_source` and note confidence |
| **Risk: standalone or integration?** | Flag appropriately | If risk exists today without integration, it's standalone |

### Human Decision Points

The system surfaces questions but doesn't decide:

| Question Type | Who Decides | Example |
|---------------|-------------|---------|
| App rationalization | Deal team | "Consolidate Salesforce instances?" |
| TSA requirements | Legal/Deal team | "6 month TSA needed?" |
| Integration timeline | PMO/IT | "Day 100 or Year 1?" |
| Synergy quantification | Finance | "$500K license savings?" |

---

## 14. Areas for Leadership Attention

### Process Strengths

1. **Complete Enumeration** - Forces individual app capture, prevents summarization
2. **Checklist-Driven** - Ensures gaps are identified even when docs are incomplete
3. **Evidence-Based** - Every finding must cite source, reducing hallucination risk
4. **Questions Over Decisions** - Surfaces considerations without being prescriptive
5. **Cost Separation** - Domain analysis is fact-based; costing is separate

### Potential Concerns / Discussion Points

#### 1. Completeness Validation
**Current State:** System checks if recorded apps match mentioned counts
**Potential Gap:** What if document says "47 applications" but only lists 30?
**Mitigation:** `flag_gap()` is called, follow-up question generated
**Discussion:** Is this sufficient? Should we block completion until resolved?

#### 2. Buyer Information Quality
**Current State:** Buyer apps recorded with `information_source` flag
**Potential Gap:** "Assumption" or "Public_Information" sources may be unreliable
**Mitigation:** Questions are generated to validate assumptions
**Discussion:** Should we weight overlap analysis differently based on source reliability?

#### 3. Cross-Domain Consistency
**Current State:** Apps mentioned in other domains should be captured
**Potential Gap:** Infrastructure domain mentions "SAP server" - is SAP recorded in Applications?
**Mitigation:** Incidental discovery pass scans other docs
**Discussion:** Should there be explicit cross-domain validation?

#### 4. Evidence Quality
**Current State:** `exact_quote` required in source_evidence
**Potential Gap:** Quotes may be taken out of context
**Mitigation:** `evidence_type` distinguishes "direct_statement" from "logical_inference"
**Discussion:** Should we require page numbers? Document timestamps?

#### 5. Capability Checklist Completeness
**Current State:** 13 capability areas defined
**Potential Gap:** Industry-specific capabilities may be missing
**Mitigation:** `industry_specific` category exists as catch-all
**Discussion:** Should checklist be configurable per deal/industry?

#### 6. Data Classification Scope
**Current State:** Simplified to PII/PHI/PCI/Financial + data residency
**Potential Gap:** Other data types may matter (trade secrets, M&A data)
**Mitigation:** Free-text notes field available
**Discussion:** Is the simplified scope sufficient for all deal types?

### Recommended Review Items

1. **Sample an analysis run** - Walk through a real output to verify completeness
2. **Test gap scenarios** - Deliberately provide incomplete docs, verify gaps flagged
3. **Buyer comparison edge cases** - What if buyer has 100 apps vs target's 10?
4. **Question quality** - Are generated questions actually actionable?
5. **Cross-domain handoff** - Verify data flows correctly to Costing Agent

---

## Appendix A: Tool Quick Reference

| Tool | Purpose | Key Required Fields |
|------|---------|---------------------|
| `record_application` | Capture individual app | name, vendor, category, hosting, criticality, source_evidence |
| `record_capability_coverage` | Assess capability area | capability_area, coverage_status, business_relevance |
| `record_buyer_application` | Capture buyer's app | name, vendor, category, capabilities, source |
| `record_application_overlap` | Compare target vs buyer | target_app, overlap_type, considerations, follow_up_questions |
| `create_current_state_entry` | Document what exists | domain, category, summary, maturity |
| `identify_risk` | Flag a risk | domain, risk, severity, integration_dependent |
| `create_strategic_consideration` | Deal implication | consideration, follow_up_question, question_target |
| `create_work_item` | Define action | title, phase, description |
| `flag_gap` | Missing information | domain, gap, suggested_source |

---

## Appendix B: ID Format Reference

| Type | Prefix | Example |
|------|--------|---------|
| Application | APP | APP-001, APP-002 |
| Capability Coverage | CAP | CAP-001, CAP-002 |
| Buyer Application | BAPP | BAPP-001, BAPP-002 |
| Overlap | OVL | OVL-001, OVL-002 |
| Current State | CS | CS-001, CS-002 |
| Risk | R | R-001, R-002 |
| Strategic Consideration | SC | SC-001, SC-002 |
| Work Item | WI | WI-001, WI-002 |
| Gap | G | G-001, G-002 |
| Question | Q | Q-001, Q-002 |
| Assumption | A | A-001, A-002 |
| Recommendation | REC | REC-001, REC-002 |

---

**Document prepared for leadership review.**
**Questions or feedback:** [To be added]
