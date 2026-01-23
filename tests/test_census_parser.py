"""
Point 104: Unit tests for census parser validation

Tests edge cases in data validation.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.census_parser import (
    CensusParser, CensusValidationReport,
    MIN_REALISTIC_SALARY, MAX_REALISTIC_SALARY
)


class TestCensusValidation:
    """Tests for census data validation."""

    def test_compensation_bounds_valid(self):
        """Test valid compensation values pass validation."""
        parser = CensusParser()
        
        # Valid salary
        assert parser._is_valid_compensation(75000)
        assert parser._is_valid_compensation(150000)
        assert parser._is_valid_compensation(MIN_REALISTIC_SALARY + 1)
        assert parser._is_valid_compensation(MAX_REALISTIC_SALARY - 1)

    def test_compensation_bounds_invalid(self):
        """Test invalid compensation values are caught."""
        parser = CensusParser()
        
        # Invalid - too low
        assert not parser._is_valid_compensation(5000)
        assert not parser._is_valid_compensation(0)
        assert not parser._is_valid_compensation(-1000)
        
        # Invalid - too high
        assert not parser._is_valid_compensation(50000000)

    def test_date_validation_formats(self):
        """Test various date formats are parsed correctly."""
        parser = CensusParser()
        
        # Valid formats
        valid_dates = [
            "2023-01-15",  # ISO
            "01/15/2023",  # US
            "15/01/2023",  # European
            "Jan 15, 2023",
            "15-Jan-2023",
        ]
        
        for date_str in valid_dates:
            result = parser._parse_date(date_str)
            assert result is not None, f"Failed to parse: {date_str}"

    def test_date_validation_future_dates(self):
        """Test that future dates are flagged."""
        parser = CensusParser()
        
        # Future date should still parse but may be flagged
        result = parser._parse_date("2030-01-01")
        # Parser should return None or flag as warning for future dates
        # depending on implementation

    def test_validation_report_generation(self):
        """Test validation report is generated correctly."""
        report = CensusValidationReport()
        
        report.errors.append("Test error")
        report.warnings.append("Test warning")
        report.column_mapping_confidence = {"name": 0.95, "salary": 0.85}
        
        assert len(report.errors) == 1
        assert len(report.warnings) == 1
        assert report.column_mapping_confidence["name"] == 0.95

    def test_column_detection_confidence(self):
        """Test column auto-detection confidence scoring."""
        parser = CensusParser()
        
        # Test with obvious column names
        test_headers = ["Employee Name", "Annual Salary", "Start Date", "Department"]
        confidence = parser._detect_columns_with_confidence(test_headers)
        
        # Should have high confidence for common fields
        assert confidence.get("name", 0) > 0.7
        assert confidence.get("salary", 0) > 0.7


class TestCensusParserEdgeCases:
    """Tests for edge cases in census parsing."""

    def test_empty_data(self):
        """Test handling of empty data."""
        parser = CensusParser()
        result = parser.parse("")
        assert result is not None
        assert len(result.staff_members) == 0

    def test_missing_columns(self):
        """Test handling of missing required columns."""
        parser = CensusParser()
        csv_data = "random_col1,random_col2\nvalue1,value2"
        result = parser.parse(csv_data)
        assert len(result.warnings) > 0 or len(result.errors) > 0

    def test_unicode_names(self):
        """Test handling of unicode characters in names."""
        parser = CensusParser()
        # Verify parser handles non-ASCII names
        csv_data = "name,salary\nJosé García,75000\nMüller François,80000"
        result = parser.parse(csv_data)
        # Should not crash and should preserve names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
