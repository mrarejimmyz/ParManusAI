#!/usr/bin/env python3
"""
Simple focused test to verify the report generation fix.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent.manus_core import Manus
from app.logger import logger


async def test_quantum_report():
    """Test quantum computing report generation."""
    print("🧪 Testing quantum computing report generation...")

    # Clean up workspace first
    workspace_path = "workspace"
    if os.path.exists(workspace_path):
        # Remove existing markdown files
        for file in os.listdir(workspace_path):
            if file.endswith(".md"):
                os.remove(os.path.join(workspace_path, file))

    # Create agent
    agent = Manus()

    # Test request
    test_message = "Research quantum computing developments in 2025"

    print(f"📝 Request: {test_message}")

    try:
        result = await asyncio.wait_for(agent.run(test_message), timeout=180)
        print(f"✅ Agent result: {result[:200]}...")

        # Check for report files
        if os.path.exists(workspace_path):
            md_files = [f for f in os.listdir(workspace_path) if f.endswith(".md")]
            print(f"📄 Found {len(md_files)} markdown files: {md_files}")

            if md_files:
                # Check the content of the first report
                with open(
                    os.path.join(workspace_path, md_files[0]), "r", encoding="utf-8"
                ) as f:
                    content = f.read()
                print(f"📊 Report size: {len(content)} characters")
                print(f"📝 First 300 characters:\n{content[:300]}...")

                if len(content) > 200:  # Minimum substantial content
                    print("✅ SUCCESS: Report generated with substantial content")
                    return True
                else:
                    print("⚠️ Report too short")
                    return False
            else:
                print("❌ No report files found")
                return False
        else:
            print("❌ Workspace not found")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    print("🚀 Report Generation Fix Test")
    print("=" * 40)

    success = await test_quantum_report()

    print("\n" + "=" * 40)
    if success:
        print("✅ TEST PASSED: Report generation fix works!")
    else:
        print("❌ TEST FAILED: Report generation needs more work")

    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
