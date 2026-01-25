"""
Validation Utilities

Input validation functions for the Streamlit app.
"""

from typing import List, Tuple, Optional
from pathlib import Path


# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".xlsx"}

# File size limits
MAX_FILE_SIZE_MB = 50
MAX_TOTAL_SIZE_MB = 200

# All available domains
ALL_DOMAINS = [
    "infrastructure",
    "network",
    "cybersecurity",
    "applications",
    "identity_access",
    "organization",
]


def validate_file_type(filename: str) -> Tuple[bool, str]:
    """
    Validate that a file has an allowed extension.

    Args:
        filename: Name of the file

    Returns:
        Tuple of (is_valid, error_message)
    """
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        return False, f"File type '{suffix}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"

    return True, ""


def validate_file_size(size_bytes: int) -> Tuple[bool, str]:
    """
    Validate that a file is within size limits.

    Args:
        size_bytes: File size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File too large ({size_mb:.1f}MB). Maximum size: {MAX_FILE_SIZE_MB}MB"

    return True, ""


def validate_total_size(total_bytes: int) -> Tuple[bool, str]:
    """
    Validate that total upload size is within limits.

    Args:
        total_bytes: Total size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    total_mb = total_bytes / (1024 * 1024)

    if total_mb > MAX_TOTAL_SIZE_MB:
        return False, f"Total upload size ({total_mb:.1f}MB) exceeds limit ({MAX_TOTAL_SIZE_MB}MB)"

    return True, ""


def validate_domain_selection(domains: List[str]) -> Tuple[bool, str]:
    """
    Validate domain selection.

    Args:
        domains: List of selected domains

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not domains:
        return False, "At least one domain must be selected"

    invalid = [d for d in domains if d not in ALL_DOMAINS]
    if invalid:
        return False, f"Invalid domain(s): {', '.join(invalid)}"

    return True, ""


def validate_target_name(name: str) -> Tuple[bool, str]:
    """
    Validate target company name.

    Args:
        name: Target company name

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Target company name is required"

    if len(name.strip()) < 2:
        return False, "Target company name must be at least 2 characters"

    if len(name) > 100:
        return False, "Target company name must be less than 100 characters"

    return True, ""


def validate_deal_type(deal_type: str) -> Tuple[bool, str]:
    """
    Validate deal type.

    Args:
        deal_type: Deal type string

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_types = ["bolt_on", "carve_out"]

    if deal_type not in valid_types:
        return False, f"Invalid deal type. Must be one of: {', '.join(valid_types)}"

    return True, ""


def validate_analysis_inputs(
    target_name: str,
    deal_type: str,
    domains: List[str],
    has_documents: bool,
    has_notes: bool,
) -> List[str]:
    """
    Validate all inputs required for analysis.

    Args:
        target_name: Target company name
        deal_type: Deal type
        domains: Selected domains
        has_documents: Whether documents are uploaded
        has_notes: Whether notes are provided

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Target name
    valid, msg = validate_target_name(target_name)
    if not valid:
        errors.append(msg)

    # Deal type
    valid, msg = validate_deal_type(deal_type)
    if not valid:
        errors.append(msg)

    # Domains
    valid, msg = validate_domain_selection(domains)
    if not valid:
        errors.append(msg)

    # Documents or notes
    if not has_documents and not has_notes:
        errors.append("Upload documents or provide notes to analyze")

    return errors


def validate_api_key(api_key: Optional[str]) -> Tuple[bool, str]:
    """
    Validate API key format (basic check).

    Args:
        api_key: Anthropic API key

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key:
        return False, "API key is required"

    if not api_key.startswith("sk-ant-"):
        return False, "Invalid API key format (should start with 'sk-ant-')"

    if len(api_key) < 40:
        return False, "API key appears too short"

    return True, ""
