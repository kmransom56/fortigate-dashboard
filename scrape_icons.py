# scrape_icons.py
import os
import json
import requests
from bs4 import BeautifulSoup

# folder where we’ll drop any SVGs we fetch
OUT_DIR = os.path.join(os.getcwd(), "app", "static", "icons")
os.makedirs(OUT_DIR, exist_ok=True)

# --- 1. SIMPLE ICONS --------------------------------------------------------
# Use the direct npm package.json to get icon data
SIMPLE_ICONS_API = "https://unpkg.com/simple-icons@latest/icons.json"


def list_simpleicons(keyword: str):
    """Return Simple-Icons entries whose title contains <keyword>."""
    response = None
    try:
        response = requests.get(SIMPLE_ICONS_API, timeout=10)
        response.raise_for_status()

        # Debug: print first 200 chars of response
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content (first 200 chars): {response.text[:200]}")

        obj = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching Simple Icons: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from Simple Icons: {e}")
        if response:
            print(f"Raw response: {response.text[:500]}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

    # JSON may be under 'icons' key or be the list directly
    icons = obj.get("icons") if isinstance(obj, dict) and "icons" in obj else obj
    return [icon for icon in icons if keyword.lower() in icon.get("title", "").lower()]


def download_simpleicon(slug: str):
    url = f"https://cdn.simpleicons.org/{slug}"
    svg = requests.get(url, timeout=10).text
    path = os.path.join(OUT_DIR, f"{slug}.svg")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(svg)
    print(f"[simpleicons] saved → {path}")


# --- 2. FORTINET MEDIA-KIT PAGE --------------------------------------------
def scrape_fortinet_media():
    url = "https://www.fortinet.com/corporate/about-us/newsroom/media-kit"
    html = requests.get(url, timeout=10).text
    soup = BeautifulSoup(html, "html.parser")

    print("\n[fortinet] assets found on page:")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(
            href.lower().endswith(ext)
            for ext in (".svg", ".png", ".eps", ".ai", ".pdf")
        ):
            print(" •", href)


# ------------------------------ main ----------------------------------------
if __name__ == "__main__":
    enterprise_keywords = [
        "cisco", "juniper", "arista", "fortinet", "hp", "dell", 
        "server", "router", "switch", "firewall", "printer", "camera"
    ]
    
    print("Searching for enterprise device icons...")
    for keyword in enterprise_keywords:
        print(f"\nSearching Simple Icons for '{keyword}'...")
        matches = list_simpleicons(keyword)
        if matches:
            print(f"Found {len(matches)} matches for {keyword}:")
            for m in matches:
                title = m.get("title", "Unknown")
                slug = m.get("slug") or m.get("title", "").lower().replace(" ", "")
                print(f" • {title}  (slug = {slug})")
                
                if matches.index(m) < 2 and slug:
                    try:
                        download_simpleicon(slug)
                    except Exception as e:
                        print(f"Error downloading {slug}: {e}")
        else:
            print(f"No icons found for {keyword}")
    
    print("\nSearching Fortinet media page...")
    scrape_fortinet_media()
