# CI/CD Integration for Test Validation

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document specifies how to integrate the test validation framework into CI/CD pipelines. Automated validation ensures that pipeline improvements don't introduce regressions and that golden fixtures remain accurate as the codebase evolves.

**Purpose:** Enable continuous validation of IT DD pipeline accuracy through automated testing in GitHub Actions.

**Scope:** GitHub Actions workflows, pytest integration, fixture validation hooks, PR checks, nightly regression tests.

---

## Architecture

### CI/CD Workflow Structure

```
GitHub Actions Workflows
├── pull-request.yml          ← Run on every PR
│   ├── Unit tests (fast)
│   ├── Golden fixture schema validation
│   └── Validation tests (CloudServe only)
│
├── nightly-regression.yml    ← Run daily at 2 AM UTC
│   ├── Full validation suite (all deals)
│   ├── Performance benchmarks
│   └── Cost accuracy trending
│
└── fixture-update.yml        ← Run when fixtures change
    ├── Schema validation
    ├── Cross-reference checks
    └── Fixture diff report

Pre-commit Hooks (Local)
├── pytest tests/unit/test_assertions.py
├── jsonschema validation on changed fixtures
└── Fixture version bump check
```

---

## Specification

### 1. Pull Request Workflow

**File:** `.github/workflows/pull-request.yml`

**Purpose:** Fast feedback on every PR - catch regressions early.

**Configuration:**

```yaml
name: Pull Request Validation

on:
  pull_request:
    branches: [main, develop]
    paths:
      - 'agents_v2/**'
      - 'stores/**'
      - 'services/**'
      - 'tests/**'
      - 'specs/test-validation/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov jsonschema

      - name: Run unit tests
        run: |
          cd "9.5/it-diligence-agent 2"
          pytest tests/unit/ -v --cov=stores --cov=agents_v2 --cov=services

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml

  fixture-validation:
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Validate golden fixtures against schema
        run: |
          cd "9.5/it-diligence-agent 2"
          pip install jsonschema

          # Validate all fixtures
          for fixture in tests/golden/*_expected.json; do
            echo "Validating $fixture..."
            jsonschema -i "$fixture" tests/golden/fixture_schema.json
          done

      - name: Check fixture versions
        run: |
          cd "9.5/it-diligence-agent 2"
          python tests/scripts/check_fixture_versions.py

  cloudserve-validation:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    needs: [unit-tests, fixture-validation]

    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd "9.5/it-diligence-agent 2"
          pip install -r requirements.txt

      - name: Run CloudServe validation test
        run: |
          cd "9.5/it-diligence-agent 2"
          pytest tests/validation/test_cloudserve_accuracy.py -v --tb=short

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: cloudserve-validation-report
          path: tests/reports/cloudserve_validation_*.html
```

**Triggers:**
- Every pull request to `main` or `develop`
- Only if relevant paths modified (agents, stores, services, tests)

**Runtime:** ~10-15 minutes total (runs in parallel)

**Pass Criteria:**
- All unit tests pass
- All fixtures validate against schema
- CloudServe validation test passes

---

### 2. Nightly Regression Workflow

**File:** `.github/workflows/nightly-regression.yml`

**Purpose:** Comprehensive validation across all deals, detect drift over time.

**Configuration:**

