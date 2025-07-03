#!/usr/bin/env python3
"""
Debug script to check current API responses from FortiGate
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.fortiswitch_service import get_fortiswitches_fullview
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    print("=== Debugging Current API Responses ===")

    try:
        # Get the current FortiSwitch data
        print("\n1. Calling get_fortiswitches_fullview()...")
        switches_data = get_fortiswitches_fullview()

        print(f"\n2. Raw response type: {type(switches_data)}")
        print(f"   Raw response length: {len(str(switches_data))}")

        # Pretty print the response
        print("\n3. Full API Response:")
        print("=" * 80)
        if isinstance(switches_data, (dict, list)):
            print(json.dumps(switches_data, indent=2, default=str))
        else:
            print(f"Non-JSON response: {switches_data}")
        print("=" * 80)

        # Analyze the structure
        if isinstance(switches_data, dict):
            print(f"\n4. Response Analysis:")
            print(f"   - Top-level keys: {list(switches_data.keys())}")

            if "switches" in switches_data:
                switches = switches_data["switches"]
                print(f"   - Number of switches: {len(switches)}")

                for i, switch in enumerate(switches):
                    print(f"\n   Switch {i+1}:")
                    if isinstance(switch, dict):
                        print(f"     - Keys: {list(switch.keys())}")
                        print(f"     - Name: {switch.get('name', 'N/A')}")
                        print(f"     - Serial: {switch.get('serial', 'N/A')}")
                        print(f"     - Status: {switch.get('status', 'N/A')}")
                        print(f"     - IP: {switch.get('ip_address', 'N/A')}")

                        if "ports" in switch:
                            ports = switch["ports"]
                            print(f"     - Number of ports: {len(ports)}")

                            # Check for devices on ports
                            ports_with_devices = [
                                p for p in ports if p.get("connected_devices")
                            ]
                            print(
                                f"     - Ports with devices: {len(ports_with_devices)}"
                            )

                            if ports_with_devices:
                                print("     - Devices found:")
                                for port in ports_with_devices:
                                    devices = port.get("connected_devices", [])
                                    print(
                                        f"       Port {port.get('name', 'Unknown')}: {len(devices)} devices"
                                    )
                                    for device in devices:
                                        print(
                                            f"         - {device.get('mac', 'Unknown MAC')}: {device.get('hostname', 'Unknown Host')}"
                                        )
                            else:
                                print("     - No devices found on any ports")
                                # Show first few ports for debugging
                                print("     - Sample ports (first 3):")
                                for port in ports[:3]:
                                    print(
                                        f"       Port {port.get('name', 'Unknown')}: {dict(port)}"
                                    )

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
