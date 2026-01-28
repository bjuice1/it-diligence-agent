"""
Applications View

Application inventory and analysis.

Steps 146-152 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional, Dict

from ..components.layout import page_header, section_header, empty_state
from ..components.badges import severity_badge, domain_badge
from ..components.charts import domain_breakdown_bar, cost_breakdown_pie
from ..components.filters import filter_bar, pagination


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

    # Extract application data
    app_data = _extract_application_data(fact_store)

    if not app_data["applications"]:
        empty_state(
            title="No Application Data",
            message="Run an analysis with applications domain to see details",
            icon="📱",
        )
        return

    # Summary
    _render_apps_summary(app_data)

    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📱 Inventory",
        "🔗 Integrations",
        "⚠️ Risks",
        "📊 Analysis",
    ])

    with tab1:
        _render_inventory_tab(app_data)

    with tab2:
        _render_integrations_tab(app_data)

    with tab3:
        _render_risks_tab(app_data, reasoning_store)

    with tab4:
        _render_analysis_tab(app_data, reasoning_store)


def _extract_application_data(fact_store: Any) -> Dict[str, Any]:
    """Extract application-related data from fact store."""
    data = {
        "applications": [],
        "integrations": [],
        "databases": [],
        "by_category": {},
        "by_hosting": {"saas": 0, "on_prem": 0, "cloud": 0, "hybrid": 0},
        # Data quality tracking
        "quality": {
            "total": 0,
            "high_confidence": 0,
            "needs_review": 0,
            "low_confidence": 0,
        },
    }

    if not fact_store or not fact_store.facts:
        return data

    # Filter applications facts
    app_facts = [f for f in fact_store.facts if f.domain == "applications"]

    for fact in app_facts:
        category = fact.category or "other"

        # Get confidence and review status
        confidence = getattr(fact, 'confidence_score', 0.0)
        needs_review = getattr(fact, 'needs_review', False)
        needs_review_reason = getattr(fact, 'needs_review_reason', '')

        app_info = {
            "name": fact.item,
            "category": category,
            "vendor": fact.details.get("vendor", ""),
            "version": fact.details.get("version", ""),
            "hosting": fact.details.get("hosting_type", ""),
            "users": fact.details.get("user_count", ""),
            "criticality": fact.details.get("criticality", "medium"),
            "status": fact.status,
            "fact_id": fact.fact_id,
            "details": fact.details,
            # Data quality fields
            "confidence": confidence,
            "needs_review": needs_review,
            "needs_review_reason": needs_review_reason,
        }

        # Track data quality
        data["quality"]["total"] += 1
        if needs_review:
            data["quality"]["needs_review"] += 1
        elif confidence >= 0.6:
            data["quality"]["high_confidence"] += 1
        else:
            data["quality"]["low_confidence"] += 1

        # Categorize
        if category == "integration":
            data["integrations"].append(app_info)
        elif category == "database":
            data["databases"].append(app_info)
        else:
            data["applications"].append(app_info)

        # Track by category
        if category not in data["by_category"]:
            data["by_category"][category] = []
        data["by_category"][category].append(app_info)

        # Track hosting type
        hosting = app_info["hosting"].lower() if app_info["hosting"] else ""
        if "saas" in hosting or "cloud" in hosting:
            data["by_hosting"]["saas"] += 1
        elif "on-prem" in hosting or "on_prem" in hosting:
            data["by_hosting"]["on_prem"] += 1
        elif "hybrid" in hosting:
            data["by_hosting"]["hybrid"] += 1

    return data


def _render_apps_summary(data: Dict[str, Any]) -> None:
    """Render applications summary metrics."""
    total_apps = len(data["applications"])
    total_integrations = len(data["integrations"])
    total_databases = len(data["databases"])

    # Count critical
    critical = len([a for a in data["applications"] if a["criticality"] == "critical"])

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📱 Applications", total_apps)

    with col2:
        st.metric("🔗 Integrations", total_integrations)

    with col3:
        st.metric("🗄️ Databases", total_databases)

    with col4:
        st.metric("🔴 Critical", critical)

    with col5:
        st.metric("📁 Categories", len(data["by_category"]))

    # Data Quality Summary
    quality = data.get("quality", {})
    if quality.get("total", 0) > 0:
        needs_review = quality.get("needs_review", 0)
        high_conf = quality.get("high_confidence", 0)
        low_conf = quality.get("low_confidence", 0)

        if needs_review > 0 or low_conf > 0:
            st.divider()
            st.markdown("##### Data Quality")
            qcol1, qcol2, qcol3 = st.columns(3)

            with qcol1:
                st.metric("✅ Validated", high_conf, help="High confidence entries")

            with qcol2:
                if needs_review > 0:
                    st.metric("⚠️ Needs Review", needs_review, help="Entries flagged for human review")
                else:
                    st.metric("⚠️ Needs Review", 0)

            with qcol3:
                if low_conf > 0:
                    st.metric("❓ Low Confidence", low_conf, help="Sparse details - may need verification")
                else:
                    st.metric("❓ Low Confidence", 0)


def _render_inventory_tab(data: Dict[str, Any]) -> None:
    """Render application inventory tab."""
    section_header("Application Inventory", icon="📋", level=4)

    # Filter controls
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        categories = ["All"] + list(data["by_category"].keys())
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
        # Data quality filter
        quality_filter = st.selectbox(
            "Quality",
            ["All", "Needs Review", "High Confidence", "Low Confidence"],
            key="apps_quality_filter",
        )

    # Filter applications
    apps = data["applications"]

    if selected_cat != "All":
        apps = [a for a in apps if a["category"] == selected_cat]

    if search:
        search_lower = search.lower()
        apps = [a for a in apps if search_lower in a["name"].lower() or search_lower in a.get("vendor", "").lower()]

    # Quality filter
    if quality_filter == "Needs Review":
        apps = [a for a in apps if a.get("needs_review", False)]
    elif quality_filter == "High Confidence":
        apps = [a for a in apps if a.get("confidence", 0) >= 0.6 and not a.get("needs_review", False)]
    elif quality_filter == "Low Confidence":
        apps = [a for a in apps if a.get("confidence", 0) < 0.6 and not a.get("needs_review", False)]

    # Results
    quality_note = f" ({quality_filter})" if quality_filter != "All" else ""
    st.caption(f"Showing {len(apps)} application(s){quality_note}")

    # Render by category
    if selected_cat == "All":
        for category in sorted(data["by_category"].keys()):
            cat_apps = [a for a in apps if a["category"] == category]
            if cat_apps:
                _render_category_apps(category, cat_apps)
    else:
        _render_category_apps(selected_cat, apps)


def _render_category_apps(category: str, apps: List[Dict]) -> None:
    """Render applications in a category."""
    category_icons = {
        "erp": "🏢",
        "crm": "👥",
        "custom": "🛠️",
        "saas": "☁️",
        "database": "🗄️",
        "development": "💻",
    }

    icon = category_icons.get(category, "📱")
    label = category.replace("_", " ").title()

    # Count apps needing review in this category
    needs_review_count = len([a for a in apps if a.get("needs_review", False)])
    review_indicator = f" ⚠️{needs_review_count}" if needs_review_count > 0 else ""

    with st.expander(f"{icon} {label} ({len(apps)}){review_indicator}", expanded=len(apps) <= 5):
        for app in apps:
            criticality_icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }.get(app["criticality"], "⚪")

            hosting_badge = ""
            if app["hosting"]:
                hosting_badge = f" `{app['hosting']}`"

            # Review/confidence indicator
            review_badge = ""
            if app.get("needs_review", False):
                review_badge = " ⚠️"
            elif app.get("confidence", 0) >= 0.6:
                review_badge = " ✓"

            st.markdown(f"{criticality_icon} **{app['name']}**{hosting_badge}{review_badge}")

            details = []
            if app["vendor"]:
                details.append(f"Vendor: {app['vendor']}")
            if app["version"]:
                details.append(f"v{app['version']}")
            if app["users"]:
                details.append(f"{app['users']} users")

            # Show confidence score
            confidence = app.get("confidence", 0)
            if confidence > 0:
                conf_pct = int(confidence * 100)
                details.append(f"Confidence: {conf_pct}%")

            if details:
                st.caption(" | ".join(details))

            # Show review reason if flagged
            if app.get("needs_review", False) and app.get("needs_review_reason"):
                st.warning(f"Review needed: {app['needs_review_reason']}", icon="⚠️")


def _render_integrations_tab(data: Dict[str, Any]) -> None:
    """Render integrations tab."""
    section_header("Application Integrations", icon="🔗", level=4)

    integrations = data["integrations"]

    if not integrations:
        st.info("No integration data identified")
        return

    st.markdown(f"**{len(integrations)} integration(s) documented:**")

    for integration in integrations:
        with st.expander(f"🔗 {integration['name']}"):
            if integration["details"]:
                for key, value in integration["details"].items():
                    if value and value != "not_stated":
                        st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")

            st.caption(f"Source: {integration['fact_id']}")

    # Integration map placeholder
    st.divider()
    st.markdown("### Integration Map")
    st.info("Visual integration map coming in future update")


def _render_risks_tab(data: Dict[str, Any], reasoning_store: Any) -> None:
    """Render application risks tab."""
    section_header("Application Risks", icon="⚠️", level=4)

    if not reasoning_store or not reasoning_store.risks:
        st.info("Run analysis to identify application risks")
        return

    # Filter to applications domain
    app_risks = [r for r in reasoning_store.risks if r.domain == "applications"]

    if not app_risks:
        st.success("No application-specific risks identified")
        return

    st.markdown(f"**{len(app_risks)} application risk(s):**")

    for risk in sorted(app_risks, key=lambda r: ["critical", "high", "medium", "low"].index(r.severity) if r.severity in ["critical", "high", "medium", "low"] else 99):
        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(risk.severity, "⚪")

        with st.expander(f"{severity_icon} {risk.title} ({risk.severity.upper()})"):
            st.write(risk.description)

            if hasattr(risk, "mitigation") and risk.mitigation:
                st.markdown("**Mitigation:**")
                st.write(risk.mitigation)

            st.caption(f"Evidence: {', '.join(getattr(risk, 'based_on_facts', []))}")


def _render_analysis_tab(data: Dict[str, Any], reasoning_store: Any) -> None:
    """Render analysis/insights tab."""
    section_header("Application Analysis", icon="📊", level=4)

    col1, col2 = st.columns(2)

    with col1:
        # Hosting breakdown
        st.markdown("### Hosting Distribution")
        hosting = data["by_hosting"]
        total = sum(hosting.values())

        if total > 0:
            for host_type, count in hosting.items():
                if count > 0:
                    pct = count / total * 100
                    st.markdown(f"- **{host_type.replace('_', '-').title()}**: {count} ({pct:.0f}%)")
        else:
            st.caption("No hosting data available")

    with col2:
        # Category breakdown
        st.markdown("### By Category")
        for category, apps in sorted(data["by_category"].items()):
            st.markdown(f"- **{category.replace('_', ' ').title()}**: {len(apps)}")

    # Work items
    st.divider()
    st.markdown("### Related Work Items")

    if reasoning_store and reasoning_store.work_items:
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
