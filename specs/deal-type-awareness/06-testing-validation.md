# Spec 06: Testing & Validation

**Status**: GREENFIELD
**Priority**: P0
**Estimated Effort**: 3 hours
**Dependencies**: Specs 01-05 (All prior specs)

---

## Problem Statement

Deal type awareness touches **7+ subsystems** (synergy engine, cost calculator, reasoning prompts, UI validation, database, API, narrative synthesis). Without comprehensive testing:

1. **Regression risk**: Changes break existing acquisition flow
2. **Cross-contamination**: Carve-out logic leaks into acquisition deals
3. **Silent failures**: Wrong recommendations with no error messages
4. **Integration gaps**: Individual components work but full pipeline fails

**Requirement**: Build a test suite that validates ALL 3 deal types × ALL 6 domains × ALL critical paths.

---

## Test Strategy

### Test Pyramid

```
                    ┌─────────────────────┐
                    │  E2E Integration    │  ← 5 tests (golden path per deal type)
                    │  (Full Pipeline)    │
                    └─────────────────────┘
                  ┌───────────────────────────┐
                  │   Integration Tests       │  ← 15 tests (subsystem integration)
                  │   (Bridge + Engine)       │
                  └───────────────────────────┘
              ┌─────────────────────────────────────┐
              │        Unit Tests                   │  ← 50 tests (individual functions)
              │  (Functions, Validators, Logic)     │
              └─────────────────────────────────────┘
```

**Total**: ~70 new tests across 3 levels

---

## Test Files Structure

```
tests/
├── unit/
│   ├── test_deal_type_validation.py          # NEW: UI/API validation
│   ├── test_synergy_engine_branching.py      # NEW: Synergy engine logic
│   ├── test_cost_multipliers.py              # NEW: Cost engine multipliers
│   └── test_prompt_conditioning.py           # NEW: Prompt injection
├── integration/
│   ├── test_deal_type_cost_flow.py           # NEW: Deal type → cost calculation
│   ├── test_deal_type_reasoning_flow.py      # NEW: Deal type → reasoning → findings
│   └── test_deal_type_entity_scoping.py      # NEW: Entity + deal type interaction
└── e2e/
    └── test_full_pipeline_by_deal_type.py    # NEW: Full discovery → narrative by type
```

---

## Unit Tests

### 1. Deal Type Validation Tests

**File**: `tests/unit/test_deal_type_validation.py` (NEW)

```python
"""
Unit tests for deal type validation logic.

Tests validation at multiple layers:
- Database constraints
- Flask form validation
- API schema validation
"""

import pytest
from web.database import Deal, db
from web.api.deals import DealSchema
from marshmallow import ValidationError

class TestDatabaseConstraints:
    """Test database-level deal type constraints."""

    def test_deal_type_not_null(self, db_session):
        """Test that deal_type cannot be NULL."""
        with pytest.raises(Exception) as exc:
            deal = Deal(name="Test", target_name="Target", deal_type=None)
            db_session.add(deal)
            db_session.commit()

        assert "NOT NULL" in str(exc.value) or "violates not-null" in str(exc.value)

    def test_deal_type_invalid_value(self, db_session):
        """Test that invalid deal_type values are rejected."""
        with pytest.raises(Exception) as exc:
            deal = Deal(name="Test", target_name="Target", deal_type="merger")
            db_session.add(deal)
            db_session.commit()

        assert "CHECK constraint" in str(exc.value) or "valid_deal_type" in str(exc.value)

    def test_deal_type_valid_values(self, db_session):
        """Test that all 3 valid deal types are accepted."""
        for deal_type in ['acquisition', 'carveout', 'divestiture']:
            deal = Deal(
                name=f"Test {deal_type}",
                target_name="Target",
                deal_type=deal_type
            )
            db_session.add(deal)
            db_session.commit()

            assert deal.id is not None
            assert deal.deal_type == deal_type

class TestAPISchemaValidation:
    """Test API schema validation for deal creation."""

    def test_schema_requires_deal_type(self):
        """Test that DealSchema requires deal_type."""
        schema = DealSchema()

        with pytest.raises(ValidationError) as exc:
            schema.load({
                'name': 'Test Deal',
                'target_name': 'Target',
                'buyer_name': 'Buyer'
                # deal_type missing
            })

        assert 'deal_type' in exc.value.messages
        assert 'required' in str(exc.value.messages['deal_type']).lower()

    def test_schema_rejects_invalid_deal_type(self):
        """Test that DealSchema rejects invalid deal_type values."""
        schema = DealSchema()

        with pytest.raises(ValidationError) as exc:
            schema.load({
                'name': 'Test Deal',
                'target_name': 'Target',
                'buyer_name': 'Buyer',
                'deal_type': 'merger'  # Invalid
            })

        assert 'deal_type' in exc.value.messages

    def test_schema_accepts_valid_deal_types(self):
        """Test that DealSchema accepts all 3 valid types."""
        schema = DealSchema()

        for deal_type in ['acquisition', 'carveout', 'divestiture']:
            data = schema.load({
                'name': 'Test Deal',
                'target_name': 'Target',
                'buyer_name': 'Buyer',
                'deal_type': deal_type
            })

            assert data['deal_type'] == deal_type
```

