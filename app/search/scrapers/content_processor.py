"""
Content processing utilities for scraped content enhancement and cleanup.
"""

import re
from typing import Optional

from app.logger import logger


class ContentProcessor:
    """Handles content processing and enhancement."""

    def __init__(self, llm=None):
        self.llm = llm

    async def process_content(self, content: str, url: str, context: str = "") -> str:
        """Process and enhance scraped content."""
        if not content or len(content.strip()) < 50:
            return content

        try:
            # Basic cleaning
            cleaned_content = self._clean_text(content)

            # LLM enhancement if available and context provided
            if self.llm and context and len(cleaned_content) > 200:
                enhanced_content = await self._llm_enhance_content(
                    cleaned_content, context, url
                )
                if (
                    enhanced_content
                    and len(enhanced_content) > len(cleaned_content) * 0.5
                ):
                    return enhanced_content

            return cleaned_content

        except Exception as e:
            logger.warning(f"Error processing content: {e}")
            return content

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

    async def _llm_enhance_content(
        self, content: str, context: str, url: str
    ) -> Optional[str]:
        """Use LLM to enhance and summarize content based on context."""
        if not self.llm:
            return None

        try:
            # Truncate content if too long for LLM processing
            max_content_length = 8000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."

            prompt = f"""Extract and summarize the most relevant information from this web content based on the context.

Context: {context}

Web Content from {url}:
{content}

Please provide a concise summary that focuses on information relevant to the context. Include:
1. Key facts and data points
2. Important quotes or statements
3. Relevant details that answer the context query
4. Proper attribution to the source

Format the response as clean, readable text without unnecessary formatting."""

            response = await self.llm.generate(prompt)

            if response and len(response.strip()) > 50:
                return f"Enhanced summary from {url}:\n\n{response.strip()}"

            return None

        except Exception as e:
            logger.warning(f"LLM content enhancement failed: {e}")
            return None

    def extract_structured_data(self, content: str) -> dict:
        """Extract structured data from content."""
        data = {
            "title": "",
            "headings": [],
            "links": [],
            "images": [],
            "tables": [],
        }

        try:
            # Extract title (look for title-like patterns)
            title_match = re.search(r"Title:\s*(.+)", content)
            if title_match:
                data["title"] = title_match.group(1).strip()

            # Extract headings (look for heading-like patterns)
            headings = re.findall(r"^([A-Z][A-Za-z\s]+):?\s*$", content, re.MULTILINE)
            data["headings"] = [h.strip() for h in headings if len(h.strip()) > 3]

            # Extract URLs
            urls = re.findall(r"https?://[^\s]+", content)
            data["links"] = list(set(urls))  # Remove duplicates

            return data

        except Exception as e:
            logger.warning(f"Error extracting structured data: {e}")
            return data
