#!/usr/bin/env python3
"""
Quick topology troubleshooting script
"""

import requests
import json
import os

def test_topology_endpoints():
    """Test all topology-related endpoints"""
    base_url = "http://localhost:10000"
    
    endpoints = [
        "/api/topology_data",
        "/fortigate/api/interfaces", 
        "/fortigate/api/switches"
    ]
    
    print("🔍 Testing Topology Endpoints")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"\n📡 {endpoint}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        if "devices" in data:
                            print(f"   Devices: {len(data.get('devices', []))}")
                        if "connections" in data:
                            print(f"   Connections: {len(data.get('connections', []))}")
                        if "error" in data:
                            print(f"   Error: {data.get('error')}")
                        if "switches" in data:
                            print(f"   Switches: {len(data.get('switches', []))}")
                    elif isinstance(data, list):
                        print(f"   Items: {len(data)}")
                    else:
                        print(f"   Data type: {type(data)}")
                        
                    # Show first few keys
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]
                        print(f"   Keys: {keys}")
                        
                except json.JSONDecodeError:
                    print(f"   Response length: {len(response.text)}")
                    print(f"   Content preview: {response.text[:100]}...")
            else:
                print(f"   Error: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed to {endpoint}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_fortigate_config():
    """Check FortiGate configuration"""
    print("\n🔧 FortiGate Configuration")
    print("=" * 50)
    
    env_vars = [
        "FORTIGATE_HOST",
        "FORTIGATE_USERNAME", 
        "FORTIGATE_SESSION_TTL",
        "FORTIGATE_ALLOW_TOKEN_FALLBACK"
    ]
    
    for var in env_vars:
        value = os.getenv(var, "Not set")
        print(f"   {var}: {value}")
    
    # Check secret files
    secret_files = [
        "secrets/fortigate_password.txt",
        "secrets/fortigate_api_token.txt"
    ]
    
    print(f"\n📁 Secret Files:")
    for file_path in secret_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    print(f"   {file_path}: {'Present' if content else 'Empty'}")
            except Exception as e:
                print(f"   {file_path}: Error reading - {e}")
        else:
            print(f"   {file_path}: Missing")

def main():
    print("🚀 FortiGate Dashboard Topology Troubleshooter")
    print("=" * 60)
    
    check_fortigate_config()
    test_topology_endpoints()
    
    print(f"\n💡 Troubleshooting Tips:")
    print(f"   1. Check FortiGate IP and credentials")  
    print(f"   2. Verify network connectivity to FortiGate")
    print(f"   3. Enable token fallback temporarily if needed")
    print(f"   4. Check FortiGate admin interface for session limits")
    print(f"   5. Review container logs: docker compose logs dashboard")

if __name__ == "__main__":
    main()