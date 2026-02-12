"""Entity value object (target vs buyer)."""
from enum import Enum


class Entity(Enum):
    """Entity value object for target vs buyer classification.

    This is a VALUE OBJECT - immutable and validated.
    Replaces scattered string checks ("target", "buyer", None) with type-safe enum.
    """
    TARGET = "target"
    BUYER = "buyer"

    @classmethod
    def from_string(cls, value: str) -> "Entity":
        """Parse from string with validation and normalization.

        Args:
            value: String like "target", "buyer", "seller", "acquirer"

        Returns:
            Entity enum value

        Raises:
            ValueError: If value cannot be mapped to an entity

        Examples:
            >>> Entity.from_string("target")
            Entity.TARGET
            >>> Entity.from_string("BUYER")
            Entity.BUYER
            >>> Entity.from_string("seller")  # Alias
            Entity.TARGET
            >>> Entity.from_string("unknown")
            ValueError: Invalid entity: unknown
        """
        if not value:
            raise ValueError("Entity value cannot be empty")

        normalized = value.lower().strip()

        # Target aliases
        if normalized in ["target", "seller", "divestiture", "tgt"]:
            return cls.TARGET

        # Buyer aliases
        if normalized in ["buyer", "acquirer", "parent", "acquiring", "buyer company"]:
            return cls.BUYER

        raise ValueError(
            f"Invalid entity: {value}. Must be 'target', 'buyer', or recognized alias."
        )

    def __str__(self) -> str:
        """String representation for display."""
        return self.value

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"Entity.{self.name}"
