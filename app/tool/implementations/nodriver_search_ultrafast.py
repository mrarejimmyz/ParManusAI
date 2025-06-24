"""
Ultra-Fast NoDriver + Text Search Tool
Uses NoDriver browser automation with text-based parsing for maximum speed
Optimized for scenarios where speed is more important than vision accuracy
"""

import asyncio
import random
import time
from typing import Any, Dict, List, Optional
import re

import nodriver as uc

from app.logger import logger
from app.tool.core.base import BaseTool, ToolConfig, ToolResult


class UltraFastNoDriverSearchTool(BaseTool):
    """Ultra-fast search tool using NoDriver + text parsing (no vision)."""

    def __init__(self, **kwargs):
        default_config = ToolConfig(
            name="ultrafast_nodriver_search",
            description="Ultra-fast web search using NoDriver browser + text parsing",
            llm_enabled=False,  # No LLM needed for text parsing
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to extract",
                        "default": 5,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds",
                        "default": 15,
                    },
                },
                "required": ["query"],
            },
        )
        super().__init__(config=default_config, **kwargs)

    async def _execute(
        self,
        query: str,
        num_results: int = 5,
        timeout: int = 15,
    ) -> ToolResult:
        """Execute ultra-fast search using NoDriver + text parsing."""

        logger.info(f"⚡ Ultra-Fast NoDriver Search: '{query}' (timeout: {timeout}s)")
        start_time = time.time()

        try:
            # Use asyncio timeout for the entire operation
            results = await asyncio.wait_for(
                self._ultrafast_search_with_text(query, num_results),
                timeout=timeout
            )

            elapsed_time = time.time() - start_time

            if results:
                logger.info(f"✅ Ultra-fast search completed in {elapsed_time:.1f}s: {len(results)} results")
                return ToolResult(
                    success=True,
                    content={
                        "query": query,
                        "results": results,
                        "total_results": len(results),
                        "search_engine": "duckduckgo",
                        "method": "ultrafast_nodriver_text",
                        "timestamp": self._get_timestamp(),
                        "execution_time": f"{elapsed_time:.1f}s",
                        "cost": "FREE"
                    }
                )
            else:
                logger.warning(f"❌ Ultra-fast search failed in {elapsed_time:.1f}s")
                return ToolResult(
                    success=False,
                    content={
                        "query": query,
                        "results": [],
                        "error": "Ultra-fast text search failed to extract results",
                        "execution_time": f"{elapsed_time:.1f}s",
                        "recommendation": "Try with vision-based search or alternative method"
                    }
                )

        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            logger.warning(f"⏰ Ultra-fast search timed out after {elapsed_time:.1f}s")
            return ToolResult(
                success=False,
                content={
                    "query": query,
                    "results": [],
                    "error": f"Search timed out after {timeout}s",
                    "execution_time": f"{elapsed_time:.1f}s",
                    "recommendation": "Increase timeout or use alternative search method"
                }
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Ultra-fast search failed in {elapsed_time:.1f}s: {e}")
            return ToolResult(
                success=False,
                content={
                    "query": query,
                    "results": [],
                    "error": str(e),
                    "execution_time": f"{elapsed_time:.1f}s",
                    "method": "ultrafast_nodriver_text"
                }
            )

    async def _ultrafast_search_with_text(self, query: str, num_results: int) -> List[Dict]:
        """Perform ultra-fast search using minimal NoDriver + text parsing."""

        browser = None
        try:
            # Ultra-minimal browser config for maximum speed
            browser_config = {
                "headless": True,
                "user_data_dir": None,
                "browser_args": [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                    '--disable-javascript',
                    '--disable-web-security',
                    '--aggressive-cache-discard',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                ]
            }

            logger.info("⚡ Starting ultra-minimal browser")
            browser = await uc.start(**browser_config)

            # Navigate directly to DuckDuckGo
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://duckduckgo.com/?q={encoded_query}"

            logger.info(f"🔍 Ultra-fast navigation to DuckDuckGo")
            page = await browser.get(search_url)

            # Minimal wait - just enough for HTML content
            await asyncio.sleep(1.0)

            # Get page HTML content directly
            logger.info("📄 Extracting HTML content")
            html_content = await page.get_content()

            # Parse results from HTML using regex
            logger.info("⚡ Ultra-fast text parsing")
            results = self._extract_results_from_html(html_content, query, num_results)

            return results        except Exception as e:
            logger.error(f"❌ Ultra-fast search error: {e}")
            return []

        finally:
            if browser:
                try:
                    await browser.stop()
                    logger.info("🔚 Browser closed")
                except:
                    pass

    def _extract_results_from_html(self, html_content: str, query: str, num_results: int) -> List[Dict]:
        """Extract search results from HTML with CAPTCHA detection."""

        results = []

        try:
            # Check for CAPTCHA or bot detection
            if self._is_captcha_page(html_content):
                logger.warning("🚫 CAPTCHA detected - trying alternative approach")
                return self._fallback_alternative_search(query, num_results)

            # DuckDuckGo result patterns
            # Each result is in a div with class containing "result"
            result_pattern = re.compile(
                r'<div[^>]*class="[^"]*result[^"]*"[^>]*>.*?</div>',
                re.DOTALL | re.IGNORECASE
            )

            # Find all result divs
            result_divs = result_pattern.findall(html_content)

            logger.info(f"🔍 Found {len(result_divs)} potential result divs")

            for i, div_html in enumerate(result_divs[:num_results * 3]):  # Process more than needed
                try:
                    # Extract title (usually in <a> tag or h2/h3)
                    title_match = re.search(
                        r'<(?:a[^>]*|h[23][^>]*)>([^<]+)</(?:a|h[23])>',
                        div_html,
                        re.IGNORECASE
                    )
                    title = title_match.group(1).strip() if title_match else ""

                    # Extract URL (usually in href attribute)
                    url_match = re.search(
                        r'href="([^"]+)"',
                        div_html,
                        re.IGNORECASE
                    )
                    url = url_match.group(1).strip() if url_match else ""

                    # Clean up DuckDuckGo redirect URLs
                    if url.startswith('/'):
                        url = f"https://duckduckgo.com{url}"
                    elif url.startswith('//'):
                        url = f"https:{url}"

                    # Extract snippet (text content, cleaned of HTML)
                    snippet_text = re.sub(r'<[^>]+>', ' ', div_html)
                    snippet_text = re.sub(r'\s+', ' ', snippet_text).strip()

                    # Get a relevant snippet around the title
                    if title and len(title) > 3:
                        title_pos = snippet_text.lower().find(title.lower())
                        if title_pos >= 0:
                            start = max(0, title_pos - 50)
                            end = min(len(snippet_text), title_pos + len(title) + 200)
                            snippet = snippet_text[start:end].strip()
                        else:
                            snippet = snippet_text[:250].strip()
                    else:
                        snippet = snippet_text[:250].strip()

                    # Basic validation
                    if title and len(title) > 3 and not self._is_irrelevant_result(title, url):
                        result = {
                            "title": title[:200],
                            "url": url,
                            "snippet": snippet,
                            "position": len(results) + 1,
                            "source": "ultrafast_html_ddg"
                        }
                        results.append(result)

                        if len(results) >= num_results:
                            break

                except Exception as e:
                    logger.debug(f"⚠️ Failed to parse result {i}: {e}")
                    continue

            # Fallback: simple text extraction if regex fails
            if not results:
                logger.info("🔄 Trying fallback text extraction")
                results = self._fallback_text_extraction(html_content, num_results)

            logger.info(f"✅ Extracted {len(results)} results from HTML")
            return results

        except Exception as e:
            logger.error(f"❌ HTML parsing failed: {e}")
            return []

    def _is_irrelevant_result(self, title: str, url: str) -> bool:
        """Filter out irrelevant results."""

        title_lower = title.lower()
        url_lower = url.lower()

        # Skip obvious non-results
        irrelevant_patterns = [
            'duckduckgo',
            'search',
            'privacy',
            'about us',
            'contact',
            'terms',
            'cookies',
            'settings'
        ]

        for pattern in irrelevant_patterns:
            if pattern in title_lower or pattern in url_lower:
                return True

        return False

    def _fallback_text_extraction(self, html_content: str, num_results: int) -> List[Dict]:
        """Fallback text extraction method."""

        results = []

        try:
            # Remove HTML tags
            text_content = re.sub(r'<[^>]+>', ' ', html_content)
            text_content = re.sub(r'\s+', ' ', text_content)

            # Look for URL patterns
            urls = re.findall(r'https?://[^\s<>"\']+', text_content)

            # Look for potential titles (capitalized phrases)
            titles = re.findall(r'[A-Z][^.!?]*[.!?]?', text_content)

            # Combine URLs and titles
            for i, (url, title) in enumerate(zip(urls[:num_results], titles[:num_results])):
                if len(title) > 10 and not self._is_irrelevant_result(title, url):
                    results.append({
                        "title": title[:100],
                        "url": url,
                        "snippet": f"Search result for query (fallback extraction)",
                        "position": i + 1,
                        "source": "ultrafast_fallback_ddg"
                    })

            return results

        except Exception as e:
            logger.error(f"❌ Fallback extraction failed: {e}")
            return []

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


# Register the tool
__all__ = ["UltraFastNoDriverSearchTool"]
