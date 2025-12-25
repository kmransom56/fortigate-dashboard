# scrape_icons.py
import os
import json
import requests
from bs4 import BeautifulSoup
import sqlite3

# --- DATABASE SETUP --------------------------------------------------------
DB_PATH = os.path.join(os.getcwd(), "app", "static", "icons.db")


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS icons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manufacturer TEXT,
            device_type TEXT,
            slug TEXT,
            title TEXT,
            icon_path TEXT,
            source_url TEXT,
            tags TEXT
        )
    """
    )
    return conn


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
    if not icons:
        return []
    return [icon for icon in icons if keyword.lower() in icon.get("title", "").lower()]


def insert_icon_metadata(
    manufacturer, device_type, slug, title, icon_path, source_url, tags=None
):
    conn = get_db_conn()
    conn.execute(
        "INSERT INTO icons (manufacturer, device_type, slug, title, icon_path, source_url, tags) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (manufacturer, device_type, slug, title, icon_path, source_url, tags),
    )
    conn.commit()
    conn.close()


def download_simpleicon(
    slug: str, manufacturer=None, device_type=None, title=None, tags=None
):
    url = f"https://cdn.simpleicons.org/{slug}"
    svg = requests.get(url, timeout=10).text
    path = os.path.join(OUT_DIR, f"{slug}.svg")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(svg)
    print(f"[simpleicons] saved → {path}")
    # Insert metadata into DB
    insert_icon_metadata(
        manufacturer=manufacturer,
        device_type=device_type,
        slug=slug,
        title=title,
        icon_path=path,
        source_url=url,
        tags=tags,
    )


# --- 2. FORTINET & MERAKI MEDIA-KIT & ICONS --------------------------------
def scrape_vendor_media(vendor: str, auto_download: bool = True):
    """
    Scrape and optionally download media assets (icons, images, vss files) for a given vendor.
    Supported vendors: 'fortinet', 'meraki', 'cisco', 'aruba', 'panasonic', 'elo', 'micros', 'par', 'hp', 'epson', 'touchdynamic', 'posiflex', 'samsung', 'nec', 'sharp', 'dell', 'lenovo', 'asus', 'acer', 'star', 'bixolon', 'zebra', 'honeywell', 'ingenico', 'verifone', 'square', 'clover', 'kitchen', 'kiosk', 'digitalmenu', 'tablet', 'register', 'printer'
    """
    vendor = vendor.lower()
    vendor_urls = {
        "fortinet": "https://www.fortinet.com/corporate/about-us/newsroom/media-kit",
        "meraki": "https://meraki.cisco.com/product-collateral/",
        "cisco": "https://www.cisco.com/c/en/us/about/brand-center/brand-assets.html",
        "aruba": "https://www.arubanetworks.com/company/newsroom/media-kit/",
        "panasonic": "https://na.panasonic.com/us/news/panasonic-media-kit",
        "elo": "https://www.elotouch.com/company/media-kit.html",
        "micros": "https://www.oracle.com/industries/food-beverage/resources/",
        "par": "https://www.partech.com/resources/",
        "hp": "https://press.hp.com/us/en/press-kit.html",
        "epson": "https://epson.com/Press-Kit",
        "touchdynamic": "https://www.touchdynamic.com/resources/",
        "posiflex": "https://posiflex.com/resources/",
        "samsung": "https://news.samsung.com/global/media-resources",
        "nec": "https://www.nec.com/en/global/brand/media.html",
        "sharp": "https://www.sharpusa.com/AboutSharp/PressRoom/MediaKit.aspx",
        "dell": "https://www.dell.com/en-us/dt/corporate/newsroom/media-kit.htm",
        "lenovo": "https://news.lenovo.com/media-kit/",
        "asus": "https://www.asus.com/us/news/media-kit/",
        "acer": "https://www.acer.com/us-en/about-acer/media-kit",
        "star": "https://www.starmicronics.com/resources/",
        "bixolon": "https://bixolon.com/html/en/media_center/media_center.html",
        "zebra": "https://www.zebra.com/us/en/about-zebra/newsroom/media-kit.html",
        "honeywell": "https://www.honeywell.com/us/en/newsroom/media-kit",
        "ingenico": "https://www.ingenico.com/resources",
        "verifone": "https://www.verifone.com/resources",
        "square": "https://squareup.com/us/en/press/media-kit",
        "clover": "https://www.clover.com/resources",
        # Quick service restaurant brands (for broad search)
        "arbys": "https://www.arbys.com/media-kit/",
        "bww": "https://www.buffalowildwings.com/en/media-kit/",
        "sonic": "https://www.sonicdrivein.com/media-kit/",
        "mcdonalds": "https://news.mcdonalds.com/media-kit",
        "wendys": "https://www.wendys.com/media-kit",
        "burgerking": "https://www.bk.com/media-kit",
        "tacobell": "https://www.tacobell.com/media-kit",
        "subway": "https://www.subway.com/en-us/aboutus/mediakit",
        "starbucks": "https://stories.starbucks.com/media-kit/",
        "dunkindonuts": "https://news.dunkindonuts.com/media-kit",
        "chipotle": "https://www.chipotle.com/media-kit",
        "pizzahut": "https://www.pizzahut.com/media-kit",
        "dominos": "https://www.dominos.com/media-kit",
        "panerabread": "https://www.panerabread.com/en-us/company/media-kit.html",
        "popeyes": "https://www.popeyes.com/media-kit",
        "kfc": "https://global.kfc.com/media-kit/",
        "chickfila": "https://www.chick-fil-a.com/media-kit",
        "jackinthebox": "https://www.jackinthebox.com/media-kit",
        "culvers": "https://www.culvers.com/media-kit",
        "raisingcanes": "https://www.raisingcanes.com/media-kit",
        "jamba": "https://www.jamba.com/media-kit",
        "auntieannes": "https://www.auntieannes.com/media-kit",
        "krispykreme": "https://www.krispykreme.com/media-kit",
        "dairyqueen": "https://www.dairyqueen.com/media-kit",
        "longjohnsilvers": "https://www.ljsilvers.com/media-kit",
        "pandaexpress": "https://www.pandaexpress.com/media-kit",
        "littlecaesars": "https://littlecaesars.com/en-us/about-us/media-kit.html",
        "firehouse": "https://www.firehousesubs.com/media-kit/",
        "jerseymikes": "https://www.jerseymikes.com/media-kit",
        "jimmyjohns": "https://www.jimmyjohns.com/media-kit",
        "wingstop": "https://www.wingstop.com/media-kit",
        "zaxbys": "https://www.zaxbys.com/media-kit",
        "papa-johns": "https://www.papajohns.com/media-kit",
        "baskinrobbins": "https://www.baskinrobbins.com/media-kit",
        "ihop": "https://www.ihop.com/en/newsroom/media-kit",
        "dennys": "https://www.dennys.com/media-kit",
        "outback": "https://www.outback.com/media-kit",
        "olivegarden": "https://www.olivegarden.com/media-kit",
        "redlobster": "https://www.redlobster.com/media-kit",
        "applebees": "https://www.applebees.com/media-kit",
        "chilis": "https://www.chilis.com/media-kit",
        "tgifridays": "https://www.tgifridays.com/media-kit",
        "cheesecakefactory": "https://www.thecheesecakefactory.com/media-kit",
        "maggiannos": "https://www.maggianos.com/media-kit",
        "pfchangs": "https://www.pfchangs.com/media-kit",
        "yardhouse": "https://www.yardhouse.com/media-kit",
        "ruthschris": "https://www.ruthschris.com/media-kit",
        "fogo": "https://fogodechao.com/media-kit/",
        "texasroadhouse": "https://www.texasroadhouse.com/media-kit",
        "logansteakhouse": "https://www.logansroadhouse.com/media-kit",
        "goldencorral": "https://www.goldencorral.com/media-kit",
        "sizzler": "https://www.sizzler.com/media-kit",
        "crackerbarrel": "https://www.crackerbarrel.com/media-kit",
        "bobevans": "https://www.bobevans.com/media-kit",
        "perkins": "https://www.perkinsrestaurants.com/media-kit",
        "shoneys": "https://www.shoneys.com/media-kit",
        "wafflehouse": "https://www.wafflehouse.com/media-kit",
        "friendlys": "https://www.friendlysrestaurants.com/media-kit",
        "steaknshake": "https://www.steaknshake.com/media-kit",
        "whitecastle": "https://www.whitecastle.com/media-kit",
        "fiveguys": "https://www.fiveguys.com/media-kit",
        "smashburger": "https://www.smashburger.com/media-kit",
        "freddys": "https://www.freddysusa.com/media-kit",
        "culvers": "https://www.culvers.com/media-kit",
        "in-n-out": "https://www.in-n-out.com/media-kit",
        "habitburger": "https://www.habitburger.com/media-kit",
        "del-taco": "https://www.deltaco.com/media-kit",
        "elpollo": "https://www.elpolloloco.com/media-kit",
        "pollo-tropical": "https://www.pollotropical.com/media-kit",
        "bostonmarket": "https://www.bostonmarket.com/media-kit",
        "qdoba": "https://www.qdoba.com/media-kit",
        "moes": "https://www.moes.com/media-kit",
        "schlotzskys": "https://www.schlotzskys.com/media-kit",
        "potbelly": "https://www.potbelly.com/media-kit",
        "panerabread": "https://www.panerabread.com/en-us/company/media-kit.html",
        # Add more as needed
    }
    url = vendor_urls.get(vendor)
    if not url:
        print(f"Unknown or unsupported vendor: {vendor}")
        return []

    try:
        html = requests.get(url, timeout=20).text
    except requests.exceptions.Timeout:
        print(f"[{vendor}] ERROR: Timed out fetching {url}")
        return []
    except Exception as e:
        print(f"[{vendor}] ERROR: {e}")
        return []
    soup = BeautifulSoup(html, "html.parser")

    found = []
    print(f"\n[{vendor}] assets found on page:")
    for a in soup.find_all("a", href=True):
        href = getattr(a, "attrs", {}).get("href", "")
        if isinstance(href, str) and any(
            href.lower().endswith(ext)
            for ext in (".svg", ".png", ".eps", ".ai", ".pdf", ".vss", ".vsdx")
        ):
            print(" •", href)
            found.append(href)
            if auto_download:
                try:
                    fname = os.path.basename(href.split("?")[0])
                    out_path = os.path.join(OUT_DIR, fname)
                    r = requests.get(href, timeout=15)
                    with open(out_path, "wb") as fp:
                        fp.write(r.content)
                    print(f"   [downloaded → {out_path}]")
                except Exception as e:
                    print(f"   [download failed: {e}]")
    return found


# ------------------------------ main ----------------------------------------
if __name__ == "__main__":
    # Equipment vendors commonly used in quick service restaurants
    equipment_vendors = [
        "Fortinet",
        "Meraki",
        "Cisco",
        "Aruba",
        "Panasonic",
        "Elo",
        "Micros",
        "PAR",
        "HP",
        "Epson",
        "TouchDynamic",
        "Posiflex",
        "Samsung",
        "NEC",
        "Sharp",
        "Dell",
        "Lenovo",
        "ASUS",
        "Acer",
        "Star",
        "Bixolon",
        "Zebra",
        "Honeywell",
        "Ingenico",
        "Verifone",
        "Square",
        "Clover",
        "NCR",
        "Toshiba",
        "Oracle",
        "APG Cash Drawer",
        "Logic Controls",
        "Bematech",
        "PioneerPOS",
        "Radiant Systems",
        "Diebold Nixdorf",
        "Fujitsu",
        "Casio",
        "Brother",
        "Citizen",
        "Seiko",
        "Datalogic",
        "Socket Mobile",
        "MagTek",
        "IDTech",
        "Cherry",
        "Unitech",
        "Honeywell",
        "Bixolon",
        "Star Micronics",
        "Epson",
        "Zebra",
        "HP",
        "Dell",
        "Lenovo",
        "Samsung",
        "NEC",
        "Sharp",
        "Acer",
        "ASUS",
        "Panasonic",
        "Elo Touch",
        "Ingenico",
        "Verifone",
        "Square",
        "Clover",
        "Micros",
        "PAR",
        "TouchDynamic",
        "Posiflex",
    ]
    # Device types for endpoints (for icon search only)
    device_types = [
        "Kitchen Display",
        "POS Terminal",
        "Kiosk",
        "Digital Menu Board",
        "Tablet",
        "Register",
        "Receipt Printer",
        "Label Printer",
        "Scanner",
        "Card Reader",
        "Cash Drawer",
        "Scale",
        "Customer Display",
    ]

    # Search and download icons for equipment vendors
    for vendor in equipment_vendors:
        print(f"Searching Simple Icons for '{vendor}'…")
        matches = list_simpleicons(vendor)
        if matches:
            print(f"Found {len(matches)} matches:")
            for m in matches:
                if matches.index(m) == 0:
                    print(f"Available fields: {list(m.keys())}")
                title = m.get("title", "Unknown")
                slug = m.get("slug") or m.get("title", "").lower().replace(" ", "")
                print(f" • {title}  (slug = {slug})")
            # Try to download the first match
            first_match = matches[0]
            slug = first_match.get("slug") or first_match.get(
                "title", ""
            ).lower().replace(" ", "")
            title = first_match.get("title", "Unknown")
            if slug:
                download_simpleicon(
                    slug, manufacturer=vendor, device_type=None, title=title, tags=None
                )
        else:
            print(f"No {vendor} icons found")

        print(f"\nSearching {vendor} media page...")
        scrape_vendor_media(vendor, auto_download=True)

    # Search and download icons for device types (icon only, no media kit)
    for dtype in device_types:
        print(f"Searching Simple Icons for '{dtype}'…")
        matches = list_simpleicons(dtype)
        if matches:
            print(f"Found {len(matches)} matches:")
            for m in matches:
                if matches.index(m) == 0:
                    print(f"Available fields: {list(m.keys())}")
                title = m.get("title", "Unknown")
                slug = m.get("slug") or m.get("title", "").lower().replace(" ", "")
                print(f" • {title}  (slug = {slug})")
            # Try to download the first match
            first_match = matches[0]
            slug = first_match.get("slug") or first_match.get(
                "title", ""
            ).lower().replace(" ", "")
            title = first_match.get("title", "Unknown")
            if slug:
                download_simpleicon(
                    slug, manufacturer=None, device_type=dtype, title=title, tags=None
                )
        else:
            print(f"No {dtype} icons found")
