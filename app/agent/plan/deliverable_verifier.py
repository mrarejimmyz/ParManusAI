"""
Deliverable verification utilities for ensuring task completion quality.
"""

import os
import re
import time
from typing import List, Tuple

from app.logger import logger


class DeliverableVerifier:
    """Handles verification of deliverables and task completion."""

    def __init__(self, agent):
        self.agent = agent

    async def verify_all_deliverables_created(self) -> bool:
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
            current_task = self._extract_current_task()

            # Count markdown files (reports) in workspace - filter by relevance to current task
            md_files = self._find_relevant_reports(workspace_path, current_task)

            if md_files:
                logger.info(
                    f"✅ Found {len(md_files)} deliverable(s) in workspace: {[os.path.basename(f) for f in md_files]}"
                )

                # Verify each file has substantial content AND check completion percentage
                verified_files = 0
                incomplete_reports = []

                for filepath in md_files:
                    verification_result = self._verify_file_completion(filepath)
                    if verification_result["is_complete"]:
                        verified_files += 1
                    else:
                        incomplete_reports.append(
                            (filepath, verification_result["completion_pct"])
                        )

                # If there are incomplete reports, don't complete the task yet
                if incomplete_reports:
                    logger.warning(
                        f"⚠️ Found {len(incomplete_reports)} incomplete report(s):"
                    )
                    for filepath, completion_pct in incomplete_reports:
                        logger.warning(
                            f"   - {os.path.basename(filepath)}: {completion_pct:.1f}% complete"
                        )

                    # Add tasks to complete the reports
                    await self._add_completion_tasks_for_incomplete_reports(
                        incomplete_reports
                    )
                    return False  # Don't complete task yet

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

    def _extract_current_task(self) -> str:
        """Extract the current task description from agent state or files."""
        current_task = ""
        try:
            if hasattr(self.agent, "state") and hasattr(self.agent.state, "messages"):
                for message in reversed(self.agent.state.messages):
                    if hasattr(message, "role") and message.role == "user":
                        if hasattr(message, "content") and isinstance(
                            message.content, str
                        ):
                            current_task = message.content
                            break

            # Also try todo.md
            if not current_task:
                workspace_path = os.path.join(os.getcwd(), "workspace")
                todo_path = os.path.join(workspace_path, "todo.md")
                if os.path.exists(todo_path):
                    with open(todo_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        goal_match = re.search(r"\*\*Goal:\*\*\s*(.+)", content)
                        if goal_match:
                            current_task = goal_match.group(1).strip()
        except Exception as e:
            logger.debug(f"Could not extract current task: {e}")

        return current_task

    def _find_relevant_reports(
        self, workspace_path: str, current_task: str
    ) -> List[str]:
        """Find markdown reports relevant to the current task."""
        md_files = []
        task_keywords = []

        if current_task:
            # Extract keywords from current task
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
                            1 for keyword in task_keywords if keyword in filename_lower
                        )

                        # Also check file creation time (reports created in last 2 hours are likely relevant)
                        try:
                            file_time = os.path.getmtime(filepath)
                            current_time = time.time()
                            is_recent = (current_time - file_time) < 7200  # 2 hours

                            if keyword_matches >= 1 or is_recent:
                                md_files.append(filepath)
                                logger.info(
                                    f"✅ Found relevant report: {file} (keywords: {keyword_matches}, recent: {is_recent})"
                                )
                        except Exception as e:
                            logger.warning(f"Error checking file time for {file}: {e}")
                    else:
                        # No current task context, include all reports
                        md_files.append(filepath)

        return md_files

    def _verify_file_completion(self, filepath: str) -> dict:
        """Verify the completion status of a single file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

                if len(content) > 500:  # Substantial content
                    # Check report completion percentage if we have report analyzer
                    completion_pct = 0
                    try:
                        if hasattr(self.agent, "action_executor") and hasattr(
                            self.agent.action_executor, "completion_analyzer"
                        ):
                            analysis = self.agent.action_executor.completion_analyzer.analyze_report_completeness(
                                filepath
                            )
                            completion_pct = analysis.get("completion_percentage", 0)

                            if completion_pct >= 90:  # Report is substantially complete
                                logger.info(
                                    f"✅ Verified complete deliverable: {os.path.basename(filepath)} ({completion_pct:.1f}% complete, {len(content)} characters)"
                                )
                                return {
                                    "is_complete": True,
                                    "completion_pct": completion_pct,
                                }
                            else:
                                logger.warning(
                                    f"⚠️ Deliverable incomplete: {os.path.basename(filepath)} ({completion_pct:.1f}% complete)"
                                )
                                return {
                                    "is_complete": False,
                                    "completion_pct": completion_pct,
                                }
                        else:
                            # Fallback to basic content check if no analyzer
                            logger.info(
                                f"✅ Verified deliverable: {os.path.basename(filepath)} ({len(content)} characters)"
                            )
                            return {"is_complete": True, "completion_pct": 100}
                    except Exception as analyzer_error:
                        logger.warning(
                            f"Could not analyze completion for {filepath}: {analyzer_error}"
                        )
                        # Fallback to basic verification
                        logger.info(
                            f"✅ Verified deliverable (basic check): {os.path.basename(filepath)} ({len(content)} characters)"
                        )
                        return {"is_complete": True, "completion_pct": 100}
                else:
                    logger.warning(
                        f"⚠️ Deliverable has insufficient content: {os.path.basename(filepath)} ({len(content)} characters)"
                    )
                    return {"is_complete": False, "completion_pct": 0}
        except Exception as e:
            logger.warning(f"Could not verify {filepath}: {e}")
            return {"is_complete": False, "completion_pct": 0}

    async def _add_completion_tasks_for_incomplete_reports(
        self, incomplete_reports: List[Tuple[str, float]]
    ):
        """Add tasks to complete incomplete reports"""
        try:
            logger.info("🔧 Adding tasks to complete incomplete reports...")

            for filepath, completion_pct in incomplete_reports:
                filename = os.path.basename(filepath)

                # Get specific missing sections from the analyzer
                try:
                    if hasattr(self.agent, "action_executor") and hasattr(
                        self.agent.action_executor, "completion_analyzer"
                    ):
                        analysis = self.agent.action_executor.completion_analyzer.analyze_report_completeness(
                            filepath
                        )
                        missing_sections = analysis.get("missing_sections", [])
                        placeholder_sections = analysis.get("placeholder_sections", [])

                        # Add a phase to complete this report
                        completion_phase = {
                            "name": f"Complete {filename}",
                            "description": f"Improve {filename} from {completion_pct:.1f}% to 100% completion",
                            "steps": [],
                        }

                        # Add specific steps for missing sections
                        for section in missing_sections:
                            completion_phase["steps"].append(
                                f"Add missing section: {section}"
                            )

                        # Add specific steps for placeholder sections
                        for section in placeholder_sections:
                            completion_phase["steps"].append(
                                f"Complete placeholder content in: {section}"
                            )

                        # Add a final review step
                        completion_phase["steps"].append(
                            f"Review and finalize {filename} to ensure 100% completion"
                        )

                        # Append this phase to the end of the plan
                        if "phases" not in self.agent.current_plan:
                            self.agent.current_plan["phases"] = []

                        self.agent.current_plan["phases"].append(completion_phase)
                        logger.info(
                            f"✅ Added completion phase for {filename} with {len(completion_phase['steps'])} steps"
                        )

                except Exception as e:
                    logger.warning(
                        f"Could not analyze {filepath} for completion tasks: {e}"
                    )

        except Exception as e:
            logger.error(f"Error adding completion tasks: {e}")
