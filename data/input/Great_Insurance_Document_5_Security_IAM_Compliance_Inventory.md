# Great Insurance — Document 5: Security, IAM & Compliance Inventory + Control Mapping (Phase 5)

> **Purpose:** Table-driven security/IAM baseline for testing AI reconciliation across conflicting sources, control coverage reasoning, Day-1 risk posture, and tool rationalization logic in an M&A workflow.  
> **Sources:**  
> - *Target Company Profile – Great Insurance* (PDF) — “IT Infrastructure” tool list for baseline security tooling.  
> - *Target Company Profile – Great Insurance* (PDF) — application list for security + identity applications.  
> **Note on “Injected” fields:** Certain columns below are **intentionally injected test hooks** (not asserted as source facts) to improve tool-testing.

---

## 1) Observed Security / IAM Tooling (Two Source Views)

### 1A) Infrastructure Security Tools (from infra section)
| Capability | Tool (Observed) |
|---|---|
| Firewall | Juniper fileciteturn6file0L41-L44 |
| Endpoint Protection | SentinelOne fileciteturn6file0L44-L45 |
| SIEM | Elastic SIEM fileciteturn6file0L44-L46 |
| MFA | Okta fileciteturn6file0L45-L47 |
| Email Security | Mimecast fileciteturn6file0L46-L47 |
| Backup (Security adjacent) | Druva fileciteturn6file0L47-L48 |

### 1B) Security & Identity Applications (from app inventory list)
| Capability | Tool (Observed) |
|---|---|
| Endpoint / EDR | CrowdStrike Falcon fileciteturn5file0L94-L96 |
| SIEM / Security Analytics | Splunk Enterprise Security fileciteturn5file0L101-L103 |
| Identity (IdP/Directory) | Microsoft Entra ID (Azure AD) fileciteturn5file0L96-L98 |
| Privileged Access (PAM) | CyberArk Privileged Access fileciteturn5file0L100-L102 |
| Email Security | Proofpoint Email Protection fileciteturn5file0L102-L104 |

---

## 2) Reconciliation Table (H4 — Dual-Tool Reality)

> **Goal:** Make the duplication visible so the AI tool must explain/resolve it.
> - This is explicitly aligned to **H4** from Document 1 (dual-tool reality).  
> - Rows below show **Observed** tools from two different sections that cover similar capabilities.

| Control Domain | Infra Tool (Observed) | App Tool (Observed) | Reconciliation Hypothesis (Injected) | Rationalization Priority (Injected) |
|---|---|---|---|---|
| Endpoint / EDR | SentinelOne fileciteturn6file0L44-L45 | CrowdStrike fileciteturn5file0L94-L96 | Dual-run during transition or inconsistent reporting | High |
| SIEM | Elastic SIEM fileciteturn6file0L44-L46 | Splunk ES fileciteturn5file0L101-L103 | Different scopes (infra vs security) or tool overlap | High |
| Email Security | Mimecast fileciteturn6file0L46-L47 | Proofpoint fileciteturn5file0L102-L104 | Business units on different stacks / legacy vs target | Medium |
| Identity (IdP/MFA) | Okta (MFA) fileciteturn6file0L45-L47 | Entra ID (IdP/Directory) fileciteturn5file0L96-L98 | Entra for directory; Okta for MFA/SSO (or vice versa) | High |
| Privileged Access | (Not listed in infra tools) | CyberArk fileciteturn5file0L100-L102 | PAM exists but not captured in infra tool list | Medium |

---

## 3) Security / IAM Inventory (Client-Ready)

**Column rules**
- Columns **Capability → Tools Observed** are source facts.
- Columns **Primary / Secondary / Coverage notes** are **Injected** for tool-testing.

