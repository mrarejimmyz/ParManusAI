"""
Backward Compatibility Wrapper for LLM-Driven Planning
This file maintains compatibility with existing code while using the new modular system
"""

from app.planning import LLMDrivenPlanner as BasePlanner


# Maintain backward compatibility
class LLMDrivenPlanner(BasePlanner):
    """
    Backward compatibility wrapper for the old interface
    """

    def __init__(self, llm=None):
        super().__init__(llm)
        self.todo_file_path = self.todo_manager.get_todo_file_path()
