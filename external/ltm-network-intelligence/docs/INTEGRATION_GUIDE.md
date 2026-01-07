# LTM Network Intelligence Platform - Integration Guide

## Overview

This guide provides comprehensive instructions for integrating the LTM Network Intelligence Platform with your existing GitHub repositories for network device management and observability.

## Target Repositories

The platform is designed to integrate with the following repositories:

- **netai-troubleshooter** - Neo4j + Milvus + LLMs for network AI troubleshooting
- **network-device-mcp-server** - FortiGate, FortiManager, and Meraki device management
- **FortiGate-Enterprise-Platform** - Enterprise FortiGate management platform
- **ai-research-platform** - AI research and development platform
- **network_device_utils** - Network device utilities and common functions

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                LTM Network Intelligence Platform            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ LTM Client  │  │ MCP Server   │  │ Knowledge Graph     │ │
│  │ (Memory)    │  │ (Enhanced)   │  │ (Neo4j + Milvus)   │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Security    │  │ API Gateway  │  │ Performance         │ │
│  │ Framework   │  │ (FastAPI)    │  │ Monitor             │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
┌─────────▼────┐    ┌─────────▼────┐    ┌─────────▼────┐
│ netai-       │    │ network-     │    │ FortiGate-   │
│ troubleshoot │    │ device-mcp-  │    │ Enterprise-  │
│ er           │    │ server       │    │ Platform     │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Quick Start Integration

### 1. Platform Setup

First, set up the LTM Network Intelligence Platform:

```bash
# Clone the platform
git clone [your-repository-url] ltm-platform
cd ltm-platform

# Install dependencies
pip install -r requirements.txt

# Initialize the platform
python unified_network_intelligence.py --initialize --components ltm,mcp,kg,security,performance,api
```

### 2. Configure Repository Paths

Edit the platform configuration to point to your existing repositories:

```json
{
  "integrations": {
    "existing_repositories": {
      "netai_troubleshooter": {
        "path": "../netai-troubleshooter",
        "integration_mode": "bridge"
      },
      "network_device_mcp_server": {
        "path": "../network-device-mcp-server", 
        "integration_mode": "enhance"
      },
      "fortigate_enterprise_platform": {
        "path": "../FortiGate-Enterprise-Platform",
        "integration_mode": "bridge"
      },
      "ai_research_platform": {
        "path": "../ai-research-platform",
        "integration_mode": "bridge"
      },
      "network_device_utils": {
        "path": "../network_device_utils",
        "integration_mode": "import"
      }
    }
  }
}
```

## Repository-Specific Integration

### netai-troubleshooter Integration

**Integration Mode**: Bridge - Connect existing Neo4j + Milvus + LLM capabilities

#### Setup Steps:

1. **Add LTM Client to your troubleshooter**:

```python
# In your main troubleshooter file
from ltm_integration import LTMClient

class EnhancedNetworkTroubleshooter:
    def __init__(self):
        self.ltm_client = LTMClient("http://localhost:8000")
        # ... existing initialization
    
    async def initialize(self):
        # Initialize LTM
        await self.ltm_client.initialize()
        await self.ltm_client.awaken({
            "platform": "Network AI Troubleshooter",
            "capabilities": ["neo4j", "milvus", "llm_analysis"]
        })
        
        # ... existing initialization
```

2. **Enhance troubleshooting with LTM memory**:

```python
async def diagnose_network_issue(self, issue_description):
    # Search LTM for similar issues
    similar_issues = await self.ltm_client.search_memories(
        query=f"network issue {issue_description}",
        tags=["troubleshooting", "diagnosis", "network"],
        limit=10
    )
    
    # Use existing Neo4j/Milvus analysis
    neo4j_results = await self.query_network_topology(issue_description)
    milvus_results = await self.semantic_search_issues(issue_description)
    
    # Combine results with LTM insights
    combined_analysis = await self.combine_insights(
        ltm_insights=similar_issues,
        graph_data=neo4j_results,
        semantic_data=milvus_results
    )
    
    # Record solution in LTM
    await self.ltm_client.record_message(
        role="troubleshooter",
        content=f"Network issue diagnosed: {issue_description}. Solution: {combined_analysis['solution']}",
        tags=["troubleshooting", "solution", "network"],
        metadata=combined_analysis
    )
    
    return combined_analysis
```

