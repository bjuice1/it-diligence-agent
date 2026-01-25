"""
Views Module

Page-level views for the Streamlit app.
"""

from .dashboard import render_dashboard, render_dashboard_summary
from .risks import render_risks_view, render_risks_tab
from .work_items import render_work_items_view
from .facts import render_facts_view
from .gaps import render_gaps_view
from .upload import render_upload_view, render_upload_widget
from .applications import render_applications_view
from .infrastructure import render_infrastructure_view
from .open_questions import render_open_questions_view
from .coverage import render_coverage_view
from .costs import render_costs_view
from .narrative import render_narrative_view

# Organization submodule
from .organization import (
    render_staffing_view,
    render_org_chart,
    render_vendors_view,
)

__all__ = [
    # Main views
    "render_dashboard",
    "render_dashboard_summary",
    "render_risks_view",
    "render_risks_tab",
    "render_work_items_view",
    "render_facts_view",
    "render_gaps_view",
    "render_upload_view",
    "render_upload_widget",

    # Domain-specific views
    "render_applications_view",
    "render_infrastructure_view",

    # Advanced views
    "render_open_questions_view",
    "render_coverage_view",
    "render_costs_view",
    "render_narrative_view",

    # Organization views
    "render_staffing_view",
    "render_org_chart",
    "render_vendors_view",
]
