# Migration & Rollout Plan for Test Validation Framework

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document outlines the phased rollout plan for implementing the test validation framework. Rather than a "big bang" deployment, this spec defines an incremental approach that delivers value early while minimizing disruption.

**Purpose:** Provide a step-by-step migration plan from current state (no validation framework) to fully operational validation system with CI/CD integration.

**Scope:** Migration phases, rollback procedures, success metrics, team coordination, and risk management.

---

## Architecture

### Migration Phases

```
Phase 0: Foundation (Week 1)
  → Create directory structure
  → Write schemas and assertion classes
  → Unit test assertion types

Phase 1: CloudServe Pilot (Week 2)
  → Create CloudServe golden fixture
  → Write CloudServe validation test
  → Manual validation run (baseline)

Phase 2: Great Insurance Expansion (Week 3)
  → Create Great Insurance fixture
  → Validate second deal
  → Refine tolerances based on learnings

Phase 3: Documentation & Templates (Week 4)
  → Write all README templates
  → Document fixture creation process
  → Create METADATA.json schema

Phase 4: CI Integration (Week 5)
  → Implement PR workflow
  → Enable pre-commit hooks
  → Test fixture update workflow

Phase 5: Nightly Regression (Week 6)
  → Implement nightly workflow
  → Set up Slack notifications
  → Establish baseline accuracy metrics

Phase 6: Full Rollout (Week 7+)
  → Backfill remaining deals
  → Enforce validation in CI
  → Quarterly maintenance process
```

---

## Specification

### Phase 0: Foundation (Week 1)

**Goal:** Set up core infrastructure without breaking existing code.

**Tasks:**

1. **Create directory structure**

```bash
cd "9.5/it-diligence-agent 2"

# Create test validation directories
mkdir -p tests/golden
mkdir -p tests/validation
mkdir -p tests/unit/assertions
mkdir -p tests/scripts
mkdir -p tests/reports

# Create spec directories (already done)
mkdir -p specs/test-validation
```

2. **Implement assertion base classes**

**File:** `tests/assertions/base.py`

```python
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class AssertionResult:
    """Result of an assertion check."""
    passed: bool
    expected: Any
    actual: Any
    diff: Any
    message: str

class Assertion:
    """Base class for all assertion types."""

    def assert_match(self, expected: Any, actual: Any) -> AssertionResult:
        """Override in subclasses."""
        raise NotImplementedError
```

3. **Implement core assertion types**

Create files in `tests/assertions/`:
- `count_assertion.py`
- `cost_assertion.py`
- `risk_assertion.py`
- `completeness_assertion.py`

4. **Write unit tests**

**File:** `tests/unit/assertions/test_count_assertion.py`

```python
import pytest
from tests.assertions.count_assertion import CountAssertion

def test_exact_match_passes():
    assertion = CountAssertion(tolerance=0)
    result = assertion.assert_match(expected=38, actual=38)
    assert result.passed

def test_within_tolerance_passes():
    assertion = CountAssertion(tolerance=2)
    result = assertion.assert_match(expected=38, actual=36)
    assert result.passed

def test_outside_tolerance_fails():
    assertion = CountAssertion(tolerance=2)
    result = assertion.assert_match(expected=38, actual=33)
    assert not result.passed
```

5. **Run unit tests**

```bash
pytest tests/unit/assertions/ -v
```

**Success Criteria:**
- All directories created
- 4 assertion types implemented
- 20+ unit tests passing
- No existing tests broken

**Time Estimate:** 2-3 days

---

### Phase 1: CloudServe Pilot (Week 2)

**Goal:** Create first golden fixture and validation test. Prove concept works.

**Tasks:**

1. **Run discovery pipeline on CloudServe**

```bash
cd "9.5/it-diligence-agent 2"
python main_v2.py data/input/ --all --target-name "CloudServe" --narrative
```

2. **Manually verify outputs**

