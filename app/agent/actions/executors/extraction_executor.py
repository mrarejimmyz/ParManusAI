"""
Extraction action executor for data gathering from web sources.
"""

from typing import Optional

from app.logger import logger


class ExtractionExecutor:
    """Handles data extraction actions from web sources"""

    def __init__(self, search_engine, query_generator, smart_monitor, progress_tracker):
        self.search_engine = search_engine
        self.query_generator = query_generator
        self.smart_monitor = smart_monitor
        self.progress_tracker = progress_tracker
        self.last_search_results = None

    async def execute_extraction_action(self, step: str, current_task: str) -> bool:
        """Execute data extraction from web sources"""
        try:
            logger.info(f"📊 EXTRACTION ACTION: {step}")

            # Start task monitoring
            await self.smart_monitor.start_task_monitoring(f"extraction: {step}")

            # Monitor this action
            monitoring_result = await self.smart_monitor.monitor_action(
                f"extraction: {step}", timeout=120.0
            )

            # Check if action was skipped due to duplicates or other reasons
            if monitoring_result.get("should_skip"):
                reason = monitoring_result.get(
                    "reason", "Action skipped by smart monitor"
                )
                suggestion = monitoring_result.get(
                    "suggestion", "Continue with next step"
                )
                logger.info(f"⏭️ Smart monitor skipped action: {reason} - {suggestion}")
                await self.progress_tracker.add_progress_note(f"Skipped: {reason}")
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

            # Generate search query
            search_query = await self.query_generator.generate_query(current_task, step)
            logger.info(f"🔍 Generated search query: {search_query}")

            # Perform search
            search_results = await self.search_engine.search(
                search_query, max_results=10
            )

            if search_results:
                self.last_search_results = search_results
                logger.info(f"✅ Found {len(search_results)} search results")
                await self.progress_tracker.add_progress_note(
                    f"Extracted {len(search_results)} results"
                )
                await self.progress_tracker.mark_step_complete(step)
                return True
            else:
                logger.warning("⚠️ No search results found")
                await self.progress_tracker.add_progress_note("No results found")
                return False

        except Exception as e:
            logger.error(f"❌ Extraction action failed: {str(e)}")
            await self.smart_monitor.monitor_action(
                "extraction_error", context={"error": str(e)}
            )
            return False

    async def _handle_recovery(self, recovery: dict, step: str) -> bool:
        """Handle recovery strategies"""
        strategy = recovery.get("strategy", "default")

        if strategy == "simplify_task":
            logger.info("🔧 Applying simplified extraction approach")
            # Implement simplified extraction logic
            return True
        elif strategy == "skip_current_step":
            logger.info("⏭️ Skipping extraction step")
            await self.progress_tracker.mark_step_complete(step)
            return True
        else:
            logger.info(f"🔧 Applying default recovery for extraction: {strategy}")
            return True
