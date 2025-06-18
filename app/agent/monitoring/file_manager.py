"""
File management and status reporting for agent monitoring.
"""

import glob
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set

from app.logger import logger

from .models import ActionHistory, FileTracker, TaskState


class FileManager:
    """Manages file tracking and duplicate prevention"""

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = workspace_path
        self.file_tracker = FileTracker()
        self.duplicate_file_threshold = 3

    def track_file_creation(self, file_path: str, topic_keywords: List[str]):
        """Track file creation to prevent duplicates"""
        self.file_tracker.created_files.add(file_path)

        # Track patterns for each topic
        for topic in topic_keywords:
            self.file_tracker.file_patterns[topic] += 1

    def should_prevent_duplicate(self, topic_keywords: List[str]) -> bool:
        """Check if file creation should be prevented due to duplicates"""
        for topic in topic_keywords:
            if self.file_tracker.file_patterns[topic] >= self.duplicate_file_threshold:
                return True
        return False

    async def cleanup_duplicate_files(self):
        """Clean up duplicate files in workspace"""
        try:
            now = datetime.now()

            # Only cleanup every 10 minutes
            if (now - self.file_tracker.last_cleanup).total_seconds() < 600:
                return

            pattern_groups = defaultdict(list)

            # Group files by similar patterns
            for file_path in glob.glob(os.path.join(self.workspace_path, "*.md")):
                basename = os.path.basename(file_path).lower()

                # Extract topic from filename
                key_patterns = [
                    "ai",
                    "artificial",
                    "blockchain",
                    "crypto",
                    "nepal",
                    "development",
                    "analysis",
                    "research",
                    "technology",
                    "economics",
                    "politics",
                ]

                for pattern in key_patterns:
                    if pattern in basename:
                        pattern_groups[pattern].append(file_path)
                        break

            # Remove duplicates, keeping the newest
            for pattern, files in pattern_groups.items():
                if len(files) > self.duplicate_file_threshold:
                    # Sort by modification time, keep the newest
                    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
                    files_to_remove = files[1:]  # Remove all but the newest

                    for file_path in files_to_remove:
                        try:
                            os.remove(file_path)
                            logger.info(
                                f"🗑️ Cleaned up duplicate file: {os.path.basename(file_path)}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to remove {file_path}: {e}")

            self.file_tracker.last_cleanup = now

        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


class StatusReporter:
    """Generates status reports and health monitoring"""

    def __init__(self):
        pass

    def get_status_report(
        self,
        task_state: TaskState,
        action_history: deque,
        circuit_breaker_count: int,
        circuit_breaker_active: bool,
    ) -> Dict[str, Any]:
        """Get comprehensive status report"""
        if not task_state:
            return {"status": "no_active_task"}

        current_time = datetime.now()

        return {
            "task_name": task_state.task_name,
            "progress_percentage": task_state.progress_percentage,
            "current_step": task_state.step,
            "max_steps": task_state.max_steps,
            "task_duration": (current_time - task_state.start_time).total_seconds(),
            "time_since_progress": (
                current_time - task_state.last_progress
            ).total_seconds(),
            "circuit_breaker_count": circuit_breaker_count,
            "circuit_breaker_active": circuit_breaker_active,
            "recent_actions": len(action_history),
            "error_count": len(task_state.errors),
            "deliverables": len(task_state.deliverables),
            "health_status": self._get_health_status(
                task_state, action_history, circuit_breaker_active
            ),
        }

    def _get_health_status(
        self, task_state: TaskState, action_history: deque, circuit_breaker_active: bool
    ) -> str:
        """Get overall health status"""
        if not task_state:
            return "unknown"

        current_time = datetime.now()
        time_since_progress = (current_time - task_state.last_progress).total_seconds()

        if circuit_breaker_active:
            return "critical"
        elif time_since_progress > 300:  # 5 minutes
            return "warning"
        elif len(task_state.errors) > 3:
            return "warning"
        else:
            return "healthy"

    def record_action(
        self,
        action: str,
        outcome: str,
        duration: float,
        output: str,
        action_history: deque,
    ):
        """Record action in history"""
        history_entry = ActionHistory(
            action=action,
            timestamp=datetime.now(),
            outcome=outcome,
            duration=duration,
            output_snippet=output[:200] if output else "",
        )
        action_history.append(history_entry)

    def update_progress(self, task_state: TaskState):
        """Update progress tracking"""
        if task_state:
            task_state.last_progress = datetime.now()
            task_state.step += 1

            # Estimate progress based on step completion
            if task_state.max_steps > 0:
                estimated_progress = (task_state.step / task_state.max_steps) * 100
                task_state.progress_percentage = min(estimated_progress, 100.0)
