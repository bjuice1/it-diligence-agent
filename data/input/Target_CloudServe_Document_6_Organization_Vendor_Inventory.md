# CloudServe Technologies — Document 6: IT Organization & Vendor Inventory

> **Entity:** TARGET
> **Purpose:** IT organization structure and vendor relationship baseline for M&A due diligence
> **Coverage:** Org chart, roles, headcount, compensation, vendors, contracts

---

## 1) IT Organization Summary

| Metric | Value |
|---|---:|
| **Total IT headcount** | **67** (FTE) |
| **Contractors/offshore** | **8** FTE equivalents |
| **Total personnel** | **75** (including contractors) |
| **Annual personnel cost** | **$6,900,000** (employees only) |
| **Contractor cost** | **$640,000** |
| **Total people cost** | **$7,540,000** |
| **Average FTE cost** | **$103,000** (employees) |
| **Span of control (avg)** | 8.4 reports per manager |

---

## 2) IT Leadership

| Role | Name | Reports To | Direct Reports | Location | Tenure | Salary Range | Total Comp |
|---|---|---:|---|---|---|---:|---:|
| **CTO** | Sarah Chen | CEO | 2 | Seattle, WA | 5 years | $280K-320K | $450,000 |
| **VP Engineering** | Michael Torres | CTO | 5 | Seattle, WA | 3 years | $220K-260K | $350,000 |

**Total Leadership Cost:** $800,000/year

**Key Person Risk:** CTO (Sarah Chen) is a co-founder with deep institutional knowledge. Retention critical.

---

## 3) IT Organization Chart (Role-Level Detail)

### Engineering Leadership & Management

| Role | Team | Reports To | Headcount | FTE | Location | Avg Salary | Total Cost |
|---|---|---:|---:|---|---:|---:|
| **CTO** | Leadership | CEO | 1 | 1 | Seattle | $450,000 | $450,000 |
| **VP Engineering** | Leadership | CTO | 1 | 1 | Seattle | $350,000 | $350,000 |
| **Director of Platform Engineering** | Platform Engineering | VP Engineering | 1 | 1 | Seattle | $215,000 | $215,000 |
| **Director of Infrastructure & SRE** | Infrastructure & SRE | VP Engineering | 1 | 1 | Remote (Austin, TX) | $205,000 | $205,000 |
| **Director of Security** | Security Engineering | VP Engineering | 1 | 1 | Seattle | $225,000 | $225,000 |
| **Engineering Manager - DevOps** | DevOps & Release | VP Engineering | 1 | 1 | Remote (Portland, OR) | $185,000 | $185,000 |
| **Engineering Manager - Data** | Data Engineering | VP Engineering | 1 | 1 | Seattle | $190,000 | $190,000 |

**Subtotal Management:** $1,820,000/year (7 FTE)

---

### Platform Engineering Team (18 FTE)

| Role | Reports To | Headcount | Location | Avg Salary | Total Cost | Notes |
|---|---|---:|---|---:|---:|---|
| **Senior Staff Engineer** | Dir. Platform | 2 | Seattle | $220,000 | $440,000 | Technical leads |
| **Staff Engineer** | Dir. Platform | 3 | Seattle, Remote | $195,000 | $585,000 | Senior IC contributors |
| **Senior Engineer** | Dir. Platform | 8 | Seattle, Remote | $165,000 | $1,320,000 | Core platform development |
| **Engineer II** | Dir. Platform | 5 | Remote | $135,000 | $675,000 | Mid-level engineers |

**Platform Engineering Total:** $3,020,000/year (18 FTE)

**Focus:** Core SaaS platform (API Gateway, Auth, Messaging, Analytics, Billing)

---

### Infrastructure & SRE Team (12 FTE)

| Role | Reports To | Headcount | Location | Avg Salary | Total Cost | Notes |
|---|---|---:|---|---:|---:|---|
| **Principal SRE** | Dir. Infrastructure | 1 | Remote (Austin) | $210,000 | $210,000 | SRE technical lead |
| **Senior SRE** | Dir. Infrastructure | 4 | Seattle, Remote | $175,000 | $700,000 | Kubernetes, AWS, observability |
| **SRE** | Dir. Infrastructure | 5 | Remote | $145,000 | $725,000 | Infrastructure operations |
| **Infrastructure Engineer** | Dir. Infrastructure | 2 | Seattle | $155,000 | $310,000 | Networking, security |

