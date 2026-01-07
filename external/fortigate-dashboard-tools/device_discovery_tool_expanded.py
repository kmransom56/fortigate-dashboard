import socket
import subprocess
import json
import csv
import pandas as pd
from typing import Dict, List, Optional, Tuple
import ipaddress
import concurrent.futures
from datetime import datetime
import re
import time
import paramiko
from netmiko import ConnectHandler
import os
import glob
from pathlib import Path


class CurlBasedMacLookup:
    """
    MAC address vendor lookup using curl instead of Python requests
    Since curl works in your environment despite Zscaler certificate interception
    """

    def __init__(self):
        self.cache = {}
        self.curl_available = self._test_curl_availability()

    def _test_curl_availability(self) -> bool:
        """Test if curl is available and working"""
        try:
            result = subprocess.run(['curl', '--version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            print(f"Curl availability test failed: {e}")
            return False

    def get_oui_from_mac(self, mac_address: str) -> str:
        """Extract OUI (first 6 characters) from MAC address"""
        clean_mac = mac_address.replace(':', '').replace('-', '').replace(' ', '').upper()
        return clean_mac[:6] if len(clean_mac) >= 6 else clean_mac

    def curl_api_lookup(self, mac_address: str) -> Optional[str]:
        """
        Use curl to lookup MAC vendor since curl works with Zscaler
        """
        if not self.curl_available:
            return None

        apis = [
            {'name': 'MacVendors.com', 'url': f"https://api.macvendors.com/{mac_address}", 'timeout': 8},
            {'name': 'MacVendors.co', 'url': f"https://macvendors.co/api/{mac_address}", 'timeout': 12}
        ]

        for api in apis:
            retries = 3
            delay = 1
            try:
                for attempt in range(retries):
                    print(f"🌐 Trying {api['name']} with curl (attempt {attempt + 1}/{retries})...")
                    curl_cmd = [
                        'curl', '-s', '-k', '--max-time', str(api['timeout']),
                        '--user-agent', 'Mozilla/5.0 (compatible; MAC-Lookup-Curl/1.0)',
                        api['url']
                    ]
                    result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=api['timeout'] + 2)
                    response = result.stdout.strip()
                    if result.returncode != 0:
                        raise subprocess.CalledProcessError(result.returncode, curl_cmd, output=result.stdout, stderr=result.stderr)

                    # Validate response
                    invalid_terms = ['not found', 'n/a', 'unknown', 'none', 'null', 'error', 'invalid']
                    if len(response) > 3 and not any(term in response.lower() for term in invalid_terms):
                        print(f"✅ Success from {api['name']}: {response}")
                        return response
                    if 'too many requests' in response.lower():
                        print(f"⚠️ {api['name']}: Rate limit hit. Retrying after {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                        continue
                    print(f"❌ {api['name']}: Invalid response: {response}")
                    break  # give up on this API
            except subprocess.TimeoutExpired:
                print(f"⏰ {api['name']}: Curl timeout after {api['timeout']}s")
                break
            except Exception as e:
                print(f"❌ {api['name']}: Curl error - {e}")
                break

            # Delay before next API if this one failed
            time.sleep(delay)
            delay *= 2

        return None


class FortiGateInterfaceParser:
    """
    Parse FortiGate interface files to extract management IP addresses
    """
    
    def __init__(self, interfaces_folder: str):
        self.interfaces_folder = Path(interfaces_folder)
        self.fortigate_info = {}
        
    def discover_fortigate_files(self) -> List[str]:
        """Find all FortiGate interface files in folder"""
        csv_files = list(self.interfaces_folder.glob("ARG0*_interfaces.csv"))
        json_files = list(self.interfaces_folder.glob("ARG0*_interfaces.json"))
        
        files = []
        for f in csv_files + json_files:
            files.append(str(f))
        
        print(f"📁 Found {len(files)} FortiGate interface files")
        return files
    
    def extract_fortigate_id(self, filename: str) -> str:
        """Extract FortiGate ID from filename (e.g., ARG0001 from ARG0001_interfaces.csv)"""
        match = re.search(r'(ARG0\d+)', Path(filename).name)
        return match.group(1) if match else "Unknown"
    
    def parse_csv_interface(self, csv_file: str) -> Dict[str, str]:
        """Parse CSV interface file to extract management IPs"""
        fortigate_id = self.extract_fortigate_id(csv_file)
        interfaces = {}
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) > 25:  # Ensure row has enough columns
                        interface_name = row[0]
                        # IP info is typically in the last columns as ['ip', 'netmask']
                        if len(row) > 26 and isinstance(row[-1], str):
                            # Parse IP info from last column that looks like ['10.213.181.1', '255.255.255.192']
                            ip_info = row[-1]
                            if ip_info and ip_info != "[]":
                                # Extract IP from string representation of list
                                ip_match = re.search(r"'(\d+\.\d+\.\d+\.\d+)'", ip_info)
                                if ip_match:
                                    ip = ip_match.group(1)
                                    # Check if this looks like a management interface
                                    if any(keyword in interface_name.lower() for keyword in ['lan', 'mgmt', 'management', 'vlan']):
                                        interfaces[interface_name] = ip
                                        print(f"  Found management IP: {interface_name} = {ip}")
        except Exception as e:
            print(f"❌ Error parsing {csv_file}: {e}")
        
        return interfaces
    
    def parse_json_interface(self, json_file: str) -> Dict[str, str]:
        """Parse JSON interface file to extract management IPs"""
        fortigate_id = self.extract_fortigate_id(json_file)
        interfaces = {}
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Navigate JSON structure to find interface data
            for interface_name, interface_data in data.items():
                if isinstance(interface_data, dict):
                    ip = interface_data.get('ip')
                    if ip and ip != '0.0.0.0':
                        # Check if this looks like a management interface
                        if any(keyword in interface_name.lower() for keyword in ['lan', 'mgmt', 'management', 'vlan']):
                            interfaces[interface_name] = ip
                            print(f"  Found management IP: {interface_name} = {ip}")
        except Exception as e:
            print(f"❌ Error parsing {json_file}: {e}")
        
        return interfaces
    
    def get_all_fortigate_ips(self) -> Dict[str, List[str]]:
        """Get all FortiGate management IPs organized by FortiGate ID"""
        files = self.discover_fortigate_files()
        all_fortigates = {}
        
        for file_path in files:
            fortigate_id = self.extract_fortigate_id(file_path)
            print(f"🔍 Parsing {fortigate_id}: {Path(file_path).name}")
            
            if file_path.endswith('.csv'):
                interfaces = self.parse_csv_interface(file_path)
            elif file_path.endswith('.json'):
                interfaces = self.parse_json_interface(file_path)
            else:
                continue
            
            if interfaces:
                all_fortigates[fortigate_id] = list(interfaces.values())
                print(f"  ✅ {fortigate_id}: Found {len(interfaces)} management IPs")
            else:
                print(f"  ⚠️ {fortigate_id}: No management IPs found")
        
        return all_fortigates
    
    def get_primary_management_ip(self, fortigate_id: str) -> Optional[str]:
        """Get the primary management IP for a specific FortiGate"""
        all_ips = self.get_all_fortigate_ips()
        if fortigate_id in all_ips and all_ips[fortigate_id]:
            return all_ips[fortigate_id][0]  # Return first management IP
        return None


class MultiFortiGateArpLookup:
    """
    Handle ARP lookups across multiple FortiGate devices
    """
    
    def __init__(self, interfaces_folder: str, username: str, password: str, port: int = 22):
        self.username = username
        self.password = password
        self.port = port
        self.parser = FortiGateInterfaceParser(interfaces_folder)
        self.fortigate_connections = {}
        self.combined_arp_cache = {}
        
    def discover_and_connect_fortigates(self) -> Dict[str, FortiGateArpLookup]:
        """Discover FortiGates and establish connections"""
        fortigate_ips = self.parser.get_all_fortigate_ips()
        connections = {}
        
        print(f"🔗 Attempting to connect to {len(fortigate_ips)} FortiGates...")
        
        for fortigate_id, ip_list in fortigate_ips.items():
            for ip in ip_list:
                print(f"  Trying {fortigate_id} at {ip}...")
                try:
                    arp_lookup = FortiGateArpLookup(ip, self.username, self.password, self.port)
                    if arp_lookup.connect():
                        connections[fortigate_id] = arp_lookup
                        print(f"  ✅ Connected to {fortigate_id} at {ip}")
                        break
                    else:
                        print(f"  ❌ Failed to connect to {fortigate_id} at {ip}")
                except Exception as e:
                    print(f"  ❌ Connection error to {fortigate_id} at {ip}: {e}")
        
        self.fortigate_connections = connections
        print(f"📡 Successfully connected to {len(connections)} FortiGates")
        return connections
    
    def get_combined_arp_table(self) -> Dict[str, Tuple[str, str]]:
        """
        Get ARP entries from all connected FortiGates
        Returns dict of {mac_address: (ip_address, fortigate_id)}
        """
        combined_arp = {}
        
        for fortigate_id, arp_lookup in self.fortigate_connections.items():
            print(f"📋 Getting ARP table from {fortigate_id}...")
            arp_table = arp_lookup.get_arp_table()
            
            for mac, ip in arp_table.items():
                if mac in combined_arp:
                    print(f"  ⚠️ Duplicate MAC {mac} found in {fortigate_id} and {combined_arp[mac][1]}")
                combined_arp[mac] = (ip, fortigate_id)
        
        self.combined_arp_cache = combined_arp
        print(f"📊 Combined ARP table: {len(combined_arp)} entries from {len(self.fortigate_connections)} FortiGates")
        return combined_arp
    
    def bulk_mac_to_ip_lookup(self, mac_addresses: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Lookup IPs for MACs across all FortiGates
        Returns dict of {mac: {'ip': ip, 'fortigate': fortigate_id}}
        """
        if not self.combined_arp_cache:
            self.get_combined_arp_table()
        
        results = {}
        found_count = 0
        
        for mac in mac_addresses:
            clean_mac = mac.upper().replace('-', ':')
            if clean_mac in self.combined_arp_cache:
                ip, fortigate_id = self.combined_arp_cache[clean_mac]
                results[mac] = {'ip': ip, 'fortigate': fortigate_id}
                found_count += 1
            else:
                results[mac] = {'ip': None, 'fortigate': None}
        
        print(f"🎯 Resolved {found_count}/{len(mac_addresses)} MAC addresses across all FortiGates")
        return results
    
    def disconnect_all(self):
        """Disconnect from all FortiGates"""
        for fortigate_id, arp_lookup in self.fortigate_connections.items():
            arp_lookup.disconnect()
            print(f"🔌 Disconnected from {fortigate_id}")


class FortiGateArpLookup:
    """
    Query FortiGate ARP table to get IP addresses from MAC addresses
    """
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.connection_params = {
            'device_type': 'fortinet',
            'host': host,
            'username': username,
            'password': password,
            'port': port,
            'timeout': 30
        }
        self.arp_cache = {}
        self.connection = None
        
    def connect(self) -> bool:
        """Establish connection to FortiGate"""
        try:
            self.connection = ConnectHandler(**self.connection_params)
            return True
        except Exception as e:
            print(f"❌ FortiGate connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close FortiGate connection"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
    
    def get_arp_table(self) -> Dict[str, str]:
        """
        Get complete ARP table from FortiGate
        Returns dict of {mac_address: ip_address}
        """
        if not self.connection and not self.connect():
            return {}
        
        try:
            # Execute FortiGate ARP command
            output = self.connection.send_command("get system arp")
            
            # Parse ARP table output
            arp_entries = {}
            for line in output.split('\n'):
                # FortiGate ARP format: Address          Age(min)   Hardware Addr     Interface
                match = re.match(r'(\d+\.\d+\.\d+\.\d+)\s+\d+\s+([0-9a-f:]{17})\s+\w+', line.strip(), re.IGNORECASE)
                if match:
                    ip = match.group(1)
                    mac = match.group(2).upper()
                    arp_entries[mac] = ip
            
            print(f"✅ Retrieved {len(arp_entries)} ARP entries from FortiGate")
            self.arp_cache.update(arp_entries)
            return arp_entries
            
        except Exception as e:
            print(f"❌ Failed to get ARP table: {e}")
            return {}
    
    def get_ip_from_mac(self, mac_address: str) -> Optional[str]:
        """
        Get IP address for a specific MAC address
        """
        clean_mac = mac_address.upper().replace('-', ':')
        
        # Check cache first
        if clean_mac in self.arp_cache:
            return self.arp_cache[clean_mac]
        
        # Refresh ARP table if not in cache
        arp_table = self.get_arp_table()
        return arp_table.get(clean_mac)
    
    def bulk_mac_to_ip_lookup(self, mac_addresses: List[str]) -> Dict[str, Optional[str]]:
        """
        Convert list of MAC addresses to IP addresses using ARP table
        """
        print(f"🔍 Looking up IP addresses for {len(mac_addresses)} MAC addresses...")
        
        # Get fresh ARP table
        arp_table = self.get_arp_table()
        
        results = {}
        found_count = 0
        
        for mac in mac_addresses:
            clean_mac = mac.upper().replace('-', ':')
            ip = arp_table.get(clean_mac)
            results[mac] = ip
            if ip:
                found_count += 1
        
        print(f"✅ Found IP addresses for {found_count}/{len(mac_addresses)} MAC addresses")
        return results


class DeviceDiscovery:
    def __init__(self, interfaces_folder: str = None, fortigate_username: str = None, 
                 fortigate_password: str = None, fortigate_host: str = None):
        # Enhanced OUI database with comprehensive vendor mappings
        self.oui_cache = {}
        self.load_comprehensive_oui_database()
        
        # Initialize curl-based lookup
        self.curl_lookup = CurlBasedMacLookup()
        
        # Initialize FortiGate ARP lookup
        self.fortigate_arp = None
        self.multi_fortigate_arp = None
        
        # Multi-FortiGate support via interface folder
        if interfaces_folder and fortigate_username and fortigate_password:
            self.multi_fortigate_arp = MultiFortiGateArpLookup(
                interfaces_folder, fortigate_username, fortigate_password
            )
            print(f"🔧 Multi-FortiGate ARP lookup configured for folder: {interfaces_folder}")
        
        # Single FortiGate support (legacy)
        elif fortigate_host and fortigate_username and fortigate_password:
            self.fortigate_arp = FortiGateArpLookup(fortigate_host, fortigate_username, fortigate_password)
            print(f"🔧 Single FortiGate ARP lookup configured for {fortigate_host}")
        
    def bulk_resolve_ips(self, mac_addresses: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Bulk resolve IP addresses from MAC addresses using FortiGate ARP tables
        """
        if self.multi_fortigate_arp:
            # Connect to all FortiGates and get combined ARP table
            self.multi_fortigate_arp.discover_and_connect_fortigates()
            return self.multi_fortigate_arp.bulk_mac_to_ip_lookup(mac_addresses)
        
        elif self.fortigate_arp:
            # Single FortiGate lookup (legacy)
            single_results = self.fortigate_arp.bulk_mac_to_ip_lookup(mac_addresses)
            # Convert to new format for consistency
            return {mac: {'ip': ip, 'fortigate': 'single'} for mac, ip in single_results.items()}
        
        return {mac: {'ip': None, 'fortigate': None} for mac in mac_addresses}
    
    def cleanup_connections(self):
        """Clean up all FortiGate connections"""
        if self.multi_fortigate_arp:
            self.multi_fortigate_arp.disconnect_all()
        elif self.fortigate_arp:
            self.fortigate_arp.disconnect()
    
    def enhanced_connectivity_test(self, ip_address: str) -> Dict[str, any]:
        """
        Enhanced connectivity testing with multiple methods
        """
        results = {
            'ip_address': ip_address,
            'ping_responsive': False,
            'response_time_ms': None,
            'hostname': 'Unknown',
            'reverse_dns_works': False
        }
        
        # Ping test with timing
        start_time = time.time()
        ping_success = self.ping_device(ip_address)
        response_time = (time.time() - start_time) * 1000
        
        results['ping_responsive'] = ping_success
        if ping_success:
            results['response_time_ms'] = round(response_time, 2)
        
        # Hostname resolution test
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            results['hostname'] = hostname
            results['reverse_dns_works'] = True
        except:
            results['hostname'] = 'Unknown'
            results['reverse_dns_works'] = False
        
        return results
        
    def load_comprehensive_oui_database(self):
        """
        Load comprehensive OUI database for offline MAC vendor lookup
        """
        # Comprehensive OUI database - expanded with common vendors
        self.oui_database = {
            # Network infrastructure (from actual discovery)
            '443839': 'Cumulus Networks, Inc.',  # From curl test result
            
            # Added specific vendor for the 18:66:DA MAC prefix that appears in the migration data
            '1866DA': 'Hangzhou Hikvision Digital Technology Co.,Ltd.',  # Added based on migration data
            
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
            
            # Security camera manufacturers
            '1866DA': 'Hangzhou Hikvision Digital Technology Co.,Ltd.',  # Added based on OUI lookup
            '28F366': 'Shenzhen Bilian Electronic Co.,Ltd',
            '485073': 'Xiaomi Communications Co Ltd',
            'C0A563': 'HUAWEI TECHNOLOGIES CO.,LTD',
            'C02506': 'AVM GmbH',
            '2C3033': 'NETGEAR',
            'B0C554': 'D-Link International',
            '0022CE': 'Cisco-Linksys, LLC',
            'E4AAEC': 'Tianjin Tianhai Special Equipment Co.,Ltd.',
        }
        
        print(f"Loaded {len(self.oui_database)} vendor mappings")
        
    def get_mac_vendor(self, mac_address: str) -> str:
        """
        Enhanced MAC vendor lookup with multiple fallback methods
        Now uses curl-based lookup which works with Zscaler
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
            
            # Method 3: Use curl-based lookup (works with Zscaler)
            vendor = self.curl_lookup.curl_api_lookup(mac_address)
            if vendor:
                self.oui_cache[oui] = vendor
                return vendor
            
            # Method 4: Pattern-based identification
            pattern_vendor = self._identify_by_pattern(oui, clean_mac)
            if pattern_vendor:
                self.oui_cache[oui] = pattern_vendor
                return pattern_vendor
            
            # Method 5: Default fallback
            self.oui_cache[oui] = "Unknown Vendor"
            return "Unknown Vendor"
            
        except Exception as e:
            print(f"Error in MAC vendor lookup for {mac_address}: {e}")
            return "Lookup Error"

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
        
        # Hikvision pattern - added for the specific 1866DA prefix
        elif oui.startswith('1866'):
            return "Hangzhou Hikvision Digital Technology Co.,Ltd."
            
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
        
        # Enhanced identification with Hikvision devices
        if '1866da' in device_info.get('mac_address', '').lower().replace(':', '').replace('-', ''):
            return "Hikvision IP Camera/NVR"
        
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
        elif 'hikvision' in vendor:
            return "Hikvision IP Camera/NVR"
        
        # Existing device type from FortiGate
        if device_type:
            return device_type.title()
        
        # Default handling for specific MAC OUIs
        if '1866da' in device_info.get('mac_address', '').lower().replace(':', '').replace('-', ''):
            return "Windows"  # Default as per migration risk data
        
        return "Unknown Device"
    
    def get_device_risk_level(self, device_info: Dict) -> str:
        """
        Assess risk level for migrating this device
        """
        device_type = device_info.get('identified_type', '').lower()
        open_ports = device_info.get('open_ports', [])
        responsive = device_info.get('responsive', False)
        vendor = device_info.get('vendor', '').lower()
        mac_address = device_info.get('mac_address', '').lower().replace(':', '').replace('-', '')
        
        # Specific handling for 1866DA devices based on migration data
        if mac_address.startswith('1866da'):
            if not responsive:
                return "LOW - Device Not Responsive"
        
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


def batch_mac_lookup(mac_addresses: List[str]) -> Dict[str, str]:
    """
    Perform efficient batch MAC lookup
    """
    discovery = DeviceDiscovery()
    results = {}
    
    print(f"Starting batch lookup of {len(mac_addresses)} MAC addresses...")
    
    # Group by OUI to avoid redundant lookups
    oui_groups = {}
    for mac in mac_addresses:
        if mac:
            oui = mac.replace(':', '').replace('-', '').upper()[:6]
            if oui not in oui_groups:
                oui_groups[oui] = []
            oui_groups[oui].append(mac)
    
    print(f"Found {len(oui_groups)} unique OUIs to process")
    
    # Process each OUI group
    for i, (oui, macs) in enumerate(oui_groups.items()):
        vendor = discovery.get_mac_vendor(macs[0])  # Use first MAC in group
        
        # Apply vendor to all MACs with this OUI
        for mac in macs:
            results[mac] = vendor
        
        # Progress indicator
        if (i + 1) % 10 == 0 or (i + 1) == len(oui_groups):
            print(f"Processed {i + 1}/{len(oui_groups)} OUIs ({len(results)}/{len(mac_addresses)} MACs)")
    
    return results


def analyze_port2_devices(port2_devices: List[Dict], interfaces_folder: str = None,
                         fortigate_username: str = None, fortigate_password: str = None,
                         fortigate_host: str = None) -> pd.DataFrame:
    """
    Comprehensive analysis with multi-FortiGate ARP integration
    """
    print("Starting comprehensive device discovery...")
    print("=" * 60)
    
    # Initialize discovery with FortiGate integration
    discovery = DeviceDiscovery(
        interfaces_folder=interfaces_folder,
        fortigate_username=fortigate_username,
        fortigate_password=fortigate_password,
        fortigate_host=fortigate_host
    )
    
    # Extract MAC addresses for bulk operations
    mac_addresses = [device.get('mac_address') for device in port2_devices if device.get('mac_address')]
    
    # Bulk MAC vendor lookup
    if mac_addresses:
        print(f"Analyzing {len(mac_addresses)} unique MAC addresses...")
        vendor_results = batch_mac_lookup(mac_addresses)
        print("MAC vendor analysis complete!")
    else:
        vendor_results = {}
    
    # Bulk IP resolution from FortiGate ARP tables
    ip_resolution_results = {}
    if mac_addresses:
        print("Resolving IP addresses from FortiGate ARP tables...")
        ip_resolution_results = discovery.bulk_resolve_ips(mac_addresses)
        print("IP resolution complete!")
    
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
        
        # Get IP address (from device data or FortiGate ARP lookup)
        ip_address = device.get('ip_address')
        
        # If no IP in device data, try FortiGate ARP lookup
        if (not ip_address or ip_address in ['None', 'Unknown', '']) and mac_address in ip_resolution_results:
            lookup_result = ip_resolution_results[mac_address]
            resolved_ip = lookup_result.get('ip')
            fortigate_source = lookup_result.get('fortigate')
            
            if resolved_ip:
                ip_address = resolved_ip
                enhanced_device['ip_address'] = ip_address
                enhanced_device['ip_source'] = f'FortiGate ARP ({fortigate_source})'
                print(f"  Resolved IP from {fortigate_source}: {ip_address}")
            else:
                enhanced_device['ip_source'] = 'Not found in ARP'
        else:
            enhanced_device['ip_source'] = 'Original data'
        
        # Enhanced network analysis if IP is available
        if ip_address and ip_address not in ['None', 'Unknown', '']:
            try:
                # Enhanced connectivity test
                connectivity_results = discovery.enhanced_connectivity_test(ip_address)
                enhanced_device.update(connectivity_results)
                
                responsive = connectivity_results['ping_responsive']
                enhanced_device['responsive'] = responsive
                print(f"  Responsive: {responsive}")
                
                if responsive:
                    response_time = connectivity_results.get('response_time_ms', 'N/A')
                    print(f"  Response time: {response_time}ms")
                    print(f"  Hostname: {connectivity_results['hostname']}")
                    
                    # Port scan
                    common_ports = [22, 80, 135, 443, 3389, 5985]
                    open_ports = discovery.scan_open_ports(ip_address, common_ports)
                    enhanced_device['open_ports'] = open_ports
                    print(f"  Open Ports: {open_ports}")
                else:
                    enhanced_device['open_ports'] = []
            except Exception as e:
                print(f"  Network analysis failed: {e}")
                enhanced_device['responsive'] = False
                enhanced_device['hostname'] = "Error"
                enhanced_device['open_ports'] = []
                enhanced_device['response_time_ms'] = None
        else:
            print(f"  No valid IP address ({ip_address})")
            enhanced_device['responsive'] = False
            enhanced_device['hostname'] = "No IP Address"
            enhanced_device['open_ports'] = []
            enhanced_device['response_time_ms'] = None
        
        # Device identification and risk assessment
        identified_type = discovery.identify_device_type(enhanced_device)
        enhanced_device['identified_type'] = identified_type
        print(f"  Identified Type: {identified_type}")
        
        risk_level = discovery.get_device_risk_level(enhanced_device)
        enhanced_device['migration_risk'] = risk_level
        print(f"  Migration Risk: {risk_level}")
        
        enhanced_devices.append(enhanced_device)
        
        if (i + 1) % 50 == 0:
            print(f"\n--- Processed {i + 1}/{len(port2_devices)} devices ---\n")
    
    # Clean up connections
    discovery.cleanup_connections()
    
    print("\nDevice analysis complete!")
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
    
    print(f"HIGH RISK DEVICES: {len(high_risk)}")
    print("- Schedule maintenance windows")
    print("- Test connectivity after migration")
    print("- Have rollback plan ready")
    print()
    
    print(f"MEDIUM RISK DEVICES: {len(medium_risk)}")
    print("- Monitor during migration")
    print("- Verify functionality post-migration")
    print()
    
    print(f"LOW RISK DEVICES: {len(low_risk)}")
    print("- Can be migrated in batches")
    print("- Minimal monitoring required")
    print()
    
    # Summary statistics
    print("\nSUMMARY STATISTICS:")
    print("-" * 30)
    print(f"Total devices: {len(df)}")
    print(f"Responsive devices: {len(df[df['responsive'] == True])}")
    print(f"Devices with open ports: {len(df[df['open_ports'].astype(str) != '[]'])}")
    
    # Vendor breakdown
    print("\nVENDOR BREAKDOWN:")
    print("-" * 20)
    vendor_counts = df['vendor'].value_counts()
    for vendor, count in vendor_counts.head(10).items():
        print(f"{vendor}: {count} devices")


def export_results(df: pd.DataFrame, filename: str = None) -> str:
    """
    Export analysis results to CSV
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"device_discovery_results_{timestamp}.csv"
    
    # Convert list columns to strings for CSV export
    df_export = df.copy()
    if 'open_ports' in df_export.columns:
        df_export['open_ports'] = df_export['open_ports'].astype(str)
    
    df_export.to_csv(filename, index=False)
    print(f"Results exported to: {filename}")
    return filename


# Example usage and main execution
if __name__ == "__main__":
    sample_devices = [
        {
            'mac_address': '18:66:DA:12:34:56',
            'switch_name': 'SW01',
            'port': 'port2',
            'device_type': 'Windows'
        },
        {
            'mac_address': '78:18:EC:AB:CD:EF',
            'switch_name': 'SW02', 
            'port': 'port2',
            'device_type': 'Unknown'
        }
    ]
    
    print("Device Discovery Tool - Multi-FortiGate Integration")
    print("=" * 60)
    
    # Method 1: Multi-FortiGate via interface files (RECOMMENDED)
    interfaces_folder = "./fortigate_interfaces"  # Folder with ARG0xxxx_interfaces.csv files
    fortigate_username = "admin"
    fortigate_password = "password"
    
    results_df = analyze_port2_devices(
        sample_devices,
        interfaces_folder=interfaces_folder,
        fortigate_username=fortigate_username,
        fortigate_password=fortigate_password
    )
    
    # Method 2: Single FortiGate (legacy)
    # results_df = analyze_port2_devices(
    #     sample_devices,
    #     fortigate_host="192.168.1.1",
    #     fortigate_username="admin",
    #     fortigate_password="password"
    # )
    
    create_migration_plan(results_df)
    export_filename = export_results(results_df)
    print(f"\nAnalysis complete! Results saved to: {export_filename}")


def demo_interface_discovery(interfaces_folder: str):
    """Demo function to show interface file parsing"""
    parser = FortiGateInterfaceParser(interfaces_folder)
    
    # Discover all FortiGate files
    files = parser.discover_fortigate_files()
    print(f"Found files: {files}")
    
    # Get all management IPs
    all_ips = parser.get_all_fortigate_ips()
    for fortigate_id, ips in all_ips.items():
        print(f"{fortigate_id}: {ips}")
    
    # Get primary IP for specific FortiGate
    primary_ip = parser.get_primary_management_ip("ARG0001")
    print(f"Primary IP for ARG0001: {primary_ip}")


def demo_multi_fortigate_arp(interfaces_folder: str, username: str, password: str):
    """Demo multi-FortiGate ARP lookup"""
    multi_arp = MultiFortiGateArpLookup(interfaces_folder, username, password)
    
    # Connect to all FortiGates
    connections = multi_arp.discover_and_connect_fortigates()
    print(f"Connected to {len(connections)} FortiGates")
    
    # Get combined ARP table
    combined_arp = multi_arp.get_combined_arp_table()
    print(f"Total ARP entries: {len(combined_arp)}")
    
    # Test MAC lookup
    test_macs = ["18:66:DA:12:34:56", "78:18:EC:AB:CD:EF"]
    results = multi_arp.bulk_mac_to_ip_lookup(test_macs)
    for mac, result in results.items():
        print(f"{mac}: {result}")
    
    # Cleanup
    multi_arp.disconnect_all()