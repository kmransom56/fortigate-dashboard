#!/usr/bin/env python3
"""
Debug script to analyze device aggregation issues in FortiSwitch service.
This script will help identify why connected devices aren't being properly
associated with switch ports.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from services.fortiswitch_service import (
    get_managed_switches,
    get_detected_devices,
    get_fgt_dhcp,
    build_mac_ip_map,
    build_detected_device_map,
    normalize_mac,
    collect_devices_per_port,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def debug_device_aggregation():
    """Debug the device aggregation process step by step."""

    print("=== FortiSwitch Device Aggregation Debug ===\n")

    # Step 1: Fetch raw data
    print("1. Fetching raw data from APIs...")
    switches_data = get_managed_switches()
    detected_data = get_detected_devices()
    dhcp_data = get_fgt_dhcp()

    print(f"   - Switches data type: {type(switches_data)}")
    print(f"   - Detected devices data type: {type(detected_data)}")
    print(f"   - DHCP data type: {type(dhcp_data)}")

    # Step 2: Analyze detected devices
    print("\n2. Analyzing detected devices...")
    if isinstance(detected_data, dict) and "results" in detected_data:
        detected_results = detected_data["results"]
        print(f"   - Found {len(detected_results)} detected devices")
        for i, device in enumerate(detected_results):
            mac = device.get("mac", "Unknown")
            port = device.get("port_name", "Unknown")
            switch_id = device.get("switch_id", "Unknown")
            vlan = device.get("vlan_id", "Unknown")
            print(
                f"     Device {i+1}: MAC={mac}, Port={port}, Switch={switch_id}, VLAN={vlan}"
            )
    else:
        print("   - No detected devices found or invalid format")

    # Step 3: Analyze DHCP data
    print("\n3. Analyzing DHCP data...")
    if isinstance(dhcp_data, dict) and "results" in dhcp_data:
        dhcp_results = dhcp_data["results"]
        print(f"   - Found {len(dhcp_results)} DHCP leases")
        for i, lease in enumerate(dhcp_results):
            mac = lease.get("mac", "Unknown")
            ip = lease.get("ip", "Unknown")
            hostname = lease.get("hostname", "Unknown")
            interface = lease.get("interface", "Unknown")
            print(
                f"     Lease {i+1}: MAC={mac}, IP={ip}, Hostname={hostname}, Interface={interface}"
            )
    else:
        print("   - No DHCP data found or invalid format")

    # Step 4: Build maps
    print("\n4. Building lookup maps...")
    dhcp_map = build_mac_ip_map(dhcp_data)
    detected_map = build_detected_device_map(detected_data)

    print(f"   - DHCP map entries: {len(dhcp_map)}")
    print(f"   - Detected device map entries: {len(detected_map)}")

    print("\n   DHCP Map contents:")
    for mac, info in dhcp_map.items():
        print(f"     {mac}: IP={info.get('ip')}, Hostname={info.get('hostname')}")

    print("\n   Detected Device Map contents:")
    for key, devices in detected_map.items():
        print(f"     {key}: {len(devices)} devices")
        for device in devices:
            print(f"       - MAC: {device.get('mac')}, VLAN: {device.get('vlan_id')}")

    # Step 5: Analyze switch data
    print("\n5. Analyzing switch data...")
    if isinstance(switches_data, dict) and "results" in switches_data:
        switch_results = switches_data["results"]
        print(f"   - Found {len(switch_results)} switches")

        for switch in switch_results:
            switch_serial = switch.get("serial", "Unknown")
            switch_name = switch.get("switch-id", "Unknown")
            ports = switch.get("ports", [])

            print(f"\n   Switch: {switch_name} (Serial: {switch_serial})")
            print(f"   - Total ports: {len(ports)}")

            # Count active ports
            active_ports = [
                p for p in ports if isinstance(p, dict) and p.get("status") == "up"
            ]
            print(f"   - Active ports: {len(active_ports)}")

            for port in active_ports:
                port_name = port.get("interface", "Unknown")
                vlan = port.get("vlan", "Unknown")
                speed = port.get("speed", 0)
                print(f"     - {port_name}: VLAN={vlan}, Speed={speed}, Status=up")

            # Step 6: Test device aggregation for this switch
            print(f"\n6. Testing device aggregation for switch {switch_serial}...")
            port_devices = collect_devices_per_port(
                ports, switch_serial, detected_map, {}, {}, dhcp_map
            )

            print(f"   - Aggregated devices on {len(port_devices)} ports")
            for port_name, devices in port_devices.items():
                if devices:
                    print(f"     Port {port_name}: {len(devices)} devices")
                    for device in devices:
                        mac = device.get("device_mac", "Unknown")
                        ip = device.get("device_ip", "Unknown")
                        hostname = device.get("device_type", "Unknown")
                        source = device.get("source", "Unknown")
                        print(f"       - {hostname} ({ip}) [{mac}] from {source}")

    print("\n=== Debug Complete ===")


def analyze_mac_matching():
    """Analyze MAC address matching between detected devices and DHCP."""

    print("\n=== MAC Address Matching Analysis ===")

    detected_data = get_detected_devices()
    dhcp_data = get_fgt_dhcp()

    # Extract MACs from detected devices
    detected_macs = set()
    if isinstance(detected_data, dict) and "results" in detected_data:
        for device in detected_data["results"]:
            mac = normalize_mac(device.get("mac"))
            if mac:
                detected_macs.add(mac)

    # Extract MACs from DHCP
    dhcp_macs = set()
    if isinstance(dhcp_data, dict) and "results" in dhcp_data:
        for lease in dhcp_data["results"]:
            mac = normalize_mac(lease.get("mac"))
            if mac:
                dhcp_macs.add(mac)

    print(f"Detected device MACs: {len(detected_macs)}")
    for mac in sorted(detected_macs):
        print(f"  - {mac}")

    print(f"\nDHCP lease MACs: {len(dhcp_macs)}")
    for mac in sorted(dhcp_macs):
        print(f"  - {mac}")

    # Find matches
    matches = detected_macs.intersection(dhcp_macs)
    print(f"\nMatching MACs: {len(matches)}")
    for mac in sorted(matches):
        print(f"  - {mac}")

    # Find mismatches
    detected_only = detected_macs - dhcp_macs
    dhcp_only = dhcp_macs - detected_macs

    print(f"\nDetected only (no DHCP): {len(detected_only)}")
    for mac in sorted(detected_only):
        print(f"  - {mac}")

    print(f"\nDHCP only (not detected): {len(dhcp_only)}")
    for mac in sorted(dhcp_only):
        print(f"  - {mac}")


if __name__ == "__main__":
    try:
        debug_device_aggregation()
        analyze_mac_matching()
    except Exception as e:
        logger.error(f"Debug script failed: {e}", exc_info=True)
        sys.exit(1)
