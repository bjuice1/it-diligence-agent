# IT Due Diligence Agent - Team Guide

*How the system works, what it covers, and how we make it better together*

---

## What This Tool Does

The IT Due Diligence Agent analyzes IT infrastructure documents and produces structured findings for M&A due diligence. It reads PDF or markdown documents describing a target company's IT environment and outputs:

- **Current State Assessment** - What exists today
- **Risk Register** - What could go wrong (standalone and integration-specific)
- **Knowledge Gaps** - What information is missing
- **Strategic Considerations** - What this means for the deal
- **Integration Work Items** - What needs to be done post-close
- **Recommendations** - Strategic guidance for the deal team

The output is designed to be **Investment Committee ready** - defensible, evidence-based, and actionable.

---

## Domain Coverage (MVP Scope)

The tool analyzes IT through **six specialized domains**:

| Domain | Agent | What It Analyzes |
|--------|-------|------------------|
| **Infrastructure** | `InfrastructureAgent` | Data centers, servers, storage, cloud platforms, hosting models |
| **Network** | `NetworkAgent` | WAN, LAN, connectivity, firewalls, DNS, IP addressing |
| **Cybersecurity** | `CybersecurityAgent` | Security tools, compliance, vulnerability management, incident response |
| **Applications** | `ApplicationsAgent` | ERP, CRM, HCM, custom apps, technical debt, licensing, overlap analysis |
| **Identity & Access** | `IdentityAccessAgent` | IAM, SSO, MFA, PAM, JML processes, access governance, directories |
| **Organization** | `OrganizationAgent` | IT org structure, key person risk, outsourcing, skill gaps *(coming soon)* |

Each domain agent is a specialist that applies the same **Four-Lens Framework**:
1. **Lens 1:** Current State - "What exists today?"
2. **Lens 2:** Risks - "What could go wrong?"
3. **Lens 3:** Strategic Implications - "What does this mean for the deal?"
4. **Lens 4:** Integration Actions - "What needs to be done?"

After all domain agents run, a **Coordinator Agent** synthesizes findings across domains and produces an executive summary.

---

## Architectural Vision: Two-Phase Agent Model

**Key Insight:** Agents should reason, not just follow checklists.

The system is evolving from a single-pass model (one agent with a massive prompt grinding through static questions) to a **two-phase model** where agents discover first, then reason about what they found.

### Why Two Phases?

| Single-Pass (Legacy) | Two-Phase (Target) |
|---------------------|-------------------|
| 300+ line prompts with all questions upfront | Lighter, focused prompts per phase |
| Static checklist regardless of environment | Adaptive analysis based on discoveries |
| Same 30 questions whether relevant or not | Emergent considerations from reasoning |
| Agent validates itself | Separation of discovery and analysis |

### The Two-Phase Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 1: DISCOVERY AGENT                    │
│                                                                 │
│  Mission: "What exists? What's documented? What's missing?"     │
│                                                                 │
│  Superpower: STANDARDIZED INVENTORY OUTPUT                      │
│  • Same structure every time                                    │
│  • Maps directly to Excel template team expects                 │
│  • Consistent categories, fields, coverage metrics              │
│                                                                 │
│  Prompt style: "Extract and categorize" (structured, rigid)     │
│  Output: Inventory tables + gap flags                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 2: REASONING AGENT                    │
│                                                                 │
│  Mission: "Given what we learned, what does it mean?"           │
│                                                                 │
│  Has: CONSIDERATION LIBRARY (reference, NOT checklist)          │
│  • Things a specialist would think about                        │
│  • NOT tethered to it - just available for reference            │
│  • Agent reasons through what's RELEVANT to THIS situation      │
│                                                                 │
│  Prompt style: "Think like a specialist" (emergent, adaptive)   │
│  Output: Risks, strategic considerations, work items            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COORDINATOR AGENT                            │
│                                                                 │
│  • Synthesizes cross-domain findings                            │
│  • Identifies dependencies between domains                      │
│  • Produces executive summary                                   │
│  • Validates completeness                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1: Discovery Agent - Standardized Inventory

