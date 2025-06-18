"""
Plan validation utilities for ensuring plan integrity and position validity.
"""

from typing import Dict, List, Optional

from app.logger import logger


class PlanValidator:
    """Handles validation of plan structure and current position."""

    def __init__(self, agent):
        self.agent = agent

    def validate_current_position(self) -> bool:
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

    def validate_plan_structure(self, plan: Dict) -> bool:
        """Validate the overall structure of a plan."""
        if not plan or not isinstance(plan, dict):
            return False

        if "phases" not in plan:
            return False

        phases = plan["phases"]
        if not isinstance(phases, list) or len(phases) == 0:
            return False

        # Validate each phase
        for i, phase in enumerate(phases):
            if not isinstance(phase, dict):
                logger.error(f"Phase {i} is not a dictionary")
                return False

            if "steps" not in phase:
                logger.error(f"Phase {i} has no steps")
                return False

            steps = phase["steps"]
            if not isinstance(steps, list):
                logger.error(f"Phase {i} steps is not a list")
                return False

        return True
