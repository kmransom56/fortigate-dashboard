import requests
import logging
import os

logger = logging.getLogger(__name__)


def get_manufacturer_from_mac(mac_address):
    """
    Looks up the manufacturer of a device based on its MAC address using custom mappings and an external API.
    """
    # Normalize MAC and extract OUI (first 6 hex digits)
    mac_clean = mac_address.upper().replace("-", "").replace(":", "")
    oui = mac_clean[:6]

    # Custom OUI mappings for digital menu board and POS vendors
    custom_oui_map = {
        # Digital Menu Board Manufacturers
        "A0B1C2": "Coates",  # Example OUI for Coates
        "B1C2D3": "Xenial",  # Example OUI for Xenial
        "001F32": "Samsung",  # Samsung (real OUI)
        # POS Vendors
        "000C29": "Infor",  # Example OUI for Infor
        "0004A3": "Micros",  # Micros (Oracle)
        "0002C7": "NCR",  # NCR (real OUI)
    }

    if oui in custom_oui_map:
        logger.info(f"Custom manufacturer found for OUI {oui}: {custom_oui_map[oui]}")
        return custom_oui_map[oui]

    # Use macvendors.com API as fallback
    url = f"https://api.macvendors.com/{oui}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        manufacturer = response.text.strip()
        logger.info(f"Manufacturer found for OUI {oui}: {manufacturer}")
        return manufacturer
    except requests.exceptions.HTTPError as e:
        status_code = getattr(e.response, "status_code", None)
        if status_code == 404:
            logger.warning(f"OUI {oui} not found in macvendors.com database.")
        else:
            logger.error(f"HTTP error looking up OUI {oui}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error looking up OUI {oui}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error looking up OUI {oui}: {e}")
        return None
