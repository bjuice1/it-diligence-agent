# IT Due Diligence Playbook

## Overview

This playbook provides a structured approach to IT due diligence for M&A transactions. It is designed to be used with AI-assisted document review tools (Tolt IQ, Harvey, Claude, etc.) to systematically extract, analyze, and synthesize IT findings from a data room.

**What this playbook is:**
- A comprehensive prompt library for IT due diligence
- A methodology that ensures consistent, thorough coverage
- A collection of lessons learned from hands-on IT DD experience
- A framework for organizing findings into actionable insights

**What this playbook is not:**
- A replacement for IT expertise and judgment
- A guarantee of finding every issue
- A substitute for management interviews and validation

---

## The Story Behind This Playbook

This playbook emerged from an attempt to build a bespoke IT due diligence tool - a custom application with structured data capture, validation logic, EOL reference databases, and automated report generation.

After significant development, we realized: **80% of the value could be achieved with well-crafted prompts run through existing AI document review tools.**

The custom tool's value was in:
- Consistent prompt methodology (captured here)
- Domain expertise encoded in questions (captured here)
- Structured thinking about what to look for (captured here)

The remaining 20% - data consistency across sessions, EOL database lookups, automated Excel formatting - didn't justify the build and maintenance overhead for most use cases.

**The result is this playbook: all the methodology, none of the maintenance.**

---

## How to Use This Playbook

### Step 1: Preparation
Before starting document review:

1. **Understand the deal context:**
   - What type of transaction? (acquisition, carve-out, merger)
   - What's the buyer's IT environment like?
   - What are the known concerns or focus areas?
   - What's the timeline and depth of diligence?

2. **Review available documents:**
   - What's in the data room?
   - Is there an application inventory?
   - Are there architecture diagrams?
   - What's the document quality like?

3. **Choose your tools:**
   - Tolt IQ for large data rooms with many documents
   - Harvey for legal-heavy review with IT components
   - Claude/GPT for smaller document sets or specific analysis
   - Combination as appropriate

### Step 2: Domain Reviews
Run each domain playlist against the relevant documents:

| Order | Domain | Playlist File | Typical Time |
|-------|--------|---------------|--------------|
| 1 | Applications | `01_applications_landscape.md` | 2-4 hours |
| 2 | Infrastructure | `02_infrastructure.md` | 1-2 hours |
| 3 | Network | `03_network.md` | 1-2 hours |
| 4 | Cybersecurity | `04_cybersecurity.md` | 2-3 hours |
| 5 | Identity & Access | `06_identity_access.md` | 1-2 hours |
| 6 | IT Organization | `05_it_organization.md` | 1-2 hours |

**Tips for domain reviews:**
- Run one domain at a time to maintain context
- Download/export outputs after each section
- Note questions that arise for follow-up
- Mark confidence level on uncertain findings

### Step 3: Synthesis
After completing domain reviews, run the synthesis playlist:

| Order | Section | Playlist File |
|-------|---------|---------------|
| 7 | Cross-Domain Synthesis | `07_cross_domain_synthesis.md` |

The synthesis pulls together:
- Consolidated findings across domains
- Four Lenses analysis (Current State, Risks, Strategy, Integration)
- Cost and complexity estimation
- Executive summary
- Management session questions

### Step 4: Management Session
Use the synthesized findings to conduct a focused management interview:
- Lead with critical questions
- Validate assumptions
- Probe areas of uncertainty
- Document answers for final report

### Step 5: Final Report
Compile findings into final deliverable:
- Executive summary (1 page)
- Domain findings
- Consolidated risks
- Integration recommendations
- Appendices (inventories, questions, contracts)

---

## Domain Guide

### Applications Landscape (`01_applications_landscape.md`)

**Purpose:** Inventory all business applications and assess coverage, health, and risk.

**Key outputs:**
- Application inventory (name, vendor, category, hosting, criticality)
- Business capability coverage matrix
- EOL and technical debt assessment
- Integration and data flow map
- Buyer comparison (if applicable)