Check `output/deals/{timestamp}_cloudserve/`:
- `inventory_store.json` - Count apps, verify costs
- `facts_{timestamp}.json` - Spot check critical facts
- `findings_{timestamp}.json` - Verify key risks detected
- `reports/it_dd_report_{timestamp}.html` - Human review

3. **Create golden fixture**

**File:** `tests/golden/cloudserve_expected.json`

Follow schema from `02-golden-fixture-schema.md`. Extract validated values from pipeline output.

4. **Validate fixture against schema**

```bash
pip install jsonschema
jsonschema -i tests/golden/cloudserve_expected.json tests/golden/fixture_schema.json
```

5. **Write validation test**

**File:** `tests/validation/test_cloudserve_accuracy.py`

```python
import pytest
import json
from pathlib import Path
from tests.assertions import CountAssertion, CostAssertion, RiskAssertion

@pytest.fixture
def golden_fixture():
    """Load CloudServe golden fixture."""
    fixture_path = Path("tests/golden/cloudserve_expected.json")
    return json.loads(fixture_path.read_text())

@pytest.fixture
def actual_output():
    """Load most recent CloudServe pipeline output."""
    # Find latest cloudserve deal output
    from stores.inventory_store import InventoryStore
    store = InventoryStore()
    store.load_from_session("cloudserve")  # Or latest timestamp
    return store

def test_application_count(golden_fixture, actual_output):
    """Verify application count matches expected."""
    expected_count = golden_fixture["applications"]["count"]
    actual_count = len(actual_output.get_items_by_type("application"))

    assertion = CountAssertion(tolerance=2)
    result = assertion.assert_match(expected_count, actual_count)

    assert result.passed, result.message

def test_total_cost(golden_fixture, actual_output):
    """Verify total cost matches expected."""
    expected_cost = golden_fixture["applications"]["total_cost"]
    actual_cost = sum(app.get("annual_cost", 0) for app in actual_output.get_items_by_type("application"))

    assertion = CostAssertion(tolerance_pct=1.0)
    result = assertion.assert_match(expected_cost, actual_cost)

    assert result.passed, result.message

def test_critical_risks_detected(golden_fixture, actual_output):
    """Verify critical risks are detected."""
    expected_risks = golden_fixture["risks"]["critical"]

    # Load findings
    from stores.finding_store import FindingStore
    findings = FindingStore()
    findings.load_from_session("cloudserve")
    actual_risks = [f.id for f in findings.get_findings_by_severity("CRITICAL")]

    assertion = RiskAssertion(allow_extra=True)
    result = assertion.assert_match(expected_risks, actual_risks)

    assert result.passed, result.message
```

6. **Run validation test**

```bash
pytest tests/validation/test_cloudserve_accuracy.py -v
```

**Success Criteria:**
- CloudServe fixture created and schema-valid
- Validation test written with 10+ assertions
- All assertions pass when run against fresh pipeline output
- Manual review confirms fixture values are accurate

**Time Estimate:** 3-4 days

**Rollback Plan:** If validation fails, this is exploratory - no impact on existing pipeline. Simply iterate on fixture/test until passing.

---

### Phase 2: Great Insurance Expansion (Week 3)

**Goal:** Validate framework works for second deal with different industry/stack.

**Tasks:**

1. **Create Great Insurance fixture**

Follow same process as CloudServe:
- Run pipeline on Great Insurance docs
- Manually verify outputs
- Extract values into `tests/golden/great_insurance_expected.json`
- Validate against schema

2. **Write validation test**

**File:** `tests/validation/test_great_insurance_accuracy.py`

Copy structure from CloudServe test, adapt assertions for Great Insurance characteristics:
- Insurance-specific apps (Duck Creek, Majesco, Guidewire)
- Different cost profile
- Different org structure

3. **Run both validation tests**

```bash
pytest tests/validation/ -v
```

4. **Refine tolerances**

If tests fail due to tight tolerances:
- Analyze failure patterns
- Adjust tolerance values in assertions
- Document rationale in spec

5. **Compare fixtures**

