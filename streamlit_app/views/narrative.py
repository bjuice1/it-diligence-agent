"""
Narrative View

Executive narrative and deal readout display.

Steps 183-185 of the alignment plan.
"""

import streamlit as st
from typing import Any, Optional, Dict, List
from pathlib import Path
import json

from ..components.layout import page_header, section_header, empty_state


def render_narrative_view(
    narrative_data: Optional[Dict] = None,
    fact_store: Optional[Any] = None,
    reasoning_store: Optional[Any] = None,
    session_dir: Optional[Path] = None,
) -> None:
    """
    Render the executive narrative view.

    Args:
        narrative_data: Pre-loaded narrative data
        fact_store: FactStore for citation lookup
        reasoning_store: ReasoningStore for findings
        session_dir: Session directory to load narrative from
    """
    page_header(
        title="Executive Narrative",
        subtitle="Investment committee-ready storyline",
        icon="📄",
    )

    # Try to load narrative if not provided
    if narrative_data is None and session_dir:
        narrative_data = _load_narrative(session_dir)

    if narrative_data is None:
        # Generate from reasoning store if available
        if reasoning_store:
            narrative_data = _generate_narrative_from_findings(reasoning_store, fact_store)

    if narrative_data is None:
        empty_state(
            title="No Narrative Available",
            message="Run analysis with --narrative flag to generate executive narrative",
            icon="📄",
        )
        _render_narrative_instructions()
        return

    # Build fact lookup for citations
    fact_lookup = _build_fact_lookup(fact_store)

    # Render narrative sections
    _render_executive_summary(narrative_data, fact_lookup)

    st.divider()

    # Domain narratives
    _render_domain_narratives(narrative_data, fact_lookup)

    st.divider()

    # Deal implications
    _render_deal_implications(narrative_data)

    # Export options
    st.divider()
    _render_export_options(narrative_data)


def _load_narrative(session_dir: Path) -> Optional[Dict]:
    """Load narrative from session directory."""
    narrative_file = session_dir / "narrative.json"

    if narrative_file.exists():
        try:
            with open(narrative_file, "r") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Error loading narrative: {e}")

    return None


def _generate_narrative_from_findings(reasoning_store: Any, fact_store: Any) -> Dict:
    """Generate a basic narrative from findings."""
    narrative = {
        "executive_summary": [],
        "domain_narratives": {},
        "deal_implications": {},
        "generated": True,
    }

    if not reasoning_store:
        return narrative

    # Executive summary bullets
    risk_count = len(reasoning_store.risks)
    critical_risks = len([r for r in reasoning_store.risks if r.severity == "critical"])
    work_item_count = len(reasoning_store.work_items)
    day1_items = len([w for w in reasoning_store.work_items if w.phase == "Day_1"])

    narrative["executive_summary"] = [
        f"Analysis identified {risk_count} risks ({critical_risks} critical) requiring attention",
        f"{work_item_count} work items identified across Day 1, Day 100, and Post-100 phases",
        f"{day1_items} critical Day 1 items require immediate post-close action",
    ]

    # Domain narratives
    domains = list(set(r.domain for r in reasoning_store.risks))

    for domain in domains:
        domain_risks = [r for r in reasoning_store.risks if r.domain == domain]
        domain_items = [w for w in reasoning_store.work_items if w.domain == domain]

        narrative["domain_narratives"][domain] = {
            "headline": f"{len(domain_risks)} risks and {len(domain_items)} work items identified",
            "key_findings": [r.title for r in domain_risks[:3]],
            "recommendations": [w.title for w in domain_items[:3]],
        }

    return narrative


def _build_fact_lookup(fact_store: Any) -> Dict[str, Dict]:
    """Build fact lookup for citation tooltips."""
    lookup = {}

    if fact_store:
        for fact in fact_store.facts:
            lookup[fact.fact_id] = {
                "description": fact.item,
                "details": getattr(fact, "details", {}),
                "status": fact.status,
            }

    return lookup


def _render_executive_summary(narrative: Dict, fact_lookup: Dict) -> None:
    """Render executive summary section."""
    section_header("Executive Summary", icon="📋", level=3)

    summary_points = narrative.get("executive_summary", [])

    if summary_points:
        for point in summary_points:
            st.markdown(f"- {point}")
    else:
        st.info("No executive summary available")

    # Key metrics if available
    metrics = narrative.get("key_metrics", {})
    if metrics:
        st.divider()
        cols = st.columns(len(metrics))
        for i, (label, value) in enumerate(metrics.items()):
            with cols[i]:
                st.metric(label, value)


