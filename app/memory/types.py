"""
Enhanced Memory Types and Data Models
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class TaskType(Enum):
    """Task categories for learning classification"""

    PLANNING = "planning"
    EXECUTION = "execution"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    REASONING = "reasoning"
    SEARCH = "search"
    INTERACTION = "interaction"


class LearningDomain(Enum):
    """Learning domains for experience categorization"""

    TECHNICAL = "technical"
    STRATEGIC = "strategic"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    USER_INTERACTION = "user_interaction"


@dataclass
class LearningExperience:
    """Represents a learning experience with context and outcomes"""

    task_type: str
    approach_used: str
    context: Dict[str, Any]
    outcome: Dict[str, Any]
    success_score: float
    efficiency_score: float
    quality_score: float
    lessons_learned: List[str]
    optimization_insights: List[str]
    timestamp: float
    domain: str = LearningDomain.TECHNICAL.value
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StrategyPattern:
    """Represents a successful strategy pattern"""

    pattern_id: str
    pattern_type: str
    context_conditions: Dict[str, Any]
    strategy_elements: List[str]
    success_rate: float
    efficiency_gain: float
    quality_improvement: float
    usage_count: int
    last_used: float
    confidence: float = 0.0
    applicability_score: float = 0.0


@dataclass
class OptimizationInsight:
    """Represents an optimization insight learned from experience"""

    insight_id: str
    insight_type: str
    context: Dict[str, Any]
    optimization_target: str
    improvement_method: str
    expected_gain: float
    validation_count: int
    confidence: float
    impact_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MemoryQuery:
    """Query for retrieving relevant memories and patterns"""

    task_type: str
    context: Dict[str, Any]
    domain: Optional[str] = None
    min_confidence: float = 0.5
    max_results: int = 10
    include_patterns: bool = True
    include_insights: bool = True


@dataclass
class LearningMetrics:
    """Metrics for tracking learning progress"""

    total_experiences: int = 0
    successful_patterns: int = 0
    optimization_insights: int = 0
    average_improvement: float = 0.0
    learning_velocity: float = 0.0
    pattern_accuracy: float = 0.0
