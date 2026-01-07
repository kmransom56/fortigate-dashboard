"""
VLAN Manager Integration
Integrates fortigatevlans project functionality into the MCP Web Server
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class VLANManager:
    """
    Manages VLAN operations by integrating fortigatevlans project functionality
    """
    
    def __init__(self, fortigatevlans_path: str = None):
        """
        Initialize VLAN Manager with path to fortigatevlans project
        """
        if fortigatevlans_path is None:
            # Default path based on known project structure
            fortigatevlans_path = "/mnt/c/Users/keith.ransom/fortigatevlans"
        
        self.project_path = Path(fortigatevlans_path)
        self.output_path = self.project_path / "output"
        self.inputs_path = self.project_path / "inputs"
        
        # Add fortigatevlans to Python path for imports
        if str(self.project_path) not in sys.path:
            sys.path.append(str(self.project_path))
    
    def get_store_vlan_config(self, brand: str, store_id: str) -> Dict[str, Any]:
        """
        Get VLAN configuration for a specific store
        
        Args:
            brand: Restaurant brand (BWW, ARBYS, SONIC)
            store_id: Store identifier
            
        Returns:
            Dictionary containing VLAN configuration data
        """
        try:
            # Construct device name based on brand and store ID
            device_name = f"IBR-{brand.upper()}-{store_id.zfill(5)}"
            
            # Try to load existing VLAN data from database
            db_path = self.output_path / "vlan_data.db"
            if db_path.exists():
                vlan_data = self._query_vlan_database(device_name)
                if vlan_data:
                    return {
                        "success": True,
                        "device_name": device_name,
                        "brand": brand,
                        "store_id": store_id,
                        "vlan_interfaces": vlan_data,
                        "last_updated": self._get_last_update_time(device_name),
                        "source": "database"
                    }
            
            # If no database data, attempt live collection
            live_data = self._collect_live_vlan_data(device_name)
            if live_data:
                return {
                    "success": True,
                    "device_name": device_name,
                    "brand": brand,
                    "store_id": store_id,
                    "vlan_interfaces": live_data,
                    "last_updated": datetime.now().isoformat(),
                    "source": "live_collection"
                }
            
            return {
                "success": False,
                "device_name": device_name,
                "error": "No VLAN data available for this store",
                "suggestion": "Run VLAN collection for this device"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"VLAN configuration lookup failed: {str(e)}"
            }
    
    def get_brand_vlan_summary(self, brand: str) -> Dict[str, Any]:
        """
        Get VLAN configuration summary for all stores in a brand
        
        Args:
            brand: Restaurant brand (BWW, ARBYS, SONIC)
            
        Returns:
            Summary of VLAN configurations across the brand
        """
        try:
            db_path = self.output_path / "vlan_data.db"
            if not db_path.exists():
                return {
                    "success": False,
                    "error": "VLAN database not found. Run VLAN collection first."
                }
            
            brand_prefix = f"IBR-{brand.upper()}-"
            devices = self._query_brand_devices(brand_prefix)
            
            summary = {
                "success": True,
                "brand": brand,
                "total_devices": len(devices),
                "devices_with_vlans": 0,
                "common_vlans": {},
                "vlan_statistics": {},
                "devices": []
            }
            
            for device in devices:
                device_info = {
                    "device_name": device['device_name'],
                    "store_id": device['device_name'].split('-')[-1],
                    "vlan_count": device['vlan_count'],
                    "last_updated": device['last_updated']
                }
                summary["devices"].append(device_info)
                
                if device['vlan_count'] > 0:
                    summary["devices_with_vlans"] += 1
            
            return summary
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Brand VLAN summary failed: {str(e)}"
            }
    
    def run_vlan_collection(self, brand: str = None, store_id: str = None) -> Dict[str, Any]:
        """
        Run VLAN collection for specified brand/store or all devices
        
        Args:
            brand: Optional brand filter
            store_id: Optional specific store
            
        Returns:
            Collection results
        """
        try:
            # Import the actual VLAN collection modules
            from vlancollector import VLANCollector
            
            collector = VLANCollector()
            
            if brand and store_id:
                device_name = f"IBR-{brand.upper()}-{store_id.zfill(5)}"
                result = collector.collect_device_vlans(device_name)
                return {
                    "success": True,
                    "operation": "single_device_collection",
                    "device_name": device_name,
                    "vlans_collected": result.get('vlan_count', 0),
                    "collection_time": datetime.now().isoformat()
                }
            elif brand:
                result = collector.collect_brand_vlans(brand)
                return {
                    "success": True,
                    "operation": "brand_collection",
                    "brand": brand,
                    "devices_processed": result.get('device_count', 0),
                    "total_vlans": result.get('total_vlans', 0),
                    "collection_time": datetime.now().isoformat()
                }
            else:
                result = collector.collect_all_vlans()
                return {
                    "success": True,
                    "operation": "full_collection",
                    "devices_processed": result.get('device_count', 0),
                    "total_vlans": result.get('total_vlans', 0),
                    "collection_time": datetime.now().isoformat()
                }
                
        except ImportError:
            return {
                "success": False,
                "error": "VLAN collector module not available. Check fortigatevlans project setup."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"VLAN collection failed: {str(e)}"
            }
    
    def get_vlan_interfaces_by_type(self, brand: str, store_id: str, vlan_type: str = "vlan10") -> Dict[str, Any]:
        """
        Get specific VLAN interfaces (e.g., VLAN 10 interfaces)
        
        Args:
            brand: Restaurant brand
            store_id: Store identifier  
            vlan_type: Type of VLAN to filter (default: vlan10)
            
        Returns:
            Filtered VLAN interface data
        """
        try:
            device_name = f"IBR-{brand.upper()}-{store_id.zfill(5)}"
            
            # Query for specific VLAN type
            interfaces = self._query_vlan_interfaces_by_type(device_name, vlan_type)
            
            return {
                "success": True,
                "device_name": device_name,
                "vlan_type": vlan_type,
                "interfaces": interfaces,
                "interface_count": len(interfaces),
                "last_updated": self._get_last_update_time(device_name)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"VLAN interface query failed: {str(e)}"
            }
    
    def _query_vlan_database(self, device_name: str) -> Optional[List[Dict]]:
        """Query VLAN data from SQLite database"""
        try:
            db_path = self.output_path / "vlan_data.db"
            if not db_path.exists():
                return None
                
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM vlan_interfaces 
                    WHERE device_name = ? 
                    ORDER BY vlan_id, interface_name
                """, (device_name,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception:
            return None
    
    def _query_brand_devices(self, brand_prefix: str) -> List[Dict]:
        """Query all devices for a brand from database"""
        try:
            db_path = self.output_path / "vlan_data.db"
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT device_name, 
                           COUNT(*) as vlan_count,
                           MAX(last_updated) as last_updated
                    FROM vlan_interfaces 
                    WHERE device_name LIKE ?
                    GROUP BY device_name
                    ORDER BY device_name
                """, (f"{brand_prefix}%",))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception:
            return []
    
    def _query_vlan_interfaces_by_type(self, device_name: str, vlan_type: str) -> List[Dict]:
        """Query VLAN interfaces by type (e.g., vlan10)"""
        try:
            db_path = self.output_path / "vlan_data.db"
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Map vlan_type to actual VLAN ID
                vlan_id_map = {
                    "vlan10": 10,
                    "vlan116": 116,
                    "vlan117": 117,
                    "management": 1
                }
                
                vlan_id = vlan_id_map.get(vlan_type.lower(), 10)
                
                cursor.execute("""
                    SELECT * FROM vlan_interfaces 
                    WHERE device_name = ? AND vlan_id = ?
                    ORDER BY interface_name
                """, (device_name, vlan_id))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception:
            return []
    
    def _get_last_update_time(self, device_name: str) -> Optional[str]:
        """Get the last update time for a device"""
        try:
            db_path = self.output_path / "vlan_data.db"
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT MAX(last_updated) 
                    FROM vlan_interfaces 
                    WHERE device_name = ?
                """, (device_name,))
                
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
                
        except Exception:
            return None
    
    def _collect_live_vlan_data(self, device_name: str) -> Optional[List[Dict]]:
        """
        Attempt to collect live VLAN data for a device
        This is a placeholder for actual live collection logic
        """
        # This would integrate with the actual FortiGate API calls
        # from the fortigatevlans project
        return None