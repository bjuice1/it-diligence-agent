"""
Point 105: Unit tests for benchmark matching

Tests profile matching accuracy.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.benchmark_service import (
    BenchmarkService, BenchmarkDataSource, benchmark_profiles
)


class TestBenchmarkService:
    """Tests for BenchmarkService."""

    def setup_method(self):
        """Create fresh service for each test."""
        self.service = BenchmarkService()

    def test_get_profile_by_industry(self):
        """Test getting benchmark profile by industry."""
        profile = self.service.get_profile("healthcare")
        assert profile is not None
        assert "it_spend_pct_revenue" in profile

    def test_get_profile_unknown_industry(self):
        """Test fallback for unknown industry."""
        profile = self.service.get_profile("unknown_industry_xyz")
        # Should return default or None
        assert profile is None or "it_spend_pct_revenue" in profile

    def test_regional_adjustment(self):
        """Test regional cost adjustments."""
        base_cost = 100000
        
        # San Francisco should have higher adjustment
        sf_adjusted = self.service.apply_regional_adjustment(base_cost, "san_francisco")
        assert sf_adjusted > base_cost
        
        # Lower cost region
        midwest_adjusted = self.service.apply_regional_adjustment(base_cost, "midwest")
        assert midwest_adjusted <= base_cost

    def test_custom_benchmark_upload(self):
        """Test uploading custom benchmarks."""
        custom_data = {
            "custom_industry": {
                "it_spend_pct_revenue": 0.05,
                "it_fte_per_1000_employees": 50
            }
        }
        
        result = self.service.upload_custom_benchmarks(custom_data)
        assert result["success"] is True
        
        # Verify custom profile is accessible
        profile = self.service.get_profile("custom_industry")
        assert profile is not None

    def test_data_source_attribution(self):
        """Test benchmark data source attribution."""
        source = BenchmarkDataSource(
            name="Gartner IT Spending",
            version="2025",
            last_updated="2025-01-01",
            source_type="external"
        )
        
        assert source.name == "Gartner IT Spending"
        assert source.version == "2025"


class TestBenchmarkMatching:
    """Tests for benchmark matching accuracy."""

    def setup_method(self):
        """Create fresh service for each test."""
        self.service = BenchmarkService()

    def test_company_vs_benchmark_comparison(self):
        """Test comparing company metrics against benchmarks."""
        company_metrics = {
            "it_spend": 5000000,
            "revenue": 100000000,
            "it_headcount": 50,
            "total_employees": 1000
        }
        
        comparison = self.service.compare_to_benchmark(
            company_metrics, 
            industry="healthcare"
        )
        
        assert "it_spend_variance" in comparison
        assert "headcount_variance" in comparison

    def test_benchmark_profile_completeness(self):
        """Test that benchmark profiles have required fields."""
        required_fields = [
            "it_spend_pct_revenue",
            "it_fte_per_1000_employees"
        ]
        
        for industry in benchmark_profiles.keys():
            profile = self.service.get_profile(industry)
            if profile:
                for field in required_fields:
                    assert field in profile, f"Missing {field} in {industry}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
