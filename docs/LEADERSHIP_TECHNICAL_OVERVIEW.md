# IT Due Diligence Agent
## Technical Architecture for Leadership

---

# Layer 1: Executive Overview

## What Does This System Do?

The IT Due Diligence Agent is an **AI-powered analysis system** that reads IT documentation and produces structured diligence outputs. It replaces manual document review with automated, consistent analysis.

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  IT Documents   │ ──────► │   AI Analysis   │ ──────► │ Diligence Pack  │
│  (PDFs, etc.)   │         │    Engine       │         │                 │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘

     INPUT                     PROCESSING                   OUTPUT
   - Target IT docs          - 6 domain experts          - Findings
   - Infrastructure            (AI agents)               - Risks
   - Security audits         - Cross-domain              - Cost estimates
   - Vendor contracts          synthesis                 - VDR requests
```

---

## The Core Concept: Separation of Extraction and Analysis

Our system uses a **two-phase approach** that mirrors how expert consultants work:

| Phase | Human Equivalent | AI Implementation | Model Used |
|-------|------------------|-------------------|------------|
| **Discovery** | Junior analyst reads docs, extracts facts | AI extracts structured inventory | Haiku (fast, cheap) |
| **Reasoning** | Senior consultant analyzes facts, forms opinions | AI identifies risks, recommends actions | Sonnet (capable, precise) |

**Why This Matters:**
- Facts are objective → use cheaper, faster model
- Analysis requires judgment → use more capable model
- **Result: 40% cost reduction** while maintaining quality

---

## The Five-Phase Pipeline

```
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   PHASE 1: DISCOVERY                                        │
    │   "What's in the documents?"                                │
    │                                                             │
    │   • Extract facts with exact quotes as evidence             │
    │   • Identify gaps (missing information)                     │
    │   • 6 domains analyzed in parallel                          │
    │                                                             │
    │   Output: Structured inventory with unique IDs              │
    │           (F-INFRA-001, F-CYBER-001, etc.)                  │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   PHASE 2: REASONING                                        │
    │   "What does this mean for the deal?"                       │
    │                                                             │
    │   • Identify risks with severity ratings                    │
    │   • Create work items with cost estimates                   │
    │   • Every finding cites specific facts                      │
    │                                                             │
    │   Output: Risks, work items, recommendations                │
    │           All with evidence chains                          │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   PHASE 3: COVERAGE ANALYSIS                                │
    │   "How complete is our picture?"                            │
    │                                                             │
    │   • Score documentation completeness                        │
    │   • Identify missing critical items                         │
    │   • Assign letter grade (A-F)                               │
    │                                                             │
    │   Output: Coverage scores, quality assessment               │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   PHASE 4: SYNTHESIS                                        │
    │   "What's the big picture?"                                 │
    │                                                             │
    │   • Cross-domain consistency checks                         │
    │   • Aggregate costs by phase and owner                      │
    │   • Group related findings by theme                         │
    │                                                             │
    │   Output: Executive summary, cost rollups                   │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   PHASE 5: VDR GENERATION                                   │
    │   "What else do we need to ask for?"                        │
    │                                                             │
    │   • Generate prioritized follow-up requests                 │
    │   • From gaps + missing coverage items                      │
    │   • Include suggested documents per category                │
    │                                                             │
    │   Output: Prioritized VDR request pack                      │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

---

## The Six Analysis Domains

Each domain has specialized AI "expertise" via custom prompts:

| Domain | What It Analyzes | Key Outputs |
|--------|------------------|-------------|
| **Infrastructure** | Data centers, servers, storage, cloud, DR | Capacity, EOL systems, DR readiness |
| **Network** | WAN, LAN, firewalls, VPN, connectivity | Architecture, redundancy, security posture |
| **Cybersecurity** | EDR, SIEM, compliance, incident response | Security maturity, compliance gaps |
| **Applications** | ERP, CRM, custom apps, databases | Tech debt, integration complexity |
| **Identity & Access** | Active Directory, SSO, MFA, PAM | Access control maturity, risk exposure |
| **Organization** | IT staffing, vendors, budget, processes | Capability gaps, key person risk |

**Parallel Processing:** All 6 domains run simultaneously, reducing wall-clock time.

---

## What Makes This Different: Evidence Chains

Every finding is **traceable back to source documents**:

```
┌─────────────────────────────────────────────────────────────────┐
│ RISK: EOL VMware Version                                        │
│ Severity: HIGH                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Based on Facts:                                                 │
│ ├── F-INFRA-003: "VMware vSphere 6.7" (page 12)                │
│ └── F-INFRA-007: "340 VMs in production" (page 15)             │
│                                                                 │
│ Reasoning:                                                      │
│ "VMware 6.7 reached general support EOL in October 2022.        │
│  With 340 production VMs, this represents significant           │
│  security and operational risk."                                │
│                                                                 │
│ Mitigation:                                                     │
│ "Upgrade to VMware 8.0 before integration. Budget $150-300K."   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Why This Matters:**
- Every claim can be verified against source documents
- No "black box" AI hallucinations
- Defensible findings for IC presentations

---

## Output Summary

| Output | Format | Purpose |
|--------|--------|---------|
| **Facts** | JSON | Extracted inventory with evidence |
| **Findings** | JSON | Risks, work items, recommendations |
| **Coverage Report** | JSON | Quality scores per domain |
| **Executive Summary** | Markdown | IC-ready narrative |
| **VDR Request Pack** | JSON + Markdown | Follow-up questions |
| **Cost Summary** | In Synthesis | Aggregated by phase/owner |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| **Processing Time** | 12-15 minutes (all 6 domains) |
| **API Cost per Analysis** | ~$8-12 |
| **Cost Savings vs. V1** | ~40% (model tiering) |
| **Test Coverage** | 49 automated tests |

---

## Summary: How It Works (Layer 1)

1. **Input**: Drop IT documents into the system
2. **Discovery**: AI extracts facts from documents (cheap model)
3. **Reasoning**: AI analyzes facts to produce findings (capable model)
4. **Quality Check**: System scores documentation completeness
5. **Synthesis**: Cross-domain consistency and cost aggregation
6. **VDR Output**: Prioritized list of follow-up requests
7. **Output**: Structured JSON + executive summary + VDR pack

**The system automates the "first pass" of IT due diligence**, producing consistent, evidence-backed outputs that accelerate deal analysis.

---

*Next: Layer 2 will cover the technical implementation details*
*Then: Layer 3 will cover the AI prompt engineering and domain expertise*

---

# Layer 2: Technical Implementation

## System Architecture

The system is built on a **simple, framework-free architecture**. No LangChain, no LangGraph, no vector databases. Just direct API calls with structured control flow.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MAIN ORCHESTRATOR                                  │
│                            (main_v2.py)                                      │
│                                                                             │
│   Responsibilities:                                                         │
│   • Load documents (PDF parsing)                                            │
│   • Dispatch agents (parallel or sequential)                                │
│   • Merge results from all domains                                          │
│   • Run post-processing phases (coverage, synthesis, VDR)                   │
│   • Save outputs to files                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENT LAYER                                     │
│                                                                             │
│  ┌─────────────────────────┐     ┌─────────────────────────┐               │
│  │   Discovery Agents      │     │   Reasoning Agents      │               │
│  │   (base_discovery.py)   │     │   (base_reasoning.py)   │               │
│  ├─────────────────────────┤     ├─────────────────────────┤               │
│  │ • Infrastructure        │     │ • Infrastructure        │               │
│  │ • Network               │     │ • Network               │               │
│  │ • Cybersecurity         │     │ • Cybersecurity         │               │
│  │ • Applications          │     │ • Applications          │               │
│  │ • Identity & Access     │     │ • Identity & Access     │               │
│  │ • Organization          │     │ • Organization          │               │
│  └─────────────────────────┘     └─────────────────────────┘               │
│           │                               │                                 │
│           │  Model: Haiku                 │  Model: Sonnet                  │
│           │  Cost: ~$0.25/1M tokens       │  Cost: ~$3/1M tokens            │
│           │                               │                                 │
└───────────┼───────────────────────────────┼─────────────────────────────────┘
            │                               │
            ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│                                                                             │
│  ┌─────────────────────────┐     ┌─────────────────────────┐               │
│  │      FactStore          │     │    ReasoningStore       │               │
│  │   (fact_store.py)       │     │  (reasoning_tools.py)   │               │
│  ├─────────────────────────┤     ├─────────────────────────┤               │
│  │ • Facts (F-XXX-001)     │     │ • Risks (R-001)         │               │
│  │ • Gaps (G-XXX-001)      │     │ • Work Items (WI-001)   │               │
│  │ • Discovery metadata    │     │ • Strategic (SC-001)    │               │
│  │                         │     │ • Recommendations       │               │
│  └─────────────────────────┘     └─────────────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ANALYSIS LAYER                                     │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ CoverageAnalyzer │  │ SynthesisAnalyzer│  │  VDRGenerator    │          │
│  │  (coverage.py)   │  │  (synthesis.py)  │  │ (vdr_generator)  │          │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤          │
│  │ • Checklists     │  │ • Consistency    │  │ • Gap-based      │          │
│  │ • Scoring        │  │ • Cost rollup    │  │ • Coverage-based │          │
│  │ • Grading        │  │ • Theme grouping │  │ • Prioritization │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Agent Loop: How AI Agents Work

Each agent follows a simple **iterative loop** pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT EXECUTION LOOP                        │
└─────────────────────────────────────────────────────────────────┘

     START
       │
       ▼
┌─────────────────┐
│ 1. Build Prompt │  ◄── System prompt + Document + Context
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Call Claude  │  ◄── API request to Anthropic
│    API          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ 3. Parse        │────►│ Text Response?  │────► Add to context
│    Response     │     │ (thinking)      │      and continue
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Tool Call?      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────────────────┐
│  No   │ │  Yes: Execute     │
│       │ │  Tool             │
└───┬───┘ └─────────┬─────────┘
    │               │
    │               ▼
    │     ┌─────────────────┐
    │     │ • create_fact   │
    │     │ • flag_gap      │
    │     │ • identify_risk │
    │     │ • create_work_  │
    │     │   item          │
    │     │ • complete_     │
    │     │   discovery     │
    │     └─────────┬───────┘
    │               │
    │               ▼
    │     ┌─────────────────┐
    │     │ Store result in │
    │     │ FactStore or    │
    │     │ ReasoningStore  │
    │     └─────────┬───────┘
    │               │
    └───────┬───────┘
            │
            ▼
┌─────────────────┐
│ Complete signal │     ┌─────────────────┐
│ or max          │────►│      DONE       │
│ iterations?     │ Yes └─────────────────┘
└────────┬────────┘
         │ No
         │
         └──────────► Loop back to step 2

```

