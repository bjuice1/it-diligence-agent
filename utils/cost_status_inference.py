"""
Cost Status Inference Utility

Shared logic for determining cost_status and cost_quality_note from cost values.
Used by both deterministic parser and LLM discovery agents to ensure consistency.
"""

from typing import Tuple, Optional


# Internal vendor keywords for exact matching
INTERNAL_VENDOR_KEYWORDS = {
    'internal',
    'in-house',
    'custom-built',
    'proprietary',
    'custom development',
    'internally developed',
}


def infer_cost_status(
    cost_value: Optional[str],
    vendor_name: Optional[str] = None,
    original_value: Optional[str] = None
) -> Tuple[str, str]:
    """
    Infer cost_status and cost_quality_note from a cost value and vendor name.

    Args:
        cost_value: Normalized cost value (numeric string or None)
        vendor_name: Vendor/provider name (used to detect internal apps)
        original_value: Original raw value before normalization (for notes)

    Returns:
        Tuple of (cost_status, cost_quality_note)

    Cost Status Values:
        - 'known': Numeric cost value provided
        - 'unknown': Cost not specified (N/A, TBD, etc.)
        - 'internal_no_cost': $0 cost for internally developed app
        - 'estimated': (reserved for future use - manual estimates)
    """
    if cost_value is None:
        # N/A, TBD, missing — mark as unknown cost
        status = 'unknown'
        note = f'Cost not specified in source'
        if original_value:
            note += f' (original value: "{original_value}")'
        return status, note

    try:
        cost_float = float(cost_value)
    except (ValueError, TypeError):
        # Invalid numeric value — treat as unknown
        status = 'unknown'
        note = f'Invalid cost value: "{cost_value}"'
        return status, note

    # Check for zero or near-zero cost (handle floating point precision)
    if abs(cost_float) < 0.01:
        # Explicit $0 — check if internal/custom
        if vendor_name:
            vendor_normalized = vendor_name.lower().strip()

            # Check for exact match or "internal X" prefix pattern
            if vendor_normalized in INTERNAL_VENDOR_KEYWORDS:
                status = 'internal_no_cost'
                note = 'Internally developed (no licensing cost)'
                return status, note

            # Check for prefix patterns like "internal development"
            if vendor_normalized.startswith('internal '):
                status = 'internal_no_cost'
                note = 'Internally developed (no licensing cost)'
                return status, note

        # $0 but not internal — free/open source
        status = 'known'
        note = 'Free or open source'
        return status, note

    # Numeric cost value
    status = 'known'
    note = ''  # No note needed for clean numeric values
    return status, note


def normalize_numeric(value: str) -> Optional[str]:
    """
    Normalize a numeric field (cost, user count, license count).

    Handles:
    - Dollar signs: "$50,000" → "50000"
    - Commas: "1,234" → "1234"
    - K/M suffixes: "50K" → "50000", "1.5M" → "1500000"
    - Ranges: "10-20" → "15" (midpoint)
    - N/A equivalents: "N/A", "TBD", "Unknown" → None

    Returns:
        Numeric string or None if N/A equivalent
    """
    if not value or not isinstance(value, str):
        return None

    value = value.strip()

    # N/A equivalents
    na_values = {
        'n/a', 'na', 'tbd', 'unknown', 'none', '-',
        'not applicable', 'pending', 'to be determined'
    }
    if value.lower() in na_values:
        return None

    # Remove dollar signs and commas
    value = value.replace('$', '').replace(',', '')

    # Handle K/M suffixes
    multiplier = 1
    if value.lower().endswith('k'):
        multiplier = 1000
        value = value[:-1]
    elif value.lower().endswith('m'):
        multiplier = 1000000
        value = value[:-1]

    # Handle ranges (take midpoint)
    if '-' in value and not value.startswith('-'):
        try:
            parts = value.split('-')
            if len(parts) == 2:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                value = str((low + high) / 2)
        except (ValueError, IndexError):
            pass  # Not a valid range, continue

    # Try to convert to float
    try:
        numeric = float(value) * multiplier
        return str(int(numeric)) if numeric == int(numeric) else str(numeric)
    except (ValueError, TypeError):
        return None
