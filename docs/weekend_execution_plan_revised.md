# Weekend Execution Plan (REVISED): 15 Hours

## What We Actually Have

The audit revealed we have **far more** than expected:

| Component | Status | Key Files |
|-----------|--------|-----------|
| Cost anchors & adjustment rules | ✅ 95% | `tools_v2/cost_model.py` (950+ lines) |
| TSA/Entanglement patterns | ✅ 95% | `tools_v2/cost_model.py`, `services/shared_services_analyzer.py` |
| Shared services analyzer | ✅ 100% | `services/shared_services_analyzer.py` (828 lines) |
| Strategic cost assessment | ✅ 95% | `prompts/shared/strategic_cost_assessment.py` (588 lines) |
| Override/correction models | ✅ 90% | `tools_v2/feedback_tracker.py`, `models/validation_models.py` |
| Cost UI skeleton | ✅ 60% | `web/blueprints/costs.py`, `web/templates/costs/` |
| Volume discount curves | ✅ 100% | `tools_v2/cost_model.py` (lines 341-385) |
| Regional multipliers | ✅ 100% | `tools_v2/cost_model.py` (lines 422-459) |

## What's Actually Missing (The Real Work)

1. **Driver Extraction Pipeline** — No code that says "scan facts, extract user_count=850, sites=4"
2. **Driver → Cost Calculation Bridge** — Can't do `cost = anchor × extracted_quantity × discount_curve`
3. **Parent as First-Class Entity** — "parent" is a string in patterns, not a data model
4. **Driver Override UI** — Can override costs, but not the drivers feeding them
5. **Wiring** — The pieces exist but aren't connected into a single flow

## Revised 15-Hour Plan

### Block 1: Driver Extraction (Hours 1-3)

This is the **critical missing piece**. Everything else exists.

#### Hour 1: Driver Extractor Core
- [ ] Create `services/cost_engine/driver_extractor.py`
- [ ] `DealDrivers` dataclass (reuse fields from audit)
- [ ] `extract_drivers_from_facts(fact_store, deal_id)` function
- [ ] Mapping rules: fact field → driver name
  - `f.details.get('user_count')` → `total_users`
  - `f.details.get('headcount')` → `total_users` (alias)
  - `f.details.get('sites')` or `f.details.get('locations')` → `sites`
  - `f.domain == 'applications'` count → `total_apps`
  - etc.

**Leverage existing:**
- `tools_v2/cost_model.py` already has quantity concepts
- `services/shared_services_analyzer.py` extracts some metrics

#### Hour 2: Driver Source Tracking
- [ ] Track which fact provided which driver value
- [ ] Handle conflicts (multiple facts claim different user counts)
- [ ] Confidence scoring (explicit fact vs inferred)
- [ ] `DriverExtractionResult` with values + sources + confidence

#### Hour 3: Driver Override Integration
- [ ] `DriverOverride` model in database (extend existing override patterns)
- [ ] `get_effective_drivers(deal_id)` — merge extracted + overrides
- [ ] API endpoint: `POST /api/drivers/<deal_id>/override`
- [ ] Unit tests

---

### Block 2: Wire Drivers to Cost Model (Hours 4-6)

Connect the new driver extraction to the **existing** cost infrastructure.

#### Hour 4: Cost Calculation with Drivers
- [ ] Create `services/cost_engine/calculator.py`
- [ ] `calculate_cost_with_drivers(cost_anchor, drivers, adjustments)` function
- [ ] Use existing `VOLUME_DISCOUNT_CURVES` from `cost_model.py`
- [ ] Use existing `ADJUSTMENT_RULES` from `cost_model.py`
- [ ] Return structured estimate with breakdown

**Example calculation:**
```python
# Identity separation
base = COST_ANCHORS['separation']['identity']['high']  # $500K
quantity_factor = volume_discount(drivers.total_users, 'per_user')  # 0.7 for 2000 users
complexity = apply_adjustments(drivers, ['industry', 'geographic'])  # 1.2
estimate = base * quantity_factor * complexity  # $500K * 0.7 * 1.2 = $420K
```

