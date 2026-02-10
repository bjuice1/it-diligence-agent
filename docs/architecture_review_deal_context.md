# IT DD Agent: Architecture Review — Deal Context, Orchestration & Agent Self-Awareness

## Purpose of This Document

Critical assessment of how the agent system manages deal context, adapts to deal types, orchestrates parallel domain agents, and maintains self-awareness of what it has and hasn't covered. Written for external review to identify architectural gaps before building further.

---

## 1. THE DEAL TYPES THAT ACTUALLY MATTER

The system currently defines 5 deal types in `deal_framework.py` (carveout, acquisition, divestiture, merger, platform_addon) and 2 in `session.py` (carve_out, bolt_on). This is already a problem — there are two overlapping enum systems that don't share a canonical definition.

More importantly, the deal types that matter in practice reduce to **three scenarios** distinguished by two questions:

### Question 1: Is there a parent company?
### Question 2: Is the target integrating into the buyer or running standalone?

| Scenario | Parent? | Integration? | What Matters |
|----------|---------|-------------|--------------|
| **A. Acquisition + Integration** | No parent (or parent is irrelevant) | Yes — target merges into buyer | Synergies, platform consolidation, migration complexity, Day-1 continuity |
| **B. Acquisition + Standalone** | No parent | No — target runs independently (PE hold) | Standalone readiness, scalability, tech debt cost, build-vs-buy for gaps |
| **C. Carve-out (parent exists)** | Yes — target is being separated from parent | Either (but separation comes first) | **Entanglement is the dominant variable.** TSA dependencies, shared systems, license disentanglement, identity separation, network separation, stranded costs |

### Why Scenario C Changes Everything

When a parent exists, **entanglement analysis becomes the primary lens**, not a secondary consideration. The system needs to answer:

- What IT systems does the target share with the parent?
- What licenses are under parent enterprise agreements?
- What infrastructure is co-located or co-managed?
- What identity/directory services are shared?
- What networks are shared (WAN, MPLS, SD-WAN)?
- What support functions (help desk, NOC, SOC) come from the parent?
- What data is commingled in shared databases?

Each of these has a **cost to disentangle** and a **timeline to disentangle**, and many are Day-1 blocking. The system has `deal_implications.py` with patterns for these (e.g., `parent_enterprise_license` triggers cost uplift for carveouts), but these patterns are **reactive** (triggered by signals in extracted facts) rather than **proactive** (the agent doesn't go looking for entanglement evidence if it hasn't found any yet).

### What the System Gets Right

- `deal_framework.py` correctly identifies that carveout/divestiture have different Day-1 workstreams than acquisitions
- `mna_framing.py` defines TSA_EXPOSURE and SEPARATION_COMPLEXITY lenses that activate for carveout/divestiture
- `buyer_context_config.py` controls which domains receive buyer facts (applications=50, infrastructure=30, etc.)
- `deal_implications.py` has codified patterns that trigger entanglement-specific cost/risk implications

### What the System Gets Wrong

1. **Deal type is set once and never re-evaluated.** If the team discovers mid-analysis that a "standalone acquisition" actually has deep parent entanglements (common — initial data rooms often omit this), the system can't adapt.

2. **The parent entity doesn't exist as a first-class concept.** The system has `target` and `buyer` entities. There's no `parent` entity. When parent systems show up in documents, they get tagged as `target` facts, losing the crucial distinction between "what the target owns" and "what the target uses but the parent owns."

3. **Entanglement isn't a domain.** It's a cross-domain concern that touches infrastructure (shared DC), applications (shared ERP modules), identity (shared AD forest), network (shared WAN), cybersecurity (shared SOC), and organization (shared IT team). The current domain-parallel architecture doesn't have a natural place for this cross-cutting analysis.

4. **The two DealType enum systems are inconsistent.** `deal_framework.py` has 5 types, `session.py` has 2. Neither maps cleanly to the three scenarios above.

---

