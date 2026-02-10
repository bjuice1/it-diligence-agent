# Spec 08: Testing & Deployment
**Version:** 1.0
**Date:** February 10, 2026
**Status:** Ready for Implementation
**Dependencies:** Specs 01-07 (all features to test and deploy)

---

## Executive Summary

This specification defines the **comprehensive testing strategy** and **phased deployment plan** for the Analysis Depth & Explanatory Intelligence Enhancement initiative.

### Scope

**What We're Testing:**
1. ResourceBuildUp data model (Spec 01)
2. ResourceCalculator logic (Spec 02)
3. Resource-Cost integration (Spec 03)
4. Hierarchical breakdown (Spec 04)
5. Explanatory UI enhancement (Spec 05)
6. Fact reasoning expansion (Spec 06)
7. User feedback system (Spec 07)

**Testing Levels:**
- Unit tests (individual functions/components)
- Integration tests (cross-module interactions)
- End-to-end tests (full user workflows)
- Performance tests (load, stress, scalability)
- User acceptance tests (real user validation)

**Deployment Strategy:**
- 4-phase rollout (dev → staging → beta → production)
- Feature flags for gradual enablement
- Rollback procedures for each phase
- Monitoring and alerts

---

## Testing Strategy

### Test Pyramid

```
                  ┌─────────────────┐
                  │   E2E Tests     │  <-- 10% (critical paths)
                  │   (10 tests)    │
                  └─────────────────┘
               ┌──────────────────────┐
               │  Integration Tests   │  <-- 30% (module interactions)
               │    (40 tests)        │
               └──────────────────────┘
          ┌──────────────────────────────┐
          │      Unit Tests              │  <-- 60% (functions/methods)
          │      (100 tests)             │
          └──────────────────────────────┘

Target: 150 total tests
Coverage goal: >80% code coverage
Execution time: <5 minutes (unit), <15 minutes (all)
```

---

## Unit Tests

### Spec 01: ResourceBuildUp Model

**File:** `tests/test_resource_buildup_model.py`

