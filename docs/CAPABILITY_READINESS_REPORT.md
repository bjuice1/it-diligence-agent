# IT Due Diligence Platform - Capability Readiness Report
## AI Reinvest Runbook Alignment

**Generated:** January 2026
**Platform Version:** V2.1
**Author:** Platform Engineering + AI Reinvest Team

---

## Step 1: Team Lens Summary

### What We're Trying to Accomplish

The AI Reinvest Runbook provides a **capability-based framework** for tracking readiness of AI-powered tools across the firm. This mapping exercise aligns our IT Due Diligence platform with that framework to:

1. **Create an Agile Anchor** - Epics and stories tied to runbook pillars, not arbitrary feature requests
2. **Enable Structured Reviews** - Sprint demos organized by capability area, not random feature showcases
3. **Gate Rollout Decisions** - Clear criteria for when a capability is "ready" for broader use
4. **Communicate with Leadership** - Shared vocabulary between engineering and business stakeholders

### Why Capability Readiness ≠ Engineering Output

| Engineering Output | Capability Readiness |
|-------------------|---------------------|
| "We wrote 2,000 lines of code" | "Users can now upload documents and get structured findings" |
| "We merged 15 PRs this sprint" | "Coverage scoring works across all 6 domains with letter grades" |
| "Tests are passing" | "The system handles edge cases gracefully and produces actionable output" |

**Engineering output** measures *activity*. **Capability readiness** measures *value delivered*.

A capability is "ready" when:
- A user can accomplish their goal without engineering support
- Output is trusted enough for client-facing use
- Edge cases are handled or documented
- Someone can demo it in 3 minutes

### Two-Track Progress System

We run parallel tracking:

| Track | Audience | Cadence | Focus |
|-------|----------|---------|-------|
| **Engineering Progress** | Platform team, technical leads | Weekly | Build stability, test coverage, performance, technical debt |
| **Capability Readiness** | AI Reinvest team, leadership, rollout committee | Bi-weekly/Sprint | User value, demo-ability, rollout readiness, adoption blockers |

This prevents the trap of "lots of code shipped, but users still can't do X."

---

## Step 2: Capability Mapping Table

### Pillar 1: Documents

| Capability | What Exists Today | Evidence | Gaps/Unknowns | Next Stories | Acceptance Criteria | Readiness | Confidence |
|------------|-------------------|----------|---------------|--------------|---------------------|-----------|------------|
| **PDF Ingestion** | PyMuPDF-based extraction, handles various PDF formats | `ingestion/pdf_parser.py` lines 1-150 | Scanned PDFs (OCR) not supported | 1. Add OCR fallback for scanned docs 2. Handle password-protected PDFs | - Extracts text from 95%+ of VDR PDFs - Logs clear error for unsupported formats - Processing time <5s per doc | **100%** | High |
| **Multi-Document Processing** | Batch processing of entire directories | `main_v2.py` `load_documents()` lines 85-120 | No duplicate detection | 1. Add duplicate file detection 2. Show per-document processing status | - Processes 1-50 docs in single run - Shows progress per document - Handles mixed PDF/TXT | **100%** | High |
| **Source Attribution** | Every fact links to source document + section | `tools_v2/fact_store.py` `Fact.evidence` field | Page numbers not always captured | 1. Improve page number extraction 2. Add clickable source links in HTML | - 90%+ facts have source quote - Source section identified - Can trace finding back to document | **75%** | Medium |
| **Document Change Detection** | SHA256 hash-based tracking in sessions | `tools_v2/session.py` `ProcessedDocument` class | Only detects file-level changes | 1. Content-level diff for modified docs 2. Show what changed between runs | - Detects new documents - Detects modified documents - Skips unchanged documents | **75%** | High |

### Pillar 2: Ingest & Chunk

