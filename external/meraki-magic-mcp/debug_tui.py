#!/usr/bin/env python3
"""
Debug script for Meraki Magic TUI
Tests TUI components and dependencies
"""

import sys
import os
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_imports():
    print_section("Checking TUI Imports")
    issues = []
    
    try:
        import meraki
        print(f"✓ meraki: {meraki.__version__}")
    except ImportError as e:
        print(f"✗ meraki: {e}")
        issues.append("meraki not installed")
    
    try:
        from textual.app import App
        print("✓ textual.app: App imported successfully")
    except ImportError as e:
        print(f"✗ textual.app: {e}")
        issues.append("textual not installed")
    
    try:
        from textual.widgets import DataTable, Button, Input
        print("✓ textual.widgets: Widgets imported successfully")
    except ImportError as e:
        print(f"✗ textual.widgets: {e}")
        issues.append("textual widgets issue")
    
    try:
        from textual.containers import Container, Horizontal, Vertical
        print("✓ textual.containers: Containers imported successfully")
    except ImportError as e:
        print(f"✗ textual.containers: {e}")
        issues.append("textual containers issue")
    
    try:
        from rich.text import Text
        from rich.markdown import Markdown
        print("✓ rich: Text and Markdown imported successfully")
    except ImportError as e:
        print(f"✗ rich: {e}")
        issues.append("rich not installed")
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv: loaded successfully")
    except ImportError as e:
        print(f"✗ python-dotenv: {e}")
        issues.append("python-dotenv not installed")
    
    return issues

def check_environment():
    print_section("Checking Environment for TUI")
    issues = []
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("MERAKI_API_KEY")
    org_id = os.getenv("MERAKI_ORG_ID")
    
    if api_key:
        print(f"✓ MERAKI_API_KEY: {'*' * 20}...{api_key[-10:]}")
    else:
        print("✗ MERAKI_API_KEY: NOT SET")
        issues.append("MERAKI_API_KEY not set")
    
    if org_id:
        print(f"✓ MERAKI_ORG_ID: {org_id}")
    else:
        print("⚠ MERAKI_ORG_ID: NOT SET (optional, will use first org)")
    
    return issues

def check_tui_file():
    print_section("Checking TUI Application File")
    issues = []
    
    tui_file = Path("meraki_tui.py")
    if tui_file.exists():
        size = tui_file.stat().st_size
        print(f"✓ meraki_tui.py: {size:,} bytes")
        
        # Check for main function
        content = tui_file.read_text()
        if "def main()" in content:
            print("✓ main() function found")
        else:
            print("✗ main() function not found")
            issues.append("main() function missing")
        
        if "class MerakiDashboard" in content:
            print("✓ MerakiDashboard class found")
        else:
            print("✗ MerakiDashboard class not found")
            issues.append("MerakiDashboard class missing")
        
        if "app.run()" in content:
            print("✓ app.run() call found")
        else:
            print("✗ app.run() call not found")
            issues.append("app.run() call missing")
    else:
        print("✗ meraki_tui.py: NOT FOUND")
        issues.append("meraki_tui.py missing")
    
    return issues

def check_textual_version():
    print_section("Checking Textual Version")
    issues = []
    
    try:
        import textual
        version = textual.__version__
        print(f"✓ Textual version: {version}")
        
        # Check if version is compatible (>= 1.0.0)
        major, minor = map(int, version.split('.')[:2])
        if major >= 1:
            print("✓ Textual version is compatible (>= 1.0.0)")
        else:
            print(f"⚠ Textual version may be too old: {version}")
            issues.append(f"Textual version {version} may be incompatible")
    except Exception as e:
        print(f"✗ Could not check Textual version: {e}")
        issues.append("Textual version check failed")
    
    return issues

def check_meraki_connection():
    print_section("Testing Meraki API Connection for TUI")
    issues = []
    
    try:
        from dotenv import load_dotenv
        import meraki
        load_dotenv()
        
        api_key = os.getenv("MERAKI_API_KEY")
        if not api_key:
            print("✗ Cannot test: API key not set")
            return ["API key not set"]
        
        dashboard = meraki.DashboardAPI(
            api_key=api_key,
            suppress_logging=True
        )
        
        # Try to get organizations (same as TUI does)
        try:
            orgs = dashboard.organizations.getOrganizations()
            print(f"✓ API Connection: SUCCESS")
            print(f"  Organizations found: {len(orgs)}")
            for org in orgs[:3]:
                print(f"    - {org.get('name', 'Unknown')} (ID: {org.get('id', 'N/A')})")
            
            # Test getting networks (TUI does this)
            if orgs:
                try:
                    networks = dashboard.organizations.getOrganizationNetworks(orgs[0]['id'])
                    print(f"✓ Network fetch: SUCCESS ({len(networks)} networks)")
                except Exception as e:
                    print(f"⚠ Network fetch: {e}")
                    issues.append(f"Network fetch error: {e}")
        except Exception as e:
            print(f"✗ API Connection: FAILED - {e}")
            issues.append(f"Meraki API error: {e}")
            
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        issues.append(f"Connection test error: {e}")
    
    return issues

def check_terminal_compatibility():
    print_section("Checking Terminal Compatibility")
    issues = []
    
    # Check if running in a terminal
    if sys.stdout.isatty():
        print("✓ Running in interactive terminal")
    else:
        print("⚠ Not running in interactive terminal (TUI may not work)")
        issues.append("Not in interactive terminal")
    
    # Check terminal size
    try:
        import shutil
        cols, rows = shutil.get_terminal_size()
        print(f"✓ Terminal size: {cols}x{rows}")
        
        if cols < 80 or rows < 24:
            print(f"⚠ Terminal may be too small (recommended: 80x24 minimum)")
            issues.append("Terminal size may be insufficient")
    except Exception as e:
        print(f"⚠ Could not determine terminal size: {e}")
    
    return issues

def main():
    print("\n" + "="*60)
    print("  Meraki Magic TUI - Debug Report")
    print("="*60)
    
    all_issues = []
    
    all_issues.extend(check_imports())
    all_issues.extend(check_environment())
    all_issues.extend(check_tui_file())
    all_issues.extend(check_textual_version())
    all_issues.extend(check_meraki_connection())
    all_issues.extend(check_terminal_compatibility())
    
    print_section("Summary")
    
    if all_issues:
        print(f"✗ Found {len(all_issues)} issue(s):")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        print("\n⚠️  Some issues were detected. Please review above.")
        return 1
    else:
        print("✓ All checks passed! TUI should work correctly.")
        print("\nTo launch the TUI:")
        print("  python3 meraki_tui.py")
        return 0

if __name__ == "__main__":
    sys.exit(main())
