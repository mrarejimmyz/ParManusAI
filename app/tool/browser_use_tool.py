"""
Browser Use Tool - Enhanced Wrapper with Stealth Mode
Now uses advanced browser tool with NoDriver integration for anti-bot detection bypass
"""

from app.logger import logger
from app.tool.implementations.browser_enhanced import EnhancedUnifiedBrowserTool

# Use the enhanced implementation with stealth capabilities
BrowserUseTool = EnhancedUnifiedBrowserTool

# Keep the interface consistent for existing code
__all__ = ["BrowserUseTool"]

logger.info(
    "🥷 Browser Use Tool now uses ENHANCED stealth mode with anti-bot detection bypass"
)
