# Great Insurance — Document 1: Executive IT Profile + Deal Testing Ledger (Phase 1)

> **Purpose:** Single-source-of-truth baseline + consistency anchor for the synthetic M&A IT diligence test dataset.  
> **Source:** *Target Company Profile – Great Insurance* (PDF) — cited inline where applicable.

---

## 1) Known Facts (Cited)

| Item | Value |
|---|---|
| Company | Great Insurance (Sell Side) |
| Annual revenue | **$500M** fileciteturn2file0L11-L13 |
| Employees | **2,296** fileciteturn2file0L12-L14 |
| IT budget | **$22.1M** (**4.4%** of revenue) fileciteturn2file0L15-L18 |
| IT headcount | **141** fileciteturn2file0L18-L21 |
| Applications | **33** apps; total annual app cost **$7,183,701** fileciteturn2file0L36-L45 |
| Hosting mix (apps) | **25** Cloud/SaaS; **8** On-Prem/Hybrid fileciteturn2file0L41-L45 |
| Data centers | **4** fileciteturn2file0L36-L37 |
| Infra spend | **$2,575,899** total infra spend fileciteturn2file0L110-L115 |
| DR posture | Strategy: **Hot**; DR Tier **2**; **RPO 0h**, **RTO 1h**; retention **180 days** fileciteturn2file0L115-L145 |
| Cloud footprint | **AWS us-east-1**, **25 accounts**, services include **DynamoDB/CloudFront/SQS**, **$123,334/mo**, **$1,480,007/yr** fileciteturn2file0L123-L126 |
| IT org + sourcing | Total personnel cost **$19,632,626**; **13%** outsourced; **7** teams fileciteturn2file0L146-L154 |
| Key partners | **CGI** MSP (**$623,830**, Infrastructure + Service Desk); **Ensono** (Infra, 9 HC, **$1,180,588**); **Unisys** (Service Desk, 9 HC, **$666,835**) fileciteturn2file0L157-L173 |
| Security tools (observed) | Firewall: **Juniper**; Endpoint: **SentinelOne**; SIEM: **Elastic SIEM**; MFA: **Okta**; Email: **Mimecast** fileciteturn2file0L126-L133 |

---

## 2) Synthetic “Test Hooks” (Injected for Tool-Testing)

> **Important:** The following are *intentional complications* to test AI tool reasoning (not asserted as source facts).

| Hook ID | Test Hook | Why it’s useful |
|---|---|---|
| H1 | **Carve-out perimeter:** one business unit uses shared corporate services (Identity + Email) | Tests separation logic + TSA dependencies |
| H2 | **Parent-hosted app:** one “Billing” platform is contractually parent-hosted until Day-180 | Tests hosting vs ownership vs contract constraints |
| H3 | **Contract cliff:** one Tier-1 vendor renewal inside 90 days | Tests risk flags + cost modeling sensitivity |
| H4 | **Dual-tool reality:** overlap across sources (e.g., multiple SIEM/endpoint/IAM tools) | Tests reconciliation + “source conflict” detection |
| H5 | **DC constraint:** one colo lease non-cancellable for 12 months | Tests exit feasibility + stranded cost |
| H6 | **Data residency constraint:** subset of PII workloads must remain initially | Tests migration sequencing + compliance impacts |

---

## 3) Deal Testing Ledger (Must-Match Facts)

| Ledger Fact | Baseline Value | Must match across docs? | Where it should appear |
|---|---:|---|---|
| # Applications | 33 fileciteturn2file0L19-L22 | Yes | Doc 2 + Doc 1 totals |
| App annual cost | $7,183,701 fileciteturn2file0L40-L42 | Yes | Doc 2 roll-up |
| Cloud/SaaS apps | 25 fileciteturn2file0L41-L44 | Yes | Doc 2 hosting mix |
| On-Prem/Hybrid apps | 8 fileciteturn2file0L43-L45 | Yes | Doc 2 hosting mix |
| # Data centers | 4 fileciteturn2file0L110-L112 | Yes | Doc 3 DC inventory |
| Infra spend | $2,575,899 fileciteturn2file0L112-L115 | Yes | Doc 3 economics |
| Cloud provider | AWS (us-east-1), 25 accounts fileciteturn2file0L123-L126 | Yes | Doc 3 cloud table |
| Cloud spend | $1,480,007/yr fileciteturn2file0L123-L126 | Yes | Doc 3 economics |
| DR strategy | Hot fileciteturn2file0L115-L117 | Yes | Doc 6 BCDR section |
| DR tier | Tier 2 fileciteturn2file0L136-L143 | Yes | Doc 6 BCDR section |
| RPO / RTO | 0h / 1h fileciteturn2file0L139-L143 | Yes | Doc 6 BCDR section |
| Backup retention | 180 days fileciteturn2file0L144-L145 | Yes | Doc 6 BCDR section |
| IT headcount | 141 fileciteturn2file0L147-L149 | Yes | Doc 6 org model |
| Outsourced % | 13% fileciteturn2file0L150-L153 | Yes | Doc 6 sourcing model |
| MSP + key vendors | CGI / Ensono / Unisys fileciteturn2file0L157-L173 | Yes | Doc 6 vendor table |

---

## 4) Environment Development Matrix (Global Structure)

| Domain | Current State (baseline) | Buyer Day-1 target | Buyer Day-100 target | TSA dependency | Primary risk |
|---|---|---|---|---|---|
| Core apps | 33 apps; mixed hosting (25 SaaS, 8 on-prem/hybrid) fileciteturn2file0L38-L45 | Stabilize access + connectivity | Start rationalization plan | Medium–High | Platform sprawl |
| Hosting | 4 DC + AWS footprint fileciteturn2file0L110-L126 | Preserve uptime + routing | DC exit plan + cloud landing zone | Medium | Stranded DC cost (H5) |
| DR/BC | Hot, Tier 2; RPO 0h, RTO 1h fileciteturn2file0L115-L145 | Confirm DR runbooks + ownership | Re-test under buyer tooling | Low–Medium | Testing evidence gaps |
| Security/IAM | Security tools present; overlap by design (H4) fileciteturn2file0L126-L133 | Maintain control coverage Day-1 | Standardize SIEM/EDR/IAM | Medium | Tool sprawl + blind spots |
| IT Ops model | 141 IT HC; 13% outsourced; CGI/Ensono/Unisys fileciteturn2file0L146-L173 | Confirm vendor roles + SLAs | Sourcing optimization | Medium | Contract cliff (H3) |

---

## 5) Consistency Checks (What the AI Tool Must Validate)

1) **Application totals reconcile**: 33 apps and $7.183M roll-up match the app inventory. fileciteturn2file0L38-L42  
2) **Hosting mix stays consistent**: 25 SaaS vs 8 on-prem/hybrid is reflected everywhere. fileciteturn2file0L41-L45  
3) **Infra footprint matches**: 4 DC + AWS (25 accounts, $1.48M/yr). fileciteturn2file0L110-L126  
4) **BCDR is stable**: Hot / Tier 2 / RPO 0h / RTO 1h / 180-day retention. fileciteturn2file0L115-L145  
5) **Org + sourcing aligns**: 141 HC, 13% outsourced, vendors + values consistent. fileciteturn2file0L146-L173  
