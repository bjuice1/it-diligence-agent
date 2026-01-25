"""
Inventory Updater for Propagating Fact Changes

When facts change, this module updates related inventories and flags
items that may need review.

Phase 4 Steps 92-105
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum

from tools_v2.dependency_tracker import (
    DependencyTracker, DependentItemType, StaleReason
)

logger = logging.getLogger(__name__)


class UpdateAction(Enum):
    """Actions taken during inventory update."""
    ADDED = "added"
    UPDATED = "updated"
    FLAGGED = "flagged"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


@dataclass
class InventoryUpdateResult:
    """Result of an inventory update operation."""
    domain: str
    items_added: int = 0
    items_updated: int = 0
    items_flagged: int = 0
    items_removed: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "items_added": self.items_added,
            "items_updated": self.items_updated,
            "items_flagged": self.items_flagged,
            "items_removed": self.items_removed,
            "total_changes": self.items_added + self.items_updated + self.items_flagged,
            "details": self.details
        }


@dataclass
class PropagationResult:
    """Result of propagating fact changes through the system."""
    facts_processed: int = 0
    inventory_updates: List[InventoryUpdateResult] = field(default_factory=list)
    risks_flagged: int = 0
    work_items_flagged: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "facts_processed": self.facts_processed,
            "inventory_updates": [u.to_dict() for u in self.inventory_updates],
            "risks_flagged": self.risks_flagged,
            "work_items_flagged": self.work_items_flagged,
            "errors": self.errors,
            "total_items_affected": sum(
                u.items_added + u.items_updated + u.items_flagged
                for u in self.inventory_updates
            ) + self.risks_flagged + self.work_items_flagged
        }


class InventoryUpdater:
    """
    Updates inventories when facts change.

    Features:
    - Update applications inventory from application facts
    - Update infrastructure inventory from infrastructure facts
    - Update security inventory from security facts
    - Flag risks when supporting facts change
    - Flag work items when underlying assumptions change
    """

    def __init__(
        self,
        fact_store=None,
        dependency_tracker: DependencyTracker = None,
        session=None
    ):
        self.fact_store = fact_store
        self.dependency_tracker = dependency_tracker or DependencyTracker()
        self.session = session

    def propagate_changes(
        self,
        changed_fact_ids: List[str],
        change_type: str = "updated"
    ) -> PropagationResult:
        """
        Propagate fact changes through the system.

        Args:
            changed_fact_ids: List of fact IDs that changed
            change_type: Type of change (added, updated, removed)

        Returns:
            PropagationResult with details of what was affected
        """
        result = PropagationResult(facts_processed=len(changed_fact_ids))

        # Group facts by domain
        facts_by_domain: Dict[str, List] = {}
        for fact_id in changed_fact_ids:
            if self.fact_store:
                fact = self.fact_store.get_fact(fact_id)
                if fact:
                    domain = fact.domain
                    if domain not in facts_by_domain:
                        facts_by_domain[domain] = []
                    facts_by_domain[domain].append(fact)

        # Update each domain's inventory
        for domain, facts in facts_by_domain.items():
            try:
                if domain == "applications":
                    update_result = self._update_applications_inventory(facts)
                elif domain == "infrastructure":
                    update_result = self._update_infrastructure_inventory(facts)
                elif domain == "security":
                    update_result = self._update_security_inventory(facts)
                else:
                    update_result = self._update_generic_inventory(domain, facts)

                result.inventory_updates.append(update_result)

            except Exception as e:
                error_msg = f"Failed to update {domain} inventory: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        # Flag dependent risks
        result.risks_flagged = self._flag_affected_risks(changed_fact_ids, change_type)

        # Flag dependent work items
        result.work_items_flagged = self._flag_affected_work_items(changed_fact_ids, change_type)

        logger.info(f"Propagated changes for {len(changed_fact_ids)} facts: "
                   f"{result.to_dict()['total_items_affected']} items affected")

        return result

    def _update_applications_inventory(self, facts: List) -> InventoryUpdateResult:
        """Update applications inventory from application facts."""
        result = InventoryUpdateResult(domain="applications")

        if not self.session or not hasattr(self.session, 'applications_store'):
            return result

        store = self.session.applications_store

        for fact in facts:
            # Try to find matching application
            app_name = fact.item
            existing_app = None

            for app in store.applications:
                if app.name.lower() == app_name.lower():
                    existing_app = app
                    break

            if existing_app:
                # Update existing application
                self._update_application_from_fact(existing_app, fact)
                result.items_updated += 1
                result.details.append({
                    "action": "updated",
                    "item": app_name,
                    "fact_id": fact.fact_id
                })

                # Register dependency
                self.dependency_tracker.register_dependency(
                    fact_id=fact.fact_id,
                    item_type=DependentItemType.INVENTORY_ITEM,
                    item_id=existing_app.name
                )
            else:
                # Flag as potential new application
                result.items_flagged += 1
                result.details.append({
                    "action": "flagged_new",
                    "item": app_name,
                    "fact_id": fact.fact_id
                })

        return result

    def _update_application_from_fact(self, app, fact):
        """Update an application item from a fact."""
        # Update fields based on fact details
        if fact.details:
            if "vendor" in fact.details:
                app.vendor = fact.details["vendor"]
            if "version" in fact.details:
                app.version = fact.details["version"]
            if "users" in fact.details:
                app.user_count = fact.details["users"]
            if "criticality" in fact.details:
                app.criticality = fact.details["criticality"]

        # Mark as needing review
        if hasattr(app, 'needs_review'):
            app.needs_review = True

    def _update_infrastructure_inventory(self, facts: List) -> InventoryUpdateResult:
        """Update infrastructure inventory from infrastructure facts."""
        result = InventoryUpdateResult(domain="infrastructure")

        if not self.session or not hasattr(self.session, 'infrastructure_store'):
            return result

        store = self.session.infrastructure_store

        for fact in facts:
            # Try to find matching infrastructure item
            item_name = fact.item
            existing_item = None

            for item in store.items:
                if item.name.lower() == item_name.lower():
                    existing_item = item
                    break

            if existing_item:
                # Update existing item
                self._update_infrastructure_from_fact(existing_item, fact)
                result.items_updated += 1
                result.details.append({
                    "action": "updated",
                    "item": item_name,
                    "fact_id": fact.fact_id
                })

                # Register dependency
                self.dependency_tracker.register_dependency(
                    fact_id=fact.fact_id,
                    item_type=DependentItemType.INVENTORY_ITEM,
                    item_id=existing_item.name
                )
            else:
                result.items_flagged += 1
                result.details.append({
                    "action": "flagged_new",
                    "item": item_name,
                    "fact_id": fact.fact_id
                })

        return result

    def _update_infrastructure_from_fact(self, item, fact):
        """Update an infrastructure item from a fact."""
        if fact.details:
            if "location" in fact.details:
                item.location = fact.details["location"]
            if "vendor" in fact.details:
                item.vendor = fact.details["vendor"]
            if "quantity" in fact.details:
                item.quantity = fact.details["quantity"]

        if hasattr(item, 'needs_review'):
            item.needs_review = True

    def _update_security_inventory(self, facts: List) -> InventoryUpdateResult:
        """Update security inventory from security facts."""
        result = InventoryUpdateResult(domain="security")

        # Security facts are particularly important - flag for review
        for fact in facts:
            result.items_flagged += 1
            result.details.append({
                "action": "flagged_review",
                "item": fact.item,
                "fact_id": fact.fact_id,
                "category": fact.category
            })

            # Always flag security changes as affecting risks
            self.dependency_tracker.flag_stale(
                item_type=DependentItemType.RISK,
                item_id=f"security_{fact.category}",
                reason=StaleReason.FACT_UPDATED,
                changed_fact_ids=[fact.fact_id]
            )

        return result

    def _update_generic_inventory(self, domain: str, facts: List) -> InventoryUpdateResult:
        """Generic update for domains without specific handling."""
        result = InventoryUpdateResult(domain=domain)

        for fact in facts:
            result.items_flagged += 1
            result.details.append({
                "action": "flagged",
                "item": fact.item,
                "fact_id": fact.fact_id
            })

        return result

    def _flag_affected_risks(self, fact_ids: List[str], change_type: str) -> int:
        """Flag risks that depend on changed facts."""
        flagged = 0

        for fact_id in fact_ids:
            # Get items that depend on this fact
            dependents = self.dependency_tracker.get_dependents(fact_id)

            for dep in dependents:
                if dep.item_type == DependentItemType.RISK:
                    reason = StaleReason.FACT_UPDATED
                    if change_type == "removed":
                        reason = StaleReason.FACT_REMOVED

                    self.dependency_tracker.flag_stale(
                        item_type=DependentItemType.RISK,
                        item_id=dep.item_id,
                        reason=reason,
                        changed_fact_ids=[fact_id]
                    )
                    flagged += 1

        return flagged

    def _flag_affected_work_items(self, fact_ids: List[str], change_type: str) -> int:
        """Flag work items that depend on changed facts."""
        flagged = 0

        for fact_id in fact_ids:
            dependents = self.dependency_tracker.get_dependents(fact_id)

            for dep in dependents:
                if dep.item_type == DependentItemType.WORK_ITEM:
                    reason = StaleReason.FACT_UPDATED
                    if change_type == "removed":
                        reason = StaleReason.FACT_REMOVED

                    self.dependency_tracker.flag_stale(
                        item_type=DependentItemType.WORK_ITEM,
                        item_id=dep.item_id,
                        reason=reason,
                        changed_fact_ids=[fact_id]
                    )
                    flagged += 1

        return flagged

    def get_stale_dashboard(self) -> Dict[str, Any]:
        """Get dashboard data for stale items."""
        return {
            "risks": [
                s.to_dict()
                for s in self.dependency_tracker.get_stale_risks()
            ],
            "work_items": [
                s.to_dict()
                for s in self.dependency_tracker.get_stale_work_items()
            ],
            "inventory": [
                s.to_dict()
                for s in self.dependency_tracker.get_stale_items(
                    DependentItemType.INVENTORY_ITEM
                )
            ],
            "stats": self.dependency_tracker.get_stats()
        }

    def bulk_revalidate(
        self,
        item_type: DependentItemType,
        reviewer: str,
        notes: str = "Bulk revalidation"
    ) -> int:
        """
        Bulk mark items as reviewed.

        Args:
            item_type: Type of items to revalidate
            reviewer: Who is doing the review
            notes: Notes about the review

        Returns:
            Number of items revalidated
        """
        items = self.dependency_tracker.get_stale_items(item_type)
        count = 0

        for item in items:
            self.dependency_tracker.mark_reviewed(
                item_type=item.item_type,
                item_id=item.item_id,
                reviewed_by=reviewer,
                notes=notes
            )
            count += 1

        logger.info(f"Bulk revalidated {count} {item_type.value} items")
        return count

    def clear_all_stale_flags(self, item_type: DependentItemType = None) -> int:
        """Clear stale flags after review."""
        items = self.dependency_tracker.get_stale_items(item_type, include_reviewed=True)
        count = 0

        for item in items:
            if item.reviewed:
                self.dependency_tracker.clear_stale_flag(
                    item_type=item.item_type,
                    item_id=item.item_id
                )
                count += 1

        logger.info(f"Cleared {count} stale flags")
        return count
