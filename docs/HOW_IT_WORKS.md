# How the IT Due Diligence Agent Works

> **For anyone who wants to understand what this tool does and how data flows through it.**

---

## What Is This Tool?

This is an AI-powered analysis tool for IT due diligence in M&A deals. You give it documents about a target company's IT environment (spreadsheets, Word docs, PDFs). It extracts the facts, identifies risks, and tells you what it all **means** for the deal—not just what exists, but the "so what."

**Key Philosophy:** We are the "brain on top"—we analyze and provide insights. We don't compete on data extraction; we make the data meaningful.

---

## Level 1: The 30-Second Version

```mermaid
flowchart LR
    A[📄 Documents] --> B[🤖 AI Analysis] --> C[📊 Insights Report]

    style A fill:#e0f2fe
    style B fill:#fef3c7
    style C fill:#dcfce7
```

**That's it.**

- **Input:** Files about the target company (Excel inventories, IT assessments, org charts)
- **Processing:** AI reads, extracts facts, identifies patterns, flags risks
- **Output:** Report that tells leadership what matters and why

---

## Level 2: The Data Journey

```mermaid
flowchart TD
    subgraph Input["📥 INPUT"]
        F1[Excel Files]
        F2[Word Docs]
        F3[PDFs]
        F4[Markdown]
    end

    subgraph Process["⚙️ PROCESSING"]
        P1[Parse & Extract Tables]
        P2[Detect Inventory Type]
        P3[Store in Inventory]
        P4[AI Discovery - Find Facts]
        P5[AI Reasoning - Find Risks]
    end

    subgraph Output["📤 OUTPUT"]
        O1[Key Findings - The So What]
        O2[Data Flow Diagrams]
        O3[Risk Register]
        O4[Work Items & Costs]
    end

    F1 --> P1
    F2 --> P1
    F3 --> P1
    F4 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> P5
    P5 --> O1
    P5 --> O2
    P5 --> O3
    P5 --> O4
```

### What Happens at Each Step:

| Step | What It Does | Example |
|------|--------------|---------|
| **Parse & Extract** | Reads files, pulls out tables and text | Excel sheet → rows of applications |
| **Detect Type** | Figures out what kind of data it is | "These columns look like an application inventory" |
| **Store in Inventory** | Saves structured data with stable IDs | `I-APP-0f2c01: Salesforce CRM` |
| **AI Discovery** | Finds facts from unstructured text | "They mention mainframe migration is planned" |
| **AI Reasoning** | Analyzes facts to find risks and implications | "Mainframe + no plan = Day 1 risk" |

---

## Level 3: Processing Stages

```mermaid
flowchart TD
    subgraph Stage1["STAGE 1: Ingestion"]
        direction TB
        S1A[File Router]
        S1B[Type Detector]
        S1C[Schema Validator]
        S1A --> S1B --> S1C
    end

    subgraph Stage2["STAGE 2: Enrichment"]
        direction TB
        S2A[Inventory Store]
        S2B[LLM Lookup]
        S2C[Flag Unknowns]
        S2A --> S2B --> S2C
    end

    subgraph Stage3["STAGE 3: Discovery"]
        direction TB
        S3A[Discovery Agents]
        S3B[Fact Store]
        S3C[Gap Detection]
        S3A --> S3B --> S3C
    end

    subgraph Stage4["STAGE 4: Reasoning"]
        direction TB
        S4A[Reasoning Agents]
        S4B[Risk Analysis]
        S4C[Work Items]
        S4A --> S4B --> S4C
    end

    subgraph Stage5["STAGE 5: Reporting"]
        direction TB
        S5A[So What Report]
        S5B[Data Flow Diagrams]
        S5C[Appendix Data]
        S5A --> S5B --> S5C
    end

    Stage1 --> Stage2 --> Stage3 --> Stage4 --> Stage5
```

### Stage Details:

#### Stage 1: Ingestion
**Goal:** Get data into the system reliably