```python
import pytest
from specs.analysis_depth_enhancement.resource_buildup_model import (
    ResourceBuildUp,
    RoleRequirement,
    validate_resource_buildup,
    normalize_skills
)

class TestRoleRequirement:
    """Test RoleRequirement dataclass."""

    def test_effort_calculation(self):
        """Test effort_pm property calculation."""
        role = RoleRequirement(
            id="R1",
            role="Senior Developer",
            fte=2.0,
            duration_months=6.0,
            skills=["Java"],
            seniority="senior"
        )

        assert role.effort_pm == 12.0  # 2.0 FTE × 6 months

    def test_phase_allocation_effort(self):
        """Test effort with phase allocation."""
        role = RoleRequirement(
            id="R2",
            role="QA Engineer",
            fte=1.0,
            duration_months=8.0,
            skills=["Testing"],
            seniority="mid",
            phase_allocation={"planning": 0.25, "execution": 0.75}
        )

        # Total effort still 8 PM, but distributed across phases
        assert role.effort_pm == 8.0

    def test_validation_negative_fte(self):
        """Test validation rejects negative FTE."""
        with pytest.raises(ValueError, match="FTE must be positive"):
            role = RoleRequirement(
                id="R3",
                role="Developer",
                fte=-1.0,
                duration_months=6.0,
                skills=["Python"],
                seniority="junior"
            )

class TestResourceBuildUp:
    """Test ResourceBuildUp dataclass."""

    def test_total_effort_from_roles(self):
        """Test total_effort_pm calculation from roles."""
        rb = ResourceBuildUp(
            id="RB-001",
            workstream="test",
            workstream_display="Test",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[
                RoleRequirement(id="R1", role="Dev", fte=2, duration_months=5, skills=[], seniority="mid"),  # 10 PM
                RoleRequirement(id="R2", role="QA", fte=1, duration_months=3, skills=[], seniority="mid"),   # 3 PM
            ],
            skills_required=[],
            sourcing_mix={},
            assumptions=[],
            source_facts=[],
            confidence=0.8
        )

        assert rb.total_effort_pm == 13.0

    def test_peak_headcount_simple(self):
        """Test peak headcount with concurrent roles."""
        rb = ResourceBuildUp(
            id="RB-002",
            workstream="test",
            workstream_display="Test",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[
                RoleRequirement(id="R1", role="Dev1", fte=2, duration_months=6, skills=[], seniority="mid"),
                RoleRequirement(id="R2", role="Dev2", fte=1, duration_months=6, skills=[], seniority="mid"),
            ],
            skills_required=[],
            sourcing_mix={},
            assumptions=[],
            source_facts=[],
            confidence=0.8
        )

        assert rb.peak_headcount == 3  # 2 + 1

    def test_peak_headcount_with_phases(self):
        """Test peak headcount respects phase allocation."""
        rb = ResourceBuildUp(
            id="RB-003",
            workstream="test",
            workstream_display="Test",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[
                RoleRequirement(
                    id="R1", role="Dev", fte=2, duration_months=6, skills=[], seniority="mid",
                    phase_allocation={"planning": 1.0, "execution": 0.0}  # Only in planning
                ),
                RoleRequirement(
                    id="R2", role="QA", fte=3, duration_months=6, skills=[], seniority="mid",
                    phase_allocation={"planning": 0.0, "execution": 1.0}  # Only in execution
                ),
            ],
            skills_required=[],
            sourcing_mix={},
            assumptions=[],
            source_facts=[],
            confidence=0.8
        )

        # Max is 3 (QA in execution), not 5 (both concurrent)
        assert rb.peak_headcount == 3

    def test_serialization_roundtrip(self):
        """Test to_dict/from_dict roundtrip."""
        original = ResourceBuildUp(
            id="RB-004",
            workstream="application_migration",
            workstream_display="Application Migration",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="medium",
            roles=[
                RoleRequirement(id="R1", role="Dev", fte=1, duration_months=6, skills=["Java"], seniority="senior")
            ],
            skills_required=["Java", "AWS"],
            sourcing_mix={"internal": 0.7, "contractor": 0.3},
            assumptions=["Team available"],
            source_facts=["F-APP-001"],
            confidence=0.85
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        reconstructed = ResourceBuildUp.from_dict(data)

        # Verify
        assert reconstructed.id == original.id
        assert reconstructed.total_effort_pm == original.total_effort_pm
        assert reconstructed.skills_required == original.skills_required

class TestValidation:
    """Test validation functions."""

    def test_validate_sourcing_mix_sum(self):
        """Test sourcing mix must sum to 1.0."""
        rb = ResourceBuildUp(
            id="RB-005",
            workstream="test",
            workstream_display="Test",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[],
            skills_required=[],
            sourcing_mix={"internal": 0.5, "contractor": 0.3},  # Sums to 0.8, not 1.0
            assumptions=[],
            source_facts=[],
            confidence=0.8
        )

        is_valid, errors = validate_resource_buildup(rb)
        assert not is_valid
        assert any("sum to 1.0" in err for err in errors)

    def test_normalize_skills_deduplication(self):
        """Test skill normalization removes duplicates."""
        skills = ["Java", "java", "JAVA", "AWS", "aws"]
        normalized = normalize_skills(skills)

        assert normalized == ["AWS", "Java"]  # Sorted, deduplicated

# ... (50 more unit tests for Spec 01)
```

### Spec 02: ResourceCalculator

**File:** `tests/test_resource_calculator.py`

