"""
Plan Analyzer
LLM-driven analysis of user requests to generate comprehensive plans
"""

import json
import re
import time
from typing import Dict

from app.logger import logger


class PlanAnalyzer:
    """
    Analyzes user requests using LLM to create comprehensive execution plans
    """

    def __init__(self, llm=None):
        self.llm = llm

    async def analyze_request(self, user_request: str) -> Dict:
        """
        Use LLM to create a comprehensive plan for any user request
        """
        logger.info(f"🎯 Creating LLM-driven comprehensive plan for: {user_request}")

        if not self.llm:
            return self._create_fallback_plan(user_request)

        # Use LLM to analyze the request and create a detailed plan
        plan_prompt = f"""
        Analyze this user request and create a comprehensive execution plan:

        Request: "{user_request}"

        Create a detailed plan that includes:
        1. Clear understanding of what the user wants
        2. Step-by-step breakdown of all tasks needed
        3. Logical sequence of operations
        4. Expected deliverables
        5. Success criteria

        Respond with JSON only:
        {{
            "goal": "clear statement of what we're trying to achieve",
            "task_type": "website_review|news_search|research|analysis|coding|report_generation|general",
            "complexity": "simple|moderate|complex",
            "estimated_duration": "estimated time to complete",
            "priority": "high|medium|low",
            "phases": [
                {{
                    "id": 1,
                    "title": "Phase name",
                    "description": "What this phase accomplishes",
                    "steps": [
                        "Specific step 1",
                        "Specific step 2",
                        "Specific step 3"
                    ],
                    "tools_needed": ["tool1", "tool2"],
                    "success_criteria": "How to know this phase is complete",
                    "estimated_time": "time for this phase"
                }}
            ],
            "final_deliverable": "What the user will receive at the end",
            "success_criteria": "How to know the entire task is complete"
        }}
        """

        try:
            response = await self.llm.ask(plan_prompt)

            # Parse LLM response - try multiple JSON extraction methods
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                # Try finding JSON between triple backticks
                json_match = re.search(
                    r"```json\s*(\{.*?\})\s*```", response, re.DOTALL
                )
                if json_match:
                    json_text = json_match.group(1)
                else:
                    json_text = response.strip()
            else:
                json_text = json_match.group(0)

            if json_text:
                try:
                    plan = json.loads(json_text)
                    plan["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

                    logger.info(
                        f"🧠 LLM created plan with {len(plan.get('phases', []))} phases"
                    )

                    return plan

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM plan JSON: {e}")
                    logger.info(f"Raw response: {response[:200]}...")
                    return self._create_fallback_plan(user_request)
            else:
                logger.warning("No JSON found in LLM response")
                return self._create_fallback_plan(user_request)

        except Exception as e:
            logger.warning(f"Failed to create LLM plan: {e}")
            return self._create_fallback_plan(user_request)

    def _create_fallback_plan(self, user_request: str) -> Dict:
        """
        Create a basic plan when LLM is not available
        """
        logger.info("🔄 Creating fallback plan (LLM not available)")

        # Simple analysis based on keywords
        task_type = "general"
        if any(
            word in user_request.lower()
            for word in ["review", "analyze", ".com", ".org", "website"]
        ):
            task_type = "website_review"
        elif any(
            word in user_request.lower()
            for word in ["news", "latest", "current", "today"]
        ):
            task_type = "news_search"
        elif any(
            word in user_request.lower() for word in ["research", "find", "search"]
        ):
            task_type = "research"

        plan = {
            "goal": user_request,
            "task_type": task_type,
            "complexity": "moderate",
            "estimated_duration": "5-10 minutes",
            "priority": "medium",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "phases": [
                {
                    "id": 1,
                    "title": "Planning and Analysis",
                    "description": "Understand the request and plan the approach",
                    "steps": [
                        "Analyze user request",
                        "Determine best approach",
                        "Gather required tools",
                    ],
                    "tools_needed": ["analysis"],
                    "success_criteria": "Clear understanding of task",
                    "estimated_time": "1-2 minutes",
                },
                {
                    "id": 2,
                    "title": "Execution",
                    "description": "Execute the planned approach",
                    "steps": [
                        "Execute primary action",
                        "Gather information/results",
                        "Verify completion",
                    ],
                    "tools_needed": ["execution"],
                    "success_criteria": "Task objectives met",
                    "estimated_time": "3-6 minutes",
                },
                {
                    "id": 3,
                    "title": "Completion and Delivery",
                    "description": "Finalize and deliver results",
                    "steps": ["Review results", "Format output", "Deliver to user"],
                    "tools_needed": ["formatting"],
                    "success_criteria": "User receives complete result",
                    "estimated_time": "1-2 minutes",
                },
            ],
            "final_deliverable": "Completed task results",
            "success_criteria": "User request fulfilled completely",
        }

        return plan
