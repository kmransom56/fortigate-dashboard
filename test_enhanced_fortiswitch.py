#!/usr/bin/env python3
"""
Test script to validate the enhanced FortiSwitch service
and compare it with the current implementation.
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

# Import both services
from app.services.fortiswitch_service import (
    get_fortiswitches as get_fortiswitches_original,
)
from app.services.fortiswitch_service_enhanced import get_fortiswitches_enhanced


def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    return logging.getLogger(__name__)


def count_devices(switches_data):
    """Count total devices across all switches."""
    total_devices = 0
    device_details = []

    for switch in switches_data:
        switch_name = switch.get("name", "Unknown")
        for port in switch.get("ports", []):
            port_name = port.get("name", "Unknown")
            devices = port.get("connected_devices", [])
            total_devices += len(devices)

            for device in devices:
                device_details.append(
                    {
                        "switch": switch_name,
                        "port": port_name,
                        "mac": device.get("device_mac", "Unknown"),
                        "ip": device.get("device_ip", "Unknown"),
                        "hostname": device.get("device_name", "Unknown"),
                        "manufacturer": device.get("manufacturer", "Unknown"),
                    }
                )

    return total_devices, device_details


def save_results(data, filename):
    """Save results to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False


def main():
    logger = setup_logging()

    print("=" * 80)
    print("FortiSwitch Service Enhancement Test")
    print("=" * 80)
    print(f"Test started at: {datetime.now()}")
    print()

    # Test original service
    print("1. Testing ORIGINAL FortiSwitch service...")
    try:
        original_data = get_fortiswitches_original()
        original_count, original_devices = count_devices(original_data)

        print(f"   ✓ Original service completed successfully")
        print(f"   ✓ Found {len(original_data)} switches")
        print(f"   ✓ Found {original_count} total devices")

        # Save original results
        save_results(original_data, "debug_scripts/test_original_results.json")
        save_results(original_devices, "debug_scripts/test_original_devices.json")

    except Exception as e:
        print(f"   ✗ Original service failed: {e}")
        logger.error(f"Original service error: {e}", exc_info=True)
        original_data = []
        original_count = 0
        original_devices = []

    print()

    # Test enhanced service
    print("2. Testing ENHANCED FortiSwitch service...")
    try:
        enhanced_data = get_fortiswitches_enhanced()
        enhanced_count, enhanced_devices = count_devices(enhanced_data)

        print(f"   ✓ Enhanced service completed successfully")
        print(f"   ✓ Found {len(enhanced_data)} switches")
        print(f"   ✓ Found {enhanced_count} total devices")

        # Save enhanced results
        save_results(enhanced_data, "debug_scripts/test_enhanced_results.json")
        save_results(enhanced_devices, "debug_scripts/test_enhanced_devices.json")

    except Exception as e:
        print(f"   ✗ Enhanced service failed: {e}")
        logger.error(f"Enhanced service error: {e}", exc_info=True)
        enhanced_data = []
        enhanced_count = 0
        enhanced_devices = []

    print()

    # Compare results
    print("3. Comparing results...")
    print(f"   Original devices detected: {original_count}")
    print(f"   Enhanced devices detected: {enhanced_count}")

    if enhanced_count > original_count:
        improvement = enhanced_count - original_count
        print(f"   ✓ IMPROVEMENT: +{improvement} additional devices detected!")
    elif enhanced_count == original_count:
        print(f"   = Same number of devices detected")
    else:
        print(f"   ⚠ Enhanced service detected fewer devices")

    print()

    # Show device details if enhanced service found devices
    if enhanced_devices:
        print("4. Enhanced service device details:")
        for device in enhanced_devices:
            print(f"   Switch: {device['switch']}")
            print(f"   Port: {device['port']}")
            print(f"   MAC: {device['mac']}")
            print(f"   IP: {device['ip']}")
            print(f"   Hostname: {device['hostname']}")
            print(f"   Manufacturer: {device['manufacturer']}")
            print(f"   ---")

    print()
    print("=" * 80)
    print("Test Summary:")
    print(
        f"- Original service: {len(original_data)} switches, {original_count} devices"
    )
    print(
        f"- Enhanced service: {len(enhanced_data)} switches, {enhanced_count} devices"
    )

    if enhanced_count > original_count:
        print(f"- ✓ Enhancement successful: +{enhanced_count - original_count} devices")
    else:
        print(f"- Results comparison: Enhanced vs Original")

    print(f"- Test completed at: {datetime.now()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
