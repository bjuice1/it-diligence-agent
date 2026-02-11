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
    "application", "app", "app name", "application name", "system", "software", "platform",
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

# Column headers that indicate organization/staffing table
ORG_INVENTORY_HEADERS = {
    "team", "team name", "department", "group", "function",
    "role", "title", "job title", "position",
    "headcount", "hc", "head count", "fte", "ftes",
    "reports to", "reporting to", "manager", "reports",
    "location", "office", "site",
    "responsibilities", "scope", "focus area",
    "name", "lead", "leader", "director", "vp",
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

    # Find highest scoring type with minimum threshold of 3
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score >= 3:
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
                        "criticality": details.get("criticality", ""),
                        "category": category,
                        "source_category": details.get("source_category", ""),
                        "category_confidence": details.get("category_confidence", ""),
                        "category_inferred_from": details.get("category_inferred_from", ""),
                    }
                    # Remove empty values
                    inv_data = {k: v for k, v in inv_data.items() if v}

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
