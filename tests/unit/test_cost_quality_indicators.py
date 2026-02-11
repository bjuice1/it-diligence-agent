"""
Unit tests for cost data quality indicators.

Tests that quality assessment functions correctly evaluate data completeness
and provide entity-aware quality scores.
"""

import pytest
from web.blueprints.costs import (
    _quality_level,
    _assess_data_quality_per_entity,
    CostCategory,
    OneTimeCosts,
    RunRateCosts,
)


class TestQualityLevel:
    """Test _quality_level() helper function."""

    def test_quality_level_none(self):
        """Zero value returns 'none'."""
        result = _quality_level(0, thresholds=[100, 500, 1000])
        assert result == "none"

    def test_quality_level_low(self):
        """Value below first threshold returns 'low'."""
        result = _quality_level(50, thresholds=[100, 500, 1000])
        assert result == "low"

    def test_quality_level_medium(self):
        """Value between first and second threshold returns 'medium'."""
        result = _quality_level(300, thresholds=[100, 500, 1000])
        assert result == "medium"

    def test_quality_level_high(self):
        """Value between second and third threshold returns 'high'."""
        result = _quality_level(750, thresholds=[100, 500, 1000])
        assert result == "high"

    def test_quality_level_very_high(self):
        """Value above third threshold returns 'very_high'."""
        result = _quality_level(2000, thresholds=[100, 500, 1000])
        assert result == "very_high"


