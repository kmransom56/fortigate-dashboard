"""
MAC Address Vendor Database and Lookup Utilities

This module provides functions and data for identifying device vendors from MAC addresses.
It includes both a local database and online lookup capabilities.
"""
import requests
import json
import os
import logging
import time
from typing import Dict, Optional, Tuple

# Set up logging
logger = logging.getLogger(__name__)

# Cache file path
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
CACHE_FILE = os.path.join(CACHE_DIR, 'mac_vendor_cache.json')

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Common vendor prefixes (first 3 bytes of MAC address)
VENDOR_MAP = {
    # Cisco
    '00:0C:29': 'Cisco',
    '00:40:96': 'Cisco',
    '00:60:09': 'Cisco',
    '00:80:C8': 'Cisco',
    '00:1A:A1': 'Cisco',
    '00:1A:A2': 'Cisco',
    '00:1A:E3': 'Cisco',
    '00:0E:38': 'Cisco',
    '00:0E:D6': 'Cisco',
    '00:13:10': 'Cisco',
    '00:13:7F': 'Cisco',
    '00:14:A8': 'Cisco',
    '00:0F:23': 'Cisco',
    
    # Dell
    '00:14:22': 'Dell',
    '00:1E:C9': 'Dell',
    'F8:BC:12': 'Dell',
    'F8:DB:88': 'Dell',
    '00:06:5B': 'Dell',
    '00:08:74': 'Dell',
    '00:0B:DB': 'Dell',
    '00:12:3F': 'Dell',
    '00:15:C5': 'Dell',
    '00:18:8B': 'Dell',
    '00:21:9B': 'Dell',
    '00:24:E8': 'Dell',
    
    # HP
    '00:0F:61': 'HP',
    '00:10:83': 'HP',
    '00:17:A4': 'HP',
    '94:57:A5': 'HP',
    '9C:8E:99': 'HP',
    '00:0B:CD': 'HP',
    '00:0D:9D': 'HP',
    '00:0E:7F': 'HP',
    '00:0F:20': 'HP',
    '00:11:0A': 'HP',
    '00:11:85': 'HP',
    '00:12:79': 'HP',
    
    # Apple
    '00:03:93': 'Apple',
    '00:05:02': 'Apple',
    '00:0A:27': 'Apple',
    '00:0A:95': 'Apple',
    '00:1E:52': 'Apple',
    '00:25:00': 'Apple',
    '00:26:BB': 'Apple',
    '00:30:65': 'Apple',
    '00:50:E4': 'Apple',
    '00:56:CD': 'Apple',
    '00:C6:10': 'Apple',
    '04:0C:CE': 'Apple',
    '04:15:52': 'Apple',
    '04:1E:64': 'Apple',
    '04:26:65': 'Apple',
    '04:52:F7': 'Apple',
    '04:54:53': 'Apple',
    '04:69:F8': 'Apple',
    
    # Fortinet
    '00:09:0F': 'Fortinet',
    '08:5B:0E': 'Fortinet',
    '00:90:6C': 'Fortinet',
    'E0:23:FF': 'Fortinet',
    '70:4C:A5': 'Fortinet',
    '90:6C:AC': 'Fortinet',
    
    # Common IoT devices
    'EC:FA:BC': 'IP Camera',
    '00:1A:79': 'Smart Device',
    
    # Samsung
    '00:15:99': 'Samsung',
    '00:17:D5': 'Samsung',
    '00:21:19': 'Samsung',
    '00:23:39': 'Samsung',
    '00:24:54': 'Samsung',
    '00:26:37': 'Samsung',
    '00:E0:64': 'Samsung',
    '04:18:0F': 'Samsung',
    '08:08:C2': 'Samsung',
    '08:37:3D': 'Samsung',
    '08:D4:2B': 'Samsung',
    '0C:14:20': 'Samsung',
    '0C:71:5D': 'Samsung',
    '0C:89:10': 'Samsung',
    
    # Printers
    '00:17:C8': 'Printer',
    '00:21:5A': 'Printer',
    '00:26:73': 'Printer',
    '00:00:AA': 'Xerox',
    '00:00:01': 'Xerox',
    '00:08:0D': 'Toshiba',
    '00:80:77': 'Brother',
    '00:80:91': 'Tokyo Electric',
    '00:90:27': 'Intel',
    '00:A0:80': 'Hewlett-Packard',
    '00:AA:00': 'Intel',
    '00:DD:00': 'Ungermann-Bass',
    '08:00:07': 'Apple',
    '08:00:08': 'BBN',
    '08:00:09': 'Hewlett-Packard',
    
    # IP Phones
    '00:04:F2': 'IP Phone',
    '00:07:0E': 'IP Phone',
    '00:0E:08': 'IP Phone',
    '00:1A:E3': 'Cisco IP Phone',
    '00:1C:58': 'Cisco IP Phone',
    '00:1E:F7': 'Cisco IP Phone',
    '00:21:55': 'Cisco IP Phone',
    
    # Microsoft/Xbox
    'FC:8C:11': 'Xbox',
    '3C:18:A0': 'Microsoft',
    '0C:37:96': 'Microsoft',
    'D8:43:AE': 'Microsoft',
    '00:0D:3A': 'Microsoft',
    '00:12:5A': 'Microsoft',
    '00:15:5D': 'Microsoft',
    '00:17:FA': 'Microsoft',
    '00:50:F2': 'Microsoft',
    '28:18:78': 'Microsoft',
    '30:59:B7': 'Microsoft',
    '4C:0B:BE': 'Microsoft',
    
    # Other common vendors
    '38:14:28': 'Huawei',
    '10:7C:61': 'Lenovo',
    'DC:A6:32': 'Raspberry Pi',
    'C4:8B:A3': 'Meraki',
    
    # Sony
    '00:01:4A': 'Sony',
    '00:13:A9': 'Sony',
    '00:1A:80': 'Sony',
    '00:1D:BA': 'Sony',
    '00:24:BE': 'Sony',
    '30:F9:ED': 'Sony',
    '54:42:49': 'Sony',
    '78:84:3C': 'Sony',
    
    # LG
    '00:1C:62': 'LG',
    '00:1E:75': 'LG',
    '00:1F:6B': 'LG',
    '00:1F:E3': 'LG',
    '00:21:FB': 'LG',
    '00:22:A9': 'LG',
    '00:24:83': 'LG',
    '00:25:E5': 'LG',
    '00:26:E2': 'LG',
    
    # Panasonic
    '00:0D:67': 'Panasonic',
    '00:13:43': 'Panasonic',
    '00:19:87': 'Panasonic',
    '00:1B:D3': 'Panasonic',
    '00:1D:0D': 'Panasonic',
    '00:1E:8F': 'Panasonic',
    '00:24:8C': 'Panasonic',
    
    # IoT device manufacturers
    '18:B4:30': 'Nest',
    '64:16:66': 'Nest',
    '7C:70:BC': 'Ecobee',
    '88:4A:EA': 'Ring',
    'B0:C5:54': 'Ring',
    
    # Network equipment vendors
    '00:15:6D': 'Ubiquiti',
    '00:27:22': 'Ubiquiti',
    '04:18:D6': 'Ubiquiti',
    '24:A4:3C': 'Ubiquiti',
    '68:72:51': 'Ubiquiti',
    '00:0B:86': 'Aruba',
    '00:1A:1E': 'Aruba',
    '00:24:6C': 'Aruba',
    '04:BD:88': 'Aruba',
    '00:05:85': 'Juniper',
    '00:10:DB': 'Juniper',
    '00:12:1E': 'Juniper',
    '00:14:F6': 'Juniper',
    
    # Mobile device manufacturers
    '00:1A:11': 'Google',
    '3C:5A:B4': 'Google',
    '54:60:09': 'Google',
    '94:EB:2C': 'Google',
    'A4:77:33': 'Google',
    'D8:6C:63': 'Google',
    '94:65:2D': 'OnePlus',
    'C0:EE:FB': 'OnePlus',
    'E4:F0:42': 'OnePlus',
    '28:6D:CD': 'Xiaomi',
    '3C:BD:D8': 'Xiaomi',
    '58:44:98': 'Xiaomi',
    '64:09:80': 'Xiaomi',
    '98:FA:E3': 'Xiaomi',
}

