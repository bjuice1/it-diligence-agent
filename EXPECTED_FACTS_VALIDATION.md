# IT Due Diligence Expected Facts - Validation Reference

> **Purpose:** Reference document for validating automation extraction accuracy
> **Scenario:** CloudServe (Target) acquisition by ESG (Buyer)
> **Documents:** 6 Target + 6 Buyer = 12 total documents
> **Generated:** 2026-02-13

---

## HOW TO USE THIS DOCUMENT

This is your "answer key" for validating the IT diligence automation tool.

**Expected Behavior:**
1. Run automation on the 12 source documents
2. Compare extracted facts against this reference
3. Calculate accuracy: `(Matched Facts / Expected Facts) × 100%`

**Acceptance Criteria:**
- ✅ **90%+ accuracy** = PASS (automation working correctly)
- ⚠️ **80-89% accuracy** = WARNING (investigate gaps)
- ❌ **<80% accuracy** = FAIL (major extraction issues)

---

## SUMMARY OF EXPECTED FACTS

| Domain | Target Facts | Buyer Facts | Total Expected |
|--------|-------------:|------------:|--------------:|
| **Applications** | 68 | 9 | 77 |
| **Vendors** | 37 | 15 | 52 |
| **Organization** | 15 | 12 | 27 |
| **Infrastructure** | TBD | TBD | TBD |
| **Network** | TBD | TBD | TBD |
| **Cybersecurity** | TBD | TBD | TBD |
| **Identity/Access** | TBD | TBD | TBD |

**TOTAL EXPECTED FACTS: ~200-250 facts** (across all domains)

---

# SECTION 1: APPLICATIONS DOMAIN

## 1.1 TARGET Applications (68 Expected)

### SOURCE: Document 2 (Application Inventory) — 38 Applications

**Core Platform Components (8 Internal Apps):**

| App Name | Vendor | Category | Version | Hosting | Annual Cost | Criticality | Contract End | Entity |
|----------|--------|----------|---------|---------|------------:|-------------|--------------|--------|
| API Gateway Service | Internal | infrastructure | v3.2 | AWS (EKS) | $0 | CRITICAL | N/A | target |
| Authentication Service | Internal | infrastructure | v2.8 | AWS (EKS) | $0 | CRITICAL | N/A | target |
| Customer Data Service | Internal | infrastructure | v4.1 | AWS (EKS) | $0 | CRITICAL | N/A | target |
| Messaging Service | Internal | infrastructure | v2.5 | AWS (EKS) | $0 | CRITICAL | N/A | target |
| Analytics Engine | Internal | infrastructure | v1.9 | AWS (EKS) | $0 | HIGH | N/A | target |
| Workflow Orchestration | Internal | infrastructure | v3.0 | AWS (EKS) | $0 | HIGH | N/A | target |
| Notification Service | Internal | infrastructure | v2.2 | AWS (Lambda) | $0 | MEDIUM | N/A | target |
| Billing & Metering | Internal | infrastructure | v1.7 | AWS (EKS) | $0 | HIGH | N/A | target |

**CRM & Sales (3 Apps):**

| App Name | Vendor | Category | Annual Cost | Contract End | Entity |
|----------|--------|----------|------------:|--------------|--------|
| Salesforce Sales Cloud | Salesforce | crm | $245,000 | 2025-10 | target |
| Outreach.io | Outreach | crm | $126,000 | 2025-06 | target |
| Gong | Gong | crm | $57,000 | 2025-12 | target |

**Finance & ERP (5 Apps):**

| App Name | Vendor | Category | Annual Cost | Contract End | Entity |
|----------|--------|----------|------------:|--------------|--------|
| NetSuite | Oracle | erp | $180,000 | 2026-03 | target |
| Stripe | Stripe | finance | $0 | Evergreen | target |
| Bill.com | Bill.com | finance | $24,000 | 2025-08 | target |
| Expensify | Expensify | finance | $18,000 | 2025-04 | target |
| Adaptive Insights | Workday | finance | $158,000 | 2025-11 | target |

**HR & Collaboration (5 Apps):**

