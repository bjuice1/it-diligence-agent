"""
Feedback Tracker for Template Refinement

Tracks refinement overrides to inform future template adjustments.

When team members override activity costs, this module captures:
1. What was overridden (activity, original cost, new cost)
2. Context (deal size, industry, complexity)
3. Rationale (why the override was made)

Over time, this data can:
- Identify templates that consistently need adjustment
- Suggest template range updates
- Generate reports on estimation accuracy

This is NOT automatic learning - it's data capture for human review.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CostOverride:
    """A single cost override event."""

    # What was overridden
    activity_name: str
    activity_id: str
    workstream: str
    template_cost_range: Tuple[float, float]  # Original from template
    override_cost_range: Tuple[float, float]  # After override

    # Context
    deal_type: str
    user_count: int
    user_count_source: str  # "extracted" or "assumed"

    # Rationale
    source: str  # "seller", "buyer", "team"
    reason: Optional[str]

    # Metadata
    session_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def cost_delta_low(self) -> float:
        return self.override_cost_range[0] - self.template_cost_range[0]

    @property
    def cost_delta_high(self) -> float:
        return self.override_cost_range[1] - self.template_cost_range[1]

    @property
    def delta_percent_low(self) -> float:
        if self.template_cost_range[0] == 0:
            return 0
        return (self.cost_delta_low / self.template_cost_range[0]) * 100

    @property
    def delta_percent_high(self) -> float:
        if self.template_cost_range[1] == 0:
            return 0
        return (self.cost_delta_high / self.template_cost_range[1]) * 100


@dataclass
class TSAOverride:
    """A TSA duration override event."""

    service: str
    workstream: str
    template_duration: Optional[Tuple[int, int]]  # Original (or None if newly added)
    override_duration: Tuple[int, int]

    source: str
    reason: Optional[str]

    session_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TemplateStats:
    """Statistics for a single activity template."""

    activity_name: str
    workstream: str

    # Override frequency
    total_appearances: int = 0
    times_overridden: int = 0

    # Cost deltas
    avg_delta_low: float = 0.0
    avg_delta_high: float = 0.0
    avg_delta_percent: float = 0.0

    # Range of overrides
    min_override_low: float = 0.0
    max_override_high: float = 0.0

    # Contexts where overridden
    override_contexts: List[str] = field(default_factory=list)  # e.g., ["carveout>1000users", "acquisition"]

    @property
    def override_rate(self) -> float:
        if self.total_appearances == 0:
            return 0
        return self.times_overridden / self.total_appearances


class FeedbackTracker:
    """
    Tracks feedback from refinement sessions.

    Usage:
        tracker = FeedbackTracker("feedback.json")

        # Record an override
        tracker.record_cost_override(
            activity_name="Migrate user accounts",
            activity_id="A-003",
            workstream="identity",
            template_cost_range=(27000, 72000),
            override_cost_range=(45000, 90000),
            deal_type="carveout",
            user_count=1800,
            user_count_source="extracted",
            source="team",
            reason="Enterprise deal, complex integrations",
            session_id="TSR-20241201-123456",
        )

        # Get stats for a template
        stats = tracker.get_template_stats("Migrate user accounts")

        # Generate report
        report = tracker.generate_report()
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.cost_overrides: List[CostOverride] = []
        self.tsa_overrides: List[TSAOverride] = []

        if self.storage_path and self.storage_path.exists():
            self._load()

    def record_cost_override(
        self,
        activity_name: str,
        activity_id: str,
        workstream: str,
        template_cost_range: Tuple[float, float],
        override_cost_range: Tuple[float, float],
        deal_type: str,
        user_count: int,
        user_count_source: str,
        source: str,
        reason: Optional[str],
        session_id: str,
    ):
        """Record a cost override."""

        override = CostOverride(
            activity_name=activity_name,
            activity_id=activity_id,
            workstream=workstream,
            template_cost_range=template_cost_range,
            override_cost_range=override_cost_range,
            deal_type=deal_type,
            user_count=user_count,
            user_count_source=user_count_source,
            source=source,
            reason=reason,
            session_id=session_id,
        )

        self.cost_overrides.append(override)

        logger.info(f"Recorded cost override: {activity_name} "
                    f"${template_cost_range} → ${override_cost_range}")

        if self.storage_path:
            self._save()

    def record_tsa_override(
        self,
        service: str,
        workstream: str,
        template_duration: Optional[Tuple[int, int]],
        override_duration: Tuple[int, int],
        source: str,
        reason: Optional[str],
        session_id: str,
    ):
        """Record a TSA duration override."""

        override = TSAOverride(
            service=service,
            workstream=workstream,
            template_duration=template_duration,
            override_duration=override_duration,
            source=source,
            reason=reason,
            session_id=session_id,
        )

        self.tsa_overrides.append(override)

        logger.info(f"Recorded TSA override: {service} "
                    f"{template_duration} → {override_duration}")

        if self.storage_path:
            self._save()

    def get_template_stats(self, activity_name: str) -> TemplateStats:
        """Get statistics for a specific activity template."""

        relevant = [o for o in self.cost_overrides if o.activity_name == activity_name]

        if not relevant:
            return TemplateStats(activity_name=activity_name, workstream="unknown")

        workstream = relevant[0].workstream

        delta_lows = [o.cost_delta_low for o in relevant]
        delta_highs = [o.cost_delta_high for o in relevant]
        delta_percents = [(o.delta_percent_low + o.delta_percent_high) / 2 for o in relevant]

        contexts = [f"{o.deal_type}>{o.user_count}users" for o in relevant]

        return TemplateStats(
            activity_name=activity_name,
            workstream=workstream,
            total_appearances=len(relevant),  # Approximation
            times_overridden=len(relevant),
            avg_delta_low=sum(delta_lows) / len(delta_lows),
            avg_delta_high=sum(delta_highs) / len(delta_highs),
            avg_delta_percent=sum(delta_percents) / len(delta_percents),
            min_override_low=min(o.override_cost_range[0] for o in relevant),
            max_override_high=max(o.override_cost_range[1] for o in relevant),
            override_contexts=list(set(contexts)),
        )

    def generate_report(self) -> Dict[str, Any]:
        """Generate a report on override patterns."""

        # Group by activity
        activity_overrides: Dict[str, List[CostOverride]] = {}
        for o in self.cost_overrides:
            if o.activity_name not in activity_overrides:
                activity_overrides[o.activity_name] = []
            activity_overrides[o.activity_name].append(o)

        # Calculate stats per activity
        activity_stats = []
        for name, overrides in activity_overrides.items():
            avg_delta = sum(o.delta_percent_low for o in overrides) / len(overrides)
            activity_stats.append({
                "activity": name,
                "workstream": overrides[0].workstream,
                "override_count": len(overrides),
                "avg_delta_percent": avg_delta,
                "contexts": list(set(o.deal_type for o in overrides)),
            })

        # Sort by override frequency
        activity_stats.sort(key=lambda x: x["override_count"], reverse=True)

        # Templates that might need adjustment
        needs_adjustment = [
            s for s in activity_stats
            if s["override_count"] >= 3 or abs(s["avg_delta_percent"]) > 25
        ]

        return {
            "total_cost_overrides": len(self.cost_overrides),
            "total_tsa_overrides": len(self.tsa_overrides),
            "unique_activities_overridden": len(activity_overrides),
            "activity_stats": activity_stats[:10],  # Top 10
            "templates_needing_review": needs_adjustment,
            "recommendations": self._generate_recommendations(needs_adjustment),
        }

    def _generate_recommendations(self, needs_adjustment: List[Dict]) -> List[str]:
        """Generate recommendations based on override patterns."""

        recommendations = []

        for stat in needs_adjustment:
            if stat["avg_delta_percent"] > 25:
                recommendations.append(
                    f"Consider increasing {stat['activity']} template range by "
                    f"~{stat['avg_delta_percent']:.0f}% (overridden {stat['override_count']} times)"
                )
            elif stat["avg_delta_percent"] < -25:
                recommendations.append(
                    f"Consider decreasing {stat['activity']} template range by "
                    f"~{abs(stat['avg_delta_percent']):.0f}% (overridden {stat['override_count']} times)"
                )
            elif stat["override_count"] >= 5:
                recommendations.append(
                    f"Review {stat['activity']} template - frequently overridden "
                    f"({stat['override_count']} times) across {stat['contexts']}"
                )

        return recommendations

    def _save(self):
        """Save to storage."""
        if not self.storage_path:
            return

        data = {
            "cost_overrides": [asdict(o) for o in self.cost_overrides],
            "tsa_overrides": [asdict(o) for o in self.tsa_overrides],
        }

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path) as f:
            data = json.load(f)

        self.cost_overrides = [
            CostOverride(**o) for o in data.get("cost_overrides", [])
        ]
        self.tsa_overrides = [
            TSAOverride(**o) for o in data.get("tsa_overrides", [])
        ]


# Global tracker instance (optional - can be instantiated per-session)
_global_tracker: Optional[FeedbackTracker] = None


def get_feedback_tracker(storage_path: Optional[str] = None) -> FeedbackTracker:
    """Get or create the global feedback tracker."""
    global _global_tracker

    if _global_tracker is None:
        _global_tracker = FeedbackTracker(storage_path)

    return _global_tracker


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'FeedbackTracker',
    'CostOverride',
    'TSAOverride',
    'TemplateStats',
    'get_feedback_tracker',
]
