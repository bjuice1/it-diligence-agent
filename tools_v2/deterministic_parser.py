"""
Deterministic Parser for Structured IT Documents

Parses markdown tables and other structured formats WITHOUT using LLMs.
This ensures 100% extraction accuracy for already-structured data.

Use Cases:
- Application inventory tables
- Infrastructure inventory tables
- Contract/vendor lists
- Any markdown table with clear column headers

The LLM discovery agents should only handle unstructured prose.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
import unicodedata
from difflib import SequenceMatcher

# Import shared cost status utility
from utils.cost_status_inference import infer_cost_status
from utils.cost_status_inference import normalize_numeric  # For test verification

logger = logging.getLogger(__name__)


# =============================================================================
# ENTITY EXTRACTION (Doc 01: Entity Propagation Hardening)
# =============================================================================

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


class EntityAmbiguityError(EntityValidationError):
    """Raised when conflicting entity signals are found."""
    pass


def extract_document_entity(
    section_text: str,
    headers: List[str],
    filename: str = None,
    metadata: Dict = None
) -> Optional[str]:
    """
    Extract entity from document context using heuristics.

    Args:
        section_text: Section header or surrounding text
        headers: Table column headers
        filename: Source filename (optional)
        metadata: Document metadata (optional)

    Returns:
        "target" | "buyer" | "per_row" | None

    Raises:
        EntityAmbiguityError: If conflicting signals found
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


# =============================================================================
# TABLE PARSER ROBUSTNESS (Doc 02: Parser Enhancements)
# =============================================================================

def normalize_unicode(text: str) -> str:
    """
    Normalize Unicode text for robust string matching.

    Handles:
    - NFD decomposition (separate base + combining marks)
    - Smart quotes → straight quotes
    - Em-dashes/en-dashes → hyphens
    - Ellipsis → three dots
    - Non-breaking spaces → regular spaces
    - Multiple spaces → single space

    Args:
        text: Raw text from PDF

    Returns:
        Normalized text
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


def expand_merged_cells(headers: List[str], rows: List[List[str]]) -> Tuple[List[str], List[List[str]]]:
    """
    Detect merged cells (empty strings after non-empty) and expand.

    When Excel merged cells are converted to PDF, empty headers appear.
    This expands them from the previous non-empty header.

    Example:
        Input:  ["Application", "", "Vendor"]
        Output: ["Application", "Application", "Vendor"]

    Args:
        headers: Raw headers (may contain empty strings)
        rows: Table rows (unchanged)

    Returns:
        (expanded_headers, rows)
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

    return expanded_headers, rows


def detect_multi_row_headers(table: Dict) -> List[str]:
    """
    Detect if first N rows are headers (multi-row header pattern).

    Heuristic: If row has mostly text and no numbers, likely header.

    Args:
        table: Table dict with 'headers' and 'rows'

    Returns:
        Combined header names
    """
    rows = table.get('rows', [])
    if len(rows) < 2:
        return table.get('headers', [])

    # Check if first 2-3 rows are headers
    header_rows = [table['headers']]

    for i, row in enumerate(rows[:3]):  # Check up to 3 rows
        # If >80% cells are text (not numbers), likely header
        cells = list(row.values()) if isinstance(row, dict) else row
        text_cells = sum(1 for c in cells if isinstance(c, str) and not c.replace('.', '').replace(',', '').isdigit())

        if len(cells) > 0 and text_cells / len(cells) > 0.8:
            header_rows.append(cells if isinstance(row, list) else list(row.values()))
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

    return table.get('headers', [])


# Header synonyms for flexible matching
HEADER_SYNONYMS = {
    'application': [
        'application', 'app', 'application name', 'system', 'system name',
        'software', 'tool', 'product', 'app name', 'applications'
    ],
    'vendor': [
        'vendor', 'supplier', 'provider', 'manufacturer', 'company', 'vendors'
    ],
    'users': [
        'users', 'user count', '# users', 'number of users', 'seats',
        'licenses', 'license count', 'user', '# of users'
    ],
    'category': [
        'category', 'type', 'classification', 'domain', 'function', 'categories'
    ],
    'entity': [
        'entity', 'company', 'organization', 'owner', 'entities'
    ],
    'version': [
        'version', 'ver', 'release', 'v', 'versions'
    ],
    'cost': [
        'cost', 'price', 'annual cost', 'yearly cost', 'spend', 'budget',
        'costs', 'annual spend', 'yearly spend'
    ],
    'hosting': [
        'hosting', 'deployment', 'location', 'environment', 'hosted by'
    ],
    'criticality': [
        'criticality', 'critical', 'priority', 'importance', 'risk'
    ]
}


def match_header(candidate: str, target_field: str) -> float:
    """
    Match header using synonym matching and fuzzy string similarity.

    Args:
        candidate: Raw header from document
        target_field: Canonical field name (e.g., "application")

    Returns:
        Confidence score 0.0-1.0
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
    similarity = SequenceMatcher(None, candidate, target_field).ratio()
    if similarity > 0.8:
        return similarity

    return 0.0  # No match


def map_headers_to_fields(headers: List[str]) -> Dict[str, Tuple[str, float]]:
    """
    Map raw headers to canonical field names.

    Args:
        headers: Raw headers from document

    Returns:
        {canonical_field: (raw_header, confidence)}
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


