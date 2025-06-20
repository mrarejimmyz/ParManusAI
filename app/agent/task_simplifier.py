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
        """Autonomously simplify complex requests into direct, actionable tasks"""
        request_lower = user_request.lower()

        # Cryptocurrency research simplification
        if any(
            keyword in request_lower
            for keyword in [
                "crypto",
                "cryptocurrency",
                "bitcoin",
                "ethereum",
                "investment",
            ]
        ):
            return """Create a comprehensive cryptocurrency investment report for 2025. Include market analysis, top cryptocurrencies (Bitcoin, Ethereum, Solana, Cardano), investment strategies (conservative, balanced, aggressive portfolios), risk assessment, and specific investment recommendations. Save as cryptocurrency_investment_report.md. Use simple Python code to generate a detailed report with current market insights."""

        # Trump report simplification
        elif "trump" in request_lower and "report" in request_lower:
            return """Create a comprehensive Trump presidency report using simple, direct Python code. Write the content as a string variable and save it to trump_presidency_report.md file. Focus on: overview, key events, major policies, and conclusion. Keep the code simple and avoid complex functions or imports."""

        # General report simplification
        elif "report" in request_lower:
            return f"""Create a report using simple Python code. Write the content as a string variable and save it to a .md file. Original request: {user_request}"""

        # File creation simplification
        elif any(word in request_lower for word in ["create", "write", "save", "file"]):
            return f"""Create or write content to a file using simple Python file operations. Use basic 'with open()' syntax. Original request: {user_request}"""

        # Research task simplification
        elif any(
            word in request_lower for word in ["research", "analyze", "search", "find"]
        ):
            return f"""Perform research and create a comprehensive report. Use simple Python code to generate content and save to a file. Focus on providing detailed, actionable information. Original request: {user_request}"""

        # Return original if no simplification patterns match
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
