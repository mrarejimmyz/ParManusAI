"""
Search Strategy Analyzer
LLM-driven analysis of user queries to determine optimal search strategies
"""

import json
import re
from typing import Dict

from app.logger import logger


class SearchStrategyAnalyzer:
    """
    Analyzes user queries using LLM to determine the best search approach
    """

    def __init__(self, llm=None):
        self.llm = llm

    async def analyze_query(self, query: str) -> Dict:
        """
        Use LLM to analyze the query and determine the optimal search strategy
        """
        try:
            if not self.llm:
                return self._get_default_strategy(query)

            prompt = f"""
            Analyze this search query and determine the optimal search strategy:

            Query: "{query}"

            Consider these factors:
            1. Is this a website review/analysis request? (contains domain like .com, .xyz + words like review, analyze)
            2. Is this a news/current events search? (contains news, latest, breaking, today)
            3. Is this a factual information lookup? (contains what is, how to, facts about)
            4. Is this location-specific or global?
            5. What type of sources would be most valuable?

            Available search methods:
            - direct_website_access: For reviewing specific websites (extract URL and access directly)
            - news_search: For current news and events (use news sources)
            - web_search: For general web information (use web search engines)
            - knowledge_search: For factual/reference information (use Wikipedia, encyclopedias)
            - combined_search: For comprehensive research (use all sources)

            Respond with JSON only:
            {{
                "approach": "direct_website_access|news_search|web_search|knowledge_search|combined_search",
                "reasoning": "why this approach is best",
                "search_queries": ["specific query 1", "specific query 2", "specific query 3"],
                "target_url": "https://example.com (only if direct website access detected)",
                "priority_sources": ["web", "news", "knowledge"],
                "content_focus": "summary|detailed"
            }}            """

            # Format the prompt as a message for the LLM
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.ask(messages)

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
                    strategy = json.loads(json_text)

                    # Ensure search_queries are strings
                    if "search_queries" in strategy:
                        strategy["search_queries"] = [
                            str(q) for q in strategy["search_queries"]
                        ]

                    # Extract website URL if detected
                    if strategy.get(
                        "approach"
                    ) == "direct_website_access" and not strategy.get("target_url"):
                        url_pattern = r"([a-zA-Z0-9-]+\.[a-zA-Z]{2,})"
                        matches = re.findall(url_pattern, query)
                        if matches:
                            strategy["target_url"] = f"https://{matches[0]}"

                    return strategy

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM strategy JSON: {e}")
                    logger.info(f"Raw response: {response[:200]}...")
                    return self._get_default_strategy(query)

            return self._get_default_strategy(query)

        except Exception as e:
            logger.warning(f"Failed to analyze query with LLM: {e}")
            return self._get_default_strategy(query)

    def _get_default_strategy(self, query: str) -> Dict:
        """
        Enhanced default strategy when LLM analysis fails
        """
        query_lower = query.lower()

        # Detect website review requests more accurately
        has_domain = any(
            domain in query_lower
            for domain in [
                ".com",
                ".xyz",
                ".org",
                ".net",
                ".io",
                ".co",
                ".tech",
                ".app",
                ".dev",
            ]
        )
        has_review_intent = any(
            action in query_lower
            for action in ["review", "analyze", "check", "visit", "look at", "examine"]
        )

        if has_domain and has_review_intent:
            # Extract the domain from the query
            url_pattern = r"([a-zA-Z0-9-]+\.[a-zA-Z]{2,})"
            matches = re.findall(url_pattern, query)
            target_url = matches[0] if matches else None

            return {
                "approach": "direct_website_access",
                "reasoning": "Detected website review request with domain and review intent",
                "search_queries": [query],
                "target_url": f"https://{target_url}" if target_url else None,
                "priority_sources": ["web"],
                "content_focus": "detailed",
            }
        elif any(
            term in query_lower
            for term in ["news", "latest", "breaking", "today", "current"]
        ):
            return {
                "approach": "news_search",
                "reasoning": "Detected news query based on temporal keywords",
                "search_queries": [query],
                "priority_sources": ["news"],
                "content_focus": "summary",
            }
        elif any(
            term in query_lower for term in ["what is", "how to", "define", "explain"]
        ):
            return {
                "approach": "knowledge_search",
                "reasoning": "Detected knowledge/factual query",
                "search_queries": [query],
                "priority_sources": ["knowledge", "web"],
                "content_focus": "summary",
            }
        else:
            return {
                "approach": "combined_search",
                "reasoning": "Default comprehensive search strategy for general queries",
                "search_queries": [query],
                "priority_sources": ["web", "news"],
                "content_focus": "summary",
            }
