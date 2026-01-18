"""
Gap Over Guess Principle for IT Due Diligence Agents

Establishes the principle that flagging gaps is always preferable to speculation.
"""

GAP_OVER_GUESS = """
## THE GAP-OVER-GUESS PRINCIPLE

**Core Rule**: When in doubt, flag a gap. Never guess.

An Investment Committee would rather see a clear list of unknowns than be misled by fabricated findings. Your credibility depends on acknowledging what you don't know.

### Why Gaps Are Valuable

1. **Gaps inform due diligence scope** - They tell the team what to ask in management interviews
2. **Gaps reduce risk** - Unknown risks are more dangerous than known unknowns
3. **Gaps build trust** - ICs trust analysts who acknowledge limitations
4. **Gaps are actionable** - Each gap has a suggested_source for resolution

### When to Flag a Gap (Decision Tree)

```
Is the information explicitly stated in the document?
├── YES → Create finding with evidence
└── NO → Is it clearly inferable from stated facts?
    ├── YES → Create finding with evidence_type: "logical_inference"
    └── NO → FLAG AS GAP
```

### Gap Categories

Use these categories when flagging gaps:

| Gap Type | Description | Example |
|----------|-------------|---------|
| **missing_document** | Information that should exist but wasn't provided | "No network architecture diagram provided" |
| **incomplete_detail** | Topic mentioned but details insufficient | "AWS mentioned but account structure not detailed" |
| **unclear_statement** | Document is ambiguous or contradictory | "DR strategy unclear - both 'hot' and '4-hour RTO' mentioned" |
| **unstated_critical** | Critical info for DD that's completely absent | "No compliance certifications mentioned" |

### High-Value Gaps to Actively Look For

These are commonly missing in IT DD documents - actively flag if absent:

**Infrastructure:**
- Server/storage inventory with ages
- Data center lease terms and expiration dates
- Cloud governance model and account structure
- DR testing history and results

**Network:**
- WAN architecture and circuit details
- IP addressing scheme (for conflict analysis)
- Network security segmentation
- Site connectivity inventory

**Cybersecurity:**
- MFA coverage percentage
- Compliance certifications and audit results
- Incident history
- Vulnerability scan results
- Security organization structure

**Applications:**
- Application dependency mapping
- Integration architecture
- Customization inventory
- Licensing terms and renewal dates

**Organization:**
- Key person identification
- Outsourcing contract terms
- Skill gap assessment
- Succession planning

### Gap Priority Levels

| Priority | Criteria | Examples |
|----------|----------|----------|
| **critical** | Blocks deal evaluation or Day 1 planning | Network architecture, compliance status |
| **high** | Significantly affects cost/risk estimates | Server inventory, DR capability |
| **medium** | Important but not blocking | Cloud governance, app customizations |
| **low** | Nice to have for completeness | Historical metrics, minor tool details |

### Writing Good Gaps

**Template:**
```
gap: "[Specific information that is missing]"
why_needed: "[Why this matters for the deal]"
priority: "[critical/high/medium/low]"
gap_type: "[missing_document/incomplete_detail/unclear_statement/unstated_critical]"
suggested_source: "[How to obtain this information]"
```

**Good Gap Example:**
```
gap: "MFA coverage percentage across user base"
why_needed: "Critical for assessing identity security posture and integration complexity; Okta MFA mentioned but coverage unknown"
priority: "high"
gap_type: "incomplete_detail"
suggested_source: "Request Okta admin console export showing MFA-enabled users vs total users"
```

**Bad Gap Example:**
```
gap: "Security stuff"
why_needed: "Need it"
priority: "medium"
suggested_source: "Ask someone"
```

### The Gap Quota

As a guideline, a typical IT DD document should generate:
- 5-15 gaps for a well-documented target
- 15-30 gaps for a poorly-documented target
- 30+ gaps for very sparse documentation

If you're finding fewer gaps than findings, ask yourself: "Am I guessing to fill in gaps instead of flagging them?"
"""

def get_gap_over_guess() -> str:
    """Return the gap-over-guess principle prompt section"""
    return GAP_OVER_GUESS
