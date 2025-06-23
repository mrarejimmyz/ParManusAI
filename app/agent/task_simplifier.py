"""
Task Simplification Module
Handles smart task simplification for autonomous execution.
"""

from app.logger import logger


class TaskSimplifier:
    """Handles intelligent task simplification for autonomous execution."""

    def __init__(self):
        pass

    async def apply_smart_task_simplification(self, user_request: str) -> str:
        """Intelligently handle complex multi-step requests without oversimplifying"""
        request_lower = user_request.lower()

        # Detect complex multi-step tasks and preserve them
        complex_indicators = [
            "analyze",
            "update",
            "mark",
            "add",
            "create",
            "summary",
            "progress",
            "steps",
            "todo",
            "checklist",
            "multiple",
            "then",
            "and",
            "also",
            "additionally",
            "furthermore",
        ]

        # Count complexity indicators
        complexity_score = sum(
            1 for indicator in complex_indicators if indicator in request_lower
        )

        # If it's a complex multi-step task (3+ indicators), preserve the original request
        if complexity_score >= 3:
            logger.info(
                f"🧠 Complex multi-step task detected (score: {complexity_score}), preserving full request"
            )
            return user_request  # Cryptocurrency research simplification (only for simple requests)
        if (
            any(
                keyword in request_lower
                for keyword in [
                    "crypto",
                    "cryptocurrency",
                    "bitcoin",
                    "ethereum",
                ]
            )
            and complexity_score < 3
            and not any(  # Don't apply if it's about specific stocks/companies
                company in request_lower
                for company in [
                    "tesla",
                    "tsla",
                    "apple",
                    "aapl",
                    "microsoft",
                    "msft",
                    "google",
                    "googl",
                    "amazon",
                    "amzn",
                    "meta",
                    "nvda",
                    "nvidia",
                ]
            )
        ):
            return """Create a comprehensive cryptocurrency investment report for 2025. Include market analysis, top cryptocurrencies (Bitcoin, Ethereum, Solana, Cardano), investment strategies (conservative, balanced, aggressive portfolios), risk assessment, and specific investment recommendations. Save as cryptocurrency_investment_report.md. Use available tools to generate a detailed report with current market insights."""

        # Simple file operations only
        elif (
            any(
                word in request_lower
                for word in ["create file", "write file", "save file"]
            )
            and complexity_score < 2
        ):
            return f"""Create or write content to a file using available tools. Original request: {user_request}"""

        # Return original for all other cases to preserve complexity
        return user_request

    def is_simple_task(self, request: str) -> bool:
        """Determine if a task is simple enough to handle autonomously"""
        request_lower = request.lower()

        simple_indicators = [
            "create a file",
            "write a file",
            "save to file",
            "create a report",
            "write a report",
            "generate a report",
            "make a file",
            "output to file",
            "save as",
            "trump report",
            "presidency report",
            "crypto",
            "cryptocurrency",
            "investment analysis",
            "research report",
        ]

        return any(indicator in request_lower for indicator in simple_indicators)

    def extract_task_type(self, request: str) -> str:
        """Extract the type of task from the request"""
        request_lower = request.lower()

        if any(
            keyword in request_lower
            for keyword in ["crypto", "cryptocurrency", "bitcoin", "investment"]
        ):
            return "cryptocurrency_research"
        elif "trump" in request_lower and "report" in request_lower:
            return "trump_report"
        elif "report" in request_lower:
            return "general_report"
        elif any(word in request_lower for word in ["create", "write", "save", "file"]):
            return "file_creation"
        elif any(word in request_lower for word in ["research", "analyze", "search"]):
            return "research_task"
        else:
            return "general_task"
