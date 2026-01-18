# Investment Thesis Presentation Generator

## Design Document

**Goal**: Generate presentation-style HTML output that tells the IT story for PE buyers

---

## Framing (Critical)

This is NOT a sales pitch. This is a **candid partner-level conversation** about what the buyer is actually taking on.

### The Perspective

Think: **Big Four Partner** sitting across the table from a PE deal team

- **Candid, not salesy** - Plain talk about what's there
- **Client-focused** - What does the buyer actually need to know?
- **Not guiding decisions** - Present facts, let them decide
- **Practical focus** - "When you own this business, here's what you'll deal with"
- **Objective** - Honest about both strengths and weaknesses

### The Tone

**Wrong**: "The target has a robust, enterprise-grade infrastructure..."
**Right**: "They're running on two colocated data centers with aging VMware. You'll need to decide if you're modernizing or migrating to cloud."

**Wrong**: "There are some minor gaps in documentation..."
**Right**: "We don't have visibility into their network architecture. That's 4 VDR requests you'll need answers on before you can plan Day 1."

**Wrong**: "The cybersecurity posture is generally aligned with best practices..."
**Right**: "No PAM solution, no documented incident response plan. If you're in a regulated industry or need cyber insurance, this is Day 1 work."

---

## Slide Structure

**Minimum**: 1 slide per domain (6 domain slides) + Executive Summary + Work Plan + Open Questions = **9-10 slides**

Each domain slide follows this structure:
1. **The "So What"** (highlight) - One sentence that captures the key implication
2. **Main Considerations** - 3-5 bullet points from the domain agent's findings
3. **Supporting Explanation** - Tell the story, not sparse, but succinct

**Not sparse with words - tell the story. But succinct - no waffling.**

---

## Content Sections

### 1. Executive View (1 slide)
**What it is**: One-page summary for IC presentation

- Total IT spend / headcount
- Key systems (ERP, CRM, core apps)
- Top 3 risks
- Total integration cost range
- Overall assessment (not a grade, a statement)

**Example statement**: "Mid-complexity integration. Core systems are stable but require modernization. Expect $4-6M over 18 months, front-loaded in Day 1."

---

### 2-7. Domain Slides (1 per agent = 6 slides)

Each domain gets its own slide with this structure:

#### Infrastructure Slide
```
┌─────────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE                                                   │
│                                                                  │
│ SO WHAT:                                                         │
│ "Hybrid cloud footprint with aging on-prem. Expect              │
│  modernization costs within 18 months."                         │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ KEY CONSIDERATIONS:                                              │
│ • Two colo facilities (Atlanta primary, NYC secondary)          │
│ • 47 AWS accounts, $6.7M annual spend                           │
│ • Azure presence ($2.9M) - potential consolidation target       │
│ • No documented DR/BCP testing                                   │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ THE STORY:                                                       │
│ The target started on-prem and has been migrating to cloud      │
│ over the past 3 years. The AWS footprint is substantial but     │
│ fragmented across 47 accounts with no central governance.       │
│ Azure was added opportunistically. You'll need to make a        │
│ cloud platform decision: consolidate on AWS, migrate to         │
│ Azure, or maintain both with proper governance. The colo        │
│ contracts likely have exit terms worth reviewing.               │
│                                                                  │
│ COST IMPACT: $X.X - $X.XM (phase breakdown)                     │
│                                                                  │
│ [Source: IT Inventory.xlsx, Cloud Cost Report Q4]               │
└─────────────────────────────────────────────────────────────────┘
```

#### Network Slide
**SO WHAT**: Network infrastructure is undocumented - significant blind spot for integration planning.

#### Cybersecurity Slide
**SO WHAT**: Security foundation exists but gaps in PAM and IR need Day 1 attention.

#### Applications Slide
**SO WHAT**: Dual-ERP complexity (NetSuite + Oracle) will require rationalization decision.

#### Identity & Access Slide
**SO WHAT**: Azure AD deployed but no privileged access controls - immediate security work needed.

