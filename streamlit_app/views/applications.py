"""
Applications View

Application inventory and analysis.

Steps 146-152 of the alignment plan.

UPDATED: Now uses applications_bridge to get ApplicationItem data with
proper names, vendors, costs, and structured category information.
"""

import streamlit as st
from typing import Any, List, Optional, Dict, Tuple
import sys
from pathlib import Path

# Add project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ..components.layout import page_header, section_header, empty_state
from ..components.badges import severity_badge, domain_badge
from ..components.charts import domain_breakdown_bar, cost_breakdown_pie
from ..components.filters import filter_bar, pagination

# Import applications bridge and models
from services.applications_bridge import (
    build_applications_inventory,
    ApplicationsInventory,
    ApplicationItem,
    AppCategory,
    DeploymentType,
    Criticality,
    CategorySummary,
)


def render_applications_view(
    fact_store: Any,
    reasoning_store: Optional[Any] = None,
    show_export: bool = True,
) -> None:
    """
    Render the applications view page.

    Args:
        fact_store: FactStore with application facts
        reasoning_store: Optional ReasoningStore for analysis
        show_export: Whether to show export options
    """
    page_header(
        title="Applications Analysis",
        subtitle="Application inventory, integrations, and risks",
        icon="📱",
    )

    # Get applications data via bridge
    inventory, status = _get_applications_inventory(fact_store)

    if not inventory or not inventory.applications:
        empty_state(
            title="No Application Data",
            message="Run an analysis with applications domain to see details",
            icon="📱",
        )
        return

    # Summary
    _render_apps_summary(inventory)

    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📱 Inventory",
        "🔗 Integrations",
        "⚠️ Risks",
        "📊 Analysis",
    ])

    with tab1:
        _render_inventory_tab(inventory)

    with tab2:
        _render_integrations_tab(inventory)

    with tab3:
        _render_risks_tab(inventory, reasoning_store)

    with tab4:
        _render_analysis_tab(inventory, reasoning_store)


def _get_applications_inventory(fact_store: Any) -> Tuple[Optional[ApplicationsInventory], str]:
    """
    Get ApplicationsInventory from fact_store via applications bridge.

    Returns:
        Tuple of (ApplicationsInventory, status_string)
    """
    if not fact_store or not hasattr(fact_store, 'facts') or not fact_store.facts:
        return None, "no_facts"

    try:
        return build_applications_inventory(fact_store)
    except Exception as e:
        st.error(f"Error loading applications data: {e}")
        return None, f"error: {str(e)}"


