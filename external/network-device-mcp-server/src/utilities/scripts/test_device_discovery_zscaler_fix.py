"""
Test script for enhanced device discovery tool with curl-based MAC lookup
Focuses on testing both Hikvision device detection and general MAC lookup functionality
"""

import sys
import json
from device_discovery_tool_zscaler_fix import DeviceDiscovery, batch_mac_lookup, CurlBasedMacLookup

def test_hikvision_detection():
    """
    Test specifically for Hikvision device detection
    """
    print("\n==== TESTING HIKVISION DEVICE DETECTION ====")
    print("=" * 50)
    
    discovery = DeviceDiscovery()
    
    # Test MAC addresses including Hikvision
    test_macs = [
        "18:66:da:2a:81:1e",  # Hikvision
        "18:66:da:3b:42:5f",  # Another Hikvision
        "00:50:f2:01:02:03",  # Microsoft
        "00:1b:63:aa:bb:cc",  # Apple
    ]
    
    for mac in test_macs:
        print(f"\nTesting MAC: {mac}")
        
        # Test vendor detection
        vendor = discovery.get_mac_vendor(mac)
        print(f"→ Vendor: {vendor}")
        
        # Test device type identification
        device_info = {
            'mac_address': mac,
            'vendor': vendor,
            'responsive': False
        }
        
        device_type = discovery.identify_device_type(device_info)
        print(f"→ Device Type: {device_type}")
        
        # Test risk assessment
        device_info['identified_type'] = device_type
        risk_level = discovery.get_device_risk_level(device_info)
        print(f"→ Migration Risk: {risk_level}")
        
        # Validate Hikvision detection
        if mac.startswith("18:66:da"):
            if "hikvision" in vendor.lower():
                print("✓ PASS: Correctly identified Hikvision vendor")
            else:
                print("✗ FAIL: Did not identify Hikvision vendor")
                
            if "hikvision" in device_type.lower():
                print("✓ PASS: Correctly identified as Hikvision device type")
            else:
                print("✗ FAIL: Did not identify Hikvision device type")
                
            if risk_level == "LOW - Device Not Responsive":
                print("✓ PASS: Correctly assessed non-responsive Hikvision risk")
            else:
                print("✗ FAIL: Incorrect risk assessment for non-responsive Hikvision")

def test_curl_mac_lookup():
    """
    Test the curl-based MAC lookup functionality
    """
    print("\n==== TESTING CURL-BASED MAC LOOKUP ====")
    print("=" * 50)
    
    curl_lookup = CurlBasedMacLookup()
    
    if not curl_lookup.curl_available:
        print("❌ Curl is not available on this system. Skipping curl tests.")
        return
    
    print("✅ Curl is available on this system.")
    
    # Test with a few MAC addresses
    test_macs = [
        "44:38:39:ff:ef:57",  # Cumulus Networks
        "00:18:7d:19:36:ce",  # TP-Link
        "18:66:da:2a:81:1e",  # Hikvision (our target)
        "AA:BB:CC:DD:EE:FF",  # Unknown MAC
    ]
    
    for mac in test_macs:
        print(f"\nTesting curl lookup for MAC: {mac}")
        result = curl_lookup.curl_api_lookup(mac)
        if result:
            print(f"✅ Found via curl: {result}")
        else:
            print(f"❌ Not found via curl")

def test_batch_lookup():
    """
    Test the batch lookup functionality
    """
    print("\n==== TESTING BATCH MAC LOOKUP ====")
    print("=" * 50)
    
    # List of test MAC addresses
    test_macs = [
        "18:66:da:2a:81:1e",  # Hikvision
        "18:66:da:3b:42:5f",  # Another Hikvision with same OUI
        "00:50:f2:01:02:03",  # Microsoft
        "00:1b:63:aa:bb:cc",  # Apple
        "44:38:39:ff:ef:57",  # Cumulus Networks
        "00:18:7d:19:36:ce",  # TP-Link
    ]
    
    print(f"Performing batch lookup of {len(test_macs)} MAC addresses...")
    results = batch_mac_lookup(test_macs)
    
    print("\nBatch lookup results:")
    for mac, vendor in results.items():
        print(f"{mac} → {vendor}")
    
    # Verify Hikvision detection in batch
    hikvision_macs = [mac for mac in test_macs if mac.startswith("18:66:da")]
    for mac in hikvision_macs:
        if mac in results and "hikvision" in results[mac].lower():
            print(f"✓ PASS: Correctly identified {mac} as Hikvision in batch")
        else:
            print(f"✗ FAIL: Did not identify {mac} as Hikvision in batch")

def main():
    """
    Main test function
    """
    print("DEVICE DISCOVERY TOOL TEST (ZSCALER FIX VERSION)")
    print("=" * 50)
    
    # Run all tests
    test_hikvision_detection()
    test_curl_mac_lookup()
    test_batch_lookup()
    
    print("\n==== TEST SUMMARY ====")
    print("=" * 50)
    print("✓ Tested Hikvision device detection")
    print("✓ Tested curl-based MAC lookup")
    print("✓ Tested batch MAC lookup")
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()
