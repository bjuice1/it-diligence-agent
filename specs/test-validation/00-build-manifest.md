# BUILD MANIFEST: Test Validation Framework

**Build Type:** TYPE B - Multi-Component System
**Status:** READY FOR EXECUTION
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Executive Summary

This manifest defines the complete build plan for implementing a test validation framework that prevents the root cause identified in audit1: **confusion about which dossier validates which source documents**.

**Problem:** CloudServe test documents were being compared against the wrong "Northstar" dossier (Great Insurance), leading to false accuracy assessments.

**Solution:** Pytest-based validation framework with golden fixtures, type-specific assertions, comprehensive documentation, and CI/CD integration.

**Build Duration:** 7 weeks (6 phases)
**Complexity:** HIGH (multi-component system with CI/CD integration)
**Dependencies:** pytest, jsonschema, GitHub Actions, Anthropic API

---

## Architecture Overview

```
Test Validation Framework
├── Golden Fixtures (JSON)
│   ├── Schema definition (fixture_schema.json)
│   └── Per-deal expected outputs (cloudserve_expected.json, etc.)
│
├── Assertion Engine
│   ├── Base assertion classes
│   └── 12 type-specific assertions (Count, Cost, Risk, etc.)
│
├── Validation Tests
│   ├── pytest test files per deal
│   └── Tolerance-based matching
│
├── Documentation System
│   ├── Test data set READMEs
│   ├── Golden fixture README
│   └── METADATA.json (auto-generated)
│
└── CI/CD Integration
    ├── Pull request workflow
    ├── Nightly regression suite
    ├── Fixture update workflow
    └── Pre-commit hooks
```

---

## Document Dependency Graph

```
00-build-manifest.md (THIS FILE)
    │
    ├─→ 01-test-validation-architecture.md
    │       │
    │       ├─→ Component: FixtureLoader
    │       ├─→ Component: Assertion Engine
    │       ├─→ Component: Test Runner
    │       └─→ Component: Report Generator
    │
    ├─→ 02-golden-fixture-schema.md
    │       │
    │       ├─→ JSON schema definition
    │       ├─→ CloudServe fixture example
    │       └─→ Validation rules
    │
    ├─→ 03-validation-assertions.md
    │       │
    │       ├─→ CountAssertion (tolerance-based)
    │       ├─→ CostAssertion (percentage-based)
    │       ├─→ RiskAssertion (set matching)
    │       ├─→ CompletenessAssertion (range)
    │       ├─→ ItemPresenceAssertion (existence)
    │       ├─→ CategoryBreakdownAssertion (distribution)
    │       └─→ 6 additional assertion types
    │
    ├─→ 04-test-data-documentation.md
    │       │
    │       ├─→ Test Data Set README template
    │       ├─→ Golden Fixture README template
    │       └─→ METADATA.json schema
    │
    ├─→ 05-ci-integration.md
    │       │
    │       ├─→ Pull request workflow
    │       ├─→ Nightly regression workflow
    │       ├─→ Fixture update workflow
    │       └─→ Pre-commit hooks
    │
    └─→ 06-migration-rollout.md
            │
            ├─→ Phase 0: Foundation
            ├─→ Phase 1: CloudServe Pilot
            ├─→ Phase 2: Great Insurance Expansion
            ├─→ Phase 3: Documentation & Templates
            ├─→ Phase 4: CI Integration (PRs)
            ├─→ Phase 5: Nightly Regression
            └─→ Phase 6: Full Rollout & Backfill
```

---

## Build Order (Critical Path)

### Phase 0: Foundation (Week 1)
**Reference:** `06-migration-rollout.md` § Phase 0

1. Create directory structure
2. Implement assertion base classes (`03-validation-assertions.md` § 1-4)
3. Write unit tests for assertions
4. Verify 20+ unit tests passing

**Outputs:**
- `tests/assertions/base.py`
- `tests/assertions/count_assertion.py`
- `tests/assertions/cost_assertion.py`
- `tests/assertions/risk_assertion.py`
- `tests/assertions/completeness_assertion.py`
- `tests/unit/assertions/test_*.py`

**Exit Criteria:** All unit tests passing, no existing tests broken

---

### Phase 1: CloudServe Pilot (Week 2)
**Reference:** `06-migration-rollout.md` § Phase 1

1. Run discovery pipeline on CloudServe docs
2. Manually verify outputs (inventory, facts, findings)
3. Create golden fixture (`02-golden-fixture-schema.md`)
4. Validate fixture against schema
5. Write validation test (`01-test-validation-architecture.md` § Test Runner)
6. Run validation test and verify pass

**Outputs:**
- `tests/golden/cloudserve_expected.json`
- `tests/golden/fixture_schema.json`
- `tests/validation/test_cloudserve_accuracy.py`

