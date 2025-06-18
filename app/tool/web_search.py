"""
Web Search Tool - Backward Compatibility Wrapper
Enhanced with unified search tool architecture
"""

from app.logger import logger
from app.tool.implementations.search import UnifiedSearchTool

# Use the unified implementation
WebSearch = UnifiedSearchTool

# Keep the interface consistent for existing code
__all__ = ["WebSearch"]

logger.info("🔄 Web Search Tool now uses unified search architecture")
