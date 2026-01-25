"""
Session Manager - Typed Session State for Streamlit

Provides a structured approach to session state management,
porting patterns from the Flask SessionStore to Streamlit.

Steps 1-10 of the alignment plan.
"""

import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import hashlib


# =============================================================================
# ENUMS
# =============================================================================

class AnalysisPhase(Enum):
    """Current phase of analysis."""
    IDLE = "idle"
    DISCOVERY = "discovery"
    REASONING = "reasoning"
    SYNTHESIS = "synthesis"
    COMPLETE = "complete"
    ERROR = "error"


class ViewMode(Enum):
    """Current view/page mode."""
    SETUP = "setup"
    PROCESSING = "processing"
    RESULTS = "results"
    DASHBOARD = "dashboard"
    RISKS = "risks"
    WORK_ITEMS = "work_items"
    FACTS = "facts"
    GAPS = "gaps"
    ORGANIZATION = "organization"
    APPLICATIONS = "applications"
    INFRASTRUCTURE = "infrastructure"
    COVERAGE = "coverage"
    COSTS = "costs"
    OPEN_QUESTIONS = "open_questions"


# =============================================================================
# STATE DATACLASSES
# =============================================================================

@dataclass
class UploadState:
    """State for document uploads."""
    target_files: List[str] = field(default_factory=list)
    buyer_files: List[str] = field(default_factory=list)
    notes_content: str = ""
    file_hashes: Dict[str, str] = field(default_factory=dict)
    total_size_bytes: int = 0
    upload_timestamp: Optional[str] = None

    def add_file(self, filename: str, content_hash: str, size: int, entity: str = "target"):
        """Add a file to the upload state."""
        if entity == "target":
            if filename not in self.target_files:
                self.target_files.append(filename)
        else:
            if filename not in self.buyer_files:
                self.buyer_files.append(filename)
        self.file_hashes[filename] = content_hash
        self.total_size_bytes += size
        self.upload_timestamp = datetime.now().isoformat()

    def has_duplicate(self, content_hash: str) -> bool:
        """Check if a file with this hash already exists."""
        return content_hash in self.file_hashes.values()

    def clear(self):
        """Clear all upload state."""
        self.target_files = []
        self.buyer_files = []
        self.notes_content = ""
        self.file_hashes = {}
        self.total_size_bytes = 0
        self.upload_timestamp = None


@dataclass
class AnalysisState:
    """State for analysis execution and results."""
    # Configuration
    target_name: str = "Target Company"
    buyer_name: Optional[str] = None
    deal_type: str = "bolt_on"
    selected_domains: List[str] = field(default_factory=lambda: [
        "infrastructure", "network", "cybersecurity",
        "applications", "identity_access", "organization"
    ])

    # Execution state
    phase: AnalysisPhase = AnalysisPhase.IDLE
    progress_percent: float = 0.0
    status_message: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Results (serialized references)
    fact_store_path: Optional[str] = None
    reasoning_store_path: Optional[str] = None
    vdr_path: Optional[str] = None
    html_report_path: Optional[str] = None
    presentation_path: Optional[str] = None

    # Counts for display
    fact_count: int = 0
    gap_count: int = 0
    risk_count: int = 0
    work_item_count: int = 0
    recommendation_count: int = 0
    strategic_count: int = 0
    facts_by_domain: Dict[str, int] = field(default_factory=dict)

    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Saved deal reference
    deal_id: Optional[str] = None

    def start(self):
        """Mark analysis as started."""
        self.phase = AnalysisPhase.DISCOVERY
        self.progress_percent = 0.0
        self.started_at = datetime.now().isoformat()
        self.errors = []
        self.warnings = []

    def update_progress(self, percent: float, message: str, phase: Optional[AnalysisPhase] = None):
        """Update progress state."""
        self.progress_percent = percent
        self.status_message = message
        if phase:
            self.phase = phase

    def complete(self):
        """Mark analysis as complete."""
        self.phase = AnalysisPhase.COMPLETE
        self.progress_percent = 1.0
        self.completed_at = datetime.now().isoformat()

    def fail(self, error: str):
        """Mark analysis as failed."""
        self.phase = AnalysisPhase.ERROR
        self.errors.append(error)

    def is_complete(self) -> bool:
        """Check if analysis is complete."""
        return self.phase == AnalysisPhase.COMPLETE

    def is_running(self) -> bool:
        """Check if analysis is running."""
        return self.phase in [
            AnalysisPhase.DISCOVERY,
            AnalysisPhase.REASONING,
            AnalysisPhase.SYNTHESIS
        ]


