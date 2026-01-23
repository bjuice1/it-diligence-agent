"""
Input Sanitization for LLM-Generated Content

Sanitizes inputs from LLM before storing to prevent:
- JSON injection
- XSS (if output is HTML)
- Data corruption
- Breaking serialization
"""

import json
import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Maximum lengths to prevent DoS
MAX_STRING_LENGTH = 10000
MAX_DICT_DEPTH = 10
MAX_LIST_LENGTH = 1000


def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """
    Sanitize a string value.
    
    - Truncates if too long
    - Removes null bytes
    - Normalizes whitespace
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Remove null bytes (can break JSON)
    value = value.replace('\x00', '')
    
    # Truncate if too long
    if len(value) > max_length:
        logger.warning(f"String truncated from {len(value)} to {max_length} characters")
        value = value[:max_length]
    
    # Normalize excessive whitespace (but preserve intentional formatting)
    # Only collapse more than 2 consecutive newlines
    value = re.sub(r'\n{3,}', '\n\n', value)
    
    return value.strip()


def sanitize_dict(data: Dict[str, Any], max_depth: int = MAX_DICT_DEPTH, depth: int = 0) -> Dict[str, Any]:
    """
    Recursively sanitize dictionary values.
    
    Args:
        data: Dictionary to sanitize
        max_depth: Maximum nesting depth
        depth: Current depth (for recursion)
    
    Returns:
        Sanitized dictionary
    """
    if depth > max_depth:
        logger.warning(f"Dictionary depth {depth} exceeds maximum {max_depth}, truncating")
        return {}
    
    sanitized = {}
    for key, value in data.items():
        # Sanitize key
        key = sanitize_string(str(key), max_length=100)
        
        # Sanitize value based on type
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, max_depth, depth + 1)
        elif isinstance(value, list):
            sanitized[key] = sanitize_list(value, max_depth, depth + 1)
        elif isinstance(value, (int, float, bool)) or value is None:
            # Safe types, keep as-is
            sanitized[key] = value
        else:
            # Unknown type, convert to string and sanitize
            sanitized[key] = sanitize_string(str(value))
    
    return sanitized


def sanitize_list(data: List[Any], max_depth: int = MAX_DICT_DEPTH, depth: int = 0) -> List[Any]:
    """
    Recursively sanitize list values.
    
    Args:
        data: List to sanitize
        max_depth: Maximum nesting depth
        depth: Current depth (for recursion)
    
    Returns:
        Sanitized list
    """
    if depth > max_depth:
        logger.warning(f"List depth {depth} exceeds maximum {max_depth}, truncating")
        return []
    
    if len(data) > MAX_LIST_LENGTH:
        logger.warning(f"List length {len(data)} exceeds maximum {MAX_LIST_LENGTH}, truncating")
        data = data[:MAX_LIST_LENGTH]
    
    sanitized = []
    for item in data:
        if isinstance(item, str):
            sanitized.append(sanitize_string(item))
        elif isinstance(item, dict):
            sanitized.append(sanitize_dict(item, max_depth, depth + 1))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item, max_depth, depth + 1))
        elif isinstance(item, (int, float, bool)) or item is None:
            sanitized.append(item)
        else:
            sanitized.append(sanitize_string(str(item)))
    
    return sanitized


def sanitize_input(data: Any) -> Any:
    """
    Sanitize input data from LLM before storing.
    
    Handles strings, dicts, lists, and nested structures.
    
    Args:
        data: Data to sanitize (any type)
    
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return sanitize_string(data)
    elif isinstance(data, dict):
        return sanitize_dict(data)
    elif isinstance(data, list):
        return sanitize_list(data)
    elif isinstance(data, (int, float, bool)) or data is None:
        return data
    else:
        # Unknown type, convert to string
        return sanitize_string(str(data))


def validate_json_safe(data: Any) -> bool:
    """
    Validate that data can be safely serialized to JSON.
    
    Args:
        data: Data to validate
    
    Returns:
        True if JSON-safe, False otherwise
    """
    try:
        json.dumps(data, ensure_ascii=False)
        return True
    except (TypeError, ValueError) as e:
        logger.warning(f"Data is not JSON-safe: {e}")
        return False
