"""
Modern Enhanced Memory System
LLM-driven memory and learning with intelligent pattern recognition
"""

import json
import time
from collections import defaultdict
from typing import Dict, List, Optional

from app.logger import logger
from app.memory.analyzer import LLMExperienceAnalyzer
from app.memory.optimizer import LLMStrategyOptimizer
from app.memory.pattern_recognizer import LLMPatternRecognizer
from app.memory.types import (
    LearningDomain,
    LearningExperience,
    LearningMetrics,
    MemoryQuery,
    OptimizationInsight,
    StrategyPattern,
    TaskType,
)


class ModernEnhancedMemorySystem:
    """
    Modern enhanced memory system with LLM-driven learning and optimization
    Replaces static analysis with intelligent reasoning
    """

    def __init__(self, llm_client=None):
        """Initialize with optional LLM client for intelligent analysis"""
        self.llm = llm_client

        # Data storage
        self.learning_experiences: List[LearningExperience] = []
        self.strategy_patterns: Dict[str, StrategyPattern] = {}
        self.optimization_insights: Dict[str, OptimizationInsight] = {}
        self.performance_trends: Dict[str, List[float]] = defaultdict(list)

        # Metrics tracking
        self.learning_metrics = LearningMetrics()

        # LLM-driven components
        self.experience_analyzer = LLMExperienceAnalyzer(llm_client)
        self.pattern_recognizer = LLMPatternRecognizer(llm_client)
        self.strategy_optimizer = LLMStrategyOptimizer(llm_client)

        logger.info(
            "🧠 Initialized modern enhanced memory system with LLM-driven reasoning"
        )

    async def record_learning_experience(
        self, task_type: str, approach_used: str, context: Dict, outcome: Dict
    ) -> str:
        """Record and analyze learning experience using LLM reasoning"""
        logger.info(f"📝 Recording learning experience for: {task_type}")

        # Use LLM-driven analysis
        experience = await self.experience_analyzer.analyze_experience(
            task_type, approach_used, context, outcome
        )

        # Store experience
        self.learning_experiences.append(experience)
        experience_id = f"experience_{len(self.learning_experiences)}"

        # Update metrics
        self.learning_metrics.total_experiences += 1
        self._update_performance_trends(experience)

        # Analyze for new patterns
        await self._update_patterns()

        # Extract optimization insights
        await self._update_optimization_insights(experience)

        logger.info(
            f"✅ Recorded experience {experience_id} with success score: {experience.success_score:.2f}"
        )
        return experience_id

    async def get_optimized_strategy(self, task_type: str, context: Dict) -> Dict:
        """Get optimized strategy using LLM-driven analysis"""
        logger.info(f"🎯 Generating optimized strategy for: {task_type}")

        # Gather relevant data
        relevant_experiences = self._find_relevant_experiences(task_type, context)
        applicable_patterns = await self._find_applicable_patterns(task_type, context)
        relevant_insights = self._get_relevant_insights(task_type, context)

        # Use LLM to optimize strategy
        strategy = await self.strategy_optimizer.optimize_strategy(
            task_type,
            context,
            relevant_experiences,
            applicable_patterns,
            relevant_insights,
        )

        logger.info(
            f"✅ Generated strategy with confidence: {strategy.get('confidence_score', 0.5):.2f}"
        )
        return strategy

    async def learn_from_feedback(self, experience_id: str, feedback: Dict) -> None:
        """Learn from feedback and update experience"""
        try:
            experience_index = int(experience_id.split("_")[1]) - 1
            if 0 <= experience_index < len(self.learning_experiences):
                experience = self.learning_experiences[experience_index]

                # Update experience with feedback
                experience.outcome.update(feedback)

                # Re-analyze with updated outcome
                updated_experience = await self.experience_analyzer.analyze_experience(
                    experience.task_type,
                    experience.approach_used,
                    experience.context,
                    experience.outcome,
                )

                # Update the stored experience
                self.learning_experiences[experience_index] = updated_experience

                # Update patterns and insights
                await self._update_patterns()

                logger.info(f"✅ Updated experience {experience_id} with feedback")
            else:
                logger.warning(f"Experience {experience_id} not found")

        except Exception as e:
            logger.error(f"Failed to process feedback for {experience_id}: {e}")

    async def get_learning_insights(self) -> Dict:
        """Get comprehensive learning insights using LLM analysis"""
        logger.info("📊 Generating learning insights")

        # Use LLM-driven analysis for recommendations
        recommendations = (
            await self.strategy_optimizer.generate_learning_recommendations(
                self.learning_experiences, list(self.strategy_patterns.values())
            )
        )

        # Add performance trends
        trends = self._analyze_performance_trends()

        insights = {
            "performance_trends": trends,
            "learning_recommendations": recommendations,
            "successful_patterns": self._get_top_patterns(),
            "optimization_opportunities": self._identify_optimization_opportunities(),
            "learning_metrics": {
                "total_experiences": self.learning_metrics.total_experiences,
                "successful_patterns": len(self.strategy_patterns),
                "optimization_insights": len(self.optimization_insights),
                "average_improvement": self._calculate_average_improvement(),
            },
        }

        logger.info(
            f"✅ Generated insights with {len(insights['successful_patterns'])} patterns"
        )
        return insights

    async def query_memory(self, query: MemoryQuery) -> Dict:
        """Query memory using intelligent matching"""
        logger.info(f"🔍 Querying memory for: {query.task_type}")

        results = {"experiences": [], "patterns": [], "insights": []}

        # Find relevant experiences
        if query.include_patterns:
            relevant_experiences = self._find_relevant_experiences(
                query.task_type, query.context
            )
            results["experiences"] = [
                self._experience_to_dict(exp)
                for exp in relevant_experiences[: query.max_results]
            ]

        # Find applicable patterns
        if query.include_patterns:
            applicable_patterns = await self._find_applicable_patterns(
                query.task_type, query.context
            )
            results["patterns"] = [
                self._pattern_to_dict(pattern)
                for pattern in applicable_patterns[: query.max_results]
            ]

        # Find relevant insights
        if query.include_insights:
            relevant_insights = self._get_relevant_insights(
                query.task_type, query.context
            )
            results["insights"] = [
                self._insight_to_dict(insight)
                for insight in relevant_insights[: query.max_results]
            ]

        return results

    async def _update_patterns(self):
        """Update patterns using LLM-driven analysis"""
        if len(self.learning_experiences) < 3:
            return  # Need minimum experiences for pattern analysis

        # Analyze recent experiences for patterns
        recent_experiences = self.learning_experiences[-20:]  # Last 20 experiences
        new_patterns = await self.pattern_recognizer.analyze_for_patterns(
            recent_experiences
        )

        # Update pattern storage
        for pattern in new_patterns:
            if pattern.pattern_id in self.strategy_patterns:
                # Update existing pattern
                existing = self.strategy_patterns[pattern.pattern_id]
                existing.usage_count += 1
                existing.last_used = pattern.last_used
                # Update metrics based on new data
                existing.success_rate = (
                    existing.success_rate + pattern.success_rate
                ) / 2
            else:
                # Store new pattern
                self.strategy_patterns[pattern.pattern_id] = pattern
                self.learning_metrics.successful_patterns += 1

    async def _update_optimization_insights(self, experience: LearningExperience):
        """Extract and update optimization insights from experience"""
        if not experience.optimization_insights:
            return

        for insight_text in experience.optimization_insights:
            # Create optimization insight
            insight_id = f"insight_{len(self.optimization_insights) + 1}"

            insight = OptimizationInsight(
                insight_id=insight_id,
                insight_type=experience.domain,
                context=experience.context,
                optimization_target="performance",
                improvement_method=insight_text,
                expected_gain=experience.success_score - 0.5,  # Relative to baseline
                validation_count=1,
                confidence=experience.success_score,
            )

            self.optimization_insights[insight_id] = insight
            self.learning_metrics.optimization_insights += 1

    def _find_relevant_experiences(
        self, task_type: str, context: Dict
    ) -> List[LearningExperience]:
        """Find experiences relevant to current task"""
        relevant = []

        for exp in self.learning_experiences:
            # Same task type gets highest priority
            if exp.task_type == task_type:
                relevant.append(exp)
            # Similar context also relevant
            elif self._context_similarity(exp.context, context) > 0.6:
                relevant.append(exp)

        # Sort by success score and recency
        relevant.sort(key=lambda x: (x.success_score, x.timestamp), reverse=True)
        return relevant[:10]

    async def _find_applicable_patterns(
        self, task_type: str, context: Dict
    ) -> List[StrategyPattern]:
        """Find patterns applicable to current context"""
        patterns = list(self.strategy_patterns.values())

        return await self.pattern_recognizer.find_applicable_patterns(
            task_type, context, patterns
        )

    def _get_relevant_insights(
        self, task_type: str, context: Dict
    ) -> List[OptimizationInsight]:
        """Get optimization insights relevant to current task"""
        relevant = []

        for insight in self.optimization_insights.values():
            if (
                task_type.lower() in insight.insight_type.lower()
                or self._context_similarity(insight.context, context) > 0.6
            ):
                relevant.append(insight)

        # Sort by confidence and expected gain
        relevant.sort(key=lambda x: (x.confidence, x.expected_gain), reverse=True)
        return relevant[:5]

    def _context_similarity(self, context1: Dict, context2: Dict) -> float:
        """Calculate similarity between contexts"""
        if not context1 or not context2:
            return 0.0

        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0

        matches = 0
        for key in common_keys:
            if str(context1[key]).lower() == str(context2[key]).lower():
                matches += 1

        return matches / len(common_keys)

    def _update_performance_trends(self, experience: LearningExperience):
        """Update performance trend tracking"""
        self.performance_trends["success"].append(experience.success_score)
        self.performance_trends["efficiency"].append(experience.efficiency_score)
        self.performance_trends["quality"].append(experience.quality_score)

        # Keep only last 50 for trend analysis
        for key in self.performance_trends:
            if len(self.performance_trends[key]) > 50:
                self.performance_trends[key] = self.performance_trends[key][-50:]

    def _analyze_performance_trends(self) -> Dict:
        """Analyze performance trends"""
        trends = {}

        for metric, values in self.performance_trends.items():
            if len(values) >= 3:
                recent_avg = sum(values[-5:]) / min(5, len(values))
                overall_avg = sum(values) / len(values)

                if recent_avg > overall_avg + 0.1:
                    trend = "improving"
                elif recent_avg < overall_avg - 0.1:
                    trend = "declining"
                else:
                    trend = "stable"

                trends[metric] = {
                    "trend": trend,
                    "recent_average": recent_avg,
                    "overall_average": overall_avg,
                    "data_points": len(values),
                }

        return trends

    def _get_top_patterns(self) -> List[Dict]:
        """Get top performing patterns"""
        patterns = list(self.strategy_patterns.values())
        patterns.sort(key=lambda x: (x.success_rate, x.usage_count), reverse=True)

        return [self._pattern_to_dict(pattern) for pattern in patterns[:5]]

    def _identify_optimization_opportunities(self) -> List[Dict]:
        """Identify optimization opportunities"""
        opportunities = []

        # Analyze insights for high-impact opportunities
        insights = list(self.optimization_insights.values())
        insights.sort(key=lambda x: x.expected_gain, reverse=True)

        for insight in insights[:3]:
            opportunities.append(
                {
                    "target": insight.optimization_target,
                    "method": insight.improvement_method,
                    "expected_gain": insight.expected_gain,
                    "confidence": insight.confidence,
                }
            )

        return opportunities

    def _calculate_average_improvement(self) -> float:
        """Calculate average improvement over time"""
        if len(self.learning_experiences) < 5:
            return 0.0

        early_scores = [exp.success_score for exp in self.learning_experiences[:5]]
        recent_scores = [exp.success_score for exp in self.learning_experiences[-5:]]

        early_avg = sum(early_scores) / len(early_scores)
        recent_avg = sum(recent_scores) / len(recent_scores)

        return recent_avg - early_avg

    def _experience_to_dict(self, experience: LearningExperience) -> Dict:
        """Convert experience to dictionary"""
        return {
            "task_type": experience.task_type,
            "approach_used": experience.approach_used,
            "success_score": experience.success_score,
            "efficiency_score": experience.efficiency_score,
            "quality_score": experience.quality_score,
            "lessons_learned": experience.lessons_learned,
            "domain": experience.domain,
            "timestamp": experience.timestamp,
        }

    def _pattern_to_dict(self, pattern: StrategyPattern) -> Dict:
        """Convert pattern to dictionary"""
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type,
            "strategy_elements": pattern.strategy_elements,
            "success_rate": pattern.success_rate,
            "usage_count": pattern.usage_count,
            "confidence": pattern.confidence,
        }

    def _insight_to_dict(self, insight: OptimizationInsight) -> Dict:
        """Convert insight to dictionary"""
        return {
            "insight_id": insight.insight_id,
            "insight_type": insight.insight_type,
            "optimization_target": insight.optimization_target,
            "improvement_method": insight.improvement_method,
            "expected_gain": insight.expected_gain,
            "confidence": insight.confidence,
        }


# Backward compatibility wrapper
class EnhancedMemorySystem:
    """Backward compatibility wrapper for existing code"""

    def __init__(self, llm_client=None):
        # Initialize the modern implementation
        self.modern_memory = ModernEnhancedMemorySystem(llm_client)

    async def record_learning_experience(
        self, task_type: str, approach_used: str, context: Dict, outcome: Dict
    ) -> str:
        """Backward compatible method"""
        return await self.modern_memory.record_learning_experience(
            task_type, approach_used, context, outcome
        )

    async def get_optimized_strategy(self, task_type: str, context: Dict) -> Dict:
        """Backward compatible method"""
        return await self.modern_memory.get_optimized_strategy(task_type, context)

    async def learn_from_feedback(self, experience_id: str, feedback: Dict) -> None:
        """Backward compatible method"""
        return await self.modern_memory.learn_from_feedback(experience_id, feedback)

    async def get_learning_insights(self) -> Dict:
        """Backward compatible method"""
        return await self.modern_memory.get_learning_insights()