The Discovery Agent's superpower is **consistency**. Every analysis produces the same inventory structure, regardless of what's in the documents.

**Example Infrastructure Inventory Output:**

| Domain | Category | Item | Vendor | Version | Count/Capacity | Status | Evidence |
|--------|----------|------|--------|---------|----------------|--------|----------|
| infrastructure | compute | Physical Servers | Dell | R740 | 47 units | Documented | "47 Dell PowerEdge R740 servers in Chicago DC" |
| infrastructure | compute | Virtual Machines | VMware | 7.0 | 200+ VMs | Documented | "Over 200 VMs on vSphere 7.0 cluster" |
| infrastructure | cloud | IaaS | AWS | - | 3 accounts | Documented | "AWS deployment across Prod, Dev, Sandbox accounts" |
| infrastructure | storage | Primary SAN | NetApp | ONTAP 9 | 500TB | Documented | "NetApp ONTAP 9 SAN with 500TB raw capacity" |
| infrastructure | backup_dr | Backup Solution | Veeam | v12 | All VMs | Partial | "Veeam v12 deployed" (cloud tiering not documented) |
| infrastructure | backup_dr | DR Strategy | - | - | - | GAP | DR capability not documented |

**Key schema rules:**
- Every entry has `domain` field for filtering
- `status` is always: "documented", "partial", or "gap"
- `evidence` contains exact quote from source document
- Gaps are explicitly recorded (not just omitted)

This structure:
- Maps directly to Excel exports the team expects
- Makes cross-deal comparison possible
- Creates clear "GAP" flags for missing information
- Is the same every time, regardless of document quality
- Enables filtering by domain across all inventory types

### Phase 2: Reasoning Agent - Emergent Analysis

The Reasoning Agent receives the Phase 1 inventory and **thinks like a specialist** about what it means.

**Key principle:** The agent has access to a consideration library, but is NOT required to work through it as a checklist. It's reference material, not a script.

**Example Consideration Library (Reference):**
```
When reasoning about infrastructure findings, a specialist might consider:
- End-of-life / end-of-support implications
- Capacity constraints vs. stated growth plans
- Single points of failure in critical systems
- Cloud vs. on-prem alignment with buyer's strategy
- Technical debt indicators and remediation complexity
- Vendor lock-in and licensing transfer implications
- Geographic/regulatory constraints on data location
- Disaster recovery gaps and business continuity exposure
- Skill dependencies on specific technologies

These are lenses for thinking, not questions to answer sequentially.
```

**How the Reasoning Agent works:**

Instead of: "Answer these 30 questions about the infrastructure"

The agent is prompted: "Given this inventory, reason through what it means for the deal. What risks emerge from this specific combination of technologies, gaps, and maturity levels? What would a specialist flag as important given THIS environment?"

The output is **emergent** - driven by what's actually relevant, not by a static checklist.

### Why This Matters

| Aspect | Phase 1 (Discovery) | Phase 2 (Reasoning) |
|--------|---------------------|---------------------|
| **Goal** | Inventory what exists | Analyze what it means |
| **Output** | Structured, consistent | Emergent, situation-specific |
| **Prompt weight** | Heavy on schema/format | Light on format, heavy on thinking |
| **Rigidity** | HIGH - same fields every time | LOW - follows the evidence |
| **Library use** | Inventory schema (strict) | Consideration library (reference) |

### Data Flow Between Phases

```
PHASE 1 OUTPUT                          PHASE 2 INPUT
─────────────────                       ─────────────────
inventory.json ─────────────────────────► Reasoning Agent receives
  │                                        full inventory as context
  ├── infrastructure items
  ├── network items                     Deal Context also injected:
  ├── applications items                  ├── buyer_environment
  ├── identity items                      ├── transaction_type
  ├── cybersecurity items                 └── integration_strategy
  └── organization items
                                        PHASE 2 OUTPUT
gaps.json ──────────────────────────────► ─────────────────
  │                                       risks.json
  └── Gaps inform uncertainty             strategic_considerations.json
      in reasoning                        work_items.json
                                          recommendations.json
```

