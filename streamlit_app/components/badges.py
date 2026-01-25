"""
Badge Components

Visual badges for severity, domain, phase, confidence, cost, and status.

Steps 58-62 of the alignment plan.
"""

import streamlit as st
from typing import Optional


# =============================================================================
# STYLING
# =============================================================================

SEVERITY_COLORS = {
    "critical": {"bg": "#fecaca", "text": "#991b1b", "icon": "🔴"},
    "high": {"bg": "#ffedd5", "text": "#c2410c", "icon": "🟠"},
    "medium": {"bg": "#fef3c7", "text": "#a16207", "icon": "🟡"},
    "low": {"bg": "#dcfce7", "text": "#166534", "icon": "🟢"},
}

DOMAIN_COLORS = {
    "infrastructure": {"bg": "#dbeafe", "text": "#1e40af", "icon": "🖥️"},
    "network": {"bg": "#e0e7ff", "text": "#3730a3", "icon": "🌐"},
    "cybersecurity": {"bg": "#fce7f3", "text": "#9d174d", "icon": "🔒"},
    "applications": {"bg": "#d1fae5", "text": "#065f46", "icon": "📱"},
    "identity_access": {"bg": "#fef3c7", "text": "#92400e", "icon": "🔑"},
    "organization": {"bg": "#f3e8ff", "text": "#6b21a8", "icon": "👥"},
}

PHASE_COLORS = {
    "Day_1": {"bg": "#fecaca", "text": "#991b1b", "icon": "🚨", "label": "Day 1"},
    "Day_100": {"bg": "#fef3c7", "text": "#92400e", "icon": "📅", "label": "Day 100"},
    "Post_100": {"bg": "#d1fae5", "text": "#065f46", "icon": "🎯", "label": "Post-100"},
}

CONFIDENCE_COLORS = {
    "high": {"bg": "#dcfce7", "text": "#166534"},
    "medium": {"bg": "#fef3c7", "text": "#a16207"},
    "low": {"bg": "#fecaca", "text": "#991b1b"},
}

STATUS_COLORS = {
    "documented": {"bg": "#dcfce7", "text": "#166534", "icon": "✅"},
    "partial": {"bg": "#fef3c7", "text": "#a16207", "icon": "⚠️"},
    "gap": {"bg": "#fecaca", "text": "#991b1b", "icon": "❌"},
    "open": {"bg": "#dbeafe", "text": "#1e40af", "icon": "🔵"},
    "answered": {"bg": "#dcfce7", "text": "#166534", "icon": "✓"},
    "deferred": {"bg": "#f3e8ff", "text": "#6b21a8", "icon": "⏳"},
}


# =============================================================================
# BADGE FUNCTIONS
# =============================================================================

def severity_badge(
    severity: str,
    show_icon: bool = True,
    size: str = "normal"
) -> str:
    """
    Render a severity badge.

    Args:
        severity: Severity level (critical, high, medium, low)
        show_icon: Whether to show the icon
        size: Badge size (small, normal, large)

    Returns:
        HTML string for the badge
    """
    colors = SEVERITY_COLORS.get(severity.lower(), SEVERITY_COLORS["medium"])

    font_size = {"small": "0.7rem", "normal": "0.75rem", "large": "0.85rem"}.get(size, "0.75rem")
    padding = {"small": "0.15rem 0.35rem", "normal": "0.25rem 0.5rem", "large": "0.3rem 0.6rem"}.get(size, "0.25rem 0.5rem")

    icon = colors["icon"] + " " if show_icon else ""
    label = severity.upper()

    return f'''
    <span style="
        display: inline-block;
        padding: {padding};
        border-radius: 9999px;
        font-size: {font_size};
        font-weight: 600;
        text-transform: uppercase;
        background: {colors["bg"]};
        color: {colors["text"]};
    ">{icon}{label}</span>
    '''


def domain_badge(
    domain: str,
    show_icon: bool = True,
    size: str = "normal"
) -> str:
    """
    Render a domain badge.

    Args:
        domain: Domain name
        show_icon: Whether to show the icon
        size: Badge size (small, normal, large)

    Returns:
        HTML string for the badge
    """
    colors = DOMAIN_COLORS.get(domain.lower(), {"bg": "#e5e7eb", "text": "#374151", "icon": "📋"})

    font_size = {"small": "0.7rem", "normal": "0.75rem", "large": "0.85rem"}.get(size, "0.75rem")
    padding = {"small": "0.15rem 0.35rem", "normal": "0.25rem 0.5rem", "large": "0.3rem 0.6rem"}.get(size, "0.25rem 0.5rem")

    icon = colors["icon"] + " " if show_icon else ""
    label = domain.replace("_", " ").title()

    return f'''
    <span style="
        display: inline-block;
        padding: {padding};
        border-radius: 9999px;
        font-size: {font_size};
        font-weight: 600;
        background: {colors["bg"]};
        color: {colors["text"]};
    ">{icon}{label}</span>
    '''


