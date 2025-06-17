"""
Agent Self-Monitor
Analyzes agent state and behavior to prevent getting stuck and ensure progress
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.logger import logger


@dataclass
class AgentState:
    """Represents the current state of the agent"""

    current_action: str
    start_time: datetime
    last_progress_time: datetime
    iteration_count: int
    last_output: str
    repeated_actions: List[str]
    error_count: int
    stuck_indicators: List[str]


class AgentSelfMonitor:
    """Monitors agent behavior and prevents getting stuck"""

    def __init__(self, llm=None):
        self.llm = llm
        self.agent_state = AgentState(
            current_action="",
            start_time=datetime.now(),
            last_progress_time=datetime.now(),
            iteration_count=0,
            last_output="",
            repeated_actions=[],
            error_count=0,
            stuck_indicators=[],
        )

        # Thresholds for detecting problems
        self.max_iterations_without_progress = 5
        self.max_time_without_progress = 300  # 5 minutes
        self.max_repeated_actions = 3
        self.max_error_count = 3

    async def monitor_action(self, action: str, output: str = "") -> Dict[str, Any]:
        """Monitor an agent action and analyze if agent is making progress"""
        self.agent_state.iteration_count += 1
        previous_action = self.agent_state.current_action
        self.agent_state.current_action = action
        self.agent_state.last_output = output

        # Track repeated actions
        if action == previous_action:
            self.agent_state.repeated_actions.append(action)
        else:
            self.agent_state.repeated_actions = []

        # Check for progress indicators
        if self._indicates_progress(action, output):
            self.agent_state.last_progress_time = datetime.now()
            self.agent_state.repeated_actions = []  # Reset on progress

        # Analyze current state
        analysis = await self._analyze_agent_state()

        if analysis["is_stuck"]:
            logger.warning(f"🔄 Agent appears to be stuck: {analysis['reason']}")
            intervention = await self._suggest_intervention()
            analysis["intervention"] = intervention

        return analysis

    def _indicates_progress(self, action: str, output: str) -> bool:
        """Check if action/output indicates real progress"""
        progress_indicators = [
            "successfully",
            "completed",
            "found",
            "extracted",
            "generated",
            "created",
            "saved",
            "updated",
            "analysis complete",
            "search results",
            "data retrieved",
        ]

        text_to_check = f"{action} {output}".lower()
        return any(indicator in text_to_check for indicator in progress_indicators)

    async def _analyze_agent_state(self) -> Dict[str, Any]:
        """Analyze current agent state for problems"""
        current_time = datetime.now()
        time_since_progress = (
            current_time - self.agent_state.last_progress_time
        ).total_seconds()

        stuck_reasons = []

        # Check for repeated actions
        if len(self.agent_state.repeated_actions) >= self.max_repeated_actions:
            stuck_reasons.append(
                f"Repeated same action {len(self.agent_state.repeated_actions)} times"
            )

        # Check for time without progress
        if time_since_progress > self.max_time_without_progress:
            stuck_reasons.append(f"No progress for {time_since_progress:.0f} seconds")

        # Check for excessive iterations
        if self.agent_state.iteration_count > self.max_iterations_without_progress:
            time_since_start = (
                current_time - self.agent_state.start_time
            ).total_seconds()
            if time_since_start > 60:  # Only flag if more than 1 minute has passed
                stuck_reasons.append(
                    f"High iteration count ({self.agent_state.iteration_count}) without resolution"
                )

        # Check for error patterns
        if self.agent_state.error_count >= self.max_error_count:
            stuck_reasons.append(f"Too many errors ({self.agent_state.error_count})")

        is_stuck = len(stuck_reasons) > 0

        return {
            "is_stuck": is_stuck,
            "reason": "; ".join(stuck_reasons) if stuck_reasons else None,
            "iteration_count": self.agent_state.iteration_count,
            "time_since_progress": time_since_progress,
            "repeated_actions": len(self.agent_state.repeated_actions),
            "current_action": self.agent_state.current_action,
        }

    async def _suggest_intervention(self) -> Dict[str, Any]:
        """Suggest intervention when agent is stuck"""
        if not self.llm:
            return self._fallback_intervention()

        try:
            prompt = f"""The agent appears to be stuck. Analyze the situation and suggest a specific intervention:

