# IT Due Diligence Agent
## Technical Deep Dive

---

# SECTION 1: OVERVIEW
## Slides 1-5

---

# Slide 1: The IT DD Challenge

## Why We Built This

| Problem | Impact | Our Solution |
|---------|--------|--------------|
| Manual document review | 80+ hours/deal | AI extraction in minutes |
| Inconsistent methodology | Quality varies | Standardized agents |
| Expensive consultants | $150-300K | Scalable technology |
| Data dumps | No insights | "So what" first |
| No audit trail | "Trust me" | Evidence chain |

### The Gap in the Market

**Existing tools** extract data.
**We provide** the analysis layer that makes data meaningful.

---

# Slide 2: The Brain on Top Philosophy

## Core Design Principles

### 1. Documents Are the Source of Truth
- Facts are **interpretations** of documents
- The document (with hash) is immutable
- Facts can be confirmed, corrected, or rejected

### 2. Extract Everything, Filter Nothing
- All identifiable facts extracted
- Filtering happens in human review
- Nothing missed due to premature filtering

### 3. Inferred Information Is Not a Fact
- If AI must deduce → it's a Gap or Question
- Facts require explicit documentary evidence
- Conclusions require facts

### 4. Draft Until Confirmed
- All output labeled "DRAFT" until facts reviewed
- Provides value immediately
- Honest about confidence levels

---

# Slide 3: System Architecture Overview

## High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                        WEB UI                                │
│                    (Flask + Templates)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                      BLUEPRINTS                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Inventory│  │  Costs  │  │ Upload  │  │  Core   │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└───────────────────────────┼─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                      DATA STORES                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │InventoryStore│  │  FactStore  │  │ReasoningStore│         │
│  │ (Structured) │  │  (Extracted)│  │  (Analyzed) │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└───────────────────────────┼─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                       AGENTS                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │  Discovery Agents   │  │  Reasoning Agents   │           │
│  │  (Haiku - Extract)  │  │  (Sonnet - Analyze) │           │
│  └─────────────────────┘  └─────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

# Slide 4: Three-Funnel Framework

## Sequential Processing Stages

```
┌─────────────────────────────────────────────────────────────┐
│              FUNNEL 1: LOGGING (Data Collection)            │
├─────────────────────────────────────────────────────────────┤
│  IN: Raw documents, extracted text, metadata                │
│  OUT: Document registry, provisional facts, gaps, logs      │
│  RULES: Extract ALL facts, NO inference, link to quotes     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FUNNEL 2: ANALYSIS (Understanding)             │
├─────────────────────────────────────────────────────────────┤
│  IN: Confirmed facts, inventory data, deal context          │
│  OUT: Risks, work items, strategic considerations           │
│  RULES: Must cite facts, consider M&A context               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FUNNEL 3: OUTPUT (Delivery)                    │
├─────────────────────────────────────────────────────────────┤
│  IN: Analysis results, cost calculations                    │
│  OUT: Executive reports, data flow diagrams, cost models    │
│  RULES: Lead with "so what", provide evidence               │
└─────────────────────────────────────────────────────────────┘
```

---

# Slide 5: Key Design Principles

## What Makes This Work

### Deterministic vs AI Processing

| Stage | Processing Type | Why |
|-------|-----------------|-----|
| File parsing | Deterministic | Reproducible |
| Type detection | Deterministic | Consistent |
| Schema validation | Deterministic | Reliable |
| Fact extraction | AI (Haiku) | Pattern recognition |
| Risk analysis | AI (Sonnet) | Reasoning required |

### Separation of Concerns

```
DISCOVERY AGENTS         REASONING AGENTS
────────────────         ────────────────
Extract facts      ──►   Analyze facts
No conclusions           Must cite facts
Fast/cheap (Haiku)       Smart (Sonnet)
```

### Evidence Chain

Every output traces back to source:
```
Risk → Facts → Source Document → Exact Quote
```

---

# SECTION 2: DATA FLOW
## Slides 6-12

---

# Slide 6: Document Ingestion Pipeline

