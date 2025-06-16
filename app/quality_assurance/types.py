"""
Quality Assurance Types and Data Structures
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class ValidationLevel(Enum):
    """Different levels of validation rigor"""

    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class QualityMetric(Enum):
    """Quality metrics for task completion assessment"""

    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    DEPTH = "depth"
    CLARITY = "clarity"
    ACTIONABILITY = "actionability"


@dataclass
class ValidationResult:
    """Result of a validation check"""

    passed: bool
    score: float  # 0.0 to 1.0
    details: str
    suggestions: List[str]
    critical_issues: List[str]


@dataclass
class QualityAssessment:
    """Comprehensive quality assessment of task completion"""

    overall_score: float
    metric_scores: Dict[QualityMetric, float]
    validation_results: Dict[str, ValidationResult]
    completion_status: str
    recommendations: List[str]
    critical_issues: List[str]