**Exit Criteria:** CloudServe validation test passes with 10+ assertions

---

### Phase 2: Great Insurance Expansion (Week 3)
**Reference:** `06-migration-rollout.md` § Phase 2

1. Create Great Insurance golden fixture
2. Write Great Insurance validation test
3. Run both validation tests
4. Refine tolerances based on multi-deal learnings
5. Document tolerance rationale

**Outputs:**
- `tests/golden/great_insurance_expected.json`
- `tests/validation/test_great_insurance_accuracy.py`

**Exit Criteria:** Both CloudServe and Great Insurance validation tests passing

---

### Phase 3: Documentation & Templates (Week 4)
**Reference:** `06-migration-rollout.md` § Phase 3

1. Write CloudServe README (`04-test-data-documentation.md` § 1)
2. Write Great Insurance README
3. Write golden fixture README (`04-test-data-documentation.md` § 2)
4. Implement METADATA.json auto-generation (`04-test-data-documentation.md` § 3)
5. Test metadata generation on both deals

**Outputs:**
- `data/input/CLOUDSERVE_README.md`
- `data/input/GREAT_INSURANCE_README.md`
- `tests/golden/README.md`
- Updated `main_v2.py` with metadata generation

**Exit Criteria:** All documentation complete, METADATA.json auto-generated on new runs

---

### Phase 4: CI Integration - Pull Requests (Week 5)
**Reference:** `06-migration-rollout.md` § Phase 4

1. Create PR workflow (`05-ci-integration.md` § 1)
2. Test PR workflow on test branch
3. Implement pre-commit hooks (`05-ci-integration.md` § 4)
4. Create fixture update workflow (`05-ci-integration.md` § 3)
5. Train team on new workflows

**Outputs:**
- `.github/workflows/pull-request.yml`
- `.pre-commit-config.yaml`
- `.github/workflows/fixture-update.yml`
- `tests/scripts/check_fixture_versions.py`
- `tests/scripts/generate_fixture_diff.py`

**Exit Criteria:** PR workflow running, pre-commit hooks installed by team

---

### Phase 5: Nightly Regression (Week 6)
**Reference:** `06-migration-rollout.md` § Phase 5

1. Create nightly workflow (`05-ci-integration.md` § 2)
2. Set up Slack notifications
3. Run nightly workflow for 1 week (baseline)
4. Create accuracy trending dashboard
5. Review results, optimize runtime

**Outputs:**
- `.github/workflows/nightly-regression.yml`
- `tests/scripts/generate_accuracy_trends.py`
- Baseline metrics document

**Exit Criteria:** Nightly workflow runs successfully for 1 week, <10% false failure rate

---

### Phase 6: Full Rollout & Backfill (Week 7+)
**Reference:** `06-migration-rollout.md` § Phase 6

1. Identify remaining deals to backfill
2. Create fixtures for all remaining deals (1 per 2-3 days)
3. Update CI to require validation on all deals
4. Document quarterly maintenance process
5. Team handoff

**Outputs:**
- Golden fixtures for all deals
- Validation tests for all deals
- READMEs for all deals
- Quarterly maintenance schedule

**Exit Criteria:** 100% deal coverage, full validation in CI, team self-sufficient

---

## File Inventory

### Specification Documents (6 + 1 manifest)

| File | Size | Purpose |
|------|------|---------|
| `00-build-manifest.md` | This file | Build plan and execution guide |
| `01-test-validation-architecture.md` | 18KB | Framework design, component specs |
| `02-golden-fixture-schema.md` | 22KB | JSON schema, CloudServe example |
| `03-validation-assertions.md` | 19KB | 12 assertion types with implementations |
| `04-test-data-documentation.md` | 17KB | README templates, metadata schema |
| `05-ci-integration.md` | 21KB | GitHub Actions workflows, pre-commit hooks |
| `06-migration-rollout.md` | 20KB | 6-phase migration plan |

**Total:** ~137KB of specification

---

### Implementation Files (To Be Created)

**Core Framework:**
- `tests/assertions/base.py` (100 lines)
- `tests/assertions/count_assertion.py` (80 lines)
- `tests/assertions/cost_assertion.py` (90 lines)
- `tests/assertions/risk_assertion.py` (100 lines)
- `tests/assertions/completeness_assertion.py` (70 lines)
- `tests/assertions/item_presence_assertion.py` (120 lines)
- `tests/assertions/category_breakdown_assertion.py` (110 lines)

**Golden Fixtures:**
- `tests/golden/fixture_schema.json` (500 lines)
- `tests/golden/cloudserve_expected.json` (400 lines)
- `tests/golden/great_insurance_expected.json` (400 lines)

**Validation Tests:**
- `tests/validation/test_cloudserve_accuracy.py` (200 lines)
- `tests/validation/test_great_insurance_accuracy.py` (200 lines)

