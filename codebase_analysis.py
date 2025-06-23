#!/usr/bin/env python3
"""
Comprehensive Codebase Redundancy Analysis
Analyzes file sizes, imports, and functionality overlap
"""

import ast
import os
import sys
from pathlib import Path


def analyze_file(file_path: str) -> dict:
    """Analyze a Python file for size, imports, classes, and functions."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        info = {
            "path": file_path,
            "size": len(content),
            "lines": len(content.split("\n")),
            "imports": [],
            "classes": [],
            "functions": [],
            "has_content": len(content.strip()) > 100,
        }

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        info["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        info["imports"].append(node.module)
                elif isinstance(node, ast.ClassDef):
                    info["classes"].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    info["functions"].append(node.name)
        except:
            pass

        return info
    except Exception as e:
        return {
            "path": file_path,
            "error": str(e),
            "size": 0,
            "lines": 0,
            "has_content": False,
        }


def main():
    """Analyze codebase redundancy."""
    print("🔍 COMPREHENSIVE CODEBASE REDUNDANCY ANALYSIS")
    print("=" * 60)

    # Browser-related files to analyze
    browser_files = [
        "app/tool/browser_use_tool.py",
        "app/tool/enhanced_browser.py",
        "app/tool/implementations/browser_enhanced.py",
        "app/tool/browser/modern_tool.py",
        "app/tool/browser/actions.py",
        "app/tool/browser/router.py",
        "app/tool/browser/state.py",
        "app/agent/browser.py",
        "app/agent/manus_browser_handler.py",
        "archive/legacy_tools/browser_use_tool_modern.py",
    ]

    # Tool base files
    base_files = [
        "app/tool/base.py",
        "app/tool/core/base.py",
        "app/tool/unified_base.py",
    ]

    all_files = browser_files + base_files

    print("\n📊 BROWSER TOOLS ANALYSIS:")
    print("-" * 60)

    browser_analysis = []
    for file_path in browser_files:
        full_path = os.path.join(Path(__file__).parent, file_path)
        if os.path.exists(full_path):
            info = analyze_file(full_path)
            browser_analysis.append(info)
            status = "✅" if info["has_content"] else "❌"
            print(f"{status} {file_path}")
            print(f"   Size: {info['size']} chars, Lines: {info['lines']}")
            if info.get("classes"):
                print(f"   Classes: {', '.join(info['classes'])}")
            if info.get("error"):
                print(f"   Error: {info['error']}")
        else:
            print(f"❌ {file_path} (missing)")

    print("\n📊 BASE TOOL CLASSES ANALYSIS:")
    print("-" * 60)

    base_analysis = []
    for file_path in base_files:
        full_path = os.path.join(Path(__file__).parent, file_path)
        if os.path.exists(full_path):
            info = analyze_file(full_path)
            base_analysis.append(info)
            status = "✅" if info["has_content"] else "❌"
            print(f"{status} {file_path}")
            print(f"   Size: {info['size']} chars, Lines: {info['lines']}")
            if info.get("classes"):
                print(f"   Classes: {', '.join(info['classes'])}")
        else:
            print(f"❌ {file_path} (missing)")

    # Find overlapping classes
    print("\n🔍 CLASS OVERLAP ANALYSIS:")
    print("-" * 60)

    all_classes = {}
    for info in browser_analysis:
        for cls in info.get("classes", []):
            if cls not in all_classes:
                all_classes[cls] = []
            all_classes[cls].append(info["path"])

    for cls, files in all_classes.items():
        if len(files) > 1:
            print(f"⚠️ Class '{cls}' found in multiple files:")
            for f in files:
                print(f"   - {f}")

    # Calculate potential savings
    print("\n💾 POTENTIAL SIZE REDUCTION:")
    print("-" * 60)

    total_size = sum(info["size"] for info in browser_analysis if info["has_content"])
    empty_files = [info for info in browser_analysis if not info["has_content"]]
    large_files = [info for info in browser_analysis if info["size"] > 5000]

    print(f"Total browser tool code: {total_size:,} characters")
    print(f"Empty/minimal files: {len(empty_files)}")
    print(f"Large files (>5KB): {len(large_files)}")

    if large_files:
        print("\n📁 LARGE FILES TO REVIEW:")
        for info in sorted(large_files, key=lambda x: x["size"], reverse=True):
            print(f"   {info['path']}: {info['size']:,} chars ({info['lines']} lines)")

    # Recommendations
    print("\n🎯 CONSOLIDATION RECOMMENDATIONS:")
    print("-" * 60)

    # Group by functionality
    print("1. CONTENT EXTRACTION:")
    extraction_files = [f for f in browser_files if "extract" in f or "enhanced" in f]
    for f in extraction_files:
        full_path = os.path.join(Path(__file__).parent, f)
        if os.path.exists(full_path):
            print(f"   - {f}")

    print("\n2. BROWSER CONTROL:")
    control_files = [
        f
        for f in browser_files
        if "modern" in f or "browser" in f and "handler" not in f
    ]
    for f in control_files:
        full_path = os.path.join(Path(__file__).parent, f)
        if os.path.exists(full_path):
            print(f"   - {f}")

    print("\n3. AGENTS/HANDLERS:")
    agent_files = [f for f in browser_files if "agent" in f or "handler" in f]
    for f in agent_files:
        full_path = os.path.join(Path(__file__).parent, f)
        if os.path.exists(full_path):
            print(f"   - {f}")


if __name__ == "__main__":
    main()
