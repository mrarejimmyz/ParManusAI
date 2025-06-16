"""
Quality Assurance - Backward Compatibility Wrapper
Enhanced with LLM-driven modular architecture for intelligent quality assurance
"""

from app.logger import logger
from app.quality_assurance import ModernQualityAssurance
from app.quality_assurance import QualityAssurance as ModularQualityAssurance

# Import the new modular implementation
QualityAssurance = ModularQualityAssurance

# Keep the interface consistent for existing code
__all__ = ["QualityAssurance"]

logger.info("🔄 Quality Assurance now uses LLM-driven modular architecture")
