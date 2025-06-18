"""
Refactored Dynamic Web Search and Scraping System using modular components.
"""

import asyncio
from typing import Dict, List, Optional
from app.logger import logger
from app.search.intelligent_scraper import IntelligentScraper
from .engines import MultiEngineSearcher, ContentAggregator


class DynamicWebSearcher:
    """
    Refactored dynamic web searcher using modular components.
    Performs real web searches, discovers links, and scrapes content intelligently.
    """

    def __init__(self, llm=None):
        self.llm = llm
        self.current_query = ""
        
        # Initialize modular components
        self.searcher = MultiEngineSearcher()
        self.intelligent_scraper = IntelligentScraper(llm=llm)
        self.content_aggregator = ContentAggregator(self.intelligent_scraper)

    async def search_and_scrape(self, query: str, max_results: int = 10, 
                               engines: List[str] = None) -> List[Dict]:
        """
        Main method: search for query, find relevant links, and scrape content
        """
        logger.info(f"🔍 Starting dynamic web search for: {query}")
        self.current_query = query

        try:
            # Step 1: Perform web search
            search_results = await self.searcher.search(query, engines)
            
            if not search_results:
                logger.warning("No search results found")
                return []

            # Limit results to max_results
            limited_results = search_results[:max_results]
            logger.info(f"📋 Found {len(limited_results)} search results to process")

            # Step 2: Scrape content from search results
            scraped_results = await self.content_aggregator.scrape_multiple_links(
                limited_results, query
            )

            # Step 3: Return comprehensive results
            return scraped_results

        except Exception as e:
            logger.error(f"Error in search_and_scrape: {e}")
            return []

    async def search_and_aggregate(self, query: str, max_results: int = 10,
                                  engines: List[str] = None, keywords: List[str] = None) -> Dict:
        """
        Search and return aggregated content summary.
        """
        logger.info(f"🔍 Starting aggregated search for: {query}")
        
        try:
            # Get scraped results
            scraped_results = await self.search_and_scrape(query, max_results, engines)
            
            # Aggregate content
            aggregated = self.content_aggregator.aggregate_content(scraped_results, query)
            
            # Filter by keywords if provided
            if keywords:
                aggregated = self.content_aggregator.filter_relevant_content(aggregated, keywords)
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error in search_and_aggregate: {e}")
            return {
                "query": query,
                "error": str(e),
                "total_sources": 0,
                "successful_scrapes": 0,
                "failed_scrapes": 0,
                "combined_content": "",
                "sources": [],
                "summary": f"Search failed: {e}"
            }

    async def quick_search(self, query: str, max_results: int = 5) -> str:
        """
        Quick search that returns a simple text summary.
        """
        try:
            aggregated = await self.search_and_aggregate(query, max_results)
            
            if aggregated.get("successful_scrapes", 0) > 0:
                return aggregated.get("combined_content", "No content found")
            else:
                # Fall back to search snippets if scraping failed
                search_results = await self.searcher.search(query)
                if search_results:
                    snippets = []
                    for result in search_results[:max_results]:
                        title = result.get("title", "")
                        snippet = result.get("snippet", "")
                        url = result.get("url", "")
                        if snippet:
                            snippets.append(f"{title}: {snippet} ({url})")
                    
                    return "\n\n".join(snippets) if snippets else "No results found"
                else:
                    return "No search results found"
                    
        except Exception as e:
            logger.error(f"Error in quick_search: {e}")
            return f"Search error: {e}"

    async def search_specific_sites(self, query: str, sites: List[str], 
                                   max_results_per_site: int = 3) -> Dict:
        """
        Search within specific sites using site: operator.
        """
        all_results = []
        
        try:
            for site in sites:
                site_query = f"site:{site} {query}"
                logger.info(f"Searching in {site}: {site_query}")
                
                # Search with site restriction
                site_results = await self.searcher.search(site_query)
                
                # Limit results per site
                limited_site_results = site_results[:max_results_per_site]
                
                # Add site information to results
                for result in limited_site_results:
                    result["target_site"] = site
                
                all_results.extend(limited_site_results)
            
            if all_results:
                # Scrape content from all site-specific results
                scraped_results = await self.content_aggregator.scrape_multiple_links(
                    all_results, query
                )
                
                # Aggregate results
                aggregated = self.content_aggregator.aggregate_content(scraped_results, query)
                aggregated["search_type"] = "site_specific"
                aggregated["target_sites"] = sites
                
                return aggregated
            else:
                return {
                    "query": query,
                    "search_type": "site_specific",
                    "target_sites": sites,
                    "total_sources": 0,
                    "successful_scrapes": 0,
                    "combined_content": "No results found in specified sites",
                    "summary": f"No results found for '{query}' in sites: {', '.join(sites)}"
                }
                
        except Exception as e:
            logger.error(f"Error in search_specific_sites: {e}")
            return {
                "query": query,
                "search_type": "site_specific",
                "target_sites": sites,
                "error": str(e),
                "summary": f"Site-specific search failed: {e}"
            }

    def get_search_stats(self) -> Dict:
        """Get statistics about the search components."""
        return {
            "current_query": self.current_query,
            "llm_available": self.llm is not None,
            "components": {
                "searcher": self.searcher is not None,
                "intelligent_scraper": self.intelligent_scraper is not None,
                "content_aggregator": self.content_aggregator is not None,
            },
            "search_engines": list(self.searcher.adapters.keys()) if self.searcher else []
        }

    async def close(self):
        """Clean up resources."""
        try:
            if self.intelligent_scraper:
                await self.intelligent_scraper.close()
        except Exception as e:
            logger.debug(f"Error closing intelligent scraper: {e}")


# Convenience function for backward compatibility
async def dynamic_web_search(query: str, llm=None, max_results: int = 10) -> List[Dict]:
    """
    Standalone function for dynamic web search (backward compatibility).
    """
    searcher = DynamicWebSearcher(llm)
    try:
        return await searcher.search_and_scrape(query, max_results)
    finally:
        await searcher.close()
