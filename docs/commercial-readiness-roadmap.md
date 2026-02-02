# IT Due Diligence Tool - Commercial Readiness Roadmap

**Purpose:** Map the path from functional prototype to client-ready tool within PwC environment

---

## Current State vs. Commercial State

| Dimension | Current (Prototype) | Commercial Requirement |
|-----------|---------------------|------------------------|
| **Hosting** | Local machine / dev environment | PwC-approved cloud infrastructure |
| **Data** | Synthetic test data | Real client VDR documents |
| **Access** | Developer access | Role-based, audited access |
| **Security** | Basic | PwC InfoSec approved |
| **AI Provider** | Direct Anthropic API | PwC-approved AI gateway |
| **Support** | Developer fixes | Defined support model |
| **Quality** | Ad-hoc review | QC process with sign-off |

---

## Phase Overview

```
[Current]     [Phase 1]        [Phase 2]         [Phase 3]        [Commercial]
Prototype --> Team Testing --> Infrastructure --> Pilot Deal --> Scaled Rollout
              (10 days)        (8-12 weeks)      (1-2 deals)      (Ongoing)

                    WE ARE HERE
```

---

## Phase 1: Functional Validation (Current Focus)

**Duration:** 10 business days
**Objective:** Confirm tool works correctly with synthetic data

**Deliverables:**
- Test results across 12 scenarios
- Bug fixes for critical/high issues
- Confidence that core logic is sound

**Gate:** Average scores >= 4.0, no critical bugs

---

## Phase 2: Enterprise Infrastructure & Compliance

**Duration:** 8-12 weeks (estimate - depends on PwC processes)
**Objective:** Deploy in PwC-approved environment with security controls

### 2.1 Infrastructure Decisions

| Decision | Options | Considerations |
|----------|---------|----------------|
| **Cloud Platform** | Azure (likely) / AWS / GCP | PwC enterprise agreements, existing approvals |
| **Deployment Model** | PaaS / Containerized / VM | Maintenance burden, scaling needs |
| **Database** | PostgreSQL / Azure SQL | Data residency, backup requirements |
| **AI Gateway** | PwC AI Platform / Direct API with controls | Firm policy on GenAI, logging requirements |

**Key Questions for IT/Architecture:**
- [ ] Which cloud platforms are pre-approved for client data?
- [ ] Is there a PwC AI/ML platform we should integrate with?
- [ ] What are the data residency requirements by region?
- [ ] Container orchestration preferences (Kubernetes, etc.)?

### 2.2 Security & InfoSec Review

| Requirement | What's Needed | Current State |
|-------------|---------------|---------------|
| **Authentication** | SSO integration (Azure AD) | Basic auth |
| **Authorization** | Role-based access, deal-level permissions | Admin only |
| **Audit Logging** | All actions logged with user, timestamp | Basic logging |
| **Encryption - Transit** | TLS 1.3 | Yes |
| **Encryption - Rest** | AES-256, key management | Database-level |
| **Data Retention** | Configurable per engagement | Manual deletion |
| **Penetration Testing** | Required before production | Not done |
| **Vulnerability Scanning** | Automated, regular | Not implemented |

**InfoSec Review Process (Typical):**
1. Submit architecture documentation
2. Security questionnaire
3. Code review / SAST scan
4. Penetration test
5. Remediation of findings
6. Approval with conditions

**Estimate:** 4-8 weeks depending on queue and findings

### 2.3 AI/GenAI Compliance

| Requirement | Description | Status |
|-------------|-------------|--------|
| **Approved Models** | Must use PwC-sanctioned AI providers | Using Anthropic - needs approval |
| **Data Handling** | Client data cannot train external models | API config prevents this |
| **Output Review** | AI outputs require human review before client delivery | Built into workflow |
| **Disclosure** | Client informed of AI assistance | Engagement letter language needed |
| **Prompt Logging** | Audit trail of AI interactions | Implemented |
| **Model Risk** | If outputs inform deal decisions, may need model validation | TBD based on use case |

**Key Questions for AI/Innovation Team:**
- [ ] Is Anthropic Claude on the approved vendor list?
- [ ] What's the process for GenAI tool approval?
- [ ] Are there specific prompt/output logging requirements?
- [ ] Does this need to go through Model Risk Management?

### 2.4 Legal & Professional Standards

| Area | Consideration | Action Needed |
|------|---------------|---------------|
| **Engagement Letters** | AI tool usage disclosure | Draft standard language |
| **Independence** | Tool doesn't create independence issues | Confirm with Independence team |
| **Confidentiality** | Data handling meets client expectations | Document controls |
| **Liability** | Outputs are decision-support, not advice | Disclaimer language |
| **Data Processing** | DPA amendments if needed | Legal review |
| **IP Ownership** | Client owns their data, firm owns tool | Standard terms |

### 2.5 Operational Readiness

| Capability | Requirement | Current State |
|------------|-------------|---------------|
| **Support Model** | Who handles bugs, questions? | Developer |
| **SLA** | Response time expectations | None |
| **Training** | User onboarding materials | None |
| **Documentation** | User guide, admin guide | Partial |
| **Incident Response** | What if tool fails mid-engagement? | Manual fallback |
| **Version Control** | How are updates deployed? | Ad-hoc |
| **Backup/Recovery** | Data backup, disaster recovery | Basic |

