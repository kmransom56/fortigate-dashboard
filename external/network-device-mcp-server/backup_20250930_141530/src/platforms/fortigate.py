"""
FortiGate API Manager
Handles direct communication with FortiGate devices via REST API
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any

import httpx

logger = logging.getLogger(__name__)

class FortiGateManager:
    def __init__(self):
        self.timeout = 30.0
    
    async def _make_request(self, host: str, token: str, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Make API request to FortiGate device"""
        url = f"https://{host}/api/v2/{endpoint.lstrip('/')}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
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
            return response.json()
    
    async def get_system_status(self, host: str, token: str) -> dict:
        """Get FortiGate system status and information"""
        try:
            result = await self._make_request(host, token, "/monitor/system/status")
            
            # Format the response for better readability
            if "results" in result:
                status_data = result["results"]
                return {
                    "hostname": status_data.get("hostname", "unknown"),
                    "version": status_data.get("version", "unknown"), 
                    "serial": status_data.get("serial", "unknown"),
                    "uptime": status_data.get("uptime", 0),
                    "cpu_usage": status_data.get("cpu", 0),
                    "memory_usage": status_data.get("memory", 0),
                    "session_count": status_data.get("session_count", 0),
                    "status": "online"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting system status from {host}: {e}")
            raise
    
    async def get_interfaces(self, host: str, token: str) -> list:
        """Get FortiGate network interfaces"""
        try:
            result = await self._make_request(host, token, "/monitor/system/interface")
            
            interfaces = []
            if "results" in result:
                for interface in result["results"]:
                    interfaces.append({
                        "name": interface.get("name"),
                        "ip": interface.get("ip"),
                        "status": interface.get("status"),
                        "speed": interface.get("speed"), 
                        "duplex": interface.get("duplex"),
                        "tx_bytes": interface.get("tx_bytes"),
                        "rx_bytes": interface.get("rx_bytes"),
                        "tx_packets": interface.get("tx_packets"),
                        "rx_packets": interface.get("rx_packets")
                    })
            
            return interfaces
            
        except Exception as e:
            logger.error(f"Error getting interfaces from {host}: {e}")
            raise
    
    async def get_firewall_policies(self, host: str, token: str) -> list:
        """Get FortiGate firewall policies"""
        try:
            result = await self._make_request(host, token, "/cmdb/firewall/policy")
            
            policies = []
            if "results" in result:
                for policy in result["results"]:
                    policies.append({
                        "policyid": policy.get("policyid"),
                        "name": policy.get("name", ""),
                        "status": policy.get("status"),
                        "action": policy.get("action"),
                        "srcintf": [intf.get("name") for intf in policy.get("srcintf", [])],
                        "dstintf": [intf.get("name") for intf in policy.get("dstintf", [])], 
                        "srcaddr": [addr.get("name") for addr in policy.get("srcaddr", [])],
                        "dstaddr": [addr.get("name") for addr in policy.get("dstaddr", [])],
                        "service": [svc.get("name") for svc in policy.get("service", [])],
                        "logtraffic": policy.get("logtraffic"),
                        "nat": policy.get("nat")
                    })
            
            return policies
            
        except Exception as e:
            logger.error(f"Error getting firewall policies from {host}: {e}")
            raise
    
    async def get_route_table(self, host: str, token: str) -> list:
        """Get FortiGate routing table"""
        try:
            result = await self._make_request(host, token, "/monitor/router/ipv4")
            
            routes = []
            if "results" in result:
                for route in result["results"]:
                    routes.append({
                        "destination": route.get("ip_mask", ""),
                        "gateway": route.get("gateway", ""),
                        "interface": route.get("interface", ""),
                        "distance": route.get("distance", 0),
                        "metric": route.get("metric", 0),
                        "type": route.get("type", "")
                    })
            
            return routes
            
        except Exception as e:
            logger.error(f"Error getting route table from {host}: {e}")
            raise
    
    async def get_vpn_status(self, host: str, token: str) -> list:
        """Get VPN tunnel status"""
        try:
            result = await self._make_request(host, token, "/monitor/vpn/ipsec")
            
            vpn_tunnels = []
            if "results" in result:
                for tunnel in result["results"]:
                    vpn_tunnels.append({
                        "name": tunnel.get("name", ""),
                        "status": tunnel.get("status", ""),
                        "remote_gw": tunnel.get("remote_gw", ""),
                        "local_gw": tunnel.get("local_gw", ""),
                        "bytes_tx": tunnel.get("bytes_tx", 0),
                        "bytes_rx": tunnel.get("bytes_rx", 0)
                    })
            
            return vpn_tunnels
            
        except Exception as e:
            logger.error(f"Error getting VPN status from {host}: {e}")
            raise
    
    async def get_security_events(self, host: str, token: str, count: int = 100) -> list:
        """Get recent security events/logs"""
        try:
            endpoint = f"/monitor/log/webfilter?count={count}"
            result = await self._make_request(host, token, endpoint)
            
            events = []
            if "results" in result:
                for event in result["results"]:
                    events.append({
                        "time": event.get("time", ""),
                        "logid": event.get("logid", ""),
                        "type": event.get("type", ""),
                        "subtype": event.get("subtype", ""),
                        "level": event.get("level", ""),
                        "srcip": event.get("srcip", ""),
                        "dstip": event.get("dstip", ""),
                        "action": event.get("action", ""),
                        "msg": event.get("msg", "")
                    })
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting security events from {host}: {e}")
            raise
    
    async def backup_config(self, host: str, token: str) -> dict:
        """Backup FortiGate configuration"""
        try:
            # This would typically return the config file or backup information
            result = await self._make_request(host, token, "/monitor/system/config/backup")
            return result
            
        except Exception as e:
            logger.error(f"Error backing up config from {host}: {e}")
            raise
    
    async def create_firewall_policy(self, host: str, token: str, policy_data: dict) -> dict:
        """Create a new firewall policy"""
        try:
            result = await self._make_request(
                host, token, "/cmdb/firewall/policy", 
                method="POST", data=policy_data
            )
            return result
            
        except Exception as e:
            logger.error(f"Error creating firewall policy on {host}: {e}")
            raise