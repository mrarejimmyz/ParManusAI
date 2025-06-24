"""
SerperDev Search Tool - Working Alternative to DuckDuckGo
Provides real-time search results through Serper.dev API
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

import aiohttp

from app.logger import logger
from app.tool.core.base import BaseTool, ToolConfig, ToolResult


class SerperSearchTool(BaseTool):
    """Real-time search tool using Serper.dev API."""

    def __init__(self, **kwargs):
        default_config = ToolConfig(
            name="serper_search",
            description="Real-time web search using Serper.dev API (reliable alternative)",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 10,
                    },
                    "search_type": {
                        "type": "string",
                        "description": "Type of search",
                        "default": "search",
                        "enum": ["search", "news", "images", "videos"],
                    },
                    "country": {
                        "type": "string",
                        "description": "Country code for localized results",
                        "default": "us"
                    },
                },
                "required": ["query"],
            },
        )

        if kwargs.get("config"):
            default_config = kwargs["config"]

        super().__init__(config=default_config, **kwargs)
        self.api_key = os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev"

    async def _execute(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search",
        country: str = "us",
    ) -> ToolResult:
        """Execute search using Serper.dev API."""

        if not self.api_key:
            logger.warning("⚠️ SERPER_API_KEY not set, using fallback search")
            return await self._fallback_search(query, num_results)

        try:
            logger.info(f"🔍 Serper.dev search: '{query}' (type: {search_type})")

            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": query,
                "num": min(num_results, 20),  # API limit
                "gl": country
            }

            # Use appropriate endpoint
            endpoint = f"/{search_type}"
            url = self.base_url + endpoint

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        formatted_results = self._format_serper_results(data, search_type)

                        logger.info(f"✅ Serper.dev returned {len(formatted_results)} results")

                        return ToolResult(
                            success=True,
                            content={
                                "query": query,
                                "results": formatted_results,
                                "total_results": len(formatted_results),
                                "search_type": search_type,
                                "source": "serper.dev",
                                "timestamp": self._get_timestamp()
                            }
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Serper.dev API error {response.status}: {error_text}")
                        return await self._fallback_search(query, num_results)

        except Exception as e:
            logger.error(f"❌ Serper.dev search failed: {e}")
            return await self._fallback_search(query, num_results)

    def _format_serper_results(self, data: Dict, search_type: str) -> List[Dict]:
        """Format Serper.dev API response into standard format."""
        results = []

        if search_type == "search":
            # Regular web search results
            organic_results = data.get("organic", [])
            for result in organic_results:
                formatted = {
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", 0),
                    "source": "serper.dev"
                }
                results.append(formatted)

        elif search_type == "news":
            # News search results
            news_results = data.get("news", [])
            for result in news_results:
                formatted = {
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "date": result.get("date", ""),
                    "source": result.get("source", ""),
                    "imageUrl": result.get("imageUrl", "")
                }
                results.append(formatted)

        # Add knowledge graph if available
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            knowledge_result = {
                "title": f"Knowledge Graph: {kg.get('title', '')}",
                "url": kg.get("website", ""),
                "snippet": kg.get("description", ""),
                "type": "knowledge_graph",
                "source": "serper.dev"
            }
            results.insert(0, knowledge_result)  # Put at top

        return results

    async def _fallback_search(self, query: str, num_results: int) -> ToolResult:
        """Fallback when Serper.dev is unavailable."""
        logger.warning("🔄 Using basic search fallback")

        # Try a simple requests-based search
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Try DuckDuckGo instant answers API
            ddg_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"

            response = requests.get(ddg_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()

                results = []
                if data.get("AbstractText"):
                    results.append({
                        "title": data.get("Heading", query),
                        "url": data.get("AbstractURL", ""),
                        "snippet": data.get("AbstractText", ""),
                        "source": "duckduckgo_api"
                    })

                # Add related topics if available
                for topic in data.get("RelatedTopics", [])[:num_results-1]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append({
                            "title": topic.get("Text", "").split(" - ")[0],
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", ""),
                            "source": "duckduckgo_api"
                        })

                if results:
                    logger.info(f"✅ DuckDuckGo API fallback: {len(results)} results")
                    return ToolResult(
                        success=True,
                        content={
                            "query": query,
                            "results": results,
                            "total_results": len(results),
                            "search_type": "fallback",
                            "source": "duckduckgo_api",
                            "timestamp": self._get_timestamp(),
                            "warning": "Limited results from fallback API"
                        }
                    )

        except Exception as e:
            logger.error(f"❌ Fallback search also failed: {e}")

        # Last resort - return empty with clear warning
        return ToolResult(
            success=False,
            content={
                "query": query,
                "results": [],
                "error": "All search methods failed - no real-time data available",
                "recommendation": "Set SERPER_API_KEY environment variable for reliable search",
                "warning": "Any generated content will be synthetic"
            }
        )

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


# Register the tool for easy import
__all__ = ["SerperSearchTool"]
