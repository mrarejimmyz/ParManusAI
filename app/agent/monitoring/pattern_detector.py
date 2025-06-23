"""
Pattern detection for agent monitoring.
"""

import glob
import os
from collections import deque
from datetime import datetime
from typing import Any, Dict, List

from app.logger import logger
from app.utils.string_safety import safe_lower

from .models import ActionHistory, FileTracker, TaskState


class PatternDetector:
    """Detects patterns in agent behavior and file creation"""

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = workspace_path
        self.max_repeated_patterns = 5
        self.min_actions_before_stuck_check = 3

    def is_action_pattern_repeating(self, action: str, action_history: deque) -> bool:
        """Check if action is part of a repeating pattern"""
        if len(action_history) < 3:
            return False

        recent_actions = list(action_history)[-6:]  # Last 6 actions
        action_lower = safe_lower(action)  # Count similar actions in recent history
        similar_count = sum(
            1
            for h in recent_actions
            if action_lower in safe_lower(h.action)
            or safe_lower(h.action) in action_lower
        )

        return similar_count >= self.max_repeated_patterns

    def analyze_action_patterns(self, action_history: deque) -> Dict[str, Any]:
        """Analyze action patterns for loops and inefficiencies"""
        if len(action_history) < 3:
            return {"has_loops": False, "pattern_strength": 0}

        recent_actions = list(action_history)[-10:]  # Last 10 actions
        action_types = [safe_lower(h.action) for h in recent_actions]

        # Check for immediate loops (A->B->A pattern)
        immediate_loops = 0
        for i in range(len(action_types) - 2):
            if action_types[i] == action_types[i + 2]:
                immediate_loops += 1

        # Check for sequence repetition
        sequence_loops = 0
        for seq_len in range(2, 4):  # Check sequences of length 2-3
            for i in range(len(action_types) - seq_len * 2):
                seq1 = action_types[i : i + seq_len]
                seq2 = action_types[i + seq_len : i + seq_len * 2]
                if seq1 == seq2:
                    sequence_loops += 1

        pattern_strength = immediate_loops + sequence_loops * 2
        has_loops = pattern_strength >= 3

        return {
            "has_loops": has_loops,
            "pattern_strength": pattern_strength,
            "immediate_loops": immediate_loops,
            "sequence_loops": sequence_loops,
        }

    def extract_topic_from_action(self, action_lower: str) -> list:
        """Extract topic keywords from action for duplicate prevention"""
        topics = []

        # Core research topics
        if any(
            word in action_lower
            for word in ["artificial intelligence", "ai", "machine learning"]
        ):
            topics.append("ai")
        elif any(word in action_lower for word in ["development", "programming"]):
            topics.append("development")
        elif any(word in action_lower for word in ["blockchain", "crypto"]):
            topics.append("blockchain")
        elif any(word in action_lower for word in ["nepal", "nepalese"]):
            topics.append("nepal")
        elif any(word in action_lower for word in ["economics", "economic"]):
            topics.append("economics")
        elif any(word in action_lower for word in ["politics", "political"]):
            topics.append("politics")
        elif any(word in action_lower for word in ["technology", "tech"]):
            topics.append("technology")
        elif any(word in action_lower for word in ["analysis", "research"]):
            topics.append("analysis")

        return topics if topics else ["general"]

    def get_topic_keywords(self, topic: str) -> list:
        """Get expanded keywords for a topic"""
        keyword_map = {
            "ai": [
                "artificial intelligence",
                "machine learning",
                "deep learning",
                "neural networks",
                "ai",
                "ml",
                "automation",
            ],
            "development": [
                "development",
                "programming",
                "software",
                "coding",
                "engineering",
                "advancement",
                "growth",
            ],
            "analysis": [
                "analysis",
                "study",
                "research",
                "investigation",
                "examination",
            ],
            "technology": ["technology", "tech", "innovation", "digital", "software"],
            "blockchain": ["blockchain", "crypto", "bitcoin", "ethereum", "defi"],
            "nepal": ["nepal", "nepalese", "kathmandu", "himalayan", "south asian"],
            "economics": ["economics", "economic", "finance", "market", "trade"],
            "politics": ["politics", "political", "government", "policy", "governance"],
        }
        return keyword_map.get(topic, [topic])

    async def check_resource_availability(self) -> bool:
        """Check if system resources are available"""
        # Check disk space
        try:
            import shutil

            _, _, free = shutil.disk_usage(self.workspace_path)
            if free < 100 * 1024 * 1024:  # Less than 100MB
                return False
        except:
            pass

        # Check if too many files in workspace
        try:
            file_count = len(glob.glob(os.path.join(self.workspace_path, "*")))
            if file_count > 100:  # Too many files
                logger.warning(
                    f"⚠️ Workspace has {file_count} files - cleanup recommended"
                )
                return False
        except:
            pass

        return True
