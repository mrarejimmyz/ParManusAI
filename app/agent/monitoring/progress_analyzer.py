"""
Progress analysis for agent monitoring.
"""

from collections import deque
from datetime import datetime
from typing import Any, Dict, List

from .models import ActionHistory, TaskState


class ProgressAnalyzer:
    """Analyzes agent progress and task state"""

    def __init__(self, max_idle_time: float = 300.0):
        self.max_idle_time = max_idle_time

    def analyze_progress(self, task_state: TaskState) -> Dict[str, Any]:
        """Analyze task progress"""
        if not task_state:
            return {"stalled": True}

        # Check if making progress
        expected_progress = (task_state.step / task_state.max_steps) * 100
        actual_progress = task_state.progress_percentage

        stalled = (
            task_state.step == 0  # Never started
            or actual_progress < expected_progress * 0.5  # Way behind
            or len(task_state.deliverables) == 0  # No outputs
        )

        return {
            "stalled": stalled,
            "expected_progress": expected_progress,
            "actual_progress": actual_progress,
            "deliverables_count": len(task_state.deliverables),
        }

    def analyze_errors(self, action_history: deque) -> Dict[str, Any]:
        """Analyze error patterns"""
        recent_errors = [
            h
            for h in action_history
            if h.outcome == "error"
            and (datetime.now() - h.timestamp).total_seconds() < 300  # Last 5 minutes
        ]

        error_rate = len(recent_errors) / max(len(action_history), 1)

        return {
            "error_rate_high": error_rate > 0.3,  # More than 30% errors
            "recent_errors": len(recent_errors),
            "error_rate": error_rate,
        }

    def comprehensive_analysis(
        self,
        task_state: TaskState,
        action_history: deque,
        pattern_analysis: Dict[str, Any],
        min_actions_before_stuck_check: int = 3,
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis of agent state"""
        if not task_state:
            return {"is_stuck": False}

        current_time = datetime.now()

        # Time-based analysis
        time_since_progress = (current_time - task_state.last_progress).total_seconds()
        task_duration = (current_time - task_state.start_time).total_seconds()

        # Progress analysis
        progress_analysis = self.analyze_progress(task_state)

        # Error analysis
        error_analysis = self.analyze_errors(action_history)

        # Determine if stuck - require multiple indicators or minimum actions
        action_count = len(action_history)

        # Don't detect stuck until we have some history
        if action_count < min_actions_before_stuck_check:
            is_stuck = False
        else:
            # Require at least 2 indicators or very clear single indicator
            stuck_indicators = []

            if time_since_progress > self.max_idle_time:
                stuck_indicators.append("idle_time")
            if pattern_analysis.get("has_loops", False):
                stuck_indicators.append("loops")
            if error_analysis.get("error_rate_high", False):
                stuck_indicators.append("high_errors")
            if progress_analysis.get("stalled", False) and action_count > 5:
                stuck_indicators.append("stalled")

            # Need at least 2 indicators, or very strong single indicator
            is_stuck = len(stuck_indicators) >= 2 or (
                len(stuck_indicators) == 1
                and stuck_indicators[0] == "idle_time"
                and time_since_progress > self.max_idle_time * 1.5
            )

        return {
            "is_stuck": is_stuck,
            "stuck_indicators": (
                stuck_indicators if "stuck_indicators" in locals() else []
            ),
            "time_since_progress": time_since_progress,
            "task_duration": task_duration,
            "action_count": action_count,
            "pattern_analysis": pattern_analysis,
            "progress_analysis": progress_analysis,
            "error_analysis": error_analysis,
        }

    def get_recommendation(
        self, is_stuck: bool, pattern_analysis: Dict, progress_analysis: Dict
    ) -> str:
        """Get recommendation based on analysis"""
        if not is_stuck:
            return "continue"

        if pattern_analysis.get("has_loops"):
            return "break_loop"
        elif progress_analysis.get("stalled"):
            return "restart_task"
        else:
            return "change_strategy"
