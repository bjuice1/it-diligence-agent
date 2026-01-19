"""
Infrastructure Inventory Panel - Gap Analysis View

Shows what infrastructure information we have vs what's missing:
- Compute, Storage, Network, EUC, DR/Backup, Monitoring
- Visual indicators for coverage status
- Links to source documents
- Missing items highlighted prominently
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tools_v2.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore
except ImportError as e:
    st.error(f"Import error: {e}")


# =============================================================================
# INFRASTRUCTURE CATEGORIES
# =============================================================================

INFRA_CATEGORIES = {
    "compute": {
        "label": "Compute",
        "icon": "🖥️",
        "keywords": ["server", "vm", "virtual machine", "compute", "cpu", "host", "vmware", "esxi", "hyper-v", "bare metal", "instance"],
        "required": True,
        "description": "Physical and virtual servers, compute instances"
    },
    "storage": {
        "label": "Storage",
        "icon": "💾",
        "keywords": ["storage", "san", "nas", "disk", "volume", "s3", "blob", "efs", "netapp", "emc", "pure"],
        "required": True,
        "description": "Storage arrays, SAN/NAS, object storage"
    },
    "network": {
        "label": "Network",
        "icon": "🌐",
        "keywords": ["network", "switch", "router", "firewall", "vlan", "subnet", "vpn", "load balancer", "dns", "wan", "lan", "mpls"],
        "required": True,
        "description": "Network infrastructure, firewalls, load balancers"
    },
    "euc": {
        "label": "End User Computing",
        "icon": "💻",
        "keywords": ["laptop", "desktop", "workstation", "endpoint", "euc", "vdi", "citrix", "windows", "mac", "chromebook"],
        "required": True,
        "description": "Laptops, desktops, VDI infrastructure"
    },
    "dr_backup": {
        "label": "DR / Backup",
        "icon": "🔄",
        "keywords": ["backup", "disaster recovery", "dr", "replication", "failover", "rto", "rpo", "veeam", "commvault", "cohesity", "rubrik", "zerto"],
        "required": True,
        "description": "Backup systems, disaster recovery, replication"
    },
    "monitoring": {
        "label": "Monitoring",
        "icon": "📊",
        "keywords": ["monitoring", "observability", "apm", "logging", "metrics", "splunk", "datadog", "newrelic", "nagios", "prometheus", "grafana"],
        "required": True,
        "description": "Monitoring, logging, observability tools"
    },
    "security": {
        "label": "Security Tools",
        "icon": "🔒",
        "keywords": ["antivirus", "edr", "siem", "dlp", "vulnerability", "patch", "crowdstrike", "sentinelone", "palo alto", "fortinet"],
        "required": True,
        "description": "Security tools, EDR, SIEM, vulnerability management"
    },
    "identity": {
        "label": "Identity",
        "icon": "🔑",
        "keywords": ["identity", "iam", "active directory", "ad", "azure ad", "entra", "ldap", "sso", "okta", "ping"],
        "required": True,
        "description": "Identity management, SSO, directories"
    },
    "cloud": {
        "label": "Cloud Platforms",
        "icon": "☁️",
        "keywords": ["aws", "azure", "gcp", "cloud", "iaas", "paas", "saas"],
        "required": False,
        "description": "Cloud platform usage (AWS, Azure, GCP)"
    },
    "database": {
        "label": "Databases",
        "icon": "🗄️",
        "keywords": ["database", "db", "sql", "oracle", "mysql", "postgres", "mongodb", "redis", "dynamo"],
        "required": False,
        "description": "Database systems and data stores"
    }
}

STATUS_COLORS = {
    "documented": "#22c55e",    # Green
    "partial": "#eab308",       # Yellow
    "missing": "#ef4444",       # Red
    "not_required": "#6b7280"   # Gray
}


def categorize_facts(facts: List[Any]) -> Dict[str, List[Any]]:
    """
    Categorize facts by infrastructure category based on keywords.
    """
    categorized = {cat: [] for cat in INFRA_CATEGORIES}

    for fact in facts:
        # Get text to search
        if hasattr(fact, 'item'):
            text = f"{fact.item} {fact.domain} {fact.category}".lower()
        else:
            text = str(fact.get("item", "")).lower()

        # Find matching category
        for cat_id, cat_config in INFRA_CATEGORIES.items():
            for keyword in cat_config["keywords"]:
                if keyword in text:
                    categorized[cat_id].append(fact)
                    break

    return categorized


def determine_status(items: List[Any], required: bool) -> str:
    """Determine the status of a category."""
    if not required:
        if items:
            return "documented"
        return "not_required"

    if not items:
        return "missing"
    elif len(items) < 2:
        return "partial"
    return "documented"


def render_status_badge(status: str) -> str:
    """Render a status badge."""
    color = STATUS_COLORS.get(status, "#6b7280")

    labels = {
        "documented": "✅ Documented",
        "partial": "⚠️ Partial",
        "missing": "❌ Missing",
        "not_required": "➖ N/A"
    }

    label = labels.get(status, status)

    return f"""
    <span style="
        background: {color}20;
        color: {color};
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: 500;
    ">{label}</span>
    """


def render_inventory_table(categorized: Dict[str, List], gaps: List[Any]) -> None:
    """Render the main inventory table."""

    # Build table data
    table_data = []

    for cat_id, cat_config in INFRA_CATEGORIES.items():
        items = categorized.get(cat_id, [])
        status = determine_status(items, cat_config["required"])

        # Get item names
        if items:
            if hasattr(items[0], 'item'):
                item_names = [f.item for f in items[:5]]
            else:
                item_names = [str(f.get("item", "")) for f in items[:5]]
            items_str = ", ".join(item_names)
            if len(items) > 5:
                items_str += f" (+{len(items) - 5} more)"
        else:
            items_str = "—"

        # Check if there's a gap for this category
        has_gap = any(cat_id in str(g.description).lower() or
                     cat_config["label"].lower() in str(g.description).lower()
                     for g in gaps if hasattr(g, 'description'))

        table_data.append({
            "icon": cat_config["icon"],
            "category": cat_config["label"],
            "status": status,
            "count": len(items),
            "items": items_str,
            "has_gap": has_gap,
            "required": cat_config["required"]
        })

    # Display table
    st.markdown("""
    <style>
    .inventory-table {
        width: 100%;
        border-collapse: collapse;
    }
    .inventory-table th, .inventory-table td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #e5e7eb;
    }
    .inventory-table th {
        background: #f9fafb;
        font-weight: 600;
    }
    .inventory-table tr:hover {
        background: #f3f4f6;
    }
    .missing-row {
        background: #fef2f2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Convert to DataFrame for display
    df = pd.DataFrame([
        {
            "Category": f"{d['icon']} {d['category']}",
            "Status": d['status'].replace("_", " ").title(),
            "Items Found": d['count'],
            "Details": d['items'],
            "Gap Flag": "⚠️" if d['has_gap'] else ""
        }
        for d in table_data
    ])

    # Highlight missing rows
    def highlight_missing(row):
        status = row['Status'].lower()
        if status == 'missing':
            return ['background-color: #fef2f2'] * len(row)
        elif status == 'partial':
            return ['background-color: #fefce8'] * len(row)
        return [''] * len(row)

    styled_df = df.style.apply(highlight_missing, axis=1)

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Category": st.column_config.TextColumn("Category", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Items Found": st.column_config.NumberColumn("Count", width="small"),
            "Details": st.column_config.TextColumn("Items", width="large"),
            "Gap Flag": st.column_config.TextColumn("Gap", width="small")
        }
    )


