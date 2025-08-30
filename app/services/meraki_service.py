"""
Meraki Switch Integration Service

Handles Meraki switch discovery and management for BWW and Arby's locations
that use FortiGate + Meraki + FortiAP infrastructure.
"""

import logging
import requests
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class MerakiService:
    """Service for integrating with Meraki Dashboard API"""
    
    def __init__(self):
        self.api_key = os.getenv("MERAKI_API_KEY")
        self.base_url = "https://api.meraki.com/api/v1"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                "X-Cisco-Meraki-API-Key": self.api_key,
                "Content-Type": "application/json"
            })
        
        # Rate limiting: Meraki allows 5 requests per second
        self.request_delay = 0.2  # 200ms between requests
        self.last_request_time = 0
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make rate-limited request to Meraki API"""
        import time
        
        # Implement rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded - wait and retry once
                logger.warning("Meraki API rate limit exceeded, waiting...")
                time.sleep(1)
                return self._make_request(endpoint, method, data)
            else:
                logger.error(f"Meraki API error: {response.status_code} - {response.text}")
                return {"error": f"API returned {response.status_code}", "details": response.text}
                
        except Exception as e:
            logger.error(f"Meraki API request failed: {e}")
            return {"error": f"Request failed: {str(e)}"}
    
    def get_organizations(self) -> List[Dict[str, Any]]:
        """Get all Meraki organizations"""
        if not self.api_key:
            return {"error": "Meraki API key not configured"}
        
        result = self._make_request("organizations")
        if isinstance(result, dict) and "error" in result:
            return result
        
        # Filter for restaurant organizations if possible
        restaurant_orgs = []
        for org in result:
            org_name = org.get("name", "").lower()
            if any(brand in org_name for brand in ["bww", "buffalo wild wings", "arby", "arbys"]):
                restaurant_orgs.append(org)
        
        return restaurant_orgs or result  # Return all if no restaurant-specific found
    
    def get_organization_networks(self, org_id: str) -> List[Dict[str, Any]]:
        """Get networks for a Meraki organization"""
        result = self._make_request(f"organizations/{org_id}/networks")
        if isinstance(result, dict) and "error" in result:
            return result
        
        return result
    
    def get_network_devices(self, network_id: str) -> List[Dict[str, Any]]:
        """Get devices in a Meraki network"""
        result = self._make_request(f"networks/{network_id}/devices")
        if isinstance(result, dict) and "error" in result:
            return result
        
        # Filter for switches only
        switches = [device for device in result if device.get("model", "").startswith("MS")]
        return switches
    
    def get_switch_ports(self, serial: str) -> List[Dict[str, Any]]:
        """Get port configuration for a Meraki switch"""
        result = self._make_request(f"devices/{serial}/switch/ports")
        if isinstance(result, dict) and "error" in result:
            return result
        
        return result
    
    def get_switch_port_statuses(self, serial: str) -> List[Dict[str, Any]]:
        """Get port status for a Meraki switch"""
        result = self._make_request(f"devices/{serial}/switch/ports/statuses")
        if isinstance(result, dict) and "error" in result:
            return result
        
        return result
    
    def get_network_clients(self, network_id: str, timespan: int = 300) -> List[Dict[str, Any]]:
        """Get clients connected to a network (last 5 minutes by default)"""
        result = self._make_request(f"networks/{network_id}/clients?timespan={timespan}")
        if isinstance(result, dict) and "error" in result:
            return result
        
        return result
    
    def discover_restaurant_meraki_switches(self, organization_filter: str = None) -> Dict[str, Any]:
        """
        Discover Meraki switches across restaurant organizations
        
        Args:
            organization_filter: Filter for specific organization (bww, arbys)
        """
        if not self.api_key:
            return {
                "error": "Meraki API key not configured",
                "switches": [],
                "source": "error"
            }
        
        logger.info(f"Starting Meraki switch discovery with filter: {organization_filter}")
        
        discovery_results = {
            "switches": [],
            "networks": [],
            "organizations": [],
            "source": "meraki_api",
            "discovery_time": datetime.now().isoformat(),
            "api_info": {
                "rate_limited": False,
                "requests_made": 0,
                "errors": []
            }
        }
        
        try:
            # Get organizations
            orgs = self.get_organizations()
            if isinstance(orgs, dict) and "error" in orgs:
                discovery_results["api_info"]["errors"].append(f"Organizations: {orgs['error']}")
                return discovery_results
            
            discovery_results["organizations"] = orgs
            discovery_results["api_info"]["requests_made"] += 1
            
            # Filter organizations based on restaurant brand
            filtered_orgs = orgs
            if organization_filter:
                filtered_orgs = []
                for org in orgs:
                    org_name = org.get("name", "").lower()
                    if organization_filter.lower() in org_name:
                        filtered_orgs.append(org)
            
            logger.info(f"Found {len(filtered_orgs)} organizations to scan")
            
            # For each organization, get networks and devices
            for org in filtered_orgs:
                org_id = org.get("id")
                org_name = org.get("name", "Unknown")
                
                # Get networks for this organization
                networks = self.get_organization_networks(org_id)
                if isinstance(networks, dict) and "error" in networks:
                    discovery_results["api_info"]["errors"].append(f"Networks for {org_name}: {networks['error']}")
                    continue
                
                discovery_results["api_info"]["requests_made"] += 1
                discovery_results["networks"].extend(networks)
                
                # For each network, get switches
                for network in networks:
                    network_id = network.get("id")
                    network_name = network.get("name", "Unknown")
                    
                    # Get devices (switches) in this network
                    devices = self.get_network_devices(network_id)
                    if isinstance(devices, dict) and "error" in devices:
                        discovery_results["api_info"]["errors"].append(f"Devices for {network_name}: {devices['error']}")
                        continue
                    
                    discovery_results["api_info"]["requests_made"] += 1
                    
                    # Process each switch
                    for device in devices:
                        switch_serial = device.get("serial")
                        switch_model = device.get("model", "Unknown")
                        
                        # Get port information
                        ports = self.get_switch_ports(switch_serial)
                        port_statuses = self.get_switch_port_statuses(switch_serial)
                        
                        if not isinstance(ports, dict) or "error" not in ports:
                            discovery_results["api_info"]["requests_made"] += 2
                        
                        # Get connected clients
                        clients = self.get_network_clients(network_id)
                        if not isinstance(clients, dict) or "error" not in clients:
                            discovery_results["api_info"]["requests_made"] += 1
                        
                        # Build switch information
                        switch_info = {
                            "serial": switch_serial,
                            "model": switch_model,
                            "name": device.get("name", f"Meraki-{switch_serial}"),
                            "network_id": network_id,
                            "network_name": network_name,
                            "organization_id": org_id,
                            "organization_name": org_name,
                            "mac": device.get("mac"),
                            "lan_ip": device.get("lanIp"),
                            "wan1_ip": device.get("wan1Ip"),
                            "wan2_ip": device.get("wan2Ip"),
                            "firmware": device.get("firmware"),
                            "status": "online" if device.get("status") == "online" else "offline",
                            "last_reported_at": device.get("lastReportedAt"),
                            "ports": ports if not isinstance(ports, dict) or "error" not in ports else [],
                            "port_statuses": port_statuses if not isinstance(port_statuses, dict) or "error" not in port_statuses else [],
                            "connected_clients": len(clients) if not isinstance(clients, dict) or "error" not in clients else 0,
                            "device_type": "meraki_switch",
                            "management_ip": device.get("lanIp", device.get("wan1Ip", "Unknown"))
                        }
                        
                        discovery_results["switches"].append(switch_info)
            
            logger.info(f"Meraki discovery complete: found {len(discovery_results['switches'])} switches across {len(filtered_orgs)} organizations")
            
        except Exception as e:
            logger.error(f"Meraki discovery failed: {e}")
            discovery_results["api_info"]["errors"].append(f"Discovery exception: {str(e)}")
        
        return discovery_results
    
    def get_switch_topology_data(self, organization_filter: str = None) -> Dict[str, Any]:
        """
        Get topology data for Meraki switches in a format compatible with the main topology service
        """
        discovery_data = self.discover_restaurant_meraki_switches(organization_filter)
        
        if "error" in discovery_data:
            return discovery_data
        
        # Transform to compatible format
        topology_data = {
            "switches": [],
            "source": "meraki_api",
            "enhancement_info": {
                "organizations_scanned": len(discovery_data.get("organizations", [])),
                "networks_found": len(discovery_data.get("networks", [])),
                "api_requests": discovery_data.get("api_info", {}).get("requests_made", 0),
                "errors": discovery_data.get("api_info", {}).get("errors", [])
            }
        }
        
        for switch in discovery_data.get("switches", []):
            # Convert Meraki switch to compatible format
            compatible_switch = {
                "serial": switch.get("serial"),
                "model": switch.get("model"),
                "status": "Authorized" if switch.get("status") == "online" else "Offline",
                "mgmt_ip": switch.get("management_ip"),
                "firmware": switch.get("firmware"),
                "ports": [
                    {
                        "port_id": port.get("portId", "Unknown"),
                        "name": port.get("name", f"Port {port.get('portId')}"),
                        "enabled": port.get("enabled", False),
                        "type": port.get("type", "access"),
                        "vlan": port.get("vlan", 1),
                        "status": "up" if port.get("enabled", False) else "down"
                    }
                    for port in switch.get("ports", [])
                ],
                "organization": switch.get("organization_name"),
                "network": switch.get("network_name"),
                "switch_type": "meraki",
                "last_seen": switch.get("last_reported_at")
            }
            
            topology_data["switches"].append(compatible_switch)
        
        return topology_data
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of Meraki API connection"""
        if not self.api_key:
            return {
                "status": "error",
                "message": "Meraki API key not configured",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Try a simple API call
            orgs = self._make_request("organizations")
            
            if isinstance(orgs, dict) and "error" in orgs:
                return {
                    "status": "error",
                    "message": f"API call failed: {orgs['error']}",
                    "timestamp": datetime.now().isoformat()
                }
            
            return {
                "status": "healthy",
                "message": f"Connected successfully, found {len(orgs)} organizations",
                "organizations_count": len(orgs),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


# Global service instance
_meraki_service = None

def get_meraki_service() -> MerakiService:
    """Get the global Meraki service instance"""
    global _meraki_service
    if _meraki_service is None:
        _meraki_service = MerakiService()
    return _meraki_service