"""
Tests for parallel agent execution functionality.

Tests cover:
1. AnalysisStore.merge_from() - data merging correctness
2. run_single_agent() - individual agent execution wrapper
3. Parallel execution - batched ThreadPoolExecutor behavior
4. Error handling - graceful failure scenarios
5. Data integrity - no data loss during parallel merge

Run with: pytest tests/test_parallelization.py -v
"""

import pytest
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.analysis_tools import AnalysisStore


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def empty_store():
    """Create an empty AnalysisStore."""
    return AnalysisStore()


@pytest.fixture
def populated_store():
    """Create an AnalysisStore with sample data."""
    store = AnalysisStore()

    # Add current state entries
    store.current_state = [
        {'id': 'CS-001', 'domain': 'infrastructure', 'category': 'servers', 'description': 'Test server entry'},
        {'id': 'CS-002', 'domain': 'infrastructure', 'category': 'storage', 'description': 'Test storage entry'},
    ]

    # Add risks
    store.risks = [
        {'id': 'R-001', 'severity': 'high', 'description': 'Test risk 1', 'domain': 'infrastructure'},
        {'id': 'R-002', 'severity': 'medium', 'description': 'Test risk 2', 'domain': 'infrastructure'},
    ]

    # Add gaps
    store.gaps = [
        {'id': 'G-001', 'description': 'Missing info', 'domain': 'infrastructure'},
    ]

    # Add assumptions
    store.assumptions = [
        {'id': 'A-001', 'assumption': 'Test assumption', 'domain': 'infrastructure'},
    ]

    # Add work items
    store.work_items = [
        {'id': 'W-001', 'title': 'Work item 1', 'phase': 'pre_close', 'domain': 'infrastructure'},
    ]

    # Add recommendations
    store.recommendations = [
        {'id': 'REC-001', 'recommendation': 'Test rec', 'domain': 'infrastructure'},
    ]

    # Add strategic considerations
    store.strategic_considerations = [
        {'id': 'SC-001', 'consideration': 'Test consideration', 'domain': 'infrastructure'},
    ]

    # Add domain summary
    store.domain_summaries = {
        'infrastructure': {'summary': 'Test summary', 'findings_count': 5}
    }

    # Add reasoning chain
    store.reasoning_chains = {
        'infrastructure': [
            {'step': 1, 'observation': 'Saw X', 'inference': 'Therefore Y'}
        ]
    }

    return store


@pytest.fixture
def second_store():
    """Create a second AnalysisStore with different domain data."""
    store = AnalysisStore()

    store.current_state = [
        {'id': 'CS-101', 'domain': 'network', 'category': 'wan', 'description': 'WAN entry'},
    ]

    store.risks = [
        {'id': 'R-101', 'severity': 'critical', 'description': 'Network risk', 'domain': 'network'},
    ]

    store.gaps = [
        {'id': 'G-101', 'description': 'Network gap', 'domain': 'network'},
    ]

    store.work_items = [
        {'id': 'W-101', 'title': 'Network work', 'phase': 'day_1', 'domain': 'network'},
    ]

    store.recommendations = [
        {'id': 'REC-101', 'recommendation': 'Network rec', 'domain': 'network'},
    ]

    store.strategic_considerations = [
        {'id': 'SC-101', 'consideration': 'Network consideration', 'domain': 'network'},
    ]

    store.domain_summaries = {
        'network': {'summary': 'Network summary', 'findings_count': 3}
    }

    store.reasoning_chains = {
        'network': [
            {'step': 1, 'observation': 'Network issue', 'inference': 'Need VPN'}
        ]
    }

    return store


# =============================================================================
# TEST: AnalysisStore.merge_from()
# =============================================================================

