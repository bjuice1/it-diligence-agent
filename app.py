"""
IT Due Diligence Streamlit App
Exact replication of Flask localhost:5001 UI/UX
"""
import streamlit as st
import time
import json
import threading
import subprocess
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Try to import the pipeline modules
try:
    from pipeline.schemas import FactStore, ReasoningStore
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    FactStore = None
    ReasoningStore = None

# Try to import the analysis runner
try:
    from web.analysis_runner import run_analysis_simple, check_pipeline_availability
    from web.task_manager import AnalysisTask, AnalysisPhase, TaskStatus
    ANALYSIS_RUNNER_AVAILABLE = True
except ImportError:
    ANALYSIS_RUNNER_AVAILABLE = False
    run_analysis_simple = None
    check_pipeline_availability = None

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="IT Due Diligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# CSS - Exact match to Flask tokens.css
# =============================================================================
FLASK_CSS = """
<style>
/* Hide Streamlit default UI */
#MainMenu, footer, header, .stDeployButton {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}
div[data-testid="stDecoration"] {display: none !important;}
div[data-testid="stStatusWidget"] {display: none !important;}
.stApp > header {display: none !important;}

/* CSS Variables - exact match to Flask tokens.css */
:root {
    --bg-base: #fafaf9;
    --bg-surface: #ffffff;
    --bg-surface-sunken: #f5f5f4;
    --text-primary: #1c1917;
    --text-secondary: #44403c;
    --text-muted: #78716c;
    --border-default: #e7e5e4;
    --accent: #f97316;
    --accent-hover: #ea580c;
    --accent-subtle: rgba(249, 115, 22, 0.08);
    --critical: #dc2626;
    --critical-bg: rgba(220, 38, 38, 0.08);
    --high: #ea580c;
    --high-bg: rgba(234, 88, 12, 0.08);
    --medium: #ca8a04;
    --medium-bg: rgba(202, 138, 4, 0.08);
    --low: #16a34a;
    --low-bg: rgba(22, 163, 74, 0.08);
    --info: #0284c7;
    --info-bg: rgba(2, 132, 199, 0.08);
    --nav-height: 56px;
    --radius-sm: 0.25rem;
    --radius-md: 0.375rem;
    --radius-lg: 0.5rem;
}

/* Base styles */
.stApp {
    background: var(--bg-base) !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Navigation Bar */
.nav-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: var(--nav-height);
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border-default);
    display: flex;
    align-items: center;
    padding: 0 24px;
    z-index: 1000;
    gap: 32px;
}

.nav-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 600;
    color: var(--text-primary);
    text-decoration: none;
}

.nav-logo-icon {
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, var(--accent), var(--accent-hover));
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 12px;
    font-weight: 700;
}

.nav-links {
    display: flex;
    gap: 4px;
    flex: 1;
}

.nav-link {
    padding: 8px 14px;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    border-radius: var(--radius-md);
    transition: all 0.15s;
    cursor: pointer;
    border: none;
    background: transparent;
}

.nav-link:hover {
    background: var(--bg-surface-sunken);
    color: var(--text-primary);
}

.nav-link.active {
    background: var(--accent-subtle);
    color: var(--accent);
}

/* Main content area */
.main-content {
    margin-top: calc(var(--nav-height) + 24px);
    padding: 0 24px 24px;
    max-width: 1400px;
    margin-left: auto;
    margin-right: auto;
}

/* Page header */
.page-header {
    margin-bottom: 24px;
}

.page-header h1 {
    font-size: 1.875rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 4px 0;
}

.page-header p {
    color: var(--text-muted);
    margin: 0;
}

/* Cards */
.card {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-default);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-title {
    font-weight: 600;
    color: var(--text-primary);
}

.card-body {
    padding: 20px;
}

/* Metrics Row */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

.metric-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    padding: 20px;
    display: flex;
    flex-direction: column;
}

.metric-card.warning {
    border-left: 3px solid var(--critical);
}

.metric-label {
    font-size: 0.875rem;
    color: var(--text-muted);
    margin-bottom: 4px;
}

.metric-value {
    font-size: 1.875rem;
    font-weight: 700;
    color: var(--text-primary);
}

.metric-subtext {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 4px;
}

/* Badges */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.badge-critical { background: var(--critical-bg); color: var(--critical); }
.badge-high { background: var(--high-bg); color: var(--high); }
.badge-medium { background: var(--medium-bg); color: var(--medium); }
.badge-low { background: var(--low-bg); color: var(--low); }
.badge-info { background: var(--info-bg); color: var(--info); }

.badge-day1 { background: var(--critical-bg); color: var(--critical); }
.badge-day100 { background: var(--medium-bg); color: var(--medium); }
.badge-post100 { background: var(--low-bg); color: var(--low); }

/* Tables */
.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th {
    text-align: left;
    padding: 12px 16px;
    background: var(--bg-surface-sunken);
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid var(--border-default);
}

.data-table td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-default);
    font-size: 0.875rem;
}

.data-table tr:hover {
    background: var(--bg-surface-sunken);
}

.data-table .truncate {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    text-decoration: none;
    border: none;
}

.btn-primary {
    background: var(--accent);
    color: white;
}

.btn-primary:hover {
    background: var(--accent-hover);
}

.btn-secondary {
    background: var(--bg-surface);
    color: var(--text-primary);
    border: 1px solid var(--border-default);
}

.btn-secondary:hover {
    background: var(--bg-surface-sunken);
}

.btn-lg {
    padding: 15px 40px;
    font-size: 1.1rem;
}

/* Upload dropzone */
.upload-dropzone {
    border: 2px dashed var(--border-default);
    border-radius: 12px;
    padding: 60px 30px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    background: var(--bg-surface-sunken);
}

.upload-dropzone:hover {
    border-color: var(--accent);
    background: var(--accent-subtle);
}

.dropzone-icon {
    font-size: 4em;
    margin-bottom: 15px;
    opacity: 0.6;
}

/* Options grid */
.options-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 10px;
    margin: 20px 0;
}

.option-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 15px;
    border: 1px solid var(--border-default);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
    background: var(--bg-surface);
}

.option-card:hover, .option-card.selected {
    border-color: var(--accent);
    background: var(--accent-subtle);
}

.option-icon {
    font-size: 1.5em;
    margin-bottom: 5px;
}

.option-label {
    font-size: 0.85em;
}

/* Context fields */
.context-fields {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-top: 15px;
}

.field-group label {
    display: block;
    font-size: 0.85em;
    color: var(--text-muted);
    margin-bottom: 5px;
}

/* Filter bar */
.filters-bar {
    display: flex;
    gap: 16px;
    padding: 16px;
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    margin-bottom: 16px;
    flex-wrap: wrap;
    align-items: flex-end;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 40px;
}

.empty-state-icon {
    font-size: 4em;
    margin-bottom: 20px;
}

.empty-state-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 8px;
}

.empty-state-text {
    color: var(--text-muted);
}

/* Two column layout */
.two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
}

/* Font utilities */
.font-mono {
    font-family: 'SF Mono', Monaco, 'Cascadia Code', Consolas, monospace;
}

.text-muted {
    color: var(--text-muted);
}

.text-sm {
    font-size: 0.875rem;
}

/* Responsive */
@media (max-width: 1024px) {
    .metrics-row { grid-template-columns: repeat(2, 1fr); }
    .two-col { grid-template-columns: 1fr; }
    .options-grid { grid-template-columns: repeat(3, 1fr); }
    .context-fields { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
    .metrics-row { grid-template-columns: 1fr; }
    .options-grid { grid-template-columns: repeat(2, 1fr); }
    .context-fields { grid-template-columns: 1fr; }
    .nav-links { display: none; }
}
</style>
"""