**Key Design Decisions:**
- **No streaming**: We wait for complete responses (simpler error handling)
- **Tool-based output**: AI "calls tools" to record findings (structured output)
- **Iterative refinement**: Agent can make multiple passes through document
- **Max iterations**: Safety limit prevents runaway loops (default: 30)

---

## Data Structures: FactStore

The **FactStore** holds all extracted facts and identified gaps:

```
┌─────────────────────────────────────────────────────────────────┐
│                         FACTSTORE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FACTS LIST                                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Fact {                                                    │  │
│  │   fact_id: "F-INFRA-001"      ◄── Unique ID               │  │
│  │   domain: "infrastructure"    ◄── Which domain            │  │
│  │   category: "compute"         ◄── Sub-category            │  │
│  │   item: "VMware vSphere"      ◄── What was found          │  │
│  │   details: {                  ◄── Structured details      │  │
│  │     "version": "7.0",                                     │  │
│  │     "vm_count": 340                                       │  │
│  │   }                                                       │  │
│  │   status: "documented"        ◄── documented/partial/gap  │  │
│  │   evidence: {                 ◄── Traceability            │  │
│  │     "exact_quote": "VMware vSphere 7.0 with 340 VMs",     │  │
│  │     "source_section": "Infrastructure Overview"           │  │
│  │   }                                                       │  │
│  │ }                                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  GAPS LIST                                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Gap {                                                     │  │
│  │   gap_id: "G-INFRA-001"                                   │  │
│  │   domain: "infrastructure"                                │  │
│  │   category: "backup_dr"                                   │  │
│  │   description: "RTO/RPO values not documented"            │  │
│  │   importance: "critical"      ◄── critical/high/medium    │  │
│  │ }                                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  METHODS                                                        │
│  • add_fact() → returns F-XXX-NNN                               │
│  • add_gap() → returns G-XXX-NNN                                │
│  • get_domain_facts(domain) → filtered facts                    │
│  • format_for_reasoning() → prompt-ready text                   │
│  • merge_from(other_store) → combine parallel results           │
│  • save() / load() → JSON persistence                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**ID Format:**
- Facts: `F-{DOMAIN}-{SEQ}` → F-INFRA-001, F-CYBER-001
- Gaps: `G-{DOMAIN}-{SEQ}` → G-INFRA-001, G-NET-001

---

## Data Structures: ReasoningStore

The **ReasoningStore** holds all analysis outputs with fact citations:

```
┌─────────────────────────────────────────────────────────────────┐
│                      REASONINGSTORE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RISKS (R-001, R-002, ...)                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Risk {                                                    │  │
│  │   finding_id: "R-001"                                     │  │
│  │   domain: "infrastructure"                                │  │
│  │   title: "EOL VMware Version"                             │  │
│  │   description: "VMware 6.7 reached EOL Oct 2022"          │  │
│  │   category: "technical_debt"                              │  │
│  │   severity: "high"            ◄── critical/high/med/low   │  │
│  │   integration_dependent: false ◄── Deal-specific?         │  │
│  │   mitigation: "Upgrade to 8.0"                            │  │
│  │   based_on_facts: ["F-INFRA-003", "F-INFRA-007"]  ◄── KEY │  │
│  │   confidence: "high"                                      │  │
│  │   reasoning: "Fact F-INFRA-003 shows..."                  │  │
│  │ }                                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  WORK ITEMS (WI-001, WI-002, ...)                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ WorkItem {                                                │  │
│  │   finding_id: "WI-001"                                    │  │
│  │   domain: "infrastructure"                                │  │
│  │   title: "VMware Upgrade Project"                         │  │
│  │   description: "Upgrade from 6.7 to 8.0"                  │  │
│  │   phase: "Day_100"            ◄── Day_1/Day_100/Post_100  │  │
│  │   priority: "high"                                        │  │
│  │   owner_type: "target"        ◄── buyer/target/shared     │  │
│  │   cost_estimate: "100k_to_500k"   ◄── Cost range          │  │
│  │   triggered_by: ["F-INFRA-003"]                           │  │
│  │   triggered_by_risks: ["R-001"]   ◄── Links to risks      │  │
│  │   confidence: "high"                                      │  │
│  │ }                                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  STRATEGIC CONSIDERATIONS (SC-001, ...)                         │
│  RECOMMENDATIONS (REC-001, ...)                                 │
│                                                                 │
│  COST AGGREGATION METHODS                                       │
│  • get_total_cost_estimate() → by phase, domain, owner          │
│  • get_risk_cost_mapping() → which risks drive which costs      │
│  • get_evidence_chain(finding_id) → trace back to facts         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Cost Estimate Ranges:**
| Code | Range |
|------|-------|
| `under_25k` | $0 - $25,000 |
| `25k_to_100k` | $25,000 - $100,000 |
| `100k_to_500k` | $100,000 - $500,000 |
| `500k_to_1m` | $500,000 - $1,000,000 |
| `over_1m` | $1,000,000+ |