---

### 2. Synergy Engine Branching Tests

**File**: `tests/unit/test_synergy_engine_branching.py` (NEW)

```python
"""
Unit tests for synergy engine conditional logic.

Tests the branching behavior:
- Acquisition → consolidation synergies
- Carve-out → separation costs
- Divestiture → separation costs (higher)
"""

import pytest
from web.blueprints.costs import _identify_synergies, _calculate_separation_costs
from stores.inventory_store import InventoryStore

class TestSynergyEngineBranching:
    """Test synergy engine conditional logic by deal type."""

    def test_acquisition_returns_consolidation_synergies(self):
        """Test that acquisition deal type returns consolidation opportunities."""
        inv_store = InventoryStore(deal_id="test")

        # Add overlapping buyer + target apps
        inv_store.add_item(domain='applications', item={'name': 'Salesforce', 'entity': 'buyer'})
        inv_store.add_item(domain='applications', item={'name': 'Salesforce', 'entity': 'target'})

        synergies = _identify_synergies(inv_store, deal_type='acquisition')

        assert len(synergies) > 0
        assert synergies[0].type == 'consolidation'
        assert 'decommission target' in synergies[0].description.lower()

    def test_carveout_returns_separation_costs(self):
        """Test that carve-out deal type returns separation costs."""
        inv_store = InventoryStore(deal_id="test")

        # Add shared services (parent-hosted)
        inv_store.add_item(domain='applications', item={
            'name': 'SAP ERP',
            'entity': 'target',
            'hosting': 'parent_datacenter'
        })

        separation_costs = _identify_synergies(inv_store, deal_type='carveout')

        assert len(separation_costs) > 0
        assert separation_costs[0].type == 'separation_cost'
        assert 'standalone' in separation_costs[0].description.lower()

    def test_divestiture_higher_costs_than_carveout(self):
        """Test that divestiture has higher costs than carveout."""
        inv_store = InventoryStore(deal_id="test")

        inv_store.add_item(domain='applications', item={
            'name': 'Shared CRM',
            'entity': 'target',
            'integration_level': 'deeply_integrated'
        })

        carveout_costs = _calculate_separation_costs(inv_store, deal_type='carveout')
        divestiture_costs = _calculate_separation_costs(inv_store, deal_type='divestiture')

        # Divestiture should have higher costs due to deeper entanglement
        assert sum(c.estimated_cost for c in divestiture_costs) > \
               sum(c.estimated_cost for c in carveout_costs)

    def test_no_consolidation_synergies_for_carveout(self):
        """Test that carve-out does NOT return consolidation synergies."""
        inv_store = InventoryStore(deal_id="test")

        # Add overlapping apps (same scenario as acquisition test)
        inv_store.add_item(domain='applications', item={'name': 'Salesforce', 'entity': 'buyer'})
        inv_store.add_item(domain='applications', item={'name': 'Salesforce', 'entity': 'target'})

        synergies = _identify_synergies(inv_store, deal_type='carveout')

        # Should return separation costs, NOT consolidation synergies
        consolidation_synergies = [s for s in synergies if s.type == 'consolidation']
        assert len(consolidation_synergies) == 0
```

