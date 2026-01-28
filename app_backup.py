"""
IT Due Diligence Agent - Streamlit UI
Exact copy of Flask app UI/UX from localhost:5001
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# =============================================================================
# PAGE CONFIG (must be first Streamlit command)
# =============================================================================
st.set_page_config(
    page_title="IT Due Diligence",
    page_icon="DD",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# IMPORTS
# =============================================================================
try:
    from config_v2 import ANTHROPIC_API_KEY, OUTPUT_DIR, FACTS_DIR, FINDINGS_DIR, INPUT_DIR
    from tools_v2.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore
    from tools_v2.session import DealType, DEAL_TYPE_CONFIG
    CONFIG_LOADED = True
except ImportError as e:
    CONFIG_LOADED = False
    IMPORT_ERROR = str(e)

# =============================================================================
# PHASE 1: CSS DESIGN SYSTEM (Steps 1-5)
# Exact copy of Flask tokens.css
# =============================================================================
CSS_TOKENS = """
<style>
/* ===================================================================
   STEP 1-2: Design Tokens (exact copy from Flask tokens.css)
   =================================================================== */
:root {
    /* Background layers */
    --bg-base: #fafaf9;
    --bg-surface: #ffffff;
    --bg-surface-raised: #ffffff;
    --bg-surface-sunken: #f5f5f4;
    --bg-overlay: rgba(0, 0, 0, 0.4);

    /* Border colors */
    --border-default: #e7e5e4;
    --border-muted: #d6d3d1;

    /* Text colors */
    --text-primary: #1c1917;
    --text-secondary: #44403c;
    --text-muted: #78716c;
    --text-inverse: #ffffff;

    /* Accent (Orange) */
    --accent: #f97316;
    --accent-hover: #ea580c;
    --accent-active: #c2410c;
    --accent-subtle: #fff7ed;

    /* Semantic colors */
    --critical: #dc2626;
    --critical-bg: #fef2f2;
    --high: #ea580c;
    --high-bg: #fff7ed;
    --medium: #ca8a04;
    --medium-bg: #fefce8;
    --low: #16a34a;
    --low-bg: #f0fdf4;
    --info: #0284c7;
    --info-bg: #f0f9ff;

    /* Typography */
    --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    --font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;

    --text-xs: 0.75rem;
    --text-sm: 0.875rem;
    --text-base: 1rem;
    --text-lg: 1.125rem;
    --text-xl: 1.25rem;
    --text-2xl: 1.5rem;
    --text-3xl: 1.875rem;

    --font-normal: 400;
    --font-medium: 500;
    --font-semibold: 600;
    --font-bold: 700;

    --leading-tight: 1.25;
    --leading-normal: 1.5;
    --leading-relaxed: 1.625;

    /* Spacing */
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-5: 1.25rem;
    --space-6: 1.5rem;
    --space-8: 2rem;
    --space-10: 2.5rem;
    --space-12: 3rem;

    /* Border radius */
    --radius-sm: 0.25rem;
    --radius-md: 0.375rem;
    --radius-lg: 0.5rem;
    --radius-xl: 0.75rem;
    --radius-full: 9999px;

    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);

    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-base: 200ms ease;
    --transition-slow: 300ms ease;

    /* Layout */
    --nav-height: 56px;
    --container-max: 1280px;
    --drawer-width: 480px;

    /* Z-index */
    --z-dropdown: 50;
    --z-sticky: 100;
    --z-drawer: 200;
    --z-modal: 300;
}

/* ===================================================================
   STEP 3: Hide ALL Streamlit default elements
   =================================================================== */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
header[data-testid="stHeader"] {display: none !important;}
.stDeployButton {display: none !important;}
section[data-testid="stSidebar"] {display: none !important;}
.block-container {padding-top: 0 !important; max-width: 100% !important;}
div[data-testid="stToolbar"] {display: none !important;}
div[data-testid="stDecoration"] {display: none !important;}
div[data-testid="stStatusWidget"] {display: none !important;}

/* ===================================================================
   STEP 4-5: Base styles
   =================================================================== */
* {
    box-sizing: border-box;
}

.stApp {
    background: var(--bg-base) !important;
    font-family: var(--font-sans);
}

/* ===================================================================
   STEP 6-15: Top Navigation Bar
   =================================================================== */
.top-nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: var(--z-sticky);
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border-default);
    height: var(--nav-height);
    display: flex;
    align-items: center;
    padding: 0 var(--space-6);
    gap: var(--space-8);
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-weight: var(--font-bold);
    font-size: var(--text-lg);
    color: var(--text-primary);
    text-decoration: none;
}

.nav-brand-icon {
    width: 28px;
    height: 28px;
    background: var(--accent);
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: var(--text-sm);
    font-weight: var(--font-bold);
}

.nav-links {
    display: flex;
    gap: var(--space-1);
}

.nav-link {
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    font-weight: var(--font-medium);
    color: var(--text-secondary);
    text-decoration: none;
    cursor: pointer;
    transition: all var(--transition-fast);
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

.nav-search {
    margin-left: auto;
    position: relative;
}

.nav-search input {
    width: 240px;
    padding: var(--space-2) var(--space-3);
    padding-left: var(--space-8);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    background: var(--bg-surface-sunken);
    transition: all var(--transition-fast);
}

.nav-search input:focus {
    outline: none;
    background: var(--bg-surface);
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-subtle);
}

.nav-search-icon {
    position: absolute;
    left: var(--space-3);
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    pointer-events: none;
}

/* ===================================================================
   STEP 16-20: Page Layout
   =================================================================== */
.main-container {
    max-width: var(--container-max);
    margin: 0 auto;
    padding: var(--space-6);
    padding-top: calc(var(--nav-height) + var(--space-6));
}

.page-header {
    margin-bottom: var(--space-6);
}

.page-header h1 {
    font-size: var(--text-2xl);
    font-weight: var(--font-bold);
    color: var(--text-primary);
    margin: 0 0 var(--space-1) 0;
    line-height: var(--leading-tight);
}

.page-header p {
    color: var(--text-muted);
    font-size: var(--text-sm);
    margin: 0;
}

.page-header-actions {
    display: flex;
    gap: var(--space-2);
    align-items: center;
}

/* ===================================================================
   PHASE 2: METRICS & CARDS (Steps 21-40)
   =================================================================== */

/* Step 21-28: Metrics Row */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-4);
    margin-bottom: var(--space-6);
}

@media (max-width: 1024px) {
    .metrics-row { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
    .metrics-row { grid-template-columns: 1fr; }
}

.metric-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    padding: var(--space-5);
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
}

.metric-card.metric-warning {
    border-left: 3px solid var(--critical);
}

.metric-label {
    font-size: var(--text-sm);
    color: var(--text-muted);
    font-weight: var(--font-medium);
}

.metric-value {
    font-size: var(--text-3xl);
    font-weight: var(--font-bold);
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
}

.metric-card.metric-warning .metric-value {
    color: var(--critical);
}

.metric-subtext {
    font-size: var(--text-xs);
    color: var(--text-muted);
}

/* Step 29-40: Cards */
.card {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    margin-bottom: var(--space-4);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4) var(--space-5);
    border-bottom: 1px solid var(--border-default);
}

.card-title {
    font-size: var(--text-base);
    font-weight: var(--font-semibold);
    color: var(--text-primary);
    margin: 0;
}

.card-body {
    padding: var(--space-5);
}

.card-body.no-padding {
    padding: 0;
}

.card-link {
    color: var(--accent);
    text-decoration: none;
    font-size: var(--text-sm);
    font-weight: var(--font-medium);
}

.card-link:hover {
    color: var(--accent-hover);
    text-decoration: underline;
}

/* Domain badges */
.domain-badges {
    display: flex;
    gap: var(--space-2);
    flex-wrap: wrap;
}

.domain-badge {
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    font-weight: var(--font-medium);
}

.domain-badge.covered {
    background: var(--low-bg);
    color: var(--low);
}

.domain-badge.missing {
    background: transparent;
    border: 1px solid var(--border-default);
    color: var(--text-muted);
}

/* ===================================================================
   PHASE 3: TABLES (Steps 41-65)
   =================================================================== */
.table-container {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    overflow: hidden;
}

.table-container.no-border {
    border: none;
    border-radius: 0;
    box-shadow: none;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th {
    padding: var(--space-3) var(--space-4);
    text-align: left;
    font-size: var(--text-xs);
    font-weight: var(--font-semibold);
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: var(--bg-surface-sunken);
    border-bottom: 1px solid var(--border-default);
}

.data-table td {
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--border-default);
    font-size: var(--text-sm);
    color: var(--text-secondary);
}

.data-table tbody tr {
    cursor: pointer;
    transition: background var(--transition-fast);
}

.data-table tbody tr:hover {
    background: var(--bg-surface-sunken);
}

.data-table tbody tr.selected {
    background: var(--accent-subtle);
}

.data-table tbody tr:last-child td {
    border-bottom: none;
}

.data-table tfoot {
    background: var(--bg-surface-sunken);
}

.data-table tfoot td {
    font-weight: var(--font-semibold);
    border-bottom: none;
}

.text-right {
    text-align: right !important;
}

.text-muted {
    color: var(--text-muted);
}

.font-mono {
    font-family: var(--font-mono);
}

.truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 200px;
    display: inline-block;
}

.cost-range {
    font-family: var(--font-mono);
    font-size: var(--text-sm);
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: var(--space-12) var(--space-6);
    color: var(--text-muted);
}

.empty-state-icon {
    font-size: 2.5rem;
    margin-bottom: var(--space-4);
}

.empty-state-title {
    font-size: var(--text-lg);
    font-weight: var(--font-semibold);
    color: var(--text-primary);
    margin-bottom: var(--space-2);
}

.empty-state-text {
    font-size: var(--text-sm);
    max-width: 400px;
    margin: 0 auto;
}

/* ===================================================================
   PHASE 4: BADGES & BUTTONS (Steps 66-85)
   =================================================================== */

/* Badges */
.badge {
    display: inline-flex;
    align-items: center;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-full);
    font-size: var(--text-xs);
    font-weight: var(--font-semibold);
    text-transform: uppercase;
    letter-spacing: 0.025em;
}

.badge-critical { background: var(--critical-bg); color: var(--critical); }
.badge-high { background: var(--high-bg); color: var(--high); }
.badge-medium { background: var(--medium-bg); color: var(--medium); }
.badge-low { background: var(--low-bg); color: var(--low); }
.badge-info { background: var(--info-bg); color: var(--info); }
.badge-success { background: var(--low-bg); color: var(--low); }

.badge-day1 { background: var(--critical-bg); color: var(--critical); }
.badge-day100 { background: var(--high-bg); color: var(--high); }
.badge-post100 { background: var(--info-bg); color: var(--info); }

.badge-outline {
    background: transparent;
    border: 1px solid currentColor;
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    font-weight: var(--font-medium);
    cursor: pointer;
    border: none;
    text-decoration: none;
    transition: all var(--transition-fast);
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background: var(--accent);
    color: var(--text-inverse);
}

.btn-primary:hover:not(:disabled) {
    background: var(--accent-hover);
}

.btn-secondary {
    background: var(--bg-surface);
    color: var(--text-primary);
    border: 1px solid var(--border-default);
}

.btn-secondary:hover:not(:disabled) {
    background: var(--bg-surface-sunken);
}

