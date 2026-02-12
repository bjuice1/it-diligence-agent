# Entity Propagation Hardening

**Status:** Specification
**Created:** 2026-02-11
**Depends On:** 00-overview-applications-enhancement.md
**Enables:** 02-table-parser-robustness.md, 03-application-cost-model.md, 05-ui-enrichment-status.md
**Estimated Scope:** 3-4 hours

---

## Overview

**Problem:** Entity (buyer vs target) currently relies on inference fallbacks in the applications bridge. If document structure is ambiguous, entity silently defaults to "target," causing buyer/target data confusion.

**Solution:** Extract and validate entity at document parse time, not during bridge processing. Fail loudly on ambiguous documents rather than guessing.

**Why this exists:** Entity is the primary dimension for filtering inventory. Silent defaults corrupt data integrity and break UI assumptions (e.g., "Target = everything, Buyer = nothing").

---

## Architecture

### Current Flow (Broken)

```
PDF: "Application Inventory" (no entity indicator)
    ↓
deterministic_parser.parse_application_table()
    ↓
ParsedTable(headers=[...], rows=[...])  # No entity field
    ↓
applications_bridge.process_applications()
    ↓
entity = drivers.entity or infer_from_context() or "target"  # Silent fallback
    ↓
InventoryStore.add_item(entity="target", ...)  # Wrong if document was buyer
```

**Failure modes:**
- Combined buyer+target table → all items tagged as "target"
- Missing section headers → defaults to "target"
- Ambiguous pronouns ("our applications") → guessed incorrectly

### Target Flow (Hardened)

```
PDF: "Target Company - Application Landscape"
    ↓
[NEW] extract_document_entity(section_text, headers)
    ↓
document_entity = "target"  # Extracted from section header
    ↓
deterministic_parser.parse_application_table(entity=document_entity)
    ↓
ParsedTable(entity="target", headers=[...], rows=[...])
    ↓
applications_bridge.process_applications()
    ↓
if not table.entity:
    raise EntityValidationError("Entity required, not inferrable from context")
    ↓
InventoryStore.add_item(entity=table.entity, ...)  # Explicit, validated
```

**Key changes:**
1. **Entity extraction at parse time** (heuristic-based, document-level)
2. **Strict validation** (no silent fallbacks)
3. **Clear error messages** (guides user to fix ambiguous documents)

---

## Specification

### 1. Entity Extraction Strategy

**Extraction points (in priority order):**

1. **Section headers** (highest confidence)
   - Pattern: `/(target|buyer|acquirer|parent)\s+(company|entity|organization)/i`
   - Example: "Target Company Applications" → `entity="target"`
   - Example: "Acquirer IT Landscape" → `entity="buyer"`

2. **Table headers** (medium confidence)
   - Column name: "Entity" or "Company" with cell values "Target" / "Buyer"
   - Extract entity from first data row if column exists

3. **Document metadata** (low confidence)
   - Filename: `target_applications.pdf` → `entity="target"`
   - PDF metadata: `/Subject` or `/Title` fields

4. **Context clues** (fallback, requires validation)
   - Pronouns: "our applications" + document ownership known
   - Section numbering: "2.3 Target IT Environment" → `entity="target"`

**Heuristic implementation:**

```python
def extract_document_entity(
    section_text: str,
    headers: List[str],
    filename: str = None,
    metadata: Dict = None
) -> Optional[str]:
    """
    Extract entity from document context using heuristics.

    Returns:
        "target" | "buyer" | None (if ambiguous)

    Raises:
        EntityAmbiguityError if conflicting signals found
    """
    signals = []

    # Check section headers
    if re.search(r'\b(target|seller|divestiture)\b', section_text, re.I):
        signals.append(("section_header", "target", "high"))
    if re.search(r'\b(buyer|acquirer|parent|acquiring)\b', section_text, re.I):
        signals.append(("section_header", "buyer", "high"))

    # Check table headers for entity column
    entity_col = next((h for h in headers if h.lower() in ['entity', 'company', 'organization']), None)
    if entity_col:
        # Entity is per-row, not document-level
        signals.append(("table_column", "per_row", "high"))
        return "per_row"  # Special case: mixed table

    # Check filename
    if filename:
        if re.search(r'\btarget\b', filename, re.I):
            signals.append(("filename", "target", "low"))
        if re.search(r'\bbuyer\b', filename, re.I):
            signals.append(("filename", "buyer", "low"))

    # Resolve signals
    high_conf_signals = [s for s in signals if s[2] == "high"]

    if len(high_conf_signals) == 0:
        return None  # Ambiguous, need user input

    if len(high_conf_signals) == 1:
        return high_conf_signals[0][1]

    # Multiple high-confidence signals - check consistency
    entities = {s[1] for s in high_conf_signals}
    if len(entities) > 1:
        raise EntityAmbiguityError(f"Conflicting entity signals: {signals}")

    return high_conf_signals[0][1]
```

