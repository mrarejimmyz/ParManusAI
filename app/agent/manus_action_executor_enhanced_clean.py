"""
Optimized Manus Action Executor with Multi-Engine Search
Clean, efficient execution that bypasses CAPTCHA using multiple search engines
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from app.logger import logger
from app.tool.optimized_bulletproof_search import OptimizedBulletproofSearch


class ManusActionExecutor:
    """Optimized action executor with multi-engine search integration"""

    def __init__(self, agent):
        """Initialize with agent reference"""
        self.agent = agent
        self.llm = getattr(
            agent, "llm", None
        )  # Pass LLM to search engine for dynamic reasoning
        self.search_engine = OptimizedBulletproofSearch(llm=self.llm)
        self.last_search_results = None

    async def execute_research_action(self, step: str) -> bool:
        """Execute research with intelligent dynamic search based on user intent"""
        try:
            logger.info(f"🔍 RESEARCH ACTION: {step}")

            # Use LLM to analyze user request and generate optimal search strategy
            search_strategy = (
                await self._analyze_user_intent_and_generate_search_strategy()
            )

            if not search_strategy:
                logger.warning(
                    "⚠️ Could not generate search strategy - using fallback direct search"
                )
                # Fallback: perform direct search with user's request
                user_message = self._get_user_message()
                result = await self.search_engine.perform_google_search(user_message)

                if result.get("success"):
                    self.last_search_results = {
                        "success": True,
                        "results": result.get("results", [])[:10],
                        "strategy": {"approach": "direct_fallback_search"},
                        "method": "fallback_direct_search",
                    }
                    logger.info(
                        f"✅ Fallback search found {len(result.get('results', []))[:10]} results"
                    )

                return True

            logger.info(
                f"🧠 Generated search strategy: {search_strategy.get('approach', 'dynamic')}"
            )

            # Execute the dynamic search strategy
            all_results = []
            for search_query in search_strategy.get("queries", []):
                logger.info(f"🔍 Executing search: {search_query}")

                result = await self.search_engine.perform_google_search(search_query)

                if result.get("success"):
                    results = result.get("results", [])
                    # Filter results based on relevance to original intent
                    relevant_results = await self._filter_results_by_intent(
                        results, search_strategy.get("intent", {})
                    )
                    all_results.extend(relevant_results)
                    logger.info(
                        f"✅ Found {len(relevant_results)} relevant results from query: {search_query}"
                    )

            if all_results:
                # Store consolidated results
                self.last_search_results = {
                    "success": True,
                    "results": all_results[:10],  # Top 10 most relevant
                    "strategy": search_strategy,
                    "method": "dynamic_reasoning_search",
                }
                logger.info(f"✅ Total relevant results: {len(all_results[:10])}")
            else:
                logger.warning("⚠️ No relevant results found - will use LLM knowledge")

            return True

        except Exception as e:
            logger.error(f"❌ Research action failed: {str(e)}")
            return True  # Continue anyway    async def execute_extraction_action(self, step: str) -> bool:
        """Execute data extraction"""
        logger.info(f"📊 EXTRACTION ACTION: {step}")
        # For extraction, check if we have search results
        if self.last_search_results and self.last_search_results.get("success"):
            logger.info("✅ Extraction successful - search results available")
            return True
        else:
            logger.warning("⚠️ Extraction incomplete - no search results available")
            return False

    async def execute_verification_action(self, step: str) -> bool:
        """Execute verification"""
        logger.info(f"✅ VERIFICATION ACTION: {step}")
        # For verification, check if we have sufficient data to verify
        if self.last_search_results and self.last_search_results.get("results"):
            num_results = len(self.last_search_results["results"])
            if num_results >= 2:  # Need at least 2 sources for verification
                logger.info(
                    f"✅ Verification successful - {num_results} sources available"
                )
                return True
            else:
                logger.warning(
                    f"⚠️ Verification incomplete - only {num_results} source(s) available"
                )
                return False
        else:
            logger.warning("⚠️ Verification incomplete - no search results to verify")
            return False

    async def execute_creation_action(self, step: str) -> bool:
        """Execute document creation using LLM"""
        try:
            logger.info(f"📝 CREATION ACTION: {step}")

            if not self.llm:
                logger.warning("⚠️ No LLM available for document creation")
                return False

            # Get user request and context
            user_message = self._get_user_message()
            context = self._get_search_context()

            # Create document prompt
            prompt = self._build_creation_prompt(user_message, context)

            logger.info("🧠 Creating document with LLM...")  # Generate content
            response = await self.llm.ask(prompt)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )

            if content and len(content) > 300:
                # Save document
                filename = self._determine_filename(user_message)
                filepath = self._save_document(filename, content)

                # Record deliverable creation in todo list
                await self._record_deliverable_creation(filename, filepath)

                logger.info(f"✅ Document created: {filepath}")
                print(
                    f"\n📄 **DOCUMENT CREATED**\n✅ File: {filename}\n✅ Path: {filepath}"
                )
                return True
            else:
                logger.warning("⚠️ Generated content too short")
                return False

        except Exception as e:
            logger.error(f"❌ Creation action failed: {str(e)}")
            return False

    async def execute_navigation_action(self, step: str) -> bool:
        """Execute navigation"""
        logger.info(f"🧭 NAVIGATION ACTION: {step}")
        return True

    async def execute_default_action(self, step: str) -> bool:
        """Execute default action"""
        logger.info(f"🔧 DEFAULT ACTION: {step}")
        return True

    async def _record_deliverable_creation(self, filename: str, filepath: str) -> None:
        """Record the creation of a deliverable in the todo list"""
        try:
            # Get reference to the agent's planning module to record deliverable
            if hasattr(self.agent, "planning_module") and hasattr(
                self.agent.planning_module, "todo_manager"
            ):
                await self.agent.planning_module.todo_manager.mark_deliverable_created(
                    filename, filepath
                )
                logger.info(f"📝 Recorded deliverable creation: {filename}")
            else:
                logger.warning(
                    "⚠️ Could not record deliverable - planning module not available"
                )
        except Exception as e:
            logger.warning(f"Failed to record deliverable creation: {e}")

    def _get_user_message(self) -> str:
        """Get the user's original request"""
        if hasattr(self.agent, "messages") and self.agent.messages:
            for msg in reversed(self.agent.messages):
                if hasattr(msg, "role") and msg.role == "user":
                    content = getattr(msg, "content", "")
                    return content.lower() if content else ""
        return "analysis report"

    def _get_search_context(self) -> str:
        """Get enhanced context from search results with full content extraction"""
        if not (self.last_search_results and self.last_search_results.get("results")):
            return "No web search data available - using LLM knowledge"

        method = self.last_search_results.get("method", "search")
        context_parts = [f"REAL SEARCH RESULTS from {method}:"]
        context_parts.append("=" * 50)

        for i, result in enumerate(self.last_search_results["results"][:3], 1):
            title = result.get("title", "No title")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            source = result.get("source", "Unknown")

            context_parts.append(f"\n{i}. ARTICLE: {title}")
            context_parts.append(f"   SOURCE: {source}")
            context_parts.append(f"   URL: {url}")

            if snippet and title:
                # Try to extract more detailed content from the article
                full_content = self._fetch_article_content(url)
                if full_content:
                    context_parts.append(f"   FULL CONTENT: {full_content[:800]}...")
                else:
                    context_parts.append(f"   SNIPPET: {snippet}")

                # Add explicit instruction to use real data
                context_parts.append(f"   ⚠️  USE THIS REAL DATA - NO PLACEHOLDERS!")

        context_parts.append("\n" + "=" * 50)
        context_parts.append(
            "INSTRUCTION: Use the specific facts, names, dates, and numbers from the search results above."
        )
        context_parts.append(
            "DO NOT use placeholders like [Date], [Number], [Flight Number] - use the actual values found."
        )

        return "\n".join(context_parts)

    def _fetch_article_content(self, url: str) -> str:
        """Fetch and extract content from article URL"""
        if not url or "example.com" in url or not url.startswith("http"):
            return ""

        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Try different selectors for article content
            selectors = [
                '[data-component="text-block"]',  # BBC
                ".article-body p",  # Generic
                ".story-body p",  # BBC old
                "article p",  # Generic article
                ".content p",  # Generic content
            ]

            content_parts = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements[:5]:  # First 5 paragraphs
                        text = element.get_text().strip()
                        if text and len(text) > 30:
                            content_parts.append(text)
                    break

            if content_parts:
                return " ".join(content_parts)

        except Exception as e:
            logger.warning(f"Failed to fetch article content from {url}: {str(e)}")

        return ""

    def _build_creation_prompt(self, user_message: str, context: str) -> str:
        """Build optimized prompt for document creation with real data emphasis"""
        return f"""Create a comprehensive, professional analysis report based on this request: "{user_message}"

{context}

CRITICAL REQUIREMENTS:
🚨 DO NOT USE PLACEHOLDERS! Use only real, specific information from the search results above.
🚨 DO NOT write [Date], [Flight Number], [Number] - use actual values from the research data.
🚨 If specific information is not available in search results, clearly state "Information not available in current sources" rather than using placeholders.

Report Structure:
- Professional markdown format with proper headers
- Executive summary with specific facts
- Detailed analysis using ONLY the real data provided
- Include actual names, dates, numbers, and details from search results
- Proper citations with real URLs
- Minimum 1000 words using substantive content

Example of what to AVOID:
❌ "On [Date], Air India flight [Flight Number] crashed"
❌ "[Number] people were killed"
❌ "The investigation found [Details]"

Example of what to INCLUDE:
✅ "On Thursday, Air India flight AI171 crashed"
✅ "At least 270 people were killed"
✅ "The Boeing 787-8 Dreamliner crashed after takeoff from Ahmedabad"

Use the specific information provided in the search results above to create a factual, detailed report.
- Professional tone suitable for business/academic use
- Use the research data provided above to enhance accuracy

Generate the complete report now:"""

    def _determine_filename(self, user_message: str) -> str:
        """Determine appropriate filename based on content and search strategy"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get the search strategy for context
        search_context = ""
        if self.last_search_results and self.last_search_results.get("strategy"):
            strategy = self.last_search_results["strategy"]
            if strategy.get("location_specific") and strategy.get("target_region"):
                search_context = f"_{strategy['target_region']}"

        # Dynamic filename based on user request
        user_lower = user_message.lower()

        if "air india" in user_lower and "crash" in user_lower:
            return f"air_india_crash_analysis_report{search_context}_{timestamp}.md"
        elif "crypto" in user_lower or "bitcoin" in user_lower:
            return f"crypto_analysis_report{search_context}_{timestamp}.md"
        elif "nepal" in user_lower:
            return f"nepal_news_analysis_report_{timestamp}.md"
        elif "india" in user_lower:
            return f"india_news_analysis_report_{timestamp}.md"
        elif "technology" in user_lower or "tech" in user_lower:
            return f"technology_analysis_report{search_context}_{timestamp}.md"
        elif "business" in user_lower or "finance" in user_lower:
            return f"business_analysis_report{search_context}_{timestamp}.md"
        elif "news" in user_lower:
            return f"news_analysis_report{search_context}_{timestamp}.md"
        else:
            return f"analysis_report{search_context}_{timestamp}.md"

    def _save_document(self, filename: str, content: str) -> str:
        """Save document to workspace"""
        workspace_path = os.path.join(os.getcwd(), "workspace", filename)
        os.makedirs(os.path.dirname(workspace_path), exist_ok=True)

        with open(workspace_path, "w", encoding="utf-8") as f:
            f.write(content)

        return workspace_path

    async def _analyze_user_intent_and_generate_search_strategy(self) -> Optional[Dict]:
        """Use LLM to analyze user intent and generate dynamic search strategy"""
        try:
            user_message = self._get_user_message()

            prompt = f"""
            Analyze this user request and generate an optimal search strategy:

            User Request: "{user_message}"

            Please provide a JSON response with:
            1. "intent" - what the user is looking for (location, topic, timeframe, etc.)
            2. "queries" - list of 2-3 specific search queries to find relevant information
            3. "approach" - brief description of the search strategy

            For location-specific news (like Nepal), include:
            - Country/region name + "news today"
            - Country/region name + "latest headlines"
            - Specific news sources from that region if known

            Example for "top 5 news of nepal today":
            {{
                "intent": {{
                    "location": "Nepal",
                    "topic": "general news",
                    "timeframe": "today",
                    "count": 5
                }},
                "queries": [
                    "Nepal news today headlines",
                    "Nepal latest breaking news",
                    "Kathmandu Post headlines today"
                ],
                "approach": "Location-specific news search with multiple sources"
            }}

            Respond with only the JSON object:
            """

            if not self.llm:
                logger.warning("No LLM available for intent analysis")
                return None

            response = await self.llm.ask(prompt)

            # Extract JSON from response

            # Try to find JSON in the response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    strategy = json.loads(json_match.group())
                    logger.info(
                        f"🧠 Generated search strategy: {strategy.get('approach', 'Unknown')}"
                    )
                    return strategy
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM response as JSON: {e}")

            # Fallback strategy
            return self._generate_fallback_strategy(user_message)

        except Exception as e:
            logger.error(f"Failed to analyze user intent: {e}")
            return self._generate_fallback_strategy(user_message)

    def _generate_fallback_strategy(self, user_message: str) -> Dict:
        """Generate a basic search strategy when LLM analysis fails"""
        strategy = {
            "intent": {"topic": "general", "timeframe": "recent"},
            "queries": [],
            "approach": "fallback_strategy",
        }

        # Extract key terms for fallback queries
        user_lower = user_message.lower()

        # Country detection
        countries = [
            "nepal",
            "india",
            "china",
            "usa",
            "uk",
            "canada",
            "australia",
            "japan",
        ]
        detected_country = None
        for country in countries:
            if country in user_lower:
                detected_country = country
                break

        if detected_country:
            strategy["intent"]["location"] = detected_country
            strategy["queries"] = [
                f"{detected_country} news today",
                f"{detected_country} latest headlines",
                f"{detected_country} breaking news",
            ]
        else:
            # General search
            words = user_message.split()[:4]
            base_query = " ".join(words)
            strategy["queries"] = [
                f"{base_query} latest news",
                f"{base_query} headlines today",
                f"{base_query} breaking news",
            ]

        return strategy

    async def _filter_results_by_intent(
        self, results: List[Dict], intent: Dict
    ) -> List[Dict]:
        """Filter search results based on user intent using LLM reasoning"""
        if not results or not self.llm:
            return results

        try:
            # Prepare results summary for LLM
            results_summary = []
            for i, result in enumerate(results[:10]):  # Limit to avoid token limit
                results_summary.append(
                    {
                        "index": i,
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", "")[:200],  # Truncate snippet
                        "source": result.get("source", ""),
                    }
                )

            prompt = f"""
            Filter these search results based on user intent:

            User Intent: {intent}

            Search Results:
            {json.dumps(results_summary, indent=2)}

            Return only the indices (numbers) of results that are most relevant to the user's intent.
            Consider:
            - Location relevance (if specified)
            - Topic relevance
            - Recency (if timeframe specified)
            - Source credibility

            Respond with just a list of numbers, e.g.: [0, 2, 5, 7]
            """

            response = await self.llm.ask(prompt)

            # Extract indices from response
            indices_match = re.search(r"\[([\d,\s]+)\]", response)
            if indices_match:
                indices_str = indices_match.group(1)
                indices = [
                    int(x.strip())
                    for x in indices_str.split(",")
                    if x.strip().isdigit()
                ]

                # Return filtered results
                filtered_results = []
                for idx in indices:
                    if 0 <= idx < len(results):
                        filtered_results.append(results[idx])

                logger.info(
                    f"🎯 Filtered {len(results)} results down to {len(filtered_results)} relevant ones"
                )
                return filtered_results

        except Exception as e:
            logger.warning(f"Failed to filter results with LLM: {e}")

        # Fallback: return all results with basic filtering
        return results
