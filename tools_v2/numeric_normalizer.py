"""
Numeric Normalizer

Converts formatted numbers to clean numeric values.
Handles currency symbols, commas, N/A values, etc.
"""

import re
from typing import Optional, Union, Any

# Null-like values that should become None
NULL_INDICATORS = {
    'n/a', 'na', 'n.a.', 'n.a',
    'tbd', 'to be determined',
    'unknown', 'unk',
    'null', 'none', 'nil',
    '-', '--', '---',
    '', ' ',
}

# Currency symbols to strip
CURRENCY_SYMBOLS = re.compile(r'[$€£¥₹₽₩₴฿]')

# Thousand separators (comma in US, period in EU)
THOUSAND_SEP = re.compile(r'(?<=\d)[,.](?=\d{3}(?:[,.\s]|$))')

# Approximation prefixes
APPROX_PREFIX = re.compile(r'^[~≈≃∼]')

# Trailing indicators
TRAILING_INDICATORS = re.compile(r'[+*]+$')

# Parenthetical suffixes like "(estimated)"
PAREN_SUFFIX = re.compile(r'\s*\([^)]*\)\s*$')


def normalize_numeric(value: Any) -> Optional[Union[int, float]]:
    """
    Convert a formatted value to a clean numeric.

    Examples:
        "$1,234.56" -> 1234.56
        "1,407 users" -> 1407
        "~500" -> 500
        "N/A" -> None
        "TBD" -> None

    Args:
        value: Raw value (string, int, float, or None)

    Returns:
        int, float, or None if not parseable
    """
    # Already numeric
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value

    # None
    if value is None:
        return None

    # Convert to string and clean
    text = str(value).strip().lower()

    # Check null indicators
    if text in NULL_INDICATORS:
        return None

    # Remove parenthetical suffixes
    text = PAREN_SUFFIX.sub('', text)

    # Extract just the numeric part (first number found)
    # This handles "1,407 users" -> "1,407"
    match = re.search(r'[\d,.$€£¥₹₽₩₴฿~≈+-]+[\d.]*', text)
    if not match:
        return None

    numeric_str = match.group()

    # Remove currency symbols
    numeric_str = CURRENCY_SYMBOLS.sub('', numeric_str)

    # Remove approximation prefixes
    numeric_str = APPROX_PREFIX.sub('', numeric_str)

    # Remove trailing indicators
    numeric_str = TRAILING_INDICATORS.sub('', numeric_str)

    # Handle thousand separators
    # Detect format: 1,234.56 (US) vs 1.234,56 (EU)
    if ',' in numeric_str and '.' in numeric_str:
        # Both present - comma before period = US format
        if numeric_str.rfind(',') < numeric_str.rfind('.'):
            numeric_str = numeric_str.replace(',', '')
        else:
            # EU format: swap
            numeric_str = numeric_str.replace('.', '').replace(',', '.')
    elif ',' in numeric_str:
        # Only commas - assume thousand separator
        numeric_str = numeric_str.replace(',', '')

    # Clean up any remaining non-numeric chars except decimal point
    numeric_str = re.sub(r'[^\d.-]', '', numeric_str)

    # Handle multiple decimal points (keep only first)
    if numeric_str.count('.') > 1:
        parts = numeric_str.split('.')
        numeric_str = parts[0] + '.' + ''.join(parts[1:])

    # Try to parse
    try:
        if '.' in numeric_str:
            return float(numeric_str)
        else:
            return int(numeric_str)
    except ValueError:
        return None


def normalize_cost(value: Any) -> Optional[float]:
    """
    Normalize a cost/currency value to float.

    Args:
        value: Raw cost value (e.g., "$1,234.56", "N/A")

    Returns:
        Float value or None
    """
    result = normalize_numeric(value)
    if result is not None:
        return float(result)
    return None


def normalize_count(value: Any) -> Optional[int]:
    """
    Normalize a count/integer value.

    Args:
        value: Raw count value (e.g., "1,407 users", "~500")

    Returns:
        Integer value or None
    """
    result = normalize_numeric(value)
    if result is not None:
        return int(result)
    return None


def is_null_value(value: Any) -> bool:
    """
    Check if a value represents null/unknown.

    Args:
        value: Any value to check

    Returns:
        True if value represents null/unknown
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in NULL_INDICATORS
    return False


def normalize_percentage(value: Any) -> Optional[float]:
    """
    Normalize a percentage value to decimal (0-1 range).

    Args:
        value: Raw percentage value (e.g., "85%", "0.85")

    Returns:
        Float in 0-1 range or None
    """
    if value is None:
        return None

    text = str(value).strip()

    # Check for null indicators
    if text.lower() in NULL_INDICATORS:
        return None

    # Check if already decimal (0-1 range)
    try:
        val = float(text)
        if 0 <= val <= 1:
            return val
        elif 1 < val <= 100:
            return val / 100.0
    except ValueError:
        pass

    # Handle percentage symbol
    if '%' in text:
        text = text.replace('%', '').strip()
        try:
            return float(text) / 100.0
        except ValueError:
            pass

    return None
