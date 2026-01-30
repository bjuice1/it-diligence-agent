"""
Markdown Parser

Parses Markdown text extracting tables and prose.
Builds on the existing deterministic_parser functionality.
"""

import re
import logging
from typing import List, Tuple, Optional
from pathlib import Path

from tools_v2.parsers.models import ParsedTable, ParseResult
from tools_v2.parsers.type_detector import detect_inventory_type

logger = logging.getLogger(__name__)


def parse_markdown(text: str, source_file: str = "") -> ParseResult:
    """
    Parse Markdown text into tables and prose.

    Args:
        text: Markdown text content
        source_file: Optional source filename

    Returns:
        ParseResult with tables and prose
    """
    result = ParseResult(
        source_file=source_file,
        file_type="markdown",
    )

    # Extract tables
    table_matches = extract_markdown_tables(text)

    # Build prose by removing tables
    prose_text = text
    for table_text, start, end in sorted(table_matches, key=lambda x: x[1], reverse=True):
        # Replace table with placeholder
        prose_text = prose_text[:start] + f"\n[TABLE]\n" + prose_text[end:]

    result.prose = _clean_prose(prose_text)

    # Parse each table
    for idx, (table_text, start, end) in enumerate(table_matches):
        parsed = parse_markdown_table(table_text)
        if parsed and parsed.row_count > 0:
            parsed.source_file = source_file
            parsed.table_index = idx
            parsed.start_char = start
            parsed.end_char = end
            parsed.raw_text = table_text

            # Detect type
            inv_type, confidence = detect_inventory_type(parsed.headers)
            parsed.detected_type = inv_type
            parsed.detection_confidence = confidence

            result.tables.append(parsed)

    return result


def parse_markdown_file(file_path: Path) -> ParseResult:
    """
    Parse a Markdown file.

    Args:
        file_path: Path to .md file

    Returns:
        ParseResult with tables and prose
    """
    file_path = Path(file_path)

    if not file_path.exists():
        result = ParseResult(source_file=file_path.name, file_type="markdown")
        result.errors.append(f"File not found: {file_path}")
        return result

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return parse_markdown(text, source_file=file_path.name)
    except Exception as e:
        result = ParseResult(source_file=file_path.name, file_type="markdown")
        result.errors.append(f"Failed to read file: {str(e)}")
        return result


def extract_markdown_tables(text: str) -> List[Tuple[str, int, int]]:
    """
    Extract all markdown tables from text.

    Returns:
        List of (table_text, start_pos, end_pos) tuples
    """
    tables = []

    # Pattern for markdown table:
    # - Header row: | col1 | col2 | col3 |
    # - Separator: |---|---|---|
    # - Data rows: | val1 | val2 | val3 |
    table_pattern = re.compile(
        r'(\|[^\n]+\|\n'           # Header row
        r'\|[-:\s|]+\|\n'          # Separator row
        r'(?:\|[^\n]+\|\n?)+)',    # Data rows
        re.MULTILINE
    )

    for match in table_pattern.finditer(text):
        tables.append((match.group(0), match.start(), match.end()))

    return tables


def parse_markdown_table(table_text: str) -> Optional[ParsedTable]:
    """
    Parse a single markdown table into ParsedTable.

    Args:
        table_text: Markdown table text

    Returns:
        ParsedTable or None if parsing fails
    """
    lines = table_text.strip().split('\n')

    if len(lines) < 3:
        return None

    # Parse header row
    header_line = lines[0]
    headers = _parse_table_row(header_line)

    if not headers:
        return None

    # Normalize headers
    headers = [_normalize_header(h, i) for i, h in enumerate(headers)]

    # Skip separator line (line 1)
    # Parse data rows
    rows = []
    for line in lines[2:]:
        cells = _parse_table_row(line)
        if cells:
            # Pad or truncate to match headers
            if len(cells) < len(headers):
                cells = cells + [None] * (len(headers) - len(cells))
            elif len(cells) > len(headers):
                cells = cells[:len(headers)]

            # Create row dict
            row_dict = {}
            has_data = False
            for i, value in enumerate(cells):
                cleaned = _clean_value(value)
                row_dict[headers[i]] = cleaned
                if cleaned:
                    has_data = True

            if has_data:
                rows.append(row_dict)

    if not rows:
        return None

    return ParsedTable(
        headers=headers,
        rows=rows,
    )


def _parse_table_row(line: str) -> List[str]:
    """Parse a markdown table row into cells."""
    # Remove leading/trailing pipes and split
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]

    cells = [cell.strip() for cell in line.split('|')]
    return cells


def _normalize_header(value: str, col_num: int) -> str:
    """Normalize a header value."""
    if not value or not value.strip():
        return f"column_{col_num}"

    header = value.strip().lower()

    # Remove markdown formatting
    header = re.sub(r'\*\*([^*]+)\*\*', r'\1', header)  # Bold
    header = re.sub(r'\*([^*]+)\*', r'\1', header)      # Italic
    header = re.sub(r'`([^`]+)`', r'\1', header)        # Code

    # Remove citation markers
    header = re.sub(r'\[\d+\]', '', header)
    header = re.sub(r'[\ue200\ue201\ue202]', '', header)

    # Remove special characters
    header = ''.join(c if c.isalnum() or c.isspace() or c == '_' else ' ' for c in header)
    header = ' '.join(header.split())

    if not header:
        return f"column_{col_num}"

    return header


def _clean_value(value: Optional[str]) -> Optional[str]:
    """Clean a cell value."""
    if not value:
        return None

    cleaned = value.strip()

    # Remove markdown formatting
    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
    cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)

    # Remove citation markers
    cleaned = re.sub(r'\[\d+\]', '', cleaned)
    cleaned = re.sub(r'[\ue200\ue201\ue202]', '', cleaned)

    cleaned = cleaned.strip()

    if not cleaned or cleaned.lower() in ['n/a', 'na', '-', '--', 'tbd', 'none', '']:
        return None

    return cleaned


def _clean_prose(text: str) -> str:
    """Clean prose text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove citation markers
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'[\ue200\ue201\ue202]', '', text)

    return text.strip()