.btn-sm {
    padding: var(--space-1) var(--space-2);
    font-size: var(--text-xs);
}

.btn-lg {
    padding: var(--space-3) var(--space-6);
    font-size: var(--text-base);
}

/* ===================================================================
   PHASE 5: FILTERS & FORMS (Steps 86-100)
   =================================================================== */
.filters-bar {
    display: flex;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-4);
    flex-wrap: wrap;
    align-items: flex-end;
}

.filter-group {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
}

.filter-label {
    font-size: var(--text-xs);
    font-weight: var(--font-semibold);
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.025em;
}

.filter-select, .filter-input {
    padding: var(--space-2) var(--space-3);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    background: var(--bg-surface);
    color: var(--text-primary);
    min-width: 140px;
}

.filter-select:focus, .filter-input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-subtle);
}

.filter-search {
    flex: 1;
    min-width: 200px;
}

.filters-actions {
    margin-left: auto;
    display: flex;
    gap: var(--space-2);
}

/* Grid layouts */
.grid { display: grid; }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.gap-4 { gap: var(--space-4); }
.mt-4 { margin-top: var(--space-4); }
.mb-4 { margin-bottom: var(--space-4); }

.flex { display: flex; }
.flex-wrap { flex-wrap: wrap; }
.items-center { align-items: center; }
.items-start { align-items: flex-start; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: var(--space-2); }
.gap-3 { gap: var(--space-3); }

/* Quick actions row */
.actions-row {
    display: flex;
    gap: var(--space-3);
    margin-top: var(--space-4);
    flex-wrap: wrap;
}

/* Hide Streamlit native nav buttons */
div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) {
    display: none !important;
}

/* Style any remaining Streamlit elements to match */
.stButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    font-weight: var(--font-medium) !important;
    padding: var(--space-2) var(--space-4) !important;
}

.stButton > button:hover {
    background: var(--accent-hover) !important;
}

.stSelectbox > div > div {
    border-color: var(--border-default) !important;
    border-radius: var(--radius-md) !important;
}

.stTextInput > div > div > input {
    border-color: var(--border-default) !important;
    border-radius: var(--radius-md) !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-subtle) !important;
}

.stTextArea > div > div > textarea {
    border-color: var(--border-default) !important;
    border-radius: var(--radius-md) !important;
}

.stCheckbox {
    color: var(--text-primary);
}

.stFileUploader > div {
    border-color: var(--border-default) !important;
    border-radius: var(--radius-lg) !important;
}

/* ===================================================================
   STREAMLIT NATIVE COMPONENT OVERRIDES
   =================================================================== */

/* st.metric styling */
div[data-testid="stMetric"] {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
}

div[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
    font-size: var(--text-sm) !important;
    font-weight: var(--font-medium) !important;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-size: var(--text-3xl) !important;
    font-weight: var(--font-bold) !important;
}

/* st.dataframe styling */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    overflow: hidden;
}

div[data-testid="stDataFrame"] thead th {
    background: var(--bg-surface-sunken) !important;
    color: var(--text-muted) !important;
    font-size: var(--text-xs) !important;
    font-weight: var(--font-semibold) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* st.tabs styling */
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    color: var(--text-secondary);
    font-weight: var(--font-medium);
    padding: var(--space-2) var(--space-4);
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}

/* st.expander styling */
div[data-testid="stExpander"] {
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    background: var(--bg-surface);
}

div[data-testid="stExpander"] summary {
    font-weight: var(--font-medium);
}

/* Detail panel styling */
.detail-panel {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    padding: var(--space-5);
    height: fit-content;
    position: sticky;
    top: calc(var(--nav-height) + var(--space-4));
}

.detail-panel-title {
    font-size: var(--text-lg);
    font-weight: var(--font-semibold);
    color: var(--text-primary);
    margin-bottom: var(--space-4);
    padding-bottom: var(--space-3);
    border-bottom: 1px solid var(--border-default);
}

.detail-section {
    margin-bottom: var(--space-5);
}

.detail-section-title {
    font-size: var(--text-xs);
    font-weight: var(--font-semibold);
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: var(--space-2);
}

.detail-section-content {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    line-height: var(--leading-relaxed);
}

/* Stat card for organization */
.stat-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    text-align: center;
}

.stat-card.highlight {
    border-color: var(--accent);
    background: var(--accent-subtle);
}

.stat-value {
    font-size: var(--text-2xl);
    font-weight: var(--font-bold);
    color: var(--text-primary);
    display: block;
}

.stat-label {
    font-size: var(--text-xs);
    color: var(--text-muted);
    text-transform: uppercase;
}

/* Nav card for organization */
.nav-card {
    display: flex;
    gap: var(--space-4);
    padding: var(--space-5);
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    text-decoration: none;
    color: inherit;
    transition: all var(--transition-fast);
    cursor: pointer;
}

.nav-card:hover {
    border-color: var(--accent);
    box-shadow: var(--shadow-md);
}

.nav-card-icon {
    font-size: 2rem;
}

.nav-card-content h3 {
    margin: 0 0 var(--space-1) 0;
    font-size: var(--text-base);
    font-weight: var(--font-semibold);
}

.nav-card-content p {
    margin: 0 0 var(--space-2) 0;
    font-size: var(--text-sm);
    color: var(--text-muted);
}

.nav-card-stat {
    font-size: var(--text-xs);
    color: var(--text-secondary);
}

/* Activity diagram cards */
.activity-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
}

.activity-card.active {
    border-color: var(--accent);
    background: var(--accent-subtle);
}

.activity-icon {
    font-size: 1.5rem;
    margin-bottom: var(--space-2);
}

.activity-name {
    font-weight: var(--font-semibold);
    margin-bottom: var(--space-2);
}

.activity-tasks {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    padding-left: var(--space-4);
    margin: var(--space-2) 0;
}

/* Tier cards for review */
.tier-card {
    background: var(--bg-surface-sunken);
    border-radius: var(--radius-lg);
    padding: var(--space-5);
    text-align: center;
    border: 2px solid transparent;
}

.tier-card.tier1 {
    border-color: var(--low);
    background: var(--low-bg);
}

.tier-card.tier2 {
    border-color: var(--info);
    background: var(--info-bg);
}

.tier-card.tier3 {
    border-color: var(--critical);
    background: var(--critical-bg);
}

.tier-count {
    font-size: var(--text-3xl);
    font-weight: var(--font-bold);
}

/* Upload zone */
.upload-zone {
    border: 2px dashed var(--border-default);
    border-radius: var(--radius-lg);
    padding: var(--space-10);
    text-align: center;
    transition: all var(--transition-fast);
}

.upload-zone:hover {
    border-color: var(--accent);
    background: var(--accent-subtle);
}

/* Change badges for documents */
.change-badge {
    display: inline-flex;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: var(--font-semibold);
}

.change-badge.new {
    background: var(--low-bg);
    color: var(--low);
}

.change-badge.updated {
    background: var(--info-bg);
    color: var(--info);
}

.change-badge.conflict {
    background: var(--critical-bg);
    color: var(--critical);
}