## Stage 1: Getting Data In

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Excel   │  │   Word   │  │   PDF    │  │ Markdown │
│  .xlsx   │  │  .docx   │  │  .pdf    │  │   .md    │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │             │
     └─────────────┴──────┬──────┴─────────────┘
                          │
                          ▼
              ┌───────────────────┐
              │    FILE ROUTER    │
              │   Detect format   │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │   TYPE DETECTOR   │
              │  Application?     │
              │  Infrastructure?  │
              │  Organization?    │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ SCHEMA VALIDATOR  │
              │ Required fields?  │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │  INVENTORY STORE  │
              │   or FACT STORE   │
              └───────────────────┘
```

**Key:** This stage is 100% deterministic. Same input = same output.

---

# Slide 7: File Type Detection & Routing

## How We Know What We're Looking At

### Excel Detection Logic

```python
# Column header patterns
APPLICATION_PATTERNS = [
    "application", "app name", "system", "software"
]
INFRASTRUCTURE_PATTERNS = [
    "server", "hostname", "ip address", "infrastructure"
]
ORGANIZATION_PATTERNS = [
    "employee", "name", "title", "department", "manager"
]
```

### Routing Rules

| Detected Type | Destination | Processing |
|---------------|-------------|------------|
| Application inventory | InventoryStore | Structured import |
| Infrastructure list | InventoryStore | Structured import |
| Org chart | FactStore | Headcount analysis |
| Narrative doc | FactStore | Discovery agents |
| Unknown | Flagged | Human review |

---

# Slide 8: Inventory Store Architecture

## Structured Data Home

### Purpose
Hold structured inventory data with stable, content-based IDs.

### Item Types

| Type | ID Pattern | Example |
|------|------------|---------|
| Application | I-APP-xxxxx | I-APP-0f2c01 |
| Infrastructure | I-INFRA-xxxxx | I-INFRA-a3b2c1 |
| Vendor | I-VEND-xxxxx | I-VEND-7d8e9f |

### Key Fields (Application)

```python
@dataclass
class InventoryItem:
    item_id: str           # I-APP-0f2c01
    inventory_type: str    # "application"
    name: str              # "Salesforce"
    entity: str            # "target" or "buyer"
    status: str            # "active", "planned", "retired"
    data: Dict             # Flexible additional fields
    source_file: str       # Origin document
    created_at: datetime
```

### Content-Based IDs
Same item always gets same ID (based on hash of key fields).
Enables deduplication and matching across documents.

---

# Slide 9: Content-Based ID Generation

## Why IDs Matter

### The Problem
Different documents reference the same things differently:
- "SAP S/4HANA" vs "SAP" vs "S4"
- "Salesforce CRM" vs "SFDC" vs "Salesforce"

### Our Solution

```python
def generate_item_id(item_type: str, name: str, entity: str) -> str:
    """Generate stable ID from content."""
    # Normalize inputs
    normalized = f"{item_type}:{name.lower().strip()}:{entity}"

    # Hash to create ID
    hash_bytes = hashlib.sha256(normalized.encode()).digest()
    short_hash = base64.b32encode(hash_bytes[:4]).decode()[:6].lower()

    return f"I-{item_type.upper()[:4]}-{short_hash}"
```

### Benefits
- Same item always gets same ID
- Can match across documents
- Enables deduplication
- Supports entity resolution

---

# Slide 10: Fact Store Architecture

## Extracted Knowledge Home

### Purpose
Hold facts extracted from documents with evidence chain.

### Fact Structure

```python
@dataclass
class Fact:
    finding_id: str        # F-APP-001
    domain: str            # applications, infrastructure, security
    category: str          # erp, crm, network, etc.
    item: str              # What this fact is about
    attribute: str         # What aspect (users, cost, version)
    value: str             # The extracted value
    confidence: str        # high, medium, low

    # Evidence chain
    source_document_id: str
    exact_quote: str
    source_section: str

    # Lifecycle
    status: str            # draft, confirmed, rejected
    reviewed_by: str
    reviewed_at: datetime
