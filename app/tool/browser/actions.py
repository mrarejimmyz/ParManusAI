"""
Browser Action Handlers

Separates browser actions into focused, maintainable handlers.
"""

from typing import Any, Dict, Optional

from browser_use.browser.context import BrowserContext

from app.logger import logger
from app.tool.base import ToolResult


class BrowserActionHandler:
    """Base class for browser action handlers."""

    def __init__(self, context: BrowserContext, selector_tracker=None):
        self.context = context
        self.selector_tracker = selector_tracker

    async def handle(self, **kwargs) -> ToolResult:
        """Handle the action. To be implemented by subclasses."""
        raise NotImplementedError


class NavigationHandler(BrowserActionHandler):
    """Handles navigation actions: go_to, go_back, refresh."""

    async def handle(
        self, action: str, url: Optional[str] = None, **kwargs
    ) -> ToolResult:
        try:
            if action == "go_to":
                if not url:
                    return ToolResult(
                        success=False, error="URL is required for go_to action"
                    )
                logger.info(f"🌐 Navigating to: {url}")
                await self.context.goto(url)
                return ToolResult(
                    success=True, content=f"Successfully navigated to {url}"
                )

            elif action == "go_back":
                logger.info("⬅️ Going back in browser history")
                await self.context.go_back()
                return ToolResult(
                    success=True, content="Successfully went back in browser history"
                )

            elif action == "refresh":
                logger.info("🔄 Refreshing page")
                await self.context.reload()
                return ToolResult(
                    success=True, content="Successfully refreshed the page"
                )

            else:
                return ToolResult(
                    success=False, error=f"Unknown navigation action: {action}"
                )

        except Exception as e:
            logger.error(f"❌ Navigation action '{action}' failed: {str(e)}")
            return ToolResult(success=False, error=f"Navigation failed: {str(e)}")


class InteractionHandler(BrowserActionHandler):
    """Handles interaction actions: click, input_text, select_option."""

    async def handle(
        self,
        action: str,
        index: Optional[int] = None,
        text: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            if action == "click":
                if index is None:
                    return ToolResult(
                        success=False, error="Index is required for click action"
                    )

                logger.info(f"🖱️ Clicking element at index: {index}")
                await self.context.click(index)
                return ToolResult(
                    success=True,
                    content=f"Successfully clicked element at index {index}",
                )

            elif action == "input_text":
                if index is None or text is None:
                    return ToolResult(
                        success=False,
                        error="Both index and text are required for input_text action",
                    )

                logger.info(f"⌨️ Inputting text at index {index}: {text[:50]}...")
                await self.context.input_text(index, text)
                return ToolResult(
                    success=True, content=f"Successfully input text at index {index}"
                )

            elif action == "select_option":
                if index is None or text is None:
                    return ToolResult(
                        success=False,
                        error="Both index and text are required for select_option action",
                    )

                logger.info(f"📋 Selecting option '{text}' at index {index}")
                await self.context.select_option(index, text)
                return ToolResult(
                    success=True,
                    content=f"Successfully selected option '{text}' at index {index}",
                )

            else:
                return ToolResult(
                    success=False, error=f"Unknown interaction action: {action}"
                )

        except Exception as e:
            logger.error(f"❌ Interaction action '{action}' failed: {str(e)}")
            return ToolResult(success=False, error=f"Interaction failed: {str(e)}")


class ScrollHandler(BrowserActionHandler):
    """Handles scrolling actions: scroll_up, scroll_down, scroll_to_text."""

    async def handle(
        self,
        action: str,
        scroll_amount: Optional[int] = None,
        text: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            if action == "scroll_up":
                amount = scroll_amount or 500
                logger.info(f"⬆️ Scrolling up by {amount} pixels")
                await self.context.scroll(-amount)
                return ToolResult(
                    success=True, content=f"Successfully scrolled up by {amount} pixels"
                )

            elif action == "scroll_down":
                amount = scroll_amount or 500
                logger.info(f"⬇️ Scrolling down by {amount} pixels")
                await self.context.scroll(amount)
                return ToolResult(
                    success=True,
                    content=f"Successfully scrolled down by {amount} pixels",
                )

            elif action == "scroll_to_text":
                if not text:
                    return ToolResult(
                        success=False,
                        error="Text is required for scroll_to_text action",
                    )

                logger.info(f"🔍 Scrolling to text: {text[:30]}...")
                await self.context.scroll_to_text(text)
                return ToolResult(
                    success=True,
                    content=f"Successfully scrolled to text: {text[:30]}...",
                )

            else:
                return ToolResult(
                    success=False, error=f"Unknown scroll action: {action}"
                )

        except Exception as e:
            logger.error(f"❌ Scroll action '{action}' failed: {str(e)}")
            return ToolResult(success=False, error=f"Scroll failed: {str(e)}")


class TabHandler(BrowserActionHandler):
    """Handles tab management: switch_tab, open_tab, close_tab."""

    async def handle(
        self,
        action: str,
        tab_id: Optional[int] = None,
        url: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            if action == "switch_tab":
                if tab_id is None:
                    return ToolResult(
                        success=False, error="Tab ID is required for switch_tab action"
                    )

                logger.info(f"🔄 Switching to tab: {tab_id}")
                await self.context.switch_to_tab(tab_id)
                return ToolResult(
                    success=True, content=f"Successfully switched to tab {tab_id}"
                )

            elif action == "open_tab":
                url_to_open = url or "about:blank"
                logger.info(f"➕ Opening new tab: {url_to_open}")
                await self.context.create_tab(url_to_open)
                return ToolResult(
                    success=True,
                    content=f"Successfully opened new tab with URL: {url_to_open}",
                )

            elif action == "close_tab":
                logger.info("❌ Closing current tab")
                await self.context.close_tab()
                return ToolResult(
                    success=True, content="Successfully closed current tab"
                )

            else:
                return ToolResult(success=False, error=f"Unknown tab action: {action}")

        except Exception as e:
            logger.error(f"❌ Tab action '{action}' failed: {str(e)}")
            return ToolResult(success=False, error=f"Tab management failed: {str(e)}")


class ExtractionHandler(BrowserActionHandler):
    """Handles content extraction actions."""

    def __init__(
        self, context: BrowserContext, content_extractor, selector_tracker=None
    ):
        super().__init__(context, selector_tracker)
        self.content_extractor = content_extractor

    async def handle(
        self, action: str, goal: Optional[str] = None, **kwargs
    ) -> ToolResult:
        try:
            if action == "extract_content":
                goal_text = goal or "Extract information from the current page"

                logger.info(f"📄 Extracting content with goal: {goal_text[:50]}...")

                # Get page content using the enhanced extractor
                extraction_result = await self.content_extractor.extract_content(
                    context=self.context, goal=goal_text
                )

                if extraction_result:
                    return ToolResult(success=True, content=extraction_result)
                else:
                    return ToolResult(
                        success=False, error="Content extraction returned empty result"
                    )

            else:
                return ToolResult(
                    success=False, error=f"Unknown extraction action: {action}"
                )

        except Exception as e:
            logger.error(f"❌ Extraction action '{action}' failed: {str(e)}")
            return ToolResult(
                success=False, error=f"Content extraction failed: {str(e)}"
            )
