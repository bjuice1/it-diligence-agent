# Audit C2: Inline Report Editing with Persistence

## Status: IMPLEMENTED
## Priority: MEDIUM (Tier 3 - Feature Improvement)
## Complexity: Deep
## Implementation Date: Feb 8, 2026

---

## 1. Problem Statement

**Symptom:** Report edit buttons exist in the UI but changes don't persist. Edits are lost on page reload.

**User Impact:**
- Cannot customize AI-generated narratives
- Must manually edit exported files
- Workflow broken - edit, refresh, lose changes
- Team collaboration on reports impossible

**Expected Behavior:**
1. Click Edit on any report section
2. Modify text inline
3. Click Save
4. Changes persist in database
5. Reload shows edited version
6. ZIP export includes edits

---

## 2. Current State Analysis

### What Exists:
| Component | Status |
|-----------|--------|
| Edit buttons in UI | Present |
| `toggleEdit()` JavaScript | Present |
| `saveEdits()` JavaScript | Present (calls API) |
| `.editable` CSS class | Present |
| POST endpoints in `pe_reports.py` | **Stubs only** |
| Database model for overrides | **Missing** |
| Override loading on render | **Missing** |

### Current Endpoint Behavior:
```python
@bp.route('/reports/api/update-assessment/<domain>', methods=['POST'])
def update_assessment(domain):
    logger.info(f"Update assessment: {domain}")
    return jsonify({'status': 'ok'})  # Does nothing!
```

---

## 3. Architecture Design

### Data Flow (Target State):
```
User clicks Edit
    → contenteditable activates
    → User modifies text
    → User clicks Save
    → JavaScript POSTs to /reports/api/update-{section}/{domain}
    → Server upserts ReportOverride record
    → Returns success
    → Page shows visual indicator (edited)

Page Load:
    → Load domain data from analysis
    → Query ReportOverride for this deal+domain
    → Merge overrides into data
    → Render with override values + indicators

ZIP Export:
    → For each domain, load overrides
    → Apply overrides to content
    → Generate HTML with human edits
```

---

## 4. Data Model

### New Model: ReportOverride

```python
class ReportOverride(db.Model):
    """Stores human edits to AI-generated report content."""
    __tablename__ = 'report_overrides'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id = db.Column(db.String(36), db.ForeignKey('deals.id'), nullable=False)
    domain = db.Column(db.String(50), nullable=False)  # applications, infrastructure, etc.
    section = db.Column(db.String(50), nullable=False)  # assessment, implications, actions
    field_name = db.Column(db.String(100), nullable=False)  # specific field within section

    original_value = db.Column(db.Text)  # AI-generated value
    override_value = db.Column(db.Text)  # Human-edited value

    created_by = db.Column(db.String(100))  # User who made edit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)  # Soft delete support

    __table_args__ = (
        db.Index('ix_override_lookup', 'deal_id', 'domain', 'section', 'field_name'),
    )
```

### Field Naming Convention:
| Section | Example field_name Values |
|---------|--------------------------|
| assessment | `summary`, `current_state`, `benchmark_analysis` |
| implications | `implication_0`, `implication_1`, `implication_2` |
| actions | `action_0`, `action_1`, `action_2` |

---

## 5. Files to Modify

### Database:
| File | Changes |
|------|---------|
| `web/database.py` | Add ReportOverride model |
| Migration | Create report_overrides table |

### Backend:
| File | Changes |
|------|---------|
| `web/blueprints/pe_reports.py` | Implement save endpoints |
| `web/blueprints/pe_reports.py` | Add override loading/applying |
| `web/blueprints/pe_reports.py` | Switch to Jinja for web view |

### Frontend:
| File | Changes |
|------|---------|
| `web/templates/reports/domain_template.html` | Visual indicators, improved JS |
| `web/static/css/reports.css` | `.human-edited` styling |

---

## 6. Endpoint Implementation

