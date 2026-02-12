"""
Normalization rules - Shared across ALL domains.

CRITICAL: Fixes P0-3 collision bug (SAP ERP vs SAP SuccessFactors).
All domains use THESE normalization rules.

Created: 2026-02-12 (Worker 1 - Kernel Foundation, Task-003)
"""

import re
from typing import Literal
from domain.kernel.observation import Observation

DomainType = Literal["application", "infrastructure", "organization"]


class NormalizationRules:
    """
    Shared normalization strategy for ALL domains.

    CRITICAL: Applications, Infrastructure, Organization all use THESE rules.
    Prevents cross-domain inconsistency in how names are normalized.

    Fixes P0-3: "SAP ERP" vs "SAP SuccessFactors" collision
    Strategy: Whitelist-based suffix removal (only TRAILING suffixes)
    """

    @staticmethod
    def normalize_name(name: str, domain: DomainType) -> str:
        """
        Normalize name for deduplication.

        CRITICAL: Different domains MAY have different normalization rules,
        but ALL apps use app rules, ALL infra uses infra rules (consistency).

        Args:
            name: Raw name (e.g., "Salesforce CRM", "AWS EC2 Production")
            domain: Which domain ("application", "infrastructure", "organization")

        Returns:
            Normalized name for fingerprinting

        Examples:
            # Applications:
            normalize_name("Salesforce CRM", "application") → "salesforce"
            normalize_name("SAP ERP", "application") → "sap"
            normalize_name("SAP SuccessFactors", "application") → "sap successfactors"
            # ↑ Different from "sap" - prevents P0-3 collision!

            # Infrastructure:
            normalize_name("AWS EC2 Production", "infrastructure") → "aws ec2 production"
            normalize_name("Azure VM Dev", "infrastructure") → "azure vm dev"
            # ↑ Keeps environment indicators

            # Organization:
            normalize_name("IT Director", "organization") → "it director"
            normalize_name("VP of Sales", "organization") → "vp of sales"
            # ↑ Keeps titles
        """
        if domain == "application":
            return NormalizationRules._normalize_application(name)
        elif domain == "infrastructure":
            return NormalizationRules._normalize_infrastructure(name)
        elif domain == "organization":
            return NormalizationRules._normalize_organization(name)
        else:
            raise ValueError(f"Unknown domain: {domain}")

    @staticmethod
    def _normalize_application(name: str) -> str:
        """
        Application-specific normalization (fixes P0-3).

        Strategy: Remove TRAILING common suffixes only (not internal ones).
        This prevents "SAP ERP" and "SAP SuccessFactors" from both → "sap".

        Examples:
            "Salesforce CRM" → "salesforce" (CRM is trailing)
            "Microsoft Dynamics CRM" → "microsoft dynamics" (CRM is trailing)
            "SAP ERP" → "sap" (ERP is trailing)
            "SAP SuccessFactors" → "sap successfactors" (no suffix to remove)
            "Oracle EBS (E-Business Suite)" → "oracle ebs" (suite is trailing)

        Args:
            name: Application name

        Returns:
            Normalized name
        """
        # Lowercase and strip
        normalized = name.lower().strip()

        # Remove special characters (but keep spaces, hyphens)
        normalized = re.sub(r'[^\w\s-]', '', normalized)

        # Remove TRAILING common suffixes only (whitelist approach)
        # This prevents "SAP ERP" and "SAP SuccessFactors" from colliding
        normalized = re.sub(
            r'\s+(crm|erp|online|cloud|suite|platform|app|system|software)$',
            '',
            normalized
        )

        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    @staticmethod
    def _normalize_infrastructure(name: str) -> str:
        """
        Infrastructure-specific normalization.

        Strategy: Keep environment indicators (prod, dev, staging).
        Infrastructure often has multiple instances that must stay separate.

        Examples:
            "AWS EC2 Production" → "aws ec2 production"
            "AWS EC2 Development" → "aws ec2 development"
            "Azure VM Prod" → "azure vm prod"

        Args:
            name: Infrastructure name

        Returns:
            Normalized name
        """
        # Keep environment indicators (prod, dev, staging)
        normalized = name.lower().strip()

        # Remove special characters
        normalized = re.sub(r'[^\w\s-]', '', normalized)

        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    @staticmethod
    def _normalize_organization(name: str) -> str:
        """
        Organization-specific normalization.

        Strategy: Keep titles (Director, Manager, VP).
        People with same name but different titles are different entities.

        Examples:
            "John Smith - IT Director" → "john smith  it director"
            "John Smith - VP of Technology" → "john smith  vp of technology"

        Args:
            name: Person name (possibly with title)

        Returns:
            Normalized name
        """
        # Keep titles (Director, Manager, VP)
        normalized = name.lower().strip()

        # Remove special characters
        normalized = re.sub(r'[^\w\s-]', '', normalized)

        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    @staticmethod
    def should_merge(obs1: Observation, obs2: Observation) -> bool:
        """
        Shared merging strategy when observations conflict.

        CRITICAL: ALL domains use SAME priority order.

        Priority (highest to lowest):
        1. manual (human-curated data) - score: 4
        2. table (deterministic extraction) - score: 3
        3. llm_prose (LLM extraction from prose) - score: 2
        4. llm_assumption (LLM inference/guessing) - score: 1

        Args:
            obs1: First observation
            obs2: Second observation

        Returns:
            True if obs1 should replace obs2 (obs1 has higher priority)

        Examples:
            # Table observation replaces LLM assumption
            obs_table = Observation(source_type="table", ...)
            obs_llm = Observation(source_type="llm_assumption", ...)
            should_merge(obs_table, obs_llm)  # → True

            # Manual observation replaces everything
            obs_manual = Observation(source_type="manual", ...)
            should_merge(obs_manual, obs_table)  # → True

            # LLM prose does NOT replace table
            should_merge(obs_llm_prose, obs_table)  # → False
        """
        return obs1.should_replace(obs2)
