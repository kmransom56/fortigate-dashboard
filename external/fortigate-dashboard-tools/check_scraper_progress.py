#!/usr/bin/env python3
"""
Progress Monitor for FortiGuard SSL-Fixed Scraper
=================================================

This script helps monitor the progress of the running scraper
and shows any results found so far.
"""

import os
import json
import glob
from datetime import datetime

def check_progress():
    print("FortiGuard Scraper Progress Monitor")
    print("=" * 40)
    print(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Look for any JSON output files created today
    today = datetime.now().strftime("%Y%m%d")
    pattern = f"fortiguard_historical_advisories_{today}_*.json"
    
    json_files = glob.glob(pattern)
    
    if json_files:
        # Get the most recent file
        latest_file = max(json_files, key=os.path.getmtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            advisories = data.get('advisories', [])
            
            print(f"[FOUND] Results file: {latest_file}")
            print(f"Total advisories found: {len(advisories)}")
            print(f"Scrape date: {metadata.get('scrape_date', 'Unknown')}")
            print(f"Failed requests: {metadata.get('failed_requests', 0)}")
            print()
            
            if advisories:
                print("Recent advisories found:")
                for i, advisory in enumerate(advisories[-5:]):  # Show last 5
                    print(f"  {advisory['id']}: {advisory['title'][:50]}...")
                
                # Quick analysis
                years = {}
                products = {}
                
                for advisory in advisories:
                    # Extract year
                    if advisory.get('id'):
                        year_match = advisory['id'].split('-')[2] if len(advisory['id'].split('-')) > 2 else None
                        if year_match:
                            year = f"20{year_match}"
                            years[year] = years.get(year, 0) + 1
                    
                    # Count products
                    for product in advisory.get('affected_products', []):
                        products[product] = products.get(product, 0) + 1
                
                print(f"\nQuick Analysis:")
                print(f"Years covered: {', '.join(sorted(years.keys()))}")
                if products:
                    top_product = max(products.items(), key=lambda x: x[1])
                    print(f"Most affected product: {top_product[0]} ({top_product[1]} advisories)")
            
        except Exception as e:
            print(f"[ERROR] Could not read results file: {e}")
    
    else:
        print("[INFO] No results files found yet")
        print("The scraper may still be running or just starting...")
    
    print()
    print("To check again, run: python check_scraper_progress.py")

if __name__ == "__main__":
    check_progress()
