from bs4 import BeautifulSoup
import json
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ScrapedTopologyService:
    """Service for parsing scraped FortiGate topology HTML data"""

    def __init__(self, scraped_html_path: str = None):
        """Initialize with optional custom HTML file path"""
        self.scraped_html_path = scraped_html_path or self._find_scraped_html()

    def _find_scraped_html(self) -> str:
        """Find scraped HTML file in various possible locations"""
        possible_paths = [
            "scraped_map.html",
            "../../scraped_map.html",
            "assets/scraped_map.html",
            "app/static/scraped_map.html",
            "static/scraped_map.html",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found scraped HTML at: {path}")
                return path

        logger.warning("No scraped HTML file found, will use real API data")
        return None

    def get_topology_data(self) -> Dict[str, Any]:
        """Get topology data from scraped HTML or real API data"""
        if self.scraped_html_path and os.path.exists(self.scraped_html_path):
            try:
                return self._parse_scraped_html()
            except Exception as e:
                logger.error(f"Failed to parse scraped HTML: {e}")

        # No scraped HTML available - use real API data instead
        logger.info("No scraped HTML found, fetching from real API")
        return self._get_real_api_data()

    def _parse_scraped_html(self) -> Dict[str, Any]:
        """Parse actual scraped HTML content"""
        with open(self.scraped_html_path, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")
        devices = []
        connections = []

        # Enhanced device parsing with multiple selectors
        device_selectors = [".device-node", ".topology-node", ".node", ".device"]

        for selector in device_selectors:
            device_elements = soup.select(selector)
            if device_elements:
                logger.info(
                    f"Found {len(device_elements)} devices using selector: {selector}"
                )
                break

        for i, device in enumerate(device_elements):
            device_data = self._extract_device_data(device, i)
            if device_data:
                devices.append(device_data)

        # Enhanced connection parsing
        connection_selectors = [
            ".connection-link",
            ".topology-link",
            ".link",
            ".connection",
        ]

        for selector in connection_selectors:
            connection_elements = soup.select(selector)
            if connection_elements:
                logger.info(
                    f"Found {len(connection_elements)} connections using selector: {selector}"
                )
                break

        for conn in connection_elements:
            connection_data = self._extract_connection_data(conn)
            if connection_data:
                connections.append(connection_data)

        return {
            "devices": devices,
            "connections": connections,
            "metadata": {
                "source": "scraped",
                "timestamp": self._get_file_timestamp(),
                "device_count": len(devices),
                "connection_count": len(connections),
            },
        }

    def _extract_device_data(
        self, device_element, index: int
    ) -> Optional[Dict[str, Any]]:
        """Extract device data from HTML element"""
        try:
            device_id = (
                device_element.get("id")
                or device_element.get("data-id")
                or f"device_{index}"
            )
            device_type = (
                device_element.get("data-type")
                or device_element.get("class", [None])[0]
                or "endpoint"
            ).lower()

            # Clean device type
            if "fortigate" in device_type:
                device_type = "fortigate"
            elif "switch" in device_type:
                device_type = "fortiswitch"
            elif "server" in device_type:
                device_type = "server"
            else:
                device_type = "endpoint"

            # Extract position
            x_pos = int(
                device_element.get("data-x")
                or device_element.get("x")
                or 100 + index * 200
            )
            y_pos = int(
                device_element.get("data-y")
                or device_element.get("y")
                or 100 + index * 150
            )

            # Extract device count
            device_count = int(device_element.get("data-count") or 1)

            # Get device name
            name = (
                device_element.get("data-name")
                or device_element.get_text(strip=True)
                or f"{device_type.title()} {index + 1}"
            )

            # Color mapping
            color_map = {
                "fortigate": "#2196f3",
                "fortiswitch": "#ff9800",
                "endpoint": "#4caf50",
                "server": "#9c27b0",
            }

            return {
                "id": device_id,
                "type": device_type,
                "name": name,
                "position": {"x": x_pos, "y": y_pos},
                "details": {
                    "deviceCount": device_count,
                    "color": color_map.get(device_type, "#2196f3"),
                    "status": device_element.get("data-status", "online"),
                    "manufacturer": (
                        "Fortinet" if device_type.startswith("forti") else "Generic"
                    ),
                },
            }
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to extract device data from element {index}: {e}")
            return None

    def _extract_connection_data(self, conn_element) -> Optional[Dict[str, Any]]:
        """Extract connection data from HTML element"""
        try:
            from_id = conn_element.get("data-from") or conn_element.get("from")
            to_id = conn_element.get("data-to") or conn_element.get("to")

            if not from_id or not to_id:
                return None

            return {
                "from": from_id,
                "to": to_id,
                "type": conn_element.get("data-type", "ethernet"),
                "status": conn_element.get("data-status", "active"),
            }
        except Exception as e:
            logger.warning(f"Failed to extract connection data: {e}")
            return None

    def _get_file_timestamp(self) -> str:
        """Get scraped file timestamp"""
        try:
            if self.scraped_html_path and os.path.exists(self.scraped_html_path):
                mtime = os.path.getmtime(self.scraped_html_path)
                return str(mtime)
        except Exception:
            pass
        return "unknown"

    def _get_real_api_data(self) -> Dict[str, Any]:
        """Get topology data from real API services including ARP table and detected devices"""
        try:
            from app.services.hybrid_topology_service import get_hybrid_topology_service
            from app.services.fortigate_service import fgt_api
            from app.services.fortigate_monitor_service import FortiGateMonitorService
            from app.utils.oui_lookup import get_manufacturer_from_mac

            hybrid_service = get_hybrid_topology_service()
            switches_data = hybrid_service.get_comprehensive_topology()

            # Get interfaces if available (optional - don't fail if unavailable)
            interfaces = {}
            try:
                from app.services.fortigate_service import get_interfaces

                interfaces = get_interfaces() or {}
            except Exception as e:
                logger.warning(f"Could not get interfaces: {e}")
                interfaces = {}

            # Transform API data to topology format
            devices = []
            connections = []

            # Get ARP table data for all connected devices
            # Note: CMDB ARP table only has static entries. For dynamic ARP cache,
            # we rely on detected devices and MAC address tables from switches
            arp_devices = {}
            try:
                # Try CMDB ARP table (static entries only)
                arp_data = fgt_api("cmdb/system/arp-table")
                if arp_data and "results" in arp_data:
                    logger.info(
                        f"Processing {len(arp_data['results'])} static ARP entries"
                    )
                    for idx, arp_entry in enumerate(arp_data["results"]):
                        ip = arp_entry.get("ip", "")
                        mac = arp_entry.get("mac", "").upper()
                        interface = arp_entry.get("interface", "")

                        # Skip invalid entries
                        if not ip or not mac or mac == "00:00:00:00:00:00":
                            continue

                        # Get manufacturer from MAC
                        manufacturer = "Unknown"
                        try:
                            manufacturer = get_manufacturer_from_mac(mac)
                        except Exception:
                            pass

                        # Create device ID from IP
                        device_id = f"device_{ip.replace('.', '_')}"

                        # Determine device type based on interface and IP
                        device_type = "endpoint"
                        if "fortilink" in interface.lower():
                            device_type = "fortiswitch"
                        elif "wan" in interface.lower():
                            device_type = "router"
                        elif (
                            "internal" in interface.lower()
                            or "local" in interface.lower()
                        ):
                            device_type = "endpoint"

                        arp_devices[device_id] = {
                            "id": device_id,
                            "type": device_type,
                            "name": (
                                f"{manufacturer} ({ip})"
                                if manufacturer != "Unknown"
                                else ip
                            ),
                            "ip": ip,
                            "mac": mac,
                            "interface": interface,
                            "manufacturer": manufacturer,
                            "position": {
                                "x": 100 + (idx % 5) * 150,
                                "y": 400 + (idx // 5) * 120,
                            },
                            "status": "online",
                            "risk": "low",
                            "details": {
                                "deviceCount": 1,
                                "color": (
                                    "#4caf50"
                                    if device_type == "endpoint"
                                    else "#9c27b0"
                                ),
                                "status": "online",
                                "manufacturer": manufacturer,
                            },
                        }
                    logger.info(
                        f"Added {len(arp_devices)} devices from static ARP table"
                    )
            except Exception as e:
                logger.warning(f"Could not get ARP table: {e}")

            # Get DHCP lease list for IP-to-MAC mappings
            dhcp_leases = {}
            try:
                # Use FortiSwitch Monitor API for DHCP lease list
                dhcp_data = fgt_api("system/dhcp-lease-list/")
                if dhcp_data and "results" in dhcp_data:
                    logger.info(
                        f"Processing {len(dhcp_data['results'])} DHCP lease entries"
                    )
                    for lease in dhcp_data["results"]:
                        ip = lease.get("ip", "")
                        mac = lease.get("mac", "").upper()
                        hostname = lease.get("hostname", "")
                        if ip and mac and mac != "00:00:00:00:00:00":
                            dhcp_leases[mac] = {
                                "ip": ip,
                                "hostname": hostname,
                                "lease_time": lease.get("lease_time", ""),
                            }
                    logger.info(f"Loaded {len(dhcp_leases)} DHCP lease mappings")
            except Exception as e:
                logger.warning(f"Could not get DHCP lease list: {e}")

            # Get MAC address table from switches for additional device discovery
            mac_address_devices = {}
            try:
                # Use FortiSwitch Monitor API for MAC address table
                # Note: This endpoint is for FortiSwitch direct API, may need switch ID
                mac_data = fgt_api("switch/mac-address/")
                if mac_data and "results" in mac_data:
                    logger.info(
                        f"Processing {len(mac_data['results'])} MAC address entries"
                    )
                    for switch_entry in mac_data["results"]:
                        if isinstance(switch_entry, dict):
                            switch_id = switch_entry.get("switch_id", "")
                            entries = switch_entry.get("entries", [])
                            for entry in entries:
                                mac = entry.get("mac", "").upper()
                                port = entry.get("port", "")
                                vlan = entry.get("vlan", "")
                                if not mac or mac == "00:00:00:00:00:00":
                                    continue

                                # Get manufacturer from MAC
                                manufacturer = "Unknown"
                                try:
                                    manufacturer = get_manufacturer_from_mac(mac)
                                except Exception:
                                    pass

                                # Create device ID from MAC
                                device_id = f"mac_{mac.replace(':', '_')}"

                                # Get IP from DHCP lease if available
                                dhcp_info = dhcp_leases.get(mac, {})
                                ip_address = dhcp_info.get("ip", "Unknown")
                                hostname = dhcp_info.get("hostname", "")

                                # Only add if not already in ARP devices
                                if device_id not in arp_devices:
                                    device_name = (
                                        hostname
                                        if hostname
                                        else (
                                            f"{manufacturer} ({ip_address})"
                                            if manufacturer != "Unknown"
                                            and ip_address != "Unknown"
                                            else f"Device {mac[:8]}"
                                        )
                                    )
                                    mac_address_devices[device_id] = {
                                        "id": device_id,
                                        "type": "endpoint",
                                        "name": device_name,
                                        "ip": ip_address,
                                        "mac": mac,
                                        "interface": port,
                                        "switch_id": switch_id,
                                        "vlan": vlan,
                                        "position": {
                                            "x": 100
                                            + (
                                                len(arp_devices)
                                                + len(mac_address_devices)
                                            )
                                            % 5
                                            * 150,
                                            "y": 400
                                            + (
                                                (
                                                    len(arp_devices)
                                                    + len(mac_address_devices)
                                                )
                                                // 5
                                            )
                                            * 120,
                                        },
                                        "status": "online",
                                        "risk": "low",
                                        "details": {
                                            "deviceCount": 1,
                                            "color": "#4caf50",
                                            "status": "online",
                                            "manufacturer": manufacturer,
                                            "port": port,
                                            "switch": switch_id,
                                        },
                                    }
                    logger.info(
                        f"Added {len(mac_address_devices)} devices from MAC address table"
                    )
            except Exception as e:
                logger.warning(f"Could not get MAC address table: {e}")

            # Get detected devices from monitor service
            detected_devices_map = {}
            try:
                monitor_service = FortiGateMonitorService()
                detected_data = monitor_service.get_detected_devices()
                if detected_data and "devices" in detected_data:
                    logger.info(
                        f"Processing {len(detected_data['devices'])} detected devices"
                    )
                    for idx, detected in enumerate(detected_data["devices"]):
                        mac = detected.get("mac", "").upper()
                        ip = detected.get("ip", "")
                        if not mac:
                            continue

                        # Try to match with ARP entry
                        device_id = None
                        for aid, adev in arp_devices.items():
                            if adev.get("mac") == mac:
                                device_id = aid
                                # Enhance ARP device with detected device info
                                arp_devices[aid]["details"]["port"] = detected.get(
                                    "port_name", ""
                                )
                                arp_devices[aid]["details"]["switch"] = detected.get(
                                    "switch_id", ""
                                )
                                break

                        # If not in ARP, create new device
                        if not device_id:
                            device_id = f"detected_{mac.replace(':', '_')}"
                            detected_devices_map[device_id] = {
                                "id": device_id,
                                "type": "endpoint",
                                "name": f"{detected.get('manufacturer', 'Device')} ({mac[:8]})",
                                "ip": ip or "Unknown",
                                "mac": mac,
                                "position": {
                                    "x": 100 + (len(arp_devices) + idx) % 5 * 150,
                                    "y": 400 + ((len(arp_devices) + idx) // 5) * 120,
                                },
                                "status": (
                                    "online" if detected.get("is_active") else "warning"
                                ),
                                "risk": "low",
                                "details": {
                                    "deviceCount": 1,
                                    "color": "#4caf50",
                                    "status": "online",
                                    "manufacturer": detected.get(
                                        "manufacturer", "Unknown"
                                    ),
                                    "port": detected.get("port_name", ""),
                                    "switch": detected.get("switch_id", ""),
                                },
                            }
                    logger.info(
                        f"Added {len(detected_devices_map)} additional detected devices"
                    )
            except Exception as e:
                logger.warning(f"Could not get detected devices: {e}")

            # Add FortiGate device
            fortigate_host = os.getenv("FORTIGATE_HOST", "192.168.0.254")
            fortigate_name = os.getenv("FORTIGATE_NAME", "FortiGate-Main")
            devices.append(
                {
                    "id": "fortigate_main",
                    "type": "fortigate",
                    "name": fortigate_name,
                    "ip": fortigate_host.replace("https://", "")
                    .replace("http://", "")
                    .split(":")[0],
                    "position": {"x": 400, "y": 100},
                    "status": "online",
                    "risk": "low",
                    "details": {
                        "deviceCount": 1,
                        "color": "#2196f3",
                        "status": "online",
                        "manufacturer": "Fortinet",
                    },
                }
            )

            # Add switches from API data
            if switches_data and switches_data.get("switches"):
                for idx, switch in enumerate(switches_data["switches"]):
                    switch_id = switch.get("serial", f"switch_{idx}")
                    devices.append(
                        {
                            "id": switch_id,
                            "type": "fortiswitch",
                            "name": switch.get("name", f"FortiSwitch {idx + 1}"),
                            "ip": switch.get("ip", ""),
                            "position": {"x": 300 + (idx % 3) * 200, "y": 300},
                            "status": (
                                "online" if switch.get("status") == "up" else "warning"
                            ),
                            "risk": "low",
                            "details": {
                                "deviceCount": (
                                    switch.get("total_connected_devices")
                                    or switch.get("connected_devices_count")
                                    or 0
                                ),
                                "color": "#ff9800",
                                "status": switch.get("status", "unknown"),
                                "manufacturer": "Fortinet",
                                "model": switch.get("model", ""),
                            },
                        }
                    )
                    # Connect switch to FortiGate
                    connections.append(
                        {
                            "from": "fortigate_main",
                            "to": switch_id,
                            "type": "ethernet",
                            "status": "active",
                        }
                    )

                    # Connect ARP devices to their switch if they're on switch ports
                    for device_id, device_data in arp_devices.items():
                        interface = device_data.get("interface", "")
                        # If device is on a switch port, connect it to the switch
                        if switch_id and interface and "port" in interface.lower():
                            connections.append(
                                {
                                    "from": switch_id,
                                    "to": device_id,
                                    "type": "ethernet",
                                    "status": "active",
                                }
                            )
                        # Otherwise connect directly to FortiGate
                        elif not any(c.get("to") == device_id for c in connections):
                            connections.append(
                                {
                                    "from": "fortigate_main",
                                    "to": device_id,
                                    "type": "ethernet",
                                    "status": "active",
                                }
                            )

            # Add all ARP devices to devices list
            devices.extend(arp_devices.values())

            # Add MAC address table devices that weren't in ARP
            devices.extend(mac_address_devices.values())

            # Add detected devices that weren't in ARP or MAC table
            devices.extend(detected_devices_map.values())

            # Connect detected devices to their switches
            for device_id, device_data in detected_devices_map.items():
                switch_id = device_data.get("details", {}).get("switch", "")
                if switch_id:
                    # Find matching switch in devices
                    for switch in devices:
                        if (
                            switch.get("id") == switch_id
                            or switch.get("serial") == switch_id
                        ):
                            connections.append(
                                {
                                    "from": switch["id"],
                                    "to": device_id,
                                    "type": "ethernet",
                                    "status": "active",
                                }
                            )
                            break
                else:
                    # Connect to FortiGate if no switch
                    connections.append(
                        {
                            "from": "fortigate_main",
                            "to": device_id,
                            "type": "ethernet",
                            "status": "active",
                        }
                    )

            logger.info(
                f"Total devices in topology: {len(devices)} (FortiGate: 1, Switches: {len(switches_data.get('switches', [])) if switches_data else 0}, ARP: {len(arp_devices)}, MAC Table: {len(mac_address_devices)}, Detected: {len(detected_devices_map)})"
            )

            return {
                "devices": devices,
                "connections": connections,
                "metadata": {
                    "source": "api",
                    "timestamp": str(
                        os.path.getmtime(__file__)
                        if os.path.exists(__file__)
                        else "unknown"
                    ),
                    "device_count": len(devices),
                    "connection_count": len(connections),
                    "switches_count": (
                        len(switches_data.get("switches", [])) if switches_data else 0
                    ),
                    "arp_devices_count": len(arp_devices),
                    "mac_table_devices_count": len(mac_address_devices),
                    "detected_devices_count": len(detected_devices_map),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get real API data: {e}")
            # Return empty data structure - no mock data per AGENTS.md
            return {
                "devices": [],
                "connections": [],
                "metadata": {
                    "source": "error",
                    "error": str(e),
                    "device_count": 0,
                    "connection_count": 0,
                },
            }


# Service instance
_scraped_topology_service = None


def get_scraped_topology_service() -> ScrapedTopologyService:
    """Get or create scraped topology service instance"""
    global _scraped_topology_service
    if _scraped_topology_service is None:
        _scraped_topology_service = ScrapedTopologyService()
    return _scraped_topology_service