### 2. Per-Row Entity Extraction (Mixed Tables)

Some documents have a single table with both buyer and target apps:

| Entity | Application | Vendor |
|--------|-------------|--------|
| Target | SAP ERP     | SAP    |
| Buyer  | Oracle ERP  | Oracle |

**Handling:**

```python
def parse_application_table_with_entity_column(
    table: Dict,
    entity_column_name: str
) -> List[ParsedTable]:
    """
    Split mixed table into separate ParsedTable objects by entity.

    Returns:
        [
            ParsedTable(entity="target", rows=[...]),
            ParsedTable(entity="buyer", rows=[...])
        ]
    """
    rows_by_entity = defaultdict(list)

    for row in table['rows']:
        entity_value = row.get(entity_column_name, '').strip().lower()

        # Normalize entity values
        if entity_value in ['target', 'seller', 'divestiture']:
            entity = 'target'
        elif entity_value in ['buyer', 'acquirer', 'parent']:
            entity = 'buyer'
        else:
            # Invalid entity value
            raise EntityValidationError(
                f"Invalid entity value '{entity_value}' in row. "
                f"Expected: target, buyer, seller, acquirer, parent"
            )

        rows_by_entity[entity].append(row)

    # Create separate ParsedTable for each entity
    return [
        ParsedTable(
            entity=entity,
            headers=[h for h in table['headers'] if h != entity_column_name],
            rows=rows,
            source_file=table.get('source_file')
        )
        for entity, rows in rows_by_entity.items()
    ]
```

### 3. Strict Validation in Bridge

**No more silent defaults:**

```python
# applications_bridge.py

def process_applications(
    parsed_table: ParsedTable,
    drivers: DealDrivers,
    inventory_store: InventoryStore
) -> int:
    """
    Process parsed application table into inventory.

    Raises:
        EntityValidationError if entity not set and not inferrable
    """
    # STRICT MODE: Entity must be explicit
    if not parsed_table.entity:
        # No silent fallback - this is a data quality error
        raise EntityValidationError(
            f"Application table from {parsed_table.source_file} has no entity. "
            f"Cannot infer entity from context. "
            f"Fix document to include entity indicator (section header or column)."
        )

    # Validate entity is valid value
    if parsed_table.entity not in ['target', 'buyer']:
        raise EntityValidationError(
            f"Invalid entity '{parsed_table.entity}'. Expected: target or buyer"
        )

    # Process with validated entity
    for row in parsed_table.rows:
        inventory_store.add_item(
            inventory_type='application',
            entity=parsed_table.entity,  # Explicit, validated
            data={
                'name': row.get('application'),
                'vendor': row.get('vendor'),
                # ... other fields
            }
        )
```

### 4. Backward Compatibility for Legacy Data

**Problem:** Existing InventoryItems may have `entity=""` or `entity=None`, which would fail strict validation.

**Solution:** Graceful degradation for legacy data created before entity enforcement cutoff date.

