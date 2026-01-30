# IT Due Diligence Analysis Agent

AI-powered IT due diligence analysis for M&A transactions. Uses Claude to analyze IT infrastructure documents and generate structured assessments with cost estimates and VDR request packs.

> **This agent delivers IT Due Diligence insights, not financial valuation.**

---

> ⚠️ **Active Development: Inventory System Upgrade**
>
> We are transitioning from 100% LLM-based extraction to a hybrid architecture:
> - **Structured inputs** (ToltIQ tables, Excel) → Deterministic parsing → **InventoryStore**
> - **Unstructured inputs** (prose, meeting notes) → LLM discovery → **FactStore**
>
> Key changes: InventoryStore + FactStore separation, content-based IDs, Application Intelligence layer.
>
> See **[Inventory System Upgrade Plan](docs/INVENTORY_SYSTEM_UPGRADE_PLAN.md)** for full details.

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and setup
git clone https://github.com/bjuice1/it-diligence-agent.git
cd it-diligence-agent

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Start with Docker
cd docker
docker compose up -d

# Access at http://localhost:5001
```

### Option 2: Local Python

```bash
pip install -r requirements.txt

# Run web interface
python -m web.app
# Access at http://localhost:5001

# Or use CLI
python main_v2.py --docs data/input --target-name "Acme Corp"
```

See [Deployment Guide](docs/deployment.md) for production setup.
See [Session Pickup Guide](docs/SESSION_PICKUP.md) for current development status.

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [Session Pickup](docs/SESSION_PICKUP.md) | **Current dev status & resume guide** |
| [Architecture](docs/architecture.md) | System architecture overview |
| [Data Flow](docs/data-flow.md) | How data moves through the system |
| [Storage](docs/storage.md) | Storage architecture and stores |
| [API Reference](docs/api.md) | REST API documentation |
| [Deployment](docs/deployment.md) | Deployment and configuration guide |
| [Output Guide](docs/OUTPUT_GUIDE.md) | All outputs explained (JSON, HTML, Excel, etc.) |
| [V2 System Architecture](docs/V2_SYSTEM_ARCHITECTURE_AND_OPTIMIZATIONS.md) | Technical deep-dive on V2 |
| [Deal Lens Architecture](docs/DEAL_LENS_ARCHITECTURE.md) | Deal types & industry considerations |

---

## What This Is

A **custom Python application** that calls the Claude API directly to perform IT due diligence analysis.

**Not LangChain. Not LangGraph. Not LangFlow.** Just straightforward Python code with a simple agent loop.

### Tech Stack
```
anthropic       # Direct Claude API (model tiering: Haiku + Sonnet)
pymupdf         # PDF extraction
sqlite3         # Persistence
python-dotenv   # Config

