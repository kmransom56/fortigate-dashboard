"""
Enhanced MAC Address Lookup Service

Leverages multiple online APIs to get detailed manufacturer and device type
information for more accurate icon mapping.
"""

import requests
import logging
import time
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EnhancedMACLookup:
    """Enhanced MAC lookup with multiple API sources and device type inference"""

    def __init__(
        self, cache_file="app/data/enhanced_mac_cache.json", max_requests_per_minute=50
    ):
        self.cache_file = cache_file
        self.max_requests_per_minute = max_requests_per_minute
        self.request_timestamps = []
        self.cache = self._load_cache()

        # Ensure cache directory exists
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)

        # Manufacturer to device type mapping for better icon selection
        self.manufacturer_device_type_map = {
            # Apple devices
            "Apple Inc.": ["laptop", "phone", "tablet", "watch"],
            "Apple": ["laptop", "phone", "tablet", "watch"],
            # Microsoft devices
            "Microsoft Corporation": ["laptop", "desktop", "tablet"],
            "Microsoft": ["laptop", "desktop", "tablet"],
            # Network equipment manufacturers
            "Cisco Systems": ["router", "switch", "access-point"],
            "Cisco": ["router", "switch", "access-point"],
            "Fortinet": ["firewall", "switch", "access-point"],
            "Juniper Networks": ["router", "switch", "firewall"],
            "Hewlett Packard": ["printer", "server", "laptop"],
            "HP": ["printer", "server", "laptop"],
            # Dell devices - comprehensive mapping
            "Dell Inc.": ["laptop", "desktop", "server", "printer", "monitor"],
            "Dell": ["laptop", "desktop", "server", "printer", "monitor"],
            "Dell Technologies": ["laptop", "desktop", "server"],
            "Dell Computer": ["laptop", "desktop", "server"],
            # Raspberry Pi devices
            "Raspberry Pi Trading Ltd": ["raspberry-pi", "iot-device", "endpoint"],
            "Raspberry Pi": ["raspberry-pi", "iot-device", "endpoint"],
            "Raspberry Pi Foundation": ["raspberry-pi", "iot-device", "endpoint"],
            # Samsung devices - including TVs
            "Samsung Electronics": [
                "phone",
                "tablet",
                "tv",
                "printer",
                "monitor",
                "smart-tv",
            ],
            "Samsung": ["phone", "tablet", "tv", "printer", "monitor", "smart-tv"],
            "Samsung Electronics Co.": ["phone", "tablet", "tv", "printer", "smart-tv"],
            "Samsung Techwin": ["camera", "surveillance"],
            # Amazon devices - including Fire TV Cube
            "Amazon Technologies": [
                "tablet",
                "smart-speaker",
                "fire-tv",
                "fire-cube",
                "smart-tv",
            ],
            "Amazon": ["tablet", "smart-speaker", "fire-tv", "fire-cube", "smart-tv"],
            "Amazon.com": ["tablet", "smart-speaker", "fire-tv", "fire-cube"],
            "Amazon Fulfillment": ["fire-tv", "fire-cube", "smart-tv"],
            # IoT and smart devices
            "Google Inc.": ["phone", "tablet", "smart-speaker", "chromecast"],
            "Google": ["phone", "tablet", "smart-speaker", "chromecast"],
            # POS and restaurant equipment
            "Ingenico": ["payment-terminal"],
            "Verifone": ["payment-terminal"],
            "NCR Corporation": ["pos", "printer"],
            "NCR": ["pos", "printer"],
            "Micros Systems": ["pos"],
            "Micros": ["pos"],
        }

    def _load_cache(self) -> dict:
        """Load cached MAC lookups from disk"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} cached enhanced MAC entries")
                    return data
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
        return {}

    def _save_cache(self):
        """Save cache to disk for persistence"""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save cache: {e}")

    def _can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limits"""
        now = time.time()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps if now - ts < 60
        ]
        return len(self.request_timestamps) < self.max_requests_per_minute

    def _wait_for_rate_limit(self):
        """Wait until we can make another request"""
        if self.request_timestamps:
            oldest_request = min(self.request_timestamps)
            wait_time = 60 - (time.time() - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)

    def _lookup_macvendors(self, oui: str) -> Optional[Dict[str, Any]]:
        """Lookup using macvendors.com API"""
        url = f"https://api.macvendors.com/{oui}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                manufacturer = response.text.strip()
                return {
                    "manufacturer": manufacturer,
                    "source": "macvendors.com",
                }
            elif response.status_code == 429:
                logger.warning(f"Rate limited by macvendors.com for OUI {oui}")
                return None
        except Exception as e:
            logger.debug(f"macvendors.com lookup failed for {oui}: {e}")
        return None

    def _lookup_macaddress_io(self, mac: str) -> Optional[Dict[str, Any]]:
        """Lookup using macaddress.io API (requires API key for full features)"""
        # Free tier: basic lookup without API key
        url = f"https://api.macaddress.io/v1?apiKey=free&output=json&search={mac}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                vendor = data.get("vendorDetails", {}).get("companyName", "")
                if vendor:
                    return {
                        "manufacturer": vendor,
                        "source": "macaddress.io",
                    }
        except Exception as e:
            logger.debug(f"macaddress.io lookup failed for {mac}: {e}")
        return None

    def _lookup_maclookup_app(self, mac: str) -> Optional[Dict[str, Any]]:
        """Lookup using maclookup.app API"""
        url = f"https://api.maclookup.app/v2/macs/{mac}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                company = data.get("company", "")
                if company:
                    return {
                        "manufacturer": company,
                        "source": "maclookup.app",
                    }
        except Exception as e:
            logger.debug(f"maclookup.app lookup failed for {mac}: {e}")
        return None

    def _infer_device_type(self, manufacturer: str) -> list:
        """Infer likely device types from manufacturer name"""
        manufacturer_lower = manufacturer.lower()
        device_types = []

        # Check exact matches first
        for mfr, types in self.manufacturer_device_type_map.items():
            if mfr.lower() in manufacturer_lower or manufacturer_lower in mfr.lower():
                device_types.extend(types)

        # Pattern-based inference
        if "network" in manufacturer_lower or "cisco" in manufacturer_lower:
            device_types.append("router")
        if "wireless" in manufacturer_lower or "wifi" in manufacturer_lower:
            device_types.append("access-point")
        if "printer" in manufacturer_lower or "print" in manufacturer_lower:
            device_types.append("printer")
        if "camera" in manufacturer_lower or "surveillance" in manufacturer_lower:
            device_types.append("camera")
        if "phone" in manufacturer_lower or "mobile" in manufacturer_lower:
            device_types.append("phone")
        if "tablet" in manufacturer_lower or "ipad" in manufacturer_lower:
            device_types.append("tablet")
        if "laptop" in manufacturer_lower or "notebook" in manufacturer_lower:
            device_types.append("laptop")
        if "server" in manufacturer_lower:
            device_types.append("server")
        if "pos" in manufacturer_lower or "point of sale" in manufacturer_lower:
            device_types.append("pos")
        if "payment" in manufacturer_lower or "terminal" in manufacturer_lower:
            device_types.append("payment-terminal")
        # Dell-specific patterns
        if "dell" in manufacturer_lower:
            device_types.extend(["laptop", "desktop", "server"])
        # Raspberry Pi patterns
        if "raspberry" in manufacturer_lower or "pi" in manufacturer_lower:
            device_types.extend(["raspberry-pi", "iot-device"])
        # Samsung TV patterns
        if "samsung" in manufacturer_lower and (
            "tv" in manufacturer_lower or "television" in manufacturer_lower
        ):
            device_types.extend(["tv", "smart-tv"])
        # Amazon Fire TV Cube patterns
        if "amazon" in manufacturer_lower and (
            "fire" in manufacturer_lower or "cube" in manufacturer_lower
        ):
            device_types.extend(["fire-tv", "fire-cube", "smart-tv"])
        if "fire cube" in manufacturer_lower or "firecube" in manufacturer_lower:
            device_types.extend(["fire-cube", "smart-tv"])

        # Remove duplicates while preserving order
        seen = set()
        unique_types = []
        for dt in device_types:
            if dt not in seen:
                seen.add(dt)
                unique_types.append(dt)

        return unique_types if unique_types else ["endpoint"]

    def lookup(self, mac_address: str) -> Dict[str, Any]:
        """
        Enhanced MAC address lookup with multiple API sources and device type inference.

        Args:
            mac_address: MAC address in any format (with or without separators)

        Returns:
            Dictionary with:
            - manufacturer: Manufacturer name
            - device_types: List of likely device types
            - source: API source used
            - cached: Whether result was from cache
        """
        # Normalize MAC and extract OUI
        mac_clean = (
            mac_address.upper().replace("-", "").replace(":", "").replace(".", "")
        )
        oui = mac_clean[:6]

        # Check cache first
        if oui in self.cache:
            cached_result = self.cache[oui].copy()
            cached_result["cached"] = True
            logger.debug(
                f"Cached result for OUI {oui}: {cached_result.get('manufacturer')}"
            )
            return cached_result

        # Check if we can make a request
        if not self._can_make_request():
            self._wait_for_rate_limit()

        # Try multiple APIs in order
        result = None
        for api_func in [
            self._lookup_macvendors,
            self._lookup_macaddress_io,
            self._lookup_maclookup_app,
        ]:
            try:
                if api_func == self._lookup_macvendors:
                    result = api_func(oui)
                else:
                    result = api_func(mac_clean)

                if result:
                    self.request_timestamps.append(time.time())
                    break
            except Exception as e:
                logger.debug(f"API lookup failed: {e}")
                continue

        # If no result, return unknown
        if not result:
            result = {
                "manufacturer": "Unknown",
                "source": "none",
            }

        # Infer device types from manufacturer
        manufacturer = result.get("manufacturer", "Unknown")
        device_types = self._infer_device_type(manufacturer)

        # Build final result
        final_result = {
            "manufacturer": manufacturer,
            "device_types": device_types,
            "source": result.get("source", "none"),
            "cached": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Cache the result
        self.cache[oui] = final_result.copy()
        self._save_cache()

        logger.info(
            f"MAC lookup for {mac_address[:8]}: {manufacturer} -> {device_types}"
        )
        return final_result


# Global instance
_enhanced_lookup = EnhancedMACLookup()


def get_enhanced_mac_info(mac_address: str) -> Dict[str, Any]:
    """
    Get enhanced MAC address information including manufacturer and device type hints.

    Args:
        mac_address: MAC address in any format

    Returns:
        Dictionary with manufacturer, device_types, source, and cached status
    """
    return _enhanced_lookup.lookup(mac_address)


def get_manufacturer_from_mac_enhanced(mac_address: str) -> Optional[str]:
    """
    Get manufacturer name from MAC address using enhanced lookup.

    Args:
        mac_address: MAC address in any format

    Returns:
        Manufacturer name or None
    """
    result = get_enhanced_mac_info(mac_address)
    manufacturer = result.get("manufacturer")
    return manufacturer if manufacturer != "Unknown" else None


def get_device_types_from_mac(mac_address: str) -> list:
    """
    Get likely device types from MAC address based on manufacturer.

    Args:
        mac_address: MAC address in any format

    Returns:
        List of likely device types
    """
    result = get_enhanced_mac_info(mac_address)
    return result.get("device_types", ["endpoint"])


def get_cache_stats() -> dict:
    """Get cache statistics"""
    return {
        "cached_entries": len(_enhanced_lookup.cache),
        "cache_file": _enhanced_lookup.cache_file,
        "requests_in_last_minute": len(_enhanced_lookup.request_timestamps),
        "rate_limit": _enhanced_lookup.max_requests_per_minute,
    }
