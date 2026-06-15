"""
Enhanced Unified Browser Tool with Stealth Mode
Integrates NoDriver for anti-bot detection bypass and smart scraping.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from app.logger import logger
from app.search.scrapers.nodriver_scraper import NoDriverScraper
from app.tool.core import BaseTool, ToolConfig, ToolResult


class EnhancedUnifiedBrowserTool(BaseTool):
    """
    Enhanced unified browser tool with advanced stealth capabilities.

    Features:
    - NoDriver integration for anti-bot detection bypass
    - Stealth mode with random user agents and viewports
    - Multi-strategy content extraction
    - Human behavior mimicking
    """

    # Browser state fields
    browser_context: Optional[Any] = Field(
        default=None, description="Browser context instance"
    )
    current_url: Optional[str] = Field(default=None, description="Current browser URL")
    initialized: bool = Field(default=False, description="Browser initialization state")
    stealth_mode: bool = Field(default=True, description="Enable stealth mode")

    # Stealth components
    nodriver_scraper: Optional[NoDriverScraper] = Field(
        default=None, description="NoDriver scraper for stealth"
    )

    def __init__(self, **kwargs):
        # Set default configuration
        default_config = ToolConfig(
            name="browser_use",
            description="Advanced browser automation with stealth mode and anti-bot detection bypass",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": [
                            "go_to",
                            "go_to_url",
                            "navigate",
                            "initialize",
                            "stealth_scrape",
                            "extract_content",
                            "analyze_structure",
                            "summarize_content",
                            "screenshot",
                            "get_state",
                            "close",
                        ],
                    },
                    "url": {
                        "type": "string",
                        "description": "URL for navigation actions",
                    },
                    "goal": {
                        "type": "string",
                        "description": "Goal for content extraction or analysis",
                    },
                    "stealth": {
                        "type": "boolean",
                        "description": "Use stealth mode for anti-bot detection bypass",
                        "default": True,
                    },
                },
                "required": ["action"],
            },
            llm_enabled=True,
            llm_reasoning=True,
            cache_enabled=False,  # Browser state changes, don't cache
            timeout=60.0,  # Increased for stealth operations
        )

        if "config" not in kwargs:
            kwargs["config"] = default_config

        super().__init__(**kwargs)

        # Initialize stealth scraper
        self.nodriver_scraper = NoDriverScraper()

    @property
    def name(self) -> str:
        """Get tool name for compatibility."""
        return self.config.name

    async def _execute(self, **kwargs) -> ToolResult:
        """Execute browser action with unified interface and stealth capabilities."""
        action = kwargs.get("action", "").lower()
        use_stealth = kwargs.get("stealth", self.stealth_mode)

        try:
            # Route to appropriate handler
            if action in ["go_to", "go_to_url", "navigate", "initialize"]:
                return await self._handle_navigation(kwargs, use_stealth)
            elif action == "stealth_scrape":
                return await self._handle_stealth_scrape(kwargs)
            elif action == "extract_content":
                return await self._handle_content_extraction(kwargs, use_stealth)
            elif action == "analyze_structure":
                return await self._handle_analyze_structure(kwargs, use_stealth)
            elif action == "summarize_content":
                return await self._handle_summarize_content(kwargs, use_stealth)
            elif action == "screenshot":
                return await self._handle_screenshot(kwargs)
            elif action == "get_state":
                return await self._get_browser_state()
            elif action == "close":
                return await self._close_browser()
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}",
                    data={
                        "available_actions": list(
                            self.config.parameters["properties"]["action"]["enum"]
                        )
                    },
                )

        except Exception as e:
            logger.error(f"❌ Browser action '{action}' failed: {e}")
            return ToolResult(
                success=False,
                error=f"Browser action failed: {str(e)}",
                data={"action": action, "error_type": type(e).__name__},
            )

    async def _handle_stealth_scrape(self, kwargs) -> ToolResult:
        """Handle stealth scraping using NoDriver."""
        url = kwargs.get("url")
        goal = kwargs.get("goal", "")

        if not url:
            return ToolResult(
                success=False, error="URL is required for stealth scraping", data={}
            )

        try:
            logger.info(f"🥷 Starting stealth scrape of: {url}")

            # Use NoDriver for stealth scraping
            content = await self.nodriver_scraper.scrape_with_nodriver(url, goal)

            if content:
                self.current_url = url
                logger.info(f"✅ Stealth scraping successful for: {url}")

                return ToolResult(
                    success=True,
                    data={
                        "content": content,
                        "url": url,
                        "method": "stealth_nodriver",
                        "goal": goal,
                        "content_length": len(content),
                    },
                    metadata={
                        "extraction_method": "stealth",
                        "anti_bot_bypass": True,
                        "timestamp": time.time(),
                    },
                )
            else:
                return ToolResult(
                    success=False,
                    error="Stealth scraping returned no content",
                    data={"url": url, "method": "stealth_nodriver"},
                )

        except Exception as e:
            logger.error(f"❌ Stealth scraping failed for {url}: {e}")
            return ToolResult(
                success=False,
                error=f"Stealth scraping failed: {str(e)}",
                data={"url": url, "error_type": type(e).__name__},
            )

    async def _handle_navigation(self, kwargs, use_stealth=True) -> ToolResult:
        """Handle navigation with optional stealth mode."""
        url = kwargs.get("url")

        if not url:
            return ToolResult(
                success=False, error="URL is required for navigation", data={}
            )

        if use_stealth:
            # Use stealth scraping for navigation
            return await self._handle_stealth_scrape(kwargs)
        else:
            # Basic navigation (could integrate with browser-use if needed)
            self.current_url = url
            return ToolResult(
                success=True,
                data={"url": url, "method": "basic_navigation"},
                metadata={"navigation_type": "basic"},
            )

    async def _handle_content_extraction(self, kwargs, use_stealth=True) -> ToolResult:
        """Handle content extraction with stealth capabilities."""
        url = kwargs.get("url", self.current_url)
        goal = kwargs.get("goal", "")

        if not url:
            return ToolResult(
                success=False, error="URL is required for content extraction", data={}
            )

        if use_stealth:
            # Use stealth scraping for content extraction
            kwargs["url"] = url
            kwargs["goal"] = goal
            return await self._handle_stealth_scrape(kwargs)
        else:
            # Basic content extraction
            return ToolResult(
                success=True,
                data={"message": "Basic content extraction not implemented"},
                metadata={"extraction_type": "basic"},
            )

    async def _get_browser_state(self) -> ToolResult:
        """Get current browser state."""
        return ToolResult(
            success=True,
            data={
                "current_url": self.current_url,
                "initialized": self.initialized,
                "stealth_mode": self.stealth_mode,
                "timestamp": time.time(),
            },
            metadata={"state_type": "browser"},
        )

    async def _handle_analyze_structure(self, kwargs, use_stealth=True) -> ToolResult:
        """Analyze page structure and safety content."""
        url = kwargs.get("url", self.current_url)
        goal = kwargs.get(
            "goal",
            "Analyze the page structure and identify accident prevention and safety guidance content.",
        )
        kwargs["url"] = url
        kwargs["goal"] = goal
        return await self._handle_content_extraction(kwargs, use_stealth)

    async def _handle_summarize_content(self, kwargs, use_stealth=True) -> ToolResult:
        """Summarize the page content with a safety focus."""
        url = kwargs.get("url", self.current_url)
        goal = kwargs.get(
            "goal",
            "Summarize the current page content focusing on accident prevention recommendations and partner safety policies.",
        )
        kwargs["url"] = url
        kwargs["goal"] = goal
        return await self._handle_content_extraction(kwargs, use_stealth)

    async def _handle_screenshot(self, kwargs) -> ToolResult:
        """Provide a page snapshot or fallback state when screenshoting is requested."""
        # If actual screenshot support is unavailable, return state and a warning.
        state_result = await self._get_browser_state()
        return ToolResult(
            success=True,
            content={
                "warning": "Screenshot is not supported by the current stealth browser tool.",
                "state": state_result.data,
            },
            metadata={"action": "screenshot_fallback"},
        )

    async def get_current_state(self) -> ToolResult:
        """Return the current browser state for compatibility with browser helper classes."""
        return await self._get_browser_state()

    async def cleanup(self) -> ToolResult:
        """Cleanup browser resources."""
        return await self._close_browser()

    async def _close_browser(self) -> ToolResult:
        """Close browser and cleanup resources."""
        try:
            if self.browser_context:
                # Cleanup browser context if exists
                self.browser_context = None

            self.initialized = False
            self.current_url = None

            logger.info("🔒 Browser closed and cleaned up")

            return ToolResult(
                success=True,
                data={"message": "Browser closed successfully"},
                metadata={"action": "cleanup"},
            )

        except Exception as e:
            logger.error(f"❌ Error closing browser: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to close browser: {str(e)}",
                data={"error_type": type(e).__name__},
            )

    async def cleanup(self):
        """Cleanup browser resources."""
        await self._close_browser()


# Keep the UnifiedBrowserTool name for backward compatibility
UnifiedBrowserTool = EnhancedUnifiedBrowserTool
