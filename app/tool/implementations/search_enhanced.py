"""
Enhanced Unified Search Tool with Intelligent Scraping
Integrates IntelligentScraper for advanced content fetching and fallback strategies.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from app.logger import logger
from app.search.intelligent_scraper import IntelligentScraper
from app.tool.core import BaseTool, ToolConfig, ToolResult


class EnhancedUnifiedSearchTool(BaseTool):
    """
    Enhanced unified search tool with intelligent scraping capabilities.

    Features:
    - IntelligentScraper integration for advanced content fetching
    - Multi-strategy scraping with fallback mechanisms
    - Stealth mode for anti-bot detection bypass
    - Concurrent URL processing
    """

    # Search and scraping components
    intelligent_scraper: Optional[IntelligentScraper] = Field(
        default=None, description="Intelligent scraper for advanced content fetching"
    )

    # Engine status tracking
    engine_status: Dict[str, Any] = Field(
        default_factory=dict, description="Engine availability status"
    )

    def __init__(self, **kwargs):
        # Set default configuration
        default_config = ToolConfig(
            name="enhanced_search",
            description="Advanced search tool with intelligent scraping and stealth capabilities",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "search_type": {
                        "type": "string",
                        "description": "Type of search to perform",
                        "enum": ["web", "news", "academic", "research"],
                        "default": "web",
                    },
                    "fetch_content": {
                        "type": "boolean",
                        "description": "Whether to fetch full content from results using intelligent scraping",
                        "default": True,
                    },
                    "stealth_mode": {
                        "type": "boolean",
                        "description": "Use stealth mode for content fetching",
                        "default": True,
                    },
                    "urls": {
                        "type": "array",
                        "description": "Specific URLs to scrape (alternative to search)",
                        "items": {"type": "string"},
                    },
                },
                "required": ["query"],
            },
            llm_enabled=True,
            llm_reasoning=True,
            cache_enabled=True,
            cache_ttl=300,  # 5 minutes
            timeout=60.0,  # Increased for intelligent scraping
            retries=2,
        )

        if "config" not in kwargs:
            kwargs["config"] = default_config

        super().__init__(**kwargs)

        # Initialize intelligent scraper with LLM
        from app.llm.core import LLM

        try:
            llm = LLM()
            self.intelligent_scraper = IntelligentScraper(llm=llm)
            logger.info("🧠 Initialized enhanced search with intelligent scraping")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize LLM for intelligent scraping: {e}")
            self.intelligent_scraper = IntelligentScraper()

    @property
    def name(self) -> str:
        """Get tool name for compatibility."""
        return self.config.name

    async def _execute(self, **kwargs) -> ToolResult:
        """Execute search with intelligent scraping capabilities."""
        try:
            query = kwargs.get("query", "")
            urls = kwargs.get("urls", [])
            fetch_content = kwargs.get("fetch_content", True)
            num_results = kwargs.get("num_results", 5)
            stealth_mode = kwargs.get("stealth_mode", True)
            search_type = kwargs.get("search_type", "web")

            # If specific URLs provided, scrape them directly
            if urls:
                return await self._scrape_urls(urls, query, stealth_mode)

            # Otherwise, perform search then scrape results
            return await self._search_and_scrape(
                query, num_results, fetch_content, stealth_mode, search_type
            )

        except Exception as e:
            logger.error(f"❌ Enhanced search failed: {e}")
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}",
                data={"error_type": type(e).__name__},
            )

    async def _scrape_urls(
        self, urls: List[str], context: str = "", stealth_mode: bool = True
    ) -> ToolResult:
        """Scrape specific URLs using intelligent scraper."""
        try:
            logger.info(f"🔍 Scraping {len(urls)} URLs with intelligent scraper")

            # Use intelligent scraper for concurrent processing
            results = await self.intelligent_scraper.scrape_multiple_urls(urls, context)

            # Process results
            scraped_content = []
            successful_scrapes = 0

            for url, content in results.items():
                if content:
                    scraped_content.append(
                        {
                            "url": url,
                            "content": content,
                            "content_length": len(content),
                            "status": "success",
                        }
                    )
                    successful_scrapes += 1
                else:
                    scraped_content.append(
                        {"url": url, "content": None, "status": "failed"}
                    )

            return ToolResult(
                success=successful_scrapes > 0,
                data={
                    "results": scraped_content,
                    "total_urls": len(urls),
                    "successful_scrapes": successful_scrapes,
                    "context": context,
                },
                metadata={
                    "scraping_method": "intelligent_multi_strategy",
                    "stealth_mode": stealth_mode,
                    "timestamp": time.time(),
                },
            )

        except Exception as e:
            logger.error(f"❌ URL scraping failed: {e}")
            return ToolResult(
                success=False,
                error=f"URL scraping failed: {str(e)}",
                data={"urls": urls, "error_type": type(e).__name__},
            )

    async def _search_and_scrape(
        self,
        query: str,
        num_results: int,
        fetch_content: bool,
        stealth_mode: bool,
        search_type: str,
    ) -> ToolResult:
        """Perform search and optionally scrape results."""
        try:
            # For now, simulate search results (integrate with actual search engines later)
            search_results = await self._simulate_search(
                query, num_results, search_type
            )

            if not fetch_content:
                return ToolResult(
                    success=True,
                    data={
                        "query": query,
                        "results": search_results,
                        "content_fetched": False,
                    },
                    metadata={"search_type": search_type},
                )

            # Extract URLs for scraping
            urls = [result.get("url") for result in search_results if result.get("url")]

            if not urls:
                return ToolResult(
                    success=False,
                    error="No URLs found in search results",
                    data={"query": query, "search_results": search_results},
                )

            # Scrape content from search result URLs
            scraping_result = await self._scrape_urls(urls, query, stealth_mode)

            if scraping_result.success:
                # Combine search results with scraped content
                enhanced_results = []
                scraped_data = {
                    item["url"]: item for item in scraping_result.data["results"]
                }

                for result in search_results:
                    url = result.get("url")
                    if url in scraped_data:
                        result["scraped_content"] = scraped_data[url]["content"]
                        result["content_length"] = scraped_data[url].get(
                            "content_length", 0
                        )
                        result["scraping_status"] = scraped_data[url]["status"]
                    enhanced_results.append(result)

                return ToolResult(
                    success=True,
                    data={
                        "query": query,
                        "results": enhanced_results,
                        "content_fetched": True,
                        "scraping_stats": {
                            "total_urls": scraping_result.data["total_urls"],
                            "successful_scrapes": scraping_result.data[
                                "successful_scrapes"
                            ],
                        },
                    },
                    metadata={
                        "search_type": search_type,
                        "intelligent_scraping": True,
                        "stealth_mode": stealth_mode,
                        "timestamp": time.time(),
                    },
                )
            else:
                return ToolResult(
                    success=True,
                    data={
                        "query": query,
                        "results": search_results,
                        "content_fetched": False,
                        "scraping_error": scraping_result.error,
                    },
                    metadata={"search_type": search_type},
                )

        except Exception as e:
            logger.error(f"❌ Search and scrape failed: {e}")
            return ToolResult(
                success=False,
                error=f"Search and scrape failed: {str(e)}",
                data={"query": query, "error_type": type(e).__name__},
            )

    async def _simulate_search(
        self, query: str, num_results: int, search_type: str
    ) -> List[Dict]:
        """Simulate search results (to be replaced with actual search engine integration)."""
        # This is a placeholder - integrate with actual search engines later
        simulated_results = []

        for i in range(min(num_results, 3)):  # Limit for demo
            simulated_results.append(
                {
                    "title": f"Search result {i+1} for: {query}",
                    "url": f"https://example.com/result-{i+1}",
                    "snippet": f"This is a simulated search result snippet for {query}",
                    "search_type": search_type,
                }
            )

        return simulated_results

    def get_stats(self) -> Dict:
        """Get statistics about search and scraping operations."""
        stats = {
            "tool_type": "enhanced_search",
            "intelligent_scraping": self.intelligent_scraper is not None,
        }

        if self.intelligent_scraper:
            stats.update(self.intelligent_scraper.get_scraping_stats())

        return stats

    async def cleanup(self):
        """Cleanup search tool resources."""
        logger.debug("🧹 Cleaning up enhanced search tool")


# Keep the UnifiedSearchTool name for backward compatibility
UnifiedSearchTool = EnhancedUnifiedSearchTool
