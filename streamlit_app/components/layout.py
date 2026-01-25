"""
Layout Components

Reusable layout components for page structure.

Steps 91-98 of the alignment plan.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Callable


# =============================================================================
# PAGE HEADER
# =============================================================================

def page_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Render a page header with optional subtitle and action buttons.

    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Optional emoji icon
        actions: Optional list of action button configs
    """
    if actions:
        cols = st.columns([4, 1])
        with cols[0]:
            header_text = f"{icon} {title}" if icon else title
            st.title(header_text)
            if subtitle:
                st.caption(subtitle)
        with cols[1]:
            for action in actions:
                if st.button(
                    action.get("label", "Action"),
                    key=action.get("key"),
                    type=action.get("type", "secondary"),
                    use_container_width=True,
                ):
                    callback = action.get("callback")
                    if callback:
                        callback()
    else:
        header_text = f"{icon} {title}" if icon else title
        st.title(header_text)
        if subtitle:
            st.caption(subtitle)


def section_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    level: int = 3,
) -> None:
    """
    Render a section header.

    Args:
        title: Section title
        subtitle: Optional subtitle
        icon: Optional emoji icon
        level: Header level (1-6)
    """
    header_text = f"{icon} {title}" if icon else title
    prefix = "#" * level
    st.markdown(f"{prefix} {header_text}")
    if subtitle:
        st.caption(subtitle)


# =============================================================================
# METRIC ROW
# =============================================================================

def metric_row(
    metrics: List[Dict[str, Any]],
    columns: Optional[int] = None,
) -> None:
    """
    Render a row of metric cards.

    Args:
        metrics: List of metric configs with keys: value, label, delta, icon
        columns: Number of columns (default: len(metrics))
    """
    num_cols = columns or len(metrics)
    cols = st.columns(num_cols)

    for i, metric in enumerate(metrics):
        with cols[i % num_cols]:
            value = metric.get("value", 0)
            label = metric.get("label", "")
            delta = metric.get("delta")
            help_text = metric.get("help")

            st.metric(
                label=label,
                value=value,
                delta=delta,
                help=help_text,
            )


def metric_row_html(
    metrics: List[Dict[str, Any]],
) -> None:
    """
    Render a styled row of metric cards using HTML.

    Args:
        metrics: List of metric configs with keys: value, label, delta, icon, color
    """
    from .cards import metric_card

    html = '<div style="display: flex; gap: 1rem; flex-wrap: wrap;">'

    for metric in metrics:
        html += f'''
        <div style="flex: 1; min-width: 150px;">
            {metric_card(
                value=metric.get("value", 0),
                label=metric.get("label", ""),
                delta=metric.get("delta"),
                icon=metric.get("icon"),
                color=metric.get("color"),
            )}
        </div>
        '''

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# CARD GRID
# =============================================================================

def card_grid(
    items: List[Any],
    render_func: Callable[[Any], None],
    columns: int = 2,
    key_prefix: str = "card",
) -> None:
    """
    Render items in a grid of cards.

    Args:
        items: List of items to render
        render_func: Function to render each item
        columns: Number of columns
        key_prefix: Prefix for card keys
    """
    cols = st.columns(columns)

    for i, item in enumerate(items):
        with cols[i % columns]:
            render_func(item)


# =============================================================================
# TAB CONTAINER
# =============================================================================

def tab_container(
    tabs: List[Dict[str, Any]],
) -> Optional[str]:
    """
    Render a tab container with content.

    Args:
        tabs: List of tab configs with keys: label, icon, content_func

    Returns:
        The selected tab label
    """
    tab_labels = [
        f"{t.get('icon', '')} {t['label']}" if t.get('icon') else t['label']
        for t in tabs
    ]

    selected_tabs = st.tabs(tab_labels)

    for i, (tab, config) in enumerate(zip(selected_tabs, tabs)):
        with tab:
            content_func = config.get("content_func")
            if content_func:
                content_func()

    return None  # Streamlit tabs don't return selected


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

