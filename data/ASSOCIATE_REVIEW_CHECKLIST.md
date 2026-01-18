# Associate Review Checklist - IT Due Diligence Findings

## Purpose
This checklist guides associates reviewing AI-generated IT due diligence findings before inclusion in client deliverables. All findings require human validation before presentation to deal teams or clients.

---

## Quick Reference: Review Workflow

```
1. Run Analysis          ->  Agent generates findings
2. Export Results        ->  JSON/HTML output created
3. Associate Review      ->  THIS CHECKLIST
4. Senior Review         ->  Manager validation
5. Client Deliverable    ->  Final report
```

---

## Section 1: Pre-Review Setup

### 1.1 Access Required Materials
- [ ] Open analysis output folder (check `data/output/analysis_YYYYMMDD_HHMMSS/`)
- [ ] Load `analysis_output.json` for detailed findings
- [ ] Open `analysis_report.html` in browser for visual review
- [ ] Have source documents available for cross-reference
- [ ] Access database via `python main.py --list-runs` to identify run ID

### 1.2 Context Gathering
- [ ] Review deal context (deal name, transaction type, key concerns)
- [ ] Understand target company industry and size
- [ ] Note any specific areas the deal team flagged for attention
- [ ] Check if this is fresh or incremental analysis

---

## Section 2: Current State Inventory Review

### 2.1 Completeness Check
For each domain, verify coverage:

**Infrastructure:**
- [ ] Data center/hosting model documented
- [ ] Server environment (physical, virtual, cloud mix)
- [ ] Storage and backup systems
- [ ] End-user computing environment
- [ ] Cloud footprint (AWS, Azure, GCP presence)

**Network:**
- [ ] WAN/LAN architecture documented
- [ ] Network security (firewalls, segmentation)
- [ ] Wireless infrastructure
- [ ] Connectivity providers/redundancy

**Cybersecurity:**
- [ ] Security organization and staffing
- [ ] Security tools inventory (EDR, SIEM, etc.)
- [ ] Identity management approach
- [ ] Recent incidents or audit findings

**Applications:**
- [ ] Tier 1/critical applications listed
- [ ] ERP, CRM, HCM systems documented
- [ ] Custom applications inventory
- [ ] Legacy systems identified
- [ ] Integration patterns noted

**Identity & Access:**
- [ ] Directory services documented
- [ ] SSO/MFA coverage noted
- [ ] Privileged access management status
- [ ] Access review processes

**Organization:**
- [ ] IT staffing numbers and structure
- [ ] Key leadership identified
- [ ] Vendor relationships documented
- [ ] Outsourcing arrangements

### 2.2 Accuracy Validation
For EACH current state item:
- [ ] **Source Evidence**: Does exact quote match source document?
- [ ] **Page Reference**: Is source page number correct?
- [ ] **Interpretation**: Is the summary an accurate representation?
- [ ] **Categorization**: Is domain/category assignment correct?
- [ ] **Maturity Assessment**: Is low/medium/high rating justified?

### 2.3 Common Current State Issues
Watch for:
- [ ] Numbers misread or transposed
- [ ] Vendor names misspelled
- [ ] Version numbers incorrect
- [ ] Dates/timelines misinterpreted
- [ ] Scope confusion (company-wide vs. single site)

---

## Section 3: Risk Assessment Review

### 3.1 Risk Completeness
- [ ] All major risk categories represented:
  - [ ] Technical risks
  - [ ] Operational risks
  - [ ] Security risks
  - [ ] Compliance risks
  - [ ] Key person/staffing risks
  - [ ] Vendor/contractual risks
  - [ ] Integration risks

### 3.2 Risk Quality Checks
For EACH risk item:

**Severity Rating (critical/high/medium/low):**
- [ ] Does evidence support the assigned severity?
- [ ] Is business impact clearly explained?
- [ ] Would a senior reviewer agree with rating?

**Timeline Assessment:**
- [ ] Is the timing (immediate/near-term/medium-term) realistic?
- [ ] Does it align with deal timeline?

**Mitigation:**
- [ ] Is mitigation approach reasonable?
- [ ] Is estimated effort/cost realistic?
- [ ] Are there alternative mitigations not considered?

**Source Evidence:**
- [ ] Is risk based on stated fact or inference?
- [ ] If inference, is logic sound?
- [ ] Is confidence level appropriate?

### 3.3 Risk Red Flags
Escalate immediately if you find:
- [ ] Security breach or incident not previously disclosed
- [ ] Material compliance violations
- [ ] Key system with no DR capability
- [ ] Critical single point of failure (person or system)
- [ ] Undisclosed litigation or regulatory issues
- [ ] Expiring licenses without renewal plans

### 3.4 Common Risk Issues
Watch for:
- [ ] Severity inflation (making everything "critical")
- [ ] Severity deflation (underestimating true impact)
- [ ] Missing financial quantification
- [ ] Vague mitigation ("will address post-close")
- [ ] Risks without clear business impact

---

## Section 4: Gap Analysis Review

### 4.1 Gap Validation
For EACH gap item:
- [ ] **Is this truly unknown?** - Might the information exist elsewhere?
- [ ] **Is it material?** - Does this gap matter for the deal?
- [ ] **Category correct?** - Is it assigned to right domain?
- [ ] **Priority appropriate?** - High/medium/low matches importance?

### 4.2 Gap Response Assessment
- [ ] Are follow-up questions properly formed?
- [ ] Is the right person/team identified to answer?
- [ ] Is the question specific enough to get useful answer?

### 4.3 Common Gap Issues
Watch for:
- [ ] Gaps that could be answered from existing documents
- [ ] Duplicate gaps phrased differently
- [ ] Overly broad gaps ("need more info on IT")
- [ ] Gaps already addressed in incremental documents

