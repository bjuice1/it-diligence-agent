"""
Staffing View

IT staffing analysis and visualization.

Steps 132-141 of the alignment plan.

UPDATED: Now uses organization_bridge to get StaffMember data with
individual names, compensation, and hierarchy information.
"""

import streamlit as st
from typing import Any, Optional, Dict, Tuple
import sys
from pathlib import Path

# Add project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ...components.layout import page_header, section_header, empty_state

# Import organization bridge and models
from services.organization_bridge import build_organization_from_facts
from models.organization_stores import OrganizationDataStore
from models.organization_models import RoleCategory, EmploymentType


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

    # Get staffing data via organization bridge
    store, status = _get_staffing_data(fact_store)

    if not store or not store.staff_members:
        empty_state(
            title="No Staffing Data",
            message="Run an analysis with organization domain to see staffing details",
            icon="👥",
        )
        return

    # Render sections using StaffMember data
    _render_staffing_summary(store)

    st.divider()

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Roles & Headcount",
        "📊 Benchmarks",
        "🏢 MSP Analysis",
        "📋 Recommendations",
    ])

    with tab1:
        _render_roles_tab(store)

    with tab2:
        _render_benchmarks_tab(store)

    with tab3:
        _render_msp_tab(store)

    with tab4:
        _render_recommendations_tab(store, reasoning_store)


def _get_staffing_data(fact_store: Any, entity: str = "target") -> Tuple[Optional[OrganizationDataStore], str]:
    """
    Get staffing data from organization bridge.

    This calls build_organization_from_facts to get StaffMember objects
    with individual names, compensation, and hierarchy data.

    Args:
        fact_store: FactStore containing organization facts
        entity: "target" or "buyer" (default: "target")

    Returns:
        Tuple of (OrganizationDataStore, status_string)
    """
    if not fact_store or not hasattr(fact_store, 'facts') or not fact_store.facts:
        return None, "no_facts"

    try:
        # P1 FIX #6: Pass entity explicitly to prevent silent misattribution
        return build_organization_from_facts(
            fact_store,
            entity=entity,
            deal_id=getattr(fact_store, 'deal_id', '')
        )
    except Exception as e:
        st.error(f"Error loading staffing data: {e}")
        return None, f"error: {str(e)}"


