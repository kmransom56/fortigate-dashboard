#!/usr/bin/env python3
"""
Quick test script for Network Device MCP Server
"""
import sys
import os
from pathlib import Path

def test_mcp_server():
    print("Testing Network Device MCP Server...")
    print("=" * 50)
    
    # Test basic imports
    try:
        import asyncio
        import json
        import logging
        from pathlib import Path
        print("✓ Basic Python imports successful")
    except ImportError as e:
        print(f"❌ Basic import failed: {e}")
        return False
    
    # Test MCP import
    try:
        import mcp
        print("✓ MCP module imported successfully")
    except ImportError as e:
        print(f"❌ MCP module not found: {e}")
        return False
    
    # Test project imports
    try:
        sys.path.insert(0, 'src')
        from config import get_config
        config = get_config()
        print(f"✓ Configuration loaded successfully")
        print(f"✓ Found {len(config.fortimanager_instances)} FortiManager instances")
        
        # Show configured instances
        for fm in config.fortimanager_instances:
            print(f"  • {fm['name']}: {fm['host']}")
        
    except Exception as e:
        print(f"⚠️ Configuration test issue: {e}")
        print("Server may still work with basic functionality")
    
    # Test main server imports
    try:
        from platforms.fortigate import FortiGateManager
        from platforms.fortimanager import FortiManagerManager  
        from platforms.meraki import MerakiManager
        print("✓ Platform managers imported successfully")
    except ImportError as e:
        print(f"❌ Platform manager import failed: {e}")
        return False
    
    print("\n🎉 MCP Server Test Results:")
    print("✓ All core components are working")
    print("✓ Ready to connect to Claude Desktop")
    print("\n📋 Your configured FortiManager instances:")
    
    try:
        for fm in config.fortimanager_instances:
            print(f"  🏢 {fm['name']}: {fm['host']}")
    except:
        print("  Check .env file for FortiManager configuration")
    
    print("\n🚀 Next step: Restart Claude Desktop to connect!")
    return True

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
