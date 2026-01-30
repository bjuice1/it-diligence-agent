"""
Facts View

Displays extracted facts with filtering, evidence, and review status.

Steps 123-130 of the alignment plan.

UPDATED: Added dedicated "Needs Review" section with export functionality,
improved fact display with confidence scores and better ID visibility.
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

    # View mode tabs - add "Needs Review" tab
    tab1, tab2, tab3 = st.tabs([
        "📁 By Domain",
        "📋 All Facts",
        "⚠️ Needs Review",
    ])

    with tab1:
        _render_domain_tabs(facts)

    with tab2:
        _render_all_facts(facts, show_export)

    with tab3:
        _render_needs_review_tab(facts)


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

    # Count needs review
    needs_review = len([f for f in facts if getattr(f, 'needs_review', False)])
    low_confidence = len([f for f in facts
                         if getattr(f, 'confidence_score', 1.0) < 0.6
                         and not getattr(f, 'needs_review', False)])

    # Metrics row 1
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

    # Metrics row 2 - data quality
    if needs_review > 0 or low_confidence > 0:
        st.divider()
        st.markdown("##### Data Quality")
        qcol1, qcol2, qcol3 = st.columns(3)

        with qcol1:
            high_conf = len([f for f in facts
                            if getattr(f, 'confidence_score', 1.0) >= 0.6
                            and not getattr(f, 'needs_review', False)])
            st.metric("✅ High Confidence", high_conf)

        with qcol2:
            st.metric("⚠️ Needs Review", needs_review,
                     help="Facts flagged for human verification")

        with qcol3:
            st.metric("❓ Low Confidence", low_confidence,
                     help="Facts with sparse data that may need verification")

        if needs_review > 0:
            st.info(f"👉 **{needs_review} fact(s) need review** - check the 'Needs Review' tab")


def _render_needs_review_tab(facts: List[Any]) -> None:
    """Render dedicated needs review section with export."""
    section_header("Facts Requiring Review", icon="⚠️", level=4)

    # Get facts needing review
    review_facts = [f for f in facts if getattr(f, 'needs_review', False)]
    low_conf_facts = [f for f in facts
                     if getattr(f, 'confidence_score', 1.0) < 0.6
                     and not getattr(f, 'needs_review', False)]

    total_review = len(review_facts) + len(low_conf_facts)

    if total_review == 0:
        st.success("No facts require review at this time")
        return

    # Summary
    st.markdown(f"""
    **Summary:**
    - 🔴 **{len(review_facts)}** facts flagged for review
    - 🟠 **{len(low_conf_facts)}** facts with low confidence

    Review these facts to improve data quality and ensure accurate analysis.
    """)

    st.divider()

    # Export section at top for visibility
    section_header("Export Review List", icon="📥", level=4)

    all_review_facts = review_facts + low_conf_facts

    col1, col2, col3 = st.columns(3)

    with col1:
        csv_data = _generate_review_csv(all_review_facts)
        st.download_button(
            label="📥 Download Review List (CSV)",
            data=csv_data,
            file_name="facts_to_review.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        import json
        json_data = json.dumps([_fact_to_review_dict(f) for f in all_review_facts], indent=2)
        st.download_button(
            label="📥 Download Review List (JSON)",
            data=json_data,
            file_name="facts_to_review.json",
            mime="application/json",
            use_container_width=True,
        )

    with col3:
        markdown_data = _generate_review_markdown(all_review_facts)
        st.download_button(
            label="📥 Download Review List (MD)",
            data=markdown_data,
            file_name="facts_to_review.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()

    # Flagged for review
    if review_facts:
        st.markdown("### 🔴 Flagged for Review")
        st.caption(f"{len(review_facts)} fact(s) explicitly flagged")

        for fact in review_facts:
            _render_review_fact_card(fact)

    # Low confidence
    if low_conf_facts:
        st.divider()
        st.markdown("### 🟠 Low Confidence")
        st.caption(f"{len(low_conf_facts)} fact(s) with confidence < 60%")

        for fact in low_conf_facts:
            _render_review_fact_card(fact)


def _render_review_fact_card(fact: Any) -> None:
    """Render a fact card optimized for review with all details visible."""
    fact_id = getattr(fact, "fact_id", "")
    item = getattr(fact, "item", "")
    domain = getattr(fact, "domain", "")
    category = getattr(fact, "category", "")
    status = getattr(fact, "status", "documented")
    entity = getattr(fact, "entity", "target")
    details = getattr(fact, "details", {})
    evidence = getattr(fact, "evidence", {})
    confidence = getattr(fact, 'confidence_score', 0.0)
    needs_review = getattr(fact, 'needs_review', False)
    review_reason = getattr(fact, 'needs_review_reason', '')
    source_doc = getattr(fact, 'source_document', '')

    conf_pct = int(confidence * 100)
    status_icon = {"documented": "✅", "partial": "⚠️", "gap": "❌"}.get(status, "")
    review_icon = "🔴" if needs_review else "🟠"

    with st.expander(f"{review_icon} **{fact_id}** | {item} | {domain} | {conf_pct}% conf", expanded=False):
        # ID and basic info prominently displayed
        st.markdown(f"""
        **Fact ID:** `{fact_id}`

        **Item:** {item}

        **Domain:** {domain.replace('_', ' ').title()} | **Category:** {category.replace('_', ' ').title()}

        **Status:** {status_icon} {status.title()} | **Confidence:** {conf_pct}%
        """)

        # Review reason (why this needs review)
        st.markdown("---")
        st.markdown("**🔍 Why Review Needed:**")
        if needs_review and review_reason:
            st.warning(review_reason)
        elif confidence < 0.6:
            st.info(f"Low confidence score ({conf_pct}%) - data may be incomplete or ambiguous")
        else:
            st.info("Flagged for verification")

        # Details
        if details:
            st.markdown("---")
            st.markdown("**📋 Details:**")
            details_items = []
            for k, v in details.items():
                if v and v != "not_stated":
                    details_items.append(f"- **{k.replace('_', ' ').title()}:** {v}")
            if details_items:
                st.markdown("\n".join(details_items))
            else:
                st.caption("No specific details extracted (sparse data)")

        # Evidence
        st.markdown("---")
        st.markdown("**📄 Source Evidence:**")
        if source_doc:
            st.caption(f"Document: {source_doc}")

        if evidence:
            exact_quote = evidence.get("exact_quote", "")
            source_section = evidence.get("source_section", "")

            if exact_quote:
                st.markdown(f'> "{exact_quote}"')
            if source_section:
                st.caption(f"Section: {source_section}")
        else:
            st.caption("No source evidence recorded")

    st.markdown("")  # Spacing


def _generate_review_csv(facts: List[Any]) -> str:
    """Generate CSV for facts needing review."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Fact ID", "Item", "Domain", "Category", "Status",
        "Confidence %", "Needs Review", "Review Reason",
        "Details", "Source Document", "Source Quote"
    ])

    # Data rows
    for fact in facts:
        confidence = getattr(fact, 'confidence_score', 0.0)
        conf_pct = int(confidence * 100)
        needs_review = getattr(fact, 'needs_review', False)
        review_reason = getattr(fact, 'needs_review_reason', '')

        if not needs_review and confidence < 0.6:
            review_reason = f"Low confidence ({conf_pct}%)"

        details = getattr(fact, "details", {})
        details_str = "; ".join([
            f"{k}: {v}" for k, v in details.items()
            if v and v != "not_stated"
        ])

        evidence = getattr(fact, "evidence", {})
        source_quote = evidence.get("exact_quote", "")[:200] if evidence else ""

        writer.writerow([
            fact.fact_id,
            fact.item,
            fact.domain,
            fact.category,
            fact.status,
            conf_pct,
            "Yes" if needs_review else "No",
            review_reason,
            details_str,
            getattr(fact, 'source_document', ''),
            source_quote,
        ])

    return output.getvalue()


