"""
Staffing View

IT staffing analysis and visualization.

Steps 132-141 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional, Dict

from ...components.layout import page_header, section_header, empty_state
from ...components.charts import domain_breakdown_bar
from ...utils.formatting import format_count


def render_staffing_view(
    fact_store: Any,
    reasoning_store: Optional[Any] = None,
) -> None:
    """
    Render the staffing analysis view.

    Args:
        fact_store: FactStore with organization facts
        reasoning_store: Optional ReasoningStore for analysis
    """
    page_header(
        title="IT Staffing Analysis",
        subtitle="Organization structure and staffing assessment",
        icon="👥",
    )

    # Extract staffing data from facts
    staffing_data = _extract_staffing_data(fact_store)

    if not staffing_data["roles"]:
        empty_state(
            title="No Staffing Data",
            message="Run an analysis with organization domain to see staffing details",
            icon="👥",
        )
        return

    # Render sections
    _render_staffing_summary(staffing_data)

    st.divider()

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Roles & Headcount",
        "📊 Benchmarks",
        "🏢 MSP Analysis",
        "📋 Recommendations",
    ])

    with tab1:
        _render_roles_tab(staffing_data)

    with tab2:
        _render_benchmarks_tab(staffing_data)

    with tab3:
        _render_msp_tab(staffing_data, fact_store)

    with tab4:
        _render_recommendations_tab(staffing_data, reasoning_store)


def _extract_staffing_data(fact_store: Any) -> Dict[str, Any]:
    """Extract staffing-related data from fact store."""
    data = {
        "roles": [],
        "total_headcount": 0,
        "msp_relationships": [],
        "vendors": [],
        "budget": None,
        "structure": None,
    }

    if not fact_store or not fact_store.facts:
        return data

    # Filter organization facts
    org_facts = [f for f in fact_store.facts if f.domain == "organization"]

    for fact in org_facts:
        category = fact.category

        if category == "staffing":
            role_info = {
                "title": fact.item,
                "count": fact.details.get("count", 1),
                "type": fact.details.get("type", "fte"),
                "level": fact.details.get("level", ""),
                "fact_id": fact.fact_id,
            }
            data["roles"].append(role_info)
            data["total_headcount"] += role_info["count"] if isinstance(role_info["count"], int) else 1

        elif category == "vendors":
            vendor_info = {
                "name": fact.item,
                "service": fact.details.get("service_type", ""),
                "relationship": fact.details.get("relationship_type", "vendor"),
                "fact_id": fact.fact_id,
            }
            if "msp" in str(vendor_info).lower() or "managed" in str(vendor_info).lower():
                data["msp_relationships"].append(vendor_info)
            else:
                data["vendors"].append(vendor_info)

        elif category == "budget":
            data["budget"] = {
                "amount": fact.details.get("amount", ""),
                "period": fact.details.get("period", "annual"),
                "fact_id": fact.fact_id,
            }

        elif category == "structure":
            data["structure"] = {
                "description": fact.item,
                "details": fact.details,
                "fact_id": fact.fact_id,
            }

    return data


def _render_staffing_summary(data: Dict[str, Any]) -> None:
    """Render staffing summary metrics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👥 Total Headcount", data["total_headcount"])

    with col2:
        fte_count = len([r for r in data["roles"] if r.get("type") == "fte"])
        st.metric("💼 FTE Roles", fte_count)

    with col3:
        st.metric("🏢 MSP Relationships", len(data["msp_relationships"]))

    with col4:
        st.metric("🤝 Vendors", len(data["vendors"]))


