"""
Simplified Manus Action Executor - Refactored Version
Streamlined version with focused functionality using comprehensive modular components
"""

import os
from typing import List, Optional

from app.agent.reporting.utils.report_completion_analyzer import ReportCompletionAnalyzer
from app.agent.reporting.validation.search_query_generator import SearchQueryGenerator
from app.logger import logger
from app.search.dynamic_web_search import DynamicWebSearcher
from .executors import (
    CreationExecutor,
    DefaultExecutor,
    ExtractionExecutor,
    NavigationExecutor,
    ResearchExecutor,
    VerificationExecutor,
)


class SimplifiedManusActionExecutor:
    """Simplified action executor with comprehensive modular components"""

    def __init__(self, agent):
        """Initialize with agent reference and modular components"""
        self.agent = agent
        self.llm = getattr(agent, "llm", None)
        workspace_root = getattr(agent, "workspace_root", "workspace")
        
        # Core components
        self.search_engine = DynamicWebSearcher(llm=self.llm)
        self.query_generator = SearchQueryGenerator()
        
        # Lazy import to avoid circular dependency
        from app.agent.progress_tracker import TodoProgressTracker
        from app.agent.reporting import ComprehensiveReportManager
        from app.agent.smart_monitor import SmartAgentMonitor

        self.report_manager = ComprehensiveReportManager(workspace_root)
        self.completion_analyzer = ReportCompletionAnalyzer()
        self.progress_tracker = TodoProgressTracker(workspace_root)
        self.smart_monitor = SmartAgentMonitor(llm=self.llm, workspace_path=workspace_root)

        # Initialize specialized executors
        self.extraction_executor = ExtractionExecutor(
            self.search_engine, self.query_generator, self.smart_monitor, self.progress_tracker
        )
        
        self.creation_executor = CreationExecutor(
            self.report_manager, self.completion_analyzer, self.progress_tracker, self.smart_monitor
        )
        
        self.research_executor = ResearchExecutor(self.extraction_executor)
        self.verification_executor = VerificationExecutor(self.progress_tracker)
        self.navigation_executor = NavigationExecutor(self.progress_tracker)
        self.default_executor = DefaultExecutor(self.progress_tracker)

        # State tracking
        self.current_task = None
        self.report_name = None

    async def execute_extraction_action(self, step: str) -> bool:
        """Execute data extraction from web sources"""
        if not self.current_task:
            self.current_task = self._get_user_message()
        
        success = await self.extraction_executor.execute_extraction_action(step, self.current_task)
        
        # Update shared state
        if hasattr(self.extraction_executor, 'last_search_results'):
            self.last_search_results = self.extraction_executor.last_search_results
            
        return success

    async def execute_creation_action(self, step: str) -> bool:
        """Execute creation/output action with report generation"""
        if not self.current_task:
            self.current_task = self._get_user_message()

        # Pass search results to creation executor
        last_search_results = getattr(self, 'last_search_results', None)
        success = await self.creation_executor.execute_creation_action(
            step, self.current_task, last_search_results
        )
        
        # Update shared state
        if hasattr(self.creation_executor, 'report_name'):
            self.report_name = self.creation_executor.report_name
            
        return success

    async def execute_research_action(self, step: str) -> bool:
        """Execute research action"""
        if not self.current_task:
            self.current_task = self._get_user_message()
        return await self.research_executor.execute_research_action(step, self.current_task)

    async def execute_verification_action(self, step: str) -> bool:
        """Execute verification"""
        return await self.verification_executor.execute_verification_action(step)

    async def execute_navigation_action(self, step: str) -> bool:
        """Execute navigation"""
        return await self.navigation_executor.execute_navigation_action(step)

    async def execute_default_action(self, step: str) -> bool:
        """Execute default action"""
        return await self.default_executor.execute_default_action(step)

    def _get_user_message(self) -> str:
        """Extract user message/task from various sources"""
        try:
            # Try to get from agent first
            if hasattr(self.agent, "get_current_user_message"):
                message = self.agent.get_current_user_message()
                if message:
                    logger.info(f"📋 Got task from agent: {message[:100]}...")
                    return message
            
            # Try to read from todo.md
            todo_path = os.path.join(self.report_manager.workspace_path, "todo.md")
            if os.path.exists(todo_path):
                with open(todo_path, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Extract goal from todo
                    lines = content.split("\n")
                    for line in lines:
                        if line.startswith("**Goal:**"):
                            task = line.replace("**Goal:**", "").strip()
                            if task:
                                logger.info(f"📋 Got task from todo: {task[:100]}...")
                                return task

            # Fallback: try to get from agent memory
            if hasattr(self.agent, "memory") and hasattr(self.agent.memory, "messages"):
                messages = self.agent.memory.messages
                for message in reversed(messages):
                    if hasattr(message, "role") and message.role == "user":
                        content = getattr(message, "content", "")
                        if content and len(content) > 10:
                            logger.info(f"📋 Got task from memory: {content[:100]}...")
                            return content

            # Last resort fallback
            fallback_task = "Create a comprehensive analysis report"
            logger.warning(f"⚠️ No specific task found, using fallback: {fallback_task}")
            return fallback_task

        except Exception as e:
            logger.error(f"❌ Error getting user message: {e}")
            return "Create a comprehensive analysis report"

    def update_report_completion(self, report_path: str = None) -> bool:
        """Update report completion analysis"""
        try:
            if not report_path:
                if self.report_name:
                    report_path = os.path.join(
                        self.report_manager.workspace_path, self.report_name
                    )
                else:
                    logger.warning("⚠️ No report path provided for completion update")
                    return False

            if not os.path.exists(report_path):
                logger.warning(f"⚠️ Report not found: {report_path}")
                return False

            return self.creation_executor._add_completion_analysis(report_path)

        except Exception as e:
            logger.error(f"❌ Error updating report completion: {e}")
            return False

    def get_current_report_status(self) -> dict:
        """Get current report status"""
        try:
            if not self.report_name:
                return {"status": "no_report", "message": "No active report"}

            report_path = os.path.join(self.report_manager.workspace_path, self.report_name)

            if not os.path.exists(report_path):
                return {"status": "missing", "message": f"Report file not found: {self.report_name}"}

            # Analyze completeness
            analysis = self.completion_analyzer.analyze_report_completeness(report_path)

            return {
                "status": "active",
                "report_name": self.report_name,
                "report_path": report_path,
                "completion_percentage": analysis.get("completion_percentage", 0),
                "completed_sections": analysis.get("completed_sections", 0),
                "total_sections": analysis.get("total_sections", 0),
                "analysis": analysis,
            }

        except Exception as e:
            logger.error(f"❌ Error getting report status: {e}")
            return {"status": "error", "message": str(e)}

    # Legacy compatibility methods for backward compatibility
    @property
    def last_search_results(self):
        """Get last search results for backward compatibility"""
        return getattr(self.extraction_executor, 'last_search_results', None)

    @last_search_results.setter  
    def last_search_results(self, value):
        """Set last search results for backward compatibility"""
        if hasattr(self.extraction_executor, 'last_search_results'):
            self.extraction_executor.last_search_results = value
