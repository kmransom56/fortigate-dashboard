#!/usr/bin/env python3
"""
Improved FortiSwitch Test Script

This script tests FortiSwitch connectivity with better error handling
and multiple authentication methods.
"""

import os
import requests
import json
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Disable HTTPS warnings
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# Configuration
FORTIGATE_IP = "192.168.0.254"
SWITCH_ID = os.getenv("FORTIGATE_SWITCH_NAME", "NETINTEGRATESW")

# Load API token from file
API_TOKEN_FILE = os.getenv("FORTIGATE_API_TOKEN_FILE", "./secrets/fortigate_api_token.txt")
if os.path.exists(API_TOKEN_FILE):
    with open(API_TOKEN_FILE, 'r') as f:
        API_TOKEN = f.read().strip()
else:
    API_TOKEN = os.getenv("FORTIGATE_API_TOKEN")

def test_connectivity():
    """Test basic connectivity to FortiGate"""
    print("🔍 Testing connectivity...")
    
    try:
        response = requests.get(f"https://{FORTIGATE_IP}/login", verify=False, timeout=10)
        if response.status_code == 200:
            print("✅ FortiGate is reachable")
            return True
        else:
            print(f"❌ FortiGate returned HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach FortiGate: {e}")
        return False

def test_api_token():
    """Test API token authentication"""
    print("\n🔑 Testing API token...")
    
    if not API_TOKEN:
        print("❌ No API token found in environment")
        print("Set it with: export FORTIGATE_API_TOKEN=your-token")
        return False
    
    print(f"Token: {API_TOKEN[:10]}...")
    
    try:
        url = f"https://{FORTIGATE_IP}/api/v2/monitor/system/status"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            print("✅ API token works!")
            return True
        else:
            print(f"❌ API token failed: HTTP {response.status_code}")
            if response.status_code == 401:
                print("   This means the token is invalid or expired")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

def test_switch_endpoints():
    """Test switch-specific endpoints"""
    print("\n🔌 Testing switch endpoints...")
    
    if not API_TOKEN:
        print("❌ No API token available")
        return False
    
    endpoints = [
        ("monitor/switch-controller/managed-switch", "List managed switches"),
        ("monitor/switch-controller/managed-switch/status", f"Status for switch {SWITCH_ID}"),
        ("monitor/switch-controller/managed-switch/interface", f"Interfaces for switch {SWITCH_ID}")
    ]
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    for endpoint, description in endpoints:
        print(f"\n📍 {description}")
        try:
            url = f"https://{FORTIGATE_IP}/api/v2/{endpoint}"
            params = {"switch-id": SWITCH_ID} if "status" in endpoint or "interface" in endpoint else None
            
            response = requests.get(url, headers=headers, params=params, verify=False, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ HTTP {response.status_code}")
                try:
                    data = response.json()
                    if 'results' in data:
                        print(f"   📊 Found {len(data['results'])} results")
                        if data['results']:
                            print(f"   📋 Sample result keys: {list(data['results'][0].keys())[:5]}")
                    else:
                        print(f"   📊 Response keys: {list(data.keys())[:5]}")
                except Exception as e:
                    print(f"   📝 Response length: {len(response.text)} chars")
            elif response.status_code == 401:
                print(f"❌ HTTP {response.status_code} (Unauthorized)")
            else:
                print(f"⚠️ HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"❌ Request timed out")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print("🚀 FortiSwitch Test Script")
    print("=" * 40)
    
    # Test connectivity
    if not test_connectivity():
        print("\n❌ Cannot proceed without connectivity")
        sys.exit(1)
    
    # Test API token
    if not test_api_token():
        print("\n❌ Cannot proceed without valid API token")
        print("\nTo fix this:")
        print("1. Get a valid API token from FortiGate GUI")
        print("2. Set it with: export FORTIGATE_API_TOKEN=your-token")
        print("3. Run this script again")
        sys.exit(1)
    
    # Test switch endpoints
    test_switch_endpoints()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
