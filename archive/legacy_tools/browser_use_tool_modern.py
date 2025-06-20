"""
Modern Browser Tool - Refactored and Optimized

A clean, modular browser automation tool with separated concerns.
Uses the browser action router and state manager for maintainable code.
"""

import time
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.llm import LLM
from app.logger import logger
from app.tool.base import BaseTool, ToolResult
from app.tool.browser import BrowserActionRouter, BrowserStateManager
from app.tool.enhanced_browser import EnhancedContentExtractor
from app.tool.web_search import WebSearch

_BROWSER_DESCRIPTION = """\
A powerful browser automation tool that allows interaction with web pages through various actions.
* This tool provides commands for controlling a browser session, navigating web pages, and extracting information
* It maintains state across calls, keeping the browser session alive until explicitly closed
* Use this when you need to browse websites, fill forms, click buttons, extract content, or perform web searches
* Each action requires specific parameters as defined in the tool's dependencies

Key capabilities include:
* Navigation: Go to specific URLs, go back, search the web, or refresh pages
* Interaction: Click elements, input text, select from dropdowns, send keyboard commands
* Scrolling: Scroll up/down by pixel amount or scroll to specific text
* Content extraction: Extract and analyze content from web pages based on specific goals
* Tab management: Switch between tabs, open new tabs, or close tabs

Note: When using element indices, refer to the numbered elements shown in the current browser state.
"""

Context = TypeVar("Context")


# Track selector usage to prevent hallucination loops
class SelectorTracker:
    def __init__(self, max_retries: int = 3):
        self.selector_counts: Dict[str, int] = {}
        self.max_retries = max_retries
        self.recent_selectors: List[str] = []
        self.max_recent = 10

    def track_selector(self, selector: str) -> bool:
        """Track selector usage and return False if overused."""
        # Clean old entries
        current_time = time.time()
        self.recent_selectors = [s for s in self.recent_selectors[-self.max_recent :]]

        # Count usage
        self.selector_counts[selector] = self.selector_counts.get(selector, 0) + 1

        # Check if overused
        if self.selector_counts[selector] > self.max_retries:
            logger.warning(
                f"⚠️ Selector {selector} used {self.selector_counts[selector]} times"
            )
            return False

        self.recent_selectors.append(selector)
        return True

    def is_valid_selector(self, selector: str) -> bool:
        """Check if selector is valid to use."""
        return self.selector_counts.get(selector, 0) < self.max_retries


