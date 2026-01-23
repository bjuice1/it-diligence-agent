"""
Streamlit UI for IT Due Diligence Reasoning Analysis

Run with: streamlit run ui/streamlit_app.py
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.fact_store import FactStore
from tools_v2.reasoning_integration import (
    run_reasoning_analysis,
    compare_scenarios,
    export_to_json,
    export_to_csv,
    VALID_DEAL_TYPES,
)
from tools_v2.database import list_deals, load_fact_store

# Page config
st.set_page_config(
    page_title="IT DD Reasoning Analysis",
    page_icon="🔍",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    .big-number {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .workstream-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .activity-item {
        background: #f8f9fa;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


def load_sessions() -> list:
    """Load available deals from database."""
    try:
        deals = list_deals()
        # Convert to session-like format for compatibility
        return [
            {
                "session_id": d["id"],
                "target_name": d["target_name"],
                "deal_type": d["deal_type"],
                "created_at": d["created_at"],
                "fact_count": d.get("fact_count", 0),
            }
            for d in deals
        ]
    except Exception:
        return []


def load_facts_files() -> list:
    """Find available facts JSON files."""
    facts_files = []
    search_paths = [
        Path("data/output"),
        Path("sessions"),
        Path("outputs"),
        Path("."),
    ]
    for path in search_paths:
        if path.exists():
            facts_files.extend(path.glob("**/facts*.json"))
    return sorted(set(facts_files), key=lambda x: x.stat().st_mtime, reverse=True)[:10]


def display_workstream_card(ws: dict, expanded: bool = False):
    """Display a workstream summary card."""
    status_colors = {
        "major_change": "🔴",
        "minor_change": "🟡",
        "no_change": "🟢",
    }
    status_icon = status_colors.get(ws.get("status", ""), "⚪")

    with st.expander(f"{status_icon} {ws['name']} - ${ws['cost_range'][0]:,.0f} - ${ws['cost_range'][1]:,.0f}", expanded=expanded):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Activities", len(ws.get("activities", [])))
        with col2:
            st.metric("Timeline", f"{ws['timeline_months'][0]}-{ws['timeline_months'][1]} mo")
        with col3:
            st.metric("TSA Required", "Yes" if ws.get("requires_tsa") else "No")

        if ws.get("activities"):
            st.markdown("**Activities:**")
            for act in ws["activities"]:
                st.markdown(f"""
                <div class="activity-item">
                    <strong>{act['name']}</strong><br>
                    <small>${act['cost_low']:,.0f} - ${act['cost_high']:,.0f} | {act['timeline_months'][0]}-{act['timeline_months'][1]} months</small><br>
                    <em>Why: {act['why_needed']}</em>
                </div>
                """, unsafe_allow_html=True)


def display_tsa_table(tsa_services: list):
    """Display TSA requirements table."""
    if not tsa_services:
        st.info("No TSA services required")
        return

    st.dataframe(
        [{
            "Service": t["service"],
            "Workstream": t["workstream"],
            "Duration": f"{t['duration_months'][0]}-{t['duration_months'][1]} months",
            "Criticality": t["criticality"],
            "Why Needed": t["why_needed"][:100] + "..." if len(t.get("why_needed", "")) > 100 else t.get("why_needed", ""),
        } for t in tsa_services],
        use_container_width=True,
    )


def display_synergies(synergies: list):
    """Display synergy opportunities."""
    if not synergies:
        st.info("No synergies identified (add buyer facts for synergy analysis)")
        return

    total_low = sum(s.get("annual_savings_range", [0, 0])[0] for s in synergies)
    total_high = sum(s.get("annual_savings_range", [0, 0])[1] for s in synergies)

    st.metric("Total Annual Synergies", f"${total_low:,.0f} - ${total_high:,.0f}")

    for s in synergies:
        st.markdown(f"""
        **{s.get('category', 'Unknown').replace('_', ' ').title()}**: {s.get('description', '')}
        - Annual Savings: ${s['annual_savings_range'][0]:,.0f} - ${s['annual_savings_range'][1]:,.0f}
        - Timeline: {s.get('timeline', 'TBD')}
        """)


def main():
    st.title("🔍 IT Due Diligence Reasoning Analysis")
    st.markdown("*Analyze IT separation/integration costs with expert reasoning*")

    # Sidebar - Input Selection
    st.sidebar.header("📁 Data Source")

    source_type = st.sidebar.radio(
        "Select data source",
        ["Manual Entry", "Load Session", "Load Facts File"],
    )

    fact_store = None
    deal_type = "carveout"
    meeting_notes = ""

    if source_type == "Manual Entry":
        st.sidebar.markdown("---")
        st.sidebar.subheader("Quick Facts Entry")

        with st.sidebar.form("quick_facts"):
            user_count = st.number_input("User Count", min_value=100, max_value=100000, value=1000)
            app_count = st.number_input("Application Count", min_value=1, max_value=500, value=30)

            parent_services = st.multiselect(
                "Parent-Provided Services",
                ["Azure AD (Identity)", "Email (M365)", "Data Center", "Network (MPLS)", "Security (SOC)", "ERP"],
                default=["Azure AD (Identity)", "Email (M365)"],
            )

            submitted = st.form_submit_button("Create Facts")

            if submitted:
                fact_store = FactStore()

                # Add user count
                fact_store.add_fact(
                    "organization", "headcount", f"{user_count} employees",
                    {"count": user_count}, "documented",
                    {"exact_quote": f"{user_count} employees"}, "target"
                )

                # Add apps
                fact_store.add_fact(
                    "applications", "portfolio", f"{app_count} applications",
                    {"count": app_count}, "documented",
                    {"exact_quote": f"{app_count} applications"}, "target"
                )

                # Add parent services
                for svc in parent_services:
                    if "Azure AD" in svc:
                        fact_store.add_fact(
                            "identity_access", "directory", "Parent Azure AD",
                            {"vendor": "Microsoft"}, "documented",
                            {"exact_quote": "Identity provided by parent Azure AD"}, "target"
                        )
                    elif "Email" in svc:
                        fact_store.add_fact(
                            "applications", "email", "Parent M365",
                            {"vendor": "Microsoft"}, "documented",
                            {"exact_quote": "Email provided by parent M365"}, "target"
                        )
                    elif "Data Center" in svc:
                        fact_store.add_fact(
                            "infrastructure", "hosting", "Parent data center",
                            {}, "documented",
                            {"exact_quote": "Hosted in parent data center"}, "target"
                        )
                    elif "Network" in svc:
                        fact_store.add_fact(
                            "network", "wan", "Parent MPLS",
                            {}, "documented",
                            {"exact_quote": "Network provided by parent"}, "target"
                        )
                    elif "Security" in svc:
                        fact_store.add_fact(
                            "cybersecurity", "monitoring", "Parent SOC",
                            {}, "documented",
                            {"exact_quote": "Security monitoring by parent SOC"}, "target"
                        )
                    elif "ERP" in svc:
                        fact_store.add_fact(
                            "applications", "erp", "Shared ERP",
                            {}, "documented",
                            {"exact_quote": "Shared ERP with parent"}, "target"
                        )

                st.sidebar.success(f"Created {len(fact_store.facts)} facts")

    elif source_type == "Load Session":
        sessions = load_sessions()
        if sessions:
            # Create display options with target name and date
            session_options = {
                s["session_id"]: f"{s['target_name']} ({s['created_at'][:10]}) - {s.get('fact_count', 0)} facts"
                for s in sessions
            }
            selected = st.sidebar.selectbox(
                "Select Saved Deal",
                options=list(session_options.keys()),
                format_func=lambda x: session_options.get(x, x)
            )
            if selected and st.sidebar.button("Load Deal"):
                try:
                    fact_store = load_fact_store(selected)
                    st.sidebar.success(f"Loaded {len(fact_store.facts)} facts")
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")
        else:
            st.sidebar.info("No saved deals found")

    else:  # Load Facts File
        facts_files = load_facts_files()
        if facts_files:
            selected_file = st.sidebar.selectbox(
                "Select Facts File",
                facts_files,
                format_func=lambda x: x.name,
            )
            if selected_file and st.sidebar.button("Load File"):
                try:
                    fact_store = FactStore.load(str(selected_file))
                    st.sidebar.success(f"Loaded {len(fact_store.facts)} facts")
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")
        else:
            st.sidebar.info("No facts files found")

    # Deal Type Selection
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Analysis Settings")

    deal_type = st.sidebar.selectbox(
        "Deal Type",
        VALID_DEAL_TYPES,
        format_func=lambda x: x.replace("_", " ").title(),
    )

    meeting_notes = st.sidebar.text_area(
        "Meeting Notes / Context",
        placeholder="Add any additional context...\n\nExamples:\n- Parent wants 12-month separation\n- Buyer uses Azure\n- 45 apps with SSO",
        height=150,
    )

    compare_mode = st.sidebar.checkbox("Compare Deal Types")

    # Main Content
    if fact_store is None:
        st.info("👈 Select a data source and load facts to begin analysis")
        st.markdown("""
        ### How to Use

        1. **Manual Entry**: Quickly create facts by entering key numbers
        2. **Load Session**: Load facts from a previous analysis session
        3. **Load Facts File**: Load from a saved JSON file

        Then select your deal type and run the analysis.
        """)
        return

    # Show fact summary
    st.subheader("📊 Facts Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Facts", len(fact_store.facts))
    with col2:
        st.metric("Gaps Identified", len(fact_store.gaps))
    with col3:
        target_facts = len([f for f in fact_store.facts if getattr(f, 'entity', 'target') == 'target'])
        buyer_facts = len(fact_store.facts) - target_facts
        st.metric("Target / Buyer Facts", f"{target_facts} / {buyer_facts}")

    # Run Analysis Button
    st.markdown("---")

    if compare_mode:
        if st.button("🔄 Compare Deal Types", type="primary", use_container_width=True):
            with st.spinner("Running comparison analysis..."):
                results = compare_scenarios(
                    fact_store,
                    ["carveout", "acquisition"],
                    meeting_notes if meeting_notes else None,
                )

            st.subheader("📈 Deal Type Comparison")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Carveout")
                if "error" in results.get("carveout", {}):
                    st.error(results["carveout"]["error"])
                else:
                    summary = results["carveout"]["summary"]
                    st.metric("Total Cost", summary["total_cost"])
                    st.metric("TSA Services", summary["tsa_count"])
                    st.metric("Activities", summary["activity_count"])
                    st.metric("Critical Path", summary["critical_path"])

            with col2:
                st.markdown("### Acquisition")
                if "error" in results.get("acquisition", {}):
                    st.error(results["acquisition"]["error"])
                else:
                    summary = results["acquisition"]["summary"]
                    st.metric("Total Cost", summary["total_cost"])
                    st.metric("TSA Services", summary["tsa_count"])
                    st.metric("Activities", summary["activity_count"])
                    st.metric("Critical Path", summary["critical_path"])

    else:
        if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
            with st.spinner(f"Running {deal_type} analysis..."):
                result = run_reasoning_analysis(
                    fact_store=fact_store,
                    deal_type=deal_type,
                    meeting_notes=meeting_notes if meeting_notes else None,
                )

            # Store in session state
            st.session_state["last_result"] = result
            st.session_state["last_deal_type"] = deal_type

    # Display Results
    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        output = result["raw_output"]
        ui_result = result["ui_result"]

        st.markdown("---")
        st.subheader("📊 Analysis Results")

        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-label">Total Cost Range</div>
            <div class="big-number">${output.grand_total[0]:,.0f} - ${output.grand_total[1]:,.0f}</div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-label">TSA Services</div>
            <div class="big-number">{len(output.tsa_requirements)}</div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-label">Activities</div>
            <div class="big-number">{len(output.derived_activities)}</div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-label">Critical Path</div>
            <div class="big-number">{output.critical_path_months[0]}-{output.critical_path_months[1]} mo</div>
            """, unsafe_allow_html=True)

        # Executive Summary
        st.markdown("### 📝 Executive Summary")
        st.markdown(output.executive_summary)

        # Tabs for detailed view
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Workstreams", "TSA Requirements", "Synergies", "Full Narrative", "Export"
        ])

        with tab1:
            st.markdown("### Workstream Breakdown")
            for ws in ui_result.workstreams:
                display_workstream_card(ws)

        with tab2:
            st.markdown("### TSA Requirements")
            display_tsa_table(ui_result.tsa_services)

        with tab3:
            st.markdown("### Synergy Opportunities")
            display_synergies(result.get("synergies", []))

        with tab4:
            st.markdown("### Full Narrative")
            st.text(result["formatted_text"])

        with tab5:
            st.markdown("### Export Results")

            col1, col2 = st.columns(2)
            with col1:
                json_data = export_to_json(result)
                st.download_button(
                    "📥 Download JSON",
                    data=json_data,
                    file_name=f"reasoning_{st.session_state.get('last_deal_type', 'analysis')}.json",
                    mime="application/json",
                )

            with col2:
                csv_data = export_to_csv(result)
                st.download_button(
                    "📥 Download CSV (Cost Table)",
                    data=csv_data,
                    file_name=f"costs_{st.session_state.get('last_deal_type', 'analysis')}.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()