| App Name | Vendor | Category | Annual Cost | Contract End | Entity |
|----------|--------|----------|------------:|--------------|--------|
| BambooHR | BambooHR | hcm | $48,000 | 2025-07 | target |
| Rippling | Rippling | hcm | $96,000 | 2026-01 | target |
| Google Workspace | Google | collaboration | $82,000 | 2025-09 | target |
| Slack | Slack | collaboration | $72,000 | 2025-05 | target |
| Zoom | Zoom | collaboration | $14,000 | 2025-03 | target |

**Development & DevOps (12 Apps):**

| App Name | Vendor | Category | Annual Cost | Contract End | Entity |
|----------|--------|----------|------------:|--------------|--------|
| GitHub Enterprise | GitHub | devops | $23,000 | 2026-02 | target |
| Datadog | Datadog | infrastructure | $150,000 | 2025-03 | target |
| PagerDuty | PagerDuty | devops | $18,000 | 2025-05 | target |
| Terraform Cloud | HashiCorp | devops | $48,000 | 2025-08 | target |
| ArgoCD | Argo Project | devops | $0 | N/A | target |
| Snyk | Snyk | security | $78,000 | 2025-06 | target |
| Postman | Postman | devops | $18,000 | 2025-10 | target |
| Jira Software | Atlassian | productivity | $12,000 | 2025-04 | target |
| Confluence | Atlassian | productivity | $6,000 | 2025-04 | target |
| Figma | Figma | productivity | $18,000 | 2025-07 | target |
| LaunchDarkly | LaunchDarkly | devops | $45,000 | 2025-09 | target |
| Sentry | Sentry | devops | $18,000 | 2025-11 | target |

**Security & Compliance (4 Apps):**

| App Name | Vendor | Category | Annual Cost | Contract End | Entity |
|----------|--------|----------|------------:|--------------|--------|
| Okta | Okta | security | $98,000 | 2025-06 | target |
| CrowdStrike Falcon | CrowdStrike | security | $87,000 | 2025-11 | target |
| Wiz | Wiz | security | $125,000 | 2025-02 | target |
| Vanta | Vanta | security | $210,000 | 2025-08 | target |

**Data & Analytics (2 Apps):**

| App Name | Vendor | Category | Annual Cost | Contract End | Entity |
|----------|--------|----------|------------:|--------------|--------|
| Snowflake | Snowflake | database | $285,000 | 2026-01 | target |
| Looker | Google | bi_analytics | $32,500 | 2025-09 | target |

**SUBTOTAL FROM DOC 2: 38 applications**

---

### SOURCE: Document 6 (Vendor Inventory) — 30 Additional Vendor Entries

**⚠️ CRITICAL VALIDATION POINT:**

These vendor entries should create **APPLICATION** inventory items (not just vendor items).

**Why:** These are SaaS applications where the vendor name IS the application name.

**Infrastructure & Cloud (2):**

| Vendor/App Name | Category | Annual Spend | Contract End | Entity |
|-----------------|----------|-------------:|--------------|--------|
| AWS | Cloud infrastructure | $4,800,000 | Evergreen | target |
| Fastly | CDN | $85,000 | 2025-03 | target |

**Note:** AWS may appear in both Doc 2 and Doc 6 — deduplication should occur based on (normalized_name, entity) fingerprint.

**All vendors from Doc 6 vendor tables (lines 200-276)** should map to applications as follows:

| Vendor | Should Map To Application | Category | Annual Spend |
|--------|---------------------------|----------|-------------:|
| Salesforce | Salesforce Sales Cloud | CRM | $245,000 |
| Oracle (NetSuite) | NetSuite | ERP | $180,000 |
| Stripe | Stripe | Payments | $0 |
| Workday (Adaptive) | Adaptive Insights | FP&A | $158,000 |
| BambooHR | BambooHR | HRIS | $48,000 |
| Rippling | Rippling | Payroll | $96,000 |
| Google (Workspace) | Google Workspace | Collaboration | $82,000 |
| Slack | Slack | Communication | $72,000 |
| Zoom | Zoom | Video conferencing | $14,000 |
| Bill.com | Bill.com | AP | $24,000 |
| Expensify | Expensify | Expense mgmt | $18,000 |
| Outreach.io | Outreach.io | Sales engagement | $126,000 |
| Gong | Gong | Sales intelligence | $57,000 |
| GitHub | GitHub Enterprise | Code repository | $156,000 |
| Datadog | Datadog | Observability | $312,000 |
| PagerDuty | PagerDuty | Incident mgmt | $64,000 |
| HashiCorp (Terraform) | Terraform Cloud | IaC | $48,000 |
| Snyk | Snyk | Code security | $78,000 |
| Postman | Postman | API testing | $42,000 |
| Atlassian (Jira) | Jira Software | Project mgmt | $98,000 |
| Atlassian (Confluence) | Confluence | Documentation | $52,000 |
| Figma | Figma | Design | $18,000 |
| LaunchDarkly | LaunchDarkly | Feature flags | $64,000 |
| Sentry | Sentry | Error tracking | $18,000 |
| Okta | Okta | Identity & SSO | $98,000 |
| Auth0 | Auth0 | Customer identity | Included in AWS |
| CrowdStrike | CrowdStrike Falcon | Endpoint security | $87,000 |
| Wiz | Wiz | Cloud security | $125,000 |
| Vanta | Vanta | Compliance | $210,000 |
| CyberArk | CyberArk | PAM | $42,000 |
| Snowflake | Snowflake | Data warehouse | $285,000 |
| Google (Looker) | Looker | BI platform | $32,500 |

**⚠️ DEDUPLICATION EXPECTED:**

Many vendors appear in BOTH Doc 2 and Doc 6. The system should:
1. Create content-hashed fingerprints based on (normalized_name, entity)
2. Merge duplicate facts from both sources
3. Final application count should be ~38 unique applications (NOT 68)

**CORRECTED EXPECTED COUNT FOR TARGET APPLICATIONS: 38 unique applications**

(8 Internal + 30 SaaS vendors, with Doc 2 and Doc 6 overlapping)

---

## 1.2 BUYER Applications (9 Expected)

### SOURCE: Buyer Document 2 (Application Portfolio)

| App Name | Vendor | Category | Users | Annual Cost | Entity |
|----------|--------|----------|------:|------------:|--------|
| SAP S/4HANA Cloud | SAP | ERP | 12,400 | $18,500,000 | buyer |
| Microsoft Dynamics 365 Sales | Microsoft | CRM | 3,200 | $9,800,000 | buyer |
| Workday HCM | Workday | HCM | 24,500 | $12,200,000 | buyer |
| BlackLine | BlackLine | Finance | 1,800 | $6,400,000 | buyer |
| SAP Ariba | SAP | Procurement | 2,100 | $3,200,000 | buyer |
| Microsoft 365 E5 | Microsoft | Collaboration | 24,500 | $14,700,000 | buyer |
| Microsoft Teams | Microsoft | Communication | 24,500 | Included in M365 | buyer |
| Power BI Premium | Microsoft | BI | 4,800 | $2,400,000 | buyer |
| ServiceNow ITSM | ServiceNow | ITSM | 2,100 | $4,200,000 | buyer |

**SUBTOTAL BUYER APPS: 9 applications**

---

## 1.3 APPLICATION FACTS VALIDATION CHECKLIST

When validating the automation output, verify:

**✅ Count Validation:**
- [ ] Target applications: 38 unique apps (NOT 68 due to deduplication)
- [ ] Buyer applications: 9 apps
- [ ] Total applications: 47 apps

**✅ Entity Scoping:**
- [ ] All Target apps have `entity: "target"`
- [ ] All Buyer apps have `entity: "buyer"`
- [ ] No apps with `entity: null` or missing entity

**✅ Vendor Table Extraction (CRITICAL):**
- [ ] All 30 vendors from Target Doc 6 tables (lines 200-276) extracted
- [ ] Zero "Skipping row without application name" errors for these vendors:
  - [ ] Snyk
  - [ ] Postman
  - [ ] Jira (Atlassian)
  - [ ] Confluence (Atlassian)
  - [ ] Figma
  - [ ] LaunchDarkly
  - [ ] Sentry
  - [ ] Okta
  - [ ] Auth0
  - [ ] CrowdStrike
  - [ ] Wiz
  - [ ] Vanta
  - [ ] CyberArk
  - [ ] Bishop Fox
  - [ ] Snowflake
  - [ ] Looker
  - [ ] CGI
  - [ ] Offshore QA (India)
  - [ ] Offshore Infra (Poland)

