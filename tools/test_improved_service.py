#!/usr/bin/env python3
"""
Test script for the improved FortiSwitch service using existing debug data.
This will demonstrate the improved device aggregation logic.
"""

import json
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

# Import the improved functions
from services.fortiswitch_service_improved import (
    build_mac_ip_map,
    build_detected_device_map,
    build_arp_map,
    collect_devices_per_port_improved,
    normalize_mac,
)


def load_debug_data():
    """Load the existing debug data files."""
    try:
        with open("debug_detected_devices.json", "r") as f:
            detected_data = json.load(f)

        with open("debug_dhcp_info.json", "r") as f:
            dhcp_data = json.load(f)

        with open("debug_switch_status.json", "r") as f:
            switch_data = json.load(f)

        return detected_data, dhcp_data, switch_data
    except Exception as e:
        logger.error(f"Error loading debug data: {e}")
        return None, None, None


def test_improved_aggregation():
    """Test the improved device aggregation logic."""

    print("=== Testing Improved FortiSwitch Device Aggregation ===\n")

    # Load debug data
    detected_data, dhcp_data, switch_data = load_debug_data()

    if not all([detected_data, dhcp_data, switch_data]):
        print("ERROR: Could not load debug data files")
        return

    print("1. Loaded debug data successfully")
    print(f"   - Detected devices: {len(detected_data.get('results', []))}")
    print(f"   - DHCP leases: {len(dhcp_data.get('results', []))}")
    print(f"   - Switches: {len(switch_data.get('results', []))}")

    # Build maps using improved functions
    print("\n2. Building lookup maps...")
    dhcp_map = build_mac_ip_map(dhcp_data)
    detected_map = build_detected_device_map(detected_data)
    arp_map = {}  # Empty for this test

    print(f"   - DHCP map entries: {len(dhcp_map)}")
    print(f"   - Detected device map entries: {len(detected_map)}")

    # Show DHCP map contents
    print("\n3. DHCP Map Contents:")
    for mac, info in dhcp_map.items():
        hostname = info.get("hostname", "Unknown")
        ip = info.get("ip", "Unknown")
        interface = info.get("interface", "Unknown")
        print(f"   {mac}: {hostname} ({ip}) on {interface}")

    # Show detected device map contents
    print("\n4. Detected Device Map Contents:")
    for key, devices in detected_map.items():
        print(f"   {key}: {len(devices)} devices")
        for device in devices:
            mac = device.get("mac", "Unknown")
            vlan = device.get("vlan_id", "Unknown")
            last_seen = device.get("last_seen", "Unknown")
            print(f"     - MAC: {mac}, VLAN: {vlan}, Last seen: {last_seen}s ago")

    # Test device aggregation for each switch
    print("\n5. Testing Device Aggregation:")

    for switch in switch_data.get("results", []):
        switch_serial = switch.get("serial", "Unknown")
        switch_name = switch.get("switch-id", "Unknown")
        ports = switch.get("ports", [])

        print(f"\n   Switch: {switch_name} (Serial: {switch_serial})")
        print(f"   Total ports: {len(ports)}")

        # Test improved aggregation
        port_devices = collect_devices_per_port_improved(
            ports, switch_serial, detected_map, dhcp_map, arp_map
        )

        print(
            f"   Ports with devices: {len([p for p, d in port_devices.items() if d])}"
        )

        # Show results for ports with devices
        for port_name, devices in port_devices.items():
            if devices:
                print(f"\n     Port {port_name}: {len(devices)} devices")
                for device in devices:
                    mac = device.get("device_mac", "Unknown")
                    ip = device.get("device_ip", "Unknown")
                    hostname = device.get("device_type", "Unknown")
                    source = device.get("source", "Unknown")
                    vlan = device.get("vlan", "Unknown")
                    print(f"       - {hostname}")
                    print(f"         MAC: {mac}")
                    print(f"         IP: {ip}")
                    print(f"         VLAN: {vlan}")
                    print(f"         Source: {source}")

        # Show port status summary
        active_ports = [p for p in ports if p.get("status") == "up"]
        print(f"\n   Port Status Summary:")
        print(f"     - Total ports: {len(ports)}")
        print(f"     - Active ports: {len(active_ports)}")
        print(
            f"     - Ports with detected devices: {len([p for p, d in port_devices.items() if d])}"
        )

        # List active ports
        print(f"\n   Active Ports:")
        for port in active_ports:
            port_name = port.get("interface", "Unknown")
            vlan = port.get("vlan", "Unknown")
            speed = port.get("speed", 0)
            device_count = len(port_devices.get(port_name, []))
            print(
                f"     - {port_name}: VLAN={vlan}, Speed={speed}Mbps, Devices={device_count}"
            )


def test_mac_normalization():
    """Test MAC address normalization improvements."""

    print("\n=== Testing MAC Address Normalization ===")

    test_macs = [
        "10:7c:61:3f:2b:5d",  # Standard format
        "10-7c-61-3f-2b-5d",  # Dash format
        "107c613f2b5d",  # No separators
        "10:7C:61:3F:2B:5D",  # Uppercase
        "10:7c:61:3f:2b:5",  # Missing leading zero
        "invalid-mac",  # Invalid
        "",  # Empty
        None,  # None
    ]

    for mac in test_macs:
        normalized = normalize_mac(mac)
        print(f"   '{mac}' -> '{normalized}'")


if __name__ == "__main__":
    try:
        test_improved_aggregation()
        test_mac_normalization()
        print("\n=== Test Complete ===")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
