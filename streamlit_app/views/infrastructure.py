"""
Infrastructure View

Infrastructure inventory and analysis.

Steps 153-160 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional, Dict

from ..components.layout import page_header, section_header, empty_state
from ..components.badges import severity_badge
from ..components.charts import domain_breakdown_bar
from ..components.filters import filter_bar, pagination


def render_infrastructure_view(
    fact_store: Any,
    reasoning_store: Optional[Any] = None,
    show_export: bool = True,
) -> None:
    """
    Render the infrastructure view page.

    Args:
        fact_store: FactStore with infrastructure facts
        reasoning_store: Optional ReasoningStore for analysis
        show_export: Whether to show export options
    """
    page_header(
        title="Infrastructure Analysis",
        subtitle="Compute, storage, network, and hosting environment",
        icon="🖥️",
    )

    # Extract infrastructure data
    infra_data = _extract_infrastructure_data(fact_store)

    if not infra_data["items"]:
        empty_state(
            title="No Infrastructure Data",
            message="Run an analysis with infrastructure domain to see details",
            icon="🖥️",
        )
        return

    # Summary
    _render_infra_summary(infra_data)

    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🖥️ Compute",
        "💾 Storage",
        "🔄 Backup/DR",
        "☁️ Cloud",
        "⚠️ Risks",
    ])

    with tab1:
        _render_compute_tab(infra_data)

    with tab2:
        _render_storage_tab(infra_data)

    with tab3:
        _render_backup_dr_tab(infra_data)

    with tab4:
        _render_cloud_tab(infra_data)

    with tab5:
        _render_infra_risks_tab(infra_data, reasoning_store)


def _extract_infrastructure_data(fact_store: Any) -> Dict[str, Any]:
    """Extract infrastructure-related data from fact store."""
    data = {
        "items": [],
        "by_category": {},
        "compute": [],
        "storage": [],
        "backup_dr": [],
        "cloud": [],
        "hosting": [],
        "legacy": [],
        "tooling": [],
    }

    if not fact_store or not fact_store.facts:
        return data

    # Filter infrastructure facts
    infra_facts = [f for f in fact_store.facts if f.domain == "infrastructure"]

    for fact in infra_facts:
        category = fact.category or "other"

        item = {
            "name": fact.item,
            "category": category,
            "vendor": fact.details.get("vendor", ""),
            "version": fact.details.get("version", ""),
            "count": fact.details.get("count", ""),
            "capacity": fact.details.get("capacity", ""),
            "status": fact.status,
            "criticality": fact.details.get("criticality", "medium"),
            "fact_id": fact.fact_id,
            "details": fact.details,
        }

        data["items"].append(item)

        # Track by category
        if category not in data["by_category"]:
            data["by_category"][category] = []
        data["by_category"][category].append(item)

        # Categorize
        if category in ["compute", "servers", "virtual"]:
            data["compute"].append(item)
        elif category in ["storage", "san", "nas"]:
            data["storage"].append(item)
        elif category in ["backup_dr", "backup", "disaster_recovery"]:
            data["backup_dr"].append(item)
        elif category in ["cloud", "iaas", "paas"]:
            data["cloud"].append(item)
        elif category == "hosting":
            data["hosting"].append(item)
        elif category == "legacy":
            data["legacy"].append(item)
        elif category == "tooling":
            data["tooling"].append(item)

    return data


def _render_infra_summary(data: Dict[str, Any]) -> None:
    """Render infrastructure summary metrics."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📊 Total Items", len(data["items"]))

    with col2:
        st.metric("🖥️ Compute", len(data["compute"]))

    with col3:
        st.metric("💾 Storage", len(data["storage"]))

    with col4:
        st.metric("☁️ Cloud", len(data["cloud"]))

    with col5:
        legacy = len(data["legacy"])
        if legacy > 0:
            st.metric("⚠️ Legacy", legacy)
        else:
            st.metric("📁 Categories", len(data["by_category"]))


def _render_compute_tab(data: Dict[str, Any]) -> None:
    """Render compute inventory tab."""
    section_header("Compute Resources", icon="🖥️", level=4)

    items = data["compute"]

    if not items:
        st.info("No compute resources documented")
        return

    st.markdown(f"**{len(items)} compute resource(s):**")

    for item in items:
        _render_infra_item(item)


