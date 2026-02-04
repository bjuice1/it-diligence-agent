"""
PE Report Renderers

Render structured data (dataclasses) to HTML.
Separates data from presentation.
"""

from tools_v2.renderers.html_renderer import (
    DomainReportRenderer,
    render_domain_report,
)
from tools_v2.renderers.dashboard_renderer import (
    DashboardRenderer,
    render_dashboard,
)

__all__ = [
    "DomainReportRenderer",
    "render_domain_report",
    "DashboardRenderer",
    "render_dashboard",
]
