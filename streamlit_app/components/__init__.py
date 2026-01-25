"""
Components Module

Reusable UI components for the Streamlit app.
"""

from .badges import (
    severity_badge,
    domain_badge,
    phase_badge,
    confidence_badge,
    cost_badge,
    status_badge,
)

from .cards import (
    metric_card,
    risk_card,
    work_item_card,
    fact_card,
    gap_card,
    collapsible_card,
    coverage_score_card,
)

from .filters import (
    filter_bar,
    search_box,
    domain_filter,
    severity_filter,
    phase_filter,
    pagination,
)

from .charts import (
    coverage_radar,
    severity_distribution,
    phase_timeline,
    cost_breakdown_pie,
    domain_breakdown_bar,
    cost_range_chart,
)

from .styles import inject_styles, get_main_css, COLORS, SPACING, RADIUS, SHADOWS

from .layout import (
    page_header,
    section_header,
    metric_row,
    card_grid,
    tab_container,
)

__all__ = [
    # Badges
    "severity_badge",
    "domain_badge",
    "phase_badge",
    "confidence_badge",
    "cost_badge",
    "status_badge",
    # Cards
    "metric_card",
    "risk_card",
    "work_item_card",
    "fact_card",
    "gap_card",
    "collapsible_card",
    "coverage_score_card",
    # Filters
    "filter_bar",
    "search_box",
    "domain_filter",
    "severity_filter",
    "phase_filter",
    "pagination",
    # Charts
    "coverage_radar",
    "severity_distribution",
    "phase_timeline",
    "cost_breakdown_pie",
    "domain_breakdown_bar",
    "cost_range_chart",
    # Layout
    "page_header",
    "section_header",
    "metric_row",
    "card_grid",
    "tab_container",
    # Styles
    "inject_styles",
    "get_main_css",
    "COLORS",
    "SPACING",
    "RADIUS",
    "SHADOWS",
]
