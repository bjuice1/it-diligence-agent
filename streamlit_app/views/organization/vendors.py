"""
Vendors View

Vendor and MSP relationship analysis.

Steps 137-138 of the alignment plan.
"""

import streamlit as st
from typing import Any, Optional, Dict, List

from ...components.layout import section_header, empty_state


def render_vendors_view(
    fact_store: Any,
    reasoning_store: Optional[Any] = None,
) -> None:
    """
    Render the vendors analysis view.

    Args:
        fact_store: FactStore with vendor facts
        reasoning_store: Optional ReasoningStore
    """
    st.markdown("### 🤝 Vendor Analysis")

    # Extract vendor data
    vendors = _extract_vendors(fact_store)

    if not vendors:
        empty_state(
            title="No Vendor Data",
            message="Run an analysis to identify vendor relationships",
            icon="🤝",
        )
        return

    # Summary
    _render_vendor_summary(vendors)

    st.divider()

    # Vendor list
    _render_vendor_list(vendors)

    # TSA implications
    st.divider()
    _render_tsa_implications(vendors, reasoning_store)


def _extract_vendors(fact_store: Any) -> List[Dict[str, Any]]:
    """Extract vendor data from facts."""
    vendors = []

    if not fact_store or not fact_store.facts:
        return vendors

    # Find vendor facts across domains
    for fact in fact_store.facts:
        if fact.category == "vendors" or "vendor" in fact.item.lower():
            vendor = {
                "name": fact.item,
                "domain": fact.domain,
                "service_type": fact.details.get("service_type", ""),
                "contract_status": fact.details.get("contract_status", ""),
                "relationship_type": fact.details.get("relationship_type", "vendor"),
                "criticality": fact.details.get("criticality", "medium"),
                "fact_id": fact.fact_id,
            }
            vendors.append(vendor)

    return vendors


def _render_vendor_summary(vendors: List[Dict[str, Any]]) -> None:
    """Render vendor summary metrics."""
    # Count by type
    msp = len([v for v in vendors if v["relationship_type"] == "msp"])
    critical = len([v for v in vendors if v["criticality"] == "critical"])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🤝 Total Vendors", len(vendors))

    with col2:
        st.metric("🏢 MSPs", msp)

    with col3:
        st.metric("🔴 Critical", critical)

    with col4:
        # Count by domain
        domains = len(set(v["domain"] for v in vendors))
        st.metric("📁 Domains", domains)


def _render_vendor_list(vendors: List[Dict[str, Any]]) -> None:
    """Render vendor list."""
    section_header("Vendor Inventory", icon="📋", level=4)

    # Group by domain
    by_domain = {}
    for vendor in vendors:
        domain = vendor["domain"]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(vendor)

    # Render by domain
    for domain, domain_vendors in by_domain.items():
        domain_label = domain.replace("_", " ").title()

        with st.expander(f"📁 {domain_label} ({len(domain_vendors)})"):
            for vendor in domain_vendors:
                criticality_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                }.get(vendor["criticality"], "⚪")

                type_badge = ""
                if vendor["relationship_type"] == "msp":
                    type_badge = " 🏢 MSP"

                st.markdown(f"{criticality_icon} **{vendor['name']}**{type_badge}")

                if vendor["service_type"]:
                    st.caption(f"Service: {vendor['service_type']}")

                if vendor["contract_status"]:
                    st.caption(f"Contract: {vendor['contract_status']}")


def _render_tsa_implications(
    vendors: List[Dict[str, Any]],
    reasoning_store: Optional[Any],
) -> None:
    """Render TSA implications for vendor relationships."""
    section_header("TSA Considerations", icon="📄", level=4)

    # Check for critical/MSP vendors
    critical_vendors = [v for v in vendors if v["criticality"] == "critical"]
    msp_vendors = [v for v in vendors if v["relationship_type"] == "msp"]

    if critical_vendors or msp_vendors:
        st.warning("**Transition Service Agreement may be needed for:**")

        for vendor in critical_vendors + msp_vendors:
            is_msp = vendor["relationship_type"] == "msp"
            label = "MSP" if is_msp else "Critical Vendor"
            st.markdown(f"- **{vendor['name']}** ({label})")

        st.markdown("""
        **Key considerations:**
        - Contract assignment or novation requirements
        - Service continuity during transition
        - Knowledge transfer from vendor staff
        - Exit planning and timeline
        """)
    else:
        st.success("No critical vendor dependencies requiring TSA identified")

    # Related work items
    if reasoning_store and reasoning_store.work_items:
        vendor_items = [
            w for w in reasoning_store.work_items
            if "vendor" in w.title.lower() or "contract" in w.title.lower()
        ]

        if vendor_items:
            st.divider()
            st.markdown("**Related Work Items:**")
            for wi in vendor_items[:3]:
                phase_icon = {"Day_1": "🚨", "Day_100": "📅", "Post_100": "🎯"}.get(wi.phase, "📋")
                st.markdown(f"- {phase_icon} {wi.title}")
