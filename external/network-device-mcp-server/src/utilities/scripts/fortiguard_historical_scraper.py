#!/usr/bin/env python3
"""
FortiGuard Historical PSIRT Scraper
Bypasses RSS feed limitations to get true historical coverage
Uses systematic URL enumeration to discover advisories from the past 3 years
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import concurrent.futures
from threading import Lock

class FortiGuardHistoricalScraper:
    def __init__(self):
        self.base_url = "https://fortiguard.fortinet.com/psirt"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.verify = False
        
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.found_advisories = []
        self.lock = Lock()
        
    def check_advisory_exists(self, advisory_id):
        """Check if a specific advisory ID exists and extract its data"""
        url = f"{self.base_url}/{advisory_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            
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
            
            # Extract title
            title_selectors = ['h1', 'h2', '.title', '#title', '[class*="title"]']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    advisory_data['title'] = title_elem.get_text(strip=True)
                    break
            
            # Extract published date
            date_patterns = [
                r'Published[:\s]+([0-9]{4}-[0-9]{2}-[0-9]{2})',
                r'Date[:\s]+([0-9]{4}-[0-9]{2}-[0-9]{2})',
                r'([0-9]{4}-[0-9]{2}-[0-9]{2})',
                r'([A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4})'
            ]
            
            page_text = soup.get_text()
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
                'article', 'main', '[class*="content"]'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    text = content_elem.get_text(strip=True)
                    if len(text) > 100:  # Only substantial content
                        advisory_data['summary'] = text[:1000]  # First 1000 chars
                        break
            
            # If we found meaningful data, return it
            if advisory_data.get('title') or advisory_data.get('published'):
                return advisory_data
                
            return None
            
        except Exception as e:
            # Silently skip errors for bulk scanning
            return None
    
    def generate_advisory_ids(self, start_year=2022, end_year=None):
        """Generate potential advisory IDs based on FortiGuard's naming pattern"""
        if end_year is None:
            end_year = datetime.now().year
        
        advisory_ids = []
        
        # FortiGuard uses pattern: FG-IR-YY-NNN
        for year in range(start_year, end_year + 1):
            year_suffix = str(year)[-2:]  # Last 2 digits
            
            # Most years have 1-300 advisories, but we'll check more to be thorough
            for num in range(1, 400):
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
                print(f"✓ Found: {advisory_id} - {advisory_data.get('title', 'No title')[:60]}...")
            
            # Small delay to be respectful
            time.sleep(0.1)
        
        # Thread-safe addition to main list
        with self.lock:
            self.found_advisories.extend(found_in_batch)
        
        return len(found_in_batch)
    
    def scan_historical_advisories(self, start_year=2022, max_workers=5):
        """Scan for historical advisories using multiple threads"""
        print(f"Starting historical scan from {start_year} to {datetime.now().year}")
        print("This will systematically check FortiGuard advisory URLs...")
        print("Note: This may take 10-30 minutes depending on how many advisories exist")
        
        # Generate all potential advisory IDs
        all_advisory_ids = self.generate_advisory_ids(start_year)
        print(f"Generated {len(all_advisory_ids)} potential advisory IDs to check")
        
        # Split into batches for parallel processing
        batch_size = 20
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
                    
                    if (batch_num + 1) % 10 == 0:  # Progress update every 10 batches
                        elapsed = time.time() - start_time
                        print(f"Progress: {batch_num + 1}/{len(batches)} batches, "
                              f"{total_found} advisories found, "
                              f"{elapsed:.1f}s elapsed")
                        
                except Exception as e:
                    print(f"Batch {batch_num} failed: {e}")
        
        elapsed = time.time() - start_time
        print(f"\nScan complete!")
        print(f"Total time: {elapsed:.1f} seconds")
        print(f"Total advisories found: {len(self.found_advisories)}")
        
        return self.found_advisories
    
    def filter_by_date_range(self, advisories, start_date=None, end_date=None):
        """Filter advisories by date range"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=3*365)
        if end_date is None:
            end_date = datetime.now()
        
        filtered = []
        for advisory in advisories:
            if advisory.get('published'):
                try:
                    pub_date = date_parser.parse(advisory['published'])
                    if pub_date.replace(tzinfo=None) >= start_date and pub_date.replace(tzinfo=None) <= end_date:
                        filtered.append(advisory)
                except:
                    # Include if we can't parse the date
                    filtered.append(advisory)
            else:
                # Include if no date available
                filtered.append(advisory)
        
        return filtered
    
    def save_advisories(self, advisories, filename=None):
        """Save advisories to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fortiguard_historical_advisories_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(advisories, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(advisories)} advisories to {filename}")
        return filename

def main():
    scraper = FortiGuardHistoricalScraper()
    
    print("FortiGuard Historical PSIRT Scraper")
    print("===================================")
    print("This tool bypasses RSS feed limitations to get true historical coverage")
    print("Automatically scanning for 3-year historical data...")
    print()
    
    # Use sensible defaults for automated 3-year scan
    start_year = 2022
    max_workers = 3  # Conservative to avoid overwhelming the server
    
    print(f"Configuration:")
    print(f"  Start year: {start_year}")
    print(f"  Max workers: {max_workers}")
    print(f"  Target: Last 3 years of advisories")
    print()
    
    # Start the historical scan
    advisories = scraper.scan_historical_advisories(start_year=start_year, max_workers=max_workers)
    
    if advisories:
        # Filter to last 3 years
        three_years_ago = datetime.now() - timedelta(days=3*365)
        recent_advisories = scraper.filter_by_date_range(advisories, start_date=three_years_ago)
        
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
        
        print("\nAdvisories by year:")
        for year in sorted(years.keys()):
            print(f"  {year}: {years[year]}")
        
        # Show CVEs
        cves = [adv.get('cve_id') for adv in recent_advisories if adv.get('cve_id')]
        print(f"\nCVEs found: {len(cves)}")
        
        print(f"\nData saved to: {filename}")
        print(f"To convert to readable formats: python json_to_readable.py {filename}")
        
    else:
        print("No advisories found.")

if __name__ == "__main__":
    main()
