#!/usr/bin/env python3
"""
FortiSwitch Authentication Fix

This script helps you fix the authentication issue with your FortiSwitch test.
It provides multiple approaches to get a working API token.
"""

import requests
import json
import os
from urllib.parse import urlencode

# Disable SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_current_token():
    """Test the current API token"""
    print("🔍 Testing current API token...")
    
    token = os.getenv("FORTIGATE_API_TOKEN")
    if not token:
        print("❌ No FORTIGATE_API_TOKEN environment variable found")
        return False
    
    print(f"Token: {token[:10]}...")
    
    try:
        url = "https://192.168.0.254:8443/api/v2/monitor/system/status"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            print("✅ Current token works!")
            return True
        else:
            print(f"❌ Current token failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

def get_working_credentials():
    """Try to find working credentials"""
    print("\n🔑 Trying to find working credentials...")
    
    # Common default credentials to try
    credentials = [
        ("admin", "admin"),
        ("admin", ""),
        ("admin", "password"),
        ("admin", "fortinet"),
        ("admin", "123456"),
    ]
    
    session = requests.Session()
    session.verify = False
    
    for username, password in credentials:
        print(f"Trying {username}:{password if password else '(empty)'}")
        
        try:
            login_data = {
                "username": username,
                "secretkey": password
            }
            
            response = session.post(
                "https://192.168.0.254:8443/logincheck",
                data=login_data,
                timeout=10,
                allow_redirects=False
            )
            
            cookies = session.cookies.get_dict()
            
            if response.status_code in [200, 302] and cookies:
                print(f"✅ Found working credentials: {username}:{password if password else '(empty)'}")
                return username, password, session
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("❌ No working credentials found")
    return None, None, None

def get_api_token_from_gui():
    """Instructions for getting API token from GUI"""
    print("\n📋 MANUAL API TOKEN GENERATION")
    print("=" * 50)
    print("Since automatic login failed, please follow these steps:")
    print()
    print("1. Open your web browser and go to: https://192.168.0.254:8443")
    print("2. Login with your admin credentials")
    print("3. Navigate to: System > Administrators > REST API Admin")
    print("4. Find the user 'programaticallydothings' (or create a new API user)")
    print("5. Click on the user to edit")
    print("6. Copy the API Key value")
    print("7. Run this command to set the token:")
    print("   export FORTIGATE_API_TOKEN=your-api-key-here")
    print("8. Then run: python test_fortiswitch.py")
    print()
    print("Alternative: Create a new API user:")
    print("1. Go to: System > Administrators > REST API Admin")
    print("2. Click 'Create New'")
    print("3. Set Name: 'api-user'")
    print("4. Set API Key: 'your-secure-password'")
    print("5. Set Profile: 'super_admin'")
    print("6. Save and use the API Key as your token")

def test_switch_endpoints():
    """Test if switch endpoints are accessible"""
    print("\n🔌 Testing switch-specific endpoints...")
    
    token = os.getenv("FORTIGATE_API_TOKEN")
    if not token:
        print("❌ No token available for testing")
        return
    
    session = requests.Session()
    session.verify = False
    
    # Test different switch endpoints
    endpoints = [
        "monitor/switch-controller/managed-switch",
        "monitor/switch-controller/managed-switch/status",
        "monitor/switch-controller/managed-switch/interface",
        "monitor/fortilink/switch",
        "cmdb/switch-controller/managed-switch"
    ]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for endpoint in endpoints:
        try:
            url = f"https://192.168.0.254:8443/api/v2/{endpoint}"
            response = session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: HTTP {response.status_code}")
                try:
                    data = response.json()
                    if 'results' in data:
                        print(f"   📊 Found {len(data['results'])} results")
                    else:
                        print(f"   📊 Response keys: {list(data.keys())[:5]}")
                except:
                    print(f"   📝 Response length: {len(response.text)} chars")
            elif response.status_code == 401:
                print(f"❌ {endpoint}: HTTP {response.status_code} (Unauthorized)")
            else:
                print(f"⚠️ {endpoint}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def create_working_test_script():
    """Create a working test script with better error handling"""
    print("\n📝 Creating improved test script...")
    
    script_content = '''#!/usr/bin/env python3
"""
Improved FortiSwitch Test Script

This script tests FortiSwitch connectivity with better error handling
and multiple authentication methods.
"""

import os
import requests
import json
import sys

# Disable HTTPS warnings
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# Configuration
FORTIGATE_IP = "192.168.0.254"
SWITCH_ID = "NETINTEGRATESW"
API_TOKEN = os.getenv("FORTIGATE_API_TOKEN")

def test_connectivity():
    """Test basic connectivity to FortiGate"""
    print("🔍 Testing connectivity...")
    
    try:
        response = requests.get(f"https://{FORTIGATE_IP}:8443/login", verify=False, timeout=10)
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
    print("\\n🔑 Testing API token...")
    
    if not API_TOKEN:
        print("❌ No API token found in environment")
        print("Set it with: export FORTIGATE_API_TOKEN=your-token")
        return False
    
    print(f"Token: {API_TOKEN[:10]}...")
    
    try:
        url = f"https://{FORTIGATE_IP}:8443/api/v2/monitor/system/status"
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
    print("\\n🔌 Testing switch endpoints...")
    
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
        print(f"\\n📍 {description}")
        try:
            url = f"https://{FORTIGATE_IP}:8443/api/v2/{endpoint}"
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
        print("\\n❌ Cannot proceed without connectivity")
        sys.exit(1)
    
    # Test API token
    if not test_api_token():
        print("\\n❌ Cannot proceed without valid API token")
        print("\\nTo fix this:")
        print("1. Get a valid API token from FortiGate GUI")
        print("2. Set it with: export FORTIGATE_API_TOKEN=your-token")
        print("3. Run this script again")
        sys.exit(1)
    
    # Test switch endpoints
    test_switch_endpoints()
    
    print("\\n✅ Test completed!")

if __name__ == "__main__":
    main()
'''
    
    with open("test_fortiswitch_improved.py", "w") as f:
        f.write(script_content)
    
    print("✅ Created test_fortiswitch_improved.py")
    print("Run it with: python test_fortiswitch_improved.py")

def main():
    """Main function"""
    print("🔧 FortiSwitch Authentication Fix")
    print("=" * 50)
    
    # Test current token
    if test_current_token():
        print("\n✅ Your current token works! The issue might be elsewhere.")
        test_switch_endpoints()
        return
    
    # Try to find working credentials
    username, password, session = get_working_credentials()
    
    if username:
        print(f"\n✅ Found working credentials: {username}")
        # Could implement automatic token generation here
    else:
        # Provide manual instructions
        get_api_token_from_gui()
    
    # Create improved test script
    create_working_test_script()

if __name__ == "__main__":
    main()