**Documentation:**
- `data/input/CLOUDSERVE_README.md` (180 lines)
- `data/input/GREAT_INSURANCE_README.md` (180 lines)
- `tests/golden/README.md` (400 lines)

**CI/CD:**
- `.github/workflows/pull-request.yml` (120 lines)
- `.github/workflows/nightly-regression.yml` (150 lines)
- `.github/workflows/fixture-update.yml` (80 lines)
- `.pre-commit-config.yaml` (40 lines)

**Helper Scripts:**
- `tests/scripts/check_fixture_versions.py` (80 lines)
- `tests/scripts/generate_fixture_diff.py` (100 lines)
- `tests/scripts/generate_accuracy_trends.py` (120 lines)

**Total Estimated Lines of Code:** ~3,700 lines

---

## Dependencies

### Python Packages

```
pytest==7.4.3
pytest-cov==4.1.0
jsonschema==4.20.0
deepdiff==6.7.1
pre-commit==3.6.0
```

### External Services

- **GitHub Actions:** CI/CD runtime
- **Slack Webhook:** Nightly regression notifications
- **Anthropic API:** Pipeline execution (for fixture creation)

### Internal Dependencies

- **InventoryStore:** Source of actual item counts/costs
- **FactStore:** Source of fact-level data
- **FindingStore:** Source of risks/work items
- **main_v2.py:** Pipeline orchestrator (needs METADATA.json hook)

---

## Success Metrics

### Framework Quality

| Metric | Target | Measurement |
|--------|--------|-------------|
| Assertion coverage | 100% of fixture fields | Count assertions in tests vs fields in schema |
| Unit test coverage | >90% | pytest --cov on assertion classes |
| False positive rate | <5% | Failed tests that shouldn't have failed |
| False negative rate | <1% | Regressions not caught by tests |

### Developer Experience

| Metric | Target | Measurement |
|--------|--------|-------------|
| PR workflow runtime | <15 minutes | GitHub Actions timing |
| Pre-commit hook runtime | <30 seconds | Local timing |
| Fixture creation time | <2 hours | Track time from docs to fixture |
| Team adoption | 100% use pre-commit | Git hook install survey |

### Business Value

| Metric | Target | Measurement |
|--------|--------|-------------|
| Undetected regressions | 0 | Production incidents linked to missed regressions |
| Fixture maintenance time | <10% of sprint | Time tracking |
| Documentation completeness | 100% | README exists for all deals |
| Confidence in accuracy | High | Team survey |

---

## Risk Register

| Risk | Severity | Likelihood | Mitigation | Owner |
|------|----------|------------|------------|-------|
| **Fixtures become test-to-test** | HIGH | LOW | Require manual verification before fixture creation | Fixture Owner |
| **CI costs exceed budget** | MEDIUM | MEDIUM | Matrix strategy, caching, monthly cost review | CI Owner |
| **Team rejects complexity** | HIGH | LOW | Phased rollout, comprehensive docs, training | Documentation Owner |
| **False positives cause alert fatigue** | MEDIUM | MEDIUM | Tolerance tuning, Slack threshold (CRITICAL only) | Assertion Owner |
| **Fixtures drift from reality** | HIGH | MEDIUM | Quarterly refresh, nightly monitoring | Fixture Owner |
| **LLM non-determinism breaks tests** | MEDIUM | HIGH | Tolerance-based assertions, re-run on failure | Assertion Owner |

---

## Rollback Plan

### Per-Phase Rollback

**Phase 0-3:** Low risk - no CI integration yet. Simply stop work if issues arise.

**Phase 4 (CI - PRs):** If PR workflow blocks >50% of PRs:
1. Comment out `on:` trigger in `.github/workflows/pull-request.yml`
2. Continue development offline
3. Re-enable when stable

**Phase 5 (Nightly):** If nightly costs >$50/month:
1. Reduce frequency (nightly → 3x/week)
2. Reduce parallelism (matrix → sequential)
3. Cache fixtures where possible

**Phase 6 (Full Rollout):** If team spends >20% time on fixture maintenance:
1. Simplify assertion types (remove complex ones)
2. Increase tolerances
3. Reduce fixture detail level

### Full Rollback

If framework fundamentally doesn't work:
1. Delete `.github/workflows/` validation files
2. Keep assertion library and fixtures (no harm)
3. Continue manual validation process
4. Conduct retrospective to identify root cause

---

## Acceptance Criteria

### Phase Completion

- [ ] All 6 phases completed per `06-migration-rollout.md`
- [ ] All implementation files created
- [ ] All dependencies installed
- [ ] All unit tests passing (100+)
- [ ] All validation tests passing (CloudServe + Great Insurance)

### Quality Gates

- [ ] Peer review on all golden fixtures
- [ ] Manual verification of fixture values
- [ ] CI workflows tested on test branches
- [ ] Pre-commit hooks tested locally
- [ ] Team training completed