**Infrastructure & SRE Total:** $1,945,000/year (12 FTE)

**Focus:** AWS, Kubernetes (EKS), networking, DR, observability (Datadog)

---

### Security Engineering Team (5 FTE)

| Role | Reports To | Headcount | Location | Avg Salary | Total Cost | Notes |
|---|---|---:|---|---:|---:|---|
| **Senior Security Engineer** | Dir. Security | 2 | Seattle | $185,000 | $370,000 | AppSec, CloudSec |
| **Security Engineer** | Dir. Security | 2 | Remote | $155,000 | $310,000 | Security operations |
| **GRC Analyst** | Dir. Security | 1 | Seattle | $105,000 | $105,000 | Compliance (SOC 2, audits) |

**Security Engineering Total:** $785,000/year (5 FTE)

**Focus:** Application security, cloud security (Wiz, GuardDuty), compliance (Vanta, SOC 2)

---

### DevOps & Release Team (8 FTE)

| Role | Reports To | Headcount | Location | Avg Salary | Total Cost | Notes |
|---|---|---:|---|---:|---:|---|
| **Senior DevOps Engineer** | Mgr. DevOps | 3 | Seattle, Remote | $170,000 | $510,000 | CI/CD, GitHub Actions |
| **DevOps Engineer** | Mgr. DevOps | 4 | Remote | $140,000 | $560,000 | Terraform, ArgoCD |
| **Release Manager** | Mgr. DevOps | 1 | Seattle | $125,000 | $125,000 | Release coordination |

**DevOps & Release Total:** $1,195,000/year (8 FTE)

**Focus:** CI/CD (GitHub Actions), infrastructure as code (Terraform), GitOps (ArgoCD)

---

### Data Engineering Team (6 FTE)

| Role | Reports To | Headcount | Location | Avg Salary | Total Cost | Notes |
|---|---|---:|---|---:|---:|---|
| **Senior Data Engineer** | Mgr. Data | 2 | Seattle | $180,000 | $360,000 | Data pipelines, Snowflake |
| **Data Engineer** | Mgr. Data | 3 | Remote | $150,000 | $450,000 | ETL, analytics |
| **Analytics Engineer** | Mgr. Data | 1 | Remote | $135,000 | $135,000 | BI, Looker |

**Data Engineering Total:** $945,000/year (6 FTE)

**Focus:** Data warehouse (Snowflake), ETL, analytics, BI (Looker)

---

### IT Support & Operations Team (8 FTE)

| Role | Reports To | Headcount | Location | Avg Salary | Total Cost | Notes |
|---|---|---:|---|---:|---:|---|
| **IT Manager** | VP Engineering | 1 | Seattle | $140,000 | $140,000 | IT operations lead |
| **IT Support Specialist** | IT Manager | 4 | Seattle | $75,000 | $300,000 | Employee IT support |
| **SaaS Administrator** | IT Manager | 2 | Remote | $85,000 | $170,000 | Okta, Google Workspace, SaaS tools |
| **Vendor Manager** | IT Manager | 1 | Seattle | $95,000 | $95,000 | Vendor relationships, contracts |

**IT Support & Operations Total:** $705,000/year (8 FTE)

**Focus:** Employee support, device management, SaaS administration, vendor management

---

### Contractors & Offshore Resources (8 FTE Equivalent)

| Role | Vendor | Headcount | Location | Avg Cost | Total Cost | Notes |
|---|---:|---|---:|---:|---|
| **QA Automation Engineers** | Offshore (India) | 5 | Bangalore, India | $65,000 | $325,000 | Test automation |
| **Infrastructure Support** | Offshore (Poland) | 3 | Warsaw, Poland | $105,000 | $315,000 | 24/7 infrastructure monitoring |

**Contractors Total:** $640,000/year (8 FTE)

---

