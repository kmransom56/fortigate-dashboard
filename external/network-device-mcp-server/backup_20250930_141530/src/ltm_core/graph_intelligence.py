"""
Network Graph Intelligence Engine
Advanced graph-based analysis for network topology and relationships
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum

# Note: Neo4j integration would be added when database is available
# For now, we'll use in-memory graph structures with Neo4j-compatible design

class NodeType(Enum):
    """Types of nodes in the network graph"""
    BRAND = "brand"
    STORE = "store"
    DEVICE = "device"
    SECURITY_EVENT = "security_event"
    PERFORMANCE_EVENT = "performance_event"
    CONFIGURATION = "configuration"
    USER = "user"
    NETWORK_SEGMENT = "network_segment"
    THREAT_ACTOR = "threat_actor"

class RelationshipType(Enum):
    """Types of relationships in the network graph"""
    BELONGS_TO = "belongs_to"
    MANAGES = "manages"
    CONNECTS_TO = "connects_to"
    AFFECTS = "affects"
    SIMILAR_TO = "similar_to"
    CAUSED_BY = "caused_by"
    LEADS_TO = "leads_to"
    CORRELATES_WITH = "correlates_with"
    ORIGINATED_FROM = "originated_from"
    TARGETS = "targets"

@dataclass
class GraphNode:
    """Represents a node in the network graph"""
    node_id: str
    node_type: NodeType
    properties: Dict[str, Any]
    labels: List[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class GraphRelationship:
    """Represents a relationship in the network graph"""
    relationship_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any]
    strength: float  # 0.0 to 1.0
    created_at: datetime
    updated_at: datetime

@dataclass
class PathAnalysis:
    """Analysis of paths between nodes"""
    source_node: str
    target_node: str
    paths: List[List[str]]  # List of node sequences
    shortest_path_length: int
    relationship_types: List[RelationshipType]
    risk_score: float
    analysis_summary: str

@dataclass
class ClusterAnalysis:
    """Analysis of node clusters"""
    cluster_id: str
    cluster_type: str
    nodes: List[str]
    central_nodes: List[str]  # Most connected nodes
    cluster_score: float
    common_attributes: Dict[str, Any]
    risk_factors: List[str]

class NetworkGraphIntelligence:
    """
    Graph-based intelligence engine for network analysis
    Analyzes relationships, patterns, and propagation paths
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Network Graph Intelligence Engine
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # In-memory graph storage (would be replaced with Neo4j)
        self.nodes: Dict[str, GraphNode] = {}
        self.relationships: Dict[str, GraphRelationship] = {}
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)
        
        # Analysis parameters
        self.max_path_length = self.config.get('max_path_length', 6)
        self.min_relationship_strength = self.config.get('min_relationship_strength', 0.3)
        
        # Initialize with basic network structure
        self._initialize_base_topology()
    
    def add_node(self, node: GraphNode) -> bool:
        """Add a node to the graph"""
        try:
            self.nodes[node.node_id] = node
            if node.node_id not in self.adjacency_list:
                self.adjacency_list[node.node_id] = []
            
            self.logger.debug(f"Added node: {node.node_id} ({node.node_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding node {node.node_id}: {e}")
            return False
    
    def add_relationship(self, relationship: GraphRelationship) -> bool:
        """Add a relationship to the graph"""
        try:
            # Ensure both nodes exist
            if (relationship.source_node_id not in self.nodes or 
                relationship.target_node_id not in self.nodes):
                self.logger.warning(f"Cannot add relationship: missing nodes")
                return False
            
            self.relationships[relationship.relationship_id] = relationship
            
            # Update adjacency list
            self.adjacency_list[relationship.source_node_id].append(relationship.target_node_id)
            
            # For undirected relationships, add reverse edge
            if relationship.relationship_type in [RelationshipType.SIMILAR_TO, 
                                                RelationshipType.CORRELATES_WITH]:
                self.adjacency_list[relationship.target_node_id].append(relationship.source_node_id)
            
            self.logger.debug(f"Added relationship: {relationship.source_node_id} -> {relationship.target_node_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding relationship {relationship.relationship_id}: {e}")
            return False
    
    def analyze_attack_paths(self, 
                           source_entities: List[str] = None,
                           target_entities: List[str] = None) -> List[PathAnalysis]:
        """
        Analyze potential attack paths through the network
        
        Args:
            source_entities: Starting points (e.g., compromised devices)
            target_entities: Target entities (e.g., critical systems)
            
        Returns:
            List of path analyses
        """
        try:
            path_analyses = []
            
            # If no source specified, use devices with recent security events
            if source_entities is None:
                source_entities = self._find_compromised_entities()
            
            # If no targets specified, use critical infrastructure
            if target_entities is None:
                target_entities = self._find_critical_entities()
            
            for source in source_entities:
                for target in target_entities:
                    if source == target:
                        continue
                    
                    paths = self._find_attack_paths(source, target)
                    if paths:
                        analysis = PathAnalysis(
                            source_node=source,
                            target_node=target,
                            paths=paths,
                            shortest_path_length=min(len(path) for path in paths) if paths else 0,
                            relationship_types=self._extract_path_relationships(paths[0] if paths else []),
                            risk_score=self._calculate_path_risk(paths[0] if paths else [], source, target),
                            analysis_summary=self._generate_path_summary(source, target, paths)
                        )
                        path_analyses.append(analysis)
            
            # Sort by risk score
            path_analyses.sort(key=lambda p: p.risk_score, reverse=True)
            
            self.logger.info(f"Analyzed {len(path_analyses)} attack paths")
            return path_analyses
            
        except Exception as e:
            self.logger.error(f"Error analyzing attack paths: {e}")
            return []
    
    def find_similar_entities(self, 
                            entity_id: str,
                            similarity_threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Find entities similar to the given entity
        
        Args:
            entity_id: Entity to find similarities for
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (entity_id, similarity_score) tuples
        """
        try:
            if entity_id not in self.nodes:
                return []
            
            target_node = self.nodes[entity_id]
            similar_entities = []
            
            # Compare with nodes of same type
            for node_id, node in self.nodes.items():
                if (node_id != entity_id and 
                    node.node_type == target_node.node_type):
                    
                    similarity = self._calculate_node_similarity(target_node, node)
                    if similarity >= similarity_threshold:
                        similar_entities.append((node_id, similarity))
            
            # Sort by similarity
            similar_entities.sort(key=lambda x: x[1], reverse=True)
            
            return similar_entities
            
        except Exception as e:
            self.logger.error(f"Error finding similar entities for {entity_id}: {e}")
            return []
    
    def analyze_impact_propagation(self, 
                                 incident_entity: str,
                                 max_hops: int = 3) -> Dict[str, Any]:
        """
        Analyze how an incident might propagate through the network
        
        Args:
            incident_entity: Entity where incident occurred
            max_hops: Maximum propagation distance
            
        Returns:
            Impact propagation analysis
        """
        try:
            if incident_entity not in self.nodes:
                return {}
            
            # BFS to find potentially affected entities
            affected_entities = []
            visited = set()
            queue = deque([(incident_entity, 0)])  # (entity, hop_count)
            
            while queue:
                current_entity, hop_count = queue.popleft()
                
                if current_entity in visited or hop_count > max_hops:
                    continue
                
                visited.add(current_entity)
                
                if hop_count > 0:  # Don't include the source entity
                    risk_score = self._calculate_propagation_risk(
                        incident_entity, current_entity, hop_count
                    )
                    affected_entities.append({
                        'entity_id': current_entity,
                        'entity_type': self.nodes[current_entity].node_type.value,
                        'hop_distance': hop_count,
                        'risk_score': risk_score,
                        'properties': self.nodes[current_entity].properties
                    })
                
                # Add neighbors to queue
                for neighbor in self.adjacency_list.get(current_entity, []):
                    if neighbor not in visited:
                        queue.append((neighbor, hop_count + 1))
            
            # Sort by risk score
            affected_entities.sort(key=lambda e: e['risk_score'], reverse=True)
            
            # Calculate summary statistics
            total_stores_affected = len([e for e in affected_entities 
                                       if e['entity_type'] == 'store'])
            total_devices_affected = len([e for e in affected_entities 
                                        if e['entity_type'] == 'device'])
            high_risk_entities = [e for e in affected_entities if e['risk_score'] > 0.7]
            
            return {
                'source_entity': incident_entity,
                'total_affected_entities': len(affected_entities),
                'stores_affected': total_stores_affected,
                'devices_affected': total_devices_affected,
                'high_risk_entities': len(high_risk_entities),
                'max_propagation_distance': max([e['hop_distance'] for e in affected_entities]) if affected_entities else 0,
                'affected_entities': affected_entities[:20],  # Top 20 by risk
                'propagation_summary': self._generate_propagation_summary(
                    incident_entity, affected_entities
                ),
                'recommendations': self._generate_containment_recommendations(
                    incident_entity, affected_entities
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing impact propagation for {incident_entity}: {e}")
            return {}
    
    def find_network_clusters(self, 
                            cluster_algorithm: str = 'connected_components') -> List[ClusterAnalysis]:
        """
        Find clusters in the network graph
        
        Args:
            cluster_algorithm: Algorithm to use for clustering
            
        Returns:
            List of cluster analyses
        """
        try:
            clusters = []
            
            if cluster_algorithm == 'connected_components':
                components = self._find_connected_components()
                
                for i, component in enumerate(components):
                    if len(component) >= 3:  # Only analyze meaningful clusters
                        cluster = self._analyze_cluster(f"component_{i}", component)
                        if cluster:
                            clusters.append(cluster)
            
            elif cluster_algorithm == 'brand_based':
                # Group by brand
                brand_clusters = defaultdict(list)
                for node_id, node in self.nodes.items():
                    if node.node_type in [NodeType.STORE, NodeType.DEVICE]:
                        brand = node.properties.get('brand', 'unknown')
                        brand_clusters[brand].append(node_id)
                
                for brand, nodes in brand_clusters.items():
                    if len(nodes) >= 3:
                        cluster = self._analyze_cluster(f"brand_{brand}", nodes)
                        if cluster:
                            clusters.append(cluster)
            
            # Sort clusters by score
            clusters.sort(key=lambda c: c.cluster_score, reverse=True)
            
            self.logger.info(f"Found {len(clusters)} network clusters")
            return clusters
            
        except Exception as e:
            self.logger.error(f"Error finding network clusters: {e}")
            return []
    
    def get_entity_influence_score(self, entity_id: str) -> float:
        """
        Calculate influence score for an entity based on its network position
        
        Args:
            entity_id: Entity to analyze
            
        Returns:
            Influence score (0.0 to 1.0)
        """
        try:
            if entity_id not in self.nodes:
                return 0.0
            
            # Calculate various centrality measures
            degree_centrality = len(self.adjacency_list.get(entity_id, [])) / max(len(self.nodes) - 1, 1)
            
            # Betweenness centrality (simplified)
            betweenness = self._calculate_betweenness_centrality(entity_id)
            
            # PageRank-like score (simplified)
            authority_score = self._calculate_authority_score(entity_id)
            
            # Combine scores
            influence_score = (degree_centrality * 0.4 + 
                             betweenness * 0.3 + 
                             authority_score * 0.3)
            
            return min(influence_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating influence score for {entity_id}: {e}")
            return 0.0
    
    def _initialize_base_topology(self):
        """Initialize basic network topology structure"""
        try:
            # Create brand nodes
            brands = ['BWW', 'ARBYS', 'SONIC']
            for brand in brands:
                brand_node = GraphNode(
                    node_id=f"brand_{brand}",
                    node_type=NodeType.BRAND,
                    properties={'name': brand, 'type': 'restaurant_chain'},
                    labels=[brand],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.add_node(brand_node)
            
            # Create some example store and device nodes
            for brand in brands:
                for store_id in ['155', '234', '789']:
                    # Store node
                    store_node = GraphNode(
                        node_id=f"store_{brand}_{store_id}",
                        node_type=NodeType.STORE,
                        properties={
                            'brand': brand,
                            'store_id': store_id,
                            'location': f"{brand} Store {store_id}"
                        },
                        labels=[brand, 'store'],
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self.add_node(store_node)
                    
                    # Relationship: Store belongs to Brand
                    brand_rel = GraphRelationship(
                        relationship_id=f"rel_brand_{brand}_{store_id}",
                        source_node_id=f"store_{brand}_{store_id}",
                        target_node_id=f"brand_{brand}",
                        relationship_type=RelationshipType.BELONGS_TO,
                        properties={},
                        strength=1.0,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self.add_relationship(brand_rel)
                    
                    # Device nodes for each store
                    for device_name in ['FortiGate-01', 'Switch-01', 'AP-01']:
                        device_node = GraphNode(
                            node_id=f"device_{brand}_{store_id}_{device_name}",
                            node_type=NodeType.DEVICE,
                            properties={
                                'brand': brand,
                                'store_id': store_id,
                                'device_name': device_name,
                                'device_type': device_name.split('-')[0]
                            },
                            labels=[brand, 'device', device_name.split('-')[0]],
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        self.add_node(device_node)
                        
                        # Relationship: Device belongs to Store
                        device_rel = GraphRelationship(
                            relationship_id=f"rel_device_{brand}_{store_id}_{device_name}",
                            source_node_id=f"device_{brand}_{store_id}_{device_name}",
                            target_node_id=f"store_{brand}_{store_id}",
                            relationship_type=RelationshipType.BELONGS_TO,
                            properties={},
                            strength=1.0,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        self.add_relationship(device_rel)
            
        except Exception as e:
            self.logger.error(f"Error initializing base topology: {e}")
    
    def _find_compromised_entities(self) -> List[str]:
        """Find entities that might be compromised"""
        # This would typically query for entities with recent security events
        # For now, return a sample of device entities
        compromised = []
        for node_id, node in self.nodes.items():
            if (node.node_type == NodeType.DEVICE and 
                'security' in str(node.properties).lower()):
                compromised.append(node_id)
        
        # If no specific compromised entities, return some device samples
        if not compromised:
            compromised = [node_id for node_id, node in self.nodes.items() 
                          if node.node_type == NodeType.DEVICE][:3]
        
        return compromised
    
    def _find_critical_entities(self) -> List[str]:
        """Find critical entities that should be protected"""
        critical = []
        for node_id, node in self.nodes.items():
            if (node.node_type == NodeType.DEVICE and 
                'FortiGate' in node.properties.get('device_name', '')):
                critical.append(node_id)
        
        return critical
    
    def _find_attack_paths(self, source: str, target: str) -> List[List[str]]:
        """Find potential attack paths between source and target"""
        try:
            paths = []
            visited = set()
            current_path = [source]
            
            self._dfs_paths(source, target, current_path, visited, paths)
            
            # Filter paths by length and relevance
            filtered_paths = [path for path in paths 
                            if len(path) <= self.max_path_length]
            
            return filtered_paths[:5]  # Return top 5 paths
            
        except Exception as e:
            self.logger.error(f"Error finding attack paths from {source} to {target}: {e}")
            return []
    
    def _dfs_paths(self, current: str, target: str, path: List[str], 
                   visited: Set[str], all_paths: List[List[str]], depth: int = 0):
        """Depth-first search for paths"""
        if depth > self.max_path_length:
            return
        
        if current == target:
            all_paths.append(path.copy())
            return
        
        visited.add(current)
        
        for neighbor in self.adjacency_list.get(current, []):
            if neighbor not in visited:
                path.append(neighbor)
                self._dfs_paths(neighbor, target, path, visited, all_paths, depth + 1)
                path.pop()
        
        visited.remove(current)
    
    def _extract_path_relationships(self, path: List[str]) -> List[RelationshipType]:
        """Extract relationship types along a path"""
        relationships = []
        
        for i in range(len(path) - 1):
            source, target = path[i], path[i + 1]
            
            # Find relationship between these nodes
            for rel in self.relationships.values():
                if ((rel.source_node_id == source and rel.target_node_id == target) or
                    (rel.source_node_id == target and rel.target_node_id == source)):
                    relationships.append(rel.relationship_type)
                    break
        
        return relationships
    
    def _calculate_path_risk(self, path: List[str], source: str, target: str) -> float:
        """Calculate risk score for an attack path"""
        if not path or len(path) < 2:
            return 0.0
        
        # Base risk factors
        path_length_factor = 1.0 / len(path)  # Shorter paths are riskier
        
        # Node type factors
        critical_nodes = 0
        for node_id in path:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                if (node.node_type == NodeType.DEVICE and 
                    'FortiGate' in node.properties.get('device_name', '')):
                    critical_nodes += 1
        
        critical_factor = critical_nodes / len(path)
        
        # Relationship strength factor
        avg_strength = 0.0
        strength_count = 0
        
        for i in range(len(path) - 1):
            for rel in self.relationships.values():
                if ((rel.source_node_id == path[i] and rel.target_node_id == path[i + 1]) or
                    (rel.source_node_id == path[i + 1] and rel.target_node_id == path[i])):
                    avg_strength += rel.strength
                    strength_count += 1
                    break
        
        if strength_count > 0:
            avg_strength /= strength_count
        
        # Combine factors
        risk_score = (path_length_factor * 0.4 + 
                     critical_factor * 0.4 + 
                     avg_strength * 0.2)
        
        return min(risk_score, 1.0)
    
    def _generate_path_summary(self, source: str, target: str, paths: List[List[str]]) -> str:
        """Generate summary for attack path analysis"""
        if not paths:
            return f"No attack paths found from {source} to {target}"
        
        shortest_path = min(paths, key=len)
        
        return (f"Found {len(paths)} potential attack paths from {source} to {target}. "
                f"Shortest path has {len(shortest_path)} hops: {' -> '.join(shortest_path[:3])}...")
    
    def _calculate_node_similarity(self, node1: GraphNode, node2: GraphNode) -> float:
        """Calculate similarity between two nodes"""
        if node1.node_type != node2.node_type:
            return 0.0
        
        # Compare properties
        common_props = set(node1.properties.keys()) & set(node2.properties.keys())
        if not common_props:
            return 0.0
        
        matches = 0
        for prop in common_props:
            if node1.properties[prop] == node2.properties[prop]:
                matches += 1
        
        similarity = matches / len(common_props)
        
        # Compare labels
        common_labels = set(node1.labels) & set(node2.labels)
        total_labels = set(node1.labels) | set(node2.labels)
        
        if total_labels:
            label_similarity = len(common_labels) / len(total_labels)
            similarity = (similarity + label_similarity) / 2
        
        return similarity
    
    def _calculate_propagation_risk(self, source: str, target: str, hop_distance: int) -> float:
        """Calculate propagation risk score"""
        if target not in self.nodes:
            return 0.0
        
        target_node = self.nodes[target]
        
        # Base risk decreases with distance
        distance_factor = 1.0 / (hop_distance + 1)
        
        # Node type factor
        type_risk = {
            NodeType.DEVICE: 0.8,
            NodeType.STORE: 0.6,
            NodeType.BRAND: 0.4,
            NodeType.NETWORK_SEGMENT: 0.7
        }.get(target_node.node_type, 0.5)
        
        # Critical system factor
        critical_factor = 1.0
        if 'FortiGate' in target_node.properties.get('device_name', ''):
            critical_factor = 1.2
        
        risk_score = distance_factor * type_risk * critical_factor
        return min(risk_score, 1.0)
    
    def _generate_propagation_summary(self, source: str, affected: List[Dict]) -> str:
        """Generate impact propagation summary"""
        if not affected:
            return f"No propagation impact identified from {source}"
        
        stores = len([e for e in affected if e['entity_type'] == 'store'])
        devices = len([e for e in affected if e['entity_type'] == 'device'])
        high_risk = len([e for e in affected if e['risk_score'] > 0.7])
        
        return (f"Incident at {source} could affect {len(affected)} entities: "
                f"{stores} stores, {devices} devices. {high_risk} high-risk entities identified.")
    
    def _generate_containment_recommendations(self, source: str, affected: List[Dict]) -> List[str]:
        """Generate containment recommendations"""
        recommendations = [
            f"Isolate {source} immediately to prevent further propagation"
        ]
        
        high_risk = [e for e in affected if e['risk_score'] > 0.8]
        if high_risk:
            recommendations.append(f"Monitor {len(high_risk)} high-risk entities for signs of compromise")
        
        stores = set(e['entity_id'] for e in affected if e['entity_type'] == 'store')
        if len(stores) > 1:
            recommendations.append(f"Implement network segmentation between affected stores")
        
        recommendations.extend([
            "Enable enhanced logging on all potentially affected systems",
            "Review and update incident response procedures",
            "Consider implementing additional monitoring controls"
        ])
        
        return recommendations
    
    def _find_connected_components(self) -> List[List[str]]:
        """Find connected components in the graph"""
        visited = set()
        components = []
        
        for node_id in self.nodes:
            if node_id not in visited:
                component = []
                stack = [node_id]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        component.append(current)
                        
                        # Add neighbors
                        for neighbor in self.adjacency_list.get(current, []):
                            if neighbor not in visited:
                                stack.append(neighbor)
                
                components.append(component)
        
        return components
    
    def _analyze_cluster(self, cluster_id: str, nodes: List[str]) -> Optional[ClusterAnalysis]:
        """Analyze a cluster of nodes"""
        try:
            if len(nodes) < 2:
                return None
            
            # Find central nodes (most connected within cluster)
            node_degrees = {}
            for node in nodes:
                degree = len([n for n in self.adjacency_list.get(node, []) if n in nodes])
                node_degrees[node] = degree
            
            central_nodes = sorted(node_degrees.keys(), key=lambda n: node_degrees[n], reverse=True)[:3]
            
            # Find common attributes
            common_attributes = {}
            if nodes:
                first_node = self.nodes.get(nodes[0])
                if first_node:
                    for prop, value in first_node.properties.items():
                        if all(self.nodes.get(node, {}).properties.get(prop) == value for node in nodes):
                            common_attributes[prop] = value
            
            # Calculate cluster score
            avg_degree = sum(node_degrees.values()) / len(node_degrees) if node_degrees else 0
            cluster_score = avg_degree / len(nodes)  # Density measure
            
            # Identify risk factors
            risk_factors = []
            security_events = sum(1 for node in nodes 
                                if self.nodes.get(node, {}).node_type == NodeType.SECURITY_EVENT)
            if security_events > 0:
                risk_factors.append(f"{security_events} security events in cluster")
            
            brands = set(self.nodes.get(node, {}).properties.get('brand') for node in nodes)
            brands.discard(None)
            if len(brands) > 1:
                risk_factors.append(f"Cross-brand cluster: {', '.join(brands)}")
            
            return ClusterAnalysis(
                cluster_id=cluster_id,
                cluster_type=common_attributes.get('type', 'mixed'),
                nodes=nodes,
                central_nodes=central_nodes,
                cluster_score=cluster_score,
                common_attributes=common_attributes,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing cluster {cluster_id}: {e}")
            return None
    
    def _calculate_betweenness_centrality(self, node_id: str) -> float:
        """Calculate simplified betweenness centrality"""
        if node_id not in self.nodes:
            return 0.0
        
        # Simplified calculation: count how many shortest paths go through this node
        # This is a basic approximation
        total_paths = 0
        paths_through_node = 0
        
        other_nodes = [n for n in self.nodes if n != node_id]
        
        for i in range(len(other_nodes)):
            for j in range(i + 1, len(other_nodes)):
                source, target = other_nodes[i], other_nodes[j]
                
                # Find shortest path
                path = self._find_shortest_path(source, target)
                if path:
                    total_paths += 1
                    if node_id in path[1:-1]:  # Node is in the middle of the path
                        paths_through_node += 1
        
        return paths_through_node / max(total_paths, 1)
    
    def _calculate_authority_score(self, node_id: str) -> float:
        """Calculate authority score (simplified PageRank)"""
        if node_id not in self.nodes:
            return 0.0
        
        # Simple authority based on incoming connections and their importance
        incoming_connections = 0
        authority_sum = 0.0
        
        for rel in self.relationships.values():
            if rel.target_node_id == node_id:
                incoming_connections += 1
                # Weight by source node's degree
                source_degree = len(self.adjacency_list.get(rel.source_node_id, []))
                authority_sum += rel.strength * (source_degree / max(len(self.nodes), 1))
        
        return authority_sum / max(incoming_connections, 1) if incoming_connections > 0 else 0.0
    
    def _find_shortest_path(self, source: str, target: str) -> List[str]:
        """Find shortest path between two nodes using BFS"""
        if source not in self.nodes or target not in self.nodes:
            return []
        
        if source == target:
            return [source]
        
        visited = set()
        queue = deque([(source, [source])])
        
        while queue:
            current, path = queue.popleft()
            
            if current in visited:
                continue
            
            visited.add(current)
            
            for neighbor in self.adjacency_list.get(current, []):
                if neighbor == target:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))
        
        return []

def create_graph_intelligence(config: Dict[str, Any] = None) -> NetworkGraphIntelligence:
    """Factory function to create NetworkGraphIntelligence"""
    return NetworkGraphIntelligence(config)