### Documentation

- [ ] All READMEs written (CloudServe, Great Insurance, golden fixtures)
- [ ] METADATA.json auto-generation implemented
- [ ] Quarterly maintenance process documented
- [ ] Team handoff guide created

### Production Readiness

- [ ] PR workflow running on all PRs
- [ ] Nightly workflow stable for 1+ week
- [ ] Slack notifications working
- [ ] Baseline accuracy metrics established
- [ ] Team self-sufficient on fixture updates

---

## Maintenance & Support

### Weekly Tasks

- Review nightly validation failures
- Triage and fix within 2 business days
- Update fixtures if pipeline improvements detected

### Monthly Tasks

- Analyze accuracy trends
- Review CI costs, optimize if needed
- Update documentation

### Quarterly Tasks

- Refresh all golden fixtures
- Add new assertion types as needed
- Team retrospective on framework
- Review and adjust tolerances

### On-Call Rotation

- **Primary:** Fixture Owner (responds to nightly failures)
- **Secondary:** CI Owner (if workflow infrastructure issue)
- **Escalation:** Tech Lead (if systematic problem)

---

## Build Command Reference

### Local Development

```bash
cd "9.5/it-diligence-agent 2"

# Install dependencies
pip install pytest pytest-cov jsonschema deepdiff pre-commit

# Run unit tests
pytest tests/unit/assertions/ -v

# Run validation tests
pytest tests/validation/ -v

# Validate fixture against schema
jsonschema -i tests/golden/cloudserve_expected.json tests/golden/fixture_schema.json

# Install pre-commit hooks
pre-commit install

# Run pre-commit manually
pre-commit run --all-files
```

### CI/CD

```bash
# Trigger PR workflow
git push origin feature-branch  # Opens PR → workflow runs

# Trigger nightly manually
# GitHub Actions UI → Nightly Regression → Run workflow

# Test fixture update workflow
# Modify fixture in PR → workflow posts diff report
```

### Pipeline Execution

```bash
# Run full pipeline with metadata generation
python main_v2.py data/input/ --all --target-name "CloudServe" --narrative

# Check generated METADATA.json
cat output/deals/{timestamp}_cloudserve/METADATA.json
```

---

## Cross-Reference Index

### Spec → Implementation Mapping

| Spec Section | Implementation File |
|--------------|---------------------|
| `01 § Component: FixtureLoader` | `tests/assertions/base.py` |
| `01 § Component: Assertion Engine` | `tests/assertions/*.py` |
| `01 § Component: Test Runner` | `tests/validation/test_*.py` |
| `02 § JSON Schema` | `tests/golden/fixture_schema.json` |
| `02 § CloudServe Example` | `tests/golden/cloudserve_expected.json` |
| `03 § CountAssertion` | `tests/assertions/count_assertion.py` |
| `03 § CostAssertion` | `tests/assertions/cost_assertion.py` |
| `03 § RiskAssertion` | `tests/assertions/risk_assertion.py` |
| `04 § Test Data README` | `data/input/CLOUDSERVE_README.md` |
| `04 § Golden Fixture README` | `tests/golden/README.md` |
| `04 § METADATA.json` | Auto-generated in `main_v2.py` |
| `05 § PR Workflow` | `.github/workflows/pull-request.yml` |
| `05 § Nightly Workflow` | `.github/workflows/nightly-regression.yml` |
| `05 § Pre-commit Hooks` | `.pre-commit-config.yaml` |
| `06 § Phase 0-6` | All implementation files |

---

## Appendix: Original Audit Context

### Root Cause (from audit1)

**Problem:** CloudServe test documents were being compared against "Northstar" dossier (Great Insurance), causing false accuracy assessments.

**Evidence:**
- GPT feedback: "These CloudServe markdown docs are what we're testing for accuracy against [Northstar truth]"
- Feb 11 dossier/workbook labeled as "Northstar truth set"
- No mapping system to link source docs → correct dossier

### Opportunity Statement

Create a systematic validation framework that:
1. Maps source documents to expected outputs (golden fixtures)
2. Validates pipeline outputs against correct fixtures
3. Documents intentional gaps vs bugs
4. Prevents future dossier mismatches

### Complexity Rating

**HIGH** - Multi-component system requiring:
- JSON schema design
- Pytest framework integration
- CI/CD workflows
- Team training and adoption
- Ongoing maintenance process

---

## BUILD STATUS

**Specification Phase:** ✅ COMPLETE (7/7 documents)
**Implementation Phase:** ⏳ PENDING (awaiting execution)
**Expected Completion:** 7 weeks from start

---

**END OF BUILD MANIFEST**

*This manifest is the master build plan. Start with Phase 0 in `06-migration-rollout.md`.*
