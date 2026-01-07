#!/usr/bin/env python3
"""
FortiGuard Historical PSIRT Scraper with Zscaler Certificate Support
Uses Zscaler certificate to resolve SSL issues in corporate environments
"""

import requests
import json
import time
import re
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import concurrent.futures
from threading import Lock

class ZscalerFortiGuardScraper:
    def __init__(self):
        self.base_url = "https://fortiguard.fortinet.com/psirt"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Set up Zscaler certificate
        zscaler_cert_path = os.path.join(os.path.dirname(__file__), 'zscaler_root.crt')
        if os.path.exists(zscaler_cert_path):
            self.session.verify = zscaler_cert_path
            print(f"Using Zscaler certificate: {zscaler_cert_path}")
        else:
            print("Warning: Zscaler certificate not found, disabling SSL verification")
            self.session.verify = False
            # Suppress SSL warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.found_advisories = []
        self.lock = Lock()
        
    def test_connection(self):
        """Test if we can connect to FortiGuard with current SSL settings"""
        test_urls = [
            "https://fortiguard.fortinet.com/psirt/FG-IR-25-006",  # Known to exist from RSS
            "https://fortiguard.fortinet.com/psirt/FG-IR-24-001",  # Test 2024 advisory
        ]
        
        print("Testing FortiGuard connectivity with Zscaler certificate...")
        
        for url in test_urls:
            try:
                response = self.session.get(url, timeout=10)
                print(f"✓ {url} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    title = soup.find('h1')
                    if title:
                        print(f"  Title: {title.get_text(strip=True)[:80]}...")
                        return True  # Success!
                elif response.status_code == 404:
                    print("  Advisory not found (404) - but connection works!")
                    
            except Exception as e:
                print(f"✗ {url} - Error: {e}")
                return False
        
        return True
    
    def check_advisory_exists(self, advisory_id):
        """Check if a specific advisory ID exists and extract its data"""
        url = f"{self.base_url}/{advisory_id}"
        
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 404:
                return None
                
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract advisory data
            advisory_data = {
                'advisory_id': advisory_id,
                'url': url,
                'status_code': response.status_code,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract title - try multiple selectors
            title_selectors = [
                'h1', 'h2', '.title', '#title', 
                '[class*="title"]', '.page-title',
                '.advisory-title', '.psirt-title'
            ]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    advisory_data['title'] = title_elem.get_text(strip=True)
                    break
            
            # If no title found, try getting it from page text
            if 'title' not in advisory_data:
                page_text = soup.get_text()
                # Look for advisory ID followed by title pattern
                title_match = re.search(rf'{advisory_id}[:\s-]+([^\n\r]+)', page_text)
                if title_match:
                    advisory_data['title'] = title_match.group(1).strip()
            
            # Extract published date
            page_text = soup.get_text()
            date_patterns = [
                r'Published[:\s]+(\d{4}-\d{2}-\d{2})',
                r'Date[:\s]+(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2})',
                r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, page_text)
                if match:
                    try:
                        parsed_date = date_parser.parse(match.group(1))
                        advisory_data['published'] = parsed_date.isoformat()
                        advisory_data['published_raw'] = match.group(1)
                        break
                    except:
                        continue
            
            # Extract CVE ID
            cve_match = re.search(r'CVE-\d{4}-\d+', page_text)
            if cve_match:
                advisory_data['cve_id'] = cve_match.group(0)
            
            # Extract summary/description
            content_selectors = [
                '.content', '.description', '.summary', 
                'article', 'main', '[class*="content"]',
                '.advisory-content', '.psirt-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    text = content_elem.get_text(strip=True)
                    if len(text) > 100:  # Only substantial content
                        advisory_data['summary'] = text[:1000]  # First 1000 chars
                        break
            
            # If we found meaningful data, return it
            if advisory_data.get('title') or advisory_data.get('published') or len(page_text) > 1000:
                return advisory_data
                
            return None
            
        except Exception as e:
            # For debugging, print first few errors
            if hasattr(self, '_error_count'):
                self._error_count += 1
            else:
                self._error_count = 1
            
            if self._error_count <= 3:
                print(f"Error checking {advisory_id}: {e}")
            
            return None
    
    def generate_advisory_ids(self, start_year=2022, end_year=None):
        """Generate potential advisory IDs based on FortiGuard's naming pattern"""
        if end_year is None:
            end_year = datetime.now().year
        
        advisory_ids = []
        
        # FortiGuard uses pattern: FG-IR-YY-NNN
        for year in range(start_year, end_year + 1):
            year_suffix = str(year)[-2:]  # Last 2 digits
            
            # Start with smaller ranges to test, then expand
            max_num = 200 if year < 2024 else 300  # More recent years might have more
            
            for num in range(1, max_num + 1):
                advisory_id = f"FG-IR-{year_suffix}-{num:03d}"
                advisory_ids.append(advisory_id)
        
        return advisory_ids
    
    def scan_advisory_batch(self, advisory_ids):
        """Scan a batch of advisory IDs"""
        found_in_batch = []
        
        for advisory_id in advisory_ids:
            advisory_data = self.check_advisory_exists(advisory_id)
            if advisory_data:
                found_in_batch.append(advisory_data)
                title = advisory_data.get('title', 'No title')[:60]
                print(f"✓ Found: {advisory_id} - {title}...")
            
            # Small delay to be respectful
            time.sleep(0.2)
        
        # Thread-safe addition to main list
        with self.lock:
            self.found_advisories.extend(found_in_batch)
        
        return len(found_in_batch)
    
    def scan_historical_advisories(self, start_year=2022, max_workers=2):
        """Scan for historical advisories using multiple threads"""
        print(f"Starting historical scan from {start_year} to {datetime.now().year}")
        print("Using Zscaler certificate for SSL connections...")
        
        # Test connection first
        if not self.test_connection():
            print("❌ Connection test failed. Cannot proceed with historical scan.")
            return []
        
        print("✅ Connection test successful! Proceeding with historical scan...")
        
        # Generate all potential advisory IDs
        all_advisory_ids = self.generate_advisory_ids(start_year)
        print(f"Generated {len(all_advisory_ids)} potential advisory IDs to check")
        
        # Split into batches for parallel processing
        batch_size = 10  # Smaller batches to be more respectful
        batches = [all_advisory_ids[i:i+batch_size] for i in range(0, len(all_advisory_ids), batch_size)]
        
        print(f"Processing in {len(batches)} batches with {max_workers} workers...")
        
        start_time = time.time()
        total_found = 0
        
        # Process batches with thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {executor.submit(self.scan_advisory_batch, batch): i 
                             for i, batch in enumerate(batches)}
            
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    found_count = future.result()
                    total_found += found_count
                    
                    if (batch_num + 1) % 5 == 0:  # Progress update every 5 batches
                        elapsed = time.time() - start_time
                        rate = (batch_num + 1) / elapsed * 60 if elapsed > 0 else 0
                        print(f"Progress: {batch_num + 1}/{len(batches)} batches, "
                              f"{total_found} advisories found, "
                              f"{rate:.1f} batches/min")
                        
                except Exception as e:
                    print(f"Batch {batch_num} failed: {e}")
        
        elapsed = time.time() - start_time
        print(f"\nScan complete!")
        print(f"Total time: {elapsed:.1f} seconds")
        print(f"Total advisories found: {len(self.found_advisories)}")
        
        return self.found_advisories
    
    def save_advisories(self, advisories, filename=None):
        """Save advisories to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fortiguard_zscaler_advisories_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(advisories, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(advisories)} advisories to {filename}")
        return filename

def main():
    scraper = ZscalerFortiGuardScraper()
    
    print("FortiGuard Historical PSIRT Scraper (Zscaler Compatible)")
    print("======================================================")
    print("This version uses your Zscaler certificate to resolve SSL issues")
    print()
    
    # Start with a quick test
    print("Step 1: Testing connection...")
    if not scraper.test_connection():
        print("❌ Cannot connect to FortiGuard. Please check your network/certificates.")
        return
    
    print("✅ Connection successful!")
    print()
    
    # Configuration
    start_year = 2022
    max_workers = 2  # Conservative to avoid overwhelming
    
    print(f"Configuration:")
    print(f"  Start year: {start_year}")
    print(f"  Max workers: {max_workers}")
    print(f"  Target: Historical advisories from past 3 years")
    print()
    
    # Start the historical scan
    advisories = scraper.scan_historical_advisories(start_year=start_year, max_workers=max_workers)
    
    if advisories:
        # Filter to last 3 years
        three_years_ago = datetime.now() - timedelta(days=3*365)
        recent_advisories = []
        
        for advisory in advisories:
            if advisory.get('published'):
                try:
                    pub_date = date_parser.parse(advisory['published'])
                    if pub_date.replace(tzinfo=None) >= three_years_ago:
                        recent_advisories.append(advisory)
                except:
                    recent_advisories.append(advisory)  # Include if can't parse date
            else:
                recent_advisories.append(advisory)  # Include if no date
        
        print(f"\nFiltered to last 3 years: {len(recent_advisories)} advisories")
        
        # Save results
        filename = scraper.save_advisories(recent_advisories)
        
        # Show summary
        print(f"\n=== SUMMARY ===")
        print(f"Total advisories found: {len(recent_advisories)}")
        
        # Group by year
        years = {}
        for advisory in recent_advisories:
            if advisory.get('published'):
                try:
                    year = date_parser.parse(advisory['published']).year
                    years[year] = years.get(year, 0) + 1
                except:
                    years['Unknown'] = years.get('Unknown', 0) + 1
            else:
                years['Unknown'] = years.get('Unknown', 0) + 1
        
        print("\nAdvisories by year:")
        for year in sorted(years.keys()):
            print(f"  {year}: {years[year]}")
        
        # Show CVEs
        cves = [adv.get('cve_id') for adv in recent_advisories if adv.get('cve_id')]
        print(f"\nCVEs found: {len(cves)}")
        for cve in cves[:10]:  # Show first 10
            print(f"  {cve}")
        
        print(f"\nData saved to: {filename}")
        print(f"To convert to readable formats: python json_to_readable.py {filename}")
        
    else:
        print("No advisories found.")

if __name__ == "__main__":
    main()
