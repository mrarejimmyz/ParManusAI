"""
Search Result Validation Module
Handles filtering and validation of search results for relevance
"""

import re
from typing import List, Tuple

from app.logger import logger


class SearchResultValidator:
    """Validates and filters search results for relevance"""

    def __init__(self):
        self.irrelevant_patterns = [
            # Language/grammar content
            r"如何|怎么|是什么意思|what does.*mean|how to type|input method",
            r"grammar|typing|language learning|dictionary|translation",
            # Shopping/sports unrelated to main topics
            r"pelota|tenis|tennis|sport|forum.*sport|shopping|buy|sale",
            r"precio|price|€|\$[0-9]|USD|EUR",
            # Chinese Q&A sites for basic questions
            r"百度知道|zhidao\.baidu|hinative\.com.*questions",
            # Login/website errors
            r"login|登录|sign in|error|404|page not found",
        ]

    async def validate_results(
        self, search_results: List[dict], task_description: str
    ) -> Tuple[List[dict], bool]:
        """Main validation method with pre-filtering and LLM validation"""
        try:
            # Pre-filter obvious irrelevant content
            pre_filtered = self._pre_filter_obvious_irrelevant(
                search_results, task_description
            )

            if len(pre_filtered) == 0:
                logger.warning("🚫 All results pre-filtered as irrelevant")
                return [], False

            # Use LLM for nuanced validation
            return await self._llm_validate_results(pre_filtered, task_description)
        except Exception as e:
            logger.warning(f"LLM validation failed, using fallback: {e}")
            return self._keyword_validate_results(search_results, task_description)

    def _pre_filter_obvious_irrelevant(
        self, search_results: List[dict], task_description: str
    ) -> List[dict]:
        """Pre-filter obviously irrelevant content"""
        task_lower = task_description.lower()

        # Define topic-specific keywords
        required_keywords = self._get_required_keywords(task_lower)

        filtered_results = []

        for result in search_results:
            title = result.get("title", "").lower()
            content = result.get("content", "").lower()
            full_text = title + " " + content

            # Check for irrelevant patterns
            if self._has_irrelevant_patterns(full_text):
                logger.info(
                    f"🚫 Pre-filtered: {result.get('title', '')[:50]}... (irrelevant pattern)"
                )
                continue

            # Check for required keywords if we have them
            if required_keywords and not self._has_relevant_keywords(
                full_text, required_keywords
            ):
                logger.info(
                    f"🚫 Pre-filtered: {result.get('title', '')[:50]}... (no relevant keywords)"
                )
                continue

            filtered_results.append(result)
            logger.info(f"✅ Pre-filter kept: {result.get('title', '')[:50]}...")

        logger.info(
            f"📊 Pre-filtering: {len(filtered_results)} kept, {len(search_results) - len(filtered_results)} filtered"
        )
        return filtered_results

    def _get_required_keywords(self, task_lower: str) -> List[str]:
        """Get required keywords based on task content"""
        if any(word in task_lower for word in ["trump", "elon", "musk"]):
            return [
                "trump",
                "elon",
                "musk",
                "politics",
                "government",
                "policy",
                "dispute",
                "conflict",
            ]
        elif any(word in task_lower for word in ["fort knox", "gold", "doge"]):
            return [
                "fort knox",
                "gold",
                "doge",
                "government",
                "efficiency",
                "treasury",
                "federal",
                "audit",
            ]
        elif "recession" in task_lower:
            return ["recession", "economic", "economy", "gdp", "financial"]
        return []

    def _has_irrelevant_patterns(self, text: str) -> bool:
        """Check if text contains irrelevant patterns"""
        return any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in self.irrelevant_patterns
        )

    def _has_relevant_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains relevant keywords"""
        return any(keyword in text for keyword in keywords)

    async def _llm_validate_results(
        self, search_results: List[dict], task_description: str
    ) -> Tuple[List[dict], bool]:
        """Use LLM to validate search result relevance"""
        try:
            from app.config import load_config
            from app.llm import LLM

            config = load_config()
            llm = LLM(config.llm)

            # Prepare results for LLM analysis
            results_text = ""
            for i, result in enumerate(search_results[:10]):
                title = result.get("title", "")
                content = result.get("content", result.get("snippet", ""))[:200]
                results_text += f"\n{i+1}. TITLE: {title}\n   CONTENT: {content}...\n"

            prompt = f"""Analyze which search results are relevant to this task:

TASK: {task_description}

SEARCH RESULTS:
{results_text}

FILTER OUT content that is:
- About grammar, language learning, or typing tutorials
- Login pages or website errors
- Completely unrelated topics (sports, shopping, travel when not relevant)
- Generic corporate pages without specific information
- Content in foreign languages that doesn't relate to the topic

KEEP content that is:
- Directly related to the task topic
- Contains relevant information or context about the subject matter
- News articles, reports, or analysis about the specific topic

OUTPUT FORMAT: For each result, output ONLY the number and either "RELEVANT" or "IRRELEVANT":
1. RELEVANT
2. IRRELEVANT
etc."""

            response = await llm.ask(prompt)

            # Parse LLM response
            relevant_results = []
            lines = response.strip().split("\n")

            for line in lines:
                line = line.strip()
                if not line or ". " not in line:
                    continue

                try:
                    parts = line.split(". ", 1)
                    if len(parts) == 2:
                        idx = int(parts[0]) - 1
                        decision = parts[1]

                        if (
                            0 <= idx < len(search_results)
                            and "RELEVANT" in decision.upper()
                        ):
                            search_results[idx]["relevance_score"] = 5
                            relevant_results.append(search_results[idx])
                            logger.info(
                                f"✅ LLM kept: {search_results[idx].get('title', '')[:50]}..."
                            )
                        else:
                            logger.warning(
                                f"🚫 LLM filtered: {search_results[idx].get('title', '')[:50]}..."
                            )
                except (ValueError, IndexError):
                    continue

            relevant_results.sort(
                key=lambda x: x.get("relevance_score", 0), reverse=True
            )
            has_good_data = len(relevant_results) > 0

            logger.info(
                f"🤖 LLM validation: {len(relevant_results)} relevant, {len(search_results) - len(relevant_results)} filtered out"
            )
            return relevant_results, has_good_data

        except Exception as e:
            logger.error(f"Error in LLM validation: {e}")
            return self._keyword_validate_results(search_results, task_description)

    def _keyword_validate_results(
        self, search_results: List[dict], task_description: str
    ) -> Tuple[List[dict], bool]:
        """Fallback keyword-based validation"""
        try:
            task_lower = task_description.lower()
            relevant_keywords = self._get_required_keywords(task_lower)

            if not relevant_keywords:
                relevant_keywords = ["data", "analysis", "report", "research"]

            relevant_results = []

            for result in search_results:
                content = result.get("content", "") + " " + result.get("title", "")
                content_lower = content.lower()

                # Check relevance score
                relevance_score = sum(
                    1 for keyword in relevant_keywords if keyword in content_lower
                )

                if relevance_score > 0:
                    result["relevance_score"] = relevance_score
                    relevant_results.append(result)

            relevant_results.sort(
                key=lambda x: x.get("relevance_score", 0), reverse=True
            )
            has_good_data = len(relevant_results) > 0 and any(
                r.get("relevance_score", 0) >= 2 for r in relevant_results
            )

            logger.info(
                f"📊 Keyword validation: {len(relevant_results)} relevant, {len(search_results) - len(relevant_results)} filtered out"
            )
            return relevant_results, has_good_data

        except Exception as e:
            logger.error(f"Error in keyword validation: {e}")
            return search_results, len(search_results) > 0
