# CloudServe Technologies — Document 1: Executive IT Profile & Deal Context

> **Entity:** TARGET
> **Purpose:** Baseline IT landscape for M&A due diligence analysis
> **Company:** CloudServe Technologies (B2B SaaS platform provider)
> **Deal Context:** Acquisition by Enterprise Solutions Group (ESG)

---

## 1) Company Overview

| Item | Value |
|---|---|
| Company | CloudServe Technologies (Target) |
| Industry | B2B SaaS - Customer engagement platform |
| Annual revenue | **$87M** (85% recurring, 15% professional services) |
| Employees | **412** (65% engineering/product, 20% sales/marketing, 15% G&A) |
| Customers | **1,847** active enterprise customers |
| Primary product | Multi-tenant customer engagement platform (API-first) |
| Markets | North America (72%), EMEA (21%), APAC (7%) |
| Founded | 2016 (8 years old) |

---

## 2) IT Budget & Spend

| Metric | Value |
|---|---:|
| Annual IT budget | **$14.2M** (**16.3%** of revenue) |
| IT headcount | **67** (includes engineering infra/platform teams) |
| Cloud infrastructure | **$4.8M/year** (AWS) |
| SaaS tooling | **$2.1M/year** (internal productivity + dev tools) |
| Personnel costs | **$6.9M/year** |
| Professional services | **$400K/year** (security audits, compliance, consultants) |

---

## 3) Application Portfolio Summary

| Metric | Value |
|---|---:|
| **Core platform components** | **8** (microservices architecture) |
| **Internal business apps** | **18** (SaaS tools for ops/sales/finance/HR) |
| **Development tools** | **12** (CI/CD, monitoring, APM, testing) |
| **Total applications** | **38** |
| **Hosting model** | 100% Cloud (AWS) |
| **Annual app cost** | **$2,331,500** (SaaS subscriptions + licenses) |

### Application Categories

| Category | Count | Annual Cost |
|---|---:|---:|
| Infrastructure | 9 | $150,000 |
| CRM | 3 | $428,000 |
| ERP | 1 | $180,000 |
| Finance | 4 | $200,000 |
| HCM | 2 | $144,000 |
| Collaboration | 3 | $168,000 |
| DevOps | 9 | $170,000 |
| Productivity | 3 | $36,000 |
| Security | 5 | $598,000 |
| Database | 1 | $285,000 |
| BI/Analytics | 1 | $32,500 |

---

## 4) Infrastructure Profile

| Metric | Value |
|---|---:|
| **Cloud provider** | AWS (us-east-1 primary, eu-west-1 secondary) |
| **AWS accounts** | **9** (prod, staging, dev, shared services, data, security, sandbox × 3) |
| **Total AWS spend** | **$4.8M/year** ($400K/month) |
| **Compute** | EKS (Kubernetes) - 47 nodes across environments |
| **Database** | RDS PostgreSQL (multi-AZ), Aurora (read replicas), DynamoDB |
| **Storage** | S3 (primary), EBS, EFS |
| **CDN** | CloudFront + Fastly ($85K/year) |
| **Data centers** | **0** (cloud-only) |

### AWS Service Breakdown

| Service Category | Monthly Cost | Annual Cost |
|---|---:|---:|
| Compute (EC2, EKS, Lambda) | $145,000 | $1,740,000 |
| Database (RDS, Aurora, DynamoDB) | $112,000 | $1,344,000 |
| Storage (S3, EBS, EFS) | $48,000 | $576,000 |
| Networking (VPC, Transit Gateway, Direct Connect) | $38,000 | $456,000 |
| CDN & Edge (CloudFront) | $32,000 | $384,000 |
| Security & Identity (WAF, GuardDuty, Secrets Manager) | $15,000 | $180,000 |
| Monitoring & Logging (CloudWatch, CloudTrail) | $10,000 | $120,000 |

---

## 5) Network & Security Posture

| Item | Value |
|---|---|
| **Network architecture** | Multi-VPC (prod, non-prod, shared services) |
| **Internet connectivity** | AWS Direct Connect (1Gbps) to corporate office |
| **VPN** | AWS Client VPN + Tailscale for remote access |
| **Firewall** | AWS WAF + Security Groups |
| **DDoS protection** | AWS Shield Standard (not Advanced) |
| **Endpoint security** | CrowdStrike Falcon |
| **SIEM** | Datadog Security Monitoring (not dedicated SIEM) |
| **Vulnerability scanning** | Snyk (code), Wiz (cloud infrastructure) |
| **Penetration testing** | Annual (last test: 6 months ago) |

