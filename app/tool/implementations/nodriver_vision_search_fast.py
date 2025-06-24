"""
Fast NoDriver Vision Search Tool with Enhanced Blue Link Detection
Optimized for speed and reliability with scrolling and content extraction.
"""

import asyncio
import json
import random
import re
import time
from typing import Dict, List, Optional

import nodriver as uc
from loguru import logger

from app.tool.core.base import BaseTool, ToolConfig, ToolResult


class FastNoDriverVisionSearchTool(BaseTool):
    """Ultra-fast NoDriver search with vision fallback and blue link detection."""

    def __init__(self):
        super().__init__(
            config=ToolConfig(
                name="web_search",
                description="Search the web for current information and extract content from articles",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find information about"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of search results to return",
                            "default": 5
                        },
                        "search_engine": {
                            "type": "string",
                            "description": "Search engine to use",
                            "default": "duckduckgo",
                            "enum": ["duckduckgo", "bing", "yahoo", "startpage"]
                        }
                    },
                    "required": ["query"]
                }            )
        )

    @property
    def name(self) -> str:
        """Get tool name for compatibility."""
        return self.config.name

    async def _execute(self, **kwargs) -> ToolResult:
        """Core execution method required by BaseTool."""
        query = kwargs.get('query', '')
        num_results = kwargs.get('num_results', 5)
        search_engine = kwargs.get('search_engine', 'duckduckgo')

        return await self.execute(query, num_results, search_engine)

    async def execute(self, query: str, num_results: int = 5, search_engine: str = "duckduckgo") -> ToolResult:
        """Execute the search and return results."""
        try:
            # Convert num_results to int if it's a string
            if isinstance(num_results, str):
                num_results = int(num_results)

            results = await self.search_web(query, num_results, search_engine)

            if not results:
                return ToolResult(
                    success=False,
                    content="No search results found. The search may have failed or returned empty results.",
                    error="No results found"
                )

            # Format results for display
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_result = f"**Result {i}:**\n"
                formatted_result += f"Title: {result.get('title', 'N/A')}\n"
                formatted_result += f"URL: {result.get('url', 'N/A')}\n"
                formatted_result += f"Source: {result.get('source', 'N/A')}\n"

                if result.get('snippet'):
                    formatted_result += f"Snippet: {result['snippet']}\n"

                if result.get('content') and len(result['content']) > 100:
                    formatted_result += f"Content Preview: {result['content'][:200]}...\n"
                    formatted_result += f"Full Content Available: {len(result['content'])} characters\n"

                formatted_results.append(formatted_result)
            content = f"Found {len(results)} search results for '{query}':\n\n" + "\n---\n".join(formatted_results)

            return ToolResult(
                success=True,
                content=content,
                metadata={"results": results, "query": query, "num_results": len(results)}
            )

        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            return ToolResult(
                success=False,
                content=f"Search failed: {str(e)}",
                error=str(e)
            )

    async def search_web(self, query: str, num_results: int = 5, search_engine: str = "duckduckgo") -> List[Dict]:
        """Fast search with blue link detection and content extraction."""

        # Ensure num_results is an integer
        num_results = self._ensure_int(num_results, 5)

        logger.info(f"🚀 Fast NoDriver Vision Search: '{query}' on {search_engine}")

        browser = None
        try:
            # Step 1: Launch stealth browser (visible for user intervention)
            browser = await uc.start(
                headless=False,  # Visible mode for user intervention
                user_data_dir=None,  # Fresh profile each time
                browser_args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-first-run',
                    '--disable-default-apps'
                ]
            )

            # Navigate to search engine
            search_urls = {
                "duckduckgo": f"https://duckduckgo.com/?q={query.replace(' ', '+')}&iar=news&ia=news",
                "bing": f"https://www.bing.com/search?q={query.replace(' ', '+')}&qft=interval%3d%229%22",
                "yahoo": f"https://search.yahoo.com/search?p={query.replace(' ', '+')}&n=20&ei=UTF-8",
                "startpage": f"https://www.startpage.com/sp/search?query={query.replace(' ', '+')}&cat=news&language=english"
            }

            search_url = search_urls.get(search_engine, search_urls["duckduckgo"])
            logger.info(f"🌐 Navigating to {search_engine}: {search_url}")

            page = await browser.get(search_url)
            await asyncio.sleep(random.uniform(3.0, 5.0))  # Allow page to load fully
              # Step 2: Try direct element clicking approach (bypass JavaScript issues)
            logger.info("🖼️ Strategy 1: Direct element detection and clicking")
            try:
                search_results = await self._direct_element_clicking(browser, page, query, num_results)
                if search_results and len(search_results) >= 1:  # Changed from min(num_results, 2) to 1
                    logger.info(f"✅ Direct element clicking successful: {len(search_results)} results with content")
                    return search_results
            except Exception as e:
                logger.warning(f"⚠️ Direct element clicking failed: {e}")

            # Step 3: Try blue link extraction (if JavaScript works)
            logger.info("🔵 Strategy 2: Smart blue link detection and extraction")
            try:
                search_results = await self._extract_blue_link_content(browser, page, query, num_results)
                if search_results and len(search_results) >= min(num_results, 2):
                    logger.info(f"✅ Blue link extraction successful: {len(search_results)} results with content")
                    return search_results
            except Exception as e:
                logger.warning(f"⚠️ Blue link extraction failed: {e}")

            # Step 4: Fallback to DOM extraction
            logger.info("🧠 Strategy 3: DOM extraction fallback")
            try:
                search_results = await self._fast_dom_extraction(page, num_results)
                if search_results:
                    logger.info(f"✅ DOM extraction successful: {len(search_results)} search results found")
                    return search_results
            except Exception as e:
                logger.warning(f"⚠️ DOM extraction failed: {e}")            # Step 5: Vision fallback
            logger.info("📸 Strategy 4: Vision analysis fallback")
            screenshot_b64 = await self._fast_screenshot(page)
            results = await self._fast_parse_with_vision(screenshot_b64, query, num_results)
            return results

        except Exception as e:
            logger.error(f"❌ Fast search error: {e}")
            return []
        finally:
            if browser:
                try:
                    await browser.stop()
                    logger.info("🔚 Browser closed")
                except Exception:
                    pass

    async def _extract_blue_link_content(self, browser, search_page, query: str, num_results: int) -> List[Dict]:
        """Smart extraction by detecting and clicking blue article title links with scrolling."""

        try:
            # First, detect blue links using enhanced DOM + color detection with scrolling
            blue_links = await self._detect_blue_article_links_with_scrolling(search_page, num_results)

            if not blue_links:
                logger.warning("❌ No blue article links detected")
                return []

            logger.info(f"✅ Detected {len(blue_links)} blue article links")

            # Process the most relevant results (limit to avoid excessive clicking)
            enriched_results = []
            for i, link_data in enumerate(blue_links[:min(num_results, 3)]):
                if not link_data.get('title') or not link_data.get('url'):
                    continue

                title = link_data.get('title')
                url = link_data.get('url')
                snippet = link_data.get('snippet', '')

                try:
                    logger.info(f"🖱️ Clicking blue link {i+1}: {title[:30]}...")

                    # Navigate to the article URL
                    article_page = await browser.get(url)
                    await asyncio.sleep(random.uniform(2.0, 3.5))

                    # Extract content using smart extraction
                    content = await self._extract_article_content_smart(article_page, query, title)

                    # Create rich result with content
                    rich_result = {
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "position": i + 1,
                        "source": "blue_link_clicked",
                        "content": content[:2500] if content else "",
                        "content_length": len(content) if content else 0
                    }

                    enriched_results.append(rich_result)
                    logger.info(f"✅ Extracted content from article: {title[:30]}")

                    # Go back to search results
                    await browser.back()
                    await asyncio.sleep(random.uniform(1.0, 2.0))

                except Exception as e:
                    logger.warning(f"❌ Failed to extract from blue link: {str(e)[:100]}")
                    # Add basic result even if extraction failed
                    enriched_results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "position": i + 1,
                        "source": "blue_link_detected"
                    })

                    # Try to go back to search results
                    try:
                        await browser.back()
                        await asyncio.sleep(1.0)
                    except:
                        pass

            return enriched_results

        except Exception as e:
            logger.error(f"❌ Blue link content extraction failed: {e}")
            return []

    async def _detect_blue_article_links_with_scrolling(self, page, num_results: int) -> List[Dict]:
        """Detect blue article links with progressive scrolling to reveal more results."""

        try:
            all_valid_links = []

            # Progressive scrolling to find blue links at different page positions
            logger.info("📜 Starting progressive scroll to detect blue article links...")

            for scroll_step in range(4):  # Try 4 scroll positions for thorough coverage
                logger.info(f"📜 Scroll position {scroll_step + 1}/4")
                  # Simple and effective JavaScript for blue link detection
                js_code = f"""
                (function() {{
                    const allLinks = document.querySelectorAll('a[href]');
                    const results = [];

                    for (const link of allLinks) {{
                        const linkText = (link.innerText || link.textContent || '').trim();
                        const href = link.href || '';

                        // Skip short text, internal links, or non-http links
                        if (linkText.length < 10 || !href.startsWith('http') ||
                            href.includes('duckduckgo.com') || href.includes('/search')) {{
                            continue;
                        }}

                        // Get basic element info
                        const rect = link.getBoundingClientRect();
                        const isVisible = rect.top >= -100 && rect.bottom <= window.innerHeight + 100;

                        if (isVisible && rect.width > 30 && rect.height > 10) {{
                            // Simple snippet extraction
                            let snippet = '';
                            const parent = link.parentElement;
                            if (parent) {{
                                const parentText = parent.innerText || '';
                                if (parentText.length > linkText.length + 10) {{
                                    const afterTitle = parentText.substring(parentText.indexOf(linkText) + linkText.length);
                                    snippet = afterTitle.trim().substring(0, 120);
                                }}
                            }}

                            // Return simple string format for reliability
                            results.push(linkText + '|||' + href + '|||' + snippet);
                        }}
                    }}

                    return results;
                }})();
                """
                  # Execute detection at current scroll position
                try:
                    blue_links_result = await page.evaluate(js_code)

                    # Handle potential JavaScript error or convert string results
                    if hasattr(blue_links_result, 'exception'):
                        logger.warning(f"JavaScript execution error: {blue_links_result.exception}")
                        blue_links = []
                    else:
                        # Convert string results to objects
                        blue_links = []
                        raw_results = blue_links_result if isinstance(blue_links_result, list) else []

                        for raw_result in raw_results:
                            if isinstance(raw_result, str) and '|||' in raw_result:
                                parts = raw_result.split('|||')
                                if len(parts) >= 3:
                                    blue_links.append({
                                        'title': parts[0].strip(),
                                        'url': parts[1].strip(),
                                        'snippet': parts[2].strip(),
                                        'reason': 'visible_external_link'
                                    })

                except Exception as e:
                    logger.warning(f"Page evaluation failed: {e}")
                    blue_links = []

                # Filter and add new unique links
                new_links_count = 0
                for link in blue_links:
                    if (link.get('title') and len(link['title']) > 5 and
                        link.get('url') and link['url'].startswith('http') and
                        not self._is_invalid_result(link['title'], link['url'])):

                        # Check if we already have this link (by URL or title)
                        is_duplicate = any(
                            existing['url'] == link['url'] or
                            (existing['title'] == link['title'] and len(link['title']) > 15)
                            for existing in all_valid_links
                        )

                        if not is_duplicate:
                            all_valid_links.append(link)
                            new_links_count += 1

                logger.info(f"📜 Position {scroll_step + 1}: Found {new_links_count} new blue links (total: {len(all_valid_links)})")

                # Log details of found links for debugging
                if new_links_count > 0:
                    logger.info(f"📝 New links found at scroll position {scroll_step + 1}:")
                    for i, link in enumerate(blue_links[:3]):
                        logger.info(f"   {i+1}. Title: {link.get('title', 'N/A')[:50]}...")
                        logger.info(f"      URL: {link.get('url', 'N/A')[:50]}...")
                        logger.info(f"      Reason: {link.get('reason', 'N/A')}")
                        logger.info(f"      Valid: {not self._is_invalid_result(link.get('title', ''), link.get('url', ''))}")

                # Stop early if we have enough high-quality results
                quality_links = [l for l in all_valid_links if len(l.get('snippet', '')) > 20]  # Lower threshold
                if len(all_valid_links) >= num_results:
                    logger.info(f"✅ Found enough links ({len(all_valid_links)}), stopping scroll")
                    break

                # Scroll down for next iteration (but not on last iteration)
                if scroll_step < 3:
                    scroll_amount = 0.8 if scroll_step == 0 else 0.6  # Larger first scroll to skip ads
                    await page.evaluate(f"window.scrollBy(0, window.innerHeight * {scroll_amount});")
                    await asyncio.sleep(random.uniform(1.2, 2.0))  # Wait for dynamic content

                    # Check if we've reached the bottom
                    at_bottom = await page.evaluate("""
                        window.innerHeight + window.pageYOffset >= document.body.offsetHeight - 200
                    """)
                    if at_bottom:
                        logger.info("📜 Reached bottom of page, stopping scroll")
                        break

            # Final sorting by quality and relevance
            all_valid_links.sort(key=lambda x: (
                len(x.get('snippet', '')) * 2,  # Prioritize links with good snippets
                -x.get('viewport_position', 1000),  # Prefer higher positioned links
                x.get('link_size', 0)  # Prefer larger clickable areas
            ), reverse=True)

            logger.info(f"✅ Final blue link detection complete: {len(all_valid_links)} unique links found")
            return all_valid_links[:num_results]

        except Exception as e:
            logger.error(f"❌ Enhanced blue link detection failed: {e}")
            return []

    async def _extract_article_content_smart(self, page, query: str, title: str) -> str:
        """Smart content extraction from article pages."""

        try:
            # Wait for content to load
            await asyncio.sleep(2.0)

            # Try multiple content extraction strategies
            content_selectors = [
                'article',
                '[role="main"]',
                '.content',
                '.article-content',
                '.post-content',
                '.entry-content',
                'main',
                '#content',
                '.text-content'
            ]

            for selector in content_selectors:
                try:
                    content = await page.evaluate(f"""
                        const element = document.querySelector('{selector}');
                        return element ? element.innerText : '';
                    """)

                    if content and len(content.strip()) > 200:
                        # Clean and extract relevant content
                        content = content.strip()
                        # Remove extra whitespace
                        content = re.sub(r'\s+', ' ', content)
                        logger.info(f"✅ Extracted content using selector: {selector}")
                        return content[:3000]  # Limit content length

                except Exception:
                    continue

            # Fallback: extract all text content
            try:
                content = await page.evaluate("""
                    document.body.innerText || document.body.textContent || ''
                """)

                if content and len(content.strip()) > 100:
                    content = re.sub(r'\s+', ' ', content.strip())
                    return content[:2000]

            except Exception:
                pass

            logger.warning("⚠️ No substantial content found")
            return ""

        except Exception as e:
            logger.error(f"❌ Content extraction failed: {e}")
            return ""

    async def _fast_dom_extraction(self, page, num_results: int) -> List[Dict]:
        """Fast DOM-based search result extraction with real search engine support."""

        try:
            # First, scroll to make sure we can see results
            await page.evaluate("window.scrollTo(0, 400);")
            await asyncio.sleep(1)

            # Try multiple approaches to get search results
            js_code = """
            (function() {
                const results = [];

                // DuckDuckGo specific selectors
                const duckSelectors = [
                    'h2 a[href*="http"]:not([href*="duckduckgo.com"])',
                    '.results_links_deep a:not([href*="duckduckgo.com"])',
                    'a[href*="http"]:not([href*="duckduckgo.com"]):not([href*="/search"]):not([href*="/help"])'
                ];

                // Bing specific selectors
                const bingSelectors = [
                    '.b_algo h2 a',
                    '.b_title a',
                    'cite + a'
                ];

                // Generic selectors
                const genericSelectors = [
                    'a[href*="http"]:not([href*="' + window.location.hostname + '"])',
                    'h1 a, h2 a, h3 a'
                ];

                const allSelectors = [...duckSelectors, ...bingSelectors, ...genericSelectors];

                for (const selector of allSelectors) {
                    try {
                        const elements = document.querySelectorAll(selector);

                        for (const element of elements) {
                            const titleText = (element.innerText || element.textContent || '').trim();
                            const url = element.href;

                            if (!titleText || titleText.length < 10 || !url || !url.startsWith('http')) {
                                continue;
                            }

                            // Skip internal/navigation links
                            if (url.includes(window.location.hostname) ||
                                url.includes('/search') ||
                                url.includes('/help') ||
                                url.includes('/about') ||
                                titleText.toLowerCase().includes('sign in') ||
                                titleText.toLowerCase().includes('privacy')) {
                                continue;
                            }

                            // Check if we already have this result
                            const duplicate = results.find(r => r.url === url || r.title === titleText);
                            if (duplicate) continue;

                            // Try to find snippet/description
                            let snippet = '';
                            let container = element.closest('div, li, article');
                            if (container) {
                                const containerText = container.innerText || '';
                                const titleIndex = containerText.indexOf(titleText);
                                if (titleIndex >= 0) {
                                    const afterTitle = containerText.substring(titleIndex + titleText.length);
                                    snippet = afterTitle.trim().substring(0, 150);
                                    snippet = snippet.replace(/^[\\s\\n\\r•·-]+/, '');
                                }
                            }

                            results.push({
                                title: titleText,
                                url: url,
                                snippet: snippet,
                                source: 'dom_extraction'
                            });

                            if (results.length >= 15) break; // Collect more than needed
                        }

                        if (results.length >= 10) break; // Stop if we have enough
                    } catch (e) {
                        console.log('Selector failed:', selector, e);
                    }
                }

                return results;
            })();
            """

            try:
                results_result = await page.evaluate(js_code)

                # Handle JavaScript result
                if hasattr(results_result, 'exception'):
                    logger.warning(f"DOM extraction JavaScript error: {results_result.exception}")
                    results = []
                elif isinstance(results_result, list):
                    results = results_result
                else:
                    logger.warning(f"Unexpected result type: {type(results_result)}")
                    results = []

            except Exception as e:
                logger.warning(f"DOM extraction evaluation failed: {e}")
                results = []

            # Process and validate results
            valid_results = []
            for i, result in enumerate(results[:num_results]):
                if isinstance(result, dict) and result.get('title') and result.get('url'):
                    if not self._is_invalid_result(result['title'], result['url']):
                        result['position'] = i + 1
                        valid_results.append(result)
                elif isinstance(result, str):
                    # Handle string results if needed
                    logger.debug(f"String result: {result[:50]}...")

            logger.info(f"✅ DOM extraction found {len(valid_results)} valid results")
            return valid_results

        except Exception as e:
            logger.error(f"❌ DOM extraction failed: {e}")
            return []

    async def _fast_screenshot(self, page) -> str:
        """Take and encode screenshot for vision analysis."""

        try:
            import base64  # Take screenshot
            try:
                # Try the direct approach first
                screenshot_path = None
                try:
                    screenshot_bytes = await page.save_screenshot()
                    # If save_screenshot returns a path instead of bytes
                    if isinstance(screenshot_bytes, str):
                        screenshot_path = screenshot_bytes
                        with open(screenshot_path, 'rb') as f:
                            screenshot_bytes = f.read()

                    if screenshot_bytes:
                        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                        return screenshot_b64

                except Exception as e:
                    logger.debug(f"Direct screenshot failed: {e}")

                # Try alternative screenshot method
                import os
                import tempfile

                if not screenshot_path:
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                        screenshot_path = tmp_file.name

                    await page.save_screenshot(screenshot_path)

                # Read and encode
                with open(screenshot_path, 'rb') as f:
                    screenshot_bytes = f.read()

                # Clean up temp file
                if os.path.exists(screenshot_path):
                    os.unlink(screenshot_path)

                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                return screenshot_b64

            except Exception as inner_e:
                logger.warning(f"Alternative screenshot method failed: {inner_e}")
                return ""

        except Exception as e:
            logger.error(f"❌ Screenshot failed: {e}")
            return ""

    async def _fast_parse_with_vision(self, screenshot_b64: str, query: str, num_results: int) -> List[Dict]:
        """Parse search results using vision analysis."""

        if not screenshot_b64:
            return []

        try:
            from app.llm import create_llm

            # Enhanced vision prompt
            vision_prompt = f"""
            SEARCH RESULTS ANALYSIS TASK:
            Query: "{query}"

            Analyze this search results page screenshot and extract {num_results} article results.
            Focus on:
            1. BLUE clickable article titles (these are the actual news/article links)
            2. Headlines with descriptive text below them
            3. Recent news articles and blog posts
            4. Avoid ads, navigation, and promotional content

            For each article result, provide:
            - title: The blue headline text (exact as shown)
            - url: Full URL if visible, or construct likely URL from domain + title
            - snippet: Description/preview text below the title
            - source: Website name or domain

            Return as JSON array with format:
            [{{"title": "...", "url": "...", "snippet": "...", "source": "..."}}]

            Focus on REAL articles about: {query}
            """

            llm = create_llm()

            response = await llm.chat_completion(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
                    ]
                }],
                temperature=0.1,
                max_tokens=2000
            )

            response_text = response.choices[0].message.content.strip()

            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                results_data = json.loads(json_match.group())

                # Process and validate results
                validated_results = []
                for i, result in enumerate(results_data[:num_results]):
                    if (result.get('title') and len(result['title']) > 5 and
                        result.get('url') and
                        not self._is_invalid_result(result['title'], result.get('url', ''))):

                        result['position'] = i + 1
                        result['source'] = 'vision_analysis'
                        validated_results.append(result)

                logger.info(f"✅ Vision analysis extracted {len(validated_results)} results")
                return validated_results

        except Exception as e:
            logger.error(f"❌ Vision parsing failed: {e}")

        return []

    async def _direct_element_clicking(self, browser, search_page, query: str, num_results: int) -> List[Dict]:
        """Direct element detection and clicking without complex JavaScript."""

        try:
            results = []

            # Scroll to reveal more content
            await search_page.evaluate("window.scrollTo(0, 300);")
            await asyncio.sleep(2)

            # Try to find clickable elements using simple CSS selectors
            # These are common patterns for search result links
            search_selectors = [
                "a[href*='http']:not([href*='duckduckgo.com']):not([href*='/search']):not([href*='/help'])",
                "h2 a", "h3 a", ".result a", "article a"
            ]

            clicked_urls = set()

            for selector in search_selectors:
                if len(results) >= num_results:
                    break

                try:
                    # Find elements matching this selector
                    elements = await search_page.select_all(selector)
                    logger.info(f"🔍 Found {len(elements)} elements with selector: {selector}")

                    for element in elements[:min(5, num_results - len(results))]:
                        try:
                            # Get basic info about the element
                            element_text = await element.apply("el => el.textContent || el.innerText || ''")
                            element_href = await element.apply("el => el.href || ''")

                            if not element_text or len(element_text.strip()) < 10:
                                continue
                            if not element_href or not element_href.startswith('http'):
                                continue
                            if element_href in clicked_urls:
                                continue
                            if self._is_invalid_result(element_text.strip(), element_href):
                                continue

                            title = element_text.strip()[:100]
                            url = element_href

                            logger.info(f"🖱️ Attempting to click: {title[:50]}...")
                            logger.info(f"   URL: {url[:50]}...")                            # Navigate directly to the URL instead of clicking
                            try:
                                logger.info(f"🖱️ Navigating to: {title[:50]}...")
                                logger.info(f"   URL: {url[:50]}...")

                                # Navigate directly to the article
                                article_page = await browser.get(url)
                                await asyncio.sleep(random.uniform(2.0, 4.0))

                                # Extract content from the article page
                                content = await self._extract_article_content_smart(article_page, query, title)

                                result = {
                                    "title": title,
                                    "url": url,
                                    "snippet": content[:200] if content else "Direct navigation extraction",
                                    "position": len(results) + 1,
                                    "source": "direct_navigation",
                                    "content": content[:2500] if content else "",
                                    "content_length": len(content) if content else 0
                                }

                                results.append(result)
                                clicked_urls.add(url)

                                logger.info(f"✅ Successfully extracted content from: {title[:30]}")
                                  # Go back to search results - use page navigation instead
                                try:
                                    # Navigate back to the search page
                                    search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}&iar=news&ia=news"
                                    search_page = await browser.get(search_url)
                                    await asyncio.sleep(random.uniform(1.5, 2.5))
                                except Exception as back_error:
                                    logger.warning(f"⚠️ Failed to return to search: {str(back_error)[:50]}")
                                    # Continue anyway - we got the content

                            except Exception as nav_error:
                                logger.warning(f"❌ Navigation failed: {str(nav_error)[:50]}")
                                # Add basic result even if navigation failed
                                results.append({
                                    "title": title,
                                    "url": url,
                                    "snippet": "Direct element detected",
                                    "position": len(results) + 1,
                                    "source": "direct_element_detected"
                                })
                                clicked_urls.add(url)

                        except Exception as element_error:
                            logger.warning(f"❌ Element processing failed: {str(element_error)[:50]}")
                            continue

                except Exception as selector_error:
                    logger.warning(f"❌ Selector {selector} failed: {str(selector_error)[:50]}")
                    continue

            logger.info(f"✅ Direct element clicking found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"❌ Direct element clicking failed: {e}")
            return []

    def _is_invalid_result(self, title: str, url: str) -> bool:
        """Check if a result should be filtered out."""

        invalid_patterns = [
            'sign in', 'login', 'register', 'subscribe', 'download',
            'privacy policy', 'terms of service', 'cookie', 'about us',
            'contact', 'help', 'support', 'faq', 'home page',
            'menu', 'navigation', 'sidebar', 'footer', 'header'
        ]

        title_lower = title.lower()
        url_lower = url.lower() if url else ""

        # Check for invalid patterns
        for pattern in invalid_patterns:
            if pattern in title_lower:
                return True

        # Check for non-article domains
        invalid_domains = [
            'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
            'youtube.com', 'reddit.com', 'pinterest.com', 'tiktok.com'
        ]

        for domain in invalid_domains:
            if domain in url_lower:
                return True

        return False

    def _ensure_int(self, value, default=5):
        """Ensure value is an integer, converting strings if necessary."""
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return value if isinstance(value, int) else default
