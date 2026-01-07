#!/usr/bin/env python3
"""
Direct test of MCP server startup to identify the exact error
"""
import sys
import traceback
import os
from pathlib import Path

def test_python_basics():
    """Test if Python and basic imports work"""
    print("=== PYTHON BASICS TEST ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    
    try:
        import asyncio
        print("✓ asyncio import: OK")
    except Exception as e:
        print(f"❌ asyncio import failed: {e}")
        return False
    
    try:
        import json, logging, os
        from pathlib import Path
        print("✓ Standard library imports: OK") 
    except Exception as e:
        print(f"❌ Standard library imports failed: {e}")
        return False
    
    return True

def test_mcp_imports():
    """Test MCP-specific imports"""
    print("\n=== MCP IMPORTS TEST ===")
    
    try:
        import mcp
        print(f"✓ MCP module: OK (version unknown)")
    except Exception as e:
        print(f"❌ MCP module failed: {e}")
        return False
    
    try:
        from mcp import types
        from mcp.server import NotificationOptions, Server
        from mcp.server.models import InitializationOptions
        from mcp.server.stdio import stdio_server
        print("✓ MCP server imports: OK")
    except Exception as e:
        print(f"❌ MCP server imports failed: {e}")
        print(f"Full error: {traceback.format_exc()}")
        return False
    
    try:
        import httpx
        print("✓ HTTP client (httpx): OK")
    except Exception as e:
        print(f"❌ HTTP client import failed: {e}")
        return False
    
    return True

def test_project_imports():
    """Test project-specific imports"""
    print("\n=== PROJECT IMPORTS TEST ===")
    
    # Set up path
    script_dir = Path(__file__).parent
    src_dir = script_dir / "src"
    sys.path.insert(0, str(src_dir))
    
    print(f"Added to Python path: {src_dir}")
    
    try:
        from config import get_config
        print("✓ Config module import: OK")
    except Exception as e:
        print(f"❌ Config module import failed: {e}")
        print(f"Full error: {traceback.format_exc()}")
        return False
    
    try:
        config = get_config()
        print(f"✓ Config loading: OK ({len(config.fortimanager_instances)} FortiManager instances)")
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        print(f"Full error: {traceback.format_exc()}")
        return False
    
    try:
        from platforms.fortigate import FortiGateManager
        from platforms.fortimanager import FortiManagerManager  
        from platforms.meraki import MerakiManager
        print("✓ Platform modules: OK")
    except Exception as e:
        print(f"❌ Platform imports failed: {e}")
        print(f"Full error: {traceback.format_exc()}")
        return False
    
    return True

def test_server_creation():
    """Test MCP server creation"""
    print("\n=== SERVER CREATION TEST ===")
    
    try:
        from mcp.server import Server
        server = Server("network-device-mcp")
        print("✓ MCP Server creation: OK")
        return True
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        print(f"Full error: {traceback.format_exc()}")
        return False

def test_full_startup():
    """Test the actual main.py startup"""
    print("\n=== FULL STARTUP TEST ===")
    
    try:
        # Import the main module
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        import main
        print("✓ Main module import: OK")
        
        # This won't actually run the async server, but will test if it can be imported
        print("✓ Full startup test: OK (import successful)")
        return True
        
    except Exception as e:
        print(f"❌ Full startup failed: {e}")
        print(f"Full error: {traceback.format_exc()}")
        return False

def main():
    """Run all tests"""
    print("COMPREHENSIVE MCP SERVER DIAGNOSTIC")
    print("=" * 50)
    
    all_passed = True
    
    # Run each test
    tests = [
        test_python_basics,
        test_mcp_imports, 
        test_project_imports,
        test_server_creation,
        test_full_startup
    ]
    
    for test in tests:
        if not test():
            all_passed = False
            print(f"\n❌ TEST FAILED: {test.__name__}")
            break  # Stop at first failure to see specific error
        print("✓ PASSED")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The MCP server should work - issue is likely with Claude Desktop connection.")
        print("Try completely restarting Claude Desktop and your computer.")
    else:
        print("❌ TESTS FAILED")
        print("The error above shows exactly why the MCP server won't start.")
        print("Copy the error message to get help fixing it.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
