"""
Scanopy Network Discovery Integration Service

Integrates Scanopy network discovery and mapping application to provide
comprehensive network topology with service detection.
"""

import logging
import os
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ScanopyService:
    """
    Service for integrating with Scanopy network discovery API.
    Provides host discovery, service detection, and topology mapping.
    """

    def __init__(self):
        self.base_url = os.getenv("SCANOPY_URL", "http://localhost:60072")
        self.api_token = os.getenv("SCANOPY_API_TOKEN")
        self.timeout = aiohttp.ClientTimeout(total=30)
        self._session: Optional[aiohttp.ClientSession] = None

        # Remove trailing slash
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if self._session is None or self._session.closed:
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"

            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self._session = aiohttp.ClientSession(
                headers=headers, timeout=self.timeout, connector=connector
            )
        return self._session

    async def _close_session(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _make_request(
        self, endpoint: str, method: str = "GET", data: Dict = None
    ) -> Dict[str, Any]:
        """
        Make async request to Scanopy API

        Args:
            endpoint: API endpoint path (without leading slash)
            method: HTTP method (GET, POST, etc.)
            data: Request body data for POST/PUT

        Returns:
            Response data as dictionary or error dictionary
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{endpoint.lstrip('/')}"

            async with session.request(method, url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logger.warning(f"Scanopy endpoint not found: {endpoint}")
                    return {"error": "Endpoint not found", "status_code": 404}
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Scanopy API error {response.status} for {endpoint}: {error_text}"
                    )
                    return {
                        "error": f"API returned {response.status}",
                        "details": error_text,
                        "status_code": response.status,
                    }

        except aiohttp.ClientConnectionError as e:
            logger.error(f"Scanopy connection error: {e}")
            return {"error": "Connection failed", "details": str(e), "available": False}
        except asyncio.TimeoutError:
            logger.error(f"Scanopy request timeout for {endpoint}")
            return {"error": "Request timeout", "available": False}
        except Exception as e:
            logger.error(f"Scanopy API request failed: {e}")
            return {"error": f"Request failed: {str(e)}", "available": False}

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Scanopy server health

        Returns:
            Health status dictionary
        """
        try:
            result = await self._make_request("/health")
            if "error" in result:
                return {
                    "status": "unavailable",
                    "url": self.base_url,
                    "available": False,
                    "error": result.get("error"),
                }

            return {
                "status": "healthy",
                "url": self.base_url,
                "available": True,
                "status_code": 200,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unavailable",
                "url": self.base_url,
                "available": False,
                "error": str(e),
            }

    async def get_hosts(
        self, organization_id: Optional[str] = None, network_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all discovered hosts from Scanopy

        Args:
            organization_id: Optional organization filter
            network_id: Optional network filter

        Returns:
            Dictionary with hosts list and count
        """
        endpoint = "/api/hosts"
        params = []
        if organization_id:
            params.append(f"organization_id={organization_id}")
        if network_id:
            params.append(f"network_id={network_id}")

        if params:
            endpoint += "?" + "&".join(params)

        result = await self._make_request(endpoint)

        if "error" in result:
            return {"hosts": [], "count": 0, "error": result.get("error")}

        # Transform Scanopy response to our format
        hosts = result.get("hosts", []) if isinstance(result, dict) else result

        transformed_hosts = []
        for host in hosts:
            transformed_host = {
                "id": host.get("id") or host.get("ip_address"),
                "ip_address": host.get("ip_address"),
                "mac_address": host.get("mac_address"),
                "hostname": host.get("hostname") or host.get("name"),
                "vendor": host.get("vendor") or host.get("manufacturer"),
                "services": host.get("services", []),
                "last_seen": host.get("last_seen"),
                "first_seen": host.get("first_seen"),
                "subnet": host.get("subnet"),
                "network_id": host.get("network_id"),
            }
            transformed_hosts.append(transformed_host)

        return {"hosts": transformed_hosts, "count": len(transformed_hosts)}

    async def get_host_by_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Get specific host details by IP address

        Args:
            ip_address: IP address to lookup

        Returns:
            Host details dictionary
        """
        # First get all hosts and filter
        hosts_result = await self.get_hosts()
        if "error" in hosts_result:
            return hosts_result

        for host in hosts_result.get("hosts", []):
            if host.get("ip_address") == ip_address:
                return host

        return {"error": "Host not found", "ip_address": ip_address}

    async def get_services(
        self, organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all detected services from Scanopy

        Args:
            organization_id: Optional organization filter

        Returns:
            Dictionary with services list
        """
        endpoint = "/api/services"
        if organization_id:
            endpoint += f"?organization_id={organization_id}"

        result = await self._make_request(endpoint)

        if "error" in result:
            return {"services": [], "count": 0, "error": result.get("error")}

        services = result.get("services", []) if isinstance(result, dict) else result

        return {"services": services, "count": len(services)}

    async def get_topology(
        self, organization_id: Optional[str] = None, network_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get network topology from Scanopy

        Args:
            organization_id: Optional organization filter
            network_id: Optional network filter

        Returns:
            Topology data dictionary
        """
        endpoint = "/api/topology"
        params = []
        if organization_id:
            params.append(f"organization_id={organization_id}")
        if network_id:
            params.append(f"network_id={network_id}")

        if params:
            endpoint += "?" + "&".join(params)

        result = await self._make_request(endpoint)

        if "error" in result:
            return {"nodes": [], "edges": [], "error": result.get("error")}

        return result

    async def trigger_scan(
        self, subnet: str, scan_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Trigger a network scan in Scanopy

        Args:
            subnet: Subnet to scan (e.g., "192.168.1.0/24")
            scan_type: Type of scan ("full" or "top_ports")

        Returns:
            Scan job information
        """
        endpoint = "/api/discovery/scan"
        data = {"subnet": subnet, "scan_type": scan_type}

        result = await self._make_request(endpoint, method="POST", data=data)

        if "error" in result:
            return {"success": False, "error": result.get("error")}

        return {
            "success": True,
            "subnet": subnet,
            "scan_type": scan_type,
            "result": result,
        }

    async def get_networks(
        self, organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all networks from Scanopy

        Args:
            organization_id: Optional organization filter

        Returns:
            List of network dictionaries
        """
        endpoint = "/api/networks"
        if organization_id:
            endpoint += f"?organization_id={organization_id}"

        result = await self._make_request(endpoint)

        if "error" in result:
            return []

        return result if isinstance(result, list) else result.get("networks", [])

    def is_available(self) -> bool:
        """
        Synchronous check if Scanopy is available
        (Uses async health_check internally)

        Returns:
            True if Scanopy is available, False otherwise
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, we can't use run_until_complete
                # Return False and let async methods handle it
                return False
            else:
                result = loop.run_until_complete(self.health_check())
                return result.get("available", False)
        except Exception:
            return False


# Global instance
_scanopy_service = None


def get_scanopy_service() -> ScanopyService:
    """Get global Scanopy service instance"""
    global _scanopy_service
    if _scanopy_service is None:
        _scanopy_service = ScanopyService()
    return _scanopy_service
