# ltm_integration/knowledge_graph_bridge.py
# Knowledge Graph Bridge with Neo4j and Milvus integration

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import numpy as np
from dataclasses import dataclass, asdict

# Neo4j imports
try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available - install with: pip install neo4j")

# Milvus imports  
try:
    from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logging.warning("Milvus client not available - install with: pip install pymilvus")

# Vector embedding (simple implementation or use proper embedding service)
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    logging.warning("SentenceTransformers not available - install with: pip install sentence-transformers")

logger = logging.getLogger(__name__)

@dataclass
class NetworkEntity:
    """Represents a network entity in the knowledge graph"""
    entity_id: str
    entity_type: str  # device, interface, subnet, policy, etc.
    name: str
    properties: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class NetworkRelationship:
    """Represents a relationship between network entities"""
    relationship_id: str
    source_entity: str
    target_entity: str
    relationship_type: str  # connects_to, manages, protects, etc.
    properties: Dict[str, Any]
    strength: float = 1.0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class NetworkInsightVector:
    """Vector representation of network insights for semantic search"""
    insight_id: str
    content: str
    vector: List[float]
    metadata: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class KnowledgeGraphBridge:
    """Bridge between LTM and Knowledge Graph (Neo4j + Milvus)"""
    
    def __init__(self, ltm_client, neo4j_config: Dict[str, str], milvus_config: Dict[str, str]):
        self.ltm_client = ltm_client
        self.neo4j_config = neo4j_config
        self.milvus_config = milvus_config
        
        # Database connections
        self.neo4j_driver = None
        self.milvus_collection = None
        self.embedding_model = None
        
        # Configuration
        self.vector_dimension = 384  # sentence-transformers/all-MiniLM-L6-v2
        self.collection_name = milvus_config.get("collection_name", "network_embeddings")
        
        # State tracking
        self.initialized = False
        self.neo4j_available = False
        self.milvus_available = False
        
    async def initialize(self) -> Dict[str, Any]:
        """Initialize knowledge graph bridge"""
        initialization_result = {
            "bridge": "Knowledge Graph Bridge",
            "timestamp": datetime.now().isoformat(),
            "neo4j_status": "unavailable",
            "milvus_status": "unavailable",
            "embedding_status": "unavailable",
            "overall_status": "failed"
        }
        
        try:
            # Initialize Neo4j connection
            if NEO4J_AVAILABLE:
                neo4j_result = await self._initialize_neo4j()
                initialization_result["neo4j_status"] = neo4j_result["status"]
                self.neo4j_available = neo4j_result["success"]
            
            # Initialize Milvus connection
            if MILVUS_AVAILABLE:
                milvus_result = await self._initialize_milvus()
                initialization_result["milvus_status"] = milvus_result["status"]
                self.milvus_available = milvus_result["success"]
            
            # Initialize embedding model
            if EMBEDDING_AVAILABLE:
                embedding_result = await self._initialize_embedding_model()
                initialization_result["embedding_status"] = embedding_result["status"]
            
            # Set overall status
            if self.neo4j_available or self.milvus_available:
                initialization_result["overall_status"] = "partial_success"
                self.initialized = True
                
                if self.neo4j_available and self.milvus_available:
                    initialization_result["overall_status"] = "success"
                    
                    # Create initial network topology
                    await self._create_initial_topology()
                    
                    # Record initialization in LTM
                    await self.ltm_client.record_message(
                        role="system",
                        content="Knowledge Graph Bridge initialized successfully with Neo4j and Milvus",
                        tags=["initialization", "knowledge_graph", "neo4j", "milvus"],
                        metadata=initialization_result
                    )
            
            logger.info(f"Knowledge Graph Bridge initialization: {initialization_result['overall_status']}")
            return initialization_result
            
        except Exception as e:
            logger.error(f"Knowledge Graph Bridge initialization failed: {e}")
            initialization_result["error"] = str(e)
            return initialization_result

    async def _initialize_neo4j(self) -> Dict[str, Any]:
        """Initialize Neo4j graph database connection"""
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                self.neo4j_config["uri"],
                auth=(self.neo4j_config["user"], self.neo4j_config["password"])
            )
            
            # Test connection
            async with self.neo4j_driver.session() as session:
                result = await session.run("RETURN 1 as test")
                await result.consume()
                
            logger.info("✓ Neo4j connection established")
            return {"success": True, "status": "connected"}
            
        except Exception as e:
            logger.error(f"Neo4j initialization failed: {e}")
            return {"success": False, "status": "failed", "error": str(e)}

    async def _initialize_milvus(self) -> Dict[str, Any]:
        """Initialize Milvus vector database connection"""
        try:
            # Connect to Milvus
            connections.connect(
                alias="default",
                host=self.milvus_config["host"],
                port=self.milvus_config["port"]
            )
            
            # Create or get collection
            if utility.has_collection(self.collection_name):
                self.milvus_collection = Collection(self.collection_name)
            else:
                # Create collection schema
                fields = [
                    FieldSchema(name="insight_id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=5000),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.vector_dimension),
                    FieldSchema(name="timestamp", dtype=DataType.VARCHAR, max_length=50),
                    FieldSchema(name="entity_type", dtype=DataType.VARCHAR, max_length=50),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=2000)
                ]
                
                schema = CollectionSchema(
                    fields=fields,
                    description="Network intelligence insights and embeddings"
                )
                
                self.milvus_collection = Collection(
                    name=self.collection_name,
                    schema=schema
                )
                
                # Create index for vector field
                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                self.milvus_collection.create_index(
                    field_name="vector",
                    index_params=index_params
                )
            
            # Load collection
            self.milvus_collection.load()
            
            logger.info("✓ Milvus connection established")
            return {"success": True, "status": "connected"}
            
        except Exception as e:
            logger.error(f"Milvus initialization failed: {e}")
            return {"success": False, "status": "failed", "error": str(e)}

    async def _initialize_embedding_model(self) -> Dict[str, Any]:
        """Initialize sentence embedding model"""
        try:
            if EMBEDDING_AVAILABLE:
                # Use a lightweight model for embeddings
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✓ Sentence transformer model loaded")
                return {"success": True, "status": "loaded"}
            else:
                # Fallback to simple embedding
                logger.warning("Using simple embedding fallback")
                return {"success": True, "status": "fallback"}
                
        except Exception as e:
            logger.error(f"Embedding model initialization failed: {e}")
            return {"success": False, "status": "failed", "error": str(e)}

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.embedding_model and EMBEDDING_AVAILABLE:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        else:
            # Simple fallback embedding (hash-based)
            import hashlib
            hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
            # Convert to pseudo-random vector
            np.random.seed(hash_value % (2**32))
            return np.random.rand(self.vector_dimension).tolist()

    async def _create_initial_topology(self):
        """Create initial network topology in Neo4j"""
        if not self.neo4j_available:
            return
            
        try:
            async with self.neo4j_driver.session() as session:
                # Create basic network structure
                await session.run("""
                    MERGE (dc:DataCenter {name: 'Primary DC', location: 'Main Site'})
                    MERGE (core:NetworkDevice {name: 'Core Switch', type: 'Switch', role: 'core'})
                    MERGE (fw:NetworkDevice {name: 'FortiGate-FW01', type: 'Firewall', role: 'security'})
                    MERGE (dist:NetworkDevice {name: 'Distribution Switch', type: 'Switch', role: 'distribution'})
                    
                    MERGE (core)-[:LOCATED_IN]->(dc)
                    MERGE (fw)-[:LOCATED_IN]->(dc)
                    MERGE (dist)-[:LOCATED_IN]->(dc)
                    
                    MERGE (core)-[:CONNECTS_TO {port: 'Gi1/1', bandwidth: '10G'}]->(fw)
                    MERGE (fw)-[:CONNECTS_TO {port: 'Gi1/2', bandwidth: '10G'}]->(dist)
                    
                    CREATE (analysis:Analysis {
                        id: randomUUID(),
                        type: 'topology_initialization',
                        timestamp: datetime(),
                        source: 'KnowledgeGraphBridge'
                    })
                """)
                
                logger.info("✓ Initial network topology created in Neo4j")
                
        except Exception as e:
            logger.error(f"Initial topology creation failed: {e}")

    async def add_network_entity(self, entity: NetworkEntity) -> Dict[str, Any]:
        """Add network entity to knowledge graph"""
        try:
            result = {
                "entity_id": entity.entity_id,
                "operation": "add_entity",
                "success": False,
                "neo4j_added": False,
                "vector_added": False
            }
            
            # Add to Neo4j
            if self.neo4j_available:
                neo4j_result = await self._add_entity_to_neo4j(entity)
                result["neo4j_added"] = neo4j_result["success"]
            
            # Add to vector database if it's an insight-type entity
            if self.milvus_available and entity.entity_type in ["insight", "analysis", "pattern"]:
                vector_result = await self._add_entity_to_vectors(entity)
                result["vector_added"] = vector_result["success"]
            
            result["success"] = result["neo4j_added"] or result["vector_added"]
            
            # Record in LTM
            if self.ltm_client and result["success"]:
                await self.ltm_client.record_message(
                    role="system",
                    content=f"Network entity added to knowledge graph: {entity.name} (type: {entity.entity_type})",
                    tags=["knowledge_graph", "entity_addition", entity.entity_type],
                    metadata=asdict(entity)
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Add entity failed: {e}")
            return {"entity_id": entity.entity_id, "success": False, "error": str(e)}

    async def _add_entity_to_neo4j(self, entity: NetworkEntity) -> Dict[str, Any]:
        """Add entity to Neo4j graph"""
        try:
            async with self.neo4j_driver.session() as session:
                # Create node based on entity type
                if entity.entity_type == "device":
                    query = """
                        MERGE (n:NetworkDevice {id: $entity_id})
                        SET n.name = $name,
                            n.type = $device_type,
                            n.timestamp = $timestamp,
                            n.properties = $properties
                        RETURN n.id as created_id
                    """
                    parameters = {
                        "entity_id": entity.entity_id,
                        "name": entity.name,
                        "device_type": entity.properties.get("device_type", "unknown"),
                        "timestamp": entity.timestamp,
                        "properties": json.dumps(entity.properties)
                    }
                    
                elif entity.entity_type == "interface":
                    query = """
                        MERGE (n:NetworkInterface {id: $entity_id})
                        SET n.name = $name,
                            n.timestamp = $timestamp,
                            n.properties = $properties
                        RETURN n.id as created_id
                    """
                    parameters = {
                        "entity_id": entity.entity_id,
                        "name": entity.name,
                        "timestamp": entity.timestamp,
                        "properties": json.dumps(entity.properties)
                    }
                    
                elif entity.entity_type == "policy":
                    query = """
                        MERGE (n:SecurityPolicy {id: $entity_id})
                        SET n.name = $name,
                            n.timestamp = $timestamp,
                            n.properties = $properties
                        RETURN n.id as created_id
                    """
                    parameters = {
                        "entity_id": entity.entity_id,
                        "name": entity.name,
                        "timestamp": entity.timestamp,
                        "properties": json.dumps(entity.properties)
                    }
                    
                else:
                    # Generic entity
                    query = """
                        MERGE (n:NetworkEntity {id: $entity_id})
                        SET n.name = $name,
                            n.entity_type = $entity_type,
                            n.timestamp = $timestamp,
                            n.properties = $properties
                        RETURN n.id as created_id
                    """
                    parameters = {
                        "entity_id": entity.entity_id,
                        "name": entity.name,
                        "entity_type": entity.entity_type,
                        "timestamp": entity.timestamp,
                        "properties": json.dumps(entity.properties)
                    }
                
                result = await session.run(query, parameters)
                record = await result.single()
                
                if record:
                    return {"success": True, "created_id": record["created_id"]}
                else:
                    return {"success": False, "error": "No record returned"}
                    
        except Exception as e:
            logger.error(f"Neo4j entity addition failed: {e}")
            return {"success": False, "error": str(e)}

    async def _add_entity_to_vectors(self, entity: NetworkEntity) -> Dict[str, Any]:
        """Add entity to Milvus vector database"""
        try:
            # Generate content for embedding
            content = f"{entity.name}: {entity.properties.get('description', '')}"
            for key, value in entity.properties.items():
                if key != 'description':
                    content += f" {key}: {value}"
            
            # Generate embedding
            vector = self._generate_embedding(content)
            
            # Prepare data for insertion
            data = [
                [entity.entity_id],  # insight_id
                [content[:4999]],    # content (limited to max length)
                [vector],            # vector
                [entity.timestamp],  # timestamp
                [entity.entity_type], # entity_type
                [json.dumps(entity.properties)[:1999]]  # metadata (limited)
            ]
            
            # Insert into Milvus
            insert_result = self.milvus_collection.insert(data)
            
            if insert_result.insert_count > 0:
                return {"success": True, "insert_count": insert_result.insert_count}
            else:
                return {"success": False, "error": "No records inserted"}
                
        except Exception as e:
            logger.error(f"Milvus entity addition failed: {e}")
            return {"success": False, "error": str(e)}

    async def add_network_relationship(self, relationship: NetworkRelationship) -> Dict[str, Any]:
        """Add relationship between network entities"""
        try:
            if not self.neo4j_available:
                return {"success": False, "error": "Neo4j not available"}
                
            async with self.neo4j_driver.session() as session:
                # Create relationship between entities
                query = """
                    MATCH (source {id: $source_id})
                    MATCH (target {id: $target_id})
                    MERGE (source)-[r:%s {id: $relationship_id}]->(target)
                    SET r.timestamp = $timestamp,
                        r.strength = $strength,
                        r.properties = $properties
                    RETURN r.id as relationship_id
                """ % relationship.relationship_type.upper()
                
                parameters = {
                    "source_id": relationship.source_entity,
                    "target_id": relationship.target_entity,
                    "relationship_id": relationship.relationship_id,
                    "timestamp": relationship.timestamp,
                    "strength": relationship.strength,
                    "properties": json.dumps(relationship.properties)
                }
                
                result = await session.run(query, parameters)
                record = await result.single()
                
                if record:
                    # Record in LTM
                    if self.ltm_client:
                        await self.ltm_client.record_message(
                            role="system",
                            content=f"Network relationship added: {relationship.source_entity} -{relationship.relationship_type}-> {relationship.target_entity}",
                            tags=["knowledge_graph", "relationship", relationship.relationship_type],
                            metadata=asdict(relationship)
                        )
                    
                    return {"success": True, "relationship_id": record["relationship_id"]}
                else:
                    return {"success": False, "error": "Relationship creation failed"}
                    
        except Exception as e:
            logger.error(f"Add relationship failed: {e}")
            return {"success": False, "error": str(e)}

    async def query_network_relationships(self, query_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query network relationships from knowledge graph"""
        try:
            if not self.neo4j_available:
                return {"success": False, "error": "Neo4j not available"}
            
            parameters = parameters or {}
            
            async with self.neo4j_driver.session() as session:
                if query_type == "topology":
                    # Get network topology
                    query = """
                        MATCH (n:NetworkDevice)-[r]->(m:NetworkDevice)
                        RETURN n.name as source, type(r) as relationship, m.name as target,
                               n.type as source_type, m.type as target_type,
                               r.properties as rel_properties
                        ORDER BY n.name
                    """
                    
                elif query_type == "device_connections":
                    device_name = parameters.get("device_name")
                    query = """
                        MATCH (n:NetworkDevice {name: $device_name})-[r]-(m)
                        RETURN n.name as device, type(r) as relationship, m.name as connected_entity,
                               labels(m) as entity_labels, r.properties as rel_properties
                    """
                    parameters = {"device_name": device_name}
                    
                elif query_type == "security_policies":
                    query = """
                        MATCH (p:SecurityPolicy)-[r]->(d:NetworkDevice)
                        RETURN p.name as policy, d.name as device, type(r) as relationship,
                               p.properties as policy_properties
                        ORDER BY p.name
                    """
                    
                elif query_type == "path_analysis":
                    source = parameters.get("source")
                    target = parameters.get("target")
                    query = """
                        MATCH path = shortestPath((source:NetworkDevice {name: $source})-[*]-(target:NetworkDevice {name: $target}))
                        RETURN [node in nodes(path) | node.name] as path_nodes,
                               [rel in relationships(path) | type(rel)] as path_relationships,
                               length(path) as path_length
                    """
                    parameters = {"source": source, "target": target}
                    
                else:
                    return {"success": False, "error": f"Unknown query type: {query_type}"}
                
                result = await session.run(query, parameters)
                records = await result.data()
                
                query_result = {
                    "success": True,
                    "query_type": query_type,
                    "timestamp": datetime.now().isoformat(),
                    "results": {
                        "count": len(records),
                        query_type: records
                    }
                }
                
                # Record query in LTM
                if self.ltm_client:
                    await self.ltm_client.record_message(
                        role="system",
                        content=f"Knowledge graph query executed: {query_type} - {len(records)} results",
                        tags=["knowledge_graph", "query", query_type],
                        metadata={"query_type": query_type, "result_count": len(records)}
                    )
                
                return query_result
                
        except Exception as e:
            logger.error(f"Network relationship query failed: {e}")
            return {"success": False, "error": str(e)}

    async def semantic_search_insights(self, search_query: str, limit: int = 10, min_similarity: float = 0.7) -> Dict[str, Any]:
        """Perform semantic search on network insights using Milvus"""
        try:
            if not self.milvus_available:
                return {"success": False, "error": "Milvus not available"}
            
            # Generate query embedding
            query_vector = self._generate_embedding(search_query)
            
            # Search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 16}
            }
            
            # Perform search
            search_results = self.milvus_collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=limit,
                output_fields=["insight_id", "content", "timestamp", "entity_type", "metadata"]
            )
            
            # Process results
            insights = []
            for hits in search_results:
                for hit in hits:
                    if hit.score >= min_similarity:
                        insight = {
                            "insight_id": hit.entity.get("insight_id"),
                            "content": hit.entity.get("content"),
                            "similarity_score": hit.score,
                            "timestamp": hit.entity.get("timestamp"),
                            "entity_type": hit.entity.get("entity_type"),
                            "metadata": json.loads(hit.entity.get("metadata", "{}"))
                        }
                        insights.append(insight)
            
            search_result = {
                "success": True,
                "search_query": search_query,
                "timestamp": datetime.now().isoformat(),
                "results": {
                    "count": len(insights),
                    "insights": insights
                }
            }
            
            # Record search in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="system",
                    content=f"Semantic search performed: '{search_query}' - {len(insights)} relevant insights found",
                    tags=["knowledge_graph", "semantic_search", "insights"],
                    metadata={"query": search_query, "result_count": len(insights)}
                )
            
            return search_result
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"success": False, "error": str(e)}

    async def discover_network_topology(self, discovery_source: Dict[str, Any]) -> Dict[str, Any]:
        """Discover and update network topology from various sources"""
        try:
            discovery_result = {
                "source": discovery_source.get("type", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "entities_discovered": 0,
                "relationships_discovered": 0,
                "entities": [],
                "relationships": []
            }
            
            # Process discovery based on source type
            if discovery_source.get("type") == "mcp_server":
                devices = discovery_source.get("devices", [])
                
                for device_data in devices:
                    # Create network entity
                    entity = NetworkEntity(
                        entity_id=f"device_{device_data.get('name', 'unknown')}",
                        entity_type="device",
                        name=device_data.get("name", "unknown"),
                        properties={
                            "device_type": device_data.get("type", "unknown"),
                            "status": device_data.get("status", "unknown"),
                            "host": device_data.get("host", ""),
                            "discovery_source": "mcp_server",
                            "health_status": device_data.get("health_status", "unknown")
                        }
                    )
                    
                    # Add to knowledge graph
                    add_result = await self.add_network_entity(entity)
                    if add_result["success"]:
                        discovery_result["entities_discovered"] += 1
                        discovery_result["entities"].append(entity.name)
            
            elif discovery_source.get("type") == "network_scan":
                # Handle network scan results
                scan_results = discovery_source.get("scan_results", [])
                
                for scan_entry in scan_results:
                    entity = NetworkEntity(
                        entity_id=f"discovered_{scan_entry.get('ip', 'unknown')}",
                        entity_type="device",
                        name=scan_entry.get("hostname", scan_entry.get("ip", "unknown")),
                        properties={
                            "ip_address": scan_entry.get("ip"),
                            "mac_address": scan_entry.get("mac", ""),
                            "device_type": scan_entry.get("device_type", "unknown"),
                            "discovery_method": "network_scan",
                            "ports_open": scan_entry.get("open_ports", [])
                        }
                    )
                    
                    add_result = await self.add_network_entity(entity)
                    if add_result["success"]:
                        discovery_result["entities_discovered"] += 1
                        discovery_result["entities"].append(entity.name)
            
            # Record discovery in LTM
            if self.ltm_client:
                await self.ltm_client.record_message(
                    role="system",
                    content=f"Network topology discovery completed: {discovery_result['entities_discovered']} entities, {discovery_result['relationships_discovered']} relationships from {discovery_result['source']}",
                    tags=["knowledge_graph", "topology_discovery", discovery_result["source"]],
                    metadata=discovery_result
                )
            
            return discovery_result
            
        except Exception as e:
            logger.error(f"Network topology discovery failed: {e}")
            return {"success": False, "error": str(e)}

    async def correlate_with_ltm_patterns(self, correlation_type: str) -> Dict[str, Any]:
        """Correlate knowledge graph data with LTM patterns"""
        try:
            if not self.ltm_client:
                return {"success": False, "error": "LTM client not available"}
            
            correlation_result = {
                "correlation_type": correlation_type,
                "timestamp": datetime.now().isoformat(),
                "patterns_found": 0,
                "correlations": [],
                "insights": []
            }
            
            # Get relevant LTM patterns
            if correlation_type == "device_performance":
                ltm_patterns = await self.ltm_client.search_memories(
                    query="device performance patterns trends analysis",
                    tags=["performance", "device", "trends"],
                    limit=15
                )
                
                # Get device information from Neo4j
                if self.neo4j_available:
                    topology_query = await self.query_network_relationships("topology")
                    devices = topology_query.get("results", {}).get("topology", [])
                    
                    # Correlate patterns with devices
                    for pattern in ltm_patterns:
                        for device in devices:
                            if device["source"].lower() in pattern.content.lower():
                                correlation = {
                                    "device": device["source"],
                                    "pattern_content": pattern.content[:200],
                                    "relevance_score": pattern.relevance_score,
                                    "correlation_strength": "high" if pattern.relevance_score > 0.8 else "medium"
                                }
                                correlation_result["correlations"].append(correlation)
                
            elif correlation_type == "security_incidents":
                ltm_patterns = await self.ltm_client.search_memories(
                    query="security incidents patterns threats analysis",
                    tags=["security", "incidents", "threats"],
                    limit=15
                )
                
                # Correlate with security policies in graph
                if self.neo4j_available:
                    policy_query = await self.query_network_relationships("security_policies")
                    policies = policy_query.get("results", {}).get("security_policies", [])
                    
                    for pattern in ltm_patterns:
                        correlation = {
                            "pattern_type": "security_incident",
                            "pattern_content": pattern.content[:200],
                            "affected_policies": len(policies),
                            "relevance_score": pattern.relevance_score
                        }
                        correlation_result["correlations"].append(correlation)
            
            correlation_result["patterns_found"] = len(ltm_patterns)
            
            # Generate insights from correlations
            if correlation_result["correlations"]:
                high_correlations = [c for c in correlation_result["correlations"] if c.get("correlation_strength") == "high"]
                
                if high_correlations:
                    correlation_result["insights"].append({
                        "insight": f"Found {len(high_correlations)} high-confidence correlations between LTM patterns and network topology",
                        "recommendation": "Review identified correlations for potential optimization opportunities",
                        "priority": "medium"
                    })
            
            return correlation_result
            
        except Exception as e:
            logger.error(f"LTM correlation failed: {e}")
            return {"success": False, "error": str(e)}

    def is_available(self) -> bool:
        """Check if knowledge graph bridge is available"""
        return self.initialized and (self.neo4j_available or self.milvus_available)

    async def get_bridge_status(self) -> Dict[str, Any]:
        """Get current status of the knowledge graph bridge"""
        return {
            "initialized": self.initialized,
            "neo4j_available": self.neo4j_available,
            "milvus_available": self.milvus_available,
            "embedding_available": EMBEDDING_AVAILABLE,
            "collection_name": self.collection_name,
            "vector_dimension": self.vector_dimension
        }

    async def close(self):
        """Close knowledge graph bridge connections"""
        try:
            if self.neo4j_driver:
                await self.neo4j_driver.close()
                
            if self.milvus_available:
                connections.disconnect("default")
                
            logger.info("Knowledge Graph Bridge closed")
        except Exception as e:
            logger.error(f"Knowledge Graph Bridge close failed: {e}")