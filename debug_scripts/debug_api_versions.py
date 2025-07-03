#!/usr/bin/env python3
"""
Debug script to test different API versions and basic connectivity
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.fortigate_session import FortiGateSessionManager
import json


def test_api_versions():
    """Test different API versions and basic endpoints"""
    session = FortiGateSessionManager()

    # Test different API versions and basic endpoints
    test_endpoints = [
        # API v1 endpoints
        "/api/v1/monitor/system/status",
        "/api/v1/monitor/system/interface",
        "/api/v1/monitor/system/dhcp",
        # API v2 basic
        "/api/v2/monitor/system/status",
        "/api/v2/monitor/system/interface",
        # Root API discovery
        "/api/",
        "/api/v1/",
        "/api/v2/",
        # Alternative paths
        "/api/monitor/system/status",
        "/monitor/system/status",
        # Web interface paths (might give clues)
        "/",
        "/login",
        "/api/v2/monitor/",
    ]

    print("=== Testing Different API Versions and Paths ===\n")

    for endpoint in test_endpoints:
        try:
            print(f"Testing: {endpoint}")
            response = session.make_api_request(endpoint)

            if isinstance(response, dict):
                status_code = response.get("status_code", "Unknown")
                if status_code == 404:
                    print(f"  ❌ 404 Not Found")
                elif status_code == 200 or "results" in response:
                    print(f"  ✅ SUCCESS!")
                    if "results" in response:
                        results = response["results"]
                        if isinstance(results, list):
                            print(f"    - {len(results)} results")
                        elif isinstance(results, dict):
                            print(f"    - Dict with keys: {list(results.keys())}")
                    else:
                        print(f"    - Response keys: {list(response.keys())}")
                elif "error" in response:
                    error = response.get("error", "Unknown")
                    message = response.get("message", "")
                    print(f"  ⚠️  Error: {error}")
                    if "html" not in message.lower():
                        print(f"    - Message: {message[:100]}")
                else:
                    print(f"  ⚠️  Status {status_code}: {list(response.keys())}")
            else:
                print(f"  ⚠️  Non-dict response: {type(response)}")

        except Exception as e:
            print(f"  ❌ Exception: {e}")

        print()


def test_direct_connection():
    """Test direct connection to FortiGate"""
    print("\n=== Testing Direct Connection ===")

    try:
        session = FortiGateSessionManager()

        # Try to get basic system info
        print("1. Testing basic authentication...")

        # Try the most basic endpoint possible
        response = session.make_api_request("/")
        print(f"Root response type: {type(response)}")

        if isinstance(response, dict):
            print(f"Root response keys: {list(response.keys())}")
            if "message" in response:
                message = response["message"]
                if isinstance(message, str) and len(message) > 100:
                    print(f"Message preview: {message[:200]}...")
                else:
                    print(f"Message: {message}")

    except Exception as e:
        print(f"Connection test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_api_versions()
    test_direct_connection()
