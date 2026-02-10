# Weekend Execution Plan: 15 Hours to Production-Ready

## What We're Building

Three interconnected capabilities that transform this from "demo tool" to "deal tool":

1. **Driver-Based Cost Engine** — Replace LLM bucket-picking with deterministic calculations
2. **TSA/Entanglement Module** — First-class parent entity + TSA economics view
3. **Interactive Data Layer** — Editable drivers, facts, and work items with persistence

These share a common foundation: **the FactStore feeds drivers, drivers feed calculations, calculations are editable, edits persist and flow through to reports.**

---

## Hour-by-Hour Execution Plan

### Block 1: Foundation (Hours 1-3)

**Goal**: Data models + driver extraction infrastructure

#### Hour 1: Core Data Models
- [ ] `DealDrivers` dataclass with all driver fields (users, sites, apps, etc.)
- [ ] `DriverOverride` database model (deal_id, driver_name, original, override, source)
- [ ] `FactCorrection` database model
- [ ] `WorkItemAdjustment` database model
- [ ] Add relationships to Deal model
- [ ] Migration script

**Files to create/modify:**
- `services/cost_engine/models.py` (new)
- `web/database.py` (add models)

#### Hour 2: Driver Extractor
- [ ] `DriverExtractor` class that walks FactStore and pulls driver values
- [ ] Mapping from fact fields to driver names (e.g., `details.user_count` → `total_users`)
- [ ] Source tracking (which fact ID provided which driver)
- [ ] Handle missing drivers gracefully (None, not error)

**Files to create:**
- `services/cost_engine/driver_extractor.py`

#### Hour 3: Driver Override Integration
- [ ] `get_effective_drivers(deal_id)` function that:
  - Extracts from facts
  - Applies any overrides from database
  - Returns merged DealDrivers with source tracking
- [ ] Unit tests for driver extraction + override merge

**Files to create:**
- `services/cost_engine/driver_service.py`
- `tests/test_driver_extraction.py`

---

### Block 2: Cost Models (Hours 4-6)

**Goal**: 15 work item types with driver-based cost calculations

#### Hour 4: Cost Model Schema + Engine
- [ ] `CostModel` dataclass (license drivers, services base, per-unit costs, complexity multipliers)
- [ ] `LicenseDriver` dataclass
- [ ] `WorkItemCostEstimate` output dataclass
- [ ] `calculate_work_item_cost(work_item_type, drivers, scenario)` function
- [ ] Scenario multipliers (upside=0.8, base=1.0, stress=1.4)

**Files to create:**
- `services/cost_engine/cost_models.py`
- `services/cost_engine/calculator.py`

#### Hour 5: Identity + Infrastructure Cost Models
- [ ] IDENTITY_SEPARATION model (Azure AD, migration, parallel run)
- [ ] MFA_DEPLOYMENT model
- [ ] DC_MIGRATION model
- [ ] CLOUD_MIGRATION model
- [ ] BACKUP_DR_STANDUP model
- [ ] SERVER_MIGRATION model

**Files to modify:**
- `services/cost_engine/cost_models.py` (add models)

#### Hour 6: Applications + Network + Security Cost Models
- [ ] ERP_STANDALONE_INSTANCE model (SAP, Oracle, NetSuite variants)
- [ ] ERP_MIGRATION model
- [ ] APP_RATIONALIZATION model
- [ ] WAN_SEPARATION model
- [ ] VPN_STANDUP model
- [ ] EDR_DEPLOYMENT model
- [ ] SIEM_IMPLEMENTATION model
- [ ] EMAIL_MIGRATION model

**Files to modify:**
- `services/cost_engine/cost_models.py` (add models)

---

### Block 3: TSA Module (Hours 7-9)

**Goal**: Parent entity + TSA economics as first-class features

#### Hour 7: Parent Entity Support
- [ ] Add `parent` to allowed entity values throughout codebase
- [ ] Update extraction prompts to distinguish target-owned vs parent-owned
- [ ] `EntanglementAnalyzer` class that:
  - Scans facts for parent references
  - Categorizes by service type (DC, ERP, Identity, Network, Security, Support)
  - Calculates entanglement score per domain

**Files to create/modify:**
- `services/cost_engine/entanglement.py` (new)
- `prompts/` (update extraction prompts)
- `tools_v2/fact_store.py` (entity validation)

#### Hour 8: TSA Service Catalog
- [ ] `TSAService` dataclass (service_type, owner, monthly_cost, duration_months, standalone_alternative)
- [ ] `TSA_SERVICE_DEFAULTS` catalog with typical costs/durations:
  - Data Center Hosting
  - ERP Instance
  - Identity Services
  - Network (WAN/MPLS)
  - Security Operations (SOC)
  - Help Desk / Service Desk
  - Application Support
- [ ] `calculate_tsa_exposure(services, duration_override=None)` function

**Files to create:**
- `services/cost_engine/tsa_catalog.py`

#### Hour 9: TSA View Generator
- [ ] `generate_tsa_view(deal_id)` function that:
  - Loads entanglement analysis
  - Maps to TSA services
  - Calculates TSA exposure (monthly × duration)
  - Calculates standalone alternative costs
  - Produces comparison table
