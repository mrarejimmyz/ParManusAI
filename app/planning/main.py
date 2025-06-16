"""
Main LLM-Driven Planning Interface
Coordinates plan analysis, generation, and todo management
"""

from typing import Dict

from app.logger import logger

from .analyzer import PlanAnalyzer
from .generator import PlanGenerator
from .todo_manager import TodoManager


class LLMDrivenPlanner:
    """
    Main interface for LLM-driven planning system
    """

    def __init__(self, llm=None):
        self.analyzer = PlanAnalyzer(llm)
        self.generator = PlanGenerator()
        self.todo_manager = TodoManager()

    async def create_comprehensive_plan(self, user_request: str) -> Dict:
        """
        Create a comprehensive plan for any user request
        """
        # Analyze request with LLM
        plan = await self.analyzer.analyze_request(user_request)

        # Enhance and validate the plan
        enhanced_plan = self.generator.enhance_plan(plan)

        if not self.generator.validate_plan(enhanced_plan):
            logger.warning("Plan validation failed, using fallback")
            enhanced_plan = self.analyzer._create_fallback_plan(user_request)
            enhanced_plan = self.generator.enhance_plan(enhanced_plan)

        # Create todo list
        await self.todo_manager.create_todo_from_plan(enhanced_plan)

        return enhanced_plan

    async def update_todo_progress(self, completed_step: str) -> None:
        """Update todo progress"""
        await self.todo_manager.update_todo_progress(completed_step)

    async def get_current_plan_status(self) -> Dict:
        """Get current plan status"""
        return await self.todo_manager.get_current_plan_status()


# Backward compatibility wrapper
class LLMDrivenPlannerCompat(LLMDrivenPlanner):
    """
    Backward compatibility wrapper for existing code
    """

    def __init__(self, llm=None):
        super().__init__(llm)
        self.todo_file_path = self.todo_manager.get_todo_file_path()