```python
# applications_bridge.py

from datetime import datetime

# Cutoff date: entity enforcement begins (deployment date)
ENTITY_ENFORCEMENT_CUTOFF = datetime(2026, 2, 15)  # Adjust to actual deployment date

def process_applications(
    parsed_table: ParsedTable,
    drivers: DealDrivers,
    inventory_store: InventoryStore
) -> int:
    """
    Process parsed application table into inventory.

    Handles both strict mode (new data) and graceful mode (legacy data).
    """
    # Check if entity is missing
    if not parsed_table.entity:
        # Determine if this is legacy data or new data
        is_legacy_data = _is_legacy_data(parsed_table)

        if is_legacy_data:
            # GRACEFUL MODE: Legacy data gets warning + default
            logger.warning(
                f"Legacy data missing entity: {parsed_table.source_file}. "
                f"Defaulting to 'target' (pre-enforcement cutoff)."
            )
            parsed_table.entity = _infer_entity_from_context(parsed_table, drivers)
        else:
            # STRICT MODE: New data must have explicit entity
            raise EntityValidationError(
                f"Application table from {parsed_table.source_file} has no entity. "
                f"Cannot infer entity from context. "
                f"Fix document to include entity indicator (section header or column)."
            )

    # Validate entity is valid value (both modes)
    if parsed_table.entity not in ['target', 'buyer']:
        raise EntityValidationError(
            f"Invalid entity '{parsed_table.entity}'. Expected: target or buyer"
        )

    # Process with validated entity
    for row in parsed_table.rows:
        inventory_store.add_item(
            inventory_type='application',
            entity=parsed_table.entity,
            data={
                'name': row.get('application'),
                'vendor': row.get('vendor'),
                # ... other fields
            }
        )

def _is_legacy_data(parsed_table: ParsedTable) -> bool:
    """Determine if parsed table is legacy data (pre-enforcement)."""
    # Check source file timestamp
    if parsed_table.source_file:
        source_path = Path(parsed_table.source_file)
        if source_path.exists():
            file_mtime = datetime.fromtimestamp(source_path.stat().st_mtime)
            return file_mtime < ENTITY_ENFORCEMENT_CUTOFF

    # If can't determine, treat as new data (strict mode)
    return False

def _infer_entity_from_context(
    parsed_table: ParsedTable,
    drivers: DealDrivers
) -> str:
    """
    Infer entity from context for legacy data (graceful fallback).

    Priority:
    1. Check source filename for "target" or "buyer" keywords
    2. Use DealDrivers.entity if available
    3. Default to "target" (most common)
    """
    # Check source file
    if parsed_table.source_file:
        filename_lower = parsed_table.source_file.lower()
        if "buyer" in filename_lower or "acquirer" in filename_lower:
            return "buyer"
        if "target" in filename_lower or "seller" in filename_lower:
            return "target"

    # Check DealDrivers
    if drivers and drivers.entity:
        return drivers.entity

    # Default to target (most common in M&A diligence)
    return "target"
```

**Migration Script:**

Before deploying Phase 1, run migration script to backfill existing inventory:

```bash
# Dry run (preview changes)
python migrations/backfill_inventory_entity.py --dry-run

# Apply changes
python migrations/backfill_inventory_entity.py

# Specific deal only
python migrations/backfill_inventory_entity.py --deal-id deal-123
```

Migration script (`migrations/backfill_inventory_entity.py`) provided as part of P0-2 fix.

### 5. User-Facing Error Messages

**When entity extraction fails, guide user to fix:**

```python
class EntityValidationError(Exception):
    """Raised when entity cannot be determined from document."""

    def __init__(self, message: str, suggestions: List[str] = None):
        self.message = message
        self.suggestions = suggestions or [
            "Add section header with 'Target' or 'Buyer' keyword",
            "Add 'Entity' column to table with 'Target'/'Buyer' values",
            "Rename file to include 'target' or 'buyer' keyword",
            "Manually tag document entity in UI before analysis"
        ]

    def __str__(self):
        msg = self.message + "\n\nSuggestions:\n"
        for i, suggestion in enumerate(self.suggestions, 1):
            msg += f"  {i}. {suggestion}\n"
        return msg
```

**UI display:**

```html
<!-- Document upload error message -->
<div class="alert alert-warning">
    <h4>Entity Not Detected: target_apps_inventory.pdf</h4>
    <p>{{ error.message }}</p>
    <ul>
        {% for suggestion in error.suggestions %}
        <li>{{ suggestion }}</li>
        {% endfor %}
    </ul>
    <button onclick="manualEntityTag('target_apps_inventory.pdf')">
        Manually Tag as Target/Buyer
    </button>
</div>
```

---

## Verification Strategy

### Unit Tests