def _render_staffing_summary(store: OrganizationDataStore) -> None:
    """Render staffing summary metrics from OrganizationDataStore."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        headcount = store.get_target_headcount() if hasattr(store, 'get_target_headcount') else len(store.staff_members)
        st.metric("👥 Total Headcount", headcount)

    with col2:
        st.metric("💼 FTE", store.total_internal_fte)

    with col3:
        st.metric("🏢 MSP Relationships", len(store.msp_relationships) if store.msp_relationships else 0)

    with col4:
        st.metric("📋 Contractors", store.total_contractor)

    # Show total compensation if available
    if store.total_compensation and store.total_compensation > 0:
        st.metric("💰 Total IT Compensation", f"${store.total_compensation:,.0f}")

    # Key person alert
    key_persons = store.get_key_persons() if hasattr(store, 'get_key_persons') else [s for s in store.staff_members if s.is_key_person]
    if key_persons:
        st.warning(f"⭐ {len(key_persons)} Key Person(s) identified - review for retention risk")


def _render_roles_tab(store: OrganizationDataStore) -> None:
    """Render roles and headcount tab using StaffMember objects."""
    section_header("IT Staff by Category", icon="👤", level=4)

    if not store.staff_members:
        st.info("No staff members identified in the documentation")
        return

    # Group by employment type
    fte_staff = [s for s in store.staff_members if s.employment_type == EmploymentType.FTE]
    contractor_staff = [s for s in store.staff_members if s.employment_type == EmploymentType.CONTRACTOR]
    msp_staff = [s for s in store.staff_members if s.employment_type == EmploymentType.MSP]
    other_staff = [s for s in store.staff_members if s.employment_type not in [EmploymentType.FTE, EmploymentType.CONTRACTOR, EmploymentType.MSP]]

    # Display FTE
    if fte_staff:
        st.markdown(f"### Full-Time Employees ({len(fte_staff)})")
        _render_staff_table(fte_staff)

    # Display Contractors
    if contractor_staff:
        st.markdown(f"### Contractors ({len(contractor_staff)})")
        _render_staff_table(contractor_staff)

    # Display MSP Staff
    if msp_staff:
        st.markdown(f"### MSP Staff ({len(msp_staff)})")
        _render_staff_table(msp_staff)

    # Display Other
    if other_staff:
        st.markdown(f"### Other ({len(other_staff)})")
        _render_staff_table(other_staff)

    # Category breakdown
    st.divider()
    section_header("By Role Category", icon="📊", level=4)

    for category in RoleCategory:
        staff_in_cat = store.get_staff_by_category(category) if hasattr(store, 'get_staff_by_category') else [s for s in store.staff_members if s.role_category == category]
        if staff_in_cat:
            with st.expander(f"{_get_category_icon(category)} {category.display_name if hasattr(category, 'display_name') else category.value} ({len(staff_in_cat)})"):
                _render_staff_table(staff_in_cat)


def _render_staff_table(staff_list) -> None:
    """Render a table of staff members with names, roles, and compensation."""
    import pandas as pd

    rows = []
    for staff in staff_list:
        comp_str = f"${staff.base_compensation:,.0f}" if staff.base_compensation else "-"
        key_badge = "⭐" if staff.is_key_person else ""

        rows.append({
            "Name": staff.name or "-",
            "Role": staff.role_title or "-",
            "Category": staff.role_category.display_name if hasattr(staff.role_category, 'display_name') else str(staff.role_category.value),
            "Compensation": comp_str,
            "Key": key_badge,
            "Location": staff.location or "-",
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Role": st.column_config.TextColumn("Role", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Compensation": st.column_config.TextColumn("Compensation", width="small"),
                "Key": st.column_config.TextColumn("Key", width="small"),
                "Location": st.column_config.TextColumn("Location", width="small"),
            }
        )


def _render_benchmarks_tab(store: OrganizationDataStore) -> None:
    """Render benchmarks comparison tab."""
    section_header("Staffing Benchmarks", icon="📊", level=4)

    # Show actual data from store
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Common IT Ratios")
        st.markdown("""
        - **IT Staff : Total Employees** - Typical 1:50 to 1:100
        - **Developers : Ops** - Varies by company type
        - **Security Staff %** - Growing trend toward 5-10%
        """)

    with col2:
        st.markdown("### Observed Staffing")
        headcount = store.get_target_headcount() if hasattr(store, 'get_target_headcount') else len(store.staff_members)
        st.markdown(f"- Total IT Headcount: **{headcount}**")
        st.markdown(f"- FTE: **{store.total_internal_fte}**")
        st.markdown(f"- Contractors: **{store.total_contractor}**")

        if store.total_compensation:
            avg_comp = store.total_compensation / headcount if headcount > 0 else 0
            st.markdown(f"- Total Compensation: **${store.total_compensation:,.0f}**")
            st.markdown(f"- Avg per Person: **${avg_comp:,.0f}**")

    # Category breakdown
    st.divider()
    st.markdown("### Headcount by Category")

    category_data = []
    for category in RoleCategory:
        staff_in_cat = store.get_staff_by_category(category) if hasattr(store, 'get_staff_by_category') else [s for s in store.staff_members if s.role_category == category]
        if staff_in_cat:
            cat_comp = sum(s.base_compensation or 0 for s in staff_in_cat)
            category_data.append({
                "Category": category.display_name if hasattr(category, 'display_name') else category.value,
                "Headcount": len(staff_in_cat),
                "Total Comp": f"${cat_comp:,.0f}" if cat_comp else "-",
            })

    if category_data:
        import pandas as pd
        df = pd.DataFrame(category_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Benchmark comparison if available
    if store.benchmark_comparison:
        st.divider()
        st.markdown("### Benchmark Comparison")
        comp = store.benchmark_comparison
        st.markdown(f"**Profile:** {comp.benchmark_profile_name}")
        st.markdown(f"**Status:** {comp.overall_status}")

        if comp.key_findings:
            st.markdown("**Key Findings:**")
            for finding in comp.key_findings:
                st.markdown(f"- {finding}")


def _render_msp_tab(store: OrganizationDataStore) -> None:
    """Render MSP analysis tab from MSPRelationship objects."""
    section_header("MSP Relationships", icon="🏢", level=4)

    if not store.msp_relationships:
        st.info("No MSP relationships identified in documentation")
        return

    st.markdown(f"**{len(store.msp_relationships)} MSP relationship(s) identified:**")

    total_msp_fte = 0
    for msp in store.msp_relationships:
        with st.expander(f"🏢 {msp.vendor_name}"):
            st.markdown(f"**FTE Equivalent:** {msp.total_fte_equivalent}")
            total_msp_fte += msp.total_fte_equivalent or 0

            if hasattr(msp, 'dependency_level') and msp.dependency_level:
                dep_name = msp.dependency_level.display_name if hasattr(msp.dependency_level, 'display_name') else str(msp.dependency_level)
                st.markdown(f"**Dependency Level:** {dep_name}")

            if hasattr(msp, 'risk_level') and msp.risk_level:
                st.markdown(f"**Risk Level:** {msp.risk_level}")

            if hasattr(msp, 'contract_expiry') and msp.contract_expiry:
                st.markdown(f"**Contract Expiry:** {msp.contract_expiry}")

            if hasattr(msp, 'services') and msp.services:
                st.markdown("**Services:**")
                for svc in msp.services:
                    svc_name = svc.service_name if hasattr(svc, 'service_name') else str(svc)
                    st.markdown(f"- {svc_name}")

    if total_msp_fte > 0:
        st.metric("Total MSP FTE Equivalent", f"{total_msp_fte:.1f}")

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


def _render_recommendations_tab(store: OrganizationDataStore, reasoning_store: Any) -> None:
    """Render recommendations tab."""
    section_header("Staffing Recommendations", icon="💡", level=4)

    # Key persons alert
    key_persons = store.get_key_persons() if hasattr(store, 'get_key_persons') else [s for s in store.staff_members if s.is_key_person]
    if key_persons:
        st.warning(f"**⭐ {len(key_persons)} Key Person(s) Identified**")
        for kp in key_persons:
            reason = kp.key_person_reason or "Critical role"
            st.markdown(f"- **{kp.name}** ({kp.role_title}): {reason}")

    # Extract org-related recommendations
    if reasoning_store and hasattr(reasoning_store, 'recommendations') and reasoning_store.recommendations:
        org_recs = [
            r for r in reasoning_store.recommendations
            if r.domain == "organization"
        ]

        if org_recs:
            st.divider()
            section_header("Analysis Recommendations", icon="💡", level=4)
            for rec in org_recs:
                icon = {"immediate": "🔴", "pre-close": "🟠", "post-close": "🟢"}.get(rec.urgency, "📋")
                with st.expander(f"{icon} {rec.title}"):
                    st.write(rec.description)
                    if hasattr(rec, 'rationale') and rec.rationale:
                        st.markdown(f"**Rationale:** {rec.rationale}")

    # Work items
    if reasoning_store and hasattr(reasoning_store, 'work_items') and reasoning_store.work_items:
        org_items = [
            w for w in reasoning_store.work_items
            if w.domain == "organization"
        ]

        if org_items:
            st.divider()
            section_header("Related Work Items", icon="📋", level=4)
            for wi in org_items[:5]:
                phase_icon = {"Day_1": "🚨", "Day_100": "📅", "Post_100": "🎯"}.get(wi.phase, "📋")
                st.markdown(f"- {phase_icon} **{wi.title}** ({wi.phase})")

            if len(org_items) > 5:
                st.caption(f"+ {len(org_items) - 5} more work items")


def _get_category_icon(category: RoleCategory) -> str:
    """Get emoji icon for category."""
    icons = {
        RoleCategory.LEADERSHIP: "👔",
        RoleCategory.INFRASTRUCTURE: "🖥️",
        RoleCategory.APPLICATIONS: "💻",
        RoleCategory.SECURITY: "🔒",
        RoleCategory.SERVICE_DESK: "🎧",
        RoleCategory.DATA: "📊",
        RoleCategory.PROJECT_MANAGEMENT: "📋",
        RoleCategory.OTHER: "👤",
    }
    return icons.get(category, "👤")
