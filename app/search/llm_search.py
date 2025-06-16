"""
Modern LLM-Driven Search - Refactored and Optimized

A clean, modular search implementation using separated search engines.
"""

from typing import Dict, List

from app.logger import logger
from app.search.engines import (
    ContentExtractor,
    KnowledgeSearchEngine,
    NewsSearchEngine,
    WebSearchEngine,
)
from app.search.strategy_analyzer import StrategyAnalyzer


class ModernLLMSearch:
    """Modern, modular LLM-driven search implementation."""

    def __init__(self, llm=None):
        self.llm = llm

        # Initialize components
        self.strategy_analyzer = StrategyAnalyzer(llm)
        self.web_engine = WebSearchEngine()
        self.news_engine = NewsSearchEngine()
        self.knowledge_engine = KnowledgeSearchEngine()
        self.content_extractor = ContentExtractor()

    async def perform_google_search(self, query: str) -> Dict:
        """
        Perform comprehensive search using LLM-driven strategy.

        Args:
            query: Search query

        Returns:
            Dict: Search results with success status
        """
        try:
            logger.info(f"🔍 Starting LLM-driven search: {query}")

            # Analyze query with LLM to determine strategy
            strategy = await self.strategy_analyzer.analyze_query(query)

            # Execute strategy
            results = await self._execute_strategy(query, strategy)

            # Post-process results
            final_results = self._process_and_rank_results(results, query)

            if final_results:
                logger.info(f"✅ Search completed: {len(final_results)} results")
                return {
                    "success": True,
                    "results": final_results,
                    "strategy": strategy,
                    "total_results": len(final_results),
                }
            else:
                logger.warning("⚠️ No results found")
                return {"success": False, "results": [], "error": "No results found"}

        except Exception as e:
            logger.error(f"❌ LLM-driven search failed: {e}")
            return {"success": False, "results": [], "error": str(e)}

    async def _execute_strategy(self, query: str, strategy: Dict) -> List[Dict]:
        """Execute search strategy across multiple engines."""
        all_results = []
        approach = strategy.get("approach", "web_search")
        queries = strategy.get("queries", [query])

        try:
            # Execute searches based on strategy
            if approach == "news_search":
                all_results.extend(await self._search_news_sources(queries))
            elif approach == "knowledge_base":
                all_results.extend(await self._search_knowledge_sources(queries))
            elif approach == "mixed":
                # Search all sources
                all_results.extend(await self._search_web_sources(queries))
                all_results.extend(await self._search_news_sources(queries))
                all_results.extend(await self._search_knowledge_sources(queries))
            else:  # web_search
                all_results.extend(await self._search_web_sources(queries))

            return all_results

        except Exception as e:
            logger.error(f"❌ Strategy execution failed: {e}")
            return []

    async def _search_web_sources(self, queries: List[str]) -> List[Dict]:
        """Search web sources."""
        results = []

        for query in queries[:2]:  # Limit to 2 queries to avoid rate limits
            try:
                web_results = await self.web_engine.search_duckduckgo_web(query)
                results.extend(web_results)
            except Exception as e:
                logger.warning(f"Web search failed for query '{query}': {e}")

        return results

    async def _search_news_sources(self, queries: List[str]) -> List[Dict]:
        """Search news sources."""
        results = []

        for query in queries[:2]:  # Limit queries
            try:
                news_results = await self.news_engine.search_bing_news(query)
                results.extend(news_results)
            except Exception as e:
                logger.warning(f"News search failed for query '{query}': {e}")

        return results

    async def _search_knowledge_sources(self, queries: List[str]) -> List[Dict]:
        """Search knowledge sources."""
        results = []

        for query in queries[:2]:  # Limit queries
            try:
                # Wikipedia
                wiki_results = self.knowledge_engine.search_wikipedia_api(query)
                results.extend(wiki_results)

                # DuckDuckGo instant answers
                instant_results = self.knowledge_engine.search_duckduckgo_instant(query)
                results.extend(instant_results)

            except Exception as e:
                logger.warning(f"Knowledge search failed for query '{query}': {e}")

        return results

    def _process_and_rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Process and rank search results."""
        try:
            # Remove duplicates
            unique_results = self._deduplicate_results(results)

            # Calculate relevance scores
            scored_results = []
            for result in unique_results:
                score = self._calculate_relevance_score(result, query)
                result["relevance_score"] = score
                scored_results.append(result)

            # Sort by relevance
            scored_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

            # Return top results
            return scored_results[:10]

        except Exception as e:
            logger.error(f"❌ Error processing results: {e}")
            return results[:10]  # Return first 10 as fallback

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on URL and title."""
        seen_urls = set()
        seen_titles = set()
        unique_results = []

        for result in results:
            url = result.get("url", "")
            title = result.get("title", "").lower()

            # Skip if URL or title already seen
            if url in seen_urls or title in seen_titles:
                continue

            # Skip if no meaningful content
            if not title.strip() or not url.strip():
                continue

            seen_urls.add(url)
            seen_titles.add(title)
            unique_results.append(result)

        return unique_results

    def _calculate_relevance_score(self, result: Dict, query: str) -> int:
        """Calculate relevance score for a result."""
        score = 0
        query_words = query.lower().split()

        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        source = result.get("source", "").lower()

        # Title relevance (higher weight)
        for word in query_words:
            if word in title:
                score += 3

        # Snippet relevance
        for word in query_words:
            if word in snippet:
                score += 1

        # Source preference
        if "wikipedia" in source:
            score += 2  # Wikipedia often has good factual content
        elif "news" in source:
            score += 1  # News is good for recent events

        # Penalize very short snippets
        if len(snippet) < 50:
            score -= 1

        return max(0, score)


# Backward compatibility alias
OptimizedBulletproofSearch = ModernLLMSearch
