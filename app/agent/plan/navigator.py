"""
Plan navigation utilities for accessing current phase and step information.
"""

from typing import Dict, Optional

from app.logger import logger


class PlanNavigator:
    """Handles navigation through plan phases and steps."""

    def __init__(self, agent):
        self.agent = agent

    async def get_current_phase(self) -> Optional[Dict]:
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

    async def get_current_step(self) -> Optional[str]:
        """Get the current step from the current phase"""
        current_phase = await self.get_current_phase()
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

    def get_phase_count(self) -> int:
        """Get the total number of phases in the current plan."""
        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            return 0
        return len(self.agent.current_plan["phases"])

    def get_step_count(self, phase_index: Optional[int] = None) -> int:
        """Get the number of steps in a specific phase (default: current phase)."""
        if phase_index is None:
            phase_index = self.agent.current_phase

        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            return 0

        if phase_index < 0 or phase_index >= len(self.agent.current_plan["phases"]):
            return 0

        phase = self.agent.current_plan["phases"][phase_index]
        if "steps" not in phase:
            return 0

        return len(phase["steps"])
