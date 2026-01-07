#!/usr/bin/env python3
"""
Create a certificate bundle that combines Zscaler certificate with standard CA certificates
"""

import os
import requests
import certifi

def create_zscaler_cert_bundle():
    """Create a certificate bundle that includes Zscaler + standard CAs"""
    
    # Get the path to the standard CA bundle
    standard_ca_bundle = certifi.where()
    
    # Path to Zscaler certificate
    zscaler_cert_path = os.path.join(os.path.dirname(__file__), 'zscaler_root.crt')
    
    # Output bundle path
    combined_bundle_path = os.path.join(os.path.dirname(__file__), 'zscaler_combined_bundle.crt')
    
    print(f"Creating combined certificate bundle...")
    print(f"Standard CA bundle: {standard_ca_bundle}")
    print(f"Zscaler certificate: {zscaler_cert_path}")
    print(f"Output bundle: {combined_bundle_path}")
    
    if not os.path.exists(zscaler_cert_path):
        print(f"ERROR: Zscaler certificate not found at {zscaler_cert_path}")
        return None
    
    try:
        # Read the standard CA bundle
        with open(standard_ca_bundle, 'r', encoding='utf-8') as f:
            standard_cas = f.read()
        
        # Read the Zscaler certificate
        with open(zscaler_cert_path, 'r', encoding='utf-8') as f:
            zscaler_cert = f.read()
        
        # Combine them (Zscaler first, then standard CAs)
        combined_bundle = zscaler_cert + '\n' + standard_cas
        
        # Write the combined bundle
        with open(combined_bundle_path, 'w', encoding='utf-8') as f:
            f.write(combined_bundle)
        
        print(f"SUCCESS: Created combined certificate bundle")
        print(f"Bundle contains {combined_bundle.count('-----BEGIN CERTIFICATE-----')} certificates")
        
        return combined_bundle_path
        
    except Exception as e:
        print(f"ERROR creating certificate bundle: {e}")
        return None

def test_bundle(bundle_path):
    """Test the certificate bundle with a simple request"""
    print(f"\nTesting certificate bundle...")
    
    session = requests.Session()
    session.verify = bundle_path
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    test_urls = [
        "https://www.google.com",  # Should work with standard CAs
        "https://fortiguard.fortinet.com/rss/ir.xml",  # Should work with Zscaler
    ]
    
    for url in test_urls:
        try:
            response = session.get(url, timeout=10)
            print(f"SUCCESS: {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"ERROR: {url} - Error: {e}")

if __name__ == "__main__":
    bundle_path = create_zscaler_cert_bundle()
    if bundle_path:
        test_bundle(bundle_path)
