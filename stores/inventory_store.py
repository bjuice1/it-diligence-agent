"""
InventoryStore - Central Storage for Inventory Items

Stores structured inventory data (applications, infrastructure, organization, vendors)
separately from observational facts.

Key Features:
- Content-based IDs for stability across re-imports
- CRUD operations with change tracking
- Query by type, entity, status, enrichment
- Merge/re-import with smart conflict resolution
- JSON persistence
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict

from stores.inventory_item import InventoryItem, MergeResult
from stores.id_generator import generate_inventory_id
from stores.inventory_schemas import (
    validate_inventory_type,
    get_required_fields,
    INVENTORY_SCHEMAS,
)

logger = logging.getLogger(__name__)


class InventoryStore:
    """
    Central storage for inventory items.

    Provides:
    - CRUD operations (add, get, update, remove)
    - Query methods (by type, entity, status, enrichment)
    - Aggregation (count, sum_costs, summary)
    - Persistence (save/load JSON)
    - Merge capabilities for re-imports
    """

    def __init__(self, deal_id: str = None, storage_path: Optional[Path] = None):
        """
        Initialize InventoryStore.

        Args:
            deal_id: Deal ID for scoping. Required for proper data isolation.
            storage_path: Optional path for persistence. If provided,
                         will attempt to load existing data. If deal_id is
                         provided without storage_path, path is auto-generated.
        """
        self.deal_id = deal_id
        self._items: Dict[str, InventoryItem] = {}
        self._lock = threading.Lock()

        # Auto-generate storage path if deal_id provided but no path
        if deal_id and not storage_path:
            try:
                from config_v2 import OUTPUT_DIR
                storage_path = OUTPUT_DIR / "deals" / deal_id / "inventory_store.json"
            except ImportError:
                storage_path = Path("output") / "deals" / deal_id / "inventory_store.json"

        self.storage_path = storage_path

        # Load existing data if path provided and file exists
        if storage_path and storage_path.exists():
            self.load_from_file(storage_path)

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def add_item(
        self,
        inventory_type: str,
        data: Dict[str, Any],
        entity: str = "target",
        deal_id: str = None,
        source_file: str = "",
        source_type: str = "import"
    ) -> str:
        """
        Add a new inventory item.

        Args:
            inventory_type: application, infrastructure, organization, vendor
            data: Item data (name, vendor, version, etc.)
            entity: "target" or "buyer"
            deal_id: Deal ID (uses store's deal_id if not provided)
            source_file: Source filename
            source_type: "import", "manual", or "discovery"

        Returns:
            The item_id of the created/existing item

        Raises:
            ValueError: If deal_id is not provided and store has no deal_id

        Note:
            If an item with the same content-based ID already exists,
            returns the existing ID without creating a duplicate.
        """
        # Resolve deal_id
        effective_deal_id = deal_id or self.deal_id
        if not effective_deal_id:
            raise ValueError(
                "deal_id is required - provide in add_item() or store constructor"
            )

        # Validate
        if not validate_inventory_type(inventory_type):
            raise ValueError(f"Invalid inventory type: {inventory_type}")

        # Check required fields
        required = get_required_fields(inventory_type)
        missing = [f for f in required if not data.get(f)]
        if missing:
            logger.warning(
                f"Missing required fields for {inventory_type}: {missing}. "
                f"Item will be created but may have issues."
            )

        # Generate content-based ID (now includes deal_id for cross-deal uniqueness)
        item_id = generate_inventory_id(inventory_type, data, entity, effective_deal_id)

        with self._lock:
            # Check if already exists
            if item_id in self._items:
                existing = self._items[item_id]
                if existing.status == "removed":
                    # Restore removed item with new data
                    existing.restore()
                    existing.update(data, modified_by="re-import")
                    logger.info(f"Restored previously removed item: {item_id}")
                else:
                    logger.debug(f"Item already exists: {item_id}")
                return item_id

            # Create new item with deal_id
            item = InventoryItem(
                item_id=item_id,
                inventory_type=inventory_type,
                entity=entity,
                deal_id=effective_deal_id,
                data=data,
                source_file=source_file,
                source_type=source_type,
            )

            self._items[item_id] = item
            logger.debug(f"Added inventory item: {item_id} ({item.name}) for deal {effective_deal_id}")

        return item_id

    def get_item(self, item_id: str) -> Optional[InventoryItem]:
        """
        Get an item by ID.

        Args:
            item_id: The item ID (e.g., "I-APP-a3f291")

        Returns:
            InventoryItem or None if not found
        """
        return self._items.get(item_id)

    def update_item(
        self,
        item_id: str,
        updates: Dict[str, Any],
        modified_by: str = ""
    ) -> bool:
        """
        Update an existing item's data.

        Args:
            item_id: The item to update
            updates: Dict of field updates
            modified_by: Who made this change

        Returns:
            True if updated, False if item not found
        """
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                logger.warning(f"Cannot update - item not found: {item_id}")
                return False

            item.update(updates, modified_by)
            logger.debug(f"Updated item: {item_id}")
            return True

    def remove_item(
        self,
        item_id: str,
        reason: str,
        removed_by: str = ""
    ) -> bool:
        """
        Mark an item as removed (soft delete).

        Args:
            item_id: The item to remove
            reason: Why it's being removed
            removed_by: Who removed it

        Returns:
            True if removed, False if item not found
        """
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                logger.warning(f"Cannot remove - item not found: {item_id}")
                return False

            item.remove(reason, removed_by)
            logger.info(f"Removed item: {item_id} - {reason}")
            return True

    def restore_item(self, item_id: str) -> bool:
        """
        Restore a removed item.

        Returns:
            True if restored, False if item not found or not removed
        """
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                return False
            if item.status != "removed":
                return False

            item.restore()
            logger.info(f"Restored item: {item_id}")
            return True

    def exists(self, item_id: str) -> bool:
        """Check if an item exists (any status)."""
        return item_id in self._items

    def exists_active(self, item_id: str) -> bool:
        """Check if an active item exists."""
        item = self._items.get(item_id)
        return item is not None and item.is_active

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_items(
        self,
        inventory_type: Optional[str] = None,
        entity: Optional[str] = None,
        deal_id: Optional[str] = None,
        status: str = "active"
    ) -> List[InventoryItem]:
        """
        Get items matching criteria.

        Args:
            inventory_type: Filter by type (None = all types)
            entity: Filter by entity (None = all entities)
            deal_id: Filter by deal (uses store's deal_id if not provided)
            status: Filter by status ("active", "removed", "all")

        Returns:
            List of matching InventoryItems
        """
        # Use store's deal_id if not explicitly provided
        effective_deal_id = deal_id or self.deal_id

        results = []

        for item in self._items.values():
            # Filter by deal_id FIRST (most important for isolation)
            if effective_deal_id and item.deal_id and item.deal_id != effective_deal_id:
                continue

            # Filter by status
            if status != "all" and item.status != status:
                continue

            # Filter by type
            if inventory_type and item.inventory_type != inventory_type:
                continue

            # Filter by entity
            if entity and item.entity != entity:
                continue

            results.append(item)

        return results

    def get_items_by_enrichment(
        self,
        category: str,
        inventory_type: Optional[str] = None
    ) -> List[InventoryItem]:
        """
        Get items by enrichment category.

        Args:
            category: industry_standard, vertical_specific, niche, unknown, custom
            inventory_type: Optional filter by inventory type

        Returns:
            List of matching active items
        """
        results = []

        for item in self._items.values():
            if not item.is_active:
                continue
            if inventory_type and item.inventory_type != inventory_type:
                continue
            if item.enrichment_category == category:
                results.append(item)

        return results

    def get_flagged_items(self, flag: str = "investigate") -> List[InventoryItem]:
        """Get items with a specific enrichment flag."""
        results = []

        for item in self._items.values():
            if item.is_active and item.enrichment.get("flag") == flag:
                results.append(item)

        return results

    def find_by_name(
        self,
        name: str,
        inventory_type: Optional[str] = None,
        exact: bool = False
    ) -> Optional[InventoryItem]:
        """
        Find an item by name.

        Args:
            name: Name to search for
            inventory_type: Optional type filter
            exact: If True, require exact match. If False, case-insensitive contains.

        Returns:
            First matching item or None
        """
        name_lower = name.lower().strip()

        for item in self._items.values():
            if not item.is_active:
                continue
            if inventory_type and item.inventory_type != inventory_type:
                continue

            item_name = item.name.lower()
            if exact:
                if item_name == name_lower:
                    return item
            else:
                if name_lower in item_name or item_name in name_lower:
                    return item

        return None

    def search(
        self,
        query: str,
        inventory_type: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> List[InventoryItem]:
        """
        Search items by text query.

        Args:
            query: Search text
            inventory_type: Optional type filter
            fields: Fields to search in (default: name, vendor, notes)

        Returns:
            List of matching active items
        """
        if fields is None:
            fields = ["name", "vendor", "vendor_name", "notes", "role"]

        query_lower = query.lower()
        results = []

        for item in self._items.values():
            if not item.is_active:
                continue
            if inventory_type and item.inventory_type != inventory_type:
                continue

            # Search in specified fields
            for field in fields:
                value = item.data.get(field, "")
                if value and query_lower in str(value).lower():
                    results.append(item)
                    break

        return results

    # =========================================================================
    # Aggregation Methods
    # =========================================================================

    def count(
        self,
        inventory_type: Optional[str] = None,
        entity: Optional[str] = None,
        status: str = "active"
    ) -> int:
        """Count items matching criteria."""
        return len(self.get_items(inventory_type=inventory_type, entity=entity, status=status))

    def sum_costs(
        self,
        inventory_type: Optional[str] = None,
        entity: Optional[str] = None
    ) -> float:
        """Sum costs of matching active items."""
        total = 0.0
        for item in self.get_items(inventory_type=inventory_type, entity=entity, status="active"):
            cost = item.cost
            if cost is not None:
                total += cost
        return total

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics.

        Returns:
            Dict with counts, costs, and enrichment breakdown
        """
        summary = {
            "total_items": 0,
            "active_items": 0,
            "removed_items": 0,
            "by_type": {},
            "by_entity": {"target": 0, "buyer": 0},
            "total_cost": 0.0,
            "enrichment_breakdown": defaultdict(int),
            "flagged_for_investigation": 0,
        }

        for item in self._items.values():
            summary["total_items"] += 1

            if item.is_active:
                summary["active_items"] += 1
                summary["by_entity"][item.entity] = summary["by_entity"].get(item.entity, 0) + 1

                # By type
                if item.inventory_type not in summary["by_type"]:
                    summary["by_type"][item.inventory_type] = {
                        "count": 0,
                        "cost": 0.0,
                    }
                summary["by_type"][item.inventory_type]["count"] += 1

                # Cost
                cost = item.cost
                if cost:
                    summary["total_cost"] += cost
                    summary["by_type"][item.inventory_type]["cost"] += cost

                # Enrichment
                if item.enrichment_category:
                    summary["enrichment_breakdown"][item.enrichment_category] += 1

                # Flagged
                if item.needs_investigation:
                    summary["flagged_for_investigation"] += 1
            else:
                summary["removed_items"] += 1

        # Convert defaultdict to regular dict
        summary["enrichment_breakdown"] = dict(summary["enrichment_breakdown"])

        return summary

    # =========================================================================
    # Persistence
    # =========================================================================

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save store to JSON file.

        Args:
            path: Path to save to. Uses storage_path if not provided.
        """
        from datetime import datetime

        save_path = path or self.storage_path
        if not save_path:
            raise ValueError("No save path provided and no storage_path set")

        save_path = Path(save_path)

        with self._lock:
            data = {
                "schema_version": "2.0",  # Updated for deal_id support
                "deal_id": self.deal_id or "",
                "created_at": datetime.now().isoformat(),
                "item_count": len(self._items),
                "items": {
                    item_id: item.to_dict()
                    for item_id, item in self._items.items()
                },
                "summary": self.get_summary(),
            }

        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(self._items)} inventory items to {save_path} (deal: {self.deal_id})")

    def load_from_file(self, path: Path) -> None:
        """
        Load store from JSON file (instance method).

        Args:
            path: Path to load from
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Inventory file not found: {path}")

        with open(path, 'r') as f:
            data = json.load(f)

        # Update deal_id from loaded data if not already set
        if not self.deal_id:
            self.deal_id = data.get("deal_id", "")

        with self._lock:
            self._items.clear()

            items_data = data.get("items", {})
            for item_id, item_dict in items_data.items():
                try:
                    item = InventoryItem.from_dict(item_dict)
                    self._items[item_id] = item
                except Exception as e:
                    logger.error(f"Failed to load item {item_id}: {e}")

        logger.info(f"Loaded {len(self._items)} inventory items from {path}")

    @classmethod
    def load(cls, path: Path, deal_id: str = None) -> "InventoryStore":
        """
        Load store from JSON file (classmethod).

        Args:
            path: Path to load from
            deal_id: Optional deal_id to use (overrides file's deal_id)

        Returns:
            Loaded InventoryStore instance
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Inventory file not found: {path}")

        with open(path, 'r') as f:
            data = json.load(f)

        # Get deal_id from argument, or from file data
        effective_deal_id = deal_id or data.get("deal_id", "")

        # Pass storage_path=None to prevent __init__ from trying to auto-load (avoids recursion)
        store = cls(deal_id=effective_deal_id, storage_path=None)

        items_data = data.get("items", {})
        for item_id, item_dict in items_data.items():
            try:
                item = InventoryItem.from_dict(item_dict)
                store._items[item_id] = item
            except Exception as e:
                logger.error(f"Failed to load item {item_id}: {e}")

        logger.info(f"Loaded {len(store._items)} inventory items from {path} (deal: {store.deal_id})")
        return store

    def to_dict(self) -> Dict[str, Any]:
        """Export all items as dict (for JSON serialization)."""
        from datetime import datetime
        return {
            "schema_version": "2.0",
            "deal_id": self.deal_id or "",
            "created_at": datetime.now().isoformat(),
            "item_count": len(self._items),
            "items": {
                item_id: item.to_dict()
                for item_id, item in self._items.items()
            },
            "summary": self.get_summary(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], deal_id: str = None) -> "InventoryStore":
        """Create InventoryStore from dict."""
        # Get deal_id from data if not provided
        effective_deal_id = deal_id or data.get("deal_id", "")
        # Pass storage_path=None to prevent auto-load recursion
        store = cls(deal_id=effective_deal_id, storage_path=None)
        items_data = data.get("items", {})
        for item_id, item_dict in items_data.items():
            item = InventoryItem.from_dict(item_dict)
            store._items[item_id] = item
        return store

    # =========================================================================
    # Merge / Re-Import
    # =========================================================================

    def merge_from(
        self,
        other: "InventoryStore",
        strategy: str = "smart"
    ) -> MergeResult:
        """
        Merge items from another store.

        Args:
            other: Source store to merge from
            strategy:
                - "add_new": Only add items not already present
                - "update": Add new, update existing with changed data
                - "smart": Add new, update existing, flag items missing from source

        Returns:
            MergeResult with statistics
        """
        result = MergeResult()

        with self._lock:
            # Track which items were in the source
            source_ids = set(other._items.keys())

            for item_id, source_item in other._items.items():
                existing = self._items.get(item_id)

                if existing is None:
                    # New item
                    self._items[item_id] = InventoryItem.from_dict(source_item.to_dict())
                    result.added += 1

                elif strategy == "add_new":
                    # Skip existing
                    result.unchanged += 1

                elif existing.status == "removed":
                    # Skip items user explicitly removed
                    result.skipped += 1

                else:
                    # Check if data changed
                    if existing.data != source_item.data:
                        existing.update(source_item.data, modified_by="merge")
                        result.updated += 1
                    else:
                        result.unchanged += 1

            # Smart strategy: flag items missing from source
            if strategy == "smart":
                for item_id, item in self._items.items():
                    if item_id not in source_ids:
                        # Item in store but not in source
                        if item.source_type == "import" and item.status == "active":
                            # Imported item missing from source - flag it
                            item.status = "deprecated"
                            item.removal_reason = "Not in updated source file"
                            result.flagged_removed += 1
                        # Manual items are kept (user added them)

        logger.info(f"Merge complete: {result}")
        return result

    def add_from_table(
        self,
        inventory_type: str,
        rows: List[Dict[str, Any]],
        entity: str = "target",
        deal_id: str = None,
        source_file: str = ""
    ) -> MergeResult:
        """
        Add multiple items from parsed table data.

        Convenience method for bulk imports from deterministic parsers.

        Args:
            inventory_type: Type of inventory
            rows: List of row dicts with field data
            entity: target or buyer
            deal_id: Deal ID (uses store's deal_id if not provided)
            source_file: Source filename

        Returns:
            MergeResult with import statistics
        """
        result = MergeResult()

        # Resolve deal_id
        effective_deal_id = deal_id or self.deal_id

        # Track existing IDs before adding
        existing_ids = set(self._items.keys())

        for row in rows:
            try:
                item_id = self.add_item(
                    inventory_type=inventory_type,
                    data=row,
                    entity=entity,
                    deal_id=effective_deal_id,
                    source_file=source_file,
                    source_type="import"
                )

                # Check if it was newly added
                if item_id not in existing_ids:
                    result.added += 1
                    existing_ids.add(item_id)  # Track for duplicates within same batch
                else:
                    result.unchanged += 1

            except Exception as e:
                result.errors.append(f"Failed to add row: {e}")
                logger.error(f"Failed to add inventory row: {e}")

        logger.info(f"Added from table ({inventory_type}): {result}")
        return result

    # =========================================================================
    # Utilities
    # =========================================================================

    def clear(self) -> None:
        """Clear all items (use with caution)."""
        with self._lock:
            self._items.clear()
        logger.warning("Cleared all inventory items")

    def get_all_ids(self, status: str = "active") -> List[str]:
        """Get all item IDs."""
        if status == "all":
            return list(self._items.keys())
        return [
            item_id for item_id, item in self._items.items()
            if item.status == status
        ]

    def __len__(self) -> int:
        """Number of active items."""
        return self.count(status="active")

    def __contains__(self, item_id: str) -> bool:
        """Check if item ID exists."""
        return item_id in self._items

    def __iter__(self):
        """Iterate over active items."""
        return iter(self.get_items(status="active"))
