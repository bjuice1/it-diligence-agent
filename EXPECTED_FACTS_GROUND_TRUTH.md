# Expected Facts Ground Truth — IT Due Diligence Test Scenario

> **Purpose:** Validation ground truth for automation testing
> **Use Case:** Compare automation output against expected facts to measure accuracy
> **Test Scenario:** CloudServe (Target) acquisition by ESG (Buyer)
> **Last Updated:** 2026-02-13

---

## Executive Summary: Expected Fact Counts by Domain

| Domain | Target Facts Expected | Buyer Facts Expected | Total Expected |
|---|---:|---:|---:|
| **ORGANIZATION** | 15 | 9 | 24 |
| **APPLICATIONS** | 38 | 9 | 47 |
| **INFRASTRUCTURE** | 35 | 12 | 47 |
| **NETWORK** | 18 | 8 | 26 |
| **CYBERSECURITY** | 22 | 15 | 37 |
| **IDENTITY_ACCESS** | 28 | 14 | 42 |
| **EXECUTIVE_PROFILE** | 12 | 8 | 20 |
| **TOTAL** | **168** | **75** | **243** |

**Note:** These are HIGH-LEVEL facts (e.g., "38 applications" should be ONE fact, not 38 individual app facts). The automation should extract aggregated inventory items separately.

---

## 1. ORGANIZATION Domain — Expected Facts

### TARGET (CloudServe) — 15 Expected Facts

| Fact ID | Fact Category | Fact Description | Value/Details |
|---|---|---|---|
| F-TGT-ORG-001 | Headcount | Total IT headcount | 67 FTE |
| F-TGT-ORG-002 | Headcount | Contractors/offshore | 8 FTE equivalents |
| F-TGT-ORG-003 | Budget | Annual personnel cost | $6,900,000 (employees only) |
| F-TGT-ORG-004 | Budget | Contractor cost | $640,000 |
| F-TGT-ORG-005 | Budget | Total people cost | $7,540,000 |
| F-TGT-ORG-006 | Leadership | CTO | Sarah Chen (co-founder, 5 years tenure, $450K total comp) |
| F-TGT-ORG-007 | Leadership | VP Engineering | Michael Torres (3 years tenure, $350K total comp) |
| F-TGT-ORG-008 | Team | Platform Engineering | 18 FTE, $3,020,000/year |
| F-TGT-ORG-009 | Team | Infrastructure & SRE | 12 FTE, $1,945,000/year |
| F-TGT-ORG-010 | Team | Security Engineering | 5 FTE, $785,000/year |
| F-TGT-ORG-011 | Team | DevOps & Release | 8 FTE, $1,195,000/year |
| F-TGT-ORG-012 | Team | Data Engineering | 6 FTE, $945,000/year |
| F-TGT-ORG-013 | Team | IT Support & Operations | 8 FTE, $705,000/year |
| F-TGT-ORG-014 | Outsourcing | Offshore QA (India) | 5 FTE, $325,000/year |
| F-TGT-ORG-015 | Outsourcing | Offshore Infrastructure (Poland) | 3 FTE, $315,000/year |

**Total: 15 facts**

### BUYER (ESG) — 9 Expected Facts

| Fact ID | Fact Category | Fact Description | Value/Details |
|---|---|---|---|
| F-BYR-ORG-001 | Headcount | Total IT headcount | 2,100 FTE |
| F-BYR-ORG-002 | Headcount | Corporate IT | 850 FTE |
| F-BYR-ORG-003 | Headcount | Product Engineering | 1,250 FTE |
| F-BYR-ORG-004 | Headcount | Contractors/offshore | 320 FTE equivalents (13%) |
| F-BYR-ORG-005 | Budget | Annual IT budget | $2.1B |
| F-BYR-ORG-006 | Budget | Personnel cost | $1.2B/year |
| F-BYR-ORG-007 | Leadership | CISO | Reports to CIO, 180 FTE global security org |
| F-BYR-ORG-008 | Team | M&A Integration Team | 25 FTE dedicated to acquisitions |
| F-BYR-ORG-009 | Presence | Global presence | 45 countries, 120 offices |

**Total: 9 facts**

---

## 2. APPLICATIONS Domain — Expected Inventory Counts

### TARGET (CloudServe) — 38 Applications Expected

