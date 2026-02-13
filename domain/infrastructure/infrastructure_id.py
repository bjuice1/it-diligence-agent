"""
InfrastructureId value object - Stable deterministic IDs.

CRITICAL: Uses kernel.FingerprintGenerator (not custom hashing).
This ensures consistent ID format across all domains.

IMPORTANT: Vendor is OPTIONAL for infrastructure (on-prem has no vendor).

Created: 2026-02-12 (Worker 3 - Infrastructure Domain, Task-016)
"""

from dataclasses import dataclass
from typing import Optional

from domain.kernel.entity import Entity
from domain.kernel.fingerprint import FingerprintGenerator
from domain.kernel.normalization import NormalizationRules


@dataclass(frozen=True)
class InfrastructureId:
    """
    Stable, deterministic ID for infrastructure.

    CRITICAL PROPERTIES:
    - Same (name, vendor, entity) always generates same ID
    - Enables deduplication across multiple analysis runs
    - Format: INFRA-{ENTITY}-{hash8}
    - Uses kernel.FingerprintGenerator (consistent with other domains)
    - Vendor is OPTIONAL (on-prem infrastructure has no vendor)

    ID Format: INFRA-TARGET-e8a9f2b1
    Example: INFRA-TARGET-e8a9f2b1

    The fingerprint is derived from:
    - Normalized name (using kernel.NormalizationRules)
    - Vendor (OPTIONAL - None for on-prem infrastructure)
    - Entity (target vs buyer)

    Example:
        from domain.kernel.entity import Entity

        # Cloud infrastructure (WITH vendor)
        id1 = InfrastructureId.generate("AWS EC2", "AWS", Entity.TARGET)
        id2 = InfrastructureId.generate("AWS EC2 Instance", "AWS", Entity.TARGET)
        assert id1 == id2  # ✅ Same ID (normalized)

        # On-prem infrastructure (NO vendor)
        id_onprem = InfrastructureId.generate("On-Prem Data Center", None, Entity.TARGET)
        assert id_onprem.value.startswith("INFRA-TARGET-")  # ✅ vendor=None works

        # Different vendor = different ID
        id_aws = InfrastructureId.generate("EC2 Instance", "AWS", Entity.TARGET)
        id_azure = InfrastructureId.generate("EC2 Instance", "Azure", Entity.TARGET)
        assert id_aws != id_azure  # ✅ Different IDs (different vendors)

        # Different entity = different ID
        id_target = InfrastructureId.generate("AWS EC2", "AWS", Entity.TARGET)
        id_buyer = InfrastructureId.generate("AWS EC2", "AWS", Entity.BUYER)
        assert id_target != id_buyer  # ✅ Different IDs
    """

    value: str  # Format: INFRA-{ENTITY}-{hash8}

    def __post_init__(self):
        """Validate ID format."""
        if not self.value:
            raise ValueError("InfrastructureId cannot be empty")

        # Validate format: INFRA-{TARGET|BUYER}-{8 hex chars}
        parts = self.value.split("-")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid InfrastructureId format: {self.value}. "
                f"Expected: INFRA-{{ENTITY}}-{{hash8}}"
            )

        domain_prefix, entity_str, hash_part = parts

        if domain_prefix != "INFRA":
            raise ValueError(
                f"InfrastructureId must start with 'INFRA-', got: {domain_prefix}"
            )

        if entity_str not in ["TARGET", "BUYER"]:
            raise ValueError(
                f"Invalid entity in InfrastructureId: {entity_str}. "
                f"Must be TARGET or BUYER"
            )

        if len(hash_part) != 8 or not all(c in "0123456789abcdef" for c in hash_part):
            raise ValueError(
                f"Invalid hash in InfrastructureId: {hash_part}. "
                f"Must be 8 lowercase hex characters"
            )

    @staticmethod
    def generate(name: str, vendor: Optional[str], entity: Entity) -> "InfrastructureId":
        """
        Generate stable ID from name + vendor + entity.

        Uses kernel primitives:
        - NormalizationRules.normalize_name() for name normalization
        - FingerprintGenerator.generate() for ID generation

        This ensures:
        - Same normalization across all domains (applications, infrastructure, org)
        - Same ID format across all domains
        - Vendor is OPTIONAL (None for on-prem infrastructure)

        Args:
            name: Infrastructure name (any variant)
            vendor: Vendor name (e.g., "AWS", "Microsoft") - OPTIONAL (None for on-prem)
            entity: Entity (TARGET or BUYER)

        Returns:
            InfrastructureId with stable fingerprint

        Examples:
            # Cloud infrastructure - WITH vendor
            id1 = InfrastructureId.generate("AWS EC2 t3.large", "AWS", Entity.TARGET)
            id2 = InfrastructureId.generate("AWS EC2", "AWS", Entity.TARGET)
            assert id1 == id2  # ✅ Same normalized name

            # On-prem infrastructure - NO vendor
            id_onprem = InfrastructureId.generate("On-Prem Data Center", None, Entity.TARGET)
            assert id_onprem.value.startswith("INFRA-TARGET-")  # ✅

            # Different vendor → different ID
            id_aws = InfrastructureId.generate("EC2", "AWS", Entity.TARGET)
            id_azure = InfrastructureId.generate("EC2", "Azure", Entity.TARGET)
            assert id_aws != id_azure  # ✅ Different vendors

            # Different entity → different ID
            id_target = InfrastructureId.generate("AWS EC2", "AWS", Entity.TARGET)
            id_buyer = InfrastructureId.generate("AWS EC2", "AWS", Entity.BUYER)
            assert id_target != id_buyer  # ✅
        """
        if not name:
            raise ValueError("Cannot generate InfrastructureId from empty name")

        # Vendor is OPTIONAL (None for on-prem infrastructure)
        # No validation needed

        if not isinstance(entity, Entity):
            raise ValueError(f"entity must be Entity enum, got {type(entity)}")

        # Normalize name using kernel rules (consistent with other domains)
        name_normalized = NormalizationRules.normalize_name(name, "infrastructure")

        # Generate fingerprint using kernel generator (consistent ID format)
        # Vendor is OPTIONAL (None for on-prem)
        fingerprint = FingerprintGenerator.generate(
            name_normalized,
            vendor,  # Can be None for on-prem infrastructure
            entity,
            "INFRA"
        )

        return InfrastructureId(value=fingerprint)

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"InfrastructureId({self.value!r})"