# Icon mapping for vendors
VENDOR_ICONS = {
    'Cisco': 'cisco.png',
    'Dell': 'dell.png',
    'HP': 'hp.png',
    'Apple': 'apple.png',
    'Fortinet': 'fortinet.png',
    'Samsung': 'samsung.png',
    'Printer': 'printer.png',
    'IP Phone': 'phone.png',
    'Xbox': 'xbox.png',
    'Microsoft': 'microsoft.png',
    'Huawei': 'huawei.png',
    'Lenovo': 'lenovo.png',
    'Raspberry Pi': 'raspberry-pi.png',
    'Meraki': 'meraki.png',
    'Sony': 'sony.png',
    'LG': 'lg.png',
    'Panasonic': 'panasonic.png',
    'Nest': 'nest.png',
    'Ring': 'ring.png',
    'Ecobee': 'ecobee.png',
    'Ubiquiti': 'ubiquiti.png',
    'Aruba': 'aruba.png',
    'Juniper': 'juniper.png',
    'Google': 'google.png',
    'OnePlus': 'oneplus.png',
    'Xiaomi': 'xiaomi.png',
    'Smart Device': 'iot.png',
    'IP Camera': 'camera.png',
    'Unknown': 'unknown.png',
}

# Color mapping for vendor categories
VENDOR_COLORS = {
    'Cisco': '#049fd9',      # Cisco blue
    'Dell': '#007db8',       # Dell blue
    'HP': '#0096d6',         # HP blue
    'Apple': '#999999',      # Apple gray
    'Fortinet': '#ee3124',   # Fortinet red
    'Samsung': '#1428a0',    # Samsung blue
    'Printer': '#000000',    # Black
    'IP Phone': '#83b81a',   # Green
    'Microsoft': '#7fba00',  # Microsoft green
    'Huawei': '#cf0a2c',     # Huawei red
    'Network': '#0078d7',    # Blue for network devices
    'Mobile': '#ffb900',     # Yellow for mobile devices
    'IoT': '#e3008c',        # Pink for IoT devices
    'Computer': '#00b7c3',   # Teal for computers
    'Unknown': '#505050',    # Gray for unknown
}