**Summary Counts:**
- **Total applications:** 38
- **Core platform components:** 8 (internal/custom-built)
- **Business applications:** 18 (SaaS subscriptions)
- **Development tools:** 12 (DevOps, monitoring, testing)
- **Annual app cost:** $2,331,500

**Expected Inventory Items by Category:**

| Category | Count | Examples |
|---|---:|---|
| **Infrastructure** | 9 | 8 platform components + Datadog |
| **CRM** | 3 | Salesforce, Outreach.io, Gong |
| **ERP** | 1 | NetSuite |
| **Finance** | 4 | Stripe, Bill.com, Expensify, Adaptive Insights |
| **HCM** | 2 | BambooHR, Rippling |
| **Collaboration** | 3 | Google Workspace, Slack, Zoom |
| **DevOps** | 9 | GitHub, Datadog, PagerDuty, Terraform, ArgoCD, Snyk, Postman, LaunchDarkly, Sentry |
| **Productivity** | 3 | Jira, Confluence, Figma |
| **Security** | 5 | Okta, CrowdStrike, Wiz, Vanta, (implicit: auth in apps) |
| **Database** | 1 | Snowflake |
| **BI/Analytics** | 1 | Looker |

**Critical Applications (CRITICAL criticality):**
1. API Gateway Service (internal)
2. Authentication Service (internal)
3. Customer Data Service (internal)
4. Messaging Service (internal)
5. NetSuite (ERP)
6. Stripe (payments)
7. Google Workspace
8. GitHub Enterprise
9. Datadog
10. Okta
11. CrowdStrike

**Contract Expiring Soon (<= 4 months):**
- Wiz: 2025-02 (2 months)
- Datadog: 2025-03 (3 months)
- Zoom: 2025-03 (3 months)
- Expensify: 2025-04 (4 months)

### BUYER (ESG) — 9 Core Applications Expected

| Application | Category | Vendor | Users | Annual Cost |
|---|---|---|---:|---:|
| SAP S/4HANA Cloud | ERP | SAP | 12,400 | $18,500,000 |
| Microsoft Dynamics 365 Sales | CRM | Microsoft | 3,200 | $9,800,000 |
| Workday HCM | HCM | Workday | 24,500 | $12,200,000 |
| SAP S/4HANA + BlackLine | Finance | SAP, BlackLine | 1,800 | $6,400,000 |
| SAP Ariba | Procurement | SAP | 2,100 | $3,200,000 |
| Microsoft 365 E5 | Collaboration | Microsoft | 24,500 | $14,700,000 |
| Microsoft Teams | Communication | Microsoft | 24,500 | Included in M365 |
| Power BI Premium | BI | Microsoft | 4,800 | $2,400,000 |
| ServiceNow ITSM | ITSM | ServiceNow | 2,100 | $4,200,000 |

**Total: 9 applications**

---

## 3. INFRASTRUCTURE Domain — Expected Facts

### TARGET (CloudServe) — 35 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **Cloud Provider** | 1 | AWS (100% cloud) |
| **AWS Accounts** | 9 | Prod, staging, dev, shared-services, data, security, 3× sandbox |
| **AWS Spend** | 1 | $4.8M/year ($400K/month) |
| **Regions** | 2 | us-east-1 (primary), eu-west-1 (DR) |
| **Data Centers** | 1 | 0 (cloud-only) |
| **Compute** | 4 | EKS clusters (4), total 47 nodes, Lambda functions |
| **Databases** | 5 | RDS PostgreSQL, Aurora, DynamoDB, ElastiCache Redis |
| **Storage** | 3 | S3 (18TB), EBS (120TB), EFS (500GB) |
| **Networking** | 5 | 4 VPCs, Transit Gateway, Direct Connect (1Gbps), NAT Gateways, CDN (CloudFront + Fastly) |
| **DR Strategy** | 4 | Warm standby, eu-west-1, RPO 4h, RTO 8h, last test 14 months ago (FAILED) |

**Infrastructure Gaps:**
- No EU data residency (GDPR risk)
- DR test failed (RTO missed: 12h actual vs 8h target)
- No Reserved Instances or Savings Plans ($800K-1.2M/year savings opportunity)
- No Shield Advanced (Layer 7 DDoS vulnerability)

**Total: ~35 facts (accounts, services, DR, gaps)**

