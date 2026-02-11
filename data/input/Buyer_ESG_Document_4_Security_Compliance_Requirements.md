# Enterprise Solutions Group (ESG) — Buyer Document 4: Security & Compliance Requirements

> **Entity:** BUYER
> **Purpose:** ESG security standards and compliance requirements for acquisition integration

---

## 1) ESG Security Posture (Baseline)

| Metric | Value |
|---|---|
| **Security team size** | 180 FTE (global SOC + engineering) |
| **Annual security budget** | $85M (tools, personnel, services) |
| **SOC operations** | 24/7/365 (3 global SOCs: US, EMEA, APAC) |
| **Security certifications** | SOC 2, ISO 27001, GDPR, CCPA, PCI-DSS L1, HIPAA, FedRAMP (in progress) |
| **Incident response** | <15 min detection, <1 hour containment (P0) |
| **Penetration testing** | Quarterly (internal + external) |

---

## 2) ESG Mandatory Security Controls (Day 1-90)

| Control | Technology | Deployment Timeline | CloudServe Gap |
|---|---|---|---|
| **Endpoint security (EDR)** | CrowdStrike Falcon Enterprise | Day 1 | ✅ Already deployed |
| **SIEM** | Splunk Enterprise Security | Within 90 days | ⚠️ GAP: Using Datadog (not SIEM) |
| **CSPM (cloud security)** | Microsoft Defender for Cloud (Azure), Wiz (AWS) | Within 90 days | ⚠️ GAP: Wiz contract expiring |
| **Vulnerability scanning** | Qualys VMDR | Within 90 days | ⚠️ GAP: No external vuln scanning |
| **PAM (privileged access)** | CyberArk Enterprise | Within 60 days | ⚠️ GAP: Limited deployment (15 users) |
| **MFA** | Azure AD MFA (100% coverage) | Within 30 days | ⚠️ GAP: 85% coverage (62 users without MFA) |
| **DLP (data loss prevention)** | Microsoft Purview DLP | Within 180 days | ⚠️ GAP: No DLP deployed |

---

## 3) ESG Compliance Requirements

### Mandatory Certifications

| Certification | ESG Status | Requirement for CloudServe | Timeline |
|---|---|---|---|
| **SOC 2 Type II** | ✅ Certified | Maintain certification | Ongoing (renewal in 4 months) |
| **ISO 27001** | ✅ Certified | Achieve certification | Within 12 months |
| **GDPR** | ✅ Compliant (audited) | Formal audit required | Within 6 months |
| **CCPA** | ✅ Compliant | Formal audit required | Within 6 months |
| **PCI-DSS** | ✅ Level 1 | N/A (no card data; Stripe handles) | N/A |
| **HIPAA** | ✅ Compliant | N/A (no PHI) | N/A |

### Compliance Gaps (CloudServe)

| Gap | Current State | Required State | Fix Cost Estimate |
|---|---|---|---|
| **ISO 27001** | Not certified | Certified within 12 months | $200K-300K |
| **GDPR audit** | Self-assessed only | Formal audit | $75K-125K |
| **CCPA audit** | Self-assessed only | Formal audit | $50K-75K |
| **SOC 2 renewal** | Due in 4 months | Accelerate renewal | $100K-150K |

**Total Compliance Remediation Cost:** $425K-650K

---

## 4) ESG Security Tool Stack (Standard)

| Category | Tool | Purpose | CloudServe Equivalent |
|---|---|---|---|
| **EDR** | CrowdStrike Falcon | Endpoint detection & response | ✅ CrowdStrike (aligned) |
| **SIEM** | Splunk Enterprise Security | Security event management | ❌ Datadog (not SIEM) |
| **CSPM** | Defender for Cloud (Azure), Wiz (AWS) | Cloud security posture | ⚠️ Wiz (contract expiring) |
| **SAST** | Checkmarx | Static code analysis | ❌ None |
| **DAST** | Veracode | Dynamic app scanning | ❌ None |
| **Vuln scanning** | Qualys VMDR | Vulnerability management | ⚠️ AWS Inspector only (internal) |
| **PAM** | CyberArk | Privileged access | ⚠️ CyberArk (limited - 15 users) |
| **DLP** | Microsoft Purview | Data loss prevention | ❌ None |
| **Threat intel** | Recorded Future | Threat intelligence | ❌ None |
| **UEBA** | Splunk UBA | User behavior analytics | ❌ None |

---

## 5) CloudServe Security Gaps & Remediation Plan

| Gap | Description | Severity | Fix Timeline | Estimated Cost |
|---|---|---|---|---:|
| **No SIEM** | Datadog Security Monitoring (not full SIEM) | 🔴 HIGH | 90 days | $150K-250K (Splunk integration) |
| **Wiz expiring** | CSPM contract ends in 2 months | 🔴 HIGH | 60 days | $125K/year (renewal) |
| **Limited PAM** | Only 15 users in CyberArk (26 privileged users not covered) | 🟠 MEDIUM | 90 days | $50K-100K (expand deployment) |
| **MFA gap** | 15% of users (62 people) not using MFA | 🟠 MEDIUM | 30 days | $10K-20K (policy enforcement) |
| **No SAST/DAST** | No static/dynamic code scanning | 🟠 MEDIUM | 180 days | $80K-120K/year (Checkmarx + Veracode) |
| **No external vuln scanning** | Only AWS Inspector (internal scans) | 🟠 MEDIUM | 90 days | $40K-60K/year (Qualys) |
| **No DLP** | Data classification policy exists but not enforced | 🟡 LOW | 180 days | $75K-125K (Purview DLP) |
| **Vuln SLA misses** | 87 open vulnerabilities, SLAs not met | 🟡 LOW | 90 days | $50K-100K (dedicated resource) |

