"""
Backward Compatibility Wrapper for LLM-Driven Search
This file maintains compatibility with existing code while using the new modular system
"""

from app.search import LLMDrivenSearch


# Maintain backward compatibility
class OptimizedBulletproofSearch(LLMDrivenSearch):
    """
    Backward compatibility wrapper that delegates to the new modular search system
    """

    def __init__(self, llm=None):
        super().__init__(llm)

    async def perform_google_search(self, query: str) -> dict:
        """
        Legacy method name for backward compatibility
        """
        return await self.search(query)
