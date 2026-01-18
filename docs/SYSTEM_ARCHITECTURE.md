# System Architecture - Technical Deep Dive

## "Is this LangGraph? LangFlow? LangChain?"

**No.** This is a custom-built Python application that calls the Anthropic Claude API directly. No frameworks.

### Why Not Use a Framework?

| Framework | What It Does | Why We Didn't Use It |
|-----------|--------------|---------------------|
| **LangChain** | Abstraction layer over LLM APIs | Adds complexity, abstraction leaks, version churn |
| **LangGraph** | State machine for agent workflows | Overkill for our linear flow, harder to debug |
| **LangFlow** | Visual drag-and-drop agent builder | No-code approach doesn't fit our needs |
| **CrewAI** | Multi-agent role-playing framework | Opinionated structure we don't need |
| **AutoGen** | Microsoft's multi-agent framework | Heavy, enterprise-focused |

### What We Built Instead

A **simple, debuggable, controllable** agent system:

```python
# This is literally how it works:

1. Load system prompt (the "playbook" for the agent)
2. Send prompt + document to Claude API
3. Claude responds with tool calls or text
4. Execute tool calls, append results to conversation
5. Loop until Claude says "done" or max iterations
6. Return structured output
```

**Total lines of code for the core agent loop:** ~200 lines in `base_agent.py`

---

## The Tech Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEPENDENCIES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   anthropic          # Direct API client for Claude              │
│   pymupdf            # PDF text extraction                       │
│   python-dotenv      # Environment variable management           │
│   sqlite3            # Built-in Python - persistence layer       │
│                                                                  │
│   That's it. No LangChain. No vector databases.                 │
│   No embeddings. No RAG pipelines.                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Why So Simple?

1. **Context window is big enough** - Claude handles 200K tokens. We don't need RAG.
2. **We control the prompts** - No framework abstractions hiding what's sent to the model
3. **Debuggable** - When something goes wrong, we can see exactly what happened
4. **Fast iteration** - Change a prompt, run again. No framework ceremony.

---

## How Agents Work

### The Core Pattern

Every agent in this system follows the same pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                         AGENT LOOP                               │
│                                                                  │
│   ┌─────────────┐                                               │
│   │   SYSTEM    │  "You are an infrastructure specialist..."    │
│   │   PROMPT    │  "Use these tools to record findings..."      │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────┐                                               │
│   │  DOCUMENT   │  PDF text extracted and passed in             │
│   │   CONTEXT   │                                               │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────────────────────────────────────────────┐       │
│   │              CLAUDE API CALL                         │       │
│   │                                                      │       │
│   │  Request: system prompt + conversation history       │       │
│   │  Response: text OR tool_use blocks                   │       │
│   └──────────────────────┬──────────────────────────────┘       │
│                          │                                       │
│            ┌─────────────┴─────────────┐                        │
│            │                           │                        │
│            ▼                           ▼                        │
│   ┌─────────────┐            ┌─────────────────┐                │
│   │    TEXT     │            │    TOOL USE     │                │
│   │  (thinking) │            │  (structured    │                │
│   │             │            │   output)       │                │
│   └─────────────┘            └────────┬────────┘                │
│                                       │                          │
│                                       ▼                          │
│                              ┌─────────────────┐                │
│                              │ EXECUTE TOOL    │                │
│                              │                 │                │
│                              │ • Validate input│                │
│                              │ • Store finding │                │
│                              │ • Return result │                │
│                              └────────┬────────┘                │
│                                       │                          │
│                                       ▼                          │
│                              ┌─────────────────┐                │
│                              │ APPEND TO       │                │
│                              │ CONVERSATION    │                │
│                              └────────┬────────┘                │
│                                       │                          │
│                          ┌────────────┴────────────┐            │
│                          │                         │            │
│                          ▼                         ▼            │
│                   ┌────────────┐          ┌─────────────┐       │
│                   │ CONTINUE   │          │    DONE     │       │
│                   │ (loop)     │          │ (complete)  │       │
│                   └────────────┘          └─────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Tools = Structured Output

