# Validation Script Usage Guide

## Overview

`validate_automation.py` compares your IT due diligence automation output against the expected facts ground truth to measure accuracy and detect known failure modes.

**Purpose:** Ensure automation is extracting the correct information from test documents.

**Location:** `/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent 2/validate_automation.py`

---

## Quick Start

### 1. Run Your Automation

First, run the automation with your test documents:

```bash
cd "/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent 2"

# CLI - full pipeline (all 6 domains, parallel)
python main_v2.py data/input/ --all --target-name "CloudServe"

# Note the deal_id and facts file location from output
```

### 2. Run Validation

```bash
# Basic validation (facts only)
python validate_automation.py --facts output/facts/facts_TIMESTAMP.json

# Full validation (facts + inventory + findings)
python validate_automation.py \
  --facts output/facts/facts_TIMESTAMP.json \
  --db data/diligence.db \
  --deal-id <deal_id_from_automation>
```

---

## Command-Line Options

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--facts` | Path to facts JSON file | `output/facts/facts_20260213.json` |

### Optional Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--db` | Path to database | `data/diligence.db` |
| `--deal-id` | Deal ID for inventory/findings queries | Required if using DB |
| `--ground-truth` | Path to ground truth markdown | `EXPECTED_FACTS_GROUND_TRUTH.md` |
| `--domain` | Validate specific domain only | All domains |
| `--json-output` | Path to save JSON report | Terminal only |
| `--md-output` | Path to save Markdown report | Terminal only |
| `--verbose` | Detailed output with breakdowns | False |

---

## Usage Examples

### Example 1: Basic Validation (Facts Only)

```bash
python validate_automation.py \
  --facts output/facts/facts_20260213_021915.json
```

**Output:**
- Terminal report with fact count validation by domain
- Known failure mode detection (org explosion, entity detection, etc.)
- Exit code: 0 (pass), 1 (fail), 2 (warning)

**When to use:** Quick check of fact extraction without database queries.

---

### Example 2: Full Validation (Facts + Inventory + Findings)

```bash
python validate_automation.py \
  --facts output/facts/facts_20260213_021915.json \
  --db data/diligence.db \
  --deal-id abc123-def456
```

**Output:**
- Fact count validation
- Inventory count validation (38 target apps, 9 buyer apps)
- Reasoning outputs validation (risks, work items, findings)
- Entity scoping validation
- Known failure mode detection

**When to use:** Complete validation including reasoning phase outputs.

---

### Example 3: Validate Specific Domain

```bash
python validate_automation.py \
  --facts output/facts/facts_20260213_021915.json \
  --domain organization
```

**Output:**
- Organization domain validation only
- Detects organization fact explosion (432 vs 15)

**When to use:** Debugging specific domain issues.

---

### Example 4: Generate Reports

```bash
python validate_automation.py \
  --facts output/facts/facts_20260213_021915.json \
  --db data/diligence.db \
  --deal-id abc123 \
  --json-output validation_report.json \
  --md-output validation_report.md \
  --verbose
```

**Output:**
- Terminal report (verbose mode with entity breakdowns)
- JSON report (`validation_report.json`) for machine consumption
- Markdown report (`validation_report.md`) for documentation

**When to use:** Creating validation documentation or feeding results into CI/CD.

---

## Understanding the Output

### Terminal Report Structure

```
================================================================================
IT DUE DILIGENCE AUTOMATION VALIDATION REPORT
================================================================================

Timestamp: 2026-02-13 15:30:45
Ground Truth: EXPECTED_FACTS_GROUND_TRUTH.md

Overall Status: PASS

  ✅ PASS: 28
  ⚠️  WARNING: 2
  ❌ FAIL: 0

FACT COUNTS BY DOMAIN:

Domain               Expected     Actual       Accuracy     Status
--------------------------------------------------------------------------------
ORGANIZATION         24           26           108.3%       ⚠️  WARNING
APPLICATIONS         47           47           100.0%       ✅ PASS
INFRASTRUCTURE       47           45           95.7%        ✅ PASS
...

INVENTORY COUNTS:

Applications: 47 (expected 47)
  └─ Target: 38 (expected 38)
  └─ Buyer:  9 (expected 9)
  Status: ✅ PASS

REASONING OUTPUTS:

Findings exist                 ✅ PASS  (Reasoning phase executed)
Risks count                    ✅ PASS  (Found 12 risks)
Work items count               ✅ PASS  (Found 15 work items)

ENTITY SCOPING:

Target facts present           ✅ PASS  (Found 168 target facts)
Buyer facts present            ✅ PASS  (Found 75 buyer facts)
Entity distribution            ✅ PASS  (Healthy distribution: 168 target, 75 buyer)

================================================================================
```

### Status Meanings

| Status | Symbol | Meaning | Action |
|--------|--------|---------|--------|
| **PASS** | ✅ | Within acceptable range (90-110% accuracy) | No action needed |
| **WARNING** | ⚠️ | Outside ideal range but not critical (80-120%) | Review for improvement |
| **FAIL** | ❌ | Critical deviation or known failure detected | Investigate and fix |

