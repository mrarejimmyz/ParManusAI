"""
Search Result Formatter - Improved output quality for search results
This module provides clean, readable formatting for search results.
"""

import json
import re
from typing import Any, Dict, List, Union


def format_search_results_cleanly(search_data: Any) -> str:
    """
    Format search results into clean, readable text without raw JSON.

    Args:
        search_data: Search result data (dict, list, or string)

    Returns:
        Cleaned, readable text suitable for reports
    """
    if isinstance(search_data, str):
        if _is_json_like(search_data):
            try:
                parsed = json.loads(search_data)
                return _format_parsed_results(parsed)
            except json.JSONDecodeError:
                return _clean_text(search_data)
        return _clean_text(search_data)

    elif isinstance(search_data, dict):
        return _format_parsed_results(search_data)

    elif isinstance(search_data, list):
        return "\n\n".join(_format_parsed_results(item) for item in search_data)

    return str(search_data)


def _is_json_like(text: str) -> bool:
    """Check if text looks like JSON."""
    text = text.strip()
    return (text.startswith('{') and text.endswith('}')) or \
           (text.startswith('[') and text.endswith(']'))


def _format_parsed_results(data: Union[Dict, List]) -> str:
    """Format parsed search results."""
    if isinstance(data, list):
        return "\n".join(f"{i+1}. {_format_single_result(item)}"
                         for i, item in enumerate(data))
    return _format_single_result(data)


def _format_single_result(result: Dict) -> str:
    """Format a single search result."""
    if not isinstance(result, dict):
        return str(result)

    parts = []

    if 'title' in result:
        parts.append(f"**{result['title']}**")

    if 'url' in result:
        parts.append(f"Source: {result['url']}")

    if 'snippet' in result:
        clean_snippet = _clean_text(result['snippet'])
        if clean_snippet:
            parts.append(f"Summary: {clean_snippet}")

    return "\n   - ".join(parts) if parts else str(result)


def _clean_text(text: str) -> str:
    """Clean text for readability."""
    if not isinstance(text, str):
        return str(text)

    # Remove JSON artifacts
    text = re.sub(r'[{}\[\]"\']', '', text)
    text = re.sub(r'\s+', ' ', text.strip())

    # Remove technical metadata
    text = re.sub(r'position:\s*\d+', '', text)
    text = re.sub(r'source:\s*\w+', '', text)
    text = re.sub(r'content_method:\s*\w+', '', text)

    # Ensure proper sentence ending
    text = text.strip()
    if text and not text.endswith('.'):
        text += '.'

    return text
