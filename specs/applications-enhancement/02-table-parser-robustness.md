# Table Parser Robustness

**Status:** Specification
**Created:** 2026-02-11
**Depends On:** 00-overview-applications-enhancement.md, 01-entity-propagation-hardening.md
**Enables:** 05-ui-enrichment-status.md, 06-testing-validation.md
**Estimated Scope:** 4-5 hours

---

## Overview

**Problem:** Table parser (`tools_v2/deterministic_parser.py`) uses heuristics that break on merged cells, multi-line content, non-standard headers, and Unicode edge cases. Current success rate ~70% on real-world documents.

**Solution:** Enhanced table extraction with merged cell handling, flexible header matching, Unicode normalization, and graceful degradation with user feedback.

**Why this exists:** Table parsing is the primary source of application inventory data. Parser failures force manual data entry, defeating automation value.

**Target:** 95%+ automated extraction success on real-world M&A due diligence documents.

---

## Architecture

### Current Parser (Brittle)

```
PDF → PyMuPDF/pdfplumber → Raw tables
    ↓
Fuzzy header matching (exact match required)
    ↓
Column alignment by position
    ↓
Row extraction (single-line cells only)
    ↓
ParsedTable
```

**Known failure modes (from code comments):**
```python
# TODO: Handle merged cells (currently causes misalignment)
# TODO: Multi-line cell content gets truncated
# FIXME: Unicode normalization needed for em-dashes, smart quotes
```

**Symptoms:**
- Merged header cells → columns misidentified
- Multi-line cells → text truncated or split incorrectly
- "Application Name" vs "Application" → header not recognized
- "Vendor—Primary" (em-dash) → matching fails

### Enhanced Parser (Robust)

```
PDF → PyMuPDF/pdfplumber → Raw tables
    ↓
[NEW] Unicode normalization (em-dash → hyphen, smart quotes → straight)
    ↓
[NEW] Merged cell detection and expansion
    ↓
[NEW] Flexible header matching (synonyms, partial match)
    ↓
[NEW] Multi-line cell handling (join with space)
    ↓
Column alignment (position + header name)
    ↓
Row extraction with validation
    ↓
ParsedTable (with extraction_quality score)
```

**Improvements:**
- Merged cells detected and expanded to all covered columns
- Unicode normalized before matching
- Headers matched with synonyms ("App" = "Application" = "System Name")
- Multi-line cells joined intelligently
- Extraction quality score (0.0-1.0) to flag low-confidence parses

---

## Specification

### 1. Unicode Normalization

**Problem:** PDFs contain Unicode variations that break string matching:
- Em-dash (`—` U+2014) instead of hyphen-minus (`-` U+002D)
- Smart quotes (`"` U+201C/D) instead of straight (`"` U+0022)
- Non-breaking space (U+00A0) instead of space (U+0020)

**Solution:**

```python
import unicodedata
import re

def normalize_unicode(text: str) -> str:
    """
    Normalize Unicode text for robust string matching.

    - NFD decomposition (separate base + combining marks)
    - Replace smart quotes, em-dashes, ellipses
    - Replace non-breaking spaces
    - Normalize whitespace
    """
    if not text:
        return ""

    # NFD normalization (decompose accented characters)
    text = unicodedata.normalize('NFD', text)

    # Smart quotes → straight quotes
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # " "
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # ' '

    # Em-dash, en-dash → hyphen
    text = text.replace('\u2014', '-').replace('\u2013', '-')

    # Ellipsis → three dots
    text = text.replace('\u2026', '...')

    # Non-breaking space → regular space
    text = text.replace('\u00a0', ' ')

    # Normalize whitespace (multiple spaces → single)
    text = re.sub(r'\s+', ' ', text).strip()

    return text
```

**Apply to all text before matching:**

