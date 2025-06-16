"""
Optimized Bulletproof Search Implementation
Fully dynamic search using real search engines - no hardcoded URLs!
"""

import json
import re
from typing import Dict, List, Optional
from urllib.parse import quote

import requests

from app.logger import logger


class OptimizedBulletproofSearch:
    """
    Optimized search with LLM-driven dynamic source selection and filtering
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
        # Dynamic search engines (no hardcoded URLs!)
        self.search_engines = [
            "duckduckgo",
            "bing",
            "wikipedia",
            "google_news_search",  # Dynamic news search
        ]

    async def perform_google_search(self, query: str) -> Dict:
        """
        Fully dynamic search using multiple search engines - no hardcoded URLs!
        """
        logger.info(f"🔍 Dynamic bulletproof search for: {query}")

        all_results = []

        # 1. Generate dynamic search queries based on user intent
        search_queries = await self._generate_dynamic_search_queries(query)
        logger.info(f"🧠 Generated {len(search_queries)} dynamic search queries")

        # 2. Execute searches across multiple engines dynamically
        for search_query in search_queries:
            logger.info(f"🔍 Executing dynamic search: {search_query}")

            # DuckDuckGo web search (dynamic results)
            ddg_results = await self._search_duckduckgo_web(search_query)
            if ddg_results:
                all_results.extend(ddg_results)
                logger.info(f"✅ DuckDuckGo web returned {len(ddg_results)} results")

            # Bing news search (dynamic results)
            bing_results = await self._search_bing_news(search_query)
            if bing_results:
                all_results.extend(bing_results)
                logger.info(f"✅ Bing news returned {len(bing_results)} results")

            # Wikipedia dynamic search
            wiki_results = self._search_wikipedia_api(search_query)
            if wiki_results:
                all_results.extend(wiki_results)
                logger.info(f"✅ Wikipedia returned {len(wiki_results)} results")

        # 3. Dynamic content extraction from found URLs
        enriched_results = await self._enrich_results_with_content(all_results)

        if enriched_results:
            # Remove duplicates and sort by relevance
            unique_results = []
            seen_urls = set()
            for result in enriched_results:
                if result.get("url") and result["url"] not in seen_urls:
                    seen_urls.add(result["url"])
                    unique_results.append(result)

            # Sort by relevance score
            unique_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)

            logger.info(f"🎯 Total unique dynamic results: {len(unique_results)}")
            return {
                "success": True,
                "query": query,
                "results": unique_results[:10],  # Top 10 most relevant
                "method": "fully_dynamic_search",
                "real_search": True,
                "search_queries": search_queries,
            }
        else:
            logger.warning(f"⚠️ No dynamic results found for query: {query}")
            return {
                "success": False,
                "query": query,
                "results": [],
                "method": "dynamic_search_failed",
                "error": "No current results found from dynamic search engines",
                "real_search": True,
            }

    def _search_duckduckgo_instant(self, query: str) -> List[Dict]:
        """
        Use DuckDuckGo Instant Answer API for factual content
        """
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
            logger.info(f"🔍 DuckDuckGo API response keys: {list(data.keys())}")

            # Debug: print what we get
            if data.get("Abstract"):
                logger.info(f"📄 Abstract found: {data.get('Heading', 'No heading')}")
            if data.get("RelatedTopics"):
                logger.info(
                    f"🔗 Related topics found: {len(data.get('RelatedTopics', []))}"
                )

            results = []

            # Check for instant answer
            if data.get("Abstract"):
                relevance = self._calculate_topic_relevance(
                    query, data.get("Heading", ""), data.get("Abstract", "")
                )
                logger.info(f"🎯 Abstract relevance: {relevance}")
                if relevance >= 2:  # Lower threshold for broader coverage
                    results.append(
                        {
                            "title": data.get("Heading", query),
                            "url": data.get(
                                "AbstractURL",
                                "https://duckduckgo.com/?q=" + quote(query),
                            ),
                            "snippet": data.get("Abstract")[:300],
                            "source": "DuckDuckGo Instant Answer",
                            "relevance": relevance + 3,  # Boost instant answers
                        }
                    )

            # Check for related topics
            for topic in data.get("RelatedTopics", [])[:3]:  # Check more topics
                if isinstance(topic, dict) and topic.get("FirstURL"):
                    text = topic.get("Text", "")
                    title = text.split(" - ")[0] if " - " in text else text
                    relevance = self._calculate_topic_relevance(query, title, text)
                    logger.info(f"🔗 Topic relevance: {relevance} for '{title[:50]}'")

                    if relevance >= 1:  # Very low threshold for topics
                        results.append(
                            {
                                "title": title[:100],
                                "url": topic["FirstURL"],
                                "snippet": text[:300],
                                "source": "DuckDuckGo Related Topic",
                                "relevance": relevance,
                            }
                        )

            return results

        except Exception as e:
            logger.warning(f"DuckDuckGo instant API error: {str(e)}")
            return []

    def _search_wikipedia_api(self, query: str) -> List[Dict]:
        """
        Enhanced Wikipedia search with relevance filtering
        """
        try:
            # Extract main topic for Wikipedia search
            main_topic = self._extract_main_topic_for_wikipedia(query)
            logger.info(f"🔍 Wikipedia search for topic: {main_topic}")

            # Try direct page summary first
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
                    logger.info(f"📖 Wikipedia relevance: {relevance}")
                    if relevance >= 1:  # Lower threshold
                        return [
                            {
                                "title": data.get("title", query),
                                "url": data.get("content_urls", {})
                                .get("desktop", {})
                                .get("page", ""),
                                "snippet": data.get("extract", "")[:300],
                                "source": "Wikipedia",
                                "relevance": relevance + 2,  # Boost Wikipedia
                            }
                        ]

            return []

        except Exception as e:
            logger.warning(f"Wikipedia API error: {str(e)}")
            return []

    def _extract_topic_keywords(self, query: str) -> Dict[str, List[str]]:
        """Extract main topic keywords from query"""
        # For general queries like "latest news today", return broad topics
        query_lower = query.lower()

        if any(
            word in query_lower
            for word in ["news", "latest", "today", "breaking", "current"]
        ):
            return {
                "general": ["news", "latest", "today", "current", "breaking"],
                "topics": ["world", "politics", "economy", "technology", "health"],
            }

        # Extract keywords from the query
        words = query_lower.split()
        return {"general": words, "topics": words}

    def _extract_main_topic_for_wikipedia(self, query: str) -> str:
        """Extract the main topic for Wikipedia search"""
        # Remove common words and focus on the main topic
        stop_words = {
            "latest",
            "news",
            "today",
            "breaking",
            "current",
            "analysis",
            "report",
        }
        words = [w for w in query.lower().split() if w not in stop_words]

        if not words:
            return "current events"

        return " ".join(words[:2])  # Take first 1-2 meaningful words

    def _calculate_topic_relevance(self, query: str, title: str, content: str) -> int:
        """
        Calculate topic relevance score (0-10)
        More lenient scoring for broader coverage
        """
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        content_words = set(content.lower().split())

        # Count word matches
        title_matches = len(query_words.intersection(title_words))
        content_matches = len(query_words.intersection(content_words))

        # Base relevance
        relevance = title_matches * 2 + content_matches

        # Boost for general news queries
        if any(
            word in query.lower() for word in ["news", "latest", "today", "current"]
        ):
            if any(
                word in title.lower() or word in content.lower()
                for word in ["news", "latest", "today", "current", "breaking"]
            ):
                relevance += 3

        return min(relevance, 10)  # Cap at 10

    def _calculate_strict_news_relevance(
        self, query: str, title: str, summary: str, main_topics: Dict
    ) -> int:
        """
        Calculate news relevance with broader criteria
        """
        relevance = 0

        # For general news queries, give base relevance to all current news
        query_lower = query.lower()
        if any(
            term in query_lower
            for term in ["news", "latest", "today", "breaking", "current"]
        ):
            relevance += 4  # Higher base score for general news queries

        # Check for general news terms in content
        news_terms = ["today", "breaking", "latest", "current", "update", "report"]
        title_lower = title.lower()
        summary_lower = summary.lower()

        # Base relevance for any news content when looking for "news"
        if any(term in title_lower or term in summary_lower for term in news_terms):
            relevance += 2

        # Check for topic matches
        for topic_list in main_topics.values():
            for topic in topic_list:
                if topic in title_lower:
                    relevance += 2
                if topic in summary_lower:
                    relevance += 1

        # Check for recent date indicators
        if any(
            term in title_lower or term in summary_lower
            for term in ["today", "2025", "june"]
        ):
            relevance += 1

        return min(relevance, 10)  # Cap at 10

    async def _generate_dynamic_search_queries(self, query: str) -> List[str]:
        """
        Generate multiple dynamic search queries based on user intent
        """
        try:
            if self.llm:
                prompt = f"""
                Generate 3-4 specific search queries for finding current news based on this request:

                User Query: "{query}"

                Create queries that will find:
                1. Current/recent news articles
                2. Location-specific sources if mentioned
                3. Relevant breaking news
                4. Official reports or announcements

                Make queries specific and likely to return current results.

                Examples:
                - For "Latvia news today" → ["Latvia breaking news 2025", "Latvia headlines June 2025", "Riga news today"]
                - For "Nepal politics" → ["Nepal political news 2025", "Nepal government latest", "Kathmandu politics today"]

                Return only a JSON array of search strings:
                ["query1", "query2", "query3"]
                """

                response = await self.llm.ask(prompt)

                # Extract JSON array from response
                import json
                import re

                json_match = re.search(r"\[.*?\]", response, re.DOTALL)
                if json_match:
                    try:
                        queries = json.loads(json_match.group())
                        if isinstance(queries, list) and queries:
                            logger.info(
                                f"🧠 LLM generated {len(queries)} dynamic queries"
                            )
                            return queries
                    except json.JSONDecodeError:
                        pass

            # Fallback: generate queries based on analysis
            return self._generate_fallback_queries(query)

        except Exception as e:
            logger.warning(f"Failed to generate dynamic queries: {e}")
            return self._generate_fallback_queries(query)

    def _generate_fallback_queries(self, query: str) -> List[str]:
        """
        Generate fallback search queries when LLM is not available
        """
        base_queries = []
        query_lower = query.lower()

        # Extract key terms
        words = query_lower.split()
        location_words = [
            "nepal",
            "india",
            "latvia",
            "china",
            "usa",
            "uk",
            "europe",
            "asia",
        ]
        topic_words = [
            "news",
            "politics",
            "economy",
            "business",
            "technology",
            "health",
        ]

        # Detect location
        location = None
        for word in words:
            if word in location_words:
                location = word
                break

        # Detect topic
        topic = "news"  # default
        for word in words:
            if word in topic_words:
                topic = word
                break

        if location:
            # Location-specific queries
            base_queries.extend(
                [
                    f"{location} {topic} today 2025",
                    f"{location} breaking news June 2025",
                    f"{location} latest headlines",
                    f"{location} current affairs 2025",
                ]
            )
        else:
            # General queries
            base_queries.extend(
                [
                    f"{topic} today 2025",
                    f"breaking {topic} June 2025",
                    f"latest {topic} headlines",
                    f"current {topic} analysis",
                ]
            )

        return base_queries[:4]  # Return top 4 queries

    async def _search_duckduckgo_web(self, query: str) -> List[Dict]:
        """
        Dynamic web search using DuckDuckGo (not just instant answers)
        """
        try:
            # Use DuckDuckGo HTML search for web results
            search_url = "https://duckduckgo.com/html/"
            params = {
                "q": query,
                "kl": "us-en",  # English results
                "s": "0",  # Start from first result
            }

            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            # Parse HTML results
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, "html.parser")

            results = []
            # Look for search result links
            result_links = soup.find_all("a", class_="result__url")
            result_titles = soup.find_all("a", class_="result__a")
            result_snippets = soup.find_all("a", class_="result__snippet")

            for i, (link, title_elem, snippet_elem) in enumerate(
                zip(result_links[:5], result_titles[:5], result_snippets[:5])
            ):
                if i >= 5:  # Limit results
                    break

                url = link.get("href", "")
                title = title_elem.get_text(strip=True) if title_elem else "No title"
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if url and not url.startswith("javascript:"):
                    # Calculate relevance
                    relevance = self._calculate_web_result_relevance(
                        query, title, snippet
                    )

                    if relevance >= 2:  # Filter out irrelevant results
                        results.append(
                            {
                                "title": title,
                                "url": url,
                                "snippet": snippet[:300],
                                "source": "DuckDuckGo Web Search",
                                "relevance": relevance,
                                "search_engine": "duckduckgo",
                            }
                        )
            return results

        except Exception as e:
            logger.warning(f"DuckDuckGo web search error: {str(e)}")
            return []

    async def _search_bing_news(self, query: str) -> List[Dict]:
        """
        Dynamic news search using Bing News web scraping (no RSS dependencies)
        """
        try:
            # Use Bing news search with web scraping
            search_url = "https://www.bing.com/news/search"
            params = {
                "q": query,
                "qft": 'interval%3d"1"',  # Recent results
                "form": "YNWS02",
            }

            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            # Parse HTML content for news results
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, "html.parser")

            results = []

            # Find news articles in Bing's structure
            news_cards = soup.find_all("div", class_=["news-card", "newsitem"])

            for card in news_cards[:5]:  # Limit to top 5 results
                try:
                    # Extract title
                    title_elem = (
                        card.find("a", {"class": "title"})
                        or card.find("h2")
                        or card.find("a")
                    )
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    # Extract URL
                    url = title_elem.get("href", "") if title_elem else ""
                    if url and not url.startswith("http"):
                        url = (
                            "https://www.bing.com" + url if url.startswith("/") else ""
                        )

                    # Extract snippet/description
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

    def _calculate_web_result_relevance(
        self, query: str, title: str, content: str
    ) -> int:
        """
        Calculate relevance for web search results
        """
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        content_words = set(content.lower().split())

        # Word match scoring
        title_matches = len(query_words.intersection(title_words))
        content_matches = len(query_words.intersection(content_words))
        relevance = title_matches * 3 + content_matches

        # Boost for news-related content
        news_indicators = [
            "news",
            "breaking",
            "latest",
            "today",
            "2025",
            "report",
            "update",
        ]
        if any(
            word in title.lower() or word in content.lower() for word in news_indicators
        ):
            relevance += 3

        # Boost for recent content
        recent_indicators = ["june", "2025", "today", "yesterday", "this week"]
        if any(
            word in title.lower() or word in content.lower()
            for word in recent_indicators
        ):
            relevance += 2

        return min(relevance, 15)

    async def _enrich_results_with_content(self, results: List[Dict]) -> List[Dict]:
        """
        Enrich search results by extracting more content from the actual web pages
        """
        enriched_results = []

        for result in results[:8]:  # Limit to avoid too many requests
            try:
                url = result.get("url", "")
                if not url or "example.com" in url:
                    enriched_results.append(result)
                    continue

                # Extract more content from the page
                page_content = await self._extract_page_content(url)

                if page_content:
                    # Update the result with richer content
                    result["full_content"] = page_content[:1000]  # First 1000 chars
                    result["enhanced"] = True

                    # Recalculate relevance with full content
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
        """
        Extract main content from a web page
        """
        try:
            response = self.session.get(url, timeout=8)
            response.raise_for_status()

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Try to find main content areas
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

            # Fallback to body content
            if not content_text:
                content_text = soup.get_text(strip=True)

            # Clean and limit content
            lines = [line.strip() for line in content_text.split("\n") if line.strip()]
            content_text = " ".join(lines[:10])  # First 10 non-empty lines

            return content_text[:1500]  # Limit to 1500 characters

        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {str(e)}")
            return ""
