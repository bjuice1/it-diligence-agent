"""Tests for CostBuildUp wiring: tool creation, calculator preference, persistence.

Spec 05: Validates estimate_cost returns CostBuildUp, calculator prefers
CostBuildUp over ranges, serialization round-trip, and tool schema.
"""
import pytest
from dataclasses import dataclass, field
from typing import Optional, List

from tools_v2.cost_estimator import estimate_cost
from tools_v2.reasoning_tools import CostBuildUp, WorkItem
from tools_v2.cost_calculator import calculate_costs_from_work_items


def _make_work_item(
    cost_estimate: str = "under_25k",
    cost_buildup: Optional[CostBuildUp] = None,
    finding_id: str = "WI-test",
    domain: str = "applications",
    phase: str = "Day_100",
    owner_type: str = "buyer",
) -> WorkItem:
    """Helper to create a WorkItem for testing."""
    return WorkItem(
        finding_id=finding_id,
        domain=domain,
        title="Test Work Item",
        description="Test description",
        phase=phase,
        priority="medium",
        owner_type=owner_type,
        triggered_by=["F-TGT-APP-001"],
        based_on_facts=["F-TGT-APP-001"],
        confidence="medium",
        reasoning="Test reasoning " * 10,
        cost_estimate=cost_estimate,
        cost_buildup=cost_buildup,
    )


class TestCostBuildUpCreation:
    """Verify estimate_cost() returns CostBuildUp with valid fields."""

    def test_estimate_cost_returns_cost_buildup(self):
        """estimate_cost should return a CostBuildUp object for valid anchor keys."""
        cb = estimate_cost("identity_separation", quantity=1, size_tier="medium")
        assert cb is not None
        assert isinstance(cb, CostBuildUp)

    def test_estimate_cost_has_valid_fields(self):
        """CostBuildUp should have all required fields populated."""
        cb = estimate_cost(
            "app_migration_simple",
            quantity=5,
            source_facts=["F-TGT-APP-001"],
            assumptions=["5 simple apps from inventory"],
        )
        assert cb is not None
        assert cb.anchor_key == "app_migration_simple"
        assert cb.quantity == 5
        assert cb.total_low > 0
        assert cb.total_high > cb.total_low
        assert cb.unit_label != ""
        assert cb.anchor_name != ""

    def test_estimate_cost_invalid_anchor_returns_none(self):
        """estimate_cost should return None for unknown anchor keys."""
        cb = estimate_cost("nonexistent_anchor_key_xyz")
        assert cb is None

    def test_estimate_cost_per_app(self):
        """Per-app estimation should scale with quantity."""
        cb1 = estimate_cost("app_migration_simple", quantity=1)
        cb5 = estimate_cost("app_migration_simple", quantity=5)
        assert cb1 is not None
        assert cb5 is not None
        # 5 apps should cost more than 1 app (accounting for possible volume discount)
        assert cb5.total_low >= cb1.total_low
        assert cb5.total_high >= cb1.total_high

    def test_estimate_cost_fixed_by_size(self):
        """Fixed-by-size estimation should vary by tier."""
        cb_small = estimate_cost("identity_separation", quantity=1, size_tier="small")
        cb_large = estimate_cost("identity_separation", quantity=1, size_tier="large")
        assert cb_small is not None
        assert cb_large is not None
        # Large should cost more than small
        assert cb_large.total_high >= cb_small.total_high

    def test_estimate_cost_preserves_source_facts(self):
        """Source facts and assumptions should be preserved."""
        cb = estimate_cost(
            "cloud_migration",
            quantity=10,
            source_facts=["F-TGT-APP-001", "F-TGT-APP-002"],
            assumptions=["10 cloud apps identified"],
            notes="Excludes ERP",
        )
        assert cb is not None
        assert cb.source_facts == ["F-TGT-APP-001", "F-TGT-APP-002"]
        assert "10 cloud apps identified" in cb.assumptions
        assert cb.notes == "Excludes ERP"


