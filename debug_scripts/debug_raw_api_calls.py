#!/usr/bin/env python3
"""
Debug script to check raw API responses from FortiGate APIs
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.fortigate_session import FortiGateSessionManager
from app.services.fortiswitch_service import get_switch_mactable, get_managed_switches
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_api_endpoint(session, endpoint, description):
    """Test a single API endpoint and return the response"""
    print(f"\n=== Testing {description} ===")
    print(f"Endpoint: {endpoint}")

    try:
        response = session.make_api_request(endpoint)
        print(f"Response type: {type(response)}")

        if isinstance(response, dict):
            print(f"Response keys: {list(response.keys())}")
            if "results" in response:
                results = response["results"]
                print(f"Results type: {type(results)}")
                if isinstance(results, list):
                    print(f"Number of results: {len(results)}")
                    if results:
                        print(
                            "First result keys:",
                            (
                                list(results[0].keys())
                                if isinstance(results[0], dict)
                                else "Not a dict"
                            ),
                        )
                elif isinstance(results, dict):
                    print(f"Results keys: {list(results.keys())}")

            # Pretty print the full response
            print("\nFull Response:")
            print("-" * 60)
            print(json.dumps(response, indent=2, default=str))
            print("-" * 60)
        else:
            print(f"Non-dict response: {response}")

        return response

    except Exception as e:
        print(f"ERROR calling {endpoint}: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    print("=== Debugging Raw FortiGate API Calls ===")

    # Initialize session
    session = FortiGateSessionManager()

    # Test each API endpoint individually
    endpoints = [
        (
            "/api/v2/monitor/switch-controller/managed-switch/status",
            "Managed Switch Status",
        ),
        ("/api/v2/monitor/switch-controller/detected-device", "Detected Devices"),
        ("/api/v2/monitor/system/dhcp", "DHCP Leases"),
        ("/api/v2/monitor/system/interface", "System Interfaces"),
        ("/api/v2/monitor/router/ipv4", "IPv4 Routing Table"),
    ]

    results = {}

    for endpoint, description in endpoints:
        results[endpoint] = test_api_endpoint(session, endpoint, description)

    # Summary analysis
    print("\n" + "=" * 80)
    print("SUMMARY ANALYSIS")
    print("=" * 80)

    # Check managed switches
    switch_status = results.get(
        "/api/v2/monitor/switch-controller/managed-switch/status"
    )
    if switch_status and isinstance(switch_status, dict) and "results" in switch_status:
        switches = switch_status["results"]
        print(
            f"\nManaged Switches Found: {len(switches) if isinstance(switches, list) else 'Not a list'}"
        )

        if isinstance(switches, list) and switches:
            for i, switch in enumerate(switches):
                if isinstance(switch, dict):
                    print(f"  Switch {i+1}:")
                    print(f"    Serial: {switch.get('serial', 'N/A')}")
                    print(f"    Name: {switch.get('name', 'N/A')}")
                    print(f"    Status: {switch.get('status', 'N/A')}")
                    print(
                        f"    Connection Status: {switch.get('connection_status', 'N/A')}"
                    )
                    print(f"    IP: {switch.get('ip', 'N/A')}")
                    print(f"    Version: {switch.get('version', 'N/A')}")

                    # Check ports if available
                    if "ports" in switch:
                        ports = switch["ports"]
                        if isinstance(ports, list):
                            up_ports = [
                                p
                                for p in ports
                                if isinstance(p, dict) and p.get("status") == "up"
                            ]
                            print(f"    Total Ports: {len(ports)}")
                            print(f"    Ports Up: {len(up_ports)}")

    # Check detected devices
    detected = results.get("/api/v2/monitor/switch-controller/detected-device")
    if detected and isinstance(detected, dict) and "results" in detected:
        devices = detected["results"]
        print(
            f"\nDetected Devices: {len(devices) if isinstance(devices, list) else 'Not a list'}"
        )
        if isinstance(devices, list) and devices:
            for i, device in enumerate(devices[:3]):  # Show first 3
                if isinstance(device, dict):
                    print(
                        f"  Device {i+1}: {device.get('mac', 'N/A')} on {device.get('switch_id', 'N/A')}"
                    )

    # Check DHCP leases
    dhcp = results.get("/api/v2/monitor/system/dhcp")
    if dhcp and isinstance(dhcp, dict) and "results" in dhcp:
        leases = dhcp["results"]
        print(
            f"\nDHCP Leases: {len(leases) if isinstance(leases, list) else 'Not a list'}"
        )
        if isinstance(leases, list) and leases:
            for i, lease in enumerate(leases[:3]):  # Show first 3
                if isinstance(lease, dict):
                    print(
                        f"  Lease {i+1}: {lease.get('mac', 'N/A')} -> {lease.get('ip', 'N/A')} ({lease.get('hostname', 'N/A')})"
                    )

    # Managed Switch Status and MAC Address Table for a specific switch
    switch_serial = "S124EPTQ22000276"  # Replace with your switch serial if different

    print("=== Managed Switch Status ===")
    switch_status = get_managed_switches()
    print(switch_status)

    print("\n=== MAC Address Table ===")
    mactable = get_switch_mactable(switch_serial)
    print(mactable)


if __name__ == "__main__":
    main()