def _render_apps_summary(inventory: ApplicationsInventory) -> None:
    """Render applications summary metrics from ApplicationsInventory."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📱 Applications", inventory.total_count)

    with col2:
        # Count integrations
        integration_count = len([a for a in inventory.applications
                                if a.category == AppCategory.INTEGRATION])
        st.metric("🔗 Integrations", integration_count)

    with col3:
        # Count databases
        database_count = len([a for a in inventory.applications
                             if a.category == AppCategory.DATABASE])
        st.metric("🗄️ Databases", database_count)

    with col4:
        st.metric("🔴 Critical", inventory.critical_count)

    with col5:
        st.metric("📁 Categories", len(inventory.by_category))

    # Cost summary if available
    if inventory.total_cost > 0:
        st.divider()
        cost_col1, cost_col2, cost_col3 = st.columns(3)

        with cost_col1:
            st.metric("💰 Total Annual Cost", f"${inventory.total_cost:,.0f}")

        with cost_col2:
            st.metric("☁️ SaaS Apps", inventory.saas_count)

        with cost_col3:
            st.metric("🏢 On-Prem Apps", inventory.on_prem_count)

    # User count if available
    if inventory.total_users > 0:
        st.metric("👥 Total Users", f"{inventory.total_users:,}")

    # Data Quality Summary - count verified vs needs review
    verified_count = len([a for a in inventory.applications if a.verified])
    low_conf_count = len([a for a in inventory.applications
                         if a.confidence_score < 0.6 and not a.verified])

    if verified_count > 0 or low_conf_count > 0:
        st.divider()
        st.markdown("##### Data Quality")
        qcol1, qcol2, qcol3 = st.columns(3)

        with qcol1:
            st.metric("✅ Verified", verified_count, help="High confidence entries")

        with qcol2:
            high_conf = len([a for a in inventory.applications
                            if a.confidence_score >= 0.6 and not a.verified])
            st.metric("📊 High Confidence", high_conf)

        with qcol3:
            st.metric("❓ Low Confidence", low_conf_count,
                     help="May need verification")


def _render_inventory_tab(inventory: ApplicationsInventory) -> None:
    """Render application inventory tab using ApplicationItem objects."""
    section_header("Application Inventory", icon="📋", level=4)

    # Filter controls
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        categories = ["All"] + [cat.display_name for cat in AppCategory
                               if cat.value in inventory.by_category]
        selected_cat = st.selectbox(
            "Category",
            categories,
            key="apps_cat_filter",
        )

    with col2:
        search = st.text_input(
            "Search",
            placeholder="Search applications...",
            key="apps_search",
        )

    with col3:
        criticality_filter = st.selectbox(
            "Criticality",
            ["All", "Critical", "High", "Medium", "Low"],
            key="apps_crit_filter",
        )

    # Filter applications
    apps = inventory.applications.copy()

    if selected_cat != "All":
        # Find the category enum
        cat_enum = next((c for c in AppCategory if c.display_name == selected_cat), None)
        if cat_enum:
            apps = [a for a in apps if a.category == cat_enum]

    if search:
        search_lower = search.lower()
        apps = [a for a in apps if search_lower in a.name.lower()
                or search_lower in a.vendor.lower()]

    if criticality_filter != "All":
        crit_enum = Criticality(criticality_filter.lower())
        apps = [a for a in apps if a.criticality == crit_enum]

    # Results
    st.caption(f"Showing {len(apps)} application(s)")

    # Render applications table
    if apps:
        _render_apps_table(apps)

    # Also render by category
    st.divider()
    section_header("By Category", icon="📂", level=4)

    for cat_value, summary in inventory.by_category.items():
        cat_apps = [a for a in apps if a.category.value == cat_value]
        if cat_apps:
            _render_category_section(summary.category, cat_apps)


def _render_apps_table(apps: List[ApplicationItem]) -> None:
    """Render a table of applications with all details."""
    import pandas as pd

    rows = []
    for app in apps:
        cost_str = f"${app.annual_cost:,.0f}" if app.annual_cost else "-"
        users_str = f"{app.user_count:,}" if app.user_count else "-"
        verified_badge = "✅" if app.verified else ""
        crit_icon = {
            Criticality.CRITICAL: "🔴",
            Criticality.HIGH: "🟠",
            Criticality.MEDIUM: "🟡",
            Criticality.LOW: "🟢",
        }.get(app.criticality, "⚪")

        rows.append({
            "App ID": app.id[:12] + "..." if len(app.id) > 12 else app.id,
            "Name": app.name,
            "Vendor": app.vendor or "-",
            "Version": app.version or "-",
            "Category": app.category.display_name,
            "Deployment": app.deployment.value.replace("_", " ").title(),
            "Criticality": f"{crit_icon} {app.criticality.value.title()}",
            "Users": users_str,
            "Annual Cost": cost_str,
            "Verified": verified_badge,
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "App ID": st.column_config.TextColumn("ID", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Vendor": st.column_config.TextColumn("Vendor", width="medium"),
                "Version": st.column_config.TextColumn("Version", width="small"),
                "Category": st.column_config.TextColumn("Category", width="medium"),
                "Deployment": st.column_config.TextColumn("Deployment", width="small"),
                "Criticality": st.column_config.TextColumn("Criticality", width="small"),
                "Users": st.column_config.TextColumn("Users", width="small"),
                "Annual Cost": st.column_config.TextColumn("Annual Cost", width="small"),
                "Verified": st.column_config.TextColumn("✓", width="small"),
            }
        )


def _render_category_section(category: AppCategory, apps: List[ApplicationItem]) -> None:
    """Render applications in a category with full details."""
    icon = category.icon
    label = category.display_name

    # Calculate category totals
    total_cost = sum(a.annual_cost for a in apps)
    critical_count = len([a for a in apps if a.criticality == Criticality.CRITICAL])

    cost_str = f" | ${total_cost:,.0f}" if total_cost > 0 else ""
    crit_str = f" | 🔴 {critical_count}" if critical_count > 0 else ""

    with st.expander(f"{icon} {label} ({len(apps)}){cost_str}{crit_str}", expanded=len(apps) <= 5):
        for app in apps:
            criticality_icon = {
                Criticality.CRITICAL: "🔴",
                Criticality.HIGH: "🟠",
                Criticality.MEDIUM: "🟡",
                Criticality.LOW: "🟢",
            }.get(app.criticality, "⚪")

            deployment_badge = ""
            if app.deployment != DeploymentType.UNKNOWN:
                deployment_badge = f" `{app.deployment.value.replace('_', '-')}`"

            verified_badge = " ✅" if app.verified else ""

            st.markdown(f"{criticality_icon} **{app.name}**{deployment_badge}{verified_badge}")

            details = []
            if app.vendor:
                details.append(f"Vendor: {app.vendor}")
            if app.version:
                details.append(f"v{app.version}")
            if app.user_count:
                details.append(f"{app.user_count:,} users")
            if app.annual_cost:
                details.append(f"${app.annual_cost:,.0f}/yr")
            if app.confidence_score > 0:
                conf_pct = int(app.confidence_score * 100)
                details.append(f"Confidence: {conf_pct}%")

            if details:
                st.caption(" | ".join(details))

            # Show evidence if available
            if app.evidence:
                with st.container():
                    st.caption(f"📄 Source: {app.source_document or 'Document'}")


def _render_integrations_tab(inventory: ApplicationsInventory) -> None:
    """Render integrations tab from ApplicationItem objects."""
    section_header("Application Integrations", icon="🔗", level=4)

    # Get integration-category apps
    integrations = [a for a in inventory.applications
                   if a.category == AppCategory.INTEGRATION]

    if not integrations:
        st.info("No integration applications identified")
        # Show apps with integrations listed
        apps_with_integrations = [a for a in inventory.applications if a.integrations]
        if apps_with_integrations:
            st.markdown(f"**{len(apps_with_integrations)} apps have integration data:**")
            for app in apps_with_integrations:
                with st.expander(f"🔗 {app.name} - {len(app.integrations)} integration(s)"):
                    for integ in app.integrations:
                        st.markdown(f"- {integ}")
        return

    st.markdown(f"**{len(integrations)} integration/middleware application(s):**")

    for app in integrations:
        with st.expander(f"🔗 {app.name} ({app.vendor or 'Unknown vendor'})"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Vendor:** {app.vendor or '-'}")
                st.markdown(f"**Version:** {app.version or '-'}")
                st.markdown(f"**Deployment:** {app.deployment.value.replace('_', ' ').title()}")

            with col2:
                if app.annual_cost:
                    st.markdown(f"**Annual Cost:** ${app.annual_cost:,.0f}")
                if app.user_count:
                    st.markdown(f"**Users:** {app.user_count:,}")
                st.markdown(f"**Criticality:** {app.criticality.value.title()}")

            if app.integrations:
                st.markdown("**Connected Systems:**")
                for integ in app.integrations:
                    st.markdown(f"- {integ}")

            st.caption(f"Source: {app.fact_id}")

    # Integration map placeholder
    st.divider()
    st.markdown("### Integration Map")
    st.info("Visual integration map coming in future update")


def _render_risks_tab(inventory: ApplicationsInventory, reasoning_store: Any) -> None:
    """Render application risks tab."""
    section_header("Application Risks", icon="⚠️", level=4)

    # Show critical applications
    critical_apps = [a for a in inventory.applications
                    if a.criticality == Criticality.CRITICAL]

    if critical_apps:
        st.warning(f"**🔴 {len(critical_apps)} Critical Application(s)**")
        for app in critical_apps:
            with st.expander(f"🔴 {app.name}"):
                st.markdown(f"**Vendor:** {app.vendor or 'Unknown'}")
                st.markdown(f"**Deployment:** {app.deployment.value.replace('_', ' ').title()}")
                if app.annual_cost:
                    st.markdown(f"**Annual Cost:** ${app.annual_cost:,.0f}")
                if app.user_count:
                    st.markdown(f"**Users:** {app.user_count:,}")
                st.markdown("**Risk Considerations:**")
                st.markdown("- Business-critical dependency")
                st.markdown("- Requires continuity planning")
                st.markdown("- Consider for Day 1 readiness")

    # Show apps needing review (low confidence)
    low_conf_apps = [a for a in inventory.applications
                    if a.confidence_score < 0.6 and not a.verified]

    if low_conf_apps:
        st.divider()
        st.info(f"**❓ {len(low_conf_apps)} Application(s) Need Verification**")
        for app in low_conf_apps[:10]:
            conf_pct = int(app.confidence_score * 100)
            st.markdown(f"- {app.name} ({conf_pct}% confidence)")
        if len(low_conf_apps) > 10:
            st.caption(f"+ {len(low_conf_apps) - 10} more")

    # Reasoning store risks
    if not reasoning_store or not hasattr(reasoning_store, 'risks') or not reasoning_store.risks:
        if not critical_apps and not low_conf_apps:
            st.info("Run analysis to identify application risks")
        return

    # Filter to applications domain
    app_risks = [r for r in reasoning_store.risks if r.domain == "applications"]

    if not app_risks:
        if not critical_apps and not low_conf_apps:
            st.success("No application-specific risks identified")
        return

    st.divider()
    st.markdown(f"**{len(app_risks)} application risk(s) from analysis:**")

    for risk in sorted(app_risks, key=lambda r: ["critical", "high", "medium", "low"].index(r.severity) if r.severity in ["critical", "high", "medium", "low"] else 99):
        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(risk.severity, "⚪")

        with st.expander(f"{severity_icon} {risk.title} ({risk.severity.upper()})"):
            st.write(risk.description)

            if hasattr(risk, "mitigation") and risk.mitigation:
                st.markdown("**Mitigation:**")
                st.write(risk.mitigation)

            st.caption(f"Evidence: {', '.join(getattr(risk, 'based_on_facts', []))}")


def _render_analysis_tab(inventory: ApplicationsInventory, reasoning_store: Any) -> None:
    """Render analysis/insights tab."""
    section_header("Application Analysis", icon="📊", level=4)

    col1, col2 = st.columns(2)

    with col1:
        # Deployment breakdown
        st.markdown("### Deployment Distribution")

        deployment_counts = {
            "SaaS/Cloud": inventory.saas_count,
            "On-Premises": inventory.on_prem_count,
            "Hybrid": len([a for a in inventory.applications
                          if a.deployment == DeploymentType.HYBRID]),
            "Unknown": len([a for a in inventory.applications
                           if a.deployment == DeploymentType.UNKNOWN]),
        }

        total = sum(deployment_counts.values())
        if total > 0:
            for deploy_type, count in deployment_counts.items():
                if count > 0:
                    pct = count / total * 100
                    st.markdown(f"- **{deploy_type}**: {count} ({pct:.0f}%)")
        else:
            st.caption("No deployment data available")

    with col2:
        # Category breakdown with costs
        st.markdown("### By Category")
        for cat_value, summary in sorted(inventory.by_category.items()):
            cost_str = f" | ${summary.total_cost:,.0f}" if summary.total_cost else ""
            st.markdown(f"- **{summary.category.display_name}**: {summary.total_count}{cost_str}")

    # Cost analysis
    if inventory.total_cost > 0:
        st.divider()
        st.markdown("### Cost Analysis")

        cost_col1, cost_col2 = st.columns(2)

        with cost_col1:
            st.metric("Total Annual IT Application Cost", f"${inventory.total_cost:,.0f}")
            avg_cost = inventory.total_cost / inventory.total_count if inventory.total_count > 0 else 0
            st.metric("Average Cost per Application", f"${avg_cost:,.0f}")

        with cost_col2:
            # Top 5 most expensive apps
            st.markdown("**Top 5 by Cost:**")
            sorted_apps = sorted(inventory.applications,
                               key=lambda a: a.annual_cost or 0, reverse=True)[:5]
            for app in sorted_apps:
                if app.annual_cost:
                    st.markdown(f"- {app.name}: ${app.annual_cost:,.0f}")

    # Work items
    st.divider()
    st.markdown("### Related Work Items")

    if reasoning_store and hasattr(reasoning_store, 'work_items') and reasoning_store.work_items:
        app_items = [w for w in reasoning_store.work_items if w.domain == "applications"]

        if app_items:
            for wi in app_items[:5]:
                phase_icon = {"Day_1": "🚨", "Day_100": "📅", "Post_100": "🎯"}.get(wi.phase, "📋")
                st.markdown(f"- {phase_icon} **{wi.title}** ({wi.phase})")

            if len(app_items) > 5:
                st.caption(f"+ {len(app_items) - 5} more")
        else:
            st.info("No application work items identified")
    else:
        st.info("Run analysis to see work items")
