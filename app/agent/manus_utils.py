import asyncio
import json
import os
import time
from typing import Dict, List, Optional

from app.exceptions import AgentTaskComplete
from app.logger import logger


class ManusUtils:
    def __init__(self, agent):
        self.agent = agent
        self.last_progression_time = 0

    async def _validate_current_position(self) -> bool:
        """Validate current phase and step indices"""
        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            return False

        # Check phase bounds
        if self.agent.current_phase < 0 or self.agent.current_phase >= len(
            self.agent.current_plan["phases"]
        ):
            logger.error(f"Invalid phase index: {self.agent.current_phase}")
            return False

        current_phase = self.agent.current_plan["phases"][self.agent.current_phase]
        if "steps" not in current_phase:
            logger.error("Current phase has no steps")
            return False

        # Check step bounds - allow being at the end of phase for progression
        if self.agent.current_step < 0:
            logger.error(f"Invalid step index: {self.agent.current_step}")
            return False

        # If step is beyond the current phase, check if we can progress to next phase
        if self.agent.current_step >= len(current_phase["steps"]):
            # This is acceptable if we're at the end and can progress to next phase
            if self.agent.current_step == len(current_phase["steps"]):
                # We're at the end of current phase, this is valid for progression
                logger.info(
                    f"At end of phase {self.agent.current_phase}, step {self.agent.current_step} (max: {len(current_phase['steps'])})"
                )
                return True
            else:
                # We're way beyond, auto-correct this
                logger.warning(
                    f"Step index {self.agent.current_step} beyond bounds (max: {len(current_phase['steps'])-1}), auto-correcting"
                )
                # Auto-correct by setting to the end of phase for progression
                self.agent.current_step = len(current_phase["steps"])
                logger.info(
                    f"Auto-corrected step to {self.agent.current_step} (end of phase)"
                )
                return True

        return True

    async def _get_current_phase(self) -> Optional[Dict]:
        """Get the current phase from the plan"""
        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            logger.error("No valid plan exists")
            return None

        try:
            if self.agent.current_phase < 0 or self.agent.current_phase >= len(
                self.agent.current_plan["phases"]
            ):
                logger.error(f"Phase index {self.agent.current_phase} out of range")
                return None
            return self.agent.current_plan["phases"][self.agent.current_phase]
        except (IndexError, KeyError) as e:
            logger.error(f"Error getting current phase: {str(e)}")
            return None

    async def _get_current_step(self) -> Optional[str]:
        """Get the current step from the current phase"""
        current_phase = await self._get_current_phase()
        if not current_phase or "steps" not in current_phase:
            return None

        try:
            # Allow being at the end of phase for progression
            if self.agent.current_step < 0:
                logger.error(f"Step index {self.agent.current_step} out of range")
                return None
            elif self.agent.current_step >= len(current_phase["steps"]):
                # At end of phase - this is valid for phase transition
                if self.agent.current_step == len(current_phase["steps"]):
                    logger.debug(f"At end of phase, step {self.agent.current_step}")
                    return "phase_complete"  # Special indicator
                else:
                    # Way beyond - auto-correct
                    logger.warning(
                        f"Step index {self.agent.current_step} too high, auto-correcting to {len(current_phase['steps'])-1}"
                    )
                    self.agent.current_step = len(current_phase["steps"]) - 1
                    return current_phase["steps"][self.agent.current_step]
            else:
                return current_phase["steps"][self.agent.current_step]
        except (IndexError, KeyError) as e:
            logger.error(f"Error getting current step: {str(e)}")
            return None

    async def progress_to_next_step(self) -> bool:
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

        current_phase = await self._get_current_phase()
        if not current_phase or "steps" not in current_phase:
            logger.error("No valid phase for progression")
            return False

        # Check if we can move to next step in current phase
        if self.agent.current_step + 1 < len(current_phase["steps"]):
            self.agent.current_step += 1
            logger.info(
                f"Progressed to step {self.agent.current_step} in phase {self.agent.current_phase}"
            )
            await self.agent.update_todo_progress()
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
        next_phase = self.agent.current_phase + 1

        # Check if we've completed all phases
        if next_phase >= len(self.agent.current_plan["phases"]):
            logger.info("All phases complete!")
            raise AgentTaskComplete("All phases of the plan have been completed")

        # Move to next phase
        self.agent.current_phase = next_phase
        self.agent.current_step = 0  # Reset step counter for new phase
        logger.info(
            f"Progressed to phase {self.agent.current_phase}, step {self.agent.current_step}"
        )
        await self.agent.update_todo_progress()
        return True

    async def recover_from_invalid_position(self) -> bool:
        """Recover from invalid position by resetting to valid indices"""
        try:
            if not self.agent.current_plan or "phases" not in self.agent.current_plan:
                logger.error("Cannot recover: no valid plan exists")
                return False

            # Reset phase if out of bounds
            if self.agent.current_phase >= len(self.agent.current_plan["phases"]):
                self.agent.current_phase = len(self.agent.current_plan["phases"]) - 1
            elif self.agent.current_phase < 0:
                self.agent.current_phase = 0

            # Reset step if out of bounds
            current_phase = self.agent.current_plan["phases"][self.agent.current_phase]
            if "steps" in current_phase:
                if self.agent.current_step >= len(current_phase["steps"]):
                    # If we're past the last step, try to move to next phase
                    if self.agent.current_phase + 1 < len(
                        self.agent.current_plan["phases"]
                    ):
                        logger.info("Moving to next phase during recovery")
                        self.agent.current_phase += 1
                        self.agent.current_step = 0
                    else:
                        # We're at the last phase, set to last valid step
                        self.agent.current_step = len(current_phase["steps"]) - 1
                elif self.agent.current_step < 0:
                    self.agent.current_step = 0
            else:
                self.agent.current_step = 0

            logger.info(
                f"Position recovered to phase {self.agent.current_phase}, step {self.agent.current_step}"
            )
            return True

        except Exception as e:
            logger.error(f"Error during position recovery: {str(e)}")
            return False

    async def sync_with_base_framework(self) -> bool:
        """Synchronize our step tracking with the base framework's step counter"""
        try:
            # This method helps coordinate between our plan-based step tracking
            # and the base framework's automatic step incrementing
            if not self.agent.current_plan or "phases" not in self.agent.current_plan:
                return False

            current_phase = await self._get_current_phase()
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
