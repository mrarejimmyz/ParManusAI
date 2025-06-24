"""
Hybrid Fast Search - Best of All Approaches
Combines ultra-fast text parsing with vision fallback and multiple search engines
"""

import asyncio
import time
import re
import urllib.parse
from typing import Dict, List
from app.logger import logger
from app.tool.core.base import BaseTool, ToolConfig, ToolResult


class HybridFastSearchTool(BaseTool):
    """Optimized hybrid search combining speed and reliability."""

    def __init__(self, **kwargs):
        default_config = ToolConfig(
            name="hybrid_fast_search",
            description="Hybrid fast search with multiple fallback strategies",
            llm_enabled=True,  # For vision when needed
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to extract",
                        "default": 5,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Total timeout in seconds",
                        "default": 45,
                    },
                },
                "required": ["query"],
            },
        )
        super().__init__(config=default_config, **kwargs)

    async def _execute(
        self,
        query: str,
        num_results: int = 5,
        timeout: int = 45,
    ) -> ToolResult:
        """Execute hybrid fast search with multiple strategies."""

        logger.info(f"🚀 Hybrid Fast Search: '{query}' (timeout: {timeout}s)")
        start_time = time.time()

        strategies = [
            ("StartPage Text", self._startpage_text_search),
            ("Bing Text", self._bing_text_search),
            ("DuckDuckGo Vision", self._duckduckgo_vision_search),
            ("LLM Fallback", self._llm_fallback_search),
        ]

        for strategy_name, strategy_func in strategies:
            try:
                logger.info(f"🔄 Trying {strategy_name} search...")
                
                # Calculate remaining timeout
                elapsed = time.time() - start_time
                remaining_timeout = max(10, timeout - elapsed)
                
                results = await asyncio.wait_for(
                    strategy_func(query, num_results),
                    timeout=remaining_timeout
                )
                
                if results:
                    total_time = time.time() - start_time
                    logger.info(f"✅ {strategy_name} succeeded in {total_time:.1f}s: {len(results)} results")
                    
                    return ToolResult(
                        success=True,
                        content={
                            "query": query,
                            "results": results,
                            "total_results": len(results),
                            "method": strategy_name.lower().replace(" ", "_"),
                            "execution_time": f"{total_time:.1f}s",
                            "cost": "FREE"
                        }
                    )
                else:
                    logger.warning(f"⚠️ {strategy_name} returned no results")
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏰ {strategy_name} timed out")
                continue
            except Exception as e:
                logger.error(f"❌ {strategy_name} failed: {e}")
                continue
        
        # If all strategies fail
        total_time = time.time() - start_time
        logger.error(f"❌ All search strategies failed in {total_time:.1f}s")
        
        return ToolResult(
            success=False,
            content={
                "query": query,
                "results": [],
                "error": "All search strategies failed",
                "execution_time": f"{total_time:.1f}s",
                "recommendation": "Try a different query or check internet connectivity"
            }
        )

    async def _startpage_text_search(self, query: str, num_results: int) -> List[Dict]:
        """Search using StartPage (privacy-focused, less bot detection)."""
        
        import nodriver as uc
        
        browser = None
        try:
            browser_config = {
                "headless": True,
                "user_data_dir": None,
                "browser_args": [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-images',
                ]
            }

            browser = await uc.start(**browser_config)
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://www.startpage.com/search?query={encoded_query}"
            
            page = await browser.get(search_url)
            await asyncio.sleep(2)
            
            html_content = await page.get_content()
            
            # Check if we got blocked
            if "blocked" in html_content.lower() or "captcha" in html_content.lower():
                logger.warning("StartPage blocked our request")
                return []
            
            # StartPage result parsing
            results = []
            
            # Multiple patterns to try
            patterns = [
                r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h3>',
                r'<a[^>]*class="[^"]*result[^"]*"[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
                r'<a[^>]*href="(https?://[^"]*)"[^>]*title="([^"]*)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    break
            
            # Filter and format results
            for url, title in matches[:num_results * 2]:
                if self._is_valid_search_result(url, title):
                    results.append({
                        "title": title.strip()[:200],
                        "url": url.strip(),
                        "snippet": f"Search result from StartPage for: {query}",
                        "position": len(results) + 1,
                        "source": "startpage_text"
                    })
                    
                    if len(results) >= num_results:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"StartPage search failed: {e}")
            return []
        finally:
            if browser:
                try:
                    await browser.stop()
                except:
                    pass

    async def _bing_text_search(self, query: str, num_results: int) -> List[Dict]:
        """Search using Bing (often less aggressive than Google/DDG)."""
        
        import nodriver as uc
        
        browser = None
        try:
            browser_config = {
                "headless": True,
                "user_data_dir": None,
                "browser_args": [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-images',
                ]
            }

            browser = await uc.start(**browser_config)
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://www.bing.com/search?q={encoded_query}"
            
            page = await browser.get(search_url)
            await asyncio.sleep(2)
            
            html_content = await page.get_content()
            
            # Check if we got blocked
            if "blocked" in html_content.lower() or "captcha" in html_content.lower():
                logger.warning("Bing blocked our request")
                return []
            
            # Bing result parsing
            results = []
            
            # Look for Bing result patterns
            patterns = [
                r'<h2[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h2>',
                r'<a[^>]*href="(https?://[^"]*)"[^>]*><h3[^>]*>([^<]+)</h3>',
                r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h3>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    break
                    
            for url, title in matches[:num_results * 2]:
                if self._is_valid_search_result(url, title):
                    results.append({
                        "title": title.strip()[:200],
                        "url": url.strip(),
                        "snippet": f"Search result from Bing for: {query}",
                        "position": len(results) + 1,
                        "source": "bing_text"
                    })
                    
                    if len(results) >= num_results:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []
        finally:
            if browser:
                try:
                    await browser.stop()
                except:
                    pass

    async def _duckduckgo_vision_search(self, query: str, num_results: int) -> List[Dict]:
        """Fallback to NoDriver + Vision when text parsing fails."""
        
        try:
            from app.tool.implementations.nodriver_vision_search_fast import FastNoDriverVisionSearchTool
            
            vision_tool = FastNoDriverVisionSearchTool(llm=self.llm)
            
            result = await vision_tool._execute(
                query=query,
                num_results=num_results,
                timeout=20  # Shorter timeout for vision
            )
            
            if result.success:
                return result.content.get("results", [])
        
        except Exception as e:
            logger.error(f"DuckDuckGo vision search failed: {e}")
        
        return []

    async def _llm_fallback_search(self, query: str, num_results: int) -> List[Dict]:
        """LLM-generated results as final fallback."""
        
        try:
            if hasattr(self, 'llm') and self.llm:
                prompt = f"""Generate {num_results} realistic search results for: "{query}"

Return as a list of results with title, url, and snippet.
Mark these as LLM-generated content.
Focus on factual, helpful information.

Format as JSON list."""

                response = await self.llm.ask(prompt)
                
                # Parse and format LLM results
                import json
                try:
                    results = json.loads(response)
                    if isinstance(results, list):
                        formatted_results = []
                        for i, result in enumerate(results[:num_results]):
                            formatted_results.append({
                                "title": str(result.get("title", f"Result {i+1}"))[:200],
                                "url": str(result.get("url", f"https://example.com/result{i+1}")),
                                "snippet": str(result.get("snippet", f"LLM-generated content for {query}"))[:300],
                                "position": i + 1,
                                "source": "llm_fallback",
                                "warning": "⚠️ This is AI-generated content, not real search results"
                            })
                        return formatted_results
                except:
                    pass
            
            # Manual fallback
            return [{
                "title": f"AI-Generated Information about {query}",
                "url": "https://ai-generated-content.example.com",
                "snippet": f"This is AI-generated content related to your search for: {query}. Please verify information independently.",
                "position": 1,
                "source": "manual_fallback",
                "warning": "⚠️ This is AI-generated content, not real search results"
            }]
              except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            return []

    def _is_valid_search_result(self, url: str, title: str) -> bool:
        """Check if result is valid and not a search engine artifact."""
        
        if not url or not title or len(title.strip()) < 3:
            logger.debug(f"❌ Invalid result: empty url/title")
            return False
            
        # Filter out obvious non-results and internal pages
        invalid_patterns = [
            "startpage.com", "bing.com", "duckduckgo.com", "google.com",
            "/search", "/cookie", "/privacy", "/terms",
            "/login", "/register", "/account", "/settings",
            "/support", "/about", "/contact", "/help"
        ]
        
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Check for invalid patterns
        for pattern in invalid_patterns:
            if pattern in url_lower or pattern in title_lower:
                logger.debug(f"❌ Filtered out internal: {title[:50]}...")
                return False
        
        # Prioritize AI-related content
        ai_keywords = [
            "artificial intelligence", "machine learning", "ai news", 
            "neural network", "deep learning", "chatgpt", "openai",
            "generative ai", "ai model", "llm", "artificial", "intelligence"
        ]
        
        is_ai_related = any(keyword in title_lower for keyword in ai_keywords)
        
        # If it's clearly AI-related, definitely include it
        if is_ai_related:
            logger.debug(f"✅ AI-related result: {title[:50]}...")
            return True
        
        # For non-AI specific results, be more selective
        # Accept news from reputable sources but log for awareness
        reputable_domains = [
            "reuters.com", "bbc.com", "cnn.com", "nytimes.com",
            "techcrunch.com", "theverge.com", "wired.com", "arstechnica.com",
            "nature.com", "sciencemag.org", "ieee.org", "mit.edu"
        ]
        
        for domain in reputable_domains:
            if domain in url_lower:
                logger.debug(f"📰 Reputable source: {title[:50]}...")
                return True
        
        # Log what we're filtering out for debugging
        logger.debug(f"⚠️ General result (may be relevant): {title[:50]} from {url_lower}")
        return True  # Be inclusive for now, let LLM filter later


# Register the tool
__all__ = ["HybridFastSearchTool"]
