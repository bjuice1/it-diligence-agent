"""
ApplicationId value object - Stable deterministic IDs.

CRITICAL: Uses kernel.FingerprintGenerator (not custom hashing).
This ensures consistent ID format across all domains.

Created: 2026-02-12 (Worker 2 - Application Domain, Task-011)
"""

from dataclasses import dataclass

from domain.kernel.entity import Entity
from domain.kernel.fingerprint import FingerprintGenerator
from domain.kernel.normalization import NormalizationRules


@dataclass(frozen=True)
class ApplicationId:
    """
    Stable, deterministic ID for applications.

    CRITICAL PROPERTIES:
    - Same (name, vendor, entity) always generates same ID
    - Enables deduplication across multiple analysis runs
    - Format: APP-{ENTITY}-{hash8}
    - Uses kernel.FingerprintGenerator (consistent with other domains)

    ID Format: APP-TARGET-a3f291c2
    Example: APP-TARGET-a3f291c2

    The fingerprint is derived from:
    - Normalized name (using kernel.NormalizationRules)
    - Vendor (prevents "SAP ERP" vs "SAP SuccessFactors" collision - P0-3 fix)
    - Entity (target vs buyer)

    Example:
        from domain.kernel.entity import Entity

        # Same name variants generate same ID
        id1 = ApplicationId.generate("Salesforce", "Salesforce", Entity.TARGET)
        id2 = ApplicationId.generate("Salesforce CRM", "Salesforce", Entity.TARGET)
        assert id1 == id2  # ✅ Same ID (normalized)

        # Different vendor = different ID (P0-3 fix)
        id_sap_erp = ApplicationId.generate("SAP ERP", "SAP", Entity.TARGET)
        id_sap_sf = ApplicationId.generate("SAP SuccessFactors", "SAP", Entity.TARGET)
        assert id_sap_erp != id_sap_sf  # ✅ Different IDs (P0-3 fix working)

        # Different entity = different ID
        id_target = ApplicationId.generate("Salesforce", "Salesforce", Entity.TARGET)
        id_buyer = ApplicationId.generate("Salesforce", "Salesforce", Entity.BUYER)
        assert id_target != id_buyer  # ✅ Different IDs
    """

    value: str  # Format: APP-{ENTITY}-{hash8}

    def __post_init__(self):
        """Validate ID format."""
        if not self.value:
            raise ValueError("ApplicationId cannot be empty")

        # Validate format: APP-{TARGET|BUYER}-{8 hex chars}
        parts = self.value.split("-")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid ApplicationId format: {self.value}. "
                f"Expected: APP-{{ENTITY}}-{{hash8}}"
            )

        domain_prefix, entity_str, hash_part = parts

        if domain_prefix != "APP":
            raise ValueError(
                f"ApplicationId must start with 'APP-', got: {domain_prefix}"
            )

        if entity_str not in ["TARGET", "BUYER"]:
            raise ValueError(
                f"Invalid entity in ApplicationId: {entity_str}. "
                f"Must be TARGET or BUYER"
            )

        if len(hash_part) != 8 or not all(c in "0123456789abcdef" for c in hash_part):
            raise ValueError(
                f"Invalid hash in ApplicationId: {hash_part}. "
                f"Must be 8 lowercase hex characters"
            )

    @staticmethod
    def generate(name: str, vendor: str, entity: Entity) -> "ApplicationId":
        """
        Generate stable ID from name + vendor + entity.

        Uses kernel primitives:
        - NormalizationRules.normalize_name() for name normalization
        - FingerprintGenerator.generate() for ID generation

        This ensures:
        - Same normalization across all domains (applications, infrastructure, org)
        - Same ID format across all domains
        - P0-3 fix (vendor included in hash)

        Args:
            name: Application name (any variant)
            vendor: Vendor name (e.g., "Salesforce", "SAP")
            entity: Entity (TARGET or BUYER)

        Returns:
            ApplicationId with stable fingerprint

        Examples:
            # Same name variants → same ID
            id1 = ApplicationId.generate("Salesforce", "Salesforce", Entity.TARGET)
            id2 = ApplicationId.generate("Salesforce CRM", "Salesforce", Entity.TARGET)
            id3 = ApplicationId.generate("SALESFORCE", "Salesforce", Entity.TARGET)
            assert id1 == id2 == id3  # ✅

            # Different vendor → different ID (P0-3 fix)
            id_sap = ApplicationId.generate("SAP ERP", "SAP", Entity.TARGET)
            id_sap_sf = ApplicationId.generate("SAP SuccessFactors", "SAP", Entity.TARGET)
            assert id_sap != id_sap_sf  # ✅ P0-3 collision prevented

            # Different entity → different ID
            id_target = ApplicationId.generate("Salesforce", "Salesforce", Entity.TARGET)
            id_buyer = ApplicationId.generate("Salesforce", "Salesforce", Entity.BUYER)
            assert id_target != id_buyer  # ✅
        """
        if not name:
            raise ValueError("Cannot generate ApplicationId from empty name")

        if not vendor:
            raise ValueError("Cannot generate ApplicationId without vendor (P0-3 fix requires vendor)")

        if not isinstance(entity, Entity):
            raise ValueError(f"entity must be Entity enum, got {type(entity)}")

        # Normalize name using kernel rules (consistent with other domains)
        name_normalized = NormalizationRules.normalize_name(name, "application")

        # Generate fingerprint using kernel generator (consistent ID format)
        # CRITICAL: Includes vendor to prevent P0-3 collision
        fingerprint = FingerprintGenerator.generate(
            name_normalized=name_normalized,
            vendor=vendor,
            entity=entity,
            domain_prefix="APP"
        )

        return ApplicationId(value=fingerprint)

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"ApplicationId({self.value!r})"
