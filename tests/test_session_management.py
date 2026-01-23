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

from web.session_store import SessionStore


class TestSessionStore:
    """Tests for SessionStore singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        SessionStore._instance = None

    def test_singleton_pattern(self):
        """Test that SessionStore follows singleton pattern."""
        store1 = SessionStore.get_instance()
        store2 = SessionStore.get_instance()
        assert store1 is store2

    def test_session_creation(self):
        """Test creating a new session."""
        store = SessionStore.get_instance()
        session_id = store.create_session()
        assert session_id is not None
        assert len(session_id) > 0

    def test_session_data_storage(self):
        """Test storing and retrieving session data."""
        store = SessionStore.get_instance()
        session_id = store.create_session()
        
        store.set_session_data(session_id, "test_key", "test_value")
        value = store.get_session_data(session_id, "test_key")
        assert value == "test_value"

    def test_session_isolation(self):
        """Test that sessions are isolated from each other."""
        store = SessionStore.get_instance()
        session1 = store.create_session()
        session2 = store.create_session()
        
        store.set_session_data(session1, "key", "value1")
        store.set_session_data(session2, "key", "value2")
        
        assert store.get_session_data(session1, "key") == "value1"
        assert store.get_session_data(session2, "key") == "value2"

    def test_session_cleanup(self):
        """Test cleaning up old sessions."""
        store = SessionStore.get_instance()
        session_id = store.create_session()
        
        # Manually set old timestamp
        if session_id in store._sessions:
            store._sessions[session_id]["created_at"] = time.time() - 100000
        
        store.cleanup_old_sessions(max_age_seconds=1000)
        
        # Session should be cleaned up
        assert store.get_session(session_id) is None

    def test_thread_safety(self):
        """Test thread safety of session operations."""
        store = SessionStore.get_instance()
        session_id = store.create_session()
        errors = []
        
        def writer(n):
            try:
                for i in range(100):
                    store.set_session_data(session_id, f"key_{n}_{i}", f"value_{n}_{i}")
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
