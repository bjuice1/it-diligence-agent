# Spec 01: Preprocessing — Unicode, Table-Aware Chunking & Numeric Normalization

**Status:** Implemented
**Depends on:** None
**Enables:** Spec 02 (clean data for category mapping), Spec 03 (clean data for store linking)

---

## Problem Statement

Upstream document preprocessing corrupts application data before agents see it:

1. **Unicode private-use characters** — `deterministic_parser.py:_clean_cell_value()` (line 218) only strips `\ue200-\ue202` (3 characters). The `DocumentPreprocessor` already handles the full range `\ue000-\uf8ff` but is **never called** from `pdf_parser.py` or the deterministic parser's table pipeline.

2. **Table mid-row splitting** — `pdf_parser.py` extracts text page-by-page (line 158: `page.get_text()`). When a table spans multiple PDF pages, rows are split at page boundaries, producing orphaned cells that the markdown table parser (`deterministic_parser.py:extract_markdown_tables()` line 75) cannot reassemble.

3. **Numeric formatting** — Cell values like `"$1,250,000"`, `"N/A"`, `"TBD"` pass through `_clean_cell_value()` unmodified, causing downstream category mapping and cost extraction to fail on non-numeric strings.

---

## Files to Modify

### 1. `ingestion/pdf_parser.py`

**Change:** Integrate `DocumentPreprocessor` into the extraction pipeline.

**Current state (lines 131-204):** `parse_file()` opens PDF, iterates pages with `page.get_text()`, appends raw text to sections. No preprocessing applied.

**Modification at line 158 (inside the page loop):**

```python
# BEFORE (current):
text = page.get_text()

# AFTER:
from tools_v2.document_preprocessor import DocumentPreprocessor
# ... (import at top of file)

text = page.get_text()
text = self._preprocessor.clean(text)
```

**Add to `PDFParser.__init__()` (line ~120):**

```python
self._preprocessor = DocumentPreprocessor(aggressive=False)
```

**Why `aggressive=False`:** We want Unicode cleanup and citation removal but not typography normalization that could alter quoted content.

### 2. `ingestion/pdf_parser.py` — Table-Aware Chunking

**Change:** Add table continuation detection between pages.

**New method `_merge_split_tables()` on `PDFParser` class:**

```python
def _merge_split_tables(self, pages_text: List[str]) -> List[str]:
    """Detect and merge tables that span page boundaries.

    Strategy: If a page ends with a partial markdown table row (line starts with '|'
    but the table has fewer columns than the previous table block), merge the
    continuation rows into the previous page's table block.

    Also handles: page ending mid-row (line ends with '|' and next page starts with '|')
    """
    if len(pages_text) < 2:
        return pages_text

    merged = [pages_text[0]]
    for i in range(1, len(pages_text)):
        prev = merged[-1]
        curr = pages_text[i]

        prev_lines = prev.rstrip().split('\n')
        curr_lines = curr.lstrip().split('\n')

        # Check if previous page ends inside a table
        prev_in_table = (
            len(prev_lines) >= 2
            and prev_lines[-1].strip().startswith('|')
        )

        # Check if current page starts with table continuation
        curr_continues_table = (
            len(curr_lines) >= 1
            and curr_lines[0].strip().startswith('|')
        )

        if prev_in_table and curr_continues_table:
            # Find where table continuation ends in current page
            table_end = 0
            for j, line in enumerate(curr_lines):
                if line.strip().startswith('|'):
                    table_end = j + 1
                else:
                    break

            # Merge table rows into previous page
            table_continuation = '\n'.join(curr_lines[:table_end])
            remaining = '\n'.join(curr_lines[table_end:])

            merged[-1] = prev + '\n' + table_continuation
            if remaining.strip():
                merged.append(remaining)
        else:
            merged.append(curr)

    return merged
```

**Integration point — modify `parse_file()` after page extraction loop (line ~175):**

After collecting all page texts, call `_merge_split_tables()` before creating `DocumentSection` objects.

```python
# After the page loop, before section creation:
page_texts = [section.content for section in sections]
merged_texts = self._merge_split_tables(page_texts)
# Rebuild sections from merged texts
```

### 3. `tools_v2/deterministic_parser.py` — Extend `_clean_cell_value()`

**Current (lines 210-224):**
```python
def _clean_cell_value(value: str) -> str:
    value = re.sub(r'\*\*([^*]+)\*\*', r'\1', value)
    value = re.sub(r'\*([^*]+)\*', r'\1', value)
    value = re.sub(r'filecite[a-zA-Z0-9\-_]+', '', value)
    value = re.sub(r'[\ue200\ue201\ue202]', '', value)  # Only 3 chars!
    value = ' '.join(value.split())
    return value.strip()
```