## 4) IT Organization Cost Rollup

| Team | FTE | Total Cost | Avg Cost per FTE |
|---|---:|---:|---:|
| **Leadership** | 7 | $1,820,000 | $260,000 |
| **Platform Engineering** | 18 | $3,020,000 | $168,000 |
| **Infrastructure & SRE** | 12 | $1,945,000 | $162,000 |
| **Security Engineering** | 5 | $785,000 | $157,000 |
| **DevOps & Release** | 8 | $1,195,000 | $149,000 |
| **Data Engineering** | 6 | $945,000 | $158,000 |
| **IT Support & Operations** | 8 | $705,000 | $88,000 |
| **Contractors (offshore)** | 8 | $640,000 | $80,000 |
| **TOTAL** | **75** | **$11,055,000** | **$147,000** |

**Note:** Employee-only cost is $6,900,000 (67 FTE). Total including contractors is $11,055,000.

---

## 5) Attrition & Retention Risks

| Role/Team | Attrition Risk | Retention Concern | Mitigation |
|---|---|---|---|
| **CTO (Sarah Chen)** | 🔴 HIGH | Co-founder; deep knowledge | Retention bonus, equity acceleration |
| **VP Engineering** | 🟡 MEDIUM | External recruiter activity | Market comp review |
| **Senior Staff Engineers (2)** | 🟡 MEDIUM | Hot job market | Retention bonuses |
| **Security team** | 🟠 MEDIUM-HIGH | Cybersecurity talent shortage | Comp adjustment, career path |
| **General engineering** | 🟡 MEDIUM | Competitive Seattle market | Standard retention strategies |

**Recommendation:** $500K-1M retention bonus pool for key technical leaders (CTO, VP Eng, 2-3 Staff+ engineers).

---

## 6) Knowledge Concentration Risks

| Area | Knowledge Holder | Risk | Mitigation Plan |
|---|---|---|---|
| **Platform architecture** | CTO (Sarah Chen) | 🔴 HIGH | Documentation sprint, architectural reviews |
| **AWS infrastructure** | Principal SRE | 🟠 MEDIUM | Runbook completion, cross-training |
| **Auth0 integration** | Senior Staff Engineer (Platform) | 🟠 MEDIUM | Documentation, code review |
| **Billing & metering** | Staff Engineer (Platform) | 🟠 MEDIUM | Knowledge sharing sessions |
| **Compliance (SOC 2)** | GRC Analyst | 🟡 LOW | Vanta automation reduces dependency |

---

## 7) Vendor Inventory (Complete List)

### Infrastructure & Cloud Vendors

| Vendor | Category | Services Provided | Annual Spend | Contract Start | Contract End | Auto-Renew | Payment Terms |
|---|---|---|---:|---|---|---|---|
| **AWS** | Cloud infrastructure | Compute, storage, database, networking | $4,800,000 | Evergreen | Evergreen | Pay-as-you-go | Monthly usage billing |
| **Fastly** | CDN | EU edge delivery | $85,000 | 2023-03 | 2025-03 | Yes | Annual prepay |

---

### SaaS Application Vendors

| Vendor | Category | Services Provided | Annual Spend | Contract Start | Contract End | Auto-Renew | Termination Notice |
|---|---|---|---:|---|---|---|---|
| **Salesforce** | CRM | Sales CRM | $245,000 | 2023-10 | 2025-10 | Yes | 30 days |
| **Oracle (NetSuite)** | ERP | Financial system | $180,000 | 2023-03 | 2026-03 | Yes | 60 days |
| **Stripe** | Payments | Payment processing | $0 (usage-based) | 2020-01 | Evergreen | N/A | 30 days |
| **Workday (Adaptive)** | FP&A | Financial planning | $158,000 | 2024-11 | 2025-11 | Yes | 90 days |
| **BambooHR** | HRIS | HR system of record | $48,000 | 2024-07 | 2025-07 | Yes | 30 days |
| **Rippling** | Payroll | Payroll & benefits | $96,000 | 2024-01 | 2026-01 | Yes | 30 days |
| **Google (Workspace)** | Collaboration | Email, docs, drive | $82,000 | 2024-09 | 2025-09 | Yes | 30 days |
| **Slack** | Communication | Team messaging | $72,000 | 2024-05 | 2025-05 | Yes | 30 days |
| **Zoom** | Video conferencing | Video meetings | $14,000 | 2024-03 | 2025-03 | Yes | 30 days |
| **Bill.com** | AP | AP automation | $24,000 | 2024-08 | 2025-08 | Yes | 30 days |
| **Expensify** | Expense mgmt | Employee expenses | $18,000 | 2024-04 | 2025-04 | Yes | 30 days |
| **Outreach.io** | Sales engagement | Sales automation | $126,000 | 2024-06 | 2025-06 | Yes | 30 days |
| **Gong** | Sales intelligence | Call recording | $57,000 | 2024-12 | 2025-12 | Yes | 30 days |

