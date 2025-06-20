"""
Web Search Tool - Enhanced Wrapper with Intelligent Scraping
Now uses advanced search tool with IntelligentScraper for multi-strategy content fetching
"""

from app.logger import logger
from app.tool.implementations.search_enhanced import EnhancedUnifiedSearchTool

# Use the enhanced implementation with intelligent scraping
WebSearch = EnhancedUnifiedSearchTool

# Keep the interface consistent for existing code
__all__ = ["WebSearch"]

logger.info(
    "🧠 Web Search Tool now uses INTELLIGENT SCRAPING with multi-strategy fallback"
)