---

## Phase 3: Pilot Engagement(s)

**Duration:** 1-2 real deals (4-8 weeks calendar time)
**Objective:** Validate in real conditions with safety nets

### Pilot Selection Criteria

**Ideal Pilot Deal:**
- [ ] Internal team is experienced (can catch tool errors)
- [ ] Timeline allows for manual backup if tool fails
- [ ] Client relationship tolerates "we're testing a new capability"
- [ ] Deal complexity is moderate (not simplest, not most complex)
- [ ] Data quality is reasonable (not worst-case VDR)

**Not Ideal for Pilot:**
- High-stakes deal with tight timeline
- New client relationship
- Unusually complex carve-out
- Poor quality VDR with mostly scanned documents

### Pilot Success Criteria

| Metric | Target |
|--------|--------|
| Time savings vs. manual | >= 30% reduction in fact-gathering time |
| Output quality | Senior reviewer rates as "usable with minor edits" |
| Error rate | No material errors in client deliverable |
| User satisfaction | Practitioners would use again |

### Pilot Feedback Collection

- Daily standups during pilot
- Structured feedback form at completion
- Comparison to similar manual engagements
- Client feedback (if appropriate)

---

## Phase 4: Scaled Rollout

**Prerequisite:** Successful pilot(s), all Phase 2 approvals in place

### Rollout Approach

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Big Bang** | All teams get access at once | Fast adoption | Risk of overwhelming support |
| **Phased by Region** | Roll out region by region | Manageable support | Slower, regional inconsistency |
| **Phased by Team** | Roll out to select teams first | Controlled, build champions | Perceived unfairness |
| **On-Demand** | Teams request access | Self-selecting adopters | Slow organic growth |

**Recommendation:** Phased by team - start with 2-3 engaged teams, build internal champions, then expand.

### Ongoing Operations

| Function | Responsibility | Cadence |
|----------|---------------|---------|
| Bug fixes | Development team | As needed |
| Feature requests | Product backlog | Quarterly review |
| Security patches | DevOps | Immediate for critical |
| User training | Enablement team | New user onboarding |
| QC spot-checks | QC function | Sample of engagements |
| Usage analytics | Product team | Monthly review |
| Model updates | Development team | Tested before deploy |

---

## Timeline Summary (Realistic)

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Functional Validation | 2 weeks | Team availability |
| Phase 2: Infrastructure & Compliance | 8-12 weeks | InfoSec queue, AI approval process |
| Phase 3: Pilot Engagement | 4-8 weeks | Right deal available |
| Phase 4: Initial Rollout | 4 weeks | Training materials ready |
| **Total to First Non-Pilot Use** | **18-32 weeks** | |

**Critical Path Items:**
1. AI/GenAI approval (often longest)
2. InfoSec review and pen test
3. Finding suitable pilot deal

---

## Risks to Commercial Readiness

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI provider not approved | Medium | High - blocks deployment | Early engagement with AI governance |
| InfoSec findings require major rework | Medium | High - delays timeline | Security review of architecture now |
| No suitable pilot deal available | Low | Medium - delays validation | Identify 3-4 candidate deals early |
| Pilot fails / poor quality | Low | High - damages credibility | Strong pilot selection, senior oversight |
| Practitioners don't adopt | Medium | Medium - low ROI | Early involvement, show value clearly |

---

## Immediate Next Steps

### This Week
1. [ ] Confirm Phase 1 testing team and start date
2. [ ] Identify AI governance contact - start approval conversation
3. [ ] Identify InfoSec contact - understand review process timeline

### Next 2 Weeks
4. [ ] Submit AI tool for GenAI governance review
5. [ ] Document current architecture for InfoSec
6. [ ] Begin Phase 1 testing

### Next Month
7. [ ] Complete Phase 1, compile results
8. [ ] Kick off InfoSec review process
9. [ ] Identify 3-4 potential pilot deals
10. [ ] Draft engagement letter AI disclosure language

---

## Leadership Decisions Needed

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **Cloud platform** | Azure / AWS / Existing PwC platform | Align with enterprise standards |
| **AI provider path** | Seek Anthropic approval / Switch to approved provider | Start approval process now |
| **Pilot approach** | Internal-only first / Client-facing | Internal team pilot first |
| **Investment level** | Minimal (current team) / Dedicated resources | Dedicated PM + Dev for Phase 2 |
| **Timeline priority** | Speed to market / Thoroughness | Balance - don't skip security |

---

## Appendix: Key Contacts Needed

| Function | Purpose | Contact |
|----------|---------|---------|
| AI/GenAI Governance | Tool approval | TBD |
| InfoSec | Security review | TBD |
| Cloud Infrastructure | Hosting options | TBD |
| Legal/OGC | Engagement letter language | TBD |
| Independence | Confirm no issues | TBD |
| Risk/Quality | QC process design | TBD |
| Deals Leadership | Pilot deal selection | TBD |
