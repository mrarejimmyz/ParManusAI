#!/usr/bin/env python3
"""
Quick Agent Test - Simple test to check basic functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent.manus_core import Manus
from app.logger import logger


async def test_basic_functionality():
    """Test basic agent functionality."""
    print("🧪 Testing basic agent functionality...")

    try:
        agent = Manus()
        result = await asyncio.wait_for(
            agent.run("Create a brief analysis report about Tesla stock"), timeout=60
        )

        print(f"✅ Result received: {result[:200]}...")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    if success:
        print("🎉 Basic test passed!")
    else:
        print("❌ Basic test failed!")
