"""
FortiSwitch Manager Module

This module provides functionality to manage FortiSwitch devices connected to a FortiGate firewall
through the FortiOS API.
"""
import requests
import urllib3
import logging
from typing import Dict, Any, Optional, List, Union

# Set up logging
logger = logging.getLogger(__name__)

# Disable SSL warnings for development environments
# In production, you should properly handle certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FortiSwitchManager:
    """
    A class to manage FortiSwitch devices connected to a FortiGate firewall.
    """
    
    def __init__(self, fortigate_ip: str, api_token: str, verify_ssl: bool = False):
        """
        Initialize the FortiSwitch manager.
        
        Args:
            fortigate_ip: IP address or hostname of the FortiGate
            api_token: API token for authentication
            verify_ssl: Whether to verify SSL certificates
        """
        self.fortigate_ip = fortigate_ip
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        
        # Ensure fortigate_ip doesn't already include https://
        if fortigate_ip.startswith('https://'):
            self.base_url = f"{fortigate_ip}/api/v2"
        else:
            self.base_url = f"https://{fortigate_ip}/api/v2"
            
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        logger.debug(f"Initialized FortiSwitchManager for FortiGate at {fortigate_ip}")
        
    def get_arp_table(self) -> Dict[str, Any]:
        """
        Get the ARP table from the FortiGate.
        Returns:
            Dictionary mapping MAC addresses to IP addresses (and full raw response)
        """
        url = f"{self.base_url}/monitor/system/arp"
        logger.debug(f"Getting ARP table from {url}")
        try:
            response = requests.get(url, headers=self.headers, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()
            arp_map = {}
            for entry in data.get('results', []):
                mac = entry.get('mac')
                ip = entry.get('ip')
                if mac and ip:
                    # Normalize MAC to all lowercase, no colons, and uppercase with colons
                    arp_map[mac] = ip
                    arp_map[mac.lower()] = ip
                    arp_map[mac.replace(':', '').lower()] = ip
                    arp_map[mac.replace(':', '').upper()] = ip
                # Optionally add other formats
            logger.info(f"Retrieved {len(arp_map)} ARP MAC/IP mappings")
            return {'success': True, 'arp_map': arp_map, 'raw': data}
        except Exception as e:
            logger.error(f"Error retrieving ARP table: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_managed_switches(self) -> Dict[str, Any]:
        """
        Get all FortiSwitches managed by the FortiGate.
        
        Returns:
            Dictionary containing the response from the API
        """
        url = f"{self.base_url}/monitor/switch-controller/managed-switch"
        logger.debug(f"Getting managed switches from {url}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            # Typically, the monitor endpoint returns a 'results' key with a list of switches
            switches = []
            for sw in data.get('results', []):
                switches.append({
                    'serial': sw.get('serial'),
                    'hostname': sw.get('hostname'),
                    'status': sw.get('status'),
                    'ip': sw.get('ip'),
                    'mac': sw.get('mac'),
                    'version': sw.get('version'),
                })
            logger.info(f"Successfully retrieved {len(switches)} managed switches")
            return {'success': True, 'switches': switches, 'raw': data}

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting managed switches: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def get_switch_details(self, switch_id: str) -> Dict[str, Any]:
        """
        Get details for a specific FortiSwitch.
        
        Args:
            switch_id: Serial number or other ID of the FortiSwitch
            
        Returns:
            Dictionary containing the response from the API
        """
        url = f"{self.base_url}/cmdb/switch-controller/managed-switch/{switch_id}"
        logger.debug(f"Getting switch details from {url}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully retrieved details for switch {switch_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting switch details: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def change_switch_ip(self, switch_id: str, new_ip: str, new_netmask: str = "255.255.255.0") -> Dict[str, Any]:
        """
        Change the IP address of a FortiSwitch.
        
        Args:
            switch_id: Serial number or other ID of the FortiSwitch
            new_ip: New IP address to assign to the FortiSwitch
            new_netmask: Network mask to use with the new IP
            
        Returns:
            Dictionary containing the response from the API
        """
        url = f"{self.base_url}/cmdb/switch-controller/managed-switch/{switch_id}"
        logger.debug(f"Changing IP address for switch {switch_id} to {new_ip}/{new_netmask}")
        
        # Data payload for the API request
        data = {
            "fsw-wan1-admin": "enable",
            "fsw-wan1-ip": new_ip,
            "fsw-wan1-netmask": new_netmask
        }
        
        try:
            response = requests.put(
                url,
                headers=self.headers,
                json=data,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated IP of {switch_id} to {new_ip}")
            return {
                "success": True,
                "message": f"Successfully updated IP of {switch_id} to {new_ip}",
                "data": result
            }
        except requests.exceptions.HTTPError as e:
            error_data = {}
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                try:
                    error_data = e.response.json()
                except:
                    error_data = {"raw_response": e.response.text}
            
            logger.error(f"API error changing switch IP: {str(e)}")
            return {
                "success": False,
                "message": f"API Error: {str(e)}",
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                "data": error_data
            }
        except Exception as e:
            logger.error(f"Unexpected error changing switch IP: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "data": None
            }
    
    def get_connected_devices(self, switch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all devices connected to FortiSwitch ports.
        
        This function retrieves data from multiple sources and correlates them:
        1. switch-controller/mac-cache for device MAC information
        2. user/device for detailed device info from FortiGate's device database
        3. system/arp to map MACs to IPs
        
        Args:
            switch_id: Optional filter for a specific switch
            
        Returns:
            Dictionary containing success status and device information
        """
        try:
            # STEP 1: Get MAC cache information
            mac_cache_url = f"{self.base_url}/monitor/switch-controller/mac-cache"
            mac_response = requests.get(mac_cache_url, headers=self.headers, verify=self.verify_ssl)
            mac_response.raise_for_status()
            mac_data = mac_response.json()
            
            # STEP 2: Get ARP table for MAC-to-IP mapping
            arp_result = self.get_arp_table()
            arp_map = arp_result.get('arp_map', {}) if arp_result.get('success', False) else {}
            
            # STEP 3: Get device list from FortiGate's device database
            device_url = f"{self.base_url}/cmdb/user/device"
            device_response = requests.get(device_url, headers=self.headers, verify=self.verify_ssl)
            device_data = {}
            if device_response.status_code == 200:
                device_data = device_response.json()
                logger.debug(f"Retrieved device data: {device_data}")
            else:
                logger.warning(f"Failed to retrieve device data: {device_response.status_code}")
                
            # Create a mapping of MAC addresses to device information
            device_map = {}
            if device_data and 'results' in device_data:
                for device in device_data.get('results', []):
                    if 'mac' in device:
                        # Normalize MAC to handle different formats
                        mac = device['mac'].lower()
                        mac_no_colons = mac.replace(':', '').lower()
                        
                        # Store both formats
                        device_map[mac] = device
                        device_map[mac_no_colons] = device
                        
                        # Also store uppercase variants
                        device_map[mac.upper()] = device
                        device_map[mac_no_colons.upper()] = device
            
            # STEP 4: Get network-monitor information (FortiOS 7.0+)
            # This is an additional source for device identification
            monitor_data = {}
            network_monitor_map = {}  # Map MAC addresses to network monitor data
            try:
                monitor_url = f"{self.base_url}/monitor/switch-controller/network-monitor"
                monitor_response = requests.get(monitor_url, headers=self.headers, verify=self.verify_ssl)
                if monitor_response.status_code == 200:
                    monitor_data = monitor_response.json()
                    logger.debug(f"Retrieved network monitor data: {monitor_data}")
                    
                    # Create a mapping of MAC addresses to network monitor data
                    if 'results' in monitor_data:
                        for device in monitor_data.get('results', []):
                            if 'mac' in device:
                                mac = device['mac'].lower()
                                mac_no_colons = mac.replace(':', '').lower()
                                
                                # Store both formats
                                network_monitor_map[mac] = device
                                network_monitor_map[mac_no_colons] = device
                                
                                # Also store uppercase variants
                                network_monitor_map[mac.upper()] = device
                                network_monitor_map[mac_no_colons.upper()] = device
            except Exception as e:
                logger.warning(f"Network monitor endpoint not available: {e}")
            
            # Filter and process the MAC cache data
            devices = []
            for entry in mac_data.get('results', []):
                # Filter by switch_id if provided
                if switch_id is not None and entry.get('switch_id') != switch_id and entry.get('switch', '').lower() != switch_id.lower():
                    continue
                    
                # Get MAC in different formats for matching
                mac = entry.get('mac', '')
                if not mac:
                    continue
                    
                mac_lower = mac.lower()
                mac_upper = mac.upper()
                mac_no_colons_lower = mac_lower.replace(':', '')
                mac_no_colons_upper = mac_upper.replace(':', '')
                
                # Try all MAC formats to find in device map and ARP table
                device_info = None
                for mac_format in [mac_lower, mac_upper, mac_no_colons_lower, mac_no_colons_upper]:
                    if mac_format in device_map:
                        device_info = device_map[mac_format]
                        break
                        
                # Get IP from ARP table or device info
                ip = 'Unknown'
                for mac_format in [mac_lower, mac_upper, mac_no_colons_lower, mac_no_colons_upper]:
                    if mac_format in arp_map:
                        ip = arp_map[mac_format]
                        break
                
                # Check network monitor data for additional info
                network_monitor_info = None
                for mac_format in [mac_lower, mac_upper, mac_no_colons_lower, mac_no_colons_upper]:
                    if mac_format in network_monitor_map:
                        network_monitor_info = network_monitor_map[mac_format]
                        break
                
                # If still unknown, try to get from device info or network monitor
                if ip == 'Unknown':
                    if device_info and 'ip' in device_info:
                        ip = device_info.get('ip')
                    elif network_monitor_info and 'ip' in network_monitor_info:
                        ip = network_monitor_info.get('ip')
                
                # Format port name for better readability
                port_raw = entry.get('port', '')
                port_name = self._format_port_name(port_raw)
                
                # Determine device type and name from available info
                # Use more descriptive defaults based on available information
                device_type = 'Network Device'  # Better default than 'Unknown'
                
                # Use MAC vendor prefix for better device naming when possible
                mac_prefix = mac[:8].upper() if len(mac) >= 8 else ''
                vendor_name = self._get_vendor_from_mac_prefix(mac_prefix)
                
                # Default device name based on port and MAC
                device_name = f"{vendor_name} ({port_name})" if vendor_name else f"Device on {port_name}"
                
                # Try to get hostname from network monitor data
                if network_monitor_info:
                    if 'host' in network_monitor_info and network_monitor_info['host']:
                        device_name = network_monitor_info['host']
                    if 'device_type' in network_monitor_info and network_monitor_info['device_type']:
                        device_type = network_monitor_info['device_type']
                
                # Override with device info if available (highest priority)
                if device_info:
                    device_type = device_info.get('type', device_type)
                    device_name = device_info.get('name', device_name)
                    
                # Create the device entry
                device_entry = {
                    'port': entry.get('port'),
                    'device_mac': mac,
                    'vlan': entry.get('vlan'),
                    'age': entry.get('age'),
                    'switch_id': entry.get('switch_id', entry.get('switch')),
                    'type': device_type,
                    'ip': ip,
                    'name': device_name
                }
                if entry.get('port') == 'port23':
                    logger.info("Skipping DHCP lookup for port 23")
                    device_entry = {
                        'port': entry.get('port'),
                        'device_mac': mac,
                        'vlan': entry.get('vlan'),
                        'age': entry.get('age'),
                        'switch_id': entry.get('switch_id', entry.get('switch')),
                        'type': 'FortiGate Connection',
                        'ip': 'N/A',
                        'name': 'netintegratefw'
                    }
                    devices.append(device_entry)
                    continue
                devices.append(device_entry)
            
            return {
                'success': True,
                'devices': devices,
                'raw': {
                    'mac_cache': mac_data,
                    'device_list': device_data,
                    'network_monitor': monitor_data
                }
            }
        except requests.exceptions.RequestException as e:
            error_data = {}
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                try:
                    error_data = e.response.json()
                except:
                    error_data = {"raw_response": e.response.text}
            
            logger.error(f"API error retrieving connected devices: {str(e)}")
            return {
                "success": False,
                "message": f"API Error: {str(e)}",
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                "data": error_data
            }
        except Exception as e:
            logger.error(f"Unexpected error retrieving connected devices: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "data": None
            }
        finally:
            pass  # Add any necessary cleanup code here
            
    def _format_port_name(self, port_raw: str) -> str:
        """
        Format port name for better readability.
        
        Args:
            port_raw: Raw port name from API (e.g., 'port1', 'port23')
            
        Returns:
            Formatted port name (e.g., 'Port 1', 'Port 23')
        """
        if not port_raw:
            return "Unknown Port"
            
        # Handle common port naming formats
        if port_raw.startswith('port'):
            try:
                port_num = int(port_raw[4:])
                return f"Port {port_num}"
            except ValueError:
                pass
                
        # Handle other formats or return original with first letter capitalized
        return port_raw[0].upper() + port_raw[1:] if port_raw else "Unknown Port"
    
    def _get_vendor_from_mac_prefix(self, mac_prefix: str, use_online_lookup: bool = True) -> str:
        """
        Get vendor name from MAC address prefix.
        Uses an enhanced implementation with a comprehensive vendor database and online lookup.
        
        Args:
            mac_prefix: MAC address (any format)
            use_online_lookup: Whether to use online lookup if not found locally
            
        Returns:
            Vendor name or empty string if not recognized
        """
        from app.services.mac_vendors import get_vendor_from_mac
        
        return get_vendor_from_mac(mac_prefix, use_online_lookup)
        
    def get_vendor_icon(self, vendor: str) -> str:
        """
        Get the icon filename for a vendor.
        
        Args:
            vendor: Vendor name
        
        Returns:
            Icon filename or default icon if not found
        """
        from app.services.mac_vendors import get_vendor_icon
        
        return get_vendor_icon(vendor)
        
    def get_vendor_color(self, vendor: str) -> str:
        """
        Get the color for a vendor.
        
        Args:
            vendor: Vendor name
        
        Returns:
            Color hex code
        """
        from app.services.mac_vendors import get_vendor_color
        
        return get_vendor_color(vendor)
        
    def refresh_vendor_cache(self) -> None:
        """
        Force a refresh of the vendor cache by clearing expired entries.
        """
        from app.services.mac_vendors import refresh_vendor_cache
        
        refresh_vendor_cache()

    def get_user_device_list(self) -> Dict[str, Any]:
        """
        Get the list of known devices from the FortiGate user device database.
        
        Returns:
            Dictionary with device information
        """
        url = f"{self.base_url}/cmdb/user/device"
        logger.debug(f"Getting device list from {url}")
        
        try:
            response = requests.get(url, headers=self.headers, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant device info
            devices = []
            for device in data.get('results', []):
                # Create a clean device entry with relevant fields
                device_entry = {
                    'name': device.get('name', 'Unknown'),
                    'mac': device.get('mac', 'Unknown'),
                    'type': device.get('type', 'Unknown'),
                    'ip': device.get('ip', 'Unknown'),
                    'master_device': device.get('master-device', ''),
                    'comment': device.get('comment', ''),
                    'user': device.get('user', ''),
                    'device_id': device.get('id', 0)
                }
                devices.append(device_entry)
                
            logger.info(f"Successfully retrieved {len(devices)} devices from device database")
            return {'success': True, 'devices': devices, 'raw': data}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting user device list: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }

    def get_switch_ports(self, switch_id: str) -> Dict[str, Any]:
        """
        Get port information for a specific FortiSwitch.
        
        Args:
            switch_id: Serial number or other ID of the FortiSwitch
            
        Returns:
            Dictionary containing the response from the API
        """
        url = f"{self.base_url}/monitor/switch-controller/port-stats"
        logger.debug(f"Getting port information for switch {switch_id}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            # port-stats returns stats for all switches; filter for this switch_id
            ports = []
            for entry in data.get('results', []):
                if entry.get('switch_id') == switch_id or entry.get('switch', '').lower() == switch_id.lower():
                    ports.append({
                        'port': entry.get('port'),
                        'status': entry.get('status'),
                        'speed': entry.get('speed'),
                        'mac': entry.get('mac'),
                        'rx_bytes': entry.get('rx_bytes'),
                        'tx_bytes': entry.get('tx_bytes'),
                        'errors': entry.get('errors'),
                    })
            logger.info(f"Successfully retrieved {len(ports)} ports for switch {switch_id}")
            return {'success': True, 'ports': ports, 'raw': data}

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting switch ports: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }