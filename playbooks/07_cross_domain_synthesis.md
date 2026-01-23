# Cross-Domain Synthesis Playlist

## Pre-Flight Considerations

**What makes Synthesis different from domain reviews:**

1. **This is where the DD story comes together** - Individual domains give you facts. Synthesis gives you the narrative: "Is this a clean IT environment, a manageable fixer-upper, or a troubled situation requiring significant investment?"

2. **Risks don't exist in isolation** - A finding in applications (SAP ECC approaching EOL) connects to infrastructure (servers at capacity), IT org (skills gap for S/4HANA), and budget (no capital set aside). Synthesis surfaces these connections.

3. **Standalone viability is the threshold question** - Can this company operate independently if the deal closes tomorrow? If not, what's the minimum investment to get there? This is often the most important finding.

4. **Integration complexity drives deal timeline and cost** - Not just "can we integrate?" but "how hard will it be?" This affects purchase price, earnout structures, and integration budgets.

5. **The management session follows** - Your synthesis should generate pointed questions for the management session. What did documents NOT tell you that you need confirmed live?

**What we learned building the bespoke tool:**

- The Four Lenses framework works well for synthesis: (1) Current State, (2) Risks, (3) Strategic Considerations, (4) Integration Actions
- Consolidating follow-up questions across domains and prioritizing them is essential - you can't ask 50 questions in a 2-hour session
- Cost estimation, even rough ranges, helps stakeholders understand the investment required
- The executive summary is what partners and deal team read - make it count

---

## Phase 1: Consolidate Domain Findings

### Prompt 1.1 - Application Landscape Summary
```
Based on the Applications Landscape review, summarize:

1. Total applications documented: X
2. Key systems by category:
   - ERP: [list]
   - HCM/Payroll: [list]
   - CRM: [list]
   - Core business-specific: [list]

3. Hosting profile:
   - On-premise: X%
   - SaaS: X%
   - Cloud-hosted: X%

4. Application health:
   - EOL/approaching EOL: [list with dates]
   - Critical technical debt: [list]
   - Key customizations: [list]

5. Top 3 application risks:
   - Risk 1
   - Risk 2
   - Risk 3

6. Critical application gaps (business capability not covered):
   - [list]

7. Open questions for management:
   - [prioritized list]
```

### Prompt 1.2 - Infrastructure and Network Summary
```
Based on Infrastructure and Network reviews, summarize:

1. Infrastructure profile:
   - Data center footprint (owned, colo, cloud)
   - Cloud maturity level
   - Compute/storage environment

2. Network architecture:
   - Site count and distribution
   - WAN technology (MPLS, SD-WAN, VPN)
   - Key connectivity considerations

3. Infrastructure health:
   - EOL infrastructure: [list]
   - DR/BC status
   - Capacity concerns

4. Top 3 infrastructure risks:
   - Risk 1
   - Risk 2
   - Risk 3

5. Integration considerations:
   - IP addressing overlap risk
   - Network connectivity requirements
   - Data center consolidation scenarios

6. Open questions for management:
   - [prioritized list]
```

### Prompt 1.3 - Security Posture Summary
```
Based on Cybersecurity and Identity reviews, summarize:

1. Security program maturity: [1-5 rating]

2. Critical security controls status:
   - MFA coverage: X% all users, X% privileged
   - EDR coverage: X%
   - Privileged access management: [status]
   - Vulnerability management: [status]

3. Compliance posture:
   - Certifications: [list]
   - Gaps: [list]

4. Top 3 security risks:
   - Risk 1
   - Risk 2
   - Risk 3

5. Identity integration considerations:
   - IdP alignment with buyer
   - Federation approach
   - Day 1 access requirements

6. Open questions for management:
   - [prioritized list]
```

### Prompt 1.4 - IT Organization Summary
```
Based on IT Organization review, summarize:

1. IT team profile:
   - Headcount: X
   - IT ratio: 1:Y
   - Structure overview

2. Key person risks:
   - [list critical individuals and what they own]

3. Operating model:
   - Maturity level
   - Outsourcing dependencies
   - Process maturity

4. Budget and spend:
   - IT budget: $X
   - IT spend as % of revenue
   - Significant contracts

5. Top 3 organization risks:
   - Risk 1
   - Risk 2
   - Risk 3

6. Retention considerations:
   - [who needs to be retained]

7. Open questions for management:
   - [prioritized list]
```

---

## Phase 2: Four Lenses Synthesis