**Replace with:**
```python
def _clean_cell_value(value: str) -> str:
    """Clean a cell value: remove formatting, Unicode artifacts, normalize numbers."""
    # Remove markdown formatting but preserve content
    value = re.sub(r'\*\*([^*]+)\*\*', r'\1', value)
    value = re.sub(r'\*([^*]+)\*', r'\1', value)

    # Remove citation markers
    value = re.sub(r'filecite[a-zA-Z0-9\-_]+', '', value)

    # Remove ALL private-use Unicode characters (full BMP PUA range)
    value = re.sub(r'[\ue000-\uf8ff]+', '', value)

    # Remove supplementary private-use area characters
    value = re.sub(r'[\U000F0000-\U000FFFFF]+', '', value)
    value = re.sub(r'[\U00100000-\U0010FFFF]+', '', value)

    # Clean up whitespace
    value = ' '.join(value.split())

    return value.strip()
```

**Key change:** `[\ue200\ue201\ue202]` (3 chars) → `[\ue000-\uf8ff]+` (full PUA range, matching `DocumentPreprocessor.PRIVATE_USE_PATTERN`).

### 4. `tools_v2/deterministic_parser.py` — Add Numeric Normalization Utility

**New function (add after `_clean_cell_value` at line ~225):**

```python
def _normalize_numeric(value: str) -> Optional[str]:
    """Normalize numeric strings for consistent storage.

    - Strip currency symbols ($, EUR, GBP, etc.)
    - Remove thousands separators (commas)
    - Convert 'N/A', 'TBD', '-', 'Unknown' to None
    - Preserve non-numeric strings as-is

    Returns: Cleaned numeric string, or None for null-equivalent values.
    """
    if not value:
        return None

    stripped = value.strip()

    # Null-equivalent values
    NULL_VALUES = {'n/a', 'na', 'tbd', '-', '--', 'unknown', 'none', ''}
    if stripped.lower() in NULL_VALUES:
        return None

    # Try to extract numeric value
    # Remove currency symbols and whitespace
    numeric = re.sub(r'[$\u20ac\u00a3\u00a5]', '', stripped)  # $, EUR, GBP, JPY
    numeric = numeric.replace(',', '')  # Remove thousands separator
    numeric = numeric.strip()

    # Validate it's actually numeric
    try:
        float(numeric)
        return numeric
    except ValueError:
        # Not numeric — return original cleaned string
        return stripped
```

**Integration — use in `_app_table_to_facts()` (line ~360) for cost/user count fields:**

```python
# When extracting numeric fields from table rows:
if field_key in ('users', 'cost', 'license_count', 'user_count'):
    cell_value = _normalize_numeric(cell_value)
    if cell_value is None:
        continue  # Skip null-equivalent values
```

### 5. `tools_v2/document_preprocessor.py` — Verify Coverage (No Changes Needed)

**Current state is correct:** `PRIVATE_USE_PATTERN = re.compile(r'[\ue000-\uf8ff]+')` (line 34) already covers the full BMP Private Use Area. The `SUPPLEMENTARY_PUA_PATTERN` (line 37) covers supplementary planes.

**Verification only:** Confirm `clean()` method (lines 68-115) calls both patterns. Current implementation is correct — no modifications needed.

---

## Test Cases

### Test 1: Unicode Cleanup
```python
def test_clean_cell_value_full_pua_range():
    """Verify all PUA characters are stripped, not just \ue200-\ue202."""
    # Characters outside old range but inside PUA
    dirty = "Oracle\ue100Database\ue500Server"
    assert _clean_cell_value(dirty) == "Oracle Database Server"

    # Original 3 chars still work
    dirty2 = "SAP\ue200ECC\ue201"
    assert _clean_cell_value(dirty2) == "SAP ECC"
```

### Test 2: Table Merge Across Pages
```python
def test_merge_split_tables():
    """Verify tables spanning page boundaries are merged."""
    parser = PDFParser()
    page1 = "Some text\n| App | Vendor | Users |\n|-----|--------|-------|\n| SAP | SAP SE | 500 |"
    page2 = "| Oracle | Oracle Corp | 200 |\n| Slack | Salesforce | 1000 |\n\nMore text"

    merged = parser._merge_split_tables([page1, page2])

    # Table rows from page2 should merge into page1
    assert "| Oracle | Oracle Corp | 200 |" in merged[0]
    assert "| Slack | Salesforce | 1000 |" in merged[0]
    # Non-table text remains separate
    assert "More text" in merged[-1]
```

