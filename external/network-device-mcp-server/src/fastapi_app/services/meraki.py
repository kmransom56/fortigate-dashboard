"""
Meraki service for interacting with Meraki Dashboard API
"""
import logging
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin

from ...core.config import settings
from ...models.meraki import (
    MerakiOrganization,
    MerakiNetwork,
    MerakiDevice,
    MerakiVLAN,
    MerakiSSID,
    MerakiClient,
    MerakiTraffic,
    MerakiAlert,
    MerakiWebhook
)

logger = logging.getLogger(__name__)

class MerakiError(Exception):
    """Custom exception for Meraki API errors"""
    pass

class MerakiService:
    """Service for interacting with Meraki Dashboard API"""
    
    BASE_URL = "https://api.meraki.com/api/v1/"
    
    def __init__(self, api_key: str = None, timeout: int = 30):
        """Initialize Meraki service with API key"""
        self.api_key = api_key or settings.MERAKI_API_KEY
        self.timeout = timeout
        self.session = None
        self.last_request = None
        self.rate_limit_remaining = 5  # Default rate limit
        self.rate_limit_reset = 60     # Default reset time in seconds
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Initialize HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                base_url=self.BASE_URL,
                headers={
                    'X-Cisco-Meraki-API-Key': self.api_key,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the Meraki API"""
        if self.session is None or self.session.closed:
            await self.connect()
        
        url = urljoin(self.BASE_URL, endpoint.lstrip('/'))
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                **kwargs
            ) as response:
                # Update rate limit info from headers
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 5))
                self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 60))
                self.last_request = datetime.utcnow()
                
                if response.status == 429:  # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit exceeded. Retry after {retry_after} seconds.")
                    raise MerakiError(f"Rate limit exceeded. Please try again in {retry_after} seconds.")
                
                response.raise_for_status()
                
                # Handle empty responses
                if response.status == 204:  # No Content
                    return {}
                    
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error calling Meraki API: {str(e)}")
            raise MerakiError(f"HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Error calling Meraki API: {str(e)}")
            raise MerakiError(f"API error: {str(e)}")
    
    # Organization Methods
    async def get_organizations(self) -> List[MerakiOrganization]:
        """Get list of organizations the API key has access to"""
        data = await self._request('GET', 'organizations')
        return [MerakiOrganization(**org) for org in data]
    
    async def get_organization(self, org_id: str) -> MerakiOrganization:
        """Get a specific organization by ID"""
        data = await self._request('GET', f'organizations/{org_id}')
        return MerakiOrganization(**data)
    
    # Network Methods
    async def get_networks(self, org_id: str) -> List[MerakiNetwork]:
        """Get list of networks in an organization"""
        data = await self._request('GET', f'organizations/{org_id}/networks')
        return [MerakiNetwork(**net) for net in data]
    
    async def get_network(self, network_id: str) -> MerakiNetwork:
        """Get a specific network by ID"""
        data = await self._request('GET', f'networks/{network_id}')
        return MerakiNetwork(**data)
    
    # Device Methods
    async def get_devices(self, network_id: str) -> List[MerakiDevice]:
        """Get list of devices in a network"""
        data = await self._request('GET', f'networks/{network_id}/devices')
        return [MerakiDevice(**device) for device in data]
    
    async def get_device(self, serial: str) -> MerakiDevice:
        """Get a specific device by serial number"""
        data = await self._request('GET', f'devices/{serial}')
        return MerakiDevice(**data)
    
    # VLAN Methods
    async def get_vlans(self, network_id: str) -> List[MerakiVLAN]:
        """Get list of VLANs in a network"""
        data = await self._request('GET', f'networks/{network_id}/appliance/vlans')
        return [MerakiVLAN(**vlan) for vlan in data]
    
    async def get_vlan(self, network_id: str, vlan_id: int) -> MerakiVLAN:
        """Get a specific VLAN by ID in a network"""
        data = await self._request('GET', f'networks/{network_id}/appliance/vlans/{vlan_id}')
        return MerakiVLAN(**data)
    
    # Wireless Methods
    async def get_ssids(self, network_id: str) -> List[MerakiSSID]:
        """Get list of SSIDs in a network"""
        data = await self._request('GET', f'networks/{network_id}/wireless/ssids')
        return [MerakiSSID(**ssid) for ssid in data]
    
    async def get_ssid(self, network_id: str, number: str) -> MerakiSSID:
        """Get a specific SSID by number in a network"""
        data = await self._request('GET', f'networks/{network_id}/wireless/ssids/{number}')
        return MerakiSSID(**data)
    
    # Client Methods
    async def get_clients(self, network_id: str, **filters) -> List[MerakiClient]:
        """Get list of clients in a network"""
        params = {}
        if 'timespan' in filters:
            params['timespan'] = filters['timespan']
        if 'per_page' in filters:
            params['perPage'] = filters['per_page']
        if 'starting_after' in filters:
            params['startingAfter'] = filters['starting_after']
            
        data = await self._request('GET', f'networks/{network_id}/clients', params=params)
        return [MerakiClient(**client) for client in data]
    
    async def get_client(self, network_id: str, client_id: str) -> MerakiClient:
        """Get a specific client by ID in a network"""
        data = await self._request('GET', f'networks/{network_id}/clients/{client_id}')
        return MerakiClient(**data)
    
    # Traffic Analysis
    async def get_network_traffic(self, network_id: str, **filters) -> List[MerakiTraffic]:
        """Get traffic analysis data for a network"""
        params = {}
        if 'timespan' in filters:
            params['timespan'] = filters['timespan']
        if 'device_type' in filters:
            params['deviceType'] = filters['device_type']
            
        data = await self._request('GET', f'networks/{network_id}/traffic', params=params)
        return [MerakiTraffic(**traffic) for traffic in data]
    
    # Alerts
    async def get_network_alerts(self, network_id: str) -> List[MerakiAlert]:
        """Get alerts for a network"""
        data = await self._request('GET', f'networks/{network_id}/alerts')
        return [MerakiAlert(**alert) for alert in data]
    
    # Webhooks
    async def get_webhooks(self, network_id: str) -> List[MerakiWebhook]:
        """Get webhooks for a network"""
        data = await self._request('GET', f'networks/{network_id}/webhooks/webhookTests')
        return [MerakiWebhook(**webhook) for webhook in data]

# Factory function to get a Meraki service instance
async def get_meraki_service(api_key: str = None):
    """Factory function to get a Meraki service instance"""
    from ...core.config import settings
    
    api_key = api_key or settings.MERAKI_API_KEY
    if not api_key:
        raise ValueError("Meraki API key is required")
    
    service = MerakiService(api_key=api_key)
    await service.connect()
    return service
