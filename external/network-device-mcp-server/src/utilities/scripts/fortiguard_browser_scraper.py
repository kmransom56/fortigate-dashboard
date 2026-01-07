#!/usr/bin/env python3
"""
FortiGuard Historical PSIRT Browser Scraper
Uses Selenium to automate browser and bypass SSL certificate issues
Gets true 3-year historical data for environment impact assessment
"""

import json
import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dateutil import parser as date_parser

class FortiGuardBrowserScraper:
    def __init__(self):
        self.base_url = "https://fortiguard.fortinet.com/psirt"
        self.driver = None
        self.found_advisories = []
        
    def setup_browser(self):
        """Set up Chrome browser with appropriate options"""
        print("Setting up browser...")
        
        chrome_options = Options()
        # Add options to work in corporate environment
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list-invalid")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Use your existing Chrome profile to inherit certificates
        # chrome_options.add_argument(f"--user-data-dir={os.path.expanduser('~')}/AppData/Local/Google/Chrome/User Data")
        # chrome_options.add_argument("--profile-directory=Default")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            print("Browser setup successful!")
            return True
        except Exception as e:
            print(f"Browser setup failed: {e}")
            return False
    
    def test_browser_access(self):
        """Test if browser can access FortiGuard"""
        test_urls = [
            "https://fortiguard.fortinet.com/rss/ir.xml",
            "https://fortiguard.fortinet.com/psirt/FG-IR-25-006"
        ]
        
        print("Testing browser access to FortiGuard...")
        
        for url in test_urls:
            try:
                print(f"Testing: {url}")
                self.driver.get(url)
                time.sleep(3)
                
                if "fortiguard" in self.driver.current_url.lower():
                    print(f"SUCCESS: Accessed {url}")
                    return True
                else:
                    print(f"WARNING: Redirected from {url}")
                    
            except Exception as e:
                print(f"ERROR: {url} - {e}")
        
        return False
    
    def extract_advisory_data(self, advisory_id):
        """Extract data from a specific advisory page"""
        url = f"{self.base_url}/{advisory_id}"
        
        try:
            print(f"Checking: {advisory_id}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check if we got a valid page (not 404)
            if "404" in self.driver.title or "not found" in self.driver.page_source.lower():
                return None
            
            advisory_data = {
                'advisory_id': advisory_id,
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract title
            try:
                title_selectors = ['h1', 'h2', '.title', '.page-title']
                for selector in title_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].text.strip():
                        advisory_data['title'] = elements[0].text.strip()
                        break
            except:
                pass
            
            # Extract page text for further parsing
            page_text = self.driver.page_source
            
            # Extract published date
            date_patterns = [
                r'Published[:\s]+(\d{4}-\d{2}-\d{2})',
                r'Date[:\s]+(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2})',
                r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})'
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
            
            # Extract summary from page text
            try:
                body_element = self.driver.find_element(By.TAG_NAME, "body")
                body_text = body_element.text
                if len(body_text) > 200:
                    advisory_data['summary'] = body_text[:1000]
            except:
                pass
            
            # If we found meaningful data, return it
            if advisory_data.get('title') or advisory_data.get('published') or len(page_text) > 5000:
                return advisory_data
            
            return None
            
        except TimeoutException:
            print(f"Timeout accessing {advisory_id}")
            return None
        except Exception as e:
            print(f"Error extracting {advisory_id}: {e}")
            return None
    
    def generate_advisory_ids(self, start_year=2022, end_year=None):
        """Generate potential advisory IDs for the past 3 years"""
        if end_year is None:
            end_year = datetime.now().year
        
        advisory_ids = []
        
        for year in range(start_year, end_year + 1):
            year_suffix = str(year)[-2:]
            
            # Estimate number of advisories per year
            if year == 2022:
                max_num = 150  # Partial year
            elif year == 2023:
                max_num = 200
            elif year == 2024:
                max_num = 250
            else:  # 2025
                max_num = 100  # Current year, partial
            
            for num in range(1, max_num + 1):
                advisory_id = f"FG-IR-{year_suffix}-{num:03d}"
                advisory_ids.append(advisory_id)
        
        return advisory_ids
    
    def scan_historical_advisories(self, start_year=2022):
        """Scan for historical advisories using browser automation"""
        print(f"Starting browser-based historical scan from {start_year}")
        print("This will systematically check FortiGuard advisory pages...")
        
        if not self.setup_browser():
            print("Failed to setup browser")
            return []
        
        if not self.test_browser_access():
            print("Failed to access FortiGuard with browser")
            self.cleanup()
            return []
        
        print("Browser access confirmed! Starting advisory scan...")
        
        # Generate advisory IDs to check
        advisory_ids = self.generate_advisory_ids(start_year)
        print(f"Generated {len(advisory_ids)} potential advisory IDs to check")
        
        start_time = time.time()
        found_count = 0
        
        for i, advisory_id in enumerate(advisory_ids):
            advisory_data = self.extract_advisory_data(advisory_id)
            
            if advisory_data:
                self.found_advisories.append(advisory_data)
                found_count += 1
                title = advisory_data.get('title', 'No title')[:60]
                print(f"FOUND: {advisory_id} - {title}...")
            
            # Progress update every 25 advisories
            if (i + 1) % 25 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed * 60 if elapsed > 0 else 0
                print(f"Progress: {i + 1}/{len(advisory_ids)} checked, "
                      f"{found_count} found, {rate:.1f} checks/min")
            
            # Small delay to be respectful
            time.sleep(1)
        
        elapsed = time.time() - start_time
        print(f"\nBrowser scan complete!")
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
                    filtered.append(advisory)  # Include if can't parse date
            else:
                filtered.append(advisory)  # Include if no date
        
        return filtered
    
    def save_advisories(self, advisories, filename=None):
        """Save advisories to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fortiguard_browser_advisories_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(advisories, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(advisories)} advisories to {filename}")
        return filename
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")

def main():
    scraper = FortiGuardBrowserScraper()
    
    try:
        print("FortiGuard Historical PSIRT Browser Scraper")
        print("==========================================")
        print("Using browser automation to get 3-year historical data")
        print("This will help assess your environment's PSIRT impact")
        print()
        
        # Start the scan
        start_year = 2022
        advisories = scraper.scan_historical_advisories(start_year=start_year)
        
        if advisories:
            # Filter to last 3 years
            three_years_ago = datetime.now() - timedelta(days=3*365)
            recent_advisories = scraper.filter_by_date_range(advisories, start_date=three_years_ago)
            
            print(f"\nFiltered to last 3 years: {len(recent_advisories)} advisories")
            
            # Save results
            filename = scraper.save_advisories(recent_advisories)
            
            # Show detailed analysis for environment impact
            print(f"\n=== ENVIRONMENT IMPACT ANALYSIS ===")
            print(f"Total advisories found (3 years): {len(recent_advisories)}")
            
            # Group by year for trend analysis
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
            
            print("\nAdvisories by year (trend analysis):")
            for year in sorted(years.keys()):
                print(f"  {year}: {years[year]} advisories")
            
            # Group by product for impact assessment
            products = {}
            for advisory in recent_advisories:
                title = advisory.get('title', '').lower()
                if 'fortios' in title:
                    products['FortiOS'] = products.get('FortiOS', 0) + 1
                elif 'fortigate' in title:
                    products['FortiGate'] = products.get('FortiGate', 0) + 1
                elif 'fortianalyzer' in title:
                    products['FortiAnalyzer'] = products.get('FortiAnalyzer', 0) + 1
                elif 'fortimanager' in title:
                    products['FortiManager'] = products.get('FortiManager', 0) + 1
                elif 'fortiweb' in title:
                    products['FortiWeb'] = products.get('FortiWeb', 0) + 1
                elif 'fortimail' in title:
                    products['FortiMail'] = products.get('FortiMail', 0) + 1
                else:
                    products['Other'] = products.get('Other', 0) + 1
            
            print("\nAdvisories by product (environment impact):")
            for product, count in sorted(products.items(), key=lambda x: x[1], reverse=True):
                print(f"  {product}: {count} advisories")
            
            # CVE analysis
            cves = [adv.get('cve_id') for adv in recent_advisories if adv.get('cve_id')]
            print(f"\nCVEs identified: {len(cves)}")
            
            # High-level risk assessment
            total_advisories = len(recent_advisories)
            if total_advisories > 200:
                risk_level = "HIGH"
            elif total_advisories > 100:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            print(f"\nEnvironment Risk Assessment:")
            print(f"  Total 3-year advisories: {total_advisories}")
            print(f"  Risk level: {risk_level}")
            print(f"  Average per year: {total_advisories / 3:.1f}")
            
            print(f"\nData saved to: {filename}")
            print(f"To convert to readable formats: python json_to_readable.py {filename}")
            
        else:
            print("No advisories found.")
    
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()