def render_coverage_summary(categorized: Dict[str, List]) -> None:
    """Render coverage summary metrics."""
    total_required = sum(1 for c in INFRA_CATEGORIES.values() if c["required"])
    documented = 0
    partial = 0
    missing = 0

    for cat_id, cat_config in INFRA_CATEGORIES.items():
        if not cat_config["required"]:
            continue
        items = categorized.get(cat_id, [])
        status = determine_status(items, True)
        if status == "documented":
            documented += 1
        elif status == "partial":
            partial += 1
        else:
            missing += 1

    # Calculate coverage percentage
    coverage_pct = int((documented + partial * 0.5) / total_required * 100) if total_required > 0 else 0

    # Color based on coverage
    if coverage_pct >= 80:
        color = "#22c55e"
    elif coverage_pct >= 50:
        color = "#eab308"
    else:
        color = "#ef4444"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Coverage", f"{coverage_pct}%")
    with col2:
        st.metric("Documented", documented, delta=None)
    with col3:
        st.metric("Partial", partial, delta=None)
    with col4:
        st.metric("Missing", missing, delta=f"-{missing}" if missing > 0 else None, delta_color="inverse")

    # Progress bar
    st.markdown(f"""
    <div style="
        background: #e5e7eb;
        border-radius: 4px;
        height: 8px;
        margin: 10px 0;
        overflow: hidden;
    ">
        <div style="
            background: {color};
            width: {coverage_pct}%;
            height: 100%;
        "></div>
    </div>
    """, unsafe_allow_html=True)