```python
class TestBenchmarkLibrary:
    """Test effort benchmarks."""

    def test_application_migration_benchmark(self):
        """Test application migration effort benchmarks."""
        from specs.analysis_depth_enhancement.resource_calculation_engine import BenchmarkLibrary, Workstream

        benchmark = BenchmarkLibrary.get_benchmark(Workstream.APPLICATION_MIGRATION)

        assert benchmark.unit_label == "application"
        assert benchmark.effort_simple_pm == 2.0
        assert benchmark.effort_critical_pm == 16.0
        assert sum(benchmark.role_mix.values()) == pytest.approx(1.0)

class TestComplexityFactors:
    """Test complexity multipliers."""

    def test_overall_multiplier_calculation(self):
        """Test geometric mean calculation."""
        from specs.analysis_depth_enhancement.resource_calculation_engine import ComplexityFactors

        factors = ComplexityFactors(
            technology_age=1.3,
            integration_density=1.4,
            documentation_quality=1.0,
            team_experience=1.0,
            timeline_pressure=1.0,
            regulatory_constraints=1.0
        )

        multiplier = factors.calculate_overall_multiplier()

        # Geometric mean should be less than max (1.4)
        assert 1.0 < multiplier < 1.4

class TestResourceCalculator:
    """Test ResourceCalculator end-to-end."""

    def test_calculate_application_migration(self):
        """Test full calculation for application migration."""
        from specs.analysis_depth_enhancement.resource_calculation_engine import (
            ResourceCalculator, Workstream, ComplexityFactors
        )

        # 3 applications in inventory
        inventory_facts = [
            {"id": "F-APP-001", "category": "application", "complexity": "medium"},
            {"id": "F-APP-002", "category": "application", "complexity": "simple"},
            {"id": "F-APP-003", "category": "application", "complexity": "complex"},
        ]

        complexity = ComplexityFactors(
            technology_age=1.2,  # Slightly old tech
            integration_density=1.1,  # Some integrations
            documentation_quality=0.9,  # Good docs (reduce effort)
            team_experience=0.9,  # Experienced team
            timeline_pressure=1.0,
            regulatory_constraints=1.0
        )

        calculator = ResourceCalculator(
            workstream=Workstream.APPLICATION_MIGRATION,
            inventory_facts=inventory_facts,
            complexity_factors=complexity
        )

        result = calculator.calculate()

        # Expected: 2 + 4 + 8 = 14 PM base
        # With complexity multiplier ~1.05, expect ~14.7 PM
        assert 14.0 < result.total_effort_pm < 16.0
        assert len(result.roles) > 0
        assert result.workstream == "application_migration"

# ... (30 more unit tests for Spec 02)
```

---

## Integration Tests

### Spec 03: Resource-Cost Integration

**File:** `tests/test_resource_cost_integration.py`

```python
class TestEndToEndResourceCost:
    """Test resource → cost integration."""

    def test_generate_cost_from_resource(self):
        """Test auto-generating cost from resource."""
        from specs.analysis_depth_enhancement.resource_buildup_model import ResourceBuildUp, RoleRequirement
        from specs.analysis_depth_enhancement.resource_cost_integration import (
            CostFromResourceBuilder, BlendedRateConfig
        )

        # Create resource
        resource = ResourceBuildUp(
            id="RB-INT-001",
            workstream="application_migration",
            workstream_display="Application Migration",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[
                RoleRequirement(
                    id="R1",
                    role="Senior Developer",
                    fte=3.0,
                    duration_months=6.0,
                    skills=["Java", "AWS"],
                    seniority="senior",
                    sourcing_type="internal"
                )
            ],
            skills_required=["Java", "AWS"],
            sourcing_mix={},
            assumptions=["Team available"],
            source_facts=["F-APP-001"],
            confidence=0.85
        )

        # Build cost
        builder = CostFromResourceBuilder(
            resource_buildup=resource,
            rate_config=BlendedRateConfig(),
            geography="onshore",
            non_labor_costs=(50000, 75000)
        )

        cost = builder.build()

        # Verify
        assert cost.derived_from_resource_buildup is True
        assert cost.resource_buildup_id == resource.id
        assert cost.labor_cost_low > 0
        assert cost.cost_low == cost.labor_cost_low + cost.non_labor_cost_low

    def test_consistency_validation(self):
        """Test consistency validation between resource and cost."""
        # ... (test that validator detects mismatches)
        pass

# ... (20 more integration tests)
```

### Spec 04: Hierarchical Breakdown

**File:** `tests/test_hierarchical_breakdown.py`

