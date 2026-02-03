"""
Tests for Phase 6: Cost Estimation Determinism

Tests:
- Cost cache functionality
- Input normalization
- Deterministic hash generation
- Consistent results from same inputs
- Rule processing order
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# COST CACHE TESTS
# =============================================================================

class TestCostCache:
    """Tests for tools_v2/cost_cache.py"""

    def test_cache_creation(self):
        """Cache should be created with default settings."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()
        assert cache is not None
        assert len(cache) == 0
        assert cache.max_entries == 1000

    def test_cache_set_and_get(self):
        """Cache should store and retrieve estimates."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()

        estimate = {"total_low": 100000, "total_high": 200000}
        facts = [{"content": "Using SAP ERP", "fact_id": "F-001"}]

        cache.set(estimate, user_count=1500, deal_type="carveout", facts=facts)

        retrieved = cache.get(user_count=1500, deal_type="carveout", facts=facts)
        assert retrieved is not None
        assert retrieved["total_low"] == 100000
        assert retrieved["total_high"] == 200000

    def test_cache_miss(self):
        """Cache should return None for unknown keys."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()
        facts = [{"content": "Test fact"}]

        result = cache.get(user_count=1000, deal_type="carveout", facts=facts)
        assert result is None

    def test_cache_key_determinism(self):
        """Same inputs should always produce same cache key."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()
        facts = [{"content": "Using SAP", "fact_id": "F-001"}]

        key1 = cache.get_cache_key(user_count=1500, deal_type="carveout", facts=facts)
        key2 = cache.get_cache_key(user_count=1500, deal_type="carveout", facts=facts)
        key3 = cache.get_cache_key(user_count=1500, deal_type="carveout", facts=facts)

        assert key1 == key2 == key3

    def test_cache_key_differs_for_different_inputs(self):
        """Different inputs should produce different cache keys."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()
        facts = [{"content": "Using SAP"}]

        key1 = cache.get_cache_key(user_count=1500, deal_type="carveout", facts=facts)
        key2 = cache.get_cache_key(user_count=2000, deal_type="carveout", facts=facts)
        key3 = cache.get_cache_key(user_count=1500, deal_type="acquisition", facts=facts)

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_cache_invalidation(self):
        """Cache entries should be invalidatable."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()
        estimate = {"total": 100000}
        facts = [{"content": "Test"}]

        cache_key = cache.set(estimate, user_count=1000, deal_type="carveout", facts=facts)

        # Verify it's cached
        assert cache.get(user_count=1000, deal_type="carveout", facts=facts) is not None

        # Invalidate
        cache.invalidate(cache_key)

        # Verify it's gone
        assert cache.get(user_count=1000, deal_type="carveout", facts=facts) is None

    def test_cache_clear(self):
        """Cache should be clearable."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()
        facts = [{"content": "Test"}]

        cache.set({"a": 1}, user_count=100, deal_type="carveout", facts=facts)
        cache.set({"b": 2}, user_count=200, deal_type="carveout", facts=facts)

        assert len(cache) == 2

        cleared = cache.clear()
        assert cleared == 2
        assert len(cache) == 0

    def test_cache_eviction(self):
        """Cache should evict oldest entries when full."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache(max_entries=3)
        facts = [{"content": "Test"}]

        cache.set({"id": 1}, user_count=100, deal_type="carveout", facts=facts)
        cache.set({"id": 2}, user_count=200, deal_type="carveout", facts=facts)
        cache.set({"id": 3}, user_count=300, deal_type="carveout", facts=facts)
        cache.set({"id": 4}, user_count=400, deal_type="carveout", facts=facts)

        # Should have evicted one entry
        assert len(cache) == 3

    def test_cache_stats(self):
        """Cache should track statistics."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()
        facts = [{"content": "Test"}]

        estimate = {"value": 1}
        cache.set(estimate, user_count=100, deal_type="carveout", facts=facts)

        # One hit
        cache.get(user_count=100, deal_type="carveout", facts=facts)
        # One miss
        cache.get(user_count=999, deal_type="carveout", facts=facts)

        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["entries"] == 1


# =============================================================================
# INPUT NORMALIZATION TESTS
# =============================================================================

