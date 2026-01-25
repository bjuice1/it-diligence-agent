"""
Risks View

Displays and manages identified risks with filtering and details.

Steps 107-114 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional

from ..components.layout import page_header, section_header, empty_state
from ..components.cards import risk_card
from ..components.filters import filter_bar, pagination, reset_pagination
from ..components.badges import severity_badge, domain_badge, render_badges_row
from ..utils.formatting import format_count


def render_risks_view(
    reasoning_store: Any,
    fact_store: Optional[Any] = None,
    show_export: bool = True,
) -> None:
    """
    Render the risks view page.

    Args:
        reasoning_store: ReasoningStore with risks
        fact_store: Optional FactStore for evidence lookup
        show_export: Whether to show export options
    """
    page_header(
        title="Risk Analysis",
        subtitle="Identified risks and mitigation strategies",
        icon="⚠️",
    )

    # Check for data
    if reasoning_store is None or not reasoning_store.risks:
        empty_state(
            title="No Risks Identified",
            message="Run an analysis to identify risks",
            icon="⚠️",
        )
        return

    risks = reasoning_store.risks

    # Summary metrics
    _render_risk_summary(risks)

    st.divider()

    # Filters
    filters = filter_bar(
        key_prefix="risks",
        show_search=True,
        show_domain=True,
        show_severity=True,
        show_phase=False,
    )

    # Apply filters
    filtered_risks = _apply_filters(risks, filters)

    # Results count
    st.caption(f"Showing {len(filtered_risks)} of {len(risks)} risks")

    # Pagination
    if len(filtered_risks) > 10:
        start, end = pagination(
            total_items=len(filtered_risks),
            items_per_page=10,
            key="risks_pagination",
        )
        page_risks = filtered_risks[start:end]
    else:
        page_risks = filtered_risks

    # Render risks
    _render_risk_list(page_risks, fact_store)

    # Export options
    if show_export:
        st.divider()
        _render_export_options(filtered_risks)


def _render_risk_summary(risks: List[Any]) -> None:
    """Render risk summary metrics."""
    # Count by severity
    critical = len([r for r in risks if r.severity == "critical"])
    high = len([r for r in risks if r.severity == "high"])
    medium = len([r for r in risks if r.severity == "medium"])
    low = len([r for r in risks if r.severity == "low"])

    # Count integration-dependent
    integration = len([r for r in risks if getattr(r, "integration_dependent", False)])

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("🔴 Critical", critical)
    with col2:
        st.metric("🟠 High", high)
    with col3:
        st.metric("🟡 Medium", medium)
    with col4:
        st.metric("🟢 Low", low)
    with col5:
        st.metric("🔗 Integration", integration)


def _apply_filters(risks: List[Any], filters: dict) -> List[Any]:
    """Apply filters to risks list."""
    filtered = risks

    # Search filter
    search = filters.get("search", "").lower()
    if search:
        filtered = [
            r for r in filtered
            if search in r.title.lower() or search in r.description.lower()
        ]

    # Domain filter
    domain = filters.get("domain")
    if domain:
        filtered = [r for r in filtered if r.domain == domain]

    # Severity filter
    severity = filters.get("severity")
    if severity:
        filtered = [r for r in filtered if r.severity == severity]

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    filtered.sort(key=lambda r: severity_order.get(r.severity, 99))

    return filtered


def _render_risk_list(risks: List[Any], fact_store: Optional[Any]) -> None:
    """Render list of risks."""
    if not risks:
        st.info("No risks match the current filters")
        return

    # Group by severity for visual organization
    current_severity = None

    for risk in risks:
        if risk.severity != current_severity:
            current_severity = risk.severity
            severity_label = {
                "critical": "🔴 Critical Risks",
                "high": "🟠 High Risks",
                "medium": "🟡 Medium Risks",
                "low": "🟢 Low Risks",
            }.get(current_severity, current_severity)
            st.markdown(f"### {severity_label}")

        risk_card(risk, show_evidence=True)


def _render_export_options(risks: List[Any]) -> None:
    """Render export options."""
    section_header("Export", icon="📥", level=4)

    col1, col2, col3 = st.columns(3)

    with col1:
        # CSV export
        csv_data = _generate_csv(risks)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="risks.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        # JSON export
        import json
        json_data = json.dumps([_risk_to_dict(r) for r in risks], indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name="risks.json",
            mime="application/json",
            use_container_width=True,
        )

    with col3:
        st.button(
            "📥 Download Excel",
            disabled=True,
            use_container_width=True,
            help="Excel export coming soon",
        )


def _generate_csv(risks: List[Any]) -> str:
    """Generate CSV data from risks."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID", "Title", "Severity", "Domain", "Description",
        "Mitigation", "Confidence", "Integration Dependent", "Evidence"
    ])

    # Data rows
    for risk in risks:
        writer.writerow([
            getattr(risk, "risk_id", ""),
            risk.title,
            risk.severity,
            risk.domain,
            risk.description,
            risk.mitigation,
            risk.confidence,
            "Yes" if getattr(risk, "integration_dependent", False) else "No",
            ", ".join(getattr(risk, "based_on_facts", [])),
        ])

    return output.getvalue()


def _risk_to_dict(risk: Any) -> dict:
    """Convert risk to dictionary."""
    return {
        "id": getattr(risk, "risk_id", ""),
        "title": risk.title,
        "severity": risk.severity,
        "domain": risk.domain,
        "description": risk.description,
        "mitigation": risk.mitigation,
        "confidence": risk.confidence,
        "reasoning": getattr(risk, "reasoning", ""),
        "integration_dependent": getattr(risk, "integration_dependent", False),
        "based_on_facts": getattr(risk, "based_on_facts", []),
    }


def render_risks_tab(reasoning_store: Any) -> None:
    """
    Render risks as a tab within another view.

    Simplified version for embedding in tabs.
    """
    if not reasoning_store or not reasoning_store.risks:
        st.info("No risks identified")
        return

    risks = reasoning_store.risks
    st.write(f"**{len(risks)} risks identified**")

    for risk in sorted(risks, key=lambda r: ["critical", "high", "medium", "low"].index(r.severity) if r.severity in ["critical", "high", "medium", "low"] else 99):
        risk_card(risk, expanded=False, show_evidence=True)
