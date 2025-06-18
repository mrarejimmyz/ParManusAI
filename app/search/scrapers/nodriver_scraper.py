"""
NoDriver-based scraping strategies for bypassing anti-bot detection.
"""

import asyncio
import random
import time
from typing import Optional

import nodriver as uc

from app.logger import logger


class NoDriverScraper:
    """Handles scraping using NoDriver technology."""

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

        self.viewport_sizes = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
        ]

    async def scrape_with_nodriver(self, url: str, context: str = "") -> Optional[str]:
        """
        Scrape using nodriver to bypass anti-bot detection
        """
        browser = None
        try:
            # Random user agent for stealth
            user_agent = random.choice(self.user_agents)
            viewport = random.choice(self.viewport_sizes)

            # Configure nodriver with stealth settings
            browser_args = [
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor",
                "--user-agent=" + user_agent,
            ]

            logger.debug(f"Launching browser with stealth settings for {url}")
            browser = await uc.start(args=browser_args, headless=True)

            # Create new page with stealth settings
            page = await browser.get(url)

            # Set viewport
            await page.evaluate(
                f"() => {{ "
                f"Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}}); "
                f"window.outerWidth = {viewport['width']}; "
                f"window.outerHeight = {viewport['height']}; "
                f"}}"
            )

            # Random delay to mimic human behavior
            await asyncio.sleep(random.uniform(1.0, 3.0))

            # Wait for content to load with timeout
            await page.wait_for_element("body", timeout=10)

            # Execute JavaScript to get comprehensive content
            content = await page.evaluate(
                """
                () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style');
                    scripts.forEach(el => el.remove());

                    // Get text content
                    const bodyText = document.body ? document.body.innerText : '';
                    const title = document.title || '';

                    return {
                        title: title,
                        content: bodyText,
                        url: window.location.href
                    };
                }
            """
            )

            if content and content.get("content"):
                result_content = (
                    f"Title: {content.get('title', '')}\n\n{content.get('content', '')}"
                )
                return result_content.strip()

            return None

        except Exception as e:
            logger.warning(f"NoDriver scraping error for {url}: {e}")
            return None
        finally:
            if browser:
                try:
                    await browser.stop()
                except Exception as e:
                    logger.debug(f"Error closing browser: {e}")

    async def scrape_with_retry(
        self, url: str, context: str = "", max_retries: int = 2
    ) -> Optional[str]:
        """Scrape with retry logic."""
        for attempt in range(max_retries + 1):
            try:
                result = await self.scrape_with_nodriver(url, context)
                if result:
                    return result

                if attempt < max_retries:
                    wait_time = (attempt + 1) * 2
                    logger.info(
                        f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)

            except Exception as e:
                logger.warning(f"NoDriver attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep((attempt + 1) * 2)

        return None
