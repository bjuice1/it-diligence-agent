"""
Gaps View

Displays identified information gaps.

Part of Steps 123-130 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional

from ..components.layout import page_header, section_header, empty_state
from ..components.cards import gap_card
from ..components.filters import filter_bar, pagination
from ..utils.formatting import format_count


def render_gaps_view(
    fact_store: Any,
    show_export: bool = True,
) -> None:
    """
    Render the gaps view page.

    Args:
        fact_store: FactStore with gaps
        show_export: Whether to show export options
    """
    page_header(
        title="Information Gaps",
        subtitle="Missing documentation requiring follow-up",
        icon="🔍",
    )

    # Check for data
    if fact_store is None or not fact_store.gaps:
        empty_state(
            title="No Gaps Identified",
            message="All required information has been documented",
            icon="✅",
        )
        return

    gaps = fact_store.gaps

    # Summary
    _render_gaps_summary(gaps)

    st.divider()

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        importance = st.selectbox(
            "Importance",
            ["All", "critical", "high", "medium", "low"],
            key="gaps_importance",
        )

    with col2:
        domain = st.selectbox(
            "Domain",
            ["All"] + list(set(g.domain for g in gaps)),
            key="gaps_domain",
            format_func=lambda x: x.replace("_", " ").title() if x != "All" else "All Domains",
        )

    with col3:
        search = st.text_input(
            "Search",
            placeholder="Search gaps...",
            key="gaps_search",
        )

    # Apply filters
    filtered = gaps

    if importance != "All":
        filtered = [g for g in filtered if getattr(g, "importance", "medium") == importance]

    if domain != "All":
        filtered = [g for g in filtered if g.domain == domain]

    if search:
        search_lower = search.lower()
        filtered = [g for g in filtered if search_lower in g.description.lower()]

    # Sort by importance
    importance_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    filtered.sort(key=lambda g: importance_order.get(getattr(g, "importance", "medium"), 99))

    # Results
    st.caption(f"Showing {len(filtered)} of {len(gaps)} gaps")

    # Render gaps by importance
    _render_gaps_list(filtered)

    # Export
    if show_export:
        st.divider()
        _render_export_options(filtered)


def _render_gaps_summary(gaps: List[Any]) -> None:
    """Render gaps summary metrics."""
    # Count by importance
    critical = len([g for g in gaps if getattr(g, "importance", "medium") == "critical"])
    high = len([g for g in gaps if getattr(g, "importance", "medium") == "high"])
    medium = len([g for g in gaps if getattr(g, "importance", "medium") == "medium"])
    low = len([g for g in gaps if getattr(g, "importance", "medium") == "low"])

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📊 Total Gaps", len(gaps))
    with col2:
        st.metric("🔴 Critical", critical)
    with col3:
        st.metric("🟠 High", high)
    with col4:
        st.metric("🟡 Medium", medium)
    with col5:
        st.metric("🟢 Low", low)


def _render_gaps_list(gaps: List[Any]) -> None:
    """Render list of gaps."""
    if not gaps:
        st.info("No gaps match the current filters")
        return

    current_importance = None

    for gap in gaps:
        importance = getattr(gap, "importance", "medium")

        if importance != current_importance:
            current_importance = importance
            importance_label = {
                "critical": "🔴 Critical Gaps",
                "high": "🟠 High Priority Gaps",
                "medium": "🟡 Medium Priority Gaps",
                "low": "🟢 Low Priority Gaps",
            }.get(current_importance, current_importance)
            st.markdown(f"### {importance_label}")

        gap_card(gap, expanded=False)


def _render_export_options(gaps: List[Any]) -> None:
    """Render export options."""
    section_header("Export", icon="📥", level=4)

    col1, col2 = st.columns(2)

    with col1:
        csv_data = _generate_csv(gaps)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="gaps.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        import json
        json_data = json.dumps([_gap_to_dict(g) for g in gaps], indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name="gaps.json",
            mime="application/json",
            use_container_width=True,
        )


def _generate_csv(gaps: List[Any]) -> str:
    """Generate CSV data from gaps."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["ID", "Description", "Domain", "Category", "Importance"])

    # Data rows
    for gap in gaps:
        writer.writerow([
            gap.gap_id,
            gap.description,
            gap.domain,
            gap.category,
            getattr(gap, "importance", "medium"),
        ])

    return output.getvalue()


def _gap_to_dict(gap: Any) -> dict:
    """Convert gap to dictionary."""
    return {
        "gap_id": gap.gap_id,
        "description": gap.description,
        "domain": gap.domain,
        "category": gap.category,
        "importance": getattr(gap, "importance", "medium"),
    }
