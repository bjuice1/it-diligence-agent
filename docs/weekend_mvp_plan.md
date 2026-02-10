# Weekend MVP Plan: 15 Hours — Ship Something Real

## The Three Things That Matter

If we only do three things this weekend:

1. **Drivers + Overrides + Persistence** (rock solid)
2. **8 Core Deterministic Cost Models** with scenarios + assumptions
3. **Exportable CSVs** (costs/drivers/assumptions) — model-ready

Everything else is Phase 2.

---

## What We're Cutting (Phase 2)

| Cut | Why |
|-----|-----|
| TSA UI with editable durations | Nice to have, not MVP |
| Work item override UI | Drivers are upstream, fix those first |
| 15+ cost model variants | 8 core models cover 80% |
| Fancy drilldown pages | Read-only table is enough for demo |
| Parent entity as full data model | Two fields (`owned_by`, `shared_with_parent`) is enough |

---

## What We're Building (MVP Scope)

### Deliverable 1: Driver Extraction + Override System

**What it does:**
- Extracts quantitative drivers from facts (user_count, sites, apps, etc.)
- Tracks source (which fact ID)
- Persists overrides when analyst corrects a value
- Merges extracted + overrides into "effective drivers"
- Stable keys for diff detection on rerun

**Output:**
```python
DealDrivers(
    total_users=850,          # source: F-ORG-012
    sites=4,                  # source: F-INFRA-001
    total_apps=47,            # source: counted from applications domain
    erp_system="SAP",         # source: F-APP-003
    identity_shared=True,     # source: F-IAM-007
    owned_by_parent=["identity", "dc_hosting", "wan"],  # derived
)
```

### Deliverable 2: 8 Core Cost Models (Deterministic)

**Standard template for each:**
```python
CostModel(
    work_item_type="identity_separation",

    # Costs
    base_services_cost=75_000,
    per_user_cost=15,
    per_site_cost=5_000,

    # Licenses (annual)
    license_per_user_annual=108,  # Azure AD P2

    # Complexity
    complexity_multiplier={"low": 0.8, "medium": 1.0, "high": 1.5},

    # Timeline
    typical_months=4,

    # Source
    source="internal_default",
    notes="Based on 10+ carveout engagements, Azure AD P2 list pricing"
)
```

**The 8 models:**

| # | Model | Covers |
|---|-------|--------|
| 1 | Identity Separation | AD/Azure AD standup, migration |
| 2 | Email Migration | M365 tenant, mailbox migration |
| 3 | WAN Separation | SD-WAN/MPLS cutover, new circuits |
| 4 | Endpoint/EDR | Device migration, security agent rollout |
| 5 | Security Ops Standup | SIEM, SOC, vuln management |
| 6 | ERP Standalone | Generic ERP instance standup (not SAP vs Oracle variants) |
| 7 | DC/Hosting Exit | Server migration, cloud standup |
| 8 | PMO/Transition | Program management, change management |

### Deliverable 3: Model-Ready Exports

**Three CSVs that drop into deal model:**

`deal_costs.csv`:
```csv
tower,work_item,one_time_upside,one_time_base,one_time_stress,run_rate_delta,source
Identity,Identity Separation,102200,127750,178850,91800,calculated
Infrastructure,DC Exit,176000,220000,308000,180000,calculated
...
```

`drivers.csv`:
```csv
driver,value,source_type,source_id,confidence,overridden
total_users,850,extracted,F-ORG-012,high,false
sites,4,extracted,F-INFRA-001,high,false
erp_system,SAP,extracted,F-APP-003,high,false
custom_apps,5,assumed,default,low,false
...
```

`assumptions.csv`:
```csv
assumption,value,impact,source
User count,850,high,F-ORG-012
SAP separation complexity,medium,high,calculated from signals
Azure AD P2 unit price,$108/user/year,medium,internal_default
TSA duration,12 months,high,default assumption
...
```

---

## Revised Hour-by-Hour (MVP Cut)

### Block 1: Drivers (Hours 1-4)

#### Hour 1: Driver Schema + Extractor Core
- [ ] `DealDrivers` dataclass with 15 core fields
- [ ] `extract_drivers_from_facts(fact_store)` function
- [ ] Field mappings (user_count, headcount → total_users, etc.)

#### Hour 2: Source Tracking + Confidence
- [ ] `DriverSource` dataclass (fact_id, confidence, extraction_method)
- [ ] Handle conflicts (multiple facts → pick highest confidence)
- [ ] Flag assumed defaults clearly

#### Hour 3: Ownership Fields (GPT's suggestion)
- [ ] Add `owned_by: target | parent | unknown` to fact extraction
- [ ] Add `shared_with_parent: bool` derivation
- [ ] `get_parent_dependencies(drivers)` → list of shared services

#### Hour 4: Override Persistence
- [ ] `DriverOverride` database model
- [ ] `get_effective_drivers(deal_id)` merges extracted + overrides
- [ ] API: `POST /api/deals/<id>/drivers/override`
- [ ] Stable driver keys for diff detection

**Deliverable:** Driver extraction works, overrides persist, CSV export of drivers.

---

### Block 2: Cost Models (Hours 5-8)

#### Hour 5: Cost Model Schema + Calculator
- [ ] `CostModel` dataclass (base, per_user, per_site, license, complexity, source)
- [ ] `calculate_cost(model, drivers)` → `CostEstimate`
- [ ] Use existing volume discount curves from `cost_model.py`
- [ ] Scenario multipliers (upside=0.85, base=1.0, stress=1.3)

