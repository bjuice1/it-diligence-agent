"""
Tests for Phase 5: Document Parsing & Preprocessing

Tests all document parsing modules:
- DocumentPreprocessor
- NumericNormalizer
- TableAwareChunker
- DeterministicTableParser
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# DOCUMENT PREPROCESSOR TESTS
# =============================================================================

class TestDocumentPreprocessor:
    """Tests for DocumentPreprocessor."""

    def test_clean_private_use_chars(self):
        """Private Use Area characters should be removed."""
        from tools_v2.document_preprocessor import DocumentPreprocessor

        preprocessor = DocumentPreprocessor()
        # U+E000 is in Private Use Area
        text = "Hello\ue000World\ue001Test"
        result = preprocessor.clean(text)

        assert '\ue000' not in result
        assert '\ue001' not in result
        assert "HelloWorldTest" == result

    def test_clean_citation_artifacts(self):
        """Citation artifacts like filecite should be removed."""
        from tools_v2.document_preprocessor import DocumentPreprocessor

        preprocessor = DocumentPreprocessor()

        # Test filecite pattern
        text = "The data shows filecite123[source] that revenue increased."
        result = preprocessor.clean(text)
        assert "filecite" not in result
        assert "revenue increased" in result

        # Test oaicite pattern
        text2 = "According to oaicite:1]the report"
        result2 = preprocessor.clean(text2)
        assert "oaicite" not in result2

    def test_clean_control_characters(self):
        """Control characters (except newlines/tabs) should be removed."""
        from tools_v2.document_preprocessor import DocumentPreprocessor

        preprocessor = DocumentPreprocessor()
        # \x00 is null, \x07 is bell
        text = "Hello\x00World\x07Test\nLine2"
        result = preprocessor.clean(text)

        assert '\x00' not in result
        assert '\x07' not in result
        assert '\n' in result  # Newline preserved

    def test_normalize_whitespace(self):
        """Multiple spaces should collapse to single space."""
        from tools_v2.document_preprocessor import DocumentPreprocessor

        preprocessor = DocumentPreprocessor()
        text = "Hello    World\t\tTest"
        result = preprocessor.clean(text)

        assert "    " not in result
        assert "Hello World Test" == result

    def test_normalize_newlines(self):
        """Multiple newlines should collapse to max 2."""
        from tools_v2.document_preprocessor import DocumentPreprocessor

        preprocessor = DocumentPreprocessor()
        text = "Para1\n\n\n\n\nPara2"
        result = preprocessor.clean(text)

        assert "\n\n\n" not in result
        assert "\n\n" in result

    def test_aggressive_mode_typography(self):
        """Aggressive mode should normalize fancy typography."""
        from tools_v2.document_preprocessor import DocumentPreprocessor

        preprocessor = DocumentPreprocessor(aggressive=True)
        # Em dash should be replaced with regular dash
        text = 'Testing em\u2014dash replacement'
        result = preprocessor.clean(text)

        # Em dash should be converted to regular dash
        assert '\u2014' not in result  # Em dash gone
        assert 'em-dash' in result  # Regular dash present

    def test_class_method_clean_text(self):
        """Class method should work for one-off cleaning."""
        from tools_v2.document_preprocessor import DocumentPreprocessor

        result = DocumentPreprocessor.clean_text("Hello  World")
        assert result == "Hello World"

    def test_convenience_function(self):
        """Convenience function should work."""
        from tools_v2.document_preprocessor import preprocess_document

        result = preprocess_document("Hello  World")
        assert result == "Hello World"

    def test_stats_tracking(self):
        """Stats should track what was removed."""
        from tools_v2.document_preprocessor import DocumentPreprocessor

        preprocessor = DocumentPreprocessor()
        text = "Test\ue000\ue001 filecite123 data"
        preprocessor.clean(text)
        stats = preprocessor.get_stats()

        assert stats['private_use_removed'] == 2
        assert stats['citations_removed'] == 1

    def test_empty_input(self):
        """Empty input should return empty."""
        from tools_v2.document_preprocessor import DocumentPreprocessor

        preprocessor = DocumentPreprocessor()
        assert preprocessor.clean("") == ""
        assert preprocessor.clean(None) is None


# =============================================================================
# NUMERIC NORMALIZER TESTS
# =============================================================================

class TestNumericNormalizer:
    """Tests for NumericNormalizer."""

    def test_normalize_currency_us(self):
        """US currency format should normalize."""
        from tools_v2.numeric_normalizer import normalize_numeric

        assert normalize_numeric("$1,234.56") == 1234.56
        assert normalize_numeric("$1,000") == 1000
        assert normalize_numeric("$99.99") == 99.99

    def test_normalize_currency_symbols(self):
        """Various currency symbols should be handled."""
        from tools_v2.numeric_normalizer import normalize_numeric

        assert normalize_numeric("€1,234") == 1234
        assert normalize_numeric("£500") == 500
        assert normalize_numeric("¥10000") == 10000

    def test_normalize_eu_format(self):
        """EU number format should normalize."""
        from tools_v2.numeric_normalizer import normalize_numeric

        # EU uses . for thousands, , for decimal
        assert normalize_numeric("1.234,56") == 1234.56

    def test_normalize_with_text(self):
        """Numbers with trailing text should extract numeric part."""
        from tools_v2.numeric_normalizer import normalize_numeric

        assert normalize_numeric("1,407 users") == 1407
        assert normalize_numeric("500 employees") == 500
        assert normalize_numeric("$50k salary") == 50

    def test_normalize_approximations(self):
        """Approximation prefixes should be removed."""
        from tools_v2.numeric_normalizer import normalize_numeric

        assert normalize_numeric("~500") == 500
        assert normalize_numeric("≈1000") == 1000
        assert normalize_numeric("~$1,500") == 1500

    def test_null_indicators(self):
        """Null indicators should return None."""
        from tools_v2.numeric_normalizer import normalize_numeric

        assert normalize_numeric("N/A") is None
        assert normalize_numeric("TBD") is None
        assert normalize_numeric("-") is None
        assert normalize_numeric("Unknown") is None
        assert normalize_numeric("null") is None

    def test_normalize_cost(self):
        """normalize_cost should return float."""
        from tools_v2.numeric_normalizer import normalize_cost

        assert normalize_cost("$1,234") == 1234.0
        assert isinstance(normalize_cost("$100"), float)
        assert normalize_cost("N/A") is None

    def test_normalize_count(self):
        """normalize_count should return int."""
        from tools_v2.numeric_normalizer import normalize_count

        assert normalize_count("1,407 users") == 1407
        assert isinstance(normalize_count("100"), int)
        assert normalize_count("TBD") is None

    def test_is_null_value(self):
        """is_null_value should identify null indicators."""
        from tools_v2.numeric_normalizer import is_null_value

        assert is_null_value("N/A") is True
        assert is_null_value("TBD") is True
        assert is_null_value(None) is True
        assert is_null_value("-") is True
        assert is_null_value("100") is False
        assert is_null_value("Active") is False

    def test_normalize_percentage(self):
        """Percentages should normalize to 0-1 range."""
        from tools_v2.numeric_normalizer import normalize_percentage

        assert normalize_percentage("85%") == 0.85
        assert normalize_percentage("100%") == 1.0
        assert normalize_percentage("0.5") == 0.5
        assert normalize_percentage("50") == 0.5  # Assumes > 1 means percentage

    def test_already_numeric(self):
        """Already numeric values should pass through."""
        from tools_v2.numeric_normalizer import normalize_numeric

        assert normalize_numeric(100) == 100
        assert normalize_numeric(3.14) == 3.14
        assert normalize_numeric(0) == 0

    def test_parenthetical_suffix_removal(self):
        """Parenthetical suffixes should be removed."""
        from tools_v2.numeric_normalizer import normalize_numeric

        assert normalize_numeric("$100 (estimated)") == 100
        assert normalize_numeric("500 (approx)") == 500


# =============================================================================
# TABLE AWARE CHUNKER TESTS
# =============================================================================

class TestTableAwareChunker:
    """Tests for TableAwareChunker."""

    def test_simple_text_chunking(self):
        """Text without tables should chunk normally."""
        from tools_v2.table_chunker import TableAwareChunker

        chunker = TableAwareChunker(max_chunk_size=100)
        text = "A" * 250
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.contains_table is False

    def test_table_detection(self):
        """Tables should be detected."""
        from tools_v2.table_chunker import TableAwareChunker

        chunker = TableAwareChunker()
        text = """
