"""Application aggregate root - SINGLE SOURCE OF TRUTH for application inventory."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from difflib import SequenceMatcher

from domain.value_objects.application_id import ApplicationId, normalize_application_name
from domain.value_objects.entity import Entity
from domain.value_objects.money import Money
from domain.entities.observation import Observation


@dataclass
class Application:
    """Application aggregate root - THE canonical source for application data.

    This is the SINGLE SOURCE OF TRUTH that replaces:
    - InventoryItem (was canonical but underutilized)
    - Fact (was observations, but treated as separate truth)
    - Database application records
    - JSON file exports

    KEY INSIGHT: Application OWNS its observations (composition),
    rather than observations existing separately and linking back.

    Identity Stability:
    - id is DETERMINISTIC: same (name, entity) → same id across runs
    - This enables reliable deduplication

    Data Quality:
    - observations list contains ALL sources (table, LLM, manual)
    - Derived fields (cost, vendor) are computed from observations
    - Highest confidence observation wins for each field
    """

    # === IDENTITY (Immutable) ===
    id: ApplicationId
    entity: Entity

    # === CORE DATA (Mutable) ===
    name: str  # Canonical name (may differ slightly from observations)
    vendor: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    hosting: Optional[str] = None  # "saas", "cloud", "on-premise"

    # === EVIDENCE (Observations) ===
    observations: List[Observation] = field(default_factory=list)

    # === DERIVED/COMPUTED FIELDS ===
    cost: Optional[Money] = None
    criticality: Optional[str] = None  # "critical", "high", "medium", "low"
    user_count: Optional[int] = None

    # === STATUS ===
    status: str = "active"  # "active", "removed", "deprecated"
    removal_reason: str = ""

    # === METADATA ===
    deal_id: str = ""  # For multi-tenant isolation
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    # =========================================================================
    # PUBLIC API - Business Logic
    # =========================================================================

    def add_observation(self, obs: Observation) -> None:
        """Add new observation and update derived fields.

        This is the PRIMARY METHOD for updating application data.
        Don't set vendor/cost directly - add observation and let
        _update_derived_fields() compute the canonical values.
        """
        self.observations.append(obs)
        self._update_derived_fields()
        self.updated_at = datetime.now().isoformat()

    def merge(self, other: "Application") -> None:
        """Merge another application into this one (deduplication).

        Use case: Two Application objects exist for same real-world app
        (should be impossible with proper ID generation, but safety net).

        Args:
            other: Application to merge into this one

        Raises:
            ValueError: If IDs don't match (can't merge different apps)
        """
        if self.id != other.id:
            raise ValueError(
                f"Cannot merge apps with different IDs: {self.id} vs {other.id}"
            )

        # Merge observations
        self.observations.extend(other.observations)

        # Recalculate derived fields
        self._update_derived_fields()

        self.updated_at = datetime.now().isoformat()

    def is_duplicate_of(self, other: "Application", threshold: float = 0.65) -> bool:
        """Check if this app is a duplicate of another using fuzzy matching.

        This is a SAFETY NET for cases where ID generation didn't catch duplicates.

        Args:
            other: Application to compare against
            threshold: Similarity threshold 0.0-1.0 (default 0.65)

        Returns:
            True if likely duplicate, False otherwise

        Examples:
            >>> app1 = Application(name="Salesforce", entity=Entity.TARGET, ...)
            >>> app2 = Application(name="Salesforce CRM", entity=Entity.TARGET, ...)
            >>> app1.is_duplicate_of(app2)
            True  # Normalized names match
        """
        # Same ID = definitely duplicate
        if self.id == other.id:
            return True

        # Different entity = definitely NOT duplicate
        if self.entity != other.entity:
            return False

        # Fuzzy name match
        name1_normalized = normalize_application_name(self.name)
        name2_normalized = normalize_application_name(other.name)

        name_similarity = SequenceMatcher(
            None,
            name1_normalized,
            name2_normalized
        ).ratio()

        if name_similarity >= threshold:
            # Optional: Boost confidence if vendor also matches
            if self.vendor and other.vendor:
                vendor_similarity = SequenceMatcher(
                    None,
                    self.vendor.lower(),
                    other.vendor.lower()
                ).ratio()

                # Weighted average (name 70%, vendor 30%)
                overall_similarity = (name_similarity * 0.7) + (vendor_similarity * 0.3)
                return overall_similarity >= threshold

            return True

        return False

    def remove(self, reason: str) -> None:
        """Mark application as removed."""
        self.status = "removed"
        self.removal_reason = reason
        self.updated_at = datetime.now().isoformat()

    def restore(self) -> None:
        """Restore removed application to active status."""
        self.status = "active"
        self.removal_reason = ""
        self.updated_at = datetime.now().isoformat()

    # =========================================================================
    # PRIVATE METHODS - Internal Logic
    # =========================================================================

    def _update_derived_fields(self) -> None:
        """Update cost, vendor, etc. from observations.

        STRATEGY: Choose highest-confidence observation for each field.
        - Deterministic (table) observations have confidence=1.0
        - LLM observations have confidence 0.7-0.9
        - Result: Table data wins ties
        """
        if not self.observations:
            return

        # Sort by confidence (highest first)
        sorted_obs = sorted(
            self.observations,
            key=lambda o: o.confidence,
            reverse=True
        )

        # Extract best values for each field
        for obs in sorted_obs:
            data = obs.extracted_data

            # Vendor (if not already set by higher-confidence observation)
            if not self.vendor and data.get("vendor"):
                self.vendor = str(data["vendor"])

            # Version
            if not self.version and data.get("version"):
                self.version = str(data["version"])

            # Category
            if not self.category and data.get("category"):
                self.category = str(data["category"])

            # Hosting
            if not self.hosting and data.get("hosting"):
                self.hosting = str(data["hosting"])

            # Cost (convert to Money value object)
            if not self.cost and data.get("cost"):
                try:
                    cost_amount = float(data["cost"])
                    cost_status = data.get("cost_status", "unknown")
                    self.cost = Money.from_float(cost_amount, status=cost_status)
                except (ValueError, TypeError):
                    pass  # Skip invalid cost data

            # Criticality
            if not self.criticality and data.get("criticality"):
                self.criticality = str(data["criticality"])

            # User count
            if not self.user_count and data.get("users"):
                try:
                    # Handle both "100" and "~100" formats
                    user_str = str(data["users"]).replace("~", "").replace(",", "")
                    self.user_count = int(user_str)
                except (ValueError, TypeError):
                    pass  # Skip invalid user count

    # =========================================================================
    # QUERIES - Read-Only Properties
    # =========================================================================

    @property
    def is_active(self) -> bool:
        """Check if application is active (not removed)."""
        return self.status == "active"

    @property
    def observation_count(self) -> int:
        """Count of observations (evidence sources)."""
        return len(self.observations)

    @property
    def has_table_data(self) -> bool:
        """Check if any observation came from deterministic table parser."""
        return any(obs.is_deterministic() for obs in self.observations)

    @property
    def has_llm_data(self) -> bool:
        """Check if any observation came from LLM extraction."""
        return any(obs.is_llm_extracted() for obs in self.observations)

    @property
    def data_quality_score(self) -> float:
        """Calculate overall data quality score 0.0-1.0.

        Factors:
        - Observation count (more evidence = higher quality)
        - Average confidence of observations
        - Field completeness (how many fields are filled)
        """
        if not self.observations:
            return 0.0

        # Average observation confidence
        avg_confidence = sum(o.confidence for o in self.observations) / len(self.observations)

        # Field completeness (% of expected fields filled)
        expected_fields = ["name", "vendor", "category", "cost", "user_count"]
        filled_fields = sum(1 for field in expected_fields if getattr(self, field))
        completeness = filled_fields / len(expected_fields)

        # Observation count bonus (capped at 5 observations)
        obs_bonus = min(len(self.observations) / 5.0, 1.0)

        # Weighted average
        quality = (
            avg_confidence * 0.5 +
            completeness * 0.3 +
            obs_bonus * 0.2
        )

        return min(quality, 1.0)  # Cap at 1.0

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> dict:
        """Convert to dictionary for API/UI."""
        return {
            "id": self.id.value,
            "entity": self.entity.value,
            "name": self.name,
            "vendor": self.vendor,
            "version": self.version,
            "category": self.category,
            "hosting": self.hosting,
            "cost": {
                "amount": float(self.cost.amount),
                "currency": self.cost.currency,
                "status": self.cost.status,
                "formatted": self.cost.format()
            } if self.cost else None,
            "criticality": self.criticality,
            "user_count": self.user_count,
            "status": self.status,
            "observation_count": self.observation_count,
            "data_quality_score": self.data_quality_score,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __str__(self) -> str:
        """String representation for logging."""
        return f"Application({self.id.value}: {self.name}, entity={self.entity.value})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"Application(id={self.id.value!r}, name={self.name!r}, "
            f"entity={self.entity.value!r}, observations={len(self.observations)})"
        )
