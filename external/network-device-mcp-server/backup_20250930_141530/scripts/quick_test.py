#!/usr/bin/env python3
"""Simple test to identify MCP server startup issues"""

import sys
import traceback
from pathlib import Path

def test_mcp_server_startup():
    """Test each component that might cause startup failure"""
    
    print("Testing MCP Server Startup Components")
    print("=" * 45)
    
    # Test 1: Basic imports
    try:
        import asyncio
        import json
        import logging
        import os
        from pathlib import Path
        print("✓ Basic imports: OK")
    except Exception as e:
        print(f"❌ Basic imports failed: {e}")
        return False
    
    # Test 2: MCP imports
    try:
        import mcp
        from mcp import types
        from mcp.server import NotificationOptions, Server
        from mcp.server.models import InitializationOptions
        from mcp.server.stdio import stdio_server
        print("✓ MCP imports: OK")
    except Exception as e:
        print(f"❌ MCP imports failed: {e}")
        print("Fix: pip install mcp>=1.0.0")
        return False
    
    # Test 3: HTTP client imports
    try:
        import httpx
        print("✓ HTTP client: OK")
    except Exception as e:
        print(f"❌ HTTP client import failed: {e}")
        print("Fix: pip install httpx")
        return False
    
    # Test 4: Project path setup
    try:
        script_dir = Path(__file__).parent.resolve()
        sys.path.insert(0, str(script_dir))
        print(f"✓ Project path: {script_dir}")
    except Exception as e:
        print(f"❌ Path setup failed: {e}")
        return False
    
    # Test 5: Config import
    try:
        from config import get_config
        print("✓ Config import: OK")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return False
    
    # Test 6: Config loading
    try:
        config = get_config()
        print(f"✓ Config loaded: {len(config.fortimanager_instances)} FortiManager instances")
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return False
    
    # Test 7: Platform imports
    try:
        from platforms.fortigate import FortiGateManager
        from platforms.fortimanager import FortiManagerManager  
        from platforms.meraki import MerakiManager
        print("✓ Platform imports: OK")
    except Exception as e:
        print(f"❌ Platform imports failed: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return False
    
    # Test 8: Server class creation
    try:
        server = Server("network-device-mcp")
        print("✓ MCP Server creation: OK")
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("The MCP server should work. Issue is likely with Claude Desktop connection.")
    print("\nYour FortiManager instances:")
    
    try:
        for fm in config.fortimanager_instances:
            print(f"  • {fm['name']}: {fm['host']}")
    except:
        print("  (Could not load FortiManager list)")
    
    return True

if __name__ == "__main__":
    try:
        success = test_mcp_server_startup()
        if not success:
            print("\n❌ STARTUP TEST FAILED")
            print("Copy the error messages above to get help fixing the issue.")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        print(f"Full error: {traceback.format_exc()}")
        sys.exit(1)
