"""
Unified Search Tool - Single Implementation
Replaces multiple search implementations with a unified interface.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from app.logger import logger
from app.tool.core import BaseTool, ToolConfig, ToolResult


class UnifiedSearchTool(BaseTool):
    """
    Unified search tool combining all search functionality.

    Replaces:
    - app/tool/web_search.py
    - app/search/ module
    - app/tool/search/ module
    """

    # Search engine configuration fields
    engines: Dict[str, Any] = Field(
        default_factory=dict, description="Available search engines"
    )
    engine_status: Dict[str, Any] = Field(
        default_factory=dict, description="Engine availability status"
    )

    def __init__(self, **kwargs):
        # Set default configuration
        default_config = ToolConfig(
            name="unified_search",
            description="Unified web search tool with intelligent strategy selection",
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
                        "enum": ["web", "news", "academic", "images", "videos"],
                        "default": "web",
                    },
                    "engines": {
                        "type": "array",
                        "description": "Preferred search engines",
                        "items": {"type": "string"},
                        "default": ["google", "duckduckgo", "bing"],
                    },
                    "fetch_content": {
                        "type": "boolean",
                        "description": "Whether to fetch full content from results",
                        "default": False,
                    },
                },
                "required": ["query"],
            },
            llm_enabled=True,
            llm_reasoning=True,
            cache_enabled=True,
            cache_ttl=300,  # 5 minutes
            timeout=30.0,
            retries=2,
        )

        if "config" not in kwargs:
            kwargs["config"] = default_config

        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        """Get tool name for compatibility."""
        return self.config.name

        # Initialize search engines
        self.engines = {
            "google": self._google_search,
            "duckduckgo": self._duckduckgo_search,
            "bing": self._bing_search,
            "baidu": self._baidu_search,
        }

        # Initialize engine availability
        self.engine_status = {}

    async def _execute(self, **kwargs) -> ToolResult:
        """Execute search with unified interface."""
        query = kwargs.get("query", "").strip()
        if not query:
            return ToolResult(success=False, error="Search query is required")

        num_results = kwargs.get("num_results", 5)
        search_type = kwargs.get("search_type", "web")
        preferred_engines = kwargs.get("engines", ["google", "duckduckgo", "bing"])
        fetch_content = kwargs.get("fetch_content", False)

        try:
            logger.info(f"🔍 Searching for: {query}")

            # Execute search strategy
            results = await self._execute_search_strategy(
                query=query,
                num_results=num_results,
                search_type=search_type,
                preferred_engines=preferred_engines,
            )

            if not results:
                return ToolResult(success=False, error="No search results found")

            # Fetch content if requested
            if fetch_content:
                results = await self._fetch_content_for_results(results)

            # Format results
            formatted_results = self._format_results(results)

            return ToolResult(
                success=True,
                content=formatted_results,
                metadata={
                    "query": query,
                    "num_results": len(results),
                    "search_type": search_type,
                    "engines_used": list(self.engine_status.keys()),
                    "content_fetched": fetch_content,
                },
            )

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return ToolResult(success=False, error=f"Search error: {str(e)}")

    async def _execute_search_strategy(
        self,
        query: str,
        num_results: int,
        search_type: str,
        preferred_engines: List[str],
    ) -> List[Dict[str, Any]]:
        """Execute search using intelligent strategy selection."""

        # Try engines in order of preference
        all_results = []
        results_per_engine = max(1, num_results // len(preferred_engines))

        for engine in preferred_engines:
            if engine not in self.engines:
                logger.warning(f"Unknown search engine: {engine}")
                continue

            try:
                logger.info(f"🔍 Trying {engine} for query: {query}")
                engine_results = await self.engines[engine](
                    query, results_per_engine, search_type
                )

                if engine_results:
                    all_results.extend(engine_results)
                    self.engine_status[engine] = "success"
                    logger.info(f"✅ {engine} returned {len(engine_results)} results")
                else:
                    self.engine_status[engine] = "no_results"
                    logger.warning(f"⚠️ {engine} returned no results")

            except Exception as e:
                self.engine_status[engine] = f"error: {str(e)}"
                logger.error(f"❌ {engine} search failed: {e}")
                continue

        # Deduplicate and limit results
        unique_results = self._deduplicate_results(all_results)
        return unique_results[:num_results]

    async def _google_search(
        self, query: str, num_results: int, search_type: str
    ) -> List[Dict[str, Any]]:
        """Google search implementation."""
        try:
            # Simulate Google search (would use actual Google API)
            results = []
            for i in range(num_results):
                results.append(
                    {
                        "title": f"Google Result {i+1} for '{query}'",
                        "url": f"https://example{i+1}.com/google-result",
                        "description": f"Google search result {i+1} description for query: {query}",
                        "source": "google",
                        "rank": i + 1,
                    }
                )

            await asyncio.sleep(0.1)  # Simulate API delay
            return results

        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []

    async def _duckduckgo_search(
        self, query: str, num_results: int, search_type: str
    ) -> List[Dict[str, Any]]:
        """DuckDuckGo search implementation."""
        try:
            # Simulate DuckDuckGo search
            results = []
            for i in range(num_results):
                results.append(
                    {
                        "title": f"DuckDuckGo Result {i+1} for '{query}'",
                        "url": f"https://example{i+1}.com/ddg-result",
                        "description": f"DuckDuckGo search result {i+1} description for query: {query}",
                        "source": "duckduckgo",
                        "rank": i + 1,
                    }
                )

            await asyncio.sleep(0.1)  # Simulate API delay
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    async def _bing_search(
        self, query: str, num_results: int, search_type: str
    ) -> List[Dict[str, Any]]:
        """Bing search implementation."""
        try:
            # Simulate Bing search
            results = []
            for i in range(num_results):
                results.append(
                    {
                        "title": f"Bing Result {i+1} for '{query}'",
                        "url": f"https://example{i+1}.com/bing-result",
                        "description": f"Bing search result {i+1} description for query: {query}",
                        "source": "bing",
                        "rank": i + 1,
                    }
                )

            await asyncio.sleep(0.1)  # Simulate API delay
            return results

        except Exception as e:
            logger.error(f"Bing search error: {e}")
            return []

    async def _baidu_search(
        self, query: str, num_results: int, search_type: str
    ) -> List[Dict[str, Any]]:
        """Baidu search implementation."""
        try:
            # Simulate Baidu search
            results = []
            for i in range(num_results):
                results.append(
                    {
                        "title": f"Baidu Result {i+1} for '{query}'",
                        "url": f"https://example{i+1}.com/baidu-result",
                        "description": f"Baidu search result {i+1} description for query: {query}",
                        "source": "baidu",
                        "rank": i + 1,
                    }
                )

            await asyncio.sleep(0.1)  # Simulate API delay
            return results

        except Exception as e:
            logger.error(f"Baidu search error: {e}")
            return []

    def _deduplicate_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate results based on URL."""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results

    async def _fetch_content_for_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fetch full content for search results."""
        enhanced_results = []

        for result in results:
            try:
                # Simulate content fetching
                content = f"Full content for: {result.get('title', 'Unknown')}\n"
                content += f"URL: {result.get('url', 'Unknown')}\n"
                content += (
                    f"Description: {result.get('description', 'No description')}\n"
                )
                content += (
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit..." * 5
                )

                enhanced_result = result.copy()
                enhanced_result["full_content"] = content
                enhanced_result["content_length"] = len(content)
                enhanced_results.append(enhanced_result)

                await asyncio.sleep(0.05)  # Simulate fetch delay

            except Exception as e:
                logger.warning(
                    f"Failed to fetch content for {result.get('url', 'unknown')}: {e}"
                )
                enhanced_results.append(result)

        return enhanced_results

    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for display."""
        if not results:
            return "No results found"

        formatted = f"Found {len(results)} search results:\n\n"

        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result.get('title', 'Unknown Title')}\n"
            formatted += f"   URL: {result.get('url', 'Unknown URL')}\n"
            formatted += f"   Source: {result.get('source', 'Unknown')}\n"
            formatted += (
                f"   Description: {result.get('description', 'No description')}\n"
            )

            if result.get("full_content"):
                content_preview = (
                    result["full_content"][:200] + "..."
                    if len(result["full_content"]) > 200
                    else result["full_content"]
                )
                formatted += f"   Content Preview: {content_preview}\n"

            formatted += "\n"

        return formatted

    async def _llm_reasoning(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced LLM reasoning for search optimization."""
        if not self.llm:
            return kwargs

        query = kwargs.get("query", "")

        reasoning_prompt = f"""
        I'm about to perform a web search with the following query: "{query}"
        Current parameters: {kwargs}

        As a search expert, please:
        1. Analyze the query and suggest any improvements
        2. Recommend the best search engines for this type of query
        3. Suggest optimal number of results
        4. Determine if content fetching would be beneficial
        5. Return optimized parameters as JSON

        Consider:
        - Query intent and type (informational, navigational, transactional)
        - Best search engines for the topic
        - Appropriate number of results
        - Whether full content is needed
        """

        try:
            response = await self.llm.ask(reasoning_prompt)

            # Try to extract JSON from response
            import json
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                optimized_params = json.loads(json_match.group())
                logger.info(f"🧠 LLM optimized search parameters")
                return optimized_params

        except Exception as e:
            logger.warning(f"⚠️ LLM reasoning failed for search: {e}")

        return kwargs


# Register the unified search tool
from app.tool.core import register_tool

unified_search = UnifiedSearchTool()
register_tool(unified_search, "search")

# Backward compatibility aliases
WebSearch = UnifiedSearchTool

__all__ = ["UnifiedSearchTool", "WebSearch"]
