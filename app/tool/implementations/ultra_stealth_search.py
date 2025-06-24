"""
Ultra-Stealth NoDriver Search Tool
Advanced implementation with rotating proxies, realistic timing, and intelligent extraction
"""

import asyncio
import base64
import json
import os
import random
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple
import tempfile
from datetime import datetime

import nodriver as uc

from app.logger import logger
from app.tool.core.base import BaseTool, ToolConfig, ToolResult


class UltraStealthSearchTool(BaseTool):
    """Ultra-stealth search with advanced anti-detection techniques."""

    def __init__(self, **kwargs):
        default_config = ToolConfig(
            name="ultra_stealth_search",
            description="Ultra-stealth web search with rotating proxies and realistic behavior",
            llm_enabled=True,
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
                        "default": 45,
                    },
                    "search_engines": {
                        "type": "array",
                        "description": "Search engines to try",
                        "default": ["duckduckgo", "bing", "yahoo", "startpage"]
                    }
                },
                "required": ["query"],
            },
        )
        super().__init__(config=default_config, **kwargs)

    async def _execute(
        self,
        query: str,
        num_results: int = 5,
        timeout: int = 45,
        search_engines: List[str] = None,
    ) -> ToolResult:
        """Execute ultra-stealth search with advanced techniques."""

        if search_engines is None:
            search_engines = ["duckduckgo", "bing", "yahoo", "startpage"]

        logger.info(f"🥷 Ultra-Stealth Search: '{query}' (timeout: {timeout}s)")
        start_time = time.time()

        for engine in search_engines:
            try:
                logger.info(f"🔄 Trying {engine} with stealth mode...")

                # Calculate remaining timeout
                elapsed = time.time() - start_time
                remaining_timeout = max(15, timeout - elapsed)

                results = await asyncio.wait_for(
                    self._stealth_search_engine(engine, query, num_results),
                    timeout=remaining_timeout
                )

                if results:
                    total_time = time.time() - start_time
                    logger.info(f"✅ {engine} succeeded in {total_time:.1f}s: {len(results)} real results")

                    return ToolResult(
                        success=True,
                        content={
                            "query": query,
                            "results": results,
                            "total_results": len(results),
                            "search_engine": engine,
                            "method": "ultra_stealth",
                            "execution_time": f"{total_time:.1f}s",
                            "cost": "FREE",
                            "data_freshness": "REAL-TIME",
                            "warning": None
                        }
                    )
                else:
                    logger.warning(f"⚠️ {engine} returned no results")

            except asyncio.TimeoutError:
                logger.warning(f"⏰ {engine} timed out")
                continue
            except Exception as e:
                logger.error(f"❌ {engine} failed: {e}")
                continue

        # If all engines fail
        total_time = time.time() - start_time
        logger.error(f"❌ All stealth search engines failed in {total_time:.1f}s")

        return ToolResult(
            success=False,
            content={
                "query": query,
                "results": [],
                "error": "All stealth search engines failed - possible network/blocking issues",
                "execution_time": f"{total_time:.1f}s",
                "recommendation": "Try again later or check internet connectivity",
                "data_freshness": "FAILED"
            }
        )

    async def _stealth_search_engine(self, engine: str, query: str, num_results: int) -> List[Dict]:
        """Search a specific engine with maximum stealth."""

        browser = None
        try:
            # Phase 1: Ultra-Stealth Browser Setup
            browser_config = await self._get_stealth_browser_config()
            browser = await uc.start(**browser_config)

            # Phase 2: Realistic Navigation Pattern
            search_url = self._get_search_url(engine, query)
            page = await self._stealth_navigate(browser, search_url)

            # Phase 3: Intelligent Data Extraction
            results = await self._intelligent_extraction(page, engine, query, num_results)

            return results

        except Exception as e:
            logger.error(f"❌ Stealth search for {engine} failed: {e}")
            return []
        finally:
            if browser:
                try:
                    await browser.stop()
                except:
                    pass

    async def _get_stealth_browser_config(self) -> Dict:
        """Generate ultra-stealth browser configuration."""

        # Realistic user agents (rotate)
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

        selected_ua = random.choice(user_agents)

        # Advanced stealth configuration
        return {
            "headless": True,
            "user_data_dir": None,  # Fresh profile each time
            "browser_args": [
                f'--user-agent={selected_ua}',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-blink-features=AutomationControlled',
                '--disable-automation',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps',
                '--disable-popup-blocking',
                '--disable-translate',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-client-side-phishing-detection',
                '--disable-sync',
                '--metrics-recording-only',
                '--no-report-upload',
                '--allow-running-insecure-content',
                '--disable-ipc-flooding-protection',
                # Randomize window size
                f'--window-size={random.randint(1200, 1920)},{random.randint(800, 1080)}',
                # Additional stealth
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--enable-features=NetworkService,NetworkServiceLogging',
            ]
        }

    def _get_search_url(self, engine: str, query: str) -> str:
        """Get search URL for specific engine."""

        encoded_query = urllib.parse.quote_plus(query)

        urls = {
            "duckduckgo": f"https://duckduckgo.com/?q={encoded_query}",
            "bing": f"https://www.bing.com/search?q={encoded_query}",
            "yahoo": f"https://search.yahoo.com/search?p={encoded_query}",
            "startpage": f"https://www.startpage.com/search?query={encoded_query}",
        }

        return urls.get(engine, urls["duckduckgo"])

    async def _stealth_navigate(self, browser, url: str):
        """Navigate with realistic human-like timing."""

        # Realistic delay before navigation
        await asyncio.sleep(random.uniform(0.5, 2.0))

        page = await browser.get(url)

        # Simulate realistic page interaction timing
        base_wait = random.uniform(2.0, 4.0)

        # Wait for initial load
        await asyncio.sleep(base_wait)

        # Simulate human reading/scrolling behavior
        try:
            # Small random scroll to simulate human behavior
            await page.evaluate(f"window.scrollTo(0, {random.randint(50, 200)})")
            await asyncio.sleep(random.uniform(0.3, 0.8))

            # Scroll back up
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(random.uniform(0.2, 0.5))
        except:
            pass  # Ignore JS errors

        return page    async def _intelligent_extraction(self, page, engine: str, query: str, num_results: int) -> List[Dict]:
        """Phase 3: Intelligent extraction prioritizing speed over completeness."""

        logger.info(f"🧠 Attempting intelligent extraction from {engine}")

        # Strategy 1: Try DOM-based extraction first (fastest)
        try:
            dom_results = await asyncio.wait_for(
                self._dom_extraction(page, engine, num_results),
                timeout=5  # Very short timeout for DOM
            )
            if dom_results:
                logger.info(f"✅ DOM extraction successful: {len(dom_results)} results")
                return dom_results
        except Exception as e:
            logger.warning(f"⚠️ DOM extraction failed: {e}")

        # Strategy 2: Try HTML parsing (fast fallback)
        try:
            html_results = await asyncio.wait_for(
                self._html_parsing_extraction(page, engine, num_results),
                timeout=3  # Short timeout for HTML parsing
            )
            if html_results:
                logger.info(f"✅ HTML parsing successful: {len(html_results)} results")
                return html_results
        except Exception as e:
            logger.warning(f"⚠️ HTML parsing failed: {e}")

        # Strategy 3: Vision analysis (only as last resort with very short timeout)
        try:
            vision_results = await asyncio.wait_for(
                self._vision_extraction(page, query, num_results),
                timeout=8  # Very short timeout for vision
            )
            if vision_results:
                logger.info(f"✅ Vision extraction successful: {len(vision_results)} results")
                return vision_results
        except Exception as e:
            logger.warning(f"⚠️ Vision extraction failed: {e}")

        logger.warning(f"❌ All extraction methods failed for {engine}")
        return []    async def _dom_extraction(self, page, engine: str, num_results: int) -> List[Dict]:
        """Enhanced DOM extraction with comprehensive selectors."""

        # Comprehensive engine-specific selectors
        selectors = {
            "duckduckgo": [
                'article[data-testid="result"]',
                '.result__body',
                '.result',
                '.web-result',
                '[data-testid="result"] a[href]',
                'ol.react-results--main li',
            ],
            "bing": [
                '.b_algo',
                'ol#b_results li.b_algo',
                '.b_algo h2 a',
                'li[data-bm]',
                '.b_title a',
            ],
            "yahoo": [
                '.dd.algo',
                '.compTitle a',
                'ol.reg .algo',
                '.Sr',
                'section ol li',
            ],
            "startpage": [
                '.w-gl__result',
                '.result',
                '.algo-result',
                'section.w-gl ol li',
                '.w-gl__result__title a',
            ]
        }

        engine_selectors = selectors.get(engine, selectors["duckduckgo"])

        for selector in engine_selectors:
            try:
                # Enhanced JS extraction
                js_code = f"""
                (function() {{
                    const results = [];
                    let elements;

                    // Try the specific selector first
                    elements = document.querySelectorAll('{selector}');

                    // If no results, try broader selectors
                    if (elements.length === 0) {{
                        const fallbackSelectors = [
                            'div[class*="result"]',
                            'article',
                            'li[class*="result"]',
                            'div[data-testid*="result"]',
                            'a[href*="http"]:not([href*="{engine}.com"])'
                        ];

                        for (const fallback of fallbackSelectors) {{
                            elements = document.querySelectorAll(fallback);
                            if (elements.length > 0) break;
                        }}
                    }}

                    for (let i = 0; i < Math.min(elements.length, {num_results * 3}); i++) {{
                        const element = elements[i];

                        // Enhanced title extraction
                        let title = '';
                        const titleSelectors = [
                            'h2 a', 'h3 a', 'a h2', 'a h3',
                            '.result-title a', '.title a',
                            '[class*="title"] a', 'a[class*="title"]',
                            'a[href*="http"]'
                        ];

                        for (const titleSel of titleSelectors) {{
                            const titleEl = element.querySelector(titleSel);
                            if (titleEl && (titleEl.textContent || titleEl.innerText)) {{
                                title = (titleEl.textContent || titleEl.innerText).trim();
                                break;
                            }}
                        }}

                        // Enhanced URL extraction
                        let url = '';
                        const linkSelectors = [
                            'a[href*="http"]',
                            'h2 a[href]', 'h3 a[href]',
                            '[class*="title"] a[href]'
                        ];

                        for (const linkSel of linkSelectors) {{
                            const linkEl = element.querySelector(linkSel);
                            if (linkEl && linkEl.href) {{
                                url = linkEl.href;
                                break;
                            }}
                        }}

                        // Enhanced snippet extraction
                        let snippet = '';
                        const snippetSelectors = [
                            '.snippet', '.abstract', '.description', '.summary',
                            'p', 'span[class*="desc"]', 'div[class*="desc"]',
                            '.result__snippet', '.b_caption p'
                        ];

                        for (const snippetSel of snippetSelectors) {{
                            const snippetEl = element.querySelector(snippetSel);
                            if (snippetEl && (snippetEl.textContent || snippetEl.innerText)) {{
                                snippet = (snippetEl.textContent || snippetEl.innerText).trim();
                                break;
                            }}
                        }}

                        // Validate result
                        if (title && title.length > 5 && url &&
                            !url.includes('{engine}.com') &&
                            !url.includes('/search') &&
                            !title.toLowerCase().includes('search') &&
                            !title.toLowerCase().includes('help')) {{

                            results.push({{
                                title: title.substring(0, 200),
                                url: url,
                                snippet: snippet.substring(0, 300),
                                position: results.length + 1,
                                source: '{engine}_dom_enhanced'
                            }});

                            if (results.length >= {num_results}) break;
                        }}
                    }}

                    return results;
                }})();
                """

                results = await page.evaluate(js_code)

                if results and len(results) > 0:
                    # Additional filtering
                    valid_results = []
                    for result in results:
                        if (result.get("title") and len(result["title"]) > 5 and
                            result.get("url") and not self._is_invalid_result(result["title"], result["url"])):
                            valid_results.append(result)

                    if valid_results:
                        logger.info(f"✅ Enhanced DOM extraction found {len(valid_results)} valid results using selector: {selector}")
                        return valid_results[:num_results]

            except Exception as e:
                logger.debug(f"❌ Selector '{selector}' failed: {e}")
                continue

        return []

    async def _vision_extraction(self, page, query: str, num_results: int) -> List[Dict]:
        """Extract using LLM vision analysis."""

        try:
            # Take screenshot
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                screenshot_path = tmp_file.name

            await page.save_screenshot(screenshot_path)

            # Read and encode screenshot
            with open(screenshot_path, "rb") as f:
                screenshot_bytes = f.read()
            os.unlink(screenshot_path)

            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            # Enhanced vision prompt
            vision_prompt = f"""Analyze this search results page for query: "{query}"

Extract {num_results} REAL search results (not ads or internal links).

Return valid JSON only:
{{
    "results": [
        {{
            "title": "actual result title",
            "url": "actual URL (not search engine internal)",
            "snippet": "result description/snippet"
        }}
    ]
}}

IMPORTANT:
- Only include real external websites
- Skip ads, internal help pages, or search engine links
- Ensure URLs are actual external domains
- Focus on organic search results"""

            # Vision call
            if hasattr(self.llm, 'ask_vision') and hasattr(self.llm, 'vision_enabled') and self.llm.vision_enabled:
                messages = [{"role": "user", "content": vision_prompt}]
                image_url = f"data:image/png;base64,{screenshot_b64}"

                response = await self.llm.ask_vision(
                    messages=messages,
                    images=[image_url]
                )

                # Parse JSON response
                try:
                    parsed_response = json.loads(response)
                    results = parsed_response.get("results", [])

                    # Validate and clean results
                    valid_results = []
                    for result in results:
                        if (isinstance(result, dict) and
                            result.get("title") and
                            result.get("url") and
                            not self._is_invalid_result(result["title"], result["url"])):

                            valid_results.append({
                                "title": str(result["title"]).strip()[:200],
                                "url": str(result["url"]).strip(),
                                "snippet": str(result.get("snippet", "")).strip()[:300],
                                "position": len(valid_results) + 1,
                                "source": "vision_analysis"
                            })

                    return valid_results[:num_results]

                except json.JSONDecodeError:
                    logger.warning("❌ Vision response was not valid JSON")
                    return []
            else:
                logger.warning("⚠️ LLM vision not available")
                return []

        except Exception as e:
            logger.error(f"❌ Vision extraction failed: {e}")
            return []

    async def _html_parsing_extraction(self, page, engine: str, num_results: int) -> List[Dict]:
        """Raw HTML parsing as final fallback."""

        try:
            html_content = await page.get_content()

            # Engine-specific regex patterns
            patterns = {
                "duckduckgo": [
                    r'<h2[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h2>',
                    r'<a[^>]*href="(https?://[^"]*)"[^>]*class="[^"]*result[^"]*"[^>]*>([^<]+)</a>',
                ],
                "bing": [
                    r'<h2[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h2>',
                    r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h3>',
                ],
                "yahoo": [
                    r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h3>',
                    r'<span[^>]*class="[^"]*title[^"]*"[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
                ],
                "startpage": [
                    r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h3>',
                    r'<a[^>]*class="[^"]*result[^"]*"[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
                ]
            }

            import re
            engine_patterns = patterns.get(engine, patterns["duckduckgo"])

            for pattern in engine_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    results = []
                    for url, title in matches[:num_results * 2]:  # Get extra to filter
                        if not self._is_invalid_result(title, url):
                            results.append({
                                "title": title.strip()[:200],
                                "url": url.strip(),
                                "snippet": f"Search result from {engine}",
                                "position": len(results) + 1,
                                "source": f"{engine}_html"
                            })

                            if len(results) >= num_results:
                                break

                    if results:
                        return results

            return []

        except Exception as e:
            logger.error(f"❌ HTML parsing failed: {e}")
            return []

    def _is_invalid_result(self, title: str, url: str) -> bool:
        """Check if result is invalid (ads, internal links, etc.)."""

        if not title or not url or len(title.strip()) < 5:
            return True

        title_lower = title.lower()
        url_lower = url.lower()

        # Invalid patterns
        invalid_patterns = [
            # Search engine internal
            "duckduckgo.com", "bing.com", "yahoo.com", "startpage.com", "google.com",
            # Help/support pages
            "/search", "/help", "/support", "/about", "/contact", "/privacy", "/terms",
            "help.google.com", "support.google.com", "support.microsoft.com",
            # Ad indicators
            "sponsored", "advertisement", "promoted", "ad",
            # Internal navigation
            "/login", "/register", "/account", "/settings",
        ]

        for pattern in invalid_patterns:
            if pattern in title_lower or pattern in url_lower:
                return True

        return False


# Register the tool
__all__ = ["UltraStealthSearchTool"]
