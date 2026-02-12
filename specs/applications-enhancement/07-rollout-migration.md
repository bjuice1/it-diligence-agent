# Rollout & Migration

**Status:** Specification
**Created:** 2026-02-11
**Depends On:** 00-overview-applications-enhancement.md, 04-cost-engine-inventory-integration.md, 06-testing-validation.md
**Estimated Scope:** 2-3 hours

---

## Overview

**Purpose:** Define safe rollout strategy for applications enhancement with feature flags, backward compatibility, cost recalculation options, and rollback procedures.

**Key Principles:**
- **No breaking changes** - Existing functionality continues to work
- **Gradual rollout** - Enable for new deals first, then migrate existing
- **Instant rollback** - Feature flag allows immediate disable if issues arise
- **Transparent migration** - Users understand what changed and why

---

## Rollout Strategy

### Phase 1: Code Deployment (Feature Flag OFF)

**Timeline:** Day 1
**Risk:** Low (no behavior change)

```bash
# Deploy code with feature flag disabled by default
export APPLICATION_INVENTORY_COSTING=false
export DEAL_TYPE_AWARENESS=true  # Keep existing feature enabled

# Deploy to production
git push production main
```

**Validation:**
- [ ] All existing tests pass (572 baseline + 89 new)
- [ ] No regression in UI/API performance
- [ ] Feature flags visible in admin panel
- [ ] Logs show "Feature disabled" messages

### Phase 2: Enable for New Deals Only

**Timeline:** Days 2-7 (monitor closely)
**Risk:** Medium (affects new data only)

**Configuration:**

```python
# config_v2.py

# Enable for new deals created after cutoff date
APPLICATION_INVENTORY_COSTING_ENABLED = (
    os.getenv('APPLICATION_INVENTORY_COSTING', 'false').lower() == 'true'
)

# Cutoff: deals created before this date use legacy costing
INVENTORY_COSTING_CUTOFF_DATE = datetime(2026, 2, 15)  # Deployment date

def should_use_inventory_costing(deal: Deal) -> bool:
    """Determine if deal should use inventory-based costing."""
    if not APPLICATION_INVENTORY_COSTING_ENABLED:
        return False

    # New deals use new costing
    if deal.created_at >= INVENTORY_COSTING_CUTOFF_DATE:
        return True

    # Existing deals opt-in via flag
    return deal.use_inventory_costing
```

**Enable feature flag:**

```bash
export APPLICATION_INVENTORY_COSTING=true
# Restart application
```

**Monitoring (Days 2-7):**

```python
# Add telemetry
logger.info(
    "Cost calculation method",
    extra={
        'deal_id': deal.id,
        'method': 'inventory' if use_inventory else 'count',
        'app_count': len(apps),
        'total_cost': cost_summary.grand_total,
        'calculation_time_ms': elapsed_ms
    }
)
```

**Watch for:**
- Cost calculation errors (should be 0)
- Performance degradation (>2x slower)
- Cost estimates >3x different from historical
- User-reported issues

**Success criteria:**
- [ ] 10+ new deals processed successfully
- [ ] Zero cost calculation errors
- [ ] Performance <5s for 100 apps
- [ ] User feedback positive (surveyed)

### Phase 3: Migrate Existing Deals (Opt-In)

**Timeline:** Days 8-21 (gradual)
**Risk:** Medium (affects existing data)

**UI Option for Deal Owners:**

```html
<!-- web/templates/deal_detail.html -->
<div class="card">
    <div class="card-header">
        <h5>Cost Calculation Method</h5>
    </div>
    <div class="card-body">
        <p>
            <strong>Current method:</strong>
            {{ 'Inventory-based (enhanced)' if deal.use_inventory_costing else 'Count-based (legacy)' }}
        </p>

        {% if not deal.use_inventory_costing %}
        <div class="alert alert-info">
            <h6>✨ New: Enhanced Application Costing</h6>
            <p>
                Recalculate costs using enhanced model with:
            </p>
            <ul>
                <li>Complexity tiers (simple vs critical apps)</li>
                <li>Category-based multipliers (ERP vs collaboration)</li>
                <li>Deployment type awareness (SaaS vs on-prem)</li>
                <li>Integration costs (APIs, SSO, data migration)</li>
            </ul>
            <p class="mb-0">
                <button class="btn btn-primary" onclick="recalculateCosts()">
                    Recalculate with Enhanced Model
                </button>
                <a href="/docs/applications-enhancement" class="btn btn-link">
                    Learn More
                </a>
            </p>
        </div>
        {% endif %}
    </div>
</div>
```