```python
def parse_application_table(table_data: Dict) -> ParsedTable:
    # Normalize all header names
    headers = [normalize_unicode(h) for h in table_data['headers']]

    # Normalize cell values
    rows = []
    for row in table_data['rows']:
        normalized_row = {
            normalize_unicode(k): normalize_unicode(v)
            for k, v in row.items()
        }
        rows.append(normalized_row)
```

### 2. Merged Cell Handling

**Problem:** Excel merged cells in headers like:

```
| Application Info      |  Environment |
| (merged across 2 cols)|              |
| Name        | Vendor  |  Type        |
```

After PDF conversion, becomes:
```
headers = ["Application Info", "", "Environment"]
```

Empty string breaks column mapping.

**Solution: Detect and expand merged cells**

```python
def expand_merged_cells(headers: List[str], rows: List[List[str]]) -> Tuple[List[str], List[List[str]]]:
    """
    Detect merged cells (empty strings after non-empty) and expand.

    Example:
        Input:  ["Application", "", "Vendor"]
        Output: ["Application", "Application", "Vendor"]
    """
    expanded_headers = []
    last_non_empty = None

    for header in headers:
        if header.strip():
            last_non_empty = header
            expanded_headers.append(header)
        else:
            # Empty header - likely merged cell
            if last_non_empty:
                expanded_headers.append(last_non_empty)
            else:
                # Edge case: first header is empty
                expanded_headers.append("UNKNOWN_COL")

    return expanded_headers, rows  # Rows unchanged (cell content already distributed)
```

**For multi-row headers:**

```python
def detect_multi_row_headers(table: Dict) -> List[str]:
    """
    Detect if first N rows are headers (multi-row header pattern).

    Heuristic: If row has mostly text and no numbers, likely header.

    Returns: Combined header names
    """
    rows = table['rows']
    if len(rows) < 2:
        return table['headers']

    # Check if first 2-3 rows are headers
    header_rows = [table['headers']]

    for i, row in enumerate(rows[:3]):  # Check up to 3 rows
        # If >80% cells are text (not numbers), likely header
        cells = list(row.values())
        text_cells = sum(1 for c in cells if isinstance(c, str) and not c.replace('.', '').isdigit())

        if text_cells / len(cells) > 0.8:
            header_rows.append(list(row.values()))
        else:
            break  # First data row found

    # Combine multi-row headers with " - "
    if len(header_rows) > 1:
        combined_headers = []
        for col_idx in range(len(header_rows[0])):
            col_parts = [row[col_idx] for row in header_rows if col_idx < len(row)]
            combined = " - ".join(p for p in col_parts if p.strip())
            combined_headers.append(combined)

        return combined_headers

    return table['headers']
```

### 3. Flexible Header Matching

**Problem:** Headers vary across documents:
- "Application" vs "Application Name" vs "App" vs "System Name"
- "Vendor" vs "Supplier" vs "Provider"

**Solution: Synonym-based fuzzy matching**

```python
HEADER_SYNONYMS = {
    'application': [
        'application', 'app', 'application name', 'system', 'system name',
        'software', 'tool', 'product'
    ],
    'vendor': [
        'vendor', 'supplier', 'provider', 'manufacturer', 'company'
    ],
    'users': [
        'users', 'user count', '# users', 'number of users', 'seats',
        'licenses', 'license count'
    ],
    'category': [
        'category', 'type', 'classification', 'domain', 'function'
    ],
    'entity': [
        'entity', 'company', 'organization', 'owner'
    ],
    'version': [
        'version', 'ver', 'release', 'v'
    ],
    'cost': [
        'cost', 'price', 'annual cost', 'yearly cost', 'spend', 'budget'
    ]
}

def match_header(candidate: str, target_field: str) -> float:
    """
    Match header using synonym matching and fuzzy string similarity.

    Returns: Confidence score 0.0-1.0
    """
    candidate = normalize_unicode(candidate.lower())

    # Check exact match
    if candidate == target_field:
        return 1.0

    # Check synonym list
    synonyms = HEADER_SYNONYMS.get(target_field, [])
    if candidate in synonyms:
        return 0.95

    # Partial match (contains)
    for synonym in synonyms:
        if synonym in candidate or candidate in synonym:
            return 0.7

    # Fuzzy string similarity (Levenshtein-based)
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, candidate, target_field).ratio()
    if similarity > 0.8:
        return similarity

    return 0.0  # No match

def map_headers_to_fields(headers: List[str]) -> Dict[str, Tuple[str, float]]:
    """
    Map raw headers to canonical field names.

    Returns: {canonical_field: (raw_header, confidence)}
    """
    mapping = {}

    for field in HEADER_SYNONYMS.keys():
        best_match = None
        best_score = 0.0

        for header in headers:
            score = match_header(header, field)
            if score > best_score:
                best_score = score
                best_match = header

        if best_match and best_score > 0.6:  # Minimum confidence threshold
            mapping[field] = (best_match, best_score)

    return mapping
```

