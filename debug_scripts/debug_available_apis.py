#!/usr/bin/env python3
"""
Debug script to find available FortiGate API endpoints
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.fortigate_session import FortiGateSessionManager
import json


def test_basic_endpoints():
    """Test basic FortiGate API endpoints to see what's available"""
    session = FortiGateSessionManager()

    # Test basic endpoints that should exist on most FortiGate versions
    basic_endpoints = [
        "/api/v2/monitor/system/status",
        "/api/v2/monitor/system/interface",
        "/api/v2/monitor/system/dhcp",
        "/api/v2/monitor/router/ipv4",
        "/api/v2/monitor/switch-controller/managed-switch",
        "/api/v2/monitor/switch-controller/managed-switch/status",
        "/api/v2/monitor/switch-controller/detected-device",
        "/api/v2/monitor/switch-controller/switch-log",
        "/api/v2/cmdb/switch-controller/managed-switch",
        "/api/v2/monitor/system/available-interfaces",
    ]

    print("=== Testing Basic FortiGate API Endpoints ===\n")

    working_endpoints = []
    failed_endpoints = []

    for endpoint in basic_endpoints:
        try:
            print(f"Testing: {endpoint}")
            response = session.make_api_request(endpoint)

            if isinstance(response, dict):
                if response.get("status_code") == 404:
                    print(f"  ❌ 404 Not Found")
                    failed_endpoints.append(endpoint)
                elif "error" in response:
                    print(f"  ❌ Error: {response.get('error', 'Unknown')}")
                    failed_endpoints.append(endpoint)
                elif "results" in response:
                    results = response["results"]
                    if isinstance(results, list):
                        print(f"  ✅ Success - {len(results)} results")
                    elif isinstance(results, dict):
                        print(f"  ✅ Success - dict with keys: {list(results.keys())}")
                    else:
                        print(f"  ✅ Success - {type(results)}")
                    working_endpoints.append(endpoint)
                else:
                    print(f"  ⚠️  Unexpected response format: {list(response.keys())}")
                    working_endpoints.append(endpoint)
            else:
                print(f"  ⚠️  Non-dict response: {type(response)}")

        except Exception as e:
            print(f"  ❌ Exception: {e}")
            failed_endpoints.append(endpoint)

        print()

    print("=" * 60)
    print("SUMMARY:")
    print(f"✅ Working endpoints ({len(working_endpoints)}):")
    for ep in working_endpoints:
        print(f"  - {ep}")

    print(f"\n❌ Failed endpoints ({len(failed_endpoints)}):")
    for ep in failed_endpoints:
        print(f"  - {ep}")

    # If we have working endpoints, get detailed info from them
    if working_endpoints:
        print("\n" + "=" * 60)
        print("DETAILED RESPONSES FROM WORKING ENDPOINTS:")
        print("=" * 60)

        for endpoint in working_endpoints[:3]:  # Show first 3 working endpoints
            try:
                print(f"\n--- {endpoint} ---")
                response = session.make_api_request(endpoint)
                if isinstance(response, dict) and "results" in response:
                    print(
                        json.dumps(response, indent=2, default=str)[:1000] + "..."
                        if len(str(response)) > 1000
                        else json.dumps(response, indent=2, default=str)
                    )
                else:
                    print(f"Response: {response}")
            except Exception as e:
                print(f"Error getting details: {e}")


if __name__ == "__main__":
    test_basic_endpoints()
