#!/usr/bin/env python3
"""
Debug script to examine DHCP data structure
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.fortiswitch_service import get_fgt_dhcp, build_mac_ip_map
import json


def main():
    print("=== Debugging DHCP Data Structure ===")

    # Get raw DHCP data
    print("1. Fetching raw DHCP data...")
    dhcp_data = get_fgt_dhcp()

    print(f"2. Raw DHCP data type: {type(dhcp_data)}")
    print(
        f"   Raw DHCP data keys: {list(dhcp_data.keys()) if isinstance(dhcp_data, dict) else 'Not a dict'}"
    )

    print("\n3. Raw DHCP data:")
    print(json.dumps(dhcp_data, indent=2, default=str))

    # Build the map
    print("\n4. Building DHCP map...")
    dhcp_map = build_mac_ip_map(dhcp_data)

    print(f"5. DHCP map result:")
    print(f"   Type: {type(dhcp_map)}")
    print(f"   Length: {len(dhcp_map)}")
    print(f"   Keys: {list(dhcp_map.keys())}")

    print("\n6. DHCP map contents:")
    for mac, info in dhcp_map.items():
        print(f"   MAC: {mac}")
        print(f"   Info: {info}")
        print()


if __name__ == "__main__":
    main()
