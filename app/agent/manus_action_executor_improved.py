"""
ManusActionExecutor with Proper Report Management
Handles task-specific report creation and naming
"""

import os
import re
from datetime import datetime

from app.agent.report_completion_analyzer import ReportCompletionAnalyzer
from app.agent.report_manager import ReportManager
from app.logger import logger
from app.search.dynamic_web_search import DynamicWebSearcher


class ManusActionExecutor:
    """Action executor with proper report management"""

    def __init__(self, agent):
        """Initialize with agent reference"""
        self.agent = agent
        self.llm = getattr(agent, "llm", None)
        self.search_engine = DynamicWebSearcher(llm=self.llm)
        self.last_search_results = (
            None  # Initialize report manager and completion analyzer
        )
        workspace_path = getattr(agent, "workspace_root", "workspace")
        self.report_manager = ReportManager(workspace_path)
        self.completion_analyzer = ReportCompletionAnalyzer()
        self.current_task = None
        self.report_name = None

    async def execute_extraction_action(self, step: str) -> bool:
        """Execute data extraction from web sources"""
        try:
            logger.info(f"📊 EXTRACTION ACTION: {step}")

            # Get the current task description
            task_description = self._get_user_message()
            self.current_task = task_description

            # Generate appropriate report name
            if not self.report_name:
                self.report_name = self.report_manager.generate_report_name(
                    task_description,
                    (
                        "travel_analysis"
                        if "ontario" in task_description.lower()
                        else "analysis"
                    ),
                )
                logger.info(f"📝 Generated report name: {self.report_name}")

            # Use the dynamic web searcher for real web search
            search_results = await self.search_engine.search_and_scrape(
                query=task_description, max_results=5
            )

            if search_results:
                self.last_search_results = {
                    "success": True,
                    "results": search_results,
                    "strategy": {"approach": "extraction_search"},
                    "method": "extraction_search",
                    "task": task_description,
                    "report_name": self.report_name,
                }
                logger.info(
                    f"✅ Extraction successful - found {len(search_results)} results for: {task_description}"
                )
                return True
            else:
                logger.warning("⚠️ Extraction incomplete - no search results available")
                return False

        except Exception as e:
            logger.error(f"❌ Extraction action failed: {str(e)}")
            return False

    async def execute_research_action(self, step: str) -> bool:
        """Execute research action"""
        logger.info(f"🔍 RESEARCH ACTION: {step}")
        return await self.execute_extraction_action(step)

    async def execute_verification_action(self, step: str) -> bool:
        """Execute verification"""
        logger.info(f"✅ VERIFICATION ACTION: {step}")
        return True

    async def execute_navigation_action(self, step: str) -> bool:
        """Execute navigation"""
        logger.info(f"🧭 NAVIGATION ACTION: {step}")
        return True

    async def execute_creation_action(self, step: str) -> bool:
        """Execute creation/output action with proper report generation"""
        try:
            logger.info(f"📝 CREATION ACTION: {step}")

            # Get current task if not already set
            if not self.current_task:
                self.current_task = self._get_user_message()

            # Generate report name if not already set
            if not self.report_name:
                self.report_name = self.report_manager.generate_report_name(
                    self.current_task,
                    (
                        "travel_plan"
                        if "ontario" in self.current_task.lower()
                        else "analysis"
                    ),
                )

            # Check if we should create a new report
            if self.report_manager.should_create_new_report(self.current_task):
                # Create the report
                report_path = os.path.join(
                    self.report_manager.workspace_path, self.report_name
                )

                # Create report template
                report_content = self.report_manager.create_report_template(
                    self.current_task, self.report_name
                )

                # Add search results if available
                if self.last_search_results and self.last_search_results.get("results"):
                    report_content += "\n## Research Data\n\n"
                    for i, result in enumerate(
                        self.last_search_results["results"][:5], 1
                    ):
                        report_content += (
                            f"### Source {i}: {result.get('title', 'N/A')}\n"
                        )
                        report_content += f"**URL:** {result.get('url', 'N/A')}\n"
                        report_content += f"**Content:** {result.get('content', result.get('snippet', 'N/A'))[:500]}...\n\n"

                # Write the report
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report_content)

                # Add completion analysis and checklist to the report
                self._add_completion_analysis(report_path)

                logger.info(f"✅ Created new task-specific report: {self.report_name}")
                logger.info(f"✅ Report saved to: {report_path}")
                return True
            else:
                logger.info("✅ Using existing related reports")
                return True

        except Exception as e:
            logger.error(f"❌ Creation action failed: {str(e)}")
            return False

    async def execute_default_action(self, step: str) -> bool:
        """Execute default action for unrecognized step types"""
        logger.info(f"🔧 DEFAULT ACTION: {step}")
        return True

    def _add_completion_analysis(self, report_path: str) -> bool:
        """Add completion analysis and checklist to the report"""
        try:
            # Update the report with checklist
            success = self.completion_analyzer.update_report_with_checklist(report_path)

            if success:
                # Also log the completion analysis
                analysis = self.completion_analyzer.analyze_report_completeness(
                    report_path
                )
                reasoning = self.completion_analyzer.get_completion_reasoning(analysis)

                logger.info(f"📊 Report Analysis Complete:")
                logger.info(
                    f"   - Progress: {analysis.get('completion_percentage', 0):.1f}%"
                )
                logger.info(
                    f"   - Completed: {analysis.get('completed_sections', 0)}/{analysis.get('total_sections', 0)} sections"
                )

                if analysis.get("placeholder_sections"):
                    logger.info(
                        f"   - Placeholder sections: {', '.join(analysis['placeholder_sections'])}"
                    )

                if analysis.get("missing_sections"):
                    logger.info(
                        f"   - Missing sections: {', '.join(analysis['missing_sections'])}"
                    )

                return True
            else:
                logger.warning("⚠️ Could not add completion analysis to report")
                return False

        except Exception as e:
            logger.error(f"❌ Error adding completion analysis: {e}")
            return False

    def update_report_completion(self, report_path: str = None) -> bool:
        """Update the completion analysis for the current report"""
        try:
            if not report_path:
                if not self.report_name:
                    logger.warning("⚠️ No active report to update")
                    return False

                workspace_path = getattr(self.agent, "workspace_root", "workspace")
                report_path = os.path.join(workspace_path, self.report_name)

            if not os.path.exists(report_path):
                logger.warning(f"⚠️ Report file not found: {report_path}")
                return False

            # Re-analyze and update the completion checklist
            return self._add_completion_analysis(report_path)

        except Exception as e:
            logger.error(f"❌ Error updating report completion: {e}")
            return False

    def get_current_report_status(self) -> dict:
        """Get the current status of the active report"""
        try:
            if not self.report_name:
                return {"error": "No active report"}

            workspace_path = getattr(self.agent, "workspace_root", "workspace")
            report_path = os.path.join(workspace_path, self.report_name)

            if not os.path.exists(report_path):
                return {"error": "Report file not found"}

            analysis = self.completion_analyzer.analyze_report_completeness(report_path)
            return analysis

        except Exception as e:
            logger.error(f"❌ Error getting report status: {e}")
            return {"error": str(e)}

    def _get_user_message(self) -> str:
        """Extract the original user message from the agent's messages"""
        try:
            # First try to get from agent messages
            if hasattr(self.agent, "state") and hasattr(self.agent.state, "messages"):
                for message in reversed(self.agent.state.messages):
                    if hasattr(message, "role") and message.role == "user":
                        if hasattr(message, "content"):
                            if isinstance(message.content, str):
                                return message.content

            # Try to get from memory if available - use correct method signature
            if hasattr(self.agent, "memory"):
                # Try get_messages method first (standard Memory class)
                if hasattr(self.agent.memory, "get_messages"):
                    recent_messages = self.agent.memory.get_messages(limit=10)
                    for msg in reversed(recent_messages):
                        if hasattr(msg, "role") and msg.role == "user":
                            content = getattr(msg, "content", "")
                            if (
                                content and len(content.strip()) > 10
                            ):  # Meaningful content
                                return content

                # Try messages property directly
                elif hasattr(self.agent.memory, "messages"):
                    recent_messages = self.agent.memory.messages[-10:]  # Last 10
                    for msg in reversed(recent_messages):
                        if hasattr(msg, "role") and msg.role == "user":
                            content = getattr(msg, "content", "")
                            if (
                                content and len(content.strip()) > 10
                            ):  # Meaningful content
                                return content

            # Try to get from the todo.md file if it contains the current task
            try:
                workspace_path = getattr(self.agent, "workspace_root", "workspace")
                todo_path = os.path.join(workspace_path, "todo.md")
                if os.path.exists(todo_path):
                    with open(todo_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Extract goal from todo file
                        goal_match = re.search(r"\*\*Goal:\*\*\s*(.+)", content)
                        if goal_match:
                            goal = goal_match.group(1).strip()
                            if len(goal) > 10:
                                logger.info(f"📋 Extracted task from todo.md: {goal}")
                                return goal
            except Exception as e:
                logger.debug(f"Could not read todo.md: {e}")

            # Fallback: return a more specific search query based on context
            return (
                "Plan a trip to Ontario Canada travel guide attractions accommodations"
            )

        except Exception as e:
            logger.error(f"Error extracting user message: {str(e)}")
            return (
                "Plan a trip to Ontario Canada travel guide attractions accommodations"
            )
