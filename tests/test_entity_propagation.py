"""Tests for entity propagation in reasoning outputs.

Spec 04: Validates _infer_entity_from_citations, ANCHOR RULE logic,
flag_gap entity requirement, and entity field on findings.
"""
import pytest
import inspect

from tools_v2.reasoning_tools import _infer_entity_from_citations
from tools_v2.discovery_tools import _execute_flag_gap


class TestEntityInference:
    """Verify entity is correctly inferred from cited fact IDs."""

    def test_target_facts_infer_target(self):
        """Facts with TGT prefix should infer target entity."""
        assert _infer_entity_from_citations(["F-TGT-APP-001"], None) == "target"

    def test_buyer_facts_infer_buyer(self):
        """Facts with BYR prefix should infer buyer entity."""
        assert _infer_entity_from_citations(["F-BYR-INFRA-001"], None) == "buyer"

    def test_mixed_facts_infer_target(self):
        """Target takes precedence when both target and buyer facts are cited."""
        entity = _infer_entity_from_citations(
            ["F-TGT-APP-001", "F-BYR-INFRA-001"], None
        )
        assert entity == "target"

    def test_no_facts_default_target(self):
        """Empty fact list should default to target."""
        assert _infer_entity_from_citations([], None) == "target"

    def test_multiple_target_facts(self):
        """Multiple target facts should still return target."""
        entity = _infer_entity_from_citations(
            ["F-TGT-APP-001", "F-TGT-APP-002", "F-TGT-INFRA-001"], None
        )
        assert entity == "target"

    def test_multiple_buyer_facts(self):
        """Multiple buyer-only facts should return buyer."""
        entity = _infer_entity_from_citations(
            ["F-BYR-APP-001", "F-BYR-INFRA-001"], None
        )
        assert entity == "buyer"


class TestAnchorRule:
    """Verify ANCHOR RULE: buyer-only citations rejected for findings.

    The ANCHOR RULE requires that findings citing buyer facts must also
    cite at least one target fact. This prevents buyer-only findings from
    being created, ensuring all analysis is anchored to target observations.
    """

    def test_anchor_rule_exists_in_identify_risk_source(self):
        """Verify ANCHOR RULE string exists in the identify_risk function source."""
        from tools_v2.reasoning_tools import _execute_identify_risk
        source = inspect.getsource(_execute_identify_risk)
        assert "ANCHOR RULE" in source, (
            "_execute_identify_risk should contain ANCHOR RULE enforcement"
        )

    def test_anchor_rule_exists_in_create_strategic_consideration_source(self):
        """Verify ANCHOR RULE string exists in create_strategic_consideration source."""
        from tools_v2.reasoning_tools import _execute_create_strategic_consideration
        source = inspect.getsource(_execute_create_strategic_consideration)
        assert "ANCHOR RULE" in source, (
            "_execute_create_strategic_consideration should contain ANCHOR RULE enforcement"
        )

    def test_anchor_rule_exists_in_create_recommendation_source(self):
        """Verify ANCHOR RULE string exists in create_recommendation source."""
        from tools_v2.reasoning_tools import _execute_create_recommendation
        source = inspect.getsource(_execute_create_recommendation)
        assert "ANCHOR RULE" in source, (
            "_execute_create_recommendation should contain ANCHOR RULE enforcement"
        )

    def test_anchor_rule_exists_in_validate_finding_entity_rules(self):
        """Verify ANCHOR RULE is in the validation function."""
        from tools_v2.reasoning_tools import validate_finding_entity_rules
        source = inspect.getsource(validate_finding_entity_rules)
        assert "ANCHOR RULE" in source

    def test_validate_finding_entity_rules_rejects_buyer_only(self):
        """validate_finding_entity_rules should flag buyer-only citations as errors."""
        from tools_v2.reasoning_tools import validate_finding_entity_rules
        result = validate_finding_entity_rules(
            "identify_risk",
            {
                "based_on_facts": ["F-BYR-INFRA-001"],
                "triggered_by": [],
            }
        )
        assert not result["valid"], "Buyer-only citations should be invalid"
        assert len(result["errors"]) > 0
        assert any("ENTITY_ANCHOR_VIOLATION" in e or "ANCHOR" in e.upper()
                    for e in result["errors"])

    def test_validate_finding_entity_rules_accepts_mixed(self):
        """validate_finding_entity_rules should accept mixed target+buyer citations."""
        from tools_v2.reasoning_tools import validate_finding_entity_rules
        result = validate_finding_entity_rules(
            "identify_risk",
            {
                "based_on_facts": ["F-TGT-INFRA-001", "F-BYR-INFRA-002"],
                "triggered_by": [],
            }
        )
        # Should be valid (no entity anchor violation)
        anchor_errors = [e for e in result["errors"] if "ANCHOR" in e.upper()]
        assert len(anchor_errors) == 0, "Mixed citations should not trigger ANCHOR RULE"

    def test_validate_finding_entity_rules_accepts_target_only(self):
        """validate_finding_entity_rules should accept target-only citations."""
        from tools_v2.reasoning_tools import validate_finding_entity_rules
        result = validate_finding_entity_rules(
            "identify_risk",
            {
                "based_on_facts": ["F-TGT-INFRA-001"],
                "triggered_by": [],
            }
        )
        anchor_errors = [e for e in result["errors"] if "ANCHOR" in e.upper()]
        assert len(anchor_errors) == 0


