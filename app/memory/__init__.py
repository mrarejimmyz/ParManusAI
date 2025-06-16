"""
Memory Module Init
LLM-driven memory and learning system
"""

from .analyzer import LLMExperienceAnalyzer
from .modern_memory import EnhancedMemorySystem, ModernEnhancedMemorySystem
from .optimizer import LLMStrategyOptimizer
from .pattern_recognizer import LLMPatternRecognizer
from .types import (
    LearningDomain,
    LearningExperience,
    LearningMetrics,
    MemoryQuery,
    OptimizationInsight,
    StrategyPattern,
    TaskType,
)

__all__ = [
    # Types
    "LearningExperience",
    "StrategyPattern",
    "OptimizationInsight",
    "MemoryQuery",
    "LearningMetrics",
    "TaskType",
    "LearningDomain",
    # Components
    "LLMExperienceAnalyzer",
    "LLMPatternRecognizer",
    "LLMStrategyOptimizer",
    # Main interfaces
    "ModernEnhancedMemorySystem",
    "EnhancedMemorySystem",  # Backward compatibility
]
