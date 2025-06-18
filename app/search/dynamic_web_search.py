"""
Dynamic Web Search and Scraping System
Performs real web searches, discovers links, and scrapes content intelligently
"""

import asyncio
import random
import re
import time
from typing import Dict, List, Optional
from urllib.parse import quote, urljoin, urlparse

import aiohttp
import requests
from bs4 import BeautifulSoup

from app.logger import logger
from app.search.intelligent_scraper import IntelligentScraper


class DynamicWebSearcher:
    """
    Performs dynamic web searches and intelligent content scraping
    """

    def __init__(self, llm=None):
        self.llm = llm
        self.session = None

        # Initialize intelligent scraper
        self.intelligent_scraper = IntelligentScraper(llm=llm)

        # We'll add intelligent scraping directly here instead of importing
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def search_and_scrape(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Main method: search for query, find relevant links, and scrape content
        """
        logger.info(f"🔍 Starting dynamic web search for: {query}")

        # Store current query for context in intelligent scraping
        self.current_query = query

        # Step 1: Perform web search to find links
        search_results = await self._perform_web_search(query)

        if not search_results:
            logger.warning("No search results found")
            return []

        # Step 2: Intelligently select which links to scrape
        selected_links = await self._select_best_links(
            query, search_results, max_results
        )

        # Step 3: Scrape content from selected links
        scraped_content = await self._scrape_multiple_links(selected_links)

        return scraped_content

    async def _perform_web_search(self, query: str) -> List[Dict]:
        """
        Perform actual web search using multiple search engines
        """
        all_results = []

        # Try multiple search engines for better coverage
        search_engines = [
            self._search_duckduckgo,
            self._search_bing,
            self._search_google,
        ]

        for search_engine in search_engines:
            try:
                results = await search_engine(query)
                all_results.extend(results)
                # Add small delay between searches
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Search engine failed: {e}")
                continue

        # Remove duplicates and return
        unique_results = self._deduplicate_results(all_results)
        logger.info(f"Found {len(unique_results)} unique search results")
        return unique_results

    async def _search_duckduckgo(self, query: str) -> List[Dict]:
        """
        Search using DuckDuckGo (more permissive for scraping)
        """
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_duckduckgo_results(html)
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")

        return []

    async def _search_bing(self, query: str) -> List[Dict]:
        """
        Search using Bing
        """
        try:
            search_url = f"https://www.bing.com/search?q={quote(query)}"

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_bing_results(html)
        except Exception as e:
            logger.error(f"Bing search failed: {e}")

        return []

    async def _search_google(self, query: str) -> List[Dict]:
        """
        Search using Google (backup, more likely to be blocked)
        """
        try:
            search_url = f"https://www.google.com/search?q={quote(query)}"

            # Use more conservative approach for Google
            await asyncio.sleep(random.uniform(1, 3))

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_google_results(html)
        except Exception as e:
            logger.warning(f"Google search failed (expected): {e}")

        return []

    def _parse_duckduckgo_results(self, html: str) -> List[Dict]:
        """Parse DuckDuckGo search results"""
        results = []
        soup = BeautifulSoup(html, "html.parser")

        for result in soup.find_all("div", class_="result"):
            try:
                title_elem = result.find("a", class_="result__a")
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get("href")

                    snippet_elem = result.find("a", class_="result__snippet")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if url and title:
                        results.append(
                            {
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "source": "DuckDuckGo",
                            }
                        )
            except Exception as e:
                continue

        return results

    def _parse_bing_results(self, html: str) -> List[Dict]:
        """Parse Bing search results"""
        results = []
        soup = BeautifulSoup(html, "html.parser")

        for result in soup.find_all("li", class_="b_algo"):
            try:
                title_elem = result.find("h2")
                link_elem = title_elem.find("a") if title_elem else None

                if link_elem:
                    title = link_elem.get_text(strip=True)
                    url = link_elem.get("href")

                    snippet_elem = result.find("p")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if url and title:
                        results.append(
                            {
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "source": "Bing",
                            }
                        )
            except Exception as e:
                continue

        return results

    def _parse_google_results(self, html: str) -> List[Dict]:
        """Parse Google search results"""
        results = []
        soup = BeautifulSoup(html, "html.parser")

        for result in soup.find_all("div", class_="g"):
            try:
                title_elem = result.find("h3")
                link_elem = result.find("a")

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get("href")

                    snippet_elem = result.find("span")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if url and title and url.startswith("http"):
                        results.append(
                            {
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "source": "Google",
                            }
                        )
            except Exception as e:
                continue

        return results

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate URLs from search results"""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results

    async def _select_best_links(
        self, query: str, search_results: List[Dict], max_results: int
    ) -> List[Dict]:
        """
        Intelligently select which links are most likely to contain relevant information
        """
        if not self.llm:
            # Fallback: use simple relevance scoring
            return self._simple_link_selection(query, search_results, max_results)

        try:
            # Use LLM to intelligently select best links
            return await self._llm_link_selection(query, search_results, max_results)
        except Exception as e:
            logger.warning(f"LLM link selection failed: {e}, using fallback")
            return self._simple_link_selection(query, search_results, max_results)

    def _simple_link_selection(
        self, query: str, search_results: List[Dict], max_results: int
    ) -> List[Dict]:
        """
        Simple relevance-based link selection
        """
        query_terms = query.lower().split()

        # Score each result based on relevance
        for result in search_results:
            score = 0
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            url = result.get("url", "").lower()

            # Score based on query terms in title, snippet, and URL
            for term in query_terms:
                if term in title:
                    score += 3
                if term in snippet:
                    score += 2
                if term in url:
                    score += 1

            # Boost certain domains for crypto queries
            if any(
                crypto_term in query.lower()
                for crypto_term in ["crypto", "bitcoin", "ethereum", "blockchain"]
            ):
                crypto_domains = [
                    "coindesk",
                    "cointelegraph",
                    "coinmarketcap",
                    "binance",
                    "kraken",
                    "crypto",
                ]
                if any(domain in url for domain in crypto_domains):
                    score += 5

            result["relevance_score"] = score

        # Sort by score and return top results
        sorted_results = sorted(
            search_results, key=lambda x: x.get("relevance_score", 0), reverse=True
        )
        return sorted_results[:max_results]

    async def _llm_link_selection(
        self, query: str, search_results: List[Dict], max_results: int
    ) -> List[Dict]:
        """
        Use LLM to intelligently select the best links to scrape
        """
        # Create a summary of available links for the LLM
        links_summary = "\n".join(
            [
                f"{i+1}. {result['title']}\n   URL: {result['url']}\n   Snippet: {result['snippet'][:100]}..."
                for i, result in enumerate(
                    search_results[:20]
                )  # Limit to top 20 for LLM
            ]
        )

        prompt = f"""I found these search results for the query: "{query}"

{links_summary}

Please select the {max_results} most relevant and useful links that would provide the best information to answer the query. Consider:
1. Relevance to the query
2. Likely to have current/accurate information
3. Authoritative sources
4. Accessibility (avoid paywalls if possible)

Respond with only the numbers of the selected links, separated by commas (e.g., "1,3,7,12")."""

        try:
            response = await self.llm.ask([{"role": "user", "content": prompt}])
            selected_numbers = [
                int(x.strip()) for x in response.split(",") if x.strip().isdigit()
            ]

            selected_results = []
            for num in selected_numbers:
                if 1 <= num <= len(search_results):
                    selected_results.append(search_results[num - 1])

            return selected_results[:max_results]

        except Exception as e:
            logger.error(f"LLM link selection failed: {e}")
            return self._simple_link_selection(query, search_results, max_results)

    async def _scrape_multiple_links(self, links: List[Dict]) -> List[Dict]:
        """
        Scrape content from multiple links with intelligent error handling
        """
        scraped_results = []

        for link in links:
            try:
                content = await self._scrape_single_link(link["url"])
                if content:
                    scraped_results.append(
                        {
                            "title": link["title"],
                            "url": link["url"],
                            "content": content,
                            "source": "scraped",
                            "original_snippet": link.get("snippet", ""),
                        }
                    )

                # Add delay between scrapes to be respectful
                await asyncio.sleep(random.uniform(1, 2))

            except Exception as e:
                logger.warning(f"Failed to scrape {link['url']}: {e}")
                continue

        return scraped_results

    async def _scrape_single_link(self, url: str) -> Optional[str]:
        """
        Scrape content from a single URL using intelligent scraper
        """
        try:
            # Use intelligent scraper with context about the search
            search_context = getattr(self, "current_query", "")
            content = await self.intelligent_scraper.intelligent_scrape(
                url, context=search_context
            )

            if content:
                logger.info(
                    f"✅ Successfully scraped content from {url} ({len(content)} chars)"
                )
                return content
            else:
                logger.warning(f"⚠️ No content extracted from {url}")
                return None

        except Exception as e:
            logger.warning(f"Intelligent scraping failed for {url}: {e}")
            # Fallback to basic scraping
            return await self._basic_scrape_fallback(url)

    async def _basic_scrape_fallback(self, url: str) -> Optional[str]:
        """Basic fallback scraping method when intelligent scraper fails"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        try:
                            content = await response.text()
                            return self._extract_main_content(content)
                        except UnicodeDecodeError:
                            logger.warning(
                                f"Unicode decode error for {url}, trying different encoding"
                            )
                            content = await response.read()
                            return content.decode("utf-8", errors="ignore")[:5000]
                    else:
                        logger.warning(
                            f"Basic fallback failed: HTTP {response.status} for {url}"
                        )
                        return None

        except Exception as e:
            logger.warning(f"Basic fallback scraping failed for {url}: {e}")
            return None

    def _extract_main_content(self, html: str) -> str:
        """
        Extract main content from HTML, filtering out navigation, ads, etc.
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for element in soup(
                ["script", "style", "nav", "header", "footer", "aside", "iframe"]
            ):
                element.decompose()

            # Try to find main content area
            main_content = None

            # Look for common content containers
            content_selectors = [
                "article",
                "main",
                '[role="main"]',
                ".content",
                ".article-content",
                ".post-content",
                ".entry-content",
                "#content",
                ".main-content",
            ]

            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    main_content = content_elem
                    break

            # Fallback to body if no specific content area found
            if not main_content:
                main_content = soup.find("body")

            if main_content:
                # Get text content and clean it
                text = main_content.get_text(separator=" ", strip=True)
                # Clean up extra whitespace
                text = re.sub(r"\s+", " ", text)
                return text[:5000]  # Limit to reasonable length
            else:
                return ""

        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return ""

    async def close(self):
        """
        Clean up resources
        """
        if self.intelligent_scraper:
            await self.intelligent_scraper.close()
        if self.session:
            await self.session.close()