**Total Security Remediation Cost:** $580K-1.02M (one-time) + $245K-305K/year (recurring tools)

---

## 6) ESG Penetration Testing Requirements

| Test Type | Frequency | Scope | CloudServe State |
|---|---|---|---|
| **External pentest** | Quarterly | Internet-facing assets | ⚠️ Annual only (last test: 6 months ago) |
| **Internal pentest** | Semi-annually | Internal network, apps | ❌ Not conducted |
| **Cloud pentest** | Semi-annually | AWS/Azure environments | ❌ Not conducted |
| **Application pentest** | Per release (major) | Customer-facing apps | ⚠️ Annual only |

**Requirement:** Increase pentest frequency to ESG standard (quarterly external, semi-annual internal).
**Cost:** $120K-180K/year (increased testing cadence)

---

## 7) ESG Incident Response Requirements

| Requirement | ESG Standard | CloudServe State | Gap |
|---|---|---|---|
| **IR plan** | Updated quarterly | Last updated: 9 months ago | ⚠️ Refresh required |
| **IR runbooks** | 100% scenario coverage | 60% coverage | ⚠️ Complete runbooks |
| **IR testing (tabletop)** | Quarterly | Never tested | 🔴 GAP: Implement testing |
| **SOC coverage** | 24/7/365 | Business hours only (via Datadog alerts) | ⚠️ Extend to ESG SOC |
| **MTTR (P0 incidents)** | <1 hour | Unknown (untested) | ⚠️ Validate capability |

**Integration:** CloudServe security events will feed into ESG's global SOC (Splunk SIEM) within 90 days.

---

## 8) ESG Data Security Requirements

| Requirement | Standard | CloudServe State |
|---|---|---|
| **Encryption at rest** | AES-256 (all data) | ✅ Aligned (AWS KMS) |
| **Encryption in transit** | TLS 1.2+ | ✅ Aligned (customer-facing) |
| **East-west traffic encryption** | Required (service mesh) | ⚠️ GAP: Not fully encrypted |
| **Data classification** | Microsoft Purview | ⚠️ GAP: Policy exists, not enforced |
| **DLP** | Microsoft Purview DLP | ⚠️ GAP: Not deployed |
| **Data residency** | Region-specific (GDPR/CCPA) | 🔴 GAP: All data in us-east-1 |
| **Backup encryption** | Required | ✅ Aligned (AWS KMS) |

**Critical Gap:** Data residency (EU data in US region) violates GDPR requirements. Must deploy EU region within 6-12 months.

---

## 9) ESG Security Metrics & Reporting

| Metric | ESG Target | Measurement | CloudServe Current State |
|---|---|---|---|
| **MFA coverage** | 100% | Okta/Azure AD reports | 85% (gap: 15%) |
| **Vulnerability remediation (Critical)** | <7 days | SIEM + vuln scanner | 12 days avg (missing SLA) |
| **Patch compliance** | 95% within 30 days | Endpoint mgmt | Unknown |
| **Security awareness training** | 100% annually | LMS tracking | Unknown |
| **Phishing simulation** | Quarterly | Security awareness platform | ❌ Not conducted |

**Requirement:** Implement ESG security metrics reporting within 90 days.

---

## 10) ESG Third-Party Risk Management (TPRM)

| Requirement | ESG Standard | CloudServe State |
|---|---|---|
| **TPRM program** | Formal assessments for all vendors | ⚠️ GAP: No TPRM program |
| **Vendor security reviews** | Annual for critical vendors | ⚠️ GAP: Not conducted |
| **Vendor access controls** | MFA required, least privilege | ⚠️ GAP: MSP (CGI) has no MFA |
| **Vendor risk tiers** | High/Medium/Low based on data access | ⚠️ GAP: No tiering |

**Requirement:** Implement TPRM program within 180 days; immediate fix for MSP MFA gap (30 days).

---

## 11) Security Integration Timeline (CloudServe)

| Milestone | Timeline | Activities |
|---|---|---|
| **Day 1-30** | Month 1 | MFA 100% enforcement, Wiz renewal, CyberArk expansion planning |
| **Day 30-90** | Months 2-3 | Splunk SIEM integration, Qualys deployment, PAM expansion |
| **Day 90-180** | Months 4-6 | ISO 27001 prep, GDPR/CCPA audits, DLP pilot |
| **Day 180-365** | Months 7-12 | ISO 27001 certification, EU data residency deployment, SAST/DAST integration |

---

## 12) Security Budget Estimate (CloudServe Integration)

| Category | One-Time Cost | Annual Recurring Cost |
|---|---:|---:|
| **SIEM (Splunk integration)** | $150K-250K | Included in ESG Splunk license |
| **PAM expansion (CyberArk)** | $50K-100K | Included in ESG CyberArk license |
| **CSPM (Wiz renewal)** | $0 | $125K |
| **Vuln scanning (Qualys)** | $0 | $40K-60K |
| **SAST/DAST** | $0 | $80K-120K |
| **Pentest (increased frequency)** | $0 | $120K-180K |
| **ISO 27001 certification** | $200K-300K | $50K-75K (annual audit) |
| **GDPR/CCPA audits** | $125K-200K | $0 (one-time) |
| **DLP (Purview)** | $75K-125K | Included in ESG M365 license |
| **EU data residency** | $250K-500K | $0 (operational cost in AWS spend) |
| **TPRM program** | $50K-100K | $30K-50K |
| **TOTAL** | **$900K-1.675M** | **$445K-610K** |

---

**END OF BUYER DOCUMENT 4**