def join_multiline_cells(rows: List[Dict]) -> List[Dict]:
    """
    Join rows where first column is empty (likely continuation).

    Heuristic: If first column empty but others have content, append to previous row.

    Args:
        rows: Parsed table rows

    Returns:
        Rows with multi-line cells joined
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


def calculate_extraction_quality(
    headers: List[str],
    header_mapping: Dict[str, Tuple[str, float]],
    rows: List[Dict]
) -> float:
    """
    Calculate extraction quality score based on:
    - Header match confidence
    - Row completeness (% non-empty cells)

    Args:
        headers: Raw headers
        header_mapping: Result from map_headers_to_fields()
        rows: Parsed table rows

    Returns:
        Quality score 0.0-1.0 (higher is better)
    """
    # Header match quality (average confidence)
    if header_mapping:
        header_score = sum(conf for _, conf in header_mapping.values()) / len(header_mapping)
    else:
        header_score = 0.0

    # Row completeness (% cells filled)
    total_cells = sum(len(row) for row in rows)
    filled_cells = sum(1 for row in rows for v in row.values() if v and v.strip())
    completeness = filled_cells / total_cells if total_cells > 0 else 0.0

    # Overall quality (weighted average)
    quality = (header_score * 0.7) + (completeness * 0.3)

    return quality


@dataclass
class ParsedTable:
    """Represents a parsed markdown table"""
    headers: List[str]
    rows: List[Dict[str, str]]
    table_type: Optional[str] = None  # "application_inventory", "infrastructure", etc.
    source_section: str = ""
    raw_text: str = ""
    entity: Optional[str] = None  # "target" or "buyer" - extracted from document context
    extraction_quality: float = 1.0  # 0.0-1.0 quality score (Doc 02: Parser Robustness)


@dataclass
class ParserResult:
    """Result of parsing a document"""
    tables: List[ParsedTable] = field(default_factory=list)
    facts_created: int = 0
    remaining_text: str = ""  # Unstructured text for LLM discovery
    errors: List[str] = field(default_factory=list)


# =============================================================================
# TABLE DETECTION PATTERNS
# =============================================================================

# Column headers that indicate an application inventory table
APP_INVENTORY_HEADERS = {
    "application", "app", "app name", "application name", "system", "software", "platform",
    "vendor", "category", "version", "hosting", "deployment", "users",
    "user count", "annual cost", "cost", "criticality", "critical", "entity"
}

# Column headers that indicate infrastructure inventory
INFRA_INVENTORY_HEADERS = {
    "server", "hostname", "host", "ip", "ip address", "os", "operating system",
    "cpu", "cores", "memory", "ram", "storage", "disk", "location", "datacenter",
    "environment", "env", "vmware", "hypervisor"
}

# Column headers that indicate contract/vendor table
CONTRACT_HEADERS = {
    "contract", "vendor", "supplier", "start date", "end date", "expiration",
    "renewal", "term", "value", "annual value", "tcv", "acv"
}

# Column headers that indicate organization/staffing table
ORG_INVENTORY_HEADERS = {
    "team", "team name", "department", "group", "function",
    "role", "title", "job title", "position",
    "headcount", "hc", "head count", "fte", "ftes",
    "reports to", "reporting to", "manager", "reports",
    "location", "office", "site",
    "responsibilities", "scope", "focus area",
    "name", "lead", "leader", "director", "vp",
    # Org-specific cost/staffing columns (avoid generic "cost"/"vendor" to prevent app table conflicts)
    "personnel cost", "total personnel cost",
    "outsourced", "outsourced %", "outsourced percentage",
    "notes", "comments",
}

# Minimum columns required to consider something a valid inventory table
MIN_COLUMNS_FOR_INVENTORY = 3


# =============================================================================
# MARKDOWN TABLE PARSER
# =============================================================================

def extract_markdown_tables(text: str) -> List[Tuple[str, int, int]]:
    """
    Extract all markdown tables from text.

    Returns:
        List of (table_text, start_pos, end_pos) tuples
    """
    tables = []

    # Pattern for markdown table: header row, separator row, data rows
    # Header: | col1 | col2 | col3 |
    # Separator: |---|---|---|  or |:---|:---:|---:|
    # Data: | val1 | val2 | val3 |

    lines = text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for potential table start (line with pipes)
        if '|' in line and line.count('|') >= 2:
            # Check if next line is a separator
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if _is_separator_row(next_line):
                    # Found a table! Collect all rows
                    table_lines = [lines[i], lines[i + 1]]
                    j = i + 2

                    while j < len(lines):
                        row_line = lines[j].strip()
                        if '|' in row_line and not _is_separator_row(row_line):
                            # Check if it's a data row (has content between pipes)
                            cells = _split_row(row_line)
                            if cells and any(c.strip() for c in cells):
                                table_lines.append(lines[j])
                                j += 1
                            else:
                                break
                        else:
                            break

                    # Only include if we have at least one data row
                    if len(table_lines) > 2:
                        table_text = '\n'.join(table_lines)
                        # Calculate approximate positions
                        start_pos = text.find(lines[i])
                        end_pos = start_pos + len(table_text)
                        tables.append((table_text, start_pos, end_pos))

                    i = j
                    continue

        i += 1

    return tables


def _is_separator_row(line: str) -> bool:
    """Check if a line is a markdown table separator row"""
    # Remove pipes and whitespace, check if only contains -, :, |
    cleaned = line.replace('|', '').replace(' ', '').replace('-', '').replace(':', '')
    return len(cleaned) == 0 and '-' in line and '|' in line


def _split_row(line: str) -> List[str]:
    """Split a markdown table row into cells"""
    # Remove leading/trailing pipes and split
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return [cell.strip() for cell in line.split('|')]


def parse_markdown_table(table_text: str) -> Optional[ParsedTable]:
    """
    Parse a markdown table into structured data.

    Args:
        table_text: Raw markdown table text

    Returns:
        ParsedTable with headers and rows, or None if parsing fails
    """
    lines = [l.strip() for l in table_text.strip().split('\n') if l.strip()]

    if len(lines) < 3:  # Need header, separator, at least one data row
        return None

    # Parse header row
    raw_headers = _split_row(lines[0])

    # DOC 02: Unicode normalization (em-dashes, smart quotes, etc.)
    raw_headers = [normalize_unicode(h) for h in raw_headers]

    # DOC 02: Expand merged cells (empty headers after non-empty)
    raw_headers, _ = expand_merged_cells(raw_headers, [])

    # Normalize headers for matching
    headers = [_normalize_header(h) for h in raw_headers]

    # Skip separator row (lines[1])

    # Parse data rows
    rows = []
    for line in lines[2:]:
        cells = _split_row(line)

        # Pad or trim cells to match header count
        while len(cells) < len(headers):
            cells.append("")
        cells = cells[:len(headers)]

        # Create dict mapping header -> value
        row_dict = {}
        for header, value in zip(headers, cells):
            if header:  # Skip empty headers
                # DOC 02: Unicode normalization for cell values
                cleaned_value = _clean_cell_value(value)
                cleaned_value = normalize_unicode(cleaned_value)
                row_dict[header] = cleaned_value

        if any(v for v in row_dict.values()):  # Skip completely empty rows
            rows.append(row_dict)

    if not rows:
        return None

    # DOC 02: Join multi-line cells (continuation rows)
    rows = join_multiline_cells(rows)

    # DOC 02: Calculate header mapping for quality score
    header_mapping = map_headers_to_fields(headers)

    # DOC 02: Calculate extraction quality
    quality = calculate_extraction_quality(headers, header_mapping, rows)

    # Log quality warnings
    if quality < 0.7:
        logger.warning(
            f"Low extraction quality ({quality:.2f}) for table. "
            f"Headers: {headers[:5]}... Manual review may be needed."
        )

    return ParsedTable(
        headers=headers,
        rows=rows,
        raw_text=table_text,
        extraction_quality=quality
    )


def _normalize_header(header: str) -> str:
    """Normalize a header name for consistent matching"""
    # DOC 02: Unicode normalization first
    header = normalize_unicode(header)

    # Remove markdown formatting
    header = re.sub(r'\*+', '', header)  # Remove bold/italic markers
    header = header.strip().lower()
    return header


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


# =============================================================================
# TABLE TYPE DETECTION
# =============================================================================

def detect_table_type(table: ParsedTable) -> str:
    """
    Detect what type of inventory table this is based on headers.

    Returns:
        "application_inventory", "infrastructure_inventory",
        "contract_inventory", "organization_inventory", or "unknown"
    """
    headers_lower = {h.lower() for h in table.headers if h}

    # Score each type
    app_score = len(headers_lower & APP_INVENTORY_HEADERS)
    infra_score = len(headers_lower & INFRA_INVENTORY_HEADERS)
    contract_score = len(headers_lower & CONTRACT_HEADERS)
    org_score = len(headers_lower & ORG_INVENTORY_HEADERS)

    # Score-based classification with priority ordering
    scores = {
        "application_inventory": app_score,
        "infrastructure_inventory": infra_score,
        "contract_inventory": contract_score,
        "organization_inventory": org_score,
    }

    # DISAMBIGUATION: If table has "vendor" column, it's likely contract/app, not org
    # (Handles vendor tables with generic "function" + "headcount" that score for org)
    if "vendor" in headers_lower and org_score > 0:
        # Boost contract score and zero out org score to prefer vendor interpretation
        scores["contract_inventory"] += 2  # Boost contract
        scores["organization_inventory"] = 0  # Zero org

    # Find highest scoring type with minimum threshold of 2
    # Lowered from 3 to handle smaller org tables (e.g., 5 columns with 2-3 matches)
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score >= 2:
        return best_type

    return "unknown"


# =============================================================================
# FACTSTORE INTEGRATION
# =============================================================================

def table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str = "target",
    source_document: str = "",
    inventory_store: Optional["InventoryStore"] = None,
) -> int:
    """
    Convert a parsed table directly into FactStore entries (and optionally InventoryStore items).

    Args:
        table: Parsed markdown table
        fact_store: FactStore instance
        entity: "target" or "buyer"
        source_document: Source filename for traceability
        inventory_store: Optional InventoryStore for bidirectional linking (Spec 03)

    Returns:
        Number of facts created
    """
    table_type = detect_table_type(table)

    if table_type == "application_inventory":
        return _app_table_to_facts(table, fact_store, entity, source_document, inventory_store)
    elif table_type == "infrastructure_inventory":
        return _infra_table_to_facts(table, fact_store, entity, source_document, inventory_store)
    elif table_type == "contract_inventory":
        return _contract_table_to_facts(table, fact_store, entity, source_document, inventory_store)
    elif table_type == "organization_inventory":
        return _org_table_to_facts(table, fact_store, entity, source_document, inventory_store)
    else:
        logger.warning(f"Unknown table type, skipping: headers={table.headers[:5]}")
        return 0


def _app_table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str,
    source_document: str,
    inventory_store: Optional["InventoryStore"] = None,
) -> int:
    """Convert application inventory table to facts (and optionally inventory items)."""
    facts_created = 0

    # ENTITY VALIDATION (Doc 01: Entity Propagation Hardening)
    # Use table.entity if available, otherwise use parameter
    table_entity = table.entity if table.entity and table.entity != "per_row" else entity

    # Validate entity is set and valid
    if not table_entity or table_entity.strip() == "":
        raise EntityValidationError(
            f"Application table from {source_document} has no entity. "
            f"Cannot infer entity from context. "
            f"Document must include entity indicator (section header, filename, or Entity column)."
        )

    if table_entity not in ['target', 'buyer']:
        raise EntityValidationError(
            f"Invalid entity '{table_entity}' in table from {source_document}. "
            f"Expected: 'target' or 'buyer'"
        )

    # Use validated entity for all items in this table
    entity = table_entity

    # Map common header variations to standard fields
    header_mapping = {
        # Application name
        "application": "item",
        "app": "item",
        "app name": "item",
        "application name": "item",
        "system": "item",
        "software": "item",
        "platform": "item",
        # Details fields
        "vendor": "vendor",
        "category": "category_detail",  # Don't overwrite domain category
        "version": "version",
        "hosting": "deployment",
        "deployment": "deployment",
        "users": "user_count",
        "user count": "user_count",
        "annual cost": "annual_cost",
        "cost": "annual_cost",
        "criticality": "criticality",
        # Additional fields
        "carve-out dependency (injected)": "carve_out_dependency",
        "carve-out dependency": "carve_out_dependency",
        "parent-hosted / tsa-locked until day-x (injected)": "tsa_locked",
        "contract renewal window (injected)": "contract_renewal_window",
        "contract renewal window": "contract_renewal_window",
    }

    for row in table.rows:
        # Find the application name
        item_name = None
        for header in ["application", "app", "app name", "application name", "system", "software", "platform"]:
            if header in row and row[header]:
                item_name = row[header]
                break

        if not item_name:
            logger.warning(f"Skipping row without application name: {row}")
            continue

        # Build details dict
        details = {}
        for header, value in row.items():
            if not value or header == item_name:
                continue

            # Map to standard field name
            std_field = header_mapping.get(header.lower(), header.lower().replace(" ", "_"))

            # Skip the item field itself
            if std_field == "item":
                continue

            # Normalize numeric fields (cost, user counts)
            if std_field in ('user_count', 'annual_cost', 'license_count'):
                normalized = _normalize_numeric(value)

                # Special handling for annual_cost to track data quality
                if std_field == 'annual_cost':
                    # Use shared utility for consistent cost_status inference
                    vendor_name = details.get('vendor', '')
                    cost_status, cost_note = infer_cost_status(
                        cost_value=normalized,
                        vendor_name=vendor_name,
                        original_value=value
                    )
                    details['cost_status'] = cost_status
                    if cost_note:  # Only store note if non-empty
                        details['cost_quality_note'] = cost_note

                    # Store the normalized cost if it's not None
                    if normalized is not None:
                        details[std_field] = normalized
                else:
                    # Non-cost numeric fields (user_count, license_count)
                    if normalized is None:
                        continue  # Skip null-equivalent values
                    details[std_field] = normalized
            else:
                details[std_field] = value

        # Use confidence-aware lookup from app_category_mappings
        from stores.app_category_mappings import categorize_app
        category, mapping, confidence, inferred_from = categorize_app(item_name)

        # SPEC: Extract canonical vendor from AppMapping if available (vendor normalization)
        # This prevents fingerprint collisions from inconsistent vendor data in source PDFs
        canonical_vendor = details.get("vendor", "")
        if mapping and confidence in ("high", "medium"):
            # Use canonical vendor from AppMapping for known apps
            canonical_vendor = mapping.vendor
            if canonical_vendor != details.get("vendor", ""):
                logger.debug(f"Normalized vendor for '{item_name}': '{details.get('vendor', '')}' → '{canonical_vendor}'")
        elif not canonical_vendor:
            # Log apps with missing vendor for manual review
            logger.warning(f"Application '{item_name}' has no vendor in table and no mapping")

        # If no mapping found, try keyword-based inference from category_detail
        cat_detail = details.get("category_detail", "").lower()
        if category == "unknown" and cat_detail:
            if "erp" in cat_detail:
                category = "erp"
            elif "crm" in cat_detail or "agency" in cat_detail:
                category = "crm"
            elif "hr" in cat_detail or "hcm" in cat_detail:
                category = "hcm"
            elif "custom" in cat_detail or "proprietary" in cat_detail:
                category = "custom"
            elif "integration" in cat_detail or "middleware" in cat_detail:
                category = "integration"
            elif "database" in cat_detail or "db" in cat_detail:
                category = "database"
            # NEW branches for verticals:
            elif any(kw in cat_detail for kw in ("insurance", "policy", "claims", "underwriting", "billing engine")):
                category = "industry_vertical"
            elif any(kw in cat_detail for kw in ("healthcare", "ehr", "clinical", "medical", "patient")):
                category = "industry_vertical"
            elif any(kw in cat_detail for kw in ("manufacturing", "mes", "scada", "plm", "cad", "cam")):
                category = "industry_vertical"
            elif any(kw in cat_detail for kw in ("retail", "pos", "point of sale", "ecommerce", "warehouse")):
                category = "industry_vertical"
            elif any(kw in cat_detail for kw in ("security", "siem", "edr", "mfa", "iam")):
                category = "security"
            elif any(kw in cat_detail for kw in ("analytics", "bi", "reporting", "dashboard")):
                category = "bi_analytics"
            elif any(kw in cat_detail for kw in ("collaboration", "chat", "video", "meeting")):
                category = "collaboration"
            elif any(kw in cat_detail for kw in ("saas", "cloud", "subscription")):
                category = "saas"

            if category != "unknown":
                confidence = "low"
                inferred_from = "keyword_inference"

        # Store provenance in the fact details dict
        details["source_category"] = cat_detail  # Raw from document
        details["category_confidence"] = confidence
        details["category_inferred_from"] = inferred_from

        # Create evidence from the row data
        evidence = {
            "exact_quote": f"{item_name} | {details.get('vendor', 'N/A')} | {details.get('version', 'N/A')}",
            "source_section": "Application Inventory Table"
        }

        # Log vendor normalization for monitoring
        if mapping and canonical_vendor != details.get("vendor", ""):
            print(f"[VENDOR FIX] Normalized '{item_name}': '{details.get('vendor', 'N/A')}' → '{canonical_vendor}'")
            logger.info(f"Vendor normalized: {item_name} | Table: '{details.get('vendor', 'N/A')}' → Canonical: '{canonical_vendor}'")

        # Add to FactStore
        try:
            fact_id = fact_store.add_fact(
                domain="applications",
                category=category,
                item=item_name,
                details=details,
                status="documented",
                evidence=evidence,
                entity=entity,
                source_document=source_document,
                needs_review=False
            )
            facts_created += 1
            logger.debug(f"Created fact {fact_id}: {item_name}")

            # Spec 03: Also create inventory item if store available
            if inventory_store is not None and fact_id:
                try:
                    inv_data = {
                        "name": item_name,
                        "vendor": canonical_vendor,  # Use normalized vendor (not raw from table)
                        "version": details.get("version", ""),
                        "hosting": details.get("deployment", ""),
                        "users": details.get("user_count", ""),
                        "cost": details.get("annual_cost", ""),
                        "cost_status": details.get("cost_status"),  # Don't default to "" - use None
                        "cost_quality_note": details.get("cost_quality_note"),  # Don't default to "" - use None
                        "criticality": details.get("criticality", ""),
                        "category": category,
                        "source_category": details.get("source_category", ""),
                        "category_confidence": details.get("category_confidence", ""),
                        "category_inferred_from": details.get("category_inferred_from", ""),
                    }
                    # Remove empty values, but preserve None for cost_status/note (explicit absence)
                    inv_data = {k: v for k, v in inv_data.items() if v is not None and v != ""}

                    inv_item_id = inventory_store.add_item(
                        inventory_type="application",
                        entity=entity,
                        data=inv_data,
                        source_file=source_document,
                        source_type="discovery",
                        deal_id=fact_store.deal_id,
                    )
                    print(f"[INVENTORY] Added app '{item_name}' as {inv_item_id} (vendor: {canonical_vendor}, entity: {entity})")

                    # Bidirectional linking
                    if inv_item_id:
                        # Link fact -> inventory
                        fact = fact_store.get_fact(fact_id)
                        if fact:
                            fact.inventory_item_id = inv_item_id

                        # Link inventory -> fact
                        inv_item = inventory_store.get_item(inv_item_id)
                        if inv_item:
                            if fact_id not in inv_item.source_fact_ids:
                                inv_item.source_fact_ids.append(fact_id)

                        logger.debug(f"Linked fact {fact_id} <-> inventory {inv_item_id}")
                except Exception as inv_e:
                    logger.warning(f"Failed to create inventory item for {item_name}: {inv_e}")

        except Exception as e:
            logger.error(f"Failed to create fact for {item_name}: {e}")

    return facts_created


def _infra_table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str,
    source_document: str,
    inventory_store: Optional["InventoryStore"] = None,
) -> int:
    """Convert infrastructure inventory table to facts (and optionally inventory items)."""
    facts_created = 0

    header_mapping = {
        "server": "item",
        "hostname": "item",
        "host": "item",
        "name": "item",
        "ip": "ip_address",
        "ip address": "ip_address",
        "os": "operating_system",
        "operating system": "operating_system",
        "cpu": "cpu",
        "cores": "cpu_cores",
        "memory": "memory",
        "ram": "memory",
        "storage": "storage",
        "disk": "storage",
        "location": "location",
        "datacenter": "datacenter",
        "data center": "datacenter",
        "environment": "environment",
        "env": "environment",
        "type": "server_type",
        "role": "role",
        "function": "function",
    }

    for row in table.rows:
        # Find the server/host name
        item_name = None
        for header in ["server", "hostname", "host", "name"]:
            if header in row and row[header]:
                item_name = row[header]
                break

        if not item_name:
            continue

        # Build details
        details = {}
        for header, value in row.items():
            if not value:
                continue
            std_field = header_mapping.get(header.lower(), header.lower().replace(" ", "_"))
            if std_field != "item":
                details[std_field] = value

        # Determine category
        category = "compute"  # Default
        if any(k in details for k in ["storage", "disk", "san", "nas"]):
            category = "storage"
        elif "backup" in item_name.lower() or "dr" in item_name.lower():
            category = "backup_dr"

        evidence = {
            "exact_quote": f"{item_name} | {details.get('operating_system', 'N/A')} | {details.get('environment', 'N/A')}",
            "source_section": "Infrastructure Inventory Table"
        }

        try:
            fact_id = fact_store.add_fact(
                domain="infrastructure",
                category=category,
                item=item_name,
                details=details,
                status="documented",
                evidence=evidence,
                entity=entity,
                source_document=source_document
            )
            facts_created += 1

            # Spec 03: Also create inventory item if store available
            if inventory_store is not None and fact_id:
                try:
                    inv_data = {
                        "name": item_name,
                        "type": details.get("server_type", ""),
                        "os": details.get("operating_system", ""),
                        "environment": details.get("environment", ""),
                        "ip": details.get("ip_address", ""),
                        "location": details.get("location", "") or details.get("datacenter", ""),
                        "cpu": details.get("cpu", "") or details.get("cpu_cores", ""),
                        "memory": details.get("memory", ""),
                        "storage": details.get("storage", ""),
                    }
                    inv_data = {k: v for k, v in inv_data.items() if v}

                    inv_item_id = inventory_store.add_item(
                        inventory_type="infrastructure",
                        entity=entity,
                        data=inv_data,
                        source_file=source_document,
                        source_type="discovery",
                        deal_id=fact_store.deal_id,
                    )

                    if inv_item_id:
                        fact = fact_store.get_fact(fact_id)
                        if fact:
                            fact.inventory_item_id = inv_item_id
                        inv_item = inventory_store.get_item(inv_item_id)
                        if inv_item:
                            if fact_id not in inv_item.source_fact_ids:
                                inv_item.source_fact_ids.append(fact_id)
                        logger.debug(f"Linked infra fact {fact_id} <-> inventory {inv_item_id}")
                except Exception as inv_e:
                    logger.warning(f"Failed to create infra inventory item for {item_name}: {inv_e}")

        except Exception as e:
            logger.error(f"Failed to create infra fact for {item_name}: {e}")

    return facts_created


def _contract_table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str,
    source_document: str,
    inventory_store: Optional["InventoryStore"] = None,
) -> int:
    """Convert contract/vendor table to facts (and optionally inventory items)."""
    facts_created = 0

    for row in table.rows:
        # Find vendor/contract name
        item_name = None
        for header in ["vendor", "supplier", "contract", "name"]:
            if header in row and row[header]:
                item_name = row[header]
                break

        if not item_name:
            continue

        details = {k: v for k, v in row.items() if v and k.lower() != item_name.lower()}

        evidence = {
            "exact_quote": f"{item_name} contract",
            "source_section": "Contract/Vendor Table"
        }

        try:
            # Contracts could go to applications (SaaS) or organization (vendor management)
            fact_id = fact_store.add_fact(
                domain="organization",
                category="outsourcing",
                item=f"{item_name} Contract",
                details=details,
                status="documented",
                evidence=evidence,
                entity=entity,
                source_document=source_document
            )
            facts_created += 1

            # Spec 03: Also create inventory item if store available
            if inventory_store is not None and fact_id:
                try:
                    inv_data = {
                        "name": item_name,
                        "contract_type": details.get("contract", ""),
                        "start_date": details.get("start_date", "") or details.get("start date", ""),
                        "end_date": details.get("end_date", "") or details.get("end date", "") or details.get("expiration", ""),
                        "acv": details.get("acv", "") or details.get("annual_value", ""),
                        "tcv": details.get("tcv", ""),
                    }
                    inv_data = {k: v for k, v in inv_data.items() if v}

                    inv_item_id = inventory_store.add_item(
                        inventory_type="vendor",
                        entity=entity,
                        data=inv_data,
                        source_file=source_document,
                        source_type="discovery",
                        deal_id=fact_store.deal_id,
                    )

                    if inv_item_id:
                        fact = fact_store.get_fact(fact_id)
                        if fact:
                            fact.inventory_item_id = inv_item_id
                        inv_item = inventory_store.get_item(inv_item_id)
                        if inv_item:
                            if fact_id not in inv_item.source_fact_ids:
                                inv_item.source_fact_ids.append(fact_id)
                        logger.debug(f"Linked contract fact {fact_id} <-> inventory {inv_item_id}")
                except Exception as inv_e:
                    logger.warning(f"Failed to create vendor inventory item for {item_name}: {inv_e}")

        except Exception as e:
            logger.error(f"Failed to create contract fact for {item_name}: {e}")

    return facts_created


def _org_table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str,
    source_document: str,
    inventory_store: Optional["InventoryStore"] = None,
) -> int:
    """Convert organization/staffing table to facts (and optionally inventory items).

    Handles tables with team/role data: Team Summary, Role Breakdown,
    IT Org Structure, Staffing tables.
    """
    facts_created = 0

    header_mapping = {
        # Team/group identifiers
        "team": "item",
        "team name": "item",
        "department": "item",
        "group": "item",
        "function": "item",
        # Role identifiers (if team not present)
        "role": "role",
        "title": "role",
        "job title": "role",
        "position": "role",
        # Person name
        "name": "person_name",
        "lead": "person_name",
        "leader": "person_name",
        "director": "person_name",
        "vp": "person_name",
        # Staffing numbers
        "headcount": "headcount",
        "hc": "headcount",
        "head count": "headcount",
        "fte": "fte",
        "ftes": "fte",
        # Reporting
        "reports to": "reports_to",
        "reporting to": "reports_to",
        "manager": "reports_to",
        "reports": "reports_to",
        # Other
        "location": "location",
        "office": "location",
        "site": "location",
        "responsibilities": "responsibilities",
        "scope": "responsibilities",
        "focus area": "responsibilities",
    }

    for row in table.rows:
        # Find the team/role name (primary identifier)
        item_name = None

        # Priority: team name > role > person name
        for header in ["team", "team name", "department", "group", "function"]:
            if header in row and row[header]:
                item_name = row[header]
                break

        if not item_name:
            for header in ["role", "title", "job title", "position"]:
                if header in row and row[header]:
                    item_name = row[header]
                    break

        if not item_name:
            for header in ["name", "lead", "leader"]:
                if header in row and row[header]:
                    item_name = row[header]
                    break

        if not item_name:
            logger.warning(f"Skipping org row without identifiable name: {row}")
            continue

        # Build details
        details = {}
        for header, value in row.items():
            if not value:
                continue
            std_field = header_mapping.get(header.lower(), header.lower().replace(" ", "_"))
            if std_field == "item":
                continue  # Skip the name field itself
            # Normalize numeric fields
            if std_field in ("headcount", "fte"):
                normalized = _normalize_numeric(value)
                if normalized is not None:
                    details[std_field] = normalized
            else:
                details[std_field] = value

        # Determine category based on content
        category = "central_it"  # Default

        # If this table has a "team" column, treat all rows as teams (central_it)
        # Don't apply keyword-based categorization which is meant for role tables
        has_team_column = any(h in table.headers for h in ["team", "team name", "department", "group", "function"])

        if not has_team_column:
            # Only apply keyword categorization for non-team tables (e.g., role tables)
            item_lower = item_name.lower()
            if any(kw in item_lower for kw in ["leader", "cio", "cto", "vp", "director", "head of"]):
                category = "leadership"
            elif any(kw in item_lower for kw in ["outsourc", "msp", "managed service", "contractor"]):
                category = "outsourcing"
            elif any(kw in item_lower for kw in ["embed", "shadow", "business"]):
                category = "embedded_it"

        evidence = {
            "exact_quote": f"{item_name} | HC: {details.get('headcount', 'N/A')} | FTE: {details.get('fte', 'N/A')}",
            "source_section": "Organization/Staffing Table"
        }

        try:
            fact_id = fact_store.add_fact(
                domain="organization",
                category=category,
                item=item_name,
                details=details,
                status="documented",
                evidence=evidence,
                entity=entity,
                source_document=source_document,
                needs_review=False,
            )
            facts_created += 1
            logger.debug(f"Created org fact {fact_id}: {item_name}")

            # Create inventory item if store available (Spec 03 linking)
            if inventory_store is not None and fact_id:
                try:
                    inv_data = {
                        "role": details.get("role", item_name),
                        "name": details.get("person_name", ""),
                        "team": item_name if category == "central_it" else "",
                        "department": "IT",
                        "headcount": details.get("headcount", ""),
                        "fte": details.get("fte", ""),
                        "location": details.get("location", ""),
                        "reports_to": details.get("reports_to", ""),
                        "responsibilities": details.get("responsibilities", ""),
                    }
                    # Remove empty values
                    inv_data = {k: v for k, v in inv_data.items() if v}

                    # Ensure required 'role' field is present
                    if "role" not in inv_data:
                        inv_data["role"] = item_name

                    inv_item_id = inventory_store.add_item(
                        inventory_type="organization",
                        entity=entity,
                        data=inv_data,
                        source_file=source_document,
                        source_type="discovery",
                        deal_id=fact_store.deal_id,
                    )

                    # Bidirectional linking
                    if inv_item_id:
                        fact = fact_store.get_fact(fact_id)
                        if fact:
                            fact.inventory_item_id = inv_item_id
                        inv_item = inventory_store.get_item(inv_item_id)
                        if inv_item:
                            if fact_id not in inv_item.source_fact_ids:
                                inv_item.source_fact_ids.append(fact_id)
                        logger.debug(f"Linked org fact {fact_id} <-> inventory {inv_item_id}")

                except Exception as inv_e:
                    logger.warning(f"Failed to create org inventory item for {item_name}: {inv_e}")

        except Exception as e:
            logger.error(f"Failed to create org fact for {item_name}: {e}")

    return facts_created


# =============================================================================
# MAIN PREPROCESSING FUNCTION
# =============================================================================

def preprocess_document(
    document_text: str,
    fact_store: "FactStore",
    entity: str = "target",
    source_document: str = "",
    inventory_store: Optional["InventoryStore"] = None,
) -> ParserResult:
    """
    Preprocess a document: extract structured tables deterministically,
    return remaining unstructured text for LLM discovery.

    Args:
        document_text: Full document text
        fact_store: FactStore instance
        entity: "target" or "buyer"
        source_document: Source filename
        inventory_store: Optional InventoryStore for bidirectional linking (Spec 03)

    Returns:
        ParserResult with tables parsed, facts created, and remaining text
    """
    result = ParserResult()

    # ENTITY EXTRACTION (Doc 01: Entity Propagation Hardening)
    # Try to extract entity from document context
    extracted_entity = extract_document_entity(
        section_text=document_text[:2000],  # Use first 2000 chars for section header detection
        headers=[],  # Will be filled per-table later
        filename=source_document,
        metadata=None
    )

    # Use extracted entity if found, otherwise use parameter default
    if extracted_entity and extracted_entity != "per_row":
        if entity != "target" and extracted_entity != entity:
            logger.warning(
                f"Entity mismatch: extracted '{extracted_entity}' from document, "
                f"but parameter specified '{entity}'. Using extracted value."
            )
        entity = extracted_entity
        logger.info(f"Extracted entity from document: {entity}")
    elif extracted_entity is None:
        logger.info(f"No entity extracted from document, using parameter default: {entity}")
    # If extracted_entity == "per_row", it will be handled per-table

    # Extract all markdown tables
    table_tuples = extract_markdown_tables(document_text)

    logger.info(f"Found {len(table_tuples)} markdown tables in document")

    # Track positions to remove from text
    positions_to_remove = []

    for table_text, start_pos, end_pos in table_tuples:
        # Parse the table
        parsed = parse_markdown_table(table_text)

        if parsed is None:
            result.errors.append(f"Failed to parse table at position {start_pos}")
            continue

        # Check if table has entity column (per-row entity)
        table_entity_check = extract_document_entity(
            section_text="",
            headers=parsed.headers,
            filename=None
        )

        if table_entity_check == "per_row":
            # Table has entity column - entity will be per-row
            parsed.entity = "per_row"
            logger.info("Table has Entity column - will split by entity per row")
        else:
            # Use document-level entity
            parsed.entity = entity

        # Detect type
        table_type = detect_table_type(parsed)
        parsed.table_type = table_type

        if table_type == "unknown":
            logger.info(f"Skipping unknown table type: {parsed.headers[:5]}")
            continue

        # Convert to facts (and optionally inventory items)
        facts_created = table_to_facts(
            table=parsed,
            fact_store=fact_store,
            entity=entity,
            source_document=source_document,
            inventory_store=inventory_store,
        )

        result.facts_created += facts_created
        result.tables.append(parsed)
        positions_to_remove.append((start_pos, end_pos))

        logger.info(f"Parsed {table_type}: {len(parsed.rows)} rows -> {facts_created} facts")

    # Build remaining text (remove parsed tables)
    # Sort positions in reverse order to remove from end first
    positions_to_remove.sort(key=lambda x: x[0], reverse=True)

    remaining = document_text
    for start, end in positions_to_remove:
        # Replace table with a marker so context isn't lost
        remaining = remaining[:start] + f"\n[TABLE PARSED: {result.tables[-1].table_type if result.tables else 'unknown'}]\n" + remaining[end:]

    result.remaining_text = remaining

    return result


# =============================================================================
# UTILITY: VALIDATION
# =============================================================================

def validate_extraction(
    table: ParsedTable,
    expected_count: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Validate that extraction was complete.

    Args:
        table: Parsed table
        expected_count: Expected row count (if known from document)

    Returns:
        (is_valid, message)
    """
    actual_count = len(table.rows)

    if expected_count is not None:
        if actual_count == expected_count:
            return True, f"Extracted {actual_count} rows (matches expected)"
        else:
            return False, f"Extracted {actual_count} rows, expected {expected_count}"

    # Basic sanity checks
    if actual_count == 0:
        return False, "No rows extracted"

    if actual_count < MIN_COLUMNS_FOR_INVENTORY:
        return False, f"Only {actual_count} rows - may be incomplete"

    return True, f"Extracted {actual_count} rows"


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python deterministic_parser.py <markdown_file>")
        sys.exit(1)

    # Read file
    with open(sys.argv[1], 'r') as f:
        text = f.read()

    # Extract tables
    tables = extract_markdown_tables(text)
    print(f"\nFound {len(tables)} tables\n")

    for i, (table_text, start, end) in enumerate(tables):
        print(f"{'='*60}")
        print(f"TABLE {i+1} (pos {start}-{end})")
        print(f"{'='*60}")

        parsed = parse_markdown_table(table_text)
        if parsed:
            table_type = detect_table_type(parsed)
            print(f"Type: {table_type}")
            print(f"Headers: {parsed.headers}")
            print(f"Rows: {len(parsed.rows)}")
            print(f"\nFirst 3 rows:")
            for row in parsed.rows[:3]:
                print(f"  {row}")
        else:
            print("Failed to parse")

        print()
