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

logger = logging.getLogger(__name__)


@dataclass
class ParsedTable:
    """Represents a parsed markdown table"""
    headers: List[str]
    rows: List[Dict[str, str]]
    table_type: Optional[str] = None  # "application_inventory", "infrastructure", etc.
    source_section: str = ""
    raw_text: str = ""


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
    "application", "app", "app name", "application name", "system", "software",
    "vendor", "category", "version", "hosting", "deployment", "users",
    "user count", "annual cost", "cost", "criticality", "critical"
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
    headers = _split_row(lines[0])
    headers = [_normalize_header(h) for h in headers]

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
                row_dict[header] = _clean_cell_value(value)

        if any(v for v in row_dict.values()):  # Skip completely empty rows
            rows.append(row_dict)

    if not rows:
        return None

    return ParsedTable(
        headers=headers,
        rows=rows,
        raw_text=table_text
    )


def _normalize_header(header: str) -> str:
    """Normalize a header name for consistent matching"""
    # Remove markdown formatting
    header = re.sub(r'\*+', '', header)  # Remove bold/italic markers
    header = header.strip().lower()
    return header


def _clean_cell_value(value: str) -> str:
    """Clean a cell value"""
    # Remove markdown formatting but preserve the content
    value = re.sub(r'\*\*([^*]+)\*\*', r'\1', value)  # **bold** -> bold
    value = re.sub(r'\*([^*]+)\*', r'\1', value)      # *italic* -> italic

    # Remove citation markers like fileciteturn3file0L35-L38
    # Also handle unicode citation wrapper characters
    value = re.sub(r'filecite[a-zA-Z0-9\-_]+', '', value)
    value = re.sub(r'[\ue200\ue201\ue202]', '', value)  # Unicode citation wrappers

    # Clean up whitespace
    value = ' '.join(value.split())

    return value.strip()


# =============================================================================
# TABLE TYPE DETECTION
# =============================================================================

def detect_table_type(table: ParsedTable) -> str:
    """
    Detect what type of inventory table this is based on headers.

    Returns:
        "application_inventory", "infrastructure_inventory",
        "contract_inventory", or "unknown"
    """
    headers_lower = {h.lower() for h in table.headers if h}

    # Score each type
    app_score = len(headers_lower & APP_INVENTORY_HEADERS)
    infra_score = len(headers_lower & INFRA_INVENTORY_HEADERS)
    contract_score = len(headers_lower & CONTRACT_HEADERS)

    # Need minimum overlap to classify
    if app_score >= 3 and app_score > infra_score and app_score > contract_score:
        return "application_inventory"
    elif infra_score >= 3 and infra_score > app_score:
        return "infrastructure_inventory"
    elif contract_score >= 3:
        return "contract_inventory"

    return "unknown"


# =============================================================================
# FACTSTORE INTEGRATION
# =============================================================================

def table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str = "target",
    source_document: str = ""
) -> int:
    """
    Convert a parsed table directly into FactStore entries.

    Args:
        table: Parsed markdown table
        fact_store: FactStore instance
        entity: "target" or "buyer"
        source_document: Source filename for traceability

    Returns:
        Number of facts created
    """
    table_type = detect_table_type(table)

    if table_type == "application_inventory":
        return _app_table_to_facts(table, fact_store, entity, source_document)
    elif table_type == "infrastructure_inventory":
        return _infra_table_to_facts(table, fact_store, entity, source_document)
    elif table_type == "contract_inventory":
        return _contract_table_to_facts(table, fact_store, entity, source_document)
    else:
        logger.warning(f"Unknown table type, skipping: headers={table.headers[:5]}")
        return 0


def _app_table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str,
    source_document: str
) -> int:
    """Convert application inventory table to facts"""
    facts_created = 0

    # Map common header variations to standard fields
    header_mapping = {
        # Application name
        "application": "item",
        "app": "item",
        "app name": "item",
        "application name": "item",
        "system": "item",
        "software": "item",
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
        for header in ["application", "app", "app name", "application name", "system", "software"]:
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

            details[std_field] = value

        # Determine category based on category_detail or default
        category = "saas"  # Default
        cat_detail = details.get("category_detail", "").lower()
        if "erp" in cat_detail:
            category = "erp"
        elif "crm" in cat_detail or "agency" in cat_detail:
            category = "crm"
        elif "hr" in cat_detail or "hcm" in cat_detail:
            category = "saas"  # HR apps typically SaaS
        elif "custom" in cat_detail or "proprietary" in cat_detail:
            category = "custom"
        elif "integration" in cat_detail or "middleware" in cat_detail:
            category = "integration"
        elif "database" in cat_detail or "db" in cat_detail:
            category = "database"

        # Create evidence from the row data
        evidence = {
            "exact_quote": f"{item_name} | {details.get('vendor', 'N/A')} | {details.get('version', 'N/A')}",
            "source_section": "Application Inventory Table"
        }

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
                needs_review=False,
                extraction_method="deterministic_parser"  # Track that this was parsed, not LLM-extracted
            )
            facts_created += 1
            logger.debug(f"Created fact {fact_id}: {item_name}")

        except Exception as e:
            logger.error(f"Failed to create fact for {item_name}: {e}")

    return facts_created


def _infra_table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str,
    source_document: str
) -> int:
    """Convert infrastructure inventory table to facts"""
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
                source_document=source_document,
                extraction_method="deterministic_parser"
            )
            facts_created += 1
        except Exception as e:
            logger.error(f"Failed to create infra fact for {item_name}: {e}")

    return facts_created


def _contract_table_to_facts(
    table: ParsedTable,
    fact_store: "FactStore",
    entity: str,
    source_document: str
) -> int:
    """Convert contract/vendor table to facts"""
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
                source_document=source_document,
                extraction_method="deterministic_parser"
            )
            facts_created += 1
        except Exception as e:
            logger.error(f"Failed to create contract fact for {item_name}: {e}")

    return facts_created


# =============================================================================
# MAIN PREPROCESSING FUNCTION
# =============================================================================

def preprocess_document(
    document_text: str,
    fact_store: "FactStore",
    entity: str = "target",
    source_document: str = ""
) -> ParserResult:
    """
    Preprocess a document: extract structured tables deterministically,
    return remaining unstructured text for LLM discovery.

    Args:
        document_text: Full document text
        fact_store: FactStore instance
        entity: "target" or "buyer"
        source_document: Source filename

    Returns:
        ParserResult with tables parsed, facts created, and remaining text
    """
    result = ParserResult()

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

        # Detect type
        table_type = detect_table_type(parsed)
        parsed.table_type = table_type

        if table_type == "unknown":
            logger.info(f"Skipping unknown table type: {parsed.headers[:5]}")
            continue

        # Convert to facts
        facts_created = table_to_facts(
            table=parsed,
            fact_store=fact_store,
            entity=entity,
            source_document=source_document
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