- **File Router** - Detects file type (Excel, Word, MD, CSV), routes to correct parser
- **Type Detector** - Looks at column headers to determine inventory type (application, infrastructure, org, vendor)
- **Schema Validator** - Checks required fields exist, warns about missing data

**Key Point:** This is DETERMINISTIC (no AI). Same input = same output. 100% reliable.

#### Stage 2: Enrichment
**Goal:** Add context to raw inventory data

- **Inventory Store** - Holds all items with content-based IDs (same item always gets same ID)
- **LLM Lookup** - AI looks up what each application is ("Duck Creek = insurance policy admin platform")
- **Flag Unknowns** - If AI doesn't recognize something, flag it for investigation (don't guess)

**Key Point:** AI only adds info when confident. Unknown = flagged, not fabricated.

#### Stage 3: Discovery
**Goal:** Extract facts from unstructured content (prose, notes, narratives)

- **Discovery Agents** - Domain-specific AI agents (infrastructure, security, applications, etc.)
- **Fact Store** - Holds extracted facts with evidence quotes
- **Gap Detection** - Identifies what's MISSING (no DR plan mentioned, no org chart provided)

**Key Point:** Every fact has an evidence quote. No hallucination—show your work.

#### Stage 4: Reasoning
**Goal:** Turn facts into insights—the "so what"

- **Reasoning Agents** - Analyze facts in context of the deal
- **Risk Analysis** - Identify risks with severity, mitigation, supporting facts
- **Work Items** - Concrete actions needed, phased (Day 1, Day 100, Post-100), with cost estimates

**Key Point:** Every finding MUST cite facts. No unsupported conclusions.

#### Stage 5: Reporting
**Goal:** Present insights in a way leadership can use

- **So What Report** - Findings first, data second
- **Data Flow Diagrams** - Visual representation of system connectivity
- **Appendix Data** - Supporting inventory tables for reference

**Key Point:** Lead with "so what," support with evidence.

---

## Level 4: Agent Architecture

```mermaid
flowchart TD
    subgraph Discovery["DISCOVERY AGENTS (Haiku - Fast/Cheap)"]
        DA1[Infrastructure Agent]
        DA2[Applications Agent]
        DA3[Cybersecurity Agent]
        DA4[Network Agent]
        DA5[Identity/Access Agent]
        DA6[Organization Agent]
    end

    subgraph DataStores["DATA STORES"]
        DS1[(Inventory Store)]
        DS2[(Fact Store)]
    end

    subgraph Reasoning["REASONING AGENTS (Sonnet - Smart)"]
        RA1[Infrastructure Reasoning]
        RA2[Applications Reasoning]
        RA3[Cybersecurity Reasoning]
        RA4[Network Reasoning]
        RA5[Identity/Access Reasoning]
        RA6[Organization Reasoning]
    end

    subgraph Output["OUTPUT"]
        O1[Risks]
        O2[Work Items]
        O3[Recommendations]
    end

    Discovery --> DS2
    DS1 --> Reasoning
    DS2 --> Reasoning
    Reasoning --> Output
```

### Two Types of Agents:

| Agent Type | Model | Purpose | Cost |
|------------|-------|---------|------|
| **Discovery** | Haiku (fast) | Extract facts from text | ~$0.01/doc |
| **Reasoning** | Sonnet (smart) | Analyze facts, find insights | ~$0.05/domain |

### Why Two Phases?

1. **Discovery is extraction** - Needs to be thorough but not brilliant
2. **Reasoning is analysis** - Needs to be smart, see patterns, understand context
3. **Separation prevents contamination** - Facts are locked before reasoning starts

---

## Level 5: Individual Agent Deep Dive

### Discovery Agent Example: Applications

```mermaid
flowchart LR
    subgraph Input
        DOC[Document Text]
        INV[Inventory Context]
    end

    subgraph Agent["Applications Discovery Agent"]
        P1[System Prompt:<br/>Extract application facts]
        P2[Tools Available:<br/>- create_fact<br/>- flag_gap<br/>- complete]
        P3[Iterate until complete]
    end

    subgraph Output
        F1[Fact: SAP ERP exists]
        F2[Fact: 500 users]
        F3[Gap: No version documented]
    end

    DOC --> Agent
    INV --> Agent
    Agent --> F1
    Agent --> F2
    Agent --> F3
```

