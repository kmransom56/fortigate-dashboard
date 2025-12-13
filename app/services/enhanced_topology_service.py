"""
FortiGate Dashboard Integration Module
Provides API endpoints compatible with the FortiGate Dashboard (FastAPI) application.

This module integrates the FortiGate-Visio-Topology enhanced discovery with
the existing FortiGate Dashboard to provide 2D and 3D network visualizations.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fortigate_visio.fortigate_client import FortiGateClient
from src.fortigate_visio.enhanced_topology_service import EnhancedTopologyService
from src.fortigate_visio.models import Device, Link, TopologyData
from src.fortigate_visio.config import settings

# Import icon mapper
try:
    from icon_mapper import IconMapper
    ICON_MAPPER_AVAILABLE = True
except ImportError:
    ICON_MAPPER_AVAILABLE = False


class FortiGateDashboardIntegration:
    """Integration service for FortiGate Dashboard application."""

    def __init__(self):
        self.client = FortiGateClient()
        self.topology_service = EnhancedTopologyService()

    def get_topology_data_2d(self) -> Dict[str, Any]:
        """
        Get topology data formatted for D3.js 2D visualization.
        Compatible with the FortiGate Dashboard topology view.

        Returns:
            Dict with 'nodes' and 'links' arrays for D3.js force layout
        """
        try:
            # Fetch all discovery data
            devices = self.client.get_devices()
            lldp_neighbors = self.client.get_lldp_neighbors()
            lldp_ports = self.client.get_lldp_ports()
            managed_switches = self.client.get_managed_switches()
            managed_aps = self.client.get_managed_aps()
            wifi_clients = self.client.get_wifi_clients()
            arp_table = self.client.get_arp_table()

            # Build enhanced topology
            topology = self.topology_service.build_enhanced_topology(
                devices=devices,
                lldp_neighbors=lldp_neighbors,
                lldp_ports=lldp_ports,
                managed_switches=managed_switches,
                managed_aps=managed_aps,
                wifi_clients=wifi_clients,
                arp_table=arp_table
            )

            # Convert to D3.js format
            nodes = []
            for device in topology.devices:
                node = {
                    "id": device.device_id,
                    "name": device.hostname or device.device_id,
                    "type": self._map_device_type(device),
                    "ip": device.ip,
                    "mac": device.mac,
                    "vendor": device.vendor,
                    "os": device.os,
                    "interface": device.interface,
                    "role": device.role,
                    "status": "online" if device.is_online else "offline",
                    "icon": self._get_device_icon(device),
                    "group": self._get_device_group(device),
                    # Extended metadata
                    "hardware_family": device.hardware_family,
                    "hardware_type": device.hardware_type,
                    "fortiswitch_port": device.fortiswitch_port_name,
                    "fortiap_ssid": device.fortiap_ssid,
                    "is_infrastructure": device.hardware_family in ["FortiSwitch", "FortiAP", "FortiGate"]
                }
                nodes.append(node)

            # Convert links to D3.js format
            links = []
            for link in topology.links:
                d3_link = {
                    "source": link.from_device_id,
                    "target": link.to_device_id,
                    "type": link.link_type,
                    "label": link.link_label,
                    "from_interface": link.from_interface,
                    "to_interface": link.to_interface,
                    "strength": self._get_link_strength(link.link_type)
                }
                links.append(d3_link)

            return {
                "nodes": nodes,
                "links": links,
                "metadata": {
                    "device_count": len(nodes),
                    "link_count": len(links),
                    "timestamp": datetime.now().isoformat(),
                    "fortigate_host": settings.fortigate_host
                }
            }

        except Exception as e:
            raise Exception(f"Failed to get 2D topology data: {str(e)}")

    def get_topology_data_3d(self) -> Dict[str, Any]:
        """
        Get topology data formatted for 3D visualization (Babylon.js/Three.js).
        Compatible with the FortiGate Dashboard 3D topology view.

        Returns:
            Dict with nodes and links formatted for 3D force graph
        """
        try:
            # Get base 2D topology
            topology_2d = self.get_topology_data_2d()

            # Enhance with 3D-specific attributes
            nodes_3d = []
            for node in topology_2d["nodes"]:
                node_3d = node.copy()
                node_3d.update({
                    "color": self._get_3d_color(node["type"]),
                    "size": self._get_3d_size(node["type"], node["is_infrastructure"]),
                    "model": self._get_3d_model(node["type"], node["hardware_family"]),
                    "position": self._calculate_3d_position(node),
                    "label_offset": 2.0
                })
                nodes_3d.append(node_3d)

            # Enhance links with 3D attributes
            links_3d = []
            for link in topology_2d["links"]:
                link_3d = link.copy()
                link_3d.update({
                    "color": self._get_link_color_3d(link["type"]),
                    "width": self._get_link_width_3d(link["type"]),
                    "curvature": 0.3 if link["type"] == "L2-Wireless" else 0.1,
                    "particles": link["type"] == "Infrastructure"
                })
                links_3d.append(link_3d)

            return {
                "nodes": nodes_3d,
                "links": links_3d,
                "metadata": topology_2d["metadata"]
            }

        except Exception as e:
            raise Exception(f"Failed to get 3D topology data: {str(e)}")

    def get_hybrid_topology_data(self) -> Dict[str, Any]:
        """
        Get hybrid topology data with both device list and network structure.
        Compatible with the hybrid topology service pattern.

        Returns:
            Dict with devices, connections, and statistics
        """
        try:
            topology_2d = self.get_topology_data_2d()

            # Transform to hybrid format
            devices = []
            for node in topology_2d["nodes"]:
                device = {
                    "device_id": node["id"],
                    "hostname": node["name"],
                    "ip": node["ip"],
                    "mac": node["mac"],
                    "manufacturer": node["vendor"],
                    "device_type": node["type"],
                    "status": node["status"],
                    "interface": node["interface"],
                    "icon_path": node["icon"],
                    "icon_title": f"{node['vendor']} {node['role']}"
                }
                devices.append(device)

            return {
                "devices": devices,
                "connections": topology_2d["links"],
                "statistics": {
                    "total_devices": topology_2d["metadata"]["device_count"],
                    "total_connections": topology_2d["metadata"]["link_count"],
                    "fortigate_count": len([d for d in devices if d["device_type"] == "fortigate"]),
                    "fortiswitch_count": len([d for d in devices if d["device_type"] == "fortiswitch"]),
                    "fortiap_count": len([d for d in devices if d["device_type"] == "fortiap"]),
                    "endpoint_count": len([d for d in devices if d["device_type"] == "endpoint"]),
                    "timestamp": topology_2d["metadata"]["timestamp"]
                }
            }

        except Exception as e:
            raise Exception(f"Failed to get hybrid topology data: {str(e)}")

    # Helper methods

    def _map_device_type(self, device: Device) -> str:
        """Map device to dashboard device type."""
        if device.hardware_family == "FortiGate":
            return "fortigate"
        elif device.hardware_family == "FortiSwitch":
            return "fortiswitch"
        elif device.hardware_family == "FortiAP":
            return "fortiap"
        elif device.role in ["Server", "server"]:
            return "server"
        else:
            return "endpoint"

    def _get_device_icon(self, device: Device) -> str:
        """Get icon path for device using enhanced icon mapper."""
        if ICON_MAPPER_AVAILABLE:
            # Convert Device to dict for icon mapper
            device_dict = {
                'hardware_family': device.hardware_family,
                'hardware_type': device.hardware_type,
                'vendor': device.vendor,
                'os': device.os,
                'role': device.role,
                'hostname': device.hostname
            }
            return IconMapper.get_icon_for_device(device_dict)

        # Fallback to simple mapping
        icon_map = {
            "FortiGate": "icons/FG-100F_101F.svg",
            "FortiSwitch": "icons/FSW-124E.svg",
            "FortiAP": "icons/FAP-221_223E.svg"
        }

        if device.hardware_family in icon_map:
            return icon_map[device.hardware_family]

        # Vendor-specific icons
        vendor_map = {
            "Apple": "icons/apple.svg",
            "Microsoft": "icons/microsoft.svg",
            "Dell": "icons/Dell.svg",
            "HP": "icons/hp.svg",
            "Cisco": "icons/cisco.svg"
        }

        for vendor_key, icon_path in vendor_map.items():
            if vendor_key.lower() in device.vendor.lower():
                return icon_path

        return "icons/Application.svg"

    def _get_device_group(self, device: Device) -> int:
        """Get D3.js group number for device coloring."""
        group_map = {
            "FortiGate": 1,
            "FortiSwitch": 2,
            "FortiAP": 3,
        }
        return group_map.get(device.hardware_family, 4)

    def _get_link_strength(self, link_type: str) -> float:
        """Get link strength for D3.js force layout."""
        strength_map = {
            "Infrastructure": 1.5,
            "L2-Wired": 1.0,
            "L2-Wireless": 0.7,
            "L3": 1.2
        }
        return strength_map.get(link_type, 1.0)

    def _get_3d_color(self, device_type: str) -> str:
        """Get color for 3D node."""
        color_map = {
            "fortigate": "#ff4444",
            "fortiswitch": "#4444ff",
            "fortiap": "#44ff44",
            "server": "#ff44ff",
            "endpoint": "#cccccc"
        }
        return color_map.get(device_type, "#aaaaaa")

    def _get_3d_size(self, device_type: str, is_infrastructure: bool) -> float:
        """Get size for 3D node."""
        if is_infrastructure:
            return 15.0 if device_type == "fortigate" else 10.0
        return 5.0

    def _get_3d_model(self, device_type: str, hardware_family: str) -> str:
        """Get 3D model path for device."""
        model_map = {
            "FortiGate": "models/fortigate-100f.glb",
            "FortiSwitch": "models/fortiswitch-124e.glb",
            "FortiAP": "models/fortiap-221e.glb"
        }
        return model_map.get(hardware_family, "models/generic-device.glb")

    def _calculate_3d_position(self, node: Dict) -> Dict[str, float]:
        """Calculate initial 3D position for node."""
        # Simple layout based on device type
        group = node["group"]
        return {
            "x": (group - 2) * 50,
            "y": 0,
            "z": 0
        }

    def _get_link_color_3d(self, link_type: str) -> str:
        """Get color for 3D link."""
        color_map = {
            "Infrastructure": "#ff9800",
            "L2-Wired": "#2196f3",
            "L2-Wireless": "#4caf50",
            "L3": "#9c27b0"
        }
        return color_map.get(link_type, "#999999")

    def _get_link_width_3d(self, link_type: str) -> float:
        """Get width for 3D link."""
        width_map = {
            "Infrastructure": 2.0,
            "L2-Wired": 1.5,
            "L2-Wireless": 1.0,
            "L3": 1.8
        }
        return width_map.get(link_type, 1.0)


# Convenience functions for direct import
def get_2d_topology() -> Dict[str, Any]:
    """Get 2D topology data for D3.js visualization."""
    integration = FortiGateDashboardIntegration()
    return integration.get_topology_data_2d()


def get_3d_topology() -> Dict[str, Any]:
    """Get 3D topology data for Babylon.js/Three.js visualization."""
    integration = FortiGateDashboardIntegration()
    return integration.get_topology_data_3d()


def get_hybrid_topology() -> Dict[str, Any]:
    """Get hybrid topology data for combined views."""
    integration = FortiGateDashboardIntegration()
    return integration.get_hybrid_topology_data()
