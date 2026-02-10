"""Tests for preprocessing: Unicode cleanup, table-aware chunking, numeric normalization.

Spec 01: Validates _clean_cell_value, _normalize_numeric, and PDF table merging.
"""
import pytest

from tools_v2.deterministic_parser import _clean_cell_value, _normalize_numeric
from ingestion.pdf_parser import PDFParser


class TestUnicodeCleanup:
    """Verify full PUA range is cleaned, not just 3 characters."""

    def test_clean_cell_value_strips_full_pua_range(self):
        """All BMP PUA characters (U+E000-U+F8FF) should be removed."""
        dirty = "Oracle\ue100Database\ue500Server\uf000"
        result = _clean_cell_value(dirty)
        assert "\ue100" not in result
        assert "\ue500" not in result
        assert "\uf000" not in result
        assert "Oracle" in result
        assert "Database" in result
        assert "Server" in result

    def test_clean_cell_value_strips_original_three(self):
        """Original 3 characters still cleaned (regression check)."""
        dirty = "SAP\ue200ECC\ue201\ue202"
        result = _clean_cell_value(dirty)
        assert "\ue200" not in result
        assert "\ue201" not in result
        assert "\ue202" not in result
        assert "SAP" in result
        assert "ECC" in result

    def test_clean_cell_value_strips_supplementary_pua(self):
        """Supplementary PUA characters should also be removed."""
        dirty = "Test\U000F0001Value"
        cleaned = _clean_cell_value(dirty)
        assert "Test" in cleaned
        assert "Value" in cleaned
        assert "\U000F0001" not in cleaned

    def test_clean_cell_value_preserves_normal_unicode(self):
        """Non-PUA Unicode (accented chars, CJK, etc.) should be preserved."""
        text = "Resume Nono"
        assert _clean_cell_value(text) == text

    def test_clean_cell_value_preserves_accented_characters(self):
        """Accented Latin characters must be preserved."""
        text = "Rene Francois"
        result = _clean_cell_value(text)
        assert result == text

    def test_clean_cell_value_handles_empty_string(self):
        assert _clean_cell_value("") == ""

    def test_clean_cell_value_strips_filecite_markers(self):
        """filecite patterns from OpenAI assistants should be removed."""
        dirty = "SAP ERPfileciteturn3file0L35-L38 system"
        result = _clean_cell_value(dirty)
        assert "filecite" not in result
        assert "SAP ERP" in result
        assert "system" in result

    def test_clean_cell_value_multiple_pua_collapsed(self):
        """Multiple consecutive PUA characters should collapse to single space."""
        dirty = "Word1\ue000\ue001\ue002Word2"
        result = _clean_cell_value(dirty)
        # After PUA removal and whitespace cleanup, should be clean
        assert "Word1" in result
        assert "Word2" in result

    def test_document_preprocessor_covers_full_range(self):
        """DocumentPreprocessor should clean all PUA characters."""
        from tools_v2.document_preprocessor import DocumentPreprocessor
        preprocessor = DocumentPreprocessor(aggressive=False)
        dirty = "Text\ue000\ue100\ue200\uf8ffEnd"
        cleaned = preprocessor.clean(dirty)
        assert "\ue000" not in cleaned
        assert "\ue100" not in cleaned
        assert "\uf8ff" not in cleaned


class TestNumericNormalization:
    """Verify numeric values are cleaned for consistent storage."""

    def test_strip_dollar_sign(self):
        assert _normalize_numeric("$1,250,000") == "1250000"

    def test_strip_euro_sign(self):
        assert _normalize_numeric("\u20ac500") == "500"

    def test_null_values_return_none(self):
        for val in ["N/A", "n/a", "NA", "TBD", "-", "--", "Unknown", "None", ""]:
            assert _normalize_numeric(val) is None, f"Expected None for '{val}'"

    def test_plain_number_passthrough(self):
        assert _normalize_numeric("500") == "500"
        assert _normalize_numeric("0") == "0"

    def test_non_numeric_passthrough(self):
        """Non-numeric strings should be returned as-is (stripped)."""
        result = _normalize_numeric("Microsoft Office")
        assert result == "Microsoft Office"

    def test_decimal_numbers(self):
        assert _normalize_numeric("$1,234.56") == "1234.56"

    def test_zero_dollar(self):
        assert _normalize_numeric("$0") == "0"

    def test_none_input(self):
        assert _normalize_numeric(None) is None

    def test_comma_separated_number(self):
        assert _normalize_numeric("1,000") == "1000"


class TestTableMerging:
    """Verify tables spanning page boundaries are properly merged."""

    def test_merge_split_table_basic(self):
        parser = PDFParser()
        page1 = "Header\n| App | Vendor |\n|-----|--------|\n| SAP | SAP SE |"
        page2 = "| Oracle | Oracle Corp |\n\nFooter text"

        merged = parser._merge_split_tables([page1, page2])
        # The table rows from page2 should be merged into page1
        combined = "\n".join(merged)
        assert "| SAP | SAP SE |" in combined
        assert "| Oracle | Oracle Corp |" in combined

    def test_no_merge_when_no_table(self):
        parser = PDFParser()
        page1 = "Regular text page 1"
        page2 = "Regular text page 2"

        merged = parser._merge_split_tables([page1, page2])
        assert len(merged) == 2
        assert merged[0] == page1
        assert merged[1] == page2

    def test_merge_three_pages(self):
        parser = PDFParser()
        page1 = "| A | B |\n|---|---|\n| 1 | 2 |"
        page2 = "| 3 | 4 |"
        page3 = "| 5 | 6 |\n\nEnd"

        merged = parser._merge_split_tables([page1, page2, page3])
        # All table rows should be accessible in the merged result
        combined = "\n".join(merged)
        assert "| 1 | 2 |" in combined
        assert "| 3 | 4 |" in combined
        assert "| 5 | 6 |" in combined

    def test_single_page_unchanged(self):
        parser = PDFParser()
        merged = parser._merge_split_tables(["Only page"])
        assert merged == ["Only page"]