**Key handoff principle:** The Reasoning Agent must ground ALL findings in the inventory. If it can't point to a specific inventory item (or gap), it shouldn't make the finding.

### New Tool Required: `create_inventory_entry`

The two-phase model requires a new tool for Phase 1:

```python
{
    "name": "create_inventory_entry",
    "description": "Record a standardized inventory item discovered in the documentation",
    "parameters": {
        "domain": "Domain this item belongs to (infrastructure, network, etc.)",
        "category": "Category within domain (compute, storage, cloud, etc.)",
        "item": "What this inventory item is",
        "status": "documented | partial | gap",
        "evidence": "Exact quote from document (required for documented/partial)",
        # ... additional optional fields per domain schema
    }
}
```

This tool enforces the standardized structure and ensures all inventory items include required fields.

---

## How the Agents Think (Current Implementation)

> **Note:** The current implementation uses a single-pass model. The two-phase model above is the target architecture.

### Current Analysis Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT: IT Documents                         │
│              (PDFs, markdown, text files)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN AGENTS (Parallel)                     │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │Infrastructure│ │   Network    │ │Cybersecurity │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Applications │ │Identity/Access│ │ Organization │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                 │
│  Each agent applies the Four-Lens Framework to its domain      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COORDINATOR AGENT                            │
│                                                                 │
│  • Synthesizes cross-domain findings                           │
│  • Identifies dependencies between domains                      │
│  • Produces executive summary                                   │
│  • Calculates overall complexity and cost                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         OUTPUTS                                 │
│                                                                 │
│  • risks.json              - Risk register with evidence        │
│  • gaps.json               - Knowledge gaps to fill             │
│  • work_items.json         - Phased integration tasks           │
│  • current_state.json      - Environment inventory              │
│  • strategic_considerations.json - Deal implications            │
│  • ANALYSIS_SUMMARY.md     - Human-readable summary             │
│  • analysis_report.html    - Interactive viewer                 │
└─────────────────────────────────────────────────────────────────┘
```

### What Guides Each Agent

Each agent is driven by a **system prompt** - a comprehensive playbook that tells it:

1. **Who it is** - "You are an expert [domain] analyst with 20+ years of experience..."
2. **What to analyze** - Specific areas within the domain (e.g., for Identity: directories, SSO, MFA, PAM, JML, access governance)
3. **What risks to look for** - Common patterns and red flags
4. **How to assess maturity** - Frameworks for evaluating capability levels
5. **How to estimate costs** - Standard work packages and labor rates
6. **Anti-hallucination rules** - Requirements for evidence and when to flag gaps

### The Anti-Hallucination System

A critical feature of the tool is preventing fabricated findings. Every significant finding requires:

| Requirement | Description |
|-------------|-------------|
| **exact_quote** | Verbatim text from the document supporting the finding |
| **evidence_type** | `direct_statement`, `logical_inference`, or `pattern_based` |
| **confidence_level** | `high`, `medium`, or `low` |

**Core principle:** If the agent can't cite evidence, it should flag a gap instead of making up a finding.

---

## How the System Improves

There are **three main pathways** for improving the agents:

### Pathway 1: Prompt Refinement

**What it is:** Editing the agent's system prompt to add new considerations, fix blind spots, or improve reasoning.

**Who can do it:** Anyone who understands the domain

**Where to edit:**
```
prompts/
├── infrastructure_prompt.py    # Infrastructure domain
├── network_prompt.py           # Network domain
├── cybersecurity_prompt.py     # Cybersecurity domain
├── applications_prompt.py      # Applications domain
├── identity_access_prompt.py   # Identity & Access domain
└── organization_prompt.py      # Organization domain (coming soon)
```

**What to add or improve:**
- New risks the agent should check for
- Better maturity assessment frameworks
- Industry-specific patterns (insurance, telecom, manufacturing, etc.)
- New analysis areas within the domain
- Improved cost estimation benchmarks
- Clearer guidance on when to flag gaps vs. make findings

**Example improvement:**
```python
# Before (in identity_access_prompt.py):
**Standalone risks to consider:**
- Low MFA coverage (<80% is concerning)
- No MFA on privileged accounts