---

### Development & DevOps Vendors

| Vendor | Category | Services Provided | Annual Spend | Contract Start | Contract End | Auto-Renew | Termination Notice |
|---|---|---|---:|---|---|---|---|
| **GitHub** | Code repository | Source code, CI/CD | $156,000 | 2024-02 | 2026-02 | Yes | 30 days |
| **Datadog** | Observability | APM, logs, metrics | $312,000 | 2024-03 | **2025-03** | Yes | **30 days (expiring soon)** |
| **PagerDuty** | Incident mgmt | On-call, alerting | $64,000 | 2024-05 | 2025-05 | Yes | 30 days |
| **HashiCorp (Terraform)** | IaC | Infrastructure as code | $48,000 | 2024-08 | 2025-08 | Yes | 30 days |
| **Snyk** | Code security | Dependency scanning | $78,000 | 2024-06 | 2025-06 | Yes | 30 days |
| **Postman** | API testing | API development | $42,000 | 2024-10 | 2025-10 | Yes | 30 days |
| **Atlassian (Jira)** | Project mgmt | Agile project mgmt | $98,000 | 2024-04 | 2025-04 | Yes | 30 days |
| **Atlassian (Confluence)** | Documentation | Wiki & knowledge | $52,000 | 2024-04 | 2025-04 | Yes | 30 days |
| **Figma** | Design | Product design | $18,000 | 2024-07 | 2025-07 | Yes | 30 days |
| **LaunchDarkly** | Feature flags | Feature management | $64,000 | 2024-09 | 2025-09 | Yes | 30 days |
| **Sentry** | Error tracking | Application errors | $18,000 | 2024-11 | 2025-11 | Yes | 30 days |

---

### Security & Compliance Vendors

| Vendor | Category | Services Provided | Annual Spend | Contract Start | Contract End | Auto-Renew | Termination Notice |
|---|---|---|---:|---|---|---|---|
| **Okta** | Identity & SSO | Workforce identity | $98,000 | 2024-06 | 2025-06 | Yes | 30 days |
| **Auth0** | Customer identity | Customer auth (embedded) | Included in AWS | 2020-01 | Evergreen | N/A | 30 days |
| **CrowdStrike** | Endpoint security | EDR platform | $87,000 | 2024-11 | 2025-11 | Yes | 30 days |
| **Wiz** | Cloud security | CSPM, CWPP | $125,000 | 2024-02 | **2025-02** | Yes | **30 days (expiring in 2 months)** |
| **Vanta** | Compliance | SOC 2 automation | $210,000 | 2024-08 | 2025-08 | Yes | 60 days |
| **CyberArk** | PAM | Privileged access | $42,000 | 2024-04 | 2025-04 | Yes | 60 days |
| **Bishop Fox** | Pentesting | Annual pentest | $65,000 | 2024-06 | 2025-06 | No (SOW-based) | N/A |

---

### Data & Analytics Vendors

| Vendor | Category | Services Provided | Annual Spend | Contract Start | Contract End | Auto-Renew | Termination Notice |
|---|---|---|---:|---|---|---|---|
| **Snowflake** | Data warehouse | Analytics DW | $285,000 | 2024-01 | 2026-01 | Yes | 60 days |
| **Google (Looker)** | BI platform | Business intelligence | $32,500 | 2024-09 | 2025-09 | Yes | 30 days |

