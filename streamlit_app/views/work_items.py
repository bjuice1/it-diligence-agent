"""
Work Items View

Displays and manages work items by phase with filtering.

Steps 115-122 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional, Dict

from ..components.layout import page_header, section_header, empty_state
from ..components.cards import work_item_card
from ..components.filters import filter_bar, pagination, phase_filter
from ..components.charts import phase_timeline, cost_range_chart
from ..utils.formatting import format_cost, format_cost_range


def render_work_items_view(
    reasoning_store: Any,
    fact_store: Optional[Any] = None,
    show_export: bool = True,
) -> None:
    """
    Render the work items view page.

    Args:
        reasoning_store: ReasoningStore with work items
        fact_store: Optional FactStore for evidence lookup
        show_export: Whether to show export options
    """
    page_header(
        title="Work Items",
        subtitle="Integration and remediation tasks by phase",
        icon="📋",
    )

    # Check for data
    if reasoning_store is None or not reasoning_store.work_items:
        empty_state(
            title="No Work Items Identified",
            message="Run an analysis to identify work items",
            icon="📋",
        )
        return

    work_items = reasoning_store.work_items

    # Summary metrics and cost overview
    _render_work_items_summary(work_items)

    st.divider()

    # Phase tabs
    tab_day1, tab_day100, tab_post100, tab_all = st.tabs([
        "🚨 Day 1",
        "📅 Day 100",
        "🎯 Post-100",
        "📊 All Items",
    ])

    with tab_day1:
        _render_phase_tab(work_items, "Day_1", fact_store)

    with tab_day100:
        _render_phase_tab(work_items, "Day_100", fact_store)

    with tab_post100:
        _render_phase_tab(work_items, "Post_100", fact_store)

    with tab_all:
        _render_all_items_tab(work_items, fact_store, show_export)


def _render_work_items_summary(work_items: List[Any]) -> None:
    """Render work items summary metrics."""
    # Count by phase
    day1 = [w for w in work_items if w.phase == "Day_1"]
    day100 = [w for w in work_items if w.phase == "Day_100"]
    post100 = [w for w in work_items if w.phase == "Post_100"]

    # Calculate costs
    total_low = sum(getattr(w, "cost_low", 0) or 0 for w in work_items)
    total_high = sum(getattr(w, "cost_high", 0) or 0 for w in work_items)

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("🚨 Day 1", len(day1))
    with col2:
        st.metric("📅 Day 100", len(day100))
    with col3:
        st.metric("🎯 Post-100", len(post100))
    with col4:
        st.metric("📊 Total", len(work_items))
    with col5:
        st.metric("💰 Est. Cost", format_cost_range(total_low, total_high))


def _render_phase_tab(
    work_items: List[Any],
    phase: str,
    fact_store: Optional[Any],
) -> None:
    """Render work items for a specific phase."""
    phase_items = [w for w in work_items if w.phase == phase]

    if not phase_items:
        phase_label = {"Day_1": "Day 1", "Day_100": "Day 100", "Post_100": "Post-100"}[phase]
        st.info(f"No {phase_label} work items identified")
        return

    # Phase cost summary
    phase_low = sum(getattr(w, "cost_low", 0) or 0 for w in phase_items)
    phase_high = sum(getattr(w, "cost_high", 0) or 0 for w in phase_items)

    st.markdown(f"**{len(phase_items)} items** | Est. Cost: {format_cost_range(phase_low, phase_high)}")

    # Filter by domain and priority
    col1, col2 = st.columns(2)

    with col1:
        domain_filter = st.selectbox(
            "Filter by Domain",
            ["All"] + list(set(w.domain for w in phase_items)),
            key=f"wi_{phase}_domain",
        )

    with col2:
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All", "critical", "high", "medium", "low"],
            key=f"wi_{phase}_priority",
        )

    # Apply filters
    filtered = phase_items

    if domain_filter != "All":
        filtered = [w for w in filtered if w.domain == domain_filter]

    if priority_filter != "All":
        filtered = [w for w in filtered if w.priority == priority_filter]

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    filtered.sort(key=lambda w: priority_order.get(w.priority, 99))

    # Render items
    for wi in filtered:
        work_item_card(wi, expanded=False, show_evidence=True)


def _render_all_items_tab(
    work_items: List[Any],
    fact_store: Optional[Any],
    show_export: bool,
) -> None:
    """Render all work items with full filtering."""
    # Cost visualization
    section_header("Cost Overview", icon="💰", level=4)

    col1, col2 = st.columns(2)

    with col1:
        phase_timeline(
            items_by_phase={
                "Day_1": len([w for w in work_items if w.phase == "Day_1"]),
                "Day_100": len([w for w in work_items if w.phase == "Day_100"]),
                "Post_100": len([w for w in work_items if w.phase == "Post_100"]),
            },
            title="Items by Phase",
            height=280,
        )

    with col2:
        # Cost by owner
        owner_costs = {}
        for wi in work_items:
            owner = getattr(wi, "owner_type", "buyer")
            cost = (getattr(wi, "cost_low", 0) or 0) + (getattr(wi, "cost_high", 0) or 0)
            owner_costs[owner] = owner_costs.get(owner, 0) + cost / 2  # Average

        from ..components.charts import cost_breakdown_pie
        cost_breakdown_pie(
            costs=owner_costs,
            title="Cost by Owner",
            group_by="domain",
            height=280,
        )

    st.divider()

    # Full filter bar
    filters = filter_bar(
        key_prefix="wi_all",
        show_search=True,
        show_domain=True,
        show_severity=True,
        show_phase=True,
    )

    # Apply filters
    filtered = work_items

    search = filters.get("search", "").lower()
    if search:
        filtered = [
            w for w in filtered
            if search in w.title.lower() or search in w.description.lower()
        ]

    domain = filters.get("domain")
    if domain:
        filtered = [w for w in filtered if w.domain == domain]

    severity = filters.get("severity")
    if severity:
        filtered = [w for w in filtered if w.priority == severity]

    phase = filters.get("phase")
    if phase:
        filtered = [w for w in filtered if w.phase == phase]

    # Results
    st.caption(f"Showing {len(filtered)} of {len(work_items)} work items")

    # Pagination
    if len(filtered) > 10:
        start, end = pagination(
            total_items=len(filtered),
            items_per_page=10,
            key="wi_all_pagination",
        )
        page_items = filtered[start:end]
    else:
        page_items = filtered

    # Render items
    for wi in page_items:
        work_item_card(wi, expanded=False, show_evidence=True)

    # Export options
    if show_export:
        st.divider()
        _render_export_options(filtered)


def _render_export_options(work_items: List[Any]) -> None:
    """Render export options."""
    section_header("Export", icon="📥", level=4)

    col1, col2 = st.columns(2)

    with col1:
        csv_data = _generate_csv(work_items)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="work_items.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        import json
        json_data = json.dumps([_work_item_to_dict(w) for w in work_items], indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name="work_items.json",
            mime="application/json",
            use_container_width=True,
        )


def _generate_csv(work_items: List[Any]) -> str:
    """Generate CSV data from work items."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID", "Title", "Phase", "Priority", "Domain", "Description",
        "Owner", "Cost Estimate", "Confidence", "Evidence"
    ])

    # Data rows
    for wi in work_items:
        writer.writerow([
            getattr(wi, "work_item_id", ""),
            wi.title,
            wi.phase,
            wi.priority,
            wi.domain,
            wi.description,
            getattr(wi, "owner_type", ""),
            getattr(wi, "cost_estimate", ""),
            wi.confidence,
            ", ".join(getattr(wi, "based_on_facts", [])),
        ])

    return output.getvalue()


def _work_item_to_dict(wi: Any) -> dict:
    """Convert work item to dictionary."""
    return {
        "id": getattr(wi, "work_item_id", ""),
        "title": wi.title,
        "phase": wi.phase,
        "priority": wi.priority,
        "domain": wi.domain,
        "description": wi.description,
        "owner_type": getattr(wi, "owner_type", ""),
        "cost_estimate": getattr(wi, "cost_estimate", ""),
        "cost_low": getattr(wi, "cost_low", 0),
        "cost_high": getattr(wi, "cost_high", 0),
        "confidence": wi.confidence,
        "reasoning": getattr(wi, "reasoning", ""),
        "based_on_facts": getattr(wi, "based_on_facts", []),
        "triggered_by": getattr(wi, "triggered_by", []),
    }