### 4. Multi-Line Cell Content

**Problem:** Cells with newlines get split or truncated:

```
| Application | Description              |
|-------------|--------------------------|
| SAP ERP     | Enterprise resource      |
|             | planning system          |
```

Parsed as two rows instead of one.

**Solution: Join continued rows**

```python
def join_multiline_cells(rows: List[Dict]) -> List[Dict]:
    """
    Join rows where first column is empty (likely continuation).

    Heuristic: If first column empty but others have content, append to previous row.
    """
    if not rows:
        return rows

    first_col = list(rows[0].keys())[0]  # Assume first column is key column
    joined_rows = []
    current_row = None

    for row in rows:
        # If first column empty, likely continuation
        if not row.get(first_col, '').strip():
            if current_row:
                # Append to previous row
                for key, value in row.items():
                    if value.strip():
                        current_row[key] = current_row.get(key, '') + ' ' + value
        else:
            # New row
            if current_row:
                joined_rows.append(current_row)
            current_row = row.copy()

    # Add last row
    if current_row:
        joined_rows.append(current_row)

    return joined_rows
```

### 5. Extraction Quality Score

**Add confidence metric to ParsedTable:**

```python
@dataclass
class ParsedTable:
    entity: Optional[str]
    headers: List[str]
    rows: List[Dict]
    source_file: str
    extraction_quality: float  # NEW: 0.0-1.0

def calculate_extraction_quality(
    headers: List[str],
    header_mapping: Dict[str, Tuple[str, float]],
    rows: List[Dict]
) -> float:
    """
    Calculate extraction quality score based on:
    - Header match confidence
    - Row completeness (% non-empty cells)
    - Unicode normalization required (lower quality if heavy normalization)

    Returns: 0.0-1.0 (higher is better)
    """
    # Header match quality (average confidence)
    if header_mapping:
        header_score = sum(conf for _, conf in header_mapping.values()) / len(header_mapping)
    else:
        header_score = 0.0

    # Row completeness (% cells filled)
    total_cells = sum(len(row) for row in rows)
    filled_cells = sum(1 for row in rows for v in row.values() if v.strip())
    completeness = filled_cells / total_cells if total_cells > 0 else 0.0

    # Overall quality (weighted average)
    quality = (header_score * 0.7) + (completeness * 0.3)

    return quality
```

**Use in UI to flag low-quality extractions:**

```python
if parsed_table.extraction_quality < 0.7:
    logger.warning(
        f"Low extraction quality ({parsed_table.extraction_quality:.2f}) "
        f"for table in {parsed_table.source_file}. Manual review recommended."
    )
```

---

## Verification Strategy

### Unit Tests

