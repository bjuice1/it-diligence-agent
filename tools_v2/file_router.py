"""
File Router

Main entry point for ingesting files into the inventory system.
Routes files through appropriate parsers and into InventoryStore.

Supports:
- Excel (.xlsx, .xls)
- Word (.docx)
- Markdown (.md)
- CSV (.csv)
- Text (.txt) - treated as prose only
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from tools_v2.parsers.models import (
    ParseResult, ParsedTable, IngestResult, TableInfo, ValidationResult
)
from tools_v2.parsers.excel_parser import parse_excel_workbook, parse_csv
from tools_v2.parsers.word_parser import parse_word_document
from tools_v2.parsers.markdown_parser import parse_markdown_file, parse_markdown
from tools_v2.parsers.type_detector import detect_inventory_type, map_headers_to_schema
from tools_v2.parsers.schema_validator import validate_table, normalize_row

from stores.inventory_store import InventoryStore
from stores.inventory_item import MergeResult
from tools_v2.enrichment.inventory_reviewer import review_inventory, ReviewResult

logger = logging.getLogger(__name__)

# Supported file extensions and their parsers
FILE_PARSERS = {
    '.xlsx': parse_excel_workbook,
    '.xls': parse_excel_workbook,
    '.docx': parse_word_document,
    '.md': parse_markdown_file,
    '.csv': parse_csv,
}

# Minimum confidence to auto-assign inventory type
MIN_DETECTION_CONFIDENCE = 0.4


def ingest_file(
    file_path: Path,
    inventory_store: InventoryStore,
    entity: str = "target",
    fact_store: Optional["FactStore"] = None,
    run_llm_discovery: bool = False,
    api_key: str = "",
    min_confidence: float = MIN_DETECTION_CONFIDENCE,
) -> IngestResult:
    """
    Ingest a file into the inventory system.

    Routes file content appropriately:
    - Tables with known inventory type -> InventoryStore
    - Tables with unknown type -> logged, returned in result
    - Prose content -> optionally sent to LLM discovery

    Args:
        file_path: Path to file to ingest
        inventory_store: InventoryStore to add items to
        entity: "target" or "buyer"
        fact_store: Optional FactStore for LLM-extracted facts
        run_llm_discovery: Whether to run LLM discovery on prose
        api_key: Anthropic API key (required if run_llm_discovery=True)
        min_confidence: Minimum confidence for auto-assigning type

    Returns:
        IngestResult with processing statistics
    """
    file_path = Path(file_path)
    result = IngestResult(
        source_file=file_path.name,
    )

    # Determine file type
    suffix = file_path.suffix.lower()
    result.file_type = suffix.lstrip('.')

    if suffix not in FILE_PARSERS:
        # Handle plain text
        if suffix in ['.txt']:
            result = _handle_text_file(file_path, result, fact_store, run_llm_discovery, api_key, entity)
            return result
        else:
            result.errors.append(f"Unsupported file type: {suffix}")
            return result

    # Parse the file
    parser = FILE_PARSERS[suffix]
    try:
        parse_result = parser(file_path)
    except Exception as e:
        result.errors.append(f"Failed to parse file: {str(e)}")
        logger.exception(f"Parse error for {file_path}")
        return result

    # Handle parse errors
    result.errors.extend(parse_result.errors)
    result.validation_warnings.extend(parse_result.warnings)

    if parse_result.errors:
        return result

    # Process tables
    for table in parse_result.tables:
        _process_table(
            table=table,
            inventory_store=inventory_store,
            entity=entity,
            result=result,
            min_confidence=min_confidence,
        )

    # Handle prose content
    if parse_result.has_prose:
        result.prose_length = len(parse_result.prose)

        if run_llm_discovery and fact_store and api_key:
            result.prose_sent_to_llm = True
            facts_count = _run_llm_discovery(
                prose=parse_result.prose,
                fact_store=fact_store,
                entity=entity,
                source_file=file_path.name,
                api_key=api_key,
            )
            result.facts_extracted = facts_count

    return result


def _process_table(
    table: ParsedTable,
    inventory_store: InventoryStore,
    entity: str,
    result: IngestResult,
    min_confidence: float,
) -> None:
    """Process a single table into inventory items."""

    # Check if type was detected with sufficient confidence
    if not table.detected_type or table.detected_type == "unknown":
        result.unknown_tables.append(TableInfo(
            table_index=table.table_index,
            headers=table.headers,
            row_count=table.row_count,
            sheet_name=table.sheet_name,
            reason_skipped="Could not detect inventory type",
        ))
        return

    if table.detection_confidence < min_confidence:
        result.unknown_tables.append(TableInfo(
            table_index=table.table_index,
            headers=table.headers,
            row_count=table.row_count,
            sheet_name=table.sheet_name,
            reason_skipped=f"Low confidence ({table.detection_confidence:.1%})",
        ))
        return

    inv_type = table.detected_type

    # Validate against schema
    validation = validate_table(table, inv_type)

    if not validation.is_valid:
        result.validation_warnings.extend(validation.errors)
        # Still try to import - might have partial data

    result.validation_warnings.extend(validation.warnings)

    # Get header mapping
    header_map = map_headers_to_schema(table.headers, inv_type)

    # Add each row to inventory
    added = 0
    for row in table.rows:
        # Normalize row to use schema field names
        normalized = normalize_row(row, inv_type, header_map)

        try:
            item_id = inventory_store.add_item(
                inventory_type=inv_type,
                data=normalized,
                entity=entity,
                source_file=table.source_file,
                source_type="import",
            )
            added += 1
        except Exception as e:
            result.errors.append(f"Failed to add row: {str(e)}")

    # Update result counts
    if inv_type not in result.by_type:
        result.by_type[inv_type] = 0
    result.by_type[inv_type] += added
    result.inventory_items_added += added


def _handle_text_file(
    file_path: Path,
    result: IngestResult,
    fact_store: Optional["FactStore"],
    run_llm_discovery: bool,
    api_key: str,
    entity: str,
) -> IngestResult:
    """Handle plain text files (prose only)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        result.prose_length = len(text)

        if run_llm_discovery and fact_store and api_key and len(text.strip()) > 100:
            result.prose_sent_to_llm = True
            facts_count = _run_llm_discovery(
                prose=text,
                fact_store=fact_store,
                entity=entity,
                source_file=file_path.name,
                api_key=api_key,
            )
            result.facts_extracted = facts_count

    except Exception as e:
        result.errors.append(f"Failed to read text file: {str(e)}")

    return result


