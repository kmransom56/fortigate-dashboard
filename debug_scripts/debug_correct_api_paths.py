#!/usr/bin/env python3
"""
Debug script to test the correct API path structure
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.fortigate_session import FortiGateSessionManager
import json


def test_correct_paths():
    """Test endpoints with the correct path structure"""
    session = FortiGateSessionManager()

    # Test endpoints with the correct path structure (no /api/v2/ prefix)
    test_endpoints = [
        # System monitoring
        "/monitor/system/status",
        "/monitor/system/interface",
        "/monitor/system/dhcp",
        "/monitor/router/ipv4",
        # Switch controller endpoints
        "/monitor/switch-controller/managed-switch",
        "/monitor/switch-controller/managed-switch/status",
        "/monitor/switch-controller/detected-device",
        "/monitor/switch-controller/switch-log",
        # Configuration endpoints
        "/cmdb/switch-controller/managed-switch",
        "/cmdb/system/interface",
        # Alternative switch paths
        "/monitor/switch-controller/fsw-firmware",
        "/monitor/switch-controller/switch-info",
    ]

    print("=== Testing Correct API Path Structure ===\n")

    working_endpoints = []

    for endpoint in test_endpoints:
        try:
            print(f"Testing: {endpoint}")
            response = session.make_api_request(endpoint)

            if isinstance(response, dict):
                if response.get("status_code") == 404:
                    print(f"  ❌ 404 Not Found")
                elif "error" in response and response.get("status_code") != 200:
                    error = response.get("error", "Unknown")
                    print(f"  ❌ Error: {error}")
                elif "results" in response or response.get("status_code") == 200:
                    print(f"  ✅ SUCCESS!")
                    working_endpoints.append(endpoint)

                    if "results" in response:
                        results = response["results"]
                        if isinstance(results, list):
                            print(f"    - {len(results)} results")
                            if results and isinstance(results[0], dict):
                                print(
                                    f"    - First result keys: {list(results[0].keys())}"
                                )
                        elif isinstance(results, dict):
                            print(f"    - Dict with keys: {list(results.keys())}")
                    else:
                        # Direct response without 'results' wrapper
                        print(f"    - Direct response keys: {list(response.keys())}")
                else:
                    print(f"  ⚠️  Unexpected response: {list(response.keys())}")
            else:
                print(f"  ⚠️  Non-dict response: {type(response)}")

        except Exception as e:
            print(f"  ❌ Exception: {e}")

        print()

    # Get detailed responses from working endpoints
    if working_endpoints:
        print("=" * 60)
        print("DETAILED RESPONSES FROM WORKING ENDPOINTS:")
        print("=" * 60)

        for endpoint in working_endpoints:
            try:
                print(f"\n--- {endpoint} ---")
                response = session.make_api_request(endpoint)

                if isinstance(response, dict):
                    # Pretty print but limit size
                    response_str = json.dumps(response, indent=2, default=str)
                    if len(response_str) > 2000:
                        print(response_str[:2000] + "\n... (truncated)")
                    else:
                        print(response_str)
                else:
                    print(f"Response: {response}")

            except Exception as e:
                print(f"Error getting details: {e}")

            print("-" * 40)


if __name__ == "__main__":
    test_correct_paths()