Some intro text.

| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |

More text after.
"""
        chunks = chunker.chunk(text)

        # Find chunk with table
        table_chunks = [c for c in chunks if c.contains_table]
        assert len(table_chunks) >= 1

    def test_table_not_split_mid_row(self):
        """Tables should not be split mid-row."""
        from tools_v2.table_chunker import TableAwareChunker

        chunker = TableAwareChunker(max_chunk_size=200)
        table = """| Column A | Column B | Column C |
|----------|----------|----------|
| Row 1    | Data     | More     |
| Row 2    | Data     | More     |
| Row 3    | Data     | More     |
| Row 4    | Data     | More     |
| Row 5    | Data     | More     |
"""
        chunks = chunker.chunk(table)

        for chunk in chunks:
            # Each chunk should have complete rows
            lines = chunk.content.strip().split('\n')
            for line in lines:
                if line.strip().startswith('|'):
                    # Should start and end with |
                    assert line.strip().endswith('|'), f"Incomplete row: {line}"

    def test_large_table_header_repetition(self):
        """Large tables should repeat headers when chunked."""
        from tools_v2.table_chunker import TableAwareChunker

        chunker = TableAwareChunker(max_chunk_size=300)

        # Create large table
        rows = ["| Header A | Header B |", "|----------|----------|"]
        for i in range(50):
            rows.append(f"| Row {i}   | Data {i} |")

        table = '\n'.join(rows)
        chunks = chunker.chunk(table)

        # If multiple chunks, each should have headers
        if len(chunks) > 1:
            for chunk in chunks:
                assert "Header A" in chunk.content
                assert "Header B" in chunk.content

    def test_mixed_content(self):
        """Mixed text and tables should chunk correctly."""
        from tools_v2.table_chunker import TableAwareChunker

        chunker = TableAwareChunker(max_chunk_size=500)
        text = """
