import subprocess
import json
import time
from typing import Optional, Dict, List
import re

class CurlMacLookup:
    """
    MAC address vendor lookup using curl instead of Python requests
    Since curl works in your environment but Python requests has SSL issues
    """
    
    def __init__(self):
        self.cache = {}
        self.curl_available = self._test_curl_availability()
        
        # Local fallback database (same as enhanced version)
        self.local_oui_database = {
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
        
        print(f"🔧 Curl-based MAC lookup initialized ({len(self.local_oui_database)} local OUIs)")
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

    def curl_api_lookup(self, mac_address: str) -> Optional[str]:
        """
        Use curl to lookup MAC vendor since curl works in your environment
        """
        if not self.curl_available:
            return None
        
        apis = [
            {
                'name': 'MacVendors.com',
                'url': f"https://api.macvendors.com/{mac_address}",
                'timeout': 8
            },
            {
                'name': 'MacVendors.co',
                'url': f"https://macvendors.co/api/{mac_address}",
                'timeout': 12
            }
        ]
        
        for api in apis:
            try:
                print(f"🌐 Trying {api['name']} with curl...")
                
                # Use curl with verbose output for debugging but capture it separately
                curl_cmd = [
                    'curl', '-s', '--max-time', str(api['timeout']),
                    '--user-agent', 'Mozilla/5.0 (compatible; MAC-Lookup-Curl/1.0)',
                    api['url']
                ]
                
                result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=api['timeout'] + 2)
                
                if result.returncode == 0:
                    response = result.stdout.strip()
                    
                    # Validate response
                    if len(response) > 3 and not any(invalid in response.lower() for invalid in [
                        'not found', 'n/a', 'unknown', 'none', 'null', 'error', 'invalid'
                    ]):
                        print(f"✅ Success from {api['name']}: {response}")
                        return response
                    else:
                        print(f"❌ {api['name']}: Invalid response: {response}")
                        
                else:
                    error_msg = result.stderr.strip() if result.stderr else f"Exit code {result.returncode}"
                    print(f"❌ {api['name']}: Curl failed - {error_msg}")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {api['name']}: Curl timeout after {api['timeout']}s")
            except Exception as e:
                print(f"❌ {api['name']}: Curl error - {str(e)}")
                
            # Brief delay between API calls
            time.sleep(1)
                
        return None

    def lookup_mac_vendor(self, mac_address: str) -> Dict[str, any]:
        """
        Comprehensive MAC vendor lookup using curl + local database
        """
        print(f"\n🔍 MAC Vendor Lookup: {mac_address}")
        print("-" * 50)
        
        oui = self.get_oui_from_mac(mac_address)
        
        result = {
            'mac_address': mac_address,
            'oui': oui,
            'vendor': None,
            'source': None,
            'success': False
        }
        
        # Check cache first
        if oui in self.cache:
            result['vendor'] = self.cache[oui]
            result['source'] = 'cache'
            result['success'] = True
            print(f"💾 Found in cache: {result['vendor']}")
            return result
        
        # Method 1: Local database
        if oui in self.local_oui_database:
            vendor = self.local_oui_database[oui]
            result['vendor'] = vendor
            result['source'] = 'local_database'
            result['success'] = True
            self.cache[oui] = vendor
            print(f"📚 Found in local database: {vendor}")
            return result
        
        # Method 2: Curl-based online lookup
        if self.curl_available:
            online_vendor = self.curl_api_lookup(mac_address)
            if online_vendor:
                result['vendor'] = online_vendor
                result['source'] = 'curl_api'
                result['success'] = True
                self.cache[oui] = online_vendor
                return result
        else:
            print("❌ Curl not available, skipping online lookup")
        
        # Method 3: Unknown
        result['vendor'] = f"Unknown Vendor (OUI: {oui})"
        result['source'] = 'unknown'
        print(f"❌ Unknown vendor for OUI: {oui}")
        
        # Provide research links
        print(f"🔗 Manual research links:")
        print(f"   • https://maclookup.app/macaddress/{oui}")
        print(f"   • https://www.wireshark.org/tools/oui-lookup.html")
        
        return result

    def batch_lookup(self, mac_addresses: List[str]) -> List[Dict[str, any]]:
        """
        Perform batch lookup with intelligent OUI grouping
        """
        print(f"\n📋 Batch MAC Lookup: {len(mac_addresses)} addresses")
        print("=" * 60)
        
        # Group by OUI to minimize API calls
        oui_groups = {}
        for mac in mac_addresses:
            oui = self.get_oui_from_mac(mac)
            if oui not in oui_groups:
                oui_groups[oui] = []
            oui_groups[oui].append(mac)
        
        print(f"📊 Processing {len(oui_groups)} unique OUIs...")
        
        results = []
        processed_ouis = set()
        
        for i, mac in enumerate(mac_addresses):
            oui = self.get_oui_from_mac(mac)
            
            # Only lookup each OUI once
            if oui not in processed_ouis:
                lookup_result = self.lookup_mac_vendor(mac)
                processed_ouis.add(oui)
                
                # Cache the result for other MACs with same OUI
                if lookup_result['success']:
                    self.cache[oui] = lookup_result['vendor']
            else:
                # Use cached result
                lookup_result = {
                    'mac_address': mac,
                    'oui': oui,
                    'vendor': self.cache.get(oui, f"Unknown Vendor (OUI: {oui})"),
                    'source': 'cache',
                    'success': oui in self.cache
                }
            
            results.append(lookup_result)
            
            # Progress reporting
            if (i + 1) % 100 == 0:
                print(f"🔄 Processed {i + 1}/{len(mac_addresses)} MAC addresses...")
        
        return results

def main():
    """
    Test the curl-based MAC lookup
    """
    lookup = CurlMacLookup()
    
    test_macs = [
        "44:38:39:ff:ef:57",  # Cumulus Networks (from your curl test)
        "00:18:7d:19:36:ce",  # TP-Link (from your logs)
        "00:1B:63:84:45:E6",  # Apple (should be in local DB)
        "00:50:56:C0:00:01",  # VMware (should be in local DB)
        "AA:BB:CC:DD:EE:FF",  # Unknown MAC for testing
    ]
    
    print("🚀 CURL-BASED MAC LOOKUP TOOL")
    print("=" * 70)
    print("This tool uses curl instead of Python requests to bypass SSL issues")
    print()
    
    for mac in test_macs:
        result = lookup.lookup_mac_vendor(mac)
        print(f"\n📋 Result for {mac}:")
        print(f"   Vendor: {result['vendor']}")
        print(f"   Source: {result['source']}")
        print(f"   Success: {result['success']}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Single MAC lookup
        mac_address = sys.argv[1]
        lookup = CurlMacLookup()
        result = lookup.lookup_mac_vendor(mac_address)
        print(f"\n🎯 Final Result: {result['vendor']} (Source: {result['source']})")
    else:
        # Run main demo
        main()