class TestDataQualityAssessment:
    """Test _assess_data_quality_per_entity() function."""

    def test_assess_quality_with_complete_data(self):
        """Quality assessment with complete data returns high scores."""
        # Create mock run_rate costs with substantial data
        headcount = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        headcount.total = 2_000_000  # $2M - should be "very_high"

        apps = CostCategory(name="applications", display_name="Apps", icon="📱")
        apps.total = 1_500_000  # $1.5M - should be "high"
        apps.items = [None] * 25  # 25 applications

        infra = CostCategory(name="infrastructure", display_name="Infra", icon="🖥️")
        infra.total = 300_000  # $300K - should be "high"
        infra.items = [None] * 10  # 10 infrastructure items

        run_rate = RunRateCosts(
            headcount=headcount,
            applications=apps,
            infrastructure=infra,
            vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")
        )

        one_time = OneTimeCosts()
        one_time.total_mid = 800_000  # $800K - should be "high"

        # Execute
        quality = _assess_data_quality_per_entity(run_rate, one_time, entity="target")

        # Verify
        # $2M headcount is above 1M threshold, so "very_high"
        assert quality["headcount"]["overall"] == "very_high"
        # $1.5M apps is between 500K-2M, so "high"
        assert quality["applications"]["overall"] == "high"
        # $300K infra is between 100K-500K, so "high"
        assert quality["infrastructure"]["overall"] == "high"
        # $800K one-time is between 500K-2M, so "high"
        assert quality["one_time"]["overall"] == "high"
        assert "target" in quality["entity_filter"]

    def test_assess_quality_with_empty_data(self):
        """Quality assessment with empty data returns 'none' scores."""
        # Create empty run_rate costs
        headcount = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        headcount.total = 0

        apps = CostCategory(name="applications", display_name="Apps", icon="📱")
        apps.total = 0
        apps.items = []

        infra = CostCategory(name="infrastructure", display_name="Infra", icon="🖥️")
        infra.total = 0
        infra.items = []

        run_rate = RunRateCosts(
            headcount=headcount,
            applications=apps,
            infrastructure=infra,
            vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")
        )

        one_time = OneTimeCosts()
        one_time.total_mid = 0

        # Execute
        quality = _assess_data_quality_per_entity(run_rate, one_time, entity="buyer")

        # Verify - all should be "none" with empty data
        assert quality["headcount"]["overall"] == "none"
        assert quality["applications"]["overall"] == "none"
        assert quality["infrastructure"]["overall"] == "none"
        assert quality["one_time"]["overall"] == "none"
        assert "buyer" in quality["entity_filter"]

    def test_assess_quality_entity_all(self):
        """Quality assessment with entity='all' shows appropriate message."""
        headcount = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        headcount.total = 500_000

        run_rate = RunRateCosts(
            headcount=headcount,
            applications=CostCategory(name="applications", display_name="Apps", icon="📱"),
            infrastructure=CostCategory(name="infrastructure", display_name="Infra", icon="🖥️"),
            vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")
        )

        one_time = OneTimeCosts()

        # Execute with entity="all"
        quality = _assess_data_quality_per_entity(run_rate, one_time, entity="all")

        # Verify - entity_filter should mention "all"
        assert "all entities" in quality["entity_filter"].lower()

    def test_quality_notes_include_metrics(self):
        """Quality assessment notes include dollar amounts and counts."""
        headcount = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        headcount.total = 1_234_567

        apps = CostCategory(name="applications", display_name="Apps", icon="📱")
        apps.total = 987_654
        apps.items = [None] * 15  # 15 apps

        infra = CostCategory(name="infrastructure", display_name="Infra", icon="🖥️")
        infra.total = 456_789
        infra.items = [None] * 8  # 8 items

        run_rate = RunRateCosts(
            headcount=headcount,
            applications=apps,
            infrastructure=infra,
            vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")
        )

        one_time = OneTimeCosts()
        one_time.total_mid = 543_210

        # Execute
        quality = _assess_data_quality_per_entity(run_rate, one_time, entity="target")

        # Verify notes contain metrics
        assert "$1,234,567" in quality["headcount"]["note"]
        assert "15 applications" in quality["applications"]["note"]
        assert "$987,654" in quality["applications"]["note"]
        assert "8 infrastructure items" in quality["infrastructure"]["note"]
        assert "$456,789" in quality["infrastructure"]["note"]
        assert "$543,210" in quality["one_time"]["note"]

    def test_quality_thresholds_work_correctly(self):
        """Verify that quality thresholds work as specified."""
        # Headcount thresholds: [100K, 500K, 1M]
        headcount_low = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        headcount_low.total = 50_000  # Below 100K = low

        headcount_medium = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        headcount_medium.total = 300_000  # 100K-500K = medium

        headcount_high = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        headcount_high.total = 750_000  # 500K-1M = high

        headcount_very_high = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        headcount_very_high.total = 2_000_000  # Above 1M = very_high

        one_time = OneTimeCosts()

        # Test low
        run_rate_low = RunRateCosts(
            headcount=headcount_low,
            applications=CostCategory(name="applications", display_name="Apps", icon="📱"),
            infrastructure=CostCategory(name="infrastructure", display_name="Infra", icon="🖥️"),
            vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")
        )
        quality_low = _assess_data_quality_per_entity(run_rate_low, one_time, "target")
        assert quality_low["headcount"]["overall"] == "low"

        # Test medium
        run_rate_medium = RunRateCosts(
            headcount=headcount_medium,
            applications=CostCategory(name="applications", display_name="Apps", icon="📱"),
            infrastructure=CostCategory(name="infrastructure", display_name="Infra", icon="🖥️"),
            vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")
        )
        quality_medium = _assess_data_quality_per_entity(run_rate_medium, one_time, "target")
        assert quality_medium["headcount"]["overall"] == "medium"

        # Test high
        run_rate_high = RunRateCosts(
            headcount=headcount_high,
            applications=CostCategory(name="applications", display_name="Apps", icon="📱"),
            infrastructure=CostCategory(name="infrastructure", display_name="Infra", icon="🖥️"),
            vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")
        )
        quality_high = _assess_data_quality_per_entity(run_rate_high, one_time, "target")
        assert quality_high["headcount"]["overall"] == "high"

        # Test very_high
        run_rate_very_high = RunRateCosts(
            headcount=headcount_very_high,
            applications=CostCategory(name="applications", display_name="Apps", icon="📱"),
            infrastructure=CostCategory(name="infrastructure", display_name="Infra", icon="🖥️"),
            vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")
        )
        quality_very_high = _assess_data_quality_per_entity(run_rate_very_high, one_time, "target")
        assert quality_very_high["headcount"]["overall"] == "very_high"