```python
class TestHierarchyIntegration:
    """Test hierarchy building and aggregation."""

    def test_build_tree_and_aggregate(self):
        """Test full hierarchy: build tree + aggregate values."""
        from specs.analysis_depth_enhancement.hierarchical_breakdown import (
            HierarchyBuilder, ResourceAggregator
        )
        from specs.analysis_depth_enhancement.resource_buildup_model import ResourceBuildUp, RoleRequirement

        # Create parent + children
        parent = ResourceBuildUp(
            id="RB-PARENT",
            workstream="application_migration",
            workstream_display="Application Migration",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[],
            skills_required=[],
            sourcing_mix={},
            assumptions=[],
            source_facts=[],
            confidence=0.8,
            children_ids=["RB-CHILD1", "RB-CHILD2"],
            is_aggregate=True
        )

        child1 = ResourceBuildUp(
            id="RB-CHILD1",
            workstream="application_migration.discovery",
            workstream_display="Discovery",
            duration_months_low=1.0,
            duration_months_high=2.0,
            duration_confidence="high",
            roles=[RoleRequirement(id="R1", role="Architect", fte=1, duration_months=2, skills=[], seniority="senior")],  # 2 PM
            skills_required=[],
            sourcing_mix={},
            assumptions=[],
            source_facts=[],
            confidence=0.8,
            parent_id="RB-PARENT",
            level=2
        )

        child2 = ResourceBuildUp(
            id="RB-CHILD2",
            workstream="application_migration.development",
            workstream_display="Development",
            duration_months_low=4.0,
            duration_months_high=6.0,
            duration_confidence="medium",
            roles=[RoleRequirement(id="R2", role="Developer", fte=3, duration_months=4, skills=[], seniority="mid")],  # 12 PM
            skills_required=[],
            sourcing_mix={},
            assumptions=[],
            source_facts=[],
            confidence=0.75,
            parent_id="RB-PARENT",
            level=2
        )

        # Build tree
        builder = HierarchyBuilder([parent, child1, child2])
        tree = builder.build_tree()

        # Aggregate
        aggregator = ResourceAggregator()
        aggregator.aggregate(tree)

        # Verify parent aggregated from children
        assert parent.aggregated_effort_pm == 14.0  # 2 + 12
        assert parent.aggregated_peak_headcount == 3  # Max of 1 and 3

# ... (10 more integration tests)
```

---

## End-to-End Tests

**File:** `tests/e2e/test_complete_workflows.py`

```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestCompleteUserWorkflow:
    """E2E tests simulating real user interactions."""

    @pytest.fixture
    def browser(self):
        """Setup browser for E2E tests."""
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    def test_view_finding_with_calculation(self, browser):
        """
        E2E: User views finding → clicks "View Calculation" → sees breakdown.
        """
        # Login
        browser.get("http://localhost:5001/login")
        browser.find_element(By.ID, "email").send_keys("test@example.com")
        browser.find_element(By.ID, "password").send_keys("testpass")
        browser.find_element(By.ID, "login-btn").click()

        # Navigate to deal
        browser.get("http://localhost:5001/deals/DEAL-001/findings")

        # Wait for findings to load
        finding_card = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "finding-card"))
        )

        # Click "View Calculation"
        calc_button = finding_card.find_element(By.LINK_TEXT, "View Calculation ▶")
        calc_button.click()

        # Wait for modal to appear
        modal = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "calculation-modal"))
        )

        # Verify cost breakdown is visible
        cost_breakdown = modal.find_element(By.CLASS_NAME, "cost-breakdown-view")
        assert cost_breakdown.is_displayed()

        # Verify total cost is shown
        total_cost = modal.find_element(By.CLASS_NAME, "cost-summary")
        assert "$" in total_cost.text

    def test_submit_feedback(self, browser):
        """
        E2E: User submits feedback via widget.
        """
        # Login
        browser.get("http://localhost:5001/login")
        browser.find_element(By.ID, "email").send_keys("test@example.com")
        browser.find_element(By.ID, "password").send_keys("testpass")
        browser.find_element(By.ID, "login-btn").click()

        # Click feedback button
        feedback_btn = browser.find_element(By.CLASS_NAME, "feedback-button")
        feedback_btn.click()

        # Fill form
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.ID, "feedback-title"))
        )

        browser.find_element(By.ID, "feedback-category").send_keys("Improvement")
        browser.find_element(By.ID, "feedback-title").send_keys("Test Feedback")
        browser.find_element(By.ID, "feedback-description").send_keys("This is a test feedback submission.")

        # Submit
        browser.find_element(By.ID, "feedback-submit-btn").click()

        # Verify success message
        success_msg = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )
        assert "Thank you" in success_msg.text

# ... (8 more E2E tests covering critical paths)
```