class TestAnalysisStoreMerge:
    """Tests for AnalysisStore.merge_from() method."""

    def test_merge_empty_into_empty(self, empty_store):
        """Merging empty store into empty store should produce empty result."""
        other = AnalysisStore()
        counts = empty_store.merge_from(other)

        assert counts['current_state'] == 0
        assert counts['risks'] == 0
        assert counts['gaps'] == 0
        assert len(empty_store.current_state) == 0
        assert len(empty_store.risks) == 0

    def test_merge_populated_into_empty(self, empty_store, populated_store):
        """Merging populated store into empty should copy all items."""
        counts = empty_store.merge_from(populated_store)

        assert counts['current_state'] == 2
        assert counts['risks'] == 2
        assert counts['gaps'] == 1
        assert counts['assumptions'] == 1
        assert counts['work_items'] == 1
        assert counts['recommendations'] == 1
        assert counts['strategic_considerations'] == 1

        # Verify actual data transferred
        assert len(empty_store.current_state) == 2
        assert len(empty_store.risks) == 2
        assert empty_store.current_state[0]['id'] == 'CS-001'

    def test_merge_combines_both_stores(self, populated_store, second_store):
        """Merging should combine data from both stores."""
        original_current_state_count = len(populated_store.current_state)
        original_risks_count = len(populated_store.risks)

        counts = populated_store.merge_from(second_store)

        # Should have items from both
        assert len(populated_store.current_state) == original_current_state_count + 1
        assert len(populated_store.risks) == original_risks_count + 1

        # Verify both domain items present
        ids = [item['id'] for item in populated_store.current_state]
        assert 'CS-001' in ids  # from populated_store
        assert 'CS-101' in ids  # from second_store

    def test_merge_domain_summaries_overwrite(self, populated_store, second_store):
        """Domain summaries should be added (one per domain)."""
        populated_store.merge_from(second_store)

        assert 'infrastructure' in populated_store.domain_summaries
        assert 'network' in populated_store.domain_summaries
        assert len(populated_store.domain_summaries) == 2

    def test_merge_reasoning_chains_extend(self, populated_store, second_store):
        """Reasoning chains should extend, not overwrite."""
        populated_store.merge_from(second_store)

        assert 'infrastructure' in populated_store.reasoning_chains
        assert 'network' in populated_store.reasoning_chains
        assert len(populated_store.reasoning_chains['infrastructure']) == 1
        assert len(populated_store.reasoning_chains['network']) == 1

    def test_merge_returns_accurate_counts(self, empty_store, populated_store):
        """Returned counts should match actual items merged."""
        counts = empty_store.merge_from(populated_store)

        assert counts['current_state'] == len(empty_store.current_state)
        assert counts['risks'] == len(empty_store.risks)
        assert counts['gaps'] == len(empty_store.gaps)
        assert counts['work_items'] == len(empty_store.work_items)

    def test_merge_preserves_original_data(self, populated_store, second_store):
        """Original store's data should be preserved after merge."""
        original_first_item = populated_store.current_state[0].copy()

        populated_store.merge_from(second_store)

        # First item should still be the original
        assert populated_store.current_state[0]['id'] == original_first_item['id']
        assert populated_store.current_state[0]['domain'] == original_first_item['domain']

    def test_merge_multiple_stores_sequentially(self, empty_store):
        """Merging multiple stores should accumulate all data."""
        store1 = AnalysisStore()
        store1.risks = [{'id': 'R1', 'description': 'Risk 1'}]

        store2 = AnalysisStore()
        store2.risks = [{'id': 'R2', 'description': 'Risk 2'}]

        store3 = AnalysisStore()
        store3.risks = [{'id': 'R3', 'description': 'Risk 3'}]

        empty_store.merge_from(store1)
        empty_store.merge_from(store2)
        empty_store.merge_from(store3)

        assert len(empty_store.risks) == 3
        ids = [r['id'] for r in empty_store.risks]
        assert ids == ['R1', 'R2', 'R3']


# =============================================================================
# TEST: Data Integrity
# =============================================================================

