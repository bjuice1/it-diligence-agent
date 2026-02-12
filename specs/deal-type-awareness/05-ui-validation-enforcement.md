# Spec 05: UI Validation & Enforcement

**Status**: GREENFIELD
**Priority**: P0
**Estimated Effort**: 1.5 hours
**Dependencies**: Spec 01 (Deal Type Architecture), Spec 04 (Cost Engine)

---

## Problem Statement

The UI allows users to create deals WITHOUT selecting a deal type, which causes:
1. **Silent defaults**: Deal type defaults to "acquisition" even when user intends carve-out
2. **No validation**: Users can submit blank/invalid deal types
3. **No contextual help**: Users don't understand implications of deal type selection
4. **Post-creation confusion**: No way to change deal type after creation (requires new deal)

**Impact**: Wrong deal type → wrong recommendations → wrong decisions → failed integrations.

---

## Solution Design

### 1. Make Deal Type REQUIRED in UI

**File**: `web/templates/deal/deal_form.html` (Line ~45)

#### Current State (BROKEN)
```html
<!-- Deal type is optional, hidden in advanced section -->
<div class="form-group">
  <label for="deal_type">Deal Type (Optional)</label>
  <select name="deal_type" id="deal_type" class="form-control">
    <option value="">-- Select --</option>
    <option value="acquisition">Acquisition</option>
    <option value="carveout">Carve-Out</option>
  </select>
</div>
```

#### Fixed State (REQUIRED)
```html
<!-- Deal type is REQUIRED, prominent placement, contextual help -->
<div class="form-group required">
  <label for="deal_type">
    Deal Type <span class="text-danger">*</span>
    <i class="fa fa-info-circle" data-toggle="tooltip"
       title="Critical: Determines recommendation logic (consolidation vs separation)"></i>
  </label>
  <select name="deal_type" id="deal_type" class="form-control" required>
    <option value="" disabled selected>-- Select Deal Type (Required) --</option>
    <option value="acquisition"
            data-description="Buyer acquires target and integrates into existing infrastructure">
      📊 Acquisition (Integration)
    </option>
    <option value="carveout"
            data-description="Target is separated from parent company and operates standalone">
      ✂️ Carve-Out (Separation from Parent)
    </option>
    <option value="divestiture"
            data-description="Seller divests division/subsidiary to buyer (clean break)">
      🔀 Divestiture (Clean Separation)
    </option>
  </select>
  <small class="form-text text-muted" id="deal-type-help">
    <!-- Dynamic help text changes based on selection -->
  </small>
</div>

<script>
// Dynamic help text
$('#deal_type').on('change', function() {
  const descriptions = {
    'acquisition': '✅ System will recommend consolidation synergies (merge target → buyer infrastructure)',
    'carveout': '⚠️ System will focus on separation costs and TSA exposure (build standalone infrastructure)',
    'divestiture': '🚨 System will calculate extraction costs (untangle from parent systems)'
  };
  $('#deal-type-help').text(descriptions[$(this).val()] || '');
});
</script>
```

---

### 2. Server-Side Validation

**File**: `web/routes/deals.py` (Line ~80, `create_deal` endpoint)

#### Add Validation Logic
```python
@deals_bp.route('/deals/create', methods=['POST'])
def create_deal():
    """Create a new deal with STRICT validation."""
    # Extract form data
    deal_type = request.form.get('deal_type', '').strip()

    # VALIDATION: Deal type is REQUIRED
    if not deal_type:
        flash('Deal type is required. Please select Acquisition, Carve-Out, or Divestiture.', 'error')
        return redirect(url_for('deals.new_deal_form'))

    # VALIDATION: Deal type must be valid enum value
    VALID_DEAL_TYPES = ['acquisition', 'carveout', 'divestiture']
    if deal_type not in VALID_DEAL_TYPES:
        flash(f'Invalid deal type: {deal_type}. Must be one of {VALID_DEAL_TYPES}.', 'error')
        return redirect(url_for('deals.new_deal_form'))

    # Create deal with validated deal_type
    deal = Deal(
        name=request.form.get('deal_name'),
        target_name=request.form.get('target_name'),
        buyer_name=request.form.get('buyer_name'),
        deal_type=deal_type,  # ✅ Guaranteed to be valid
        created_by_id=current_user.id
    )

    db.session.add(deal)
    db.session.commit()

    flash(f'Deal created successfully as {deal_type.upper()}.', 'success')
    return redirect(url_for('deals.deal_detail', deal_id=deal.id))
```

