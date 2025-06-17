"""
Search Query Generator Module
Handles intelligent generation of search queries for different tasks
"""

import re

from app.logger import logger


class SearchQueryGenerator:
    """Generates intelligent search queries based on task analysis"""

    async def generate_query(self, task_description: str, step: str) -> str:
        """Generate focused search query using LLM intelligence"""
        try:
            return await self._llm_generate_query(task_description, step)
        except Exception as e:
            logger.error(f"Error generating LLM search query: {e}")
            return self._fallback_query(task_description, step)

    async def _llm_generate_query(self, task_description: str, step: str) -> str:
        """Use LLM to intelligently generate search query"""
        try:
            from app.config import load_config
            from app.llm_hybrid import HybridOllamaLLM

            config = load_config()
            llm = HybridOllamaLLM(config)

            prompt = f"""Analyze this task and generate the best web search query:

TASK: {task_description}
CURRENT STEP: {step}

Create a focused, specific search query that will find relevant and current information.

GUIDELINES:
1. Extract the core topic/subject from the task
2. Include relevant keywords and entities
3. Add current year (2025) if it's about recent events
4. Make it specific enough to avoid irrelevant results
5. Keep it concise but comprehensive

EXAMPLES:
- Task: "why are trump and elon musk fighting now" → "Trump Elon Musk conflict dispute 2025"
- Task: "recession status analysis" → "US recession indicators 2025 economic status"
- Task: "why gold cannot be counted at fort knox by elon musk DOGE" → "Fort Knox gold audit DOGE Elon Musk government efficiency"

OUTPUT: Return ONLY the search query, nothing else."""

            response = await llm.ask(prompt)

            # Clean up the response
            search_query = response.strip().strip("\"'`")

            # Ensure reasonable length
            if len(search_query) > 100:
                words = search_query.split()[:10]
                search_query = " ".join(words)

            logger.info(f"🤖 LLM generated search query: '{search_query}'")
            return search_query

        except Exception as e:
            logger.error(f"Error in LLM search query generation: {e}")
            raise

    def _fallback_query(self, task_description: str, step: str) -> str:
        """Fallback method if LLM generation fails"""
        try:
            # Extract meaningful terms
            stop_words = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "being",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
            }

            words = re.findall(r"\b\w+\b", task_description.lower())
            meaningful_words = [
                w for w in words if w not in stop_words and len(w) > 2
            ]  # Take the first 5-6 meaningful words
            search_terms = meaningful_words[:6]

            # Add current year for recent topics
            search_query = " ".join(search_terms)
            if any(
                word in task_description.lower()
                for word in ["current", "now", "recent", "today", "latest"]
            ):
                search_query += " 2025"

            logger.info(f"🔄 Fallback search query: '{search_query}'")
            return search_query

        except Exception as e:
            logger.error(f"Error in fallback search query: {e}")
            return "current news analysis 2025"
