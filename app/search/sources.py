"""
Search Sources Module
Contains individual search engine implementations
"""

import re
from typing import Dict, List
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from app.logger import logger


class SearchSources:
    """
    Individual search engine implementations
    """

    def __init__(self):
        self.session = requests.Session()
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

    async def search_duckduckgo_web(self, query: str) -> List[Dict]:
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
                return self.search_duckduckgo_instant(query)

            response.raise_for_status()

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
                    relevance = self._calculate_relevance(query, title, snippet)

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
            return self.search_duckduckgo_instant(query)

    async def search_bing_news(self, query: str) -> List[Dict]:
        """Dynamic news search using Bing News"""
        try:
            if isinstance(query, dict):
                query = str(query.get("query", query))

            search_url = "https://www.bing.com/news/search"
            params = {"q": query, "qft": 'interval%3d"1"', "form": "YNWS02"}

            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()

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
                        relevance = self._calculate_relevance(query, title, snippet)

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

    def search_wikipedia_api(self, query: str) -> List[Dict]:
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
                    relevance = self._calculate_relevance(
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

    def search_duckduckgo_instant(self, query: str) -> List[Dict]:
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
                relevance = self._calculate_relevance(
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

    async def access_website_directly(self, url: str) -> Dict:
        """Access a website directly for analysis"""
        try:
            if not url.startswith("http"):
                url = f"https://{url}"

            logger.info(f"🌐 Accessing website directly: {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

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

    def _calculate_relevance(self, query: str, title: str, content: str) -> int:
        """Calculate relevance between query and content"""
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        content_words = set(content.lower().split())

        title_matches = len(query_words.intersection(title_words))
        content_matches = len(query_words.intersection(content_words))

        return title_matches * 3 + content_matches
