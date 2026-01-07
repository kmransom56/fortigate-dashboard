import requests
import socket
import subprocess
import json
import csv
import pandas as pd
from typing import Dict, List, Optional
import ipaddress
import concurrent.futures
from datetime import datetime
import re
import time


class DeviceDiscovery:
    def __init__(self):
        # Enhanced OUI database with comprehensive vendor mappings
        self.oui_cache = {}
        self.load_comprehensive_oui_database()
        
    def load_comprehensive_oui_database(self):
        """
        Load comprehensive OUI database for offline MAC vendor lookup
        """
        # Comprehensive OUI database - expanded with common vendors
        self.oui_database = {
            # Network infrastructure (from actual discovery)
            '443839': 'Cumulus Networks, Inc.',  # From curl test result
            
            # Major computer manufacturers
            '000000': 'Xerox Corporation',
            '0050F2': 'Microsoft Corporation',
            '001122': 'Cimsys Inc.',
            '0003FF': 'Microsoft Corporation',
            '7818EC': 'Sony Corporation',  # Your example MAC
            '78CA39': 'Sony Corporation',
            '001B63': 'Apple Inc.',
            '001ED2': 'Apple Inc.',
            '001F5B': 'Apple Inc.',
            '0023DF': 'Apple Inc.',
            '002608': 'Apple Inc.',
            '0026BB': 'Apple Inc.',
            '28E02C': 'Apple Inc.',
            '3C0754': 'Apple Inc.',
            '40A6D9': 'Apple Inc.',
            '64B853': 'Apple Inc.',
            '68AB1E': 'Apple Inc.',
            '70CD60': 'Apple Inc.',
            '7CF05F': 'Apple Inc.',
            '84A134': 'Apple Inc.',
            '98B8E8': 'Apple Inc.',
            'A85C2C': 'Apple Inc.',
            'B065BD': 'Apple Inc.',
            'B418D1': 'Apple Inc.',
            'DC2B2A': 'Apple Inc.',
            'E0F847': 'Apple Inc.',
            'F0DBE2': 'Apple Inc.',
            
            # Dell computers
            '001E4F': 'Dell Inc.',
            '0026B9': 'Dell Inc.',
            '002564': 'Dell Inc.',
            '0025A5': 'Dell Inc.',
            'D4BED9': 'Dell Inc.',
            'F04DA2': 'Dell Inc.',
            '843497': 'Dell Inc.',
            
            # HP/HPE
            '001A4B': 'Hewlett Packard Enterprise',
            '002264': 'Hewlett Packard Enterprise',
            '0030C1': 'Hewlett Packard Enterprise',
            '009C02': 'Hewlett Packard Enterprise',
            '1C98EC': 'Hewlett Packard Enterprise',
            '3464A9': 'Hewlett Packard Enterprise',
            '70106F': 'Hewlett Packard Enterprise',
            
            # Lenovo/IBM
            '000476': 'IBM Corp.',
            '002655': 'IBM Corp.',
            '404E36': 'Lenovo',
            '8CFABA': 'Lenovo',
            'E41D2D': 'Lenovo',
            
            # Acer
            'C4D987': 'Acer Incorporated',
            '7427EA': 'Acer Incorporated',
            '0026C7': 'Acer Incorporated',
            '6CF049': 'Acer Incorporated',
            
            # ASUS
            '1C872C': 'ASUSTeK Computer Inc.',
            '2C56DC': 'ASUSTeK Computer Inc.',
            '60A44C': 'ASUSTeK Computer Inc.',
            
            # Network equipment
            '9C1E95': 'Actiontec Electronics Inc.',
            '941C56': 'Actiontec Electronics Inc.',
            '001B2F': 'Cisco Systems Inc.',
            '001C58': 'Cisco Systems Inc.',
            '00215A': 'Cisco Systems Inc.',
            '0024F7': 'Cisco Systems Inc.',
            '002618': 'Cisco Systems Inc.',
            '0040F4': 'Cisco Systems Inc.',
            '506B4B': 'Cisco Systems Inc.',
            '7C95F3': 'Cisco Systems Inc.',
            
            # TP-Link (very common)
            '00187D': 'TP-Link Technologies Co. Ltd.',
            '001A92': 'TP-Link Technologies Co. Ltd.',
            '002191': 'TP-Link Technologies Co. Ltd.',
            '0025BC': 'TP-Link Technologies Co. Ltd.',
            '50C7BF': 'TP-Link Technologies Co. Ltd.',
            '14CC20': 'TP-Link Technologies Co. Ltd.',
            '64F9A0': 'TP-Link Technologies Co. Ltd.',
            '8430C6': 'TP-Link Technologies Co. Ltd.',
            'D8C790': 'TP-Link Technologies Co. Ltd.',
            
            # D-Link
            '0007E9': 'D-Link Corporation',
            '001346': 'D-Link Corporation', 
            '001CF0': 'D-Link Corporation',
            '1CAFF7': 'D-Link Corporation',
            
            # Netgear
            '0022F0': 'Netgear Inc.',
            '002554': 'Netgear Inc.',
            '00606D': 'Netgear Inc.',
            '20E52A': 'Netgear Inc.',
            'A0040A': 'Netgear Inc.',
            
            # Linksys
            '000625': 'Linksys LLC',
            '000C41': 'Linksys LLC',
            '0013F7': 'Linksys LLC',
            '0014BF': 'Linksys LLC',
            '0016B6': 'Linksys LLC',
            
            # Fortinet devices
            '90F652': 'Fortinet Inc.',
            '0009DE': 'Fortinet Inc.',
            '00095E': 'Fortinet Inc.',
            
            # VMware virtual NICs
            '005056': 'VMware Inc.',
            '000C29': 'VMware Inc.',
            '001C14': 'VMware Inc.',
            
            # Intel NICs
            '001B21': 'Intel Corporation',
            '002129': 'Intel Corporation',
            '0025B3': 'Intel Corporation',
            '68B599': 'Intel Corporation',
            'A0369F': 'Intel Corporation',
            'D05099': 'Intel Corporation',
            
            # Realtek
            '525400': 'Realtek Semiconductor Corp.',
            'E0B655': 'Realtek Semiconductor Corp.',
            
            # Broadcom
            '002590': 'Broadcom Corporation',
            'E4F4C6': 'Broadcom Limited',
            
            # Microsoft (including Surface devices)
            '1C697A': 'Microsoft Corporation',
            'F4F951': 'Microsoft Corporation',
            '00127F': 'Microsoft Corporation',
            
            # Samsung
            '002566': 'Samsung Electronics Co. Ltd.',
            '0026E2': 'Samsung Electronics Co. Ltd.',
            '34E2FD': 'Samsung Electronics Co. Ltd.',
            '68A86D': 'Samsung Electronics Co. Ltd.',
            'E8039A': 'Samsung Electronics Co. Ltd.',
            
            # Generic/commonly seen
            'DC7FA4': 'Generic/Unknown Manufacturer',
            '14EDBB': 'Generic/Unknown Manufacturer',
            '000000': 'Invalid MAC Address',
            
            # IoT and embedded devices
            'B827EB': 'Raspberry Pi Foundation',
            'E45F01': 'Raspberry Pi Foundation',
            'DC4F22': 'Espressif Inc.',  # ESP32/ESP8266
            'CC50E3': 'Espressif Inc.',
            '5CCF7F': 'Espressif Inc.',
            
            # Printers
            '00025B': 'HP Inc.',
            '001B38': 'Canon Inc.',
            '002507': 'Canon Inc.',
            '3C2AF4': 'Brother Industries Ltd.',
            '008742': 'Epson Corporation',
            
            # Mobile devices common prefixes
            '02001E': 'Generic Mobile Device',
            '020011': 'Generic Mobile Device',
        }
        
        print(f"Loaded {len(self.oui_database)} vendor mappings")
        
    def get_mac_vendor(self, mac_address: str) -> str:
        """
        Enhanced MAC vendor lookup with multiple fallback methods
        """
        try:
            # Clean and extract OUI (first 3 bytes)
            clean_mac = mac_address.replace(':', '').replace('-', '').replace(' ', '').upper()
            if len(clean_mac) < 6:
                return "Invalid MAC Address"
            
            oui = clean_mac[:6]
            
            # Method 1: Check local comprehensive database first
            if oui in self.oui_database:
                vendor = self.oui_database[oui]
                self.oui_cache[oui] = vendor
                return vendor
            
            # Method 2: Check cache from previous lookups
            if oui in self.oui_cache:
                return self.oui_cache[oui]
            
            # Method 3: Try multiple online APIs with proper error handling
            vendor = self._lookup_oui_multiple_sources(oui, mac_address)
            if vendor and vendor != "Unknown":
                self.oui_cache[oui] = vendor
                return vendor
            
            # Method 4: Pattern-based identification for common formats
            vendor = self._identify_by_pattern(oui, clean_mac)
            if vendor:
                self.oui_cache[oui] = vendor
                return vendor
            
            # Method 5: Return formatted unknown with OUI for manual lookup
            return f"Unknown Vendor (OUI: {oui})"
            
        except Exception as e:
            return f"Lookup Error: {str(e)}"
    
    def _lookup_oui_multiple_sources(self, oui: str, full_mac: str) -> str:
        """
        Robust MAC vendor lookup with multiple APIs and improved error handling
        """
        # Format MAC address properly for different APIs
        mac_with_colons = ':'.join([full_mac[i:i+2] for i in range(0, 12, 2)])
        
        # Enhanced API configuration with variable timeouts and better headers
        apis = [
            {
                'name': 'MacVendors.com',
                'url': f"https://api.macvendors.com/{mac_with_colons}",
                'timeout': 5,
                'expected_format': 'text'
            },
            {
                'name': 'MacVendors.co',
                'url': f"https://macvendors.co/api/{mac_with_colons}",
                'timeout': 10,  # Longer timeout for slower API
                'expected_format': 'json'
            },
            {
                'name': 'MacVendorLookup.com',
                'url': f"https://www.macvendorlookup.com/api/v2/{oui}",
                'timeout': 8,
                'expected_format': 'json'
            },
            {
                'name': 'MacLookup.app',
                'url': f"https://api.maclookup.app/v2/macs/{mac_with_colons}",
                'timeout': 7,
                'expected_format': 'json'
            },
            {
                'name': 'HWAddress.com',
                'url': f"https://hwaddress.com/company/{oui}",
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
                    # Validate response has meaningful content
                    response_text = response.text.strip()
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

    def _identify_by_pattern(self, oui: str, full_mac: str) -> str:
        """
        Identify vendor by MAC address patterns and common ranges
        """
        # Virtual machine patterns
        if oui.startswith('000C29') or oui.startswith('005056'):
            return "VMware Virtual Machine"
        elif oui.startswith('080027'):
            return "VirtualBox Virtual Machine"
        elif oui.startswith('525400'):
            return "QEMU Virtual Machine"
        
        # Microsoft patterns
        elif oui.startswith('0050F2') or oui.startswith('1C697A'):
            return "Microsoft Corporation"
        
        # Apple patterns  
        elif oui in ['001B63', '001ED2', '001F5B', '0023DF', '002608', '0026BB']:
            return "Apple Inc."
        
        # Generic/local administration bit set
        elif int(oui[1], 16) & 2:  # Check if locally administered
            return "Locally Administered Address"
        
        return None

    def ping_device(self, ip_address: str, timeout: int = 2) -> bool:
        """
        Ping a device to check if it's responsive
        """
        try:
            if hasattr(subprocess, 'DEVNULL'):
                result = subprocess.run(['ping', '-n', '1', '-w', str(timeout*1000), ip_address], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                result = subprocess.run(['ping', '-n', '1', '-w', str(timeout*1000), ip_address], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except:
            return False
    
    def get_hostname(self, ip_address: str) -> str:
        """
        Try to resolve hostname from IP address
        """
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            return hostname
        except:
            return "Unknown"
    
    def scan_open_ports(self, ip_address: str, common_ports: List[int] = None) -> List[int]:
        """
        Scan for open ports on a device
        """
        if common_ports is None:
            common_ports = [22, 23, 53, 80, 135, 139, 443, 445, 993, 995, 3389, 5985, 8080]
        
        open_ports = []
        
        def check_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip_address, port))
                sock.close()
                if result == 0:
                    return port
            except:
                pass
            return None
        
        # Use threading for faster scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_port, port) for port in common_ports]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    open_ports.append(result)
        
        return sorted(open_ports)
    
    def identify_device_type(self, device_info: Dict) -> str:
        """
        Try to identify device type based on available information
        """
        open_ports = device_info.get('open_ports', [])
        vendor = device_info.get('vendor', '').lower()
        hostname = device_info.get('hostname', '').lower()
        device_type = device_info.get('device_type', '').lower()
        
        # Port-based identification
        if 3389 in open_ports or 5985 in open_ports:
            return "Windows Computer/Server"
        elif 22 in open_ports and 80 in open_ports:
            return "Linux Server/Appliance"
        elif 22 in open_ports:
            return "Linux/Unix Device"
        elif 23 in open_ports:
            return "Network Device (Telnet)"
        elif 80 in open_ports or 443 in open_ports:
            return "Web Server/Appliance"
        
        # Vendor-based identification
        if 'cisco' in vendor or 'cisco' in hostname:
            return "Cisco Network Device"
        elif 'hp' in vendor or 'hewlett' in vendor:
            return "HP Device"
        elif 'dell' in vendor or 'dell' in hostname:
            return "Dell Computer"
        elif 'acer' in vendor:
            return "Acer Computer"
        elif 'actiontec' in vendor:
            return "Actiontec Router/Modem"
        elif 'microsoft' in vendor:
            return "Microsoft Device"
        elif 'sony' in vendor:
            return "Sony Device/Media Equipment"
        elif 'apple' in vendor:
            return "Apple Device"
        elif 'lenovo' in vendor or 'ibm' in vendor:
            return "Lenovo/IBM Computer"
        elif 'vmware' in vendor or 'virtual' in vendor:
            return "Virtual Machine"
        elif 'fortinet' in vendor:
            return "Fortinet Network Device"
        elif 'intel' in vendor:
            return "Intel Network Adapter"
        elif 'realtek' in vendor or 'broadcom' in vendor:
            return "Network Interface Device"
        
        # Existing device type from FortiGate
        if device_type:
            return device_type.title()
        
        return "Unknown Device"
    
    def get_device_risk_level(self, device_info: Dict) -> str:
        """
        Assess risk level for migrating this device
        """
        device_type = device_info.get('identified_type', '').lower()
        open_ports = device_info.get('open_ports', [])
        responsive = device_info.get('responsive', False)
        vendor = device_info.get('vendor', '').lower()
        
        # High risk devices
        if any(keyword in device_type for keyword in ['server', 'router', 'switch', 'firewall']):
            return "HIGH - Critical Infrastructure"
        elif any(keyword in vendor for keyword in ['cisco', 'fortinet', 'hp enterprise']):
            return "HIGH - Network Infrastructure"
        elif 3389 in open_ports or 22 in open_ports:
            return "MEDIUM - Administrative Access"
        elif responsive and open_ports:
            return "MEDIUM - Active Device"
        elif not responsive:
            return "LOW - Device Not Responsive"
        else:
            return "LOW - Standard Device"


def diagnose_mac_lookup_apis(mac_address: str = "00:18:7d:19:36:ce"):
    """
    Diagnostic tool to test all MAC lookup APIs and show detailed results
    """
    print(f"DIAGNOSING MAC LOOKUP APIs FOR: {mac_address}")
    print("=" * 60)
    
    # Prepare different formats
    clean_mac = mac_address.replace(':', '').replace('-', '').replace(' ', '').upper()
    oui = clean_mac[:6]
    mac_with_colons = ':'.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
    mac_with_dashes = '-'.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
    oui_with_colons = ':'.join([oui[i:i+2] for i in range(0, 6, 2)])
    
    print(f"Clean MAC: {clean_mac}")
    print(f"OUI: {oui}")
    print(f"MAC with colons: {mac_with_colons}")
    print(f"MAC with dashes: {mac_with_dashes}")
    print(f"OUI with colons: {oui_with_colons}")
    print()
    
    # Test each API individually
    test_apis = [
        {
            'name': 'MacVendors.com',
            'url': f"https://api.macvendors.com/{mac_with_colons}",
            'expected_format': 'text',
            'description': 'Popular free API, rate limited'
        },
        {
            'name': 'MacVendors.co', 
            'url': f"https://macvendors.co/api/{mac_with_colons}",
            'expected_format': 'json',
            'description': 'Alternative API with JSON response'
        },
        {
            'name': 'MacVendorLookup.com',
            'url': f"https://www.macvendorlookup.com/api/v2/{oui}",
            'expected_format': 'json',
            'description': 'OUI-based lookup'
        },
        {
            'name': 'MacLookup.app',
            'url': f"https://api.maclookup.app/v2/macs/{mac_with_colons}",
            'expected_format': 'json',
            'description': 'Newer API service'
        },
        {
            'name': 'IEEE OUI Registry (alternative)',
            'url': f"https://standards-oui.ieee.org/oui/oui.txt",
            'expected_format': 'text',
            'description': 'Official IEEE registry (large file)'
        }
    ]
    
    for api in test_apis:
        print(f"Testing: {api['name']}")
        print(f"URL: {api['url']}")
        print(f"Description: {api['description']}")
        
        try:
            start_time = time.time()
            
            response = requests.get(
                api['url'],
                timeout=10,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            )
            
            response_time = time.time() - start_time
            
            print(f"  ✓ HTTP Status: {response.status_code}")
            print(f"  ✓ Response Time: {response_time:.2f}s")
            print(f"  ✓ Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"  ✓ Content Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                if api['expected_format'] == 'json':
                    try:
                        json_data = response.json()
                        print(f"  ✓ JSON Response: {json.dumps(json_data, indent=2)[:200]}...")
                        
                        # Try to extract vendor
                        if isinstance(json_data, dict):
                            vendor = json_data.get('company', json_data.get('vendor', json_data.get('organization', 'Not found')))
                        elif isinstance(json_data, list) and len(json_data) > 0:
                            vendor = json_data[0].get('company', 'Not found')
                        else:
                            vendor = 'Unknown format'
                        
                        print(f"  ✓ Extracted Vendor: {vendor}")
                        
                    except json.JSONDecodeError as e:
                        print(f"  ✗ JSON Parse Error: {e}")
                        print(f"  ✗ Raw Response: {response.text[:200]}...")
                else:
                    response_text = response.text.strip()
                    if 'oui.txt' in api['url']:
                        # Special handling for IEEE registry
                        if oui in response_text:
                            lines = response_text.split('\n')
                            for line in lines:
                                if oui in line:
                                    print(f"  ✓ Found in IEEE registry: {line}")
                                    break
                        else:
                            print(f"  ✗ OUI {oui} not found in IEEE registry")
                    else:
                        print(f"  ✓ Text Response: {response_text}")
            
            elif response.status_code == 429:
                print(f"  ⚠ Rate Limited - try again later")
                print(f"  ⚠ Headers: {dict(response.headers)}")
            else:
                print(f"  ✗ Error Response: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            print(f"  ✗ Request Timeout (>10s)")
        except requests.exceptions.ConnectionError:
            print(f"  ✗ Connection Error - API may be down")
        except Exception as e:
            print(f"  ✗ Unexpected Error: {e}")
        
        print("-" * 40)
    
    print("\n💡 TROUBLESHOOTING TIPS:")
    print("1. Rate Limiting: Many free APIs limit requests (try different APIs)")
    print("2. Format Issues: Some APIs need colons (:), others need dashes (-)")
    print("3. User-Agent: Some APIs block automated requests")
    print("4. Network: Check if your network blocks these API domains")
    print("5. Offline Mode: Use local database for better reliability")


def test_mac_formats(mac_address: str):
    """
    Test different MAC address formats with a simple API
    """
    print(f"TESTING MAC FORMATS FOR: {mac_address}")
    print("=" * 50)
    
    clean_mac = mac_address.replace(':', '').replace('-', '').replace(' ', '').upper()
    
    formats = [
        clean_mac,  # 00187D1936CE
        ':'.join([clean_mac[i:i+2] for i in range(0, 12, 2)]),  # 00:18:7D:19:36:CE
        '-'.join([clean_mac[i:i+2] for i in range(0, 12, 2)]),  # 00-18-7D-19-36-CE
        '.'.join([clean_mac[i:i+4] for i in range(0, 12, 4)]),  # 0018.7D19.36CE
        clean_mac[:6],  # 00187D (OUI only)
        ':'.join([clean_mac[i:i+2] for i in range(0, 6, 2)])  # 00:18:7D (OUI with colons)
    ]
    
    for fmt in formats:
        print(f"Testing format: {fmt}")
        try:
            response = requests.get(
                f"https://api.macvendors.com/{fmt}",
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            if response.status_code == 200:
                print(f"  ✓ SUCCESS: {response.text.strip()}")
            else:
                print(f"  ✗ HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
        
        time.sleep(1)  # Rate limiting delay
        print()  # Add spacing between tests


def analyze_mac_patterns_in_dataset(port2_devices: List[Dict]) -> pd.DataFrame:
    """
    Analyze MAC address patterns in your actual dataset to build custom vendor mappings
    """
    print("Analyzing MAC address patterns in your dataset...")
    print("=" * 60)
    
    discovery = DeviceDiscovery()
    mac_analysis = []
    
    # Extract unique OUIs from your data
    ouis_found = {}
    
    for device in port2_devices:
        mac_address = device.get('mac_address')
        if mac_address:
            oui = mac_address.replace(':', '').replace('-', '').upper()[:6]
            
            if oui not in ouis_found:
                vendor = discovery.get_mac_vendor(mac_address)
                ouis_found[oui] = {
                    'oui': oui,
                    'example_mac': mac_address,
                    'vendor': vendor,
                    'count': 1,
                    'device_types': set()
                }
            else:
                ouis_found[oui]['count'] += 1
            
            # Track device types for this OUI
            device_type = device.get('device_type', 'Unknown')
            ouis_found[oui]['device_types'].add(device_type)
    
    # Convert to list and sort by count
    mac_analysis = list(ouis_found.values())
    mac_analysis.sort(key=lambda x: x['count'], reverse=True)
    
    print(f"Found {len(mac_analysis)} unique OUIs in your dataset:")
    print("-" * 60)
    
    for i, oui_info in enumerate(mac_analysis[:20]):  # Show top 20
        device_types = ', '.join(oui_info['device_types'])
        print(f"{i+1:2d}. OUI: {oui_info['oui']} | Count: {oui_info['count']:3d} | {oui_info['vendor']}")
        print(f"    Example MAC: {oui_info['example_mac']} | Device Types: {device_types}")
        print()
    
    # Create custom vendor mapping for your environment
    create_custom_vendor_mapping(mac_analysis)
    
    return pd.DataFrame(mac_analysis)


def create_custom_vendor_mapping(mac_analysis: List[Dict]):
    """
    Create a custom vendor mapping file based on your network's actual devices
    """
    custom_mapping = {}
    unknown_ouis = []
    
    for oui_info in mac_analysis:
        vendor = oui_info['vendor']
        oui = oui_info['oui']
        
        if 'Unknown' in vendor or 'Generic' in vendor:
            unknown_ouis.append(oui_info)
        else:
            custom_mapping[oui] = vendor
    
    # Save custom mapping
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save identified vendors
    with open(f'custom_vendor_mapping_{timestamp}.py', 'w') as f:
        f.write("# Custom OUI mapping generated from your FortiGate data\n")
        f.write("# Add this to your DeviceDiscovery class oui_database\n\n")
        f.write("custom_oui_database = {\n")
        for oui, vendor in sorted(custom_mapping.items()):
            f.write(f"    '{oui}': '{vendor}',\n")
        f.write("}\n")
    
    # Save unknown OUIs for manual research
    with open(f'unknown_ouis_{timestamp}.csv', 'w') as f:
        f.write("OUI,Example_MAC,Count,Device_Types,Manual_Lookup_URL\n")
        for oui_info in unknown_ouis:
            device_types = '|'.join(oui_info['device_types'])
            lookup_url = f"https://maclookup.app/macaddress/{oui_info['oui']}"
            f.write(f"{oui_info['oui']},{oui_info['example_mac']},{oui_info['count']},\"{device_types}\",{lookup_url}\n")
    
    print(f"\nCustom vendor mapping saved to: custom_vendor_mapping_{timestamp}.py")
    print(f"Unknown OUIs for research saved to: unknown_ouis_{timestamp}.csv")
    print(f"\nFound {len(custom_mapping)} identified vendors and {len(unknown_ouis)} unknown OUIs")
    
    if unknown_ouis:
        print("\nTop unknown OUIs to research manually:")
        for oui_info in sorted(unknown_ouis, key=lambda x: x['count'], reverse=True)[:10]:
            print(f"  {oui_info['oui']} ({oui_info['count']} devices) - {oui_info['example_mac']}")
            print(f"    Lookup: https://maclookup.app/macaddress/{oui_info['oui']}")


def bulk_mac_lookup(mac_addresses: List[str]) -> Dict[str, str]:
    """
    Perform bulk MAC address lookup for better efficiency
    """
    discovery = DeviceDiscovery()
    results = {}
    
    print(f"Performing bulk lookup for {len(mac_addresses)} MAC addresses...")
    
    # Group by OUI to avoid duplicate lookups
    oui_groups = {}
    for mac in mac_addresses:
        if mac:
            oui = mac.replace(':', '').replace('-', '').upper()[:6]
            if oui not in oui_groups:
                oui_groups[oui] = []
            oui_groups[oui].append(mac)
    
    print(f"Found {len(oui_groups)} unique OUIs to lookup...")
    
    # Lookup each OUI once
    for i, (oui, macs) in enumerate(oui_groups.items()):
        vendor = discovery.get_mac_vendor(macs[0])  # Use first MAC as example
        
        # Apply to all MACs with this OUI
        for mac in macs:
            results[mac] = vendor
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(oui_groups)} OUIs...")
    
    return results


def analyze_port2_devices(port2_devices: List[Dict]) -> pd.DataFrame:
    """
    Perform comprehensive analysis of port 2 devices with improved MAC lookup
    """
    print("Starting comprehensive device discovery...")
    print("=" * 60)
    
    # First, do bulk MAC analysis for efficiency
    mac_addresses = [device.get('mac_address') for device in port2_devices if device.get('mac_address')]
    
    if mac_addresses:
        print(f"Analyzing {len(mac_addresses)} unique MAC addresses...")
        vendor_results = bulk_mac_lookup(mac_addresses)
        print("MAC vendor analysis complete!")
    else:
        vendor_results = {}
    
    discovery = DeviceDiscovery()
    enhanced_devices = []
    
    print(f"\nAnalyzing {len(port2_devices)} devices individually...")
    print("-" * 40)
    
    for i, device in enumerate(port2_devices):
        mac_address = device.get('mac_address', 'Unknown')
        print(f"Analyzing device {i+1}/{len(port2_devices)}: {mac_address}")
        
        enhanced_device = device.copy()
        
        # Use pre-calculated vendor lookup
        if mac_address in vendor_results:
            vendor = vendor_results[mac_address]
            enhanced_device['vendor'] = vendor
            print(f"  Vendor: {vendor}")
        else:
            enhanced_device['vendor'] = "No MAC Address"
        
        # Network analysis if IP is available
        ip_address = device.get('ip_address')
        if ip_address and ip_address not in ['None', 'Unknown', '']:
            try:
                # Ping test
                responsive = discovery.ping_device(ip_address)
                enhanced_device['responsive'] = responsive
                print(f"  Responsive: {responsive}")
                
                if responsive:
                    # Hostname lookup
                    hostname = discovery.get_hostname(ip_address)
                    enhanced_device['hostname'] = hostname
                    print(f"  Hostname: {hostname}")
                    
                    # Port scan (reduced set for faster execution)
                    common_ports = [22, 80, 135, 443, 3389, 5985]  # Reduced for speed
                    open_ports = discovery.scan_open_ports(ip_address, common_ports)
                    enhanced_device['open_ports'] = open_ports
                    print(f"  Open Ports: {open_ports}")
                else:
                    enhanced_device['hostname'] = "Not Responsive"
                    enhanced_device['open_ports'] = []
            except Exception as e:
                print(f"  Network analysis failed: {e}")
                enhanced_device['responsive'] = False
                enhanced_device['hostname'] = "Error"
                enhanced_device['open_ports'] = []
        else:
            print(f"  No valid IP address ({ip_address})")
            enhanced_device['responsive'] = False
            enhanced_device['hostname'] = "No IP Address"
            enhanced_device['open_ports'] = []
        
        # Device identification
        identified_type = discovery.identify_device_type(enhanced_device)
        enhanced_device['identified_type'] = identified_type
        print(f"  Identified Type: {identified_type}")
        
        # Risk assessment
        risk_level = discovery.get_device_risk_level(enhanced_device)
        enhanced_device['migration_risk'] = risk_level
        print(f"  Migration Risk: {risk_level}")
        
        enhanced_devices.append(enhanced_device)
        
        # Progress indicator for large datasets
        if (i + 1) % 50 == 0:
            print(f"\n--- Processed {i + 1}/{len(port2_devices)} devices ---\n")
    
    print("\nDevice analysis complete!")
    
    # Analyze MAC patterns in your dataset
    print("\nAnalyzing MAC address patterns...")
    analyze_mac_patterns_in_dataset(port2_devices)
    
    return pd.DataFrame(enhanced_devices)


def create_migration_plan(df: pd.DataFrame) -> None:
    """
    Create a migration plan for port 2 devices
    """
    print("\nMIGRATION PLAN FOR PORT 2 → V118_ISOM CONVERSION")
    print("=" * 70)
    
    # Group by risk level
    risk_groups = df.groupby('migration_risk')
    
    for risk_level, group in risk_groups:
        print(f"\n{risk_level} DEVICES ({len(group)} devices):")
        print("-" * 50)
        
        for _, device in group.iterrows():
            print(f"MAC: {device.get('mac_address', 'Unknown')}")
            print(f"  IP: {device.get('ip_address', 'Unknown')}")
            print(f"  Type: {device.get('identified_type', 'Unknown')}")
            print(f"  Switch: {device.get('switch_name', 'Unknown')}")
            print(f"  Vendor: {device.get('vendor', 'Unknown')}")
            if device.get('hostname') != 'Unknown':
                print(f"  Hostname: {device.get('hostname')}")
            print()
    
    # Migration recommendations
    print("\nMIGRATION RECOMMENDATIONS:")
    print("=" * 40)
    
    high_risk = df[df['migration_risk'].str.contains('HIGH', na=False)]
    medium_risk = df[df['migration_risk'].str.contains('MEDIUM', na=False)]
    low_risk = df[df['migration_risk'].str.contains('LOW', na=False)]
    
    print(f"1. HIGH RISK ({len(high_risk)} devices): Schedule maintenance window")
    print(f"2. MEDIUM RISK ({len(medium_risk)} devices): Coordinate with users")
    print(f"3. LOW RISK ({len(low_risk)} devices): Can migrate during business hours")
    
    # Port suggestions
    print(f"\nSUGGESTED ALTERNATIVE PORTS:")
    print("- General devices: port3, port4, port5")
    print("- Servers/Critical: port1 (if available)")
    print("- IoT/Sensors: port6-8")
    print("- Printers: port9-12")


def save_migration_report(df: pd.DataFrame) -> None:
    """
    Save detailed migration report
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"port2_migration_plan_{timestamp}.csv"
    
    # Select relevant columns for the report
    report_columns = [
        'mac_address', 'ip_address', 'device_name', 'identified_type', 
        'vendor', 'hostname', 'switch_name', 'responsive', 'open_ports',
        'migration_risk'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in report_columns if col in df.columns]
    report_df = df[available_columns]
    
    report_df.to_csv(filename, index=False)
    print(f"\nDetailed migration report saved to: {filename}")
    
    # Create summary report
    summary_filename = f"port2_migration_summary_{timestamp}.txt"
    with open(summary_filename, 'w') as f:
        f.write("PORT 2 MIGRATION SUMMARY\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Total devices on port 2: {len(df)}\n")
        f.write(f"Responsive devices: {len(df[df['responsive'] == True])}\n")
        f.write(f"High risk devices: {len(df[df['migration_risk'].str.contains('HIGH', na=False)])}\n")
        f.write(f"Medium risk devices: {len(df[df['migration_risk'].str.contains('MEDIUM', na=False)])}\n")
        f.write(f"Low risk devices: {len(df[df['migration_risk'].str.contains('LOW', na=False)])}\n\n")
        
        # Add vendor breakdown
        f.write("VENDOR BREAKDOWN:\n")
        vendor_counts = df['vendor'].value_counts()
        for vendor, count in vendor_counts.items():
            f.write(f"  {vendor}: {count}\n")
    
    print(f"Migration summary saved to: {summary_filename}")


def main():
    """
    Main function to run device discovery and migration planning
    """
    # First, run the original script to get port 2 devices
    print("Make sure you've run the fortinet parser first to get port2 devices!")
    print("This script expects a 'port2_devices_report.csv' file to exist.")
    print()
    
    try:
        # Try to load existing port 2 devices
        df_port2 = pd.read_csv('port2_devices_report.csv')
        print(f"Loaded {len(df_port2)} port 2 devices from previous analysis")
        
        # Convert to list of dictionaries for processing
        port2_devices = df_port2.to_dict('records')
        
        # Perform comprehensive analysis
        enhanced_df = analyze_port2_devices(port2_devices)
        
        # Create migration plan
        create_migration_plan(enhanced_df)
        
        # Save reports
        save_migration_report(enhanced_df)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\nAnalysis complete! Check the generated files:")
        print("=" * 50)
        print("📁 OUTPUT FILES CREATED:")
        print(f"  📊 Detailed Report: port2_migration_plan_{timestamp}.csv")
        print(f"  📋 Summary Report: port2_migration_summary_{timestamp}.txt") 
        print(f"  🏷️  Vendor Mappings: custom_vendor_mapping_{timestamp}.py")
        print(f"  ❓ Unknown OUIs: unknown_ouis_{timestamp}.csv")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Review the migration plan CSV for device details")
        print("2. Check unknown OUIs and add custom mappings if needed")
        
    except FileNotFoundError:
        print("Error: 'port2_devices_report.csv' not found!")
        print("Please run the fortinet parser script first to generate port 2 device list.")
    except Exception as e:
        print(f"Error during analysis: {e}")


def show_output_files():
    """
    Show all output files created by the device discovery tool
    """
    import glob
    import os
    
    print("DEVICE DISCOVERY OUTPUT FILES")
    print("=" * 60)
    
    file_patterns = [
        ("📊 Migration Plans", "port2_migration_plan_*.csv"),
        ("📋 Summary Reports", "port2_migration_summary_*.txt"),
        ("🏷️  Vendor Mappings", "custom_vendor_mapping_*.py"),
        ("❓ Unknown OUIs", "unknown_ouis_*.csv"),
        ("📈 MAC Analysis", "mac_analysis_*.csv"),
        ("📝 Migration Logs", "*migration_log_*.txt")
    ]
    
    for file_type, pattern in file_patterns:
        files = glob.glob(pattern)
        if files:
            print(f"\n{file_type}:")
            for file in sorted(files, reverse=True):  # Most recent first
                size = os.path.getsize(file)
                mtime = os.path.getmtime(file)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  📄 {file} ({size:,} bytes, {date_str})")
        else:
            print(f"\n{file_type}: No files found")
    
    print("\n" + "=" * 60)


def explain_output_files():
    """
    Explain what each output file contains
    """
    explanations = {
        "port2_migration_plan_*.csv": {
            "description": "Complete device migration plan with risk assessment",
            "contains": [
                "MAC addresses and IP addresses",
                "Device vendors and types", 
                "Network responsiveness data",
                "Open ports and services",
                "Migration risk levels",
                "Switch and port information"
            ],
            "use_for": "Main input for FortiManager API and jumpbox automation"
        },
        "port2_migration_summary_*.txt": {
            "description": "High-level summary of migration analysis",
            "contains": [
                "Total device counts",
                "Risk level breakdown", 
                "Vendor distribution",
                "Responsiveness statistics"
            ],
            "use_for": "Quick overview and reporting to management"
        },
        "custom_vendor_mapping_*.py": {
            "description": "Vendor mappings discovered in your network",
            "contains": [
                "OUI to vendor name mappings",
                "Python dictionary format",
                "Ready to import into scripts"
            ],
            "use_for": "Improving vendor detection for future runs"
        },
        "unknown_ouis_*.csv": {
            "description": "Unknown OUIs that need manual research",
            "contains": [
                "Unidentified OUI codes",
                "Device counts per OUI",
                "Research links for manual lookup"
            ],
            "use_for": "Manual vendor identification and database improvement"
        }
    }
    
    print("OUTPUT FILE EXPLANATIONS")
    print("=" * 60)
    
    for pattern, info in explanations.items():
        print(f"\n📄 {pattern}")
        print(f"   Description: {info['description']}")
        print(f"   Contains:")
        for item in info['contains']:
            print(f"     • {item}")
        print(f"   Use for: {info['use_for']}")
    
    print("\n" + "=" * 60)


def quick_mac_lookup(mac_address: str):
    """
    Quick lookup tool for individual MAC addresses
    """
    discovery = DeviceDiscovery()
    
    print(f"Looking up MAC address: {mac_address}")
    print("=" * 50)
    
    # Clean MAC
    clean_mac = mac_address.replace(':', '').replace('-', '').replace(' ', '').upper()
    oui = clean_mac[:6]
    
    print(f"OUI: {oui}")
    
    # Try multiple lookup methods
    print("\nTrying lookup methods:")
    
    # Method 1: Local database
    if oui in discovery.oui_database:
        print(f"✓ Local database: {discovery.oui_database[oui]}")
    else:
        print("✗ Not found in local database")
    
    # Method 2: Online lookup
    vendor = discovery._lookup_oui_multiple_sources(oui, mac_address)
    if vendor:
        print(f"✓ Online lookup: {vendor}")
    else:
        print("✗ Online lookup failed")
    
    # Method 3: Pattern recognition
    pattern_vendor = discovery._identify_by_pattern(oui, clean_mac)
    if pattern_vendor:
        print(f"✓ Pattern recognition: {pattern_vendor}")
    else:
        print("✗ No pattern match")
    
    # Final result
    final_vendor = discovery.get_mac_vendor(mac_address)
    print(f"\nFinal result: {final_vendor}")
    
    # Provide research links
    print(f"\nManual research links:")
    print(f"  • https://maclookup.app/macaddress/{oui}")
    print(f"  • https://www.wireshark.org/tools/oui-lookup.html")
    print(f"  • https://hwaddress.com/?q={oui}")


def update_custom_vendor_database(oui: str, vendor_name: str):
    """
    Add custom vendor mapping to local database
    """
    config_file = "custom_vendor_additions.py"
    
    # Create or append to custom config
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(config_file, "a") as f:
        f.write(f"# Added on {timestamp}\n")
        f.write(f"'{oui.upper()}': '{vendor_name}',\n")
    
    print(f"Added {oui} -> {vendor_name} to {config_file}")
    print("Restart the script to use the new mapping.")


if __name__ == "__main__":
    import sys
    
    # Add command line options for MAC lookup
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "lookup" and len(sys.argv) > 2:
            mac_address = sys.argv[2]
            quick_mac_lookup(mac_address)
        elif command == "show-files":
            show_output_files()
            sys.exit(0)
        elif command == "diagnose" and len(sys.argv) > 2:
            mac_address = sys.argv[2]
            diagnose_mac_lookup_apis(mac_address)
            sys.exit(0)
        elif command == "test-formats" and len(sys.argv) > 2:
            mac_address = sys.argv[2]
            test_mac_formats(mac_address)
            sys.exit(0)
        elif command == "diagnose":
            diagnose_mac_lookup_apis()  # Use default MAC
            sys.exit(0)
        elif command == "explain-files":
            explain_output_files() 
            sys.exit(0)
        elif command == "add" and len(sys.argv) > 3:
            oui = sys.argv[2]
            vendor = sys.argv[3]
            update_custom_vendor_database(oui, vendor)
            sys.exit(0)
        elif command == "help":
            print("Usage:")
            print(f"  {sys.argv[0]} lookup <mac_address>       # Lookup specific MAC")
            print(f"  {sys.argv[0]} add <oui> <vendor>         # Add custom vendor")
            print(f"  {sys.argv[0]} diagnose [mac_address]     # Diagnose API issues")
            print(f"  {sys.argv[0]} test-formats <mac_address> # Test MAC format variations")
            print(f"  {sys.argv[0]} show-files                 # Show all output files")
            print(f"  {sys.argv[0]} explain-files              # Explain what each file contains")
            print(f"  {sys.argv[0]}                            # Run full analysis")
            print()
            print("Examples:")
            print(f"  {sys.argv[0]} lookup 00:18:7d:19:36:ce")
            print(f"  {sys.argv[0]} diagnose 00:18:7d:19:36:ce")
            print(f"  {sys.argv[0]} add 00187D 'TP-Link Technologies'")
            sys.exit(0)
    
    # Default behavior - run main analysis
    main()