"""
Browser Use Tool - Backward Compatibility Wrapper
Enhanced with LLM-driven modular architecture for intelligent browser automation
"""

from app.logger import logger
from app.tool.browser import ModernBrowserTool

# Use the new modular implementation
BrowserUseTool = ModernBrowserTool

# Keep the interface consistent for existing code
__all__ = ["BrowserUseTool"]

logger.info("🔄 Browser Use Tool now uses LLM-driven modular architecture")