**✅ Deduplication:**
- [ ] Applications appearing in BOTH Doc 2 and Doc 6 are merged (not duplicated)
- [ ] Fingerprints include entity to prevent Target/Buyer cross-merging
- [ ] Examples to check: Salesforce, Datadog, Okta, GitHub, Snowflake

**✅ Critical Fields:**
- [ ] All apps have `annual_cost` (even if $0 for internal apps)
- [ ] All apps have `criticality` (CRITICAL/HIGH/MEDIUM/LOW)
- [ ] All apps have `contract_end` (even if "N/A" for internal or "Evergreen")
- [ ] All apps have `category` mapped correctly (see app_category_mappings.py)

**✅ Inventory Type:**
- [ ] All vendor table entries create `inventory_type: "application"` (NOT "vendor")
- [ ] Check InventoryStore, not just FactStore counts

---

# SECTION 2: VENDORS DOMAIN

## 2.1 TARGET Vendors (37 Expected)

### SOURCE: Document 6 (Vendor Inventory Tables)

**All vendors listed in lines 200-276 should create VENDOR inventory items:**

| Vendor Name | Category | Annual Spend | Contract End | Termination Notice | Entity |
|-------------|----------|-------------:|--------------|-------------------|--------|
| AWS | Cloud infrastructure | $4,800,000 | Evergreen | Pay-as-you-go | target |
| Fastly | CDN | $85,000 | 2025-03 | Annual prepay | target |
| Salesforce | CRM | $245,000 | 2025-10 | 30 days | target |
| Oracle (NetSuite) | ERP | $180,000 | 2026-03 | 60 days | target |
| Stripe | Payments | $0 | Evergreen | 30 days | target |
| Workday (Adaptive) | FP&A | $158,000 | 2025-11 | 90 days | target |
| BambooHR | HRIS | $48,000 | 2025-07 | 30 days | target |
| Rippling | Payroll | $96,000 | 2026-01 | 30 days | target |
| Google (Workspace) | Collaboration | $82,000 | 2025-09 | 30 days | target |
| Slack | Communication | $72,000 | 2025-05 | 30 days | target |
| Zoom | Video conferencing | $14,000 | 2025-03 | 30 days | target |
| Bill.com | AP | $24,000 | 2025-08 | 30 days | target |
| Expensify | Expense mgmt | $18,000 | 2025-04 | 30 days | target |
| Outreach.io | Sales engagement | $126,000 | 2025-06 | 30 days | target |
| Gong | Sales intelligence | $57,000 | 2025-12 | 30 days | target |
| GitHub | Code repository | $156,000 | 2026-02 | 30 days | target |
| Datadog | Observability | $312,000 | 2025-03 | 30 days (expiring soon) | target |
| PagerDuty | Incident mgmt | $64,000 | 2025-05 | 30 days | target |
| HashiCorp (Terraform) | IaC | $48,000 | 2025-08 | 30 days | target |
| Snyk | Code security | $78,000 | 2025-06 | 30 days | target |
| Postman | API testing | $42,000 | 2025-10 | 30 days | target |
| Atlassian (Jira) | Project mgmt | $98,000 | 2025-04 | 30 days | target |
| Atlassian (Confluence) | Documentation | $52,000 | 2025-04 | 30 days | target |
| Figma | Design | $18,000 | 2025-07 | 30 days | target |
| LaunchDarkly | Feature flags | $64,000 | 2025-09 | 30 days | target |
| Sentry | Error tracking | $18,000 | 2025-11 | 30 days | target |
| Okta | Identity & SSO | $98,000 | 2025-06 | 30 days | target |
| Auth0 | Customer identity | Included in AWS | Evergreen | 30 days | target |
| CrowdStrike | Endpoint security | $87,000 | 2025-11 | 30 days | target |
| Wiz | Cloud security | $125,000 | 2025-02 | 30 days (expiring in 2 months) | target |
| Vanta | Compliance | $210,000 | 2025-08 | 60 days | target |
| CyberArk | PAM | $42,000 | 2025-04 | 60 days | target |
| Bishop Fox | Pentesting | $65,000 | 2025-06 | No (SOW-based) | target |
| Snowflake | Data warehouse | $285,000 | 2026-01 | 60 days | target |
| Google (Looker) | BI platform | $32,500 | 2025-09 | 30 days | target |
| CGI | MSP (limited) | $85,000 | 2025-12 | 90 days | target |
| Offshore QA (India) | Staff augmentation | $325,000 | 2025-06 | 60 days | target |
| Offshore Infra (Poland) | Staff augmentation | $315,000 | 2025-09 | 60 days | target |

