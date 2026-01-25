"""
Styles Module

CSS theme matching Flask app design system.

Step 199 of the alignment plan.
"""

# =============================================================================
# DESIGN TOKENS (matching Flask tokens.css)
# =============================================================================

COLORS = {
    # Background layers
    "bg_base": "#fafaf9",
    "bg_surface": "#ffffff",
    "bg_surface_raised": "#ffffff",
    "bg_surface_sunken": "#f5f5f4",

    # Border colors
    "border_default": "#e7e5e4",
    "border_muted": "#d6d3d1",

    # Text colors
    "text_primary": "#1c1917",
    "text_secondary": "#44403c",
    "text_muted": "#78716c",
    "text_inverse": "#ffffff",

    # Accent (Orange)
    "accent": "#f97316",
    "accent_hover": "#ea580c",
    "accent_active": "#c2410c",
    "accent_subtle": "#fff7ed",

    # Semantic colors
    "critical": "#dc2626",
    "critical_bg": "#fef2f2",
    "high": "#ea580c",
    "high_bg": "#fff7ed",
    "medium": "#ca8a04",
    "medium_bg": "#fefce8",
    "low": "#16a34a",
    "low_bg": "#f0fdf4",
    "info": "#0284c7",
    "info_bg": "#f0f9ff",

    # Domain colors
    "infrastructure": "#3b82f6",
    "network": "#6366f1",
    "cybersecurity": "#ec4899",
    "applications": "#10b981",
    "identity_access": "#f59e0b",
    "organization": "#8b5cf6",
}

SPACING = {
    "1": "0.25rem",
    "2": "0.5rem",
    "3": "0.75rem",
    "4": "1rem",
    "5": "1.25rem",
    "6": "1.5rem",
    "8": "2rem",
}

RADIUS = {
    "sm": "0.25rem",
    "md": "0.375rem",
    "lg": "0.5rem",
    "xl": "0.75rem",
    "full": "9999px",
}

SHADOWS = {
    "sm": "0 1px 2px 0 rgba(0,0,0,0.05)",
    "md": "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)",
    "lg": "0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1)",
}


# =============================================================================
# MAIN CSS (matching Flask base.html styling)
# =============================================================================

