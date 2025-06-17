"""
Feature Completeness Verification Module
Ensures ALL features from the original monolithic files are preserved
"""

import inspect
from typing import Dict, List, Set, Tuple

from app.logger import logger


class FeatureCompletenessVerifier:
    """
    Verifies that all features from the original monolithic files
    are preserved in the new modular system
    """

    def __init__(self):
        self.original_features = self._get_original_features()
        self.modular_features = self._get_modular_features()

    def _get_original_features(self) -> Dict[str, Set[str]]:
        """Define all features from the original files"""
        return {
            "report_manager_features": {
                # Core methods
                "generate_report_name",
                "create_report_template",
                "should_create_new_report",
                "create_report",
                "create_intelligent_report",
                "create_intelligent_report_from_search_data",
                "create_llm_driven_report",
                # Specialized report methods
                "_create_travel_report",
                "_create_generic_report",
                "_create_kathmandu_report",
                "_create_waterloo_report",
                "_create_intelligent_generic_report",
                # Todo management
                "update_todo_with_next_steps",
                "_update_travel_todo",
                "_update_generic_todo",
                # Search validation
                "_validate_search_results_relevance",
                "_llm_validate_search_results_relevance",
                "_pre_filter_obvious_irrelevant",
                "_keyword_validate_search_results_relevance",
                # Utility methods
                "_create_data_driven_fallback",
            },
            "action_executor_features": {
                # Action execution methods
                "execute_extraction_action",
                "execute_research_action",
                "execute_verification_action",
                "execute_navigation_action",
                "execute_creation_action",
                "execute_default_action",
                # Report completion and status
                "_add_completion_analysis",
                "update_report_completion",
                "get_current_report_status",
                "complete_incomplete_report",
                "_generate_report_completion",
                "_enhance_report_manually",
                # Search query generation
                "_generate_search_query",
                "_llm_generate_search_query",
                "_fallback_search_query",
                # Utility methods
                "_get_user_message",
            },
        }

    def _get_modular_features(self) -> Dict[str, Set[str]]:
        """Get features available in modular system"""
        from app.agent.complete_feature_manager import CompleteFeatureManager

        # Get all public methods from the feature manager
        feature_manager = CompleteFeatureManager()
        public_methods = set()

        for name, method in inspect.getmembers(
            feature_manager, predicate=inspect.ismethod
        ):
            if not name.startswith("__"):  # Exclude special methods
                public_methods.add(name)

        return {"complete_feature_manager": public_methods}

    def verify_completeness(self) -> Dict[str, any]:
        """Verify that all original features are available in modular system"""
        verification_results = {
            "missing_features": [],
            "available_features": [],
            "completeness_percentage": 0,
            "coverage_by_category": {},
            "recommendations": [],
        }

        # Combine all original features
        all_original = set()
        for category, features in self.original_features.items():
            all_original.update(features)

        # Get modular features
        modular_features = set()
        for category, features in self.modular_features.items():
            modular_features.update(features)

        # Find missing features
        missing = all_original - modular_features
        available = all_original & modular_features

        verification_results["missing_features"] = list(missing)
        verification_results["available_features"] = list(available)
        verification_results["completeness_percentage"] = (
            len(available) / len(all_original)
        ) * 100

        # Check coverage by category
        for category, original_features in self.original_features.items():
            category_missing = original_features - modular_features
            category_available = original_features & modular_features

            verification_results["coverage_by_category"][category] = {
                "total": len(original_features),
                "available": len(category_available),
                "missing": len(category_missing),
                "percentage": (len(category_available) / len(original_features)) * 100,
                "missing_features": list(category_missing),
            }

        # Generate recommendations
        if missing:
            verification_results["recommendations"].append(
                f"Implement missing features: {', '.join(missing)}"
            )

        return verification_results

    def print_verification_report(self) -> None:
        """Print a detailed verification report"""
        results = self.verify_completeness()

        print("\\n" + "=" * 80)
        print("FEATURE COMPLETENESS VERIFICATION REPORT")
        print("=" * 80)

        print(f"\\n📊 OVERALL COMPLETENESS: {results['completeness_percentage']:.1f}%")
        print(f"✅ Available Features: {len(results['available_features'])}")
        print(f"❌ Missing Features: {len(results['missing_features'])}")

        print("\\n📋 COVERAGE BY CATEGORY:")
        for category, stats in results["coverage_by_category"].items():
            print(f"\\n{category}:")
            print(
                f"  ✅ {stats['available']}/{stats['total']} ({stats['percentage']:.1f}%)"
            )

            if stats["missing_features"]:
                print(f"  ❌ Missing: {', '.join(stats['missing_features'])}")

        if results["missing_features"]:
            print(f"\\n🚨 MISSING FEATURES:")
            for feature in results["missing_features"]:
                print(f"  - {feature}")

        if results["recommendations"]:
            print(f"\\n💡 RECOMMENDATIONS:")
            for rec in results["recommendations"]:
                print(f"  - {rec}")

        print("\\n" + "=" * 80)

    def get_feature_mapping(self) -> Dict[str, str]:
        """Get mapping of original features to modular implementations"""
        return {
            # Report creation
            "generate_report_name": "complete_feature_manager.generate_report_name",
            "create_report": "complete_feature_manager.create_report",
            "create_intelligent_report": "complete_feature_manager.create_intelligent_report",
            # Specialized reports
            "_create_travel_report": "report_template_manager._create_travel_report",
            "_create_kathmandu_report": "report_template_manager._create_kathmandu_report",
            "_create_waterloo_report": "report_template_manager._create_waterloo_report",
            # Todo management
            "update_todo_with_next_steps": "enhanced_todo_manager.update_todo_with_next_steps",
            "_update_travel_todo": "enhanced_todo_manager._update_travel_todo",
            # Search validation
            "_validate_search_results_relevance": "search_validator.validate_results",
            "_pre_filter_obvious_irrelevant": "search_result_prefilter.pre_filter_results",
            # Query generation
            "_generate_search_query": "search_query_generator.generate_search_query",
            "_llm_generate_search_query": "search_query_generator._llm_generate_search_query",
            # LLM analysis
            "create_llm_driven_report": "data_driven_report_generator.create_llm_driven_report",
        }

    def verify_modular_architecture(self) -> Dict[str, bool]:
        """Verify that the modular architecture is properly implemented"""
        checks = {}

        try:
            # Test imports
            from app.agent.complete_feature_manager import CompleteFeatureManager
            from app.agent.enhanced_todo_manager import EnhancedTodoManager
            from app.agent.llm_response_parser import LLMResponseParser
            from app.agent.report_name_generator import ReportNameGenerator
            from app.agent.search_result_prefilter import SearchResultPreFilter

            checks["imports_working"] = True
        except ImportError as e:
            checks["imports_working"] = False
            logger.error(f"Import error: {e}")

        try:
            # Test instantiation
            feature_manager = CompleteFeatureManager()
            checks["instantiation_working"] = True
        except Exception as e:
            checks["instantiation_working"] = False
            logger.error(f"Instantiation error: {e}")

        try:
            # Test feature verification
            feature_manager = CompleteFeatureManager()
            verification = feature_manager.verify_feature_completeness()
            checks["feature_verification_working"] = True
        except Exception as e:
            checks["feature_verification_working"] = False
            logger.error(f"Feature verification error: {e}")

        return checks


def run_complete_verification():
    """Run complete verification and print results"""
    verifier = FeatureCompletenessVerifier()

    print("🔍 Running complete feature verification...")

    # Architecture verification
    arch_results = verifier.verify_modular_architecture()
    print("\\n🏗️ ARCHITECTURE VERIFICATION:")
    for check, result in arch_results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}: {result}")

    # Feature completeness verification
    verifier.print_verification_report()

    # Feature mapping
    mapping = verifier.get_feature_mapping()
    print("\\n🗺️ KEY FEATURE MAPPINGS:")
    for original, modular in list(mapping.items())[:10]:  # Show first 10
        print(f"  {original} → {modular}")

    return verifier.verify_completeness()


if __name__ == "__main__":
    run_complete_verification()
