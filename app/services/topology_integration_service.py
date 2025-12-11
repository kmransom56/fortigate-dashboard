"""
Topology Integration Service for FortiGate Dashboard
Integrates with FortiGate-Visio-Topology API for enhanced topology data
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Add the integration module to path
integration_path = Path("/media/keith/Windows Backup/projects/fortigate-visio-topology/dashboard_integration")
sys.path.insert(0, str(integration_path))

try:
    from fortigate_dashboard_integration import (
        FortiGateDashboardIntegration,
        get_2d_topology,
        get_3d_topology,
        get_hybrid_topology
    )
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"FortiGate-Visio topology integration not available: {e}")
    INTEGRATION_AVAILABLE = False


class TopologyIntegrationService:
    """Service for accessing enhanced topology data from FortiGate-Visio-Topology API."""

    def __init__(self):
        self.integration = FortiGateDashboardIntegration() if INTEGRATION_AVAILABLE else None
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Check if integration is available."""
        return INTEGRATION_AVAILABLE and self.integration is not None

    def get_2d_topology_data(self) -> Dict[str, Any]:
        """
        Get enhanced 2D topology data for D3.js visualization.

        Returns:
            Dict with nodes and links for D3.js force layout
        """
        if not self.is_available():
            raise Exception("Topology integration not available")

        try:
            return self.integration.get_topology_data_2d()
        except Exception as e:
            self.logger.error(f"Error fetching 2D topology: {e}")
            raise

    def get_3d_topology_data(self) -> Dict[str, Any]:
        """
        Get enhanced 3D topology data for 3d-force-graph visualization.

        Returns:
            Dict with nodes and links optimized for 3D rendering
        """
        if not self.is_available():
            raise Exception("Topology integration not available")

        try:
            return self.integration.get_topology_data_3d()
        except Exception as e:
            self.logger.error(f"Error fetching 3D topology: {e}")
            raise

    def get_hybrid_topology_data(self) -> Dict[str, Any]:
        """
        Get hybrid topology format compatible with existing services.

        Returns:
            Dict with devices, connections, and statistics
        """
        if not self.is_available():
            raise Exception("Topology integration not available")

        try:
            return self.integration.get_hybrid_topology_data()
        except Exception as e:
            self.logger.error(f"Error fetching hybrid topology: {e}")
            raise

    def get_device_statistics(self) -> Dict[str, Any]:
        """Get topology statistics."""
        if not self.is_available():
            return {"error": "Integration not available"}

        try:
            topology = self.integration.get_topology_data_2d()
            nodes = topology.get("nodes", [])
            links = topology.get("links", [])

            # Count device types
            device_types = {}
            for node in nodes:
                dtype = node.get("type", "unknown")
                device_types[dtype] = device_types.get(dtype, 0) + 1

            # Count link types
            link_types = {}
            for link in links:
                ltype = link.get("type", "unknown")
                link_types[ltype] = link_types.get(ltype, 0) + 1

            return {
                "total_devices": len(nodes),
                "total_links": len(links),
                "device_types": device_types,
                "link_types": link_types,
                "infrastructure_count": len([n for n in nodes if n.get("is_infrastructure", False)]),
                "endpoint_count": len([n for n in nodes if not n.get("is_infrastructure", False)]),
                "timestamp": topology.get("metadata", {}).get("timestamp")
            }
        except Exception as e:
            self.logger.error(f"Error fetching statistics: {e}")
            return {"error": str(e)}


# Singleton instance
_topology_integration_service = None


def get_topology_integration_service() -> TopologyIntegrationService:
    """Get singleton instance of TopologyIntegrationService."""
    global _topology_integration_service
    if _topology_integration_service is None:
        _topology_integration_service = TopologyIntegrationService()
    return _topology_integration_service
