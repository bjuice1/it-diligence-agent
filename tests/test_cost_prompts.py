"""Tests for cost guidance in reasoning prompts.

Spec 06: Validates shared cost estimation guidance content,
all 6 domain prompts include cost guidance, and domain-specific
anchor keys appear in the correct prompts.
"""
import pytest
import importlib

from prompts.shared.cost_estimation_guidance import get_cost_estimation_guidance


class TestSharedGuidance:
    """Verify shared cost estimation guidance content."""

    def test_guidance_includes_anchor_table(self):
        """Guidance should include the COST ANCHORS REFERENCE TABLE."""
        guidance = get_cost_estimation_guidance()
        assert "COST ANCHORS REFERENCE TABLE" in guidance
        assert "anchor_key" in guidance

    def test_guidance_includes_worked_examples(self):
        """Guidance should include worked examples for each estimation method."""
        guidance = get_cost_estimation_guidance()
        assert "Worked Example: per_user" in guidance
        assert "Worked Example: per_app" in guidance
        assert "Worked Example: fixed_by_size" in guidance
        assert "Worked Example: fixed_by_complexity" in guidance

    def test_guidance_includes_critical_rules(self):
        """Guidance should include the critical rules for cost estimation."""
        guidance = get_cost_estimation_guidance()
        assert "quantity MUST come from cited facts" in guidance
        assert "source_facts MUST reference real fact IDs" in guidance

    def test_guidance_includes_cost_buildup_structure(self):
        """Guidance should explain the cost_buildup object structure."""
        guidance = get_cost_estimation_guidance()
        assert "cost_buildup" in guidance
        assert "anchor_key" in guidance
        assert "quantity" in guidance
        assert "unit_label" in guidance

    def test_guidance_includes_estimation_methods_table(self):
        """Guidance should include the estimation methods table."""
        guidance = get_cost_estimation_guidance()
        assert "Estimation Methods" in guidance
        assert "per_user" in guidance
        assert "per_app" in guidance
        assert "fixed_by_size" in guidance

    def test_guidance_includes_key_anchor_keys(self):
        """Guidance should list all major anchor keys."""
        guidance = get_cost_estimation_guidance()
        key_anchors = [
            "app_migration_simple",
            "app_migration_moderate",
            "app_migration_complex",
            "dc_migration",
            "cloud_migration",
            "identity_separation",
            "network_separation",
            "security_remediation",
            "pmo_overhead",
        ]
        for anchor in key_anchors:
            assert anchor in guidance, f"Anchor key '{anchor}' should be in guidance"


class TestAllDomainsHaveGuidance:
    """Verify all 6 domain prompts include cost guidance."""

    @pytest.mark.parametrize("module_name,func_name", [
        ("v2_infrastructure_reasoning_prompt", "get_infrastructure_reasoning_prompt"),
        ("v2_network_reasoning_prompt", "get_network_reasoning_prompt"),
        ("v2_cybersecurity_reasoning_prompt", "get_cybersecurity_reasoning_prompt"),
        ("v2_applications_reasoning_prompt", "get_applications_reasoning_prompt"),
        ("v2_identity_access_reasoning_prompt", "get_identity_access_reasoning_prompt"),
        ("v2_organization_reasoning_prompt", "get_organization_reasoning_prompt"),
    ])
    def test_prompt_includes_cost_guidance(self, module_name, func_name):
        """Each domain reasoning prompt should include cost estimation guidance."""
        module = importlib.import_module(f"prompts.{module_name}")
        func = getattr(module, func_name)
        # These functions require inventory and deal_context args
        prompt = func(inventory={}, deal_context={})
        assert "COST ANCHORS REFERENCE TABLE" in prompt, (
            f"{func_name} should include COST ANCHORS REFERENCE TABLE"
        )
        assert "cost_buildup" in prompt, (
            f"{func_name} should include cost_buildup guidance"
        )

    @pytest.mark.parametrize("module_name", [
        "v2_infrastructure_reasoning_prompt",
        "v2_network_reasoning_prompt",
        "v2_cybersecurity_reasoning_prompt",
        "v2_applications_reasoning_prompt",
        "v2_identity_access_reasoning_prompt",
        "v2_organization_reasoning_prompt",
    ])
    def test_prompt_module_imports_cost_guidance(self, module_name):
        """Each domain prompt module should import get_cost_estimation_guidance."""
        module = importlib.import_module(f"prompts.{module_name}")
        source = importlib.import_module(f"prompts.{module_name}")
        # Check that cost_estimation_guidance is used (imported)
        import inspect
        source_code = inspect.getsource(module)
        assert "cost_estimation_guidance" in source_code, (
            f"{module_name} should import from cost_estimation_guidance"
        )


class TestDomainSpecificAnchors:
    """Verify domain-specific anchor keys appear in correct prompts."""

    def test_infrastructure_has_dc_migration(self):
        """Infrastructure prompt should reference dc_migration anchor."""
        from prompts.v2_infrastructure_reasoning_prompt import get_infrastructure_reasoning_prompt
        prompt = get_infrastructure_reasoning_prompt(inventory={}, deal_context={})
        assert "dc_migration" in prompt

    def test_infrastructure_has_cloud_migration(self):
        """Infrastructure prompt should reference cloud_migration anchor."""
        from prompts.v2_infrastructure_reasoning_prompt import get_infrastructure_reasoning_prompt
        prompt = get_infrastructure_reasoning_prompt(inventory={}, deal_context={})
        assert "cloud_migration" in prompt

    def test_applications_has_app_migration(self):
        """Applications prompt should reference app migration anchors."""
        from prompts.v2_applications_reasoning_prompt import get_applications_reasoning_prompt
        prompt = get_applications_reasoning_prompt(inventory={}, deal_context={})
        assert "app_migration_simple" in prompt
        assert "app_migration_complex" in prompt

    def test_identity_has_identity_separation(self):
        """Identity/access prompt should reference identity_separation anchor."""
        from prompts.v2_identity_access_reasoning_prompt import get_identity_access_reasoning_prompt
        prompt = get_identity_access_reasoning_prompt(inventory={}, deal_context={})
        assert "identity_separation" in prompt

    def test_network_has_network_separation(self):
        """Network prompt should reference network_separation anchor."""
        from prompts.v2_network_reasoning_prompt import get_network_reasoning_prompt
        prompt = get_network_reasoning_prompt(inventory={}, deal_context={})
        assert "network_separation" in prompt

    def test_cybersecurity_has_security_anchors(self):
        """Cybersecurity prompt should reference security anchors."""
        from prompts.v2_cybersecurity_reasoning_prompt import get_cybersecurity_reasoning_prompt
        prompt = get_cybersecurity_reasoning_prompt(inventory={}, deal_context={})
        assert "security_remediation" in prompt
        assert "security_tool_deployment" in prompt

    def test_organization_has_pmo_overhead(self):
        """Organization prompt should reference pmo_overhead anchor."""
        from prompts.v2_organization_reasoning_prompt import get_organization_reasoning_prompt
        prompt = get_organization_reasoning_prompt(inventory={}, deal_context={})
        assert "pmo_overhead" in prompt