class TestInputNormalization:
    """Tests for input normalization."""

    def test_normalize_facts_sorts_by_content(self):
        """Facts should be sorted by content."""
        from tools_v2.cost_cache import normalize_facts_for_estimation

        facts = [
            {"content": "Zebra fact", "fact_id": "F-003"},
            {"content": "Apple fact", "fact_id": "F-001"},
            {"content": "Middle fact", "fact_id": "F-002"},
        ]

        normalized = normalize_facts_for_estimation(facts)

        assert normalized[0]["content"] == "Apple fact"
        assert normalized[1]["content"] == "Middle fact"
        assert normalized[2]["content"] == "Zebra fact"

    def test_normalize_facts_removes_duplicates(self):
        """Duplicate facts should be removed."""
        from tools_v2.cost_cache import normalize_facts_for_estimation

        facts = [
            {"content": "Same fact", "fact_id": "F-001"},
            {"content": "Same fact", "fact_id": "F-002"},
            {"content": "Different fact", "fact_id": "F-003"},
        ]

        normalized = normalize_facts_for_estimation(facts)

        assert len(normalized) == 2

    def test_normalize_facts_strips_whitespace(self):
        """Whitespace should be stripped."""
        from tools_v2.cost_cache import normalize_facts_for_estimation

        facts = [
            {"content": "  padded fact  ", "fact_id": "F-001"},
        ]

        normalized = normalize_facts_for_estimation(facts)

        assert normalized[0]["content"] == "padded fact"

    def test_cache_key_case_insensitive(self):
        """Cache keys should be case insensitive for deal_type."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()
        facts = [{"content": "Test"}]

        key1 = cache.get_cache_key(user_count=100, deal_type="CARVEOUT", facts=facts)
        key2 = cache.get_cache_key(user_count=100, deal_type="carveout", facts=facts)
        key3 = cache.get_cache_key(user_count=100, deal_type="Carveout", facts=facts)

        assert key1 == key2 == key3

    def test_cache_key_ignores_fact_order(self):
        """Cache keys should be same regardless of fact order."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()

        facts1 = [
            {"content": "Alpha"},
            {"content": "Beta"},
            {"content": "Gamma"},
        ]
        facts2 = [
            {"content": "Gamma"},
            {"content": "Alpha"},
            {"content": "Beta"},
        ]

        key1 = cache.get_cache_key(user_count=100, deal_type="carveout", facts=facts1)
        key2 = cache.get_cache_key(user_count=100, deal_type="carveout", facts=facts2)

        assert key1 == key2


# =============================================================================
# DETERMINISTIC HASH TESTS
# =============================================================================

class TestDeterministicHash:
    """Tests for deterministic hash generation."""

    def test_hash_consistency_across_calls(self):
        """Same inputs should produce same hash across multiple calls."""
        from tools_v2.cost_cache import get_deterministic_estimate_hash

        facts = [{"content": "SAP ERP system", "fact_id": "F-001"}]

        hashes = [
            get_deterministic_estimate_hash(
                user_count=1500,
                deal_type="carveout",
                facts=facts,
                app_count=20
            )
            for _ in range(10)
        ]

        # All hashes should be identical
        assert len(set(hashes)) == 1

    def test_hash_changes_with_inputs(self):
        """Different inputs should produce different hashes."""
        from tools_v2.cost_cache import get_deterministic_estimate_hash

        facts = [{"content": "Test fact"}]

        hash1 = get_deterministic_estimate_hash(
            user_count=1000, deal_type="carveout", facts=facts
        )
        hash2 = get_deterministic_estimate_hash(
            user_count=1001, deal_type="carveout", facts=facts
        )
        hash3 = get_deterministic_estimate_hash(
            user_count=1000, deal_type="acquisition", facts=facts
        )

        assert hash1 != hash2
        assert hash1 != hash3


# =============================================================================
# COST MODEL DETERMINISM TESTS
# =============================================================================