# After (adding a missed pattern):
**Standalone risks to consider:**
- Low MFA coverage (<80% is concerning)
- No MFA on privileged accounts
- Service account sprawl (accounts that never rotate passwords)
- Orphan accounts from previous M&A not cleaned up
```

### Pathway 2: Expanding the Consideration Library

**What it is:** Building structured reference data that agents can draw from, separate from the prompts.

**Why it matters:** As we learn more patterns, we don't want prompts to grow infinitely. Instead, we extract reference data into catalogs.

**Future structure:**
```
data/catalogs/
├── eol_database.yaml           # End-of-life dates for technologies
├── compliance_frameworks.yaml  # SOX, PCI, HIPAA requirements
├── cost_benchmarks.yaml        # Standard cost ranges by work type
├── identity_risks.yaml         # Common identity risks catalog
├── infrastructure_risks.yaml   # Common infrastructure risks
└── industry_patterns.yaml      # Industry-specific considerations
```

**Example catalog entry:**
```yaml
# eol_database.yaml
windows_server:
  - version: "2012 R2"
    end_of_support: "2023-10-10"
    risk_level: "critical"
  - version: "2016"
    end_of_support: "2027-01-12"
    risk_level: "medium"
  - version: "2019"
    end_of_support: "2029-01-09"
    risk_level: "low"
```

### Pathway 3: Agent Subdivision

**What it is:** Splitting a broad agent into multiple focused agents for deeper analysis.

**When to consider:**
- A domain is too broad for one agent to cover deeply
- Different expertise needed for sub-areas
- Want parallel execution for speed
- Team wants clear ownership of sub-domains

**Example subdivision:**

| Original | Subdivided Into |
|----------|-----------------|
| Identity & Access Agent | **Identity Provider Agent** (directories, federation) |
| | **Authentication Agent** (SSO, MFA, passwordless) |
| | **Privileged Access Agent** (PAM, service accounts) |
| | **Access Governance Agent** (JML, certifications, RBAC) |

**Trade-offs:**

| Approach | Pros | Cons |
|----------|------|------|
| Single broad agent | Simpler, cross-area context | Less depth |
| Multiple focused agents | Deeper analysis, parallelization | More complexity, possible duplicates |

---

## How to Contribute: Practical Steps

### Step 1: Run and Review

1. Run the tool against a scenario (generated or real)
2. Open the output files (`risks.json`, `gaps.json`, etc.)
3. Ask yourself:
   - What did it catch correctly?
   - What did it miss that an expert would catch?
   - What did it get wrong?
   - What was it overly confident about?

### Step 2: Document Findings

Create an issue or note in this format:

```markdown
## Agent: [Domain Name]

### Caught Correctly
- [Finding ID]: [Description of what it got right]

### Missed
- [Description of what was missed and why it matters]
- Suggested prompt addition: "[Exact text to add to prompt]"

### Got Wrong
- [Finding ID]: [What was incorrect and why]
- Root cause: [Why the agent made this mistake]

