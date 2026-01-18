# Getting Started Guide
## IT Due Diligence Agent

---

## Quick Start (5 Minutes)

### Step 1: Set Up Your Environment

```bash
# Navigate to the project
cd /path/to/it-diligence-agent

# Install dependencies (first time only)
pip install -r requirements.txt

# Set your API key (first time only)
export ANTHROPIC_API_KEY="your-key-here"
```

### Step 2: Choose Your Interface

**Option A: Web UI (Recommended for most users)**
```bash
streamlit run app.py
```
Then open http://localhost:8501 in your browser. You can:
- Drag & drop documents
- Configure deal settings visually
- See progress and results in real-time

**Option B: Command Line**
Continue to Step 3 below for CLI usage.

---

## Command Line Usage

### Step 2b: Add Documents

Drop IT documents into the `input/` folder:

```
it-diligence-agent/
└── input/
    ├── IT_Overview.pdf
    ├── Security_Assessment.pdf
    ├── Network_Diagram.pdf
    └── ... (any IT-related docs)
```

**Supported formats:** PDF, TXT, MD

### Step 3: Run Analysis

```bash
python main_v2.py input/
```

You'll see progress as it runs:

```
Phase 1: Discovery
  [====] Infrastructure complete
  [====] Network complete
  [====] Cybersecurity complete
  [====] Applications complete
  [====] Identity & Access complete
  [====] Organization complete

Phase 2: Reasoning
  [====] All domains complete

Phase 3: Coverage Analysis
  [====] Complete

Phase 4: Synthesis
  [====] Complete

Phase 5: VDR Generation
  [====] Complete

Output files saved to: output/
```

### Step 4: Review Outputs

Outputs are in the `output/` folder:

```
output/
├── facts_20260115_143022.json         # Extracted facts
├── findings_20260115_143022.json      # Risks, work items
├── coverage_20260115_143022.json      # Coverage scores
├── synthesis_20260115_143022.json     # Cross-domain analysis
├── executive_summary_20260115_143022.md   # Narrative summary
├── vdr_requests_20260115_143022.json  # Follow-up requests
└── vdr_requests_20260115_143022.md    # VDR requests (readable)
```

---

## Understanding the Outputs

### Executive Summary (Start Here)

**File:** `executive_summary_*.md`

This is the human-readable narrative. Start here to get the big picture.

```markdown
# Executive Summary

## Overall Assessment
Documentation coverage: Grade B (67% of critical items)

## Key Risks
1. EOL VMware version (HIGH) - vSphere 6.7 requires upgrade
2. No documented DR testing (MEDIUM) - RTO/RPO unclear
...

## Recommended Actions
- Request DR documentation
- Clarify VMware upgrade timeline
...
```

### Coverage Report

**File:** `coverage_*.json`

Shows what's documented vs. what's missing:

```json
{
  "summary": {
    "overall_coverage_percent": 45.2,
    "critical_coverage_percent": 67.0
  },
  "domains": {
    "infrastructure": {
      "coverage_percent": 62.5,
      "missing_critical": [
        {"item": "rpo_rto", "description": "Recovery objectives"}
      ]
    }
  }
}
```

**What to look for:**
- Overall grade (A-F)
- Which domains have gaps
- Missing critical items → these become VDR requests

### VDR Requests

**File:** `vdr_requests_*.md`

Ready-to-send follow-up questions:

```markdown
## CRITICAL Priority

### VDR-001: Documentation needed: RTO/RPO values not documented
**Domain:** infrastructure | **Category:** backup_dr

Please provide documentation to address this information gap.

**Suggested Documents:**
- DR plan
- Backup policies
- RTO/RPO documentation
```

**What to do:**
- Review for relevance to this specific deal
- Add any deal-specific questions
- Remove anything already answered
- Send to target

### Findings (Risks & Work Items)

**File:** `findings_*.json`

Detailed risks and recommended work items:

```json
{
  "risks": [
    {
      "finding_id": "R-001",
      "title": "EOL VMware Version",
      "severity": "high",
      "based_on_facts": ["F-INFRA-003"],
      "mitigation": "Upgrade to vSphere 8.0",
      "reasoning": "VMware 6.7 reached EOL October 2022..."
    }
  ],
  "work_items": [
    {
      "finding_id": "WI-001",
      "title": "VMware Upgrade Project",
      "phase": "Day_100",
      "cost_estimate": "100k_to_500k",
      "owner_type": "target"
    }
  ]
}
```

**What to look for:**
- High/Critical severity risks
- Cost estimates (are they reasonable?)
- Phase assignments (Day 1 vs Day 100)
- Evidence citations (do they check out?)

