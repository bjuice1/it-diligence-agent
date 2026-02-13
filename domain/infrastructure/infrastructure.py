"""
Infrastructure aggregate - THE canonical infrastructure entity.

CRITICAL: Uses kernel.Observation (not custom schema).
This is the domain model for infrastructure items (servers, databases, networks, SaaS, storage).

Created: 2026-02-12 (Worker 3 - Infrastructure Domain, Task-015)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation


@dataclass
class Infrastructure:
    """
    Infrastructure aggregate root.

    CRITICAL PROPERTIES:
    - Aggregate root (owns observations)
    - Uses kernel.Observation (shared schema)
    - Uses kernel.Entity (target vs buyer)
    - Vendor is OPTIONAL (on-prem has no vendor)
    - Entity and deal_id are REQUIRED

    ID Format: INFRA-TARGET-a3f291c2
    Example: INFRA-TARGET-e8a9f2b1

    Infrastructure Types:
    - Servers (physical, virtual, cloud)
    - Databases (SQL, NoSQL, data warehouses)
    - Networks (routers, switches, firewalls)
    - SaaS platforms (cloud services)
    - Storage (SAN, NAS, object storage)

    Examples:
        # Cloud infrastructure (WITH vendor)
        infra1 = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2 t3.large",
            name_normalized="aws ec2",
            vendor="AWS",  # Has vendor
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # On-prem infrastructure (NO vendor)
        infra2 = Infrastructure(
            id="INFRA-TARGET-b4e8f1d3",
            name="On-Prem Data Center",
            name_normalized="on-prem data center",
            vendor=None,  # No vendor (on-prem)
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
    """

    # Identity
    id: str  # Format: INFRA-{ENTITY}-{hash8}
    name: str  # Original name (not normalized)
    name_normalized: str  # Normalized name (for deduplication)
    vendor: Optional[str]  # Vendor (e.g., "AWS", "Microsoft") - OPTIONAL for on-prem
    entity: Entity  # TARGET or BUYER
    deal_id: str  # Multi-tenant isolation

    # Observations
    observations: List[Observation] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate infrastructure on creation."""
        # Validate ID format
        if not self.id:
            raise ValueError("Infrastructure ID cannot be empty")

        # Validate ID format: INFRA-{ENTITY}-{hash8}
        parts = self.id.split("-")
        if len(parts) != 3 or parts[0] != "INFRA":
            raise ValueError(
                f"Invalid infrastructure ID format: {self.id}. "
                f"Expected: INFRA-{{ENTITY}}-{{hash8}}"
            )

        # Validate name
        if not self.name:
            raise ValueError("Infrastructure name cannot be empty")

        if not self.name_normalized:
            raise ValueError("Infrastructure name_normalized cannot be empty")

        # Vendor is OPTIONAL (can be None for on-prem)
        # No validation needed

        # Validate entity (REQUIRED)
        if not self.entity:
            raise ValueError("Infrastructure entity is required")

        if not isinstance(self.entity, Entity):
            raise ValueError(
                f"Infrastructure entity must be Entity enum, got {type(self.entity)}"
            )

        # Validate deal_id (REQUIRED for multi-tenant isolation)
        if not self.deal_id:
            raise ValueError("Infrastructure deal_id is required for multi-tenant isolation")

        # Validate observations
        for obs in self.observations:
            if not isinstance(obs, Observation):
                raise ValueError(
                    f"Infrastructure observations must be Observation instances, got {type(obs)}"
                )

            # Ensure observation entity matches infrastructure entity
            if obs.entity != self.entity:
                raise ValueError(
                    f"Observation entity ({obs.entity}) must match infrastructure entity ({self.entity})"
                )

            # Ensure observation deal_id matches infrastructure deal_id
            if obs.deal_id != self.deal_id:
                raise ValueError(
                    f"Observation deal_id ({obs.deal_id}) must match infrastructure deal_id ({self.deal_id})"
                )

    def add_observation(self, observation: Observation) -> None:
        """
        Add observation to infrastructure.

        Uses priority-based merging:
        - manual (priority 4) > table (3) > llm_prose (2) > llm_assumption (1)
        - Higher priority observations replace lower priority ones

        Args:
            observation: Observation to add

        Raises:
            ValueError: If observation entity doesn't match infrastructure entity
            ValueError: If observation deal_id doesn't match infrastructure deal_id

        Example:
            obs = Observation(
                source_type="table",
                confidence=0.95,
                evidence="Doc page 5",
                extracted_at=datetime.now(),
                deal_id="deal-123",
                entity=Entity.TARGET,
                data={"cost": 50000, "users": 100}
            )
            infrastructure.add_observation(obs)
        """
        # Validate entity match
        if observation.entity != self.entity:
            raise ValueError(
                f"Cannot add observation with entity {observation.entity} "
                f"to infrastructure with entity {self.entity}"
            )

        # Validate deal_id match
        if observation.deal_id != self.deal_id:
            raise ValueError(
                f"Cannot add observation with deal_id {observation.deal_id} "
                f"to infrastructure with deal_id {self.deal_id}"
            )

        # Add observation (priority-based merging handled by caller)
        self.observations.append(observation)
        self.updated_at = datetime.now()

    def get_cost_from_observations(self) -> Optional[float]:
        """
        Extract cost from observations (highest priority wins).

        Returns:
            Cost if found in observations, None otherwise

        Example:
            cost = infrastructure.get_cost_from_observations()
            # Returns: 50000.0 (from highest priority observation with cost data)
        """
        # Sort observations by priority (highest first)
        sorted_obs = sorted(
            self.observations,
            key=lambda o: o.get_priority_score(),
            reverse=True
        )

        # Find first observation with cost data
        for obs in sorted_obs:
            if obs.data and "cost" in obs.data:
                return float(obs.data["cost"])

        return None

    def merge(self, other: "Infrastructure") -> None:
        """
        Merge another infrastructure into this one.

        Used during deduplication when two infrastructure items are found to be the same.
        Merges observations (priority-based).

        Args:
            other: Infrastructure to merge from

        Raises:
            ValueError: If entities don't match
            ValueError: If deal_ids don't match

        Example:
            infra1.merge(infra2)  # Merges infra2's observations into infra1
        """
        # Validate same entity
        if other.entity != self.entity:
            raise ValueError(
                f"Cannot merge infrastructure with different entities: "
                f"{self.entity} vs {other.entity}"
            )

        # Validate same deal
        if other.deal_id != self.deal_id:
            raise ValueError(
                f"Cannot merge infrastructure from different deals: "
                f"{self.deal_id} vs {other.deal_id}"
            )

        # Merge observations
        for obs in other.observations:
            self.add_observation(obs)

        self.updated_at = datetime.now()

    def is_duplicate_of(self, other: "Infrastructure", threshold: float = 0.85) -> bool:
        """
        Check if this infrastructure is a duplicate of another.

        Duplicates have:
        - Same normalized name (similarity >= threshold)
        - Same entity
        - Same deal_id

        Args:
            other: Infrastructure to compare with
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            True if duplicate, False otherwise

        Example:
            is_dup = infra1.is_duplicate_of(infra2, threshold=0.85)
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
        Serialize infrastructure to dictionary.

        Returns:
            Dictionary representation

        Example:
            data = infrastructure.to_dict()
            # Returns: {"id": "INFRA-TARGET-...", "name": "AWS EC2", ...}
        """
        return {
            "id": self.id,
            "name": self.name,
            "name_normalized": self.name_normalized,
            "vendor": self.vendor,
            "entity": self.entity.value,
            "deal_id": self.deal_id,
            "observations": [obs.to_dict() for obs in self.observations],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Infrastructure":
        """
        Deserialize infrastructure from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Infrastructure instance

        Example:
            infrastructure = Infrastructure.from_dict(data)
        """
        return Infrastructure(
            id=data["id"],
            name=data["name"],
            name_normalized=data["name_normalized"],
            vendor=data.get("vendor"),  # Optional
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
        vendor_str = f" ({self.vendor})" if self.vendor else " (on-prem)"
        return f"{self.name}{vendor_str} [{self.entity.name}]"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"Infrastructure(id={self.id!r}, name={self.name!r}, "
            f"vendor={self.vendor!r}, entity={self.entity!r})"
        )