**What makes this domain unique:**
- Business-centric (maps to processes, not just tech)
- Vendor dependency is critical (roadmaps, licensing, support)
- Customization is hidden risk (two "SAP" deployments can be completely different)
- Shadow IT is common (official inventory misses things)

**Critical questions to answer:**
1. What are the core business systems (ERP, HCM, CRM)?
2. Are there EOL applications requiring upgrade investment?
3. What capabilities are NOT covered by documented applications?
4. What's the customization level of key systems?

---

### Infrastructure (`02_infrastructure.md`)

**Purpose:** Assess compute, storage, data center, and cloud environments.

**Key outputs:**
- Data center and hosting inventory
- Compute and storage environment inventory
- Cloud maturity assessment
- DR/BC capability assessment
- Infrastructure contracts

**What makes this domain unique:**
- Physical and financial reality (capital assets, depreciation)
- Cloud vs. on-prem is THE strategic question
- Capacity and runway affect growth
- DR/BC is often the hidden gap

**Critical questions to answer:**
1. What's the data center footprint and exit strategy?
2. What's the cloud maturity and migration status?
3. Is there tested disaster recovery for critical systems?
4. What infrastructure is approaching end of life?

---

### Network (`03_network.md`)

**Purpose:** Assess WAN, LAN, connectivity, and network security posture.

**Key outputs:**
- Sites and connectivity inventory
- WAN architecture (MPLS, SD-WAN, VPN)
- IP addressing and DNS documentation
- Network security components
- Telecom contracts

**What makes this domain unique:**
- Connectivity = business operation
- Contracts have long lead times (60-120 days for changes)
- Integration complexity is high (IP conflicts, firewall rules)
- Documentation is typically poor

**Critical questions to answer:**
1. What's the WAN architecture and how hard to integrate?
2. What's the IP addressing scheme and overlap risk?
3. Is there a network diagram that's actually current?
4. What are the key telecom contracts and terms?

---

### Cybersecurity (`04_cybersecurity.md`)

**Purpose:** Assess security program maturity, controls, and risk posture.

**Key outputs:**
- Security program maturity rating
- Security controls inventory (endpoint, network, data, monitoring)
- Compliance and certification status
- Vulnerability management assessment
- Incident history (if disclosed)

**What makes this domain unique:**
- Material deal risk (breaches can be deal-breakers)
- What you see isn't always what you get (claims vs. reality)
- Compliance ≠ security
- Integration creates new attack surface

**Critical questions to answer:**
1. What is MFA coverage (all users, privileged)?
2. What was found in the last penetration test?
3. Has there been any security incident in the past 3 years?
4. What's the vulnerability remediation SLA and compliance?

---

### Identity & Access (`06_identity_access.md`)

**Purpose:** Assess identity infrastructure, authentication, authorization, and privileged access.

**Key outputs:**
- Identity provider inventory
- MFA implementation details
- Access control model assessment
- Privileged access management evaluation
- Cloud IAM assessment

**What makes this domain unique:**
- IAM is the glue for integration (Day 1 access)
- MFA is single most important security control
- Privileged access is high-value target
- Integration creates new attack surface

**Critical questions to answer:**
1. What is MFA coverage percentage (all users, privileged)?
2. Is there a PAM solution for privileged access?
3. How are accounts de-provisioned when people leave?
4. How many domain admins / global admins exist?

---

### IT Organization (`05_it_organization.md`)

**Purpose:** Assess IT team structure, capabilities, culture, and key person risk.

**Key outputs:**
- IT org structure and headcount
- Key person identification
- Operating model assessment
- Budget and spend analysis
- Skills and capability assessment

**What makes this domain unique:**
- People are hardest to integrate (retention, change resistance)
- Key person risk is real (knowledge concentration)
- Culture fit matters for integration success
- Cost benchmarking is expected (IT spend ratios)