### Security Compliance Status

| Framework | Status | Last Audit |
|---|---|---|
| SOC 2 Type II | ✅ Certified | 8 months ago (due for renewal in 4 months) |
| ISO 27001 | ❌ Not certified | N/A |
| GDPR | ⚠️ Partial compliance | Self-assessed (no audit) |
| CCPA | ⚠️ Partial compliance | Self-assessed (no audit) |
| HIPAA | ❌ Not applicable | N/A |

---

## 6) Identity & Access Management

| Item | Value |
|---|---|
| **Primary IdP** | Okta (workforce identity) |
| **Customer IdP** | Auth0 (built into platform for customer users) |
| **MFA coverage** | 85% (admin/eng required, business users optional) |
| **SSO integrations** | 12 apps (Slack, GitHub, AWS, Google Workspace, etc.) |
| **Privileged access** | AWS IAM + CyberArk (limited deployment - 15 users) |
| **Password policy** | 12 char minimum, 90-day rotation (admins only) |

---

## 7) Business Continuity & Disaster Recovery

| Item | Value |
|---|---|
| **DR strategy** | Warm standby (eu-west-1 region) |
| **RPO** | 4 hours |
| **RTO** | 8 hours |
| **Backup strategy** | AWS Backup (RDS snapshots daily, S3 versioning) |
| **Backup retention** | 30 days (production), 7 days (non-prod) |
| **DR testing** | Last test: 14 months ago (failed to meet RTO) |
| **Runbook documentation** | ⚠️ Incomplete (only 40% of scenarios documented) |

### BCDR Gaps Identified

| Gap | Severity | Impact |
|---|---|---|
| DR testing overdue (14 months since last test) | HIGH | Unknown recovery capability |
| RTO not validated (last test failed) | HIGH | Business continuity risk |
| Backup retention too short (30 days) | MEDIUM | Regulatory/compliance risk |
| Runbook coverage incomplete (40%) | MEDIUM | Recovery delays, knowledge dependency |

---

## 8) IT Organization Structure

| Metric | Value |
|---|---:|
| **Total IT headcount** | **67** |
| **Engineering** | 48 (includes platform, infra, SRE, security) |
| **IT Operations** | 12 (SRE, support, infra) |
| **InfoSec** | 5 (security engineering, compliance, GRC) |
| **IT Leadership** | 2 (CTO, VP Engineering) |
| **Outsourced/contractors** | 8 FTE equivalents (15% of IT workforce) |

### Team Breakdown

| Team | Headcount | Focus Area |
|---|---:|---|
| Engineering Leadership | 2 | CTO, VP Engineering |
| Platform Engineering | 18 | Core SaaS platform development |
| Infrastructure & SRE | 12 | AWS, Kubernetes, observability |
| Security Engineering | 5 | AppSec, CloudSec, compliance |
| DevOps & Release | 8 | CI/CD, deployments, tooling |
| Data Engineering | 6 | Data pipelines, analytics platform |
| IT Support & Operations | 8 | Employee IT, SaaS admin, vendor mgmt |
| Contractors (Offshore) | 8 | QA automation, infra support |

---

## 9) Key Vendor Relationships

| Vendor | Category | Annual Spend | Contract End | Auto-Renew |
|---|---|---:|---|---|
| AWS | Cloud infrastructure | $4,800,000 | Evergreen | Pay-as-you-go |
| Salesforce | CRM | $245,000 | 8 months | Yes |
| GitHub | Code repository & CI/CD | $156,000 | 14 months | Yes |
| Datadog | Observability & monitoring | $312,000 | 3 months | Yes |
| Okta | Identity & SSO | $98,000 | 6 months | Yes |
| CrowdStrike | Endpoint security | $87,000 | 11 months | Yes |
| PagerDuty | Incident management | $64,000 | 5 months | Yes |
| Wiz | Cloud security posture | $125,000 | 2 months | Yes |

---

## 10) Deal Context & Integration Considerations

### Business Rationale (Buyer Perspective)

| Factor | Rationale |
|---|---|
| **Strategic fit** | Adds customer engagement capabilities to ESG's enterprise suite |
| **Customer overlap** | ~15% overlap (cross-sell opportunity) |
| **Technology fit** | Modern API-first platform complements ESG's legacy systems |
| **Market expansion** | Accelerates ESG's SaaS transformation |

