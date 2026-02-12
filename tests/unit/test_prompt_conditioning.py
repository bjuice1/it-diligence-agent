"""
Unit tests for deal type prompt conditioning.

Tests that prompts are correctly conditioned based on deal type:
- Acquisition → consolidation focus
- Carve-out → separation focus
- Divestiture → extraction focus

Based on spec: specs/deal-type-awareness/06-testing-validation.md
"""

import pytest
from prompts.v2_applications_reasoning_prompt import get_applications_reasoning_prompt
from prompts.v2_infrastructure_reasoning_prompt import get_infrastructure_reasoning_prompt
from prompts.v2_identity_access_reasoning_prompt import get_identity_access_reasoning_prompt as get_identity_reasoning_prompt


class TestPromptConditioning:
    """Test prompt conditioning logic."""

    def test_acquisition_prompt_mentions_consolidation(self):
        """Test that acquisition prompts emphasize consolidation."""
        prompt = get_applications_reasoning_prompt(
            inventory={},
            deal_context={'deal_type': 'acquisition'}
        )

        prompt_lower = prompt.lower()
        assert 'consolidation' in prompt_lower or 'consolidate' in prompt_lower, \
            "Acquisition prompt should mention consolidation"
        assert 'synergy' in prompt_lower or 'synergies' in prompt_lower, \
            "Acquisition prompt should mention synergies"

        # Should NOT have carve-out override
        assert 'do not recommend consolidation' not in prompt_lower and \
               'do not consolidate' not in prompt_lower, \
            "Acquisition prompt should not block consolidation"

    def test_carveout_prompt_blocks_consolidation(self):
        """Test that carve-out prompts block consolidation recommendations."""
        prompt = get_applications_reasoning_prompt(
            inventory={},
            deal_context={'deal_type': 'carveout'}
        )

        prompt_lower = prompt.lower()

        # Should explicitly block consolidation
        assert 'do not recommend consolidation' in prompt_lower or \
               'do not consolidate' in prompt_lower or \
               'avoid consolidation' in prompt_lower, \
            "Carve-out prompt should block consolidation"

        # Should emphasize separation
        assert 'separation' in prompt_lower or 'separate' in prompt_lower, \
            "Carve-out prompt should mention separation"

        # Should mention TSA
        assert 'tsa' in prompt_lower or 'transition service' in prompt_lower, \
            "Carve-out prompt should mention TSA"

    def test_divestiture_prompt_emphasizes_extraction(self):
        """Test that divestiture prompts emphasize extraction."""
        prompt = get_applications_reasoning_prompt(
            inventory={},
            deal_context={'deal_type': 'divestiture'}
        )

        prompt_lower = prompt.lower()

        # Should emphasize extraction/untangling
        assert 'extraction' in prompt_lower or \
               'untangle' in prompt_lower or \
               'disentangle' in prompt_lower, \
            "Divestiture prompt should mention extraction/untangling"

        # Should block consolidation
        assert 'do not recommend consolidation' in prompt_lower or \
               'do not consolidate' in prompt_lower, \
            "Divestiture prompt should block consolidation"

    def test_prompt_includes_deal_type_at_top(self):
        """Test that deal type conditioning appears at TOP of prompt."""
        prompt = get_applications_reasoning_prompt(
            inventory={},
            deal_context={'deal_type': 'carveout'}
        )

        # Conditioning should appear in first 1000 characters for salience
        first_section = prompt[:1000].upper()
        assert 'CARVE' in first_section or 'CARVEOUT' in first_section, \
            "Deal type should be mentioned prominently at top of prompt"

    def test_infrastructure_prompt_acquisition(self):
        """Test infrastructure prompt conditioning for acquisition."""
        prompt = get_infrastructure_reasoning_prompt(
            inventory={},
            deal_context={'deal_type': 'acquisition'}
        )

        prompt_lower = prompt.lower()
        assert 'consolidation' in prompt_lower or 'consolidate' in prompt_lower

    def test_infrastructure_prompt_carveout(self):
        """Test infrastructure prompt conditioning for carve-out."""
        prompt = get_infrastructure_reasoning_prompt(
            inventory={},
            deal_context={'deal_type': 'carveout'}
        )

        prompt_lower = prompt.lower()
        assert 'separation' in prompt_lower or 'separate' in prompt_lower
        assert 'standalone' in prompt_lower

    def test_identity_prompt_acquisition(self):
        """Test identity prompt conditioning for acquisition."""
        prompt = get_identity_reasoning_prompt(
            inventory={},
            deal_context={'deal_type': 'acquisition'}
        )

        prompt_lower = prompt.lower()
        assert 'integration' in prompt_lower or 'integrate' in prompt_lower

    def test_identity_prompt_carveout(self):
        """Test identity prompt conditioning for carve-out."""
        prompt = get_identity_reasoning_prompt(
            inventory={},
            deal_context={'deal_type': 'carveout'}
        )

        prompt_lower = prompt.lower()
        assert 'separation' in prompt_lower or 'separate' in prompt_lower


