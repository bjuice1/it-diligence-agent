"""
Shared Data Models for Parsers

Common dataclasses used across all file parsers:
- ParsedTable: A single table extracted from any source
- ParseResult: Complete result from parsing a document
- ValidationResult: Result of schema validation
- IngestResult: Result of ingesting a file into stores
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


@dataclass
class ParsedTable:
    """
    A single table extracted from a document.

    Represents tabular data from Word, Excel, Markdown, or CSV.
    Headers are normalized to lowercase.
    """
    headers: List[str]              # Column headers (lowercase)
    rows: List[Dict[str, Any]]      # List of row dicts {header: value}

    # Source information
    source_file: str = ""           # Original filename
    sheet_name: str = ""            # Excel sheet name (if applicable)
    table_index: int = 0            # Index within document (0-based)

    # Position info (for Word/Markdown)
    start_char: int = 0             # Start position in document
    end_char: int = 0               # End position in document

    # Detection results (filled by type detector)
    detected_type: str = ""         # application, infrastructure, etc.
    detection_confidence: float = 0.0

    # Raw text (for debugging)
    raw_text: str = ""              # Original table text if available

    @property
    def row_count(self) -> int:
        """Number of data rows (excluding header)."""
        return len(self.rows)

    @property
    def column_count(self) -> int:
        """Number of columns."""
        return len(self.headers)

    def get_column_values(self, column: str) -> List[Any]:
        """Get all values for a specific column."""
        col_lower = column.lower()
        return [row.get(col_lower) for row in self.rows]

    def has_column(self, column: str) -> bool:
        """Check if table has a column (case-insensitive)."""
        return column.lower() in self.headers

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "headers": self.headers,
            "rows": self.rows,
            "source_file": self.source_file,
            "sheet_name": self.sheet_name,
            "table_index": self.table_index,
            "detected_type": self.detected_type,
            "detection_confidence": self.detection_confidence,
            "row_count": self.row_count,
        }


@dataclass
class ParseResult:
    """
    Complete result from parsing a document.

    Contains all extracted tables and any remaining prose text.
    """
    tables: List[ParsedTable] = field(default_factory=list)
    prose: str = ""                 # Non-table text content

    # Source info
    source_file: str = ""
    file_type: str = ""             # word, excel, markdown, csv, pdf

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)  # Document properties

    # Processing info
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def table_count(self) -> int:
        """Number of tables found."""
        return len(self.tables)

    @property
    def total_rows(self) -> int:
        """Total rows across all tables."""
        return sum(t.row_count for t in self.tables)

    @property
    def has_prose(self) -> bool:
        """Check if there's meaningful prose content."""
        # More than just whitespace
        return len(self.prose.strip()) > 100

    def get_tables_by_type(self, inventory_type: str) -> List[ParsedTable]:
        """Get tables detected as a specific inventory type."""
        return [t for t in self.tables if t.detected_type == inventory_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_file": self.source_file,
            "file_type": self.file_type,
            "table_count": self.table_count,
            "total_rows": self.total_rows,
            "has_prose": self.has_prose,
            "prose_length": len(self.prose),
            "tables": [t.to_dict() for t in self.tables],
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class ValidationResult:
    """
    Result of validating a table against an inventory schema.
    """
    is_valid: bool = True           # Passes validation (has required fields)
    inventory_type: str = ""        # Type validated against

    # Field analysis
    missing_required: List[str] = field(default_factory=list)
    missing_optional: Dict[str, int] = field(default_factory=dict)  # field -> count missing
    extra_fields: List[str] = field(default_factory=list)  # Fields not in schema

    # Value issues
    empty_required: Dict[str, int] = field(default_factory=dict)  # field -> count empty

    # Messages
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Stats
    total_rows: int = 0
    valid_rows: int = 0

    @property
    def completeness_score(self) -> float:
        """Calculate completeness as percentage of optional fields present."""
        if not self.missing_optional:
            return 1.0
        total_missing = sum(self.missing_optional.values())
        total_possible = self.total_rows * len(self.missing_optional)
        if total_possible == 0:
            return 1.0
        return 1.0 - (total_missing / total_possible)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "inventory_type": self.inventory_type,
            "missing_required": self.missing_required,
            "missing_optional": self.missing_optional,
            "extra_fields": self.extra_fields,
            "warnings": self.warnings,
            "errors": self.errors,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "completeness_score": self.completeness_score,
        }