def _render_domain_narratives(narrative: Dict, fact_lookup: Dict) -> None:
    """Render domain-specific narratives."""
    section_header("Domain Analysis", icon="📁", level=3)

    domain_narratives = narrative.get("domain_narratives", {})

    if not domain_narratives:
        st.info("No domain narratives available")
        return

    # Create tabs for each domain
    domains = list(domain_narratives.keys())
    domain_labels = [d.replace("_", " ").title() for d in domains]

    tabs = st.tabs(domain_labels)

    for tab, domain in zip(tabs, domains):
        with tab:
            domain_data = domain_narratives[domain]

            # Headline
            headline = domain_data.get("headline", "")
            if headline:
                st.markdown(f"**{headline}**")

            # Key findings
            findings = domain_data.get("key_findings", [])
            if findings:
                st.markdown("### Key Findings")
                for finding in findings:
                    st.markdown(f"- {finding}")

            # Recommendations
            recommendations = domain_data.get("recommendations", [])
            if recommendations:
                st.markdown("### Recommendations")
                for rec in recommendations:
                    st.markdown(f"- {rec}")

            # Narrative prose
            prose = domain_data.get("narrative", "")
            if prose:
                st.markdown("### Analysis")
                st.write(prose)


def _render_deal_implications(narrative: Dict) -> None:
    """Render deal implications section."""
    section_header("Deal Implications", icon="💼", level=3)

    implications = narrative.get("deal_implications", {})

    if not implications:
        st.info("No deal implications data available")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Value considerations
        st.markdown("### Value Considerations")
        value_items = implications.get("value", [])
        if value_items:
            for item in value_items:
                st.markdown(f"- 💰 {item}")
        else:
            st.caption("No value considerations identified")

        # Integration complexity
        st.markdown("### Integration Complexity")
        complexity_items = implications.get("integration", [])
        if complexity_items:
            for item in complexity_items:
                st.markdown(f"- 🔧 {item}")
        else:
            st.caption("No integration items identified")

    with col2:
        # Synergy opportunities
        st.markdown("### Synergy Opportunities")
        synergy_items = implications.get("synergies", [])
        if synergy_items:
            for item in synergy_items:
                st.markdown(f"- 🎯 {item}")
        else:
            st.caption("No synergy opportunities identified")

        # TSA considerations
        st.markdown("### TSA Considerations")
        tsa_items = implications.get("tsa", [])
        if tsa_items:
            for item in tsa_items:
                st.markdown(f"- 📄 {item}")
        else:
            st.caption("No TSA considerations identified")


def _render_export_options(narrative: Dict) -> None:
    """Render export options for narrative."""
    section_header("Export", icon="📥", level=4)

    col1, col2, col3 = st.columns(3)

    with col1:
        # Markdown export
        md_content = _generate_narrative_markdown(narrative)
        st.download_button(
            label="📥 Download Markdown",
            data=md_content,
            file_name="executive_narrative.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col2:
        # JSON export
        json_content = json.dumps(narrative, indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_content,
            file_name="narrative.json",
            mime="application/json",
            use_container_width=True,
        )

    with col3:
        st.button(
            "📥 Download PDF",
            disabled=True,
            use_container_width=True,
            help="PDF export coming soon",
        )


def _generate_narrative_markdown(narrative: Dict) -> str:
    """Generate markdown version of narrative."""
    lines = [
        "# Executive Narrative",
        "",
        "## Executive Summary",
        "",
    ]

    for point in narrative.get("executive_summary", []):
        lines.append(f"- {point}")

    lines.extend(["", "## Domain Analysis", ""])

    for domain, data in narrative.get("domain_narratives", {}).items():
        lines.append(f"### {domain.replace('_', ' ').title()}")
        lines.append("")

        if data.get("headline"):
            lines.append(f"**{data['headline']}**")
            lines.append("")

        if data.get("key_findings"):
            lines.append("**Key Findings:**")
            for finding in data["key_findings"]:
                lines.append(f"- {finding}")
            lines.append("")

        if data.get("recommendations"):
            lines.append("**Recommendations:**")
            for rec in data["recommendations"]:
                lines.append(f"- {rec}")
            lines.append("")

    return "\n".join(lines)


def _render_narrative_instructions() -> None:
    """Render instructions for generating narratives."""
    st.markdown("""
    ### How to Generate Narratives

    The Executive Narrative synthesizes findings into a coherent story for the investment committee.

    **To generate a narrative:**

    1. **CLI Method:**
    ```bash
    python main_v2.py data/input/ --all --narrative
    ```

    2. **Programmatic Method:**
    ```python
    from agents_v2 import NarrativeSynthesisAgent

    agent = NarrativeSynthesisAgent()
    narrative = agent.synthesize(
        domain_findings=findings,
        deal_context={"deal_type": "carveout", "target_name": "Acme"}
    )
    ```

    **Narrative Sections:**
    - **Executive Summary** - 6-8 bullet points for the IC
    - **Domain Analysis** - Function-by-function deep dive
    - **Deal Implications** - Value, integration, synergies, TSA
    - **Risk & Opportunity Tables** - Prioritized action items
    """)