3. **Bridge Knowledge Graph data**:

```python
# Add to your existing Neo4j queries
async def enhanced_topology_query(self, query_params):
    # Run existing Neo4j query
    topology_data = await self.run_neo4j_query(query_params)
    
    # Send topology insights to LTM platform
    if hasattr(self, 'ltm_platform_bridge'):
        await self.ltm_platform_bridge.update_topology_data(topology_data)
    
    return topology_data
```

### network-device-mcp-server Integration

**Integration Mode**: Enhance - Extend existing MCP server with LTM capabilities

#### Setup Steps:

1. **Extend your existing MCP server**:

```python
# Modify your existing MCP server
from ltm_enhanced_mcp_server import LTMEnhancedNetworkMCPServer

class YourExistingMCPServer(LTMEnhancedNetworkMCPServer):
    def __init__(self, config_path):
        super().__init__(config_path)
        # Keep your existing initialization
        
    async def initialize(self):
        # Initialize with LTM
        await super().initialize_with_ltm()
        
        # Add your existing device configurations
        await self.load_your_existing_devices()
```

2. **Enhance existing tools with LTM learning**:

```python
@self.server.call_tool()
async def enhanced_get_fortigate_status(device_name: str):
    # Use your existing FortiGate API calls
    status = await self.get_fortigate_status_original(device_name)
    
    # Enhance with LTM insights
    if self.ltm_client:
        # Search for historical patterns
        patterns = await self.ltm_client.search_memories(
            query=f"fortigate {device_name} status performance",
            tags=["fortigate", "status", "performance"]
        )
        
        # Add LTM insights to response
        status["ltm_insights"] = [
            {
                "pattern": p.content,
                "relevance": p.relevance_score,
                "timestamp": p.timestamp
            } for p in patterns[:3]
        ]
        
        # Record current status for learning
        await self.ltm_client.record_message(
            role="device_monitor",
            content=f"FortiGate {device_name} status check: {status.get('health', 'unknown')}",
            tags=["fortigate", "status", device_name],
            metadata=status
        )
    
    return status
```

### FortiGate-Enterprise-Platform Integration

**Integration Mode**: Bridge - Connect enterprise platform with LTM intelligence

#### Setup Steps:

1. **Add LTM bridge to your platform**:

```python
# In your main enterprise platform
from ltm_integration import LTMClient
from ltm_integration.knowledge_graph_bridge import KnowledgeGraphBridge

class EnhancedFortiGatePlatform:
    def __init__(self):
        self.ltm_client = LTMClient()
        self.kg_bridge = None
        # ... existing initialization
        
    async def initialize(self):
        await self.ltm_client.initialize()
        
        # Initialize knowledge graph bridge
        self.kg_bridge = KnowledgeGraphBridge(
            ltm_client=self.ltm_client,
            neo4j_config=self.config["neo4j"],
            milvus_config=self.config["milvus"]
        )
        await self.kg_bridge.initialize()
```

2. **Enhanced policy management with learning**:

```python
async def create_security_policy(self, policy_data):
    # Create policy using existing methods
    policy_result = await self.create_policy_original(policy_data)
    
    # Learn from policy creation
    if self.ltm_client:
        await self.ltm_client.record_message(
            role="policy_manager",
            content=f"Security policy created: {policy_data['name']} - {policy_data['action']}",
            tags=["security_policy", "creation", policy_data["action"]],
            metadata=policy_data
        )
    
    # Add to knowledge graph
    if self.kg_bridge:
        from ltm_integration.knowledge_graph_bridge import NetworkEntity
        policy_entity = NetworkEntity(
            entity_id=f"policy_{policy_result['id']}",
            entity_type="policy",
            name=policy_data["name"],
            properties=policy_data
        )
        await self.kg_bridge.add_network_entity(policy_entity)
    
    return policy_result
```

