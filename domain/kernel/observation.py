"""
Observation schema - Shared across ALL domains.

CRITICAL: This is THE observation schema for the entire system.
Applications, Infrastructure, Organization all use THIS schema.

Created: 2026-02-12 (Worker 1 - Kernel Foundation, Task-002)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from domain.kernel.entity import Entity


@dataclass
class Observation:
    """
    Shared observation schema for ALL domains.

    CRITICAL: Applications, Infrastructure, Organization all use THIS schema.
    Prevents domain-specific observation formats from diverging.

    An observation represents a piece of information extracted from a document,
    along with metadata about its source, confidence, and context.

    Fields:
        source_type: How was this observation extracted?
            - "table": Deterministic table parsing
            - "llm_prose": LLM extraction from prose text
            - "manual": Human-curated data entry
            - "llm_assumption": LLM inference/guessing

        confidence: Confidence score (0.0 to 1.0)
            - 1.0 = Certain (e.g., extracted from structured table)
            - 0.7-0.9 = High confidence (e.g., LLM extraction from clear prose)
            - 0.5-0.7 = Medium confidence (e.g., LLM extraction from ambiguous text)
            - 0.0-0.5 = Low confidence (e.g., LLM assumptions)

        evidence: Where this observation came from
            - Example: "Page 5, Applications table, row 3"
            - Example: "Section 3.2, paragraph 4"
            - Example: "IT Landscape.pdf, page 12"

        extracted_at: Timestamp when observation was created

        deal_id: Deal identifier (REQUIRED for multi-tenant isolation)
            - Example: "deal-abc123"
            - Ensures observations from different deals don't mix

        entity: Entity this observation belongs to (target vs buyer)
            - REQUIRED to prevent cross-entity contamination
            - Example: Entity.TARGET, Entity.BUYER

        data: Domain-specific observation data (flexible dict)
            - Application domain: {"cost": 50000, "users": 100, "vendor": "Salesforce"}
            - Infrastructure domain: {"provider": "AWS", "instances": 15, "cost": 10000}
            - Organization domain: {"title": "IT Director", "department": "Technology"}

    Example usage:
        # Application domain observation
        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Page 5, Applications table, row 3",
            extracted_at=datetime.now(),
            deal_id="deal-abc123",
            entity=Entity.TARGET,
            data={"cost": 50000, "users": 100, "vendor": "Salesforce"}
        )

        # Infrastructure domain observation (SAME schema)
        obs = Observation(
            source_type="llm_prose",
            confidence=0.70,
            evidence="Mentioned in section 3.2",
            extracted_at=datetime.now(),
            deal_id="deal-abc123",
            entity=Entity.TARGET,
            data={"provider": "AWS", "instances": 15}
        )
    """

    source_type: Literal["table", "llm_prose", "manual", "llm_assumption"]
    confidence: float  # 0.0 to 1.0
    evidence: str  # Where this observation came from
    extracted_at: datetime
    deal_id: str  # REQUIRED for multi-tenant isolation
    entity: Entity  # REQUIRED (target vs buyer)
    data: dict[str, Any]  # Domain-specific observation data

    def __post_init__(self):
        """
        Validate observation after initialization.

        Raises:
            ValueError: If validation fails
        """
        # Validate confidence range
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

        # Validate source_type
        valid_source_types = ["table", "llm_prose", "manual", "llm_assumption"]
        if self.source_type not in valid_source_types:
            raise ValueError(
                f"Invalid source_type: '{self.source_type}'. "
                f"Must be one of: {valid_source_types}"
            )

        # Validate deal_id is provided (required for isolation)
        if not self.deal_id or not self.deal_id.strip():
            raise ValueError(
                "deal_id is required for multi-tenant isolation. "
                "Cannot be empty or None."
            )

        # Validate entity is provided
        if not isinstance(self.entity, Entity):
            raise ValueError(
                f"entity must be an Entity enum (TARGET or BUYER), "
                f"got {type(self.entity).__name__}"
            )

        # Validate evidence is provided
        if not self.evidence or not self.evidence.strip():
            raise ValueError(
                "evidence is required (where observation came from). "
                "Cannot be empty."
            )

        # Validate data is a dict
        if not isinstance(self.data, dict):
            raise ValueError(
                f"data must be a dict, got {type(self.data).__name__}"
            )

    def get_priority_score(self) -> int:
        """
        Get priority score for observation merging.

        Higher score = higher priority (wins in conflicts).

        Priority order:
        1. manual (4) - Human-curated data
        2. table (3) - Deterministic extraction
        3. llm_prose (2) - LLM extraction from prose
        4. llm_assumption (1) - LLM inference/guessing

        Returns:
            Priority score (1-4)
        """
        PRIORITY = {
            "manual": 4,
            "table": 3,
            "llm_prose": 2,
            "llm_assumption": 1
        }
        return PRIORITY.get(self.source_type, 0)

    def should_replace(self, other: "Observation") -> bool:
        """
        Determine if this observation should replace another.

        Used when merging observations with conflicting data.

        Args:
            other: Another observation to compare against

        Returns:
            True if this observation should replace the other (higher priority)

        Examples:
            # Table observation replaces LLM assumption
            obs_table = Observation(source_type="table", ...)
            obs_llm = Observation(source_type="llm_assumption", ...)
            obs_table.should_replace(obs_llm)  # → True

            # Manual observation replaces everything
            obs_manual = Observation(source_type="manual", ...)
            obs_manual.should_replace(obs_table)  # → True
        """
        return self.get_priority_score() > other.get_priority_score()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert observation to dictionary (for JSON serialization).

        Returns:
            Dictionary representation of observation
        """
        return {
            "source_type": self.source_type,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "extracted_at": self.extracted_at.isoformat(),
            "deal_id": self.deal_id,
            "entity": str(self.entity),  # Convert Entity to string
            "data": self.data
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Observation":
        """
        Create observation from dictionary (for JSON deserialization).

        Args:
            data: Dictionary representation

        Returns:
            Observation instance

        Raises:
            ValueError: If data is invalid
        """
        # Parse datetime
        if isinstance(data["extracted_at"], str):
            extracted_at = datetime.fromisoformat(data["extracted_at"])
        else:
            extracted_at = data["extracted_at"]

        # Parse entity
        if isinstance(data["entity"], str):
            entity = Entity.from_string(data["entity"])
        else:
            entity = data["entity"]

        return cls(
            source_type=data["source_type"],
            confidence=data["confidence"],
            evidence=data["evidence"],
            extracted_at=extracted_at,
            deal_id=data["deal_id"],
            entity=entity,
            data=data["data"]
        )
