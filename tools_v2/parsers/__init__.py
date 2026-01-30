"""
Parsers Package

File parsers for the inventory system.
Supports Excel, Word, Markdown, and CSV files.

Main entry point: file_router.ingest_file()
"""

from tools_v2.parsers.models import (
    ParsedTable,
    ParseResult,
    ValidationResult,
    IngestResult,
    TableInfo,
)

from tools_v2.parsers.type_detector import (
    detect_inventory_type,
    detect_with_details,
    suggest_inventory_type,
    map_headers_to_schema,
)

from tools_v2.parsers.schema_validator import (
    validate_table,
    validate_row,
    normalize_row,
    summarize_validation,
)

from tools_v2.parsers.excel_parser import (
    parse_excel_workbook,
    parse_csv,
)

from tools_v2.parsers.word_parser import (
    parse_word_document,
    parse_docx_tables_only,
)

from tools_v2.parsers.markdown_parser import (
    parse_markdown,
    parse_markdown_file,
    extract_markdown_tables,
    parse_markdown_table,
)

__all__ = [
    # Models
    "ParsedTable",
    "ParseResult",
    "ValidationResult",
    "IngestResult",
    "TableInfo",
    # Type detection
    "detect_inventory_type",
    "detect_with_details",
    "suggest_inventory_type",
    "map_headers_to_schema",
    # Validation
    "validate_table",
    "validate_row",
    "normalize_row",
    "summarize_validation",
    # Excel
    "parse_excel_workbook",
    "parse_csv",
    # Word
    "parse_word_document",
    "parse_docx_tables_only",
    # Markdown
    "parse_markdown",
    "parse_markdown_file",
    "extract_markdown_tables",
    "parse_markdown_table",
]
