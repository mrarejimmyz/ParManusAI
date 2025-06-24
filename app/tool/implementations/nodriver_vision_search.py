"""
Free NoDriver + Vision Search Tool
Uses NoDriver browser automation with LLM vision to parse search results
Completely free alternative that leverages existing capabilities
"""

import asyncio
import base64
import os
import random
import time
from typing import Any, Dict, List, Optional

import nodriver as uc

from app.logger import logger
from app.tool.core.base import BaseTool, ToolConfig, ToolResult


class NoDriverVisionSearchTool(BaseTool):
    """Free search tool using NoDriver + LLM Vision to parse results."""

    def __init__(self, **kwargs):
        default_config = ToolConfig(
            name="nodriver_vision_search",
            description="Free web search using NoDriver browser + LLM vision parsing",
            llm_enabled=True,  # Enable LLM for vision capabilities
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to extract",
                        "default": 10,
                    },
                    "search_engine": {
                        "type": "string",
                        "description": "Search engine to use",
                        "default": "duckduckgo",
                        "enum": ["duckduckgo", "bing", "startpage"],
                    },
                    "stealth_level": {
                        "type": "string",
                        "description": "Stealth level",
                        "default": "high",
                        "enum": ["low", "medium", "high", "maximum"],
                    },                },
                "required": ["query"],
            },
        )

        super().__init__(config=default_config, **kwargs)

    async def _execute(
        self,
        query: str,
        num_results: int = 10,
        search_engine: str = "duckduckgo",
        stealth_level: str = "high",
    ) -> ToolResult:
        """Execute search using NoDriver + Vision."""

        logger.info(f"🔍 NoDriver Vision Search: '{query}' on {search_engine}")

        try:
            # Try the primary search engine
            results = await self._search_with_vision(query, num_results, search_engine, stealth_level)

            if not results and search_engine != "bing":
                logger.info("🔄 Primary search failed, trying Bing as fallback")
                results = await self._search_with_vision(query, num_results, "bing", stealth_level)

            if not results and search_engine != "startpage":
                logger.info("🔄 Trying StartPage as final fallback")
                results = await self._search_with_vision(query, num_results, "startpage", stealth_level)

            if results:
                logger.info(f"✅ NoDriver Vision Search successful: {len(results)} results")
                return ToolResult(
                    success=True,
                    content={
                        "query": query,
                        "results": results,
                        "total_results": len(results),
                        "search_engine": search_engine,
                        "method": "nodriver_vision",
                        "timestamp": self._get_timestamp(),
                        "cost": "FREE"
                    }
                )
            else:
                logger.warning("❌ All NoDriver vision searches failed")
                return ToolResult(
                    success=False,
                    content={
                        "query": query,
                        "results": [],
                        "error": "NoDriver vision parsing failed on all search engines",
                        "recommendation": "Check network connectivity and search engine availability"
                    }
                )

        except Exception as e:
            logger.error(f"❌ NoDriver Vision Search failed: {e}")
            return ToolResult(
                success=False,
                content={
                    "query": query,
                    "results": [],
                    "error": str(e),
                    "method": "nodriver_vision"
                }
            )

    async def _search_with_vision(
        self, query: str, num_results: int, search_engine: str, stealth_level: str
    ) -> List[Dict]:
        """Perform search using NoDriver + Vision parsing."""

        browser = None
        try:
            # Configure browser with maximum stealth
            browser_config = self._get_stealth_config(stealth_level)

            logger.info(f"🚀 Starting stealth browser for {search_engine}")
            browser = await uc.start(**browser_config)

            # Navigate to search engine
            search_url = self._get_search_url(search_engine, query)
            logger.info(f"🔍 Navigating to: {search_url}")

            page = await browser.get(search_url)

            # Random human-like delay
            await asyncio.sleep(random.uniform(2.0, 4.0))

            # Wait for page to fully load
            await self._wait_for_page_load(page)            # Take screenshot for vision analysis
            logger.info("📸 Taking screenshot for vision analysis")
            # NoDriver screenshot method - get as bytes directly
            screenshot_path = "temp_screenshot.png"
            await page.save_screenshot(screenshot_path)

            # Read screenshot as bytes
            with open(screenshot_path, "rb") as f:
                screenshot = f.read()

            # Clean up temp file
            import os
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)

            # Convert screenshot to base64
            screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')

            # Use LLM vision to parse search results
            logger.info("👁️ Using LLM vision to parse search results")
            results = await self._parse_results_with_vision(
                screenshot_b64, query, num_results, search_engine
            )

            # Verify results and get page content for snippets if needed
            if results:
                results = await self._enhance_results_with_content(page, results[:num_results])

            return results

        except Exception as e:
            logger.error(f"❌ Error in vision search for {search_engine}: {e}")
            return []

        finally:
            if browser:
                try:
                    await browser.stop()
                except:
                    pass

    def _get_stealth_config(self, stealth_level: str) -> Dict:
        """Get browser configuration for maximum stealth."""

        base_config = {
            "headless": True,
            "user_data_dir": None,  # Don't persist data
        }

        if stealth_level == "maximum":
            # Maximum stealth configuration
            return {
                **base_config,
                "headless": False,  # Visible browser is less suspicious
                "user_data_dir": f"/tmp/nodriver_profile_{random.randint(1000, 9999)}",
                "browser_args": [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu',
                    f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ]
            }
        elif stealth_level == "high":
            return {
                **base_config,
                "browser_args": [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                ]
            }
        else:
            return base_config

    def _get_search_url(self, search_engine: str, query: str) -> str:
        """Get search URL for different engines."""

        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)

        urls = {
            "duckduckgo": f"https://duckduckgo.com/?q={encoded_query}",
            "bing": f"https://www.bing.com/search?q={encoded_query}",
            "startpage": f"https://www.startpage.com/search?query={encoded_query}",
        }

        return urls.get(search_engine, urls["duckduckgo"])

    async def _wait_for_page_load(self, page) -> None:
        """Wait for page to fully load."""
        try:
            # Wait for basic elements to load
            await asyncio.sleep(3)

            # Execute JavaScript to check if page is fully loaded
            await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        if (document.readyState === 'complete') {
                            resolve();
                        } else {
                            window.addEventListener('load', resolve);
                        }
                    });
                }
            """)

            # Additional wait for dynamic content
            await asyncio.sleep(2)

        except Exception as e:
            logger.warning(f"⚠️ Page load wait failed: {e}")
            await asyncio.sleep(5)  # Fallback wait

    async def _parse_results_with_vision(
        self, screenshot_b64: str, query: str, num_results: int, search_engine: str
    ) -> List[Dict]:
        """Use LLM vision to parse search results from screenshot."""

        try:
            vision_prompt = f"""
