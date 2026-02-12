"""Money value object for cost representation."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts with status tracking.

    This is IMMUTABLE (frozen=True) to prevent accidental mutation.
    Represents cost with explicit status (known, estimated, etc.)

    Examples:
        >>> known_cost = Money(50000, status="known")
        >>> estimated_cost = Money(25000, status="estimated")
        >>> total = known_cost + estimated_cost
        >>> total.amount
        Decimal('75000')
        >>> total.status
        'mixed'  # Combination of known + estimated
    """
    amount: Decimal
    currency: str = "USD"
    status: str = "unknown"  # known, estimated, internal_no_cost, unknown, mixed

    def __post_init__(self):
        """Validate invariants."""
        if not isinstance(self.amount, (int, float, Decimal)):
            raise TypeError(f"Amount must be numeric, got {type(self.amount)}")

        if self.amount < 0:
            raise ValueError(f"Amount cannot be negative: {self.amount}")

        valid_statuses = ["known", "estimated", "internal_no_cost", "unknown", "mixed"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")

        # Convert amount to Decimal for precision
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))

    def __add__(self, other: "Money") -> "Money":
        """Add two Money values.

        Raises:
            ValueError: If currencies don't match
        """
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money to {type(other)}")

        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} + {other.currency}")

        # Determine combined status
        if self.status == other.status:
            new_status = self.status
        else:
            new_status = "mixed"

        return Money(
            amount=self.amount + other.amount,
            currency=self.currency,
            status=new_status
        )

    def __mul__(self, factor: float) -> "Money":
        """Multiply amount by a factor."""
        return Money(
            amount=self.amount * Decimal(str(factor)),
            currency=self.currency,
            status=self.status
        )

    def is_known(self) -> bool:
        """Check if cost is from documents (not estimated)."""
        return self.status == "known"

    def is_estimated(self) -> bool:
        """Check if cost is estimated."""
        return self.status == "estimated"

    def format(self) -> str:
        """Format as currency string.

        Examples:
            >>> Money(50000).format()
            '$50,000.00'
            >>> Money(1234.56).format()
            '$1,234.56'
        """
        return f"${self.amount:,.2f}"

    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        """Create zero-value Money."""
        return cls(amount=Decimal('0'), currency=currency, status="known")

    @classmethod
    def from_float(cls, amount: float, status: str = "unknown", currency: str = "USD") -> "Money":
        """Create Money from float (common use case)."""
        return cls(amount=Decimal(str(amount)), currency=currency, status=status)
