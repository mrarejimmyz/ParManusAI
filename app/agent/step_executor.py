"""
Step Execution Module for Manus Agent
Handles the main execution logic for different types of steps.
"""

import asyncio
import json
import time
from typing import Dict, Optional

from app.logger import logger
from app.schema import Function, ToolCall


class StepExecutor:
    """Executes different types of steps in the agent's plan."""

    def __init__(self, agent):
        self.agent = agent
        self.action_executor = None

    def _initialize_action_executor(self):
        """Initialize action executor if not already done."""
        if (
            not hasattr(self.agent, "action_executor")
            or self.agent.action_executor is None
        ):
            from app.agent.actions import (
                SimplifiedManusActionExecutor as ManusActionExecutor,
            )

            self.agent.action_executor = ManusActionExecutor(self.agent)
            self.action_executor = self.agent.action_executor

    async def execute_step(self, current_step: str) -> bool:
        """Execute a step based on its content and type."""

        # Initialize action executor if needed
        self._initialize_action_executor()

        step_lower = current_step.lower()

        # Handle different types of steps with actual tool execution

        # Research and planning steps - navigate to relevant websites
        if any(
            keyword in step_lower
            for keyword in ["research", "plan", "identify", "sources"]
        ):
            return await self._execute_research_step(current_step)

        # Data extraction steps - scrape and collect information
        elif any(
            keyword in step_lower
            for keyword in ["extract", "headlines", "gather", "collect", "visit"]
        ):
            return await self._execute_extraction_step(current_step)

        # Verification steps - check multiple sources
        elif any(
            keyword in step_lower
            for keyword in ["verify", "check", "multiple sources", "confirm"]
        ):
            return await self._execute_verification_step(current_step)

        # File creation steps - generate reports and documents
        elif any(
            keyword in step_lower
            for keyword in [
                "generate",
                "create",
                "format",
                "output",
                ".md",
                "write",
                "report",
            ]
        ):
            return await self._execute_creation_step(current_step)

        # Navigation steps (legacy support)
        elif "navigate" in step_lower or "Navigate to website" in current_step:
            return await self._execute_navigation_step(current_step)

        # Default case - try to determine action from context
        else:
            return await self._execute_default_step(current_step)

    async def _execute_research_step(self, current_step: str) -> bool:
        """Execute research action."""
        logger.info(f"Executing research action for: {current_step}")
        action_success = await self.agent.action_executor.execute_research_action(
            current_step
        )

        if action_success:
            success = await self.agent.utils_module.progress_to_next_step(verified=True)
            return True
        else:
            logger.warning(f"Research action failed for step: {current_step}")
            # For research, we can proceed but mark as unverified
            await self.agent.utils_module.progress_to_next_step(verified=False)
            return True  # Continue execution

    async def _execute_extraction_step(self, current_step: str) -> bool:
        """Execute data extraction action."""
        logger.info(f"Executing data extraction for: {current_step}")
        action_success = await self.agent.action_executor.execute_extraction_action(
            current_step
        )

        if action_success:
            success = await self.agent.utils_module.progress_to_next_step(verified=True)
            return True
        else:
            logger.warning(f"Extraction action failed for step: {current_step}")
            # For extraction, we can proceed but mark as unverified
            await self.agent.utils_module.progress_to_next_step(verified=False)
            return True  # Continue execution

    async def _execute_verification_step(self, current_step: str) -> bool:
        """Execute verification action."""
        logger.info(f"Executing verification action for: {current_step}")
        action_success = await self.agent.action_executor.execute_verification_action(
            current_step
        )

        if action_success:
            success = await self.agent.utils_module.progress_to_next_step(verified=True)
            return True
        else:
            logger.warning(f"Verification action failed for step: {current_step}")
            # For verification, we can proceed but mark as unverified
            await self.agent.utils_module.progress_to_next_step(verified=False)
            return True  # Continue execution

    async def _execute_creation_step(self, current_step: str) -> bool:
        """Execute file creation action."""
        logger.info(f"Executing file creation for: {current_step}")
        action_success = await self.agent.action_executor.execute_creation_action(
            current_step
        )

        if action_success:
            # For creation actions, also verify the deliverable was actually created
            from app.agent.deliverable_verifier import DeliverableVerifier

            verifier = DeliverableVerifier()
            deliverable_verified = await verifier.verify_deliverable_creation(
                current_step
            )

            if deliverable_verified:
                # Update report completion status after creation
                self.agent.action_executor.update_report_completion()
                success = await self.agent.utils_module.progress_to_next_step(
                    verified=True
                )
                return True
            else:
                logger.warning(
                    f"Creation action completed but deliverable not verified for step: {current_step}"
                )
                # Creation step must be verified to proceed
                return False  # Do not progress, retry this step
        else:
            logger.warning(f"Creation action failed for step: {current_step}")
            # Creation failure is critical - do not progress
            return False  # Do not progress, retry this step

    async def _execute_navigation_step(self, current_step: str) -> bool:
        """Execute navigation action."""
        logger.info(f"Executing navigation for: {current_step}")
        action_success = await self.agent.action_executor.execute_navigation_action(
            current_step
        )

        if action_success:
            success = await self.agent.utils_module.progress_to_next_step(verified=True)
            return True
        else:
            logger.warning(f"Navigation action failed for step: {current_step}")
            # For navigation, we can proceed but mark as unverified
            await self.agent.utils_module.progress_to_next_step(verified=False)
            return True  # Continue execution

    async def _execute_default_step(self, current_step: str) -> bool:
        """Execute default action."""
        logger.info(f"Executing default action for: {current_step}")
        action_success = await self.agent.action_executor.execute_default_action(
            current_step
        )

        if action_success:
            success = await self.agent.utils_module.progress_to_next_step(verified=True)
            return True
        else:
            logger.warning(f"Default action failed for step: {current_step}")
            # For default actions, we can proceed but mark as unverified
            await self.agent.utils_module.progress_to_next_step(verified=False)
            return True  # Continue execution

    async def handle_browser_initialization(self, url: str) -> bool:
        """Handle browser initialization if needed."""
        if not self.agent.browser_state.get("initialized"):
            browser_args = {"action": "initialize", "url": url}
            func = Function(name="browser_use", arguments=json.dumps(browser_args))
            self.agent.tool_calls = [
                ToolCall(
                    id="browser_init_" + str(int(time.time())),
                    type="function",
                    function=func,
                )
            ]
            return True
        return False
