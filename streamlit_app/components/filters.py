"""
Filter Components

Reusable filter and pagination components.

Steps 66-68 of the alignment plan.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Tuple


# =============================================================================
# CONSTANTS
# =============================================================================

ALL_DOMAINS = [
    "infrastructure",
    "network",
    "cybersecurity",
    "applications",
    "identity_access",
    "organization",
]

ALL_SEVERITIES = ["critical", "high", "medium", "low"]

ALL_PHASES = ["Day_1", "Day_100", "Post_100"]


# =============================================================================
# SEARCH BOX
# =============================================================================

def search_box(
    key: str,
    placeholder: str = "Search...",
    label: Optional[str] = None,
) -> str:
    """
    Render a search box.

    Args:
        key: Unique key for the input
        placeholder: Placeholder text
        label: Optional label

    Returns:
        The search query string
    """
    return st.text_input(
        label or "Search",
        placeholder=placeholder,
        key=key,
        label_visibility="collapsed" if not label else "visible",
    )


# =============================================================================
# DOMAIN FILTER
# =============================================================================

def domain_filter(
    key: str,
    domains: Optional[List[str]] = None,
    default: str = "All",
    label: str = "Domain",
) -> Optional[str]:
    """
    Render a domain filter dropdown.

    Args:
        key: Unique key for the select
        domains: List of domains to show (default: all)
        default: Default selection
        label: Label for the select

    Returns:
        Selected domain or None for "All"
    """
    available = domains or ALL_DOMAINS
    options = ["All"] + available

    selected = st.selectbox(
        label,
        options=options,
        key=key,
        format_func=lambda x: x.replace("_", " ").title() if x != "All" else "All Domains",
    )

    return None if selected == "All" else selected


def domain_multiselect(
    key: str,
    domains: Optional[List[str]] = None,
    default: Optional[List[str]] = None,
    label: str = "Domains",
) -> List[str]:
    """
    Render a multi-select domain filter.

    Args:
        key: Unique key for the multiselect
        domains: List of domains to show (default: all)
        default: Default selections
        label: Label for the multiselect

    Returns:
        List of selected domains
    """
    available = domains or ALL_DOMAINS

    return st.multiselect(
        label,
        options=available,
        default=default or available,
        key=key,
        format_func=lambda x: x.replace("_", " ").title(),
    )


# =============================================================================
# SEVERITY FILTER
# =============================================================================

def severity_filter(
    key: str,
    severities: Optional[List[str]] = None,
    default: str = "All",
    label: str = "Severity",
) -> Optional[str]:
    """
    Render a severity filter dropdown.

    Args:
        key: Unique key for the select
        severities: List of severities to show (default: all)
        default: Default selection
        label: Label for the select

    Returns:
        Selected severity or None for "All"
    """
    available = severities or ALL_SEVERITIES
    options = ["All"] + available

    selected = st.selectbox(
        label,
        options=options,
        key=key,
        format_func=lambda x: x.title() if x != "All" else "All Severities",
    )

    return None if selected == "All" else selected


def severity_multiselect(
    key: str,
    severities: Optional[List[str]] = None,
    default: Optional[List[str]] = None,
    label: str = "Severities",
) -> List[str]:
    """
    Render a multi-select severity filter.

    Args:
        key: Unique key for the multiselect
        severities: List of severities to show (default: all)
        default: Default selections
        label: Label for the multiselect

    Returns:
        List of selected severities
    """
    available = severities or ALL_SEVERITIES

    return st.multiselect(
        label,
        options=available,
        default=default or available,
        key=key,
        format_func=lambda x: x.title(),
    )


# =============================================================================
# PHASE FILTER
# =============================================================================

def phase_filter(
    key: str,
    phases: Optional[List[str]] = None,
    default: str = "All",
    label: str = "Phase",
) -> Optional[str]:
    """
    Render a phase filter dropdown.

    Args:
        key: Unique key for the select
        phases: List of phases to show (default: all)
        default: Default selection
        label: Label for the select

    Returns:
        Selected phase or None for "All"
    """
    available = phases or ALL_PHASES
    options = ["All"] + available

    phase_labels = {
        "Day_1": "🚨 Day 1",
        "Day_100": "📅 Day 100",
        "Post_100": "🎯 Post-100",
        "All": "All Phases",
    }

    selected = st.selectbox(
        label,
        options=options,
        key=key,
        format_func=lambda x: phase_labels.get(x, x),
    )

    return None if selected == "All" else selected


# =============================================================================
# FILTER BAR
# =============================================================================

def filter_bar(
    key_prefix: str,
    show_search: bool = True,
    show_domain: bool = True,
    show_severity: bool = True,
    show_phase: bool = False,
    columns: int = 4,
) -> Dict[str, Any]:
    """
    Render a complete filter bar with multiple filters.

    Args:
        key_prefix: Prefix for all filter keys
        show_search: Whether to show search box
        show_domain: Whether to show domain filter
        show_severity: Whether to show severity filter
        show_phase: Whether to show phase filter
        columns: Number of columns for layout

    Returns:
        Dictionary of filter values
    """
    filters = {}

    cols = st.columns(columns)
    col_idx = 0

    if show_search:
        with cols[col_idx % columns]:
            filters["search"] = search_box(f"{key_prefix}_search", placeholder="Search...")
        col_idx += 1

    if show_domain:
        with cols[col_idx % columns]:
            filters["domain"] = domain_filter(f"{key_prefix}_domain")
        col_idx += 1

    if show_severity:
        with cols[col_idx % columns]:
            filters["severity"] = severity_filter(f"{key_prefix}_severity")
        col_idx += 1

    if show_phase:
        with cols[col_idx % columns]:
            filters["phase"] = phase_filter(f"{key_prefix}_phase")
        col_idx += 1

    return filters


# =============================================================================
# PAGINATION
# =============================================================================

def pagination(
    total_items: int,
    items_per_page: int,
    key: str,
    show_info: bool = True,
) -> Tuple[int, int]:
    """
    Render pagination controls.

    Args:
        total_items: Total number of items
        items_per_page: Items per page
        key: Unique key for the page state

    Returns:
        Tuple of (start_index, end_index)
    """
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

    # Initialize page state
    page_key = f"{key}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    current_page = st.session_state[page_key]

    # Ensure valid page
    if current_page >= total_pages:
        current_page = total_pages - 1
        st.session_state[page_key] = current_page

    # Calculate indices
    start = current_page * items_per_page
    end = min(start + items_per_page, total_items)

    # Render controls
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Previous", key=f"{key}_prev", disabled=current_page <= 0):
            st.session_state[page_key] = current_page - 1
            st.rerun()

    with col2:
        if show_info:
            st.markdown(
                f"<div style='text-align: center; padding: 0.5rem;'>"
                f"Page {current_page + 1} of {total_pages} ({total_items} items)"
                f"</div>",
                unsafe_allow_html=True
            )

    with col3:
        if st.button("Next →", key=f"{key}_next", disabled=current_page >= total_pages - 1):
            st.session_state[page_key] = current_page + 1
            st.rerun()

    return start, end


def reset_pagination(key: str):
    """Reset pagination to first page."""
    page_key = f"{key}_page"
    if page_key in st.session_state:
        st.session_state[page_key] = 0


# =============================================================================
# SORT CONTROLS
# =============================================================================

def sort_control(
    key: str,
    options: List[Tuple[str, str]],
    default: str = None,
    label: str = "Sort by",
) -> Tuple[str, bool]:
    """
    Render sort controls.

    Args:
        key: Unique key for the control
        options: List of (value, label) tuples
        default: Default sort option
        label: Label for the control

    Returns:
        Tuple of (sort_field, ascending)
    """
    col1, col2 = st.columns([3, 1])

    with col1:
        sort_by = st.selectbox(
            label,
            options=[opt[0] for opt in options],
            format_func=lambda x: dict(options).get(x, x),
            key=f"{key}_sort",
        )

    with col2:
        ascending = st.checkbox("Asc", value=False, key=f"{key}_asc")

    return sort_by, ascending
