"""
LLM-Driven Pattern Recognizer
Replaces static pattern analysis with intelligent recognition
"""

import hashlib
import json
from typing import Dict, List, Optional

from app.logger import logger
from app.memory.types import LearningExperience, OptimizationInsight, StrategyPattern


class LLMPatternRecognizer:
    """Recognizes patterns in learning experiences using LLM reasoning"""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def analyze_for_patterns(
        self, experiences: List[LearningExperience]
    ) -> List[StrategyPattern]:
        """Analyze experiences to identify successful patterns"""
        logger.info(f"🔍 Analyzing {len(experiences)} experiences for patterns")

        if not experiences:
            return []

        if self.llm and len(experiences) >= 3:
            return await self._llm_pattern_recognition(experiences)
        else:
            return await self._fallback_pattern_analysis(experiences)

    async def _llm_pattern_recognition(
        self, experiences: List[LearningExperience]
    ) -> List[StrategyPattern]:
        """Use LLM to identify patterns in experiences"""
        # Group experiences by type for analysis
        experience_groups = self._group_experiences(experiences)
        patterns = []

        for task_type, group_experiences in experience_groups.items():
            if len(group_experiences) < 2:
                continue

            pattern_prompt = f"""
            Analyze these learning experiences to identify successful patterns:

            Task Type: {task_type}

            Experiences:
            """

            for i, exp in enumerate(group_experiences[:5]):  # Limit for context
                pattern_prompt += f"""
            Experience {i+1}:
            - Approach: {exp.approach_used}
            - Context: {exp.context}
            - Success: {exp.success_score:.2f}
            - Efficiency: {exp.efficiency_score:.2f}
            - Quality: {exp.quality_score:.2f}
            """

            pattern_prompt += """

            Identify successful patterns by analyzing:
            - Common elements in high-performing approaches
            - Context conditions that lead to success
            - Strategy elements that consistently work
            - Factors that differentiate success from failure

            Return JSON array of patterns:
            [
                {
                    "pattern_type": "approach_pattern | context_pattern | strategy_pattern",
                    "context_conditions": {"key": "value"},
                    "strategy_elements": ["element1", "element2"],
                    "success_indicators": ["indicator1", "indicator2"],
                    "confidence": 0.0-1.0
                }
            ]
            """

            try:
                response = await self.llm.generate_response(pattern_prompt)
                llm_patterns = json.loads(response)

                for i, pattern_data in enumerate(llm_patterns):
                    pattern_id = self._generate_pattern_id(task_type, pattern_data)

                    pattern = StrategyPattern(
                        pattern_id=pattern_id,
                        pattern_type=pattern_data.get(
                            "pattern_type", "strategy_pattern"
                        ),
                        context_conditions=pattern_data.get("context_conditions", {}),
                        strategy_elements=pattern_data.get("strategy_elements", []),
                        success_rate=self._calculate_pattern_success_rate(
                            group_experiences, pattern_data
                        ),
                        efficiency_gain=self._calculate_efficiency_gain(
                            group_experiences, pattern_data
                        ),
                        quality_improvement=self._calculate_quality_improvement(
                            group_experiences, pattern_data
                        ),
                        usage_count=1,
                        last_used=max(exp.timestamp for exp in group_experiences),
                        confidence=pattern_data.get("confidence", 0.5),
                    )
                    patterns.append(pattern)

            except Exception as e:
                logger.warning(f"LLM pattern recognition failed for {task_type}: {e}")
                # Fall back to simple pattern analysis
                patterns.extend(
                    await self._fallback_pattern_analysis(group_experiences)
                )

        logger.info(f"✅ Identified {len(patterns)} successful patterns")
        return patterns

    async def find_applicable_patterns(
        self, task_type: str, context: Dict, patterns: List[StrategyPattern]
    ) -> List[StrategyPattern]:
        """Find patterns applicable to current context using LLM reasoning"""
        if not patterns:
            return []

        # Filter patterns by task type first
        relevant_patterns = [p for p in patterns if task_type in p.pattern_id.lower()]

        if not relevant_patterns:
            return []

        if self.llm:
            return await self._llm_pattern_matching(
                task_type, context, relevant_patterns
            )
        else:
            return await self._fallback_pattern_matching(context, relevant_patterns)

    async def _llm_pattern_matching(
        self, task_type: str, context: Dict, patterns: List[StrategyPattern]
    ) -> List[StrategyPattern]:
        """Use LLM to match patterns to current context"""
        matching_prompt = f"""
        Determine which patterns are applicable to this current situation:

        Current Task: {task_type}
        Current Context: {context}

        Available Patterns:
        """

        for i, pattern in enumerate(patterns[:5]):  # Limit for context
            matching_prompt += f"""
        Pattern {i+1}:
        - Type: {pattern.pattern_type}
        - Context Conditions: {pattern.context_conditions}
        - Strategy Elements: {pattern.strategy_elements}
        - Success Rate: {pattern.success_rate:.2f}
        - Confidence: {pattern.confidence:.2f}
        """

        matching_prompt += """

        Analyze each pattern and determine:
        - How well the context conditions match the current situation
        - Whether the strategy elements are applicable
        - The expected effectiveness for this specific context

        Return JSON array of applicable patterns with scores:
        [
            {
                "pattern_index": 0,
                "applicability_score": 0.0-1.0,
                "match_reasoning": "explanation",
                "expected_effectiveness": 0.0-1.0
            }
        ]

        Only include patterns with applicability_score > 0.6.
        """

        try:
            response = await self.llm.generate_response(matching_prompt)
            matches = json.loads(response)

            applicable_patterns = []
            for match in matches:
                pattern_idx = match.get("pattern_index", 0)
                if pattern_idx < len(patterns):
                    pattern = patterns[pattern_idx]
                    pattern.applicability_score = match.get("applicability_score", 0.0)
                    applicable_patterns.append(pattern)

            # Sort by applicability score
            applicable_patterns.sort(key=lambda p: p.applicability_score, reverse=True)
            return applicable_patterns

        except Exception as e:
            logger.warning(f"LLM pattern matching failed: {e}")
            return await self._fallback_pattern_matching(context, patterns)

    def _group_experiences(
        self, experiences: List[LearningExperience]
    ) -> Dict[str, List[LearningExperience]]:
        """Group experiences by task type"""
        groups = {}
        for exp in experiences:
            if exp.task_type not in groups:
                groups[exp.task_type] = []
            groups[exp.task_type].append(exp)
        return groups

    def _generate_pattern_id(self, task_type: str, pattern_data: Dict) -> str:
        """Generate unique pattern ID"""
        pattern_str = f"{task_type}_{pattern_data.get('pattern_type', '')}_{pattern_data.get('context_conditions', {})}"
        return f"pattern_{hashlib.md5(pattern_str.encode()).hexdigest()[:8]}"

    def _calculate_pattern_success_rate(
        self, experiences: List[LearningExperience], pattern_data: Dict
    ) -> float:
        """Calculate success rate for pattern based on matching experiences"""
        matching_experiences = []
        strategy_elements = pattern_data.get("strategy_elements", [])

        for exp in experiences:
            # Simple matching based on approach containing strategy elements
            if any(
                element.lower() in exp.approach_used.lower()
                for element in strategy_elements
            ):
                matching_experiences.append(exp)

        if not matching_experiences:
            return 0.5  # Default when no matches

        return sum(exp.success_score for exp in matching_experiences) / len(
            matching_experiences
        )

    def _calculate_efficiency_gain(
        self, experiences: List[LearningExperience], pattern_data: Dict
    ) -> float:
        """Calculate efficiency gain for pattern"""
        # Similar logic to success rate but for efficiency
        strategy_elements = pattern_data.get("strategy_elements", [])
        matching_experiences = [
            exp
            for exp in experiences
            if any(
                element.lower() in exp.approach_used.lower()
                for element in strategy_elements
            )
        ]

        if not matching_experiences:
            return 0.0

        return (
            sum(exp.efficiency_score for exp in matching_experiences)
            / len(matching_experiences)
            - 0.5
        )

    def _calculate_quality_improvement(
        self, experiences: List[LearningExperience], pattern_data: Dict
    ) -> float:
        """Calculate quality improvement for pattern"""
        strategy_elements = pattern_data.get("strategy_elements", [])
        matching_experiences = [
            exp
            for exp in experiences
            if any(
                element.lower() in exp.approach_used.lower()
                for element in strategy_elements
            )
        ]

        if not matching_experiences:
            return 0.0

        return (
            sum(exp.quality_score for exp in matching_experiences)
            / len(matching_experiences)
            - 0.5
        )

    async def _fallback_pattern_analysis(
        self, experiences: List[LearningExperience]
    ) -> List[StrategyPattern]:
        """Fallback pattern analysis when LLM is not available"""
        patterns = []

        # Group by approach and find successful ones
        approach_groups = {}
        for exp in experiences:
            if exp.approach_used not in approach_groups:
                approach_groups[exp.approach_used] = []
            approach_groups[exp.approach_used].append(exp)

        for approach, group_exps in approach_groups.items():
            if len(group_exps) >= 2:
                avg_success = sum(exp.success_score for exp in group_exps) / len(
                    group_exps
                )

                if avg_success > 0.7:  # Threshold for successful pattern
                    pattern_id = (
                        f"pattern_{hashlib.md5(approach.encode()).hexdigest()[:8]}"
                    )

                    pattern = StrategyPattern(
                        pattern_id=pattern_id,
                        pattern_type="approach_pattern",
                        context_conditions={},
                        strategy_elements=[approach],
                        success_rate=avg_success,
                        efficiency_gain=sum(exp.efficiency_score for exp in group_exps)
                        / len(group_exps)
                        - 0.5,
                        quality_improvement=sum(exp.quality_score for exp in group_exps)
                        / len(group_exps)
                        - 0.5,
                        usage_count=len(group_exps),
                        last_used=max(exp.timestamp for exp in group_exps),
                        confidence=0.6,
                    )
                    patterns.append(pattern)

        return patterns

    async def _fallback_pattern_matching(
        self, context: Dict, patterns: List[StrategyPattern]
    ) -> List[StrategyPattern]:
        """Fallback pattern matching"""
        # Simple keyword-based matching
        applicable = []

        for pattern in patterns:
            score = 0.5  # Base score

            # Check if context conditions match
            for key, value in pattern.context_conditions.items():
                if key in context and str(context[key]).lower() == str(value).lower():
                    score += 0.2

            if score > 0.6:
                pattern.applicability_score = score
                applicable.append(pattern)

        return sorted(applicable, key=lambda p: p.applicability_score, reverse=True)
