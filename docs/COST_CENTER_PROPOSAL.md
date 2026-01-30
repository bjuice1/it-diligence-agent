# Cost Center - Unified Financial View

> **Purpose**: Single page consolidating all cost data with finance-focused lenses
> **Status**: Proposal
> **Date**: January 2026

---

## The Problem

Cost data is scattered across:
- Organization module (headcount costs)
- Inventory (app/infra license costs)
- Work items (one-time integration costs)
- Various cost models (not surfaced in UI)

Finance teams need ONE place to see the full cost picture.

---

## Proposed Cost Center Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        COST CENTER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  EXECUTIVE SUMMARY                                       │   │
│  │  Total Run-Rate: $X.XM/yr | One-Time: $X.XM - $X.XM     │   │
│  │  Headcount: XX FTE ($X.XM) | Non-Headcount: $X.XM       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ RUN-RATE COSTS  │ │ ONE-TIME COSTS  │ │ COST INSIGHTS   │   │
│  │ (Annual)        │ │ (Integration)   │ │ (Commentary)    │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section 1: Run-Rate Costs (Annual Recurring)

### 1.1 Headcount Costs
Source: Organization Analysis (FactStore)

| Category | FTE | Avg Comp | Total Cost | % of IT |
|----------|-----|----------|------------|---------|
| Leadership | 3 | $180K | $540K | 5% |
| Applications | 25 | $125K | $3.1M | 30% |
| Infrastructure | 18 | $110K | $2.0M | 19% |
| Security | 8 | $140K | $1.1M | 11% |
| Service Desk | 12 | $65K | $780K | 8% |
| Data/Analytics | 6 | $130K | $780K | 8% |
| PM/Governance | 5 | $115K | $575K | 6% |
| Other | 15 | $90K | $1.4M | 13% |
| **Total Headcount** | **92** | | **$10.3M** | **100%** |

Commentary:
- Headcount cost per employee: $X (benchmark: $Y)
- Key person risk: 3 individuals with unique knowledge
- Contractor ratio: X% (benchmark: Y%)

### 1.2 Non-Headcount Costs
Source: InventoryStore (Applications + Infrastructure)

| Category | Item Count | Annual Cost | Notes |
|----------|------------|-------------|-------|
| **Applications** | 33 | $7.18M | |
| - Core Business (Critical) | 8 | $3.2M | Duck Creek, Majesco, etc. |
| - ERP Systems | 2 | $586K | NetSuite + SAP |
| - HCM/HR | 2 | $478K | Workday + ADP |
| - CRM | 2 | $565K | Salesforce + Dynamics |
| - Other Applications | 19 | $2.35M | |
| **Infrastructure** | 2 | TBD | |
| - Data Centers | | | Dallas primary |
| - Cloud Services | | | |
| **Total Non-Headcount** | | **$7.18M+** | |

Commentary:
- Application cost per user: $X (need total user count)
- Dual-platform situations: ERP ($586K), CRM ($565K), HCM ($478K)
- Potential consolidation savings: $X-$Y annually

### 1.3 Vendor/MSP Costs
Source: Organization Analysis + Inventory enrichment

| Vendor/MSP | Service | FTE Equiv | Annual Cost | Risk Level |
|------------|---------|-----------|-------------|------------|
| Cognizant | Claims Support | 15 | $X | High |
| HCL | Help Desk | 8 | $X | Medium |
| ... | ... | ... | ... | ... |
| **Total MSP** | | **X** | **$X.XM** | |

Commentary:
- MSP concentration risk: X% with single vendor
- Services without internal backup: X
- Contract renewal timeline concerns: X

### 1.4 Run-Rate Summary

| Cost Type | Annual Cost | % of Total |
|-----------|-------------|------------|
| Headcount | $10.3M | 59% |
| Applications | $7.2M | 41% |
| Infrastructure | $TBD | X% |
| MSP/Vendors | $TBD | X% |
| **Total Run-Rate** | **$17.5M+** | **100%** |

---

## Section 2: One-Time Costs (Integration/Separation)

### 2.1 By Phase

| Phase | Cost Range | Key Activities |
|-------|------------|----------------|
| **Pre-Close** | $150K - $400K | DD validation, planning |
| **Day 1** | $500K - $1.5M | Identity separation, TSA setup |
| **Year 1** | $2M - $8M | App migrations, infra moves |
| **Year 2+** | $1M - $4M | ERP rationalization, optimization |
| **Total** | **$3.7M - $13.9M** | |

### 2.2 By Category