class TestCostModelDeterminism:
    """Tests for CostModel deterministic behavior."""

    def test_rules_sorted_by_id(self):
        """Rules should be sorted by rule_id for consistent processing."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)

        rule_ids = [r.rule_id for r in model.rules]

        assert rule_ids == sorted(rule_ids)

    def test_same_inputs_same_output(self):
        """Same inputs should always produce same output."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)

        facts = [
            {"content": "Using SAP ERP", "fact_id": "F-001"},
            {"content": "2500 employees", "fact_id": "F-002"},
        ]

        result1 = model.estimate_costs(
            user_count=2500,
            deal_type="carveout",
            facts=facts,
            app_count=30,
        )

        result2 = model.estimate_costs(
            user_count=2500,
            deal_type="carveout",
            facts=facts,
            app_count=30,
        )

        # Results should be identical
        assert result1["grand_total"] == result2["grand_total"]
        assert result1["separation_subtotal"] == result2["separation_subtotal"]
        assert result1["input_hash"] == result2["input_hash"]

    def test_fact_order_independence(self):
        """Result should be same regardless of fact order."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)

        facts1 = [
            {"content": "SAP ERP", "fact_id": "F-001"},
            {"content": "Healthcare company", "fact_id": "F-002"},
            {"content": "Global operations", "fact_id": "F-003"},
        ]

        facts2 = [
            {"content": "Global operations", "fact_id": "F-003"},
            {"content": "SAP ERP", "fact_id": "F-001"},
            {"content": "Healthcare company", "fact_id": "F-002"},
        ]

        result1 = model.estimate_costs(
            user_count=2000,
            deal_type="carveout",
            facts=facts1,
        )

        result2 = model.estimate_costs(
            user_count=2000,
            deal_type="carveout",
            facts=facts2,
        )

        assert result1["grand_total"] == result2["grand_total"]
        assert result1["input_hash"] == result2["input_hash"]

    def test_rule_matching_determinism(self):
        """Rule matching should be deterministic."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)

        facts = [
            {"content": "Healthcare company with HIPAA requirements", "fact_id": "F-001"},
            {"content": "Heavy customization of SAP", "fact_id": "F-002"},
        ]

        matches1 = model.match_facts_to_rules(facts)
        matches2 = model.match_facts_to_rules(facts)

        # Same rules should match in same order
        rules1 = [m[0].rule_id for m in matches1]
        rules2 = [m[0].rule_id for m in matches2]

        assert rules1 == rules2

    def test_matched_facts_sorted(self):
        """Matched fact IDs should be sorted."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)

        facts = [
            {"content": "healthcare with HIPAA", "fact_id": "Z-999"},
            {"content": "medical records", "fact_id": "A-001"},
        ]

        matches = model.match_facts_to_rules(facts)

        for rule, fact_ids in matches:
            assert fact_ids == sorted(fact_ids)


# =============================================================================
# CACHE INTEGRATION TESTS
# =============================================================================

class TestCacheIntegration:
    """Tests for cache integration with CostModel."""

    def test_model_uses_cache_by_default(self):
        """CostModel should use cache by default."""
        from tools_v2.cost_model import CostModel
        from tools_v2.cost_cache import clear_cost_cache

        clear_cost_cache()

        model = CostModel(use_cache=True)
        facts = [{"content": "Test fact"}]

        result1 = model.estimate_costs(
            user_count=1000,
            deal_type="carveout",
            facts=facts,
        )

        result2 = model.estimate_costs(
            user_count=1000,
            deal_type="carveout",
            facts=facts,
        )

        # Both should have same values
        assert result1["grand_total"] == result2["grand_total"]

    def test_model_can_disable_cache(self):
        """CostModel should allow disabling cache."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)
        facts = [{"content": "Test fact"}]

        result = model.estimate_costs(
            user_count=1000,
            deal_type="carveout",
            facts=facts,
        )

        # Should still produce valid result
        assert "grand_total" in result
        assert result.get("is_cached") is False

    def test_methodology_version_updated(self):
        """Methodology should indicate deterministic version."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)
        facts = [{"content": "Test"}]

        result = model.estimate_costs(
            user_count=1000,
            deal_type="carveout",
            facts=facts,
        )

        assert "deterministic" in result["methodology"]


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases in determinism."""

    def test_empty_facts(self):
        """Empty facts should produce consistent results."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)

        result1 = model.estimate_costs(
            user_count=1000,
            deal_type="carveout",
            facts=[],
        )

        result2 = model.estimate_costs(
            user_count=1000,
            deal_type="carveout",
            facts=[],
        )

        assert result1["grand_total"] == result2["grand_total"]

    def test_facts_with_missing_content(self):
        """Facts with missing content should be handled."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)
        facts = [
            {"fact_id": "F-001"},  # Missing content
            {"content": "Valid fact", "fact_id": "F-002"},
        ]

        result = model.estimate_costs(
            user_count=1000,
            deal_type="carveout",
            facts=facts,
        )

        assert "grand_total" in result

    def test_whitespace_variations(self):
        """Different whitespace should produce same results."""
        from tools_v2.cost_cache import CostEstimateCache

        cache = CostEstimateCache()

        key1 = cache.get_cache_key(
            user_count=1000,
            deal_type="  carveout  ",  # Extra spaces
            facts=[{"content": "  SAP ERP  "}]
        )
        key2 = cache.get_cache_key(
            user_count=1000,
            deal_type="carveout",
            facts=[{"content": "SAP ERP"}]
        )

        # Keys should be the same after normalization
        assert key1 == key2

    def test_unicode_in_facts(self):
        """Unicode in facts should be handled."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)
        facts = [
            {"content": "Using SAP \u2014 ERP system", "fact_id": "F-001"},  # em-dash
        ]

        result = model.estimate_costs(
            user_count=1000,
            deal_type="carveout",
            facts=facts,
        )

        assert "grand_total" in result


# =============================================================================
# REGRESSION TESTS
# =============================================================================

class TestDeterminismRegression:
    """Regression tests to catch determinism issues."""

    def test_multiple_runs_identical(self):
        """Multiple runs with same inputs should be identical."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)

        facts = [
            {"content": "Legacy ERP system", "fact_id": "F-001"},
            {"content": "Multiple data centers", "fact_id": "F-002"},
            {"content": "Security gaps identified", "fact_id": "F-003"},
        ]

        results = []
        for _ in range(5):
            result = model.estimate_costs(
                user_count=3000,
                deal_type="carveout",
                facts=facts,
                app_count=50,
                dc_count=2,
                site_count=10,
            )
            results.append(result["grand_total"])

        # All results should be identical
        assert len(set(results)) == 1, f"Got different results: {results}"

    def test_input_hash_stable(self):
        """Input hash should be stable across runs."""
        from tools_v2.cost_model import CostModel

        model = CostModel(use_cache=False)
        facts = [{"content": "Test", "fact_id": "F-001"}]

        hashes = []
        for _ in range(5):
            result = model.estimate_costs(
                user_count=1000,
                deal_type="carveout",
                facts=facts,
            )
            hashes.append(result["input_hash"])

        assert len(set(hashes)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