**Critical questions to answer:**
1. Who are the critical IT people and what do they own?
2. What's the IT budget and how does it benchmark?
3. What's the outsourcing/MSP dependency?
4. Is the IT leader a flight risk?

---

### Cross-Domain Synthesis (`07_cross_domain_synthesis.md`)

**Purpose:** Consolidate findings into integrated assessment and executive deliverables.

**Key outputs:**
- Domain summaries
- Four Lenses analysis
- Cost and complexity estimation
- Executive summary
- Management session questions
- Final risk register

**What makes this domain unique:**
- This is where the story comes together
- Risks connect across domains
- Integration complexity becomes clear
- Executive communication matters

---

## Key Lessons Learned

### From Building the Tool

1. **"Unknown" is a valid answer** - Don't force guesses. Explicitly marking "Unknown" or "Not documented" is more valuable than false confidence.

2. **Business capability coverage matters more than app counts** - Having 200 applications means nothing. Not having payroll is a crisis.

3. **EOL dates from LLMs are unreliable** - If EOL accuracy matters, verify against vendor documentation or maintain reference data.

4. **Follow-up questions are an output, not a failure** - Documents don't contain everything. Generating good questions is part of the value.

5. **Structured output enables downstream work** - Tables that can be exported to Excel are more useful than prose paragraphs.

### From Doing IT Due Diligence

1. **Read the documents before jumping to conclusions** - What looks like a gap in the first document may be explained in the fifth.

2. **Probe security claims hard** - "We have MFA" ≠ "MFA is enforced for all users."

3. **The IT leader relationship with business is revealing** - Cost center vs. strategic partner tells you about IT maturity.

4. **Customization is hidden complexity** - Two identical product names can have wildly different implementation complexity.

5. **Contracts often have change of control provisions** - Check before assuming licenses transfer cleanly.

6. **Day 1 requirements drive integration pace** - What must work on close determines minimum integration scope.

7. **The management session is where gaps get filled** - Documents provide foundation; live discussion provides context.

---

## Quick Reference: Critical Questions

If you only have time for a few questions per domain:

| Domain | #1 Question | #2 Question |
|--------|-------------|-------------|
| Applications | What ERP/financial system runs the business? | What apps are approaching EOL? |
| Infrastructure | What's the cloud vs. on-prem split? | Is there tested disaster recovery? |
| Network | What's the WAN architecture? | Is there IP overlap risk? |
| Security | What is MFA coverage %? | When was last pentest and findings? |
| Identity | How are accounts de-provisioned? | Is there PAM for privileged access? |
| IT Org | Who are the key person dependencies? | What's the IT budget and trend? |

---

## Playbook Files

| File | Description |
|------|-------------|
| `00_MASTER_IT_DD_PLAYBOOK.md` | This document - overview and guidance |
| `01_applications_landscape.md` | Applications review prompts |
| `02_infrastructure.md` | Infrastructure review prompts |
| `03_network.md` | Network review prompts |
| `04_cybersecurity.md` | Cybersecurity review prompts |
| `05_it_organization.md` | IT organization review prompts |
| `06_identity_access.md` | Identity & access review prompts |
| `07_cross_domain_synthesis.md` | Synthesis and final deliverables prompts |

---

## Version History

- **v1.0** (2024): Initial playbook derived from bespoke tool development
- Methodology based on Four Lenses DD Framework
- Prompts designed for use with Tolt IQ, Harvey, Claude, and similar tools

---

## Acknowledgments

This playbook represents encoded expertise from multiple IT due diligence engagements. The goal was to create a repeatable, transferable methodology that captures institutional knowledge without requiring custom tooling.

The best IT DD still requires:
- Experienced practitioners who know what questions to ask
- Judgment about what matters for this specific deal
- Validation through management interviews
- Integration with financial and legal DD workstreams

Use this playbook as a foundation, not a substitute for thinking.
