"""
Table-Aware Chunker

Chunks documents while preserving table integrity.
No mid-row splits - tables are kept whole or chunked at row boundaries
with headers repeated.

Phase 5 Document Parsing.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Chunk:
    """A document chunk with metadata."""
    content: str
    start_offset: int
    end_offset: int
    chunk_index: int
    contains_table: bool = False
    table_continuation: bool = False  # True if this is a continuation of a split table


class TableAwareChunker:
    """
    Chunks text while preserving table integrity.

    Features:
    - Detects Markdown tables (pipe-delimited)
    - Never splits tables mid-row
    - Large tables get chunked with repeated headers
    - Respects max_chunk_size while prioritizing table integrity
    """

    # Pattern to detect Markdown table rows
    TABLE_ROW_PATTERN = re.compile(r'^\s*\|.*\|\s*$', re.MULTILINE)

    # Pattern for table separator row (---|---|---)
    TABLE_SEP_PATTERN = re.compile(r'^\s*\|[\s\-:|]+\|\s*$', re.MULTILINE)

    def __init__(
        self,
        max_chunk_size: int = 4000,
        overlap: int = 200,
        min_chunk_size: int = 500,
    ):
        """
        Initialize chunker.

        Args:
            max_chunk_size: Target max characters per chunk
            overlap: Characters to overlap between chunks (for context)
            min_chunk_size: Minimum chunk size before merging with next
        """
        self.max_chunk_size = max_chunk_size
        # Ensure overlap doesn't exceed half of max_chunk_size to prevent infinite loops
        self.overlap = min(overlap, max_chunk_size // 2)
        self.min_chunk_size = min(min_chunk_size, max_chunk_size // 2)

    def chunk(self, text: str) -> List[Chunk]:
        """
        Chunk text while preserving table integrity.

        Args:
            text: Input text to chunk

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        # Find all tables in the text
        tables = self._find_tables(text)

        if not tables:
            # No tables - use simple chunking
            return self._simple_chunk(text)

        # Chunk around tables
        return self._chunk_with_tables(text, tables)

    def _find_tables(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Find all Markdown tables in text.

        Returns:
            List of (start_offset, end_offset, table_content) tuples
        """
        tables = []
        lines = text.split('\n')

        i = 0
        current_offset = 0

        while i < len(lines):
            line = lines[i]

            # Check if this line starts a table
            if self._is_table_row(line):
                table_start = current_offset
                table_lines = [line]

                # Consume all consecutive table rows
                j = i + 1
                while j < len(lines) and self._is_table_row(lines[j]):
                    table_lines.append(lines[j])
                    j += 1

                # Only count as table if we have at least header + separator + 1 row
                if len(table_lines) >= 3 and self._has_separator(table_lines):
                    table_content = '\n'.join(table_lines)
                    table_end = table_start + len(table_content)
                    tables.append((table_start, table_end, table_content))

                    # Move past the table
                    i = j
                    current_offset = table_end + 1  # +1 for newline
                    continue

            # Move to next line
            current_offset += len(line) + 1  # +1 for newline
            i += 1

        return tables

    def _is_table_row(self, line: str) -> bool:
        """Check if a line is a table row (starts and ends with |)."""
        stripped = line.strip()
        return stripped.startswith('|') and stripped.endswith('|')

    def _has_separator(self, lines: List[str]) -> bool:
        """Check if table lines contain a separator row."""
        for line in lines[:3]:  # Separator should be in first 3 lines
            if self.TABLE_SEP_PATTERN.match(line):
                return True
        return False

    def _chunk_with_tables(
        self,
        text: str,
        tables: List[Tuple[int, int, str]]
    ) -> List[Chunk]:
        """Chunk text while keeping tables intact."""
        chunks = []
        chunk_index = 0
        current_pos = 0

        for table_start, table_end, table_content in tables:
            # Chunk text before this table
            if current_pos < table_start:
                pre_table_text = text[current_pos:table_start]
                pre_chunks = self._simple_chunk(
                    pre_table_text,
                    start_offset=current_pos,
                    start_index=chunk_index
                )
                chunks.extend(pre_chunks)
                chunk_index += len(pre_chunks)

            # Handle the table
            table_chunks = self._chunk_table(
                table_content,
                start_offset=table_start,
                start_index=chunk_index
            )
            chunks.extend(table_chunks)
            chunk_index += len(table_chunks)

            current_pos = table_end + 1  # Move past newline

        # Chunk remaining text after last table
        if current_pos < len(text):
            remaining = text[current_pos:]
            remaining_chunks = self._simple_chunk(
                remaining,
                start_offset=current_pos,
                start_index=chunk_index
            )
            chunks.extend(remaining_chunks)

        return chunks

    def _chunk_table(
        self,
        table_content: str,
        start_offset: int = 0,
        start_index: int = 0
    ) -> List[Chunk]:
        """
        Chunk a single table, preserving row integrity.

        Large tables are split at row boundaries with headers repeated.
        """
        lines = table_content.split('\n')

        # Extract header (first 2 lines: header row + separator)
        if len(lines) < 2:
            # Malformed table - treat as single chunk
            return [Chunk(
                content=table_content,
                start_offset=start_offset,
                end_offset=start_offset + len(table_content),
                chunk_index=start_index,
                contains_table=True,
            )]

        header_lines = lines[:2]
        header = '\n'.join(header_lines)
        data_lines = lines[2:]

        # If table fits in one chunk, return it whole
        if len(table_content) <= self.max_chunk_size:
            return [Chunk(
                content=table_content,
                start_offset=start_offset,
                end_offset=start_offset + len(table_content),
                chunk_index=start_index,
                contains_table=True,
            )]

        # Split into chunks at row boundaries
        chunks = []
        current_rows = []
        current_size = len(header) + 1  # +1 for newline after header
        chunk_index = start_index
        current_offset = start_offset
        is_continuation = False

        for row in data_lines:
            row_size = len(row) + 1  # +1 for newline

            # Check if adding this row would exceed max size
            if current_size + row_size > self.max_chunk_size and current_rows:
                # Emit current chunk
                chunk_content = header + '\n' + '\n'.join(current_rows)
                chunks.append(Chunk(
                    content=chunk_content,
                    start_offset=current_offset,
                    end_offset=current_offset + len(chunk_content),
                    chunk_index=chunk_index,
                    contains_table=True,
                    table_continuation=is_continuation,
                ))

                # Reset for next chunk
                current_offset += len('\n'.join(current_rows)) + 1
                current_rows = []
                current_size = len(header) + 1
                chunk_index += 1
                is_continuation = True

            current_rows.append(row)
            current_size += row_size

        # Emit final chunk
        if current_rows:
            chunk_content = header + '\n' + '\n'.join(current_rows)
            chunks.append(Chunk(
                content=chunk_content,
                start_offset=current_offset,
                end_offset=current_offset + len(chunk_content),
                chunk_index=chunk_index,
                contains_table=True,
                table_continuation=is_continuation,
            ))

        return chunks

    def _simple_chunk(
        self,
        text: str,
        start_offset: int = 0,
        start_index: int = 0
    ) -> List[Chunk]:
        """
        Simple text chunking (no tables).

        Splits at paragraph boundaries when possible.
        """
        if not text.strip():
            return []

        # If text fits in one chunk, return it
        if len(text) <= self.max_chunk_size:
            return [Chunk(
                content=text.strip(),
                start_offset=start_offset,
                end_offset=start_offset + len(text),
                chunk_index=start_index,
                contains_table=False,
            )]

        chunks = []
        chunk_index = start_index
        current_pos = 0

        while current_pos < len(text):
            # Determine chunk end
            chunk_end = min(current_pos + self.max_chunk_size, len(text))

            # Try to break at a paragraph boundary
            if chunk_end < len(text):
                # Look for double newline (paragraph break)
                para_break = text.rfind('\n\n', current_pos, chunk_end)
                if para_break > current_pos + self.min_chunk_size:
                    chunk_end = para_break + 2
                else:
                    # Try single newline
                    line_break = text.rfind('\n', current_pos, chunk_end)
                    if line_break > current_pos + self.min_chunk_size:
                        chunk_end = line_break + 1
                    else:
                        # Try space
                        space = text.rfind(' ', current_pos, chunk_end)
                        if space > current_pos + self.min_chunk_size:
                            chunk_end = space + 1

            chunk_content = text[current_pos:chunk_end].strip()

            if chunk_content:
                chunks.append(Chunk(
                    content=chunk_content,
                    start_offset=start_offset + current_pos,
                    end_offset=start_offset + chunk_end,
                    chunk_index=chunk_index,
                    contains_table=False,
                ))
                chunk_index += 1

            # Move position, accounting for overlap
            if chunk_end < len(text):
                new_pos = chunk_end - self.overlap
                # Ensure we always make forward progress
                if new_pos <= current_pos:
                    new_pos = current_pos + 1
                current_pos = new_pos
            else:
                current_pos = chunk_end

        return chunks


def chunk_document(
    text: str,
    max_chunk_size: int = 4000,
    overlap: int = 200
) -> List[Chunk]:
    """
    Convenience function to chunk a document.

    Args:
        text: Document text
        max_chunk_size: Target max characters per chunk
        overlap: Characters to overlap between chunks

    Returns:
        List of Chunk objects
    """
    chunker = TableAwareChunker(
        max_chunk_size=max_chunk_size,
        overlap=overlap
    )
    return chunker.chunk(text)


def chunk_with_context(
    text: str,
    context_header: str = "",
    max_chunk_size: int = 4000
) -> List[Chunk]:
    """
    Chunk document with a context header prepended to each chunk.

    Useful for including document metadata in each chunk.

    Args:
        text: Document text
        context_header: Header to prepend (e.g., "Source: document.pdf\n\n")
        max_chunk_size: Target max size (header size is subtracted)

    Returns:
        List of Chunk objects with headers prepended
    """
    # Adjust max size for header
    effective_max = max_chunk_size - len(context_header)
    if effective_max < 500:
        effective_max = 500  # Minimum usable size

    chunker = TableAwareChunker(max_chunk_size=effective_max)
    chunks = chunker.chunk(text)

    # Prepend header to each chunk
    for chunk in chunks:
        chunk.content = context_header + chunk.content

    return chunks