```yaml
name: Nightly Regression Suite

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
  workflow_dispatch:      # Manual trigger

jobs:
  full-validation-suite:
    runs-on: ubuntu-latest
    timeout-minutes: 60

    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

    strategy:
      matrix:
        deal: [cloudserve, great_insurance]
      fail-fast: false  # Run all deals even if one fails

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd "9.5/it-diligence-agent 2"
          pip install -r requirements.txt

      - name: Run full pipeline on ${{ matrix.deal }}
        run: |
          cd "9.5/it-diligence-agent 2"
          python main_v2.py data/input/ --all --target-name "${{ matrix.deal }}" --narrative

      - name: Run validation tests
        run: |
          cd "9.5/it-diligence-agent 2"
          pytest tests/validation/test_${{ matrix.deal }}_accuracy.py -v --tb=short

      - name: Generate accuracy trending data
        run: |
          cd "9.5/it-diligence-agent 2"
          python tests/scripts/generate_accuracy_trends.py ${{ matrix.deal }}

      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: validation-report-${{ matrix.deal }}
          path: |
            tests/reports/${{ matrix.deal }}_validation_*.html
            tests/reports/trends_*.json

  performance-benchmarks:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    needs: full-validation-suite

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd "9.5/it-diligence-agent 2"
          pip install -r requirements.txt
          pip install pytest-benchmark

      - name: Run performance benchmarks
        run: |
          cd "9.5/it-diligence-agent 2"
          pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark_results.json

      - name: Compare against baseline
        run: |
          cd "9.5/it-diligence-agent 2"
          python tests/scripts/compare_benchmarks.py benchmark_results.json tests/benchmarks/baseline.json

  notify-on-failure:
    runs-on: ubuntu-latest
    needs: [full-validation-suite, performance-benchmarks]
    if: failure()

    steps:
      - name: Send Slack notification
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "⚠️ Nightly regression tests FAILED",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Nightly Regression Suite Failed*\n\nCheck GitHub Actions for details:\n${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

**Triggers:**
- Scheduled: Daily at 2 AM UTC
- Manual: Via GitHub Actions UI

**Runtime:** ~60 minutes (runs all deals in parallel)

**Outputs:**
- Validation reports per deal
- Accuracy trending JSON
- Performance benchmark comparisons
- Slack notification on failure

---

### 3. Fixture Update Workflow

**File:** `.github/workflows/fixture-update.yml`

**Purpose:** Extra validation when golden fixtures are modified.

**Configuration:**

```yaml
name: Fixture Update Validation

on:
  pull_request:
    paths:
      - 'tests/golden/*.json'
      - 'tests/golden/fixture_schema.json'

jobs:
  fixture-diff-report:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2  # Need previous commit for diff

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Generate fixture diff
        run: |
          cd "9.5/it-diligence-agent 2"
          pip install deepdiff
          python tests/scripts/generate_fixture_diff.py > fixture_diff_report.md

      - name: Post diff as PR comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const diff = fs.readFileSync('fixture_diff_report.md', 'utf8');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🔍 Golden Fixture Changes Detected\n\n${diff}`
            });

      - name: Check version bumps
        run: |
          cd "9.5/it-diligence-agent 2"
          python tests/scripts/check_fixture_versions.py --require-bump

      - name: Validate updated fixtures
        run: |
          cd "9.5/it-diligence-agent 2"
          pip install jsonschema

          # Get list of changed fixtures
          git diff --name-only HEAD^ HEAD | grep 'tests/golden/.*\.json' | while read fixture; do
            echo "Validating $fixture..."
            jsonschema -i "$fixture" tests/golden/fixture_schema.json
          done

      - name: Run affected validation tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd "9.5/it-diligence-agent 2"
          pip install -r requirements.txt

          # Extract deal name from changed fixture
          git diff --name-only HEAD^ HEAD | grep 'tests/golden/.*_expected\.json' | while read fixture; do
            deal_name=$(basename "$fixture" | sed 's/_expected\.json//')
            echo "Running validation test for $deal_name..."
            pytest tests/validation/test_${deal_name}_accuracy.py -v
          done
```

**Triggers:**
- Pull requests that modify `tests/golden/*.json`

**Actions:**
- Generate human-readable diff of fixture changes
- Post diff as PR comment for review
- Verify version numbers were bumped
- Validate updated fixtures against schema
- Run validation tests for affected deals

---

### 4. Pre-commit Hooks (Local Development)

**File:** `.pre-commit-config.yaml`

**Purpose:** Fast local checks before code is pushed.