---

## Performance Tests

**File:** `tests/performance/test_load.py`

```python
import time
from locust import HttpUser, task, between

class DealAnalysisUser(HttpUser):
    """Simulate user analyzing deals."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Login before tasks."""
        self.client.post("/login", {
            "email": "loadtest@example.com",
            "password": "testpass"
        })

    @task(3)
    def view_findings(self):
        """View findings page (most common action)."""
        self.client.get("/deals/DEAL-001/findings")

    @task(2)
    def view_calculation(self):
        """View calculation breakdown."""
        self.client.get("/api/findings/FND-001")

    @task(1)
    def submit_feedback(self):
        """Submit feedback."""
        self.client.post("/api/feedback/submit", {
            "category": "improvement",
            "title": "Load test feedback",
            "description": "Testing system under load"
        })

# Run with: locust -f tests/performance/test_load.py --users 50 --spawn-rate 5
```

**Performance Targets:**
- 50 concurrent users
- 95th percentile response time: <500ms for findings page
- 95th percentile response time: <200ms for API endpoints
- No errors under sustained load (10 minutes)

---

## Test Automation

### CI/CD Pipeline

**File:** `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: |
          pytest tests/test_*.py -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run migrations
        run: flask db upgrade
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost/test

      - name: Run integration tests
        run: pytest tests/integration/ -v

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install selenium

      - name: Start application
        run: |
          flask run &
          sleep 10

      - name: Run E2E tests
        run: pytest tests/e2e/ -v
```

---

## Deployment Strategy

### Phase 1: Development Environment

**Timeline:** Week 1-2 (already in progress during spec writing)

**Actions:**
- Deploy all features to dev environment
- Run full test suite
- Manual exploratory testing
- Fix critical bugs

**Success Criteria:**
- All tests passing
- No P0 bugs
- Code review completed

---

### Phase 2: Staging Environment

**Timeline:** Week 3

**Actions:**
1. **Deploy to staging**
   ```bash
   git checkout develop
   git pull origin develop
   git tag v2.0.0-staging
   git push --tags

   # Deploy via CI/CD or manual
   ./deploy.sh staging
   ```

2. **Run smoke tests**
   - Verify all pages load
   - Test critical workflows
   - Check database migrations

3. **Load testing**
   ```bash
   locust -f tests/performance/test_load.py \
     --host https://staging.example.com \
     --users 50 \
     --spawn-rate 5 \
     --run-time 10m
   ```

4. **Data migration test**
   - Backup production database
   - Restore to staging
   - Run migrations
   - Verify data integrity

**Success Criteria:**
- All smoke tests pass
- Performance targets met
- No data migration errors
- Security scan clean

---

### Phase 3: Beta Rollout

**Timeline:** Week 4

**Feature Flags Setup:**

```python
# web/feature_flags.py
class FeatureFlags:
    """Feature flags for gradual rollout."""

    @staticmethod
    def is_enabled(feature_name: str, user_id: str = None, deal_id: str = None) -> bool:
        """Check if feature is enabled for user/deal."""

        # Check database for feature flag
        flag = FeatureFlag.query.filter_by(name=feature_name).first()

        if not flag or not flag.enabled:
            return False

        # Rollout percentage
        if flag.rollout_percentage < 100:
            # Hash user_id to deterministic 0-100
            import hashlib
            hash_input = f"{feature_name}:{user_id or deal_id or ''}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            bucket = hash_value % 100

            if bucket >= flag.rollout_percentage:
                return False

        return True

# Usage in code:
if FeatureFlags.is_enabled("resource_buildup", user_id=current_user.id):
    # Show new ResourceBuildUp features
    pass
else:
    # Show old version
    pass
```