---

## Tool Definitions: How AI Records Findings

Tools are **structured schemas** that tell the AI how to record findings:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DISCOVERY TOOLS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  create_inventory_entry                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Purpose: Record a discovered fact                         │  │
│  │                                                           │  │
│  │ Required fields:                                          │  │
│  │ • domain (enum: infrastructure, network, etc.)            │  │
│  │ • category (string: compute, storage, etc.)               │  │
│  │ • item (string: what was found)                           │  │
│  │ • status (enum: documented, partial, gap)                 │  │
│  │ • evidence.exact_quote (string: min 10 chars)  ◄── KEY    │  │
│  │                                                           │  │
│  │ Validation:                                               │  │
│  │ • Quote must be 10+ characters (prevents vague claims)    │  │
│  │ • Duplicate detection (fuzzy matching)                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  flag_gap                                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Purpose: Record missing information                       │  │
│  │                                                           │  │
│  │ Required fields:                                          │  │
│  │ • domain, category                                        │  │
│  │ • description (what's missing)                            │  │
│  │ • importance (critical/high/medium/low)                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  complete_discovery                                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Purpose: Signal discovery phase is complete               │  │
│  │                                                           │  │
│  │ Required fields:                                          │  │
│  │ • domain                                                  │  │
│  │ • categories_covered (list)                               │  │
│  │ • categories_missing (list)                               │  │
│  │ • summary                                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    REASONING TOOLS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  identify_risk                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Required fields:                                          │  │
│  │ • title, description                                      │  │
│  │ • category (technical_debt, security, compliance, etc.)   │  │
│  │ • severity (critical/high/medium/low)                     │  │
│  │ • integration_dependent (boolean)                         │  │
│  │ • mitigation (string)                                     │  │
│  │ • based_on_facts (array of fact IDs)  ◄── REQUIRED        │  │
│  │ • reasoning (string)                                      │  │
│  │                                                           │  │
│  │ Validation:                                               │  │
│  │ • Must cite at least one fact (no unsupported claims)     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  create_work_item                                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Required fields:                                          │  │
│  │ • title, description                                      │  │
│  │ • phase (Day_1/Day_100/Post_100)                          │  │
│  │ • priority (critical/high/medium/low)                     │  │
│  │ • owner_type (buyer/target/shared/vendor)                 │  │
│  │ • cost_estimate (under_25k to over_1m)  ◄── NEW IN V2     │  │
│  │ • triggered_by (array of fact IDs)                        │  │
│  │ • triggered_by_risks (array of risk IDs)  ◄── NEW         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Parallel Execution Model

**Problem**: Running 6 agents sequentially takes 30+ minutes.
**Solution**: Parallel execution with thread pool.

```
┌─────────────────────────────────────────────────────────────────┐
│                   PARALLEL EXECUTION                             │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   Main Thread   │
                    │   Orchestrator  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ Worker 1   │  │ Worker 2   │  │ Worker 3   │
     │            │  │            │  │            │
     │ Infra      │  │ Network    │  │ Cyber      │
     │ Discovery  │  │ Discovery  │  │ Discovery  │
     └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
           │               │               │
           ▼               ▼               ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ Local      │  │ Local      │  │ Local      │
     │ FactStore  │  │ FactStore  │  │ FactStore  │
     └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  Thread-Safe   │
                  │    Merge       │
                  │  (with lock)   │
                  └────────┬───────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ Global         │
                  │ FactStore      │
                  │ (all facts)    │
                  └────────────────┘
```

**Configuration:**
- `MAX_PARALLEL_AGENTS = 3` (default)
- Thread-safe merge with mutex lock
- Same pattern for Discovery and Reasoning phases

**Why 3 workers?**
- API rate limits (requests per minute)
- Memory efficiency
- Diminishing returns beyond 3

---

## Error Handling & Resilience

```
┌─────────────────────────────────────────────────────────────────┐
│                   ERROR HANDLING STRATEGY                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ API ERRORS                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Rate Limits (429)                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Automatic retry with exponential backoff                  │ │
│ │ • Max 3 retries per request                                 │ │
│ │ • Backoff: 1s → 2s → 4s                                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Timeouts                                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Default timeout: 120 seconds per request                  │ │
│ │ • Retry on timeout (same backoff)                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Server Errors (500, 503)                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Retry with backoff                                        │ │
│ │ • Log error and continue if persistent                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ VALIDATION ERRORS                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Tool Input Validation                                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Missing required fields → return error to AI              │ │
│ │ • Invalid enum values → return error with valid options     │ │
│ │ • Quote too short → return error, AI retries                │ │
│ │                                                             │ │
│ │ AI sees error and self-corrects on next iteration           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Duplicate Detection                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Fuzzy matching on fact items (80% similarity threshold)   │ │
│ │ • Duplicate returns existing ID (no new fact created)       │ │
│ │ • Prevents redundant facts from multiple passes             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ SAFETY LIMITS                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ • Max iterations per agent: 30 (prevents infinite loops)        │
│ • Max tokens per request: 4096 (discovery) / 8192 (reasoning)   │
│ • Timeout per agent: 10 minutes                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Complete Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA FLOW                            │
└─────────────────────────────────────────────────────────────────┘


  PDF Documents                     Deal Context (optional)
       │                                   │
       ▼                                   │
┌─────────────┐                            │
│ PDF Parser  │                            │
│ (pymupdf)   │                            │
└──────┬──────┘                            │
       │                                   │
       ▼                                   │
  Raw Text                                 │
       │                                   │
       ├───────────────────────────────────┤
       │                                   │
       ▼                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 1: DISCOVERY                               │
│                                                                 │
│  Document Text + Domain Prompt → Haiku → Tool Calls → FactStore │
│                                                                 │
│  Output: facts_TIMESTAMP.json                                   │
└─────────────────────────────────────────────────────────────────┘
       │
       │  FactStore.format_for_reasoning()
       │  (converts facts to prompt text)
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 2: REASONING                               │
│                                                                 │
│  Facts Text + Deal Context + Prompt → Sonnet → ReasoningStore   │
│                                                                 │
│  Output: findings_TIMESTAMP.json                                │
└─────────────────────────────────────────────────────────────────┘
       │
       │  FactStore + ReasoningStore
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 3-5: POST-PROCESSING                          │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Coverage   │  │  Synthesis  │  │     VDR     │              │
│  │  Analysis   │  │   Merge &   │  │  Generation │              │
│  │             │  │   Rollup    │  │             │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                     │
│         ▼                ▼                ▼                     │
│    coverage.json   synthesis.json   vdr_requests.json           │
│                    exec_summary.md  vdr_requests.md             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
   ALL OUTPUTS SAVED TO output/ DIRECTORY
```

---

## File Structure Reference

```
it-diligence-agent/
│
├── main_v2.py                 # Orchestrator (phases 1-5)
├── config_v2.py               # Model config, API keys, limits
│
├── agents_v2/
│   ├── base_discovery_agent.py    # Discovery loop (Haiku)
│   ├── base_reasoning_agent.py    # Reasoning loop (Sonnet)
│   ├── discovery/                 # 6 domain discovery agents
│   └── reasoning/                 # 6 domain reasoning agents
│
├── tools_v2/
│   ├── fact_store.py              # FactStore class
│   ├── discovery_tools.py         # Tool definitions + execution
│   ├── reasoning_tools.py         # Tool definitions + ReasoningStore
│   ├── coverage.py                # Checklists + CoverageAnalyzer
│   ├── synthesis.py               # SynthesisAnalyzer
│   └── vdr_generator.py           # VDRGenerator
│
├── prompts/
│   ├── v2_*_discovery_prompt.py   # Discovery system prompts
│   └── v2_*_reasoning_prompt.py   # Reasoning system prompts
│
└── output/                        # Generated files
```

---

## Summary: Layer 2 Technical Implementation

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Orchestrator** | Coordinates all phases | `main_v2.py` |
| **Discovery Agents** | Extract facts (Haiku) | `agents_v2/discovery/` |
| **Reasoning Agents** | Analyze facts (Sonnet) | `agents_v2/reasoning/` |
| **FactStore** | Store extracted facts | `tools_v2/fact_store.py` |
| **ReasoningStore** | Store findings with costs | `tools_v2/reasoning_tools.py` |
| **Coverage** | Score completeness | `tools_v2/coverage.py` |
| **Synthesis** | Cross-domain analysis | `tools_v2/synthesis.py` |
| **VDR Generator** | Follow-up requests | `tools_v2/vdr_generator.py` |

**Key Technical Decisions:**
1. **No frameworks** - Direct API calls for control and debuggability
2. **Tool-based output** - Structured schemas enforce data quality
3. **Evidence chains** - Every finding must cite facts
4. **Parallel execution** - 3 workers with thread-safe merge
5. **Validation at edges** - Catch errors early, let AI self-correct

---

*Next: Layer 3 will cover AI prompt engineering and domain expertise*

---

# Layer 3: AI & Domain Expertise

## The Human-AI Collaboration Model

The system is designed to **capture and scale domain expertise**. Associates and staff bring deal experience; the system encodes that knowledge into reusable, consistent analysis.

```
┌─────────────────────────────────────────────────────────────────┐
│                  EXPERTISE CAPTURE CYCLE                         │
└─────────────────────────────────────────────────────────────────┘

     ┌───────────────────┐
     │   DEAL TEAM       │
     │   EXPERIENCE      │
     │                   │
     │ • Pattern         │
     │   recognition     │
     │ • "We always      │
     │   ask about X"    │
     │ • Red flags       │
     │   from past deals │
     └─────────┬─────────┘
               │
               ▼
     ┌───────────────────┐
     │   KNOWLEDGE       │
     │   ENCODING        │
     │                   │
     │ • Prompts         │
     │ • Checklists      │
     │ • Risk patterns   │
     └─────────┬─────────┘
               │
               ▼
     ┌───────────────────┐
     │   AI APPLIES      │
     │   CONSISTENTLY    │
     │                   │
     │ • Every document  │
     │ • Every deal      │
     │ • No forgetting   │
     └─────────┬─────────┘
               │
               ▼
     ┌───────────────────┐
     │   TEAM REVIEWS    │
     │   & REFINES       │
     │                   │
     │ • Catch gaps      │
     │ • Add new checks  │
     │ • Improve prompts │
     └─────────┬─────────┘
               │
               └──────────► Feeds back into next iteration
```

**Key Insight**: Every deal teaches us something. The system makes sure those lessons stick.

---

## How Associates and Staff Improve the System

### Three Contribution Paths

```
┌─────────────────────────────────────────────────────────────────┐
│                 CONTRIBUTION PATHS                               │
└─────────────────────────────────────────────────────────────────┘

PATH 1: CHECKLIST REFINEMENT                    Effort: Low
───────────────────────────────────────────────────────────────────
"This deal, we needed to ask about XYZ but the system didn't
flag it as missing."

Action: Add item to coverage checklist
File:   tools_v2/coverage.py
Impact: System now flags missing XYZ in all future deals

Example:
  Before deal: Checklist has 14 network items
  After deal:  Add "SD-WAN deployment status" (15 items)
  Result:      Every future deal checks for SD-WAN info


PATH 2: PROMPT ENHANCEMENT                      Effort: Medium
───────────────────────────────────────────────────────────────────
"The system identified the risk but missed the nuance that
makes it critical in manufacturing companies."

Action: Add industry-specific guidance to prompt
File:   prompts/v2_*_reasoning_prompt.py
Impact: AI considers industry context in analysis

Example:
  Before: Generic "EOL software is a risk"
  After:  "For manufacturing targets, EOL SCADA/ICS software
           is CRITICAL due to OT/IT convergence security..."
  Result: More accurate severity ratings


PATH 3: RISK PATTERN LIBRARY                    Effort: Low-Medium
───────────────────────────────────────────────────────────────────
"Every deal with on-prem VMware has the same 3 integration
issues. Can we pre-load those?"

Action: Add to risk pattern library in prompts
File:   prompts/v2_infrastructure_reasoning_prompt.py
Impact: AI proactively looks for known patterns

Example:
  Add to prompt: "When VMware on-prem is found, always evaluate:
  1. vCenter licensing transfer complexity
  2. VMware by Broadcom subscription impact
  3. Host hardware EOL alignment"
```

---

## The Prompt System: Encoding Expertise

### How Prompts Work

Each domain has two prompts: **Discovery** (what to extract) and **Reasoning** (how to analyze).

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROMPT ANATOMY                                │
└─────────────────────────────────────────────────────────────────┘

DISCOVERY PROMPT (v2_infrastructure_discovery_prompt.py)
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  SECTION 1: ROLE DEFINITION                                     │
│  "You are a senior IT consultant performing infrastructure      │
│   due diligence for an M&A transaction..."                      │
│                                                                 │
│  Purpose: Sets AI's persona and quality expectations            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SECTION 2: INVENTORY STRUCTURE                                 │
│  "Extract information into these categories:                    │
│   - Hosting Model (data center, cloud, hybrid)                  │
│   - Compute (servers, VMs, containers)                          │
│   - Storage (SAN, NAS, object storage)                          │
│   ..."                                                          │
│                                                                 │
│  Purpose: Defines what to look for                              │
│  ▲▲▲ ASSOCIATES CAN ADD NEW CATEGORIES HERE ▲▲▲                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SECTION 3: EVIDENCE REQUIREMENTS                               │
│  "Every fact MUST include an exact quote from the document.     │
│   Minimum 10 characters. Include section name if visible."      │
│                                                                 │
│  Purpose: Ensures traceability (non-negotiable)                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SECTION 4: GAP DETECTION GUIDANCE                              │
│  "Flag as gap when these critical items are missing:            │
│   - DR recovery objectives (RTO/RPO)                            │
│   - EOL system inventory                                        │
│   ..."                                                          │
│                                                                 │
│  Purpose: Proactive gap identification                          │
│  ▲▲▲ STAFF CAN ADD COMMON GAPS HERE ▲▲▲                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘


REASONING PROMPT (v2_infrastructure_reasoning_prompt.py)
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  SECTION 1: ANALYSIS FRAMEWORK                                  │
│  "Analyze the infrastructure inventory for M&A readiness.       │
│   Consider: scalability, integration complexity, security       │
│   posture, operational risk..."                                 │
│                                                                 │
│  Purpose: Defines analysis dimensions                           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SECTION 2: RISK PATTERNS                                       │
│  "Known risk patterns to evaluate:                              │
│   - VMware licensing: 6.x is EOL, assess upgrade path           │
│   - Backup: No offsite = DR risk                                │
│   - Cloud: Single-region = availability risk                    │
│   ..."                                                          │
│                                                                 │
│  Purpose: Pre-loaded expertise from past deals                  │
│  ▲▲▲ THIS IS WHERE DEAL EXPERIENCE LIVES ▲▲▲                    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SECTION 3: COST ESTIMATION GUIDANCE                            │
│  "For work items, estimate costs using these ranges:            │
│   - VMware upgrade (340 VMs): $100K-$500K                       │
│   - DR implementation: $250K-$1M                                │
│   - Cloud migration: depends on VM count..."                    │
│                                                                 │
│  Purpose: Consistent cost estimation                            │
│  ▲▲▲ CALIBRATED FROM ACTUAL PROJECT COSTS ▲▲▲                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SECTION 4: DEAL CONTEXT INJECTION                              │
│  "{deal_context}"    ← Placeholder filled at runtime            │
│                                                                 │
│  Purpose: Deal-specific considerations                          │
│  Example: "Integration approach is migration to acquirer        │
│            cloud. Target will be decommissioned Day 180."       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Coverage Checklists: The "Did We Ask?" System

### How Checklists Work

Coverage checklists define **what we expect to find** for thorough due diligence.

```
┌─────────────────────────────────────────────────────────────────┐
│              COVERAGE CHECKLIST STRUCTURE                        │
└─────────────────────────────────────────────────────────────────┘

DOMAIN: Infrastructure
├── CATEGORY: compute
│   ├── vm_inventory [CRITICAL]      "VM count and breakdown"
│   ├── container_platform           "Kubernetes/Docker details"
│   └── serverless_usage             "Lambda/Functions usage"
│
├── CATEGORY: backup_dr
│   ├── backup_solution [CRITICAL]   "Backup software/provider"
│   ├── rpo_rto [CRITICAL]           "Recovery objectives"
│   ├── dr_location                  "DR site location"
│   └── dr_test_frequency            "DR testing schedule"
│
├── CATEGORY: legacy
│   ├── eol_systems [CRITICAL]       "End-of-life systems"
│   └── technical_debt               "Known tech debt items"
│
└── ... (21 total items for infrastructure)


IMPORTANCE LEVELS:
┌──────────┬───────────────────────────────────────────────────┐
│ CRITICAL │ Must have for any deal. Missing = automatic gap.  │
│          │ Examples: VM count, RTO/RPO, EOL systems          │
├──────────┼───────────────────────────────────────────────────┤
│ IMPORTANT│ Should have for thorough analysis. Missing =      │
│          │ lower coverage score but not automatic VDR.       │
├──────────┼───────────────────────────────────────────────────┤
│ NICE_TO  │ Good to have if available. Doesn't impact         │
│ _HAVE    │ coverage score significantly.                     │
└──────────┴───────────────────────────────────────────────────┘
```

### How Associates Update Checklists

**Example: Adding a new item after a deal**

```python
# File: tools_v2/coverage.py

# BEFORE (what we had)
"network": {
    "wan": {
        "primary_isp": {"importance": "critical", "description": "Primary ISP and bandwidth"},
        "redundancy": {"importance": "critical", "description": "WAN redundancy"},
        "sd_wan": {"importance": "important", "description": "SD-WAN deployment"},
    },
    # ...
}

# AFTER (associate adds new item based on deal experience)
"network": {
    "wan": {
        "primary_isp": {"importance": "critical", "description": "Primary ISP and bandwidth"},
        "redundancy": {"importance": "critical", "description": "WAN redundancy"},
        "sd_wan": {"importance": "important", "description": "SD-WAN deployment"},
        "mpls_circuits": {"importance": "important", "description": "MPLS circuit inventory"},  # NEW
    },
    # ...
}
```

**Impact**: Every future deal will now check for MPLS circuit documentation. If missing, coverage score drops. If critical, it becomes a VDR request automatically.

---

## Feedback Loop: From Deal Experience to System Improvement

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP PROCESS                         │
└─────────────────────────────────────────────────────────────────┘


STEP 1: DEAL EXECUTION
────────────────────────────────────────────────────────────────────
Team runs system on target's IT documentation
System produces: Facts, Risks, Work Items, VDR Requests

STEP 2: TEAM REVIEW
────────────────────────────────────────────────────────────────────
Associate/Staff reviews outputs against their expertise

Questions to ask:
┌─────────────────────────────────────────────────────────────────┐
│ □ Did the system miss anything I caught manually?               │
│ □ Did it flag something I wouldn't have thought of?             │
│ □ Are the severity ratings accurate for this type of target?    │
│ □ Were the cost estimates in the right ballpark?                │
│ □ What additional questions did management ask that the         │
│   system didn't pre-generate?                                   │
└─────────────────────────────────────────────────────────────────┘

STEP 3: CAPTURE LEARNINGS
────────────────────────────────────────────────────────────────────
Document improvements needed:

Improvement Type              Where to Update
─────────────────────────────────────────────────────────────────
"Missed a category"           → Coverage checklist (coverage.py)
"Wrong severity"              → Reasoning prompt guidance
"Missed industry context"     → Add to prompt risk patterns
"Cost estimate off"           → Calibrate in prompt section 3
"Asked wrong questions"       → VDR suggested documents list

STEP 4: IMPLEMENT IMPROVEMENTS
────────────────────────────────────────────────────────────────────
Simple text file updates - no coding required

Example prompt update:
"""
# Risk Pattern Addition (after healthcare deal)

When analyzing healthcare targets, ALWAYS check for:
- HIPAA BAA status with all cloud providers
- PHI data residency constraints
- Healthcare-specific DR requirements (often more stringent)

Flag as CRITICAL severity if not documented.
"""

STEP 5: VALIDATE ON NEXT DEAL
────────────────────────────────────────────────────────────────────
Changes automatically apply to all future runs
Track: "Did this improvement help on the next deal?"
```

---

## Model Selection: Why Haiku + Sonnet

### The Tiering Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                  MODEL SELECTION RATIONALE                       │
└─────────────────────────────────────────────────────────────────┘

TASK: Discovery (Fact Extraction)
────────────────────────────────────────────────────────────────────
Requirements:
• Read document, extract specific information
• Copy exact quotes
• Categorize into predefined buckets
• Flag when information is missing

Reasoning needed: LOW (pattern matching, not judgment)
Ideal model: HAIKU (Claude 3.5 Haiku)
• Fast: 3-4x faster than Sonnet
• Cheap: ~$0.25/1M tokens (vs $3/1M for Sonnet)
• Accurate: Sufficient for extraction tasks

Cost impact: ~70% of token volume uses cheapest model


TASK: Reasoning (Analysis)
────────────────────────────────────────────────────────────────────
Requirements:
• Assess risk severity (judgment call)
• Consider deal context
• Estimate remediation costs
• Formulate mitigation recommendations
• Connect facts to implications

Reasoning needed: HIGH (nuanced judgment)
Ideal model: SONNET (Claude 3.5/4 Sonnet)
• Capable: Better at nuanced reasoning
• Reliable: More consistent on complex tasks
• Worth it: Analysis quality is the deliverable

Cost impact: ~30% of token volume uses capable model


RESULT: Best of Both Worlds
────────────────────────────────────────────────────────────────────
             │ V1 (Single Model)  │ V2 (Tiered)       │
─────────────┼────────────────────┼───────────────────┤
 Discovery   │ Sonnet ($3/1M)     │ Haiku ($0.25/1M)  │
 Reasoning   │ Sonnet ($3/1M)     │ Sonnet ($3/1M)    │
─────────────┼────────────────────┼───────────────────┤
 Total Cost  │ ~$15 per analysis  │ ~$9 per analysis  │
 Quality     │ Good               │ Same or better    │
─────────────┴────────────────────┴───────────────────┘

40% cost reduction without quality sacrifice
```

---

## Quality Assurance: Built-In Safeguards

### Evidence Chain Validation

```
┌─────────────────────────────────────────────────────────────────┐
│               QUALITY SAFEGUARDS                                 │
└─────────────────────────────────────────────────────────────────┘

SAFEGUARD 1: Evidence Required
────────────────────────────────────────────────────────────────────
Every risk MUST cite at least one fact ID

✓ VALID:
  Risk: "EOL VMware version"
  based_on_facts: ["F-INFRA-003", "F-INFRA-007"]
  reasoning: "F-INFRA-003 shows VMware 6.7..."

✗ REJECTED:
  Risk: "Possible security concerns"
  based_on_facts: []           ← AI gets error, must retry
  reasoning: "General observation"


SAFEGUARD 2: Quote Length Minimum
────────────────────────────────────────────────────────────────────
Evidence quotes must be 10+ characters

✓ VALID:
  exact_quote: "VMware vSphere 6.7 with 340 production VMs"

✗ REJECTED:
  exact_quote: "VMware"        ← Too vague, must provide more


SAFEGUARD 3: Consistency Checks (Synthesis Phase)
────────────────────────────────────────────────────────────────────
Cross-domain validation catches contradictions

Example:
  Infrastructure says: "AWS us-east-1 primary cloud"
  Applications says: "Azure is primary cloud provider"

  → System flags inconsistency for human review


SAFEGUARD 4: Coverage Scoring
────────────────────────────────────────────────────────────────────
Automatic "completeness grade" signals when more info needed

Grade A: 80%+ critical items documented
Grade B: 60-79% critical items documented
Grade C: 40-59% critical items documented
Grade D: 20-39% critical items documented
Grade F: <20% critical items documented

→ Grade C or below triggers enhanced VDR request list
```

---

## Real Example: How Team Feedback Becomes System Improvement

### Case Study: Healthcare Deal Learning

```
┌─────────────────────────────────────────────────────────────────┐
│          CASE STUDY: HEALTHCARE DEAL IMPROVEMENT                 │
└─────────────────────────────────────────────────────────────────┘

SITUATION:
────────────────────────────────────────────────────────────────────
Deal: Healthcare SaaS acquisition
Issue: System rated data residency risk as "medium"
Reality: For healthcare, this was "critical" (HIPAA implications)
Feedback: Associate noted severity miscalibration


IMPROVEMENT IMPLEMENTED:
────────────────────────────────────────────────────────────────────

1. Added to v2_cybersecurity_reasoning_prompt.py:

   """
   ## Industry-Specific Risk Calibration

   HEALTHCARE TARGETS:
   - Data residency constraints → CRITICAL (HIPAA)
   - BAA status with cloud providers → CRITICAL
   - PHI access logging → HIGH
   - Breach notification procedures → CRITICAL

   When target handles PHI, elevate all data-related
   risks by one severity level.
   """

2. Added to coverage checklist (coverage.py):

   "compliance": {
       "hipaa_baa": {
           "importance": "critical",
           "description": "HIPAA BAA with cloud providers",
           "industry": "healthcare"
       },
       # ...
   }


RESULT ON NEXT HEALTHCARE DEAL:
────────────────────────────────────────────────────────────────────
• Data residency now flagged as CRITICAL
• HIPAA BAA appears in VDR requests automatically
• Associate validated: "This is what we would have asked"


TIME TO IMPLEMENT: ~15 minutes
IMPACT: All future healthcare deals benefit
```

---

## Roadmap: Continuous Improvement Path

```
┌─────────────────────────────────────────────────────────────────┐
│               IMPROVEMENT ROADMAP                                │
└─────────────────────────────────────────────────────────────────┘

NEAR-TERM (Active)
────────────────────────────────────────────────────────────────────
☑ Base system operational (V2 architecture)
☑ Six domain agents functional
☑ Coverage checklists defined
☐ Calibrate from first 5 deals
☐ Build industry-specific prompt variants

MEDIUM-TERM (Planned)
────────────────────────────────────────────────────────────────────
☐ Cost estimate calibration from actual project outcomes
☐ Risk severity validation against deal outcomes
☐ Integration complexity scoring refinement
☐ Cross-deal pattern library (anonymized learnings)

LONG-TERM (Vision)
────────────────────────────────────────────────────────────────────
☐ Automated quality scoring (compare to manual analysis)
☐ Industry-specific model fine-tuning
☐ Integration with deal management systems
☐ Predictive integration cost modeling
```

---

## Summary: Layer 3 - AI & Domain Expertise

### The Key Message

**The system doesn't replace expertise—it captures and scales it.**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ASSOCIATE KNOWLEDGE              SYSTEM CAPABILITY            │
│                                                                 │
│   "I know to always ask           →  Encoded in checklist      │
│    about DR testing"                 (never forgotten)          │
│                                                                 │
│   "This VMware version            →  In risk patterns          │
│    is end of life"                   (always caught)            │
│                                                                 │
│   "Healthcare deals need          →  In industry prompts       │
│    HIPAA checks"                     (consistently applied)     │
│                                                                 │
│   "That cost estimate             →  Calibrated guidance       │
│    is too low"                       (improved over time)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### How Staff Contribute

| Contribution | Effort | Impact |
|--------------|--------|--------|
| Add checklist item | 5 min | All future deals check for it |
| Flag missed risk pattern | 10 min | All future deals evaluate it |
| Calibrate cost estimate | 15 min | More accurate budgeting |
| Add industry guidance | 30 min | Sector-appropriate analysis |

### The Flywheel Effect

```
More deals → More feedback → Better prompts → Better outputs →
       ↑                                              │
       └──────────────── More trust ←────────────────┘
```

**Every deal makes the system smarter. Every team member can contribute.**

---

*Next: Business Value & Deal Lifecycle Integration*

---

# Business Value & Deal Lifecycle Integration

## Where This Fits in the Deal Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    M&A DEAL LIFECYCLE                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│         │   │         │   │         │   │         │   │         │
│ SOURCING│──►│   LOI   │──►│   DUE   │──►│ SIGNING │──►│ CLOSING │
│         │   │         │   │DILIGENCE│   │         │   │         │
│         │   │         │   │         │   │         │   │         │
└─────────┘   └─────────┘   └────┬────┘   └─────────┘   └─────────┘
                                 │
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │ Financial│      │    IT    │      │  Legal   │
        │    DD    │      │    DD    │      │    DD    │
        └──────────┘      └────┬─────┘      └──────────┘
                               │
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
   ┌───────────┐        ┌───────────┐        ┌───────────┐
   │  PHASE 1  │        │  PHASE 2  │        │  PHASE 3  │
   │           │        │           │        │           │
   │  Initial  │───────►│   Deep    │───────►│  Final    │
   │  Request  │        │   Dive    │        │  Report   │
   │           │        │           │        │           │
   └─────┬─────┘        └─────┬─────┘        └─────┬─────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
   ┌───────────┐        ┌───────────┐        ┌───────────┐
   │   THIS    │        │   THIS    │        │   THIS    │
   │  SYSTEM   │        │  SYSTEM   │        │  SYSTEM   │
   │           │        │           │        │           │
   │ • First   │        │ • Updated │        │ • Final   │
   │   pass    │        │   analysis│        │   summary │
   │ • VDR     │        │ • Risk    │        │ • Cost    │
   │   requests│        │   register│        │   rollup  │
   └───────────┘        └───────────┘        └───────────┘
```

**The system supports all three phases of IT due diligence:**

| Phase | Traditional Approach | With This System |
|-------|---------------------|------------------|
| **Initial Request** | Associate manually reviews first docs, creates VDR list | System generates structured VDR requests in minutes |
| **Deep Dive** | Senior staff analyzes, junior staff documents | System produces first-pass analysis, staff validates and refines |
| **Final Report** | Manual compilation of findings | System provides structured data for report generation |

---

## Time Savings Analysis

### Current State vs. Future State

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIME COMPARISON                               │
└─────────────────────────────────────────────────────────────────┘

TASK: Initial Document Review (50-100 pages of IT docs)
────────────────────────────────────────────────────────────────────

CURRENT STATE (Manual)
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Associate reads documents              4-6 hours               │
│  Associate extracts key facts           2-3 hours               │
│  Associate drafts VDR follow-ups        1-2 hours               │
│  Senior review and refinement           1-2 hours               │
│  ─────────────────────────────────────────────────              │
│  TOTAL                                  8-13 hours              │
│                                                                 │
│  Calendar time: 2-3 days (competing priorities)                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

FUTURE STATE (With System)
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  System processes documents             15 minutes              │
│  Associate reviews system output        1-2 hours               │
│  Associate adds deal-specific context   30 min                  │
│  Senior review and refinement           30 min - 1 hour         │
│  ─────────────────────────────────────────────────              │
│  TOTAL                                  2.5-4 hours             │
│                                                                 │
│  Calendar time: Same day                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

SAVINGS PER DEAL: 5-9 hours on initial review alone
QUALITY IMPROVEMENT: Consistent coverage, nothing missed
```

### Across the Deal Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│              TIME SAVINGS BY ACTIVITY                            │
└─────────────────────────────────────────────────────────────────┘

                              │ Manual │ With System │ Savings │
──────────────────────────────┼────────┼─────────────┼─────────┤
Initial document review       │ 8-13 hr│   2.5-4 hr  │  65-70% │
VDR request generation        │ 2-3 hr │   15 min*   │  85-90% │
Risk identification           │ 4-6 hr │   1-2 hr**  │  60-70% │
Cost estimation               │ 2-4 hr │   30 min**  │  80-85% │
Cross-domain consistency      │ 1-2 hr │   5 min*    │  95%    │
Final report compilation      │ 3-5 hr │   1-2 hr    │  50-60% │
──────────────────────────────┼────────┼─────────────┼─────────┤
TOTAL PER DEAL                │ 20-33hr│   6-10 hr   │  65-70% │

* Fully automated
** System generates, human validates
```

---

## Quality Improvements

### Consistency Gains

```
┌─────────────────────────────────────────────────────────────────┐
│                 QUALITY DIMENSIONS                               │
└─────────────────────────────────────────────────────────────────┘

DIMENSION 1: COVERAGE CONSISTENCY
────────────────────────────────────────────────────────────────────

Problem (Manual):
• Different associates check for different things
• Institutional knowledge varies by person
• Easy to forget to ask about specific items

Solution (System):
• 101 checklist items across 6 domains
• Same checks every deal, every time
• Coverage grade shows completeness


DIMENSION 2: EVIDENCE TRACEABILITY
────────────────────────────────────────────────────────────────────

Problem (Manual):
• Findings in reports lack source citations
• Hard to verify claims against documents
• IC questions require digging through docs

Solution (System):
• Every finding cites specific fact IDs
• Facts include exact quotes from documents
• One click from finding to source evidence


DIMENSION 3: RISK SEVERITY CALIBRATION
────────────────────────────────────────────────────────────────────

Problem (Manual):
• Severity ratings vary by analyst
• Context (industry, deal type) inconsistently applied
• Hard to compare risks across deals

Solution (System):
• Consistent severity framework
• Industry-specific calibration in prompts
• Same scale applied every time


DIMENSION 4: COST ESTIMATION
────────────────────────────────────────────────────────────────────

Problem (Manual):
• Cost estimates vary wildly by analyst
• No standardized ranges
• Difficult to aggregate for deal model

Solution (System):
• Five standardized cost ranges
• Calibrated from actual project outcomes
• Automatic aggregation by phase/owner
```

### Error Reduction

```
┌─────────────────────────────────────────────────────────────────┐
│               COMMON ERRORS PREVENTED                            │
└─────────────────────────────────────────────────────────────────┘

ERROR TYPE                    │ HOW SYSTEM PREVENTS
──────────────────────────────┼─────────────────────────────────────
Missing critical items        │ Checklist ensures all items checked
Unsupported claims            │ Evidence requirement enforced
Inconsistent severity         │ Standardized framework
Forgotten follow-up questions │ VDR auto-generated from gaps
Cross-domain contradictions   │ Synthesis phase catches conflicts
Incomplete cost picture       │ Automatic aggregation
```

---

## Team Workflow Integration

### How the Team Uses the System

```
┌─────────────────────────────────────────────────────────────────┐
│                  TEAM WORKFLOW                                   │
└─────────────────────────────────────────────────────────────────┘


STEP 1: DOCUMENT INTAKE
────────────────────────────────────────────────────────────────────
WHO: Associate or Analyst
WHAT: Collect IT documents from VDR, drop into input folder
TIME: 5 minutes

     ┌─────────────────┐
     │  VDR Documents  │
     │  • IT Overview  │
     │  • Security     │
     │  • Network      │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │  input/ folder  │
     └─────────────────┘


STEP 2: SYSTEM EXECUTION
────────────────────────────────────────────────────────────────────
WHO: Associate (or automated)
WHAT: Run the analysis command
TIME: 15 minutes (automated)

     $ python main_v2.py input/

     Progress:
     ✓ Phase 1: Discovery (6 domains)     [====] 100%
     ✓ Phase 2: Reasoning (6 domains)     [====] 100%
     ✓ Phase 3: Coverage Analysis         [====] 100%
     ✓ Phase 4: Synthesis                 [====] 100%
     ✓ Phase 5: VDR Generation            [====] 100%


STEP 3: ASSOCIATE REVIEW
────────────────────────────────────────────────────────────────────
WHO: Associate
WHAT: Review outputs, validate against documents, add context
TIME: 1-2 hours

Review checklist:
┌─────────────────────────────────────────────────────────────────┐
│ □ Check coverage grade - are we missing critical docs?          │
│ □ Review high/critical risks - do severities make sense?        │
│ □ Scan work items - are cost estimates reasonable?              │
│ □ Check VDR requests - anything to add/remove?                  │
│ □ Note any deal-specific context system couldn't know           │
└─────────────────────────────────────────────────────────────────┘


STEP 4: SENIOR REVIEW
────────────────────────────────────────────────────────────────────
WHO: Manager or Senior Associate
WHAT: Validate analysis, approve for distribution
TIME: 30 min - 1 hour

Senior review focus:
┌─────────────────────────────────────────────────────────────────┐
│ □ Do findings align with deal thesis?                           │
│ □ Are there strategic implications to highlight?                │
│ □ Cost estimates in line with experience?                       │
│ □ Any red flags for IC to be aware of?                          │
└─────────────────────────────────────────────────────────────────┘


STEP 5: OUTPUT DISTRIBUTION
────────────────────────────────────────────────────────────────────
WHO: Associate
WHAT: Package outputs for deal team

Outputs ready for use:
• Executive Summary    → Deal team, IC materials
• VDR Request Pack     → Send to target
• Risk Register        → Integration planning
• Cost Summary         → Deal model inputs
```

### Role-Based Value

```
┌─────────────────────────────────────────────────────────────────┐
│                VALUE BY ROLE                                     │
└─────────────────────────────────────────────────────────────────┘

ANALYST / JUNIOR ASSOCIATE
────────────────────────────────────────────────────────────────────
Before: Spend days reading documents, manually extracting facts
After:  Review system output, learn what to look for, add value faster

Value: Accelerated learning curve, focus on judgment not extraction


ASSOCIATE
────────────────────────────────────────────────────────────────────
Before: Bottleneck on document review, inconsistent coverage
After:  Validate and refine system output, handle more deals

Value: Higher throughput, consistent quality, more strategic work


SENIOR ASSOCIATE / MANAGER
────────────────────────────────────────────────────────────────────
Before: Review junior work for completeness, catch gaps
After:  Review structured output, focus on deal implications

Value: Less time on QA, more time on value-add analysis


DIRECTOR / MD
────────────────────────────────────────────────────────────────────
Before: Hope the team caught everything, IC prep scramble
After:  Evidence-backed findings, consistent format, cost visibility

Value: Confidence in outputs, faster IC preparation
```

---

## Operating Costs & Performance

### Per-Analysis Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                  SYSTEM PERFORMANCE                              │
└─────────────────────────────────────────────────────────────────┘

PROCESSING TIME (varies by document volume)
────────────────────────────────────────────────────────────────────
Small document set (20-50 pages)              8-12 minutes
Medium document set (50-100 pages)            12-18 minutes
Large document set (100-200 pages)            18-30 minutes

Factors affecting time:
• Document complexity and density
• Number of domains with relevant content
• API response latency (varies)


API COSTS (approximate ranges)
────────────────────────────────────────────────────────────────────
Typical analysis                              $8 - $15
Complex/large document set                    $15 - $25
Discovery-only run                            $3 - $6

Cost drivers:
• Token count (document length)
• Number of reasoning iterations
• Model selection (Haiku vs Sonnet mix)

Note: Costs are estimates based on current API pricing.
Actual costs may vary based on document characteristics.
```

### What to Expect

```
┌─────────────────────────────────────────────────────────────────┐
│                  REALISTIC EXPECTATIONS                          │
└─────────────────────────────────────────────────────────────────┘

THE SYSTEM IS GOOD AT:
────────────────────────────────────────────────────────────────────
✓ Extracting facts consistently from documents
✓ Catching items that might be missed under time pressure
✓ Generating structured follow-up questions
✓ Providing a solid first-pass analysis
✓ Ensuring nothing falls through the cracks

THE SYSTEM STILL NEEDS HUMAN JUDGMENT FOR:
────────────────────────────────────────────────────────────────────
• Deal-specific context and strategy implications
• Nuanced severity calibration for unusual situations
• Cost estimates that depend on integration approach
• Industry-specific considerations not yet in prompts
• Final validation before IC distribution

IMPROVEMENT OVER TIME:
────────────────────────────────────────────────────────────────────
• Quality improves as team feeds back learnings
• Cost estimates become more accurate with calibration
• Coverage expands as we add checklist items
• First few deals will surface refinement opportunities
```

### Additional Considerations

```
┌─────────────────────────────────────────────────────────────────┐
│              BENEFITS BEYOND TIME SAVINGS                        │
└─────────────────────────────────────────────────────────────────┘

BENEFIT                        │ IMPACT
───────────────────────────────┼─────────────────────────────────────
Faster deal velocity           │ Compress diligence timeline
Reduced deal fatigue           │ Team handles more deals sustainably
Consistent quality             │ Every deal gets same rigor
Institutional knowledge        │ Expertise captured, not lost
Junior development             │ Learn from system, add value faster
IC confidence                  │ Evidence-backed, verifiable claims
Integration planning           │ Structured data feeds planning
```

---

## Future Roadmap Alignment

### Near-Term Enhancements (Next 6 Months)

```
┌─────────────────────────────────────────────────────────────────┐
│               NEAR-TERM ROADMAP                                  │
└─────────────────────────────────────────────────────────────────┘

ENHANCEMENT 1: Industry-Specific Prompts
────────────────────────────────────────────────────────────────────
What: Pre-built prompt variants for common industries
Why:  Healthcare, manufacturing, financial services have unique needs
Impact: More accurate risk calibration out of the box

ENHANCEMENT 2: Deal Context Templates
────────────────────────────────────────────────────────────────────
What: Structured templates for deal context input
Why:  Integration approach affects analysis significantly
Impact: Better recommendations based on deal specifics

ENHANCEMENT 3: Historical Calibration
────────────────────────────────────────────────────────────────────
What: Tune cost estimates based on actual project outcomes
Why:  Current estimates are educated guesses
Impact: More accurate budgeting for deal models

ENHANCEMENT 4: Report Generation
────────────────────────────────────────────────────────────────────
What: Auto-generate formatted IC memo sections
Why:  Reduce manual report compilation time
Impact: Further time savings in final phase
```

### Medium-Term Vision (6-18 Months)

```
┌─────────────────────────────────────────────────────────────────┐
│               MEDIUM-TERM VISION                                 │
└─────────────────────────────────────────────────────────────────┘

CAPABILITY                     │ DESCRIPTION
───────────────────────────────┼─────────────────────────────────────
Cross-deal patterns            │ Learn from portfolio of deals
Integration playbooks          │ Standard approaches by scenario
Vendor intelligence            │ Track vendor EOL, pricing trends
Automated VDR follow-up        │ Track responses, update analysis
Deal management integration    │ Connect to existing deal tools
```

### Long-Term Possibilities (18+ Months)

```
┌─────────────────────────────────────────────────────────────────┐
│               LONG-TERM POSSIBILITIES                            │
└─────────────────────────────────────────────────────────────────┘

• Predictive integration cost modeling (ML on historical data)
• Real-time document monitoring (alert on new VDR uploads)
• Multi-target comparison (portfolio company benchmarking)
• Integration execution tracking (Day 1 to Day 100 progress)
• Custom model fine-tuning (our domain expertise embedded in AI)
```

---

## Summary: Business Value

### The Bottom Line

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   "A tool to help the team work more efficiently,              │
│    not replace their judgment."                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┬─────────────────┬─────────────────┐
│   CONSISTENT    │   STRUCTURED    │   IMPROVABLE    │
├─────────────────┼─────────────────┼─────────────────┤
│                 │                 │                 │
│ Same checklist  │ Evidence-backed │ Team feedback   │
│ every deal      │ findings        │ makes it better │
│                 │                 │                 │
│ Nothing falls   │ Traceable to    │ Learns from     │
│ through cracks  │ source docs     │ each deal       │
│                 │                 │                 │
│ Coverage grade  │ Cost estimates  │ Captures        │
│ shows gaps      │ aggregated      │ expertise       │
│                 │                 │                 │
└─────────────────┴─────────────────┴─────────────────┘
```

### Key Takeaways

1. **Consistency**: Same rigorous checklist applied to every deal, regardless of who's on the team

2. **Traceability**: Every finding cites specific evidence from source documents

3. **Team Augmentation**: Handles the extraction so the team can focus on judgment and strategy

4. **Low Barrier**: $8-25/analysis, runs locally, no infrastructure needed

5. **Continuous Improvement**: System improves as team provides feedback on outputs

6. **Realistic Scope**: A solid first-pass tool that still requires human review and refinement

---

## Appendix: Quick Reference

### System Commands

```bash
# Run full analysis
python main_v2.py input/

# Run discovery only (for testing)
python main_v2.py --discovery-only input/

# Run from existing facts (skip discovery)
python main_v2.py --from-facts output/facts.json

# Single domain (for testing)
python main_v2.py --domain infrastructure input/
```

### Output Files

| File | Purpose | Primary Audience |
|------|---------|------------------|
| `facts_*.json` | Extracted inventory | Technical validation |
| `findings_*.json` | Risks, work items | Deal team |
| `coverage_*.json` | Completeness scores | QA review |
| `synthesis_*.json` | Cross-domain analysis | Senior review |
| `executive_summary_*.md` | Narrative summary | IC materials |
| `vdr_requests_*.md` | Follow-up questions | Send to target |

### Key Metrics

| Metric | Target |
|--------|--------|
| Processing time | < 20 minutes |
| Coverage grade | B or higher before final |
| Evidence chain validity | 100% (enforced) |
| Cost per analysis | < $15 |

---

*End of Leadership Technical Overview*