### Prompt 2.1 - Lens 1: Current State Assessment
```
Provide a current state assessment of the IT environment:

For each domain, rate maturity (Low/Medium/High) and summarize key characteristics:

1. Applications:
   - Maturity: [rating]
   - Key characteristics: [bullet points]

2. Infrastructure:
   - Maturity: [rating]
   - Key characteristics: [bullet points]

3. Network:
   - Maturity: [rating]
   - Key characteristics: [bullet points]

4. Security:
   - Maturity: [rating]
   - Key characteristics: [bullet points]

5. Identity & Access:
   - Maturity: [rating]
   - Key characteristics: [bullet points]

6. IT Organization:
   - Maturity: [rating]
   - Key characteristics: [bullet points]

Overall IT maturity: Low | Medium | High

Standalone viability assessment:
- Can this company operate independently? (Yes / With constraints / No)
- What are the constraints or blockers?
```

### Prompt 2.2 - Lens 2: Risk Synthesis
```
Consolidate all risks from domain reviews and synthesize:

1. Critical Risks (must address before or immediately after close):
   For each:
   - Risk description
   - Domain (Apps, Infra, Security, etc.)
   - Business impact
   - Mitigation approach
   - Estimated cost to remediate

2. High Risks (should address within first 90 days):
   [Same format]

3. Medium Risks (plan during first year):
   [Same format]

Top 5 Overall Risks (ranked):
1. [Risk + one-line summary]
2. [Risk + one-line summary]
3. [Risk + one-line summary]
4. [Risk + one-line summary]
5. [Risk + one-line summary]

Risk-adjusted considerations for deal:
- Do any risks warrant purchase price adjustment?
- Should any risks be covered by escrow or indemnity?
- Are there walk-away risks?
```

### Prompt 2.3 - Lens 3: Strategic Considerations
```
Identify strategic IT considerations for the deal:

1. Integration approach considerations:
   - Quick integration vs. gradual transition
   - Lift and shift vs. transformation
   - Retain systems vs. migrate to buyer platforms

2. Synergy opportunities:
   - License consolidation (same vendors)
   - Headcount efficiencies
   - Infrastructure consolidation
   - Vendor consolidation

3. Investment requirements:
   - Deferred maintenance / catch-up spend
   - Modernization investments required
   - Security remediation
   - Integration costs

4. Long-term IT strategy implications:
   - Technology direction alignment
   - Cloud strategy alignment
   - Security posture alignment
   - IT operating model alignment

5. Deal structure considerations:
   - Pre-close requirements
   - Day 1 readiness activities
   - Transition services agreement (TSA) needs
   - Earnout protection considerations
```

### Prompt 2.4 - Lens 4: Integration Actions and Workstreams
```
Define key integration workstreams and actions:

**Pre-Close (if applicable):**
- [ ] [Action item]
- [ ] [Action item]

**Day 1 Requirements:**
- [ ] [Action item - what must be ready on close]
- [ ] [Action item]

**First 30 Days:**
- [ ] [Action item]
- [ ] [Action item]

**First 90 Days:**
- [ ] [Action item]
- [ ] [Action item]

**First Year:**
- [ ] [Action item]
- [ ] [Action item]

**Key Integration Workstreams:**
1. Network Integration
   - Activities: [list]
   - Timeline: [X months]
   - Estimated effort/cost: [range]

2. Identity Integration
   - Activities: [list]
   - Timeline: [X months]
   - Estimated effort/cost: [range]

3. Application Integration/Migration
   - Activities: [list]
   - Timeline: [X months]
   - Estimated effort/cost: [range]

4. Security Alignment
   - Activities: [list]
   - Timeline: [X months]
   - Estimated effort/cost: [range]

5. IT Organization Integration
   - Activities: [list]
   - Timeline: [X months]
   - Considerations: [retention, reorg, etc.]
```

---

## Phase 3: Cost and Complexity Assessment

### Prompt 3.1 - Integration Cost Estimation
```
Estimate integration costs (ranges acceptable):

1. One-time integration costs:
   - Network integration: $X - $Y
   - Identity integration: $X - $Y
   - Application migration/integration: $X - $Y
   - Security remediation: $X - $Y
   - Professional services: $X - $Y
   - Total one-time: $X - $Y

2. Ongoing cost changes:
   - License consolidation savings: ($X)/year
   - Headcount changes: +/- X FTEs
   - Infrastructure changes: $X/year impact
   - Net ongoing impact: $X/year

3. Deferred spend / catch-up costs:
   - EOL system upgrades: $X - $Y
   - Infrastructure refresh: $X - $Y
   - Security investments: $X - $Y
   - Total catch-up: $X - $Y

4. Key assumptions:
   - [List assumptions behind estimates]

5. Cost risks:
   - [What could make it higher]
```