| Capability | Tools Observed | Primary Tool (Injected) | Secondary Tool (Injected) | Coverage Notes (Injected) |
|---|---|---|---|---|
| Firewall | Juniper fileciteturn6file0L41-L44 | Juniper | — | Network perimeter control |
| Endpoint / EDR | SentinelOne; CrowdStrike fileciteturn6file0L44-L45 fileciteturn5file0L94-L96 | CrowdStrike | SentinelOne | Consolidate within 6 months |
| SIEM | Elastic SIEM; Splunk ES fileciteturn6file0L44-L46 fileciteturn5file0L101-L103 | Splunk ES | Elastic | Normalize log sources Day-1 |
| MFA / SSO | Okta; Entra ID fileciteturn6file0L45-L47 fileciteturn5file0L96-L98 | Entra ID | Okta | Clarify authoritative IdP |
| PAM | CyberArk fileciteturn5file0L100-L102 | CyberArk | — | Privileged access governance |
| Email security | Mimecast; Proofpoint fileciteturn6file0L46-L47 fileciteturn5file0L102-L104 | Proofpoint | Mimecast | Align to email platform |
| Backup | Druva fileciteturn6file0L47-L48 | Druva | — | Backup protection + retention |

---

## 4) Control Mapping (Basic)

> A lightweight mapping to test whether the AI can relate tooling to control objectives.

| Control Objective | Evidence/Tooling (Observed) | Gaps to Validate (Injected) |
|---|---|---|
| Identity assurance (authn/authz) | Entra ID; Okta fileciteturn5file0L96-L98 fileciteturn6file0L45-L47 | Confirm MFA enforcement + conditional access coverage |
| Privileged access governance | CyberArk fileciteturn5file0L100-L102 | Confirm break-glass accounts + logging to SIEM |
| Threat detection & response | CrowdStrike; SentinelOne; Splunk ES; Elastic SIEM fileciteturn5file0L94-L96 fileciteturn6file0L44-L46 fileciteturn5file0L101-L103 | Confirm SOC coverage, alert triage process |
| Email protection | Mimecast; Proofpoint fileciteturn6file0L46-L47 fileciteturn5file0L102-L104 | Confirm phishing simulation / user training |
| Data protection | Druva (backup) fileciteturn6file0L47-L48 | Confirm encryption at rest/in transit standards |

---

## 5) Environment Development Matrix (Security / IAM)

| Domain | Current State (baseline) | Buyer Day-1 target | Buyer Day-100 target | TSA dependency | Primary risk |
|---|---|---|---|---|---|
| Endpoint / EDR | Two tools indicated (SentinelOne + CrowdStrike) fileciteturn6file0L44-L45 fileciteturn5file0L94-L96 | Maintain coverage, centralize policies | Consolidate to single EDR | Medium | Gaps from tool overlap |
| SIEM | Elastic SIEM + Splunk ES fileciteturn6file0L44-L46 fileciteturn5file0L101-L103 | Ensure log forwarding Day-1 | Standardize SOC + detections | Medium | Blind spots during consolidation |
| Identity / MFA | Entra + Okta both present fileciteturn5file0L96-L98 fileciteturn6file0L45-L47 | Confirm authoritative IdP | Unified identity architecture | **High** (ties to carve-out shared services) | Access cutover risk |
| Email security | Mimecast + Proofpoint fileciteturn6file0L46-L47 fileciteturn5file0L102-L104 | Preserve filtering | Standardize | Medium | Misconfigurations during transition |
| PAM | CyberArk present fileciteturn5file0L100-L102 | Ensure privileged workflows Day-1 | Expand least privilege | Low–Medium | Incomplete onboarding |

---

## 6) Hook-Control Ledger (Security)

| Hook | Rule | Current setting in Document 5 |
|---|---|---|
| H4 Dual-tool reality | Overlap across sources must be explicit | Endpoint/SIEM/Email/Identity show overlap across infra vs app lists |
| H1 Carve-out perimeter | Shared identity/email drives TSA | Identity/MFA domain flagged **High TSA dependency** (assumed) |

---

## 7) Consistency Checks (Doc 1/2/3 ↔ Doc 5)

1) Tools from infra section match the infra facts (Juniper/SentinelOne/Elastic SIEM/Okta/Mimecast/Druva). fileciteturn6file0L41-L48  
2) Security & identity apps match Doc 2 (CrowdStrike/Splunk/Entra/CyberArk/Proofpoint). fileciteturn5file0L94-L104  
3) Dual-tool overlaps are flagged explicitly for testing (H4).  

---

## Next Document (when you want it)
**Document 6: IT Organization, Sourcing, IT Ops / ITSM, and BCDR Summary**  
(we’ll tie DR facts + vendor model together and ensure all must-match ledger facts reconcile).