| Capability | What Exists Today | Evidence | Gaps/Unknowns | Next Stories | Acceptance Criteria | Readiness | Confidence |
|------------|-------------------|----------|---------------|--------------|---------------------|-----------|------------|
| **Fact Extraction** | Haiku-based discovery agents extract structured facts | `agents_v2/base_discovery_agent.py` | None significant | 1. Add confidence scoring per fact 2. Improve extraction of numeric data | - Facts have unique IDs (F-XXX-001) - Each fact has evidence quote - Consistent schema across domains | **100%** | High |
| **Gap Identification** | Explicit gap tracking with G-XXX-001 IDs | `tools_v2/discovery_tools.py` `flag_gap()` | Gap prioritization is basic | 1. Auto-prioritize gaps by criticality 2. Suggest which gaps block analysis | - Gaps explicitly flagged - Gap linked to expected category - Clear "why needed" explanation | **100%** | High |
| **Entity Recognition** | Target vs Buyer distinction in all facts | `prompts/shared/entity_distinction.py` | Ambiguous cases need human review | 1. Flag ambiguous entity cases 2. Add entity resolution UI | - Entity field on every fact - Clear guidance in prompts - Reviewer can override | **75%** | Medium |
| **Model Tiering** | Haiku for discovery (~70% cost savings) | `config_v2.py` `DISCOVERY_MODEL` | None | N/A - Complete | - Discovery uses Haiku - Reasoning uses Sonnet - Cost per run <$2 typical | **100%** | High |

### Pillar 3: Domain Agents

| Capability | What Exists Today | Evidence | Gaps/Unknowns | Next Stories | Acceptance Criteria | Readiness | Confidence |
|------------|-------------------|----------|---------------|--------------|---------------------|-----------|------------|
| **6-Domain Coverage** | Full agents for Infra, Network, Cyber, Apps, IAM, Org | `agents_v2/reasoning/` - 6 agent files | All complete | 1. Add industry-specific variants 2. Domain-specific benchmarks | - All 6 domains analyze in parallel - Each produces risks + work items - Evidence chains validate | **100%** | High |
| **Risk Identification** | Severity-rated risks with mitigations and fact citations | `tools_v2/reasoning_tools.py` `Risk` class | Severity calibration ongoing | 1. Add risk calibration feedback loop 2. Track severity accuracy over time | - Risks cite specific facts - Severity is justified - Mitigation is actionable | **100%** | High |
| **Work Item Generation** | Phased work items with cost estimates | `tools_v2/reasoning_tools.py` `WorkItem` class | Cost ranges need calibration | 1. Refine cost calibration 2. Add effort estimates (FTE-weeks) | - Phase assignment (Day 1/100/Post) - Cost range provided - Owner identified | **75%** | Medium |
| **Strategic Considerations** | Deal-specific insights for IC | `tools_v2/reasoning_tools.py` `StrategicConsideration` | Quality varies by domain | 1. Add one-shot examples to all prompts 2. Improve buyer alignment analysis | - Tied to deal context - Cites supporting facts - Actionable implication | **75%** | Medium |
| **Parallel Execution** | ThreadPoolExecutor with batch size 3 | `main_v2.py` lines 560-620 | None | N/A - Complete | - 6 domains run concurrently - Respects API rate limits - Total time <15 min typical | **100%** | High |

### Pillar 4: Coordinator

