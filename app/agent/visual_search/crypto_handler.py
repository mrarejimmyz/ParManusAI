"""
LLM-Driven Crypto Data Handler
Replaces static crypto parsing with intelligent analysis
"""

import re
from typing import Dict, List, Optional

from app.agent.visual_search.types import CryptoData, SearchResult
from app.logger import logger


class LLMCryptoHandler:
    """Handles cryptocurrency data extraction with LLM analysis"""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def extract_crypto_data(self, content: str, query: str) -> List[SearchResult]:
        """Extract cryptocurrency data using LLM-driven analysis"""
        logger.info(f"🪙 Starting LLM-driven crypto extraction for: {query}")

        if self.llm:
            return await self._llm_crypto_extraction(content, query)
        else:
            return await self._fallback_crypto_extraction(content, query)

    async def _llm_crypto_extraction(
        self, content: str, query: str
    ) -> List[SearchResult]:
        """Use LLM to intelligently extract crypto data"""
        crypto_prompt = f"""
        Analyze this content and extract cryptocurrency data relevant to the query: "{query}"

        Content: {content[:3000]}

        Extract structured cryptocurrency information including:
        - Names and symbols
        - Current prices
        - Market rankings
        - Market caps
        - 24h price changes
        - Any other relevant metrics

        Return JSON array with format:
        [
            {{
                "name": "Bitcoin",
                "symbol": "BTC",
                "price": "$50,000",
                "rank": "1",
                "market_cap": "$1T",
                "change_24h": "+2.5%",
                "description": "Leading cryptocurrency",
                "confidence": 0.95
            }}
        ]

        Focus on accuracy and relevance to the query. If no crypto data is found, return empty array.
        """

        try:
            response = await self.llm.generate_response(crypto_prompt)
            import json

            crypto_list = json.loads(response)

            # Convert to SearchResult format
            results = []
            for i, crypto_data in enumerate(crypto_list[:10]):
                crypto = CryptoData(
                    name=crypto_data.get("name", "Unknown"),
                    symbol=crypto_data.get("symbol", ""),
                    price=crypto_data.get("price"),
                    rank=crypto_data.get("rank"),
                    market_cap=crypto_data.get("market_cap"),
                    change_24h=crypto_data.get("change_24h"),
                    metadata={
                        "confidence": crypto_data.get("confidence", 0.5),
                        "description": crypto_data.get("description", ""),
                    },
                )

                # Create search result
                title = f"#{crypto.rank} {crypto.name}"
                if crypto.symbol:
                    title += f" ({crypto.symbol})"
                if crypto.price:
                    title += f" - {crypto.price}"

                snippet = f"Cryptocurrency data for {crypto.name}"
                if crypto.change_24h:
                    snippet += f" | 24h change: {crypto.change_24h}"
                if crypto.market_cap:
                    snippet += f" | Market cap: {crypto.market_cap}"

                result = SearchResult(
                    title=title,
                    url=await self._generate_crypto_url(crypto, query),
                    snippet=snippet,
                    rank=(
                        int(crypto.rank)
                        if crypto.rank and crypto.rank.isdigit()
                        else i + 1
                    ),
                    confidence=crypto.metadata.get("confidence"),
                    metadata={"crypto_data": crypto},
                )
                results.append(result)

            logger.info(f"✅ LLM extracted {len(results)} crypto results")
            return results

        except Exception as e:
            logger.warning(f"LLM crypto extraction failed: {e}")
            return await self._fallback_crypto_extraction(content, query)

    async def _fallback_crypto_extraction(
        self, content: str, query: str
    ) -> List[SearchResult]:
        """Fallback crypto extraction using pattern matching"""
        logger.info("🔄 Using fallback crypto extraction")

        # Enhanced crypto mapping with more comprehensive patterns
        crypto_patterns = await self._get_crypto_patterns()

        # Filter content to remove noise
        filtered_content = self._filter_crypto_content(content)

        # Extract crypto data
        found_cryptos = []
        lines = filtered_content.split("\n")

        for line in lines:
            line_clean = line.strip()
            if len(line_clean) < 5:
                continue

            crypto_data = self._extract_crypto_from_line(line_clean, crypto_patterns)
            if crypto_data:
                found_cryptos.append(crypto_data)

            # Limit results
            if len(found_cryptos) >= 10:
                break

        # Convert to SearchResult format
        results = []
        for i, crypto in enumerate(found_cryptos):
            title = f"#{crypto.rank} {crypto.name}"
            if crypto.symbol:
                title += f" ({crypto.symbol})"
            if crypto.price:
                title += f" - {crypto.price}"

            snippet = f"Cryptocurrency: {crypto.name}"
            if crypto.change_24h:
                snippet += f" | 24h: {crypto.change_24h}"

            result = SearchResult(
                title=title,
                url=await self._generate_crypto_url(crypto, query),
                snippet=snippet,
                rank=(
                    int(crypto.rank) if crypto.rank and crypto.rank.isdigit() else i + 1
                ),
                metadata={"crypto_data": crypto},
            )
            results.append(result)

        logger.info(f"📊 Fallback extracted {len(results)} crypto results")
        return results

    async def _get_crypto_patterns(self) -> Dict:
        """Get cryptocurrency patterns for extraction"""
        if self.llm:
            # Let LLM provide current crypto patterns
            pattern_prompt = """
            Provide a comprehensive list of top cryptocurrencies with their common names and symbols.

            Return JSON format:
            {
                "bitcoin": ["bitcoin", "btc"],
                "ethereum": ["ethereum", "eth", "ether"],
                ...
            }

            Include top 20 cryptocurrencies by market cap.
            """

            try:
                response = await self.llm.generate_response(pattern_prompt)
                import json

                return json.loads(response)
            except:
                pass

        # Fallback patterns
        return {
            "bitcoin": ["bitcoin", "btc"],
            "ethereum": ["ethereum", "eth", "ether"],
            "tether": ["tether", "usdt"],
            "bnb": ["bnb", "binance coin", "binance"],
            "xrp": ["xrp", "ripple"],
            "solana": ["solana", "sol"],
            "usdc": ["usdc", "usd coin"],
            "cardano": ["cardano", "ada"],
            "dogecoin": ["dogecoin", "doge"],
            "avalanche": ["avalanche", "avax"],
            "polygon": ["polygon", "matic"],
            "chainlink": ["chainlink", "link"],
            "litecoin": ["litecoin", "ltc"],
            "polkadot": ["polkadot", "dot"],
            "uniswap": ["uniswap", "uni"],
        }

    def _filter_crypto_content(self, content: str) -> str:
        """Filter content to focus on crypto-relevant information"""
        lines = content.split("\n")
        filtered_lines = []

        # Skip obvious metadata lines
        skip_phrases = [
            "enhanced content extraction",
            "analysis goal:",
            "website analysis:",
            "content overview:",
            "key findings:",
            "total content length:",
            "browser tool analysis",
        ]

        for line in lines:
            line_lower = line.lower().strip()

            # Skip metadata
            if any(phrase in line_lower for phrase in skip_phrases):
                continue

            # Skip lines with too many special characters (likely noise)
            if sum(1 for c in line if not c.isalnum() and c != " ") > len(line) * 0.3:
                continue

            # Keep lines that might contain crypto data
            if len(line.strip()) > 5 and (
                any(
                    crypto_word in line_lower
                    for crypto_word in [
                        "crypto",
                        "bitcoin",
                        "eth",
                        "price",
                        "$",
                        "market",
                        "cap",
                        "rank",
                    ]
                )
                or re.search(r"\$[\d,]+", line)
            ):
                filtered_lines.append(line.strip())

        return "\n".join(filtered_lines)

    def _extract_crypto_from_line(
        self, line: str, crypto_patterns: Dict
    ) -> Optional[CryptoData]:
        """Extract crypto data from a single line"""
        line_lower = line.lower()

        # Find matching crypto
        for crypto_name, patterns in crypto_patterns.items():
            if any(pattern in line_lower for pattern in patterns):
                # Extract price
                price_match = re.search(r"\$[\d,]+\.?\d*", line)
                price = price_match.group(0) if price_match else None

                # Extract rank
                rank_match = re.search(r"#(\d+)", line)
                rank = rank_match.group(1) if rank_match else None

                # Extract percentage change
                change_match = re.search(r"[+-]?\d+\.?\d*%", line)
                change_24h = change_match.group(0) if change_match else None

                # Extract market cap
                market_cap = None
                cap_patterns = [r"\$[\d,]+\.?\d*[BMT]", r"[\d,]+\.?\d*[BMT]"]
                for pattern in cap_patterns:
                    cap_match = re.search(pattern, line)
                    if cap_match and cap_match.group(0) != price:
                        market_cap = cap_match.group(0)
                        break

                # Get symbol
                symbol = patterns[1] if len(patterns) > 1 else crypto_name[:3].upper()

                return CryptoData(
                    name=crypto_name.title(),
                    symbol=symbol.upper(),
                    price=price,
                    rank=rank,
                    market_cap=market_cap,
                    change_24h=change_24h,
                )

        return None

    async def _generate_crypto_url(self, crypto: CryptoData, query: str) -> str:
        """Generate appropriate URL for crypto data"""
        if self.llm:
            # Let LLM suggest best URL
            url_prompt = f"""
            Suggest the best URL for cryptocurrency data for {crypto.name} based on the query: "{query}"

            Options could include:
            - CoinMarketCap
            - CoinGecko
            - Official website
            - Trading platform

            Return just the URL, no explanation.
            """

            try:
                url = await self.llm.generate_response(url_prompt)
                return url.strip().strip('"')
            except:
                pass

        # Fallback URL generation
        if "coinmarketcap" in query.lower():
            return "https://coinmarketcap.com/"
        elif "coingecko" in query.lower():
            return "https://coingecko.com/"
        else:
            return f"https://coinmarketcap.com/currencies/{crypto.name.lower()}/"
