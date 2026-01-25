"""
Chart Components

Visualization components for coverage, severity, phases, and costs.

Steps 79-85 of the alignment plan.
"""

import streamlit as st
from typing import Dict, List, Optional, Any

# Try to import plotly, fall back to basic charts if not available
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# =============================================================================
# COLORS
# =============================================================================

DOMAIN_COLORS = {
    "infrastructure": "#3b82f6",
    "network": "#6366f1",
    "cybersecurity": "#ec4899",
    "applications": "#10b981",
    "identity_access": "#f59e0b",
    "organization": "#8b5cf6",
}

SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#22c55e",
}

PHASE_COLORS = {
    "Day_1": "#dc2626",
    "Day_100": "#f59e0b",
    "Post_100": "#22c55e",
}


# =============================================================================
# COVERAGE RADAR CHART
# =============================================================================

def coverage_radar(
    coverage_scores: Dict[str, float],
    title: str = "Coverage by Domain",
    height: int = 400,
) -> None:
    """
    Render a radar chart of coverage scores by domain.

    Args:
        coverage_scores: Dict of domain -> score (0-100)
        title: Chart title
        height: Chart height in pixels
    """
    if not PLOTLY_AVAILABLE:
        _fallback_coverage_display(coverage_scores, title)
        return

    domains = list(coverage_scores.keys())
    scores = list(coverage_scores.values())

    # Close the radar by repeating first value
    domains = domains + [domains[0]]
    scores = scores + [scores[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=[d.replace("_", " ").title() for d in domains],
        fill='toself',
        fillcolor='rgba(249, 115, 22, 0.2)',
        line=dict(color='#f97316', width=2),
        name='Coverage'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix='%',
            ),
        ),
        showlegend=False,
        title=title,
        height=height,
        margin=dict(l=50, r=50, t=60, b=50),
    )

    st.plotly_chart(fig, use_container_width=True)


def _fallback_coverage_display(coverage_scores: Dict[str, float], title: str):
    """Fallback display when plotly not available."""
    st.subheader(title)
    for domain, score in coverage_scores.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(score / 100)
        with col2:
            st.write(f"{domain.replace('_', ' ').title()}: {score:.0f}%")


# =============================================================================
# SEVERITY DISTRIBUTION
# =============================================================================

def severity_distribution(
    counts: Dict[str, int],
    title: str = "Risk Severity Distribution",
    chart_type: str = "bar",
    height: int = 300,
) -> None:
    """
    Render severity distribution chart.

    Args:
        counts: Dict of severity -> count
        title: Chart title
        chart_type: "bar" or "pie"
        height: Chart height in pixels
    """
    if not PLOTLY_AVAILABLE:
        _fallback_severity_display(counts, title)
        return

    severities = ["critical", "high", "medium", "low"]
    values = [counts.get(s, 0) for s in severities]
    colors = [SEVERITY_COLORS[s] for s in severities]

    if chart_type == "pie":
        fig = go.Figure(data=[go.Pie(
            labels=[s.title() for s in severities],
            values=values,
            marker=dict(colors=colors),
            hole=0.4,
        )])
    else:
        fig = go.Figure(data=[go.Bar(
            x=[s.title() for s in severities],
            y=values,
            marker_color=colors,
        )])

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=chart_type == "pie",
    )

    st.plotly_chart(fig, use_container_width=True)


def _fallback_severity_display(counts: Dict[str, int], title: str):
    """Fallback display when plotly not available."""
    st.subheader(title)
    for severity in ["critical", "high", "medium", "low"]:
        count = counts.get(severity, 0)
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}[severity]
        st.write(f"{icon} {severity.title()}: {count}")


# =============================================================================
# PHASE TIMELINE
# =============================================================================

def phase_timeline(
    items_by_phase: Dict[str, int],
    title: str = "Work Items by Phase",
    height: int = 300,
) -> None:
    """
    Render a phase timeline chart.

    Args:
        items_by_phase: Dict of phase -> count
        title: Chart title
        height: Chart height in pixels
    """
    if not PLOTLY_AVAILABLE:
        _fallback_phase_display(items_by_phase, title)
        return

    phases = ["Day_1", "Day_100", "Post_100"]
    phase_labels = ["Day 1", "Day 100", "Post-100"]
    values = [items_by_phase.get(p, 0) for p in phases]
    colors = [PHASE_COLORS[p] for p in phases]

    fig = go.Figure(data=[go.Bar(
        x=phase_labels,
        y=values,
        marker_color=colors,
        text=values,
        textposition='auto',
    )])

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_title="Phase",
        yaxis_title="Count",
    )

    st.plotly_chart(fig, use_container_width=True)


def _fallback_phase_display(items_by_phase: Dict[str, int], title: str):
    """Fallback display when plotly not available."""
    st.subheader(title)
    phase_labels = {"Day_1": "🚨 Day 1", "Day_100": "📅 Day 100", "Post_100": "🎯 Post-100"}
    for phase, label in phase_labels.items():
        count = items_by_phase.get(phase, 0)
        st.write(f"{label}: {count}")


