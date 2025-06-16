"""
LLM-Driven Search Operations
Replaces static search logic with adaptive reasoning
"""

import asyncio
import urllib.parse
from typing import Dict, List

from app.agent.visual_search.types import SearchContext, SearchResult, SearchStrategy
from app.logger import logger


class LLMSearchOperations:
    """Handles search operations with LLM-guided strategy selection"""

    def __init__(self, browser_handler, llm_client=None):
        self.browser = browser_handler
        self.llm = llm_client

    async def perform_intelligent_search(self, context: SearchContext) -> Dict:
        """Perform search using LLM-determined optimal strategy"""
        logger.info(f"🔍 Starting LLM-guided search for: {context.query}")

        # Let LLM analyze query and determine best search approach
        search_strategy = await self._determine_search_strategy(context)

        # Execute search using determined strategy
        for attempt in range(context.retry_attempts):
            result = await self._execute_search_strategy(
                search_strategy, context, attempt
            )

            if result["success"]:
                return result

            # Let LLM analyze failure and adapt strategy
            if attempt < context.retry_attempts - 1:
                search_strategy = await self._adapt_search_strategy(
                    search_strategy, result, context
                )

        return {
            "success": False,
            "error": "All search strategies failed after LLM analysis",
        }

    async def _determine_search_strategy(self, context: SearchContext) -> Dict:
        """Let LLM determine optimal search strategy"""
        if not self.llm:
            # Fallback strategy selection
            return {
                "primary": SearchStrategy.DIRECT_URL,
                "fallbacks": [
                    SearchStrategy.WEB_SEARCH,
                    SearchStrategy.MANUAL_INTERACTION,
                ],
                "reasoning": "Default strategy selection",
            }

        strategy_prompt = f"""
        Analyze this search query and determine the optimal search strategy: "{context.query}"

        Consider:
        - Query complexity and specificity
        - Likelihood of getting blocked by anti-bot measures
        - Speed vs reliability tradeoffs
        - Content type expected (general web, crypto data, news, etc.)

        Available strategies:
        1. DIRECT_URL: Construct search URL directly
        2. WEB_SEARCH: Use browser's built-in search action
        3. MANUAL_INTERACTION: Simulate human search behavior
        4. LLM_GUIDED: Adaptive approach based on page analysis

        Return JSON with:
        - primary_strategy: the best first choice
        - fallback_strategies: ordered list of alternatives
        - reasoning: explanation for the choice
        - special_considerations: any specific handling needed
        """

        try:
            response = await self.llm.generate_response(strategy_prompt)
            import json

            strategy = json.loads(response)
            return strategy
        except Exception as e:
            logger.warning(f"LLM strategy determination failed: {e}")
            return {
                "primary_strategy": "DIRECT_URL",
                "fallback_strategies": ["WEB_SEARCH", "MANUAL_INTERACTION"],
                "reasoning": f"Fallback due to LLM error: {e}",
            }

    async def _execute_search_strategy(
        self, strategy: Dict, context: SearchContext, attempt: int
    ) -> Dict:
        """Execute the determined search strategy"""
        primary = strategy.get("primary_strategy", "DIRECT_URL")
        fallbacks = strategy.get("fallback_strategies", [])

        # Try primary strategy first, then fallbacks
        strategies_to_try = [primary] + fallbacks
        current_strategy = strategies_to_try[min(attempt, len(strategies_to_try) - 1)]

        logger.info(f"🎯 Executing search strategy: {current_strategy}")

        if current_strategy == "DIRECT_URL":
            return await self._direct_url_search(context)
        elif current_strategy == "WEB_SEARCH":
            return await self._web_search_action(context)
        elif current_strategy == "MANUAL_INTERACTION":
            return await self._manual_search_interaction(context)
        elif current_strategy == "LLM_GUIDED":
            return await self._llm_guided_search(context)
        else:
            return {"success": False, "error": f"Unknown strategy: {current_strategy}"}

    async def _direct_url_search(self, context: SearchContext) -> Dict:
        """Perform search by constructing URL directly"""
        try:
            encoded_query = urllib.parse.quote_plus(context.query)
            search_url = f"https://www.google.com/search?q={encoded_query}&num={context.max_results}"

            nav_result = await self.browser.execute(action="go_to_url", url=search_url)

            if nav_result.error:
                return {
                    "success": False,
                    "error": f"Direct URL navigation failed: {nav_result.error}",
                }

            await asyncio.sleep(2)  # Allow page to load
            return {"success": True, "method": "direct_url"}

        except Exception as e:
            return {"success": False, "error": f"Direct URL search failed: {e}"}

    async def _web_search_action(self, context: SearchContext) -> Dict:
        """Use browser's built-in web search action"""
        try:
            search_result = await self.browser.execute(
                action="web_search", query=context.query
            )

            if search_result.error:
                return {
                    "success": False,
                    "error": f"Web search action failed: {search_result.error}",
                }

            return {"success": True, "method": "web_search"}

        except Exception as e:
            return {"success": False, "error": f"Web search action failed: {e}"}

    async def _manual_search_interaction(self, context: SearchContext) -> Dict:
        """Simulate manual search interaction"""
        try:
            # Navigate to Google homepage
            nav_result = await self.browser.execute(
                action="go_to_url", url="https://www.google.com"
            )

            if nav_result.error:
                return {
                    "success": False,
                    "error": f"Homepage navigation failed: {nav_result.error}",
                }

            await asyncio.sleep(2)

            # Type search query
            type_result = await self.browser.execute(
                action="type_text", text=context.query
            )

            if type_result.error:
                return {
                    "success": False,
                    "error": f"Text input failed: {type_result.error}",
                }

            # Press Enter
            enter_result = await self.browser.execute(action="key_press", key="Return")

            if enter_result.error:
                return {
                    "success": False,
                    "error": f"Enter key failed: {enter_result.error}",
                }

            await asyncio.sleep(3)  # Wait for results
            return {"success": True, "method": "manual_interaction"}

        except Exception as e:
            return {"success": False, "error": f"Manual interaction failed: {e}"}

    async def _llm_guided_search(self, context: SearchContext) -> Dict:
        """Use LLM to guide search process dynamically"""
        if not self.llm:
            # Fallback to direct URL if no LLM
            return await self._direct_url_search(context)

        try:
            # Let LLM analyze current page and determine next steps
            page_analysis = await self._analyze_current_page(context)

            if page_analysis.get("search_possible"):
                # Execute LLM-recommended actions
                actions = page_analysis.get("recommended_actions", [])

                for action in actions:
                    result = await self.browser.execute(**action)
                    if result.error:
                        logger.warning(f"LLM-guided action failed: {result.error}")
                    else:
                        await asyncio.sleep(1)

                return {"success": True, "method": "llm_guided"}
            else:
                # LLM determined search is not possible, try alternative
                return await self._direct_url_search(context)

        except Exception as e:
            return {"success": False, "error": f"LLM-guided search failed: {e}"}

    async def _analyze_current_page(self, context: SearchContext) -> Dict:
        """Let LLM analyze current page and recommend actions"""
        try:
            # Extract current page content
            extract_result = await self.browser.execute(
                action="extract_content",
                goal="Extract page structure and interactive elements",
            )

            if extract_result.error:
                return {
                    "search_possible": False,
                    "reason": "Could not extract page content",
                }

            analysis_prompt = f"""
            Analyze this page content and determine how to perform a search for: "{context.query}"

            Page content: {extract_result.output[:2000]}

            Provide JSON response with:
            - search_possible: true/false
            - recommended_actions: list of browser actions to execute
            - reasoning: explanation of the approach

            Actions format: {{"action": "action_name", "parameter": "value"}}
            Available actions: type_text, click_element, key_press, go_to_url
            """

            response = await self.llm.generate_response(analysis_prompt)
            import json

            return json.loads(response)

        except Exception as e:
            logger.warning(f"Page analysis failed: {e}")
            return {"search_possible": False, "reason": f"Analysis error: {e}"}

    async def _adapt_search_strategy(
        self, original_strategy: Dict, failed_result: Dict, context: SearchContext
    ) -> Dict:
        """Let LLM adapt search strategy based on failure"""
        if not self.llm:
            # Simple fallback adaptation
            fallbacks = original_strategy.get("fallback_strategies", [])
            if fallbacks:
                return {
                    **original_strategy,
                    "primary_strategy": fallbacks[0],
                    "fallback_strategies": fallbacks[1:],
                }
            return original_strategy

        adaptation_prompt = f"""
        The search strategy failed. Analyze and create an improved approach:

        Original strategy: {original_strategy}
        Failure details: {failed_result}
        Query: {context.query}

        Consider:
        - Why the strategy might have failed
        - Alternative approaches that could work
        - Any anti-bot measures to circumvent
        - Different search engines or methods

        Return improved strategy JSON with same format as original.
        """

        try:
            response = await self.llm.generate_response(adaptation_prompt)
            import json

            adapted_strategy = json.loads(response)
            return adapted_strategy
        except Exception as e:
            logger.warning(f"Strategy adaptation failed: {e}")
            return original_strategy