def _generate_review_markdown(facts: List[Any]) -> str:
    """Generate Markdown report for facts needing review."""
    lines = [
        "# Facts Requiring Review",
        "",
        f"**Total:** {len(facts)} fact(s) need verification",
        "",
        "---",
        "",
    ]

    for fact in facts:
        confidence = getattr(fact, 'confidence_score', 0.0)
        conf_pct = int(confidence * 100)
        needs_review = getattr(fact, 'needs_review', False)
        review_reason = getattr(fact, 'needs_review_reason', '')

        if not needs_review and confidence < 0.6:
            review_reason = f"Low confidence ({conf_pct}%)"

        lines.append(f"## {fact.fact_id}")
        lines.append("")
        lines.append(f"**Item:** {fact.item}")
        lines.append(f"**Domain:** {fact.domain} | **Category:** {fact.category}")
        lines.append(f"**Status:** {fact.status} | **Confidence:** {conf_pct}%")
        lines.append("")
        lines.append(f"**Review Reason:** {review_reason}")
        lines.append("")

        details = getattr(fact, "details", {})
        if details:
            lines.append("**Details:**")
            for k, v in details.items():
                if v and v != "not_stated":
                    lines.append(f"- {k}: {v}")
            lines.append("")

        evidence = getattr(fact, "evidence", {})
        if evidence and evidence.get("exact_quote"):
            lines.append("**Source:**")
            lines.append(f'> "{evidence["exact_quote"][:300]}"')
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _fact_to_review_dict(fact: Any) -> dict:
    """Convert fact to dictionary for review export."""
    confidence = getattr(fact, 'confidence_score', 0.0)
    needs_review = getattr(fact, 'needs_review', False)
    review_reason = getattr(fact, 'needs_review_reason', '')

    if not needs_review and confidence < 0.6:
        review_reason = f"Low confidence ({int(confidence * 100)}%)"

    return {
        "fact_id": fact.fact_id,
        "item": fact.item,
        "domain": fact.domain,
        "category": fact.category,
        "status": fact.status,
        "confidence_percent": int(confidence * 100),
        "needs_review": needs_review,
        "review_reason": review_reason,
        "entity": getattr(fact, "entity", "target"),
        "details": getattr(fact, "details", {}),
        "evidence": getattr(fact, "evidence", {}),
        "source_document": getattr(fact, "source_document", ""),
    }


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

    # Count review items in this domain
    review_count = len([f for f in facts
                       if getattr(f, 'needs_review', False)
                       or getattr(f, 'confidence_score', 1.0) < 0.6])

    if review_count > 0:
        st.info(f"⚠️ {review_count} fact(s) in this domain need review")

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
                # Count review items in category
                cat_review = len([f for f in cat_filtered
                                 if getattr(f, 'needs_review', False)
                                 or getattr(f, 'confidence_score', 1.0) < 0.6])
                review_indicator = f" ⚠️{cat_review}" if cat_review > 0 else ""

                st.markdown(f"### {category.replace('_', ' ').title()} ({len(cat_filtered)}){review_indicator}")
                for fact in cat_filtered:
                    _render_enhanced_fact_card(fact)
                    st.divider()
    else:
        for fact in filtered:
            _render_enhanced_fact_card(fact)
            st.divider()