**Backend recalculation:**

```python
# web/blueprints/costs.py

@bp.route('/deals/<deal_id>/recalculate-costs', methods=['POST'])
@login_required
def recalculate_costs(deal_id: str):
    """Recalculate deal costs using inventory-based method."""
    deal = Deal.query.get_or_404(deal_id)

    # Permission check
    if not current_user.can_edit_deal(deal):
        abort(403)

    # Get inventory store
    inv_store = get_inventory_store_for_deal(deal_id)

    if not inv_store or inv_store.get_item_count() == 0:
        flash('No inventory data available for recalculation', 'warning')
        return redirect(url_for('deals.view', deal_id=deal_id))

    try:
        # Recalculate costs using inventory
        cost_summary = calculate_application_costs_from_inventory(
            inv_store,
            deal_type=deal.deal_type,
            entity='target'
        )

        # Store old costs for comparison
        old_total = deal.total_application_cost or 0

        # Update deal
        deal.total_application_cost = cost_summary.grand_total
        deal.use_inventory_costing = True
        deal.cost_recalculated_at = datetime.utcnow()
        deal.cost_recalculated_by = current_user.id

        db.session.commit()

        # Show comparison
        delta = cost_summary.grand_total - old_total
        delta_pct = (delta / old_total * 100) if old_total > 0 else 0

        flash(
            f'Costs recalculated: ${cost_summary.grand_total:,.0f} '
            f'({"+" if delta > 0 else ""}{delta_pct:+.1f}% vs legacy)',
            'success'
        )

        # Log for audit
        logger.info(
            f"Cost recalculation: deal={deal_id}, "
            f"old={old_total}, new={cost_summary.grand_total}, "
            f"delta={delta}, user={current_user.email}"
        )

        return redirect(url_for('deals.view', deal_id=deal_id))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Cost recalculation failed: {e}", exc_info=True)
        flash(f'Recalculation failed: {str(e)}', 'danger')
        return redirect(url_for('deals.view', deal_id=deal_id))
```

**Migration Workflow:**

1. **Deal owner clicks "Recalculate"**
2. **System validates inventory exists**
3. **Calculate new costs using inventory method**
4. **Show comparison (old vs new)**
5. **User confirms or cancels**
6. **Update deal costs + set flag**

**Gradual Migration Plan:**

```markdown
# Existing Deal Migration Schedule

## Week 1 (Days 8-14)
- Migrate 10 pilot deals (hand-picked, recent, good data quality)
- Monitor for issues
- Collect user feedback

## Week 2 (Days 15-21)
- Migrate 50 more deals (medium priority)
- Validate cost variance acceptable (<±30%)
- Adjust multipliers if systematic bias detected

## Week 3 (Days 22-28)
- Open to all users (self-service recalculation)
- Email notification: "Enhanced costing now available"
- Support team trained on differences

## Week 4+ (Days 29+)
- Monitor adoption rate
- Follow up with non-adopters
- Consider making default for all deals (Phase 4)
```

### Phase 4: Full Rollout (Default Enabled)

**Timeline:** Day 30+ (after Phase 3 validation)
**Risk:** Low (tested on new + migrated deals)

**Configuration change:**

```python
# config_v2.py

# Default to inventory-based costing for all deals
def should_use_inventory_costing(deal: Deal) -> bool:
    """Determine if deal should use inventory-based costing."""
    if not APPLICATION_INVENTORY_COSTING_ENABLED:
        return False

    # Opt-out only (default is inventory-based)
    return not deal.force_legacy_costing  # Rare override
```

**Communication:**

```markdown
# Email to all users

Subject: Enhanced Application Cost Modeling Now Default

We've rolled out enhanced application cost modeling to all deals:

✅ What's New:
- Costs vary by application complexity (simple vs critical)
- Category-based multipliers (ERP costs more than chat tools)
- Deployment type awareness (SaaS vs on-prem)
- Integration costs (APIs, SSO, data migration)

✅ What This Means:
- More accurate cost estimates (50% → 85% accuracy)
- Better budget planning for M&A deals
- Transparent cost breakdowns (see why SAP costs $500K)

✅ Action Required:
- None - all new deals use enhanced model automatically
- Existing deals: Click "Recalculate Costs" to upgrade

Questions? support@yourcompany.com
```

