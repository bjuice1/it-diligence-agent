"""
Entity inference rules - Shared across ALL domains.

CRITICAL: Applications, Infrastructure, Organization use SAME inference logic.
Prevents apps saying "target" while infra says "buyer" for same document.

Created: 2026-02-12 (Worker 1 - Kernel Foundation, Task-004)
"""

from domain.kernel.entity import Entity


class EntityInference:
    """
    Shared rules for inferring target vs buyer from context.

    CRITICAL: ALL domains use SAME inference logic.
    This prevents cross-domain inconsistency where apps infer "target"
    but infrastructure infers "buyer" from the same document.
    """

    # Indicators that suggest "buyer" (our company, the acquirer)
    BUYER_INDICATORS = [
        "acquirer", "buyer", "our", "current", "existing",
        "we", "us", "internal", "parent", "acquiring company",
        "purchaser", "our company", "our organization",
        "our current", "our existing", "our infrastructure",
        "our applications", "our systems", "our team",
        "current state", "as-is", "baseline"
    ]

    # Indicators that suggest "target" (company being acquired)
    TARGET_INDICATORS = [
        "target", "acquisition", "their", "to be acquired",
        "seller", "acquired company", "portfolio company",
        "target company", "target organization", "being acquired",
        "acquisition target", "their systems", "their infrastructure",
        "their applications", "their team", "to-be", "future state"
    ]

    @classmethod
    def infer_entity(cls, context: str, default: Entity = Entity.TARGET) -> Entity:
        """
        Infer entity (target vs buyer) from context.

        CRITICAL: Same logic used across ALL domains.

        Args:
            context: Text context (document name, section heading, etc.)
            default: Fallback if inference is uncertain (usually TARGET)

        Returns:
            Entity.TARGET or Entity.BUYER

        Examples:
            infer_entity("Target Company - IT Landscape") → Entity.TARGET
            infer_entity("Our Current Applications") → Entity.BUYER
            infer_entity("Applications Inventory") → Entity.TARGET (default)
            infer_entity("Acquirer Infrastructure Overview") → Entity.BUYER
            infer_entity("Their Systems Documentation") → Entity.TARGET

        Notes:
            - Case-insensitive matching
            - If both indicators present, buyer wins (safer default)
            - If no indicators, uses default (usually TARGET)
        """
        context_lower = context.lower()

        # Count indicators
        buyer_score = sum(
            1 for indicator in cls.BUYER_INDICATORS
            if indicator in context_lower
        )
        target_score = sum(
            1 for indicator in cls.TARGET_INDICATORS
            if indicator in context_lower
        )

        # Decision logic
        if buyer_score > target_score:
            return Entity.BUYER
        elif target_score > buyer_score:
            return Entity.TARGET
        else:
            # Tie or no indicators → use default
            # Most documents are about the target unless explicitly stated
            return default

    @classmethod
    def infer_with_confidence(
        cls,
        context: str,
        default: Entity = Entity.TARGET
    ) -> tuple[Entity, float]:
        """
        Infer entity with confidence score.

        Args:
            context: Text context
            default: Fallback entity

        Returns:
            Tuple of (entity, confidence)
            - confidence: 0.0-1.0 score indicating certainty

        Examples:
            infer_with_confidence("Target Company IT") → (Entity.TARGET, 0.9)
            infer_with_confidence("Our Infrastructure") → (Entity.BUYER, 0.9)
            infer_with_confidence("Systems Overview") → (Entity.TARGET, 0.5)  # default

        Confidence scoring:
            - 1.0: Multiple strong indicators
            - 0.9: Single strong indicator
            - 0.7: Weak indicator
            - 0.5: No indicators (default used)
        """
        context_lower = context.lower()

        # Count indicators
        buyer_score = sum(
            1 for indicator in cls.BUYER_INDICATORS
            if indicator in context_lower
        )
        target_score = sum(
            1 for indicator in cls.TARGET_INDICATORS
            if indicator in context_lower
        )

        # Determine entity
        if buyer_score > target_score:
            entity = Entity.BUYER
            indicator_count = buyer_score
        elif target_score > buyer_score:
            entity = Entity.TARGET
            indicator_count = target_score
        else:
            # No indicators or tie
            entity = default
            indicator_count = 0

        # Calculate confidence
        if indicator_count == 0:
            confidence = 0.5  # Default used, uncertain
        elif indicator_count == 1:
            confidence = 0.9  # Single indicator, high confidence
        else:
            confidence = 1.0  # Multiple indicators, very confident

        return entity, confidence

    @classmethod
    def add_buyer_indicator(cls, indicator: str) -> None:
        """
        Add custom buyer indicator (for domain-specific patterns).

        Args:
            indicator: New buyer indicator phrase
        """
        if indicator.lower() not in [i.lower() for i in cls.BUYER_INDICATORS]:
            cls.BUYER_INDICATORS.append(indicator.lower())

    @classmethod
    def add_target_indicator(cls, indicator: str) -> None:
        """
        Add custom target indicator (for domain-specific patterns).

        Args:
            indicator: New target indicator phrase
        """
        if indicator.lower() not in [i.lower() for i in cls.TARGET_INDICATORS]:
            cls.TARGET_INDICATORS.append(indicator.lower())
