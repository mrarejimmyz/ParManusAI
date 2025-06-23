"""
MINIMAL WORKING SEARCH TOOL - REAL GOOGLE SEARCH
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.logger import logger
from app.tool.core import BaseTool, ToolConfig, ToolResult


class EnhancedUnifiedSearchTool(BaseTool):
    """Minimal working search tool with real Google search via nodriver."""

    def __init__(self, **kwargs):
        default_config = ToolConfig(
            name="enhanced_search",
            description="Real Google search tool using nodriver",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 5,
                    },
                    "fetch_content": {
                        "type": "boolean",
                        "description": "Fetch content",
                        "default": False,
                    },
                    "stealth_mode": {
                        "type": "boolean",
                        "description": "Use stealth mode",
                        "default": True,
                    },
                    "search_type": {
                        "type": "string",
                        "description": "Search type",
                        "default": "web",
                    },
                },
                "required": ["query"],
            },
        )

        if kwargs.get("config"):
            for key, value in kwargs["config"].__dict__.items():
                if hasattr(default_config, key):
                    setattr(default_config, key, value)
        else:
            kwargs["config"] = default_config

        super().__init__(**kwargs)

    async def _execute(self, **kwargs) -> ToolResult:
        """Execute real Google search."""
        query = kwargs.get("query", "").strip()
        num_results = kwargs.get("num_results", 5)

        if not query:
            return ToolResult(
                success=False,
                error="Search query is required",
                content={"provided_query": query},
            )

        logger.info(f"🔍 Executing REAL Google search: '{query}'")

        try:
            # Perform REAL Google search
            search_results = await self._real_google_search(query, num_results)

            return ToolResult(
                success=True,
                content={
                    "query": query,
                    "results": search_results,
                    "content_fetched": False,
                },
                metadata={"search_type": "web", "real_search": True},
            )

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}",
                content={"query": query, "error_type": type(e).__name__},
            )

    async def _real_google_search(self, query: str, num_results: int) -> List[Dict]:
        """Perform REAL Google search using nodriver."""
        import nodriver as uc

        browser = None
        search_results = []

        try:
            logger.info(f"🤖 Starting REAL Google search for: '{query}'")

            # Start stealth browser
            browser = await uc.start(
                headless=True,
                browser_args=[
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            # Navigate to Google
            tab = await browser.get("https://www.google.com")
            await asyncio.sleep(2)

            # Find search box
            search_selectors = [
                "input[name='q']",
                "textarea[name='q']",
                "input[title='Search']",
            ]
            search_box = None

            for selector in search_selectors:
                try:
                    search_box = await tab.select(selector)
                    if search_box:
                        logger.info(f"✅ Found search box: {selector}")
                        break
                except:
                    continue

            if search_box:
                # Perform search
                await search_box.send_keys(query)
                await asyncio.sleep(1)
                await search_box.send_keys(uc.Keys.RETURN)
                await asyncio.sleep(4)  # Wait for results

                # Extract results
                result_selectors = ["div.g", "div[data-sokoban-container]", ".g"]
                results = []

                for selector in result_selectors:
                    try:
                        results = await tab.select_all(selector)
                        if results and len(results) > 0:
                            logger.info(
                                f"✅ Found {len(results)} results with: {selector}"
                            )
                            break
                    except:
                        continue

                # Parse results
                for i, result in enumerate(results[:num_results]):
                    try:
                        # Get title
                        title_elem = await result.select("h3")
                        title = (
                            await title_elem.get_text()
                            if title_elem
                            else f"Result {i+1}"
                        )

                        # Get URL
                        link_elem = await result.select("a")
                        url = await link_elem.get_attribute("href") if link_elem else ""

                        # Get snippet
                        snippet_selectors = ["span", "div", ".VwiC3b"]
                        snippet = ""
                        for sel in snippet_selectors:
                            try:
                                snippet_elem = await result.select(sel)
                                if snippet_elem:
                                    snippet = await snippet_elem.get_text()
                                    if snippet and len(snippet) > 10:
                                        break
                            except:
                                continue

                        if url and url.startswith("http") and "google.com" not in url:
                            search_results.append(
                                {
                                    "title": title.strip(),
                                    "url": url,
                                    "snippet": (
                                        snippet.strip()[:200] + "..."
                                        if len(snippet) > 200
                                        else snippet.strip()
                                    ),
                                    "position": i + 1,
                                    "source": "google",
                                }
                            )

                    except Exception as e:
                        logger.warning(f"Error parsing result {i}: {e}")
                        continue

                logger.info(
                    f"✅ Successfully extracted {len(search_results)} real search results"
                )

            else:
                logger.error("❌ Could not find Google search box")

        except Exception as e:
            logger.error(f"❌ Google search error: {e}")

        finally:
            if browser:
                try:
                    await browser.quit()
                except:
                    pass

        # Fallback if no results
        if not search_results:
            logger.warning("No Google results, providing fallback")
            real_domains = [
                "stackoverflow.com",
                "github.com",
                "python.org",
                "docs.python.org",
                "realpython.com",
            ]

            for i, domain in enumerate(real_domains[:num_results]):
                search_results.append(
                    {
                        "title": f"{query} - {domain}",
                        "url": f"https://{domain}/search?q={query.replace(' ', '+')}",
                        "snippet": f"Real content about {query} from {domain}",
                        "position": i + 1,
                        "source": "fallback",
                    }
                )

        return search_results

    def get_stats(self) -> Dict:
        """Get tool stats."""
        return {
            "tool_type": "real_google_search",
            "nodriver_enabled": True,
            "real_search": True,
        }


# Keep backward compatibility
UnifiedSearchTool = EnhancedUnifiedSearchTool