Claude's "tool use" feature is how we get structured JSON output:

```python
# We define tools like this:
{
    "name": "identify_risk",
    "description": "Record a risk finding",
    "input_schema": {
        "type": "object",
        "properties": {
            "risk": {"type": "string"},
            "severity": {"enum": ["critical", "high", "medium", "low"]},
            "domain": {"type": "string"},
            ...
        }
    }
}

# Claude calls the tool with structured data:
{
    "type": "tool_use",
    "name": "identify_risk",
    "input": {
        "risk": "30 VMs running EOL Windows Server 2012 R2",
        "severity": "critical",
        "domain": "infrastructure",
        ...
    }
}

# We execute the tool, store the finding, return confirmation
# Claude sees the result and continues analysis
```

**This is not magic. It's just a loop calling an API.**

---

## Agent Orchestration

### Current: Sequential with Parallel Domain Execution

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN.PY ORCHESTRATION                         │
│                                                                  │
│   1. DOCUMENT INGESTION                                         │
│      └── PDF → Text extraction                                  │
│                                                                  │
│   2. PHASE 1: DOMAIN ANALYSIS (Parallel)                        │
│      ┌────────────────────────────────────────────────────┐     │
│      │  ThreadPoolExecutor (batches of 3)                 │     │
│      │                                                    │     │
│      │  Batch 1: Infrastructure, Network, Cybersecurity   │     │
│      │  Batch 2: Applications, Identity, Organization     │     │
│      │                                                    │     │
│      │  Each agent gets:                                  │     │
│      │  • Own AnalysisStore instance                      │     │
│      │  • Full document text                              │     │
│      │  • Domain-specific prompt                          │     │
│      └────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│      ┌────────────────────────────────────────────────────┐     │
│      │  MERGE RESULTS                                     │     │
│      │  master_store.merge_from(agent_store)              │     │
│      └────────────────────────────────────────────────────┘     │
│                                                                  │
│   3. PHASE 2: COORDINATOR SYNTHESIS (Sequential)                │
│      └── Cross-domain dependencies, executive summary           │
│                                                                  │
│   4. PHASE 3: OUTPUT GENERATION                                 │
│      └── JSON files, HTML report, database persistence          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Why Batched Parallel Execution?

- **API Rate Limits**: 450K tokens/minute cap means we can't blast 6 agents simultaneously
- **Batches of 3**: Stays within rate limits while still parallelizing
- **Isolated Stores**: Each agent writes to its own store, then we merge (thread-safe)

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                │
│                                                                  │
│   PDF Documents                                                  │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────┐                                               │
│   │ PDF Parser  │  pymupdf extracts text                        │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────┐                                               │
│   │  Raw Text   │  Combined document text (all pages)           │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ├──────────────────────────────────────┐               │
│          │                                      │               │
│          ▼                                      ▼               │
│   ┌─────────────┐                       ┌─────────────┐         │
│   │   Agent 1   │  ...                  │   Agent N   │         │
│   │             │                       │             │         │
│   │ Prompt +    │                       │ Prompt +    │         │
│   │ Document +  │                       │ Document +  │         │
│   │ Tools       │                       │ Tools       │         │
│   └──────┬──────┘                       └──────┬──────┘         │
│          │                                      │               │
│          ▼                                      ▼               │
│   ┌─────────────┐                       ┌─────────────┐         │
│   │AnalysisStore│                       │AnalysisStore│         │
│   │  (isolated) │                       │  (isolated) │         │
│   └──────┬──────┘                       └──────┬──────┘         │
│          │                                      │               │
│          └──────────────┬───────────────────────┘               │
│                         │                                        │
│                         ▼                                        │
│                  ┌─────────────┐                                │
│                  │   MERGE     │  merge_from() combines stores  │
│                  │             │                                │
│                  │ Master Store│                                │
│                  └──────┬──────┘                                │
│                         │                                        │
│          ┌──────────────┼──────────────┐                        │
│          │              │              │                        │
│          ▼              ▼              ▼                        │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐                  │
│   │   JSON    │  │  SQLite   │  │   HTML    │                  │
│   │   Files   │  │    DB     │  │  Report   │                  │
│   └───────────┘  └───────────┘  └───────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Version Roadmap

