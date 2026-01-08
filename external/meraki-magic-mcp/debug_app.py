#!/usr/bin/env python3
"""
Debug script for Meraki Magic MCP
Tests all components and identifies issues
"""

import sys
import os
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_imports():
    print_section("Checking Imports")
    issues = []
    
    try:
        import meraki
        print(f"✓ meraki: {meraki.__version__}")
    except ImportError as e:
        print(f"✗ meraki: {e}")
        issues.append("meraki not installed")
    
    try:
        from mcp.server.fastmcp import FastMCP
        print("✓ mcp.server.fastmcp: FastMCP imported successfully")
    except ImportError as e:
        print(f"✗ mcp.server.fastmcp: {e}")
        issues.append("mcp package issue")
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv: loaded successfully")
    except ImportError as e:
        print(f"✗ python-dotenv: {e}")
        issues.append("python-dotenv not installed")
    
    try:
        from pydantic import Field
        print("✓ pydantic: loaded successfully")
    except ImportError as e:
        print(f"✗ pydantic: {e}")
        issues.append("pydantic not installed")
    
    return issues

def check_environment():
    print_section("Checking Environment Variables")
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
        print("✗ MERAKI_ORG_ID: NOT SET")
        issues.append("MERAKI_ORG_ID not set")
    
    # Check optional settings
    caching = os.getenv("ENABLE_CACHING", "true")
    print(f"  ENABLE_CACHING: {caching}")
    
    read_only = os.getenv("READ_ONLY_MODE", "false")
    print(f"  READ_ONLY_MODE: {read_only}")
    
    return issues

def check_files():
    print_section("Checking Application Files")
    issues = []
    
    files_to_check = [
        "meraki-mcp-dynamic.py",
        "meraki-mcp.py",
        ".env",
        "requirements.txt",
        "mcpserver.json"
    ]
    
    for file in files_to_check:
        path = Path(file)
        if path.exists():
            size = path.stat().st_size
            print(f"✓ {file}: {size:,} bytes")
        else:
            print(f"✗ {file}: NOT FOUND")
            issues.append(f"{file} missing")
    
    return issues

def check_meraki_connection():
    print_section("Testing Meraki API Connection")
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
        
        # Try to get organizations
        try:
            orgs = dashboard.organizations.getOrganizations()
            print(f"✓ API Connection: SUCCESS")
            print(f"  Organizations found: {len(orgs)}")
            for org in orgs[:3]:  # Show first 3
                print(f"    - {org.get('name', 'Unknown')} (ID: {org.get('id', 'N/A')})")
        except Exception as e:
            print(f"✗ API Connection: FAILED - {e}")
            issues.append(f"Meraki API error: {e}")
            
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        issues.append(f"Connection test error: {e}")
    
    return issues

def check_mcp_server():
    print_section("Testing MCP Server Initialization")
    issues = []
    
    try:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("Test MCP Server")
        print("✓ MCP Server: Created successfully")
        
        # Try to add a test tool
        @mcp.tool()
        def test_tool() -> str:
            """Test tool"""
            return "OK"
        
        print("✓ MCP Tool: Registered successfully")
        
    except Exception as e:
        print(f"✗ MCP Server: {e}")
        issues.append(f"MCP server error: {e}")
    
    return issues

def check_syntax():
    print_section("Checking Python Syntax")
    issues = []
    
    import py_compile
    
    files_to_check = ["meraki-mcp-dynamic.py", "meraki-mcp.py"]
    
    for file in files_to_check:
        if Path(file).exists():
            try:
                py_compile.compile(file, doraise=True)
                print(f"✓ {file}: Syntax OK")
            except py_compile.PyCompileError as e:
                print(f"✗ {file}: Syntax Error - {e}")
                issues.append(f"{file} syntax error")
        else:
            print(f"✗ {file}: File not found")
            issues.append(f"{file} missing")
    
    return issues

def check_fastmcp_cli():
    print_section("Checking fastmcp CLI")
    issues = []
    
    import shutil
    
    # Check if fastmcp is in PATH
    fastmcp_path = shutil.which("fastmcp")
    if fastmcp_path:
        print(f"✓ fastmcp CLI: Found at {fastmcp_path}")
    else:
        print("✗ fastmcp CLI: Not found in PATH")
        issues.append("fastmcp CLI not available")
    
    # Check if it's in venv
    venv_fastmcp = Path(".venv/bin/fastmcp")
    if venv_fastmcp.exists():
        print(f"✓ fastmcp in venv: Found at {venv_fastmcp}")
    else:
        print("✗ fastmcp in venv: Not found")
        if not issues:
            print("  (This is OK if using system Python)")
    
    return issues

def main():
    print("\n" + "="*60)
    print("  Meraki Magic MCP - Debug Report")
    print("="*60)
    
    all_issues = []
    
    all_issues.extend(check_imports())
    all_issues.extend(check_environment())
    all_issues.extend(check_files())
    all_issues.extend(check_syntax())
    all_issues.extend(check_mcp_server())
    all_issues.extend(check_fastmcp_cli())
    all_issues.extend(check_meraki_connection())
    
    print_section("Summary")
    
    if all_issues:
        print(f"✗ Found {len(all_issues)} issue(s):")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        print("\n⚠️  Some issues were detected. Please review above.")
        return 1
    else:
        print("✓ All checks passed! Application appears to be working correctly.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
