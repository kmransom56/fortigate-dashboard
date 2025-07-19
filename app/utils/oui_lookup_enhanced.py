import requests
import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

class OUILookupCache:
    """Process automation for MAC vendor lookups with intelligent rate limiting"""
    
    def __init__(self, cache_file="app/data/oui_cache.json", max_requests_per_minute=50):
        self.cache_file = cache_file
        self.max_requests_per_minute = max_requests_per_minute
        self.request_timestamps = []
        self.cache = self._load_cache()
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    def _load_cache(self) -> dict:
        """Load cached OUI lookups from disk"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} cached OUI entries")
                    return data
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache to disk for persistence"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save cache: {e}")
    
    def _can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limits"""
        now = time.time()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                 if now - ts < 60]
        
        return len(self.request_timestamps) < self.max_requests_per_minute
    
    def _wait_for_rate_limit(self):
        """Wait until we can make another request"""
        if self.request_timestamps:
            oldest_request = min(self.request_timestamps)
            wait_time = 60 - (time.time() - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)

# Global cache instance
_cache_instance = OUILookupCache()

def get_manufacturer_from_mac(mac_address: str) -> Optional[str]:
    """
    Automated MAC vendor lookup with intelligent caching and rate limiting.
    Perfect for device management automation workflows.
    """
    # Normalize MAC and extract OUI (first 6 hex digits)
    mac_clean = mac_address.upper().replace("-", "").replace(":", "")
    oui = mac_clean[:6]

    # Custom OUI mappings for digital menu board and POS vendors
    custom_oui_map = {
        # Digital Menu Board Manufacturers
        "A0B1C2": "Coates",
        "B1C2D3": "Xenial", 
        "001F32": "Samsung",
        # POS Vendors
        "000C29": "Infor",
        "0004A3": "Micros",
        "0002C7": "NCR",
        # Common network devices (expand as needed)
        "FC8C11": "Microsoft Corporation",
        "54BF64": "Dell Inc.",
        "3C18A0": "Hon Hai Precision",
        "DCA632": "Apple Inc.",
    }

    # 1. Check custom mappings first (fastest)
    if oui in custom_oui_map:
        logger.info(f"Custom manufacturer found for OUI {oui}: {custom_oui_map[oui]}")
        return custom_oui_map[oui]

    # 2. Check cache (fast)
    if oui in _cache_instance.cache:
        logger.debug(f"Cached manufacturer found for OUI {oui}: {_cache_instance.cache[oui]}")
        return _cache_instance.cache[oui]

    # 3. API lookup with rate limiting (slow but automated)
    if not _cache_instance._can_make_request():
        _cache_instance._wait_for_rate_limit()

    url = f"https://api.macvendors.com/{oui}"
    try:
        _cache_instance.request_timestamps.append(time.time())
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            manufacturer = response.text.strip()
            # Cache successful lookups
            _cache_instance.cache[oui] = manufacturer
            _cache_instance._save_cache()
            logger.info(f"Manufacturer found for OUI {oui}: {manufacturer}")
            return manufacturer
        elif response.status_code == 404:
            # Cache "not found" to avoid repeated lookups
            _cache_instance.cache[oui] = "Unknown"
            _cache_instance._save_cache()
            logger.warning(f"OUI {oui} not found in database")
            return "Unknown"
        elif response.status_code == 429:
            logger.warning(f"Rate limited for OUI {oui}, will retry with backoff")
            time.sleep(5)  # Brief pause for rate limiting
            return "Rate Limited"
        else:
            logger.error(f"HTTP {response.status_code} for OUI {oui}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error looking up OUI {oui}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error looking up OUI {oui}: {e}")
        return None

def get_cache_stats() -> dict:
    """Get automation metrics for monitoring"""
    return {
        "cached_entries": len(_cache_instance.cache),
        "cache_file": _cache_instance.cache_file,
        "requests_in_last_minute": len(_cache_instance.request_timestamps),
        "rate_limit": _cache_instance.max_requests_per_minute
    }

def clear_cache():
    """Clear the OUI cache (useful for testing)"""
    _cache_instance.cache.clear()
    _cache_instance._save_cache()
    logger.info("OUI cache cleared")
