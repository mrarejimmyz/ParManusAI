"""
Recovery strategies for agent monitoring.
"""

import time
from datetime import datetime
from typing import Any, Dict, List

from app.logger import logger

from .models import TaskState


class RecoveryManager:
    """Manages various recovery strategies for stuck agents"""

    def __init__(self):
        self.recovery_strategies = [
            "simplify_task",
            "change_approach",
            "skip_current_step",
            "restart_phase",
            "complete_with_partial",
        ]
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_count = 0
        self.circuit_breaker_cooldown = 300  # 5 minutes
        self.last_circuit_break = None

    async def smart_recovery(
        self, analysis: Dict[str, Any], task_state: TaskState
    ) -> Dict[str, Any]:
        """Apply intelligent recovery based on analysis"""
        if self._is_circuit_broken():
            return await self._handle_circuit_breaker_recovery()

        recommendation = analysis.get("recommendation", "change_strategy")
        stuck_indicators = analysis.get("stuck_indicators", [])

        # Choose strategy based on indicators
        if "loops" in stuck_indicators:
            return await self._break_loop_strategy()
        elif "stalled" in stuck_indicators:
            return await self._restart_current_phase(task_state)
        elif "high_errors" in stuck_indicators:
            return await self._simplify_task_strategy()
        elif "idle_time" in stuck_indicators:
            return await self._change_approach_strategy()
        else:
            return await self._default_recovery()

    async def _break_loop_strategy(self) -> Dict[str, Any]:
        """Break out of detected loops"""
        logger.info("🔄 Breaking loop pattern")

        return {
            "strategy": "break_loop",
            "action": "Skip repeated action and try alternative",
            "message": "Detected loop pattern - applying alternative approach",
        }

    async def _simplify_task_strategy(self) -> Dict[str, Any]:
        """Simplify the current task"""
        logger.info("📉 Simplifying task")

        return {
            "strategy": "simplify_task",
            "action": "Break down task into smaller steps",
            "message": "Task simplified to reduce complexity",
        }

    async def _change_approach_strategy(self) -> Dict[str, Any]:
        """Change the overall approach"""
        logger.info("🔄 Changing approach")

        return {
            "strategy": "change_approach",
            "action": "Try fundamentally different method",
            "message": "Switched to alternative approach",
        }

    async def _skip_current_step_strategy(self) -> Dict[str, Any]:
        """Skip the current step if it's not critical"""
        logger.info("⏭️ Skipping current step")

        return {
            "strategy": "skip_current_step",
            "action": "Move to next step",
            "message": "Skipped current step as non-critical",
        }

    async def _restart_current_phase(self, task_state: TaskState) -> Dict[str, Any]:
        """Restart the current phase"""
        logger.info("🔄 Restarting current phase")

        if task_state:
            task_state.step = max(0, task_state.step - 2)
            task_state.last_progress = datetime.now()

        return {
            "strategy": "restart_phase",
            "action": "Restart current phase with fresh approach",
            "message": "Phase restarted with clean state",
        }

    async def _complete_with_partial_results(self) -> Dict[str, Any]:
        """Complete task with current partial results"""
        logger.info("✅ Completing with partial results")

        return {
            "strategy": "complete_with_partial",
            "action": "Mark task as complete with current results",
            "message": "Task completed with available partial results",
        }

    async def _default_recovery(self) -> Dict[str, Any]:
        """Default recovery when other strategies fail"""
        logger.info("🔧 Applying default recovery")

        return {
            "strategy": "default",
            "action": "Apply generic recovery measures",
            "message": "Applied default recovery strategy",
        }

    async def _final_recovery(self) -> Dict[str, Any]:
        """Final recovery when all strategies are exhausted"""
        logger.error(
            "🚨 All recovery strategies exhausted - requesting manual intervention"
        )

        return {
            "strategy": "manual_intervention",
            "action": "Request human assistance",
            "message": "All automated recovery attempts failed - manual intervention required",
            "requires_human": True,
        }

    def _is_circuit_broken(self) -> bool:
        """Check if circuit breaker is active"""
        if self.circuit_breaker_count >= self.circuit_breaker_threshold:
            if self.last_circuit_break:
                time_since_break = (
                    datetime.now() - self.last_circuit_break
                ).total_seconds()
                return time_since_break < self.circuit_breaker_cooldown
            return True
        return False

    async def _handle_circuit_breaker_recovery(self) -> Dict[str, Any]:
        """Handle circuit breaker activation"""
        logger.warning("🔌 Circuit breaker active - preventing action execution")

        return {
            "status": "circuit_breaker",
            "message": "Too many failures - circuit breaker active",
            "cooldown_remaining": self.circuit_breaker_cooldown,
        }

    async def handle_action_error(
        self, action: str, error: Exception, duration: float, task_state: TaskState
    ) -> Dict[str, Any]:
        """Handle action execution errors"""
        self.circuit_breaker_count += 1

        if self.circuit_breaker_count >= self.circuit_breaker_threshold:
            self.last_circuit_break = datetime.now()

        if task_state:
            task_state.errors.append(str(error))

        return {
            "status": "error",
            "error": str(error),
            "duration": duration,
            "circuit_breaker_count": self.circuit_breaker_count,
        }
