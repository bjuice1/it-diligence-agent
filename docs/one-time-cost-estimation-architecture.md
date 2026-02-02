# One-Time Cost Estimation Architecture

## Executive Summary

This document outlines the current architecture for one-time cost estimation in the IT Due Diligence tool, provides a critical audit of gaps, and proposes a roadmap to commercial-grade capabilities.

**Current State:** Solid MVP with transparent build-up methodology
**Gap to Commercial:** Missing resource-level detail, timeline integration, and scenario modeling
**Recommendation:** Phased enhancement with leadership alignment on key decisions

---

## 1. Data Flow Architecture

### High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ONE-TIME COST ESTIMATION PIPELINE                         │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   INPUTS     │     │  EXTRACTION  │     │   REASONING  │     │   COSTING    │
│              │     │              │     │              │     │              │
│ • VDR Docs   │────▶│ • Parse PDFs │────▶│ • Identify   │────▶│ • Link to    │
│ • Interviews │     │ • Extract    │     │   work items │     │   anchors    │
│ • IT Surveys │     │   facts      │     │ • Assign     │     │ • Apply      │
│ • Vendor     │     │ • Count      │     │   phase/     │     │   discounts  │
│   quotes     │     │   entities   │     │   priority   │     │ • Regional   │
│              │     │              │     │              │     │   adjust     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  RAW DATA    │     │    FACTS     │     │  WORK ITEMS  │     │ COST BUILD-  │
│              │     │              │     │              │     │    UPS       │
│ PDFs, Excel, │     │ • 1,500 users│     │ • Identity   │     │ • Anchor     │
│ Word docs    │     │ • 45 apps    │     │   separation │     │ • Method     │
│              │     │ • 12 sites   │     │ • License    │     │ • Quantity   │
│              │     │ • 200 servers│     │   transition │     │ • Discounts  │
│              │     │ • Azure AD   │     │ • App        │     │ • Region     │
│              │     │ • SAP ERP    │     │   migration  │     │ • Total      │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Estimation Sources

The system supports multiple estimation sources with different confidence levels:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           ESTIMATION SOURCES                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  BENCHMARK  │  │  INVENTORY  │  │   VENDOR    │  │ HISTORICAL  │         │
│  │             │  │             │  │   QUOTE     │  │             │         │
│  │ COST_ANCHORS│  │ Real counts │  │             │  │ Past project│         │
│  │ from market │  │ from facts  │  │ Actual $$$  │  │ actuals     │         │
│  │ research    │  │             │  │ from vendor │  │             │         │
│  │             │  │             │  │             │  │             │         │
│  │ Confidence: │  │ Confidence: │  │ Confidence: │  │ Confidence: │         │
│  │   MEDIUM    │  │    HIGH     │  │    HIGH     │  │   MEDIUM    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                │                 │
│         └────────────────┴────────────────┴────────────────┘                 │
│                                   │                                          │
│                                   ▼                                          │
│                          ┌─────────────┐                                     │
│                          │   HYBRID    │  Weighted combination               │
│                          │  ESTIMATE   │  of multiple sources                │
│                          │             │                                     │
│                          │ Confidence: │                                     │
│                          │    HIGH     │                                     │
│                          └─────────────┘                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### The Build-Up Chain (Traceability)

Every cost estimate traces back to source documents:

```
DOCUMENT              FACT                  WORK ITEM             COST BUILD-UP
    │                    │                      │                      │
    ▼                    ▼                      ▼                      ▼
"Org chart          "1,500 total          "Separate             anchor: identity_separation
 shows 1,500         employees in          identity              method: fixed_by_size
 employees"          IT scope"             infrastructure"       tier: medium (1,000-5,000)
                                                                 unit_cost: $300K-$800K
                                                                 volume_discount: 0.75
                                                                 regional_mult: 0.35
                                                                 total: $79K-$210K
                                                                 assumptions: [
                                                                   "1,500 users → medium tier",
                                                                   "Volume discount: 25%",
                                                                   "Regional (India): 35%"
                                                                 ]
                                                                 confidence: HIGH
```

---

## 2. Current Capabilities

### What's Implemented

