import re
import pandas as pd
from typing import List, Dict

def parse_fortinet_data(file_path: str) -> List[Dict]:
    """
    Parse Fortinet device data and extract device information
    """
    devices = []
    
    try:
        # Read the file - could be text or CSV
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Split into individual device entries
        # This assumes each device entry is on a line or separated by specific patterns
        lines = content.split('\n')
        
        for line in lines:
            if line.strip():  # Skip empty lines
                device_info = parse_device_line(line)
                if device_info:
                    devices.append(device_info)
                    
    except Exception as e:
        print(f"Error reading file: {e}")
        
    return devices

def parse_device_line(line: str) -> Dict:
    """
    Parse a single line/entry of device data
    """
    device_info = {}
    
    # Extract MAC address (pattern: xx:xx:xx:xx:xx:xx)
    mac_pattern = r'([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})'
    mac_matches = re.findall(mac_pattern, line, re.IGNORECASE)
    if mac_matches:
        device_info['mac_address'] = mac_matches[0]
    
    # Extract IP address
    ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    ip_matches = re.findall(ip_pattern, line)
    if ip_matches:
        device_info['ip_address'] = ip_matches[0]
    
    # Extract port information (IBR_SONIC-XXXXX-SWX: portXX)
    port_pattern = r'(IBR_SONIC-[^:]+):\s*port(\d+)'
    port_match = re.search(port_pattern, line, re.IGNORECASE)
    if port_match:
        device_info['switch_name'] = port_match.group(1)
        device_info['port_number'] = int(port_match.group(2))
    
    # Extract device type/OS
    if 'Windows' in line:
        device_info['device_type'] = 'Windows'
    elif 'Linux' in line:
        device_info['device_type'] = 'Linux'
    elif 'Router' in line:
        device_info['device_type'] = 'Router'
    elif 'Laptop' in line:
        device_info['device_type'] = 'Laptop'
    elif 'Desktop' in line:
        device_info['device_type'] = 'Desktop'
    else:
        device_info['device_type'] = 'Other'
    
    # Extract device name/hostname (this might need adjustment based on your data format)
    # Look for common device name patterns
    device_name_patterns = [
        r'(DM-\d+-\d+)',  # DM-4446-26 pattern
        r'(BACKUP\d+)',   # BACKUP3628 pattern
        r'(IBR_SONIC-\d+)'  # IBR_SONIC-XXXXX pattern
    ]
    
    for pattern in device_name_patterns:
        name_match = re.search(pattern, line)
        if name_match:
            device_info['device_name'] = name_match.group(1)
            break
    
    # Store the original line for reference
    device_info['raw_data'] = line
    
    return device_info if device_info else None

def find_port2_devices(devices: List[Dict]) -> List[Dict]:
    """
    Filter devices connected to port 2
    """
    port2_devices = []
    
    for device in devices:
        # Check for various port 2 formats
        port_num = device.get('port_number')
        raw_data = device.get('raw_data', '')
        
        # Direct port number match
        if port_num == 2:
            port2_devices.append(device)
        # Also check for text patterns in case regex missed some formats
        elif 'port2' in raw_data.lower() or 'port 2' in raw_data.lower() or 'port02' in raw_data.lower():
            port2_devices.append(device)
    
    return port2_devices

def debug_port_patterns(devices: List[Dict], limit: int = 50) -> None:
    """
    Debug function to see what port patterns are actually found
    """
    print(f"\nDEBUG: Analyzing port patterns from first {limit} devices...")