```python
# tests/unit/test_table_parser_robustness.py

def test_unicode_normalization_em_dash():
    """Em-dash normalized to hyphen for matching."""
    text = "Application—Primary"
    normalized = normalize_unicode(text)
    assert normalized == "Application-Primary"

def test_unicode_normalization_smart_quotes():
    """Smart quotes normalized to straight quotes."""
    text = ""SAP ERP""
    normalized = normalize_unicode(text)
    assert normalized == '"SAP ERP"'

def test_merged_cell_expansion():
    """Empty headers expanded from previous non-empty."""
    headers = ["Application", "", "Vendor", ""]
    expanded, _ = expand_merged_cells(headers, [])
    assert expanded == ["Application", "Application", "Vendor", "Vendor"]

def test_flexible_header_matching_synonym():
    """'App' matches 'application' field with high confidence."""
    score = match_header("App", "application")
    assert score > 0.9

def test_flexible_header_matching_partial():
    """'Application Name' matches 'application' with medium confidence."""
    score = match_header("Application Name", "application")
    assert score > 0.6

def test_multiline_cell_joining():
    """Continuation rows (empty first column) joined to previous."""
    rows = [
        {'application': 'SAP', 'description': 'Enterprise'},
        {'application': '', 'description': 'planning system'}
    ]
    joined = join_multiline_cells(rows)

    assert len(joined) == 1
    assert joined[0]['application'] == 'SAP'
    assert 'Enterprise planning system' in joined[0]['description']

def test_extraction_quality_high():
    """High-quality extraction (good headers, complete rows) scores >0.8."""
    headers = ['Application', 'Vendor', 'Users']
    header_mapping = {
        'application': ('Application', 1.0),
        'vendor': ('Vendor', 1.0),
        'users': ('Users', 1.0)
    }
    rows = [
        {'Application': 'SAP', 'Vendor': 'SAP AG', 'Users': '1000'},
        {'Application': 'Slack', 'Vendor': 'Salesforce', 'Users': '500'}
    ]

    quality = calculate_extraction_quality(headers, header_mapping, rows)
    assert quality > 0.8

def test_extraction_quality_low():
    """Low-quality extraction (poor headers, sparse rows) scores <0.5."""
    headers = ['Col1', 'Col2', 'Col3']
    header_mapping = {}  # No matches
    rows = [
        {'Col1': 'SAP', 'Col2': '', 'Col3': ''},
        {'Col1': '', 'Col2': '', 'Col3': ''}
    ]

    quality = calculate_extraction_quality(headers, header_mapping, rows)
    assert quality < 0.5
```

### Integration Tests with Real PDFs

```python
# tests/integration/test_parser_real_documents.py

def test_parse_merged_header_excel_pdf(sample_merged_header_pdf):
    """Real PDF with merged header cells extracts correctly."""
    parsed = parse_document(sample_merged_header_pdf)

    assert parsed.extraction_quality > 0.7
    assert 'application' in parsed.headers  # Header matched despite merge
    assert len(parsed.rows) > 0

def test_parse_multiline_cells_pdf(sample_multiline_cells_pdf):
    """PDF with multi-line cell content joins correctly."""
    parsed = parse_document(sample_multiline_cells_pdf)

    # Check that multi-line description joined
    app_with_multiline = next(
        (r for r in parsed.rows if 'planning system' in r.get('description', '').lower()),
        None
    )
    assert app_with_multiline is not None

def test_parse_unicode_heavy_pdf(sample_unicode_pdf):
    """PDF with em-dashes, smart quotes extracts correctly."""
    parsed = parse_document(sample_unicode_pdf)

    # Should parse despite Unicode variations
    assert parsed.extraction_quality > 0.6
    assert len(parsed.rows) > 0
```

### Manual Verification

**Test cases with real M&A documents:**

1. **Upload Excel → PDF with merged headers**
   - ✅ Parser detects and expands merged cells
   - ✅ Extraction quality >0.7
   - ✅ All columns mapped correctly

2. **Upload document with "System Name" instead of "Application"**
   - ✅ Synonym matching maps "System Name" → "application"
   - ✅ Confidence score shown in logs

3. **Upload document with em-dashes and smart quotes**
   - ✅ Unicode normalization succeeds
   - ✅ Header matching works despite Unicode

4. **Upload document with multi-line cells**
   - ✅ Continuation rows joined automatically
   - ✅ Full text extracted (not truncated)

