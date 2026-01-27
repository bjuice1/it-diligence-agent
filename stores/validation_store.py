"""
Validation Store - Persistence for Validation State

Stores and manages validation states for facts across all domains.
Provides methods for:
- Getting/updating fact validation states
- Finding facts needing review
- Tracking domain-level validation
- Managing flags
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from threading import RLock

from models.validation_models import (
    ValidationStatus, FlagSeverity, FlagCategory,
    ValidationFlag, FactValidationState, DomainValidationState,
    CrossDomainValidationState, generate_flag_id
)

logger = logging.getLogger(__name__)


class ValidationStore:
    """
    Stores validation state for all facts in an analysis session.

    Thread-safe storage with optional persistence to disk.
    """

    def __init__(self, session_id: str, persist_dir: Optional[Path] = None):
        """
        Initialize the validation store.

        Args:
            session_id: Unique identifier for this analysis session
            persist_dir: Optional directory for persistence (if None, memory only)
        """
        self.session_id = session_id
        self.persist_dir = persist_dir
        self._lock = RLock()  # Use reentrant lock for nested locking

        # In-memory storage
        self._fact_states: Dict[str, FactValidationState] = {}
        self._domain_states: Dict[str, DomainValidationState] = {}
        self._cross_domain_state: Optional[CrossDomainValidationState] = None

        # Load from disk if persistence enabled and file exists
        if persist_dir:
            self._load_from_disk()

    # =========================================================================
    # FACT VALIDATION STATE
    # =========================================================================

    def get_validation_state(self, fact_id: str) -> Optional[FactValidationState]:
        """Get validation state for a specific fact."""
        with self._lock:
            return self._fact_states.get(fact_id)

    def get_or_create_state(self, fact_id: str) -> FactValidationState:
        """Get validation state, creating if it doesn't exist."""
        with self._lock:
            if fact_id not in self._fact_states:
                self._fact_states[fact_id] = FactValidationState(fact_id=fact_id)
            return self._fact_states[fact_id]

    def update_validation_state(self, fact_id: str, state: FactValidationState):
        """Update validation state for a fact."""
        with self._lock:
            self._fact_states[fact_id] = state
            self._persist_if_enabled()

    def get_all_fact_states(self, domain: Optional[str] = None) -> List[FactValidationState]:
        """Get all fact validation states, optionally filtered by domain."""
        with self._lock:
            states = list(self._fact_states.values())
            # Note: We'd need fact->domain mapping to filter by domain
            # For now, return all
            return states

    # =========================================================================
    # HUMAN REVIEW QUEUE
    # =========================================================================

    def get_facts_needing_review(
        self,
        domain: Optional[str] = None,
        min_severity: Optional[FlagSeverity] = None,
        limit: int = 100
    ) -> List[FactValidationState]:
        """
        Get facts that need human review.

        Args:
            domain: Filter by domain (requires fact->domain mapping)
            min_severity: Minimum severity level to include
            limit: Maximum number of results

        Returns:
            List of FactValidationState objects needing review,
            sorted by severity (CRITICAL first)
        """
        with self._lock:
            # Filter to facts needing review
            needing_review = [
                state for state in self._fact_states.values()
                if state.needs_human_review
            ]

            # Filter by minimum severity if specified
            if min_severity:
                needing_review = [
                    state for state in needing_review
                    if state.highest_severity and
                       state.highest_severity.priority >= min_severity.priority
                ]

            # Sort by severity (highest first)
            def severity_key(state: FactValidationState) -> int:
                sev = state.highest_severity
                return sev.priority if sev else 0

            needing_review.sort(key=severity_key, reverse=True)

            return needing_review[:limit]

    def count_needing_review(self, domain: Optional[str] = None) -> int:
        """Count facts needing human review."""
        return len(self.get_facts_needing_review(domain=domain, limit=10000))

    def count_reviewed(self, domain: Optional[str] = None) -> int:
        """Count facts that have been human reviewed."""
        with self._lock:
            return sum(1 for s in self._fact_states.values() if s.human_reviewed)

    # =========================================================================
    # HUMAN REVIEW ACTIONS
    # =========================================================================

    def mark_human_confirmed(
        self,
        fact_id: str,
        reviewer: str,
        notes: Optional[str] = None
    ):
        """Mark a fact as confirmed by human review."""
        with self._lock:
            state = self._fact_states.get(fact_id)
            if state:
                state.mark_human_confirmed(reviewer, notes)
                self._persist_if_enabled()
                logger.info(f"Fact {fact_id} confirmed by {reviewer}")

    def mark_human_corrected(
        self,
        fact_id: str,
        corrected_by: str,
        correction_id: str,
        original: Dict[str, Any],
        corrected: Dict[str, Any],
        notes: Optional[str] = None
    ):
        """Mark a fact as corrected by human."""
        with self._lock:
            state = self._fact_states.get(fact_id)
            if state:
                state.mark_human_corrected(
                    corrected_by, correction_id, original, corrected, notes
                )
                self._persist_if_enabled()
                logger.info(f"Fact {fact_id} corrected by {corrected_by}")

    def mark_human_rejected(
        self,
        fact_id: str,
        reviewer: str,
        reason: str
    ):
        """Mark a fact as rejected by human."""
        with self._lock:
            state = self._fact_states.get(fact_id)
            if state:
                state.mark_human_rejected(reviewer, reason)
                self._persist_if_enabled()
                logger.info(f"Fact {fact_id} rejected by {reviewer}: {reason}")

    # =========================================================================
    # FLAG MANAGEMENT
    # =========================================================================

    def add_flag(
        self,
        fact_id: str,
        flag: ValidationFlag,
        source: str = "ai_validation"
    ):
        """Add a validation flag to a fact."""
        with self._lock:
            state = self.get_or_create_state(fact_id)
            flag.source = source
            state.add_flag(flag)
            self._persist_if_enabled()
            logger.debug(f"Added {flag.severity.value} flag to {fact_id}: {flag.message[:50]}")

    def resolve_flag(
        self,
        fact_id: str,
        flag_id: str,
        resolved_by: str,
        note: Optional[str] = None
    ) -> bool:
        """Resolve a validation flag."""
        with self._lock:
            state = self._fact_states.get(fact_id)
            if not state:
                return False

            for flag in state.ai_flags:
                if flag.flag_id == flag_id:
                    flag.resolve(resolved_by, note)
                    self._persist_if_enabled()
                    logger.info(f"Flag {flag_id} resolved by {resolved_by}")
                    return True

            return False

    def get_all_flags(
        self,
        unresolved_only: bool = True,
        min_severity: Optional[FlagSeverity] = None
    ) -> List[ValidationFlag]:
        """Get all flags across all facts."""
        with self._lock:
            all_flags = []
            for state in self._fact_states.values():
                for flag in state.ai_flags:
                    if unresolved_only and flag.resolved:
                        continue
                    if min_severity and flag.severity.priority < min_severity.priority:
                        continue
                    all_flags.append(flag)

            # Sort by severity
            all_flags.sort(key=lambda f: f.severity.priority, reverse=True)
            return all_flags

    # =========================================================================
    # EVIDENCE VALIDATION
    # =========================================================================

    def update_evidence_status(
        self,
        fact_id: str,
        verified: bool,
        match_score: float,
        matched_text: Optional[str] = None
    ):
        """Update evidence verification status for a fact."""
        with self._lock:
            state = self.get_or_create_state(fact_id)
            state.evidence_verified = verified
            state.evidence_match_score = match_score
            state.evidence_matched_text = matched_text

            # Add flag if evidence not found
            if not verified and match_score < 0.5:
                flag = ValidationFlag(
                    flag_id=generate_flag_id(),
                    severity=FlagSeverity.CRITICAL,
                    category=FlagCategory.EVIDENCE,
                    message="Evidence not found in source document - possible hallucination",
                    suggestion="Verify this fact manually against the source document"
                )
                state.add_flag(flag)
            elif not verified and match_score < 0.85:
                flag = ValidationFlag(
                    flag_id=generate_flag_id(),
                    severity=FlagSeverity.WARNING,
                    category=FlagCategory.EVIDENCE,
                    message=f"Evidence partially matches ({match_score:.0%}) - may be paraphrased",
                    suggestion="Check if the paraphrasing is accurate"
                )
                state.add_flag(flag)

            self._persist_if_enabled()

    # =========================================================================
    # AI VALIDATION
    # =========================================================================

    def mark_ai_validated(
        self,
        fact_id: str,
        confidence: float,
        flags: Optional[List[ValidationFlag]] = None
    ):
        """Mark a fact as AI validated with given confidence and flags."""
        with self._lock:
            state = self.get_or_create_state(fact_id)
            state.mark_ai_validated(confidence)

            if flags:
                for flag in flags:
                    state.add_flag(flag)

            self._persist_if_enabled()

    # =========================================================================
    # DOMAIN VALIDATION STATE
    # =========================================================================

    def get_domain_state(self, domain: str) -> DomainValidationState:
        """Get validation state for a domain, creating if needed."""
        with self._lock:
            if domain not in self._domain_states:
                self._domain_states[domain] = DomainValidationState(domain=domain)
            return self._domain_states[domain]

    def update_domain_state(self, domain: str, state: DomainValidationState):
        """Update domain validation state."""
        with self._lock:
            self._domain_states[domain] = state
            self._persist_if_enabled()

    def get_all_domain_states(self) -> Dict[str, DomainValidationState]:
        """Get all domain states."""
        with self._lock:
            return dict(self._domain_states)

    # =========================================================================
    # CROSS-DOMAIN VALIDATION
    # =========================================================================

    def get_cross_domain_state(self) -> Optional[CrossDomainValidationState]:
        """Get cross-domain validation state."""
        with self._lock:
            return self._cross_domain_state

    def set_cross_domain_state(self, state: CrossDomainValidationState):
        """Set cross-domain validation state."""
        with self._lock:
            self._cross_domain_state = state
            self._persist_if_enabled()

    # =========================================================================
    # AGGREGATE STATISTICS
    # =========================================================================

    def get_overall_confidence(self) -> float:
        """Calculate overall confidence across all domains."""
        domain_states = self.get_all_domain_states()
        if not domain_states:
            return 0.0

        confidences = [s.overall_confidence for s in domain_states.values()]
        return sum(confidences) / len(confidences)

    def get_stats_by_domain(self) -> Dict[str, Dict[str, int]]:
        """Get statistics broken down by domain."""
        result = {}
        for domain, state in self._domain_states.items():
            result[domain] = {
                "total_facts": state.total_facts,
                "facts_flagged": state.facts_flagged,
                "facts_reviewed": state.facts_human_reviewed,
                "facts_confirmed": state.facts_confirmed,
                "facts_corrected": state.facts_corrected,
                "confidence": state.overall_confidence
            }
        return result

    def get_stats_by_severity(self) -> Dict[str, int]:
        """Get flag counts by severity."""
        all_flags = self.get_all_flags(unresolved_only=True)
        stats = {sev.value: 0 for sev in FlagSeverity}
        for flag in all_flags:
            stats[flag.severity.value] += 1
        return stats

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
        filepath = self.persist_dir / f"validation_state_{self.session_id}.json"

        data = {
            "session_id": self.session_id,
            "saved_at": datetime.now().isoformat(),
            "fact_states": {k: v.to_dict() for k, v in self._fact_states.items()},
            "domain_states": {k: v.to_dict() for k, v in self._domain_states.items()},
            "cross_domain_state": self._cross_domain_state.to_dict() if self._cross_domain_state else None
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved validation state to {filepath}")

    def _load_from_disk(self):
        """Load state from disk if it exists."""
        if not self.persist_dir:
            return

        filepath = self.persist_dir / f"validation_state_{self.session_id}.json"
        if not filepath.exists():
            return

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self._fact_states = {
                k: FactValidationState.from_dict(v)
                for k, v in data.get("fact_states", {}).items()
            }

            # Domain states would need from_dict method
            # For now, leave empty and let them be recreated

            logger.info(f"Loaded validation state from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load validation state: {e}")

    def clear(self):
        """Clear all validation state."""
        with self._lock:
            self._fact_states.clear()
            self._domain_states.clear()
            self._cross_domain_state = None
            self._persist_if_enabled()