**Beta Cohorts:**
- Week 4 Day 1-2: Internal team (10% rollout)
- Week 4 Day 3-4: Power users (25% rollout)
- Week 4 Day 5-7: All beta participants (50% rollout)

**Monitoring:**
- Error rate < 0.5%
- Page load time < 2s (p95)
- User feedback score > 4.0/5.0

**Rollback Plan:**
```bash
# If critical issue detected:
# 1. Disable feature flag
UPDATE feature_flags SET enabled = false WHERE name = 'resource_buildup';

# 2. If database migration issue:
flask db downgrade -1  # Revert last migration

# 3. If full rollback needed:
git revert <commit-hash>
git push origin main
./deploy.sh production
```

---

### Phase 4: Production Rollout

**Timeline:** Week 5

**Rollout Schedule:**
- Day 1: 10% of users
- Day 2: 25% of users
- Day 3: 50% of users
- Day 4: 75% of users
- Day 5: 100% of users

**Go/No-Go Checklist:**
- [ ] All beta feedback addressed
- [ ] Error rate < 0.1% in beta
- [ ] Performance targets met
- [ ] Load testing passed (200 concurrent users)
- [ ] Rollback procedure tested
- [ ] Monitoring dashboards configured
- [ ] Support team trained
- [ ] User documentation published

**Deployment Steps:**

```bash
# 1. Final code freeze
git checkout main
git merge develop
git tag v2.0.0
git push --tags

# 2. Database backup
pg_dump $DATABASE_URL > backup_pre_v2.0.0.sql

# 3. Run migrations
flask db upgrade

# 4. Deploy application
./deploy.sh production

# 5. Enable feature flag (10% rollout)
UPDATE feature_flags
SET enabled = true, rollout_percentage = 10
WHERE name = 'resource_buildup';

# 6. Monitor for 4 hours

# 7. Gradually increase rollout
# Day 2: 25%, Day 3: 50%, etc.
```

**Monitoring Dashboards:**

```python
# web/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Counters
resource_buildup_generated = Counter(
    'resource_buildup_generated_total',
    'Total ResourceBuildUp instances generated'
)

cost_from_resource_generated = Counter(
    'cost_from_resource_generated_total',
    'Total CostBuildUp instances auto-generated from resources'
)

# Histograms
resource_calculation_duration = Histogram(
    'resource_calculation_duration_seconds',
    'Time to calculate ResourceBuildUp'
)

# Gauges
active_features = Gauge(
    'active_features',
    'Number of features currently enabled',
    ['feature_name']
)
```

**Alerts:**

```yaml
# prometheus/alerts.yml
groups:
  - name: resource_buildup
    rules:
      - alert: HighResourceCalculationLatency
        expr: resource_calculation_duration_seconds{quantile="0.95"} > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Resource calculation taking >1s (p95)"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status="500"}[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Error rate >1%"
```

---

## Documentation

### User-Facing Documentation

**File:** `docs/user-guide/resource-buildup.md`

```markdown
# Resource & Cost Transparency Guide

## Overview

The IT Diligence Agent now provides complete transparency into:
- **Resource estimates** (how many people, what skills, how long)
- **Cost breakdowns** (labor vs non-labor, role-by-role)
- **Calculation formulas** (see exactly how numbers are derived)

## Viewing Resource Estimates

1. Navigate to a finding with cost estimates
2. Click **"View Calculation"**
3. Select the **"Resource Estimate"** tab

You'll see:
- Total effort in person-months
- Peak team size
- Role breakdown (PM, developers, QA, etc.)
- Skills required
- Sourcing mix (internal, contractor, vendor)

## Understanding Cost Breakdowns

Click **"Cost Estimate"** tab to see:
- Total cost range
- Labor costs (with blended rate)
- Non-labor costs (tools, licenses, infrastructure)
- Assumptions made in the estimate

## Drilling Down

For hierarchical breakdowns:
1. Click the **▼** arrow next to a workstream
2. See sub-tasks and their individual estimates
3. Click any sub-task to view its detailed breakdown

## Providing Feedback

Found an issue or have a suggestion?
1. Click the **💬 Feedback** button (bottom-right)
2. Describe what you'd like to see improved
3. We'll notify you when it's addressed!
```

