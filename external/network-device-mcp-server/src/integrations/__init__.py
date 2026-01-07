"""
Integration modules for consolidating existing Fortinet projects
into the unified MCP Web Server platform.
"""

from .vlan_manager import VLANManager
from .troubleshooter import FortigateTroubleshooter  
from .ap_manager import FortiAPManager
from .utilities import NetworkUtilities
from .dashboard_merger import DashboardMerger
from .fortianalyzer import FortiAnalyzerManager
from .webfilters import WebFiltersManager

__all__ = [
    'VLANManager',
    'FortigateTroubleshooter', 
    'FortiAPManager',
    'NetworkUtilities',
    'DashboardMerger',
    'FortiAnalyzerManager',
    'WebFiltersManager'
]