"""
Correction Pipeline - Handles Human Corrections with Ripple Effects

When a human corrects a fact:
1. Validate the correction
2. Record the correction with audit trail
3. Update the fact in the store
4. Calculate ripple effects (derived values that need updating)
5. Check for new inconsistencies created by the correction
6. Update validation state

This ensures corrections are tracked and their effects propagate correctly.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from models.validation_models import (
    ValidationFlag, FlagSeverity, FlagCategory,
    CorrectionRecord, RippleEffect, CorrectionResult,
    generate_flag_id, generate_correction_id
)
from stores.validation_store import ValidationStore
from stores.correction_store import CorrectionStore

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Expected salary ranges by category (for sanity checks)
EXPECTED_SALARY_RANGES = {
    "leadership": (150000, 350000),
    "applications": (80000, 180000),
    "infrastructure": (70000, 160000),
    "security": (90000, 200000),
    "service_desk": (45000, 100000),
    "pmo": (80000, 170000),
    "data": (85000, 180000),
    "development": (90000, 200000),
    "default": (50000, 200000),
}

# Fields that trigger derived value recalculation
HEADCOUNT_FIELDS = ["headcount", "fte", "staff_count", "team_size"]
COST_FIELDS = ["personnel_cost", "total_cost", "budget", "spend"]


# =============================================================================
# CORRECTION PIPELINE CLASS
# =============================================================================

class CorrectionPipeline:
    """
    Handles human corrections with full audit trail and ripple effects.

    Responsibilities:
    - Apply corrections to facts
    - Record corrections for audit
    - Calculate and apply ripple effects
    - Check for new inconsistencies
    - Update validation state
    """

    def __init__(
        self,
        fact_store,  # FactStore instance
        validation_store: ValidationStore,
        correction_store: CorrectionStore,
        api_key: Optional[str] = None
    ):
        """
        Initialize the correction pipeline.

        Args:
            fact_store: Store containing the facts
            validation_store: Store for validation state
            correction_store: Store for correction records
            api_key: Optional API key for consistency checking
        """
        self.fact_store = fact_store
        self.validation_store = validation_store
        self.correction_store = correction_store
        self.api_key = api_key

    # =========================================================================
    # MAIN CORRECTION METHOD
    # =========================================================================

    def apply_correction(
        self,
        fact_id: str,
        corrected_fields: Dict[str, Any],
        reason: str,
        corrected_by: str,
        new_evidence: Optional[str] = None
    ) -> CorrectionResult:
        """
        Apply a human correction to a fact.

        Args:
            fact_id: ID of the fact to correct
            corrected_fields: Dict of field -> new_value
            reason: Reason for the correction
            corrected_by: Username/ID of person making correction
            new_evidence: Optional new evidence quote

        Returns:
            CorrectionResult with status and any ripple effects
        """
        logger.info(f"Applying correction to {fact_id} by {corrected_by}")

        # Step 1: Validate fact exists
        fact = self._get_fact(fact_id)
        if not fact:
            return CorrectionResult(
                success=False,
                correction_id="",
                original_value={},
                corrected_value=corrected_fields,
                derived_values_updated=[],
                new_flags_created=[],
                message=f"Fact {fact_id} not found"
            )

        # Step 2: Store original values
        original_value = self._get_original_values(fact, corrected_fields)

        # Step 3: Generate correction ID
        correction_id = generate_correction_id()

        # Step 4: Record correction
        correction_record = CorrectionRecord(
            correction_id=correction_id,
            fact_id=fact_id,
            timestamp=datetime.now(),
            corrected_by=corrected_by,
            original_value=original_value,
            corrected_value=corrected_fields,
            reason=reason,
            new_evidence=new_evidence
        )

        # Step 5: Update the fact
        updated_fact = self._apply_field_updates(fact, corrected_fields)
        if new_evidence:
            updated_fact = self._update_evidence(updated_fact, new_evidence)

        self._save_fact(updated_fact)

        # Step 6: Calculate ripple effects
        ripple_effects = self._calculate_ripple_effects(
            updated_fact, corrected_fields
        )

        # Apply ripple effects
        for effect in ripple_effects:
            self._apply_ripple_effect(effect)

        # Step 7: Check for new inconsistencies
        new_flags = self._check_for_new_inconsistencies(
            updated_fact, corrected_fields
        )

        # Add flags to validation store
        for flag in new_flags:
            self.validation_store.add_flag(
                fact_id=fact_id,
                flag=flag,
                source="correction_ripple"
            )

        # Step 8: Update validation state
        self.validation_store.mark_human_corrected(
            fact_id=fact_id,
            corrected_by=corrected_by,
            correction_id=correction_id,
            original=original_value,
            corrected=corrected_fields,
            notes=reason
        )

        # Step 9: Record correction with ripple effects
        self.correction_store.record_correction(
            record=correction_record,
            ripple_effects=ripple_effects
        )

        logger.info(
            f"Correction {correction_id} applied: "
            f"{len(ripple_effects)} ripple effects, {len(new_flags)} new flags"
        )

        return CorrectionResult(
            success=True,
            correction_id=correction_id,
            original_value=original_value,
            corrected_value=corrected_fields,
            derived_values_updated=ripple_effects,
            new_flags_created=new_flags,
            message="Correction applied successfully"
        )

    # =========================================================================
    # FACT ACCESS METHODS
    # =========================================================================

    def _get_fact(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """Get a fact by ID."""
        if hasattr(self.fact_store, 'get_fact'):
            fact = self.fact_store.get_fact(fact_id)
            if fact:
                return fact.to_dict() if hasattr(fact, 'to_dict') else fact
        return None

    def _get_original_values(
        self,
        fact: Dict[str, Any],
        corrected_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract original values for fields being corrected."""
        original = {}
        details = fact.get("details", {})

        for field in corrected_fields.keys():
            if field in details:
                original[field] = details[field]
            elif field in fact:
                original[field] = fact[field]
            else:
                original[field] = None

        return original

    def _apply_field_updates(
        self,
        fact: Dict[str, Any],
        corrected_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply field updates to fact."""
        updated = fact.copy()
        if "details" not in updated:
            updated["details"] = {}

        for field, new_value in corrected_fields.items():
            # Update in details dict
            updated["details"][field] = new_value

            # Also update top-level if it's a common field
            if field in ["item", "category", "domain"]:
                updated[field] = new_value

        return updated

    def _update_evidence(
        self,
        fact: Dict[str, Any],
        new_evidence: str
    ) -> Dict[str, Any]:
        """Update evidence in fact."""
        updated = fact.copy()

        if "evidence" not in updated:
            updated["evidence"] = {}

        if isinstance(updated["evidence"], dict):
            updated["evidence"]["exact_quote"] = new_evidence
            updated["evidence"]["updated_at"] = datetime.now().isoformat()
        else:
            updated["evidence"] = {
                "exact_quote": new_evidence,
                "updated_at": datetime.now().isoformat()
            }

        return updated

    def _save_fact(self, fact: Dict[str, Any]):
        """Save updated fact to store."""
        if hasattr(self.fact_store, 'update_fact'):
            self.fact_store.update_fact(fact)
        elif hasattr(self.fact_store, 'save_fact'):
            self.fact_store.save_fact(fact)

    # =========================================================================
    # RIPPLE EFFECT CALCULATION
    # =========================================================================

    def _calculate_ripple_effects(
        self,
        corrected_fact: Dict[str, Any],
        corrected_fields: Dict[str, Any]
    ) -> List[RippleEffect]:
        """
        Calculate ripple effects from a correction.

        Identifies derived values that need to be updated.
        """
        effects = []

        # Check for headcount changes
        headcount_changed = any(
            field in corrected_fields for field in HEADCOUNT_FIELDS
        )
        if headcount_changed:
            headcount_effects = self._calculate_headcount_ripples(
                corrected_fact, corrected_fields
            )
            effects.extend(headcount_effects)

        # Check for cost changes
        cost_changed = any(
            field in corrected_fields for field in COST_FIELDS
        )
        if cost_changed:
            cost_effects = self._calculate_cost_ripples(
                corrected_fact, corrected_fields
            )
            effects.extend(cost_effects)

        return effects

    def _calculate_headcount_ripples(
        self,
        corrected_fact: Dict[str, Any],
        corrected_fields: Dict[str, Any]
    ) -> List[RippleEffect]:
        """Calculate ripple effects for headcount changes."""
        effects = []
        domain = corrected_fact.get("domain", "")

        # Get new headcount value
        new_headcount = None
        for field in HEADCOUNT_FIELDS:
            if field in corrected_fields:
                new_headcount = self._parse_numeric(corrected_fields[field])
                break

        if new_headcount is None:
            return effects

        # Recalculate total headcount for domain
        if domain == "organization":
            total_effect = self._recalculate_total_headcount(
                corrected_fact, new_headcount
            )
            if total_effect:
                effects.append(total_effect)

        # Recalculate cost per person if we have cost
        details = corrected_fact.get("details", {})
        personnel_cost = None
        for field in COST_FIELDS:
            if field in details:
                personnel_cost = self._parse_cost(details[field])
                break

        if personnel_cost and new_headcount > 0:
            old_cost_per_person = details.get("cost_per_person")
            new_cost_per_person = personnel_cost / new_headcount

            effects.append(RippleEffect(
                field="cost_per_person",
                old_value=old_cost_per_person,
                new_value=new_cost_per_person,
                reason=f"Recalculated due to headcount change to {new_headcount}",
                affected_fact_ids=[corrected_fact.get("fact_id", "")]
            ))

        return effects

    def _recalculate_total_headcount(
        self,
        corrected_fact: Dict[str, Any],
        new_headcount: int
    ) -> Optional[RippleEffect]:
        """Recalculate total IT headcount from all teams."""
        if not hasattr(self.fact_store, 'get_facts_by_domain'):
            return None

        domain = corrected_fact.get("domain", "organization")
        all_facts = self.fact_store.get_facts_by_domain(domain)

        if not all_facts:
            return None

        # Sum headcounts from all central_it facts
        total = 0
        affected_ids = []

        for fact in all_facts:
            if isinstance(fact, dict):
                fact_dict = fact
            elif hasattr(fact, 'to_dict'):
                fact_dict = fact.to_dict()
            else:
                continue

            if fact_dict.get("category") == "central_it":
                details = fact_dict.get("details", {})
                fact_id = fact_dict.get("fact_id", "")

                # Use new value if this is the corrected fact
                if fact_id == corrected_fact.get("fact_id"):
                    total += new_headcount
                else:
                    for field in HEADCOUNT_FIELDS:
                        if field in details:
                            total += self._parse_numeric(details[field])
                            break

                affected_ids.append(fact_id)

        # Get old total if it exists
        old_total = None
        if hasattr(self.fact_store, 'get_derived_value'):
            old_total = self.fact_store.get_derived_value("total_it_headcount")

        # Store new total
        if hasattr(self.fact_store, 'set_derived_value'):
            self.fact_store.set_derived_value(
                key="total_it_headcount",
                value=total,
                derived_from=affected_ids,
                note="Recalculated after headcount correction"
            )

        return RippleEffect(
            field="total_it_headcount",
            old_value=old_total,
            new_value=total,
            reason="Recalculated from team headcounts after correction",
            affected_fact_ids=affected_ids
        )

    def _calculate_cost_ripples(
        self,
        corrected_fact: Dict[str, Any],
        corrected_fields: Dict[str, Any]
    ) -> List[RippleEffect]:
        """Calculate ripple effects for cost changes."""
        effects = []

        # Get new cost value
        new_cost = None
        for field in COST_FIELDS:
            if field in corrected_fields:
                new_cost = self._parse_cost(corrected_fields[field])
                break

        if new_cost is None:
            return effects

        # Recalculate cost per person if we have headcount
        details = corrected_fact.get("details", {})
        headcount = None
        for field in HEADCOUNT_FIELDS:
            if field in details:
                headcount = self._parse_numeric(details[field])
                break

        if headcount and headcount > 0:
            old_cost_per_person = details.get("cost_per_person")
            new_cost_per_person = new_cost / headcount

            effects.append(RippleEffect(
                field="cost_per_person",
                old_value=old_cost_per_person,
                new_value=new_cost_per_person,
                reason=f"Recalculated due to cost change to ${new_cost:,.0f}",
                affected_fact_ids=[corrected_fact.get("fact_id", "")]
            ))

        return effects

    def _apply_ripple_effect(self, effect: RippleEffect):
        """Apply a ripple effect - update the derived value."""
        # Update each affected fact
        for fact_id in effect.affected_fact_ids:
            fact = self._get_fact(fact_id)
            if fact:
                if "details" not in fact:
                    fact["details"] = {}
                fact["details"][effect.field] = effect.new_value
                self._save_fact(fact)

        logger.debug(
            f"Applied ripple effect: {effect.field} = {effect.new_value}"
        )

    # =========================================================================
    # INCONSISTENCY CHECKING
    # =========================================================================

    def _check_for_new_inconsistencies(
        self,
        corrected_fact: Dict[str, Any],
        corrected_fields: Dict[str, Any]
    ) -> List[ValidationFlag]:
        """Check if the correction creates new inconsistencies."""
        flags = []

        # Check 1: Cost per person sanity
        cost_flag = self._check_cost_per_person_sanity(
            corrected_fact, corrected_fields
        )
        if cost_flag:
            flags.append(cost_flag)

        # Check 2: Headcount sanity
        headcount_flag = self._check_headcount_sanity(
            corrected_fact, corrected_fields
        )
        if headcount_flag:
            flags.append(headcount_flag)

        # Check 3: Cross-reference consistency
        cross_ref_flags = self._check_cross_reference_consistency(
            corrected_fact, corrected_fields
        )
        flags.extend(cross_ref_flags)

        return flags

    def _check_cost_per_person_sanity(
        self,
        corrected_fact: Dict[str, Any],
        corrected_fields: Dict[str, Any]
    ) -> Optional[ValidationFlag]:
        """Check if cost per person is reasonable after correction."""
        details = corrected_fact.get("details", {})
        category = corrected_fact.get("category", "default")

        # Get headcount
        headcount = None
        for field in HEADCOUNT_FIELDS:
            value = corrected_fields.get(field) or details.get(field)
            if value:
                headcount = self._parse_numeric(value)
                break

        # Get cost
        cost = None
        for field in COST_FIELDS:
            value = corrected_fields.get(field) or details.get(field)
            if value:
                cost = self._parse_cost(value)
                break

        if not headcount or not cost or headcount == 0:
            return None

        cost_per_person = cost / headcount
        expected_range = EXPECTED_SALARY_RANGES.get(
            category, EXPECTED_SALARY_RANGES["default"]
        )

        # Check if outside expected range
        if cost_per_person < expected_range[0] * 0.7:
            return ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.CONSISTENCY,
                message=(
                    f"Cost per person (${cost_per_person:,.0f}) is unusually low "
                    f"for {category} (expected ${expected_range[0]:,}-${expected_range[1]:,})"
                ),
                suggestion="Verify the cost figure - personnel cost may be understated"
            )
        elif cost_per_person > expected_range[1] * 1.3:
            return ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.CONSISTENCY,
                message=(
                    f"Cost per person (${cost_per_person:,.0f}) is unusually high "
                    f"for {category} (expected ${expected_range[0]:,}-${expected_range[1]:,})"
                ),
                suggestion="Verify the cost figure - may include non-personnel costs"
            )

        return None

    def _check_headcount_sanity(
        self,
        corrected_fact: Dict[str, Any],
        corrected_fields: Dict[str, Any]
    ) -> Optional[ValidationFlag]:
        """Check if headcount is reasonable after correction."""
        # Get new headcount
        new_headcount = None
        for field in HEADCOUNT_FIELDS:
            if field in corrected_fields:
                new_headcount = self._parse_numeric(corrected_fields[field])
                break

        if new_headcount is None:
            return None

        # Check for unreasonable values
        if new_headcount < 0:
            return ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.ERROR,
                category=FlagCategory.ACCURACY,
                message="Headcount cannot be negative",
                suggestion="Correct the headcount value"
            )

        if new_headcount > 10000:
            return ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.ACCURACY,
                message=f"Very high headcount ({new_headcount}) - please verify",
                suggestion="Confirm this is the correct headcount for this team"
            )

        return None

    def _check_cross_reference_consistency(
        self,
        corrected_fact: Dict[str, Any],
        corrected_fields: Dict[str, Any]
    ) -> List[ValidationFlag]:
        """Check cross-reference consistency after correction."""
        # This would check against other domains
        # For now, return empty list - full implementation in Phase 5
        return []

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _parse_numeric(self, value: Any) -> int:
        """Parse a numeric value from various formats."""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # Extract number from string
            match = re.search(r'[\d,]+', value.replace(',', ''))
            if match:
                return int(match.group().replace(',', ''))
        return 0

    def _parse_cost(self, value: Any) -> float:
        """Parse a cost value from various formats."""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.upper().replace(",", "").replace("$", "")

            multiplier = 1
            if "M" in value:
                multiplier = 1_000_000
                value = value.replace("M", "")
            elif "K" in value:
                multiplier = 1_000
                value = value.replace("K", "")

            try:
                return float(value) * multiplier
            except ValueError:
                pass

        return 0.0


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_correction_pipeline(
    fact_store,
    validation_store: ValidationStore,
    correction_store: CorrectionStore,
    api_key: Optional[str] = None
) -> CorrectionPipeline:
    """Create a correction pipeline instance."""
    return CorrectionPipeline(
        fact_store=fact_store,
        validation_store=validation_store,
        correction_store=correction_store,
        api_key=api_key
    )


def apply_correction(
    fact_store,
    validation_store: ValidationStore,
    correction_store: CorrectionStore,
    fact_id: str,
    corrected_fields: Dict[str, Any],
    reason: str,
    corrected_by: str,
    new_evidence: Optional[str] = None
) -> CorrectionResult:
    """Convenience function to apply a correction."""
    pipeline = CorrectionPipeline(
        fact_store=fact_store,
        validation_store=validation_store,
        correction_store=correction_store
    )
    return pipeline.apply_correction(
        fact_id=fact_id,
        corrected_fields=corrected_fields,
        reason=reason,
        corrected_by=corrected_by,
        new_evidence=new_evidence
    )