/* Conflict card */
.conflict-card {
    background: var(--bg-surface);
    border: 1px solid var(--critical);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    margin-bottom: var(--space-3);
}
</style>
"""

# =============================================================================
# NAVIGATION PAGES
# =============================================================================
PAGES = [
    ("dashboard", "Dashboard"),
    ("risks", "Risks"),
    ("work_items", "Work Items"),
    ("questions", "Questions"),
    ("facts", "Facts"),
    ("gaps", "Gaps"),
    ("organization", "Organization"),
    ("applications", "Applications"),
    ("infrastructure", "Infrastructure"),
    ("review", "Review"),
    ("documents", "Documents"),
    ("upload", "Upload"),
]

# Organization sub-pages
ORG_SUBPAGES = [
    ("org_overview", "Overview"),
    ("org_staffing", "Staffing Census"),
    ("org_benchmark", "Benchmark"),
    ("org_msp", "MSP Dependencies"),
    ("org_shared", "Shared Services"),
]


# =============================================================================
# REUSABLE COMPONENT FUNCTIONS
# =============================================================================

def severity_badge(severity: str) -> str:
    """Return HTML for a severity badge."""
    if not severity:
        return '<span class="badge badge-info">N/A</span>'
    return f'<span class="badge badge-{severity.lower()}">{severity.upper()}</span>'


def phase_badge(phase: str) -> str:
    """Return HTML for a phase badge."""
    if not phase:
        return ""
    phase_key = phase.lower().replace("_", "").replace(" ", "")
    display = phase.replace("_", " ")
    return f'<span class="badge badge-{phase_key}">{display}</span>'


def status_badge(status: str) -> str:
    """Return HTML for a status badge."""
    badge_map = {
        "documented": ("success", "✓"),
        "partial": ("medium", "~"),
        "gap": ("critical", "✗"),
    }
    variant, icon = badge_map.get(status, ("info", "?"))
    return f'<span class="badge badge-{variant}">{icon}</span>'


def render_filters(page_key: str, filter_specs: list) -> dict:
    """
    Render a filter bar with Streamlit widgets.

    filter_specs: list of dicts with keys: key, label, options
    Returns: dict of filter values
    """
    filters = {}

    # Create filter bar container
    st.markdown('<div class="filters-bar" style="display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end; padding: 1rem; background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: 0.5rem; margin-bottom: 1rem;">', unsafe_allow_html=True)

    cols = st.columns(len(filter_specs) + 1)  # +1 for search

    for i, spec in enumerate(filter_specs):
        with cols[i]:
            st.markdown(f'<span class="filter-label">{spec["label"]}</span>', unsafe_allow_html=True)
            filters[spec["key"]] = st.selectbox(
                spec["label"],
                spec["options"],
                key=f"{page_key}_{spec['key']}",
                label_visibility="collapsed"
            )

    with cols[-1]:
        st.markdown('<span class="filter-label">Search</span>', unsafe_allow_html=True)
        filters["search"] = st.text_input(
            "Search",
            key=f"{page_key}_search",
            label_visibility="collapsed",
            placeholder="Search..."
        )

    st.markdown('</div>', unsafe_allow_html=True)

    return filters


def apply_filters(data: list, filters: dict, search_fields: list = None) -> list:
    """Apply filter values to a list of data objects."""
    filtered = data

    # Apply dropdown filters
    for key, value in filters.items():
        if key == "search":
            continue
        if value and value != "All":
            filtered = [item for item in filtered if getattr(item, key, None) == value.lower().replace(" ", "_")]

    # Apply search
    if filters.get("search") and search_fields:
        search_term = filters["search"].lower()
        filtered = [
            item for item in filtered
            if any(search_term in str(getattr(item, field, "")).lower() for field in search_fields)
        ]

    return filtered


def render_detail_panel(title: str, sections: list):
    """
    Render a detail panel with sections.

    sections: list of dicts with keys: title, content (can be HTML or text)
    """
    html = f'''
    <div class="detail-panel">
        <div class="detail-panel-title">{title}</div>
    '''

    for section in sections:
        html += f'''
        <div class="detail-section">
            <div class="detail-section-title">{section["title"]}</div>
            <div class="detail-section-content">{section["content"]}</div>
        </div>
        '''

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_stat_cards(stats: list):
    """
    Render a row of stat cards.

    stats: list of dicts with keys: value, label, highlight (optional)
    """
    cols = st.columns(len(stats))
    for i, stat in enumerate(stats):
        with cols[i]:
            highlight = "highlight" if stat.get("highlight") else ""
            st.markdown(f'''
            <div class="stat-card {highlight}">
                <span class="stat-value">{stat["value"]}</span>
                <span class="stat-label">{stat["label"]}</span>
            </div>
            ''', unsafe_allow_html=True)


def render_nav_cards(cards: list):
    """
    Render navigation cards for module sub-pages.

    cards: list of dicts with keys: icon, title, description, stat, page_key
    """
    cols = st.columns(2)
    for i, card in enumerate(cards):
        with cols[i % 2]:
            if st.button(f"{card['icon']} {card['title']}", key=f"nav_card_{card['page_key']}", use_container_width=True):
                st.session_state["org_subpage"] = card["page_key"]
                st.rerun()
            st.markdown(f'''
            <div style="margin-top: -0.5rem; margin-bottom: 1rem; padding: 0 0.5rem;">
                <p style="font-size: 0.875rem; color: var(--text-muted); margin: 0;">{card["description"]}</p>
                <span style="font-size: 0.75rem; color: var(--text-secondary);">{card.get("stat", "")}</span>
            </div>
            ''', unsafe_allow_html=True)


def render_activity_cards(activities: list):
    """Render IT activity/support cards."""
    cols = st.columns(3)
    for i, activity in enumerate(activities):
        with cols[i % 3]:
            active_class = "active" if activity.get("active") else ""
            tasks_html = "".join([f"<li>{task}</li>" for task in activity.get("tasks", [])])
            st.markdown(f'''
            <div class="activity-card {active_class}">
                <div class="activity-icon">{activity["icon"]}</div>
                <div class="activity-name">{activity["name"]}</div>
                <ul class="activity-tasks">{tasks_html}</ul>
            </div>
            ''', unsafe_allow_html=True)


def render_tier_cards(tiers: list):
    """Render tier cards for review queue."""
    cols = st.columns(3)
    for i, tier in enumerate(tiers):
        with cols[i]:
            st.markdown(f'''
            <div class="tier-card tier{tier["number"]}">
                <div style="font-weight: 600; margin-bottom: 0.5rem;">Tier {tier["number"]}: {tier["name"]}</div>
                <div class="tier-count">{tier["count"]}</div>
                <div style="font-size: 0.875rem; color: var(--text-muted); margin: 0.5rem 0;">{tier["description"]}</div>
            </div>
            ''', unsafe_allow_html=True)
            if tier["count"] > 0 and tier.get("action_label"):
                if st.button(tier["action_label"], key=f"tier_{tier['number']}_action", use_container_width=True):
                    if tier.get("action_callback"):
                        tier["action_callback"]()


def render_nav_bar():
    """Render the top navigation bar (Steps 6-15)."""
    if "page" not in st.session_state:
        st.session_state["page"] = "dashboard"

    current_page = st.session_state.get("page", "dashboard")

    # Static header HTML (brand + search)
    nav_html = '''
    <div class="top-nav">
        <div class="nav-brand">
            <span class="nav-brand-icon">DD</span>
            <span>IT Due Diligence</span>
        </div>
        <div style="flex: 1;"></div>
        <div class="nav-search">
            <svg class="nav-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input type="text" placeholder="Search findings..." />
        </div>
    </div>
    <div style="height: 56px;"></div>
    '''
    st.markdown(nav_html, unsafe_allow_html=True)

    # Functional navigation using Streamlit buttons
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div > div > div > button {
        background: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 0.5rem 0.75rem !important;
        border-radius: 6px !important;
        margin: 0 !important;
        width: auto !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div > div > div > button:hover {
        background: var(--bg-surface-sunken) !important;
        color: var(--text-primary) !important;
    }
    .nav-button-row {
        display: flex;
        gap: 0.25rem;
        padding: 0.5rem 1rem;
        background: var(--bg-surface);
        border-bottom: 1px solid var(--border-default);
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create button columns for navigation
    cols = st.columns(len(PAGES))
    for i, (page_id, label) in enumerate(PAGES):
        with cols[i]:
            button_type = "primary" if page_id == current_page else "secondary"
            if st.button(label, key=f"nav_{page_id}", type=button_type, use_container_width=True):
                st.session_state["page"] = page_id
                st.rerun()


def page_header(title: str, subtitle: str, actions_html: str = ""):
    """Render page header (Steps 16-20)."""
    html = f'''
    <div class="page-header">
        <div class="flex justify-between items-start">
            <div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            {actions_html}
        </div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# DATA LOADING
# =============================================================================
def load_data():
    """Load fact store and reasoning store."""
    fact_store = st.session_state.get("fact_store")
    reasoning_store = st.session_state.get("reasoning_store")

    if fact_store is None:
        output_dir = Path("output")
        if output_dir.exists():
            facts_files = sorted(output_dir.glob("facts_*.json"), reverse=True)
            if facts_files:
                try:
                    fact_store = FactStore()
                    fact_store.load(str(facts_files[0]))
                    st.session_state["fact_store"] = fact_store
                except:
                    pass

    if reasoning_store is None:
        output_dir = Path("output")
        if output_dir.exists():
            findings_files = sorted(output_dir.glob("findings_*.json"), reverse=True)
            if findings_files:
                try:
                    reasoning_store = ReasoningStore()
                    reasoning_store.load(str(findings_files[0]))
                    st.session_state["reasoning_store"] = reasoning_store
                except:
                    pass

    return fact_store, reasoning_store


# =============================================================================
# COMPONENT HELPERS
# =============================================================================
def metrics_row(metrics: list):
    """Render metrics row (Steps 21-28)."""
    html = '<div class="metrics-row">'
    for m in metrics:
        warning_class = "metric-warning" if m.get("warning") else ""
        subtext = f'<span class="metric-subtext">{m.get("subtext", "")}</span>' if m.get("subtext") else ""
        html += f'''
        <div class="metric-card {warning_class}">
            <span class="metric-label">{m["label"]}</span>
            <span class="metric-value">{m["value"]}</span>
            {subtext}
        </div>
        '''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def badge(text: str, variant: str = "info"):
    """Return badge HTML."""
    return f'<span class="badge badge-{variant}">{text}</span>'


def data_table(headers: list, rows: list, footer: list = None):
    """Render a data table (Steps 41-56)."""
    header_html = "".join([f'<th>{h}</th>' for h in headers])

    rows_html = ""
    for row in rows:
        cells = "".join([f'<td>{cell}</td>' for cell in row])
        rows_html += f'<tr>{cells}</tr>'

    footer_html = ""
    if footer:
        footer_cells = "".join([f'<td>{cell}</td>' for cell in footer])
        footer_html = f'<tfoot><tr>{footer_cells}</tr></tfoot>'

    html = f'''
    <table class="data-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
        {footer_html}
    </table>
    '''
    return html


def empty_state(icon: str, title: str, text: str):
    """Render empty state."""
    return f'''
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-text">{text}</div>
    </div>
    '''


def card_start(title: str, link_text: str = None, link_href: str = "#"):
    """Start a card component."""
    link_html = f'<a href="{link_href}" class="card-link">{link_text}</a>' if link_text else ""
    return f'''
    <div class="card">
        <div class="card-header">
            <span class="card-title">{title}</span>
            {link_html}
        </div>
        <div class="card-body no-padding">
    '''


def card_end():
    """End a card component."""
    return '</div></div>'


# =============================================================================
# PAGE: DASHBOARD (Steps 101-105)
# =============================================================================
def page_dashboard():
    fact_store, reasoning_store = load_data()

    # Header with action button
    col_title, col_action = st.columns([4, 1])
    with col_title:
        st.markdown('''
        <div class="page-header">
            <h1>Analysis Dashboard</h1>
            <p>Overview of IT due diligence findings for this deal</p>
        </div>
        ''', unsafe_allow_html=True)
    with col_action:
        if st.button("New Analysis", type="secondary", use_container_width=True):
            st.session_state["page"] = "upload"
            st.rerun()

    # Check for data
    facts_count = len(fact_store.facts) if fact_store else 0
    risks_count = len(reasoning_store.risks) if reasoning_store else 0

    if facts_count == 0 and risks_count == 0:
        st.markdown(f'''
        <div class="card" style="text-align: center; padding: 60px 40px;">
            <div style="font-size: 4em; margin-bottom: 20px;">📊</div>
            <h2 style="margin-bottom: 10px;">No Analysis Results</h2>
            <p class="text-muted" style="margin-bottom: 30px; max-width: 400px; margin-left: auto; margin-right: auto;">
                Upload documents to start analyzing IT infrastructure, security, applications, and organization.
            </p>
        </div>
        ''', unsafe_allow_html=True)

        if st.button("Upload Documents", type="primary"):
            st.session_state["page"] = "upload"
            st.rerun()
        return

    # Calculate metrics
    gaps_count = len(fact_store.gaps) if fact_store else 0
    work_items_count = len(reasoning_store.work_items) if reasoning_store else 0
    critical_risks = len([r for r in reasoning_store.risks if r.severity == "critical"]) if reasoning_store else 0
    high_risks = len([r for r in reasoning_store.risks if r.severity == "high"]) if reasoning_store else 0
    day1_count = len([w for w in reasoning_store.work_items if w.phase == "Day_1"]) if reasoning_store else 0
    domains_with_facts = list(set(f.domain for f in fact_store.facts)) if fact_store else []

    # Native Streamlit metrics row
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Facts Discovered",
            facts_count,
            help=f"Across {len(domains_with_facts)} domains"
        )

    with m2:
        st.metric(
            "Information Gaps",
            gaps_count,
            delta=f"{gaps_count - 10} above threshold" if gaps_count > 10 else None,
            delta_color="inverse" if gaps_count > 10 else "off"
        )

    with m3:
        risk_delta = f"{critical_risks} critical" if critical_risks > 0 else None
        st.metric(
            "Risks Identified",
            risks_count,
            delta=risk_delta,
            delta_color="inverse" if critical_risks > 0 else "off"
        )

    with m4:
        st.metric(
            "Work Items",
            work_items_count,
            help=f"{day1_count} for Day 1"
        )

    # Domain coverage card
    all_domains = ['infrastructure', 'network', 'cybersecurity', 'applications', 'identity_access', 'organization']
    badges_html = '<div class="domain-badges">'
    for domain in all_domains:
        covered = domain in domains_with_facts
        badge_class = "covered" if covered else "missing"
        icon = "✓" if covered else "○"
        badges_html += f'<span class="domain-badge {badge_class}">{icon} {domain.replace("_", " ").title()}</span>'
    badges_html += '</div>'

    st.markdown(f'''
    <div class="card">
        <div class="card-header"><span class="card-title">Domain Coverage</span></div>
        <div class="card-body">{badges_html}</div>
    </div>
    ''', unsafe_allow_html=True)

    # Two column grid for Cost Summary and Top Risks
    import pandas as pd

    cost_col, risks_col = st.columns(2)

    # Cost Summary Card
    with cost_col:
        st.markdown('''<div class="card"><div class="card-header"><span class="card-title">Cost Summary</span></div><div class="card-body">''', unsafe_allow_html=True)

        cost_data = {"Day_1": {"count": 0, "low": 0, "high": 0}, "Day_100": {"count": 0, "low": 0, "high": 0}, "Post_100": {"count": 0, "low": 0, "high": 0}}
        if reasoning_store:
            for wi in reasoning_store.work_items:
                phase = wi.phase or "Day_100"
                if phase in cost_data:
                    cost_data[phase]["count"] += 1
                    cost_data[phase]["low"] += getattr(wi, "cost_low", 0) or 0
                    cost_data[phase]["high"] += getattr(wi, "cost_high", 0) or 0

        cost_df_data = []
        total_count, total_low, total_high = 0, 0, 0
        for phase in ["Day_1", "Day_100", "Post_100"]:
            d = cost_data[phase]
            cost_df_data.append({
                "Phase": phase.replace("_", " "),
                "Items": d["count"],
                "Cost Range": f"${d['low']:,.0f} - ${d['high']:,.0f}"
            })
            total_count += d["count"]
            total_low += d["low"]
            total_high += d["high"]

        cost_df = pd.DataFrame(cost_df_data)
        st.dataframe(cost_df, use_container_width=True, hide_index=True)

        st.markdown(f'''
        <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: var(--bg-surface-sunken); border-radius: 0.375rem; margin-top: 0.5rem;">
            <strong>Total</strong>
            <span><strong>{total_count}</strong> items</span>
            <span class="font-mono"><strong>${total_low:,.0f} - ${total_high:,.0f}</strong></span>
        </div>
        ''', unsafe_allow_html=True)

        if st.button("View all work items →", key="dash_view_wi", type="secondary"):
            st.session_state["page"] = "work_items"
            st.rerun()

        st.markdown('</div></div>', unsafe_allow_html=True)

    # Top Risks Card
    with risks_col:
        st.markdown('''<div class="card"><div class="card-header"><span class="card-title">Top Risks</span></div><div class="card-body">''', unsafe_allow_html=True)

        if reasoning_store and reasoning_store.risks:
            top_risks = sorted(reasoning_store.risks, key=lambda r: ["critical", "high", "medium", "low"].index(r.severity) if r.severity in ["critical", "high", "medium", "low"] else 99)[:5]

            risks_df_data = []
            for risk in top_risks:
                risks_df_data.append({
                    "Severity": (risk.severity or "N/A").upper(),
                    "Risk": risk.title[:50] + "..." if len(risk.title) > 50 else risk.title,
                    "Domain": (risk.domain or "").replace("_", " ").title()
                })

            risks_df = pd.DataFrame(risks_df_data)
            event = st.dataframe(
                risks_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="dash_risks_table"
            )

            if event.selection.rows:
                selected_idx = event.selection.rows[0]
                st.session_state["selected_risk_id"] = top_risks[selected_idx].finding_id
                st.session_state["page"] = "risks"
                st.rerun()

            if st.button("View all risks →", key="dash_view_risks", type="secondary"):
                st.session_state["page"] = "risks"
                st.rerun()
        else:
            st.markdown(empty_state("🎉", "No risks identified", "The analysis hasn't found any significant risks yet."), unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    # Day 1 Work Items
    st.markdown('---', unsafe_allow_html=False)

    if reasoning_store:
        day1_items = [wi for wi in reasoning_store.work_items if wi.phase == "Day_1"][:5]
        if day1_items:
            st.subheader("Day 1 Work Items")

            day1_df_data = []
            for wi in day1_items:
                cost_est = getattr(wi, "cost_estimate", "TBD")
                if hasattr(cost_est, "replace"):
                    cost_est = cost_est.replace("_", " ")
                day1_df_data.append({
                    "ID": wi.finding_id,
                    "Title": wi.title[:60] + "..." if len(wi.title) > 60 else wi.title,
                    "Domain": (wi.domain or "").replace("_", " ").title(),
                    "Owner": getattr(wi, "owner_type", "buyer").title(),
                    "Cost": str(cost_est)
                })

            day1_df = pd.DataFrame(day1_df_data)
            event = st.dataframe(
                day1_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="dash_day1_table"
            )

            if event.selection.rows:
                selected_idx = event.selection.rows[0]
                st.session_state["selected_wi_id"] = day1_items[selected_idx].finding_id
                st.session_state["page"] = "work_items"
                st.rerun()

    # Quick actions
    st.markdown('---', unsafe_allow_html=False)
    st.subheader("Quick Actions")

    action_cols = st.columns(4)

    with action_cols[0]:
        if st.button("📊 Export to Excel", use_container_width=True, type="primary"):
            # Export functionality
            if fact_store and reasoning_store:
                export_data = {
                    "facts": len(fact_store.facts),
                    "risks": len(reasoning_store.risks),
                    "work_items": len(reasoning_store.work_items)
                }
                st.success(f"Export ready: {export_data['facts']} facts, {export_data['risks']} risks, {export_data['work_items']} work items")
            else:
                st.warning("No data to export")

    with action_cols[1]:
        if st.button("📄 Export JSON", use_container_width=True):
            if fact_store and reasoning_store:
                st.info("JSON export functionality available")
            else:
                st.warning("No data to export")

    with action_cols[2]:
        if st.button(f"🔍 Review Gaps ({gaps_count})", use_container_width=True):
            st.session_state["page"] = "gaps"
            st.rerun()

    with action_cols[3]:
        if st.button("📋 Generate VDR Request", use_container_width=True):
            st.info("VDR request generation available")


# =============================================================================
# PAGE: RISKS (Steps 106-108)
# =============================================================================
def page_risks():
    fact_store, reasoning_store = load_data()
    page_header("Risks", "Identified risks and mitigation strategies")

    if not reasoning_store or not reasoning_store.risks:
        st.markdown(empty_state("⚠️", "No Risks", "Run an analysis to identify risks."), unsafe_allow_html=True)
        return

    # Get unique domains for filter
    all_domains = list(set(r.domain for r in reasoning_store.risks if r.domain))
    domain_options = ["All"] + [d.replace("_", " ").title() for d in sorted(all_domains)]

    # Functional filters using Streamlit widgets
    filter_cols = st.columns([1, 1, 1, 2])

    with filter_cols[0]:
        severity_filter = st.selectbox(
            "Severity",
            ["All", "Critical", "High", "Medium", "Low"],
            key="risks_severity"
        )

    with filter_cols[1]:
        domain_filter = st.selectbox(
            "Domain",
            domain_options,
            key="risks_domain"
        )

    with filter_cols[2]:
        type_filter = st.selectbox(
            "Type",
            ["All", "Integration", "Standalone"],
            key="risks_type"
        )

    with filter_cols[3]:
        search_filter = st.text_input(
            "Search",
            key="risks_search",
            placeholder="Search risks..."
        )

    # Filter risks
    filtered_risks = reasoning_store.risks.copy()

    if severity_filter != "All":
        filtered_risks = [r for r in filtered_risks if r.severity and r.severity.lower() == severity_filter.lower()]

    if domain_filter != "All":
        domain_key = domain_filter.lower().replace(" ", "_")
        filtered_risks = [r for r in filtered_risks if r.domain == domain_key]

    if type_filter != "All":
        if type_filter == "Integration":
            filtered_risks = [r for r in filtered_risks if r.integration_dependent]
        else:
            filtered_risks = [r for r in filtered_risks if not r.integration_dependent]

    if search_filter:
        search_lower = search_filter.lower()
        filtered_risks = [r for r in filtered_risks if search_lower in r.title.lower() or search_lower in (r.description or "").lower()]

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    filtered_risks = sorted(filtered_risks, key=lambda r: severity_order.get(r.severity, 99) if r.severity else 99)

    st.markdown(f'<p style="color: var(--text-muted); margin-bottom: 1rem;">Showing {len(filtered_risks)} of {len(reasoning_store.risks)} risks</p>', unsafe_allow_html=True)

    # Two-column layout: table + detail panel
    col1, col2 = st.columns([7, 3])

    with col1:
        # Create DataFrame for interactive table
        import pandas as pd

        if filtered_risks:
            df_data = []
            for risk in filtered_risks:
                df_data.append({
                    "ID": risk.finding_id,
                    "Severity": (risk.severity or "N/A").upper(),
                    "Title": risk.title[:80] + "..." if len(risk.title) > 80 else risk.title,
                    "Domain": (risk.domain or "").replace("_", " ").title(),
                    "Type": "Integration" if risk.integration_dependent else "Standalone",
                    "Confidence": risk.confidence or "N/A"
                })

            df = pd.DataFrame(df_data)

            # Display interactive dataframe
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Severity": st.column_config.TextColumn("Severity", width="small"),
                    "Title": st.column_config.TextColumn("Risk", width="large"),
                    "Domain": st.column_config.TextColumn("Domain", width="medium"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Confidence": st.column_config.TextColumn("Conf.", width="small"),
                }
            )

            # Handle row selection
            if event.selection.rows:
                selected_idx = event.selection.rows[0]
                st.session_state["selected_risk_id"] = filtered_risks[selected_idx].finding_id
        else:
            st.info("No risks match the current filters.")

    with col2:
        # Detail panel
        selected_id = st.session_state.get("selected_risk_id")
        if selected_id:
            # Find the selected risk
            selected_risk = next((r for r in reasoning_store.risks if r.finding_id == selected_id), None)
            if selected_risk:
                render_detail_panel(
                    selected_risk.title,
                    [
                        {"title": "ID", "content": f'<span class="font-mono">{selected_risk.finding_id}</span>'},
                        {"title": "Severity", "content": severity_badge(selected_risk.severity)},
                        {"title": "Domain", "content": (selected_risk.domain or "N/A").replace("_", " ").title()},
                        {"title": "Description", "content": selected_risk.description or "No description available"},
                        {"title": "Mitigation", "content": selected_risk.mitigation or "No mitigation specified"},
                        {"title": "Based On Facts", "content": ", ".join(selected_risk.based_on_facts) if selected_risk.based_on_facts else "N/A"},
                        {"title": "Integration Dependent", "content": "Yes" if selected_risk.integration_dependent else "No"},
                    ]
                )
        else:
            st.markdown('''
            <div class="detail-panel" style="text-align: center; padding: 2rem;">
                <p style="color: var(--text-muted);">Select a risk to view details</p>
            </div>
            ''', unsafe_allow_html=True)


# =============================================================================
# PAGE: WORK ITEMS (Steps 109-111)
# =============================================================================
def page_work_items():
    fact_store, reasoning_store = load_data()
    page_header("Work Items", "Integration and remediation tasks")

    if not reasoning_store or not reasoning_store.work_items:
        st.markdown(empty_state("📋", "No Work Items", "Run an analysis to generate work items."), unsafe_allow_html=True)
        return

    import pandas as pd

    # Count items by phase for tabs
    day1_count = len([w for w in reasoning_store.work_items if w.phase == "Day_1"])
    day100_count = len([w for w in reasoning_store.work_items if w.phase == "Day_100"])
    post100_count = len([w for w in reasoning_store.work_items if w.phase == "Post_100"])

    # Phase tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        f"All ({len(reasoning_store.work_items)})",
        f"Day 1 ({day1_count})",
        f"Day 100 ({day100_count})",
        f"Post-100 ({post100_count})"
    ])

    def render_work_items_table(items, tab_key):
        """Render work items table with filters."""
        if not items:
            st.info("No work items in this phase.")
            return

        # Filters
        filter_cols = st.columns([1, 1, 2])

        with filter_cols[0]:
            priority_filter = st.selectbox(
                "Priority",
                ["All", "Critical", "High", "Medium", "Low"],
                key=f"wi_{tab_key}_priority"
            )

        with filter_cols[1]:
            owner_filter = st.selectbox(
                "Owner",
                ["All", "Buyer", "Seller", "Joint"],
                key=f"wi_{tab_key}_owner"
            )

        with filter_cols[2]:
            search_filter = st.text_input(
                "Search",
                key=f"wi_{tab_key}_search",
                placeholder="Search work items..."
            )

        # Apply filters
        filtered = items.copy()

        if priority_filter != "All":
            filtered = [w for w in filtered if w.priority and w.priority.lower() == priority_filter.lower()]

        if owner_filter != "All":
            filtered = [w for w in filtered if getattr(w, "owner_type", "buyer").lower() == owner_filter.lower()]

        if search_filter:
            search_lower = search_filter.lower()
            filtered = [w for w in filtered if search_lower in w.title.lower() or search_lower in (w.description or "").lower()]

        st.markdown(f'<p style="color: var(--text-muted); margin: 0.5rem 0;">Showing {len(filtered)} items</p>', unsafe_allow_html=True)

        # Two-column layout
        col1, col2 = st.columns([7, 3])

        with col1:
            if filtered:
                df_data = []
                for wi in filtered:
                    df_data.append({
                        "ID": wi.finding_id,
                        "Title": wi.title[:60] + "..." if len(wi.title) > 60 else wi.title,
                        "Domain": (wi.domain or "").replace("_", " ").title(),
                        "Phase": (wi.phase or "").replace("_", " "),
                        "Priority": (wi.priority or "medium").title(),
                        "Owner": getattr(wi, "owner_type", "buyer").title(),
                        "Cost": getattr(wi, "cost_estimate", "TBD").replace("_", " ") if hasattr(wi, "cost_estimate") else "TBD"
                    })

                df = pd.DataFrame(df_data)

                event = st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key=f"wi_table_{tab_key}",
                    column_config={
                        "ID": st.column_config.TextColumn("ID", width="small"),
                        "Title": st.column_config.TextColumn("Title", width="large"),
                        "Domain": st.column_config.TextColumn("Domain", width="medium"),
                        "Phase": st.column_config.TextColumn("Phase", width="small"),
                        "Priority": st.column_config.TextColumn("Priority", width="small"),
                        "Owner": st.column_config.TextColumn("Owner", width="small"),
                        "Cost": st.column_config.TextColumn("Cost", width="medium"),
                    }
                )

                if event.selection.rows:
                    selected_idx = event.selection.rows[0]
                    st.session_state["selected_wi_id"] = filtered[selected_idx].finding_id
            else:
                st.info("No work items match the current filters.")

        with col2:
            selected_id = st.session_state.get("selected_wi_id")
            if selected_id:
                selected_wi = next((w for w in reasoning_store.work_items if w.finding_id == selected_id), None)
                if selected_wi:
                    cost_low = getattr(selected_wi, "cost_low", 0) or 0
                    cost_high = getattr(selected_wi, "cost_high", 0) or 0
                    cost_range = f"${cost_low:,.0f} - ${cost_high:,.0f}" if cost_low or cost_high else "TBD"

                    render_detail_panel(
                        selected_wi.title,
                        [
                            {"title": "ID", "content": f'<span class="font-mono">{selected_wi.finding_id}</span>'},
                            {"title": "Phase", "content": phase_badge(selected_wi.phase)},
                            {"title": "Priority", "content": severity_badge(selected_wi.priority)},
                            {"title": "Owner", "content": getattr(selected_wi, "owner_type", "buyer").title()},
                            {"title": "Domain", "content": (selected_wi.domain or "N/A").replace("_", " ").title()},
                            {"title": "Cost Estimate", "content": f'<span class="font-mono">{cost_range}</span>'},
                            {"title": "Description", "content": selected_wi.description or "No description available"},
                            {"title": "Based On", "content": ", ".join(selected_wi.based_on_facts) if selected_wi.based_on_facts else "N/A"},
                        ]
                    )
            else:
                st.markdown('''
                <div class="detail-panel" style="text-align: center; padding: 2rem;">
                    <p style="color: var(--text-muted);">Select a work item to view details</p>
                </div>
                ''', unsafe_allow_html=True)

    with tab1:
        render_work_items_table(reasoning_store.work_items, "all")

    with tab2:
        day1_items = [w for w in reasoning_store.work_items if w.phase == "Day_1"]
        render_work_items_table(day1_items, "day1")

    with tab3:
        day100_items = [w for w in reasoning_store.work_items if w.phase == "Day_100"]
        render_work_items_table(day100_items, "day100")

    with tab4:
        post100_items = [w for w in reasoning_store.work_items if w.phase == "Post_100"]
        render_work_items_table(post100_items, "post100")


# =============================================================================
# PAGE: QUESTIONS
# =============================================================================
def page_questions():
    fact_store, reasoning_store = load_data()
    page_header("Open Questions", "Information requests for the data room")

    if not fact_store or not fact_store.gaps:
        st.markdown(empty_state("❓", "No Open Questions", "Run an analysis to identify information gaps."), unsafe_allow_html=True)
        return

    rows = []
    for gap in fact_store.gaps:
        imp = getattr(gap, 'importance', 'medium') or 'medium'
        imp_badge = badge(imp.upper(), imp)
        rows.append([
            imp_badge,
            f'<span class="truncate" style="max-width: 400px;">{gap.description}</span>',
            (gap.domain or "").replace("_", " ").title(),
            gap.category or "N/A"
        ])

    table_html = data_table(["Importance", "Question", "Domain", "Category"], rows)
    st.markdown(f'<div class="table-container">{table_html}</div>', unsafe_allow_html=True)


# =============================================================================
# PAGE: FACTS
# =============================================================================
def page_facts():
    fact_store, reasoning_store = load_data()
    page_header("Facts", "Extracted facts from documents")

    if not fact_store or not fact_store.facts:
        st.markdown(empty_state("📁", "No Facts", "Run an analysis to extract facts."), unsafe_allow_html=True)
        return

    st.markdown(f'<p style="color: var(--text-muted); margin-bottom: var(--space-4);">Showing {len(fact_store.facts)} facts</p>', unsafe_allow_html=True)

    rows = []
    for fact in fact_store.facts[:100]:
        status_badge = {"documented": badge("✓", "success"), "partial": badge("~", "medium"), "gap": badge("✗", "critical")}.get(fact.status, badge("?", "info"))
        rows.append([
            f'<span class="font-mono">{fact.fact_id}</span>',
            f'<span class="truncate" style="max-width: 300px;">{fact.item}</span>',
            (fact.domain or "").replace("_", " ").title(),
            fact.category or "N/A",
            status_badge
        ])

    table_html = data_table(["ID", "Fact", "Domain", "Category", "Status"], rows)
    st.markdown(f'<div class="table-container">{table_html}</div>', unsafe_allow_html=True)


# =============================================================================
# PAGE: GAPS
# =============================================================================
def page_gaps():
    fact_store, reasoning_store = load_data()
    page_header("Gaps", "Missing information identified")

    if not fact_store or not fact_store.gaps:
        st.markdown(empty_state("🔍", "No Gaps", "Run an analysis to identify gaps."), unsafe_allow_html=True)
        return

    rows = []
    for gap in fact_store.gaps:
        imp = getattr(gap, 'importance', 'medium') or 'medium'
        imp_badge = badge(imp.upper(), imp)
        rows.append([
            imp_badge,
            f'<span class="truncate" style="max-width: 400px;">{gap.description}</span>',
            (gap.domain or "").replace("_", " ").title(),
            gap.category or "N/A"
        ])

    table_html = data_table(["Importance", "Gap", "Domain", "Category"], rows)
    st.markdown(f'<div class="table-container">{table_html}</div>', unsafe_allow_html=True)


# =============================================================================
# PAGE: ORGANIZATION
# =============================================================================
def page_organization():
    fact_store, reasoning_store = load_data()

    # Initialize organization sub-page state
    if "org_subpage" not in st.session_state:
        st.session_state["org_subpage"] = "org_overview"

    subpage = st.session_state.get("org_subpage", "org_overview")

    # Sub-navigation tabs
    tab_labels = [label for _, label in ORG_SUBPAGES]
    tab_keys = [key for key, _ in ORG_SUBPAGES]

    current_idx = tab_keys.index(subpage) if subpage in tab_keys else 0
    tabs = st.tabs(tab_labels)

    # Route to sub-page content
    with tabs[0]:  # Overview
        render_org_overview(fact_store, reasoning_store)

    with tabs[1]:  # Staffing Census
        render_org_staffing(fact_store)

    with tabs[2]:  # Benchmark
        render_org_benchmark(fact_store)

    with tabs[3]:  # MSP Dependencies
        render_org_msp(fact_store)

    with tabs[4]:  # Shared Services
        render_org_shared_services(fact_store)


def render_org_overview(fact_store, reasoning_store):
    """Render organization overview page."""
    page_header("Organization & Staffing Analysis", "IT staffing assessment with benchmark comparison and dependency analysis")

    if not fact_store:
        st.markdown(empty_state("👥", "No Organization Data", "Run an analysis first."), unsafe_allow_html=True)
        return

    org_facts = [f for f in fact_store.facts if f.domain == "organization"]

    # Calculate summary stats (demo values - would come from actual analysis)
    total_staff = len([f for f in org_facts if "staff" in f.item.lower() or "employee" in f.item.lower() or "head" in f.item.lower()])
    total_staff = max(total_staff, 12)  # Demo minimum

    # Summary stats row
    render_stat_cards([
        {"value": total_staff, "label": "Total IT Staff"},
        {"value": "$1.2M", "label": "Total Comp"},
        {"value": "3", "label": "Key Persons", "highlight": True},
        {"value": "4", "label": "MSP Vendors"},
        {"value": "2.5", "label": "Hidden FTE", "highlight": True},
    ])

    st.divider()

    # Navigation cards
    st.subheader("Analysis Modules")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('''
        <div class="nav-card" onclick="document.querySelector('[data-baseweb=\\"tab\\"][id*=\\"tab-1\\"]').click()">
            <div class="nav-card-icon">👥</div>
            <div class="nav-card-content">
                <h3>Staffing Census</h3>
                <p>Role-by-role breakdown with compensation and tenure data</p>
                <span class="nav-card-stat">12 staff | 10 FTE, 2 contractors</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('''
        <div class="nav-card" onclick="document.querySelector('[data-baseweb=\\"tab\\"][id*=\\"tab-3\\"]').click()">
            <div class="nav-card-icon">🔗</div>
            <div class="nav-card-content">
                <h3>MSP Dependencies</h3>
                <p>Outsourced services, FTE equivalents, and exit risk</p>
                <span class="nav-card-stat">4 vendors | 3.5 FTE eq.</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown('''
        <div class="nav-card" onclick="document.querySelector('[data-baseweb=\\"tab\\"][id*=\\"tab-2\\"]').click()">
            <div class="nav-card-icon">📊</div>
            <div class="nav-card-content">
                <h3>Benchmark Comparison</h3>
                <p>Compare staffing against industry benchmarks</p>
                <span class="nav-card-stat" style="color: var(--medium);">Status: Review Needed</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('''
        <div class="nav-card" onclick="document.querySelector('[data-baseweb=\\"tab\\"][id*=\\"tab-4\\"]').click()">
            <div class="nav-card-icon">🏢</div>
            <div class="nav-card-content">
                <h3>Shared Services</h3>
                <p>Hidden headcount from parent company dependencies</p>
                <span class="nav-card-stat" style="color: var(--critical);">2.5 hidden FTE need</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    st.divider()

    # IT Support Coverage
    st.subheader("How IT Supports the Business")

    cols = st.columns(3)

    activities = [
        {"icon": "💻", "name": "Applications Team", "tasks": ["ERP System", "CRM & Sales tools", "Custom apps", "Integrations"]},
        {"icon": "🌐", "name": "Infrastructure Team", "tasks": ["Cloud environment", "Active Directory", "Servers & storage", "Backup & DR"]},
        {"icon": "🔒", "name": "Security Team", "tasks": ["Endpoint protection", "Firewall", "Vulnerability mgmt", "SIEM monitoring"]},
    ]

    for i, activity in enumerate(activities):
        with cols[i]:
            tasks_html = "".join([f"<li>{t}</li>" for t in activity["tasks"]])
            st.markdown(f'''
            <div class="activity-card">
                <div class="activity-icon">{activity["icon"]}</div>
                <div class="activity-name">{activity["name"]}</div>
                <ul class="activity-tasks">{tasks_html}</ul>
            </div>
            ''', unsafe_allow_html=True)

    # Key Findings
    if org_facts:
        st.divider()
        st.subheader("Key Organization Facts")

        for fact in org_facts[:5]:
            st.markdown(f'''
            <div style="display: flex; gap: 0.5rem; padding: 0.75rem 0; border-bottom: 1px solid var(--border-default);">
                <span class="font-mono" style="color: var(--text-muted); min-width: 80px;">{fact.fact_id}</span>
                <span>{fact.item}</span>
            </div>
            ''', unsafe_allow_html=True)


def render_org_staffing(fact_store):
    """Render staffing census page."""
    page_header("Staffing Census", "Role-by-role breakdown of IT organization")

    if not fact_store:
        st.info("No staffing data available. Run an analysis first.")
        return

    import pandas as pd

    # Demo staffing data (would come from actual analysis)
    staffing_data = [
        {"Role": "IT Director", "Name": "John Smith", "Type": "FTE", "Tenure": "5 years", "Key Person": "Yes", "Comp Range": "$150-180K"},
        {"Role": "Sr. Developer", "Name": "Jane Doe", "Type": "FTE", "Tenure": "3 years", "Key Person": "Yes", "Comp Range": "$120-140K"},
        {"Role": "Systems Admin", "Name": "Bob Wilson", "Type": "FTE", "Tenure": "4 years", "Key Person": "No", "Comp Range": "$90-110K"},
        {"Role": "Network Engineer", "Name": "Alice Brown", "Type": "FTE", "Tenure": "2 years", "Key Person": "No", "Comp Range": "$85-100K"},
        {"Role": "Security Analyst", "Name": "Charlie Davis", "Type": "FTE", "Tenure": "1 year", "Key Person": "No", "Comp Range": "$80-95K"},
        {"Role": "Help Desk", "Name": "Eve Johnson", "Type": "Contractor", "Tenure": "6 months", "Key Person": "No", "Comp Range": "$45-55K"},
    ]

    df = pd.DataFrame(staffing_data)

    # Filters
    col1, col2 = st.columns([1, 1])
    with col1:
        type_filter = st.selectbox("Employment Type", ["All", "FTE", "Contractor"], key="staff_type")
    with col2:
        key_filter = st.selectbox("Key Person", ["All", "Yes", "No"], key="staff_key")

    # Apply filters
    filtered_df = df.copy()
    if type_filter != "All":
        filtered_df = filtered_df[filtered_df["Type"] == type_filter]
    if key_filter != "All":
        filtered_df = filtered_df[filtered_df["Key Person"] == key_filter]

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Role": st.column_config.TextColumn("Role", width="medium"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Tenure": st.column_config.TextColumn("Tenure", width="small"),
            "Key Person": st.column_config.TextColumn("Key", width="small"),
            "Comp Range": st.column_config.TextColumn("Comp Range", width="medium"),
        }
    )

    # Summary stats
    st.markdown(f'''
    <div style="display: flex; gap: 2rem; margin-top: 1rem; padding: 1rem; background: var(--bg-surface-sunken); border-radius: 0.5rem;">
        <span><strong>{len(filtered_df)}</strong> total staff shown</span>
        <span><strong>{len(filtered_df[filtered_df["Type"] == "FTE"])}</strong> FTEs</span>
        <span><strong>{len(filtered_df[filtered_df["Type"] == "Contractor"])}</strong> contractors</span>
        <span><strong>{len(filtered_df[filtered_df["Key Person"] == "Yes"])}</strong> key persons</span>
    </div>
    ''', unsafe_allow_html=True)


def render_org_benchmark(fact_store):
    """Render benchmark comparison page."""
    page_header("Benchmark Comparison", "Compare IT staffing against industry standards")

    import pandas as pd

    # Demo benchmark data
    benchmark_data = [
        {"Function": "Applications", "Current FTE": 2, "Benchmark FTE": 3, "Gap": -1, "Status": "Under"},
        {"Function": "Infrastructure", "Current FTE": 2, "Benchmark FTE": 2, "Gap": 0, "Status": "OK"},
        {"Function": "Security", "Current FTE": 1, "Benchmark FTE": 1.5, "Gap": -0.5, "Status": "Under"},
        {"Function": "Network", "Current FTE": 1, "Benchmark FTE": 1, "Gap": 0, "Status": "OK"},
        {"Function": "Help Desk", "Current FTE": 1, "Benchmark FTE": 2, "Gap": -1, "Status": "Under"},
        {"Function": "Management", "Current FTE": 1, "Benchmark FTE": 1, "Gap": 0, "Status": "OK"},
    ]

    df = pd.DataFrame(benchmark_data)

    # Summary metrics
    total_current = df["Current FTE"].sum()
    total_benchmark = df["Benchmark FTE"].sum()
    total_gap = df["Gap"].sum()

    cols = st.columns(4)
    with cols[0]:
        st.metric("Current FTE", f"{total_current:.1f}")
    with cols[1]:
        st.metric("Benchmark FTE", f"{total_benchmark:.1f}")
    with cols[2]:
        st.metric("Gap", f"{total_gap:+.1f}", delta_color="inverse")
    with cols[3]:
        status = "Under-staffed" if total_gap < 0 else "Adequately Staffed"
        st.metric("Overall Status", status)

    st.divider()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Function": st.column_config.TextColumn("Function", width="medium"),
            "Current FTE": st.column_config.NumberColumn("Current", format="%.1f", width="small"),
            "Benchmark FTE": st.column_config.NumberColumn("Benchmark", format="%.1f", width="small"),
            "Gap": st.column_config.NumberColumn("Gap", format="%+.1f", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
        }
    )

    # Key findings
    st.subheader("Key Findings")
    under_staffed = df[df["Status"] == "Under"]
    if not under_staffed.empty:
        for _, row in under_staffed.iterrows():
            st.warning(f"**{row['Function']}**: {abs(row['Gap']):.1f} FTE below benchmark")
    else:
        st.success("All functions are at or above benchmark staffing levels.")


def render_org_msp(fact_store):
    """Render MSP dependencies page."""
    page_header("MSP Dependencies", "Outsourced services and vendor dependencies")

    import pandas as pd

    # Demo MSP data
    msp_data = [
        {"Vendor": "CloudOps Inc", "Services": "Cloud infrastructure management", "FTE Equiv": 1.5, "Annual Cost": "$180K", "Exit Risk": "High"},
        {"Vendor": "SecureIT", "Services": "24/7 SOC monitoring", "FTE Equiv": 1.0, "Annual Cost": "$120K", "Exit Risk": "Medium"},
        {"Vendor": "NetManage", "Services": "Network support", "FTE Equiv": 0.5, "Annual Cost": "$60K", "Exit Risk": "Low"},
        {"Vendor": "HelpDesk Pro", "Services": "Overflow help desk", "FTE Equiv": 0.5, "Annual Cost": "$45K", "Exit Risk": "Low"},
    ]

    df = pd.DataFrame(msp_data)

    # Summary
    total_fte = df["FTE Equiv"].sum()
    total_cost = "$405K"  # Sum of costs

    cols = st.columns(3)
    with cols[0]:
        st.metric("Total MSP Vendors", len(df))
    with cols[1]:
        st.metric("Total FTE Equivalent", f"{total_fte:.1f}")
    with cols[2]:
        st.metric("Annual MSP Spend", total_cost)

    st.divider()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Vendor": st.column_config.TextColumn("Vendor", width="medium"),
            "Services": st.column_config.TextColumn("Services", width="large"),
            "FTE Equiv": st.column_config.NumberColumn("FTE Eq.", format="%.1f", width="small"),
            "Annual Cost": st.column_config.TextColumn("Annual Cost", width="small"),
            "Exit Risk": st.column_config.TextColumn("Exit Risk", width="small"),
        }
    )

    # High risk vendors
    high_risk = df[df["Exit Risk"] == "High"]
    if not high_risk.empty:
        st.subheader("High Exit Risk Vendors")
        for _, row in high_risk.iterrows():
            st.error(f"**{row['Vendor']}**: {row['Services']} ({row['FTE Equiv']} FTE eq.) - May require internalization or alternative vendor")


def render_org_shared_services(fact_store):
    """Render shared services analysis page."""
    page_header("Shared Services Analysis", "Hidden headcount from parent company dependencies")

    import pandas as pd

    # Demo shared services data
    ss_data = [
        {"Service": "Corporate IT Support", "Provider": "Parent Corp", "FTE Allocation": 1.0, "Transferring": "No", "Replacement Cost": "$95K"},
        {"Service": "Network Operations", "Provider": "Parent Corp", "FTE Allocation": 0.5, "Transferring": "No", "Replacement Cost": "$50K"},
        {"Service": "Security Operations", "Provider": "Parent Corp", "FTE Allocation": 0.5, "Transferring": "Yes", "Replacement Cost": "-"},
        {"Service": "License Management", "Provider": "Parent Corp", "FTE Allocation": 0.25, "Transferring": "No", "Replacement Cost": "$25K"},
        {"Service": "Procurement", "Provider": "Parent Corp", "FTE Allocation": 0.25, "Transferring": "No", "Replacement Cost": "$20K"},
    ]

    df = pd.DataFrame(ss_data)

    # Summary
    total_fte = df["FTE Allocation"].sum()
    non_transferring = df[df["Transferring"] == "No"]["FTE Allocation"].sum()

    cols = st.columns(3)
    with cols[0]:
        st.metric("Total Shared Services FTE", f"{total_fte:.2f}")
    with cols[1]:
        st.metric("Not Transferring", f"{non_transferring:.2f}", delta_color="inverse")
    with cols[2]:
        replacement_total = "$190K"  # Would calculate from data
        st.metric("Replacement Cost", replacement_total)

    st.divider()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Service": st.column_config.TextColumn("Service", width="medium"),
            "Provider": st.column_config.TextColumn("Provider", width="medium"),
            "FTE Allocation": st.column_config.NumberColumn("FTE", format="%.2f", width="small"),
            "Transferring": st.column_config.TextColumn("Transferring?", width="small"),
            "Replacement Cost": st.column_config.TextColumn("Replacement", width="small"),
        }
    )

    # Warning for hidden headcount
    if non_transferring > 0:
        st.warning(f'''
        **Hidden Headcount Risk**: {non_transferring:.1f} FTE worth of shared services will NOT transfer with the deal.
        These functions will need to be replaced or internalized post-close.
        ''')


# =============================================================================
# PAGE: APPLICATIONS
# =============================================================================
def page_applications():
    fact_store, reasoning_store = load_data()
    page_header("Applications", "Application inventory and analysis")

    if not fact_store:
        st.markdown(empty_state("💻", "No Application Data", "Run an analysis first."), unsafe_allow_html=True)
        return

    app_facts = [f for f in fact_store.facts if f.domain == "applications"]

    import pandas as pd

    # Category overview cards
    categories = {}
    for fact in app_facts:
        cat = fact.category or "Other"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(fact)

    if not app_facts:
        # Show demo data if no facts
        st.info("No application facts found. Showing demo application inventory.")

        demo_apps = [
            {"Name": "SAP ERP", "Category": "ERP", "Criticality": "Critical", "Vendor": "SAP", "Users": 500, "Status": "Active"},
            {"Name": "Salesforce", "Category": "CRM", "Criticality": "High", "Vendor": "Salesforce", "Users": 150, "Status": "Active"},
            {"Name": "ServiceNow", "Category": "ITSM", "Criticality": "High", "Vendor": "ServiceNow", "Users": 50, "Status": "Active"},
            {"Name": "Microsoft 365", "Category": "Productivity", "Criticality": "Critical", "Vendor": "Microsoft", "Users": 800, "Status": "Active"},
            {"Name": "Workday", "Category": "HR", "Criticality": "Medium", "Vendor": "Workday", "Users": 200, "Status": "Active"},
            {"Name": "Custom Portal", "Category": "Custom", "Criticality": "Medium", "Vendor": "Internal", "Users": 100, "Status": "Active"},
        ]

        # Category stats
        cat_stats = {}
        for app in demo_apps:
            cat = app["Category"]
            if cat not in cat_stats:
                cat_stats[cat] = 0
            cat_stats[cat] += 1

        # Display category cards
        cols = st.columns(min(len(cat_stats), 4))
        for i, (cat, count) in enumerate(cat_stats.items()):
            with cols[i % 4]:
                st.markdown(f'''
                <div class="stat-card">
                    <span class="stat-value">{count}</span>
                    <span class="stat-label">{cat}</span>
                </div>
                ''', unsafe_allow_html=True)

        st.divider()

        # Filters
        filter_cols = st.columns([1, 1, 2])
        with filter_cols[0]:
            cat_filter = st.selectbox("Category", ["All"] + list(cat_stats.keys()), key="app_cat")
        with filter_cols[1]:
            crit_filter = st.selectbox("Criticality", ["All", "Critical", "High", "Medium", "Low"], key="app_crit")
        with filter_cols[2]:
            search = st.text_input("Search", key="app_search", placeholder="Search applications...")

        # Filter demo data
        filtered = demo_apps.copy()
        if cat_filter != "All":
            filtered = [a for a in filtered if a["Category"] == cat_filter]
        if crit_filter != "All":
            filtered = [a for a in filtered if a["Criticality"] == crit_filter]
        if search:
            search_lower = search.lower()
            filtered = [a for a in filtered if search_lower in a["Name"].lower() or search_lower in a["Vendor"].lower()]

        df = pd.DataFrame(filtered)

        # Two columns: table + detail
        col1, col2 = st.columns([7, 3])

        with col1:
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="apps_table",
                column_config={
                    "Name": st.column_config.TextColumn("Application", width="large"),
                    "Category": st.column_config.TextColumn("Category", width="small"),
                    "Criticality": st.column_config.TextColumn("Criticality", width="small"),
                    "Vendor": st.column_config.TextColumn("Vendor", width="medium"),
                    "Users": st.column_config.NumberColumn("Users", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                }
            )

            if event.selection.rows:
                st.session_state["selected_app"] = filtered[event.selection.rows[0]]

        with col2:
            selected = st.session_state.get("selected_app")
            if selected:
                render_detail_panel(
                    selected["Name"],
                    [
                        {"title": "Category", "content": selected["Category"]},
                        {"title": "Criticality", "content": severity_badge(selected["Criticality"].lower())},
                        {"title": "Vendor", "content": selected["Vendor"]},
                        {"title": "Active Users", "content": f'{selected["Users"]:,}'},
                        {"title": "Status", "content": selected["Status"]},
                    ]
                )
            else:
                st.markdown('''
                <div class="detail-panel" style="text-align: center; padding: 2rem;">
                    <p style="color: var(--text-muted);">Select an application to view details</p>
                </div>
                ''', unsafe_allow_html=True)

        return

    # If we have real facts, show them
    st.markdown(f'<p style="color: var(--text-muted);">Found {len(app_facts)} application facts</p>', unsafe_allow_html=True)

    # Group by category with expanders
    for cat, facts in sorted(categories.items()):
        with st.expander(f"{cat} ({len(facts)} facts)", expanded=len(facts) < 10):
            for fact in facts:
                st.markdown(f'''
                <div style="display: flex; gap: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border-default);">
                    <span class="font-mono" style="color: var(--text-muted); min-width: 80px;">{fact.fact_id}</span>
                    <span>{fact.item}</span>
                    <span class="badge badge-{fact.status or 'info'}" style="margin-left: auto;">{fact.status or "N/A"}</span>
                </div>
                ''', unsafe_allow_html=True)


# =============================================================================
# PAGE: INFRASTRUCTURE
# =============================================================================
def page_infrastructure():
    fact_store, reasoning_store = load_data()
    page_header("Infrastructure", "Infrastructure inventory and analysis")

    if not fact_store:
        st.markdown(empty_state("🖥️", "No Infrastructure Data", "Run an analysis first."), unsafe_allow_html=True)
        return

    infra_facts = [f for f in fact_store.facts if f.domain == "infrastructure"]
    network_facts = [f for f in fact_store.facts if f.domain == "network"]

    import pandas as pd

    # Combine infrastructure and network
    all_infra = infra_facts + network_facts

    if not all_infra:
        # Show demo data
        st.info("No infrastructure facts found. Showing demo infrastructure inventory.")

        demo_infra = [
            {"Name": "AWS Primary", "Category": "Cloud", "Type": "IaaS", "Status": "Active", "Age": "3 years", "EOL Risk": "Low"},
            {"Name": "Azure DR", "Category": "Cloud", "Type": "IaaS", "Status": "Active", "Age": "2 years", "EOL Risk": "Low"},
            {"Name": "DC1 Servers", "Category": "On-Prem", "Type": "Compute", "Status": "Active", "Age": "5 years", "EOL Risk": "Medium"},
            {"Name": "SAN Storage", "Category": "Storage", "Type": "SAN", "Status": "Active", "Age": "4 years", "EOL Risk": "Medium"},
            {"Name": "Core Switches", "Category": "Network", "Type": "Switching", "Status": "Active", "Age": "3 years", "EOL Risk": "Low"},
            {"Name": "WAN Links", "Category": "Network", "Type": "WAN", "Status": "Active", "Age": "2 years", "EOL Risk": "Low"},
            {"Name": "Legacy DB Server", "Category": "On-Prem", "Type": "Database", "Status": "Deprecated", "Age": "8 years", "EOL Risk": "High"},
        ]

        # Category stats
        cat_stats = {}
        for item in demo_infra:
            cat = item["Category"]
            if cat not in cat_stats:
                cat_stats[cat] = 0
            cat_stats[cat] += 1

        # Display category cards
        cols = st.columns(min(len(cat_stats), 4))
        for i, (cat, count) in enumerate(cat_stats.items()):
            with cols[i % 4]:
                st.markdown(f'''
                <div class="stat-card">
                    <span class="stat-value">{count}</span>
                    <span class="stat-label">{cat}</span>
                </div>
                ''', unsafe_allow_html=True)

        st.divider()

        # Filters
        filter_cols = st.columns([1, 1, 1, 2])
        with filter_cols[0]:
            cat_filter = st.selectbox("Category", ["All"] + list(cat_stats.keys()), key="infra_cat")
        with filter_cols[1]:
            status_filter = st.selectbox("Status", ["All", "Active", "Deprecated"], key="infra_status")
        with filter_cols[2]:
            eol_filter = st.selectbox("EOL Risk", ["All", "High", "Medium", "Low"], key="infra_eol")
        with filter_cols[3]:
            search = st.text_input("Search", key="infra_search", placeholder="Search infrastructure...")

        # Filter
        filtered = demo_infra.copy()
        if cat_filter != "All":
            filtered = [i for i in filtered if i["Category"] == cat_filter]
        if status_filter != "All":
            filtered = [i for i in filtered if i["Status"] == status_filter]
        if eol_filter != "All":
            filtered = [i for i in filtered if i["EOL Risk"] == eol_filter]
        if search:
            search_lower = search.lower()
            filtered = [i for i in filtered if search_lower in i["Name"].lower() or search_lower in i["Type"].lower()]

        df = pd.DataFrame(filtered)

        # Two columns
        col1, col2 = st.columns([7, 3])

        with col1:
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="infra_table",
                column_config={
                    "Name": st.column_config.TextColumn("Name", width="large"),
                    "Category": st.column_config.TextColumn("Category", width="small"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Age": st.column_config.TextColumn("Age", width="small"),
                    "EOL Risk": st.column_config.TextColumn("EOL Risk", width="small"),
                }
            )

            if event.selection.rows:
                st.session_state["selected_infra"] = filtered[event.selection.rows[0]]

        with col2:
            selected = st.session_state.get("selected_infra")
            if selected:
                eol_color = {"High": "critical", "Medium": "medium", "Low": "low"}.get(selected["EOL Risk"], "info")
                render_detail_panel(
                    selected["Name"],
                    [
                        {"title": "Category", "content": selected["Category"]},
                        {"title": "Type", "content": selected["Type"]},
                        {"title": "Status", "content": selected["Status"]},
                        {"title": "Age", "content": selected["Age"]},
                        {"title": "EOL Risk", "content": f'<span class="badge badge-{eol_color}">{selected["EOL Risk"]}</span>'},
                    ]
                )
            else:
                st.markdown('''
                <div class="detail-panel" style="text-align: center; padding: 2rem;">
                    <p style="color: var(--text-muted);">Select an item to view details</p>
                </div>
                ''', unsafe_allow_html=True)

        # EOL warnings
        high_risk = [i for i in demo_infra if i["EOL Risk"] == "High"]
        if high_risk:
            st.divider()
            st.subheader("EOL Risk Items")
            for item in high_risk:
                st.error(f"**{item['Name']}**: {item['Age']} old - requires upgrade or replacement planning")

        return

    # If we have real facts
    st.markdown(f'<p style="color: var(--text-muted);">Found {len(all_infra)} infrastructure facts</p>', unsafe_allow_html=True)

    # Group by category
    categories = {}
    for fact in all_infra:
        cat = fact.category or "Other"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(fact)

    for cat, facts in sorted(categories.items()):
        with st.expander(f"{cat} ({len(facts)} facts)", expanded=len(facts) < 10):
            for fact in facts:
                st.markdown(f'''
                <div style="display: flex; gap: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border-default);">
                    <span class="font-mono" style="color: var(--text-muted); min-width: 80px;">{fact.fact_id}</span>
                    <span>{fact.item}</span>
                </div>
                ''', unsafe_allow_html=True)


# =============================================================================
# PAGE: UPLOAD
# =============================================================================
def page_upload():
    page_header("Upload & Analyze", "Upload documents and run IT due diligence analysis")

    if not CONFIG_LOADED:
        st.error(f"Configuration error: {IMPORT_ERROR}")
        return

    # Deal info
    st.markdown('<div class="card"><div class="card-header"><span class="card-title">1. Deal Information</span></div><div class="card-body">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        target_name = st.text_input("Target Company", value="Target Company", key="target_name")
        deal_type = st.selectbox("Deal Type", ["bolt_on", "carve_out"],
                                  format_func=lambda x: "Bolt-On (Integration)" if x == "bolt_on" else "Carve-Out (Separation)",
                                  key="deal_type")
    with col2:
        buyer_name = st.text_input("Buyer Company (optional)", key="buyer_name")

    st.markdown('</div></div>', unsafe_allow_html=True)

    # Documents
    st.markdown('<div class="card"><div class="card-header"><span class="card-title">2. Documents</span></div><div class="card-body">', unsafe_allow_html=True)

    use_sample = st.checkbox("Use sample documents from data/input/", key="use_sample")

    if not use_sample:
        uploaded_files = st.file_uploader("Upload IT profiles, assessments, security audits", type=["pdf", "txt", "md"], accept_multiple_files=True, key="file_upload")
        if uploaded_files:
            st.success(f"✓ {len(uploaded_files)} document(s) ready")
    else:
        uploaded_files = None
        if INPUT_DIR.exists():
            sample_files = list(INPUT_DIR.glob("*.pdf")) + list(INPUT_DIR.glob("*.txt")) + list(INPUT_DIR.glob("*.md"))
            if sample_files:
                st.success(f"✓ Found {len(sample_files)} sample document(s)")

    notes = st.text_area("Quick Notes (optional)", placeholder="Paste meeting notes here...", key="notes")

    st.markdown('</div></div>', unsafe_allow_html=True)

    # Domains
    st.markdown('<div class="card"><div class="card-header"><span class="card-title">3. Analysis Domains</span></div><div class="card-body">', unsafe_allow_html=True)

    all_domains = ["infrastructure", "network", "cybersecurity", "applications", "identity_access", "organization"]
    select_all = st.checkbox("Select All", value=True, key="select_all")
    selected_domains = all_domains if select_all else st.multiselect("Select domains", all_domains, default=["infrastructure", "cybersecurity"])

    st.markdown('</div></div>', unsafe_allow_html=True)

    # Run button
    can_run = bool(target_name) and bool(selected_domains) and (use_sample or uploaded_files or notes)

    if st.button("🚀 Run Analysis", type="primary", disabled=not can_run, use_container_width=True):
        st.info("Analysis would run here...")


# =============================================================================
# PAGE: REVIEW
# =============================================================================
def page_review():
    page_header("Review Queue", "Review and approve changes from incremental analysis")

    # Check if we have any pending changes (would come from document processing)
    # For now, show demo/placeholder content

    # Initialize review state
    if "pending_changes" not in st.session_state:
        st.session_state["pending_changes"] = {
            "tier1": [],  # Auto-apply: low-risk, high confidence
            "tier2": [],  # Batch review: medium confidence
            "tier3": [],  # Individual review: conflicts
        }

    tier1_count = len(st.session_state["pending_changes"]["tier1"])
    tier2_count = len(st.session_state["pending_changes"]["tier2"])
    tier3_count = len(st.session_state["pending_changes"]["tier3"])
    total_count = tier1_count + tier2_count + tier3_count

    if total_count == 0:
        # Empty state
        st.markdown('''
        <div class="card" style="text-align: center; padding: 60px 40px;">
            <div style="font-size: 4em; margin-bottom: 20px;">✅</div>
            <h2 style="margin-bottom: 10px;">No Pending Changes</h2>
            <p class="text-muted" style="margin-bottom: 30px; max-width: 400px; margin-left: auto; margin-right: auto;">
                All changes have been reviewed. Upload new documents to generate more analysis updates.
            </p>
        </div>
        ''', unsafe_allow_html=True)

        if st.button("Go to Documents", type="primary"):
            st.session_state["page"] = "documents"
            st.rerun()
        return

    # Tier cards
    st.markdown(f'<p style="color: var(--text-muted); margin-bottom: 1rem;">Total pending changes: {total_count}</p>', unsafe_allow_html=True)

    render_tier_cards([
        {
            "number": 1,
            "name": "Auto-Apply",
            "count": tier1_count,
            "description": "Low-risk, high confidence changes",
            "action_label": "Auto-Apply All" if tier1_count > 0 else None,
            "action_callback": lambda: auto_apply_tier1()
        },
        {
            "number": 2,
            "name": "Batch Review",
            "count": tier2_count,
            "description": "Quick scan recommended",
            "action_label": "Review Batch" if tier2_count > 0 else None,
            "action_callback": lambda: st.session_state.update({"review_mode": "batch"})
        },
        {
            "number": 3,
            "name": "Conflicts",
            "count": tier3_count,
            "description": "Conflicts with verified facts",
            "action_label": "Resolve Conflicts" if tier3_count > 0 else None,
            "action_callback": lambda: st.session_state.update({"review_mode": "conflicts"})
        },
    ])

    st.divider()

    # Show review content based on mode
    review_mode = st.session_state.get("review_mode", None)

    if review_mode == "batch":
        st.subheader("Batch Review")
        st.info("Batch review mode - review multiple changes at once.")
        # Would show batch review UI here

    elif review_mode == "conflicts":
        st.subheader("Conflict Resolution")
        st.warning("Conflict resolution mode - these changes conflict with verified facts.")
        # Would show conflict resolution UI here

    # Recent activity
    st.subheader("Recent Review Activity")
    st.markdown('''
    <div class="card">
        <div class="card-body">
            <p style="color: var(--text-muted); text-align: center; padding: 2rem;">
                No recent review activity. Changes will appear here after document processing.
            </p>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def auto_apply_tier1():
    """Auto-apply all Tier 1 changes."""
    st.session_state["pending_changes"]["tier1"] = []
    st.success("All Tier 1 changes have been applied!")


# =============================================================================
# PAGE: DOCUMENTS
# =============================================================================
def page_documents():
    page_header("Document Management", "Upload documents for incremental analysis updates")

    # Initialize document state
    if "documents" not in st.session_state:
        st.session_state["documents"] = []
    if "analysis_runs" not in st.session_state:
        st.session_state["analysis_runs"] = []

    # Upload section
    st.markdown('''
    <div class="card">
        <div class="card-header">
            <span class="card-title">Upload Documents</span>
        </div>
        <div class="card-body">
    ''', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Drag & drop files or click to browse",
        type=["pdf", "txt", "md", "docx", "xlsx"],
        accept_multiple_files=True,
        key="doc_upload",
        help="Supports: PDF, TXT, MD, DOCX, XLSX"
    )

    if uploaded_files:
        st.success(f"✓ {len(uploaded_files)} file(s) ready for upload")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Upload & Analyze", type="primary", use_container_width=True):
                # Process uploaded files
                for file in uploaded_files:
                    st.session_state["documents"].append({
                        "filename": file.name,
                        "status": "processed",
                        "version": 1,
                        "facts_count": 0,
                        "uploaded_at": datetime.now().isoformat()[:10]
                    })
                st.success(f"Uploaded {len(uploaded_files)} document(s)!")
                st.rerun()
        with col2:
            if st.button("Clear", type="secondary", use_container_width=True):
                st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)

    # What's New section (if there are recent changes)
    fact_store, reasoning_store = load_data()
    if fact_store and hasattr(fact_store, 'facts'):
        # Show recently added facts (mock - would track actual changes)
        recent_facts = fact_store.facts[:5] if len(fact_store.facts) > 5 else fact_store.facts

        if recent_facts:
            st.markdown('''
            <div class="card" style="margin-top: 1rem;">
                <div class="card-header">
                    <span class="card-title">Recent Facts</span>
                </div>
                <div class="card-body">
            ''', unsafe_allow_html=True)

            for fact in recent_facts:
                domain = (fact.domain or "").replace("_", " ").title()
                st.markdown(f'''
                <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border-default);">
                    <span class="change-badge new">NEW</span>
                    <span style="color: var(--text-secondary); font-size: 0.875rem; min-width: 100px;">{domain}</span>
                    <span style="font-size: 0.875rem;">{fact.item[:80]}{"..." if len(fact.item) > 80 else ""}</span>
                </div>
                ''', unsafe_allow_html=True)

            st.markdown('</div></div>', unsafe_allow_html=True)

    # Document Registry
    st.markdown('''
    <div class="card" style="margin-top: 1rem;">
        <div class="card-header">
            <span class="card-title">Document Registry</span>
        </div>
    ''', unsafe_allow_html=True)

    docs = st.session_state.get("documents", [])

    if docs:
        import pandas as pd

        df = pd.DataFrame(docs)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "filename": st.column_config.TextColumn("Document", width="large"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "version": st.column_config.NumberColumn("Version", width="small"),
                "facts_count": st.column_config.NumberColumn("Facts", width="small"),
                "uploaded_at": st.column_config.TextColumn("Uploaded", width="medium"),
            }
        )
    else:
        # Check if there are files in the input directory
        input_dir = Path("data/input")
        sample_files = []
        if input_dir.exists():
            sample_files = list(input_dir.glob("*.pdf")) + list(input_dir.glob("*.txt")) + list(input_dir.glob("*.md"))

        if sample_files:
            st.info(f"Found {len(sample_files)} sample document(s) in data/input/. Go to Upload to analyze them.")
        else:
            st.markdown('''
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                <p>No documents uploaded yet.</p>
                <p style="font-size: 0.875rem;">Upload documents above to track and enable incremental analysis.</p>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Analysis History
    runs = st.session_state.get("analysis_runs", [])
    if runs:
        st.markdown('''
        <div class="card" style="margin-top: 1rem;">
            <div class="card-header">
                <span class="card-title">Analysis History</span>
            </div>
            <div class="card-body">
        ''', unsafe_allow_html=True)

        for run in runs:
            st.markdown(f'''
            <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-default);">
                <span class="font-mono">{run.get("run_id", "N/A")}</span>
                <span>{run.get("documents_processed", 0)} docs processed</span>
                <span style="color: var(--text-muted);">{run.get("started_at", "")[:10]}</span>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)


# =============================================================================
# MAIN
# =============================================================================
def main():
    # Inject CSS
    st.markdown(CSS_TOKENS, unsafe_allow_html=True)

    # Render nav bar
    render_nav_bar()

    # Main container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Route to page
    page = st.session_state.get("page", "dashboard")

    if page == "dashboard":
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
    elif page == "review":
        page_review()
    elif page == "documents":
        page_documents()
    elif page == "upload":
        page_upload()
    else:
        page_dashboard()

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