---

### 3. Database Constraint Enforcement

**File**: `web/database.py` (Line ~514, Deal model)

#### Current State
```python
class Deal(BaseModel):
    __tablename__ = 'deals'

    # ... other fields ...
    deal_type = Column(String(50), default='acquisition')  # ❌ Allows NULL, defaults silently
```

#### Fixed State
```python
class Deal(BaseModel):
    __tablename__ = 'deals'

    # ... other fields ...
    deal_type = Column(
        String(50),
        nullable=False,  # ✅ NOT NULL constraint
        default='acquisition',  # Keep default for backward compatibility with existing code
        # ⚠️ NOTE: After migration period (Spec 07), remove default to force explicit selection
    )

    # Add check constraint for valid values
    __table_args__ = (
        CheckConstraint(
            "deal_type IN ('acquisition', 'carveout', 'divestiture')",
            name='valid_deal_type'
        ),
        # ... other constraints ...
    )
```

#### Migration Script

**File**: `migrations/versions/YYYYMMDD_add_deal_type_constraint.py` (NEW)

```python
"""Add NOT NULL and CHECK constraint to deal_type

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2025-XX-XX

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Step 1: Set NULL values to 'acquisition' (safe default)
    op.execute("""
        UPDATE deals
        SET deal_type = 'acquisition'
        WHERE deal_type IS NULL
    """)

    # Step 2: Add NOT NULL constraint
    op.alter_column('deals', 'deal_type',
                    existing_type=sa.String(50),
                    nullable=False)

    # Step 3: Add CHECK constraint for valid values
    op.create_check_constraint(
        'valid_deal_type',
        'deals',
        "deal_type IN ('acquisition', 'carveout', 'divestiture')"
    )

def downgrade():
    op.drop_constraint('valid_deal_type', 'deals', type_='check')
    op.alter_column('deals', 'deal_type',
                    existing_type=sa.String(50),
                    nullable=True)
```

---

### 4. Edit Deal Functionality (Allow Post-Creation Changes)

**File**: `web/templates/deal/deal_detail.html` (NEW section)

Currently, there is NO way to edit deal type after creation. Add edit capability:

```html
<!-- Deal Detail Page - Add Edit Button -->
<div class="card">
  <div class="card-header">
    <h3>Deal Information</h3>
    <button class="btn btn-sm btn-warning" data-toggle="modal" data-target="#editDealTypeModal">
      ✏️ Edit Deal Type
    </button>
  </div>
  <div class="card-body">
    <dl class="row">
      <dt class="col-sm-3">Deal Type:</dt>
      <dd class="col-sm-9">
        <span class="badge badge-{{ 'info' if deal.deal_type == 'acquisition' else 'warning' }}">
          {{ deal.deal_type|upper }}
        </span>
      </dd>
    </dl>
  </div>
</div>

<!-- Edit Deal Type Modal -->
<div class="modal fade" id="editDealTypeModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">⚠️ Change Deal Type</h5>
      </div>
      <div class="modal-body">
        <div class="alert alert-warning">
          <strong>Warning:</strong> Changing deal type will trigger re-analysis with new recommendation logic.
          All existing synergy calculations and cost estimates will be recalculated.
        </div>
        <form method="POST" action="{{ url_for('deals.update_deal_type', deal_id=deal.id) }}">
          <div class="form-group">
            <label>New Deal Type:</label>
            <select name="deal_type" class="form-control" required>
              <option value="acquisition" {{ 'selected' if deal.deal_type == 'acquisition' }}>
                📊 Acquisition (Integration)
              </option>
              <option value="carveout" {{ 'selected' if deal.deal_type == 'carveout' }}>
                ✂️ Carve-Out (Separation)
              </option>
              <option value="divestiture" {{ 'selected' if deal.deal_type == 'divestiture' }}>
                🔀 Divestiture (Clean Separation)
              </option>
            </select>
          </div>
          <button type="submit" class="btn btn-primary">Update & Re-Analyze</button>
        </form>
      </div>
    </div>
  </div>
</div>
```