---

### 3. Cost Multiplier Tests

**File**: `tests/unit/test_cost_multipliers.py` (NEW)

```python
"""
Unit tests for deal type cost multipliers.

Tests that cost multipliers are applied correctly:
- Acquisition = 1.0x baseline
- Carve-out = 1.5-3.0x
- Divestiture = 2.0-3.5x
"""

import pytest
from services.cost_engine.models import get_deal_type_multiplier, DEAL_TYPE_MULTIPLIERS
from services.cost_engine.calculator import calculate_costs
from models.work_item import WorkItem

class TestDealTypeMultipliers:
    """Test cost multiplier logic."""

    def test_acquisition_baseline_multipliers(self):
        """Test that acquisition uses 1.0 multipliers (baseline)."""
        for category in ['identity', 'application', 'infrastructure']:
            multiplier = get_deal_type_multiplier('acquisition', category)
            assert multiplier == 1.0

    def test_carveout_higher_than_acquisition(self):
        """Test that carve-out multipliers are higher than acquisition."""
        for category in ['identity', 'application', 'infrastructure']:
            acq_mult = get_deal_type_multiplier('acquisition', category)
            carve_mult = get_deal_type_multiplier('carveout', category)

            assert carve_mult > acq_mult
            assert carve_mult >= 1.5  # At least 1.5x

    def test_divestiture_highest_multipliers(self):
        """Test that divestiture has highest multipliers."""
        for category in ['identity', 'application', 'infrastructure']:
            acq_mult = get_deal_type_multiplier('acquisition', category)
            carve_mult = get_deal_type_multiplier('carveout', category)
            div_mult = get_deal_type_multiplier('divestiture', category)

            assert div_mult >= carve_mult >= acq_mult

    def test_invalid_deal_type_raises_error(self):
        """Test that invalid deal type raises ValueError."""
        with pytest.raises(ValueError) as exc:
            get_deal_type_multiplier('merger', 'identity')

        assert 'Invalid deal_type' in str(exc.value)

    def test_cost_calculation_applies_multipliers(self):
        """Test that calculate_costs applies multipliers correctly."""
        work_items = [
            WorkItem(
                id="WI-001",
                domain="identity",
                title="IAM Separation",
                effort_estimate="high"
            )
        ]

        inv_store = InventoryStore(deal_id="test")

        # Calculate for acquisition
        acq_cost = calculate_costs(work_items, inv_store, deal_type='acquisition')

        # Calculate for carve-out
        carve_cost = calculate_costs(work_items, inv_store, deal_type='carveout')

        # Carve-out should be 2.5x more expensive (identity multiplier)
        assert carve_cost.total_cost / acq_cost.total_cost >= 2.0
```

---

### 4. Prompt Conditioning Tests

**File**: `tests/unit/test_prompt_conditioning.py` (NEW)

