#!/usr/bin/env python3
"""
Codebase Cleanup Script - Phase 1: Remove Redundant Browser Tools
CRITICAL: This removes duplicate/redundant files to clean up the massive codebase duplication
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def check_file_usage(file_path: str) -> bool:
    """Check if a file is being imported/used elsewhere in the codebase."""
    import re
    import subprocess

    try:
        # Get just the filename without extension for import checking
        file_name = Path(file_path).stem

        # Search for imports of this file
        result = subprocess.run(
            [
                "grep",
                "-r",
                "--include=*.py",
                f"from.*{file_name}\\|import.*{file_name}",
                ".",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0:
            imports = result.stdout.strip().split("\n")
            # Filter out self-references
            real_imports = [imp for imp in imports if file_path not in imp]
            return len(real_imports) > 0

        return False
    except Exception as e:
        print(f"⚠️ Could not check usage for {file_path}: {e}")
        return True  # Err on the side of caution


def backup_file_if_has_content(file_path: str) -> bool:
    """Backup file if it has meaningful content."""
    try:
        if not os.path.exists(file_path):
            print(f"📝 File doesn't exist: {file_path}")
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if len(content) < 100:  # Very small or empty files
            print(f"📝 File is empty/minimal: {file_path}")
            return False

        # Check if it's just imports and basic structure
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        meaningful_lines = [
            line
            for line in lines
            if not (
                line.startswith("#")
                or line.startswith("import ")
                or line.startswith("from ")
                or line.startswith('"""')
                or line.startswith("'''")
                or line == "pass"
            )
        ]

        if len(meaningful_lines) < 5:
            print(f"📝 File has minimal content: {file_path}")
            return False

        # File has meaningful content, back it up
        backup_path = f"{file_path}.backup"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"💾 Backed up {file_path} to {backup_path}")
        return True

    except Exception as e:
        print(f"❌ Error backing up {file_path}: {e}")
        return False


def safe_remove_file(file_path: str, reason: str) -> bool:
    """Safely remove a file after checks."""
    try:
        if not os.path.exists(file_path):
            print(f"✅ Already removed: {file_path}")
            return True

        print(f"\n🔍 Analyzing: {file_path}")
        print(f"📋 Reason: {reason}")

        # Check if file is being used
        if check_file_usage(file_path):
            print(f"⚠️ SKIPPING: {file_path} - Still being imported/used")
            return False

        # Backup if has content
        has_content = backup_file_if_has_content(file_path)

        # Remove the file
        os.remove(file_path)
        print(f"🗑️ REMOVED: {file_path}")

        if has_content:
            print(f"💾 Content was backed up before removal")

        return True

    except Exception as e:
        print(f"❌ Error removing {file_path}: {e}")
        return False


def main():
    """Main cleanup function."""
    print("🧹 CODEBASE CLEANUP - Phase 1: Browser Tool Redundancy Removal")
    print("=" * 70)

    # Files to remove (redundant/duplicate browser tools)
    files_to_remove = [
        # Empty/minimal files
        ("app/tool/browser_use_tool_modern.py", "Empty file - no content"),
        ("app/tool/implementations/browser.py", "Empty file - no content"),
        # Legacy files
        (
            "archive/legacy_tools/browser_use_tool_modern.py",
            "Legacy implementation - archived",
        ),
        # Redundant base tool classes
        ("app/tool/unified_base.py", "Redundant base class - use core/base.py"),
        # Potentially redundant (need to check content)
        (
            "app/tool/enhanced_browser.py",
            "Content merged into implementations/browser_enhanced.py",
        ),
    ]

    removed_count = 0
    skipped_count = 0

    for file_path, reason in files_to_remove:
        full_path = os.path.join(Path(__file__).parent, file_path)

        if safe_remove_file(full_path, reason):
            removed_count += 1
        else:
            skipped_count += 1

    print("\n" + "=" * 70)
    print(f"📊 CLEANUP SUMMARY:")
    print(f"✅ Files removed: {removed_count}")
    print(f"⚠️ Files skipped: {skipped_count}")

    if removed_count > 0:
        print(f"\n🎉 Successfully cleaned up {removed_count} redundant files!")
        print("📁 Backups created for files with meaningful content")
        print("🔄 Next: Run tests to ensure nothing is broken")
    else:
        print("\n⚠️ No files were removed - manual review needed")

    # Check for remaining redundancy
    print(f"\n🔍 REMAINING BROWSER TOOLS:")
    browser_files = [
        "app/tool/browser_use_tool.py",
        "app/tool/implementations/browser_enhanced.py",
        "app/tool/browser/modern_tool.py",
        "app/agent/browser.py",
        "app/agent/manus_browser_handler.py",
    ]

    for file_path in browser_files:
        full_path = os.path.join(Path(__file__).parent, file_path)
        if os.path.exists(full_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (missing)")

    print(f"\n📋 NEXT STEPS:")
    print("1. Run tests to ensure nothing is broken")
    print("2. Fix any import errors from removed files")
    print("3. Consolidate remaining browser tools")
    print("4. Update tool registry imports")


if __name__ == "__main__":
    main()
