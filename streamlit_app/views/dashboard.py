"""
Dashboard View

Main dashboard showing executive summary and key metrics.

Steps 99-106 of the alignment plan.
"""

import streamlit as st
from typing import Optional, Dict, Any

from ..components.layout import (
    page_header,
    section_header,
    metric_row,
    empty_state,
)
from ..components.charts import (
    severity_distribution,
    phase_timeline,
    domain_breakdown_bar,
    cost_breakdown_pie,
)
from ..components.badges import severity_badge, domain_badge
from ..utils.formatting import format_cost, format_count


def render_dashboard(
    fact_store: Any,
    reasoning_store: Any,
    target_name: str = "Target Company",
    show_actions: bool = True,
) -> None:
    """
    Render the main dashboard view.

    Args:
        fact_store: FactStore object with extracted facts
        reasoning_store: ReasoningStore with analysis results
        target_name: Name of the target company
        show_actions: Whether to show action buttons
    """
    # Header
    page_header(
        title=f"{target_name} - IT Due Diligence",
        subtitle="Executive Summary",
        icon="📊",
    )

    # Check for data
    if fact_store is None or reasoning_store is None:
        empty_state(
            title="No Analysis Data",
            message="Run an analysis to see the dashboard",
            icon="📊",
        )
        return

    # Key Metrics Row
    _render_key_metrics(fact_store, reasoning_store)

    st.divider()

    # Two-column layout for charts
    col1, col2 = st.columns(2)

    with col1:
        _render_risk_summary(reasoning_store)

    with col2:
        _render_work_items_summary(reasoning_store)

    st.divider()

    # Domain breakdown
    _render_domain_breakdown(fact_store, reasoning_store)

    # Quick actions
    if show_actions:
        st.divider()
        _render_quick_actions()


def _render_key_metrics(fact_store: Any, reasoning_store: Any) -> None:
    """Render the key metrics row."""
    section_header("Key Metrics", icon="📈")

    # Calculate metrics
    fact_count = len(fact_store.facts) if fact_store else 0
    gap_count = len(fact_store.gaps) if fact_store else 0
    risk_count = len(reasoning_store.risks) if reasoning_store else 0
    work_item_count = len(reasoning_store.work_items) if reasoning_store else 0

    # Critical counts
    critical_risks = len([r for r in reasoning_store.risks if r.severity == "critical"]) if reasoning_store else 0
    day1_items = len([w for w in reasoning_store.work_items if w.phase == "Day_1"]) if reasoning_store else 0

    # Render metrics
    metrics = [
        {"value": fact_count, "label": "Facts Extracted", "help": f"{gap_count} gaps identified"},
        {"value": risk_count, "label": "Risks", "help": f"{critical_risks} critical"},
        {"value": work_item_count, "label": "Work Items", "help": f"{day1_items} Day 1 items"},
        {"value": gap_count, "label": "Gaps", "help": "Missing information"},
    ]

    metric_row(metrics)


def _render_risk_summary(reasoning_store: Any) -> None:
    """Render risk summary section."""
    section_header("Risk Overview", icon="⚠️", level=4)

    if not reasoning_store or not reasoning_store.risks:
        st.info("No risks identified")
        return

    # Count by severity
    severity_counts = {}
    for risk in reasoning_store.risks:
        severity = risk.severity or "medium"
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    # Render chart
    severity_distribution(
        counts=severity_counts,
        title="",
        chart_type="bar",
        height=250,
    )

    # Top risks list
    st.markdown("**Top Risks:**")
    critical_high = [r for r in reasoning_store.risks if r.severity in ["critical", "high"]]
    for risk in critical_high[:3]:
        icon = "🔴" if risk.severity == "critical" else "🟠"
        st.markdown(f"- {icon} {risk.title}")

    if len(critical_high) > 3:
        st.caption(f"+ {len(critical_high) - 3} more critical/high risks")


def _render_work_items_summary(reasoning_store: Any) -> None:
    """Render work items summary section."""
    section_header("Work Items by Phase", icon="📋", level=4)

    if not reasoning_store or not reasoning_store.work_items:
        st.info("No work items identified")
        return

    # Count by phase
    phase_counts = {}
    phase_costs = {}

    for wi in reasoning_store.work_items:
        phase = wi.phase or "Day_100"
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

        # Accumulate costs
        cost_low = getattr(wi, "cost_low", 0) or 0
        cost_high = getattr(wi, "cost_high", 0) or 0
        if phase not in phase_costs:
            phase_costs[phase] = {"low": 0, "high": 0}
        phase_costs[phase]["low"] += cost_low
        phase_costs[phase]["high"] += cost_high

    # Render chart
    phase_timeline(
        items_by_phase=phase_counts,
        title="",
        height=250,
    )

    # Cost summary by phase
    st.markdown("**Estimated Costs:**")
    for phase in ["Day_1", "Day_100", "Post_100"]:
        if phase in phase_costs:
            low = phase_costs[phase]["low"]
            high = phase_costs[phase]["high"]
            label = {"Day_1": "Day 1", "Day_100": "Day 100", "Post_100": "Post-100"}[phase]
            if high > 0:
                st.caption(f"{label}: {format_cost(low)} - {format_cost(high)}")


def _render_domain_breakdown(fact_store: Any, reasoning_store: Any) -> None:
    """Render domain breakdown section."""
    section_header("Analysis by Domain", icon="📁", level=4)

    # Count facts by domain
    facts_by_domain = {}
    if fact_store:
        for fact in fact_store.facts:
            domain = fact.domain
            facts_by_domain[domain] = facts_by_domain.get(domain, 0) + 1

    # Count risks by domain
    risks_by_domain = {}
    if reasoning_store:
        for risk in reasoning_store.risks:
            domain = risk.domain
            risks_by_domain[domain] = risks_by_domain.get(domain, 0) + 1

    # Two columns for charts
    col1, col2 = st.columns(2)

    with col1:
        domain_breakdown_bar(
            counts=facts_by_domain,
            title="Facts by Domain",
            height=280,
        )

    with col2:
        domain_breakdown_bar(
            counts=risks_by_domain,
            title="Risks by Domain",
            height=280,
        )


def _render_quick_actions() -> None:
    """Render quick action buttons."""
    section_header("Quick Actions", icon="⚡", level=4)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📥 Export Report", use_container_width=True):
            st.info("Export functionality coming soon")

    with col2:
        if st.button("📋 View All Risks", use_container_width=True):
            st.session_state["current_view"] = "risks"
            st.rerun()

    with col3:
        if st.button("📝 View Work Items", use_container_width=True):
            st.session_state["current_view"] = "work_items"
            st.rerun()

    with col4:
        if st.button("🔄 New Analysis", use_container_width=True):
            st.session_state["analysis_complete"] = False
            st.rerun()


def render_dashboard_summary(
    results: Dict[str, Any],
) -> None:
    """
    Render a compact dashboard summary from results dict.

    Args:
        results: Analysis results dictionary
    """
    fact_count = results.get("facts", {}).get("count", 0)
    gap_count = results.get("facts", {}).get("gaps", 0)
    risk_count = results.get("findings", {}).get("risks", 0)
    work_item_count = results.get("findings", {}).get("work_items", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Facts", fact_count, help=f"{gap_count} gaps")
    with col2:
        st.metric("Risks", risk_count)
    with col3:
        st.metric("Work Items", work_item_count)
    with col4:
        st.metric("VDR Requests", results.get("vdr", {}).get("total", 0))
