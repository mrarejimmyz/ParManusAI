"""
Refactored ManusUtils - Lightweight coordinator for plan management modules.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Optional

from app.agent.plan import (
    DeliverableVerifier,
    PlanNavigator,
    PlanValidator,
    ProgressionManager,
    RecoveryManager,
)
from app.exceptions import AgentTaskComplete
from app.logger import logger


class ManusUtils:
    """
    Lightweight coordinator for plan management.
    Delegates specific responsibilities to specialized modules.
    """

    def __init__(self, agent):
        self.agent = agent

        # Initialize specialized modules
        self.validator = PlanValidator(agent)
        self.navigator = PlanNavigator(agent)
        self.progression = ProgressionManager(agent)
        self.verifier = DeliverableVerifier(agent)
        self.recovery = RecoveryManager(agent)

        # Legacy properties for backward compatibility
        self.last_progression_time = self.progression.last_progression_time

    # Delegation methods for backward compatibility
    async def _validate_current_position(self) -> bool:
        """Validate current phase and step indices (delegates to validator)"""
        return self.validator.validate_current_position()

    async def _get_current_phase(self) -> Optional[Dict]:
        """Get the current phase from the plan (delegates to navigator)"""
        return await self.navigator.get_current_phase()

    async def _get_current_step(self) -> Optional[str]:
        """Get the current step from the current phase (delegates to navigator)"""
        return await self.navigator.get_current_step()

    async def progress_to_next_step(self, verified: bool = True) -> bool:
        """Progress to the next step (delegates to progression manager)"""
        return await self.progression.progress_to_next_step(verified)

    async def progress_to_next_phase(self) -> bool:
        """Progress to the next phase (delegates to progression manager)"""
        return await self.progression.progress_to_next_phase()

    async def _verify_all_deliverables_created(self) -> bool:
        """Verify deliverables (delegates to verifier)"""
        return await self.verifier.verify_all_deliverables_created()

    async def _add_completion_tasks_for_incomplete_reports(self, incomplete_reports):
        """Add completion tasks (delegates to verifier)"""
        return await self.verifier._add_completion_tasks_for_incomplete_reports(
            incomplete_reports
        )

    async def recover_from_invalid_position(self) -> bool:
        """Recover from invalid position (delegates to recovery manager)"""
        return await self.recovery.recover_from_invalid_position()

    async def sync_with_base_framework(self) -> bool:
        """Synchronize with base framework (delegates to progression manager)"""
        return await self.progression.sync_with_base_framework()

    # Additional convenience methods
    def get_plan_status(self) -> Dict:
        """Get comprehensive status of the current plan."""
        try:
            total_phases = self.navigator.get_phase_count()
            current_phase_steps = self.navigator.get_step_count()

            return {
                "current_phase": self.agent.current_phase,
                "current_step": self.agent.current_step,
                "total_phases": total_phases,
                "current_phase_steps": current_phase_steps,
                "has_valid_plan": total_phases > 0,
                "progress_percentage": (
                    (self.agent.current_phase / total_phases * 100)
                    if total_phases > 0
                    else 0
                ),
            }
        except Exception as e:
            logger.error(f"Error getting plan status: {e}")
            return {
                "current_phase": self.agent.current_phase,
                "current_step": self.agent.current_step,
                "total_phases": 0,
                "current_phase_steps": 0,
                "has_valid_plan": False,
                "progress_percentage": 0,
            }

    async def emergency_recovery(self) -> bool:
        """Emergency recovery that attempts multiple strategies."""
        return self.recovery.emergency_recovery()
