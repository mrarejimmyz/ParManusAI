"""
LLM-Driven Search Engine Implementations

Separates different search engine implementations for better maintainability.
"""

import asyncio
import json
import urllib.parse
from typing import Dict, List

import aiohttp
import requests
from bs4 import BeautifulSoup

from app.logger import logger


class WebSearchEngine:
    """Handles general web search operations."""

    async def search_duckduckgo_web(self, query: str) -> List[Dict]:
        """Search DuckDuckGo web results."""
        try:
            logger.info(f"🔍 Searching DuckDuckGo web: {query}")

            # Use DuckDuckGo HTML search
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_duckduckgo_html(html)

            return []

        except Exception as e:
            logger.error(f"❌ DuckDuckGo web search failed: {e}")
            return []

    def _parse_duckduckgo_html(self, html: str) -> List[Dict]:
        """Parse DuckDuckGo HTML results."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Find result containers
            result_containers = soup.find_all("div", class_="result")

            for container in result_containers:
                try:
                    # Extract title
                    title_elem = container.find("a", class_="result__a")
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    url = title_elem.get("href", "")

                    # Extract snippet
                    snippet_elem = container.find("a", class_="result__snippet")
                    snippet = snippet_elem.text.strip() if snippet_elem else ""

                    if title and url:
                        results.append(
                            {
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "source": "DuckDuckGo Web",
                            }
                        )

                except Exception as e:
                    logger.debug(f"Error parsing DDG result: {e}")
                    continue

            logger.info(f"✅ Found {len(results)} DuckDuckGo web results")
            return results[:10]  # Limit to top 10

        except Exception as e:
            logger.error(f"❌ Error parsing DuckDuckGo HTML: {e}")
            return []


class NewsSearchEngine:
    """Handles news-specific search operations."""

    async def search_bing_news(self, query: str) -> List[Dict]:
        """Search Bing News."""
        try:
            logger.info(f"📰 Searching Bing News: {query}")

            # Bing News search (using public endpoint)
            url = "https://www.bing.com/news/search"
            params = {"q": query, "format": "rss"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._parse_bing_news_rss(content)

            return []

        except Exception as e:
            logger.error(f"❌ Bing News search failed: {e}")
            return []

    def _parse_bing_news_rss(self, rss_content: str) -> List[Dict]:
        """Parse Bing News RSS results."""
        try:
            soup = BeautifulSoup(rss_content, "xml")
            results = []

            items = soup.find_all("item")
            for item in items:
                try:
                    title = item.find("title")
                    link = item.find("link")
                    description = item.find("description")
                    pub_date = item.find("pubDate")

                    if title and link:
                        results.append(
                            {
                                "title": title.text.strip(),
                                "url": link.text.strip(),
                                "snippet": (
                                    description.text.strip() if description else ""
                                ),
                                "published": pub_date.text.strip() if pub_date else "",
                                "source": "Bing News",
                            }
                        )

                except Exception as e:
                    logger.debug(f"Error parsing Bing news item: {e}")
                    continue

            logger.info(f"✅ Found {len(results)} Bing news results")
            return results[:10]

        except Exception as e:
            logger.error(f"❌ Error parsing Bing News RSS: {e}")
            return []


class KnowledgeSearchEngine:
    """Handles knowledge base searches (Wikipedia, etc.)."""

    def search_wikipedia_api(self, query: str) -> List[Dict]:
        """Search Wikipedia using API."""
        try:
            logger.info(f"📚 Searching Wikipedia: {query}")

            # Extract main topic
            topic = self._extract_main_topic_for_wikipedia(query)

            # Wikipedia API search
            api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
            encoded_topic = urllib.parse.quote(topic)

            try:
                response = requests.get(
                    f"{api_url}{encoded_topic}",
                    timeout=10,
                    headers={"User-Agent": "ParManus/1.0"},
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "title": data.get("title", ""),
                            "url": data.get("content_urls", {})
                            .get("desktop", {})
                            .get("page", ""),
                            "snippet": data.get("extract", ""),
                            "source": "Wikipedia",
                        }
                    ]

            except Exception as e:
                logger.debug(f"Wikipedia API failed: {e}")

            # Fallback to search API
            search_url = "https://en.wikipedia.org/api/rest_v1/page/search/"
            params = {"q": topic, "limit": 5}

            try:
                response = requests.get(
                    search_url,
                    params=params,
                    timeout=10,
                    headers={"User-Agent": "ParManus/1.0"},
                )

                if response.status_code == 200:
                    data = response.json()
                    results = []

                    for page in data.get("pages", []):
                        results.append(
                            {
                                "title": page.get("title", ""),
                                "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page.get('key', ''))}",
                                "snippet": page.get("excerpt", ""),
                                "source": "Wikipedia",
                            }
                        )

                    logger.info(f"✅ Found {len(results)} Wikipedia results")
                    return results

            except Exception as e:
                logger.debug(f"Wikipedia search API failed: {e}")

            return []

        except Exception as e:
            logger.error(f"❌ Wikipedia search failed: {e}")
            return []

    def _extract_main_topic_for_wikipedia(self, query: str) -> str:
        """Extract main topic from query for Wikipedia search."""
        # Remove common question words
        stop_words = [
            "what",
            "is",
            "the",
            "a",
            "an",
            "how",
            "why",
            "when",
            "where",
            "who",
        ]
        words = query.lower().split()

        # Filter out stop words
        filtered_words = [word for word in words if word not in stop_words]

        # Return first few meaningful words
        if filtered_words:
            return " ".join(filtered_words[:3])
        else:
            return query

    def search_duckduckgo_instant(self, query: str) -> List[Dict]:
        """Search DuckDuckGo instant answers."""
        try:
            logger.info(f"⚡ Searching DuckDuckGo instant: {query}")

            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = []

                # Abstract (main answer)
                if data.get("Abstract"):
                    results.append(
                        {
                            "title": data.get("AbstractText", ""),
                            "url": data.get("AbstractURL", ""),
                            "snippet": data.get("Abstract", ""),
                            "source": "DuckDuckGo Instant",
                        }
                    )

                # Related topics
                for topic in data.get("RelatedTopics", [])[:3]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append(
                            {
                                "title": topic.get("FirstURL", "")
                                .split("/")[-1]
                                .replace("_", " "),
                                "url": topic.get("FirstURL", ""),
                                "snippet": topic.get("Text", ""),
                                "source": "DuckDuckGo Related",
                            }
                        )

                logger.info(f"✅ Found {len(results)} DuckDuckGo instant results")
                return results

            return []

        except Exception as e:
            logger.error(f"❌ DuckDuckGo instant search failed: {e}")
            return []


class ContentExtractor:
    """Handles content extraction from web pages."""

    async def extract_page_content(self, url: str) -> str:
        """Extract main content from a web page."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_text_from_html(html)

            return ""

        except Exception as e:
            logger.error(f"❌ Failed to extract content from {url}: {e}")
            return ""

    def _extract_text_from_html(self, html: str) -> str:
        """Extract clean text from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Try to find main content
            content_selectors = [
                "article",
                ".content",
                ".main-content",
                ".post-content",
                ".entry-content",
                "main",
                "#content",
            ]

            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break

            # Fallback to body
            if not content:
                content = soup.find("body")

            if content:
                text = content.get_text()
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (
                    phrase.strip() for line in lines for phrase in line.split("  ")
                )
                text = " ".join(chunk for chunk in chunks if chunk)

                # Limit length
                return text[:2000] + "..." if len(text) > 2000 else text

            return ""

        except Exception as e:
            logger.error(f"❌ Error extracting text from HTML: {e}")
            return ""