class TestCostCalculatorPreference:
    """Verify calculator prefers CostBuildUp over string ranges."""

    def test_prefers_buildup_totals(self):
        """When CostBuildUp exists, calculator should use its totals."""
        cb = estimate_cost("identity_separation", quantity=1, size_tier="medium")
        assert cb is not None

        wi_with = _make_work_item(
            cost_estimate="250k_to_500k",
            cost_buildup=cb,
            finding_id="WI-001",
        )
        wi_without = _make_work_item(
            cost_estimate="25k_to_100k",
            cost_buildup=None,
            finding_id="WI-002",
        )

        breakdown = calculate_costs_from_work_items([wi_with, wi_without])

        # First item should use cost_buildup
        assert breakdown.work_item_costs[0]["estimation_source"] == "cost_buildup"
        assert breakdown.work_item_costs[0]["low"] == cb.total_low

        # Second item should fallback to cost_range
        assert breakdown.work_item_costs[1]["estimation_source"] == "cost_range"
        assert breakdown.work_item_costs[1]["low"] == 25_000

    def test_all_range_only_works(self):
        """All work items with only cost_estimate should work as before."""
        items = [
            _make_work_item(cost_estimate="under_25k", finding_id="WI-001"),
            _make_work_item(cost_estimate="100k_to_250k", finding_id="WI-002"),
        ]
        breakdown = calculate_costs_from_work_items(items)
        # under_25k: low=0, high=25000
        # 100k_to_250k: low=100000, high=250000
        assert breakdown.total_low == 100_000  # 0 + 100K
        assert breakdown.total_high == 275_000  # 25K + 250K

    def test_all_buildup_works(self):
        """All work items with CostBuildUp should use precise amounts."""
        cb1 = estimate_cost("app_migration_simple", quantity=3)
        cb2 = estimate_cost("cloud_migration", quantity=5)
        assert cb1 is not None
        assert cb2 is not None

        items = [
            _make_work_item(cost_estimate="25k_to_100k", cost_buildup=cb1, finding_id="WI-001"),
            _make_work_item(cost_estimate="100k_to_250k", cost_buildup=cb2, finding_id="WI-002"),
        ]
        breakdown = calculate_costs_from_work_items(items)
        assert breakdown.total_low == cb1.total_low + cb2.total_low
        assert breakdown.total_high == cb1.total_high + cb2.total_high

    def test_empty_work_items(self):
        """Empty list should produce zero totals."""
        breakdown = calculate_costs_from_work_items([])
        assert breakdown.total_low == 0
        assert breakdown.total_high == 0
        assert breakdown.total_work_items == 0


class TestCostBuildUpSerialization:
    """Verify to_dict/from_dict round-trip for CostBuildUp."""

    def test_cost_buildup_to_dict(self):
        """CostBuildUp.to_dict should include all fields."""
        cb = estimate_cost("app_migration_simple", quantity=5)
        assert cb is not None
        d = cb.to_dict()
        assert d["anchor_key"] == "app_migration_simple"
        assert d["quantity"] == 5
        assert "total_low" in d
        assert "total_high" in d
        assert "unit_cost_low" in d
        assert "unit_cost_high" in d
        assert "estimation_method" in d

    def test_cost_buildup_from_dict(self):
        """CostBuildUp.from_dict should restore all fields."""
        cb = estimate_cost("identity_separation", quantity=1, size_tier="small")
        assert cb is not None
        d = cb.to_dict()
        restored = CostBuildUp.from_dict(d)
        assert restored.anchor_key == cb.anchor_key
        assert restored.total_low == cb.total_low
        assert restored.total_high == cb.total_high
        assert restored.quantity == cb.quantity

    def test_cost_buildup_round_trip(self):
        """Full round-trip: CostBuildUp -> dict -> CostBuildUp should be identical."""
        cb = estimate_cost(
            "cloud_migration",
            quantity=10,
            source_facts=["F-TGT-APP-001"],
            assumptions=["10 cloud apps"],
            notes="Test notes",
        )
        assert cb is not None
        d = cb.to_dict()
        restored = CostBuildUp.from_dict(d)
        assert restored.to_dict() == d

    def test_work_item_to_dict_includes_buildup(self):
        """WorkItem.to_dict should include cost_buildup when present."""
        cb = estimate_cost("cloud_migration", quantity=10)
        assert cb is not None
        wi = _make_work_item(cost_buildup=cb)
        d = wi.to_dict()
        assert "cost_buildup" in d
        assert d["cost_buildup"] is not None
        assert d["cost_buildup"]["anchor_key"] == "cloud_migration"

    def test_work_item_to_dict_none_buildup(self):
        """WorkItem.to_dict should have None cost_buildup when not present."""
        wi = _make_work_item(cost_buildup=None)
        d = wi.to_dict()
        assert "cost_buildup" in d
        assert d["cost_buildup"] is None


class TestToolSchema:
    """Verify create_work_item tool schema includes cost_buildup."""

    def test_work_item_dataclass_has_cost_buildup_field(self):
        """WorkItem should have a cost_buildup field."""
        from tools_v2.reasoning_tools import WorkItem
        import dataclasses
        field_names = [f.name for f in dataclasses.fields(WorkItem)]
        assert "cost_buildup" in field_names

    def test_cost_buildup_is_optional(self):
        """cost_buildup should be Optional (defaults to None)."""
        wi = WorkItem(
            finding_id="WI-test",
            domain="applications",
            title="Test",
            description="Test",
            phase="Day_100",
            priority="medium",
            owner_type="buyer",
            triggered_by=[],
            based_on_facts=[],
            confidence="medium",
            reasoning="Test",
            cost_estimate="under_25k",
        )
        assert wi.cost_buildup is None

    def test_get_cost_range_key(self):
        """CostBuildUp.get_cost_range_key should return valid range string."""
        cb = estimate_cost("app_migration_simple", quantity=1)
        assert cb is not None
        range_key = cb.get_cost_range_key()
        valid_ranges = ["under_25k", "25k_to_100k", "100k_to_500k", "500k_to_1m", "over_1m"]
        assert range_key in valid_ranges

    def test_format_summary(self):
        """CostBuildUp.format_summary should return a readable string."""
        cb = estimate_cost("app_migration_simple", quantity=5)
        assert cb is not None
        summary = cb.format_summary()
        assert isinstance(summary, str)
        assert "$" in summary  # Should contain dollar amounts
        assert len(summary) > 10