| Capability | Description | Status |
|------------|-------------|--------|
| **Cost Anchors** | 50+ market benchmarks for IT activities | ✅ Complete |
| **Build-Up Transparency** | Shows anchor, method, quantity, assumptions | ✅ Complete |
| **Volume Discounts** | Auto-apply discounts at scale (users, apps, sites) | ✅ Complete |
| **Regional Multipliers** | Adjust for offshore/nearshore delivery | ✅ Complete |
| **Multiple Sources** | Benchmark, inventory, vendor quote, historical | ✅ Complete |
| **Hybrid Estimates** | Combine multiple sources with weighting | ✅ Complete |
| **Vendor Quote Import** | CSV/JSON import for actual vendor pricing | ✅ Complete |
| **Excel Export** | Cost Build-Up worksheet with full detail | ✅ Complete |
| **Confidence Tracking** | High/Medium/Low based on data sources | ✅ Complete |

### Volume Discount Curves

| Scale | Users | Apps | Sites | Servers |
|-------|-------|------|-------|---------|
| Tier 1 | 0-99: 0% | 0-9: 0% | 0-4: 0% | 0-24: 0% |
| Tier 2 | 100-499: 5% | 10-24: 10% | 5-14: 10% | 25-99: 10% |
| Tier 3 | 500-999: 15% | 25-49: 20% | 15-29: 20% | 100-249: 20% |
| Tier 4 | 1,000-2,499: 25% | 50-99: 30% | 30-49: 30% | 250-499: 30% |
| Tier 5 | 2,500-4,999: 35% | 100+: 40% | 50+: 40% | 500+: 40% |
| Tier 6 | 5,000+: 45% | - | - | - |

### Regional Multipliers

| Region | Multiplier | Notes |
|--------|------------|-------|
| US East (base) | 1.00 | NYC, Boston, DC |
| US West | 1.15 | SF, Seattle, LA |
| US Midwest | 0.85 | Chicago, Denver |
| UK | 1.10 | London |
| Western Europe | 1.05 | Germany, France |
| Eastern Europe | 0.50 | Poland, Romania |
| India | 0.35 | Major IT hub |
| Mexico | 0.55 | Nearshore |

---

## 3. Critical Audit: Gaps for Commercial Use

### Gaps That Will Concern Clients

| Gap | Why It Matters | Likely Client Question |
|-----|----------------|------------------------|
| **Static Benchmarks** | Anchors from 2024 research, no auto-update | "Are your numbers current?" |
| **No Validation Loop** | Can't show estimate vs actual accuracy | "How accurate have you been historically?" |
| **Single Scenario** | No what-if modeling capability | "What if we do 50% offshore?" |
| **No Risk Quantification** | Contingency is not data-driven | "Why 15% contingency vs 25%?" |
| **Missing Labor Breakdown** | No FTE × Rate × Duration detail | "Show me the resource plan" |
| **No Timeline Integration** | Costs without cash flow schedule | "When do we spend this money?" |
| **No Dependencies** | Work items treated as independent | "What has to happen before what?" |
| **No Change Tracking** | Can't show estimate evolution | "Why did the cost change from last week?" |

### Incomplete Features

| Area | Current State | Commercial Need |
|------|---------------|-----------------|
| Vendor Quotes | Import exists, not in UI | Quote management dashboard |
| Confidence Scoring | Labels only (H/M/L) | Quantified probability bands |
| Source Lineage | Tracked internally | Visual lineage diagram |
| Volume Discounts | Fixed curves | Client-specific schedules |
| Regional Rates | Generic multipliers | Client's actual blended rates |

### What's Working Well

| Strength | Commercial Value |
|----------|------------------|
| Build-up transparency | Defensible, auditable estimates |
| Multiple estimation sources | Not relying on single data point |
| Structured data model | Clean, extensible, professional |
| Excel export | Clients can review and adjust |
| Phase grouping | Aligns with deal timeline |

---

## 4. Commercial-Grade Requirements

### Estimation Confidence Framework