def get_main_css() -> str:
    """Get the main CSS stylesheet matching Flask design."""
    return f"""
    <style>
    /* =================================================================
       DESIGN TOKENS AS CSS VARIABLES
       ================================================================= */
    :root {{
        /* Background layers */
        --bg-base: {COLORS["bg_base"]};
        --bg-surface: {COLORS["bg_surface"]};
        --bg-surface-raised: {COLORS["bg_surface_raised"]};
        --bg-surface-sunken: {COLORS["bg_surface_sunken"]};

        /* Borders */
        --border-default: {COLORS["border_default"]};
        --border-muted: {COLORS["border_muted"]};

        /* Text */
        --text-primary: {COLORS["text_primary"]};
        --text-secondary: {COLORS["text_secondary"]};
        --text-muted: {COLORS["text_muted"]};

        /* Accent */
        --accent: {COLORS["accent"]};
        --accent-hover: {COLORS["accent_hover"]};
        --accent-subtle: {COLORS["accent_subtle"]};

        /* Semantic */
        --critical: {COLORS["critical"]};
        --critical-bg: {COLORS["critical_bg"]};
        --high: {COLORS["high"]};
        --high-bg: {COLORS["high_bg"]};
        --medium: {COLORS["medium"]};
        --medium-bg: {COLORS["medium_bg"]};
        --low: {COLORS["low"]};
        --low-bg: {COLORS["low_bg"]};
        --info: {COLORS["info"]};
        --info-bg: {COLORS["info_bg"]};

        /* Typography */
        --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        --font-mono: 'SF Mono', Monaco, 'Cascadia Code', monospace;
    }}

    /* =================================================================
       STREAMLIT OVERRIDES
       ================================================================= */

    /* Hide default Streamlit elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{display: none;}}

    /* Main app background */
    .stApp {{
        background: var(--bg-base);
    }}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background: var(--bg-surface);
        border-right: 1px solid var(--border-default);
    }}

    section[data-testid="stSidebar"] > div {{
        padding-top: 1rem;
    }}

    /* =================================================================
       TYPOGRAPHY
       ================================================================= */
    h1 {{
        font-family: var(--font-sans);
        font-weight: 700;
        color: var(--text-primary);
        font-size: 1.5rem !important;
        margin-bottom: 0.25rem !important;
    }}

    h2, h3, h4 {{
        font-family: var(--font-sans);
        font-weight: 600;
        color: var(--text-primary);
    }}

    p, span, div {{
        font-family: var(--font-sans);
    }}

    /* =================================================================
       BUTTONS
       ================================================================= */
    .stButton > button {{
        font-family: var(--font-sans);
        font-weight: 500;
        font-size: 0.875rem;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        transition: all 150ms ease;
    }}

    .stButton > button[kind="primary"] {{
        background-color: var(--accent) !important;
        border-color: var(--accent) !important;
        color: white !important;
    }}

    .stButton > button[kind="primary"]:hover {{
        background-color: var(--accent-hover) !important;
        border-color: var(--accent-hover) !important;
    }}

    .stButton > button[kind="secondary"] {{
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-default) !important;
        color: var(--text-primary) !important;
    }}

    .stButton > button[kind="secondary"]:hover {{
        background: var(--bg-surface-sunken) !important;
        border-color: var(--border-muted) !important;
    }}

    /* =================================================================
       METRICS (Dashboard cards)
       ================================================================= */
    [data-testid="stMetric"] {{
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: 0.5rem;
        padding: 1.25rem;
        box-shadow: {SHADOWS["sm"]};
    }}

    [data-testid="stMetricLabel"] {{
        font-size: 0.875rem !important;
        color: var(--text-muted) !important;
        font-weight: 500 !important;
    }}

    [data-testid="stMetricValue"] {{
        font-size: 1.875rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        font-variant-numeric: tabular-nums;
    }}

    /* =================================================================
       CARDS & CONTAINERS
       ================================================================= */
    .metric-card {{
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: 0.5rem;
        padding: 1.25rem;
        box-shadow: {SHADOWS["sm"]};
    }}

    .metric-card-warning {{
        border-left: 3px solid var(--critical);
    }}

    .card {{
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: 0.5rem;
        box-shadow: {SHADOWS["sm"]};
    }}

    /* =================================================================
       BADGES
       ================================================================= */
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }}

    .badge-critical {{ background: var(--critical-bg); color: var(--critical); }}
    .badge-high {{ background: var(--high-bg); color: var(--high); }}
    .badge-medium {{ background: var(--medium-bg); color: var(--medium); }}
    .badge-low {{ background: var(--low-bg); color: var(--low); }}
    .badge-info {{ background: var(--info-bg); color: var(--info); }}

    .badge-day1 {{ background: var(--critical-bg); color: var(--critical); }}
    .badge-day100 {{ background: var(--high-bg); color: var(--high); }}
    .badge-post100 {{ background: var(--info-bg); color: var(--info); }}

    /* =================================================================
       TABS
       ================================================================= */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.25rem;
        background: var(--bg-surface-sunken);
        padding: 0.25rem;
        border-radius: 0.5rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 0.375rem;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-muted);
        padding: 0.5rem 1rem;
        background: transparent;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--text-primary);
    }}

    .stTabs [aria-selected="true"] {{
        background: var(--bg-surface) !important;
        color: var(--text-primary) !important;
        box-shadow: {SHADOWS["sm"]};
    }}

    /* =================================================================
       EXPANDERS
       ================================================================= */
    .streamlit-expanderHeader {{
        font-weight: 600;
        font-size: 0.875rem;
        color: var(--text-primary);
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: 0.5rem;
    }}

    .streamlit-expanderContent {{
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-top: none;
        border-radius: 0 0 0.5rem 0.5rem;
    }}

    /* =================================================================
       SELECT BOXES & INPUTS
       ================================================================= */
    .stSelectbox > div > div {{
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: 0.375rem;
    }}

    .stTextInput > div > div > input {{
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: 0.375rem;
        font-size: 0.875rem;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-subtle);
    }}

    /* =================================================================
       DATAFRAMES & TABLES
       ================================================================= */
    .stDataFrame {{
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: 0.5rem;
        overflow: hidden;
    }}

    /* =================================================================
       PROGRESS BARS
       ================================================================= */
    .stProgress > div > div > div {{
        background-color: var(--accent);
    }}

    /* =================================================================
       FILE UPLOADER
       ================================================================= */
    .stFileUploader > div {{
        background: var(--bg-surface);
        border: 2px dashed var(--border-default);
        border-radius: 0.5rem;
        padding: 2rem;
    }}

    .stFileUploader > div:hover {{
        border-color: var(--accent);
        background: var(--accent-subtle);
    }}

    /* =================================================================
       DIVIDERS
       ================================================================= */
    hr {{
        border: none;
        border-top: 1px solid var(--border-default);
        margin: 1.5rem 0;
    }}

    /* =================================================================
       ALERTS
       ================================================================= */
    .stAlert {{
        border-radius: 0.5rem;
        font-size: 0.875rem;
    }}

    /* =================================================================
       CUSTOM COMPONENTS
       ================================================================= */

    /* Filters bar */
    .filters-bar {{
        display: flex;
        gap: 0.75rem;
        padding: 1rem;
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
        align-items: center;
    }}

    /* Page header */
    .page-header {{
        margin-bottom: 1.5rem;
    }}

    .page-header h1 {{
        font-size: 1.5rem !important;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.25rem !important;
    }}

    .page-header p {{
        color: var(--text-muted);
        font-size: 0.875rem;
    }}

    /* Metrics row */
    .metrics-row {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }}

    @media (max-width: 1024px) {{
        .metrics-row {{ grid-template-columns: repeat(2, 1fr); }}
    }}

    @media (max-width: 640px) {{
        .metrics-row {{ grid-template-columns: 1fr; }}
    }}

    /* Cost display */
    .cost-range {{
        font-family: var(--font-mono);
        font-size: 0.875rem;
        color: var(--text-secondary);
    }}

    /* Empty state */
    .empty-state {{
        text-align: center;
        padding: 3rem 1.5rem;
        color: var(--text-muted);
    }}

    .empty-state-icon {{
        font-size: 2rem;
        margin-bottom: 1rem;
    }}

    .empty-state-title {{
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }}

    /* Links */
    a {{
        color: var(--accent);
        text-decoration: none;
        font-weight: 500;
    }}

    a:hover {{
        color: var(--accent-hover);
        text-decoration: underline;
    }}

    /* Sidebar navigation buttons */
    section[data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        justify-content: flex-start;
        text-align: left;
        background: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        font-weight: 500;
        padding: 0.5rem 0.75rem;
        border-radius: 0.375rem;
    }}

    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: var(--bg-surface-sunken) !important;
        color: var(--text-primary) !important;
    }}

    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: var(--accent-subtle) !important;
        color: var(--accent) !important;
    }}

    /* Radio buttons as tabs */
    .stRadio > div {{
        gap: 0.25rem;
    }}

    .stRadio > div[data-baseweb="radio"] {{
        background: var(--bg-surface-sunken);
        padding: 0.25rem;
        border-radius: 0.5rem;
    }}
    </style>
    """