That's it. No frameworks. No vector databases. No RAG pipelines.
```

---

## Current State (V2)

### What's Working

- **Discovery → Reasoning split** for better quality and cost efficiency
- **Model tiering**: Haiku for extraction (~70% cheaper), Sonnet for analysis
- **6 domain agents** with parallel execution
- **Coverage analysis** with letter grades (A-F)
- **Cross-domain synthesis** for consistency checking
- **Cost aggregation** by phase, domain, and owner
- **VDR request generation** from gaps and coverage
- **Evidence chains**: Every finding cites specific fact IDs
- **Interactive CLI** for reviewing and adjusting analysis results
- **HTML Reports** with filtering by domain, severity, category, phase
- **Investment Thesis Presentation** - slide-deck style HTML for PE buyers
- **196 unit tests** passing

### V2 Architecture

```
PDF Documents
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│           PHASE 1: DISCOVERY (Haiku - Fast & Cheap)             │
│                                                                 │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│   │Infrastructure│ │   Network    │ │Cybersecurity │  Parallel │
│   │  Discovery   │ │  Discovery   │ │  Discovery   │           │
│   └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│   │ Applications │ │Identity/Access│ │ Organization │  Parallel │
│   │  Discovery   │ │  Discovery   │ │  Discovery   │           │
│   └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
│   Output: FactStore with F-XXX-001 IDs + Gaps (G-XXX-001)       │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│           PHASE 2: REASONING (Sonnet - Capable)                 │
│                                                                 │
│   Each domain reasoning agent receives facts and produces:      │
│   • Risks (with severity, mitigation, fact citations)           │
│   • Strategic Considerations (buyer alignment lens)             │
│   • Work Items (with cost estimates, phase, owner)              │
│   • Recommendations                                             │
│                                                                 │
│   Output: ReasoningStore with evidence chains                   │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│           PHASE 3: COVERAGE ANALYSIS                            │
│                                                                 │
│   • Scores documentation completeness per domain                │
│   • Identifies missing critical items                           │
│   • Assigns letter grade (A-F)                                  │
│                                                                 │
│   Output: coverage_{timestamp}.json                             │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│           PHASE 4: SYNTHESIS                                    │
│                                                                 │
│   • Cross-domain consistency checks                             │
│   • Related finding grouping by theme                           │
│   • Cost aggregation (by phase, domain, owner)                  │
│   • Risk aggregation                                            │
│                                                                 │
│   Output: synthesis_{timestamp}.json                            │
│           executive_summary_{timestamp}.md                      │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│           PHASE 5: VDR GENERATION                               │
│                                                                 │
│   • Generates follow-up data requests from:                     │
│     - Identified gaps                                           │
│     - Missing coverage items                                    │
│     - Low-confidence risks                                      │
│   • Prioritized by criticality                                  │
│   • Includes suggested documents per category                   │
│                                                                 │
│   Output: vdr_requests_{timestamp}.json                         │
│           vdr_requests_{timestamp}.md                           │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│           PHASE 6: NARRATIVE GENERATION (Optional)              │
│                          --narrative flag                        │
│                                                                 │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│   │Infrastructure│ │   Network    │ │Cybersecurity │  Parallel │
│   │  Narrative   │ │  Narrative   │ │  Narrative   │  (Sonnet) │
│   └──────────────┘ └──────────────┘ └──────────────┘           │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│   │ Applications │ │Identity/Access│ │ Organization │  Parallel │
│   │  Narrative   │ │  Narrative   │ │  Narrative   │           │
│   └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
│   ┌──────────────────────────────────────────────────────┐     │
│   │              Cost Synthesis Agent                     │     │
│   │  Aggregates costs, generates executive cost narrative │     │
│   └──────────────────────────────────────────────────────┘     │
│                                                                 │
│   Output: narratives_{timestamp}.json                           │
│           investment_thesis_{timestamp}.html (LLM-generated)    │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
   OUTPUTS
   ├── facts_{timestamp}.json           # Extracted inventory
   ├── findings_{timestamp}.json        # Risks, work items, etc.
   ├── coverage_{timestamp}.json        # Coverage scores
   ├── synthesis_{timestamp}.json       # Cross-domain analysis
   ├── executive_summary_{timestamp}.md # IC-ready summary
   ├── vdr_requests_{timestamp}.json    # Follow-up requests
   ├── vdr_requests_{timestamp}.md      # Markdown VDR list
   ├── narratives_{timestamp}.json      # LLM-generated narratives (with --narrative)
   ├── it_dd_report_{timestamp}.html    # Interactive HTML report
   └── investment_thesis_{timestamp}.html # PE buyer presentation