### Facts (Raw Extraction)

**File:** `facts_*.json`

Everything extracted from documents with source quotes:

```json
{
  "facts": [
    {
      "fact_id": "F-INFRA-003",
      "domain": "infrastructure",
      "category": "compute",
      "item": "VMware vSphere",
      "details": {"version": "6.7", "vm_count": 340},
      "evidence": {
        "exact_quote": "VMware vSphere 6.7 hosting 340 production VMs",
        "source_section": "Infrastructure Overview"
      }
    }
  ]
}
```

**When to check this:**
- To verify a finding's evidence
- To see what was extracted from a specific domain
- To check if something was missed

---

## Session-Based Workflow (Incremental Analysis)

For ongoing deals where you receive documents over time, use sessions to avoid re-processing everything from scratch.

### Create a Session

```bash
python main_v2.py input/ --session acme_2024 --target-name "Acme Corp" --deal-type carve_out
```

**Deal types shape the analysis:**
- `carve_out` - Target separating from parent. Focus on TSA dependencies, stranded costs, standalone readiness, shared infrastructure separation
- `bolt_on` - Target integrating into buyer. Focus on platform alignment, synergies, integration complexity, consolidation opportunities

### Add More Documents Later

```bash
# Drop new documents in input/, then run:
python main_v2.py input/ --session acme_2024 --all
```

The system will:
1. Detect new/changed documents (via hash comparison)
2. Process only the new documents
3. Merge new facts with existing facts
4. Re-run reasoning on the complete fact set

### Check Session Status

```bash
python session_cli.py status acme_2024
```

Shows documents processed, facts extracted, and run history.

### Export Session Outputs

```bash
python session_cli.py export acme_2024 --output-dir output/acme_final/
```

### Session Directory Structure

```
sessions/
└── acme_2024/
    ├── state.json          # Session metadata
    ├── facts.json          # All extracted facts
    ├── reasoning.json      # All findings
    ├── documents/          # (optional) copied source docs
    └── outputs/            # Generated reports
```

---

## Common Commands

### Run Full Analysis
```bash
python main_v2.py input/
```

### Run Discovery Only (Faster, Cheaper)
```bash
python main_v2.py --discovery-only input/
```
Use this to quickly see what facts are extracted before running full reasoning.

### Run Single Domain (Testing)
```bash
python main_v2.py --domain infrastructure input/
```
Useful for testing changes to a specific domain's prompts.

### Skip VDR Generation
```bash
python main_v2.py --no-vdr input/
```

### Run from Existing Facts
```bash
python main_v2.py --from-facts output/facts_20260115.json
```
Skip discovery, just re-run reasoning on previously extracted facts.

---

## Review Checklist

After each run, check these items:

### Coverage Review
- [ ] What's the overall coverage grade?
- [ ] Which domains have the most gaps?
- [ ] Are there critical items missing that we should request?

### Risk Review
- [ ] Do the HIGH/CRITICAL risks make sense?
- [ ] Are severity ratings appropriate for this deal?
- [ ] Do the evidence citations check out?

### Work Item Review
- [ ] Are cost estimates in the right ballpark?
- [ ] Do phase assignments make sense (Day 1 vs Day 100)?
- [ ] Who should own each item (buyer vs target)?

### VDR Review
- [ ] Are the generated questions relevant?
- [ ] Anything to add based on deal context?
- [ ] Anything to remove (already answered)?

### Deal Context
- [ ] What does the system NOT know about this deal?
- [ ] Any industry-specific considerations to add?
- [ ] Integration approach implications?

---

## Troubleshooting

### "API key not found"
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### "Rate limit exceeded"
Wait a few minutes and retry. The system has automatic retry built in.

### "No documents found"
Make sure documents are in the `input/` folder and are PDF or TXT format.

### Analysis seems incomplete
- Check if documents contain relevant IT information
- Try running `--discovery-only` first to see what's extracted
- Some documents may not contain the domains being analyzed

### Cost estimate seems off
This is expected - estimates are rough ranges. Add your judgment based on deal specifics. Flag it so we can calibrate the prompts.

---

## Getting Help

- **Technical issues:** Check this guide first, then ask the team
- **Improving the system:** See CONTRIBUTION_GUIDE.md
- **Understanding outputs:** See LEADERSHIP_TECHNICAL_OVERVIEW.md

---

## Next Steps After Your First Run

1. **Review the executive summary** - Does it capture the key points?
2. **Spot-check a few findings** - Do the evidence citations match?
3. **Note what's missing** - What did you catch that the system didn't?
4. **Provide feedback** - Help us improve for the next deal

---

*Questions? See FAQ.md or ask the team.*