### Exit Codes

| Code | Meaning | When to Expect |
|------|---------|----------------|
| **0** | All validations pass | Automation working correctly |
| **1** | Critical failures detected | Known failure modes present (org explosion, missing reasoning, entity detection failure) |
| **2** | Warnings only | Minor deviations but no critical issues |

---

## Known Failure Modes Detected

The validation script automatically detects these known issues:

### 1. Organization Fact Explosion

**Symptom:** Organization domain shows 400+ facts instead of ~15

**Example output:**
```
🚨 KNOWN FAILURE MODES DETECTED:

  ❌ Organization fact explosion
     Found 432 organization facts (expected ~15)
     Cause: Extracting one fact per table row instead of aggregated facts
```

**Root cause:** Discovery agent creating individual facts for each person/row instead of team-level aggregated facts.

**Fix:** Modify organization discovery agent to aggregate facts by team/category.

---

### 2. Entity Detection Failure

**Symptom:** All facts tagged as "target", 0 buyer facts

**Example output:**
```
🚨 KNOWN FAILURE MODES DETECTED:

  ❌ Entity detection failure
     All facts tagged as 'target', 0 buyer facts found
     Cause: Entity detection logic defaulting all facts to 'target'
```

**Root cause:** Entity detection preprocessing failing, all facts default to `entity: "target"`.

**Fix:** Enhance entity detection logic in document preprocessing.

---

### 3. Reasoning Phase Not Executed

**Symptom:** 0 risks, 0 work items, 0 findings

**Example output:**
```
🚨 KNOWN FAILURE MODES DETECTED:

  ❌ Reasoning phase not executed
     0 risks, 0 work items, 0 findings of any type
     Cause: Web app only runs Phase 1 (Discovery), Phase 2 (Reasoning) never called
```

**Root cause:** Web app (`web/tasks/analysis_tasks.py`) only runs discovery phase, reasoning agents never invoked.

**Fix:** Add Phase 2 (Reasoning) execution after Phase 1 (Discovery) in `_analyze_domain()` function.

---

### 4. Inventory Count Inflation

**Symptom:** Application count >50 (expected 47)

**Example output:**
```
🚨 KNOWN FAILURE MODES DETECTED:

  ❌ Inventory count inflation
     Found 65 applications (expected 38 target + 9 buyer = 47)
     Cause: Counting facts instead of inventory items, or duplicate entries
```

**Root cause:** UI counting facts instead of inventory items, or duplicate inventory entries due to fingerprint collisions.

**Fix:** Query `InventoryStore` instead of `FactStore` for counts; ensure fingerprints include entity to prevent merging.

---

## Validation Criteria

### Fact Count Accuracy

| Accuracy Range | Status | Meaning |
|----------------|--------|---------|
| 90% - 110% | PASS | Within acceptable tolerance |
| 80% - 90% or 110% - 120% | WARNING | Outside ideal range but not critical |
| <80% or >120% | FAIL | Critical deviation |

### Inventory Count Accuracy

| Item Type | Requirement | Tolerance |
|-----------|-------------|-----------|
| Applications | **Exact match** | 0% (must be 38 target + 9 buyer = 47) |
| Infrastructure | Approximate | ±5 items |

### Reasoning Output Thresholds

| Output Type | Expected Minimum | Pass Threshold |
|-------------|------------------|----------------|
| Total findings | >0 | At least 1 finding (proves reasoning ran) |
| Risks | ≥10 | 10 or more risks identified |
| Work items | ≥12 | 12 or more work items identified |

---

## Troubleshooting

### Error: Ground truth file not found

```
❌ Error: Ground truth file not found: EXPECTED_FACTS_GROUND_TRUTH.md
```

**Solution:** Ensure you're running the script from the correct directory, or specify the path:

```bash
python validate_automation.py \
  --facts output/facts/facts_TIMESTAMP.json \
  --ground-truth /path/to/EXPECTED_FACTS_GROUND_TRUTH.md
```

---

### Error: Facts JSON not found

```
❌ Error: Facts JSON not found: output/facts/facts_TIMESTAMP.json
```

**Solution:** Run automation first to generate facts file, or check the correct timestamp:

```bash
# List available facts files
ls -lh output/facts/

# Use the most recent one
python validate_automation.py --facts output/facts/facts_20260213_021915.json
```

---

### Warning: Database not found

```
Warning: Database not found at data/diligence.db, skipping inventory validation
```

**Impact:** Inventory and findings validation will be skipped.

**Solution:**
- For CLI automation: Use JSON-only validation (no `--db` argument)
- For web app: Specify correct database path with `--db` argument

---

### Warning: Could not query inventory

```
Warning: Could not query inventory: no such table: inventory_items
```

**Cause:** Database exists but schema is different (older version, not initialized, etc.)

**Solution:** Check database schema or regenerate database by running automation again.

---

## Integration with CI/CD

### Basic CI Integration

