"""Planning and task analysis utilities for the ParManus system."""

import re
from typing import Dict, List, Optional


class TaskAnalyzer:
    """Advanced task analysis and categorization."""

    @staticmethod
    async def categorize_task(user_request: str, llm=None) -> str:
        """Determine task type from user request using LLM intelligence."""
        if not llm:
            # Fallback to simple heuristics if no LLM available
            return TaskAnalyzer._fallback_categorize_task(user_request)

        try:
            prompt = f"""Analyze this user request and categorize it into one of these task types:

- report_generation: Creating reports, analyses, detailed documents, investigations
- news_gathering: Getting current news, latest information, headlines, recent events
- website_review: Reviewing, analyzing, or checking websites or web content
- accident_prevention: Accident risk analysis, safety prevention strategies, and safety improvement planning
- file_operation: File-related tasks like reading, writing, creating, modifying files
- code_task: Programming, coding, scripting, or development tasks
- general_task: Any other type of task

User request: "{user_request}"

Respond with only the task type category (e.g., "report_generation")."""

            response = await llm.ask(prompt)
            task_type = response.strip().lower()

            # Validate the response
            valid_types = {
                "report_generation",
                "news_gathering",
                "website_review",
                "accident_prevention",
            }

            if task_type in valid_types:
                return task_type
            else:
                # Fallback if LLM response is invalid
                return TaskAnalyzer._fallback_categorize_task(user_request)

        except Exception as e:
            import logging

            logging.warning(f"LLM task categorization failed: {e}")
            return TaskAnalyzer._fallback_categorize_task(user_request)

    @staticmethod
    def _fallback_categorize_task(user_request: str) -> str:
        """Fallback task categorization using simple heuristics."""
        request_lower = user_request.lower()

        # Simple keyword-based fallback
        if any(x in request_lower for x in ["report", "analysis", "detailed"]):
            return "report_generation"
        elif any(x in request_lower for x in ["news", "current", "latest"]):
            return "news_gathering"
        elif any(x in request_lower for x in ["http", "www", ".com", "website"]):
            return "website_review"
        elif any(
            x in request_lower
            for x in ["accident", "crash", "collision", "safety", "risk", "prevention"]
        ):
            return "accident_prevention"
        elif any(x in request_lower for x in ["file", "read", "write"]):
            return "file_operation"
        elif any(x in request_lower for x in ["code", "program", "script"]):
            return "code_task"

        return "general_task"

    @staticmethod
    def assess_task_complexity(user_request: str) -> str:
        """Advanced complexity assessment based on multiple factors."""
        words = user_request.split()
        subtasks = len(re.findall(r"and|then|after|before|while", user_request.lower()))

        complexity_score = len(words) * 0.5 + subtasks * 2

        if complexity_score < 5:
            return "simple"
        elif complexity_score < 15:
            return "moderate"
        return "complex"

    @staticmethod
    def estimate_duration(analysis: Dict) -> str:
        """Estimate task duration based on comprehensive analysis."""
        complexity = analysis.get("complexity", "moderate")
        task_type = analysis.get("task_type", "general_task")

        base_durations = {"simple": 5, "moderate": 15, "complex": 30}

        type_multipliers = {
            "news_gathering": 1.3,
            "website_review": 1.2,
            "accident_prevention": 1.3,
            "file_operation": 0.8,
            "code_task": 1.5,
            "general_task": 1.0,
        }

        base_time = base_durations.get(complexity, 15)
        multiplier = type_multipliers.get(task_type, 1.0)

        estimated_minutes = int(base_time * multiplier)
        return f"{max(5, estimated_minutes-5)}-{estimated_minutes+5} minutes"


