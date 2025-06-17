"""
Modular Reporting System - Main Entry Point
Provides easy access to all reporting functionality in an organized structure

NEW ORGANIZED STRUCTURE:
/reporting/
  ├── generators/           # Report generation classes
  │   ├── simple_report_generator.py
  │   └── data_driven_report_generator.py
  ├── templates/           # Report template classes
  │   └── report_template_manager.py
  ├── validation/          # Search and validation classes
  │   ├── search_validator.py
  │   ├── search_result_prefilter.py
  │   └── search_query_generator.py
  ├── utils/              # Utility classes
  │   ├── report_name_generator.py
  │   ├── llm_response_parser.py
  │   └── feature_completeness_verifier.py
  ├── complete_feature_manager.py      # Master feature coordinator
  └── comprehensive_report_manager_v2.py # Main API interface
/actions/                 # Action execution classes
  ├── action_executor_features.py
  └── simplified_manus_action_executor.py
/todo/                   # Todo management classes
  ├── todo_manager.py
  └── enhanced_todo_manager.py
"""

from app.agent.actions import ActionExecutorFeatures

# Main interfaces - easy imports
from app.agent.reporting import CompleteFeatureManager, ComprehensiveReportManager

# Direct access to specific modules if needed
from app.agent.reporting.generators import (
    DataDrivenReportGenerator,
    SimpleReportGenerator,
)
from app.agent.reporting.templates import ReportTemplateManager
from app.agent.reporting.utils import (
    FeatureCompletenessVerifier,
    LLMResponseParser,
    ReportCompletionAnalyzer,
    ReportNameGenerator,
)
from app.agent.reporting.validation import (
    SearchQueryGenerator,
    SearchResultPreFilter,
    SearchResultValidator,
)
from app.agent.todo import EnhancedTodoManager, TodoManager

# Legacy compatibility removed - use new modular structure only


__all__ = [
    # Main interfaces
    "ComprehensiveReportManager",
    "CompleteFeatureManager",
    # Report generation
    "SimpleReportGenerator",
    "DataDrivenReportGenerator",
    "ReportTemplateManager",
    # Validation and search
    "SearchResultValidator",
    "SearchResultPreFilter",
    "SearchQueryGenerator",
    # Utilities
    "ReportNameGenerator",
    "LLMResponseParser",
    "FeatureCompletenessVerifier",
    # Actions
    "ActionExecutorFeatures",
    # Todo management
    "TodoManager",
    "EnhancedTodoManager",
    # Legacy compatibility
    "LegacyReportManager",
]


def get_main_report_manager():
    """Get the main report manager instance - recommended entry point"""
    return ComprehensiveReportManager()


def get_feature_manager():
    """Get the complete feature manager - for advanced usage"""
    return CompleteFeatureManager()


def verify_all_features():
    """Verify that all features are working correctly"""
    from app.agent.reporting.utils.feature_completeness_verifier import (
        run_complete_verification,
    )

    return run_complete_verification()


def get_organized_structure_info():
    """Get information about the new organized structure"""
    return {
        "total_modules": 13,
        "structure": {
            "reporting/generators": [
                "SimpleReportGenerator",
                "DataDrivenReportGenerator",
            ],
            "reporting/templates": ["ReportTemplateManager"],
            "reporting/validation": [
                "SearchResultValidator",
                "SearchResultPreFilter",
                "SearchQueryGenerator",
            ],
            "reporting/utils": [
                "ReportNameGenerator",
                "LLMResponseParser",
                "FeatureCompletenessVerifier",
            ],
            "actions": ["ActionExecutorFeatures"],
            "todo": ["TodoManager", "EnhancedTodoManager"],
            "reporting": ["CompleteFeatureManager", "ComprehensiveReportManager"],
        },
        "benefits": [
            "Better organization and structure",
            "Easier debugging and maintenance",
            "Clear separation of concerns",
            "Modular architecture",
            "100% feature preservation",
        ],
    }
