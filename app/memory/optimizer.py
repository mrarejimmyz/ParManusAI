"""
LLM-Driven Strategy Optimizer
Replaces static optimization logic with intelligent recommendations
"""

import json
from typing import Dict, List, Optional

from app.logger import logger
from app.memory.types import (
    LearningExperience,
    MemoryQuery,
    OptimizationInsight,
    StrategyPattern,
)


class LLMStrategyOptimizer:
    """Optimizes strategies using LLM-driven analysis and recommendations"""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def optimize_strategy(
        self,
        task_type: str,
        context: Dict,
        experiences: List[LearningExperience],
        patterns: List[StrategyPattern],
        insights: List[OptimizationInsight],
    ) -> Dict:
        """Generate optimized strategy using LLM reasoning"""
        logger.info(f"🎯 Optimizing strategy for task: {task_type}")

        if self.llm:
            return await self._llm_strategy_optimization(
                task_type, context, experiences, patterns, insights
            )
        else:
            return await self._fallback_strategy_optimization(
                task_type, context, experiences, patterns
            )

    async def _llm_strategy_optimization(
        self,
        task_type: str,
        context: Dict,
        experiences: List[LearningExperience],
        patterns: List[StrategyPattern],
        insights: List[OptimizationInsight],
    ) -> Dict:
        """Use LLM to create optimized strategy"""

        # Prepare relevant data for LLM analysis
        relevant_experiences = self._filter_relevant_experiences(
            experiences, task_type, context
        )
        applicable_patterns = self._filter_applicable_patterns(
            patterns, task_type, context
        )
        relevant_insights = self._filter_relevant_insights(insights, task_type, context)

        optimization_prompt = f"""
        Create an optimized strategy for this task based on learning history:

        CURRENT TASK:
        Type: {task_type}
        Context: {context}

        RELEVANT EXPERIENCE DATA:
        """

        # Add top relevant experiences
        for i, exp in enumerate(relevant_experiences[:3]):
            optimization_prompt += f"""
        Experience {i+1}:
        - Approach: {exp.approach_used}
        - Success: {exp.success_score:.2f}
        - Efficiency: {exp.efficiency_score:.2f}
        - Quality: {exp.quality_score:.2f}
        - Lessons: {exp.lessons_learned[:2]}
        """

        # Add applicable patterns
        if applicable_patterns:
            optimization_prompt += "\n\nAPPLICABLE PATTERNS:\n"
            for i, pattern in enumerate(applicable_patterns[:3]):
                optimization_prompt += f"""
        Pattern {i+1}:
        - Elements: {pattern.strategy_elements}
        - Success Rate: {pattern.success_rate:.2f}
        - Efficiency Gain: {pattern.efficiency_gain:.2f}
        """

        # Add optimization insights
        if relevant_insights:
            optimization_prompt += "\n\nOPTIMIZATION INSIGHTS:\n"
            for i, insight in enumerate(relevant_insights[:3]):
                optimization_prompt += f"""
        Insight {i+1}:
        - Target: {insight.optimization_target}
        - Method: {insight.improvement_method}
        - Expected Gain: {insight.expected_gain:.2f}
        """

        optimization_prompt += """

        Based on this learning history, create an optimized strategy that:
        1. Incorporates successful patterns from past experiences
        2. Applies relevant optimization insights
        3. Adapts to the current context
        4. Maximizes success, efficiency, and quality

        Return JSON strategy:
        {
            "base_approach": "primary strategy to use",
            "optimization_elements": ["element1", "element2"],
            "quality_enhancements": ["enhancement1", "enhancement2"],
            "efficiency_improvements": ["improvement1", "improvement2"],
            "learning_adaptations": ["adaptation1", "adaptation2"],
            "confidence_score": 0.0-1.0,
            "expected_improvements": {
                "success": 0.0-1.0,
                "efficiency": 0.0-1.0,
                "quality": 0.0-1.0
            },
            "reasoning": "explanation of strategy choices",
            "risk_mitigation": ["risk1", "risk2"],
            "success_metrics": ["metric1", "metric2"]
        }
        """

        try:
            response = await self.llm.generate_response(optimization_prompt)
            strategy = json.loads(response)

            # Validate and enhance strategy
            strategy = self._validate_strategy(strategy)

            logger.info(
                f"✅ Generated optimized strategy with confidence: {strategy.get('confidence_score', 0.5):.2f}"
            )
            return strategy

        except Exception as e:
            logger.warning(f"LLM strategy optimization failed: {e}")
            return await self._fallback_strategy_optimization(
                task_type, context, experiences, patterns
            )

    async def generate_learning_recommendations(
        self, experiences: List[LearningExperience], patterns: List[StrategyPattern]
    ) -> Dict:
        """Generate learning and improvement recommendations"""
        if self.llm:
            return await self._llm_learning_recommendations(experiences, patterns)
        else:
            return await self._fallback_learning_recommendations(experiences, patterns)

    async def _llm_learning_recommendations(
        self, experiences: List[LearningExperience], patterns: List[StrategyPattern]
    ) -> Dict:
        """Use LLM to generate learning recommendations"""

        # Analyze performance trends
        success_trend = [exp.success_score for exp in experiences[-10:]]
        efficiency_trend = [exp.efficiency_score for exp in experiences[-10:]]
        quality_trend = [exp.quality_score for exp in experiences[-10:]]

        recommendation_prompt = f"""
        Analyze this learning history and provide improvement recommendations:

        PERFORMANCE TRENDS (last 10 experiences):
        Success scores: {success_trend}
        Efficiency scores: {efficiency_trend}
        Quality scores: {quality_trend}

        SUCCESSFUL PATTERNS:
        """

        for i, pattern in enumerate(patterns[:5]):
            recommendation_prompt += f"""
        Pattern {i+1}:
        - Success Rate: {pattern.success_rate:.2f}
        - Usage Count: {pattern.usage_count}
        - Elements: {pattern.strategy_elements[:3]}
        """

        recommendation_prompt += """

        LEARNING INSIGHTS:
        """

        all_lessons = []
        for exp in experiences[-5:]:
            all_lessons.extend(exp.lessons_learned)

        # Get unique lessons
        unique_lessons = list(set(all_lessons))[:10]

        for lesson in unique_lessons:
            recommendation_prompt += f"- {lesson}\n"

        recommendation_prompt += """

        Based on this analysis, provide comprehensive recommendations:

        Return JSON:
        {
            "performance_analysis": {
                "success_trend": "improving|stable|declining",
                "efficiency_trend": "improving|stable|declining",
                "quality_trend": "improving|stable|declining",
                "overall_assessment": "assessment summary"
            },
            "improvement_recommendations": [
                {
                    "area": "success|efficiency|quality|strategy",
                    "recommendation": "specific recommendation",
                    "priority": "high|medium|low",
                    "expected_impact": 0.0-1.0,
                    "implementation": "how to implement"
                }
            ],
            "learning_opportunities": [
                "opportunity 1", "opportunity 2"
            ],
            "pattern_insights": [
                "insight 1", "insight 2"
            ],
            "strategy_adaptations": [
                "adaptation 1", "adaptation 2"
            ],
            "focus_areas": [
                "area 1", "area 2"
            ]
        }
        """

        try:
            response = await self.llm.generate_response(recommendation_prompt)
            recommendations = json.loads(response)

            logger.info(
                f"✅ Generated learning recommendations with {len(recommendations.get('improvement_recommendations', []))} improvements"
            )
            return recommendations

        except Exception as e:
            logger.warning(f"LLM recommendation generation failed: {e}")
            return await self._fallback_learning_recommendations(experiences, patterns)

    def _filter_relevant_experiences(
        self, experiences: List[LearningExperience], task_type: str, context: Dict
    ) -> List[LearningExperience]:
        """Filter experiences relevant to current task"""
        relevant = []

        for exp in experiences:
            # Same task type
            if exp.task_type == task_type:
                relevant.append(exp)
            # Similar context
            elif self._context_similarity(exp.context, context) > 0.7:
                relevant.append(exp)

        # Sort by success score and recency
        relevant.sort(key=lambda x: (x.success_score, x.timestamp), reverse=True)
        return relevant[:10]

    def _filter_applicable_patterns(
        self, patterns: List[StrategyPattern], task_type: str, context: Dict
    ) -> List[StrategyPattern]:
        """Filter patterns applicable to current task"""
        applicable = []

        for pattern in patterns:
            if task_type.lower() in pattern.pattern_id.lower():
                applicable.append(pattern)

        # Sort by success rate and usage
        applicable.sort(key=lambda x: (x.success_rate, x.usage_count), reverse=True)
        return applicable[:5]

    def _filter_relevant_insights(
        self, insights: List[OptimizationInsight], task_type: str, context: Dict
    ) -> List[OptimizationInsight]:
        """Filter insights relevant to current task"""
        relevant = []

        for insight in insights:
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

    def _validate_strategy(self, strategy: Dict) -> Dict:
        """Validate and ensure strategy has required fields"""
        defaults = {
            "base_approach": "systematic analysis and execution",
            "optimization_elements": [],
            "quality_enhancements": [],
            "efficiency_improvements": [],
            "learning_adaptations": [],
            "confidence_score": 0.5,
            "expected_improvements": {
                "success": 0.1,
                "efficiency": 0.1,
                "quality": 0.1,
            },
            "reasoning": "Generated based on learning history",
            "risk_mitigation": [],
            "success_metrics": [],
        }

        for key, default_value in defaults.items():
            if key not in strategy:
                strategy[key] = default_value

        # Ensure confidence is within bounds
        strategy["confidence_score"] = max(
            0.0, min(1.0, strategy.get("confidence_score", 0.5))
        )

        return strategy

    async def _fallback_strategy_optimization(
        self,
        task_type: str,
        context: Dict,
        experiences: List[LearningExperience],
        patterns: List[StrategyPattern],
    ) -> Dict:
        """Fallback strategy optimization"""
        # Find best performing experiences
        relevant_experiences = self._filter_relevant_experiences(
            experiences, task_type, context
        )

        if relevant_experiences:
            best_exp = max(relevant_experiences, key=lambda x: x.success_score)
            base_approach = best_exp.approach_used
            optimization_elements = best_exp.optimization_insights[:3]
            confidence = best_exp.success_score
        else:
            base_approach = "systematic analysis and execution"
            optimization_elements = ["thorough analysis", "step-by-step execution"]
            confidence = 0.5

        return {
            "base_approach": base_approach,
            "optimization_elements": optimization_elements,
            "quality_enhancements": ["thorough validation", "comprehensive testing"],
            "efficiency_improvements": [
                "optimized resource usage",
                "streamlined process",
            ],
            "learning_adaptations": ["continuous improvement", "feedback integration"],
            "confidence_score": confidence,
            "expected_improvements": {
                "success": 0.1,
                "efficiency": 0.1,
                "quality": 0.1,
            },
            "reasoning": "Based on best performing similar experiences",
            "risk_mitigation": ["error handling", "fallback strategies"],
            "success_metrics": ["task completion", "quality metrics"],
        }

    async def _fallback_learning_recommendations(
        self, experiences: List[LearningExperience], patterns: List[StrategyPattern]
    ) -> Dict:
        """Fallback learning recommendations"""
        if not experiences:
            return {
                "performance_analysis": {
                    "overall_assessment": "Insufficient data for analysis"
                },
                "improvement_recommendations": [],
                "learning_opportunities": ["Start recording more detailed experiences"],
                "pattern_insights": ["Need more data to identify patterns"],
                "strategy_adaptations": ["Focus on consistent approach documentation"],
                "focus_areas": ["Data collection", "Experience recording"],
            }

        # Simple analysis
        recent_success = sum(exp.success_score for exp in experiences[-5:]) / min(
            5, len(experiences)
        )

        recommendations = []
        if recent_success < 0.7:
            recommendations.append(
                {
                    "area": "success",
                    "recommendation": "Focus on improving task completion rates",
                    "priority": "high",
                    "expected_impact": 0.3,
                    "implementation": "Analyze failed attempts and adapt strategies",
                }
            )

        return {
            "performance_analysis": {
                "overall_assessment": f"Recent success rate: {recent_success:.2f}"
            },
            "improvement_recommendations": recommendations,
            "learning_opportunities": ["Pattern recognition", "Strategy optimization"],
            "pattern_insights": [f"Identified {len(patterns)} successful patterns"],
            "strategy_adaptations": ["Continue learning from experiences"],
            "focus_areas": ["Success optimization", "Quality improvement"],
        }