## 2. ORCHESTRATION: WHAT EXISTS AND WHAT'S MISSING

### What Exists (More Than Initially Apparent)

The system has **four orchestrators** that are fully implemented:

**A. ExtractionOrchestrator** (`services/extraction_orchestrator.py`)
- Manages extract → validate → retry loop per domain
- Targeted re-extraction when validation fails (focuses on specific gaps)
- Up to 3 attempts before escalating to human
- This is solid and production-ready.

**B. MultiPassOrchestrator** (`agents_v2/multipass_orchestrator.py`)
- Three-pass extraction: (1) System Discovery, (2) Detail Extraction, (3) Validation & Reconciliation
- Sequential through all domains
- Tracks metrics per pass

**C. ReasoningOrchestrator** (`tools_v2/reasoning_orchestrator.py`)
- Coordinates three-stage reasoning (considerations → work items → cost/timeline)
- Supports fast mode (stages 1+2 only) and full mode (all 3)
- Produces risks, work items, recommendations, strategic considerations

**D. CrossDomainValidator** (`tools_v2/cross_domain_validator.py`)
- **This is the closest thing to "looking across agent outputs for overlap."** It runs 7 deterministic consistency checks:
  - Headcount vs endpoints ratio
  - Headcount vs applications count
  - Vendor consistency across domains
  - Security team vs security tools
  - Cost per head sanity
  - Budget vs component costs
  - Stated vs calculated headcount
- Also runs an LLM holistic review for logical inconsistencies

**E. Coverage Analyzer** (`tools_v2/coverage.py`)
- Per-domain checklists with critical/important/nice-to-have items
- Calculates what percentage of expected items were found
- Identifies gaps — "we expected to find X but didn't"

### The Execution Flow (main_v2.py)

```
1. Load documents
2. Discovery — parallel domain agents extract facts → FactStore
3. Reasoning — parallel domain agents analyze facts → ReasoningStore
4. Coverage analysis — what's missing?
5. Cross-domain synthesis — consistency checks
6. Narrative generation
7. Report output
```

### What's Actually Missing

**Missing #1: No "What's Next" Manifest**