class PlanGenerator:
    """Advanced plan generation with task-specific templates."""

    @staticmethod
    def create_enhanced_phases(
        context: Dict, strategy: Dict, insights: Dict
    ) -> List[Dict]:
        """Create execution phases based on task type and context."""
        task_type = context.get("task_type", "general_task")

        if task_type == "report_generation":
            return [
                {
                    "id": 1,
                    "title": "Research and Information Gathering",
                    "description": "Research the topic and gather relevant information from multiple sources",
                    "tools_needed": ["browser_use"],
                    "steps": [
                        "Identify key search terms and sources",
                        "Search for reliable information sources",
                        "Extract relevant facts and data",
                        "Gather information from multiple perspectives",
                    ],
                    "success_criteria": "Comprehensive information collected from reliable sources",
                },
                {
                    "id": 2,
                    "title": "Verification and Cross-Referencing",
                    "description": "Verify information accuracy and cross-reference multiple sources",
                    "tools_needed": ["browser_use"],
                    "steps": [
                        "Verify facts from multiple sources",
                        "Check for consistency across sources",
                        "Identify any conflicting information",
                        "Validate timeline and details",
                    ],
                    "success_criteria": "Information verified and cross-referenced for accuracy",
                },
                {
                    "id": 3,
                    "title": "Report Creation and Formatting",
                    "description": "Create comprehensive report with proper structure and formatting",
                    "tools_needed": ["python_execute"],
                    "steps": [
                        "Organize collected information logically",
                        "Create detailed report with proper sections",
                        "Format as professional markdown document",
                        "Include executive summary and recommendations",
                    ],
                    "success_criteria": "Professional report created with comprehensive analysis",
                },
            ]

        elif task_type == "news_gathering":
            return [
                {
                    "id": 1,
                    "title": "Research Planning",
                    "description": "Plan news sources and research strategy",
                    "tools_needed": ["browser_use"],
                    "steps": [
                        "Identify reliable news sources",
                        "Plan research approach",
                    ],
                    "success_criteria": "Research strategy established",
                },
                {
                    "id": 2,
                    "title": "News Collection",
                    "description": "Browse news websites and gather current information",
                    "tools_needed": ["browser_use"],
                    "steps": [
                        "Visit major news websites",
                        "Extract current headlines",
                        "Gather detailed information",
                        "Verify information from multiple sources",
                    ],
                    "success_criteria": "Current news information collected",
                },
                {
                    "id": 3,
                    "title": "Content Creation",
                    "description": "Compile and format news into requested format",
                    "tools_needed": ["python_execute"],
                    "steps": [
                        "Organize collected news",
                        "Create formatted output",
                        "Generate news_report.md",
                    ],
                    "success_criteria": "News report created with real current information",
                },
            ]

        elif task_type == "website_review":
            return [
                {
                    "id": 1,
                    "title": "Initial Access",
                    "description": "Navigate and verify website access",
                    "tools_needed": ["browser_use"],
                    "steps": ["Navigate to website", "Verify access"],
                    "success_criteria": "Successfully accessed target URL",
                },
                {
                    "id": 2,
                    "title": "Content Analysis",
                    "description": "Extract and analyze website content",
                    "tools_needed": ["browser_use"],
                    "steps": [
                        "Extract main content",
                        "Capture screenshots",
                        "Analyze page structure",
                    ],
                    "success_criteria": "Content analyzed and documented",
                },
                {
                    "id": 3,
                    "title": "Documentation",
                    "description": "Document findings and create report",
                    "tools_needed": ["python_execute"],
                    "steps": ["Generate analysis.md", "Create summary.md"],
                    "success_criteria": "Documentation complete",
                },
            ]

        elif task_type == "accident_prevention":
            return [
                {
                    "id": 1,
                    "title": "Risk Analysis",
                    "description": "Analyze accident risk factors and partner safety guidelines",
                    "tools_needed": ["browser_use", "analysis"],
                    "steps": [
                        "Review partner accident prevention resources",
                        "Identify common risk patterns",
                        "Summarize safety guidance",
                    ],
                    "success_criteria": "Risk factors and prevention recommendations identified",
                },
                {
                    "id": 2,
                    "title": "Prevention Guidance",
                    "description": "Create actionable accident reduction recommendations",
                    "tools_needed": ["python_execute", "browser_use"],
                    "steps": [
                        "Draft safe driving best practices",
                        "Recommend documentation and compliance steps",
                        "Align recommendations with partner rules",
                    ],
                    "success_criteria": "Actionable accident prevention guidance created",
                },
                {
                    "id": 3,
                    "title": "Monitoring & Reporting",
                    "description": "Prepare a plan for tracking safety outcomes and incident reporting",
                    "tools_needed": ["python_execute"],
                    "steps": [
                        "Define monitoring criteria",
                        "Create reports for safety improvement",
                        "Prepare follow-up recommendations",
                    ],
                    "success_criteria": "Monitoring plan and safety report prepared",
                },
            ]

        elif task_type == "file_operation":
            return [
                {
                    "id": 1,
                    "title": "Preparation",
                    "description": "Analyze file operation requirements",
                    "tools_needed": ["python_execute"],
                    "steps": ["Validate paths", "Check permissions"],
                    "success_criteria": "Operation validated",
                },
                {
                    "id": 2,
                    "title": "Execution",
                    "description": "Perform file operations",
                    "tools_needed": ["python_execute"],
                    "steps": ["Execute operation", "Verify results"],
                    "success_criteria": "Operation completed",
                },
            ]

        # Default general task phases
        return [
            {
                "id": 1,
                "title": "Analysis",
                "description": "Analyze requirements",
                "tools_needed": ["python_execute"],
                "steps": ["Analyze request", "Create plan"],
                "success_criteria": "Requirements understood",
            },
            {
                "id": 2,
                "title": "Execution",
                "description": "Execute planned actions",
                "tools_needed": ["python_execute", "browser_use"],
                "steps": ["Execute actions", "Validate results"],
                "success_criteria": "Actions completed",
            },
        ]

    @staticmethod
    def define_success_criteria(analysis: Dict) -> List[str]:
        """Define detailed success criteria based on task analysis."""
        task_type = analysis.get("task_type", "general_task")
        complexity = analysis.get("complexity", "moderate")

        base_criteria = [
            "All planned actions completed successfully",
            "Results properly documented",
        ]

        if task_type == "website_review":
            base_criteria.extend(
                [
                    "Website content extracted and analyzed",
                    "Screenshots captured",
                    "Analysis report generated",
                ]
            )
        elif task_type == "accident_prevention":
            base_criteria.extend(
                [
                    "Accident risk factors identified",
                    "Preventive safety recommendations created",
                    "Partner accident prevention workflow aligned",
                ]
            )
        elif complexity == "complex":
            base_criteria.extend(
                ["Edge cases handled", "Performance optimized", "Error recovery tested"]
            )

        return base_criteria
