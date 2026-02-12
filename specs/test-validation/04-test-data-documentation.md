# Test Data Documentation Standards

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document defines standards for documenting test data sets used in IT due diligence pipeline validation. Proper documentation prevents confusion about which dossier validates which source documents (the root cause identified in audit1).

**Purpose:** Provide templates and guidelines for creating clear, maintainable documentation that maps source documents → expected outputs → validation criteria.

**Scope:** README templates, metadata structures, mapping tables, and maintenance procedures for test data sets.

---

## Architecture

### Documentation Structure

```
data/input/
├── Target_CloudServe_Document_*.md (6 files)      ← Source documents
├── Buyer_ESG_Document_*.md (6 files)
├── Great_Insurance_Document_*.md (7 files)
└── CLOUDSERVE_README.md                          ← Documentation (NEW)
    └── Mapping to output/deals/cloudserve/
    └── Expected outcomes
    └── Intentional gaps

tests/golden/
├── cloudserve_expected.json                      ← Golden fixture
├── great_insurance_expected.json
└── README.md                                      ← Fixture documentation (NEW)
    └── How to create fixtures
    └── How to update fixtures

output/deals/
├── 2026-02-11_110325_cloudserve/                ← Actual outputs
│   ├── inventory_store.json
│   ├── facts.json
│   └── METADATA.json                             ← Deal metadata (NEW)
│       └── Links back to source documents
└── 2026-02-10_172444_great-insurance/
```

---

## Specification

### 1. Test Data Set README Template

**File:** `data/input/{DEAL_NAME}_README.md`

**Purpose:** Explain what this test data set represents and how to use it.

**Template:**

