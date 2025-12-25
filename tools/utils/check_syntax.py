#!/usr/bin/env python3
"""
Syntax Checker for Python Files

This script checks Python files for syntax errors using multiple methods:
1. py_compile - Python's built-in compiler
2. ast.parse - Abstract syntax tree parser
3. importlib - Attempts to import the module

This is more comprehensive than black/flake8 which only check formatting/style.
"""

import sys
import ast
import py_compile
import importlib.util
from pathlib import Path
from typing import List, Tuple


def check_syntax_py_compile(file_path: Path) -> Tuple[bool, str]:
    """Check syntax using py_compile"""
    try:
        py_compile.compile(str(file_path), doraise=True)
        return True, ""
    except py_compile.PyCompileError as e:
        return False, f"py_compile error: {e.msg} at line {e.lineno}"


def check_syntax_ast(file_path: Path) -> Tuple[bool, str]:
    """Check syntax using ast.parse"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content, filename=str(file_path))
        return True, ""
    except SyntaxError as e:
        lines = content.split("\n")
        error_context = []
        start = max(0, e.lineno - 3)
        end = min(len(lines), e.lineno + 2)
        for i in range(start, end):
            marker = ">>> " if i == e.lineno - 1 else "    "
            error_context.append(f"{marker}{i+1:4d}: {lines[i]}")
        return False, f"ast.parse error: {e.msg} at line {e.lineno}\n" + "\n".join(
            error_context
        )


def check_syntax_import(file_path: Path) -> Tuple[bool, str]:
    """Check syntax by attempting to import (only for modules, not scripts)"""
    # Skip import check for scripts (files with if __name__ == "__main__")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "__name__" in content and "__main__" in content:
            return True, "Skipped (script file)"
    except Exception:
        pass

    try:
        spec = importlib.util.spec_from_file_location("module", str(file_path))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        return True, ""
    except SyntaxError as e:
        return False, f"import error: {e.msg} at line {e.lineno}"
    except Exception as e:
        # Other import errors (missing dependencies) are OK for syntax checking
        return True, f"Import skipped (dependency issue: {type(e).__name__})"


def check_file(file_path: Path, verbose: bool = False) -> bool:
    """Check a single file for syntax errors"""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    if not file_path.suffix == ".py":
        if verbose:
            print(f"⏭️  Skipping non-Python file: {file_path}")
        return True

    errors = []

    # Check 1: py_compile
    success, error = check_syntax_py_compile(file_path)
    if not success:
        errors.append(("py_compile", error))

    # Check 2: ast.parse
    success, error = check_syntax_ast(file_path)
    if not success:
        errors.append(("ast.parse", error))

    # Check 3: import (optional, may fail due to dependencies)
    success, error = check_syntax_import(file_path)
    if not success and "dependency issue" not in error.lower():
        errors.append(("import", error))

    if errors:
        print(f"❌ {file_path}")
        for method, error_msg in errors:
            print(f"   [{method}] {error_msg}")
        return False
    else:
        if verbose:
            print(f"✅ {file_path}")
        return True


def check_directory(directory: Path, verbose: bool = False) -> Tuple[int, int]:
    """Check all Python files in a directory"""
    directory = Path(directory)
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return 0, 0

    python_files = list(directory.rglob("*.py"))
    total = len(python_files)
    passed = 0

    for file_path in python_files:
        if check_file(file_path, verbose=verbose):
            passed += 1

    return passed, total


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check Python files for syntax errors"
    )
    parser.add_argument(
        "paths", nargs="+", help="Files or directories to check", type=Path
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=["__pycache__", ".venv", "venv", ".git"],
        help="Directories to exclude",
    )

    args = parser.parse_args()

    total_passed = 0
    total_files = 0

    for path in args.paths:
        path = Path(path)
        if path.is_file():
            if check_file(path, verbose=args.verbose):
                total_passed += 1
            total_files += 1
        elif path.is_dir():
            # Filter out excluded directories
            python_files = [
                f
                for f in path.rglob("*.py")
                if not any(exclude in f.parts for exclude in args.exclude)
            ]
            for file_path in python_files:
                if check_file(file_path, verbose=args.verbose):
                    total_passed += 1
                total_files += 1

    print(f"\n{'='*60}")
    print(f"Results: {total_passed}/{total_files} files passed")
    if total_passed < total_files:
        print(f"❌ {total_files - total_passed} files have syntax errors")
        sys.exit(1)
    else:
        print("✅ All files passed syntax check")
        sys.exit(0)


if __name__ == "__main__":
    main()
