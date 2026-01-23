"""
Point 102: Unit tests for AnalysisTaskManager

Tests task lifecycle states and concurrent task handling.
"""

import pytest
import time
import threading
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from web.task_manager import (
    AnalysisTaskManager, AnalysisTask, AnalysisPhase, TaskStatus
)


class TestAnalysisTask:
    """Tests for AnalysisTask dataclass."""

    def test_task_creation(self):
        """Test task creation with required fields."""
        task = AnalysisTask(
            session_id="test-123",
            file_paths=["/tmp/test.pdf"]
        )
        assert task.session_id == "test-123"
        assert task.status == TaskStatus.PENDING
        assert task.phase == AnalysisPhase.INITIALIZING

    def test_task_progress_update(self):
        """Test updating task progress."""
        task = AnalysisTask(
            session_id="test-123",
            file_paths=["/tmp/test.pdf"]
        )
        task.update_progress({
            "phase": AnalysisPhase.PARSING_DOCUMENTS,
            "documents_processed": 5,
            "total_documents": 10
        })
        assert task.phase == AnalysisPhase.PARSING_DOCUMENTS
        assert task.progress["documents_processed"] == 5

    def test_task_cancellation(self):
        """Test task cancellation."""
        task = AnalysisTask(
            session_id="test-123",
            file_paths=["/tmp/test.pdf"]
        )
        task.cancel()
        assert task._cancelled is True


class TestAnalysisTaskManager:
    """Tests for AnalysisTaskManager singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        AnalysisTaskManager._instance = None

    def test_singleton_pattern(self):
        """Test that manager follows singleton pattern."""
        manager1 = AnalysisTaskManager.get_instance()
        manager2 = AnalysisTaskManager.get_instance()
        assert manager1 is manager2

    def test_task_submission(self):
        """Test submitting a new task."""
        manager = AnalysisTaskManager.get_instance()
        task = AnalysisTask(
            session_id="test-submit",
            file_paths=["/tmp/test.pdf"]
        )
        result = manager.submit_task(task)
        assert result == "test-submit"

    def test_multiple_tasks(self):
        """Test managing multiple concurrent tasks."""
        manager = AnalysisTaskManager.get_instance()
        
        for i in range(5):
            task = AnalysisTask(
                session_id=f"test-multi-{i}",
                file_paths=["/tmp/test.pdf"]
            )
            manager.submit_task(task)
        
        for i in range(5):
            assert manager.get_task(f"test-multi-{i}") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
