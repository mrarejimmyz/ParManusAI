"""
Recovery utilities for handling invalid plan states and positions.
"""

from app.logger import logger


class RecoveryManager:
    """Handles recovery from invalid plan states and positions."""

    def __init__(self, agent):
        self.agent = agent

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

    def reset_to_beginning(self) -> bool:
        """Reset agent position to the beginning of the plan."""
        try:
            if not self.agent.current_plan or "phases" not in self.agent.current_plan:
                logger.error("Cannot reset: no valid plan exists")
                return False

            self.agent.current_phase = 0
            self.agent.current_step = 0
            logger.info("Agent position reset to beginning of plan")
            return True

        except Exception as e:
            logger.error(f"Error resetting position: {str(e)}")
            return False

    def emergency_recovery(self) -> bool:
        """Emergency recovery that attempts multiple recovery strategies."""
        try:
            logger.warning("Attempting emergency recovery...")

            # First try normal position recovery
            if self.recover_from_invalid_position():
                logger.info("Emergency recovery successful via position recovery")
                return True

            # If that fails, try resetting to beginning
            if self.reset_to_beginning():
                logger.info("Emergency recovery successful via reset to beginning")
                return True

            # If all else fails, clear the plan entirely
            self.agent.current_plan = None
            self.agent.current_phase = 0
            self.agent.current_step = 0
            logger.warning("Emergency recovery cleared plan - agent will need new plan")
            return True

        except Exception as e:
            logger.error(f"Emergency recovery failed: {str(e)}")
            return False