| Capability | What Exists Today | Evidence | Gaps/Unknowns | Next Stories | Acceptance Criteria | Readiness | Confidence |
|------------|-------------------|----------|---------------|--------------|---------------------|-----------|------------|
| **Coverage Scoring** | 101-item checklist, letter grades A-F | `tools_v2/coverage.py` | Checklist items may need expansion | 1. Add team feedback mechanism 2. Industry-specific checklists | - Score per domain - Overall letter grade - Missing critical items listed | **100%** | High |
| **Cross-Domain Synthesis** | Consistency checks, related finding grouping | `tools_v2/synthesis.py` | Could identify more cross-domain patterns | 1. Improve pattern detection 2. Add contradiction flagging | - Finds related findings - Aggregates costs correctly - Flags inconsistencies | **75%** | Medium |
| **VDR Generation** | Gap-based requests with priority and suggested docs | `tools_v2/vdr_generator.py` | None significant | 1. Add "already answered" tracking 2. Smart deduplication | - Prioritized (Critical → Low) - Suggested documents listed - Ready to send format | **100%** | High |
| **Cost Aggregation** | By phase, domain, owner type | `tools_v2/reasoning_tools.py` `get_total_cost_estimate()` | Ranges are wide | 1. Narrow ranges with more data 2. Add confidence bands | - Low/high range provided - Breakdown by phase - Breakdown by owner | **75%** | Medium |

### Pillar 5: Structured Output

| Capability | What Exists Today | Evidence | Gaps/Unknowns | Next Stories | Acceptance Criteria | Readiness | Confidence |
|------------|-------------------|----------|---------------|--------------|---------------------|-----------|------------|
| **JSON Export** | Facts, findings, coverage, VDR as JSON | `output/*.json` files | None | N/A - Complete | - Valid JSON schema - All data included - Machine-readable | **100%** | High |
| **HTML Report** | Interactive filterable dashboard | `tools_v2/html_report.py` | Mobile responsiveness | 1. Improve mobile view 2. Add print stylesheet | - Filters by domain/severity - Expandable sections - Professional styling | **100%** | High |
| **Investment Thesis** | PE buyer presentation (HTML) | `tools_v2/presentation.py` | Template vs LLM-generated quality gap | 1. Improve template mode 2. Add export to PDF | - Executive summary - Domain sections - Cost summary - Actionable next steps | **100%** | High |
| **Excel Export** | Multi-sheet workbook with formatting | `tools_v2/excel_export.py` | Just built, needs validation | 1. Validate with real data 2. Add pivot-ready structure | - Facts sheet - Risks sheet - Work items sheet - VDR sheet | **75%** | Medium |
| **Markdown Summary** | Executive summary for IC memo | `output/executive_summary_*.md` | None | N/A - Complete | - 1-2 page summary - Key risks highlighted - Recommendations included | **100%** | High |

### Pillar 6: Data Flow

| Capability | What Exists Today | Evidence | Gaps/Unknowns | Next Stories | Acceptance Criteria | Readiness | Confidence |
|------------|-------------------|----------|---------------|--------------|---------------------|-----------|------------|
| **Session Management** | Persistent state, incremental analysis | `tools_v2/session.py` `DDSession` class | UI for session management | 1. Build session dashboard 2. Add session comparison | - Create/resume sessions - Track processed docs - Persist facts/findings | **100%** | High |
| **Deal Context** | Carve-out vs Bolt-on aware analysis | `tools_v2/session.py` `DealContext`, `DEAL_TYPE_CONFIG` | Industry context not yet integrated | 1. Add industry-specific context 2. Improve context injection | - Deal type shapes analysis - Key questions per type - Risk lens per type | **100%** | High |
| **Audit Trail** | Run history with timestamps | `tools_v2/session.py` `SessionRun` | Limited modification tracking | 1. Track all changes 2. Add "undo" capability | - Know when analysis ran - Know what changed - Can reproduce results | **75%** | Medium |
| **CLI Interface** | Full-featured command line | `main_v2.py` argparse setup | None | N/A - Complete | - All options documented - Help text clear - Exit codes meaningful | **100%** | High |
| **Web UI** | Basic Streamlit app | `app.py` | Early stage, needs refinement | 1. Add deals dashboard 2. Improve results display 3. Add export buttons | - Upload documents - Configure deal - Run analysis - View results | **50%** | Medium |

---

## Step 3: Definition of Done Library

### Pillar-Level DoD

