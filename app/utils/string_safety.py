"""
Global utilities for safe string operations.
Prevents dict.lower() errors by ensuring safe type conversion.
"""

import logging
from typing import Any, Union

logger = logging.getLogger(__name__)


def safe_lower(value: Any) -> str:
    """
    Safely convert any value to lowercase string.

    This function prevents 'dict' object has no attribute 'lower' errors
    by ensuring the value is converted to a string before calling .lower().

    Args:
        value: Any value that might need to be lowercased

    Returns:
        str: Lowercase string representation of the value
    """
    if value is None:
        return ""

    if isinstance(value, str):
        return value.lower()

    # Handle common types safely
    if isinstance(value, (int, float, bool)):
        return str(value).lower()

    if isinstance(value, (dict, list, tuple, set)):
        # Log the conversion for debugging
        logger.debug(
            f"🔧 safe_lower: Converting {type(value).__name__} to string: {value}"
        )
        return str(value).lower()

    # Handle any other type
    try:
        return str(value).lower()
    except Exception as e:
        logger.warning(
            f"⚠️ safe_lower: Error converting {type(value).__name__} to string: {e}"
        )
        return str(type(value).__name__).lower()


def safe_contains_lower(text: Any, search_term: str) -> bool:
    """
    Safely check if search_term is contained in the lowercase version of text.

    Args:
        text: Text to search in (any type)
        search_term: Term to search for (will be lowercased)

    Returns:
        bool: True if search_term is found in lowercase text
    """
    safe_text = safe_lower(text)
    safe_search = safe_lower(search_term)
    return safe_search in safe_text


def ensure_string_for_lower(value: Any) -> str:
    """
    Ensure a value is safe for .lower() operations.

    Args:
        value: Any value that might be used with .lower()

    Returns:
        str: Safe string representation
    """
    if isinstance(value, str):
        return value

    if value is None:
        return ""

    # Convert to string with logging for debugging
    if isinstance(value, dict):
        logger.warning(f"🔧 Converting dict to string for .lower() safety: {value}")
        return str(value)

    return str(value)
