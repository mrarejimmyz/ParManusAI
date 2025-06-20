"""
Todo Management Module for Manus Agent
Handles todo.md file operations and goal extraction.
"""

import os
import re
from typing import Dict, Optional

from app.config import config
from app.logger import logger


class TodoManager:
    """Manages todo.md file operations and goal extraction."""

    def __init__(self, agent=None):
        self.agent = agent
        self.todo_file_path = os.path.join(config.workspace_root, "todo.md")

    async def read_todo_goal(self) -> Optional[str]:
        """Read the goal from todo.md file."""
        try:
            if os.path.exists(self.todo_file_path):
                with open(self.todo_file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract goal from todo.md
                goal_match = re.search(r"\*\*Goal:\*\*\s*(.+)", content)
                if goal_match:
                    goal = goal_match.group(1).strip()
                    logger.info(f"📋 Found goal in todo.md: {goal}")
                    return goal
        except Exception as e:
            logger.error(f"Error reading todo.md: {e}")

        return None

    async def auto_plan_from_todo(self) -> bool:
        """Automatically create a plan from todo.md goal and fill in empty steps."""
        goal = await self.read_todo_goal()
        if not goal:
            return False

        try:
            # Check if todo.md has empty steps sections
            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if todo has current phase markers (indicating it's an active todo)
            has_current_phase = "[CURRENT]" in content
            has_pending_phases = "[PENDING]" in content

            if has_current_phase and has_pending_phases:
                logger.info(
                    "📋 Found active todo with current phase - working with existing structure"
                )
                # For active todos, don't overwrite - just use the existing structure
                return True

            empty_steps = re.findall(r"\*\*Steps:\*\*\s*$", content, re.MULTILINE)

            if len(empty_steps) > 0:
                logger.info(
                    "🤖 Auto-generating action plan for empty steps sections..."
                )

                # Create a comprehensive plan
                if (
                    self.agent
                    and hasattr(self.agent, "llm_planner")
                    and self.agent.llm_planner
                ):
                    plan = await self.agent.llm_planner.create_comprehensive_plan(goal)
                    if self.agent:
                        self.agent.current_plan = plan

                    # Update todo.md with generated steps
                    await self.update_todo_with_steps(plan)
                    return True

        except Exception as e:
            logger.error(f"Error auto-planning from todo: {e}")

        return False

    async def update_todo_with_steps(self, plan: Dict):
        """Update todo.md file with generated steps from the plan."""
        try:
            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Generate steps for each phase
            for i, phase in enumerate(plan.get("phases", [])):
                phase_num = i + 1
                steps_text = "\n".join([f"- {step}" for step in phase.get("steps", [])])

                # Replace empty steps section for this phase
                pattern = f"(## Phase {phase_num}:.*?\\*\\*Steps:\\*\\*\\s*)"
                replacement = f"\\g<1>\n{steps_text}"
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)

            # Write updated content back
            with open(self.todo_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info("✅ Updated todo.md with generated action steps")

        except Exception as e:
            logger.error(f"Error updating todo.md: {e}")

    def check_for_todo_request(self, request: str) -> bool:
        """Check if the request is related to todo.md."""
        return "todo.md" in request.lower() or "work on the todo" in request.lower()

    async def create_todo_list(self, plan: Dict) -> str:
        """Create a todo list from a plan."""
        if self.agent and hasattr(self.agent, "planning_module"):
            return await self.agent.planning_module.create_todo_list(plan)
        return ""

    async def update_todo_progress(self):
        """Update todo progress."""
        if self.agent and hasattr(self.agent, "planning_module"):
            return await self.agent.planning_module.update_todo_progress()
        return None
