#!/usr/bin/env python3
"""
Code Fixing and Linting Script

Automatically fixes code issues using black, isort, autopep8, and flake8.
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path

# Try to find tools in virtual environment
def find_tool(tool_name):
    """Find a tool in PATH or virtual environment"""
    # Check if tool is in PATH
    tool_path = shutil.which(tool_name)
    if tool_path:
        return tool_path
    
    # Check in virtual environment
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        venv_tool = os.path.join(venv_path, 'bin', tool_name)
        if os.path.exists(venv_tool):
            return venv_tool
    
    # Check in .venv
    project_root = Path(__file__).parent
    venv_tool = project_root / '.venv' / 'bin' / tool_name
    if venv_tool.exists():
        return str(venv_tool)
    
    return tool_name  # Return as-is, let subprocess handle the error


def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0 and check:
            if result.stderr:
                print(f"Error: {result.stderr}")
            if result.stdout:
                print(result.stdout)
            return False
        if result.stdout and not result.stdout.strip().startswith("All done!"):
            print(result.stdout)
        return result.returncode == 0
    except FileNotFoundError as e:
        print(f"❌ Tool not found: {cmd[0]}")
        print(f"   Install with: uv pip install {cmd[0]}")
        return False


def fix_with_black(file_path=None, check_only=False):
    """Format code with black"""
    cmd = [sys.executable, "-m", "black"]
    if check_only:
        cmd.append("--check")
    else:
        cmd.append("--quiet")
    cmd.append("--line-length=100")
    if file_path:
        cmd.append(str(file_path))
    else:
        cmd.append(".")
    return run_command(cmd, check=False)


def fix_with_isort(file_path=None, check_only=False):
    """Sort imports with isort"""
    cmd = [sys.executable, "-m", "isort"]
    if check_only:
        cmd.append("--check-only")
    else:
        cmd.append("--quiet")
    cmd.append("--profile=black")
    cmd.append("--line-length=100")
    if file_path:
        cmd.append(str(file_path))
    else:
        cmd.append(".")
    return run_command(cmd, check=False)


def fix_with_autopep8(file_path=None, check_only=False):
    """Fix PEP 8 issues with autopep8"""
    cmd = [sys.executable, "-m", "autopep8"]
    if check_only:
        cmd.append("--diff")
    else:
        cmd.append("--in-place")
    cmd.append("--aggressive")
    cmd.append("--aggressive")
    cmd.append("--max-line-length=100")
    if file_path:
        cmd.append(str(file_path))
    else:
        cmd.append("--recursive")
        cmd.append("--in-place")
        cmd.append(".")
    return run_command(cmd, check=False)


def check_with_flake8(file_path=None):
    """Check code with flake8"""
    cmd = [sys.executable, "-m", "flake8"]
    cmd.append("--max-line-length=100")
    cmd.append("--extend-ignore=E203,W503")  # Ignore conflicts with black
    cmd.append("--exclude=venv,.venv,__pycache__,.git")
    if file_path:
        cmd.append(str(file_path))
    else:
        cmd.append(".")
    return run_command(cmd, check=False)


def check_syntax(file_path):
    """Check Python syntax by compiling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, file_path, 'exec')
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}:")
        print(f"   Line {e.lineno}: {e.msg}")
        if e.text:
            print(f"   {e.text.strip()}")
        return False
    except Exception as e:
        print(f"❌ Error checking {file_path}: {e}")
        return False


def fix_file(file_path, check_only=False):
    """Fix a single file"""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    if not file_path.suffix == '.py':
        print(f"⚠️  Skipping non-Python file: {file_path}")
        return True
    
    print(f"\n{'='*60}")
    print(f"Fixing: {file_path}")
    print(f"{'='*60}")
    
    # Check syntax first
    if not check_syntax(file_path):
        return False
    
    # Fix with various tools
    success = True
    success &= fix_with_isort(file_path, check_only=check_only)
    success &= fix_with_black(file_path, check_only=check_only)
    if not check_only:
        success &= fix_with_autopep8(file_path, check_only=check_only)
    
    # Check with flake8
    if not check_only:
        print(f"\nChecking {file_path} with flake8...")
        check_with_flake8(file_path)
    
    return success


def fix_directory(directory=".", check_only=False):
    """Fix all Python files in a directory"""
    directory = Path(directory)
    print(f"\n{'='*60}")
    print(f"Fixing all Python files in: {directory}")
    print(f"{'='*60}\n")
    
    # Find all Python files
    python_files = list(directory.rglob("*.py"))
    
    # Exclude common directories
    exclude_dirs = {'venv', '.venv', '__pycache__', '.git', 'node_modules', 'libvisio2svg'}
    python_files = [
        f for f in python_files
        if not any(excluded in f.parts for excluded in exclude_dirs)
    ]
    
    print(f"Found {len(python_files)} Python files\n")
    
    # Fix imports first
    print("1. Sorting imports with isort...")
    fix_with_isort(check_only=check_only)
    
    # Format with black
    print("\n2. Formatting with black...")
    fix_with_black(check_only=check_only)
    
    # Fix PEP 8 issues
    if not check_only:
        print("\n3. Fixing PEP 8 issues with autopep8...")
        fix_with_autopep8(check_only=check_only)
    
    # Check syntax for all files
    print("\n4. Checking syntax...")
    syntax_errors = []
    for file_path in python_files:
        if not check_syntax(file_path):
            syntax_errors.append(file_path)
    
    if syntax_errors:
        print(f"\n❌ Found syntax errors in {len(syntax_errors)} files:")
        for f in syntax_errors:
            print(f"   - {f}")
        return False
    
    # Check with flake8
    if not check_only:
        print("\n5. Checking with flake8...")
        check_with_flake8()
    
    print("\n✅ Code fixing complete!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Fix code issues using black, isort, autopep8, and flake8"
    )
    parser.add_argument(
        'file',
        nargs='?',
        help='File or directory to fix (default: current directory)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check only, do not modify files'
    )
    parser.add_argument(
        '--black-only',
        action='store_true',
        help='Only run black formatter'
    )
    parser.add_argument(
        '--isort-only',
        action='store_true',
        help='Only run isort'
    )
    parser.add_argument(
        '--flake8-only',
        action='store_true',
        help='Only run flake8'
    )
    
    args = parser.parse_args()
    
    target = args.file or "."
    target_path = Path(target)
    
    if args.black_only:
        fix_with_black(target if target_path.is_file() else None, check_only=args.check)
    elif args.isort_only:
        fix_with_isort(target if target_path.is_file() else None, check_only=args.check)
    elif args.flake8_only:
        check_with_flake8(target if target_path.is_file() else None)
    elif target_path.is_file():
        fix_file(target_path, check_only=args.check)
    else:
        fix_directory(target, check_only=args.check)


if __name__ == "__main__":
    main()
