"""
Browser Use Tool - Backward Compatibility Wrapper
Enhanced with unified browser tool architecture
"""

from app.logger import logger
from app.tool.implementations.browser import UnifiedBrowserTool

# Use the unified implementation
BrowserUseTool = UnifiedBrowserTool

# Keep the interface consistent for existing code
__all__ = ["BrowserUseTool"]

logger.info("🔄 Browser Use Tool now uses unified browser architecture")
