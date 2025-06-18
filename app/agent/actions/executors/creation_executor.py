"""
Creation action executor for report generation and management.
"""

import os
from typing import Optional

from app.logger import logger


class CreationExecutor:
    """Handles creation and report generation actions"""

    def __init__(
        self, report_manager, completion_analyzer, progress_tracker, smart_monitor
    ):
        self.report_manager = report_manager
        self.completion_analyzer = completion_analyzer
        self.progress_tracker = progress_tracker
        self.smart_monitor = smart_monitor
        self.report_name = None

    async def execute_creation_action(
        self, step: str, current_task: str, last_search_results: dict = None
    ) -> bool:
        """Execute creation/output action with report generation"""
        try:
            logger.info(f"📝 CREATION ACTION: {step}")

            # Start task monitoring
            await self.smart_monitor.start_task_monitoring(f"creation: {step}")

            # Monitor this action
            monitoring_result = await self.smart_monitor.monitor_action(
                f"creation: {step}", timeout=180.0
            )

            # Check if action was skipped due to duplicates or other reasons
            if monitoring_result.get("should_skip"):
                reason = monitoring_result.get(
                    "reason", "Action skipped by smart monitor"
                )
                suggestion = monitoring_result.get(
                    "suggestion", "Continue with next step"
                )
                logger.info(
                    f"⏭️ Smart monitor skipped creation action: {reason} - {suggestion}"
                )
                await self.progress_tracker.add_progress_note(
                    f"Skipped creation: {reason}"
                )

                # If skipped due to duplicates, try to work with existing report
                if "duplicate" in reason.lower():
                    existing_report = await self._find_existing_report(current_task)
                    if existing_report:
                        logger.info(
                            f"📄 Using existing report instead: {os.path.basename(existing_report)}"
                        )
                        success = await self._complete_incomplete_report(
                            existing_report
                        )
                        if success:
                            await self.progress_tracker.mark_step_complete(step)
                        return success

                return True  # Continue to next step

            # Check if stuck or if there's a recovery recommendation
            analysis = monitoring_result.get("analysis", {})
            if analysis.get("is_stuck"):
                reason = analysis.get("recommendation", "Agent appears stuck")
                logger.info(f"🔧 Smart monitor intervention: {reason}")
                await self.progress_tracker.add_progress_note(
                    f"Smart monitor intervention: {reason}"
                )

                # Apply smart recovery if suggested
                recovery = analysis.get("recovery")
                if recovery:
                    logger.info(f"🔧 Applying recovery: {recovery['strategy']}")
                    return await self._handle_recovery(recovery, step)

            # Check for existing report to avoid duplicates FIRST
            existing_report = await self._find_existing_report(current_task)
            if existing_report:
                logger.info(
                    f"📄 Found existing report: {os.path.basename(existing_report)}"
                )

                # Check if it needs completion - improved logic to prevent loops
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
                    pattern in current_task.lower()
                    for pattern in ["update", "enhance", "improve", "modify", "revise"]
                )

                if is_update_task and completion_pct >= 70:
                    logger.info(
                        f"📝 Update task detected - existing report at {completion_pct:.1f}% is sufficient for updating"
                    )
                    self.report_name = os.path.basename(existing_report)
                    await self.progress_tracker.mark_step_complete(step)
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
                    self.report_name = os.path.basename(existing_report)
                    await self.progress_tracker.mark_step_complete(step)
                    await self.smart_monitor.monitor_action(
                        "creation_complete",
                        context={"action": "used_existing_comprehensive_report"},
                    )
                    return True

                elif is_sufficient:
                    logger.info(
                        f"📝 Report is {completion_pct:.1f}% complete - trying one enhancement attempt"
                    )
                    success = await self._complete_incomplete_report(existing_report)
                    if success:
                        logger.info("✅ Successfully enhanced existing report")
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
                    success = await self._complete_incomplete_report(existing_report)
                    if success:
                        logger.info("✅ Successfully enhanced existing report")
                        await self.progress_tracker.mark_step_complete(step)
                        await self.smart_monitor.monitor_action(
                            "creation_complete",
                            context={"action": "enhanced_incomplete_report"},
                        )
                        return True

            # No existing report found, generate new report name
            if not self.report_name:
                self.report_name = self.report_manager.generate_report_name(
                    current_task
                )
                logger.info(f"📝 Generated NEW report name: {self.report_name}")

            # Get search results if available
            search_results = []
            if last_search_results and last_search_results.get("results"):
                search_results = last_search_results["results"]

            # Create report using comprehensive report manager
            logger.info("🧠 Creating new intelligent report")
            report_path = await self.report_manager.create_llm_driven_report(
                current_task, search_results
            )

            # Add completion analysis
            self._add_completion_analysis(report_path)

            logger.info(f"✅ Created report: {self.report_name}")
            logger.info(f"✅ Report saved to: {report_path}")

            # Mark step as complete in todo.md
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

    async def _find_existing_report(self, task_description: str) -> Optional[str]:
        """Find existing report for the task"""
        # Implementation would go here
        return None

    async def _complete_incomplete_report(self, report_path: str) -> bool:
        """Complete an incomplete report"""
        # Implementation would go here
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

    async def _handle_recovery(self, recovery: dict, step: str) -> bool:
        """Handle recovery strategies for creation actions"""
        strategy = recovery.get("strategy", "default")

        if strategy == "simplify_task":
            logger.info("🔧 Creating simplified report")
            # Create a basic report instead of comprehensive one
            return True
        elif strategy == "skip_current_step":
            logger.info("⏭️ Skipping creation step")
            await self.progress_tracker.mark_step_complete(step)
            return True
        else:
            logger.info(f"🔧 Applying default recovery for creation: {strategy}")
            return True
