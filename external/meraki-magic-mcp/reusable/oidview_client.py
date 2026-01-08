"""
OidView MIB API Client

A Python client for the OidView MIB API (https://www.oidview.com/api/api.html)
that allows querying and searching thousands of SNMP MIBs programmatically.

⚠️  NOTE: API key registration may not be working. Consider using:
    - reusable.oid_lookup.OIDLookup (free, no API key required)
    - Alternative free OID lookup services

The API provides access to MIB information including:
- Vendor information and MIBs
- MIB object details by OID or name
- MIB object relationships (parent, children, siblings)
- MIB search capabilities

To request an API key (if registration is working):
    Visit: https://www.oidview.com/contact.html

Example usage:
    from reusable.oidview_client import OidViewClient
    
    client = OidViewClient(api_key="your-api-key")
    
    # Get MIB object info by OID
    result = client.get_mib_object_info(oid="1.3.6.1.2.1.1.1.0")
    
    # Get MIB object info by name
    result = client.get_mib_object_info_by_name(name="sysDescr", vendor="RFC1213")
    
    # Search for MIB objects
    results = client.search_mib_objects(vendor="Fortinet", token="system")
"""

import requests
from typing import Optional, Dict, List, Any
from urllib.parse import urlencode


class OidViewClient:
    """
    Client for the OidView MIB API.
    
    The API requires an API key for authentication. You can sign up at:
    https://www.oidview.com/api/api.html
    
    API Documentation: https://www.oidview.com/api/api.html
    """
    
    BASE_URL = "https://www.oidview.com/api"
    API_VERSION = "v1"
    SERVICE_NAME = "mibService"
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the OidView API client.
        
        Args:
            api_key: Your OidView API key (required for most endpoints)
            base_url: Override the default base URL (optional)
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
        
        # Set default headers for JSON responses
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Network-Observability-Platform/1.0'
        })
    
    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Make a request to the OidView API.
        
        Args:
            endpoint: API endpoint name (e.g., 'getMibObjectInfo')
            params: Query parameters
            format: Response format ('json' or 'xml')
            
        Returns:
            API response as dictionary (JSON) or string (XML)
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key if provided
        if params is None:
            params = {}
        if self.api_key:
            params['key'] = self.api_key
        
        # Set Accept header based on format
        headers = self.session.headers.copy()
        if format == 'json':
            headers['Accept'] = 'application/json'
        else:
            headers['Accept'] = 'application/xml'
        
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            if format == 'json':
                return response.json()
            else:
                return response.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def get_vendors(self, format: str = 'json') -> Dict[str, Any]:
        """
        Returns a list of all vendors in the database for which there are MIBs.
        
        Args:
            format: Response format ('json' or 'xml')
            
        Returns:
            List of vendors
        """
        return self._make_request('getVendors', format=format)
    
    def get_vendor_info(self, vendor: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns information about a specific vendor.
        
        Args:
            vendor: Vendor name (e.g., 'Fortinet', 'Cisco')
            format: Response format ('json' or 'xml')
            
        Returns:
            Vendor information
        """
        return self._make_request('getVendorInfo', params={'vendor': vendor}, format=format)
    
    def get_vendor_mibs(self, vendor: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns all available MIBs for a particular vendor.
        
        Args:
            vendor: Vendor name
            format: Response format ('json' or 'xml')
            
        Returns:
            List of MIBs for the vendor
        """
        return self._make_request('getVendorMibs', params={'vendor': vendor}, format=format)
    
    def get_mib_info(self, mib: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns detailed information about a particular MIB.
        
        Args:
            mib: MIB name
            format: Response format ('json' or 'xml')
            
        Returns:
            MIB information
        """
        return self._make_request('getMibInfo', params={'mib': mib}, format=format)
    
    def get_mib_object_info(self, oid: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns information about a MIB Object using the OID.
        
        Args:
            oid: Object Identifier (e.g., '1.3.6.1.2.1.1.1.0')
            format: Response format ('json' or 'xml')
            
        Returns:
            MIB object information including name, description, type, etc.
        """
        return self._make_request('getMibObjectInfo', params={'oid': oid}, format=format)
    
    def get_mib_object_info_by_name(
        self, 
        name: str, 
        vendor: Optional[str] = None,
        mib: Optional[str] = None,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Returns information about a MIB Object using the object name.
        
        Args:
            name: Object name (e.g., 'sysDescr')
            vendor: Vendor name (optional, helps narrow search)
            mib: MIB name (optional, helps narrow search)
            format: Response format ('json' or 'xml')
            
        Returns:
            MIB object information
        """
        params = {'name': name}
        if vendor:
            params['vendor'] = vendor
        if mib:
            params['mib'] = mib
        
        return self._make_request('getMibObjectInfoByName', params=params, format=format)
    
    def get_mib_object_parent(self, oid: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns information about the parent MIB Object.
        
        Args:
            oid: Object Identifier
            format: Response format ('json' or 'xml')
            
        Returns:
            Parent MIB object information
        """
        return self._make_request('getMibObjectParent', params={'oid': oid}, format=format)
    
    def get_mib_object_path(self, oid: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns the entire path of the MIB Object.
        
        Args:
            oid: Object Identifier
            format: Response format ('json' or 'xml')
            
        Returns:
            Complete OID path
        """
        return self._make_request('getMibObjectPath', params={'oid': oid}, format=format)
    
    def get_mib_object_children(self, oid: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns the children of a certain MIB object.
        
        Args:
            oid: Object Identifier
            format: Response format ('json' or 'xml')
            
        Returns:
            List of child MIB objects
        """
        return self._make_request('getMibObjectChildren', params={'oid': oid}, format=format)
    
    def get_mib_object_siblings(self, oid: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns the siblings of a certain MIB object.
        
        Args:
            oid: Object Identifier
            format: Response format ('json' or 'xml')
            
        Returns:
            List of sibling MIB objects
        """
        return self._make_request('getMibObjectSiblings', params={'oid': oid}, format=format)
    
    def get_mib_object_child_count(self, oid: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns the number of children for a MIB Object.
        
        Args:
            oid: Object Identifier
            format: Response format ('json' or 'xml')
            
        Returns:
            Child count
        """
        return self._make_request('getMibObjectChildCount', params={'oid': oid}, format=format)
    
    def get_mib_object_sibling_count(self, oid: str, format: str = 'json') -> Dict[str, Any]:
        """
        Returns the number of siblings for a MIB Object.
        
        Args:
            oid: Object Identifier
            format: Response format ('json' or 'xml')
            
        Returns:
            Sibling count
        """
        return self._make_request('getMibObjectSiblingCount', params={'oid': oid}, format=format)
    
    def search_mib_objects_by_vendor(
        self, 
        vendor: str, 
        token: str,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Returns MIB objects in vendor MIBs matching a particular token.
        
        Args:
            vendor: Vendor name
            token: Search token/keyword
            format: Response format ('json' or 'xml')
            
        Returns:
            List of matching MIB objects
        """
        return self._make_request(
            'getMibSearchResultsByVendor',
            params={'vendor': vendor, 'token': token},
            format=format
        )
    
    def decode_oid_to_name(self, oid: str) -> Optional[str]:
        """
        Convenience method to decode an OID to its MIB object name.
        
        Args:
            oid: Object Identifier
            
        Returns:
            MIB object name if found, None otherwise
        """
        try:
            result = self.get_mib_object_info(oid)
            # Response structure may vary, adjust based on actual API response
            if isinstance(result, dict):
                return result.get('name') or result.get('objectName')
            return None
        except Exception:
            return None
    
    def get_oid_description(self, oid: str) -> Optional[str]:
        """
        Get the description for an OID.
        
        Args:
            oid: Object Identifier
            
        Returns:
            Description string if found, None otherwise
        """
        try:
            result = self.get_mib_object_info(oid)
            if isinstance(result, dict):
                return result.get('description') or result.get('desc')
            return None
        except Exception:
            return None
