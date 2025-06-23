#!/usr/bin/env python3
"""
Simple test to verify search is working with content extraction
"""

import asyncio
import json
import sys

# Add project root to path
sys.path.append(".")

from app.tool.implementations.search_enhanced import EnhancedUnifiedSearchTool


async def simple_search_test():
    """Simple search test with content extraction."""

    print("🔍 SIMPLE SEARCH TEST")
    print("=" * 50)

    search_tool = EnhancedUnifiedSearchTool()

    # Test with a simple query
    query = "python programming tutorial"
    print(f"Query: '{query}'")

    result = await search_tool._execute(
        query=query, num_results=3, fetch_content=True, stealth_mode=True
    )

    print(f"\nSuccess: {result.success}")

    if result.success and result.content:
        results = result.content.get("results", [])
        content_fetched = result.content.get("content_fetched", False)

        print(f"Number of results: {len(results)}")
        print(f"Content enhanced: {content_fetched}")

        for i, res in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Title: {res.get('title', 'No title')}")
            print(f"URL: {res.get('url', 'No URL')}")
            print(f"Source: {res.get('source', 'No source')}")
            print(f"Content method: {res.get('content_method', 'none')}")
            print(f"Anti-bot bypass: {res.get('anti_bot_bypass', False)}")

            content = res.get("content", "")
            if content:
                print(f"Content length: {len(content)} chars")
                print(f"Content preview: {content[:200]}...")
            else:
                print("No content extracted")

            snippet = res.get("snippet", "")
            print(f"Snippet: {snippet[:150]}...")

        # Save results for inspection
        with open("simple_search_results.json", "w") as f:
            json.dump(result.content, f, indent=2)
        print(f"\n💾 Results saved to simple_search_results.json")

        return True
    else:
        print(f"❌ Search failed: {getattr(result, 'error', 'Unknown error')}")
        return False


if __name__ == "__main__":
    success = asyncio.run(simple_search_test())
    if success:
        print("\n✅ SEARCH IS WORKING!")
    else:
        print("\n❌ SEARCH FAILED!")