---

## Backward Compatibility

### Data Schema (No Changes)

**No database migrations required:**

```sql
-- Existing schema supports new features
ALTER TABLE deals ADD COLUMN use_inventory_costing BOOLEAN DEFAULT FALSE;
ALTER TABLE deals ADD COLUMN cost_recalculated_at TIMESTAMP;
ALTER TABLE deals ADD COLUMN cost_recalculated_by INTEGER REFERENCES users(id);

-- Inventory schema already has needed fields
-- (category, complexity, deployment_type, etc.)
```

### API Compatibility

**Existing API endpoints unchanged:**

```python
# GET /api/deals/{deal_id}/costs
# Returns same structure, but values may differ

{
    "deal_id": "deal-123",
    "total_application_cost": 850000,  # New value (inventory-based)
    "calculation_method": "inventory",  # NEW field
    "breakdown": {  # NEW: per-app breakdown
        "apps": [
            {
                "name": "SAP ERP",
                "cost": 470000,
                "complexity": "critical",
                "category": "erp"
            },
            # ...
        ]
    },
    # ... rest of response unchanged
}
```

### Legacy Code Paths

**Both paths supported:**

```python
def calculate_deal_costs(
    deal_id: str,
    drivers: DealDrivers,
    deal_type: str = 'acquisition',
    inventory_store: Optional[InventoryStore] = None
) -> DealCostSummary:
    """
    Dual-mode cost calculation.

    Path 1 (new): inventory_store provided → inventory-based
    Path 2 (legacy): no inventory_store → count-based (DealDrivers)
    """
    if inventory_store and should_use_inventory_costing(deal):
        # New path
        return _calculate_with_inventory(inventory_store, deal_type)
    else:
        # Legacy path
        return _calculate_with_counts(drivers, deal_type)
```

---

## Rollback Procedures

### Instant Rollback (Feature Flag)

**If critical issues arise:**

```bash
# Disable feature immediately
export APPLICATION_INVENTORY_COSTING=false

# Restart application
systemctl restart it-diligence-agent

# Verify rollback
curl https://app.example.com/health | jq '.features.application_inventory_costing'
# => {"enabled": false}
```

**Rollback time:** <5 minutes

### Per-Deal Rollback

**If specific deal has issues:**

```python
# Admin UI or API
deal.use_inventory_costing = False
deal.total_application_cost = original_cost  # Restore old value
db.session.commit()
```

### Full Rollback (Code Revert)

**If feature fundamentally broken:**

```bash
# Revert to previous release
git revert <applications-enhancement-commit-hash>
git push production main

# Or roll back to previous tag
git checkout v2.4.0
git push production HEAD:main --force
```

**Rollback triggers:**

| Trigger | Severity | Action |
|---------|----------|--------|
| >5% of cost calculations fail | Critical | Instant rollback (feature flag) |
| Performance >3x slower | High | Investigate, rollback if not fixable in 1 hour |
| Cost estimates >5x off | High | Per-deal rollback, investigate |
| User complaints >10 | Medium | Pause migration, address issues |

---

## Monitoring & Observability

### Metrics to Track

```python
# Prometheus metrics

application_cost_calculations_total = Counter(
    'application_cost_calculations_total',
    'Total application cost calculations',
    ['method', 'deal_type', 'status']
)

application_cost_calculation_duration_seconds = Histogram(
    'application_cost_calculation_duration_seconds',
    'Time to calculate application costs',
    ['method', 'app_count_bucket']
)

application_cost_variance = Gauge(
    'application_cost_variance',
    'Ratio of new cost to legacy cost',
    ['deal_id']
)
```

**Dashboards:**

```markdown
# Cost Calculation Dashboard

## Health
- Success rate: 99.8% (target: >99%)
- P50 latency: 150ms
- P95 latency: 800ms (target: <2s)
- P99 latency: 1.2s

## Adoption
- New deals using inventory costing: 100%
- Existing deals migrated: 45% (target: 80% by Day 30)

## Variance
- Median cost change: +15% (inventory costs higher, expected)
- 90th percentile: +35%
- Outliers (>2x): 3 deals (flagged for review)
```

