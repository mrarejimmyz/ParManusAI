#!/usr/bin/env python3
"""
Enhanced Search and Vision Content Extraction - End-to-End Test
Tests the complete pipeline: Search → Content Enhancement → Report Generation
"""

import asyncio
import os
import sys
import time
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_enhanced_search_basic():
    """Test 1: Basic search functionality with content enhancement"""
    print("🔍 TEST 1: Enhanced Search Basic Functionality")
    print("=" * 50)

    from app.tool.implementations.search_enhanced import EnhancedUnifiedSearchTool

    search_tool = EnhancedUnifiedSearchTool()

    test_queries = [
        "artificial intelligence 2025",
        "iran israel conflict news",
        "climate change solutions",
        "python programming tutorial",
    ]

    results_summary = []

    for query in test_queries:
        print(f"\n📝 Testing query: '{query}'")
        start_time = time.time()

        result = await search_tool._execute(query=query, num_results=3)

        elapsed = time.time() - start_time
        print(f"⏱️  Search completed in {elapsed:.2f} seconds")

        if result.success:
            print("✅ Search successful!")
            results = result.content.get("results", [])
            enhanced = result.content.get("content_fetched", False)

            results_summary.append(
                {
                    "query": query,
                    "results_count": len(results),
                    "enhanced": enhanced,
                    "time": elapsed,
                }
            )

            print(f"📊 Found {len(results)} results")
            print(f"🔧 Content enhanced: {enhanced}")

            # Show first result details
            if results:
                first_result = results[0]
                print(f"📰 Title: {first_result.get('title', 'No title')[:80]}...")
                print(f"🌐 Source: {first_result.get('source', 'Unknown')}")

                if "content_method" in first_result:
                    print(f"🔧 Content method: {first_result['content_method']}")

                if "content" in first_result:
                    content_length = len(first_result["content"])
                    content_preview = first_result["content"][:150].replace("\n", " ")
                    print(f"📄 Content: {content_length} chars - {content_preview}...")
                else:
                    print("📄 No enhanced content")
        else:
            print(f"❌ Search failed: {result.error}")
            results_summary.append(
                {
                    "query": query,
                    "results_count": 0,
                    "enhanced": False,
                    "time": elapsed,
                    "error": result.error,
                }
            )

    # Summary
    print(f"\n📊 SUMMARY:")
    total_queries = len(results_summary)
    successful_queries = len([r for r in results_summary if r["results_count"] > 0])
    enhanced_queries = len([r for r in results_summary if r.get("enhanced", False)])
    avg_time = sum(r["time"] for r in results_summary) / len(results_summary)

    print(f"✅ Successful queries: {successful_queries}/{total_queries}")
    print(f"🔧 Enhanced queries: {enhanced_queries}/{total_queries}")
    print(f"⏱️  Average time: {avg_time:.2f} seconds")

    print("\n" + "=" * 50)
    return successful_queries >= 3  # Expect at least 3/4 to succeed


async def test_vision_content_extraction():
    """Test 2: Vision-based content extraction"""
    print("🔍 TEST 2: Vision Content Extraction")
    print("=" * 50)

    from app.tool.implementations.search_enhanced import EnhancedUnifiedSearchTool

    search_tool = EnhancedUnifiedSearchTool()

    # Test current news generation (should always work)
    print("\n📰 Testing current news generation...")
    result = await search_tool._execute(
        query="iran israel latest developments news", num_results=2
    )

    if result.success:
        results = result.content.get("results", [])
        print(f"✅ Generated {len(results)} news results")

        for i, res in enumerate(results, 1):
            print(f"\n📄 Result {i}:")
            print(f"  Title: {res.get('title', 'No title')[:60]}...")
            print(f"  Source: {res.get('source', 'Unknown')}")

            if "content" in res:
                content_length = len(res["content"])
                print(f"  ✅ Enhanced content: {content_length} chars")
                print(f"  Method: {res.get('content_method', 'Not specified')}")

                # Verify content quality
                content = res["content"]
                has_structure = any(
                    marker in content
                    for marker in ["Key Points:", "Analysis:", "Overview:"]
                )
                print(f"  🏗️  Structured content: {has_structure}")
            else:
                print(f"  ❌ No enhanced content")
    else:
        print(f"❌ News generation failed: {result.error}")
        return False

    print("\n" + "=" * 50)
    return True


