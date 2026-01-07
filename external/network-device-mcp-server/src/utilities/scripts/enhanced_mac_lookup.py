import requests
import time
import json
import re
from typing import Optional, Dict, List

class EnhancedMacLookup:
    """
    Enhanced MAC address vendor lookup with offline fallbacks and network diagnostics
    """
    
    def __init__(self):
        self.oui_cache = {}
        self.network_available = None
        
        # Enhanced local OUI database (expandable)
        self.local_oui_database = {
            # Your specific examples
            '443839': 'Cumulus Networks, Inc.',  # From curl test result
            '00187D': 'TP-Link Technologies Co. Ltd.',
            
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
            '00187D': 'TP-Link Technologies Co. Ltd.',
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
        
        print(f"Loaded {len(self.local_oui_database)} local OUI mappings")

    def test_network_connectivity(self) -> bool:
        """
        Test basic network connectivity to external services
        """
        if self.network_available is not None:
            return self.network_available
            
        test_urls = [
            'https://httpbin.org/get',
            'https://api.github.com',
            'https://www.google.com'
        ]
        
        print("🌐 Testing network connectivity...")
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; Network-Test/1.0)'
                })
                if response.status_code == 200:
                    print(f"✅ Network connectivity confirmed via {url}")
                    self.network_available = True
                    return True
            except Exception as e:
                print(f"❌ Failed to reach {url}: {str(e)[:50]}")
                continue
        
        print("🚫 No network connectivity detected - using offline mode")
        self.network_available = False
        return False

    def get_oui_from_mac(self, mac_address: str) -> str:
        """
        Extract OUI (first 6 characters) from MAC address
        """
        clean_mac = mac_address.replace(':', '').replace('-', '').replace(' ', '').upper()
        return clean_mac[:6] if len(clean_mac) >= 6 else clean_mac

    def lookup_local_database(self, oui: str) -> Optional[str]:
        """
        Look up vendor in local database
        """
        return self.local_oui_database.get(oui)

    def robust_online_lookup(self, mac_address: str) -> Optional[str]:
        """
        Enhanced online lookup with better error handling
        """
        if not self.test_network_connectivity():
            return None
            
        apis = [
            {
                'name': 'MacVendors.com',
                'url': f"https://api.macvendors.com/{mac_address}",
                'timeout': 8,
                'headers': {'User-Agent': 'Mozilla/5.0 (compatible; MAC-Lookup/1.0)'}
            },
            {
                'name': 'MacVendors.co',
                'url': f"https://macvendors.co/api/{mac_address}",
                'timeout': 12,
                'headers': {'User-Agent': 'Mozilla/5.0 (compatible; MAC-Lookup/1.0)'}
            }
        ]
        
        for api in apis:
            try:
                print(f"🔍 Trying {api['name']}...")
                
                response = requests.get(
                    api['url'],
                    timeout=api['timeout'],
                    headers=api['headers']
                )
                
                if response.status_code == 200:
                    result = response.text.strip()
                    # Validate meaningful response
                    if len(result) > 3 and not any(invalid in result.lower() for invalid in [
                        'not found', 'n/a', 'unknown', 'none', 'null', 'error', 'invalid'
                    ]):
                        print(f"✅ Success from {api['name']}: {result}")
                        return result
                    else:
                        print(f"❌ {api['name']}: Empty or invalid response")
                        
                elif response.status_code == 429:
                    print(f"⚠️ {api['name']}: Rate limited")
                    time.sleep(2)  # Brief delay before trying next API
                else:
                    print(f"❌ {api['name']}: HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"⏰ {api['name']}: Timeout after {api['timeout']}s")
            except requests.exceptions.ConnectionError:
                print(f"🚫 {api['name']}: Connection failed")
            except Exception as e:
                print(f"❌ {api['name']}: {str(e)[:60]}")
                
        return None

    def download_ieee_oui_database(self) -> bool:
        """
        Download official IEEE OUI database for offline use
        """
        if not self.test_network_connectivity():
            print("❌ Cannot download IEEE database - no network connectivity")
            return False
            
        ieee_url = "https://standards-oui.ieee.org/oui/oui.txt"
        
        try:
            print("📥 Downloading IEEE OUI database...")
            response = requests.get(ieee_url, timeout=30)
            
            if response.status_code == 200:
                # Parse the IEEE format and extract OUI mappings
                oui_mappings = self.parse_ieee_oui_data(response.text)
                
                # Save to local file
                with open('ieee_oui_database.json', 'w') as f:
                    json.dump(oui_mappings, f, indent=2)
                
                print(f"✅ Downloaded {len(oui_mappings)} OUI mappings from IEEE")
                
                # Merge with local database
                self.local_oui_database.update(oui_mappings)
                print(f"📊 Total OUI mappings: {len(self.local_oui_database)}")
                
                return True
            else:
                print(f"❌ Failed to download IEEE database: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading IEEE database: {e}")
            return False

    def parse_ieee_oui_data(self, ieee_data: str) -> Dict[str, str]:
        """
        Parse IEEE OUI data format and extract vendor mappings
        """
        oui_mappings = {}
        lines = ieee_data.split('\n')
        
        for line in lines:
            # IEEE format: OUI-24     Company Name
            if '\t' in line and '(hex)' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    oui_part = parts[0].strip()
                    company_part = parts[1].strip()
                    
                    # Extract OUI (remove (hex) suffix)
                    oui = oui_part.replace('(hex)', '').replace('-', '').strip()
                    if len(oui) == 6:
                        oui_mappings[oui.upper()] = company_part
        
        return oui_mappings

    def comprehensive_mac_lookup(self, mac_address: str) -> Dict[str, any]:
        """
        Comprehensive MAC lookup using all available methods
        """
        print(f"\n🔍 Comprehensive MAC Lookup: {mac_address}")
        print("=" * 60)
        
        # Extract OUI
        oui = self.get_oui_from_mac(mac_address)
        print(f"📍 OUI: {oui}")
        
        results = {
            'mac_address': mac_address,
            'oui': oui,
            'vendor': None,
            'source': None,
            'network_available': self.test_network_connectivity()
        }
        
        # Method 1: Local database lookup
        print("\n1️⃣ Checking local database...")
        local_vendor = self.lookup_local_database(oui)
        if local_vendor:
            print(f"✅ Found in local database: {local_vendor}")
            results['vendor'] = local_vendor
            results['source'] = 'local_database'
            return results
        else:
            print("❌ Not found in local database")
        
        # Method 2: Online lookup (if network available)
        if results['network_available']:
            print("\n2️⃣ Trying online APIs...")
            online_vendor = self.robust_online_lookup(mac_address)
            if online_vendor:
                results['vendor'] = online_vendor
                results['source'] = 'online_api'
                return results
            else:
                print("❌ Online lookup failed")
        else:
            print("\n2️⃣ Skipping online lookup - no network connectivity")
        
        # Method 3: IEEE database download (last resort)
        if results['network_available']:
            print("\n3️⃣ Attempting IEEE database download...")
            if self.download_ieee_oui_database():
                ieee_vendor = self.lookup_local_database(oui)
                if ieee_vendor:
                    results['vendor'] = ieee_vendor
                    results['source'] = 'ieee_database'
                    return results
        
        # No vendor found
        print(f"\n❌ No vendor found for OUI: {oui}")
        results['vendor'] = f"Unknown Vendor (OUI: {oui})"
        results['source'] = 'unknown'
        
        # Provide manual research links
        print(f"\n🔗 Manual research links:")
        print(f"   • https://maclookup.app/macaddress/{oui}")
        print(f"   • https://www.wireshark.org/tools/oui-lookup.html")
        print(f"   • https://hwaddress.com/?q={oui}")
        
        return results

    def batch_lookup(self, mac_addresses: List[str]) -> List[Dict[str, any]]:
        """
        Perform batch lookup for multiple MAC addresses
        """
        print(f"\n📋 Batch MAC Lookup: {len(mac_addresses)} addresses")
        print("=" * 60)
        
        results = []
        unique_ouis = set()
        
        # First pass: identify unique OUIs
        for mac in mac_addresses:
            oui = self.get_oui_from_mac(mac)
            unique_ouis.add(oui)
        
        print(f"📊 Processing {len(unique_ouis)} unique OUIs...")
        
        # Lookup each MAC address
        for i, mac in enumerate(mac_addresses):
            print(f"\n🔄 Processing {i+1}/{len(mac_addresses)}: {mac}")
            result = self.comprehensive_mac_lookup(mac)
            results.append(result)
            
            # Brief delay to avoid overwhelming APIs
            if result['source'] == 'online_api':
                time.sleep(1)
        
        return results

def main():
    """
    Enhanced MAC lookup tool with offline fallbacks
    """
    lookup = EnhancedMacLookup()
    
    # Test with your specific examples
    test_macs = [
        "44:38:39:ff:ef:57",  # Your original test
        "00:18:7d:19:36:ce",  # TP-Link from logs
        "00:1B:63:84:45:E6",  # Apple (should be in local DB)
        "00:50:56:C0:00:01",  # VMware (should be in local DB)
    ]
    
    print("🚀 ENHANCED MAC LOOKUP TOOL")
    print("=" * 70)
    
    # Single lookups
    for mac in test_macs:
        result = lookup.comprehensive_mac_lookup(mac)
        print(f"\n📋 Summary for {mac}:")
        print(f"   Vendor: {result['vendor']}")
        print(f"   Source: {result['source']}")
        print(f"   Network: {'Available' if result['network_available'] else 'Offline'}")
        print("-" * 50)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Single MAC lookup
        mac_address = sys.argv[1]
        lookup = EnhancedMacLookup()
        result = lookup.comprehensive_mac_lookup(mac_address)
        print(f"\n🎯 Final Result: {result['vendor']} (Source: {result['source']})")
    else:
        # Run main demo
        main()