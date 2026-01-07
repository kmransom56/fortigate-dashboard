"""
Hybrid Topology Service

Combines SNMP-based discovery with FortiGate API data to provide
comprehensive network topology information.
"""

import logging
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from .snmp_service import get_snmp_discovery
from .fortiswitch_api_service import get_fortiswitch_api_service
from .fortigate_monitor_service import get_fortigate_monitor_service
from .meraki_service import get_meraki_service
from .organization_service import get_organization_service

logger = logging.getLogger(__name__)

class HybridTopologyService:
    """
    Service that combines SNMP discovery with API data to provide
    the most complete network topology information possible.
    """
    
    def __init__(self):
        self.snmp_service = get_snmp_discovery()
        self.api_service = get_fortiswitch_api_service()
        self.monitor_service = get_fortigate_monitor_service()
        self.meraki_service = get_meraki_service()
        self.org_service = get_organization_service()
    
    def get_comprehensive_topology(self) -> Dict[str, Any]:
        """
        Get comprehensive topology data using Monitor API, Switch API, and SNMP.
        Prioritizes real-time Monitor API data for device detection.
        """
        try:
            # Try to get data from all sources concurrently
            api_data = None
            snmp_data = None
            monitor_data = None
            
            # Get data sequentially for now to debug issues
            # Get API data (switch configuration)
            try:
                api_data = self.api_service.get_managed_switches()
                logger.info("Successfully retrieved Switch API data")
            except Exception as e:
                logger.warning(f"Switch API data retrieval failed: {e}")
            
            # Get Monitor data (real-time devices) - HIGHEST PRIORITY
            try:
                monitor_data = self.monitor_service.get_detected_devices()
                logger.info("Successfully retrieved Monitor API data")
            except Exception as e:
                logger.error(f"Monitor API data retrieval FAILED: {e}")
                monitor_data = None
            
            # Get SNMP data (fallback/supplement)
            try:
                snmp_data = self.snmp_service.get_fortiswitch_data()
                logger.info("Successfully retrieved SNMP data")
            except Exception as e:
                logger.warning(f"SNMP data retrieval failed: {e}")
            
            # Combine and prioritize the data
            return self._merge_topology_data_enhanced(api_data, snmp_data, monitor_data)
            
        except Exception as e:
            logger.error(f"Exception in hybrid topology service: {e}")
            return {"switches": [], "total_switches": 0, "source": "hybrid", "error": str(e)}
    
    def _merge_topology_data(self, api_data: Dict[str, Any], snmp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge API and SNMP data, prioritizing API data when available.
        """
        # If API data is good, use it as primary
        if api_data and not api_data.get("error") and api_data.get("switches"):
            logger.info("Using API data as primary source")
            merged_data = api_data.copy()
            
            # Enhance API data with SNMP device information
            if snmp_data and not snmp_data.get("error"):
                merged_data = self._enhance_api_with_snmp(merged_data, snmp_data)
                merged_data["source"] = "api_enhanced_with_snmp"
            else:
                merged_data["source"] = "api_only"
                
            return merged_data
        
        # Fall back to SNMP data if API failed
        elif snmp_data and not snmp_data.get("error") and snmp_data.get("switches"):
            logger.info("Using SNMP data as primary source (API unavailable)")
            snmp_data["source"] = "snmp_fallback"
            return snmp_data
        
        # Both failed - return empty but valid structure
        else:
            logger.warning("Both API and SNMP data unavailable")
            return {
                "switches": [],
                "total_switches": 0,
                "source": "none_available",
                "errors": {
                    "api": api_data.get("error") if api_data else "No data",
                    "snmp": snmp_data.get("error") if snmp_data else "No data"
                }
            }
    
    def _enhance_api_with_snmp(self, api_data: Dict[str, Any], snmp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance API switch data with device information from SNMP discovery.
        """
        try:
            # Get SNMP device list
            snmp_devices = self.snmp_service.get_network_devices()
            
            # Create lookup by port for matching
            snmp_device_by_port = {}
            for device in snmp_devices:
                port_name = device.get("port_name", "")
                if port_name:
                    # Normalize port names (port13 -> port13, etc.)
                    normalized_port = port_name.lower()
                    snmp_device_by_port[normalized_port] = device
            
            # Enhance API switch data
            enhanced_switches = []
            for switch in api_data.get("switches", []):
                enhanced_switch = switch.copy()
                
                # Enhance port information with SNMP device data
                enhanced_ports = []
                for port in switch.get("ports", []):
                    enhanced_port = port.copy()
                    port_name = port.get("name", "").lower()
                    
                    # Look for matching SNMP device
                    if port_name in snmp_device_by_port:
                        snmp_device = snmp_device_by_port[port_name]
                        
                        # Add connected device information
                        connected_device = {
                            "ip": snmp_device.get("ip"),
                            "mac": snmp_device.get("mac"),
                            "hostname": snmp_device.get("hostname"),
                            "device_name": snmp_device.get("hostname"),
                            "manufacturer": snmp_device.get("manufacturer"),
                            "device_type": snmp_device.get("device_type"),
                            "device_ip": snmp_device.get("ip"),
                            "device_mac": snmp_device.get("mac"),
                            "source": "snmp_discovery"
                        }
                        enhanced_port["connected_devices"] = [connected_device]
                        enhanced_port["has_snmp_data"] = True
                        
                        logger.debug(f"Enhanced {port_name} with SNMP device: {snmp_device.get('hostname')}")
                    else:
                        enhanced_port["connected_devices"] = []
                        enhanced_port["has_snmp_data"] = False
                    
                    enhanced_ports.append(enhanced_port)
                
                enhanced_switch["ports"] = enhanced_ports
                
                # Update switch-level connected device count
                total_connected = sum(1 for port in enhanced_ports if port.get("connected_devices"))
                enhanced_switch["connected_devices_count"] = total_connected
                
                enhanced_switches.append(enhanced_switch)
            
            # Update the data
            enhanced_data = api_data.copy()
            enhanced_data["switches"] = enhanced_switches
            enhanced_data["enhancement_info"] = {
                "snmp_devices_found": len(snmp_devices),
                "ports_enhanced": sum(1 for switch in enhanced_switches 
                                    for port in switch.get("ports", []) 
                                    if port.get("has_snmp_data"))
            }
            
            logger.info(f"Enhanced API data with {len(snmp_devices)} SNMP devices")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error enhancing API data with SNMP: {e}")
            return api_data  # Return original API data if enhancement fails
    
    def _merge_topology_data_enhanced(self, api_data: Dict[str, Any], snmp_data: Dict[str, Any], monitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced merge with Monitor API, Switch API, and SNMP data.
        Prioritizes Monitor API for real-time device detection.
        """
        try:
            # Start with switch configuration from API or SNMP
            base_data = None
            if api_data and not api_data.get("error") and api_data.get("switches"):
                base_data = api_data.copy()
                logger.info("Using Switch API as base configuration")
            elif snmp_data and not snmp_data.get("error") and snmp_data.get("switches"):
                base_data = snmp_data.copy()
                logger.info("Using SNMP as base configuration (Switch API unavailable)")
            else:
                logger.warning("No switch configuration data available")
                return {"switches": [], "total_switches": 0, "source": "none_available"}
            
            # Enhance with real-time Monitor API device detection
            logger.info(f"Monitor data available: {monitor_data is not None}")
            if monitor_data:
                logger.info(f"Monitor data keys: {list(monitor_data.keys())}")
                logger.info(f"Monitor devices count: {len(monitor_data.get('devices', []))}")
                
            if monitor_data and not monitor_data.get("error") and monitor_data.get("devices"):
                enhanced_switches = []
                
                # Create device lookup by switch and port
                monitor_devices = {}
                for device in monitor_data.get("devices", []):
                    switch_id = device.get("switch_id", "")
                    port_name = device.get("port_name", "")
                    key = f"{switch_id}:{port_name}"
                    
                    # Convert Monitor API device to topology format
                    topo_device = {
                        "ip": device.get("ip", ""),  # Monitor API doesn't provide IP
                        "mac": device.get("mac", ""),
                        "hostname": device.get("hostname", f"Device-{device.get('mac', '')[-8:]}"),
                        "device_name": device.get("hostname", f"Device-{device.get('mac', '')[-8:]}"),
                        "manufacturer": device.get("manufacturer", "Unknown"),  # Could enhance with OUI lookup
                        "device_type": device.get("device_type", "endpoint"),
                        "device_ip": device.get("ip", ""),
                        "device_mac": device.get("mac", ""),
                        "last_seen": device.get("last_seen_human", "unknown"),
                        "is_active": device.get("is_active", False),
                        "activity_status": device.get("activity_status", "unknown"),
                        "vlan_id": device.get("vlan_id", 0),
                        "port_statistics": device.get("port_statistics", {}),
                        "source": "monitor_api_realtime"
                    }
                    
                    if key not in monitor_devices:
                        monitor_devices[key] = []
                    monitor_devices[key].append(topo_device)
                
                # Enhance each switch with monitor data
                for switch in base_data.get("switches", []):
                    enhanced_switch = switch.copy()
                    switch_serial = switch.get("serial", "")
                    switch_name = switch.get("name", switch.get("switch_id", ""))
                    
                    # Enhance ports with monitor device data
                    enhanced_ports = []
                    for port in switch.get("ports", []):
                        enhanced_port = port.copy()
                        port_name = port.get("name", "")
                        
                        # Look for monitor devices on this port
                        lookup_key = f"{switch_name}:{port_name}"
                        if lookup_key in monitor_devices:
                            enhanced_port["connected_devices"] = monitor_devices[lookup_key]
                            enhanced_port["has_monitor_data"] = True
                            enhanced_port["device_count"] = len(monitor_devices[lookup_key])
                            logger.info(f"Enhanced {port_name} with {len(monitor_devices[lookup_key])} monitor devices")
                        else:
                            logger.debug(f"No monitor devices found for {lookup_key}, available keys: {list(monitor_devices.keys())[:3]}")
                            enhanced_port["connected_devices"] = enhanced_port.get("connected_devices", [])
                            enhanced_port["has_monitor_data"] = False
                            enhanced_port["device_count"] = len(enhanced_port.get("connected_devices", []))
                        
                        enhanced_ports.append(enhanced_port)
                    
                    enhanced_switch["ports"] = enhanced_ports
                    enhanced_switch["total_connected_devices"] = sum(p.get("device_count", 0) for p in enhanced_ports)
                    enhanced_switches.append(enhanced_switch)
                
                # Update the data
                enhanced_data = base_data.copy()
                enhanced_data["switches"] = enhanced_switches
                enhanced_data["source"] = f"{base_data.get('source', 'unknown')}_enhanced_with_monitor"
                enhanced_data["monitor_enhancement"] = {
                    "total_monitor_devices": len(monitor_data.get("devices", [])),
                    "active_devices": monitor_data.get("active_devices", 0),
                    "ports_enhanced": sum(1 for switch in enhanced_switches 
                                        for port in switch.get("ports", []) 
                                        if port.get("has_monitor_data")),
                    "monitor_api_info": monitor_data.get("api_info", {})
                }
                
                logger.info(f"Enhanced topology with {len(monitor_data.get('devices', []))} monitor devices")
                return enhanced_data
                
            else:
                logger.warning("No Monitor API device data available, using base configuration")
                base_data["source"] = f"{base_data.get('source', 'unknown')}_monitor_unavailable"
                return base_data
                
        except Exception as e:
            logger.error(f"Error in enhanced topology merge: {e}")
            # Fall back to original merge method
            return self._merge_topology_data(api_data, snmp_data)
    
    def get_network_devices(self) -> List[Dict[str, Any]]:
        """
        Get all network devices from combined sources.
        """
        try:
            # Get comprehensive topology
            topology = self.get_comprehensive_topology()
            
            # Extract devices from switches
            devices = []
            for switch in topology.get("switches", []):
                switch_serial = switch.get("serial")
                switch_name = switch.get("name")
                
                for port in switch.get("ports", []):
                    for device in port.get("connected_devices", []):
                        # Add switch context
                        device_with_context = device.copy()
                        device_with_context["switch_serial"] = switch_serial
                        device_with_context["switch_name"] = switch_name
                        device_with_context["port_name"] = port.get("name")
                        devices.append(device_with_context)
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting network devices: {e}")
            return []
    
    def get_enterprise_topology(self, org_filter: str = None) -> Dict[str, Any]:
        """
        Get enterprise-wide topology including both FortiSwitches and Meraki switches
        
        Args:
            org_filter: Filter for specific organization (sonic, bww, arbys)
        """
        logger.info(f"Getting enterprise topology with filter: {org_filter}")
        
        enterprise_data = {
            "fortiswitches": [],
            "meraki_switches": [],
            "source": "enterprise_multi_vendor",
            "discovery_time": None,
            "api_info": {
                "fortiswitch_requests": 0,
                "meraki_requests": 0,
                "errors": []
            }
        }
        
        try:
            # Get current location infrastructure type (from organization service)
            if org_filter is None or org_filter == "local":
                logger.info("Local lab mode: Skipping enterprise/Meraki discovery")
                return self.get_comprehensive_topology()

            if org_filter == "sonic":
                try:
                    fortiswitch_data = self.get_comprehensive_topology()
                    if fortiswitch_data and not fortiswitch_data.get("error"):
                        enterprise_data["fortiswitches"] = fortiswitch_data.get("switches", [])
                        enterprise_data["api_info"]["fortiswitch_requests"] = fortiswitch_data.get("api_info", {}).get("requests", 0)
                        logger.info(f"Found {len(enterprise_data['fortiswitches'])} FortiSwitches")
                    else:
                        enterprise_data["api_info"]["errors"].append(f"FortiSwitch: {fortiswitch_data.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"FortiSwitch discovery failed: {e}")
                    enterprise_data["api_info"]["errors"].append(f"FortiSwitch exception: {str(e)}")
            
            # Get Meraki data (for BWW and Arby's locations)
            # SKIP Meraki for local lab to avoid unnecessary timeouts
            if org_filter is not None and org_filter in ["bww", "arbys"]:
                try:
                    meraki_data = self.meraki_service.get_switch_topology_data(org_filter)
                    if meraki_data and not meraki_data.get("error"):
                        enterprise_data["meraki_switches"] = meraki_data.get("switches", [])
                        enterprise_data["api_info"]["meraki_requests"] = meraki_data.get("enhancement_info", {}).get("api_requests", 0)
                        logger.info(f"Found {len(enterprise_data['meraki_switches'])} Meraki switches")
                    else:
                        enterprise_data["api_info"]["errors"].append(f"Meraki: {meraki_data.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Meraki discovery failed: {e}")
                    enterprise_data["api_info"]["errors"].append(f"Meraki exception: {str(e)}")
            
            # Combine all switches into unified format
            all_switches = []
            
            # Add FortiSwitches
            for switch in enterprise_data["fortiswitches"]:
                unified_switch = {
                    "serial": switch.get("serial"),
                    "model": switch.get("model"),
                    "name": switch.get("name"),
                    "status": switch.get("status"),
                    "mgmt_ip": switch.get("mgmt_ip"),
                    "switch_type": "fortiswitch",
                    "organization": "sonic",  # Sonic uses FortiGate + FortiSwitch + FortiAP
                    "infrastructure_type": "fortinet_full",
                    "ports": switch.get("ports", []),
                    "connected_devices_count": switch.get("total_connected_devices", 0)
                }
                all_switches.append(unified_switch)
            
            # Add Meraki switches (BWW and Arby's use FortiGate + Meraki + FortiAP)
            for switch in enterprise_data["meraki_switches"]:
                org_name = switch.get("organization", "unknown").lower()
                if "buffalo" in org_name or "bww" in org_name:
                    org_brand = "bww"
                elif "arby" in org_name:
                    org_brand = "arbys"
                else:
                    org_brand = "unknown"
                
                unified_switch = {
                    "serial": switch.get("serial"),
                    "model": switch.get("model"),
                    "name": switch.get("name"),
                    "status": switch.get("status"),
                    "mgmt_ip": switch.get("mgmt_ip"),
                    "switch_type": "meraki",
                    "organization": org_brand,
                    "infrastructure_type": "fortinet_meraki",  # BWW/Arby's: FortiGate + Meraki + FortiAP
                    "ports": switch.get("ports", []),
                    "connected_devices_count": switch.get("connected_clients", 0),
                    "network": switch.get("network")
                }
                all_switches.append(unified_switch)
            
            enterprise_data["switches"] = all_switches
            enterprise_data["total_switches"] = len(all_switches)
            enterprise_data["fortiswitch_count"] = len(enterprise_data["fortiswitches"])
            enterprise_data["meraki_count"] = len(enterprise_data["meraki_switches"])
            
            logger.info(f"Enterprise topology complete: {len(all_switches)} total switches ({enterprise_data['fortiswitch_count']} FortiSwitch, {enterprise_data['meraki_count']} Meraki)")
            
            return enterprise_data
            
        except Exception as e:
            logger.error(f"Enterprise topology discovery failed: {e}")
            enterprise_data["api_info"]["errors"].append(f"Enterprise discovery exception: {str(e)}")
            return enterprise_data
    
    def get_topology_summary(self) -> Dict[str, Any]:
        """Get comprehensive topology summary"""
        topology = self.get_comprehensive_topology()
        devices = self.get_network_devices()
        
        # Count devices by type
        servers = [d for d in devices if d.get("device_type") == "server"]
        endpoints = [d for d in devices if d.get("device_type") == "endpoint"]
        
        return {
            "fortigate_count": 1,
            "fortiswitch_count": topology.get("total_switches", 0),
            "server_count": len(servers),
            "endpoint_count": len(endpoints),
            "total_devices": 1 + topology.get("total_switches", 0) + len(devices),
            "data_source": topology.get("source", "unknown"),
            "last_updated": topology.get("api_info", {}),
            "enhancement_info": topology.get("enhancement_info", {})
        }

# Global instance
_hybrid_topology_service = None

def get_hybrid_topology_service() -> HybridTopologyService:
    """Get global hybrid topology service instance"""
    global _hybrid_topology_service
    if _hybrid_topology_service is None:
        _hybrid_topology_service = HybridTopologyService()
    return _hybrid_topology_service