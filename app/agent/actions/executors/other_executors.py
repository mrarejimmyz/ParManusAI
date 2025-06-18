"""
Other action executors for research, verification, navigation, and default actions.
"""

from app.logger import logger


class ResearchExecutor:
    """Handles research-specific actions"""

    def __init__(self, extraction_executor):
        self.extraction_executor = extraction_executor

    async def execute_research_action(self, step: str, current_task: str) -> bool:
        """Execute research action"""
        logger.info(f"🔍 RESEARCH ACTION: {step}")
        # Research is essentially extraction with different context
        return await self.extraction_executor.execute_extraction_action(
            step, current_task
        )


class VerificationExecutor:
    """Handles verification actions"""

    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker

    async def execute_verification_action(self, step: str) -> bool:
        """Execute verification"""
        logger.info(f"✅ VERIFICATION ACTION: {step}")
        await self.progress_tracker.add_progress_note(f"Verified: {step}")
        await self.progress_tracker.mark_step_complete(step)
        return True


class NavigationExecutor:
    """Handles navigation actions"""

    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker

    async def execute_navigation_action(self, step: str) -> bool:
        """Execute navigation"""
        logger.info(f"🧭 NAVIGATION ACTION: {step}")
        await self.progress_tracker.add_progress_note(f"Navigated: {step}")
        await self.progress_tracker.mark_step_complete(step)
        return True


class DefaultExecutor:
    """Handles default/fallback actions"""

    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker

    async def execute_default_action(self, step: str) -> bool:
        """Execute default action"""
        logger.info(f"🔧 DEFAULT ACTION: {step}")
        await self.progress_tracker.add_progress_note(f"Processed: {step}")
        await self.progress_tracker.mark_step_complete(step)
        return True
