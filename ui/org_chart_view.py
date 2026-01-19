"""
Organization Chart View - Streamlit UI Components

Visualizes organizational structure with:
- Interactive org chart (mermaid diagram)
- Dropdown filters for departments/roles
- Links to organizational facts and findings
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tools_v2.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore
except ImportError as e:
    st.error(f"Import error: {e}")


@dataclass
class OrgNode:
    """Represents a node in the org chart."""
    id: str
    title: str
    name: Optional[str] = None
    department: Optional[str] = None
    reports_to: Optional[str] = None
    headcount: Optional[int] = None
    facts: List[str] = None  # Fact IDs related to this node

    def __post_init__(self):
        if self.facts is None:
            self.facts = []


def extract_org_structure(fact_store: FactStore) -> Dict[str, Any]:
    """
    Extract organizational structure from facts.

    Looks for org-related facts and builds a hierarchy.
    """
    org_facts = [f for f in fact_store.facts if f.domain == "organization"]

    # Build org nodes from facts
    nodes = {}
    relationships = []

    # Extract roles, departments, and reporting structures
    for fact in org_facts:
        category = fact.category.lower()
        item = fact.item
        details = fact.details or {}

        if category in ["leadership", "executive", "management", "c-suite"]:
            node_id = f"exec_{len(nodes)}"
            nodes[node_id] = OrgNode(
                id=node_id,
                title=details.get("title", item),
                name=details.get("name", ""),
                department=details.get("department", "Executive"),
                reports_to=details.get("reports_to"),
                headcount=details.get("headcount"),
                facts=[fact.fact_id]
            )

        elif category in ["department", "team", "function", "division"]:
            node_id = f"dept_{len(nodes)}"
            nodes[node_id] = OrgNode(
                id=node_id,
                title=item,
                department=item,
                headcount=details.get("headcount") or details.get("count"),
                facts=[fact.fact_id]
            )

        elif category in ["headcount", "staffing", "fte"]:
            # Add to existing or create new
            dept = details.get("department", "General")
            node_id = f"hc_{len(nodes)}"
            nodes[node_id] = OrgNode(
                id=node_id,
                title=f"{dept} Team",
                department=dept,
                headcount=details.get("count") or details.get("headcount"),
                facts=[fact.fact_id]
            )

    return {
        "nodes": nodes,
        "relationships": relationships,
        "total_facts": len(org_facts),
        "raw_facts": org_facts
    }


def generate_mermaid_org_chart(org_data: Dict[str, Any], selected_dept: str = "All") -> str:
    """
    Generate a Mermaid diagram for the org chart.
    """
    nodes = org_data.get("nodes", {})

    if not nodes:
        # Return a sample org chart if no data
        return """
flowchart TD
    CEO[CEO / President]
    CFO[CFO]
    CTO[CTO]
    COO[COO]
    CISO[CISO]

    CEO --> CFO
    CEO --> CTO
    CEO --> COO
    CTO --> CISO

    CFO --> FIN[Finance Team]
    CTO --> ENG[Engineering]
    CTO --> IT[IT Operations]
    COO --> OPS[Operations]
    CISO --> SEC[Security Team]

    style CEO fill:#f97316,color:#fff
    style CFO fill:#3b82f6,color:#fff
    style CTO fill:#3b82f6,color:#fff
    style COO fill:#3b82f6,color:#fff
    style CISO fill:#10b981,color:#fff
