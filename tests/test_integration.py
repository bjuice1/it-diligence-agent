"""
Points 106-110: Integration Tests

- Point 106: End-to-end upload-to-dashboard test
- Point 107: Organization module integration test
- Point 108: Multi-user concurrency test
- Point 109: API failure simulation tests
- Point 110: Large file handling test
"""

import pytest
import time
import threading
import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# Point 106: End-to-End Upload to Dashboard Test
# =============================================================================

class TestEndToEndFlow:
    """Tests for complete upload-to-dashboard flow."""

    @pytest.fixture
    def test_documents_dir(self):
        """Get path to Great Insurance test documents."""
        return Path(__file__).parent.parent / "data" / "input" / "Tests"

    def test_upload_flow_mock(self, test_documents_dir):
        """Test upload flow with test documents (mocked)."""
        from web.task_manager import AnalysisTask, AnalysisPhase, TaskStatus
        from web.session_store import SessionStore
        
        # Create session
        store = SessionStore.get_instance()
        session_id = store.create_session()
        
        # Simulate file upload
        test_files = list(test_documents_dir.glob("*.md"))[:3]
        if not test_files:
            pytest.skip("No test documents found")
        
        # Create analysis task
        task = AnalysisTask(
            session_id=session_id,
            file_paths=[str(f) for f in test_files]
        )
        
        assert task.status == TaskStatus.PENDING
        assert len(task.file_paths) > 0

    def test_session_persistence(self):
        """Test that session data persists across operations."""
        from web.session_store import SessionStore
        
        store = SessionStore.get_instance()
        session_id = store.create_session()
        
        # Store analysis results
        store.set_session_data(session_id, "facts_count", 42)
        store.set_session_data(session_id, "risks_count", 10)
        
        # Verify persistence
        assert store.get_session_data(session_id, "facts_count") == 42
        assert store.get_session_data(session_id, "risks_count") == 10


# =============================================================================
# Point 107: Organization Module Integration Test
# =============================================================================

class TestOrganizationModuleIntegration:
    """Tests for organization module integration with pipeline."""

    def test_census_to_benchmark_flow(self):
        """Test flow from census data to benchmark comparison."""
        from parsers.census_parser import CensusParser
        from services.benchmark_service import BenchmarkService
        
        # Sample census data
        csv_data = '''name,role,salary,start_date
John Smith,IT Manager,120000,2020-01-15
Jane Doe,Developer,95000,2021-03-20
Bob Wilson,Analyst,75000,2022-06-01'''
        
        # Parse census
        parser = CensusParser()
        census_result = parser.parse(csv_data)
        
        # Get benchmark comparison
        benchmark = BenchmarkService()
        profile = benchmark.get_profile("technology")
        
        assert census_result is not None
        assert profile is not None

    def test_staffing_comparison_integration(self):
        """Test staffing comparison service integration."""
        from services.staffing_comparison_service import StaffingComparisonService
        
        service = StaffingComparisonService()
        
        # Test with sample data
        target_staff = [
            {"role": "IT Manager", "count": 2},
            {"role": "Developer", "count": 10},
        ]
        
        comparison = service.compare_staffing(
            target_staff,
            industry="technology",
            company_size=500
        )
        
        assert comparison is not None


# =============================================================================
# Point 108: Multi-User Concurrency Test
# =============================================================================

