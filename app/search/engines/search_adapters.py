"""
Search engine adapters for different web search providers.
"""

import asyncio
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from app.logger import logger


class SearchEngineAdapter:
    """Base class for search engine adapters."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def search(self, query: str) -> List[Dict]:
        """Search for a query. Should be implemented by subclasses."""
        raise NotImplementedError


class DuckDuckGoAdapter(SearchEngineAdapter):
    """DuckDuckGo search adapter."""

    async def search(self, query: str) -> List[Dict]:
        """Search using DuckDuckGo."""
        try:
            url = f"https://html.duckduckgo.com/html/?q={query}"

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_duckduckgo_results(html)
                    else:
                        logger.warning(
                            f"DuckDuckGo search failed with status {response.status}"
                        )
                        return []

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    def _parse_duckduckgo_results(self, html: str) -> List[Dict]:
        """Parse DuckDuckGo search results."""
        results = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            result_elements = soup.find_all("div", class_="result")

            for element in result_elements[:10]:  # Limit to top 10
                try:
                    title_element = element.find("a", class_="result__a")
                    if title_element:
                        title = title_element.get_text().strip()
                        url = title_element.get("href", "")

                        snippet_element = element.find("a", class_="result__snippet")
                        snippet = (
                            snippet_element.get_text().strip()
                            if snippet_element
                            else ""
                        )

                        if url and title:
                            results.append(
                                {
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet,
                                    "source": "duckduckgo",
                                }
                            )
                except Exception as e:
                    logger.debug(f"Error parsing DuckDuckGo result element: {e}")
                    continue

            logger.info(f"DuckDuckGo found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error parsing DuckDuckGo results: {e}")
            return []


class BingAdapter(SearchEngineAdapter):
    """Bing search adapter."""

    async def search(self, query: str) -> List[Dict]:
        """Search using Bing."""
        try:
            url = f"https://www.bing.com/search?q={query}"

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_bing_results(html)
                    else:
                        logger.warning(
                            f"Bing search failed with status {response.status}"
                        )
                        return []

        except Exception as e:
            logger.error(f"Bing search error: {e}")
            return []

    def _parse_bing_results(self, html: str) -> List[Dict]:
        """Parse Bing search results."""
        results = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            result_elements = soup.find_all("li", class_="b_algo")

            for element in result_elements[:10]:  # Limit to top 10
                try:
                    title_element = element.find("h2")
                    if title_element:
                        link_element = title_element.find("a")
                        if link_element:
                            title = link_element.get_text().strip()
                            url = link_element.get("href", "")

                            snippet_element = element.find("p")
                            snippet = (
                                snippet_element.get_text().strip()
                                if snippet_element
                                else ""
                            )

                            if url and title:
                                results.append(
                                    {
                                        "title": title,
                                        "url": url,
                                        "snippet": snippet,
                                        "source": "bing",
                                    }
                                )
                except Exception as e:
                    logger.debug(f"Error parsing Bing result element: {e}")
                    continue

            logger.info(f"Bing found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error parsing Bing results: {e}")
            return []


class GoogleAdapter(SearchEngineAdapter):
    """Google search adapter."""

    async def search(self, query: str) -> List[Dict]:
        """Search using Google."""
        try:
            url = f"https://www.google.com/search?q={query}"

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_google_results(html)
                    else:
                        logger.warning(
                            f"Google search failed with status {response.status}"
                        )
                        return []

        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []

    def _parse_google_results(self, html: str) -> List[Dict]:
        """Parse Google search results."""
        results = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            result_elements = soup.find_all("div", class_="g")

            for element in result_elements[:10]:  # Limit to top 10
                try:
                    title_element = element.find("h3")
                    if title_element:
                        link_element = element.find("a")
                        if link_element:
                            title = title_element.get_text().strip()
                            url = link_element.get("href", "")

                            snippet_elements = element.find_all("span")
                            snippet = ""
                            for span in snippet_elements:
                                text = span.get_text().strip()
                                if len(text) > 50:  # Likely the snippet
                                    snippet = text
                                    break

                            if url and title and url.startswith("http"):
                                results.append(
                                    {
                                        "title": title,
                                        "url": url,
                                        "snippet": snippet,
                                        "source": "google",
                                    }
                                )
                except Exception as e:
                    logger.debug(f"Error parsing Google result element: {e}")
                    continue

            logger.info(f"Google found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error parsing Google results: {e}")
            return []


class MultiEngineSearcher:
    """Coordinates searches across multiple search engines."""

    def __init__(self):
        self.adapters = {
            "duckduckgo": DuckDuckGoAdapter(),
            "bing": BingAdapter(),
            "google": GoogleAdapter(),
        }

    async def search(self, query: str, engines: List[str] = None) -> List[Dict]:
        """Search using multiple engines."""
        if engines is None:
            engines = ["duckduckgo", "bing"]  # Default engines

        all_results = []
        tasks = []

        for engine in engines:
            if engine in self.adapters:
                tasks.append(self.adapters[engine].search(query))

        if tasks:
            results_list = await asyncio.gather(*tasks, return_exceptions=True)

            for results in results_list:
                if isinstance(results, list):
                    all_results.extend(results)
                else:
                    logger.warning(f"Search engine returned error: {results}")

        # Deduplicate results
        return self._deduplicate_results(all_results)

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on URL."""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results
