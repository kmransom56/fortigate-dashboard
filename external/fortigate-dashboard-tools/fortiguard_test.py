#!/usr/bin/env python3
"""
Quick test to verify FortiGuard advisory access
"""

import requests
import time
from bs4 import BeautifulSoup

def test_fortiguard_access():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    session.verify = False
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Test a few known advisory patterns
    test_urls = [
        "https://fortiguard.fortinet.com/psirt/FG-IR-24-001",
        "https://fortiguard.fortinet.com/psirt/FG-IR-24-002", 
        "https://fortiguard.fortinet.com/psirt/FG-IR-24-003",
        "https://fortiguard.fortinet.com/psirt/FG-IR-23-001",
        "https://fortiguard.fortinet.com/psirt/FG-IR-25-001",
        "https://fortiguard.fortinet.com/psirt/FG-IR-25-006"  # We know this exists from RSS
    ]
    
    print("Testing FortiGuard advisory access...")
    print("=" * 50)
    
    for url in test_urls:
        try:
            print(f"Testing: {url}")
            response = session.get(url, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('h1')
                if title:
                    print(f"  Title: {title.get_text(strip=True)[:80]}...")
                    print("  ✓ FOUND VALID ADVISORY!")
                else:
                    print("  - No title found")
            elif response.status_code == 404:
                print("  - Not found (404)")
            else:
                print(f"  - Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"  - Error: {e}")
        
        print()
        time.sleep(1)  # Be respectful
    
    print("Test complete!")

if __name__ == "__main__":
    test_fortiguard_access()
