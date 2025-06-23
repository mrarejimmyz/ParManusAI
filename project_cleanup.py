#!/usr/bin/env python3
"""
PROJECT FILES CLEANUP - Based on main.py dependency analysis
Only removes PROJECT files that are NOT imported from main.py
"""

import os
import shutil
from pathlib import Path


def safe_remove_file(file_path: str):
    """Safely remove a file with backup."""
    try:
        if os.path.exists(file_path):
            # Create backup
            backup_path = f"{file_path}.unused_backup"
            shutil.copy2(file_path, backup_path)

            # Remove original
            os.remove(file_path)
            print(f"🗑️ Removed: {file_path}")
            print(f"💾 Backup: {backup_path}")
        else:
            print(f"⚠️ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error removing {file_path}: {e}")


def main():
    print("🧹 PROJECT FILES CLEANUP")
    print("Removing PROJECT files NOT used by main.py")
    print("=" * 50)

    # Only PROJECT files that are NOT in the dependency tree
    unused_project_files = [
        # BROWSER TOOLS - NOT USED by main.py
        "app/tool/enhanced_browser.py",  # 13,280 chars - NOT imported
        "app/tool/browser/modern_tool.py",  # 12,575 chars - NOT imported
        # AGENT VISION - NOT USED
        "app/agent/vision_browser_interaction.py",  # 10,608 chars - NOT imported
        # BACKUP/ALTERNATE TOOL MANAGERS - NOT USED
        "app/agent/core/tool_manager_backup.py",  # 8,788 chars - NOT imported
        "app/agent/core/tool_manager_fixed.py",  # 8,575 chars - NOT imported
        # LLM TOOL PATCH - NOT USED
        "app/llm_tool_patch.py",  # 20,476 chars - NOT imported
        # LEGACY BROWSER TOOLS - NOT USED
        "archive/legacy_tools/browser_old.py",  # 14,928 chars
        "archive/legacy_tools/browser_basic_old.py",  # 14,921 chars
        "archive/legacy_tools/browser_use_tool_modern.py",  # 11,210 chars
        # TEST FILES (many unused)
        "test_tool_call_argument_fixing_complete.py",
        "test_llm_tool_fixing_pipeline.py",
        "debug_tool_call_generation.py",
        "test_tool_call_argument_debug_fixed.py",
        "test_browser_hallucination_protection.py",
        "test_tool_call_argument_debug.py",
        "test_comprehensive_browser_open_fix.py",
        "test_tool_execution_comprehensive.py",
        "test_llm_tool_format.py",
        "test_tool_execution_debug.py",
        "test_tool_argument_validation.py",
        "test_llm_tool_call_debug.py",
        "debug_tool_call_processing.py",
        "test_browser_open_action_fix.py",
        "test_trump_report_tool_call.py",
        "test_tool_format.py",
        "test_browser_enhanced_fix.py",
        "test_manus_tools.py",
        "debug_tool_call_format.py",
        "test_available_tools.py",
        "test_basic_tool.py",
        "test_toolcall_agent_early_detection.py",
        "test_tool_collection_fix.py",
        "test_simple_tool_exec.py",
    ]

    removed_count = 0
    total_size_saved = 0

    for file_path in unused_project_files:
        full_path = os.path.join(Path(__file__).parent, file_path)

        if os.path.exists(full_path):
            # Get file size before removing
            size = os.path.getsize(full_path)
            total_size_saved += size

            safe_remove_file(full_path)
            removed_count += 1
        else:
            print(f"⚠️ Already removed or not found: {file_path}")

    print(f"\n✅ CLEANUP SUMMARY:")
    print(f"   Files removed: {removed_count}")
    print(f"   Size saved: {total_size_saved:,} bytes ({total_size_saved/1024:.1f} KB)")

    # Show remaining key browser files
    print(f"\n📁 REMAINING KEY BROWSER FILES:")
    key_browser_files = [
        "app/tool/browser_use_tool.py",  # Simple wrapper - USED
        "app/tool/implementations/browser_enhanced.py",  # Main implementation - USED
        "app/agent/browser.py",  # Browser agent - USED
        "app/agent/manus_browser_handler.py",  # Browser handler - USED
    ]

    for file_path in key_browser_files:
        full_path = os.path.join(Path(__file__).parent, file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"   ✅ {file_path} ({size:,} bytes)")

    print(f"\n🎯 NEXT STEPS:")
    print("1. Run tests to ensure nothing is broken")
    print("2. Consider consolidating remaining browser components")
    print("3. Remove more redundant test files if needed")


if __name__ == "__main__":
    main()