class TestMultiUserConcurrency:
    """Tests for parallel analyses not interfering with each other."""

    def test_concurrent_sessions(self):
        """Test that concurrent sessions don't interfere."""
        from web.session_store import SessionStore
        
        store = SessionStore.get_instance()
        errors = []
        session_ids = []
        
        def create_and_use_session(user_num):
            try:
                session_id = store.create_session()
                session_ids.append(session_id)
                
                # Store user-specific data
                for i in range(10):
                    store.set_session_data(session_id, f"data_{i}", f"user_{user_num}_{i}")
                
                # Verify data integrity
                for i in range(10):
                    value = store.get_session_data(session_id, f"data_{i}")
                    expected = f"user_{user_num}_{i}"
                    if value != expected:
                        errors.append(f"Data mismatch for user {user_num}: {value} != {expected}")
            except Exception as e:
                errors.append(str(e))
        
        # Run concurrent users
        threads = [threading.Thread(target=create_and_use_session, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(session_ids) == 10

    def test_concurrent_task_submission(self):
        """Test concurrent task submission."""
        from web.task_manager import AnalysisTaskManager, AnalysisTask
        
        AnalysisTaskManager._instance = None
        manager = AnalysisTaskManager.get_instance()
        errors = []
        
        def submit_task(task_num):
            try:
                task = AnalysisTask(
                    session_id=f"concurrent-{task_num}",
                    file_paths=[f"/tmp/test_{task_num}.pdf"]
                )
                manager.submit_task(task)
            except Exception as e:
                errors.append(str(e))
        
        threads = [threading.Thread(target=submit_task, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


# =============================================================================
# Point 109: API Failure Simulation Tests
# =============================================================================

class TestAPIFailureSimulation:
    """Tests for behavior when Anthropic API fails."""

    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after repeated failures."""
        from tools_v2.rate_limiter import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=3)
        
        # Record failures
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == CircuitState.OPEN

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        from tools_v2.rate_limiter import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        # Trigger open state
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery
        time.sleep(0.2)
        assert cb.state == CircuitState.HALF_OPEN

    def test_api_error_classification(self):
        """Test API error classification."""
        from tools_v2.rate_limiter import APIError, APIErrorType
        
        # Rate limit error
        rate_limit_err = APIError.classify_error(Exception("rate limit exceeded"), 429)
        assert rate_limit_err.is_retriable is True
        assert rate_limit_err.error_type == APIErrorType.RETRIABLE
        
        # Auth error
        auth_err = APIError.classify_error(Exception("unauthorized"), 401)
        assert auth_err.is_retriable is False
        assert auth_err.error_type == APIErrorType.FATAL

    def test_graceful_degradation(self):
        """Test graceful degradation with cached results."""
        from tools_v2.rate_limiter import APIRateLimiter
        
        APIRateLimiter._instance = None
        limiter = APIRateLimiter.get_instance()
        
        # Cache a result
        limiter.cache_result("test_key", {"result": "cached_value"})
        
        # Enter degraded mode
        limiter.enter_degraded_mode()
        assert limiter.is_degraded() is True
        
        # Should return cached result
        cached = limiter.get_cached_result("test_key")
        assert cached is not None
        assert cached["result"] == "cached_value"


# =============================================================================
# Point 110: Large File Handling Test
# =============================================================================

class TestLargeFileHandling:
    """Tests with realistic large document sets."""

    def test_large_document_count(self):
        """Test handling many documents."""
        from web.task_manager import AnalysisTask
        
        # Create task with many file paths
        file_paths = [f"/tmp/doc_{i}.pdf" for i in range(200)]
        
        task = AnalysisTask(
            session_id="large-doc-test",
            file_paths=file_paths
        )
        
        assert len(task.file_paths) == 200

    def test_large_fact_store(self):
        """Test FactStore with many entries."""
        from tools_v2.fact_store import FactStore
        
        store = FactStore()
        
        # Add many facts
        for i in range(1000):
            store.add_fact(
                domain="infrastructure",
                category="test",
                content=f"Test fact {i}",
                evidence=f"Evidence {i}",
                confidence="high",
                source=f"doc_{i}.pdf"
            )
        
        assert len(store.facts) == 1000
        
        # Test querying performance
        start = time.time()
        results = store.query_by_domain("infrastructure")
        elapsed = time.time() - start
        
        assert len(results) == 1000
        assert elapsed < 1.0  # Should be fast

    def test_reasoning_store_capacity(self):
        """Test ReasoningStore with many entries."""
        from tools_v2.reasoning_tools import ReasoningStore
        
        store = ReasoningStore()
        
        # Add many risks
        for i in range(500):
            store.add_risk(
                domain="infrastructure",
                title=f"Risk {i}",
                description=f"Description {i}",
                category="technical_debt",
                severity="medium",
                integration_dependent=False,
                mitigation=f"Mitigation {i}",
                based_on_facts=[f"F-{i}"],
                confidence="medium",
                reasoning=f"Reasoning for risk {i}"
            )
        
        assert len(store.risks) == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
