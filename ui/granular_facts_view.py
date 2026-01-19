"""
Granular Facts View - Streamlit UI Components

This module provides Streamlit UI components for viewing and
exporting granular facts from the multi-pass extraction system.

Components:
- Granular Facts Tab: Searchable, filterable table of all line-item facts
- System Registry Tab: View all discovered systems
- Validation Dashboard: Pass/Warn/Fail status overview
- Export Panel: Excel/CSV download buttons
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import io

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tools_v2.granular_facts_store import GranularFactsStore
    from tools_v2.system_registry import SystemRegistry
    from tools_v2.validation_engine import ValidationReport, load_validation_report
    from tools_v2.excel_exporter import ExcelExporter, CSVExporter, OPENPYXL_AVAILABLE
except ImportError as e:
    st.error(f"Import error: {e}")
    OPENPYXL_AVAILABLE = False


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_granular_data(session_dir: Path) -> Dict[str, Any]:
    """Load granular extraction data from a session directory."""
    data = {
        "system_registry": None,
        "granular_facts": None,
        "validation_report": None,
        "has_data": False
    }

    session_dir = Path(session_dir)

    # Load system registry
    registry_path = session_dir / "system_registry.json"
    if registry_path.exists():
        data["system_registry"] = SystemRegistry.load(registry_path)

    # Load granular facts
    facts_path = session_dir / "granular_facts.json"
    if facts_path.exists():
        data["granular_facts"] = GranularFactsStore.load(facts_path)

    # Load validation report
    validation_path = session_dir / "validation_report.json"
    if validation_path.exists():
        data["validation_report"] = load_validation_report(validation_path)

    data["has_data"] = (
        data["system_registry"] is not None or
        data["granular_facts"] is not None
    )

    return data


def facts_to_dataframe(granular_facts_store: GranularFactsStore) -> pd.DataFrame:
    """Convert granular facts to a pandas DataFrame."""
    if not granular_facts_store or granular_facts_store.total_facts == 0:
        return pd.DataFrame()

    rows = granular_facts_store.to_rows()
    return pd.DataFrame(rows)


def systems_to_dataframe(system_registry: SystemRegistry) -> pd.DataFrame:
    """Convert system registry to a pandas DataFrame."""
    if not system_registry or system_registry.total_systems == 0:
        return pd.DataFrame()

    rows = system_registry.to_rows()
    return pd.DataFrame(rows)


# =============================================================================
# STREAMLIT COMPONENTS
# =============================================================================

def render_granular_facts_tab(session_dir: Path):
    """
    Render the Granular Facts tab content.

    Shows a searchable, filterable table of all extracted line-item facts.
    """
    st.subheader("Granular Facts Inventory")

    # Load data
    data = load_granular_data(session_dir)

    if not data["has_data"]:
        st.info(
            "No granular facts available. Run multi-pass extraction to "
            "populate this view with detailed line-item facts."
        )

        # Show how to run
        with st.expander("How to enable granular extraction"):
            st.markdown("""
            The multi-pass extraction system captures granular, line-item facts:

            **Pass 1: System Discovery**
            - Identifies all platforms, vendors, and systems

            **Pass 2: Detail Extraction**
            - Extracts counts, versions, costs, configurations
            - Links each fact to its parent system

            **Pass 3: Validation**
            - Cross-checks details against summaries
            - Flags inconsistencies

            To run: `python -c "from agents_v2.multipass_orchestrator import run_multipass_extraction; ..."`
            """)
        return

    granular_facts = data["granular_facts"]
    system_registry = data["system_registry"]

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Facts",
            granular_facts.total_facts if granular_facts else 0
        )

    with col2:
        st.metric(
            "Systems",
            system_registry.total_systems if system_registry else 0
        )

    with col3:
        domains = len(granular_facts.domains) if granular_facts else 0
        st.metric("Domains", domains)

    with col4:
        if data["validation_report"]:
            rate = data["validation_report"].pass_rate
            st.metric("Validation", f"{rate:.0%}")
        else:
            st.metric("Validation", "N/A")

    st.divider()

    # Filters
    st.markdown("**Filters**")
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        domain_options = ["All"] + (granular_facts.domains if granular_facts else [])
        selected_domain = st.selectbox("Domain", domain_options)

    with filter_col2:
        type_counts = granular_facts.count_by_type() if granular_facts else {}
        type_options = ["All"] + list(type_counts.keys())
        selected_type = st.selectbox("Fact Type", type_options)

    with filter_col3:
        search_term = st.text_input("Search", placeholder="Search items...")

    # Build filtered dataframe
    if granular_facts:
        df = facts_to_dataframe(granular_facts)

        if selected_domain != "All":
            df = df[df["Domain"] == selected_domain]

        if selected_type != "All":
            df = df[df["Type"] == selected_type]

        if search_term:
            mask = df.apply(
                lambda row: search_term.lower() in str(row).lower(),
                axis=1
            )
            df = df[mask]

        # Display count
        st.caption(f"Showing {len(df)} of {granular_facts.total_facts} facts")

        # Display table
        if not df.empty:
            st.dataframe(
                df,
                use_container_width=True,
                height=400,
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Item": st.column_config.TextColumn("Item", width="medium"),
                    "Value": st.column_config.TextColumn("Value", width="small"),
                    "Unit": st.column_config.TextColumn("Unit", width="small"),
                    "Evidence": st.column_config.TextColumn("Evidence", width="large"),
                }
            )
        else:
            st.info("No facts match your filters.")

    # Export section
    st.divider()
    render_export_panel(session_dir, data)


def render_systems_tab(session_dir: Path):
    """
    Render the Systems Registry tab content.

    Shows all systems discovered in Pass 1.
    """
    st.subheader("Systems Registry")

    data = load_granular_data(session_dir)
    system_registry = data["system_registry"]

    if not system_registry or system_registry.total_systems == 0:
        st.info("No systems discovered yet. Run Pass 1 to identify systems.")
        return

    # Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Systems", system_registry.total_systems)

    with col2:
        st.metric("Categories", len(system_registry.categories))

    with col3:
        st.metric("Vendors", len(system_registry.vendors))

    st.divider()

    # Group by category
    for category in sorted(system_registry.categories):
        systems = system_registry.get_systems_by_category(category)

        with st.expander(f"{category.replace('_', ' ').title()} ({len(systems)})"):
            for system in systems:
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**{system.name}**")
                    if system.vendor:
                        st.caption(f"Vendor: {system.vendor}")
                    if system.description:
                        st.caption(system.description)

                with col2:
                    # Criticality badge
                    crit_colors = {
                        "critical": "red",
                        "high": "orange",
                        "medium": "blue",
                        "low": "green"
                    }
                    color = crit_colors.get(system.criticality, "gray")
                    st.markdown(
                        f"<span style='background-color:{color};color:white;"
                        f"padding:2px 8px;border-radius:4px;font-size:12px'>"
                        f"{system.criticality.upper()}</span>",
                        unsafe_allow_html=True
                    )

                    # Fact count
                    if data["granular_facts"]:
                        facts = data["granular_facts"].get_facts_by_system(system.system_id)
                        st.caption(f"{len(facts)} facts")

                st.markdown("---")


def render_validation_tab(session_dir: Path):
    """
    Render the Validation Dashboard tab.

    Shows Pass 3 validation results with pass/warn/fail status.
    """
    st.subheader("Validation Dashboard")

    data = load_granular_data(session_dir)
    validation_report = data["validation_report"]

    if not validation_report:
        st.info("No validation results available. Run Pass 3 to validate extraction.")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Pass Rate",
            f"{validation_report.pass_rate:.1%}",
            delta="Valid" if validation_report.is_valid else "Issues Found"
        )

    with col2:
        st.metric("Passed", validation_report.pass_count)

    with col3:
        st.metric("Warnings", validation_report.warn_count)

    with col4:
        st.metric("Failures", validation_report.fail_count)

    st.divider()

    # Failures section
    failures = validation_report.get_failures()
    if failures:
        st.markdown("### Failures")
        for result in failures:
            with st.container():
                st.error(f"**{result.check_type}**: {result.message}")
                if result.suggested_action:
                    st.caption(f"Action: {result.suggested_action}")

    # Warnings section
    warnings = validation_report.get_warnings()
    if warnings:
        st.markdown("### Warnings")
        for result in warnings[:10]:  # Limit display
            with st.container():
                st.warning(f"**{result.check_type}**: {result.message}")

        if len(warnings) > 10:
            st.caption(f"... and {len(warnings) - 10} more warnings")

    # Passes section
    if validation_report.pass_count > 0:
        with st.expander(f"Passed Checks ({validation_report.pass_count})"):
            passes = [r for r in validation_report.results if r.status == "pass"]
            for result in passes[:20]:
                st.success(f"{result.check_type}: {result.message}")


def render_export_panel(session_dir: Path, data: Dict[str, Any] = None):
    """
    Render the export panel with download buttons.
    """
    st.markdown("### Export Data")

    if data is None:
        data = load_granular_data(session_dir)

    if not data["has_data"]:
        st.info("No data available to export.")
        return

    col1, col2, col3 = st.columns(3)

    granular_facts = data["granular_facts"]
    system_registry = data["system_registry"]
    validation_report = data["validation_report"]

    # CSV Export
    with col1:
        if granular_facts and granular_facts.total_facts > 0:
            csv_data = granular_facts.to_json()
            st.download_button(
                label="Download JSON",
                data=csv_data,
                file_name="granular_facts.json",
                mime="application/json"
            )

    # CSV Facts
    with col2:
        if granular_facts and granular_facts.total_facts > 0:
            df = facts_to_dataframe(granular_facts)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download CSV",
                data=csv_buffer.getvalue(),
                file_name="granular_facts.csv",
                mime="text/csv"
            )

    # Excel Export
    with col3:
        if OPENPYXL_AVAILABLE and granular_facts:
            if st.button("Generate Excel"):
                try:
                    # Create Excel in memory
                    output_path = session_dir / "exports" / "full_inventory.xlsx"
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    exporter = ExcelExporter()
                    exporter.create_full_workbook(
                        system_registry or SystemRegistry(),
                        granular_facts,
                        validation_report or ValidationReport(),
                        output_path
                    )

                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Download Excel",
                            data=f.read(),
                            file_name="full_inventory.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    st.success("Excel file generated!")

                except Exception as e:
                    st.error(f"Error generating Excel: {e}")
        else:
            st.caption("Excel export requires openpyxl")


def render_granular_facts_section(session_dir: Path):
    """
    Main entry point for rendering the granular facts section.

    Creates tabs for Facts, Systems, and Validation.
    """
    tab1, tab2, tab3 = st.tabs([
        "Granular Facts",
        "Systems Registry",
        "Validation"
    ])

    with tab1:
        render_granular_facts_tab(session_dir)

    with tab2:
        render_systems_tab(session_dir)

    with tab3:
        render_validation_tab(session_dir)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Granular Facts Viewer", layout="wide")
    st.title("Granular Facts Viewer")

    # Test with a session directory
    session_dir = st.text_input(
        "Session Directory",
        value="sessions/test_session"
    )

    if session_dir:
        render_granular_facts_section(Path(session_dir))
