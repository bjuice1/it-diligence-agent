# Enterprise Solutions Group (ESG) — Buyer Document 2: Application Portfolio & Standards

> **Entity:** BUYER
> **Purpose:** ESG standard application portfolio for overlap analysis and migration planning

---

## 1) ESG Corporate Application Portfolio

| Category | Application | Vendor | Users | Annual Cost | Notes |
|---|---|---|---:|---:|---|
| **ERP** | SAP S/4HANA Cloud | SAP | 12,400 | $18,500,000 | Global ERP system |
| **CRM** | Microsoft Dynamics 365 Sales | Microsoft | 3,200 | $9,800,000 | Enterprise CRM |
| **HCM** | Workday HCM | Workday | 24,500 | $12,200,000 | Global HRIS |
| **Finance** | SAP S/4HANA + BlackLine | SAP, BlackLine | 1,800 | $6,400,000 | Financial close automation |
| **Procurement** | SAP Ariba | SAP | 2,100 | $3,200,000 | Source-to-pay |
| **Collaboration** | Microsoft 365 E5 | Microsoft | 24,500 | $14,700,000 | Email, docs, SharePoint |
| **Communication** | Microsoft Teams | Microsoft | 24,500 | Included in M365 | Chat, meetings |
| **BI** | Power BI Premium | Microsoft | 4,800 | $2,400,000 | Enterprise BI |
| **ITSM** | ServiceNow ITSM | ServiceNow | 2,100 | $4,200,000 | IT service management |

---

## 2) CloudServe vs. ESG Application Overlap Analysis

| Category | CloudServe Application | ESG Standard | Overlap? | Disposition Recommendation |
|---|---|---|---|---|
| **ERP** | NetSuite | SAP S/4HANA | ✅ YES | Migrate to SAP (24 months) |
| **CRM** | Salesforce | Dynamics 365 | ✅ YES | Migrate to Dynamics 365 (18 months) |
| **HCM** | BambooHR, Rippling | Workday | ✅ YES | Migrate to Workday (12 months) |
| **Collaboration** | Google Workspace | Microsoft 365 | ✅ YES | Migrate to M365 (6 months) |
| **Communication** | Slack | Teams | ✅ YES | Migrate to Teams (6 months) |
| **BI** | Looker | Power BI | ✅ YES | Migrate to Power BI (12 months) |
| **ITSM** | None | ServiceNow | ❌ NO | Extend ServiceNow to CloudServe |
| **Finance** | NetSuite, Bill.com | SAP, BlackLine | ⚠️ PARTIAL | Migrate to SAP ecosystem |
| **Monitoring** | Datadog | Splunk | ⚠️ PARTIAL | Migrate to Splunk (12 months) |

**Estimated Consolidation Savings:** $600K-900K/year (CloudServe SaaS licenses)
**Estimated Migration Cost:** $1.5M-3M (one-time)

---

## 3) Application Migration Priority Matrix

| Application | Priority | Complexity | Timeline | Rationale |
|---|---|---|---|---|
| **M365 (email/collaboration)** | 🔴 HIGH | LOW | 6 months | User productivity, security (MFA via Azure AD) |
| **Teams (communication)** | 🔴 HIGH | LOW | 6 months | Bundled with M365 |
| **Workday (HCM)** | 🟠 MEDIUM | MEDIUM | 12 months | HR data consolidation |
| **Dynamics 365 (CRM)** | 🟠 MEDIUM | MEDIUM | 18 months | Sales process alignment |
| **SAP S/4HANA (ERP)** | 🟡 LOW | HIGH | 24 months | Complex migration, business continuity risk |
| **Power BI (BI)** | 🟡 LOW | LOW | 12 months | Analytics consolidation |
| **Splunk (monitoring)** | 🟠 MEDIUM | MEDIUM | 12 months | Security requirement (SIEM) |

---

**END OF BUYER DOCUMENT 2**
