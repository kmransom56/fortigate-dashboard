#!bin/python
# scrape_icons.py
import os
import json
import requests
from bs4 import BeautifulSoup

# folder where we'll drop any SVGs we fetch
OUT_DIR = os.path.join(os.getcwd(), "app", "static", "icons")
os.makedirs(OUT_DIR, exist_ok=True)

# --- 1. SIMPLE ICONS --------------------------------------------------------
SIMPLE_ICONS_JSON = (
    "https://cdn.jsdelivr.net/npm/simple-icons/_data/simple-icons.json"
)

def list_simpleicons(keyword: str):
    """Return Simple-Icons entries whose title contains <keyword>."""
    try:
        resp = requests.get(SIMPLE_ICONS_JSON, timeout=10).json()
        # jsdelivr returns a list directly, earlier versions returned {"icons": [...]}
        icons = resp["icons"] if isinstance(resp, dict) and "icons" in resp else resp
        matches = []
        for icon in icons:
            # Handle different API response formats
            title = icon.get("title", icon.get("name", ""))
            slug = icon.get("slug", icon.get("title", "").lower().replace(" ", ""))
            if keyword.lower() in title.lower():
                matches.append({"title": title, "slug": slug})
        return matches
    except Exception as e:
        print(f"Error fetching Simple Icons: {e}")
        return []

def download_simpleicon(slug: str):
    url = f"https://cdn.simpleicons.org/{slug}"
    svg = requests.get(url, timeout=10).text
    path = os.path.join(OUT_DIR, f"{slug}.svg")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(svg)
    print(f"[simpleicons] saved → {path}")

# --- 2. FORTINET MEDIA-KIT PAGE --------------------------------------------
def scrape_fortinet_media():
    """Check Fortinet press kit and icon library for assets."""
    urls = [
        "https://www.fortinet.com/corporate/about-us/newsroom/press-kit",
        "https://icons.fortinet.com/"
    ]
    
    for url in urls:
        try:
            print(f"\n[fortinet] Checking {url}...")
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f" • Failed to access (HTTP {response.status_code})")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            assets_found = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(href.lower().endswith(ext) for ext in (".svg", ".png", ".eps", ".ai", ".pdf", ".zip")):
                    assets_found.append(href)
            
            if assets_found:
                print(f" • Found {len(assets_found)} assets:")
                for asset in assets_found[:10]:  # Show first 10
                    print(f"   - {asset}")
                if len(assets_found) > 10:
                    print(f"   ... and {len(assets_found) - 10} more")
                
                # Download Fortinet Icon Library if found
                for asset in assets_found:
                    if "Fortinet-Icon-Library.zip" in asset:
                        download_fortinet_icon_library(url, asset)
                        
            else:
                print(" • No direct asset links found (may require login or have dynamic content)")
                
        except Exception as e:
            print(f" • Error accessing {url}: {e}")

def download_fortinet_icon_library(base_url, zip_path):
    """Download and extract Fortinet Icon Library."""
    import zipfile
    
    try:
        # Construct full URL
        if zip_path.startswith("http"):
            zip_url = zip_path
        else:
            zip_url = base_url.rstrip("/") + "/" + zip_path.lstrip("/")
        
        print(f"\n[fortinet] Downloading Fortinet Icon Library...")
        print(f" • URL: {zip_url}")
        
        # Download the zip file
        response = requests.get(zip_url, timeout=30)
        if response.status_code != 200:
            print(f" • Failed to download (HTTP {response.status_code})")
            return
        
        # Save zip file temporarily
        zip_file_path = os.path.join(OUT_DIR, "Fortinet-Icon-Library.zip")
        with open(zip_file_path, "wb") as f:
            f.write(response.content)
        print(f" • Downloaded to {zip_file_path}")
        
        # Extract zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            extract_dir = os.path.join(OUT_DIR, "fortinet-icons")
            os.makedirs(extract_dir, exist_ok=True)
            zip_ref.extractall(extract_dir)
            print(f" • Extracted to {extract_dir}")
            
            # List extracted files
            extracted_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().endswith(('.svg', '.png', '.eps', '.ai')):
                        extracted_files.append(os.path.join(root, file))
            
            print(f" • Extracted {len(extracted_files)} icon files:")
            for file_path in extracted_files[:10]:  # Show first 10
                rel_path = os.path.relpath(file_path, extract_dir)
                print(f"   - {rel_path}")
            if len(extracted_files) > 10:
                print(f"   ... and {len(extracted_files) - 10} more")
        
        # Clean up zip file
        os.remove(zip_file_path)
        print(f" • Cleaned up temporary zip file")
        
    except Exception as e:
        print(f" • Error downloading Fortinet Icon Library: {e}")

def list_mui_icons():
    """List available Material-UI device icons (these are imported as React components, not downloaded)."""
    mui_device_icons = [
        "Router", "Security", "Wifi", "SettingsEthernet", "VpnKey",
        "Computer", "PhoneAndroid", "Tablet", "Watch", "Tv",
        "Speaker", "Headphones", "Mouse", "Keyboard", "Print",
        "Scanner", "Memory", "Storage", "CloudQueue", "Dns",
        "Hub", "Cable", "PowerSettingsNew", "SignalWifi4Bar",
        "NetworkCheck", "NetworkWifi", "WifiTethering", "BluetoothConnected",
        "DeviceHub", "Devices", "DevicesOther", "DesktopWindows",
        "LaptopMac", "PhonelinkSetup", "Cast", "CastConnected"
    ]
    
    print(f"\n[mui-icons] Available Material-UI icons for devices:")
    print("Note: These are imported as React components, not downloaded as files.")
    for icon in mui_device_icons:
        print(f" • {icon}Icon (import from @mui/icons-material/{icon})")
    
    return mui_device_icons

# ---------- HTML gallery -------------
GALLERY_PATH = os.path.join(OUT_DIR, "gallery.html")

def build_gallery(matches):
    """Generate a simple HTML page displaying the provided icons."""
    rows = []
    for icon in matches:
        slug = icon["slug"]
        title = icon["title"]
        rows.append(
            f"<div style='text-align:center;margin:10px'><img src='https://cdn.simpleicons.org/{slug}' width='64'><br>{title}</div>"
        )
    grid = "".join(rows)
    html = f"<html><head><title>Icon Gallery</title></head><body><h1>Matched Icons</h1><div style='display:flex;flex-wrap:wrap'>{grid}</div></body></html>"
    with open(GALLERY_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[gallery] Open {GALLERY_PATH} in your browser to preview the icons.")

# ------------------------------ main ----------------------------------------
if __name__ == "__main__":
    # Device types for your dashboard
    device_keywords = [
        "fortinet", "cisco", "router", "switch", "firewall", 
        "wireless", "access", "gateway", "network", "server",
        "security", "vpn", "wifi", "ethernet", "modem"
    ]
    
    all_matches = []
    
    for keyword in device_keywords:
        print(f"\nSearching Simple Icons for '{keyword}'…")
        matches = list_simpleicons(keyword)
        if matches:
            print(f"Found {len(matches)} matches:")
            for m in matches:
                print(f" • {m['title']}  (slug = {m['slug']})")
                all_matches.append(m)
            
            # Download the first match for each keyword
            download_simpleicon(matches[0]['slug'])
    
    if all_matches:
        print(f"\nTotal icons found: {len(all_matches)}")
        build_gallery(all_matches)
    
    print("\nChecking Fortinet media kit…")
    scrape_fortinet_media()
    
    print("\nListing Material-UI icons…")
    list_mui_icons()
