"""
LLM-Driven Navigation Component
Replaces static navigation logic with dynamic reasoning
"""

import asyncio
from typing import Dict, Optional

from app.agent.visual_search.types import (
    NavigationResult,
    NavigationStatus,
    SearchContext,
)
from app.logger import logger


class LLMNavigationManager:
    """Handles navigation with LLM-driven decision making"""

    def __init__(self, browser_handler, llm_client=None):
        self.browser = browser_handler
        self.llm = llm_client

    async def navigate_with_reasoning(self, context: SearchContext) -> NavigationResult:
        """Navigate using LLM reasoning to determine best approach"""
        logger.info(f"🧠 Using LLM-driven navigation for: {context.query}")

        # Let LLM analyze the query and determine navigation strategy
        navigation_plan = await self._get_navigation_plan(context)

        # Execute the plan
        for attempt in range(context.retry_attempts):
            result = await self._execute_navigation_plan(navigation_plan, attempt)

            if result.success:
                return result

            # Let LLM analyze the failure and suggest next approach
            if attempt < context.retry_attempts - 1:
                navigation_plan = await self._adapt_navigation_plan(
                    navigation_plan, result, context
                )

        return NavigationResult(
            success=False,
            status=NavigationStatus.FAILED,
            error="All navigation attempts failed after LLM analysis",
        )

    async def _get_navigation_plan(self, context: SearchContext) -> Dict:
        """Let LLM create navigation plan based on query analysis"""
        if not self.llm:
            # Fallback to simple plan
            return {"strategy": "direct", "url": "https://www.google.com"}

        prompt = f"""
        Analyze this search query and create an optimal navigation plan: "{context.query}"

        Consider:
        - Is this a general web search or specific site search?
        - Would direct URL construction be better than manual search?
        - Are there specific sites that would be most relevant?

        Provide a JSON navigation plan with:
        - strategy: "direct_url" | "homepage_search" | "site_specific"
        - target_url: primary URL to navigate to
        - backup_urls: alternative URLs if primary fails
        - verification_keywords: words to check for successful navigation
        """

        try:
            response = await self.llm.generate_response(prompt)
            # Parse LLM response into navigation plan
            import json

            plan = json.loads(response)
            return plan
        except Exception as e:
            logger.warning(f"LLM navigation planning failed: {e}")
            return {"strategy": "direct", "url": "https://www.google.com"}

    async def _execute_navigation_plan(
        self, plan: Dict, attempt: int
    ) -> NavigationResult:
        """Execute the navigation plan"""
        strategy = plan.get("strategy", "direct")
        target_url = plan.get("target_url", "https://www.google.com")

        try:
            # Navigate to target URL
            nav_result = await self.browser.execute(action="go_to_url", url=target_url)

            if nav_result.error:
                return NavigationResult(
                    success=False,
                    status=NavigationStatus.FAILED,
                    error=f"Navigation failed: {nav_result.error}",
                )

            # LLM-driven verification
            verification = await self._verify_navigation_success(plan)

            if verification["success"]:
                return NavigationResult(
                    success=True,
                    status=NavigationStatus.SUCCESS,
                    page_content=verification.get("content"),
                )
            else:
                return NavigationResult(
                    success=False,
                    status=NavigationStatus.RETRY_NEEDED,
                    error=verification.get("reason"),
                )

        except Exception as e:
            return NavigationResult(
                success=False, status=NavigationStatus.FAILED, error=str(e)
            )

    async def _verify_navigation_success(self, plan: Dict) -> Dict:
        """Use LLM to verify navigation was successful"""
        if not self.llm:
            # Simple fallback verification
            try:
                extract_result = await self.browser.execute(
                    action="extract_content",
                    goal="Check if this page is ready for search operations",
                )
                return {
                    "success": not extract_result.error,
                    "content": (
                        extract_result.output if not extract_result.error else None
                    ),
                }
            except:
                return {"success": False, "reason": "Page verification failed"}

        # LLM-powered verification
        try:
            extract_result = await self.browser.execute(
                action="extract_content",
                goal="Extract page content for verification analysis",
            )

            if extract_result.error:
                return {"success": False, "reason": "Could not extract page content"}

            verification_prompt = f"""
            Analyze this page content and determine if navigation was successful:

            Expected: {plan.get('verification_keywords', 'search functionality')}
            Content: {extract_result.output[:1000]}

            Return JSON with:
            - success: true/false
            - reason: explanation
            - ready_for_search: true/false
            """

            verification_response = await self.llm.generate_response(
                verification_prompt
            )
            import json

            return json.loads(verification_response)

        except Exception as e:
            logger.warning(f"LLM verification failed: {e}")
            return {"success": False, "reason": f"Verification error: {e}"}

    async def _adapt_navigation_plan(
        self,
        original_plan: Dict,
        failed_result: NavigationResult,
        context: SearchContext,
    ) -> Dict:
        """Let LLM adapt the navigation plan based on failure"""
        if not self.llm:
            # Simple fallback adaptation
            backup_urls = original_plan.get("backup_urls", ["https://www.google.com"])
            if backup_urls:
                return {**original_plan, "target_url": backup_urls[0]}
            return original_plan

        adaptation_prompt = f"""
        The navigation plan failed. Analyze and create an improved plan:

        Original plan: {original_plan}
        Failure reason: {failed_result.error}
        Query: {context.query}

        Create an adapted navigation plan that addresses the failure.
        Consider alternative approaches, different URLs, or modified strategies.
        """

        try:
            response = await self.llm.generate_response(adaptation_prompt)
            import json

            adapted_plan = json.loads(response)
            return adapted_plan
        except Exception as e:
            logger.warning(f"Plan adaptation failed: {e}")
            return original_plan
