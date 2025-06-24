"""
Web Search Tool - Enhanced Wrapper with NoDriver Vision Search
Now uses the fixed FastNoDriverVisionSearchTool for reliable search with content extraction
"""

from app.logger import logger
from app.tool.implementations.nodriver_vision_search_fast import \
    FastNoDriverVisionSearchTool

# Use the fixed NoDriver implementation that actually works
WebSearch = FastNoDriverVisionSearchTool

# Keep the interface consistent for existing code
__all__ = ["WebSearch"]

logger.info(
    "🧠 Web Search Tool now uses FIXED NODRIVER SEARCH with working blue link detection"
)
