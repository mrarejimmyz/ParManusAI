"""
Search Executor
Executes search strategies and manages results
"""

from typing import Dict, List

from app.logger import logger

from .sources import SearchSources


class SearchExecutor:
    """
    Executes search strategies determined by the analyzer
    """

    def __init__(self):
        self.sources = SearchSources()

    async def execute_strategy(self, query: str, strategy: Dict) -> List[Dict]:
        """
        Execute the search strategy determined by the LLM
        """
        approach = strategy.get("approach", "combined_search")
        search_queries = strategy.get("search_queries", [query])

        logger.info(
            f"🚀 Executing {approach} strategy with {len(search_queries)} queries"
        )

        all_results = []

        if approach == "direct_website_access":
            # Handle direct website access
            target_url = strategy.get("target_url")
            if target_url:
                website_result = await self.sources.access_website_directly(target_url)
                if website_result:
                    all_results.append(website_result)

            # Also do some web searches for context
            for search_query in search_queries[:2]:
                web_results = await self._search_web_sources(search_query)
                all_results.extend(web_results)

        elif approach == "news_search":
            # Focus on news sources
            for search_query in search_queries:
                news_results = await self._search_news_sources(search_query)
                all_results.extend(news_results)

        elif approach == "knowledge_search":
            # Focus on factual/reference sources
            for search_query in search_queries:
                knowledge_results = await self._search_knowledge_sources(search_query)
                all_results.extend(knowledge_results)

        elif approach == "web_search":
            # Focus on general web search
            for search_query in search_queries:
                web_results = await self._search_web_sources(search_query)
                all_results.extend(web_results)

        else:  # combined_search or fallback
            # Use all available sources
            for search_query in search_queries:
                web_results = await self._search_web_sources(search_query)
                news_results = await self._search_news_sources(search_query)
                knowledge_results = await self._search_knowledge_sources(search_query)

                all_results.extend(web_results)
                all_results.extend(news_results)
                all_results.extend(knowledge_results)

        # Remove duplicates and prioritize based on strategy
        unique_results = self._deduplicate_and_prioritize(all_results, strategy)

        # Enhance results with content if needed
        if strategy.get("content_focus") == "detailed":
            unique_results = await self._enrich_results_with_content(unique_results)

        return unique_results[:10]  # Return top 10 results

    async def _search_web_sources(self, query: str) -> List[Dict]:
        """Search general web sources dynamically"""
        results = []

        # Try DuckDuckGo
        ddg_results = await self.sources.search_duckduckgo_web(query)
        results.extend(ddg_results)

        return results

    async def _search_news_sources(self, query: str) -> List[Dict]:
        """Search news sources dynamically"""
        results = []

        # Try Bing News
        bing_results = await self.sources.search_bing_news(query)
        results.extend(bing_results)

        return results

    async def _search_knowledge_sources(self, query: str) -> List[Dict]:
        """Search knowledge/reference sources dynamically"""
        results = []

        # Try Wikipedia
        wiki_results = self.sources.search_wikipedia_api(query)
        results.extend(wiki_results)

        # Try DuckDuckGo instant answers
        instant_results = self.sources.search_duckduckgo_instant(query)
        results.extend(instant_results)

        return results

    def _deduplicate_and_prioritize(
        self, results: List[Dict], strategy: Dict
    ) -> List[Dict]:
        """Remove duplicates and prioritize results based on strategy"""
        # Remove duplicates by URL
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)

                # Adjust relevance based on strategy priorities
                priority_sources = strategy.get("priority_sources", [])
                source = result.get("source", "").lower()

                for priority in priority_sources:
                    if priority.lower() in source:
                        result["relevance"] = result.get("relevance", 0) + 3
                        break

                unique_results.append(result)

        # Sort by relevance
        unique_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)

        return unique_results

    async def _enrich_results_with_content(self, results: List[Dict]) -> List[Dict]:
        """Enrich search results by extracting more content from web pages"""
        enriched_results = []

        for result in results[:8]:
            try:
                url = result.get("url", "")
                if not url or "example.com" in url:
                    enriched_results.append(result)
                    continue

                page_content = await self._extract_page_content(url)

                if page_content:
                    result["full_content"] = page_content[:1000]
                    result["enhanced"] = True

                    query = result.get("query", "")
                    if query:
                        enhanced_relevance = self.sources._calculate_relevance(
                            query, result.get("title", ""), page_content
                        )
                        result["relevance"] = max(
                            result.get("relevance", 0), enhanced_relevance
                        )

                enriched_results.append(result)

            except Exception as e:
                logger.warning(
                    f"Failed to enrich result {result.get('url', '')}: {str(e)}"
                )
                enriched_results.append(result)

        return enriched_results

    async def _extract_page_content(self, url: str) -> str:
        """Extract main content from a web page"""
        try:
            response = self.sources.session.get(url, timeout=8)
            response.raise_for_status()

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, "html.parser")

            for script in soup(["script", "style"]):
                script.decompose()

            content_selectors = [
                "article",
                ".content",
                ".post-content",
                ".entry-content",
                ".article-body",
                "main",
                "#content",
            ]

            content_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content_text = elements[0].get_text(strip=True)
                    break

            if not content_text:
                content_text = soup.get_text(strip=True)

            lines = [line.strip() for line in content_text.split("\n") if line.strip()]
            content_text = " ".join(lines[:10])

            return content_text[:1500]

        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {str(e)}")
            return ""
