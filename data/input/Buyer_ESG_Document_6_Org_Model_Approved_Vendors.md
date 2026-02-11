# Enterprise Solutions Group (ESG) — Buyer Document 6: Organization Model & Approved Vendor List

> **Entity:** BUYER
> **Purpose:** ESG IT organization structure and approved vendor standards for integration planning

---

## 1) ESG IT Organization Overview

| Metric | Value |
|---|---:|
| **Total IT headcount** | **2,100** FTE (corporate IT + product engineering) |
| **Corporate IT** | 850 FTE (infrastructure, security, operations, support) |
| **Product Engineering** | 1,250 FTE (R&D for ESG products) |
| **IT budget** | $2.1B annually |
| **Personnel cost** | $1.2B annually |
| **Contractor/offshore** | 320 FTE equivalents (13% of workforce) |
| **Global presence** | 45 countries, 120 offices |

---

## 2) ESG IT Leadership Structure

| Role | Reports To | Team Size | Location |
|---|---|---:|---|
| **Chief Information Officer (CIO)** | CEO | 4 direct reports | Redmond, WA |
| **Chief Information Security Officer (CISO)** | CIO | 180 (global security org) | Redmond, WA |
| **SVP, Corporate IT** | CIO | 850 | Redmond, WA |
| **SVP, Product Engineering** | CTO (not under CIO) | 1,250 | Distributed |
| **VP, Cloud Infrastructure** | SVP Corporate IT | 220 | Redmond, WA |
| **VP, IT Operations** | SVP Corporate IT | 180 | Redmond, WA |
| **VP, Enterprise Applications** | SVP Corporate IT | 140 | Redmond, WA |
| **VP, M&A Integration** | SVP Corporate IT | 25 (dedicated M&A team) | Redmond, WA |

---

## 3) ESG M&A Integration Team (Dedicated)

| Role | Headcount | Focus Area |
|---|---:|---|
| **M&A Integration Director** | 1 | Integration program management |
| **Cloud Migration Architects** | 5 | AWS/Azure migration planning |
| **Identity Integration Specialists** | 4 | IdP migrations (Okta → Azure AD) |
| **Security Integration Lead** | 3 | SIEM, PAM, CSPM integration |
| **Application Migration Leads** | 6 | ERP, CRM, HCM migrations |
| **Compliance Specialists** | 2 | ISO, GDPR, SOC 2 support |
| **Project Managers** | 4 | Integration project coordination |

**Total M&A Integration Team:** 25 FTE (dedicated to acquisitions)

---

## 4) ESG Integration Philosophy for Acquisitions

| Principle | Description |
|---|---|
| **"Run then transform"** | Stabilize operations Day 1-100, then integrate Day 100+ |
| **Platform autonomy** | Acquired product platforms maintain technical autonomy for 12-18 months |
| **Corporate standards (mandatory)** | Security, identity, compliance enforced immediately (30-90 days) |
| **Tool consolidation (phased)** | Gradual migration to ESG tools (6-24 month timelines) |
| **Retain key talent** | Retention bonuses for technical leaders (CTO, VPs, Staff+ engineers) |

---

## 5) CloudServe Integration: Organization Approach

| CloudServe State | ESG Integration Approach |
|---|---|
| **67 IT FTE** | Absorb into ESG corporate IT (850 FTE); maintain team identity initially |
| **CTO (co-founder)** | Retention critical; offer SVP title + equity retention package |
| **VP Engineering** | Retain as Director/Sr. Director reporting to ESG VP Product Engineering |
| **Platform Engineering (18)** | Maintain autonomy; integrate into ESG product engineering org |
| **Infrastructure/SRE (12)** | Integrate into ESG Cloud Infrastructure team (220 FTE) |
| **Security (5)** | Integrate into ESG CISO org (180 FTE) |
| **IT Ops (8)** | Integrate into ESG IT Operations team (180 FTE) |
| **Contractors (8)** | Validate against ESG approved vendor list; transition if needed |

