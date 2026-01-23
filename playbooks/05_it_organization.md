# IT Organization Review Playlist

## Pre-Flight Considerations

**What makes IT Organization different from other IT domains:**

1. **People are the hardest integration challenge** - Systems can be migrated on a schedule. People leave, resist change, or become flight risks. IT org assessment is about retention, capability, and change readiness.

2. **Key person risk is real** - In many targets, 1-2 people hold all the knowledge. If they leave, you lose the ability to operate critical systems. Identify these people early.

3. **Culture and operating model matter** - A scrappy, ticket-avoiding IT team integrating into a process-heavy, ITIL-driven buyer (or vice versa) creates friction. Understand the operating model fit.

4. **Cost benchmarking is expected** - IT headcount per employee, IT spend as % of revenue - these are standard M&A metrics. Significant deviation signals either underinvestment or inefficiency.

5. **Outsourcing and managed services complicate the picture** - "We have 5 IT people" might mean "we have 5 IT people plus 20 contractors plus an MSP." Get the full picture.

6. **Skills gaps emerge post-close** - The target's IT team may not have skills the buyer needs (cloud, security, modern development). This isn't a risk per se, but it's a planning input.

**What we learned building the bespoke tool:**

- Org charts are often outdated. Ask for a current one or have IT leadership draw it in the management session.
- "IT" may be distributed - developers in Product, data people in Finance, shadow IT everywhere. Get the full picture.
- Tenure distribution matters - a team of 10-year veterans has institutional knowledge but may resist change; a team of recent hires might lack context.
- The IT leader's relationship with the business is revealing - are they at the leadership table or viewed as a cost center?

---

## Phase 1: IT Team Structure

### Prompt 1.1 - IT Organization Overview
```
Document the IT organization structure:

1. IT leadership:
   - IT leader title and name (CIO, VP IT, IT Director, IT Manager)
   - Reporting line (CEO, CFO, COO, other)
   - Tenure in role
   - IT at the executive/leadership table? (Yes/No)

2. IT team size and structure:
   - Total IT headcount (employees)
   - IT headcount ratio (IT FTEs / Total company employees)
   - Organization structure (functional, regional, product-aligned)
   - Major teams or functions

3. IT sub-teams (identify each):
   - Infrastructure / Operations
   - Applications / Development
   - Security
   - Help Desk / Support
   - Data / Analytics
   - Project Management / PMO
   - Other

For each sub-team:
- Name | Headcount | Leader | Key responsibilities

4. Geographic distribution:
   - Where is IT located?
   - Onshore vs. offshore split
   - Remote work prevalence

Format org summary as: Total IT FTEs: X | IT Ratio: 1:Y | Teams: Z
```

### Prompt 1.2 - IT Staffing Details
```
For IT team members mentioned or listed, capture:

- Name/Role
- Function (Infra, Apps, Security, Support, etc.)
- Tenure (years with company)
- Key responsibilities
- Systems/applications they own
- Single point of failure? (Yes/No - are they the only one who knows something critical?)

Identify:
1. Key person dependencies (critical knowledge held by one person)
2. Recent departures (last 12 months)
3. Open positions / hiring challenges
4. Planned additions or reductions

Create a table: Name | Title | Function | Tenure | Key Systems Owned | SPOF Risk?

Flag:
- Roles with <1 year tenure in critical positions
- Single points of failure for critical systems
- Open positions unfilled >6 months
```

---

## Phase 2: IT Operating Model

### Prompt 2.1 - IT Service Delivery Model
```
Assess how IT delivers services:

1. Service desk / help desk:
   - Internal team or outsourced?
   - ITSM tool (ServiceNow, Jira Service Management, Freshservice, Zendesk, other)
   - Ticket volume (if mentioned)
   - SLAs defined?
   - User satisfaction measured?

2. IT processes maturity:
   - ITIL adoption level (None, Partial, Full)
   - Change management process? (CAB, change windows)
   - Incident management process?
   - Problem management?
   - Configuration management (CMDB)?

3. IT governance:
   - IT steering committee or governance board?
   - IT project prioritization process?
   - Business relationship management?
   - IT budget management process?

4. Documentation and knowledge:
   - Knowledge base exists?
   - System documentation quality
   - Runbooks for operations?

Rate IT operations maturity: Reactive | Proactive | Service-Oriented | Business Partner
```

