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

        # Check if this is a todo-related request and we have an active todo
        if hasattr(
            self.agent, "todo_manager"
        ) and self.agent.todo_manager.check_for_todo_request(user_request):

            # Check if we have an active todo with current/pending phases
            import os

            todo_path = self.agent.todo_manager.todo_file_path
            if os.path.exists(todo_path):
                with open(todo_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "[CURRENT]" in content and "[PENDING]" in content:
                    logger.info(
                        "📋 Working with existing active todo - skipping new plan creation"
                    )
                    # Return a minimal plan that doesn't overwrite the todo
                    goal = await self.agent.todo_manager.read_todo_goal()
                    return {
                        "goal": goal or "Work on existing todo",
                        "phases": [
                            {
                                "id": 1,
                                "title": "Continue current todo phase",
                                "description": "Work on the current phase in the existing todo",
                                "steps": ["Continue with current todo phase"],
                            }
                        ],
                        "existing_todo": True,  # Flag to indicate we're working with existing todo
                    }

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
        try:  # Note: action_executor was removed during refactoring
            # Report guidance is now handled by other components
            return "Report guidance available through other systems"

        except Exception as e:
            logger.error(f"Error getting report guidance: {e}")
            return "Could not get report guidance"