**Configuration:**

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: bash -c 'cd "9.5/it-diligence-agent 2" && pytest tests/unit/test_assertions.py -v'
        language: system
        pass_filenames: false
        stages: [commit]

      - id: validate-fixtures
        name: Validate golden fixtures
        entry: bash -c 'cd "9.5/it-diligence-agent 2" && for f in tests/golden/*_expected.json; do jsonschema -i "$f" tests/golden/fixture_schema.json || exit 1; done'
        language: system
        files: 'tests/golden/.*\.json$'
        pass_filenames: false

      - id: check-fixture-version
        name: Check fixture version bump
        entry: bash -c 'cd "9.5/it-diligence-agent 2" && python tests/scripts/check_fixture_versions.py --require-bump'
        language: system
        files: 'tests/golden/.*_expected\.json$'
        pass_filenames: false

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-json
        files: 'tests/golden/.*\.json$'
      - id: check-yaml
      - id: trailing-whitespace
      - id: end-of-file-fixer
```

**Installation:**

```bash
pip install pre-commit
cd "9.5/it-diligence-agent 2"
pre-commit install
```

**Runtime:** ~30 seconds (only runs affected hooks)

---

### 5. Helper Scripts

**File:** `tests/scripts/check_fixture_versions.py`

**Purpose:** Ensure fixture versions are bumped when content changes.

```python
#!/usr/bin/env python3
"""
Check that fixture versions are bumped when content changes.
"""
import json
import sys
import subprocess
from pathlib import Path

def get_changed_fixtures():
    """Get list of changed fixture files from git."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD^", "HEAD"],
        capture_output=True,
        text=True
    )

    return [
        line for line in result.stdout.split('\n')
        if line.endswith('_expected.json')
    ]

def check_version_bump(fixture_path: Path, require_bump: bool = False):
    """Check if version was bumped in this commit."""
    # Get current version
    current = json.loads(fixture_path.read_text())
    current_version = current.get("metadata", {}).get("version", "0.0.0")

    # Get previous version
    result = subprocess.run(
        ["git", "show", f"HEAD^:{fixture_path}"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        # New file, version check passes
        return True

    previous = json.loads(result.stdout)
    previous_version = previous.get("metadata", {}).get("version", "0.0.0")

    if require_bump and current_version == previous_version:
        print(f"❌ {fixture_path}: Version not bumped (still {current_version})")
        return False

    print(f"✓ {fixture_path}: Version {previous_version} → {current_version}")
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-bump", action="store_true")
    args = parser.parse_args()

    changed_fixtures = get_changed_fixtures()

    if not changed_fixtures:
        print("No fixture changes detected")
        return 0

    all_passed = True
    for fixture_path in changed_fixtures:
        if not check_version_bump(Path(fixture_path), args.require_bump):
            all_passed = False

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
```

---

**File:** `tests/scripts/generate_fixture_diff.py`

**Purpose:** Generate human-readable diff of fixture changes.

```python
#!/usr/bin/env python3
"""
Generate markdown diff report for fixture changes.
"""
import json
import subprocess
from pathlib import Path
from deepdiff import DeepDiff

def get_changed_fixtures():
    """Get list of changed fixture files."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD^", "HEAD"],
        capture_output=True,
        text=True
    )

    return [
        line for line in result.stdout.split('\n')
        if line.endswith('_expected.json')
    ]

