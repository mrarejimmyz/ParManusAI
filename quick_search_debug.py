#!/usr/bin/env python3
"""
Quick test of the search tool to diagnose the issue
"""

import asyncio
import sys
import traceback

# Add project root to path
sys.path.append(".")

from app.logger import logger


async def test_search_tool():
    """Test the search tool directly."""

    print("🔍 Testing search tool directly...")

    try:
        # Import the search tool
        from app.tool.implementations.search_enhanced import EnhancedUnifiedSearchTool

        print("✅ Search tool imported successfully")

        # Initialize the tool
        search_tool = EnhancedUnifiedSearchTool()
        print("✅ Search tool initialized successfully")

        # Test with a simple query
        test_query = "artificial intelligence"
        print(f"🔍 Testing with query: '{test_query}'")

        result = await search_tool._execute(query=test_query, num_results=3)

        print(f"🎯 Search result success: {result.success}")

        if result.success:
            content = result.content
            results = content.get("results", [])
            print(f"📄 Number of results: {len(results)}")

            for i, res in enumerate(results, 1):
                print(f"  Result {i}:")
                print(f"    Title: {res.get('title', 'No title')}")
                print(f"    URL: {res.get('url', 'No URL')}")
                print(f"    Source: {res.get('source', 'No source')}")
                print(f"    Snippet: {res.get('snippet', 'No snippet')[:100]}...")
        else:
            print(f"❌ Search failed: {getattr(result, 'error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()


async def test_duckduckgo_api():
    """Test DuckDuckGo API directly"""

    print("\n🦆 Testing DuckDuckGo API directly...")

    try:
        from urllib.parse import quote_plus

        import requests

        query = "artificial intelligence"
        encoded_query = quote_plus(query)
        api_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"

        print(f"🔗 API URL: {api_url}")

        response = requests.get(api_url, timeout=10)
        print(f"📡 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"📄 Response keys: {list(data.keys())}")

            if data.get("RelatedTopics"):
                print(f"🔍 Found {len(data['RelatedTopics'])} related topics")
                for i, topic in enumerate(data["RelatedTopics"][:3]):
                    if isinstance(topic, dict):
                        print(f"  Topic {i+1}: {topic.get('Text', 'No text')[:100]}...")
                        print(f"    URL: {topic.get('FirstURL', 'No URL')}")

            if data.get("Abstract"):
                print(f"📝 Abstract: {data['Abstract'][:200]}...")
                print(f"📝 Abstract URL: {data.get('AbstractURL', 'No URL')}")
        else:
            print(f"❌ API request failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ DuckDuckGo API test failed: {e}")
        traceback.print_exc()


async def test_nodriver_import():
    """Test NoDriver import"""

    print("\n🥷 Testing NoDriver import...")

    try:
        from app.search.scrapers.nodriver_scraper import NoDriverScraper

        print("✅ NoDriverScraper imported successfully")

        scraper = NoDriverScraper()
        print("✅ NoDriverScraper initialized successfully")

    except Exception as e:
        print(f"❌ NoDriver import failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":

    async def main():
        await test_search_tool()
        await test_duckduckgo_api()
        await test_nodriver_import()

    asyncio.run(main())
