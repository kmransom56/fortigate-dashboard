"""
Cisco Meraki API Manager
Handles communication with Meraki Dashboard API
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any

import httpx

logger = logging.getLogger(__name__)

class MerakiManager:
    def __init__(self):
        self.base_url = "https://api.meraki.com/api/v1"
        self.timeout = 30.0
    
    def _get_headers(self, api_key: str) -> dict:
        """Get headers for Meraki API requests"""
        return {
            "X-Cisco-Meraki-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _make_request(self, endpoint: str, api_key: str, method: str = "GET", data: dict = None) -> dict:
        """Make request to Meraki Dashboard API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers(api_key)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204:
                return {"status": "success", "message": "No content"}
            
            return response.json()
    
    async def get_organizations(self, api_key: str) -> list:
        """Get Meraki organizations"""
        try:
            result = await self._make_request("organizations", api_key)
            
            orgs = []
            for org in result:
                orgs.append({
                    "id": org.get("id", ""),
                    "name": org.get("name", ""),
                    "url": org.get("url", ""),
                    "api_enabled": org.get("api", {}).get("enabled", False)
                })
            
            return orgs
            
        except Exception as e:
            logger.error(f"Error getting Meraki organizations: {e}")
            raise
    
    async def get_networks(self, api_key: str, org_id: str) -> list:
        """Get networks in a Meraki organization"""
        try:
            endpoint = f"organizations/{org_id}/networks"
            result = await self._make_request(endpoint, api_key)
            
            networks = []
            for network in result:
                networks.append({
                    "id": network.get("id", ""),
                    "name": network.get("name", ""),
                    "product_types": network.get("productTypes", []),
                    "time_zone": network.get("timeZone", ""),
                    "tags": network.get("tags", []),
                    "enrollment_string": network.get("enrollmentString", "")
                })
            
            return networks
            
        except Exception as e:
            logger.error(f"Error getting Meraki networks for org {org_id}: {e}")
            raise
    
    async def get_devices(self, api_key: str, network_id: str) -> list:
        """Get devices in a Meraki network"""
        try:
            endpoint = f"networks/{network_id}/devices"
            result = await self._make_request(endpoint, api_key)
            
            devices = []
            for device in result:
                devices.append({
                    "serial": device.get("serial", ""),
                    "mac": device.get("mac", ""),
                    "name": device.get("name", ""),
                    "model": device.get("model", ""),
                    "product_type": device.get("productType", ""),
                    "network_id": device.get("networkId", ""),
                    "address": device.get("address", ""),
                    "lat": device.get("lat"),
                    "lng": device.get("lng"),
                    "notes": device.get("notes", ""),
                    "tags": device.get("tags", []),
                    "lan_ip": device.get("lanIp", ""),
                    "firmware": device.get("firmware", "")
                })
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting Meraki devices for network {network_id}: {e}")
            raise
    
    async def get_device_status(self, api_key: str, org_id: str) -> list:
        """Get device status for all devices in organization"""
        try:
            endpoint = f"organizations/{org_id}/devices/statuses"
            result = await self._make_request(endpoint, api_key)
            
            statuses = []
            for status in result:
                statuses.append({
                    "name": status.get("name", ""),
                    "serial": status.get("serial", ""),
                    "mac": status.get("mac", ""),
                    "status": status.get("status", ""),
                    "last_reported_at": status.get("lastReportedAt", ""),
                    "network_id": status.get("networkId", ""),
                    "product_type": status.get("productType", ""),
                    "model": status.get("model", ""),
                    "public_ip": status.get("publicIp", ""),
                    "gateway": status.get("gateway", ""),
                    "ip_type": status.get("ipType", "")
                })
            
            return statuses
            
        except Exception as e:
            logger.error(f"Error getting device statuses for org {org_id}: {e}")
            raise
    
    async def update_device(self, api_key: str, network_id: str, serial: str, config: dict) -> dict:
        """Update Meraki device configuration"""
        try:
            endpoint = f"networks/{network_id}/devices/{serial}"
            result = await self._make_request(endpoint, api_key, "PUT", config)
            
            return {
                "status": "success",
                "serial": serial,
                "updated_fields": list(config.keys()),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error updating device {serial}: {e}")
            raise
    
    async def get_network_clients(self, api_key: str, network_id: str, timespan: int = 86400) -> list:
        """Get clients connected to a network"""
        try:
            endpoint = f"networks/{network_id}/clients?timespan={timespan}"
            result = await self._make_request(endpoint, api_key)
            
            clients = []
            for client in result:
                clients.append({
                    "id": client.get("id", ""),
                    "mac": client.get("mac", ""),
                    "ip": client.get("ip", ""),
                    "ip6": client.get("ip6", ""),
                    "description": client.get("description", ""),
                    "first_seen": client.get("firstSeen", ""),
                    "last_seen": client.get("lastSeen", ""),
                    "manufacturer": client.get("manufacturer", ""),
                    "os": client.get("os", ""),
                    "user": client.get("user", ""),
                    "vlan": client.get("vlan", ""),
                    "switch_port": client.get("switchport", ""),
                    "wireless": client.get("wireless", {}),
                    "usage": client.get("usage", {})
                })
            
            return clients
            
        except Exception as e:
            logger.error(f"Error getting network clients for {network_id}: {e}")
            raise
    
    async def get_switch_ports(self, api_key: str, serial: str) -> list:
        """Get switch port configuration"""
        try:
            endpoint = f"devices/{serial}/switch/ports"
            result = await self._make_request(endpoint, api_key)
            
            ports = []
            for port in result:
                ports.append({
                    "port_id": port.get("portId", ""),
                    "name": port.get("name", ""),
                    "enabled": port.get("enabled", False),
                    "poe_enabled": port.get("poeEnabled", False),
                    "type": port.get("type", ""),
                    "vlan": port.get("vlan", ""),
                    "voice_vlan": port.get("voiceVlan", ""),
                    "allowed_vlans": port.get("allowedVlans", ""),
                    "isolation_enabled": port.get("isolationEnabled", False),
                    "rstp_enabled": port.get("rstpEnabled", False),
                    "stp_guard": port.get("stpGuard", ""),
                    "link_negotiation": port.get("linkNegotiation", ""),
                    "port_schedule_id": port.get("portScheduleId", ""),
                    "tags": port.get("tags", [])
                })
            
            return ports
            
        except Exception as e:
            logger.error(f"Error getting switch ports for {serial}: {e}")
            raise
    
    async def get_wireless_ssids(self, api_key: str, network_id: str) -> list:
        """Get wireless SSIDs configuration"""
        try:
            endpoint = f"networks/{network_id}/wireless/ssids"
            result = await self._make_request(endpoint, api_key)
            
            ssids = []
            for ssid in result:
                ssids.append({
                    "number": ssid.get("number", ""),
                    "name": ssid.get("name", ""),
                    "enabled": ssid.get("enabled", False),
                    "splash_page": ssid.get("splashPage", ""),
                    "ssid_admin_accessible": ssid.get("ssidAdminAccessible", False),
                    "auth_mode": ssid.get("authMode", ""),
                    "encryption_mode": ssid.get("encryptionMode", ""),
                    "wpa_encryption_mode": ssid.get("wpaEncryptionMode", ""),
                    "radius_servers": ssid.get("radiusServers", []),
                    "radius_accounting_enabled": ssid.get("radiusAccountingEnabled", False),
                    "radius_accounting_servers": ssid.get("radiusAccountingServers", []),
                    "ip_assignment_mode": ssid.get("ipAssignmentMode", ""),
                    "use_vlan_tagging": ssid.get("useVlanTagging", False),
                    "vlan_id": ssid.get("vlanId", ""),
                    "default_vlan_id": ssid.get("defaultVlanId", ""),
                    "band_selection": ssid.get("bandSelection", ""),
                    "per_client_bandwidth_limit_up": ssid.get("perClientBandwidthLimitUp", 0),
                    "per_client_bandwidth_limit_down": ssid.get("perClientBandwidthLimitDown", 0)
                })
            
            return ssids
            
        except Exception as e:
            logger.error(f"Error getting wireless SSIDs for network {network_id}: {e}")
            raise
    
    async def get_security_events(self, api_key: str, org_id: str, timespan: int = 86400) -> list:
        """Get security events from organization"""
        try:
            endpoint = f"organizations/{org_id}/securityEvents?timespan={timespan}"
            result = await self._make_request(endpoint, api_key)
            
            events = []
            for event in result:
                events.append({
                    "ts": event.get("ts", ""),
                    "event_type": event.get("eventType", ""),
                    "client_name": event.get("clientName", ""),
                    "client_mac": event.get("clientMac", ""),
                    "device_mac": event.get("deviceMac", ""),
                    "blocked": event.get("blocked", False),
                    "ssid": event.get("ssid", ""),
                    "message": event.get("message", ""),
                    "signature": event.get("signature", ""),
                    "priority": event.get("priority", ""),
                    "classification": event.get("classification", ""),
                    "canonical_name": event.get("canonicalName", ""),
                    "target": event.get("target", ""),
                    "file_hash": event.get("fileHash", ""),
                    "file_type": event.get("fileType", ""),
                    "src_ip": event.get("srcIp", ""),
                    "dest_ip": event.get("destIp", ""),
                    "protocol": event.get("protocol", ""),
                    "port": event.get("port", ""),
                    "uri": event.get("uri", "")
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting security events for org {org_id}: {e}")
            raise
    
    async def create_network(self, api_key: str, org_id: str, network_config: dict) -> dict:
        """Create a new Meraki network"""
        try:
            endpoint = f"organizations/{org_id}/networks"
            result = await self._make_request(endpoint, api_key, "POST", network_config)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating network in org {org_id}: {e}")
            raise
    
    async def claim_device(self, api_key: str, network_id: str, serial: str) -> dict:
        """Claim a device into a network"""
        try:
            endpoint = f"networks/{network_id}/devices/claim"
            data = {"serials": [serial]}
            result = await self._make_request(endpoint, api_key, "POST", data)
            
            return {
                "status": "success",
                "serial": serial,
                "network_id": network_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error claiming device {serial}: {e}")
            raise