#!/usr/bin/env python3
"""
Final verification test for multi-task agent completion
"""

import asyncio
import os
import shutil
import time
from pathlib import Path

from app.agent.manus_core import Manus


async def test_multi_task_completion():
    """Test that agent properly handles multi-task requests and terminates correctly."""
    print("🚀 FINAL MULTI-TASK VERIFICATION TEST")
    print("=" * 50)

    # Clean up previous test
    test_dir = Path("final_verification_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)

    start_time = time.time()

    try:
        # Create agent
        agent = await Manus.create()
        print("✅ Agent created successfully")

        # Multi-task request
        request = """I need you to create MULTIPLE files for a comprehensive tutorial. This is a multi-task request:

TASK 1: Create 'final_verification_test/python_guide.md' with comprehensive Python tutorial
TASK 2: Create 'final_verification_test/web_dev_guide.md' with web development basics
TASK 3: Create 'final_verification_test/data_science_guide.md' with data science overview
TASK 4: Create 'final_verification_test/completion_report.md' with a summary of all created files

Complete ALL FOUR tasks before terminating. This involves multiple files and should not terminate early."""

        print("📝 MULTI-TASK REQUEST:")
        print(request[:200] + "...")
        print("\n⏳ Running agent...")

        # Run agent
        result = await agent.run(request)

        end_time = time.time()
        duration = end_time - start_time

        print(f"✅ Agent completed in {duration:.2f} seconds")
        print(f"🔤 Result: {str(result)[:100]}...")

        # Verify all files were created
        expected_files = [
            "final_verification_test/python_guide.md",
            "final_verification_test/web_dev_guide.md",
            "final_verification_test/data_science_guide.md",
            "final_verification_test/completion_report.md",
        ]

        created_files = []
        for file_path in expected_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                created_files.append(file_path)
                print(f"✅ {file_path} created ({size} chars)")
            else:
                print(f"❌ {file_path} missing")

        # Verify completion
        if len(created_files) == len(expected_files):
            print(
                f"\n🎉 SUCCESS: Created {len(created_files)}/{len(expected_files)} requested files!"
            )
            print("✅ Agent correctly handled multi-task request")
            print("✅ Agent terminated after completing all tasks")
            print("🏆 FINAL RESULT: SUCCESS")
            return True
        else:
            print(
                f"\n❌ FAILURE: Only created {len(created_files)}/{len(expected_files)} files"
            )
            print("🔴 FINAL RESULT: FAILURE")
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run verification test."""
    print("🧪 STARTING FINAL VERIFICATION TEST")
    print("=" * 60)

    # Test multi-task completion
    multi_task_success = await test_multi_task_completion()

    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Multi-task handling: {'✅ PASS' if multi_task_success else '❌ FAIL'}")

    print(
        f"\n🏆 OVERALL RESULT: {'✅ TEST PASSED' if multi_task_success else '❌ TEST FAILED'}"
    )

    return multi_task_success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
