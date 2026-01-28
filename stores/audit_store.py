"""
Audit Store - Tracks All Validation Actions

Provides a complete audit trail of:
- Extraction events
- Validation events
- Human review events
- Correction events
- System events

This enables:
- Compliance reporting
- Debugging validation issues
- Understanding how facts evolved
- Tracking who did what and when
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# AUDIT ACTION TYPES
# =============================================================================

class AuditAction(Enum):
    """Types of auditable actions."""
    # Extraction events
    FACT_EXTRACTED = "fact_extracted"
    DOMAIN_EXTRACTION_STARTED = "domain_extraction_started"
    DOMAIN_EXTRACTION_COMPLETED = "domain_extraction_completed"

    # Validation events
    FACT_VALIDATED = "fact_validated"
    FLAG_ADDED = "flag_added"
    FLAG_RESOLVED = "flag_resolved"
    EVIDENCE_VERIFIED = "evidence_verified"
    CATEGORY_VALIDATED = "category_validated"
    DOMAIN_VALIDATED = "domain_validated"
    CROSS_DOMAIN_VALIDATED = "cross_domain_validated"
    ADVERSARIAL_REVIEW_COMPLETED = "adversarial_review_completed"

    # Human review events
    HUMAN_REVIEW_STARTED = "human_review_started"
    HUMAN_CONFIRMED = "human_confirmed"
    HUMAN_CORRECTED = "human_corrected"
    HUMAN_REJECTED = "human_rejected"
    HUMAN_SKIPPED = "human_skipped"
    MANUAL_FLAG_ADDED = "manual_flag_added"

    # Re-extraction events
    REEXTRACTION_TRIGGERED = "reextraction_triggered"
    REEXTRACTION_COMPLETED = "reextraction_completed"
    ESCALATION_CREATED = "escalation_created"

    # Derived value events
    DERIVED_VALUE_UPDATED = "derived_value_updated"
    RIPPLE_EFFECT_APPLIED = "ripple_effect_applied"

    # System events
    SESSION_STARTED = "session_started"
    SESSION_LOADED = "session_loaded"
    EXPORT_GENERATED = "export_generated"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AuditEntry:
    """A single audit log entry."""
    entry_id: str
    timestamp: datetime
    action: AuditAction
    fact_id: Optional[str] = None
    domain: Optional[str] = None
    user: Optional[str] = None
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    details: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "fact_id": self.fact_id,
            "domain": self.domain,
            "user": self.user,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "details": self.details,
            "session_id": self.session_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEntry':
        return cls(
            entry_id=data["entry_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action=AuditAction(data["action"]),
            fact_id=data.get("fact_id"),
            domain=data.get("domain"),
            user=data.get("user"),
            previous_state=data.get("previous_state"),
            new_state=data.get("new_state"),
            details=data.get("details", {}),
            session_id=data.get("session_id")
        )


@dataclass
class AuditSummary:
    """Summary of audit activity."""
    total_entries: int
    by_action: Dict[str, int]
    by_domain: Dict[str, int]
    by_user: Dict[str, int]
    time_range: Dict[str, str]
    recent_entries: List[AuditEntry]


# =============================================================================
# AUDIT STORE CLASS
# =============================================================================

class AuditStore:
    """
    Stores and retrieves audit log entries.

    Provides:
    - In-memory storage with optional persistence
    - Filtering by action, domain, user, time
    - Fact-specific audit trails
    - Summary statistics
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        storage_path: Optional[Path] = None,
        max_entries: int = 10000
    ):
        """
        Initialize the audit store.

        Args:
            session_id: Optional session identifier
            storage_path: Optional path for persistence
            max_entries: Maximum entries to keep in memory
        """
        self.session_id = session_id
        self.storage_path = storage_path
        self.max_entries = max_entries
        self.entries: List[AuditEntry] = []
        self._entry_counter = 0

        # Load from storage if available
        if storage_path and storage_path.exists():
            self._load_from_storage()

    # =========================================================================
    # LOGGING METHODS
    # =========================================================================

    def log_action(
        self,
        action: AuditAction,
        fact_id: Optional[str] = None,
        domain: Optional[str] = None,
        user: Optional[str] = None,
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an auditable action.

        Args:
            action: The action type
            fact_id: Optional fact being affected
            domain: Optional domain
            user: Optional user performing action
            previous_state: State before action
            new_state: State after action
            details: Additional details

        Returns:
            entry_id of the logged entry
        """
        self._entry_counter += 1
        entry_id = f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._entry_counter:04d}"

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            action=action,
            fact_id=fact_id,
            domain=domain,
            user=user,
            previous_state=previous_state,
            new_state=new_state,
            details=details or {},
            session_id=self.session_id
        )

        self.entries.append(entry)

        # Trim if over max
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

        # Auto-save if storage configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Audit: {action.value} - {fact_id or domain or 'system'}")

        return entry_id

    # =========================================================================
    # CONVENIENCE LOGGING METHODS
    # =========================================================================

    def log_fact_extracted(
        self,
        fact_id: str,
        domain: str,
        details: Dict[str, Any]
    ) -> str:
        """Log fact extraction."""
        return self.log_action(
            action=AuditAction.FACT_EXTRACTED,
            fact_id=fact_id,
            domain=domain,
            details=details
        )

    def log_fact_validated(
        self,
        fact_id: str,
        confidence: float,
        flags_count: int
    ) -> str:
        """Log fact validation."""
        return self.log_action(
            action=AuditAction.FACT_VALIDATED,
            fact_id=fact_id,
            details={
                "confidence": confidence,
                "flags_count": flags_count
            }
        )

    def log_flag_added(
        self,
        fact_id: str,
        flag_id: str,
        severity: str,
        message: str,
        source: str = "ai"
    ) -> str:
        """Log flag addition."""
        return self.log_action(
            action=AuditAction.FLAG_ADDED,
            fact_id=fact_id,
            details={
                "flag_id": flag_id,
                "severity": severity,
                "message": message,
                "source": source
            }
        )

    def log_flag_resolved(
        self,
        fact_id: str,
        flag_id: str,
        resolved_by: str,
        note: Optional[str] = None
    ) -> str:
        """Log flag resolution."""
        return self.log_action(
            action=AuditAction.FLAG_RESOLVED,
            fact_id=fact_id,
            user=resolved_by,
            details={
                "flag_id": flag_id,
                "note": note
            }
        )

    def log_human_confirmed(
        self,
        fact_id: str,
        reviewer: str,
        notes: Optional[str] = None
    ) -> str:
        """Log human confirmation."""
        return self.log_action(
            action=AuditAction.HUMAN_CONFIRMED,
            fact_id=fact_id,
            user=reviewer,
            details={"notes": notes}
        )

    def log_human_corrected(
        self,
        fact_id: str,
        reviewer: str,
        correction_id: str,
        original: Dict[str, Any],
        corrected: Dict[str, Any]
    ) -> str:
        """Log human correction."""
        return self.log_action(
            action=AuditAction.HUMAN_CORRECTED,
            fact_id=fact_id,
            user=reviewer,
            previous_state=original,
            new_state=corrected,
            details={"correction_id": correction_id}
        )

    def log_human_rejected(
        self,
        fact_id: str,
        reviewer: str,
        reason: str
    ) -> str:
        """Log human rejection."""
        return self.log_action(
            action=AuditAction.HUMAN_REJECTED,
            fact_id=fact_id,
            user=reviewer,
            details={"reason": reason}
        )

    def log_reextraction(
        self,
        domain: str,
        attempt: int,
        missing_items: List[str]
    ) -> str:
        """Log re-extraction trigger."""
        return self.log_action(
            action=AuditAction.REEXTRACTION_TRIGGERED,
            domain=domain,
            details={
                "attempt": attempt,
                "missing_items": missing_items
            }
        )

    def log_escalation(
        self,
        domain: str,
        attempts: int,
        remaining_issues: List[str]
    ) -> str:
        """Log escalation to human review."""
        return self.log_action(
            action=AuditAction.ESCALATION_CREATED,
            domain=domain,
            details={
                "attempts": attempts,
                "remaining_issues": remaining_issues
            }
        )

    def log_ripple_effect(
        self,
        source_fact_id: str,
        affected_fact_ids: List[str],
        field: str,
        old_value: Any,
        new_value: Any
    ) -> str:
        """Log ripple effect from correction."""
        return self.log_action(
            action=AuditAction.RIPPLE_EFFECT_APPLIED,
            fact_id=source_fact_id,
            previous_state={field: old_value},
            new_state={field: new_value},
            details={"affected_fact_ids": affected_fact_ids}
        )

    # =========================================================================
    # RETRIEVAL METHODS
    # =========================================================================

    def get_audit_trail(self, fact_id: str) -> List[AuditEntry]:
        """
        Get complete audit trail for a specific fact.

        Args:
            fact_id: The fact to get history for

        Returns:
            List of audit entries in chronological order
        """
        return [e for e in self.entries if e.fact_id == fact_id]

    def get_audit_log(
        self,
        action: Optional[AuditAction] = None,
        domain: Optional[str] = None,
        user: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """
        Get filtered audit log.

        Args:
            action: Filter by action type
            domain: Filter by domain
            user: Filter by user
            since: Filter entries after this time
            until: Filter entries before this time
            limit: Maximum entries to return

        Returns:
            List of matching audit entries
        """
        results = self.entries

        if action:
            results = [e for e in results if e.action == action]

        if domain:
            results = [e for e in results if e.domain == domain]

        if user:
            results = [e for e in results if e.user == user]

        if since:
            results = [e for e in results if e.timestamp >= since]

        if until:
            results = [e for e in results if e.timestamp <= until]

        # Return most recent first, limited
        return list(reversed(results[-limit:]))

    def get_recent_activity(
        self,
        limit: int = 20,
        include_system: bool = False
    ) -> List[AuditEntry]:
        """
        Get recent activity for display.

        Args:
            limit: Maximum entries
            include_system: Include system events

        Returns:
            Recent audit entries
        """
        results = self.entries

        if not include_system:
            system_actions = {
                AuditAction.SESSION_STARTED,
                AuditAction.SESSION_LOADED,
                AuditAction.EXPORT_GENERATED
            }
            results = [e for e in results if e.action not in system_actions]

        return list(reversed(results[-limit:]))

    def get_summary(self) -> AuditSummary:
        """
        Get summary statistics of audit activity.

        Returns:
            AuditSummary with counts and breakdowns
        """
        by_action = {}
        by_domain = {}
        by_user = {}

        for entry in self.entries:
            # Count by action
            action_name = entry.action.value
            by_action[action_name] = by_action.get(action_name, 0) + 1

            # Count by domain
            if entry.domain:
                by_domain[entry.domain] = by_domain.get(entry.domain, 0) + 1

            # Count by user
            if entry.user:
                by_user[entry.user] = by_user.get(entry.user, 0) + 1

        # Time range
        time_range = {}
        if self.entries:
            time_range["earliest"] = self.entries[0].timestamp.isoformat()
            time_range["latest"] = self.entries[-1].timestamp.isoformat()

        return AuditSummary(
            total_entries=len(self.entries),
            by_action=by_action,
            by_domain=by_domain,
            by_user=by_user,
            time_range=time_range,
            recent_entries=self.get_recent_activity(10)
        )

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _save_to_storage(self):
        """Save audit log to storage."""
        if not self.storage_path:
            return

        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(
                    [e.to_dict() for e in self.entries],
                    f,
                    indent=2,
                    default=str
                )
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")

    def _load_from_storage(self):
        """Load audit log from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.entries = [AuditEntry.from_dict(d) for d in data]
                self._entry_counter = len(self.entries)
                logger.info(f"Loaded {len(self.entries)} audit entries from storage")
        except Exception as e:
            logger.error(f"Failed to load audit log: {e}")

    def export_to_json(self, filepath: Path) -> bool:
        """
        Export full audit log to JSON file.

        Args:
            filepath: Path to export to

        Returns:
            True if successful
        """
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(
                    {
                        "session_id": self.session_id,
                        "export_timestamp": datetime.now().isoformat(),
                        "total_entries": len(self.entries),
                        "entries": [e.to_dict() for e in self.entries]
                    },
                    f,
                    indent=2,
                    default=str
                )
            return True
        except Exception as e:
            logger.error(f"Failed to export audit log: {e}")
            return False

    def clear(self):
        """Clear all audit entries."""
        self.entries = []
        self._entry_counter = 0
        if self.storage_path and self.storage_path.exists():
            self.storage_path.unlink()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_audit_store(
    session_id: Optional[str] = None,
    storage_path: Optional[Path] = None
) -> AuditStore:
    """Create an audit store instance."""
    return AuditStore(session_id=session_id, storage_path=storage_path)
