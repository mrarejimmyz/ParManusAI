"""
Main LLM-Driven Search Interface
Coordinates strategy analysis and execution
"""

from typing import Dict

from app.logger import logger

from .executor import SearchExecutor
from .strategy_analyzer import SearchStrategyAnalyzer


class LLMDrivenSearch:
    """
    Main interface for LLM-driven dynamic search
    """

    def __init__(self, llm=None):
        self.analyzer = SearchStrategyAnalyzer(llm)
        self.executor = SearchExecutor(llm)  # Pass LLM to executor

    async def search(self, query: str) -> Dict:
        """
        Main search method that coordinates analysis and execution
        """
        logger.info(f"🔍 LLM-driven dynamic search for: {query}")

        # Analyze query and determine strategy
        strategy = await self.analyzer.analyze_query(query)
        logger.info(
            f"🧠 LLM determined strategy: {strategy.get('approach', 'unknown')}"
        )

        # Execute the strategy
        results = await self.executor.execute_strategy(query, strategy)

        if results:
            logger.info(
                f"🎯 Strategy executed successfully: {len(results)} results found"
            )
            return {
                "success": True,
                "query": query,
                "results": results,
                "method": "llm_driven_dynamic_search",
                "strategy": strategy,
                "real_search": True,
            }
        else:
            logger.warning(f"⚠️ No results found with LLM strategy, trying fallback")
            # Try a simple fallback approach
            fallback_results = await self._simple_fallback_search(query)
            return {
                "success": len(fallback_results) > 0,
                "query": query,
                "results": fallback_results,
                "method": "fallback_search",
                "real_search": True,
            }

    async def _simple_fallback_search(self, query: str) -> list:
        """Simple fallback when all else fails"""
        results = []

        # Try basic searches
        web_results = await self.executor._search_web_sources(query)
        news_results = await self.executor._search_news_sources(query)

        results.extend(web_results)
        results.extend(news_results)

        return results[:5]


# Backward compatibility wrapper
class OptimizedBulletproofSearch(LLMDrivenSearch):
    """
    Backward compatibility wrapper for the old interface
    """

    async def perform_google_search(self, query: str) -> Dict:
        """Compatibility method for existing code"""
        return await self.search(query)
