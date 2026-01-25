"""
IT Due Diligence Agent - Refactored Streamlit App

Main entry point for the refactored Streamlit application.
Uses the modular component and view architecture.

Run with: streamlit run streamlit_app/main.py
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import local modules
from streamlit_app.state import SessionManager, init_session, get_session
from streamlit_app.config import (
    get_config,
    is_api_configured,
    sync_with_project_config,
)
from streamlit_app.components.styles import inject_styles
from streamlit_app.components.layout import page_header, render_stepper
from streamlit_app.views import (
    render_dashboard,
    render_risks_view,
    render_work_items_view,
    render_facts_view,
    render_gaps_view,
    render_upload_view,
    render_applications_view,
    render_infrastructure_view,
    render_open_questions_view,
    render_coverage_view,
    render_costs_view,
    render_narrative_view,
    render_staffing_view,
    render_org_chart,
    render_vendors_view,
)


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="IT Due Diligence Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# CSS STYLING
# =============================================================================

# CSS is now handled by streamlit_app.components.styles.inject_styles


# =============================================================================
# NAVIGATION
# =============================================================================

VIEWS = {
    "setup": {"label": "Setup", "icon": "📤", "section": "main"},
    "dashboard": {"label": "Dashboard", "icon": "📊", "section": "main"},
    "risks": {"label": "Risks", "icon": "⚠️", "section": "analysis"},
    "work_items": {"label": "Work Items", "icon": "📋", "section": "analysis"},
    "facts": {"label": "Facts", "icon": "📁", "section": "analysis"},
    "gaps": {"label": "Gaps", "icon": "🔍", "section": "analysis"},
    "applications": {"label": "Applications", "icon": "💻", "section": "domains"},
    "infrastructure": {"label": "Infrastructure", "icon": "🖥️", "section": "domains"},
    "organization": {"label": "Organization", "icon": "👥", "section": "domains"},
    "open_questions": {"label": "Open Questions", "icon": "❓", "section": "advanced"},
    "coverage": {"label": "Coverage", "icon": "📊", "section": "advanced"},
    "costs": {"label": "Costs", "icon": "💰", "section": "advanced"},
    "narrative": {"label": "Narrative", "icon": "📄", "section": "advanced"},
}


def render_sidebar():
    """Render sidebar navigation."""
    session = get_session()

    with st.sidebar:
        st.markdown("### IT Due Diligence")

        # Show analysis status
        if session.analysis.is_complete():
            st.success(f"✓ {session.analysis.target_name}")
            st.caption(f"{session.analysis.fact_count} facts | {session.analysis.risk_count} risks")
        elif session.analysis.is_running():
            st.info("⏳ Analysis running...")
            st.progress(session.analysis.progress_percent)
        else:
            st.caption("No analysis loaded")

        st.divider()

        current_view = st.session_state.get("current_view", "setup")
        analysis_complete = session.analysis.is_complete()

        # Group views by section
        sections = {
            "main": [],
            "analysis": [],
            "domains": [],
            "advanced": [],
        }

        for view_id, view_info in VIEWS.items():
            section = view_info.get("section", "main")
            sections[section].append((view_id, view_info))

        # Render main section (always visible)
        for view_id, view_info in sections["main"]:
            if view_id != "setup" and not analysis_complete:
                continue

            is_current = view_id == current_view
            button_type = "primary" if is_current else "secondary"

            if st.button(
                f"{view_info['icon']} {view_info['label']}",
                key=f"nav_{view_id}",
                use_container_width=True,
                type=button_type,
            ):
                st.session_state["current_view"] = view_id
                st.rerun()

        # Only show other sections if analysis is complete
        if analysis_complete:
            st.divider()
            st.markdown("##### Analysis")

            for view_id, view_info in sections["analysis"]:
                is_current = view_id == current_view
                button_type = "primary" if is_current else "secondary"

                if st.button(
                    f"{view_info['icon']} {view_info['label']}",
                    key=f"nav_{view_id}",
                    use_container_width=True,
                    type=button_type,
                ):
                    st.session_state["current_view"] = view_id
                    st.rerun()

            st.divider()
            st.markdown("##### Domains")

            for view_id, view_info in sections["domains"]:
                is_current = view_id == current_view
                button_type = "primary" if is_current else "secondary"

                if st.button(
                    f"{view_info['icon']} {view_info['label']}",
                    key=f"nav_{view_id}",
                    use_container_width=True,
                    type=button_type,
                ):
                    st.session_state["current_view"] = view_id
                    st.rerun()

            st.divider()
            st.markdown("##### Advanced")

            for view_id, view_info in sections["advanced"]:
                is_current = view_id == current_view
                button_type = "primary" if is_current else "secondary"

                if st.button(
                    f"{view_info['icon']} {view_info['label']}",
                    key=f"nav_{view_id}",
                    use_container_width=True,
                    type=button_type,
                ):
                    st.session_state["current_view"] = view_id
                    st.rerun()

        st.divider()

        # Load saved analysis
        with st.expander("📂 Load Previous"):
            _render_load_options()

        # Debug info
        if get_config().debug:
            with st.expander("🔧 Debug"):
                st.json(session.to_dict())


def _render_load_options():
    """Render options to load previous analysis."""
    # Check for saved files
    output_dir = Path("output")

    if output_dir.exists():
        facts_files = sorted(output_dir.glob("facts_*.json"), reverse=True)

        if facts_files:
            st.caption(f"Found {len(facts_files)} analysis file(s)")

            selected = st.selectbox(
                "Select analysis",
                [""] + [f.stem.replace("facts_", "") for f in facts_files[:10]],
                key="load_analysis_select",
            )

            if selected and st.button("Load", key="load_analysis_btn"):
                _load_analysis(selected)
        else:
            st.caption("No saved analyses found")
    else:
        st.caption("Output directory not found")


def _load_analysis(timestamp: str):
    """Load a previous analysis."""
    try:
        from tools_v2.fact_store import FactStore
        from tools_v2.reasoning_tools import ReasoningStore

        output_dir = Path("output")
        facts_file = output_dir / f"facts_{timestamp}.json"
        findings_file = output_dir / f"findings_{timestamp}.json"

        # Load stores
        fact_store = FactStore.load(str(facts_file))
        reasoning_store = None

        if findings_file.exists():
            reasoning_store = ReasoningStore.load(str(findings_file))

        # Update session
        session = get_session()
        session.analysis.fact_count = len(fact_store.facts)
        session.analysis.gap_count = len(fact_store.gaps)

        if reasoning_store:
            session.analysis.risk_count = len(reasoning_store.risks)
            session.analysis.work_item_count = len(reasoning_store.work_items)

        session.analysis.complete()

        # Store in session state for views
        st.session_state["fact_store"] = fact_store
        st.session_state["reasoning_store"] = reasoning_store
        st.session_state["current_view"] = "dashboard"

        st.success("Loaded!")
        st.rerun()

    except Exception as e:
        st.error(f"Error loading: {e}")


# =============================================================================
# MAIN VIEWS
# =============================================================================

def render_setup_view():
    """Render the setup/upload view."""
    page_header(
        title="IT Due Diligence Agent",
        subtitle="Upload documents to analyze",
        icon="🔍",
    )

    # Check API
    if not is_api_configured():
        st.error("API key not configured!")
        st.info("Set ANTHROPIC_API_KEY in environment or Streamlit secrets")
        return

    # Deal info
    st.markdown("### 1. Deal Information")

    col1, col2 = st.columns(2)

    with col1:
        target_name = st.text_input(
            "Target Company Name",
            value="Target Company",
            key="target_name",
        )

        deal_type = st.selectbox(
            "Deal Type",
            ["bolt_on", "carve_out"],
            format_func=lambda x: "Bolt-On (Integration)" if x == "bolt_on" else "Carve-Out (Separation)",
            key="deal_type",
        )

    with col2:
        buyer_name = st.text_input(
            "Buyer Company (optional)",
            key="buyer_name",
        )

    # Domain selection
    st.divider()
    st.markdown("### 2. Analysis Domains")

    all_domains = [
        "infrastructure", "network", "cybersecurity",
        "applications", "identity_access", "organization"
    ]

    select_all = st.checkbox("Select All", value=True, key="select_all_domains")

    if select_all:
        domains = all_domains
    else:
        domains = st.multiselect(
            "Select domains",
            all_domains,
            default=["infrastructure", "cybersecurity"],
            format_func=lambda x: x.replace("_", " ").title(),
        )

    # Documents
    st.divider()
    st.markdown("### 3. Documents")

    upload_result = render_upload_view()

    # Run button
    st.divider()
    st.markdown("### 4. Run Analysis")

    can_run = bool(target_name) and bool(domains) and upload_result.get("ready")

    if not can_run:
        if not target_name:
            st.warning("Enter target company name")
        if not domains:
            st.warning("Select at least one domain")
        if not upload_result.get("ready"):
            st.warning("Upload documents or add notes")

    if st.button(
        "🚀 Run Analysis",
        disabled=not can_run,
        type="primary",
        use_container_width=True,
    ):
        _run_analysis(
            target_name=target_name,
            deal_type=deal_type,
            buyer_name=buyer_name,
            domains=domains,
            upload_result=upload_result,
        )


def _run_analysis(target_name, deal_type, buyer_name, domains, upload_result):
    """Run the analysis pipeline."""
    import tempfile
    import shutil

    from streamlit_app.pipeline import AnalysisRunner
    from streamlit_app.storage import FileManager

    # Progress display
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(pct, msg, phase=None):
        progress_bar.progress(pct)
        status_text.text(msg)

    try:
        # Handle sample docs vs uploaded files
        if upload_result.get("use_sample"):
            from config_v2 import INPUT_DIR

            # Copy sample docs to temp dir with entity structure
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                target_dir = temp_path / "target"
                target_dir.mkdir()

                for f in INPUT_DIR.glob("*"):
                    if f.is_file():
                        shutil.copy(f, target_dir / f.name)

                # Load documents
                file_manager = FileManager(temp_path)
                file_manager._load_registry()
                document_text = file_manager.load_document_text()

                # Run analysis
                runner = AnalysisRunner(
                    target_name=target_name,
                    deal_type=deal_type,
                    buyer_name=buyer_name if buyer_name else None,
                    domains=domains,
                )

                result = runner.run(
                    document_text=document_text,
                    progress_callback=update_progress,
                )

        else:
            # Use uploaded files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                file_manager = FileManager(temp_path)

                # Save uploaded files
                for f in upload_result.get("target_files", []):
                    file_manager.save_file(f, f.name, "target")

                if upload_result.get("notes"):
                    file_manager.save_notes(upload_result["notes"], "target")

                for f in upload_result.get("buyer_files", []):
                    file_manager.save_file(f, f.name, "buyer")

                # Load documents
                document_text = file_manager.load_document_text()

                # Run analysis
                runner = AnalysisRunner(
                    target_name=target_name,
                    deal_type=deal_type,
                    buyer_name=buyer_name if buyer_name else None,
                    domains=domains,
                )

                result = runner.run(
                    document_text=document_text,
                    progress_callback=update_progress,
                )

        # Store results
        if result.is_complete():
            session = get_session()
            session.analysis.target_name = target_name
            session.analysis.deal_type = deal_type
            session.analysis.fact_count = result.fact_count
            session.analysis.gap_count = result.gap_count
            session.analysis.risk_count = result.risk_count
            session.analysis.work_item_count = result.work_item_count
            session.analysis.complete()

            st.session_state["fact_store"] = result.fact_store
            st.session_state["reasoning_store"] = result.reasoning_store
            st.session_state["analysis_result"] = result
            st.session_state["current_view"] = "dashboard"

            st.success("Analysis complete!")
            st.rerun()
        else:
            st.error("Analysis failed!")
            for error in result.errors:
                st.error(error)
            if result.traceback:
                with st.expander("Error details"):
                    st.code(result.traceback)

    except Exception as e:
        import traceback
        st.error(f"Error: {e}")
        with st.expander("Details"):
            st.code(traceback.format_exc())


def render_results_view(view_id: str):
    """Render a results view."""
    fact_store = st.session_state.get("fact_store")
    reasoning_store = st.session_state.get("reasoning_store")
    analysis_result = st.session_state.get("analysis_result")
    session = get_session()

    if view_id == "dashboard":
        render_dashboard(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            target_name=session.analysis.target_name,
        )

    elif view_id == "risks":
        render_risks_view(reasoning_store, fact_store)

    elif view_id == "work_items":
        render_work_items_view(reasoning_store, fact_store)

    elif view_id == "facts":
        render_facts_view(fact_store)

    elif view_id == "gaps":
        render_gaps_view(fact_store)

    elif view_id == "applications":
        render_applications_view(fact_store, reasoning_store)

    elif view_id == "infrastructure":
        render_infrastructure_view(fact_store, reasoning_store)

    elif view_id == "organization":
        # Show organization sub-navigation
        org_tab = st.radio(
            "Organization View",
            ["Staffing", "Org Chart", "Vendors"],
            horizontal=True,
            key="org_sub_nav",
        )

        if org_tab == "Staffing":
            render_staffing_view(fact_store, reasoning_store)
        elif org_tab == "Org Chart":
            render_org_chart(fact_store)
        else:
            render_vendors_view(fact_store, reasoning_store)

    elif view_id == "open_questions":
        render_open_questions_view(fact_store, reasoning_store)

    elif view_id == "coverage":
        render_coverage_view(fact_store)

    elif view_id == "costs":
        render_costs_view(reasoning_store)

    elif view_id == "narrative":
        # Get session directory if available
        session_dir = None
        if analysis_result and hasattr(analysis_result, "session_dir"):
            session_dir = analysis_result.session_dir

        render_narrative_view(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            session_dir=session_dir,
        )

    else:
        st.warning(f"Unknown view: {view_id}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main application entry point."""
    # Load secrets to environment
    try:
        if 'ANTHROPIC_API_KEY' in st.secrets:
            os.environ['ANTHROPIC_API_KEY'] = st.secrets['ANTHROPIC_API_KEY']
    except Exception:
        pass

    # Sync with project config
    sync_with_project_config()

    # Initialize session
    init_session()

    # Inject CSS styles
    inject_styles()

    # Render sidebar
    render_sidebar()

    # Render main view
    current_view = st.session_state.get("current_view", "setup")
    session = get_session()

    if current_view == "setup" or not session.analysis.is_complete():
        render_setup_view()
    else:
        render_results_view(current_view)


if __name__ == "__main__":
    main()
