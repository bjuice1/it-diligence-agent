"""
PersonId value object - Stable deterministic IDs.

CRITICAL: Uses kernel.FingerprintGenerator (not custom hashing).
This ensures consistent ID format across all domains.

IMPORTANT: Vendor is ALWAYS None for people (no vendor concept).

Created: 2026-02-12 (Worker 4 - Organization Domain, Task-021)
"""

from dataclasses import dataclass

from domain.kernel.entity import Entity
from domain.kernel.fingerprint import FingerprintGenerator
from domain.kernel.normalization import NormalizationRules


@dataclass(frozen=True)
class PersonId:
    """
    Stable, deterministic ID for people.

    CRITICAL PROPERTIES:
    - Same (name, entity) always generates same ID
    - Enables deduplication across multiple analysis runs
    - Format: ORG-{ENTITY}-{hash8}
    - Uses kernel.FingerprintGenerator (consistent with other domains)
    - Vendor is ALWAYS None (people have no vendor)

    ID Format: ORG-TARGET-f3b8c9d2
    Example: ORG-TARGET-f3b8c9d2

    The fingerprint is derived from:
    - Normalized name (using kernel.NormalizationRules)
    - Vendor (ALWAYS None for people)
    - Entity (target vs buyer)

    Example:
        from domain.kernel.entity import Entity

        # Person
        id1 = PersonId.generate("John Smith - CTO", Entity.TARGET)
        id2 = PersonId.generate("John Smith", Entity.TARGET)
        assert id1 == id2  # ✅ Same ID (normalized)

        # Team/Department
        id_team = PersonId.generate("IT Department", Entity.TARGET)
        assert id_team.value.startswith("ORG-TARGET-")  # ✅

        # Different entity = different ID
        id_target = PersonId.generate("John Smith", Entity.TARGET)
        id_buyer = PersonId.generate("John Smith", Entity.BUYER)
        assert id_target != id_buyer  # ✅ Different IDs
    """

    value: str  # Format: ORG-{ENTITY}-{hash8}

    def __post_init__(self):
        """Validate ID format."""
        if not self.value:
            raise ValueError("PersonId cannot be empty")

        # Validate format: ORG-{TARGET|BUYER}-{8 hex chars}
        parts = self.value.split("-")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid PersonId format: {self.value}. "
                f"Expected: ORG-{{ENTITY}}-{{hash8}}"
            )

        domain_prefix, entity_str, hash_part = parts

        if domain_prefix != "ORG":
            raise ValueError(
                f"PersonId must start with 'ORG-', got: {domain_prefix}"
            )

        if entity_str not in ["TARGET", "BUYER"]:
            raise ValueError(
                f"Invalid entity in PersonId: {entity_str}. "
                f"Must be TARGET or BUYER"
            )

        if len(hash_part) != 8 or not all(c in "0123456789abcdef" for c in hash_part):
            raise ValueError(
                f"Invalid hash in PersonId: {hash_part}. "
                f"Must be 8 lowercase hex characters"
            )

    @staticmethod
    def generate(name: str, entity: Entity) -> "PersonId":
        """
        Generate stable ID from name + entity.

        Uses kernel primitives:
        - NormalizationRules.normalize_name() for name normalization
        - FingerprintGenerator.generate() for ID generation

        This ensures:
        - Same normalization across all domains (applications, infrastructure, org)
        - Same ID format across all domains
        - Vendor is ALWAYS None (people have no vendor)

        Args:
            name: Person name (any variant)
            entity: Entity (TARGET or BUYER)

        Returns:
            PersonId with stable fingerprint

        Examples:
            # Person - same name variants generate same ID
            id1 = PersonId.generate("John Smith - CTO", Entity.TARGET)
            id2 = PersonId.generate("John Smith", Entity.TARGET)
            id3 = PersonId.generate("JOHN SMITH", Entity.TARGET)
            assert id1 == id2 == id3  # ✅ Same normalized name

            # Team/Department
            id_team = PersonId.generate("IT Department", Entity.TARGET)
            assert id_team.value.startswith("ORG-TARGET-")  # ✅

            # Different entity → different ID
            id_target = PersonId.generate("John Smith", Entity.TARGET)
            id_buyer = PersonId.generate("John Smith", Entity.BUYER)
            assert id_target != id_buyer  # ✅
        """
        if not name:
            raise ValueError("Cannot generate PersonId from empty name")

        if not isinstance(entity, Entity):
            raise ValueError(f"entity must be Entity enum, got {type(entity)}")

        # Normalize name using kernel rules (consistent with other domains)
        name_normalized = NormalizationRules.normalize_name(name, "organization")

        # Generate fingerprint using kernel generator (consistent ID format)
        # Vendor is ALWAYS None for people (no vendor concept)
        fingerprint = FingerprintGenerator.generate(
            name_normalized,
            None,  # vendor is ALWAYS None for people
            entity,
            "ORG"
        )

        return PersonId(value=fingerprint)

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"PersonId({self.value!r})"
