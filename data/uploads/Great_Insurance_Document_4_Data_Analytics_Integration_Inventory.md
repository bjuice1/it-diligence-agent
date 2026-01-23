# Great Insurance — Document 4: Data, Analytics & Integration Inventory (Phase 4)

> **Purpose:** Table-driven data/analytics baseline for testing AI extraction, dependency reasoning, integration mapping, and migration constraints in an M&A workflow.  
> **Source:** *Target Company Profile – Great Insurance* (PDF) — cited inline for factual fields.  
> **Note on “Injected” fields:** Certain columns/rows below are **intentionally injected test hooks** (not asserted as source facts) to improve tool-testing.

---

## 1) Known Data & Analytics Platforms (Observed in Application List)

The following platforms appear in the target’s application list and will anchor the data estate inventory:

- **Microsoft Power BI Premium** fileciteturn5file0L89-L91  
- **Snowflake** fileciteturn5file0L97-L99  
- **Databricks** fileciteturn5file0L92-L94  
- **Qlik Sense** fileciteturn5file0L86-L88  

---

## 2) Data Platform Inventory (Table)

**Column rules**
- Columns **Platform → Annual Cost** are *source facts* (cited from the app list).
- Columns **Data Domains / Feeds / Criticality** are **assumptions/inferred placeholders** to test tool reasoning (not asserted facts unless separately sourced).

| Platform | Type | Hosting | Users | Annual Cost | Data Domains (Assumed) | Primary Inputs (Assumed) | Primary Outputs (Assumed) | Criticality (Assumed) |
|---|---|---|---:|---:|---|---|---|---|
| Microsoft Power BI Premium | BI / Reporting | SaaS | 749 | $160,093 fileciteturn5file0L89-L91 | Enterprise reporting | Snowflake, core apps | Exec dashboards, ops reports | Medium |
| Snowflake | Data warehouse | SaaS | 1,554 | $106,737 fileciteturn5file0L97-L99 | Policy/Claims/Billing data marts | Core apps, integrations | BI, data sharing | High |
| Databricks | Compute / ML | SaaS | 1,583 | $139,612 fileciteturn5file0L92-L94 | Modeling, actuarial, ML | Snowflake/raw feeds | Models, feature sets | Medium |
| Qlik Sense | BI / Analytics | On-Prem | 1,992 | $195,736 fileciteturn5file0L86-L88 | Department analytics | Extracts, flat files | Team dashboards | Medium |

---

## 3) Core System Data Sources (Integration “Touchpoints”)

> The profile includes multiple core systems (policy, claims, billing, ERP).  
> This table creates a **standard set of integration touchpoints** for M&A testing.

**Source-anchored systems (examples)**
- Policy: Duck Creek Policy; Guidewire PolicyCenter; Majesco Policy for L&A fileciteturn3file1L11-L16  
- Claims: Duck Creek Claims; Guidewire ClaimCenter fileciteturn3file1L13-L16  
- Billing: CSG Ascendon; Netcracker Revenue Mgmt; Amdocs Revenue Mgmt fileciteturn3file1L15-L21 fileciteturn5file0L84-L86  
- ERP: NetSuite; SAP S/4HANA fileciteturn3file1L17-L19 fileciteturn5file0L79-L81  

| Source System | Data Domain | Integration Method (Injected/Assumed) | Downstream Targets | Failure Impact (Assumed) | TSA Risk (Assumed) |
|---|---|---|---|---|---|
| Policy Admin (Duck Creek / Majesco / Guidewire) | Policy master, premiums | ETL + APIs | Snowflake, BI | High | Medium |
| Claims (Duck Creek / Guidewire) | Claims, reserves | ETL + batch files | Snowflake, BI | High | Medium |
| Billing (Netcracker / CSG / Amdocs) | Invoicing, payments | ETL + events | Snowflake, Finance | High | **High** (aligns with parent-hosted hook in Doc 2) |
| ERP (NetSuite / SAP) | GL, AP/AR | APIs + connectors | BI, Finance | Medium | Medium |

---

## 4) Data Governance & Residency Constraints (H6 — Injected Test Hook)

> **H6 (Injected):** A subset of PII workloads must remain in a specific environment initially (data residency / regulatory / contractual).  
> This is *not* stated as a fact in the profile — it is included to improve tool-testing.

| Constraint Area | Current State (Injected) | Buyer Day-1 Constraint | Buyer Day-100 Target | Primary Impact |
|---|---|---|---|---|
| PII residency | PII dataset for claims/policy must remain in **AWS us-east-1** until compliance sign-off | Cannot migrate PII out of region/cloud until Day-120 | Controlled migration with evidence package | Sequencing, tooling, cost |
| Data sharing | No external data sharing permitted without anonymization | Masking/tokenization required | Standardized data products | Data pipeline design |
| Access controls | Elevated access restricted to small set of roles | MFA + PAM enforced | RBAC + least privilege | Identity dependencies |

**AWS region anchor:** us-east-1 fileciteturn6file1L25-L28

---

## 5) Environment Development Matrix (Data / Analytics)

| Domain | Current State (baseline) | Buyer Day-1 target | Buyer Day-100 target | TSA dependency | Primary risk |
|---|---|---|---|---|---|
| Warehouse + BI | Snowflake + Power BI Premium fileciteturn5file0L89-L99 | Preserve reporting continuity | Standardize KPI model | Medium | Data model inconsistency |
| Advanced analytics | Databricks present fileciteturn5file0L92-L94 | Maintain pipelines | Re-platform if needed | Low–Medium | Skills/tooling mismatch |
| Dept analytics | Qlik Sense on-prem fileciteturn5file0L86-L88 | Keep running | Consolidate to BI standard | Medium | Shadow analytics |
| Residency constraint | H6 injected constraint | Respect Day-1 residency rule | Evidence-driven migration | Medium | Compliance delays |

---

## 6) Hook-Control Ledger (Data)

| Hook | Rule | Current setting in Document 4 |
|---|---|---|
| H6 Data residency | Some PII workloads constrained initially | PII must remain in **AWS us-east-1** until Day-120 (Injected) |
| Dependency link | Billing feeds should show elevated TSA risk | Billing touchpoint marked **High TSA risk** (Assumed for testing) |

---

## 7) Consistency Checks (Doc 1/2/3 ↔ Doc 4)

1) Data platforms listed here appear in the application inventory (Doc 2). fileciteturn5file0L86-L99  
2) AWS region referenced = **us-east-1** (Doc 3). fileciteturn6file1L25-L28  
3) Core system names align to Doc 2 (Policy/Claims/Billing/ERP examples). fileciteturn3file1L11-L21 fileciteturn5file0L79-L86  

---

## Next Document (when you want it)
**Document 5: Security / IAM / Compliance Inventory + Control Mapping**  
(we’ll implement the **H4 dual-tool reality** reconciliation explicitly there).