### Key Integration Challenges (Preliminary)

| Challenge | Description | Priority |
|---|---|---|
| **Security maturity gap** | Target lacks ISO 27001, incomplete GDPR/CCPA | HIGH |
| **Compliance certification** | SOC 2 renewal needed in 4 months | HIGH |
| **Multi-tenant data isolation** | Validate data sovereignty for EU/APAC customers | HIGH |
| **Infrastructure standardization** | Align AWS account structure to ESG standards | MEDIUM |
| **DR capability validation** | Last DR test failed; RTO/RPO unproven | MEDIUM |
| **Identity integration** | Okta (target) vs. Azure AD (buyer) | MEDIUM |
| **Vendor consolidation** | Tool overlap (Datadog vs. ESG's Splunk, GitHub vs. GitLab) | LOW |

---

## 11) Preliminary Risk Assessment

| Risk Area | Risk Description | Severity | Mitigation Needed |
|---|---|---|---|
| **Security compliance** | SOC 2 renewal due in 4 months; no ISO 27001 | 🔴 HIGH | Accelerate compliance audit; budget $150K-250K |
| **DR readiness** | Last DR test failed 14 months ago; RTO unproven | 🔴 HIGH | Execute DR test; budget $50K-100K for runbook remediation |
| **Data sovereignty** | GDPR/CCPA compliance unaudited; EU data residency unclear | 🟠 MEDIUM | Legal review + compliance audit; $75K-150K |
| **Key person dependency** | CTO founded company; deep knowledge concentration | 🟠 MEDIUM | Retention agreement + knowledge transfer plan |
| **Infrastructure tech debt** | AWS account sprawl; inconsistent tagging/governance | 🟡 LOW | 6-month cleanup project; $50K-100K |

---

## 12) Preliminary One-Time Cost Estimates

| Cost Category | Description | Estimated Range |
|---|---|---:|
| **Security remediation** | ISO 27001 certification, GDPR/CCPA audit, gap closure | $250K - $500K |
| **Compliance certification** | SOC 2 renewal acceleration, documentation update | $100K - $150K |
| **DR capability build** | Runbook completion, DR testing, RTO validation | $75K - $125K |
| **Infrastructure standardization** | AWS account restructure, tagging, governance | $50K - $100K |
| **Identity integration** | Okta → Azure AD migration planning (phased) | $100K - $200K |
| **Vendor rationalization** | Tool consolidation, contract negotiations | $25K - $50K |
| **Knowledge transfer** | Documentation, training, process alignment | $50K - $100K |
| **TOTAL ESTIMATED ONE-TIME COSTS** | | **$650K - $1.225M** |

---

## 13) Documentation Gaps Identified

> **Note:** The following gaps will be evident during AI analysis and should generate VDR requests.

| Gap Category | Missing Information | Impact on Analysis |
|---|---|---|
| **Network architecture** | No network diagram; VPC peering/Transit Gateway topology unclear | Cannot assess network segmentation/blast radius |
| **Integration inventory** | API integrations with customer systems undocumented | Cannot assess carve-out complexity |
| **Contract details** | Vendor contracts lack termination clauses, liability caps | Cannot assess vendor risk/exit costs |
| **BCDR runbooks** | Only 40% of failure scenarios documented | Cannot validate recovery capability |
| **Security controls** | No control matrix; NIST CSF/CIS alignment unknown | Cannot assess security maturity |
| **Org chart** | No formal reporting structure beyond team names | Cannot assess leadership depth/succession |

---

## 14) Consistency Anchor (For Cross-Document Validation)

| Fact | Value | Should Match In |
|---|---:|---|
| Total applications | 38 | Document 2 |
| Total app cost | $2,331,500 | Document 2 |
| Cloud provider | AWS | Document 3 |
| AWS accounts | 9 | Document 3 |
| AWS annual spend | $4,800,000 | Document 3 |
| IT headcount | 67 | Document 6 |
| Outsourced % | 15% (8 FTE) | Document 6 |
| SOC 2 status | Certified (renewal in 4 months) | Document 4 |
| DR strategy | Warm standby | Document 3 |
| RPO / RTO | 4h / 8h | Document 3 |

---

**END OF DOCUMENT 1**