def sidebar_navigation(
    items: List[Dict[str, Any]],
    current: str,
    key: str = "nav",
) -> str:
    """
    Render sidebar navigation.

    Args:
        items: List of nav items with keys: id, label, icon
        current: Currently selected item id
        key: Unique key for the navigation

    Returns:
        Selected item id
    """
    with st.sidebar:
        for item in items:
            item_id = item["id"]
            label = item.get("label", item_id)
            icon = item.get("icon", "")

            button_label = f"{icon} {label}" if icon else label
            is_current = item_id == current

            # Style current item differently
            button_type = "primary" if is_current else "secondary"

            if st.button(
                button_label,
                key=f"{key}_{item_id}",
                use_container_width=True,
                type=button_type,
            ):
                return item_id

    return current


# =============================================================================
# STEPPER
# =============================================================================

def render_stepper(
    steps: List[Dict[str, Any]],
    current_step: int = 0,
) -> None:
    """
    Render a stepper/progress indicator.

    Args:
        steps: List of step configs with keys: title, subtitle, completed
        current_step: Current step index (0-based)
    """
    html = '<div style="padding: 1rem 0;">'

    for i, step in enumerate(steps):
        is_completed = step.get("completed", i < current_step)
        is_current = i == current_step

        # CSS classes
        css_class = "stepper-item"
        if is_current:
            css_class += " active"
        elif is_completed:
            css_class += " completed"

        # Step number display
        number_display = "✓" if is_completed else str(i + 1)

        html += f'''
        <div style="
            display: flex;
            align-items: flex-start;
            padding: 0.75rem 1rem;
            margin-bottom: 0.25rem;
            border-radius: 8px;
            {'background: #fff7ed; border: 2px solid #f97316;' if is_current else
             'background: #fef3e8;' if is_completed else ''}
        ">
            <div style="
                width: 28px;
                height: 28px;
                border-radius: 50%;
                {'background: #f97316; color: white;' if is_current else
                 'background: #22c55e; color: white;' if is_completed else
                 'background: #e5e7eb; color: #a8a29e;'}
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 0.85rem;
                margin-right: 0.75rem;
                flex-shrink: 0;
            ">{number_display}</div>
            <div>
                <div style="
                    font-weight: 600;
                    font-size: 0.9rem;
                    color: {'#f97316' if is_current else '#1c1917'};
                ">{step.get('title', f'Step {i+1}')}</div>
                <div style="font-size: 0.75rem; color: #a8a29e;">
                    {step.get('subtitle', '')}
                </div>
            </div>
        </div>
        '''

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# EMPTY STATE
# =============================================================================

def empty_state(
    title: str,
    message: str,
    icon: str = "📭",
    action: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render an empty state placeholder.

    Args:
        title: Empty state title
        message: Descriptive message
        icon: Emoji icon
        action: Optional action button config
    """
    st.markdown(f'''
    <div style="
        text-align: center;
        padding: 3rem 2rem;
        background: #f5f5f4;
        border-radius: 12px;
        margin: 1rem 0;
    ">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <div style="font-size: 1.25rem; font-weight: 600; color: #1c1917; margin-bottom: 0.5rem;">
            {title}
        </div>
        <div style="font-size: 0.9rem; color: #57534e; max-width: 400px; margin: 0 auto;">
            {message}
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if action:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                action.get("label", "Action"),
                key=action.get("key"),
                type="primary",
                use_container_width=True,
            ):
                callback = action.get("callback")
                if callback:
                    callback()


# =============================================================================
# LOADING STATE
# =============================================================================

def loading_state(
    message: str = "Loading...",
    show_spinner: bool = True,
) -> None:
    """
    Render a loading state placeholder.

    Args:
        message: Loading message
        show_spinner: Whether to show spinner
    """
    if show_spinner:
        with st.spinner(message):
            st.empty()
    else:
        st.markdown(f'''
        <div style="
            text-align: center;
            padding: 2rem;
            color: #57534e;
        ">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⏳</div>
            <div>{message}</div>
        </div>
        ''', unsafe_allow_html=True)


# =============================================================================
# DIVIDER WITH LABEL
# =============================================================================

def labeled_divider(label: str) -> None:
    """
    Render a divider with a centered label.

    Args:
        label: The label text
    """
    st.markdown(f'''
    <div style="
        display: flex;
        align-items: center;
        margin: 1.5rem 0;
    ">
        <div style="flex: 1; height: 1px; background: #e5e7eb;"></div>
        <div style="
            padding: 0 1rem;
            font-size: 0.8rem;
            color: #a8a29e;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        ">{label}</div>
        <div style="flex: 1; height: 1px; background: #e5e7eb;"></div>
    </div>
    ''', unsafe_allow_html=True)
