# V2 IT Due Diligence Agent - System Architecture & Optimization Analysis

## Purpose of This Document

This document describes the architecture, execution flow, and optimization opportunities for an AI-powered IT due diligence analysis system. The system uses Claude (Anthropic's LLM) to analyze IT documentation and produce risk assessments, work items, and recommendations for M&A transactions.

We are seeking feedback on the proposed optimizations and any additional approaches we may have missed.

---

## 1. System Overview

### What It Does

The system ingests IT documentation (PDFs, text files) from a target company in an M&A transaction and produces:
- **Facts**: Structured inventory of IT assets (servers, applications, security tools, etc.)
- **Gaps**: Missing information that should be investigated
- **Risks**: Identified issues with severity ratings and mitigations
- **Work Items**: Phased integration tasks (Day 1, Day 100, etc.)
- **Recommendations**: Strategic guidance for the deal team

### Architecture: Two-Phase Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: DISCOVERY                          │
│                                                                     │
│  Document Text ──► Discovery Agent (Haiku) ──► FactStore           │
│                         │                           │               │
│                    Tool Calls:                 Stores:              │
│                    - create_inventory_entry    - Facts (F-XXX-001)  │
│                    - flag_gap                  - Gaps (G-XXX-001)   │
│                    - complete_discovery                             │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PHASE 2: REASONING                          │
│                                                                     │
│  FactStore ──► Reasoning Agent (Sonnet) ──► ReasoningStore         │
│                         │                           │               │
│                    Tool Calls:                 Stores:              │
│                    - identify_risk             - Risks (R-001)      │
│                    - create_strategic_...      - Considerations     │
│                    - create_work_item          - Work Items         │
│                    - create_recommendation     - Recommendations    │
│                    - complete_reasoning                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Domain Coverage

The system analyzes 6 IT domains, each with its own discovery and reasoning agent:

| Domain | Categories |
|--------|------------|
| Infrastructure | hosting, compute, storage, backup_dr, cloud, legacy, tooling |
| Network | wan, lan, remote_access, dns_dhcp, load_balancing, network_security, monitoring |
| Cybersecurity | endpoint, perimeter, detection, vulnerability, compliance, incident_response, governance |
| Applications | erp, crm, custom, saas, integration, development, database |
| Identity & Access | directory, authentication, privileged_access, provisioning, sso, mfa, governance |
| Organization | structure, staffing, vendors, skills, processes, budget, roadmap |

### Model Tiering

| Phase | Model | Rationale | Pricing (per 1M tokens) |
|-------|-------|-----------|-------------------------|
| Discovery | Claude 3.5 Haiku | Simpler extraction task, cost-efficient | $0.25 in / $1.25 out |
| Reasoning | Claude Sonnet 4 | Complex analysis requires stronger reasoning | $3.00 in / $15.00 out |

---

## 2. Execution Flow (Detailed)

### Discovery Agent Loop

```python
def discover(self, document_text: str):
    # Build initial message with document
    self.messages = [{"role": "user", "content": document_text}]

    iteration = 0
    while not self.discovery_complete and iteration < self.max_iterations:  # max = 30
        iteration += 1

        # API call - sends system prompt + tools + messages every time
        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            system=self.system_prompt,      # ~7,000 tokens (static)
            tools=DISCOVERY_TOOLS,          # ~8,000 tokens (static)
            messages=self.messages          # Growing conversation history
        )

        # Process tool calls
        for tool_call in response.content:
            if tool_call.type == "tool_use":
                result = execute_tool(tool_call.name, tool_call.input)
                # Tool results added to message history

        # Check if agent signaled completion
        if "complete_discovery" was called:
            self.discovery_complete = True
```

**Key Observation**: The `system` prompt and `tools` are identical on every iteration but are sent (and billed) repeatedly.

### Reasoning Agent Loop

```python
def reason(self, deal_context: Dict):
    # Get facts from discovery phase
    inventory_text = self.fact_store.format_for_reasoning(self.domain)

    # Build system prompt with inventory injected
    system_prompt = self.system_prompt.replace("{inventory}", inventory_text)

    iteration = 0
    while not self.reasoning_complete and iteration < self.max_iterations:  # max = 40
        iteration += 1

        # API call
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            system=system_prompt,           # ~7,000 base + 4,000-8,000 inventory
            tools=REASONING_TOOLS,          # ~11,000 tokens (static)
            messages=self.messages          # Growing conversation history
        )

        # Process tool calls (identify_risk, create_work_item, etc.)
        for tool_call in response.content:
            result = execute_tool(tool_call.name, tool_call.input)
            # Findings stored in ReasoningStore with fact citations
```

**Key Observation**: The inventory (all discovered facts) is embedded in the system prompt and sent on every iteration, even though it never changes during reasoning.

### Parallel Execution

```python
# Discovery runs in parallel across domains (max 3 concurrent)
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(run_discovery, domain): domain
        for domain in ["infrastructure", "network", "cybersecurity", ...]
    }

# Reasoning cannot start until ALL discovery completes (data dependency)
# Then reasoning runs in parallel across domains
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(run_reasoning, domain): domain
        for domain in domains_with_facts
    }
```

---

## 3. Current Token Consumption Analysis

### Per-Iteration Token Breakdown

#### Discovery Phase (Haiku)
```
Component                    Tokens      Notes
─────────────────────────────────────────────────────
System prompt                7,000       Static, sent every iteration
Tool definitions             8,000       Static, sent every iteration
Document excerpt             1,000       Varies by document
Message history              500-5,000   Grows each iteration
─────────────────────────────────────────────────────
Total per iteration          16,500-20,000
```

#### Reasoning Phase (Sonnet)
```
Component                    Tokens      Notes
─────────────────────────────────────────────────────
System prompt (base)         7,000       Static
Inventory injection          4,000-8,000 Static after discovery, sent every iteration
Tool definitions             11,000      Static, sent every iteration
Deal context                 500         Optional, static
Message history              500-25,000  Grows significantly
─────────────────────────────────────────────────────
Total per iteration          23,000-51,000
```

### Full Run Estimate (6 Domains)

```
DISCOVERY (Haiku @ $0.25/$1.25 per 1M tokens)
─────────────────────────────────────────────
Iterations:     30 max × 6 domains = 180 iterations
Input tokens:   18,000 avg × 180 = 3,240,000 tokens
Output tokens:  3,000 avg × 180 = 540,000 tokens
Cost:           (3.24 × $0.25) + (0.54 × $1.25) = $1.49

REASONING (Sonnet @ $3.00/$15.00 per 1M tokens)
─────────────────────────────────────────────
Iterations:     40 max × 6 domains = 240 iterations
Input tokens:   35,000 avg × 240 = 8,400,000 tokens
Output tokens:  4,000 avg × 240 = 960,000 tokens
Cost:           (8.4 × $3.00) + (0.96 × $15.00) = $39.60

TOTAL ESTIMATED COST: ~$41-45 per full analysis
```

### Where Tokens Are Wasted

| Waste Category | Tokens Wasted | % of Total | Root Cause |
|----------------|---------------|------------|------------|
| Repeated system prompts | 2,800,000 | 22% | No caching, sent every iteration |
| Repeated tool definitions | 4,200,000 | 33% | No caching, sent every iteration |
| Repeated inventory | 1,600,000 | 13% | Embedded in system prompt |
| Unnecessary iterations | 1,500,000 | 12% | No early stopping when converged |
| **Total Waste** | **~10,100,000** | **~80%** | |

---

## 4. Proposed Optimizations

### Optimization 1: Prompt Caching

**Problem**: System prompts (~7,000 tokens) and tool definitions (~8,000-11,000 tokens) are sent on every API call, billed at full price each time.

**Solution**: Use Anthropic's prompt caching feature. Mark static content with `cache_control`, and subsequent requests pay only 25% for cached content.

**Implementation**:
```python
# Current
response = client.messages.create(
    system=system_prompt,
    tools=tools,
    messages=messages
)

# Optimized
response = client.messages.create(
    system=[{
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"}
    }],
    tools=tools,  # Also cached with beta header
    messages=messages,
    extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
)
```

**Expected Savings**:
- First call: Full price
- Calls 2-N: 25% price for cached portions
- Net savings: ~$12-15 per run (30-35%)

**Risks/Trade-offs**:
- Cache expires after 5 minutes of inactivity
- Requires SDK version 0.25+

---

### Optimization 2: Dynamic Iteration Limits (Early Stopping)

**Problem**: Agents iterate up to max_iterations (30 for discovery, 40 for reasoning) even when they've exhausted useful work. Many runs show diminishing returns after iteration 10-15.

**Observed Pattern**:
```
Iteration 1-5:   15 facts extracted (3.0 per iteration)
Iteration 6-10:  8 facts extracted (1.6 per iteration)
Iteration 11-15: 3 facts extracted (0.6 per iteration)
Iteration 16-25: 1 fact extracted (0.1 per iteration)  ← Waste
Iteration 26:    complete_discovery called
```

**Solution**: Track extraction rate and trigger completion when converged.

**Implementation**:
```python
stagnant_iterations = 0
facts_before = len(fact_store.facts)

while not complete and iteration < max_iterations:
    iteration += 1
    response = call_model()
    process_response(response)

    # Convergence detection
    facts_after = len(fact_store.facts)
    if facts_after == facts_before:
        stagnant_iterations += 1
    else:
        stagnant_iterations = 0
    facts_before = facts_after

    # Early stopping
    if stagnant_iterations >= 3:
        prompt_agent_to_complete()
```

**Expected Savings**:
- Reduce average iterations from 25 to 12-15
- Save ~40% of iteration costs
- Net savings: ~$8-12 per run

**Risks/Trade-offs**:
- May miss edge-case facts that appear late
- Threshold (3 iterations) may need tuning per domain

---

### Optimization 3: Extract Static Reference Content from Prompts

**Problem**: Reasoning prompts contain a ~100-line "Consideration Library" - a reference guide for analysis patterns. This static content (~4,000 tokens) is sent on every iteration.

**Current Prompt Structure**:
```
[Mission statement - 500 tokens]
[Inventory placeholder - replaced with facts]
[Consideration Library - 4,000 tokens]  ← Static reference material
  - Technical debt patterns
  - Integration complexity patterns
  - Security assessment patterns
  - ...20+ pattern categories
[Quality standards - 500 tokens]
[Workflow instructions - 500 tokens]
```

**Solution**: Move static reference content to tool descriptions (which are cached) or provide via a retrieval tool.

**Option A - Embed in Tool Descriptions**:
```python
# Move patterns to tool definition
{
    "name": "identify_risk",
    "description": """Identify a risk.

    ANALYSIS PATTERNS TO CONSIDER:
    - EOL software: Check versions against vendor lifecycle
    - Capacity constraints: Compare utilization to growth projections
    - Single points of failure: Identify non-redundant components
    ..."""
}
```

**Option B - Retrieval Tool**:
```python
{
    "name": "get_analysis_patterns",
    "description": "Retrieve analysis patterns for a category",
    "input_schema": {
        "properties": {
            "category": {"enum": ["technical_debt", "integration", "security"]}
        }
    }
}

def execute_get_analysis_patterns(category):
    return PATTERN_LIBRARY[category]  # Return only relevant patterns
```

**Expected Savings**:
- 4,000 tokens × 40 iterations × 6 domains = 960,000 tokens
- Net savings: ~$3-4 per run

**Risks/Trade-offs**:
- Option B adds tool call overhead
- May reduce reasoning quality if agent doesn't have patterns in context

---

### Optimization 4: Compress Inventory Injection

**Problem**: The full fact inventory (all details, evidence quotes, metadata) is injected into the system prompt on every reasoning iteration. For 50 facts, this is 4,000-8,000 tokens repeated 40 times.

**Current Inventory Format**:
```markdown
## INFRASTRUCTURE INVENTORY

### HOSTING
**F-INFRA-001**: Primary Data Center
- Details: {"vendor": "Equinix", "location": "Chicago", "tier": "III", "sqft": 5000, "power": "2N", "contract_end": "2025-12-31"}
- Evidence: "The company operates its primary infrastructure from the Equinix CH3 facility located in Chicago, Illinois. This Tier III certified data center provides..."
- Status: documented

**F-INFRA-002**: DR Site
- Details: {"vendor": "Equinix", "location": "Dallas", "tier": "II", "purpose": "disaster_recovery"}
- Evidence: "A secondary disaster recovery site is maintained at Equinix DA1 in Dallas..."
- Status: documented

[... 48 more facts with full details ...]
```

**Solution**: Send a compressed summary and provide full details on-demand via tool.

**Compressed Format**:
```markdown
## INVENTORY SUMMARY (50 facts)

HOSTING (2 facts): Equinix data centers - Chicago (Tier III, primary), Dallas (Tier II, DR)
COMPUTE (12 facts): 180 VMs on VMware 6.7, 15 physical servers (Dell PowerEdge)
STORAGE (5 facts): 500TB NetApp SAN, 200TB Isilon NAS, 50TB Pure FlashArray
BACKUP (3 facts): Veeam B&R, daily backups, 30-day retention, DR tested quarterly
CLOUD (8 facts): AWS (3 accounts, us-east-1), Azure (1 tenant, dev/test)

Fact IDs: F-INFRA-001 through F-INFRA-050
Use get_fact_details(fact_id) to retrieve full information for any fact.
```

**New Tool**:
```python
{
    "name": "get_fact_details",
    "description": "Retrieve full details and evidence for a specific fact",
    "input_schema": {
        "properties": {
            "fact_id": {"type": "string", "description": "Fact ID, e.g., F-INFRA-001"}
        }
    }
}
```

**Expected Savings**:
- Reduce inventory from 6,000 to 800 tokens
- 5,200 tokens × 40 iterations × 6 domains = 1,248,000 tokens
- Net savings: ~$5-10 per run

**Risks/Trade-offs**:
- Agent must make tool calls to get details (adds latency)
- May reduce reasoning quality if agent doesn't retrieve relevant facts
- Citation accuracy may decrease without full context

---

### Optimization 5: Two-Phase Discovery (Extraction + Validation)

**Problem**: The current discovery loop uses the LLM for both extraction AND validation. The LLM:
1. Reads the document
2. Extracts facts
3. Checks for duplicates (via tool responses)
4. Re-reads sections it may have missed
5. Validates its own work

This is expensive because validation logic runs inside the LLM loop.

**Current Flow**:
```
Document → LLM Loop (30 iterations) → Validated Facts
              ↑                ↓
              ← duplicate? ←──┘
              ← short quote? ←┘
```

**Proposed Flow**:
```
Document → LLM Extraction (1-3 calls) → Raw Facts
                                            ↓
                    Python Validation (no LLM) → Validated Facts
                    - Deduplicate by similarity
                    - Verify quotes exist in document
                    - Normalize categories
                                            ↓
              LLM Enrichment (targeted calls) → Enriched Facts
              - Fill in missing details only
```

**Implementation**:

Phase 1 - Extraction (LLM, simplified prompt):
```python
EXTRACTION_PROMPT = """
Extract ALL IT assets from this document. For each, provide:
- item: Name/description
- category: hosting/compute/storage/etc.
- quote: Exact text from document

Do NOT analyze or validate. Extract everything you find.
Output as JSON array.
"""

response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=8192,  # One big extraction
    system=EXTRACTION_PROMPT,
    messages=[{"role": "user", "content": document_text}]
)
raw_facts = parse_json(response.content)
```

Phase 2 - Validation (Python, no LLM):
```python
def validate_facts(raw_facts, document_text):
    validated = []
    seen = set()

    for fact in raw_facts:
        # Check quote exists (fuzzy match)
        if not fuzzy_match(fact["quote"], document_text, threshold=0.8):
            continue  # Hallucinated quote

        # Check duplicate (similarity)
        normalized = normalize(fact["item"])
        if any(similarity(normalized, s) > 0.85 for s in seen):
            continue  # Duplicate
        seen.add(normalized)

        validated.append(fact)

    return validated
```

Phase 3 - Enrichment (LLM, targeted):
```python
# Only for facts missing key details
incomplete = [f for f in validated if not f.get("vendor") or not f.get("version")]

for fact in incomplete:
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"Extract vendor and version for: {fact['item']}\nContext: {fact['quote']}"
        }]
    )
    fact.update(parse_response(response))
```

**Expected Savings**:
- Current: 30 iterations × 18,000 tokens = 540,000 tokens/domain
- Proposed: 1 extraction (50,000) + validation (0) + 10 enrichments (5,000) = 55,000 tokens/domain
- Reduction: ~90% on discovery phase
- Net savings: ~$1.20 per run (discovery is already cheap)

**Risks/Trade-offs**:
- Single-pass extraction may miss facts that require multi-step reasoning
- JSON parsing may fail on malformed output
- Loses the iterative refinement capability

---

### Optimization 6: Lazy/Pipelined Reasoning

**Problem**: Reasoning phase cannot start until ALL discovery phases complete. With 6 domains running in parallel (max 3 concurrent), we have:

```
Time 0    ────────────────────────────────────────────────────►

Discovery: [Infra]  [Net]   [Cyber]  ← Batch 1
           [Apps]   [IAM]   [Org]    ← Batch 2 (waits for batch 1)
                                     ↓
Reasoning:                           [All 6 domains start here]
```

The reasoning phase for infrastructure could start as soon as infrastructure discovery finishes, but it waits for all 6 domains.

**Solution**: Pipeline reasoning to start per-domain as soon as that domain's discovery completes.

**Implementation**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def analyze_domain(domain, document_text, fact_store):
    # Run discovery
    discovery_result = await run_discovery(domain, document_text, fact_store)

    # Immediately start reasoning for this domain
    reasoning_result = await run_reasoning(domain, fact_store)

    return {domain: {"discovery": discovery_result, "reasoning": reasoning_result}}

async def main(document_text):
    fact_store = FactStore()

    # All domains run independently
    tasks = [
        analyze_domain(domain, document_text, fact_store)
        for domain in DOMAINS
    ]

    results = await asyncio.gather(*tasks)
    return merge_results(results)
```

**Expected Savings**:
- Wall-clock time reduction: 30-40%
- Token cost: No change (same work, different timing)

**Risks/Trade-offs**:
- More complex orchestration
- Cross-domain insights may be missed (e.g., network facts informing infrastructure reasoning)
- Would need a final "cross-domain synthesis" pass

---

### Optimization 7: Batch API for Non-Urgent Analysis

**Problem**: All API calls are synchronous, waiting for immediate response. For batch analysis of multiple documents, this is inefficient.

**Solution**: Use Anthropic's Batch API for non-urgent processing at 50% cost.

**Implementation**:
```python
# Create batch
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": f"discovery-{domain}",
            "params": {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": messages
            }
        }
        for domain in DOMAINS
    ]
)

