import requests
import ssl
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for testing
urllib3.disable_warnings(InsecureRequestWarning)

def test_direct_api_call(mac_address):
    """
    Direct API test with various configurations to bypass connectivity issues
    """
    print(f"🧪 Testing direct API calls for: {mac_address}")
    print("=" * 60)
    
    # Different request configurations to try
    configs = [
        {
            'name': 'Standard Request',
            'session_args': {},
            'request_args': {
                'verify': True,
                'timeout': 10,
                'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            }
        },
        {
            'name': 'No SSL Verification',
            'session_args': {},
            'request_args': {
                'verify': False,
                'timeout': 10,
                'headers': {'User-Agent': 'curl/8.12.1'}  # Mimic curl user agent
            }
        },
        {
            'name': 'Custom SSL Context',
            'session_args': {},
            'request_args': {
                'verify': False,
                'timeout': 15,
                'headers': {
                    'User-Agent': 'curl/8.12.1',
                    'Accept': '*/*',
                    'Connection': 'keep-alive'
                }
            }
        }
    ]
    
    url = f"https://api.macvendors.com/{mac_address}"
    
    for config in configs:
        try:
            print(f"\n🔧 Trying: {config['name']}")
            print(f"URL: {url}")
            
            session = requests.Session()
            
            # Apply session configuration
            for key, value in config['session_args'].items():
                setattr(session, key, value)
            
            response = session.get(url, **config['request_args'])
            
            print(f"✅ Status Code: {response.status_code}")
            print(f"✅ Response: '{response.text.strip()}'")
            print(f"✅ Headers: {dict(response.headers)}")
            
            if response.status_code == 200 and response.text.strip():
                print(f"🎯 SUCCESS! Vendor: {response.text.strip()}")
                return response.text.strip()
                
        except requests.exceptions.SSLError as e:
            print(f"🔒 SSL Error: {str(e)[:100]}")
        except requests.exceptions.ConnectionError as e:
            print(f"🚫 Connection Error: {str(e)[:100]}")
        except requests.exceptions.Timeout as e:
            print(f"⏰ Timeout: {str(e)}")
        except Exception as e:
            print(f"❌ Other Error: {str(e)[:100]}")
    
    print(f"\n❌ All attempts failed for {mac_address}")
    return None

def update_local_database_with_known_results():
    """
    Update local database with known results from curl test
    """
    known_vendors = {
        '443839': 'Cumulus Networks, Inc.',  # From your curl test
        '00187D': 'TP-Link Technologies Co. Ltd.',  # From your existing data
    }
    
    print("📝 Updating enhanced_mac_lookup.py with known vendors...")
    
    # Read the current file
    with open('enhanced_mac_lookup.py', 'r') as f:
        content = f.read()
    
    # Find the local database section and update it
    lines = content.split('\n')
    new_lines = []
    in_database = False
    
    for line in lines:
        if "'443839': 'Unknown Vendor (443839)'," in line:
            # Replace the unknown entry with the correct vendor
            new_lines.append("            '443839': 'Cumulus Networks, Inc.',  # From curl test result")
        else:
            new_lines.append(line)
    
    # Write back the updated content
    with open('enhanced_mac_lookup.py', 'w') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ Updated enhanced_mac_lookup.py with correct vendor")
    
    return known_vendors

if __name__ == "__main__":
    import sys
    
    # Update local database first
    known_vendors = update_local_database_with_known_results()
    
    # Test MAC address
    test_mac = sys.argv[1] if len(sys.argv) > 1 else "44:38:39:ff:ef:57"
    
    # Try direct API call
    result = test_direct_api_call(test_mac)
    
    # Show summary
    print(f"\n📋 SUMMARY FOR {test_mac}")
    print("=" * 40)
    
    oui = test_mac.replace(':', '').replace('-', '').upper()[:6]
    
    if result:
        print(f"🌐 Online Result: {result}")
    else:
        print("🌐 Online Result: Failed")
    
    if oui in known_vendors:
        print(f"💾 Local Database: {known_vendors[oui]}")
    else:
        print("💾 Local Database: Not found")
    
    # Recommendation
    if result:
        print(f"\n✅ RECOMMENDED: Use '{result}' for OUI {oui}")
    elif oui in known_vendors:
        print(f"\n✅ RECOMMENDED: Use '{known_vendors[oui]}' for OUI {oui}")
    else:
        print(f"\n❌ Manual research needed for OUI {oui}")
        print(f"🔗 Research links:")
        print(f"   • https://maclookup.app/macaddress/{oui}")
        print(f"   • https://www.wireshark.org/tools/oui-lookup.html")