```

### Domains

| Domain | Covers |
|--------|--------|
| applications | ERP, CRM, custom apps, SaaS |
| infrastructure | Servers, storage, network, cloud |
| security | IAM, MFA, encryption, compliance |
| organization | Headcount, roles, reporting |
| network | Connectivity, WAN, internet |

---

# Slide 11: Evidence Chain Implementation

## From Risk to Source

### Data Model

```
┌─────────────────────────────────────────────────────────────┐
│                         RISK                                 │
│  finding_id: R-APP-001                                      │
│  citing_facts: ["F-APP-001", "F-APP-003", "F-APP-007"]     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         FACT                                 │
│  finding_id: F-APP-001                                      │
│  source_document_id: DOC-a7f3c2                            │
│  exact_quote: "SAP S/4HANA serves as our core ERP..."      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       DOCUMENT                               │
│  document_id: DOC-a7f3c2                                    │
│  file_hash: sha256:a7f3c2d8e9f0...                         │
│  file_name: "Application_Inventory.xlsx"                    │
└─────────────────────────────────────────────────────────────┘
```

### Query Pattern

```python
def get_evidence_chain(risk_id: str):
    risk = reasoning_store.get_risk(risk_id)
    facts = [fact_store.get(f_id) for f_id in risk.citing_facts]
    documents = [doc_store.get(f.source_document_id) for f in facts]
    return risk, facts, documents
```

---

# Slide 12: Two Data Systems

## FactStore vs InventoryStore

### The Challenge
Two sources of truth that must align:
- **FactStore**: 38 facts from discovery agents (unstructured)
- **InventoryStore**: 33 apps from structured imports (Excel)

### Resolution Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA RESOLUTION                           │
│                                                             │
│   ROUTE tries:                                              │
│   1. InventoryStore first (structured = higher quality)     │
│   2. Fall back to FactStore (if no structured data)        │
│   3. Merge when both exist                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Bridge Functions

```python
def build_applications_from_inventory_store(inv_store):
    """Build application list from structured inventory."""
    apps = inv_store.get_items(
        inventory_type="application",
        entity="target",
        status="active"
    )
    return [convert_to_app_model(app) for app in apps]
```

### When to Use Which

| Use Case | Source |
|----------|--------|
| Application list | InventoryStore |
| Application facts | FactStore |
| Cost data | InventoryStore |
| Narrative insights | FactStore |

---

# SECTION 3: AGENTS
## Slides 13-20

---

# Slide 13: Discovery vs Reasoning Agents

## Two-Phase Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DISCOVERY AGENTS                          │
│                    (Haiku - Fast/Cheap)                      │
├─────────────────────────────────────────────────────────────┤
│  PURPOSE: Extract facts from documents                       │
│  COST: ~$0.01 per document                                  │
│  MODEL: Claude Haiku (fast, cheap)                          │
│                                                             │
│  RULES:                                                     │
│  • Extract ALL facts, even low confidence                   │
│  • NO inference - only explicit statements                  │
│  • Every fact links to exact quote                          │
│  • Call "complete" when document exhausted                  │
└─────────────────────────────────────────────────────────────┘
                            │
                    Facts locked
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    REASONING AGENTS                          │
│                    (Sonnet - Smart)                          │
├─────────────────────────────────────────────────────────────┤
│  PURPOSE: Analyze facts, find the "so what"                 │
│  COST: ~$0.05 per domain                                    │
│  MODEL: Claude Sonnet (smart, nuanced)                      │
│                                                             │
│  RULES:                                                     │
│  • MUST cite facts for every conclusion                     │
│  • Consider M&A context (carve-out, acquisition)           │
│  • Generate risks with severity + mitigation                │
│  • Generate work items with phase + cost                    │
└─────────────────────────────────────────────────────────────┘
```

---

# Slide 14: Discovery Agent Deep Dive

## How Facts Get Extracted

### Agent Configuration