# =============================================================================
# COST BREAKDOWN PIE
# =============================================================================

def cost_breakdown_pie(
    costs: Dict[str, float],
    title: str = "Cost Breakdown",
    group_by: str = "domain",
    height: int = 350,
) -> None:
    """
    Render a pie chart of cost breakdown.

    Args:
        costs: Dict of category -> cost value
        title: Chart title
        group_by: "domain" or "phase"
        height: Chart height in pixels
    """
    if not costs or sum(costs.values()) == 0:
        st.info("No cost data available")
        return

    if not PLOTLY_AVAILABLE:
        _fallback_cost_display(costs, title)
        return

    labels = list(costs.keys())
    values = list(costs.values())

    # Get colors based on group_by
    if group_by == "domain":
        colors = [DOMAIN_COLORS.get(l, "#6b7280") for l in labels]
        labels = [l.replace("_", " ").title() for l in labels]
    else:
        colors = [PHASE_COLORS.get(l, "#6b7280") for l in labels]
        labels = [{"Day_1": "Day 1", "Day_100": "Day 100", "Post_100": "Post-100"}.get(l, l) for l in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
    )])

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )

    st.plotly_chart(fig, use_container_width=True)


def _fallback_cost_display(costs: Dict[str, float], title: str):
    """Fallback display when plotly not available."""
    st.subheader(title)
    total = sum(costs.values())
    for category, value in costs.items():
        pct = (value / total * 100) if total > 0 else 0
        st.write(f"{category.replace('_', ' ').title()}: ${value:,.0f} ({pct:.1f}%)")


# =============================================================================
# DOMAIN BREAKDOWN BAR
# =============================================================================

def domain_breakdown_bar(
    counts: Dict[str, int],
    title: str = "Items by Domain",
    orientation: str = "h",
    height: int = 300,
) -> None:
    """
    Render a bar chart of counts by domain.

    Args:
        counts: Dict of domain -> count
        title: Chart title
        orientation: "h" for horizontal, "v" for vertical
        height: Chart height in pixels
    """
    if not PLOTLY_AVAILABLE:
        _fallback_domain_display(counts, title)
        return

    domains = list(counts.keys())
    values = list(counts.values())
    colors = [DOMAIN_COLORS.get(d, "#6b7280") for d in domains]
    labels = [d.replace("_", " ").title() for d in domains]

    if orientation == "h":
        fig = go.Figure(data=[go.Bar(
            y=labels,
            x=values,
            orientation='h',
            marker_color=colors,
            text=values,
            textposition='auto',
        )])
    else:
        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=values,
            textposition='auto',
        )])

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=120 if orientation == "h" else 40, r=40, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)


def _fallback_domain_display(counts: Dict[str, int], title: str):
    """Fallback display when plotly not available."""
    st.subheader(title)
    for domain, count in counts.items():
        st.write(f"{domain.replace('_', ' ').title()}: {count}")


# =============================================================================
# COST RANGE VISUALIZATION
# =============================================================================

def cost_range_chart(
    work_items: List[Any],
    title: str = "Cost Estimates by Phase",
    height: int = 400,
) -> None:
    """
    Render a cost range visualization showing low/high estimates.

    Args:
        work_items: List of work item objects with cost_low, cost_high, phase
        title: Chart title
        height: Chart height in pixels
    """
    if not work_items:
        st.info("No work items with cost estimates")
        return

    # Aggregate by phase
    phase_costs = {}
    for wi in work_items:
        phase = getattr(wi, "phase", "Day_100")
        cost_low = getattr(wi, "cost_low", 0) or 0
        cost_high = getattr(wi, "cost_high", 0) or 0

        if phase not in phase_costs:
            phase_costs[phase] = {"low": 0, "high": 0}
        phase_costs[phase]["low"] += cost_low
        phase_costs[phase]["high"] += cost_high

    # Display as table if plotly not available
    if not PLOTLY_AVAILABLE:
        st.subheader(title)
        for phase in ["Day_1", "Day_100", "Post_100"]:
            if phase in phase_costs:
                low = phase_costs[phase]["low"]
                high = phase_costs[phase]["high"]
                st.write(f"{phase}: ${low:,.0f} - ${high:,.0f}")
        return

    # Create range chart
    phases = ["Day_1", "Day_100", "Post_100"]
    phase_labels = ["Day 1", "Day 100", "Post-100"]

    lows = [phase_costs.get(p, {}).get("low", 0) for p in phases]
    highs = [phase_costs.get(p, {}).get("high", 0) for p in phases]

    fig = go.Figure()

    # Add range bars
    for i, (label, low, high) in enumerate(zip(phase_labels, lows, highs)):
        color = PHASE_COLORS[phases[i]]
        fig.add_trace(go.Bar(
            x=[label],
            y=[high - low],
            base=[low],
            name=label,
            marker_color=color,
            text=[f"${low/1000:.0f}K - ${high/1000:.0f}K"],
            textposition='outside',
        ))

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis_title="Cost ($)",
        showlegend=False,
        yaxis=dict(tickformat="$,.0f"),
    )

    st.plotly_chart(fig, use_container_width=True)
