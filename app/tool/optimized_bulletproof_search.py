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
    Optimized search with LLM-driven dynamic source selection and filtering
    """

    def __init__(self, llm=None):
        self.session = requests.Session()
        self.llm = llm  # For dynamic reasoning
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
        
        # Dynamic news sources by region/topic
        self.news_sources = {
            "global": [
                ("http://feeds.bbci.co.uk/news/rss.xml", "BBC News"),
                ("http://feeds.bbci.co.uk/news/world/rss.xml", "BBC World News"),
                ("https://rss.cnn.com/rss/edition.rss", "CNN International"),
            ],
            "asia": [
                ("http://feeds.bbci.co.uk/news/world/asia/rss.xml", "BBC Asia"),
                ("https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "Times of India"),
                ("http://english.alarabiya.net/en/rss.xml", "Al Arabiya English"),
            ],
            "nepal": [
                ("https://kathmandupost.com/rss", "Kathmandu Post"),
                ("https://myrepublica.nagariknetwork.com/rss/", "My Republica"),
                ("https://thehimalayantimes.com/rss", "The Himalayan Times"),
                ("http://feeds.bbci.co.uk/news/world/asia/rss.xml", "BBC Asia"),
            ],
            "india": [
                ("https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "Times of India"),
                ("https://www.hindustantimes.com/rss/topnews/rssfeed.xml", "Hindustan Times"),
                ("https://indianexpress.com/print/front-page/feed/", "Indian Express"),
                ("http://feeds.bbci.co.uk/news/world/asia/rss.xml", "BBC Asia"),
            ],
            "technology": [
                ("https://feeds.arstechnica.com/arstechnica/index", "Ars Technica"),
                ("https://www.wired.com/feed/rss", "Wired"),
                ("https://techcrunch.com/feed/", "TechCrunch"),
            ],
            "business": [                ("https://feeds.bloomberg.com/markets/news.rss", "Bloomberg Markets"),
                ("https://www.ft.com/rss/home", "Financial Times"),
                ("https://www.reuters.com/business/finance", "Reuters Business"),
            ]
        }

    async def perform_google_search(self, query: str) -> Dict:
        """
        Optimized search with dynamic source selection based on query analysis
        """
        logger.info(f"🔍 Optimized bulletproof search for: {query}")

        all_results = []

        # 1. Analyze query to determine optimal sources
        search_strategy = await self._analyze_query_and_select_sources(query)
        logger.info(f"🧠 Search strategy: {search_strategy.get('approach', 'default')}")

        # 2. DuckDuckGo instant answers (for factual content)
        ddg_instant = self._search_duckduckgo_instant(query)
        if ddg_instant:
            all_results.extend(ddg_instant)
            logger.info(f"✅ DuckDuckGo instant returned {len(ddg_instant)} results")

        # 3. Wikipedia API (for encyclopedic content)
        wiki_results = self._search_wikipedia_api(query)
        if wiki_results:
            all_results.extend(wiki_results)
            logger.info(f"✅ Wikipedia API returned {len(wiki_results)} results")

        # 4. Dynamic news sources based on query analysis
        news_results = await self._search_dynamic_news_sources(query, search_strategy)
        if news_results:
            all_results.extend(news_results)
            logger.info(f"✅ Dynamic news sources returned {len(news_results)} results")

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
                "method": "optimized_dynamic_search",
                "real_search": True,
                "strategy": search_strategy,
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
                                .get("page", ""),                                "snippet": data.get("extract", "")[:300],
                                "source": "Wikipedia",
                                "relevance": relevance + 2,  # Boost Wikipedia
                            }
                        ]

            return []

        except Exception as e:
            logger.warning(f"Wikipedia API error: {str(e)}")
            return []

    def _calculate_enhanced_relevance(self, query: str, title: str, content: str, strategy: Dict) -> int:
        """
        Enhanced relevance calculation considering search strategy
        """
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        content_words = set(content.lower().split())

        # Base relevance from word matches
        title_matches = len(query_words.intersection(title_words))
        content_matches = len(query_words.intersection(content_words))
        relevance = title_matches * 3 + content_matches

        # Location-specific boosting
        if strategy.get("location_specific"):
            target_region = strategy.get("target_region", "").lower()
            if target_region:
                if target_region in title.lower():
                    relevance += 5  # Strong boost for location in title
                if target_region in content.lower():
                    relevance += 3  # Moderate boost for location in content

        # General news terms boost
        news_terms = ["news", "latest", "today", "breaking", "current", "update", "report"]
        if any(term in title.lower() or term in content.lower() for term in news_terms):
            relevance += 2

        # Recency indicators
        recent_terms = ["today", "2025", "this week", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if any(term in title.lower() or term in content.lower() for term in recent_terms):
            relevance += 2

        return min(relevance, 15)  # Cap at 15

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

        # For general news queries, give base relevance to all current news
        query_lower = query.lower()
        if any(
            term in query_lower
            for term in ["news", "latest", "today", "breaking", "current"]
        ):
            relevance += 4  # Higher base score for general news queries

        # Check for general news terms in content
        news_terms = ["today", "breaking", "latest", "current", "update", "report"]
        title_lower = title.lower()
        summary_lower = summary.lower()

        # Base relevance for any news content when looking for "news"
        if any(term in title_lower or term in summary_lower for term in news_terms):
            relevance += 2

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
            relevance += 1

        return min(relevance, 10)  # Cap at 10

    async def _analyze_query_and_select_sources(self, query: str) -> Dict:
        """
        Use LLM to analyze query and determine optimal news sources
        """
        try:
            if not self.llm:
                return self._fallback_source_selection(query)
                
            prompt = f"""
            Analyze this search query and recommend the best news sources and approach:
            
            Query: "{query}"
            
            Available source categories:
            - global: General international news (BBC, CNN)
            - asia: Asian regional news including South Asia
            - nepal: Nepal-specific news sources (Kathmandu Post, My Republica)
            - india: India-specific news sources (Times of India, Hindustan Times)
            - technology: Tech news (TechCrunch, Wired, Ars Technica)
            - business: Business/financial news (Bloomberg, Financial Times)
            
            Respond with JSON:
            {{
                "primary_categories": ["category1", "category2"],
                "approach": "description of search strategy",
                "location_specific": true/false,
                "target_region": "region name if applicable"
            }}
            
            For location-specific queries like "Nepal news", prioritize regional sources.
            For general news, use global sources.
            For specific topics, use topic-specific sources.
            """
            
            response = await self.llm.ask(prompt)
            
            # Extract JSON from response
            import re
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    strategy = json.loads(json_match.group())
                    return strategy
                except json.JSONDecodeError:
                    pass
                    
            return self._fallback_source_selection(query)
            
        except Exception as e:
            logger.warning(f"Failed to analyze query with LLM: {e}")
            return self._fallback_source_selection(query)

    def _fallback_source_selection(self, query: str) -> Dict:
        """
        Fallback source selection when LLM is not available
        """
        query_lower = query.lower()
        
        # Location-based detection
        if "nepal" in query_lower:
            return {
                "primary_categories": ["nepal", "asia"],
                "approach": "Nepal-focused search with regional backup",
                "location_specific": True,
                "target_region": "nepal"
            }
        elif "india" in query_lower:
            return {
                "primary_categories": ["india", "asia"],
                "approach": "India-focused search with regional backup",
                "location_specific": True,
                "target_region": "india"
            }
        
        # Topic-based detection
        elif any(term in query_lower for term in ["crypto", "technology", "tech", "ai", "software"]):
            return {
                "primary_categories": ["technology", "global"],
                "approach": "Technology-focused search",
                "location_specific": False,
                "target_region": None
            }
        elif any(term in query_lower for term in ["business", "economy", "finance", "market"]):
            return {
                "primary_categories": ["business", "global"],
                "approach": "Business-focused search",
                "location_specific": False,
                "target_region": None
            }
        else:
            # Default to global news
            return {
                "primary_categories": ["global", "asia"],
                "approach": "General news search",
                "location_specific": False,
                "target_region": None
            }

    async def _search_dynamic_news_sources(self, query: str, strategy: Dict) -> List[Dict]:
        """
        Search news sources dynamically based on strategy
        """
        results = []
        categories = strategy.get("primary_categories", ["global"])
        
        logger.info(f"📰 Dynamic news search using categories: {categories}")
        
        for category in categories:
            if category in self.news_sources:
                feeds = self.news_sources[category]
                category_results = await self._search_news_category(query, feeds, category, strategy)
                results.extend(category_results)
                
        # Remove duplicates and limit results
        unique_results = []
        seen_urls = set()
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # Sort by relevance and return top results
        unique_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return unique_results[:10]  # Top 10 from dynamic sources

    async def _search_news_category(self, query: str, feeds: List, category: str, strategy: Dict) -> List[Dict]:
        """
        Search a specific category of news feeds
        """
        results = []
        
        for feed_url, source_name in feeds:
            try:
                response = self.session.get(feed_url, timeout=15)
                response.raise_for_status()
                
                import feedparser
                feed = feedparser.parse(response.content)
                logger.info(f"📰 {source_name}: found {len(feed.entries)} entries")
                
                for entry in feed.entries[:15]:  # Check more entries for better filtering
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    
                    # Calculate relevance with enhanced scoring for location-specific queries
                    relevance_score = self._calculate_enhanced_relevance(
                        query, title, summary, strategy
                    )
                    
                    # More lenient threshold for location-specific queries
                    threshold = 2 if strategy.get("location_specific") else 4
                    
                    if relevance_score >= threshold:
                        results.append({
                            "title": title,
                            "url": entry.get("link", ""),
                            "snippet": summary[:300],
                            "source": source_name,
                            "published": entry.get("published", ""),
                            "relevance": relevance_score,
                            "category": category
                        })
                        
            except Exception as e:
                logger.warning(f"Failed to fetch from {source_name}: {str(e)}")
                continue
                
        return results
