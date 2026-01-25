"""
State Management Module

Provides session state management for the Streamlit app,
including typed session state, persistence, and cleanup.
"""

from .session_manager import (
    SessionManager,
    SessionState,
    AnalysisState,
    UploadState,
    ViewState,
    init_session,
    get_session,
    reset_session,
)

__all__ = [
    "SessionManager",
    "SessionState",
    "AnalysisState",
    "UploadState",
    "ViewState",
    "init_session",
    "get_session",
    "reset_session",
]
