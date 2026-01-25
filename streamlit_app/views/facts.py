"""
Facts View

Displays extracted facts with filtering and evidence.

Steps 123-130 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional, Dict

from ..components.layout import page_header, section_header, empty_state
from ..components.cards import fact_card
from ..components.filters import filter_bar, pagination, domain_filter
from ..components.charts import domain_breakdown_bar
from ..utils.formatting import format_count


def render_facts_view(
    fact_store: Any,
    show_export: bool = True,
) -> None:
    """
    Render the facts view page.

    Args:
        fact_store: FactStore with extracted facts
        show_export: Whether to show export options
    """
    page_header(
        title="Extracted Facts",
        subtitle="IT inventory and documentation from source documents",
        icon="📁",
    )

    # Check for data
    if fact_store is None or not fact_store.facts:
        empty_state(
            title="No Facts Extracted",
            message="Run an analysis to extract facts from documents",
            icon="📁",
        )
        return

    facts = fact_store.facts

    # Summary
    _render_facts_summary(facts)

    st.divider()

    # Domain tabs or filter view
    view_mode = st.radio(
        "View Mode",
        ["By Domain", "All Facts"],
        horizontal=True,
        key="facts_view_mode",
    )

    if view_mode == "By Domain":
        _render_domain_tabs(facts)
    else:
        _render_all_facts(facts, show_export)


def _render_facts_summary(facts: List[Any]) -> None:
    """Render facts summary metrics."""
    # Count by domain
    facts_by_domain = {}
    for fact in facts:
        domain = fact.domain
        facts_by_domain[domain] = facts_by_domain.get(domain, 0) + 1

    # Count by status
    documented = len([f for f in facts if f.status == "documented"])
    partial = len([f for f in facts if f.status == "partial"])
    gap = len([f for f in facts if f.status == "gap"])

    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📊 Total Facts", len(facts))
    with col2:
        st.metric("✅ Documented", documented)
    with col3:
        st.metric("⚠️ Partial", partial)
    with col4:
        st.metric("❌ Gaps", gap)
    with col5:
        st.metric("📁 Domains", len(facts_by_domain))


def _render_domain_tabs(facts: List[Any]) -> None:
    """Render facts grouped by domain in tabs."""
    # Group by domain
    facts_by_domain = {}
    for fact in facts:
        domain = fact.domain
        if domain not in facts_by_domain:
            facts_by_domain[domain] = []
        facts_by_domain[domain].append(fact)

    # Create tabs
    domains = list(facts_by_domain.keys())
    tab_labels = [f"{d.replace('_', ' ').title()} ({len(facts_by_domain[d])})" for d in domains]

    tabs = st.tabs(tab_labels)

    for tab, domain in zip(tabs, domains):
        with tab:
            domain_facts = facts_by_domain[domain]
            _render_domain_facts(domain_facts, domain)


def _render_domain_facts(facts: List[Any], domain: str) -> None:
    """Render facts for a specific domain."""
    # Group by category
    by_category = {}
    for fact in facts:
        cat = fact.category or "other"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(fact)

    # Category filter
    categories = ["All"] + list(by_category.keys())
    selected_cat = st.selectbox(
        "Filter by Category",
        categories,
        key=f"facts_{domain}_cat",
    )

    # Filter
    if selected_cat != "All":
        filtered = by_category.get(selected_cat, [])
    else:
        filtered = facts

    # Search
    search = st.text_input(
        "Search facts",
        placeholder="Search by item name or details...",
        key=f"facts_{domain}_search",
    )

    if search:
        search_lower = search.lower()
        filtered = [
            f for f in filtered
            if search_lower in f.item.lower() or
               search_lower in str(f.details).lower()
        ]

    # Results
    st.caption(f"Showing {len(filtered)} facts")

    # Render by category
    if selected_cat == "All":
        for category, cat_facts in sorted(by_category.items()):
            cat_filtered = [f for f in cat_facts if f in filtered]
            if cat_filtered:
                st.markdown(f"### {category.replace('_', ' ').title()} ({len(cat_filtered)})")
                for fact in cat_filtered:
                    fact_card(fact, show_details=True, show_evidence=True)
                    st.divider()
    else:
        for fact in filtered:
            fact_card(fact, show_details=True, show_evidence=True)
            st.divider()


def _render_all_facts(facts: List[Any], show_export: bool) -> None:
    """Render all facts with filtering."""
    # Domain breakdown chart
    facts_by_domain = {}
    for fact in facts:
        domain = fact.domain
        facts_by_domain[domain] = facts_by_domain.get(domain, 0) + 1

    domain_breakdown_bar(
        counts=facts_by_domain,
        title="Facts by Domain",
        height=250,
    )

    st.divider()

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        domain = st.selectbox(
            "Domain",
            ["All"] + list(facts_by_domain.keys()),
            key="facts_all_domain",
            format_func=lambda x: x.replace("_", " ").title() if x != "All" else "All Domains",
        )

    with col2:
        status = st.selectbox(
            "Status",
            ["All", "documented", "partial", "gap"],
            key="facts_all_status",
        )

    with col3:
        search = st.text_input(
            "Search",
            placeholder="Search facts...",
            key="facts_all_search",
        )

    # Apply filters
    filtered = facts

    if domain != "All":
        filtered = [f for f in filtered if f.domain == domain]

    if status != "All":
        filtered = [f for f in filtered if f.status == status]

    if search:
        search_lower = search.lower()
        filtered = [
            f for f in filtered
            if search_lower in f.item.lower() or
               search_lower in str(f.details).lower()
        ]

    # Results
    st.caption(f"Showing {len(filtered)} of {len(facts)} facts")

    # Pagination
    if len(filtered) > 20:
        start, end = pagination(
            total_items=len(filtered),
            items_per_page=20,
            key="facts_all_pagination",
        )
        page_facts = filtered[start:end]
    else:
        page_facts = filtered

    # Render facts
    for fact in page_facts:
        fact_card(fact, show_details=True, show_evidence=True)
        st.divider()

    # Export
    if show_export:
        _render_export_options(filtered)


def _render_export_options(facts: List[Any]) -> None:
    """Render export options."""
    section_header("Export", icon="📥", level=4)

    col1, col2 = st.columns(2)

    with col1:
        csv_data = _generate_csv(facts)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="facts.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        import json
        json_data = json.dumps([_fact_to_dict(f) for f in facts], indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name="facts.json",
            mime="application/json",
            use_container_width=True,
        )


def _generate_csv(facts: List[Any]) -> str:
    """Generate CSV data from facts."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID", "Item", "Domain", "Category", "Status", "Entity",
        "Details", "Source"
    ])

    # Data rows
    for fact in facts:
        details_str = ", ".join([
            f"{k}: {v}" for k, v in getattr(fact, "details", {}).items()
            if v and v != "not_stated"
        ])

        evidence = getattr(fact, "evidence", {})
        source = evidence.get("exact_quote", "")[:100]

        writer.writerow([
            fact.fact_id,
            fact.item,
            fact.domain,
            fact.category,
            fact.status,
            getattr(fact, "entity", "target"),
            details_str,
            source,
        ])

    return output.getvalue()


def _fact_to_dict(fact: Any) -> dict:
    """Convert fact to dictionary."""
    return {
        "fact_id": fact.fact_id,
        "item": fact.item,
        "domain": fact.domain,
        "category": fact.category,
        "status": fact.status,
        "entity": getattr(fact, "entity", "target"),
        "details": getattr(fact, "details", {}),
        "evidence": getattr(fact, "evidence", {}),
    }