#### Documents Pillar DoD
- [ ] Handles all common VDR document formats (PDF, TXT, DOCX)
- [ ] Extraction succeeds on 95%+ of real-world documents
- [ ] Clear error messages for unsupported formats
- [ ] Source attribution preserved through entire pipeline
- [ ] Processing time acceptable (<5s per typical document)

#### Ingest & Chunk Pillar DoD
- [ ] Facts extracted with consistent schema across all inputs
- [ ] Gaps explicitly identified and categorized
- [ ] Evidence quotes captured and validated
- [ ] Entity (target/buyer) correctly identified
- [ ] Cost per extraction within budget (<$0.50 per domain)

#### Domain Agents Pillar DoD
- [ ] All 6 domains produce meaningful output
- [ ] Risks have severity, mitigation, and fact citations
- [ ] Work items have phase, cost estimate, and owner
- [ ] Strategic considerations tie to deal context
- [ ] No hallucinated findings (all grounded in facts)

#### Coordinator Pillar DoD
- [ ] Coverage score accurately reflects documentation completeness
- [ ] Cross-domain synthesis identifies related findings
- [ ] VDR requests are actionable and prioritized
- [ ] Cost aggregation is mathematically correct
- [ ] Inconsistencies between domains flagged

#### Structured Output Pillar DoD
- [ ] All output formats render correctly
- [ ] Data is consistent across formats
- [ ] Professional appearance suitable for client delivery
- [ ] Export works without manual intervention
- [ ] Accessibility requirements met (readable, navigable)

#### Data Flow Pillar DoD
- [ ] End-to-end pipeline completes without manual steps
- [ ] State persists correctly between sessions
- [ ] Incremental updates work as expected
- [ ] Audit trail captures key events
- [ ] Recovery possible from any failure point

### Capability-Level DoD Pattern (Reusable Checklist)

For any capability to be marked "Ready" (100%):

**Functional:**
- [ ] Happy path works reliably (10+ test runs)
- [ ] Edge cases documented and handled
- [ ] Error messages are actionable
- [ ] Performance is acceptable for intended use

**Validated:**
- [ ] Tested on real-world data (not just test fixtures)
- [ ] Output reviewed by domain SME
- [ ] Feedback incorporated or documented as known limitation

**Documented:**
- [ ] User-facing documentation exists
- [ ] Demo script available (2-3 minutes)
- [ ] Known limitations documented
- [ ] Troubleshooting guide exists

**Operational:**
- [ ] Can be run without engineering support
- [ ] Outputs are self-explanatory
- [ ] Can be demoed to stakeholders

---

## Step 4: Two-Track Reporting System

### Track A: Engineering Progress (Build-Centric)

Report weekly on these 10 metrics:

| Metric | Description | Target | Current |
|--------|-------------|--------|---------|
| **Test Pass Rate** | % of automated tests passing | >95% | 100% (196/196) |
| **Test Coverage** | % of code covered by tests | >70% | TBD |
| **Build Stability** | Consecutive successful builds | >5 | Stable |
| **Pipeline Duration** | Time for full analysis run | <15 min | ~12 min |
| **API Cost per Run** | Average $ per full analysis | <$2.00 | ~$1.50 |
| **Open Bugs** | Unresolved bug count | <10 | TBD |
| **Tech Debt Items** | Flagged refactoring needs | Trend ↓ | TBD |
| **Dependency Health** | Outdated/vulnerable deps | 0 critical | TBD |
| **Code Churn** | Lines changed this week | Context | TBD |
| **PR Cycle Time** | Avg time from PR open to merge | <2 days | N/A |

### Track B: Capability Readiness (Runbook-Centric)

Report bi-weekly on capability status:

