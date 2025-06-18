"""
Intelligent Web Scraper using NoDriver Technology
Bypasses anti-bot detection and handles various content types robustly
"""

import asyncio
import json
import mimetypes
import random
import re
import time
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import nodriver as uc
from bs4 import BeautifulSoup

from app.logger import logger


class IntelligentScraper:
    """
    Advanced web scraper using nodriver technology to bypass bot detection
    """

    def __init__(self, llm=None):
        self.llm = llm
        self.session = None
        self.browser = None
        self.page = None

        # Anti-detection configurations
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

    async def intelligent_scrape(
        self, url: str, context: str = "", retry_count: int = 3
    ) -> Optional[str]:
        """
        Main intelligent scraping method with fallback strategies
        """
        logger.info(f"🔍 Starting intelligent scrape of: {url}")

        # Strategy 1: Try nodriver (best for anti-bot detection)
        try:
            content = await self._scrape_with_nodriver(url, context)
            if content:
                logger.info(f"✅ NoDriver scraping successful for {url}")
                return content
        except Exception as e:
            logger.warning(f"NoDriver scraping failed for {url}: {e}")

        # Strategy 2: Try stealth aiohttp with random headers
        try:
            content = await self._scrape_with_stealth_aiohttp(url, context)
            if content:
                logger.info(f"✅ Stealth aiohttp scraping successful for {url}")
                return content
        except Exception as e:
            logger.warning(f"Stealth aiohttp scraping failed for {url}: {e}")

        # Strategy 3: Basic fallback
        try:
            content = await self._basic_scrape_fallback(url)
            if content:
                logger.info(f"✅ Basic fallback scraping successful for {url}")
                return content
        except Exception as e:
            logger.warning(f"Basic fallback scraping failed for {url}: {e}")

        logger.error(f"❌ All scraping strategies failed for {url}")
        return None

    async def _scrape_with_nodriver(self, url: str, context: str = "") -> Optional[str]:
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
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                f"--user-agent={user_agent}",
                f"--window-size={viewport['width']},{viewport['height']}",
            ]

            browser = await uc.start(
                headless=True,
                sandbox=False,
                browser_args=browser_args,
                lang="en-US",
            )

            # Get the main tab
            tab = browser.main_tab

            # Add random delay to mimic human behavior
            await asyncio.sleep(random.uniform(0.5, 2.0))

            # Navigate to the page
            await tab.get(url)

            # Wait for content to load
            await asyncio.sleep(random.uniform(1, 3))

            # Get page content
            content = await tab.get_content()

            # Process content based on type
            processed_content = await self._process_content(content, url, context)

            return processed_content

        except Exception as e:
            logger.error(f"NoDriver scraping error for {url}: {e}")
            return None
        finally:
            if browser:
                try:
                    browser.stop()
                except:
                    pass

    async def _scrape_with_stealth_aiohttp(
        self, url: str, context: str = ""
    ) -> Optional[str]:
        """
        Scrape using aiohttp with stealth headers and anti-detection measures
        """
        try:
            # Random headers to avoid detection
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }

            # Add referrer for some sites
            parsed_url = urlparse(url)
            if parsed_url.netloc:
                headers["Referer"] = f"https://{parsed_url.netloc}/"

            # Random delay
            await asyncio.sleep(random.uniform(0.5, 2.0))

            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(
                headers=headers, timeout=timeout
            ) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        # Detect content type
                        content_type = response.headers.get("content-type", "").lower()

                        if "json" in content_type:
                            content = await response.json()
                            return await self._process_json_content(
                                content, url, context
                            )
                        elif "xml" in content_type:
                            text = await response.text()
                            return await self._process_xml_content(text, url, context)
                        elif "pdf" in content_type:
                            # Handle PDF content
                            return await self._handle_pdf_content(
                                response, url, context
                            )
                        else:
                            # HTML content
                            text = await response.text()
                            return await self._process_html_content(text, url, context)
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None

        except Exception as e:
            logger.error(f"Stealth aiohttp scraping error for {url}: {e}")
            return None

    async def _basic_scrape_fallback(self, url: str) -> Optional[str]:
        """
        Basic fallback scraping method
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(
                headers=headers, timeout=timeout
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, "html.parser")

                        # Remove script and style elements
                        for script in soup(
                            ["script", "style", "nav", "footer", "header"]
                        ):
                            script.decompose()

                        # Get text content
                        text = soup.get_text()

                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (
                            phrase.strip()
                            for line in lines
                            for phrase in line.split("  ")
                        )
                        text = " ".join(chunk for chunk in chunks if chunk)

                        return text[:5000] if text else None

        except Exception as e:
            logger.error(f"Basic fallback scraping error for {url}: {e}")
            return None

    async def _process_content(self, content: str, url: str, context: str = "") -> str:
        """
        Process and clean scraped content based on type
        """
        try:
            # Detect content type and process accordingly
            if content.strip().startswith("<!DOCTYPE html") or "<html" in content:
                return await self._process_html_content(content, url, context)
            elif content.strip().startswith("{") or content.strip().startswith("["):
                try:
                    json_content = json.loads(content)
                    return await self._process_json_content(json_content, url, context)
                except:
                    # If JSON parsing fails, treat as text
                    return await self._process_text_content(content, url, context)
            elif content.strip().startswith("<?xml"):
                return await self._process_xml_content(content, url, context)
            else:
                return await self._process_text_content(content, url, context)

        except Exception as e:
            logger.error(f"Content processing error for {url}: {e}")
            return content[:5000] if content else ""

    async def _process_html_content(
        self, html: str, url: str, context: str = ""
    ) -> str:
        """
        Process HTML content and extract meaningful text
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for element in soup(
                [
                    "script",
                    "style",
                    "nav",
                    "footer",
                    "header",
                    "aside",
                    "iframe",
                    "noscript",
                ]
            ):
                element.decompose()

            # Try to find main content areas first
            main_content = None
            content_selectors = [
                "main",
                "article",
                '[role="main"]',
                ".content",
                ".main-content",
                ".post-content",
                ".entry-content",
                ".article-content",
                ".page-content",
            ]

            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if main_content:
                # Extract text from main content area
                text = main_content.get_text(separator=" ", strip=True)
            else:
                # Fallback: extract text from body
                body = soup.find("body")
                if body:
                    text = body.get_text(separator=" ", strip=True)
                else:
                    text = soup.get_text(separator=" ", strip=True)

            # Clean up the text
            text = self._clean_text(text)

            # If we have LLM and context, use it for intelligent extraction
            if self.llm and context and text:
                text = await self._llm_enhance_content(text, context, url)

            return text[:8000] if text else ""

        except Exception as e:
            logger.error(f"HTML processing error for {url}: {e}")
            return ""

    async def _process_json_content(
        self, json_data: Union[dict, list], url: str, context: str = ""
    ) -> str:
        """
        Process JSON content and extract relevant information
        """
        try:
            # Convert JSON to readable text
            if isinstance(json_data, dict):
                # Look for common content fields
                content_fields = [
                    "content",
                    "text",
                    "description",
                    "body",
                    "message",
                    "data",
                ]
                for field in content_fields:
                    if field in json_data and json_data[field]:
                        return str(json_data[field])[:5000]

                # If no specific content field, return formatted JSON
                return json.dumps(json_data, indent=2)[:5000]

            elif isinstance(json_data, list):
                # Process list of items
                texts = []
                for item in json_data[:10]:  # Limit to first 10 items
                    if isinstance(item, dict):
                        for field in ["content", "text", "description", "title"]:
                            if field in item and item[field]:
                                texts.append(str(item[field]))
                                break
                    else:
                        texts.append(str(item))

                return " ".join(texts)[:5000]

            return str(json_data)[:5000]

        except Exception as e:
            logger.error(f"JSON processing error for {url}: {e}")
            return ""

    async def _process_xml_content(self, xml: str, url: str, context: str = "") -> str:
        """
        Process XML content and extract text
        """
        try:
            soup = BeautifulSoup(xml, "xml")
            text = soup.get_text(separator=" ", strip=True)
            return self._clean_text(text)[:5000]

        except Exception as e:
            logger.error(f"XML processing error for {url}: {e}")
            return ""

    async def _process_text_content(
        self, text: str, url: str, context: str = ""
    ) -> str:
        """
        Process plain text content
        """
        return self._clean_text(text)[:5000]

    async def _handle_pdf_content(self, response, url: str, context: str = "") -> str:
        """
        Handle PDF content (basic implementation)
        """
        try:
            # For now, return a message about PDF detection
            # In a more advanced implementation, you could use PyPDF2 or similar
            return f"PDF document detected at {url}. Content extraction from PDFs requires additional tools."

        except Exception as e:
            logger.error(f"PDF processing error for {url}: {e}")
            return ""

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common noise patterns
        text = re.sub(
            r"(Cookie|Privacy) Policy.*?(?=\.|$)", "", text, flags=re.IGNORECASE
        )
        text = re.sub(
            r"Subscribe.*?newsletter.*?(?=\.|$)", "", text, flags=re.IGNORECASE
        )
        text = re.sub(r"Follow us on.*?(?=\.|$)", "", text, flags=re.IGNORECASE)

        # Remove email addresses and URLs from content
        text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "", text)
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )

        return text.strip()

    async def _llm_enhance_content(self, content: str, context: str, url: str) -> str:
        """
        Use LLM to extract most relevant content based on search context
        """
        try:
            if not self.llm or not content or len(content) < 100:
                return content

            prompt = f"""
            Extract the most relevant information from this web content based on the search context.

            Search Context: {context}
            Source URL: {url}            Content:
            {content[:4000]}

            Please extract and summarize only the most relevant information that relates to the search context.
            Focus on facts, data, and key information. Remove navigation, ads, and irrelevant content.
            Return a clean, focused summary of 2-3 paragraphs maximum.
            """

            try:
                enhanced_content = await self.llm.ask(prompt)

                if enhanced_content and len(enhanced_content.strip()) > 50:
                    return enhanced_content.strip()

            except Exception as llm_error:
                logger.warning(f"LLM enhancement failed: {llm_error}")

            return content

        except Exception as e:
            logger.error(f"LLM enhancement error: {e}")
            return content

    async def close(self):
        """
        Clean up resources
        """
        if self.session:
            await self.session.close()
        if self.browser:
            try:
                await self.browser.stop()
            except:
                pass


# For backward compatibility and direct usage
async def intelligent_scrape(url: str, context: str = "", llm=None) -> Optional[str]:
    """
    Standalone function for intelligent scraping
    """
    scraper = IntelligentScraper(llm=llm)
    try:
        return await scraper.intelligent_scrape(url, context)
    finally:
        await scraper.close()
