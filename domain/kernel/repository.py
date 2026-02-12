"""
Repository base class - Shared across ALL domains.

CRITICAL: Applications, Infrastructure, Organization all extend THIS.
Ensures consistent repository interface and fixes P0-2 (O(n²) reconciliation).

Created: 2026-02-12 (Worker 1 - Kernel Foundation, Task-006)
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
import logging

from domain.kernel.entity import Entity

# Type variable for domain aggregate
T = TypeVar('T')

logger = logging.getLogger(__name__)


class DomainRepository(ABC, Generic[T]):
    """
    Base repository - same pattern for Apps, Infra, Org.

    CRITICAL: All domain repositories MUST extend this.
    Provides shared deduplication primitives and query patterns.

    Fixes P0-2: reconcile_duplicates() with circuit breaker (O(n log n), NOT O(n²))
    """

    # Circuit breaker for reconciliation (P0-2 fix)
    MAX_ITEMS_FOR_RECONCILIATION = 500

    @abstractmethod
    def save(self, item: T) -> T:
        """
        Save item to repository (insert or update).

        Args:
            item: Domain aggregate to save

        Returns:
            Saved item (with any generated fields populated)

        Example:
            app = Application(...)
            saved_app = repository.save(app)
        """
        pass

    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        """
        Find item by domain ID.

        Args:
            id: Domain ID (e.g., "APP-TARGET-a3f291c2")

        Returns:
            Item if found, None otherwise

        Example:
            app = repository.find_by_id("APP-TARGET-a3f291c2")
            if app:
                print(f"Found: {app.name}")
        """
        pass

    @abstractmethod
    def find_or_create(
        self,
        name: str,
        entity: Entity,
        **kwargs
    ) -> T:
        """
        Shared deduplication primitive.

        This is THE method that prevents duplicates.

        Strategy:
        1. Normalize name (using kernel.NormalizationRules)
        2. Generate fingerprint (using kernel.FingerprintGenerator)
        3. Check if exists in DB (by fingerprint)
        4. If exists: return existing (optionally merge observations)
        5. If not: create new

        Args:
            name: Raw name (e.g., "Salesforce CRM", "AWS EC2 Production")
            entity: Entity (target or buyer)
            **kwargs: Additional domain-specific fields

        Returns:
            Existing item (if found) or newly created item

        Example:
            # First call: Creates new application
            app1 = repository.find_or_create("Salesforce CRM", Entity.TARGET)
            # app1.id = "APP-TARGET-a3f291c2"

            # Second call: Finds existing application (deduplication!)
            app2 = repository.find_or_create("Salesforce", Entity.TARGET)
            # app2.id = "APP-TARGET-a3f291c2" (same ID!)
            # app1 == app2

        Notes:
            - Normalization happens inside this method
            - Vendor is extracted from kwargs if present (for P0-3 fix)
            - Observations are merged if item exists
        """
        pass

    @abstractmethod
    def find_by_entity(self, entity: Entity) -> List[T]:
        """
        Find all items for entity (target or buyer).

        Args:
            entity: Entity.TARGET or Entity.BUYER

        Returns:
            List of items for that entity

        Example:
            target_apps = repository.find_by_entity(Entity.TARGET)
            buyer_apps = repository.find_by_entity(Entity.BUYER)
        """
        pass

    @abstractmethod
    def find_similar(
        self,
        name: str,
        threshold: float = 0.85,
        limit: int = 5
    ) -> List[T]:
        """
        Find similar items using fuzzy search.

        CRITICAL: Uses database trigram indexes (NOT O(n²)).
        See P0-2 fix - reconciliation must be O(n log n), not O(n²).

        Args:
            name: Name to search for
            threshold: Similarity threshold (0.0-1.0, default 0.85)
            limit: Maximum results to return

        Returns:
            List of similar items (sorted by similarity, descending)

        Example:
            # Find items similar to "Salesforce"
            similar = repository.find_similar("Salesforce", threshold=0.85, limit=5)
            # Returns: ["Salesforce CRM", "Salesforce.com", "Sales Force"]

        Notes:
            - Uses PostgreSQL pg_trgm extension (trigram similarity)
            - Falls back to basic fuzzy matching if pg_trgm unavailable
            - Complexity: O(log n) per query (database index)
        """
        pass

    def reconcile_duplicates(
        self,
        items: List[T],
        threshold: float = 0.85
    ) -> int:
        """
        Shared reconciliation - NEVER inline, always background.

        CRITICAL: Fixes P0-2 (O(n²) reconciliation kills production).

        Strategy:
        1. Check count - if >500 items, skip (circuit breaker)
        2. Use database fuzzy search (O(n log n))
        3. Merge duplicates
        4. Return count of merged items

        NEVER call this in main request path - use Celery background job.

        Args:
            items: List of items to reconcile
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            Number of items merged

        Example:
            # In Celery task (background):
            apps = repository.find_by_entity(Entity.TARGET)
            merged_count = repository.reconcile_duplicates(apps, threshold=0.85)
            logger.info(f"Merged {merged_count} duplicate applications")

        Notes:
            - Circuit breaker at MAX_ITEMS_FOR_RECONCILIATION (500)
            - Uses find_similar() to avoid O(n²) nested loop
            - Logs warning if circuit breaker activates
        """
        # P0-2 fix: Circuit breaker
        if len(items) > self.MAX_ITEMS_FOR_RECONCILIATION:
            logger.warning(
                f"Too many items ({len(items)}) for reconciliation. "
                f"Skipping to avoid O(n²) performance issue. "
                f"Max: {self.MAX_ITEMS_FOR_RECONCILIATION}"
            )
            return 0

        merged_count = 0

        for item in items:
            # P0-2 fix: Use database fuzzy search (O(log n) per query)
            # NOT nested loop (O(n²))
            similar = self.find_similar(
                self._get_item_name(item),
                threshold=threshold,
                limit=5
            )

            for candidate in similar:
                # Skip self
                if self._get_item_id(item) == self._get_item_id(candidate):
                    continue

                # Check if actually duplicate
                if self._is_duplicate(item, candidate, threshold):
                    # Merge candidate into item
                    self._merge_items(item, candidate)
                    merged_count += 1

        if merged_count > 0:
            logger.info(
                f"Reconciliation complete: merged {merged_count} duplicates "
                f"from {len(items)} items"
            )

        return merged_count

    # Helper methods (subclasses implement these)

    @abstractmethod
    def _get_item_name(self, item: T) -> str:
        """Get item name (for similarity search)."""
        pass

    @abstractmethod
    def _get_item_id(self, item: T) -> str:
        """Get item ID (for deduplication check)."""
        pass

    @abstractmethod
    def _is_duplicate(self, item1: T, item2: T, threshold: float) -> bool:
        """Check if two items are duplicates."""
        pass

    @abstractmethod
    def _merge_items(self, target: T, source: T) -> None:
        """Merge source item into target."""
        pass

    # Query methods (concrete implementations can override)

    def count_by_entity(self, entity: Entity) -> int:
        """
        Count items for entity.

        Args:
            entity: Entity.TARGET or Entity.BUYER

        Returns:
            Count of items

        Default implementation:
            return len(self.find_by_entity(entity))

        Subclasses should override with optimized database query.
        """
        return len(self.find_by_entity(entity))

    def find_all(self) -> List[T]:
        """
        Find all items (across both entities).

        Returns:
            List of all items

        Warning: Can be expensive for large datasets.
        """
        target_items = self.find_by_entity(Entity.TARGET)
        buyer_items = self.find_by_entity(Entity.BUYER)
        return target_items + buyer_items

    def delete_by_id(self, id: str) -> bool:
        """
        Delete item by ID.

        Args:
            id: Domain ID

        Returns:
            True if deleted, False if not found

        Note: Default implementation not provided (subclass must implement).
        """
        raise NotImplementedError(
            "delete_by_id() must be implemented by subclass"
        )
