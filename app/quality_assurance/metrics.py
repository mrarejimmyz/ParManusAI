"""
Quality Metrics Calculator
Handles calculation and management of quality metrics.
"""

import logging
from typing import Any, Dict, List

from .types import QualityMetric, ValidationResult

logger = logging.getLogger(__name__)


class QualityMetricsCalculator:
    """Calculates quality metrics based on validation results"""

    def __init__(self):
        self.metric_weights = {
            QualityMetric.COMPLETENESS: 0.25,
            QualityMetric.ACCURACY: 0.20,
            QualityMetric.RELEVANCE: 0.20,
            QualityMetric.DEPTH: 0.15,
            QualityMetric.CLARITY: 0.10,
            QualityMetric.ACTIONABILITY: 0.10,
        }

    def calculate_quality_metrics(
        self,
        task_goal: str,
        execution_results: List[Dict],
        validation_results: Dict[str, ValidationResult],
    ) -> Dict[QualityMetric, float]:
        """
        Calculate quality metrics based on validation results
        """
        metrics = {}

        # Map validation results to quality metrics
        if "basic_completion" in validation_results:
            metrics[QualityMetric.COMPLETENESS] = validation_results[
                "basic_completion"
            ].score

        if "content_quality" in validation_results:
            metrics[QualityMetric.CLARITY] = validation_results["content_quality"].score

        if "goal_alignment" in validation_results:
            metrics[QualityMetric.RELEVANCE] = validation_results[
                "goal_alignment"
            ].score
            metrics[QualityMetric.ACCURACY] = validation_results["goal_alignment"].score

        if "depth_analysis" in validation_results:
            metrics[QualityMetric.DEPTH] = validation_results["depth_analysis"].score

        if "actionability" in validation_results:
            metrics[QualityMetric.ACTIONABILITY] = validation_results[
                "actionability"
            ].score

        # Fill in missing metrics with default values
        for metric in QualityMetric:
            if metric not in metrics:
                metrics[metric] = 0.5  # Neutral score for unmeasured metrics

        return metrics

    def calculate_overall_score(
        self, metric_scores: Dict[QualityMetric, float]
    ) -> float:
        """Calculate weighted overall score from metric scores"""
        if not metric_scores:
            return 0.0

        weighted_sum = sum(
            score * self.metric_weights.get(metric, 1.0 / len(QualityMetric))
            for metric, score in metric_scores.items()
        )

        total_weight = sum(
            self.metric_weights.get(metric, 1.0 / len(QualityMetric))
            for metric in metric_scores.keys()
        )

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def determine_completion_status(self, overall_score: float) -> str:
        """Determine overall completion status based on score"""
        if overall_score >= 0.8:
            return "excellent"
        elif overall_score >= 0.7:
            return "good"
        elif overall_score >= 0.6:
            return "satisfactory"
        elif overall_score >= 0.4:
            return "needs_improvement"
        else:
            return "poor"

    def generate_recommendations(
        self,
        metric_scores: Dict[QualityMetric, float],
        validation_results: Dict[str, ValidationResult],
    ) -> List[str]:
        """Generate improvement recommendations based on assessment"""
        recommendations = []

        # Collect suggestions from all validation results
        for validation_result in validation_results.values():
            recommendations.extend(validation_result.suggestions)

        # Add metric-specific recommendations
        for metric, score in metric_scores.items():
            if score < 0.6:
                if metric == QualityMetric.COMPLETENESS:
                    recommendations.append("Ensure all task components are addressed")
                elif metric == QualityMetric.DEPTH:
                    recommendations.append(
                        "Provide more detailed analysis and insights"
                    )
                elif metric == QualityMetric.ACTIONABILITY:
                    recommendations.append(
                        "Include specific recommendations and next steps"
                    )
                elif metric == QualityMetric.CLARITY:
                    recommendations.append("Improve content clarity and organization")
                elif metric == QualityMetric.RELEVANCE:
                    recommendations.append("Better align results with task goals")
                elif metric == QualityMetric.ACCURACY:
                    recommendations.append("Verify and improve accuracy of information")

        # Remove duplicates and limit to top recommendations
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:5]

    def identify_critical_issues(
        self, overall_score: float, validation_results: Dict[str, ValidationResult]
    ) -> List[str]:
        """Identify critical issues that must be addressed"""
        critical_issues = []

        # Collect critical issues from validation results
        for validation_result in validation_results.values():
            critical_issues.extend(validation_result.critical_issues)

        # Add overall critical issues
        if overall_score < 0.4:
            critical_issues.append("Overall task completion quality is poor")

        # Remove duplicates
        return list(dict.fromkeys(critical_issues))
