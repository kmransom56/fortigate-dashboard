"""
FortiGate service for interacting with FortiGate devices
"""
import logging
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin

from ...core.config import settings
from ...models.fortigate import (
    FortiGateInterface,
    FortiGateVLAN,
    FortiGatePolicy,
    FortiGateVPNTunnel,
    FortiGateSystemStatus,
    FortiGateLogEntry,
    FortiGateCommandRequest,
    FortiGateCommandResponse
)

logger = logging.getLogger(__name__)

class FortiGateError(Exception):
    """Custom exception for FortiGate API errors"""
    pass

class FortiGateService:
    """Service for interacting with FortiGate devices"""
    
    def __init__(self, host: str, token: str, verify_ssl: bool = True, port: int = 443):
        """Initialize FortiGate service with connection details"""
        self.base_url = f"https://{host}:{port}"
        self.token = token
        self.verify_ssl = verify_ssl
        self.session = None
        self.last_connection = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Initialize connection to FortiGate"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                base_url=self.base_url,
                headers={
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                connector=aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
            )
            self.last_connection = datetime.utcnow()
    
    async def close(self):
        """Close the connection"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the FortiGate API"""
        if self.session is None or self.session.closed:
            await self.connect()
        
        url = urljoin(f"{self.base_url}/api/v2/", endpoint.lstrip('/'))
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                ssl=None if self.verify_ssl else False,
                **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error calling FortiGate API: {str(e)}")
            raise FortiGateError(f"HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Error calling FortiGate API: {str(e)}")
            raise FortiGateError(f"API error: {str(e)}")
    
    # System Methods
    async def get_system_status(self) -> FortiGateSystemStatus:
        """Get system status information"""
        data = await self._request('GET', 'monitor/system/status')
        return FortiGateSystemStatus(**data['results'])
    
    async def get_system_ha_status(self) -> Dict[str, Any]:
        """Get HA status information"""
        return await self._request('GET', 'monitor/system/ha')
    
    # Interface Methods
    async def get_interfaces(self) -> List[FortiGateInterface]:
        """Get all interfaces"""
        data = await self._request('GET', 'cmdb/system/interface')
        return [FortiGateInterface(**iface) for iface in data['results']]
    
    async def get_interface(self, name: str) -> Optional[FortiGateInterface]:
        """Get a specific interface by name"""
        try:
            data = await self._request('GET', f'cmdb/system/interface/{name}')
            return FortiGateInterface(**data['results']) if data.get('results') else None
        except FortiGateError as e:
            if "Object does not exist" in str(e):
                return None
            raise
    
    # VLAN Methods
    async def get_vlans(self) -> List[FortiGateVLAN]:
        """Get all VLANs"""
        data = await self._request('GET', 'cmdb/system/interface')
        return [FortiGateVLAN(**vlan) for vlan in data['results'] 
                if vlan.get('type', '').lower() == 'vlan']
    
    async def get_vlan(self, vlan_id: int) -> Optional[FortiGateVLAN]:
        """Get a specific VLAN by ID"""
        try:
            data = await self._request('GET', f'cmdb/system/interface/vlan{vlan_id}')
            return FortiGateVLAN(**data['results'][0]) if data.get('results') else None
        except FortiGateError as e:
            if "Object does not exist" in str(e):
                return None
            raise
    
    # Policy Methods
    async def get_policies(self) -> List[FortiGatePolicy]:
        """Get all firewall policies"""
        data = await self._request('GET', 'cmdb/firewall/policy')
        return [FortiGatePolicy(**policy) for policy in data['results']]
    
    async def get_policy(self, policy_id: int) -> Optional[FortiGatePolicy]:
        """Get a specific firewall policy by ID"""
        try:
            data = await self._request('GET', f'cmdb/firewall/policy/{policy_id}')
            return FortiGatePolicy(**data['results'][0]) if data.get('results') else None
        except FortiGateError as e:
            if "Object does not exist" in str(e):
                return None
            raise
    
    # VPN Methods
    async def get_vpn_tunnels(self) -> List[FortiGateVPNTunnel]:
        """Get all VPN tunnels"""
        data = await self._request('GET', 'monitor/vpn/ipsec')
        return [FortiGateVPNTunnel(**tunnel) for tunnel in data.get('tunnels', [])]
    
    # Logging Methods
    async def get_logs(self, log_type: str = 'traffic', count: int = 50) -> List[FortiGateLogEntry]:
        """Get logs from FortiGate"""
        params = {
            'log-type': log_type,
            'count': min(count, 1000)  # Limit to 1000 entries max
        }
        data = await self._request('GET', f'monitor/log/{log_type}/select', params=params)
        return [FortiGateLogEntry(**entry) for entry in data.get('results', [])]
    
    # Command Execution
    async def execute_command(self, command: str, vdom: str = 'root') -> FortiGateCommandResponse:
        """Execute a CLI command on the FortiGate"""
        data = {
            'command': command,
            'vdom': vdom
        }
        result = await self._request('POST', 'monitor/system/execute', json=data)
        return FortiGateCommandResponse(
            command=command,
            response=result.get('response', ''),
            vdom=vdom,
            timestamp=datetime.utcnow().isoformat()
        )

# Factory function to get a FortiGate service instance
async def get_fortigate_service(host: str = None, token: str = None, verify_ssl: bool = True):
    """Factory function to get a FortiGate service instance"""
    host = host or settings.FORTIGATE_HOST
    token = token or settings.FORTIGATE_API_TOKEN
    
    if not host or not token:
        raise ValueError("FortiGate host and API token must be provided")
    
    service = FortiGateService(host=host, token=token, verify_ssl=verify_ssl)
    await service.connect()
    return service