```
┌────────────────────────────────────────────────────────────────────────┐
│                    ESTIMATION CONFIDENCE BANDS                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  DATA QUALITY          ESTIMATE RANGE        CONTINGENCY               │
│  ────────────          ──────────────        ───────────               │
│                                                                        │
│  HIGH                  ±15%                  10%                       │
│  (Vendor quote +       $850K - $1.15M        $100K                     │
│   inventory +                                                          │
│   historical)                                                          │
│                                                                        │
│  MEDIUM                ±30%                  20%                       │
│  (Benchmark +          $700K - $1.3M         $200K                     │
│   inventory)                                                           │
│                                                                        │
│  LOW                   ±50%                  35%                       │
│  (Benchmark only,      $500K - $1.5M         $350K                     │
│   limited data)                                                        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Resource-Based Costing (Not Yet Implemented)

**Current State:**
```
Work Item: Identity Separation
Cost: $300K-$800K (single range)
```

**Commercial Need:**
```
Work Item: Identity Separation

LABOR DETAIL:
┌────────────────────────────────────────────────────┐
│ Role              │ FTEs │ Weeks │ Rate/Hr │ Total │
├───────────────────┼──────┼───────┼─────────┼───────┤
│ Solution Architect│  1   │   4   │  $250   │ $40K  │
│ IAM Engineer      │  3   │  12   │  $175   │ $252K │
│ Project Manager   │  1   │  16   │  $200   │ $128K │
│ QA Engineer       │  2   │   6   │  $150   │ $72K  │
├───────────────────┼──────┼───────┼─────────┼───────┤
│ Labor Subtotal    │      │       │         │ $492K │
└────────────────────────────────────────────────────┘

NON-LABOR DETAIL:
┌────────────────────────────────────────────────────┐
│ Item              │ Qty  │ Unit Cost │ Total      │
├───────────────────┼──────┼───────────┼────────────┤
│ Azure AD P2 (1yr) │ 1500 │ $9/user/mo│ $162K      │
│ Migration Tooling │  1   │ Fixed     │ $50K       │
│ Training          │ 1500 │ $30/user  │ $45K       │
├───────────────────┼──────┼───────────┼────────────┤
│ Non-Labor Subtotal│      │           │ $257K      │
└────────────────────────────────────────────────────┘

