"""
Search Result Pre-Filter Module
Advanced filtering logic for obviously irrelevant search results
"""

import re
from typing import Dict, List, Tuple

from app.logger import logger


class SearchResultPreFilter:
    """
    Specialized module for pre-filtering obviously irrelevant search results
    before expensive LLM analysis
    """

    def __init__(self):
        self.irrelevant_patterns = self._initialize_irrelevant_patterns()
        self.topic_keywords = self._initialize_topic_keywords()

    def _initialize_irrelevant_patterns(self) -> List[str]:
        """Initialize patterns that indicate irrelevant content"""
        return [
            # Language/grammar content
            r"如何|怎么|是什么意思|what does.*mean|how to type|input method",
            r"grammar|typing|language learning|dictionary|translation",
            r"波浪号|tilde|word.*format|formatting.*word",
            # Shopping/sports unrelated to main topics
            r"pelota|tenis|tennis|sport|forum.*sport|shopping|buy|sale",
            r"precio|price|€|\$[0-9]|USD|EUR|商品|购买",
            # Chinese Q&A sites for basic questions
            r"百度知道|zhidao\.baidu|hinative\.com.*questions",
            # Login/website errors
            r"login|登录|sign in|error|404|page not found|access denied",
            r"register|注册|sign up|create account|forgot password",
            # Generic promotional content
            r"click here|download now|free trial|advertisement|广告",
            r"subscribe|newsletter|mailing list|follow us|social media",
            # Technical documentation unrelated to topics
            r"api documentation|code example|programming tutorial|developer guide",
            r"installation guide|setup tutorial|configuration file",
        ]

    def _initialize_topic_keywords(self) -> Dict[str, List[str]]:
        """Initialize keywords for different topic categories"""
        return {
            "political": [
                "trump",
                "biden",
                "elon",
                "musk",
                "politics",
                "government",
                "policy",
                "administration",
                "president",
                "congress",
                "senate",
            ],
            "economic": [
                "recession",
                "economic",
                "economy",
                "gdp",
                "financial",
                "market",
                "inflation",
                "unemployment",
                "federal reserve",
                "treasury",
                "fiscal",
            ],
            "fort_knox": [
                "fort knox",
                "gold",
                "doge",
                "treasury",
                "federal",
                "audit",
                "government efficiency",
                "accountability",
                "reserves",
            ],
            "technology": [
                "tesla",
                "spacex",
                "twitter",
                "x platform",
                "tech",
                "innovation",
                "artificial intelligence",
                "social media",
                "electric vehicle",
            ],
            "travel": [
                "waterloo",
                "kathmandu",
                "travel",
                "trip",
                "tourism",
                "visit",
                "destination",
                "hotel",
                "accommodation",
                "attractions",
            ],
        }

    def pre_filter_results(
        self, search_results: List[Dict], task_description: str
    ) -> Tuple[List[Dict], int]:
        """
        Pre-filter search results to remove obviously irrelevant content

        Args:
            search_results: List of search result dictionaries
            task_description: The task description to match against

        Returns:
            Tuple of (filtered_results, number_filtered_out)
        """
        if not search_results:
            return [], 0

        filtered_results = []
        filtered_count = 0

        # Determine topic category
        topic_category = self._determine_topic_category(task_description)
        required_keywords = self.topic_keywords.get(topic_category, [])

        for result in search_results:
            if self._is_obviously_irrelevant(
                result, task_description, required_keywords
            ):
                filtered_count += 1
                logger.info(
                    f"🚫 Pre-filtered: {result.get('title', '')[:50]}... (irrelevant pattern)"
                )
            else:
                filtered_results.append(result)
                logger.info(f"✅ Pre-filter kept: {result.get('title', '')[:50]}...")

        logger.info(
            f"📊 Pre-filtering: {len(filtered_results)} kept, {filtered_count} filtered"
        )
        return filtered_results, filtered_count

    def _determine_topic_category(self, task_description: str) -> str:
        """Determine the main topic category for keyword matching"""
        task_lower = task_description.lower()

        if any(word in task_lower for word in ["trump", "elon", "musk", "biden"]):
            return "political"
        elif any(word in task_lower for word in ["recession", "economic", "gdp"]):
            return "economic"
        elif any(word in task_lower for word in ["fort knox", "gold", "doge"]):
            return "fort_knox"
        elif any(word in task_lower for word in ["tesla", "spacex", "twitter", "tech"]):
            return "technology"
        elif any(
            word in task_lower for word in ["waterloo", "kathmandu", "travel", "trip"]
        ):
            return "travel"
        else:
            return "general"

    def _is_obviously_irrelevant(
        self, result: Dict, task_description: str, required_keywords: List[str]
    ) -> bool:
        """Check if a result is obviously irrelevant"""
        title = result.get("title", "").lower()
        content = result.get("content", "").lower()
        full_text = title + " " + content

        # Check for irrelevant patterns
        for pattern in self.irrelevant_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                return True

        # Check for required keywords if we have them
        if required_keywords:
            has_relevant_keyword = any(
                keyword in full_text for keyword in required_keywords
            )
            if not has_relevant_keyword:
                return True

        # Additional checks for specific problematic content
        if self._has_problematic_content(full_text):
            return True

        return False

    def _has_problematic_content(self, text: str) -> bool:
        """Check for additional problematic content patterns"""
        problematic_indicators = [
            # Too short or generic content
            len(text.strip()) < 50,
            # Mostly non-English content when English expected
            self._is_mostly_non_english(text),
            # Generic error messages
            "page not found" in text or "404" in text,
            "login required" in text or "access denied" in text,
            # Pure promotional content
            text.count("buy") + text.count("sale") + text.count("discount") > 3,
        ]

        return any(problematic_indicators)

    def _is_mostly_non_english(self, text: str) -> bool:
        """Simple check for non-English content"""
        # Count Chinese/Japanese characters
        non_latin_chars = len(
            re.findall(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]", text)
        )
        total_chars = len(text)

        if total_chars == 0:
            return False

        # If more than 30% non-Latin characters, consider mostly non-English
        return (non_latin_chars / total_chars) > 0.3

    def get_filter_statistics(
        self, original_count: int, filtered_count: int
    ) -> Dict[str, int]:
        """Get statistics about the filtering process"""
        return {
            "original_count": original_count,
            "kept_count": original_count - filtered_count,
            "filtered_count": filtered_count,
            "retention_rate": (
                ((original_count - filtered_count) / original_count * 100)
                if original_count > 0
                else 0
            ),
        }