def _render_storage_tab(data: Dict[str, Any]) -> None:
    """Render storage inventory tab."""
    section_header("Storage Resources", icon="💾", level=4)

    items = data["storage"]

    if not items:
        st.info("No storage resources documented")
        return

    st.markdown(f"**{len(items)} storage resource(s):**")

    for item in items:
        _render_infra_item(item)


def _render_backup_dr_tab(data: Dict[str, Any]) -> None:
    """Render backup/DR tab."""
    section_header("Backup & Disaster Recovery", icon="🔄", level=4)

    items = data["backup_dr"]

    if not items:
        st.warning("No backup/DR documentation found - this is a potential gap")
        return

    st.markdown(f"**{len(items)} backup/DR item(s):**")

    for item in items:
        _render_infra_item(item)

    # DR assessment
    st.divider()
    st.markdown("### DR Assessment")

    # Check for key DR elements
    has_rpo = any("rpo" in str(i["details"]).lower() for i in items)
    has_rto = any("rto" in str(i["details"]).lower() for i in items)
    has_dr_site = any("dr site" in str(i["details"]).lower() or "disaster" in i["name"].lower() for i in items)

    col1, col2, col3 = st.columns(3)

    with col1:
        icon = "✅" if has_rpo else "❌"
        st.markdown(f"{icon} **RPO Defined**")

    with col2:
        icon = "✅" if has_rto else "❌"
        st.markdown(f"{icon} **RTO Defined**")

    with col3:
        icon = "✅" if has_dr_site else "❌"
        st.markdown(f"{icon} **DR Site**")


def _render_cloud_tab(data: Dict[str, Any]) -> None:
    """Render cloud resources tab."""
    section_header("Cloud Resources", icon="☁️", level=4)

    items = data["cloud"]

    if not items:
        st.info("No cloud resources documented")
        return

    st.markdown(f"**{len(items)} cloud resource(s):**")

    # Group by provider if possible
    by_provider = {}
    for item in items:
        provider = item["vendor"] or "Unknown"
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(item)

    for provider, provider_items in by_provider.items():
        provider_icon = {
            "aws": "🟠",
            "azure": "🔵",
            "gcp": "🔴",
            "google": "🔴",
        }.get(provider.lower(), "☁️")

        with st.expander(f"{provider_icon} {provider} ({len(provider_items)})"):
            for item in provider_items:
                _render_infra_item(item, show_vendor=False)


def _render_infra_risks_tab(data: Dict[str, Any], reasoning_store: Any) -> None:
    """Render infrastructure risks tab."""
    section_header("Infrastructure Risks", icon="⚠️", level=4)

    if not reasoning_store or not reasoning_store.risks:
        st.info("Run analysis to identify infrastructure risks")
        return

    # Filter to infrastructure domain
    infra_risks = [r for r in reasoning_store.risks if r.domain == "infrastructure"]

    if not infra_risks:
        st.success("No infrastructure-specific risks identified")
        return

    st.markdown(f"**{len(infra_risks)} infrastructure risk(s):**")

    for risk in sorted(infra_risks, key=lambda r: ["critical", "high", "medium", "low"].index(r.severity) if r.severity in ["critical", "high", "medium", "low"] else 99):
        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(risk.severity, "⚪")

        with st.expander(f"{severity_icon} {risk.title} ({risk.severity.upper()})"):
            st.write(risk.description)

            if hasattr(risk, "mitigation") and risk.mitigation:
                st.markdown("**Mitigation:**")
                st.write(risk.mitigation)

            st.caption(f"Evidence: {', '.join(getattr(risk, 'based_on_facts', []))}")

    # Legacy systems warning
    if data["legacy"]:
        st.divider()
        st.warning(f"**{len(data['legacy'])} legacy system(s) identified** - review for modernization")

        for item in data["legacy"]:
            st.markdown(f"- ⚠️ {item['name']}")


def _render_infra_item(item: Dict, show_vendor: bool = True) -> None:
    """Render a single infrastructure item."""
    criticality_icon = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }.get(item["criticality"], "⚪")

    status_icon = {"documented": "✅", "partial": "⚠️", "gap": "❌"}.get(item["status"], "")

    st.markdown(f"{criticality_icon} **{item['name']}** {status_icon}")

    details = []
    if show_vendor and item["vendor"]:
        details.append(f"Vendor: {item['vendor']}")
    if item["version"]:
        details.append(f"v{item['version']}")
    if item["count"]:
        details.append(f"Count: {item['count']}")
    if item["capacity"]:
        details.append(f"Capacity: {item['capacity']}")

    if details:
        st.caption(" | ".join(details))
