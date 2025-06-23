#!/usr/bin/env python3
"""
Diagnostic Test for Agent Workflow
Identifies exactly what happens during agent execution and why it might timeout.
"""

import asyncio
import os
import sys
import time
import traceback

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

from app.logger import logger


async def diagnose_agent_workflow():
    """Run detailed diagnostic of agent workflow with extensive logging."""
    print("🔍 DIAGNOSTIC: Agent Workflow Analysis")
    print("=" * 60)

    try:
        # Ensure output directory exists
        os.makedirs("agent_test_output", exist_ok=True)

        # Clear any existing test files
        test_file = "agent_test_output/research_report.txt"
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"✅ Cleared existing test file: {test_file}")

        # Import agent
        print("📦 Importing agent...")
        from app.agent.manus_core import Manus

        # Create agent
        print("🤖 Creating agent...")
        agent = Manus()
        print(f"✅ Agent created: {agent}")  # Check agent tools
        if hasattr(agent, "available_tools"):
            if hasattr(agent.available_tools, "tool_map"):
                print(
                    f"🛠️  Available tools: {list(agent.available_tools.tool_map.keys())}"
                )
            elif hasattr(agent.available_tools, "tools"):
                tool_names = [
                    getattr(tool, "name", str(tool))
                    for tool in agent.available_tools.tools
                ]
                print(f"🛠️  Available tools: {tool_names}")
            else:
                print(f"🛠️  Available tools object: {type(agent.available_tools)}")
        else:
            print("⚠️  No available_tools attribute found")

        # Define task
        task = """
Research "Python web frameworks" using web search.
Create a file called 'research_report.txt' in the 'agent_test_output' directory with:
1. Search results with real URLs
2. Summary of the frameworks
3. Comparison of features

Use real web search and include actual URLs. Complete the task and terminate.
"""

        print(f"📋 Task defined: {task[:100]}...")

        # Track execution with detailed timing
        start_time = time.time()
        step_count = 0
        max_steps = 20  # Reasonable limit

        print("🚀 Starting agent execution...")

        # Run agent step by step with monitoring
        try:
            # Initialize agent
            await agent.add_user_message(task)
            print(f"✅ Added user message at {time.time() - start_time:.1f}s")

            while step_count < max_steps:
                step_count += 1
                step_start = time.time()

                print(f"\n🔄 STEP {step_count} (at {time.time() - start_time:.1f}s)")

                # Check agent state
                if hasattr(agent, "state"):
                    print(f"   State: {agent.state}")

                # Execute one step
                result = await asyncio.wait_for(
                    agent.step(), timeout=30
                )  # 30s per step
                step_duration = time.time() - step_start

                print(f"   Duration: {step_duration:.1f}s")
                print(
                    f"   Result: {result[:200]}..."
                    if len(str(result)) > 200
                    else f"   Result: {result}"
                )

                # Check if agent finished
                if hasattr(agent, "state") and str(agent.state).upper() == "FINISHED":
                    print(f"✅ Agent finished after {step_count} steps")
                    break

                # Check for completion patterns in result
                if any(
                    phrase in str(result).lower()
                    for phrase in ["completed", "finished", "done", "created"]
                ):
                    print(f"✅ Completion detected in result")
                    break

                # Check if file was created
                if os.path.exists(test_file):
                    print(f"✅ Output file detected: {test_file}")
                    break

                # Brief pause between steps
                await asyncio.sleep(0.1)

            else:
                print(f"⚠️  Reached maximum steps ({max_steps}) without completion")

        except asyncio.TimeoutError:
            print(f"⏰ Step timeout after {step_count} steps")
        except Exception as e:
            print(f"❌ Step execution error: {e}")
            traceback.print_exc()

        total_time = time.time() - start_time
        print(f"\n📊 Execution completed in {total_time:.1f}s after {step_count} steps")

        # Check final results
        if os.path.exists(test_file):
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            print(f"✅ Output file created: {len(content)} characters")

            # Check for URLs
            import re

            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
            print(f"🔗 URLs found: {len(urls)}")

            if urls:
                print("   Sample URLs:")
                for url in urls[:3]:
                    print(f"   - {url}")

            # Show content preview
            print(f"\n📄 Content preview:")
            print(content[:500] + "..." if len(content) > 500 else content)

            return True
        else:
            print(f"❌ No output file created at {test_file}")

            # Check if file was created elsewhere
            for root, dirs, files in os.walk("."):
                if "research_report.txt" in files:
                    found_path = os.path.join(root, "research_report.txt")
                    print(f"🔍 Found file at alternate location: {found_path}")

            return False

    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        traceback.print_exc()
        return False


async def main():
    """Run the diagnostic."""
    success = await diagnose_agent_workflow()
    print(f"\n{'='*60}")
    print(f"DIAGNOSTIC RESULT: {'SUCCESS' if success else 'FAILURE'}")
    return success


if __name__ == "__main__":
    asyncio.run(main())
