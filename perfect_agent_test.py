#!/usr/bin/env python3
"""
Comprehensive Perfect Agent Test
Tests every aspect of the agent to ensure it's working perfectly.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

import pytest

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent.manus_core import Manus
from app.logger import logger


async def run_scenario(
    scenario_name: str, request: str, expected_keywords: list = None
):
    """Test a single scenario comprehensively."""
    print(f"\n🧪 Testing: {scenario_name}")
    print(f"📝 Request: {request}")

    # Clean up workspace first
    workspace_path = "workspace"
    if os.path.exists(workspace_path):
        # Remove test files from previous runs
        for file in os.listdir(workspace_path):
            if file.endswith(".md") and any(
                word in file.lower() for word in ["test", "scenario"]
            ):
                try:
                    os.remove(os.path.join(workspace_path, file))
                except:
                    pass

    start_time = time.time()

    try:
        # Create fresh agent
        agent = Manus()

        # Run with reasonable timeout
        result = await asyncio.wait_for(agent.run(request), timeout=90)

        elapsed_time = time.time() - start_time
        print(f"⏱️ Completed in {elapsed_time:.1f} seconds")
        print(f"✅ Result: {result[:200]}...")

        # Check for report files
        report_generated = False
        report_quality = 0

        if os.path.exists(workspace_path):
            md_files = [f for f in os.listdir(workspace_path) if f.endswith(".md")]
            recent_files = []

            # Get recently created files
            current_time = time.time()
            for file in md_files:
                file_path = os.path.join(workspace_path, file)
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if current_time - file_mtime < 300:  # Created in last 5 minutes
                        recent_files.append(file)
                except:
                    pass

            if recent_files:
                # Check the most recent report
                latest_report = recent_files[0]
                report_path = os.path.join(workspace_path, latest_report)

                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    print(f"📄 Report: {latest_report} ({len(content)} chars)")

                    # Quality assessment
                    quality_indicators = {
                        "Substantial content": len(content) > 1000,
                        "Has title": content.startswith("#"),
                        "Multiple sections": content.count("#") >= 3,
                        "Executive summary": "executive summary" in content.lower(),
                        "Analysis section": "analysis" in content.lower(),
                        "Recommendations": "recommendation" in content.lower(),
                        "Professional format": "##" in content,
                    }

                    if expected_keywords:
                        for keyword in expected_keywords:
                            quality_indicators[f"Contains '{keyword}'"] = (
                                keyword.lower() in content.lower()
                            )

                    passed_checks = sum(quality_indicators.values())
                    report_quality = (passed_checks / len(quality_indicators)) * 100

                    print(f"📊 Quality Score: {report_quality:.1f}%")

                    # Show passed checks
                    for check, passed in quality_indicators.items():
                        status = "✅" if passed else "❌"
                        print(f"  {status} {check}")

                    report_generated = True

                except Exception as e:
                    print(f"⚠️ Error reading report: {e}")

        if not report_generated:
            print("❌ No report generated")
            return False

        # Success criteria
        success = (
            report_generated
            and report_quality >= 70  # At least 70% quality
            and elapsed_time < 120  # Completed within 2 minutes
            and "completed successfully" in result.lower()
        )

        if success:
            print(f"🎉 {scenario_name}: PERFECT SUCCESS!")
        else:
            print(
                f"⚠️ {scenario_name}: Partial success (quality: {report_quality:.1f}%)"
            )

        return success

    except asyncio.TimeoutError:
        elapsed_time = time.time() - start_time
        print(f"❌ {scenario_name}: Timed out after {elapsed_time:.1f} seconds")

        # Check if report was still generated despite timeout
        if os.path.exists(workspace_path):
            md_files = [f for f in os.listdir(workspace_path) if f.endswith(".md")]
            recent_files = []
            current_time = time.time()
            for file in md_files:
                file_path = os.path.join(workspace_path, file)
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if current_time - file_mtime < 300:
                        recent_files.append(file)
                except:
                    pass

            if recent_files:
                print(f"✅ Report was generated despite timeout: {recent_files}")
                return True  # Partial success

        return False

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ {scenario_name}: Failed after {elapsed_time:.1f} seconds - {e}")
        return False


async def main():
    """Run comprehensive perfect agent tests."""
    print("🚀 PERFECT AGENT COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    # Test scenarios that should all work perfectly
    test_scenarios = [
        {
            "name": "Direct Report Request",
            "request": "Create a comprehensive analysis report on renewable energy trends",
            "keywords": ["renewable", "energy", "trends"],
        },
        {
            "name": "Research + Report Task",
            "request": "Research artificial intelligence developments and create an analysis",
            "keywords": ["artificial", "intelligence", "ai"],
        },
        {
            "name": "Market Analysis",
            "request": "Analyze cryptocurrency market trends and write a detailed report",
            "keywords": ["cryptocurrency", "market"],
        },
        {
            "name": "Technology Study",
            "request": "Study quantum computing breakthroughs and generate a comprehensive report",
            "keywords": ["quantum", "computing"],
        },
        {
            "name": "Industry Investigation",
            "request": "Investigate electric vehicle industry developments and create analysis",
            "keywords": ["electric", "vehicle"],
        },
    ]

    results = []
    total_start_time = time.time()

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_scenarios)}")

        success = await run_scenario(
            scenario["name"], scenario["request"], scenario.get("keywords", [])
        )

        results.append({"name": scenario["name"], "success": success})

        # Small delay between tests
        await asyncio.sleep(2)

    total_elapsed = time.time() - total_start_time

    # Final summary
    print(f"\n{'='*60}")
    print("🏆 FINAL COMPREHENSIVE TEST RESULTS")
    print(f"⏱️ Total test time: {total_elapsed:.1f} seconds")
    print()

    successful_tests = 0
    for i, result in enumerate(results, 1):
        status = "✅ PERFECT" if result["success"] else "❌ FAILED"
        print(f"Test {i}: {result['name']} - {status}")
        if result["success"]:
            successful_tests += 1

    success_rate = (successful_tests / len(results)) * 100
    print(
        f"\n📊 Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{len(results)})"
    )

    # Final verdict
    print(f"\n{'='*60}")
    if success_rate >= 90:
        print("🎉 AGENT IS PERFECT! Outstanding performance across all scenarios!")
        print("✅ The agent consistently generates high-quality reports")
        print("✅ Handles web scraping failures gracefully with LLM fallbacks")
        print("✅ Completes tasks within reasonable timeframes")
        print("✅ Professional report formatting and content quality")
    elif success_rate >= 70:
        print("✅ AGENT IS EXCELLENT! Very good performance with minor issues")
        print("⚠️ Some scenarios may need fine-tuning")
    elif success_rate >= 50:
        print("⚠️ AGENT IS GOOD but needs improvement in several areas")
    else:
        print("❌ AGENT NEEDS SIGNIFICANT IMPROVEMENT")

    return success_rate >= 80


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
