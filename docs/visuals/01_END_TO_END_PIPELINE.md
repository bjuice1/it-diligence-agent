# End-to-End Pipeline: IT Due Diligence Agent

## Overview Diagram

```mermaid
flowchart TB
    subgraph INPUT["📥 INPUT LAYER"]
        PDF[("📄 PDF Documents<br/>(Target & Buyer)")]
        NOTES["📝 Meeting Notes"]
        META["⚙️ Deal Config<br/>(Type, Domains)"]
    end

    subgraph INGESTION["🔄 INGESTION"]
        PARSE["PDF Parser<br/>(PyMuPDF)"]
        COMBINE["Document<br/>Combiner"]
        ENTITY["Entity Tagger<br/>(Target vs Buyer)"]
    end

    subgraph DISCOVERY["🔍 PHASE 1: DISCOVERY"]
        direction TB
        D_INFRA["Infrastructure<br/>Agent"]
        D_NET["Network<br/>Agent"]
        D_SEC["Security<br/>Agent"]
        D_APP["Applications<br/>Agent"]
        D_IAM["Identity<br/>Agent"]
        D_ORG["Organization<br/>Agent"]
    end

    subgraph FACTSTORE["💾 FACT STORE"]
        FACTS[("Facts<br/>(F-XXX-001)")]
        GAPS[("Gaps<br/>(G-XXX-001)")]
    end

    subgraph REASONING["🧠 PHASE 2: REASONING"]
        direction TB
        R_RISK["Risk<br/>Analysis"]
        R_WORK["Work Item<br/>Generation"]
        R_STRAT["Strategic<br/>Considerations"]
        R_REC["Recommendations"]
    end

    subgraph REASONSTORE["💾 REASONING STORE"]
        RISKS[("Risks")]
        WORKITEMS[("Work Items")]
        STRATEGIC[("Strategic<br/>Considerations")]
        RECS[("Recommendations")]
    end

    subgraph QUALITY["✅ PHASE 3-5: QUALITY"]
        COVERAGE["Coverage<br/>Analysis"]
        SYNTHESIS["Cross-Domain<br/>Synthesis"]
        VDR["VDR Request<br/>Generation"]
    end

    subgraph NARRATIVE["📖 PHASE 6-8: NARRATIVE"]
        DOMAIN_NAR["Domain<br/>Narratives"]
        EXEC_NAR["Executive<br/>Narrative"]
        NAR_QA["Narrative<br/>QA Review"]
    end

    subgraph OUTPUT["📊 OUTPUT LAYER"]
        READOUT["Deal Readout<br/>(1-pager)"]
        INVENTORY["Infrastructure<br/>Inventory"]
        ORGCHART["Org Chart"]
        EXCEL["Excel Export"]
        HTML["HTML Report"]
    end

    %% Flow connections
    PDF --> PARSE
    NOTES --> COMBINE
    META --> COMBINE
    PARSE --> COMBINE
    COMBINE --> ENTITY

    ENTITY --> D_INFRA & D_NET & D_SEC & D_APP & D_IAM & D_ORG

    D_INFRA & D_NET & D_SEC & D_APP & D_IAM & D_ORG --> FACTS
    D_INFRA & D_NET & D_SEC & D_APP & D_IAM & D_ORG --> GAPS

    FACTS --> R_RISK & R_WORK & R_STRAT & R_REC
    GAPS --> R_RISK & R_WORK & R_STRAT & R_REC

    R_RISK --> RISKS
    R_WORK --> WORKITEMS
    R_STRAT --> STRATEGIC
    R_REC --> RECS

    FACTS --> COVERAGE
    RISKS & WORKITEMS --> SYNTHESIS
    GAPS --> VDR

    FACTS & RISKS & WORKITEMS --> DOMAIN_NAR
    DOMAIN_NAR --> EXEC_NAR
    EXEC_NAR --> NAR_QA

    COVERAGE & SYNTHESIS & VDR --> READOUT
    FACTS --> INVENTORY
    FACTS --> ORGCHART
    RISKS & WORKITEMS & RECS --> EXCEL
    NAR_QA --> HTML

    %% Styling
    classDef input fill:#e0f2fe,stroke:#0284c7
    classDef process fill:#fef3c7,stroke:#d97706
    classDef store fill:#d1fae5,stroke:#059669
    classDef output fill:#f3e8ff,stroke:#9333ea

    class PDF,NOTES,META input
    class PARSE,COMBINE,ENTITY,D_INFRA,D_NET,D_SEC,D_APP,D_IAM,D_ORG,R_RISK,R_WORK,R_STRAT,R_REC,COVERAGE,SYNTHESIS,VDR,DOMAIN_NAR,EXEC_NAR,NAR_QA process
    class FACTS,GAPS,RISKS,WORKITEMS,STRATEGIC,RECS store
    class READOUT,INVENTORY,ORGCHART,EXCEL,HTML output
```

