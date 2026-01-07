import requests
import time

def robust_mac_lookup(mac_address):
    """
    Robust MAC vendor lookup function with improved error handling and timeout management
    """
    apis = [
        {
            'name': 'MacVendors.com',
            'url': f"https://api.macvendors.com/{mac_address}",
            'timeout': 5,
            'expected_format': 'text'
        },
        {
            'name': 'MacVendors.co',
            'url': f"https://macvendors.co/api/{mac_address}",
            'timeout': 10,  # Longer timeout for slower API
            'expected_format': 'json'
        },
        {
            'name': 'MacVendorLookup.com',
            'url': f"https://www.macvendorlookup.com/api/v2/{mac_address.replace(':', '')[:6]}",
            'timeout': 8,
            'expected_format': 'json'
        },
        {
            'name': 'MacLookup.app',
            'url': f"https://api.maclookup.app/v2/macs/{mac_address}",
            'timeout': 7,
            'expected_format': 'json'
        },
        {
            'name': 'HWAddress.com',
            'url': f"https://hwaddress.com/company/{mac_address.replace(':', '')[:6]}",
            'timeout': 6,
            'expected_format': 'text'
        }
    ]
    
    for api in apis:
        try:
            print(f"Trying {api['name']}...")
            
            response = requests.get(
                api['url'],
                timeout=api['timeout'],
                headers={'User-Agent': 'Mozilla/5.0 (compatible; MAC-Lookup/1.0)'}
            )
            
            if response.status_code == 200:
                response_text = response.text.strip()
                # Validate response has meaningful content
                if len(response_text) > 3 and not any(invalid in response_text.lower() for invalid in [
                    'not found', 'n/a', 'unknown', 'none', 'null', 'error', 'invalid'
                ]):
                    print(f"✅ Success: {response_text}")
                    return response_text
                else:
                    print(f"❌ {api['name']}: No valid vendor found")
                    
            elif response.status_code == 429:
                print(f"⚠️ {api['name']}: Rate limited")
            else:
                print(f"❌ {api['name']}: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ {api['name']} timed out")
        except requests.exceptions.ConnectionError:
            print(f"❌ {api['name']}: Connection failed")
        except requests.exceptions.RequestException as e:
            print(f"❌ {api['name']} failed: {e}")
        except Exception as e:
            print(f"❌ {api['name']}: Unexpected error: {str(e)[:50]}")
    
    return None

def test_multiple_macs():
    """
    Test multiple MAC addresses to verify the robust lookup works
    """
    test_macs = [
        "44:38:39:ff:ef:57",  # Original test MAC
        "00:18:7d:19:36:ce",  # TP-Link from your logs
        "00:1B:63:84:45:E6",  # Apple MAC
        "00:50:56:C0:00:01",  # VMware MAC
    ]
    
    print("TESTING ROBUST MAC LOOKUP FUNCTION")
    print("=" * 60)
    
    for mac in test_macs:
        print(f"\n🔍 Testing MAC: {mac}")
        print("-" * 40)
        result = robust_mac_lookup(mac)
        if result:
            print(f"🎯 Final Result: {result}")
        else:
            print("❌ No vendor found from any API")
        print()

def compare_old_vs_new_approach():
    """
    Compare the improvements in the new approach vs old approach
    """
    print("IMPROVEMENTS IN ROBUST MAC LOOKUP")
    print("=" * 50)
    print("✅ Variable timeout per API (5-10 seconds vs fixed 5)")
    print("✅ Better User-Agent header for compatibility")
    print("✅ Enhanced response validation")
    print("✅ More descriptive error messages with emojis")
    print("✅ Clearer success detection logic")
    print("✅ Improved exception handling for different error types")
    print()
    print("Key Features:")
    print("• Timeout tailored to each API's typical response time")
    print("• Validates response content to avoid empty/error responses")
    print("• Uses Mozilla User-Agent to avoid bot detection")
    print("• Distinguishes between timeout, connection, and other errors")
    print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific MAC address
        mac_address = sys.argv[1]
        print(f"Testing MAC address: {mac_address}")
        print("=" * 50)
        result = robust_mac_lookup(mac_address)
        if result:
            print(f"\n🎯 Final Result: {result}")
        else:
            print("\n❌ No vendor found from any API")
    else:
        # Run comparison and multiple tests
        compare_old_vs_new_approach()
        test_multiple_macs()