# Introduction

This is introductory text that comes before the table.

| System | Status |
|--------|--------|
| App A  | Active |
| App B  | Down   |

## Conclusion

This is text after the table.
"""
        chunks = chunker.chunk(text)

        # Should have at least intro, table, and conclusion
        assert len(chunks) >= 1

        # Table should be in a chunk
        all_content = ' '.join(c.content for c in chunks)
        assert "App A" in all_content
        assert "Introduction" in all_content
        assert "Conclusion" in all_content

    def test_empty_input(self):
        """Empty input should return empty list."""
        from tools_v2.table_chunker import TableAwareChunker

        chunker = TableAwareChunker()
        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []

    def test_chunk_dataclass(self):
        """Chunk dataclass should have correct fields."""
        from tools_v2.table_chunker import TableAwareChunker, Chunk

        chunker = TableAwareChunker()
        chunks = chunker.chunk("Test content here")

        assert len(chunks) == 1
        chunk = chunks[0]

        assert hasattr(chunk, 'content')
        assert hasattr(chunk, 'start_offset')
        assert hasattr(chunk, 'end_offset')
        assert hasattr(chunk, 'chunk_index')
        assert hasattr(chunk, 'contains_table')

    def test_convenience_functions(self):
        """Convenience functions should work."""
        from tools_v2.table_chunker import chunk_document, chunk_with_context

        chunks = chunk_document("Test content")
        assert len(chunks) >= 1

        chunks_with_ctx = chunk_with_context(
            "Test content",
            context_header="Source: test.pdf\n\n"
        )
        assert chunks_with_ctx[0].content.startswith("Source: test.pdf")


# =============================================================================
# DETERMINISTIC TABLE PARSER TESTS
# =============================================================================

class TestDeterministicTableParser:
    """Tests for DeterministicTableParser."""

    def test_parse_simple_table(self):
        """Simple table should parse correctly."""
        from tools_v2.table_parser import DeterministicTableParser

        parser = DeterministicTableParser()
        table = """| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |"""

        result = parser.parse_single(table)

        assert result is not None
        assert result.headers == ['Name', 'Value']
        assert len(result.rows) == 2
        assert result.rows[0]['Name'] == 'A'
        assert result.rows[0]['Value'] == 1  # Normalized to int

    def test_numeric_normalization(self):
        """Numeric values should be normalized."""
        from tools_v2.table_parser import DeterministicTableParser

        parser = DeterministicTableParser(normalize_numbers=True)
        table = """| Item | Cost | Count |
|------|------|-------|
| A    | $1,234 | 500 |
| B    | N/A  | ~100  |"""

        result = parser.parse_single(table)

        assert result.rows[0]['Cost'] == 1234
        assert result.rows[0]['Count'] == 500
        assert result.rows[1]['Cost'] is None  # N/A -> None
        assert result.rows[1]['Count'] == 100  # ~100 -> 100

    def test_preserve_raw_values(self):
        """Raw values should be preserved."""
        from tools_v2.table_parser import DeterministicTableParser

        parser = DeterministicTableParser()
        table = """| Name | Value |
|------|-------|
| A    | $100  |"""

        result = parser.parse_single(table)

        assert result.raw_rows[0] == ['A', '$100']
        assert result.rows[0]['Value'] == 100  # Normalized

    def test_to_records_with_raw(self):
        """to_records should include raw values when requested."""
        from tools_v2.table_parser import DeterministicTableParser

        parser = DeterministicTableParser()
        table = """| Name | Value |
