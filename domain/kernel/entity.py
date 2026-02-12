"""
Entity value object - Shared across ALL domains.

CRITICAL: Applications, Infrastructure, Organization all use THIS enum.
Prevents cross-domain inconsistency (app says 'target', infra says 'buyer').

Created: 2026-02-12 (Worker 1 - Kernel Foundation, Task-001)
"""

from enum import Enum


class Entity(str, Enum):
    """
    Entity enum - represents whether data belongs to target or buyer company.

    CRITICAL: This is THE canonical entity enum for the entire system.
    ALL domains (applications, infrastructure, organization) MUST use this.

    Values:
        TARGET: The company being acquired (seller, portfolio company)
        BUYER: The acquiring company (acquirer, parent company, our company)

    Usage:
        from domain.kernel.entity import Entity

        # Create entity
        entity = Entity.TARGET
        entity = Entity.BUYER

        # String conversion
        str(entity)  # Returns: "target" or "buyer"

        # Comparison
        if entity == Entity.TARGET:
            ...

        # Database storage
        # Entity stores as string ("target" or "buyer") due to str inheritance
    """

    TARGET = "target"
    BUYER = "buyer"

    def __str__(self) -> str:
        """Return lowercase string representation."""
        return self.value

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"Entity.{self.name}"

    @classmethod
    def from_string(cls, value: str) -> "Entity":
        """
        Create Entity from string value.

        Args:
            value: String value ("target", "buyer", case-insensitive)

        Returns:
            Entity.TARGET or Entity.BUYER

        Raises:
            ValueError: If value is not "target" or "buyer"

        Examples:
            Entity.from_string("target")  # → Entity.TARGET
            Entity.from_string("TARGET")  # → Entity.TARGET
            Entity.from_string("buyer")   # → Entity.BUYER
            Entity.from_string("invalid") # → ValueError
        """
        value_lower = value.lower().strip()

        if value_lower == "target":
            return cls.TARGET
        elif value_lower == "buyer":
            return cls.BUYER
        else:
            raise ValueError(
                f"Invalid entity value: '{value}'. "
                f"Must be 'target' or 'buyer' (case-insensitive)."
            )
