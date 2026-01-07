#!/usr/bin/env python3
"""
Create directory structure from markdown file.
Supports both tree-style and list-style markdown formats.
"""

import os
import re
import argparse
from pathlib import Path

def parse_tree_structure(content):
    """Parse tree-style markdown structure (├── └── format)"""
    directories = []
    files = []
    
    lines = content.split('\n')
    path_stack = []
    
    for line in lines:
        if not line.strip():
            continue
            
        # Remove tree characters and get the item name
        cleaned = re.sub(r'^[│├└─\s]*', '', line).strip()
        if not cleaned:
            continue
            
        # Count indentation level
        indent_match = re.match(r'^(\s*[│├└─\s]*)', line)
        indent_level = len(indent_match.group(1).replace('│', '').replace('├', '').replace('└', '').replace('─', '')) // 4 if indent_match else 0
        
        # Adjust path stack to current level
        path_stack = path_stack[:indent_level]
        
        # Build full path
        if path_stack:
            full_path = '/'.join(path_stack + [cleaned])
        else:
            full_path = cleaned
            
        # Determine if it's a file or directory.
        # Original logic misclassified dotfiles like .gitignore as directories.
        base_name = cleaned.rstrip('/')
        is_dotfile = base_name.startswith('.') and len(base_name) > 1
        # Heuristic: treat as file if (a) dotfile OR (b) contains a dot after first char and not explicitly marked as directory
        is_file = False
        if not cleaned.endswith('/'):
            if is_dotfile:
                is_file = True
            elif '.' in base_name[1:]:  # ignore leading char to avoid single leading dot case
                is_file = True
        if is_file:
            files.append(full_path)
        else:
            directories.append(full_path)
            path_stack.append(cleaned)
    
    return directories, files

def parse_list_structure(content):
    """Parse list-style markdown structure (- /path/to/dir format)"""
    directories = []
    files = []
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or not line.startswith(('-', '*', '+')):
            continue
            
        # Remove list marker and clean path
        path = re.sub(r'^[-*+]\s*', '', line).strip()
        if not path:
            continue
            
        # Remove leading slashes
        path = path.lstrip('/')
        
        # Determine if it's a file or directory
        if '.' in os.path.basename(path) and not path.endswith('/'):
            files.append(path)
            # Also add parent directories
            parent = os.path.dirname(path)
            if parent and parent not in directories:
                directories.append(parent)
        else:
            # Remove trailing slash if present
            path = path.rstrip('/')
            if path and path not in directories:
                directories.append(path)
    
    return directories, files

def create_structure(base_path, directories, files, dry_run=False):
    """Create the directory structure and files"""
    base_path = Path(base_path)
    
    if dry_run:
        print(f"DRY RUN - Would create structure in: {base_path}")
        print("\nDirectories:")
        for directory in sorted(directories):
            print(f"  📁 {directory}")
        print("\nFiles:")
        for file in sorted(files):
            print(f"  📄 {file}")
        return
    
    # Create base directory if it doesn't exist
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Create directories
    for directory in directories:
        dir_path = base_path / directory
        try:
            if dir_path.exists() and dir_path.is_file():
                print(f"Skipping directory '{dir_path}' because a file with that name already exists")
                continue
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except FileExistsError:
            # Rare race condition case or path occupied by file
            print(f"Warning: Could not create directory (already exists as file?): {dir_path}")
    
    # Create files
    for file in files:
        file_path = base_path / file
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Create empty file if it doesn't exist
        if not file_path.exists():
            file_path.touch()
            print(f"Created file: {file_path}")

def main():
    parser = argparse.ArgumentParser(description='Create directory structure from markdown file')
    parser.add_argument('markdown_file', help='Path to markdown file containing structure')
    parser.add_argument('-o', '--output', default='.', help='Output directory (default: current directory)')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Show what would be created without creating')
    parser.add_argument('-f', '--format', choices=['auto', 'tree', 'list'], default='auto', 
                       help='Markdown format: tree (├──), list (-), or auto-detect')
    
    args = parser.parse_args()
    
    # Read markdown file
    try:
        with open(args.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.markdown_file}' not found")
        return 1
    except Exception as e:
        print(f"Error reading file: {e}")
        return 1
    
    # Parse structure based on format
    if args.format == 'auto':
        # Auto-detect format
        if '├──' in content or '└──' in content:
            directories, files = parse_tree_structure(content)
        else:
            directories, files = parse_list_structure(content)
    elif args.format == 'tree':
        directories, files = parse_tree_structure(content)
    else:  # list
        directories, files = parse_list_structure(content)
    
    if not directories and not files:
        print("No directory structure found in markdown file")
        return 1
    
    # Create structure
    create_structure(args.output, directories, files, args.dry_run)
    
    if not args.dry_run:
        print(f"\nDirectory structure created successfully in: {os.path.abspath(args.output)}")

if __name__ == '__main__':
    exit(main())