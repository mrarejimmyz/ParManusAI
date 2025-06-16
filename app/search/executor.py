"""
Search Executor
Executes search strategies and manages results with dynamic web search
"""

from typing import Dict, List

from app.logger import logger

from .dynamic_web_search import DynamicWebSearcher
from .sources import SearchSources


class SearchExecutor:
    """
    Executes search strategies determined by the analyzer
    """

    def __init__(self, llm=None):
        self.sources = SearchSources()
        self.dynamic_searcher = DynamicWebSearcher(llm)

    async def execute_strategy(self, query: str, strategy: Dict) -> List[Dict]:
        """
        Execute the search strategy determined by the LLM using dynamic web search
        """
        approach = strategy.get("approach", "dynamic_search")
        search_queries = strategy.get("search_queries", [query])

        logger.info(
            f"🚀 Executing {approach} strategy with {len(search_queries)} queries"
        )

        all_results = []

        # Use dynamic web search as the primary method
        if approach in [
            "dynamic_search",
            "combined_search",
            "web_search",
            "news_search",
        ]:
            logger.info("🔍 Using dynamic web search and scraping")

            for search_query in search_queries[
                :3
            ]:  # Limit to 3 queries to avoid overload
                try:
                    dynamic_results = await self.dynamic_searcher.search_and_scrape(
                        search_query, max_results=5
                    )
                    all_results.extend(dynamic_results)
                    logger.info(
                        f"Found {len(dynamic_results)} results for query: {search_query}"
                    )
                except Exception as e:
                    logger.error(f"Dynamic search failed for '{search_query}': {e}")
                    # Fallback to old method for this query
                    fallback_results = await self._fallback_search(search_query)
                    all_results.extend(fallback_results)

        elif approach == "direct_website_access":
            # Handle direct website access
            target_url = strategy.get("target_url")
            if target_url:
                try:
                    content = await self.dynamic_searcher._scrape_single_link(
                        target_url
                    )
                    if content:
                        all_results.append(
                            {
                                "title": "Direct Website Access",
                                "url": target_url,
                                "content": content,
                                "source": "direct_access",
                            }
                        )
                except Exception as e:
                    logger.error(f"Direct access failed for {target_url}: {e}")

            # Also do some dynamic searches for context
            for search_query in search_queries[:2]:
                try:
                    dynamic_results = await self.dynamic_searcher.search_and_scrape(
                        search_query, max_results=3
                    )
                    all_results.extend(dynamic_results)
                except Exception as e:
                    logger.warning(f"Context search failed for '{search_query}': {e}")

        else:
            # For any other approach, use dynamic search
            logger.info("Using dynamic search as fallback")
            try:
                dynamic_results = await self.dynamic_searcher.search_and_scrape(
                    query, max_results=8
                )
                all_results.extend(dynamic_results)
            except Exception as e:
                logger.error(f"Dynamic search failed: {e}")
                # Use old fallback methods
                fallback_results = await self._fallback_search(query)
                all_results.extend(fallback_results)

        logger.info(f"Total results collected: {len(all_results)}")
        return all_results

    async def _fallback_search(self, query: str) -> List[Dict]:
        """
        Fallback search using old methods when dynamic search fails
        """
        logger.info(f"Using fallback search for: {query}")

        fallback_results = []

        # Try web sources
        try:
            web_results = await self._search_web_sources(query)
            fallback_results.extend(web_results)
        except Exception as e:
            logger.warning(f"Web search fallback failed: {e}")

        # Try news sources
        try:
            news_results = await self._search_news_sources(query)
            fallback_results.extend(news_results)
        except Exception as e:
            logger.warning(f"News search fallback failed: {e}")

        return fallback_results

    async def _search_web_sources(self, query: str) -> List[Dict]:
        """Search general web sources (fallback method)"""
        results = []

        # Try DuckDuckGo
        try:
            ddg_results = self.sources.search_duckduckgo_instant(query)
            results.extend(ddg_results)
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")

        return results

    async def _search_news_sources(self, query: str) -> List[Dict]:
        """Search news sources (fallback method)"""
        results = []

        # Try Bing News
        try:
            news_results = self.sources.search_bing_news(query)
            results.extend(news_results)
        except Exception as e:
            logger.warning(f"News search failed: {e}")

        return results
