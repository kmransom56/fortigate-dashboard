import os
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the specialized utilities in DATASTORE
UTILITIES_PATH = Path("/media/keith/DATASTORE/Utilities")

class ToolboxService:
    """
    Exposes the 30+ (actually 95+) specialized utilities from the DATASTORE
    as a searchable 'NOC Toolbox' for the Enterprise Dashboard.
    """
    
    def __init__(self):
        self.categories = {
            "Network Discovery": ["device_discovery_tool", "unified_snmp_discovery", "topology_visualizer"],
            "Security & SSL": ["ssl_universal_fix", "zscaler_ssl_fix", "create_cert_bundle", "ssl_diagnostic_tool"],
            "FortiNet Specs": ["fortigate_config_diff", "fortimanager_api_solution", "fortiguard_psirt"],
            "Diagnostics": ["snmp_checker", "isp_report_generator", "ip_lookup"]
        }

    def get_toolbox_inventory(self) -> List[Dict[str, Any]]:
        """Returns a categorized catalog of available industrial tools."""
        inventory = []
        if not UTILITIES_PATH.exists():
            return [{"category": "Offline", "tools": [{"name": "DATASTORE not mounted", "description": "Utilities unavailable"}]}]

        for category, tool_prefixes in self.categories.items():
            category_tools = []
            for prefix in tool_prefixes:
                # Find matching files in the utilities folder
                matches = list(UTILITIES_PATH.glob(f"{prefix}*"))
                for match in matches:
                    if match.suffix in ['.py', '.sh', '.js']:
                        category_tools.append({
                            "name": match.name,
                            "type": match.suffix[1:].upper(),
                            "path": str(match),
                            "description": self._get_tool_description(match.name)
                        })
            inventory.append({
                "category": category,
                "tools": category_tools
            })
        return inventory

    def _get_tool_description(self, filename: str) -> str:
        """Heuristic-based description generation for existing tools."""
        descriptions = {
            "device_discovery_tool.py": "Advanced L2/L3 device discovery with multi-vendor support.",
            "ssl_universal_fix.py": "Enterprise-grade SSL/CA bundle reconciliation engine.",
            "topology_visualizer.py": "High-fidelity network graph generator using D3/Cytoscape logic.",
            "fortigate_config_diff.py": "Deep-packet configuration comparison for FortiOS clusters.",
            "zscaler_ssl_fix.py": "Automated Zscaler Root CA injection for proxy-restricted environments."
        }
        return descriptions.get(filename, "Specialized operational utility for network orchestration.")

toolbox_service = ToolboxService()
