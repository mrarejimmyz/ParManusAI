"""
Planning Coordinator Module for Manus Agent
Coordinates task planning with LLM-driven and legacy planners.
"""

from typing import Dict, Optional

from app.logger import logger


class PlanningCoordinator:
    """Coordinates task planning between different planning systems."""

    def __init__(self, agent):
        self.agent = agent
        self.llm_planner = None

    def ensure_llm_planner(self):
        """Ensure LLM planner is initialized with the current LLM."""
        if self.llm_planner is None and self.agent.llm is not None:
            from app.llm_planning import LLMDrivenPlanner

            self.llm_planner = LLMDrivenPlanner(llm=self.agent.llm)
            self.agent.llm_planner = self.llm_planner

    async def create_task_plan(self, user_request: str, query_analyzer) -> Dict:
        """Create comprehensive task plan using LLM-driven planner"""
        logger.info(f"🎯 Creating LLM-driven comprehensive plan for: {user_request}")

        # Ensure LLM planner is initialized
        self.ensure_llm_planner()

        if self.llm_planner is None:
            logger.warning("LLM planner not available, using legacy planning only")
            return await self.agent.planning_module.create_task_plan(user_request)

        # Check if it's a simple query that can be handled directly
        is_simple = await query_analyzer.is_simple_query(user_request)
        if is_simple:
            logger.info("Detected simple query, handling directly without planning")
            response = await query_analyzer.handle_simple_query(user_request)
            return {
                "phases": [
                    {
                        "steps": [
                            {
                                "type": "function",
                                "function": {
                                    "name": "respond",
                                    "arguments": {"response": response},
                                },
                            }
                        ]
                    }
                ]
            }

        # Use the new LLM-driven planner for all requests
        plan = await self.llm_planner.create_comprehensive_plan(user_request)

        # Also create legacy plan for compatibility
        legacy_plan = await self.agent.planning_module.create_task_plan(user_request)

        # Merge the plans (LLM plan takes priority)
        if plan:
            plan["legacy_phases"] = legacy_plan.get("phases", [])
            return plan
        else:
            return legacy_plan

    async def get_current_report_guidance(self) -> str:
        """Get guidance on what needs to be completed in the current report"""
        try:
            if not hasattr(self.agent, "action_executor"):
                return "No active action executor"

            status = self.agent.action_executor.get_current_report_status()

            if "error" in status:
                return f"Report status error: {status['error']}"

            completion_pct = status.get("completion_percentage", 0)
            completed_sections = status.get("completed_sections", 0)
            total_sections = status.get("total_sections", 0)
            missing_sections = status.get("missing_sections", [])
            placeholder_sections = status.get("placeholder_sections", [])

            guidance = f"Current report is {completion_pct:.1f}% complete ({completed_sections}/{total_sections} sections).\n"

            if placeholder_sections:
                guidance += f"Priority: Replace placeholders in {', '.join(placeholder_sections[:3])}\n"

            if missing_sections:
                guidance += f"Still needed: {', '.join(missing_sections[:3])}\n"

            if completion_pct < 50:
                guidance += "Focus on Executive Summary and Key Findings first."

            return guidance

        except Exception as e:
            logger.error(f"Error getting report guidance: {e}")
            return "Could not get report guidance"