#### Organization Slide
**SO WHAT**: Heavy outsourcing (44%) creates transition risk and potential service gaps.

---

### 8. Integration Scenarios (2 slides)
**What it is**: How this fits with buyer's environment

**Scenario A: Standalone** (carve-out, hold separately)
- What needs to happen Day 1
- Ongoing operational costs
- Key risks if staying standalone

**Scenario B: Integrate** (merge with buyer's platform)
- Migration path (cloud, systems, identity)
- Cost and timeline
- Key dependencies and blockers

---

### 9. Work Plan (1-2 slides)
**What it is**: What actually needs to happen

| Phase | Work | Owner | Cost Range |
|-------|------|-------|------------|
| Day 1 | TSA setup, security basics, access | Both | $X - $Y |
| Day 100 | Core migrations, system decisions | Target | $X - $Y |
| Post 100 | Long-term modernization | Buyer | $X - $Y |

---

### 10. Open Questions (1 slide)
**What it is**: What we still don't know

- VDR requests outstanding
- Assumptions that need validation
- Dependencies on target cooperation

**Framing**: "These are the things that could change the numbers"

---

## Output Format

### HTML Presentation
- Slide-deck style layout (one section per "slide")
- Printable to PDF
- Clickable navigation
- Expandable details (click to see supporting facts)
- Clean, professional styling

### Structure
```html
<div class="slide" id="executive-view">
  <h1>Executive Summary</h1>
  <div class="key-metrics">...</div>
  <div class="assessment">...</div>
  <button class="details-toggle">See supporting data</button>
  <div class="details hidden">
    <!-- Facts, work items that support this view -->
  </div>
</div>
```

---

## Data Sources

The presentation pulls from existing analysis:

| Section | Data Source |
|---------|-------------|
| Current State | FactStore (facts by domain) |
| What Works | Facts with status=documented, low-risk findings |
| What Doesn't | Risks, Gaps, high-severity findings |
| Integration | Work items by phase + integration_dependent flags |
| Work Plan | Work items with cost_estimate |
| Open Questions | Gaps + VDR requests |

---

## Implementation Approach

### Phase 1: Static Template
1. Create `tools_v2/presentation.py`
2. Build template with hardcoded sections
3. Inject data from FactStore/ReasoningStore
4. Generate `presentation_{timestamp}.html`

### Phase 2: Narrative Generation
1. Add LLM call to generate section narratives
2. Use facts as context, generate prose
3. Maintain candid, partner-level tone

### Phase 3: Integration Scenarios
1. Accept buyer profile input
2. Generate scenario-specific recommendations
3. Compare target vs buyer environments

---

## Example Output

### Executive View

```
ACME Corp IT Due Diligence
Investment Thesis Summary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEY METRICS
• IT Spend: ~$12M annually (cloud: $9.5M, colo: $800K)
• Headcount: 117 internal, 44% outsourced operations
• Core Systems: NetSuite (ERP), Salesforce (CRM), AWS/Azure hybrid

TOP RISKS
1. No PAM solution - privileged access uncontrolled
2. Dual-ERP environment - 8,200 users across NetSuite + Oracle
3. Colocation contracts - potential exit penalties

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOTTOM LINE

Mid-complexity integration. The IT environment is functional but
carries deferred modernization. Cloud-first, but with legacy patterns.

Expected integration cost: $4.5M - $13.3M over 18 months
• Day 1: $1.7M - $5.3M (security, access, TSA)
• Day 100: $2.0M - $5.4M (core decisions, migrations)
• Post 100: $0.8M - $2.6M (long-term modernization)

The target can run standalone with TSA, but you'll want to make
platform decisions within 6 months to avoid duplicate spend.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[See Current State →]  [See Risks →]  [See Work Plan →]
```

---

## Non-Goals

- This is NOT a replacement for the full DD report
- This is NOT meant to make decisions for the buyer
- This is NOT a checklist or compliance document
- This is NOT for target consumption (buyer-facing only)

---

## Success Criteria

1. A PE partner can present this to their IC with no editing
2. Tone is consistently candid, not promotional
3. All claims link back to specific facts
4. Integration scenarios are actionable
5. Cost ranges are clearly explained
6. Open questions are front and center

---

## Key Principles

### 1. Holistic "So What" Perspective
Don't just list facts - explain what they mean for the buyer.

**Wrong**: "They have 47 AWS accounts."
**Right**: "47 AWS accounts across the org suggests decentralized cloud governance. You'll need to consolidate billing, standardize security policies, and likely sunset some accounts. Budget 3-6 months for cloud rationalization."

### 2. Visual Fact Presentation
Facts should be visually clear, scannable:
- Key metrics in large callout boxes
- Risk severity as color-coded badges
- Cost ranges in prominent tables
- Timeline diagrams for integration phases

### 3. Source Citations (Document Callouts)
Every fact should trace back to source documents with small callouts:

```
┌─────────────────────────────────────────────┐
│ AWS Annual Spend: $6.7M                      │
│ ─────────────────────────────────────────── │
│ Source: "Application Inventory.xlsx" p.3     │
│         "Cloud Cost Report Q4 2025.pdf"      │
└─────────────────────────────────────────────┘
```

This builds trust and enables verification.

---

## Implementation Checklist

### Phase 1: Core Presentation (MVP) ✅ Complete
- [x] Create `tools_v2/presentation.py`
- [x] Build slide-deck HTML template
- [x] Executive Summary slide
- [x] Domain slides (6 slides, one per agent)
- [x] Work Plan by phase
- [x] Cost summary table
- [x] Open Questions slide
- [x] Generate from existing FactStore/ReasoningStore

### Phase 2: Source Citations ✅ Complete
- [x] Track source documents in FactStore evidence
- [x] Display source references in narratives
- [x] Link to fact IDs for traceability
- [x] Confidence indicator (high/medium/low)

### Phase 3: Narrative Generation ✅ Complete
- [x] LLM-generated "so what" summaries per section
- [x] Candid tone enforcement in prompts
- [x] 6 domain narrative agents (parallel, Sonnet)
- [x] Cost synthesis agent (sequential)
- [x] Thread-safe NarrativeStore
- [x] `--narrative` flag to enable
- [x] Executive-ready language

**Implementation Files**:
- `agents_v2/narrative/base_narrative_agent.py` - Base class
- `agents_v2/narrative/*_narrative.py` - 6 domain agents
- `agents_v2/narrative/cost_synthesis_agent.py` - Cost aggregation
- `tools_v2/narrative_tools.py` - NarrativeStore, tools, validation

### Phase 4: Integration Scenarios (Not Started)
- [ ] Accept buyer profile input (optional)
- [ ] Generate standalone vs integrate analysis
- [ ] Cost comparison by scenario
- [ ] Synergy identification
- [ ] TSA requirements

### Phase 5: Visual Enhancements (Not Started)
- [ ] Infrastructure diagrams (auto-generated)
- [ ] Application landscape map
- [ ] Timeline visualization
- [ ] Risk heat map
- [ ] Cost waterfall chart

### Phase 6: Export Options (Not Started)
- [ ] PowerPoint export (via python-pptx)
- [ ] PDF export (print-friendly CSS)
- [ ] Notion/Confluence import format

---

## Usage

### Template-Based (Fast, Default)
```bash
python main_v2.py data/input/ --all --target-name "ACME Corp"
```
Generates `investment_thesis_{timestamp}.html` using template interpolation.

### LLM-Generated Narratives (Best Quality)
```bash
python main_v2.py data/input/ --all --narrative --target-name "ACME Corp"
```
Runs 6 narrative agents + cost synthesis agent. Produces richer storytelling content.

**Additional Output**: `narratives_{timestamp}.json`

---

*Design Version: 1.2 | January 15, 2026 | Phases 1-3 Complete*