def phase_badge(
    phase: str,
    show_icon: bool = True,
    size: str = "normal"
) -> str:
    """
    Render a phase badge.

    Args:
        phase: Phase name (Day_1, Day_100, Post_100)
        show_icon: Whether to show the icon
        size: Badge size (small, normal, large)

    Returns:
        HTML string for the badge
    """
    colors = PHASE_COLORS.get(phase, {"bg": "#e5e7eb", "text": "#374151", "icon": "📋", "label": phase})

    font_size = {"small": "0.7rem", "normal": "0.75rem", "large": "0.85rem"}.get(size, "0.75rem")
    padding = {"small": "0.15rem 0.35rem", "normal": "0.25rem 0.5rem", "large": "0.3rem 0.6rem"}.get(size, "0.25rem 0.5rem")

    icon = colors["icon"] + " " if show_icon else ""
    label = colors["label"]

    return f'''
    <span style="
        display: inline-block;
        padding: {padding};
        border-radius: 9999px;
        font-size: {font_size};
        font-weight: 600;
        background: {colors["bg"]};
        color: {colors["text"]};
    ">{icon}{label}</span>
    '''


def confidence_badge(
    confidence: str,
    size: str = "normal"
) -> str:
    """
    Render a confidence badge.

    Args:
        confidence: Confidence level (high, medium, low)
        size: Badge size (small, normal, large)

    Returns:
        HTML string for the badge
    """
    colors = CONFIDENCE_COLORS.get(confidence.lower(), CONFIDENCE_COLORS["medium"])

    font_size = {"small": "0.65rem", "normal": "0.7rem", "large": "0.8rem"}.get(size, "0.7rem")
    padding = {"small": "0.1rem 0.3rem", "normal": "0.15rem 0.4rem", "large": "0.2rem 0.5rem"}.get(size, "0.15rem 0.4rem")

    return f'''
    <span style="
        display: inline-block;
        padding: {padding};
        border-radius: 4px;
        font-size: {font_size};
        background: {colors["bg"]};
        color: {colors["text"]};
    ">Confidence: {confidence}</span>
    '''


def cost_badge(
    cost_estimate: str,
    size: str = "normal"
) -> str:
    """
    Render a cost badge.

    Args:
        cost_estimate: Cost estimate string (e.g., "under_25k", "$50K-$100K")
        size: Badge size (small, normal, large)

    Returns:
        HTML string for the badge
    """
    # Map cost ranges to colors
    cost_lower = cost_estimate.lower().replace(" ", "_")

    if "under" in cost_lower or "25k" in cost_lower:
        bg, text = "#dcfce7", "#166534"
    elif "100k" in cost_lower or "500k" in cost_lower:
        bg, text = "#fef3c7", "#a16207"
    elif "1m" in cost_lower or "over" in cost_lower:
        bg, text = "#fecaca", "#991b1b"
    else:
        bg, text = "#e5e7eb", "#374151"

    font_size = {"small": "0.65rem", "normal": "0.7rem", "large": "0.8rem"}.get(size, "0.7rem")
    padding = {"small": "0.1rem 0.3rem", "normal": "0.15rem 0.4rem", "large": "0.2rem 0.5rem"}.get(size, "0.15rem 0.4rem")

    # Format label
    label = cost_estimate.replace("_", " ").replace("k", "K").replace("m", "M")

    return f'''
    <span style="
        display: inline-block;
        padding: {padding};
        border-radius: 4px;
        font-size: {font_size};
        font-weight: 500;
        background: {bg};
        color: {text};
    ">💰 {label}</span>
    '''


def status_badge(
    status: str,
    size: str = "normal"
) -> str:
    """
    Render a status badge.

    Args:
        status: Status (documented, partial, gap, open, answered, deferred)
        size: Badge size (small, normal, large)

    Returns:
        HTML string for the badge
    """
    colors = STATUS_COLORS.get(status.lower(), {"bg": "#e5e7eb", "text": "#374151", "icon": "•"})

    font_size = {"small": "0.65rem", "normal": "0.7rem", "large": "0.8rem"}.get(size, "0.7rem")
    padding = {"small": "0.1rem 0.3rem", "normal": "0.15rem 0.4rem", "large": "0.2rem 0.5rem"}.get(size, "0.15rem 0.4rem")

    return f'''
    <span style="
        display: inline-block;
        padding: {padding};
        border-radius: 4px;
        font-size: {font_size};
        background: {colors["bg"]};
        color: {colors["text"]};
    ">{colors["icon"]} {status.title()}</span>
    '''


# =============================================================================
# STREAMLIT HELPERS
# =============================================================================

def render_severity_badge(severity: str, **kwargs):
    """Render severity badge in Streamlit."""
    st.markdown(severity_badge(severity, **kwargs), unsafe_allow_html=True)


def render_domain_badge(domain: str, **kwargs):
    """Render domain badge in Streamlit."""
    st.markdown(domain_badge(domain, **kwargs), unsafe_allow_html=True)


def render_phase_badge(phase: str, **kwargs):
    """Render phase badge in Streamlit."""
    st.markdown(phase_badge(phase, **kwargs), unsafe_allow_html=True)


def render_badges_row(badges: list):
    """Render multiple badges in a row."""
    html = '<div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">'
    html += "".join(badges)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