### BUYER (ESG) — 12 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **Cloud Strategy** | 3 | Azure-first (70%), AWS accepted (25%), GCP limited (5%) |
| **Azure Spend** | 1 | $650M/year |
| **AWS Spend** | 1 | $180M/year (legacy acquisitions) |
| **Azure Regions** | 5 | East US, West Europe, Southeast Asia, UK South, Australia East |
| **Data Center Exit** | 1 | Complete by 2027 |
| **Standards** | 1 | AKS (Azure), EKS accepted for acquisitions |

**Total: 12 facts**

---

## 4. NETWORK Domain — Expected Facts

### TARGET (CloudServe) — 18 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **Network Model** | 1 | Cloud-native (AWS VPC) |
| **VPCs** | 4 | Prod, non-prod, shared, EU prod |
| **Connectivity** | 3 | Direct Connect (1Gbps), AWS Client VPN (150 users), Tailscale (50 users) |
| **Security Controls** | 4 | AWS Security Groups, AWS WAF, AWS Shield Standard, NACLs |
| **Network Segmentation** | 4 | Public subnets, private app subnets, private data subnets, management subnet |
| **Remote Access** | 3 | AWS Client VPN, Tailscale, Bastion hosts |

**Network Gaps:**
- No Shield Advanced (DDoS protection gap)
- No external vulnerability scanning
- No session recording for bastion hosts

**Total: 18 facts**

### BUYER (ESG) — 8 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **Network Standards** | 4 | Azure Virtual WAN, ExpressRoute, Azure VPN Gateway, Zscaler (cloud proxy) |
| **Requirements** | 4 | ExpressRoute for ESG connectivity, SD-WAN (Virtual WAN), DDoS Standard, Encryption at rest/transit |

**Total: 8 facts**

---

## 5. CYBERSECURITY Domain — Expected Facts

### TARGET (CloudServe) — 22 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **Security Tools** | 6 | CrowdStrike Falcon ($87K), Wiz ($125K, expiring), Snyk ($78K), GuardDuty ($60K), WAF ($48K), Vanta ($210K) |
| **Compliance** | 4 | SOC 2 Type II (certified, renewal in 4 mo), ISO 27001 (not certified), GDPR (self-assessed), CCPA (self-assessed) |
| **Vulnerability Management** | 5 | Code scanning (Snyk), container scanning (Snyk+ECR), cloud config (Wiz), network (AWS Inspector), pentest (annual, Bishop Fox) |
| **Vuln Remediation SLAs** | 3 | Critical: 7d SLA / 12d actual, High: 30d / 45d, Medium: 90d / 120d (ALL MISSING SLA) |
| **Encryption** | 4 | At rest (AES-256, AWS KMS), in transit (TLS 1.2+), backups (encrypted), east-west (partial - GAP) |

**Security Gaps:**
- Wiz contract expiring (2 months)
- SOC 2 renewal urgent (4 months)
- No ISO 27001 certification
- MFA coverage 85% (62 users without MFA)
- 87 open vulnerabilities (12 critical, 34 high)
- No dedicated SIEM (Datadog Security Monitoring insufficient)
- No data classification enforcement / DLP

**Total: 22 facts**

### BUYER (ESG) — 15 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **Security Posture** | 4 | 180 FTE security team, $85M annual budget, 24/7/365 SOC (3 global), Quarterly pentests |
| **Mandatory Controls** | 7 | CrowdStrike (Day 1), Splunk SIEM (90d), Defender/Wiz CSPM (90d), Qualys (90d), CyberArk PAM (60d), MFA 100% (30d), Purview DLP (180d) |
| **Compliance** | 4 | SOC 2, ISO 27001, GDPR (audited), CCPA, PCI-DSS L1, HIPAA, FedRAMP (in progress) |

**Total: 15 facts**

---

## 6. IDENTITY_ACCESS Domain — Expected Facts