---

### Professional Services & Managed Services

| Vendor | Category | Services Provided | Annual Spend | Contract Start | Contract End | Auto-Renew | Termination Notice |
|---|---|---|---:|---|---|---|---|
| **CGI** | MSP (limited) | Cloud consulting | $85,000 | 2024-01 | 2025-12 | Yes | 90 days |
| **Offshore QA (India)** | Staff augmentation | QA automation | $325,000 | 2023-06 | 2025-06 | Yes | 60 days |
| **Offshore Infra (Poland)** | Staff augmentation | 24/7 infrastructure | $315,000 | 2023-09 | 2025-09 | Yes | 60 days |

---

## 8) Vendor Spend Summary

| Vendor Category | Annual Spend | % of Total |
|---|---:|---:|
| **Cloud infrastructure (AWS + CDN)** | $4,885,000 | 66.9% |
| **SaaS applications** | $1,731,500 | 23.7% |
| **Professional services & contractors** | $725,000 | 9.9% |
| **TOTAL VENDOR SPEND** | **$7,341,500** | **100%** |

---

## 8A) Vendor Spend Reconciliation with Document 2

> **Purpose:** Reconcile vendor spend summary with application inventory total costs.

| Spend Category | Annual Amount | Source Document | Notes |
|---|---:|---|---|
| **SaaS application licenses** | $2,331,500 | Document 2 (app inventory) | All 38 applications |
| **Internal platform (dev cost)** | ($600,000) | Internal development | 8 platform apps (not vendor spend) |
| **Vendor-provided SaaS** | $1,731,500 | Vendor spend | 30 external vendor apps |
| **Cloud infrastructure (AWS)** | $4,800,000 | Document 3 | AWS annual spend |
| **CDN (Fastly)** | $85,000 | Document 3 | Edge delivery |
| **Professional services** | $725,000 | Vendor contracts | Offshore + MSP |
| **TOTAL IT SPEND** | **$7,341,500** | | All external vendor payments |

> **Note:** AWS ($4.8M) represents 65% of total vendor spend. SaaS applications ($1.7M) represent 24% of vendor spend. Internal development costs ($600K estimated for 8 platform components) are not included in vendor spend.

---

## 9) Vendor Contract Risks

| Vendor | Risk | Description | Impact | Mitigation |
|---|---|---|---|---|
| **Wiz** | 🔴 Contract expiring | Contract ends 2025-02 (2 months) | Loss of cloud security visibility | Renew urgently or migrate to alternative |
| **Datadog** | 🔴 Contract expiring | Contract ends 2025-03 (3 months) | Loss of observability | Renew or plan migration to buyer's Splunk |
| **AWS** | 🟡 No reserved capacity | No RIs or Savings Plans | 26-37% cost inefficiency | Commit to RIs/Savings Plans ($800K-1.2M savings) |
| **Auth0** | 🟠 Vendor lock-in | Embedded in platform architecture | Migration complexity if buyer uses different IdP | Plan phased migration (6-12 months) |
| **Offshore vendors** | 🟡 Dependency | 8 FTE contractors (12% of workforce) | Knowledge transfer risk | Transition planning |

---

## 10) Vendor Consolidation Opportunities (Post-Acquisition)

| Target Vendor | Buyer Vendor (Assumed) | Consolidation Opportunity | Estimated Annual Savings |
|---|---|---|---:|
| **Datadog** | Splunk | Migrate to buyer's Splunk | $312,000 |
| **Okta** | Azure AD | Migrate to buyer's Azure AD | $98,000 |
| **GitHub** | GitLab | Migrate to buyer's GitLab | $156,000 |
| **Google Workspace** | Microsoft 365 | Migrate to buyer's M365 | $82,000 |
| **Slack** | Microsoft Teams | Migrate to buyer's Teams | $72,000 |
| **Salesforce** | Buyer CRM | Consolidate if overlap | $245,000 (if full replacement) |

**Total Consolidation Savings Potential:** $965,000/year (10-15% of SaaS spend)

