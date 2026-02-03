"""
Deterministic Table Parser

Parses Markdown tables into structured data with consistent,
deterministic output. Same input always produces same output.

Phase 5 Document Parsing.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from tools_v2.numeric_normalizer import normalize_numeric, is_null_value


@dataclass
class ParsedTable:
    """A parsed table with headers and rows."""
    headers: List[str]
    rows: List[Dict[str, Any]]
    raw_rows: List[List[str]]  # Original string values
    source_text: str = ""
    start_offset: int = 0
    end_offset: int = 0


@dataclass
class TableCell:
    """A single table cell with parsed value."""
    raw_value: str
    parsed_value: Any  # Normalized numeric or original string
    column_index: int
    column_name: str
    is_numeric: bool = False
    is_null: bool = False


class DeterministicTableParser:
    """
    Parses Markdown tables into structured data.

    Features:
    - Deterministic output (same input = same output)
    - Handles various Markdown table formats
    - Normalizes numeric values using NumericNormalizer
    - Preserves original values alongside parsed values
    - Handles malformed tables gracefully
    """

    # Pattern for table row (pipe-delimited)
    ROW_PATTERN = re.compile(r'^\s*\|(.+)\|\s*$')

    # Pattern for separator row
    SEP_PATTERN = re.compile(r'^[\s\-:|]+$')

    def __init__(self, normalize_numbers: bool = True):
        """
        Initialize parser.

        Args:
            normalize_numbers: If True, attempt to parse numeric values
        """
        self.normalize_numbers = normalize_numbers

    def parse(self, text: str) -> List[ParsedTable]:
        """
        Parse all tables from text.

        Args:
            text: Text containing Markdown tables

        Returns:
            List of ParsedTable objects
        """
        tables = []
        lines = text.split('\n')

        i = 0
        current_offset = 0

        while i < len(lines):
            line = lines[i]

            # Check if this starts a table
            if self._is_table_row(line):
                table_start = current_offset
                table_lines = [line]
                line_indices = [i]

                # Collect consecutive table rows
                j = i + 1
                while j < len(lines) and self._is_table_row(lines[j]):
                    table_lines.append(lines[j])
                    line_indices.append(j)
                    j += 1

                # Parse if we have a valid table structure
                if self._is_valid_table(table_lines):
                    table = self._parse_table(
                        table_lines,
                        start_offset=table_start
                    )
                    if table:
                        tables.append(table)

                i = j
                current_offset = table_start + sum(len(l) + 1 for l in table_lines)
                continue

            current_offset += len(line) + 1
            i += 1

        return tables

    def parse_single(self, table_text: str) -> Optional[ParsedTable]:
        """
        Parse a single table from text.

        Args:
            table_text: Text containing exactly one table

        Returns:
            ParsedTable or None if parsing fails
        """
        tables = self.parse(table_text)
        return tables[0] if tables else None

    def _is_table_row(self, line: str) -> bool:
        """Check if line is a table row."""
        stripped = line.strip()
        return stripped.startswith('|') and stripped.endswith('|')

    def _is_valid_table(self, lines: List[str]) -> bool:
        """
        Check if lines form a valid table.

        Requires at least: header row, separator row, one data row.
        """
        if len(lines) < 3:
            return False

        # Second row should be separator
        cells = self._split_row(lines[1])
        for cell in cells:
            if not self.SEP_PATTERN.match(cell):
                return False

        return True

    def _split_row(self, line: str) -> List[str]:
        """Split a table row into cells."""
        # Remove leading/trailing pipes and split
        match = self.ROW_PATTERN.match(line)
        if not match:
            return []

        content = match.group(1)

        # Split by | but handle escaped pipes
        cells = []
        current = []
        escaped = False

        for char in content:
            if escaped:
                current.append(char)
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '|':
                cells.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        # Don't forget last cell
        if current:
            cells.append(''.join(current).strip())

        return cells

    def _parse_table(
        self,
        lines: List[str],
        start_offset: int = 0
    ) -> Optional[ParsedTable]:
        """Parse table lines into structured data."""
        if len(lines) < 3:
            return None

        # Parse header (first row)
        headers = self._split_row(lines[0])
        if not headers:
            return None

        # Skip separator (second row)
        # Parse data rows (rest)
        raw_rows = []
        rows = []

        for line in lines[2:]:
            cells = self._split_row(line)

            # Pad or trim to match header count
            while len(cells) < len(headers):
                cells.append('')
            cells = cells[:len(headers)]

            raw_rows.append(cells)

            # Create row dict with parsed values
            row = {}
            for idx, (header, value) in enumerate(zip(headers, cells)):
                parsed = self._parse_cell(value)
                row[header] = parsed

            rows.append(row)

        # Calculate end offset
        source_text = '\n'.join(lines)
        end_offset = start_offset + len(source_text)

        return ParsedTable(
            headers=headers,
            rows=rows,
            raw_rows=raw_rows,
            source_text=source_text,
            start_offset=start_offset,
            end_offset=end_offset,
        )

    def _parse_cell(self, value: str) -> Any:
        """
        Parse a cell value.

        Returns normalized numeric if applicable, otherwise original string.
        """
        if is_null_value(value):
            return None

        if self.normalize_numbers:
            numeric = normalize_numeric(value)
            if numeric is not None:
                return numeric

        return value

    def to_dicts(self, table: ParsedTable) -> List[Dict[str, Any]]:
        """
        Convert parsed table to list of dicts.

        This is the same as table.rows but provided for API consistency.
        """
        return table.rows

    def to_records(
        self,
        table: ParsedTable,
        include_raw: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Convert to records with optional raw values.

        Args:
            table: ParsedTable to convert
            include_raw: If True, include _raw_<column> fields

        Returns:
            List of record dicts
        """
        records = []

        for row_idx, row in enumerate(table.rows):
            record = dict(row)

            if include_raw:
                raw_row = table.raw_rows[row_idx]
                for col_idx, header in enumerate(table.headers):
                    record[f'_raw_{header}'] = raw_row[col_idx]

            records.append(record)

        return records


def parse_table(text: str) -> Optional[ParsedTable]:
    """
    Convenience function to parse a single table.

    Args:
        text: Text containing a Markdown table

    Returns:
        ParsedTable or None
    """
    parser = DeterministicTableParser()
    return parser.parse_single(text)


def parse_tables(text: str) -> List[ParsedTable]:
    """
    Convenience function to parse all tables from text.

    Args:
        text: Text containing Markdown tables

    Returns:
        List of ParsedTable objects
    """
    parser = DeterministicTableParser()
    return parser.parse(text)


def extract_table_data(text: str) -> List[List[Dict[str, Any]]]:
    """
    Extract all table data as lists of dicts.

    Args:
        text: Text containing Markdown tables

    Returns:
        List of tables, each table is a list of row dicts
    """
    tables = parse_tables(text)
    return [table.rows for table in tables]