### Prompt 3.2 - Integration Complexity Score
```
Rate overall integration complexity:

Score each factor (1-5, where 5 is most complex):

1. Application landscape complexity: X/5
   - Reasoning: [why this score]

2. Infrastructure compatibility: X/5
   - Reasoning: [why this score]

3. Network integration complexity: X/5
   - Reasoning: [why this score]

4. Security posture gap: X/5
   - Reasoning: [why this score]

5. Identity integration complexity: X/5
   - Reasoning: [why this score]

6. IT organization alignment: X/5
   - Reasoning: [why this score]

**Overall Integration Complexity Score: X/30**

Interpretation:
- 6-12: Low complexity - straightforward integration
- 13-18: Moderate complexity - manageable with planning
- 19-24: High complexity - significant effort required
- 25-30: Very high complexity - major program required

Comparative benchmark:
- How does this compare to typical IT integrations?
- What's the most complex aspect?
```

---

## Phase 4: Executive Deliverables

### Prompt 4.1 - Executive Summary (1 page)
```
Generate a one-page executive summary:

**IT Due Diligence Summary: [Target Company Name]**

**Overall Assessment:** [One sentence - Clean / Manageable / Concerning / Problematic]

**Key Findings:**
1. [Most important finding]
2. [Second most important]
3. [Third most important]

**Critical Risks:**
- [Risk 1]: [Impact and mitigation]
- [Risk 2]: [Impact and mitigation]

**Investment Required:**
- One-time integration: $X - $Y
- Ongoing changes: $X/year
- Deferred catch-up: $X - $Y

**Integration Complexity:** [Low / Moderate / High / Very High]
- Key driver: [What makes it this level]

**Standalone Viability:** [Yes / With constraints / No]
- Key constraint: [If applicable]

**Recommendations:**
1. [Top recommendation]
2. [Second recommendation]
3. [Third recommendation]

**Critical Questions for Management Session:**
1. [Most important question]
2. [Second most important]
3. [Third most important]
```

### Prompt 4.2 - Management Session Questions
```
Consolidate and prioritize questions for management session:

**Must Ask (Critical gaps affecting deal):**
1. [Question] - Why it matters: [reason]
2. [Question] - Why it matters: [reason]
3. [Question] - Why it matters: [reason]

**Should Ask (Important for planning):**
1. [Question] - Why it matters: [reason]
2. [Question] - Why it matters: [reason]
3. [Question] - Why it matters: [reason]
4. [Question] - Why it matters: [reason]
5. [Question] - Why it matters: [reason]

**If Time Permits (Nice to have):**
1. [Question]
2. [Question]
3. [Question]

**Questions by Topic (for session organization):**

IT Leadership & Strategy:
- [questions]

Applications:
- [questions]

Infrastructure & Operations:
- [questions]

Security & Compliance:
- [questions]

Organization & People:
- [questions]
```

### Prompt 4.3 - Final Risk Register
```
Produce final consolidated risk register:

| ID | Risk | Domain | Severity | Impact | Likelihood | Mitigation | Owner | Cost Est. |
|----|------|--------|----------|--------|------------|------------|-------|-----------|
| R1 | [Risk description] | [Domain] | Critical/High/Med/Low | [Business impact] | High/Med/Low | [Mitigation] | [Suggested owner] | $X |
| R2 | ... | ... | ... | ... | ... | ... | ... | ... |

Summary:
- Critical risks: X
- High risks: X
- Medium risks: X
- Low risks: X

Risks requiring pre-close action: [list]
Risks requiring Day 1 action: [list]
```

---

## Output Checklist

After running this playlist, you should have:
- [ ] Domain summary for each area (Apps, Infra, Network, Security, IAM, IT Org)
- [ ] Four Lenses analysis (Current State, Risks, Strategy, Integration Actions)
- [ ] Cost estimation with assumptions
- [ ] Integration complexity score
- [ ] One-page executive summary
- [ ] Prioritized management session questions
- [ ] Final consolidated risk register
- [ ] Integration workstream definition with timelines

---

## Recommended Document Structure

Final IT DD report should be organized as:

1. **Executive Summary** (1 page)
2. **Methodology** (brief description of approach)
3. **Current State by Domain** (Applications, Infrastructure, Network, Security, IAM, IT Org)
4. **Key Findings and Risks** (consolidated, prioritized)
5. **Integration Considerations** (complexity, approach, timeline)
6. **Cost Implications** (one-time, ongoing, catch-up)
7. **Recommendations** (prioritized action items)
8. **Appendices:**
   - A: Application Inventory
   - B: Infrastructure Inventory
   - C: Risk Register
   - D: Follow-up Questions
   - E: Contract Summary