def _render_enhanced_fact_card(fact: Any) -> None:
    """Render enhanced fact card with confidence and review indicators."""
    fact_id = getattr(fact, "fact_id", "")
    item = getattr(fact, "item", "")
    domain = getattr(fact, "domain", "")
    category = getattr(fact, "category", "")
    status = getattr(fact, "status", "documented")
    entity = getattr(fact, "entity", "target")
    details = getattr(fact, "details", {})
    evidence = getattr(fact, "evidence", {})
    confidence = getattr(fact, 'confidence_score', 1.0)
    needs_review = getattr(fact, 'needs_review', False)

    conf_pct = int(confidence * 100)
    entity_badge = "🎯" if entity == "target" else "🏢"
    status_icon = {"documented": "✅", "partial": "⚠️", "gap": "❌"}.get(status, "")

    # Review indicator
    review_badge = ""
    if needs_review:
        review_badge = " 🔴"
    elif confidence < 0.6:
        review_badge = " 🟠"

    # Header with prominent ID
    st.markdown(f"**`{fact_id}`** {entity_badge} {status_icon}{review_badge}")
    st.markdown(f"**{item}**")

    # Confidence bar
    if confidence < 1.0:
        conf_color = "green" if confidence >= 0.6 else "orange" if confidence >= 0.4 else "red"
        st.progress(confidence, text=f"Confidence: {conf_pct}%")

    # Synthesized statement
    statement = _synthesize_fact_statement(fact)
    st.markdown(f"> {statement}")

    # Details
    if details:
        details_str = ", ".join([
            f"{k}: {v}"
            for k, v in details.items()
            if v and v != "not_stated"
        ])
        if details_str:
            st.caption(f"📋 {details_str}")

    # Source quote
    if evidence and evidence.get("exact_quote"):
        quote = evidence["exact_quote"]
        if len(quote) > 150:
            quote = quote[:150] + "..."
        st.caption(f'📄 Source: "{quote}"')


