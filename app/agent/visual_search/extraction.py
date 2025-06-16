"""
LLM-Driven Content Extraction
Replaces static parsing with intelligent content analysis
"""

import re
from typing import Dict, List, Optional

from app.agent.visual_search.types import CryptoData, ExtractionConfig, SearchResult
from app.logger import logger


class LLMContentExtractor:
    """Handles content extraction with LLM-driven analysis"""

    def __init__(self, browser_handler, llm_client=None):
        self.browser = browser_handler
        self.llm = llm_client

    async def extract_search_results(
        self, config: ExtractionConfig
    ) -> List[SearchResult]:
        """Extract search results using LLM-driven analysis"""
        logger.info("📑 Starting LLM-driven content extraction")

        # Check for anti-bot measures first
        if await self._detect_access_blocked():
            logger.warning("🚫 Access blocked detected - returning empty results")
            return []

        # Extract raw content
        raw_content = await self._extract_raw_content(config)
        if not raw_content:
            return []

        # Let LLM analyze and structure the content
        if self.llm:
            return await self._llm_structured_extraction(raw_content, config)
        else:
            return await self._fallback_extraction(raw_content, config)

    async def _detect_access_blocked(self) -> bool:
        """Use LLM to detect if access is blocked"""
        try:
            # Get current URL and basic page info
            extract_result = await self.browser.execute(
                action="extract_content",
                goal="Check for CAPTCHA, sorry pages, or access restrictions",
            )

            if extract_result.error:
                return True

            content = extract_result.output.lower()

            # Quick check for obvious blocking
            blocking_indicators = [
                "captcha",
                "sorry",
                "blocked",
                "access denied",
                "rate limit",
            ]
            if any(indicator in content for indicator in blocking_indicators):
                return True

            # LLM analysis for more subtle blocking
            if self.llm:
                detection_prompt = f"""
                Analyze this page content to determine if access is blocked or restricted:

                Content: {extract_result.output[:1000]}

                Look for:
                - CAPTCHA challenges
                - "Sorry" or error pages
                - Rate limiting messages
                - Bot detection notices
                - Unusual page structures that indicate blocking

                Return JSON: {{"blocked": true/false, "reason": "explanation"}}
                """

                try:
                    response = await self.llm.generate_response(detection_prompt)
                    import json

                    result = json.loads(response)
                    return result.get("blocked", False)
                except:
                    pass

            return False

        except Exception as e:
            logger.warning(f"Block detection failed: {e}")
            return False

    async def _extract_raw_content(self, config: ExtractionConfig) -> Optional[str]:
        """Extract raw content from the page"""
        try:
            if config.extraction_method == "llm_guided" and self.llm:
                # Let LLM determine extraction goal
                goal = await self._generate_extraction_goal(config)
            else:
                goal = f"Extract {', '.join(config.target_elements)} from this page"

            extract_result = await self.browser.execute(
                action="extract_content", goal=goal
            )

            if extract_result.error:
                logger.error(f"Content extraction failed: {extract_result.error}")
                return None

            return extract_result.output

        except Exception as e:
            logger.error(f"Raw content extraction failed: {e}")
            return None

    async def _generate_extraction_goal(self, config: ExtractionConfig) -> str:
        """Let LLM generate extraction goal based on target elements"""
        if not self.llm:
            return f"Extract {', '.join(config.target_elements)} from this page"

        goal_prompt = f"""
        Create an optimal extraction goal for browser content extraction.

        Target elements: {config.target_elements}
        Structured output needed: {config.structured_output}
        Include metadata: {config.include_metadata}

        Create a clear, specific goal that will help extract the most relevant information.
        Focus on actionable instructions for content extraction.
        """

        try:
            goal = await self.llm.generate_response(goal_prompt)
            return goal.strip().strip('"')
        except Exception as e:
            logger.warning(f"Goal generation failed: {e}")
            return f"Extract {', '.join(config.target_elements)} from this page"

    async def _llm_structured_extraction(
        self, raw_content: str, config: ExtractionConfig
    ) -> List[SearchResult]:
        """Use LLM to intelligently structure the extracted content"""
        structure_prompt = f"""
        Analyze this raw content and extract structured search results:

        Raw content: {raw_content[:config.max_content_length]}

        Target elements: {config.target_elements}

        Extract and structure information into search results. Look for:
        - Titles/headings
        - URLs/links
        - Descriptions/snippets
        - Relevant metadata

        Return JSON array of results with format:
        [
            {{
                "title": "result title",
                "url": "result url",
                "snippet": "description",
                "rank": number,
                "confidence": 0.0-1.0,
                "metadata": {{}}
            }}
        ]

        Focus on the most relevant and high-quality results.
        """

        try:
            response = await self.llm.generate_response(structure_prompt)
            import json

            results_data = json.loads(response)

            # Convert to SearchResult objects
            results = []
            for i, data in enumerate(results_data[:10]):  # Limit to 10 results
                result = SearchResult(
                    title=data.get("title", f"Result {i+1}"),
                    url=data.get("url", ""),
                    snippet=data.get("snippet", ""),
                    rank=data.get("rank", i + 1),
                    confidence=data.get("confidence"),
                    metadata=data.get("metadata"),
                )
                results.append(result)

            logger.info(f"✅ LLM extracted {len(results)} structured results")
            return results

        except Exception as e:
            logger.warning(f"LLM structured extraction failed: {e}")
            return await self._fallback_extraction(raw_content, config)

    async def _fallback_extraction(
        self, raw_content: str, config: ExtractionConfig
    ) -> List[SearchResult]:
        """Fallback extraction when LLM is not available"""
        logger.info("🔄 Using fallback extraction method")

        results = []

        # Check if this looks like crypto data
        if self._is_crypto_content(raw_content):
            crypto_results = await self._extract_crypto_fallback(raw_content)
            return crypto_results

        # General fallback extraction
        lines = [line.strip() for line in raw_content.split("\n") if line.strip()]

        # Filter out metadata and noise
        filtered_lines = []
        skip_phrases = [
            "enhanced content extraction",
            "analysis goal:",
            "website analysis:",
            "content overview:",
            "key findings:",
        ]

        for line in lines:
            if not any(phrase in line.lower() for phrase in skip_phrases):
                if len(line) > 10 and len(line) < 200:
                    filtered_lines.append(line)

        # Extract URLs
        url_pattern = r'https?://[^\s<>"\']+[^\s<>"\'.,)]'
        urls = re.findall(url_pattern, raw_content)
        unique_urls = list(dict.fromkeys(urls))  # Remove duplicates

        # Create results from content
        for i, line in enumerate(filtered_lines[:5]):
            url = unique_urls[i] if i < len(unique_urls) else ""

            result = SearchResult(title=line[:100], url=url, snippet=line, rank=i + 1)
            results.append(result)

        logger.info(f"📋 Fallback extraction found {len(results)} results")
        return results

    def _is_crypto_content(self, content: str) -> bool:
        """Check if content appears to be cryptocurrency-related"""
        crypto_indicators = [
            "bitcoin",
            "ethereum",
            "cryptocurrency",
            "crypto",
            "market cap",
            "coinmarketcap",
            "binance",
            "price",
            "btc",
            "eth",
            "usdt",
            "blockchain",
        ]
        content_lower = content.lower()
        return (
            sum(1 for indicator in crypto_indicators if indicator in content_lower) >= 2
        )

    async def _extract_crypto_fallback(self, content: str) -> List[SearchResult]:
        """Fallback crypto data extraction"""
        logger.info("🪙 Using fallback crypto extraction")

        results = []

        # Define crypto patterns
        crypto_map = {
            "bitcoin": ["bitcoin", "btc"],
            "ethereum": ["ethereum", "eth"],
            "tether": ["tether", "usdt"],
            "bnb": ["bnb", "binance coin"],
            "xrp": ["xrp", "ripple"],
            "solana": ["solana", "sol"],
            "usdc": ["usdc", "usd coin"],
            "cardano": ["cardano", "ada"],
            "dogecoin": ["dogecoin", "doge"],
            "avalanche": ["avalanche", "avax"],
        }

        lines = content.split("\n")
        found_cryptos = []

        for line in lines:
            line_clean = line.strip().lower()
            if len(line_clean) < 5:
                continue

            for crypto_name, patterns in crypto_map.items():
                if any(pattern in line_clean for pattern in patterns):
                    # Try to extract price
                    price_match = re.search(r"\$[\d,]+\.?\d*", line)
                    price = price_match.group(0) if price_match else "N/A"

                    # Try to extract rank
                    rank_match = re.search(r"#(\d+)", line)
                    rank = (
                        rank_match.group(1)
                        if rank_match
                        else str(len(found_cryptos) + 1)
                    )

                    crypto_data = CryptoData(
                        name=crypto_name.title(),
                        symbol=(
                            patterns[1]
                            if len(patterns) > 1
                            else crypto_name[:3].upper()
                        ),
                        price=price,
                        rank=rank,
                    )
                    found_cryptos.append(crypto_data)
                    break

        # Convert to SearchResult format
        for i, crypto in enumerate(found_cryptos[:10]):
            result = SearchResult(
                title=f"#{crypto.rank} {crypto.name} ({crypto.symbol}) - {crypto.price}",
                url="https://coinmarketcap.com/",
                snippet=f"Cryptocurrency ranking and price data for {crypto.name}",
                rank=int(crypto.rank) if crypto.rank.isdigit() else i + 1,
                metadata={"crypto_data": crypto},
            )
            results.append(result)

        logger.info(f"🔍 Extracted {len(results)} crypto results")
        return results
