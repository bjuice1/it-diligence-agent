"""
Cost Analysis View

Detailed cost breakdown and analysis.

Steps 176-182 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional, Dict

from ..components.layout import page_header, section_header, empty_state
from ..components.charts import cost_breakdown_pie, phase_timeline, cost_range_chart
from ..utils.formatting import format_cost, format_cost_range


def render_costs_view(
    reasoning_store: Any,
    show_export: bool = True,
) -> None:
    """
    Render the cost analysis view page.

    Args:
        reasoning_store: ReasoningStore with work items containing costs
        show_export: Whether to show export options
    """
    page_header(
        title="Cost Analysis",
        subtitle="Integration and remediation cost estimates",
        icon="💰",
    )

    if not reasoning_store or not reasoning_store.work_items:
        empty_state(
            title="No Cost Data",
            message="Run an analysis to see cost estimates",
            icon="💰",
        )
        return

    # Extract cost data
    cost_data = _extract_cost_data(reasoning_store.work_items)

    # Summary
    _render_cost_summary(cost_data)

    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "📅 By Phase",
        "📁 By Domain",
        "👤 By Owner",
    ])

    with tab1:
        _render_overview_tab(cost_data)

    with tab2:
        _render_phase_tab(cost_data)

    with tab3:
        _render_domain_tab(cost_data)

    with tab4:
        _render_owner_tab(cost_data)

    # Export
    if show_export:
        st.divider()
        _render_export_section(cost_data, reasoning_store.work_items)


def _extract_cost_data(work_items: List[Any]) -> Dict[str, Any]:
    """Extract and aggregate cost data from work items."""
    data = {
        "total_low": 0,
        "total_high": 0,
        "by_phase": {},
        "by_domain": {},
        "by_owner": {},
        "items_with_cost": 0,
        "items_without_cost": 0,
    }

    for wi in work_items:
        cost_low = getattr(wi, "cost_low", 0) or 0
        cost_high = getattr(wi, "cost_high", 0) or 0
        phase = wi.phase or "Day_100"
        domain = wi.domain or "other"
        owner = getattr(wi, "owner_type", "buyer") or "buyer"

        # Track items with/without costs
        if cost_high > 0:
            data["items_with_cost"] += 1
        else:
            data["items_without_cost"] += 1

        # Totals
        data["total_low"] += cost_low
        data["total_high"] += cost_high

        # By phase
        if phase not in data["by_phase"]:
            data["by_phase"][phase] = {"low": 0, "high": 0, "count": 0, "items": []}
        data["by_phase"][phase]["low"] += cost_low
        data["by_phase"][phase]["high"] += cost_high
        data["by_phase"][phase]["count"] += 1
        data["by_phase"][phase]["items"].append(wi)

        # By domain
        if domain not in data["by_domain"]:
            data["by_domain"][domain] = {"low": 0, "high": 0, "count": 0, "items": []}
        data["by_domain"][domain]["low"] += cost_low
        data["by_domain"][domain]["high"] += cost_high
        data["by_domain"][domain]["count"] += 1
        data["by_domain"][domain]["items"].append(wi)

        # By owner
        if owner not in data["by_owner"]:
            data["by_owner"][owner] = {"low": 0, "high": 0, "count": 0, "items": []}
        data["by_owner"][owner]["low"] += cost_low
        data["by_owner"][owner]["high"] += cost_high
        data["by_owner"][owner]["count"] += 1
        data["by_owner"][owner]["items"].append(wi)

    return data


def _render_cost_summary(data: Dict) -> None:
    """Render cost summary metrics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #fef3c7; border-radius: 8px; border: 2px solid #f59e0b;">
            <div style="font-size: 1.5rem; font-weight: bold; color: #92400e;">
                {format_cost_range(data['total_low'], data['total_high'])}
            </div>
            <div style="font-size: 0.8rem; color: #78350f;">Total Estimated Cost</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        midpoint = (data["total_low"] + data["total_high"]) / 2
        st.metric("📊 Midpoint", format_cost(midpoint))

    with col3:
        st.metric("📋 Items with Cost", data["items_with_cost"])

    with col4:
        st.metric("❓ Items TBD", data["items_without_cost"])


def _render_overview_tab(data: Dict) -> None:
    """Render cost overview tab."""
    col1, col2 = st.columns(2)

    with col1:
        section_header("Cost by Phase", icon="📅", level=4)

        # Prepare data for pie chart
        phase_costs = {
            phase: (values["low"] + values["high"]) / 2
            for phase, values in data["by_phase"].items()
            if values["high"] > 0
        }

        if phase_costs:
            cost_breakdown_pie(
                costs=phase_costs,
                title="",
                group_by="phase",
                height=300,
            )
        else:
            st.info("No cost data available")

    with col2:
        section_header("Cost by Owner", icon="👤", level=4)

        owner_costs = {
            owner: (values["low"] + values["high"]) / 2
            for owner, values in data["by_owner"].items()
            if values["high"] > 0
        }

        if owner_costs:
            cost_breakdown_pie(
                costs=owner_costs,
                title="",
                group_by="domain",
                height=300,
            )
        else:
            st.info("No cost data available")

    # Summary table
    st.divider()
    section_header("Cost Summary Table", icon="📊", level=4)

    # Create summary DataFrame
    summary_data = []

    for phase in ["Day_1", "Day_100", "Post_100"]:
        if phase in data["by_phase"]:
            p = data["by_phase"][phase]
            summary_data.append({
                "Phase": {"Day_1": "Day 1", "Day_100": "Day 100", "Post_100": "Post-100"}[phase],
                "Items": p["count"],
                "Low Estimate": format_cost(p["low"]),
                "High Estimate": format_cost(p["high"]),
                "Midpoint": format_cost((p["low"] + p["high"]) / 2),
            })

    if summary_data:
        st.table(summary_data)


