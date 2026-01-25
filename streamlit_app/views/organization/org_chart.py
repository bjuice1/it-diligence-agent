"""
Org Chart View

Organizational structure visualization using Mermaid.

Steps 133, 143 of the alignment plan.
"""

import streamlit as st
from typing import Any, Optional, Dict, List


def render_org_chart(
    fact_store: Any,
    reasoning_store: Optional[Any] = None,
) -> None:
    """
    Render the org chart visualization.

    Args:
        fact_store: FactStore with organization facts
        reasoning_store: Optional ReasoningStore
    """
    st.markdown("### 🏢 Organization Chart")

    # Extract org data
    org_data = _extract_org_data(fact_store)

    if not org_data["nodes"]:
        st.info("No organizational structure data available")
        _render_placeholder_chart()
        return

    # Generate and render Mermaid chart
    mermaid_code = _generate_mermaid_chart(org_data)

    # Render chart
    _render_mermaid(mermaid_code)

    # Export options
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="📥 Download Mermaid Code",
            data=mermaid_code,
            file_name="org_chart.mmd",
            mime="text/plain",
        )

    with col2:
        st.button(
            "📥 Download PNG",
            disabled=True,
            help="PNG export coming soon",
        )


def _extract_org_data(fact_store: Any) -> Dict[str, Any]:
    """Extract org chart data from facts."""
    data = {
        "nodes": [],
        "relationships": [],
    }

    if not fact_store or not fact_store.facts:
        return data

    # Find organization/structure facts
    org_facts = [
        f for f in fact_store.facts
        if f.domain == "organization" and f.category in ["structure", "staffing"]
    ]

    # Build nodes from staffing facts
    for fact in org_facts:
        if fact.category == "staffing":
            node = {
                "id": fact.fact_id.replace("-", "_"),
                "label": fact.item,
                "type": fact.details.get("type", "role"),
                "reports_to": fact.details.get("reports_to", None),
            }
            data["nodes"].append(node)

    # Build relationships
    for node in data["nodes"]:
        if node.get("reports_to"):
            # Find parent node
            parent_label = node["reports_to"]
            parent = next((n for n in data["nodes"] if parent_label.lower() in n["label"].lower()), None)
            if parent:
                data["relationships"].append({
                    "from": parent["id"],
                    "to": node["id"],
                })

    return data


def _generate_mermaid_chart(org_data: Dict[str, Any]) -> str:
    """Generate Mermaid flowchart code from org data."""
    lines = ["graph TD"]

    # Add nodes
    for node in org_data["nodes"]:
        node_id = node["id"]
        label = node["label"]

        # Style based on type
        if node["type"] == "leadership":
            lines.append(f'    {node_id}["{label}"]:::leadership')
        elif node["type"] == "team":
            lines.append(f'    {node_id}["{label}"]:::team')
        else:
            lines.append(f'    {node_id}["{label}"]')

    # Add relationships
    for rel in org_data["relationships"]:
        lines.append(f'    {rel["from"]} --> {rel["to"]}')

    # Add styles
    lines.extend([
        "",
        "    classDef leadership fill:#f97316,stroke:#ea580c,color:#fff",
        "    classDef team fill:#dbeafe,stroke:#3b82f6,color:#1e40af",
    ])

    return "\n".join(lines)


def _render_placeholder_chart() -> str:
    """Render a placeholder org chart."""
    placeholder = """
graph TD
    CIO["CIO / IT Leader"]

    CIO --> INFRA["Infrastructure"]
    CIO --> APPS["Applications"]
    CIO --> SEC["Security"]
    CIO --> OPS["Operations"]

    INFRA --> SYS["Systems Admin"]
    INFRA --> NET["Network Admin"]

    APPS --> DEV["Development"]
    APPS --> SUPPORT["App Support"]

    SEC --> SECOPS["Security Ops"]

    OPS --> HELPDESK["Help Desk"]
    OPS --> DBA["Database Admin"]

    classDef leadership fill:#f97316,stroke:#ea580c,color:#fff
    classDef team fill:#dbeafe,stroke:#3b82f6,color:#1e40af

    class CIO leadership
    class INFRA,APPS,SEC,OPS team
    """

    st.caption("*Placeholder chart - upload documents with org data for actual structure*")
    _render_mermaid(placeholder)


def _render_mermaid(code: str) -> None:
    """
    Render Mermaid diagram in Streamlit.

    Uses streamlit-mermaid if available, falls back to code display.
    """
    try:
        # Try to use streamlit-mermaid
        import streamlit_mermaid as stmd
        stmd.st_mermaid(code, height=400)
    except ImportError:
        # Fallback: Show as HTML using Mermaid CDN
        html = f"""
        <div class="mermaid" style="text-align: center;">
        {code}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        </script>
        """
        st.components.v1.html(html, height=450, scrolling=True)


def render_org_chart_inline(
    fact_store: Any,
    height: int = 300,
) -> None:
    """
    Render org chart inline (for embedding in other views).

    Args:
        fact_store: FactStore with organization facts
        height: Chart height in pixels
    """
    org_data = _extract_org_data(fact_store)

    if not org_data["nodes"]:
        st.info("No org chart data available")
        return

    mermaid_code = _generate_mermaid_chart(org_data)

    try:
        import streamlit_mermaid as stmd
        stmd.st_mermaid(mermaid_code, height=height)
    except ImportError:
        st.code(mermaid_code, language="mermaid")