### Save Assessment:
```python
@bp.route('/reports/api/update-assessment/<domain>', methods=['POST'])
def update_assessment(domain):
    deal_id = session.get('current_deal_id')
    if not deal_id:
        return jsonify({'error': 'No deal selected'}), 400

    data = request.get_json()

    for field_name, value in data.items():
        _upsert_override(
            deal_id=deal_id,
            domain=domain,
            section='assessment',
            field_name=field_name,
            override_value=value
        )

    db.session.commit()
    return jsonify({'status': 'ok', 'saved_fields': list(data.keys())})


def _upsert_override(deal_id, domain, section, field_name, override_value):
    """Insert or update a report override."""
    existing = ReportOverride.query.filter_by(
        deal_id=deal_id,
        domain=domain,
        section=section,
        field_name=field_name
    ).first()

    if existing:
        existing.override_value = override_value
        existing.updated_at = datetime.utcnow()
        existing.active = True
    else:
        override = ReportOverride(
            deal_id=deal_id,
            domain=domain,
            section=section,
            field_name=field_name,
            override_value=override_value
        )
        db.session.add(override)
```

---

## 7. Override Loading & Applying

```python
def _load_overrides(deal_id: str, domain: str) -> Dict[str, Dict[str, str]]:
    """Load all overrides for a deal+domain, organized by section."""
    overrides = ReportOverride.query.filter_by(
        deal_id=deal_id,
        domain=domain,
        active=True
    ).all()

    result = {'assessment': {}, 'implications': {}, 'actions': {}}
    for o in overrides:
        if o.section in result:
            result[o.section][o.field_name] = o.override_value

    return result


def _apply_overrides(domain_data: dict, overrides: dict) -> dict:
    """Apply human overrides to AI-generated domain data."""
    data = domain_data.copy()

    # Apply assessment overrides
    if 'assessment' in overrides:
        for field, value in overrides['assessment'].items():
            if 'benchmark_assessment' in data:
                data['benchmark_assessment'][field] = value

    # Apply implications overrides
    if 'implications' in overrides:
        for field, value in overrides['implications'].items():
            idx = int(field.split('_')[1])  # implication_0 → 0
            if idx < len(data.get('implications', [])):
                data['implications'][idx] = value

    # Apply actions overrides
    if 'actions' in overrides:
        for field, value in overrides['actions'].items():
            idx = int(field.split('_')[1])  # action_0 → 0
            if idx < len(data.get('actions', [])):
                data['actions'][idx] = value

    return data
```

---

## 8. Template Changes

### Visual Indicator CSS:
```css
.human-edited {
    border-left: 3px solid #f59e0b;  /* Amber */
    padding-left: 8px;
    position: relative;
}

.human-edited::after {
    content: "(edited)";
    position: absolute;
    top: -8px;
    right: 0;
    font-size: 10px;
    color: #f59e0b;
    font-style: italic;
}
```

### Jinja Template Update:
```html
<div class="assessment-section
     {% if 'summary' in overrides.assessment %}human-edited{% endif %}"
     data-field="summary">
    <p class="editable" contenteditable="false">
        {{ domain_data.benchmark_assessment.summary }}
    </p>
</div>
```

