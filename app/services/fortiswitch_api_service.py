"""
FortiSwitch API Service for Sonic Locations

Uses FortiGate API to discover and manage FortiSwitch devices for Sonic restaurants
(Sonic uses FortiGate + FortiSwitch + FortiAP infrastructure).
Based on the working API endpoint: cmdb/switch-controller/managed-switch
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .fortigate_service import fgt_api, load_api_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FortiSwitchPort:
    """Represents a FortiSwitch port"""
    name: str
    status: str
    speed: str
    duplex: str
    vlan: str
    mac_address: str
    poe_status: str
    connected_devices: List[Dict[str, Any]]

@dataclass
class FortiSwitchDevice:
    """Represents a FortiSwitch device"""
    serial: str
    switch_id: str
    name: str
    model: str
    status: str
    total_ports: int
    active_ports: int
    os_version: str
    ports: List[FortiSwitchPort]

class FortiSwitchAPIService:
    """
    Service for discovering and managing FortiSwitch devices via FortiGate API.
    Uses the working endpoint: cmdb/switch-controller/managed-switch
    """
    
    def __init__(self):
        self.api_token = load_api_token()
        if not self.api_token:
            logger.warning("No API token available for FortiSwitch API service")
    
    def get_managed_switches(self) -> Dict[str, Any]:
        """
        Get managed FortiSwitch devices from FortiGate API.
        Returns comprehensive switch information including ports and devices.
        """
        try:
            # Use the working API endpoint
            data = fgt_api("cmdb/switch-controller/managed-switch")
            
            if "error" in data:
                logger.error(f"API error getting managed switches: {data}")
                return {"switches": [], "total_switches": 0, "source": "api", "error": data.get("error")}
            
            # Process the results
            switches = []
            if "results" in data and isinstance(data["results"], list):
                for switch_data in data["results"]:
                    switch = self._process_switch_data(switch_data)
                    if switch:
                        switches.append(switch)
            
            logger.info(f"Retrieved {len(switches)} FortiSwitch devices via API")
            
            return {
                "switches": switches,
                "total_switches": len(switches),
                "source": "api",
                "api_info": {
                    "endpoint": "cmdb/switch-controller/managed-switch",
                    "revision": data.get("revision"),
                    "matched_count": data.get("matched_count", len(switches))
                }
            }
            
        except Exception as e:
            logger.error(f"Exception getting managed switches: {e}")
            return {"switches": [], "total_switches": 0, "source": "api", "error": str(e)}
    
    def _process_switch_data(self, switch_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process raw switch data from API into structured format"""
        try:
            # Extract basic switch information
            serial = switch_data.get("sn", "")
            switch_id = switch_data.get("switch-id", "")
            
            # Process ports
            ports = []
            port_data = switch_data.get("ports", [])
            active_port_count = 0
            
            for port in port_data:
                if isinstance(port, dict):
                    port_status = port.get("status", "down")
                    if port_status == "up":
                        active_port_count += 1
                    
                    # Create port information
                    port_info = {
                        "name": port.get("port-name", ""),
                        "status": port_status,
                        "speed": port.get("speed", "auto"),
                        "duplex": "full" if port.get("status") == "up" else "unknown",
                        "vlan": port.get("vlan", ""),
                        "mac_address": port.get("mac-addr", ""),
                        "poe_status": port.get("poe-status", "unknown"),
                        "poe_power": port.get("poe-max-power", ""),
                        "media_type": port.get("media-type", ""),
                        "description": port.get("description", ""),
                        "connected_devices": []  # Would need additional API calls to populate
                    }
                    ports.append(port_info)
            
            # Create switch summary
            switch_summary = {
                "serial": serial,
                "switch_id": switch_id,
                "name": switch_id,  # Use switch-id as name
                "model": "FortiSwitch",  # Could be extracted from dynamic-capability if needed
                "status": "authorized" if switch_data.get("dynamically-discovered") else "unknown",
                "total_ports": len(ports),
                "active_ports": active_port_count,
                "os_version": switch_data.get("version", ""),
                "connection_type": "FortiLink",
                "management_ip": "10.255.1.2",  # FortiLink management IP
                "ports": ports,
                "raw_data": {
                    "firmware_provision": switch_data.get("firmware-provision"),
                    "ptp_status": switch_data.get("ptp-status"),
                    "tunnel_discovered": switch_data.get("tunnel-discovered"),
                    "directly_connected": switch_data.get("directly-connected")
                }
            }
            
            return switch_summary
            
        except Exception as e:
            logger.error(f"Error processing switch data: {e}")
            return None
    
    def get_switch_by_serial(self, serial: str) -> Optional[Dict[str, Any]]:
        """Get specific switch by serial number"""
        switches_data = self.get_managed_switches()
        
        for switch in switches_data.get("switches", []):
            if switch.get("serial") == serial:
                return switch
        
        return None
    
    def get_port_information(self, switch_serial: str, port_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific port"""
        switch = self.get_switch_by_serial(switch_serial)
        
        if switch:
            for port in switch.get("ports", []):
                if port.get("name") == port_name:
                    return port
        
        return None
    
    def get_active_ports(self, switch_serial: str = None) -> List[Dict[str, Any]]:
        """Get all active ports, optionally filtered by switch serial"""
        active_ports = []
        switches_data = self.get_managed_switches()
        
        for switch in switches_data.get("switches", []):
            if switch_serial and switch.get("serial") != switch_serial:
                continue
                
            for port in switch.get("ports", []):
                if port.get("status") == "up":
                    # Add switch context to port info
                    port_with_context = port.copy()
                    port_with_context["switch_serial"] = switch.get("serial")
                    port_with_context["switch_name"] = switch.get("name")
                    active_ports.append(port_with_context)
        
        return active_ports
    
    def get_network_summary(self) -> Dict[str, Any]:
        """Get network topology summary"""
        switches_data = self.get_managed_switches()
        
        total_ports = 0
        total_active_ports = 0
        
        for switch in switches_data.get("switches", []):
            total_ports += switch.get("total_ports", 0)
            total_active_ports += switch.get("active_ports", 0)
        
        return {
            "switch_count": switches_data.get("total_switches", 0),
            "total_ports": total_ports,
            "active_ports": total_active_ports,
            "utilization": round((total_active_ports / total_ports * 100), 1) if total_ports > 0 else 0,
            "data_source": "api",
            "last_updated": switches_data.get("api_info", {})
        }

# Global instance
_fortiswitch_api_service = None

def get_fortiswitch_api_service() -> FortiSwitchAPIService:
    """Get global FortiSwitch API service instance for Sonic locations"""
    global _fortiswitch_api_service
    if _fortiswitch_api_service is None:
        _fortiswitch_api_service = FortiSwitchAPIService()
    return _fortiswitch_api_service

# Legacy compatibility
def get_fortiswitch_service() -> FortiSwitchAPIService:
    """Legacy alias for FortiSwitch service (Sonic locations)"""
    return get_fortiswitch_api_service()