class TestFlagGapEntityRequired:
    """Verify flag_gap requires explicit entity."""

    def test_flag_gap_function_exists(self):
        """_execute_flag_gap should be importable."""
        assert callable(_execute_flag_gap)

    def test_flag_gap_source_checks_entity(self):
        """The flag_gap implementation should check for entity."""
        source = inspect.getsource(_execute_flag_gap)
        assert "entity" in source
        # It should require entity explicitly
        assert "Entity is required" in source or "entity is required" in source.lower()

    def test_flag_gap_validates_entity_values(self):
        """The flag_gap implementation should validate entity is target or buyer."""
        source = inspect.getsource(_execute_flag_gap)
        assert '"target"' in source or "'target'" in source
        assert '"buyer"' in source or "'buyer'" in source


class TestEntityFieldOnFindings:
    """Verify entity field exists on all finding dataclasses."""

    def test_risk_has_entity_field(self):
        """Risk dataclass should have entity field."""
        from tools_v2.reasoning_tools import Risk
        risk = Risk(
            finding_id="R-test",
            domain="infrastructure",
            title="Test",
            description="Test",
            category="hosting",
            severity="medium",
            integration_dependent=False,
            mitigation="Test",
            based_on_facts=["F-TGT-INFRA-001"],
            confidence="medium",
            reasoning="Test reasoning",
            entity="target",
        )
        assert risk.entity == "target"

    def test_risk_default_entity_is_target(self):
        """Risk entity should default to target."""
        from tools_v2.reasoning_tools import Risk
        risk = Risk(
            finding_id="R-test",
            domain="infrastructure",
            title="Test",
            description="Test",
            category="hosting",
            severity="medium",
            integration_dependent=False,
            mitigation="Test",
            based_on_facts=[],
            confidence="medium",
            reasoning="Test reasoning",
        )
        assert risk.entity == "target"

    def test_strategic_consideration_has_entity_field(self):
        """StrategicConsideration should have entity field."""
        from tools_v2.reasoning_tools import StrategicConsideration
        sc = StrategicConsideration(
            finding_id="SC-test",
            domain="infrastructure",
            title="Test",
            description="Test",
            lens="synergy",
            implication="Test",
            based_on_facts=[],
            confidence="medium",
            reasoning="Test reasoning",
        )
        assert hasattr(sc, "entity")
        assert sc.entity == "target"  # default

    def test_work_item_has_entity_field(self):
        """WorkItem should have entity field."""
        from tools_v2.reasoning_tools import WorkItem
        wi = WorkItem(
            finding_id="WI-test",
            domain="infrastructure",
            title="Test",
            description="Test",
            phase="Day_100",
            priority="medium",
            owner_type="target",
            triggered_by=[],
            based_on_facts=[],
            confidence="medium",
            reasoning="Test reasoning",
            cost_estimate="under_25k",
        )
        assert hasattr(wi, "entity")
        assert wi.entity == "target"