### Improved saveEdits() JavaScript:
```javascript
async function saveEdits() {
    const sections = {
        'assessment': {},
        'implications': {},
        'actions': {}
    };

    // Collect all edited content
    document.querySelectorAll('.editable').forEach(el => {
        const field = el.closest('[data-field]')?.dataset.field;
        const section = el.closest('[data-section]')?.dataset.section;

        if (field && section && sections[section] !== undefined) {
            sections[section][field] = el.innerText;
        }
    });

    // POST each non-empty section
    const domain = window.currentDomain;
    const promises = [];

    for (const [section, fields] of Object.entries(sections)) {
        if (Object.keys(fields).length > 0) {
            promises.push(
                fetch(`/reports/api/update-${section}/${domain}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(fields)
                })
            );
        }
    }

    const results = await Promise.all(promises);
    const allOk = results.every(r => r.ok);

    if (allOk) {
        showNotification('Changes saved', 'success');
        // Add visual indicators
        document.querySelectorAll('.editable').forEach(el => {
            el.closest('[data-field]')?.classList.add('human-edited');
        });
    } else {
        showNotification('Save failed', 'error');
    }

    toggleEdit();  // Exit edit mode
}
```

---

## 9. Audit Steps

### Phase 1: Understand Current State
- [ ] 1.1 Read current `domain_template.html` - what editing exists?
- [ ] 1.2 Read current `pe_reports.py` - trace endpoint stubs
- [ ] 1.3 Check if template is used (Jinja vs standalone HTML)
- [ ] 1.4 Map data flow from analysis → template

### Phase 2: Implement Data Layer
- [ ] 2.1 Add ReportOverride model to database.py
- [ ] 2.2 Create migration for report_overrides table
- [ ] 2.3 Run migration

### Phase 3: Implement Endpoints
- [ ] 3.1 Implement `update_assessment()` endpoint
- [ ] 3.2 Implement `update_implications()` endpoint
- [ ] 3.3 Implement `update_actions()` endpoint
- [ ] 3.4 Add `_upsert_override()` helper
- [ ] 3.5 Add `_load_overrides()` helper
- [ ] 3.6 Add `_apply_overrides()` helper

### Phase 4: Implement Rendering
- [ ] 4.1 Switch web view to Jinja template
- [ ] 4.2 Load overrides before rendering
- [ ] 4.3 Pass overrides to template
- [ ] 4.4 Add visual indicators in template

### Phase 5: Update Frontend
- [ ] 5.1 Add `.human-edited` CSS
- [ ] 5.2 Update `saveEdits()` JavaScript
- [ ] 5.3 Add data-field attributes to editable elements
- [ ] 5.4 Test edit → save → reload cycle

### Phase 6: Apply to Export
- [ ] 6.1 Load overrides in `generate_reports()` ZIP function
- [ ] 6.2 Apply overrides before rendering each domain
- [ ] 6.3 Test ZIP export includes edits

---

## 10. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Data loss if migration fails | Backup before migration |
| Breaking existing report view | Feature flag for gradual rollout |
| Conflict between editors | Last-write-wins (simple), or show conflict |
| XSS from user content | Sanitize HTML on save |

---

## 11. Success Criteria

- [ ] Edit button enables contenteditable
- [ ] Save button POSTs to correct endpoint
- [ ] Endpoint creates/updates ReportOverride record
- [ ] Page reload shows persisted edit
- [ ] Visual indicator shows edited sections
- [ ] ZIP export includes human edits
- [ ] No deal selected shows graceful error

---

## 12. Questions for Review

1. Should we track edit history (audit log)?
2. Should multiple users be able to edit same report?
3. How to handle conflicts if two users edit simultaneously?
4. Should there be a "revert to original" button?
5. Should edits be per-user or shared across team?

---

## 13. Dependencies

- None (can be built independently)

## 14. Blocks

- Team collaboration on reports
- Professional report delivery workflow

---

## 15. Implementation Notes (Feb 8, 2026)

### Already Implemented in `web/blueprints/pe_reports.py`:

**Data Model:**
- `ReportOverride` model in `web/database.py` with deal relationship
- Fields: deal_id, domain, section, field_name, original_value, override_value, active

**Helper Functions:**
- `_load_overrides(deal_id, domain)` - Loads active overrides grouped by section
- `_apply_overrides(domain_data, overrides)` - Applies overrides to DomainReportData
- `_save_overrides(deal_id, domain, section, edits)` - Upsert pattern for saving
- `_get_editing_injection_html(domain, overrides)` - Full JS/CSS injection for editing

**Endpoints (all implemented):**
- `POST /reports/api/update-assessment/<domain>` - Save assessment edits
- `POST /reports/api/update-implications/<domain>` - Save implications edits
- `POST /reports/api/update-actions/<domain>` - Save actions edits

**Report Rendering:**
- `domain_report()` route loads overrides before rendering
- Applies overrides to domain_data
- Injects editing JS/CSS for web UI viewing

**ZIP Export:**
- `generate_reports()` loads and applies overrides to each domain before export
- Human edits flow through to exported HTML files

**Editing UI:**
- Floating Edit/Save/Cancel toolbar
- contenteditable mode on data-field elements
- Visual indicators (.human-edited class with amber border)
- Auto-detection of changed fields
- Grouped by section for efficient saving

### Success Criteria Status:
- [x] Edit button enables contenteditable
- [x] Save button POSTs to correct endpoint
- [x] Endpoint creates/updates ReportOverride record
- [x] Page reload shows persisted edit
- [x] Visual indicator shows edited sections
- [x] ZIP export includes human edits
- [x] No deal selected shows graceful error (400 response)