### Developer Documentation

**File:** `docs/developer/resource-buildup-api.md`

```markdown
# ResourceBuildUp API Reference

## Overview

The ResourceBuildUp framework provides programmatic resource estimation
and cost derivation for M&A IT due diligence.

## Creating a ResourceBuildUp

```python
from specs.analysis_depth_enhancement.resource_buildup_model import (
    ResourceBuildUp, RoleRequirement
)

resource = ResourceBuildUp(
    workstream="application_migration",
    workstream_display="Application Migration",
    duration_months_low=6.0,
    duration_months_high=8.0,
    duration_confidence="medium",
    roles=[
        RoleRequirement(
            role="Senior Developer",
            fte=3.0,
            duration_months=6.0,
            skills=["Java", "AWS"],
            seniority="senior",
            sourcing_type="internal"
        )
    ],
    # ... other fields
)
```

## Auto-Generating from Inventory

```python
from specs.analysis_depth_enhancement.resource_calculation_engine import (
    ResourceCalculator, Workstream
)

calculator = ResourceCalculator(
    workstream=Workstream.APPLICATION_MIGRATION,
    inventory_facts=app_inventory_facts,
    complexity_factors=ComplexityFactors(technology_age=1.2)
)

resource = calculator.calculate()
```

## Generating Costs from Resources

```python
from specs.analysis_depth_enhancement.resource_cost_integration import (
    CostFromResourceBuilder
)

builder = CostFromResourceBuilder(
    resource_buildup=resource,
    non_labor_costs=(50000, 75000)
)

cost = builder.build()
```

See full API docs for all methods and options.
```

---

## Post-Deployment

### Week 1 After Launch

**Daily Monitoring:**
- Check error rates (target: <0.1%)
- Review user feedback submissions
- Monitor performance metrics
- Check feature flag rollout progress

**Weekly Report:**
- Total users on new features: X%
- Error count: Y
- User feedback: Z submissions (W positive, V negative)
- Performance: p95 response time = Nms

### Month 1 After Launch

**User Acceptance Survey:**
```
1. Does the analysis provide sufficient context? (Yes/No/Somewhat)
2. Can you understand where cost estimates come from? (Yes/No/Somewhat)
3. Is the resource breakdown helpful? (Yes/No/Somewhat)
4. Rate the new features: (1-5 stars)
5. What would you improve?
```

**Target:** >80% positive responses on Q1-3, >4.0 avg rating on Q4

### Continuous Improvement

**Feedback Loop:**
1. Review feedback dashboard weekly
2. Prioritize top-voted items
3. Plan fixes/enhancements in next sprint
4. Notify users when feedback addressed
5. Measure impact (did it solve the problem?)

---

## Success Metrics

### Technical Metrics

✅ **Deployment successful when:**
- [ ] Code coverage >80%
- [ ] All tests passing (unit, integration, E2E)
- [ ] Zero P0 bugs in production
- [ ] Performance targets met (p95 < 500ms)
- [ ] Error rate < 0.1%
- [ ] 100% rollout achieved

### User Metrics

✅ **User adoption successful when:**
- [ ] >60% of users click "View Calculation" at least once
- [ ] >40% of users submit feedback
- [ ] "Need more context" complaints drop >75%
- [ ] User satisfaction survey: >80% positive
- [ ] NPS score improves by >10 points

### Business Metrics

✅ **Business impact achieved when:**
- [ ] Deal analysis time reduced by >20%
- [ ] Cost estimate accuracy improves (vs actuals)
- [ ] Resource planning adopted by PM teams
- [ ] Feedback-driven improvements shipped monthly

---

## Document Status

**Status:** ✅ Ready for Implementation
**Dependencies:** Specs 01-07 (all features)
**Next Steps:** Begin execution - start with Phase 1 development

**Author:** Claude Sonnet 4.5
**Date:** February 10, 2026
**Version:** 1.0
