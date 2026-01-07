#!/usr/bin/env python3
"""
ADOM Discovery Tool - Find the correct ADOMs for each FortiManager
"""
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from config import get_config
    from platforms.fortimanager import FortiManagerManager
    print("✅ Successfully imported MCP modules")
except ImportError as e:
    print(f"❌ Failed to import MCP modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

async def discover_adoms():
    """Discover available ADOMs on each FortiManager instance"""
    print("🔍 Discovering ADOMs on FortiManager instances...")
    print("=" * 60)
    
    config = get_config()
    fm_manager = FortiManagerManager()
    
    for fm in config.fortimanager_instances:
        print(f"\n📊 FortiManager: {fm['name']} ({fm['host']})")
        print("-" * 40)
        
        try:
            # Try to get ADOMs list (this might need to be implemented)
            print(f"   Connecting to {fm['host']}...")
            
            # For now, let's try common ADOM names and see device counts
            common_adoms = ['root', 'global', fm['name'].lower(), 
                           f"{fm['name'].lower()}_adom", 'main', 'production']
            
            for adom in common_adoms:
                try:
                    print(f"   Trying ADOM: '{adom}'...")
                    devices = await fm_manager.get_managed_devices(
                        fm['host'], fm['username'], fm['password'], adom
                    )
                    
                    device_count = len(devices) if devices else 0
                    print(f"   ✅ ADOM '{adom}': {device_count} devices")
                    
                    if device_count > 50:  # Likely the right ADOM
                        print(f"   🎯 CANDIDATE: '{adom}' has {device_count} devices - likely correct!")
                        
                        # Show first few device names as sample
                        if devices and len(devices) > 0:
                            print(f"   📱 Sample devices:")
                            for i, device in enumerate(devices[:3]):
                                if isinstance(device, dict):
                                    name = device.get('name', 'Unknown')
                                    print(f"      {i+1}. {name}")
                                else:
                                    print(f"      {i+1}. {device}")
                    
                except Exception as e:
                    print(f"   ❌ ADOM '{adom}': {str(e)}")
                
        except Exception as e:
            print(f"   ❌ Failed to connect: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATION:")
    print("1. Look for ADOMs with high device counts (1000+)")
    print("2. Update the API to use the correct ADOM for each brand")
    print("3. Consider implementing ADOM selection in the UI")

if __name__ == "__main__":
    try:
        asyncio.run(discover_adoms())
    except KeyboardInterrupt:
        print("\n⚠️ Discovery cancelled by user")
    except Exception as e:
        print(f"\n❌ Discovery failed: {e}")