TOTAL:           $749K
Contingency (20%): $150K
────────────────────────
LOADED TOTAL:    $899K
```

### Timeline Integration (Not Yet Implemented)

**Current State:**
```
Phase: Day_100
Cost: $500K
```

**Commercial Need:**
```
┌─────────────────────────────────────────────────────────┐
│ CASH FLOW PROJECTION - Identity Separation              │
├─────────────────────────────────────────────────────────┤
│ Month 1:   $50K   ████                    (Planning)    │
│ Month 2:   $75K   ██████                  (Design)      │
│ Month 3:  $150K   ████████████            (Build-Peak)  │
│ Month 4:  $125K   ██████████              (Build)       │
│ Month 5:   $75K   ██████                  (Test)        │
│ Month 6:   $25K   ██                      (Hypercare)   │
├─────────────────────────────────────────────────────────┤
│ TOTAL:    $500K                                         │
└─────────────────────────────────────────────────────────┘
```

### Scenario Modeling (Not Yet Implemented)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SCENARIO COMPARISON                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SCENARIO              BASE        OFFSHORE     ACCELERATED   MINIMAL   │
│  ────────              ────        ────────     ───────────   ───────   │
│                                                                         │
│  Delivery Model        US-based    60% India    US-based      Hybrid    │
│  Timeline              18 months   18 months    12 months     24 months │
│  Scope                 Full        Full         Full          Core only │
│                                                                         │
│  ONE-TIME COST         $4.2M       $2.8M        $5.1M         $2.1M     │
│  Run-Rate Impact       +$1.2M/yr   +$1.0M/yr    +$1.2M/yr     +$0.8M/yr │
│  Risk Level            Medium      Medium-High  High          Low       │
│                                                                         │
│  ► RECOMMENDED                     ✓                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Proposed Roadmap

### Phase 3A: Foundation (Recommended Next)

| Feature | Description | Effort | Impact |
|---------|-------------|--------|--------|
| Labor Detail Model | FTE × Rate × Weeks breakdown | Medium | HIGH |
| Auto-Contingency | Calculate contingency from confidence level | Low | HIGH |
| Variance Tracking | Store estimate vs actual for calibration | Medium | HIGH |
| Source Lineage UI | Visual diagram showing data sources | Low | MEDIUM |

### Phase 3B: Advanced Capabilities

| Feature | Description | Effort | Impact |
|---------|-------------|--------|--------|
| Timeline Integration | Cash flow by month/quarter | High | HIGH |
| Scenario Modeling | Compare 2-3 delivery scenarios | High | HIGH |
| Dynamic Benchmarks | API for quarterly price updates | Medium | MEDIUM |
| Client Discount Import | Client-specific volume/rate schedules | Low | MEDIUM |

### Phase 3C: Differentiators

| Feature | Description | Effort | Impact |
|---------|-------------|--------|--------|
| AI Price Research | Live web search for current pricing | High | HIGH |
| Historical Project DB | Past project actuals for calibration | Medium | HIGH |
| Monte Carlo Simulation | Probabilistic cost modeling | High | MEDIUM |
| Deal Model Integration | Export to client financial models | High | MEDIUM |

---

## 6. Leadership Decisions Required

### Strategic Decisions

| Decision | Options | Recommendation | Why It Matters |
|----------|---------|----------------|----------------|
| **Target Accuracy** | ±15% vs ±30% vs "directional" | ±30% for Phase 1 | Sets expectation with clients; ±15% requires vendor quotes |
| **Benchmark Source** | Internal research vs Licensed data vs Hybrid | Hybrid | Licensed data (Gartner, etc.) adds credibility but costs $50K+/yr |
| **Delivery Model Default** | US-only vs Blended vs Client-specific | Blended (60/40) | Affects all cost estimates; need standard assumption |
| **Contingency Policy** | Fixed % vs Confidence-based vs Client choice | Confidence-based | More defensible; auto-calculated from data quality |

### Resource Decisions

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| **Historical Data** | Build internally vs Partner vs Skip | Build internally | Need 10-20 past projects for calibration; ~2 months effort |
| **Benchmark Updates** | Annual vs Quarterly vs Real-time | Quarterly | Balance freshness vs effort; annual too stale |
| **Client Customization** | Standard only vs Light custom vs Full custom | Light custom | Allow discount schedule import, not full model rebuild |

### Go-to-Market Decisions

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| **Positioning** | "AI-powered" vs "Data-driven" vs "Expert-validated" | Data-driven + Expert-validated | AI alone may raise accuracy concerns |
| **Deliverable Format** | Tool access vs Export only vs Hybrid | Hybrid (Excel + Dashboard) | Clients want to manipulate numbers |
| **Pricing Basis** | Per-deal vs Subscription vs Included | Per-deal initially | Prove value before subscription model |

### Confirmation Needed

Before proceeding with Phase 3A, please confirm:

- [ ] **Accuracy target:** Are we comfortable stating "±30% accuracy at medium confidence"?
- [ ] **Delivery model default:** Should we assume blended delivery (60% onshore / 40% offshore)?
- [ ] **Contingency approach:** Agree to auto-calculate contingency based on data quality?
- [ ] **Historical data:** Commit to documenting 10+ past projects for calibration?
- [ ] **Resource allocation:** Approve ~2-3 weeks development for Phase 3A?

---

## 7. Appendix: Technical Details

### Current Cost Model Files

| File | Purpose |
|------|---------|
| `tools_v2/cost_model.py` | Cost anchors, volume curves, regional multipliers |
| `tools_v2/cost_estimator.py` | Estimation functions, vendor quote import |
| `tools_v2/reasoning_tools.py` | CostBuildUp dataclass, WorkItem model |
| `tools_v2/excel_export.py` | Cost Build-Up worksheet generation |

### Cost Anchor Categories

| Category | Count | Examples |
|----------|-------|----------|
| One-Time Separation | 15 | Identity separation, app migration, network separation |
| TSA Exit | 8 | Identity exit, email exit, infrastructure exit |
| Run-Rate | 12 | Microsoft licensing, cloud hosting, MSP services |
| Acquisition/Integration | 10 | Identity integration, ERP consolidation |

### Data Quality Scoring

| Source Combination | Confidence | Suggested Contingency |
|--------------------|------------|----------------------|
| Vendor quote + Inventory + Historical | HIGH | 10% |
| Benchmark + Inventory | MEDIUM | 20% |
| Vendor quote only | MEDIUM-HIGH | 15% |
| Benchmark only | LOW | 35% |
| No data (estimate) | VERY LOW | 50% |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-02 | IT DD Team | Initial architecture documentation |

---

*This document should be reviewed with leadership before proceeding with Phase 3 development.*
