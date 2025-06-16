"""
Optimized Bulletproof Search Implementation
Focused on topic relevance and content quality filtering
"""

from typing import Dict, List, Optional
from urllib.parse import quote

import feedparser
import requests

from app.logger import logger


class OptimizedBulletproofSearch:
    """
    Optimized search with strict topic relevance filtering
    """

    def __init__(self):
        self.session = requests.Session()
        # Set realistic headers to avoid blocking
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
            }
        )

    async def perform_google_search(self, query: str) -> Dict:
        """
        Optimized search with strict topic filtering
        """
        logger.info(f"🔍 Optimized bulletproof search for: {query}")

        all_results = []

        # 1. DuckDuckGo instant answers (for factual content)
        ddg_instant = self._search_duckduckgo_instant(query)
        if ddg_instant:
            all_results.extend(ddg_instant)
            logger.info(f"✅ DuckDuckGo instant returned {len(ddg_instant)} results")

        # 2. Wikipedia API (for encyclopedic content)
        wiki_results = self._search_wikipedia_api(query)
        if wiki_results:
            all_results.extend(wiki_results)
            logger.info(f"✅ Wikipedia API returned {len(wiki_results)} results")

        # 3. Highly filtered news sources (only topic-relevant)
        news_results = self._search_filtered_news(query)
        if news_results:
            all_results.extend(news_results)
            logger.info(f"✅ Filtered news returned {len(news_results)} results")

        if all_results:
            # Remove duplicates and sort by relevance
            unique_results = []
            seen_urls = set()
            for result in all_results:
                if result.get("url") and result["url"] not in seen_urls:
                    seen_urls.add(result["url"])
                    unique_results.append(result)

            # Sort by relevance score
            unique_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)

            logger.info(f"🎯 Total unique results: {len(unique_results)}")
            return {
                "success": True,
                "query": query,
                "results": unique_results[:8],  # Top 8 most relevant
                "method": "optimized_bulletproof_apis",
                "real_search": True,
            }
        else:
            logger.warning(f"⚠️ All optimized APIs failed for query: {query}")
            return {
                "success": False,
                "query": query,
                "results": [],
                "method": "no_fallback",
                "error": "All verified search APIs failed - no fake results provided",
                "real_search": False,
            }

    def _search_duckduckgo_instant(self, query: str) -> List[Dict]:
        """
        Use DuckDuckGo Instant Answer API for factual content
        """
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_redirect": "1",
                "no_html": "1",
                "skip_disambig": "1",
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"🔍 DuckDuckGo API response keys: {list(data.keys())}")

            # Debug: print what we get
            if data.get("Abstract"):
                logger.info(f"📄 Abstract found: {data.get('Heading', 'No heading')}")
            if data.get("RelatedTopics"):
                logger.info(
                    f"🔗 Related topics found: {len(data.get('RelatedTopics', []))}"
                )

            results = []

            # Check for instant answer
            if data.get("Abstract"):
                relevance = self._calculate_topic_relevance(
                    query, data.get("Heading", ""), data.get("Abstract", "")
                )
                logger.info(f"🎯 Abstract relevance: {relevance}")
                if relevance >= 2:  # Lower threshold for broader coverage
                    results.append(
                        {
                            "title": data.get("Heading", query),
                            "url": data.get(
                                "AbstractURL",
                                "https://duckduckgo.com/?q=" + quote(query),
                            ),
                            "snippet": data.get("Abstract")[:300],
                            "source": "DuckDuckGo Instant Answer",
                            "relevance": relevance + 3,  # Boost instant answers
                        }
                    )

            # Check for related topics
            for topic in data.get("RelatedTopics", [])[:3]:  # Check more topics
                if isinstance(topic, dict) and topic.get("FirstURL"):
                    text = topic.get("Text", "")
                    title = text.split(" - ")[0] if " - " in text else text
                    relevance = self._calculate_topic_relevance(query, title, text)
                    logger.info(f"🔗 Topic relevance: {relevance} for '{title[:50]}'")

                    if relevance >= 1:  # Very low threshold for topics
                        results.append(
                            {
                                "title": title[:100],
                                "url": topic["FirstURL"],
                                "snippet": text[:300],
                                "source": "DuckDuckGo Related Topic",
                                "relevance": relevance,
                            }
                        )

            return results

        except Exception as e:
            logger.warning(f"DuckDuckGo instant API error: {str(e)}")
            return []

    def _search_wikipedia_api(self, query: str) -> List[Dict]:
        """
        Enhanced Wikipedia search with relevance filtering
        """
        try:
            # Extract main topic for Wikipedia search
            main_topic = self._extract_main_topic_for_wikipedia(query)
            logger.info(f"🔍 Wikipedia search for topic: {main_topic}")

            # Try direct page summary first
            search_url = (
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(main_topic)}"
            )

            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("extract"):
                    relevance = self._calculate_topic_relevance(
                        query, data.get("title", ""), data.get("extract", "")
                    )
                    logger.info(f"📖 Wikipedia relevance: {relevance}")
                    if relevance >= 1:  # Lower threshold
                        return [
                            {
                                "title": data.get("title", query),
                                "url": data.get("content_urls", {})
                                .get("desktop", {})
                                .get("page", ""),
                                "snippet": data.get("extract", "")[:300],
                                "source": "Wikipedia",
                                "relevance": relevance + 2,  # Boost Wikipedia
                            }
                        ]

            return []

        except Exception as e:
            logger.warning(f"Wikipedia API error: {str(e)}")
            return []

    def _search_filtered_news(self, query: str) -> List[Dict]:
        """
        Highly filtered news search - only topic-relevant content
        """
        results = []
        main_topics = self._extract_topic_keywords(query)
        logger.info(f"📰 News search for topics: {main_topics}")

        # BBC News RSS with strict filtering
        try:
            feeds = [
                ("http://feeds.bbci.co.uk/news/rss.xml", "BBC News"),
                ("http://feeds.bbci.co.uk/news/world/rss.xml", "BBC World News"),
            ]

            for feed_url, source_name in feeds:
                try:
                    response = self.session.get(feed_url, timeout=10)
                    response.raise_for_status()

                    feed = feedparser.parse(response.content)
                    logger.info(f"📰 {source_name}: found {len(feed.entries)} entries")

                    for entry in feed.entries[:20]:  # Check more entries
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")

                        # Lower threshold for broader news coverage
                        relevance_score = self._calculate_strict_news_relevance(
                            query, title, summary, main_topics
                        )

                        logger.info(
                            f"📰 News relevance: {relevance_score} for '{title[:50]}'"
                        )

                        # Include relevant news (lower threshold)
                        if relevance_score >= 3:  # Much lower threshold
                            results.append(
                                {
                                    "title": title,
                                    "url": entry.get("link", ""),
                                    "snippet": summary[:300],
                                    "source": source_name,
                                    "published": entry.get("published", ""),
                                    "relevance": relevance_score,
                                }
                            )

                except Exception as e:
                    logger.warning(f"{source_name} RSS error: {str(e)}")
                    continue

        except Exception as e:
            logger.warning(f"News search error: {str(e)}")

        # Sort by relevance and return results
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        logger.info(f"📰 Total news results after filtering: {len(results)}")
        return results[:5]  # Return top 5 most relevant news items

    def _extract_topic_keywords(self, query: str) -> Dict[str, List[str]]:
        """Extract main topic keywords from query"""
        # For general queries like "latest news today", return broad topics
        query_lower = query.lower()

        if any(
            word in query_lower
            for word in ["news", "latest", "today", "breaking", "current"]
        ):
            return {
                "general": ["news", "latest", "today", "current", "breaking"],
                "topics": ["world", "politics", "economy", "technology", "health"],
            }

        # Extract keywords from the query
        words = query_lower.split()
        return {"general": words, "topics": words}

    def _extract_main_topic_for_wikipedia(self, query: str) -> str:
        """Extract the main topic for Wikipedia search"""
        # Remove common words and focus on the main topic
        stop_words = {
            "latest",
            "news",
            "today",
            "breaking",
            "current",
            "analysis",
            "report",
        }
        words = [w for w in query.lower().split() if w not in stop_words]

        if not words:
            return "current events"

        return " ".join(words[:2])  # Take first 1-2 meaningful words

    def _calculate_topic_relevance(self, query: str, title: str, content: str) -> int:
        """
        Calculate topic relevance score (0-10)
        More lenient scoring for broader coverage
        """
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        content_words = set(content.lower().split())

        # Count word matches
        title_matches = len(query_words.intersection(title_words))
        content_matches = len(query_words.intersection(content_words))

        # Base relevance
        relevance = title_matches * 2 + content_matches

        # Boost for general news queries
        if any(
            word in query.lower() for word in ["news", "latest", "today", "current"]
        ):
            if any(
                word in title.lower() or word in content.lower()
                for word in ["news", "latest", "today", "current", "breaking"]
            ):
                relevance += 3

        return min(relevance, 10)  # Cap at 10

    def _calculate_strict_news_relevance(
        self, query: str, title: str, summary: str, main_topics: Dict
    ) -> int:
        """
        Calculate news relevance with broader criteria
        """
        relevance = 0

        # Check for general news terms
        news_terms = ["news", "latest", "today", "breaking", "current", "update"]
        query_lower = query.lower()
        title_lower = title.lower()
        summary_lower = summary.lower()

        # Base relevance for news content
        if any(term in title_lower or term in summary_lower for term in news_terms):
            relevance += 3

        # Check for topic matches
        for topic_list in main_topics.values():
            for topic in topic_list:
                if topic in title_lower:
                    relevance += 2
                if topic in summary_lower:
                    relevance += 1

        # Check for recent date indicators
        if any(
            term in title_lower or term in summary_lower
            for term in ["today", "2025", "june"]
        ):
            relevance += 2

        return min(relevance, 10)  # Cap at 10