def generate_diff_report(fixture_path: Path):
    """Generate diff for a single fixture."""
    # Get current version
    current = json.loads(fixture_path.read_text())

    # Get previous version
    result = subprocess.run(
        ["git", "show", f"HEAD^:{fixture_path}"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return f"### {fixture_path.name}\n\n**New fixture created**\n"

    previous = json.loads(result.stdout)

    # Calculate diff
    diff = DeepDiff(previous, current, ignore_order=True)

    report = f"### {fixture_path.name}\n\n"

    if "values_changed" in diff:
        report += "**Values Changed:**\n\n"
        for key, change in diff["values_changed"].items():
            report += f"- `{key}`: `{change['old_value']}` → `{change['new_value']}`\n"
        report += "\n"

    if "iterable_item_added" in diff:
        report += "**Items Added:**\n\n"
        for item in diff["iterable_item_added"].values():
            report += f"- {item}\n"
        report += "\n"

    if "iterable_item_removed" in diff:
        report += "**Items Removed:**\n\n"
        for item in diff["iterable_item_removed"].values():
            report += f"- {item}\n"
        report += "\n"

    return report

def main():
    changed_fixtures = get_changed_fixtures()

    if not changed_fixtures:
        print("No fixture changes detected.")
        return

    print(f"# Golden Fixture Changes\n\n")
    print(f"**Files Modified:** {len(changed_fixtures)}\n\n")

    for fixture_path in changed_fixtures:
        print(generate_diff_report(Path(fixture_path)))

if __name__ == "__main__":
    main()
```

---

## Verification Strategy

### Manual Testing

**Test: Trigger PR workflow**

1. Create branch: `git checkout -b test/ci-validation`
2. Modify fixture: `tests/golden/cloudserve_expected.json` (change app count)
3. Push: `git push origin test/ci-validation`
4. Open PR
5. Verify workflow runs and fails (intentional failure)
6. Revert change, verify workflow passes

**Expected:** Workflow detects fixture change, runs validation, reports failure.

---

**Test: Trigger nightly regression manually**

1. Go to GitHub Actions → Nightly Regression Suite
2. Click "Run workflow"
3. Wait ~60 minutes
4. Verify all deals validated, reports uploaded

**Expected:** All validation tests pass, reports generated, no Slack notification.

---

### Automated Checks

**Test: Pre-commit hook**

```bash
# Install pre-commit
pip install pre-commit
cd "9.5/it-diligence-agent 2"
pre-commit install

# Modify fixture
vim tests/golden/cloudserve_expected.json  # Change a value without bumping version

# Try to commit
git add tests/golden/cloudserve_expected.json
git commit -m "Test pre-commit hook"

# Expected: Commit blocked, version bump required
```

---

## Benefits

### Why CI/CD Integration

1. **Early Detection:** Catch regressions in PRs before merge
2. **Confidence:** Know every commit passes validation
3. **Trending:** Track accuracy over time with nightly runs
4. **Documentation:** Fixture diffs provide clear change history

### Why Pre-commit Hooks

1. **Fast Feedback:** Validation in <30 seconds locally
2. **Prevents Broken Commits:** Can't push invalid fixtures
3. **Developer Experience:** Catch issues before CI runs

---

## Expectations

### Success Metrics

1. **PR pass rate:** >95% of PRs pass validation on first run
2. **Nightly stability:** <1 false failure per month
3. **Developer adoption:** >80% use pre-commit hooks
4. **CI runtime:** PR workflow <15 minutes, nightly <60 minutes

### Acceptance Criteria

- Pull request workflow implemented and tested
- Nightly regression workflow running daily
- Fixture update workflow posting diff reports
- Pre-commit hooks installable and functional
- All helper scripts tested and documented

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **API costs too high:** Nightly runs use real LLM calls | Use matrix strategy to control parallelism, cache fixtures where possible |
| **Flaky tests:** Non-deterministic LLM outputs cause failures | Use tolerance-based assertions, re-run failed tests once |
| **Slow CI:** Developers bypass checks | Optimize PR workflow (<15 min), make pre-commit hooks fast (<30s) |
| **Fixture drift:** Old fixtures become stale | Nightly runs detect drift, quarterly fixture refresh process |

---

## Results Criteria

- Pull request workflow defined in `.github/workflows/pull-request.yml`
- Nightly regression workflow in `.github/workflows/nightly-regression.yml`
- Fixture update workflow in `.github/workflows/fixture-update.yml`
- Pre-commit config in `.pre-commit-config.yaml`
- Helper scripts in `tests/scripts/` (check_fixture_versions.py, generate_fixture_diff.py)
- All workflows tested and passing

---

## Cross-References

- **01-test-validation-architecture.md:** Test runner integration points
- **02-golden-fixture-schema.md:** Schema validation in CI
- **03-validation-assertions.md:** Assertions used in CI tests
- **04-test-data-documentation.md:** Fixture versioning and maintenance
- **06-migration-rollout.md:** Phased CI enablement during rollout
