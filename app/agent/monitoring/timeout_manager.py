"""
Timeout management for agent monitoring.
"""

import asyncio
from collections import deque
from typing import Any, Dict, List

from app.logger import logger
from app.utils.string_safety import safe_lower

from .models import ActionHistory


class TimeoutManager:
    """Intelligent timeout calculation and handling"""

    def __init__(self):
        self.action_history: deque = deque(maxlen=50)

    def calculate_smart_timeout(self, action: str, base_timeout: float) -> float:
        """Calculate intelligent timeout based on action history"""
        # Get historical data for similar actions
        similar_actions = [
            h
            for h in self.action_history
            if safe_lower(action) in safe_lower(h.action)
            or safe_lower(h.action) in safe_lower(action)
        ]

        if similar_actions:
            avg_duration = sum(h.duration for h in similar_actions) / len(
                similar_actions
            )
            # Add 50% buffer to average duration
            smart_timeout = avg_duration * 1.5
            # But don't exceed 3x base timeout or go below base timeout
            return max(base_timeout, min(smart_timeout, base_timeout * 3))

        return base_timeout

    async def handle_smart_timeout(self, action: str, timeout: float) -> Dict[str, Any]:
        """Handle timeout with intelligent recovery"""
        logger.warning(f"⏱️ Action '{action}' timed out after {timeout}s")

        # Analyze why timeout occurred
        timeout_analysis = await self._analyze_timeout_cause(action)

        # Suggest recovery based on analysis
        if timeout_analysis.get("likely_cause") == "heavy_computation":
            return {
                "status": "timeout_retry",
                "message": "Heavy computation detected, will retry with longer timeout",
                "suggested_timeout": timeout * 2,
                "output": f"Timeout due to heavy computation",
            }
        elif timeout_analysis.get("likely_cause") == "network_delay":
            return {
                "status": "timeout_network",
                "message": "Network delay detected, will retry with exponential backoff",
                "output": f"Timeout due to network issues",
            }
        else:
            return {
                "status": "timeout_stuck",
                "message": "Agent appears stuck, triggering recovery",
                "output": f"Action stuck - timeout after {timeout}s",
            }

    async def _analyze_timeout_cause(self, action: str) -> Dict[str, Any]:
        """Analyze likely cause of timeout"""
        # Check recent actions for patterns
        recent_actions = list(self.action_history)[-5:]

        # Check for computation-heavy actions
        computation_keywords = ["search", "analyze", "process", "generate", "scrape"]
        if any(keyword in safe_lower(action) for keyword in computation_keywords):
            return {"likely_cause": "heavy_computation"}

        # Check for network-related actions
        network_keywords = ["web", "url", "download", "fetch", "api"]
        if any(keyword in safe_lower(action) for keyword in network_keywords):
            return {"likely_cause": "network_delay"}

        # Check for repeated similar actions (stuck pattern)
        similar_recent = sum(
            1 for h in recent_actions if safe_lower(action) in safe_lower(h.action)
        )
        if similar_recent >= 3:
            return {"likely_cause": "stuck_pattern"}

        return {"likely_cause": "unknown"}
