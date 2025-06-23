#!/usr/bin/env python3
"""
Quick NoDriver test to verify it's working correctly.
"""

import asyncio
import sys

from app.search.scrapers.nodriver_scraper import NoDriverScraper


async def quick_test():
    """Quick test of NoDriver functionality."""
    print("🔥 Quick NoDriver Test")
    print("=" * 40)

    scraper = NoDriverScraper()

    # Test with a simple page
    url = "https://httpbin.org/html"

    try:
        print(f"🎯 Testing: {url}")
        content = await scraper.scrape_with_nodriver(url, "Extract content")

        if content:
            print(f"✅ Success! Content length: {len(content)} characters")
            print(f"📄 Preview: {content[:100]}...")
            return True
        else:
            print("❌ No content extracted")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(quick_test())
    if result:
        print("\n✅ NoDriver is working correctly!")
    else:
        print("\n❌ NoDriver test failed!")