class ModernBrowserTool(Generic[Context], BaseTool):
    """Modern, modular browser automation tool."""

    llm: LLM = Field(..., description="LLM instance for browser operations")

    def __init__(self, **data: Any):
        super().__init__(**data)

        # Initialize components
        self.state_manager = BrowserStateManager(self.llm)
        self.content_extractor = EnhancedContentExtractor()
        self.selector_tracker = SelectorTracker()
        self.web_search = WebSearch()

        # Action router will be initialized when browser is ready
        self.action_router: Optional[BrowserActionRouter] = None

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v: dict, info: ValidationInfo) -> dict:
        """Validate and set default parameters."""
        return v

    @field_validator("llm")
    @classmethod
    def validate_llm(cls, v: Any) -> Any:
        """Validate LLM instance."""
        if not hasattr(v, "ask"):
            raise ValueError("LLM must have an 'ask' method")
        return v

    @property
    def description(self) -> str:
        return _BROWSER_DESCRIPTION

    async def _ensure_router_ready(self) -> BrowserActionRouter:
        """Ensure action router is initialized with browser context."""
        if not self.action_router:
            # Initialize browser context
            context = await self.state_manager.ensure_browser_initialized()

            # Initialize action router
            self.action_router = BrowserActionRouter(
                context=context,
                content_extractor=self.content_extractor,
                selector_tracker=self.selector_tracker,
            )

        return self.action_router

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        tab_id: Optional[int] = None,
        goal: Optional[str] = None,
        search_query: Optional[str] = None,
        include_screenshot: bool = False,
        **kwargs,
    ) -> ToolResult:
        """
        Execute a browser action.

        Args:
            action: The action to perform
            url: URL for navigation actions
            index: Element index for interaction actions
            text: Text for input or selection actions
            scroll_amount: Scroll distance in pixels
            tab_id: Tab ID for tab management
            goal: Goal for content extraction
            search_query: Query for web search
            include_screenshot: Include screenshot in state
            **kwargs: Additional parameters

        Returns:
            ToolResult: Result of the action
        """
        try:
            start_time = time.time()
            logger.info(f"🎬 Executing browser action: {action}")

            # Handle special actions that don't need routing
            if action == "search":
                return await self._handle_search(search_query)
            elif action == "get_state":
                return await self._handle_get_state(include_screenshot)
            elif action == "close":
                return await self._handle_close()

            # Ensure router is ready for standard actions
            router = await self._ensure_router_ready()

            # Route action to appropriate handler
            result = await router.route_action(
                action=action,
                url=url,
                index=index,
                text=text,
                scroll_amount=scroll_amount,
                tab_id=tab_id,
                goal=goal,
                **kwargs,
            )

            # Add timing information
            execution_time = time.time() - start_time
            if hasattr(result, "metadata"):
                result.metadata = result.metadata or {}
                result.metadata["execution_time"] = execution_time

            return result

        except Exception as e:
            logger.error(f"❌ Browser action '{action}' failed: {str(e)}")
            return ToolResult(success=False, error=f"Browser action failed: {str(e)}")

    async def _handle_search(self, query: Optional[str]) -> ToolResult:
        """Handle web search action."""
        if not query:
            return ToolResult(
                success=False, error="Search query is required for search action"
            )

        try:
            logger.info(f"🔍 Performing web search: {query}")
            search_results = await self.web_search.search(query)

            if search_results:
                return ToolResult(
                    success=True,
                    content=f"Search results for '{query}':\n\n{search_results}",
                )
            else:
                return ToolResult(success=False, error="No search results found")

        except Exception as e:
            return ToolResult(success=False, error=f"Search failed: {str(e)}")

    async def _handle_get_state(self, include_screenshot: bool = False) -> ToolResult:
        """Handle get current state action."""
        try:
            state = await self.state_manager.get_current_state(include_screenshot)

            if state.get("success"):
                return ToolResult(success=True, content=state)
            else:
                return ToolResult(
                    success=False,
                    error=state.get("error", "Failed to get browser state"),
                )

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get state: {str(e)}")

    async def _handle_close(self) -> ToolResult:
        """Handle browser close action."""
        try:
            await self.state_manager.cleanup()
            self.action_router = None

            return ToolResult(success=True, content="Browser closed successfully")

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to close browser: {str(e)}")

    async def get_current_state(
        self, include_screenshot: bool = False
    ) -> Dict[str, Any]:
        """Get current browser state (public method)."""
        return await self.state_manager.get_current_state(include_screenshot)

    async def cleanup(self):
        """Clean up browser resources."""
        try:
            await self.state_manager.cleanup()
            self.action_router = None
            logger.info("✅ Modern browser tool cleaned up successfully")
        except Exception as e:
            logger.error(f"❌ Error during browser cleanup: {str(e)}")

    async def vision_analyze(self, goal: str) -> str:
        """Perform vision analysis of current page."""
        try:
            # Ensure browser is initialized
            await self._ensure_router_ready()

            # Get current state with screenshot
            state = await self.get_current_state(include_screenshot=True)

            if not state.get("success"):
                return "Failed to capture page for vision analysis"

            screenshot = state.get("page_info", {}).get("screenshot")
            if not screenshot:
                return "No screenshot available for vision analysis"

            # Use LLM for vision analysis
            prompt = f"""
            Analyze this webpage screenshot with the following goal: {goal}

            Provide a detailed analysis of what you can see and how it relates to the goal.
            Include information about:
            - Key visual elements
            - Layout and structure
            - Relevant content
            - Any actionable items
            """

            response = await self.llm.ask(prompt)
            return response.content if hasattr(response, "content") else str(response)

        except Exception as e:
            logger.error(f"❌ Vision analysis failed: {str(e)}")
            return f"Vision analysis failed: {str(e)}"


# Backward compatibility alias
BrowserUseTool = ModernBrowserTool