def _render_roles_tab(data: Dict[str, Any]) -> None:
    """Render roles and headcount tab."""
    section_header("IT Roles", icon="👤", level=4)

    if not data["roles"]:
        st.info("No specific roles identified in the documentation")
        return

    # Group by type
    by_type = {}
    for role in data["roles"]:
        role_type = role.get("type", "fte")
        if role_type not in by_type:
            by_type[role_type] = []
        by_type[role_type].append(role)

    # Display by type
    for role_type, roles in by_type.items():
        type_label = {
            "fte": "Full-Time Employees",
            "contractor": "Contractors",
            "consultant": "Consultants",
            "msp": "MSP Staff",
        }.get(role_type, role_type.title())

        st.markdown(f"### {type_label} ({len(roles)})")

        for role in roles:
            count = role.get("count", 1)
            count_str = f" x{count}" if count > 1 else ""
            level = role.get("level", "")
            level_str = f" ({level})" if level else ""

            st.markdown(f"- **{role['title']}**{count_str}{level_str}")


def _render_benchmarks_tab(data: Dict[str, Any]) -> None:
    """Render benchmarks comparison tab."""
    section_header("Staffing Benchmarks", icon="📊", level=4)

    st.info("Benchmark comparison requires industry data and company size context")

    # Placeholder for benchmark metrics
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Common IT Ratios")
        st.markdown("""
        - **IT Staff : Total Employees** - Typical 1:50 to 1:100
        - **Developers : Ops** - Varies by company type
        - **Security Staff %** - Growing trend toward 5-10%
        """)

    with col2:
        st.markdown("### Observed")
        if data["total_headcount"] > 0:
            st.markdown(f"- Total IT Staff: **{data['total_headcount']}**")
            st.markdown(f"- Unique Roles: **{len(data['roles'])}**")
        else:
            st.markdown("- *Insufficient data for benchmarks*")


def _render_msp_tab(data: Dict[str, Any], fact_store: Any) -> None:
    """Render MSP analysis tab."""
    section_header("MSP Relationships", icon="🏢", level=4)

    if not data["msp_relationships"]:
        st.info("No MSP relationships identified in documentation")
        return

    st.markdown(f"**{len(data['msp_relationships'])} MSP relationship(s) identified:**")

    for msp in data["msp_relationships"]:
        with st.expander(f"🏢 {msp['name']}"):
            st.markdown(f"**Service:** {msp.get('service', 'Not specified')}")
            st.markdown(f"**Relationship:** {msp.get('relationship', 'Vendor')}")
            st.caption(f"Source: {msp.get('fact_id', '')}")

    # TSA considerations
    st.divider()
    section_header("TSA Considerations", icon="📋", level=4)

    st.markdown("""
    **Potential Transition Service Agreement needs:**
    - MSP contract assignments or novation
    - Knowledge transfer from MSP staff
    - Service level continuity
    - Exit planning and transition timeline
    """)


def _render_recommendations_tab(data: Dict[str, Any], reasoning_store: Any) -> None:
    """Render recommendations tab."""
    section_header("Staffing Recommendations", icon="💡", level=4)

    # Extract org-related recommendations
    if reasoning_store and reasoning_store.recommendations:
        org_recs = [
            r for r in reasoning_store.recommendations
            if r.domain == "organization"
        ]

        if org_recs:
            for rec in org_recs:
                icon = {"immediate": "🔴", "pre-close": "🟠", "post-close": "🟢"}.get(rec.urgency, "📋")
                with st.expander(f"{icon} {rec.title}"):
                    st.write(rec.description)
                    st.markdown(f"**Rationale:** {rec.rationale}")
        else:
            st.info("No organization-specific recommendations")
    else:
        st.info("Run analysis with reasoning phase to get recommendations")

    # Work items
    st.divider()
    section_header("Related Work Items", icon="📋", level=4)

    if reasoning_store and reasoning_store.work_items:
        org_items = [
            w for w in reasoning_store.work_items
            if w.domain == "organization"
        ]

        if org_items:
            for wi in org_items[:5]:
                phase_icon = {"Day_1": "🚨", "Day_100": "📅", "Post_100": "🎯"}.get(wi.phase, "📋")
                st.markdown(f"- {phase_icon} **{wi.title}** ({wi.phase})")

            if len(org_items) > 5:
                st.caption(f"+ {len(org_items) - 5} more work items")
        else:
            st.info("No organization work items identified")
    else:
        st.info("Run analysis to identify work items")