def analyze_all_ports(devices: List[Dict]) -> Dict:
    """
    Analyze all ports found in the dataset
    """
    port_counts = {}
    missing_port_count = 0
    
    for device in devices:
        port_num = device.get('port_number')
        if port_num is not None:
            port_counts[port_num] = port_counts.get(port_num, 0) + 1
        else:
            missing_port_count += 1
    
    print(f"\nPORT ANALYSIS:")
    print("=" * 40)
    print(f"Devices with missing port info: {missing_port_count}")
    print(f"Devices with port info: {len(devices) - missing_port_count}")
    
    if port_counts:
        print("\nTop 20 most used ports:")
        sorted_ports = sorted(port_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        for port, count in sorted_ports:
            print(f"  Port {port}: {count} devices")
        
        # Specifically check for port 2
        if 2 in port_counts:
            print(f"\n*** PORT 2 FOUND: {port_counts[2]} devices ***")
        else:
            print("\n*** PORT 2 NOT FOUND in parsed data ***")
    
    return port_counts
    
def search_raw_text_for_port2(devices: List[Dict]) -> List[Dict]:
    """
    Search raw text for any mention of port 2, regardless of regex parsing
    """
    print(f"\nSEARCHING RAW TEXT for 'port2' patterns...")
    print("=" * 50)
    
    found_devices = []
    patterns_to_check = ['port2', 'port 2', 'port02', 'port_2']
    
    for device in devices:
        raw_data = device.get('raw_data', '').lower()
        
        for pattern in patterns_to_check:
            if pattern in raw_data:
                found_devices.append(device)
                # Show first few examples
                if len(found_devices) <= 5:
                    print(f"Found '{pattern}' in: {device.get('raw_data', '')[:200]}...")
                    print()
                break
    
    print(f"Found {len(found_devices)} devices with 'port2' patterns in raw text")
    return found_devices
    
    port_patterns = set()
    port_numbers = set()
    
    for i, device in enumerate(devices[:limit]):
        raw_data = device.get('raw_data', '')
        port_num = device.get('port_number')
        
        # Find all port-related text
        port_matches = re.findall(r'port\s*\d+', raw_data, re.IGNORECASE)
        for match in port_matches:
            port_patterns.add(match)
        
        if port_num is not None:
            port_numbers.add(port_num)
        
        # Show a few examples
        if i < 10 and ('port' in raw_data.lower() or port_num is not None):
            print(f"Example {i+1}:")
            print(f"  Port Number: {port_num}")
            print(f"  Raw excerpt: ...{raw_data[max(0, raw_data.lower().find('port')-20):raw_data.lower().find('port')+50]}...")
            print()
    
    print(f"Found port patterns: {sorted(port_patterns)}")
    print(f"Found port numbers: {sorted(port_numbers) if port_numbers else 'None'}")
    print("=" * 60)

def create_report(port2_devices: List[Dict]) -> pd.DataFrame:
    """
    Create a pandas DataFrame report of port 2 devices
    """
    if not port2_devices:
        print("No devices found connected to port 2")
        return pd.DataFrame()
    
    df = pd.DataFrame(port2_devices)
    
    # Select relevant columns for the report
    report_columns = ['mac_address', 'ip_address', 'device_name', 'device_type', 
                     'switch_name', 'port_number']
    
    # Only include columns that exist in the data
    available_columns = [col for col in report_columns if col in df.columns]
    
    return df[available_columns]

def main():
    """
    Main function to process the Fortinet data and find port 2 devices
    """
    # Replace with your actual file path
    file_path = "fortinet_data.txt"  # Updated to match your file
    
    print("Parsing Fortinet device data...")
    devices = parse_fortinet_data(file_path)
    print(f"Found {len(devices)} total devices")
    
    # Debug: Show port patterns to understand the data format
    debug_port_patterns(devices, limit=50)
    
    # Analyze all ports in the dataset
    port_counts = analyze_all_ports(devices)
    
    # Search raw text for port2 patterns
    raw_text_port2 = search_raw_text_for_port2(devices)
    
    print("\nSearching for devices on port 2...")
    port2_devices = find_port2_devices(devices)
    print(f"Found {len(port2_devices)} devices connected to port 2")
    
    if port2_devices:
        print("\nDevices connected to port 2:")
        print("=" * 50)
        
        # Create DataFrame report
        df_report = create_report(port2_devices)
        print(df_report.to_string(index=False))
        
        # Save to CSV for further analysis
        df_report.to_csv('port2_devices_report.csv', index=False)
        print(f"\nReport saved to 'port2_devices_report.csv'")
        
        # Print detailed information
        print("\nDetailed Information:")
        print("=" * 50)
        for i, device in enumerate(port2_devices, 1):
            print(f"\nDevice {i}:")
            for key, value in device.items():
                if key != 'raw_data':  # Skip raw data in summary
                    print(f"  {key}: {value}")
    
    return port2_devices

# Alternative function for processing if your data is already in a different format
def process_csv_data(csv_file_path: str):
    """
    If your data is in CSV format, use this function
    """
    try:
        df = pd.read_csv(csv_file_path)
        
        # Adjust column names based on your CSV structure
        # You'll need to modify these based on your actual column names
        if 'Port' in df.columns:
            port2_devices = df[df['Port'] == 2]
        elif 'port' in df.columns:
            port2_devices = df[df['port'] == 2]
        else:
            # Search for port information in text columns
            for col in df.columns:
                if df[col].dtype == 'object':  # Text columns
                    port2_mask = df[col].str.contains('port2', case=False, na=False)
                    if port2_mask.any():
                        port2_devices = df[port2_mask]
                        break
        
        return port2_devices
        
    except Exception as e:
        print(f"Error processing CSV: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    main()