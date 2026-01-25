"""
Upload View

Enhanced document upload experience.

Steps 186-195 of the alignment plan.
"""

import streamlit as st
from typing import Optional, List, Any
from pathlib import Path

from ..components.layout import page_header, section_header
from ..utils.formatting import format_file_size
from ..utils.validators import validate_file_type, validate_file_size


def render_upload_view(
    on_submit: Optional[callable] = None,
) -> dict:
    """
    Render the upload view page.

    Args:
        on_submit: Optional callback when files are submitted

    Returns:
        Dictionary with upload state
    """
    page_header(
        title="Upload Documents",
        subtitle="Upload IT documentation for analysis",
        icon="📤",
    )

    result = {
        "target_files": [],
        "buyer_files": [],
        "notes": "",
        "ready": False,
    }

    # Use sample docs option
    use_sample = st.checkbox(
        "🧪 Use sample documents (for testing)",
        value=False,
        help="Load documents from data/input/ directory",
        key="upload_use_sample",
    )

    if use_sample:
        result["use_sample"] = True
        _render_sample_docs_info()
        result["ready"] = True
        return result

    # Target documents section
    section_header("Target Company Documents", icon="🎯", level=4)
    st.caption("Upload IT profiles, security assessments, architecture diagrams")

    target_files = st.file_uploader(
        "Upload files",
        type=["pdf", "txt", "md", "docx"],
        accept_multiple_files=True,
        key="target_upload",
        label_visibility="collapsed",
    )

    if target_files:
        _render_file_list(target_files, "target")
        result["target_files"] = target_files

    # Notes section
    st.divider()
    section_header("Quick Notes", subtitle="Optional meeting notes or discussion points", icon="📝", level=4)

    notes = st.text_area(
        "Notes",
        height=120,
        placeholder="From call with CTO:\n- VMware upgrade planned for Q2\n- Security team hiring 2 more\n- Budget ~$2M annually",
        key="target_notes",
        label_visibility="collapsed",
    )

    if notes:
        result["notes"] = notes

    # Buyer documents (optional)
    with st.expander("📁 Buyer / Integration Context (optional)"):
        st.caption("Upload buyer documents for integration analysis context")

        buyer_files = st.file_uploader(
            "Upload buyer files",
            type=["pdf", "txt", "md", "docx"],
            accept_multiple_files=True,
            key="buyer_upload",
            label_visibility="collapsed",
        )

        if buyer_files:
            _render_file_list(buyer_files, "buyer")
            result["buyer_files"] = buyer_files

    # Summary
    st.divider()
    _render_upload_summary(result)

    # Check readiness
    has_content = bool(target_files) or bool(notes.strip())
    result["ready"] = has_content

    return result


def _render_sample_docs_info() -> None:
    """Render info about sample documents."""
    try:
        from config_v2 import INPUT_DIR
        sample_dir = INPUT_DIR
    except ImportError:
        sample_dir = Path("data/input")

    if sample_dir.exists():
        files = list(sample_dir.glob("*.pdf")) + list(sample_dir.glob("*.txt")) + list(sample_dir.glob("*.md"))
        if files:
            st.success(f"✓ Found {len(files)} sample document(s) in {sample_dir}")
            with st.expander("View sample files"):
                for f in files[:10]:
                    size = f.stat().st_size
                    st.caption(f"📄 {f.name} ({format_file_size(size)})")
                if len(files) > 10:
                    st.caption(f"... and {len(files) - 10} more")
        else:
            st.warning(f"No sample documents found in {sample_dir}")
    else:
        st.warning(f"Sample directory not found: {sample_dir}")


def _render_file_list(files: List[Any], entity: str) -> None:
    """Render a list of uploaded files with validation."""
    st.markdown(f"**{len(files)} file(s) uploaded:**")

    total_size = 0
    has_errors = False

    for file in files:
        col1, col2, col3 = st.columns([3, 1, 1])

        # Get file info
        file.seek(0)
        content = file.read()
        file.seek(0)
        size = len(content)
        total_size += size

        # Validate
        type_valid, type_msg = validate_file_type(file.name)
        size_valid, size_msg = validate_file_size(size)

        with col1:
            icon = "📄" if type_valid else "⚠️"
            st.markdown(f"{icon} **{file.name}**")

        with col2:
            st.caption(format_file_size(size))

        with col3:
            if not type_valid:
                st.error("Invalid type", icon="⚠️")
                has_errors = True
            elif not size_valid:
                st.error("Too large", icon="⚠️")
                has_errors = True
            else:
                st.success("OK", icon="✅")

    # Total size
    st.caption(f"Total: {format_file_size(total_size)}")

    if has_errors:
        st.warning("Some files have validation errors and may not be processed")


def _render_upload_summary(result: dict) -> None:
    """Render upload summary."""
    section_header("Summary", icon="📋", level=4)

    col1, col2, col3 = st.columns(3)

    target_count = len(result.get("target_files", []))
    buyer_count = len(result.get("buyer_files", []))
    has_notes = bool(result.get("notes", "").strip())

    with col1:
        icon = "✅" if target_count > 0 else "⚪"
        st.markdown(f"{icon} **Target Files:** {target_count}")

    with col2:
        icon = "✅" if buyer_count > 0 else "⚪"
        st.markdown(f"{icon} **Buyer Files:** {buyer_count}")

    with col3:
        icon = "✅" if has_notes else "⚪"
        st.markdown(f"{icon} **Notes:** {'Yes' if has_notes else 'No'}")

    if not result.get("ready"):
        st.info("📤 Upload at least one document or add notes to continue")


def render_upload_widget(
    key_prefix: str = "upload",
    show_buyer: bool = False,
) -> dict:
    """
    Render a compact upload widget for embedding.

    Args:
        key_prefix: Prefix for widget keys
        show_buyer: Whether to show buyer upload

    Returns:
        Dictionary with files and notes
    """
    result = {"files": [], "notes": ""}

    # File upload
    files = st.file_uploader(
        "Upload documents",
        type=["pdf", "txt", "md", "docx"],
        accept_multiple_files=True,
        key=f"{key_prefix}_files",
    )

    if files:
        result["files"] = files
        st.caption(f"✓ {len(files)} file(s) ready")

    # Notes
    notes = st.text_area(
        "Notes (optional)",
        height=80,
        key=f"{key_prefix}_notes",
    )

    if notes:
        result["notes"] = notes

    return result
