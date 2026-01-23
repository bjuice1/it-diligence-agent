# Great Insurance — Document 7: Buyer Day‑1 / Day‑100 Disposition + TSA Workplan (Phase 7)

> **Purpose:** A single execution grid that ties together **Apps + Infra + Data + Security + Ops** into a buyer-focused Day‑1 stabilization plan and Day‑100 transformation plan.  
> **Sources:** Derived from Documents 1–6 (which cite the target PDF). This document includes **injected test hooks** explicitly labeled.

---

## 1) Deal Context Snapshot (Must-Match Anchors)

| Anchor | Value |
|---|---|
| Applications | **33** total; **$7,183,701** annual cost fileciteturn2file0L36-L45 |
| Hosting mix | **25** Cloud/SaaS; **8** On-Prem/Hybrid fileciteturn2file0L41-L45 |
| Data centers | **4** fileciteturn2file0L36-L37 |
| Infra spend | **$2,575,899** fileciteturn2file0L110-L115 |
| Cloud | **AWS us-east-1**, **25 accounts**, **$1,480,007/yr** fileciteturn2file0L123-L126 |
| BCDR | **Hot**, Tier **2**, **RPO 0h**, **RTO 1h**, retention **180 days** fileciteturn2file0L115-L145 |
| IT org | **141** IT HC; **13%** outsourced fileciteturn2file0L146-L154 |

---

## 2) Injected “Test Hook” Commitments (Control Ledger)

These are the intentional complications that the AI tool must reason through:

| Hook | Injected Reality | Where it is encoded |
|---|---|---|
| H1 Carve-out perimeter | Shared corporate services for **Identity + Email** (dependency risk) | Docs 1, 2, 5, 7 |
| H2 Parent-hosted app | **Netcracker Revenue Mgmt** is TSA-locked **until Day‑180** | Doc 2, Doc 7 |
| H3 Contract cliff | Renewal due **<90 days** (ServiceNow + Workday) | Doc 2, Doc 6, Doc 7 |
| H4 Dual-tool reality | Overlapping tooling across sources (SIEM/EDR/Identity/Email security) | Doc 5, Doc 7 |
| H5 DC lease constraint | One DC has non-cancellable lease for 12 months | Doc 3, Doc 7 |
| H6 Data residency | PII constrained initially to **AWS us-east-1** until Day‑120 | Doc 4, Doc 7 |

---

## 3) Buyer Disposition Strategy (Definitions)

| Disposition | Meaning |
|---|---|
| **Keep** | Retain as-is; stabilize and govern |
| **Keep w TSA** | Keep operational but under TSA constraint for a defined period |
| **Consolidate** | Multiple tools exist; converge to one standard |
| **Migrate** | Move hosting/platform (e.g., on-prem → cloud, tool A → tool B) |
| **Replace** | Plan to swap to buyer standard platform |
| **Retire** | Decommission post-close / post-migration |
| **Split** | Separate shared environment/tenancy into standalone |

---

## 4) Day‑1 / Day‑100 Execution Grid (Top Dependencies)

> **How to use:** This is the “one table” your AI tool should be able to generate consistently: **workstream → deliverables → dependencies → risks → TSA**.

| Workstream | Day‑1 Objective | Day‑1 Deliverables | Day‑100 Objective | Day‑100 Deliverables | TSA Dependency | Primary Risk |
|---|---|---|---|---|---|---|
| Identity & Access | Maintain access Day‑1 | Confirm authoritative IdP; enforce MFA | Converge identity architecture | Unified IdP + RBAC | **High (H1)** | Access cutover outage |
| Email & Collaboration | Preserve comms | Mail routing + security continuity | Standardize security + governance | Policy + training + tooling standard | **High (H1)** | Misconfig / phishing exposure |
| Core Billing | Maintain revenue ops | Netcracker runs under TSA | Buyer hosting control | Exit TSA; migrate/convert | **Yes (H2)** | Billing interruptions |
| ITSM / Service | Preserve incident response | Keep ServiceNow live; ensure ticket intake | Standardize processes | Tool/process convergence | Possible | Renewal cliff (H3) |
| Security Monitoring | Avoid blind spots | Ensure log forwarding into chosen SIEM | Consolidate + mature SOC | Runbooks + detections | Medium | Overlap creates gaps (H4) |
| Data & Analytics | Preserve reporting | Snowflake/BI continuity; respect residency | Formal data governance | Data products + model standard | **Yes (H6)** | Compliance delay |
| Data Centers & Hosting | Keep uptime | DC connectivity, monitoring | Consolidation / exit plan | Close/retain plan + migration waves | Medium | Stranded costs (H5) |

---

## 5) System-Level Disposition (Seed List)

### 5A) Shared Services Disposition (Carve-out / TSA Hotspots)
These are the **highest Day‑1 integration risks** because they create immediate continuity requirements.

