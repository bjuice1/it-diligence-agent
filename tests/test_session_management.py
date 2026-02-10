"""
Point 103: Unit tests for session management

Tests session isolation and cleanup.
"""

import pytest
import time
import threading
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from stores.session_store import SessionStore


class TestSessionStore:
    """Tests for SessionStore singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        SessionStore._instance = None
        SessionStore._initialized = False

    def test_singleton_pattern(self):
        """Test that SessionStore follows singleton pattern."""
        store1 = SessionStore()
        store2 = SessionStore()
        assert store1 is store2

    def test_session_creation(self):
        """Test creating a new session."""
        store = SessionStore()
        session_id = store.create_session()
        assert session_id is not None
        assert len(session_id) > 0

    def test_session_data_storage(self):
        """Test storing and retrieving session data."""
        store = SessionStore()
        session_id = store.create_session()

        # SessionStore uses set_analysis_task / get_session for data
        store.set_analysis_task(session_id, "test-task-123")
        task_id = store.get_analysis_task_id(session_id)
        assert task_id == "test-task-123"

    def test_session_isolation(self):
        """Test that sessions are isolated from each other."""
        store = SessionStore()
        session1 = store.create_session()
        session2 = store.create_session()

        store.set_analysis_task(session1, "task-1")
        store.set_analysis_task(session2, "task-2")

        assert store.get_analysis_task_id(session1) == "task-1"
        assert store.get_analysis_task_id(session2) == "task-2"

    def test_session_cleanup(self):
        """Test cleaning up old sessions."""
        store = SessionStore()
        session_id = store.create_session()

        # Manually set old timestamp using datetime
        from datetime import datetime, timedelta
        session = store.get_session(session_id)
        if session:
            session.last_accessed = datetime.now() - timedelta(hours=48)

        # Configure short timeout and cleanup
        store.configure(timeout_hours=1)
        removed = store.cleanup_expired()

        # Session should be cleaned up
        assert store.get_session(session_id) is None

    def test_thread_safety(self):
        """Test thread safety of session operations."""
        store = SessionStore()
        errors = []
        session_ids = []

        def writer(n):
            try:
                sid = store.create_session()
                session_ids.append(sid)
                store.set_analysis_task(sid, f"task-{n}")
                # Verify
                result = store.get_analysis_task_id(sid)
                assert result == f"task-{n}"
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
