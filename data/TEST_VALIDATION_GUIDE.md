# Test Validation Guide - Synthetic Documents
## Points 99-103: Expected Findings Verification

This document maps the content in synthetic documents to expected analysis findings.
Use this to validate the IT DD Agent is correctly identifying findings.

---

## Document 1: synthetic_it_discovery_v1.txt

### Point 99: Clear Facts → Inventory Items

The agent should identify these as current state inventory entries:

| Section | Expected Inventory Items |
|---------|-------------------------|
| Infrastructure | 127 physical servers, 340 VMs, VMware 7.0, NetApp FAS8200 450TB |
| Infrastructure | Columbus data center: 8,500 sq ft, 2MW power, N+1 UPS |
| Infrastructure | 2,800 desktops/laptops, 450 mobile devices |
| Network | Cisco Nexus 9000 core, Catalyst 9300 distribution, Meraki wireless |
| Network | Palo Alto PA-5250 firewall, MPLS WAN (12 sites) |
| Cloud | AWS: 3 accounts, $45K/month, us-east-2 primary |
| Applications | SAP S/4HANA (850 users), Salesforce (320 users), FactoryTalk (180 users) |
| Applications | 47 sanctioned SaaS apps, 23 custom applications |
| Security | CrowdStrike Falcon, Splunk SIEM, Proofpoint, Tenable, Okta SSO |
| Organization | 47 IT FTEs, 5-person security team, CIO Robert Chen |

### Point 100: Ambiguous Statements → Assumptions

| Statement | Expected Assumption |
|-----------|---------------------|
| "Partial cloud backup to AWS (implemented 2023)" | DR capability may be limited |
| "SAP indirect access terms may need review" | Licensing exposure exists |
| "CyberArk implementation in progress, 60% complete" | PAM not fully deployed |
| "MFA NOT enforced for on-premises applications" | Hybrid MFA gap exists |
| "Approximately 23 internally developed applications" | Custom app count approximate |
| "Last full DR test: Never conducted" | DR untested, may not work |
| "Windows 11 migration 60% complete" | Mixed OS environment |

### Point 101: Obvious Gaps → Gap Entries

| Missing Information | Expected Gap |
|--------------------|--------------|
| No security awareness training mentioned | Training program gap |
| OT/ICS security controls not mentioned | OT security gap |
| Third-party risk management informal | Vendor risk gap |
| AS/400 documentation limited | Legacy system documentation gap |
| No SOC 2 certification | Compliance gap |
| FactoryTalk no DR capability | Manufacturing DR gap |
| Patch management SLA not met | Patch compliance gap |

### Point 102: Risks to Identify

| Evidence | Expected Risk |
|----------|---------------|
| AS/400 developer retiring in 18 months | Key person risk - CRITICAL |
| Single SAP Basis administrator | Key person risk - HIGH |
| Network architect position open | Staffing gap risk |
| No MFA for on-prem applications | Security control gap - HIGH |
| Never conducted full DR test | Business continuity risk - CRITICAL |
| FactoryTalk has no DR | Manufacturing risk - CRITICAL |
| 3 critical, 12 high pen test findings | Security vulnerability risk |
| Shadow IT (47 SaaS apps) | Governance risk |
| SAP indirect access exposure | Licensing/compliance risk |

---

## Document 2: synthetic_it_discovery_v2_followup.txt

### New Information (for Incremental Analysis)

This document should trigger:

1. **Escalated Risks** (severity increased):
   - AS/400 risk: Developer declined consulting, no documentation for 60%
   - DR risk: Actual RTO is 5-7 days, not 48-72 hours
   - Security risk: Phishing incident more serious than disclosed

2. **New Risks Identified**:
   - Cyber insurance policy violation (incident not reported)
   - Shadow IT with customer data (23 unsanctioned apps)
   - 127 service accounts with non-expiring passwords
   - Generator failed load test
   - OSHA citation pending
   - IT staff flight risk (45% actively looking)
   - SAP Basis admin departed (January 2026)
   - SAP audit scheduled Q2 2025 (exposure $500K-$2M)
   - Secureworks may terminate on change of control
   - Pending lawsuit from former security analyst