Current Action: {self.agent_state.current_action}
Iteration Count: {self.agent_state.iteration_count}
Repeated Actions: {len(self.agent_state.repeated_actions)}
Last Output: {self.agent_state.last_output[:200]}...

Suggest a specific intervention strategy. Choose from:
1. "change_approach" - Try a different method or tool
2. "simplify_task" - Break down the current task into smaller steps
3. "skip_step" - Move on to the next step if current is non-critical
4. "restart_phase" - Go back and restart the current phase
5. "request_help" - Ask for user guidance

Respond with just the intervention type and a brief explanation."""

            response = await self.llm.ask(prompt)

            # Parse response
            lines = response.strip().split("\n")
            intervention_type = lines[0].lower().replace('"', "").strip()
            explanation = lines[1] if len(lines) > 1 else "LLM suggested intervention"

            return {
                "type": intervention_type,
                "explanation": explanation,
                "suggested_action": self._get_intervention_action(intervention_type),
            }

        except Exception as e:
            logger.warning(f"LLM intervention suggestion failed: {e}")
            return self._fallback_intervention()

    def _fallback_intervention(self) -> Dict[str, Any]:
        """Fallback intervention logic when LLM is unavailable"""
        # Simple rule-based intervention
        if len(self.agent_state.repeated_actions) >= 3:
            return {
                "type": "change_approach",
                "explanation": "Detected repeated actions, suggesting approach change",
                "suggested_action": "Try a different search strategy or tool",
            }
        elif self.agent_state.iteration_count > 10:
            return {
                "type": "simplify_task",
                "explanation": "High iteration count, suggesting task simplification",
                "suggested_action": "Break current task into smaller, more specific steps",
            }
        else:
            return {
                "type": "restart_phase",
                "explanation": "General stuck condition, suggesting phase restart",
                "suggested_action": "Restart current phase with fresh approach",
            }

    def _get_intervention_action(self, intervention_type: str) -> str:
        """Get specific action for intervention type"""
        actions = {
            "change_approach": "Try a different search method, tool, or strategy",
            "simplify_task": "Break the current task into 2-3 smaller, specific steps",
            "skip_step": "Mark current step as optional and move to next step",
            "restart_phase": "Start the current phase over with a fresh approach",
            "request_help": "Pause and ask user for guidance or clarification",
        }
        return actions.get(intervention_type, "Continue with alternative approach")

    def mark_error(self, error_message: str):
        """Mark an error occurrence"""
        self.agent_state.error_count += 1
        self.agent_state.stuck_indicators.append(f"Error: {error_message[:100]}")
        logger.debug(f"Agent error count: {self.agent_state.error_count}")

    def reset_monitoring(self):
        """Reset monitoring state (e.g., when starting new task)"""
        self.agent_state = AgentState(
            current_action="",
            start_time=datetime.now(),
            last_progress_time=datetime.now(),
            iteration_count=0,
            last_output="",
            repeated_actions=[],
            error_count=0,
            stuck_indicators=[],
        )
        logger.info("🔄 Reset agent monitoring state")

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall agent health status"""
        current_time = datetime.now()
        time_since_progress = (
            current_time - self.agent_state.last_progress_time
        ).total_seconds()

        # Determine health status
        if time_since_progress < 60 and self.agent_state.error_count == 0:
            status = "healthy"
        elif time_since_progress < 300 and self.agent_state.error_count < 2:
            status = "ok"
        elif (
            len(self.agent_state.repeated_actions) < 3
            and self.agent_state.error_count < 3
        ):
            status = "warning"
        else:
            status = "critical"

        return {
            "status": status,
            "uptime": (current_time - self.agent_state.start_time).total_seconds(),
            "time_since_progress": time_since_progress,
            "iteration_count": self.agent_state.iteration_count,
            "error_count": self.agent_state.error_count,
            "repeated_actions": len(self.agent_state.repeated_actions),
        }