**File**: `web/routes/deals.py` (NEW endpoint)

```python
@deals_bp.route('/deals/<deal_id>/update_type', methods=['POST'])
def update_deal_type(deal_id):
    """Update deal type and trigger re-analysis."""
    deal = Deal.query.get_or_404(deal_id)

    new_deal_type = request.form.get('deal_type')

    # Validate
    if new_deal_type not in ['acquisition', 'carveout', 'divestiture']:
        flash('Invalid deal type.', 'error')
        return redirect(url_for('deals.deal_detail', deal_id=deal_id))

    old_type = deal.deal_type
    deal.deal_type = new_deal_type
    db.session.commit()

    # Trigger re-analysis (optional - can be manual)
    # analysis_runner.rerun_reasoning(deal_id)

    flash(f'Deal type changed from {old_type} → {new_deal_type}. Please re-run analysis to update recommendations.', 'warning')
    return redirect(url_for('deals.deal_detail', deal_id=deal_id))
```

---

### 5. Deal Type Visibility in UI

Make deal type PROMINENT across the entire UI:

#### A. Deal List Page

**File**: `web/templates/deal/deal_list.html`

```html
<table class="table table-striped">
  <thead>
    <tr>
      <th>Deal Name</th>
      <th>Target</th>
      <th>Deal Type</th>  <!-- NEW column -->
      <th>Status</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {% for deal in deals %}
    <tr>
      <td>{{ deal.name }}</td>
      <td>{{ deal.target_name }}</td>
      <td>
        <span class="badge badge-{{ 'info' if deal.deal_type == 'acquisition' else 'warning' }}">
          {{ deal.deal_type|upper }}
        </span>
      </td>
      <td>{{ deal.status }}</td>
      <td><a href="{{ url_for('deals.deal_detail', deal_id=deal.id) }}">View</a></td>
    </tr>
    {% endfor %}
  </tbody>
</table>
```

#### B. Deal Header Badge

**File**: `web/templates/base.html` (deal context header)

```html
<!-- Show deal type in page header -->
{% if current_deal %}
<div class="alert alert-{{ 'info' if current_deal.deal_type == 'acquisition' else 'warning' }} mb-3">
  <strong>Current Deal:</strong> {{ current_deal.name }}
  <span class="badge badge-dark">{{ current_deal.deal_type|upper }}</span>
  {% if current_deal.deal_type == 'carveout' %}
    <small>(Separation mode - no consolidation synergies)</small>
  {% elif current_deal.deal_type == 'acquisition' %}
    <small>(Integration mode - consolidation focus)</small>
  {% endif %}
</div>
{% endif %}
```

---

### 6. Deal Type Filter in Reports

**File**: `web/templates/reports/cost_summary.html`

Add deal type context to cost reports:

```html
<div class="card">
  <div class="card-header">
    <h2>Cost Summary</h2>
    <span class="badge badge-lg badge-{{ 'info' if deal.deal_type == 'acquisition' else 'warning' }}">
      {{ deal.deal_type|upper }}
    </span>
  </div>
  <div class="card-body">
    {% if deal.deal_type == 'carveout' %}
    <div class="alert alert-info">
      <i class="fa fa-info-circle"></i>
      <strong>Carve-Out Cost Model:</strong> Costs reflect separation and standalone build-out (1.5-3x higher than acquisition).
      TSA costs included.
    </div>
    {% endif %}

    <table class="table">
      <tr>
        <th>Total Integration Cost:</th>
        <td>${{ "{:,.0f}".format(cost_estimate.total_cost) }}</td>
      </tr>
      {% if deal.deal_type == 'carveout' %}
      <tr>
        <th>TSA Costs (12 months):</th>
        <td>${{ "{:,.0f}".format(cost_estimate.tsa_costs) }}</td>
      </tr>
      {% endif %}
    </table>
  </div>
</div>
```

---

## Client-Side Validation (JavaScript)

**File**: `web/static/js/deal_form_validation.js` (NEW)

