"""
Unified LLM Module - Single Export Point
Replaces all existing LLM implementations with a unified interface.
"""

from .core import (
    BaseLLMProvider,
    MessageFormatter,
    OllamaProvider,
    TokenCounter,
    UnifiedLLM,
    create_llm,
)

# Single export - this is the only LLM interface the rest of the codebase should use
LLM = UnifiedLLM

# Backward compatibility exports
create_llm_with_tools = create_llm

__all__ = [
    "LLM",
    "UnifiedLLM",
    "create_llm",
    "create_llm_with_tools",
    "TokenCounter",
    "MessageFormatter",
    "BaseLLMProvider",
    "OllamaProvider",
]
