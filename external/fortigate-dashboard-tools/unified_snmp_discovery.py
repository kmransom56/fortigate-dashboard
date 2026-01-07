#!/usr/bin/env python3
"""
Unified Network Device Discovery and SNMP Testing
Combines FortiGate (via FortiManager) and Meraki device discovery for comprehensive SNMP monitoring
"""

import subprocess
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
import sys

def run_fortigate_discovery():
    """Run FortiGate device discovery"""
    print("🔍 Discovering FortiGate devices...")
    try:
        result = subprocess.run([
            sys.executable, 'fortigate_mgmt_collector.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ FortiGate discovery completed successfully")
            return True
        else:
            print(f"❌ FortiGate discovery failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ fortigate_mgmt_collector.py not found")
        return False

def run_meraki_discovery():
    """Run Meraki device discovery"""
    print("🔍 Discovering Meraki devices...")
    try:
        result = subprocess.run([
            sys.executable, 'meraki_device_collector.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Meraki discovery completed successfully")
            return True
        else:
            print(f"❌ Meraki discovery failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ meraki_device_collector.py not found")
        return False

def find_latest_file(pattern: str) -> str:
    """Find the latest file matching a pattern"""
    files = list(Path('.').glob(pattern))
    if files:
        return str(max(files, key=lambda f: f.stat().st_mtime))
    return ""

def combine_device_lists() -> str:
    """Combine FortiGate and Meraki device lists"""
    print("🔗 Combining device lists...")
    
    # Find latest files
    fortigate_file = find_latest_file("snmp_stores_*.csv")
    meraki_file = find_latest_file("meraki_snmp_stores_*.csv")
    
    combined_devices = []
    
    # Load FortiGate devices
    if fortigate_file and Path(fortigate_file).exists():
        with open(fortigate_file, 'r') as f:
            reader = csv.DictReader(f)
            fg_devices = list(reader)
            combined_devices.extend(fg_devices)
            print(f"  📡 Loaded {len(fg_devices)} FortiGate devices")
    else:
        print("  ⚠️ No FortiGate device file found")
    
    # Load Meraki devices
    if meraki_file and Path(meraki_file).exists():
        with open(meraki_file, 'r') as f:
            reader = csv.DictReader(f)
            meraki_devices = list(reader)
            combined_devices.extend(meraki_devices)
            print(f"  📡 Loaded {len(meraki_devices)} Meraki devices")
    else:
        print("  ⚠️ No Meraki device file found")
    
    # Save combined list
    if combined_devices:
        output_file = f"combined_snmp_stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(output_file, 'w', newline='') as f:
            fieldnames = ['store_name', 'ip', 'device_type']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(combined_devices)
        
        print(f"✅ Combined device list saved: {output_file} ({len(combined_devices)} total devices)")
        return output_file
    else:
        print("❌ No devices found to combine")
        return ""

def run_snmp_testing(device_file: str, username: str, auth_password: str, priv_password: str, output_format: str = "console"):
    """Run SNMP connectivity testing"""
    print(f"🧪 Testing SNMP connectivity for devices in {device_file}...")
    
    cmd = [
        sys.executable, 'snmp_checker.py',
        '-u', username,
        '-A', auth_password,
        '-X', priv_password,
        '-f', device_file,
        '-o', output_format,
        '-w', '15'  # Use more workers for faster testing
    ]
    
    try:
        result = subprocess.run(cmd, text=True)
        if result.returncode == 0:
            print("✅ SNMP testing completed")
        else:
            print("⚠️ SNMP testing completed with some issues")
    except FileNotFoundError:
        print("❌ snmp_checker.py not found")

def generate_comprehensive_report(device_file: str):
    """Generate a comprehensive network monitoring readiness report"""
    print("📊 Generating comprehensive report...")
    
    if not Path(device_file).exists():
        print(f"❌ Device file {device_file} not found")
        return
    
    # Read device list
    devices = []
    with open(device_file, 'r') as f:
        reader = csv.DictReader(f)
        devices = list(reader)
    
    # Categorize devices
    fortigates = [d for d in devices if 'fortigate' in d['device_type'].lower()]
    merakis = [d for d in devices if 'meraki' in d['device_type'].lower()]
    
    # Generate report
    report_file = f"network_monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("NETWORK MONITORING READINESS REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total Devices: {len(devices)}\n")
        f.write(f"FortiGate Devices: {len(fortigates)}\n")
        f.write(f"Meraki Devices: {len(merakis)}\n\n")
        
        f.write("FORTIGATE DEVICES\n")
        f.write("-" * 40 + "\n")
        for device in fortigates:
            f.write(f"  {device['store_name']} ({device['ip']}) - {device['device_type']}\n")
        
        f.write(f"\nMERAKI DEVICES\n")
        f.write("-" * 40 + "\n")
        for device in merakis:
            f.write(f"  {device['store_name']} ({device['ip']}) - {device['device_type']}\n")
        
        f.write(f"\nNEXT STEPS\n")
        f.write("-" * 40 + "\n")
        f.write("1. Verify SNMP credentials are consistent across all devices\n")
        f.write("2. Configure Auvik with the tested device list\n")
        f.write("3. Set up monitoring policies for each device type\n")
        f.write("4. Schedule regular connectivity testing\n")
    
    print(f"📄 Comprehensive report saved: {report_file}")

def main():
    parser = argparse.ArgumentParser(description='Unified Network Device Discovery and SNMP Testing')
    parser.add_argument('--skip-discovery', action='store_true', help='Skip device discovery, use existing files')
    parser.add_argument('--fortigate-only', action='store_true', help='Only discover FortiGate devices')
    parser.add_argument('--meraki-only', action='store_true', help='Only discover Meraki devices')
    parser.add_argument('--snmp-username', '-u', default='InspireSNMP', help='SNMP username')
    parser.add_argument('--snmp-auth-password', '-A', required=True, help='SNMP authentication password')
    parser.add_argument('--snmp-priv-password', '-X', required=True, help='SNMP privacy password')
    parser.add_argument('--output-format', '-o', choices=['console', 'csv', 'json'], default='csv', help='SNMP test output format')
    parser.add_argument('--test-only', action='store_true', help='Only run SNMP testing on existing device list')
    
    args = parser.parse_args()
    
    print("🚀 Starting Unified Network Device Discovery and SNMP Testing")
    print("=" * 80)
    
    device_file = ""
    
    if not args.test_only and not args.skip_discovery:
        # Device Discovery Phase
        print("\n📡 PHASE 1: DEVICE DISCOVERY")
        print("-" * 40)
        
        discovery_success = False
        
        if not args.meraki_only:
            discovery_success |= run_fortigate_discovery()
        
        if not args.fortigate_only:
            discovery_success |= run_meraki_discovery()
        
        if discovery_success:
            device_file = combine_device_lists()
        else:
            print("❌ Device discovery failed")
            return
    else:
        # Use existing combined file
        device_file = find_latest_file("combined_snmp_stores_*.csv")
        if not device_file:
            device_file = find_latest_file("snmp_stores_*.csv")
        if not device_file:
            device_file = find_latest_file("meraki_snmp_stores_*.csv")
    
    if not device_file or not Path(device_file).exists():
        print("❌ No device file found for SNMP testing")
        return
    
    # SNMP Testing Phase
    print(f"\n🧪 PHASE 2: SNMP CONNECTIVITY TESTING")
    print("-" * 40)
    
    run_snmp_testing(
        device_file, 
        args.snmp_username, 
        args.snmp_auth_password, 
        args.snmp_priv_password,
        args.output_format
    )
    
    # Reporting Phase
    print(f"\n📊 PHASE 3: COMPREHENSIVE REPORTING")
    print("-" * 40)
    
    generate_comprehensive_report(device_file)
    
    print(f"\n🎉 PROCESS COMPLETE!")
    print("=" * 80)
    print(f"📁 Device List: {device_file}")
    print(f"📄 Check the generated reports for detailed results")
    print(f"🔧 Configure Auvik using the tested device list")

if __name__ == "__main__":
    main()