5. **Upload poorly formatted document (low quality)**
   - ✅ Extraction quality <0.7 flags manual review
   - ✅ User sees warning in UI

---

## Benefits

### Automation Rate
- **Current:** 70% documents parse automatically
- **Target:** 95% documents parse automatically
- **Impact:** 3x reduction in manual data entry effort

### Data Quality
- **Unicode issues eliminated:** Em-dashes, smart quotes no longer break matching
- **Merged cells handled:** Excel → PDF conversion no longer causes column misalignment
- **Multi-line cells preserved:** Full text extracted, not truncated

### User Trust
- **Extraction quality score:** Users can see parser confidence
- **Graceful degradation:** Low-quality extractions flagged for review
- **Transparency:** Logs show which heuristics were applied

---

## Expectations

### Success Criteria

- [ ] 95%+ extraction success rate on 20 real M&A documents
- [ ] Unicode normalization handles em-dashes, smart quotes, non-breaking spaces
- [ ] Merged cell detection expands headers correctly
- [ ] Synonym matching maps 90%+ common header variations
- [ ] Multi-line cells joined without truncation
- [ ] Extraction quality score accurately reflects data quality (validated manually)

### Non-Goals

- ❌ OCR for scanned PDFs (assume digital text)
- ❌ Image-based table extraction (assume text-based tables)
- ❌ LLM-based table understanding (heuristics first, LLM fallback later if needed)

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Merged cell detection fails | Medium | Medium | Test with 10+ Excel → PDF samples; refine heuristics |
| Synonym list incomplete | High | Low | Iteratively expand based on real document analysis |
| Multi-line heuristic overfits | Low | Medium | Validate on 20+ documents; adjust threshold |
| Performance regression | Low | Low | Benchmark on 100-row table; optimize if >2s |

---

## Results Criteria

### Acceptance Criteria

1. **Unicode normalization implemented** for em-dash, smart quotes, non-breaking space
2. **Merged cell expansion** functional for single-row and multi-row headers
3. **Synonym-based header matching** with 90%+ accuracy
4. **Multi-line cell joining** without data loss
5. **Extraction quality score** calculated and stored in ParsedTable
6. **All unit tests passing** (15+ tests covering edge cases)
7. **Integration tests passing** with real PDF fixtures (3+ documents)

### Implementation Checklist

**Files to modify:**

- [ ] `tools_v2/deterministic_parser.py`
  - Add `normalize_unicode()` function
  - Add `expand_merged_cells()` function
  - Add `detect_multi_row_headers()` function
  - Add `match_header()` and `map_headers_to_fields()` functions
  - Add `join_multiline_cells()` function
  - Add `calculate_extraction_quality()` function
  - Modify `parse_application_table()` to use enhanced parsing

- [ ] `models/parsed_table.py` (or inline dataclass)
  - Add `extraction_quality: float` field

- [ ] `tests/unit/test_table_parser_robustness.py` (new file)
  - 15+ unit tests for Unicode, merged cells, synonyms, multi-line

- [ ] `tests/integration/test_parser_real_documents.py` (new file)
  - 3+ integration tests with real PDF fixtures

**Files to create:**

- [ ] `data/test_fixtures/parser_robustness/`
  - `merged_headers.pdf` - Excel with merged header cells
  - `multiline_cells.pdf` - Table with multi-line cell content
  - `unicode_heavy.pdf` - Em-dashes, smart quotes, special chars
  - `non_standard_headers.pdf` - "System Name" instead of "Application"

---

## Related Documents

- **00-overview-applications-enhancement.md** - Architecture overview
- **01-entity-propagation-hardening.md** - Entity extraction (prerequisite)
- **05-ui-enrichment-status.md** - Displays extraction quality score
- `specs/deal-type-awareness/01-preprocessing.md` - Prior Unicode work

---

**Document Status:** ✅ Complete
**Last Updated:** 2026-02-11
**Next Document:** 05-ui-enrichment-status.md (parallel with 04)
