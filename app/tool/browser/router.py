"""
Browser Action Router

Routes browser actions to appropriate handlers.
"""

from typing import Any, Dict, Optional

from browser_use.browser.context import BrowserContext

from app.logger import logger
from app.tool.base import ToolResult
from app.tool.browser.actions import (
    ExtractionHandler,
    InteractionHandler,
    NavigationHandler,
    ScrollHandler,
    TabHandler,
)


class BrowserActionRouter:
    """Routes browser actions to appropriate specialized handlers."""

    def __init__(self, context: BrowserContext, content_extractor, selector_tracker):
        self.context = context
        self.selector_tracker = selector_tracker

        # Initialize handlers
        self.navigation_handler = NavigationHandler(context, selector_tracker)
        self.interaction_handler = InteractionHandler(context, selector_tracker)
        self.scroll_handler = ScrollHandler(context, selector_tracker)
        self.tab_handler = TabHandler(context, selector_tracker)
        self.extraction_handler = ExtractionHandler(
            context, content_extractor, selector_tracker
        )

        # Action routing map
        self.action_map = {
            # Navigation actions
            "go_to": self.navigation_handler,
            "go_back": self.navigation_handler,
            "refresh": self.navigation_handler,
            # Interaction actions
            "click": self.interaction_handler,
            "input_text": self.interaction_handler,
            "select_option": self.interaction_handler,
            # Scroll actions
            "scroll_up": self.scroll_handler,
            "scroll_down": self.scroll_handler,
            "scroll_to_text": self.scroll_handler,
            # Tab management
            "switch_tab": self.tab_handler,
            "open_tab": self.tab_handler,
            "close_tab": self.tab_handler,
            # Content extraction
            "extract_content": self.extraction_handler,
        }

    async def route_action(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        tab_id: Optional[int] = None,
        goal: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Route an action to the appropriate handler.

        Args:
            action: The action to perform
            url: URL for navigation actions
            index: Element index for interaction actions
            text: Text for input or selection actions
            scroll_amount: Scroll distance in pixels
            tab_id: Tab ID for tab management
            goal: Goal for content extraction
            **kwargs: Additional parameters

        Returns:
            ToolResult: Result of the action
        """
        try:
            # Validate action
            if not action:
                return ToolResult(success=False, error="Action parameter is required")

            # Get appropriate handler
            handler = self.action_map.get(action)
            if not handler:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}. Available actions: {list(self.action_map.keys())}",
                )

            # Track selector usage for anti-hallucination
            if index is not None and self.selector_tracker:
                selector_key = f"{action}_{index}"
                if not self.selector_tracker.track_selector(selector_key):
                    return ToolResult(
                        success=False,
                        error=f"Selector index {index} has been used too many times recently. Please try a different approach.",
                    )

            # Route to handler
            logger.info(f"🎯 Routing action '{action}' to {handler.__class__.__name__}")

            result = await handler.handle(
                action=action,
                url=url,
                index=index,
                text=text,
                scroll_amount=scroll_amount,
                tab_id=tab_id,
                goal=goal,
                **kwargs,
            )

            if result.success:
                logger.info(f"✅ Action '{action}' completed successfully")
            else:
                logger.warning(f"⚠️ Action '{action}' failed: {result.error}")

            return result

        except Exception as e:
            logger.error(f"❌ Error routing action '{action}': {str(e)}")
            return ToolResult(success=False, error=f"Action routing failed: {str(e)}")

    def get_available_actions(self) -> list:
        """Get list of available actions."""
        return list(self.action_map.keys())

    def get_action_help(self, action: str) -> Optional[str]:
        """Get help text for a specific action."""
        help_text = {
            "go_to": "Navigate to a specific URL. Requires: url",
            "go_back": "Go back in browser history. No parameters required.",
            "refresh": "Refresh the current page. No parameters required.",
            "click": "Click an element. Requires: index",
            "input_text": "Input text into an element. Requires: index, text",
            "select_option": "Select an option from a dropdown. Requires: index, text",
            "scroll_up": "Scroll up. Optional: scroll_amount (default 500px)",
            "scroll_down": "Scroll down. Optional: scroll_amount (default 500px)",
            "scroll_to_text": "Scroll to specific text. Requires: text",
            "switch_tab": "Switch to a tab. Requires: tab_id",
            "open_tab": "Open a new tab. Optional: url (default about:blank)",
            "close_tab": "Close current tab. No parameters required.",
            "extract_content": "Extract content from page. Optional: goal",
        }
        return help_text.get(action)