```python
"""
Unit tests for deal type prompt conditioning.

Tests that prompts are correctly conditioned based on deal type:
- Acquisition → consolidation focus
- Carve-out → separation focus
- Divestiture → extraction focus
"""

import pytest
from prompts.v2_applications_reasoning_prompt import build_applications_reasoning_prompt

class TestPromptConditioning:
    """Test prompt conditioning logic."""

    def test_acquisition_prompt_mentions_consolidation(self):
        """Test that acquisition prompts emphasize consolidation."""
        prompt = build_applications_reasoning_prompt(
            facts=[],
            deal_context={'deal_type': 'acquisition'}
        )

        assert 'consolidation' in prompt.lower()
        assert 'synergy' in prompt.lower()
        assert 'DO NOT recommend consolidation' not in prompt  # Should NOT have carve-out override

    def test_carveout_prompt_blocks_consolidation(self):
        """Test that carve-out prompts block consolidation recommendations."""
        prompt = build_applications_reasoning_prompt(
            facts=[],
            deal_context={'deal_type': 'carveout'}
        )

        assert 'DO NOT recommend consolidation' in prompt
        assert 'separation' in prompt.lower()
        assert 'TSA' in prompt  # Transition Service Agreement

    def test_divestiture_prompt_emphasizes_extraction(self):
        """Test that divestiture prompts emphasize extraction."""
        prompt = build_applications_reasoning_prompt(
            facts=[],
            deal_context={'deal_type': 'divestiture'}
        )

        assert 'extraction' in prompt.lower() or 'untangle' in prompt.lower()
        assert 'DO NOT recommend consolidation' in prompt

    def test_prompt_includes_deal_type_at_top(self):
        """Test that deal type conditioning appears at TOP of prompt."""
        prompt = build_applications_reasoning_prompt(
            facts=[],
            deal_context={'deal_type': 'carveout'}
        )

        # Conditioning should appear in first 500 characters for salience
        assert 'CARVE-OUT' in prompt[:500]
```

---

## Integration Tests

### 5. Deal Type → Cost Calculation Flow

**File**: `tests/integration/test_deal_type_cost_flow.py` (NEW)

```python
"""
Integration tests for deal type → cost calculation flow.

Tests the full path: Deal model → analysis_runner → cost_engine → result
"""

import pytest
from web.database import Deal, db
from web.analysis_runner import run_reasoning_phase
from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore

class TestDealTypeCostFlow:
    """Test deal type propagation through cost calculation pipeline."""

    def test_acquisition_cost_flow(self, db_session):
        """Test that acquisition deal type flows through to cost calculation."""
        # Create acquisition deal
        deal = Deal(
            name="Acquisition Test",
            target_name="Target",
            buyer_name="Buyer",
            deal_type="acquisition"
        )
        db_session.add(deal)
        db_session.commit()

        # Run analysis
        fact_store = FactStore(deal_id=deal.id)
        inv_store = InventoryStore(deal_id=deal.id)

        # Add sample facts/inventory
        # ... (omitted for brevity)

        # Run reasoning phase (includes cost calculation)
        result = run_reasoning_phase(
            deal_id=deal.id,
            fact_store=fact_store,
            inventory_store=inv_store
        )

        # Verify cost estimate reflects acquisition logic
        assert result['cost_estimate']['deal_type'] == 'acquisition'
        assert result['cost_estimate']['tsa_costs'] == 0  # No TSA for acquisition

    def test_carveout_cost_flow(self, db_session):
        """Test that carve-out deal type flows through to cost calculation."""
        deal = Deal(
            name="Carve-Out Test",
            target_name="Target",
            buyer_name="Buyer",
            deal_type="carveout"
        )
        db_session.add(deal)
        db_session.commit()

        fact_store = FactStore(deal_id=deal.id)
        inv_store = InventoryStore(deal_id=deal.id)

        result = run_reasoning_phase(
            deal_id=deal.id,
            fact_store=fact_store,
            inventory_store=inv_store
        )

        # Verify cost estimate reflects carve-out logic
        assert result['cost_estimate']['deal_type'] == 'carveout'
        assert result['cost_estimate']['tsa_costs'] > 0  # TSA costs present
        assert result['cost_estimate']['total_cost'] > 0  # Higher costs

    def test_cost_multiplier_applied_in_pipeline(self, db_session):
        """Test that cost multipliers are applied in full pipeline."""
        # Same work items, different deal types → different costs
        acq_deal = Deal(name="Acq", target_name="T", deal_type="acquisition")
        carve_deal = Deal(name="Carve", target_name="T", deal_type="carveout")

        db_session.add_all([acq_deal, carve_deal])
        db_session.commit()

        # Run identical analysis for both
        acq_result = run_reasoning_phase(deal_id=acq_deal.id, ...)
        carve_result = run_reasoning_phase(deal_id=carve_deal.id, ...)

        # Carve-out should cost more
        assert carve_result['cost_estimate']['total_cost'] > \
               acq_result['cost_estimate']['total_cost']
```

