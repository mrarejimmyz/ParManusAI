"""
GPU Manager - Backward Compatibility Wrapper
Enhanced with LLM-driven modular architecture for intelligent GPU management
"""

from app.gpu import GPUManager as ModularGPUManager
from app.gpu import ModernGPUManager
from app.logger import logger

# Import the new modular implementation
GPUManager = ModularGPUManager

# Keep the interface consistent for existing code
__all__ = ["GPUManager"]

logger.info("🔄 GPU Manager now uses LLM-driven modular architecture")