#### Hour 5: Scenario Engine
- [ ] `calculate_scenarios(drivers, cost_type)` → upside/base/stress
- [ ] Use existing anchor ranges (low/mid/high already defined)
- [ ] Apply driver uncertainty (±20% on unverified drivers)
- [ ] Output: `{upside: $X, base: $Y, stress: $Z, assumptions: [...]}`

#### Hour 6: Work Item Cost Enrichment
- [ ] Modify work item creation to use driver-based calculation
- [ ] Replace bucket assignment with calculated range
- [ ] Keep evidence chain (work item → drivers used → facts cited)
- [ ] Update `ReasoningStore` to store enriched costs

---

### Block 3: TSA View (Hours 7-9)

**Most of this exists** in `shared_services_analyzer.py`. We're wiring + UI.

#### Hour 7: TSA Data Pipeline
- [ ] Create `services/cost_engine/tsa_service.py`
- [ ] `generate_tsa_view(deal_id)` that calls existing `SharedServicesAnalyzer`
- [ ] Structure output for UI consumption:
  ```python
  {
    "services": [
      {"name": "DC Hosting", "provider": "Parent", "monthly": 45000,
       "duration_months": 18, "total": 810000, "standalone_cost": 320000}
    ],
    "total_tsa_exposure": 3960000,
    "total_standalone_cost": 1400000,
    "duration_scenarios": {12: X, 18: Y, 24: Z}
  }
  ```

#### Hour 8: Parent Entity Formalization
- [ ] Add `parent` to entity enum/validation in `tools_v2/fact_store.py`
- [ ] Update extraction prompts to tag parent-owned items with `entity: parent`
- [ ] `get_parent_dependencies(fact_store)` helper
- [ ] Entanglement score calculation (% of facts referencing parent)

#### Hour 9: TSA Duration Sensitivity
- [ ] TSA scenario calculator (12/18/24 month toggles)
- [ ] Monthly cost × duration matrix
- [ ] Standalone alternative comparison
- [ ] "Break-even" calculation (when does standalone cost less than TSA?)

---

### Block 4: Interactive UI (Hours 10-12)

Build on **existing** `web/blueprints/costs.py` and templates.

#### Hour 10: Driver Editor Page
- [ ] New route: `/costs/drivers` or `/deals/<id>/drivers`
- [ ] Template showing all extracted drivers with:
  - Value
  - Source (fact ID or "assumed")
  - Confidence
  - Override button
- [ ] Inline edit with AJAX save to `DriverOverride`
- [ ] Visual: extracted (gray) vs overridden (amber) vs assumed (red outline)

#### Hour 11: Enhanced Cost Summary
- [ ] Modify existing `/costs/` to show driver-based calculations
- [ ] Add scenario toggle (upside/base/stress)
- [ ] Show calculation breakdown on hover/click
- [ ] "Assumptions" panel showing top 10 drivers
- [ ] "To tighten estimate" list

#### Hour 12: TSA View Page
- [ ] New route: `/costs/tsa` or `/deals/<id>/tsa`
- [ ] TSA services table with editable duration/monthly cost
- [ ] Duration slider (12/18/24 months) with live recalculation
- [ ] Standalone comparison column
- [ ] Export to CSV for deal model

---

### Block 5: Integration + Polish (Hours 13-15)

#### Hour 13: PE Report Integration
- [ ] Update `pe_reports.py` cost section to use new calculator
- [ ] TSA section for carveout deals (conditional)
- [ ] Assumptions footnotes
- [ ] Driver sources in "Facts Cited"

#### Hour 14: Deal Type Routing
- [ ] Deal type selector in UI (acquisition/standalone/carveout)
- [ ] Conditional TSA view (only for carveout)
- [ ] Deal-type-specific driver requirements
- [ ] "What's missing for this deal type" checklist

#### Hour 15: Testing + Documentation
- [ ] End-to-end test: upload docs → extract → view drivers → override → view costs → view TSA
- [ ] Fix integration bugs
- [ ] Update existing cost documentation
- [ ] Demo walkthrough notes