|------|-------|
| A    | $100  |"""

        result = parser.parse_single(table)
        records = parser.to_records(result, include_raw=True)

        assert records[0]['Value'] == 100
        assert records[0]['_raw_Value'] == '$100'

    def test_parse_multiple_tables(self):
        """Multiple tables should all be parsed."""
        from tools_v2.table_parser import DeterministicTableParser

        parser = DeterministicTableParser()
        text = """
First table:

| A | B |
|---|---|
| 1 | 2 |

Second table:

| X | Y |
|---|---|
| 3 | 4 |
"""
        tables = parser.parse(text)

        assert len(tables) == 2
        assert tables[0].headers == ['A', 'B']
        assert tables[1].headers == ['X', 'Y']

    def test_handle_malformed_rows(self):
        """Malformed rows should be handled gracefully."""
        from tools_v2.table_parser import DeterministicTableParser

        parser = DeterministicTableParser()
        # Row with missing column
        table = """| A | B | C |
|---|---|---|
| 1 | 2 |
| 3 | 4 | 5 |"""

        result = parser.parse_single(table)

        # Should pad missing columns
        assert len(result.rows[0]) == 3
        assert result.rows[0]['C'] is None  # Padded and normalized to None

    def test_disable_numeric_normalization(self):
        """With normalize_numbers=False, values stay as strings."""
        from tools_v2.table_parser import DeterministicTableParser

        parser = DeterministicTableParser(normalize_numbers=False)
        table = """| Name | Value |
|------|-------|
| A    | 100   |"""

        result = parser.parse_single(table)

        assert result.rows[0]['Value'] == '100'  # String, not int

    def test_deterministic_output(self):
        """Same input should produce same output."""
        from tools_v2.table_parser import DeterministicTableParser

        parser = DeterministicTableParser()
        table = """| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |"""

        result1 = parser.parse_single(table)
        result2 = parser.parse_single(table)

        assert result1.headers == result2.headers
        assert result1.rows == result2.rows
        assert result1.raw_rows == result2.raw_rows

    def test_convenience_functions(self):
        """Convenience functions should work."""
        from tools_v2.table_parser import parse_table, parse_tables, extract_table_data

        table = """| A | B |
|---|---|
| 1 | 2 |"""

        result = parse_table(table)
        assert result is not None

        results = parse_tables(table)
        assert len(results) == 1

        data = extract_table_data(table)
        assert len(data) == 1
        assert data[0][0]['A'] == 1

    def test_empty_input(self):
        """Empty input should return None/empty."""
        from tools_v2.table_parser import parse_table, parse_tables

        assert parse_table("") is None
        assert parse_table("No tables here") is None
        assert parse_tables("") == []

    def test_offsets_tracked(self):
        """Start and end offsets should be tracked."""
        from tools_v2.table_parser import DeterministicTableParser

        parser = DeterministicTableParser()
        text = """Intro text

| A | B |
|---|---|
| 1 | 2 |

More text"""

        tables = parser.parse(text)

        assert len(tables) == 1
        assert tables[0].start_offset > 0  # After intro
        assert tables[0].end_offset > tables[0].start_offset


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestParsingIntegration:
    """Integration tests combining multiple modules."""

    def test_preprocess_then_parse(self):
        """Preprocessor output should parse correctly."""
        from tools_v2.document_preprocessor import preprocess_document
        from tools_v2.table_parser import parse_table

        # Dirty input with PUA chars
        dirty = """| System\ue000 | Cost |
|------|------|
| App A | $1,234 |"""

        clean = preprocess_document(dirty)
        result = parse_table(clean)

        assert result is not None
        assert 'System' in result.headers[0]  # PUA removed
        assert result.rows[0]['Cost'] == 1234

    def test_preprocess_chunk_parse(self):
        """Full pipeline: preprocess -> chunk -> parse."""
        from tools_v2.document_preprocessor import preprocess_document
        from tools_v2.table_chunker import chunk_document
        from tools_v2.table_parser import parse_tables

        document = """
# Report filecite123

Some intro text with\ue000 special chars.

| Application | Status | Users |
|-------------|--------|-------|
| CRM         | Active | 1,500 |
| ERP         | Active | 800   |

## Conclusion

Final notes.
"""
        # Step 1: Preprocess
        clean = preprocess_document(document)
        assert 'filecite' not in clean
        assert '\ue000' not in clean

        # Step 2: Chunk
        chunks = chunk_document(clean)
        assert len(chunks) >= 1

        # Step 3: Parse tables from chunks
        all_tables = []
        for chunk in chunks:
            tables = parse_tables(chunk.content)
            all_tables.extend(tables)

        assert len(all_tables) >= 1
        table = all_tables[0]
        assert table.rows[0]['Users'] == 1500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