```

---

## Key V2 Features

### 1. Model Tiering (Cost Optimization)
| Phase | Model | Purpose | Cost |
|-------|-------|---------|------|
| Discovery | Haiku | Fact extraction | ~$0.25/1M tokens |
| Reasoning | Sonnet | Analysis & judgment | ~$3/1M tokens |

**Result**: ~70% cost reduction vs. using Sonnet for everything.

### 2. Evidence Chains
Every finding cites specific facts:
```json
{
  "risk_id": "R-001",
  "title": "EOL VMware Version",
  "based_on_facts": ["F-INFRA-003", "F-INFRA-007"],
  "reasoning": "Fact F-INFRA-003 shows VMware 6.7, which reached EOL Oct 2022..."
}
```

### 3. Cost Estimates on Work Items
```json
{
  "work_item_id": "WI-001",
  "title": "Upgrade VMware to 8.0",
  "phase": "Day_100",
  "cost_estimate": "100k_to_500k",
  "owner_type": "target",
  "triggered_by_risks": ["R-001"]
}
```

Cost ranges: `under_25k`, `25k_to_100k`, `100k_to_500k`, `500k_to_1m`, `over_1m`

### 4. Coverage Scoring
```
Coverage Grade: B
Overall Coverage: 78.5%
Critical Coverage: 92.0%
Missing Critical Items: 3

Domain Breakdown:
  infrastructure: 85.0% (critical: 100.0%)
  cybersecurity: 72.0% (critical: 87.5%)
  applications: 68.0% (critical: 80.0%)
```

### 5. VDR Request Generation
Automatically generates prioritized follow-up requests:
```markdown
## CRITICAL Priority (12)

### VDR-001: Documentation needed: RTO/RPO values not documented
**Domain:** infrastructure | **Category:** backup_dr
**Suggested Documents:**
- DR plan
- Backup policies
- DR test results
```

### 6. Investment Thesis Presentation
Generates a slide-deck style HTML presentation for PE buyers:
- **Executive Summary** with key metrics, top risks, cost breakdown
- **Domain Slides** (one per agent) with "So What" highlights
- **Work Plan** by phase with cost estimates
- **Open Questions** for VDR follow-up

Each slide follows a candid, partner-level tone:
```
┌─────────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE                                                   │
│                                                                  │
│ SO WHAT:                                                         │
│ "Hybrid cloud footprint with aging on-prem. Expect              │
│  modernization costs within 18 months."                         │
│                                                                  │
│ KEY CONSIDERATIONS:                                              │
│ • Two colo facilities (Atlanta primary, NYC secondary)          │
│ • 47 AWS accounts, $6.7M annual spend                           │
│ • No documented DR/BCP testing                                   │
│                                                                  │
│ COST IMPACT: $1.2M - $3.5M                                       │
└─────────────────────────────────────────────────────────────────┘
```

Run with custom target name:
```bash
python main_v2.py data/input/ --target-name "ACME Corp"
```

### 7. Narrative Generation (LLM-Generated Storytelling)
Use `--narrative` flag to enable LLM-generated narratives for the investment thesis:
```bash
python main_v2.py data/input/ --all --narrative
```

This runs:
- **6 Domain Narrative Agents** (parallel, Sonnet) - Generate partner-level storytelling for each domain
- **1 Cost Synthesis Agent** (sequential) - Aggregates costs into coherent executive narrative

**Output**: `narratives_{timestamp}.json` + enhanced `investment_thesis_{timestamp}.html`

The narrative agents produce:
- "So What" headlines that capture key implications
- 2-3 paragraph candid narratives (not salesy, practical)
- Cost impact summaries per domain
- Source citations and confidence levels

See [Output Guide](docs/OUTPUT_GUIDE.md) for complete output documentation.

---

## Quick Start

### V2 Pipeline (Recommended)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and add your Anthropic API key

# 3. Run V2 analysis (single domain)
python main_v2.py data/input/document.pdf --domain infrastructure

# 4. Run V2 analysis (all 6 domains, parallel)
python main_v2.py data/input/ --all

# 5. Run with options
python main_v2.py data/input/ --all --no-vdr          # Skip VDR generation
python main_v2.py data/input/ --all --no-synthesis    # Skip synthesis
python main_v2.py data/input/ --all --sequential      # No parallelization

# 6. Resume from existing facts (skip discovery)
python main_v2.py --from-facts output/facts_20260115.json

# 7. Interactive mode - review and adjust results
python main_v2.py data/input/ --all --interactive     # Run analysis then enter interactive
python main_v2.py --interactive-only                   # Load existing results into interactive mode
```

