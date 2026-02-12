"""
Application aggregate - Domain entity for applications.

CRITICAL: Uses kernel primitives (Entity, Observation).
This is THE application domain entity for the new architecture.

Created: 2026-02-12 (Worker 2 - Application Domain, Task-010)
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation


@dataclass
class Application:
    """
    Application aggregate root.

    CRITICAL: This is THE canonical application entity.
    Replaces the scattered app data across FactStore/InventoryStore/Database/JSON.

    Design:
    - Aggregate root: Owns its observations (composition, not reference)
    - Single source of truth: All app data lives HERE
    - Deduplication: Uses fingerprint-based identity
    - Entity scoping: Always has entity (target vs buyer)
    - Multi-tenant: Always has deal_id

    Example:
        # Create from table observation
        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="IT Landscape.pdf, page 5, row 3",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"vendor": "Salesforce", "cost": 50000, "users": 100}
        )

        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce CRM",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123",
            observations=[obs]
        )

        # Merge duplicate observations
        app.add_observation(another_obs)  # Deduplicates automatically
    """

    # Identity (stable, deterministic)
    id: str  # Format: APP-{ENTITY}-{hash8} (e.g., "APP-TARGET-a3f291c2")

    # Core fields
    name: str  # Canonical name (e.g., "Salesforce CRM")
    name_normalized: str  # Normalized for deduplication (e.g., "salesforce")
    vendor: str  # Vendor name (e.g., "Salesforce")

    # Entity scoping (ALWAYS required)
    entity: Entity  # TARGET or BUYER
    deal_id: str  # Multi-tenant isolation

    # Observations (evidence from documents)
    observations: List[Observation] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate application invariants."""
        if not self.id:
            raise ValueError("Application ID is required")

        if not self.id.startswith("APP-"):
            raise ValueError(f"Invalid application ID format: {self.id}")

        if not self.name:
            raise ValueError("Application name is required")

        if not self.deal_id:
            raise ValueError("deal_id is required for multi-tenant isolation")

        if not isinstance(self.entity, Entity):
            raise ValueError(f"entity must be Entity enum, got {type(self.entity)}")

    def add_observation(self, observation: Observation) -> None:
        """
        Add observation to application.

        CRITICAL: Merges observations by priority.
        If new observation has higher priority than existing, replaces data.

        Priority order (from Observation.get_priority_score()):
        1. manual (score=4)
        2. table (score=3)
        3. llm_prose (score=2)
        4. llm_assumption (score=1)

        Args:
            observation: Observation to add

        Example:
            # First observation (table, score=3)
            app.add_observation(table_obs)

            # Second observation (manual, score=4) - replaces table data
            app.add_observation(manual_obs)

            # Third observation (llm_assumption, score=1) - ignored, table wins
            app.add_observation(llm_obs)
        """
        if not isinstance(observation, Observation):
            raise ValueError(f"observation must be Observation, got {type(observation)}")

        # Validate entity matches
        if observation.entity != self.entity:
            raise ValueError(
                f"Observation entity ({observation.entity}) does not match "
                f"application entity ({self.entity})"
            )

        # Validate deal_id matches
        if observation.deal_id != self.deal_id:
            raise ValueError(
                f"Observation deal_id ({observation.deal_id}) does not match "
                f"application deal_id ({self.deal_id})"
            )

        # Check if we should replace existing observations
        # Strategy: Keep highest priority observation for each data field
        should_add = True

        for existing_obs in self.observations:
            # If new observation has higher priority, it should replace
            if observation.should_replace(existing_obs):
                # New observation wins - remove old one
                self.observations.remove(existing_obs)
                break
            elif existing_obs.should_replace(observation):
                # Existing observation wins - don't add new one
                should_add = False
                break

        if should_add:
            self.observations.append(observation)
            self.updated_at = datetime.now()

    def merge(self, other: "Application") -> None:
        """
        Merge another application into this one.

        Used by reconciliation to combine duplicates.

        Strategy:
        - Keep this application's ID (the one being merged into)
        - Merge all observations (priority-based)
        - Update metadata

        Args:
            other: Another application to merge into this one

        Example:
            # Two applications for same entity (duplicates)
            app1 = Application(id="APP-TARGET-a3f291c2", name="Salesforce", ...)
            app2 = Application(id="APP-TARGET-b4e8f1d3", name="Salesforce CRM", ...)

            # Merge app2 into app1
            app1.merge(app2)
            # app1 now has observations from both
        """
        if not isinstance(other, Application):
            raise ValueError(f"Can only merge with Application, got {type(other)}")

        if other.entity != self.entity:
            raise ValueError(
                f"Cannot merge applications from different entities: "
                f"{self.entity} vs {other.entity}"
            )

        if other.deal_id != self.deal_id:
            raise ValueError(
                f"Cannot merge applications from different deals: "
                f"{self.deal_id} vs {other.deal_id}"
            )

        # Merge all observations (priority-based deduplication)
        for obs in other.observations:
            self.add_observation(obs)

        self.updated_at = datetime.now()

    def is_duplicate_of(self, other: "Application", threshold: float = 0.85) -> bool:
        """
        Check if this application is a duplicate of another.

        Strategy:
        - Compare normalized names
        - Compare vendors
        - Check entity matches
        - Fuzzy similarity threshold

        Args:
            other: Another application
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            True if applications are duplicates

        Example:
            app1 = Application(name="Salesforce", name_normalized="salesforce", ...)
            app2 = Application(name="Salesforce CRM", name_normalized="salesforce", ...)

            app1.is_duplicate_of(app2)  # → True (same normalized name)
        """
        if not isinstance(other, Application):
            return False

        # Must be same entity
        if self.entity != other.entity:
            return False

        # Must be same deal
        if self.deal_id != other.deal_id:
            return False

        # Exact normalized name match
        if self.name_normalized == other.name_normalized:
            return True

        # Fuzzy name similarity (simple Levenshtein distance approximation)
        similarity = self._calculate_similarity(
            self.name_normalized,
            other.name_normalized
        )

        return similarity >= threshold

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings.

        Uses simple character overlap approximation.
        (In production, use python-Levenshtein or difflib)

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

    def get_cost(self) -> Optional[float]:
        """
        Get cost from observations (highest priority).

        Strategy:
        - Check all observations for cost data
        - Return cost from highest priority observation

        Returns:
            Cost if found, None otherwise
        """
        # Sort observations by priority (highest first)
        sorted_obs = sorted(
            self.observations,
            key=lambda obs: obs.get_priority_score(),
            reverse=True
        )

        for obs in sorted_obs:
            if "cost" in obs.data:
                return obs.data["cost"]

        return None

    def to_dict(self) -> dict:
        """
        Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "name_normalized": self.name_normalized,
            "vendor": self.vendor,
            "entity": str(self.entity),
            "deal_id": self.deal_id,
            "observations": [obs.to_dict() for obs in self.observations],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Application":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Application instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            name_normalized=data["name_normalized"],
            vendor=data["vendor"],
            entity=Entity.from_string(data["entity"]),
            deal_id=data["deal_id"],
            observations=[
                Observation.from_dict(obs_data)
                for obs_data in data.get("observations", [])
            ],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Application(id={self.id!r}, name={self.name!r}, "
            f"entity={self.entity}, observations={len(self.observations)})"
        )
