"""
Enhanced Memory and Learning System for ParManusAI - Backward Compatibility Wrapper
Enhanced with LLM-driven modular architecture for intelligent learning and optimization
"""

from app.logger import logger
from app.memory import EnhancedMemorySystem as ModularEnhancedMemorySystem
from app.memory import ModernEnhancedMemorySystem

# Import the new modular implementation
EnhancedMemorySystem = ModularEnhancedMemorySystem

# Keep the interface consistent for existing code
__all__ = ["EnhancedMemorySystem"]

logger.info("🔄 Enhanced Memory System now uses LLM-driven modular architecture")
