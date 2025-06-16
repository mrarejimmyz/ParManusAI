"""
Memory Module Init
LLM-driven memory and learning system
"""

# Import legacy Memory class for backward compatibility
# We need to import from the app.memory module (not package)
import importlib.util
import os
import sys
from pathlib import Path

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

# Get the path to the legacy memory.py file
legacy_memory_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "memory.py"
)
spec = importlib.util.spec_from_file_location("legacy_memory", legacy_memory_path)
legacy_memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_memory)

# Import the Memory class
Memory = legacy_memory.Memory

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
    # Legacy compatibility
    "Memory",
]
