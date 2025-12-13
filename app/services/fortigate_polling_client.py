"""
FortiGate Polling Client - Real Data Acquisition
Based on fortigate-visio-topology/src/fortigate_visio/fortigate_client.py
"""

import os
import requests
import urllib3
from typing import List, Dict, Any, Optional
from loguru import logger

# Disable SSL warnings if verify_ssl is False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FortiGatePollingClient:
    """Client for polling real data from FortiGate API."""

    def __init__(
        self,
        host: Optional[str] = None,
        api_token: Optional[str] = None,
        verify_ssl: bool = False,
        timeout: int = 30
    ):
        self.host = host or os.getenv("FORTIGATE_HOST", "https://192.168.0.254")

        # Load API token from file or env
        if api_token:
            self.api_token = api_token
        else:
            token_file = os.getenv("FORTIGATE_API_TOKEN_FILE", "secrets/fortigate_api_token.txt")
            try:
                with open(token_file, 'r') as f:
                    self.api_token = f.read().strip()
            except FileNotFoundError:
                self.api_token = os.getenv("FORTIGATE_API_TOKEN", "")

        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Ensure host has no trailing slash
        self.host = self.host.rstrip('/')

        logger.info(f"FortiGate Polling Client initialized: {self.host}")

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json"
        }

    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to FortiGate API."""
        url = f"{self.host}{endpoint}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"FortiGate API request failed: {endpoint} - {str(e)}")
            raise Exception(f"FortiGate API request failed: {str(e)}")

    def get_devices(self) -> List[Dict[str, Any]]:
        """
        Query FortiGate for detected devices.
        Uses /api/v2/monitor/user/device/query endpoint.
        """
        endpoint = "/api/v2/monitor/user/device/query"

        try:
            data = self._make_request(endpoint)

            # FortiOS 7.6 may return results under different keys
            raw_devices = data.get("results", data.get("data", data))

            # If it's a dict with more nesting, try to find the device list
            if isinstance(raw_devices, dict):
                raw_devices = raw_devices.get("devices", [])

            devices = []
            for d in raw_devices:
                device = self._parse_device(d)
                devices.append(device)

            logger.info(f"Retrieved {len(devices)} devices from FortiGate")
            return devices
        except Exception as e:
            logger.error(f"Failed to get devices from FortiGate: {str(e)}")
            return []

    def _parse_device(self, raw_device: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw FortiGate device data into standardized format."""

        # Generate a unique device ID
        device_id = (
            raw_device.get("id") or
            raw_device.get("uuid") or
            f"{raw_device.get('mac', 'unknown')}-{raw_device.get('detected_interface', 'na')}"
        )

        return {
            "device_id": device_id,
            "hostname": raw_device.get("hostname") or raw_device.get("device_name") or "",
            "ip": raw_device.get("ipv4_address") or raw_device.get("ip") or "",
            "mac": raw_device.get("mac") or "",
            "vendor": raw_device.get("hardware_vendor") or raw_device.get("device_vendor") or "",
            "os": raw_device.get("os_name") or raw_device.get("os") or "",
            "interface": raw_device.get("detected_interface") or "",
            "role": raw_device.get("device_type") or raw_device.get("category") or "Unknown",
            "is_online": raw_device.get("is_online", True),
            "parent_device_id": "",
            "notes": "",
            # Extended fields
            "host_src": raw_device.get("host_src") or "",
            "hardware_type": raw_device.get("hardware_type") or "",
            "hardware_family": raw_device.get("hardware_family") or "",
            # FortiSwitch fields
            "fortiswitch_id": raw_device.get("fortiswitch_id"),
            "fortiswitch_port_name": raw_device.get("fortiswitch_port_name"),
            "fortiswitch_port_id": raw_device.get("fortiswitch_port_id"),
            "fortiswitch_serial": raw_device.get("fortiswitch_serial"),
            "fortiswitch_vlan_id": raw_device.get("fortiswitch_vlan_id"),
            "is_fortiswitch_client": raw_device.get("is_fortiswitch_client", False),
            # FortiAP fields
            "fortiap_id": raw_device.get("fortiap_id"),
            "fortiap_name": raw_device.get("fortiap_name"),
            "fortiap_ssid": raw_device.get("fortiap_ssid")
        }

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to FortiGate API."""
        try:
            endpoint = "/api/v2/monitor/system/status"
            data = self._make_request(endpoint)

            result = data.get("results", {})
            logger.success(f"FortiGate connection successful: {result.get('hostname', 'Unknown')}")

            return {
                "success": True,
                "message": "Connection successful",
                "version": result.get("version", "Unknown"),
                "hostname": result.get("hostname", "Unknown")
            }
        except Exception as e:
            logger.error(f"FortiGate connection failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            }

    def get_lldp_neighbors(self) -> List[Dict[str, Any]]:
        """Get LLDP neighbor information for physical topology discovery."""
        endpoint = "/api/v2/monitor/network/lldp/neighbors"

        try:
            data = self._make_request(endpoint)
            results = data.get("results", [])
            logger.info(f"Retrieved {len(results)} LLDP neighbors")
            return results if isinstance(results, list) else []
        except Exception as e:
            logger.warning(f"Failed to get LLDP neighbors: {str(e)}")
            return []

    def get_lldp_ports(self) -> List[Dict[str, Any]]:
        """Get LLDP port information."""
        endpoint = "/api/v2/monitor/network/lldp/ports"

        try:
            data = self._make_request(endpoint)
            results = data.get("results", [])
            logger.info(f"Retrieved {len(results)} LLDP ports")
            return results if isinstance(results, list) else []
        except Exception as e:
            logger.warning(f"Failed to get LLDP ports: {str(e)}")
            return []

    def get_managed_switches(self) -> List[Dict[str, Any]]:
        """Get managed FortiSwitch devices."""
        endpoint = "/api/v2/monitor/switch-controller/managed-switch/status"

        try:
            data = self._make_request(endpoint)
            results = data.get("results", [])
            logger.info(f"Retrieved {len(results)} managed switches")
            return results if isinstance(results, list) else []
        except Exception as e:
            logger.warning(f"Failed to get managed switches: {str(e)}")
            return []

    def get_managed_aps(self) -> List[Dict[str, Any]]:
        """Get managed FortiAP access points."""
        endpoint = "/api/v2/monitor/wifi/managed_ap"

        try:
            data = self._make_request(endpoint)
            results = data.get("results", [])
            logger.info(f"Retrieved {len(results)} managed APs")
            return results if isinstance(results, list) else []
        except Exception as e:
            logger.warning(f"Failed to get managed APs: {str(e)}")
            return []

    def get_wifi_clients(self) -> List[Dict[str, Any]]:
        """Get WiFi clients connected to FortiAPs."""
        endpoint = "/api/v2/monitor/wifi/client"

        try:
            data = self._make_request(endpoint)
            results = data.get("results", [])
            logger.info(f"Retrieved {len(results)} WiFi clients")
            return results if isinstance(results, list) else []
        except Exception as e:
            logger.warning(f"Failed to get WiFi clients: {str(e)}")
            return []

    def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get FortiGate interface information with statistics."""
        endpoint = "/api/v2/monitor/system/interface"

        try:
            data = self._make_request(endpoint)
            results = data.get("results", [])
            logger.info(f"Retrieved {len(results)} interfaces")
            return results if isinstance(results, list) else []
        except Exception as e:
            logger.warning(f"Failed to get interfaces: {str(e)}")
            return []

    def get_arp_table(self) -> List[Dict[str, Any]]:
        """Get IPv4 ARP table for IP-to-MAC mappings."""
        endpoint = "/api/v2/monitor/network/arp"

        try:
            data = self._make_request(endpoint)
            results = data.get("results", [])
            logger.info(f"Retrieved {len(results)} ARP entries")
            return results if isinstance(results, list) else []
        except Exception as e:
            logger.warning(f"Failed to get ARP table: {str(e)}")
            return []

    def get_all_topology_data(self) -> Dict[str, Any]:
        """Get all topology data in one call."""
        logger.info("Fetching comprehensive topology data from FortiGate...")

        return {
            "devices": self.get_devices(),
            "lldp_neighbors": self.get_lldp_neighbors(),
            "lldp_ports": self.get_lldp_ports(),
            "managed_switches": self.get_managed_switches(),
            "managed_aps": self.get_managed_aps(),
            "wifi_clients": self.get_wifi_clients(),
            "interfaces": self.get_interfaces(),
            "arp_table": self.get_arp_table()
        }


# Singleton instance
_fortigate_client = None

def get_fortigate_polling_client() -> FortiGatePollingClient:
    """Get singleton FortiGate polling client."""
    global _fortigate_client
    if _fortigate_client is None:
        _fortigate_client = FortiGatePollingClient()
    return _fortigate_client