---

## 6) ESG Approved Vendor List

### Cloud & Infrastructure

| Category | Tier 1 (Preferred) | Tier 2 (Accepted) | Tier 3 (Phase Out) |
|---|---|---|---|
| **Cloud (primary)** | Microsoft Azure | AWS (for acquisitions) | GCP (analytics only) |
| **CDN** | Azure Front Door | Akamai, Cloudflare | Fastly (phase out) |
| **DNS** | Azure DNS | Route53 (AWS) | — |
| **Monitoring** | Splunk, Azure Monitor | Datadog (12-month acceptance) | — |

**CloudServe Impact:** AWS accepted; Datadog → Splunk migration within 12 months.

---

### Security

| Category | Tier 1 (Preferred) | Tier 2 (Accepted) | Tier 3 (Phase Out) |
|---|---|---|---|
| **Endpoint security (EDR)** | CrowdStrike Falcon | — | — |
| **SIEM** | Splunk Enterprise Security | — | — |
| **CSPM** | Microsoft Defender for Cloud (Azure) | Wiz (AWS) | — |
| **SAST** | Checkmarx | — | Snyk (phase to Checkmarx) |
| **Vulnerability scanning** | Qualys VMDR | — | AWS Inspector (limited) |
| **PAM** | CyberArk | — | — |
| **DLP** | Microsoft Purview | — | — |
| **Compliance automation** | Built-in (Purview, SailPoint) | Vanta (12-month acceptance) | — |

**CloudServe Impact:** CrowdStrike aligned; Wiz accepted (AWS); Snyk → Checkmarx (12 months); Vanta → ESG tools (12 months).

---

### Identity & Access

| Category | Tier 1 (Preferred) | Tier 2 (Accepted) | Tier 3 (Phase Out) |
|---|---|---|---|
| **Workforce IdP** | Azure AD (Entra ID) | Okta (12-month migration) | — |
| **Customer IdP** | Azure AD B2C | Auth0 (24-month migration) | — |
| **IGA** | SailPoint IdentityIQ | — | — |
| **PAM** | CyberArk | — | — |

**CloudServe Impact:** Okta → Azure AD (6-12 months); Auth0 → Azure AD B2C (18-24 months).

---

### Enterprise Applications

| Category | Tier 1 (Preferred) | Tier 2 (Accepted) | Tier 3 (Phase Out) |
|---|---|---|---|
| **ERP** | SAP S/4HANA | NetSuite (24-month migration) | — |
| **CRM** | Microsoft Dynamics 365 | Salesforce (18-month migration) | — |
| **HCM** | Workday | BambooHR, Rippling (12-month migration) | — |
| **Collaboration** | Microsoft 365 E5 | Google Workspace (6-month migration) | — |
| **Communication** | Microsoft Teams | Slack (6-month migration) | — |
| **ITSM** | ServiceNow | Jira Service Management (accepted) | — |
| **BI** | Power BI | Looker (12-month migration) | — |

**CloudServe Impact:** Most apps in Tier 2 (accepted temporarily); phased migration to Tier 1 per timelines.

---

### Development & DevOps

| Category | Tier 1 (Preferred) | Tier 2 (Accepted) | Tier 3 (Phase Out) |
|---|---|---|---|
| **Code repository** | GitLab (self-hosted) | GitHub (24-month migration) | — |
| **CI/CD** | GitLab CI, Azure DevOps | GitHub Actions (accepted) | — |
| **IaC** | Terraform | ARM templates (Azure) | — |
| **APM** | Splunk APM | Datadog (12-month migration) | — |
| **Incident mgmt** | PagerDuty | — | — |

**CloudServe Impact:** GitHub → GitLab (24 months); GitHub Actions accepted temporarily; Datadog → Splunk APM (12 months).

---

### Data & Analytics