---

### 6. Deal Type → Reasoning → Findings Flow

**File**: `tests/integration/test_deal_type_reasoning_flow.py` (NEW)

```python
"""
Integration tests for deal type → reasoning → findings flow.

Tests that deal type conditioning reaches reasoning agents and affects findings.
"""

import pytest
from agents_v2.reasoning.applications_reasoning_agent import ApplicationsReasoningAgent
from stores.fact_store import FactStore

class TestDealTypeReasoningFlow:
    """Test deal type affects reasoning agent outputs."""

    def test_acquisition_generates_consolidation_findings(self):
        """Test that acquisition generates consolidation-focused findings."""
        fact_store = FactStore(deal_id="test")

        # Add facts about overlapping applications
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce CRM",
            details={'usage': 'high'},
            entity="buyer"
        )
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce CRM",
            details={'usage': 'high'},
            entity="target"
        )

        agent = ApplicationsReasoningAgent(deal_type='acquisition')
        findings = agent.analyze(fact_store)

        # Should recommend consolidation
        consolidation_findings = [f for f in findings if 'consolidat' in f.description.lower()]
        assert len(consolidation_findings) > 0

    def test_carveout_does_not_generate_consolidation_findings(self):
        """Test that carve-out does NOT generate consolidation findings."""
        fact_store = FactStore(deal_id="test")

        # Same overlapping apps as acquisition test
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce CRM",
            details={'usage': 'high'},
            entity="buyer"
        )
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce CRM",
            details={'usage': 'high'},
            entity="target"
        )

        agent = ApplicationsReasoningAgent(deal_type='carveout')
        findings = agent.analyze(fact_store)

        # Should NOT recommend consolidation
        consolidation_findings = [f for f in findings if 'consolidat' in f.description.lower()]
        assert len(consolidation_findings) == 0

        # Should focus on separation
        separation_findings = [f for f in findings if 'separat' in f.description.lower() or 'standalone' in f.description.lower()]
        assert len(separation_findings) > 0
```

---

## End-to-End Tests

### 7. Full Pipeline by Deal Type

**File**: `tests/e2e/test_full_pipeline_by_deal_type.py` (NEW)

