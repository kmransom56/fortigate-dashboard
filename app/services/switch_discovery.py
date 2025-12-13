"""
Switch Discovery and Management Service
Automated discovery, monitoring, and management of FortiSwitch devices
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import asyncio
import aiohttp


class SwitchPort(BaseModel):
    """FortiSwitch port information"""
    port_number: int
    name: str
    status: str  # up, down, disabled
    speed: str  # 1G, 10G, etc.
    duplex: str  # full, half
    vlan: Optional[int] = None
    poe_enabled: bool = False
    poe_power: Optional[float] = None  # Watts
    description: Optional[str] = None
    connected_device: Optional[str] = None
    mac_address: Optional[str] = None


class ManagedSwitch(BaseModel):
    """Complete FortiSwitch device information"""
    serial: str
    name: str
    model: str
    version: str
    status: str  # authorized, unauthorized, offline
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    location: Optional[str] = None
    uptime: Optional[int] = None  # seconds
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    temperature: Optional[float] = None
    ports: List[SwitchPort] = []
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class SwitchDiscoveryService:
    """Service for discovering and managing FortiSwitch devices"""
    
    def __init__(
        self,
        fortigate_host: str,
        fortigate_port: int,
        api_token: Optional[str] = None,
        redis_client: Optional[Any] = None
    ):
        self.fortigate_host = fortigate_host
        self.fortigate_port = fortigate_port
        self.api_token = api_token
        self.redis = redis_client
        self.base_url = f"https://{fortigate_host}:{fortigate_port}/api/v2"
        
    async def discover_switches(self) -> List[ManagedSwitch]:
        """Discover all managed switches from FortiGate"""
        switches = []
        
        # Get managed switches
        managed_switches = await self._api_request(
            "cmdb/switch-controller/managed-switch"
        )
        
        for switch_data in managed_switches.get("results", []):
            # Get detailed port information
            ports = await self._get_switch_ports(switch_data["switch-id"])
            
            # Get real-time status
            status = await self._get_switch_status(switch_data["switch-id"])
            
            switch = ManagedSwitch(
                serial=switch_data["switch-id"],
                name=switch_data.get("name", switch_data["switch-id"]),
                model=switch_data.get("fsw-wan1-peer", {}).get("model", "Unknown"),
                version=switch_data.get("version", "Unknown"),
                status=switch_data.get("status", "unknown"),
                ip_address=status.get("ip_address"),
                mac_address=status.get("mac_address"),
                location=switch_data.get("description"),
                uptime=status.get("uptime"),
                cpu_usage=status.get("cpu", {}).get("usage"),
                memory_usage=status.get("memory", {}).get("usage"),
                temperature=status.get("temperature"),
                ports=ports
            )
            
            switches.append(switch)
            
            # Cache in Redis
            if self.redis:
                await self._cache_switch(switch)
        
        return switches
    
    async def _get_switch_ports(self, switch_id: str) -> List[SwitchPort]:
        """Get detailed port information for a switch"""
        ports = []
        
        port_data = await self._api_request(
            f"monitor/switch-controller/managed-switch/port-stats?mkey={switch_id}"
        )
        
        for port in port_data.get("results", []):
            switch_port = SwitchPort(
                port_number=port.get("port_number", 0),
                name=port.get("name", f"port{port.get('port_number')}"),
                status=port.get("status", "unknown"),
                speed=port.get("speed", "unknown"),
                duplex=port.get("duplex", "unknown"),
                vlan=port.get("vlan"),
                poe_enabled=port.get("poe_enabled", False),
                poe_power=port.get("poe_power_watts"),
                description=port.get("description"),
                connected_device=port.get("lldp_neighbor", {}).get("system_name"),
                mac_address=port.get("mac_address")
            )
            ports.append(switch_port)
        
        return ports
    
    async def _get_switch_status(self, switch_id: str) -> Dict[str, Any]:
        """Get real-time switch status"""
        status = await self._api_request(
            f"monitor/switch-controller/managed-switch/status?mkey={switch_id}"
        )
        return status.get("results", [{}])[0] if status.get("results") else {}
    
    async def _api_request(self, endpoint: str) -> Dict[str, Any]:
        """Make API request to FortiGate"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"HTTP {response.status}", "results": []}
        except Exception as e:
            return {"error": str(e), "results": []}
    
    async def _cache_switch(self, switch: ManagedSwitch):
        """Cache switch data in Redis"""
        if not self.redis:
            return
        
        key = f"switch:{switch.serial}"
        await self.redis.setex(
            key,
            3600,  # 1 hour TTL
            switch.model_dump_json()
        )
    
    async def get_cached_switches(self) -> List[ManagedSwitch]:
        """Get all cached switches from Redis"""
        if not self.redis:
            return []
        
        keys = await self.redis.keys("switch:*")
        switches = []
        
        for key in keys:
            data = await self.redis.get(key)
            if data:
                switch = ManagedSwitch.model_validate_json(data)
                switches.append(switch)
        
        return switches
    
    async def monitor_switch_health(self, switch_id: str) -> Dict[str, Any]:
        """Monitor health metrics for a specific switch"""
        status = await self._get_switch_status(switch_id)
        
        health = {
            "switch_id": switch_id,
            "healthy": True,
            "issues": [],
            "metrics": {}
        }
        
        # Check CPU usage
        cpu_usage = status.get("cpu", {}).get("usage", 0)
        health["metrics"]["cpu_usage"] = cpu_usage
        if cpu_usage > 80:
            health["healthy"] = False
            health["issues"].append(f"High CPU usage: {cpu_usage}%")
        
        # Check memory usage
        memory_usage = status.get("memory", {}).get("usage", 0)
        health["metrics"]["memory_usage"] = memory_usage
        if memory_usage > 90:
            health["healthy"] = False
            health["issues"].append(f"High memory usage: {memory_usage}%")
        
        # Check temperature
        temperature = status.get("temperature")
        if temperature:
            health["metrics"]["temperature"] = temperature
            if temperature > 70:
                health["healthy"] = False
                health["issues"].append(f"High temperature: {temperature}°C")
        
        # Check port status
        ports = await self._get_switch_ports(switch_id)
        down_ports = [p for p in ports if p.status == "down"]
        health["metrics"]["total_ports"] = len(ports)
        health["metrics"]["down_ports"] = len(down_ports)
        
        if len(down_ports) > len(ports) * 0.3:  # More than 30% ports down
            health["issues"].append(f"{len(down_ports)} ports are down")
        
        return health
    
    async def auto_configure_switch(
        self,
        switch_id: str,
        template: str = "standard"
    ) -> Dict[str, Any]:
        """
        Auto-configure a switch based on template
        Templates: standard, datacenter, edge, access
        """
        templates = {
            "standard": {
                "storm_control": True,
                "dhcp_snooping": True,
                "poe_schedule": "24x7",
                "stp_enabled": True
            },
            "datacenter": {
                "storm_control": True,
                "dhcp_snooping": True,
                "poe_schedule": "disabled",
                "stp_enabled": True,
                "jumbo_frames": True,
                "flow_control": True
            },
            "edge": {
                "storm_control": True,
                "dhcp_snooping": True,
                "poe_schedule": "business_hours",
                "stp_enabled": True,
                "port_security": True
            }
        }
        
        config = templates.get(template, templates["standard"])
        
        # Apply configuration via FortiGate API
        result = await self._api_request(
            f"cmdb/switch-controller/managed-switch/{switch_id}",
            method="PUT",
            data=config
        )
        
        return {
            "switch_id": switch_id,
            "template": template,
            "applied_config": config,
            "success": "error" not in result
        }
    
    async def scan_for_rogue_devices(self) -> List[Dict[str, Any]]:
        """Scan for unauthorized devices on the network"""
        rogue_devices = []
        
        # Get detected devices
        detected = await self._api_request(
            "monitor/switch-controller/detected-device"
        )
        
        for device in detected.get("results", []):
            if device.get("status") == "unauthorized":
                rogue_devices.append({
                    "mac_address": device.get("mac"),
                    "detected_on_switch": device.get("switch_id"),
                    "detected_on_port": device.get("port"),
                    "first_seen": device.get("first_seen"),
                    "last_seen": device.get("last_seen"),
                    "manufacturer": device.get("manufacturer")
                })
        
        return rogue_devices
    
    async def generate_switch_report(self, switches: List[ManagedSwitch]) -> Dict[str, Any]:
        """Generate comprehensive report of all switches"""
        total_ports = sum(len(s.ports) for s in switches)
        active_ports = sum(
            len([p for p in s.ports if p.status == "up"])
            for s in switches
        )
        poe_ports = sum(
            len([p for p in s.ports if p.poe_enabled])
            for s in switches
        )
        
        return {
            "summary": {
                "total_switches": len(switches),
                "authorized": len([s for s in switches if s.status == "authorized"]),
                "offline": len([s for s in switches if s.status == "offline"]),
                "total_ports": total_ports,
                "active_ports": active_ports,
                "port_utilization": (active_ports / total_ports * 100) if total_ports > 0 else 0,
                "poe_enabled_ports": poe_ports
            },
            "switches": [
                {
                    "serial": s.serial,
                    "name": s.name,
                    "model": s.model,
                    "status": s.status,
                    "uptime": s.uptime,
                    "port_count": len(s.ports),
                    "active_ports": len([p for p in s.ports if p.status == "up"])
                }
                for s in switches
            ],
            "generated_at": datetime.utcnow().isoformat()
        }


# Example usage
async def example_usage():
    """Example of switch discovery"""
    service = SwitchDiscoveryService(
        fortigate_host="192.168.0.254",
        fortigate_port=10443,
        api_token="your_api_token_here"
    )
    
    # Discover all switches
    switches = await service.discover_switches()
    print(f"Discovered {len(switches)} switches")
    
    # Monitor health
    for switch in switches:
        health = await service.monitor_switch_health(switch.serial)
        if not health["healthy"]:
            print(f"Switch {switch.name} has issues: {health['issues']}")
    
    # Generate report
    report = await service.generate_switch_report(switches)
    print(f"Report: {report['summary']}")
    
    # Scan for rogue devices
    rogues = await service.scan_for_rogue_devices()
    if rogues:
        print(f"Found {len(rogues)} rogue devices!")


if __name__ == "__main__":
    asyncio.run(example_usage())