# Inject CSS
st.markdown(FLASK_CSS, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
if "page" not in st.session_state:
    st.session_state["page"] = "welcome"
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "analysis_running" not in st.session_state:
    st.session_state["analysis_running"] = False
if "analysis_complete" not in st.session_state:
    st.session_state["analysis_complete"] = False

# =============================================================================
# DATA LOADING
# =============================================================================
def load_data():
    """Load fact store and reasoning store from output files.

    Returns: (fact_store, reasoning_store, metadata)
    Where metadata contains info about loaded files for freshness tracking.
    """
    fact_store = None
    reasoning_store = None
    metadata = {
        'facts_file': None,
        'facts_timestamp': None,
        'findings_file': None,
        'findings_timestamp': None,
        'load_time': datetime.now().isoformat()
    }

    # Use the correct output directory (same as Flask app)
    output_dir = Path(__file__).parent / "output"

    # Find the most recent facts file (matching Flask app behavior)
    facts_files = sorted(output_dir.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    findings_files = sorted(output_dir.glob("findings_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

    # Load from most recent facts file that has actual facts
    for fact_file in facts_files:
        if fact_file.stat().st_size > 500:  # Skip empty/minimal files
            try:
                with open(fact_file) as f:
                    data = json.load(f)
                    # Skip files with no actual facts
                    if not data.get('facts') or len(data.get('facts', [])) == 0:
                        continue
                    if PIPELINE_AVAILABLE and FactStore:
                        fact_store = FactStore.model_validate(data)
                    else:
                        # Create a simple namespace object
                        class SimpleStore:
                            def __init__(self, data):
                                self.facts = [type('Fact', (), f)() for f in data.get('facts', [])]
                                self.gaps = [type('Gap', (), g)() for g in data.get('gaps', [])]
                                for i, f in enumerate(self.facts):
                                    for k, v in data.get('facts', [])[i].items():
                                        setattr(f, k, v)
                                for i, g in enumerate(self.gaps):
                                    for k, v in data.get('gaps', [])[i].items():
                                        setattr(g, k, v)
                        fact_store = SimpleStore(data)
                    # Record metadata
                    metadata['facts_file'] = fact_file.name
                    metadata['facts_timestamp'] = datetime.fromtimestamp(fact_file.stat().st_mtime).isoformat()
                    break
            except Exception as e:
                continue  # Try next file

    # Load from most recent findings file that has actual findings
    for findings_file in findings_files:
        if findings_file.stat().st_size > 500:  # Skip empty/minimal files
            try:
                with open(findings_file) as f:
                    data = json.load(f)
                    # Skip files with no actual findings
                    has_content = (
                        len(data.get('risks', [])) > 0 or
                        len(data.get('work_items', [])) > 0 or
                        len(data.get('open_questions', [])) > 0
                    )
                    if not has_content:
                        continue
                    if PIPELINE_AVAILABLE and ReasoningStore:
                        reasoning_store = ReasoningStore.model_validate(data)
                    else:
                        class SimpleStore:
                            def __init__(self, data):
                                self.risks = [type('Risk', (), {})() for r in data.get('risks', [])]
                                self.work_items = [type('WI', (), {})() for w in data.get('work_items', [])]
                                self.open_questions = [type('Q', (), {})() for q in data.get('open_questions', [])]
                                for i, r in enumerate(self.risks):
                                    for k, v in data.get('risks', [])[i].items():
                                        setattr(r, k, v)
                                for i, w in enumerate(self.work_items):
                                    for k, v in data.get('work_items', [])[i].items():
                                        setattr(w, k, v)
                                for i, q in enumerate(self.open_questions):
                                    for k, v in data.get('open_questions', [])[i].items():
                                        setattr(q, k, v)
                        reasoning_store = SimpleStore(data)
                    # Record metadata
                    metadata['findings_file'] = findings_file.name
                    metadata['findings_timestamp'] = datetime.fromtimestamp(findings_file.stat().st_mtime).isoformat()
                    break
            except Exception as e:
                continue  # Try next file

    return fact_store, reasoning_store, metadata


def load_data_legacy():
    """Legacy wrapper for backward compatibility - returns just fact_store, reasoning_store."""
    fact_store, reasoning_store, _ = load_data()
    return fact_store, reasoning_store

# =============================================================================
# NAVIGATION BAR
# =============================================================================
def render_nav():
    """Render the top navigation bar using Streamlit native components."""
    pages = [
        ("dashboard", "Dashboard"),
        ("risks", "Risks"),
        ("work_items", "Work Items"),
        ("questions", "Questions"),
        ("facts", "Facts"),
        ("gaps", "Gaps"),
        ("organization", "Organization"),
        ("applications", "Applications"),
        ("infrastructure", "Infrastructure"),
        ("upload", "Upload"),
    ]

    current_page = st.session_state.get("page", "dashboard")

    # Render logo HTML
    st.markdown('''
    <div class="nav-bar">
        <div class="nav-logo">
            <div class="nav-logo-icon">DD</div>
            <span>IT Due Diligence</span>
        </div>
    </div>
    <div style="height: 70px;"></div>
    ''', unsafe_allow_html=True)

    # Create navigation using Streamlit columns with buttons
    nav_cols = st.columns(len(pages))
    for i, (page_id, page_name) in enumerate(pages):
        with nav_cols[i]:
            button_type = "primary" if current_page == page_id else "secondary"
            if st.button(page_name, key=f"nav_{page_id}", use_container_width=True, type=button_type):
                st.session_state["page"] = page_id
                st.rerun()

# =============================================================================
# PAGE: WELCOME
# =============================================================================
def page_welcome():
    """Landing/welcome page matching Flask design - integrated with Streamlit."""

    # Inject CSS for the welcome page styling
    st.markdown("""
        <style>
        /* Override Streamlit's default background for welcome page */
        .stApp {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
        }
        [data-testid="stHeader"] { background: transparent !important; }

        /* Welcome page specific styles */
        .welcome-hero {
            text-align: center;
            padding: 40px 20px;
            color: white;
        }
        .welcome-logo {
            width: 120px;
            height: 120px;
            background: linear-gradient(135deg, #e94560, #533483);
            border-radius: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 30px;
            font-size: 3em;
            font-weight: bold;
            color: white;
            box-shadow: 0 20px 60px rgba(233, 69, 96, 0.3);
        }
        .welcome-title {
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 15px;
            color: white;
        }
        .welcome-tagline {
            font-size: 1.2em;
            color: #888;
            margin-bottom: 40px;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 40px 0;
        }
        .feature-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            color: white;
        }
        .feature-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .feature-title {
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 8px;
            color: white;
        }
        .feature-desc {
            font-size: 0.9em;
            color: #888;
        }
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 50px;
            margin: 40px 0;
            padding: 25px;
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: 700;
            color: #e94560;
        }
        .stat-label {
            font-size: 0.85em;
            color: #666;
        }
        /* Style Streamlit buttons to match */
        .stButton > button {
            background: linear-gradient(135deg, #e94560, #533483) !important;
            color: white !important;
            border: none !important;
            padding: 15px 35px !important;
            font-size: 1.1em !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
            box-shadow: 0 10px 30px rgba(233, 69, 96, 0.3) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(233, 69, 96, 0.4) !important;
        }
        .stButton > button[kind="secondary"] {
            background: rgba(255,255,255,0.1) !important;
            border: 2px solid rgba(255,255,255,0.2) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Hero section
    st.markdown("""
        <div class="welcome-hero">
            <div class="welcome-logo">DD</div>
            <div class="welcome-title">IT Due Diligence Agent</div>
            <div class="welcome-tagline">AI-powered analysis for M&A technology assessments</div>
        </div>
    """, unsafe_allow_html=True)

    # CTA Buttons using native Streamlit (they work!)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("📁 Upload Documents", use_container_width=True, key="welcome_upload"):
                st.session_state["page"] = "upload"
                st.rerun()
        with bcol2:
            if st.button("📊 View Dashboard", use_container_width=True, key="welcome_dashboard"):
                st.session_state["page"] = "dashboard"
                st.rerun()

    # Features section
    st.markdown("""
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">💻</div>
                <div class="feature-title">Applications Analysis</div>
                <div class="feature-desc">Inventory apps, assess licenses, identify technical debt</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🌐</div>
                <div class="feature-title">Infrastructure Review</div>
                <div class="feature-desc">Cloud vs on-prem, capacity, EOL equipment</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔒</div>
                <div class="feature-title">Security Assessment</div>
                <div class="feature-desc">Controls, vulnerabilities, compliance gaps</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Stats bar
    st.markdown("""
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-value">6</div>
                <div class="stat-label">Analysis Domains</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">100+</div>
                <div class="stat-label">Risk Patterns</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">AI</div>
                <div class="stat-label">Powered Insights</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =============================================================================
# PAGE: UPLOAD
# =============================================================================
def page_upload():
    """Upload documents page using native Streamlit components."""
    render_nav()

    st.title("Upload Documents for Analysis")
    st.write("Upload VDR documents, census data, and other materials for AI-powered analysis")

    st.divider()

    # File uploader
    uploaded_files = st.file_uploader(
        "Drag & Drop Files Here or click to browse",
        type=["pdf", "xlsx", "xls", "csv", "docx", "doc", "pptx", "ppt", "txt", "json", "md"],
        accept_multiple_files=True,
        key="file_uploader"
    )

    if uploaded_files:
        st.session_state["uploaded_files"] = uploaded_files
        st.success(f"✓ {len(uploaded_files)} file(s) selected")

        # Show file list
        for f in uploaded_files:
            st.write(f"📄 **{f.name}** - {f.size/1024:.1f} KB")

    st.divider()

    # Analysis Options
    st.subheader("Analysis Domains")

    domains = ["Applications", "Infrastructure", "Cybersecurity", "Network", "Identity & Access", "Organization"]
    domain_icons = ["💻", "🌐", "🔒", "📡", "👤", "👥"]

    cols = st.columns(6)
    selected_domains = []
    for i, (domain, icon) in enumerate(zip(domains, domain_icons)):
        with cols[i]:
            if st.checkbox(f"{icon} {domain}", value=True, key=f"domain_{domain}"):
                selected_domains.append(domain.lower())

    st.divider()

    # Deal Context
    st.subheader("Deal Context (Optional)")

    col1, col2, col3 = st.columns(3)
    with col1:
        deal_type = st.selectbox("Deal Type", ["Acquisition (Bolt-on)", "Carve-out / Divestiture"])
    with col2:
        target_name = st.text_input("Target Company", placeholder="Company name")
    with col3:
        industry = st.selectbox("Industry", ["", "Financial Services", "Healthcare", "Manufacturing", "Retail", "Insurance", "Technology"])

    employee_count = st.number_input("Employee Count", min_value=0, value=0)

    st.divider()

    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶ Start Analysis", type="primary", use_container_width=True, disabled=not uploaded_files):
            # Save uploaded files to data/input
            input_dir = Path("data/input")
            input_dir.mkdir(parents=True, exist_ok=True)

            saved_paths = []
            for uploaded_file in uploaded_files:
                file_path = input_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_paths.append(str(file_path))

            st.session_state["uploaded_files"] = [f.name for f in uploaded_files]
            st.session_state["uploaded_paths"] = saved_paths
            st.session_state["analysis_running"] = True
            st.session_state["analysis_start_time"] = datetime.now().isoformat()
            st.session_state["page"] = "processing"
            st.rerun()

        st.write("")

        if st.button("📊 Go to Dashboard", use_container_width=True):
            st.session_state["page"] = "dashboard"
            st.rerun()

    st.caption("Analysis typically takes 2-5 minutes depending on document volume")

# =============================================================================
# PAGE: PROCESSING
# =============================================================================
def run_analysis_subprocess():
    """Run analysis using main.py as a subprocess."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent)
    )
    return result.returncode == 0, result.stdout, result.stderr

def page_processing():
    """Processing page matching Flask design - integrated with Streamlit."""

    # Check if analysis should be running
    analysis_running = st.session_state.get("analysis_running", False)
    uploaded_paths = st.session_state.get("uploaded_paths", [])

    # Check if we have existing results
    fact_store, reasoning_store, _ = load_data()
    has_results = (fact_store and fact_store.facts) or (reasoning_store and reasoning_store.risks)

    facts_count = len(fact_store.facts) if fact_store and fact_store.facts else 0
    risks_count = len(reasoning_store.risks) if reasoning_store and reasoning_store.risks else 0
    wi_count = len(reasoning_store.work_items) if reasoning_store and reasoning_store.work_items else 0

    status_title = "Analysis Complete!" if has_results else "Ready to Analyze"
    status_desc = "Your documents have been processed." if has_results else "Upload documents to begin analysis."
    step_status = "Complete" if has_results else "Pending"
    step_color = "#00d9ff" if has_results else "#666"
    step_bg = "rgba(0, 217, 255, 0.1)" if has_results else "rgba(255,255,255,0.05)"

    # Inject CSS
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
        }
        [data-testid="stHeader"] { background: transparent !important; }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .proc-container {
            text-align: center;
            padding: 40px 20px;
            color: white;
            max-width: 600px;
            margin: 0 auto;
        }
        .logo-container {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 0 auto 40px;
        }
        .ring1 {
            position: absolute;
            width: 150px; height: 150px;
            border: 3px solid transparent;
            border-top-color: #e94560;
            border-right-color: #e94560;
            border-radius: 50%;
            animation: spin 3s linear infinite;
        }
        .ring2 {
            position: absolute;
            width: 120px; height: 120px;
            top: 15px; left: 15px;
            border: 3px solid transparent;
            border-bottom-color: #533483;
            border-left-color: #533483;
            border-radius: 50%;
            animation: spin 2s linear infinite reverse;
        }
        .ring3 {
            position: absolute;
            width: 90px; height: 90px;
            top: 30px; left: 30px;
            border: 3px solid transparent;
            border-top-color: #00d9ff;
            border-radius: 50%;
            animation: spin 1.5s linear infinite;
        }
        .logo-center {
            position: absolute;
            width: 60px; height: 60px;
            top: 45px; left: 45px;
            background: linear-gradient(135deg, #e94560, #533483);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5em;
            font-weight: bold;
            color: white;
        }
        .proc-title {
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 10px;
            color: white;
        }
        .proc-subtitle {
            color: #888;
            margin-bottom: 30px;
        }
        .stats-row {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 30px 0;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #00d9ff;
        }
        .stat-label {
            font-size: 0.8em;
            color: #666;
        }
        .steps-container {
            text-align: left;
            margin: 30px 0;
        }
        .step-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px 20px;
            margin: 10px 0;
            border-radius: 10px;
        }
        .step-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
        }
        .step-text {
            flex: 1;
        }
        .step-label {
            font-weight: 600;
            color: white;
        }
        .fun-fact {
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            font-style: italic;
            color: #888;
            margin-top: 20px;
        }
        .stButton > button {
            background: linear-gradient(135deg, #e94560, #533483) !important;
            color: white !important;
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Animated logo and header
    st.markdown(f"""
        <div class="proc-container">
            <div class="logo-container">
                <div class="ring1"></div>
                <div class="ring2"></div>
                <div class="ring3"></div>
                <div class="logo-center">DD</div>
            </div>
            <div class="proc-title">{status_title}</div>
            <div class="proc-subtitle">{status_desc}</div>
            <div class="stats-row">
                <div class="stat-item">
                    <div class="stat-value">{facts_count}</div>
                    <div class="stat-label">Facts Extracted</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{risks_count}</div>
                    <div class="stat-label">Risks Identified</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{wi_count}</div>
                    <div class="stat-label">Work Items</div>
                </div>
            </div>
            <div class="steps-container">
                <div class="step-item" style="background: {step_bg}; border-left: 3px solid {step_color};">
                    <div class="step-icon" style="background: {step_color};">📁</div>
                    <div class="step-text"><div class="step-label">Processing Documents</div><div style="font-size: 0.85em; color: {step_color};">{step_status}</div></div>
                </div>
                <div class="step-item" style="background: {step_bg}; border-left: 3px solid {step_color};">
                    <div class="step-icon" style="background: {step_color};">🔍</div>
                    <div class="step-text"><div class="step-label">Extracting Facts</div><div style="font-size: 0.85em; color: {step_color};">{step_status}</div></div>
                </div>
                <div class="step-item" style="background: {step_bg}; border-left: 3px solid {step_color};">
                    <div class="step-icon" style="background: {step_color};">⚠️</div>
                    <div class="step-text"><div class="step-label">Identifying Risks</div><div style="font-size: 0.85em; color: {step_color};">{step_status}</div></div>
                </div>
                <div class="step-item" style="background: {step_bg}; border-left: 3px solid {step_color};">
                    <div class="step-icon" style="background: {step_color};">📊</div>
                    <div class="step-text"><div class="step-label">Generating Report</div><div style="font-size: 0.85em; color: {step_color};">{step_status}</div></div>
                </div>
            </div>
            <div class="fun-fact">
                💡 Did you know? The average M&A IT due diligence uncovers 15-25 previously unknown risks.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Action buttons using native Streamlit
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if has_results:
            if st.button("📊 View Dashboard", type="primary", use_container_width=True, key="proc_dashboard"):
                st.session_state["page"] = "dashboard"
                st.rerun()
            st.write("")
            if st.button("📄 Upload More Documents", use_container_width=True, key="proc_upload"):
                st.session_state["page"] = "upload"
                st.rerun()
        else:
            if st.button("📄 Upload Documents", type="primary", use_container_width=True, key="proc_upload2"):
                st.session_state["page"] = "upload"
                st.rerun()
            st.write("")
            if st.button("📊 View Dashboard Anyway", use_container_width=True, key="proc_dash2"):
                st.session_state["page"] = "dashboard"
                st.rerun()

    # If analysis is running, run it
    if analysis_running and uploaded_paths and not has_results:
        with st.spinner("Running analysis pipeline..."):
            try:
                success, stdout, stderr = run_analysis_subprocess()
                if success:
                    st.session_state["analysis_running"] = False
                    st.session_state["analysis_complete"] = True
                    st.rerun()
                else:
                    st.error(f"Analysis failed: {stderr[:500] if stderr else 'Unknown error'}")
                    st.session_state["analysis_running"] = False
            except Exception as e:
                st.error(f"Error running analysis: {str(e)}")
                st.session_state["analysis_running"] = False

            st.write("")

            if st.button("📊 View Dashboard Anyway", use_container_width=True, key="proc_dash2"):
                st.session_state["page"] = "dashboard"
                st.rerun()

# =============================================================================
# PAGE: DASHBOARD
# =============================================================================
def page_dashboard():
    """Main dashboard page."""
    fact_store, reasoning_store, metadata = load_data()

    render_nav()

    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown('''
    <div class="page-header">
        <h1>Analysis Dashboard</h1>
        <p>Overview of IT due diligence findings for this deal</p>
    </div>
    ''', unsafe_allow_html=True)

    # Show data source info for freshness tracking
    if metadata.get('facts_file'):
        facts_ts = metadata.get('facts_timestamp', 'Unknown')
        if facts_ts and facts_ts != 'Unknown':
            try:
                dt = datetime.fromisoformat(facts_ts)
                facts_ts_display = dt.strftime('%Y-%m-%d %H:%M')
            except:
                facts_ts_display = facts_ts[:16] if len(facts_ts) > 16 else facts_ts
        else:
            facts_ts_display = 'Unknown'
        st.caption(f"📁 Data source: `{metadata.get('facts_file')}` (Last modified: {facts_ts_display})")

    facts_count = len(fact_store.facts) if fact_store else 0
    risks_count = len(reasoning_store.risks) if reasoning_store else 0
    gaps_count = len(fact_store.gaps) if fact_store else 0
    work_items_count = len(reasoning_store.work_items) if reasoning_store else 0

    if facts_count == 0 and risks_count == 0:
        st.markdown('''
        <div class="card" style="text-align: center; padding: 60px 40px;">
            <div class="empty-state-icon">📊</div>
            <div class="empty-state-title">No Analysis Results</div>
            <div class="empty-state-text">Upload documents to start analyzing IT infrastructure, security, applications, and organization.</div>
        </div>
        ''', unsafe_allow_html=True)

        if st.button("Upload Documents", type="primary"):
            st.session_state["page"] = "upload"
            st.rerun()
        return

    # Metrics row
    critical_risks = len([r for r in reasoning_store.risks if getattr(r, 'severity', '') == 'critical']) if reasoning_store else 0
    high_risks = len([r for r in reasoning_store.risks if getattr(r, 'severity', '') == 'high']) if reasoning_store else 0
    day1_count = len([w for w in reasoning_store.work_items if getattr(w, 'phase', '') == 'Day_1']) if reasoning_store else 0

    domains = list(set(getattr(f, 'domain', '') for f in fact_store.facts)) if fact_store else []

    st.markdown(f'''
    <div class="metrics-row">
        <div class="metric-card">
            <span class="metric-label">Facts Discovered</span>
            <span class="metric-value">{facts_count}</span>
            <span class="metric-subtext">Across {len(domains)} domains</span>
        </div>
        <div class="metric-card {"warning" if gaps_count > 10 else ""}">
            <span class="metric-label">Information Gaps</span>
            <span class="metric-value">{gaps_count}</span>
            <span class="metric-subtext">Requiring VDR requests</span>
        </div>
        <div class="metric-card {"warning" if critical_risks > 0 else ""}">
            <span class="metric-label">Risks Identified</span>
            <span class="metric-value">{risks_count}</span>
            <span class="metric-subtext"><span style="color: var(--critical);">{critical_risks} critical</span>, {high_risks} high</span>
        </div>
        <div class="metric-card">
            <span class="metric-label">Work Items</span>
            <span class="metric-value">{work_items_count}</span>
            <span class="metric-subtext">{day1_count} for Day 1</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Two column grid
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card"><div class="card-header"><span class="card-title">Cost Summary</span></div><div class="card-body">', unsafe_allow_html=True)

        if reasoning_store and reasoning_store.work_items:
            cost_data = {"Day_1": {"count": 0, "low": 0, "high": 0}, "Day_100": {"count": 0, "low": 0, "high": 0}, "Post_100": {"count": 0, "low": 0, "high": 0}}
            for wi in reasoning_store.work_items:
                phase = getattr(wi, 'phase', 'Day_100')
                if phase in cost_data:
                    cost_data[phase]["count"] += 1
                    cost_data[phase]["low"] += getattr(wi, 'cost_low', 0) or 0
                    cost_data[phase]["high"] += getattr(wi, 'cost_high', 0) or 0

            st.markdown('<table class="data-table"><thead><tr><th>Phase</th><th>Items</th><th style="text-align:right;">Cost Range</th></tr></thead><tbody>', unsafe_allow_html=True)

            total_count, total_low, total_high = 0, 0, 0
            for phase in ["Day_1", "Day_100", "Post_100"]:
                d = cost_data[phase]
                badge_class = phase.lower().replace("_", "")
                st.markdown(f'<tr><td><span class="badge badge-{badge_class}">{phase.replace("_", " ")}</span></td><td>{d["count"]}</td><td style="text-align:right;">${d["low"]:,.0f} - ${d["high"]:,.0f}</td></tr>', unsafe_allow_html=True)
                total_count += d["count"]
                total_low += d["low"]
                total_high += d["high"]

            st.markdown(f'</tbody><tfoot style="background: var(--bg-surface-sunken);"><tr><td><strong>Total</strong></td><td><strong>{total_count}</strong></td><td style="text-align:right;"><strong>${total_low:,.0f} - ${total_high:,.0f}</strong></td></tr></tfoot></table>', unsafe_allow_html=True)
        else:
            st.info("No work items found")

        st.markdown('</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card"><div class="card-header"><span class="card-title">Top Risks</span></div><div class="card-body">', unsafe_allow_html=True)

        if reasoning_store and reasoning_store.risks:
            sorted_risks = sorted(reasoning_store.risks, key=lambda r: ["critical", "high", "medium", "low"].index(getattr(r, 'severity', 'low')) if getattr(r, 'severity', 'low') in ["critical", "high", "medium", "low"] else 99)[:5]

            st.markdown('<table class="data-table"><thead><tr><th>Severity</th><th>Risk</th><th>Domain</th></tr></thead><tbody>', unsafe_allow_html=True)

            for risk in sorted_risks:
                sev = getattr(risk, 'severity', 'info')
                title = getattr(risk, 'title', 'N/A')[:50]
                domain = getattr(risk, 'domain', '').replace('_', ' ').title()
                st.markdown(f'<tr><td><span class="badge badge-{sev}">{sev.upper()}</span></td><td class="truncate">{title}</td><td class="text-muted">{domain}</td></tr>', unsafe_allow_html=True)

            st.markdown('</tbody></table>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state"><div class="empty-state-icon">🎉</div><div class="empty-state-title">No risks identified</div></div>', unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# PAGE: RISKS
# =============================================================================
def page_risks():
    """Risks listing page using native Streamlit components."""
    render_nav()
    fact_store, reasoning_store, _ = load_data()

    st.title("Risks")
    st.write("Identified risks and mitigation strategies")
    st.divider()

    if not reasoning_store or not reasoning_store.risks:
        st.warning("⚠️ No risks identified yet. Run an analysis to identify risks.")
        return

    # Summary metrics
    all_risks = reasoning_store.risks
    critical = len([r for r in all_risks if getattr(r, 'severity', '') == 'critical'])
    high = len([r for r in all_risks if getattr(r, 'severity', '') == 'high'])
    medium = len([r for r in all_risks if getattr(r, 'severity', '') == 'medium'])
    low = len([r for r in all_risks if getattr(r, 'severity', '') == 'low'])

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total", len(all_risks))
    with col2:
        st.metric("Critical", critical)
    with col3:
        st.metric("High", high)
    with col4:
        st.metric("Medium", medium)
    with col5:
        st.metric("Low", low)

    st.divider()

    # Filters
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        severity_filter = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"])
    with col2:
        domains = list(set(getattr(r, 'domain', '') for r in all_risks if getattr(r, 'domain', '')))
        domain_filter = st.selectbox("Domain", ["All"] + sorted(domains))
    with col3:
        search = st.text_input("Search", placeholder="Search risks...")

    # Filter
    filtered = all_risks
    if severity_filter != "All":
        filtered = [r for r in filtered if getattr(r, 'severity', '').lower() == severity_filter.lower()]
    if domain_filter != "All":
        filtered = [r for r in filtered if getattr(r, 'domain', '') == domain_filter]
    if search:
        filtered = [r for r in filtered if search.lower() in getattr(r, 'title', '').lower()]

    st.caption(f"Showing {len(filtered)} of {len(all_risks)} risks")

    # Display risks
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_risks = sorted(filtered, key=lambda r: severity_order.get(getattr(r, 'severity', 'low'), 99))

    for risk in sorted_risks:
        sev = getattr(risk, 'severity', 'info')
        title = getattr(risk, 'title', 'N/A')
        domain = getattr(risk, 'domain', '').replace('_', ' ').title()
        description = getattr(risk, 'description', '')
        mitigation = getattr(risk, 'mitigation', '')

        # Severity color
        sev_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        sev_icon = sev_colors.get(sev, "⚪")

        with st.expander(f"{sev_icon} **{sev.upper()}** | {title} | _{domain}_"):
            if description:
                st.write(f"**Description:** {description}")
            if mitigation:
                st.write(f"**Mitigation:** {mitigation}")

# =============================================================================
# PAGE: WORK ITEMS
# =============================================================================
def page_work_items():
    """Work items listing page using native Streamlit."""
    render_nav()
    fact_store, reasoning_store, _ = load_data()

    st.title("Work Items")
    st.write("Integration and remediation tasks")
    st.divider()

    if not reasoning_store or not reasoning_store.work_items:
        st.warning("📋 No work items yet. Run an analysis to generate work items.")
        return

    all_items = reasoning_store.work_items
    day1 = [w for w in all_items if getattr(w, 'phase', '') == 'Day_1']
    day100 = [w for w in all_items if getattr(w, 'phase', '') == 'Day_100']
    post100 = [w for w in all_items if getattr(w, 'phase', '') == 'Post_100']

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", len(all_items))
    with col2:
        st.metric("Day 1", len(day1))
    with col3:
        st.metric("Day 100", len(day100))
    with col4:
        st.metric("Post-100", len(post100))

    st.divider()

    # Tabs for phases
    tab1, tab2, tab3, tab4 = st.tabs([
        f"All ({len(all_items)})",
        f"🚨 Day 1 ({len(day1)})",
        f"📅 Day 100 ({len(day100)})",
        f"📆 Post-100 ({len(post100)})"
    ])

    def render_work_items(items):
        if not items:
            st.info("No work items in this phase")
            return

        for wi in items:
            title = getattr(wi, 'title', 'N/A')
            domain = getattr(wi, 'domain', '').replace('_', ' ').title()
            phase = getattr(wi, 'phase', 'Day_100').replace('_', ' ')
            priority = getattr(wi, 'priority', 'medium')
            owner = getattr(wi, 'owner_type', 'buyer')
            description = getattr(wi, 'description', '')
            cost_est = getattr(wi, 'cost_estimate', None)

            # Priority icons
            priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            priority_icon = priority_icons.get(priority, "⚪")

            with st.expander(f"{priority_icon} {title} | _{domain}_ | {phase}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Priority:** {priority.title()}")
                with col2:
                    st.write(f"**Owner:** {owner.title()}")
                with col3:
                    if cost_est:
                        st.write(f"**Cost:** {cost_est}")
                if description:
                    st.write(f"**Description:** {description}")

    with tab1:
        render_work_items(all_items)
    with tab2:
        render_work_items(day1)
    with tab3:
        render_work_items(day100)
    with tab4:
        render_work_items(post100)

# =============================================================================
# SIMPLE PAGES
# =============================================================================
def page_questions():
    """Open Questions page."""
    render_nav()
    fact_store, reasoning_store, _ = load_data()

    st.title("Open Questions")
    st.write("Questions requiring clarification from the target company")
    st.divider()

    if not reasoning_store or not reasoning_store.open_questions:
        st.info("❓ No open questions identified yet.")
        return

    st.metric("Total Questions", len(reasoning_store.open_questions))
    st.divider()

    for i, q in enumerate(reasoning_store.open_questions, 1):
        question_text = getattr(q, 'question', getattr(q, 'item', 'N/A'))
        domain = getattr(q, 'domain', 'General')
        importance = getattr(q, 'importance', 'medium')

        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**Q{i}.** {question_text}")
            with col2:
                st.caption(domain)
            st.divider()

def page_facts():
    """Facts page - all discovered facts from document analysis."""
    render_nav()
    fact_store, reasoning_store, _ = load_data()

    st.title("Facts")
    st.write("Discovered facts from document analysis")
    st.divider()

    if not fact_store or not fact_store.facts:
        st.info("📋 No facts discovered yet. Upload and analyze documents to extract facts.")
        return

    # Summary
    st.metric("Total Facts", len(fact_store.facts))

    # Group by domain
    domains = {}
    for f in fact_store.facts:
        d = getattr(f, 'domain', 'other')
        if d not in domains:
            domains[d] = []
        domains[d].append(f)

    st.divider()

    # Show domain tabs or expanders
    for domain, facts in sorted(domains.items()):
        with st.expander(f"📁 {domain.replace('_', ' ').title()} ({len(facts)} facts)", expanded=False):
            # Group by category within domain
            categories = {}
            for f in facts:
                cat = getattr(f, 'category', 'General')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(f)

            for cat, cat_facts in sorted(categories.items()):
                st.write(f"**{cat}** ({len(cat_facts)})")
                for fact in cat_facts[:10]:  # Limit to 10 per category
                    item = getattr(fact, 'item', getattr(fact, 'fact', 'N/A'))
                    st.write(f"• {item}")
                if len(cat_facts) > 10:
                    st.caption(f"... and {len(cat_facts) - 10} more")
                st.write("")

def page_gaps():
    """Information Gaps page."""
    render_nav()
    fact_store, reasoning_store, _ = load_data()

    st.title("Information Gaps")
    st.write("Missing information that may require VDR requests")
    st.divider()

    if not fact_store or not fact_store.gaps:
        st.success("✅ No information gaps identified - documentation appears complete.")
        return

    st.metric("Total Gaps", len(fact_store.gaps))
    st.divider()

    # Group by domain
    domains = {}
    for g in fact_store.gaps:
        d = getattr(g, 'domain', 'General')
        if d not in domains:
            domains[d] = []
        domains[d].append(g)

    for domain, gaps in sorted(domains.items()):
        with st.expander(f"⚠️ {domain.replace('_', ' ').title()} ({len(gaps)} gaps)", expanded=True):
            for gap in gaps:
                item = getattr(gap, 'item', getattr(gap, 'gap', 'N/A'))
                st.warning(f"• {item}")

def page_organization():
    """Organization module - IT team structure and staffing matching Flask design."""
    render_nav()
    fact_store, reasoning_store, _ = load_data()

    # Page header
    st.markdown('''
    <div class="page-header">
        <h1>Organization & Staffing Analysis</h1>
        <p style="color: #888;">IT staffing assessment with benchmark comparison and dependency analysis</p>
    </div>
    ''', unsafe_allow_html=True)

    if not fact_store or not fact_store.facts:
        st.markdown('''
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); color: #92400e; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;">
            <strong>No Data</strong> - Run an analysis with documents containing organization/staffing information to populate this view.
        </div>
        ''', unsafe_allow_html=True)
        return

    # Filter organization facts
    org_facts = [f for f in fact_store.facts if getattr(f, 'domain', '').lower() == 'organization']

    if not org_facts:
        st.info("No organization data found in the analysis.")
        return

    # Data source banner
    st.markdown(f'''
    <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); color: #166534; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;">
        <strong>Analysis Data</strong> - Showing organization data extracted from your documents.
    </div>
    ''', unsafe_allow_html=True)

    # Group facts by category
    categories = {}
    for f in org_facts:
        cat = getattr(f, 'category', 'general')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)

    # Category icons
    cat_icons = {
        'staffing': '👥', 'leadership': '👔', 'it_staff': '💻', 'roles': '🎭',
        'compensation': '💰', 'msp': '🔗', 'vendors': '📦', 'general': '📋',
        'structure': '🏛️', 'outsourcing': '🌐', 'contractors': '🔧'
    }

    # Calculate summary stats
    staffing_count = len(categories.get('staffing', []) + categories.get('it_staff', []) + categories.get('roles', []))
    leadership_count = len(categories.get('leadership', []))
    msp_count = len(categories.get('msp', []) + categories.get('vendors', []) + categories.get('outsourcing', []))

    # Summary Stats
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Facts", len(org_facts))
    with col2:
        st.metric("Staffing Info", staffing_count)
    with col3:
        st.metric("Leadership", leadership_count)
    with col4:
        st.metric("MSP/Vendors", msp_count)
    with col5:
        org_risks = [r for r in (reasoning_store.risks if reasoning_store else []) if getattr(r, 'domain', '').lower() == 'organization']
        st.metric("Related Risks", len(org_risks))

    st.divider()

    # Navigation Cards Section
    st.subheader("Analysis Areas")

    nav_col1, nav_col2 = st.columns(2)

    with nav_col1:
        st.markdown('''
        <div style="background: var(--bg-surface, #1a1a2e); border: 1px solid var(--border-default, #333); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; align-items: flex-start; gap: 15px;">
                <div style="font-size: 2em;">👥</div>
                <div>
                    <div style="font-weight: 600; font-size: 1.1em;">Staffing Census</div>
                    <div style="color: #888; font-size: 0.9em; margin-top: 5px;">Role-by-role breakdown with compensation and tenure data</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('''
        <div style="background: var(--bg-surface, #1a1a2e); border: 1px solid var(--border-default, #333); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; align-items: flex-start; gap: 15px;">
                <div style="font-size: 2em;">🔗</div>
                <div>
                    <div style="font-weight: 600; font-size: 1.1em;">MSP Dependencies</div>
                    <div style="color: #888; font-size: 0.9em; margin-top: 5px;">Outsourced services, FTE equivalents, and exit risk</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    with nav_col2:
        st.markdown('''
        <div style="background: var(--bg-surface, #1a1a2e); border: 1px solid var(--border-default, #333); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; align-items: flex-start; gap: 15px;">
                <div style="font-size: 2em;">📊</div>
                <div>
                    <div style="font-weight: 600; font-size: 1.1em;">Benchmark Comparison</div>
                    <div style="color: #888; font-size: 0.9em; margin-top: 5px;">Compare staffing against industry benchmarks</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('''
        <div style="background: var(--bg-surface, #1a1a2e); border: 1px solid var(--border-default, #333); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; align-items: flex-start; gap: 15px;">
                <div style="font-size: 2em;">🏢</div>
                <div>
                    <div style="font-weight: 600; font-size: 1.1em;">Shared Services</div>
                    <div style="color: #888; font-size: 0.9em; margin-top: 5px;">Hidden headcount from parent company dependencies</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    st.divider()

    # IT Support Coverage Section
    st.subheader("🏛️ How IT Supports the Business")
    st.caption("What each team owns and maintains")

    team_cols = st.columns(3)

    with team_cols[0]:
        st.markdown('''
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 1px solid #93c5fd; border-radius: 12px; padding: 20px; height: 200px;">
            <div style="font-size: 1.5em; margin-bottom: 10px;">💻</div>
            <div style="font-weight: 600; color: #1e40af; margin-bottom: 10px;">Applications Team</div>
            <div style="font-size: 0.85em; color: #1e3a8a;">
                <strong>Supports:</strong><br>
                • ERP System<br>
                • CRM & Sales tools<br>
                • Custom applications<br>
                • Integrations
            </div>
        </div>
        ''', unsafe_allow_html=True)

    with team_cols[1]:
        st.markdown('''
        <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1px solid #86efac; border-radius: 12px; padding: 20px; height: 200px;">
            <div style="font-size: 1.5em; margin-bottom: 10px;">🌐</div>
            <div style="font-weight: 600; color: #166534; margin-bottom: 10px;">Infrastructure Team</div>
            <div style="font-size: 0.85em; color: #14532d;">
                <strong>Maintains:</strong><br>
                • Cloud environment<br>
                • Active Directory<br>
                • Servers & storage<br>
                • Backup & DR
            </div>
        </div>
        ''', unsafe_allow_html=True)

    with team_cols[2]:
        st.markdown('''
        <div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border: 1px solid #fca5a5; border-radius: 12px; padding: 20px; height: 200px;">
            <div style="font-size: 1.5em; margin-bottom: 10px;">🔒</div>
            <div style="font-weight: 600; color: #991b1b; margin-bottom: 10px;">Security Team</div>
            <div style="font-size: 0.85em; color: #7f1d1d;">
                <strong>Manages:</strong><br>
                • Security operations<br>
                • Identity & access<br>
                • Compliance<br>
                • Incident response
            </div>
        </div>
        ''', unsafe_allow_html=True)

    st.divider()

    # Detailed Facts Section
    st.subheader("📋 Organization Facts by Category")

    for cat_name, cat_facts in sorted(categories.items(), key=lambda x: -len(x[1])):
        icon = cat_icons.get(cat_name, '📋')
        display_name = cat_name.replace('_', ' ').title()
        with st.expander(f"{icon} {display_name} ({len(cat_facts)} facts)", expanded=False):
            for fact in cat_facts:
                item = getattr(fact, 'item', 'N/A')
                details = getattr(fact, 'details', '')
                evidence = getattr(fact, 'evidence', '')
                source = getattr(fact, 'source_document', '')
                confidence = getattr(fact, 'confidence_score', 0)

                st.markdown(f"**• {item}**")
                if details:
                    st.write(details)
                if evidence:
                    st.markdown(f"*Evidence: \"{evidence[:100]}...\"*" if len(evidence) > 100 else f"*Evidence: \"{evidence}\"*")
                if source:
                    st.caption(f"📄 Source: {source}")

                # Confidence indicator
                conf_pct = int(confidence * 100)
                if conf_pct >= 80:
                    st.progress(confidence, text=f"Confidence: {conf_pct}% ✓")
                elif conf_pct >= 50:
                    st.progress(confidence, text=f"Confidence: {conf_pct}%")
                else:
                    st.progress(max(0.05, confidence), text=f"Confidence: {conf_pct}% ⚠️")
                st.write("")

def page_applications():
    """Applications module - Application inventory and analysis matching Flask design."""
    render_nav()
    fact_store, reasoning_store, _ = load_data()

    # Page header
    st.markdown('''
    <div class="page-header">
        <h1>Applications Inventory</h1>
    </div>
    ''', unsafe_allow_html=True)

    if not fact_store or not fact_store.facts:
        st.markdown('''
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); color: #92400e; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;">
            <strong>No Data</strong> - Run an analysis with documents containing application information to populate this inventory.
        </div>
        ''', unsafe_allow_html=True)
        return

    # Filter application facts
    app_facts = [f for f in fact_store.facts if getattr(f, 'domain', '').lower() == 'applications']

    if not app_facts:
        st.info("No applications data found in the analysis.")
        return

    # Data source banner
    st.markdown(f'''
    <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); color: #166534; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;">
        <strong>Analysis Data</strong> - Showing {len(app_facts)} applications extracted from your documents.
    </div>
    ''', unsafe_allow_html=True)

    # Group facts by category
    categories = {}
    for f in app_facts:
        cat = getattr(f, 'category', 'general')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)

    # Category icons
    cat_icons = {
        'erp': '📊', 'crm': '👥', 'integration': '🔗', 'vertical': '🏭',
        'enterprise': '🏢', 'productivity': '📝', 'general': '📦',
        'security': '🔒', 'analytics': '📈', 'collaboration': '💬',
        'finance': '💰', 'hr': '👔'
    }

    # Summary Stats
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Apps", len(app_facts))
    with col2:
        st.metric("Categories", len(categories))
    with col3:
        erp_count = len(categories.get('erp', []))
        st.metric("ERP Systems", erp_count)
    with col4:
        enterprise_count = len(categories.get('enterprise', []))
        st.metric("Enterprise", enterprise_count)
    with col5:
        app_risks = [r for r in (reasoning_store.risks if reasoning_store else []) if getattr(r, 'domain', '').lower() == 'applications']
        st.metric("Related Risks", len(app_risks))

    st.divider()

    # Categories Grid
    st.subheader("Application Categories")
    cat_cols = st.columns(4)
    for i, (cat_name, cat_facts) in enumerate(sorted(categories.items(), key=lambda x: -len(x[1]))):
        with cat_cols[i % 4]:
            icon = cat_icons.get(cat_name, '📦')
            display_name = cat_name.replace('_', ' ').title()
            st.markdown(f'''
            <div style="background: var(--bg-surface, #1a1a2e); border: 1px solid var(--border-default, #333); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="font-size: 2em; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; background: rgba(100,100,255,0.1); border-radius: 10px;">{icon}</div>
                    <div>
                        <div style="font-weight: 600;">{display_name}</div>
                        <div style="color: #888; font-size: 0.9em;">{len(cat_facts)} apps</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

    st.divider()

    # Core Systems Section (ERP, CRM)
    core_categories = ['erp', 'crm']
    core_facts = []
    for cat in core_categories:
        core_facts.extend(categories.get(cat, []))

    if core_facts:
        st.subheader("🏢 Core Business Systems")
        core_cols = st.columns(3)
        for i, fact in enumerate(core_facts[:6]):
            with core_cols[i % 3]:
                item = str(getattr(fact, 'item', 'Application') or 'Application')
                details = str(getattr(fact, 'details', '') or '')
                category = str(getattr(fact, 'category', 'general') or 'general').upper()

                details_html = f'<div style="font-size: 0.8em; color: #6b21a8; margin-top: 5px;">{details[:60]}...</div>' if details else ''
                st.markdown(f'''
                <div style="background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%); border: 1px solid #d8b4fe; border-radius: 12px; padding: 15px; margin-bottom: 10px;">
                    <div style="font-size: 0.75em; color: #7c3aed; font-weight: bold; margin-bottom: 5px;">{category}</div>
                    <div style="font-weight: 600; color: #581c87;">{item[:40]}{"..." if len(item) > 40 else ""}</div>
                    {details_html}
                </div>
                ''', unsafe_allow_html=True)

    # Full Applications Table
    st.subheader("📋 All Applications")

    import pandas as pd
    table_data = []
    for fact in app_facts:
        item = str(getattr(fact, 'item', 'N/A') or 'N/A')
        # Clean up item if it contains markdown-like formatting
        if item.startswith('**'):
            item = item.replace('**', '').split(':')[0] if ':' in item else item.replace('**', '')

        details = str(getattr(fact, 'details', '') or '')
        source = str(getattr(fact, 'source_document', '') or '')
        category = str(getattr(fact, 'category', 'general') or 'general')
        conf_score = getattr(fact, 'confidence_score', 0) or 0

        table_data.append({
            'Application': item[:40],
            'Category': category.replace('_', ' ').title(),
            'Details': details[:40],
            'Source': source[:20],
            'Confidence': f"{int(conf_score * 100)}%"
        })

    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Detailed view by category
    st.divider()
    st.subheader("📁 Detailed View by Category")
    for cat_name, cat_facts in sorted(categories.items(), key=lambda x: -len(x[1])):
        icon = cat_icons.get(cat_name, '📦')
        display_name = cat_name.replace('_', ' ').title()
        with st.expander(f"{icon} {display_name} ({len(cat_facts)} apps)", expanded=False):
            for fact in cat_facts:
                item = getattr(fact, 'item', 'N/A')
                details = getattr(fact, 'details', '')
                evidence = getattr(fact, 'evidence', '')
                source = getattr(fact, 'source_document', '')
                confidence = getattr(fact, 'confidence_score', 0)

                # Clean up item
                if item.startswith('**'):
                    item = item.replace('**', '').split(':')[0] if ':' in item else item.replace('**', '')

                st.markdown(f"**• {item}**")
                if details:
                    st.write(details)
                if evidence:
                    st.markdown(f"*Evidence: \"{evidence[:100]}...\"*" if len(evidence) > 100 else f"*Evidence: \"{evidence}\"*")
                if source:
                    st.caption(f"📄 Source: {source}")

                # Confidence indicator
                conf_pct = int(confidence * 100)
                if conf_pct >= 80:
                    st.progress(confidence, text=f"Confidence: {conf_pct}% ✓")
                elif conf_pct >= 50:
                    st.progress(confidence, text=f"Confidence: {conf_pct}%")
                else:
                    st.progress(max(0.05, confidence), text=f"Confidence: {conf_pct}% ⚠️")
                st.write("")

def page_infrastructure():
    """Infrastructure module - Infrastructure inventory and analysis matching Flask design."""
    render_nav()
    fact_store, reasoning_store, _ = load_data()

    # Page header
    st.markdown('''
    <div class="page-header">
        <h1>Infrastructure Inventory</h1>
    </div>
    ''', unsafe_allow_html=True)

    if not fact_store or not fact_store.facts:
        st.markdown('''
        <div class="data-source-banner" style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); color: #92400e; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;">
            <strong>No Data</strong> - Run an analysis with documents containing infrastructure information to populate this inventory.
        </div>
        ''', unsafe_allow_html=True)
        return

    # Filter infrastructure facts
    infra_facts = [f for f in fact_store.facts if getattr(f, 'domain', '').lower() == 'infrastructure']

    if not infra_facts:
        st.info("No infrastructure data found in the analysis.")
        return

    # Data source banner
    st.markdown(f'''
    <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); color: #166534; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;">
        <strong>Analysis Data</strong> - Showing {len(infra_facts)} infrastructure items extracted from your documents.
    </div>
    ''', unsafe_allow_html=True)

    # Group facts by category
    categories = {}
    for f in infra_facts:
        cat = getattr(f, 'category', 'general')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)

    # Calculate summary stats
    cloud_count = len(categories.get('cloud', []))
    hosting_count = len(categories.get('hosting', []))
    compute_count = len(categories.get('compute', []) + categories.get('servers', []))
    network_count = len(categories.get('network', []))

    # Category icons
    cat_icons = {
        'cloud': '☁️', 'hosting': '🏢', 'compute': '💻', 'servers': '🖥️',
        'network': '🌐', 'backup_dr': '💾', 'tooling': '🔧', 'general': '📦',
        'storage': '💿', 'security': '🔒'
    }

    # Summary Stats
    st.markdown('''<div class="summary-stats" style="display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap;">''', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Items", len(infra_facts))
    with col2:
        st.metric("Data Centers", hosting_count)
    with col3:
        st.metric("Cloud Items", cloud_count)
    with col4:
        st.metric("Compute/Servers", compute_count)
    with col5:
        infra_risks = [r for r in (reasoning_store.risks if reasoning_store else []) if getattr(r, 'domain', '').lower() == 'infrastructure']
        st.metric("Related Risks", len(infra_risks))

    st.divider()

    # Categories Grid
    st.subheader("Categories")
    cat_cols = st.columns(4)
    for i, (cat_name, cat_facts) in enumerate(sorted(categories.items(), key=lambda x: -len(x[1]))):
        with cat_cols[i % 4]:
            icon = cat_icons.get(cat_name, '📦')
            display_name = cat_name.replace('_', ' ').title()
            st.markdown(f'''
            <div style="background: var(--bg-surface, #1a1a2e); border: 1px solid var(--border-default, #333); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="font-size: 2em;">{icon}</div>
                    <div>
                        <div style="font-weight: 600;">{display_name}</div>
                        <div style="color: #888; font-size: 0.9em;">{len(cat_facts)} items</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

    st.divider()

    # Cloud Platforms Section
    cloud_facts = categories.get('cloud', [])
    if cloud_facts:
        st.subheader("☁️ Cloud Infrastructure")
        cloud_cols = st.columns(3)
        for i, fact in enumerate(cloud_facts[:6]):
            with cloud_cols[i % 3]:
                item = str(getattr(fact, 'item', 'Cloud Item') or 'Cloud Item')
                details = str(getattr(fact, 'details', '') or '')
                # Detect cloud provider
                item_lower = item.lower()
                if 'aws' in item_lower or 'amazon' in item_lower:
                    provider = "☁️ AWS"
                    bg_color = "#fff7ed"
                    border_color = "#fed7aa"
                elif 'azure' in item_lower or 'microsoft' in item_lower:
                    provider = "☁️ Azure"
                    bg_color = "#eff6ff"
                    border_color = "#bfdbfe"
                elif 'gcp' in item_lower or 'google' in item_lower:
                    provider = "☁️ GCP"
                    bg_color = "#f0fdf4"
                    border_color = "#bbf7d0"
                else:
                    provider = "☁️"
                    bg_color = "#f0f9ff"
                    border_color = "#bae6fd"

                details_html = f'<div style="font-size: 0.8em; color: #64748b; margin-top: 5px;">{details[:60]}...</div>' if details else ''
                st.markdown(f'''
                <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 15px; margin-bottom: 10px;">
                    <div style="font-weight: bold; color: #0369a1; margin-bottom: 5px;">{provider}</div>
                    <div style="font-size: 0.95em; color: #0c4a6e;">{item[:50]}{"..." if len(item) > 50 else ""}</div>
                    {details_html}
                </div>
                ''', unsafe_allow_html=True)

    # Data Centers / Hosting Section
    hosting_facts = categories.get('hosting', [])
    if hosting_facts:
        st.subheader("🏢 Data Centers & Hosting")
        for fact in hosting_facts:
            item = str(getattr(fact, 'item', 'Data Center') or 'Data Center')
            details = str(getattr(fact, 'details', '') or '')
            source = str(getattr(fact, 'source_document', '') or '')
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{item}**")
                    if details:
                        st.caption(details[:150])
                with col2:
                    if source:
                        st.caption(f"📄 {source[:20]}...")
            st.divider()

    # Full Infrastructure Table
    st.subheader("📋 All Infrastructure Items")

    # Create dataframe for table display
    import pandas as pd
    table_data = []
    for fact in infra_facts:
        item = str(getattr(fact, 'item', 'N/A') or 'N/A')
        details = str(getattr(fact, 'details', '') or '')
        source = str(getattr(fact, 'source_document', '') or '')
        category = str(getattr(fact, 'category', 'general') or 'general')
        conf_score = getattr(fact, 'confidence_score', 0) or 0

        table_data.append({
            'Item': item[:50],
            'Category': category.replace('_', ' ').title(),
            'Details': details[:40],
            'Source': source[:20],
            'Confidence': f"{int(conf_score * 100)}%"
        })

    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Detailed view by category
    st.divider()
    st.subheader("📁 Detailed View by Category")
    for cat_name, cat_facts in sorted(categories.items(), key=lambda x: -len(x[1])):
        icon = cat_icons.get(cat_name, '📦')
        display_name = cat_name.replace('_', ' ').title()
        with st.expander(f"{icon} {display_name} ({len(cat_facts)} items)", expanded=False):
            for fact in cat_facts:
                item = getattr(fact, 'item', 'N/A')
                details = getattr(fact, 'details', '')
                evidence = getattr(fact, 'evidence', '')
                source = getattr(fact, 'source_document', '')
                confidence = getattr(fact, 'confidence_score', 0)

                st.markdown(f"**• {item}**")
                if details:
                    st.write(details)
                if evidence:
                    st.markdown(f"*Evidence: \"{evidence[:100]}...\"*" if len(evidence) > 100 else f"*Evidence: \"{evidence}\"*")
                if source:
                    st.caption(f"📄 Source: {source}")

                # Confidence indicator
                conf_pct = int(confidence * 100)
                if conf_pct >= 80:
                    st.progress(confidence, text=f"Confidence: {conf_pct}% ✓")
                elif conf_pct >= 50:
                    st.progress(confidence, text=f"Confidence: {conf_pct}%")
                else:
                    st.progress(max(0.05, confidence), text=f"Confidence: {conf_pct}% ⚠️")
                st.write("")

# =============================================================================
# MAIN ROUTER
# =============================================================================
def main():
    page = st.session_state.get("page", "welcome")

    if page == "welcome":
        page_welcome()
    elif page == "upload":
        page_upload()
    elif page == "processing":
        page_processing()
    elif page == "dashboard":
        page_dashboard()
    elif page == "risks":
        page_risks()
    elif page == "work_items":
        page_work_items()
    elif page == "questions":
        page_questions()
    elif page == "facts":
        page_facts()
    elif page == "gaps":
        page_gaps()
    elif page == "organization":
        page_organization()
    elif page == "applications":
        page_applications()
    elif page == "infrastructure":
        page_infrastructure()
    else:
        page_welcome()

if __name__ == "__main__":
    main()