def render_missing_items_alert(categorized: Dict[str, List]) -> None:
    """Render prominent alert for missing items."""
    missing_cats = []

    for cat_id, cat_config in INFRA_CATEGORIES.items():
        if not cat_config["required"]:
            continue
        items = categorized.get(cat_id, [])
        if not items:
            missing_cats.append(cat_config)

    if missing_cats:
        st.error(f"**{len(missing_cats)} Required Categories Missing Documentation**")

        cols = st.columns(min(len(missing_cats), 4))
        for i, cat in enumerate(missing_cats[:4]):
            with cols[i % 4]:
                st.markdown(f"""
                <div style="
                    background: #fee2e2;
                    border: 1px solid #fecaca;
                    border-radius: 8px;
                    padding: 12px;
                    text-align: center;
                ">
                    <div style="font-size: 1.5em;">{cat['icon']}</div>
                    <div style="font-weight: 500; color: #dc2626;">{cat['label']}</div>
                    <div style="font-size: 0.8em; color: #7f1d1d;">{cat['description']}</div>
                </div>
                """, unsafe_allow_html=True)

        if len(missing_cats) > 4:
            st.warning(f"Plus {len(missing_cats) - 4} more missing categories...")


def render_category_details(categorized: Dict[str, List]) -> None:
    """Render expandable details for each category."""
    st.markdown("### Category Details")

    for cat_id, cat_config in INFRA_CATEGORIES.items():
        items = categorized.get(cat_id, [])
        status = determine_status(items, cat_config["required"])

        icon = cat_config["icon"]
        label = cat_config["label"]
        count = len(items)

        status_emoji = {"documented": "✅", "partial": "⚠️", "missing": "❌", "not_required": "➖"}.get(status, "")

        with st.expander(f"{icon} {label} ({count} items) {status_emoji}"):
            st.markdown(f"*{cat_config['description']}*")

            if items:
                # Show items as table
                item_data = []
                for item in items[:20]:
                    if hasattr(item, 'item'):
                        item_data.append({
                            "Item": item.item,
                            "Domain": item.domain,
                            "Source": item.source_document[:30] + "..." if len(item.source_document) > 30 else item.source_document,
                            "Verified": "✅" if item.verified else "⚠️"
                        })
                    else:
                        item_data.append({
                            "Item": str(item.get("item", "")),
                            "Domain": str(item.get("domain", "")),
                            "Source": "-",
                            "Verified": "✅" if item.get("verified") else "⚠️"
                        })

                df = pd.DataFrame(item_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                if count > 20:
                    st.info(f"Showing 20 of {count} items")
            else:
                st.warning("No items documented for this category")

                # Suggest what to look for
                st.markdown(f"**Look for:** {', '.join(cat_config['keywords'][:5])}")


def render_inventory_panel_section(session_dir: Path):
    """
    Main entry point for the Infrastructure Inventory panel.
    """
    st.header("Infrastructure Inventory")

    # Load data
    fact_store = None
    reasoning_store = None
    facts = []
    gaps = []

    facts_path = session_dir / "facts.json"
    findings_path = session_dir / "findings.json"

    if facts_path.exists():
        try:
            fact_store = FactStore.load(str(facts_path))
            # Filter to infrastructure domain
            facts = [f for f in fact_store.facts if f.domain in ["infrastructure", "network", "cybersecurity"]]
        except Exception as e:
            st.warning(f"Could not load facts: {e}")

    if findings_path.exists():
        try:
            reasoning_store = ReasoningStore.load(str(findings_path))
            gaps = reasoning_store.gaps
        except Exception:
            pass

    if not facts:
        st.info("No infrastructure facts found. Run an analysis with infrastructure documents to populate this view.")

        # Show what we're looking for
        st.markdown("### What We Track")
        cols = st.columns(4)
        for i, (cat_id, cat_config) in enumerate(list(INFRA_CATEGORIES.items())[:8]):
            with cols[i % 4]:
                st.markdown(f"""
                <div style="
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 5px 0;
                    text-align: center;
                ">
                    <div style="font-size: 1.5em;">{cat_config['icon']}</div>
                    <div style="font-weight: 500;">{cat_config['label']}</div>
                </div>
                """, unsafe_allow_html=True)
        return

    # Categorize facts
    categorized = categorize_facts(facts)

    # Render sections
    st.markdown("### Coverage Summary")
    render_coverage_summary(categorized)

    st.markdown("---")

    # Alert for missing items
    render_missing_items_alert(categorized)

    st.markdown("---")

    # Main inventory table
    st.markdown("### Inventory by Category")
    render_inventory_table(categorized, gaps)

    st.markdown("---")

    # Detailed view
    render_category_details(categorized)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Infrastructure Inventory", layout="wide")
    st.title("Infrastructure Inventory Test")
    render_inventory_panel_section(Path("sessions/test"))