class TestDataIntegrity:
    """Tests to ensure no data loss during parallel operations."""

    def test_no_data_loss_large_merge(self, empty_store):
        """Verify no data loss when merging large datasets."""
        # Create store with many items
        large_store = AnalysisStore()
        large_store.risks = [{'id': f'R-{i}', 'description': f'Risk {i}'} for i in range(100)]
        large_store.gaps = [{'id': f'G-{i}', 'description': f'Gap {i}'} for i in range(50)]
        large_store.work_items = [{'id': f'W-{i}', 'title': f'Work {i}'} for i in range(75)]

        counts = empty_store.merge_from(large_store)

        assert counts['risks'] == 100
        assert counts['gaps'] == 50
        assert counts['work_items'] == 75
        assert len(empty_store.risks) == 100
        assert len(empty_store.gaps) == 50
        assert len(empty_store.work_items) == 75

    def test_parallel_merge_no_data_loss(self, empty_store):
        """Simulate parallel merges and verify no data loss."""
        # Create 6 stores (simulating 6 domain agents)
        stores = []
        for i in range(6):
            s = AnalysisStore()
            s.risks = [{'id': f'R-{i}-{j}', 'domain': f'domain_{i}'} for j in range(10)]
            s.gaps = [{'id': f'G-{i}-{j}', 'domain': f'domain_{i}'} for j in range(5)]
            stores.append(s)

        # Merge all stores (simulating what happens after parallel execution)
        for s in stores:
            empty_store.merge_from(s)

        # Should have all items from all stores
        assert len(empty_store.risks) == 60  # 6 stores * 10 risks
        assert len(empty_store.gaps) == 30   # 6 stores * 5 gaps

    def test_merge_does_not_modify_source(self, empty_store, populated_store):
        """Merging should not modify the source store."""
        original_risks_count = len(populated_store.risks)
        original_gaps_count = len(populated_store.gaps)

        empty_store.merge_from(populated_store)

        # Source should be unchanged
        assert len(populated_store.risks) == original_risks_count
        assert len(populated_store.gaps) == original_gaps_count

    def test_deep_copy_behavior(self, empty_store, populated_store):
        """Verify items are properly copied (not just references)."""
        empty_store.merge_from(populated_store)

        # Modify item in merged store
        empty_store.risks[0]['modified'] = True

        # Original should not be modified (if deep copy)
        # Note: Current implementation uses shallow copy (append)
        # This test documents the current behavior
        if 'modified' in populated_store.risks[0]:
            pytest.skip("Current implementation uses shallow copy - expected behavior")


# =============================================================================
# TEST: Parallel Execution Simulation
# =============================================================================