Use helper script to identify differences in structure:

```bash
python tests/scripts/compare_fixtures.py cloudserve great_insurance
```

**Success Criteria:**
- Great Insurance fixture created
- Validation test passes
- Tolerance values refined based on 2 deals
- Pattern differences documented

**Time Estimate:** 3-4 days

**Rollback Plan:** If Great Insurance validation reveals CloudServe fixture was wrong, fix CloudServe fixture (treat as bug fix, not rollback).

---

### Phase 3: Documentation & Templates (Week 4)

**Goal:** Enable others to create fixtures without tribal knowledge.

**Tasks:**

1. **Write CloudServe README**

**File:** `data/input/CLOUDSERVE_README.md`

Follow template from `04-test-data-documentation.md`. Document:
- Source documents (6 files)
- Expected outcomes (38 apps, $2.3M cost)
- Intentional gaps (carve-out dependencies, API integration list)
- Validation mapping to fixture

2. **Write Great Insurance README**

**File:** `data/input/GREAT_INSURANCE_README.md`

Same structure as CloudServe.

3. **Write golden fixture README**

**File:** `tests/golden/README.md`

Complete guide on:
- How to create new fixture
- How to update existing fixture
- Version numbering convention
- Fixture maintenance best practices

4. **Implement METADATA.json generation**

Add code to `main_v2.py` to auto-generate metadata file:

```python
def generate_deal_metadata(deal_path: Path, source_docs: List[Path], outputs: Dict[str, Path]):
    """Generate METADATA.json for a deal output."""
    metadata = {
        "$schema": "deal-metadata-v1.0",
        "deal_id": deal_path.name,
        "created_at": datetime.now().isoformat(),
        "source_documents": [
            {
                "filename": doc.name,
                "path": str(doc),
                "md5_hash": hashlib.md5(doc.read_bytes()).hexdigest(),
                "size_bytes": doc.stat().st_size
            }
            for doc in source_docs
        ],
        "outputs": {k: str(v) for k, v in outputs.items()},
        "golden_fixture": f"tests/golden/{deal_name}_expected.json",
        "validation_test": f"tests/validation/test_{deal_name}_accuracy.py"
    }

    metadata_path = deal_path / "METADATA.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
```

5. **Test metadata generation**

```bash
python main_v2.py data/input/ --all --target-name "CloudServe" --narrative
```

Verify `METADATA.json` exists in output directory.

**Success Criteria:**
- CloudServe README complete
- Great Insurance README complete
- Golden fixture README complete
- METADATA.json auto-generated on all new runs
- Documentation reviewed by second team member

**Time Estimate:** 2-3 days

---

### Phase 4: CI Integration - Pull Requests (Week 5)

**Goal:** Enable automated validation in PR workflow.

**Tasks:**

1. **Create PR workflow**

**File:** `.github/workflows/pull-request.yml`

Copy configuration from `05-ci-integration.md`.

2. **Test PR workflow**

Create test branch:

```bash
git checkout -b test/pr-workflow
# Make trivial change
git add .
git commit -m "Test PR workflow"
git push origin test/pr-workflow
```

Open PR, verify workflow runs.

3. **Implement pre-commit hooks**

**File:** `.pre-commit-config.yaml`

```bash
# Install
pip install pre-commit
pre-commit install

# Test
echo "test" >> tests/golden/cloudserve_expected.json
git add tests/golden/cloudserve_expected.json
git commit -m "Test pre-commit"
# Should block due to invalid JSON
```

4. **Create fixture update workflow**

**File:** `.github/workflows/fixture-update.yml`

Test by modifying a fixture in a PR.

5. **Team training**

- Demo PR workflow to team
- Show pre-commit hook installation
- Walk through fixture diff reports

**Success Criteria:**
- PR workflow running on all PRs
- Pre-commit hooks installed by all developers
- Fixture update workflow posting diff reports
- Team trained on new workflows

**Time Estimate:** 3-4 days

