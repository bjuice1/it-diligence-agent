"""
Formatting Utilities

Helper functions for formatting values for display.
"""

from datetime import datetime
from typing import Optional, Union


def format_cost(value: Union[int, float], include_symbol: bool = True) -> str:
    """
    Format a cost value for display.

    Args:
        value: Cost value in dollars
        include_symbol: Whether to include $ symbol

    Returns:
        Formatted string (e.g., "$1.5M", "$50K", "$500")
    """
    if value is None or value == 0:
        return "$0" if include_symbol else "0"

    symbol = "$" if include_symbol else ""

    if value >= 1_000_000:
        return f"{symbol}{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{symbol}{value/1_000:.0f}K"
    else:
        return f"{symbol}{value:,.0f}"


def format_cost_range(
    low: int,
    high: int,
    include_symbol: bool = True
) -> str:
    """
    Format a cost range for display.

    Args:
        low: Low estimate
        high: High estimate
        include_symbol: Whether to include $ symbol

    Returns:
        Formatted range string
    """
    if low == 0 and high == 0:
        return "TBD"

    if low == high:
        return format_cost(low, include_symbol)

    return f"{format_cost(low, include_symbol)} - {format_cost(high, include_symbol)}"


def format_percentage(
    value: float,
    decimals: int = 0,
    include_symbol: bool = True
) -> str:
    """
    Format a percentage value.

    Args:
        value: Percentage value (0-100)
        decimals: Number of decimal places
        include_symbol: Whether to include % symbol

    Returns:
        Formatted percentage string
    """
    symbol = "%" if include_symbol else ""
    return f"{value:.{decimals}f}{symbol}"


def format_count(
    value: int,
    singular: str = "item",
    plural: Optional[str] = None
) -> str:
    """
    Format a count with appropriate singular/plural form.

    Args:
        value: Count value
        singular: Singular form of the noun
        plural: Plural form (default: singular + "s")

    Returns:
        Formatted count string
    """
    if plural is None:
        plural = singular + "s"

    noun = singular if value == 1 else plural
    return f"{value:,} {noun}"


def format_timestamp(
    timestamp: Union[str, datetime],
    format_str: str = "%Y-%m-%d %H:%M"
) -> str:
    """
    Format a timestamp for display.

    Args:
        timestamp: ISO format string or datetime object
        format_str: Output format string

    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            return timestamp
    else:
        dt = timestamp

    return dt.strftime(format_str)


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """
    Format file size for display.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_domain_name(domain: str) -> str:
    """
    Format a domain name for display.

    Args:
        domain: Domain name (e.g., "identity_access")

    Returns:
        Formatted name (e.g., "Identity Access")
    """
    return domain.replace("_", " ").title()


def format_phase_name(phase: str) -> str:
    """
    Format a phase name for display.

    Args:
        phase: Phase name (e.g., "Day_1")

    Returns:
        Formatted name (e.g., "Day 1")
    """
    phase_map = {
        "Day_1": "Day 1",
        "Day_100": "Day 100",
        "Post_100": "Post-100",
    }
    return phase_map.get(phase, phase)


def format_severity_label(severity: str) -> str:
    """
    Format severity with icon.

    Args:
        severity: Severity level

    Returns:
        Formatted severity with icon
    """
    icons = {
        "critical": "🔴 Critical",
        "high": "🟠 High",
        "medium": "🟡 Medium",
        "low": "🟢 Low",
    }
    return icons.get(severity.lower(), severity.title())