The agents run, produce output, and stop. There's no mechanism where the system says: "I've completed extraction for 6 domains. Based on what I found (and didn't find), here's what the team should investigate next." The coverage analyzer identifies gaps, but those gaps aren't translated into actionable next steps for the deal team.

What should exist: After each analysis run, the system produces a **Deal Context Report** that says:
- Here's what I analyzed and what I found
- Here's what I expected to find but didn't (coverage gaps)
- Here are cross-domain inconsistencies that need human clarification
- **Here are deal-type-specific questions that remain unanswered** (e.g., for a carveout: "No evidence of shared identity infrastructure was found — confirm whether target has its own AD forest or shares with parent")
- Here's what changes if you provide additional information

**Missing #2: No Deal-Type Checklist at Completion**

The coverage checklists are per-domain and per-category (e.g., "infrastructure > backup_dr > RPO/RTO targets"). They don't include deal-type-specific checks. For example:

For a carveout, the system should verify at completion:
- [ ] Identified all parent-shared systems
- [ ] Identified all enterprise license agreements through parent
- [ ] Identified shared infrastructure (DC, cloud accounts)
- [ ] Identified shared identity/directory services
- [ ] Identified shared network links
- [ ] Identified shared support services (help desk, NOC, SOC)
- [ ] Estimated TSA durations per service
- [ ] Estimated standalone costs for each shared service
- [ ] Identified Day-1 blocking dependencies

For an acquisition + integration, the checklist is different:
- [ ] Identified overlapping systems (target vs buyer)
- [ ] Identified vendor mismatch risks
- [ ] Estimated migration complexity per domain
- [ ] Identified synergy opportunities with cost estimates
- [ ] Identified integration timeline by domain
- [ ] Identified buyer platform standards target must conform to

These checklists exist conceptually in `deal_framework.py` (workstream definitions) but are not wired into the post-analysis verification step.

**Missing #3: No Cross-Domain Insight Aggregation**

The CrossDomainValidator checks for **consistency** (do the numbers add up across domains). It does NOT check for **insight** (the applications team found SAP is shared with parent, AND the infrastructure team found the primary DC is parent-owned — together this means Day-1 is blocked without TSA).

What should exist: A synthesis step that takes all domain findings and identifies **compound risks** — situations where findings from multiple domains combine to create a risk bigger than any individual finding.

**Missing #4: Incremental Context Is Passive**

The system supports meeting notes as input and can process new documents incrementally. But it's passive — you feed it data and it re-runs. It doesn't say "based on what I've found so far, here are the 5 questions I'd ask in the next management meeting." This is the "agent knowing what's next" capability you're describing.

---

## 3. AGENT SELF-AWARENESS: "WHAT DID I DO, WHAT'S NEXT"

### Current State

The agents have **no self-awareness**. Each domain agent extracts or reasons independently. They don't know:
- What other agents found
- What the overall deal context implies they should look for
- What's missing from their own analysis
- What questions remain unanswered

The coverage analyzer and cross-domain validator partially address this after the fact, but they're post-processing — not integrated into the agent's reasoning loop.

### What "Self-Aware" Should Mean in Practice

After completing an analysis run, the system should produce a structured output:

```
DEAL CONTEXT ASSESSMENT
=======================
Deal Type: Carve-out from Parent Corp
Entity Structure: Target (AcmeCo) being separated from Parent (MegaCorp)
Buyer: PE Fund X (no existing platform)

ANALYSIS COMPLETED
==================
Domains Analyzed: infrastructure, applications, cybersecurity, network, identity_access, organization
Documents Processed: 14 (of 14 in data room)
Facts Extracted: 347 across 6 domains
Risks Identified: 23 (8 critical, 9 high, 6 medium)
Work Items: 31

DEAL-TYPE-SPECIFIC FINDINGS
============================
Entanglement Score: HIGH (4 of 6 domains have parent dependencies)
- Infrastructure: Primary DC is parent-owned (confirmed)
- Applications: SAP ERP runs on parent's S/4HANA instance (confirmed)
- Identity: Target uses parent's Azure AD tenant (confirmed)
- Network: WAN circuits under parent's MPLS contract (confirmed)
- Cybersecurity: SOC is parent-managed (no standalone capability)
- Organization: 3 of 12 IT staff are parent employees supporting target

TSA REQUIREMENTS IDENTIFIED: 6 services
  - DC hosting: 12-18 months, $40-60K/month
  - SAP instance: 18-24 months, $80-120K/month
  - Identity services: 6-12 months, $15-25K/month
  - Network (WAN): 6-12 months, $20-30K/month
  - SOC monitoring: 12-18 months, $25-40K/month
  - Shared IT staff: 6-12 months, $45-65K/month

WHAT I DIDN'T FIND (GAPS)
===========================
1. No evidence of backup/DR configuration — is this parent-managed too?
2. No license inventory — are all licenses under parent EAs?
3. No evidence of data classification — is data commingled in parent databases?
4. Network diagram not found — exact separation scope unknown

RECOMMENDED NEXT STEPS FOR DEAL TEAM
======================================
1. REQUEST from target management: Complete license inventory (especially Microsoft EA, SAP, Oracle)
2. CLARIFY in next management call: Backup/DR ownership — is this parent-provided?
3. REQUEST: Network topology diagram showing parent vs target segments
4. CLARIFY: Data commingling in shared databases — what data extraction is needed?
5. VALIDATE: TSA pricing — are parent's estimates aligned with market?

IF ADDITIONAL INFORMATION IS PROVIDED
=======================================
- Adding license inventory → updates cost estimates for standalone licensing
- Adding network diagram → enables separation timeline for network domain
- Management call notes → may resolve open entanglement questions
- Buyer platform details → enables integration planning for post-separation
```

This is the "tool shed" you're describing — the agent's ability to say "here's my current state, here's what would change my output, go get me this and I'll update."

---

## 4. CONSISTENCY OF OUTPUT WHEN NEW INFORMATION ARRIVES

### Current Mechanism

- `DDSession` tracks processed documents with SHA256 hashes
- New/modified documents trigger incremental extraction
- Reasoning re-runs on the full updated fact set
- `analysis_runner.py` persists incrementally (crash-durable)

### The Problem

When new information arrives (meeting notes, follow-up documents, clarifications from management), the system re-runs reasoning from scratch on the updated fact set. This means:

1. **Output can change unpredictably.** Adding a single clarifying fact can cause the LLM to reframe its entire narrative differently. There's no mechanism to say "keep the existing narrative and just incorporate this new fact."

2. **No diff of what changed.** The team sees a new report but doesn't know what's different from the last version. The `PendingChange` model exists in the database for tracking changes, but it's not wired into the narrative regeneration flow.

3. **Human edits get overwritten.** The `ReportOverride` model we just built solves this for report text, but the underlying findings/risks/work items can still change when reasoning re-runs. A risk that was human-reviewed and accepted might disappear or change if new facts shift the LLM's analysis.

### What Should Exist

- **Finding stability**: Once a finding is human-reviewed, it's pinned — new information can add findings but shouldn't silently modify reviewed ones
- **Change tracking**: Every re-analysis produces a delta showing what was added, modified, or removed
- **Narrative stability**: New facts are incorporated as addendums or modifications to existing narrative, not full rewrites
- **Override preservation**: Human edits to report text are preserved across re-analysis runs (this is now implemented via ReportOverride)

---

## 5. ARCHITECTURAL GAPS — PRIORITIZED

### Gap 1: Parent Entity (HIGH — Blocks Entanglement Analysis)

**Current**: Only `target` and `buyer` entities exist.
**Needed**: `parent` as a third entity type. When facts reference parent-owned systems, they should be tagged `entity=parent`, enabling:
- Automatic entanglement surface calculation (how many facts reference parent?)
- TSA scope derivation (parent-owned = needs TSA)
- Separation cost estimation
- Day-1 dependency mapping

**Complexity**: Medium. Entity is already a string field. Adding "parent" to the allowed values and teaching extraction agents to distinguish target-owned vs parent-owned is the core work.

### Gap 2: Deal-Type Completion Checklists (HIGH — Enables "Did I Consider This?")

**Current**: Coverage checklists are domain-specific (e.g., "does infrastructure have backup/DR info?").
**Needed**: Deal-type-specific checklists that run after analysis:
- Carveout: entanglement identified for each domain? TSA scoped? Standalone costs estimated?
- Acquisition + integration: overlaps identified? synergies estimated? migration complexity assessed?
- Acquisition + standalone: scalability assessed? tech debt quantified? gaps identified?

**Complexity**: Low. The framework exists in `deal_framework.py`. Needs to be extracted into a verifiable checklist that runs post-analysis and reports what's covered vs what's not.

### Gap 3: "What's Next" Output (HIGH — Enables Agent Self-Awareness)

**Current**: Agent produces findings and stops.
**Needed**: After each run, produce a structured "next steps" artifact that:
- Lists coverage gaps as specific questions for the deal team
- Prioritizes by deal-type relevance (entanglement questions first for carveouts)
- Specifies what information would change the analysis if provided
- Can be exported as a "management call prep sheet"

**Complexity**: Medium. Requires a new synthesis step that combines coverage gaps, deal-type checklist gaps, and cross-domain inconsistencies into a structured output.

### Gap 4: Cross-Domain Compound Risk Detection (MEDIUM)

**Current**: CrossDomainValidator checks numerical consistency.
**Needed**: Pattern detection for compound risks:
- "SAP is parent-shared (applications) + DC is parent-owned (infrastructure) = ERP migration is blocked until infrastructure is separated"
- "No standalone AD (identity) + VPN terminates at parent DC (network) = remote access is Day-1 blocked"

**Complexity**: Medium-High. Requires defining compound risk patterns and a synthesis step that matches them against cross-domain findings.

### Gap 5: Incremental Stability (MEDIUM — Enables Consistent Updates)

**Current**: Re-analysis can change everything.
**Needed**: Finding pinning, change tracking, narrative stability as described in Section 4.

**Complexity**: Medium. The PendingChange model exists. ReportOverride is built. The missing piece is making the reasoning pipeline aware of pinned findings and producing deltas.

### Gap 6: Unified Deal Type System (LOW — Cleanup)

**Current**: Two incompatible DealType enums (`deal_framework.py` has 5, `session.py` has 2).
**Needed**: Single canonical DealType enum mapping to the three scenarios described in Section 1, used everywhere.

**Complexity**: Low. Refactoring exercise.

---

## 6. WHAT THE SYSTEM GETS RIGHT (CREDIT WHERE DUE)

The architecture is genuinely well-structured for what it does:

1. **The orchestration layers are real.** ExtractionOrchestrator, ReasoningOrchestrator, MultiPassOrchestrator, and CrossDomainValidator are fully implemented, not stubs.

2. **The prompt template system is deal-type-aware.** Different deal types genuinely receive different prompts, emphasis configurations, required sections, and validation rules.

3. **The entity separation is solid.** Facts are tagged with entity, filtered by entity in generators, and buyer context is domain-configurable with token budgets.

4. **The coverage checklists are comprehensive.** Every domain has detailed expected-item lists with criticality ratings.

5. **Incremental analysis works.** Document change detection, crash-durable persistence, and meeting notes integration are implemented.

6. **The M&A framing is thoughtful.** Five analysis lenses (Day-1, TSA, Separation, Synergy, Cost) with deal-type-specific activation is a good design.

The gaps are in the **connective tissue** — the system does good work per-domain and per-run, but doesn't yet tell the team what to do with the results, what's missing, or how new information would change things. That's the "agent self-awareness" layer.

---

## 7. RECOMMENDATION FOR REVIEW

The core question for architectural review: **Is the right approach to build the "what's next" / self-awareness layer as a post-analysis synthesis step (Option A), or should it be embedded into each agent's reasoning loop so agents can request additional context mid-analysis (Option B)?**

**Option A (Post-Analysis Synthesis)**:
- Simpler to implement — new module that reads all outputs and produces a structured assessment
- Works with the current parallel-agent architecture (agents still run independently)
- Can be iterated quickly
- Downside: agents can't adapt their own analysis based on what other agents found

**Option B (Agent-Embedded Self-Awareness)**:
- Each agent checks deal-type checklist items during its own reasoning
- Agents can flag "I need information from another domain to answer this"
- More sophisticated — agents are truly aware of what they know and don't know
- Downside: significantly more complex, requires inter-agent communication or shared state during execution
- Partially conflicts with parallel execution (agents would need to coordinate)

**Option C (Hybrid — Recommended)**:
- Agents run in parallel as today (no inter-agent communication during execution)
- Each agent checks its own domain-specific items from the deal-type checklist during reasoning
- Post-analysis synthesis step aggregates all domain outputs and produces:
  - Cross-domain compound risks
  - Deal-type completion checklist (checked vs unchecked)
  - Prioritized next-steps for the deal team
  - "What would change" if specific information is provided
- This gives you agent self-awareness within each domain AND cross-domain orchestration after completion
- The orchestrator (which already exists) becomes the "what's next" producer

This document should be reviewed with specific attention to:
1. Are the three deal scenarios (Section 1) the right simplification?
2. Is parent entity as a first-class concept the right architectural move?
3. Is Option C (hybrid) the right approach for self-awareness?
4. What's missing from the gap analysis?