### V1 Pipeline (Legacy)

```bash
python main.py data/input/document.pdf
```

### Output Location
```
output/
├── facts/
│   └── facts_20260115_120000.json          # Extracted facts
├── findings/
│   └── findings_20260115_120000.json       # Reasoning results
├── coverage_20260115_120000.json           # Coverage scores
├── synthesis_20260115_120000.json          # Cross-domain analysis
├── executive_summary_20260115_120000.md    # Human-readable summary
├── vdr_requests_20260115_120000.json       # VDR pack (JSON)
├── vdr_requests_20260115_120000.md         # VDR pack (Markdown)
└── it_dd_report_20260115_120000.html       # Interactive HTML report (filterable)
```

---

## Project Structure

```
it-diligence-agent/
├── main_v2.py              # V2 entry point (6-phase pipeline)
├── main.py                 # V1 entry point (legacy)
├── config_v2.py            # V2 configuration (model tiering)
├── config.py               # V1 configuration
│
├── agents_v2/              # V2 Agents
│   ├── base_discovery_agent.py    # Discovery base (Haiku)
│   ├── base_reasoning_agent.py    # Reasoning base (Sonnet)
│   ├── discovery/
│   │   ├── infrastructure_discovery.py
│   │   ├── network_discovery.py
│   │   ├── cybersecurity_discovery.py
│   │   ├── applications_discovery.py
│   │   ├── identity_access_discovery.py
│   │   └── organization_discovery.py
│   ├── reasoning/
│   │   ├── infrastructure_reasoning.py
│   │   ├── network_reasoning.py
│   │   ├── cybersecurity_reasoning.py
│   │   ├── applications_reasoning.py
│   │   ├── identity_access_reasoning.py
│   │   └── organization_reasoning.py
│   └── narrative/          # NEW: Narrative agents for investment thesis
│       ├── base_narrative_agent.py  # Base class for narrative agents
│       ├── infrastructure_narrative.py
│       ├── network_narrative.py
│       ├── cybersecurity_narrative.py
│       ├── applications_narrative.py
│       ├── identity_narrative.py
│       ├── organization_narrative.py
│       └── cost_synthesis_agent.py  # Aggregates costs across domains
│
├── tools_v2/               # V2 Tools
│   ├── fact_store.py       # FactStore (facts + gaps)
│   ├── discovery_tools.py  # create_inventory_entry, flag_gap
│   ├── reasoning_tools.py  # identify_risk, create_work_item (with costs)
│   ├── narrative_tools.py  # NarrativeStore, domain narrative tools
│   ├── coverage.py         # Coverage checklists & scoring
│   ├── vdr_generator.py    # VDR request generation
│   ├── synthesis.py        # Cross-domain consistency
│   ├── html_report.py      # HTML report generator with filtering
│   └── presentation.py     # Investment thesis presentation generator
│
├── interactive/            # Interactive Review Mode
│   ├── session.py          # Session management, undo, modifications
│   ├── cli.py              # REPL interface
│   └── commands.py         # 16 commands (list, adjust, explain, etc.)
│
├── web/                    # Web Interface (Flask)
│   ├── app.py              # Flask routes
│   └── templates/          # HTML templates
│
├── agents/                 # V1 Agents (legacy)
│   ├── base_agent.py
│   └── [domain]_agent.py
│
├── prompts/                # System prompts
│   ├── v2_*_discovery_prompt.py   # V2 discovery prompts
│   ├── v2_*_reasoning_prompt.py   # V2 reasoning prompts
│   └── *_prompt.py                # V1 prompts
│
├── tests/
│   ├── test_v2_tools.py    # V2 core tests
│   └── test_interactive.py # Interactive mode tests (196 total)
│
├── docs/
│   ├── V2_SYSTEM_ARCHITECTURE_AND_OPTIMIZATIONS.md
│   ├── SYSTEM_ARCHITECTURE.md
│   └── COST_ESTIMATION_MODULE.md
│
└── data/
    ├── input/              # Drop documents here
    └── output/             # Analysis results
```

