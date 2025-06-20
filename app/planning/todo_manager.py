"""
Todo Manager
Handles creation and management of todo.md files
"""

import os
import re
from typing import Dict

from app.config import config
from app.logger import logger


class TodoManager:
    """
    Manages todo file creation, updates, and progress tracking
    """

    def __init__(self):
        self.todo_file_path = os.path.join(config.workspace_root, "todo.md")

    async def create_todo_from_plan(self, plan: Dict) -> None:
        """
        Create a detailed todo.md file from the LLM-generated plan or update existing one
        """
        # Check if todo already exists and if it's the same goal
        if await self._should_update_existing_todo(plan):
            await self._update_existing_todo(plan)
            return

        # Create new todo
        await self._create_new_todo(plan)

    async def update_todo_progress(
        self, completed_step: str, verified: bool = True
    ) -> None:
        """
        Update the todo list with completed steps, only if verified
        """
        try:
            if not os.path.exists(self.todo_file_path):
                return

            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if verified:
                # Mark step as completed only if verified
                updated_content = content.replace(
                    f"[ ] {completed_step}", f"[x] {completed_step}"
                )
                logger.info(f"✅ Marked step as complete: {completed_step}")
            else:
                # Mark step as attempted but not verified
                updated_content = content.replace(
                    f"[ ] {completed_step}",
                    f"[?] {completed_step} (attempted - verification needed)",
                )
                logger.warning(
                    f"⚠️ Marked step as attempted but unverified: {completed_step}"
                )

            with open(self.todo_file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

        except Exception as e:
            logger.warning(f"Failed to update todo progress: {e}")

    async def mark_deliverable_created(
        self, deliverable_name: str, filepath: str
    ) -> None:
        """
        Add a record of created deliverables to the todo file
        """
        try:
            if not os.path.exists(self.todo_file_path):
                return

            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Add deliverable record
            deliverable_section = f"\n### 📄 Deliverables Created\n- ✅ {deliverable_name}: `{filepath}`\n"

            # Insert before progress tracking section if it exists
            if "## 📈 Progress Tracking" in content:
                updated_content = content.replace(
                    "## 📈 Progress Tracking",
                    deliverable_section + "\n## 📈 Progress Tracking",
                )
            else:
                # Append to end
                updated_content = content + deliverable_section

            with open(self.todo_file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"📄 Recorded deliverable: {deliverable_name} -> {filepath}")

        except Exception as e:
            logger.warning(f"Failed to record deliverable: {e}")

    async def get_current_plan_status(self) -> Dict:
        """
        Get the current status of the plan from the todo file
        """
        try:
            if not os.path.exists(self.todo_file_path):
                return {"status": "no_plan", "message": "No todo file found"}

            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Count completed vs total steps
            total_checkboxes = content.count("[ ]") + content.count("[x]")
            completed_checkboxes = content.count("[x]")

            if total_checkboxes == 0:
                progress = 0
            else:
                progress = (completed_checkboxes / total_checkboxes) * 100

            return {
                "status": "active",
                "progress": round(progress, 1),
                "completed_steps": completed_checkboxes,
                "total_steps": total_checkboxes,
                "message": f"Progress: {completed_checkboxes}/{total_checkboxes} steps completed ({progress:.1f}%)",
            }

        except Exception as e:
            logger.warning(f"Failed to get plan status: {e}")
            return {"status": "error", "message": str(e)}

    def get_todo_file_path(self) -> str:
        """Get the path to the todo file"""
        return self.todo_file_path

    async def _should_update_existing_todo(self, plan: Dict) -> bool:
        """
        Check if we should update an existing todo instead of creating a new one
        """
        if not os.path.exists(self.todo_file_path):
            return False

        try:
            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract existing goal
            goal_match = re.search(r"\*\*Goal:\*\*\s*(.+)", content)
            if not goal_match:
                # Check simpler format
                goal_match = re.search(r"\*\*Goal:\*\*\s*(.+)", content)

            if goal_match:
                existing_goal = goal_match.group(1).strip()
                new_goal = plan.get("goal", "").strip()

                # If goals are similar, update existing instead of replacing
                if existing_goal and new_goal:
                    # Simple similarity check - if they share key words or are similar
                    if (
                        existing_goal.lower() in new_goal.lower()
                        or new_goal.lower() in existing_goal.lower()
                        or len(
                            set(existing_goal.lower().split())
                            & set(new_goal.lower().split())
                        )
                        >= 2
                    ):
                        logger.info(
                            f"📝 Updating existing todo for similar goal: {existing_goal}"
                        )
                        return True

        except Exception as e:
            logger.warning(f"Error checking existing todo: {e}")

        return False

    async def _update_existing_todo(self, plan: Dict) -> None:
        """
        Update existing todo by advancing to next step/phase instead of overwriting
        """
        try:
            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find current phase and advance it
            updated_content = await self._advance_current_phase(content, plan)

            with open(self.todo_file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info("✅ Updated existing todo with next steps")

        except Exception as e:
            logger.warning(f"Error updating existing todo: {e}")
            # Fall back to creating new todo
            await self._create_new_todo(plan)

    async def _advance_current_phase(self, content: str, plan: Dict) -> str:
        """
        Advance the current phase by marking current step complete and moving to next
        """
        # Find the current phase marker [CURRENT]
        current_match = re.search(r"## Phase (\d+):[^\[]*\[CURRENT\]", content)
        if current_match:
            current_phase_num = int(current_match.group(1))

            # Mark current phase as complete and move to next
            content = re.sub(
                r"(## Phase " + str(current_phase_num) + r":[^\[]*)\[CURRENT\]",
                r"\1[COMPLETE]",
                content,
            )

            # Mark next phase as current
            next_phase_num = current_phase_num + 1
            content = re.sub(
                r"(## Phase " + str(next_phase_num) + r":[^\[]*)\[PENDING\]",
                r"\1[CURRENT]",
                content,
            )

            # Add any steps from the new plan if the phase has empty steps
            if plan.get("phases") and len(plan["phases"]) >= next_phase_num:
                next_phase = plan["phases"][next_phase_num - 1]
                steps = next_phase.get("steps", [])
                if steps:
                    # Check if the next phase has empty steps
                    phase_pattern = (
                        f"## Phase {next_phase_num}:.*?\\*\\*Steps:\\*\\*\\s*\\n\\n"
                    )
                    if re.search(phase_pattern, content, re.DOTALL):
                        steps_text = "\n".join([f"- {step}" for step in steps])
                        content = re.sub(
                            f"(## Phase {next_phase_num}:.*?\\*\\*Steps:\\*\\*\\s*)\\n\\n",
                            f"\\1\n{steps_text}\n\n",
                            content,
                            flags=re.DOTALL,
                        )

            logger.info(
                f"📈 Advanced from Phase {current_phase_num} to Phase {next_phase_num}"
            )
        else:
            # No current phase found, try to mark first incomplete step as current
            content = self._mark_next_step_current(content)

        return content

    def _mark_next_step_current(self, content: str) -> str:
        """
        Find first pending phase and mark it as current
        """
        content = re.sub(
            r"(## Phase \d+:[^\[]*)\[PENDING\]", r"\1[CURRENT]", content, count=1
        )
        return content

    async def _create_new_todo(self, plan: Dict) -> None:
        """
        Create a completely new todo (fallback method)
        """
        # This is the original logic, extracted for clarity
        logger.info("📝 Creating new detailed todo list from LLM plan")

        todo_content = f"""# 📋 Task Execution Plan

## 🎯 Goal
**{plan.get('goal', 'No goal specified')}**

## 📊 Task Details
- **Type:** {plan.get('task_type', 'general')}
- **Complexity:** {plan.get('complexity', 'unknown')}
- **Priority:** {plan.get('priority', 'medium')}
- **Estimated Duration:** {plan.get('estimated_duration', 'unknown')}
- **Created:** {plan.get('created_at', 'unknown')}

## 🏆 Final Deliverable
{plan.get('final_deliverable', 'Task completion')}

## ✅ Success Criteria
{plan.get('success_criteria', 'User satisfaction')}

---

"""

        # Add phases and steps
        phases = plan.get("phases", [])
        for i, phase in enumerate(phases):
            todo_content += f"""## Phase {phase.get('id', i+1)}: {phase.get('title', 'Unnamed Phase')}

**Description:** {phase.get('description', 'No description')}

**Estimated Time:** {phase.get('estimated_time', 'unknown')}

**Tools Needed:** {', '.join(phase.get('tools_needed', ['None']))}

**Success Criteria:** {phase.get('success_criteria', 'Complete all steps')}

### 📝 Steps:
"""

            steps = phase.get("steps", [])
            for j, step in enumerate(steps, 1):
                todo_content += f"{j}. [ ] {step}\n"

            todo_content += "\n---\n\n"

        # Add progress tracking section
        todo_content += """## 📈 Progress Tracking

### Current Status
- [ ] Planning Complete
- [ ] Execution Started
- [ ] Phase 1 Complete
- [ ] Phase 2 Complete
- [ ] All Phases Complete
- [ ] Final Review
- [ ] Task Complete

### Notes
(Add notes and observations here as the task progresses)

---

*Generated by LLM-Driven Planning System*
"""  # Write to file
        try:
            with open(self.todo_file_path, "w", encoding="utf-8") as f:
                f.write(todo_content)

            logger.info(f"📝 Todo list saved to {self.todo_file_path}")

        except Exception as e:
            logger.warning(f"Failed to save todo list: {e}")
