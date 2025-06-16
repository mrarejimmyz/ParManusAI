"""
Reasoning Types and Data Models
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ReasoningDepth(Enum):
    """Levels of reasoning depth"""

    SURFACE = "surface"
    ANALYTICAL = "analytical"
    STRATEGIC = "strategic"
    DEEP = "deep"
    EXPERT = "expert"


class LearningMode(Enum):
    """Learning modes for reasoning adaptation"""

    PASSIVE = "passive"
    ACTIVE = "active"
    ADAPTIVE = "adaptive"
    OPTIMIZATION = "optimization"


class AnalysisLayer(Enum):
    """Analysis layers for multi-layered reasoning"""

    SURFACE = "surface"
    ANALYTICAL = "analytical"
    STRATEGIC = "strategic"
    DEEP = "deep"
    EXPERT = "expert"


@dataclass
class ReasoningContext:
    """Context for AI reasoning and decision making"""

    task_complexity: str
    previous_attempts: List[Dict[str, Any]]
    success_patterns: List[Dict[str, Any]]
    failure_patterns: List[Dict[str, Any]]
    optimization_targets: List[str]
    learning_insights: List[str]
    domain: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisResult:
    """Result of reasoning analysis"""

    layer: str
    insights: Dict[str, Any]
    confidence: float
    reasoning: str
    recommendations: List[str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StrategyAdaptation:
    """Strategy adaptation based on learning"""

    original_approach: str
    adapted_approach: str
    reasoning: str
    confidence: float
    expected_improvement: str
    adaptation_type: str = "optimization"
    validation_criteria: Optional[List[str]] = None


@dataclass
class ReasoningQuery:
    """Query for reasoning analysis"""

    task: str
    context: Dict[str, Any]
    desired_depth: ReasoningDepth = ReasoningDepth.EXPERT
    focus_areas: Optional[List[str]] = None
    optimization_goals: Optional[List[str]] = None


@dataclass
class ExecutionResult:
    """Result of strategy execution"""

    success: bool
    performance_metrics: Dict[str, float]
    lessons_learned: List[str]
    optimization_opportunities: List[str]
    quality_metrics: Dict[str, float]
    execution_time: float
    error_details: Optional[Dict[str, Any]] = None
