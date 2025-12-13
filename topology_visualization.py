"""
Network Topology Visualization Service
Integrates FortiGate, FortiSwitch, and Neo4j for comprehensive network mapping
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from neo4j import AsyncGraphDatabase
from pydantic import BaseModel


class NetworkNode(BaseModel):
    """Network device node"""
    id: str
    name: str
    type: str  # fortigate, fortiswitch, ap, client
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    status: str = "unknown"
    location: Optional[str] = None
    metadata: Dict[str, Any] = {}


class NetworkLink(BaseModel):
    """Network connection/link"""
    source: str
    target: str
    type: str  # ethernet, wifi, trunk, access
    interface_source: Optional[str] = None
    interface_target: Optional[str] = None
    speed: Optional[str] = None
    status: str = "unknown"


class TopologyVisualizationService:
    """Service for building and visualizing network topology"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = AsyncGraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        
    async def close(self):
        """Close Neo4j connection"""
        await self.driver.close()
    
    async def clear_topology(self):
        """Clear existing topology data"""
        async with self.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
    
    async def create_node(self, node: NetworkNode):
        """Create or update a network node in Neo4j"""
        async with self.driver.session() as session:
            query = """
            MERGE (n:Device {id: $id})
            SET n.name = $name,
                n.type = $type,
                n.ip_address = $ip_address,
                n.mac_address = $mac_address,
                n.model = $model,
                n.serial = $serial,
                n.status = $status,
                n.location = $location,
                n.updated_at = datetime(),
                n.metadata = $metadata
            RETURN n
            """
            await session.run(
                query,
                id=node.id,
                name=node.name,
                type=node.type,
                ip_address=node.ip_address,
                mac_address=node.mac_address,
                model=node.model,
                serial=node.serial,
                status=node.status,
                location=node.location,
                metadata=node.metadata
            )
    
    async def create_link(self, link: NetworkLink):
        """Create a link between two devices"""
        async with self.driver.session() as session:
            query = """
            MATCH (a:Device {id: $source})
            MATCH (b:Device {id: $target})
            MERGE (a)-[r:CONNECTED_TO {type: $type}]->(b)
            SET r.interface_source = $interface_source,
                r.interface_target = $interface_target,
                r.speed = $speed,
                r.status = $status,
                r.updated_at = datetime()
            RETURN r
            """
            await session.run(
                query,
                source=link.source,
                target=link.target,
                type=link.type,
                interface_source=link.interface_source,
                interface_target=link.interface_target,
                speed=link.speed,
                status=link.status
            )
    
    async def build_topology_from_fortigate(self, fortigate_data: Dict[str, Any]):
        """
        Build topology from FortiGate API data
        
        Expected format:
        {
            'switches': [...],
            'interfaces': [...],
            'detected_devices': [...]
        }
        """
        # Create FortiGate node
        fortigate = NetworkNode(
            id="fortigate-primary",
            name=fortigate_data.get("hostname", "FortiGate"),
            type="fortigate",
            ip_address=fortigate_data.get("ip_address"),
            model=fortigate_data.get("model"),
            serial=fortigate_data.get("serial"),
            status="online",
            metadata=fortigate_data.get("metadata", {})
        )
        await self.create_node(fortigate)
        
        # Create switches
        for switch_data in fortigate_data.get("switches", []):
            switch = NetworkNode(
                id=f"switch-{switch_data['serial']}",
                name=switch_data.get("name", switch_data["serial"]),
                type="fortiswitch",
                ip_address=switch_data.get("ip_address"),
                mac_address=switch_data.get("mac_address"),
                model=switch_data.get("model"),
                serial=switch_data["serial"],
                status=switch_data.get("status", "unknown"),
                location=switch_data.get("location"),
                metadata={
                    "port_count": switch_data.get("port_count"),
                    "firmware": switch_data.get("version"),
                }
            )
            await self.create_node(switch)
            
            # Link switch to FortiGate
            link = NetworkLink(
                source="fortigate-primary",
                target=switch.id,
                type="management",
                interface_source=switch_data.get("fortigate_port"),
                status="up"
            )
            await self.create_link(link)
        
        # Create detected devices (APs, clients, etc.)
        for device_data in fortigate_data.get("detected_devices", []):
            device = NetworkNode(
                id=f"device-{device_data['mac_address']}",
                name=device_data.get("hostname", device_data["mac_address"]),
                type=device_data.get("type", "client"),
                ip_address=device_data.get("ip_address"),
                mac_address=device_data["mac_address"],
                status=device_data.get("status", "unknown"),
                metadata=device_data.get("metadata", {})
            )
            await self.create_node(device)
            
            # Link to parent switch or FortiGate
            parent_id = device_data.get("parent_device", "fortigate-primary")
            link = NetworkLink(
                source=parent_id,
                target=device.id,
                type=device_data.get("connection_type", "ethernet"),
                interface_source=device_data.get("parent_port"),
                status="up"
            )
            await self.create_link(link)
    
    async def get_topology_graph(self) -> Dict[str, Any]:
        """Get complete topology as graph structure for visualization"""
        async with self.driver.session() as session:
            # Get all nodes
            nodes_result = await session.run("""
                MATCH (n:Device)
                RETURN n.id as id, n.name as name, n.type as type,
                       n.ip_address as ip_address, n.status as status,
                       n.model as model, n.location as location
            """)
            nodes = [dict(record) async for record in nodes_result]
            
            # Get all links
            links_result = await session.run("""
                MATCH (a:Device)-[r:CONNECTED_TO]->(b:Device)
                RETURN a.id as source, b.id as target, r.type as type,
                       r.interface_source as interface_source,
                       r.interface_target as interface_target,
                       r.status as status
            """)
            links = [dict(record) async for record in links_result]
            
            return {
                "nodes": nodes,
                "links": links,
                "metadata": {
                    "node_count": len(nodes),
                    "link_count": len(links),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
    
    async def find_path(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        """Find shortest path between two devices"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH path = shortestPath(
                    (a:Device {id: $source})-[*]-(b:Device {id: $target})
                )
                RETURN [node in nodes(path) | {
                    id: node.id, 
                    name: node.name,
                    type: node.type
                }] as nodes,
                [rel in relationships(path) | {
                    type: rel.type,
                    status: rel.status
                }] as links
            """, source=source_id, target=target_id)
            
            record = await result.single()
            if record:
                return {
                    "nodes": record["nodes"],
                    "links": record["links"]
                }
            return {"nodes": [], "links": []}
    
    async def get_device_neighbors(self, device_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get neighboring devices up to specified depth"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (center:Device {id: $device_id})
                OPTIONAL MATCH path = (center)-[*1..{depth}]-(neighbor:Device)
                WITH center, collect(DISTINCT neighbor) as neighbors,
                     collect(DISTINCT path) as paths
                RETURN center.id as device_id,
                       [n in neighbors | {
                           id: n.id,
                           name: n.name,
                           type: n.type,
                           status: n.status
                       }] as neighbors
            """.replace("{depth}", str(depth)), device_id=device_id)
            
            record = await result.single()
            if record:
                return dict(record)
            return {"device_id": device_id, "neighbors": []}
    
    async def analyze_network_health(self) -> Dict[str, Any]:
        """Analyze overall network health metrics"""
        async with self.driver.session() as session:
            # Count devices by type and status
            type_result = await session.run("""
                MATCH (n:Device)
                RETURN n.type as type, n.status as status, count(*) as count
            """)
            device_stats = [dict(record) async for record in type_result]
            
            # Find disconnected devices
            isolated_result = await session.run("""
                MATCH (n:Device)
                WHERE NOT (n)--()
                RETURN collect(n.id) as isolated_devices
            """)
            isolated = await isolated_result.single()
            
            # Find critical paths (devices with high connectivity)
            critical_result = await session.run("""
                MATCH (n:Device)-[r]-()
                WITH n, count(r) as connections
                WHERE connections > 5
                RETURN n.id as device_id, n.name as name, connections
                ORDER BY connections DESC
                LIMIT 10
            """)
            critical_devices = [dict(record) async for record in critical_result]
            
            return {
                "device_statistics": device_stats,
                "isolated_devices": isolated["isolated_devices"] if isolated else [],
                "critical_devices": critical_devices,
                "analyzed_at": datetime.utcnow().isoformat()
            }


# Example usage for FastAPI integration
async def example_usage():
    """Example of how to use the topology service"""
    service = TopologyVisualizationService(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="neo4j_password"
    )
    
    try:
        # Build topology from FortiGate data
        fortigate_data = {
            "hostname": "FG-PRIMARY",
            "ip_address": "192.168.0.254",
            "model": "FortiGate-100F",
            "serial": "FG100F3G12345678",
            "switches": [
                {
                    "serial": "FS108E4Q20123456",
                    "name": "CORE-SW-01",
                    "model": "FS-108E",
                    "status": "authorized",
                    "port_count": 8,
                    "version": "7.2.1",
                    "fortigate_port": "port1"
                }
            ],
            "detected_devices": []
        }
        
        await service.build_topology_from_fortigate(fortigate_data)
        
        # Get topology for visualization
        topology = await service.get_topology_graph()
        print(f"Topology: {len(topology['nodes'])} nodes, {len(topology['links'])} links")
        
        # Analyze health
        health = await service.analyze_network_health()
        print(f"Health analysis complete")
        
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
