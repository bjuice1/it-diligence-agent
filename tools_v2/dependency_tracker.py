"""
Dependency Tracker for Fact-to-Item Relationships

Tracks which items (risks, work items, inventory items) depend on which facts.
When facts change, this allows identifying what needs review.

Phase 4 Steps 86-91
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import json

logger = logging.getLogger(__name__)


class DependentItemType(Enum):
    """Types of items that can depend on facts."""
    RISK = "risk"
    WORK_ITEM = "work_item"
    INVENTORY_ITEM = "inventory_item"
    ASSUMPTION = "assumption"
    RECOMMENDATION = "recommendation"


class StaleReason(Enum):
    """Reasons why an item might be stale."""
    FACT_UPDATED = "fact_updated"
    FACT_REMOVED = "fact_removed"
    FACT_CONFLICT = "fact_conflict"
    VERIFICATION_CHANGED = "verification_changed"


@dataclass
class Dependency:
    """A dependency between a fact and an item."""
    fact_id: str
    item_type: DependentItemType
    item_id: str
    relationship: str = "supports"  # supports, contradicts, informs
    strength: float = 1.0  # How strongly this fact supports the item
    created_at: str = ""
    created_by: str = "auto"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "item_type": self.item_type.value,
            "item_id": self.item_id,
            "relationship": self.relationship,
            "strength": self.strength,
            "created_at": self.created_at,
            "created_by": self.created_by
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dependency':
        data = data.copy()
        if 'item_type' in data and isinstance(data['item_type'], str):
            data['item_type'] = DependentItemType(data['item_type'])
        return cls(**data)


@dataclass
class StaleItem:
    """An item that has been flagged as potentially stale."""
    item_type: DependentItemType
    item_id: str
    reason: StaleReason
    changed_fact_ids: List[str] = field(default_factory=list)
    flagged_at: str = ""
    reviewed: bool = False
    reviewed_at: str = ""
    reviewed_by: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_type": self.item_type.value,
            "item_id": self.item_id,
            "reason": self.reason.value,
            "changed_fact_ids": self.changed_fact_ids,
            "flagged_at": self.flagged_at,
            "reviewed": self.reviewed,
            "reviewed_at": self.reviewed_at,
            "reviewed_by": self.reviewed_by,
            "notes": self.notes
        }


class DependencyTracker:
    """
    Tracks dependencies between facts and other items.

    Features:
    - Register dependencies when items are created
    - Query what depends on a fact
    - Flag stale items when facts change
    - Track review status of stale items
    """

    def __init__(self):
        # fact_id -> list of dependencies
        self._by_fact: Dict[str, List[Dependency]] = {}

        # (item_type, item_id) -> list of dependencies
        self._by_item: Dict[Tuple[str, str], List[Dependency]] = {}

        # Stale items pending review
        self._stale_items: Dict[str, StaleItem] = {}  # "type:id" -> StaleItem

    def register_dependency(
        self,
        fact_id: str,
        item_type: DependentItemType,
        item_id: str,
        relationship: str = "supports",
        strength: float = 1.0,
        created_by: str = "auto"
    ) -> Dependency:
        """
        Register a dependency between a fact and an item.

        Args:
            fact_id: The fact ID that supports this item
            item_type: Type of dependent item
            item_id: ID of the dependent item
            relationship: How the fact relates (supports, contradicts, informs)
            strength: How strongly this dependency holds (0-1)
            created_by: Who/what created this dependency

        Returns:
            The created Dependency
        """
        dep = Dependency(
            fact_id=fact_id,
            item_type=item_type,
            item_id=item_id,
            relationship=relationship,
            strength=strength,
            created_at=datetime.now().isoformat(),
            created_by=created_by
        )

        # Index by fact
        if fact_id not in self._by_fact:
            self._by_fact[fact_id] = []
        self._by_fact[fact_id].append(dep)

        # Index by item
        key = (item_type.value, item_id)
        if key not in self._by_item:
            self._by_item[key] = []
        self._by_item[key].append(dep)

        logger.debug(f"Registered dependency: {fact_id} -> {item_type.value}:{item_id}")
        return dep

    def get_dependents(self, fact_id: str) -> List[Dependency]:
        """Get all items that depend on a fact."""
        return self._by_fact.get(fact_id, [])

    def get_dependencies(
        self,
        item_type: DependentItemType,
        item_id: str
    ) -> List[Dependency]:
        """Get all facts that an item depends on."""
        key = (item_type.value, item_id)
        return self._by_item.get(key, [])

    def get_affected_items(self, fact_ids: List[str]) -> Dict[str, List[str]]:
        """
        Get all items affected by changes to given facts.

        Args:
            fact_ids: List of fact IDs that changed

        Returns:
            Dict mapping item_type to list of item_ids
        """
        affected: Dict[str, Set[str]] = {}

        for fact_id in fact_ids:
            for dep in self._by_fact.get(fact_id, []):
                item_type = dep.item_type.value
                if item_type not in affected:
                    affected[item_type] = set()
                affected[item_type].add(dep.item_id)

        return {k: list(v) for k, v in affected.items()}

    def flag_stale(
        self,
        item_type: DependentItemType,
        item_id: str,
        reason: StaleReason,
        changed_fact_ids: List[str]
    ) -> StaleItem:
        """
        Flag an item as potentially stale due to fact changes.

        Args:
            item_type: Type of the stale item
            item_id: ID of the stale item
            reason: Why it's stale
            changed_fact_ids: Which facts triggered this

        Returns:
            The StaleItem record
        """
        key = f"{item_type.value}:{item_id}"

        # Update existing or create new
        if key in self._stale_items:
            stale = self._stale_items[key]
            # Add new fact IDs
            for fid in changed_fact_ids:
                if fid not in stale.changed_fact_ids:
                    stale.changed_fact_ids.append(fid)
        else:
            stale = StaleItem(
                item_type=item_type,
                item_id=item_id,
                reason=reason,
                changed_fact_ids=changed_fact_ids,
                flagged_at=datetime.now().isoformat()
            )
            self._stale_items[key] = stale

        logger.info(f"Flagged stale: {key} due to {reason.value}")
        return stale

    def flag_affected_by_fact_change(
        self,
        fact_id: str,
        reason: StaleReason = StaleReason.FACT_UPDATED
    ) -> List[StaleItem]:
        """
        Flag all items affected by a change to a specific fact.

        Args:
            fact_id: The fact that changed
            reason: Why it changed

        Returns:
            List of flagged StaleItems
        """
        flagged = []
        for dep in self._by_fact.get(fact_id, []):
            stale = self.flag_stale(
                dep.item_type,
                dep.item_id,
                reason,
                [fact_id]
            )
            flagged.append(stale)
        return flagged

    def mark_reviewed(
        self,
        item_type: DependentItemType,
        item_id: str,
        reviewed_by: str,
        notes: str = ""
    ) -> bool:
        """
        Mark a stale item as reviewed.

        Args:
            item_type: Type of the item
            item_id: ID of the item
            reviewed_by: Who reviewed it
            notes: Optional notes

        Returns:
            True if item was found and marked
        """
        key = f"{item_type.value}:{item_id}"
        if key not in self._stale_items:
            return False

        stale = self._stale_items[key]
        stale.reviewed = True
        stale.reviewed_at = datetime.now().isoformat()
        stale.reviewed_by = reviewed_by
        stale.notes = notes

        logger.info(f"Marked reviewed: {key}")
        return True

    def clear_stale_flag(
        self,
        item_type: DependentItemType,
        item_id: str
    ) -> bool:
        """Remove stale flag from an item."""
        key = f"{item_type.value}:{item_id}"
        if key in self._stale_items:
            del self._stale_items[key]
            return True
        return False

    def get_stale_items(
        self,
        item_type: DependentItemType = None,
        include_reviewed: bool = False
    ) -> List[StaleItem]:
        """
        Get all stale items.

        Args:
            item_type: Filter by type (optional)
            include_reviewed: Include already reviewed items

        Returns:
            List of StaleItems
        """
        items = list(self._stale_items.values())

        if item_type:
            items = [i for i in items if i.item_type == item_type]

        if not include_reviewed:
            items = [i for i in items if not i.reviewed]

        return items

    def get_stale_risks(self) -> List[StaleItem]:
        """Get risks that need review due to fact changes."""
        return self.get_stale_items(DependentItemType.RISK)

    def get_stale_work_items(self) -> List[StaleItem]:
        """Get work items that need review due to fact changes."""
        return self.get_stale_items(DependentItemType.WORK_ITEM)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about dependencies and stale items."""
        stale = list(self._stale_items.values())
        return {
            "total_dependencies": sum(len(deps) for deps in self._by_fact.values()),
            "facts_with_dependents": len(self._by_fact),
            "items_with_dependencies": len(self._by_item),
            "stale_items": len([s for s in stale if not s.reviewed]),
            "reviewed_items": len([s for s in stale if s.reviewed]),
            "stale_by_type": {
                t.value: len([s for s in stale if s.item_type == t and not s.reviewed])
                for t in DependentItemType
            }
        }

    def remove_dependency(
        self,
        fact_id: str,
        item_type: DependentItemType,
        item_id: str
    ) -> bool:
        """Remove a specific dependency."""
        # Remove from fact index
        if fact_id in self._by_fact:
            self._by_fact[fact_id] = [
                d for d in self._by_fact[fact_id]
                if not (d.item_type == item_type and d.item_id == item_id)
            ]

        # Remove from item index
        key = (item_type.value, item_id)
        if key in self._by_item:
            self._by_item[key] = [
                d for d in self._by_item[key]
                if d.fact_id != fact_id
            ]

        return True

    def export_to_dict(self) -> Dict[str, Any]:
        """Export tracker state for serialization."""
        return {
            "dependencies": [
                dep.to_dict()
                for deps in self._by_fact.values()
                for dep in deps
            ],
            "stale_items": [s.to_dict() for s in self._stale_items.values()]
        }

    def import_from_dict(self, data: Dict[str, Any]) -> None:
        """Import tracker state from dict."""
        self._by_fact = {}
        self._by_item = {}
        self._stale_items = {}

        for dep_data in data.get("dependencies", []):
            dep = Dependency.from_dict(dep_data)

            if dep.fact_id not in self._by_fact:
                self._by_fact[dep.fact_id] = []
            self._by_fact[dep.fact_id].append(dep)

            key = (dep.item_type.value, dep.item_id)
            if key not in self._by_item:
                self._by_item[key] = []
            self._by_item[key].append(dep)

        for stale_data in data.get("stale_items", []):
            item_type = DependentItemType(stale_data["item_type"])
            reason = StaleReason(stale_data["reason"])
            stale = StaleItem(
                item_type=item_type,
                item_id=stale_data["item_id"],
                reason=reason,
                changed_fact_ids=stale_data.get("changed_fact_ids", []),
                flagged_at=stale_data.get("flagged_at", ""),
                reviewed=stale_data.get("reviewed", False),
                reviewed_at=stale_data.get("reviewed_at", ""),
                reviewed_by=stale_data.get("reviewed_by", ""),
                notes=stale_data.get("notes", "")
            )
            key = f"{item_type.value}:{stale.item_id}"
            self._stale_items[key] = stale