def _run_llm_discovery(
    prose: str,
    fact_store: "FactStore",
    entity: str,
    source_file: str,
    api_key: str,
) -> int:
    """
    Run LLM discovery on prose content.

    Returns number of facts extracted.
    """
    # This would integrate with the existing discovery agents
    # For now, return 0 - actual implementation would call the agents
    logger.info(f"LLM discovery requested for {len(prose)} chars from {source_file}")

    # TODO: Integrate with existing discovery agents
    # from tools_v2.preprocessing_router import run_hybrid_discovery
    # result = run_hybrid_discovery(prose, fact_store, source_file, entity, api_key)
    # return result.get("llm_facts", 0)

    return 0


def ingest_directory(
    dir_path: Path,
    inventory_store: InventoryStore,
    entity: str = "target",
    recursive: bool = False,
    extensions: Optional[List[str]] = None,
) -> Dict[str, IngestResult]:
    """
    Ingest all supported files from a directory.

    Args:
        dir_path: Directory path
        inventory_store: InventoryStore to add items to
        entity: "target" or "buyer"
        recursive: Whether to search subdirectories
        extensions: List of extensions to process (default: all supported)

    Returns:
        Dict mapping filename -> IngestResult
    """
    dir_path = Path(dir_path)
    results = {}

    if not dir_path.is_dir():
        logger.error(f"Not a directory: {dir_path}")
        return results

    # Determine which extensions to process
    if extensions:
        allowed = {ext if ext.startswith('.') else f'.{ext}' for ext in extensions}
    else:
        allowed = set(FILE_PARSERS.keys()) | {'.txt'}

    # Find files
    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"

    for file_path in dir_path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in allowed:
            logger.info(f"Ingesting: {file_path.name}")
            result = ingest_file(file_path, inventory_store, entity)
            results[file_path.name] = result

    return results


