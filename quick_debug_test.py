#!/usr/bin/env python3
"""
Quick Debug Test - Just run one thinking step to see JSON parsing
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent.manus_core import Manus
from app.logger import logger


async def quick_debug_test():
    """Quick test to debug JSON parsing."""
    print("🔧 Quick Debug Test")

    test_request = "Create investment analysis for Tesla stock"
    print(f"📝 Test Request: {test_request}")

    try:
        agent = Manus()
        # Just run one step to see the debug output
        await agent.add_user_message(test_request)

        # Run the thinking step directly
        if hasattr(agent, "thinking_engine"):
            await agent.thinking_engine.think()

        print("✅ Debug step completed")
        return True

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(quick_debug_test())
    print(f"Debug result: {'SUCCESS' if success else 'FAILED'}")