| Category | Tier 1 (Preferred) | Tier 2 (Accepted) | Tier 3 (Phase Out) |
|---|---|---|---|
| **Data warehouse** | Azure Synapse Analytics | Snowflake (24-month migration) | — |
| **Data lake** | Azure Data Lake Gen2 | S3 (accepted for AWS workloads) | — |
| **BI** | Power BI | Looker (12-month migration) | — |
| **ETL/ELT** | Azure Data Factory | — | — |

**CloudServe Impact:** Snowflake → Synapse (24 months); S3 accepted (AWS workloads); Looker → Power BI (12 months).

---

## 7) ESG Vendor Rationalization Process

### Step 1: Vendor Inventory (Day 1-30)

| Activity | Timeline | Owner |
|---|---|---|
| **Complete vendor inventory** | Day 1-30 | CloudServe IT + ESG M&A Integration |
| **Categorize vendors (Tier 1/2/3)** | Day 1-30 | ESG Vendor Management |
| **Identify Tier 3 (phase out) vendors** | Day 1-30 | ESG M&A Integration |

### Step 2: Migration Planning (Day 30-90)

| Activity | Timeline | Owner |
|---|---|---|
| **Create migration plan for Tier 3 vendors** | Day 30-90 | ESG M&A Integration + CloudServe IT |
| **Negotiate contract exits** | Day 30-90 | ESG Procurement + Legal |
| **Estimate cost savings** | Day 30-90 | ESG Finance |

### Step 3: Execution (Day 90+)

| Vendor | Migration Timeline | Estimated Savings |
|---|---|---:|
| **Google Workspace → M365** | 6 months | $82K/year |
| **Slack → Teams** | 6 months | $72K/year |
| **Okta → Azure AD** | 6-12 months | $98K/year |
| **Datadog → Splunk** | 12 months | $312K/year |
| **Looker → Power BI** | 12 months | $32.5K/year |
| **NetSuite → SAP** | 24 months | TBD (offset by SAP licensing) |
| **Salesforce → Dynamics 365** | 18 months | TBD (offset by D365 licensing) |

**Total Estimated Savings:** $596.5K/year (productivity tools only)

---

## 8) ESG Offshore & Contractor Policies

### Approved Offshore Partners

| Partner | Location | Focus Area | Notes |
|---|---|---|
| **Infosys** | India, Poland | Infrastructure support, app dev | Preferred partner |
| **Cognizant** | India, Philippines | Application support, testing | Preferred partner |
| **Capgemini** | India, Poland, Romania | Cloud migration, DevOps | Preferred partner |

**CloudServe Impact:** Current offshore vendors (India QA, Poland infrastructure) must be validated against ESG approved list or transitioned.

### Contractor Vetting Process

| Step | Requirement | Timeline |
|---|---|---|
| **Background check** | All contractors (criminal, employment) | Before access granted |
| **Security training** | ESG security awareness | Within 7 days |
| **NDA** | ESG standard NDA | Before access granted |
| **Access provisioning** | Azure AD B2B guest access | Day 1 |
| **Quarterly access review** | Review all contractor access | Quarterly |

---

## 9) CloudServe Talent Retention Strategy

### Retention Priorities (ESG Approach)

| Role/Level | Retention Priority | Retention Bonus | Equity Acceleration | Notes |
|---|---|---:|---:|---|
| **CTO (co-founder)** | 🔴 CRITICAL | $500K (2-year vest) | 100% unvested equity | Offer SVP title |
| **VP Engineering** | 🔴 CRITICAL | $250K (2-year vest) | 50% unvested equity | Offer Director/Sr. Director title |
| **Staff+ Engineers (2)** | 🟠 HIGH | $150K each (2-year vest) | 25% unvested equity | Technical leadership |
| **Senior SREs (4)** | 🟠 HIGH | $75K each (1-year vest) | — | Infrastructure knowledge |
| **Security Engineers (5)** | 🟡 MEDIUM | $50K each (1-year vest) | — | Security talent shortage |

**Total Retention Budget:** $1.2M-1.5M (over 2 years)