| Category | Low | Mid | High | Confidence | Source |
|----------|-----|-----|------|------------|--------|
| **Identity/IAM** | $300K | $600K | $1M | High | Industry benchmark |
| **Application Migration** | $800K | $2M | $4M | Medium | Per-app analysis |
| **ERP Rationalization** | $1.5M | $3M | $6M | Medium | Dual ERP complexity |
| **Infrastructure** | $400K | $800K | $1.5M | Medium | DC count based |
| **Security Remediation** | $200K | $400K | $700K | High | Gap analysis |
| **Network Integration** | $150K | $300K | $500K | Low | Discovery gaps |
| **Staff Aug/Consulting** | $300K | $600K | $1M | High | Industry typical |

### 2.3 Activity-Level Detail (SME-Verified)

Each activity should have:
- Description
- Cost range (low/mid/high)
- Duration estimate
- Dependencies
- SME verification status
- Assumptions

Example:
```
Activity: ERP Consolidation (NetSuite + SAP → Single Platform)
  Range: $1.5M - $6M
  Duration: 18-36 months
  Dependencies: Business process harmonization complete
  Verified By: [SME Name], [Date]
  Assumptions:
    - Assumes single-instance target
    - Does not include business process redesign
    - Based on 2,900 combined users
```

---

## Section 3: Cost Insights (Commentary)

### 3.1 Scaling Considerations

**Headcount Scaling:**
- Current IT:Employee ratio: X:X
- Post-acquisition if standalone: Likely need +X FTE for:
  - Shared services replacement
  - IT leadership gap
  - Security coverage
- Estimated additional headcount cost: $X/year

**Application Scaling:**
- License costs may increase X% due to volume discount loss
- SaaS renegotiation timing: X contracts in next 12 months

### 3.2 Areas of Concern

| Area | Issue | Cost Impact | Priority |
|------|-------|-------------|----------|
| Dual ERP | NetSuite + SAP both CRITICAL | $586K run-rate + $3M integration | High |
| Dual HCM | Workday + ADP redundancy | $478K run-rate + $300K consolidation | Medium |
| Security Gaps | 6 high-priority gaps identified | $200-400K remediation | High |
| MSP Dependency | X% of ops with single MSP | Transition risk | Medium |

### 3.3 Opportunity Areas

| Opportunity | Potential Savings | Timeframe |
|-------------|-------------------|-----------|
| CRM Consolidation | $250-300K/year | 12-18 months |
| License Optimization | $100-200K/year | 6-12 months |
| MSP Renegotiation | $X/year | Contract renewal |

---

## Section 4: Finance Lenses (Team-Built)

These are curated views your team builds and verifies:

### Lens 1: "What Does IT Really Cost?"
- Total run-rate with hidden costs exposed
- Benchmark comparison (IT spend as % of revenue)
- Per-employee IT cost

### Lens 2: "Integration Budget Planning"
- One-time costs by quarter
- Cash flow timeline
- Confidence-weighted estimates

### Lens 3: "Synergy Identification"
- Consolidation opportunities with $ values
- Quick wins vs. long-term plays
- Dependency mapping

### Lens 4: "Risk-Adjusted Costs"
- Costs if key risks materialize
- Contingency recommendations
- Scenario modeling (best/expected/worst)

---

## Data Sources & Verification

| Data Point | Source | Verification Status |
|------------|--------|---------------------|
| Headcount costs | FactStore → Organization Analysis | From documents |
| App license costs | InventoryStore | From Application Inventory doc |
| One-time estimates | Cost Engine + Benchmarks | Industry ranges |
| Activity details | Work Items + Templates | Needs SME review |

---

## Implementation Plan

### Phase 1: Cost Center Page (1-2 weeks)
- [ ] Create `/costs` route in Flask
- [ ] Build cost summary from existing data sources
- [ ] Display run-rate breakdown (headcount + apps)
- [ ] Display one-time cost summary from work items

### Phase 2: Cost Integration (2-3 weeks)
- [ ] Pull MSP costs from organization analysis
- [ ] Connect infrastructure costs from inventory
- [ ] Calculate totals and percentages
- [ ] Add benchmark comparisons

### Phase 3: Commentary & Lenses (Ongoing)
- [ ] Build insight generation from cost patterns
- [ ] Create lens templates for finance team
- [ ] Add SME verification workflow
- [ ] Export to Excel for deal models

---

## Questions for Team

1. What cost categories are most important to surface first?
2. Which one-time cost activities need SME verification?
3. What benchmarks should we use for comparison?
4. How should cost ranges be presented (low/mid/high vs. confidence intervals)?

---

*Document created: January 2026*