### V1: Current State (MVP)

**What's Built:**
- 6 domain agents running in parallel (batched)
- Single-pass analysis (discovery + reasoning combined)
- Coordinator synthesis for cross-domain dependencies
- JSON output + HTML viewer + SQLite persistence
- 35 unit tests passing

**Architecture:**
```
Document → Domain Agents (parallel) → Coordinator → Output
```

**Limitations:**
- Single-pass (no separation of discovery vs. reasoning)
- Cost estimates are "gut feel" from agent, not bottoms-up
- No explicit inventory structure (varies by run)

---

### V2: Target State (Next Phase)

**What's Planned:**
- **Two-phase agents**: Discovery (extract facts) → Reasoning (analyze)
- **Standardized inventory**: Same structure every time
- **Cost refinement pipeline**: Multi-stage estimate validation

**Architecture:**
```
Document → Discovery Agents → Standardized Inventory
                                      │
                                      ▼
                            Reasoning Agents → Risks, Strategic, Work Items
                                      │
                                      ▼
                            Coordinator → Executive Summary
                                      │
                                      ▼
                            Cost Refinement (optional) → Bottoms-Up Estimates
```

**Key Changes:**
1. **Discovery agents** produce structured inventory (Excel-ready)
2. **Reasoning agents** receive inventory as input, produce analysis
3. **Cost agents** (new) validate and refine estimates

---

### V3: Future State (Cost Estimation Module)

**What's Planned:**
- Multi-stage cost estimation pipeline
- Resource rate library (50-75 roles × regions × provider types)
- Bottoms-up work item costing

**Architecture:**
```
Confirmed Work Items
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│                  COST ESTIMATION PIPELINE                      │
│                                                                │
│   Stage 1: High-Level Research                                │
│   └── AI researches typical costs, produces assumptions       │
│                         │                                      │
│                         ▼                                      │
│   Stage 2: Component Breakdown                                │
│   └── Labor vs. software vs. infrastructure allocation        │
│                         │                                      │
│                         ▼                                      │
│   Stage 3: Validation                                         │
│   └── Sanity check against benchmarks                         │
│                         │                                      │
│                         ▼                                      │
│   Stage 4: Bottoms-Up Resource Build                          │
│   └── Milestones → Resource types → Hours → Rate library      │
│                                                                │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
Defensible Cost Estimates with Resource Plans
```

See `docs/COST_ESTIMATION_MODULE.md` for full details.

---

## Key Design Decisions

### 1. Direct API vs. Framework

**Decision:** Direct Anthropic API calls

**Rationale:**
- Full control over prompts and conversation
- No abstraction layers hiding behavior
- Easier debugging and iteration
- Fewer dependencies to manage

### 2. Tools for Structured Output

**Decision:** Use Claude's tool_use feature for all findings

**Rationale:**
- Guaranteed JSON structure
- Type validation built-in
- Natural fit for structured output
- No parsing/extraction needed

### 3. Parallel with Batching

**Decision:** ThreadPoolExecutor with batches of 3

**Rationale:**
- Respect API rate limits (450K tokens/min)
- Still faster than sequential (2x speedup)
- Isolated stores prevent race conditions
- Easy to adjust batch size

### 4. SQLite for Persistence

**Decision:** Local SQLite database

**Rationale:**
- Zero infrastructure required
- Portable (single file)
- SQL queries for analysis
- Good enough for single-user tool

### 5. Prompts as Code

**Decision:** Prompts live in `prompts/*.py` files

**Rationale:**
- Version controlled with code
- Can import shared components
- IDE support for editing
- No external prompt management

---

## File Structure (Annotated)

