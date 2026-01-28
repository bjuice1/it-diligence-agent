"""
Validation Metrics and Analytics

Phase 17: Monitoring & Analytics (Points 231-240)
- Metrics collection for validation runs
- Analytics for pass rates, confidence, flag types
- Dashboard data generation

Usage:
    metrics = ValidationMetrics()
    metrics.record_validation_run(domain, result)
    dashboard_data = metrics.get_dashboard_data()
"""

import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from collections import defaultdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# METRICS ENUMS AND DATACLASSES
# =============================================================================

class MetricType(Enum):
    """Types of metrics collected."""
    VALIDATION_RUN = "validation_run"
    REEXTRACTION = "reextraction"
    HUMAN_REVIEW = "human_review"
    CORRECTION = "correction"
    FLAG_GENERATED = "flag_generated"
    FLAG_RESOLVED = "flag_resolved"
    ESCALATION = "escalation"


@dataclass
class MetricEntry:
    """A single metric entry."""
    metric_type: MetricType
    timestamp: datetime
    domain: Optional[str] = None
    category: Optional[str] = None
    value: float = 1.0
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeSeriesPoint:
    """A point in a time series."""
    timestamp: datetime
    value: float


@dataclass
class AggregatedMetric:
    """Aggregated metric with statistics."""
    name: str
    count: int
    total: float
    average: float
    min_value: float
    max_value: float
    time_series: List[TimeSeriesPoint] = field(default_factory=list)


# =============================================================================
# METRICS COLLECTION (Points 231-235)
# =============================================================================

