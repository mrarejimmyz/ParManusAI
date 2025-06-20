"""
Query Analysis Module for Manus Agent
Handles simple query detection and routing logic.
"""

import re
from typing import List

from app.logger import logger


class QueryAnalyzer:
    """Analyzes user queries to determine complexity and routing."""

    def __init__(self, llm=None):
        self.llm = llm
        self._simple_patterns = [
            # Mathematical questions
            r"\b\d+\s*[\+\-\*\/]\s*\d+",
            r"what\s+is\s+\d+",
            r"calculate",
            r"math",
            # Simple factual questions
            r"^what\s+is\s+(?:your\s+)?name",
            r"^who\s+are\s+you",
            r"^what\s+can\s+you\s+do",
            r"^hello",
            r"^hi\b",
            # Quick recommendations that can be answered from knowledge
            r"^name\s+\d+\s+\w+\s+to\s+(?:invest|buy|use)",
            r"^recommend\s+(?:a|one|\d+)",
            r"^suggest\s+(?:a|one|\d+)",
            r"^what\s+(?:is\s+)?(?:the\s+)?best\s+\w+",
            # Simple explanations
            r"^explain\s+\w+\s+in\s+\w+\s+words",
            r"^define\s+\w+",
            r"^what\s+does\s+\w+\s+mean",
        ]

        # Patterns that indicate complex queries requiring tool execution
        self._complex_patterns = [
            r"print.*hello.*world",
            r"print.*['\"].*['\"]",
            r"execute.*python",
            r"run.*python",
            r"python.*print",
            r"use.*python",
            r"python.*script",
            r"create.*script",
            r"write.*code",
            r"tool.*execute",
            r"run.*code",
            r"execute.*code",
        ]

    async def is_simple_query(self, user_request: str) -> bool:
        """Detect if this is a simple query that doesn't need complex planning."""
        request_lower = user_request.lower().strip()

        # First check for complex patterns - these override simple classification
        for pattern in self._complex_patterns:
            if re.search(pattern, request_lower):
                logger.info(
                    "🔍 Pattern-based detection: This is a complex query requiring tool execution"
                )
                return False

        # Check simple patterns
        for pattern in self._simple_patterns:
            if re.search(pattern, request_lower):
                logger.info("🔍 Pattern-based detection: This is a simple query")
                return True

        # For queries that don't match patterns, use fallback
        return self._fallback_is_simple_query(user_request)

    def _fallback_is_simple_query(self, user_request: str) -> bool:
        """Fallback simple query detection using basic heuristics."""
        request_lower = user_request.lower()

        # Check for short queries (likely simple)
        if len(request_lower.split()) <= 6:
            simple_keywords = [
                "what",
                "who",
                "when",
                "where",
                "how",
                "why",
                "is",
                "are",
                "can",
                "do",
                "does",
            ]
            if any(request_lower.startswith(kw) for kw in simple_keywords):
                return True

        return False

    async def handle_simple_query(self, user_request: str) -> str:
        """Handle simple queries directly with LLM without complex planning."""
        logger.info(f"🚀 Handling simple query directly: {user_request}")

        # Ensure LLM is available
        if not self.llm:
            return "I need an LLM to answer your question."

        # Create a focused prompt for simple queries
        simple_prompt = f"""You are Manus, a helpful AI assistant. The user has asked a simple, direct question that needs a clear, concise answer.

User question: {user_request}

Please provide a direct, helpful answer. If this is asking for a recommendation (like crypto to invest), provide ONE specific recommendation with a brief reason why. Keep your response concise and actionable.

If you cannot provide a specific recommendation due to lack of current market data, clearly state this limitation and provide general guidance instead."""

        try:
            response = await self.llm.ask([{"role": "user", "content": simple_prompt}])
            return response
        except Exception as e:
            logger.error(f"Error in simple query handling: {e}")
            return f"I encountered an error while processing your question: {str(e)}"
