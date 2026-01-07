#!/usr/bin/env python3
"""
Browser Profile Scraper - Uses Your Existing Chrome Profile
===========================================================

This scraper uses your existing Chrome browser profile with all
your corporate certificates and authentication already configured.
"""

import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

class BrowserProfileScraper:
    def __init__(self):
        self.driver = None
        self.found_advisories = []
        
    def setup_browser_with_profile(self):
        """Set up Chrome using your existing profile"""
        print("Setting up Chrome with your existing profile...")
        
        chrome_options = Options()
        
        # Use your existing Chrome profile
        username = os.getenv('USERNAME')
        profile_path = f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data"
        
        if os.path.exists(profile_path):
            chrome_options.add_argument(f"--user-data-dir={profile_path}")
            chrome_options.add_argument("--profile-directory=Default")
            print(f"Using Chrome profile: {profile_path}")
        else:
            print("Default Chrome profile not found, using fresh profile")
        
        # Additional options for corporate environment
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions-except")
        chrome_options.add_argument("--disable-plugins-discovery")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        
        # Keep browser visible for debugging
        # chrome_options.add_argument("--headless")  # Commented out for debugging
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("[OK] Browser setup successful with existing profile!")
            return True
        except Exception as e:
            print(f"[ERROR] Browser setup failed: {e}")
            return False
    
    def test_fortiguard_access(self):
        """Test if we can access FortiGuard with the browser"""
        print("\nTesting FortiGuard access...")
        
        test_urls = [
            "https://fortiguard.fortinet.com/",
            "https://fortiguard.fortinet.com/psirt",
            "https://fortiguard.fortinet.com/psirt/FG-IR-25-006"
        ]
        
        for url in test_urls:
            try:
                print(f"Testing: {url}")
                self.driver.get(url)
                time.sleep(3)
                
                current_url = self.driver.current_url
                page_title = self.driver.title
                
                print(f"  Current URL: {current_url}")
                print(f"  Page Title: {page_title}")
                
                if "fortiguard" in current_url.lower() or "fortiguard" in page_title.lower():
                    print("  [SUCCESS] Successfully accessed FortiGuard!")
                    return True
                else:
                    print("  [WARNING] May be redirected or blocked")
                    
            except Exception as e:
                print(f"  [ERROR] Error: {e}")
        
        return False
    
    def scrape_single_advisory(self, advisory_id):
        """Scrape a single advisory using browser automation"""
        url = f"https://fortiguard.fortinet.com/psirt/{advisory_id}"
        
        try:
            print(f"Scraping {advisory_id}...")
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Check if we got a valid advisory page
            if "404" in self.driver.title or "not found" in self.driver.title.lower():
                return None
            
            # Extract advisory data
            advisory_data = {
                'id': advisory_id,
                'url': url,
                'title': '',
                'content': '',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Get page title
            advisory_data['title'] = self.driver.title
            
            # Get page content
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                advisory_data['content'] = body.text[:1000]  # First 1000 chars
            except:
                advisory_data['content'] = "Could not extract content"
            
            print(f"  [SUCCESS] Successfully scraped {advisory_id}")
            return advisory_data
            
        except Exception as e:
            print(f"  [ERROR] Error scraping {advisory_id}: {e}")
            return None
    
    def test_sample_advisories(self):
        """Test scraping a few sample advisories"""
        sample_ids = [
            "FG-IR-25-006",
            "FG-IR-24-001", 
            "FG-IR-23-001",
            "FG-IR-22-047"
        ]
        
        print(f"\nTesting sample advisory scraping...")
        
        results = []
        for advisory_id in sample_ids:
            result = self.scrape_single_advisory(advisory_id)
            if result:
                results.append(result)
                print(f"  Title: {result['title'][:60]}...")
            time.sleep(2)  # Be nice to the server
        
        return results
    
    def save_results(self, results, filename=None):
        """Save scraping results"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"browser_profile_scrape_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {filename}")
        return filename
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            self.driver.quit()

def main():
    scraper = BrowserProfileScraper()
    
    print("FortiGuard Browser Profile Scraper")
    print("=" * 40)
    print("Using your existing Chrome profile to bypass network restrictions")
    print()
    
    try:
        # Setup browser with your profile
        if not scraper.setup_browser_with_profile():
            print("Failed to setup browser. Exiting.")
            return
        
        # Test FortiGuard access
        if not scraper.test_fortiguard_access():
            print("Cannot access FortiGuard. Check network connectivity.")
            return
        
        # Test sample advisory scraping
        results = scraper.test_sample_advisories()
        
        if results:
            print(f"\n[SUCCESS] Successfully scraped {len(results)} advisories!")
            scraper.save_results(results)
            
            print("\nSample results:")
            for result in results:
                print(f"  {result['id']}: {result['title'][:50]}...")
        else:
            print("\n[ERROR] No advisories could be scraped")
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()
