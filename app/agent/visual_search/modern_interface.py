"""
Modern Visual Google Search Interface
LLM-driven modular search system with intelligent reasoning
"""

import asyncio
from typing import Dict, List, Optional

from app.agent.visual_search.crypto_handler import LLMCryptoHandler
from app.agent.visual_search.extraction import LLMContentExtractor
from app.agent.visual_search.navigation import LLMNavigationManager
from app.agent.visual_search.search_operations import LLMSearchOperations
from app.agent.visual_search.types import (
    ExtractionConfig,
    SearchContext,
    SearchResult,
    SearchStrategy,
)
from app.logger import logger


class ModernVisualGoogleSearch:
    """
    Modern visual Google search with LLM-driven reasoning
    Replaces static logic with adaptive, intelligent decision making
    """

    def __init__(self, browser_handler, llm_client=None):
        """Initialize with browser handler and optional LLM client"""
        self.browser = browser_handler
        self.llm = llm_client

        # Initialize modular components
        self.navigator = LLMNavigationManager(browser_handler, llm_client)
        self.search_ops = LLMSearchOperations(browser_handler, llm_client)
        self.extractor = LLMContentExtractor(browser_handler, llm_client)
        self.crypto_handler = LLMCryptoHandler(llm_client)

        logger.info("🚀 Initialized modern visual search with LLM-driven reasoning")

    async def perform_intelligent_search(self, query: str, **kwargs) -> Dict:
        """
        Perform intelligent search using LLM reasoning throughout the process

        Args:
            query: Search query
            **kwargs: Additional configuration options

        Returns:
            Dict with search results and metadata
        """
        logger.info(f"🧠 Starting intelligent search: {query}")

        # Create search context with LLM analysis
        context = await self._create_search_context(query, **kwargs)

        try:
            # Step 1: Intelligent navigation
            nav_result = await self.navigator.navigate_with_reasoning(context)
            if not nav_result.success:
                return {
                    "success": False,
                    "error": f"Navigation failed: {nav_result.error}",
                    "stage": "navigation",
                }

            # Step 2: Adaptive search execution
            search_result = await self.search_ops.perform_intelligent_search(context)
            if not search_result["success"]:
                return {
                    "success": False,
                    "error": f"Search failed: {search_result['error']}",
                    "stage": "search",
                }

            # Step 3: Intelligent content extraction
            extraction_config = await self._create_extraction_config(query, context)
            results = await self.extractor.extract_search_results(extraction_config)

            # Step 4: Post-process results with LLM reasoning
            processed_results = await self._post_process_results(
                results, query, context
            )

            return {
                "success": True,
                "query": query,
                "results": processed_results,
                "metadata": {
                    "search_context": context,
                    "extraction_method": extraction_config.extraction_method,
                    "total_results": len(processed_results),
                },
            }

        except Exception as e:
            logger.error(f"❌ Intelligent search failed: {str(e)}")
            return {"success": False, "error": str(e), "stage": "execution"}

    async def _create_search_context(self, query: str, **kwargs) -> SearchContext:
        """Create search context with LLM analysis"""
        if self.llm:
            # Let LLM analyze query and determine optimal context
            context_prompt = f"""
            Analyze this search query and determine optimal search parameters: "{query}"

            Consider:
            - Query complexity and type (informational, navigational, commercial)
            - Expected result count needed
            - Timeout requirements based on complexity
            - Any special filters or preferences

            Return JSON with:
            - max_results: recommended number of results (5-20)
            - timeout: recommended timeout in seconds (10-60)
            - preferred_strategy: "DIRECT_URL" | "WEB_SEARCH" | "MANUAL_INTERACTION" | "LLM_GUIDED"
            - retry_attempts: number of retries (1-5)
            - filters: any special considerations
            """

            try:
                response = await self.llm.generate_response(context_prompt)
                import json

                llm_context = json.loads(response)

                return SearchContext(
                    query=query,
                    max_results=llm_context.get("max_results", 10),
                    timeout=llm_context.get("timeout", 30.0),
                    retry_attempts=llm_context.get("retry_attempts", 3),
                    preferred_strategy=SearchStrategy(
                        llm_context.get("preferred_strategy", "DIRECT_URL")
                    ),
                    filters=llm_context.get("filters"),
                )
            except Exception as e:
                logger.warning(f"LLM context creation failed: {e}")

        # Fallback context creation
        return SearchContext(
            query=query,
            max_results=kwargs.get("max_results", 10),
            timeout=kwargs.get("timeout", 30.0),
            retry_attempts=kwargs.get("retry_attempts", 3),
            preferred_strategy=kwargs.get("strategy", SearchStrategy.DIRECT_URL),
        )

    async def _create_extraction_config(
        self, query: str, context: SearchContext
    ) -> ExtractionConfig:
        """Create extraction configuration with LLM guidance"""
        if self.llm:
            # Let LLM determine extraction strategy
            extraction_prompt = f"""
            Determine optimal content extraction strategy for query: "{query}"

            Consider:
            - What type of content is expected (text, data, links, etc.)
            - How structured the output should be
            - Whether this is crypto/financial data, news, general info, etc.
            - What elements are most important to extract

            Return JSON with:
            - target_elements: array of element types to focus on
            - extraction_method: "llm_guided" | "pattern_based" | "hybrid"
            - structured_output: true/false
            - include_metadata: true/false
            - max_content_length: number (1000-10000)
            """

            try:
                response = await self.llm.generate_response(extraction_prompt)
                import json

                llm_config = json.loads(response)

                return ExtractionConfig(
                    target_elements=llm_config.get(
                        "target_elements", ["title", "url", "snippet"]
                    ),
                    extraction_method=llm_config.get("extraction_method", "llm_guided"),
                    structured_output=llm_config.get("structured_output", True),
                    include_metadata=llm_config.get("include_metadata", False),
                    max_content_length=llm_config.get("max_content_length", 5000),
                )
            except Exception as e:
                logger.warning(f"LLM extraction config failed: {e}")

        # Fallback configuration
        return ExtractionConfig(
            target_elements=["title", "url", "snippet"],
            extraction_method="llm_guided" if self.llm else "pattern_based",
            structured_output=True,
            include_metadata=False,
            max_content_length=5000,
        )

    async def _post_process_results(
        self, results: List[SearchResult], query: str, context: SearchContext
    ) -> List[Dict]:
        """Post-process results with LLM reasoning"""
        if not results:
            return []

        # Check if this appears to be crypto-related
        if await self._is_crypto_query(query):
            logger.info("🪙 Detected crypto query, using specialized handler")
            # Extract content for crypto analysis
            raw_content = await self._get_page_content_for_crypto()
            if raw_content:
                crypto_results = await self.crypto_handler.extract_crypto_data(
                    raw_content, query
                )
                if crypto_results:
                    results = crypto_results

        # Convert results to dictionary format with LLM enhancement
        processed_results = []

        for result in results:
            result_dict = {
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "rank": result.rank,
            }

            # Add confidence and metadata if available
            if result.confidence is not None:
                result_dict["confidence"] = result.confidence
            if result.metadata:
                result_dict["metadata"] = result.metadata

            processed_results.append(result_dict)

        # LLM-driven result ranking and filtering
        if self.llm and len(processed_results) > 1:
            processed_results = await self._llm_rank_results(processed_results, query)

        logger.info(f"✅ Post-processed {len(processed_results)} results")
        return processed_results

    async def _is_crypto_query(self, query: str) -> bool:
        """Determine if query is crypto-related using LLM"""
        if self.llm:
            crypto_prompt = f"""
            Determine if this search query is related to cryptocurrency:

            Query: "{query}"

            Return JSON: {{"is_crypto": true/false, "confidence": 0.0-1.0}}
            """

            try:
                response = await self.llm.generate_response(crypto_prompt)
                import json

                result = json.loads(response)
                return result.get("is_crypto", False)
            except:
                pass

        # Fallback detection
        crypto_keywords = [
            "crypto",
            "bitcoin",
            "ethereum",
            "cryptocurrency",
            "btc",
            "eth",
            "coinmarketcap",
            "market cap",
            "blockchain",
            "altcoin",
            "defi",
            "nft",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in crypto_keywords)

    async def _get_page_content_for_crypto(self) -> Optional[str]:
        """Get page content for crypto analysis"""
        try:
            extract_result = await self.browser.execute(
                action="extract_content",
                goal="Extract cryptocurrency data, prices, and market information",
            )
            return extract_result.output if not extract_result.error else None
        except Exception as e:
            logger.warning(f"Failed to get page content for crypto: {e}")
            return None

    async def _llm_rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Use LLM to rank and filter results by relevance"""
        ranking_prompt = f"""
        Rank these search results by relevance to the query: "{query}"

        Results: {results[:5]}  # Limit for context

        Return the results reordered by relevance, with the most relevant first.
        You can also filter out clearly irrelevant results.

        Return JSON array of results in order of relevance.
        """

        try:
            response = await self.llm.generate_response(ranking_prompt)
            import json

            ranked_results = json.loads(response)

            # Ensure we have valid results
            if isinstance(ranked_results, list) and ranked_results:
                logger.info("🎯 LLM ranked results by relevance")
                return ranked_results
        except Exception as e:
            logger.warning(f"LLM ranking failed: {e}")

        # Return original results if ranking fails
        return results

    async def visit_search_result(self, url: str) -> Dict:
        """Visit a specific search result URL and extract content"""
        logger.info(f"🔗 Visiting search result: {url}")

        try:
            # Navigate to URL
            nav_result = await self.browser.execute(action="go_to_url", url=url)

            if nav_result.error:
                return {"success": False, "error": nav_result.error}

            await asyncio.sleep(3)  # Allow page to load

            # Extract content with LLM guidance
            if self.llm:
                goal = await self._generate_visit_extraction_goal(url)
            else:
                goal = "Extract relevant information from this webpage"

            content_result = await self.browser.execute(
                action="extract_content", goal=goal
            )

            return {"success": True, "url": url, "content": content_result.output}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_visit_extraction_goal(self, url: str) -> str:
        """Generate LLM-guided extraction goal for visiting URLs"""
        goal_prompt = f"""
        Create an extraction goal for visiting this URL: {url}

        Consider:
        - What type of site this appears to be
        - What information would be most valuable to extract
        - How to focus on the main content vs navigation/ads

        Return a clear, specific extraction goal (one sentence).
        """

        try:
            goal = await self.llm.generate_response(goal_prompt)
            return goal.strip().strip('"')
        except:
            return "Extract the main content and key information from this webpage"

    async def close(self) -> None:
        """Cleanup resources"""
        logger.info("🧹 Cleaning up modern visual search resources")
        try:
            await self.browser.close()
        except Exception as e:
            logger.error(f"❌ Failed to close browser: {str(e)}")


# Backward compatibility wrapper
class VisualGoogleSearch:
    """Backward compatibility wrapper for existing code"""

    def __init__(self, browser_handler):
        # Initialize the modern implementation
        self.modern_search = ModernVisualGoogleSearch(browser_handler)
        self.browser = browser_handler

    async def perform_visual_google_search(self, query: str) -> Dict:
        """Backward compatible search method"""
        result = await self.modern_search.perform_intelligent_search(query)
        return result

    async def close(self) -> None:
        """Cleanup resources"""
        await self.modern_search.close()