```python
DISCOVERY_AGENT_CONFIG = {
    "model": "claude-3-haiku",
    "max_tokens": 4096,
    "tools": [
        "create_fact",
        "flag_gap",
        "complete"
    ],
    "system_prompt": """
    You are an IT due diligence fact extractor.

    For each document:
    1. Read thoroughly
    2. Extract EVERY fact about IT systems
    3. Provide exact quotes as evidence
    4. Flag gaps where info should exist but doesn't
    5. Call complete when done

    RULES:
    - Only extract explicit statements
    - Never infer or deduce
    - Low confidence facts still get extracted
    """
}
```

### Processing Loop

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│  Document  │ ──► │   Agent    │ ──► │   Facts    │
│   Text     │     │  Process   │     │   Store    │
└────────────┘     └────────────┘     └────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Tool calls:     │
              │ • create_fact() │
              │ • flag_gap()    │
              │ • complete()    │
              └─────────────────┘
```

---

# Slide 15: Fact Extraction Rules

## What Makes a Valid Fact

### Required Elements

| Element | Description | Example |
|---------|-------------|---------|
| **Item** | What the fact is about | "SAP S/4HANA" |
| **Attribute** | What aspect | "user_count" |
| **Value** | The extracted value | "500" |
| **Quote** | Exact text from doc | "approximately 500 active users" |
| **Source** | Document section | "IT Overview, page 3" |

### Valid vs Invalid Facts

| Statement | Valid? | Why |
|-----------|--------|-----|
| "SAP has 500 users" (doc says this) | ✓ Valid | Explicit statement |
| "SAP is probably critical" (not stated) | ✗ Invalid | Inference |
| "They likely use AWS" (not stated) | ✗ Invalid | Assumption |
| "No DR plan mentioned" | ✓ Valid (Gap) | Absence is factual |

### Confidence Levels

```python
CONFIDENCE_RULES = {
    "high": "Explicitly stated with specific numbers",
    "medium": "Stated but somewhat ambiguous",
    "low": "Implied or partially stated"
}
```

---

# Slide 16: Reasoning Agent Deep Dive

## How Insights Get Generated

### Agent Configuration

```python
REASONING_AGENT_CONFIG = {
    "model": "claude-3-sonnet",
    "max_tokens": 8192,
    "tools": [
        "create_risk",
        "create_work_item",
        "create_recommendation",
        "complete"
    ],
    "system_prompt": """
    You are an M&A IT due diligence analyst.

    Given facts about a target company's IT:
    1. Identify risks with M&A implications
    2. Create work items for integration
    3. Provide recommendations

    RULES:
    - EVERY conclusion must cite specific facts
    - Consider deal context (carve-out vs acquisition)
    - Provide severity ratings with rationale
    - Include cost estimates using standard ranges
    """
}
```

### Input Context

```python
reasoning_input = {
    "facts": all_facts_for_domain,
    "inventory": relevant_inventory_items,
    "deal_context": {
        "type": "carve_out",  # or "acquisition", "merger"
        "buyer_has": ["SAP", "Azure"],
        "timeline": "6 months to close"
    }
}
```

---

# Slide 17: Risk Generation Logic

## How Risks Are Created

### Risk Tool Schema

```python
def create_risk(
    domain: str,           # applications, infrastructure, etc.
    title: str,            # Clear statement of risk
    description: str,      # Full explanation
    severity: str,         # critical, high, medium, low
    so_what: str,          # M&A implication
    mitigation: str,       # Recommended approach
    citing_facts: List[str],  # REQUIRED - fact IDs
    timeline: str,         # When this matters
    mna_lens: str          # valuation, integration, tsa_exposure
) -> Risk:
```

### Severity Guidelines

| Level | Criteria |
|-------|----------|
| **Critical** | Blocks close, >$1M impact, safety/legal |
| **High** | Day 1 issue, $500K-$1M, major integration |
| **Medium** | Day 100 issue, $100K-$500K, moderate effort |
| **Low** | Post-100, <$100K, nice to address |

### M&A Lenses

```python
MNA_LENSES = [
    "day_1_continuity",    # Will business run on Day 1?
    "tsa_exposure",        # Transition services needed?
    "integration_cost",    # What will integration cost?
    "synergy_potential",   # Can we reduce costs?
    "valuation_impact",    # Affects deal price?
    "hidden_liability"     # Undisclosed obligations?
]
```

---

# Slide 18: Work Item Generation

## From Risk to Action

### Work Item Tool Schema

```python
def create_work_item(
    domain: str,
    title: str,            # What needs to be done
    description: str,      # Full details
    phase: str,            # Day_1, Day_100, Post_100
    priority: str,         # critical, high, medium, low
    owner_type: str,       # buyer, target, shared, vendor
    cost_estimate: str,    # under_25k, 25k_to_100k, etc.
    triggered_by: List[str],    # Fact IDs
    triggered_by_risks: List[str],  # Risk IDs
    dependencies: List[str],    # Other work item IDs
    reasoning: str         # WHY this work is needed
) -> WorkItem:
```

### Phase Definitions

| Phase | Timeline | Focus |
|-------|----------|-------|
| **Day_1** | Close date | Business must run |
| **Day_100** | First 100 days | Initial integration |
| **Post_100** | After 100 days | Optimization |

### Cost Estimate Ranges

```python
COST_RANGES = {
    "under_25k": {"low": 0, "high": 25_000},
    "25k_to_100k": {"low": 25_000, "high": 100_000},
    "100k_to_500k": {"low": 100_000, "high": 500_000},
    "500k_to_1m": {"low": 500_000, "high": 1_000_000},
    "over_1m": {"low": 1_000_000, "high": 2_500_000}
}
```

---

# Slide 19: Cost Estimation Engine

## Turning Work Items into Dollars

### Cost Calculation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Work Items  │ ──► │ Cost Range  │ ──► │ Aggregated  │
│ with keys   │     │ Lookup      │     │ Totals      │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Aggregation Logic

```python
def calculate_one_time_costs(work_items):
    """Calculate total one-time costs by phase."""

    totals = {"low": 0, "high": 0}
    by_phase = {}

    for wi in work_items:
        cost_key = wi.cost_estimate  # e.g., "100k_to_500k"
        cost_range = COST_RANGES.get(cost_key)

        if cost_range:
            totals["low"] += cost_range["low"]
            totals["high"] += cost_range["high"]

            # Group by phase
            phase = wi.phase
            if phase not in by_phase:
                by_phase[phase] = {"low": 0, "high": 0, "items": []}
            by_phase[phase]["low"] += cost_range["low"]
            by_phase[phase]["high"] += cost_range["high"]
            by_phase[phase]["items"].append(wi)

    totals["mid"] = (totals["low"] + totals["high"]) / 2
    return totals, by_phase
