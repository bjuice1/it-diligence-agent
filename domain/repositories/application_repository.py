"""ApplicationRepository interface - defines persistence contract."""
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.application import Application
from domain.value_objects.application_id import ApplicationId
from domain.value_objects.entity import Entity


class ApplicationRepository(ABC):
    """Repository interface for Application aggregate.

    This is an INTERFACE (abstract base class) that defines the contract
    for persistence. Concrete implementations live in infrastructure/ layer.

    Benefits:
    - Domain layer doesn't depend on database
    - Can swap PostgreSQL for MongoDB without changing domain logic
    - Can mock repository for testing (no database needed)

    Implementations:
    - PostgreSQLApplicationRepository (production)
    - InMemoryApplicationRepository (testing)
    - JSONFileApplicationRepository (export/import)
    """

    @abstractmethod
    def save(self, app: Application) -> None:
        """Save or update application (upsert).

        If app.id already exists: UPDATE
        If app.id is new: INSERT

        Args:
            app: Application to persist

        Raises:
            PersistenceError: If save fails
        """
        pass

    @abstractmethod
    def find_by_id(self, app_id: ApplicationId) -> Optional[Application]:
        """Find application by ID.

        Args:
            app_id: ApplicationId to search for

        Returns:
            Application if found, None if not found
        """
        pass

    @abstractmethod
    def find_or_create(
        self,
        name: str,
        entity: Entity,
        initial_data: dict = None
    ) -> Application:
        """Find existing app or create new one.

        THIS IS THE DEDUPLICATION METHOD.

        Algorithm:
        1. Generate stable ApplicationId from (name, entity)
        2. Check if Application with that ID exists
        3. If YES: return existing (deduplication worked!)
        4. If NO: create new Application and save

        Result: GUARANTEED single Application per (normalized_name, entity)

        Args:
            name: Application name (any variant - will be normalized)
            entity: Entity (TARGET or BUYER)
            initial_data: Optional initial field values

        Returns:
            Existing Application (if found) or newly created Application

        Examples:
            >>> repo.find_or_create("Salesforce", Entity.TARGET)
            Application(id=app_a3f291cd_target, ...)
            >>> repo.find_or_create("Salesforce CRM", Entity.TARGET)  # Same ID!
            Application(id=app_a3f291cd_target, ...)  # Returns existing, no duplicate
        """
        pass

    @abstractmethod
    def find_by_entity(
        self,
        entity: Entity,
        status: str = "active"
    ) -> List[Application]:
        """Find all applications for an entity.

        Args:
            entity: Entity to filter by
            status: Status filter (default "active")

        Returns:
            List of Applications (may be empty)
        """
        pass

    @abstractmethod
    def find_similar(
        self,
        name: str,
        entity: Entity,
        threshold: float = 0.65
    ) -> List[Application]:
        """Find applications with similar names (fuzzy search).

        Used for:
        - Detecting duplicates that slipped through normalization
        - Search autocomplete
        - Manual reconciliation

        Args:
            name: Name to search for
            entity: Entity to filter by
            threshold: Similarity threshold 0.0-1.0

        Returns:
            List of similar Applications

        Examples:
            >>> repo.find_similar("Salesforce", Entity.TARGET, threshold=0.7)
            [
                Application(name="Salesforce"),
                Application(name="Salesforce CRM"),
                Application(name="Salesforce Commerce Cloud")
            ]
        """
        pass

    @abstractmethod
    def count_by_entity(self, entity: Entity, status: str = "active") -> int:
        """Count applications for an entity.

        Args:
            entity: Entity to count
            status: Status filter (default "active")

        Returns:
            Count of applications
        """
        pass

    @abstractmethod
    def delete(self, app_id: ApplicationId) -> None:
        """Hard delete application (use with caution).

        Prefer app.remove(reason) for soft delete.

        Args:
            app_id: ID of application to delete

        Raises:
            NotFoundException: If application doesn't exist
        """
        pass


class PersistenceError(Exception):
    """Raised when persistence operation fails."""
    pass


class NotFoundException(Exception):
    """Raised when entity is not found."""
    pass