---

## Section 5: Assumption Review

### 5.1 Assumption Validation
For EACH assumption:
- [ ] **Is assumption stated?** - The uncertain item is clear
- [ ] **Is implication explained?** - Why this matters
- [ ] **Is basis documented?** - What led to this assumption
- [ ] **Is confidence level appropriate?** (high/medium/low)

### 5.2 Assumption Risk Assessment
- [ ] What happens if assumption is wrong?
- [ ] Should this be converted to a gap/question?
- [ ] Is there a way to validate before close?

### 5.3 Common Assumption Issues
Watch for:
- [ ] Assumptions stated as facts
- [ ] Unsupported confidence levels
- [ ] Missing "if wrong" impact analysis
- [ ] Circular reasoning

---

## Section 6: Work Items & Recommendations

### 6.1 Work Item Review
For EACH work item:
- [ ] **Actionable?** - Can someone actually do this?
- [ ] **Specific?** - Clear scope and deliverable?
- [ ] **Owned?** - Clear responsibility assigned?
- [ ] **Prioritized?** - Pre-close vs. post-close appropriate?
- [ ] **Linked?** - Connected to underlying risk/gap?

### 6.2 Recommendation Review
For EACH recommendation:
- [ ] **Evidence-based?** - Supported by findings?
- [ ] **Realistic?** - Achievable given constraints?
- [ ] **Prioritized?** - Urgency level appropriate?
- [ ] **Quantified?** - Effort/cost estimated where possible?

### 6.3 Integration Considerations
- [ ] Are Day 1 requirements clearly identified?
- [ ] Are TSA needs flagged appropriately?
- [ ] Are integration blockers called out?
- [ ] Are synergy opportunities noted where relevant?

---

## Section 7: Cross-Domain Consistency

### 7.1 Internal Consistency Checks
- [ ] Do staffing numbers match across domains?
- [ ] Are application names spelled consistently?
- [ ] Do vendor references align?
- [ ] Are dates/timelines consistent?

### 7.2 Contradiction Detection
- [ ] Flag any contradictory statements
- [ ] Note where findings conflict with source documents
- [ ] Identify logical inconsistencies in risk assessments

---

## Section 8: Output Quality

### 8.1 Format and Presentation
- [ ] IDs are sequential and formatted correctly
- [ ] No duplicate findings
- [ ] No empty or placeholder content
- [ ] Professional language throughout

### 8.2 Client-Ready Assessment
- [ ] Would you be comfortable presenting these findings?
- [ ] Are there findings that need rephrasing?
- [ ] Are sensitivity concerns addressed?

---

## Section 9: Documentation

### 9.1 Required Documentation
- [ ] Note all corrections made
- [ ] Document additions based on reviewer judgment
- [ ] Flag items for senior review
- [ ] Record time spent on review

### 9.2 Escalation Triggers
Escalate to senior reviewer if:
- [ ] Material errors in critical findings
- [ ] Deal-breaking risks identified
- [ ] Significant uncertainty in key areas
- [ ] Source evidence quality concerns

---

## Section 10: Sign-Off

### 10.1 Reviewer Attestation
```
I have reviewed the AI-generated findings for this analysis run and:

[ ] Verified source evidence accuracy
[ ] Validated risk severity ratings
[ ] Confirmed gap materiality
[ ] Checked assumption reasonableness
[ ] Reviewed work item actionability
[ ] Confirmed no contradictions exist
[ ] Flagged items requiring escalation

Reviewer: ________________________
Date: ____________________________
Run ID: __________________________
Time Spent: ______________________
```

### 10.2 Issues Log
| Finding ID | Issue Type | Description | Resolution | Status |
|------------|------------|-------------|------------|--------|
| | | | | |
| | | | | |
| | | | | |

---

## Appendix A: Severity Rating Guide

| Rating | Criteria | Examples |
|--------|----------|----------|
| **Critical** | Deal-breaking; immediate action required; >$1M impact | Security breach, key system failure risk |
| **High** | Material concern; address pre-close; $250K-$1M impact | Single points of failure, compliance gaps |
| **Medium** | Should address within 6 months; $50K-$250K impact | Technical debt, process improvements |
| **Low** | Nice to have; <$50K impact | Minor enhancements, documentation |

---

## Appendix B: Domain-Specific Focus Areas

### Infrastructure Red Flags
- Servers/storage past end-of-life
- Data center lease expiration within 2 years
- No disaster recovery capability
- Aging UPS/cooling infrastructure

### Network Red Flags
- Flat network (no segmentation)
- End-of-support network equipment
- No redundant WAN links
- No network monitoring

### Cybersecurity Red Flags
- No EDR/SIEM
- MFA not enforced
- No vulnerability management
- Recent breaches
- No security organization

### Applications Red Flags
- Mission-critical legacy systems
- Single maintainer dependencies
- No source code access
- End-of-support platforms
- No DR for critical apps

### Identity Red Flags
- No centralized identity
- Shared accounts
- No privileged access management
- No access reviews
- Weak password policies

### Organization Red Flags
- Key person dependencies
- High turnover indicators
- Understaffing
- No documentation culture
- Vendor concentration

---

## Appendix C: Quick Validation Commands

```bash
# List all analysis runs
python main.py --list-runs

# Show questions/gaps for a run
python main.py --questions RUN-XXXXXX

# Show assumptions needing validation
python main.py --assumptions RUN-XXXXXX

# Compare two analysis runs
python main.py --compare RUN-XXX RUN-YYY
```

---

*Document Version: 1.0*
*Created: January 2026*
*Point 115 - 115PP Implementation Plan*
