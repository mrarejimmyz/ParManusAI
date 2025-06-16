"""
Plan Generator
Formats and structures plans from analyzer output
"""

from typing import Dict


class PlanGenerator:
    """
    Formats and enhances plans from the analyzer
    """

    @staticmethod
    def enhance_plan(plan: Dict) -> Dict:
        """
        Enhance the plan with additional metadata and validation
        """
        # Ensure all required fields are present
        if not plan.get("goal"):
            plan["goal"] = "Complete user request"

        if not plan.get("task_type"):
            plan["task_type"] = "general"

        if not plan.get("complexity"):
            plan["complexity"] = "moderate"

        if not plan.get("estimated_duration"):
            plan["estimated_duration"] = "5-10 minutes"

        if not plan.get("priority"):
            plan["priority"] = "medium"

        # Ensure phases have proper structure
        phases = plan.get("phases", [])
        for i, phase in enumerate(phases):
            if not phase.get("id"):
                phase["id"] = i + 1

            if not phase.get("title"):
                phase["title"] = f"Phase {phase['id']}"

            if not phase.get("description"):
                phase["description"] = f"Execute phase {phase['id']} tasks"

            if not phase.get("steps"):
                phase["steps"] = ["Complete phase tasks"]

            if not phase.get("tools_needed"):
                phase["tools_needed"] = ["general"]

            if not phase.get("success_criteria"):
                phase["success_criteria"] = "All steps completed"

            if not phase.get("estimated_time"):
                phase["estimated_time"] = "2-3 minutes"

        # Add progress tracking fields
        plan["current_phase"] = 0
        plan["current_step"] = 0
        plan["status"] = "pending"
        plan["completed_phases"] = []

        return plan

    @staticmethod
    def validate_plan(plan: Dict) -> bool:
        """
        Validate that the plan has all required components
        """
        required_fields = ["goal", "task_type", "phases"]

        for field in required_fields:
            if field not in plan:
                return False

        # Validate phases
        phases = plan.get("phases", [])
        if not phases:
            return False

        for phase in phases:
            required_phase_fields = ["id", "title", "steps"]
            for field in required_phase_fields:
                if field not in phase:
                    return False

        return True
