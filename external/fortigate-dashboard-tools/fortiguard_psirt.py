#!/usr/bin/env python3
"""
FortiGuard PSIRT Advisory Downloader
Downloads and processes PSIRT advisories from FortiGuard RSS feed
"""

import requests
import feedparser
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
from dateutil import parser as date_parser
import re

class PSIRTDownloader:
    def __init__(self):
        self.rss_url = "https://www.fortiguard.com/rss/ir.xml"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Disable SSL verification for corporate environments
        self.session.verify = False
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def fetch_rss_feed(self):
        """Fetch and parse the RSS feed"""
        try:
            response = self.session.get(self.rss_url, timeout=30, verify=False)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            return feed
        except Exception as e:
            print(f"Error fetching RSS feed: {e}")
            return None
    
    def extract_advisory_details(self, entry):
        """Extract details from RSS entry"""
        return {
            'title': entry.get('title', ''),
            'link': entry.get('link', ''),
            'published': entry.get('published', ''),
            'summary': entry.get('summary', ''),
            'id': entry.get('id', ''),
            'cve_id': self.extract_cve_id(entry.get('title', '')),
            'advisory_id': self.extract_advisory_id(entry.get('link', ''))
        }
    
    def extract_cve_id(self, title):
        """Extract CVE ID from title"""
        import re
        cve_match = re.search(r'CVE-\d{4}-\d+', title)
        return cve_match.group(0) if cve_match else None
    
    def extract_advisory_id(self, link):
        """Extract advisory ID from link"""
        import re
        advisory_match = re.search(r'FG-IR-\d{2}-\d+', link)
        return advisory_match.group(0) if advisory_match else None
    
    def download_advisory_content(self, advisory_url):
        """Download detailed content from advisory page"""
        try:
            response = self.session.get(advisory_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract structured data from the advisory page
            advisory_data = {
                'url': advisory_url,
                'downloaded_at': datetime.now().isoformat(),
                'raw_html': response.text,
                'parsed_content': self.parse_advisory_content(soup)
            }
            
            return advisory_data
        except Exception as e:
            print(f"Error downloading advisory content: {e}")
            return None
    
    def parse_advisory_content(self, soup):
        """Parse advisory page content into structured data"""
        content = {}
        
        # Extract main content sections
        content_div = soup.find('div', class_='content')
        if content_div:
            content['description'] = content_div.get_text(strip=True)
        
        # Extract affected products
        affected_products = []
        product_sections = soup.find_all('div', class_='affected-products')
        for section in product_sections:
            products = section.get_text(strip=True)
            if products:
                affected_products.append(products)
        content['affected_products'] = affected_products
        
        # Extract solution information
        solution_section = soup.find('div', class_='solution')
        if solution_section:
            content['solution'] = solution_section.get_text(strip=True)
        
        return content
    
    def save_advisories_to_file(self, advisories, filename=None):
        """Save advisories to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fortiguard_psirt_advisories_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(advisories, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(advisories)} advisories to {filename}")
        return filename
    
    def download_recent_advisories(self, limit=10, download_full_content=False):
        """Download recent PSIRT advisories"""
        print("Fetching RSS feed...")
        feed = self.fetch_rss_feed()
        
        if not feed or not feed.entries:
            print("No advisories found in RSS feed")
            return []
        
        advisories = []
        print(f"Processing {min(limit, len(feed.entries))} recent advisories...")
        
        for i, entry in enumerate(feed.entries[:limit]):
            print(f"Processing advisory {i+1}/{min(limit, len(feed.entries))}")
            
            advisory = self.extract_advisory_details(entry)
            
            if download_full_content and advisory['link']:
                print(f"  Downloading full content for {advisory['advisory_id']}")
                full_content = self.download_advisory_content(advisory['link'])
                if full_content:
                    advisory['full_content'] = full_content
                
                # Rate limiting to be respectful
                time.sleep(1)
            
            advisories.append(advisory)
        
        return advisories
    
    def download_advisories_by_date_range(self, start_date=None, end_date=None, download_full_content=False):
        """Download PSIRT advisories within a specific date range"""
        if start_date is None:
            # Default to 3 years ago
            start_date = datetime.now() - timedelta(days=3*365)
        if end_date is None:
            end_date = datetime.now()
        
        print(f"Fetching advisories from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        
        # First, get all available entries from RSS feed
        feed = self.fetch_rss_feed()
        if not feed or not feed.entries:
            print("No advisories found in RSS feed")
            return []
        
        print(f"Found {len(feed.entries)} total entries in RSS feed")
        
        # Filter entries by date range
        filtered_entries = []
        for entry in feed.entries:
            try:
                # Parse the published date
                if hasattr(entry, 'published'):
                    entry_date = date_parser.parse(entry.published)
                    # Make timezone-naive for comparison
                    if entry_date.tzinfo:
                        entry_date = entry_date.replace(tzinfo=None)
                    
                    if start_date <= entry_date <= end_date:
                        filtered_entries.append(entry)
            except Exception as e:
                print(f"Warning: Could not parse date for entry: {e}")
                # Include entries with unparseable dates to be safe
                filtered_entries.append(entry)
        
        print(f"Found {len(filtered_entries)} advisories within date range")
        
        if not filtered_entries:
            print("No advisories found within the specified date range")
            return []
        
        # Process filtered entries
        advisories = []
        for i, entry in enumerate(filtered_entries):
            print(f"Processing advisory {i+1}/{len(filtered_entries)}")
            
            advisory = self.extract_advisory_details(entry)
            
            if download_full_content and advisory['link']:
                print(f"  Downloading full content for {advisory['advisory_id']}")
                full_content = self.download_advisory_content(advisory['link'])
                if full_content:
                    advisory['full_content'] = full_content
                
                # Rate limiting to be respectful
                time.sleep(1)
            
            advisories.append(advisory)
        
        return advisories
    
    def download_all_available_advisories(self, download_full_content=False):
        """Download all available PSIRT advisories from RSS feed"""
        print("Fetching all available advisories from RSS feed...")
        feed = self.fetch_rss_feed()
        
        if not feed or not feed.entries:
            print("No advisories found in RSS feed")
            return []
        
        print(f"Found {len(feed.entries)} total advisories in RSS feed")
        
        advisories = []
        for i, entry in enumerate(feed.entries):
            print(f"Processing advisory {i+1}/{len(feed.entries)}")
            
            advisory = self.extract_advisory_details(entry)
            
            if download_full_content and advisory['link']:
                print(f"  Downloading full content for {advisory['advisory_id']}")
                full_content = self.download_advisory_content(advisory['link'])
                if full_content:
                    advisory['full_content'] = full_content
                
                # Rate limiting to be respectful
                time.sleep(0.5)  # Slightly faster for bulk downloads
            
            advisories.append(advisory)
        
        return advisories
    
    def filter_advisories_by_product(self, advisories, product_filter):
        """Filter advisories by product name"""
        filtered = []
        for advisory in advisories:
            title = advisory.get('title', '').lower()
            summary = advisory.get('summary', '').lower()
            
            if product_filter.lower() in title or product_filter.lower() in summary:
                filtered.append(advisory)
        
        return filtered

def main():
    downloader = PSIRTDownloader()
    
    print("FortiGuard PSIRT Advisory Downloader")
    print("====================================")
    print("1. Download recent advisories (last 20)")
    print("2. Download all available advisories")
    print("3. Download advisories from past 3 years")
    print("4. Download advisories from custom date range")
    
    choice = input("\nSelect option (1-4) [default: 3]: ").strip() or "3"
    
    advisories = []
    
    if choice == "1":
        print("\n=== Downloading Recent PSIRT Advisories ===")
        advisories = downloader.download_recent_advisories(limit=20, download_full_content=False)
        
    elif choice == "2":
        print("\n=== Downloading All Available PSIRT Advisories ===")
        advisories = downloader.download_all_available_advisories(download_full_content=False)
        
    elif choice == "3":
        print("\n=== Downloading PSIRT Advisories from Past 3 Years ===")
        advisories = downloader.download_advisories_by_date_range(download_full_content=False)
        
    elif choice == "4":
        print("\n=== Custom Date Range Download ===")
        start_date_str = input("Enter start date (YYYY-MM-DD) [default: 3 years ago]: ").strip()
        end_date_str = input("Enter end date (YYYY-MM-DD) [default: today]: ").strip()
        
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid start date format, using default (3 years ago)")
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid end date format, using default (today)")
        
        advisories = downloader.download_advisories_by_date_range(
            start_date=start_date, 
            end_date=end_date, 
            download_full_content=False
        )
    
    else:
        print("Invalid choice, defaulting to past 3 years")
        advisories = downloader.download_advisories_by_date_range(download_full_content=False)
    
    if advisories:
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = downloader.save_advisories_to_file(
            advisories, 
            f"fortiguard_psirt_advisories_{timestamp}.json"
        )
        
        # Show summary
        print(f"\n=== Summary ===")
        print(f"Total advisories downloaded: {len(advisories)}")
        
        # Group by product
        products = {}
        for advisory in advisories:
            title = advisory.get('title', '')
            # Enhanced product extraction from title
            if 'FortiOS' in title:
                products['FortiOS'] = products.get('FortiOS', 0) + 1
            elif 'FortiGate' in title:
                products['FortiGate'] = products.get('FortiGate', 0) + 1
            elif 'FortiAnalyzer' in title:
                products['FortiAnalyzer'] = products.get('FortiAnalyzer', 0) + 1
            elif 'FortiManager' in title:
                products['FortiManager'] = products.get('FortiManager', 0) + 1
            elif 'FortiWeb' in title:
                products['FortiWeb'] = products.get('FortiWeb', 0) + 1
            elif 'FortiMail' in title:
                products['FortiMail'] = products.get('FortiMail', 0) + 1
            elif 'FortiClient' in title:
                products['FortiClient'] = products.get('FortiClient', 0) + 1
            else:
                products['Other'] = products.get('Other', 0) + 1
        
        print("\nAdvisories by product:")
        for product, count in sorted(products.items(), key=lambda x: x[1], reverse=True):
            print(f"  {product}: {count}")
        
        # Show date range of advisories
        if advisories:
            dates = []
            for advisory in advisories:
                try:
                    if advisory.get('published'):
                        date_obj = date_parser.parse(advisory['published'])
                        dates.append(date_obj)
                except:
                    pass
            
            if dates:
                dates.sort()
                print(f"\nDate range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
        
        # Show recent CVEs
        print("\nRecent CVEs:")
        cve_count = 0
        for advisory in advisories:
            if cve_count >= 10:  # Show up to 10 CVEs
                break
            cve = advisory.get('cve_id')
            if cve and cve != 'N/A':
                title = advisory.get('title', '')[:80] + "..." if len(advisory.get('title', '')) > 80 else advisory.get('title', '')
                print(f"  {cve}: {title}")
                cve_count += 1
        
        if cve_count == 0:
            print("  No CVE IDs found in recent advisories")
        
        # Example: Filter for FortiOS advisories only
        fortios_advisories = downloader.filter_advisories_by_product(advisories, 'FortiOS')
        if fortios_advisories:
            print(f"\nFound {len(fortios_advisories)} FortiOS-specific advisories")
            fortios_filename = downloader.save_advisories_to_file(
                fortios_advisories, 
                f"fortios_advisories_{datetime.now().strftime('%Y%m%d')}.json"
            )
        
        # Ask if user wants to convert to readable formats
        convert_choice = input("\nConvert to readable formats (CSV, HTML, TXT)? (y/n) [default: y]: ").strip().lower()
        if convert_choice != 'n':
            print("\nConverting to readable formats...")
            # This would require the json_to_readable.py script to be available
            print(f"To convert manually, run: python json_to_readable.py {filename}")
    
    else:
        print("\nNo advisories found or downloaded.")

if __name__ == "__main__":
    main()