---

## What We're NOT Rebuilding

These exist and work — leave them alone:

- ❌ Don't rebuild cost anchors (use `COST_ANCHORS` in `cost_model.py`)
- ❌ Don't rebuild TSA patterns (use `TSA_EXPOSURE_PATTERNS`)
- ❌ Don't rebuild adjustment rules (use `ADJUSTMENT_RULES`)
- ❌ Don't rebuild shared services logic (use `SharedServicesAnalyzer`)
- ❌ Don't rebuild volume curves (use `VOLUME_DISCOUNT_CURVES`)
- ❌ Don't rebuild override models (extend existing `CostOverride`)
- ❌ Don't rebuild cost UI from scratch (extend existing templates)

---

## Key Files to Create

```
services/cost_engine/
  __init__.py
  driver_extractor.py      # NEW - extract drivers from facts
  calculator.py            # NEW - driver-based cost calculation
  tsa_service.py           # NEW - TSA view generation (wraps SharedServicesAnalyzer)

web/blueprints/
  costs.py                 # MODIFY - add driver routes, enhance summary

web/templates/costs/
  driver_editor.html       # NEW - driver view/edit page
  tsa_view.html            # NEW - TSA economics page
  center.html              # MODIFY - add scenario toggle, assumptions panel
```

---

## Key Files to Modify

```
tools_v2/cost_model.py           # Minor - add driver integration hooks
tools_v2/fact_store.py           # Minor - add 'parent' entity validation
web/database.py                  # Minor - add DriverOverride model
web/blueprints/pe_reports.py     # Moderate - use new cost calculator
prompts/extraction/              # Minor - update to tag parent entities
```

---

## Success Criteria (Same as Before)

By end of weekend:

1. ✅ **Extract drivers** from facts with source tracking
2. ✅ **Calculate costs** using driver × anchor × discount × adjustment
3. ✅ **Show three scenarios** with explicit assumptions
4. ✅ **Handle parent entities** and calculate TSA exposure
5. ✅ **Let users edit** drivers and see costs recalculate
6. ✅ **Produce model-ready output** for deal financials
7. ✅ **Show "what's missing"** as actionable items

---

## Risk Mitigation (Updated)

**Risk**: Driver extraction doesn't find values in facts
**Mitigation**: Facts already have these fields — we're just not reading them. Check `details.user_count`, `details.headcount`, etc.

**Risk**: Existing cost model doesn't integrate cleanly
**Mitigation**: It's well-structured. We're adding a driver layer on top, not replacing.

**Risk**: UI work expands
**Mitigation**: Existing cost UI is 60% there. We're adding 2 pages, not 10.

---

## Hour-by-Hour Checklist

| Hour | Block | Deliverable | Key File |
|------|-------|-------------|----------|
| 1 | Foundation | Driver extractor core | `driver_extractor.py` |
| 2 | Foundation | Source tracking + confidence | `driver_extractor.py` |
| 3 | Foundation | Override integration + API | `driver_extractor.py`, `database.py` |
| 4 | Wiring | Cost calculation with drivers | `calculator.py` |
| 5 | Wiring | Scenario engine | `calculator.py` |
| 6 | Wiring | Work item enrichment | `calculator.py` |
| 7 | TSA | TSA data pipeline | `tsa_service.py` |
| 8 | TSA | Parent entity formalization | `fact_store.py` |
| 9 | TSA | Duration sensitivity | `tsa_service.py` |
| 10 | UI | Driver editor page | `driver_editor.html` |
| 11 | UI | Enhanced cost summary | `center.html` |
| 12 | UI | TSA view page | `tsa_view.html` |
| 13 | Integration | PE report integration | `pe_reports.py` |
| 14 | Integration | Deal type routing | Multiple |
| 15 | Polish | Testing + docs | Tests, docs |

---

## Let's Go

The plan is now **realistic** — we're connecting existing pieces, not building from scratch. The driver extraction layer is the linchpin. Once that's done, everything else clicks into place.

Ready to start Hour 1?