### TARGET (CloudServe) — 28 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **Workforce IdP** | 5 | Okta ($98K), 412 users, MFA 85% (350/412), SSO 12 apps, password policy 12 char / 90d rotation (admins) |
| **Customer IdP** | 4 | Auth0 (embedded), 1.8M end-user accounts, MFA optional (35% adopt), 287 SAML + 54 OIDC integrations |
| **Privileged Access** | 5 | CyberArk ($42K), 15 users covered, 26 privileged users NOT covered (GAP), session recording enabled, password vaulting partial |
| **AWS IAM** | 6 | AWS SSO enabled (Okta federated), 12 permission sets, 8 legacy IAM users (GAP), 9 root accounts (MFA enabled, CyberArk vaulted) |
| **MFA Coverage** | 8 | Executives 100%, Engineering 100%, IT/Security 100%, Sales 78%, Marketing 76%, Finance 89%, HR 100%, CS 73% |
| **Access Reviews** | 5 | Okta (quarterly, 2mo ago), AWS (quarterly, 4mo overdue), GitHub (quarterly, 3mo ago), DB (quarterly, 8mo overdue), PAM (monthly, 1mo ago) |

**IAM Gaps:**
- MFA 85% (15% gap = 62 users)
- PAM coverage limited (26 users uncovered)
- Manual app provisioning (6 apps, 50% of apps)
- Orphaned account risk (no automation)
- Legacy IAM users (8 need migration to SSO)
- MSP vendor has no MFA (CGI)
- Access reviews overdue (AWS 4mo, DB 8mo)

**Total: 28 facts**

### BUYER (ESG) — 14 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **IAM Architecture** | 6 | Azure AD (24,500 users), Azure AD B2C (customer IdP), Azure AD MFA (100%), SSO (180+ apps), CyberArk (1,200 users), SailPoint IGA |
| **Requirements** | 8 | MFA 100% (30d), PAM all admins (60d), Azure AD federation (30d), Okta→Azure AD (6-12mo), Auth0→Azure AD B2C (18-24mo), SailPoint onboarding (6mo), Conditional Access policies, Legacy IAM cleanup (90d) |

**Total: 14 facts**

---

## 7. EXECUTIVE_PROFILE Domain — Expected Facts

### TARGET (CloudServe) — 12 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **Company Overview** | 6 | CloudServe Technologies, B2B SaaS, $87M revenue, 412 employees, 1,847 customers, Founded 2016 (8 years) |
| **IT Budget** | 4 | $14.2M annual (16.3% of revenue), $4.8M cloud, $2.1M SaaS, $6.9M personnel |
| **Key Risks** | 2 | Security compliance (SOC 2 renewal, no ISO), DR readiness (last test failed) |

**Total: 12 facts**

### BUYER (ESG) — 8 Expected Facts

| Fact Category | Expected Facts | Key Values |
|---|---|---|
| **Company Overview** | 5 | Enterprise Solutions Group, Enterprise software, $12.4B revenue, 24,500 employees, 2,100 IT FTE |
| **Integration Philosophy** | 3 | "Run then transform" (Day 1-100 stabilize), Platform autonomy (12-18mo), Corporate standards enforced (30-90d) |

**Total: 8 facts**

---

## Validation Criteria — Automation Accuracy Thresholds

### Fact Extraction Accuracy

| Domain | Expected Fact Count | Acceptable Range | Pass Threshold |
|---|---:|---|---|
| **ORGANIZATION** | 24 (15 target + 9 buyer) | 20-28 | ≥ 90% accuracy |
| **APPLICATIONS** | 47 inventory items | 42-52 | ≥ 90% match |
| **INFRASTRUCTURE** | 47 facts | 40-54 | ≥ 85% accuracy |
| **NETWORK** | 26 facts | 22-30 | ≥ 85% accuracy |
| **CYBERSECURITY** | 37 facts | 32-42 | ≥ 85% accuracy |
| **IDENTITY_ACCESS** | 42 facts | 36-48 | ≥ 85% accuracy |
| **EXECUTIVE_PROFILE** | 20 facts | 17-23 | ≥ 85% accuracy |

### Known Failure Modes to Test For

1. **Organization Fact Explosion**
   - **Expected:** 15 target org facts
   - **Common Failure:** 432 facts (one fact per table row instead of aggregated)
   - **Test:** Assert fact count ≤ 30 for organization domain

2. **Entity Detection Failure**
   - **Expected:** Facts correctly tagged as `entity: target` or `entity: buyer`
   - **Common Failure:** "Conflicting entity signals" error, all facts default to `entity: target`
   - **Test:** Assert both target and buyer facts exist for each domain