**SUBTOTAL TARGET VENDORS: 37 vendors**

---

## 2.2 BUYER Vendors (15 Expected)

### SOURCE: Buyer Document 6 (Approved Vendor List)

**Tier 1 (Preferred) Vendors:**

| Vendor Name | Category | Entity |
|-------------|----------|--------|
| Microsoft Azure | Cloud (primary) | buyer |
| SAP | ERP | buyer |
| Microsoft | CRM, Collaboration, BI | buyer |
| Workday | HCM | buyer |
| ServiceNow | ITSM | buyer |
| Splunk | SIEM, Monitoring | buyer |
| CrowdStrike Falcon | EDR | buyer |
| CyberArk | PAM | buyer |
| SailPoint | IGA | buyer |
| Azure AD (Entra ID) | IdP | buyer |
| GitLab | Code repository | buyer |
| Terraform | IaC | buyer |
| PagerDuty | Incident mgmt | buyer |
| Infosys | Offshore partner | buyer |
| Cognizant | Offshore partner | buyer |

**SUBTOTAL BUYER VENDORS: 15 vendors** (Tier 1 only for simplicity)

---

## 2.3 VENDOR FACTS VALIDATION CHECKLIST

**✅ Count Validation:**
- [ ] Target vendors: 37 vendors
- [ ] Buyer vendors: 15 vendors (Tier 1 preferred)
- [ ] Total vendors: 52 vendors

**✅ Entity Scoping:**
- [ ] All Target vendors have `entity: "target"`
- [ ] All Buyer vendors have `entity: "buyer"`

**✅ Vendor-Specific Fields:**
- [ ] All vendors have `annual_spend` (even if "$0" or "Included in...")
- [ ] All vendors have `contract_end` date
- [ ] All vendors have `termination_notice` period
- [ ] Vendors with expiring contracts flagged (Wiz 2025-02, Datadog 2025-03)

**✅ Dual Inventory Creation:**
- [ ] Vendors should create BOTH vendor items AND application items
- [ ] Verify in InventoryStore that same vendor appears in both inventory types

---

# SECTION 3: ORGANIZATION DOMAIN

## 3.1 TARGET Organization (15 Expected)

### SOURCE: Document 6 (IT Organization)

**High-Level Org Facts:**

| Fact ID | Fact Type | Value | Source |
|---------|-----------|-------|--------|
| F-TGT-ORG-001 | Total IT headcount | 67 FTE | Doc 6, line 13 |
| F-TGT-ORG-002 | Contractors/offshore | 8 FTE | Doc 6, line 14 |
| F-TGT-ORG-003 | Total personnel | 75 FTE | Doc 6, line 15 |
| F-TGT-ORG-004 | Annual personnel cost | $6,900,000 | Doc 6, line 16 |
| F-TGT-ORG-005 | Contractor cost | $640,000 | Doc 6, line 17 |
| F-TGT-ORG-006 | Total people cost | $7,540,000 | Doc 6, line 18 |
| F-TGT-ORG-007 | Average FTE cost | $103,000 | Doc 6, line 19 |
| F-TGT-ORG-008 | Span of control (avg) | 8.4 reports per manager | Doc 6, line 20 |

**Leadership Facts:**

| Fact ID | Role | Name | Salary | Total Comp | Tenure | Reports To | Entity |
|---------|------|------|-------:|------------|--------|-----------|--------|
| F-TGT-ORG-009 | CTO | Sarah Chen | $280K-320K | $450,000 | 5 years | CEO | target |
| F-TGT-ORG-010 | VP Engineering | Michael Torres | $220K-260K | $350,000 | 3 years | CTO | target |

**Team Breakdown Facts:**

| Fact ID | Team | Headcount | Total Cost | Entity |
|---------|------|----------:|------------|--------|
| F-TGT-ORG-011 | Platform Engineering | 18 FTE | $3,020,000/year | target |
| F-TGT-ORG-012 | Infrastructure & SRE | 12 FTE | $1,945,000/year | target |
| F-TGT-ORG-013 | Security Engineering | 5 FTE | $785,000/year | target |
| F-TGT-ORG-014 | DevOps & Release | 8 FTE | $1,195,000/year | target |
| F-TGT-ORG-015 | Data Engineering | 6 FTE | $945,000/year | target |

