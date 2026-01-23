# Great Insurance — Document 2: Application Inventory & Rationalization Workbook (Phase 2)

> **Purpose:** Table-driven application inventory for testing AI extraction, reconciliation, risk flagging, and “hook” reasoning in an M&A IT diligence workflow.  
> **Source:** *Target Company Profile – Great Insurance* (PDF) — cited inline for factual columns.

---

## Step 1 — Inventory Rollups (Baseline)

| Metric | Value |
|---|---:|
| Total applications | **33** fileciteturn3file0L35-L38 |
| Total annual app cost | **$7,183,701** fileciteturn3file0L36-L39 |
| Cloud/SaaS apps | **25** fileciteturn3file0L39-L42 |
| On-Prem/Hybrid apps | **8** fileciteturn3file0L40-L42 |

---

## Step 1 — Category Rollup

| Category | Count | Annual Cost |
|---|---:|---:|
| Policy Administration | 3 | $1,399,745 fileciteturn3file0L45-L47 |
| Claims Management | 2 | $857,113 fileciteturn3file0L46-L48 |
| Billing | 3 | $837,814 fileciteturn3file0L47-L49 |
| ERP | 2 | $586,011 fileciteturn3file0L48-L50 |
| CRM/Agency Management | 2 | $565,800 fileciteturn3file0L49-L51 |
| HR/HCM | 2 | $478,092 fileciteturn3file0L50-L52 |
| Finance | 2 | $345,860 fileciteturn3file0L51-L52 |
| Analytics & Actuarial | 2 | $335,348 fileciteturn3file0L52-L54 |
| Collaboration | 2 | $301,571 fileciteturn3file0L53-L55 |
| Document Management | 2 | $274,987 fileciteturn3file0L54-L55 |
| Data & Analytics | 2 | $266,830 fileciteturn3file1L3-L6 |
| IT Service Management | 2 | $263,636 fileciteturn3file1L3-L6 |
| Email & Communication | 2 | $224,385 fileciteturn3file1L5-L6 |
| Identity & Access | 2 | $218,024 fileciteturn3file1L5-L7 |
| Security | 2 | $203,484 fileciteturn3file1L6-L8 |
| Backup & DR | 1 | $25,000 fileciteturn3file1L7-L8 |

---

## Step 2 — Full Application Inventory (33 rows) + Injected Test-Hook Columns

**Column rules**
- Columns **Application → Criticality** are *source facts* (cited).
- Columns **Carve-out dependency / TSA lock / Contract renewal window** are **injected test hooks** for tool-testing.

