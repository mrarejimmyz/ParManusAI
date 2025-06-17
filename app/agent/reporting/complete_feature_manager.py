"""
Complete Feature Manager
Ensures ALL features from the original monolithic files are preserved and accessible
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Import all modular components from their new locations
from app.agent.actions.action_executor_features import ActionExecutorFeatures
from app.agent.reporting.generators.data_driven_report_generator import (
    DataDrivenReportGenerator,
)
from app.agent.reporting.generators.simple_report_generator import SimpleReportGenerator
from app.agent.reporting.templates.report_template_manager import ReportTemplateManager
from app.agent.reporting.utils.llm_response_parser import LLMResponseParser
from app.agent.reporting.utils.report_name_generator import ReportNameGenerator
from app.agent.reporting.validation.search_query_generator import SearchQueryGenerator
from app.agent.reporting.validation.search_result_prefilter import SearchResultPreFilter
from app.agent.reporting.validation.search_validator import SearchResultValidator
from app.agent.todo.enhanced_todo_manager import EnhancedTodoManager
from app.logger import logger


class CompleteFeatureManager:
    """
    Master manager that provides access to ALL features from the original files
    This ensures no functionality is lost in the modularization process
    """

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = workspace_path
        os.makedirs(workspace_path, exist_ok=True)
        # Initialize ALL modular components
        self.name_generator = ReportNameGenerator()
        self.prefilter = SearchResultPreFilter()
        self.response_parser = LLMResponseParser()
        self.enhanced_todo = EnhancedTodoManager(workspace_path)
        self.template_manager = ReportTemplateManager(workspace_path)
        self.search_validator = SearchResultValidator()
        self.data_generator = DataDrivenReportGenerator(workspace_path)
        self.simple_generator = SimpleReportGenerator(workspace_path)
        self.query_generator = SearchQueryGenerator()
        self.action_executor = ActionExecutorFeatures()

        logger.info("🔧 Complete Feature Manager initialized with ALL modules")

    # =============================================================================
    # REPORT NAME GENERATION FEATURES
    # =============================================================================

    def generate_report_name(
        self, task_description: str, report_type: str = "analysis"
    ) -> str:
        """Generate unique report filename - preserves original functionality"""
        return self.name_generator.generate_report_name(task_description, report_type)

    def generate_specialized_name(
        self, task_description: str, report_type: str, suffix: str = None
    ) -> str:
        """Generate specialized report names with custom suffixes"""
        return self.name_generator.generate_specialized_name(
            task_description, report_type, suffix
        )

    def generate_todo_name(self, task_description: str) -> str:
        """Generate filename for todo files"""
        return self.name_generator.generate_todo_name(task_description)

    # =============================================================================
    # BASIC REPORT CREATION FEATURES
    # =============================================================================

    def should_create_new_report(self, task_description: str) -> bool:
        """Determine if a new report should be created - preserves original logic"""
        return True  # Original always returned True

    def create_report_template(self, task_description: str, report_name: str) -> str:
        """Create basic report template - preserves original functionality"""
        return self.template_manager.create_basic_template(
            task_description, report_name
        )

    def create_report(self, task_description: str, content: str = None) -> str:
        """Create new report file - preserves original functionality"""
        report_name = self.generate_report_name(task_description)

        if content is None:
            content = self.create_report_template(task_description, report_name)

        report_path = os.path.join(self.workspace_path, report_name)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"📝 Created basic report: {report_name}")
        return report_path

    # =============================================================================
    # INTELLIGENT REPORT CREATION FEATURES
    # =============================================================================

    def create_intelligent_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create intelligent report with predefined content - preserves original functionality"""
        content = self.template_manager.create_intelligent_report(
            task_description, findings, recommendations, next_steps
        )

        report_name = self.generate_report_name(task_description)
        report_path = os.path.join(self.workspace_path, report_name)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"📝 Created intelligent report: {report_name}")
        return report_path

    def create_intelligent_report_from_search_data(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create intelligent report from search data - preserves original functionality"""
        report_name = self.generate_report_name(task_description)

        if search_results:
            # Use template manager for search-based reports
            content = self.template_manager.create_search_based_report(
                task_description, search_results
            )
        else:
            # Fallback to basic template
            content = self.create_report_template(task_description, report_name)

        report_path = os.path.join(self.workspace_path, report_name)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"📝 Created search-based report: {report_name}")
        return report_path

    # =============================================================================
    # LLM-DRIVEN REPORT FEATURES
    # =============================================================================

    async def create_llm_driven_report(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create LLM-driven report - preserves original functionality"""
        report_name = self.generate_report_name(task_description)

        if not search_results:
            # Fallback to template if no search results
            content = self.create_report_template(task_description, report_name)
            report_path = os.path.join(self.workspace_path, report_name)

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            # Use data-driven generator for LLM reports
            report_path = await self.data_generator.create_llm_driven_report(
                task_description, search_results, report_name
            )

        return report_path

    # =============================================================================
    # SPECIALIZED REPORT TEMPLATES
    # =============================================================================

    def _create_travel_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create travel report - preserves original functionality"""
        return self.template_manager._create_travel_report(
            task_description, findings, recommendations, next_steps
        )

    def _create_generic_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create generic report - preserves original functionality"""
        return self.template_manager._create_generic_report(
            task_description, findings, recommendations, next_steps
        )

    def _create_kathmandu_report(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create Kathmandu report - preserves original functionality"""
        return self.template_manager._create_kathmandu_report(
            task_description, search_results
        )

    def _create_waterloo_report(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create Waterloo report - preserves original functionality"""
        return self.template_manager._create_waterloo_report(
            task_description, search_results
        )

    def _create_intelligent_generic_report(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create intelligent generic report - preserves original functionality"""
        return self.template_manager._create_intelligent_generic_report(
            task_description, search_results
        )

    # =============================================================================
    # TODO MANAGEMENT FEATURES
    # =============================================================================

    def update_todo_with_next_steps(
        self, task_description: str, todo_path: str = "workspace/todo.md"
    ) -> None:
        """Update todo with next steps - preserves original functionality"""
        self.enhanced_todo.update_todo_with_next_steps(task_description, todo_path)

    def _update_travel_todo(self, todo_path: str) -> None:
        """Update travel todo - preserves original functionality"""
        self.enhanced_todo._update_travel_todo(todo_path)

    def _update_generic_todo(self, task_description: str, todo_path: str) -> None:
        """Update generic todo - preserves original functionality"""
        self.enhanced_todo._update_generic_todo(task_description, todo_path)

    def create_new_todo_from_task(self, task_description: str) -> str:
        """Create new todo file for specific task"""
        return self.enhanced_todo.create_new_todo_from_task(task_description)

    # =============================================================================
    # SEARCH RESULT VALIDATION FEATURES
    # =============================================================================

    async def _validate_search_results_relevance(
        self, search_results: List[Dict], task_description: str
    ) -> Tuple[List[Dict], bool]:
        """Validate search results relevance - preserves original functionality"""
        return await self.search_validator.validate_results(
            search_results, task_description
        )

    async def _llm_validate_search_results_relevance(
        self, search_results: List[Dict], task_description: str
    ) -> Tuple[List[Dict], bool]:
        """LLM-based validation - preserves original functionality"""
        return await self.search_validator._llm_validate_search_results_relevance(
            search_results, task_description
        )

    def _pre_filter_obvious_irrelevant(
        self, search_results: List[Dict], task_description: str
    ) -> List[Dict]:
        """Pre-filter irrelevant results - preserves original functionality"""
        filtered_results, _ = self.prefilter.pre_filter_results(
            search_results, task_description
        )
        return filtered_results

    def _keyword_validate_search_results_relevance(
        self, search_results: List[Dict], task_description: str
    ) -> Tuple[List[Dict], bool]:
        """Keyword-based validation - preserves original functionality"""
        return self.search_validator._keyword_validate_search_results_relevance(
            search_results, task_description
        )

    # =============================================================================
    # FALLBACK AND UTILITY FEATURES
    # =============================================================================

    def _create_data_driven_fallback(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create fallback report when LLM unavailable - preserves original functionality"""
        return self.data_generator._create_data_driven_fallback(
            task_description, search_results
        )

    # =============================================================================
    # SEARCH QUERY GENERATION FEATURES (from action executor)
    # =============================================================================

    async def _generate_search_query(self, task_description: str, step: str) -> str:
        """Generate search query - preserves original functionality"""
        return await self.query_generator.generate_search_query(task_description, step)

    async def _llm_generate_search_query(self, task_description: str, step: str) -> str:
        """LLM-based query generation - preserves original functionality"""
        return await self.query_generator._llm_generate_search_query(
            task_description, step
        )

    def _fallback_search_query(self, task_description: str, step: str) -> str:
        """Fallback query generation - preserves original functionality"""
        return self.query_generator._fallback_search_query(task_description, step)

    # =============================================================================
    # RESPONSE PARSING FEATURES
    # =============================================================================

    def parse_llm_relevance_response(
        self, llm_response: str, search_results: List[Dict]
    ) -> Tuple[List[Dict], List[str]]:
        """Parse LLM relevance decisions"""
        return self.response_parser.parse_relevance_decisions(
            llm_response, search_results
        )

    def parse_structured_content(self, llm_response: str) -> Dict[str, str]:
        """Parse LLM response into structured sections"""
        return self.response_parser.parse_structured_content(llm_response)

    # =============================================================================
    # ACTION EXECUTOR FEATURES (from manus_action_executor_improved.py)
    # =============================================================================

    async def execute_extraction_action(self, step: str) -> bool:
        """Execute extraction-type action step - preserves original functionality"""
        return await self.action_executor.execute_extraction_action(step)

    async def execute_research_action(self, step: str) -> bool:
        """Execute research-type action step - preserves original functionality"""
        return await self.action_executor.execute_research_action(step)

    async def execute_verification_action(self, step: str) -> bool:
        """Execute verification-type action step - preserves original functionality"""
        return await self.action_executor.execute_verification_action(step)

    async def execute_navigation_action(self, step: str) -> bool:
        """Execute navigation-type action step - preserves original functionality"""
        return await self.action_executor.execute_navigation_action(step)

    async def execute_creation_action(self, step: str) -> bool:
        """Execute creation-type action step - preserves original functionality"""
        return await self.action_executor.execute_creation_action(step)

    async def execute_default_action(self, step: str) -> bool:
        """Execute default/fallback action step - preserves original functionality"""
        return await self.action_executor.execute_default_action(step)

    # =============================================================================
    # REPORT COMPLETION AND STATUS FEATURES
    # =============================================================================

    def _add_completion_analysis(self, report_path: str) -> bool:
        """Add completion analysis to report - preserves original functionality"""
        return self.action_executor._add_completion_analysis(report_path)

    def update_report_completion(self, report_path: str = None) -> bool:
        """Update report completion status - preserves original functionality"""
        return self.action_executor.update_report_completion(report_path)

    def get_current_report_status(self) -> Dict[str, Any]:
        """Get current report status - preserves original functionality"""
        return self.action_executor.get_current_report_status()

    def complete_incomplete_report(self, report_path: str) -> bool:
        """Complete incomplete report - preserves original functionality"""
        return self.action_executor.complete_incomplete_report(report_path)

    def _generate_report_completion(
        self, current_content: str, missing_sections: List[str]
    ) -> str:
        """Generate completion content - preserves original functionality"""
        return self.action_executor._generate_report_completion(
            current_content, missing_sections
        )

    def _enhance_report_manually(self, current_content: str) -> str:
        """Enhance report manually - preserves original functionality"""
        return self.action_executor._enhance_report_manually(current_content)

    def _get_user_message(self) -> str:
        """Get user message - preserves original functionality"""
        return self.action_executor._get_user_message()

    def get_all_available_features(self) -> Dict[str, List[str]]:
        """Return list of all available features organized by category"""
        return {
            "report_generation": [
                "generate_report_name",
                "create_report",
                "create_intelligent_report",
                "create_llm_driven_report",
                "create_intelligent_report_from_search_data",
            ],
            "specialized_reports": [
                "_create_travel_report",
                "_create_generic_report",
                "_create_kathmandu_report",
                "_create_waterloo_report",
                "_create_intelligent_generic_report",
            ],
            "todo_management": [
                "update_todo_with_next_steps",
                "_update_travel_todo",
                "_update_generic_todo",
                "create_new_todo_from_task",
            ],
            "search_validation": [
                "_validate_search_results_relevance",
                "_llm_validate_search_results_relevance",
                "_pre_filter_obvious_irrelevant",
                "_keyword_validate_search_results_relevance",
            ],
            "query_generation": [
                "_generate_search_query",
                "_llm_generate_search_query",
                "_fallback_search_query",
            ],
            "action_execution": [
                "execute_extraction_action",
                "execute_research_action",
                "execute_verification_action",
                "execute_navigation_action",
                "execute_creation_action",
                "execute_default_action",
            ],
            "report_completion": [
                "_add_completion_analysis",
                "update_report_completion",
                "get_current_report_status",
                "complete_incomplete_report",
                "_generate_report_completion",
                "_enhance_report_manually",
            ],
            "response_parsing": [
                "parse_llm_relevance_response",
                "parse_structured_content",
            ],
            "utilities": [
                "generate_specialized_name",
                "generate_todo_name",
                "_create_data_driven_fallback",
                "should_create_new_report",
                "create_report_template",
                "_get_user_message",
            ],
        }

    def verify_feature_completeness(self) -> Dict[str, bool]:
        """Verify that all original features are accessible"""
        all_features = self.get_all_available_features()
        verification_results = {}

        for category, features in all_features.items():
            category_complete = True
            for feature in features:
                if not hasattr(self, feature):
                    category_complete = False
                    logger.warning(f"⚠️ Missing feature: {feature}")

            verification_results[category] = category_complete
            if category_complete:
                logger.info(f"✅ {category}: All {len(features)} features available")
            else:
                logger.warning(f"❌ {category}: Some features missing")

        return verification_results

    def get_feature_usage_stats(self) -> Dict[str, int]:
        """Track usage of different features (for debugging and optimization)"""  # This would be implemented with actual usage tracking
        # For now, return a placeholder
        return {
            "reports_created": 0,
            "todos_updated": 0,
            "search_validations": 0,
            "llm_queries": 0,
        }

    def get_latest_report(self) -> Optional[str]:
        """Get the latest report file from the workspace"""
        import glob

        # Look for all .md files in the workspace
        pattern = os.path.join(self.workspace_path, "*.md")
        report_files = glob.glob(pattern)

        if not report_files:
            return None

        # Filter out todo.md and find actual reports
        actual_reports = [f for f in report_files if not f.endswith("todo.md")]

        if not actual_reports:
            return None

        # Return the most recently modified file
        latest_report = max(actual_reports, key=os.path.getmtime)
        return latest_report

    # =============================================================================