class ValidationMetrics:
    """
    Collects and stores validation metrics.

    Tracks:
    - validation_runs_total (Point 231)
    - reextraction_triggers_total (Point 232)
    - human_reviews_total (Point 233)
    - corrections_total (Point 234)
    - flags_generated_total (Point 235)
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._entries: List[MetricEntry] = []
        self._counters: Dict[str, int] = defaultdict(int)
        self._storage_path = storage_path

    # -------------------------------------------------------------------------
    # Recording Methods
    # -------------------------------------------------------------------------

    def record_validation_run(
        self,
        domain: str,
        passed: bool,
        confidence: float,
        duration_ms: float,
        facts_validated: int,
    ) -> None:
        """Record a validation run (Point 231)."""
        self._entries.append(MetricEntry(
            metric_type=MetricType.VALIDATION_RUN,
            timestamp=datetime.now(),
            domain=domain,
            value=1 if passed else 0,
            labels={
                "passed": str(passed),
                "domain": domain,
            },
            metadata={
                "confidence": confidence,
                "duration_ms": duration_ms,
                "facts_validated": facts_validated,
            }
        ))
        self._counters["validation_runs_total"] += 1
        if passed:
            self._counters["validation_passes_total"] += 1

    def record_reextraction(
        self,
        domain: str,
        attempt: int,
        reason: str,
        improved: bool,
    ) -> None:
        """Record a reextraction trigger (Point 232)."""
        self._entries.append(MetricEntry(
            metric_type=MetricType.REEXTRACTION,
            timestamp=datetime.now(),
            domain=domain,
            value=attempt,
            labels={
                "domain": domain,
                "reason": reason,
            },
            metadata={
                "attempt": attempt,
                "improved": improved,
            }
        ))
        self._counters["reextraction_triggers_total"] += 1

    def record_human_review(
        self,
        domain: str,
        reviewer: str,
        action: str,  # "confirmed", "corrected", "rejected", "skipped"
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Record a human review (Point 233)."""
        self._entries.append(MetricEntry(
            metric_type=MetricType.HUMAN_REVIEW,
            timestamp=datetime.now(),
            domain=domain,
            value=1,
            labels={
                "domain": domain,
                "action": action,
                "reviewer": reviewer,
            },
            metadata={
                "duration_seconds": duration_seconds,
            }
        ))
        self._counters["human_reviews_total"] += 1
        self._counters[f"human_reviews_{action}"] += 1

    def record_correction(
        self,
        domain: str,
        fact_id: str,
        field_corrected: str,
        ripple_effects: int,
    ) -> None:
        """Record a correction (Point 234)."""
        self._entries.append(MetricEntry(
            metric_type=MetricType.CORRECTION,
            timestamp=datetime.now(),
            domain=domain,
            value=1,
            labels={
                "domain": domain,
                "field": field_corrected,
            },
            metadata={
                "fact_id": fact_id,
                "ripple_effects": ripple_effects,
            }
        ))
        self._counters["corrections_total"] += 1

    def record_flag(
        self,
        domain: str,
        severity: str,
        category: str,
        resolved: bool = False,
    ) -> None:
        """Record a flag generated or resolved (Point 235)."""
        metric_type = MetricType.FLAG_RESOLVED if resolved else MetricType.FLAG_GENERATED

        self._entries.append(MetricEntry(
            metric_type=metric_type,
            timestamp=datetime.now(),
            domain=domain,
            category=category,
            value=1,
            labels={
                "domain": domain,
                "severity": severity,
                "category": category,
            },
        ))

        if resolved:
            self._counters["flags_resolved_total"] += 1
        else:
            self._counters["flags_generated_total"] += 1
            self._counters[f"flags_{severity}"] += 1

    def record_escalation(
        self,
        domain: str,
        attempts: int,
        remaining_issues: int,
    ) -> None:
        """Record an escalation."""
        self._entries.append(MetricEntry(
            metric_type=MetricType.ESCALATION,
            timestamp=datetime.now(),
            domain=domain,
            value=1,
            labels={"domain": domain},
            metadata={
                "attempts": attempts,
                "remaining_issues": remaining_issues,
            }
        ))
        self._counters["escalations_total"] += 1

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def get_counter(self, name: str) -> int:
        """Get a counter value."""
        return self._counters.get(name, 0)

    def get_all_counters(self) -> Dict[str, int]:
        """Get all counter values."""
        return dict(self._counters)

    def get_entries(
        self,
        metric_type: Optional[MetricType] = None,
        domain: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[MetricEntry]:
        """Get metric entries with filters."""
        entries = self._entries

        if metric_type:
            entries = [e for e in entries if e.metric_type == metric_type]

        if domain:
            entries = [e for e in entries if e.domain == domain]

        if since:
            entries = [e for e in entries if e.timestamp >= since]

        if until:
            entries = [e for e in entries if e.timestamp <= until]

        return entries

    def get_validation_pass_rate(
        self,
        domain: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> float:
        """Get validation pass rate."""
        entries = self.get_entries(
            metric_type=MetricType.VALIDATION_RUN,
            domain=domain,
            since=since,
        )

        if not entries:
            return 0.0

        passed = sum(1 for e in entries if e.labels.get("passed") == "True")
        return passed / len(entries)

    def get_average_confidence(
        self,
        domain: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> float:
        """Get average confidence score."""
        entries = self.get_entries(
            metric_type=MetricType.VALIDATION_RUN,
            domain=domain,
            since=since,
        )

        if not entries:
            return 0.0

        confidences = [e.metadata.get("confidence", 0) for e in entries]
        return sum(confidences) / len(confidences)

    def get_flag_distribution(
        self,
        since: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """Get distribution of flags by severity."""
        return {
            "critical": self._counters.get("flags_critical", 0),
            "error": self._counters.get("flags_error", 0),
            "warning": self._counters.get("flags_warning", 0),
            "info": self._counters.get("flags_info", 0),
        }

    def get_review_turnaround(
        self,
        since: Optional[datetime] = None,
    ) -> Optional[float]:
        """Get average review turnaround time in seconds."""
        entries = self.get_entries(
            metric_type=MetricType.HUMAN_REVIEW,
            since=since,
        )

        durations = [
            e.metadata.get("duration_seconds")
            for e in entries
            if e.metadata.get("duration_seconds") is not None
        ]

        if not durations:
            return None

        return sum(durations) / len(durations)

    def get_correction_rate(self) -> float:
        """Get correction rate (corrections / reviews)."""
        reviews = self._counters.get("human_reviews_total", 0)
        corrections = self._counters.get("corrections_total", 0)

        if reviews == 0:
            return 0.0

        return corrections / reviews

    # -------------------------------------------------------------------------
    # Time Series Methods
    # -------------------------------------------------------------------------

    def get_time_series(
        self,
        metric_type: MetricType,
        interval: str = "hour",  # "hour", "day", "week"
        domain: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[TimeSeriesPoint]:
        """Get time series data for a metric."""
        entries = self.get_entries(
            metric_type=metric_type,
            domain=domain,
            since=since,
        )

        if not entries:
            return []

        # Group by interval
        if interval == "hour":
            bucket_fn = lambda dt: dt.replace(minute=0, second=0, microsecond=0)
        elif interval == "day":
            bucket_fn = lambda dt: dt.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # week
            bucket_fn = lambda dt: (dt - timedelta(days=dt.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        buckets = defaultdict(float)
        for entry in entries:
            bucket = bucket_fn(entry.timestamp)
            buckets[bucket] += entry.value

        return [
            TimeSeriesPoint(timestamp=ts, value=val)
            for ts, val in sorted(buckets.items())
        ]


# =============================================================================
# ANALYTICS DASHBOARD (Points 236-240)
# =============================================================================

@dataclass
class DashboardData:
    """Data for analytics dashboard."""
    # Summary stats
    total_validations: int
    pass_rate: float
    average_confidence: float
    total_flags: int
    total_reviews: int
    correction_rate: float

    # Charts
    pass_rate_over_time: List[TimeSeriesPoint]
    confidence_by_domain: Dict[str, float]
    flag_distribution: Dict[str, int]
    review_turnaround_avg: Optional[float]
    corrections_over_time: List[TimeSeriesPoint]

    # Domain breakdown
    domain_stats: Dict[str, Dict[str, Any]]


class AnalyticsDashboard:
    """
    Generates analytics dashboard data.

    Charts (Points 236-240):
    - Validation pass rate over time
    - Average confidence by domain
    - Common flag types
    - Human review turnaround
    - Correction rate
    """

    def __init__(self, metrics: ValidationMetrics):
        self.metrics = metrics

    def get_dashboard_data(
        self,
        since: Optional[datetime] = None,
        domains: Optional[List[str]] = None,
    ) -> DashboardData:
        """Generate full dashboard data."""
        if since is None:
            since = datetime.now() - timedelta(days=30)

        # Summary stats
        counters = self.metrics.get_all_counters()

        # Confidence by domain
        confidence_by_domain = {}
        for domain in (domains or ["infrastructure", "network", "applications", "organization", "cybersecurity"]):
            conf = self.metrics.get_average_confidence(domain=domain, since=since)
            if conf > 0:
                confidence_by_domain[domain] = conf

        # Domain stats
        domain_stats = {}
        for domain in (domains or ["infrastructure", "network", "applications", "organization", "cybersecurity"]):
            entries = self.metrics.get_entries(
                metric_type=MetricType.VALIDATION_RUN,
                domain=domain,
                since=since,
            )
            if entries:
                domain_stats[domain] = {
                    "validations": len(entries),
                    "pass_rate": self.metrics.get_validation_pass_rate(domain=domain, since=since),
                    "avg_confidence": self.metrics.get_average_confidence(domain=domain, since=since),
                }

        return DashboardData(
            total_validations=counters.get("validation_runs_total", 0),
            pass_rate=self.metrics.get_validation_pass_rate(since=since),
            average_confidence=self.metrics.get_average_confidence(since=since),
            total_flags=counters.get("flags_generated_total", 0),
            total_reviews=counters.get("human_reviews_total", 0),
            correction_rate=self.metrics.get_correction_rate(),
            pass_rate_over_time=self.metrics.get_time_series(
                MetricType.VALIDATION_RUN,
                interval="day",
                since=since,
            ),
            confidence_by_domain=confidence_by_domain,
            flag_distribution=self.metrics.get_flag_distribution(since=since),
            review_turnaround_avg=self.metrics.get_review_turnaround(since=since),
            corrections_over_time=self.metrics.get_time_series(
                MetricType.CORRECTION,
                interval="day",
                since=since,
            ),
            domain_stats=domain_stats,
        )

    def get_chart_data(
        self,
        chart_type: str,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get data for a specific chart.

        Chart types:
        - pass_rate_over_time (Point 236)
        - confidence_by_domain (Point 237)
        - flag_types (Point 238)
        - review_turnaround (Point 239)
        - correction_rate (Point 240)
        """
        if since is None:
            since = datetime.now() - timedelta(days=30)

        if chart_type == "pass_rate_over_time":
            time_series = self.metrics.get_time_series(
                MetricType.VALIDATION_RUN,
                interval="day",
                since=since,
            )
            return {
                "type": "line",
                "title": "Validation Pass Rate Over Time",
                "data": [
                    {"date": p.timestamp.isoformat(), "value": p.value}
                    for p in time_series
                ],
                "x_label": "Date",
                "y_label": "Pass Rate",
            }

        elif chart_type == "confidence_by_domain":
            domains = ["infrastructure", "network", "applications", "organization", "cybersecurity"]
            data = []
            for domain in domains:
                conf = self.metrics.get_average_confidence(domain=domain, since=since)
                if conf > 0:
                    data.append({"domain": domain, "confidence": conf})

            return {
                "type": "bar",
                "title": "Average Confidence by Domain",
                "data": data,
                "x_label": "Domain",
                "y_label": "Confidence",
            }

        elif chart_type == "flag_types":
            distribution = self.metrics.get_flag_distribution(since=since)
            return {
                "type": "pie",
                "title": "Common Flag Types",
                "data": [
                    {"severity": k, "count": v}
                    for k, v in distribution.items()
                    if v > 0
                ],
            }

        elif chart_type == "review_turnaround":
            # Get review entries with duration
            entries = self.metrics.get_entries(
                metric_type=MetricType.HUMAN_REVIEW,
                since=since,
            )

            # Group by day
            by_day = defaultdict(list)
            for entry in entries:
                if entry.metadata.get("duration_seconds"):
                    day = entry.timestamp.date()
                    by_day[day].append(entry.metadata["duration_seconds"])

            data = [
                {
                    "date": str(day),
                    "avg_seconds": sum(durations) / len(durations),
                }
                for day, durations in sorted(by_day.items())
            ]

            return {
                "type": "line",
                "title": "Human Review Turnaround Time",
                "data": data,
                "x_label": "Date",
                "y_label": "Average Seconds",
            }

        elif chart_type == "correction_rate":
            time_series = self.metrics.get_time_series(
                MetricType.CORRECTION,
                interval="day",
                since=since,
            )
            return {
                "type": "line",
                "title": "Corrections Over Time",
                "data": [
                    {"date": p.timestamp.isoformat(), "count": p.value}
                    for p in time_series
                ],
                "x_label": "Date",
                "y_label": "Corrections",
            }

        else:
            raise ValueError(f"Unknown chart type: {chart_type}")


# =============================================================================
# PROMETHEUS-STYLE METRICS EXPORT
# =============================================================================

class MetricsExporter:
    """Export metrics in Prometheus format."""

    def __init__(self, metrics: ValidationMetrics):
        self.metrics = metrics

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        counters = self.metrics.get_all_counters()

        # Add counters
        for name, value in counters.items():
            metric_name = f"validation_{name}"
            lines.append(f"# HELP {metric_name} Total count of {name}")
            lines.append(f"# TYPE {metric_name} counter")
            lines.append(f"{metric_name} {value}")

        # Add gauges for rates
        pass_rate = self.metrics.get_validation_pass_rate()
        lines.append("# HELP validation_pass_rate Current validation pass rate")
        lines.append("# TYPE validation_pass_rate gauge")
        lines.append(f"validation_pass_rate {pass_rate}")

        avg_confidence = self.metrics.get_average_confidence()
        lines.append("# HELP validation_avg_confidence Average validation confidence")
        lines.append("# TYPE validation_avg_confidence gauge")
        lines.append(f"validation_avg_confidence {avg_confidence}")

        correction_rate = self.metrics.get_correction_rate()
        lines.append("# HELP validation_correction_rate Correction rate")
        lines.append("# TYPE validation_correction_rate gauge")
        lines.append(f"validation_correction_rate {correction_rate}")

        return "\n".join(lines)

    def export_json(self) -> str:
        """Export metrics as JSON."""
        data = {
            "counters": self.metrics.get_all_counters(),
            "rates": {
                "pass_rate": self.metrics.get_validation_pass_rate(),
                "avg_confidence": self.metrics.get_average_confidence(),
                "correction_rate": self.metrics.get_correction_rate(),
            },
            "flag_distribution": self.metrics.get_flag_distribution(),
            "exported_at": datetime.now().isoformat(),
        }
        return json.dumps(data, indent=2)
