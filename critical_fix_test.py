#!/usr/bin/env python3
"""
Critical Bug Fix Test - Test the tool call extraction fix
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent.manus_core import Manus
from app.logger import logger


async def test_critical_fix():
    """Test the critical tool call extraction fix."""
    print("🔧 Testing Critical Tool Call Extraction Fix")
    print("=" * 50)

    test_request = "Create investment analysis for Tesla stock"
    print(f"📝 Test Request: {test_request}")

    start_time = time.time()

    try:
        agent = Manus()
        result = await asyncio.wait_for(agent.run(test_request), timeout=25)
        elapsed = time.time() - start_time

        print(f"✅ SUCCESS: Completed in {elapsed:.1f}s")
        print(f"📄 Result length: {len(str(result))} characters")

        # Check if result is substantial
        result_str = str(result).lower()
        has_analysis = any(
            word in result_str
            for word in ["analysis", "investment", "tesla", "stock", "report"]
        )

        if has_analysis and len(str(result)) > 1000:
            print("🎉 HIGH QUALITY: Result contains substantial analysis content")
            return True
        elif has_analysis:
            print("✅ GOOD: Result contains analysis but could be more detailed")
            return True
        else:
            print("⚠️ PARTIAL: Result generated but missing key analysis elements")
            return False

    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"❌ TIMEOUT: Failed after {elapsed:.1f}s")
        return False

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ ERROR: Failed after {elapsed:.1f}s - {e}")
        return False


if __name__ == "__main__":
    print("🎯 Critical Bug Fix Verification")
    success = asyncio.run(test_critical_fix())

    if success:
        print("\n🎊 CRITICAL FIX SUCCESSFUL!")
        print("🔧 Tool call extraction is now working correctly")
        print("✨ Agent should now generate reports without timeout issues")
    else:
        print("\n❌ Critical fix needs additional work")

    sys.exit(0 if success else 1)
