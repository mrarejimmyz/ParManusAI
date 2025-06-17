"""
Report Name Generator Module
Handles intelligent filename generation for reports with various options
"""

import re
from datetime import datetime
from typing import Optional


class ReportNameGenerator:
    """
    Specialized module for generating unique, meaningful report filenames
    """

    def __init__(self):
        self.max_task_length = 50
        self.default_report_type = "analysis"

    def generate_report_name(
        self, task_description: str, report_type: str = None
    ) -> str:
        """
        Generate a unique report filename based on task description and type

        Args:
            task_description: The task or topic description
            report_type: Type of report (analysis, travel, research, etc.)

        Returns:
            A unique filename string
        """
        if report_type is None:
            report_type = self._determine_report_type(task_description)

        clean_task = self._clean_task_description(task_description)
        date_str = self._generate_timestamp()

        return f"{report_type}_{clean_task}_{date_str}.md"

    def _determine_report_type(self, task_description: str) -> str:
        """Automatically determine report type based on task description"""
        task_lower = task_description.lower()

        if any(
            word in task_lower
            for word in ["trip", "travel", "visit", "waterloo", "kathmandu"]
        ):
            return "travel"
        elif any(word in task_lower for word in ["analysis", "analyze", "study"]):
            return "analysis"
        elif any(word in task_lower for word in ["research", "investigate", "explore"]):
            return "research"
        elif any(word in task_lower for word in ["plan", "planning", "strategy"]):
            return "planning"
        elif any(word in task_lower for word in ["todo", "task", "action"]):
            return "todo"
        else:
            return self.default_report_type

    def _clean_task_description(self, task_description: str) -> str:
        """Clean and format task description for filename"""
        # Remove non-alphanumeric characters except spaces and hyphens
        clean_task = re.sub(r"[^\w\s-]", "", task_description.lower())

        # Replace spaces and multiple hyphens with single underscores
        clean_task = re.sub(r"[-\s]+", "_", clean_task)

        # Truncate if too long
        if len(clean_task) > self.max_task_length:
            clean_task = clean_task[: self.max_task_length].rstrip("_")

        # Remove leading/trailing underscores
        clean_task = clean_task.strip("_")

        # Ensure we have at least something
        if not clean_task:
            clean_task = "report"

        return clean_task

    def _generate_timestamp(self) -> str:
        """Generate timestamp for unique filename"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_specialized_name(
        self, task_description: str, report_type: str, suffix: Optional[str] = None
    ) -> str:
        """
        Generate specialized report name with custom suffix

        Args:
            task_description: The task description
            report_type: Specific report type
            suffix: Additional suffix (e.g., "draft", "final", "v2")

        Returns:
            Specialized filename
        """
        clean_task = self._clean_task_description(task_description)
        date_str = self._generate_timestamp()

        if suffix:
            return f"{report_type}_{clean_task}_{suffix}_{date_str}.md"
        else:
            return f"{report_type}_{clean_task}_{date_str}.md"

    def generate_todo_name(self, task_description: str) -> str:
        """Generate filename for todo/task files"""
        return self.generate_specialized_name(task_description, "todo", "tasks")

    def generate_analysis_name(
        self, task_description: str, analysis_type: str = None
    ) -> str:
        """Generate filename for analysis reports"""
        suffix = analysis_type if analysis_type else None
        return self.generate_specialized_name(task_description, "analysis", suffix)