3. **Gaps Answered**:
   - AS/400 details now provided (2.4M lines, 847 tables, 12TB)
   - DR true state now disclosed
   - Technical debt quantified ($2.925M backlog)

4. **New Gaps Created**:
   - Former employee lawsuit details
   - Exact SAP audit exposure
   - Secureworks replacement timing if terminated

---

## Validation Checklist (Points 104-109)

### Fresh Analysis Validation

- [ ] **104**: Analysis runs without errors
- [ ] **105**: All 6 domains produce findings:
  - [ ] Infrastructure findings present
  - [ ] Network findings present
  - [ ] Cybersecurity findings present
  - [ ] Applications findings present
  - [ ] Identity & Access findings present
  - [ ] Organization findings present
- [ ] **106**: Check database has records:
  ```bash
  python main.py --list-runs
  ```
- [ ] **107**: HTML viewer opens and displays results
- [ ] **108**: JSON files created in output directory:
  - [ ] analysis_output.json
  - [ ] risks.json
  - [ ] gaps.json
  - [ ] assumptions.json
  - [ ] current_state.json
  - [ ] work_items.json
- [ ] **109**: Manual review confirms reasonable findings

### Incremental Analysis Validation (Points 110-114)

- [ ] **110**: Second document analyzed
- [ ] **111**: Incremental mode loads previous findings
- [ ] **112**: New findings merge correctly
- [ ] **113**: Duplicates not repeated
- [ ] **114**: Changed findings show updates (e.g., severity changes)

### Key Finding Counts (Approximate Expectations)

| Finding Type | Doc 1 Alone | After Doc 2 |
|-------------|-------------|-------------|
| Current State | 40-60 | 60-80 |
| Risks | 15-25 | 30-45 |
| Gaps | 10-20 | 15-25 |
| Assumptions | 15-25 | 20-35 |
| Work Items | 20-35 | 40-60 |
| Recommendations | 8-15 | 15-25 |

---

## Domain-Specific Validation

### Infrastructure Domain
Must identify:
- [ ] Data center specs (Columbus, 8,500 sq ft, 2MW)
- [ ] Server count (127 physical, 340 VMs)
- [ ] Storage (NetApp 450TB)
- [ ] Technical debt ($2.925M after Doc 2)

### Network Domain
Must identify:
- [ ] Network architecture (Cisco Nexus/Catalyst, Meraki)
- [ ] WAN structure (MPLS, 12 sites)
- [ ] SD-WAN evaluation in progress
- [ ] Equipment age issues (40% switches end-of-sale)

### Cybersecurity Domain
Must identify:
- [ ] Security tools (CrowdStrike, Splunk, Proofpoint)
- [ ] MFA gaps (on-prem not enforced)
- [ ] Phishing incident (March 2024)
- [ ] Pen test findings (3 critical, 12 high)
- [ ] OT/ICS vulnerabilities (after Doc 2)

### Applications Domain
Must identify:
- [ ] ERP (SAP S/4HANA)
- [ ] CRM (Salesforce)
- [ ] MES (FactoryTalk)
- [ ] Legacy system risk (AS/400)
- [ ] Custom application portfolio (23 apps)

### Identity & Access Domain
Must identify:
- [ ] AD structure (single forest)
- [ ] SSO implementation (Okta, 85% coverage)
- [ ] MFA gaps
- [ ] PAM in progress (CyberArk 60%)
- [ ] Privileged access issues (14 domain admins, after Doc 2)

### Organization Domain
Must identify:
- [ ] IT staff count (47 FTEs)
- [ ] Leadership team
- [ ] Key person risks
- [ ] Staff sentiment issues (after Doc 2)
- [ ] Recent departures (after Doc 2)

---

*Created: January 2026*
*Version: 1.0*
