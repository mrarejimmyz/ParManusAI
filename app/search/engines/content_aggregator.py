"""
Content aggregation and processing for search results.
"""

import asyncio
from typing import Dict, List, Optional

from app.logger import logger


class ContentAggregator:
    """Handles aggregation and processing of scraped content."""

    def __init__(self, intelligent_scraper):
        self.intelligent_scraper = intelligent_scraper

    async def scrape_multiple_links(
        self, links: List[Dict], query: str = ""
    ) -> List[Dict]:
        """Scrape content from multiple links concurrently."""
        logger.info(f"📄 Scraping content from {len(links)} links...")

        # Limit concurrent scraping to avoid overwhelming servers
        semaphore = asyncio.Semaphore(3)

        async def scrape_single_with_context(link_info):
            async with semaphore:
                url = link_info.get("url", "")
                if not url:
                    return None

                try:
                    # Use the intelligent scraper with query context
                    content = await self.intelligent_scraper.intelligent_scrape(
                        url, query
                    )

                    if content and len(content.strip()) > 100:
                        return {
                            "url": url,
                            "title": link_info.get("title", ""),
                            "snippet": link_info.get("snippet", ""),
                            "content": content,
                            "source": link_info.get("source", ""),
                            "scraped": True,
                        }
                    else:
                        logger.warning(f"Insufficient content from {url}")
                        return {
                            "url": url,
                            "title": link_info.get("title", ""),
                            "snippet": link_info.get("snippet", ""),
                            "content": link_info.get("snippet", ""),
                            "source": link_info.get("source", ""),
                            "scraped": False,
                        }

                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    return {
                        "url": url,
                        "title": link_info.get("title", ""),
                        "snippet": link_info.get("snippet", ""),
                        "content": link_info.get("snippet", ""),
                        "source": link_info.get("source", ""),
                        "scraped": False,
                        "error": str(e),
                    }

        # Execute scraping tasks
        tasks = [scrape_single_with_context(link) for link in links]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        valid_results = []
        for result in results:
            if result is not None and not isinstance(result, Exception):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraping task failed: {result}")

        successful_scrapes = sum(1 for r in valid_results if r.get("scraped", False))
        logger.info(
            f"✅ Successfully scraped {successful_scrapes}/{len(valid_results)} links"
        )

        return valid_results

    def aggregate_content(self, scraped_results: List[Dict], query: str = "") -> Dict:
        """Aggregate content from scraped results into a comprehensive summary."""
        try:
            all_content = []
            successful_scrapes = []
            failed_scrapes = []

            for result in scraped_results:
                if result.get("scraped", False) and result.get("content"):
                    successful_scrapes.append(result)
                    content = result["content"]
                    title = result.get("title", "")
                    url = result.get("url", "")

                    # Format content with source attribution
                    formatted_content = f"Source: {title} ({url})\n{content}\n"
                    all_content.append(formatted_content)
                else:
                    failed_scrapes.append(result)

            # Combine all content
            combined_content = "\n" + "=" * 50 + "\n".join(all_content)

            return {
                "query": query,
                "total_sources": len(scraped_results),
                "successful_scrapes": len(successful_scrapes),
                "failed_scrapes": len(failed_scrapes),
                "combined_content": combined_content,
                "sources": successful_scrapes,
                "failed_sources": failed_scrapes,
                "summary": self._create_summary(successful_scrapes, query),
            }

        except Exception as e:
            logger.error(f"Error aggregating content: {e}")
            return {
                "query": query,
                "total_sources": len(scraped_results),
                "successful_scrapes": 0,
                "failed_scrapes": len(scraped_results),
                "combined_content": "",
                "sources": [],
                "failed_sources": scraped_results,
                "summary": f"Error aggregating content: {e}",
            }

    def _create_summary(self, successful_scrapes: List[Dict], query: str) -> str:
        """Create a summary of the aggregated content."""
        if not successful_scrapes:
            return "No content was successfully scraped."

        total_chars = sum(
            len(result.get("content", "")) for result in successful_scrapes
        )
        sources = [result.get("title", "Unknown") for result in successful_scrapes]

        summary = f"""
Search Results Summary for: "{query}"

Sources found: {len(successful_scrapes)}
Total content: {total_chars:,} characters

Sources:
""" + "\n".join(
            f"- {source}" for source in sources
        )

        return summary.strip()

    def filter_relevant_content(
        self, aggregated_results: Dict, keywords: List[str] = None
    ) -> Dict:
        """Filter content based on relevance to keywords."""
        if not keywords:
            return aggregated_results

        try:
            relevant_sources = []
            keywords_lower = [k.lower() for k in keywords]

            for source in aggregated_results.get("sources", []):
                content = source.get("content", "").lower()
                title = source.get("title", "").lower()

                # Check if any keyword appears in title or content
                relevance_score = 0
                for keyword in keywords_lower:
                    if keyword in title:
                        relevance_score += 2  # Title matches are more important
                    if keyword in content:
                        relevance_score += 1

                if relevance_score > 0:
                    source["relevance_score"] = relevance_score
                    relevant_sources.append(source)

            # Sort by relevance score
            relevant_sources.sort(
                key=lambda x: x.get("relevance_score", 0), reverse=True
            )

            # Create filtered results
            filtered_results = aggregated_results.copy()
            filtered_results["sources"] = relevant_sources
            filtered_results["filtered_by"] = keywords
            filtered_results["original_source_count"] = len(
                aggregated_results.get("sources", [])
            )
            filtered_results["filtered_source_count"] = len(relevant_sources)

            return filtered_results

        except Exception as e:
            logger.error(f"Error filtering content: {e}")
            return aggregated_results