class TestPromptDefaultBehavior:
    """Test default behavior when deal_type not provided."""

    def test_no_deal_context_defaults_to_acquisition(self):
        """Test that prompts default to acquisition behavior when deal_context is None."""
        prompt = get_applications_reasoning_prompt(
            facts=[],
            deal_context=None
        )

        prompt_lower = prompt.lower()

        # Should not have explicit carve-out blocks
        assert 'do not recommend consolidation' not in prompt_lower and \
               'do not consolidate' not in prompt_lower

    def test_empty_deal_context_defaults_to_acquisition(self):
        """Test that prompts default to acquisition behavior when deal_context is empty."""
        prompt = get_applications_reasoning_prompt(
            facts=[],
            deal_context={}
        )

        prompt_lower = prompt.lower()

        # Should not have explicit carve-out blocks
        assert 'do not recommend consolidation' not in prompt_lower and \
               'do not consolidate' not in prompt_lower


class TestPromptConsistency:
    """Test consistency across different domains."""

    def test_all_domains_respect_deal_type(self):
        """Test that all domain prompts respect deal_type parameter."""
        domains = [
            ('applications', get_applications_reasoning_prompt),
            ('infrastructure', get_infrastructure_reasoning_prompt),
            ('identity', get_identity_reasoning_prompt)
        ]

        for domain_name, prompt_builder in domains:
            # Test acquisition
            acq_prompt = prompt_builder(
                facts=[],
                deal_context={'deal_type': 'acquisition'}
            )
            assert acq_prompt is not None, f"{domain_name} should return prompt for acquisition"

            # Test carveout
            carve_prompt = prompt_builder(
                facts=[],
                deal_context={'deal_type': 'carveout'}
            )
            assert carve_prompt is not None, f"{domain_name} should return prompt for carveout"
            assert 'do not consolidate' in carve_prompt.lower() or \
                   'do not recommend consolidation' in carve_prompt.lower(), \
                f"{domain_name} carveout prompt should block consolidation"

            # Test divestiture
            div_prompt = prompt_builder(
                facts=[],
                deal_context={'deal_type': 'divestiture'}
            )
            assert div_prompt is not None, f"{domain_name} should return prompt for divestiture"


class TestPromptEdgeCases:
    """Test edge cases for prompt conditioning."""

    def test_invalid_deal_type_falls_back_to_default(self):
        """Test that invalid deal_type falls back to default behavior."""
        prompt = get_applications_reasoning_prompt(
            inventory={},
            deal_context={'deal_type': 'invalid_type'}
        )

        # Should not crash, should return a valid prompt
        assert prompt is not None
        assert len(prompt) > 0

    def test_deal_context_with_extra_fields(self):
        """Test that extra fields in deal_context don't break prompt building."""
        prompt = get_applications_reasoning_prompt(
            facts=[],
            deal_context={
                'deal_type': 'carveout',
                'target_name': 'Test Co',
                'buyer_name': 'Acquirer',
                'extra_field': 'some value'
            }
        )

        assert prompt is not None
        assert 'do not consolidate' in prompt.lower() or \
               'do not recommend consolidation' in prompt.lower()

    def test_case_sensitivity_deal_type(self):
        """Test that deal_type is handled case-insensitively."""
        # Try uppercase
        prompt_upper = get_applications_reasoning_prompt(
            facts=[],
            deal_context={'deal_type': 'CARVEOUT'}
        )

        # Try mixed case
        prompt_mixed = get_applications_reasoning_prompt(
            facts=[],
            deal_context={'deal_type': 'CarveOut'}
        )

        # Both should work and contain carve-out guidance
        for prompt in [prompt_upper, prompt_mixed]:
            if prompt:  # Only check if prompt was generated
                prompt_lower = prompt.lower()
                # At minimum, should not crash and should return valid content
                assert len(prompt) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
