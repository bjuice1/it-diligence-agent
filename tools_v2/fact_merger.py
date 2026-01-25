"""
Fact Merger for Incremental Document Updates

Handles merging new facts from updated documents while:
- Preserving human verifications
- Detecting conflicts between old and new facts
- Flagging changes for review
- Maintaining fact history
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import difflib

from tools_v2.fact_store import FactStore, Fact, VerificationStatus

logger = logging.getLogger(__name__)


class MergeAction(Enum):
    """What action to take when merging a fact."""
    ADD = "add"                  # New fact, add to store
    UPDATE = "update"            # Update existing fact (preserve verification)
    SKIP = "skip"                # Duplicate, skip
    CONFLICT = "conflict"        # Conflicts with verified fact, flag for review
    SUPERSEDE = "supersede"      # Replace old fact with new


class ConflictType(Enum):
    """Type of conflict detected during merge."""
    VALUE_CHANGED = "value_changed"      # Same fact, different value
    EVIDENCE_CHANGED = "evidence_changed"  # Different evidence for same fact
    STATUS_CONFLICT = "status_conflict"   # New says X, old verified as Y
    REMOVED = "removed"                   # Fact no longer in new document


@dataclass
class FactConflict:
    """Represents a conflict between old and new fact."""
    conflict_id: str
    conflict_type: ConflictType
    existing_fact_id: str
    new_fact_data: Dict[str, Any]
    field_conflicts: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)  # field -> (old, new)
    resolution: str = ""         # "keep_existing", "use_new", "merge", ""
    resolved_by: str = ""
    resolved_at: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type.value,
            "existing_fact_id": self.existing_fact_id,
            "new_fact_data": self.new_fact_data,
            "field_conflicts": self.field_conflicts,
            "resolution": self.resolution,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at,
            "notes": self.notes
        }


@dataclass
class MergeResult:
    """Result of a merge operation."""
    facts_added: List[str] = field(default_factory=list)
    facts_updated: List[str] = field(default_factory=list)
    facts_skipped: List[str] = field(default_factory=list)
    facts_removed: List[str] = field(default_factory=list)
    conflicts: List[FactConflict] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.facts_added) + len(self.facts_updated) + len(self.facts_removed)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "facts_added": self.facts_added,
            "facts_updated": self.facts_updated,
            "facts_skipped": self.facts_skipped,
            "facts_removed": self.facts_removed,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "total_changes": self.total_changes,
            "has_conflicts": self.has_conflicts
        }


class FactMerger:
    """
    Merges new facts into an existing fact store.

    Strategies:
    - Unverified facts: Update freely
    - Verified facts: Flag conflicts for human review
    - New facts: Add with "new" change status
    - Missing facts: Mark as potentially removed
    """

    # Similarity threshold for considering facts as duplicates
    SIMILARITY_THRESHOLD = 0.85

    def __init__(self, fact_store: FactStore):
        self.fact_store = fact_store
        self.conflicts: List[FactConflict] = []
        self._conflict_counter = 0

    def _generate_conflict_id(self) -> str:
        """Generate unique conflict ID."""
        self._conflict_counter += 1
        return f"CONF-{self._conflict_counter:04d}"

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def find_matching_fact(self, new_fact_data: Dict[str, Any]) -> Optional[Fact]:
        """
        Find an existing fact that matches the new fact data.

        Matching criteria:
        1. Same fact_id (if provided)
        2. Same domain + category + high similarity item name
        3. High similarity in evidence quote
        """
        # Try exact ID match first
        if "fact_id" in new_fact_data:
            existing = self.fact_store.get_fact(new_fact_data["fact_id"])
            if existing:
                return existing

        domain = new_fact_data.get("domain", "")
        category = new_fact_data.get("category", "")
        item = new_fact_data.get("item", "")

        # Search for similar facts in same domain/category
        candidates = [
            f for f in self.fact_store.facts
            if f.domain == domain and f.category == category
        ]

        best_match = None
        best_score = 0.0

        for candidate in candidates:
            # Check item similarity
            item_sim = self.compute_similarity(item, candidate.item)

            # Check evidence similarity if both have evidence
            evidence_sim = 0.0
            new_evidence = new_fact_data.get("evidence", {}).get("exact_quote", "")
            old_evidence = candidate.evidence.get("exact_quote", "") if candidate.evidence else ""
            if new_evidence and old_evidence:
                evidence_sim = self.compute_similarity(new_evidence, old_evidence)

            # Combined score (weight item more heavily)
            score = (item_sim * 0.7) + (evidence_sim * 0.3)

            if score > best_score and score >= self.SIMILARITY_THRESHOLD:
                best_score = score
                best_match = candidate

        return best_match

    def detect_conflicts(
        self,
        existing_fact: Fact,
        new_fact_data: Dict[str, Any]
    ) -> Optional[FactConflict]:
        """
        Detect if there's a conflict between existing verified fact and new data.

        Only flags conflicts for VERIFIED facts. Unverified facts can be updated freely.
        """
        # Only check conflicts for verified facts
        if existing_fact.verification_status != VerificationStatus.CONFIRMED:
            return None

        field_conflicts = {}

        # Check item/name changes
        if new_fact_data.get("item") and new_fact_data["item"] != existing_fact.item:
            field_conflicts["item"] = (existing_fact.item, new_fact_data["item"])

        # Check status changes
        if new_fact_data.get("status") and new_fact_data["status"] != existing_fact.status:
            field_conflicts["status"] = (existing_fact.status, new_fact_data["status"])

        # Check significant detail changes
        new_details = new_fact_data.get("details", {})
        for key, new_value in new_details.items():
            old_value = existing_fact.details.get(key)
            if old_value and str(old_value) != str(new_value):
                field_conflicts[f"details.{key}"] = (old_value, new_value)

        # Check evidence changes
        new_evidence = new_fact_data.get("evidence", {}).get("exact_quote", "")
        old_evidence = existing_fact.evidence.get("exact_quote", "") if existing_fact.evidence else ""
        if new_evidence and old_evidence:
            similarity = self.compute_similarity(new_evidence, old_evidence)
            if similarity < 0.8:  # Significant evidence change
                field_conflicts["evidence"] = (old_evidence[:100], new_evidence[:100])

        if field_conflicts:
            conflict_type = ConflictType.VALUE_CHANGED
            if "evidence" in field_conflicts:
                conflict_type = ConflictType.EVIDENCE_CHANGED

            return FactConflict(
                conflict_id=self._generate_conflict_id(),
                conflict_type=conflict_type,
                existing_fact_id=existing_fact.fact_id,
                new_fact_data=new_fact_data,
                field_conflicts=field_conflicts
            )

        return None

    def determine_action(
        self,
        new_fact_data: Dict[str, Any],
        source_document: str = ""
    ) -> Tuple[MergeAction, Optional[Fact], Optional[FactConflict]]:
        """
        Determine what action to take for a new fact.

        Returns:
            Tuple of (action, existing_fact if matched, conflict if any)
        """
        # Find matching existing fact
        existing = self.find_matching_fact(new_fact_data)

        if not existing:
            return MergeAction.ADD, None, None

        # Check if it's from the same document (re-processing)
        if source_document and existing.source_document == source_document:
            # Same document, check if content changed
            if self._facts_are_identical(existing, new_fact_data):
                return MergeAction.SKIP, existing, None
            else:
                # Content changed in same doc - update
                return MergeAction.UPDATE, existing, None

        # Check for conflicts with verified facts
        conflict = self.detect_conflicts(existing, new_fact_data)
        if conflict:
            return MergeAction.CONFLICT, existing, conflict

        # Unverified fact - can update freely
        if existing.verification_status == VerificationStatus.PENDING:
            return MergeAction.UPDATE, existing, None

        # Verified but no conflicts - skip (already have good data)
        return MergeAction.SKIP, existing, None

    def _facts_are_identical(self, existing: Fact, new_data: Dict[str, Any]) -> bool:
        """Check if facts are identical (no meaningful changes)."""
        if new_data.get("item") != existing.item:
            return False
        if new_data.get("status") != existing.status:
            return False
        if new_data.get("details") != existing.details:
            return False
        return True

    def merge_fact(
        self,
        new_fact_data: Dict[str, Any],
        source_document: str = ""
    ) -> Tuple[MergeAction, Optional[str]]:
        """
        Merge a single fact into the store.

        Returns:
            Tuple of (action taken, fact_id if added/updated)
        """
        action, existing, conflict = self.determine_action(new_fact_data, source_document)

        if action == MergeAction.ADD:
            # Add new fact
            new_fact_data["source_document"] = source_document
            fact = self.fact_store.add_fact_from_dict(new_fact_data)
            if fact:
                # Mark as new for "What's New" view
                fact.verification_note = f"[NEW] Added from {source_document}"
                return action, fact.fact_id
            return action, None

        elif action == MergeAction.UPDATE:
            # Update existing fact while preserving verification status
            self._update_fact(existing, new_fact_data, source_document)
            return action, existing.fact_id

        elif action == MergeAction.CONFLICT:
            # Store conflict for review
            self.conflicts.append(conflict)
            return action, existing.fact_id

        else:  # SKIP
            return action, existing.fact_id if existing else None

    def _update_fact(
        self,
        existing: Fact,
        new_data: Dict[str, Any],
        source_document: str
    ) -> None:
        """Update existing fact with new data while preserving key fields."""
        # Preserve these fields
        preserved_verification = existing.verification_status
        preserved_note = existing.verification_note
        preserved_reviewer = existing.reviewer_id

        # Update fields
        if new_data.get("item"):
            existing.item = new_data["item"]
        if new_data.get("details"):
            existing.details.update(new_data["details"])
        if new_data.get("evidence"):
            existing.evidence = new_data["evidence"]
        if new_data.get("status"):
            existing.status = new_data["status"]

        # Track update
        existing.updated_at = datetime.now().isoformat()
        if source_document and source_document not in existing.source_document:
            existing.source_document = f"{existing.source_document}, {source_document}"

        # Restore verification (but add note about update)
        existing.verification_status = preserved_verification
        existing.verification_note = f"[UPDATED] {preserved_note}" if preserved_note else "[UPDATED]"
        existing.reviewer_id = preserved_reviewer

        # Recalculate confidence
        existing.confidence_score = existing.calculate_confidence()

    def merge_document_facts(
        self,
        new_facts: List[Dict[str, Any]],
        source_document: str,
        remove_missing: bool = False
    ) -> MergeResult:
        """
        Merge all facts from a document.

        Args:
            new_facts: List of fact dictionaries from the new/updated document
            source_document: Filename of the source document
            remove_missing: If True, mark facts no longer in document as removed

        Returns:
            MergeResult with details of what changed
        """
        result = MergeResult()

        # Track which existing facts were matched
        matched_fact_ids = set()

        for fact_data in new_facts:
            action, fact_id = self.merge_fact(fact_data, source_document)

            if action == MergeAction.ADD:
                result.facts_added.append(fact_id)
            elif action == MergeAction.UPDATE:
                result.facts_updated.append(fact_id)
                matched_fact_ids.add(fact_id)
            elif action == MergeAction.SKIP:
                result.facts_skipped.append(fact_id)
                matched_fact_ids.add(fact_id)
            elif action == MergeAction.CONFLICT:
                matched_fact_ids.add(fact_id)

        # Handle removed facts (facts from this doc no longer present)
        if remove_missing:
            existing_from_doc = [
                f for f in self.fact_store.facts
                if source_document in (f.source_document or "")
                and f.fact_id not in matched_fact_ids
            ]
            for fact in existing_from_doc:
                if fact.verification_status != VerificationStatus.CONFIRMED:
                    # Only auto-remove unverified facts
                    result.facts_removed.append(fact.fact_id)
                    fact.verification_note = f"[REMOVED] No longer in {source_document}"
                else:
                    # Create conflict for verified facts
                    conflict = FactConflict(
                        conflict_id=self._generate_conflict_id(),
                        conflict_type=ConflictType.REMOVED,
                        existing_fact_id=fact.fact_id,
                        new_fact_data={},
                        notes=f"Fact no longer found in updated {source_document}"
                    )
                    self.conflicts.append(conflict)

        result.conflicts = self.conflicts.copy()
        return result

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        resolved_by: str,
        notes: str = ""
    ) -> bool:
        """
        Resolve a conflict.

        Args:
            conflict_id: The conflict to resolve
            resolution: "keep_existing", "use_new", or "merge"
            resolved_by: Who is resolving
            notes: Optional notes about the resolution
        """
        conflict = None
        for c in self.conflicts:
            if c.conflict_id == conflict_id:
                conflict = c
                break

        if not conflict:
            return False

        conflict.resolution = resolution
        conflict.resolved_by = resolved_by
        conflict.resolved_at = datetime.now().isoformat()
        conflict.notes = notes

        existing_fact = self.fact_store.get_fact(conflict.existing_fact_id)
        if not existing_fact:
            return False

        if resolution == "keep_existing":
            # Keep the verified fact as-is
            existing_fact.verification_note += f" [Conflict resolved: kept existing by {resolved_by}]"

        elif resolution == "use_new":
            # Update with new data (loses verification)
            self._update_fact(existing_fact, conflict.new_fact_data, "")
            existing_fact.verification_status = VerificationStatus.PENDING
            existing_fact.verified = False
            existing_fact.verification_note = f"[Conflict resolved: updated with new data by {resolved_by}]"

        elif resolution == "merge":
            # Merge new data but keep verification
            for field, (old_val, new_val) in conflict.field_conflicts.items():
                if field.startswith("details."):
                    key = field.replace("details.", "")
                    existing_fact.details[key] = f"{old_val} / {new_val}"
            existing_fact.verification_note += f" [Conflict merged by {resolved_by}: {notes}]"

        return True

    def get_pending_conflicts(self) -> List[FactConflict]:
        """Get all unresolved conflicts."""
        return [c for c in self.conflicts if not c.resolution]

    def get_whats_new(self, since_run_id: str = None) -> Dict[str, List[Fact]]:
        """
        Get facts that are new or changed.

        Returns dict with:
        - new: Facts added since last run
        - updated: Facts that were updated
        - conflicts: Facts with pending conflicts
        """
        new_facts = [
            f for f in self.fact_store.facts
            if "[NEW]" in (f.verification_note or "")
        ]

        updated_facts = [
            f for f in self.fact_store.facts
            if "[UPDATED]" in (f.verification_note or "")
        ]

        conflict_fact_ids = {c.existing_fact_id for c in self.get_pending_conflicts()}
        conflict_facts = [
            f for f in self.fact_store.facts
            if f.fact_id in conflict_fact_ids
        ]

        return {
            "new": new_facts,
            "updated": updated_facts,
            "conflicts": conflict_facts
        }

    def clear_change_markers(self) -> None:
        """Clear [NEW] and [UPDATED] markers from facts (after user has reviewed)."""
        for fact in self.fact_store.facts:
            if fact.verification_note:
                fact.verification_note = fact.verification_note.replace("[NEW] ", "")
                fact.verification_note = fact.verification_note.replace("[UPDATED] ", "")
                fact.verification_note = fact.verification_note.replace("[REMOVED] ", "")