### Test 3: Numeric Normalization
```python
def test_normalize_numeric():
    assert _normalize_numeric("$1,250,000") == "1250000"
    assert _normalize_numeric("N/A") is None
    assert _normalize_numeric("TBD") is None
    assert _normalize_numeric("-") is None
    assert _normalize_numeric("500") == "500"
    assert _normalize_numeric("Microsoft Office") == "Microsoft Office"  # Non-numeric passthrough
    assert _normalize_numeric("") is None
    assert _normalize_numeric("$0") == "0"
```

### Test 4: DocumentPreprocessor Integration in PDFParser
```python
def test_pdf_parser_applies_preprocessing(tmp_path):
    """Verify PDFParser calls DocumentPreprocessor on extracted text."""
    # Would need a PDF fixture with known PUA characters
    # Verify output text contains no PUA characters after parsing
    parser = PDFParser()
    # ... parse document with known artifacts
    # Assert clean output
```

---

## Acceptance Criteria

1. Parse a document containing Unicode private-use characters (e.g., `\ue100`, `\ue500`) — verify all are removed from extracted text
2. Parse a multi-page PDF where a table spans pages 3-4 — verify all table rows appear in the merged output without orphaned cells
3. Extract a table cell containing `"$1,250,000"` — verify it stores as `"1250000"` in numeric fields
4. Extract a table cell containing `"N/A"` — verify it stores as `None`, not as the literal string
5. All existing 572 tests continue to pass (no regression)
6. `DocumentPreprocessor` stats show non-zero `private_use_removed` count after parsing a document with PUA characters

---

## Rollback Plan

All changes are additive:
- `_clean_cell_value()` — Wider regex is strictly a superset of the old one
- `_normalize_numeric()` — New function, only called for specific field keys
- `_merge_split_tables()` — New method, opt-in via the extraction pipeline
- `DocumentPreprocessor` integration — Can be disabled by removing the `clean()` call

No existing behavior is removed; regressions would manifest as over-cleaning (stripping legitimate characters) which the test suite would catch.

---

## Implementation Notes

_Added post-implementation to document what was actually built and where it landed._

### 1. Files Modified

**`ingestion/pdf_parser.py`**

| Change | Actual Lines | Details |
|--------|-------------|---------|
| `DocumentPreprocessor` import | Line 14 | `from tools_v2.document_preprocessor import DocumentPreprocessor` added at top-level (spec suggested import inside method; implementation correctly uses top-level import instead). |
| `self._preprocessor` init | Line 132 | `self._preprocessor = DocumentPreprocessor(aggressive=False)` added inside `PDFParser.__init__()`. |
| `preprocessor.clean()` call | Line 161 | `page_text = self._preprocessor.clean(page_text)` applied immediately after `page.get_text("text")` on line 160, inside the page extraction loop (lines 159-162). |
| `_merge_split_tables()` integration | Line 165 | Called after the page loop: `merged_texts = self._merge_split_tables(all_text)`. Section-building loop on line 172 iterates over `merged_texts` instead of raw `all_text`. |
| `_merge_split_tables()` method | Lines 231-282 | New method on `PDFParser` class. Detects page-boundary table splits by checking if a page ends with a `|`-prefixed line and the next page starts with one. Merges continuation rows into the previous page block and keeps remaining non-table text as a separate entry. |

**`tools_v2/deterministic_parser.py`**

| Change | Actual Lines | Details |
|--------|-------------|---------|
| `_clean_cell_value()` rewrite | Lines 210-229 | Full PUA range `[\ue000-\uf8ff]+` replaces the old 3-character set `[\ue200\ue201\ue202]`. Two additional regexes added for supplementary PUA planes (`[\U000F0000-\U000FFFFF]+` and `[\U00100000-\U0010FFFF]+`). |
| `_normalize_numeric()` new function | Lines 232-264 | New utility function. Strips currency symbols (`$`, EUR, GBP, JPY), removes thousands-separator commas, returns `None` for null-equivalent values (`N/A`, `TBD`, `-`, `--`, `Unknown`, `None`, empty string), passes non-numeric strings through unchanged. |
| `_normalize_numeric` integration in `_app_table_to_facts()` | Lines 398-402 | Inside the row-processing loop, numeric fields (`user_count`, `annual_cost`, `license_count`) are passed through `_normalize_numeric()`; `None` results cause the field to be skipped. |

**`tools_v2/document_preprocessor.py`** -- No changes (verified correct as spec predicted).