**What the Applications Discovery Agent Does:**

1. Receives document text + existing inventory
2. Searches for application-related information
3. For each finding:
   - Creates a FACT with evidence quote
   - Or flags a GAP if info is missing
4. Continues until document is exhausted
5. Calls `complete` when done

**Example Fact Created:**
```json
{
  "fact_id": "F-APP-001",
  "domain": "applications",
  "category": "erp",
  "item": "SAP S/4HANA",
  "details": {
    "users": 500,
    "deployment": "on-premises",
    "criticality": "critical"
  },
  "evidence": {
    "exact_quote": "SAP S/4HANA serves as our core ERP platform with approximately 500 active users",
    "source_section": "IT Infrastructure Overview"
  }
}
```

### Reasoning Agent Example: Applications

```mermaid
flowchart LR
    subgraph Input
        FACTS[All Application Facts]
        CTX[Deal Context]
    end

    subgraph Agent["Applications Reasoning Agent"]
        P1[System Prompt:<br/>Analyze for M&A risks]
        P2[Tools Available:<br/>- create_risk<br/>- create_work_item<br/>- complete]
        P3[Must cite facts]
    end

    subgraph Output
        R1[Risk: ERP concentration]
        W1[Work Item: License review]
        W2[Work Item: Migration assessment]
    end

    FACTS --> Agent
    CTX --> Agent
    Agent --> R1
    Agent --> W1
    Agent --> W2
```

**What the Applications Reasoning Agent Does:**

1. Receives all application facts + deal context (carve-out? acquisition?)
2. Analyzes patterns:
   - Cost concentration
   - Vendor lock-in
   - Integration complexity
   - Technical debt
3. Creates RISKS with:
   - Severity rating
   - Mitigation approach
   - Supporting fact citations
4. Creates WORK ITEMS with:
   - Phase (Day 1, Day 100, Post-100)
   - Cost estimate
   - Owner (buyer/target/shared)

**Example Risk Created:**
```json
{
  "finding_id": "R-APP-001",
  "title": "High ERP Concentration Risk",
  "description": "SAP S/4HANA handles 80% of business transactions with heavy customization",
  "severity": "high",
  "so_what": "Migration or replacement would cost $2-4M and take 18-24 months",
  "mitigation": "Negotiate extended TSA, begin assessment immediately",
  "citing_facts": ["F-APP-001", "F-APP-003", "F-APP-007"]
}
```

---

## Summary: The Complete Picture

```mermaid
flowchart TB
    subgraph User["👤 USER"]
        U1[Uploads Documents]
        U2[Views Report]
    end

    subgraph System["🤖 SYSTEM"]
        direction TB
        S1[Parse Files<br/>DETERMINISTIC]
        S2[Build Inventory<br/>DETERMINISTIC]
        S3[Enrich with AI<br/>OPTIONAL]
        S4[Discovery Agents<br/>EXTRACT FACTS]
        S5[Reasoning Agents<br/>FIND INSIGHTS]
        S6[Generate Report<br/>SO WHAT FIRST]
    end

    subgraph Value["💡 VALUE DELIVERED"]
        V1[Key Findings]
        V2[Data Flow Diagrams]
        V3[Risk Register]
        V4[Action Items]
    end

    U1 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 --> S6
    S6 --> U2
    S6 --> V1
    S6 --> V2
    S6 --> V3
    S6 --> V4
```

**The Key Insight:**

We are not a data extraction tool. We are the **brain on top**.

- ToltIQ extracts data → We analyze it
- Documents contain facts → We find the "so what"
- Inventory is data → Insights are value

**What makes this different:**
1. Lead with insights, not data
2. Every finding cites evidence
3. Diagrams you can validate in calls
4. Designed for M&A context, not generic IT assessment

---

*Document created: January 2026*
*For questions: Ask the person who gave you this tool*
