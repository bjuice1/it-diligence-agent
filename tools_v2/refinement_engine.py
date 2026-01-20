"""
Refinement Engine - Interactive Analysis Refinement

Supports iterative refinement of reasoning analysis based on:
- Team member inputs/clarifications
- Seller-provided TSA details
- Buyer technology confirmations
- Timeline/budget constraints
- Workstream-specific overrides

Key Concepts:
1. **Refinement Inputs** - Structured inputs that modify the analysis
2. **Change Tracking** - Track what changed and why
3. **Incremental Updates** - Don't re-run everything, update affected areas
4. **Refinement History** - Full audit trail of how analysis evolved

Usage:
    session = RefinementSession.create(fact_store, deal_type="acquisition")

    # Initial analysis
    session.run_initial_analysis()

    # Team provides clarification
    session.add_refinement(RefinementInput(
        type="tsa_requirement",
        source="seller",
        details={"service": "email", "duration_months": 6, "reason": "Migration complexity"}
    ))

    # Re-analyze affected areas
    session.apply_refinements()

    # Compare to previous
    delta = session.get_change_summary()
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from enum import Enum
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# REFINEMENT INPUT TYPES
# =============================================================================

class RefinementType(Enum):
    """Types of refinements that can be applied."""

    # TSA-related
    TSA_REQUIREMENT = "tsa_requirement"          # Seller says they need to provide TSA
    TSA_CONSTRAINT = "tsa_constraint"            # Buyer says max TSA duration is X
    TSA_COST = "tsa_cost"                        # Seller provides TSA pricing

    # Technology clarifications
    TECH_CONFIRMATION = "tech_confirmation"      # Confirm target/buyer tech stack
    TECH_MISMATCH_OVERRIDE = "tech_mismatch"     # Override auto-detected mismatch

    # Timeline/Budget
    TIMELINE_CONSTRAINT = "timeline_constraint"  # Must complete by X
    BUDGET_CONSTRAINT = "budget_constraint"      # Budget cap for workstream

    # Workstream-specific
    ACTIVITY_OVERRIDE = "activity_override"      # Override cost/timeline for activity
    ACTIVITY_ADD = "activity_add"                # Add activity not derived
    ACTIVITY_REMOVE = "activity_remove"          # Remove derived activity

    # Context
    DEAL_CONTEXT = "deal_context"                # Update deal type, buyer info, etc.
    QUANTITATIVE = "quantitative"                # Update user count, app count, etc.

    # General
    NOTE = "note"                                # General clarification note


@dataclass
class RefinementInput:
    """A single refinement input from a team member."""

    type: str  # RefinementType value
    source: str  # Who provided this: "seller", "buyer", "team", "document"

    # What's being refined
    workstream: Optional[str] = None  # Which workstream this affects
    activity_id: Optional[str] = None  # Specific activity if applicable

    # The refinement details
    details: Dict[str, Any] = field(default_factory=dict)

    # Rationale
    reason: Optional[str] = None
    evidence: Optional[str] = None  # Quote or reference

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    added_by: Optional[str] = None  # Team member name

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "RefinementInput":
        return cls(**data)


@dataclass
class RefinementResult:
    """Result of applying a refinement."""

    refinement_id: str
    input: RefinementInput

    # What changed
    affected_workstreams: List[str]
    affected_activities: List[str]

    # Before/after for changed values
    changes: List[Dict[str, Any]]  # [{field, old_value, new_value, reason}]

    # Cost impact
    cost_delta: tuple  # (low_delta, high_delta)

    # Status
    applied: bool = True
    error: Optional[str] = None


# =============================================================================
# REFINEMENT SESSION
# =============================================================================

@dataclass
class AnalysisSnapshot:
    """Snapshot of analysis state at a point in time."""

    snapshot_id: str
    timestamp: str

    # Trigger
    trigger: str  # "initial" or refinement_id that caused this

    # Full output at this point
    total_cost: tuple
    tsa_count: int
    activity_count: int
    workstream_costs: Dict[str, tuple]

    # Hash for comparison
    content_hash: str


class RefinementSession:
    """
    Manages iterative refinement of an analysis.

    Tracks the evolution of analysis through multiple rounds of refinement
    as team members provide clarifications and new information.
    """

    def __init__(
        self,
        session_id: str,
        fact_store: Any,  # FactStore
        deal_type: str,
        buyer_context: Optional[Dict] = None,
        meeting_notes: Optional[str] = None,
    ):
        self.session_id = session_id
        self.fact_store = fact_store
        self.deal_type = deal_type
        self.buyer_context = buyer_context or {}
        self.meeting_notes = meeting_notes or ""

        # Refinement tracking
        self.refinements: List[RefinementInput] = []
        self.refinement_results: List[RefinementResult] = []

        # Analysis snapshots (for comparison)
        self.snapshots: List[AnalysisSnapshot] = []

        # Current analysis result
        self.current_result: Optional[Dict] = None

        # Overrides applied (accumulated from refinements)
        self.tsa_overrides: List[Dict] = []  # Additional TSA requirements
        self.activity_overrides: Dict[str, Dict] = {}  # activity_id -> override
        self.removed_activities: List[str] = []  # activity_ids to exclude
        self.additional_activities: List[Dict] = []  # manually added activities
        self.quantitative_overrides: Dict[str, Any] = {}  # user_count, app_count, etc.

        self.created_at = datetime.now().isoformat()
        logger.info(f"Created refinement session: {session_id}")

    @classmethod
    def create(
        cls,
        fact_store: Any,
        deal_type: str,
        buyer_context: Optional[Dict] = None,
        meeting_notes: Optional[str] = None,
    ) -> "RefinementSession":
        """Create a new refinement session."""
        session_id = f"REF-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return cls(
            session_id=session_id,
            fact_store=fact_store,
            deal_type=deal_type,
            buyer_context=buyer_context,
            meeting_notes=meeting_notes,
        )

    def run_initial_analysis(self) -> Dict:
        """Run initial analysis before any refinements."""
        from tools_v2.reasoning_integration import run_reasoning_analysis

        logger.info("Running initial analysis")

        result = run_reasoning_analysis(
            fact_store=self.fact_store,
            deal_type=self.deal_type,
            meeting_notes=self.meeting_notes,
            include_buyer_context=bool(self.buyer_context),
        )

        self.current_result = result

        # Take initial snapshot
        self._take_snapshot("initial")

        return result

    def add_refinement(self, refinement: RefinementInput) -> str:
        """
        Add a refinement input.

        Returns refinement ID for tracking.
        """
        refinement_id = f"R-{len(self.refinements)+1:03d}"
        self.refinements.append(refinement)

        logger.info(f"Added refinement {refinement_id}: {refinement.type} from {refinement.source}")

        return refinement_id

    def add_tsa_requirement(
        self,
        service: str,
        workstream: str,
        duration_months: tuple,
        source: str = "seller",
        reason: Optional[str] = None,
        cost_per_month: Optional[float] = None,
    ) -> str:
        """Convenience method to add a TSA requirement."""

        details = {
            "service": service,
            "workstream": workstream,
            "duration_months": duration_months,
        }
        if cost_per_month:
            details["cost_per_month"] = cost_per_month

        refinement = RefinementInput(
            type=RefinementType.TSA_REQUIREMENT.value,
            source=source,
            workstream=workstream,
            details=details,
            reason=reason,
        )

        return self.add_refinement(refinement)

    def add_activity_override(
        self,
        activity_id: str,
        cost_override: Optional[tuple] = None,
        timeline_override: Optional[tuple] = None,
        source: str = "team",
        reason: Optional[str] = None,
    ) -> str:
        """Convenience method to override activity cost/timeline."""

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

    def add_timeline_constraint(
        self,
        workstream: Optional[str],
        max_months: int,
        source: str = "buyer",
        reason: Optional[str] = None,
    ) -> str:
        """Add timeline constraint (e.g., "must complete identity in 6 months")."""

        refinement = RefinementInput(
            type=RefinementType.TIMELINE_CONSTRAINT.value,
            source=source,
            workstream=workstream,
            details={"max_months": max_months},
            reason=reason,
        )

        return self.add_refinement(refinement)

    def add_quantitative_update(
        self,
        field: str,  # "user_count", "app_count", "site_count", etc.
        value: Any,
        source: str = "team",
        reason: Optional[str] = None,
    ) -> str:
        """Update quantitative context (user count, app count, etc.)."""

        refinement = RefinementInput(
            type=RefinementType.QUANTITATIVE.value,
            source=source,
            details={field: value},
            reason=reason,
        )

        return self.add_refinement(refinement)

    def add_note(
        self,
        note: str,
        workstream: Optional[str] = None,
        source: str = "team",
    ) -> str:
        """Add a general clarification note."""

        refinement = RefinementInput(
            type=RefinementType.NOTE.value,
            source=source,
            workstream=workstream,
            details={"note": note},
        )

        return self.add_refinement(refinement)

    def apply_refinements(self, since_index: int = 0) -> List[RefinementResult]:
        """
        Apply refinements and re-run analysis.

        Args:
            since_index: Only apply refinements from this index onwards

        Returns:
            List of refinement results showing what changed
        """
        if self.current_result is None:
            raise ValueError("Must run initial analysis first")

        results = []
        refinements_to_apply = self.refinements[since_index:]

        if not refinements_to_apply:
            logger.info("No new refinements to apply")
            return results

        logger.info(f"Applying {len(refinements_to_apply)} refinements")

        # Process each refinement to update overrides
        for i, ref in enumerate(refinements_to_apply):
            result = self._process_refinement(ref, f"R-{since_index + i + 1:03d}")
            results.append(result)
            self.refinement_results.append(result)

        # Re-run analysis with updated context
        self._rerun_analysis()

        # Take snapshot
        trigger = results[-1].refinement_id if results else "batch"
        self._take_snapshot(trigger)

        return results

    def _process_refinement(self, ref: RefinementInput, ref_id: str) -> RefinementResult:
        """Process a single refinement, updating internal state."""

        affected_workstreams = []
        affected_activities = []
        changes = []

        ref_type = ref.type

        if ref_type == RefinementType.TSA_REQUIREMENT.value:
            # Add TSA override
            tsa_override = {
                "service": ref.details.get("service"),
                "workstream": ref.workstream or ref.details.get("workstream"),
                "duration_months": ref.details.get("duration_months"),
                "why_needed": ref.reason or "Specified by seller",
                "criticality": ref.details.get("criticality", "high"),
                "source": ref.source,
            }
            self.tsa_overrides.append(tsa_override)

            affected_workstreams.append(tsa_override["workstream"])
            changes.append({
                "field": "tsa_requirements",
                "action": "added",
                "value": tsa_override,
                "reason": ref.reason,
            })

        elif ref_type == RefinementType.ACTIVITY_OVERRIDE.value:
            # Store activity override
            if ref.activity_id:
                self.activity_overrides[ref.activity_id] = ref.details
                affected_activities.append(ref.activity_id)
                changes.append({
                    "field": f"activity.{ref.activity_id}",
                    "action": "modified",
                    "value": ref.details,
                    "reason": ref.reason,
                })

        elif ref_type == RefinementType.ACTIVITY_REMOVE.value:
            # Mark activity for removal
            if ref.activity_id:
                self.removed_activities.append(ref.activity_id)
                affected_activities.append(ref.activity_id)
                changes.append({
                    "field": f"activity.{ref.activity_id}",
                    "action": "removed",
                    "reason": ref.reason,
                })

        elif ref_type == RefinementType.QUANTITATIVE.value:
            # Update quantitative overrides
            for field, value in ref.details.items():
                old_value = self.quantitative_overrides.get(field)
                self.quantitative_overrides[field] = value
                changes.append({
                    "field": field,
                    "old_value": old_value,
                    "new_value": value,
                    "reason": ref.reason,
                })

        elif ref_type == RefinementType.NOTE.value:
            # Append to meeting notes
            note = ref.details.get("note", "")
            source_prefix = f"[{ref.source}]" if ref.source else ""
            self.meeting_notes += f"\n{source_prefix} {note}"

            if ref.workstream:
                affected_workstreams.append(ref.workstream)

        elif ref_type == RefinementType.DEAL_CONTEXT.value:
            # Update deal context
            if "deal_type" in ref.details:
                old_type = self.deal_type
                self.deal_type = ref.details["deal_type"]
                changes.append({
                    "field": "deal_type",
                    "old_value": old_type,
                    "new_value": self.deal_type,
                    "reason": ref.reason,
                })
            if "buyer_context" in ref.details:
                self.buyer_context.update(ref.details["buyer_context"])

        # Calculate cost delta (will be updated after re-analysis)
        cost_delta = (0, 0)

        return RefinementResult(
            refinement_id=ref_id,
            input=ref,
            affected_workstreams=affected_workstreams,
            affected_activities=affected_activities,
            changes=changes,
            cost_delta=cost_delta,
        )

    def _rerun_analysis(self):
        """Re-run analysis with current overrides."""
        from tools_v2.reasoning_integration import run_reasoning_analysis

        # Build enhanced meeting notes with all context
        enhanced_notes = self.meeting_notes

        # Add quantitative overrides to notes
        if self.quantitative_overrides:
            quant_lines = []
            for field, value in self.quantitative_overrides.items():
                quant_lines.append(f"{field}: {value}")
            enhanced_notes += "\n\nQuantitative updates:\n" + "\n".join(quant_lines)

        # Run analysis
        result = run_reasoning_analysis(
            fact_store=self.fact_store,
            deal_type=self.deal_type,
            meeting_notes=enhanced_notes,
            include_buyer_context=bool(self.buyer_context),
        )

        # Apply TSA overrides
        output = result["raw_output"]
        for tsa in self.tsa_overrides:
            # Add to TSA requirements if not already present
            existing = [t for t in output.tsa_requirements if t.service == tsa["service"]]
            if not existing:
                from tools_v2.reasoning_engine import TSARequirement
                output.tsa_requirements.append(TSARequirement(
                    service=tsa["service"],
                    workstream=tsa["workstream"],
                    why_needed=tsa["why_needed"],
                    duration_months=tsa["duration_months"],
                    criticality=tsa["criticality"],
                    exit_activities=[],  # Will be linked to activities later
                    supporting_facts=[f"Refinement: {tsa.get('source', 'team')}"],
                ))

        # Apply activity overrides
        for activity in output.derived_activities:
            if activity.activity_id in self.activity_overrides:
                override = self.activity_overrides[activity.activity_id]
                if "cost_range" in override:
                    activity.cost_range = override["cost_range"]
                if "timeline_months" in override:
                    activity.timeline_months = override["timeline_months"]

        # Remove excluded activities
        output.derived_activities = [
            a for a in output.derived_activities
            if a.activity_id not in self.removed_activities
        ]

        # Recalculate totals
        output.grand_total = (
            sum(a.cost_range[0] for a in output.derived_activities),
            sum(a.cost_range[1] for a in output.derived_activities),
        )

        # Update workstream costs
        output.workstream_costs = {}
        for activity in output.derived_activities:
            ws = activity.workstream
            if ws not in output.workstream_costs:
                output.workstream_costs[ws] = (0, 0)
            output.workstream_costs[ws] = (
                output.workstream_costs[ws][0] + activity.cost_range[0],
                output.workstream_costs[ws][1] + activity.cost_range[1],
            )

        self.current_result = result

    def _take_snapshot(self, trigger: str):
        """Take a snapshot of current analysis state."""
        if not self.current_result:
            return

        output = self.current_result["raw_output"]

        # Create content hash for change detection
        content = json.dumps({
            "total": output.grand_total,
            "tsa": len(output.tsa_requirements),
            "activities": len(output.derived_activities),
            "workstreams": output.workstream_costs,
        }, sort_keys=True)
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]

        snapshot = AnalysisSnapshot(
            snapshot_id=f"SNAP-{len(self.snapshots)+1:03d}",
            timestamp=datetime.now().isoformat(),
            trigger=trigger,
            total_cost=output.grand_total,
            tsa_count=len(output.tsa_requirements),
            activity_count=len(output.derived_activities),
            workstream_costs=dict(output.workstream_costs),
            content_hash=content_hash,
        )

        self.snapshots.append(snapshot)

    def get_change_summary(self) -> Dict:
        """Get summary of changes from initial to current state."""
        if len(self.snapshots) < 2:
            return {"message": "Need at least 2 snapshots to compare"}

        initial = self.snapshots[0]
        current = self.snapshots[-1]

        cost_delta = (
            current.total_cost[0] - initial.total_cost[0],
            current.total_cost[1] - initial.total_cost[1],
        )

        return {
            "initial": {
                "total_cost": initial.total_cost,
                "tsa_count": initial.tsa_count,
                "activity_count": initial.activity_count,
            },
            "current": {
                "total_cost": current.total_cost,
                "tsa_count": current.tsa_count,
                "activity_count": current.activity_count,
            },
            "delta": {
                "cost": cost_delta,
                "tsa": current.tsa_count - initial.tsa_count,
                "activities": current.activity_count - initial.activity_count,
            },
            "refinements_applied": len(self.refinements),
            "snapshots": len(self.snapshots),
        }

    def get_refinement_history(self) -> List[Dict]:
        """Get full refinement history."""
        history = []

        for i, ref in enumerate(self.refinements):
            result = self.refinement_results[i] if i < len(self.refinement_results) else None

            history.append({
                "refinement_id": f"R-{i+1:03d}",
                "timestamp": ref.timestamp,
                "type": ref.type,
                "source": ref.source,
                "workstream": ref.workstream,
                "details": ref.details,
                "reason": ref.reason,
                "applied": result.applied if result else False,
                "changes": result.changes if result else [],
            })

        return history

    def to_dict(self) -> Dict:
        """Serialize session to dict for persistence."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "deal_type": self.deal_type,
            "buyer_context": self.buyer_context,
            "meeting_notes": self.meeting_notes,
            "refinements": [r.to_dict() for r in self.refinements],
            "snapshots": [asdict(s) for s in self.snapshots],
            "tsa_overrides": self.tsa_overrides,
            "activity_overrides": self.activity_overrides,
            "removed_activities": self.removed_activities,
            "quantitative_overrides": self.quantitative_overrides,
        }

    def save(self, path: str):
        """Save session to file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved refinement session to {path}")

    @classmethod
    def load(cls, path: str, fact_store: Any) -> "RefinementSession":
        """Load session from file."""
        with open(path) as f:
            data = json.load(f)

        session = cls(
            session_id=data["session_id"],
            fact_store=fact_store,
            deal_type=data["deal_type"],
            buyer_context=data.get("buyer_context"),
            meeting_notes=data.get("meeting_notes"),
        )

        session.created_at = data["created_at"]
        session.refinements = [RefinementInput.from_dict(r) for r in data.get("refinements", [])]
        session.tsa_overrides = data.get("tsa_overrides", [])
        session.activity_overrides = data.get("activity_overrides", {})
        session.removed_activities = data.get("removed_activities", [])
        session.quantitative_overrides = data.get("quantitative_overrides", {})

        return session


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'RefinementType',
    'RefinementInput',
    'RefinementResult',
    'RefinementSession',
    'AnalysisSnapshot',
]