**Rollback Plan:** If CI causes too many delays, temporarily disable workflow (comment out `on:` triggers), iterate offline, re-enable when stable.

---

### Phase 5: Nightly Regression (Week 6)

**Goal:** Establish continuous monitoring of pipeline accuracy.

**Tasks:**

1. **Create nightly workflow**

**File:** `.github/workflows/nightly-regression.yml`

2. **Set up Slack notifications**

Configure `SLACK_WEBHOOK_URL` secret in GitHub repo settings.

3. **Establish baseline metrics**

Run nightly workflow manually for 5 consecutive nights:

```bash
# GitHub Actions UI → Nightly Regression → Run workflow
```

Track:
- Pass/fail rates
- Runtime per deal
- API costs
- False positive rate

4. **Create accuracy trending dashboard**

**File:** `tests/scripts/generate_accuracy_trends.py`

Generate JSON with historical accuracy data:

```json
{
  "cloudserve": {
    "2026-02-11": {"app_count_accuracy": 1.0, "cost_accuracy": 0.99},
    "2026-02-12": {"app_count_accuracy": 1.0, "cost_accuracy": 0.98},
    ...
  }
}
```

5. **Review first week of results**

After 1 week of nightly runs:
- Identify flaky tests (adjust tolerances)
- Optimize runtime (cache, parallelism)
- Verify Slack notifications working

**Success Criteria:**
- Nightly workflow runs successfully for 1 week
- <10% false failure rate
- Slack notifications delivered
- Baseline metrics documented

**Time Estimate:** 4-5 days (including 1 week observation period)

---

### Phase 6: Full Rollout & Backfill (Week 7+)

**Goal:** Expand to all existing deals, enforce validation universally.

**Tasks:**

1. **Identify remaining deals**

```bash
cd "9.5/it-diligence-agent 2"
ls data/input/ | grep -E "Target_.*_Document" | cut -d_ -f2 | sort -u
```

Expected deals to backfill:
- Buyer_ESG (if separate from CloudServe)
- Any other test data sets

2. **Backfill fixtures**

For each deal:
- Run pipeline
- Create golden fixture
- Write validation test
- Write README

Pace: 1 deal per 2-3 days.

3. **Update CI to require validation**

Modify `.github/workflows/pull-request.yml`:

```yaml
# Change from CloudServe-only to all deals
- name: Run all validation tests
  run: |
    pytest tests/validation/ -v --tb=short
```

4. **Quarterly maintenance process**

Document in `tests/golden/README.md`:

**Quarterly Fixture Review:**
1. Re-run pipeline on all deals
2. Compare outputs to fixtures
3. Update fixtures if improvements detected
4. Bump version numbers
5. Document changes in PR

5. **Team handoff**

- Train team on fixture creation
- Establish on-call rotation for nightly failures
- Document escalation path

**Success Criteria:**
- All existing deals have fixtures
- All PRs run full validation suite
- Quarterly maintenance scheduled
- Team self-sufficient on fixture updates

**Time Estimate:** 2-4 weeks (depending on number of deals)

---

## Verification Strategy

### Success Metrics (Per Phase)

| Phase | Metric | Target |
|-------|--------|--------|
| Phase 0 | Unit tests passing | 100% (20+ tests) |
| Phase 1 | CloudServe assertions passing | 100% (10+ assertions) |
| Phase 2 | Great Insurance assertions passing | 100% |
| Phase 3 | Documentation completeness | 100% (all READMEs) |
| Phase 4 | PR workflow adoption | 100% of PRs |
| Phase 5 | Nightly false failure rate | <10% |
| Phase 6 | Deal coverage | 100% of test deals |

### Rollback Triggers

Rollback to previous phase if:

1. **Phase 1/2:** Validation tests pass <80% of the time → Tolerances too strict
2. **Phase 4:** PR workflow blocks >50% of PRs → Workflow too strict, disable temporarily
3. **Phase 5:** Nightly costs >$50/month → Reduce frequency or parallelism
4. **Phase 6:** Team spends >20% time on fixture maintenance → Simplify framework

