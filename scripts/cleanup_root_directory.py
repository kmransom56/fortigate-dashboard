#!/usr/bin/env python3
"""
Root Directory Cleanup Script

Safely organizes files in the root directory by moving them to appropriate locations.
Preserves all functionality and updates path references where needed.
"""

import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Tuple

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Files that MUST stay in root
KEEP_IN_ROOT = {
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "requirements.txt",
    "pyproject.toml",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "docker-compose.prod.yml",
    "docker-compose.enterprise.yml",
    ".gitignore",
    "redis.conf",
    "svgo.config.js",
    "svgo.config.json",
    ".env",
    "uv.lock",
}

# Directory structure to create
DIRECTORIES = {
    "docs/archive/analysis": [],
    "docs/archive/reports": [],
    "docs/archive/features": [],
    "docs/archive/quickref": [],
    "docs/api": [],
    "docs/agents": [],
    "tools/icons": [],
    "tools/tests": [],
    "tools/troubleshoot": [],
    "tools/utils": [],
    "tools/agents": [],
    "scripts/icons": [],
}

# File movement mapping: (source, destination_directory, update_paths)
FILE_MOVEMENTS = {
    # Documentation - Analysis
    "AI_AGENT_IMPLEMENTATION_COMPLETE.md": ("docs/archive/analysis", False),
    "AI_AGENT_INTEGRATION_ANALYSIS.md": ("docs/archive/analysis", False),
    "ALL_ENDPOINTS_IMPLEMENTED.md": ("docs/archive/analysis", False),
    "API_CODE_ANALYSIS.md": ("docs/archive/analysis", False),
    "API_IMPLEMENTATION_SUMMARY.md": ("docs/archive/analysis", False),
    "COMPLETE_API_COVERAGE_ANALYSIS.md": ("docs/archive/analysis", False),
    "SYSTEM_API_COVERAGE.md": ("docs/archive/analysis", False),
    "PERFORMANCE_OPTIMIZATION_SUMMARY.md": ("docs/archive/analysis", False),
    "ICON_ORGANIZATION_SUMMARY.md": ("docs/archive/analysis", False),
    "ICON_PROJECT_SUMMARY.md": ("docs/archive/analysis", False),
    
    # Documentation - Reports
    "api_token_troubleshoot.md": ("docs/archive/reports", False),
    "fortiswitch_troubleshooting_report.md": ("docs/archive/reports", False),
    "performance_analysis_report.md": ("docs/archive/reports", False),
    "icon_catalog_report.md": ("docs/archive/reports", False),
    "deployment_summary.md": ("docs/archive/reports", False),
    "device_inventory.md": ("docs/archive/reports", False),
    "optimization_implementation_guide.md": ("docs/archive/reports", False),
    
    # Documentation - Features
    "3D_TOPOLOGY_ENHANCEMENTS.md": ("docs/archive/features", False),
    "ENTERPRISE_ARCHITECTURE.md": ("docs/archive/features", False),
    "QSR_RESTAURANT_TECHNOLOGY_RESEARCH.md": ("docs/archive/features", False),
    "REDIS_SESSION_MIGRATION_GUIDE.md": ("docs/archive/features", False),
    "DOCKER_DEPLOYMENT_GUIDE.md": ("docs/archive/features", False),
    "SCANOPY_INTEGRATION.md": ("docs/archive/features", False),
    
    # Documentation - Quick Reference
    "QUICK_FIX.md": ("docs/archive/quickref", False),
    "QUICKSTART_AUTOGEN.md": ("docs/archive/quickref", False),
    "CODE_FIXING_GUIDE.md": ("docs/archive/quickref", False),
    "README_AUTOGEN_AGENT.md": ("docs/archive/quickref", False),
    
    # Documentation - API
    "API_ENDPOINTS_REFERENCE.md": ("docs/api", False),
    
    # Documentation - Agents
    "GEMINI.md": ("docs/agents", False),
    "CLAUDE.local.md": ("docs/agents", False),
    
    # Python Scripts - Icons
    "catalog_icons.py": ("tools/icons", True),
    "get_icons.py": ("tools/icons", True),
    "populate_fortinet_icons.py": ("tools/icons", True),
    "scrape_icons.py": ("tools/icons", True),
    "simple_Icons.py": ("tools/icons", True),
    "simple_svg_optimize.py": ("tools/icons", True),
    "optimize_svg_files.py": ("tools/icons", True),
    "optimize_large_svgs.py": ("tools/icons", True),
    "analyze_svg_optimization.py": ("tools/icons", True),
    "extract_visio_stencils.py": ("tools/icons", True),
    
    # Python Scripts - Tests
    "test_complete_topology.py": ("tools/tests", True),
    "test_enhanced_fortiswitch.py": ("tools/tests", True),
    "test_fortiswitch_improved.py": ("tools/tests", True),
    "test_fortiswitch.py": ("tools/tests", True),
    "test_icon_integration.py": ("tools/tests", True),
    "test_topology_endpoints.py": ("tools/tests", True),
    "test_topology_icons.py": ("tools/tests", True),
    "simple_test.py": ("tools/tests", True),
    "performance_test.py": ("tools/tests", True),
    
    # Python Scripts - Troubleshoot
    "topology_troubleshoot.py": ("tools/troubleshoot", True),
    "topology_fix.py": ("tools/troubleshoot", True),
    "fix_fortiswitch_auth.py": ("tools/troubleshoot", True),
    "get_new_api_token.py": ("tools/troubleshoot", True),
    "fortigate_self_api_doc.py": ("tools/troubleshoot", True),
    
    # Python Scripts - Utils
    "fix_code.py": ("tools/utils", True),
    "scrape_topology.py": ("tools/utils", True),
    
    # Python Scripts - Agents
    "autogen_agent.py": ("tools/agents", True),
    "example_agent_usage.py": ("tools/agents", True),
    
    # Shell Scripts
    "deploy.sh": ("scripts", False),
    "download_icons.sh": ("scripts/icons", False),
    
    # Temporary files to remove
    "cookies.txt": (None, False),  # Remove
    "compose.yml.txt": (None, False),  # Remove
    "Untitled-1": (None, False),  # Remove
    "AGENTS.bak": (None, False),  # Remove
}