```python
# tests/unit/test_entity_extraction.py

def test_extract_from_section_header_target():
    """Section header with 'target' keyword extracts correctly."""
    text = "3.2 Target Company Application Landscape"
    entity = extract_document_entity(text, headers=[])
    assert entity == "target"

def test_extract_from_section_header_buyer():
    """Section header with 'acquirer' keyword extracts as buyer."""
    text = "Acquirer IT Environment"
    entity = extract_document_entity(text, headers=[])
    assert entity == "buyer"

def test_extract_from_filename():
    """Filename with 'buyer' extracts correctly (low confidence)."""
    entity = extract_document_entity(
        section_text="Application Inventory",
        headers=[],
        filename="buyer_applications.pdf"
    )
    assert entity == "buyer"

def test_ambiguous_returns_none():
    """Ambiguous context returns None (requires user input)."""
    entity = extract_document_entity(
        section_text="IT Applications",
        headers=[],
        filename="apps.pdf"
    )
    assert entity is None

def test_conflicting_signals_raises_error():
    """Conflicting high-confidence signals raise error."""
    with pytest.raises(EntityAmbiguityError):
        extract_document_entity(
            section_text="Target Company (acquired by Buyer Corp)",
            headers=[],
            filename="buyer_target_combined.pdf"
        )

def test_per_row_entity_column_detected():
    """Table with entity column returns 'per_row'."""
    entity = extract_document_entity(
        section_text="Application Inventory",
        headers=["Entity", "Application", "Vendor"]
    )
    assert entity == "per_row"

def test_mixed_table_split_by_entity():
    """Mixed table splits into separate target/buyer tables."""
    table = {
        'headers': ['Entity', 'Application', 'Vendor'],
        'rows': [
            {'Entity': 'Target', 'Application': 'SAP', 'Vendor': 'SAP AG'},
            {'Entity': 'Buyer', 'Application': 'Oracle', 'Vendor': 'Oracle'},
            {'Entity': 'Target', 'Application': 'Slack', 'Vendor': 'Salesforce'}
        ]
    }

    tables = parse_application_table_with_entity_column(table, 'Entity')

    assert len(tables) == 2
    target_table = next(t for t in tables if t.entity == 'target')
    buyer_table = next(t for t in tables if t.entity == 'buyer')

    assert len(target_table.rows) == 2
    assert len(buyer_table.rows) == 1
    assert 'Entity' not in target_table.headers  # Column removed after split

def test_bridge_raises_on_missing_entity():
    """Bridge raises EntityValidationError if table has no entity."""
    table = ParsedTable(entity=None, headers=[...], rows=[...])

    with pytest.raises(EntityValidationError, match="has no entity"):
        process_applications(table, drivers, inv_store)

def test_bridge_raises_on_invalid_entity():
    """Bridge raises EntityValidationError on invalid entity value."""
    table = ParsedTable(entity="unknown", headers=[...], rows=[...])

    with pytest.raises(EntityValidationError, match="Invalid entity"):
        process_applications(table, drivers, inv_store)
```

### Integration Tests

```python
# tests/integration/test_entity_end_to_end.py

def test_target_document_end_to_end(sample_pdf_with_target_header):
    """Document with 'Target Company' header flows through to inventory."""
    # Parse document
    parsed = parse_document(sample_pdf_with_target_header)

    # Process through bridge
    inv_store = InventoryStore(deal_id="test")
    process_applications(parsed, drivers, inv_store)

    # Verify all items have entity=target
    items = inv_store.get_items(inventory_type='application')
    assert all(item.entity == 'target' for item in items)
    assert len(inv_store.get_items(entity='buyer')) == 0

def test_buyer_document_end_to_end(sample_pdf_with_buyer_header):
    """Document with 'Acquirer' header flows through to buyer inventory."""
    parsed = parse_document(sample_pdf_with_buyer_header)

    inv_store = InventoryStore(deal_id="test")
    process_applications(parsed, drivers, inv_store)

    # Verify all items have entity=buyer
    items = inv_store.get_items(inventory_type='application')
    assert all(item.entity == 'buyer' for item in items)
    assert len(inv_store.get_items(entity='target')) == 0

def test_mixed_table_end_to_end(sample_pdf_with_entity_column):
    """Mixed table with Entity column splits correctly."""
    parsed = parse_document(sample_pdf_with_entity_column)

    inv_store = InventoryStore(deal_id="test")
    process_applications(parsed, drivers, inv_store)

    # Verify both target and buyer items exist
    target_items = inv_store.get_items(entity='target', inventory_type='application')
    buyer_items = inv_store.get_items(entity='buyer', inventory_type='application')

    assert len(target_items) > 0
    assert len(buyer_items) > 0

    # Verify no cross-contamination
    assert all(item.entity == 'target' for item in target_items)
    assert all(item.entity == 'buyer' for item in buyer_items)
```

### Manual Verification

**Test cases:**

1. **Upload document with "Target Company Applications" section header**
   - ✅ All apps should have entity="target" in inventory
   - ✅ UI should show correct entity filter results

2. **Upload document with "Buyer IT Landscape" section header**
   - ✅ All apps should have entity="buyer" in inventory
   - ✅ UI should show correct entity filter results

3. **Upload ambiguous document (no entity indicators)**
   - ✅ Should show error message with suggestions
   - ✅ Should offer manual entity tagging in UI

4. **Upload mixed table with Entity column**
   - ✅ Should split into target and buyer inventories
   - ✅ UI should show both entities with correct counts

5. **Upload document with conflicting signals**
   - ✅ Should raise EntityAmbiguityError with details
   - ✅ Should guide user to resolve conflict