def _synthesize_fact_statement(fact: Any) -> str:
    """Synthesize a fact statement from details."""
    item = getattr(fact, "item", "")
    details = getattr(fact, "details", {})

    parts = [item]

    # Add key details
    if details.get("version"):
        parts.append(f"(v{details['version']})")
    if details.get("count"):
        parts.append(f"- {details['count']} units")
    if details.get("vendor"):
        parts.append(f"by {details['vendor']}")
    if details.get("status"):
        parts.append(f"[{details['status']}]")

    return " ".join(parts)


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
    col1, col2, col3, col4 = st.columns(4)

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
        quality_filter = st.selectbox(
            "Data Quality",
            ["All", "High Confidence", "Needs Review", "Low Confidence"],
            key="facts_all_quality",
        )

    with col4:
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

    if quality_filter == "Needs Review":
        filtered = [f for f in filtered if getattr(f, 'needs_review', False)]
    elif quality_filter == "High Confidence":
        filtered = [f for f in filtered
                   if getattr(f, 'confidence_score', 1.0) >= 0.6
                   and not getattr(f, 'needs_review', False)]
    elif quality_filter == "Low Confidence":
        filtered = [f for f in filtered
                   if getattr(f, 'confidence_score', 1.0) < 0.6
                   and not getattr(f, 'needs_review', False)]

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
        _render_enhanced_fact_card(fact)
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
        "Confidence %", "Needs Review", "Details", "Source"
    ])

    # Data rows
    for fact in facts:
        confidence = getattr(fact, 'confidence_score', 1.0)
        conf_pct = int(confidence * 100)
        needs_review = getattr(fact, 'needs_review', False)

        details_str = ", ".join([
            f"{k}: {v}" for k, v in getattr(fact, "details", {}).items()
            if v and v != "not_stated"
        ])

        evidence = getattr(fact, "evidence", {})
        source = evidence.get("exact_quote", "")[:100] if evidence else ""

        writer.writerow([
            fact.fact_id,
            fact.item,
            fact.domain,
            fact.category,
            fact.status,
            getattr(fact, "entity", "target"),
            conf_pct,
            "Yes" if needs_review else "No",
            details_str,
            source,
        ])

    return output.getvalue()


def _fact_to_dict(fact: Any) -> dict:
    """Convert fact to dictionary."""
    confidence = getattr(fact, 'confidence_score', 1.0)
    return {
        "fact_id": fact.fact_id,
        "item": fact.item,
        "domain": fact.domain,
        "category": fact.category,
        "status": fact.status,
        "entity": getattr(fact, "entity", "target"),
        "confidence_percent": int(confidence * 100),
        "needs_review": getattr(fact, "needs_review", False),
        "details": getattr(fact, "details", {}),
        "evidence": getattr(fact, "evidence", {}),
    }
