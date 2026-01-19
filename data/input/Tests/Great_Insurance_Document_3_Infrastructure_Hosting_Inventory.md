# Great Insurance — Document 3: Infrastructure & Hosting Inventory (Phase 3)

> **Purpose:** Table-driven infrastructure baseline for testing AI extraction, reconciliation, DC exit reasoning, and TSA/stranded-cost logic in an M&A workflow.  
> **Source:** *Target Company Profile – Great Insurance* (PDF) — cited inline for factual fields.  
> **Note on “Injected” fields:** Certain columns below are **intentionally injected test hooks** (not asserted as source facts) to improve tool-testing.

---

## 1) Infrastructure Rollups (Baseline)

| Metric | Value |
|---|---:|
| Data centers | **4** fileciteturn6file0L26-L30 |
| Cloud providers | **1** fileciteturn6file0L28-L31 |
| Total infra spend | **$2,575,899** fileciteturn6file0L30-L34 |
| DR strategy | **Hot** fileciteturn6file0L32-L34 |
| AWS region | **us-east-1** fileciteturn6file1L25-L28 |
| AWS accounts | **25** fileciteturn6file1L25-L28 |
| AWS services (observed) | **DynamoDB, CloudFront, SQS** fileciteturn6file1L25-L28 |
| AWS spend | **$123,334/mo**; **$1,480,007/yr** fileciteturn6file1L25-L28 |

---

## 2) Data Center Facilities (Inventory)

**Column rules**
- Columns **Facility → Annual Cost** are *source facts* (cited).
- Columns **Exit Feasibility / Lease Constraint** are **Injected** for tool-testing.

| Facility | Location | Type | Tier | Capacity | Annual Cost | Exit Feasibility (Injected) | Lease Constraint (Injected) |
|---|---|---|---|---:|---:|---|---|
| Primary DC – Dallas | Dallas, TX | Colocation | Tier 3 | 24 racks | $992,625 fileciteturn6file1L19-L23 | Medium | **Non-cancellable 12 months (H5)** |
| Secondary DC – Seattle | Seattle, WA | Colocation | Tier 3 | 3 racks | $103,267 fileciteturn6file1L21-L24 | High | None |
| Secondary DC – Phoenix | Phoenix, AZ | Owned | Tier 2 | 11 racks | $0 fileciteturn6file1L22-L24 | High | None |
| Secondary DC – Atlanta | Atlanta, GA | Owned | Tier 2 | 4 racks | $0 fileciteturn6file1L23-L24 | High | None |

---

## 3) Cloud Infrastructure (Inventory)

| Provider | Region | Accounts | Services (Observed) | Monthly | Annual |
|---|---|---:|---|---:|---:|
| AWS | us-east-1 | 25 | DynamoDB, CloudFront, SQS | $123,334/mo | $1,480,007/yr fileciteturn6file1L25-L28 |

---

## 4) Spend Check (Reconciliation Aid)

> The profile provides **Total Infra Spend = $2,575,899** and **AWS Annual = $1,480,007**.  
> Use this table to test whether your AI tool can reconcile and highlight remaining “non-cloud infra” spend.

| Spend Bucket | Annual Amount | Status |
|---|---:|---|
| Total Infra Spend | $2,575,899 fileciteturn6file0L30-L34 | Source fact |
| Cloud (AWS) | $1,480,007 fileciteturn6file1L25-L28 | Source fact |
| Implied non-cloud infra (Total − AWS) | $1,095,892 | **Derived** (reconciliation check) |

---

## 5) Environment Development Matrix (Infrastructure / Hosting)

| Tower | Current State (baseline) | Buyer Day-1 target | Buyer Day-100 target | TSA dependency | Primary risk |
|---|---|---|---|---|---|
| Data centers | 4 sites (2 colo, 2 owned) fileciteturn6file1L19-L24 | Preserve uptime/connectivity | Consolidation plan (exit/retain) | Medium | Stranded cost from lease constraint (H5) |
| Cloud | AWS us-east-1, 25 accounts fileciteturn6file1L25-L28 | Confirm landing zone + access | Account rationalization / shared services | Medium | Governance + account sprawl |
| DR posture | Hot strategy fileciteturn6file0L32-L34 | Confirm DR ownership + runbooks | Re-test under buyer tooling | Low–Medium | Evidence + runbook maturity |

---

## 6) Hook-Control Ledger (Infrastructure)

| Hook | Rule | Current setting in Document 3 |
|---|---|---|
| H5 DC constraint | One colo has a non-cancellable lease | **Primary DC – Dallas** flagged “Non-cancellable 12 months” (Injected) |
| (Reconciliation) Cloud vs total infra | Tool should explain remaining infra spend | Implied non-cloud infra = **$1,095,892** (Derived) |

---

## 7) Consistency Checks (Doc 1 ↔ Doc 3)

1) Data centers = **4** fileciteturn6file0L26-L30  
2) Total infra spend = **$2,575,899** fileciteturn6file0L30-L34  
3) Cloud provider = **AWS**; region **us-east-1**; accounts **25** fileciteturn6file1L25-L28  
4) AWS spend = **$123,334/mo** and **$1,480,007/yr** fileciteturn6file1L25-L28  
5) DR strategy = **Hot** fileciteturn6file0L32-L34  

---

## Next Document (when you want it)
**Document 4: Data, Analytics & Integration Inventory**  
(we’ll implement the **H6 data residency** hook there).