```

---

# Slide 20: Model Selection Strategy

## Haiku vs Sonnet

### When to Use Which

| Task | Model | Why |
|------|-------|-----|
| Fact extraction | Haiku | Volume, cost, speed |
| Type detection | Haiku | Simple classification |
| Risk analysis | Sonnet | Nuanced reasoning |
| Cost estimation | Sonnet | Judgment required |
| Report generation | Sonnet | Quality writing |

### Cost Comparison

| Model | Input (1M tokens) | Output (1M tokens) |
|-------|-------------------|---------------------|
| Haiku | $0.25 | $1.25 |
| Sonnet | $3.00 | $15.00 |

### Typical Deal Cost

| Stage | Calls | Model | Cost |
|-------|-------|-------|------|
| Document parsing | 20 | Haiku | ~$0.50 |
| Fact extraction | 20 | Haiku | ~$1.00 |
| Reasoning (6 domains) | 6 | Sonnet | ~$3.00 |
| **Total** | | | **~$4.50** |

---

# SECTION 4: COST CENTER
## Slides 21-24

---

# Slide 21: Cost Center Architecture

## All Costs in One Place

### Data Model

```python
@dataclass
class CostCenterData:
    run_rate: RunRateCosts      # Annual recurring
    one_time: OneTimeCosts      # Integration costs
    synergies: List[Synergy]    # Savings opportunities
    insights: List[Insight]     # Auto-generated commentary
    data_quality: Dict          # Confidence per source