# Load vendor cache from file
def load_vendor_cache() -> Dict[str, Tuple[str, float]]:
    """
    Load the vendor cache from file.
    
    Returns:
        Dictionary mapping MAC prefixes to (vendor, timestamp) tuples
    """
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading vendor cache: {str(e)}")
        return {}

# Save vendor cache to file
def save_vendor_cache(cache: Dict[str, Tuple[str, float]]) -> None:
    """
    Save the vendor cache to file.
    
    Args:
        cache: Dictionary mapping MAC prefixes to (vendor, timestamp) tuples
    """
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving vendor cache: {str(e)}")

# Initialize cache
_vendor_cache = load_vendor_cache()

def lookup_vendor_online(mac_prefix: str) -> Optional[str]:
    """
    Look up a vendor for a MAC prefix using the MacVendors API.
    
    Args:
        mac_prefix: MAC address prefix (first 6 characters without colons)
    
    Returns:
        Vendor name or None if lookup failed
    """
    # Format MAC for API (remove colons and use first 6 chars)
    mac_for_api = mac_prefix.replace(':', '').upper()[:6]
    
    try:
        response = requests.get(f"https://api.macvendors.com/{mac_for_api}", timeout=2)
        if response.status_code == 200:
            return response.text.strip()
        elif response.status_code == 429:
            logger.warning("Rate limit exceeded for MAC vendor API")
            return None
        else:
            logger.debug(f"MAC vendor lookup failed with status {response.status_code}")
            return None
    except Exception as e:
        logger.debug(f"Error looking up MAC vendor: {str(e)}")
        return None