3. **Inventory Count Accuracy**
   - **Expected:** 38 target apps (as inventory items, not facts)
   - **Common Failure:** Counting facts instead of inventory items → inflated counts
   - **Test:** UI shows 38 apps, not 100+

4. **Reasoning Phase Missing**
   - **Expected:** Risks, work items, cost estimates generated
   - **Common Failure:** 0 risks, 0 work items, $0 cost estimates (reasoning phase not running)
   - **Test:** Assert findings_count > 0 after reasoning phase

---

## Cross-Document Consistency Checks

### Consistency Anchors (Values MUST Match Across Documents)

| Fact | Value | Appears In | Validation Rule |
|---|---:|---|---|
| **Total applications** | 38 | Doc 1 & Doc 2 | MUST match exactly |
| **Total app cost** | $2,331,500 | Doc 1 & Doc 2 | MUST match exactly |
| **AWS annual spend** | $4,800,000 | Doc 1, Doc 3, Doc 6 | MUST match exactly |
| **AWS accounts** | 9 | Doc 1 & Doc 3 | MUST match exactly |
| **IT headcount** | 67 | Doc 1 & Doc 6 | MUST match exactly |
| **Contractors** | 8 FTE | Doc 1 & Doc 6 | MUST match exactly |
| **Personnel cost** | $6,900,000 | Doc 1 & Doc 6 | MUST match exactly |
| **SOC 2 status** | Certified, renewal in 4 months | Doc 1 & Doc 4 | MUST match exactly |
| **DR strategy** | Warm standby, eu-west-1, RPO 4h, RTO 8h | Doc 1 & Doc 3 | MUST match exactly |
| **MFA coverage** | 85% (350/412 users) | Doc 1, Doc 4, Doc 5 | MUST match exactly |

---

## Gap Identification — Expected VDR Requests

The automation should identify these documentation gaps and generate VDR requests:

### TARGET (CloudServe) Expected Gaps

1. **Network architecture diagrams** (mentioned missing in Doc 1, 3, 4)
2. **API integration list** (customer-facing integrations undocumented — Doc 2)
3. **Auth0 configuration details** (tenant config, custom rules — Doc 2)
4. **Stripe integration details** (webhook configs — Doc 2)
5. **Vendor contracts** (top 10 vendors by spend — Doc 2, 6)
6. **Platform SLAs** (customer SLA commitments — Doc 2)
7. **Data retention policies** (GDPR/CCPA compliance — Doc 2)
8. **DR runbooks** (only 40% complete — Doc 1, 3)
9. **Penetration test report** (last test 6 months ago — Doc 4)
10. **Security group rules export** (all rules — Doc 4)
11. **Okta configuration export** (policies, rules, integrations — Doc 5)
12. **AWS IAM policies** (all roles/policies — Doc 3, 5)
13. **Privileged user list** (complete list with admin rights — Doc 5)
14. **Org chart diagram** (visual reporting structure — Doc 6)

**Expected VDR Request Count:** 12-15 gaps flagged

---

## Risk Identification — Expected Risks

### HIGH Severity Risks (Expected)

1. **Wiz contract expiring** (2 months — CSPM visibility loss)
2. **Datadog contract expiring** (3 months — observability loss)
3. **SOC 2 renewal urgency** (4 months — customer attrition risk)
4. **DR capability unproven** (last test failed 14 months ago)
5. **No EU data residency** (GDPR compliance risk)
6. **No ISO 27001** (30% of enterprise customers require it)
7. **Key person dependency** (CTO co-founder with deep knowledge)

### MEDIUM Severity Risks (Expected)

1. **MFA coverage gap** (15% of workforce, 62 users)
2. **Limited PAM coverage** (26 privileged users uncovered)
3. **Vulnerability remediation SLA misses** (87 open vulns)
4. **No SIEM** (Datadog Security Monitoring insufficient)
5. **Data classification unenforced** (no DLP)
6. **GDPR/CCPA self-assessed only** (no formal audit)
7. **Auth0 vendor lock-in** (migration complexity)

**Expected Risk Count:** 12-15 risks flagged

---

## Work Item Identification — Expected Work Items

### Day 1 Work Items (Expected)

1. **Enforce MFA for 62 users** (30 days)
2. **Renew Wiz contract** (URGENT — 2 months)
3. **Renew Datadog contract** (URGENT — 3 months)
4. **Azure AD federation** (enable SSO to ESG apps)