```

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      COST CENTER                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │             EXECUTIVE SUMMARY                        │   │
│  │  Run-Rate: $36.1M │ One-Time: $2.2M-$8.4M          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ RUN-RATE │  │ ONE-TIME │  │ SYNERGIES│  │ INSIGHTS │   │
│  │ (Tab 1)  │  │ (Tab 2)  │  │ (Tab 3)  │  │ (Tab 4)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# Slide 22: Run-Rate Cost Gathering

## Annual Recurring Costs

### Sources

| Category | Source | Method |
|----------|--------|--------|
| Headcount | FactStore | Organization analysis |
| Applications | InventoryStore | Sum of license costs |
| Infrastructure | InventoryStore | Sum of infra costs |
| Vendors/MSP | FactStore | Contract analysis |

### Headcount Calculation

```python
def gather_headcount_costs():
    """Pull headcount costs from organization facts."""

    # Get org facts
    org_facts = fact_store.get_by_domain("organization")

    # Sum by category
    categories = {}
    for fact in org_facts:
        if fact.attribute == "headcount":
            cat = fact.category  # leadership, apps, infra, etc.
            count = int(fact.value)

            # Apply compensation assumptions
            avg_comp = COMP_BY_CATEGORY.get(cat, 100_000)
            cost = count * avg_comp

            categories[cat] = {
                "count": count,
                "avg_comp": avg_comp,
                "total": cost
            }

    return categories
```

### Application Cost Calculation

```python
def gather_application_costs():
    """Pull application costs from inventory."""

    apps = inventory_store.get_items(
        inventory_type="application",
        status="active"
    )

    total = sum(app.data.get("cost", 0) for app in apps)
    return total, apps
```

---

# Slide 23: One-Time Cost Calculation

## Integration Cost Aggregation

### From Work Items to Dollars

```python
def gather_one_time_costs():
    """Aggregate work item costs."""

    COST_RANGE_VALUES = {
        "under_25k": {"low": 0, "high": 25_000},
        "25k_to_100k": {"low": 25_000, "high": 100_000},
        "100k_to_500k": {"low": 100_000, "high": 500_000},
        "500k_to_1m": {"low": 500_000, "high": 1_000_000},
        "over_1m": {"low": 1_000_000, "high": 2_500_000}
    }

    by_phase = {}

    for wi in reasoning_store.work_items:
        cost_key = wi.cost_estimate
        cost_range = COST_RANGE_VALUES.get(cost_key, {"low": 0, "high": 0})

        phase = wi.phase
        if phase not in by_phase:
            by_phase[phase] = {"low": 0, "high": 0, "items": []}

        by_phase[phase]["low"] += cost_range["low"]
        by_phase[phase]["high"] += cost_range["high"]
        by_phase[phase]["items"].append(wi)

    return by_phase
```

### Output Format

| Phase | Work Items | Low | High | Mid |
|-------|------------|-----|------|-----|
| Day_1 | 5 | $275K | $1.0M | $650K |
| Day_100 | 10 | $1.2M | $4.5M | $2.9M |
| Post_100 | 6 | $750K | $2.9M | $1.8M |
| **Total** | **21** | **$2.2M** | **$8.4M** | **$5.3M** |

---

# Slide 24: Synergy Identification

## Finding Cost Savings

### Detection Patterns

```python
SYNERGY_PATTERNS = {
    "dual_platform": {
        "description": "Two systems serving same function",
        "examples": ["Dual ERP", "Dual CRM", "Dual HCM"],
        "savings_range": (0.3, 0.5)  # 30-50% of smaller platform
    },
    "license_optimization": {
        "description": "Unused or underutilized licenses",
        "examples": ["Shelfware", "Duplicate users"],
        "savings_range": (0.1, 0.2)  # 10-20% of license cost
    },
    "vendor_consolidation": {
        "description": "Multiple vendors for same service",
        "examples": ["Multiple MSPs", "Competing tools"],
        "savings_range": (0.15, 0.25)
    }
}
```

### Synergy Calculation

```python
def identify_synergies():
    """Find synergy opportunities from inventory."""

    synergies = []

    # Check for dual platforms
    for func in ["ERP", "CRM", "HCM"]:
        apps = inventory_store.get_by_function(func)
        if len(apps) > 1:
            smaller_cost = min(app.cost for app in apps)
            synergy = {
                "type": "dual_platform",
                "description": f"Dual {func} - consolidation opportunity",
                "annual_savings_low": smaller_cost * 0.3,
                "annual_savings_high": smaller_cost * 0.5,
                "affected_items": [app.name for app in apps]
            }
            synergies.append(synergy)

    return synergies