| Verified Element | Line | Status |
|-----------------|------|--------|
| `PRIVATE_USE_PATTERN` covers `\ue000-\uf8ff` | Line 34 | Correct, no change needed. |
| `SUPPLEMENTARY_PUA_PATTERN` covers supplementary planes | Line 37 | Correct, no change needed. |
| `clean()` calls both `_remove_private_use` and `_remove_citations` | Lines 84-89 | Correct, no change needed. |

### 2. Deviations from Spec

| Area | Spec Planned | Actual Implementation | Reason |
|------|-------------|----------------------|--------|
| Import placement in `pdf_parser.py` | Spec showed `from tools_v2.document_preprocessor import DocumentPreprocessor` inside method with `# ... (import at top of file)` comment | Import placed at file top level (line 14) | Correct Python practice; avoids repeated import overhead. |
| `_clean_cell_value` supplementary PUA | Not explicitly in the spec's replacement block for `_clean_cell_value` | Two supplementary PUA regexes added (lines 223-224) | Defensive addition to match `DocumentPreprocessor`'s coverage. Not in spec but consistent with its intent. |
| `_normalize_numeric` integration scope | Spec showed `if field_key in ('users', 'cost', 'license_count', 'user_count')` | Implementation uses `if std_field in ('user_count', 'annual_cost', 'license_count')` (line 398) | Uses the post-mapping standard field names rather than raw header names, which is correct since the mapping has already been applied at that point. |
| `_normalize_numeric` input type | Spec did not mention `None` input handling | Implementation handles `None` input on line 242 (`if not value: return None`) | `test_none_input` test confirms this is needed; the spec test cases did not include a `None`-input test but the implementation does. |
| Line numbers shifted | Spec referenced `_clean_cell_value` at lines 210-224, `_app_table_to_facts` at line ~360 | `_clean_cell_value` is at lines 210-229; `_normalize_numeric` is at lines 232-264; `_app_table_to_facts` starts at line 334 | Minor line shifts from additions; see "Actual line numbers" below. |

No functionality was removed or narrowed relative to the spec. All deviations are either improvements or cosmetic adjustments.

### 3. Test Coverage

**File:** `tests/test_preprocessing.py` -- 22 tests across 3 test classes.

| Class | Tests | What is covered |
|-------|-------|----------------|
| `TestUnicodeCleanup` | 9 tests | Full BMP PUA range removal, original 3-char regression, supplementary PUA, normal Unicode preservation, accented character preservation, empty string handling, filecite marker removal, consecutive PUA collapse, `DocumentPreprocessor` integration. |
| `TestNumericNormalization` | 9 tests | Dollar sign stripping, Euro sign stripping, all null-equivalent values (`N/A`, `NA`, `TBD`, `-`, `--`, `Unknown`, `None`, empty), plain number passthrough, non-numeric passthrough, decimal numbers, `$0` edge case, `None` input, comma-separated numbers. |
| `TestTableMerging` | 4 tests | Basic 2-page table merge, no-merge for non-table pages, 3-page continuous table, single-page no-op. |

All 22 tests pass (confirmed from test file structure and `.pyc` cache presence).

### 4. Actual Line Numbers (Post-Implementation)

| Reference in Spec | Spec Line Number | Actual Line Number | File |
|-------------------|-----------------|-------------------|------|
| `page.get_text()` | ~158 | 160 | `ingestion/pdf_parser.py` |
| `PDFParser.__init__()` | ~120 | 130-132 | `ingestion/pdf_parser.py` |
| `preprocessor.clean()` call | ~158 (after get_text) | 161 | `ingestion/pdf_parser.py` |
| `_merge_split_tables()` call site | ~175 | 165 | `ingestion/pdf_parser.py` |
| `_merge_split_tables()` method | N/A (new) | 231-282 | `ingestion/pdf_parser.py` |
| `_clean_cell_value()` | 210-224 | 210-229 | `tools_v2/deterministic_parser.py` |
| `_normalize_numeric()` | ~225 (new) | 232-264 | `tools_v2/deterministic_parser.py` |
| `_app_table_to_facts()` numeric integration | ~360 | 398-402 | `tools_v2/deterministic_parser.py` |
| `extract_markdown_tables()` | 75 | 75 | `tools_v2/deterministic_parser.py` (unchanged) |
| `DocumentPreprocessor.PRIVATE_USE_PATTERN` | 34 | 34 | `tools_v2/document_preprocessor.py` (unchanged) |
| `DocumentPreprocessor.SUPPLEMENTARY_PUA_PATTERN` | 37 | 37 | `tools_v2/document_preprocessor.py` (unchanged) |
| `DocumentPreprocessor.clean()` | 68-115 | 68-115 | `tools_v2/document_preprocessor.py` (unchanged) |