```markdown
# {Deal Name} Test Data Set

**Deal Type:** [M&A Acquisition | Carve-out | Merger]
**Target Industry:** [SaaS/Platform | Insurance | Healthcare | ...]
**Buyer Industry:** [Private Equity | Strategic | ...]
**Complexity:** [Low | Medium | High | Extreme]
**Version:** 1.0
**Last Updated:** YYYY-MM-DD

---

## Overview

**Purpose of this test set:** [1-2 sentences]

**Scenario:** [Brief description of the M&A scenario this represents]

**Key Characteristics:**
- Application count: X
- Annual IT spend: $Y
- Headcount: Z
- Primary tech stack: [List]

---

## Source Documents

| Document | Filename | Domain | Pages | Completeness |
|----------|----------|--------|-------|--------------|
| Doc 1 | Target_{Deal}_Document_1_Executive_IT_Profile.md | Executive Overview | 3 | 85% |
| Doc 2 | Target_{Deal}_Document_2_Application_Inventory.md | Applications | 12 | 95% |
| Doc 3 | Target_{Deal}_Document_3_Infrastructure_Hosting_Inventory.md | Infrastructure | 8 | 88% |
| Doc 4 | Target_{Deal}_Document_4_Network_Cybersecurity_Inventory.md | Network/Cyber | 6 | 82% |
| Doc 5 | Target_{Deal}_Document_5_Identity_Access_Management.md | Identity | 4 | 90% |
| Doc 6 | Target_{Deal}_Document_6_Organization_Vendor_Inventory.md | Organization | 5 | 78% |

---

## Expected Outcomes

### Ground Truth (Validated)

**Applications:**
- Count: 38
- Total Cost: $2,331,500
- Critical Apps: 11
- Key Apps: Salesforce, NetSuite, Okta, Datadog

**Infrastructure:**
- Items: 120 (85 containers, 12 serverless, 23 managed services)
- Hosting: 100% AWS
- Environments: Production, Staging, Development

**Organization:**
- Headcount: 45
- Total Compensation: $6.75M
- Functions: Engineering (28), DevOps (8), Security (4), Ops (3), Leadership (2)

**Risks (Critical):**
- R-WIZ-CONTRACT-EXPIRING: Wiz contract ends in 2 months
- R-DATADOG-HIGH-COST: Datadog cost increasing
- R-DUAL-ERP-POTENTIAL: Potential ERP overlap with buyer

---

## Intentional Gaps

**Data intentionally MISSING from source documents:**

1. **Carve-Out Dependencies:** CloudServe is a standalone acquisition, not a carve-out. No "Carve Out Dependency" field expected.

2. **Detailed API Integration List:** Document 2 mentions this as a VDR request (data gap). Pipeline should flag this gap, not extract non-existent data.

3. **Historical Cost Trends:** Only current annual costs provided. No trend analysis possible.

**Why these gaps exist:** To test that the pipeline correctly identifies missing data and generates appropriate VDR requests.

---

## Validation Mapping

**Golden Fixture:** `tests/golden/cloudserve_expected.json`

**Pipeline Output:** `output/deals/{timestamp}_cloudserve/`

**Validation Test:** `tests/validation/test_cloudserve_accuracy.py`

**Run validation:**
```bash
pytest tests/validation/test_cloudserve_accuracy.py -v
```

**Expected result:** All assertions pass ✅

---

## Known Issues

**Issue #1:** Category mapping for "policy administration" systems
- **Status:** Known limitation
- **Impact:** Duck Creek/Majesco may be categorized as "industry_vertical" instead of more specific category
- **Workaround:** Assertion uses tolerance to allow minor category variations

---

## Maintenance

**When to update this README:**
- Source documents modified
- Expected outcomes change (e.g., improved extraction finds more apps)
- New intentional gaps added

**Update procedure:**
1. Modify source documents
2. Update "Expected Outcomes" section with new ground truth
3. Regenerate golden fixture (see `tests/golden/README.md`)
4. Update "Last Updated" timestamp

---

## Cross-References

- **Golden Fixture:** `tests/golden/cloudserve_expected.json`
- **Validation Spec:** `specs/test-validation/03-validation-assertions.md`
- **Pipeline Output:** `output/deals/*/METADATA.json`
```

---

### 2. Golden Fixture README Template

**File:** `tests/golden/README.md`

**Purpose:** Explain how to create and update golden fixture files.

**Template:**

```markdown
# Golden Fixtures - Usage Guide

Golden fixtures represent **expected pipeline outputs** for validation testing. Each fixture is a JSON file containing ground truth values that actual pipeline outputs are compared against.

---

## Creating a New Fixture

**Prerequisites:**
1. Source documents exist in `data/input/`
2. Test data README created (see `data/input/{DEAL}_README.md` template)
3. Pipeline has been run manually and outputs reviewed for accuracy

**Steps:**

### Step 1: Run Discovery Pipeline

```bash
cd "9.5/it-diligence-agent 2"
python main_v2.py data/input/ --all --target-name "{DealName}" --narrative
```

Wait for pipeline to complete (~5-10 minutes).

### Step 2: Review Outputs Manually

Check `output/deals/{timestamp}_{dealname}/`:
- `inventory_store.json` - Verify app counts, costs accurate
- `facts_{timestamp}.json` - Verify facts extracted correctly
- `findings_{timestamp}.json` - Verify risks/work items make sense
- `reports/it_dd_report_{timestamp}.html` - Human-readable dossier

**Validation questions:**
- Are all expected apps present?
- Are costs extracted correctly (no $0 where cost exists)?
- Are critical risks detected?

### Step 3: Create Fixture JSON

Use `02-golden-fixture-schema.md` as template.

**File:** `tests/golden/{dealname}_expected.json`

**Extract values from validated outputs:**

```json
{
  "metadata": {
    "deal_name": "cloudserve",
    "entity": "target",
    "created_at": "2026-02-11T11:30:00Z",
    "source_documents": [
      "Target_CloudServe_Document_1_Executive_IT_Profile.md",
      ...
    ],
    "version": "1.0.0",
    "notes": "CloudServe is a SaaS platform company..."
  },
  "applications": {
    "count": 38,  ← From inventory_store.json item count
    "total_cost": 2331500,  ← Sum of app costs
    "by_category": { ... },  ← From category breakdown
    ...
  },
  ...
}
```

**Tip:** Use `scripts/generate_fixture.py` (if exists) to auto-generate skeleton, then manually verify/adjust.

### Step 4: Validate Fixture Schema

```bash
jsonschema -i tests/golden/{dealname}_expected.json tests/golden/fixture_schema.json
```

If errors: fix JSON format, then re-validate.

### Step 5: Create Validation Test

**File:** `tests/validation/test_{dealname}_accuracy.py`

See `test_cloudserve_accuracy.py` as example.

Minimum assertions:
- Application count
- Total cost
- Critical apps present
- Critical risks detected
- Headcount
- Completeness scores

### Step 6: Run Validation

```bash
pytest tests/validation/test_{dealname}_accuracy.py -v
```

**Expected:** All tests pass ✅

If failures:
- Check if pipeline output is actually wrong (bug) → fix pipeline
- Check if fixture has typos → fix fixture
- Check if tolerance too strict → adjust assertion tolerance

### Step 7: Commit Fixture

```bash
git add tests/golden/{dealname}_expected.json
git add tests/validation/test_{dealname}_accuracy.py
git add data/input/{DEALNAME}_README.md
git commit -m "Add golden fixture for {DealName} test scenario"
```

---

## Updating an Existing Fixture

**When to update:**
- Pipeline improvements change extraction accuracy (e.g., better category mapping)
- Source documents modified
- Intentional gaps added/removed

**Procedure:**

1. **Verify change is intentional:**
   - Run pipeline on unchanged source docs
   - Compare new output to old fixture
   - If differences are improvements (not regressions), update fixture

2. **Update fixture JSON:**
   - Modify `tests/golden/{dealname}_expected.json`
   - Update version number (e.g., 1.0.0 → 1.1.0)
   - Add notes explaining what changed

3. **Re-validate:**
   ```bash
   pytest tests/validation/test_{dealname}_accuracy.py -v
   ```

4. **Document in PR:**
   - Explain why fixture changed
   - Show diff of old vs new values
   - Confirm manual review verified accuracy

**DO NOT update fixtures to make failing tests pass without understanding root cause.**

---

## Fixture Maintenance Best Practices

### Version Control

- **Commit fixtures to git:** Treat as source code
- **Review changes:** PR reviews should verify fixture updates are correct
- **Semantic versioning:** MAJOR.MINOR.PATCH
  - MAJOR: Breaking schema changes
  - MINOR: New fields added
  - PATCH: Value corrections

### Documentation

- **metadata.notes:** Always document fixture purpose
- **expected_gaps:** List intentional missing data with reasons
- **Cross-reference:** Link to source docs and validation tests

### Quality Checks

- **Peer review:** Have second person verify fixture values before commit
- **Schema validation:** Always run `jsonschema` before commit
- **Test run:** Verify validation test passes before push

---

## Troubleshooting

**Problem:** Fixture validation fails with schema error

**Solution:**
```bash
# Validate fixture against schema
jsonschema -i tests/golden/cloudserve_expected.json tests/golden/fixture_schema.json

# Common issues:
# - Missing required field (add it)
# - Wrong type (string vs integer)
# - Invalid enum value (check allowed values)
```

**Problem:** Validation test fails but pipeline output looks correct

**Solution:**
- Check assertion tolerance (may be too strict)
- Verify fixture has correct expected values
- Check for typos in fixture (case sensitivity)

**Problem:** Don't know what values to put in fixture

**Solution:**
1. Run pipeline on source docs
2. Manually review outputs for accuracy
3. Extract validated values into fixture
4. When in doubt, be conservative (use ranges, tolerances)

---

## Cross-References

- **Schema Specification:** `specs/test-validation/02-golden-fixture-schema.md`
- **Assertion Types:** `specs/test-validation/03-validation-assertions.md`
- **Architecture:** `specs/test-validation/01-test-validation-architecture.md`
```

---

### 3. Deal Output Metadata

**File:** `output/deals/{deal_id}/METADATA.json` (auto-generated by pipeline)

**Purpose:** Link pipeline outputs back to source documents for traceability.

**Schema:**

```json
{
  "$schema": "deal-metadata-v1.0",
  "deal_id": "2026-02-11_110325_cloudserve",
  "deal_name": "cloudserve",
  "entity": "target",
  "created_at": "2026-02-11T11:07:10Z",
  "pipeline_version": "2.4.0",
  "source_documents": [
    {
      "filename": "Target_CloudServe_Document_1_Executive_IT_Profile.md",
      "path": "data/input/Target_CloudServe_Document_1_Executive_IT_Profile.md",
      "md5_hash": "a1b2c3d4...",
      "size_bytes": 15234,
      "entity": "target"
    },
    ...
  ],
  "outputs": {
    "inventory_store": "inventory_store.json",
    "facts": "facts_20260211_110710.json",
    "findings": "findings_20260211_110710.json",
    "dossier": "reports/it_dd_report_20260211_110710.html"
  },
  "golden_fixture": "tests/golden/cloudserve_expected.json",
  "validation_test": "tests/validation/test_cloudserve_accuracy.py",
  "validation_status": "passed",
  "validation_run_at": "2026-02-11T11:15:00Z"
}
```

**Auto-generation:** Pipeline should create this file automatically at end of run.

---

## Verification Strategy

### Manual Verification Steps

**Test: Create new fixture from scratch**

1. Run discovery on CloudServe docs
2. Follow `tests/golden/README.md` instructions
3. Create fixture without looking at existing cloudserve_expected.json
4. Compare created fixture to reference
5. Verify values match within tolerance

**Expected:** Newly created fixture validates successfully against schema and test passes.

---

### Automated Checks

**Test: Metadata file generated**

```python
def test_metadata_file_exists(deal_path):
    """Every deal output should have METADATA.json."""
    metadata_file = deal_path / "METADATA.json"
    assert metadata_file.exists()

    metadata = json.loads(metadata_file.read_text())
    assert "source_documents" in metadata
    assert "golden_fixture" in metadata
```

---

## Benefits

### Why Documentation Templates

1. **Consistency:** All test sets documented the same way
2. **Onboarding:** New team members can understand test data quickly
3. **Maintenance:** Clear update procedures prevent drift

### Why Metadata Files

1. **Traceability:** Link outputs back to inputs
2. **Reproducibility:** Know exactly which docs produced which dossier
3. **Validation:** Auto-verify that correct fixture is used for each deal

---

## Expectations

### Success Metrics

1. **Coverage:** All test data sets have README files
2. **Clarity:** New team member can understand test set in <5 minutes
3. **Accuracy:** Mapping from source → output → fixture is unambiguous
4. **Freshness:** READMEs updated within 1 week of test data changes

### Acceptance Criteria

- CloudServe README created and reviewed
- Great Insurance README created
- Golden fixture README with create/update procedures
- METADATA.json schema defined and auto-generated

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Documentation drift:** READMEs become stale | Add "Last Updated" timestamp, review quarterly |
| **Metadata not generated:** Pipeline skips METADATA.json | Add validation check in CI/CD |
| **Fixtures created incorrectly:** Human error in manual extraction | Peer review process, auto-generation scripts where possible |

---

## Results Criteria

- CloudServe README exists and documents all 6 source docs
- Golden fixture README has complete create/update procedures
- METADATA.json schema defined
- Sample METADATA.json exists for CloudServe deal

---

## Cross-References

- **Architecture:** `01-test-validation-architecture.md`
- **Fixture Schema:** `02-golden-fixture-schema.md`
- **Assertions:** `03-validation-assertions.md`
- **Migration:** `06-migration-rollout.md` (backfilling documentation)
