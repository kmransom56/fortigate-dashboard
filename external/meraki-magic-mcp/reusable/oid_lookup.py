"""
OID Lookup Utilities

Provides multiple methods for looking up OID information without requiring
API keys. Includes fallback mechanisms using free public OID databases.

This module provides alternatives to the OidView API for cases where:
- API key registration is not working
- You need free, no-key-required OID lookups
- You want local caching and offline capability
"""

import requests
import re
from typing import Optional, Dict, Any
from urllib.parse import quote
import time


class OIDLookup:
    """
    Multi-source OID lookup with fallback mechanisms.
    
    Tries multiple free OID lookup services in order:
    1. OidRef.com (free, no API key)
    2. Alvestrand.no (free, no API key)
    3. OidInfo.com (free, no API key)
    4. Local ASCII decoding (fallback)
    """
    
    def __init__(self, cache: Optional[Dict[str, Any]] = None):
        """
        Initialize OID lookup with optional cache.
        
        Args:
            cache: Dictionary to cache OID lookups (optional)
        """
        self.cache = cache or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Network-Observability-Platform/1.0'
        })
        self.timeout = 5
    
    def lookup_oid_ref(self, oid: str) -> Optional[Dict[str, Any]]:
        """
        Look up OID using OidRef.com (free, no API key required).
        
        Note: API endpoint doesn't exist, but HTML pages may work.
        
        Args:
            oid: Object Identifier
            
        Returns:
            Dictionary with 'name' and 'description' if found, None otherwise
        """
        try:
            # Try HTML page (API endpoint doesn't exist)
            url = f"https://oidref.com/{oid}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                html = response.text
                # Try to extract name and description from HTML
                # Look for title or heading
                title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
                h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
                desc_match = re.search(r'<p[^>]*>([^<]+)</p>', html, re.IGNORECASE)
                
                name = None
                if h1_match:
                    name = h1_match.group(1).strip()
                elif title_match:
                    name = title_match.group(1).strip()
                
                if name:
                    return {
                        'name': name,
                        'description': desc_match.group(1).strip() if desc_match else '',
                        'source': 'oidref.com'
                    }
        except Exception:
            pass
        
        return None
    
    def lookup_alvestrand(self, oid: str) -> Optional[Dict[str, Any]]:
        """
        Look up OID using Alvestrand.no (free, no API key required).
        
        This is a reliable source that works well for standard SNMP OIDs.
        
        Args:
            oid: Object Identifier
            
        Returns:
            Dictionary with 'name' and 'description' if found, None otherwise
        """
        try:
            url = f"https://www.alvestrand.no/objectid/{oid}.html"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                html = response.text
                # Extract information from HTML
                # Title format: "OID description for {oid} - {name}"
                title_match = re.search(r'<title>OID description for [^-]+ - ([^<]+)</title>', html, re.IGNORECASE)
                h1_match = re.search(r'<h1[^>]*>([^-]+) - ([^<]+)</h1>', html, re.IGNORECASE)
                desc_match = re.search(r'<strong>OID description:</strong><br>\s*([^<]+)', html, re.IGNORECASE)
                
                name = None
                if h1_match:
                    # Extract name from "OID - Name" format
                    name = h1_match.group(2).strip()
                elif title_match:
                    name = title_match.group(1).strip()
                
                description = ''
                if desc_match:
                    description = desc_match.group(1).strip()
                
                if name:
                    return {
                        'name': name,
                        'description': description,
                        'source': 'alvestrand.no'
                    }
        except Exception:
            pass
        
        return None
    
    def lookup_oid_info(self, oid: str) -> Optional[Dict[str, Any]]:
        """
        Look up OID using OidInfo.com (free, no API key required).
        
        Args:
            oid: Object Identifier
            
        Returns:
            Dictionary with 'name' and 'description' if found, None otherwise
        """
        try:
            url = f"https://oid-info.com/get/{oid}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data:
                        return {
                            'name': data.get('name', ''),
                            'description': data.get('description', ''),
                            'source': 'oid-info.com'
                        }
                except:
                    # Try HTML parsing
                    html = response.text
                    name_match = re.search(r'<title>([^<]+)</title>', html)
                    if name_match:
                        return {
                            'name': name_match.group(1).strip(),
                            'description': '',
                            'source': 'oid-info.com'
                        }
        except Exception:
            pass
        
        return None
    
    def lookup_mibdb(self, oid: str) -> Optional[Dict[str, Any]]:
        """
        Look up OID using MIB-Database.com (free, no API key required).
        
        Args:
            oid: Object Identifier
            
        Returns:
            Dictionary with 'name' and 'description' if found, None otherwise
        """
        try:
            # MIB-Database.com uses a search/query interface
            url = f"https://www.mib-depot.com/cgi-bin/getmib.cgi?oid={oid}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                html = response.text
                # Try to extract OID name from HTML
                name_match = re.search(r'OID:\s*([^\s<]+)', html, re.IGNORECASE)
                desc_match = re.search(r'Description[:\s]+([^<\n]+)', html, re.IGNORECASE)
                
                if name_match:
                    return {
                        'name': name_match.group(1).strip(),
                        'description': desc_match.group(1).strip() if desc_match else '',
                        'source': 'mib-depot.com'
                    }
        except Exception:
            pass
        
        return None
    
    def lookup_snmplink(self, oid: str) -> Optional[Dict[str, Any]]:
        """
        Look up OID using SNMPLink.org (free, no API key required).
        
        Args:
            oid: Object Identifier
            
        Returns:
            Dictionary with 'name' and 'description' if found, None otherwise
        """
        try:
            # SNMPLink uses a different URL structure
            url = f"https://www.snmplink.org/oid/{oid.replace('.', '-')}.html"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                html = response.text
                # Extract information from HTML
                name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
                desc_match = re.search(r'<p[^>]*>([^<]+)</p>', html, re.IGNORECASE)
                
                if name_match:
                    return {
                        'name': name_match.group(1).strip(),
                        'description': desc_match.group(1).strip() if desc_match else '',
                        'source': 'snmplink.org'
                    }
        except Exception:
            pass
        
        return None
    
    def decode_oid_ascii(self, oid_string: str) -> Optional[str]:
        """
        Decode OID string using ASCII character conversion.
        
        This is a fallback method that converts numeric OID parts to ASCII characters.
        Useful for device names encoded as OIDs (e.g., FortiAP-1.16.70.80...).
        
        Args:
            oid_string: OID string (e.g., "1.16.70.80.50.51")
            
        Returns:
            Decoded string if valid ASCII found, None otherwise
        """
        decoded = ""
        parts = oid_string.split(".")
        found_printable = False
        
        for part in parts:
            if part.isdigit():
                num = int(part)
                if 32 <= num <= 126:  # Printable ASCII range
                    decoded += chr(num)
                    found_printable = True
                elif num < 32:
                    # Non-printable control character - skip it but continue
                    continue
                else:
                    # Number > 126 - not ASCII, might be invalid
                    # But continue in case there's valid data after
                    continue
            else:
                # Non-numeric part - invalid for ASCII decoding
                return None
        
        # Return decoded string if we found at least some printable characters
        return decoded if found_printable and len(decoded) > 0 else None
    
    def lookup(self, oid: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Look up OID using multiple sources with fallback.
        
        Args:
            oid: Object Identifier
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with 'name', 'description', and 'source' if found, None otherwise
        """
        # Check cache first
        if use_cache and oid in self.cache:
            return self.cache[oid]
        
        # Try multiple sources in order (most reliable first)
        sources = [
            self.lookup_alvestrand,  # Most reliable for standard SNMP OIDs
            self.lookup_oid_ref,
            self.lookup_oid_info,
            self.lookup_mibdb,
            self.lookup_snmplink,
        ]
        
        for source_func in sources:
            try:
                result = source_func(oid)
                if result:
                    # Cache the result
                    if use_cache:
                        self.cache[oid] = result
                    return result
            except Exception:
                continue
        
        # If all sources fail, try ASCII decoding for numeric OID strings
        if re.match(r'^\d+(\.\d+)+$', oid):
            decoded = self.decode_oid_ascii(oid)
            if decoded:
                result = {
                    'name': decoded,
                    'description': 'Decoded from ASCII',
                    'source': 'ascii_decode'
                }
                if use_cache:
                    self.cache[oid] = result
                return result
        
        return None
    
    def get_name(self, oid: str) -> Optional[str]:
        """
        Convenience method to get just the OID name.
        
        Args:
            oid: Object Identifier
            
        Returns:
            OID name if found, None otherwise
        """
        result = self.lookup(oid)
        return result.get('name') if result else None
    
    def get_description(self, oid: str) -> Optional[str]:
        """
        Convenience method to get just the OID description.
        
        Args:
            oid: Object Identifier
            
        Returns:
            OID description if found, None otherwise
        """
        result = self.lookup(oid)
        return result.get('description') if result else None


def decode_device_oid(oid_string: str, device_type: str = "FortiAP") -> str:
    """
    Decode OID-based device name with multiple fallback strategies.
    
    This function is designed to work with NeDi's OID-based device names
    like "FortiAP-1.16.70.80.50.51.49.70.84.70.50.48.48.50.51.48.52.51"
    
    The OID format is typically: prefix (1.16) + ASCII-encoded device info
    Example: 1.16.70.80.50.51.49.70.84.70.50.48.48.50.51.48.52.51
             decodes to: FP231F-20035593 (skipping the 1.16 prefix)
    
    Args:
        oid_string: OID string (numeric parts only, e.g., "1.16.70.80...")
        device_type: Device type prefix (e.g., "FortiAP", "FortiSwitch")
        
    Returns:
        Decoded device name (e.g., "FortiAP-FP231F-20035593")
    """
    lookup = OIDLookup()
    
    # First try full OID lookup (for standard SNMP OIDs)
    result = lookup.lookup(oid_string)
    if result and result.get('name') and result.get('source') != 'ascii_decode':
        return f"{device_type}-{result['name']}"
    
    # For device OID strings, try ASCII decoding
    # Device OIDs often start with a prefix like "1.16" that should be skipped
    parts = oid_string.split('.')
    
    # Try skipping common prefix patterns (e.g., "1.16", "1.3.6.1")
    # First, try skipping first 2 parts if they look like a prefix
    if len(parts) >= 3:
        if parts[0] == '1' and parts[1].isdigit() and int(parts[1]) < 20:
            # Likely a prefix, skip it
            remaining = '.'.join(parts[2:])
            decoded = lookup.decode_oid_ascii(remaining)
            if decoded and len(decoded) > 0:
                return f"{device_type}-{decoded}"
    
    # If prefix skipping didn't work, try full OID
    decoded = lookup.decode_oid_ascii(oid_string)
    if decoded and len(decoded) > 0:
        return f"{device_type}-{decoded}"
    
    # Last resort: return original
    return f"{device_type}-{oid_string}"
