"""
Open Questions View

Displays and manages open questions generated during analysis.

Steps 161-168 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional, Dict

from ..components.layout import page_header, section_header, empty_state
from ..components.badges import severity_badge, domain_badge
from ..components.filters import filter_bar, pagination


def render_open_questions_view(
    fact_store: Any,
    reasoning_store: Optional[Any] = None,
    show_vdr: bool = True,
) -> None:
    """
    Render the open questions view page.

    Args:
        fact_store: FactStore (may contain questions)
        reasoning_store: Optional ReasoningStore
        show_vdr: Whether to show VDR generation option
    """
    page_header(
        title="Open Questions",
        subtitle="Questions requiring follow-up with the target",
        icon="❓",
    )

    # Extract questions from various sources
    questions = _extract_questions(fact_store, reasoning_store)

    if not questions:
        empty_state(
            title="No Open Questions",
            message="All identified questions have been addressed",
            icon="✅",
        )
        return

    # Summary
    _render_questions_summary(questions)

    st.divider()

    # Tabs by status
    tab1, tab2, tab3 = st.tabs([
        "🔵 Open",
        "✓ Answered",
        "⏳ Deferred",
    ])

    with tab1:
        _render_questions_tab(questions, "open")

    with tab2:
        _render_questions_tab(questions, "answered")

    with tab3:
        _render_questions_tab(questions, "deferred")

    # VDR generation
    if show_vdr:
        st.divider()
        _render_vdr_section(questions)


def _extract_questions(fact_store: Any, reasoning_store: Any) -> List[Dict[str, Any]]:
    """Extract open questions from various sources."""
    questions = []

    # From gaps (convert to questions)
    if fact_store and fact_store.gaps:
        for gap in fact_store.gaps:
            question = {
                "id": f"Q-{gap.gap_id}",
                "text": f"Please provide documentation on: {gap.description}",
                "domain": gap.domain,
                "category": gap.category,
                "priority": getattr(gap, "importance", "medium"),
                "source": "gap",
                "source_id": gap.gap_id,
                "status": "open",
                "answer": None,
                "trigger_context": f"Gap identified in {gap.category}",
            }
            questions.append(question)

    # From reasoning store open questions (if available)
    if reasoning_store and hasattr(reasoning_store, "open_questions"):
        for oq in reasoning_store.open_questions:
            question = {
                "id": getattr(oq, "question_id", f"Q-{len(questions)+1}"),
                "text": getattr(oq, "question", str(oq)),
                "domain": getattr(oq, "domain", ""),
                "category": getattr(oq, "category", ""),
                "priority": getattr(oq, "priority", "medium"),
                "source": "analysis",
                "source_id": getattr(oq, "triggered_by", []),
                "status": getattr(oq, "status", "open"),
                "answer": getattr(oq, "answer", None),
                "trigger_context": getattr(oq, "trigger_context", ""),
            }
            questions.append(question)

    return questions


def _render_questions_summary(questions: List[Dict]) -> None:
    """Render questions summary metrics."""
    open_q = len([q for q in questions if q["status"] == "open"])
    answered = len([q for q in questions if q["status"] == "answered"])
    deferred = len([q for q in questions if q["status"] == "deferred"])

    # Priority breakdown
    critical = len([q for q in questions if q["priority"] == "critical" and q["status"] == "open"])
    high = len([q for q in questions if q["priority"] == "high" and q["status"] == "open"])

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("❓ Total", len(questions))

    with col2:
        st.metric("🔵 Open", open_q)

    with col3:
        st.metric("✓ Answered", answered)

    with col4:
        st.metric("🔴 Critical", critical)

    with col5:
        st.metric("🟠 High", high)


def _render_questions_tab(questions: List[Dict], status: str) -> None:
    """Render questions filtered by status."""
    filtered = [q for q in questions if q["status"] == status]

    if not filtered:
        status_label = {"open": "open", "answered": "answered", "deferred": "deferred"}[status]
        st.info(f"No {status_label} questions")
        return

    # Filter controls
    col1, col2 = st.columns(2)

    with col1:
        domains = ["All"] + list(set(q["domain"] for q in filtered if q["domain"]))
        selected_domain = st.selectbox(
            "Domain",
            domains,
            key=f"q_{status}_domain",
        )

    with col2:
        search = st.text_input(
            "Search",
            placeholder="Search questions...",
            key=f"q_{status}_search",
        )

    # Apply filters
    if selected_domain != "All":
        filtered = [q for q in filtered if q["domain"] == selected_domain]

    if search:
        search_lower = search.lower()
        filtered = [q for q in filtered if search_lower in q["text"].lower()]

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    filtered.sort(key=lambda q: priority_order.get(q["priority"], 99))

    # Render questions
    st.caption(f"{len(filtered)} question(s)")

    for question in filtered:
        _render_question_card(question, allow_answer=(status == "open"))


def _render_question_card(question: Dict, allow_answer: bool = False) -> None:
    """Render a single question card."""
    priority_icon = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }.get(question["priority"], "⚪")

    domain_label = question["domain"].replace("_", " ").title() if question["domain"] else "General"

    with st.expander(f"{priority_icon} {question['text'][:80]}{'...' if len(question['text']) > 80 else ''}"):
        # Question details
        st.markdown(f"**Question:** {question['text']}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"**Domain:** {domain_label}")

        with col2:
            st.markdown(f"**Priority:** {question['priority'].title()}")

        with col3:
            st.markdown(f"**Source:** {question['source']}")

        if question["trigger_context"]:
            st.caption(f"Context: {question['trigger_context']}")

        # Answer section
        if question["answer"]:
            st.divider()
            st.markdown("**Answer:**")
            st.success(question["answer"])

        # Answer input for open questions
        if allow_answer:
            st.divider()
            answer = st.text_area(
                "Provide Answer",
                key=f"answer_{question['id']}",
                height=80,
                label_visibility="collapsed",
                placeholder="Enter answer or notes...",
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✓ Mark Answered", key=f"ans_{question['id']}"):
                    # Note: In real app, this would update the store
                    st.success("Marked as answered")

            with col2:
                if st.button("⏳ Defer", key=f"def_{question['id']}"):
                    st.info("Deferred")

            with col3:
                if st.button("🗑️ Remove", key=f"rem_{question['id']}"):
                    st.warning("Removed")


def _render_vdr_section(questions: List[Dict]) -> None:
    """Render VDR generation section."""
    section_header("VDR Request Generation", icon="📋", level=4)

    open_questions = [q for q in questions if q["status"] == "open"]

    if not open_questions:
        st.success("All questions answered - no VDR requests needed")
        return

    st.markdown(f"**{len(open_questions)} open question(s)** can be converted to VDR requests")

    # Priority selection
    col1, col2 = st.columns(2)

    with col1:
        include_critical = st.checkbox("Include Critical", value=True)
        include_high = st.checkbox("Include High", value=True)

    with col2:
        include_medium = st.checkbox("Include Medium", value=True)
        include_low = st.checkbox("Include Low", value=False)

    # Filter for VDR
    vdr_questions = []
    if include_critical:
        vdr_questions.extend([q for q in open_questions if q["priority"] == "critical"])
    if include_high:
        vdr_questions.extend([q for q in open_questions if q["priority"] == "high"])
    if include_medium:
        vdr_questions.extend([q for q in open_questions if q["priority"] == "medium"])
    if include_low:
        vdr_questions.extend([q for q in open_questions if q["priority"] == "low"])

    st.caption(f"{len(vdr_questions)} question(s) selected for VDR")

    # Generate VDR
    if st.button("📥 Generate VDR Request List", type="primary"):
        vdr_content = _generate_vdr_markdown(vdr_questions)

        st.download_button(
            label="📥 Download VDR Requests (Markdown)",
            data=vdr_content,
            file_name="vdr_requests.md",
            mime="text/markdown",
        )

        with st.expander("Preview VDR Requests"):
            st.markdown(vdr_content)


def _generate_vdr_markdown(questions: List[Dict]) -> str:
    """Generate VDR request markdown."""
    lines = [
        "# Virtual Data Room Requests",
        "",
        f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"Total Requests: {len(questions)}",
        "",
        "---",
        "",
    ]

    # Group by domain
    by_domain = {}
    for q in questions:
        domain = q["domain"] or "General"
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(q)

    for domain, domain_questions in sorted(by_domain.items()):
        lines.append(f"## {domain.replace('_', ' ').title()}")
        lines.append("")

        for i, q in enumerate(domain_questions, 1):
            priority_marker = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(q["priority"], "")
            lines.append(f"{i}. {priority_marker} **{q['priority'].upper()}**: {q['text']}")

        lines.append("")

    return "\n".join(lines)