### Alerts

```yaml
# alerts.yml

- alert: HighApplicationCostFailureRate
  expr: rate(application_cost_calculations_total{status="error"}[5m]) > 0.05
  for: 5m
  annotations:
    summary: "High cost calculation failure rate: {{ $value }}"
    action: "Disable feature flag if sustained"

- alert: ApplicationCostPerformanceDegraded
  expr: histogram_quantile(0.95, application_cost_calculation_duration_seconds) > 5
  for: 10m
  annotations:
    summary: "P95 cost calculation latency > 5s"
    action: "Investigate performance, consider rollback"
```

---

## Documentation & Training

### User Documentation

**Create:**
- [ ] `/docs/applications-enhancement.md` - Overview for users
- [ ] `/docs/cost-model-changes.md` - What changed and why
- [ ] `/docs/recalculation-guide.md` - How to recalculate existing deals
- [ ] Video tutorial (5 min): "Understanding New Cost Estimates"

### Support Team Training

**Train on:**
- How to explain cost variance to users (why SAP costs more than Slack)
- How to manually recalculate costs for a deal
- How to interpret cost breakdown in UI
- When to escalate to engineering (real bugs vs expected behavior)

### Runbook

```markdown
# Applications Enhancement Runbook

## Deployment
1. Deploy code with feature flag OFF
2. Validate: all tests pass, no regressions
3. Enable feature flag for new deals only
4. Monitor for 7 days
5. Migrate existing deals (gradual, opt-in)
6. Full rollout after 30 days

## Common Issues

### Cost calculation fails with "No category for app X"
- **Cause:** Enrichment failed, category missing
- **Fix:** Run manual enrichment via UI, or set category manually
- **Prevention:** Improve enrichment prompts

### Costs are 3x higher than expected
- **Cause:** Likely correct (old model underestimated)
- **Fix:** Validate with stakeholder, adjust multipliers if systematic
- **Not a bug:** Different complexity apps have wide variance

### Performance slow (>5s for 50 apps)
- **Cause:** Database query N+1, or missing index
- **Fix:** Check logs for query count, add inventory_store index
- **Temporary:** Disable feature flag while investigating

## Rollback
- **Instant:** `export APPLICATION_INVENTORY_COSTING=false && restart`
- **Per-deal:** Set `deal.use_inventory_costing = False` in admin UI
- **Full:** `git revert` or `git checkout v2.4.0`
```

---

## Results Criteria

### Acceptance Criteria for Rollout

**Before Phase 1 (Code Deployment):**
- [ ] All 572 existing tests pass
- [ ] All 89 new tests pass
- [ ] Feature flags implemented and tested
- [ ] Rollback procedure documented and tested

**Before Phase 2 (New Deals Only):**
- [ ] Phase 1 validation complete (no regressions)
- [ ] Monitoring dashboards live
- [ ] Alerts configured and tested
- [ ] Support team trained

**Before Phase 3 (Migrate Existing):**
- [ ] 10+ new deals processed successfully
- [ ] Zero cost calculation errors
- [ ] Performance <5s for 100 apps
- [ ] User feedback positive

**Before Phase 4 (Full Rollout):**
- [ ] 50+ existing deals migrated successfully
- [ ] Cost variance within ±30% (or explained)
- [ ] Adoption rate >60% of eligible deals
- [ ] User documentation complete

---

## Timeline Summary

| Phase | Duration | Risk | Rollback Time |
|-------|----------|------|---------------|
| 1: Code Deploy (flag OFF) | Day 1 | Low | <5 min |
| 2: New Deals Only | Days 2-7 | Medium | <5 min |
| 3: Migrate Existing (Opt-In) | Days 8-28 | Medium | Per-deal: <1 min |
| 4: Full Rollout (Default) | Day 30+ | Low | <5 min |

**Total rollout time:** 30+ days (conservative, gradual)

**Fast-track option:** If Phase 2 validation goes perfectly, can compress to 14 days.

---

## Related Documents

- **00-overview-applications-enhancement.md** - Architecture overview
- **04-cost-engine-inventory-integration.md** - Feature flag implementation
- **06-testing-validation.md** - Testing before rollout

---

**Document Status:** ✅ Complete
**Last Updated:** 2026-02-11
**All 7 specification documents complete!**
