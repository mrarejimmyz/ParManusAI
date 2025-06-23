#!/usr/bin/env python3
"""
Dependency Tree Tracker - Start from main.py and trace all dependencies
This will help us identify what's actually needed vs what can be removed
"""

import ast
import json
import os
import sys
from collections import defaultdict, deque
from pathlib import Path


class DependencyTracker:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependencies = defaultdict(set)
        self.file_info = {}
        self.visited = set()
        self.queue = deque()

    def parse_file_imports(self, file_path: Path) -> tuple[list, dict]:
        """Parse a Python file and extract imports and basic info."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            info = {
                "path": str(file_path),
                "size": len(content),
                "lines": len(content.split("\n")),
                "exists": True,
                "error": None,
            }

            imports = []

            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(
                                {"type": "import", "module": alias.name, "from": None}
                            )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(
                                {
                                    "type": "from_import",
                                    "module": node.module,
                                    "from": [alias.name for alias in node.names],
                                }
                            )
            except SyntaxError as e:
                info["error"] = f"Syntax error: {str(e)}"

            return imports, info

        except Exception as e:
            info = {"path": str(file_path), "exists": False, "error": str(e)}
            return [], info

    def resolve_import_to_file(
        self, import_info: dict, current_file: Path
    ) -> list[Path]:
        """Resolve an import to actual file paths."""
        module = import_info["module"]
        resolved_files = []

        # Handle relative imports
        if module.startswith("."):
            # Relative import - resolve relative to current file's directory
            current_dir = current_file.parent
            parts = module.split(".")

            # Count leading dots for relative level
            level = 0
            for part in parts:
                if part == "":
                    level += 1
                else:
                    break

            # Go up 'level' directories
            target_dir = current_dir
            for _ in range(level):
                target_dir = target_dir.parent

            # Add remaining path parts
            remaining_parts = [p for p in parts if p != ""]
            for part in remaining_parts:
                target_dir = target_dir / part

            # Try as file or package
            py_file = target_dir.with_suffix(".py")
            init_file = target_dir / "__init__.py"

            if py_file.exists() and py_file.is_relative_to(self.project_root):
                resolved_files.append(py_file)
            if init_file.exists() and init_file.is_relative_to(self.project_root):
                resolved_files.append(init_file)

        else:
            # Absolute import - check if it's a project module
            parts = module.split(".")
            # Try to find in project
            module_path = Path("/".join(parts))
            potential_paths = [
                self.project_root / f"{module_path}.py",
                self.project_root / module_path / "__init__.py",
            ]

            for path in potential_paths:
                if path.exists() and path.is_relative_to(self.project_root):
                    resolved_files.append(path)
                    break

        return resolved_files

    def trace_dependencies(self, start_file: str):
        """Trace all dependencies starting from a file."""
        start_path = self.project_root / start_file

        if not start_path.exists():
            print(f"❌ Start file not found: {start_file}")
            return

        self.queue.append(start_path)

        while self.queue:
            current_file = self.queue.popleft()

            if current_file in self.visited:
                continue

            self.visited.add(current_file)

            print(f"📂 Analyzing: {current_file.relative_to(self.project_root)}")

            imports, info = self.parse_file_imports(current_file)
            self.file_info[str(current_file)] = info

            if info["error"]:
                print(f"   ⚠️ Error: {info['error']}")
                continue

            # Process each import
            for import_info in imports:
                resolved_files = self.resolve_import_to_file(import_info, current_file)

                for resolved_file in resolved_files:
                    if resolved_file not in self.visited:
                        self.queue.append(resolved_file)

                    # Track the dependency
                    self.dependencies[str(current_file)].add(str(resolved_file))

                    print(
                        f"   📦 {import_info['module']} → {resolved_file.relative_to(self.project_root)}"
                    )

    def generate_report(self):
        """Generate a comprehensive dependency report."""
        print("\n" + "=" * 80)
        print("📊 DEPENDENCY ANALYSIS REPORT")
        print("=" * 80)

        # Find all files that are actually used
        all_used_files = set()
        for deps in self.dependencies.values():
            all_used_files.update(deps)
        all_used_files.update(self.dependencies.keys())

        print(f"\n✅ USED FILES ({len(all_used_files)}):")
        print("-" * 40)

        used_by_category = defaultdict(list)
        total_size = 0

        for file_path in sorted(all_used_files):
            rel_path = Path(file_path).relative_to(self.project_root)
            info = self.file_info.get(file_path, {})
            size = info.get("size", 0)
            total_size += size

            # Categorize
            if "tool" in str(rel_path):
                used_by_category["tools"].append((rel_path, size))
            elif "agent" in str(rel_path):
                used_by_category["agents"].append((rel_path, size))
            elif "browser" in str(rel_path):
                used_by_category["browser"].append((rel_path, size))
            else:
                used_by_category["core"].append((rel_path, size))

        for category, files in used_by_category.items():
            print(f"\n📁 {category.upper()}:")
            for file_path, size in sorted(files):
                print(f"   ✅ {file_path} ({size:,} chars)")

        print(f"\n💾 Total used code: {total_size:,} characters")

        # Find unused files
        print(f"\n🔍 SCANNING FOR UNUSED FILES:")
        print("-" * 40)

        unused_files = []
        browser_patterns = ["browser", "tool"]

        for pattern in browser_patterns:
            for py_file in self.project_root.rglob(f"**/*{pattern}*.py"):
                if py_file.is_file() and str(py_file) not in all_used_files:
                    try:
                        size = py_file.stat().st_size
                        if size > 100:  # Only report non-trivial files
                            unused_files.append((py_file, size))
                    except:
                        pass

        if unused_files:
            print(f"\n❌ UNUSED FILES ({len(unused_files)}):")
            unused_size = sum(size for _, size in unused_files)
            for file_path, size in sorted(
                unused_files, key=lambda x: x[1], reverse=True
            ):
                rel_path = file_path.relative_to(self.project_root)
                print(f"   🗑️ {rel_path} ({size:,} chars)")

            print(f"\n💾 Total unused code: {unused_size:,} characters")
            print(
                f"🎯 Potential savings: {unused_size:,} characters ({len(unused_files)} files)"
            )

        # Generate removal script
        self.generate_cleanup_script(unused_files)

    def generate_cleanup_script(self, unused_files):
        """Generate a safe cleanup script."""
        script_content = '''#!/usr/bin/env python3
"""
Auto-generated cleanup script based on dependency analysis
ONLY removes files that are NOT imported from main.py
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
    print("🧹 DEPENDENCY-BASED CLEANUP")
    print("Removing files NOT used by main.py")
    print("=" * 50)

    files_to_remove = [
'''

        for file_path, size in unused_files:
            rel_path = file_path.relative_to(self.project_root)
            script_content += f'        "{rel_path}",  # {size:,} chars\n'

        script_content += """    ]

    removed_count = 0
    for file_path in files_to_remove:
        full_path = os.path.join(Path(__file__).parent, file_path)
        safe_remove_file(full_path)
        removed_count += 1

    print(f"\\n✅ Cleanup complete: {removed_count} files removed")

if __name__ == "__main__":
    main()
"""

        with open(self.project_root / "dependency_cleanup.py", "w") as f:
            f.write(script_content)

        print(f"\n📝 Generated cleanup script: dependency_cleanup.py")


def main():
    """Main function to run dependency analysis."""
    project_root = Path(__file__).parent
    tracker = DependencyTracker(str(project_root))

    print("🔍 DEPENDENCY TRACKER - Starting from main.py")
    print("=" * 60)

    # Start tracing from main.py
    tracker.trace_dependencies("main.py")

    # Generate comprehensive report
    tracker.generate_report()


if __name__ == "__main__":
    main()
