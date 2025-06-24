"""
Simplified NoDriver Search Tool that actually works
Focus on reliable DOM extraction with scrolling
"""

import asyncio
import random
import re
from typing import Dict, List

import nodriver as uc
from loguru import logger

from app.tool.web_search import WebSearch


class SimplifiedNoDriverSearchTool(WebSearch):
    """Simplified NoDriver search that prioritizes working functionality."""

    def __init__(self):
        super().__init__()

    async def search_web(self, query: str, num_results: int = 5, search_engine: str = "duckduckgo") -> List[Dict]:
        """Simplified search with scrolling and reliable DOM extraction."""

        logger.info(f"🚀 Simplified NoDriver Search: '{query}' on {search_engine}")

        browser = None
        try:
            # Step 1: Launch browser
            browser = await uc.start(
                headless=False,  # Visible mode
                user_data_dir=None,
                browser_args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--no-first-run'
                ]
            )

            # Step 2: Navigate to search engine
            search_urls = {
                "duckduckgo": f"https://duckduckgo.com/?q={query.replace(' ', '+')}&iar=news&ia=news",
                "bing": f"https://www.bing.com/search?q={query.replace(' ', '+')}&qft=interval%3d%229%22",
                "startpage": f"https://www.startpage.com/sp/search?query={query.replace(' ', '+')}&cat=news"
            }

            search_url = search_urls.get(search_engine, search_urls["duckduckgo"])
            logger.info(f"🌐 Navigating to: {search_url}")

            page = await browser.get(search_url)
            await asyncio.sleep(4.0)  # Wait for page load

            # Step 3: Progressive scrolling to reveal more content
            logger.info("📜 Scrolling to reveal more search results...")
            await self._scroll_and_load_content(page)

            # Step 4: Extract search results using simple DOM extraction
            logger.info("🔍 Extracting search results...")
            results = await self._extract_search_results(page, query, num_results)

            if results:
                logger.info(f"✅ Found {len(results)} search results")
                return results
            else:
                logger.warning("❌ No search results found")
                return []

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
        finally:
            if browser:
                try:
                    await browser.stop()
                    logger.info("🔚 Browser closed")
                except:
                    pass

    async def _scroll_and_load_content(self, page):
        """Scroll progressively to load more content."""

        try:
            for i in range(3):  # 3 scroll steps
                logger.info(f"📜 Scroll step {i+1}/3")

                # Scroll down by viewport height
                await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8);")
                await asyncio.sleep(2.0)  # Wait for content to load

                # Check if we reached bottom
                at_bottom = await page.evaluate("""
                    window.innerHeight + window.pageYOffset >= document.body.offsetHeight - 200
                """)

                if at_bottom:
                    logger.info("📜 Reached bottom of page")
                    break

            logger.info("✅ Scrolling completed")

        except Exception as e:
            logger.warning(f"⚠️ Scrolling failed: {e}")

    async def _extract_search_results(self, page, query: str, num_results: int) -> List[Dict]:
        """Extract search results using robust DOM selectors."""

        try:
            # JavaScript to extract search results with multiple strategies
            extraction_js = f"""
            (function() {{
                const results = [];

                // Strategy 1: Look for any external links with substantial text
                const allLinks = document.querySelectorAll('a[href]');
                const currentDomain = window.location.hostname;

                for (const link of allLinks) {{
                    const text = (link.innerText || link.textContent || '').trim();
                    const href = link.href || '';

                    // Skip if too short, internal, or common UI elements
                    if (text.length < 12 ||
                        !href.startsWith('http') ||
                        href.includes(currentDomain) ||
                        href.includes('/search') ||
                        href.includes('/help') ||
                        text.toLowerCase().includes('privacy') ||
                        text.toLowerCase().includes('terms') ||
                        text.toLowerCase().includes('about')) {{
                        continue;
                    }}

                    // Look for article-like characteristics
                    const hasCapitalStart = /^[A-Z]/.test(text);
                    const hasMultipleWords = text.split(' ').length >= 3;
                    const isReasonableLength = text.length >= 15 && text.length <= 200;

                    if (hasCapitalStart && hasMultipleWords && isReasonableLength) {{
                        // Try to find description/snippet nearby
                        let snippet = '';

                        // Look in parent container for additional text
                        let container = link.parentElement;
                        if (container) {{
                            const containerText = container.innerText || '';
                            if (containerText.length > text.length + 20) {{
                                const afterTitle = containerText.substring(containerText.indexOf(text) + text.length);
                                snippet = afterTitle.trim().substring(0, 200);
                                // Clean up snippet
                                snippet = snippet.replace(/^[\\s\\n\\r•·-]+/, '').replace(/\\s+/g, ' ');
                            }}
                        }}

                        // Extract domain for source
                        let source = '';
                        try {{
                            const url = new URL(href);
                            source = url.hostname.replace('www.', '');
                        }} catch (e) {{
                            source = href.split('/')[2] || 'unknown';
                        }}

                        results.push({{
                            title: text,
                            url: href,
                            snippet: snippet,
                            source: source,
                            extraction_method: 'simple_dom'
                        }});

                        if (results.length >= {num_results * 2}) break;
                    }}
                }}

                // Strategy 2: Common search result containers
                const commonSelectors = [
                    'article a[href*="http"]',
                    '.result a[href*="http"]',
                    '.search-result a[href*="http"]',
                    '[class*="result"] a[href*="http"]',
                    'h2 a[href*="http"]',
                    'h3 a[href*="http"]'
                ];

                for (const selector of commonSelectors) {{
                    const elements = document.querySelectorAll(selector);
                    for (const element of elements) {{
                        const text = (element.innerText || element.textContent || '').trim();
                        const href = element.href || '';

                        if (text.length >= 12 &&
                            href.startsWith('http') &&
                            !href.includes(currentDomain) &&
                            !results.some(r => r.url === href)) {{

                            let source = '';
                            try {{
                                const url = new URL(href);
                                source = url.hostname.replace('www.', '');
                            }} catch (e) {{
                                source = 'unknown';
                            }}

                            results.push({{
                                title: text,
                                url: href,
                                snippet: '',
                                source: source,
                                extraction_method: 'selector_based'
                            }});

                            if (results.length >= {num_results * 2}) break;
                        }}
                    }}
                    if (results.length >= {num_results * 2}) break;
                }}

                // Remove duplicates and return top results
                const uniqueResults = [];
                const seenUrls = new Set();

                for (const result of results) {{
                    if (!seenUrls.has(result.url)) {{
                        seenUrls.add(result.url);
                        uniqueResults.push(result);
                        if (uniqueResults.length >= {num_results}) break;
                    }}
                }}

                return uniqueResults;
            }})();
            """

            # Execute extraction
            results = await page.evaluate(extraction_js)

            # Handle potential errors
            if hasattr(results, 'exception'):
                logger.warning(f"JavaScript extraction error: {results.exception}")
                return []

            if not isinstance(results, list):
                logger.warning(f"Unexpected result type: {type(results)}")
                return []

            # Process and validate results
            validated_results = []
            for i, result in enumerate(results):
                if (result.get('title') and result.get('url') and
                    not self._is_invalid_result(result['title'], result['url'])):

                    # Enrich with position and metadata
                    validated_result = {
                        'title': result['title'][:150],  # Limit title length
                        'url': result['url'],
                        'snippet': result.get('snippet', '')[:200],  # Limit snippet
                        'source': result.get('source', 'unknown'),
                        'position': i + 1,
                        'extraction_method': result.get('extraction_method', 'dom'),
                        'search_engine': 'duckduckgo'  # Add metadata
                    }
                    validated_results.append(validated_result)

            logger.info(f"🎯 Extracted {len(validated_results)} validated results")
            return validated_results

        except Exception as e:
            logger.error(f"❌ Result extraction failed: {e}")
            return []

    def _is_invalid_result(self, title: str, url: str) -> bool:
        """Check if result should be filtered out."""

        invalid_patterns = [
            'sign in', 'login', 'register', 'subscribe', 'download',
            'privacy policy', 'terms of service', 'cookie policy',
            'about us', 'contact us', 'help', 'support', 'faq'
        ]

        title_lower = title.lower()
        url_lower = url.lower()

        # Check for invalid patterns in title
        for pattern in invalid_patterns:
            if pattern in title_lower:
                return True

        # Check for invalid domains
        invalid_domains = [
            'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
            'youtube.com', 'reddit.com', 'pinterest.com'
        ]

        for domain in invalid_domains:
            if domain in url_lower:
                return True

        return False