def inject_styles():
    """Inject CSS styles into Streamlit app."""
    import streamlit as st
    st.markdown(get_main_css(), unsafe_allow_html=True)


# =============================================================================
# COMPONENT STYLE HELPERS
# =============================================================================

def card_style(variant: str = "default") -> str:
    """Get card CSS style."""
    variants = {
        "default": f"""
            background: {COLORS["bg_surface"]};
            border: 1px solid {COLORS["border_default"]};
            border-radius: {RADIUS["lg"]};
            padding: {SPACING["5"]};
            box-shadow: {SHADOWS["sm"]};
        """,
        "primary": f"""
            background: {COLORS["bg_surface"]};
            border: 2px solid {COLORS["accent"]};
            border-radius: {RADIUS["lg"]};
            padding: {SPACING["5"]};
            box-shadow: {SHADOWS["md"]};
        """,
        "warning": f"""
            background: {COLORS["bg_surface"]};
            border: 1px solid {COLORS["border_default"]};
            border-left: 3px solid {COLORS["critical"]};
            border-radius: {RADIUS["lg"]};
            padding: {SPACING["5"]};
            box-shadow: {SHADOWS["sm"]};
        """,
        "sunken": f"""
            background: {COLORS["bg_surface_sunken"]};
            border: 1px dashed {COLORS["border_default"]};
            border-radius: {RADIUS["lg"]};
            padding: {SPACING["5"]};
        """,
    }
    return variants.get(variant, variants["default"])


def badge_style(severity: str) -> str:
    """Get badge CSS style for severity."""
    severity_styles = {
        "critical": f"background: {COLORS['critical_bg']}; color: {COLORS['critical']};",
        "high": f"background: {COLORS['high_bg']}; color: {COLORS['high']};",
        "medium": f"background: {COLORS['medium_bg']}; color: {COLORS['medium']};",
        "low": f"background: {COLORS['low_bg']}; color: {COLORS['low']};",
        "info": f"background: {COLORS['info_bg']}; color: {COLORS['info']};",
    }

    base = """
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    """

    return base + severity_styles.get(severity, "")
