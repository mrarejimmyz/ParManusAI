"""
HTTP-based scraping strategies using aiohttp with stealth features.
"""

import random
import re
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

from app.logger import logger


class HttpScraper:
    """Handles HTTP-based scraping with stealth features."""

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    async def scrape_with_stealth_aiohttp(
        self, url: str, context: str = ""
    ) -> Optional[str]:
        """
        Scrape using stealth aiohttp with randomized headers
        """
        try:
            headers = self._get_stealth_headers()

            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(
                timeout=timeout, headers=headers
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content_type = response.headers.get("content-type", "").lower()

                        if "application/pdf" in content_type:
                            return await self._handle_pdf_content(
                                response, url, context
                            )
                        elif "xml" in content_type:
                            text = await response.text()
                            return await self._process_xml_content(text, url, context)
                        else:
                            text = await response.text()
                            return await self._process_html_content(text, url, context)
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None

        except Exception as e:
            logger.warning(f"Stealth aiohttp error for {url}: {e}")
            return None

    async def basic_scrape_fallback(self, url: str) -> Optional[str]:
        """
        Basic scraping fallback without special anti-detection
        """
        try:
            headers = {"User-Agent": random.choice(self.user_agents)}

            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        text = await response.text()
                        soup = BeautifulSoup(text, "html.parser")

                        # Remove scripts and styles
                        for element in soup(["script", "style"]):
                            element.decompose()

                        # Get clean text
                        clean_text = soup.get_text()
                        clean_text = self._clean_text(clean_text)

                        if len(clean_text.strip()) > 100:
                            return clean_text

                        return None
                    else:
                        logger.warning(
                            f"Basic fallback HTTP {response.status} for {url}"
                        )
                        return None

        except Exception as e:
            logger.warning(f"Basic fallback error for {url}: {e}")
            return None

    def _get_stealth_headers(self) -> dict:
        """Generate stealth headers for HTTP requests."""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }

    async def _process_html_content(
        self, content: str, url: str, context: str = ""
    ) -> str:
        """Process HTML content and extract clean text."""
        try:
            soup = BeautifulSoup(content, "html.parser")

            # Remove unwanted elements
            for element in soup(
                ["script", "style", "nav", "header", "footer", "aside"]
            ):
                element.decompose()

            # Extract title
            title = soup.title.string if soup.title else ""

            # Extract main content
            main_content = ""
            main_tags = soup.find_all(["main", "article", "section", "div"])

            if main_tags:
                for tag in main_tags:
                    text = tag.get_text()
                    if len(text) > len(main_content):
                        main_content = text
            else:
                main_content = soup.get_text()

            # Clean and format
            clean_content = self._clean_text(main_content)

            result = f"Title: {title}\n\n{clean_content}" if title else clean_content
            return result.strip()

        except Exception as e:
            logger.warning(f"Error processing HTML content: {e}")
            return content

    async def _process_xml_content(self, xml: str, url: str, context: str = "") -> str:
        """Process XML content."""
        try:
            # Basic XML processing - extract text content
            soup = BeautifulSoup(xml, "xml")

            # Remove CDATA sections and get text
            text_content = soup.get_text()

            # Clean the text
            clean_content = self._clean_text(text_content)

            return clean_content

        except Exception as e:
            logger.warning(f"Error processing XML content: {e}")
            return xml

    async def _handle_pdf_content(self, response, url: str, context: str = "") -> str:
        """Handle PDF content extraction."""
        try:
            # For now, return a placeholder for PDF content
            # In a full implementation, you might use a PDF parsing library
            return f"PDF document detected at {url}. Content extraction for PDFs is not implemented in this module."

        except Exception as e:
            logger.warning(f"Error handling PDF content: {e}")
            return f"Error processing PDF from {url}: {e}"

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters and normalize
        text = re.sub(r"[^\w\s\-.,!?;:()\[\]{}\"']", " ", text)

        # Remove excessive newlines
        text = re.sub(r"\n\s*\n", "\n\n", text)

        # Limit line length for readability
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if len(line) > 200:
                # Break long lines at sentence boundaries
                sentences = re.split(r"(?<=[.!?])\s+", line)
                current_line = ""

                for sentence in sentences:
                    if len(current_line + sentence) <= 200:
                        current_line += sentence + " "
                    else:
                        if current_line:
                            cleaned_lines.append(current_line.strip())
                        current_line = sentence + " "

                if current_line:
                    cleaned_lines.append(current_line.strip())
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()
