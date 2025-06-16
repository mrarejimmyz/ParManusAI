"""
Visual Google Search Implementation - Backward Compatibility Wrapper
Enhanced with LLM-driven modular architecture for intelligent reasoning
"""

from app.logger import logger
from app.agent.visual_search import ModernVisualGoogleSearch, VisualGoogleSearch as ModularVisualGoogleSearch

# Import the new modular implementation
VisualGoogleSearch = ModularVisualGoogleSearch

# Keep the interface consistent for existing code
__all__ = ["VisualGoogleSearch"]

logger.info("� Visual Google Search now uses LLM-driven modular architecture")