| Domain | Systems/Tools (Observed) | Day‑1 Disposition | Day‑100 Target | Dependency | Notes |
|---|---|---|---|---|---|
| Identity/MFA | Entra ID; Okta fileciteturn5file0L96-L98 fileciteturn6file0L45-L47 | **Keep (stabilize)** | **Consolidate** | H1 | Must identify authoritative identity plane |
| Email security | Mimecast; Proofpoint fileciteturn6file0L46-L47 fileciteturn5file0L102-L104 | Keep | Consolidate | H1/H4 | Confirm mail routing + filtering ownership |
| SIEM | Elastic SIEM; Splunk ES fileciteturn6file0L44-L46 fileciteturn5file0L101-L103 | Keep (ensure forwarding) | Consolidate | H4 | Avoid telemetry loss during convergence |
| EDR | SentinelOne; CrowdStrike fileciteturn6file0L44-L45 fileciteturn5file0L94-L96 | Keep | Consolidate | H4 | Policy + agent overlap risks |

### 5B) Core Systems Disposition (Policy / Claims / Billing / ERP)
| Domain | Systems (Observed) | Day‑1 Disposition | Day‑100 Target | TSA | Notes |
|---|---|---|---|---|---|
| Policy | Duck Creek Policy; Guidewire PolicyCenter; Majesco fileciteturn3file1L11-L16 | Keep | Rationalize (assess) | No | Multiple policy platforms = longer-term rationalization |
| Claims | Duck Creek Claims; Guidewire ClaimCenter fileciteturn3file1L13-L16 | Keep | Rationalize (assess) | No | Maintain continuity, then assess consolidation |
| Billing | Netcracker Revenue Mgmt fileciteturn3file1L19-L21 | **Keep w TSA** | Migrate/Exit TSA | **Yes (H2)** | TSA until Day‑180 (Injected) |
| Billing | CSG Ascendon; Amdocs Revenue Mgmt fileciteturn3file1L15-L17 fileciteturn5file0L84-L86 | Keep | Rationalize | No | Determine which billing is in-scope per perimeter |
| ERP | NetSuite; SAP S/4HANA fileciteturn3file1L17-L19 fileciteturn5file0L79-L81 | Keep | Assess Replace/Consolidate | Possible | Two ERPs implies integration + reporting complexity |

---

## 6) TSA Workplan (Phased)

> **Goal:** A buyer-friendly TSA plan with explicit **start/stop conditions**.

| TSA Area | Why TSA is needed | Start Condition | Exit Criteria | Target Exit |
|---|---|---|---|---|
| Identity/Email shared services (H1) | Shared auth + comms dependencies | Close / Day‑1 | New IdP/email routing validated + cutover runbook executed | Day‑60 to Day‑120 (Injected) |
| Parent-hosted Billing (H2) | Netcracker hosted by Parent | Close / Day‑1 | Buyer hosting control + parallel run validated | **Day‑180** (Injected) |
| Data residency (H6) | PII must remain in region | Close / Day‑1 | Compliance sign-off + evidence pack | **Day‑120** (Injected) |
| ITSM continuity | Ticketing/SLA continuity | Close / Day‑1 | Buyer support model stood up | Day‑30 to Day‑90 (Injected) |

---

## 7) “Contract Cliff” Response Plan (H3)

> **Injected:** Workday + ServiceNow flagged <90 day renewal risk in Doc 2 (for testing).

| Vendor/App | Risk | Day‑1 Action | Day‑30 Action | Day‑60 Action | Owner |
|---|---|---|---|---|---|
| Workday HCM fileciteturn5file0L85-L87 | Renewal <90d (Injected) | Confirm renewal date + notice terms | Decide renew vs bridge | Execute | Apps lead |
| ServiceNow ITSM fileciteturn5file0L95-L97 | Renewal <90d (Injected) | Confirm renewal date + entitlements | Decide renew vs replace | Execute | Ops/ITSM lead |

---

## 8) Day‑1 Readiness Checklist (What to Validate Immediately)

| Area | Validation Item | Evidence |
|---|---|---|
| Access | Authoritative IdP + MFA enforced | Config export, policy screenshots (to be collected) |
| Security monitoring | Log forwarding continuity | SIEM source list + ingest checks |
| Billing continuity | Netcracker runbooks + parent constraints | TSA clause + operational runbook |
| DR readiness | DR tests + ownership | DR runbook + last test date (to be collected) |
| Hosting | DC + cloud connectivity baseline | Network diagrams + monitoring dashboards |

---

## 9) Next Add-On (Optional “Document 8”)
If you want an even better testing dataset, we can create a **Document 8: Synthetic VDR Artifacts Pack**:
- sample TSA clauses,
- sample network diagrams (text-based),
- sample incident runbooks,
- sample vendor renewal notices,
- sample DR test report excerpt (synthetic),
all consistent with the anchors above.
