#!/usr/bin/env python3
"""
Test Advisory Access and Content Extraction
===========================================

This script tests access to FortiGuard advisories and diagnoses
content extraction issues.
"""

# Apply SSL fixes FIRST
import ssl_universal_fix
ssl_universal_fix.apply_all_ssl_fixes(verbose=True)

import requests
import time
from bs4 import BeautifulSoup

def test_advisory_access():
    """Test access to a known advisory"""
    print("\nTesting Advisory Access")
    print("=" * 30)
    
    # Test URLs - some known to exist
    test_urls = [
        "https://fortiguard.fortinet.com/psirt/FG-IR-25-006",  # Recent, likely exists
        "https://fortiguard.fortinet.com/psirt/FG-IR-24-001",  # 2024
        "https://fortiguard.fortinet.com/psirt/FG-IR-23-001",  # 2023
        "https://fortiguard.fortinet.com/psirt/FG-IR-22-047",  # 2022 - mentioned in scraper output
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        try:
            response = session.get(url, timeout=15)
            print(f"  Status: {response.status_code}")
            print(f"  Content length: {len(response.text)}")
            
            if response.status_code == 200:
                # Parse content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for title
                title_elem = soup.find('h1')
                if title_elem:
                    title = title_elem.get_text().strip()
                    print(f"  Title: {title[:100]}...")
                else:
                    print("  Title: Not found")
                
                # Look for common FortiGuard elements
                if "fortiguard" in response.text.lower():
                    print("  ✓ Contains FortiGuard content")
                else:
                    print("  ✗ No FortiGuard content detected")
                
                # Check for advisory-specific content
                if "advisory" in response.text.lower():
                    print("  ✓ Contains advisory content")
                else:
                    print("  ✗ No advisory content detected")
                
                # Check for CVE
                if "cve-" in response.text.lower():
                    print("  ✓ Contains CVE references")
                else:
                    print("  ✗ No CVE references found")
                
                # Check if it's a redirect/landing page
                if "explore latest research" in response.text.lower():
                    print("  ⚠️ Appears to be a landing/redirect page")
                
                # Show first 200 chars of text content
                text_content = soup.get_text()[:200].strip()
                print(f"  First 200 chars: {text_content}...")
                
            else:
                print(f"  ✗ Failed with status {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}...")
        
        time.sleep(2)  # Be nice to the server

def test_rss_feed():
    """Test RSS feed access"""
    print("\n\nTesting RSS Feed Access")
    print("=" * 30)
    
    rss_url = "https://fortiguard.fortinet.com/rss/ir.xml"
    
    try:
        session = requests.Session()
        response = session.get(rss_url, timeout=15)
        print(f"RSS Status: {response.status_code}")
        print(f"RSS Content length: {len(response.text)}")
        
        if response.status_code == 200:
            # Parse RSS
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            items = root.findall('.//item')
            print(f"RSS Items found: {len(items)}")
            
            if items:
                for i, item in enumerate(items[:3]):  # Show first 3
                    title = item.find('title')
                    link = item.find('link')
                    if title is not None and link is not None:
                        print(f"  [{i+1}] {title.text}")
                        print(f"      {link.text}")
        
    except Exception as e:
        print(f"RSS Error: {e}")

if __name__ == "__main__":
    test_advisory_access()
    test_rss_feed()