#### Hour 6: Models 1-4 (Identity, Email, WAN, Endpoint)
- [ ] Identity Separation model
- [ ] Email Migration model
- [ ] WAN Separation model
- [ ] Endpoint/EDR model
- [ ] Each with: base cost, per-user, complexity signals, source notes

#### Hour 7: Models 5-8 (Security, ERP, DC, PMO)
- [ ] Security Ops Standup model
- [ ] ERP Standalone model (generic)
- [ ] DC/Hosting Exit model
- [ ] PMO/Transition model

#### Hour 8: Deal-Level Aggregation
- [ ] `calculate_deal_costs(deal_id)` → aggregates all applicable work items
- [ ] Tower grouping (Identity, Apps, Infra, Network, Security, EUC, PMO)
- [ ] Three scenarios with totals
- [ ] Assumptions list extraction
- [ ] **CSV export: deal_costs.csv, assumptions.csv**

**Deliverable:** 8 cost models produce scenarios, deal-level totals, exportable CSVs.

---

### Block 3: Minimal UI (Hours 9-11)

#### Hour 9: Driver View Page
- [ ] Route: `/deals/<id>/drivers`
- [ ] Simple table: driver | value | source | confidence | override button
- [ ] Inline edit → saves to DriverOverride
- [ ] Visual: extracted (default) vs overridden (amber) vs assumed (red)
- [ ] Download drivers.csv button

#### Hour 10: Cost Summary Page (Read-Only)
- [ ] Route: `/deals/<id>/costs` (enhance existing)
- [ ] Tower totals table with upside/base/stress columns
- [ ] Assumptions panel (top 10)
- [ ] "To tighten estimate" list (missing/assumed drivers)
- [ ] Download deal_costs.csv + assumptions.csv buttons

#### Hour 11: Integration with Existing Cost Center
- [ ] Wire new calculator into existing `/costs/` blueprint
- [ ] Replace bucket-based display with scenario-based
- [ ] Keep existing run-rate display (it works)
- [ ] Add "Export for Deal Model" button

**Deliverable:** Two working pages — drivers (editable) and costs (read-only with export).

---

### Block 4: PE Report + Polish (Hours 12-15)

#### Hour 12: PE Report Integration
- [ ] Update cost section in domain reports to use new calculator
- [ ] Show base scenario with upside/stress in parentheses
- [ ] Add assumptions footnote section
- [ ] Driver sources in "Facts Cited"

#### Hour 13: Deal Type Awareness
- [ ] Deal type field in Deal model (if not already)
- [ ] Carveout → show "Parent Dependencies" section
- [ ] Acquisition → show "Integration Considerations"
- [ ] Standalone → show "Standalone Readiness"
- [ ] Route cost models based on deal type

#### Hour 14: Rerun Stability
- [ ] Stable work item keys (type + domain + target)
- [ ] On rerun: detect added/removed/changed
- [ ] Preserve driver overrides across reruns
- [ ] Show diff summary: "3 new work items, 1 removed, 2 changed"

#### Hour 15: End-to-End Test + Demo Prep
- [ ] Test: create deal → run analysis → view drivers → override → view costs → export CSVs
- [ ] Fix bugs
- [ ] Prepare demo script
- [ ] Document what's MVP vs Phase 2

**Deliverable:** PE reports use new costs, deal type routing works, demo-ready.

---

## Phase 2 (Next Weekend)

- TSA View UI with editable durations
- TSA duration sensitivity slider
- Work item override UI (adjust individual estimates)
- Additional cost model variants (SAP vs Oracle vs NetSuite)
- Parent entity as full data model
- Cost vs budget comparison
- Benchmark database across deals

---

## Success = Monday Demo

**Demo script:**

1. "Here's a deal we analyzed — 347 facts extracted"
2. "The system found these drivers" → show driver page
3. "User count was extracted as 850, but we know it's 1,200" → override
4. "Costs recalculate automatically" → show cost page with new numbers
5. "Here are three scenarios for IC" → upside/base/stress
6. "Here are the top assumptions driving these numbers" → assumptions panel
7. "Export for deal model" → download CSVs
8. "Every number traces back to facts or explicit assumptions" → show sources

If we can do that demo, we win.

---

## File Checklist

**Create:**
```
services/cost_engine/
  __init__.py
  drivers.py           # DealDrivers, DriverSource, extract_drivers_from_facts
  models.py            # CostModel definitions (8 models)
  calculator.py        # calculate_cost, calculate_deal_costs
  exports.py           # generate_cost_csv, generate_drivers_csv, generate_assumptions_csv

web/templates/costs/
  drivers.html         # Driver view/edit page
```

**Modify:**
```
web/database.py                  # Add DriverOverride model
web/blueprints/costs.py          # Add driver route, enhance cost summary
web/templates/costs/center.html  # Add scenario display, export buttons
web/blueprints/pe_reports.py     # Use new calculator
```

---

## Go/No-Go Checklist (Before Starting)

- [ ] Understand existing `COST_ANCHORS` structure in `cost_model.py`
- [ ] Understand existing `VOLUME_DISCOUNT_CURVES`
- [ ] Understand existing cost UI in `web/blueprints/costs.py`
- [ ] Confirm FactStore has the fields we need to extract (user_count, etc.)
- [ ] Confirm database migration path for DriverOverride

Ready to start Hour 1?
