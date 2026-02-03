# Roadmap
## IT Due Diligence Agent - What's Built, What's Next

---

## Current State (What's Built)

### Core Capabilities ✓

| Capability | Status | Description |
|------------|--------|-------------|
| Document Processing | ✓ Complete | PDF/TXT parsing, text extraction |
| Six-Domain Analysis | ✓ Complete | Infrastructure, Network, Cyber, Apps, IAM, Org |
| Fact Extraction | ✓ Complete | Evidence-backed facts with source quotes |
| Risk Identification | ✓ Complete | Severity ratings, mitigations, citations |
| Work Item Generation | ✓ Complete | Phased, with cost estimates and ownership |
| Coverage Scoring | ✓ Complete | 101-item checklist, letter grades |
| VDR Request Generation | ✓ Complete | Gap-based follow-up questions |
| Cross-Domain Synthesis | ✓ Complete | Consistency checks, cost aggregation |
| Executive Summary | ✓ Complete | Human-readable narrative output |

### Architecture ✓

| Component | Status | Description |
|-----------|--------|-------------|
| V2 Pipeline | ✓ Complete | Discovery → Reasoning split |
| Model Tiering | ✓ Complete | Haiku for extraction, Sonnet for analysis |
| Evidence Chains | ✓ Complete | Every finding cites specific facts |
| Parallel Execution | ✓ Complete | 6 domains run concurrently |
| Tool-Based Output | ✓ Complete | Structured schemas for AI output |
| Session Management | ✓ Complete | Incremental analysis, state persistence |
| Deal Context | ✓ Complete | Deal-type aware analysis (carve-out, bolt-on, platform) |
| Entity Tracking | ✓ Complete | Target vs buyer distinction in facts |

### Documentation ✓

| Document | Status |
|----------|--------|
| Technical Overview | ✓ Complete |
| Getting Started Guide | ✓ Complete |
| Use Cases | ✓ Complete |
| FAQ | ✓ Complete |
| Contribution Guide | ✓ Complete |
| Demo Script | ✓ Complete |

---

## Near-Term (Next 3-6 Months)

### Inventory System Upgrade (Priority: Critical - In Progress)

> **See [INVENTORY_SYSTEM_UPGRADE_PLAN.md](INVENTORY_SYSTEM_UPGRADE_PLAN.md) for full implementation details.**

**Current State:** 100% LLM-based extraction, single FactStore, sequential IDs

**Target State:** Hybrid architecture separating structured inventory from observational facts

| Component | Description |
|-----------|-------------|
| InventoryStore | Structured records for apps, infrastructure, org - directly editable |
| FactStore | Observations with evidence from unstructured content - immutable |
| Deterministic Parsing | Regex/table parsing for ToltIQ outputs (100% accuracy) |
| Content-Based IDs | Hash of key fields for stability across re-imports |
| Application Intelligence | Categorize apps as standard, vertical-specific, niche, custom, unknown |

**Why This Matters:**
- Eliminates extraction errors for structured data (33/33 apps vs probabilistic LLM)
- Enables "brain on top" positioning - analysis layer over reliable data
- Supports direct Excel/table imports from ToltIQ without LLM lossyness

---

### Web-Based User Interface (Priority: High)

**Current State:** CLI-based, input via folder structure, outputs as files

**Target State:** Web UI for easier use by non-technical team members

| Component | Description |
|-----------|-------------|
| Upload Interface | Drag-and-drop for VDR documents (PDF, Word, Excel) |
| Deal Configuration | Form-based input for deal context, target/buyer info |
| Progress Dashboard | Real-time progress tracking for each domain |
| Output Viewer | Interactive HTML preview with export options |

**Technology Options:**
- **Streamlit** (fastest to implement, Python-native) - Recommended for V1
- Next.js + FastAPI (more scalable, better UX) - For production scale
- Gradio (good for ML-focused apps)

### Benchmark Data Integration (Priority: High)

**Current State:** No external benchmarking, findings based solely on document analysis

**Target State:** Compare target metrics against industry benchmarks

| Benchmark Type | Metrics |
|----------------|---------|
| IT Spend | IT spend as % of revenue, cost per user |
| Staffing | IT FTE ratios, team composition |
| Technology | Cloud adoption, app portfolio size |
| Integration | Historical cost/timeline by deal type |

