#!/usr/bin/env python3
"""
Quick validation test for NoDriver + Vision integration
"""

import asyncio
import sys


async def quick_integration_test():
    """Quick test of the integration."""
    print("🔥 Quick NoDriver + Vision Integration Test")
    print("=" * 50)

    try:
        # Test imports
        print("📋 Testing imports...")
        from app.search.scrapers.nodriver_scraper import NoDriverScraper
        from app.tool.implementations.browser_enhanced import EnhancedUnifiedBrowserTool
        from app.tool.implementations.search_enhanced import EnhancedUnifiedSearchTool

        print("✅ All imports successful")

        # Test NoDriver scraper initialization
        print("📋 Testing NoDriver initialization...")
        scraper = NoDriverScraper()
        print("✅ NoDriver scraper initialized")

        # Test browser tool initialization
        print("📋 Testing browser tool initialization...")
        browser_tool = EnhancedUnifiedBrowserTool()
        print("✅ Browser tool initialized")

        # Test search tool initialization
        print("📋 Testing search tool initialization...")
        search_tool = EnhancedUnifiedSearchTool()
        print("✅ Search tool initialized")

        # Test simple URL with NoDriver
        print("📋 Testing simple URL with NoDriver...")
        test_url = "https://httpbin.org/html"

        try:
            content = await scraper.scrape_with_nodriver(test_url, "Extract content")
            if content and len(content) > 20:
                print(f"✅ NoDriver extraction successful: {len(content)} characters")
                print(f"📄 Preview: {content[:100]}...")
            else:
                print("❌ NoDriver extraction failed or insufficient content")
        except Exception as e:
            print(f"❌ NoDriver test failed: {e}")

        # Test vision integration via search tool
        print("📋 Testing vision integration...")
        try:
            vision_content = await search_tool._extract_content_with_vision(test_url)
            if vision_content and len(vision_content) > 20:
                print(
                    f"✅ Vision integration successful: {len(vision_content)} characters"
                )
                print(f"📄 Preview: {vision_content[:100]}...")
            else:
                print("❌ Vision integration failed or insufficient content")
        except Exception as e:
            print(f"❌ Vision integration test failed: {e}")

        print("\n🎉 Quick integration test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(quick_integration_test())