Analyze this screenshot of search results for the query: "{query}"

Extract up to {num_results} search results from the image. For each result, identify:
1. Title (the main clickable headline)
2. URL (the green/blue link URL, may be shortened)
3. Snippet (the description text below the title)
4. Position (result number)

Return the results in this exact JSON format:
{{
    "results": [
        {{
            "title": "exact title text",
            "url": "exact URL or domain",
            "snippet": "exact description text",
            "position": 1
        }}
    ]
}}

Search engine: {search_engine}
Focus on the main organic search results, ignore ads and special boxes.
Extract text exactly as shown, don't modify or interpret.
"""            # Use the LLM with vision capability
            try:
                logger.info(f"🔍 LLM instance: {type(self.llm)}")
                logger.info(f"👁️ Has ask_vision: {hasattr(self.llm, 'ask_vision')}")
                logger.info(f"🔧 Has vision_enabled: {hasattr(self.llm, 'vision_enabled')}")

                if hasattr(self.llm, 'vision_enabled'):
                    logger.info(f"✅ Vision enabled: {self.llm.vision_enabled}")
                else:
                    logger.warning("⚠️ No vision_enabled attribute")

                if hasattr(self.llm, 'ask_vision') and hasattr(self.llm, 'vision_enabled') and self.llm.vision_enabled:
                    # Format as messages for the vision API
                    messages = [
                        {
                            "role": "user",
                            "content": vision_prompt
                        }
                    ]

                    # Convert base64 to data URL format
                    image_url = f"data:image/png;base64,{screenshot_b64}"

                    logger.info("🚀 Calling LLM vision API...")
                    response = await self.llm.ask_vision(
                        messages=messages,
                        images=[image_url]
                    )
                    logger.info("✅ LLM vision call successful")
                else:
                    logger.warning("⚠️ LLM vision not available or not enabled, using text fallback")
                    return []
            except Exception as e:
                logger.error(f"❌ LLM vision failed: {e}, using text fallback")
                return []

            # Parse the JSON response
            import json
            try:
                parsed_response = json.loads(response)
                results = parsed_response.get("results", [])

                # Clean and validate results
                cleaned_results = []
                for result in results:
                    if isinstance(result, dict) and result.get("title"):
                        cleaned_result = {
                            "title": str(result.get("title", "")).strip(),
                            "url": str(result.get("url", "")).strip(),
                            "snippet": str(result.get("snippet", "")).strip(),
                            "position": result.get("position", len(cleaned_results) + 1),
                            "source": f"vision_parsed_{search_engine}"
                        }
                        cleaned_results.append(cleaned_result)

                logger.info(f"👁️ Vision extracted {len(cleaned_results)} results")
                return cleaned_results

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse vision response as JSON: {e}")
                # Try to extract results from plain text response
                return self._extract_results_from_text(response, num_results)

        except Exception as e:
            logger.error(f"❌ Vision parsing failed: {e}")
            return []

    def _extract_results_from_text(self, text_response: str, num_results: int) -> List[Dict]:
        """Extract results from plain text response as fallback."""

        import re
        results = []

        # Try to find structured patterns in the text
        lines = text_response.split('\n')
        current_result = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for title patterns
            if line.startswith(('Title:', 'title:', '1.', '2.', '3.', '4.', '5.')):
                if current_result and current_result.get('title'):
                    results.append(current_result)
                    current_result = {}
                current_result['title'] = re.sub(r'^(Title:|title:|\d+\.)\s*', '', line)

            # Look for URL patterns
            elif line.startswith(('URL:', 'url:', 'Link:')) or 'http' in line:
                current_result['url'] = re.sub(r'^(URL:|url:|Link:)\s*', '', line)

            # Look for snippet patterns
            elif line.startswith(('Snippet:', 'snippet:', 'Description:')):
                current_result['snippet'] = re.sub(r'^(Snippet:|snippet:|Description:)\s*', '', line)

        # Add the last result
        if current_result and current_result.get('title'):
            results.append(current_result)

        # Clean up and add missing fields
        for i, result in enumerate(results):
            result['position'] = i + 1
            result['source'] = 'text_parsed'
            if not result.get('url'):
                result['url'] = ''
            if not result.get('snippet'):
                result['snippet'] = ''

        return results[:num_results]

    async def _enhance_results_with_content(self, page, results: List[Dict]) -> List[Dict]:
        """Enhance results by getting actual page content for better snippets."""

        try:
            # Get page content
            content = await page.get_content()

            # Use basic text extraction for now
            # In a full implementation, you could use the LLM to extract better snippets

            for result in results:
                if not result.get('snippet') or len(result['snippet']) < 50:
                    # Try to find better snippet from page content
                    title = result.get('title', '').lower()
                    if title:
                        # Simple snippet extraction based on title proximity
                        import re
                        pattern = re.compile(f'.{0,100}{re.escape(title)}.{0,200}', re.IGNORECASE)
                        match = pattern.search(content)
                        if match:
                            snippet = match.group(0).strip()
                            # Clean up HTML and extra whitespace
                            snippet = re.sub(r'<[^>]+>', '', snippet)
                            snippet = re.sub(r'\s+', ' ', snippet)
                            if len(snippet) > 50:
                                result['snippet'] = snippet[:300] + "..."

            return results

        except Exception as e:
            logger.warning(f"⚠️ Content enhancement failed: {e}")
            return results

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


# Register the tool
__all__ = ["NoDriverVisionSearchTool"]
