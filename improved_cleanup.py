#!/usr/bin/env python3
"""
Improved Codebase Cleanup Script - Uses Python to check imports
"""

import ast
import os
import shutil
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def find_imports_in_file(file_path: str, target_module: str) -> bool:
    """Check if a file imports the target module."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the AST to find imports
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return False

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if target_module in alias.name:
                        return True
            elif isinstance(node, ast.ImportFrom):
                if node.module and target_module in node.module:
                    return True
                # Check if importing from a package that contains the target
                if node.module:
                    module_parts = node.module.split(".")
                    if target_module in module_parts:
                        return True

        # Also check for string references
        if target_module in content:
            return True

        return False
    except Exception as e:
        return False


def check_file_usage(file_path: str) -> bool:
    """Check if a file is being imported/used elsewhere in the codebase."""
    # Get the module name from file path
    rel_path = os.path.relpath(file_path, Path(__file__).parent)
    module_name = rel_path.replace("\\", ".").replace("/", ".").replace(".py", "")
    file_name = Path(file_path).stem

    print(f"   Checking usage for module: {module_name} (file: {file_name})")

    # Search through Python files
    project_root = Path(__file__).parent
    found_usage = False

    for py_file in project_root.rglob("*.py"):
        if py_file.resolve() == Path(file_path).resolve():
            continue  # Skip self

        if find_imports_in_file(str(py_file), file_name) or find_imports_in_file(
            str(py_file), module_name
        ):
            print(f"   ⚠️ Found usage in: {py_file}")
            found_usage = True

    return found_usage


def backup_and_remove_file(file_path: str, reason: str) -> bool:
    """Backup and remove a file."""
    try:
        if not os.path.exists(file_path):
            print(f"✅ Already removed: {file_path}")
            return True

        print(f"\n🔍 Analyzing: {file_path}")
        print(f"📋 Reason: {reason}")

        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if len(content) < 50:
            print(f"📝 File is empty/minimal ({len(content)} chars)")
        else:
            print(f"📝 File has content ({len(content)} chars)")
            # Create backup
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            print(f"💾 Backed up to: {backup_path}")

        # Check if file is being used
        if check_file_usage(file_path):
            print(f"⚠️ SKIPPING: File is still being imported/used")
            return False

        # Remove the file
        os.remove(file_path)
        print(f"🗑️ REMOVED: {file_path}")
        return True

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def main():
    """Main cleanup function."""
    print("🧹 IMPROVED CODEBASE CLEANUP - Browser Tool Redundancy Removal")
    print("=" * 70)

    # Files to remove (redundant/duplicate browser tools)
    files_to_remove = [
        # Empty/minimal files first
        ("app/tool/browser_use_tool_modern.py", "Empty file - no meaningful content"),
        ("app/tool/implementations/browser.py", "Empty file - no meaningful content"),
        # Base tool redundancy
        ("app/tool/unified_base.py", "Redundant base class - use core/base.py"),
        # Legacy files
        (
            "archive/legacy_tools/browser_use_tool_modern.py",
            "Legacy implementation - archived",
        ),
        # Enhanced browser (check if content can be merged)
        (
            "app/tool/enhanced_browser.py",
            "Content should be merged into implementations/browser_enhanced.py",
        ),
    ]

    removed_count = 0
    skipped_count = 0

    for file_path, reason in files_to_remove:
        full_path = os.path.join(Path(__file__).parent, file_path)

        if backup_and_remove_file(full_path, reason):
            removed_count += 1
        else:
            skipped_count += 1

    print("\n" + "=" * 70)
    print(f"📊 CLEANUP SUMMARY:")
    print(f"✅ Files removed: {removed_count}")
    print(f"⚠️ Files skipped: {skipped_count}")

    # Show remaining browser files
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
            with open(full_path, "r") as f:
                size = len(f.read())
            print(f"  ✅ {file_path} ({size} chars)")
        else:
            print(f"  ❌ {file_path} (missing)")


if __name__ == "__main__":
    main()
