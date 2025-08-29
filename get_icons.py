import os
import requests
import json
from urllib.parse import urljoin, urlparse
import time

print("🔍 Starting enhanced icon download script...")

# Known icon repositories and direct sources
icon_sources = {
    "simple_icons": {
        "base_url": "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/",
        "icons": ["fortinet", "cisco", "ubiquiti", "mikrotik", "pfsense", "openwrt", "ddwrt", "meraki", "juniper", "aruba", "dell", "hp", "lenovo", "supermicro"]
    },
    "feather_icons": {
        "base_url": "https://raw.githubusercontent.com/feathericons/feather/master/icons/",
        "icons": ["wifi", "server", "monitor", "smartphone", "tablet", "laptop", "router", "shield", "lock", "unlock", "settings", "activity", "bar-chart", "trending-up"]
    },
    "heroicons": {
        "base_url": "https://raw.githubusercontent.com/tailwindlabs/heroicons/master/src/24/outline/",
        "icons": ["wifi", "server", "computer-desktop", "device-phone-mobile", "device-tablet", "shield-check", "lock-closed", "cog-6-tooth", "chart-bar", "signal"]
    }
}

# POS and retail specific icons to search for
pos_keywords = ["pos", "point-of-sale", "retail", "cash-register", "payment", "terminal", "kiosk", "menu", "restaurant"]

# Output folder
download_dir = "downloaded_files"
print(f"📁 Creating directory: {download_dir}")
os.makedirs(download_dir, exist_ok=True)
print(f"✅ Directory ready: {os.path.exists(download_dir)}")

def download_file(url, custom_name=None):
    """Download a file from URL with better error handling and naming"""
    try:
        # Use custom name if provided, otherwise extract from URL
        if custom_name:
            local_filename = os.path.join(download_dir, custom_name)
        else:
            filename = os.path.basename(urlparse(url).path)
            if not filename or not filename.endswith(('.svg', '.png', '.ico')):
                filename = f"icon_{int(time.time())}.svg"
            local_filename = os.path.join(download_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(local_filename):
            print(f"⏭️  Skipping (exists): {os.path.basename(local_filename)}")
            return True
            
        print(f"⬇️  Downloading: {os.path.basename(local_filename)}")
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        with open(local_filename, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(local_filename)
        print(f"✅ Saved: {os.path.basename(local_filename)} ({file_size} bytes)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error for {url}: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to save {url}: {e}")
        return False

def download_from_icon_library(library_name, library_info):
    """Download icons from a known icon library"""
    print(f"\n📚 Downloading from {library_name}...")
    success_count = 0
    
    for icon_name in library_info["icons"]:
        url = urljoin(library_info["base_url"], f"{icon_name}.svg")
        custom_name = f"{library_name}_{icon_name}.svg"
        
        if download_file(url, custom_name):
            success_count += 1
        
        # Small delay to be respectful to the server
        time.sleep(0.5)
    
    print(f"📊 {library_name}: {success_count}/{len(library_info['icons'])} icons downloaded")
    return success_count

def search_github_for_pos_icons():
    """Search GitHub API for POS-related icons"""
    print(f"\n🔍 Searching GitHub for POS icons...")
    
    # GitHub search API endpoint
    github_search_url = "https://api.github.com/search/repositories"
    
    search_queries = [
        "pos icons svg",
        "point of sale icons", 
        "retail icons svg",
        "restaurant icons"
    ]
    
    downloaded_count = 0
    
    for query in search_queries:
        try:
            print(f"🔍 Searching: {query}")
            params = {
                'q': f'{query} language:svg',
                'sort': 'stars',
                'per_page': 5
            }
            
            response = requests.get(github_search_url, params=params, timeout=10)
            if response.status_code == 200:
                results = response.json()
                print(f"📋 Found {results.get('total_count', 0)} repositories")
                
                # This is a basic implementation - in practice you'd need to explore the repos
                # For now, let's just acknowledge the search worked
                for repo in results.get('items', [])[:2]:
                    print(f"  📦 {repo['name']}: {repo['html_url']}")
                    
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"❌ GitHub search error: {e}")
    
    return downloaded_count

# Main execution
def main():
    total_downloaded = 0
    
    # Download from known icon libraries
    for library_name, library_info in icon_sources.items():
        downloaded = download_from_icon_library(library_name, library_info)
        total_downloaded += downloaded
    
    # Search GitHub for additional POS icons
    github_downloaded = search_github_for_pos_icons()
    total_downloaded += github_downloaded
    
    # Add some additional useful icons from other sources
    additional_icons = [
        {
            "url": "https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/assets/Cash%20Register/SVG/ic_fluent_cash_register_24_regular.svg",
            "name": "fluent_cash_register.svg"
        },
        {
            "url": "https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/assets/Point%20Of%20Sale/SVG/ic_fluent_point_of_sale_24_regular.svg", 
            "name": "fluent_point_of_sale.svg"
        },
        {
            "url": "https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/assets/Food/SVG/ic_fluent_food_24_regular.svg",
            "name": "fluent_food.svg"
        }
    ]
    
    print(f"\n🏪 Downloading additional POS/retail icons...")
    for icon_info in additional_icons:
        if download_file(icon_info["url"], icon_info["name"]):
            total_downloaded += 1
        time.sleep(0.5)
    
    # Summary
    print(f"\n🎉 Download complete!")
    print(f"📊 Total icons downloaded: {total_downloaded}")
    
    # List all downloaded files
    try:
        downloaded_files = [f for f in os.listdir(download_dir) if f.endswith(('.svg', '.png', '.ico'))]
        print(f"📁 Files in {download_dir}:")
        for file in sorted(downloaded_files):
            file_path = os.path.join(download_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  📄 {file} ({file_size} bytes)")
    except Exception as e:
        print(f"❌ Error listing files: {e}")

if __name__ == "__main__":
    main()