| Application | Vendor | Category | Version | Hosting | Users | Annual Cost | Criticality | Carve-out dependency (Injected) | Parent-hosted / TSA-locked until Day-X (Injected) | Contract renewal window (Injected) |
|---|---|---|---|---|---:|---:|---|---|---|---|
| Duck Creek Policy | Duck Creek | Policy Administration | 12 | On Prem | 1,407 | $546,257 | CRITICAL fileciteturn3file1L11-L16 | N | N | >180d |
| Majesco Policy for L&A | Majesco | Policy Administration | 2023.2 | On Prem | 1,565 | $440,225 | CRITICAL fileciteturn3file1L11-L13 | N | N | >180d |
| Duck Creek Claims | Duck Creek | Claims Management | 11 | On Prem | 1,608 | $435,426 | CRITICAL fileciteturn3file1L13-L15 | N | N | >180d |
| Guidewire ClaimCenter | Guidewire | Claims Management | Jasper | Cloud | 1,348 | $421,687 | CRITICAL fileciteturn3file1L13-L16 | N | N | >180d |
| Guidewire PolicyCenter | Guidewire | Policy Administration | Kufri | On Prem | 1,252 | $413,263 | CRITICAL fileciteturn3file1L14-L16 | N | N | >180d |
| CSG Ascendon | CSG | Billing | 2022 | SaaS | 1,534 | $343,532 | HIGH fileciteturn3file1L15-L17 | N | N | 90–180d |
| Salesforce Sales Cloud | Salesforce | CRM/Agency Management | Spring ’24 | SaaS | 1,308 | $311,556 | LOW fileciteturn3file1L16-L18 | Y | N | >180d |
| NetSuite | Oracle | ERP | 2023.1 | SaaS | 1,049 | $309,562 | CRITICAL fileciteturn3file1L17-L19 | N | N | >180d |
| ADP Workforce Now | ADP | HR/HCM | 2024 | SaaS | 1,385 | $281,181 | HIGH fileciteturn3file1L18-L20 | Y | N | 90–180d |
| Netcracker Revenue Management | NEC/Netcracker | Billing | 18 | Cloud | 1,444 | $279,087 | HIGH fileciteturn3file1L19-L21 | N | **Y — Day-180** | 90–180d |
| SAP S/4HANA | SAP | ERP | 2020 | Hybrid | 1,917 | $276,449 | CRITICAL fileciteturn5file0L79-L81 | N | N | >180d |
| Microsoft Dynamics 365 Sales | Microsoft | CRM/Agency Management | 2024 Wave 1 | SaaS | 1,074 | $254,244 | MEDIUM fileciteturn5file0L80-L82 | Y | N | 90–180d |
| BlackLine | BlackLine | Finance | evergreen | SaaS | 1,583 | $240,728 | HIGH fileciteturn5file0L81-L83 | N | N | >180d |
| Amdocs Revenue Management | Amdocs | Billing | 2022.1 | On Prem | 1,211 | $215,194 | HIGH fileciteturn5file0L84-L86 | N | N | 90–180d |
| Workday HCM | Workday | HR/HCM | 2024R1 | SaaS | 1,908 | $196,910 | HIGH fileciteturn5file0L85-L87 | Y | N | **<90d** |
| Qlik Sense | Qlik | Analytics & Actuarial | May 2024 | On Prem | 1,992 | $195,736 | MEDIUM fileciteturn5file0L86-L88 | N | N | >180d |
| Box Enterprise | Box | Document Management | evergreen | SaaS | 1,741 | $170,462 | LOW fileciteturn5file0L87-L89 | Y | N | >180d |
| Microsoft 365 E3 | Microsoft | Collaboration | evergreen | SaaS | 1,278 | $162,259 | MEDIUM fileciteturn5file0L88-L90 | Y | N | >180d |
| Microsoft Power BI Premium | Microsoft | Data & Analytics | evergreen | SaaS | 749 | $160,093 | MEDIUM fileciteturn5file0L89-L91 | N | N | 90–180d |
| Microsoft Exchange Online | Microsoft | Email & Communication | evergreen | SaaS | 1,171 | $155,967 | MEDIUM fileciteturn5file0L90-L92 | Y | N | >180d |
| Jira Service Management | Atlassian | IT Service Management | evergreen | SaaS | 1,549 | $140,056 | HIGH fileciteturn5file0L91-L93 | N | N | 90–180d |
| Databricks | Databricks | Analytics & Actuarial | evergreen | SaaS | 1,583 | $139,612 | MEDIUM fileciteturn5file0L92-L94 | N | N | >180d |
| Slack Business+ | Salesforce | Collaboration | evergreen | SaaS | 1,648 | $139,312 | MEDIUM fileciteturn5file0L93-L95 | Y | N | 90–180d |
| CrowdStrike Falcon | CrowdStrike | Security | evergreen | SaaS | 1,930 | $124,054 | HIGH fileciteturn5file0L94-L96 | N | N | 90–180d |
| ServiceNow ITSM | ServiceNow | IT Service Management | Vancouver | SaaS | 1,471 | $123,580 | HIGH fileciteturn5file0L95-L97 | N | N | **<90d** |
| Microsoft Entra ID (Azure AD) | Microsoft | Identity & Access | evergreen | SaaS | 1,357 | $120,324 | MEDIUM fileciteturn5file0L96-L98 | Y | N | >180d |
| Snowflake | Snowflake | Data & Analytics | evergreen | SaaS | 1,554 | $106,737 | LOW fileciteturn5file0L97-L99 | N | N | >180d |
| Concur | SAP | Finance | evergreen | SaaS | 1,007 | $105,131 | HIGH fileciteturn5file0L98-L100 | Y | N | 90–180d |
| Microsoft SharePoint Online | Microsoft | Document Management | evergreen | SaaS | 1,228 | $104,525 | MEDIUM fileciteturn5file0L99-L101 | Y | N | >180d |
| CyberArk Privileged Access | CyberArk | Identity & Access | 13.0 | SaaS | 1,638 | $97,700 | LOW fileciteturn5file0L100-L102 | N | N | >180d |
| Splunk Enterprise Security | Splunk | Security | 9.2 | SaaS | 1,672 | $79,430 | HIGH fileciteturn5file0L101-L103 | N | N | 90–180d |
| Proofpoint Email Protection | Proofpoint | Email & Communication | evergreen | SaaS | 1,530 | $68,419 | MEDIUM fileciteturn5file0L102-L104 | Y | N | 90–180d |
| Zerto | Zerto | Backup & DR | 9.7 | On Prem | 1,601 | $25,000 | MEDIUM fileciteturn5file0L103-L104 | N | N | >180d |

---

## Step 3 — Hook-Control Ledger (Must Stay Stable)

| Hook | Rule | Current setting in Document 2 |
|---|---|---|
| H1 Carve-out perimeter | Shared services should be identifiable in apps list | Carve-out dependency **Y** tagged for Identity/Email/Collab/Docs + selected HR/Finance |
| H2 Parent-hosted app | **Exactly one** app gets TSA-lock Day-180 | **Netcracker Revenue Management = Y / Day-180** |
| H3 Contract cliff | At least one “<90d” renewal exists | **Workday HCM** + **ServiceNow ITSM** flagged **<90d** |
| H4 Dual-tool reality | Overlap exists across security tooling | Security apps include **CrowdStrike** + **Splunk ES** (Doc 5 will introduce additional observed tools to reconcile) fileciteturn5file0L94-L103 |

---

## Document 2 — Consistency Checks (Internal)

1) Total apps = **33** fileciteturn3file0L35-L38  
2) Total cost = **$7,183,701** fileciteturn3file0L36-L39  
3) Hosting mix = **25** SaaS/Cloud + **8** On-Prem/Hybrid fileciteturn3file0L39-L42  
4) Billing category totals remain **3 apps / $837,814** fileciteturn3file0L47-L49  
5) Exactly **one** TSA-locked app exists (Netcracker) and nothing else is flagged.

---

## Next Step (when you want it)
Add **Disposition columns** for M&A testing:
- Day-1 disposition (Keep / Keep w TSA / Replace / Retire / Split)
- Day-100 target (Keep / Consolidate / Migrate / Replace / Retire)
- Primary dependency (Identity / Network / Data / Parent hosting / Vendor renewal)
