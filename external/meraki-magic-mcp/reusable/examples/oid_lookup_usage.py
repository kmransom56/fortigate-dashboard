"""
OID Lookup Usage Examples (No API Key Required)

This module demonstrates how to use the free OID lookup utilities
that don't require API keys or registration.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from reusable.oid_lookup import OIDLookup, decode_device_oid


def example_basic_lookup():
    """Basic OID lookup examples."""
    print("=" * 60)
    print("Basic OID Lookup (No API Key Required)")
    print("=" * 60)
    
    lookup = OIDLookup()
    
    # Example 1: Look up standard SNMP OID
    print("\n1. Looking up sysDescr OID (1.3.6.1.2.1.1.1.0):")
    print("-" * 60)
    result = lookup.lookup("1.3.6.1.2.1.1.1.0")
    if result:
        print(f"Name: {result.get('name')}")
        print(f"Description: {result.get('description')}")
        print(f"Source: {result.get('source')}")
    else:
        print("Not found")
    
    # Example 2: Look up sysUpTime
    print("\n2. Looking up sysUpTime OID (1.3.6.1.2.1.1.3.0):")
    print("-" * 60)
    result = lookup.lookup("1.3.6.1.2.1.1.3.0")
    if result:
        print(f"Name: {result.get('name')}")
        print(f"Source: {result.get('source')}")
    else:
        print("Not found")
    
    # Example 3: Get just the name
    print("\n3. Getting OID name directly:")
    print("-" * 60)
    name = lookup.get_name("1.3.6.1.2.1.1.1.0")
    print(f"Name: {name}")


def example_device_oid_decoding():
    """Examples of decoding device OID strings."""
    print("\n" + "=" * 60)
    print("Device OID Decoding Examples")
    print("=" * 60)
    
    # Example: FortiAP OID-based device name
    # Format: FortiAP-1.16.70.80.50.51.49.70.84.70.50.48.48.50.51.48.52.51
    oid_string = "1.16.70.80.50.51.49.70.84.70.50.48.48.50.51.48.52.51"
    
    print(f"\nDecoding OID string: {oid_string}")
    print("-" * 60)
    
    decoded = decode_device_oid(oid_string, device_type="FortiAP")
    print(f"Decoded: {decoded}")
    
    # Try another example
    print("\nAnother example:")
    oid_string2 = "1.16.70.80.50.50.49.70.84.70.50.48.48.51.53.57.51"
    decoded2 = decode_device_oid(oid_string2, device_type="FortiAP")
    print(f"OID: {oid_string2}")
    print(f"Decoded: {decoded2}")


def example_caching():
    """Example of using caching for OID lookups."""
    print("\n" + "=" * 60)
    print("OID Lookup with Caching")
    print("=" * 60)
    
    # Create lookup with cache
    cache = {}
    lookup = OIDLookup(cache=cache)
    
    print("\nFirst lookup (will query API):")
    import time
    start = time.time()
    result1 = lookup.lookup("1.3.6.1.2.1.1.1.0")
    time1 = time.time() - start
    print(f"Time: {time1:.2f}s, Result: {result1.get('name') if result1 else 'None'}")
    
    print("\nSecond lookup (from cache):")
    start = time.time()
    result2 = lookup.lookup("1.3.6.1.2.1.1.1.0")
    time2 = time.time() - start
    print(f"Time: {time2:.4f}s, Result: {result2.get('name') if result2 else 'None'}")
    print(f"Cache size: {len(cache)} entries")


def example_multiple_oids():
    """Example of looking up multiple OIDs."""
    print("\n" + "=" * 60)
    print("Multiple OID Lookups")
    print("=" * 60)
    
    lookup = OIDLookup()
    
    test_oids = [
        "1.3.6.1.2.1.1.1.0",  # sysDescr
        "1.3.6.1.2.1.1.3.0",  # sysUpTime
        "1.3.6.1.2.1.2.2.1.2",  # ifDescr
        "1.3.6.1.2.1.1.5.0",  # sysName
    ]
    
    print("\nLooking up multiple OIDs:")
    for oid in test_oids:
        result = lookup.lookup(oid)
        if result:
            print(f"  {oid}: {result.get('name')} ({result.get('source')})")
        else:
            print(f"  {oid}: Not found")


if __name__ == "__main__":
    # Run examples
    example_basic_lookup()
    example_device_oid_decoding()
    example_caching()
    example_multiple_oids()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nKey advantages of this approach:")
    print("✅ No API key required")
    print("✅ Free to use")
    print("✅ Multiple fallback sources")
    print("✅ Local caching support")
    print("✅ Works offline (with cached data)")
