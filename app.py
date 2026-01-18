"""
IT Due Diligence Agent - Streamlit UI

A simple web interface for running IT due diligence analysis.

Run with: streamlit run app.py
Then open: http://localhost:8501
"""

import streamlit as st
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set page config first (must be first Streamlit command)
st.set_page_config(
    page_title="IT Due Diligence Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# MODERN UI STYLING
# =============================================================================
def inject_custom_css():
    """Inject modern CSS styling for the app."""
    st.markdown("""
    <style>
    /* === Design Tokens === */
    :root {
        --accent: #f97316;
        --accent-hover: #ea580c;
        --bg-base: #fafaf9;
        --bg-surface: #ffffff;
        --bg-surface-hover: #f5f5f4;
        --bg-surface-sunken: #f5f5f4;
        --text-primary: #1c1917;
        --text-secondary: #57534e;
        --text-muted: #a8a29e;
        --border-default: #e7e5e4;
        --border-muted: #d6d3d1;
        --critical: #dc2626;
        --high: #f97316;
        --medium: #eab308;
        --low: #22c55e;
        --radius-md: 8px;
        --radius-lg: 12px;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);
    }

    /* === Stepper Sidebar === */
    .stepper-container {
        padding: 1rem 0;
    }

    .stepper-item {
        display: flex;
        align-items: flex-start;
        padding: 0.75rem 1rem;
        margin-bottom: 0.25rem;
        border-radius: var(--radius-md);
        cursor: pointer;
        transition: all 0.15s ease;
    }

    .stepper-item:hover {
        background: var(--bg-surface-hover);
    }

    .stepper-item.active {
        background: var(--bg-surface);
        border: 2px solid var(--accent);
    }

    .stepper-item.completed {
        background: #fef3e8;
    }

    .step-number {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: var(--border-default);
        color: var(--text-muted);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 0.75rem;
        flex-shrink: 0;
    }

    .stepper-item.active .step-number {
        background: var(--accent);
        color: white;
    }

    .stepper-item.completed .step-number {
        background: var(--low);
        color: white;
    }

    .step-content {
        flex: 1;
    }

    .step-title {
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--text-primary);
        margin-bottom: 0.125rem;
    }

    .step-subtitle {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .stepper-item.active .step-title {
        color: var(--accent);
    }

    /* === Cards === */
    .upload-card {
        background: var(--bg-surface);
        border: 2px solid var(--border-default);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .upload-card.primary {
        border-color: var(--accent);
        box-shadow: var(--shadow-md);
    }

    .upload-card.secondary {
        border-style: dashed;
        background: var(--bg-surface-sunken);
    }

    .card-title {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        color: var(--text-primary);
    }

    .card-subtitle {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-bottom: 1rem;
    }

    /* === Metric Cards === */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        flex: 1;
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-lg);
        padding: 1.25rem;
        text-align: center;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
    }

    .metric-label {
        font-size: 0.8rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* === Run Button === */
    .run-button-container {
        margin-top: 2rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%);
        border-radius: var(--radius-lg);
        border: 2px solid var(--accent);
        text-align: center;
    }

    .stButton > button[kind="primary"] {
        background-color: var(--accent) !important;
        border-color: var(--accent) !important;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 0.75rem 2rem;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: var(--accent-hover) !important;
        border-color: var(--accent-hover) !important;
    }

    /* === Badges === */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .badge-critical { background: #fecaca; color: #991b1b; }
    .badge-high { background: #ffedd5; color: #c2410c; }
    .badge-medium { background: #fef3c7; color: #a16207; }
    .badge-low { background: #dcfce7; color: #166534; }

    /* === Progress Steps Summary === */
    .step-summary {
        background: var(--bg-surface-sunken);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin-top: 1rem;
    }

    .step-summary-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--border-muted);
    }

    .step-summary-item:last-child {
        border-bottom: none;
    }

    /* === Hide Streamlit Defaults === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* === Better File Uploader === */
    .stFileUploader > div > div {
        border-radius: var(--radius-lg);
    }

    /* === Divider === */
    hr {
        border: none;
        border-top: 1px solid var(--border-default);
        margin: 1.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Import project modules
try:
    from config_v2 import ANTHROPIC_API_KEY, OUTPUT_DIR, FACTS_DIR, FINDINGS_DIR
    from tools_v2.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore
    from tools_v2.session import DDSession, DealType, DEAL_TYPE_CONFIG
    from tools_v2.database import (
        init_database, create_deal, get_deal, list_deals, delete_deal,
        save_deal_complete, load_fact_store, load_reasoning_store, get_deal_summary
    )
    CONFIG_LOADED = True
except ImportError as e:
    CONFIG_LOADED = False
    IMPORT_ERROR = str(e)


def check_api_key() -> bool:
    """Check if API key is configured."""
    if not CONFIG_LOADED:
        return False
    return bool(ANTHROPIC_API_KEY)


def save_uploaded_files(uploaded_files, target_dir: Path, entity: str = "target") -> list:
    """Save uploaded files to target directory with entity subdirectory."""
    saved_files = []
    entity_dir = target_dir / entity
    entity_dir.mkdir(parents=True, exist_ok=True)

    for uploaded_file in uploaded_files:
        file_path = entity_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_files.append(file_path)

    return saved_files


def save_notes_as_file(notes_text: str, target_dir: Path, entity: str = "target") -> Optional[Path]:
    """Save notes text as a file for processing."""
    if not notes_text or not notes_text.strip():
        return None

    entity_dir = target_dir / entity
    entity_dir.mkdir(parents=True, exist_ok=True)

    # Create a text file with the notes
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    notes_file = entity_dir / f"meeting_notes_{timestamp}.txt"

    with open(notes_file, "w") as f:
        f.write("# Meeting Notes / Discussion Points\n\n")
        f.write(notes_text)

    return notes_file


def load_documents_with_entity(input_dir: Path) -> str:
    """
    Load documents from entity subdirectories with clear entity markers.

    Expects structure:
        input_dir/
        ├── target/  (required)
        │   ├── doc1.pdf
        │   └── notes.txt
        └── buyer/   (optional)
            └── buyer_doc.pdf
    """
    from ingestion.pdf_parser import PDFParser

    combined_text = []
    parser = PDFParser()

    # Load TARGET documents (required)
    target_dir = input_dir / "target"
    if target_dir.exists():
        combined_text.append("=" * 80)
        combined_text.append("# ENTITY: TARGET")
        combined_text.append("# All documents below describe the TARGET company (being evaluated)")
        combined_text.append("=" * 80 + "\n")

        # Parse PDFs
        for pdf_file in target_dir.glob("*.pdf"):
            try:
                parsed = parser.parse_file(pdf_file)
                combined_text.append(f"\n# Document: {pdf_file.name}")
                combined_text.append(f"# Entity: TARGET")
                combined_text.append(parsed.raw_text)
                combined_text.append("\n" + "-" * 40 + "\n")
            except Exception as e:
                print(f"Error parsing {pdf_file.name}: {e}")

        # Parse text files (notes, etc.)
        for txt_file in list(target_dir.glob("*.txt")) + list(target_dir.glob("*.md")):
            try:
                with open(txt_file, "r", encoding='utf-8') as f:
                    content = f.read()
                combined_text.append(f"\n# Document: {txt_file.name}")
                combined_text.append(f"# Entity: TARGET")
                combined_text.append(content)
                combined_text.append("\n" + "-" * 40 + "\n")
            except Exception as e:
                print(f"Error reading {txt_file.name}: {e}")

    # Load BUYER documents (optional)
    buyer_dir = input_dir / "buyer"
    if buyer_dir.exists() and any(buyer_dir.iterdir()):
        combined_text.append("\n" + "=" * 80)
        combined_text.append("# ENTITY: BUYER")
        combined_text.append("# All documents below describe the BUYER company (for integration context)")
        combined_text.append("=" * 80 + "\n")

        # Parse PDFs
        for pdf_file in buyer_dir.glob("*.pdf"):
            try:
                parsed = parser.parse_file(pdf_file)
                combined_text.append(f"\n# Document: {pdf_file.name}")
                combined_text.append(f"# Entity: BUYER")
                combined_text.append(parsed.raw_text)
                combined_text.append("\n" + "-" * 40 + "\n")
            except Exception as e:
                print(f"Error parsing {pdf_file.name}: {e}")

        # Parse text files
        for txt_file in list(buyer_dir.glob("*.txt")) + list(buyer_dir.glob("*.md")):
            try:
                with open(txt_file, "r", encoding='utf-8') as f:
                    content = f.read()
                combined_text.append(f"\n# Document: {txt_file.name}")
                combined_text.append(f"# Entity: BUYER")
                combined_text.append(content)
                combined_text.append("\n" + "-" * 40 + "\n")
            except Exception as e:
                print(f"Error reading {txt_file.name}: {e}")

    return "\n".join(combined_text)


def run_analysis(
    input_dir: Path,
    target_name: str,
    deal_type: str,
    buyer_name: Optional[str],
    domains: list,
    progress_callback=None
) -> Dict[str, Any]:
    """Run the analysis pipeline."""
    from main_v2 import (
        run_parallel_discovery,
        run_parallel_reasoning,
        merge_reasoning_stores,
        run_coverage_analysis,
        run_vdr_generation,
        run_synthesis,
    )
    from tools_v2.session import DealContext
    from tools_v2.html_report import generate_html_report
    from tools_v2.presentation import generate_presentation

    results = {
        "status": "running",
        "facts": None,
        "findings": None,
        "coverage": None,
        "vdr": None,
        "errors": []
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # Phase 1: Load documents with entity markers
        if progress_callback:
            progress_callback(0.1, "Loading documents...")

        document_text = load_documents_with_entity(input_dir)
        results["doc_length"] = len(document_text)

        # Phase 2: Discovery
        if progress_callback:
            progress_callback(0.2, "Running discovery (extracting facts)...")

        fact_store = run_parallel_discovery(
            document_text=document_text,
            domains=domains,
            max_workers=3,
            target_name=target_name
        )
        results["facts"] = {
            "count": len(fact_store.facts),
            "gaps": len(fact_store.gaps),
            "by_domain": {d: len([f for f in fact_store.facts if f.domain == d]) for d in domains}
        }

        # Save facts
        facts_file = FACTS_DIR / f"facts_{timestamp}.json"
        fact_store.save(str(facts_file))
        results["facts_file"] = str(facts_file)

        # Phase 3: Reasoning
        if progress_callback:
            progress_callback(0.5, "Running reasoning (analyzing facts)...")

        # Build deal context
        deal_context = {
            "target_name": target_name,
            "deal_type": deal_type,
            "buyer_name": buyer_name
        }

        # Create DealContext for formatted prompt
        dc = DealContext(
            target_name=target_name,
            deal_type=deal_type,
            buyer_name=buyer_name
        )
        deal_context["_prompt_context"] = dc.to_prompt_context()

        reasoning_results = run_parallel_reasoning(
            fact_store=fact_store,
            domains=domains,
            deal_context=deal_context,
            max_workers=3
        )

        # Merge reasoning stores
        merged_store = merge_reasoning_stores(fact_store, reasoning_results)
        results["findings"] = {
            "risks": len(merged_store.risks),
            "work_items": len(merged_store.work_items),
            "recommendations": len(merged_store.recommendations),
            "strategic": len(merged_store.strategic_considerations)
        }

        # Save findings
        findings_file = FINDINGS_DIR / f"findings_{timestamp}.json"
        merged_store.save(str(findings_file))
        results["findings_file"] = str(findings_file)

        # Phase 4: Coverage Analysis (SKIPPED - matching logic needs improvement)
        if progress_callback:
            progress_callback(0.7, "Skipping coverage analysis...")

        results["coverage"] = {
            "overall_percent": 0,
            "grade": "N/A"
        }

        # Phase 5: VDR Generation
        if progress_callback:
            progress_callback(0.85, "Generating VDR requests...")

        vdr_results = run_vdr_generation(fact_store, merged_store)
        results["vdr"] = {
            "total": vdr_results.get("vdr_pack", {}).get("total_requests", 0),
            "critical": vdr_results.get("vdr_pack", {}).get("by_priority", {}).get("critical", 0)
        }

        # Save VDR
        vdr_file = OUTPUT_DIR / f"vdr_requests_{timestamp}.json"
        with open(vdr_file, "w") as f:
            json.dump(vdr_results, f, indent=2)
        results["vdr_file"] = str(vdr_file)

        # Phase 6: Generate HTML Report
        if progress_callback:
            progress_callback(0.90, "Generating HTML report...")

        html_report_file = generate_html_report(
            fact_store=fact_store,
            reasoning_store=merged_store,
            output_dir=OUTPUT_DIR,
            timestamp=timestamp,
            target_name=target_name
        )
        results["html_report_file"] = str(html_report_file)

        # Phase 7: Generate Investment Thesis
        if progress_callback:
            progress_callback(0.95, "Generating investment thesis...")

        presentation_file = generate_presentation(
            fact_store=fact_store,
            reasoning_store=merged_store,
            output_dir=OUTPUT_DIR,
            target_name=target_name,
            timestamp=timestamp
        )
        results["presentation_file"] = str(presentation_file)

        if progress_callback:
            progress_callback(1.0, "Analysis complete!")

        results["status"] = "complete"
        results["timestamp"] = timestamp

        # Store for display
        results["fact_store"] = fact_store
        results["reasoning_store"] = merged_store

    except Exception as e:
        results["status"] = "error"
        results["errors"].append(str(e))
        import traceback
        results["traceback"] = traceback.format_exc()

    return results


def save_deal_to_database(
    target_name: str,
    deal_type: str,
    buyer_name: Optional[str],
    fact_store: FactStore,
    reasoning_store: ReasoningStore
) -> str:
    """Save a completed deal to the database."""
    # Create deal name from target and timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    deal_name = f"{target_name} - {timestamp}"

    # Create the deal record
    deal_id = create_deal(
        name=deal_name,
        target_name=target_name,
        deal_type=deal_type,
        buyer_name=buyer_name
    )

    # Save fact store and reasoning store
    save_deal_complete(deal_id, fact_store, reasoning_store)

    return deal_id


def format_cost_range(low: int, high: int) -> str:
    """Format cost range for display."""
    def format_val(v):
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        elif v >= 1_000:
            return f"${v/1_000:.0f}K"
        else:
            return f"${v:,.0f}"

    if low == 0 and high == 0:
        return "TBD"
    return f"{format_val(low)} - {format_val(high)}"


def display_results(results: Dict[str, Any]):
    """Display analysis results."""

    if results["status"] == "error":
        st.error("Analysis failed!")
        for error in results.get("errors", []):
            st.error(error)
        if "traceback" in results:
            with st.expander("Error Details"):
                st.code(results["traceback"])
        return

    # Summary metrics
    st.subheader("📊 Analysis Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Facts Extracted", results["facts"]["count"])
        st.caption(f"Gaps: {results['facts']['gaps']}")

    with col2:
        st.metric("Risks Identified", results["findings"]["risks"])
        st.caption(f"Work Items: {results['findings']['work_items']}")

    with col3:
        st.metric("VDR Requests", results["vdr"]["total"])
        st.caption(f"Critical: {results['vdr']['critical']}")

    # Facts by domain
    st.subheader("📁 Facts by Domain")
    facts_by_domain = results["facts"]["by_domain"]
    cols = st.columns(len(facts_by_domain))
    for i, (domain, count) in enumerate(facts_by_domain.items()):
        with cols[i]:
            st.metric(domain.replace("_", " ").title(), count)

    # Detailed findings
    if "fact_store" in results and "reasoning_store" in results:
        fact_store = results["fact_store"]
        reasoning_store = results["reasoning_store"]

        st.subheader("🔍 Detailed Findings")

        tab1, tab2, tab3, tab4 = st.tabs(["Risks", "Work Items", "Recommendations", "Facts"])

        with tab1:
            if reasoning_store.risks:
                for risk in reasoning_store.risks:
                    severity_color = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(risk.severity, "⚪")

                    with st.expander(f"{severity_color} {risk.title} ({risk.severity.upper()})"):
                        st.write(risk.description)
                        st.write(f"**Mitigation:** {risk.mitigation}")
                        st.write(f"**Based on:** {', '.join(risk.based_on_facts)}")
            else:
                st.info("No risks identified")

        with tab2:
            if reasoning_store.work_items:
                # Group by phase
                for phase in ["Day_1", "Day_100", "Post_100"]:
                    phase_items = [wi for wi in reasoning_store.work_items if wi.phase == phase]
                    if phase_items:
                        st.write(f"**{phase.replace('_', ' ')}** ({len(phase_items)} items)")
                        for wi in phase_items:
                            with st.expander(f"{wi.title} - {wi.cost_estimate}"):
                                st.write(wi.description)
                                st.write(f"**Owner:** {wi.owner_type}")
                                st.write(f"**Priority:** {wi.priority}")
            else:
                st.info("No work items identified")

        with tab3:
            if reasoning_store.recommendations:
                for rec in reasoning_store.recommendations:
                    with st.expander(f"📋 {rec.title}"):
                        st.write(rec.description)
                        st.write(f"**Action:** {rec.action_type}")
                        st.write(f"**Urgency:** {rec.urgency}")
            else:
                st.info("No recommendations")

        with tab4:
            # Import fact synthesis function
            from tools_v2.html_report import _synthesize_fact_statement

            # Group facts by domain
            facts_by_domain = {}
            for fact in fact_store.facts:
                if fact.domain not in facts_by_domain:
                    facts_by_domain[fact.domain] = []
                facts_by_domain[fact.domain].append(fact)

            st.write(f"**{len(fact_store.facts)} facts** across {len(facts_by_domain)} domains")

            for domain, domain_facts in facts_by_domain.items():
                with st.expander(f"📁 {domain.replace('_', ' ').title()} ({len(domain_facts)} facts)"):
                    for fact in domain_facts:
                        # Use synthesized fact statement
                        fact_statement = _synthesize_fact_statement(fact)
                        entity_badge = "🎯" if fact.entity == "target" else "🏢"

                        st.markdown(f"**{fact.fact_id}** {entity_badge}")
                        st.markdown(f"> {fact_statement}")

                        if fact.evidence.get("exact_quote"):
                            st.caption(f"📄 Source: \"{fact.evidence['exact_quote'][:150]}...\"")
                        st.divider()

    # Output files with download buttons
    st.subheader("📄 Output Files")

    output_config = [
        ("html_report_file", "📊 HTML Report", "text/html"),
        ("presentation_file", "📈 Investment Thesis", "text/html"),
        ("vdr_file", "📋 VDR Requests", "application/json"),
        ("facts_file", "📁 Facts (JSON)", "application/json"),
        ("findings_file", "🔍 Findings (JSON)", "application/json"),
    ]

    # Create columns for download buttons
    col1, col2 = st.columns(2)

    for idx, (key, label, mime_type) in enumerate(output_config):
        if key in results and results[key]:
            file_path = results[key]
            try:
                with open(file_path, "r") as f:
                    file_content = f.read()
                filename = Path(file_path).name

                # Alternate between columns
                with col1 if idx % 2 == 0 else col2:
                    st.download_button(
                        label=f"⬇️ {label}",
                        data=file_content,
                        file_name=filename,
                        mime=mime_type,
                        use_container_width=True
                    )
            except Exception as e:
                st.warning(f"Could not load {label}: {e}")


# =============================================================================
# STEPPER SIDEBAR COMPONENT (Visual indicator only)
# =============================================================================

def render_stepper(step_statuses: dict):
    """Render the stepper sidebar as a visual progress indicator."""
    steps = [
        {"num": 1, "title": "Deal Info", "subtitle": "Target & deal type"},
        {"num": 2, "title": "Domains", "subtitle": "Analysis scope"},
        {"num": 3, "title": "Documents", "subtitle": "Upload & notes"},
        {"num": 4, "title": "Run", "subtitle": "Start analysis"},
    ]

    st.markdown('<div class="stepper-container">', unsafe_allow_html=True)

    for step in steps:
        step_num = step["num"]
        is_completed = step_statuses.get(step_num, False)

        # Determine CSS class
        css_class = "stepper-item"
        if is_completed:
            css_class += " completed"

        # Step number or checkmark
        number_display = "✓" if is_completed else str(step_num)

        st.markdown(f'''
        <div class="{css_class}">
            <div class="step-number">{number_display}</div>
            <div class="step-content">
                <div class="step-title">{step["title"]}</div>
                <div class="step-subtitle">{step["subtitle"]}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# MAIN APP - Single page layout
# =============================================================================

def main():
    # Inject custom CSS
    inject_custom_css()

    # Check configuration
    if not CONFIG_LOADED:
        st.error(f"Configuration error: {IMPORT_ERROR}")
        st.info("Make sure you're running from the project directory and dependencies are installed.")
        return

    if not check_api_key():
        st.error("API key not configured!")
        st.info("Set ANTHROPIC_API_KEY in your environment or .env file")
        return

    # Default values
    all_domains = ["infrastructure", "network", "cybersecurity", "applications", "identity_access", "organization"]

    # ==========================================================================
    # SIDEBAR - Progress indicator + Saved Deals
    # ==========================================================================
    with st.sidebar:
        st.markdown("### IT Due Diligence")
        st.caption("Analysis Workflow")

        st.divider()

        # Calculate step completion dynamically (will update as user fills in)
        step_statuses = {1: False, 2: False, 3: False, 4: False}

        # Render stepper (updated after main content renders)
        stepper_placeholder = st.empty()

        st.divider()

        # Saved Deals Section
        with st.expander("📂 Saved Deals", expanded=False):
            saved_deals = list_deals()

            if saved_deals:
                deal_options = {d["id"]: f"{d['target_name']} ({d['created_at'][:10]})" for d in saved_deals}
                deal_options[""] = "-- Select --"

                selected_deal_id = st.selectbox(
                    "Load Previous",
                    options=[""] + list(deal_options.keys())[:-1],
                    format_func=lambda x: deal_options.get(x, x),
                    key="deal_selector",
                    label_visibility="collapsed"
                )

                if selected_deal_id:
                    deal_summary = get_deal_summary(selected_deal_id)
                    if deal_summary:
                        st.caption(f"**{deal_summary['target_name']}**")
                        st.caption(f"Facts: {deal_summary['fact_count']} | Risks: {deal_summary['risk_count']}")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Load", key="load_deal_btn", use_container_width=True):
                                fact_store = load_fact_store(selected_deal_id)
                                reasoning_store = load_reasoning_store(selected_deal_id)
                                domains = list(deal_summary.get('facts_by_domain', {}).keys())
                                st.session_state["results"] = {
                                    "status": "complete",
                                    "facts": {
                                        "count": len(fact_store.facts),
                                        "gaps": len(fact_store.gaps),
                                        "by_domain": {d: len([f for f in fact_store.facts if f.domain == d]) for d in domains}
                                    },
                                    "findings": {
                                        "risks": len(reasoning_store.risks),
                                        "work_items": len(reasoning_store.work_items),
                                        "recommendations": len(reasoning_store.recommendations),
                                        "strategic": len(reasoning_store.strategic_considerations)
                                    },
                                    "coverage": {"overall_percent": 0, "grade": "N/A"},
                                    "vdr": {"total": 0, "critical": 0},
                                    "fact_store": fact_store,
                                    "reasoning_store": reasoning_store,
                                    "loaded_deal_id": selected_deal_id,
                                    "loaded_deal_name": deal_summary['name']
                                }
                                st.session_state["analysis_complete"] = True
                                st.rerun()

                        with col2:
                            if st.button("Delete", key="delete_deal_btn", use_container_width=True):
                                delete_deal(selected_deal_id)
                                st.success("Deleted")
                                st.rerun()
            else:
                st.caption("No saved deals")

    # ==========================================================================
    # MAIN CONTENT - Single page with all sections
    # ==========================================================================

    # Header
    st.title("IT Due Diligence Agent")

    # Check if we have results to display
    if st.session_state.get("analysis_complete"):
        st.markdown("### Analysis Results")
        display_results(st.session_state["results"])

        # Option to start new analysis
        if st.button("← Start New Analysis", type="primary"):
            st.session_state["analysis_complete"] = False
            st.rerun()
    else:
        # --------------------------------------------------------------------------
        # SECTION 1: Deal Information
        # --------------------------------------------------------------------------
        st.markdown("### 1. Deal Information")

        col1, col2 = st.columns(2)

        with col1:
            target_name = st.text_input(
                "Target Company Name",
                value="Target Company",
                key="target_name",
                help="The company being evaluated for acquisition"
            )

            deal_type = st.selectbox(
                "Deal Type",
                options=["bolt_on", "carve_out"],
                format_func=lambda x: {
                    "bolt_on": "Bolt-On (Integration)",
                    "carve_out": "Carve-Out (Separation)"
                }.get(x, x),
                key="deal_type"
            )
            deal_config = DEAL_TYPE_CONFIG.get(DealType(deal_type), {})
            st.caption(deal_config.get("description", ""))

        with col2:
            buyer_name = st.text_input(
                "Buyer Company Name (optional)",
                value="",
                key="buyer_name",
                help="For integration context - leave blank if not applicable"
            )

        # Update step status
        step_statuses[1] = bool(target_name and target_name.strip())

        st.divider()

        # --------------------------------------------------------------------------
        # SECTION 2: Domain Selection
        # --------------------------------------------------------------------------
        st.markdown("### 2. Analysis Domains")

        select_all = st.checkbox("Select All Domains", value=True, key="select_all_domains")

        if select_all:
            selected_domains = all_domains.copy()
        else:
            selected_domains = st.multiselect(
                "Select Domains",
                options=all_domains,
                default=["infrastructure", "cybersecurity"],
                format_func=lambda x: x.replace("_", " ").title(),
                key="domain_multiselect"
            )

        # Show selected as chips
        if selected_domains:
            domain_chips = " ".join([f"`{d.replace('_', ' ').title()}`" for d in selected_domains])
            st.caption(f"Selected: {domain_chips}")

        # Update step status
        step_statuses[2] = bool(selected_domains)

        st.divider()

        # --------------------------------------------------------------------------
        # SECTION 3: Document Upload
        # --------------------------------------------------------------------------
        st.markdown("### 3. Documents")

        # PRIMARY: Target Documents
        st.markdown("**Target Company Documents**")
        target_files = st.file_uploader(
            "Upload IT profiles, assessments, security audits",
            type=["pdf", "txt", "md"],
            accept_multiple_files=True,
            key="target_upload"
        )

        if target_files:
            st.success(f"✓ {len(target_files)} document(s) ready")

        # SECONDARY: Notes
        st.markdown("**Quick Notes** (optional)")
        target_notes = st.text_area(
            "Paste meeting notes or discussion points",
            height=100,
            placeholder="From call with CTO:\n- VMware upgrade planned for Q2\n- Security team hiring 2 more",
            key="target_notes",
            label_visibility="collapsed"
        )

        # OPTIONAL: Buyer Documents
        with st.expander("Buyer / Integration Context (optional)"):
            buyer_files = st.file_uploader(
                "Buyer documents",
                type=["pdf", "txt", "md"],
                accept_multiple_files=True,
                key="buyer_upload"
            )
            if buyer_files:
                st.info(f"📋 {len(buyer_files)} buyer document(s) ready")

        # Update step status
        has_docs = bool(target_files)
        has_notes = bool(target_notes and target_notes.strip())
        step_statuses[3] = has_docs or has_notes

        st.divider()

        # --------------------------------------------------------------------------
        # SECTION 4: Run Analysis
        # --------------------------------------------------------------------------
        st.markdown("### 4. Run Analysis")

        # Validation
        can_run = True
        issues = []

        if not (has_docs or has_notes):
            can_run = False
            issues.append("Upload documents or add notes")

        if not target_name or not target_name.strip():
            can_run = False
            issues.append("Enter target company name")

        if not selected_domains:
            can_run = False
            issues.append("Select at least one domain")

        if issues:
            for issue in issues:
                st.warning(f"⚠️ {issue}")

        # Run button
        run_button = st.button(
            "🚀 Run Analysis",
            disabled=not can_run,
            type="primary",
            use_container_width=True,
            key="run_analysis_btn"
        )

        if can_run:
            st.caption("Analysis typically takes 2-5 minutes")

        # Update step status
        step_statuses[4] = st.session_state.get("analysis_complete", False)

        # Update stepper in sidebar
        with stepper_placeholder:
            render_stepper(step_statuses)

        # Run analysis
        if run_button and can_run:
            st.divider()

            # Create temp directory for uploaded files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Save uploaded files
                with st.spinner("Preparing documents..."):
                    saved_files = []

                    if target_files:
                        saved_files.extend(save_uploaded_files(target_files, temp_path, entity="target"))

                    if target_notes and target_notes.strip():
                        notes_file = save_notes_as_file(target_notes, temp_path, entity="target")
                        if notes_file:
                            saved_files.append(notes_file)

                    if buyer_files:
                        saved_files.extend(save_uploaded_files(buyer_files, temp_path, entity="buyer"))

                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(pct, msg):
                    progress_bar.progress(pct)
                    status_text.text(msg)

                # Run analysis
                with st.spinner("Running analysis..."):
                    results = run_analysis(
                        input_dir=temp_path,
                        target_name=target_name,
                        deal_type=deal_type,
                        buyer_name=buyer_name if buyer_name else None,
                        domains=selected_domains,
                        progress_callback=update_progress
                    )

                # Store results
                st.session_state["results"] = results
                st.session_state["analysis_complete"] = True

                # Auto-save deal
                if results["status"] == "complete" and "fact_store" in results and "reasoning_store" in results:
                    try:
                        deal_id = save_deal_to_database(
                            target_name=target_name,
                            deal_type=deal_type,
                            buyer_name=buyer_name if buyer_name else None,
                            fact_store=results["fact_store"],
                            reasoning_store=results["reasoning_store"]
                        )
                        st.session_state["saved_deal_id"] = deal_id
                        st.success("✅ Deal saved automatically")
                    except Exception as e:
                        st.warning(f"Could not save deal: {e}")

                st.rerun()


if __name__ == "__main__":
    main()
