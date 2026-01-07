#!/usr/bin/env python3
"""
Quick test to check FortiManager connectivity and API responses
"""
import requests
import json

def test_local_api():
    """Test the local Flask API endpoints"""
    print("🧪 Testing Network MCP Server API...")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        "/health",
        "/api",
        "/api/brands", 
        "/api/brands/BWW/overview",
        "/api/fortimanager"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Testing: {endpoint}")
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'error' in data:
                    print(f"   Error: {data['error']}")
                else:
                    print("   ✅ Success!")
                    # Show first few keys of response
                    if isinstance(data, dict):
                        keys = list(data.keys())[:3]
                        print(f"   Data keys: {keys}")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                print(f"   Response: {response.text[:100]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection Error: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON Error: {str(e)}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🔍 If APIs are failing:")
    print("1. Check server logs in the terminal")
    print("2. Verify FortiManager connectivity") 
    print("3. Test network access to devices")
    print("4. Check .env credentials")

if __name__ == "__main__":
    test_local_api()