**SUBTOTAL TARGET ORG FACTS: 15 high-level facts**

(Additional granular role-level facts from lines 39-149 can be extracted but are not critical for validation)

---

## 3.2 BUYER Organization (12 Expected)

### SOURCE: Buyer Document 6 (IT Organization)

**High-Level Org Facts:**

| Fact ID | Fact Type | Value | Source |
|---------|-----------|-------|--------|
| F-BYR-ORG-001 | Total IT headcount | 2,100 FTE | Buyer Doc 6, line 12 |
| F-BYR-ORG-002 | Corporate IT | 850 FTE | Buyer Doc 6, line 13 |
| F-BYR-ORG-003 | Product Engineering | 1,250 FTE | Buyer Doc 6, line 14 |
| F-BYR-ORG-004 | IT budget | $2.1B annually | Buyer Doc 6, line 15 |
| F-BYR-ORG-005 | Personnel cost | $1.2B annually | Buyer Doc 6, line 16 |
| F-BYR-ORG-006 | Contractor/offshore | 320 FTE | Buyer Doc 6, line 17 |
| F-BYR-ORG-007 | Global presence | 45 countries, 120 offices | Buyer Doc 6, line 18 |

**Leadership Facts:**

| Fact ID | Role | Reports To | Team Size | Entity |
|---------|------|-----------|----------:|--------|
| F-BYR-ORG-008 | CIO | CEO | 4 direct reports | buyer |
| F-BYR-ORG-009 | CISO | CIO | 180 (global security) | buyer |
| F-BYR-ORG-010 | SVP Corporate IT | CIO | 850 | buyer |
| F-BYR-ORG-011 | VP M&A Integration | SVP Corporate IT | 25 (dedicated M&A team) | buyer |
| F-BYR-ORG-012 | M&A Integration Director | VP M&A Integration | Team of 25 | buyer |

**SUBTOTAL BUYER ORG FACTS: 12 facts**

---

## 3.3 ORGANIZATION FACTS VALIDATION CHECKLIST

**✅ Count Validation:**
- [ ] Target organization facts: 15+
- [ ] Buyer organization facts: 12+
- [ ] Total organization facts: 27+

**✅ Entity Scoping:**
- [ ] All Target org facts have `entity: "target"`
- [ ] All Buyer org facts have `entity: "buyer"`

**✅ Key Person Risks:**
- [ ] CTO (Sarah Chen) identified as retention-critical
- [ ] VP Engineering (Michael Torres) identified as retention-critical

**✅ Org Structure:**
- [ ] 7 teams identified (Platform, Infrastructure, Security, DevOps, Data, IT Ops, Contractors)
- [ ] Headcount per team extracted
- [ ] Total cost per team extracted

---

# SECTION 4: INFRASTRUCTURE DOMAIN

## 4.1 TARGET Infrastructure (Expected Facts TBD)

### SOURCE: Document 3 (Infrastructure & Hosting Inventory)

**Expected fact categories:**
- Hosting model (100% AWS)
- Compute resources (EKS clusters, EC2, Lambda)
- Storage (S3, EBS, RDS)
- Backup & DR strategy
- Cloud cost ($4.8M AWS annual spend)
- CDN (Fastly)
- Legacy systems (if any)

**PLACEHOLDER: Full extraction TBD** (requires reading Document 3)

---

## 4.2 BUYER Infrastructure (Expected Facts TBD)

### SOURCE: Buyer Document 3 (Infrastructure & Cloud Standards)

**Expected fact categories:**
- Preferred cloud: Microsoft Azure
- Multi-cloud strategy (Azure primary, AWS for acquisitions)
- Infrastructure standards
- Migration approach for AWS → Azure (optional, 12-24 months)

**PLACEHOLDER: Full extraction TBD** (requires reading Buyer Document 3)

---

# SECTION 5: NETWORK DOMAIN

## 5.1 TARGET Network (Expected Facts TBD)

### SOURCE: Document 4 (Network & Cybersecurity Inventory)

**Expected fact categories:**
- WAN connectivity
- Remote access (VPN)
- DNS & DHCP
- Network security (firewalls, segmentation)
- Load balancing
- Monitoring

