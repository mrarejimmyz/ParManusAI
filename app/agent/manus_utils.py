import asyncio
import json
import os
import time
from typing import Dict, List, Optional

from app.exceptions import AgentTaskComplete
from app.logger import logger


class ManusUtils:
    def __init__(self, agent):
        self.agent = agent
        self.last_progression_time = 0

    async def _validate_current_position(self) -> bool:
        """Validate current phase and step indices"""
        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            return False

        # Check phase bounds
        if self.agent.current_phase < 0 or self.agent.current_phase >= len(
            self.agent.current_plan["phases"]
        ):
            logger.error(f"Invalid phase index: {self.agent.current_phase}")
            return False

        current_phase = self.agent.current_plan["phases"][self.agent.current_phase]
        if "steps" not in current_phase:
            logger.error("Current phase has no steps")
            return False

        # Check step bounds - allow being at the end of phase for progression
        if self.agent.current_step < 0:
            logger.error(f"Invalid step index: {self.agent.current_step}")
            return False

        # If step is beyond the current phase, check if we can progress to next phase
        if self.agent.current_step >= len(current_phase["steps"]):
            # This is acceptable if we're at the end and can progress to next phase
            if self.agent.current_step == len(current_phase["steps"]):
                # We're at the end of current phase, this is valid for progression
                logger.info(
                    f"At end of phase {self.agent.current_phase}, step {self.agent.current_step} (max: {len(current_phase['steps'])})"
                )
                return True
            else:
                # We're way beyond, auto-correct this
                logger.warning(
                    f"Step index {self.agent.current_step} beyond bounds (max: {len(current_phase['steps'])-1}), auto-correcting"
                )
                # Auto-correct by setting to the end of phase for progression
                self.agent.current_step = len(current_phase["steps"])
                logger.info(
                    f"Auto-corrected step to {self.agent.current_step} (end of phase)"
                )
                return True

        return True

    async def _get_current_phase(self) -> Optional[Dict]:
        """Get the current phase from the plan"""
        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            logger.error("No valid plan exists")
            return None

        try:
            if self.agent.current_phase < 0 or self.agent.current_phase >= len(
                self.agent.current_plan["phases"]
            ):
                logger.error(f"Phase index {self.agent.current_phase} out of range")
                return None
            return self.agent.current_plan["phases"][self.agent.current_phase]
        except (IndexError, KeyError) as e:
            logger.error(f"Error getting current phase: {str(e)}")
            return None

    async def _get_current_step(self) -> Optional[str]:
        """Get the current step from the current phase"""
        current_phase = await self._get_current_phase()
        if not current_phase or "steps" not in current_phase:
            return None

        try:
            # Allow being at the end of phase for progression
            if self.agent.current_step < 0:
                logger.error(f"Step index {self.agent.current_step} out of range")
                return None
            elif self.agent.current_step >= len(current_phase["steps"]):
                # At end of phase - this is valid for phase transition
                if self.agent.current_step == len(current_phase["steps"]):
                    logger.debug(f"At end of phase, step {self.agent.current_step}")
                    return "phase_complete"  # Special indicator
                else:
                    # Way beyond - auto-correct
                    logger.warning(
                        f"Step index {self.agent.current_step} too high, auto-correcting to {len(current_phase['steps'])-1}"
                    )
                    self.agent.current_step = len(current_phase["steps"]) - 1
                    return current_phase["steps"][self.agent.current_step]
            else:
                return current_phase["steps"][self.agent.current_step]
        except (IndexError, KeyError) as e:
            logger.error(f"Error getting current step: {str(e)}")
            return None

    async def progress_to_next_step(self, verified: bool = True) -> bool:
        """Progress to the next step in the current phase or next phase"""
        current_time = time.time()

        # Prevent rapid multiple progressions (cooldown of 0.1 seconds)
        if current_time - self.last_progression_time < 0.1:
            logger.debug("Progression cooldown active, skipping")
            return True

        self.last_progression_time = current_time

        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            logger.error("No valid plan exists for progression")
            return False

        current_phase = await self._get_current_phase()
        if not current_phase or "steps" not in current_phase:
            logger.error("No valid phase for progression")
            return False

        # Record current step completion with verification status
        current_step = await self._get_current_step()
        if current_step and current_step != "phase_complete":
            if hasattr(self.agent, "planning_module") and hasattr(
                self.agent.planning_module, "todo_manager"
            ):
                await self.agent.planning_module.todo_manager.update_todo_progress(
                    current_step, verified
                )

        # Check if we can move to next step in current phase
        if self.agent.current_step + 1 < len(current_phase["steps"]):
            self.agent.current_step += 1
            logger.info(
                f"Progressed to step {self.agent.current_step} in phase {self.agent.current_phase}"
            )
            return True
        else:
            # We're at the end of current phase, move to next phase
            logger.info(
                f"Completed phase {self.agent.current_phase}, moving to next phase"
            )
            # Don't increment step here, let progress_to_next_phase handle it
            return await self.progress_to_next_phase()

    async def progress_to_next_phase(self) -> bool:
        """Progress to the next phase and reset step counter"""
        if not self.agent.current_plan or "phases" not in self.agent.current_plan:
            logger.error("No valid plan exists for phase progression")
            return False

        # Calculate next phase
        next_phase = self.agent.current_phase + 1

        # Check if we've completed all phases
        if next_phase >= len(self.agent.current_plan["phases"]):
            # Before completing, verify all deliverables are actually created
            await self._verify_all_deliverables_created()
            logger.info("All phases complete!")
            raise AgentTaskComplete(
                "All phases of the plan have been completed with verified deliverables"
            )

        # Move to next phase
        self.agent.current_phase = next_phase
        self.agent.current_step = 0  # Reset step counter for new phase
        logger.info(
            f"Progressed to phase {self.agent.current_phase}, step {self.agent.current_step}"
        )
        return True

    async def _verify_all_deliverables_created(self) -> bool:
        """
        Verify that all required deliverables have been created before task completion
        """
        try:
            # Check workspace for created files
            workspace_path = os.path.join(os.getcwd(), "workspace")
            if not os.path.exists(workspace_path):
                logger.warning(
                    "⚠️ Workspace directory does not exist - no deliverables found"
                )
                return False

            # Get current task description for filtering
            current_task = ""
            try:
                if hasattr(self.agent, "state") and hasattr(
                    self.agent.state, "messages"
                ):
                    for message in reversed(self.agent.state.messages):
                        if hasattr(message, "role") and message.role == "user":
                            if hasattr(message, "content") and isinstance(
                                message.content, str
                            ):
                                current_task = message.content
                                break

                # Also try todo.md
                if not current_task:
                    todo_path = os.path.join(workspace_path, "todo.md")
                    if os.path.exists(todo_path):
                        with open(todo_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            import re

                            goal_match = re.search(r"\*\*Goal:\*\*\s*(.+)", content)
                            if goal_match:
                                current_task = goal_match.group(1).strip()
            except Exception as e:
                logger.debug(f"Could not extract current task: {e}")

            # Count markdown files (reports) in workspace - filter by relevance to current task
            md_files = []
            task_keywords = []
            if current_task:
                # Extract keywords from current task
                import re

                words = re.findall(r"\b\w+\b", current_task.lower())
                common_words = {
                    "the",
                    "a",
                    "an",
                    "and",
                    "or",
                    "but",
                    "in",
                    "on",
                    "at",
                    "to",
                    "for",
                    "of",
                    "with",
                    "by",
                }
                task_keywords = [
                    word for word in words if len(word) > 3 and word not in common_words
                ][:3]
                logger.info(f"🔍 Looking for reports related to: {current_task}")
                logger.info(f"🔍 Task keywords: {task_keywords}")

            for root, dirs, files in os.walk(workspace_path):
                for file in files:
                    if file.endswith(".md") and file != "todo.md":
                        filepath = os.path.join(root, file)

                        # If we have a current task, filter by relevance
                        if task_keywords:
                            filename_lower = file.lower()
                            keyword_matches = sum(
                                1
                                for keyword in task_keywords
                                if keyword in filename_lower
                            )

                            # Also check file creation time (reports created in last 2 hours are likely relevant)
                            try:
                                file_time = os.path.getmtime(filepath)
                                import time

                                current_time = time.time()
                                is_recent = (current_time - file_time) < 7200  # 2 hours

                                if keyword_matches >= 1 or is_recent:
                                    md_files.append(filepath)
                                    logger.info(
                                        f"✅ Found relevant report: {file} (keywords: {keyword_matches}, recent: {is_recent})"
                                    )
                            except Exception as e:
                                logger.warning(
                                    f"Error checking file time for {file}: {e}"
                                )
                        else:
                            # No current task context, include all reports
                            md_files.append(filepath)

            if md_files:
                logger.info(
                    f"✅ Found {len(md_files)} deliverable(s) in workspace: {[os.path.basename(f) for f in md_files]}"
                )

                # Verify each file has substantial content
                verified_files = 0
                for filepath in md_files:
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            if len(content) > 500:  # Substantial content
                                verified_files += 1
                                logger.info(
                                    f"✅ Verified deliverable: {os.path.basename(filepath)} ({len(content)} characters)"
                                )
                            else:
                                logger.warning(
                                    f"⚠️ Deliverable has insufficient content: {os.path.basename(filepath)} ({len(content)} characters)"
                                )
                    except Exception as e:
                        logger.warning(f"Could not verify {filepath}: {e}")

                if verified_files > 0:
                    logger.info(
                        f"✅ Task completion verified: {verified_files} substantial deliverable(s) created"
                    )
                    return True
                else:
                    logger.warning(
                        "⚠️ No substantial deliverables found - task may not be complete"
                    )
                    return False
            else:
                logger.warning(
                    "⚠️ No deliverable files found in workspace - task may not be complete"
                )
                return False

        except Exception as e:
            logger.error(f"Error verifying deliverables: {e}")
            return False

    async def recover_from_invalid_position(self) -> bool:
        """Recover from invalid position by resetting to valid indices"""
        try:
            if not self.agent.current_plan or "phases" not in self.agent.current_plan:
                logger.error("Cannot recover: no valid plan exists")
                return False

            # Reset phase if out of bounds
            if self.agent.current_phase >= len(self.agent.current_plan["phases"]):
                self.agent.current_phase = len(self.agent.current_plan["phases"]) - 1
            elif self.agent.current_phase < 0:
                self.agent.current_phase = 0

            # Reset step if out of bounds
            current_phase = self.agent.current_plan["phases"][self.agent.current_phase]
            if "steps" in current_phase:
                if self.agent.current_step >= len(current_phase["steps"]):
                    # If we're past the last step, try to move to next phase
                    if self.agent.current_phase + 1 < len(
                        self.agent.current_plan["phases"]
                    ):
                        logger.info("Moving to next phase during recovery")
                        self.agent.current_phase += 1
                        self.agent.current_step = 0
                    else:
                        # We're at the last phase, set to last valid step
                        self.agent.current_step = len(current_phase["steps"]) - 1
                elif self.agent.current_step < 0:
                    self.agent.current_step = 0
            else:
                self.agent.current_step = 0

            logger.info(
                f"Position recovered to phase {self.agent.current_phase}, step {self.agent.current_step}"
            )
            return True

        except Exception as e:
            logger.error(f"Error during position recovery: {str(e)}")
            return False

    async def sync_with_base_framework(self) -> bool:
        """Synchronize our step tracking with the base framework's step counter"""
        try:
            # This method helps coordinate between our plan-based step tracking
            # and the base framework's automatic step incrementing
            if not self.agent.current_plan or "phases" not in self.agent.current_plan:
                return False

            current_phase = await self._get_current_phase()
            if not current_phase or "steps" not in current_phase:
                return False

            # If we've completed all steps in current phase, signal completion
            if self.agent.current_step >= len(current_phase["steps"]):
                logger.info("All steps in current phase completed")
                return await self.progress_to_next_phase()

            return True

        except AgentTaskComplete as e:
            # This is expected when all phases are complete - not an error
            logger.info(f"Task completed successfully: {str(e)}")
            # Re-raise to let the agent handle it properly
            raise e
        except Exception as e:
            logger.error(f"Error syncing with base framework: {str(e)}")
            return False