```
it-diligence-agent/
│
├── main.py                     # Entry point - orchestrates everything
│                               # Handles parallel execution, merging, output
│
├── config.py                   # Configuration (domains, paths, settings)
│
├── agents/
│   ├── base_agent.py           # THE CORE: Agent loop implementation
│   │                           # ~200 lines that do all the work
│   │
│   ├── infrastructure_agent.py # Domain agent (imports base + prompt)
│   ├── network_agent.py        # Domain agent
│   ├── cybersecurity_agent.py  # Domain agent
│   ├── applications_agent.py   # Domain agent
│   ├── identity_access_agent.py# Domain agent
│   ├── organization_agent.py   # Domain agent
│   └── coordinator_agent.py    # Synthesis agent
│
├── prompts/
│   ├── dd_reasoning_framework.py  # Shared four-lens framework
│   ├── infrastructure_prompt.py   # Domain-specific prompt
│   ├── network_prompt.py          # Domain-specific prompt
│   ├── cybersecurity_prompt.py    # Domain-specific prompt
│   ├── applications_prompt.py     # Domain-specific prompt
│   ├── identity_access_prompt.py  # Domain-specific prompt
│   ├── organization_prompt.py     # Domain-specific prompt
│   └── coordinator_prompt.py      # Synthesis prompt
│
├── tools/
│   └── analysis_tools.py       # Tool definitions + AnalysisStore
│                               # All structured output goes through here
│
├── storage/
│   ├── database.py             # SQLite wrapper
│   ├── models.py               # Data models (Risk, Gap, WorkItem, etc.)
│   └── repository.py           # CRUD operations
│
├── ingestion/
│   └── pdf_parser.py           # PDF → text extraction
│
├── tests/
│   ├── test_parallelization.py # 24 tests for parallel execution
│   └── test_run_single_agent.py# 11 tests for agent wrapper
│
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md  # This file
│   └── COST_ESTIMATION_MODULE.md # Future cost estimation design
│
└── data/
    ├── input/                  # Drop documents here
    ├── output/                 # Analysis results
    └── diligence.db            # SQLite database
```

---

## How to Explain This to Someone

### Quick Answer
> "It's a Python application that calls the Claude API directly. Each agent is just a loop: send prompt, get response, execute tools, repeat. No frameworks - just straightforward code."

### Longer Answer
> "We built custom agents that use Claude's tool-use feature for structured output. Each domain specialist agent analyzes the document through its lens, recording findings via tools. The agents run in parallel (batched for rate limits), then a coordinator synthesizes cross-domain insights. It's maybe 500 lines of core code - the rest is prompts and data handling."

### For Technical Folks
> "It's a tool-use agent loop over the Anthropic API. Agents are stateless - they get a prompt, document, and tool definitions, then iterate until complete. We use ThreadPoolExecutor for parallelization with isolated AnalysisStore instances that merge post-execution. Persistence is SQLite. No LangChain, no vector DB, no RAG - the context window is big enough to just send the whole document."

---

## Performance Characteristics

| Metric | Typical Value |
|--------|---------------|
| Document processing | 5-10 seconds |
| Per-agent analysis | 3-5 minutes |
| Total parallel execution (6 agents) | 8-10 minutes |
| Coordinator synthesis | 2-3 minutes |
| **Total end-to-end** | **12-15 minutes** |
| API tokens per run | ~4-5M tokens |
| Output files generated | 12-15 files |

---

## Summary

This is **not a framework-based system**. It's a custom Python application with:

1. **Direct API calls** to Claude (anthropic SDK)
2. **Simple agent loop** (~200 lines of core code)
3. **Tool-use for structured output** (guaranteed JSON)
4. **Parallel execution** with batching (respects rate limits)
5. **SQLite persistence** (zero infrastructure)
6. **Prompts as code** (version controlled)

The magic is in the **prompts**, not the code. The code is intentionally simple so we can focus on what matters: the analysis logic in the prompts and the structured output from the tools.

---

*Document Version: 1.0*
*Last Updated: January 2026*
