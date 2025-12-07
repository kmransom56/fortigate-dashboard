"""
Brand-Specific Network Device Detection Service

Handles intelligent detection of network infrastructure based on restaurant brand:
- Sonic: FortiGate + FortiSwitch + FortiAP
- BWW: FortiGate + Meraki + FortiAP  
- Arby's: FortiGate + Meraki + FortiAP
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import asyncio
from datetime import datetime
import ipaddress

from .organization_service import get_organization_service, RestaurantBrand, InfrastructureType
from .meraki_service import get_meraki_service
from .fortiswitch_api_service import get_fortiswitch_service
from .fortigate_inventory_service import get_fortigate_inventory_service

logger = logging.getLogger(__name__)

class DeviceType(Enum):
    FORTIGATE = "fortigate"
    FORTISWITCH = "fortiswitch"
    MERAKI_SWITCH = "meraki_switch"
    FORTIAP = "fortiap"
    RESTAURANT_DEVICE = "restaurant_device"

@dataclass
class BrandDetectionResult:
    brand: RestaurantBrand
    location_id: str
    store_number: str
    confidence: float
    infrastructure_type: InfrastructureType
    detected_devices: List[Dict[str, Any]]
    discovery_method: str

class BrandDetectionService:
    """Service for detecting restaurant brand and associated network infrastructure"""
    
    def __init__(self):
        self.org_service = get_organization_service()
        self.meraki_service = get_meraki_service()
        self.inventory_service = get_fortigate_inventory_service()
        
        # IP range mappings for restaurant brands (from VLAN10 data analysis)
        self.brand_ip_patterns = {
            RestaurantBrand.SONIC: [
                "10.0.0.0/8",     # Common Sonic range
                "172.16.0.0/12",  # Private range
                "192.168.0.0/16"  # Home/test range
            ],
            RestaurantBrand.BWW: [
                "10.1.0.0/16",    # BWW specific range
                "172.20.0.0/16",  # BWW corporate range
            ],
            RestaurantBrand.ARBYS: [
                "10.2.0.0/16",    # Arby's specific range
                "172.30.0.0/16",  # Arby's corporate range
            ]
        }
    
    def detect_brand_from_ip(self, ip_address: str) -> Tuple[Optional[RestaurantBrand], float]:
        """
        Detect restaurant brand based on IP address patterns
        
        Returns:
            Tuple of (brand, confidence_score)
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            
            for brand, ip_ranges in self.brand_ip_patterns.items():
                for ip_range in ip_ranges:
                    network = ipaddress.ip_network(ip_range)
                    if ip in network:
                        # Higher confidence for more specific ranges
                        confidence = 0.9 if network.prefixlen >= 16 else 0.7
                        return brand, confidence
            
            return None, 0.0
            
        except ValueError:
            logger.warning(f"Invalid IP address for brand detection: {ip_address}")
            return None, 0.0
    
    def detect_brand_from_inventory(self, ip_address: str) -> Tuple[Optional[RestaurantBrand], float, Optional[str]]:
        """
        Detect brand from FortiGate inventory data
        
        Returns:
            Tuple of (brand, confidence, store_number)
        """
        try:
            location = self.inventory_service.get_location_by_ip(ip_address)
            if location:
                brand_mapping = {
                    "Sonic": RestaurantBrand.SONIC,
                    "BWW": RestaurantBrand.BWW,
                    "Arbys": RestaurantBrand.ARBYS
                }
                
                brand = brand_mapping.get(location.brand)
                return brand, 0.95, location.store_number  # High confidence from inventory
            
            return None, 0.0, None
            
        except Exception as e:
            logger.error(f"Error detecting brand from inventory: {e}")
            return None, 0.0, None
    
    async def detect_infrastructure_type(self, ip_address: str, brand: RestaurantBrand) -> InfrastructureType:
        """
        Detect infrastructure type based on brand and device discovery
        
        Args:
            ip_address: FortiGate management IP
            brand: Detected restaurant brand
        """
        try:
            if brand == RestaurantBrand.SONIC:
                # Sonic uses full Fortinet stack
                return InfrastructureType.FORTINET_FULL
            
            elif brand in [RestaurantBrand.BWW, RestaurantBrand.ARBYS]:
                # BWW and Arby's use FortiGate + Meraki switches
                return InfrastructureType.FORTINET_MERAKI
            
            else:
                # Unknown brand - try to detect from actual devices
                return await self._probe_infrastructure_type(ip_address)
                
        except Exception as e:
            logger.error(f"Error detecting infrastructure type: {e}")
            return InfrastructureType.MIXED
    
    async def _probe_infrastructure_type(self, ip_address: str) -> InfrastructureType:
        """
        Probe infrastructure type by attempting device discovery
        """
        try:
            # Try FortiSwitch discovery first
            try:
                fortiswitch_service = get_fortiswitch_service()
                switches = fortiswitch_service.get_managed_switches()
                
                if switches and not switches.get("error") and switches.get("switches"):
                    logger.info("Detected FortiSwitch infrastructure")
                    return InfrastructureType.FORTINET_FULL
                    
            except Exception as e:
                logger.debug(f"FortiSwitch detection failed: {e}")
            
            # Try Meraki discovery
            try:
                meraki_data = self.meraki_service.discover_restaurant_meraki_switches()
                
                if meraki_data and not meraki_data.get("error") and meraki_data.get("switches"):
                    logger.info("Detected Meraki switch infrastructure")
                    return InfrastructureType.FORTINET_MERAKI
                    
            except Exception as e:
                logger.debug(f"Meraki detection failed: {e}")
            
            # Default to mixed if unclear
            return InfrastructureType.MIXED
            
        except Exception as e:
            logger.error(f"Infrastructure probing failed: {e}")
            return InfrastructureType.MIXED
    
    async def discover_brand_devices(self, ip_address: str) -> BrandDetectionResult:
        """
        Comprehensive brand detection and device discovery
        
        Args:
            ip_address: FortiGate management IP address
        """
        logger.info(f"Starting brand detection for IP: {ip_address}")
        
        # Step 1: Try inventory-based detection (highest confidence)
        brand, confidence, store_number = self.detect_brand_from_inventory(ip_address)
        detection_method = "inventory_lookup"
        
        # Step 2: Fallback to IP-based detection
        if not brand:
            brand, confidence = self.detect_brand_from_ip(ip_address)
            detection_method = "ip_pattern_match"
            store_number = f"unknown_{ip_address.replace('.', '_')}"
        
        # Step 3: Default to unknown if no detection
        if not brand:
            brand = RestaurantBrand.SONIC  # Default for home lab
            confidence = 0.1
            detection_method = "default_fallback"
            store_number = f"lab_{ip_address.replace('.', '_')}"
        
        # Step 4: Detect infrastructure type
        infrastructure_type = await self.detect_infrastructure_type(ip_address, brand)
        
        # Step 5: Discover devices based on detected infrastructure
        detected_devices = await self._discover_devices_by_type(infrastructure_type, ip_address)
        
        result = BrandDetectionResult(
            brand=brand,
            location_id=f"{brand.value}_{store_number}",
            store_number=store_number,
            confidence=confidence,
            infrastructure_type=infrastructure_type,
            detected_devices=detected_devices,
            discovery_method=detection_method
        )
        
        logger.info(f"Brand detection complete: {brand.value} ({confidence:.2f} confidence) - {len(detected_devices)} devices")
        return result
    
    async def _discover_devices_by_type(self, infrastructure_type: InfrastructureType, ip_address: str) -> List[Dict[str, Any]]:
        """
        Discover devices based on infrastructure type
        """
        devices = []
        
        try:
            if infrastructure_type == InfrastructureType.FORTINET_FULL:
                # Sonic: Discover FortiGate + FortiSwitch + FortiAP
                devices.extend(await self._discover_fortigate_devices(ip_address))
                devices.extend(await self._discover_fortiswitch_devices(ip_address))
                devices.extend(await self._discover_fortiap_devices(ip_address))
                
            elif infrastructure_type == InfrastructureType.FORTINET_MERAKI:
                # BWW/Arby's: Discover FortiGate + Meraki + FortiAP
                devices.extend(await self._discover_fortigate_devices(ip_address))
                devices.extend(await self._discover_meraki_devices(ip_address))
                devices.extend(await self._discover_fortiap_devices(ip_address))
                
            else:
                # Mixed: Try all discovery methods
                devices.extend(await self._discover_fortigate_devices(ip_address))
                devices.extend(await self._discover_fortiswitch_devices(ip_address))
                devices.extend(await self._discover_meraki_devices(ip_address))
                devices.extend(await self._discover_fortiap_devices(ip_address))
        
        except Exception as e:
            logger.error(f"Device discovery failed: {e}")
        
        return devices
    
    async def _discover_fortigate_devices(self, ip_address: str) -> List[Dict[str, Any]]:
        """Discover FortiGate firewall (present in all brands)"""
        devices = []
        try:
            # FortiGate is always present - add basic info
            devices.append({
                "device_type": DeviceType.FORTIGATE.value,
                "ip_address": ip_address,
                "model": "Unknown",  # Would be detected via SNMP/API
                "serial": "Unknown",
                "status": "detected",
                "discovery_method": "assumption",  # All brands have FortiGate
                "management_interface": "primary"
            })
            logger.info(f"Added FortiGate device: {ip_address}")
        except Exception as e:
            logger.error(f"FortiGate discovery error: {e}")
        
        return devices
    
    async def _discover_fortiswitch_devices(self, ip_address: str) -> List[Dict[str, Any]]:
        """Discover FortiSwitch devices (Sonic only)"""
        devices = []
        try:
            fortiswitch_service = get_fortiswitch_service()
            switches_data = fortiswitch_service.get_managed_switches()
            
            if switches_data and not switches_data.get("error"):
                for switch in switches_data.get("switches", []):
                    devices.append({
                        "device_type": DeviceType.FORTISWITCH.value,
                        "serial": switch.get("serial"),
                        "model": switch.get("model"),
                        "ip_address": switch.get("mgmt_ip"),
                        "status": switch.get("status"),
                        "discovery_method": "fortilink_api",
                        "port_count": len(switch.get("ports", []))
                    })
                    
            logger.info(f"Discovered {len(devices)} FortiSwitch devices")
        except Exception as e:
            logger.debug(f"FortiSwitch discovery failed (expected for non-Sonic): {e}")
        
        return devices
    
    async def _discover_meraki_devices(self, ip_address: str) -> List[Dict[str, Any]]:
        """Discover Meraki switches (BWW/Arby's only)"""
        devices = []
        try:
            # Determine organization filter based on IP
            brand, _ = self.detect_brand_from_ip(ip_address)
            org_filter = None
            
            if brand == RestaurantBrand.BWW:
                org_filter = "bww"
            elif brand == RestaurantBrand.ARBYS:
                org_filter = "arbys"
            
            switches_data = self.meraki_service.discover_restaurant_meraki_switches(org_filter)
            
            if switches_data and not switches_data.get("error"):
                for switch in switches_data.get("switches", []):
                    devices.append({
                        "device_type": DeviceType.MERAKI_SWITCH.value,
                        "serial": switch.get("serial"),
                        "model": switch.get("model"),
                        "ip_address": switch.get("management_ip"),
                        "status": switch.get("status"),
                        "discovery_method": "meraki_dashboard_api",
                        "organization": switch.get("organization_name"),
                        "network": switch.get("network_name"),
                        "client_count": switch.get("connected_clients", 0)
                    })
                    
            logger.info(f"Discovered {len(devices)} Meraki switches")
        except Exception as e:
            logger.debug(f"Meraki discovery failed (expected for non-BWW/Arby's): {e}")
        
        return devices
    
    async def _discover_fortiap_devices(self, ip_address: str) -> List[Dict[str, Any]]:
        """Discover FortiAP devices (all brands)"""
        devices = []
        try:
            # FortiAP discovery would typically go through FortiGate WiFi controller
            # This is a placeholder for actual FortiAP discovery implementation
            
            # Simulate FortiAP discovery based on brand
            brand, _ = self.detect_brand_from_ip(ip_address)
            
            if brand == RestaurantBrand.SONIC:
                ap_count = 4  # Typical for Sonic locations
            elif brand == RestaurantBrand.BWW:
                ap_count = 6  # Larger venues need more APs
            elif brand == RestaurantBrand.ARBYS:
                ap_count = 3  # Smaller venues
            else:
                ap_count = 2  # Default
            
            for i in range(ap_count):
                devices.append({
                    "device_type": DeviceType.FORTIAP.value,
                    "serial": f"FAP-{ip_address.replace('.', '')}-{i+1:02d}",
                    "model": "FAP-231F",  # Common model
                    "ip_address": f"{'.'.join(ip_address.split('.')[:-1])}.{100+i}",
                    "status": "online",
                    "discovery_method": "simulated_controller",
                    "location": f"Zone-{i+1}",
                    "ssid_count": 3  # Guest, Employee, Management
                })
            
            logger.info(f"Simulated {len(devices)} FortiAP devices for {brand.value if brand else 'unknown'}")
        except Exception as e:
            logger.error(f"FortiAP discovery error: {e}")
        
        return devices
    
    def get_expected_infrastructure(self, brand: RestaurantBrand) -> Dict[str, Any]:
        """
        Get expected infrastructure components for a restaurant brand
        """
        infrastructure_map = {
            RestaurantBrand.SONIC: {
                "firewall": "FortiGate",
                "switches": "FortiSwitch",
                "wireless": "FortiAP",
                "management": "FortiManager (optional)",
                "expected_devices": ["FortiGate", "FortiSwitch", "FortiAP"],
                "topology_type": "fortinet_security_fabric"
            },
            RestaurantBrand.BWW: {
                "firewall": "FortiGate", 
                "switches": "Meraki",
                "wireless": "FortiAP",
                "management": "Meraki Dashboard + FortiManager",
                "expected_devices": ["FortiGate", "Meraki Switch", "FortiAP"],
                "topology_type": "hybrid_fortinet_meraki"
            },
            RestaurantBrand.ARBYS: {
                "firewall": "FortiGate",
                "switches": "Meraki", 
                "wireless": "FortiAP",
                "management": "Meraki Dashboard + FortiManager",
                "expected_devices": ["FortiGate", "Meraki Switch", "FortiAP"],
                "topology_type": "hybrid_fortinet_meraki"
            }
        }
        
        return infrastructure_map.get(brand, {
            "firewall": "Unknown",
            "switches": "Unknown",
            "wireless": "Unknown", 
            "management": "Unknown",
            "expected_devices": [],
            "topology_type": "unknown"
        })
    
    async def get_brand_topology_summary(self, brand_filter: str = None) -> Dict[str, Any]:
        """
        Get topology summary filtered by restaurant brand
        """
        summary = {
            "brands": {},
            "total_devices": 0,
            "discovery_time": datetime.now().isoformat(),
            "infrastructure_types": {}
        }
        
        try:
            # Get inventory data for brand filtering
            inventory_data = self.inventory_service.get_inventory_summary()
            
            for brand_name, brand_data in inventory_data.get("brands", {}).items():
                if brand_filter and brand_filter.lower() != brand_name.lower():
                    continue
                
                # Map brand name to enum
                brand_enum = None
                if brand_name.lower() == "sonic":
                    brand_enum = RestaurantBrand.SONIC
                elif brand_name.lower() == "bww":
                    brand_enum = RestaurantBrand.BWW
                elif brand_name.lower() == "arbys":
                    brand_enum = RestaurantBrand.ARBYS
                
                if brand_enum:
                    expected_infra = self.get_expected_infrastructure(brand_enum)
                    
                    summary["brands"][brand_name] = {
                        "location_count": brand_data.get("count", 0),
                        "expected_infrastructure": expected_infra,
                        "fortigate_count": brand_data.get("count", 0),  # 1 per location
                        "estimated_switches": brand_data.get("count", 0),  # 1 per location
                        "estimated_aps": brand_data.get("count", 0) * (4 if brand_enum == RestaurantBrand.SONIC else 3 if brand_enum == RestaurantBrand.ARBYS else 6),
                        "infrastructure_type": expected_infra.get("topology_type")
                    }
                    
                    summary["total_devices"] += brand_data.get("count", 0) * 6  # Estimate 6 devices per location
            
            # Count infrastructure types
            for brand_info in summary["brands"].values():
                infra_type = brand_info.get("infrastructure_type", "unknown")
                summary["infrastructure_types"][infra_type] = summary["infrastructure_types"].get(infra_type, 0) + brand_info.get("location_count", 0)
            
        except Exception as e:
            logger.error(f"Error generating brand topology summary: {e}")
            summary["error"] = str(e)
        
        return summary


# Global service instance
_brand_detection_service = None

def get_brand_detection_service() -> BrandDetectionService:
    """Get the global brand detection service instance"""
    global _brand_detection_service
    if _brand_detection_service is None:
        _brand_detection_service = BrandDetectionService()
    return _brand_detection_service