def auto_detect_dependencies(fact_store, dependency_tracker: DependencyTracker):
    """
    Auto-detect dependencies based on fact content.

    Scans facts for references to risks, work items, etc.
    """
    if not fact_store:
        return

    for fact in fact_store.facts:
        # Check if fact mentions risk indicators
        item_lower = fact.item.lower()
        details_str = str(fact.details).lower()

        # Security-related facts often support security risks
        if fact.domain == "security":
            dependency_tracker.register_dependency(
                fact_id=fact.fact_id,
                item_type=DependentItemType.RISK,
                item_id="security_risks",
                relationship="informs",
                created_by="auto_detect"
            )

        # Compliance facts support compliance risks
        if fact.domain == "compliance":
            dependency_tracker.register_dependency(
                fact_id=fact.fact_id,
                item_type=DependentItemType.RISK,
                item_id="compliance_risks",
                relationship="informs",
                created_by="auto_detect"
            )

        # Infrastructure facts inform infrastructure work items
        if fact.domain == "infrastructure":
            dependency_tracker.register_dependency(
                fact_id=fact.fact_id,
                item_type=DependentItemType.INVENTORY_ITEM,
                item_id="infrastructure_inventory",
                relationship="supports",
                created_by="auto_detect"
            )

    logger.info(f"Auto-detected {dependency_tracker.get_stats()['total_dependencies']} dependencies")
