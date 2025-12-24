"""
FortiGate Comprehensive API Service

Provides access to all 246+ API endpoints across 5 API definition files.
Organized by category with both dedicated functions and generic endpoint caller.
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

from .fortigate_service import fgt_api

logger = logging.getLogger(__name__)


class APICategory(Enum):
    """API endpoint categories"""

    SYSTEM_MONITOR = "system_monitor"
    SYSTEM_CONFIG = "system_config"
    SWITCH_CONTROLLER = "switch_controller"
    FORTISWITCH_MONITOR = "fortiswitch_monitor"
    FORTISWITCH_SYSTEM = "fortiswitch_system"


class FortiGateComprehensiveAPI:
    """
    Comprehensive API service providing access to all FortiGate/FortiSwitch endpoints.
    Supports both dedicated functions and generic endpoint calling.
    """

    def __init__(self):
        self.endpoint_registry = self._build_endpoint_registry()

    def _build_endpoint_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        Build registry of all 246 available endpoints from API definition files.
        Auto-generated from JSON API definition files.
        """
        registry = {}

        # Load all endpoints from JSON files dynamically
        import json
        import os

        api_def_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "api_definitions",
        )

        files = {
            "system_monitor": (
                "FortiOS 7.6 FortiOS 7.6.3 Monitor API system.json",
                "monitor",
                APICategory.SYSTEM_MONITOR,
            ),
            "switch_controller": (
                "FortiOS 7.6 FortiOS 7.6.3 Monitor API switch-controller.json",
                "monitor",
                APICategory.SWITCH_CONTROLLER,
            ),
            "fortiswitch": (
                "FortiSwitch 7.6.1 Monitor API switch.json",
                "monitor",
                APICategory.FORTISWITCH_MONITOR,
            ),
            "fortiswitch_system": (
                "FortiSwitch 7.6.1 Monitor API system.json",
                "monitor",
                APICategory.FORTISWITCH_SYSTEM,
            ),
            "config": (
                "FortiOS 7.6 FortiOS 7.6.3 Configuration API system.json",
                "cmdb",
                APICategory.SYSTEM_CONFIG,
            ),
        }

        for category, (filename, base_path, category_enum) in files.items():
            filepath = os.path.join(api_def_path, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        endpoints = list(data.get("paths", {}).keys())
                        for endpoint in endpoints:
                            registry[endpoint] = {
                                "category": category_enum,
                                "base_path": base_path,
                                "method": "GET",
                            }
                except Exception as e:
                    logger.warning(f"Failed to load {filename}: {e}")
            else:
                logger.warning(f"API definition file not found: {filepath}")

        logger.info(f"Loaded {len(registry)} endpoints into registry")
        return registry

    def call_endpoint(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """
        Generic endpoint caller - can call any registered endpoint.

        Args:
            endpoint: Endpoint path (e.g., "/system/status" or "system/status")
            params: Optional query parameters
            method: HTTP method (GET, POST, PUT, DELETE)

        Returns:
            API response dictionary
        """
        # Normalize endpoint
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]

        # Check if endpoint is in registry
        full_path = f"/{endpoint}" if not endpoint.startswith("/") else endpoint
        if full_path not in self.endpoint_registry:
            logger.warning(
                f"Endpoint {endpoint} not in registry, attempting call anyway"
            )

        # Determine base path
        if endpoint.startswith("monitor/") or endpoint.startswith("cmdb/"):
            api_endpoint = endpoint
        elif endpoint.startswith("system/") or endpoint.startswith("switch/"):
            # Try to determine if it's monitor or cmdb
            if full_path in self.endpoint_registry:
                base = self.endpoint_registry[full_path]["base_path"]
                api_endpoint = f"{base}{full_path}"
            else:
                # Default to monitor for system/switch endpoints
                api_endpoint = f"monitor{full_path}"
        else:
            # Assume monitor for unknown endpoints
            api_endpoint = f"monitor/{endpoint}"

        logger.debug(f"Calling endpoint: {api_endpoint} (method: {method})")
        return fgt_api(api_endpoint, params=params)

    def list_endpoints(self, category: Optional[APICategory] = None) -> List[str]:
        """List all available endpoints, optionally filtered by category"""
        if category:
            return [
                endpoint
                for endpoint, info in self.endpoint_registry.items()
                if info["category"] == category
            ]
        return list(self.endpoint_registry.keys())

    def get_endpoint_info(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific endpoint"""
        full_path = f"/{endpoint}" if not endpoint.startswith("/") else endpoint
        return self.endpoint_registry.get(full_path)

    # === System Monitor API Methods ===

    def get_system_status(self) -> Dict[str, Any]:
        """Get FortiGate system status"""
        return self.call_endpoint("monitor/system/status")

    def get_available_interfaces(self) -> Dict[str, Any]:
        """Get available interfaces"""
        return self.call_endpoint("monitor/system/available-interfaces")

    def get_interface_status(self) -> Dict[str, Any]:
        """Get interface status"""
        return self.call_endpoint("monitor/system/interface")

    def get_security_fabric_csf(self) -> Dict[str, Any]:
        """Get Security Fabric information via /system/csf endpoint"""
        return self.call_endpoint("monitor/system/csf")

    def get_security_fabric_pending(self) -> Dict[str, Any]:
        """Get pending Security Fabric authorizations"""
        return self.call_endpoint("monitor/system/csf/pending-authorizations")

    def get_security_rating_status(self) -> Dict[str, Any]:
        """Get security rating status"""
        return self.call_endpoint("monitor/system/security-rating/status")

    def get_performance_status(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.call_endpoint("monitor/system/performance/status")

    def get_cluster_state(self) -> Dict[str, Any]:
        """Get cluster/HA state"""
        return self.call_endpoint("monitor/system/cluster/state")

    # === Switch Controller API Methods ===

    def get_switch_health_status(
        self, switch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get switch health status"""
        endpoint = "monitor/switch-controller/managed-switch/health-status"
        params = {"mkey": switch_id} if switch_id else None
        return self.call_endpoint(endpoint, params=params)

    def get_switch_port_health(self, switch_id: Optional[str] = None) -> Dict[str, Any]:
        """Get port health information"""
        endpoint = "monitor/switch-controller/managed-switch/port-health"
        params = {"mkey": switch_id} if switch_id else None
        return self.call_endpoint(endpoint, params=params)

    def get_switch_cable_status(
        self, switch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cable status"""
        endpoint = "monitor/switch-controller/managed-switch/cable-status"
        params = {"mkey": switch_id} if switch_id else None
        return self.call_endpoint(endpoint, params=params)

    def get_switch_transceivers(
        self, switch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get transceiver information"""
        endpoint = "monitor/switch-controller/managed-switch/transceivers"
        params = {"mkey": switch_id} if switch_id else None
        return self.call_endpoint(endpoint, params=params)

    def get_switch_tx_rx_stats(self, switch_id: Optional[str] = None) -> Dict[str, Any]:
        """Get TX/RX statistics"""
        endpoint = "monitor/switch-controller/managed-switch/tx-rx"
        params = {"mkey": switch_id} if switch_id else None
        return self.call_endpoint(endpoint, params=params)

    def get_matched_devices(self) -> Dict[str, Any]:
        """Get NAC/policy matched devices"""
        return self.call_endpoint("monitor/switch-controller/matched-devices")

    def get_switch_models(self) -> Dict[str, Any]:
        """Get supported switch models"""
        return self.call_endpoint("monitor/switch-controller/managed-switch/models")

    # === FortiSwitch Direct API Methods ===

    def get_fortiswitch_port_info(self) -> Dict[str, Any]:
        """Get FortiSwitch port information"""
        return self.call_endpoint("monitor/switch/port/")

    def get_fortiswitch_port_statistics(self) -> Dict[str, Any]:
        """Get FortiSwitch port statistics"""
        return self.call_endpoint("monitor/switch/port-statistics/")

    def get_fortiswitch_poe_status(self) -> Dict[str, Any]:
        """Get PoE status"""
        return self.call_endpoint("monitor/switch/poe-status/")

    def get_fortiswitch_poe_summary(self) -> Dict[str, Any]:
        """Get PoE summary"""
        return self.call_endpoint("monitor/switch/poe-summary/")

    def get_fortiswitch_stp_state(self) -> Dict[str, Any]:
        """Get STP state"""
        return self.call_endpoint("monitor/switch/stp-state/")

    def get_fortiswitch_trunk_state(self) -> Dict[str, Any]:
        """Get trunk state"""
        return self.call_endpoint("monitor/switch/trunk-state/")

    def get_fortiswitch_loop_guard(self) -> Dict[str, Any]:
        """Get loop guard state"""
        return self.call_endpoint("monitor/switch/loop-guard-state/")

    def get_fortiswitch_cable_diag(self) -> Dict[str, Any]:
        """Get cable diagnostics"""
        return self.call_endpoint("monitor/switch/cable-diag/")

    def get_fortiswitch_capabilities(self) -> Dict[str, Any]:
        """Get switch capabilities"""
        return self.call_endpoint("monitor/switch/capabilities/")

    def get_fortiswitch_acl_stats(self) -> Dict[str, Any]:
        """Get ACL statistics"""
        return self.call_endpoint("monitor/switch/acl-stats/")

    def get_fortiswitch_qos_stats(self) -> Dict[str, Any]:
        """Get QoS statistics"""
        return self.call_endpoint("monitor/switch/qos-stats/")

    def get_fortiswitch_dhcp_snooping_db(self) -> Dict[str, Any]:
        """Get DHCP snooping database"""
        return self.call_endpoint("monitor/switch/dhcp-snooping-db/")

    def get_fortiswitch_igmp_snooping(self) -> Dict[str, Any]:
        """Get IGMP snooping groups"""
        return self.call_endpoint("monitor/switch/igmp-snooping-group/")

    def get_fortiswitch_mclag_list(self) -> Dict[str, Any]:
        """Get MCLAG list"""
        return self.call_endpoint("monitor/switch/mclag-list/")

    def get_fortiswitch_modules_status(self) -> Dict[str, Any]:
        """Get module status"""
        return self.call_endpoint("monitor/switch/modules-status/")

    def get_fortiswitch_8021x_status(self) -> Dict[str, Any]:
        """Get 802.1x status"""
        return self.call_endpoint("monitor/switch/802.1x-status/")

    def get_fortiswitch_flapguard_status(self) -> Dict[str, Any]:
        """Get flap guard status"""
        return self.call_endpoint("monitor/switch/flapguard-status/")

    # === Interface Management ===

    def get_interface_poe(self) -> Dict[str, Any]:
        """Get PoE status for interfaces"""
        return self.call_endpoint("monitor/system/interface/poe")

    def get_interface_transceivers(self) -> Dict[str, Any]:
        """Get transceiver information for interfaces"""
        return self.call_endpoint("monitor/system/interface/transceivers")

    def get_interface_dhcp_status(self) -> Dict[str, Any]:
        """Get DHCP status per interface"""
        return self.call_endpoint("monitor/system/interface/dhcp-status")

    # === Configuration API Methods ===

    def get_arp_table_config(self) -> Dict[str, Any]:
        """Get ARP table configuration"""
        return self.call_endpoint("cmdb/system/arp-table")

    def get_proxy_arp_config(self) -> Dict[str, Any]:
        """Get proxy ARP configuration"""
        return self.call_endpoint("cmdb/system/proxy-arp")


# Global instance
_comprehensive_api = None


def get_comprehensive_api() -> FortiGateComprehensiveAPI:
    """Get global comprehensive API service instance"""
    global _comprehensive_api
    if _comprehensive_api is None:
        _comprehensive_api = FortiGateComprehensiveAPI()
    return _comprehensive_api
