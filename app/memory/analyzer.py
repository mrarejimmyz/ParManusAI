"""
LLM-Driven Experience Analyzer
Replaces static scoring with intelligent analysis
"""

import time
from typing import Dict, List, Optional

from app.logger import logger
from app.memory.types import LearningDomain, LearningExperience, TaskType


class LLMExperienceAnalyzer:
    """Analyzes learning experiences using LLM reasoning"""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def analyze_experience(
        self, task_type: str, approach_used: str, context: Dict, outcome: Dict
    ) -> LearningExperience:
        """Analyze experience using LLM-driven assessment"""
        logger.info(f"🧠 Analyzing learning experience for task: {task_type}")

        if self.llm:
            scores = await self._llm_score_experience(
                task_type, approach_used, context, outcome
            )
            lessons = await self._llm_extract_lessons(approach_used, outcome)
            insights = await self._llm_extract_insights(context, outcome)
            domain = await self._llm_classify_domain(task_type, context)
        else:
            scores = self._fallback_scoring(outcome)
            lessons = self._fallback_lessons(approach_used, outcome)
            insights = self._fallback_insights(context, outcome)
            domain = LearningDomain.TECHNICAL.value

        experience = LearningExperience(
            task_type=task_type,
            approach_used=approach_used,
            context=context,
            outcome=outcome,
            success_score=scores["success"],
            efficiency_score=scores["efficiency"],
            quality_score=scores["quality"],
            lessons_learned=lessons,
            optimization_insights=insights,
            timestamp=time.time(),
            domain=domain,
        )

        logger.info(
            f"✅ Experience analyzed - Success: {scores['success']:.2f}, Quality: {scores['quality']:.2f}"
        )
        return experience

    async def _llm_score_experience(
        self, task_type: str, approach: str, context: Dict, outcome: Dict
    ) -> Dict[str, float]:
        """Use LLM to intelligently score the experience"""
        scoring_prompt = f"""
        Analyze this learning experience and provide intelligent scoring:

        Task Type: {task_type}
        Approach Used: {approach}
        Context: {context}
        Outcome: {outcome}

        Evaluate and score (0.0-1.0) based on:

        SUCCESS SCORE:
        - Did the task achieve its intended goals?
        - Were objectives met effectively?
        - Was the outcome satisfactory?

        EFFICIENCY SCORE:
        - How quickly was the task completed?
        - Were resources used optimally?
        - Could it have been done more efficiently?

        QUALITY SCORE:
        - How thorough and accurate was the work?
        - Was deep reasoning applied?
        - Were best practices followed?

        Return JSON:
        {{
            "success": 0.0-1.0,
            "efficiency": 0.0-1.0,
            "quality": 0.0-1.0,
            "reasoning": "explanation of scores"
        }}
        """

        try:
            response = await self.llm.generate_response(scoring_prompt)
            import json

            scores = json.loads(response)
            return {
                "success": max(0.0, min(1.0, scores.get("success", 0.5))),
                "efficiency": max(0.0, min(1.0, scores.get("efficiency", 0.5))),
                "quality": max(0.0, min(1.0, scores.get("quality", 0.5))),
            }
        except Exception as e:
            logger.warning(f"LLM scoring failed: {e}")
            return self._fallback_scoring(outcome)

    async def _llm_extract_lessons(self, approach: str, outcome: Dict) -> List[str]:
        """Use LLM to extract meaningful lessons from the experience"""
        lessons_prompt = f"""
        Extract key lessons learned from this experience:

        Approach Used: {approach}
        Outcome: {outcome}

        Identify:
        - What worked well and why
        - What could be improved
        - Key insights for future similar tasks
        - Best practices discovered
        - Patterns worth remembering

        Return JSON array of specific, actionable lessons:
        ["lesson 1", "lesson 2", ...]

        Focus on insights that would help improve future performance.
        """

        try:
            response = await self.llm.generate_response(lessons_prompt)
            import json

            lessons = json.loads(response)
            return lessons if isinstance(lessons, list) else [str(lessons)]
        except Exception as e:
            logger.warning(f"LLM lesson extraction failed: {e}")
            return self._fallback_lessons(approach, outcome)

    async def _llm_extract_insights(self, context: Dict, outcome: Dict) -> List[str]:
        """Use LLM to extract optimization insights"""
        insights_prompt = f"""
        Extract optimization insights from this experience:

        Context: {context}
        Outcome: {outcome}

        Identify:
        - Optimization opportunities discovered
        - Performance improvement methods
        - Resource efficiency gains
        - Quality enhancement techniques
        - Strategic improvements

        Return JSON array of specific optimization insights:
        ["insight 1", "insight 2", ...]

        Focus on actionable insights that could improve future performance.
        """

        try:
            response = await self.llm.generate_response(insights_prompt)
            import json

            insights = json.loads(response)
            return insights if isinstance(insights, list) else [str(insights)]
        except Exception as e:
            logger.warning(f"LLM insight extraction failed: {e}")
            return self._fallback_insights(context, outcome)

    async def _llm_classify_domain(self, task_type: str, context: Dict) -> str:
        """Use LLM to classify the learning domain"""
        classification_prompt = f"""
        Classify the learning domain for this experience:

        Task Type: {task_type}
        Context: {context}

        Available domains:
        - TECHNICAL: Technical implementation, code, systems
        - STRATEGIC: Planning, decision-making, high-level strategy
        - QUALITY: Quality assurance, validation, testing
        - EFFICIENCY: Performance optimization, resource management
        - USER_INTERACTION: User experience, communication, interface

        Return just the domain name (e.g., "TECHNICAL").
        """

        try:
            response = await self.llm.generate_response(classification_prompt)
            domain = response.strip().upper()

            # Validate domain
            valid_domains = [d.value.upper() for d in LearningDomain]
            if domain in valid_domains:
                return domain.lower()
            else:
                return LearningDomain.TECHNICAL.value

        except Exception as e:
            logger.warning(f"LLM domain classification failed: {e}")
            return LearningDomain.TECHNICAL.value

    def _fallback_scoring(self, outcome: Dict) -> Dict[str, float]:
        """Fallback scoring when LLM is not available"""
        success = 0.7 if outcome.get("task_completed", False) else 0.4
        efficiency = 0.8 if outcome.get("efficient_execution", False) else 0.5
        quality = 0.7 if outcome.get("high_quality", False) else 0.5

        return {"success": success, "efficiency": efficiency, "quality": quality}

    def _fallback_lessons(self, approach: str, outcome: Dict) -> List[str]:
        """Fallback lesson extraction"""
        lessons = []

        if outcome.get("task_completed", False):
            lessons.append(f"Approach '{approach}' was effective for task completion")

        if outcome.get("efficient_execution", False):
            lessons.append("Efficient execution methods should be prioritized")

        if outcome.get("high_quality", False):
            lessons.append("Quality-focused approaches yield better results")

        return lessons or ["Experience recorded for future reference"]

    def _fallback_insights(self, context: Dict, outcome: Dict) -> List[str]:
        """Fallback insight extraction"""
        insights = []

        if outcome.get("optimization_applied", False):
            insights.append("Optimization strategies improve performance")

        if context.get("complexity") == "high" and outcome.get("task_completed", False):
            insights.append("Complex tasks benefit from structured approaches")

        return insights or ["General optimization opportunity identified"]
