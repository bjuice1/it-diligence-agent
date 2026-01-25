"""
Card Components

Reusable card components for displaying data.

Steps 57, 69-78 of the alignment plan.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from .badges import (
    severity_badge,
    domain_badge,
    phase_badge,
    confidence_badge,
    cost_badge,
    status_badge,
)


# =============================================================================
# METRIC CARD
# =============================================================================

def metric_card(
    value: Any,
    label: str,
    delta: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None,
) -> str:
    """
    Render a metric card.

    Args:
        value: The metric value
        label: The metric label
        delta: Optional delta/change indicator
        icon: Optional icon
        color: Optional accent color

    Returns:
        HTML string for the card
    """
    accent = color or "#f97316"
    icon_html = f'<span style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</span>' if icon else ""
    delta_html = f'<div style="font-size: 0.75rem; color: #22c55e; margin-top: 0.25rem;">{delta}</div>' if delta else ""

    return f'''
    <div style="
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    ">
        {icon_html}
        <div style="font-size: 2rem; font-weight: 700; color: #1c1917; line-height: 1.2;">{value}</div>
        <div style="font-size: 0.8rem; color: #a8a29e; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem;">{label}</div>
        {delta_html}
    </div>
    '''


def render_metric_card(value: Any, label: str, **kwargs):
    """Render metric card in Streamlit."""
    st.markdown(metric_card(value, label, **kwargs), unsafe_allow_html=True)


# =============================================================================
# RISK CARD
# =============================================================================

def risk_card(
    risk: Any,
    expanded: bool = False,
    show_evidence: bool = True,
) -> None:
    """
    Render a risk card using Streamlit components.

    Args:
        risk: Risk object with title, description, severity, etc.
        expanded: Whether to show expanded view
        show_evidence: Whether to show evidence citations
    """
    severity = getattr(risk, "severity", "medium")
    title = getattr(risk, "title", "Unknown Risk")
    description = getattr(risk, "description", "")
    domain = getattr(risk, "domain", "")
    mitigation = getattr(risk, "mitigation", "")
    confidence = getattr(risk, "confidence", "medium")
    reasoning = getattr(risk, "reasoning", "")
    based_on_facts = getattr(risk, "based_on_facts", [])
    integration_dependent = getattr(risk, "integration_dependent", False)

    # Header badges
    integration_label = "🔗 Integration" if integration_dependent else "⚡ Standalone"

    with st.expander(f"{title} ({severity.upper()}) - {integration_label}", expanded=expanded):
        # Badges row
        badges_html = f'''
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;">
            {severity_badge(severity)}
            {domain_badge(domain) if domain else ""}
            {confidence_badge(confidence)}
        </div>
        '''
        st.markdown(badges_html, unsafe_allow_html=True)

        # Description
        st.markdown("**Description:**")
        st.write(description)

        # Reasoning
        if reasoning:
            st.markdown("---")
            st.markdown("**💭 Analysis Logic:**")
            st.info(reasoning)

        # Mitigation
        if mitigation:
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Mitigation:**")
                st.write(mitigation)
            with col2:
                st.markdown(f"**Confidence:** {confidence}")

        # Evidence
        if show_evidence and based_on_facts:
            st.caption(f"📋 Evidence: {', '.join(based_on_facts)}")


# =============================================================================
# WORK ITEM CARD
# =============================================================================

def work_item_card(
    work_item: Any,
    expanded: bool = False,
    show_evidence: bool = True,
) -> None:
    """
    Render a work item card using Streamlit components.

    Args:
        work_item: WorkItem object
        expanded: Whether to show expanded view
        show_evidence: Whether to show evidence citations
    """
    title = getattr(work_item, "title", "Unknown Work Item")
    description = getattr(work_item, "description", "")
    phase = getattr(work_item, "phase", "Day_100")
    priority = getattr(work_item, "priority", "medium")
    cost_estimate = getattr(work_item, "cost_estimate", "TBD")
    owner_type = getattr(work_item, "owner_type", "buyer")
    confidence = getattr(work_item, "confidence", "medium")
    reasoning = getattr(work_item, "reasoning", "")
    based_on_facts = getattr(work_item, "based_on_facts", [])
    triggered_by = getattr(work_item, "triggered_by", [])
    dependencies = getattr(work_item, "dependencies", [])

    priority_icon = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }.get(priority, "⚪")

    with st.expander(f"{priority_icon} {title} | {cost_estimate} | {owner_type}", expanded=expanded):
        # Badges row
        badges_html = f'''
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;">
            {phase_badge(phase)}
            {severity_badge(priority)}
            {cost_badge(cost_estimate)}
        </div>
        '''
        st.markdown(badges_html, unsafe_allow_html=True)

        # Description
        st.markdown("**Description:**")
        st.write(description)

        # Reasoning
        if reasoning:
            st.markdown("---")
            st.markdown("**💭 Why This Work Is Needed:**")
            st.info(reasoning)

        # Details
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Owner:** {owner_type}")
        with col2:
            st.markdown(f"**Priority:** {priority}")
        with col3:
            st.markdown(f"**Confidence:** {confidence}")

        # Dependencies
        if dependencies:
            st.markdown(f"**Dependencies:** {', '.join(dependencies)}")

        # Evidence
        if show_evidence:
            if triggered_by:
                st.caption(f"📋 Triggered by: {', '.join(triggered_by)}")
            if based_on_facts:
                st.caption(f"📋 Evidence: {', '.join(based_on_facts)}")


# =============================================================================
# FACT CARD
# =============================================================================

def fact_card(
    fact: Any,
    show_details: bool = True,
    show_evidence: bool = True,
) -> None:
    """
    Render a fact card using Streamlit components.

    Args:
        fact: Fact object
        show_details: Whether to show detail fields
        show_evidence: Whether to show source quote
    """
    fact_id = getattr(fact, "fact_id", "")
    item = getattr(fact, "item", "")
    domain = getattr(fact, "domain", "")
    category = getattr(fact, "category", "")
    status = getattr(fact, "status", "documented")
    entity = getattr(fact, "entity", "target")
    details = getattr(fact, "details", {})
    evidence = getattr(fact, "evidence", {})

    entity_badge = "🎯" if entity == "target" else "🏢"
    status_icon = {"documented": "✅", "partial": "⚠️", "gap": "❌"}.get(status, "")

    # Header
    st.markdown(f"**{fact_id}** {entity_badge} {status_icon} `{item}`")

    # Synthesized statement
    statement = _synthesize_fact_statement(fact)
    st.markdown(f"> {statement}")

    # Details
    if show_details and details:
        details_str = ", ".join([
            f"{k}: {v}"
            for k, v in details.items()
            if v and v != "not_stated"
        ])
        if details_str:
            st.caption(f"📋 {details_str}")

    # Source quote
    if show_evidence and evidence.get("exact_quote"):
        quote = evidence["exact_quote"]
        if len(quote) > 150:
            quote = quote[:150] + "..."
        st.caption(f'📄 Source: "{quote}"')


def _synthesize_fact_statement(fact: Any) -> str:
    """Synthesize a fact statement from details."""
    item = getattr(fact, "item", "")
    details = getattr(fact, "details", {})

    parts = [item]

    # Add key details
    if details.get("version"):
        parts.append(f"(v{details['version']})")
    if details.get("count"):
        parts.append(f"- {details['count']} units")
    if details.get("vendor"):
        parts.append(f"by {details['vendor']}")
    if details.get("status"):
        parts.append(f"[{details['status']}]")

    return " ".join(parts)


# =============================================================================
# GAP CARD
# =============================================================================

def gap_card(
    gap: Any,
    expanded: bool = False,
) -> None:
    """
    Render a gap card using Streamlit components.

    Args:
        gap: Gap object
        expanded: Whether to show expanded view
    """
    gap_id = getattr(gap, "gap_id", "")
    description = getattr(gap, "description", "")
    domain = getattr(gap, "domain", "")
    category = getattr(gap, "category", "")
    importance = getattr(gap, "importance", "medium")

    importance_icon = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }.get(importance, "⚪")

    short_desc = description[:50] + "..." if len(description) > 50 else description

    with st.expander(f"{importance_icon} {gap_id}: {short_desc}", expanded=expanded):
        st.markdown(f"**Domain:** {domain}")
        st.markdown(f"**Category:** {category}")
        st.markdown(f"**Description:** {description}")
        st.markdown(f"**Importance:** {importance}")


# =============================================================================
# COLLAPSIBLE CARD
# =============================================================================

def collapsible_card(
    title: str,
    content: str,
    expanded: bool = False,
    icon: Optional[str] = None,
) -> None:
    """
    Render a simple collapsible card.

    Args:
        title: Card title
        content: Card content (markdown)
        expanded: Whether to start expanded
        icon: Optional icon
    """
    header = f"{icon} {title}" if icon else title
    with st.expander(header, expanded=expanded):
        st.markdown(content)


# =============================================================================
# COVERAGE SCORE CARD
# =============================================================================

def coverage_score_card(
    domain: str,
    score: float,
    grade: str,
    missing_items: List[str] = None,
) -> None:
    """
    Render a coverage score card.

    Args:
        domain: Domain name
        score: Coverage score (0-100)
        grade: Letter grade (A-F)
        missing_items: List of missing critical items
    """
    # Color based on grade
    grade_colors = {
        "A": "#22c55e",
        "B": "#84cc16",
        "C": "#eab308",
        "D": "#f97316",
        "F": "#dc2626",
    }
    color = grade_colors.get(grade[0], "#6b7280")

    st.markdown(f'''
    <div style="
        background: white;
        border: 1px solid #e5e7eb;
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-weight: 600; color: #1c1917;">{domain.replace("_", " ").title()}</div>
                <div style="font-size: 0.8rem; color: #6b7280;">{score:.0f}% coverage</div>
            </div>
            <div style="
                font-size: 1.5rem;
                font-weight: 700;
                color: {color};
            ">{grade}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if missing_items:
        with st.expander("Missing items"):
            for item in missing_items:
                st.markdown(f"- {item}")
