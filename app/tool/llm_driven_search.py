"""
LLM Driven Search - Backward Compatibility Wrapper
Enhanced with LLM-driven modular architecture for intelligent search operations
"""

from app.logger import logger
from app.search import LLMDrivenSearch as ModularLLMDrivenSearch
from app.search import ModernLLMDrivenSearch

# Import the new modular implementation
LLMDrivenSearch = ModularLLMDrivenSearch

# Keep the interface consistent for existing code
__all__ = ["LLMDrivenSearch"]

logger.info("🔄 LLM Driven Search now uses LLM-driven modular architecture")
