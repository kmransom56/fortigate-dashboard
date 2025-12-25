from bs4 import BeautifulSoup
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _get_device_icon(
    manufacturer: str = None,
    device_type: str = None,
    model: str = None,
    mac: str = None,
) -> tuple:
    """
    Get icon path and title for a device using enhanced MAC lookup and icon database.

    Uses online MAC address lookup APIs to get detailed manufacturer and device type
    information for more accurate icon matching.

    Returns tuple of (icon_path, icon_title).
    """
    """
    Get icon path and title for a device using icon database lookup.
    Returns tuple of (icon_path, icon_title).
    """
    icon_path = ""
    icon_title = ""

    # Enhanced MAC lookup for better manufacturer and device type detection
    if mac and (not manufacturer or manufacturer == "Unknown"):
        try:
            from app.utils.enhanced_mac_lookup import get_enhanced_mac_info

            mac_info = get_enhanced_mac_info(mac)
            if (
                mac_info.get("manufacturer")
                and mac_info.get("manufacturer") != "Unknown"
            ):
                manufacturer = mac_info.get("manufacturer")
                logger.debug(f"Enhanced MAC lookup for {mac[:8]}: {manufacturer}")
                # Use device type hints from MAC lookup if device_type not specified
                if not device_type or device_type == "endpoint":
                    device_type_hints = mac_info.get("device_types", [])
                    if device_type_hints:
                        # Prefer more specific device types
                        preferred_types = [
                            "laptop",
                            "phone",
                            "tablet",
                            "printer",
                            "camera",
                            "pos",
                            "payment-terminal",
                            "raspberry-pi",
                            "tv",
                            "smart-tv",
                            "fire-tv",
                            "fire-cube",
                            "server",
                            "desktop",
                        ]
                        for preferred in preferred_types:
                            if preferred in device_type_hints:
                                device_type = preferred
                                logger.debug(
                                    f"Inferred device type from MAC: {device_type}"
                                )
                                break
                        # If no preferred type found, use first hint
                        if device_type == "endpoint" and device_type_hints:
                            device_type = device_type_hints[0]
                            logger.debug(f"Using device type hint: {device_type}")
        except Exception as e:
            logger.debug(f"Enhanced MAC lookup failed: {e}")

    try:
        from app.utils.icon_db import get_icon as _get_icon
        from app.utils.icon_db import get_icon_binding as _get_binding

        # Special handling for Fortinet devices (FortiGate, FortiSwitch, FortiAP) - try model-based lookup first
        if device_type in ["fortigate", "fortiswitch", "fortiap"] and model:
            # Try to match model in manifest.json
            try:
                import json
                import os

                manifest_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "app",
                    "static",
                    "icons",
                    "manifest.json",
                )
                if os.path.exists(manifest_path):
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)

                    # Determine device prefix and directory
                    device_prefix = {
                        "fortigate": "FG-",
                        "fortiswitch": "FSW-",
                        "fortiap": "FAP-",
                    }.get(device_type, "")
                    device_dir = {
                        "fortigate": "fortinet/fortigate",
                        "fortiswitch": "fortinet/fortiswitch",
                        "fortiap": "fortiap",
                    }.get(device_type, "")
                    device_name = {
                        "fortigate": "FortiGate",
                        "fortiswitch": "FortiSwitch",
                        "fortiap": "FortiAP",
                    }.get(device_type, "Device")

                    # Try exact model match (e.g., "FG-100F", "FSW-124E", "FAP-231F")
                    model_upper = model.upper().replace("-", "-")
                    if model_upper in manifest:
                        icon_file = manifest[model_upper]
                        # Check if it's in device-specific subdirectory
                        if icon_file.startswith(
                            device_dir + "/"
                        ) or icon_file.startswith(device_dir.replace("/", "-") + "/"):
                            icon_path = f"icons/{icon_file}"
                        else:
                            # Check if specific model icon exists in device directory
                            device_icon_dir = os.path.join(
                                os.path.dirname(
                                    os.path.dirname(os.path.dirname(__file__))
                                ),
                                "app",
                                "static",
                                "icons",
                                device_dir,
                            )
                            # Try to find model-specific icon
                            model_clean = model_upper.replace(
                                device_prefix, ""
                            ).replace("_", "-")
                            possible_icons = [
                                f"{model_upper}.svg",
                                f"{device_prefix}{model_clean}.svg",
                                f"{model_upper}-restaurant.svg",
                                f"{model_upper}-rugged.svg",
                            ]
                            for icon_file_name in possible_icons:
                                if os.path.exists(
                                    os.path.join(device_icon_dir, icon_file_name)
                                ):
                                    icon_path = f"icons/{device_dir}/{icon_file_name}"
                                    icon_title = f"{device_name} {model}"
                                    break
                            # If no specific icon found, use manifest mapping
                            if not icon_path and model_upper in manifest:
                                icon_file = manifest[model_upper]
                                # Check if manifest points to device directory
                                if icon_file.startswith(device_dir):
                                    icon_path = f"icons/{icon_file}"
                                else:
                                    icon_path = f"icons/{icon_file}"
                                icon_title = f"{device_name} {model}"
                    else:
                        # Try partial model match (e.g., "100F" from "FG-100F")
                        model_parts = model_upper.replace(device_prefix, "").split("-")[
                            0
                        ]
                        for key, value in manifest.items():
                            if model_parts in key or key in model_upper:
                                icon_file = value
                                if icon_file.startswith(
                                    device_dir + "/"
                                ) or icon_file.startswith(
                                    device_dir.replace("/", "-") + "/"
                                ):
                                    icon_path = f"icons/{icon_file}"
                                else:
                                    icon_path = f"icons/{icon_file}"
                                icon_title = f"{device_name} {model}"
                                break
            except Exception as e:
                logger.debug(f"Model-based icon lookup failed: {e}")

        # Try icon binding first (most specific) - includes MAC-based lookup
        if not icon_path:
            binding = _get_binding(
                manufacturer=manufacturer,
                mac=mac,
                device_type=device_type,
            )
            if binding and binding.get("icon_path"):
                icon_path = binding.get("icon_path")
                icon_title = binding.get("title") or icon_title

        # Try manufacturer lookup
        if not icon_path and manufacturer:
            icon_info = _get_icon(manufacturer=manufacturer)
            if icon_info:
                icon_path = icon_info.get("icon_path") or icon_path
                icon_title = icon_info.get("title") or icon_title

        # Try device type lookup
        if not icon_path and device_type:
            icon_info = _get_icon(device_type=device_type)
            if icon_info:
                icon_path = icon_info.get("icon_path") or icon_path
                icon_title = icon_info.get("title") or icon_title

    except Exception as e:
        logger.error(f"Icon lookup failed: {e}")
        # Log error for AI healer to detect and fix
        try:
            from app.services.ai_healer import get_ai_healer

            healer = get_ai_healer()
            error_msg = f"Icon lookup failed for device: manufacturer={manufacturer}, device_type={device_type}, model={model}, mac={mac}, error={str(e)}"
            diagnosis = healer.diagnose(error_msg)
            if diagnosis["matches_found"]:
                logger.info(
                    f"AI Healer suggested fix: {diagnosis['matches_found'][0]['fix']}"
                )
        except Exception:
            pass

    # No fallback - let AI healer fix missing icons
    if not icon_path:
        error_msg = f"No icon found for device: manufacturer={manufacturer}, device_type={device_type}, model={model}, mac={mac}"
        logger.error(error_msg)
        # Report to AI healer
        try:
            from app.services.ai_healer import get_ai_healer

            healer = get_ai_healer()
            diagnosis = healer.diagnose(error_msg)
            if diagnosis["matches_found"]:
                logger.info(
                    f"AI Healer suggested fix: {diagnosis['matches_found'][0]['fix']}"
                )
        except Exception:
            pass

    return icon_path, icon_title


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
            # Note: interfaces variable reserved for future use
            try:
                from app.services.fortigate_service import get_interfaces

                _ = get_interfaces() or {}
            except Exception as e:
                logger.warning(f"Could not get interfaces: {e}")

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

                        # Get manufacturer from MAC using enhanced lookup
                        manufacturer = "Unknown"
                        device_type_hint = "endpoint"
                        try:
                            from app.utils.enhanced_mac_lookup import (
                                get_enhanced_mac_info,
                            )

                            mac_info = get_enhanced_mac_info(mac)
                            manufacturer = mac_info.get("manufacturer", "Unknown")
                            device_type_hints = mac_info.get("device_types", [])
                            if device_type_hints:
                                device_type_hint = device_type_hints[0]
                        except Exception:
                            # Fallback to basic lookup
                            try:
                                manufacturer = get_manufacturer_from_mac(mac)
                            except Exception:
                                pass

                        # Create device ID from IP
                        device_id = f"device_{ip.replace('.', '_')}"

                        # Determine device type based on interface, IP, and MAC lookup hints
                        device_type = device_type_hint  # Use hint from MAC lookup
                        if "fortilink" in interface.lower():
                            device_type = "fortiswitch"
                        elif "wan" in interface.lower():
                            device_type = "router"
                        elif (
                            "internal" in interface.lower()
                            or "local" in interface.lower()
                        ):
                            # Keep device_type_hint if it's more specific than "endpoint"
                            if device_type == "endpoint":
                                device_type = "endpoint"

                        # Get icon for this device
                        icon_path, icon_title = _get_device_icon(
                            manufacturer=manufacturer, device_type=device_type, mac=mac
                        )

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
                                "iconPath": icon_path,
                                "iconTitle": icon_title,
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

                                # Get manufacturer from MAC using enhanced lookup
                                manufacturer = "Unknown"
                                device_type_hint = "endpoint"
                                try:
                                    from app.utils.enhanced_mac_lookup import (
                                        get_enhanced_mac_info,
                                    )

                                    mac_info = get_enhanced_mac_info(mac)
                                    manufacturer = mac_info.get(
                                        "manufacturer", "Unknown"
                                    )
                                    device_type_hints = mac_info.get("device_types", [])
                                    if device_type_hints:
                                        device_type_hint = device_type_hints[0]
                                except Exception:
                                    # Fallback to basic lookup
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
                                    # Get icon for this device using enhanced lookup
                                    icon_path, icon_title = _get_device_icon(
                                        manufacturer=manufacturer,
                                        device_type=device_type_hint,
                                        mac=mac,
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
                                        "manufacturer": manufacturer,
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
                                            "vlan": vlan,
                                            "iconPath": icon_path,
                                            "iconTitle": icon_title,
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
                                # Update icon if not already set or if we have better manufacturer info
                                detected_manufacturer = detected.get("manufacturer", "")
                                if (
                                    detected_manufacturer
                                    and detected_manufacturer != "Unknown"
                                ):
                                    if not arp_devices[aid]["details"].get("iconPath"):
                                        icon_path, icon_title = _get_device_icon(
                                            manufacturer=detected_manufacturer,
                                            device_type=adev.get("type", "endpoint"),
                                            mac=mac,
                                        )
                                        arp_devices[aid]["details"][
                                            "iconPath"
                                        ] = icon_path
                                        arp_devices[aid]["details"][
                                            "iconTitle"
                                        ] = icon_title
                                break

                        # If not in ARP, create new device
                        if not device_id:
                            device_id = f"detected_{mac.replace(':', '_')}"
                            detected_manufacturer = detected.get(
                                "manufacturer", "Unknown"
                            )

                            # Get icon for this device
                            icon_path, icon_title = _get_device_icon(
                                manufacturer=detected_manufacturer,
                                device_type="endpoint",
                                mac=mac,
                            )

                            detected_devices_map[device_id] = {
                                "id": device_id,
                                "type": "endpoint",
                                "name": f"{detected_manufacturer} ({mac[:8]})",
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
                                    "manufacturer": detected_manufacturer,
                                    "port": detected.get("port_name", ""),
                                    "switch": detected.get("switch_id", ""),
                                    "iconPath": icon_path,
                                    "iconTitle": icon_title,
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

            # Get FortiGate model and MAC from system info (if available)
            fgt_model = os.getenv("FORTIGATE_MODEL", "")
            fgt_mac = ""  # MAC not typically available for FortiGate itself
            try:
                # Try to get system status for model info
                system_status = fgt_api("monitor/system/status")
                if system_status:
                    fgt_model = system_status.get("model", fgt_model)
            except Exception:
                pass

            # Get icon for FortiGate using model
            fgt_icon_path, fgt_icon_title = _get_device_icon(
                manufacturer="Fortinet",
                device_type="fortigate",
                model=fgt_model,
                mac=fgt_mac,
            )

            devices.append(
                {
                    "id": "fortigate_main",
                    "type": "fortigate",
                    "name": fortigate_name,
                    "ip": fortigate_host.replace("https://", "")
                    .replace("http://", "")
                    .split(":")[0],
                    "model": fgt_model,
                    "mac": fgt_mac,
                    "position": {"x": 400, "y": 100},
                    "status": "online",
                    "risk": "low",
                    "details": {
                        "deviceCount": 1,
                        "color": "#2196f3",
                        "status": "online",
                        "manufacturer": "Fortinet",
                        "model": fgt_model,
                        "iconPath": fgt_icon_path,
                        "iconTitle": fgt_icon_title,
                    },
                }
            )

            # Get FortiAPs from Security Fabric or detected devices
            fortiap_devices = {}
            try:
                # Try Security Fabric API for managed FortiAPs
                try:
                    fabric_data = fgt_api("monitor/system/fortiguard/security-fabric")
                    if fabric_data and "results" in fabric_data:
                        for fabric_device in fabric_data["results"]:
                            device_type = fabric_device.get("device_type", "").lower()
                            if "ap" in device_type or "fortiap" in device_type:
                                ap_serial = fabric_device.get("serial", "")
                                ap_name = fabric_device.get(
                                    "name", f"FortiAP-{ap_serial[:8]}"
                                )
                                ap_id = f"fortiap_{ap_serial}"

                                # Get icon for FortiAP using model and MAC
                                ap_model = fabric_device.get("model", "")
                                ap_mac = fabric_device.get("mac", "").upper()
                                ap_icon_path, ap_icon_title = _get_device_icon(
                                    manufacturer="Fortinet",
                                    device_type="fortiap",
                                    model=ap_model,
                                    mac=ap_mac,
                                )

                                fortiap_devices[ap_id] = {
                                    "id": ap_id,
                                    "type": "fortiap",
                                    "name": ap_name,
                                    "ip": fabric_device.get("ip", ""),
                                    "serial": ap_serial,
                                    "model": ap_model,
                                    "mac": ap_mac,
                                    "position": {
                                        "x": 200 + (len(fortiap_devices) % 4) * 150,
                                        "y": 500 + (len(fortiap_devices) // 4) * 120,
                                    },
                                    "status": (
                                        "online"
                                        if fabric_device.get("status") == "online"
                                        else "warning"
                                    ),
                                    "risk": "low",
                                    "details": {
                                        "deviceCount": 1,
                                        "color": "#9c27b0",
                                        "status": fabric_device.get(
                                            "status", "unknown"
                                        ),
                                        "manufacturer": "Fortinet",
                                        "model": ap_model,
                                        "iconPath": ap_icon_path,
                                        "iconTitle": ap_icon_title,
                                    },
                                }
                        logger.info(
                            f"Found {len(fortiap_devices)} FortiAPs from Security Fabric"
                        )
                except Exception as e:
                    logger.debug(f"Security Fabric API not available: {e}")

                # Also check detected devices for FortiAP MAC addresses (Fortinet OUI: 00:09:0f, 70:4c:a5, etc.)
                fortinet_ouis = ["00:09:0f", "70:4c:a5", "00:0c:29", "fc:ec:da"]
                for device_id, device_data in (
                    list(arp_devices.items())
                    + list(mac_address_devices.items())
                    + list(detected_devices_map.items())
                ):
                    mac = device_data.get("mac", "").upper()
                    if mac and any(mac.startswith(oui) for oui in fortinet_ouis):
                        # Check if it's likely a FortiAP (not FortiGate or FortiSwitch)
                        device_type = device_data.get("type", "")
                        manufacturer = device_data.get("manufacturer", "")
                        if device_type != "fortigate" and device_type != "fortiswitch":
                            # Could be a FortiAP - check if not already identified
                            if device_id not in fortiap_devices:
                                # Try to identify as FortiAP
                                ap_id = f"fortiap_{mac.replace(':', '_')}"
                                if ap_id not in fortiap_devices:
                                    # Try to extract model from device name or use MAC for lookup
                                    device_name = device_data.get("name", "")
                                    ap_model = ""
                                    # Try to extract model from name (e.g., "FAP-231F" or "FortiAP-231F")
                                    if "FAP-" in device_name.upper():
                                        parts = device_name.upper().split("FAP-")
                                        if len(parts) > 1:
                                            model_part = (
                                                parts[1].split()[0].split("(")[0]
                                            )
                                            ap_model = f"FAP-{model_part}"

                                    ap_icon_path, ap_icon_title = _get_device_icon(
                                        manufacturer="Fortinet",
                                        device_type="fortiap",
                                        model=ap_model,
                                        mac=mac,
                                    )

                                fortiap_devices[ap_id] = {
                                    "id": ap_id,
                                    "type": "fortiap",
                                    "name": f"FortiAP {ap_model if ap_model else mac[:8]}",
                                    "ip": device_data.get("ip", ""),
                                    "mac": mac,
                                    "model": ap_model,
                                    "position": {
                                        "x": 200 + (len(fortiap_devices) % 4) * 150,
                                        "y": 500 + (len(fortiap_devices) // 4) * 120,
                                    },
                                    "status": device_data.get("status", "online"),
                                    "risk": "low",
                                    "details": {
                                        "deviceCount": 1,
                                        "color": "#9c27b0",
                                        "status": device_data.get("status", "unknown"),
                                        "manufacturer": "Fortinet",
                                        "model": ap_model,
                                        "iconPath": ap_icon_path,
                                        "iconTitle": ap_icon_title,
                                    },
                                }
                                logger.info(f"Identified FortiAP from MAC: {mac}")
            except Exception as e:
                logger.warning(f"Could not get FortiAPs: {e}")

            # Add switches from API data
            if switches_data and switches_data.get("switches"):
                for idx, switch in enumerate(switches_data["switches"]):
                    switch_id = switch.get("serial", f"switch_{idx}")
                    switch_model = switch.get("model", "")

                    # Get switch MAC address if available
                    switch_mac = (
                        switch.get("mac", "").upper()
                        or switch.get("mac_address", "").upper()
                    )

                    # Get icon for switch using model and MAC
                    switch_icon_path, switch_icon_title = _get_device_icon(
                        manufacturer="Fortinet",
                        device_type="fortiswitch",
                        model=switch_model,
                        mac=switch_mac,
                    )

                    devices.append(
                        {
                            "id": switch_id,
                            "type": "fortiswitch",
                            "name": switch.get("name", f"FortiSwitch {idx + 1}"),
                            "ip": switch.get("ip", ""),
                            "model": switch_model,
                            "mac": switch_mac,
                            "serial": switch.get("serial", switch_id),
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
                                "model": switch_model,
                                "iconPath": switch_icon_path,
                                "iconTitle": switch_icon_title,
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

            # Add FortiAPs to devices list
            devices.extend(fortiap_devices.values())

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

            # Connect FortiAPs to their switches (FortiAPs are typically connected via PoE)
            for ap_id, ap_data in fortiap_devices.items():
                # Try to find which switch the FortiAP is connected to
                # Check if FortiAP MAC or IP matches any switch port device
                ap_mac = ap_data.get("mac", "")
                ap_ip = ap_data.get("ip", "")
                connected_switch_id = None

                # Check detected devices for FortiAP connection
                for device_id, device_data in detected_devices_map.items():
                    if (
                        device_data.get("mac") == ap_mac
                        or device_data.get("ip") == ap_ip
                    ):
                        connected_switch_id = device_data.get("details", {}).get(
                            "switch", ""
                        )
                        break

                # If found a switch, connect to it; otherwise connect to FortiGate
                if connected_switch_id:
                    for switch in devices:
                        if (
                            switch.get("id") == connected_switch_id
                            or switch.get("serial") == connected_switch_id
                        ):
                            connections.append(
                                {
                                    "from": switch["id"],
                                    "to": ap_id,
                                    "type": "poe",
                                    "status": "active",
                                }
                            )
                            break
                else:
                    # Connect to nearest switch or FortiGate
                    if switches_data and switches_data.get("switches"):
                        # Connect to first switch (FortiAPs are usually on switches)
                        first_switch = devices[1] if len(devices) > 1 else None
                        if first_switch and first_switch.get("type") == "fortiswitch":
                            connections.append(
                                {
                                    "from": first_switch["id"],
                                    "to": ap_id,
                                    "type": "poe",
                                    "status": "active",
                                }
                            )
                        else:
                            connections.append(
                                {
                                    "from": "fortigate_main",
                                    "to": ap_id,
                                    "type": "wireless",
                                    "status": "active",
                                }
                            )

            logger.info(
                f"Total devices in topology: {len(devices)} (FortiGate: 1, Switches: {len(switches_data.get('switches', [])) if switches_data else 0}, ARP: {len(arp_devices)}, MAC Table: {len(mac_address_devices)}, Detected: {len(detected_devices_map)}, FortiAPs: {len(fortiap_devices)})"
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
