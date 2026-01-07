#!/usr/bin/env python3
"""
Simplified FortiGuard Browser Scraper
Uses existing Chrome installation without automatic driver download
"""

import json
import time
import re
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from dateutil import parser as date_parser

class SimpleFortiGuardScraper:
    def __init__(self):
        self.base_url = "https://fortiguard.fortinet.com/psirt"
        self.driver = None
        self.found_advisories = []
        
    def find_chrome_driver(self):
        """Find existing ChromeDriver or use system Chrome"""
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found Chrome at: {path}")
                return path
        
        return None
    
    def setup_browser_simple(self):
        """Set up browser with minimal configuration"""
        print("Setting up browser (simple mode)...")
        
        chrome_options = Options()
        
        # Find Chrome executable
        chrome_path = self.find_chrome_driver()
        if chrome_path:
            chrome_options.binary_location = chrome_path
        
        # Minimal options for corporate environment
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        
        # Try to use system ChromeDriver
        try:
            # First try: Use system PATH
            self.driver = webdriver.Chrome(options=chrome_options)
            print("Browser setup successful (system ChromeDriver)!")
            return True
        except WebDriverException as e:
            print(f"System ChromeDriver failed: {e}")
            
        # Second try: Manual ChromeDriver path
        possible_driver_paths = [
            r"C:\Windows\chromedriver.exe",
            r"C:\Program Files\chromedriver.exe",
            r"C:\chromedriver.exe",
        ]
        
        for driver_path in possible_driver_paths:
            if os.path.exists(driver_path):
                try:
                    service = Service(driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    print(f"Browser setup successful with {driver_path}!")
                    return True
                except Exception as e:
                    print(f"Failed with {driver_path}: {e}")
        
        print("Browser setup failed - ChromeDriver not found")
        return False
    
    def test_manual_approach(self):
        """Provide manual approach if browser automation fails"""
        print("\n" + "="*60)
        print("MANUAL APPROACH FOR 3-YEAR HISTORICAL DATA")
        print("="*60)
        print()
        print("Since browser automation is having issues in your corporate environment,")
        print("here's a manual approach to get the 3-year historical data you need:")
        print()
        print("1. OPEN YOUR BROWSER and go to: https://fortiguard.fortinet.com/psirt")
        print()
        print("2. MANUALLY CHECK these advisory patterns:")
        print("   - FG-IR-22-001 through FG-IR-22-150 (2022)")
        print("   - FG-IR-23-001 through FG-IR-23-200 (2023)")  
        print("   - FG-IR-24-001 through FG-IR-24-250 (2024)")
        print("   - FG-IR-25-001 through FG-IR-25-100 (2025)")
        print()
        print("3. FOR EACH VALID ADVISORY, note:")
        print("   - Advisory ID (FG-IR-XX-XXX)")
        print("   - Title")
        print("   - Published date")
        print("   - CVE ID (if any)")
        print("   - Affected products")
        print()
        print("4. SAMPLE URLs to check:")
        for year in [22, 23, 24, 25]:
            for num in [1, 5, 10, 15, 20]:
                print(f"   https://fortiguard.fortinet.com/psirt/FG-IR-{year}-{num:03d}")
        print()
        print("5. CREATE A SPREADSHEET with your findings for analysis")
        print()
        print("This manual approach will give you the comprehensive 3-year")
        print("historical data needed to assess your environment's PSIRT impact.")
        print()
        print("="*60)
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            self.driver.quit()

def main():
    scraper = SimpleFortiGuardScraper()
    
    print("FortiGuard Simple Browser Scraper")
    print("=================================")
    print("Attempting simplified browser automation...")
    print()
    
    if not scraper.setup_browser_simple():
        print("Browser automation failed in corporate environment.")
        scraper.test_manual_approach()
        return
    
    try:
        # If we get here, browser worked
        print("Browser automation successful!")
        print("Testing FortiGuard access...")
        
        scraper.driver.get("https://fortiguard.fortinet.com/psirt/FG-IR-25-006")
        time.sleep(5)
        
        if "fortiguard" in scraper.driver.current_url.lower():
            print("SUCCESS: Can access FortiGuard advisories!")
            print("Browser automation is working in your environment.")
            print()
            print("The full historical scan would take 30-60 minutes.")
            print("Would you like to proceed with the automated scan?")
        else:
            print("Browser opened but couldn't access FortiGuard properly.")
            scraper.test_manual_approach()
            
    except Exception as e:
        print(f"Browser test failed: {e}")
        scraper.test_manual_approach()
    
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()