**PLACEHOLDER: Full extraction TBD** (requires reading Document 4)

---

## 5.2 BUYER Network (Expected Facts TBD)

### SOURCE: Buyer Document 4 (Security & Compliance Requirements)

**Expected fact categories:**
- Network security standards
- Required network controls
- Integration requirements

**PLACEHOLDER: Full extraction TBD**

---

# SECTION 6: CYBERSECURITY DOMAIN

## 6.1 TARGET Cybersecurity (Expected Facts TBD)

### SOURCE: Document 4 (Network & Cybersecurity Inventory)

**Expected fact categories:**
- Endpoint security (CrowdStrike Falcon)
- Cloud security (Wiz, AWS GuardDuty, AWS WAF)
- Code security (Snyk)
- Compliance (Vanta, SOC 2)
- PAM (CyberArk)
- Pentesting (Bishop Fox)

**PLACEHOLDER: Full extraction TBD** (requires reading Document 4)

---

## 6.2 BUYER Cybersecurity (Expected Facts TBD)

### SOURCE: Buyer Document 4 (Security & Compliance Requirements)

**Expected fact categories:**
- Mandatory security controls
- EDR (CrowdStrike Falcon - aligned)
- SIEM (Splunk)
- CSPM (Microsoft Defender for Cloud/Wiz)
- Compliance frameworks (ISO 27001, SOC 2, GDPR)

**PLACEHOLDER: Full extraction TBD**

---

# SECTION 7: IDENTITY & ACCESS DOMAIN

## 7.1 TARGET Identity & Access (Expected Facts TBD)

### SOURCE: Document 5 (Identity & Access Management)

**Expected fact categories:**
- Workforce IdP (Okta)
- Customer IdP (Auth0)
- SSO coverage (12 apps)
- MFA adoption (85% of workforce)
- PAM (CyberArk)
- Provisioning (Okta Workflows)

**PLACEHOLDER: Full extraction TBD** (requires reading Document 5)

---

## 7.2 BUYER Identity & Access (Expected Facts TBD)

### SOURCE: Buyer Document 5 (IAM Standards & Requirements)

**Expected fact categories:**
- Preferred IdP (Azure AD / Entra ID)
- IGA (SailPoint IdentityIQ)
- Migration path: Okta → Azure AD (6-12 months)
- Migration path: Auth0 → Azure AD B2C (18-24 months)

**PLACEHOLDER: Full extraction TBD**

---

# VALIDATION SCORING

## Scoring Formula

```
Accuracy = (Matched Facts / Expected Facts) × 100%
```

**Matched Fact Criteria:**
- Fact extracted with correct entity (target/buyer)
- Fact value matches expected value (within tolerance)
- Fact type correctly classified

**Tolerance Levels:**
- Exact match required: Entity, application names, vendor names, headcount
- ±5% tolerance: Annual costs, budgets
- Date tolerance: ±1 month for contract dates

---

## Acceptance Thresholds

| Score | Status | Action |
|-------|--------|--------|
| 95-100% | ✅ EXCELLENT | Automation production-ready |
| 90-94% | ✅ PASS | Minor tuning recommended |
| 80-89% | ⚠️ WARNING | Investigate gaps, re-test |
| 70-79% | ⚠️ FAIL | Major fixes needed |
| <70% | ❌ CRITICAL | Extraction broken, halt deployment |

---

## Critical Failure Indicators

**Immediate halt if ANY of these occur:**

- ❌ Entity scoping failure (target/buyer mixed up)
- ❌ Vendor table mass skipping (40+ vendors missed)
- ❌ Application count off by >20% (e.g., showing 30 apps when 38 expected)
- ❌ Inventory type confusion (vendors creating only vendor items, not apps)
- ❌ Deduplication failure (duplicate apps across Doc 2 and Doc 6)

---

# TEST EXECUTION COMMANDS

## Run Full Analysis

```bash
cd "9.5/it-diligence-agent 2"

# Full pipeline with all 12 documents
python main_v2.py data/input/ --all --target-name "CloudServe" --buyer-name "ESG"
```

## Compare Output to Expected Facts

