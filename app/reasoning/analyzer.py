"""
LLM-Driven Multi-Layer Analyzer
Replaces static analysis layers with intelligent reasoning
"""

import time
from typing import Dict, List, Optional

from app.logger import logger
from app.reasoning.types import (
    AnalysisLayer,
    AnalysisResult,
    ReasoningContext,
    ReasoningDepth,
)


class LLMMultiLayerAnalyzer:
    """Performs multi-layered analysis using LLM reasoning"""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def analyze_task_deeply(
        self, task: str, context: Dict, depth: ReasoningDepth = ReasoningDepth.EXPERT
    ) -> Dict:
        """Perform deep multi-layered analysis of the task"""
        logger.info(f"🧠 Starting deep analysis for task: {task[:50]}...")

        analysis = {
            "task": task,
            "timestamp": time.time(),
            "reasoning_depth": depth.value,
            "reasoning_layers": {},
        }

        # Determine which layers to analyze based on depth
        layers_to_analyze = self._get_layers_for_depth(depth)

        # Perform analysis for each layer
        for layer in layers_to_analyze:
            layer_result = await self._analyze_layer(task, context, layer)
            analysis["reasoning_layers"][layer.value] = layer_result

        # Synthesize cross-layer insights
        if self.llm:
            analysis["synthesis"] = await self._synthesize_insights(
                analysis["reasoning_layers"]
            )
        else:
            analysis["synthesis"] = self._fallback_synthesis(
                analysis["reasoning_layers"]
            )

        logger.info(f"✅ Completed {len(layers_to_analyze)}-layer analysis")
        return analysis

    async def _analyze_layer(
        self, task: str, context: Dict, layer: AnalysisLayer
    ) -> Dict:
        """Analyze task at specific reasoning layer"""
        if self.llm:
            return await self._llm_layer_analysis(task, context, layer)
        else:
            return await self._fallback_layer_analysis(task, context, layer)

    async def _llm_layer_analysis(
        self, task: str, context: Dict, layer: AnalysisLayer
    ) -> Dict:
        """Use LLM for intelligent layer analysis"""
        layer_prompts = {
            AnalysisLayer.SURFACE: self._get_surface_prompt(task, context),
            AnalysisLayer.ANALYTICAL: self._get_analytical_prompt(task, context),
            AnalysisLayer.STRATEGIC: self._get_strategic_prompt(task, context),
            AnalysisLayer.DEEP: self._get_deep_prompt(task, context),
            AnalysisLayer.EXPERT: self._get_expert_prompt(task, context),
        }

        prompt = layer_prompts.get(layer, self._get_surface_prompt(task, context))

        try:
            response = await self.llm.generate_response(prompt)
            import json

            layer_analysis = json.loads(response)

            return {
                "insights": layer_analysis.get("insights", {}),
                "recommendations": layer_analysis.get("recommendations", []),
                "confidence": layer_analysis.get("confidence", 0.5),
                "reasoning": layer_analysis.get("reasoning", "LLM analysis completed"),
                "optimization_opportunities": layer_analysis.get(
                    "optimization_opportunities", []
                ),
                "risk_factors": layer_analysis.get("risk_factors", []),
            }

        except Exception as e:
            logger.warning(f"LLM layer analysis failed for {layer.value}: {e}")
            return await self._fallback_layer_analysis(task, context, layer)

    def _get_surface_prompt(self, task: str, context: Dict) -> str:
        """Generate prompt for surface-level analysis"""
        return f"""
        Perform surface-level analysis of this task:

        Task: {task}
        Context: {context}

        Analyze at a surface level focusing on:
        - Primary objective and immediate goals
        - Obvious requirements and constraints
        - Clear next steps
        - Immediate resource needs

        Return JSON:
        {{
            "insights": {{
                "primary_objective": "main goal",
                "immediate_requirements": ["req1", "req2"],
                "obvious_constraints": ["constraint1", "constraint2"],
                "next_steps": ["step1", "step2"]
            }},
            "recommendations": ["rec1", "rec2"],
            "confidence": 0.0-1.0,
            "reasoning": "explanation of analysis"
        }}
        """

    def _get_analytical_prompt(self, task: str, context: Dict) -> str:
        """Generate prompt for analytical analysis"""
        return f"""
        Perform analytical-level analysis of this task:

        Task: {task}
        Context: {context}

        Analyze analytically focusing on:
        - Success factors and failure risks
        - Resource optimization opportunities
        - Alternative approaches and methods
        - Quality assurance considerations

        Return JSON:
        {{
            "insights": {{
                "success_factors": ["factor1", "factor2"],
                "risk_assessment": ["risk1", "risk2"],
                "resource_optimization": ["opt1", "opt2"],
                "alternative_approaches": ["approach1", "approach2"]
            }},
            "recommendations": ["rec1", "rec2"],
            "optimization_opportunities": ["opp1", "opp2"],
            "risk_factors": ["risk1", "risk2"],
            "confidence": 0.0-1.0,
            "reasoning": "analytical reasoning explanation"
        }}
        """

    def _get_strategic_prompt(self, task: str, context: Dict) -> str:
        """Generate prompt for strategic analysis"""
        return f"""
        Perform strategic-level analysis of this task:

        Task: {task}
        Context: {context}

        Analyze strategically focusing on:
        - Long-term implications and consequences
        - Strategic optimization opportunities
        - Learning and capability building potential
        - Quality enhancement strategies

        Return JSON:
        {{
            "insights": {{
                "long_term_implications": ["implication1", "implication2"],
                "strategic_opportunities": ["opp1", "opp2"],
                "learning_potential": ["learning1", "learning2"],
                "quality_enhancement": ["enhancement1", "enhancement2"]
            }},
            "recommendations": ["rec1", "rec2"],
            "optimization_opportunities": ["opp1", "opp2"],
            "confidence": 0.0-1.0,
            "reasoning": "strategic reasoning explanation"
        }}
        """

    def _get_deep_prompt(self, task: str, context: Dict) -> str:
        """Generate prompt for deep analysis"""
        return f"""
        Perform deep-level analysis of this task:

        Task: {task}
        Context: {context}

        Analyze deeply focusing on:
        - Pattern recognition and hidden connections
        - Predictive modeling and outcome forecasting
        - Adaptive strategies and dynamic approaches
        - Innovation opportunities and breakthrough potential

        Return JSON:
        {{
            "insights": {{
                "pattern_recognition": ["pattern1", "pattern2"],
                "predictive_modeling": ["prediction1", "prediction2"],
                "adaptive_strategies": ["strategy1", "strategy2"],
                "innovation_opportunities": ["innovation1", "innovation2"]
            }},
            "recommendations": ["rec1", "rec2"],
            "optimization_opportunities": ["opp1", "opp2"],
            "confidence": 0.0-1.0,
            "reasoning": "deep analysis reasoning"
        }}
        """

    def _get_expert_prompt(self, task: str, context: Dict) -> str:
        """Generate prompt for expert-level analysis"""
        return f"""
        Perform expert-level analysis of this task:

        Task: {task}
        Context: {context}

        Analyze at expert level focusing on:
        - Mastery application and best practices
        - Optimization synthesis and integration
        - Breakthrough potential and paradigm shifts
        - Excellence frameworks and world-class standards

        Return JSON:
        {{
            "insights": {{
                "mastery_application": ["mastery1", "mastery2"],
                "optimization_synthesis": ["synthesis1", "synthesis2"],
                "breakthrough_potential": ["breakthrough1", "breakthrough2"],
                "excellence_framework": ["framework1", "framework2"]
            }},
            "recommendations": ["rec1", "rec2"],
            "optimization_opportunities": ["opp1", "opp2"],
            "confidence": 0.0-1.0,
            "reasoning": "expert analysis reasoning"
        }}
        """

    async def _synthesize_insights(self, layers: Dict) -> Dict:
        """Use LLM to synthesize insights across layers"""
        synthesis_prompt = f"""
        Synthesize insights from this multi-layered analysis:

        Analysis Layers:
        {layers}

        Create a comprehensive synthesis that:
        - Identifies the most critical insights across all layers
        - Finds connections and patterns between layers
        - Prioritizes recommendations by impact and feasibility
        - Provides an integrated optimization strategy

        Return JSON:
        {{
            "key_insights": ["insight1", "insight2"],
            "cross_layer_patterns": ["pattern1", "pattern2"],
            "priority_recommendations": [
                {{"recommendation": "rec1", "priority": "high|medium|low", "impact": 0.0-1.0}}
            ],
            "integrated_strategy": "comprehensive strategy description",
            "optimization_roadmap": ["step1", "step2"],
            "confidence": 0.0-1.0
        }}
        """

        try:
            response = await self.llm.generate_response(synthesis_prompt)
            import json

            return json.loads(response)
        except Exception as e:
            logger.warning(f"LLM synthesis failed: {e}")
            return self._fallback_synthesis(layers)

    def _get_layers_for_depth(self, depth: ReasoningDepth) -> List[AnalysisLayer]:
        """Get analysis layers based on reasoning depth"""
        layer_mapping = {
            ReasoningDepth.SURFACE: [AnalysisLayer.SURFACE],
            ReasoningDepth.ANALYTICAL: [
                AnalysisLayer.SURFACE,
                AnalysisLayer.ANALYTICAL,
            ],
            ReasoningDepth.STRATEGIC: [
                AnalysisLayer.SURFACE,
                AnalysisLayer.ANALYTICAL,
                AnalysisLayer.STRATEGIC,
            ],
            ReasoningDepth.DEEP: [
                AnalysisLayer.SURFACE,
                AnalysisLayer.ANALYTICAL,
                AnalysisLayer.STRATEGIC,
                AnalysisLayer.DEEP,
            ],
            ReasoningDepth.EXPERT: list(AnalysisLayer),
        }

        return layer_mapping.get(depth, [AnalysisLayer.SURFACE])

    async def _fallback_layer_analysis(
        self, task: str, context: Dict, layer: AnalysisLayer
    ) -> Dict:
        """Fallback analysis when LLM is not available"""
        fallback_insights = {
            AnalysisLayer.SURFACE: {
                "primary_objective": "Complete the given task",
                "immediate_requirements": ["Understanding", "Planning", "Execution"],
                "obvious_constraints": ["Time", "Resources", "Quality"],
            },
            AnalysisLayer.ANALYTICAL: {
                "success_factors": ["Clear planning", "Systematic execution"],
                "risk_assessment": ["Complexity risk", "Resource constraints"],
                "alternative_approaches": ["Sequential approach", "Parallel approach"],
            },
            AnalysisLayer.STRATEGIC: {
                "long_term_implications": [
                    "Learning opportunity",
                    "Capability building",
                ],
                "strategic_opportunities": [
                    "Process improvement",
                    "Quality enhancement",
                ],
            },
            AnalysisLayer.DEEP: {
                "pattern_recognition": ["Task patterns", "Success patterns"],
                "adaptive_strategies": ["Flexible approach", "Feedback integration"],
            },
            AnalysisLayer.EXPERT: {
                "mastery_application": ["Best practices", "Expert techniques"],
                "excellence_framework": [
                    "Quality standards",
                    "Optimization principles",
                ],
            },
        }

        return {
            "insights": fallback_insights.get(layer, {}),
            "recommendations": ["Apply systematic approach", "Focus on quality"],
            "confidence": 0.6,
            "reasoning": f"Fallback {layer.value} analysis",
            "optimization_opportunities": [
                "Process optimization",
                "Quality improvement",
            ],
            "risk_factors": ["Complexity", "Resource constraints"],
        }

    def _fallback_synthesis(self, layers: Dict) -> Dict:
        """Fallback synthesis when LLM is not available"""
        all_recommendations = []
        all_insights = []

        for layer_data in layers.values():
            all_recommendations.extend(layer_data.get("recommendations", []))
            insights = layer_data.get("insights", {})
            for insight_list in insights.values():
                if isinstance(insight_list, list):
                    all_insights.extend(insight_list)
                else:
                    all_insights.append(str(insight_list))

        return {
            "key_insights": all_insights[:5],  # Top 5 insights
            "cross_layer_patterns": ["Systematic approach", "Quality focus"],
            "priority_recommendations": [
                {"recommendation": rec, "priority": "medium", "impact": 0.5}
                for rec in all_recommendations[:3]
            ],
            "integrated_strategy": "Apply systematic multi-layered approach with focus on quality and optimization",
            "optimization_roadmap": ["Analyze", "Plan", "Execute", "Optimize"],
            "confidence": 0.6,
        }