---

## Benefits

### Data Integrity
- **Zero silent defaults:** Entity always explicit or validation fails
- **Audit trail:** Entity extraction method logged (section header, filename, etc.)
- **No cross-contamination:** Buyer apps never tagged as target

### User Experience
- **Clear errors:** User knows exactly why extraction failed
- **Actionable guidance:** Suggestions on how to fix document
- **Manual override:** UI allows tagging when heuristics fail

### Maintainability
- **Explicit over implicit:** No hidden inference logic
- **Testable:** Heuristics are pure functions, easily unit tested
- **Extensible:** New extraction patterns can be added incrementally

---

## Expectations

### Success Criteria

- [ ] 100% of parsed applications have explicit entity (never None)
- [ ] Entity extraction fails loudly on ambiguous documents (no silent defaults)
- [ ] Mixed tables (entity column) split correctly into target/buyer inventories
- [ ] Error messages provide actionable guidance (tested with 5 users)
- [ ] 95%+ extraction success on real documents (10-20 sample docs)

### Non-Goals

- ❌ LLM-based entity detection (future enhancement if heuristics <90% accurate)
- ❌ Multi-language support (English only for now)
- ❌ OCR error correction (assume readable PDF text)

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Heuristics <90% accurate | Medium | High | Test on 20 real documents pre-implementation; add LLM fallback if needed |
| User confusion on error messages | Low | Medium | User testing with 5 people; iterate on message clarity |
| Mixed tables rare, code unused | Low | Low | Validate with user: have they seen mixed tables? If no, defer feature |
| Filename extraction unreliable | High | Low | Use as low-confidence signal only; prioritize section headers |

---

## Results Criteria

### Acceptance Criteria

1. **Entity extraction function implemented** with priority-ordered heuristics
2. **ParsedTable includes entity field** (required, not optional)
3. **Bridge validation enforces entity** (raises error if missing/invalid)
4. **Mixed table handling** splits by entity column if present
5. **Error messages user-friendly** with actionable suggestions
6. **All unit tests passing** (10+ tests covering heuristics and validation)
7. **Integration tests passing** (3+ end-to-end scenarios)

### Implementation Checklist

**Pre-implementation (REQUIRED before Phase 1):**

- [ ] **Run data migration** to backfill existing inventory with missing entity values:
  ```bash
  # Dry run first (preview changes)
  python migrations/backfill_inventory_entity.py --dry-run

  # Apply changes
  python migrations/backfill_inventory_entity.py

  # Review audit log: data/inventory_entity_backfill_audit_*.json
  ```

**Files to modify:**

- [ ] `tools_v2/deterministic_parser.py`
  - Add `extract_document_entity()` function
  - Add `parse_application_table_with_entity_column()` function
  - Modify `parse_application_table()` to accept and propagate entity

- [ ] `services/applications_bridge.py`
  - Add graceful validation in `process_applications()` (strict for new, graceful for legacy)
  - Add `_is_legacy_data()` and `_infer_entity_from_context()` helper functions
  - Add `EntityValidationError` exception
  - Set `ENTITY_ENFORCEMENT_CUTOFF` date

- [ ] `models/parsed_table.py` (if exists) or inline dataclass
  - Add `entity: Optional[str]` field to ParsedTable

- [ ] `tests/unit/test_entity_extraction.py` (new file)
  - 10+ unit tests for extraction heuristics
  - Add tests for legacy data graceful degradation

- [ ] `tests/integration/test_entity_end_to_end.py` (new file)
  - 3+ integration tests for document → inventory flow

**Files to create:**

- [ ] `migrations/backfill_inventory_entity.py` ✅ **ALREADY CREATED** (P0-2 fix)
  - Migration script to backfill missing entity values
  - Supports --dry-run and --deal-id options

- [ ] `data/test_fixtures/entity_extraction/`
  - `target_header.pdf` - Document with "Target Company" section
  - `buyer_header.pdf` - Document with "Acquirer" section
  - `mixed_table.xlsx` - Excel with Entity column
  - `ambiguous.pdf` - Document with no entity indicators

---

## Related Documents

- **00-overview-applications-enhancement.md** - Architecture overview
- **02-table-parser-robustness.md** - Depends on entity being available
- **05-ui-enrichment-status.md** - Displays entity and extraction metadata
- `audits/B1_buyer_target_separation.md` - Original entity scoping audit

---

**Document Status:** ✅ Complete
**Last Updated:** 2026-02-11
**Next Document:** 02-table-parser-robustness.md (depends on this)