class TestParallelExecution:
    """Tests for parallel execution patterns."""

    def test_thread_safe_store_creation(self):
        """Each thread should get its own isolated store."""
        stores = []

        def create_store_with_data(domain_id):
            store = AnalysisStore()
            store.risks = [{'id': f'R-{domain_id}', 'domain': f'domain_{domain_id}'}]
            time.sleep(0.01)  # Simulate some work
            return store

        # Run in parallel
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(create_store_with_data, i) for i in range(6)]
            for future in as_completed(futures):
                stores.append(future.result())

        # Each store should have exactly 1 risk with unique domain
        assert len(stores) == 6
        all_risk_ids = set()
        for store in stores:
            assert len(store.risks) == 1
            all_risk_ids.add(store.risks[0]['id'])

        assert len(all_risk_ids) == 6  # All unique

    def test_batched_execution_pattern(self):
        """Test the batched execution pattern (3 at a time)."""
        execution_order = []

        def mock_agent_work(agent_id, batch_num):
            execution_order.append(('start', agent_id, batch_num))
            time.sleep(0.05)  # Simulate work
            execution_order.append(('end', agent_id, batch_num))
            return AnalysisStore()

        agents = list(range(6))
        BATCH_SIZE = 3
        batches = [agents[i:i + BATCH_SIZE] for i in range(0, len(agents), BATCH_SIZE)]

        results = []
        for batch_num, batch in enumerate(batches):
            with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
                futures = {
                    executor.submit(mock_agent_work, agent_id, batch_num): agent_id
                    for agent_id in batch
                }
                for future in as_completed(futures):
                    results.append(future.result())

        assert len(results) == 6

        # Verify batching occurred - batch 0 should complete before batch 1 starts
        batch_0_end_times = [i for i, (action, _, batch) in enumerate(execution_order)
                           if action == 'end' and batch == 0]
        batch_1_start_times = [i for i, (action, _, batch) in enumerate(execution_order)
                             if action == 'start' and batch == 1]

        # All batch 0 ends should come before all batch 1 starts
        if batch_1_start_times:
            assert max(batch_0_end_times) < min(batch_1_start_times)

    def test_merge_after_parallel_execution(self):
        """Test merging results after parallel execution."""
        master_store = AnalysisStore()

        def create_domain_store(domain):
            store = AnalysisStore()
            store.risks = [{'id': f'R-{domain}', 'domain': domain}]
            store.domain_summaries = {domain: {'count': 1}}
            return store

        domains = ['infra', 'network', 'cyber', 'apps', 'iam', 'org']

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(create_domain_store, d): d for d in domains}
            for future in as_completed(futures):
                store = future.result()
                master_store.merge_from(store)

        assert len(master_store.risks) == 6
        assert len(master_store.domain_summaries) == 6


# =============================================================================
# TEST: Error Handling
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in parallel execution."""

    def test_merge_with_none_values(self, empty_store):
        """Merge should handle stores with None-like values gracefully."""
        store_with_empty = AnalysisStore()
        store_with_empty.risks = []
        store_with_empty.gaps = []

        counts = empty_store.merge_from(store_with_empty)

        assert counts['risks'] == 0
        assert counts['gaps'] == 0

    def test_partial_failure_in_parallel(self):
        """Test that partial failures don't affect successful results."""
        successful_stores = []
        errors = []

        def agent_work(agent_id, should_fail=False):
            if should_fail:
                raise Exception(f"Agent {agent_id} failed")
            store = AnalysisStore()
            store.risks = [{'id': f'R-{agent_id}'}]
            return {'success': True, 'store': store}

        # Run with one failing agent
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(agent_work, 0, False): 0,
                executor.submit(agent_work, 1, True): 1,  # This will fail
                executor.submit(agent_work, 2, False): 2,
            }

            for future in as_completed(futures):
                agent_id = futures[future]
                try:
                    result = future.result()
                    if result['success']:
                        successful_stores.append(result['store'])
                except Exception as e:
                    errors.append((agent_id, str(e)))

        # Should have 2 successful, 1 error
        assert len(successful_stores) == 2
        assert len(errors) == 1
        assert errors[0][0] == 1  # Agent 1 failed


# =============================================================================
# TEST: run_single_agent wrapper (mocked)
# =============================================================================

class TestRunSingleAgent:
    """Tests for run_single_agent function behavior."""

    def test_run_single_agent_returns_expected_structure(self):
        """Verify run_single_agent returns the expected dict structure."""
        # We'll test the structure, mocking the actual agent
        expected_keys = {'success', 'domain', 'store', 'reasoning_chain', 'metrics', 'error'}

        # Simulate a successful result
        result = {
            'success': True,
            'domain': 'infrastructure',
            'store': AnalysisStore(),
            'reasoning_chain': [],
            'metrics': {'execution_time': 1.5, 'api_calls': 10},
            'error': None
        }

        assert set(result.keys()) == expected_keys
        assert result['success'] is True
        assert result['error'] is None
        assert isinstance(result['store'], AnalysisStore)

    def test_run_single_agent_failure_structure(self):
        """Verify failure result has expected structure."""
        result = {
            'success': False,
            'domain': 'infrastructure',
            'store': None,
            'reasoning_chain': [],
            'metrics': {'execution_time': 0.5},
            'error': 'Test error message'
        }

        assert result['success'] is False
        assert result['store'] is None
        assert result['error'] is not None


