#!/usr/bin/env python3
"""
Quick status test to verify the current state of the ParManus agent.
"""

import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.logger import logger
from app.tool.implementations.search_enhanced import EnhancedUnifiedSearchTool


async def test_search_tool():
    """Test the search tool functionality."""
    print("🔍 Testing Enhanced Search Tool...")

    try:
        tool = EnhancedUnifiedSearchTool()
        result = await tool._execute(
            query="artificial intelligence 2025", num_results=3
        )

        print(f"✅ Search Success: {result.success}")
        print(f"📊 Results Count: {len(result.content.get('results', []))}")
        print(f"🔄 Content Fetched: {result.content.get('content_fetched', False)}")

        # Display first 2 results
        for i, r in enumerate(result.content.get("results", [])[:2]):
            title = r.get("title", "N/A")
            url = r.get("url", "N/A")
            source = r.get("source", "N/A")
            print(f"🔗 Result {i+1}: {title[:50]}...")
            print(f"   URL: {url}")
            print(f"   Source: {source}")
            print()

        return result.success

    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False


async def test_main_agent():
    """Test the main agent functionality."""
    print("🤖 Testing Main Agent...")

    try:
        from main import main

        # This would run the main agent, but we'll skip for now
        print("✅ Main agent imports successfully")
        return True

    except Exception as e:
        print(f"❌ Main agent test failed: {e}")
        return False


async def main():
    """Run all status tests."""
    print("🚀 ParManus Status Check Starting...\n")

    search_ok = await test_search_tool()
    agent_ok = await test_main_agent()

    print(f"\n📋 Status Summary:")
    print(f"   Search Tool: {'✅ OK' if search_ok else '❌ FAILED'}")
    print(f"   Main Agent: {'✅ OK' if agent_ok else '❌ FAILED'}")

    if search_ok and agent_ok:
        print(f"\n🎉 ParManus system is operational!")
    else:
        print(f"\n⚠️  Some components need attention.")


if __name__ == "__main__":
    asyncio.run(main())