def reimport_file(
    file_path: Path,
    inventory_store: InventoryStore,
    entity: str = "target",
    merge_strategy: str = "smart",
) -> IngestResult:
    """
    Re-import a file, merging with existing inventory data.

    Args:
        file_path: Path to file
        inventory_store: Existing InventoryStore
        entity: "target" or "buyer"
        merge_strategy: "add_new", "update", or "smart"

    Returns:
        IngestResult with merge statistics
    """
    # Create temporary store for new data
    temp_store = InventoryStore()

    # Ingest into temp store
    ingest_result = ingest_file(file_path, temp_store, entity)

    if ingest_result.errors:
        return ingest_result

    # Merge into main store
    merge_result = inventory_store.merge_from(temp_store, strategy=merge_strategy)

    # Update ingest result with merge info
    ingest_result.inventory_items_added = merge_result.added
    ingest_result.inventory_items_updated = merge_result.updated
    ingest_result.inventory_items_unchanged = merge_result.unchanged

    return ingest_result


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """
    Analyze a file without importing it.

    Useful for previewing what would be imported.

    Args:
        file_path: Path to file

    Returns:
        Analysis dict with table info, detected types, etc.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    analysis = {
        "file": file_path.name,
        "file_type": suffix.lstrip('.'),
        "tables": [],
        "total_rows": 0,
        "has_prose": False,
        "prose_length": 0,
        "detected_types": {},
        "errors": [],
    }

    if suffix not in FILE_PARSERS:
        if suffix == '.txt':
            try:
                with open(file_path, 'r') as f:
                    text = f.read()
                analysis["has_prose"] = True
                analysis["prose_length"] = len(text)
            except Exception as e:
                analysis["errors"].append(str(e))
        else:
            analysis["errors"].append(f"Unsupported file type: {suffix}")
        return analysis

    # Parse file
    parser = FILE_PARSERS[suffix]
    try:
        parse_result = parser(file_path)
    except Exception as e:
        analysis["errors"].append(f"Parse error: {str(e)}")
        return analysis

    analysis["has_prose"] = parse_result.has_prose
    analysis["prose_length"] = len(parse_result.prose)

    for table in parse_result.tables:
        table_info = {
            "index": table.table_index,
            "sheet": table.sheet_name,
            "headers": table.headers,
            "row_count": table.row_count,
            "detected_type": table.detected_type,
            "confidence": table.detection_confidence,
        }
        analysis["tables"].append(table_info)
        analysis["total_rows"] += table.row_count

        # Count by type
        t = table.detected_type or "unknown"
        if t not in analysis["detected_types"]:
            analysis["detected_types"][t] = 0
        analysis["detected_types"][t] += table.row_count

    return analysis


def enrich_inventory(
    inventory_store: InventoryStore,
    api_key: str,
    inventory_types: Optional[List[str]] = None,
    entity: str = "target",
    skip_enriched: bool = True,
) -> Dict[str, ReviewResult]:
    """
    Run LLM-based enrichment on inventory items.

    For each item, the LLM:
    - Looks up what the application/system is
    - Adds a description if it knows the product
    - Flags items as "needs_investigation" if uncertain

    Args:
        inventory_store: The inventory store to enrich
        api_key: Anthropic API key
        inventory_types: List of types to enrich (default: ["application"])
        entity: Entity filter ("target" or "buyer")
        skip_enriched: Skip items that already have enrichment

    Returns:
        Dict mapping inventory_type -> ReviewResult
    """
    if inventory_types is None:
        inventory_types = ["application"]

    results = {}

    for inv_type in inventory_types:
        logger.info(f"Enriching {inv_type} inventory...")

        result = review_inventory(
            inventory_store=inventory_store,
            api_key=api_key,
            inventory_type=inv_type,
            entity=entity,
            skip_enriched=skip_enriched,
        )

        results[inv_type] = result
        logger.info(
            f"{inv_type}: {result.items_reviewed} reviewed, "
            f"{result.items_enriched} enriched, "
            f"{result.items_flagged} flagged"
        )

    return results


def ingest_and_enrich(
    file_path: Path,
    inventory_store: InventoryStore,
    api_key: str,
    entity: str = "target",
    enrich_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Convenience function: ingest a file and enrich in one step.

    Args:
        file_path: Path to file to ingest
        inventory_store: InventoryStore to add items to
        api_key: Anthropic API key
        entity: "target" or "buyer"
        enrich_types: Inventory types to enrich (default: ["application"])

    Returns:
        Dict with ingest_result and enrich_results
    """
    # Ingest
    ingest_result = ingest_file(file_path, inventory_store, entity)

    # Enrich
    enrich_results = {}
    if not ingest_result.errors and api_key:
        enrich_results = enrich_inventory(
            inventory_store=inventory_store,
            api_key=api_key,
            inventory_types=enrich_types,
            entity=entity,
            skip_enriched=True,
        )

    return {
        "ingest": ingest_result,
        "enrich": enrich_results,
    }