```python
"""
End-to-end tests for full pipeline by deal type.

Tests the complete flow:
Document upload → Discovery → Reasoning → Cost → Narrative
for all 3 deal types.
"""

import pytest
from main_v2 import run_full_pipeline
from web.database import Deal, db

class TestFullPipelineByDealType:
    """E2E tests for full pipeline with different deal types."""

    @pytest.mark.slow
    def test_acquisition_full_pipeline(self, sample_documents):
        """Test full pipeline for acquisition deal."""
        deal = Deal(
            name="Acquisition E2E",
            target_name="Target Co",
            buyer_name="Buyer Co",
            deal_type="acquisition"
        )
        db.session.add(deal)
        db.session.commit()

        # Run full pipeline
        result = run_full_pipeline(
            deal_id=deal.id,
            documents=sample_documents,
            all_domains=True,
            narrative=True
        )

        # Verify acquisition-specific outputs
        assert result['status'] == 'success'
        assert 'consolidation' in result['narrative'].lower()
        assert result['cost_estimate']['tsa_costs'] == 0

    @pytest.mark.slow
    def test_carveout_full_pipeline(self, sample_documents):
        """Test full pipeline for carve-out deal."""
        deal = Deal(
            name="Carve-Out E2E",
            target_name="Target Co",
            buyer_name="NewCo",
            deal_type="carveout"
        )
        db.session.add(deal)
        db.session.commit()

        result = run_full_pipeline(
            deal_id=deal.id,
            documents=sample_documents,
            all_domains=True,
            narrative=True
        )

        # Verify carve-out-specific outputs
        assert result['status'] == 'success'
        assert 'separation' in result['narrative'].lower()
        assert 'standalone' in result['narrative'].lower()
        assert result['cost_estimate']['tsa_costs'] > 0

    @pytest.mark.slow
    def test_divestiture_full_pipeline(self, sample_documents):
        """Test full pipeline for divestiture deal."""
        deal = Deal(
            name="Divestiture E2E",
            target_name="Divested Unit",
            buyer_name="Acquirer",
            deal_type="divestiture"
        )
        db.session.add(deal)
        db.session.commit()

        result = run_full_pipeline(
            deal_id=deal.id,
            documents=sample_documents,
            all_domains=True,
            narrative=True
        )

        # Verify divestiture-specific outputs
        assert result['status'] == 'success'
        assert result['cost_estimate']['total_cost'] > 0  # Highest costs
```

---

## Golden Test Fixtures

Create golden test fixtures for each deal type to enable regression testing.

**File**: `tests/fixtures/golden_acquisition.json` (NEW)

```json
{
  "deal_type": "acquisition",
  "expected_outputs": {
    "synergy_count": 5,
    "synergy_types": ["consolidation", "license_optimization"],
    "tsa_costs": 0,
    "cost_multiplier_identity": 1.0,
    "findings_contain": ["consolidate", "migrate", "decommission"],
    "findings_not_contain": ["separate", "standalone", "TSA"]
  }
}
```

**File**: `tests/fixtures/golden_carveout.json` (NEW)

```json
{
  "deal_type": "carveout",
  "expected_outputs": {
    "synergy_count": 0,
    "separation_cost_count": 8,
    "tsa_costs_min": 50000,
    "cost_multiplier_identity": 2.5,
    "findings_contain": ["separate", "standalone", "TSA", "build"],
    "findings_not_contain": ["consolidate", "decommission target"]
  }
}
```

---

## Regression Tests

**File**: `tests/regression/test_deal_type_regression.py` (NEW)

```python
"""
Regression tests to ensure deal type changes don't break existing behavior.
"""

import pytest
import json

class TestDealTypeRegression:
    """Regression tests using golden fixtures."""

    @pytest.mark.parametrize("golden_file", [
        "tests/fixtures/golden_acquisition.json",
        "tests/fixtures/golden_carveout.json",
        "tests/fixtures/golden_divestiture.json"
    ])
    def test_golden_outputs(self, golden_file):
        """Test that outputs match golden fixtures."""
        with open(golden_file) as f:
            golden = json.load(f)

        deal_type = golden['deal_type']
        expected = golden['expected_outputs']

        # Run pipeline
        result = run_full_pipeline(deal_type=deal_type, ...)

        # Validate against golden expectations
        if 'synergy_count' in expected:
            assert len(result['synergies']) == expected['synergy_count']

        if 'tsa_costs' in expected:
            assert result['cost_estimate']['tsa_costs'] == expected['tsa_costs']

        if 'findings_contain' in expected:
            narrative = result['narrative'].lower()
            for term in expected['findings_contain']:
                assert term in narrative

        if 'findings_not_contain' in expected:
            narrative = result['narrative'].lower()
            for term in expected['findings_not_contain']:
                assert term not in narrative
```

---

## Test Coverage Targets

