#!/usr/bin/env python3
"""
Cleanup script to remove duplicate reports and test the fixed logic
"""

import glob
import os
from datetime import datetime


def cleanup_duplicate_reports():
    """Remove duplicate reports, keeping only the latest one"""
    print("🧹 CLEANING UP DUPLICATE REPORTS")

    workspace_path = "workspace"
    if not os.path.exists(workspace_path):
        print("❌ Workspace directory not found")
        return

    # Find all analysis reports
    pattern = os.path.join(workspace_path, "analysis_*.md")
    report_files = glob.glob(pattern)

    if len(report_files) <= 1:
        print(f"✅ Only {len(report_files)} report(s) found, no cleanup needed")
        return

    print(f"📄 Found {len(report_files)} report files")

    # Group reports by base task (everything before the timestamp)
    report_groups = {}
    for filepath in report_files:
        filename = os.path.basename(filepath)
        # Extract everything before the last timestamp pattern
        base_name = "_".join(filename.split("_")[:-2])  # Remove date and time parts

        if base_name not in report_groups:
            report_groups[base_name] = []
        report_groups[base_name].append(filepath)

    print(f"📊 Found {len(report_groups)} unique report types")

    total_removed = 0
    for base_name, files in report_groups.items():
        if len(files) > 1:
            print(f"\n🔍 Processing {base_name}: {len(files)} files")

            # Sort by modification time and keep the latest
            files.sort(key=os.path.getmtime, reverse=True)
            latest_file = files[0]
            old_files = files[1:]

            print(f"✅ Keeping: {os.path.basename(latest_file)}")

            for old_file in old_files:
                try:
                    os.remove(old_file)
                    print(f"🗑️ Removed: {os.path.basename(old_file)}")
                    total_removed += 1
                except Exception as e:
                    print(f"❌ Failed to remove {os.path.basename(old_file)}: {e}")
        else:
            print(f"✅ {base_name}: Only 1 file, no cleanup needed")

    print(f"\n🎉 Cleanup complete! Removed {total_removed} duplicate files")


def test_existing_report_logic():
    """Test the existing report finder logic"""
    print("\n🧪 TESTING EXISTING REPORT LOGIC")

    try:
        import sys

        sys.path.append(".")

        class MockAgent:
            def __init__(self):
                self.workspace_root = "workspace"

        from app.agent.actions.simplified_manus_action_executor import (
            SimplifiedManusActionExecutor,
        )

        executor = SimplifiedManusActionExecutor(MockAgent())

        # Test with the GitHub analysis task
        task = "Analyze the GitHub repository of mrarejimmyz/ParManusAI and provide insights"
        existing = executor._find_existing_report(task)

        if existing:
            print(f"✅ Found existing report: {os.path.basename(existing)}")

            # Check completion status
            analysis = executor.completion_analyzer.analyze_report_completeness(
                existing
            )
            completion_pct = analysis.get("completion_percentage", 0)
            missing = analysis.get("missing_sections", [])

            print(f"📊 Completion: {completion_pct:.1f}%")
            print(f"📋 Missing sections: {missing}")

            if completion_pct >= 90:
                print(
                    "✅ Report is complete - agent should use this instead of creating new one"
                )
            else:
                print("⚠️ Report is incomplete - agent should enhance it")
        else:
            print("❌ No existing report found")

    except Exception as e:
        print(f"❌ Test failed: {e}")


def main():
    """Run cleanup and tests"""
    print("🚀 DUPLICATE REPORT CLEANUP & TEST")
    print("=" * 50)

    cleanup_duplicate_reports()
    test_existing_report_logic()

    print("\n" + "=" * 50)
    print("✅ All operations complete!")
    print("📝 The agent should now:")
    print("   - Find existing reports instead of creating new ones")
    print("   - Update incomplete reports to 100% completion")
    print("   - Stop creating duplicate files")


if __name__ == "__main__":
    main()
