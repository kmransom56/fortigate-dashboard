#!/usr/bin/env python3
"""
Test script for FortiGate session authentication
"""

import sys

sys.path.append(".")

from app.services.fortigate_session import get_session_manager
from app.services.fortigate_service import get_interfaces


def test_session_authentication():
    """Test FortiGate session authentication"""
    print("Testing FortiGate Session Authentication")
    print("=" * 50)

    # Test session manager
    session_manager = get_session_manager()

    print(f"FortiGate IP: {session_manager.fortigate_ip}")
    print(f"Username: {session_manager.username}")
    print(f"Password loaded: {'Yes' if session_manager.password else 'No'}")

    # Try to login
    print("\nAttempting to login...")
    success = session_manager.login()

    if success:
        print("✅ Login successful!")
        print(
            f"Session key: {session_manager.session_key[:20]}..."
            if session_manager.session_key
            else "None"
        )
        print(f"Session expires: {session_manager.session_expires}")

        # Test API call
        print("\nTesting API call...")
        result = session_manager.make_api_request("cmdb/system/interface")

        if "error" in result:
            print(f"❌ API call failed: {result}")
        else:
            print(
                f"✅ API call successful! Retrieved {len(result.get('results', []))} interfaces"
            )

        # Test through service
        print("\nTesting through service...")
        interfaces = get_interfaces()
        print(f"✅ Service returned {len(interfaces)} interfaces")

        # Logout
        session_manager.logout()
        print("✅ Logged out successfully")

    else:
        print("❌ Login failed!")
        print("This could be due to:")
        print("- Incorrect credentials")
        print("- Network connectivity issues")
        print("- FortiGate not accessible")
        print("- FortiGate doesn't support session authentication")


if __name__ == "__main__":
    test_session_authentication()
