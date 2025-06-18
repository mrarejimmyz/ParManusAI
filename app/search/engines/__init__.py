"""
Search engine modules for web search and content aggregation.
"""

from .content_aggregator import ContentAggregator
from .search_adapters import (
    BingAdapter,
    DuckDuckGoAdapter,
    GoogleAdapter,
    MultiEngineSearcher,
    SearchEngineAdapter,
)

# Alias for backward compatibility
SearchAdapters = MultiEngineSearcher

__all__ = [
    "SearchEngineAdapter",
    "DuckDuckGoAdapter",
    "BingAdapter",
    "GoogleAdapter",
    "MultiEngineSearcher",
    "SearchAdapters",  # Alias
    "ContentAggregator",
]
