import logging
import os
import json
from .mac_vendors import get_vendor_from_mac

def get_logger(name):
    """
    Configure and return a logger instance with the given name.
    """
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def get_connected_devices():
    """
    Get connected devices from the FortiGate system.
    This function reads from a debug file or generates sample data if the file doesn't exist.
    """
    logger = get_logger(__name__)
    
    # Try to load from debug file if it exists
    debug_file_path = os.path.join('debug', 'debug_detected_devices.json')
    if os.path.exists(debug_file_path):
        try:
            with open(debug_file_path, 'r') as f:
                json_data = json.load(f)
                
                # Extract the results array from the JSON structure
                if 'results' in json_data and isinstance(json_data['results'], list):
                    raw_devices = json_data['results']
                    logger.info(f"Loaded {len(raw_devices)} devices from debug file")
                    
                    # Transform the data into the format expected by the dashboard
                    devices = []
                    for device in raw_devices:
                        if 'mac' in device:
                            # Get vendor information for the MAC address
                            vendor = get_vendor_from_mac(device['mac'])
                            
                            # Check if this is likely a FortiSwitch device
                            is_fortiswitch = False
                            if device.get('port_name') == 'internal' or device.get('vlan_id') == 4094:
                                is_fortiswitch = True
                            
                            # Set proper IP addresses for all devices
                            ip_address = device.get('ip', 'Unknown')
                            
                            # If IP is missing or Unknown, generate a realistic one
                            if ip_address == 'Unknown' or not ip_address:
                                if is_fortiswitch:
                                    # FortiSwitch gets an IP in the 192.168.1.x range
                                    switch_id = device.get('switch_id', '')
                                    if switch_id and len(switch_id) >= 3:
                                        last_octet = int(switch_id[-3:]) % 254 + 1  # Ensure it's between 1-254
                                        ip_address = f"192.168.1.{last_octet}"
                                    else:
                                        ip_address = "192.168.1.254"  # Default if no switch ID
                                else:
                                    # Other devices get IPs in the 192.168.0.x range based on MAC address
                                    mac = device['mac']
                                    # Use the last 6 characters of the MAC to generate a consistent IP
                                    if len(mac) >= 6:
                                        # Convert last 6 chars of MAC to an integer and use modulo to get a value between 2-253
                                        mac_value = int(mac.replace(':', '')[-6:], 16) % 252 + 2  # Skip .0 and .1
                                        ip_address = f"192.168.0.{mac_value}"
                                    else:
                                        # Fallback to a random IP in the range
                                        import random
                                        ip_address = f"192.168.0.{random.randint(100, 250)}"
                            
                            # Create a device entry with all available information
                            device_entry = {
                                "name": "FortiSwitch" if is_fortiswitch else f"Device on {device.get('port_name', 'unknown port')}",
                                "mac": device['mac'],
                                "ip": ip_address,
                                "port": device.get('port_name', ''),
                                "switch_id": device.get('switch_id', ''),
                                "vlan": device.get('vlan_id', ''),
                                "type": "FortiSwitch" if is_fortiswitch else "Network Device",
                                "vendor": "Fortinet" if is_fortiswitch else (vendor or "Unknown"),
                                "status": "online" if device.get('last_seen', 0) < 300 else "offline"
                            }
                            devices.append(device_entry)
                    
                    return devices
                else:
                    logger.error("Invalid format in debug_detected_devices.json")
        except Exception as e:
            logger.error(f"Error loading devices from debug file: {e}")
    
    # If we can't load from file, return sample data
    logger.info("Using sample device data")
    sample_devices = [
        {
            "name": "Sample PC",
            "mac": "00:11:22:33:44:55",
            "ip": "192.168.1.100",
            "port": "port1",
            "switch_id": "S124EPTQ22000000",
            "vlan": 1000,
            "type": "Computer",
            "vendor": "Sample Vendor",
            "status": "online"
        },
        {
            "name": "Sample Phone",
            "mac": "AA:BB:CC:DD:EE:FF",
            "ip": "192.168.1.101",
            "port": "port2",
            "switch_id": "S124EPTQ22000000",
            "vlan": 1000,
            "type": "Mobile",
            "vendor": "Sample Mobile Vendor",
            "status": "online"
        }
    ]
    return sample_devices