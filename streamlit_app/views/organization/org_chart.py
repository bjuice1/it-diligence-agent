"""
Org Chart View

Organizational structure visualization using Mermaid.

Steps 133, 143 of the alignment plan.

UPDATED: Now uses organization_bridge to get StaffMember data with
proper hierarchy from reports_to relationships.
"""

import streamlit as st
from typing import Any, Optional, Dict, List
import sys
from pathlib import Path

# Add project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.organization_bridge import build_organization_from_facts
from models.organization_stores import OrganizationDataStore
from models.organization_models import RoleCategory


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
    st.markdown("### Organization Chart")

    # Get org data via bridge
    store, status = _get_org_data_store(fact_store)

    if not store or not store.staff_members:
        st.info("No organizational structure data available")
        _render_placeholder_chart()
        return

    # Build org data from StaffMember objects
    org_data = _build_org_chart_data(store)

    if not org_data["nodes"]:
        st.info("No organizational structure data available")
        _render_placeholder_chart()
        return

    # Generate and render Mermaid chart
    mermaid_code = _generate_mermaid_chart(org_data)

    # Render chart
    _render_mermaid(mermaid_code)

    # Show staff list below chart
    st.divider()
    _render_staff_list(store)

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


def _get_org_data_store(fact_store: Any) -> tuple:
    """Get OrganizationDataStore from facts via organization bridge."""
    if not fact_store or not hasattr(fact_store, 'facts') or not fact_store.facts:
        return None, "no_facts"

    try:
        return build_organization_from_facts(fact_store)
    except Exception as e:
        st.error(f"Error loading org data: {e}")
        return None, f"error: {str(e)}"


def _build_org_chart_data(store: OrganizationDataStore) -> Dict[str, Any]:
    """
    Build org chart data from OrganizationDataStore.

    Uses StaffMember.reports_to for proper hierarchy.
    """
    data = {
        "nodes": [],
        "relationships": [],
    }

    # Build nodes from staff members
    for staff in store.staff_members:
        # Determine node type based on category
        if staff.role_category == RoleCategory.LEADERSHIP:
            node_type = "leadership"
        elif staff.role_category in [RoleCategory.INFRASTRUCTURE, RoleCategory.APPLICATIONS, RoleCategory.SECURITY]:
            node_type = "team"
        else:
            node_type = "role"

        # Create label with name and title
        if staff.name and staff.name != "-" and staff.name != "Unknown":
            label = f"{staff.name}\\n{staff.role_title}"
        else:
            label = staff.role_title

        node = {
            "id": _sanitize_id(staff.id),
            "label": label,
            "type": node_type,
            "reports_to": staff.reports_to,
            "category": staff.role_category,
            "compensation": staff.base_compensation,
            "is_key_person": staff.is_key_person,
        }
        data["nodes"].append(node)

    # Build relationships from reports_to
    for node in data["nodes"]:
        if node.get("reports_to"):
            parent_name = node["reports_to"]
            # Try to find parent by name or title
            parent = _find_parent_node(data["nodes"], parent_name)
            if parent:
                data["relationships"].append({
                    "from": parent["id"],
                    "to": node["id"],
                })

    return data


def _sanitize_id(id_str: str) -> str:
    """Sanitize ID for Mermaid (no special characters)."""
    return id_str.replace("-", "_").replace(" ", "_").replace(".", "_")


def _find_parent_node(nodes: List[Dict], parent_name: str) -> Optional[Dict]:
    """Find a parent node by name or title."""
    parent_lower = parent_name.lower()

    # Try exact match on name/title
    for node in nodes:
        label = node.get("label", "").lower()
        if parent_lower in label or label in parent_lower:
            return node

    # Try partial match
    for node in nodes:
        label = node.get("label", "").lower()
        # Check if any word matches
        parent_words = parent_lower.split()
        for word in parent_words:
            if len(word) > 3 and word in label:
                return node

    return None


def _generate_mermaid_chart(org_data: Dict[str, Any]) -> str:
    """Generate Mermaid flowchart code from org data."""
    lines = ["graph TD"]

    # Group nodes by type for styling
    leadership_ids = []
    team_ids = []
    role_ids = []

    # Add nodes
    for node in org_data["nodes"]:
        node_id = node["id"]
        label = node["label"]

        # Add key person indicator
        if node.get("is_key_person"):
            label = f"⭐ {label}"

        # Escape quotes in label
        label = label.replace('"', "'")

        lines.append(f'    {node_id}["{label}"]')

        # Track for styling
        if node["type"] == "leadership":
            leadership_ids.append(node_id)
        elif node["type"] == "team":
            team_ids.append(node_id)
        else:
            role_ids.append(node_id)

    # Add relationships
    for rel in org_data["relationships"]:
        lines.append(f'    {rel["from"]} --> {rel["to"]}')

    # Add styles
    lines.extend([
        "",
        "    classDef leadership fill:#f97316,stroke:#ea580c,color:#fff",
        "    classDef team fill:#dbeafe,stroke:#3b82f6,color:#1e40af",
        "    classDef role fill:#f3f4f6,stroke:#9ca3af,color:#374151",
    ])

    # Apply styles
    if leadership_ids:
        lines.append(f"    class {','.join(leadership_ids)} leadership")
    if team_ids:
        lines.append(f"    class {','.join(team_ids)} team")
    if role_ids:
        lines.append(f"    class {','.join(role_ids)} role")

    return "\n".join(lines)


def _render_staff_list(store: OrganizationDataStore) -> None:
    """Render a tabular list of staff below the chart."""
    import pandas as pd

    st.markdown("### Staff Directory")

    rows = []
    for staff in store.staff_members:
        comp_str = f"${staff.base_compensation:,.0f}" if staff.base_compensation else "-"
        key_badge = "⭐" if staff.is_key_person else ""
        reports_to = staff.reports_to or "-"

        rows.append({
            "Name": staff.name or "-",
            "Role": staff.role_title,
            "Reports To": reports_to,
            "Category": staff.role_category.display_name if hasattr(staff.role_category, 'display_name') else staff.role_category.value,
            "Compensation": comp_str,
            "Key": key_badge,
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Role": st.column_config.TextColumn("Role", width="medium"),
                "Reports To": st.column_config.TextColumn("Reports To", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Compensation": st.column_config.TextColumn("Compensation", width="small"),
                "Key": st.column_config.TextColumn("Key", width="small"),
            }
        )


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
    store, status = _get_org_data_store(fact_store)

    if not store or not store.staff_members:
        st.info("No org chart data available")
        return

    org_data = _build_org_chart_data(store)

    if not org_data["nodes"]:
        st.info("No org chart data available")
        return

    mermaid_code = _generate_mermaid_chart(org_data)

    try:
        import streamlit_mermaid as stmd
        stmd.st_mermaid(mermaid_code, height=height)
    except ImportError:
        st.code(mermaid_code, language="mermaid")
