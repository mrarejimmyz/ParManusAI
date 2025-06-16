"""
Modern Browser Tool - Unified Interface for Modular Browser System

Combines all modular browser components into a single, coherent interface.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union

from browser_use.browser.context import BrowserContext
from pydantic import Field

from app.logger import logger
from app.tool.base import BaseTool, ToolResult

from .actions import (
    BrowserActionHandler,
    ExtractionHandler,
    InteractionHandler,
    NavigationHandler,
    ScrollHandler,
    TabHandler,
)
from .router import BrowserActionRouter
from .state import BrowserStateManager


class ModernBrowserTool(BaseTool):
    """
    Modern Browser Tool with LLM-driven intelligence.

    Combines all modular browser components into a unified interface
    while maintaining backward compatibility.
    """  # Define all fields as class attributes

    llm: Optional[Any] = Field(default=None, description="Language model instance")
    context: Optional[BrowserContext] = Field(
        default=None, description="Browser context"
    )
    state_manager: Optional[Any] = Field(default=None, description="State manager")
    router: Optional[Any] = Field(default=None, description="Action router")
    navigation_handler: Optional[Any] = Field(
        default=None, description="Navigation handler"
    )
    interaction_handler: Optional[Any] = Field(
        default=None, description="Interaction handler"
    )
    scroll_handler: Optional[Any] = Field(default=None, description="Scroll handler")
    tab_handler: Optional[Any] = Field(default=None, description="Tab handler")
    extraction_handler: Optional[Any] = Field(
        default=None, description="Extraction handler"
    )

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, llm=None, context=None, **kwargs):
        # Initialize with required fields for BaseTool
        super().__init__(
            name="modern_browser_tool",
            description="Modern Browser Tool with LLM-driven intelligence",
            llm=llm,
            **kwargs,
        )
        # Initialize handlers after super().__init__
        self.context = None
        self.state_manager = BrowserStateManager(llm) if llm else None
        self.router = None  # Will be initialized when context is available

        # Initialize handlers (will be set up when context is available)
        self.navigation_handler = None
        self.interaction_handler = None
        self.scroll_handler = None
        self.tab_handler = None
        self.extraction_handler = None

    async def setup_context(self, context: BrowserContext):
        """Setup browser context and initialize handlers."""
        self.context = context
        self.state_manager.context = context

        # Initialize all handlers with the context
        self.navigation_handler = NavigationHandler(context)
        self.interaction_handler = InteractionHandler(context)
        self.scroll_handler = ScrollHandler(context)
        self.tab_handler = TabHandler(context)
        self.extraction_handler = ExtractionHandler(context)

        logger.info("🚀 Modern Browser Tool initialized with LLM-driven capabilities")

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute browser actions with LLM-driven intelligence.

        Args:
            action: The action to perform
            **kwargs: Action-specific parameters
        """
        if not self.context:
            return ToolResult(
                success=False,
                error="Browser context not initialized. Call setup_context first.",
            )

        action = kwargs.get("action", "")

        try:
            # Use router to determine the best handler and approach
            route_result = await self.router.route_action(action, **kwargs)

            if not route_result.success:
                return route_result

            handler_name = route_result.content.get("handler")
            optimized_params = route_result.content.get("params", kwargs)

            # Execute action using the appropriate handler
            if handler_name == "navigation":
                result = await self.navigation_handler.handle(**optimized_params)
            elif handler_name == "interaction":
                result = await self.interaction_handler.handle(**optimized_params)
            elif handler_name == "scroll":
                result = await self.scroll_handler.handle(**optimized_params)
            elif handler_name == "tab":
                result = await self.tab_handler.handle(**optimized_params)
            elif handler_name == "extraction":
                result = await self.extraction_handler.handle(**optimized_params)
            else:
                # Fallback to direct action execution
                result = await self._execute_direct_action(action, **kwargs)

            # Update state after successful action
            if result.success:
                await self.state_manager.update_state(action, result)

            return result

        except Exception as e:
            error_msg = f"Browser action failed: {str(e)}"
            logger.error(error_msg)
            return ToolResult(success=False, error=error_msg)

    async def _execute_direct_action(self, action: str, **kwargs) -> ToolResult:
        """Fallback method for direct action execution."""
        try:
            # Basic navigation actions
            if action == "go_to":
                url = kwargs.get("url")
                if not url:
                    return ToolResult(success=False, error="URL required for go_to")

                await self.context.goto(url)
                return ToolResult(success=True, content=f"Navigated to {url}")

            elif action == "click":
                selector = kwargs.get("selector") or kwargs.get("element_id")
                if not selector:
                    return ToolResult(
                        success=False, error="Selector required for click"
                    )

                element = await self.context.page.query_selector(selector)
                if element:
                    await element.click()
                    return ToolResult(
                        success=True, content=f"Clicked element: {selector}"
                    )
                else:
                    return ToolResult(
                        success=False, error=f"Element not found: {selector}"
                    )

            elif action == "type":
                selector = kwargs.get("selector") or kwargs.get("element_id")
                text = kwargs.get("text") or kwargs.get("value", "")

                if not selector:
                    return ToolResult(success=False, error="Selector required for type")

                element = await self.context.page.query_selector(selector)
                if element:
                    await element.fill(text)
                    return ToolResult(
                        success=True, content=f"Typed '{text}' into {selector}"
                    )
                else:
                    return ToolResult(
                        success=False, error=f"Element not found: {selector}"
                    )

            elif action == "get_text":
                selector = kwargs.get("selector") or kwargs.get("element_id")
                if selector:
                    element = await self.context.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        return ToolResult(success=True, content=text)
                    else:
                        return ToolResult(
                            success=False, error=f"Element not found: {selector}"
                        )
                else:
                    # Get page text
                    text = await self.context.page.text_content("body")
                    return ToolResult(success=True, content=text)

            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}. Use router for complex actions.",
                )

        except Exception as e:
            return ToolResult(
                success=False, error=f"Direct action execution failed: {str(e)}"
            )

    async def get_page_content(self) -> ToolResult:
        """Get current page content."""
        if not self.context:
            return ToolResult(success=False, error="Browser context not initialized")

        try:
            content = await self.context.page.content()
            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(
                success=False, error=f"Failed to get page content: {str(e)}"
            )

    async def get_current_url(self) -> str:
        """Get current page URL."""
        if not self.context:
            return ""

        try:
            return self.context.page.url
        except Exception:
            return ""

    async def screenshot(self, path: Optional[str] = None) -> ToolResult:
        """Take a screenshot of the current page."""
        if not self.context:
            return ToolResult(success=False, error="Browser context not initialized")

        try:
            screenshot_bytes = await self.context.page.screenshot(path=path)
            if path:
                return ToolResult(success=True, content=f"Screenshot saved to {path}")
            else:
                return ToolResult(success=True, content=screenshot_bytes)
        except Exception as e:
            return ToolResult(success=False, error=f"Screenshot failed: {str(e)}")

    def get_name(self) -> str:
        """Get tool name."""
        return "modern_browser_tool"

    def get_description(self) -> str:
        """Get tool description."""
        return """
        Modern Browser Tool with LLM-driven intelligence.

        Capabilities:
        - Intelligent navigation and interaction
        - Smart element detection and handling
        - LLM-guided action optimization
        - Advanced state management
        - Error recovery and adaptation

        Actions: go_to, click, type, get_text, scroll, screenshot, and more.
        """

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Browser action to perform",
                    "enum": [
                        "go_to",
                        "click",
                        "type",
                        "get_text",
                        "scroll",
                        "screenshot",
                        "go_back",
                        "refresh",
                        "wait",
                    ],
                },
                "url": {"type": "string", "description": "URL for navigation actions"},
                "selector": {
                    "type": "string",
                    "description": "CSS selector or element identifier",
                },
                "text": {"type": "string", "description": "Text to type or search for"},
                "value": {
                    "type": "string",
                    "description": "Value to enter into form fields",
                },
                "element_id": {
                    "type": "string",
                    "description": "Element ID for interaction",
                },
            },
            "required": ["action"],
        }
