"""
Correction Store - Persistence for Human Corrections

Stores and manages correction records for audit trail.
Every human correction is tracked with:
- What was changed
- Who changed it
- Why it was changed
- What ripple effects occurred
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from threading import Lock

from models.validation_models import CorrectionRecord, RippleEffect

logger = logging.getLogger(__name__)


class CorrectionStore:
    """
    Stores all correction records for audit trail.

    Thread-safe storage with optional persistence to disk.
    """

    def __init__(self, session_id: str, persist_dir: Optional[Path] = None):
        """
        Initialize the correction store.

        Args:
            session_id: Unique identifier for this analysis session
            persist_dir: Optional directory for persistence
        """
        self.session_id = session_id
        self.persist_dir = persist_dir
        self._lock = Lock()

        # In-memory storage
        self._corrections: Dict[str, CorrectionRecord] = {}  # correction_id -> record
        self._fact_corrections: Dict[str, List[str]] = {}    # fact_id -> [correction_ids]
        self._ripple_effects: Dict[str, List[RippleEffect]] = {}  # correction_id -> effects

        # Load from disk if enabled
        if persist_dir:
            self._load_from_disk()

    # =========================================================================
    # RECORD CORRECTIONS
    # =========================================================================

    def record_correction(
        self,
        record: CorrectionRecord,
        ripple_effects: Optional[List[RippleEffect]] = None
    ):
        """
        Record a correction.

        Args:
            record: The correction record
            ripple_effects: Any derived values that were updated
        """
        with self._lock:
            # Store the correction
            self._corrections[record.correction_id] = record

            # Track which corrections apply to which facts
            if record.fact_id not in self._fact_corrections:
                self._fact_corrections[record.fact_id] = []
            self._fact_corrections[record.fact_id].append(record.correction_id)

            # Store ripple effects
            if ripple_effects:
                self._ripple_effects[record.correction_id] = ripple_effects

            self._persist_if_enabled()

            logger.info(
                f"Recorded correction {record.correction_id} for fact {record.fact_id} "
                f"by {record.corrected_by}"
            )

    # =========================================================================
    # QUERY CORRECTIONS
    # =========================================================================

    def get_correction(self, correction_id: str) -> Optional[CorrectionRecord]:
        """Get a specific correction by ID."""
        with self._lock:
            return self._corrections.get(correction_id)

    def get_corrections_for_fact(self, fact_id: str) -> List[CorrectionRecord]:
        """Get all corrections made to a specific fact."""
        with self._lock:
            correction_ids = self._fact_corrections.get(fact_id, [])
            return [
                self._corrections[cid]
                for cid in correction_ids
                if cid in self._corrections
            ]

    def get_all_corrections(
        self,
        domain: Optional[str] = None,
        corrected_by: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[CorrectionRecord]:
        """
        Get all corrections, optionally filtered.

        Args:
            domain: Filter by domain (requires fact->domain mapping)
            corrected_by: Filter by who made the correction
            since: Only corrections after this timestamp
        """
        with self._lock:
            corrections = list(self._corrections.values())

            if corrected_by:
                corrections = [c for c in corrections if c.corrected_by == corrected_by]

            if since:
                corrections = [c for c in corrections if c.timestamp >= since]

            # Sort by timestamp descending (most recent first)
            corrections.sort(key=lambda c: c.timestamp, reverse=True)

            return corrections

    def get_ripple_effects(self, correction_id: str) -> List[RippleEffect]:
        """Get ripple effects for a correction."""
        with self._lock:
            return self._ripple_effects.get(correction_id, [])

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_correction_count(self) -> int:
        """Get total number of corrections."""
        with self._lock:
            return len(self._corrections)

    def get_corrections_by_user(self) -> Dict[str, int]:
        """Get correction counts grouped by user."""
        with self._lock:
            counts: Dict[str, int] = {}
            for record in self._corrections.values():
                user = record.corrected_by
                counts[user] = counts.get(user, 0) + 1
            return counts

    def get_most_corrected_facts(self, limit: int = 10) -> List[tuple]:
        """Get facts that have been corrected the most."""
        with self._lock:
            fact_counts = [
                (fact_id, len(correction_ids))
                for fact_id, correction_ids in self._fact_corrections.items()
            ]
            fact_counts.sort(key=lambda x: x[1], reverse=True)
            return fact_counts[:limit]

    def get_correction_summary(self) -> Dict[str, Any]:
        """Get summary statistics about corrections."""
        with self._lock:
            return {
                "total_corrections": len(self._corrections),
                "facts_corrected": len(self._fact_corrections),
                "corrections_by_user": self.get_corrections_by_user(),
                "total_ripple_effects": sum(
                    len(effects) for effects in self._ripple_effects.values()
                )
            }

    # =========================================================================
    # AUDIT EXPORT
    # =========================================================================

    def export_audit_trail(self) -> List[Dict[str, Any]]:
        """Export all corrections as audit trail."""
        with self._lock:
            trail = []
            for record in sorted(self._corrections.values(), key=lambda r: r.timestamp):
                entry = record.to_dict()
                entry["ripple_effects"] = [
                    e.to_dict() for e in self._ripple_effects.get(record.correction_id, [])
                ]
                trail.append(entry)
            return trail

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _persist_if_enabled(self):
        """Save to disk if persistence is enabled."""
        if self.persist_dir:
            self._save_to_disk()

    def _save_to_disk(self):
        """Save current state to disk."""
        if not self.persist_dir:
            return

        self.persist_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.persist_dir / f"corrections_{self.session_id}.json"

        data = {
            "session_id": self.session_id,
            "saved_at": datetime.now().isoformat(),
            "corrections": {k: v.to_dict() for k, v in self._corrections.items()},
            "fact_corrections": self._fact_corrections,
            "ripple_effects": {
                k: [e.to_dict() for e in v]
                for k, v in self._ripple_effects.items()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved corrections to {filepath}")

    def _load_from_disk(self):
        """Load state from disk if it exists."""
        if not self.persist_dir:
            return

        filepath = self.persist_dir / f"corrections_{self.session_id}.json"
        if not filepath.exists():
            return

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self._corrections = {
                k: CorrectionRecord.from_dict(v)
                for k, v in data.get("corrections", {}).items()
            }
            self._fact_corrections = data.get("fact_corrections", {})

            # Ripple effects would need from_dict - skip for now

            logger.info(f"Loaded {len(self._corrections)} corrections from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load corrections: {e}")

    def clear(self):
        """Clear all correction records."""
        with self._lock:
            self._corrections.clear()
            self._fact_corrections.clear()
            self._ripple_effects.clear()
            self._persist_if_enabled()