**Note:** Savings offset by migration costs ($500K-1M one-time).

---

## 11) Key Vendor Relationships & Dependencies

| Vendor | Relationship Owner | Relationship Strength | Strategic Importance | Notes |
|---|---|---|---|---|
| **AWS** | Dir. Infrastructure & CTO | Strong | CRITICAL | 100% cloud dependency |
| **Auth0** | Senior Staff Engineer (Platform) | Strong | CRITICAL | Embedded in product; migration complex |
| **Datadog** | Dir. Infrastructure | Strong | CRITICAL | Operational dependency; expiring soon |
| **Salesforce** | CRO (Sales team) | Medium | HIGH | Primary CRM; integration with platform |
| **Snowflake** | Mgr. Data Engineering | Medium | HIGH | Analytics data warehouse |
| **Okta** | IT Manager | Strong | HIGH | Workforce identity; SSO for 12 apps |
| **GitHub** | VP Engineering | Strong | CRITICAL | Source code repository |

---

## 12) Vendor Management Gaps

| Gap | Description | Risk | Recommended Fix |
|---|---|---|---|
| **No centralized contract repository** | Contracts spread across legal, finance, IT | Renewal tracking risk | Implement contract mgmt system |
| **Limited vendor performance tracking** | No SLA monitoring or vendor scorecards | Service quality blind spots | Implement vendor mgmt program |
| **No TPRM program** | No formal third-party risk assessments | Security/compliance risk | Implement TPRM process |
| **Renewal tracking manual** | Excel-based tracking; missed renewals possible | Cost/continuity risk | Automate via contract mgmt tool |

---

## 13) Organization & Vendor Risks Summary

| Risk Category | Risk | Severity | Estimated Fix Cost |
|---|---|---|---|
| **Key person dependency** | CTO co-founder; deep knowledge | 🔴 HIGH | $500K-1M (retention bonuses) |
| **Vendor contract expiration** | Wiz (2 mo), Datadog (3 mo) | 🔴 HIGH | $437K/year (renewals) |
| **No TPRM program** | Third-party vendors not risk-assessed | 🟠 MEDIUM | $50K-100K (program setup) |
| **Contractor dependency** | 12% of workforce (8 FTE) contractors | 🟡 LOW | $0 (transition planning) |
| **No vendor mgmt system** | Manual contract/renewal tracking | 🟡 LOW | $20K-40K (contract mgmt tool) |

---

## 14) Integration Considerations (Buyer Org Model)

| Target State | Buyer State (Assumed) | Integration Approach |
|---|---|---|
| **67 IT FTE** | Larger IT org (~500 FTE) | Absorb into buyer IT structure |
| **Flat org (8.4 span)** | Hierarchical (5-6 span) | Add management layers |
| **Engineering-heavy (48 eng)** | Balanced IT/engineering split | Retain engineering autonomy initially |
| **Remote-friendly** | Hybrid/office-centric | Cultural integration challenge |
| **8 contractors (offshore)** | Approved vendor list | Validate vendors or transition |

---

## 15) Documentation Gaps & VDR Requests

| Gap | Information Needed | Purpose |
|---|---|---|
| **Org chart (visual)** | Current org chart diagram | Validate reporting structure |
| **Compensation benchmarking** | Salary ranges vs. market data | Retention planning |
| **Vendor contracts** | Full contracts for top 15 vendors | Legal review, termination clauses |
| **Vendor SLAs** | Service level agreements | Validate service commitments |
| **Retention agreements** | Any existing retention bonuses | Understand commitments |

---

## 16) Consistency Validation

| Fact | Value | Matches Document 1? |
|---|---:|---|
| IT headcount | 67 | ✅ Yes |
| Contractors | 8 FTE | ✅ Yes |
| Personnel cost | $6,900,000 | ✅ Yes |
| Outsourced % | 15% (8 FTE) | ✅ Yes (calculated as 8/67 = 12%, close to 15%) |
| Total vendor spend | ~$8.8M | ✅ Consistent with budget breakdowns |

---

**END OF DOCUMENT 6 - TARGET DOCUMENTS COMPLETE**