```javascript
/**
 * Deal Form Validation - Enforce deal type selection
 */

$(document).ready(function() {
  // Prevent form submission if deal type not selected
  $('#deal-form').on('submit', function(e) {
    const dealType = $('#deal_type').val();

    if (!dealType || dealType === '') {
      e.preventDefault();
      alert('❌ Deal type is required. Please select Acquisition, Carve-Out, or Divestiture.');
      $('#deal_type').focus();
      return false;
    }

    // Confirmation for carve-out/divestiture (high-risk types)
    if (dealType === 'carveout' || dealType === 'divestiture') {
      const confirmed = confirm(
        `⚠️ You selected ${dealType.toUpperCase()}.\n\n` +
        'This will analyze the deal as a SEPARATION (not integration).\n' +
        'System will calculate standalone build-out costs.\n\n' +
        'Is this correct?'
      );

      if (!confirmed) {
        e.preventDefault();
        return false;
      }
    }

    return true;
  });

  // Show visual indicator when deal type changes
  $('#deal_type').on('change', function() {
    const dealType = $(this).val();
    const indicator = $('.deal-type-indicator');

    if (dealType === 'acquisition') {
      indicator.html('📊 Integration Mode').removeClass('bg-warning').addClass('bg-info');
    } else if (dealType === 'carveout') {
      indicator.html('✂️ Separation Mode').removeClass('bg-info').addClass('bg-warning');
    } else if (dealType === 'divestiture') {
      indicator.html('🔀 Divestiture Mode').removeClass('bg-info').addClass('bg-warning');
    }
  });
});
```

---

## API Validation

**File**: `web/api/deals.py` (API endpoint for programmatic deal creation)

```python
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, validate, ValidationError

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

class DealSchema(Schema):
    """Schema for deal creation API."""
    name = fields.Str(required=True)
    target_name = fields.Str(required=True)
    buyer_name = fields.Str(required=True)
    deal_type = fields.Str(
        required=True,  # ✅ REQUIRED
        validate=validate.OneOf(['acquisition', 'carveout', 'divestiture']),
        error_messages={
            'required': 'Deal type is required.',
            'validator_failed': 'Deal type must be one of: acquisition, carveout, divestiture.'
        }
    )

@api_bp.route('/deals', methods=['POST'])
def create_deal_api():
    """API endpoint to create deal with strict validation."""
    schema = DealSchema()

    try:
        # Validate request body
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Create deal
    deal = Deal(**data, created_by_id=current_user.id)
    db.session.add(deal)
    db.session.commit()

    return jsonify({
        'id': deal.id,
        'deal_type': deal.deal_type,
        'message': 'Deal created successfully'
    }), 201
```

---

## Documentation Updates

**File**: `docs/user_guide/creating_deals.md` (UPDATE)

Add section on deal type selection:

```markdown
## Selecting the Correct Deal Type

The deal type is **CRITICAL** and determines how the system analyzes your transaction:

### Acquisition (Integration)
- **Use when**: Buyer is acquiring target and will integrate into existing infrastructure
- **System behavior**: Recommends consolidation synergies (merge apps, networks, systems)
- **Cost model**: Baseline costs for extending buyer infrastructure
- **Example**: Private equity firm buys a SaaS company and migrates to their cloud platform

### Carve-Out (Separation from Parent)
- **Use when**: Target is being separated from a parent company and needs standalone systems
- **System behavior**: Focuses on separation costs, TSA exposure, standalone build-out
- **Cost model**: 1.5-3x higher costs due to building NEW infrastructure from scratch
- **Example**: Division of a Fortune 500 company is spun out and needs its own IT stack

### Divestiture (Clean Separation)
- **Use when**: Seller is divesting a division/subsidiary to a buyer (clean break from seller)
- **System behavior**: Analyzes extraction costs, data migration, untangling from parent
- **Cost model**: Highest costs due to complex separation from entangled systems
- **Example**: Conglomerate sells business unit to competitor

⚠️ **Common Mistake**: Selecting "Acquisition" for a carve-out will result in WRONG recommendations (system will suggest consolidating with parent, which is the opposite of the goal).

✅ **Best Practice**: If unsure, ask: "Is the target joining buyer's systems (acquisition) or leaving parent's systems (carve-out)?"
```

---

## Error Messages

Standardized error messages for validation failures:

| Scenario | Error Message |
|----------|---------------|
| Blank deal type | `Deal type is required. Please select Acquisition, Carve-Out, or Divestiture.` |
| Invalid deal type | `Invalid deal type: "merger". Must be one of: acquisition, carveout, divestiture.` |
| Database constraint violation | `Database constraint violated: deal_type must be one of the valid types.` |
| API validation failure | `{"errors": {"deal_type": ["Deal type is required."]}}` |

---

## Success Criteria

- [ ] Deal type field is REQUIRED in `web/templates/deal/deal_form.html` with `required` attribute
- [ ] Server-side validation in `web/routes/deals.py` rejects blank/invalid deal types
- [ ] Database migration adds NOT NULL + CHECK constraint to `deals.deal_type`
- [ ] Edit deal type functionality added (modal + endpoint)
- [ ] Deal type visible in deal list, deal header, cost reports
- [ ] Client-side JavaScript validation prevents form submission without deal type
- [ ] API schema validation enforces deal type for programmatic creation
- [ ] User documentation updated with deal type selection guide
- [ ] All validation errors use standardized, helpful messages

---

## Testing

**File**: `tests/test_ui_deal_type_validation.py` (NEW)

```python
import pytest
from web.app import create_app, db
from web.database import Deal, User

class TestDealTypeValidation:
    """Test UI-level deal type validation."""

    @pytest.fixture
    def client(self):
        app = create_app('testing')
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()

    def test_create_deal_without_type_fails(self, client):
        """Test that creating deal without deal_type is rejected."""
        response = client.post('/deals/create', data={
            'deal_name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co'
            # deal_type is MISSING
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Deal type is required' in response.data

    def test_create_deal_with_invalid_type_fails(self, client):
        """Test that invalid deal_type is rejected."""
        response = client.post('/deals/create', data={
            'deal_name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co',
            'deal_type': 'merger'  # ❌ Invalid
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid deal type' in response.data

    def test_create_deal_with_valid_type_succeeds(self, client):
        """Test that valid deal_type is accepted."""
        response = client.post('/deals/create', data={
            'deal_name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co',
            'deal_type': 'carveout'  # ✅ Valid
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Deal created successfully' in response.data

    def test_update_deal_type_triggers_warning(self, client):
        """Test that updating deal type shows re-analysis warning."""
        # Create deal
        deal = Deal(name='Test', deal_type='acquisition')
        db.session.add(deal)
        db.session.commit()

        # Update deal type
        response = client.post(f'/deals/{deal.id}/update_type', data={
            'deal_type': 'carveout'
        }, follow_redirects=True)

        assert b're-run analysis' in response.data
```

---

## Files Modified

| File | Lines Changed | Type |
|------|---------------|------|
| `web/templates/deal/deal_form.html` | ~40 | Update |
| `web/templates/deal/deal_detail.html` | +60 | Add modal |
| `web/templates/deal/deal_list.html` | ~10 | Add column |
| `web/templates/base.html` | ~15 | Add header |
| `web/routes/deals.py` | ~30 | Validation |
| `web/database.py` | ~10 | Constraint |
| `web/static/js/deal_form_validation.js` | +50 | New file |
| `migrations/versions/YYYYMMDD_add_deal_type_constraint.py` | +40 | New file |
| `tests/test_ui_deal_type_validation.py` | +80 | New file |
| `docs/user_guide/creating_deals.md` | +30 | Update |

**Total**: ~365 lines of code

---

## Dependencies

**Depends On**:
- Spec 01: Deal Type Architecture (taxonomy definitions)
- Spec 04: Cost Engine Deal Awareness (cost calculations need valid deal_type)

**Blocks**:
- Spec 06: Testing & Validation (tests need UI enforcement in place)
- Spec 07: Migration & Rollout (migration assumes UI validation is live)

---

## Estimated Effort

- **UI Updates**: 0.5 hours (form changes, templates)
- **Validation Logic**: 0.5 hours (server-side + client-side)
- **Database Migration**: 0.25 hours (constraint + migration script)
- **Testing**: 0.25 hours (UI validation tests)
- **Total**: 1.5 hours

---

**Next Steps**: Proceed to Spec 06 (Testing & Validation) to build comprehensive test coverage for all deal types.