# Poll for completion (async)
while batch.status != "completed":
    await asyncio.sleep(60)
    batch = client.messages.batches.retrieve(batch.id)

# Get results
results = client.messages.batches.results(batch.id)
```

**Expected Savings**:
- 50% cost reduction on all API calls
- Trade-off: Results in minutes/hours, not seconds

**Risks/Trade-offs**:
- Not suitable for interactive/real-time use
- Agentic loops become complex (need to batch tool results)
- 24-hour maximum processing window

---

## 5. Summary: Optimization Impact Matrix

| Optimization | Implementation Effort | Cost Savings | Speed Improvement | Risk Level |
|--------------|----------------------|--------------|-------------------|------------|
| Prompt Caching | 15 minutes | 30-35% | None | Very Low |
| Early Stopping | 1 hour | 15-20% | 30-40% | Low |
| Extract Reference Content | 30 minutes | 5-8% | None | Low |
| Compress Inventory | 2 hours | 10-15% | Slight decrease | Medium |
| Two-Phase Discovery | 4 hours | 2-3% (discovery cheap) | 20% | Medium |
| Pipelined Reasoning | 3 hours | None | 30-40% | Medium |
| Batch API | 2 hours | 50% | Negative (async) | Low |

### Recommended Implementation Order

1. **Prompt Caching** (15 min) - Immediate 30-35% savings, no risk
2. **Early Stopping** (1 hr) - Additional 15-20% savings, low risk
3. **Extract Reference Content** (30 min) - Additional 5-8% savings
4. **Compress Inventory** (2 hrs) - Additional 10-15% savings, needs quality validation
5. **Pipelined Reasoning** (3 hrs) - 30-40% wall-clock improvement

**Conservative Estimate**: Optimizations 1-3 would reduce cost from ~$44 to ~$22-25 per run (45-50% reduction) with minimal implementation risk.

---

## 6. Questions for Review

1. **Prompt Caching**: Are there any downsides to aggressive caching we should consider? Cache invalidation concerns?

2. **Early Stopping**: What's the right threshold for convergence? Should it vary by domain (e.g., security might need more iterations than organization)?

3. **Inventory Compression**: How do we validate that compressed inventory doesn't degrade reasoning quality? What metrics should we track?

4. **Two-Phase Discovery**: Is the complexity worth the savings given discovery is already using the cheaper Haiku model?

5. **Alternative Approaches**: Are there optimization strategies we've missed? Other patterns from production LLM systems?

6. **Trade-offs**: Which optimizations would you prioritize if you could only implement 2-3?

---

## Appendix: File Structure

```
it-diligence-agent/
├── agents_v2/
│   ├── base_discovery_agent.py    # Discovery loop implementation
│   ├── base_reasoning_agent.py    # Reasoning loop implementation
│   ├── discovery/                 # 6 domain-specific discovery agents
│   └── reasoning/                 # 6 domain-specific reasoning agents
├── tools_v2/
│   ├── fact_store.py              # Fact storage with unique IDs
│   ├── discovery_tools.py         # Tool definitions for discovery
│   └── reasoning_tools.py         # Tool definitions for reasoning
├── prompts/
│   ├── v2_*_discovery_prompt.py   # 6 discovery prompts
│   └── v2_*_reasoning_prompt.py   # 6 reasoning prompts
├── config_v2.py                   # Model settings, thresholds
└── main_v2.py                     # Orchestration, parallel execution
```