### ai-research-platform Integration

**Integration Mode**: Bridge - Connect AI research capabilities with network intelligence

#### Setup Steps:

1. **Connect research models with LTM**:

```python
# In your AI research platform
from ltm_integration import NetworkIntelligenceEngine

class EnhancedAIResearchPlatform:
    def __init__(self):
        self.ltm_client = LTMClient()
        self.network_intelligence = None
        
    async def initialize(self):
        await self.ltm_client.initialize()
        self.network_intelligence = NetworkIntelligenceEngine(self.ltm_client)
```

2. **Enhanced model training with network data**:

```python
async def train_network_prediction_model(self, training_data):
    # Use existing ML training pipeline
    model = await self.train_model_original(training_data)
    
    # Generate insights using network intelligence
    if self.network_intelligence:
        insights = []
        for data_point in training_data:
            insight = await self.network_intelligence.analyze_device_performance(data_point)
            insights.append(insight)
        
        # Create intelligence report
        report = await self.network_intelligence.generate_intelligence_report(insights)
        
        # Record research findings in LTM
        await self.ltm_client.record_message(
            role="ai_researcher",
            content=f"Network prediction model trained with {len(training_data)} samples. Insights: {len(insights)} generated",
            tags=["ai_research", "model_training", "network_prediction"],
            metadata={"model_metrics": model.metrics, "insights_summary": report["executive_summary"]}
        )
    
    return model
```

### network_device_utils Integration

**Integration Mode**: Import - Use utility functions directly in platform

#### Setup Steps:

1. **Import utilities into platform**:

```python
# In the LTM platform configuration
import sys
sys.path.append("../network_device_utils")

# Import your existing utilities
from network_utils import (
    device_connector,
    configuration_manager,
    monitoring_utils
)

# Enhance utilities with LTM
class LTMEnhancedDeviceConnector(device_connector.DeviceConnector):
    def __init__(self, ltm_client):
        super().__init__()
        self.ltm_client = ltm_client
        
    async def connect_to_device(self, device_config):
        # Use original connection method
        connection = await super().connect_to_device(device_config)
        
        # Record connection in LTM
        if connection.success and self.ltm_client:
            await self.ltm_client.record_message(
                role="device_connector",
                content=f"Successfully connected to device {device_config['name']} ({device_config['type']})",
                tags=["device_connection", "success", device_config["type"]],
                metadata=device_config
            )
        
        return connection
```

## Advanced Integration Features

### 1. Cross-Repository Learning

Enable learning across all integrated repositories:

```python
# In unified_network_intelligence.py
async def analyze_cross_platform_patterns(self):
    """Analyze patterns across all integrated platforms"""
    
    # Collect insights from all platforms
    netai_insights = await self.get_netai_troubleshooter_insights()
    mcp_insights = await self.get_mcp_server_insights()
    fortigate_insights = await self.get_fortigate_platform_insights()
    research_insights = await self.get_ai_research_insights()
    
    # Correlate insights using network intelligence
    all_insights = netai_insights + mcp_insights + fortigate_insights + research_insights
    
    if self.network_intelligence:
        correlations = await self.network_intelligence.correlate_insights(all_insights)
        
        # Record cross-platform learning
        await self.ltm_client.record_message(
            role="platform_orchestrator", 
            content=f"Cross-platform analysis completed: {len(all_insights)} insights from {4} platforms analyzed",
            tags=["cross_platform", "analysis", "correlation"],
            metadata=correlations
        )
        
        return correlations
```

### 2. Unified Dashboard Integration

Create a unified dashboard that shows data from all repositories:

