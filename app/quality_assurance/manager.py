"""
Quality Assurance Manager
Main interface for quality assurance system coordination.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from .metrics import QualityMetricsCalculator
from .types import QualityAssessment, ValidationLevel
from .validators import SuccessValidator

logger = logging.getLogger(__name__)


class QualityAssuranceManager:
    """
    Manages overall quality assurance for the ParManusAI system
    """

    def __init__(self, llm=None):
        self.validator = SuccessValidator(llm)
        self.metrics_calculator = QualityMetricsCalculator()
        self.quality_standards = self._initialize_quality_standards()

    def _initialize_quality_standards(self) -> Dict[str, float]:
        """Initialize quality standards for different task types"""
        return {
            "website_analysis": 0.75,
            "research_task": 0.80,
            "content_generation": 0.70,
            "data_analysis": 0.85,
            "general_task": 0.70,
        }

    async def assess_task_quality(
        self,
        task_goal: str,
        execution_results: List[Dict],
        task_type: str = "general_task",
    ) -> Tuple[bool, QualityAssessment]:
        """Assess if task meets quality standards"""
        # Determine validation level based on task type
        validation_level = ValidationLevel.STANDARD
        if task_type in ["research_task", "data_analysis"]:
            validation_level = ValidationLevel.COMPREHENSIVE

        # Run validation
        validation_results = await self.validator.validate_task_completion(
            task_goal, execution_results, validation_level
        )

        # Calculate quality metrics
        metric_scores = self.metrics_calculator.calculate_quality_metrics(
            task_goal, execution_results, validation_results
        )

        # Calculate overall score
        overall_score = self.metrics_calculator.calculate_overall_score(metric_scores)

        # Determine completion status
        completion_status = self.metrics_calculator.determine_completion_status(
            overall_score
        )

        # Generate recommendations
        recommendations = self.metrics_calculator.generate_recommendations(
            metric_scores, validation_results
        )

        # Identify critical issues
        critical_issues = self.metrics_calculator.identify_critical_issues(
            overall_score, validation_results
        )

        # Create assessment
        assessment = QualityAssessment(
            overall_score=overall_score,
            metric_scores=metric_scores,
            validation_results=validation_results,
            completion_status=completion_status,
            recommendations=recommendations,
            critical_issues=critical_issues,
        )

        # Record validation
        self.validator.record_validation(
            task_goal,
            overall_score,
            completion_status,
            len(critical_issues),
            len(recommendations),
        )

        # Check against quality standards
        required_score = self.quality_standards.get(task_type, 0.70)
        meets_standards = overall_score >= required_score

        logger.info(
            f"Quality assessment: {overall_score:.2f} (required: {required_score:.2f})"
        )

        return meets_standards, assessment

    def get_quality_report(self) -> Dict[str, Any]:
        """Generate a quality report based on validation history"""
        if not self.validator.validation_history:
            return {"message": "No validation history available"}

        history = self.validator.validation_history
        recent_validations = history[-10:]  # Last 10 validations

        avg_score = sum(v["overall_score"] for v in recent_validations) / len(
            recent_validations
        )

        status_distribution = {}
        for validation in recent_validations:
            status = validation["completion_status"]
            status_distribution[status] = status_distribution.get(status, 0) + 1

        return {
            "total_validations": len(history),
            "recent_average_score": avg_score,
            "status_distribution": status_distribution,
            "quality_trend": (
                "improving"
                if len(history) > 5
                and sum(v["overall_score"] for v in history[-5:])
                > sum(v["overall_score"] for v in history[-10:-5])
                else "stable"
            ),
        }

    def update_quality_standards(self, task_type: str, standard: float) -> None:
        """Update quality standard for a specific task type"""
        if 0.0 <= standard <= 1.0:
            self.quality_standards[task_type] = standard
            logger.info(f"Updated quality standard for {task_type}: {standard}")
        else:
            logger.warning(
                f"Invalid quality standard: {standard}. Must be between 0.0 and 1.0"
            )

    def get_quality_standards(self) -> Dict[str, float]:
        """Get current quality standards"""
        return self.quality_standards.copy()
