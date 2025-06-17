"""
Comprehensive Modular Report Manager
Combines all report generation capabilities in a clean, modular architecture
"""

import os
from typing import Dict, List, Optional

from app.logger import logger

from .complete_feature_manager import CompleteFeatureManager


class ComprehensiveReportManager:
    """
    Comprehensive report manager that provides access to ALL features from the original
    large file but in a clean, modular architecture for easier debugging.
    This is the main interface that preserves 100% compatibility with the original API.
    """

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = workspace_path
        os.makedirs(workspace_path, exist_ok=True)

        # Use the complete feature manager for ALL functionality
        self.feature_manager = CompleteFeatureManager(workspace_path)

        # Verify all features are available
        verification = self.feature_manager.verify_feature_completeness()
        all_complete = all(verification.values())

        if all_complete:
            logger.info(
                "✅ Comprehensive Report Manager: ALL original features verified and accessible"
            )
        else:
            logger.warning("⚠️ Some features may be missing - check logs for details")

    # =============================================================================
    # CORE INTERFACE METHODS - PRESERVE ORIGINAL API 100%
    # =============================================================================

    def generate_report_name(
        self, task_description: str, report_type: str = "analysis"
    ) -> str:
        """Generate a unique report filename"""
        return self.feature_manager.generate_report_name(task_description, report_type)

    def should_create_new_report(self, task_description: str) -> bool:
        """Determine if a new report should be created"""
        return self.feature_manager.should_create_new_report(task_description)

    def create_report_template(self, task_description: str, report_name: str) -> str:
        """Create a basic report template"""
        return self.feature_manager.create_report_template(
            task_description, report_name
        )

    def create_report(self, task_description: str, content: str = None) -> str:
        """Create a new report file"""
        return self.feature_manager.create_report(task_description, content)

    def create_intelligent_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create a report with intelligent content based on task type"""
        return self.feature_manager.create_intelligent_report(
            task_description, findings, recommendations, next_steps
        )

    def create_intelligent_report_from_search_data(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create an intelligent report by analyzing search results"""
        return self.feature_manager.create_intelligent_report_from_search_data(
            task_description, search_results
        )

    async def create_llm_driven_report(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create intelligent report using LLM analysis of search results"""
        return await self.feature_manager.create_llm_driven_report(
            task_description, search_results
        )

    # =============================================================================
    # SPECIALIZED REPORT METHODS - PRESERVE ORIGINAL FUNCTIONALITY
    # =============================================================================

    def _create_travel_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create a travel-specific report with intelligent content"""
        return self.feature_manager._create_travel_report(
            task_description, findings, recommendations, next_steps
        )

    def _create_generic_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create a generic report with intelligent content"""
        return self.feature_manager._create_generic_report(
            task_description, findings, recommendations, next_steps
        )

    def _create_kathmandu_report(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create an intelligent Kathmandu travel report"""
        return self.feature_manager._create_kathmandu_report(
            task_description, search_results
        )

    def _create_waterloo_report(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create an intelligent Waterloo travel report"""
        return self.feature_manager._create_waterloo_report(
            task_description, search_results
        )

    def _create_intelligent_generic_report(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create an intelligent generic report from search data"""
        return self.feature_manager._create_intelligent_generic_report(
            task_description, search_results
        )

    # =============================================================================
    # TODO MANAGEMENT METHODS - PRESERVE ORIGINAL FUNCTIONALITY
    # =============================================================================

    def update_todo_with_next_steps(
        self, task_description: str, todo_path: str = "workspace/todo.md"
    ) -> None:
        """Update the todo.md file with intelligent next steps"""
        self.feature_manager.update_todo_with_next_steps(task_description, todo_path)

    def _update_travel_todo(self, todo_path: str) -> None:
        """Update todo with travel-specific research steps"""
        self.feature_manager._update_travel_todo(todo_path)

    def _update_generic_todo(self, task_description: str, todo_path: str) -> None:
        """Update todo with generic task steps"""
        self.feature_manager._update_generic_todo(task_description, todo_path)

    # =============================================================================
    # SEARCH VALIDATION METHODS - PRESERVE ORIGINAL FUNCTIONALITY
    # =============================================================================

    async def _validate_search_results_relevance(
        self, search_results: List[Dict], task_description: str
    ):
        """Validate that search results are relevant to the task using LLM intelligence with fallback"""
        return await self.feature_manager._validate_search_results_relevance(
            search_results, task_description
        )

    async def _llm_validate_search_results_relevance(
        self, search_results: List[Dict], task_description: str
    ):
        """Use LLM to intelligently assess content relevance"""
        return await self.feature_manager._llm_validate_search_results_relevance(
            search_results, task_description
        )

    def _pre_filter_obvious_irrelevant(
        self, search_results: List[Dict], task_description: str
    ) -> List[Dict]:
        """Pre-filter obviously irrelevant content before LLM analysis"""
        return self.feature_manager._pre_filter_obvious_irrelevant(
            search_results, task_description
        )

    def _keyword_validate_search_results_relevance(
        self, search_results: List[Dict], task_description: str
    ):
        """Fallback keyword-based validation method"""
        return self.feature_manager._keyword_validate_search_results_relevance(
            search_results, task_description
        )

    # =============================================================================
    # UTILITY METHODS - PRESERVE ORIGINAL FUNCTIONALITY
    # =============================================================================

    def _create_data_driven_fallback(
        self, task_description: str, search_results: List[Dict]
    ) -> str:
        """Create intelligent content when LLM is unavailable"""
        return self.feature_manager._create_data_driven_fallback(
            task_description, search_results
        )

    # =============================================================================
    # ADDITIONAL FEATURES AND DIAGNOSTICS
    # =============================================================================

    def get_available_features(self) -> Dict[str, List[str]]:
        """Get list of all available features"""
        return self.feature_manager.get_all_available_features()

    def verify_all_features_working(self) -> bool:
        """Verify that all original features are working"""
        verification = self.feature_manager.verify_feature_completeness()
        return all(verification.values())