```

---

# SECTION 5: HUMAN REVIEW
## Slides 25-27

---

# Slide 25: Validation Workflow

## From Draft to Confirmed

### Fact Lifecycle

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  DRAFT   │ ──► │  REVIEW  │ ──► │ CONFIRMED│
│          │     │  QUEUE   │     │          │
└──────────┘     └──────────┘     └──────────┘
                      │
                      ▼
               ┌──────────┐
               │ REJECTED │
               │    or    │
               │ CORRECTED│
               └──────────┘
```

### Status Definitions

| Status | Meaning |
|--------|---------|
| **draft** | AI-extracted, not yet reviewed |
| **pending_review** | Queued for human review |
| **confirmed** | Human verified as correct |
| **corrected** | Human fixed an error |
| **rejected** | Human determined invalid |

### Confidence Impact

| Fact Status | Analysis Confidence |
|-------------|---------------------|
| All confirmed | High |
| Mix confirmed/draft | Medium |
| All draft | Low (labeled "DRAFT") |

---

# Slide 26: SME Verification Process

## Expert Review for High-Value Items

### What Gets Flagged for SME

| Trigger | Example | SME Type |
|---------|---------|----------|
| Cost > $500K | ERP migration estimate | Finance |
| Security gap | No MFA for admins | Security |
| Key person risk | Single DBA | HR/Ops |
| Contract issue | Auto-renewal clause | Legal |

### Verification Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                   SME VERIFICATION QUEUE                     │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │ ERP Migration Cost Estimate                         │    │
│  │ Current: $1.5M - $6M                               │    │
│  │ Confidence: Medium                                  │    │
│  │                                                     │    │
│  │ SME Action:                                         │    │
│  │ ○ Confirm estimate                                  │    │
│  │ ○ Adjust range: [____] - [____]                    │    │
│  │ ○ Add context: [________________________]          │    │
│  │                                                     │    │
│  │ [Approve] [Request More Info] [Reject]             │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# Slide 27: Correction & Learning Loop

## Improving Over Time

### Correction Recording

```python
@dataclass
class Correction:
    finding_id: str
    original_value: str
    corrected_value: str
    correction_type: str  # value_error, misattribution, false_positive
    corrected_by: str
    corrected_at: datetime
    notes: str
```

### Learning Patterns

| Error Type | Example | System Response |
|------------|---------|-----------------|
| Value error | "500 users" → "5000 users" | Highlight similar patterns |
| Misattribution | Wrong app assigned | Improve entity resolution |
| False positive | Extracted non-fact | Adjust extraction threshold |
| Missing fact | Human found more | Flag similar gaps |

### Feedback to Agents

```python
def apply_correction_feedback(correction):
    """Use corrections to improve future runs."""

    # Log correction pattern
    pattern = {
        "domain": correction.domain,
        "error_type": correction.correction_type,
        "original": correction.original_value,
        "corrected": correction.corrected_value
    }
    correction_patterns.append(pattern)

    # Update agent context for similar items
    if similar_items := find_similar(correction):
        for item in similar_items:
            item.flag_for_review(
                reason=f"Similar to corrected item {correction.finding_id}"
            )
```

---

# SECTION 6: OPERATIONS
## Slides 28-30

---

# Slide 28: Deployment Architecture

## Docker-Based Deployment