```python
async def generate_unified_dashboard(self):
    """Generate unified dashboard across all platforms"""
    
    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "platforms": {},
        "unified_metrics": {},
        "cross_platform_insights": {}
    }
    
    # Collect data from each platform
    dashboard["platforms"]["netai_troubleshooter"] = await self.get_netai_status()
    dashboard["platforms"]["mcp_server"] = await self.get_mcp_status() 
    dashboard["platforms"]["fortigate_platform"] = await self.get_fortigate_status()
    dashboard["platforms"]["ai_research"] = await self.get_ai_research_status()
    
    # Generate unified metrics
    dashboard["unified_metrics"] = await self.calculate_unified_metrics(dashboard["platforms"])
    
    # Cross-platform insights
    dashboard["cross_platform_insights"] = await self.analyze_cross_platform_patterns()
    
    return dashboard
```

### 3. Automated Integration Testing

Set up automated testing for integrations:

```python
# tests/integration/test_repository_integrations.py
import pytest
import asyncio

class TestRepositoryIntegrations:
    
    async def test_netai_troubleshooter_integration(self):
        """Test netai-troubleshooter integration"""
        # Test LTM bridge functionality
        platform = UnifiedNetworkIntelligencePlatform()
        await platform.initialize()
        
        # Test troubleshooter connectivity
        result = await platform.test_netai_integration()
        assert result["success"] == True
        assert "neo4j" in result["capabilities"]
        assert "milvus" in result["capabilities"]
        
    async def test_mcp_server_enhancement(self):
        """Test MCP server enhancement"""
        # Test enhanced MCP server
        mcp_server = LTMEnhancedNetworkMCPServer()
        await mcp_server.initialize_with_ltm()
        
        # Test LTM-enhanced tool calls
        result = await mcp_server._proxy_to_mcp("get_device_status", {"device_name": "test"})
        assert result["ltm_enhanced"] == True
        
    async def test_knowledge_graph_integration(self):
        """Test knowledge graph bridge"""
        kg_bridge = KnowledgeGraphBridge(
            ltm_client=LTMClient(),
            neo4j_config=TEST_NEO4J_CONFIG,
            milvus_config=TEST_MILVUS_CONFIG
        )
        
        await kg_bridge.initialize()
        assert kg_bridge.is_available() == True
```

## Migration Strategies

### Gradual Migration Approach

1. **Phase 1**: Setup LTM platform alongside existing repositories
2. **Phase 2**: Add LTM clients to existing repositories without changing core functionality  
3. **Phase 3**: Enhance existing functions with LTM insights
4. **Phase 4**: Full integration with knowledge graph and cross-platform learning
5. **Phase 5**: Optimize and consolidate based on learned patterns

### Data Migration

```python
# Migration script for existing data
async def migrate_existing_data():
    """Migrate existing repository data to LTM platform"""
    
    # Migrate netai-troubleshooter data
    await migrate_neo4j_topology_to_kg_bridge()
    await migrate_milvus_embeddings_to_platform()
    
    # Migrate MCP server configurations
    await migrate_device_configs_to_enhanced_server()
    
    # Migrate FortiGate policies and configurations
    await migrate_fortigate_policies_to_knowledge_graph()
    
    # Migrate AI research models and datasets
    await migrate_research_data_to_ltm_memory()
```

## Configuration Examples

### Environment Configuration

```bash
# .env file for integrated platform
LTM_SERVER_URL=http://localhost:8000
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

MILVUS_HOST=localhost
MILVUS_PORT=19530

FORTIGATE_API_KEY=your_fortigate_api_key
MERAKI_API_KEY=your_meraki_api_key

REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://user:pass@localhost/ltm_audit

# Repository paths
NETAI_TROUBLESHOOTER_PATH=../netai-troubleshooter
MCP_SERVER_PATH=../network-device-mcp-server
FORTIGATE_PLATFORM_PATH=../FortiGate-Enterprise-Platform
AI_RESEARCH_PATH=../ai-research-platform
NETWORK_UTILS_PATH=../network_device_utils
```

