"""
Integration tests for run_single_agent function.

These tests verify the actual function in main.py works correctly
by mocking the agent class and API calls.

Run with: pytest tests/test_run_single_agent.py -v
"""

import pytest
import sys
from pathlib import Path
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.analysis_tools import AnalysisStore

# Import the function under test
from main import run_single_agent


@dataclass
class MockAgentMetrics:
    """Mock for AgentMetrics dataclass."""
    api_calls: int = 10
    tool_calls: int = 10
    tokens_used: int = 50000
    execution_time: float = 5.0
    iterations: int = 10
    errors: int = 0
    retries: int = 0
    duplicates_detected: int = 0


class MockAgent:
    """Mock agent class for testing."""

    def __init__(self, store):
        self.store = store
        self.domain = 'mock_domain'
        self.metrics = MockAgentMetrics()
        self._reasoning_chain = []

    def analyze(self, document_text, deal_context):
        """Mock analyze that adds data to store."""
        self.store.risks.append({
            'id': 'R-MOCK-001',
            'description': 'Mock risk',
            'domain': self.domain
        })
        self._reasoning_chain.append({
            'step': 1,
            'observation': 'Mock observation'
        })

    def get_reasoning_chain(self):
        return self._reasoning_chain


class FailingAgent:
    """Agent that always fails for error testing."""

    def __init__(self, store):
        self.store = store
        self.domain = 'failing_domain'

    def analyze(self, document_text, deal_context):
        raise Exception("Simulated agent failure")

    def get_reasoning_chain(self):
        return []


class TestRunSingleAgentFunction:
    """Tests for the run_single_agent function in main.py."""

    def test_successful_execution(self):
        """Test successful agent execution returns expected structure."""
        result = run_single_agent(
            MockAgent,
            'MockAgent',
            'Test document content',
            {'deal_name': 'Test Deal'}
        )

        assert result['success'] is True
        assert result['domain'] == 'mock_domain'
        assert result['error'] is None
        assert isinstance(result['store'], AnalysisStore)
        assert len(result['store'].risks) == 1
        assert result['store'].risks[0]['id'] == 'R-MOCK-001'

    def test_returns_reasoning_chain(self):
        """Test that reasoning chain is properly returned."""
        result = run_single_agent(
            MockAgent,
            'MockAgent',
            'Test document',
            {}
        )

        assert 'reasoning_chain' in result
        assert len(result['reasoning_chain']) == 1
        assert result['reasoning_chain'][0]['observation'] == 'Mock observation'

    def test_returns_metrics(self):
        """Test that metrics are properly extracted."""
        result = run_single_agent(
            MockAgent,
            'MockAgent',
            'Test document',
            {}
        )

        assert 'metrics' in result
        assert 'execution_time' in result['metrics']
        assert result['metrics']['execution_time'] > 0
        assert result['metrics']['api_calls'] == 10

    def test_handles_agent_failure(self):
        """Test graceful handling of agent exceptions."""
        result = run_single_agent(
            FailingAgent,
            'FailingAgent',
            'Test document',
            {}
        )

        assert result['success'] is False
        assert result['store'] is None
        assert result['error'] is not None
        assert 'Simulated agent failure' in result['error']
        assert result['reasoning_chain'] == []

    def test_isolated_stores(self):
        """Test that each call gets its own isolated store."""
        result1 = run_single_agent(MockAgent, 'Agent1', 'Doc1', {})
        result2 = run_single_agent(MockAgent, 'Agent2', 'Doc2', {})

        # Each should have exactly 1 risk (not accumulated)
        assert len(result1['store'].risks) == 1
        assert len(result2['store'].risks) == 1

        # Stores should be different objects
        assert result1['store'] is not result2['store']

    def test_domain_name_on_failure(self):
        """Test that domain name is captured even on failure."""
        result = run_single_agent(
            FailingAgent,
            'TestFailingAgent',
            'Test document',
            {}
        )

        # Should use the lowercase agent name as fallback domain
        assert result['domain'] == 'testfailingagent'


class TestRunSingleAgentEdgeCases:
    """Edge case tests for run_single_agent."""

    def test_empty_document(self):
        """Test handling of empty document."""
        result = run_single_agent(
            MockAgent,
            'MockAgent',
            '',  # Empty document
            {}
        )

        # Should still succeed (agent decides what to do with empty doc)
        assert result['success'] is True

    def test_empty_deal_context(self):
        """Test handling of empty deal context."""
        result = run_single_agent(
            MockAgent,
            'MockAgent',
            'Test document',
            {}  # Empty context
        )

        assert result['success'] is True

    def test_none_deal_context(self):
        """Test handling of None deal context."""
        # This might fail depending on agent implementation
        # Testing the boundary condition
        class NoneContextAgent(MockAgent):
            def analyze(self, document_text, deal_context):
                if deal_context is None:
                    raise ValueError("deal_context cannot be None")
                super().analyze(document_text, deal_context)

        result = run_single_agent(
            NoneContextAgent,
            'NoneContextAgent',
            'Test document',
            None
        )

        # Should fail gracefully
        assert result['success'] is False
        assert 'None' in result['error']


class TestMetricsExtraction:
    """Tests specifically for metrics extraction logic."""

    def test_metrics_from_dataclass(self):
        """Test extraction of metrics from AgentMetrics dataclass."""
        result = run_single_agent(
            MockAgent,
            'MockAgent',
            'Test document',
            {}
        )

        # Should properly extract api_calls from dataclass
        assert result['metrics']['api_calls'] == 10

    def test_metrics_without_agent_metrics(self):
        """Test handling when agent has no metrics attribute."""
        class NoMetricsAgent(MockAgent):
            def __init__(self, store):
                super().__init__(store)
                del self.metrics  # Remove metrics

        result = run_single_agent(
            NoMetricsAgent,
            'NoMetricsAgent',
            'Test document',
            {}
        )

        # Should still succeed with default api_calls of 0
        assert result['success'] is True
        assert result['metrics']['api_calls'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