def _render_phase_tab(data: Dict) -> None:
    """Render cost by phase tab."""
    section_header("Cost Breakdown by Phase", icon="📅", level=4)

    phases = ["Day_1", "Day_100", "Post_100"]
    phase_labels = {"Day_1": "🚨 Day 1", "Day_100": "📅 Day 100", "Post_100": "🎯 Post-100"}

    for phase in phases:
        if phase not in data["by_phase"]:
            continue

        phase_data = data["by_phase"][phase]
        label = phase_labels.get(phase, phase)

        with st.expander(f"{label} - {format_cost_range(phase_data['low'], phase_data['high'])} ({phase_data['count']} items)"):
            # Group by priority
            items = phase_data["items"]
            by_priority = {}

            for item in items:
                priority = item.priority or "medium"
                if priority not in by_priority:
                    by_priority[priority] = []
                by_priority[priority].append(item)

            for priority in ["critical", "high", "medium", "low"]:
                if priority not in by_priority:
                    continue

                priority_items = by_priority[priority]
                priority_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}[priority]

                st.markdown(f"**{priority_icon} {priority.title()}** ({len(priority_items)})")

                for item in priority_items:
                    cost = getattr(item, "cost_estimate", "TBD")
                    st.markdown(f"- {item.title} - `{cost}`")


def _render_domain_tab(data: Dict) -> None:
    """Render cost by domain tab."""
    section_header("Cost Breakdown by Domain", icon="📁", level=4)

    # Sort by cost descending
    sorted_domains = sorted(
        data["by_domain"].items(),
        key=lambda x: x[1]["high"],
        reverse=True
    )

    for domain, domain_data in sorted_domains:
        label = domain.replace("_", " ").title()
        range_str = format_cost_range(domain_data["low"], domain_data["high"])

        with st.expander(f"📁 {label} - {range_str} ({domain_data['count']} items)"):
            for item in domain_data["items"]:
                cost = getattr(item, "cost_estimate", "TBD")
                phase_icon = {"Day_1": "🚨", "Day_100": "📅", "Post_100": "🎯"}.get(item.phase, "")
                st.markdown(f"- {phase_icon} {item.title} - `{cost}`")


def _render_owner_tab(data: Dict) -> None:
    """Render cost by owner tab."""
    section_header("Cost Breakdown by Owner", icon="👤", level=4)

    owner_labels = {
        "buyer": "🏢 Buyer",
        "seller": "🏪 Seller",
        "joint": "🤝 Joint",
        "target": "🎯 Target",
    }

    for owner, owner_data in sorted(data["by_owner"].items()):
        label = owner_labels.get(owner, owner.title())
        range_str = format_cost_range(owner_data["low"], owner_data["high"])

        with st.expander(f"{label} - {range_str} ({owner_data['count']} items)"):
            # Group by phase
            by_phase = {}
            for item in owner_data["items"]:
                phase = item.phase or "Day_100"
                if phase not in by_phase:
                    by_phase[phase] = []
                by_phase[phase].append(item)

            for phase in ["Day_1", "Day_100", "Post_100"]:
                if phase not in by_phase:
                    continue

                phase_label = {"Day_1": "Day 1", "Day_100": "Day 100", "Post_100": "Post-100"}[phase]
                st.markdown(f"**{phase_label}**")

                for item in by_phase[phase]:
                    cost = getattr(item, "cost_estimate", "TBD")
                    st.markdown(f"- {item.title} - `{cost}`")


def _render_export_section(data: Dict, work_items: List[Any]) -> None:
    """Render export options."""
    section_header("Export", icon="📥", level=4)

    col1, col2, col3 = st.columns(3)

    with col1:
        csv_data = _generate_cost_csv(work_items)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="cost_analysis.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        summary_md = _generate_cost_summary_md(data)
        st.download_button(
            label="📥 Download Summary",
            data=summary_md,
            file_name="cost_summary.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col3:
        st.button(
            "📥 Download Excel",
            disabled=True,
            use_container_width=True,
            help="Excel export coming soon",
        )


def _generate_cost_csv(work_items: List[Any]) -> str:
    """Generate CSV data for cost analysis."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Title", "Phase", "Domain", "Owner", "Priority",
        "Cost Estimate", "Cost Low", "Cost High"
    ])

    # Data
    for wi in work_items:
        writer.writerow([
            wi.title,
            wi.phase,
            wi.domain,
            getattr(wi, "owner_type", ""),
            wi.priority,
            getattr(wi, "cost_estimate", ""),
            getattr(wi, "cost_low", 0),
            getattr(wi, "cost_high", 0),
        ])

    return output.getvalue()


def _generate_cost_summary_md(data: Dict) -> str:
    """Generate markdown summary of costs."""
    lines = [
        "# Cost Analysis Summary",
        "",
        f"**Total Estimated Cost:** {format_cost_range(data['total_low'], data['total_high'])}",
        "",
        "## By Phase",
        "",
    ]

    for phase in ["Day_1", "Day_100", "Post_100"]:
        if phase in data["by_phase"]:
            p = data["by_phase"][phase]
            label = {"Day_1": "Day 1", "Day_100": "Day 100", "Post_100": "Post-100"}[phase]
            lines.append(f"- **{label}:** {format_cost_range(p['low'], p['high'])} ({p['count']} items)")

    lines.extend([
        "",
        "## By Owner",
        "",
    ])

    for owner, o in data["by_owner"].items():
        lines.append(f"- **{owner.title()}:** {format_cost_range(o['low'], o['high'])} ({o['count']} items)")

    return "\n".join(lines)