---

## The Six Domains

| Domain | Discovery Categories | Key Items |
|--------|---------------------|-----------|
| **Infrastructure** | hosting, compute, storage, backup_dr, cloud, legacy, tooling | Data centers, VMs, SAN, DR |
| **Network** | wan, lan, remote_access, dns_dhcp, load_balancing, network_security | Firewalls, VPN, ISP |
| **Cybersecurity** | endpoint, perimeter, detection, vulnerability, compliance, incident_response | EDR, SIEM, SOC2 |
| **Applications** | erp, crm, custom, saas, integration, development, database | SAP, Salesforce, custom apps |
| **Identity & Access** | directory, authentication, privileged_access, provisioning, sso, mfa | AD, Okta, PAM |
| **Organization** | structure, staffing, vendors, skills, processes, budget, roadmap | Headcount, contracts |

---

## Example Outputs

### Executive Summary
```markdown
# Executive Summary

## Overview
- Total Facts Discovered: 47
- Information Gaps: 8
- Risks Identified: 12
- Work Items: 23

## Coverage Quality
- Overall Coverage: 72.3%
- Critical Item Coverage: 85.0%
- Missing Critical Items: 5

## Cost Estimates
- Total Range: $1,250,000 - $3,500,000

### By Phase:
  - Day_1: $125,000 - $350,000 (5 items)
  - Day_100: $875,000 - $2,150,000 (12 items)
  - Post_100: $250,000 - $1,000,000 (6 items)

### By Owner:
  - buyer: $200,000 - $500,000 (4 items)
  - target: $750,000 - $2,000,000 (15 items)
  - shared: $300,000 - $1,000,000 (4 items)
```

### Risk with Evidence Chain
```json
{
  "finding_id": "R-001",
  "domain": "infrastructure",
  "title": "EOL VMware Version",
  "description": "VMware 6.7 reached end of life October 2022",
  "category": "technical_debt",
  "severity": "high",
  "integration_dependent": false,
  "mitigation": "Upgrade to VMware 8.0 before integration",
  "based_on_facts": ["F-INFRA-003"],
  "confidence": "high",
  "reasoning": "Fact F-INFRA-003 documents VMware vSphere 6.7 which reached general support EOL in October 2022"
}
```

### Work Item with Cost
```json
{
  "finding_id": "WI-001",
  "domain": "infrastructure",
  "title": "VMware Upgrade Project",
  "description": "Upgrade VMware infrastructure from 6.7 to 8.0",
  "phase": "Day_100",
  "priority": "high",
  "owner_type": "target",
  "cost_estimate": "100k_to_500k",
  "triggered_by": ["F-INFRA-003"],
  "triggered_by_risks": ["R-001"]
}
```

### VDR Request
```json
{
  "request_id": "VDR-001",
  "domain": "infrastructure",
  "category": "backup_dr",
  "title": "Documentation needed: RTO/RPO values not documented",
  "priority": "critical",
  "source": "gap",
  "source_id": "G-INFRA-001",
  "suggested_documents": [
    "DR plan",
    "Backup policies",
    "DR test results",
    "RTO/RPO documentation"
  ]
}
```

---

## Performance

| Metric | V1 | V2 |
|--------|----|----|
| Per-agent analysis | 3-5 min | 2-3 min (discovery) + 3-4 min (reasoning) |
| Total (6 domains parallel) | 8-10 min | 10-12 min |
| Coverage + Synthesis + VDR | N/A | <1 min |
| **End-to-end** | **12-15 min** | **12-15 min** |
| API cost per run | ~$15-20 | ~$8-12 (model tiering) |

---

## CLI Reference

