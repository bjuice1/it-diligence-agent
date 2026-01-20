"""
Three-Stage Refinement Integration

Bridges the RefinementSession with the Three-Stage Reasoning architecture.

This module enables:
1. Running initial three-stage analysis within a refinement session
2. Applying refinements (TSA, activity overrides, etc.) to three-stage output
3. Fast re-analysis (Stage 1 + 2 only) during refinement iterations
4. Full validation when preparing final output

Cost Model:
- Initial analysis: ~$0.30-0.50 (all 3 stages)
- Fast refinement: ~$0.15-0.20 (Stage 1 + 2 only)
- Pre-client validation: ~$0.10-0.15 (Stage 3 only)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import hashlib

from tools_v2.three_stage_reasoning import (
    run_three_stage_analysis,
    stage1_identify_considerations,
    stage2_match_activities,
    stage3_validate,
    ThreeStageOutput,
    IdentifiedConsideration,
    MatchedActivity,
    ValidationResult,
    format_three_stage_output,
)
from tools_v2.refinement_engine import (
    RefinementSession,
    RefinementInput,
    RefinementType,
    RefinementResult,
    AnalysisSnapshot,
)

logger = logging.getLogger(__name__)


# =============================================================================
# THREE-STAGE REFINEMENT SESSION
# =============================================================================

@dataclass
class ThreeStageSnapshot:
    """Snapshot of three-stage analysis at a point in time."""

    snapshot_id: str
    timestamp: str
    trigger: str

    # Stage outputs
    consideration_count: int
    activity_count: int
    tsa_count: int

    # Costs
    total_cost_range: Tuple[float, float]
    llm_cost: float

    # Validation
    confidence_score: float

    # Hash for comparison
    content_hash: str


class ThreeStageRefinementSession:
    """
    Refinement session that uses three-stage reasoning.

    Combines:
    - Three-stage analysis (LLM → Rules → LLM)
    - Iterative refinement support
    - Cost-efficient mode switching

    Usage:
        session = ThreeStageRefinementSession.create(fact_store, "carveout")

        # Initial full analysis
        result = session.run_initial_analysis()

        # Add refinements
        session.add_tsa_requirement(...)
        session.add_activity_override(...)

        # Fast re-analysis (Stage 1+2 only)
        result = session.apply_refinements_fast()

        # Full validation before delivery
        result = session.run_full_validation()
    """

    def __init__(
        self,
        session_id: str,
        fact_store: Any,
        deal_type: str,
        meeting_notes: str = "",
        model: str = "claude-sonnet-4-20250514",
    ):
        self.session_id = session_id
        self.fact_store = fact_store
        self.deal_type = deal_type
        self.meeting_notes = meeting_notes
        self.model = model

        # Current analysis state
        self.current_output: Optional[ThreeStageOutput] = None
        self.considerations: List[IdentifiedConsideration] = []
        self.activities: List[MatchedActivity] = []
        self.tsa_services: List[Dict] = []
        self.quant_context: Dict = {}

        # Refinements
        self.refinements: List[RefinementInput] = []
        self.refinement_results: List[RefinementResult] = []

        # Overrides (accumulated from refinements)
        self.tsa_overrides: List[Dict] = []
        self.activity_overrides: Dict[str, Dict] = {}
        self.removed_activities: List[str] = []
        self.quantitative_overrides: Dict[str, Any] = {}
        self.additional_context: List[str] = []

        # Snapshots
        self.snapshots: List[ThreeStageSnapshot] = []

        # Cost tracking
        self.total_llm_cost: float = 0.0

        self.created_at = datetime.now().isoformat()
        logger.info(f"Created three-stage refinement session: {session_id}")

    @classmethod
    def create(
        cls,
        fact_store: Any,
        deal_type: str,
        meeting_notes: str = "",
        model: str = "claude-sonnet-4-20250514",
    ) -> "ThreeStageRefinementSession":
        """Create a new three-stage refinement session."""
        session_id = f"TSR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return cls(
            session_id=session_id,
            fact_store=fact_store,
            deal_type=deal_type,
            meeting_notes=meeting_notes,
            model=model,
        )

    # =========================================================================
    # ANALYSIS METHODS
    # =========================================================================

    def run_initial_analysis(self) -> ThreeStageOutput:
        """
        Run full three-stage analysis.

        Cost: ~$0.30-0.50
        """
        logger.info("Running initial three-stage analysis")

        # Build context with any pre-set meeting notes
        context = self.meeting_notes
        if self.additional_context:
            context += "\n\n" + "\n".join(self.additional_context)

        # Run three-stage analysis
        output = run_three_stage_analysis(
            fact_store=self.fact_store,
            deal_type=self.deal_type,
            meeting_notes=context,
            model=self.model,
        )

        # Store state
        self.current_output = output
        self.considerations = output.considerations
        self.activities = list(output.activities)
        self.tsa_services = list(output.tsa_services)
        self.quant_context = {}  # Will be populated from Stage 1

        # Track costs
        self.total_llm_cost += output.total_llm_cost

        # Take snapshot
        self._take_snapshot("initial")

        return output

    def apply_refinements_fast(self) -> Dict[str, Any]:
        """
        Apply refinements with fast analysis (Stage 1 + 2 only).

        Skips validation to save cost during iterative refinement.

        Cost: ~$0.15-0.20
        """
        if not self.refinements:
            return self._build_current_result()

        logger.info(f"Applying {len(self.refinements)} refinements (fast mode)")

        # Build enhanced context with refinements
        context = self._build_enhanced_context()

        # Run Stage 1: LLM identifies considerations
        from tools_v2.reasoning_integration import factstore_to_reasoning_format
        facts = factstore_to_reasoning_format(self.fact_store)

        considerations, quant_context, cost = stage1_identify_considerations(
            facts=facts,
            deal_type=self.deal_type,
            additional_context=context,
            model=self.model,
        )

        self.total_llm_cost += cost

        # Apply quantitative overrides
        for field, value in self.quantitative_overrides.items():
            quant_context[field] = value

        self.quant_context = quant_context

        # Run Stage 2: Rules match activities
        activities, tsa_services = stage2_match_activities(
            considerations=considerations,
            quant_context=quant_context,
            deal_type=self.deal_type,
        )

        # Apply refinement overrides
        activities = self._apply_activity_overrides(activities)
        tsa_services = self._apply_tsa_overrides(tsa_services)

        # Store state
        self.considerations = considerations
        self.activities = activities
        self.tsa_services = tsa_services

        # Take snapshot
        self._take_snapshot(f"refinement-fast")

        return self._build_current_result(validated=False)

    def run_full_validation(self) -> ThreeStageOutput:
        """
        Run full analysis with validation (all 3 stages).

        Use before presenting to client.

        Cost: ~$0.30-0.50
        """
        logger.info("Running full validation")

        # Build enhanced context
        context = self._build_enhanced_context()

        # Run three-stage analysis
        output = run_three_stage_analysis(
            fact_store=self.fact_store,
            deal_type=self.deal_type,
            meeting_notes=context,
            model=self.model,
        )

        # Apply overrides to output
        output.activities = self._apply_activity_overrides(list(output.activities))
        output.tsa_services = self._apply_tsa_overrides(list(output.tsa_services))

        # Recalculate totals
        total_low = sum(a.cost_range[0] for a in output.activities)
        total_high = sum(a.cost_range[1] for a in output.activities)
        output.total_cost_range = (total_low, total_high)

        # Store state
        self.current_output = output
        self.considerations = output.considerations
        self.activities = output.activities
        self.tsa_services = output.tsa_services

        # Track costs
        self.total_llm_cost += output.total_llm_cost

        # Take snapshot
        self._take_snapshot("validated")

        return output

    def validate_only(self) -> Tuple[ValidationResult, float]:
        """
        Run Stage 3 validation only on current state.

        Use when you've made manual adjustments and want to validate.

        Cost: ~$0.10-0.15
        """
        from tools_v2.reasoning_integration import factstore_to_reasoning_format
        facts = factstore_to_reasoning_format(self.fact_store)

        validation, cost = stage3_validate(
            facts=facts,
            considerations=self.considerations,
            activities=self.activities,
            tsa_services=self.tsa_services,
            deal_type=self.deal_type,
            quant_context=self.quant_context,
            model=self.model,
        )

        self.total_llm_cost += cost

        return validation, cost

    # =========================================================================
    # REFINEMENT METHODS
    # =========================================================================

    def add_refinement(self, refinement: RefinementInput) -> str:
        """Add a refinement input."""
        refinement_id = f"R-{len(self.refinements)+1:03d}"
        self.refinements.append(refinement)

        # Process refinement immediately to update overrides
        self._process_refinement(refinement)

        logger.info(f"Added refinement {refinement_id}: {refinement.type}")
        return refinement_id

    def add_tsa_requirement(
        self,
        service: str,
        workstream: str,
        duration_months: Tuple[int, int],
        source: str = "seller",
        reason: Optional[str] = None,
    ) -> str:
        """Add a TSA requirement (e.g., seller specifies they'll provide email)."""

        refinement = RefinementInput(
            type=RefinementType.TSA_REQUIREMENT.value,
            source=source,
            workstream=workstream,
            details={
                "service": service,
                "workstream": workstream,
                "duration_months": duration_months,
            },
            reason=reason,
        )

        return self.add_refinement(refinement)

    def add_activity_override(
        self,
        activity_id: str,
        cost_override: Optional[Tuple[float, float]] = None,
        timeline_override: Optional[Tuple[int, int]] = None,
        source: str = "team",
        reason: Optional[str] = None,
    ) -> str:
        """Override cost or timeline for a specific activity."""

        details = {}
        if cost_override:
            details["cost_range"] = cost_override
        if timeline_override:
            details["timeline_months"] = timeline_override

        refinement = RefinementInput(
            type=RefinementType.ACTIVITY_OVERRIDE.value,
            source=source,
            activity_id=activity_id,
            details=details,
            reason=reason,
        )

        return self.add_refinement(refinement)

    def add_quantitative_update(
        self,
        field: str,
        value: Any,
        source: str = "team",
        reason: Optional[str] = None,
    ) -> str:
        """Update quantitative context (user_count, app_count, etc.)."""

        refinement = RefinementInput(
            type=RefinementType.QUANTITATIVE.value,
            source=source,
            details={field: value},
            reason=reason,
        )

        return self.add_refinement(refinement)

    def add_context_note(
        self,
        note: str,
        source: str = "team",
        workstream: Optional[str] = None,
    ) -> str:
        """Add context note that will influence Stage 1 interpretation."""

        refinement = RefinementInput(
            type=RefinementType.NOTE.value,
            source=source,
            workstream=workstream,
            details={"note": note},
        )

        return self.add_refinement(refinement)

    def remove_activity(
        self,
        activity_id: str,
        source: str = "team",
        reason: Optional[str] = None,
    ) -> str:
        """Mark an activity for removal."""

        refinement = RefinementInput(
            type=RefinementType.ACTIVITY_REMOVE.value,
            source=source,
            activity_id=activity_id,
            reason=reason,
        )

        return self.add_refinement(refinement)

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    def _process_refinement(self, ref: RefinementInput):
        """Process refinement and update internal overrides."""

        ref_type = ref.type

        if ref_type == RefinementType.TSA_REQUIREMENT.value:
            self.tsa_overrides.append({
                "service": ref.details.get("service"),
                "workstream": ref.workstream or ref.details.get("workstream"),
                "duration_months": ref.details.get("duration_months"),
                "reason": ref.reason,
                "source": ref.source,
            })

        elif ref_type == RefinementType.ACTIVITY_OVERRIDE.value:
            if ref.activity_id:
                self.activity_overrides[ref.activity_id] = ref.details

        elif ref_type == RefinementType.ACTIVITY_REMOVE.value:
            if ref.activity_id:
                self.removed_activities.append(ref.activity_id)

        elif ref_type == RefinementType.QUANTITATIVE.value:
            for field, value in ref.details.items():
                self.quantitative_overrides[field] = value

        elif ref_type == RefinementType.NOTE.value:
            note = ref.details.get("note", "")
            source_prefix = f"[{ref.source}]" if ref.source else ""
            self.additional_context.append(f"{source_prefix} {note}")

    def _build_enhanced_context(self) -> str:
        """Build enhanced context including all refinements."""

        context_parts = [self.meeting_notes] if self.meeting_notes else []

        # Add additional context from notes
        if self.additional_context:
            context_parts.append("\n--- Team Input ---")
            context_parts.extend(self.additional_context)

        # Add quantitative overrides
        if self.quantitative_overrides:
            context_parts.append("\n--- Updated Quantities ---")
            for field, value in self.quantitative_overrides.items():
                context_parts.append(f"{field}: {value}")

        # Add TSA override context
        if self.tsa_overrides:
            context_parts.append("\n--- Confirmed TSA Requirements ---")
            for tsa in self.tsa_overrides:
                context_parts.append(
                    f"- {tsa['service']} ({tsa['workstream']}): "
                    f"{tsa['duration_months'][0]}-{tsa['duration_months'][1]} months "
                    f"(Source: {tsa.get('source', 'team')})"
                )

        return "\n".join(context_parts)

    def _apply_activity_overrides(
        self,
        activities: List[MatchedActivity],
    ) -> List[MatchedActivity]:
        """Apply activity overrides and removals."""

        result = []

        for activity in activities:
            # Skip removed activities
            if activity.activity_id in self.removed_activities:
                continue

            # Apply overrides
            if activity.activity_id in self.activity_overrides:
                override = self.activity_overrides[activity.activity_id]
                if "cost_range" in override:
                    activity.cost_range = tuple(override["cost_range"])
                if "timeline_months" in override:
                    activity.timeline_months = tuple(override["timeline_months"])

            result.append(activity)

        return result

    def _apply_tsa_overrides(self, tsa_services: List[Dict]) -> List[Dict]:
        """Add TSA override services."""

        result = list(tsa_services)

        for tsa_override in self.tsa_overrides:
            # Check if already exists
            existing = [
                t for t in result
                if t.get("service") == tsa_override["service"]
            ]

            if not existing:
                result.append({
                    "service": tsa_override["service"],
                    "workstream": tsa_override["workstream"],
                    "duration_months": tsa_override["duration_months"],
                    "triggered_by": f"refinement-{tsa_override.get('source', 'team')}",
                })

        return result

    def _build_current_result(self, validated: bool = False) -> Dict[str, Any]:
        """Build result dict from current state."""

        total_low = sum(a.cost_range[0] for a in self.activities)
        total_high = sum(a.cost_range[1] for a in self.activities)

        return {
            "session_id": self.session_id,
            "deal_type": self.deal_type,
            "mode": "validated" if validated else "fast",
            "considerations": [asdict(c) for c in self.considerations],
            "activities": [asdict(a) for a in self.activities],
            "tsa_services": self.tsa_services,
            "total_cost_range": (total_low, total_high),
            "refinements_applied": len(self.refinements),
            "total_llm_cost": self.total_llm_cost,
            "validated": validated,
        }

    def _take_snapshot(self, trigger: str):
        """Take snapshot of current state."""

        total_low = sum(a.cost_range[0] for a in self.activities)
        total_high = sum(a.cost_range[1] for a in self.activities)

        content = json.dumps({
            "considerations": len(self.considerations),
            "activities": len(self.activities),
            "tsa": len(self.tsa_services),
            "cost": (total_low, total_high),
        }, sort_keys=True)
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]

        # Get confidence from validation if available
        confidence = 0.0
        if self.current_output and self.current_output.validation:
            confidence = self.current_output.validation.confidence_score

        snapshot = ThreeStageSnapshot(
            snapshot_id=f"SNAP-{len(self.snapshots)+1:03d}",
            timestamp=datetime.now().isoformat(),
            trigger=trigger,
            consideration_count=len(self.considerations),
            activity_count=len(self.activities),
            tsa_count=len(self.tsa_services),
            total_cost_range=(total_low, total_high),
            llm_cost=self.total_llm_cost,
            confidence_score=confidence,
            content_hash=content_hash,
        )

        self.snapshots.append(snapshot)

    # =========================================================================
    # SUMMARY AND EXPORT
    # =========================================================================

    def get_change_summary(self) -> Dict:
        """Get summary of changes from initial to current state."""

        if len(self.snapshots) < 2:
            return {"message": "Need at least 2 snapshots to compare"}

        initial = self.snapshots[0]
        current = self.snapshots[-1]

        return {
            "initial": {
                "cost_range": initial.total_cost_range,
                "considerations": initial.consideration_count,
                "activities": initial.activity_count,
                "tsa_services": initial.tsa_count,
            },
            "current": {
                "cost_range": current.total_cost_range,
                "considerations": current.consideration_count,
                "activities": current.activity_count,
                "tsa_services": current.tsa_count,
            },
            "delta": {
                "cost_low": current.total_cost_range[0] - initial.total_cost_range[0],
                "cost_high": current.total_cost_range[1] - initial.total_cost_range[1],
                "considerations": current.consideration_count - initial.consideration_count,
                "activities": current.activity_count - initial.activity_count,
            },
            "refinements_applied": len(self.refinements),
            "total_llm_cost": self.total_llm_cost,
        }

    def get_formatted_output(self) -> str:
        """Get formatted output for display."""

        if self.current_output:
            return format_three_stage_output(self.current_output)

        # Build output from current state
        lines = []
        lines.append("=" * 70)
        lines.append("THREE-STAGE REFINEMENT SESSION")
        lines.append("=" * 70)

        lines.append(f"\nSession: {self.session_id}")
        lines.append(f"Deal Type: {self.deal_type}")
        lines.append(f"Refinements: {len(self.refinements)}")
        lines.append(f"LLM Cost: ${self.total_llm_cost:.4f}")

        lines.append(f"\n{'='*70}")
        lines.append("CONSIDERATIONS")
        lines.append("=" * 70)

        for c in self.considerations:
            lines.append(f"\n[{c.consideration_id}] {c.workstream.upper()}")
            lines.append(f"  {c.finding}")

        lines.append(f"\n{'='*70}")
        lines.append("ACTIVITIES")
        lines.append("=" * 70)

        total_low = 0
        total_high = 0
        for a in self.activities:
            lines.append(f"\n[{a.activity_id}] {a.name}")
            lines.append(f"  ${a.cost_range[0]:,.0f} - ${a.cost_range[1]:,.0f}")
            total_low += a.cost_range[0]
            total_high += a.cost_range[1]

        lines.append(f"\n{'='*70}")
        lines.append(f"TOTAL: ${total_low:,.0f} - ${total_high:,.0f}")
        lines.append(f"TSA Services: {len(self.tsa_services)}")
        lines.append("=" * 70)

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Serialize session for persistence."""

        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "deal_type": self.deal_type,
            "meeting_notes": self.meeting_notes,
            "model": self.model,
            "refinements": [asdict(r) if hasattr(r, '__dataclass_fields__') else r.to_dict() for r in self.refinements],
            "tsa_overrides": self.tsa_overrides,
            "activity_overrides": self.activity_overrides,
            "removed_activities": self.removed_activities,
            "quantitative_overrides": self.quantitative_overrides,
            "additional_context": self.additional_context,
            "total_llm_cost": self.total_llm_cost,
            "snapshots": [asdict(s) for s in self.snapshots],
        }

    def save(self, path: str):
        """Save session to file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved session to {path}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_refinement_session(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str = "",
) -> ThreeStageRefinementSession:
    """Create a new three-stage refinement session."""
    return ThreeStageRefinementSession.create(
        fact_store=fact_store,
        deal_type=deal_type,
        meeting_notes=meeting_notes,
    )


def quick_three_stage_analysis(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str = "",
) -> ThreeStageOutput:
    """Run quick three-stage analysis without refinement session."""
    return run_three_stage_analysis(
        fact_store=fact_store,
        deal_type=deal_type,
        meeting_notes=meeting_notes,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ThreeStageRefinementSession',
    'ThreeStageSnapshot',
    'create_refinement_session',
    'quick_three_stage_analysis',
]