```bash
# Extract actual fact counts
python -c "
import json
facts = json.load(open('output/facts/facts_TIMESTAMP.json'))
target_apps = [f for f in facts if f['entity'] == 'target' and f['domain'] == 'applications']
buyer_apps = [f for f in facts if f['entity'] == 'buyer' and f['domain'] == 'applications']
print(f'Target apps: {len(target_apps)} (expected: 38)')
print(f'Buyer apps: {len(buyer_apps)} (expected: 9)')
"

# Check InventoryStore counts
python -c "
from stores.inventory_store import InventoryStore
store = InventoryStore()
store.load_from_file('output/inventory/inventory_TIMESTAMP.json')
target_apps = store.get_items(entity='target', inventory_type='application')
buyer_apps = store.get_items(entity='buyer', inventory_type='application')
print(f'Target apps in inventory: {len(target_apps)} (expected: 38)')
print(f'Buyer apps in inventory: {len(buyer_apps)} (expected: 9)')
"
```

---

# KNOWN ISSUES TO TEST FOR

Based on the error logs you provided, verify these bugs are FIXED:

## Issue 1: Vendor Table Skipping (CRITICAL)

**Symptom:**
```
[err] Skipping row without application name: {'vendor': 'Snyk', ...}
[err] Skipping row without application name: {'vendor': 'Postman', ...}
```

**Expected behavior after fix:**
- ✅ All 30 vendor rows from Doc 6 tables extracted
- ✅ Zero "Skipping row" errors for vendor tables
- ✅ Vendor column used as application name fallback

**Validation:**
```bash
# Should show zero skipping errors
grep "Skipping row without application name" output/logs/*.log
```

---

## Issue 2: Inventory Type Confusion

**Symptom:**
- Vendor tables creating `inventory_type: "vendor"` only
- Applications missing from UI because UI queries `inventory_type: "application"`

**Expected behavior after fix:**
- ✅ Vendor tables create BOTH vendor items AND application items
- ✅ Application count in UI matches expected count (38 target, 9 buyer)

**Validation:**
```bash
# Check inventory types
python -c "
from stores.inventory_store import InventoryStore
store = InventoryStore()
store.load_from_file('output/inventory/inventory_TIMESTAMP.json')
vendors = store.get_items(inventory_type='vendor', entity='target')
apps = store.get_items(inventory_type='application', entity='target')
print(f'Target vendors: {len(vendors)} (expected: 37)')
print(f'Target apps: {len(apps)} (expected: 38)')
"
```

---

## Issue 3: Entity Scoping Failures

**Symptom:**
- Facts/inventory items with `entity: null` or missing entity
- Target items appearing under Buyer (or vice versa)

**Expected behavior:**
- ✅ All facts have `entity: "target"` or `entity: "buyer"`
- ✅ No null/missing entity fields
- ✅ Entity correctly detected from document source

**Validation:**
```bash
# Check for null entities
python -c "
import json
facts = json.load(open('output/facts/facts_TIMESTAMP.json'))
null_entity = [f for f in facts if f.get('entity') is None]
print(f'Facts with null entity: {len(null_entity)} (expected: 0)')
if null_entity:
    print('ERROR: Null entities found!')
    for f in null_entity[:5]:
        print(f'  - {f}')
"
```

---

## Issue 4: Deduplication Failures

**Symptom:**
- Same application appearing multiple times (from Doc 2 and Doc 6)
- Inflated application counts (e.g., 68 instead of 38)

**Expected behavior:**
- ✅ Deduplication based on (normalized_name, entity) fingerprint
- ✅ Final count matches expected (38 target apps, not 68)
- ✅ Facts from multiple sources merged into single inventory item

**Validation:**
```bash
# Check for duplicate apps
python -c "
from stores.inventory_store import InventoryStore
from collections import Counter
store = InventoryStore()
store.load_from_file('output/inventory/inventory_TIMESTAMP.json')
apps = store.get_items(inventory_type='application', entity='target')
names = [app['name'] for app in apps]
duplicates = [name for name, count in Counter(names).items() if count > 1]
print(f'Duplicate app names: {len(duplicates)} (expected: 0)')
if duplicates:
    print('ERROR: Duplicates found!')
    for dup in duplicates:
        print(f'  - {dup}')
"
```

---

# REVISION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-13 | Initial validation reference created |

---

**END OF EXPECTED FACTS VALIDATION DOCUMENT**
