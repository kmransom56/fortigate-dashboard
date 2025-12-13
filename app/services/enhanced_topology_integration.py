"""
Enhanced Topology Integration Service
Uses REAL FortiGate API data polling with LLDP discovery
Based on fortigate-visio-topology/src/fortigate_visio/enhanced_topology_service.py
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedTopologyIntegration:
    """Service for enhanced topology discovery using real FortiGate data."""

    def __init__(self):
        """Initialize the enhanced topology service with real data polling."""
        # Import icon mapper
        try:
            from app.services.icon_mapper import IconMapper
            self.icon_mapper = IconMapper()
            logger.info("Icon mapper initialized successfully")
        except ImportError as e:
            logger.warning(f"Icon mapper not available: {e}")
            self.icon_mapper = None

        # Import FortiGate polling client
        try:
            from app.services.fortigate_polling_client import get_fortigate_polling_client
            self.polling_client = get_fortigate_polling_client()
            logger.info("FortiGate polling client initialized successfully")
        except ImportError as e:
            logger.warning(f"FortiGate polling client not available: {e}")
            self.polling_client = None

    def get_device_icon(self, device: Dict[str, Any]) -> str:
        """
        Get the appropriate icon path for a device using the advanced icon mapper.

        Args:
            device: Device dictionary with hardware/vendor information

        Returns:
            Icon path relative to /static/
        """
        if self.icon_mapper:
            icon_path = self.icon_mapper.get_icon_for_device(device)
            # Ensure path starts with /static/
            if not icon_path.startswith('/static/'):
                icon_path = f"/static/{icon_path}"
            return icon_path

        # Fallback to basic icon mapping
        device_type = device.get('type', 'unknown').lower()
        if 'fortigate' in device_type:
            return '/static/icons/fortinet/fortigate/default.svg'
        elif 'fortiswitch' in device_type:
            return '/static/icons/fortinet/fortiswitch/default.svg'
        elif 'fortiap' in device_type:
            return '/static/icons/fortinet/fortiap/default.svg'
        return '/static/icons/Application.svg'

    def enhance_topology_data(self, topology_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance existing topology data with better icons and metadata.

        Args:
            topology_data: Raw topology data

        Returns:
            Enhanced topology data with improved icons and device classification
        """
        if not topology_data.get('devices'):
            return topology_data

        enhanced_devices = []
        for device in topology_data['devices']:
            enhanced_device = device.copy()

            # Get better icon using icon mapper
            enhanced_device['icon'] = self.get_device_icon(device)

            # Add infrastructure classification
            enhanced_device['is_infrastructure'] = self._is_infrastructure_device(device)

            enhanced_devices.append(enhanced_device)

        topology_data['devices'] = enhanced_devices
        topology_data['enhanced'] = True
        topology_data['enhancement_timestamp'] = datetime.now().isoformat()

        return topology_data

    def _is_infrastructure_device(self, device: Dict[str, Any]) -> bool:
        """Determine if a device is infrastructure (vs endpoint)."""
        device_type = device.get('type', '').lower()
        name = device.get('name', '').lower()
        hardware_family = device.get('hardware_family', '').lower()

        infrastructure_keywords = [
            'fortigate', 'fortiswitch', 'fortiap',
            'switch', 'router', 'firewall', 'ap', 'access point'
        ]

        return (any(keyword in device_type or keyword in name or keyword in hardware_family
                   for keyword in infrastructure_keywords))

    def get_topology_with_lldp(self) -> Dict[str, Any]:
        """
        Get topology data with REAL LLDP discovery from FortiGate API.

        Returns:
            Topology data with LLDP-discovered physical connections
        """
        if not self.polling_client:
            logger.error("FortiGate polling client not available")
            return {"devices": [], "connections": [], "error": "Polling client not available"}

        try:
            # Get all topology data from FortiGate
            logger.info("Fetching real topology data from FortiGate API...")
            raw_data = self.polling_client.get_all_topology_data()

            # Build enhanced topology from real data
            topology = self._build_enhanced_topology(
                devices=raw_data.get('devices', []),
                lldp_neighbors=raw_data.get('lldp_neighbors', []),
                lldp_ports=raw_data.get('lldp_ports', []),
                managed_switches=raw_data.get('managed_switches', []),
                managed_aps=raw_data.get('managed_aps', []),
                wifi_clients=raw_data.get('wifi_clients', []),
                arp_table=raw_data.get('arp_table', [])
            )

            logger.info(f"Built topology with {len(topology['devices'])} devices and {len(topology['connections'])} connections")
            return topology

        except Exception as e:
            logger.error(f"Error getting LLDP topology: {e}", exc_info=True)
            return {"devices": [], "connections": [], "error": str(e)}

    def _build_enhanced_topology(
        self,
        devices: List[Dict[str, Any]],
        lldp_neighbors: List[Dict[str, Any]],
        lldp_ports: List[Dict[str, Any]],
        managed_switches: List[Dict[str, Any]],
        managed_aps: List[Dict[str, Any]],
        wifi_clients: List[Dict[str, Any]],
        arp_table: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build comprehensive topology from real FortiGate data."""

        all_devices = []
        all_connections = []

        # Add FortiGate as root device
        fortigate_device = {
            "id": "fortigate-primary",
            "name": "FortiGate",
            "type": "fortigate",
            "hardware_family": "FortiGate",
            "vendor": "Fortinet",
            "position": {"x": 400, "y": 100},
            "icon": self.get_device_icon({"hardware_family": "FortiGate"})
        }
        all_devices.append(fortigate_device)

        # Add managed switches
        for idx, switch in enumerate(managed_switches):
            switch_id = f"switch-{switch.get('serial', idx)}"
            switch_device = {
                "id": switch_id,
                "name": switch.get('switch-id', f"Switch-{idx}"),
                "type": "fortiswitch",
                "hardware_family": "FortiSwitch",
                "vendor": "Fortinet",
                "serial": switch.get('serial'),
                "status": switch.get('status'),
                "position": {"x": 200 + (idx * 150), "y": 300},
                "icon": self.get_device_icon({"hardware_family": "FortiSwitch"})
            }
            all_devices.append(switch_device)

            # Add connection to FortiGate
            all_connections.append({
                "source": "fortigate-primary",
                "target": switch_id,
                "type": "fortilink",
                "interface": switch.get('fgt_peer_intf_name', 'fortilink')
            })

        # Add managed APs
        for idx, ap in enumerate(managed_aps):
            ap_id = f"ap-{ap.get('serial', idx)}"
            ap_device = {
                "id": ap_id,
                "name": ap.get('name', f"AP-{idx}"),
                "type": "fortiap",
                "hardware_family": "FortiAP",
                "vendor": "Fortinet",
                "serial": ap.get('serial'),
                "status": ap.get('status'),
                "position": {"x": 600 + (idx * 150), "y": 300},
                "icon": self.get_device_icon({"hardware_family": "FortiAP"})
            }
            all_devices.append(ap_device)

            # Add connection to FortiGate (usually wireless or dedicated port)
            all_connections.append({
                "source": "fortigate-primary",
                "target": ap_id,
                "type": "physical",
                "interface": "wireless"
            })

        # Add LLDP-discovered devices
        for idx, neighbor in enumerate(lldp_neighbors):
            neighbor_id = f"lldp-{idx}"
            neighbor_device = {
                "id": neighbor_id,
                "name": neighbor.get('system_name', f"Device-{idx}"),
                "type": "network_device",
                "vendor": neighbor.get('chassis_id', 'Unknown'),
                "position": {"x": 400 + (idx * 100), "y": 500},
                "icon": self.get_device_icon({"type": "network_device"})
            }
            all_devices.append(neighbor_device)

            # Add LLDP connection
            all_connections.append({
                "source": "fortigate-primary",
                "target": neighbor_id,
                "type": "lldp",
                "interface": neighbor.get('port_name', 'unknown')
            })

        # Add WiFi clients
        for idx, client in enumerate(wifi_clients):
            client_mac = client.get('mac', '').replace(':', '')
            client_id = f"wifi-{client_mac or idx}"
            client_device = {
                "id": client_id,
                "name": client.get('hostname', client.get('mac', f"WiFi-Client-{idx}")),
                "type": "wifi_client",
                "vendor": client.get('manufacturer', 'Unknown'),
                "mac": client.get('mac'),
                "ssid": client.get('ssid'),
                "position": {"x": 700 + (idx * 50), "y": 500},
                "icon": self.get_device_icon({"type": "mobile", "vendor": client.get('manufacturer', '')})
            }
            all_devices.append(client_device)

            # Find parent AP
            ap_id = f"ap-{client.get('wtp_id', '')}"
            if any(dev['id'] == ap_id for dev in all_devices):
                all_connections.append({
                    "source": ap_id,
                    "target": client_id,
                    "type": "wifi",
                    "ssid": client.get('ssid', 'unknown')
                })

        # Add remaining devices
        for idx, device in enumerate(devices):
            if not device.get('mac'):
                continue

            device_id = device.get('device_id', f"device-{idx}")

            # Skip if already added
            if any(dev['id'] == device_id for dev in all_devices):
                continue

            device_entry = {
                "id": device_id,
                "name": device.get('hostname', device.get('mac')),
                "type": device.get('role', 'unknown'),
                "vendor": device.get('vendor', 'Unknown'),
                "mac": device.get('mac'),
                "ip": device.get('ip'),
                "hardware_family": device.get('hardware_family', ''),
                "position": {"x": 100 + (idx * 80), "y": 600},
                "icon": self.get_device_icon(device)
            }
            all_devices.append(device_entry)

            # Add connection based on interface
            if device.get('is_fortiswitch_client'):
                # Connected via FortiSwitch
                switch_id = f"switch-{device.get('fortiswitch_serial', '')}"
                if any(dev['id'] == switch_id for dev in all_devices):
                    all_connections.append({
                        "source": switch_id,
                        "target": device_id,
                        "type": "ethernet",
                        "port": device.get('fortiswitch_port_name', 'unknown')
                    })
            elif device.get('interface'):
                # Direct connection to FortiGate
                all_connections.append({
                    "source": "fortigate-primary",
                    "target": device_id,
                    "type": "ethernet",
                    "interface": device.get('interface')
                })

        return {
            "devices": all_devices,
            "connections": all_connections,
            "metadata": {
                "source": "fortigate_api_polling",
                "timestamp": datetime.now().isoformat(),
                "device_count": len(all_devices),
                "connection_count": len(all_connections),
                "lldp_enabled": len(lldp_neighbors) > 0,
                "switches_count": len(managed_switches),
                "aps_count": len(managed_aps),
                "wifi_clients_count": len(wifi_clients)
            }
        }

    def get_fortiswitch_port_details(self) -> Dict[str, Any]:
        """
        Get FortiSwitch port-level client tracking with REAL data.

        Returns:
            Port-level device associations from FortiGate API
        """
        if not self.polling_client:
            logger.error("FortiGate polling client not available")
            return {"error": "Polling client not available"}

        try:
            switches = self.polling_client.get_managed_switches()
            devices = self.polling_client.get_devices()

            ports = []
            for switch in switches:
                switch_ports = switch.get('ports', [])
                for port in switch_ports:
                    # Find devices connected to this port
                    connected_devices = [
                        dev for dev in devices
                        if dev.get('fortiswitch_serial') == switch.get('serial')
                        and dev.get('fortiswitch_port_name') == port.get('interface')
                    ]

                    ports.append({
                        "switch_id": switch.get('serial'),
                        "switch_name": switch.get('switch-id'),
                        "port_name": port.get('interface'),
                        "status": port.get('status'),
                        "vlan": port.get('vlan'),
                        "speed": port.get('speed'),
                        "connected_devices": connected_devices
                    })

            return {
                "switches": switches,
                "ports": ports,
                "feature": "fortiswitch_port_tracking",
                "status": "active"
            }

        except Exception as e:
            logger.error(f"Error getting FortiSwitch port details: {e}")
            return {"error": str(e)}

    def get_fortiap_client_associations(self) -> Dict[str, Any]:
        """
        Get FortiAP WiFi client associations with REAL data.

        Returns:
            WiFi client associations by SSID from FortiGate API
        """
        if not self.polling_client:
            logger.error("FortiGate polling client not available")
            return {"error": "Polling client not available"}

        try:
            aps = self.polling_client.get_managed_aps()
            clients = self.polling_client.get_wifi_clients()

            # Group clients by AP and SSID
            associations = {}
            for client in clients:
                ap_id = client.get('wtp_id', 'unknown')
                ssid = client.get('ssid', 'unknown')

                key = f"{ap_id}:{ssid}"
                if key not in associations:
                    associations[key] = {
                        "ap_id": ap_id,
                        "ap_name": next((ap.get('name') for ap in aps if ap.get('serial') == ap_id), ap_id),
                        "ssid": ssid,
                        "clients": []
                    }

                associations[key]['clients'].append({
                    "mac": client.get('mac'),
                    "hostname": client.get('hostname'),
                    "ip": client.get('ip'),
                    "signal": client.get('signal'),
                    "data_rate": client.get('data_rate_bps')
                })

            return {
                "access_points": aps,
                "ssids": list(set(c.get('ssid') for c in clients if c.get('ssid'))),
                "associations": list(associations.values()),
                "total_clients": len(clients),
                "feature": "fortiap_client_tracking",
                "status": "active"
            }

        except Exception as e:
            logger.error(f"Error getting FortiAP client associations: {e}")
            return {"error": str(e)}


# Singleton instance
_enhanced_topology_service = None

def get_enhanced_topology_service() -> EnhancedTopologyIntegration:
    """Get or create the enhanced topology service singleton."""
    global _enhanced_topology_service
    if _enhanced_topology_service is None:
        _enhanced_topology_service = EnhancedTopologyIntegration()
    return _enhanced_topology_service
