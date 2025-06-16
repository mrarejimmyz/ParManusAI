"""
Optimized Nodriver-based Google Search Implementation
Clean, fast, and reliable stealth browsing for research
"""

import asyncio
import os
from typing import Dict, List, Optional
from urllib.parse import quote

from app.logger import logger

try:
    import nodriver as uc

    NODRIVER_AVAILABLE = True
except ImportError:
    NODRIVER_AVAILABLE = False
    logger.warning("nodriver not available")


class NodriverGoogleSearch:
    """Optimized Google search using nodriver for stealth browsing"""

    def __init__(self):
        self.browser = None
        self.page = None

    async def perform_google_search(self, query: str) -> Dict:
        """Perform Google search with CAPTCHA detection and fallback"""
        if not NODRIVER_AVAILABLE:
            return {"success": False, "error": "nodriver not available"}

        try:
            logger.info(f"🔍 Starting Google search: {query}")

            await self._init_browser()

            # Navigate to search
            search_url = f"https://www.google.com/search?q={quote(query)}"
            await self.page.get(search_url)
            await asyncio.sleep(2)

            # Check for CAPTCHA/blocking
            page_content = await self.page.get_content()
            if any(
                term in page_content.lower()
                for term in ["captcha", "sorry", "unusual traffic"]
            ):
                logger.warning("🚫 Google CAPTCHA/blocking detected")
                return {"success": False, "error": "Google CAPTCHA detected"}

            # Extract results
            results = await self._extract_results()
            await self._cleanup()

            return {
                "success": True,
                "query": query,
                "results": results,
                "method": "nodriver",
            }

        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            await self._cleanup()
            return {"success": False, "error": str(e)}

    async def _init_browser(self):
        """Initialize browser with optimal settings"""
        # Try browsers in priority order
        browsers = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            None,  # Auto-detection
        ]

        for browser_path in browsers:
            if browser_path and not os.path.exists(browser_path):
                continue

            try:
                logger.info(f"🔍 Trying: {browser_path or 'auto-detection'}")

                config = uc.Config()
                if browser_path:
                    config.browser_executable_path = browser_path
                config.headless = True
                config.sandbox = False

                self.browser = await uc.start(config=config)
                self.page = await self.browser.get("https://www.google.com")
                await asyncio.sleep(1)

                logger.info("✅ Browser ready")
                return

            except Exception as e:
                logger.warning(f"⚠️ Failed: {str(e)[:50]}...")
                continue

        raise Exception("No browser available")

    async def _extract_results(self) -> List[Dict]:
        """Extract search results from page"""
        results = []

        try:
            # Modern Google result selectors
            selectors = ["div[data-result-index]", ".g", ".tF2Cxc"]

            for selector in selectors:
                elements = await self.page.select_all(selector)
                if elements:
                    logger.info(f"📊 Found {len(elements)} results")

                    for i, element in enumerate(elements[:5]):  # Limit to top 5
                        try:
                            # Get title
                            title_elem = await element.query_selector("h3")
                            title = (
                                await title_elem.text()
                                if title_elem
                                else f"Result {i+1}"
                            )

                            # Get URL
                            link_elem = await element.query_selector("a[href]")
                            url = (
                                await link_elem.get_attribute("href")
                                if link_elem
                                else None
                            )

                            # Get snippet
                            snippet_elem = await element.query_selector(
                                ".VwiC3b, .s3v9rd"
                            )
                            snippet = await snippet_elem.text() if snippet_elem else ""

                            if url and not url.startswith("/"):
                                results.append(
                                    {
                                        "title": title.strip(),
                                        "url": url,
                                        "snippet": snippet.strip()[:150],
                                    }
                                )

                        except Exception as e:
                            logger.warning(f"⚠️ Failed to extract result {i}: {str(e)}")
                            continue

                    break  # Stop after first successful selector

        except Exception as e:
            logger.warning(f"⚠️ Result extraction failed: {str(e)}")

        return results

    async def _cleanup(self):
        """Clean up browser resources"""
        try:
            if self.browser:
                await self.browser.stop()
                self.browser = None
                self.page = None
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {str(e)}")
