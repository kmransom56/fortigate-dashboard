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
            "static/scraped_map.html"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found scraped HTML at: {path}")
                return path
                
        logger.warning("No scraped HTML file found, will use fallback data")
        return None

    def get_topology_data(self) -> Dict[str, Any]:
        """Get topology data from scraped HTML or fallback demo data"""
        if self.scraped_html_path and os.path.exists(self.scraped_html_path):
            try:
                return self._parse_scraped_html()
            except Exception as e:
                logger.error(f"Failed to parse scraped HTML: {e}")
        
        logger.info("Using fallback demo data")
        return self._get_fallback_data()
    
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
                logger.info(f"Found {len(device_elements)} devices using selector: {selector}")
                break
                
        for i, device in enumerate(device_elements):
            device_data = self._extract_device_data(device, i)
            if device_data:
                devices.append(device_data)
        
        # Enhanced connection parsing
        connection_selectors = [".connection-link", ".topology-link", ".link", ".connection"]
        
        for selector in connection_selectors:
            connection_elements = soup.select(selector)
            if connection_elements:
                logger.info(f"Found {len(connection_elements)} connections using selector: {selector}")
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
                "connection_count": len(connections)
            }
        }
    
    def _extract_device_data(self, device_element, index: int) -> Optional[Dict[str, Any]]:
        """Extract device data from HTML element"""
        try:
            device_id = device_element.get("id") or device_element.get("data-id") or f"device_{index}"
            device_type = (device_element.get("data-type") or 
                          device_element.get("class", [None])[0] or 
                          "endpoint").lower()
            
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
            x_pos = int(device_element.get("data-x") or device_element.get("x") or 100 + index * 200)
            y_pos = int(device_element.get("data-y") or device_element.get("y") or 100 + index * 150)
            
            # Extract device count
            device_count = int(device_element.get("data-count") or 1)
            
            # Get device name
            name = (device_element.get("data-name") or 
                   device_element.get_text(strip=True) or 
                   f"{device_type.title()} {index + 1}")
            
            # Color mapping
            color_map = {
                "fortigate": "#2196f3",
                "fortiswitch": "#ff9800", 
                "endpoint": "#4caf50",
                "server": "#9c27b0"
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
                    "manufacturer": "Fortinet" if device_type.startswith("forti") else "Generic"
                }
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
                "status": conn_element.get("data-status", "active")
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
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return enhanced fallback demo data"""
        devices = [
            {
                "id": "fortigate_main",
                "type": "fortigate", 
                "name": "FortiGate Main",
                "position": {"x": 400, "y": 100},
                "details": {
                    "deviceCount": 1, 
                    "color": "#2196f3",
                    "status": "online",
                    "manufacturer": "Fortinet"
                }
            },
            {
                "id": "switch_1",
                "type": "fortiswitch",
                "name": "FortiSwitch 1", 
                "position": {"x": 300, "y": 300},
                "details": {
                    "deviceCount": 3,
                    "color": "#ff9800",
                    "status": "online",
                    "manufacturer": "Fortinet"
                }
            },
            {
                "id": "switch_2", 
                "type": "fortiswitch",
                "name": "FortiSwitch 2",
                "position": {"x": 500, "y": 300},
                "details": {
                    "deviceCount": 6,
                    "color": "#ff9800", 
                    "status": "online",
                    "manufacturer": "Fortinet"
                }
            },
            {
                "id": "endpoint_1",
                "type": "endpoint",
                "name": "Endpoints",
                "position": {"x": 400, "y": 500},
                "details": {
                    "deviceCount": 12,
                    "color": "#4caf50",
                    "status": "online", 
                    "manufacturer": "Generic"
                }
            }
        ]
        
        connections = [
            {"from": "fortigate_main", "to": "switch_1", "type": "ethernet", "status": "active"},
            {"from": "fortigate_main", "to": "switch_2", "type": "ethernet", "status": "active"},
            {"from": "switch_1", "to": "endpoint_1", "type": "ethernet", "status": "active"},
            {"from": "switch_2", "to": "endpoint_1", "type": "ethernet", "status": "active"}
        ]
        
        return {
            "devices": devices,
            "connections": connections,
            "metadata": {
                "source": "fallback",
                "timestamp": "demo",
                "device_count": len(devices),
                "connection_count": len(connections)
            }
        }

# Service instance
_scraped_topology_service = None

def get_scraped_topology_service() -> ScrapedTopologyService:
    """Get or create scraped topology service instance"""
    global _scraped_topology_service
    if _scraped_topology_service is None:
        _scraped_topology_service = ScrapedTopologyService()
    return _scraped_topology_service
