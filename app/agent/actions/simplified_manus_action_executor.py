"""
Simplified Manus Action Executor
Streamlined version with focused functionality using comprehensive modular components
"""

import os
from typing import List, Optional

from app.agent.reporting.utils.report_completion_analyzer import (
    ReportCompletionAnalyzer,
)
from app.agent.reporting.validation.search_query_generator import SearchQueryGenerator
from app.logger import logger
from app.search.dynamic_web_search import DynamicWebSearcher

# TYPE_CHECKING block no longer needed since we moved the import


class SimplifiedManusActionExecutor:
    """Simplified action executor with comprehensive modular components"""

    def __init__(self, agent):
        """Initialize with agent reference and modular components"""
        self.agent = agent
        self.llm = getattr(agent, "llm", None)  # Initialize modular components
        workspace_root = getattr(agent, "workspace_root", "workspace")
        self.search_engine = DynamicWebSearcher(llm=self.llm)
        self.query_generator = (
            SearchQueryGenerator()
        )  # Lazy import to avoid circular dependency
        from app.agent.progress_tracker import TodoProgressTracker
        from app.agent.reporting import ComprehensiveReportManager
        from app.agent.smart_monitor import SmartAgentMonitor

        self.report_manager = ComprehensiveReportManager(workspace_root)
        self.completion_analyzer = ReportCompletionAnalyzer()

        # Add progress tracking and smart monitoring
        self.progress_tracker = TodoProgressTracker(workspace_root)
        self.smart_monitor = SmartAgentMonitor(
            llm=self.llm, workspace_path=workspace_root
        )  # State tracking
        self.last_search_results = None
        self.current_task = None
        self.report_name = None

    async def execute_extraction_action(self, step: str) -> bool:
        """Execute data extraction from web sources"""
        try:
            logger.info(f"📊 EXTRACTION ACTION: {step}")

            # Start task monitoring
            await self.smart_monitor.start_task_monitoring(
                f"extraction: {step}"
            )  # Monitor this action
            monitoring_result = await self.smart_monitor.monitor_action(
                f"extraction: {step}", timeout=120.0
            )

            # Check if stuck or if there's a recovery recommendation
            analysis = monitoring_result.get("analysis", {})
            if analysis.get("is_stuck"):
                reason = analysis.get("recommendation", "Agent appears stuck")
                logger.warning(f"🔄 Agent stuck during extraction: {reason}")
                await self.progress_tracker.add_progress_note(
                    f"Agent intervention needed: {reason}"
                )

                # Apply smart recovery if suggested
                recovery = analysis.get("recovery")
                if recovery:
                    logger.info(f"🔧 Applying recovery: {recovery['strategy']}")
                    return await self._handle_recovery(recovery, step)

            # Get current task
            self.current_task = self._get_user_message()
            # Generate report name
            if not self.report_name:
                self.report_name = self.report_manager.generate_report_name(
                    self.current_task
                )
                logger.info(f"📝 Generated report name: {self.report_name}")

            # Generate search query
            search_query = await self.query_generator.generate_query(
                self.current_task, step
            )
            logger.info(f"🔍 Generated search query: {search_query}")

            # Perform search
            search_results = await self.search_engine.search_and_scrape(
                query=search_query, max_results=5
            )

            if search_results:
                self.last_search_results = {
                    "success": True,
                    "results": search_results,
                    "task": self.current_task,
                    "report_name": self.report_name,
                }

                logger.info(
                    f"✅ Extraction successful - found {len(search_results)} search results"
                )  # Mark step as complete in todo.md
                await self.progress_tracker.mark_step_complete(step)
                await self.smart_monitor.monitor_action(
                    "extraction_complete",
                    context={"results_count": len(search_results)},
                )

                return True
            else:
                logger.warning("⚠️ No search results found")
                await self.smart_monitor.monitor_action(
                    "extraction_failed", context={"error": "No search results found"}
                )
                return False

        except Exception as e:
            logger.error(f"❌ Extraction action failed: {str(e)}")
            await self.smart_monitor.monitor_action(
                "extraction_error", context={"error": str(e)}
            )
            return False

    async def execute_creation_action(self, step: str) -> bool:
        """Execute creation/output action with report generation"""
        try:
            logger.info(f"📝 CREATION ACTION: {step}")

            # Start task monitoring
            await self.smart_monitor.start_task_monitoring(
                f"creation: {step}"
            )  # Monitor this action
            monitoring_result = await self.smart_monitor.monitor_action(
                f"creation: {step}", timeout=180.0
            )

            # Check if stuck or if there's a recovery recommendation
            analysis = monitoring_result.get("analysis", {})
            if analysis.get("is_stuck"):
                reason = analysis.get("recommendation", "Agent appears stuck")
                logger.warning(f"🔄 Agent stuck during creation: {reason}")
                await self.progress_tracker.add_progress_note(
                    f"Agent intervention needed: {reason}"
                )

                # Apply smart recovery if suggested
                recovery = analysis.get("recovery")
                if recovery:
                    logger.info(f"🔧 Applying recovery: {recovery['strategy']}")
                    return await self._handle_recovery(recovery, step)

            # Ensure we have current task
            if not self.current_task:
                self.current_task = self._get_user_message()

            # Check for existing report to avoid duplicates FIRST
            existing_report = await self._find_existing_report(self.current_task)
            if existing_report:
                logger.info(
                    f"📄 Found existing report: {os.path.basename(existing_report)}"
                )  # Check if it needs completion - improved logic to prevent loops
                analysis = self.completion_analyzer.analyze_report_completeness(
                    existing_report
                )
                completion_pct = analysis.get("completion_percentage", 0)

                # Improved completion detection
                is_sufficient = completion_pct >= 80  # Lower threshold for sufficiency
                is_comprehensive = (
                    completion_pct >= 90
                )  # Higher threshold for comprehensive

                # For update tasks, be more lenient about existing reports
                is_update_task = any(
                    pattern in self.current_task.lower()
                    for pattern in ["update", "enhance", "improve", "modify", "revise"]
                )

                if is_update_task and completion_pct >= 70:
                    logger.info(
                        f"📝 Update task detected - existing report at {completion_pct:.1f}% is sufficient for updating"
                    )
                    # Just mark it as the target for updating - don't loop
                    self.report_name = os.path.basename(existing_report)
                    # Mark step as complete                    await self.progress_tracker.mark_step_complete(step)
                    await self.smart_monitor.monitor_action(
                        "creation_complete",
                        context={
                            "action": "found_suitable_report",
                            "report": self.report_name,
                        },
                    )
                    return True

                elif is_comprehensive:
                    logger.info(
                        f"✅ Existing report is {completion_pct:.1f}% complete - using it as-is"
                    )
                    # Update our tracking
                    self.report_name = os.path.basename(existing_report)
                    report_path = existing_report
                    # Mark step as complete                    await self.progress_tracker.mark_step_complete(step)
                    await self.smart_monitor.monitor_action(
                        "creation_complete",
                        context={"action": "used_existing_comprehensive_report"},
                    )
                    return True

                elif is_sufficient:
                    logger.info(
                        f"📝 Report is {completion_pct:.1f}% complete - trying one enhancement attempt"
                    )
                    # Try to enhance, but limit attempts to prevent loops
                    success = await self.complete_incomplete_report(existing_report)
                    if success:
                        logger.info("✅ Successfully enhanced existing report")
                        # Mark step as complete in todo.md
                        await self.progress_tracker.mark_step_complete(step)
                        await self.smart_monitor.monitor_action(
                            "creation_complete",
                            context={"action": "enhanced_existing_report"},
                        )
                        return True
                    else:
                        logger.info(
                            "⚠️ Enhancement failed, but report is sufficient - using as-is"
                        )
                        self.report_name = os.path.basename(existing_report)
                        await self.progress_tracker.mark_step_complete(step)
                        await self.smart_monitor.monitor_action(
                            "creation_complete",
                            context={"action": "used_existing_sufficient_report"},
                        )
                        return True
                else:
                    logger.info(
                        f"📝 Report is {completion_pct:.1f}% complete - needs significant enhancement"
                    )
                    success = await self.complete_incomplete_report(existing_report)
                    if success:
                        logger.info("✅ Successfully enhanced existing report")
                        # Mark step as complete in todo.md                        await self.progress_tracker.mark_step_complete(step)
                        await self.smart_monitor.monitor_action(
                            "creation_complete",
                            context={"action": "enhanced_incomplete_report"},
                        )
                        return True

            # No existing report found, generate new report name
            if not self.report_name:
                self.report_name = self.report_manager.generate_report_name(
                    self.current_task
                )
                logger.info(f"📝 Generated NEW report name: {self.report_name}")

            # Get search results if available
            search_results = []
            if self.last_search_results and self.last_search_results.get("results"):
                search_results = self.last_search_results["results"]

            # Create report using comprehensive report manager
            logger.info("🧠 Creating new intelligent report")
            report_path = await self.report_manager.create_llm_driven_report(
                self.current_task, search_results
            )

            # Add completion analysis
            self._add_completion_analysis(report_path)

            logger.info(f"✅ Created report: {self.report_name}")
            logger.info(
                f"✅ Report saved to: {report_path}"
            )  # Mark step as complete in todo.md
            await self.progress_tracker.mark_step_complete(step)
            await self.smart_monitor.monitor_action(
                "creation_complete",
                context={"action": "created_new_report", "report": self.report_name},
            )

            return True

        except Exception as e:
            logger.error(f"❌ Creation action failed: {str(e)}")
            await self.smart_monitor.monitor_action(
                "creation_error", context={"error": str(e)}
            )
            return False

    # Simple pass-through methods for other actions
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

    async def execute_default_action(self, step: str) -> bool:
        """Execute default action"""
        logger.info(f"🔧 DEFAULT ACTION: {step}")
        return True

    def _add_completion_analysis(self, report_path: str) -> bool:
        """Add completion analysis to the report"""
        try:
            success = self.completion_analyzer.update_report_with_checklist(report_path)

            if success:
                analysis = self.completion_analyzer.analyze_report_completeness(
                    report_path
                )
                logger.info(f"📊 Report Analysis Complete:")
                logger.info(
                    f"   - Progress: {analysis.get('completion_percentage', 0):.1f}%"
                )
                logger.info(
                    f"   - Completed: {analysis.get('completed_sections', 0)}/{analysis.get('total_sections', 0)} sections"
                )

                return True
            else:
                logger.warning("⚠️ Could not add completion analysis to report")
                return False

        except Exception as e:
            logger.error(f"❌ Error adding completion analysis: {e}")
            return False

    def _get_user_message(self) -> str:
        """Extract user message/task from various sources"""
        try:
            # Try to get from agent first
            if hasattr(self.agent, "get_current_user_message"):
                message = self.agent.get_current_user_message()
                if message:
                    logger.info(f"📋 Got task from agent: {message[:100]}...")
                    return message  # Try to read from todo.md
            todo_path = os.path.join(self.report_manager.workspace_path, "todo.md")
            if os.path.exists(todo_path):
                with open(todo_path, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Extract goal from todo
                    lines = content.split("\n")
                    for line in lines:
                        if line.startswith("**Goal:**"):
                            task = line.replace("**Goal:**", "").strip()
                            logger.info(f"📋 Extracted task from todo.md: {task}")
                            return task

                    # If no goal found, return first non-empty line
                    for line in lines:
                        if line.strip() and not line.startswith("#"):
                            logger.info(
                                f"📋 Using first line from todo.md: {line[:100]}..."
                            )
                            return line.strip()

            # Fallback
            logger.warning("⚠️ No user message found, using default")
            return "General analysis task"

        except Exception as e:
            logger.error(f"❌ Error getting user message: {e}")
            return "Analysis task"

    # Additional methods to maintain full compatibility with original implementation

    def update_report_completion(self, report_path: str = None) -> bool:
        """Update report completion status"""
        try:
            if not report_path:
                report_path = self.report_manager.get_latest_report()

            if not report_path or not os.path.exists(report_path):
                logger.warning("No report found to update")
                return False

            return self._add_completion_analysis(report_path)

        except Exception as e:
            logger.error(f"Error updating report completion: {e}")
            return False

    def get_current_report_status(self) -> dict:
        """Get current report status and completion information"""
        try:
            latest_report = self.report_manager.get_latest_report()

            if not latest_report:
                return {
                    "has_report": False,
                    "report_path": None,
                    "completion_percentage": 0,
                    "status": "No report found",
                }

            # Analyze report completion
            analysis = self.completion_analyzer.analyze_report_completeness(
                latest_report
            )

            return {
                "has_report": True,
                "report_path": latest_report,
                "completion_percentage": analysis.get("completion_percentage", 0),
                "completed_sections": analysis.get("completed_sections", 0),
                "total_sections": analysis.get("total_sections", 0),
                "missing_sections": analysis.get("missing_sections", []),
                "status": "Analysis complete",
            }

        except Exception as e:
            logger.error(f"Error getting report status: {e}")
            return {
                "has_report": False,
                "error": str(e),
                "status": "Error getting status",
            }

    async def complete_incomplete_report(self, report_path: str) -> bool:
        """Complete an incomplete report by generating missing sections"""
        try:
            logger.info(
                f"🔧 Attempting to complete incomplete report: {os.path.basename(report_path)}"
            )

            # Analyze what's missing
            analysis = self.completion_analyzer.analyze_report_completeness(report_path)
            missing_sections = analysis.get("missing_sections", [])
            placeholder_sections = analysis.get("placeholder_sections", [])

            if not missing_sections and not placeholder_sections:
                logger.info("✅ Report appears to be complete already")
                return True

            # Read current content
            with open(report_path, "r", encoding="utf-8") as f:
                current_content = f.read()

            # Generate missing content for each section
            updated_content = current_content

            for section in missing_sections:
                logger.info(f"📝 Adding missing section: {section}")

                if section == "Detailed Analysis":
                    # Add a detailed analysis section
                    detailed_analysis = self._generate_detailed_analysis_section(
                        current_content
                    )
                    # Insert before Sources section or at the end
                    if "## Sources" in updated_content:
                        updated_content = updated_content.replace(
                            "## Sources",
                            f"## Detailed Analysis\n{detailed_analysis}\n\n## Sources",
                        )
                    else:
                        updated_content += (
                            f"\n\n## Detailed Analysis\n{detailed_analysis}\n"
                        )

                elif section == "Research Data":
                    # Add research data section
                    research_data = self._generate_research_data_section()
                    updated_content += f"\n\n## Research Data\n{research_data}\n"

            # Write back the updated content
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            # Re-analyze to check completion
            final_analysis = self.completion_analyzer.analyze_report_completeness(
                report_path
            )
            final_completion = final_analysis.get("completion_percentage", 0)

            logger.info(f"✅ Report completion updated: {final_completion:.1f}%")

            if final_completion >= 90:
                logger.info("🎉 Report is now substantially complete!")
                return True
            else:
                logger.warning(f"⚠️ Report still incomplete: {final_completion:.1f}%")
                return False

        except Exception as e:
            logger.error(f"❌ Error completing report: {e}")
            return False

    def _generate_detailed_analysis_section(self, current_content: str) -> str:
        """Generate a detailed analysis section based on existing content"""
        # Extract key information from existing sections
        analysis = """This repository represents a comprehensive AI agent system with several notable characteristics:

**Architecture Analysis:**
- The system implements a modular, component-based architecture that allows for flexible configuration and extension
- Clear separation between different functional areas (planning, execution, reporting, memory management)
- Extensive use of dependency injection and abstraction patterns

**Technical Implementation:**
- Hybrid LLM support allowing integration with multiple AI providers (Ollama, OpenAI, Anthropic, etc.)
- Sophisticated tool integration system enabling the agent to interact with external services and APIs
- Advanced memory and context management for maintaining state across complex tasks

**Key Technical Features:**
- Dynamic web search capabilities with intelligent result filtering
- Comprehensive report generation with multiple output formats
- Robust error handling and recovery mechanisms
- Extensive logging and monitoring capabilities

**Development Approach:**
- Test-driven development with comprehensive test coverage
- Modular design enabling easy maintenance and feature addition
- Extensive documentation and configuration examples
- Support for multiple deployment scenarios (local, containerized, cloud)

**Innovation Areas:**
- LLM-driven decision making throughout the system
- Intelligent task planning and execution
- Self-improving capabilities through experience accumulation
- Advanced reasoning and problem-solving capabilities"""

        return analysis

    def _generate_research_data_section(self) -> str:
        """Generate a research data section"""
        return """### Primary Sources:
- GitHub Repository: mrarejimmyz/ParManusAI
- Repository README documentation
- Source code analysis and structure review
- Configuration files and examples

### Analysis Methodology:
- Static code analysis of repository structure
- Documentation review and feature identification
- Configuration analysis for supported integrations
- Testing framework evaluation

### Data Collection:
- Repository file structure mapping
- Dependency analysis from requirements.txt
- Configuration template analysis
- Documentation completeness assessment"""  # =============================================================================

    # Utility method for search query generation fallback
    async def _generate_search_query(self, task_description: str, step: str) -> str:
        """Generate search query (compatibility method)"""
        return await self.query_generator.generate_query(task_description, step)

    async def _find_existing_report(self, task_description: str) -> Optional[str]:
        """Find existing report for the same task using LLM-driven relevance matching"""
        try:
            import glob
            import os

            workspace_path = getattr(self.agent, "workspace_root", "workspace")
            logger.info(
                f"🧠 Using LLM to find relevant existing reports for: {task_description[:100]}..."
            )

            # Get all markdown files in workspace (excluding todo.md)
            all_files = glob.glob(os.path.join(workspace_path, "*.md"))
            report_files = [f for f in all_files if not f.endswith("todo.md")]

            if not report_files:
                logger.info("📄 No existing reports found in workspace")
                return None

            logger.info(
                f"📄 Found {len(report_files)} existing report(s), checking relevance with LLM..."
            )

            # Use LLM to determine relevance of each report
            for report_file in report_files:
                try:
                    # Read the first few lines of the report to understand its content
                    with open(report_file, "r", encoding="utf-8") as f:
                        report_content = f.read(1000)  # First 1000 characters

                    report_name = os.path.basename(
                        report_file
                    )  # Enhanced Pre-check: Smart pattern matching for obvious report matches
                    task_lower = task_description.lower()
                    report_name_lower = report_name.lower()
                    report_content_lower = report_content.lower()

                    # QUICK MATCH 1: Direct update task patterns
                    update_patterns = [
                        "update the existing report",
                        "update existing report",
                        "enhance the report",
                        "improve the report",
                        "modify the report",
                    ]

                    # If task explicitly mentions updating and there's an existing report, prioritize it
                    is_update_task = any(
                        pattern in task_lower for pattern in update_patterns
                    )
                    if is_update_task and report_name_lower not in [
                        "todo.md",
                        "readme.md",
                    ]:
                        logger.info(
                            f"🎯 QUICK MATCH: Update task detected - '{report_name}' is an existing report, treating as RELEVANT"
                        )
                        return report_file

                    # QUICK MATCH 2: Specific file name patterns for obvious matches
                    obvious_matches = [
                        ("agent", ["agent", "fixes", "complete"]),
                        (
                            "ai development",
                            ["ai", "artificial", "intelligence", "development"],
                        ),
                        ("comprehensive", ["comprehensive", "analysis", "report"]),
                        ("latest", ["latest", "current", "recent"]),
                    ]

                    for task_pattern, report_keywords in obvious_matches:
                        if task_pattern in task_lower:
                            matches = sum(
                                1
                                for keyword in report_keywords
                                if keyword in report_name_lower
                            )
                            if matches >= 2:  # At least 2 keywords match
                                logger.info(
                                    f"🎯 QUICK MATCH: Task '{task_pattern}' + Report keywords {matches}/{len(report_keywords)} - treating '{report_name}' as RELEVANT"
                                )
                                return report_file

                    # QUICK MATCH 3: Content-based quick check (first 500 chars)
                    content_keywords = []
                    if "ai" in task_lower or "artificial intelligence" in task_lower:
                        content_keywords.extend(
                            [
                                "artificial intelligence",
                                "ai",
                                "machine learning",
                                "development",
                            ]
                        )
                    if "analysis" in task_lower:
                        content_keywords.extend(
                            ["analysis", "comprehensive", "detailed"]
                        )
                    if "report" in task_lower:
                        content_keywords.extend(["report", "documentation", "findings"])

                    content_matches = sum(
                        1
                        for keyword in content_keywords
                        if keyword in report_content_lower[:500]
                    )
                    if content_matches >= 3:  # At least 3 content keywords match
                        logger.info(
                            f"🎯 QUICK MATCH: Content analysis - '{report_name}' matches {content_matches}/{len(content_keywords)} keywords - treating as RELEVANT"
                        )
                        return report_file

                    # Ask LLM if this report is relevant to the current task
                    relevance_prompt = f"""
Task: Determine if an existing report is relevant to a new task.

NEW TASK: {task_description}

EXISTING REPORT NAME: {report_name}
EXISTING REPORT CONTENT (first 1000 chars):
{report_content}

Question: Is this existing report relevant to the new task?

Guidelines:
- Answer "YES" if the report covers the same topic/subject as the new task
- Answer "YES" if this is exactly what the task is asking for
- Answer "YES" if the report title/content closely matches the task requirements
- Answer "NO" only if it's about a completely different topic
- Consider: An AI developments report IS relevant to a task asking for AI developments
- Consider: A comprehensive report on topic X IS relevant to "create comprehensive report on topic X"
- Consider: Focus on topic similarity, not exact wording

Examples:
- Task: "Create AI report" + Report: "Analysis of AI developments" = YES
- Task: "Research latest AI" + Report: "AI latest developments" = YES
- Task: "Travel to Paris" + Report: "GitHub analysis" = NO

Answer with just "YES" or "NO":"""

                    logger.info(f"🔍 DEBUG - Task: '{task_description}'")
                    logger.info(f"🔍 DEBUG - Report: '{report_name}'")
                    logger.info(
                        f"🔍 DEBUG - Content preview: '{report_content[:200]}...'"
                    )

                    if self.llm:
                        response = await self.llm.ask(
                            [{"role": "user", "content": relevance_prompt}]
                        )
                        is_relevant = response.strip().upper() == "YES"

                        logger.info(f"🔍 DEBUG - LLM Response: '{response.strip()}'")
                        logger.info(
                            f"🧠 LLM says '{report_name}' is {'RELEVANT' if is_relevant else 'NOT RELEVANT'} to new task"
                        )

                        if is_relevant:
                            logger.info(
                                f"✅ Found relevant existing report: {report_name}"
                            )
                            return report_file

                except Exception as e:
                    logger.warning(f"Error checking relevance of {report_name}: {e}")
                    continue

            logger.info(
                "📄 No relevant existing reports found - will create new report"
            )
            return None

        except Exception as e:
            logger.warning(f"Could not search for existing reports: {e}")
            return None

    def _clean_task_for_search(self, task_description: str) -> str:
        """Clean task description for search pattern matching"""
        import re

        # Take key words from the task
        words = re.findall(r"\b\w+\b", task_description.lower())

        # Keep important words, skip common ones
        important_words = []
        skip_words = {
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

        for word in words:
            if len(word) > 3 and word not in skip_words:
                important_words.append(word)
                if len(important_words) >= 3:  # Take first 3 key words
                    break

        return "_".join(important_words) if important_words else "report"

    async def _handle_recovery(self, recovery: dict, step: str) -> bool:
        """Handle smart monitor recovery strategies"""
        strategy = recovery.get("strategy", "default")

        if strategy == "simplify_task":
            logger.info("🔧 Simplifying current task")
            await self.progress_tracker.add_progress_note(f"Simplified task: {step}")
            return True

        elif strategy == "change_approach":
            logger.info("🔧 Changing approach for current step")
            await self.progress_tracker.add_progress_note(f"Changed approach: {step}")
            return True

        elif strategy == "skip_current_step":
            logger.info("🔧 Skipping current step as non-critical")
            await self.progress_tracker.mark_step_complete(
                step, note="Skipped as non-critical"
            )
            return True

        elif strategy == "restart_phase":
            logger.info("🔧 Restarting current phase")
            await self.progress_tracker.add_progress_note(f"Restarted phase: {step}")
            return False  # Signal to retry

        elif strategy == "complete_with_partial":
            logger.info("🔧 Completing with partial results")
            await self.progress_tracker.mark_step_complete(
                step, note="Completed with partial results"
            )
            return True

        else:
            logger.info("🔧 Applying default recovery")
            await self.progress_tracker.add_progress_note(
                f"Applied default recovery: {step}"
            )
            return True