async def test_full_research_workflow():
    """Test 3: Full research workflow simulation"""
    print("🔍 TEST 3: Full Research Workflow")
    print("=" * 50)

    from app.tool.implementations.search_enhanced import EnhancedUnifiedSearchTool

    search_tool = EnhancedUnifiedSearchTool()

    # Simulate a multi-step research process
    research_topic = "renewable energy technology innovations 2025"
    search_queries = [
        "renewable energy technology 2025",
        "solar power innovations recent",
        "wind energy advances breakthrough",
        "energy storage battery technology",
    ]

    print(f"📝 Research topic: {research_topic}")
    print(f"🔍 Performing {len(search_queries)} searches...")

    all_results = []
    total_content_chars = 0
    start_time = time.time()

    for i, query in enumerate(search_queries, 1):
        print(f"\n📍 Search {i}/{len(search_queries)}: '{query}'")

        result = await search_tool._execute(query=query, num_results=3)

        if result.success:
            results = result.content.get("results", [])
            all_results.extend(results)

            # Count enhanced content
            enhanced_in_iteration = 0
            content_in_iteration = 0

            for res in results:
                if "content" in res:
                    enhanced_in_iteration += 1
                    content_in_iteration += len(res["content"])

            total_content_chars += content_in_iteration
            print(
                f"  ✅ Found {len(results)} results, {enhanced_in_iteration} enhanced, {content_in_iteration} chars"
            )
        else:
            print(f"  ❌ Search failed: {result.error}")

    elapsed = time.time() - start_time

    # Analyze results
    print(f"\n📊 RESEARCH WORKFLOW RESULTS:")
    print(f"⏱️  Total time: {elapsed:.2f} seconds")
    print(f"📄 Total results: {len(all_results)}")
    print(f"📝 Total content: {total_content_chars:,} characters")

    # Content enhancement analysis
    enhanced_count = sum(1 for r in all_results if "content" in r)
    enhancement_rate = (enhanced_count / len(all_results) * 100) if all_results else 0
    print(
        f"🔧 Enhancement rate: {enhancement_rate:.1f}% ({enhanced_count}/{len(all_results)})"
    )

    # Source diversity
    sources = set(r.get("source", "unknown") for r in all_results)
    print(f"🌐 Source diversity: {len(sources)} different sources")

    # Content methods
    methods = {}
    for result in all_results:
        method = result.get("content_method", "none")
        methods[method] = methods.get(method, 0) + 1

    print(f"🔧 Content methods:")
    for method, count in methods.items():
        print(f"  {method}: {count}")

    success = (
        len(all_results) >= 8 and enhancement_rate >= 50
    )  # Expect reasonable results
    print(f"\n{'✅ WORKFLOW SUCCESS' if success else '❌ WORKFLOW ISSUES'}")

    print("\n" + "=" * 50)
    return success


async def test_agent_integration():
    """Test 4: Integration with full agent system"""
    print("🔍 TEST 4: Agent Integration Test")
    print("=" * 50)

    # Test with actual agent command
    print("📝 Testing full agent research command...")

    import subprocess
    import tempfile

    # Run agent with research command
    cmd = [
        sys.executable,
        "main.py",
        "--prompt",
        "research quantum computing breakthroughs 2024 2025",
    ]

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        elapsed = time.time() - start_time

        print(f"⏱️  Agent completed in {elapsed:.2f} seconds")
        print(f"📊 Return code: {result.returncode}")

        if result.returncode == 0:
            print("✅ Agent execution successful!")

            # Check for generated report
            workspace_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "workspace"
            )
            if os.path.exists(workspace_dir):
                md_files = [f for f in os.listdir(workspace_dir) if f.endswith(".md")]
                recent_files = []

                for f in md_files:
                    file_path = os.path.join(workspace_dir, f)
                    if (
                        os.path.getmtime(file_path) > start_time - 60
                    ):  # Modified in last minute before test
                        recent_files.append(f)

                if recent_files:
                    print(f"📄 Generated reports: {recent_files}")

                    # Analyze the most recent report
                    latest_file = max(
                        recent_files,
                        key=lambda f: os.path.getmtime(os.path.join(workspace_dir, f)),
                    )
                    report_path = os.path.join(workspace_dir, latest_file)

                    with open(report_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    print(f"📊 Report length: {len(content)} characters")

                    # Check for quality indicators
                    quality_indicators = [
                        "Key Points:",
                        "Analysis:",
                        "Source:",
                        "Research",
                        "content",
                    ]

                    found_indicators = sum(
                        1 for indicator in quality_indicators if indicator in content
                    )
                    print(
                        f"🏆 Quality indicators: {found_indicators}/{len(quality_indicators)}"
                    )

                    success = len(content) > 1000 and found_indicators >= 3
                    print(
                        f"{'✅ REPORT QUALITY GOOD' if success else '⚠️ REPORT QUALITY CONCERNS'}"
                    )

                    return success
                else:
                    print("❌ No recent report files found")
                    return False
            else:
                print("❌ Workspace directory not found")
                return False
        else:
            print(f"❌ Agent execution failed!")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Agent execution timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ Agent execution error: {e}")
        return False

    print("\n" + "=" * 50)


async def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 ENHANCED SEARCH & VISION - END-TO-END TEST SUITE")
    print("=" * 60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    tests = [
        ("Basic Search", test_enhanced_search_basic),
        ("Vision Content", test_vision_content_extraction),
        ("Research Workflow", test_full_research_workflow),
        ("Agent Integration", test_agent_integration),
    ]

    results = []
    start_time = time.time()

    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            print(
                f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}"
            )
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))

    # Final summary
    elapsed = time.time() - start_time
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n" + "=" * 60)
    print("🏁 TEST SUITE SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total execution time: {elapsed:.2f} seconds")
    print(f"✅ Tests passed: {passed}/{total}")
    print(f"❌ Tests failed: {total - passed}/{total}")
    print(f"📊 Success rate: {(passed/total*100):.1f}%")

    print(f"\nDetailed results:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status} {test_name}")

    if passed == total:
        print(
            "\n🎉 ALL TESTS PASSED! Enhanced search and vision system is working correctly."
        )
    else:
        print(
            f"\n⚠️  {total - passed} test(s) failed. Review the output above for details."
        )

    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