"""

    # Build mermaid from actual nodes
    lines = ["flowchart TD"]

    # Filter by department if selected
    filtered_nodes = nodes.values()
    if selected_dept != "All":
        filtered_nodes = [n for n in nodes.values() if n.department == selected_dept]

    # Add nodes
    for node in filtered_nodes:
        label = node.title
        if node.name:
            label = f"{node.title}<br/>{node.name}"
        if node.headcount:
            label += f"<br/>({node.headcount} FTE)"

        lines.append(f'    {node.id}["{label}"]')

    # Add relationships
    for node in filtered_nodes:
        if node.reports_to and node.reports_to in nodes:
            lines.append(f"    {node.reports_to} --> {node.id}")

    # Add styling
    lines.append("")
    lines.append("    %% Styling")
    for i, node in enumerate(filtered_nodes):
        if "exec" in node.id or "ceo" in node.id.lower():
            lines.append(f"    style {node.id} fill:#f97316,color:#fff")
        elif "dept" in node.id:
            lines.append(f"    style {node.id} fill:#3b82f6,color:#fff")

    return "\n".join(lines)


def render_mermaid(mermaid_code: str, height: int = 400):
    """
    Render a Mermaid diagram in Streamlit.
    """
    html = f"""
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0;
                padding: 20px;
                background: transparent;
            }}
            .mermaid {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div class="mermaid">
{mermaid_code}
        </div>
    </body>
    </html>
    """
    components.html(html, height=height, scrolling=True)


def render_org_dropdown(fact_store: FactStore, reasoning_store: ReasoningStore = None):
    """
    Render dropdown-based org explorer.
    """
    st.subheader("Organization Explorer")

    org_facts = [f for f in fact_store.facts if f.domain == "organization"]

    if not org_facts:
        st.info("No organizational facts found. Run analysis on documents containing org information.")
        return

    # Get unique categories/departments
    categories = list(set(f.category for f in org_facts))

    # Dropdown for category
    selected_category = st.selectbox(
        "Select Area",
        ["All"] + sorted(categories),
        key="org_category_select"
    )

    # Filter facts
    if selected_category != "All":
        filtered_facts = [f for f in org_facts if f.category == selected_category]
    else:
        filtered_facts = org_facts

    # Display as expandable cards
    for fact in filtered_facts:
        with st.expander(f"👤 {fact.item} ({fact.category})"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**{fact.item}**")
                if fact.details:
                    for k, v in fact.details.items():
                        st.markdown(f"- {k}: {v}")

                # Show evidence
                quote = fact.evidence.get("exact_quote", "")
                if quote:
                    st.markdown("**Evidence:**")
                    st.markdown(f"> {quote[:200]}...")

            with col2:
                st.caption(f"Fact ID: {fact.fact_id}")
                st.caption(f"Status: {fact.status}")
                if fact.verified:
                    st.success("✅ Verified")
                else:
                    st.warning("⚠️ Unverified")


def render_org_considerations(reasoning_store: ReasoningStore):
    """
    Render organizational considerations with dropdowns.
    """
    st.subheader("Organizational Considerations")

    if not reasoning_store:
        st.info("No reasoning data available.")
        return

    # Get org-related risks and work items
    org_risks = [r for r in reasoning_store.risks if r.domain == "organization"]
    org_work_items = [w for w in reasoning_store.work_items if w.domain == "organization"]
    org_strategic = [s for s in reasoning_store.strategic_considerations if s.domain == "organization"]

    # Dropdown for consideration type
    consideration_type = st.selectbox(
        "Consideration Type",
        ["All", "Risks", "Work Items", "Strategic Considerations"],
        key="org_consideration_type"
    )

    # Display based on selection
    if consideration_type in ["All", "Risks"] and org_risks:
        st.markdown("### Organizational Risks")
        for risk in org_risks:
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(risk.severity, "⚪")
            with st.expander(f"{severity_icon} {risk.title}"):
                st.markdown(risk.description)
                st.markdown(f"**Mitigation:** {risk.mitigation}")
                st.caption(f"Based on: {', '.join(risk.based_on_facts)}")

    if consideration_type in ["All", "Work Items"] and org_work_items:
        st.markdown("### Organizational Work Items")
        for wi in org_work_items:
            with st.expander(f"📋 {wi.title} ({wi.phase})"):
                st.markdown(wi.description)
                st.markdown(f"**Owner:** {wi.owner_type}")
                st.markdown(f"**Cost:** {wi.cost_estimate}")

    if consideration_type in ["All", "Strategic Considerations"] and org_strategic:
        st.markdown("### Strategic Considerations")
        for sc in org_strategic:
            with st.expander(f"💡 {sc.title}"):
                st.markdown(sc.description)


def render_org_chart_section(session_dir: Path):
    """
    Main entry point for the org chart UI.
    """
    # Load data
    facts_path = session_dir / "facts.json"
    findings_path = session_dir / "findings.json"

    fact_store = None
    reasoning_store = None

    if facts_path.exists():
        try:
            fact_store = FactStore.load(str(facts_path))
        except Exception as e:
            st.warning(f"Could not load facts: {e}")

    if findings_path.exists():
        try:
            reasoning_store = ReasoningStore.load(str(findings_path))
        except Exception as e:
            st.warning(f"Could not load findings: {e}")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Org Chart", "Org Explorer", "Considerations"])

    with tab1:
        st.subheader("Organization Chart")

        # Department filter
        if fact_store:
            org_data = extract_org_structure(fact_store)
            departments = list(set(n.department for n in org_data["nodes"].values() if n.department))

            selected_dept = st.selectbox(
                "Filter by Department",
                ["All"] + sorted(departments),
                key="org_chart_dept_filter"
            )

            mermaid_code = generate_mermaid_org_chart(org_data, selected_dept)
        else:
            st.info("No org data loaded - showing sample chart")
            mermaid_code = generate_mermaid_org_chart({})

        render_mermaid(mermaid_code, height=500)

        # Show raw mermaid code option
        with st.expander("View Diagram Code"):
            st.code(mermaid_code, language="mermaid")

    with tab2:
        if fact_store:
            render_org_dropdown(fact_store, reasoning_store)
        else:
            st.info("Load facts to explore organizational data.")

    with tab3:
        if reasoning_store:
            render_org_considerations(reasoning_store)
        else:
            st.info("Load findings to view organizational considerations.")


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Organization Chart", layout="wide")
    st.title("Organization Chart Viewer")

    session_dir = st.text_input(
        "Session Directory",
        value="sessions/test_session"
    )

    if session_dir:
        render_org_chart_section(Path(session_dir))
