"""
Browser State Management

Handles browser state tracking and context management.
"""

import time
from typing import Any, Dict, Optional

from browser_use import Browser as BrowserUseBrowser
from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

from app.config import config
from app.logger import logger


class BrowserStateManager:
    """Manages browser state and context lifecycle."""

    def __init__(self, llm):
        self.llm = llm
        self.context: Optional[BrowserContext] = None
        self.browser: Optional[BrowserUseBrowser] = None
        self.last_action_time = 0
        self.session_timeout = 300  # 5 minutes

    async def ensure_browser_initialized(self) -> BrowserContext:
        """Ensure browser is initialized and return context."""
        try:
            # Check if context exists and is still valid
            if self.context and await self._is_context_valid():
                # Update last action time
                self.last_action_time = time.time()
                return self.context

            # Clean up existing context if invalid
            if self.context:
                await self._cleanup_context()

            # Initialize new browser context
            logger.info("🌐 Initializing new browser context...")

            # Configure browser
            browser_config = BrowserConfig(
                headless=config.browser.get("headless", True),
                disable_security=config.browser.get("disable_security", True),
                chrome_instance_path=config.browser.get("chrome_path"),
                cdp_url=config.browser.get("cdp_url"),
                new_context_config=BrowserContextConfig(
                    save_recording_path=config.browser.get("recording_path"),
                    no_viewport=config.browser.get("no_viewport", False),
                    browser_window_size=config.browser.get(
                        "window_size", {"width": 1280, "height": 720}
                    ),
                    trace_path=config.browser.get("trace_path"),
                ),
            )

            # Create browser instance
            self.browser = BrowserUseBrowser(config=browser_config, llm=self.llm)

            # Create new context
            self.context = await self.browser.new_context()
            self.last_action_time = time.time()

            logger.info("✅ Browser context initialized successfully")
            return self.context

        except Exception as e:
            logger.error(f"❌ Failed to initialize browser context: {str(e)}")
            raise Exception(f"Browser initialization failed: {str(e)}")

    async def get_current_state(
        self, include_screenshot: bool = False
    ) -> Dict[str, Any]:
        """Get current browser state and page information."""
        try:
            if not self.context:
                return {"success": False, "error": "Browser not initialized"}

            # Get current page info
            page_info = {
                "url": await self.context.get_url(),
                "title": await self.context.get_title(),
                "timestamp": time.time(),
            }

            # Get page structure (DOM elements)
            try:
                dom_elements = await self.context.get_dom_elements_with_info()
                page_info["elements"] = dom_elements
                page_info["element_count"] = len(dom_elements) if dom_elements else 0
            except Exception as e:
                logger.warning(f"Could not get DOM elements: {e}")
                page_info["elements"] = []
                page_info["element_count"] = 0

            # Get screenshot if requested
            if include_screenshot:
                try:
                    screenshot = await self.context.screenshot()
                    page_info["screenshot"] = screenshot
                except Exception as e:
                    logger.warning(f"Could not capture screenshot: {e}")
                    page_info["screenshot"] = None

            return {
                "success": True,
                "page_info": page_info,
                "browser_initialized": True,
                "last_action_time": self.last_action_time,
            }

        except Exception as e:
            logger.error(f"❌ Error getting browser state: {str(e)}")
            return {"success": False, "error": f"Failed to get browser state: {str(e)}"}

    async def cleanup(self):
        """Clean up browser resources."""
        try:
            logger.info("🧹 Cleaning up browser resources...")

            if self.context:
                await self._cleanup_context()

            if self.browser:
                try:
                    await self.browser.close()
                    logger.info("✅ Browser closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
                finally:
                    self.browser = None

            self.last_action_time = 0

        except Exception as e:
            logger.error(f"❌ Error during browser cleanup: {str(e)}")

    async def _is_context_valid(self) -> bool:
        """Check if current context is still valid."""
        try:
            if not self.context:
                return False

            # Check if session has timed out
            if time.time() - self.last_action_time > self.session_timeout:
                logger.info("🕐 Browser session timed out")
                return False

            # Try to get current URL to verify context is responsive
            await self.context.get_url()
            return True

        except Exception:
            return False

    async def _cleanup_context(self):
        """Clean up current context."""
        try:
            if self.context:
                await self.context.close()
                logger.info("✅ Browser context closed")
        except Exception as e:
            logger.warning(f"Error closing context: {e}")
        finally:
            self.context = None

    def is_initialized(self) -> bool:
        """Check if browser is initialized."""
        return self.context is not None

    def get_session_info(self) -> Dict[str, Any]:
        """Get information about current session."""
        return {
            "initialized": self.is_initialized(),
            "last_action_time": self.last_action_time,
            "session_age": (
                time.time() - self.last_action_time if self.last_action_time > 0 else 0
            ),
            "session_timeout": self.session_timeout,
        }