### Prompt 2.2 - Outsourcing and Managed Services
```
Document all external IT resources:

1. Managed Service Providers (MSPs):
   - Provider name
   - Services provided (help desk, infrastructure, security)
   - Contract term and cost
   - Geographic location (onshore/offshore)

2. Staff augmentation / contractors:
   - Number of IT contractors
   - Roles filled by contractors
   - Agencies used
   - Long-term contractors (>1 year)

3. Outsourced development:
   - Development vendors
   - What's developed externally?
   - Onshore vs. offshore
   - Code ownership

4. Consulting and professional services:
   - Implementation partners
   - Advisory relationships
   - Ongoing engagements

Total external IT resources: MSP FTEs equivalent: X | Contractors: Y | Offshore dev: Z

Flag:
- Heavy reliance on single MSP
- Contractors in critical roles with no knowledge transfer
- Offshore development with IP concerns
```

---

## Phase 3: IT Budget and Spend

### Prompt 3.1 - IT Budget Analysis
```
Document IT spending:

1. Total IT budget:
   - Annual IT budget (if disclosed)
   - IT spend as % of revenue
   - IT spend per employee

2. Budget breakdown (if available):
   - Personnel (salaries, benefits)
   - Software licenses / SaaS
   - Hardware / infrastructure
   - Telecom / network
   - Outsourcing / managed services
   - Projects / capital
   - Cloud spend

3. Budget trends:
   - YoY change
   - Recent significant investments
   - Planned investments
   - Deferred investments or technical debt

4. Benchmarking:
   - How does IT spend compare to industry?
   - Is IT viewed as cost center or investment?
   - Any efficiency initiatives underway?

Create budget summary table: Category | Annual Spend | % of Total | Notes

Flag:
- IT spend significantly below industry benchmark (underinvestment)
- IT spend significantly above benchmark (inefficiency or complexity)
- Deferred capital spend (aging systems)
```

### Prompt 3.2 - IT Contracts Overview
```
Inventory significant IT contracts:

For each contract:
- Vendor
- Category (software, services, hardware, telecom)
- Annual value
- Contract term / end date
- Auto-renewal terms
- Change of control provisions
- Termination for convenience?

Prioritize:
1. Contracts > $100K annually
2. Contracts expiring within 12 months
3. Contracts with change of control issues
4. Multi-year commitments with early termination penalties

Note: Detailed application and infrastructure contracts covered in those playlists. Focus here on services, MSP, and enterprise agreements.
```

---

## Phase 4: IT Capabilities and Skills

### Prompt 4.1 - Skills Assessment
```
Assess IT team capabilities:

1. Core skills present:
   - Infrastructure (Windows, Linux, virtualization, cloud)
   - Networking (WAN, LAN, security)
   - Security (operational security, compliance)
   - Applications (ERP, CRM, custom development)
   - Development (languages, frameworks)
   - Data / Analytics (BI, data engineering)
   - Project management

2. Skills gaps:
   - What skills are mentioned as lacking?
   - What skills are being sought in hiring?
   - What's outsourced due to skill gaps?

3. Modern capabilities:
   - Cloud (AWS, Azure, GCP certifications or experience)
   - DevOps / CI/CD
   - Infrastructure as Code
   - Containerization / Kubernetes
   - Data engineering / modern data stack
   - Security (cloud security, zero trust)

4. Training and development:
   - Training budget
   - Certifications held
   - Learning programs

Create skills matrix: Skill Area | Current Capability (Strong/Adequate/Weak/None) | Gap Risk

Flag:
- Critical skills held by single person
- No cloud capabilities if moving to cloud
- No security skills if no dedicated security person
```

