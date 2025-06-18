"""
Data models for agent monitoring system.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Set


@dataclass
class ActionHistory:
    """Track action history for pattern detection"""

    action: str
    timestamp: datetime
    outcome: str
    duration: float
    output_snippet: str


@dataclass
class FileTracker:
    """Track file creation to prevent duplicates"""

    created_files: Set[str] = field(default_factory=set)
    file_patterns: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_cleanup: datetime = field(default_factory=datetime.now)


@dataclass
class TaskState:
    """Enhanced task state tracking"""

    task_name: str
    start_time: datetime
    last_progress: datetime
    phase: str = "unknown"
    step: int = 0
    max_steps: int = 10
    progress_percentage: float = 0.0
    deliverables: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
