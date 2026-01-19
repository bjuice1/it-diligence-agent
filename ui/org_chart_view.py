"""
Organization Chart View - Streamlit UI Components

Visualizes organizational structure with:
- Interactive org chart (mermaid diagram)
- Dropdown filters for departments/roles/teams
- Headcount breakdown by team
- Links to organizational facts and findings
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tools_v2.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore
except ImportError as e:
    st.error(f"Import error: {e}")


# =============================================================================
# SAMPLE ORG DATA (when no facts available)
# =============================================================================

SAMPLE_ORG_STRUCTURE = {
    "Executive Leadership": {
        "icon": "👔",
        "roles": [
            {"title": "CEO", "name": "", "headcount": 1},
            {"title": "CFO", "name": "", "headcount": 1},
            {"title": "CTO", "name": "", "headcount": 1},
            {"title": "COO", "name": "", "headcount": 1},
        ],
        "total": 4
    },
    "IT / Technology": {
        "icon": "💻",
        "roles": [
            {"title": "VP of Engineering", "name": "", "headcount": 1},
            {"title": "IT Director", "name": "", "headcount": 1},
            {"title": "Infrastructure Team", "name": "", "headcount": 8},
            {"title": "Security Team", "name": "", "headcount": 4},
            {"title": "Help Desk", "name": "", "headcount": 6},
        ],
        "total": 20
    },
    "Applications": {
        "icon": "📱",
        "roles": [
            {"title": "VP of Applications", "name": "", "headcount": 1},
            {"title": "ERP Team", "name": "", "headcount": 12},
            {"title": "Web Development", "name": "", "headcount": 15},
            {"title": "QA Team", "name": "", "headcount": 8},
            {"title": "DevOps", "name": "", "headcount": 10},
        ],
        "total": 46
    },
    "Finance": {
        "icon": "💰",
        "roles": [
            {"title": "Controller", "name": "", "headcount": 1},
            {"title": "Accounting Team", "name": "", "headcount": 8},
            {"title": "FP&A", "name": "", "headcount": 4},
        ],
        "total": 13
    },
    "Operations": {
        "icon": "⚙️",
        "roles": [
            {"title": "VP Operations", "name": "", "headcount": 1},
            {"title": "Supply Chain", "name": "", "headcount": 15},
            {"title": "Manufacturing", "name": "", "headcount": 50},
            {"title": "Quality", "name": "", "headcount": 10},
        ],
        "total": 76
    }
}


def extract_org_from_facts(fact_store: FactStore) -> Dict[str, Any]:
    """
    Extract organizational structure from facts.
    """
    if not fact_store:
        return {}

    org_facts = [f for f in fact_store.facts if f.domain == "organization"]

    if not org_facts:
        return {}

    # Group by category
    org_structure = {}

    for fact in org_facts:
        category = fact.category.replace("_", " ").title()

        if category not in org_structure:
            org_structure[category] = {
                "icon": "👤",
                "roles": [],
                "total": 0,
                "facts": []
            }

        # Extract headcount from details
        headcount = 1
        if fact.details:
            headcount = fact.details.get("headcount") or fact.details.get("count") or fact.details.get("fte") or 1
            if isinstance(headcount, str):
                try:
                    headcount = int(headcount)
                except:
                    headcount = 1

        org_structure[category]["roles"].append({
            "title": fact.item,
            "name": fact.details.get("name", "") if fact.details else "",
            "headcount": headcount,
            "fact_id": fact.fact_id,
            "verified": fact.verified
        })
        org_structure[category]["total"] += headcount
        org_structure[category]["facts"].append(fact)

    return org_structure


def render_mermaid_chart(org_structure: Dict, selected_dept: str = "All"):
    """Render mermaid org chart."""

    # Build mermaid code
    lines = ["flowchart TD"]

    # Add CEO at top
    lines.append('    CEO["👔 CEO / President"]')

    # Add departments
    dept_ids = []
    for i, (dept_name, dept_data) in enumerate(org_structure.items()):
        if selected_dept != "All" and dept_name != selected_dept:
            continue

        dept_id = f"DEPT{i}"
        dept_ids.append(dept_id)
        icon = dept_data.get("icon", "📁")
        total = dept_data.get("total", 0)
        lines.append(f'    {dept_id}["{icon} {dept_name}<br/>({total} FTE)"]')
        lines.append(f'    CEO --> {dept_id}')

        # Add roles under department
        for j, role in enumerate(dept_data.get("roles", [])[:5]):  # Limit to 5 roles
            role_id = f"R{i}_{j}"
            title = role.get("title", "Role")
            hc = role.get("headcount", 1)
            if hc > 1:
                lines.append(f'    {role_id}["{title}<br/>({hc})"]')
            else:
                lines.append(f'    {role_id}["{title}"]')
            lines.append(f'    {dept_id} --> {role_id}')

    # Styling
    lines.append("")
    lines.append("    style CEO fill:#f97316,color:#fff")
    for dept_id in dept_ids:
        lines.append(f"    style {dept_id} fill:#3b82f6,color:#fff")

    mermaid_code = "\n".join(lines)

    # Render
    html = f"""
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>
        <style>
            body {{ margin: 0; padding: 20px; background: transparent; }}
            .mermaid {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
        </style>
    </head>
    <body>
        <div class="mermaid">
{mermaid_code}
        </div>
    </body>
    </html>
    """
    components.html(html, height=500, scrolling=True)

    return mermaid_code


def render_org_dropdown_explorer(org_structure: Dict):
    """
    Render the main org dropdown explorer.
    THIS IS THE KEY COMPONENT - shows dropdown for each department.
    """
    st.subheader("👥 Organization Explorer")

    # Calculate totals
    total_headcount = sum(d.get("total", 0) for d in org_structure.values())
    dept_count = len(org_structure)

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Headcount", total_headcount)
    with col2:
        st.metric("Departments", dept_count)
    with col3:
        st.metric("Roles Tracked", sum(len(d.get("roles", [])) for d in org_structure.values()))

    st.divider()

    # MAIN DROPDOWN - Select Department
    dept_names = list(org_structure.keys())

    selected_dept = st.selectbox(
        "🏢 Select Department/Team",
        ["-- Select a Department --"] + dept_names,
        key="org_dept_dropdown",
        help="Select a department to see its team structure and roles"
    )

    if selected_dept and selected_dept != "-- Select a Department --":
        dept_data = org_structure.get(selected_dept, {})

        st.markdown(f"### {dept_data.get('icon', '📁')} {selected_dept}")
        st.markdown(f"**Total Headcount: {dept_data.get('total', 0)} FTE**")

        st.divider()

        # Show roles in this department
        roles = dept_data.get("roles", [])

        if roles:
            st.markdown("#### Team Breakdown")

            # Create a table of roles
            role_data = []
            for role in roles:
                role_data.append({
                    "Role/Team": role.get("title", "Unknown"),
                    "Name": role.get("name", "-"),
                    "Headcount": role.get("headcount", 1),
                    "Verified": "✅" if role.get("verified", False) else "⚠️"
                })

            df = pd.DataFrame(role_data)

            # Display as styled table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Role/Team": st.column_config.TextColumn("Role/Team", width="medium"),
                    "Headcount": st.column_config.NumberColumn("Headcount", width="small"),
                    "Verified": st.column_config.TextColumn("Status", width="small")
                }
            )

            # Visual breakdown
            st.markdown("#### Headcount Distribution")
            chart_data = pd.DataFrame({
                "Role": [r.get("title", "") for r in roles],
                "Headcount": [r.get("headcount", 1) for r in roles]
            })
            st.bar_chart(chart_data.set_index("Role"))

        else:
            st.info("No detailed roles available for this department.")

    else:
        # Show all departments as cards when nothing selected
        st.markdown("### All Departments")

        cols = st.columns(2)
        for i, (dept_name, dept_data) in enumerate(org_structure.items()):
            with cols[i % 2]:
                with st.container():
                    icon = dept_data.get("icon", "📁")
                    total = dept_data.get("total", 0)
                    role_count = len(dept_data.get("roles", []))

                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:8px; padding:15px; margin:5px 0;">
                        <h4>{icon} {dept_name}</h4>
                        <p><strong>{total}</strong> FTE across <strong>{role_count}</strong> roles</p>
                    </div>
                    """, unsafe_allow_html=True)


