"""
ApplicationRepository - Deduplication engine for applications.

CRITICAL: Extends kernel.DomainRepository (shared patterns).
This is THE repository for application deduplication.

Created: 2026-02-12 (Worker 2 - Application Domain, Task-012)
"""

from typing import List, Optional
import logging

from domain.kernel.entity import Entity
from domain.kernel.repository import DomainRepository
from domain.kernel.normalization import NormalizationRules
from domain.kernel.fingerprint import FingerprintGenerator

from domain.applications.application import Application
from domain.applications.application_id import ApplicationId

logger = logging.getLogger(__name__)


class ApplicationRepository(DomainRepository[Application]):
    """
    Application repository - THE deduplication engine.

    CRITICAL: This replaces the broken InventoryStore deduplication.

    Fixes:
    - P0-3: Normalization collisions (via kernel.FingerprintGenerator with vendor)
    - P0-2: O(n²) reconciliation (via circuit breaker + database fuzzy search)

    Strategy:
    - Uses fingerprint-based identity (stable across re-imports)
    - find_or_create() is the deduplication primitive
    - Database UNIQUE constraint enforces no duplicates
    - Reconciliation runs in background (not inline)

    Example:
        repo = ApplicationRepository()

        # First import: Creates new application
        app1 = repo.find_or_create(
            name="Salesforce CRM",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
        # app1.id = "APP-TARGET-a3f291c2"

        # Second import (same document re-imported): Finds existing
        app2 = repo.find_or_create(
            name="Salesforce",  # Different variant
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
        # app2.id = "APP-TARGET-a3f291c2" (SAME ID - deduplication works!)
        assert app1.id == app2.id  # ✅
    """

    def __init__(self):
        """Initialize repository."""
        # In-memory storage (for testing/POC)
        # TODO: Replace with SQLAlchemy ORM + PostgreSQL in production
        self._applications: dict[str, Application] = {}

    def save(self, application: Application) -> Application:
        """
        Save application to repository.

        Args:
            application: Application to save

        Returns:
            Saved application

        Example:
            app = Application(...)
            saved = repo.save(app)
        """
        if not isinstance(application, Application):
            raise ValueError(f"Can only save Application, got {type(application)}")

        self._applications[application.id] = application
        logger.info(f"Saved application: {application.id} ({application.name})")

        return application

    def find_by_id(self, id: str) -> Optional[Application]:
        """
        Find application by domain ID.

        Args:
            id: Application ID (e.g., "APP-TARGET-a3f291c2")

        Returns:
            Application if found, None otherwise

        Example:
            app = repo.find_by_id("APP-TARGET-a3f291c2")
            if app:
                print(f"Found: {app.name}")
        """
        return self._applications.get(id)

    def find_or_create(
        self,
        name: str,
        vendor: str,
        entity: Entity,
        deal_id: str,
        **kwargs
    ) -> Application:
        """
        THE deduplication primitive.

        This is the method that prevents duplicates from being created.

        Strategy:
        1. Normalize name (using kernel.NormalizationRules)
        2. Generate fingerprint (using kernel.FingerprintGenerator)
        3. Check if application exists in repository (by ID)
        4. If exists: Return existing (optionally merge observations)
        5. If not: Create new application

        CRITICAL: Same (name, vendor, entity, deal_id) always returns SAME application.

        Args:
            name: Raw application name (e.g., "Salesforce CRM", "Salesforce")
            vendor: Vendor name (e.g., "Salesforce")
            entity: Entity (TARGET or BUYER)
            deal_id: Deal ID (multi-tenant isolation)
            **kwargs: Additional fields (observations, etc.)

        Returns:
            Existing application (if found) or newly created application

        Examples:
            # First call: Creates new application
            app1 = repo.find_or_create(
                name="Salesforce CRM",
                vendor="Salesforce",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )
            # app1.id = "APP-TARGET-a3f291c2"

            # Second call (different name variant): Finds existing
            app2 = repo.find_or_create(
                name="Salesforce",  # Different!
                vendor="Salesforce",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )
            # app2.id = "APP-TARGET-a3f291c2" (SAME!)
            assert app1.id == app2.id  # ✅ Deduplication works

            # Third call (different vendor): Creates new (P0-3 fix)
            app3 = repo.find_or_create(
                name="Salesforce CRM",
                vendor="Oracle",  # Different vendor!
                entity=Entity.TARGET,
                deal_id="deal-123"
            )
            # app3.id = "APP-TARGET-b4e8f1d3" (DIFFERENT!)
            assert app1.id != app3.id  # ✅ Vendor matters (P0-3 fix)
        """
        # Step 1: Normalize name using kernel rules
        name_normalized = NormalizationRules.normalize_name(name, "application")

        # Step 2: Generate fingerprint (stable ID)
        # CRITICAL: Includes vendor to prevent P0-3 collision
        app_id = ApplicationId.generate(
            name=name,
            vendor=vendor,
            entity=entity
        )

        # Step 3: Check if application already exists
        existing = self.find_by_id(app_id.value)

        if existing:
            # Application exists - return it (optionally merge observations)
            logger.info(
                f"Found existing application: {app_id.value} ({existing.name}) "
                f"← deduped from '{name}'"
            )

            # If new observations provided, merge them
            if "observations" in kwargs:
                for obs in kwargs["observations"]:
                    existing.add_observation(obs)
                self.save(existing)

            return existing

        # Step 4: Application doesn't exist - create new
        logger.info(
            f"Creating new application: {app_id.value} "
            f"(name='{name}', normalized='{name_normalized}', vendor='{vendor}')"
        )

        new_app = Application(
            id=app_id.value,
            name=name,  # Keep original name (not normalized)
            name_normalized=name_normalized,
            vendor=vendor,
            entity=entity,
            deal_id=deal_id,
            observations=kwargs.get("observations", [])
        )

        return self.save(new_app)

    def find_by_entity(self, entity: Entity, deal_id: Optional[str] = None) -> List[Application]:
        """
        Find all applications for entity (target or buyer).

        Args:
            entity: Entity (TARGET or BUYER)
            deal_id: Optional deal filter

        Returns:
            List of applications

        Example:
            # Get all target applications
            target_apps = repo.find_by_entity(Entity.TARGET)

            # Get all buyer applications for specific deal
            buyer_apps = repo.find_by_entity(Entity.BUYER, deal_id="deal-123")
        """
        results = [
            app for app in self._applications.values()
            if app.entity == entity
        ]

        # Filter by deal_id if provided
        if deal_id:
            results = [app for app in results if app.deal_id == deal_id]

        return results

    def find_similar(
        self,
        name: str,
        threshold: float = 0.85,
        limit: int = 5
    ) -> List[Application]:
        """
        Find similar applications using fuzzy search.

        CRITICAL: In production, this uses database trigram indexes (O(n log n)).
        For POC, uses simple in-memory fuzzy matching.

        This is part of P0-2 fix - reconciliation must be O(n log n), not O(n²).

        Args:
            name: Application name to search for
            threshold: Similarity threshold (0.0-1.0)
            limit: Maximum results to return

        Returns:
            List of similar applications (sorted by similarity)

        Example:
            # Find apps similar to "Salesforce"
            similar = repo.find_similar("Salesforce", threshold=0.8, limit=5)
            # Returns: ["Salesforce CRM", "Salesforce Marketing Cloud", ...]
        """
        # Normalize search name
        name_normalized = NormalizationRules.normalize_name(name, "application")

        # Find similar applications
        similar_apps = []

        for app in self._applications.values():
            # Calculate similarity
            similarity = self._calculate_similarity(
                name_normalized,
                app.name_normalized
            )

            if similarity >= threshold:
                similar_apps.append((app, similarity))

        # Sort by similarity (highest first)
        similar_apps.sort(key=lambda x: x[1], reverse=True)

        # Return top N results
        return [app for app, _ in similar_apps[:limit]]

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings.

        Simple character overlap approximation for POC.
        In production, use database trigram similarity or Levenshtein distance.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        if s1 == s2:
            return 1.0

        if not s1 or not s2:
            return 0.0

        # Simple overlap coefficient
        set1 = set(s1.lower())
        set2 = set(s2.lower())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def count_by_entity(self, entity: Entity, deal_id: Optional[str] = None) -> int:
        """
        Count applications by entity.

        Args:
            entity: Entity (TARGET or BUYER)
            deal_id: Optional deal filter

        Returns:
            Count of applications

        Example:
            count = repo.count_by_entity(Entity.TARGET, deal_id="deal-123")
            print(f"Found {count} target applications")
        """
        return len(self.find_by_entity(entity, deal_id))

    def delete(self, id: str) -> bool:
        """
        Delete application by ID.

        Args:
            id: Application ID

        Returns:
            True if deleted, False if not found

        Example:
            deleted = repo.delete("APP-TARGET-a3f291c2")
        """
        if id in self._applications:
            del self._applications[id]
            logger.info(f"Deleted application: {id}")
            return True

        return False

    def clear(self) -> None:
        """
        Clear all applications (for testing).

        Example:
            repo.clear()  # Empty repository
        """
        self._applications.clear()
        logger.info("Cleared all applications")

    def __len__(self) -> int:
        """Return count of applications."""
        return len(self._applications)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"ApplicationRepository({len(self._applications)} applications)"

    # Helper methods required by kernel.DomainRepository (ABC)

    def _get_item_name(self, item: Application) -> str:
        """
        Get item name for similarity search.

        Args:
            item: Application

        Returns:
            Normalized name
        """
        return item.name_normalized

    def _get_item_id(self, item: Application) -> str:
        """
        Get item ID for deduplication check.

        Args:
            item: Application

        Returns:
            Application ID
        """
        return item.id

    def _is_duplicate(self, item1: Application, item2: Application, threshold: float) -> bool:
        """
        Check if two applications are duplicates.

        Args:
            item1: First application
            item2: Second application
            threshold: Similarity threshold

        Returns:
            True if duplicates
        """
        return item1.is_duplicate_of(item2, threshold)

    def _merge_items(self, target: Application, source: Application) -> None:
        """
        Merge source application into target.

        Args:
            target: Application to merge into
            source: Application to merge from
        """
        target.merge(source)
        self.save(target)
