"""
Person aggregate - THE canonical organization entity.

CRITICAL: Uses kernel.Observation (not custom schema).
This is the domain model for people, teams, and departments.

Created: 2026-02-12 (Worker 4 - Organization Domain, Task-020)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation


@dataclass
class Person:
    """
    Person aggregate root.

    CRITICAL PROPERTIES:
    - Aggregate root (owns observations)
    - Uses kernel.Observation (shared schema)
    - Uses kernel.Entity (target vs buyer)
    - Vendor is ALWAYS None (people have no vendor)
    - Entity and deal_id are REQUIRED

    ID Format: ORG-TARGET-f3b8c9d2
    Example: ORG-TARGET-f3b8c9d2

    Organization Types:
    - People (employees, executives, contractors)
    - Teams (IT team, Finance team)
    - Departments (IT Department, HR Department)
    - Roles (CTO, CFO, IT Director)

    Examples:
        # Person
        person1 = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith - CTO",
            name_normalized="john smith",
            vendor=None,  # People have no vendor
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Team/Department
        team1 = Person(
            id="ORG-TARGET-a1b2c3d4",
            name="IT Department",
            name_normalized="it department",
            vendor=None,  # Departments have no vendor
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
    """

    # Identity
    id: str  # Format: ORG-{ENTITY}-{hash8}
    name: str  # Original name (not normalized)
    name_normalized: str  # Normalized name (for deduplication)
    vendor: Optional[str]  # ALWAYS None for people (included for consistency)
    entity: Entity  # TARGET or BUYER
    deal_id: str  # Multi-tenant isolation

    # Observations
    observations: List[Observation] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate person on creation."""
        # Validate ID format
        if not self.id:
            raise ValueError("Person ID cannot be empty")

        # Validate ID format: ORG-{ENTITY}-{hash8}
        parts = self.id.split("-")
        if len(parts) != 3 or parts[0] != "ORG":
            raise ValueError(
                f"Invalid person ID format: {self.id}. "
                f"Expected: ORG-{{ENTITY}}-{{hash8}}"
            )

        # Validate name
        if not self.name:
            raise ValueError("Person name cannot be empty")

        if not self.name_normalized:
            raise ValueError("Person name_normalized cannot be empty")

        # Vendor should ALWAYS be None for people
        # (We keep the field for consistency with other domains)
        if self.vendor is not None:
            raise ValueError(
                "Person vendor must be None. People/teams/departments have no vendor."
            )

        # Validate entity (REQUIRED)
        if not self.entity:
            raise ValueError("Person entity is required")

        if not isinstance(self.entity, Entity):
            raise ValueError(
                f"Person entity must be Entity enum, got {type(self.entity)}"
            )

        # Validate deal_id (REQUIRED for multi-tenant isolation)
        if not self.deal_id:
            raise ValueError("Person deal_id is required for multi-tenant isolation")

        # Validate observations
        for obs in self.observations:
            if not isinstance(obs, Observation):
                raise ValueError(
                    f"Person observations must be Observation instances, got {type(obs)}"
                )

            # Ensure observation entity matches person entity
            if obs.entity != self.entity:
                raise ValueError(
                    f"Observation entity ({obs.entity}) must match person entity ({self.entity})"
                )

            # Ensure observation deal_id matches person deal_id
            if obs.deal_id != self.deal_id:
                raise ValueError(
                    f"Observation deal_id ({obs.deal_id}) must match person deal_id ({self.deal_id})"
                )

    def add_observation(self, observation: Observation) -> None:
        """
        Add observation to person.

        Uses priority-based merging:
        - manual (priority 4) > table (3) > llm_prose (2) > llm_assumption (1)
        - Higher priority observations replace lower priority ones

        Args:
            observation: Observation to add

        Raises:
            ValueError: If observation entity doesn't match person entity
            ValueError: If observation deal_id doesn't match person deal_id

        Example:
            obs = Observation(
                source_type="table",
                confidence=0.95,
                evidence="Doc page 5",
                extracted_at=datetime.now(),
                deal_id="deal-123",
                entity=Entity.TARGET,
                data={"role": "CTO", "department": "IT"}
            )
            person.add_observation(obs)
        """
        # Validate entity match
        if observation.entity != self.entity:
            raise ValueError(
                f"Cannot add observation with entity {observation.entity} "
                f"to person with entity {self.entity}"
            )

        # Validate deal_id match
        if observation.deal_id != self.deal_id:
            raise ValueError(
                f"Cannot add observation with deal_id {observation.deal_id} "
                f"to person with deal_id {self.deal_id}"
            )

        # Add observation (priority-based merging handled by caller)
        self.observations.append(observation)
        self.updated_at = datetime.now()

    def get_role_from_observations(self) -> Optional[str]:
        """
        Extract role from observations (highest priority wins).

        Returns:
            Role if found in observations, None otherwise

        Example:
            role = person.get_role_from_observations()
            # Returns: "CTO" (from highest priority observation with role data)
        """
        # Sort observations by priority (highest first)
        sorted_obs = sorted(
            self.observations,
            key=lambda o: o.get_priority_score(),
            reverse=True
        )

        # Find first observation with role data
        for obs in sorted_obs:
            if obs.data and "role" in obs.data:
                return str(obs.data["role"])

        return None

    def merge(self, other: "Person") -> None:
        """
        Merge another person into this one.

        Used during deduplication when two person items are found to be the same.
        Merges observations (priority-based).

        Args:
            other: Person to merge from

        Raises:
            ValueError: If entities don't match
            ValueError: If deal_ids don't match

        Example:
            person1.merge(person2)  # Merges person2's observations into person1
        """
        # Validate same entity
        if other.entity != self.entity:
            raise ValueError(
                f"Cannot merge person with different entities: "
                f"{self.entity} vs {other.entity}"
            )

        # Validate same deal
        if other.deal_id != self.deal_id:
            raise ValueError(
                f"Cannot merge person from different deals: "
                f"{self.deal_id} vs {other.deal_id}"
            )

        # Merge observations
        for obs in other.observations:
            self.add_observation(obs)

        self.updated_at = datetime.now()

    def is_duplicate_of(self, other: "Person", threshold: float = 0.85) -> bool:
        """
        Check if this person is a duplicate of another.

        Duplicates have:
        - Same normalized name (similarity >= threshold)
        - Same entity
        - Same deal_id

        Args:
            other: Person to compare with
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            True if duplicate, False otherwise

        Example:
            is_dup = person1.is_duplicate_of(person2, threshold=0.85)
        """
        # Different entity = not duplicate
        if self.entity != other.entity:
            return False

        # Different deal = not duplicate
        if self.deal_id != other.deal_id:
            return False

        # Same ID = exact duplicate
        if self.id == other.id:
            return True

        # Check name similarity
        # Simple character overlap for now (production would use database trigram)
        name1 = set(self.name_normalized.lower())
        name2 = set(other.name_normalized.lower())

        if not name1 or not name2:
            return False

        intersection = len(name1 & name2)
        union = len(name1 | name2)
        similarity = intersection / union if union > 0 else 0.0

        return similarity >= threshold

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize person to dictionary.

        Returns:
            Dictionary representation

        Example:
            data = person.to_dict()
            # Returns: {"id": "ORG-TARGET-...", "name": "John Smith", ...}
        """
        return {
            "id": self.id,
            "name": self.name,
            "name_normalized": self.name_normalized,
            "vendor": self.vendor,  # Always None for people
            "entity": self.entity.value,
            "deal_id": self.deal_id,
            "observations": [obs.to_dict() for obs in self.observations],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Person":
        """
        Deserialize person from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Person instance

        Example:
            person = Person.from_dict(data)
        """
        return Person(
            id=data["id"],
            name=data["name"],
            name_normalized=data["name_normalized"],
            vendor=data.get("vendor"),  # Should always be None
            entity=Entity.from_string(data["entity"]),
            deal_id=data["deal_id"],
            observations=[
                Observation.from_dict(obs_data)
                for obs_data in data.get("observations", [])
            ],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} [{self.entity.name}]"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"Person(id={self.id!r}, name={self.name!r}, "
            f"entity={self.entity!r})"
        )