### Day 100 Work Items (Expected)

1. **Expand CyberArk PAM** (26 additional users)
2. **Splunk SIEM integration** (90 days)
3. **Qualys vulnerability scanning deployment** (90 days)
4. **ISO 27001 preparation** (12-month project start)
5. **GDPR/CCPA formal audits** (6 months)
6. **Okta → Azure AD migration** (6-12 month project start)

### Post-100 Work Items (Expected)

1. **EU data residency deployment** (6-12 months)
2. **Auth0 → Azure AD B2C migration** (18-24 months)
3. **NetSuite → SAP S/4HANA migration** (24 months)
4. **Salesforce → Dynamics 365 migration** (18 months)
5. **GitHub → GitLab migration** (24 months)
6. **Snowflake → Synapse migration** (24 months)

**Expected Work Item Count:** 15-20 work items across all phases

---

## Cost Estimate Validation

### Expected One-Time Costs (Ranges)

| Category | Expected Range | Source Documents |
|---|---:|---|
| **Security remediation** | $900K - $1.675M | Buyer Doc 4 |
| **Identity migration** | $625K - $1.15M | Buyer Doc 5 |
| **Application migration** | $1.5M - $3M | Buyer Doc 2 |
| **Infrastructure integration** | $500K - $1M | Buyer Doc 3 |
| **Compliance (ISO, GDPR, audits)** | $425K - $650K | Buyer Doc 4 |
| **Talent retention** | $1.2M - $1.5M | Buyer Doc 6 |
| **TOTAL ONE-TIME** | **$5.15M - $9M** | Buyer Doc 6 summary |

**ESG Budgeted Range:** $4M - $8M (per Buyer Doc 1)

### Expected Annual Recurring Impact

| Category | Expected Impact | Source |
|---|---:|---|
| **Security tools (new)** | +$445K - $610K | Buyer Doc 4 |
| **Okta savings** | -$98K | Buyer Doc 5 |
| **App consolidation** | -$400K | Buyer Doc 6 |
| **Tool consolidation** | -$300K | Buyer Doc 6 |
| **Compliance audits** | +$50K - $75K | Buyer Doc 4 |
| **NET ANNUAL IMPACT** | **-$303K to +$785K** | Buyer Doc 6 |

**Expected Vendor Consolidation Savings:** ~$800K/year (Year 2+)

---

## Entity Scoping Validation

### Critical Entity Validation Rules

1. **Every fact MUST have an `entity` field** (`"target"` or `"buyer"`)
2. **Inventory items MUST have entity in fingerprint** (prevent cross-entity merging)
3. **UI filters MUST use entity** (separate target vs buyer views)

### Expected Entity Breakdown

| Domain | Target Facts | Buyer Facts | Total |
|---|---:|---:|---:|
| **ORGANIZATION** | 15 | 9 | 24 |
| **APPLICATIONS** | 38 items | 9 items | 47 items |
| **INFRASTRUCTURE** | 35 | 12 | 47 |
| **NETWORK** | 18 | 8 | 26 |
| **CYBERSECURITY** | 22 | 15 | 37 |
| **IDENTITY_ACCESS** | 28 | 14 | 42 |
| **EXECUTIVE_PROFILE** | 12 | 8 | 20 |

**Test:** UI should show non-zero counts for BOTH target AND buyer when filtered by entity.

**Common Failure:** All items show as `entity: target`, buyer shows 0 items.

---

## Document Source Mapping

### Target Documents → Domains

| Document | Primary Domains | Expected Facts |
|---|---|---:|
| **Target Doc 1: Executive IT Profile** | EXECUTIVE_PROFILE, all domains (summary) | 12 |
| **Target Doc 2: Application Inventory** | APPLICATIONS | 38 items |
| **Target Doc 3: Infrastructure Hosting** | INFRASTRUCTURE | 35 |
| **Target Doc 4: Network & Cybersecurity** | NETWORK, CYBERSECURITY | 40 |
| **Target Doc 5: Identity & Access** | IDENTITY_ACCESS | 28 |
| **Target Doc 6: Organization & Vendors** | ORGANIZATION | 15 |

### Buyer Documents → Domains

