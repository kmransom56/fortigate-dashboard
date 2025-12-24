"""
FortiGate Monitor API Service

Uses FortiGate Monitor API endpoints to discover real-time device information:
- /monitor/switch-controller/detected-device - Real-time device detection
- /monitor/switch-controller/matched-devices - NAC/policy matched devices
- /monitor/switch-controller/managed-switch/port-stats - Port statistics
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from .fortigate_service import fgt_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DetectedDevice:
    """Represents a device detected by FortiGate on FortiSwitch ports"""

    mac: str
    switch_id: str
    port_name: str
    port_id: int
    vlan_id: int
    last_seen: int  # seconds ago
    vdom: str
    is_active: bool = False  # derived from last_seen


@dataclass
class PortStatistics:
    """Represents port traffic statistics"""

    port_name: str
    tx_bytes: int
    tx_packets: int
    rx_bytes: int
    rx_packets: int
    tx_errors: int
    rx_errors: int
    rx_drops: int
    utilization_score: float = 0.0  # derived metric


class FortiGateMonitorService:
    """
    Service for real-time network monitoring using FortiGate Monitor API.
    Provides dynamic device discovery and port statistics.
    """

    def __init__(self):
        self.active_threshold = 300  # Consider device active if seen within 5 minutes

    def get_detected_devices(self) -> Dict[str, Any]:
        """
        Get real-time detected devices from FortiGate Monitor API.
        Returns devices with MAC-to-port mappings and activity status.
        """
        try:
            data = fgt_api("monitor/switch-controller/detected-device")

            if "error" in data:
                logger.error(f"API error getting detected devices: {data}")
                return {
                    "devices": [],
                    "total_devices": 0,
                    "source": "monitor_api",
                    "error": data.get("error"),
                }

            # Process detected devices
            devices = []
            active_devices = 0

            if "results" in data and isinstance(data["results"], list):
                for device_data in data["results"]:
                    # Determine if device is active (seen recently)
                    last_seen = device_data.get("last_seen", 999999)
                    is_active = last_seen <= self.active_threshold

                    if is_active:
                        active_devices += 1

                    # Get manufacturer from OUI lookup
                    mac = device_data.get("mac", "")
                    manufacturer = "Unknown Manufacturer"
                    try:
                        from app.utils.oui_lookup import get_manufacturer_from_mac

                        manufacturer = get_manufacturer_from_mac(mac)
                        logger.debug(f"OUI lookup for {mac}: {manufacturer}")
                    except Exception as e:
                        logger.warning(f"OUI lookup failed for {mac}: {e}")

                    # Get appropriate icon
                    icon_path = None
                    icon_title = None
                    try:
                        from app.utils.icon_db import get_icon, get_icon_binding

                        # Try manufacturer-specific icon first
                        icon_info = get_icon(manufacturer=manufacturer)
                        if not icon_info:
                            # Try icon binding
                            binding = get_icon_binding(manufacturer=manufacturer)
                            if binding:
                                icon_info = {
                                    "icon_path": binding["icon_path"],
                                    "title": binding["title"],
                                }

                        if icon_info:
                            icon_path = icon_info["icon_path"]
                            icon_title = icon_info["title"]
                        else:
                            # Fall back to device type icon
                            type_icon = get_icon(device_type="endpoint")
                            if type_icon:
                                icon_path = type_icon["icon_path"]
                                icon_title = type_icon["title"]
                    except Exception as e:
                        logger.warning(f"Icon lookup failed for {mac}: {e}")

                    device = {
                        "mac": mac,
                        "switch_id": device_data.get("switch_id", ""),
                        "port_name": device_data.get("port_name", ""),
                        "port_id": device_data.get("port_id", 0),
                        "vlan_id": device_data.get("vlan_id", 0),
                        "last_seen": last_seen,
                        "last_seen_human": self._format_time_ago(last_seen),
                        "vdom": device_data.get("vdom", "root"),
                        "is_active": is_active,
                        "activity_status": "active" if is_active else "inactive",
                        "device_type": "endpoint",
                        "manufacturer": manufacturer,
                        "icon_path": icon_path,
                        "icon_title": icon_title,
                        "source": "fortigate_monitor",
                    }
                    devices.append(device)

            logger.info(
                f"Retrieved {len(devices)} detected devices ({active_devices} active)"
            )

            return {
                "devices": devices,
                "total_devices": len(devices),
                "active_devices": active_devices,
                "inactive_devices": len(devices) - active_devices,
                "source": "monitor_api",
                "timestamp": datetime.now().isoformat(),
                "api_info": {
                    "endpoint": "monitor/switch-controller/detected-device",
                    "serial": data.get("serial"),
                    "version": data.get("version"),
                    "build": data.get("build"),
                },
            }

        except Exception as e:
            logger.error(f"Exception getting detected devices: {e}")
            return {
                "devices": [],
                "total_devices": 0,
                "source": "monitor_api",
                "error": str(e),
            }

    def get_port_statistics(self, switch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get port statistics for FortiSwitches.
        Optionally filter by switch_id.
        """
        try:
            # Build endpoint with optional filter
            endpoint = "monitor/switch-controller/managed-switch/port-stats"
            if switch_id:
                endpoint += f"?mkey={switch_id}"

            data = fgt_api(endpoint)

            if "error" in data:
                logger.error(f"API error getting port stats: {data}")
                return {
                    "port_stats": [],
                    "total_switches": 0,
                    "source": "monitor_api",
                    "error": data.get("error"),
                }

            # Process port statistics
            switch_stats = []
            total_ports = 0

            if "results" in data and isinstance(data["results"], list):
                for switch_data in data["results"]:
                    switch_serial = switch_data.get("serial", "")
                    switch_id_val = switch_data.get("switch-id", "")

                    port_stats = []
                    ports_data = switch_data.get("ports", {})

                    for port_name, stats in ports_data.items():
                        if isinstance(stats, dict):
                            # Calculate utilization score (simple metric based on traffic)
                            tx_bytes = stats.get("tx-bytes", 0)
                            rx_bytes = stats.get("rx-bytes", 0)
                            total_bytes = tx_bytes + rx_bytes

                            # Simple utilization score (could be enhanced)
                            utilization_score = min(
                                100, total_bytes / 1000000000
                            )  # GB scale

                            port_stat = {
                                "port_name": port_name,
                                "tx_bytes": tx_bytes,
                                "tx_packets": stats.get("tx-packets", 0),
                                "rx_bytes": rx_bytes,
                                "rx_packets": stats.get("rx-packets", 0),
                                "tx_errors": stats.get("tx-errors", 0),
                                "rx_errors": stats.get("rx-errors", 0),
                                "rx_drops": stats.get("rx-drops", 0),
                                "total_bytes": total_bytes,
                                "utilization_score": round(utilization_score, 2),
                                "health_status": (
                                    "good"
                                    if stats.get("tx-errors", 0) == 0
                                    and stats.get("rx-errors", 0) == 0
                                    else "warning"
                                ),
                            }
                            port_stats.append(port_stat)
                            total_ports += 1

                    switch_stat = {
                        "serial": switch_serial,
                        "switch_id": switch_id_val,
                        "port_count": len(port_stats),
                        "ports": port_stats,
                        "total_traffic": sum(p["total_bytes"] for p in port_stats),
                        "avg_utilization": (
                            round(
                                sum(p["utilization_score"] for p in port_stats)
                                / len(port_stats),
                                2,
                            )
                            if port_stats
                            else 0
                        ),
                    }
                    switch_stats.append(switch_stat)

            logger.info(
                f"Retrieved port statistics for {len(switch_stats)} switches, {total_ports} ports"
            )

            return {
                "port_stats": switch_stats,
                "total_switches": len(switch_stats),
                "total_ports": total_ports,
                "source": "monitor_api",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Exception getting port statistics: {e}")
            return {
                "port_stats": [],
                "total_switches": 0,
                "source": "monitor_api",
                "error": str(e),
            }

    def get_comprehensive_device_data(self) -> Dict[str, Any]:
        """
        Combine detected devices with port statistics for comprehensive view.
        """
        try:
            # Get both datasets
            devices_data = self.get_detected_devices()
            stats_data = self.get_port_statistics()

            # Create port statistics lookup
            port_stats_lookup = {}
            for switch in stats_data.get("port_stats", []):
                switch_id = switch.get("switch_id", "")
                for port in switch.get("ports", []):
                    key = f"{switch_id}:{port.get('port_name', '')}"
                    port_stats_lookup[key] = port

            # Enhance devices with port statistics
            enhanced_devices = []
            for device in devices_data.get("devices", []):
                enhanced_device = device.copy()

                # Add port statistics if available
                lookup_key = f"{device.get('switch_id')}:{device.get('port_name')}"
                if lookup_key in port_stats_lookup:
                    port_stats = port_stats_lookup[lookup_key]
                    enhanced_device["port_statistics"] = {
                        "tx_bytes": port_stats.get("tx_bytes", 0),
                        "rx_bytes": port_stats.get("rx_bytes", 0),
                        "total_bytes": port_stats.get("total_bytes", 0),
                        "utilization_score": port_stats.get("utilization_score", 0),
                        "health_status": port_stats.get("health_status", "unknown"),
                    }
                    enhanced_device["has_statistics"] = True
                else:
                    enhanced_device["has_statistics"] = False

                enhanced_devices.append(enhanced_device)

            return {
                "devices": enhanced_devices,
                "total_devices": len(enhanced_devices),
                "active_devices": devices_data.get("active_devices", 0),
                "source": "monitor_comprehensive",
                "timestamp": datetime.now().isoformat(),
                "statistics_coverage": len(
                    [d for d in enhanced_devices if d.get("has_statistics")]
                ),
                "api_info": devices_data.get("api_info", {}),
            }

        except Exception as e:
            logger.error(f"Exception getting comprehensive device data: {e}")
            return {
                "devices": [],
                "total_devices": 0,
                "source": "monitor_comprehensive",
                "error": str(e),
            }

    def _format_time_ago(self, seconds: int) -> str:
        """Format seconds into human-readable time ago"""
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"

    def get_device_by_mac(self, mac_address: str) -> Optional[Dict[str, Any]]:
        """Get specific device by MAC address"""
        devices_data = self.get_comprehensive_device_data()

        for device in devices_data.get("devices", []):
            if device.get("mac", "").lower() == mac_address.lower():
                return device

        return None

    def get_port_devices(self, switch_id: str, port_name: str) -> List[Dict[str, Any]]:
        """Get all devices connected to a specific port"""
        devices_data = self.get_comprehensive_device_data()

        port_devices = []
        for device in devices_data.get("devices", []):
            if (
                device.get("switch_id") == switch_id
                and device.get("port_name") == port_name
            ):
                port_devices.append(device)

        return port_devices


# Global instance
_fortigate_monitor_service = None


def get_fortigate_monitor_service() -> FortiGateMonitorService:
    """Get global FortiGate Monitor service instance"""
    global _fortigate_monitor_service
    if _fortigate_monitor_service is None:
        _fortigate_monitor_service = FortiGateMonitorService()
    return _fortigate_monitor_service