---

## Team Coordination

### Roles & Responsibilities

| Role | Responsibilities |
|------|------------------|
| **Fixture Owner** | Create/maintain golden fixtures for assigned deals |
| **CI Owner** | Maintain GitHub Actions workflows, debug CI failures |
| **Assertion Owner** | Maintain assertion library, add new assertion types as needed |
| **Documentation Owner** | Keep READMEs up to date, onboard new team members |

### Communication Plan

**Weekly Standup:**
- Review nightly validation results
- Triage fixture drift issues
- Plan fixture updates

**Monthly Review:**
- Accuracy trending analysis
- False positive/negative rates
- CI cost optimization

**Quarterly Planning:**
- Fixture refresh cycle
- New assertion types needed
- Framework improvements

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Fixtures drift from reality** | High | Medium | Quarterly refresh, nightly monitoring |
| **CI costs too high** | Medium | Medium | Matrix strategy, caching, cost alerts |
| **Team rejects framework (too complex)** | High | Low | Phased rollout, good docs, training |
| **False positives cause alert fatigue** | Medium | Medium | Tolerance tuning, Slack threshold (CRITICAL only) |
| **Fixtures become test-to-test** | High | Low | Peer review, manual verification required |

---

## Results Criteria

- All 6 phases completed
- CloudServe + Great Insurance validated continuously
- CI/CD workflows operational
- Team trained and self-sufficient
- Quarterly maintenance process established
- Documentation complete

---

## Migration Checklist

### Pre-Migration

- [ ] Spec documents reviewed and approved
- [ ] Team capacity allocated (7+ weeks)
- [ ] GitHub Actions enabled on repo
- [ ] Slack webhook configured

### Phase 0 (Foundation)

- [ ] Directory structure created
- [ ] Assertion base classes implemented
- [ ] Core assertion types implemented (Count, Cost, Risk, Completeness)
- [ ] Unit tests passing (20+ tests)

### Phase 1 (CloudServe Pilot)

- [ ] CloudServe fixture created
- [ ] Schema validation passing
- [ ] Validation test written (10+ assertions)
- [ ] Manual verification completed

### Phase 2 (Great Insurance)

- [ ] Great Insurance fixture created
- [ ] Validation test passing
- [ ] Tolerances refined

### Phase 3 (Documentation)

- [ ] CloudServe README written
- [ ] Great Insurance README written
- [ ] Golden fixture README written
- [ ] METADATA.json auto-generation implemented

### Phase 4 (CI - PRs)

- [ ] PR workflow implemented
- [ ] Pre-commit hooks configured
- [ ] Fixture update workflow implemented
- [ ] Team trained

### Phase 5 (Nightly)

- [ ] Nightly workflow implemented
- [ ] Slack notifications working
- [ ] Baseline metrics established
- [ ] 1 week observation period completed

### Phase 6 (Full Rollout)

- [ ] All deals backfilled
- [ ] Full validation in CI
- [ ] Quarterly maintenance scheduled
- [ ] Team handoff completed

---

## Post-Migration

### Ongoing Maintenance

**Weekly:**
- Review nightly validation failures
- Triage and fix within 2 business days

**Monthly:**
- Analyze accuracy trends
- Optimize CI costs
- Update documentation

**Quarterly:**
- Refresh all fixtures
- Add new assertion types as needed
- Team retrospective on framework

### Success Indicators (6 Months)

- Zero undetected regressions in production
- <5% false failure rate in nightly runs
- <10% team time spent on validation maintenance
- 100% of new deals have fixtures within 1 week

---

## Cross-References

- **01-test-validation-architecture.md:** Framework architecture being rolled out
- **02-golden-fixture-schema.md:** Schema used in Phase 1-2
- **03-validation-assertions.md:** Assertions implemented in Phase 0
- **04-test-data-documentation.md:** Templates created in Phase 3
- **05-ci-integration.md:** CI workflows implemented in Phase 4-5
