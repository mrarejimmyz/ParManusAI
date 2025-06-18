"""
Refactored Intelligent Web Scraper using modular components.
"""

import asyncio
from typing import Optional
from app.logger import logger
from .scrapers import NoDriverScraper, HttpScraper, ContentProcessor


class IntelligentScraper:
    """
    Refactored intelligent web scraper using modular components.
    Coordinates different scraping strategies for optimal results.
    """

    def __init__(self, llm=None):
        self.llm = llm
        
        # Initialize scraping modules
        self.nodriver_scraper = NoDriverScraper()
        self.http_scraper = HttpScraper()
        self.content_processor = ContentProcessor(llm)

    async def intelligent_scrape(
        self, url: str, context: str = "", retry_count: int = 3
    ) -> Optional[str]:
        """
        Main intelligent scraping method with fallback strategies
        """
        logger.info(f"🔍 Starting intelligent scrape of: {url}")

        # Strategy 1: Try nodriver (best for anti-bot detection)
        try:
            content = await self.nodriver_scraper.scrape_with_retry(url, context, max_retries=1)
            if content:
                logger.info(f"✅ NoDriver scraping successful for {url}")
                processed_content = await self.content_processor.process_content(content, url, context)
                return processed_content
        except Exception as e:
            logger.warning(f"NoDriver scraping failed for {url}: {e}")

        # Strategy 2: Try stealth aiohttp with random headers
        try:
            content = await self.http_scraper.scrape_with_stealth_aiohttp(url, context)
            if content:
                logger.info(f"✅ Stealth aiohttp scraping successful for {url}")
                processed_content = await self.content_processor.process_content(content, url, context)
                return processed_content
        except Exception as e:
            logger.warning(f"Stealth aiohttp scraping failed for {url}: {e}")

        # Strategy 3: Basic fallback
        try:
            content = await self.http_scraper.basic_scrape_fallback(url)
            if content:
                logger.info(f"✅ Basic fallback scraping successful for {url}")
                processed_content = await self.content_processor.process_content(content, url, context)
                return processed_content
        except Exception as e:
            logger.warning(f"Basic fallback scraping failed for {url}: {e}")

        logger.error(f"❌ All scraping strategies failed for {url}")
        return None

    async def scrape_multiple_urls(self, urls: list, context: str = "") -> dict:
        """Scrape multiple URLs concurrently."""
        results = {}
        
        # Limit concurrent requests to avoid overwhelming servers
        semaphore = asyncio.Semaphore(3)
        
        async def scrape_single(url):
            async with semaphore:
                try:
                    result = await self.intelligent_scrape(url, context)
                    return url, result
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    return url, None

        # Execute all scraping tasks concurrently
        tasks = [scrape_single(url) for url in urls]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for task_result in completed_tasks:
            if isinstance(task_result, tuple):
                url, content = task_result
                results[url] = content
            else:
                logger.error(f"Scraping task failed: {task_result}")
        
        return results

    def get_scraping_stats(self) -> dict:
        """Get statistics about scraping operations."""
        return {
            "strategies_available": ["nodriver", "stealth_http", "basic_fallback"],
            "llm_enhancement": self.llm is not None,
            "modules_loaded": {
                "nodriver_scraper": self.nodriver_scraper is not None,
                "http_scraper": self.http_scraper is not None,
                "content_processor": self.content_processor is not None,
            }
        }

    async def close(self):
        """Clean up resources if needed."""
        # Currently no persistent resources to clean up
        # But this method is available for future use
        pass


# Convenience function for backward compatibility
async def intelligent_scrape(url: str, context: str = "", llm=None) -> Optional[str]:
    """
    Standalone function for intelligent scraping (backward compatibility).
    """
    scraper = IntelligentScraper(llm)
    try:
        return await scraper.intelligent_scrape(url, context)
    finally:
        await scraper.close()
