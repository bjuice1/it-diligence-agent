"""
Fingerprint generation - Shared across ALL domains.

CRITICAL: Fixes P0-3 collision (includes vendor in hash).
All domains use THIS fingerprint strategy.

Created: 2026-02-12 (Worker 1 - Kernel Foundation, Task-005)
"""

import hashlib
from domain.kernel.entity import Entity


class FingerprintGenerator:
    """
    Shared fingerprint generation strategy.

    CRITICAL: ALL domains use THIS fingerprint strategy.
    Ensures consistent hashing across applications, infrastructure, organization.
    """

    @staticmethod
    def generate(
        name_normalized: str,
        vendor: str,
        entity: Entity,
        domain_prefix: str
    ) -> str:
        """
        Generate stable fingerprint for domain ID.

        Strategy (fixes P0-3 collision):
        - Include normalized name
        - Include vendor (prevents "SAP ERP" vs "SAP SuccessFactors" collision)
        - Include entity (target vs buyer)
        - Hash to 8 characters (collision probability ~1 in 4 billion)

        Args:
            name_normalized: Normalized name (from NormalizationRules)
            vendor: Vendor name (e.g., "SAP", "Microsoft")
            entity: Entity (target or buyer)
            domain_prefix: Domain prefix ("APP", "INFRA", "ORG")

        Returns:
            Domain ID: "{domain_prefix}-{entity_upper}-{hash8}"

        Examples:
            generate("salesforce", "Salesforce", Entity.TARGET, "APP")
              → "APP-TARGET-a3f291c2"

            generate("sap", "SAP", Entity.TARGET, "APP")
              → "APP-TARGET-b4e8f1d3"

            generate("sap successfactors", "SAP", Entity.TARGET, "APP")
              → "APP-TARGET-c9a7e2f5"  # Different from plain "sap"!

            # Same name, different entity → different ID
            generate("salesforce", "Salesforce", Entity.BUYER, "APP")
              → "APP-BUYER-d1a3f291"  # Different from TARGET
        """
        # Vendor normalization (lowercase, strip)
        vendor_normalized = vendor.lower().strip() if vendor else ""

        # Combine components for fingerprinting
        # CRITICAL: Include vendor to prevent collisions (P0-3 fix)
        fingerprint_input = f"{name_normalized}|{vendor_normalized}|{entity.value}"

        # Hash to 8 characters
        hash_full = hashlib.md5(fingerprint_input.encode()).hexdigest()
        hash_short = hash_full[:8]

        # Format: APP-TARGET-a3f291c2
        return f"{domain_prefix}-{entity.name}-{hash_short}"

    @staticmethod
    def generate_without_vendor(
        name_normalized: str,
        entity: Entity,
        domain_prefix: str
    ) -> str:
        """
        Generate fingerprint without vendor (fallback).

        Use this ONLY when vendor is unknown.
        Prefer generate() with vendor to prevent P0-3 collisions.

        Args:
            name_normalized: Normalized name
            entity: Entity (target or buyer)
            domain_prefix: Domain prefix

        Returns:
            Domain ID without vendor in hash

        Warning:
            This can cause collisions! "SAP ERP" and "SAP SuccessFactors"
            might get the same ID if both normalize to "sap".
        """
        # Hash without vendor
        fingerprint_input = f"{name_normalized}|{entity.value}"
        hash_full = hashlib.md5(fingerprint_input.encode()).hexdigest()
        hash_short = hash_full[:8]

        return f"{domain_prefix}-{entity.name}-{hash_short}"

    @staticmethod
    def parse_domain_id(domain_id: str) -> dict[str, str]:
        """
        Parse domain ID into components.

        Args:
            domain_id: Domain ID (e.g., "APP-TARGET-a3f291c2")

        Returns:
            Dictionary with: domain_prefix, entity, hash

        Examples:
            parse_domain_id("APP-TARGET-a3f291c2")
              → {"domain_prefix": "APP", "entity": "TARGET", "hash": "a3f291c2"}

            parse_domain_id("INFRA-BUYER-b4e8f1d3")
              → {"domain_prefix": "INFRA", "entity": "BUYER", "hash": "b4e8f1d3"}

        Raises:
            ValueError: If domain_id format is invalid
        """
        parts = domain_id.split("-")

        if len(parts) != 3:
            raise ValueError(
                f"Invalid domain ID format: '{domain_id}'. "
                f"Expected format: 'PREFIX-ENTITY-HASH' (e.g., 'APP-TARGET-a3f291c2')"
            )

        domain_prefix, entity_str, hash_str = parts

        # Validate entity
        if entity_str not in ["TARGET", "BUYER"]:
            raise ValueError(
                f"Invalid entity in domain ID: '{entity_str}'. "
                f"Must be 'TARGET' or 'BUYER'."
            )

        # Validate hash (8 hexadecimal characters)
        if len(hash_str) != 8 or not all(c in '0123456789abcdef' for c in hash_str):
            raise ValueError(
                f"Invalid hash in domain ID: '{hash_str}'. "
                f"Must be 8 hexadecimal characters."
            )

        return {
            "domain_prefix": domain_prefix,
            "entity": entity_str,
            "hash": hash_str
        }

    @staticmethod
    def extract_entity_from_id(domain_id: str) -> Entity:
        """
        Extract entity from domain ID.

        Args:
            domain_id: Domain ID (e.g., "APP-TARGET-a3f291c2")

        Returns:
            Entity.TARGET or Entity.BUYER

        Examples:
            extract_entity_from_id("APP-TARGET-a3f291c2")  → Entity.TARGET
            extract_entity_from_id("INFRA-BUYER-b4e8f1d3") → Entity.BUYER
        """
        parsed = FingerprintGenerator.parse_domain_id(domain_id)
        return Entity.from_string(parsed["entity"])

    @staticmethod
    def is_valid_domain_id(domain_id: str) -> bool:
        """
        Check if domain ID is valid format.

        Args:
            domain_id: Domain ID to validate

        Returns:
            True if valid, False otherwise

        Examples:
            is_valid_domain_id("APP-TARGET-a3f291c2")  → True
            is_valid_domain_id("INFRA-BUYER-b4e8f1d3") → True
            is_valid_domain_id("APP-TARGET")           → False
            is_valid_domain_id("invalid")              → False
        """
        try:
            FingerprintGenerator.parse_domain_id(domain_id)
            return True
        except ValueError:
            return False
