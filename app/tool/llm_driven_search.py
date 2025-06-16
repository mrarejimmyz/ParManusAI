"""
Fully LLM-Driven Dynamic Search Implementation
Uses LLM reasoning to determine optimal search strategies for any query type
"""

import json
import re
from typing import Dict, List, Optional
from urllib.parse import quote

import requests

from app.logger import logger


class OptimizedBulletproofSearch:
    """
    LLM-driven dynamic search that adapts to any query type intelligently
    """

    def __init__(self, llm=None):
        self.session = requests.Session()
        self.llm = llm  # For dynamic reasoning
        # Set realistic headers to avoid blocking
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
            }
        )

    async def perform_google_search(self, query: str) -> Dict:
        """
        LLM-driven dynamic search that adapts to any query type
        """
        logger.info(f"🔍 LLM-driven dynamic search for: {query}")

        # Use LLM to analyze query and determine optimal search strategy
        search_strategy = await self._analyze_query_with_llm(query)
        logger.info(
            f"🧠 LLM determined strategy: {search_strategy.get('approach', 'unknown')}"
        )

        # Execute the strategy dynamically
        results = await self._execute_dynamic_strategy(query, search_strategy)

        if results:
            logger.info(
                f"🎯 Strategy executed successfully: {len(results)} results found"
            )
            return {
                "success": True,
                "query": query,
                "results": results,
                "method": "llm_driven_dynamic_search",
                "strategy": search_strategy,
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

    async def _analyze_query_with_llm(self, query: str) -> Dict:
        """
        Use LLM to analyze the query and determine the optimal search strategy
        """
        try:
            if not self.llm:
                return self._get_default_strategy(query)

            prompt = f"""
            Analyze this search query and determine the optimal search strategy:

            Query: "{query}"

            Consider these factors:
            1. Is this a website review/analysis request? (contains domain like .com, .xyz + words like review, analyze)
            2. Is this a news/current events search? (contains news, latest, breaking, today)
            3. Is this a factual information lookup? (contains what is, how to, facts about)
            4. Is this location-specific or global?
            5. What type of sources would be most valuable?

            Available search methods:
            - direct_website_access: For reviewing specific websites (extract URL and access directly)
            - news_search: For current news and events (use news sources)
            - web_search: For general web information (use web search engines)
            - knowledge_search: For factual/reference information (use Wikipedia, encyclopedias)
            - combined_search: For comprehensive research (use all sources)

            Respond with JSON only:
            {{
                "approach": "direct_website_access|news_search|web_search|knowledge_search|combined_search",
                "reasoning": "why this approach is best",
                "search_queries": ["specific query 1", "specific query 2", "specific query 3"],
                "target_url": "https://example.com (only if direct website access detected)",
                "priority_sources": ["web", "news", "knowledge"],
                "content_focus": "summary|detailed"
            }}
            """

            response = await self.llm.ask(prompt)

            # Parse LLM response
            json_match = re.search(r"\\{.*\\}", response, re.DOTALL)
            if json_match:
                try:
                    strategy = json.loads(json_match.group())
                    # Ensure search_queries are strings
                    if "search_queries" in strategy:
                        strategy["search_queries"] = [
                            str(q) for q in strategy["search_queries"]
                        ]

                    # Extract website URL if detected
                    if strategy.get(
                        "approach"
                    ) == "direct_website_access" and not strategy.get("target_url"):
                        url_pattern = r"([a-zA-Z0-9-]+\\.[a-zA-Z]{2,})"
                        matches = re.findall(url_pattern, query)
                        if matches:
                            strategy["target_url"] = matches[0]

                    return strategy
                except json.JSONDecodeError:
                    pass

            return self._get_default_strategy(query)

        except Exception as e:
            logger.warning(f"Failed to analyze query with LLM: {e}")
            return self._get_default_strategy(query)

    async def _execute_dynamic_strategy(self, query: str, strategy: Dict) -> List[Dict]:
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
                website_result = await self._access_website_directly(target_url)
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
        """
        Search general web sources dynamically
        """
        results = []

        # Try DuckDuckGo
        ddg_results = await self._search_duckduckgo_web(query)
        results.extend(ddg_results)

        return results

    async def _search_news_sources(self, query: str) -> List[Dict]:
        """
        Search news sources dynamically
        """
        results = []

        # Try Bing News
        bing_results = await self._search_bing_news(query)
        results.extend(bing_results)

        return results

    async def _search_knowledge_sources(self, query: str) -> List[Dict]:
        """
        Search knowledge/reference sources dynamically
        """
        results = []

        # Try Wikipedia
        wiki_results = self._search_wikipedia_api(query)
        results.extend(wiki_results)

        # Try DuckDuckGo instant answers
        instant_results = self._search_duckduckgo_instant(query)
        results.extend(instant_results)

        return results

    async def _access_website_directly(self, url: str) -> Dict:
        """
        Access a website directly for analysis
        """
        try:
            if not url.startswith("http"):
                url = f"https://{url}"

            logger.info(f"🌐 Accessing website directly: {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract information
            title = soup.title.get_text() if soup.title else "No title"

            # Get meta description
            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "")

            # Get some content
            content_text = soup.get_text()[:2000]  # First 2000 chars

            return {
                "title": f"Direct Access: {title}",
                "url": url,
                "snippet": description if description else content_text[:300],
                "full_content": content_text,
                "source": "Direct Website Access",
                "relevance": 10,
                "direct_access": True,
            }

        except Exception as e:
            logger.warning(f"Failed to access website {url}: {str(e)}")
            return None

    def _deduplicate_and_prioritize(
        self, results: List[Dict], strategy: Dict
    ) -> List[Dict]:
        """
        Remove duplicates and prioritize results based on strategy
        """
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

    def _get_default_strategy(self, query: str) -> Dict:
        """
        Default strategy when LLM analysis fails
        """
        # Simple heuristics as fallback
        query_lower = query.lower()

        if any(
            domain in query_lower for domain in [".com", ".xyz", ".org", ".net", ".io"]
        ) and any(action in query_lower for action in ["review", "analyze", "check"]):
            return {
                "approach": "direct_website_access",
                "reasoning": "Detected website review request",
                "search_queries": [query],
                "priority_sources": ["web"],
                "content_focus": "detailed",
            }
        elif any(
            term in query_lower for term in ["news", "latest", "breaking", "today"]
        ):
            return {
                "approach": "news_search",
                "reasoning": "Detected news query",
                "search_queries": [query],
                "priority_sources": ["news"],
                "content_focus": "summary",
            }
        else:
            return {
                "approach": "combined_search",
                "reasoning": "Default comprehensive search strategy",
                "search_queries": [query],
                "priority_sources": ["web", "news"],
                "content_focus": "summary",
            }

    async def _simple_fallback_search(self, query: str) -> List[Dict]:
        """
        Simple fallback when all else fails
        """
        results = []

        # Try basic searches
        web_results = await self._search_web_sources(query)
        news_results = await self._search_news_sources(query)

        results.extend(web_results)
        results.extend(news_results)

        return results[:5]

    # Keep existing search methods but simplified
    async def _search_duckduckgo_web(self, query: str) -> List[Dict]:
        """Dynamic web search using DuckDuckGo"""
        try:
            if isinstance(query, dict):
                query = str(query.get("query", query))

            search_url = "https://duckduckgo.com/html/"
            params = {"q": query, "kl": "us-en", "s": "0"}

            response = self.session.get(search_url, params=params, timeout=10)

            if response.status_code == 403:
                logger.info(
                    f"🔄 DuckDuckGo blocked, trying instant answers API for: {query}"
                )
                return self._search_duckduckgo_instant(query)

            response.raise_for_status()

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, "html.parser")

            results = []
            result_links = soup.find_all("a", class_="result__url")[:5]
            result_titles = soup.find_all("a", class_="result__a")
            result_snippets = soup.find_all("a", class_="result__snippet")

            for i, (link, title_elem, snippet_elem) in enumerate(
                zip(result_links[:5], result_titles[:5], result_snippets[:5])
            ):
                if i >= 5:
                    break

                url = link.get("href", "")
                title = title_elem.get_text(strip=True) if title_elem else "No title"
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if url and not url.startswith("javascript:"):
                    relevance = self._calculate_web_result_relevance(
                        query, title, snippet
                    )

                    if relevance >= 2:
                        results.append(
                            {
                                "title": title,
                                "url": url,
                                "snippet": snippet[:300],
                                "source": "DuckDuckGo Web Search",
                                "relevance": relevance,
                                "search_engine": "duckduckgo",
                                "query": query,
                            }
                        )
            return results

        except Exception as e:
            logger.warning(f"DuckDuckGo web search error: {str(e)}")
            return self._search_duckduckgo_instant(query)

    async def _search_bing_news(self, query: str) -> List[Dict]:
        """Dynamic news search using Bing News"""
        try:
            if isinstance(query, dict):
                query = str(query.get("query", query))

            search_url = "https://www.bing.com/news/search"
            params = {"q": query, "qft": 'interval%3d"1"', "form": "YNWS02"}

            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, "html.parser")

            results = []
            news_cards = soup.find_all("div", class_=["news-card", "newsitem"])

            for card in news_cards[:5]:
                try:
                    title_elem = (
                        card.find("a", {"class": "title"})
                        or card.find("h2")
                        or card.find("a")
                    )
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    url = title_elem.get("href", "") if title_elem else ""
                    if url and not url.startswith("http"):
                        url = (
                            "https://www.bing.com" + url if url.startswith("/") else ""
                        )

                    snippet_elem = card.find("div", {"class": "snippet"}) or card.find(
                        "p"
                    )
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if title and url and url.startswith("http"):
                        relevance = self._calculate_web_result_relevance(
                            query, title, snippet
                        )

                        results.append(
                            {
                                "title": title,
                                "url": url,
                                "snippet": snippet[:300],
                                "source": "Bing News Search",
                                "relevance": relevance,
                                "search_engine": "bing",
                                "query": query,
                            }
                        )

                except Exception as e:
                    logger.warning(f"Failed to parse Bing news card: {str(e)}")
                    continue

            return results

        except Exception as e:
            logger.warning(f"Bing news search error: {str(e)}")
            return []

    def _search_wikipedia_api(self, query: str) -> List[Dict]:
        """Enhanced Wikipedia search"""
        try:
            if isinstance(query, dict):
                query = str(query.get("query", query))

            main_topic = self._extract_main_topic_for_wikipedia(query)
            logger.info(f"🔍 Wikipedia search for topic: {main_topic}")

            search_url = (
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(main_topic)}"
            )

            response = self.session.get(search_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("extract"):
                    relevance = self._calculate_topic_relevance(
                        query, data.get("title", ""), data.get("extract", "")
                    )

                    if relevance >= 3:
                        logger.info(f"📖 Wikipedia relevance: {relevance}")
                        return [
                            {
                                "title": data.get("title", query),
                                "url": data.get("content_urls", {})
                                .get("desktop", {})
                                .get("page", ""),
                                "snippet": data.get("extract", "")[:300],
                                "source": "Wikipedia",
                                "relevance": relevance + 2,
                            }
                        ]

            return []

        except Exception as e:
            logger.warning(f"Wikipedia API error: {str(e)}")
            return []

    def _search_duckduckgo_instant(self, query: str) -> List[Dict]:
        """Use DuckDuckGo Instant Answer API"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_redirect": "1",
                "no_html": "1",
                "skip_disambig": "1",
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []

            if data.get("Abstract"):
                relevance = self._calculate_topic_relevance(
                    query, data.get("Heading", ""), data.get("Abstract", "")
                )
                if relevance >= 2:
                    results.append(
                        {
                            "title": data.get("Heading", query),
                            "url": data.get(
                                "AbstractURL",
                                "https://duckduckgo.com/?q=" + quote(query),
                            ),
                            "snippet": data.get("Abstract")[:300],
                            "source": "DuckDuckGo Instant Answer",
                            "relevance": relevance + 3,
                        }
                    )

            return results

        except Exception as e:
            logger.warning(f"DuckDuckGo instant API error: {str(e)}")
            return []

    # Helper methods
    def _extract_main_topic_for_wikipedia(self, query: str) -> str:
        """Extract the main topic for Wikipedia search"""
        words = query.lower().split()
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "news",
            "latest",
            "today",
            "2025",
        }
        filtered_words = [
            word for word in words if word not in stop_words and len(word) > 2
        ]
        return " ".join(filtered_words[:3]) if filtered_words else query

    def _calculate_topic_relevance(self, query: str, title: str, content: str) -> int:
        """Calculate relevance between query and content"""
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        content_words = set(content.lower().split())

        title_matches = len(query_words.intersection(title_words))
        content_matches = len(query_words.intersection(content_words))

        return title_matches * 3 + content_matches

    def _calculate_web_result_relevance(
        self, query: str, title: str, content: str
    ) -> int:
        """Calculate relevance for web search results"""
        return self._calculate_topic_relevance(query, title, content)

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
                        enhanced_relevance = self._calculate_web_result_relevance(
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
            response = self.session.get(url, timeout=8)
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

            lines = [line.strip() for line in content_text.split("\\n") if line.strip()]
            content_text = " ".join(lines[:10])

            return content_text[:1500]

        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {str(e)}")
            return ""
