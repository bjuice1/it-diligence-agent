"""
Tier Classifier for Incremental Updates

Classifies extracted facts into review tiers:
- Tier 1 (Auto-Apply): Low-risk, additive, high confidence
- Tier 2 (Batch Review): Medium risk, quick scan needed
- Tier 3 (Individual Review): Conflicts with verified facts

Phase 2 Steps 34-50
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class Tier(Enum):
    """Review tier for a fact change."""
    AUTO_APPLY = 1      # Tier 1: Apply automatically
    BATCH_REVIEW = 2    # Tier 2: Quick batch review
    INDIVIDUAL_REVIEW = 3  # Tier 3: Individual attention needed


class ChangeCategory(Enum):
    """Category of change being made."""
    ADDITIVE = "additive"           # New fact, no conflict
    CORRECTIVE = "corrective"       # Updates unverified fact
    CONTRADICTORY = "contradictory" # Conflicts with verified
    REMOVAL = "removal"             # Fact being removed


@dataclass
class TierClassificationResult:
    """Result of tier classification for a fact."""
    tier: Tier
    change_category: ChangeCategory
    reasons: List[str] = field(default_factory=list)
    affected_items: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    auto_apply_eligible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier.value,
            "tier_name": self.tier.name,
            "change_category": self.change_category.value,
            "reasons": self.reasons,
            "affected_items": self.affected_items,
            "risk_score": self.risk_score,
            "auto_apply_eligible": self.auto_apply_eligible
        }


@dataclass
class ClassificationStats:
    """Statistics for a batch of classifications."""
    total: int = 0
    tier1_count: int = 0
    tier2_count: int = 0
    tier3_count: int = 0
    auto_apply_count: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "total": self.total,
            "tier1": self.tier1_count,
            "tier2": self.tier2_count,
            "tier3": self.tier3_count,
            "auto_apply": self.auto_apply_count
        }


class TierClassifier:
    """
    Classifies fact changes into review tiers.

    Classification Rules:

    Tier 1 (Auto-Apply):
    - New additive facts (no existing fact to conflict with)
    - High confidence (>= 0.85)
    - Non-critical domains (vendors, contracts, some infrastructure)
    - Updates to unverified facts with minimal change

    Tier 2 (Batch Review):
    - New facts in critical domains (security, compliance)
    - Moderate confidence (0.6 - 0.85)
    - Significant updates to unverified facts
    - Multiple related facts from same document

    Tier 3 (Individual Review):
    - Any conflict with VERIFIED fact
    - Changes that affect risk assessments
    - Facts with multiple contradictions
    - Removal of existing facts
    """

    # Domains requiring extra scrutiny
    CRITICAL_DOMAINS = ["security", "compliance", "data"]
    MEDIUM_DOMAINS = ["applications", "infrastructure"]
    LOW_RISK_DOMAINS = ["vendors", "contracts", "organization"]

    # Confidence thresholds
    HIGH_CONFIDENCE = 0.85
    MEDIUM_CONFIDENCE = 0.6

    # Auto-apply settings (configurable)
    AUTO_APPLY_ENABLED = True
    AUTO_APPLY_MIN_CONFIDENCE = 0.9

    def __init__(self, fact_store=None, fact_merger=None):
        self.fact_store = fact_store
        self.fact_merger = fact_merger
        self.settings = {
            "auto_apply_enabled": self.AUTO_APPLY_ENABLED,
            "auto_apply_min_confidence": self.AUTO_APPLY_MIN_CONFIDENCE,
            "critical_domains": self.CRITICAL_DOMAINS.copy(),
        }

    def configure(self, **kwargs):
        """Configure classifier settings."""
        for key, value in kwargs.items():
            if key in self.settings:
                self.settings[key] = value

    def classify_fact(
        self,
        fact_data: Dict[str, Any],
        existing_fact: Optional[Any] = None,
        has_conflict: bool = False
    ) -> TierClassificationResult:
        """
        Classify a single fact into a review tier.

        Args:
            fact_data: Dictionary of fact data
            existing_fact: Matching existing fact if found
            has_conflict: Whether a conflict was detected

        Returns:
            TierClassificationResult with tier and reasons
        """
        reasons = []
        affected_items = []
        risk_score = 0.0

        domain = fact_data.get("domain", "unknown")
        confidence = fact_data.get("confidence_score", 0.5)

        # Determine change category
        if has_conflict:
            change_category = ChangeCategory.CONTRADICTORY
        elif existing_fact:
            if self._is_verified(existing_fact):
                change_category = ChangeCategory.CONTRADICTORY
            else:
                change_category = ChangeCategory.CORRECTIVE
        else:
            change_category = ChangeCategory.ADDITIVE

        # === Tier 3 Checks (highest priority) ===

        # Check for verified fact conflict
        if has_conflict:
            reasons.append("Conflicts with verified fact")
            risk_score += 0.5
            return TierClassificationResult(
                tier=Tier.INDIVIDUAL_REVIEW,
                change_category=change_category,
                reasons=reasons,
                affected_items=self._get_affected_items(fact_data),
                risk_score=min(1.0, risk_score),
                auto_apply_eligible=False
            )

        # Check if updating a verified fact
        if existing_fact and self._is_verified(existing_fact):
            reasons.append("Updates verified fact - requires review")
            risk_score += 0.4
            return TierClassificationResult(
                tier=Tier.INDIVIDUAL_REVIEW,
                change_category=ChangeCategory.CONTRADICTORY,
                reasons=reasons,
                affected_items=self._get_affected_items(fact_data),
                risk_score=min(1.0, risk_score),
                auto_apply_eligible=False
            )

        # Check for risk impact
        if self._affects_risks(fact_data):
            reasons.append("May affect risk assessments")
            risk_score += 0.3
            return TierClassificationResult(
                tier=Tier.INDIVIDUAL_REVIEW,
                change_category=change_category,
                reasons=reasons,
                affected_items=self._get_affected_items(fact_data),
                risk_score=min(1.0, risk_score),
                auto_apply_eligible=False
            )

        # === Tier 2 Checks ===

        # Critical domain + new fact
        if domain in self.settings["critical_domains"] and not existing_fact:
            reasons.append(f"New fact in critical domain ({domain})")
            risk_score += 0.2
            return TierClassificationResult(
                tier=Tier.BATCH_REVIEW,
                change_category=change_category,
                reasons=reasons,
                affected_items=affected_items,
                risk_score=min(1.0, risk_score),
                auto_apply_eligible=False
            )

        # Medium confidence
        if self.MEDIUM_CONFIDENCE <= confidence < self.HIGH_CONFIDENCE:
            reasons.append(f"Moderate confidence ({confidence:.2f})")
            risk_score += 0.15
            return TierClassificationResult(
                tier=Tier.BATCH_REVIEW,
                change_category=change_category,
                reasons=reasons,
                affected_items=affected_items,
                risk_score=min(1.0, risk_score),
                auto_apply_eligible=False
            )

        # Significant update to unverified fact
        if existing_fact and not self._is_verified(existing_fact):
            if self._is_significant_change(existing_fact, fact_data):
                reasons.append("Significant change to existing fact")
                risk_score += 0.1
                return TierClassificationResult(
                    tier=Tier.BATCH_REVIEW,
                    change_category=change_category,
                    reasons=reasons,
                    affected_items=affected_items,
                    risk_score=min(1.0, risk_score),
                    auto_apply_eligible=False
                )

        # === Tier 1 (Auto-Apply) ===

        # All checks passed - eligible for auto-apply
        auto_eligible = (
            self.settings["auto_apply_enabled"] and
            confidence >= self.settings["auto_apply_min_confidence"] and
            change_category == ChangeCategory.ADDITIVE and
            domain in self.LOW_RISK_DOMAINS
        )

        if auto_eligible:
            reasons.append("High confidence, additive, low-risk domain")
        else:
            reasons.append("Eligible for quick batch review")
            if confidence >= self.HIGH_CONFIDENCE:
                reasons.append(f"High confidence ({confidence:.2f})")
            if change_category == ChangeCategory.ADDITIVE:
                reasons.append("Additive change (new fact)")

        return TierClassificationResult(
            tier=Tier.AUTO_APPLY,
            change_category=change_category,
            reasons=reasons,
            affected_items=affected_items,
            risk_score=min(1.0, risk_score),
            auto_apply_eligible=auto_eligible
        )

    def classify_batch(
        self,
        facts: List[Dict[str, Any]],
        source_document: str = ""
    ) -> Tuple[Dict[Tier, List[Dict]], ClassificationStats]:
        """
        Classify a batch of facts from a document.

        Args:
            facts: List of fact dictionaries
            source_document: Source document name

        Returns:
            Tuple of (classified facts by tier, statistics)
        """
        classified = {
            Tier.AUTO_APPLY: [],
            Tier.BATCH_REVIEW: [],
            Tier.INDIVIDUAL_REVIEW: []
        }

        stats = ClassificationStats(total=len(facts))

        for fact_data in facts:
            # Find existing fact
            existing = None
            has_conflict = False

            if self.fact_merger:
                from tools_v2.fact_merger import MergeAction
                action, existing, conflict = self.fact_merger.determine_action(
                    fact_data, source_document
                )
                has_conflict = action == MergeAction.CONFLICT
            elif self.fact_store:
                existing = self._find_existing_fact(fact_data)

            # Classify
            result = self.classify_fact(fact_data, existing, has_conflict)

            # Add to appropriate tier
            classified_fact = {
                "fact": fact_data,
                "classification": result.to_dict(),
                "existing_fact_id": existing.fact_id if existing else None
            }
            classified[result.tier].append(classified_fact)

            # Update stats
            if result.tier == Tier.AUTO_APPLY:
                stats.tier1_count += 1
                if result.auto_apply_eligible:
                    stats.auto_apply_count += 1
            elif result.tier == Tier.BATCH_REVIEW:
                stats.tier2_count += 1
            else:
                stats.tier3_count += 1

        return classified, stats

    def _is_verified(self, fact) -> bool:
        """Check if a fact is verified."""
        if hasattr(fact, 'verification_status'):
            from stores.fact_store import VerificationStatus
            return fact.verification_status == VerificationStatus.CONFIRMED
        return getattr(fact, 'verified', False)

    def _is_significant_change(
        self,
        existing_fact,
        new_fact_data: Dict[str, Any]
    ) -> bool:
        """Determine if change is significant."""
        # Check status change
        if new_fact_data.get("status") != existing_fact.status:
            return True

        # Check item name change
        if new_fact_data.get("item") and new_fact_data["item"] != existing_fact.item:
            return True

        # Check detail changes
        new_details = new_fact_data.get("details", {})
        existing_details = existing_fact.details or {}

        # Count changed fields
        changes = 0
        for key, value in new_details.items():
            if key not in existing_details or existing_details[key] != value:
                changes += 1

        return changes >= 2  # Significant if 2+ fields changed

    def _affects_risks(self, fact_data: Dict[str, Any]) -> bool:
        """Check if fact change might affect risk assessments."""
        # Security facts always affect risks
        if fact_data.get("domain") == "security":
            return True

        # Check for risk-related keywords
        item = fact_data.get("item", "").lower()
        status = fact_data.get("status", "").lower()

        risk_keywords = [
            "vulnerability", "breach", "incident", "risk",
            "critical", "failure", "outage", "expired",
            "non-compliant", "audit finding"
        ]

        for keyword in risk_keywords:
            if keyword in item or keyword in status:
                return True

        return False

    def _get_affected_items(self, fact_data: Dict[str, Any]) -> List[str]:
        """Get items that might be affected by this fact change."""
        affected = []

        # This would integrate with dependency tracking (Phase 4)
        # For now, return empty list
        return affected

    def _find_existing_fact(self, fact_data: Dict[str, Any]):
        """Find existing fact matching the new fact data."""
        if not self.fact_store:
            return None

        domain = fact_data.get("domain", "")
        item = fact_data.get("item", "").lower()

        for fact in self.fact_store.facts:
            if fact.domain == domain and fact.item.lower() == item:
                return fact

        return None

    def get_auto_apply_facts(
        self,
        classified: Dict[Tier, List[Dict]]
    ) -> List[Dict]:
        """Get facts eligible for auto-apply."""
        return [
            item for item in classified.get(Tier.AUTO_APPLY, [])
            if item["classification"]["auto_apply_eligible"]
        ]

    def get_review_summary(
        self,
        classified: Dict[Tier, List[Dict]],
        stats: ClassificationStats
    ) -> Dict[str, Any]:
        """Get summary for review UI."""
        return {
            "totals": stats.to_dict(),
            "tier1": {
                "name": "Auto-Apply",
                "description": "Low-risk changes that can be applied automatically",
                "count": stats.tier1_count,
                "auto_apply_count": stats.auto_apply_count,
                "items": [
                    {
                        "item": f["fact"].get("item"),
                        "domain": f["fact"].get("domain"),
                        "confidence": f["fact"].get("confidence_score", 0),
                        "auto_eligible": f["classification"]["auto_apply_eligible"]
                    }
                    for f in classified.get(Tier.AUTO_APPLY, [])[:10]  # Limit preview
                ]
            },
            "tier2": {
                "name": "Batch Review",
                "description": "Quick scan recommended before applying",
                "count": stats.tier2_count,
                "items": [
                    {
                        "item": f["fact"].get("item"),
                        "domain": f["fact"].get("domain"),
                        "reasons": f["classification"]["reasons"]
                    }
                    for f in classified.get(Tier.BATCH_REVIEW, [])[:10]
                ]
            },
            "tier3": {
                "name": "Individual Review",
                "description": "Requires careful individual review",
                "count": stats.tier3_count,
                "items": [
                    {
                        "item": f["fact"].get("item"),
                        "domain": f["fact"].get("domain"),
                        "reasons": f["classification"]["reasons"],
                        "existing_fact_id": f["existing_fact_id"]
                    }
                    for f in classified.get(Tier.INDIVIDUAL_REVIEW, [])
                ]
            }
        }