| Document | Primary Domains | Expected Facts |
|---|---|---:|
| **Buyer Doc 1: IT Profile & Standards** | EXECUTIVE_PROFILE | 8 |
| **Buyer Doc 2: Application Portfolio** | APPLICATIONS | 9 items |
| **Buyer Doc 3: Infrastructure Standards** | INFRASTRUCTURE | 12 |
| **Buyer Doc 4: Security & Compliance** | CYBERSECURITY | 15 |
| **Buyer Doc 5: IAM Standards** | IDENTITY_ACCESS | 14 |
| **Buyer Doc 6: Org Model & Vendors** | ORGANIZATION | 9 |

---

## Test Scenarios — Automation Validation

### Scenario 1: Full Pipeline Test (All 12 Documents)

**Input:** All 6 target + 6 buyer documents
**Expected Output:**
- **Facts extracted:** 243 total (168 target + 75 buyer)
- **Inventory items:** 47 applications (38 target + 9 buyer)
- **Entity distribution:** Non-zero for both target and buyer in all domains
- **Risks identified:** 12-15 risks
- **Work items identified:** 15-20 work items
- **Cost estimates:** $5M-9M one-time, -$300K to +$785K annual
- **VDR requests:** 12-15 gaps flagged

**Pass Criteria:**
- ✅ Fact count within ±10% of expected
- ✅ Inventory count matches exactly (38 target apps, 9 buyer apps)
- ✅ Both entities represented (no 0 counts)
- ✅ Risks flagged (≥10)
- ✅ Work items generated (≥12)
- ✅ Cost estimates in expected range

### Scenario 2: Target-Only Test (6 Target Documents)

**Input:** Target documents only
**Expected Output:**
- **Facts:** 168 target facts, 0 buyer facts
- **Applications:** 38 target apps
- **Entity:** All facts tagged `entity: "target"`

**Pass Criteria:**
- ✅ No buyer facts (count = 0)
- ✅ All facts have `entity: "target"`

### Scenario 3: Buyer-Only Test (6 Buyer Documents)

**Input:** Buyer documents only
**Expected Output:**
- **Facts:** 75 buyer facts, 0 target facts
- **Applications:** 9 buyer apps
- **Entity:** All facts tagged `entity: "buyer"`

**Pass Criteria:**
- ✅ No target facts (count = 0)
- ✅ All facts have `entity: "buyer"`

### Scenario 4: Organization Fact Explosion Test

**Focus:** Organization domain (Target Doc 6)
**Known Issue:** Extracts 432 facts instead of 15
**Expected:** 15 facts (one fact per team/role category, not per person/row)

**Pass Criteria:**
- ✅ Organization fact count ≤ 30 (with tolerance)
- ❌ FAIL if count ≥ 400 (indicates row-by-row extraction bug)

### Scenario 5: Reasoning Phase Test

**Focus:** Phase 2 (Reasoning) execution
**Known Issue:** Web app skips reasoning phase → 0 risks, 0 work items, $0 costs

**Expected Output:**
- Risks: ≥10
- Work items: ≥12
- Findings count: ≥30
- Cost estimates: Present and non-zero

**Pass Criteria:**
- ✅ findings_count > 0
- ✅ risks.length ≥ 10
- ✅ work_items.length ≥ 12
- ❌ FAIL if all values = 0 (reasoning phase didn't run)

---

## Usage Instructions — `/itddcheck` Command

### Running Validation

```bash
# CLI validation
python main_v2.py data/input/ --all --target-name "CloudServe"

# Compare output against this ground truth
diff output/facts/facts_TIMESTAMP.json EXPECTED_FACTS_GROUND_TRUTH.md
```

### Validation Checklist

- [ ] **Fact counts** match expected ranges (±10%)
- [ ] **Inventory counts** match exactly (38 target apps, 9 buyer apps)
- [ ] **Entity distribution** both target and buyer present
- [ ] **Organization facts** ≤ 30 (not 400+)
- [ ] **Risks identified** ≥ 10
- [ ] **Work items identified** ≥ 12
- [ ] **Cost estimates** in expected range ($5M-9M one-time)
- [ ] **VDR requests** ≥ 12 gaps flagged
- [ ] **Consistency checks** pass (app cost, AWS spend, headcount)
- [ ] **Entity scoping** no null/missing entity values

---

**END OF EXPECTED FACTS GROUND TRUTH**