def get_vendor_from_mac(mac: str, use_online_lookup: bool = True) -> str:
    """
    Get vendor name from MAC address, with caching and online lookup.
    
    Args:
        mac: MAC address (any format)
        use_online_lookup: Whether to use online lookup if not found locally
    
    Returns:
        Vendor name or empty string if not recognized
    """
    if not mac:
        return ""
        
    # Normalize MAC format
    normalized_mac = mac.replace('-', ':').upper()
    
    # Try to match the first 8 chars (includes colons)
    mac_prefix = normalized_mac[:8]
    
    # Check local vendor map first
    if mac_prefix in VENDOR_MAP:
        return VENDOR_MAP[mac_prefix]
    
    # Check first 3 bytes in different formats
    if len(normalized_mac) >= 8:
        first_three_bytes = normalized_mac[:8]
        if first_three_bytes in VENDOR_MAP:
            return VENDOR_MAP[first_three_bytes]
    
    # Check cache
    cache_key = normalized_mac[:8]
    if cache_key in _vendor_cache:
        vendor, timestamp = _vendor_cache[cache_key]
        # Cache entries expire after 30 days
        if time.time() - timestamp < 30 * 24 * 60 * 60:
            return vendor
    
    # Try online lookup if enabled
    if use_online_lookup:
        vendor = lookup_vendor_online(normalized_mac)
        if vendor:
            # Save to cache
            _vendor_cache[cache_key] = (vendor, time.time())
            save_vendor_cache(_vendor_cache)
            return vendor
    
    return ""

def get_vendor_icon(vendor: str) -> str:
    """
    Get the icon filename for a vendor.
    
    Args:
        vendor: Vendor name
    
    Returns:
        Icon filename or default icon if not found
    """
    return VENDOR_ICONS.get(vendor, VENDOR_ICONS.get('Unknown'))

def get_vendor_color(vendor: str) -> str:
    """
    Get the color for a vendor.
    
    Args:
        vendor: Vendor name
    
    Returns:
        Color hex code
    """
    if vendor in VENDOR_COLORS:
        return VENDOR_COLORS[vendor]
    
    # Categorize vendors
    if any(net in vendor.lower() for net in ['cisco', 'juniper', 'aruba', 'ubiquiti', 'meraki', 'fortinet']):
        return VENDOR_COLORS['Network']
    elif any(mobile in vendor.lower() for mobile in ['apple', 'samsung', 'google', 'oneplus', 'xiaomi', 'phone']):
        return VENDOR_COLORS['Mobile']
    elif any(iot in vendor.lower() for iot in ['nest', 'ring', 'ecobee', 'camera', 'smart']):
        return VENDOR_COLORS['IoT']
    elif any(comp in vendor.lower() for comp in ['dell', 'hp', 'microsoft', 'lenovo', 'raspberry']):
        return VENDOR_COLORS['Computer']
    
    return VENDOR_COLORS['Unknown']

def refresh_vendor_cache() -> None:
    """
    Force a refresh of the vendor cache by clearing expired entries.
    """
    global _vendor_cache
    
    # Remove entries older than 30 days
    current_time = time.time()
    _vendor_cache = {
        k: (v, t) for k, (v, t) in _vendor_cache.items()
        if current_time - t < 30 * 24 * 60 * 60
    }
    
    save_vendor_cache(_vendor_cache)
    logger.info("Vendor cache refreshed")
