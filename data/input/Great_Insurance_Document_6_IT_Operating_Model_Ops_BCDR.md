# Great Insurance — Document 6: IT Operating Model, Sourcing, ITSM & BCDR Summary (Phase 6/7)

> **Purpose:** Table-driven operating model baseline for testing AI extraction of org economics, vendor sourcing, ITSM coverage, and DR/BC alignment in an M&A workflow.  
> **Source:** *Target Company Profile – Great Insurance* (PDF) — cited inline for factual fields.  
> **Note on “Injected” fields:** Where explicitly labeled, certain fields are **injected** for tool-testing (not asserted source facts).

---

## 1) Org & Spend Rollups (Baseline)

| Metric | Value |
|---|---:|
| IT headcount | **141** fileciteturn2file0L147-L149 |
| Total personnel cost | **$19,632,626** fileciteturn2file0L146-L149 |
| Outsourced percentage | **13%** fileciteturn2file0L150-L153 |
| # IT teams | **7** fileciteturn2file0L150-L154 |
| IT budget (context) | **$22.1M** fileciteturn2file0L15-L18 |

---

## 2) IT Team Breakdown (Inventory)

| Team | Headcount | Total Personnel Cost | Outsourced % | Notes |
|---|---:|---:|---:|---|
| IT Leadership | 8 | $2,075,736 | 0% | Leadership + oversight fileciteturn6file1L32-L41 |
| Applications | 46 | $6,634,032 | 0% | Core apps delivery fileciteturn6file1L41-L45 |
| Data & Analytics | 17 | $2,715,440 | 0% | Reporting/BI/analytics fileciteturn6file1L43-L46 |
| Cybersecurity | 11 | $1,867,863 | 0% | Security governance/ops fileciteturn6file1L44-L47 |
| Infrastructure | 24 | $3,148,235 | 38% | Includes Ensono support fileciteturn6file1L45-L48 |
| Service Desk | 21 | $1,555,949 | 43% | Includes Unisys support fileciteturn6file1L46-L49 |
| Enterprise PMO | 14 | $1,635,371 | 0% | Projects/portfolio fileciteturn6file1L47-L50 |

---

## 3) Key Roles (Sampling)

| Role | Count | Salary Range | Total Cost |
|---|---:|---|---:|
| VP of IT / VP of Technology | 2 | $180k–$280k | $557,490 fileciteturn6file1L55-L60 |
| Directors (IT/Security/Apps) | 6 | $145k–$225k | $1,106,673 fileciteturn6file1L57-L60 |

---

## 4) Vendor & Sourcing Model (Inventory)

### 4A) Managed Services Provider (MSP)
| Vendor | Scope | Annual Cost |
|---|---|---:|
| CGI | Infrastructure + Service Desk | $623,830 fileciteturn2file0L157-L163 |

### 4B) Outsourced Team Providers
| Function | Vendor | Headcount | Run Rate |
|---|---|---:|---:|
| Infrastructure | Ensono | 9 | $1,180,588 fileciteturn2file0L164-L168 |
| Service Desk | Unisys | 9 | $666,835 fileciteturn2file0L169-L173 |

---

## 5) ITSM Coverage (Observed)

> **Observed ITSM tools** from the application list:  
> - **ServiceNow ITSM** fileciteturn5file0L95-L97  
> - **Jira Service Management** fileciteturn5file0L91-L93

| ITSM Capability | Tool(s) Observed | Primary Tool (Injected) | Notes (Injected) |
|---|---|---|---|
| Incident / Request | ServiceNow ITSM; Jira Service Management fileciteturn5file0L91-L97 | ServiceNow | Jira used by select IT teams |
| Change management | ServiceNow ITSM (assumed) | ServiceNow | Validate CAB cadence |
| CMDB / Asset | ServiceNow (assumed) | ServiceNow | Validate population completeness |

---

## 6) BCDR Summary (Baseline)

| Item | Value |
|---|---|
| DR strategy | **Hot** fileciteturn2file0L115-L117 |
| DR Tier | **2** fileciteturn2file0L136-L143 |
| RPO | **0 hours** fileciteturn2file0L139-L143 |
| RTO | **1 hour** fileciteturn2file0L139-L143 |
| Backup retention | **180 days** fileciteturn2file0L144-L145 |
| Backup tooling (infra section) | Druva fileciteturn6file0L47-L48 |
| DR application (app list) | Zerto fileciteturn5file0L103-L104 |

### 6A) BCDR Tooling Reconciliation (testing-friendly)
| Capability | Tool (Infra) | Tool (App) | Reconciliation Hypothesis (Injected) |
|---|---|---|---|
| Backup | Druva fileciteturn6file0L47-L48 | — | Enterprise backup platform |
| DR replication | — | Zerto fileciteturn5file0L103-L104 | Zerto used for DR orchestration/replication |

---

## 7) Environment Development Matrix (Ops Model)

| Domain | Current State (baseline) | Buyer Day-1 target | Buyer Day-100 target | TSA dependency | Primary risk |
|---|---|---|---|---|---|
| IT org | 141 HC, 7 teams fileciteturn2file0L146-L154 | Confirm ownership + accountability | Optimize spans/layers | Medium | Knowledge transfer |
| Sourcing | CGI MSP + Ensono + Unisys fileciteturn2file0L157-L173 | Validate contracts + SLAs | Consolidate vendors | Medium | Contract/renewal risk |
| ITSM | ServiceNow + Jira SM fileciteturn5file0L91-L97 | Ensure incident continuity | Standardize tooling | Medium | Process variation |
| BCDR | Hot, Tier 2, RPO 0h, RTO 1h fileciteturn2file0L115-L145 | Confirm DR runbooks + evidence | Re-test under buyer | Low–Medium | Audit readiness |

---

## 8) Hook-Control Ledger (Ops / Org)

| Hook | Rule | Current setting in Document 6 |
|---|---|---|
| H3 Contract cliff | At least one renewal in <90d exists (from Doc 2) | ServiceNow ITSM / Workday flagged <90d in Doc 2 (Injected) |
| H1 Carve-out perimeter | Shared services create TSA need | Identity/Email dependencies drive Day-1 cutover sequencing (ties to Docs 2/5) |
| Reconciliation | DR/backup tools appear across sections | Druva (infra) + Zerto (apps) reconciled in 6A |

---

## 9) Final “Must-Match” Ledger Cross-Check (All Docs)

| Ledger Fact | Expected | Source |
|---|---:|---|
| # Applications | 33 | fileciteturn2file0L36-L45 |
| App annual cost | $7,183,701 | fileciteturn2file0L40-L42 |
| # Data centers | 4 | fileciteturn2file0L36-L37 |
| Infra spend | $2,575,899 | fileciteturn2file0L110-L115 |
| AWS accounts | 25 | fileciteturn2file0L123-L126 |
| AWS annual spend | $1,480,007 | fileciteturn2file0L123-L126 |
| DR (Hot / Tier 2 / RPO 0h / RTO 1h / 180d) | Yes | fileciteturn2file0L115-L145 |
| IT headcount | 141 | fileciteturn2file0L146-L149 |
| Outsourced % | 13% | fileciteturn2file0L150-L153 |

---

## Dataset Complete (6 Documents)

You now have:
1) Executive IT Profile + Deal Testing Ledger  
2) Application Inventory & Rationalization Workbook  
3) Infrastructure & Hosting Inventory  
4) Data, Analytics & Integration Inventory  
5) Security, IAM & Compliance Inventory + Control Mapping  
6) IT Operating Model, Sourcing, ITSM & BCDR Summary