@dataclass
class TableInfo:
    """Brief info about a table (for reporting unknown tables)."""
    table_index: int
    headers: List[str]
    row_count: int
    sheet_name: str = ""
    reason_skipped: str = ""


@dataclass
class IngestResult:
    """
    Result of ingesting a file into stores.

    Tracks what was added to InventoryStore and FactStore.
    """
    # Source
    source_file: str = ""
    file_type: str = ""

    # Inventory results
    inventory_items_added: int = 0
    inventory_items_updated: int = 0
    inventory_items_unchanged: int = 0

    # By inventory type
    by_type: Dict[str, int] = field(default_factory=dict)  # type -> count added

    # Facts (from prose via LLM)
    facts_extracted: int = 0
    prose_sent_to_llm: bool = False
    prose_length: int = 0

    # Tables that couldn't be processed
    unknown_tables: List[TableInfo] = field(default_factory=list)

    # Validation
    validation_warnings: List[str] = field(default_factory=list)

    # Errors
    errors: List[str] = field(default_factory=list)

    @property
    def total_inventory_processed(self) -> int:
        """Total inventory items processed."""
        return (self.inventory_items_added +
                self.inventory_items_updated +
                self.inventory_items_unchanged)

    @property
    def success(self) -> bool:
        """Check if ingestion was successful (no critical errors)."""
        return len(self.errors) == 0

    def format_summary(self) -> str:
        """Format a human-readable summary."""
        lines = [
            f"Ingested: {self.source_file}",
            "",
        ]

        # Inventory by type
        for inv_type, count in sorted(self.by_type.items()):
            lines.append(f"  {inv_type.title()}: {count} items loaded")

        if not self.by_type:
            lines.append("  No inventory items found")

        # Validation warnings
        if self.validation_warnings:
            lines.append("")
            lines.append("  Warnings:")
            for warn in self.validation_warnings[:5]:
                lines.append(f"    - {warn}")
            if len(self.validation_warnings) > 5:
                lines.append(f"    ... and {len(self.validation_warnings) - 5} more")

        # Unknown tables
        if self.unknown_tables:
            lines.append("")
            lines.append(f"  Unknown tables: {len(self.unknown_tables)}")
            for table in self.unknown_tables[:3]:
                headers_str = ", ".join(table.headers[:4])
                if len(table.headers) > 4:
                    headers_str += "..."
                lines.append(f"    Table {table.table_index}: [{headers_str}] - {table.reason_skipped}")

        # Prose/LLM
        if self.prose_sent_to_llm:
            lines.append("")
            lines.append(f"  Prose: {self.prose_length:,} chars sent to LLM discovery")
            if self.facts_extracted > 0:
                lines.append(f"    -> {self.facts_extracted} facts extracted")

        # Errors
        if self.errors:
            lines.append("")
            lines.append("  ERRORS:")
            for err in self.errors:
                lines.append(f"    - {err}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_file": self.source_file,
            "file_type": self.file_type,
            "inventory_items_added": self.inventory_items_added,
            "inventory_items_updated": self.inventory_items_updated,
            "inventory_items_unchanged": self.inventory_items_unchanged,
            "by_type": self.by_type,
            "facts_extracted": self.facts_extracted,
            "prose_sent_to_llm": self.prose_sent_to_llm,
            "unknown_tables": [
                {"index": t.table_index, "headers": t.headers, "rows": t.row_count}
                for t in self.unknown_tables
            ],
            "validation_warnings": self.validation_warnings,
            "errors": self.errors,
            "success": self.success,
        }