def render_org_considerations(reasoning_store: ReasoningStore):
    """Render org-related risks and work items."""
    st.subheader("⚠️ Organizational Considerations")

    if not reasoning_store:
        st.info("No findings data available.")
        return

    org_risks = [r for r in reasoning_store.risks if r.domain == "organization"]
    org_work_items = [w for w in reasoning_store.work_items if w.domain == "organization"]

    if not org_risks and not org_work_items:
        st.info("No organization-specific risks or work items found.")
        return

    # Dropdown for type
    view_type = st.selectbox(
        "View",
        ["All", "Risks Only", "Work Items Only"],
        key="org_consideration_type"
    )

    if view_type in ["All", "Risks Only"] and org_risks:
        st.markdown("### Organizational Risks")
        for risk in org_risks:
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(risk.severity, "⚪")
            with st.expander(f"{severity_icon} {risk.title}"):
                st.markdown(risk.description)
                if risk.mitigation:
                    st.markdown(f"**Mitigation:** {risk.mitigation}")

    if view_type in ["All", "Work Items Only"] and org_work_items:
        st.markdown("### Organizational Work Items")
        for wi in org_work_items:
            with st.expander(f"📋 {wi.title} ({wi.phase})"):
                st.markdown(wi.description)
                st.markdown(f"**Owner:** {wi.owner_type} | **Cost:** {wi.cost_estimate}")


def render_org_chart_section(session_dir: Path):
    """
    Main entry point for the org chart UI.
    """
    st.header("🏢 Organization Structure")

    # Try to load actual data
    fact_store = None
    reasoning_store = None
    org_structure = None

    facts_path = session_dir / "facts.json"
    findings_path = session_dir / "findings.json"

    if facts_path.exists():
        try:
            fact_store = FactStore.load(str(facts_path))
            org_structure = extract_org_from_facts(fact_store)
        except Exception as e:
            st.warning(f"Could not load facts: {e}")

    if findings_path.exists():
        try:
            reasoning_store = ReasoningStore.load(str(findings_path))
        except Exception as e:
            pass

    # Use sample data if no real org data
    if not org_structure:
        st.info("📊 Showing sample organization structure. Run analysis with organizational documents to populate with real data.")
        org_structure = SAMPLE_ORG_STRUCTURE

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Org Explorer", "🗺️ Org Chart", "⚠️ Considerations"])

    with tab1:
        render_org_dropdown_explorer(org_structure)

    with tab2:
        st.subheader("Organization Chart")

        # Department filter for chart
        dept_filter = st.selectbox(
            "Filter Chart by Department",
            ["All"] + list(org_structure.keys()),
            key="chart_dept_filter"
        )

        mermaid_code = render_mermaid_chart(org_structure, dept_filter)

        with st.expander("View Diagram Code"):
            st.code(mermaid_code, language="mermaid")

    with tab3:
        render_org_considerations(reasoning_store)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Organization Chart", layout="wide")
    st.title("Organization Chart Viewer")
    render_org_chart_section(Path("sessions/test"))
