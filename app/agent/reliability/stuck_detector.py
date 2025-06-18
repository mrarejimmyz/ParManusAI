"""
Stuck state detection utilities for identifying when an agent is in a loop.
"""

import time
from collections import deque
from typing import List

from app.logger import logger


class StuckStateDetector:
    """Advanced stuck state detection with multiple strategies."""

    def __init__(self, window_size: int = 5, similarity_threshold: float = 0.8):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.recent_responses = deque(maxlen=window_size)
        self.recent_actions = deque(maxlen=window_size)
        self.stuck_count = 0
        self.last_progress_time = time.time()

    def add_response(self, content: str, actions: List[str] = None):
        """Add a response for analysis."""
        self.recent_responses.append(content)
        if actions:
            self.recent_actions.append(tuple(actions))
        else:
            self.recent_actions.append(())

    def is_stuck(self) -> bool:
        """Detect if the agent is stuck using multiple strategies."""
        if len(self.recent_responses) < 2:
            return False

        # Strategy 1: Exact duplicate detection
        if self._has_exact_duplicates():
            self.stuck_count += 1
            logger.debug(f"Exact duplicate detected (count: {self.stuck_count})")
            return self.stuck_count >= 2

        # Strategy 2: Semantic similarity detection
        if self._has_semantic_similarity():
            self.stuck_count += 1
            logger.debug(f"Semantic similarity detected (count: {self.stuck_count})")
            return self.stuck_count >= 3

        # Strategy 3: Action repetition detection
        if self._has_action_repetition():
            self.stuck_count += 1
            logger.debug(f"Action repetition detected (count: {self.stuck_count})")
            return self.stuck_count >= 2

        # Strategy 4: Time-based stagnation
        if self._is_time_stagnant():
            self.stuck_count += 1
            logger.debug(f"Time stagnation detected (count: {self.stuck_count})")
            return self.stuck_count >= 1

        # Reset counter if no stuck condition detected
        self.stuck_count = max(0, self.stuck_count - 1)
        return False

    def _has_exact_duplicates(self) -> bool:
        """Check for exact duplicate responses."""
        if len(self.recent_responses) < 2:
            return False

        last_response = self.recent_responses[-1]
        return any(
            response == last_response for response in list(self.recent_responses)[:-1]
        )

    def _has_semantic_similarity(self) -> bool:
        """Check for semantically similar responses."""
        if len(self.recent_responses) < 2:
            return False

        try:
            from difflib import SequenceMatcher

            last_response = self.recent_responses[-1]
            for response in list(self.recent_responses)[:-1]:
                similarity = SequenceMatcher(None, response, last_response).ratio()
                if similarity > self.similarity_threshold:
                    return True
            return False
        except Exception as e:
            logger.debug(f"Error in semantic similarity check: {e}")
            return False

    def _has_action_repetition(self) -> bool:
        """Check for repeated action patterns."""
        if len(self.recent_actions) < 2:
            return False

        last_actions = self.recent_actions[-1]
        return any(
            actions == last_actions for actions in list(self.recent_actions)[:-1]
        )

    def _is_time_stagnant(self) -> bool:
        """Check if too much time has passed without progress."""
        return time.time() - self.last_progress_time > 300  # 5 minutes

    def reset(self):
        """Reset the detector state."""
        self.recent_responses.clear()
        self.recent_actions.clear()
        self.stuck_count = 0
        self.last_progress_time = time.time()

    def mark_progress(self):
        """Mark that progress has been made."""
        self.last_progress_time = time.time()
        self.stuck_count = 0
