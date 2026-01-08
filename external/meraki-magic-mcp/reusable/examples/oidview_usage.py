"""
OidView MIB API Usage Examples

This module demonstrates how to use the OidView MIB API client
for network device OID decoding and MIB information retrieval.

Prerequisites:
    - OidView API key (sign up at https://www.oidview.com/api/api.html)
    - Set OIDVIEW_API_KEY environment variable or pass to client
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from reusable.oidview_client import OidViewClient


def example_basic_usage():
    """Basic usage examples without API key (limited functionality)."""
    print("=" * 60)
    print("Basic OidView API Usage Examples")
    print("=" * 60)
    
    # Initialize client (works without API key for some endpoints)
    client = OidViewClient()
    
    # Example 1: Get MIB object info by OID
    print("\n1. Getting MIB object info for sysDescr OID:")
    print("-" * 60)
    try:
        result = client.get_mib_object_info(oid="1.3.6.1.2.1.1.1.0")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Some endpoints may require an API key")
    
    # Example 2: Get MIB object info by name
    print("\n2. Getting MIB object info by name 'sysDescr':")
    print("-" * 60)
    try:
        result = client.get_mib_object_info_by_name(name="sysDescr", vendor="RFC1213")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")


def example_with_api_key():
    """Examples using API key for full functionality."""
    print("\n" + "=" * 60)
    print("OidView API Usage with API Key")
    print("=" * 60)
    
    # Get API key from environment or use placeholder
    api_key = os.getenv('OIDVIEW_API_KEY', 'your-api-key-here')
    
    if api_key == 'your-api-key-here':
        print("\n⚠️  Warning: Using placeholder API key.")
        print("Set OIDVIEW_API_KEY environment variable for full functionality.")
        print("Sign up at: https://www.oidview.com/api/api.html\n")
    
    client = OidViewClient(api_key=api_key)
    
    # Example 1: Get all vendors
    print("\n1. Getting list of all vendors:")
    print("-" * 60)
    try:
        vendors = client.get_vendors()
        print(f"Found {len(vendors) if isinstance(vendors, list) else 'N/A'} vendors")
        if isinstance(vendors, list) and len(vendors) > 0:
            print(f"Sample vendors: {vendors[:5]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Get Fortinet vendor info
    print("\n2. Getting Fortinet vendor information:")
    print("-" * 60)
    try:
        vendor_info = client.get_vendor_info(vendor="Fortinet")
        print(f"Vendor Info: {vendor_info}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Get Fortinet MIBs
    print("\n3. Getting Fortinet MIBs:")
    print("-" * 60)
    try:
        mibs = client.get_vendor_mibs(vendor="Fortinet")
        print(f"Found {len(mibs) if isinstance(mibs, list) else 'N/A'} MIBs")
        if isinstance(mibs, list) and len(mibs) > 0:
            print(f"Sample MIBs: {mibs[:5]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: Decode OID to name
    print("\n4. Decoding OID to MIB object name:")
    print("-" * 60)
    test_oids = [
        "1.3.6.1.2.1.1.1.0",  # sysDescr
        "1.3.6.1.2.1.1.3.0",  # sysUpTime
        "1.3.6.1.2.1.2.2.1.2",  # ifDescr
    ]
    
    for oid in test_oids:
        try:
            name = client.decode_oid_to_name(oid)
            desc = client.get_oid_description(oid)
            print(f"OID {oid}:")
            print(f"  Name: {name}")
            print(f"  Description: {desc}")
        except Exception as e:
            print(f"OID {oid}: Error - {e}")
    
    # Example 5: Search MIB objects
    print("\n5. Searching Fortinet MIB objects for 'system':")
    print("-" * 60)
    try:
        results = client.search_mib_objects_by_vendor(vendor="Fortinet", token="system")
        print(f"Found {len(results) if isinstance(results, list) else 'N/A'} results")
        if isinstance(results, list) and len(results) > 0:
            print(f"Sample results: {results[:3]}")
    except Exception as e:
        print(f"Error: {e}")


def example_oid_decoding_integration():
    """Example of integrating OidView API with OID decoding."""
    print("\n" + "=" * 60)
    print("OID Decoding Integration Example")
    print("=" * 60)
    
    api_key = os.getenv('OIDVIEW_API_KEY')
    if not api_key:
        print("⚠️  OIDVIEW_API_KEY not set. Skipping integration example.")
        return
    
    client = OidViewClient(api_key=api_key)
    
    # Example: Decode a FortiAP OID-based device name
    # Format: FortiAP-1.16.70.80.50.51.49.70.84.70.50.48.48.50.51.48.52.51
    oid_string = "1.16.70.80.50.51.49.70.84.70.50.48.48.50.51.48.52.51"
    
    print(f"\nDecoding OID string: {oid_string}")
    print("-" * 60)
    
    # Try to decode each numeric part as ASCII
    decoded = ""
    for part in oid_string.split("."):
        if part.isdigit():
            num = int(part)
            if 32 <= num <= 126:  # Printable ASCII range
                decoded += chr(num)
            else:
                decoded += f".{part}"
    
    print(f"Decoded string: {decoded}")
    
    # Try to get MIB information for related OIDs
    print("\nAttempting to get MIB info for related OIDs:")
    related_oids = [
        "1.3.6.1.4.1.12356",  # Fortinet enterprise OID
        "1.3.6.1.2.1.1.1.0",  # sysDescr
    ]
    
    for oid in related_oids:
        try:
            info = client.get_mib_object_info(oid)
            print(f"\nOID {oid}:")
            print(f"  Info: {info}")
        except Exception as e:
            print(f"OID {oid}: Error - {e}")


if __name__ == "__main__":
    # Run examples
    example_basic_usage()
    example_with_api_key()
    example_oid_decoding_integration()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nTo use the OidView API:")
    print("1. Sign up at: https://www.oidview.com/api/api.html")
    print("2. Get your API key")
    print("3. Set environment variable: export OIDVIEW_API_KEY='your-key'")
    print("4. Use the OidViewClient in your code")