### Container Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   APP    │  │  WORKER  │  │ POSTGRES │  │  REDIS   │   │
│  │  :5001   │  │ (Celery) │  │  :5432   │  │  :6379   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                             │
│  ┌──────────┐  ┌──────────┐                                │
│  │  MINIO   │  │  BEAT    │                                │
│  │  :9000   │  │(Scheduler)│                                │
│  └──────────┘  └──────────┘                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Quick Start

```bash
# Navigate to docker directory
cd docker/

# Start all services
docker-compose up

# Access application
open http://localhost:5001
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| ANTHROPIC_API_KEY | AI API access | Required |
| FLASK_SECRET_KEY | Session encryption | Generated |
| DATABASE_URL | PostgreSQL connection | Docker internal |
| REDIS_URL | Redis connection | Docker internal |

---

# Slide 29: Extending the System

## How to Add New Capabilities

### Adding a New Discovery Agent

```python
# 1. Create agent configuration
NEW_AGENT_CONFIG = {
    "name": "vendor_discovery",
    "domain": "vendors",
    "model": "claude-3-haiku",
    "system_prompt": """...""",
    "tools": ["create_fact", "flag_gap", "complete"]
}

# 2. Register in agent registry
DISCOVERY_AGENTS["vendors"] = NEW_AGENT_CONFIG

# 3. Add domain to FactStore
VALID_DOMAINS.append("vendors")
```

### Adding a New Cost Category

```python
# 1. Add gathering function
def gather_vendor_costs():
    vendor_items = inventory_store.get_items(
        inventory_type="vendor"
    )
    return sum(v.data.get("annual_cost", 0) for v in vendor_items)

# 2. Add to Cost Center
run_rate.vendors = CostCategory(
    name="vendors",
    display_name="Vendor & MSP",
    total=gather_vendor_costs()
)
```

### Adding a New Report Type

```python
# 1. Create template
# templates/reports/vendor_analysis.html

# 2. Create route
@app.route('/reports/vendors')
def vendor_report():
    vendors = inventory_store.get_items(inventory_type="vendor")
    return render_template('reports/vendor_analysis.html',
                          vendors=vendors)
```

---

# Slide 30: Troubleshooting & Maintenance

## Common Issues and Solutions

### Issue: Facts Not Extracting

```
Symptom: Document uploaded but no facts created
```

| Check | Solution |
|-------|----------|
| Document readable? | Check file format |
| Agent running? | Check Celery worker logs |
| API key valid? | Verify ANTHROPIC_API_KEY |
| Rate limited? | Wait and retry |

### Issue: Costs Showing $0

```
Symptom: Cost Center shows $0 for category
```

| Check | Solution |
|-------|----------|
| Data exists? | Check InventoryStore count |
| Cost field populated? | Verify source data has costs |
| Correct attribute name? | Check cost_estimate vs cost |

### Issue: Evidence Chain Broken

```
Symptom: Risk doesn't link to facts
```

| Check | Solution |
|-------|----------|
| Fact IDs valid? | Verify citing_facts list |
| Facts in store? | Check FactStore for IDs |
| Source doc exists? | Verify document registry |

### Maintenance Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Clear old sessions | Weekly | `python scripts/cleanup_sessions.py` |
| Backup database | Daily | `pg_dump diligence > backup.sql` |
| Check disk space | Weekly | `df -h /app/data` |
| Review error logs | Daily | `docker logs app --tail 100` |

---

# Summary

## Key Technical Concepts

| Concept | Implementation |
|---------|----------------|
| **Evidence Chain** | Risk → Facts → Documents → Quotes |
| **Two-Phase Agents** | Discovery (extract) → Reasoning (analyze) |
| **Dual Data Stores** | FactStore + InventoryStore |
| **Cost Center** | Run-rate + One-time + Synergies |
| **Human Review** | Draft → Review → Confirmed |

## Architecture Principles

1. **Documents are source of truth**
2. **Extract everything, filter later**
3. **No inference without evidence**
4. **Transparent about uncertainty**
5. **Separation of discovery and reasoning**

---

*Technical Reference Documentation*
*January 2026*