- [ ] TSA sensitivity analysis (12/18/24 month scenarios)
- [ ] Integration with cost engine (TSA as cost component)

**Files to create:**
- `services/cost_engine/tsa_view.py`

---

### Block 4: Interactive UI (Hours 10-12)

**Goal**: Web interface for viewing and editing drivers, costs, TSA

#### Hour 10: Driver Editor UI
- [ ] `/deals/<deal_id>/drivers` route showing all drivers with values + sources
- [ ] Inline edit capability (click to edit, save persists to DriverOverride)
- [ ] Visual distinction: extracted (gray) vs overridden (amber)
- [ ] "Reset to extracted" option for overrides
- [ ] Jinja template with edit JS (similar to report editing we built)

**Files to create:**
- `web/blueprints/cost_engine.py` (new blueprint)
- `web/templates/costs/driver_editor.html`

#### Hour 11: Cost Summary UI
- [ ] `/deals/<deal_id>/costs` route showing:
  - One-time costs by tower (identity, apps, infra, network, security, EUC, PMO)
  - Scenario toggle (upside/base/stress)
  - Drill-down to work items per tower
  - Assumptions list with edit capability
- [ ] Work item cost adjustment UI (override calculated cost with reason)

**Files to create:**
- `web/templates/costs/cost_summary.html`
- `web/templates/costs/work_item_detail.html`

#### Hour 12: TSA View UI
- [ ] `/deals/<deal_id>/tsa` route showing:
  - TSA services table (service, owner, monthly, duration, total)
  - Standalone comparison column
  - Duration sensitivity slider (12/18/24 months)
  - Total TSA exposure summary
  - Editable monthly costs and durations
- [ ] Export to Excel/CSV for deal model import

**Files to create:**
- `web/templates/costs/tsa_view.html`

---

### Block 5: Integration + Polish (Hours 13-15)

**Goal**: Wire everything together, test end-to-end, polish output

#### Hour 13: PE Report Integration
- [ ] Update `pe_reports.py` to use new cost engine instead of old bucket system
- [ ] Costs report pulls from `calculate_deal_costs()` not work item buckets
- [ ] TSA section in executive summary for carveout deals
- [ ] Assumptions list in cost report footer

**Files to modify:**
- `web/blueprints/pe_reports.py`
- `tools_v2/costs_report.py`
- `tools_v2/executive_summary_pe.py`

#### Hour 14: Deal-Type Aware Flow
- [ ] Deal type selection UI (acquisition+integration, acquisition+standalone, carveout)
- [ ] Conditional TSA module (only shows for carveout)
- [ ] Deal-type-specific driver requirements
- [ ] "What's missing" checklist per deal type
- [ ] Store deal_type properly and use it to route analysis

**Files to modify:**
- `web/templates/deals/deal_detail.html`
- `services/cost_engine/driver_service.py`

#### Hour 15: End-to-End Testing + Documentation
- [ ] Test full flow: create deal → run analysis → view drivers → override → view costs → view TSA → export
- [ ] Fix any integration bugs
- [ ] Update `README.md` with new cost engine documentation
- [ ] Create sample deal with realistic data for demo

**Files to create/modify:**
- `tests/test_cost_engine_e2e.py`
- `README.md`

---

## File Structure After Weekend

```
services/
  cost_engine/
    __init__.py
    models.py              # DealDrivers, CostModel, LicenseDriver, estimates
    driver_extractor.py    # Extract drivers from FactStore
    driver_service.py      # Get effective drivers with overrides
    cost_models.py         # 15+ work item type cost models
    calculator.py          # calculate_work_item_cost(), calculate_deal_costs()
    entanglement.py        # Parent entity analysis
    tsa_catalog.py         # TSA service definitions and defaults
    tsa_view.py            # TSA exposure calculations

web/
  blueprints/
    cost_engine.py         # Routes for /drivers, /costs, /tsa
  templates/
    costs/
      driver_editor.html
      cost_summary.html
      work_item_detail.html
      tsa_view.html
```

---

## Success Criteria

By end of weekend, the system can:

1. **Extract drivers** from facts with source tracking
2. **Calculate costs** using driver × unit price × complexity, not LLM buckets
3. **Show three scenarios** (upside/base/stress) with explicit assumptions
4. **Handle parent entities** and calculate TSA exposure
5. **Let users edit** drivers, costs, and TSA parameters with persistence
6. **Produce model-ready output** that can go into a deal financial model
7. **Show "what's missing"** as actionable items for the deal team

---

## Risk Mitigation

**Risk**: Cost models take longer than expected to define
**Mitigation**: Start with 8 core models (identity, ERP, DC, network, security, email, PMO, MSP), add others later

**Risk**: UI work expands
**Mitigation**: Keep UI minimal — tables with inline edit, no fancy components. Function over form.

**Risk**: Integration bugs between new cost engine and existing reports
**Mitigation**: Keep old cost calculation as fallback, feature-flag new engine

**Risk**: Driver extraction doesn't find enough values
**Mitigation**: Sensible defaults + clear "assumed" labeling. Missing data is a feature (tells team what to get).

---

## Let's Go

This plan is aggressive but achievable. Each hour has a concrete deliverable. The blocks are sequenced so each builds on the previous.

Ready to start with Block 1, Hour 1?