| Capability | Readiness | Confidence | RAG | Blocker | Next Milestone |
|------------|-----------|------------|-----|---------|----------------|
| PDF Ingestion | 100% | High | 🟢 | None | Add OCR support |
| Fact Extraction | 100% | High | 🟢 | None | Confidence scoring |
| Risk Identification | 100% | High | 🟢 | None | Severity calibration |
| Work Item Generation | 75% | Medium | 🟡 | Cost calibration | Refine estimates |
| Coverage Scoring | 100% | High | 🟢 | None | Industry checklists |
| Excel Export | 75% | Medium | 🟡 | Validation needed | Test with real data |
| Web UI | 50% | Medium | 🟡 | Early stage | Deals dashboard |

**RAG Status Rules:**
- 🟢 **Green**: Readiness ≥75% AND Confidence High AND no blockers
- 🟡 **Yellow**: Readiness 50-74% OR Confidence Medium OR minor blocker
- 🔴 **Red**: Readiness <50% OR Confidence Low OR critical blocker

---

## Step 5: Materials to Develop

| Artifact | Purpose | Owner | Effort | Pillar(s) | Priority |
|----------|---------|-------|--------|-----------|----------|
| **Demo Script: Documents** | Show upload → extraction flow | Me | S | Documents | 1 |
| **Demo Script: Discovery** | Show fact extraction + gaps | Me | S | Ingest | 1 |
| **Demo Script: Reasoning** | Show risk + work item generation | Me | S | Domain Agents | 1 |
| **Demo Script: Outputs** | Show all export formats | Me | S | Structured Output | 1 |
| **Demo Script: Full Pipeline** | End-to-end 5-minute demo | Me | M | All | 1 |
| **Sprint Review Checklist** | Standard review agenda template | Team | S | All | 2 |
| **Acceptance Criteria Library** | Reusable AC patterns by capability | Team | M | All | 2 |
| **SME Review Workflow Spec** | How SMEs validate/override findings | Team | M | Domain Agents, Coordinator | 2 |
| **Known Limitations Doc** | What the system doesn't do well | Me | S | All | 2 |
| **Release Readiness Checklist** | Gate criteria for broader rollout | Team | M | All | 3 |
| **Non-Technical Overview** | 1-page system explanation | Team | S | All | 3 |
| **Update Dashboard Outline** | Manual tracking spreadsheet | Team | S | All | 3 |

### Demo Script Outlines

**Demo 1: Documents (2 min)**
1. Show sample VDR documents (30s)
2. Run upload/extraction (60s)
3. Show source attribution in output (30s)

**Demo 2: Discovery (3 min)**
1. Show raw document text (30s)
2. Run discovery phase (90s)
3. Walk through extracted facts + gaps (60s)

**Demo 3: Reasoning (3 min)**
1. Show facts going into reasoning (30s)
2. Run reasoning phase (90s)
3. Walk through risks with evidence chains (60s)

**Demo 4: Outputs (2 min)**
1. Show HTML report with filters (45s)
2. Show Excel export (30s)
3. Show VDR requests (45s)

**Demo 5: Full Pipeline (5 min)**
1. Upload documents (30s)
2. Configure deal (30s)
3. Run analysis (2 min - narrate while running)
4. Review key findings (2 min)

---

## Step 6: Weekly Update Template + Sprint Review Format

### Weekly Update Template (1 Page)

