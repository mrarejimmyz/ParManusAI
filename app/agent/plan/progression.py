"""
Plan progression management for advancing through phases and steps.
"""

import time
from typing import Dict, Optional

from app.exceptions import AgentTaskComplete
from app.logger import logger


class ProgressionManager:
    """Handles progression through plan phases and steps."""

    def __init__(self, agent):
        self.agent = agent
        self.last_progression_time = 0

    async def progress_to_next_step(self, verified: bool = True) -> bool:
        """Progress to the next step in the current phase or next phase"""
        current_time = time.time()

        # Prevent rapid multiple progressions (cooldown of 0.1 seconds)
        if current_time - self.last_progression_time < 0.1:
            logger.debug("Progression cooldown active, skipping")
            return True

        self.last_progression_time = current_time

        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            logger.error("No valid plan exists for progression")
            return False

        # Import navigator here to avoid circular imports
        from .navigator import PlanNavigator

        navigator = PlanNavigator(self.agent)

        current_phase = await navigator.get_current_phase()
        if not current_phase or "steps" not in current_phase:
            logger.error("No valid phase for progression")
            return False

        # Record current step completion with verification status
        current_step = await navigator.get_current_step()
        if current_step and current_step != "phase_complete":
            if hasattr(self.agent, "planning_module") and hasattr(
                self.agent.planning_module, "todo_manager"
            ):
                await self.agent.planning_module.todo_manager.update_todo_progress(
                    current_step, verified
                )

        # Check if we can move to next step in current phase
        if self.agent.current_step + 1 < len(current_phase["steps"]):
            self.agent.current_step += 1
            logger.info(
                f"Progressed to step {self.agent.current_step} in phase {self.agent.current_phase}"
            )
            return True
        else:
            # We're at the end of current phase, move to next phase
            logger.info(
                f"Completed phase {self.agent.current_phase}, moving to next phase"
            )
            # Don't increment step here, let progress_to_next_phase handle it
            return await self.progress_to_next_phase()

    async def progress_to_next_phase(self) -> bool:
        """Progress to the next phase and reset step counter"""
        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            logger.error("No valid plan exists for phase progression")
            return False

        # Calculate next phase
        next_phase = self.agent.current_phase + 1  # Check if we've completed all phases
        if next_phase >= len(self.agent.current_plan["phases"]):
            # Import deliverable verifier here to avoid circular imports
            from .deliverable_verifier import DeliverableVerifier

            verifier = DeliverableVerifier(self.agent)

            # Before completing, verify all deliverables are actually created
            deliverables_verified = await verifier.verify_all_deliverables_created()

            if not deliverables_verified:
                # Incomplete deliverables found and completion tasks added
                # The plan now has more phases, so continue execution
                logger.info("🔄 Added completion tasks - continuing execution...")
                # Stay in current phase since new phases were inserted
                return True
            else:
                logger.info("All phases complete!")
                raise AgentTaskComplete(
                    "All phases of the plan have been completed with verified deliverables"
                )

        # Move to next phase
        self.agent.current_phase = next_phase
        self.agent.current_step = 0  # Reset step counter for new phase
        logger.info(
            f"Progressed to phase {self.agent.current_phase}, step {self.agent.current_step}"
        )
        return True

    async def sync_with_base_framework(self) -> bool:
        """Synchronize our step tracking with the base framework's step counter"""
        try:
            # This method helps coordinate between our plan-based step tracking
            # and the base framework's automatic step incrementing
            if not self.agent.current_plan or "phases" not in self.agent.current_plan:
                return False

            # Import navigator here to avoid circular imports
            from .navigator import PlanNavigator

            navigator = PlanNavigator(self.agent)

            current_phase = await navigator.get_current_phase()
            if not current_phase or "steps" not in current_phase:
                return False

            # If we've completed all steps in current phase, signal completion
            if self.agent.current_step >= len(current_phase["steps"]):
                logger.info("All steps in current phase completed")
                return await self.progress_to_next_phase()

            return True

        except AgentTaskComplete as e:
            # This is expected when all phases are complete - not an error
            logger.info(f"Task completed successfully: {str(e)}")
            # Re-raise to let the agent handle it properly
            raise e
        except Exception as e:
            logger.error(f"Error syncing with base framework: {str(e)}")
            return False
