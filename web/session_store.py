"""
Session Store - Thread-safe session management for Flask app.

Replaces the global session object with proper per-user session isolation.
"""

import threading
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class UserSession:
    """Represents a user's analysis session."""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    analysis_task_id: Optional[str] = None
    analysis_session: Any = None  # The actual Session object

    def touch(self):
        """Update last accessed time."""
        self.last_accessed = datetime.now()


class SessionStore:
    """
    Thread-safe session storage.

    Manages user sessions with:
    - Unique session IDs
    - Auto-expiry of old sessions
    - Thread-safe access
    - Persistence option
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._sessions: Dict[str, UserSession] = {}
        self._sessions_lock = threading.Lock()
        self._session_timeout = timedelta(hours=24)
        self._storage_dir: Optional[Path] = None
        self._initialized = True

    def configure(self, storage_dir: Optional[Path] = None, timeout_hours: int = 24):
        """Configure the session store."""
        if storage_dir:
            self._storage_dir = Path(storage_dir)
            self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._session_timeout = timedelta(hours=timeout_hours)

    def create_session(self) -> str:
        """Create a new user session and return the session ID."""
        session_id = f"sess_{uuid.uuid4().hex[:16]}"

        with self._sessions_lock:
            self._sessions[session_id] = UserSession(session_id=session_id)

        return session_id

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get a session by ID, updating last accessed time."""
        with self._sessions_lock:
            session = self._sessions.get(session_id)
            if session:
                session.touch()
            return session

    def get_or_create_analysis_session(self, session_id: str):
        """Get the analysis Session object, creating if needed."""
        from interactive.session import Session

        user_session = self.get_session(session_id)
        if not user_session:
            return None

        if user_session.analysis_session is None:
            user_session.analysis_session = Session()

        return user_session.analysis_session

    def set_analysis_task(self, session_id: str, task_id: str):
        """Associate an analysis task with a session."""
        with self._sessions_lock:
            session = self._sessions.get(session_id)
            if session:
                session.analysis_task_id = task_id

    def get_analysis_task_id(self, session_id: str) -> Optional[str]:
        """Get the current analysis task ID for a session."""
        with self._sessions_lock:
            session = self._sessions.get(session_id)
            if session:
                return session.analysis_task_id
        return None

    def load_session_from_results(self, session_id: str, facts_file: str, findings_file: Optional[str] = None):
        """Load analysis results into a session."""
        from interactive.session import Session

        user_session = self.get_session(session_id)
        if not user_session:
            return None

        # Load session from result files
        analysis_session = Session.load_from_files(
            facts_file=Path(facts_file),
            findings_file=Path(findings_file) if findings_file else None
        )

        user_session.analysis_session = analysis_session
        return analysis_session

    def delete_session(self, session_id: str):
        """Delete a session."""
        with self._sessions_lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

    def cleanup_expired(self):
        """Remove expired sessions."""
        now = datetime.now()

        with self._sessions_lock:
            expired = [
                sid for sid, session in self._sessions.items()
                if now - session.last_accessed > self._session_timeout
            ]
            for sid in expired:
                del self._sessions[sid]

        return len(expired)

    def get_session_count(self) -> int:
        """Get current session count."""
        with self._sessions_lock:
            return len(self._sessions)

    def get_active_sessions(self) -> list:
        """Get summary of active sessions."""
        with self._sessions_lock:
            return [
                {
                    "session_id": s.session_id,
                    "created_at": s.created_at.isoformat(),
                    "last_accessed": s.last_accessed.isoformat(),
                    "has_analysis": s.analysis_session is not None,
                    "task_id": s.analysis_task_id,
                }
                for s in self._sessions.values()
            ]


# Global instance
session_store = SessionStore()


def get_or_create_session_id(flask_session) -> str:
    """Get existing session ID from Flask session or create new one."""
    session_id = flask_session.get('user_session_id')

    if not session_id or not session_store.get_session(session_id):
        session_id = session_store.create_session()
        flask_session['user_session_id'] = session_id

    return session_id