| Subsystem | Target Coverage | Current Coverage | Gap |
|-----------|----------------|------------------|-----|
| Deal validation | 100% | 0% | 100% |
| Synergy engine | 90% | 45% | 45% |
| Cost calculator | 90% | 60% | 30% |
| Reasoning agents | 85% | 70% | 15% |
| Prompt builders | 80% | 40% | 40% |
| UI routes | 75% | 50% | 25% |
| **Overall** | **85%** | **55%** | **30%** |

---

## Test Execution Plan

### Phase 1: Unit Tests (Day 1)
1. Run `pytest tests/unit/test_deal_type_validation.py -v`
2. Run `pytest tests/unit/test_synergy_engine_branching.py -v`
3. Run `pytest tests/unit/test_cost_multipliers.py -v`
4. Run `pytest tests/unit/test_prompt_conditioning.py -v`
5. Target: 50 unit tests passing

### Phase 2: Integration Tests (Day 2)
1. Run `pytest tests/integration/test_deal_type_cost_flow.py -v`
2. Run `pytest tests/integration/test_deal_type_reasoning_flow.py -v`
3. Run `pytest tests/integration/test_deal_type_entity_scoping.py -v`
4. Target: 15 integration tests passing

### Phase 3: E2E Tests (Day 3)
1. Run `pytest tests/e2e/test_full_pipeline_by_deal_type.py -v --slow`
2. Generate golden fixtures from successful runs
3. Run regression tests against golden fixtures
4. Target: 5 E2E tests passing

---

## Success Criteria

- [ ] 70+ new tests added across unit/integration/e2e levels
- [ ] All 3 deal types covered: acquisition, carveout, divestiture
- [ ] Golden test fixtures created for regression prevention
- [ ] Test coverage increased from 55% → 85% for affected subsystems
- [ ] All tests pass in CI/CD pipeline
- [ ] No regressions in existing acquisition flow (backward compatibility validated)
- [ ] Tests validate BOTH positive cases (correct outputs) and negative cases (wrong recommendations prevented)

---

## Files Created

| File | Lines | Type |
|------|-------|------|
| `tests/unit/test_deal_type_validation.py` | 120 | New |
| `tests/unit/test_synergy_engine_branching.py` | 150 | New |
| `tests/unit/test_cost_multipliers.py` | 130 | New |
| `tests/unit/test_prompt_conditioning.py` | 100 | New |
| `tests/integration/test_deal_type_cost_flow.py` | 180 | New |
| `tests/integration/test_deal_type_reasoning_flow.py` | 140 | New |
| `tests/e2e/test_full_pipeline_by_deal_type.py` | 200 | New |
| `tests/regression/test_deal_type_regression.py` | 80 | New |
| `tests/fixtures/golden_acquisition.json` | 20 | New |
| `tests/fixtures/golden_carveout.json` | 20 | New |
| `tests/fixtures/golden_divestiture.json` | 20 | New |

**Total**: ~1,160 lines of test code

---

## Dependencies

**Depends On**:
- Spec 01: Deal Type Architecture (taxonomy)
- Spec 02: Synergy Engine Conditional Logic (branching to test)
- Spec 03: Reasoning Prompt Conditioning (prompts to test)
- Spec 04: Cost Engine Deal Awareness (multipliers to test)
- Spec 05: UI Validation Enforcement (validation to test)

**Blocks**:
- Spec 07: Migration & Rollout (migration requires passing tests)

---

## Estimated Effort

- **Unit test development**: 1.5 hours
- **Integration test development**: 1.0 hours
- **E2E test development**: 0.5 hours
- **Golden fixtures + regression tests**: 0.5 hours
- **Test debugging + coverage analysis**: 0.5 hours
- **Total**: 3.0 hours

---

**Next Steps**: Proceed to Spec 07 (Migration & Rollout) to define backward compatibility strategy and deployment plan.