**Data Sources:**
- Excel/CSV files with curated benchmark data
- Industry reports (Gartner, Forrester, etc.)
- Historical deal data from completed transactions

**Output Enhancement Example:**
> "Target IT spend is $2.1M (2.8% of revenue), below the healthcare industry median of 3.5%."

### IT Organization Enhancements (Priority: High)

#### Spans & Layers Analysis
| Metric | Description |
|--------|-------------|
| Layer Count | Levels from CEO to individual contributor |
| Span of Control | Direct reports per manager |
| Target Ratios | Compare to optimal (5-7 direct reports) |
| Recommendations | Flatten/restructure suggestions |

**Output Example:**
```
IT Organization Structure:
- Layers: 5 (CEO → CIO → VP → Director → Manager → IC)
- Avg Span of Control: 3.2 (below optimal 5-7)
- Recommendation: Flatten by 1 layer post-close
```

#### Additional Org Analysis
- Key person risk analysis (tenure, single points of failure)
- Retention planning priorities
- Knowledge transfer requirements
- Succession planning gaps

### Application Portfolio Enhancements (Priority: High)

#### Enterprise Application Landscape Diagram
- Visual portfolio by category
- Integration mapping (which apps talk to which)
- Rationalization opportunities
- Technical debt scoring per application

#### Application Rationalization Calculator
- Overlap detection (multiple CRMs, ERPs, etc.)
- Cost to maintain vs cost to migrate
- Synergy potential from consolidation

### Output Organization Improvements (Priority: Medium)

**Current:**
```
output/
├── facts.json
├── findings.json
├── investment_thesis.html
└── ...
```

**Proposed:**
```
output/
├── {deal_name}_{timestamp}/
│   ├── reports/
│   │   ├── investment_thesis.html
│   │   └── executive_summary.pdf
│   ├── data/
│   │   ├── facts.json
│   │   └── reasoning.json
│   ├── deliverables/
│   │   ├── vdr_requests.xlsx
│   │   └── work_plan.xlsx
│   └── metadata/
│       └── run_config.json
```

### Calibration & Refinement

| Item | Priority | Description |
|------|----------|-------------|
| Cost Estimate Calibration | High | Tune ranges based on actual project costs |
| Severity Calibration | High | Validate ratings against deal outcomes |
| Checklist Expansion | Medium | Add items based on team feedback |
| Prompt Refinement | Ongoing | Improve based on each deal's learnings |

**How we'll do it:**
- Track actual costs vs. estimates on closed deals
- Collect team feedback on severity accuracy
- Add new checklist items as gaps are identified
- Refine prompts based on missed patterns

### Industry-Specific Variants

| Industry | Priority | Key Additions |
|----------|----------|---------------|
| Healthcare | High | HIPAA, BAA, PHI handling, medical device IT |
| Financial Services | High | PCI-DSS, SOX, trading systems, data residency |
| Manufacturing | Medium | OT/IT convergence, SCADA, plant systems |
| Software/SaaS | Medium | CI/CD, multi-tenancy, SLA commitments |

**How we'll do it:**
- Create industry-specific prompt variants
- Add industry checklists for specialized requirements
- Calibrate severity based on industry context

### Workflow Improvements

| Item | Priority | Description |
|------|----------|-------------|
| Deal Context Templates | ✓ Complete | Deal-type aware analysis (carve-out, bolt-on, platform) |
| Incremental Analysis | ✓ Complete | Session-based, hash-based change detection |
| Output Formatting | Medium | Direct export to IC memo sections |
| Comparison Mode | Low | Side-by-side target comparison |

---

## Medium-Term (6-18 Months)

### Enhanced Analysis

| Capability | Description |
|------------|-------------|
| Historical Patterns | Learn from portfolio of completed deals |
| Vendor Intelligence | Track EOL dates, pricing trends, risk signals |
| Integration Playbooks | Standard approaches by common scenarios |
| Complexity Scoring | Quantified integration complexity metric |

### Workflow Integration

| Capability | Description |
|------------|-------------|
| VDR Tracking | Track which requests answered, update analysis |
| Deal Management Integration | Connect to existing deal pipeline tools |
| Collaboration Features | Multiple reviewers, comments, approvals |
| Report Generation | Auto-generate formatted IC memo sections |

### Quality & Confidence

| Capability | Description |
|------------|-------------|
| Confidence Scoring | How confident is the system in each finding |
| Uncertainty Flags | Explicit "needs human review" markers |
| Auto-Validation | Cross-reference findings against known data |
| Quality Metrics | Track accuracy over time by domain/type |