```
usage: main_v2.py [-h] [--from-facts FROM_FACTS] [--discovery-only]
                  [--domain {infrastructure,network,cybersecurity,applications,identity_access,organization}]
                  [--all] [--sequential] [--no-vdr] [--no-synthesis]
                  [--narrative] [--target-name TARGET_NAME]
                  [--deal-context DEAL_CONTEXT] [--output-dir OUTPUT_DIR] [-v]
                  [input_path]

Options:
  input_path              Path to input documents (file or directory)
  --from-facts FILE       Load facts from existing JSON (skip discovery)
  --discovery-only        Run discovery only (no reasoning/synthesis)
  --domain DOMAIN         Single domain to analyze (default: infrastructure)
  --all                   Analyze all 6 domains (parallel by default)
  --sequential            Disable parallelization
  --no-vdr                Skip VDR request generation
  --no-synthesis          Skip cross-domain synthesis
  --narrative             Enable LLM-generated narratives for investment thesis
  --target-name NAME      Target company name for presentation
  --deal-context FILE     Path to deal context JSON
  -v, --verbose           Enable verbose logging
```

### Common Workflows

```bash
# Full analysis with all outputs
python main_v2.py data/input/ --all

# Full analysis with LLM-generated narratives (best quality)
python main_v2.py data/input/ --all --narrative --target-name "ACME Corp"

# Quick single-domain analysis
python main_v2.py data/input/ --domain infrastructure

# Re-run reasoning on existing facts
python main_v2.py --from-facts output/facts_20260115.json --all

# Interactive mode for review/adjustment
python main_v2.py data/input/ --all --interactive
```

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Current status: 196 passed
```

---

## Roadmap

### V2: Discovery/Reasoning Split ✅ (Complete)
- [x] Separate fact extraction from analysis
- [x] Model tiering (Haiku for discovery, Sonnet for reasoning)
- [x] Evidence chains with fact citations
- [x] Cost estimates on work items
- [x] Coverage checklists and scoring
- [x] Cross-domain synthesis
- [x] VDR request generation
- [x] Interactive CLI for review/adjustment
- [x] HTML reports with filtering

### V3: Investment Thesis & Integration View (In Progress)
- [x] Fact synthesis to readable statements (Jan 15, 2026)
- [x] **Investment Thesis Presentation Mode** - Slide-deck HTML for PE buyers
- [x] **Narrative Generation** - 6 domain agents + cost synthesis agent (Jan 15, 2026)
- [ ] **Integration Scenario Modeling** - How target fits with buyer's environment
- [ ] **Value Creation Analysis** - Synergies, cost reduction opportunities
- [ ] **Sell-Side Narrative** - Story-telling view of IT capabilities
- [ ] Flask web UI for browser-based interaction

### V4: Enhanced Analysis (Future)
- [ ] Prompt caching for repeated documents
- [ ] Streaming responses for progress visibility
- [ ] Coordinator agent for cross-domain dependencies
- [ ] Integration with deal context (buyer profile)
- [ ] Multi-language document support

### V5: Cost Estimation Module (Future)
- [ ] Multi-stage cost refinement pipeline
- [ ] Bottoms-up resource planning
- [ ] Rate library (roles × regions × provider types)

See [Cost Estimation Module](docs/COST_ESTIMATION_MODULE.md) for detailed design.

---

## FAQ

### Is this LangChain/LangGraph?
No. Direct Anthropic API calls. No frameworks.

### Why two models (Haiku + Sonnet)?
Haiku is 10x cheaper and fast enough for fact extraction. Sonnet's reasoning capability is needed for analysis and judgment calls.

### How do I customize the analysis?
Edit prompts in `prompts/v2_*_prompt.py`. The coverage checklists are in `tools_v2/coverage.py`.

### Can it handle multiple documents?
Yes. Point it at a folder and it processes all PDFs.

### What's a "fact" vs a "finding"?
- **Fact**: Extracted information with evidence (e.g., "VMware 6.7, 340 VMs")
- **Finding**: Analysis result citing facts (e.g., "Risk: EOL VMware needs upgrade")

### How are costs calculated?
Work items include a `cost_estimate` range. Synthesis aggregates these by phase, domain, and owner type.

---

## License

Internal use only.

---

*Last Updated: January 15, 2026 (V2.3 - Narrative Generation & Output Guide)*