def create_directories():
    """Create all necessary directories"""
    print("📁 Creating directory structure...")
    for directory in DIRECTORIES.keys():
        dir_path = PROJECT_ROOT / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {directory}")
    print()


def update_python_paths(file_path: Path, old_root: Path, new_root: Path):
    """Update Python path references in a file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Update relative imports that reference app/
        if "app/" in content:
            # Calculate relative path from new location to app/
            rel_path = os.path.relpath(
                PROJECT_ROOT / "app",
                file_path.parent
            ).replace("\\", "/")
            
            # Update common patterns
            patterns = [
                (r'("app/)', f'"{rel_path}/'),
                (r"('app/)", f"'{rel_path}/"),
                (r'(sys\.path\.append\(["\'])(\.\./)*app', 
                 f'\\1{rel_path}'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
        
        # Update sys.path.insert patterns
        if "sys.path" in content:
            # Calculate path to project root
            rel_to_root = os.path.relpath(
                PROJECT_ROOT,
                file_path.parent
            ).replace("\\", "/")
            
            # Update sys.path.insert(0, ...) patterns
            content = re.sub(
                r'sys\.path\.insert\(0,\s*os\.path\.join\(os\.path\.dirname\(__file__\),\s*"\.\."\)\)',
                f'sys.path.insert(0, os.path.join(os.path.dirname(__file__), "{rel_to_root}"))',
                content
            )
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
    except Exception as e:
        print(f"   ⚠️  Warning: Could not update paths in {file_path.name}: {e}")
        return False
    
    return False


def move_file(source: Path, dest_dir: Path, update_paths: bool):
    """Move a file to destination directory"""
    if not source.exists():
        return False, "File not found"
    
    dest_path = dest_dir / source.name
    
    # Check if destination already exists
    if dest_path.exists():
        return False, "Destination already exists"
    
    try:
        # Create destination directory if needed
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(source), str(dest_path))
        
        # Update paths if needed
        if update_paths and source.suffix == '.py':
            update_python_paths(dest_path, PROJECT_ROOT, dest_dir)
        
        return True, "Moved successfully"
    except Exception as e:
        return False, f"Error: {e}"


def remove_file(file_path: Path):
    """Remove a file"""
    if not file_path.exists():
        return False, "File not found"
    
    try:
        file_path.unlink()
        return True, "Removed successfully"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Main cleanup function"""
    print("🧹 Root Directory Cleanup Script")
    print("=" * 50)
    print()
    
    # Create directories
    create_directories()
    
    # Track results
    moved = []
    removed = []
    skipped = []
    errors = []
    
    # Process files
    print("📦 Moving files...")
    for filename, (dest_dir, update_paths) in FILE_MOVEMENTS.items():
        source = PROJECT_ROOT / filename
        
        if not source.exists():
            skipped.append((filename, "File not found"))
            continue
        
        # Check if file should be kept in root
        if filename in KEEP_IN_ROOT:
            skipped.append((filename, "Must stay in root"))
            continue
        
        # Remove file if dest_dir is None
        if dest_dir is None:
            success, message = remove_file(source)
            if success:
                removed.append((filename, message))
            else:
                errors.append((filename, message))
            continue
        
        # Move file
        dest_path = PROJECT_ROOT / dest_dir
        success, message = move_file(source, dest_path, update_paths)
        
        if success:
            moved.append((filename, dest_dir))
        else:
            errors.append((filename, message))
    
    # Print summary
    print()
    print("=" * 50)
    print("📊 Cleanup Summary")
    print("=" * 50)
    print()
    
    if moved:
        print(f"✅ Moved {len(moved)} files:")
        for filename, dest in moved:
            print(f"   • {filename} → {dest}/")
        print()
    
    if removed:
        print(f"🗑️  Removed {len(removed)} files:")
        for filename, _ in removed:
            print(f"   • {filename}")
        print()
    
    if skipped:
        print(f"⏭️  Skipped {len(skipped)} files:")
        for filename, reason in skipped[:10]:  # Show first 10
            print(f"   • {filename} ({reason})")
        if len(skipped) > 10:
            print(f"   ... and {len(skipped) - 10} more")
        print()
    
    if errors:
        print(f"❌ Errors ({len(errors)} files):")
        for filename, error in errors:
            print(f"   • {filename}: {error}")
        print()
    
    print("=" * 50)
    print("✨ Cleanup complete!")
    print()
    print("📝 Next steps:")
    print("   1. Review moved files")
    print("   2. Test application startup")
    print("   3. Verify Docker builds")
    print("   4. Update any documentation references")
    print()


if __name__ == "__main__":
    main()
