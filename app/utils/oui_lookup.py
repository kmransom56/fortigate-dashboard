import requests
import logging
import os

logger = logging.getLogger(__name__)


def get_manufacturer_from_mac(mac_address):
    """
    Looks up the manufacturer of a device based on its MAC address using an external API.
    """
    oui = (
        mac_address[:8].upper().replace("-", "").replace(":", "")
    )  # Extract first 6 hex digits (3 bytes)

    # Use macvendors.com API
    url = f"https://api.macvendors.com/{oui}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        manufacturer = response.text.strip()
        logger.info(f"Manufacturer found for OUI {oui}: {manufacturer}")
        return manufacturer
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
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
