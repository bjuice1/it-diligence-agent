"""
Diagram rendering components for Streamlit UI.

Provides mermaid diagram rendering, charts, and other visualizations.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, List, Any


def render_mermaid(mermaid_code: str, height: int = 400) -> None:
    """
    Render a mermaid diagram in Streamlit.

    Args:
        mermaid_code: The mermaid diagram code
        height: Height of the diagram container in pixels
    """
    html = f"""
    <div style="background: white; padding: 20px; border-radius: 8px;">
        <pre class="mermaid" style="display: flex; justify-content: center;">
{mermaid_code}
        </pre>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
    """
    components.html(html, height=height)


def render_cost_breakdown_chart(cost_data: Dict[str, Any]) -> None:
    """
    Render a cost breakdown chart by phase.

    Args:
        cost_data: Dictionary with 'by_phase' containing Day_1, Day_100, Post_100 costs
    """
    import pandas as pd

    by_phase = cost_data.get("by_phase", {})

    # Prepare data for chart
    phases = []
    low_costs = []
    high_costs = []

    for phase in ["Day_1", "Day_100", "Post_100"]:
        if phase in by_phase:
            phases.append(phase.replace("_", " "))
            low_costs.append(by_phase[phase].get("low", 0))
            high_costs.append(by_phase[phase].get("high", 0))

    if not phases:
        st.info("No cost data available")
        return

    # Create a simple bar chart showing the range
    chart_data = pd.DataFrame({
        "Phase": phases,
        "Low Estimate": [c / 1000 for c in low_costs],  # Convert to thousands
        "High Estimate": [c / 1000 for c in high_costs],
    })

    st.bar_chart(
        chart_data.set_index("Phase"),
        use_container_width=True
    )
    st.caption("Cost estimates in thousands ($K)")


def render_risk_distribution_chart(risks: List[Dict]) -> None:
    """
    Render a risk distribution chart by severity.

    Args:
        risks: List of risk dictionaries with 'severity' field
    """
    import pandas as pd

    # Count by severity
    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for risk in risks:
        sev = risk.get("severity", "medium").capitalize()
        if sev in severity_counts:
            severity_counts[sev] += 1

    # Create chart
    _ = pd.DataFrame({
        "Severity": list(severity_counts.keys()),
        "Count": list(severity_counts.values())
    })

    # Use columns for a horizontal display
    cols = st.columns(4)
    colors = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}

    for i, (sev, count) in enumerate(severity_counts.items()):
        with cols[i]:
            st.metric(
                label=f"{colors[sev]} {sev}",
                value=count
            )


def render_timeline_diagram(work_items: List[Dict]) -> None:
    """
    Render a timeline/gantt-style diagram for work items by phase.

    Args:
        work_items: List of work item dictionaries with 'phase' and 'title'
    """
    # Group by phase
    phases = {"Day_1": [], "Day_100": [], "Post_100": []}
    for wi in work_items:
        phase = wi.get("phase", "Day_100")
        if phase in phases:
            phases[phase].append(wi.get("title", "Unnamed"))

    # Build mermaid gantt
    mermaid_code = """gantt
    title Integration Timeline
    dateFormat  YYYY-MM-DD

    section Day 1
"""

    start_date = "2024-01-01"
    for i, item in enumerate(phases["Day_1"][:5]):  # Limit to 5 per phase
        mermaid_code += f"    {item[:30]} :d1_{i}, {start_date}, 30d\n"

    mermaid_code += "\n    section Day 100\n"
    for i, item in enumerate(phases["Day_100"][:5]):
        mermaid_code += f"    {item[:30]} :d100_{i}, 2024-02-01, 90d\n"

    mermaid_code += "\n    section Post 100\n"
    for i, item in enumerate(phases["Post_100"][:5]):
        mermaid_code += f"    {item[:30]} :p100_{i}, 2024-05-01, 180d\n"

    render_mermaid(mermaid_code, height=350)


def render_infrastructure_diagram(facts: List[Dict]) -> None:
    """
    Render an infrastructure overview diagram from facts.

    Args:
        facts: List of fact dictionaries from infrastructure domain
    """
    # Filter infrastructure facts
    infra_facts = [f for f in facts if f.get("domain") == "infrastructure"]

    if not infra_facts:
        st.info("No infrastructure facts available for diagram")
        return

    # Group by category
    categories = {}
    for fact in infra_facts:
        cat = fact.get("category", "Other")
        if cat not in categories:
            categories[cat] = []
        item = fact.get("item", "")
        if item and item not in categories[cat]:
            categories[cat].append(item)

    # Build mermaid flowchart
    mermaid_code = "flowchart TB\n"
    mermaid_code += "    subgraph Infrastructure\n"

    for cat, items in categories.items():
        safe_cat = cat.replace(" ", "_").replace("-", "_")
        mermaid_code += f"        subgraph {safe_cat}[{cat}]\n"
        for i, item in enumerate(items[:5]):  # Limit items
            safe_item = item.replace('"', "'")[:25]
            mermaid_code += f"            {safe_cat}_{i}[{safe_item}]\n"
        mermaid_code += "        end\n"

    mermaid_code += "    end\n"

    render_mermaid(mermaid_code, height=400)


def render_domain_summary_cards(facts: List[Dict], gaps: List[Dict]) -> None:
    """
    Render summary cards for each domain showing facts vs gaps.

    Args:
        facts: List of all facts
        gaps: List of all gaps
    """
    domains = ["infrastructure", "cybersecurity", "applications", "organization", "data"]

    cols = st.columns(len(domains))

    for i, domain in enumerate(domains):
        domain_facts = len([f for f in facts if f.get("domain") == domain])
        domain_gaps = len([g for g in gaps if g.get("domain") == domain])

        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
                        padding: 1rem; border-radius: 8px; text-align: center;
                        border: 1px solid #7dd3fc;">
                <div style="font-size: 0.8rem; color: #0369a1; text-transform: uppercase;">
                    {domain}
                </div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #0c4a6e;">
                    {domain_facts}
                </div>
                <div style="font-size: 0.75rem; color: #64748b;">
                    facts | {domain_gaps} gaps
                </div>
            </div>
            """, unsafe_allow_html=True)
