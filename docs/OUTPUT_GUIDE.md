# IT Due Diligence Agent - Output Guide

This document explains all the outputs generated when running an IT due diligence analysis.

---

## Quick Reference

| Output | Format | Purpose | Audience |
|--------|--------|---------|----------|
| [Investment Thesis](#investment-thesis-presentation) | HTML | PE buyer presentation | Deal Team / IC |
| [IT DD Report](#it-dd-report) | HTML | Full interactive analysis | DD Team |
| [Executive Summary](#executive-summary) | Markdown | IC-ready summary | Leadership |
| [VDR Requests](#vdr-requests) | Markdown + JSON | Follow-up document requests | Deal Team |
| [Findings Export](#excel-export) | Excel | Sortable/filterable data | Analysts |
| [Raw Data](#json-data-files) | JSON | Machine-readable data | Technical |

---

## Output Directory Structure

After running the analysis, outputs are saved to the `output/` directory:

```
output/
├── facts_{timestamp}.json              # Extracted inventory (discovery phase)
├── findings_{timestamp}.json           # Risks, work items, recommendations
├── coverage_{timestamp}.json           # Documentation coverage scores
├── synthesis_{timestamp}.json          # Cross-domain analysis
├── executive_summary_{timestamp}.md    # IC-ready summary
├── vdr_requests_{timestamp}.json       # VDR requests (JSON)
├── vdr_requests_{timestamp}.md         # VDR requests (Markdown)
├── narratives_{timestamp}.json         # LLM-generated narratives (with --narrative)
├── it_dd_report_{timestamp}.html       # Full interactive report
└── investment_thesis_{timestamp}.html  # PE buyer presentation
```

---

## HTML Reports

### Investment Thesis Presentation

**File**: `investment_thesis_{timestamp}.html`

**Purpose**: A slide-deck style presentation for PE buyers. This is your IC-ready deliverable.

**What's Included**:
- **Executive Summary** - Key metrics, top risks, total cost range
- **Domain Slides** (6 slides) - One per domain with:
  - "So What" headline - The key implication in one sentence
  - Key Considerations - 3-5 bullet points with specifics
  - The Story - 2-3 paragraph candid narrative
  - Cost Impact - Domain-specific cost range
- **Cost Summary** - Aggregated by phase, domain, and owner
- **Work Plan** - Day 1, Day 100, Post-100 breakdown
- **Open Questions** - VDR items that need resolution

**Generation Modes**:

| Mode | Command | Quality | Speed |
|------|---------|---------|-------|
| Template-based | Default | Good | Fast |
| LLM-generated | `--narrative` | Best | Slower |

The `--narrative` flag runs 6 parallel narrative agents (Sonnet) plus a cost synthesis agent to generate partner-level storytelling content.

**Example Slide**:
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

---

### IT DD Report

**File**: `it_dd_report_{timestamp}.html`

**Purpose**: Full interactive report for the DD team. Includes all findings with filtering and drill-down.

**Features**:
- **Filtering** by domain, severity, category, phase
- **Evidence chains** - Click any finding to see supporting facts
- **Cost breakdown** - Interactive cost tables
- **Export options** - Print to PDF

**Sections**:
1. Summary dashboard with key metrics
2. Risks by severity (critical → low)
3. Gaps and missing information
4. Work items by phase
5. Strategic considerations
6. Recommendations

---

## Markdown Documents

### Executive Summary

**File**: `executive_summary_{timestamp}.md`

**Purpose**: IC-ready summary that can be dropped into a deal memo.

**Contents**:
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
- Grade: B

## Cost Estimates
- Total Range: $1,250,000 - $3,500,000

### By Phase:
  - Day 1: $125,000 - $350,000 (5 items)
  - Day 100: $875,000 - $2,150,000 (12 items)
  - Post 100: $250,000 - $1,000,000 (6 items)

### By Owner:
  - Buyer: $200,000 - $500,000
  - Target: $750,000 - $2,000,000

## Top Risks
1. No PAM solution - privileged access uncontrolled
2. EOL VMware 6.7 - needs immediate upgrade
3. Dual-ERP complexity - rationalization needed
```

---

### VDR Requests

**Files**:
- `vdr_requests_{timestamp}.md` (human-readable)
- `vdr_requests_{timestamp}.json` (machine-readable)

**Purpose**: Prioritized list of documents to request from the target in the Virtual Data Room.

**Contents**:
```markdown
## CRITICAL Priority (12 requests)

### VDR-001: Documentation needed: RTO/RPO values not documented
**Domain:** infrastructure | **Category:** backup_dr
**Source:** Gap G-INFRA-001

**Suggested Documents:**
- DR plan
- Backup policies
- DR test results
- RTO/RPO documentation

---

### VDR-002: Network architecture diagrams missing
**Domain:** network | **Category:** wan
**Source:** Coverage gap

**Suggested Documents:**
- Network topology diagram
- VLAN documentation
- Firewall rules export
```

**JSON Structure**:
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
    "DR test results"
  ]
}
```

---

## Excel Export

**File**: `findings_{run_id}_{timestamp}.xlsx`

**Purpose**: Client-ready Excel workbook with all findings in sortable/filterable format.

**Generation**: Run from the V1 pipeline or use the excel export utility:
```bash
python tools/excel_export.py
```

**Worksheets**:

| Sheet | Contents | Key Columns |
|-------|----------|-------------|
| **Summary** | Overview dashboard | Counts, severity breakdown, phase breakdown |
| **Risks** | All identified risks | Domain, Description, Severity, Likelihood, Mitigation, Cost Impact |
| **Gaps** | Missing information | Domain, Gap Description, Priority, Suggested Source |
| **Work Items** | Integration tasks | Title, Phase, Effort, Cost Estimate, Dependencies |
| **Recommendations** | Strategic guidance | Recommendation, Rationale, Priority, Timing |
| **Current State** | IT inventory | Domain, Category, Item, Status, Maturity |
| **Assumptions** | Assumptions made | Assumption, Basis, Confidence, Validation Needed |

**Features**:
- Conditional formatting (severity/priority colors)
- Frozen header rows
- Auto-filter enabled
- Professional styling

---

## JSON Data Files

These are the machine-readable outputs for programmatic access or further processing.

### facts_{timestamp}.json

**Purpose**: Complete IT inventory extracted during discovery phase.

**Structure**:
```json
{
  "facts": [
    {
      "fact_id": "F-INFRA-001",
      "domain": "infrastructure",
      "category": "hosting",
      "item": "Primary Data Center",
      "details": {
        "vendor": "Equinix",
        "location": "Chicago",
        "tier": "III"
      },
      "evidence": {
        "exact_quote": "The company operates from Equinix CH3...",
        "source_section": "IT Overview"
      },
      "status": "documented"
    }
  ],
  "gaps": [
    {
      "gap_id": "G-INFRA-001",
      "domain": "infrastructure",
      "category": "backup_dr",
      "missing_item": "RTO/RPO values",
      "why_critical": "Cannot assess DR capability without recovery targets",
      "priority": "high"
    }
  ]
}
```

---

### findings_{timestamp}.json

**Purpose**: All analysis results from the reasoning phase.

**Contents**:
- Risks (with severity, mitigation, fact citations)
- Strategic Considerations
- Work Items (with cost estimates, phase, owner)
- Recommendations

**Structure**:
```json
{
  "risks": [
    {
      "finding_id": "R-001",
      "domain": "infrastructure",
      "title": "EOL VMware Version",
      "description": "VMware 6.7 reached end of life October 2022",
      "severity": "high",
      "based_on_facts": ["F-INFRA-003"],
      "mitigation": "Upgrade to VMware 8.0",
      "confidence": "high"
    }
  ],
  "work_items": [
    {
      "finding_id": "WI-001",
      "domain": "infrastructure",
      "title": "VMware Upgrade Project",
      "phase": "Day_100",
      "cost_estimate": "100k_to_500k",
      "owner_type": "target",
      "triggered_by": ["F-INFRA-003"],
      "triggered_by_risks": ["R-001"]
    }
  ]
}
```

---

### coverage_{timestamp}.json

**Purpose**: Documentation coverage analysis and scoring.

**Structure**:
```json
{
  "overall_score": 78.5,
  "overall_grade": "B",
  "critical_coverage": 92.0,
  "missing_critical_count": 3,
  "domains": {
    "infrastructure": {
      "score": 85.0,
      "critical_score": 100.0,
      "documented": ["hosting", "compute", "storage"],
      "missing": ["tooling"],
      "critical_missing": []
    }
  }
}
```

---

### synthesis_{timestamp}.json

**Purpose**: Cross-domain analysis and consistency checks.

**Contents**:
- Related findings grouped by theme
- Cross-domain dependencies
- Cost aggregation summaries
- Risk correlation analysis

---

### narratives_{timestamp}.json

**Purpose**: LLM-generated narrative content (only with `--narrative` flag).

**Structure**:
```json
{
  "domain_narratives": {
    "infrastructure": {
      "domain": "infrastructure",
      "so_what": "Hybrid cloud footprint with aging on-prem...",
      "considerations": [
        "Two colo facilities (Atlanta primary, NYC secondary)",
        "47 AWS accounts, $6.7M annual spend"
      ],
      "narrative": "The target started on-prem and has been...",
      "cost_summary": "$1.2M - $3.5M, primarily in Day 100 work",
      "key_facts": ["F-INFRA-001", "F-INFRA-003"],
      "sources": ["IT Inventory.xlsx", "Cloud Cost Report"],
      "confidence": "high"
    }
  },
  "cost_narrative": {
    "executive_summary": "The integration will cost between...",
    "key_drivers": ["PAM implementation ($250K-$500K)"],
    "assumptions": ["Target IT team stays through Day 100"],
    "risks_to_estimates": ["Colo exit penalties unknown"]
  }
}
```

---

## Database Persistence

**File**: `data/diligence.db`

**Purpose**: SQLite database storing historical analysis data.

**Tables**:
- `runs` - Analysis run metadata
- `risks` - All risks across runs
- `gaps` - Information gaps
- `work_items` - Integration tasks
- `recommendations` - Strategic recommendations
- `inventory_items` - Current state facts
- `assumptions` - Analysis assumptions

**Usage**:
```python
from storage import Database, Repository

db = Database()
repo = Repository(db)

# Get latest run
latest = repo.get_latest_run()

# Query risks
risks = repo.get_risks_by_severity(latest.run_id, 'critical')
```

---

## Output by Command

| Command | Outputs Generated |
|---------|-------------------|
| `python main_v2.py data/input/ --all` | facts, findings, coverage, synthesis, vdr_requests, executive_summary, it_dd_report, investment_thesis |
| `python main_v2.py data/input/ --all --narrative` | All above + narratives (LLM-generated investment thesis) |
| `python main_v2.py --discovery-only` | facts only |
| `python main_v2.py --from-facts facts.json` | findings, coverage, synthesis, etc. (skips discovery) |
| `python main_v2.py --no-vdr` | All except vdr_requests |
| `python main.py` (V1) | analysis_report.html, individual JSON files, Excel export |

---

## Tips for Using Outputs

### For Investment Committee Presentation
Use `investment_thesis_{timestamp}.html` - it's designed as a slide deck.

### For Deal Team Deep Dive
Use `it_dd_report_{timestamp}.html` - full filtering and drill-down.

### For VDR Follow-up
Use `vdr_requests_{timestamp}.md` - copy/paste into VDR request tracker.

### For Financial Modeling
Use `findings_{timestamp}.json` and extract:
- `work_items[].cost_estimate` for integration budget
- Aggregate by `phase` and `owner_type`

### For Sharing with Client (Excel)
Run the Excel export for a professional multi-worksheet workbook.

---

*Last Updated: January 15, 2026*
