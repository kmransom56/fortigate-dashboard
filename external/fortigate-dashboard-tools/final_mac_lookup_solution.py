import subprocess
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import time
from typing import Optional, Dict, List

class FinalMacLookup:
    """
    Final comprehensive MAC lookup solution addressing SSL certificate issues
    
    Problem Identified:
    - Python requests fails with: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
    - Basic Constraints of CA cert not marked critical
    
    Solution:
    1. Offline-first with comprehensive local database
    2. Curl-based online lookup (since curl works in your environment)
    3. Fallback to requests with verify=False if needed
    """
    
    def __init__(self):
        self.cache = {}
        self.curl_available = self._test_curl_availability()
        
        # Comprehensive local OUI database
        self.local_oui_database = {
            # Discovered from your network
            '443839': 'Cumulus Networks, Inc.',  # From curl test result
            '00187D': 'TP-Link Technologies Co. Ltd.',  # From your logs
            
            # Major manufacturers
            '001B63': 'Apple Inc.',
            '001ED2': 'Apple Inc.',
            '28E02C': 'Apple Inc.',
            '3C0754': 'Apple Inc.',
            '40A6D9': 'Apple Inc.',
            '68AB1E': 'Apple Inc.',
            '7CF05F': 'Apple Inc.',
            'B065BD': 'Apple Inc.',
            'DC2B2A': 'Apple Inc.',
            'F0DBE2': 'Apple Inc.',
            
            # Dell
            '001E4F': 'Dell Inc.',
            '0026B9': 'Dell Inc.',
            '002564': 'Dell Inc.',
            'D4BED9': 'Dell Inc.',
            'F04DA2': 'Dell Inc.',
            
            # HP/HPE
            '001A4B': 'Hewlett Packard Enterprise',
            '002264': 'Hewlett Packard Enterprise',
            '0030C1': 'Hewlett Packard Enterprise',
            '70106F': 'Hewlett Packard Enterprise',
            
            # VMware Virtual NICs
            '005056': 'VMware Inc.',
            '000C29': 'VMware Inc.',
            '001C14': 'VMware Inc.',
            
            # Cisco
            '001B2F': 'Cisco Systems Inc.',
            '001C58': 'Cisco Systems Inc.',
            '00215A': 'Cisco Systems Inc.',
            '0024F7': 'Cisco Systems Inc.',
            '002618': 'Cisco Systems Inc.',
            '506B4B': 'Cisco Systems Inc.',
            
            # TP-Link (common in corporate networks)
            '001A92': 'TP-Link Technologies Co. Ltd.',
            '002191': 'TP-Link Technologies Co. Ltd.',
            '50C7BF': 'TP-Link Technologies Co. Ltd.',
            '14CC20': 'TP-Link Technologies Co. Ltd.',
            '64F9A0': 'TP-Link Technologies Co. Ltd.',
            'D8C790': 'TP-Link Technologies Co. Ltd.',
            
            # Microsoft devices
            '0050F2': 'Microsoft Corporation',
            '1C697A': 'Microsoft Corporation',
            'F4F951': 'Microsoft Corporation',
            
            # Intel NICs
            '001B21': 'Intel Corporation',
            '0025B3': 'Intel Corporation',
            '68B599': 'Intel Corporation',
            'A0369F': 'Intel Corporation',
            
            # Samsung
            '002566': 'Samsung Electronics Co. Ltd.',
            '34E2FD': 'Samsung Electronics Co. Ltd.',
            '68A86D': 'Samsung Electronics Co. Ltd.',
            
            # Common IoT devices
            'B827EB': 'Raspberry Pi Foundation',
            'DC4F22': 'Espressif Inc. (ESP32/ESP8266)',
            'CC50E3': 'Espressif Inc. (ESP32/ESP8266)',
        }
        
        print(f"🔧 Final MAC lookup solution initialized")
        print(f"📚 Local database: {len(self.local_oui_database)} OUI mappings")
        print(f"📡 Curl available: {self.curl_available}")

    def _test_curl_availability(self) -> bool:
        """Test if curl is available and working"""
        try:
            result = subprocess.run(['curl', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def get_oui_from_mac(self, mac_address: str) -> str:
        """Extract OUI (first 6 characters) from MAC address"""
        clean_mac = mac_address.replace(':', '').replace('-', '').replace(' ', '').upper()
        return clean_mac[:6] if len(clean_mac) >= 6 else clean_mac

    def method_1_local_database(self, oui: str) -> Optional[str]:
        """Method 1: Local database lookup (fastest, most reliable)"""
        return self.local_oui_database.get(oui)

    def method_2_curl_lookup(self, mac_address: str) -> Optional[str]:
        """Method 2: Curl-based online lookup (works in your environment)"""
        if not self.curl_available:
            return None
        
        try:
            curl_cmd = [
                'curl', '-s', '--max-time', '8',
                '--user-agent', 'Mozilla/5.0 (compatible; MAC-Lookup-Curl/1.0)',
                f"https://api.macvendors.com/{mac_address}"
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                response = result.stdout.strip()
                
                # Validate response
                if len(response) > 3 and not any(invalid in response.lower() for invalid in [
                    'not found', 'n/a', 'unknown', 'none', 'null', 'error', 'invalid'
                ]):
                    return response
                    
        except Exception as e:
            print(f"❌ Curl lookup failed: {str(e)[:50]}")
            
        return None

    def method_3_requests_no_ssl(self, mac_address: str) -> Optional[str]:
        """Method 3: Python requests without SSL verification (fallback)"""
        try:
            urllib3.disable_warnings(InsecureRequestWarning)
            
            response = requests.get(
                f"https://api.macvendors.com/{mac_address}",
                timeout=10,
                verify=False,  # Bypass SSL verification
                headers={'User-Agent': 'Mozilla/5.0 (compatible; MAC-Lookup-NoSSL/1.0)'}
            )
            
            if response.status_code == 200:
                result = response.text.strip()
                
                # Validate response
                if len(result) > 3 and not any(invalid in result.lower() for invalid in [
                    'not found', 'n/a', 'unknown', 'none', 'null', 'error', 'invalid'
                ]):
                    return result
                    
        except Exception as e:
            print(f"❌ No-SSL requests failed: {str(e)[:50]}")
            
        return None

    def comprehensive_lookup(self, mac_address: str) -> Dict[str, any]:
        """
        Comprehensive MAC vendor lookup using all available methods
        """
        print(f"\n🔍 MAC Vendor Lookup: {mac_address}")
        print("-" * 50)
        
        oui = self.get_oui_from_mac(mac_address)
        
        result = {
            'mac_address': mac_address,
            'oui': oui,
            'vendor': None,
            'source': None,
            'success': False,
            'ssl_issue_bypassed': False
        }
        
        # Check cache first
        if oui in self.cache:
            result['vendor'] = self.cache[oui]
            result['source'] = 'cache'
            result['success'] = True
            print(f"💾 Found in cache: {result['vendor']}")
            return result
        
        # Method 1: Local database (fastest, most reliable)
        print("1️⃣ Checking local database...")
        local_vendor = self.method_1_local_database(oui)
        if local_vendor:
            result['vendor'] = local_vendor
            result['source'] = 'local_database'
            result['success'] = True
            self.cache[oui] = local_vendor
            print(f"✅ Found in local database: {local_vendor}")
            return result
        
        print("❌ Not found in local database")
        
        # Method 2: Curl-based lookup (works in your environment)
        print("2️⃣ Trying curl-based online lookup...")
        if self.curl_available:
            curl_vendor = self.method_2_curl_lookup(mac_address)
            if curl_vendor:
                result['vendor'] = curl_vendor
                result['source'] = 'curl_api'
                result['success'] = True
                self.cache[oui] = curl_vendor
                print(f"✅ Found via curl: {curl_vendor}")
                return result
            else:
                print("❌ Curl lookup failed")
        else:
            print("❌ Curl not available")
        
        # Method 3: Requests without SSL verification (last resort)
        print("3️⃣ Trying requests without SSL verification...")
        no_ssl_vendor = self.method_3_requests_no_ssl(mac_address)
        if no_ssl_vendor:
            result['vendor'] = no_ssl_vendor
            result['source'] = 'requests_no_ssl'
            result['success'] = True
            result['ssl_issue_bypassed'] = True
            self.cache[oui] = no_ssl_vendor
            print(f"✅ Found via no-SSL requests: {no_ssl_vendor}")
            print("⚠️ SSL verification was bypassed")
            return result
        else:
            print("❌ No-SSL requests failed")
        
        # Unknown vendor
        result['vendor'] = f"Unknown Vendor (OUI: {oui})"
        result['source'] = 'unknown'
        print(f"❌ Unknown vendor for OUI: {oui}")
        
        # Provide research links
        print(f"🔗 Manual research links:")
        print(f"   • https://maclookup.app/macaddress/{oui}")
        print(f"   • https://www.wireshark.org/tools/oui-lookup.html")
        
        return result

def demonstrate_ssl_solution():
    """
    Demonstrate the SSL issue and solution
    """
    print("🔒 SSL CERTIFICATE VERIFICATION ISSUE ANALYSIS")
    print("=" * 70)
    print("Problem: Python requests fails with SSL certificate verification")
    print("Error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")
    print("Details: unable to get local issuer certificate")
    print()
    print("Root Cause: Corporate environment SSL certificate validation issues")
    print()
    print("✅ Solutions Implemented:")
    print("1. Offline-first approach with comprehensive local database")
    print("2. Curl-based online lookup (curl works in your environment)")
    print("3. Fallback to requests with verify=False if needed")
    print("4. Intelligent caching to minimize online lookups")
    print()
    
    lookup = FinalMacLookup()
    
    test_cases = [
        ("44:38:39:ff:ef:57", "Should find: Cumulus Networks, Inc."),
        ("00:18:7d:19:36:ce", "Should find: TP-Link Technologies Co. Ltd."),
        ("00:1B:63:84:45:E6", "Should find: Apple Inc. (local DB)"),
        ("AA:BB:CC:DD:EE:FF", "Should test online lookup"),
    ]
    
    print("🧪 TESTING ALL METHODS:")
    print("=" * 50)
    
    for mac, expected in test_cases:
        print(f"\n📋 Test Case: {mac}")
        print(f"Expected: {expected}")
        
        result = lookup.comprehensive_lookup(mac)
        
        print(f"🎯 Result: {result['vendor']}")
        print(f"📍 Source: {result['source']}")
        print(f"✅ Success: {result['success']}")
        if result.get('ssl_issue_bypassed'):
            print(f"⚠️ SSL bypassed: {result['ssl_issue_bypassed']}")
        print()

def create_integration_instructions():
    """
    Create instructions for integrating into device discovery tool
    """
    instructions = """
# INTEGRATION INSTRUCTIONS FOR DEVICE DISCOVERY TOOL

## Replace the _lookup_oui_multiple_sources method in device_discovery_tool.py:

```python
def _lookup_oui_multiple_sources(self, oui: str, full_mac: str) -> str:
    '''
    Enhanced MAC vendor lookup addressing SSL certificate issues
    Uses curl-based approach since curl works in your environment
    '''
    # Try curl first (most reliable in your environment)
    try:
        curl_cmd = [
            'curl', '-s', '--max-time', '8',
            '--user-agent', 'Mozilla/5.0 (compatible; MAC-Lookup/1.0)',
            f"https://api.macvendors.com/{full_mac}"
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            response = result.stdout.strip()
            if len(response) > 3 and 'not found' not in response.lower():
                print(f"    ✓ Curl lookup: {response}")
                return response
                
    except Exception as e:
        print(f"    ✗ Curl failed: {str(e)[:50]}")
    
    # Fallback to requests without SSL verification
    try:
        import urllib3
        from urllib3.exceptions import InsecureRequestWarning
        urllib3.disable_warnings(InsecureRequestWarning)
        
        response = requests.get(
            f"https://api.macvendors.com/{full_mac}",
            timeout=10,
            verify=False,  # Bypass SSL verification
            headers={'User-Agent': 'Mozilla/5.0 (compatible; MAC-Lookup/1.0)'}
        )
        
        if response.status_code == 200:
            result = response.text.strip()
            if len(result) > 3 and 'not found' not in result.lower():
                print(f"    ✓ No-SSL lookup: {result}")
                return result
                
    except Exception as e:
        print(f"    ✗ No-SSL failed: {str(e)[:50]}")
    
    return None
```

## Add import at top of file:
```python
import subprocess
```

## Benefits:
- ✅ Bypasses SSL certificate verification issues
- ✅ Uses curl (which works in your environment)
- ✅ Maintains fallback to requests without SSL verification
- ✅ Preserves existing local database functionality
- ✅ Minimal code changes to existing tool
"""
    
    with open('integration_instructions.md', 'w') as f:
        f.write(instructions)
    
    print("📄 Integration instructions saved to: integration_instructions.md")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Run demonstration
        demonstrate_ssl_solution()
        create_integration_instructions()
    elif len(sys.argv) > 1:
        # Single MAC lookup
        mac_address = sys.argv[1]
        lookup = FinalMacLookup()
        result = lookup.comprehensive_lookup(mac_address)
        print(f"\n🎯 Final Result: {result['vendor']} (Source: {result['source']})")
    else:
        # Quick test
        lookup = FinalMacLookup()
        result = lookup.comprehensive_lookup("44:38:39:ff:ef:57")
        print(f"\n🎯 Quick Test Result: {result['vendor']} (Source: {result['source']})")