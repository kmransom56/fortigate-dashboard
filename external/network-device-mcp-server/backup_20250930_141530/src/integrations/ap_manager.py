"""
FortiAP Manager Integration
Integrates addfortiap project functionality into the MCP Web Server
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class FortiAPManager:
    """
    Manages FortiAP operations by integrating addfortiap project functionality
    """
    
    def __init__(self, addfortiap_path: str = None):
        """
        Initialize FortiAP Manager with path to addfortiap project
        """
        if addfortiap_path is None:
            addfortiap_path = "/mnt/c/Users/keith.ransom/addfortiap"
        
        self.project_path = Path(addfortiap_path)
        
        # Add addfortiap to Python path for imports
        if str(self.project_path) not in sys.path:
            sys.path.append(str(self.project_path))
    
    def get_brand_access_points(self, brand: str) -> Dict[str, Any]:
        """
        Get all FortiAPs for a specific brand
        
        Args:
            brand: Restaurant brand (BWW, ARBYS, SONIC)
            
        Returns:
            Dictionary containing FortiAP information for the brand
        """
        try:
            # Load FortiAP data from database
            aps_data = self._query_brand_aps(brand)
            
            summary = {
                "success": True,
                "brand": brand,
                "total_aps": len(aps_data),
                "online_aps": len([ap for ap in aps_data if ap.get('status') == 'online']),
                "offline_aps": len([ap for ap in aps_data if ap.get('status') == 'offline']),
                "access_points": aps_data,
                "last_updated": datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get FortiAPs for {brand}: {str(e)}"
            }
    
    def get_store_access_points(self, brand: str, store_id: str) -> Dict[str, Any]:
        """
        Get FortiAPs for a specific store
        
        Args:
            brand: Restaurant brand
            store_id: Store identifier
            
        Returns:
            Dictionary containing store's FortiAP information
        """
        try:
            device_name = f"IBR-{brand.upper()}-{store_id.zfill(5)}"
            store_aps = self._query_store_aps(device_name)
            
            return {
                "success": True,
                "device_name": device_name,
                "brand": brand,
                "store_id": store_id,
                "access_point_count": len(store_aps),
                "access_points": store_aps,
                "ap_summary": self._generate_ap_summary(store_aps),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get store FortiAPs: {str(e)}"
            }
    
    def deploy_fortiap(self, brand: str, store_id: str, ap_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy a new FortiAP to a store
        
        Args:
            brand: Restaurant brand
            store_id: Store identifier
            ap_config: FortiAP configuration parameters
            
        Returns:
            Deployment result
        """
        try:
            device_name = f"IBR-{brand.upper()}-{store_id.zfill(5)}"
            
            # Import the FortiAP deployment functionality
            from add_fortiaps import FortiAPDeployer
            
            deployer = FortiAPDeployer()
            result = deployer.deploy_ap(device_name, ap_config)
            
            return {
                "success": True,
                "device_name": device_name,
                "deployment_id": result.get('deployment_id'),
                "ap_serial": ap_config.get('serial_number'),
                "ap_model": ap_config.get('model'),
                "deployment_status": result.get('status', 'initiated'),
                "deployment_time": datetime.now().isoformat()
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "FortiAP deployment module not available"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"FortiAP deployment failed: {str(e)}"
            }
    
    def get_ap_status(self, ap_serial: str) -> Dict[str, Any]:
        """
        Get status of a specific FortiAP by serial number
        
        Args:
            ap_serial: FortiAP serial number
            
        Returns:
            FortiAP status information
        """
        try:
            ap_data = self._query_ap_by_serial(ap_serial)
            
            if not ap_data:
                return {
                    "success": False,
                    "error": f"FortiAP with serial {ap_serial} not found"
                }
            
            return {
                "success": True,
                "serial_number": ap_serial,
                "ap_details": ap_data,
                "status": ap_data.get('status', 'unknown'),
                "last_seen": ap_data.get('last_seen'),
                "firmware_version": ap_data.get('firmware'),
                "client_count": ap_data.get('client_count', 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get FortiAP status: {str(e)}"
            }
    
    def get_wireless_clients(self, brand: str, store_id: str) -> Dict[str, Any]:
        """
        Get wireless clients connected to store's FortiAPs
        
        Args:
            brand: Restaurant brand
            store_id: Store identifier
            
        Returns:
            Wireless client information
        """
        try:
            device_name = f"IBR-{brand.upper()}-{store_id.zfill(5)}"
            clients_data = self._query_wireless_clients(device_name)
            
            return {
                "success": True,
                "device_name": device_name,
                "total_clients": len(clients_data),
                "clients_by_ssid": self._group_clients_by_ssid(clients_data),
                "clients_by_ap": self._group_clients_by_ap(clients_data),
                "wireless_clients": clients_data,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get wireless clients: {str(e)}"
            }
    
    def run_ap_health_check(self, brand: str, store_id: str) -> Dict[str, Any]:
        """
        Run comprehensive health check for store's FortiAPs
        
        Args:
            brand: Restaurant brand
            store_id: Store identifier
            
        Returns:
            Health check results
        """
        try:
            device_name = f"IBR-{brand.upper()}-{store_id.zfill(5)}"
            store_aps = self._query_store_aps(device_name)
            
            health_results = {
                "success": True,
                "device_name": device_name,
                "test_time": datetime.now().isoformat(),
                "ap_health": [],
                "overall_score": 0,
                "recommendations": []
            }
            
            total_score = 0
            for ap in store_aps:
                ap_health = self._check_ap_health(ap)
                health_results["ap_health"].append(ap_health)
                total_score += ap_health.get("health_score", 0)
            
            if store_aps:
                health_results["overall_score"] = int(total_score / len(store_aps))
            
            health_results["recommendations"] = self._generate_ap_recommendations(health_results["ap_health"])
            
            return health_results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"FortiAP health check failed: {str(e)}"
            }
    
    def get_rf_analysis(self, brand: str, store_id: str) -> Dict[str, Any]:
        """
        Get RF analysis for store's wireless environment
        
        Args:
            brand: Restaurant brand
            store_id: Store identifier
            
        Returns:
            RF analysis results
        """
        try:
            device_name = f"IBR-{brand.upper()}-{store_id.zfill(5)}"
            rf_data = self._query_rf_data(device_name)
            
            return {
                "success": True,
                "device_name": device_name,
                "rf_analysis": {
                    "channel_utilization": rf_data.get("channel_util", {}),
                    "interference_analysis": rf_data.get("interference", {}),
                    "signal_coverage": rf_data.get("coverage", {}),
                    "neighboring_aps": rf_data.get("neighbors", [])
                },
                "optimization_suggestions": self._generate_rf_recommendations(rf_data),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"RF analysis failed: {str(e)}"
            }
    
    def _query_brand_aps(self, brand: str) -> List[Dict[str, Any]]:
        """Query FortiAPs for a brand from database"""
        try:
            db_path = self.project_path / "fortiap.db"
            if not db_path.exists():
                return []
            
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                brand_prefix = f"IBR-{brand.upper()}-"
                cursor.execute("""
                    SELECT * FROM fortiaps 
                    WHERE device_name LIKE ?
                    ORDER BY device_name, ap_name
                """, (f"{brand_prefix}%",))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception:
            return []
    
    def _query_store_aps(self, device_name: str) -> List[Dict[str, Any]]:
        """Query FortiAPs for a specific store"""
        try:
            db_path = self.project_path / "fortiap.db"
            if not db_path.exists():
                return []
            
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM fortiaps 
                    WHERE device_name = ?
                    ORDER BY ap_name
                """, (device_name,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception:
            return []
    
    def _query_ap_by_serial(self, ap_serial: str) -> Optional[Dict[str, Any]]:
        """Query FortiAP by serial number"""
        try:
            db_path = self.project_path / "fortiap.db"
            if not db_path.exists():
                return None
            
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM fortiaps 
                    WHERE serial_number = ?
                """, (ap_serial,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception:
            return None
    
    def _query_wireless_clients(self, device_name: str) -> List[Dict[str, Any]]:
        """Query wireless clients for a device"""
        try:
            # This would query the actual wireless client data
            # Placeholder implementation
            return [
                {
                    "mac_address": "00:11:22:33:44:55",
                    "ssid": "Guest",
                    "ap_name": "AP1",
                    "signal_strength": -45,
                    "connection_time": "2024-01-01T10:00:00Z"
                }
            ]
            
        except Exception:
            return []
    
    def _query_rf_data(self, device_name: str) -> Dict[str, Any]:
        """Query RF data for a device"""
        try:
            # This would query actual RF analysis data
            # Placeholder implementation
            return {
                "channel_util": {"2.4GHz": 45, "5GHz": 25},
                "interference": {"sources": ["microwave", "bluetooth"]},
                "coverage": {"signal_map": "good"},
                "neighbors": []
            }
            
        except Exception:
            return {}
    
    def _generate_ap_summary(self, aps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for FortiAPs"""
        try:
            online_count = len([ap for ap in aps if ap.get('status') == 'online'])
            offline_count = len([ap for ap in aps if ap.get('status') == 'offline'])
            
            models = {}
            for ap in aps:
                model = ap.get('model', 'unknown')
                models[model] = models.get(model, 0) + 1
            
            return {
                "total": len(aps),
                "online": online_count,
                "offline": offline_count,
                "models": models,
                "uptime_avg": self._calculate_average_uptime(aps)
            }
            
        except Exception:
            return {"error": "Failed to generate AP summary"}
    
    def _check_ap_health(self, ap: Dict[str, Any]) -> Dict[str, Any]:
        """Check individual FortiAP health"""
        try:
            health_score = 100
            issues = []
            
            # Check status
            if ap.get('status') != 'online':
                health_score -= 50
                issues.append(f"AP {ap.get('ap_name')} is offline")
            
            # Check uptime
            uptime = ap.get('uptime', 0)
            if uptime < 86400:  # Less than 1 day
                health_score -= 20
                issues.append(f"AP {ap.get('ap_name')} has low uptime")
            
            # Check client count
            client_count = ap.get('client_count', 0)
            if client_count > 50:  # High client load
                health_score -= 15
                issues.append(f"AP {ap.get('ap_name')} has high client load")
            
            return {
                "ap_name": ap.get('ap_name'),
                "serial_number": ap.get('serial_number'),
                "health_score": max(0, health_score),
                "status": "healthy" if health_score >= 80 else "needs_attention",
                "issues": issues
            }
            
        except Exception:
            return {
                "ap_name": ap.get('ap_name', 'unknown'),
                "health_score": 0,
                "status": "error",
                "issues": ["Health check failed"]
            }
    
    def _generate_ap_recommendations(self, ap_health: List[Dict[str, Any]]) -> List[str]:
        """Generate FortiAP recommendations based on health checks"""
        recommendations = []
        
        offline_aps = [ap for ap in ap_health if ap.get('status') != 'online']
        if offline_aps:
            recommendations.append(f"Check connectivity for {len(offline_aps)} offline access points")
        
        low_score_aps = [ap for ap in ap_health if ap.get('health_score', 0) < 70]
        if low_score_aps:
            recommendations.append(f"Investigate {len(low_score_aps)} access points with low health scores")
        
        if not recommendations:
            recommendations.append("All FortiAPs are operating normally")
        
        return recommendations
    
    def _generate_rf_recommendations(self, rf_data: Dict[str, Any]) -> List[str]:
        """Generate RF optimization recommendations"""
        recommendations = []
        
        # Channel utilization recommendations
        channel_util = rf_data.get("channel_util", {})
        if channel_util.get("2.4GHz", 0) > 60:
            recommendations.append("Consider channel optimization for 2.4GHz band")
        if channel_util.get("5GHz", 0) > 70:
            recommendations.append("Consider channel optimization for 5GHz band")
        
        # Interference recommendations
        interference = rf_data.get("interference", {})
        if interference.get("sources"):
            recommendations.append("Address RF interference sources detected")
        
        if not recommendations:
            recommendations.append("RF environment is optimal")
        
        return recommendations
    
    def _calculate_average_uptime(self, aps: List[Dict[str, Any]]) -> float:
        """Calculate average uptime for FortiAPs"""
        try:
            if not aps:
                return 0.0
            
            total_uptime = sum(ap.get('uptime', 0) for ap in aps)
            return total_uptime / len(aps)
            
        except Exception:
            return 0.0
    
    def _group_clients_by_ssid(self, clients: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group wireless clients by SSID"""
        ssid_counts = {}
        for client in clients:
            ssid = client.get('ssid', 'unknown')
            ssid_counts[ssid] = ssid_counts.get(ssid, 0) + 1
        return ssid_counts
    
    def _group_clients_by_ap(self, clients: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group wireless clients by AP"""
        ap_counts = {}
        for client in clients:
            ap_name = client.get('ap_name', 'unknown')
            ap_counts[ap_name] = ap_counts.get(ap_name, 0) + 1
        return ap_counts