### Prompt 4.2 - Development and Project Capability
```
Assess software development and project delivery:

1. Development team:
   - Internal developers (count, roles)
   - Languages and frameworks used
   - SDLC methodology (Agile, Waterfall, hybrid)
   - Dev tools (source control, CI/CD, testing)

2. Project delivery:
   - IT PMO exists?
   - Project management methodology
   - Active projects (count, size)
   - Project success rate

3. Custom development:
   - What's built in-house?
   - Legacy code ownership
   - Technical debt in custom apps

4. Integration capability:
   - API development experience
   - Integration tools knowledge
   - M&A integration experience

Rate project delivery capability: Ad-hoc | Basic | Managed | Optimized
```

---

## Phase 5: IT Culture and Change Readiness

### Prompt 5.1 - IT Culture Assessment
```
Assess IT team culture and operating style:

1. IT-Business relationship:
   - How does business perceive IT? (Partner, Order-taker, Obstacle)
   - IT involvement in business strategy?
   - Shadow IT prevalence (business buying own tools)

2. Operating style:
   - Process-oriented or flexible?
   - Documentation-heavy or tribal knowledge?
   - Proactive or reactive?
   - Innovation-focused or maintenance-focused?

3. Team dynamics:
   - Tenure distribution (years of experience)
   - Recent turnover
   - Employee satisfaction indicators
   - Collaboration across IT teams

4. Change readiness:
   - History of major changes (system implementations, migrations)
   - Change resistance indicators
   - Adaptability to new processes

Assess culture fit with buyer (if known):
- Similar operating models: Easy integration
- Different operating models: Change management needed
```

### Prompt 5.2 - Key Person and Retention Risk
```
Identify retention and key person risks:

1. Critical personnel:
   - Who are the indispensable people?
   - What systems/knowledge do they hold?
   - What happens if they leave?

2. Flight risk indicators:
   - Long tenure + approaching retirement
   - Uncertainty about role post-acquisition
   - Competing offers known
   - Signs of disengagement

3. Retention considerations:
   - Existing retention agreements
   - Bonus or equity vesting schedules
   - Non-compete agreements

4. Knowledge transfer risk:
   - Undocumented systems
   - Single person with access credentials
   - Relationships with vendors (personal vs. company)

Create key person risk table: Name | Role | Critical Knowledge | Flight Risk | Retention Priority

Recommend retention approach for high-priority individuals.
```

---

## Phase 6: Risks and Integration Considerations

### Prompt 6.1 - IT Organization Risks
```
Synthesize IT organization risks:

For each risk:
- Risk title
- Description
- Severity (Critical/High/Medium/Low)
- Category:
  - Operational Continuity (can they keep running?)
  - Integration Complexity (how hard to integrate?)
  - Cost Risk (unexpected costs)
  - Talent Risk (retention, skills)
- Evidence (source quote)
- Mitigation approach

Common IT org risks:
- Key person dependency (single point of failure)
- Skills gaps for integration activities
- Outsourcing dependency with change of control risk
- Underinvestment (deferred spend catch-up required)
- Culture mismatch with buyer
- IT leader flight risk
- Poor IT-business relationship (shadow IT, workarounds)
```

### Prompt 6.2 - IT Organization Follow-up Questions
```
Generate follow-up questions for IT organization gaps:

For each question:
- Question text
- Why it matters
- Priority (Must have / Important / Nice to have)
- Who should answer (CIO, HR, Management)

Essential questions:
1. Walk us through the IT org chart and key responsibilities
2. Who are your most critical IT team members and why?
3. What IT roles are you struggling to fill or retain?
4. What's your IT budget and how has it changed over the past 3 years?
5. What major IT projects have you completed recently and what's planned?
6. How do you handle IT knowledge documentation and transfer?
7. If you (IT leader) left tomorrow, what would be at risk?
8. What's your biggest IT challenge right now?
```

---

## Output Checklist

After running this playlist, you should have:
- [ ] IT organization structure and headcount
- [ ] IT team roster with tenure and key system ownership
- [ ] Key person / single point of failure identification
- [ ] IT operating model and process maturity assessment
- [ ] Outsourcing and contractor inventory
- [ ] IT budget and spend analysis
- [ ] IT skills assessment with gaps identified
- [ ] Culture and change readiness assessment
- [ ] Retention risk assessment for key personnel
- [ ] Prioritized risk list
- [ ] Follow-up questions for management sessions