### Docker Compose Integration

```yaml
# docker-compose.integration.yml
version: '3.8'
services:
  ltm-platform:
    build: .
    ports:
      - "8000:8000"  # LTM Platform
      - "8002:8002"  # API Gateway
      - "8003:8003"  # Prometheus metrics
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - ../netai-troubleshooter:/app/integrations/netai-troubleshooter:ro
      - ../network-device-mcp-server:/app/integrations/mcp-server:ro
      - ../FortiGate-Enterprise-Platform:/app/integrations/fortigate-platform:ro
    environment:
      - LTM_SERVER_URL=http://localhost:8000
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
    depends_on:
      - neo4j
      - milvus
      - redis
      
  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/your_password
      
  milvus:
    image: milvusdb/milvus:latest
    ports:
      - "19530:19530"
      
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## Best Practices

### 1. Gradual Integration
- Start with read-only LTM integration
- Gradually add learning capabilities
- Test each integration phase thoroughly

### 2. Data Consistency
- Maintain data consistency across platforms
- Use transaction-like operations for critical updates
- Implement rollback mechanisms

### 3. Performance Optimization
- Cache frequently accessed LTM memories
- Use async operations for all integrations
- Monitor performance impact of integrations

### 4. Security Considerations
- Use secure communications between platforms
- Implement proper authentication for cross-platform calls
- Audit all cross-platform data transfers

### 5. Monitoring and Logging
- Log all integration activities
- Monitor integration health
- Set up alerts for integration failures

## Troubleshooting

### Common Integration Issues

1. **Repository Path Issues**
   ```python
   # Check if repository paths are correct
   import os
   for repo_name, config in self.config["integrations"]["existing_repositories"].items():
       path = config["path"]
       if not os.path.exists(path):
           logger.error(f"Repository {repo_name} not found at {path}")
   ```

2. **LTM Connection Issues**
   ```python
   # Test LTM connectivity
   async def test_ltm_connection(self):
       try:
           await self.ltm_client.initialize()
           stats = await self.ltm_client.get_session_stats()
           return {"success": True, "stats": stats}
       except Exception as e:
           return {"success": False, "error": str(e)}
   ```

3. **Knowledge Graph Connection Issues**
   ```python
   # Test knowledge graph connectivity
   async def test_kg_connectivity(self):
       try:
           status = await self.kg_bridge.get_bridge_status()
           return status
       except Exception as e:
           return {"error": str(e)}
   ```

### Integration Health Checks

```python
async def run_integration_health_checks(self):
    """Run comprehensive integration health checks"""
    
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "repository_status": {},
        "platform_component_status": {}
    }
    
    # Check each repository integration
    for repo_name in self.config["integrations"]["existing_repositories"].keys():
        try:
            status = await self.check_repository_integration(repo_name)
            health_status["repository_status"][repo_name] = status
            
            if not status["healthy"]:
                health_status["overall_status"] = "degraded"
                
        except Exception as e:
            health_status["repository_status"][repo_name] = {
                "healthy": False,
                "error": str(e)
            }
            health_status["overall_status"] = "unhealthy"
    
    return health_status
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Update Integration Configurations**
   - Review and update repository paths
   - Update API keys and credentials
   - Validate integration health

2. **Performance Tuning** 
   - Monitor LTM memory usage
   - Optimize knowledge graph queries
   - Tune caching strategies

3. **Security Updates**
   - Rotate API keys and secrets
   - Update security configurations
   - Review audit logs

### Getting Help

- Check the troubleshooting section above
- Review integration logs in `logs/integration.log`
- Run health checks: `python unified_network_intelligence.py --health-check`
- Contact support with specific error messages and logs

This integration guide provides a comprehensive approach to connecting the LTM Network Intelligence Platform with your existing repositories while maintaining their individual functionality and adding powerful learning and intelligence capabilities.