---

## 10) ESG Integration Success Metrics (Organization)

| Metric | Target | Measurement |
|---|---|---|
| **Key technical talent retention** | 90%+ in first 12 months | HR tracking (CTO, VP Eng, Staff+ engineers) |
| **Employee satisfaction** | 80%+ favorable (integration survey) | Quarterly surveys |
| **Voluntary attrition** | <15% in first 12 months | HR tracking |
| **Time to productivity (new ESG tools)** | <90 days | Training completion + tool adoption |

---

## 11) CloudServe Vendor Gaps vs. ESG Standards

| CloudServe Vendor | ESG Standard | Gap Severity | Action |
|---|---|---|---|
| **AWS** | Azure (preferred) | 🟡 LOW | Accept AWS for 12-24 months; eventual Azure migration optional |
| **Okta** | Azure AD | 🟠 MEDIUM | Migrate within 6-12 months |
| **Auth0** | Azure AD B2C | 🔴 HIGH | Migrate within 18-24 months (complex) |
| **Datadog** | Splunk | 🟠 MEDIUM | Migrate within 12 months |
| **GitHub** | GitLab | 🟡 LOW | Migrate within 24 months |
| **Google Workspace** | M365 | 🟠 MEDIUM | Migrate within 6 months |
| **Slack** | Teams | 🟡 LOW | Migrate within 6 months |
| **Salesforce** | Dynamics 365 | 🟠 MEDIUM | Migrate within 18 months |
| **NetSuite** | SAP S/4HANA | 🔴 HIGH | Migrate within 24 months |
| **Snowflake** | Synapse | 🟠 MEDIUM | Migrate within 24 months |
| **Looker** | Power BI | 🟡 LOW | Migrate within 12 months |
| **Snyk** | Checkmarx | 🟡 LOW | Migrate within 12 months |
| **Vanta** | Built-in (Purview, SailPoint) | 🟡 LOW | Phase out within 12 months |

---

## 12) ESG Vendor Consolidation Savings (CloudServe)

| Vendor Category | CloudServe Annual Spend | Post-Consolidation Savings | Notes |
|---|---:|---:|---|
| **Productivity (M365 vs. Google/Slack)** | $154K | $154K | Included in ESG M365 E5 license |
| **IdP (Azure AD vs. Okta)** | $98K | $98K | Included in ESG M365 E5 license |
| **Monitoring (Splunk vs. Datadog)** | $312K | $312K | Included in ESG Splunk license |
| **BI (Power BI vs. Looker)** | $32.5K | $32.5K | Included in ESG M365 license |
| **Compliance (built-in vs. Vanta)** | $210K | $210K | Included in ESG Purview/SailPoint |
| **TOTAL SAVINGS** | **$806.5K/year** | **$806.5K/year** | Offset by migration costs ($1.5M-3M one-time) |

**Net Savings (Year 2+):** $800K/year after migration costs recovered (payback: 2-4 years)

---

## 13) Integration Budget Summary (CloudServe → ESG)

| Category | One-Time Cost | Annual Recurring Impact |
|---|---:|---:|
| **Security remediation** | $900K-1.675M | +$445K-610K (new tools) |
| **Identity migration (Okta/Auth0)** | $625K-1.15M | -$98K (Okta savings) |
| **Application migration (ERP/CRM/HCM)** | $1.5M-3M | -$400K (app consolidation) |
| **Infrastructure integration** | $500K-1M | -$300K (tool consolidation) |
| **Compliance (ISO, GDPR, audits)** | $425K-650K | +$50K-75K (annual audits) |
| **Talent retention** | $1.2M-1.5M | $0 |
| **TOTAL INTEGRATION COST** | **$5.15M-9M** | **-$303K to +$785K** |

**ESG Budgeted Range for CloudServe:** $4M-8M (within expected range)

---

**END OF BUYER DOCUMENT 6 - ALL BUYER DOCUMENTS COMPLETE**