@dataclass
class ViewState:
    """State for UI view/navigation."""
    current_view: ViewMode = ViewMode.SETUP
    previous_view: Optional[ViewMode] = None

    # Filter states (persisted across view changes)
    risk_filters: Dict[str, Any] = field(default_factory=dict)
    work_item_filters: Dict[str, Any] = field(default_factory=dict)
    fact_filters: Dict[str, Any] = field(default_factory=dict)

    # Pagination states
    risk_page: int = 0
    work_item_page: int = 0
    fact_page: int = 0
    items_per_page: int = 20

    # Search states
    risk_search: str = ""
    work_item_search: str = ""
    fact_search: str = ""

    # Expanded items (for detail views)
    expanded_risks: List[str] = field(default_factory=list)
    expanded_work_items: List[str] = field(default_factory=list)
    expanded_facts: List[str] = field(default_factory=list)

    def navigate_to(self, view: ViewMode):
        """Navigate to a new view."""
        self.previous_view = self.current_view
        self.current_view = view

    def go_back(self):
        """Go back to previous view."""
        if self.previous_view:
            self.current_view = self.previous_view
            self.previous_view = None


@dataclass
class SessionState:
    """Complete session state container."""
    # Version for schema migrations
    schema_version: int = 1

    # Session metadata
    session_id: str = ""
    created_at: str = ""
    last_activity: str = ""

    # Component states
    uploads: UploadState = field(default_factory=UploadState)
    analysis: AnalysisState = field(default_factory=AnalysisState)
    view: ViewState = field(default_factory=ViewState)

    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "background_processing": False,  # Not yet implemented
        "organization_module": True,
        "open_questions": True,
        "cost_analysis": True,
        "narrative_view": True,
    })

    # Debug mode
    debug: bool = False

    def touch(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence."""
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "uploads": {
                "target_files": self.uploads.target_files,
                "buyer_files": self.uploads.buyer_files,
                "notes_content": self.uploads.notes_content,
                "file_hashes": self.uploads.file_hashes,
                "total_size_bytes": self.uploads.total_size_bytes,
            },
            "analysis": {
                "target_name": self.analysis.target_name,
                "buyer_name": self.analysis.buyer_name,
                "deal_type": self.analysis.deal_type,
                "selected_domains": self.analysis.selected_domains,
                "phase": self.analysis.phase.value,
                "progress_percent": self.analysis.progress_percent,
                "fact_count": self.analysis.fact_count,
                "gap_count": self.analysis.gap_count,
                "risk_count": self.analysis.risk_count,
                "work_item_count": self.analysis.work_item_count,
                "deal_id": self.analysis.deal_id,
            },
            "view": {
                "current_view": self.view.current_view.value,
                "risk_filters": self.view.risk_filters,
                "work_item_filters": self.view.work_item_filters,
                "fact_filters": self.view.fact_filters,
            },
            "features": self.features,
            "debug": self.debug,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """Deserialize from dictionary."""
        state = cls()
        state.schema_version = data.get("schema_version", 1)
        state.session_id = data.get("session_id", "")
        state.created_at = data.get("created_at", "")
        state.last_activity = data.get("last_activity", "")

        # Uploads
        uploads_data = data.get("uploads", {})
        state.uploads.target_files = uploads_data.get("target_files", [])
        state.uploads.buyer_files = uploads_data.get("buyer_files", [])
        state.uploads.notes_content = uploads_data.get("notes_content", "")
        state.uploads.file_hashes = uploads_data.get("file_hashes", {})
        state.uploads.total_size_bytes = uploads_data.get("total_size_bytes", 0)

        # Analysis
        analysis_data = data.get("analysis", {})
        state.analysis.target_name = analysis_data.get("target_name", "Target Company")
        state.analysis.buyer_name = analysis_data.get("buyer_name")
        state.analysis.deal_type = analysis_data.get("deal_type", "bolt_on")
        state.analysis.selected_domains = analysis_data.get("selected_domains", [])
        state.analysis.phase = AnalysisPhase(analysis_data.get("phase", "idle"))
        state.analysis.progress_percent = analysis_data.get("progress_percent", 0.0)
        state.analysis.fact_count = analysis_data.get("fact_count", 0)
        state.analysis.gap_count = analysis_data.get("gap_count", 0)
        state.analysis.risk_count = analysis_data.get("risk_count", 0)
        state.analysis.work_item_count = analysis_data.get("work_item_count", 0)
        state.analysis.deal_id = analysis_data.get("deal_id")

        # View
        view_data = data.get("view", {})
        state.view.current_view = ViewMode(view_data.get("current_view", "setup"))
        state.view.risk_filters = view_data.get("risk_filters", {})
        state.view.work_item_filters = view_data.get("work_item_filters", {})
        state.view.fact_filters = view_data.get("fact_filters", {})

        # Features
        state.features = data.get("features", state.features)
        state.debug = data.get("debug", False)

        return state


# =============================================================================
# SESSION MANAGER
# =============================================================================

class SessionManager:
    """
    Manages Streamlit session state with typed access.

    Provides:
    - Typed access to session state
    - Session initialization with defaults
    - Session persistence (export/import)
    - Session cleanup and reset
    - Debug utilities
    """

    SESSION_KEY = "_itdd_session"

    @classmethod
    def init(cls, force_new: bool = False) -> SessionState:
        """
        Initialize session state if not exists.

        Args:
            force_new: If True, creates a new session even if one exists

        Returns:
            The current SessionState
        """
        if force_new or cls.SESSION_KEY not in st.session_state:
            session = SessionState(
                session_id=cls._generate_session_id(),
                created_at=datetime.now().isoformat(),
                last_activity=datetime.now().isoformat(),
            )
            st.session_state[cls.SESSION_KEY] = session

        return st.session_state[cls.SESSION_KEY]

    @classmethod
    def get(cls) -> SessionState:
        """
        Get the current session state.

        Initializes if not exists.
        """
        if cls.SESSION_KEY not in st.session_state:
            return cls.init()

        session = st.session_state[cls.SESSION_KEY]
        session.touch()
        return session

    @classmethod
    def reset(cls, preserve_features: bool = True) -> SessionState:
        """
        Reset session state to defaults.

        Args:
            preserve_features: If True, keeps feature flags from old session
        """
        old_features = {}
        if preserve_features and cls.SESSION_KEY in st.session_state:
            old_features = st.session_state[cls.SESSION_KEY].features

        session = cls.init(force_new=True)

        if preserve_features:
            session.features.update(old_features)

        return session

    @classmethod
    def export(cls) -> str:
        """Export current session state as JSON."""
        session = cls.get()
        return json.dumps(session.to_dict(), indent=2)

    @classmethod
    def import_state(cls, json_data: str) -> SessionState:
        """Import session state from JSON."""
        data = json.loads(json_data)
        session = SessionState.from_dict(data)
        st.session_state[cls.SESSION_KEY] = session
        return session

    @classmethod
    def set_debug(cls, enabled: bool):
        """Enable or disable debug mode."""
        session = cls.get()
        session.debug = enabled

    @classmethod
    def is_debug(cls) -> bool:
        """Check if debug mode is enabled."""
        session = cls.get()
        return session.debug

    @classmethod
    def _generate_session_id(cls) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def init_session(force_new: bool = False) -> SessionState:
    """Initialize session state."""
    return SessionManager.init(force_new=force_new)


def get_session() -> SessionState:
    """Get current session state."""
    return SessionManager.get()


def reset_session(preserve_features: bool = True) -> SessionState:
    """Reset session state."""
    return SessionManager.reset(preserve_features=preserve_features)


# =============================================================================
# FILE HASH UTILITY
# =============================================================================

def compute_file_hash(content: bytes) -> str:
    """Compute SHA256 hash of file content."""
    return hashlib.sha256(content).hexdigest()[:16]