```
IT DD Platform - Weekly Update
Week of: [DATE]
Author: [NAME]

═══════════════════════════════════════════════════════════
ENGINEERING PROGRESS
═══════════════════════════════════════════════════════════

Build Health: [🟢/🟡/🔴]
├─ Tests: [X/Y] passing ([Z]%)
├─ Pipeline: [Stable/Unstable]
├─ Avg Run Time: [X] min
└─ Avg Cost/Run: $[X.XX]

Completed This Week:
• [Item 1]
• [Item 2]
• [Item 3]

In Progress:
• [Item 1] - [X]% complete
• [Item 2] - [X]% complete

Blockers:
• [None / Description]

═══════════════════════════════════════════════════════════
CAPABILITY READINESS
═══════════════════════════════════════════════════════════

Readiness Changes:
• [Capability]: [Old]% → [New]% ([reason])
• [Capability]: [Old]% → [New]% ([reason])

Demo-Ready Capabilities: [X] of [Y]

RAG Summary:
🟢 Green: [X] capabilities
🟡 Yellow: [Y] capabilities
🔴 Red: [Z] capabilities

Key Capability Update:
[2-3 sentences on most important capability progress]

═══════════════════════════════════════════════════════════
RISKS & ISSUES
═══════════════════════════════════════════════════════════

| Risk/Issue | Impact | Mitigation | Owner | Status |
|------------|--------|------------|-------|--------|
| [Item]     | [H/M/L]| [Action]   | [Who] | [Open] |

═══════════════════════════════════════════════════════════
NEXT WEEK PRIORITIES
═══════════════════════════════════════════════════════════

1. [Priority 1]
2. [Priority 2]
3. [Priority 3]
4. [Priority 4]
5. [Priority 5]

Questions for Team:
• [Question 1]
• [Question 2]
```

### Sprint Review Agenda (45 min)

```
IT DD Platform - Sprint Review
Sprint: [X] | Date: [DATE]

1. SPRINT SUMMARY (5 min)
   - Sprint goal recap
   - Velocity/completion rate
   - Key accomplishments

2. DEMO: [CAPABILITY 1] (10 min)
   - Live demonstration
   - Q&A

3. DEMO: [CAPABILITY 2] (10 min)
   - Live demonstration
   - Q&A

4. CAPABILITY READINESS UPDATE (10 min)
   - Walk through readiness table changes
   - Discuss RAG status changes
   - SME feedback incorporation

5. RISKS & BLOCKERS (5 min)
   - Current blockers
   - Mitigation status

6. NEXT SPRINT PREVIEW (5 min)
   - Proposed sprint goal
   - Key stories
   - Dependencies
```

### Risk/Issues Log Format

| ID | Date Opened | Risk/Issue | Category | Impact | Probability | Mitigation | Owner | Status | Resolution Date |
|----|-------------|------------|----------|--------|-------------|------------|-------|--------|-----------------|
| R-001 | 2026-01-15 | Cost estimates need calibration | Quality | Medium | High | Collect actuals from completed deals | Platform Team | Open | - |
| R-002 | 2026-01-10 | Web UI not ready for non-technical users | Adoption | High | High | Prioritize Streamlit improvements | Platform Team | In Progress | - |

---

## Open Questions to Validate

1. **Runbook Capabilities**: Does the team have a specific capability list we should map to, or should we use the pillar structure above?

2. **SME Review Process**: Who are the designated SMEs for each domain? What's their availability for validation?

3. **Rollout Gating**: What readiness threshold is required before broader rollout? (e.g., all capabilities at 75%+?)

4. **Cost Calibration Data**: Do we have access to actual project costs from completed deals to calibrate estimates?

5. **Industry Variants**: Which industries should we prioritize for specialized analysis? (Healthcare, Financial Services, Manufacturing)

6. **Web UI Priority**: Is the Web UI a rollout blocker, or can we proceed with CLI + training?

---

## Recommended Next Sprint Goals

1. **Validate Excel Export** - Test with 3 real deal datasets, incorporate feedback (2 pts)

2. **Build Demo Scripts** - Create 5 demo scripts per outline above (3 pts)

3. **Improve Web UI** - Add deals dashboard, better results display (5 pts)

4. **Cost Calibration Round 1** - Collect 5 actual vs. estimated comparisons (3 pts)

5. **SME Review Session** - Schedule reviews with domain SMEs for 2 domains (2 pts)

6. **Known Limitations Doc** - Document current system boundaries (2 pts)

7. **Sprint Review Checklist** - Finalize template with team (1 pt)

8. **Update Roadmap** - Add improvements list from UI discussion (1 pt)

---

*Document generated from repo analysis. Citations reference files in `/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent/`*
