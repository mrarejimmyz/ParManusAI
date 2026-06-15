import json
import re
import time
from typing import Dict, Optional

from app.config import config
from app.logger import logger
from app.schema import Function, ToolCall


class ManusBrowserHandler:
    def __init__(self, agent_instance):
        self.agent = agent_instance

    async def _initialize_browser_state(self):
        """Initializes or resets the browser state for a new task."""
        if not self.agent.browser_state.get("initialized"):
            logger.info("Initializing browser state...")
            self.agent.browser_state = {
                "current_url": None,
                "content_extracted": False,
                "analysis_complete": False,
                "screenshots_taken": False,
                "last_action": None,
                "page_ready": False,
                "structure_analyzed": False,
                "summary_complete": False,
                "initialized": True,  # Mark as initialized
            }
            logger.debug("Browser state initialized.")

    def _extract_url_from_request(self, step: str) -> Optional[str]:
        """Extracts a URL from a given step string."""
        url = None
        # Look for common URL patterns
        url_patterns = [
            r'https?://[^\s<>"]+|www\.[^\s<>"]+',  # Standard URLs
            r'(?<=review\s)[^\s<>"]+\.[^\s<>"]+',  # URLs after "review"
            r'(?<=visit\s)[^\s<>"]+\.[^\s<>"]+',  # URLs after "visit"
            r'(?<=open\s)[^\s<>"]+\.[^\s<>"]+',  # URLs after "open"
            r'(?<=goto\s)[^\s<>"]+\.[^\s<>"]+',  # URLs after "goto"
            r'(?<=navigate to\s)[^\s<>"]+\.[^\s<>"]+',  # URLs after "navigate to"
        ]

        for pattern in url_patterns:
            matches = re.findall(pattern, step, re.IGNORECASE)
            if matches:
                url = matches[0]
                break
        return url

    async def handle_browser_task(self, step: str) -> Optional[Dict]:
        """Advanced browser task handling with state management"""
        logger.debug(f"Handling browser task: {step}")
        logger.debug(f"Current browser state: {self.agent.browser_state}")

        try:
            if not self.agent.current_plan or "phases" not in self.agent.current_plan:
                logger.error("No valid plan exists")
                return None

            if getattr(self.agent, "browser_state", None) is None:
                self.agent.browser_state = {}

            await self._initialize_browser_state()

            # Handle website navigation
            if "navigate" in step.lower() or step.lower() == "navigate to website":
                if self.agent.browser_state.get(
                    "current_url"
                ) and self.agent.browser_state.get("page_ready"):
                    logger.info("Navigation already completed")
                    return None

                if self.agent.browser_state.get("current_url"):
                    logger.debug("URL set but waiting for page readiness")
                    return None

                user_messages = [
                    msg for msg in self.agent.memory.messages if msg.role == "user"
                ]
                if not user_messages:
                    logger.error("No user request found in memory")
                    return None

                message = user_messages[-1].content
                url = self._extract_url_from_request(
                    step
                ) or self._extract_url_from_request(message)
                if not url:
                    logger.warning("No URL found in user request for navigation.")
                    return None

                if not url.startswith("http"):
                    url = "https://" + url

                logger.info(f"Navigating to URL: {url}")
                browser_args = {"action": "navigate", "url": url}
                func = Function(name="browser_use", arguments=json.dumps(browser_args))
                self.agent.tool_calls = [
                    ToolCall(
                        id="browser_nav_" + str(int(time.time())),
                        type="function",
                        function=func,
                    )
                ]
                self.agent.browser_state["current_url"] = url
                self.agent.browser_state["page_ready"] = False
                self.agent.browser_state["last_action"] = "navigate"
                return {"tool_code": "browser_use", "args": browser_args}

            # Other browser tasks (e.g., content extraction, analysis, screenshot)
            elif "extract content" in step.lower() or step.lower() == "extract content":
                if not self.agent.browser_state.get("content_extracted"):
                    logger.info("Extracting content from current page.")
                    browser_args = {"action": "extract_content"}
                    func = Function(
                        name="browser_use", arguments=json.dumps(browser_args)
                    )
                    self.agent.tool_calls = [
                        ToolCall(
                            id="browser_extract_" + str(int(time.time())),
                            type="function",
                            function=func,
                        )
                    ]
                    self.agent.browser_state["last_action"] = "extract_content"
                    return {"tool_code": "browser_use", "args": browser_args}
                else:
                    logger.info("Content already extracted.")
                    return None

            elif (
                "analyze structure" in step.lower()
                or step.lower() == "analyze page structure"
            ):
                if not self.agent.browser_state.get("structure_analyzed"):
                    logger.info("Analyzing page structure.")
                    browser_args = {"action": "analyze_structure"}
                    func = Function(
                        name="browser_use", arguments=json.dumps(browser_args)
                    )
                    self.agent.tool_calls = [
                        ToolCall(
                            id="browser_analyze_" + str(int(time.time())),
                            type="function",
                            function=func,
                        )
                    ]
                    self.agent.browser_state["last_action"] = "analyze_structure"
                    return {"tool_code": "browser_use", "args": browser_args}
                else:
                    logger.info("Page structure already analyzed.")
                    return None

            elif "screenshot" in step.lower() or "take screenshots" in step.lower():
                if not self.agent.browser_state.get("screenshots_taken"):
                    logger.info("Taking screenshots.")
                    browser_args = {"action": "screenshot"}
                    func = Function(
                        name="browser_use", arguments=json.dumps(browser_args)
                    )
                    self.agent.tool_calls = [
                        ToolCall(
                            id="browser_screenshot_" + str(int(time.time())),
                            type="function",
                            function=func,
                        )
                    ]
                    self.agent.browser_state["last_action"] = "screenshot"
                    return {"tool_code": "browser_use", "args": browser_args}
                else:
                    logger.info("Screenshots already taken.")
                    return None

            elif (
                "summarize content" in step.lower()
                or step.lower() == "summarize content"
            ):
                if not self.agent.browser_state.get("summary_complete"):
                    logger.info("Summarizing content.")
                    browser_args = {"action": "summarize_content"}
                    func = Function(
                        name="browser_use", arguments=json.dumps(browser_args)
                    )
                    self.agent.tool_calls = [
                        ToolCall(
                            id="browser_summarize_" + str(int(time.time())),
                            type="function",
                            function=func,
                        )
                    ]
                    self.agent.browser_state["last_action"] = "summarize_content"
                    return {"tool_code": "browser_use", "args": browser_args}
                else:
                    logger.info("Content already summarized.")
                    return None

            else:
                logger.warning(f"Unknown browser task: {step}")
                return None

        except Exception as e:
            logger.error(f"Error in handle_browser_task: {e}", exc_info=True)
            return None