---

## Long-Term (18+ Months)

### Advanced Capabilities

| Capability | Description |
|------------|-------------|
| Predictive Cost Modeling | ML-based cost prediction from deal characteristics |
| Real-Time Monitoring | Alert when new VDR documents uploaded |
| Multi-Target Analysis | Portfolio company benchmarking |
| Integration Tracking | Day 1 → Day 100 progress monitoring |
| Custom Model Tuning | Fine-tune models on our domain expertise |

### Platform Evolution

| Capability | Description |
|------------|-------------|
| Web Interface | Browser-based access, no command line |
| API Access | Integrate into other deal tools |
| Multi-User Support | Team collaboration, permissions |
| Audit Trail | Full history of analyses and changes |

---

## What's NOT Planned

To keep scope focused, these are explicitly out of scope:

| Item | Reason |
|------|--------|
| Financial DD | Different domain, different expertise |
| Legal DD | Requires legal judgment, different risk profile |
| Automated Deal Decisions | Tool assists, doesn't decide |
| Public Company Analysis | Focus is M&A targets, not public research |

---

## How Priorities Are Set

Roadmap priorities based on:

1. **Team Feedback** - What would help most on actual deals?
2. **Frequency** - How often does this come up?
3. **Impact** - How much time/quality improvement?
4. **Effort** - How complex to implement?

**Your input matters.** If something would help your work, raise it.

---

## How to Influence the Roadmap

### Request a Feature
Tell the team:
- What you need
- Why it would help
- How often it would be used
- Example scenario

### Report a Gap
When the system misses something:
- What happened
- What should have happened
- How important was it

### Volunteer to Test
New features need real-world validation:
- Try new capabilities on actual deals
- Provide honest feedback
- Help calibrate and refine

---

## Version History

| Version | Date | Major Changes |
|---------|------|---------------|
| V2.3 | Feb 2026 | **In Progress** - Deal isolation (deal_id scoping), presentation reliability (dashboard fixes, Mermaid sanitization), document preprocessing (PUA removal, table-aware chunking, numeric normalization) |
| V2.2 | Jan 2026 | Inventory system upgrade (InventoryStore, deterministic parsing, content-based IDs, LLM enrichment, inventory reports) |
| V2.1 | Jan 2026 | Session management, incremental analysis, deal context (carve-out/bolt-on/platform), entity tracking (target/buyer) |
| V2.0 | Jan 2026 | Discovery/Reasoning split, model tiering, evidence chains, coverage scoring, VDR generation, synthesis |
| V1.0 | Dec 2025 | Initial release, single-phase analysis, basic outputs |

---

## Summary

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   BUILT              NEXT 6 MONTHS           6-18 MONTHS    18+ MONTHS   │
│                                                                          │
│   ✓ 6 domains        Web UI (Streamlit)      Playbooks     Predictive   │
│   ✓ Evidence chains  Benchmark integration   VDR integration  ML models │
│   ✓ Coverage scoring Spans & layers          Vendor intel   API access  │
│   ✓ VDR generation   App landscape           Comparison     Real-time   │
│   ✓ Synthesis        Output organization     Confidence     Monitoring  │
│   ✓ Entity tracking  Industry variants       Quality metrics           │
│   ✓ Org chart        Export formats          Collaboration             │
│   ✓ Sessions/incr.   Cost calibration                                   │
│   ✓ Deal context                                                         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**The foundation is solid. Now we refine based on real-world use.**

---

## Domain-Specific Enhancement Summary

| Domain | Current | Planned Enhancements |
|--------|---------|---------------------|
| **Infrastructure** | Facts, risks, costs | Cloud maturity scoring, tech debt quantification, migration modeling |
| **Network** | Connectivity inventory | Topology visualization, SD-WAN readiness, bandwidth analysis |
| **Cybersecurity** | Tool inventory, gaps | Security maturity model (NIST), compliance scoring, insurance readiness |
| **Applications** | App list, landscape table | Rationalization calculator, integration mapping, tech debt scoring |
| **Identity & Access** | IAM inventory | Zero Trust readiness, Day 1 access planning, PAM coverage analysis |
| **IT Organization** | Org chart table | Spans & layers, key person risk, retention planning, benchmark comparison |

---

*Last updated: February 2026*