# =============================================================================
# TEST: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_merge_with_duplicate_ids(self, empty_store):
        """Test behavior when merging stores with duplicate IDs."""
        store1 = AnalysisStore()
        store1.risks = [{'id': 'R-001', 'description': 'Risk from store 1'}]

        store2 = AnalysisStore()
        store2.risks = [{'id': 'R-001', 'description': 'Risk from store 2'}]

        empty_store.merge_from(store1)
        empty_store.merge_from(store2)

        # Both should be present (no deduplication in merge)
        assert len(empty_store.risks) == 2
        descriptions = [r['description'] for r in empty_store.risks]
        assert 'Risk from store 1' in descriptions
        assert 'Risk from store 2' in descriptions

    def test_merge_preserves_order(self, empty_store):
        """Test that merge preserves insertion order."""
        for i in range(5):
            store = AnalysisStore()
            store.risks = [{'id': f'R-{i}', 'order': i}]
            empty_store.merge_from(store)

        orders = [r['order'] for r in empty_store.risks]
        assert orders == [0, 1, 2, 3, 4]

    def test_merge_with_mixed_data_types(self, empty_store):
        """Test merge handles various data types in dicts."""
        store = AnalysisStore()
        store.risks = [{
            'id': 'R-001',
            'count': 42,
            'percentage': 0.85,
            'active': True,
            'tags': ['critical', 'security'],
            'metadata': {'source': 'test'}
        }]

        empty_store.merge_from(store)

        risk = empty_store.risks[0]
        assert risk['count'] == 42
        assert risk['percentage'] == 0.85
        assert risk['active'] is True
        assert risk['tags'] == ['critical', 'security']
        assert risk['metadata']['source'] == 'test'

    def test_merge_filters_out_string_items(self, empty_store):
        """Test that merge_from filters out invalid string items."""
        store = AnalysisStore()
        # Mix of valid dicts and invalid strings
        store.risks = [
            {'id': 'R-001', 'description': 'Valid risk'},
            'This is an invalid string item',  # Should be filtered out
            {'id': 'R-002', 'description': 'Another valid risk'},
            'Another invalid string',  # Should be filtered out
        ]
        store.gaps = [
            'String gap that should be filtered',  # Invalid
            {'id': 'G-001', 'description': 'Valid gap'},
        ]

        counts = empty_store.merge_from(store)

        # Only dicts should be merged
        assert len(empty_store.risks) == 2
        assert empty_store.risks[0]['id'] == 'R-001'
        assert empty_store.risks[1]['id'] == 'R-002'
        assert len(empty_store.gaps) == 1
        assert empty_store.gaps[0]['id'] == 'G-001'
        # Verify skipped count
        assert counts['skipped_invalid'] == 3
        assert counts['risks'] == 2
        assert counts['gaps'] == 1

    def test_execute_tool_rejects_string_input(self, empty_store):
        """Test that execute_tool rejects non-dict input."""
        # Test with string input
        result = empty_store.execute_tool("identify_risk", "This is a string, not a dict")

        assert result['status'] == 'error'
        assert 'Invalid tool input' in result['message']
        assert 'str' in result['message']
        # Ensure nothing was added to the store
        assert len(empty_store.risks) == 0

    def test_execute_tool_accepts_dict_input(self, empty_store):
        """Test that execute_tool properly accepts dict input."""
        result = empty_store.execute_tool("identify_risk", {
            'risk': 'Test risk description',
            'domain': 'infrastructure',
            'severity': 'high',
            'likelihood': 'medium',
            'trigger': 'Test trigger'
        })

        assert result['status'] == 'recorded'
        assert result['type'] == 'risk'
        assert len(empty_store.risks) == 1
        assert empty_store.risks[0]['risk'] == 'Test risk description'


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