---

## Simplified Linear View

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INGEST    │────▶│  DISCOVER   │────▶│   REASON    │────▶│   REFINE    │────▶│   OUTPUT    │
│             │     │             │     │             │     │             │     │             │
│ • PDFs      │     │ • Extract   │     │ • Analyze   │     │ • Coverage  │     │ • Readout   │
│ • Notes     │     │   Facts     │     │   Risks     │     │ • Synthesis │     │ • Inventory │
│ • Config    │     │ • Flag      │     │ • Generate  │     │ • VDR       │     │ • Reports   │
│             │     │   Gaps      │     │   Work Items│     │ • Narrative │     │ • Excel     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                          │                   │                   │
                          ▼                   ▼                   ▼
                    ┌───────────┐       ┌───────────┐       ┌───────────┐
                    │ FactStore │       │ Reasoning │       │  Quality  │
                    │           │       │   Store   │       │  Scores   │
                    │ • Facts   │       │ • Risks   │       │ • Coverage│
                    │ • Gaps    │       │ • WorkItems│      │ • Flags   │
                    └───────────┘       │ • Recs    │       └───────────┘
                                        └───────────┘
```

---

## Model & Cost Breakdown

| Phase | Model | Est. Cost | Parallelization |
|-------|-------|-----------|-----------------|
| Discovery (6 domains) | Haiku | ~$0.05-0.10 | Yes (6 parallel) |
| Reasoning (6 domains) | Sonnet | ~$0.30-0.50 | Yes (6 parallel) |
| Coverage | Rules | $0 | N/A |
| Synthesis | Sonnet | ~$0.05-0.10 | No |
| VDR Generation | Rules + Haiku | ~$0.02 | No |
| Narratives (6 domains) | Sonnet | ~$0.20-0.30 | Yes (6 parallel) |
| Executive Narrative | Sonnet | ~$0.05-0.10 | No |
| **Total** | | **~$0.70-1.20** | |

---

## Key Data Objects

### Fact (from Discovery)
```json
{
  "fact_id": "F-INFRA-001",
  "domain": "infrastructure",
  "category": "cloud",
  "item": "AWS is primary cloud provider",
  "details": {"provider": "AWS", "regions": ["us-east-1"]},
  "status": "documented",
  "evidence": {"exact_quote": "...", "source_section": "..."},
  "entity": "target"
}
```

### Gap (from Discovery)
```json
{
  "gap_id": "G-SEC-001",
  "domain": "cybersecurity",
  "category": "compliance",
  "description": "No SOC 2 certification mentioned",
  "importance": "high"
}
```

### Risk (from Reasoning)
```json
{
  "finding_id": "R-INFRA-001",
  "domain": "infrastructure",
  "title": "Legacy ERP Dependency",
  "description": "...",
  "severity": "high",
  "mitigation": "...",
  "based_on_facts": ["F-APP-003", "F-INFRA-007"]
}
```

### Work Item (from Reasoning)
```json
{
  "finding_id": "W-IAM-001",
  "domain": "identity_access",
  "title": "SSO Integration",
  "description": "...",
  "phase": "Day_100",
  "cost_estimate": "50k_to_100k",
  "triggered_by": ["G-IAM-002"],
  "triggered_by_risks": ["R-IAM-001"]
}
```