```bash
#!/bin/bash
# validate.sh - Run automation validation in CI pipeline

set -e  # Exit on error

# Run automation
python main_v2.py data/input/ --all --target-name "CloudServe"

# Extract deal_id from output (adjust grep pattern as needed)
DEAL_ID=$(grep -oP 'deal_id: \K[a-f0-9-]+' automation.log | head -1)

# Find most recent facts file
FACTS_FILE=$(ls -t output/facts/facts_*.json | head -1)

# Run validation
python validate_automation.py \
  --facts "$FACTS_FILE" \
  --db data/diligence.db \
  --deal-id "$DEAL_ID" \
  --json-output validation_report.json

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Validation PASSED"
elif [ $EXIT_CODE -eq 2 ]; then
  echo "⚠️  Validation completed with WARNINGS"
  # Continue deployment but flag for review
else
  echo "❌ Validation FAILED"
  # Block deployment
  exit 1
fi
```

### GitHub Actions Example

```yaml
name: Validate IT DD Automation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run automation
        run: |
          python main_v2.py data/input/ --all --target-name "CloudServe"

      - name: Run validation
        run: |
          FACTS_FILE=$(ls -t output/facts/facts_*.json | head -1)
          python validate_automation.py \
            --facts "$FACTS_FILE" \
            --json-output validation_report.json

      - name: Upload validation report
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: validation_report.json
```

---

## Advanced Usage

### Custom Ground Truth File

If you create a custom ground truth for different test scenarios:

```bash
python validate_automation.py \
  --facts output/facts/facts_CUSTOM.json \
  --ground-truth tests/custom_scenario_ground_truth.md
```

### Filtering by Entity

The script automatically validates both target and buyer entities. To check entity-specific accuracy, use verbose mode:

```bash
python validate_automation.py \
  --facts output/facts/facts_TIMESTAMP.json \
  --verbose
```

This shows target vs buyer breakdowns for each domain.

---

## Updating Ground Truth

When test documents change or expected values need updating:

1. **Edit** `EXPECTED_FACTS_GROUND_TRUTH.md`
2. **Update** the summary table with new expected counts:
   ```markdown
   | Domain | Target Facts Expected | Buyer Facts Expected | Total Expected |
   |---|---:|---:|---:|
   | **ORGANIZATION** | 15 | 9 | 24 |
   ```
3. **Document** changes in the ground truth file header
4. **Re-run validation** to confirm new thresholds

---

## FAQ

### Q: Why does my organization domain show WARNING even though counts are close?

**A:** The validation uses ±10% tolerance. If actual is 26 and expected is 24, that's 108% accuracy, triggering a WARNING (outside 90-110% range but not critical).

**Action:** If consistently outside range, update ground truth or investigate if discovery agent is over-extracting.

---

### Q: What if I don't have a database (CLI-only automation)?

**A:** The script works fine without a database. Just omit `--db` and `--deal-id` arguments. Inventory and findings validation will be skipped, but fact count validation still works.

```bash
python validate_automation.py --facts output/facts/facts_TIMESTAMP.json
```

---

### Q: Can I run validation on partial results (one domain only)?

**A:** Yes! Use `--domain` flag:

```bash
python validate_automation.py \
  --facts output/facts/facts_TIMESTAMP.json \
  --domain organization
```

This validates only the organization domain, useful for focused debugging.

---

### Q: How do I interpret a 0% accuracy for a domain?

**A:** This means the automation extracted 0 facts for that domain (actual = 0, expected > 0). Common causes:
- Domain agent didn't run
- Documents missing for that domain
- Discovery agent crashed silently

**Check:** Automation logs for errors in that specific domain agent.

---

### Q: What's the difference between PASS with 100% and PASS with 95%?

**A:** Both are PASS status (within tolerance). 95% means you extracted 5% fewer facts than expected, which is acceptable. 100% means exact match. Neither is "better" — what matters is PASS vs FAIL.

---

## Next Steps

After running validation:

1. **If PASS:** Automation is working correctly, use for production analysis
2. **If WARNING:** Review specific domains with warnings, consider if acceptable or needs tuning
3. **If FAIL:** Investigate known failure modes, fix root causes, re-run validation

**For known failures:**
- Organization explosion → Fix organization discovery agent
- Entity detection → Fix document preprocessing / entity detection logic
- Missing reasoning → Add Phase 2 (Reasoning) to web app pipeline
- Inventory inflation → Fix UI queries to use InventoryStore not FactStore

---

## Support

**Documentation:**
- Ground truth file: `EXPECTED_FACTS_GROUND_TRUTH.md`
- This guide: `VALIDATION_USAGE_GUIDE.md`
- Audit reports: See conversation history for `/audit1`, `/audit2` outputs

**Common issues:**
- Check automation logs: `output/logs/`
- Check database schema: `web/database.py`
- Check fact structure: `stores/fact_store.py`

---

**Last Updated:** 2026-02-13
**Script Version:** 1.0
**Compatible with:** IT DD Automation v2.4