### Improvement Ideas
- [Ideas for new maturity frameworks, risk patterns, etc.]
```

### Step 3: Make Prompt Changes

1. Open the relevant prompt file in `prompts/`
2. Find the appropriate section (e.g., "AREA 3: PRIVILEGED ACCESS MANAGEMENT")
3. Add your improvement (new risks, better frameworks, clearer guidance)
4. Test by running the agent again

### Step 4: Consider the Reasoning

Beyond just "what to check for," consider:

- **Sequencing:** Should certain checks happen before others?
- **Dependencies:** Does one finding depend on another?
- **Evidence requirements:** What evidence should support this finding?
- **Confidence calibration:** How confident should the agent be about this type of finding?

---

## Questions to Guide Improvement

When reviewing agent outputs, ask:

### About Coverage
- Are there common DD findings this agent never produces?
- Are there industry-specific patterns we're missing?
- Are there new technologies/platforms we don't cover?

### About Accuracy
- Are confidence levels appropriate for the evidence?
- Are findings actually supported by the document?
- Are we seeing hallucinated details?

### About Usefulness
- Would an IC find this output useful?
- Are the risk mitigations actionable?
- Are cost estimates in the right ballpark?
- Are gaps specific enough to act on?

### About the Workflow
- Is the agent checking things in the right order?
- Are there dependencies between findings we're missing?
- Should we subdivide any agents for better focus?

---

## File Structure Reference

```
it-diligence-agent/
├── main.py                 # Entry point - orchestrates the analysis
├── config.py               # Configuration settings
│
├── agents/                 # Domain agent implementations
│   ├── base_agent.py       # Shared agent logic
│   ├── infrastructure_agent.py
│   ├── network_agent.py
│   ├── cybersecurity_agent.py
│   ├── applications_agent.py
│   ├── identity_access_agent.py
│   └── coordinator_agent.py
│
├── prompts/                # Agent system prompts (EDIT THESE)
│   ├── dd_reasoning_framework.py    # Shared four-lens methodology
│   ├── infrastructure_prompt.py
│   ├── network_prompt.py
│   ├── cybersecurity_prompt.py
│   ├── applications_prompt.py
│   ├── identity_access_prompt.py
│   ├── coordinator_prompt.py
│   └── shared/             # Anti-hallucination components
│       ├── evidence_requirements.py
│       ├── hallucination_guardrails.py
│       ├── gap_over_guess.py
│       └── confidence_calibration.py
│
├── tools/                  # Tool definitions for agents
│   └── analysis_tools.py   # All tool schemas and AnalysisStore
│
├── data/
│   ├── input/              # Place documents here
│   └── output/             # Analysis results go here
│
└── EXPANSION_PLAN_120.md   # Full 120-point development plan
```

---

## Running the Tool

### Basic Usage

```bash
# Analyze a specific file
python main.py path/to/document.pdf

# Analyze all files in input directory
python main.py

# Analyze a specific folder
python main.py path/to/folder/
```

### Output Location

Results are saved to `data/output/analysis_YYYYMMDD_HHMMSS/`

### Key Output Files

| File | Description |
|------|-------------|
| `risks.json` | All identified risks with evidence |
| `gaps.json` | Knowledge gaps requiring follow-up |
| `work_items.json` | Phased integration tasks |
| `current_state.json` | Environment inventory |
| `strategic_considerations.json` | Deal implications |
| `ANALYSIS_SUMMARY.md` | Human-readable summary |
| `analysis_report.html` | Interactive viewer |
| `reasoning_chains.json` | Audit trail of agent reasoning |

---

## Summary: How We Get Better

| Improvement Type | Who Does It | Effort | Impact |
|------------------|-------------|--------|--------|
| **Add missed risk patterns** | Domain expert | Low | Medium |
| **Add maturity frameworks** | Domain expert | Medium | Medium |
| **Add industry patterns** | Domain expert | Medium | High |
| **Build reference catalogs** | Developer + Domain | Medium | High |
| **Subdivide agents** | Developer | High | High |
| **Improve anti-hallucination** | Developer | Medium | High |

**The key insight:** The prompts are living documents. The more real scenarios we run, the more we learn, and the better the prompts become. Each team member's domain expertise makes the whole system smarter.

---

*Last updated: January 2026*
*Version: 2.0 (with anti-hallucination framework)*
